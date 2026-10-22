"""Expanded body coverage cannot relabel the historical source-role counts."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import editorial_role_manifestations
from build_ocr_quality_report import herodas_role_qualification
from repair_editorial_roles import AUDIT


@pytest.mark.parametrize("body_recovered", [False, True])
def test_body_recovery_scope_is_separate_from_historical_partition(tmp_path, monkeypatch, body_recovered):
    audit = tmp_path / AUDIT / "changes.json"
    audit.parent.mkdir(parents=True)
    audit.write_bytes(b"{}\n")
    historical = {"original_rows": 136, "primary_rows": 62,
        "original_analysis_tokens": 2846, "primary_analysis_tokens": 2036,
        "retained_analysis_tokens": 810}
    latest = {"original_passages": 62, "recovered_passages": 22, "primary_passages": 84,
        "original_body_pages": 13, "body_pages": 35, "raw_ocr_unresolved_slots": 31,
        "unresolved_slots": 4, "new_noncountable_slots": 99}
    coverage = {"policy": "source-reviewed-editorial-role-partition", "counts": historical}
    if body_recovered:
        coverage = {"policy": "source-reviewed-body-recovery", "counts": latest,
            "manifest": "data/corpus_changes/herodas-headlam-knox-body/changes.json",
            "manifest_sha256": "a" * 64,
            "qualification": "New source pages with explicit glyph uncertainty; this is not an OCR error-rate measurement.",
            "source_role_review": coverage}
    monkeypatch.setattr(editorial_role_manifestations, "metadata", lambda root: {
        "herodas.mimiambi": {"coverage_composition": coverage}})
    result = herodas_role_qualification(tmp_path)
    assert result["counts"] == historical
    assert "not character error rate" in result["qualification"]
    if body_recovered:
        current = result["later_body_recovery"]
        assert current["counts"] == latest
        assert current["counts"]["primary_passages"] == 84
        assert current["counts"]["recovered_passages"] == 22
        assert current["counts"]["body_pages"] == 35
        assert current["counts"]["raw_ocr_unresolved_slots"] != current["counts"]["unresolved_slots"]
        assert current["manifest"] == coverage["manifest"]
        assert current["manifest_sha256"] == coverage["manifest_sha256"]
        assert current["qualification"] == coverage["qualification"]
    else:
        assert "later_body_recovery" not in result
