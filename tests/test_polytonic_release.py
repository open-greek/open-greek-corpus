import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_corpus_release import polytonic_quality
from report_polytonic_loss import POLICY, dump


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(data):
    evidence = data / "quality/polytonic-loss-pages.jsonl.gz"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"pinned page evidence")
    corpus = data / "corpus"
    corpus.mkdir()
    source = corpus / "test.work.jsonl"
    source.write_text('{"source":"ocr","text":"λόγος"}\n')
    validation = data / "evaluation/polytonic-loss"
    validation.mkdir(parents=True)
    (validation / "policy.json").write_bytes(dump(POLICY))
    pages = [{"id": str(i), "split": "calibration" if i < 20 else "test", "volume": "test"}
             for i in range(60)]
    (validation / "manifest.json").write_text(json.dumps({"pages": pages,
        "policy_sha256": digest(validation / "policy.json")}))
    (validation / "scan-review.json").write_text("{}\n")
    (data / "polytonic_loss_report.json").write_text(json.dumps({
        "selection_rule": None, "page_readings_sha256": digest(evidence),
        "corpus_sha256": hashlib.sha256(f"test.work\t{digest(source)}\n".encode()).hexdigest(),
        "input_corpus_files": {source.name: digest(source)},
        "counts": {"readings": 3, "flagged": 1}, "scope": "Review candidates only",
        "policy": POLICY, "policy_sha256": digest(validation / "policy.json")}))
    inputs = {key: digest(validation / filename) for key, filename in
              [("manifest_sha256", "manifest.json"), ("policy_sha256", "policy.json"),
               ("scan_review_sha256", "scan-review.json")]}
    (validation / "raw").mkdir()
    for family in ("3.6", "3.8"):
        name = "qwen" + family.replace(".", "")
        metadata = {"model": f"Qwen/Qwen{family}-27B-FP8"}
        rows = [{**page, "raw_prediction": "λόγος", "finish_reason": "stop"} for page in pages]
        raw = validation / "raw" / (name + ".jsonl")
        raw.write_text("".join(json.dumps(row) + "\n" for row in [{"_meta": metadata}, *rows]))
        run = {"metadata": metadata, "predictions_sha256": digest(raw),
               "predictions_path": "data/evaluation/polytonic-loss/raw/" + name + ".jsonl",
               "measurement_limits": ["No assessable positive case in this run"],
               "by_split": {"calibration": {"pages": 20}, "test": {"pages": 40}},
               "false_positives": [], "missed_cases": [], "unassessable_pages": [], "pages": rows}
        (validation / (name + "-validation.json")).write_text(json.dumps({
            **inputs, "selection_rule": None, "scan_review_complete": True, "runs": [run]}))
    return validation


def test_release_pins_review_evidence_and_both_fixed_fresh_runs(tmp_path):
    validation = fixture(tmp_path)
    result = polytonic_quality(tmp_path)
    assert result["fresh_validation_status"] == "complete"
    assert result["selection_rule"] is None
    assert len(result["fresh_validation"]) == 2
    assert result["fresh_validation"][0]["runs"][0]["measurement_limits"] == ["No assessable positive case in this run"]
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


@pytest.mark.parametrize("change", ["modify", "add", "remove"])
def test_release_rejects_changed_or_new_corpus_inputs(tmp_path, change):
    fixture(tmp_path)
    source = tmp_path / "corpus/test.work.jsonl"
    if change == "modify":
        source.write_text("changed")
    elif change == "add":
        (source.parent / "new.work.jsonl").write_text("new")
    else:
        source.unlink()
    with pytest.raises(ValueError, match="different corpus"):
        polytonic_quality(tmp_path)


def test_release_rejects_repeated_fixed_page_identity(tmp_path):
    validation = fixture(tmp_path)
    path = validation / "qwen36-validation.json"
    value = json.loads(path.read_text())
    value["runs"][0]["pages"][-1] = value["runs"][0]["pages"][0]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Repeated page identity"):
        polytonic_quality(tmp_path)


def test_release_rejects_changed_raw_prediction_or_report(tmp_path):
    validation = fixture(tmp_path)
    path = validation / "qwen36-validation.json"
    value = json.loads(path.read_text())
    value["runs"][0]["pages"][0]["raw_prediction"] = "changed"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="differs from raw predictions"):
        polytonic_quality(tmp_path)
    (validation / "raw/qwen36.jsonl").write_text("changed")
    with pytest.raises(ValueError, match="raw predictions changed"):
        polytonic_quality(tmp_path)
