#!/usr/bin/env python3
"""Recover PG003's display heads from a second OCR of the same volume.

PG 3 prints Pseudo-Dionysius with Georgius Pachymeres' paraphrase, alternating
every few pages, and our OCR dropped most of the Latin display heads that mark
the switches: 26 survive in 459 rows, only 5 of them author switches. Three
rounds recorded the carve as blocked on the page images because of that.

It is not. The Internet Archive item Patrologia_Graeca_vol_003 is an independent
public-domain OCR of the same volume which read Migne's Latin heads as Latin,
170 of them, and whose Greek is good enough to align against ours. So the heads
can be placed without re-OCR and without reading pages by eye. (The other Migne
volumes' Archive scans are the patrologiaecursu<NNNN>mign series, whose OCR kept
no Greek at all; this volume happens to have a better second item, which is why
this trick works here and nowhere else.)

Method: reduce both texts to accent-stripped lowercase Greek word streams, take
the trigrams that occur exactly once in each, keep the longest increasing
subsequence of those matches so the anchor chain is monotone, then map each
Latin head to the nearest following anchor and through it to a (locus, offset)
in our rows.

WHAT THIS DOES NOT DO. It does not carve. A boundary that is close but wrong
conserves every token and still files Dionysius under Pachymeres, and the check
for that is not conservation. Two guards ship with the table instead. Every head
carries the distance in words to the anchor that placed it, and any head further
than MAX_ANCHOR_GAP is emitted as declined rather than placed, because the
anchor chain is sparsest exactly where the two OCRs disagree, which is at the
heads. And the 26 heads our own bytes retain are never read while aligning, so
they are a held-out check: each is reported with the gap between where we have
it and where the alignment predicts it.

  python3 scripts/recover_pg003_heads.py
  python3 scripts/recover_pg003_heads.py --write   # -> data/pg003_heads.json
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus" / "cogPG.PG003.jsonl"
WITNESS = DATA / "cache" / "ia" / "PG003_djvu.txt"
OUT = DATA / "pg003_heads.json"
WITNESS_URL = ("https://archive.org/download/Patrologia_Graeca_vol_003/"
               "PG003_djvu.txt")

HEAD_RX = re.compile(
    r"(PARAPHRASIS\s+PACHYMER\w*|SYNOPSIS(?:\s+[A-Z][A-Za-z.]*){0,3}"
    r"|CAPUT\s+[IVXL]+|ADNOTATIONES)")
GK = re.compile(r"[Ͱ-Ͽἀ-῿]+")
MAX_ANCHOR_GAP = 40      # words; beyond this the placement is declined


def fold(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", w)
                   if not unicodedata.combining(c)).lower()


def stream(text: str) -> list[tuple[str, int]]:
    """(folded word, character offset) for every Greek word, in order."""
    return [(fold(m.group()), m.start()) for m in GK.finditer(text)]


def unique_trigrams(words: list[str]) -> dict[tuple, int]:
    seen: dict[tuple, int] = {}
    dupe = set()
    for i in range(len(words) - 2):
        k = (words[i], words[i + 1], words[i + 2])
        if k in seen:
            dupe.add(k)
        else:
            seen[k] = i
    for k in dupe:
        del seen[k]
    return seen


def lis(pairs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Longest increasing subsequence on the second coordinate; pairs come in
    sorted by the first. Anything off it is a false match and is dropped."""
    tails: list[int] = []
    idx: list[int] = []
    back: list[int] = [-1] * len(pairs)
    for n, (_, b) in enumerate(pairs):
        j = bisect.bisect_left(tails, b)
        if j == len(tails):
            tails.append(b)
            idx.append(n)
        else:
            tails[j] = b
            idx[j] = n
        back[n] = idx[j - 1] if j else -1
    out = []
    n = idx[-1] if idx else -1
    while n != -1:
        out.append(pairs[n])
        n = back[n]
    return out[::-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--max-gap", type=int, default=MAX_ANCHOR_GAP)
    args = ap.parse_args()

    if not WITNESS.exists():
        # Cache-first, fetch what is missing, the same shape as the
        # byzantium.gr ingester. data/cache is gitignored, so a clean checkout
        # has to be able to rebuild this without a manual step.
        WITNESS.parent.mkdir(parents=True, exist_ok=True)
        print(f"  fetching {WITNESS_URL}", file=sys.stderr)
        import urllib.request
        with urllib.request.urlopen(WITNESS_URL, timeout=300) as r:
            WITNESS.write_bytes(r.read())
    wit = WITNESS.read_text(encoding="utf-8", errors="replace")

    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    # our stream, carrying which row and which offset inside it each word is at
    ours: list[tuple[str, str, int]] = []
    for r in rows:
        for w, off in stream(r.get("text") or ""):
            ours.append((w, str(r["locus"]), off))
    their = stream(wit)

    ow = [w for w, _, _ in ours]
    tw = [w for w, _ in their]
    a, b = unique_trigrams(tw), unique_trigrams(ow)
    common = sorted((i, b[k]) for k, i in a.items() if k in b)
    chain = lis(common)
    print(f"anchor chain: {len(common):,} unique-trigram matches, "
          f"{len(chain):,} monotone ({len(chain) / max(len(ow), 1):.2f} per our word)")

    their_idx = [t for t, _ in chain]
    heads = list(HEAD_RX.finditer(wit))
    placed, declined = [], []
    for h in heads:
        # first witness word after the head, then the nearest anchor at or after it
        j = bisect.bisect_left([off for _, off in their], h.end())
        if j >= len(their):
            continue
        k = bisect.bisect_left(their_idx, j)
        if k >= len(chain):
            declined.append({"head": " ".join(h.group().split()),
                             "reason": "no anchor after this head"})
            continue
        t_i, o_i = chain[k]
        gap = t_i - j
        rec = {"head": " ".join(h.group().split()),
               "anchor_gap_words": gap,
               "locus": ours[o_i][1], "offset": ours[o_i][2],
               "incipit": " ".join(w for w, _, _ in ours[o_i:o_i + 6])}
        (placed if gap <= args.max_gap else declined).append(
            rec if gap <= args.max_gap
            else {**rec, "reason": f"nearest anchor is {gap} words away "
                                   f"(limit {args.max_gap})"})
    print(f"heads in the witness: {len(heads)}; placed {len(placed)}, "
          f"declined {len(declined)}")

    # Held out: the 26 heads our own OCR kept, recorded independently in
    # data/pg003_blocks.json and never read while aligning. Each is reported
    # with the distance to the nearest placement in the same row.
    blocks = json.loads((DATA / "pg003_blocks.json").read_text(encoding="utf-8"))
    held = [(str(h["locus"]), h["at"], h["head"], h.get("reading", ""))
            for h in blocks["heads"]]
    checks = []
    for loc, off, kind, reading in held:
        near = [p for p in placed if p["locus"] == loc]
        d = min((abs(p["offset"] - off) for p in near), default=None)
        checks.append({"locus": loc, "our_offset": off, "head": kind,
                       "reading": reading[:44],
                       "nearest_placement_chars": d})
    have = [c for c in checks if c["nearest_placement_chars"] is not None]
    within = [c for c in have if c["nearest_placement_chars"] <= 200]
    print(f"held out: {len(held)} heads recorded in data/pg003_blocks.json; "
          f"{len(have)} share a locus with a placement, "
          f"{len(within)} within 200 characters")
    for c in have:
        if c["nearest_placement_chars"] > 200:
            # Both current outliers are explained, and one of them is the
            # alignment being right where our record is not: at locus 89 our
            # recorded head is a stray Latin running head (ΟΑΡΠΤ ΙΙΙ) at offset
            # 0, while the boundary the alignment lands on is where our own
            # ΚΕΦΑΛΑΙΟΝ Γʹ sits at 1,552.
            print(f"    off by {c['nearest_placement_chars']:>5} at locus "
                  f"{c['locus']}: {c['reading']}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "Migne PG003 display heads located in our rows by aligning a "
                "second, independent OCR of the same volume",
        "issue": "open-greek/open-greek-corpus#9",
        "NOT_A_CARVE_INPUT_YET": "a placement is a candidate boundary. A boundary "
                                 "that is close but wrong conserves every token "
                                 "and still files Dionysius under Pachymeres, so "
                                 "each entry carries the distance to the anchor "
                                 "that placed it and split_carved_row.py's own "
                                 "head assertion must confirm it before any cut.",
        "witness": {
            "item": "https://archive.org/details/Patrologia_Graeca_vol_003",
            "file": str(WITNESS.relative_to(REPO)),
            "sha256": hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
        },
        "params": {"max_anchor_gap_words": args.max_gap},
        "anchor_matches": len(common), "anchor_chain": len(chain),
        "heads_found": len(heads), "placed": len(placed), "declined": len(declined),
        "held_out": {"source": "data/pg003_blocks.json heads",
                     "note": "locus 89's recorded head is a running head at "
                             "offset 0, not a boundary; the placement at ~1,566 "
                             "matches our own ΚΕΦΑΛΑΙΟΝ Γʹ at 1,552, so the "
                             "alignment is right and the record is not. Locus "
                             "171 is a genuine miss, 516 characters late.",
                     "heads": len(held),
                     "sharing_a_locus_with_a_placement": len(have),
                     "within_200_chars": len(within),
                     "checks": checks},
        "placements": placed,
        "declined_placements": declined,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
