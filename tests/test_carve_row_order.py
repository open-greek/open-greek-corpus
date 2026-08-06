"""Row order in a carve. The bug this guards was silent by construction.

carve() partitions by slicing the row list between consecutive starts, so that
list has to be in reading order. Five Walz files are written with their rows
sorted lexicographically inside a page (1, 10, 11, ... 19, 2, 20), which puts .9
last. A work starting mid-page at .9 took that row alone and jumped to the next
page. Every row still landed in exactly one bucket, so the partition was exact
and token conservation passed; the text was just in the wrong work.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import carve_edition_volume as cev  # noqa: E402


def test_document_order_is_numeric_not_lexicographic():
    loci = [f"vol_0023.{n}" for n in (1, 10, 11, 2, 20, 3, 9)]
    assert [l.split(".")[1] for l in sorted(loci, key=cev._doc_key)] == \
        ["1", "2", "3", "9", "10", "11", "20"]


def test_pages_sort_before_rows():
    assert cev._doc_key("vol_0009.99") < cev._doc_key("vol_0010.1")


def test_a_non_numeric_ordinal_does_not_raise():
    cev._doc_key("vol_0023.4a")


@pytest.fixture
def volume(tmp_path, monkeypatch):
    """One page written lexicographically, with a second work starting at .9."""
    rows = [{"urn": "ocr.test_vol", "locus": f"test_vol_0023.{n}",
             "text": f"λόγος{n} καὶ πρᾶγμα{n}", "source": "ocr",
             "edition": "test", "license": "PD"}
            for n in sorted(range(1, 13), key=str)]
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "ocr.test_vol.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    monkeypatch.setattr(cev, "CORPUS", corpus)
    monkeypatch.setattr(cev, "SECONDARY", tmp_path / "secondary")
    monkeypatch.setattr(cev, "CHANGES", tmp_path / "changes")
    (tmp_path / "changes").mkdir()
    return tmp_path


def test_a_mid_page_start_takes_the_rest_of_its_page(volume, capsys):
    plan = {
        "volume": "test", "urn": "ocr.test_vol",
        "edition_title": "Test", "printed_to_scan_offset": 0,
        "front_matter_before": "test_vol_0023.1",
        "works": [
            {"n": "I", "slug": "a.one", "title": "One", "author_display": "A",
             "tlg": None, "printed_pages": "23", "start": "test_vol_0023.1",
             "incipit_check": "λόγος1", "evidence": "test"},
            {"n": "II", "slug": "b.two", "title": "Two", "author_display": "B",
             "tlg": None, "printed_pages": "23", "start": "test_vol_0023.9",
             "incipit_check": "λόγος9", "evidence": "test"},
        ],
        "shared_pages": ["23"],
    }
    assert cev.carve(plan, False, Path("data/test_plan.json")) == 0
    out = capsys.readouterr().out
    # Work II starts at .9, so it must hold .9 through .12: four rows, not one.
    line = next(l for l in out.splitlines() if "b.two" in l)
    assert " 4 " in line.replace(",", " "), line
    line_a = next(l for l in out.splitlines() if "a.one" in l)
    assert " 8 " in line_a.replace(",", " "), line_a


def test_the_scrambled_page_is_reported(volume, capsys):
    plan = {
        "volume": "test", "urn": "ocr.test_vol", "edition_title": "Test",
        "printed_to_scan_offset": 0, "front_matter_before": "test_vol_0023.1",
        "works": [{"n": "I", "slug": "a.one", "title": "One",
                   "author_display": "A", "tlg": None, "printed_pages": "23",
                   "start": "test_vol_0023.1", "incipit_check": "λόγος1",
                   "evidence": "test"}],
    }
    cev.carve(plan, False, Path("data/test_plan.json"))
    assert "not in numeric row order" in capsys.readouterr().out
