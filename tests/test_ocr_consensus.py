"""Votes retain disagreements and can reconstruct every supplied OCR witness."""
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ocr_consensus import merge_witnesses, tokenize
from frequency_projection import lexical_text
from repair_meibom_work_assignments import page_assignment, fresh_jobs, manifest


def witness(identifier, text, artifact=None):
    return {"id": identifier, "text": text,
        "artifact_sha256": artifact or hashlib.sha256(identifier.encode()).hexdigest()}


def test_shared_words_count_once_and_losing_readings_remain_reversible():
    inputs = [witness("a", "ὁ δὲ λόγος σαφής."), witness("b", "ὁ δὲ λόγος σαφής."),
        witness("c", "ὁ δὲ λόγος σοφός.")]
    result = merge_witnesses(inputs)
    assert result["analysis_text"] == "ὁ δὲ λόγος σαφής"
    assert {w["id"]: w["text"] for w in result["ocr_consensus"]["witnesses"]} == {
        w["id"]: w["text"] for w in inputs}
    assert any(r["text"] == "σοφός" for slot in result["ocr_consensus"]["slots"] for r in slot["readings"])


def test_tie_has_all_readings_and_contributes_no_arbitrary_scalar_token():
    result = merge_witnesses([witness("a", "ὁ δὲ λόγος σαφής."),
        witness("b", "ὁ δὲ λόγος σοφός.")])
    assert result["analysis_text"] == "ὁ δὲ λόγος"
    slot = result["ocr_consensus"]["slots"][-1]
    assert slot["selected"] is None
    assert slot["tied_readings"] == ["σαφής", "σοφός"]
    assert lexical_text(result) == "ὁ δὲ λόγος"


def test_short_witness_abstains_outside_its_coverage_instead_of_deleting_text():
    result = merge_witnesses([witness("a", "ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς"),
        witness("b", "ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς"),
        witness("c", "λόγος ἔχει")])
    assert result["analysis_text"] == "ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς"
    assert result["ocr_consensus"]["slots"][-1]["abstentions"] == ["c"]


def test_an_interior_omission_votes_but_is_not_invented_at_the_end():
    result = merge_witnesses([witness("a", "ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς"),
        witness("b", "ὁ δὲ λόγος ἔχει πάντα καλῶς")])
    slot = next(slot for slot in result["ocr_consensus"]["slots"]
        if any(reading["text"] == "ταῦτα" for reading in slot["readings"]))
    assert slot["tied_readings"] == ["", "ταῦτα"]
    assert "ταῦτα" not in result["analysis_text"]


def test_duplicate_raw_artifact_cannot_cast_two_votes():
    one = witness("a", "λόγος σαφής")
    duplicate = witness("b", "λόγος σαφής", artifact=one["artifact_sha256"])
    other = witness("c", "λόγος σοφός")
    result = merge_witnesses([one, duplicate, other])
    assert len(result["ocr_consensus"]["witnesses"]) == 2
    assert result["ocr_consensus"]["slots"][-1]["status"] == "unresolved"
    with pytest.raises(ValueError, match="conflicting"):
        merge_witnesses([one, witness("b", "σοφός", artifact=one["artifact_sha256"])])


def test_duplicate_scan_readings_from_one_run_cast_one_group_vote():
    a, b = witness("a", "λόγος σαφής"), witness("b", "λόγος σαφής")
    a["vote_group"] = b["vote_group"] = "same-run"
    result = merge_witnesses([a, b, witness("c", "λόγος σοφός")])
    assert result["ocr_consensus"]["slots"][-1]["status"] == "unresolved"


def test_input_order_does_not_choose_a_different_reading():
    inputs = [witness("a", "ὁ λόγος σαφής"), witness("b", "ὁ λόγος σοφός")]
    assert merge_witnesses(inputs) == merge_witnesses(list(reversed(inputs)))


def test_orthographic_alignment_does_not_flatten_accents_in_votes():
    result = merge_witnesses([witness("a", "θεός"), witness("b", "θεὸς")])
    assert result["analysis_text"] == ""
    assert set(result["ocr_consensus"]["slots"][0]["tied_readings"]) == {"θεός", "θεὸς"}
    assert tokenize("λόγος Latin λέ-\nγεται.") == [("λόγος", "λόγος"), ("λέγεται", "λέγεται.")]


def test_mixed_script_words_remain_whole_opaque_readings():
    assert tokenize("ἀνдрῶν εἰρῆkenai.") == [("ἀνдрῶν", "ἀνдрῶν"), ("εἰρῆkenai", "εἰρῆkenai.")]
    result = merge_witnesses([witness("a", "λόγος ἀνдрῶν εἰρῆkenai."),
        witness("b", "λόγος ἀνдрῶν εἰρῆkenai.")])
    assert result["text"] == "λόγος ἀνдрῶν εἰρῆkenai."
    assert result["analysis_text"] == "λόγος"
    assert result["ocr_consensus"]["counts"]["damaged-reading"] == 2
    assert all(not slot["lexical_eligible"] for slot in result["ocr_consensus"]["slots"][1:])
    assert not any(reading["text"] in {"ἀν", "ῶν", "εἰρῆ"}
        for slot in result["ocr_consensus"]["slots"] for reading in slot["readings"])


def test_mixed_and_pure_greek_readings_tie_without_silent_script_repair():
    result = merge_witnesses([witness("a", "ἀνдрῶν"), witness("b", "ἀνδρῶν")])
    assert result["analysis_text"] == ""
    assert result["ocr_consensus"]["slots"][0]["tied_readings"] == ["ἀνδρῶν", "ἀνдрῶν"]


def test_all_aristides_printed_pages_have_one_fresh_job_and_correct_column():
    jobs = fresh_jobs()["pages"]
    assert sorted(page["printed_page"] for page in jobs) == list(range(1, 165))
    assert len({p["scan_page"] for p in jobs}) == 164
    assert all((p["printed_page"] % 2 == 1) == (p["greek_column"] == "left") for p in jobs)
    assert page_assignment(60)["class"] == "blank_scan"
    assert page_assignment(701)["work"] == "paratext"
    assert page_assignment(201)["work"] == "cleonides.introductio-harmonica"
    assert page_assignment(223)["work"] == "euclides-geom.sectio-canonis-sp"
    assert page_assignment(614)["printed_page"] == page_assignment(608)["printed_page"] == 84
    assert page_assignment(650)["printed_page"] == page_assignment(644)["printed_page"] == 114
    assert page_assignment(700)["printed_page"] == 164
