import copy
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from photius_retries import encode, sha, validate_retry_metadata, confirmed_mark_stripping
from prepare_photius_retries import CHECKPOINT38, build_supplement
from prepare_photius_coverage import build
from run_reviewed_scan_retry import metadata


def provider_metadata():
    request = build_supplement(113, "right-first-part02")
    args = SimpleNamespace(**CHECKPOINT38, max_tokens=6000)
    return request, metadata(args, encode(request), request, dict(CHECKPOINT38))


def test_provider_retry_requires_its_exact_published_runner_policy_and_runtime():
    request, meta = provider_metadata()
    validate_retry_metadata(meta, request)
    validate_retry_metadata({"temperature": 0}, request)
    for field, value in [("runner_sha256", "0" * 64), ("image_helper_sha256", "0" * 64),
                         ("temperature", 0), ("manifest_archive", "different.json"),
                         ("max_tokens", 0), ("backend", "other")]:
        with pytest.raises(ValueError, match="published authority"):
            validate_retry_metadata({**meta, field: value}, request)
    for field in ["presence_penalty", "seed", "top_k"]:
        altered = copy.deepcopy(meta)
        altered["generation_policy"][field] += 1
        with pytest.raises(ValueError, match="published authority"):
            validate_retry_metadata(altered, request)
    with pytest.raises(ValueError, match="published authority"):
        validate_retry_metadata({**meta, "runtime": {**CHECKPOINT38, "revision": "other"}}, request)
    with pytest.raises(ValueError, match="published authority"):
        validate_retry_metadata(meta, build())
    with pytest.raises(ValueError, match="Unknown retry decoding"):
        validate_retry_metadata({"temperature": .7}, request)


def test_exact_mark_exception_can_pin_partial_breathing_loss_without_relaxing_the_frozen_rule():
    import json
    from report_polytonic_loss import POLICY, detect
    row = {"raw_prediction": "ὁ " + "λογος σαφης και καλος εστιν. " * 30, "finish_reason": "stop"}
    line = json.dumps(row, ensure_ascii=False).encode()
    raw = b'{"_meta":{}}\n' + line + b"\n"
    measured = detect(row["raw_prediction"])
    assert measured["flag"] and measured["breathing_letters"] == 1
    condition = {"kind": "source-confirmed-polytonic-mark-stripping", "raw_file_sha256": sha(raw),
        "prediction_record_sha256": sha(line), "raw_prediction_sha256": sha(row["raw_prediction"].encode()),
        "finish_reason": "stop", "frozen_policy_sha256": sha(encode(POLICY)),
        "greek_letters": measured["greek_letters"], "breathing_letters": 1}
    assert confirmed_mark_stripping({"replacement_condition": condition}, raw, line, row)
    assert not confirmed_mark_stripping({"replacement_condition": {**condition, "breathing_letters": 0}}, raw, line, row)
    assert not confirmed_mark_stripping({"replacement_condition": condition}, raw + b" ", line, row)
