"""Enlarged retries retain the original page request and reading order."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_jahn_aristides as jahn


def test_page81_retry_pins_original_and_preserves_nonoverlapping_body_strips(tmp_path, monkeypatch):
    monkeypatch.setattr(jahn, "ROOT", tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pinned scan")
    monkeypatch.setattr(jahn, "SOURCE_SHA256", hashlib.sha256(pdf.read_bytes()).hexdigest())
    original = tmp_path / "data/ingest_reviews/original.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"sources": {"jahn": {"license": "PD"}}, "pages": [
        {"id": "page81", "scan_page": 81, "printed_page": 8, "book": 1,
         "source": "jahn", "region": [.04, .04, .95, .92], "max_side": 2600}]}))
    before = original.read_bytes()
    result = jahn.prepare_page81_retry(pdf, original.with_name("retry.json"), original)
    assert original.read_bytes() == before
    assert result["retry_of"]["sha256"] == hashlib.sha256(before).hexdigest()
    assert result["retry_of"]["path"] == "data/ingest_reviews/original.json"
    strips = result["pages"]
    assert [s["reading_order"] for s in strips] == [1, 2, 3]
    assert all(s["reconstructs"] == "page81" and s["max_side"] > 2600 for s in strips)
    assert strips[0]["region"][3] == strips[1]["region"][1]
    assert strips[1]["region"][3] == strips[2]["region"][1]
    pdf.write_bytes(b"different scan")
    with pytest.raises(ValueError, match="differs"):
        jahn.prepare_page81_retry(pdf, original.with_name("retry.json"), original)


def test_length_retry_separates_notation_from_complete_prose_strips(tmp_path, monkeypatch):
    monkeypatch.setattr(jahn, "ROOT", tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pinned scan")
    monkeypatch.setattr(jahn, "SOURCE_SHA256", hashlib.sha256(pdf.read_bytes()).hexdigest())
    original = tmp_path / "data/ingest_reviews/original.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"sources": {"jahn1882": {"license": "PD"}}, "pages": [
        {"id": f"page{scan}", "scan_page": scan, "printed_page": scan - 73,
         "book": 1 if scan < 111 else 2, "source": "jahn1882", "region": [0, 0, 1, 1]}
        for scan in [90, 112]]}))
    before = original.read_bytes()
    result = jahn.prepare_failed_pages_retry(pdf, original.with_name("retry.json"), original)
    assert original.read_bytes() == before
    assert len(result["pages"]) == 5
    assert [p["scan_page"] for p in result["pages"]] == [90, 90, 112, 112, 112]
    assert all(p["text_role"] == "authorial-notation-heading" for p in result["pages"][:2])
    assert all(not r["lexical_eligible"] and r["retained_as"] == "source-image"
        for r in result["nonlexical_source_regions"]["page90"])
    assert result["retry_of"]["sha256"] == hashlib.sha256(before).hexdigest()


def test_notation_retry_keeps_every_mode_caption_and_all_three_prose_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(jahn, "ROOT", tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pinned scan")
    monkeypatch.setattr(jahn, "SOURCE_SHA256", hashlib.sha256(pdf.read_bytes()).hexdigest())
    original = tmp_path / "data/ingest_reviews/original.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"sources": {"jahn1882": {"license": "PD"}}, "pages": [
        {"id": f"page{scan}", "scan_page": scan, "printed_page": scan - 73,
         "book": 1, "source": "jahn1882", "region": [0, 0, 1, 1]}
        for scan in [82, 87, 91]]}))
    result = jahn.prepare_notation_retry(pdf, original.with_name("retry.json"), original)
    assert len(result["pages"]) == 10
    assert len([p for p in result["pages"] if p["text_role"] == "mode-caption"]) == 6
    assert {p["scan_page"] for p in result["pages"]} == {82, 87, 91}
    assert len(result["nonlexical_source_regions"]["page87"]) == 6
    assert all(not r["lexical_eligible"] for regions in result["nonlexical_source_regions"].values() for r in regions)


def test_length_supplement_exactly_partitions_only_failed_first_strip(tmp_path, monkeypatch):
    monkeypatch.setattr(jahn, "ROOT", tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pinned scan")
    monkeypatch.setattr(jahn, "SOURCE_SHA256", hashlib.sha256(pdf.read_bytes()).hexdigest())
    original = tmp_path / "data/ingest_reviews/original.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"sources": {"jahn1882": {"license": "PD"}}, "pages": [
        {"id": f"page{scan}", "scan_page": scan, "printed_page": scan - 73,
         "book": 1 if scan == 90 else 2, "source": "jahn1882", "region": [0, 0, 1, 1]}
        for scan in [90, 112]]}))
    base_path = original.with_name("jahn-aristides-length-retry.json")
    base = jahn.prepare_failed_pages_retry(pdf, base_path, original)
    before = base_path.read_bytes()
    result = jahn.prepare_length_supplement(pdf, original.with_name("supplement.json"), original)
    assert base_path.read_bytes() == before
    assert result["supplements"]["manifest_sha256"] == hashlib.sha256(before).hexdigest()
    first = next(p for p in base["pages"] if p["scan_page"] == 112)
    assert all(p["replaces"] == first["id"] for p in result["pages"])
    a, b = [p["region"] for p in result["pages"]]
    assert a[:3] == first["region"][:3] and b[3] == first["region"][3]
    assert a[3] == b[1] and a[0] == b[0] and a[2] == b[2]
