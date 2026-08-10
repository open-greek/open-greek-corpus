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


PAGE_KEY = re.compile(r"^(.*?)_(\d{2,})$")
MIN_RUN_LINKS = 3    # pairs in a row at one offset before it counts as a run


def page_of(key: str) -> tuple[str, int] | None:
    m = PAGE_KEY.match(str(key))
    return (m.group(1), int(m.group(2))) if m else None


def cross_file_hits(files: list[Path]) -> list[dict]:
    """Pages of one scan item that the per-file sweep can never compare.

    scan_file compares units inside one file, which is what a duplicated leaf
    was assumed to be. But a carve splits a scan item across the works printed
    in it, and 90 of the 244 served items are split that way. So a printed page
    delivered twice, once into each of two works, is invisible: neither file
    holds both copies and nothing ever puts them side by side.

    This adds that comparison and only that one. A page's rows are joined across
    every file that holds them, since a page straddling a carve boundary is one
    printed page in two pieces rather than two pages; then pages of one item are
    compared, and a pair is emitted only when the two sides come from different
    files. Everything the per-file sweep already found is untouched, so this can
    add candidates and can never revise or remove one.

    Served and witness text are kept apart. After the collapse passes 4,078 page
    keys have rows in both data/corpus and data/corpus_secondary, and joining
    across the two would rejoin a displaced read with the read that beat it and
    then report the pair as a duplicate of itself.
    """
    if "ocr" not in SOURCES:
        # Page units exist only in the line-level `ocr` source. In cgpg mode the
        # unit is a row, and letting this run there mixed ocr page pairs into
        # the leaf artifact, taking its served figure from 6 pairs to 45.
        return []
    out: list[dict] = []
    for universe in ("corpus", "corpus_secondary"):
        # item -> page key -> {files, texts}
        items: dict[str, dict[str, dict]] = defaultdict(dict)
        for fp in files:
            if fp.parent.name != universe:
                continue
            rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
            units = page_units(rows)
            if units is None:
                continue
            rel = fp.relative_to(REPO).as_posix()
            for key, text in units:
                item = key.rsplit("_", 1)[0]
                u = items[item].setdefault(key, {"files": set(), "parts": []})
                u["files"].add(rel)
                u["parts"].append((rel, text))
        for item, pages in sorted(items.items()):
            if len({f for u in pages.values() for f in u["files"]}) < 2:
                continue                      # item lives in one file; already done
            keys, sets, texts, srcs = [], [], [], []
            for key in sorted(pages):
                u = pages[key]
                text = " ".join(t for _f, t in sorted(u["parts"]))
                b = bigrams(text)
                if len(b) < MIN_BIGRAMS:
                    continue
                keys.append(key)
                sets.append(b)
                texts.append(text)
                srcs.append(sorted(u["files"]))
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    if srcs[i] == srcs[j]:
                        continue              # same file(s): scan_file had it
                    floor = min(len(sets[i]), len(sets[j]))
                    cont = len(sets[i] & sets[j]) / floor
                    if cont < GATE:
                        continue
                    a, b = texts[i], texts[j]
                    wa, wb = set(words(a)), words(b)
                    out.append({
                        "file": srcs[i][0], "files_a": srcs[i], "files_b": srcs[j],
                        "cross_file": True,
                        "served": universe == "corpus",
                        "locus_a": keys[i], "locus_b": keys[j],
                        "containment": round(cont, 4),
                        "bigrams_a": len(sets[i]), "bigrams_b": len(sets[j]),
                        "tokens_b": len(_GK.findall(b)),
                        "words_absent_from_a": sum(1 for w in wb if w not in wa),
                        "words_b": len(wb),
                        "unique_runs_if_b_dropped": unique_runs(b, a),
                        "unique_runs_if_a_dropped": unique_runs(a, b)})
    return out


def find_runs(hits: list[dict]) -> list[dict]:
    """Group pairs into runs of consecutive pages repeating at a fixed offset.

    Containment answers "do these two pages say the same thing", and on a
    rescanned leaf that is exactly the question a differently-garbled second
    read fails: the two copies of Nicetas' page 504 read Ἐπηγγέλατο and
    Ἐπηγεμῶτο, and enough of the page goes that way to drag the score under any
    gate that is safe for a single pair.

    Position answers a different question, and this one the garbling cannot
    touch. Ten consecutive pages each matching the page ten later is not ten
    coincidences; it is one leaf-run delivered twice. The offsets bear that out
    corpus-wide: 292 same-item pairs sit at offset 10 and the histogram is
    almost entirely even, while offset 1, which is what genuinely neighbouring
    pages would produce, has 9.

    A run is EVIDENCE, not a verdict. It says a pair is worth considering
    despite its score; every post-condition downstream still applies to it.
    """
    by_offset: dict[tuple, set] = defaultdict(set)
    for h in hits:
        if h.get("cross_file"):
            # A run is one scanner handing the same stretch of leaves to one
            # file twice. A cross-file pair is a different claim, and letting it
            # chain would admit a within-file pair below the containment gate on
            # the strength of a neighbour that is not evidence for it.
            h["same_item"] = True
            h["page_offset"] = None
            continue
        pa, pb = page_of(h["locus_a"]), page_of(h["locus_b"])
        h["same_item"] = bool(pa and pb and pa[0] == pb[0])
        h["page_offset"] = abs(pb[1] - pa[1]) if h["same_item"] else None
        if h["same_item"] and h["page_offset"]:
            by_offset[(h["file"], pa[0], h["page_offset"])].add(min(pa[1], pb[1]))

    runs, member = [], {}
    for (f, item, off), starts in sorted(by_offset.items()):
        block: list[int] = []
        for p in sorted(starts) + [None]:
            if block and p is not None and p == block[-1] + 1:
                block.append(p)
                continue
            if len(block) >= MIN_RUN_LINKS:
                rid = f"{item}+{off}@{block[0]}"
                runs.append({"run": rid, "file": f, "item": item,
                             "page_offset": off, "first_page": block[0],
                             "last_page": block[-1], "links": len(block)})
                for s in block:
                    member[(f, item, off, s)] = rid
            block = [p] if p is not None else []

    for h in hits:
        h["run"] = None
        if h["same_item"] and h["page_offset"]:
            pa = page_of(h["locus_a"])
            h["run"] = member.get((h["file"], pa[0], h["page_offset"],
                                   min(pa[1], page_of(h["locus_b"])[1])))
    for r in runs:
        sel = [h for h in hits if h["run"] == r["run"]]
        r["pairs"] = len(sel)
        # Distinct later pages, not a sum over pairs. A page read three times
        # (Themistius 198-204 is) appears in several pairs, and adding tokens_b
        # each time would report more duplicate text than the file contains.
        # This is the figure that gets published, so it has to be the honest one.
        seen = {}
        for h in sel:
            seen[h["locus_b"]] = h["tokens_b"]
        r["second_copy_pages"] = len(seen)
        r["tokens_b"] = sum(seen.values())
        r["containment_min"] = min(h["containment"] for h in sel)
        r["containment_max"] = max(h["containment"] for h in sel)
        r["served"] = any(h["served"] for h in sel)
    runs.sort(key=lambda r: (-r["tokens_b"], r["file"], r["run"]))
    return runs


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
    hits.extend(cross_file_hits(files))
    hits.sort(key=lambda h: (-h["containment"], h["file"],
                             h["locus_a"], h["locus_b"]))
    runs = find_runs(hits)
    served_runs = [r for r in runs if r["served"]]

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
    print(f"  leaf-runs (consecutive pages repeating at a fixed offset): "
          f"{len(runs)}, of which {len(served_runs)} touch served text, "
          f"{sum(r['tokens_b'] for r in served_runs):,} tok in second reads")
    for r in served_runs[:8]:
        print(f"    {r['file'].split('/')[-1][:44]:<44} {r['item']} "
              f"{r['first_page']}-{r['last_page']} +{r['page_offset']} "
              f"({r['links']} links, containment {r['containment_min']:.2f}"
              f"-{r['containment_max']:.2f})")
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
        "issue": "open-greek/open-greek-corpus#33",
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
        # continuously. Split same-item from cross-item, because both drop
        # tools refuse a cross-item pair by rule, so a combined figure counts
        # pairs nothing can act on. In the 0.90 band that is most of them.
        #
        # An earlier version of this comment said the low bands were "ordinary
        # neighbouring pages of one book". That was wrong, and the run block
        # below is what disproves it: the same-item offsets are almost all even
        # and pile up at 10, while offset 1, which is what a neighbouring page
        # would give, appears 9 times corpus-wide.
        "served_droppable_by_containment": [
            {"band": lbl, "pairs": len(sel),
             "tokens": sum(h["tokens_b"] for h in sel),
             "same_item_pairs": len([h for h in sel if h["same_item"]]),
             "same_item_tokens": sum(h["tokens_b"] for h in sel if h["same_item"])}
            for lbl, sel in ((lbl, [h for h in served_clean
                                    if lo <= h["containment"] < hi])
                             for lbl, lo, hi in (("0.99+", 0.99, 1.01),
                                                 ("0.90-0.99", 0.90, 0.99),
                                                 ("0.80-0.90", 0.80, 0.90),
                                                 ("0.60-0.80", 0.60, 0.80),
                                                 ("0.40-0.60", 0.40, 0.60)))],
        "duplicate_runs": {
            "what": "consecutive pages repeating at a fixed offset inside one "
                    "scan item: a leaf-run the OCR delivered twice",
            "why": "containment asks whether two pages say the same thing, and "
                   "a second read garbled differently enough fails that test "
                   "however safe the gate is. Position asks something the "
                   "garbling cannot touch, so a run admits a pair the score "
                   "alone would refuse. It admits it for CONSIDERATION only; "
                   "every post-condition in collapse_duplicate_reads.py still "
                   "has to pass before any page is displaced.",
            "min_links": MIN_RUN_LINKS,
            "runs": len(runs), "served_runs": len(served_runs),
            "served_tokens_in_second_reads": sum(r["tokens_b"] for r in served_runs),
            "detail": runs,
        },
        "by_file": dict(by_file.most_common()),
        "pairs": hits,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out_fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
