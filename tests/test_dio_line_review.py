from copy import deepcopy
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import scan_dio_line_reviews as review
from ocr_consensus import merge_witnesses


def fixture():
    _, authority = review.load_authority()
    witnesses = []
    for family, pair in authority["records"].items():
        raw = pair["finer"]
        meta = raw["metadata"]
        witnesses.append({"id": family, "model": meta["model"], "revision": meta["revision"],
            "text": raw["prediction"]["raw_prediction"] + "\nμὲν γὰρ τοῖς",
            "artifact_sha256": raw["artifact_sha256"], "vote_group": family,
            "preprocessing": [{"raw_strips": [raw["prediction"]]}]})
    page = {"id": review.PAGE, "work": "cassius-dio.historiae-romanae", "scan_page": 195,
        "region": [0,.4542,.5,.94]}
    source = {"sha256": review.SOURCE_SHA256, "url": "https://archive.org/reviewed.pdf"}
    return merge_witnesses(witnesses), page, source, witnesses


def test_named_review_preserves_raw_votes_and_restores_every_byte_of_network():
    raw, page, source, witnesses = fixture()
    original = deepcopy(raw)
    corrected, archive, audit = review.reviewed_line(raw, page, source, witnesses, "data/changes/networks.gz")
    assert raw == original and archive == (review.PAGE + ":raw-ocr", original)
    assert corrected["text"].startswith(review.LINE)
    assert corrected["analysis_text"].split()[:8] == review.WORDS[1:]
    assert not corrected["ocr_consensus"]["slots"][0]["lexical_eligible"]
    assert audit["eligibility"]["joined_spelling_invented"] is False
    assert len(corrected["ocr_consensus"]["witnesses"]) == 2
    assert review.unapply_review(corrected, archive[1]) == original
    damaged = deepcopy(archive[1]); damaged["text"] += " changed"
    with pytest.raises(ValueError, match="raw Dio network changed"):
        review.unapply_review(corrected, damaged)


def test_review_requires_exact_source_and_completed_raw_records():
    raw, page, source, witnesses = fixture()
    with pytest.raises(ValueError, match="source or panel changed"):
        review.reviewed_line(raw, page, {**source, "sha256": "changed"}, witnesses, "data/changes/networks.gz")
    changed = deepcopy(witnesses)
    changed[0]["preprocessing"][0]["raw_strips"][0]["raw_prediction"] += " changed"
    with pytest.raises(ValueError, match="reading changed"):
        review.reviewed_line(raw, page, source, changed, "data/changes/networks.gz")


def test_unrelated_line_remains_unchanged():
    raw, page, source, witnesses = fixture()
    assert review.reviewed_line(raw, {**page, "id": "another-page"}, source, witnesses,
        "data/changes/networks.gz") == (raw, None, None)


def test_late_transmission_keeps_epitomes_distinct_from_direct_text():
    from dio_transmission_reviews import reviewed_transmission, PINS
    page = {"work": "cassius-dio.historiae-romanae", "source_volume": 8,
        "transmission": "direct-text-with-excerpts-and-summaries"}
    assert reviewed_transmission(page, {"sha256": PINS[8]})[0] == "epitome-and-excerpts"
    assert reviewed_transmission({**page, "source_volume": 9}, {"sha256": PINS[9]})[0] == "mixed-direct-manuscript-excerpts-and-epitomes"
    assert reviewed_transmission({**page, "admission": "comparative-paratext"}, {"sha256": PINS[8]}) is None
    with pytest.raises(ValueError, match="transmission source changed"):
        reviewed_transmission(page, {"sha256": "changed"})
