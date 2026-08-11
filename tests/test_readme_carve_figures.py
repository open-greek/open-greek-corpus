"""README figures about carve state and duplicate pages, bound to their sources.

tests/test_readme_figures.py binds the Status line and the anchor sentence, and
those two stay right. These did not, and nothing was watching: the README said
174,312 Greek tokens were volume-keyed when 22,116 were, that one whole volume
was still uncarved a round after it had been carved, and that 131 pairs and
38,159 tokens sat above 0.90 containment when the artifact it names in the same
sentence said 7 and 2,575. A factor of fifteen, in prose a reader has no reason
to doubt, next to a filename that would have corrected it.

Each figure here is asserted against the thing the sentence itself cites, so the
test fails on the same rebuild that moves the number.
"""

import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_public_corpus import _GK  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
README = (REPO / "README.md").read_text(encoding="utf-8")


def _n(s: str) -> int:
    return int(s.replace(",", ""))


def _band(artifact: str, band: str) -> dict:
    rows = json.loads((REPO / "data" / artifact).read_text(encoding="utf-8"))
    for b in rows["served_droppable_by_containment"]:
        if b["band"] == band:
            return b
    raise AssertionError(f"{artifact} has no band {band}")


def test_nothing_is_volume_keyed_any_more():
    """The class this file was written to watch is empty.

    It used to bind two prose figures against a live count. On 2026-08-10 the
    last 8,741 tokens, which were the edition's own apparatus, moved to
    data/paratext, so there is no count left to drift. What has to stay true is
    that none comes back without the README saying so.
    """
    assert not glob.glob(str(REPO / "data" / "corpus" / "cogPG.*.jsonl"))
    assert "no `cogPG.*` file is volume-keyed any more" in README


def test_duplicate_page_bands_match_the_artifact_named_beside_them():
    m = re.search(r"([\d,]+) served pairs and ([\d,]+) tokens sit\n\s*above 0\.90, "
                  r"another ([\d,]+) pairs and ([\d,]+) tokens between 0\.80 and 0\.90",
                  README)
    assert m, "the containment band sentence moved; update this test with it"
    hi, lo = _band("duplicate_page_candidates.json", "0.90-0.99"), \
        _band("duplicate_page_candidates.json", "0.80-0.90")
    assert (_n(m.group(1)), _n(m.group(2))) == (hi["pairs"], hi["tokens"])
    assert (_n(m.group(3)), _n(m.group(4))) == (lo["pairs"], lo["tokens"])


def test_same_item_band_figures_match_the_artifact():
    """The actionable half of the banded figures.

    The combined totals beside these count cross-item pairs, which both drop
    tools refuse by rule, so quoting only those overstated what could be acted
    on by 4.3x in the top band. Both numbers are in the prose now and both are
    bound here.
    """
    m = re.search(r"same-item ones beside them, (\d+) pairs\n\s*and ([\d,]+) tokens "
                  r"in the top band and (\d+) and ([\d,]+) in the next", README)
    assert m, "the same-item sentence moved; update this test with it"
    hi = _band("duplicate_page_candidates.json", "0.90-0.99")
    lo = _band("duplicate_page_candidates.json", "0.80-0.90")
    assert (int(m.group(1)), _n(m.group(2))) == (hi["same_item_pairs"],
                                                 hi["same_item_tokens"])
    assert (int(m.group(3)), _n(m.group(4))) == (lo["same_item_pairs"],
                                                 lo["same_item_tokens"])


def test_leaf_run_residual_matches_the_artifact():
    # "about" was dropped from the sentence when the residual went to zero and
    # there was nothing left to round.
    m = re.search(r"(\d+) runs are recorded in `duplicate_runs`, (\d+) of them "
                  r"touching served\n\s*text, and (?:about )?([\d,]+) tokens", README)
    assert m, "the leaf-run sentence moved; update this test with it"
    runs = json.loads((REPO / "data" / "duplicate_page_candidates.json")
                      .read_text(encoding="utf-8"))["duplicate_runs"]
    assert (int(m.group(1)), int(m.group(2)), _n(m.group(3))) == (
        runs["runs"], runs["served_runs"], runs["served_tokens_in_second_reads"])


def test_duplicate_leaf_served_figure_matches_the_artifact():
    m = re.search(r"of which (\d+) pairs and\n\s*([\d,]+) tokens are in served text",
                  README)
    assert m, "the leaf served sentence moved; update this test with it"
    leaf = json.loads((REPO / "data" / "duplicate_leaf_candidates.json")
                      .read_text(encoding="utf-8"))
    assert (int(m.group(1)), _n(m.group(2))) == (
        leaf["clean_second_copies_served"], leaf["clean_second_copies_served_tokens"])
