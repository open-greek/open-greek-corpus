"""The two-signal test that separates transliterated Latin from Greek.

Either signal alone convicts the wrong text. Unaccented is not Latin: this
corpus is full of unaccented display heads and all-caps OCR. Latin-shaped tokens
are not Latin either, once OCR has chewed a Greek word into ιν or ετ. The pair
is what works, and these cases are the pair's edges.

The stakes are asymmetric. A false positive here would tell a reader that real
Greek is Latin and, if a disposition ever acts on this list, would delete it.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import measure_latin_in_greek_script as m  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
ARTIFACT = REPO / "data" / "latin_in_greek_script.json"

POLYCARP = REPO / "data" / "corpus" / "polycarpus.epistula-ad-philippenses.jsonl"


def _row(locus: str) -> str:
    """The row as served, not a paste of it.

    An earlier version of this test quoted an excerpt and it failed: the
    excerpt carried four distinct Latin markers where the floor is five, so it
    tested the truncation rather than the row. Reading the corpus keeps the
    case honest, and it also means the test notices if the text changes.
    """
    for line in POLYCARP.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if str(r["locus"]) == locus:
                return r.get("text") or ""
    raise AssertionError(f"{locus} is not in {POLYCARP.name}")


GREEK_SAMPLE = ("Ἐγράψατέ μοι καὶ ὑμεῖς καὶ Ἰγνάτιος, ἵν᾽, ἐάν τις ἀπέρχηται εἰς "
                "Συρίαν, καὶ τὰ παῤ ὑμῶν ἀποκομίσῃ γράμματα: ὅπερ ποιήσω, ἐὰν "
                "λάβω καιρὸν εὔθετον, εἴτε ἐγώ, εἴτε ὄν πέμπω πρεσβεύσοντα.")


def _flags(text: str) -> bool:
    toks = m._GK.findall(text)
    hits = {w for w in (t.lower() for t in toks) if w in m.MARKERS}
    return (len(toks) >= m.MIN_TOKENS and len(hits) >= m.MIN_MARKERS
            and m.accent_rate(text, len(toks)) < m.MAX_ACCENT)


PARATEXT = REPO / "data" / "paratext" / "latin_in_greek_script.jsonl"


def test_the_served_corpus_holds_none_of_it():
    """The class is out of data/corpus, so out of every Greek rollup."""
    assert m.scan() == []


def test_it_was_kept_not_dropped():
    rows = [json.loads(l) for l in
            PARATEXT.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert sum(len(m._GK.findall(r["text"])) for r in rows) == 2006
    assert {r["slug"] for r in rows} == {
        "hermas.pastor", "polycarpus.epistula-ad-philippenses",
        "polybius-history.historiae"}


def test_the_greek_sharing_those_rows_stayed_in_the_corpus():
    """The reason this was done by span. Moving the 16 mixed rows whole would
    have taken their Greek with the Latin; 497 tokens of it are still served."""
    rows = [json.loads(l) for l in
            PARATEXT.read_text(encoding="utf-8").splitlines() if l.strip()]
    mixed = [r for r in rows if r["greek_remaining_in_this_row"]]
    assert mixed, "no row recorded Greek left behind"
    assert sum(r["greek_remaining_in_this_row"] for r in mixed) == 497
    poly = _row("13.2")
    assert "Ἐγράψατέ" in poly or "ἐπιστολὰς" in poly


def test_the_detector_still_knows_latin_from_greek():
    """Kept because the rule still gates this file and any text delivered later.

    Tested against text that actually moved, not a paste: an earlier version
    repeated one sentence three times and failed, because repeating it does not
    add distinct markers and the floor counts distinct ones.
    """
    rows = [json.loads(l) for l in
            PARATEXT.read_text(encoding="utf-8").splitlines() if l.strip()]
    longest = max(rows, key=lambda r: len(r["text"]))["text"]
    assert _flags(longest)
    assert not _flags(GREEK_SAMPLE)


def test_unaccented_greek_alone_is_not_enough():
    """A display head is unaccented and is not Latin."""
    head = " ".join(["ΚΕΦΑΛΑΙΟΝ", "ΠΕΡΙ", "ΤΗΣ", "ΟΥΡΑΝΙΑΣ", "ΙΕΡΑΡΧΙΑΣ"] * 6)
    assert m.accent_rate(head, len(m._GK.findall(head))) < m.MAX_ACCENT
    assert not _flags(head)


def test_no_marker_is_also_a_greek_word():
    """προ, περι and και transliterate onto real Greek; they must stay out."""
    for w in ("προ", "περι", "και", "ουν", "δε", "τε", "μεν"):
        assert w not in m.MARKERS


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not built")
def test_the_artifact_is_empty_and_says_why():
    """The measurement now scans a corpus the class has left.

    It used to name three works and 2,006 tokens. Those went to
    data/paratext/latin_in_greek_script.jsonl on 2026-08-10, so the artifact
    reporting zero is the class being gone rather than the detector breaking.
    test_the_detector_still_knows_latin_from_greek is what keeps those apart.
    """
    d = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert d["tokens"] == 0 and d["by_work"] == []
