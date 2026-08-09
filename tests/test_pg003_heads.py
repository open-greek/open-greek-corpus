"""The PG003 paraphrase head matcher, which decides where an author changes.

recover_pg003_heads.py stopped enumerating spellings and started folding the
scanner's Greek lookalikes and scoring similarity, because Migne's PARAPHRASIS
PACHYMERAE comes back garbled a different way almost every time. A fuzzy match
that drifts is worse than a strict one that misses: a page header taken for a
display head puts an author switch at the top of a page in the middle of a
block, and every token after it goes to the wrong man.

So the cases here are the two ends of that. The readings are verbatim from the
Internet Archive OCR of the volume, not invented.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import recover_pg003_heads as r  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
GEOMETRY = REPO / "data" / "pg003_head_geometry.json"


# Display heads: the full spelling with the printed number. Every one of these
# was missed by the fixed expression that shipped before.
@pytest.mark.parametrize("line", [
    "PARAPHRASIS PACHYMERAE (22).",          # clean, for a floor
    "FARAPHRASIS PACHYMERLE (1).",
    "PARAPHRASIS ΡΑΟΠΥΜΕΒ ΑΣ (28).",         # read as Greek lookalikes
    "TARAPIIRASI: CI YMEILE (15).",          # the worst one in the volume
    "136 PARAPIRASIS PACHYMERJE. (20).",     # column number ahead of the head
    "PARAPHHASIS  PACHYMERE (49).",
])
def test_display_heads_are_found(line):
    assert r.paraphrase_heads(line + "\n"), f"missed {line!r}"


# Running heads. These name the work and abbreviate the paraphrase, and they sit
# at the top of every page of a block rather than at its start. Taking one as a
# boundary is the failure this matcher has to avoid.
@pytest.mark.parametrize("line", [
    "DE COELESTI HIERARCHIA, CAP. I. — PARAPHR. PACHYMERJE.",
    "ΡΕ COELESTI HIERARCHIA, CAP. Il, — PARAPHR. PACHYMERAE.",
    "DE DIVINIS NOMINIBUS, CAP. X. -- PARAPHR. PACHYMERUE.",
    "1. — PARAPHR. PACHYMERA.",
    # Prose in the volume's own front matter, which names the paraphrase twice.
    "Scholia S. Maximi, et Paraprasis Pachymera: sub-",
])
def test_running_heads_and_prose_are_refused(line):
    assert not r.paraphrase_heads(line + "\n"), f"took {line!r} for a head"


def test_the_number_is_what_separates_them():
    """Same words, same page, and only one of them opens a block."""
    assert r.paraphrase_heads("PARAPHRASIS PACHYMERAE (22).\n")
    assert not r.paraphrase_heads("PARAPHRASIS PACHYMERAE.\n")


def test_homoglyph_fold_is_a_fold_and_not_a_transliteration():
    # Greek capitals that LOOK like Latin ones become them; the rest are dropped
    # rather than guessed at, so a genuinely Greek line cannot score.
    assert r.latin_key("ΡΑΟΠΥΜΕΒ") == "PAOYMEB"
    assert r.latin_key("ΚΕΦΑΛΑΙΟΝ") == "KEAAION"


@pytest.mark.skipif(not GEOMETRY.exists(), reason="head geometry not measured")
def test_geometry_still_says_display_head():
    """The matcher's whole premise, asserted against the measurement.

    If a rebuild ever flips this, the boundaries in data/pg003_heads.json stop
    meaning what they say and the carve has to stop.
    """
    g = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    full = g["summary"]["numbered_full_form"]
    abbr = g["summary"]["abbreviated"]
    assert full["within_top_10_percent"] == 0
    assert full["is_first_line_on_its_page"] == 0
    assert abbr["within_top_10_percent"] >= 0.8 * abbr["lines"]
    assert full["median_top_of_page_fraction"] > 0.25
