import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_manetho_citations as repair
from build_work_index import resolve_citation, load_citation_aliases
from migration_fixtures import copy_repair_state


def record(book):
    return {"urn": repair.WORK, "edition": repair.EDITION, "source": "first1k",
            "license": "CC-BY-SA-4.0", "locus": f"{book}.1.358",
            "text": "τριβάδας", "corrections": ["spacing-breathing"]}


@pytest.mark.parametrize("old,new", list(repair.BOOKS.items()))
def test_each_checked_book_maps_once(old, new):
    row = record(old)
    result = repair.remap_record(row)
    assert result["locus"] == f"{new}.1.358"
    assert result["source_citation"] == {"scheme": repair.SCHEME, "locus": row["locus"]}
    assert result["text"] == row["text"] and result["corrections"] == row["corrections"]
    with pytest.raises(ValueError, match="already been mapped"):
        repair.remap_record(result)


def test_mapping_is_scoped_to_the_edition_and_rejects_changed_source(tmp_path):
    row = dict(record("5"), edition="another-edition")
    assert repair.remap_record(row) is row
    path = tmp_path / "tei.xml"
    path.write_text("different source")
    with pytest.raises(ValueError, match="TEI changed"):
        repair.validate_source(repair.WORK, repair.EDITION, "first1k", path)
    repair.validate_source(repair.WORK, "another-edition", "first1k", path)


def test_committed_replay_and_current_citations_remain_distinct_from_historical_ones():
    repair.run(ROOT, "check")
    index = json.loads((ROOT / "data/work_index.json").read_text())
    assert resolve_citation(index, repair.WORK, "4.1.358")["locus"] == "4.1.358"
    assert resolve_citation(index, repair.WORK, "5.1.358", scheme=repair.SCHEME)["locus"] == "4.1.358"
    assert resolve_citation(index, repair.WORK, "4.1.358", scheme=repair.SCHEME)["locus"] == "6.1.358"
    rows = [json.loads(line) for line in (ROOT / repair.CORPUS_PATH).read_text().splitlines()]
    assert len(rows) == len({r["locus"] for r in rows}) == 2981
    assert "τριβάδας" in next(r["text"] for r in rows if r["locus"] == "4.1.358")
    with pytest.raises(ValueError, match="different work"):
        resolve_citation(index, "other", "5.1.358", scheme=repair.SCHEME)
    with pytest.raises(KeyError):
        resolve_citation(index, repair.WORK, "5.1.99999", scheme=repair.SCHEME)


def test_scheme_validator_checks_destinations(tmp_path, monkeypatch):
    import build_work_index as index
    monkeypatch.setattr(index, "REPO", tmp_path)
    path = tmp_path / "aliases.json"
    path.write_text(json.dumps({"schemes": {"bad": {"work": "missing", "aliases": {}}}}))
    with pytest.raises(ValueError, match="Unknown citation scheme work"):
        load_citation_aliases(path, {})


def test_prior_accent_decisions_apply_before_book_numbers_are_changed():
    from build_corpus_loci import load_text_corrections, apply_text_corrections
    audit_dir = ROOT / repair.AUDIT
    snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
    rows = [json.loads(line) for line in snapshots[repair.CORPUS_PATH].splitlines()]
    prior = json.loads((ROOT / repair.PRIOR_AUDIT).read_text())
    block = next(b for b in prior["files"] if b["file"] == repair.CORPUS_PATH)
    rules = load_text_corrections()
    for edit in block["edits"]:
        row = rows[edit["index"]]
        original = row["text"]
        for offset, token in edit["was"]:
            corrected = prior["substitutions"][token]
            original = original[:offset] + token + original[offset + len(corrected):]
        assert apply_text_corrections(repair.WORK, row["locus"], original, rules) == row["text"]


def test_undo_restores_every_input_byte_and_checks_output_guards(tmp_path):
    audit_dir = ROOT / repair.AUDIT
    snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
    copy_repair_state(ROOT, tmp_path, repair)
    target = tmp_path / repair.CORPUS_PATH
    original = target.read_bytes()
    target.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        repair.run(tmp_path, "undo")
    target.write_bytes(original)
    repair.run(tmp_path, "undo")
    for path, expected in snapshots.items():
        target = tmp_path / path
        assert (target.read_text() if target.exists() else None) == expected, path
