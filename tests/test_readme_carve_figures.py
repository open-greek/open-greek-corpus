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


def test_volume_keyed_sentence_matches_the_corpus():
    m = re.search(r"(\d+) `cogPG\.\*` files are still volume-keyed, holding "
                  r"([\d,]+) Greek\ntokens", README)
    assert m, "the volume-keyed sentence moved; update this test with it"
    files = sorted(glob.glob(str(REPO / "data" / "corpus" / "cogPG.*.jsonl")))
    total = 0
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    total += len(_GK.findall(json.loads(line).get("text") or ""))
    assert (int(m.group(1)), _n(m.group(2))) == (len(files), total)


def test_leftovers_sentence_matches_the_same_files():
    """The follow-up sentence counts the same mass a second way; both must agree,
    which is what caught nine files being called ten's worth of leftovers."""
    m = re.search(r"remaining\nfiles are carved volumes' leftovers, ([\d,]+) tokens",
                  README)
    assert m, "the leftovers sentence moved; update this test with it"
    said = re.search(r"(\d+) `cogPG\.\*` files are still volume-keyed, holding "
                     r"([\d,]+) Greek\ntokens", README)
    assert _n(m.group(1)) == _n(said.group(2))


def test_duplicate_page_bands_match_the_artifact_named_beside_them():
    m = re.search(r"([\d,]+) served pairs and ([\d,]+) tokens sit\n\s*above 0\.90, "
                  r"another ([\d,]+) pairs and ([\d,]+) tokens between 0\.80 and 0\.90",
                  README)
    assert m, "the containment band sentence moved; update this test with it"
    hi, lo = _band("duplicate_page_candidates.json", "0.90-0.99"), \
        _band("duplicate_page_candidates.json", "0.80-0.90")
    assert (_n(m.group(1)), _n(m.group(2))) == (hi["pairs"], hi["tokens"])
    assert (_n(m.group(3)), _n(m.group(4))) == (lo["pairs"], lo["tokens"])


def test_duplicate_leaf_served_figure_matches_the_artifact():
    m = re.search(r"of which (\d+) pairs and\n\s*([\d,]+) tokens are in served text",
                  README)
    assert m, "the leaf served sentence moved; update this test with it"
    leaf = json.loads((REPO / "data" / "duplicate_leaf_candidates.json")
                      .read_text(encoding="utf-8"))
    assert (int(m.group(1)), _n(m.group(2))) == (
        leaf["clean_second_copies_served"], leaf["clean_second_copies_served_tokens"])
