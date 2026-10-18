import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_dio_early_body_regions as early
from scan_ocr_bundle import _relation


def test_second_review_preserves_all_late_jobs_and_only_retries_early_apparatus():
    base_raw, effective_raw, review_raw = early.BASE.read_bytes(), early.EFFECTIVE.read_bytes(), early.REVIEW.read_bytes()
    base, effective, review = json.loads(base_raw), json.loads(effective_raw), json.loads(review_raw)
    changed = _relation(base_raw, effective_raw, {early.sha(review_raw): review_raw})
    assert len(base["pages"]) == len(effective["pages"]) == 1500
    assert len(changed) == review["changed_early_regions"] == 279
    assert len(review["evidence"]) == review["reviewed_early_regions"] == 759
    assert [p for p in base["pages"] if p["source_volume"] >= 6] == [p for p in effective["pages"] if p["source_volume"] >= 6]
    assert all(p["source_volume"] in {1, 2} for p in effective["pages"] if p["id"] in changed)
    groups = early.shard_outputs(effective)
    assert list(map(len, groups)) == [140, 139]
    assert set(groups[0]).isdisjoint(groups[1]) and set(groups[0] + groups[1]) == changed
    for index, ids in enumerate(groups):
        assert json.loads((early.SHARDS / f"shard-{index:02d}.json").read_text()) == ids


def test_primary_paragraphs_and_latin_credits_survive_source_checked_overrides():
    base = {p["id"]: p for p in json.loads(early.BASE.read_text())["pages"]}
    effective = {p["id"]: p for p in json.loads(early.EFFECTIVE.read_text())["pages"]}
    for identifier in ["dio-cary-v1-pdf0050-fragment", "dio-cary-v1-pdf0078-comparison",
            "dio-cary-v2-pdf0098-comparison", "dio-cary-v2-pdf0196-fragment"]:
        assert effective[identifier] == base[identifier]
    assert effective["dio-cary-v1-pdf0137-fragment"]["region"][-1] > .7924
    assert effective["dio-cary-v2-pdf0218-fragment"]["region"][-1] > .77
    assert effective["dio-cary-v2-pdf0121-comparison"]["region"][-1] == .8445
    assert effective["dio-cary-v2-pdf0220-fragment"]["region"][-1] < .303
    assert effective["dio-cary-v2-pdf0232-fragment"]["region"][-1] < .3
