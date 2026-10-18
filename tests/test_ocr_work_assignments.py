"""Work routing depends on the printed sequence, never a guessed OCR initial."""
import importlib.util
import json
import gzip
import shutil
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_ocr_work_assignments as repair
import build_work_index as index
import rename_work


def record(work, page, text="σκιρόμαντις· ὁ ἐπὶ Σκίρῳ μαντευόμενος"):
    return {"urn": work, "cts": "urn:cts:greekLit:tlg4085.tlg002",
            "locus": f"hesychius_masked_{page:04d}.23", "text": text,
            "edition": "qwen36-hesychius_schmidt_masked", "corrections": ["freq"]}


def test_sigma_gloss_and_continuation_follow_physical_page():
    for text in ("σκιρόμαντις· ὁ ἐπὶ Σκίρῳ μαντευόμενος", "ὁ μαντευόμενος", "τὸν λόγον"):
        row = record(repair.HESYCHIUS[0], 728, text)
        path, corrected, evidence = repair.assign(row)
        assert corrected["urn"] == repair.HESYCHIUS[1]
        assert corrected["cts"].endswith("003")
        assert corrected["text"] == row["text"]
        assert corrected["corrections"] == ["freq"]


def test_pi_initial_on_alpha_page_stays_with_alpha_page():
    row = record(repair.HESYCHIUS[1], 20, "πτίοις ἐκ βύβλων (πρὸς) κάθαρσιν οὖσα")
    assert repair.assign(row)[1]["urn"] == repair.HESYCHIUS[0]


@pytest.mark.parametrize("page,target", [(626, 0), (627, 1), (864, 1)])
def test_reviewed_book_boundaries(page, target):
    assert repair.hesychius_section(page) == repair.HESYCHIUS[target]


def test_ethnic_word_index_is_preserved_outside_primary_corpus():
    row = record(repair.HESYCHIUS[0], 865)
    path, corrected, evidence = repair.assign(row)
    assert path == repair.PARATEXT
    assert corrected["text"] == row["text"]
    assert corrected["class"] == "edition_index"
    assert corrected["lang"] == "grc"
    with pytest.raises(ValueError, match="Unreviewed"):
        repair.hesychius_section(875)


@pytest.mark.parametrize("work", list(repair.KAIBEL))
def test_anthology_witness_never_retains_a_single_authors_work_anchor(work):
    row = {"urn": work, "cts": "urn:cts:greekLit:tlg1654.tlg001",
           "locus": "run_0065.31", "text": "ᾄδειν ὑπῆρχε πρὸς ψαλάγματα λύρας·"}
    path, corrected, evidence = repair.assign(row)
    assert corrected["urn"] == repair.KAIBEL[work]
    assert "cts" not in corrected
    assert corrected["text"] == row["text"]


def test_route_keeps_every_reading_and_links_all_changed_destinations():
    a, b = repair.HESYCHIUS
    old_a, old_b = record(a, 728), record(b, 20, "πτίοις ἐκ βύβλων")
    sources = {a: repair.jsonl([old_a]), b: repair.jsonl([old_b])}
    outputs, changes, aliases = repair.route(sources)
    rows = [json.loads(line) for raw in outputs.values() for line in raw.splitlines()]
    assert sorted(row["text"] for row in rows) == sorted([old_a["text"], old_b["text"]])
    assert len(changes) == 2
    assert aliases[a][old_a["locus"]]["slug"] == b
    assert aliases[b][old_b["locus"]]["slug"] == a


def test_passage_alias_validator_refuses_dangling_or_unsafe_destinations(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "REPO", tmp_path)
    target = tmp_path / "data/corpus/new.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text('{"locus": "1", "text": "λόγος"}\n')
    path = tmp_path / "aliases.json"
    destination = {"path": "data/corpus/new.jsonl", "slug": "new", "locus": "1"}
    def write():
        path.write_text(json.dumps({"aliases": {"old": {"1": destination}}}))
    works = {"new": {"former_slugs": ["old"]}}
    write()
    assert index.load_passage_aliases(path, works)["old"]["1"] == destination
    destination["locus"] = "2"
    write()
    with pytest.raises(ValueError, match="Missing passage alias"):
        index.load_passage_aliases(path, works)
    destination["path"] = "../escape.jsonl"
    write()
    with pytest.raises(ValueError, match="Invalid passage alias path"):
        index.load_passage_aliases(path, works)


def test_committed_repair_replays_without_changing_any_text():
    if not (ROOT / repair.AUDIT / "changes.json").exists():
        pytest.skip("repair not applied yet")
    repair.run(ROOT, "check")


def test_rename_preserves_crosswalk_rows_without_cts(tmp_path, monkeypatch):
    path = tmp_path / "crosswalk.tsv"
    monkeypatch.setattr(rename_work, "CW_TSV", path)
    rename_work._write_crosswalk_tsv({"pta-work": {"pta": "pta0001.pta001"}})
    assert path.read_text() == "slug\tcts_urn\ttlg\npta-work\t\tpta:pta0001.pta001\n"


def test_repair_undo_restores_exact_primary_secondary_and_metadata_bytes(tmp_path):
    audit_dir = ROOT / repair.AUDIT
    if not (audit_dir / "changes.json").exists():
        pytest.skip("repair not applied yet")
    audit = json.loads((audit_dir / "changes.json").read_text())
    snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
    # Reverse later migrations before checking the original output guards.
    import repair_lydus_identity as lydus
    import repair_manetho_citations as manetho
    from migration_fixtures import copy_repair_state
    copy_repair_state(ROOT, tmp_path, repair, [manetho, lydus])
    repair.run(tmp_path, "undo")
    for path, expected in snapshots.items():
        target = tmp_path / path
        assert (target.read_text() if target.exists() else None) == expected, path


def test_committed_volume_identities_and_reported_hesychius_gloss():
    if not (ROOT / repair.AUDIT / "changes.json").exists():
        pytest.skip("repair not applied yet")
    data = json.loads((ROOT / "data/work_index.json").read_text())
    for old, new in repair.KAIBEL.items():
        work = data["works"][new]
        assert work["author"]["name"] == repair.VOLUME_NAME
        assert not work["work_anchors"].get("tlg")
        assert data["redirects"][old] == new
        assert work["volume_witness"]["volume"] == "kaibel-cgf-i-1-1899"
    target = data["passage_aliases"][repair.HESYCHIUS[0]]["hesychius_masked_0728.23"]
    assert target["slug"] == repair.HESYCHIUS[1]
