"""The syllable test behind data/nonfinal_graves.json.

It is vendored rather than imported, so that a published count cannot change
with whether a sibling checkout exists. That makes it a copy, and a copy needs a
test that it still agrees with what it was copied from.

The reason a syllable-aware test is needed at all, rather than "is there a grave
before the last vowel": Greek diphthongs are one syllable. ταὶς has two vowels
and one nucleus, so its grave IS final and the word is fine; a bare-vowel test
calls it a violation. Getting that wrong inflates a published defect count.
"""

import json
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

APPLIED = (Path(__file__).resolve().parent.parent / "data" / "corpus_changes"
           / "nonfinal_grave_tranche.applied.json")


def _applied() -> dict:
    """form -> target, from the repair that ran rather than the live class.

    These used to be asserted against data/nonfinal_graves.json's decided set.
    They have since been repaired out of the corpus, so that set no longer holds
    them and could not: the artifact measures what is still wrong. The decisions
    live in the audit, which is also what a reader would use to reverse them.
    """
    return json.loads(APPLIED.read_text(encoding="utf-8"))["substitutions"]


@pytest.mark.parametrize("form,target", [
    ("\u1f10\u03c0\u03b5\u1f76\u03b4\u1f74", "\u1f10\u03c0\u03b5\u03b9\u03b4\u03ae"),
    ("\u03bc\u1f74\u03c4\u03b5", "\u03bc\u03ae\u03c4\u03b5"),
    ("\u1f10\u03b3\u1f7c\u03b3\u03b5", "\u1f14\u03b3\u03c9\u03b3\u03b5"),
])
def test_the_counterexamples_were_repaired_to_the_right_word(form, target):
    """ἐπεὶδὴ is ἐπειδή, the grave dropped rather than moved; ἐγὼγε is ἔγωγε and
    not the attested-and-wrong ἐγώγε. These sank the four-shape rule and the
    repair had to get them right."""
    assert _applied().get(form) == target


@pytest.mark.parametrize("form", [
    "\u03c4\u1f70\u03bb\u03bb\u03b1",
    "\u1f70\u03bb\u03bb\u1f70",
    "\u03c4\u1f70\u03bd\u03b1\u03bd\u03c4\u03af\u03b1",
])
def test_the_ones_the_rule_must_refuse_were_not_repaired(form):
    """τἄλλα against τἆλλα; ἀλλά against ἄλλα, which shares its skeleton; and
    τὰναντία, whose repair moves a breathing and not only an accent."""
    assert form not in _applied()


def test_every_applied_repair_moved_only_an_accent():
    audits = sorted(APPLIED.parent.glob("nonfinal_grave_tranche*.applied.json"))
    assert len(audits) >= 3, "the applied audits are the record; where are they"
    for fp in audits:
        if "marks" in fp.name:
            continue  # that tranche moves breathings by design, and says so
        for f, t in json.loads(fp.read_text(encoding="utf-8"))["substitutions"].items():
            assert m.without_accents(f) == m.without_accents(t), (f, t)
            assert m.has_nonfinal_grave(f) and not m.has_nonfinal_grave(t)


COMPLETING = APPLIED.with_name(
    "nonfinal_grave_tranche_thirdparty.completing-2026-08-11.applied.json")


@pytest.mark.parametrize("form,target", [
    ("ὃροι", "ὅροι"),
    ("ἒστω", "ἔστω"),
])
def test_the_completing_pass_reached_below_the_sample_window(form, target):
    """ὃροι (share 1.0) and ἒστω (0.997) cleared the third-party bar on
    2026-08-10 and were not applied, because that sheet was generated from the
    artifact's 400-row decided sample by an uncommitted one-off. The completing
    apply must hold them: if they ever leave, a tranche was built from the
    sample again."""
    subs = json.loads(COMPLETING.read_text(encoding="utf-8"))["substitutions"]
    assert subs.get(form) == target
