"""Issue #35: the spacing marks that were becoming lemmas.

U+1FBF and U+1FFE sit inside the Greek block, so _GK reads them as Greek. A bare
one became a lemma holding over a thousand tokens, and a mark welded to a real
word minted a lemma beside that word's own. Cisco's call on 2026-08-11 was that
this is a tokenizer problem and not a text one, so nothing in data/corpus moves
and the fix is in the lemma pipeline.

What the issue warns about, and what these assert: ᾿ς and ᾿κ are genuine
aphaeresis in the Byzantine vernacular, where the mark IS the elided syllable,
so stripping it gives a different word. The discriminator is
measure_spacing_marks.classify, shared with the measurement rather than
reimplemented here.
"""

import collections
import gzip
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_work_lemma_counts import spacing_mark_forms  # noqa: E402
from measure_spacing_marks import classify, PSILI, DASIA  # noqa: E402

TABLE = REPO / "data" / "work_lemma_counts.tsv.gz"


@pytest.mark.parametrize("form,dropped,alias", [
    ("᾿", True, None),                  # a bare mark is not a word
    ("῾", True, None),
    ("᾿᾿", True, None),
    ("῾τὸ", False, "τὸ"),               # quotation mark welded to a real word
    ("῾ὁ", False, "ὁ"),
    ("῾ἔστι᾿", False, "ἔστι"),          # both ends: with the closer it reached ἑστία
    ("῾ποτέ᾿", False, "ποτέ"),          # and this one reached ποτέω
    ("῾῾ὡς", False, "ὡς"),              # doubled: one strip leaves ῾ὡς
    ("᾿᾿Ἀργος᾿", False, "Ἀργος"),
    # Left alone, and the issue is explicit about why: the mark is the elided
    # syllable and stripping it produces a different word.
    ("᾿ς", False, None),
    ("᾿κ", False, None),
    # U+1FBD koronis is a different character. Elided forms must not be touched.
    ("δ᾽", False, None),
])
def test_spacing_mark_forms(form, dropped, alias):
    drop, al = spacing_mark_forms([form])
    assert (form in drop) is dropped
    assert al.get(form) == alias


def _mark_lemmas():
    if not TABLE.exists():
        pytest.skip("lemma table not built in this tree")
    out = collections.Counter()
    with gzip.open(TABLE, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[1] and p[1][0] in (PSILI, DASIA):
                out[p[1]] += int(p[2])
    return out


def test_no_lemma_is_a_bare_mark_or_a_quoted_word():
    """The two classes #35 names are gone from the published table."""
    by = collections.Counter()
    for lem, n in _mark_lemmas().items():
        by[classify(lem)] += n
    assert by["punctuation_only"] == 0
    assert by["quotation_mark"] == 0


def test_aphaeresis_lemmas_survive():
    """Removing these would be the failure mode the issue warns about."""
    by = collections.Counter()
    for lem, n in _mark_lemmas().items():
        by[classify(lem)] += n
    assert by["aphaeresis"] > 0
