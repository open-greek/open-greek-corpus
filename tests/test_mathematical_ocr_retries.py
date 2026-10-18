import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("math_retry_prepare", ROOT / "scripts/prepare_mathematical_ocr_retries.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_committed_request_pins_originals_and_source_review():
    request = json.loads((ROOT / prepare.OUTPUT).read_text())
    assert request["retry_of"]["sha256"] == prepare.MANIFEST_SHA256
    assert request["retry_of"]["original_predictions_sha256"] == prepare.ORIGINAL_SHA256
    assert request["retry_of"]["model"] == prepare.MODEL
    assert request["retry_of"]["revision"] == prepare.REVISION
    assert len(request["pages"]) == 15
    assert set(request["review"]["findings"]) == set(prepare.REGIONS)
    for identifier, regions in prepare.REGIONS.items():
        jobs = [p for p in request["pages"] if p["reconstructs"] == identifier]
        assert [p["reading_order"] for p in jobs] == [1, 2, 3]
        assert [p["region"] for p in jobs] == regions
        assert all(p["max_side"] == 3200 for p in jobs)
        finding = request["review"]["findings"][identifier]
        assert finding["original_text"]
        assert len(finding["original_image_sha256"]) == 64
        assert len(finding["original_prediction_sha256"]) == 64
        assert finding["source_pdf_sha256"] == request["sources"][jobs[0]["source"]]["sha256"]


def test_reprepare_rejects_changed_original_request(tmp_path):
    original = tmp_path / "manifest.json"
    predictions = tmp_path / "predictions.jsonl"
    original.write_text("{}")
    predictions.write_text("{}")
    with pytest.raises(ValueError, match="Original mathematical"):
        prepare.prepare(original, predictions, tmp_path, tmp_path / "retry.json")
    assert not (tmp_path / "retry.json").exists()
