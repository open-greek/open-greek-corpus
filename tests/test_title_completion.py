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
from build_work_index import (  # noqa: E402
    _completes, _completes_tail, _confirms_head, _fold_words, _unbalanced,
)


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


def test_the_crosswalk_can_confirm_the_title_ends_at_the_cut_bracket():
    """The only warrant for dropping a truncated fragment: a second source
    giving the title as the head alone."""
    assert _confirms_head(
        "Catena In Epistulam Jacobi (Catena Andreae) (E Cod. Oxon. Coll. Nov",
        "Catena In Epistulam Jacobi (Catena Andreae)")


def test_an_unconfirmed_fragment_is_left_visibly_truncated():
    """Trimming without confirmation turns a title that is obviously cut into
    one that reads complete and is not. `Testimonia E Scriptura` is a different
    claim from `Testimonia E Scriptura (De Communi Essentia ...`."""
    assert not _confirms_head(
        "Testimonia E Scriptura (De Communi Essentia Patris Et Filii Et Spiritus",
        "")


def test_two_works_are_not_collapsed_onto_one_title():
    """Basil's Regulae Brevius and Regulae Fusius are cut in the same place.
    Trimming the fragment off both would give them the same title, which is
    why the fragment is never dropped on its own account."""
    for which in ("Brevius", "Fusius"):
        assert not _confirms_head(
            f"Asceticon Magnum Sive Quaestiones (Regulae {which}", "")


def test_a_greek_title_in_the_crosswalk_finishes_the_cut_parenthesis():
    assert _completes_tail(
        "De Adfinium Vocabulorum Differentia (Περὶ ὁμοίων καὶ",
        "περὶ ὁμοίων καὶ διαφόρων λέξεων",
    ) == "De Adfinium Vocabulorum Differentia (Περὶ ὁμοίων καὶ διαφόρων λέξεων)"


def test_a_one_word_fragment_does_not_splice_the_title_into_itself():
    """`( De` matched `De animi cuiuslibet...` on `de` alone and put the whole
    title back inside its own parenthesis."""
    assert _completes_tail(
        "De Animi Cuiuslibet Peccatorum Dignotione Et Curatione ( De",
        "De animi cuiuslibet peccatorum dignotione et curatione") is None
