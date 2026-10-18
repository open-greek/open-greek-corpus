import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_corpus_release import polytonic_quality


def fixture(data):
    evidence = data / "quality/polytonic-loss-pages.jsonl.gz"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"pinned page evidence")
    (data / "polytonic_loss_report.json").write_text(json.dumps({
        "selection_rule": None, "page_readings_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        "counts": {"readings": 3, "flagged": 1}, "scope": "Review candidates only",
        "policy": {"operating_limits": ["No automatic text selection"]}}))
    validation = data / "evaluation/polytonic-loss"
    validation.mkdir(parents=True)
    inputs = {}
    for key, filename in [("manifest_sha256", "manifest.json"), ("policy_sha256", "policy.json"),
                          ("scan_review_sha256", "scan-review.json")]:
        path = validation / filename
        path.write_text("{}\n")
        inputs[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    for family in ("3.6", "3.8"):
        run = {"metadata": {"model": f"Qwen/Qwen{family}-27B-FP8"}, "predictions_sha256": "pinned",
               "by_split": {"calibration": {"pages": 20}, "test": {"pages": 40}},
               "false_positives": [], "missed_cases": [], "unassessable_pages": [],
               "pages": [{"id": str(i)} for i in range(60)]}
        (validation / ("qwen" + family.replace(".", "") + "-validation.json")).write_text(json.dumps({
            **inputs, "selection_rule": None, "scan_review_complete": True, "runs": [run]}))
    return validation


def test_release_pins_review_evidence_and_both_fixed_fresh_runs(tmp_path):
    validation = fixture(tmp_path)
    result = polytonic_quality(tmp_path)
    assert result["fresh_validation_status"] == "complete"
    assert result["selection_rule"] is None
    assert len(result["fresh_validation"]) == 2
    (validation / "qwen38-validation.json").unlink()
    assert polytonic_quality(tmp_path)["fresh_validation_status"] == "pending"


def test_release_rejects_stale_validation_and_page_evidence(tmp_path):
    validation = fixture(tmp_path)
    (validation / "scan-review.json").write_text("changed")
    with pytest.raises(ValueError, match="inputs changed"):
        polytonic_quality(tmp_path)
    (tmp_path / "quality/polytonic-loss-pages.jsonl.gz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="page evidence changed"):
        polytonic_quality(tmp_path)
