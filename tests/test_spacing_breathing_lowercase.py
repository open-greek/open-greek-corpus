"""The lowercase half of the spacing-breathing composition, issue #35.

Composing a spacing breathing onto the letter after it is a Unicode identity:
the page prints one letter with a breathing, our bytes hold two characters. It
changes the encoding and never the reading, which is why it needs a lower bar
than a repair that picks a different word. The bar it does need is that the mark
really is that letter's breathing, and three gates carry that: a precomposed
character has to exist, the letter must not be upsilon or rho under a psili
(both take the rough breathing), and the composed form has to be attested in the
non-OCR text. Without the last one ῾οὺκ composes to ὁὺκ, which is not a word.
"""

import json
import sys
import unicodedata
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_public_corpus import _GK  # noqa: E402
import compose_spacing_breathings as cs  # noqa: E402
from measure_spacing_marks import classify  # noqa: E402

AUDIT = (REPO / "data" / "corpus_changes"
         / "spacing-breathing-composition.lowercase.json")


def _audit():
    if not AUDIT.exists():
        pytest.skip("the lowercase composition is not applied in this tree")
    return json.loads(AUDIT.read_text(encoding="utf-8"))


@pytest.mark.parametrize("word,composed", [
    ("῾η", "ἡ"),
    ("᾿επειδὴ", "ἐπειδὴ"),
    ("῾ιεροσολύμων", "ἱεροσολύμων"),
    ("῾ρ", "ῥ"),
    # No precomposed character: capital upsilon and rho with psili. Left whole
    # rather than half-normalized into letter plus combining mark.
    ("᾿Υπόθεσις", None),
    ("᾿Ρωμαίοις", None),
])
def test_compose_word(word, composed):
    assert cs.compose_word(word) == composed


def test_composition_does_not_fix_the_example_the_issue_gives():
    """#35 says ῾υμετἑρα is ὑμετέρα. Composing gets the breathing and leaves the
    accent, so that token is not in this class's 64 and the issue overstates
    what composing does."""
    assert cs.compose_word("῾υμετἑρα") == "ὑμετἑρα"
    assert cs.compose_word("῾υμετἑρα") != "ὑμετέρα"


def test_every_substitution_recorded_was_a_breathing_and_is_now_composed():
    rec = _audit()
    for pair in rec["distinct_substitutions"]:
        was, now = pair.split(" -> ")
        assert classify(was) == "uncomposed_breathing"
        assert cs.compose_word(was) == now
        # one token before, one token after, and one character shorter
        assert len(_GK.findall(now)) == 1
        assert len(now) == len(was) - 1


def test_the_composed_forms_are_gone_from_the_corpus():
    """Read the rows, not the audit: the point is what the corpus now holds."""
    rec = _audit()
    gone = {p.split(" -> ")[0] for p in rec["distinct_substitutions"]}
    for blk in rec["files"]:
        text = (REPO / blk["file"]).read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            for w in _GK.findall(json.loads(line).get("text") or ""):
                assert w not in gone, f"{w} still served in {blk['file']}"


def test_held_back_classes_are_still_held_back():
    rec = _audit()
    held = rec["held_back"]
    assert held["no precomposed character"] == 250
    assert held["psili on upsilon or rho, which take the rough breathing"] == 5
    assert held["composed form attested nowhere in the non-OCR text"] == 53
