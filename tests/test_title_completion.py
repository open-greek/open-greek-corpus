"""Restoring a truncated title from the crosswalk (issue #24).

The vendored Canon cuts titles: 84 of the 86 that end mid-parenthesis are
already cut in work_inventory.json before our code reads them. Where the
crosswalk holds the same title whole, it wins. The danger is the fold, which
drops case, diacritics and punctuation so the two sources can be compared at
all, and which is loose enough to match titles that are not repairs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_work_index import _completes, _fold_words, _unbalanced  # noqa: E402


def test_a_restored_tail_is_accepted():
    assert _completes(
        "Catena In Epistulam Ad Colossenses (Typus Parisinus) (E Cod",
        "Catena In Epistulam Ad Colossenses (Typus Parisinus) (E Cod. Coislin. 204)")


def test_case_and_diacritics_do_not_block_it():
    """The two sources disagree on both, which is why the fold drops them."""
    assert _completes(
        "Scholia Et Glossae In Nicandri Theriaca (Scholia Vetera Et",
        "Scholia et glossae in Nicandri theriaca (scholia vetera et recentiora)")


def test_a_longer_title_that_is_not_a_repair_is_refused():
    """`De Usu Partium` is complete. The crosswalk's longer form is a different
    citation of the work, not its restored tail, and swapping it in would also
    undo the Title-Case convention."""
    assert not _unbalanced("De Usu Partium")
    # the caller gates on _unbalanced, so this never reaches _completes; assert
    # the gate itself, since that is what stops it
    assert _completes("De Usu Partium", "De usu partium corporis humani I-XI")


def test_a_different_scope_is_refused_by_the_prefix_test():
    """Not every longer title extends the shorter one word for word."""
    assert not _completes("Epistulae", "Decretum, Orationes, Epistulae")


def test_a_candidate_that_is_itself_truncated_is_refused():
    assert not _completes("Catena In Epistulam Ad Colossenses (E Cod",
                          "Catena In Epistulam Ad Colossenses (E Cod. Coislin")


def test_a_different_work_cannot_take_its_place():
    assert not _completes("Homiliae In Job (Fragmenta In Catenis",
                          "Selecta In Job (Fragmenta In Catenis, Typus I)")


def test_an_equal_title_is_not_an_extension():
    assert not _completes("Fragmenta (Ex Incerto Libro)", "Fragmenta (ex incerto libro)")


def test_the_fold_keeps_greek_and_drops_punctuation():
    assert _fold_words("(= Περὶ διαφόρους)") == ["περι", "διαφορους"]


def test_a_square_bracket_counts_as_truncation_too():
    """The Canon uses brackets for editorial qualifiers, and exactly one served
    title is cut inside one rather than inside a parenthesis."""
    assert _unbalanced("Περὶ νοήσεως καὶ αἰσθήσεως. [ὅτι ἐν μόνῳ τῷ θεῷ τὸ")
    assert not _unbalanced("In Aristotelis Libros De Anima Commentaria [Sp.?]")


def test_a_corrupted_title_is_not_treated_as_merely_truncated():
    """The crosswalk still holds `Recensio ιἰ` from before the beta-code
    decoder was fixed, where the CTS metadata has `Recensio ii`. Greek iotas
    are not Latin ones, so the prefix test refuses it, and it should: making
    the fold equate homoglyphs would weaken the test across every entry to
    repair a single title."""
    assert not _completes(
        "Catena In Marcum (Recensio ιἰ (E Codd. Oxon. Bodl. Laud. 33",
        "Catena In Marcum (Recensio ii) (E Codd. Oxon. Bodl. Laud. 33 + Paris. gr. 178)")
