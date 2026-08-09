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


def _flags(text: str) -> bool:
    toks = m._GK.findall(text)
    hits = {w for w in (t.lower() for t in toks) if w in m.MARKERS}
    return (len(toks) >= m.MIN_TOKENS and len(hits) >= m.MIN_MARKERS
            and m.accent_rate(text, len(toks)) < m.MAX_ACCENT)


def test_transliterated_latin_is_caught():
    """Polycarp 11.1, "nimis contristatus sum pro Valente"."""
    assert _flags(_row("11.1"))


def test_a_short_latin_row_is_reached_by_its_run_not_by_a_lower_floor():
    """Polycarp 10.1 carries four markers where five are asked, so the row
    alone cannot say it, and the strict test is right to refuse. It is Latin,
    and the scan reaches it because 10.2 beside it is confirmed."""
    assert not _flags(_row("10.1"))
    got = {(r["work"], r["locus"]) for r in m.scan()}
    assert ("polycarpus.epistula-ad-philippenses", "10.1") in got


def test_the_greek_chapter_in_the_same_work_is_not():
    """Polycarp 13 is Greek and sits between Latin chapters; it must survive."""
    assert not _flags(_row("13.1"))
    assert not _flags(_row("13.2"))


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
def test_the_artifact_names_only_the_two_works_that_survive_in_latin():
    d = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert {w["work"] for w in d["by_work"]} == {
        "hermas.pastor", "polycarpus.epistula-ad-philippenses"}
    assert d["tokens"] == sum(w["tokens"] for w in d["by_work"])
