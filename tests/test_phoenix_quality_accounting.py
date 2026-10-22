"""Phoenix quality reports distinguish scope from source-recognition changes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_ocr_quality_report import (greek_tokens, iter_records,
                                      phoenix_review_qualification)
from check_ocr_ledgers import reviewed_run_metadata
from frequency_projection import FrequencyProjection
from repair_phoenix_crusius import PRIMARY, verify


def test_scope_and_same_verse_comparisons_are_separate():
    frequency = FrequencyProjection(ROOT / "data")
    records = list(iter_records(ROOT / PRIMARY))
    all_forms = {token for row in records for token in greek_tokens(frequency.text(row))}
    report = phoenix_review_qualification(ROOT, records, all_forms, frequency)
    assert report["legacy_whole_volume"]["n_tokens"] == 29998
    assert report["same_verses_before_review"]["n_tokens"] == 132
    assert report["served_after_review"]["n_tokens"] == 129
    assert report["served_after_review"]["n_tokens_checked"] == 87
    assert report["counts"]["surface_tokens"] == 133
    assert report["served_after_review"]["n_surface_tokens"] == 134
    assert "different scopes" in report["qualification"]


def test_historical_run_and_served_page_counts_remain_distinct():
    row = {"urn": "phoenix.fragmenta", "edition": "qwen36-phoenix_choliambi_crusius", "pages": 1}
    metadata = reviewed_run_metadata(row, ROOT)
    assert row["pages"] == 1  # this helper proposes metadata; it never edits data
    assert metadata["pages"] == 107
    assert "not 107 pages of Phoenix" in metadata["scope_note"]
    audit, _, _ = verify(ROOT)
    assert audit["counts"]["source_scan_pages"] == [68, 69]
    assert reviewed_run_metadata({"urn": "other.work"}, ROOT) == {}
