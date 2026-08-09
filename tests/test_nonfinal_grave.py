"""The syllable test behind data/nonfinal_graves.json.

It is vendored rather than imported, so that a published count cannot change
with whether a sibling checkout exists. That makes it a copy, and a copy needs a
test that it still agrees with what it was copied from.

The reason a syllable-aware test is needed at all, rather than "is there a grave
before the last vowel": Greek diphthongs are one syllable. ταὶς has two vowels
and one nucleus, so its grave IS final and the word is fine; a bare-vowel test
calls it a violation. Getting that wrong inflates a published defect count.
"""

import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import measure_nonfinal_graves as m  # noqa: E402

GREEK_OCR = Path.home() / "Documents" / "greek-ocr" / "scripts"


@pytest.mark.parametrize("word,bad", [
    ("ἐπεὶδὴ", True),        # grave on the penult, the largest real case
    ("μὴτε", True),
    ("ταὶς", False),         # diphthong: one nucleus, the grave is final
    ("καὶ", False),
    ("τὸ", False),
    ("ἄνθρωπος", False),     # acute, not a grave
    # Diaeresis splits ἀι into two nuclei, so this word has three (α, ι, η) and
    # its grave sits on the last of them: final, and legal. I first wrote this
    # case down as a violation and the code was right and I was wrong.
    ("ἀΐδὴς", False),
])
def test_known_cases(word, bad):
    assert m.has_nonfinal_grave(word) is bad


def test_single_syllable_is_never_a_violation():
    for w in ("τὸ", "γὰρ", "μὲν", "δὲ"):
        assert not m.has_nonfinal_grave(w)


def test_shapes_are_plural_and_exclude_the_form_itself():
    sh = m.shapes("ἐπεὶδὴ")
    assert sh["dropped"] == "ἐπειδὴ"
    assert sh["acute"] == "ἐπείδὴ"
    assert len({v for v in sh.values()}) > 1


@pytest.mark.skipif(not (GREEK_OCR / "corrections.py").exists(),
                    reason="greek-ocr checkout not present")
def test_agrees_with_the_implementation_it_was_copied_from():
    sys.path.insert(0, str(GREEK_OCR))
    import corrections  # noqa: E402

    def ref(tok: str) -> bool:
        n, acc = corrections.accent_positions(tok)
        return any(mark == "̀" for k, mark in acc.items() if k != 1)

    words = ["ἐπεὶδὴ", "μὴτε", "ταὶς", "καὶ", "τὸ", "ἄνθρωπος", "τὰλλα",
             "ἐγὼγε", "τὰναντία", "οὐδὲς", "ἀΐδὴς", "εὐθὺς", "ποιὲω"]
    mine = [m.has_nonfinal_grave(w) for w in words]
    theirs = [ref(w) for w in words]
    assert mine == theirs, [w for w, a, b in zip(words, mine, theirs) if a != b]


# The skeleton class: which clean Greek word has these letters. The four-shape
# space could not decide these, which is the whole reason this exists, so the
# outcomes are pinned. Two of them must stay REFUSED; a rule that decides τὰλλα
# is a rule that will decide anything.
def _decided():
    import json
    fp = Path(__file__).resolve().parent.parent / "data" / "nonfinal_graves.json"
    rows = json.loads(fp.read_text(encoding="utf-8"))["skeleton_class"]["decided"]
    return {r["form"]: r for r in rows}


@pytest.mark.parametrize("form,target", [
    ("ἐπεὶδὴ", "ἐπειδή"),     # the grave is DROPPED, not moved
    ("μὴτε", "μήτε"),
    ("ἐγὼγε", "ἔγωγε"),       # not ἐγώγε, which is attested and wrong
    ("τὰναντία", "τἀναντία"),  # not τάναντία, likewise
])
def test_the_counterexamples_that_sank_the_four_shape_rule_are_decided(form, target):
    d = _decided()
    assert form in d, f"{form} is no longer in the decided set"
    assert d[form]["target"] == target
    assert d[form]["share"] >= 0.90


@pytest.mark.parametrize("form", ["τὰλλα", "ὰλλὰ"])
def test_the_ambiguous_ones_stay_refused(form):
    """τἄλλα against τἆλλα, and ἀλλά against ἄλλα, which shares its skeleton."""
    assert form not in _decided(), f"{form} should not be decided by this rule"


def test_the_tranche_never_moves_a_breathing_or_iota_subscript():
    import json
    fp = (Path(__file__).resolve().parent.parent / "data"
          / "nonfinal_grave_tranche.json")
    rows = json.loads(fp.read_text(encoding="utf-8"))["rows"]
    assert rows, "the tranche is empty"
    for r in rows:
        assert r["accent_only"], r["form"]
        assert m.without_accents(r["form"]) == m.without_accents(r["target"])
