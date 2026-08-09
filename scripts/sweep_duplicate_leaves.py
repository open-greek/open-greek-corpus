#!/usr/bin/env python3
"""Find printed leaves the OCR delivered twice, anywhere in the corpus.

One was found by hand in PG118 (pages 21 and 22 arrived twice, 1,063 tokens
served and counted twice). The only detector that had ever run is the
rescanned-leaf shed inside carve_cgpg_volume.py, which gates on difflib
similarity >= 0.60 against the row it keeps, and that gate is exactly what let
this one through: the second read of page 22 walked the columns in a different
order, so two rows of one page score 0.482.

So this asks a different question. Word BIGRAM containment ignores order almost
entirely while staying specific enough not to fire on two pages of the same
author. On the known case the separation is not marginal: the two duplicate
pairs score 0.960 and 0.841, and the worst non-duplicate pair in the same block
scores 0.079, with a median of 0.022.

Rows are compared only inside their own file, because that is what a duplicated
leaf is. A rare-bigram inverted index does the candidate search, so a file of n
rows costs far less than n^2 set intersections.

This REPORTS. It never edits the corpus; acting on a candidate means reading the
page and writing an entry in data/duplicate_leaves.json, because two rows of
similar Greek are not on their own evidence that a leaf was scanned twice rather
than an author repeating himself.

  python3 scripts/sweep_duplicate_leaves.py
  python3 scripts/sweep_duplicate_leaves.py --write   # -> data/duplicate_leaf_candidates.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "duplicate_leaf_candidates.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

GATE = 0.40        # containment above this is a candidate; known cases are 0.84+
MIN_BIGRAMS = 150  # a printed Migne page runs ~350 bigrams; below this a row is
                   # not a leaf, and short formulaic rows contain each other
                   # trivially (at 40 the sweep returned 12,335 pairs, almost all
                   # of them repeated citation formulae in fragment collections)
COMMON = 0.10      # a bigram in more than this share of a file's rows is not rare

# Only page-level OCR can have a leaf delivered twice. cgpg rows ARE Migne
# pages (median 2,414 characters), so there a duplicated leaf is a duplicated
# row, which is what this finds. The `ocr` source is line-level (median 48
# characters), so the same accident would show up as a duplicated RUN of rows
# and needs a different detector; TEI sources were never scanned by us at all.
SOURCES = {"cgpg"}


def bigrams(text: str) -> set:
    s = "".join(c for c in unicodedata.normalize("NFD", text)
                if not unicodedata.combining(c)).lower()
    w = re.sub(r"[^α-ω ]+", " ", s).split()
    return set(zip(w, w[1:]))


def scan_file(fp: Path) -> list[dict]:
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    sets, loci = [], []
    for r in rows:
        if r.get("source") not in SOURCES:
            continue
        b = bigrams(r.get("text") or "")
        if len(b) >= MIN_BIGRAMS:
            sets.append(b)
            loci.append(str(r["locus"]))
    n = len(sets)
    if n < 2:
        return []

    post = defaultdict(list)
    for i, b in enumerate(sets):
        for g in b:
            post[g].append(i)
    cap = max(2, int(n * COMMON))
    shared: dict[int, Counter] = defaultdict(Counter)
    for g, idxs in post.items():
        if len(idxs) > cap:
            continue                      # common phrasing, not identity
        for a_i in range(len(idxs)):
            for b_i in range(a_i + 1, len(idxs)):
                shared[idxs[a_i]][idxs[b_i]] += 1

    out = []
    for i, cnts in shared.items():
        for j, c in cnts.items():
            floor = min(len(sets[i]), len(sets[j]))
            if c < floor * GATE * 0.5:    # cheap prefilter on rare bigrams alone
                continue
            inter = len(sets[i] & sets[j])
            cont = inter / floor
            if cont >= GATE:
                out.append({"file": fp.relative_to(REPO).as_posix(),
                            "locus_a": loci[i], "locus_b": loci[j],
                            "containment": round(cont, 4),
                            "bigrams_a": len(sets[i]), "bigrams_b": len(sets[j])})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--gate", type=float, default=GATE)
    ap.add_argument("--min-bigrams", type=int, default=MIN_BIGRAMS)
    args = ap.parse_args()
    globals()["GATE"] = args.gate
    globals()["MIN_BIGRAMS"] = args.min_bigrams

    files = sorted(list((DATA / "corpus").glob("*.jsonl"))
                   + list((DATA / "corpus_secondary").glob("*.jsonl")))
    hits, scanned = [], 0
    for fp in files:
        scanned += 1
        try:
            hits.extend(scan_file(fp))
        except Exception as e:                      # a malformed row must not
            print(f"  ! {fp.name}: {e}", file=sys.stderr)   # hide the rest
    hits.sort(key=lambda h: -h["containment"])

    by_file = Counter(h["file"] for h in hits)
    print(f"scanned {scanned:,} files at containment gate {args.gate}")
    print(f"candidate row pairs: {len(hits):,} in {len(by_file)} files")
    for h in hits[:25]:
        print(f"    {h['containment']:.3f}  {h['file'].split('/')[-1][:44]:<44} "
              f"{h['locus_a']} ~ {h['locus_b']}")
    if len(hits) > 25:
        print(f"    ... {len(hits) - 25:,} more")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "row pairs inside one corpus file whose word-bigram containment "
                "is high enough that they may be the same printed page delivered "
                "twice by the OCR",
        "issue": "open-greek/open-greek-corpus#8",
        "method": "bigram containment over min(|a|,|b|), which ignores reading "
                  "order; the shed in carve_cgpg_volume.py uses difflib "
                  "similarity, which a column-reordered second read defeats "
                  "(PG118 loci 22 and 24 scored 0.482 there and 0.841 here)",
        "NOT_A_DROP_LIST": "a candidate is a reason to read the page, not a "
                           "reason to delete a row. Dropping one goes through "
                           "data/duplicate_leaves.json, which requires the scan "
                           "page and an enumeration of what the dropped copy has "
                           "that the kept copy does not.",
        "params": {"gate": args.gate, "min_bigrams": args.min_bigrams,
                   "common_bigram_share": COMMON, "sources": sorted(SOURCES)},
        "files_scanned": scanned,
        "candidates": len(hits),
        "by_file": dict(by_file.most_common()),
        "pairs": hits,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
