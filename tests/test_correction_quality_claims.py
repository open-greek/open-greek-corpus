"""Correction-log quality claims must resolve to the current primary text."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_corpus_catalog as catalog
import build_provenance as provenance
from correction_quality_claims import verified_manual_works


def put(data, name, value, *, jsonl=False):
    path = data / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if jsonl:
        text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in value)
    else:
        text = json.dumps(value, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return path


def mirror(data, *, slug="sample.work", locus="1", corrected="λόγος", by="agent", claimed=True):
    put(data, "corrections_log/provenance.json", {
        "corrected_works": [slug] if claimed else [], "auto_corrected_works": []})
    return put(data, "corrections_log/applied.jsonl", [{"urn": slug, "locus": locus,
        "original": "λογος", "corrected": corrected, "by": by}], jsonl=True)


def primary(data, *, slug="sample.work", locus="1", text="λόγος", corrections=None, storage="corpus"):
    row = {"urn": slug, "locus": locus, "text": text, "source": "ocr", "edition": "fixture", "license": "PD"}
    if corrections is not None:
        row["corrections"] = corrections
    return put(data, f"{storage}/{slug}.jsonl", [row], jsonl=True)


@pytest.mark.parametrize("missing", ["both", "provenance", "applied"])
def test_missing_optional_mirror_supplies_no_enrichment(tmp_path, missing):
    primary(tmp_path)
    mirror(tmp_path)
    if missing in {"both", "provenance"}:
        (tmp_path / "corrections_log/provenance.json").unlink()
    if missing in {"both", "applied"}:
        (tmp_path / "corrections_log/applied.jsonl").unlink()
    assert verified_manual_works(tmp_path) == set()


@pytest.mark.parametrize("method", ["llm", "agent", "manual"])
def test_manual_reading_at_the_same_current_primary_locus_is_verified(tmp_path, method):
    primary(tmp_path, text="ὁ λόγος·")
    mirror(tmp_path, by=method)
    assert verified_manual_works(tmp_path) == {"sample.work"}


@pytest.mark.parametrize("method", ["freq", "confusion", "dehyphenation", "unknown"])
def test_nonmanual_record_cannot_support_a_manual_claim(tmp_path, method):
    primary(tmp_path)
    mirror(tmp_path, by=method)
    assert verified_manual_works(tmp_path) == set()


def test_a_rekeyed_reading_does_not_resolve_by_text_search(tmp_path):
    primary(tmp_path, locus="new.1")
    mirror(tmp_path, locus="old.1")
    assert verified_manual_works(tmp_path) == set()


def test_a_matching_reading_elsewhere_cannot_support_the_recorded_locus(tmp_path):
    primary(tmp_path, locus="1", text="ἄλλος")
    path = tmp_path / "corpus/sample.work.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"locus": "2", "text": "λόγος"}, ensure_ascii=False) + "\n")
    mirror(tmp_path, locus="1")
    assert verified_manual_works(tmp_path) == set()


@pytest.mark.parametrize("storage", ["corpus_secondary", "ocr_witnesses", "paratext"])
def test_secondary_or_retained_only_reading_is_not_current_primary_evidence(tmp_path, storage):
    primary(tmp_path, storage=storage)
    mirror(tmp_path)
    assert verified_manual_works(tmp_path) == set()


def test_matching_secondary_cannot_override_a_different_primary_reading(tmp_path):
    primary(tmp_path, text="ἄλλος")
    primary(tmp_path, storage="corpus_secondary")
    mirror(tmp_path)
    assert verified_manual_works(tmp_path) == set()


def test_corrected_reading_inside_a_longer_greek_token_is_not_standing(tmp_path):
    primary(tmp_path, text="ἡμιθεός")
    mirror(tmp_path, corrected="θεός")
    assert "θεός" in "ἡμιθεός"
    assert verified_manual_works(tmp_path) == set()


def test_original_reading_does_not_support_a_reverted_correction(tmp_path):
    primary(tmp_path, text="λογος")
    mirror(tmp_path)
    assert verified_manual_works(tmp_path) == set()


def test_record_alone_without_the_provenance_claim_is_not_enrichment(tmp_path):
    primary(tmp_path)
    mirror(tmp_path, claimed=False)
    assert verified_manual_works(tmp_path) == set()


def test_at_least_one_current_manual_record_can_survive_stale_records(tmp_path):
    primary(tmp_path)
    applied = mirror(tmp_path, locus="old.1")
    with applied.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"urn": "sample.work", "locus": "1", "corrected": "λόγος", "by": "manual"}, ensure_ascii=False) + "\n")
    assert verified_manual_works(tmp_path) == {"sample.work"}


def test_catalog_and_readme_share_verified_manual_claims_without_auto_coverage_gate(tmp_path, monkeypatch):
    data = tmp_path / "data"
    primary(data, slug="valid.work")
    primary(data, slug="stale.work")
    primary(data, slug="stamped.work", corrections=["manual"])
    primary(data, slug="auto.work", corrections=["dehyphenation"])
    put(data, "corrections_log/provenance.json", {
        "corrected_works": ["valid.work", "stale.work"], "auto_corrected_works": []})
    put(data, "corrections_log/applied.jsonl", [
        {"urn": "valid.work", "locus": "1", "corrected": "λόγος", "by": "agent"},
        {"urn": "stale.work", "locus": "old.1", "corrected": "λόγος", "by": "manual"}], jsonl=True)
    slugs = ["valid.work", "stale.work", "stamped.work", "auto.work"]
    editions = {slug: {"source": "ocr", "edition": "fixture", "license": "PD", "n_passages": 1} for slug in slugs}
    index = {"works": {slug: {"id": f"ogc{i:06d}", "title": "Fixture work", "author": {"name": "Fixture author"}}
        for i, slug in enumerate(slugs, 1)}}
    put(data, "corpus_editions.json", editions)
    put(data, "work_index.json", index)
    put(data, "work_token_totals.json", {slug: {"tokens": 1, "tokens_lemmatized": 1} for slug in slugs})
    put(data, "ocr_quality_report.json", {"works": {slug: {} for slug in slugs}})
    put(data, "served_scheme_inference.json", {"works": {slug: {} for slug in slugs}})
    components = {"works": {slug: {"mixed_ocr_digital": False, "analysis_tokens": 1} for slug in slugs}}
    monkeypatch.setattr(catalog, "DATA", data)
    monkeypatch.setattr(catalog, "CORPUS", data / "corpus")
    monkeypatch.setattr(catalog, "load_verified", lambda directory: components)
    monkeypatch.setattr(catalog, "validate_catalog", lambda report, rows: None)
    rows, _ = catalog.build_rows()
    statuses = {row[0]: row[catalog.COLUMNS.index("correction")] for row in rows}
    assert statuses == {"valid.work": "manual", "stale.work": "raw-ocr",
        "stamped.work": "manual", "auto.work": "auto-corrected"}
    readme = tmp_path / "README.md"
    readme.write_text(provenance.START + "\n" + provenance.END + "\n")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "DATA", data)
    monkeypatch.setattr(provenance, "README", readme)
    monkeypatch.setattr(provenance, "load_verified", lambda directory: components)
    monkeypatch.setattr(provenance, "sync_anchor_counts", lambda text, works: text)
    provenance.main()
    for slug, status in statuses.items():
        line = next(line for line in readme.read_text().splitlines() if line.startswith("| " + slug + " |"))
        assert line.endswith("| " + ("raw OCR" if status == "raw-ocr" else status) + " |")
