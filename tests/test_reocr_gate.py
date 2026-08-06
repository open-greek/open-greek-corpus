"""The ingest gate that let a shredded re-OCR replace five Walz volumes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ingest_held_reocr import reading_order_regressed  # noqa: E402


def rows(texts):
    return [{"text": t} for t in texts]


# One page of running text against the same page read as two columns of stubs,
# which is what the masked run did to Walz scan 0016 of v4.
WHOLE = rows(["τῇ δόξῃ· ὥσπερ γὰρ ἡ δόξα ἄνευ λόγου προέχεται, οὕτω καὶ ἡ "
              "ἐμπειρία αἰτίας τῶν ὑποκειμένων αὐτῇ πραγμάτων οὐκ ἐπίσταται."] * 40)
SHREDDED = rows(["λογεῖ τῇ δόξῃ·", "ται, οὕτω καὶ", "πραγμάτων οὐκ",
                 "τί τρεῖς εἰσι γνω", "τὰ λόγου γιγνώ"] * 40)


def test_the_swap_this_gate_exists_for_is_refused():
    regressed, note = reading_order_regressed(WHOLE, SHREDDED)
    assert regressed, note


def test_a_lexicon_is_not_shredded_just_because_its_rows_are_short():
    """Photius went 30.3% -> 56.1% short-row mass in the same run and is fine:
    its rows end at word boundaries and it multiplied rows only 1.65x. Short
    rows alone must not condemn a work, which is why the row multiplier is
    required as well."""
    short = rows(["ἀείνως.", "ἄλυτον.", "ἀνεψιαδός.", "ἀδύρ."] * 100)
    more = rows(["ἀείνως.", "ἄλυτον.", "ἀνεψιαδός.", "ἀδύρ.", "ἀθέμισα."] * 130)
    regressed, note = reading_order_regressed(short, more)
    assert not regressed, note


def test_an_unchanged_text_passes():
    regressed, _ = reading_order_regressed(WHOLE, WHOLE)
    assert not regressed


def test_the_reverse_direction_is_not_flagged():
    """Repairing a shredded text is exactly what we want to allow."""
    regressed, _ = reading_order_regressed(SHREDDED, WHOLE)
    assert not regressed


def test_the_note_carries_both_numbers_a_reviewer_needs():
    _, note = reading_order_regressed(WHOLE, SHREDDED)
    assert "short-row mass" in note and "rows" in note and "x" in note
