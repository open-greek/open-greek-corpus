import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import prepare_photius_apparatus_review as review


@pytest.fixture
def completed(monkeypatch):
    # The decomposed mark makes Python/code-point offsets observably different
    # from UTF-8 byte offsets or a silently normalized reading.
    row = {"locus": review.PREFIX + "0069.1", "text": "α\u0313νθρωπος λέγει. a. 1. λόγος c.", "edition": "fixture"}
    monkeypatch.setattr(review, "historical_rows", lambda root=review.ROOT: {69: [row]})
    item = review.worksheet([69])
    item["reviewed_at"] = item["pages"][0]["reviewed_at"] = "2026-10-18"
    item["pages"][0]["evidence"] = "Printed footer compared with the exact body row."
    text = row["text"]; start = text.index("a. 1.")
    item["pages"][0]["rows"][0]["exclusions"] = [{"start": start, "end": len(text),
        "original_text": text[start:], "classification": "critical-apparatus",
        "source_region": [.1, .7, .9, .8], "evidence": "Small footer lemma and siglum."}]
    return item


def test_exact_unicode_span_preserves_body_and_completed_authority(completed):
    assert review.validate(completed, complete=True) is completed
    row = completed["pages"][0]["rows"][0]
    span = row["exclusions"][0]
    assert row["full_row_text"][:span["start"]] == "α\u0313νθρωπος λέγει. "
    assert span["start"] != len(row["full_row_text"][:span["start"]].encode())


def test_prepared_worksheet_does_not_claim_a_completed_review(completed):
    prepared = review.worksheet([69])
    assert prepared["reviewed_at"] is None
    assert prepared["pages"][0]["evidence"] == ""
    with pytest.raises(ValueError, match="completed date"):
        review.validate(prepared)


@pytest.mark.parametrize("change", ["text", "row_hash", "source_hash", "missing_row", "duplicate_row", "missing_page"])
def test_reject_changed_or_incomplete_source_identity(completed, change):
    item = copy.deepcopy(completed); page = item["pages"][0]; row = page["rows"][0]
    if change == "text": row["full_row_text"] = row["full_row_text"].replace("α\u0313", "ἀ")
    elif change == "row_hash": row["row_sha256"] = "0" * 64
    elif change == "source_hash": page["source_pdf_sha256"] = "0" * 64
    elif change == "missing_row": page["rows"] = []
    elif change == "duplicate_row": page["rows"].append(copy.deepcopy(row))
    elif change == "missing_page": item["pages"] = []
    with pytest.raises(ValueError): review.validate(item, complete=True)


@pytest.mark.parametrize("box", [[True,.7,.9,.8], [.9,.7,.1,.8], [.1,.8,.9,.7],
    [.1,.7,float("nan"),.8], [.1,.7,.9,float("inf")], [0,.7,1.1,.8]])
def test_reject_unsupported_source_regions(completed, box):
    completed["pages"][0]["rows"][0]["exclusions"][0]["source_region"] = box
    with pytest.raises(ValueError, match="source evidence"): review.validate(completed)


@pytest.mark.parametrize("change", ["byte_offset", "wrong_original", "overlap", "empty", "unknown_class", "no_evidence"])
def test_reject_unauditable_exclusion(completed, change):
    row = completed["pages"][0]["rows"][0]; span = row["exclusions"][0]
    if change == "byte_offset": span["start"] = len(row["full_row_text"][:span["start"]].encode())
    elif change == "wrong_original": span["original_text"] += "x"
    elif change == "overlap": row["exclusions"].append(copy.deepcopy(span))
    elif change == "empty": span["end"] = span["start"]
    elif change == "unknown_class": span["classification"] = "body"
    elif change == "no_evidence": span["evidence"] = ""
    with pytest.raises(ValueError): review.validate(completed)


def test_merge_cannot_hide_a_duplicate_reviewed_page(completed):
    completed["pages"].append(copy.deepcopy(completed["pages"][0]))
    with pytest.raises(ValueError, match="physical page"): review.validate(completed, complete=True)
