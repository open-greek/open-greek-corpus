#!/usr/bin/env python3
"""Find the display heads in a range of a corpus file, in EITHER script.

Every CGPG carve turns on the same question: does this block of Migne carry a
head that names the work or its author, and where does it fall? Four volumes in,
the answer has been got by hand four times, with the same two traps each time.

The first trap is searching in Greek only. Migne prints running heads in Latin,
and our OCR reads them as Greek letter shapes, so a Greek search finds nothing
where the page is covered in headers. PG151's homiliary spells its own head nine
ways (ΟΜΙΛΙΑ, but also ΠΟΜΙΙΙΑ, ΗΟΜΙΗΙΑ, ΙΟΜΙΓΗΑ, ΧΟΜΙΝΙΑ), and PG113's legal
compendium announces itself as ΚΟΜΑΝΟΚΟΜ ΙΜΡΡ. ... ΛΕΩΟΜ ΟΟΜΡΕΝΡΙΑΚΙΟΘ. Neither
is findable by looking for words. Both are obvious as runs of capitals.

The second is searching only the start of a row. A carve moves whole rows, so
where a head FALLS decides whether a carve can express the boundary at all, and
a scan windowed to the first few words cannot see a head that sits mid-row. That
mistake got published for PG003 (issue #9): heads there turned out to fall inside
rows 15 times out of 26, which is why that volume still cannot be carved on loci.

So this scans whole rows for capital runs of either script and reports the
offset. What it does NOT do is decide anything. A head that names a work is
evidence; the absence of one is not evidence of anything except that our OCR
dropped it, which is the state PG139's remaining blocks are in.

  python3 scripts/scan_display_heads.py cogPG.PG139
  python3 scripts/scan_display_heads.py cogPG.PG139 --from 13 --to 118
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"

# Two or more all-caps words in a row is a display head; a single one is as
# likely to be a proper noun or a numeral mid-sentence.
RUN = re.compile(r"(?:[Α-ΩA-Z]{4,}[ .,:]{1,3}){2,}")
WORD = re.compile(r"[Α-ΩA-Z]{4,}")
HEAD_ZONE = 40           # at or before this offset, the head opens its row


def strip_marks(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(c))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="corpus file stem, e.g. cogPG.PG139")
    ap.add_argument("--from", dest="lo", type=int, default=None)
    ap.add_argument("--to", dest="hi", type=int, default=None)
    args = ap.parse_args()

    fp = CORPUS / f"{args.slug}.jsonl"
    if not fp.exists():
        raise SystemExit(f"no such corpus file: {fp}")
    rows = {}
    for line in fp.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[int(str(r["locus"]).split(".")[0])] = " ".join(
                (r.get("text") or "").split())
    keys = [k for k in sorted(rows)
            if (args.lo is None or k >= args.lo) and (args.hi is None or k <= args.hi)]
    if not keys:
        raise SystemExit("no rows in that range")

    heads, words = [], Counter()
    for k in keys:
        bare = strip_marks(rows[k])
        for m in RUN.finditer(bare):
            heads.append((k, m.start(), len(bare), m.group().strip()))
        for m in WORD.finditer(bare):
            words[m.group()] += 1

    span = f"{keys[0]}-{keys[-1]}"
    mid = [h for h in heads if h[1] >= HEAD_ZONE]
    print(f"{args.slug} {span}: {len(keys)} rows")
    print(f"  {len(heads)} display heads (2+ capitalized words), "
          f"{len(mid)} of them MID-ROW")
    if mid:
        print(f"  a mid-row head cannot be expressed by a whole-row carve, which "
              f"is what carve_cgpg_volume.py does")
    for k, at, n, txt in heads[:30]:
        where = "opens" if at < HEAD_ZONE else "MID  "
        print(f"    {k:>4} {where} {at:>5}/{n:<5} {txt[:56]}")
    print(f"\n  {len(words)} distinct all-caps words; commonest:")
    for w, n in words.most_common(12):
        print(f"    {w:<20} x{n}")
    if not heads:
        print("\n  No display head survives here. That is not evidence about what "
              "the text is:\n  it means the OCR dropped the heads, and settling "
              "the block needs the page images.")


if __name__ == "__main__":
    main()
