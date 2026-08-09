#!/usr/bin/env python3
"""Find printed leaves the OCR delivered twice, anywhere in the corpus.

One was found by hand in PG118 (pages 21 and 22 arrived twice, 1,063 tokens
served and counted twice). Nothing had ever looked for the rest. The
rescanned-leaf machinery inside carve_cgpg_volume.py is not a detector: its
drop_duplicates list is curated by hand, ten groups across two volumes in the
whole plan, and its difflib >= 0.60 test only verifies pairs a human already
named. So this is the first search, and the reason PG118's leaf survived is that
nobody listed it, not that a threshold was set wrong.

Word BIGRAM containment is used rather than difflib similarity because it
ignores reading order: the second read of PG118 page 22 walked the columns
differently and scores 0.482 by difflib against 0.841 by containment, so an
order-sensitive search would miss that whole class. On the known case the separation is not marginal: the two duplicate
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
from drop_duplicate_leaf import unique_runs, words  # noqa: E402

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


# In the line-level `ocr` source a printed page is a RUN of rows keyed
# <item>_<page>.<line>, not a single row, so the unit has to be the page or the
# whole class is invisible. This is the gap that hid 64 byte-identical duplicate
# pages until 2026-08-09. A file whose loci are citation loci (a bare "1",
# "3.2") is not page-keyed and is skipped ENTIRE rather than partially: reading
# "3" as a page would compare whole books.
PAGE_LOCUS = re.compile(r"^(.*_\d{2,})\.\d+$")


def page_units(rows: list[dict]) -> list[tuple[str, str]] | None:
    """[(page key, joined text)] for a page-keyed ocr file, else None."""
    if not rows or any(r.get("source") != "ocr" for r in rows):
        return None
    out: dict[str, list[str]] = {}
    for r in rows:
        m = PAGE_LOCUS.match(str(r["locus"]))
        if not m:
            return None
        out.setdefault(m.group(1), []).append(r.get("text") or "")
    return [(k, " ".join(v)) for k, v in out.items()]


def scan_file(fp: Path) -> list[dict]:
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    sets, loci, texts = [], [], []
    served = fp.parent.name == "corpus"
    units = page_units(rows) if "ocr" in SOURCES else None
    if "ocr" in SOURCES and units is None:
        # Not page-keyed. Falling through to the row loop here would compare
        # citation units, which in these files are whole books, and the first
        # run of this code did exactly that: antimachus 176~177 and a Menander
        # pair that was two lines of one page. Skip the file entire.
        return []
    if units is not None:
        for key, text in units:
            b = bigrams(text)
            if len(b) >= MIN_BIGRAMS:
                sets.append(b)
                loci.append(key)
                texts.append(text)
        rows = []
    for r in rows:
        if r.get("source") not in SOURCES:
            continue
        b = bigrams(r.get("text") or "")
        if len(b) >= MIN_BIGRAMS:
            sets.append(b)
            loci.append(str(r["locus"]))
            texts.append(r.get("text") or "")
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
                a, b = texts[i], texts[j]
                # BOTH directions. locus_a is simply the earlier locus, never a
                # verdict about which copy to keep, and assuming otherwise is a
                # live trap: in PG126 the earlier copy is the interloper and the
                # later one is the page that continues the text, so a reader
                # taking "drop the second" from this file would have deleted the
                # in-sequence page and kept the stray.
                runs = unique_runs(b, a)
                runs_a = unique_runs(a, b)
                wa = set(words(a))
                wb = words(b)
                out.append({"file": fp.relative_to(REPO).as_posix(),
                            "served": served,
                            "locus_a": loci[i], "locus_b": loci[j],
                            "containment": round(cont, 4),
                            "bigrams_a": len(sets[i]), "bigrams_b": len(sets[j]),
                            "tokens_b": len(_GK.findall(b)),
                            # what dropping b would cost: the same test
                            # drop_duplicate_leaf.py gates on. A clean rescanned
                            # leaf has none of this; a pair that merely overlaps
                            # has plenty, and must not be dropped either way.
                            "words_absent_from_a": sum(1 for w in wb if w not in wa),
                            "words_b": len(wb),
                            "unique_runs_if_b_dropped": runs,
                            "unique_runs_if_a_dropped": runs_a})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--gate", type=float, default=GATE)
    ap.add_argument("--min-bigrams", type=int, default=MIN_BIGRAMS)
    ap.add_argument("--source", default="cgpg",
                    help="cgpg compares rows (a Migne page is a row); ocr "
                         "compares pages (a page is a run of rows)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    globals()["GATE"] = args.gate
    globals()["MIN_BIGRAMS"] = args.min_bigrams
    globals()["SOURCES"] = {args.source}
    out_fp = (REPO / args.out) if args.out else OUT

    files = sorted(list((DATA / "corpus").glob("*.jsonl"))
                   + list((DATA / "corpus_secondary").glob("*.jsonl")))
    hits, scanned = [], 0
    for fp in files:
        scanned += 1
        try:
            hits.extend(scan_file(fp))
        except Exception as e:                      # a malformed row must not
            print(f"  ! {fp.name}: {e}", file=sys.stderr)   # hide the rest
    # Total order, not just by score. The candidate search walks a dict keyed
    # by bigram, and set iteration order varies with PYTHONHASHSEED between
    # processes, so ties left to insertion order made this file differ between
    # runs. Same failure as data/grave_residue.json had.
    hits.sort(key=lambda h: (-h["containment"], h["file"],
                             h["locus_a"], h["locus_b"]))

    # A pair with no unique run is a clean second copy: dropping it costs
    # nothing. A pair with unique runs overlaps without being a copy, and
    # dropping either side would lose text, so it is NOT a candidate for the
    # drop tool no matter how high the containment.
    clean = [h for h in hits
             if not (h["unique_runs_if_b_dropped"] and h["unique_runs_if_a_dropped"])]
    overlapping = [h for h in hits
                   if h["unique_runs_if_b_dropped"] and h["unique_runs_if_a_dropped"]]
    served_clean = [h for h in clean if h["served"]]
    by_file = Counter(h["file"] for h in hits)
    print(f"scanned {scanned:,} files at containment gate {args.gate}")
    print(f"candidate row pairs: {len(hits):,} in {len(by_file)} files")
    print(f"  droppable one way (one side holds nothing the other lacks): {len(clean)}, "
          f"{sum(h['tokens_b'] for h in clean):,} tok")
    print(f"    of those in SERVED text: {len(served_clean)}, "
          f"{sum(h['tokens_b'] for h in served_clean):,} tok")
    print(f"  not droppable either way (each side has text the other lacks): "
          f"{len(overlapping)}, {sum(h['tokens_b'] for h in overlapping):,} tok "
          f"- do not drop these")
    for h in hits[:25]:
        print(f"    {h['containment']:.3f}  {h['file'].split('/')[-1][:44]:<44} "
              f"{h['locus_a']} ~ {h['locus_b']}")
    if len(hits) > 25:
        print(f"    ... {len(hits) - 25:,} more")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    out_fp.write_text(json.dumps({
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
        "clean_second_copies": len(clean),
        "clean_second_copies_tokens": sum(h["tokens_b"] for h in clean),
        "clean_second_copies_served": len(served_clean),
        "clean_second_copies_served_tokens": sum(h["tokens_b"] for h in served_clean),
        "overlapping_not_copies": len(overlapping),
        "overlapping_not_copies_tokens": sum(h["tokens_b"] for h in overlapping),
        # By band, because a single total would mislead: containment falls off
        # continuously and the low bands are ordinary neighbouring pages of one
        # book, not duplicates. Only the top band is anywhere near decidable.
        "served_droppable_by_containment": [
            {"band": lbl, "pairs": len(sel),
             "tokens": sum(h["tokens_b"] for h in sel)}
            for lbl, sel in ((lbl, [h for h in served_clean
                                    if lo <= h["containment"] < hi])
                             for lbl, lo, hi in (("0.99+", 0.99, 1.01),
                                                 ("0.90-0.99", 0.90, 0.99),
                                                 ("0.80-0.90", 0.80, 0.90),
                                                 ("0.60-0.80", 0.60, 0.80),
                                                 ("0.40-0.60", 0.40, 0.60)))],
        "by_file": dict(by_file.most_common()),
        "pairs": hits,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out_fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
