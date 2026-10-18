import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_dio_ocr_retries as retry


def test_committed_retry_scope_preserves_every_pinned_original():
    manifest_raw = (ROOT / retry.MANIFEST).read_bytes()
    assert hashlib.sha256(manifest_raw).hexdigest() == retry.MANIFEST_SHA256
    pages = {p["id"]: p for p in json.loads(manifest_raw)["pages"]}
    expected_counts = {"qwen36": (14, 14), "qwen38": (18, 16)}
    for family, (total, failures) in expected_counts.items():
        request = json.loads((ROOT / retry.DIRECTORY / f"cassius-dio-{family}-retry-jobs.json").read_bytes())
        originals = request["review"]["original_predictions"]
        assert set(originals) == set(retry.ORIGINAL_PINS[family])
        assert len(originals) == total
        assert sum(pin["original_prediction"]["finish_reason"] == "length" for pin in originals.values()) == failures
        assert len(request["pages"]) == 3 * total
        for identifier, pin in originals.items():
            assert retry.sha(retry.encode({"metadata": pin["original_metadata"],
                "prediction": pin["original_prediction"]})) == retry.ORIGINAL_PINS[family][identifier]
            assert pin["original_prediction"]["region"] == pages[identifier]["region"]
            assert pin["source_evidence"]


def test_reviewed_strips_are_contiguous_and_retain_bottom_boundary():
    pages = {p["id"]: p for p in json.loads((ROOT / retry.MANIFEST).read_bytes())["pages"]}
    assert len(retry.REGIONS) == 20
    for identifier, regions in retry.REGIONS.items():
        assert len(regions) == 3
        assert regions[0][1] == .065
        assert regions[-1][3] == pages[identifier]["region"][3]
        for region in regions:
            assert region[0] == .04 and region[2] == .47
            assert region[1] < region[3]
        assert regions[0][3] == regions[1][1]
        assert regions[1][3] == regions[2][1]


def test_changed_original_record_cannot_match_a_reviewed_artifact(tmp_path):
    family = "qwen38"
    request = json.loads((ROOT / retry.DIRECTORY / f"cassius-dio-{family}-retry-jobs.json").read_bytes())
    identifier, pin = next(iter(request["review"]["original_predictions"].items()))
    row = {**pin["original_prediction"], "raw_prediction": "changed"}
    path = tmp_path / "changed.jsonl"
    path.write_text(json.dumps({"_meta": pin["original_metadata"]}) + "\n" + json.dumps(row) + "\n")
    assert retry.ORIGINAL_PINS[family][identifier] not in retry.load_originals([path])
    with pytest.raises(ValueError, match="Repeated original"):
        retry.load_originals([path, path])


def test_changed_complete_manifest_is_rejected_before_any_output(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_bytes((ROOT / retry.MANIFEST).read_bytes() + b" ")
    with pytest.raises(ValueError, match="complete reviewed Dio manifest changed"):
        retry.prepare(path, [], tmp_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()
