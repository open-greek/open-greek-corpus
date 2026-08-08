"""Guards on cutting a row at a character offset.

Two failure modes matter here and neither is caught by token conservation.

A wrong offset conserves every token and still files the wrong text under the
wrong author, so the cut is asserted against the head string that must sit AT
it and the text that must end the part before it. That is what these tests
exercise: a plausible-but-wrong offset has to be refused, not absorbed.

And a cut that lands inside a Greek run turns one token into two, which inflates
the corpus by exactly the number of cuts. It is small enough to look like noise
and permanent once published, so an offset that is not at a whitespace boundary
is refused before anything is written.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import split_carved_row as scr  # noqa: E402

TEXT = "τέλος τοῦ προτέρου. ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ Ἐπὶ Νέρωνος τοῦ Καίσαρος"
OFF = TEXT.index("ΜΑΡΤΥΡΙΟΝ")


def test_correct_cut_passes():
    scr.check_cut(TEXT, OFF, "ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ", "τοῦ προτέρου.", "ok")


def test_offset_drifted_to_the_next_word_is_refused():
    """Drift by one word. It lands on a clean boundary, so only the head test
    can catch it, which is the point of asserting the head separately."""
    off = TEXT.index("ΠΑΥΛΟΥ")
    assert TEXT[off - 1].isspace()
    with pytest.raises(SystemExit, match="expected the head"):
        scr.check_cut(TEXT, off, "ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ", "", "drifted")


def test_offset_drifted_inside_a_word_is_refused():
    with pytest.raises(SystemExit, match="not at a whitespace boundary"):
        scr.check_cut(TEXT, OFF + 2, "ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ", "", "drifted")


def test_cut_inside_a_word_is_refused_even_if_the_head_matches():
    """The head can still match at an offset that splits the previous word."""
    text = TEXT.replace("προτέρου. ΜΑΡΤΥΡΙΟΝ", "προτέρουΜΑΡΤΥΡΙΟΝ")
    off = text.index("ΜΑΡΤΥΡΙΟΝ")
    with pytest.raises(SystemExit, match="not at a whitespace boundary"):
        scr.check_cut(text, off, "ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ", "", "midword")


def test_wrong_preceding_text_is_refused():
    """Right head, wrong place: the same head printed twice in one volume."""
    with pytest.raises(SystemExit, match="should end with"):
        scr.check_cut(TEXT, OFF, "ΜΑΡΤΥΡΙΟΝ ΠΑΥΛΟΥ", "ἑτέρα ἀρχή.", "wrong copy")


def test_offset_past_the_end_is_refused():
    with pytest.raises(SystemExit, match="outside a row"):
        scr.check_cut(TEXT, len(TEXT) + 5, "", "", "past end")


def test_whitespace_cut_does_not_change_the_token_count():
    """Why the boundary rule exists: cutting mid-run would add a token."""
    assert scr.n_tok(TEXT[:OFF]) + scr.n_tok(TEXT[OFF:]) == scr.n_tok(TEXT)
    bad = TEXT.index("Νέρωνος") + 3
    assert scr.n_tok(TEXT[:bad]) + scr.n_tok(TEXT[bad:]) == scr.n_tok(TEXT) + 1
