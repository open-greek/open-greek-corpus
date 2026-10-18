import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_dio_body_regions as bodies
from scan_ocr_bundle import _relation


def artifacts():
    original_raw = bodies.ORIGINAL.read_bytes()
    effective_raw = bodies.EFFECTIVE.read_bytes()
    review_raw = bodies.REVIEW.read_bytes()
    return original_raw, effective_raw, review_raw


def test_complete_review_preserves_early_jobs_and_all_source_identities():
    original_raw, effective_raw, review_raw = artifacts()
    original, effective = json.loads(original_raw), json.loads(effective_raw)
    review = json.loads(review_raw)
    changed = _relation(original_raw, effective_raw, {bodies.sha(review_raw): review_raw})
    assert len(original["pages"]) == len(effective["pages"]) == 1500
    assert len(changed) == len(review["evidence"]) == 741
    assert [p for p in original["pages"] if p["source_volume"] < 6] == [p for p in effective["pages"] if p["source_volume"] < 6]
    assert len([p for p in effective["pages"] if p.get("prompt_suffix") == bodies.FINITE_DOT_SUFFIX]) == 15
    assert all(0 < p["region"][3] <= .91 for p in effective["pages"] if p["source_volume"] >= 6)


def test_full_page_review_retains_primary_quotations_and_separates_comparison():
    _, effective_raw, review_raw = artifacts()
    effective, review = json.loads(effective_raw), json.loads(review_raw)
    pages = {p["id"]: p for p in effective["pages"]}
    assert pages["dio-cary-v8-pdf0078"]["region"][-1] == .91
    assert pages["dio-cary-v9-pdf0242"]["region"][-1] >= .86
    assert pages["dio-cary-v7-pdf0187"]["region"][-1] < .242
    assert pages["dio-cary-v9-pdf0123"]["region"][-1] < .42
    assert pages["dio-cary-v9-pdf0174"]["region"][-1] < .4
    held = review["held_comparison_regions"][0]
    assert held["classification"] == "comparative-quotation"
    comparison = json.loads(bodies.COMPARISON.read_text())
    assert comparison == bodies.comparison_manifest(effective, review)
    assert comparison["pages"][0]["admission"] == "comparative-paratext"
    assert len(held["credits"]) == 2


def test_review_authority_rejects_unreviewed_prompt_or_source_change():
    original_raw, effective_raw, review_raw = artifacts()
    effective = json.loads(effective_raw)
    effective["prompt"] += " silently changed"
    with pytest.raises(ValueError, match="other manifest fields"):
        _relation(original_raw, bodies.encode(effective), {bodies.sha(review_raw): review_raw})
    effective = json.loads(effective_raw)
    next(p for p in effective["pages"] if p.get("prompt_suffix"))["prompt_suffix"] += " changed"
    with pytest.raises(ValueError, match="source-reviewed evidence"):
        _relation(original_raw, bodies.encode(effective), {bodies.sha(review_raw): review_raw})
