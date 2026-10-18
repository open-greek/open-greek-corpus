import copy
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from photius_retries import encode, validate_retry_metadata
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
