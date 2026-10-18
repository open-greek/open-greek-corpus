import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ocr_consensus import merge_witnesses


def merge(left, right):
    return merge_witnesses([{"id": "a", "text": left, "artifact_sha256": "first"},
                            {"id": "b", "text": right, "artifact_sha256": "second"}])


def test_printed_page_end_fragment_keeps_hyphen_without_becoming_a_word():
    result = merge("τὰ ὅμο-\n", "τὰ ὅμο-\n")
    assert result["text"] == "τὰ ὅμο-"
    assert result["analysis_text"] == "τὰ"
    slot = result["ocr_consensus"]["slots"][-1]
    assert slot["selected"] == "ὅμο"
    assert slot["lexical_eligible"] is False
    assert slot["lexical_exclusion"] == "source-page-end-fragment"
    assert slot["terminal_fragment_support"] == ["a", "b"]


def test_one_lost_terminal_hyphen_does_not_license_a_fragment_as_a_word():
    result = merge("τὰ ὅμο-", "τὰ ὅμο")
    assert result["analysis_text"] == "τὰ"
    assert result["ocr_consensus"]["slots"][-1]["terminal_fragment_support"] == ["a"]


def test_complete_word_split_across_lines_inside_the_page_remains_countable():
    result = merge("τὰ ὁμο-\nγενῆ", "τὰ ὁμογενῆ")
    assert result["analysis_text"] == "τὰ ὁμογενῆ"
    assert result["ocr_consensus"]["slots"][-1]["lexical_eligible"] is True
