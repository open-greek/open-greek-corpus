import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_mathematical_citations as repair
from build_work_index import resolve_citation
from migration_fixtures import copy_repair_state


@pytest.mark.parametrize("work,old,new", [
    ("pappus-mathematics.synagoge", "1.1", "2.1"),
    ("pappus-mathematics.synagoge", "2", "3"),
    ("pappus-mathematics.synagoge", "2.1", "3.1"),
    ("pappus-mathematics.synagoge", "3.1", "4.1"),
    ("pappus-mathematics.synagoge", "4.1", "5.1"),
    ("apollonius-geom.conica", "1", "4.1"),
    ("apollonius-geom.conica", "57", "4.57"),
])
def test_source_citations_map_once_without_changing_readings(work, old, new):
    row = {"urn": work, "edition": "1st1K-grc1", "source": "first1k",
           "locus": old, "text": "λόγος", "variants": ["λόγοι"]}
    result = repair.remap_record(row)
    assert result["locus"] == new
    assert result["text"] == row["text"] and result["variants"] == row["variants"]
    assert result["source_citation"]["locus"] == old
    with pytest.raises(ValueError, match="already been mapped"):
        repair.remap_record(result)
    other = dict(row, edition="another-edition")
    assert repair.remap_record(other) is other


def test_changed_source_cannot_reuse_reviewed_book_mapping(tmp_path):
    path = tmp_path / "different.xml"
    path.write_text("changed source")
    for work in repair.RULES:
        with pytest.raises(ValueError, match="TEI changed"):
            repair.validate_source(work, repair.EDITION, "first1k", path)
    with pytest.raises(ValueError, match="Unreviewed Apollonius"):
        repair.remap_record({"urn": "apollonius-geom.conica", "source": "first1k",
            "edition": repair.EDITION, "locus": "58"})


def test_replay_and_historical_colliding_book_numbers_are_explicit():
    repair.run(ROOT, "check")
    index = json.loads((ROOT / "data/work_index.json").read_text())
    work = "pappus-mathematics.synagoge"
    assert resolve_citation(index, work, "2.1")["locus"] == "2.1"
    assert resolve_citation(index, work, "2.1",
        scheme=repair.RULES[work]["scheme"])["locus"] == "3.1"
    work = "apollonius-geom.conica"
    assert resolve_citation(index, work, "57",
        scheme=repair.RULES[work]["scheme"])["locus"] == "4.57"


def test_undo_restores_exact_inputs_and_rejects_later_edits(tmp_path):
    copy_repair_state(ROOT, tmp_path, repair)
    snapshots = json.loads(gzip.decompress((ROOT / repair.AUDIT / "before.json.gz").read_bytes()))
    path = tmp_path / repair.ALIASES
    raw = path.read_bytes()
    path.write_bytes(raw + b"\n")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        repair.run(tmp_path, "undo")
    path.write_bytes(raw)
    repair.run(tmp_path, "undo")
    for relative, original in snapshots.items():
        assert (tmp_path / relative).read_text() == original


def test_ocr_manifests_cover_each_missing_greek_page_once():
    directory = ROOT / "data/ingest_reviews/coverage"
    six_seven = json.loads((directory / "pappus-6-7.json").read_text())
    eight = json.loads((directory / "pappus-8.json").read_text())
    for manifest, expected in [(six_seven, list(range(474, 1021, 2))),
                               (eight, list(range(1022, 1135, 2)))]:
        assert [p["printed_page"] for p in manifest["pages"]] == expected
        assert len({(p["source"], p["pdf_page"]) for p in manifest["pages"]}) == len(expected)
    assert all(p["source"] == "pappialexandrin01hultgoog"
               for p in six_seven["pages"] if p["printed_page"] in {634, 636, 638})
    assert all(p["transmission"] == "excerpt-from-heron"
               for p in eight["pages"] if p["printed_page"] >= 1116)
    conica = json.loads((directory / "apollonius-conica-1-3.json").read_text())
    assert conica["greek_pages"] == list(range(20, 469, 2))
    assert [b["first_pdf_page"] for b in conica["books"]] == [20, 210, 336]
