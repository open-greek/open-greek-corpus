"""Figures the README states in prose have to match the data it describes.

Most of the README's numbers sit inside generated blocks or are rewritten by the
round that changes them. These two are neither: they are hand-written sentences
that nothing rebuilds, so they drift silently. Both were wrong when this test was
added. The Status line still said ~3,820 works and ~66.7M tokens against 3,908
and 65.6M, and the anchor sentence said `tlg` on 3,322 works when the true count
had FALLEN to 3,300, because works carrying a cog-native id stopped publishing a
TLG number they never had.

A wrong count in the README is not cosmetic: it is the first number a reader
takes, and the corpus total is the one figure a consumer checks a download
against.
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
WORKS = json.loads((REPO / "data" / "work_index.json")
                   .read_text(encoding="utf-8"))["works"]


def _n(s: str) -> int:
    return int(s.replace(",", ""))


def test_anchor_counts_match_work_index():
    m = re.search(r"`cts` on ([\d,]+) works, `tlg` on ([\d,]+),\s*\n"
                  r"`wikidata` on ([\d,]+)\)", README)
    assert m, "the anchor sentence moved; update this test with it"
    said_cts, said_tlg, said_wd = (_n(m.group(i)) for i in (1, 2, 3))
    have = lambda k: sum(1 for x in WORKS.values()  # noqa: E731
                         if (x.get("work_anchors") or {}).get(k))
    assert (said_cts, said_tlg, said_wd) == (have("cts"), have("tlg"),
                                            have("wikidata"))


def test_status_line_matches_the_served_corpus():
    m = re.search(r"- ([\d,]+) works served, ([\d.]+)M Greek tokens", README)
    assert m, "the Status line moved; update this test with it"
    assert _n(m.group(1)) == len(WORKS)

    total = 0
    for fp in glob.glob(str(REPO / "data" / "corpus" / "*.jsonl")):
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    total += len(_GK.findall(json.loads(line).get("text") or ""))
    # One decimal place, so the assertion is as tight as the claim itself.
    assert f"{total / 1e6:.1f}" == m.group(2), \
        f"README says {m.group(2)}M, corpus holds {total:,}"
