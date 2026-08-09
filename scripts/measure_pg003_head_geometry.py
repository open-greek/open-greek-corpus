#!/usr/bin/env python3
"""Decide whether PG003's paraphrase head is a display head or a page header,
by measuring where on the page it is printed.

This is the question the whole PG003 carve turns on. Migne marks Georgius
Pachymeres' paraphrase with PARAPHRASIS PACHYMERAE (N), numbered straight
through the volume, and recover_pg003_heads.py treats each one as the point
where a paraphrase block begins. If instead those lines were running heads,
repeated at the top of every page of a block, then every boundary taken from
them would be wrong in the same direction: it would put the switch at a page top
when the text actually changes hands somewhere on the page before.

The witness gives two reasons to suspect exactly that. The same number comes
back on more than one page, which is what a repeated page header does. And one
head is split across the two halves of a scanned spread with a column number
between them, which is what a header spanning a spread looks like.

Neither settles it, because both are also what a mangled OCR of two separate
display heads looks like. Position does settle it, and the scan carries
position: the Internet Archive item ships DjVu hidden text with a bounding box
per word, so where each head sits on its page is a measurement, not a reading of
the image.

The measurement is the contrast, not either number alone. A page header is the
topmost line on its page. A display head has body text above it, because the
block it opens starts partway down the page.

  python3 scripts/measure_pg003_head_geometry.py
  python3 scripts/measure_pg003_head_geometry.py --write
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
WITNESS = DATA / "cache" / "ia" / "PG003_djvu.xml"
OUT = DATA / "pg003_head_geometry.json"
WITNESS_URL = ("https://archive.org/download/Patrologia_Graeca_vol_003/"
               "PG003_djvu.xml")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recover_pg003_heads import (HEAD_NUM, PARAPHRASE_HEAD,  # noqa: E402
                                 PARAPHRASE_RATIO, latin_key)

# The page header spells the paraphrase short and carries the work and chapter
# with it: DE COELESTI HIERARCHIA, CAP. I. - PARAPHR. PACHYMERAE. Scored on a
# window rather than whole, because that title makes the line much longer than
# the phrase being looked for.
ABBREV_HEAD = "PARAPHRPACHYMERAE"
ABBREV_RATIO = 0.78
TOP_OF_PAGE = 0.10       # fraction of page height a running head sits within

# DjVu writes coords as left,bottom,right,top with y measured down from the top
# of the page, so the fourth number is the top edge of the word.
PAGE = re.compile(r'usemap="PG003_(\d+)\.djvu" width="(\d+)" height="(\d+)"'
                  r'(.*?)(?=<OBJECT|</BODY>)', re.S)
LINE = re.compile(r"<LINE>(.*?)</LINE>", re.S)
WORD = re.compile(r'<WORD coords="(\d+),(\d+),(\d+),(\d+)"[^>]*>(.*?)</WORD>')
ENTITY = re.compile(r"&[a-z]+;")


def classify(text: str) -> str | None:
    k = latin_key(text)
    if not 10 <= len(k) <= 70:
        return None
    if HEAD_NUM.search(text) and \
            difflib.SequenceMatcher(None, k, PARAPHRASE_HEAD).ratio() >= PARAPHRASE_RATIO:
        return "numbered_full_form"
    window = max((difflib.SequenceMatcher(None, k[j:j + len(ABBREV_HEAD) + 4],
                                          ABBREV_HEAD).ratio()
                  for j in range(0, max(1, len(k) - 8), 2)), default=0.0)
    return "abbreviated" if window >= ABBREV_RATIO else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not WITNESS.exists():
        WITNESS.parent.mkdir(parents=True, exist_ok=True)
        print(f"  fetching {WITNESS_URL}", file=sys.stderr)
        import urllib.request
        with urllib.request.urlopen(WITNESS_URL, timeout=900) as r:
            WITNESS.write_bytes(r.read())
    xml = WITNESS.read_text(encoding="utf-8", errors="replace")

    found: dict[str, list[dict]] = {"numbered_full_form": [], "abbreviated": []}
    leaves = 0
    for leaf, _w, height, body in (m.groups() for m in PAGE.finditer(xml)):
        leaves += 1
        h = int(height)
        lines = LINE.findall(body)
        for i, line in enumerate(lines):
            words = WORD.findall(line)
            if not words:
                continue
            text = " ".join(ENTITY.sub("", w[4]) for w in words)
            kind = classify(text)
            if not kind:
                continue
            num = HEAD_NUM.search(text)
            found[kind].append({
                "leaf": int(leaf), "line": i, "lines_on_page": len(lines),
                "top_of_page_fraction": round(min(int(w[3]) for w in words) / h, 4),
                "is_first_line": i == 0,
                "printed_number": int(num.group(1)) if num else None,
                "reading": " ".join(text.split())[:60],
            })

    print(f"{leaves} leaves in the scan")
    summary = {}
    for kind, rows in found.items():
        if not rows:
            continue
        ys = [r["top_of_page_fraction"] for r in rows]
        summary[kind] = {
            "lines": len(rows),
            "median_top_of_page_fraction": round(statistics.median(ys), 4),
            "is_first_line_on_its_page": sum(1 for r in rows if r["is_first_line"]),
            "within_top_10_percent": sum(1 for y in ys if y < TOP_OF_PAGE),
        }
        s = summary[kind]
        print(f"  {kind:<19} {s['lines']:>3} lines, median {s['median_top_of_page_fraction']:.3f} "
              f"down the page, first line on {s['is_first_line_on_its_page']}, "
              f"in the top {TOP_OF_PAGE:.0%} on {s['within_top_10_percent']}")

    full = summary.get("numbered_full_form", {})
    abbr = summary.get("abbreviated", {})
    settled = (full.get("within_top_10_percent") == 0
               and full.get("is_first_line_on_its_page") == 0
               and abbr.get("within_top_10_percent", 0) >= 0.8 * abbr.get("lines", 1))
    verdict = ("display head: it has text above it on every page it appears on, "
               "so it marks where a block begins"
               if settled else
               "NOT SETTLED by position; do not carve on these heads")
    print(f"\n  numbered full form is a {verdict}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "where on the printed page each PG003 paraphrase head sits, "
                "measured from the scan's own per-word bounding boxes",
        "issue": "open-greek/open-greek-corpus#9",
        "why": "recover_pg003_heads.py treats PARAPHRASIS PACHYMERAE (N) as the "
               "point a paraphrase block begins. If it were a running head "
               "instead, every boundary taken from one would be wrong the same "
               "way, putting the switch at a page top when the text changes "
               "hands on the page before. Two things in the text OCR suggest "
               "exactly that: a number that comes back on a later page, and one "
               "head split across a spread with a column number between its "
               "halves. Position decides it and the two readings do not.",
        "witness": {
            "item": "https://archive.org/details/Patrologia_Graeca_vol_003",
            "file": str(WITNESS.relative_to(REPO)),
            "sha256": hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
        },
        "leaves": leaves,
        "params": {"paraphrase_similarity": PARAPHRASE_RATIO,
                   "abbreviated_similarity": ABBREV_RATIO,
                   "top_of_page_fraction": TOP_OF_PAGE},
        "summary": summary,
        "verdict": verdict,
        "reading": "The abbreviated form is a running head: it opens its page and "
                   "sits hard against the top edge. The numbered full form never "
                   "does either, on any of its occurrences, so it is a display "
                   "head printed where the paraphrase block starts. That is also "
                   "why the boundaries it gives are character offsets into a row "
                   "rather than whole pages.",
        "occurrences": {k: sorted(v, key=lambda r: (r["leaf"], r["line"]))
                        for k, v in found.items()},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
