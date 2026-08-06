#!/usr/bin/env python3
"""Carve a Walz Rhetores Graeci volume dump into per-treatise corpus files.

About 1.29M tokens of Byzantine rhetorical commentary sit in ten volumes under
fabricated urns of the form ocr.walz_rhetores_v7pt1, one per printed volume,
rather than as the roughly sixty distinct treatises they contain (issue #10).
Most of those treatises have no other open digital text, and under a volume urn
none of them can be cited, filtered or attributed.

Driven by data/walz_carve_plan.json. Two things about that plan shape are
deliberate.

A work carries a START locus and no end. The script assigns every row from one
start up to the next, so the partition is exact by construction and a gap or an
overlap is not expressible. Ranges with explicit ends are how a carve mis-files
text, and the exposure is not evenly spread: in v7pt1 item IX is 86% of the
volume, so a one-page slip at its end would mis-file more than every other
boundary combined. Here its end is simply where the trailing residual begins.

Loci key to the printed Walz page (issue #15), derived arithmetically as
scan - offset, keeping the source row ordinal: scan 46 row 9 becomes 34.9. The
ordinal is NOT renumbered per work. Two works share printed page 34, and
renumbering would put both of them at 34.1 and stop the ordinal meaning a line
on the page, which is the whole reason for keying to the printed page. The
run's pages_pg.json is deliberately not consulted: it misreads roughly fourteen
folios in v7pt1, and the arithmetic is exact.

The offset is a list of zones, because a scanned volume is not always a clean
arithmetic sequence. v6 has both defects at once: scans 586-587 are a second
image of printed 564-565, and printed 580-581 were never scanned. Their effects
cancel, so the offset is -20 at both ends of the volume and -22 for the fourteen
pages between them, and a carve that checks only its endpoints validates and
then mis-numbers those fourteen. Dropped scans are archived verbatim in the
audit; a page number produced twice anywhere in the volume is a hard failure,
which is the check that would have caught a wrong zone.

Verification is hard-fail and runs before anything is written:

  * exact row partition - every row lands in exactly one bucket, and the buckets
    sum to the input;
  * exact Greek-token conservation, counted with build_public_corpus._GK, the
    corpus's own tokenizer. Not a reimplementation: counting the same file with
    a hand-written Greek class gives 167,847 against the published 167,389, and
    a postcondition that fails for that reason is worse than none;
  * an incipit anchor per work, normalized, which must be found in the row the
    plan names as its start;
  * target loci unique within each new work.

A reversible audit lands in data/corpus_changes/, carrying the full locus map
old to new, so the carve can be undone and any correction record keyed to the
old locus can still be placed.

  carve_walz_volume.py --volume v7pt1           # check only, writes nothing
  carve_walz_volume.py --volume v7pt1 --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CHANGES = DATA / "corpus_changes"
PLAN = DATA / "walz_carve_plan.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402


def tokens(text: str) -> int:
    return len(_GK.findall(text or ""))


def norm(s: str) -> str:
    """Accent- and case-blind, for the incipit anchors. The display titles are
    OCR'd from capitals and carry Latin homoglyphs (ANΩNΥMOY for ΑΝΩΝΥΜΟΥ), so
    an exact match would fail on the very rows the anchors exist to confirm."""
    d = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in d if not unicodedata.combining(c) and c.isalnum())


def offset_for(scan: int, zones: list[dict], default: int) -> int | None:
    for z in zones:
        lo, hi = z["scans"]
        if lo <= scan <= hi:
            return z["offset"]
    return default


def scan_of(locus: str) -> int:
    return int(locus.rsplit("_", 1)[1].split(".")[0])


def row_of(locus: str) -> str:
    return locus.rsplit(".", 1)[1]


def carve(vol: dict, apply: bool) -> int:
    urn = vol["urn"]
    src = CORPUS / f"{urn}.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    order = [r["locus"] for r in rows]
    index = {loc: i for i, loc in enumerate(order)}
    zones = vol.get("offset_zones", [])
    default_offset = vol.get("printed_to_scan_offset")
    drop_scans = set(vol.get("drop_scans", []))

    # The partition, by consecutive starts. Anything before the first work is
    # front matter and anything from the trailing marker on is the tail; both
    # stay in the volume file as residual.
    starts = [(w["start"], w) for w in vol["works"]]
    for loc, w in starts:
        if loc not in index:
            print(f"  FAIL: start locus {loc} (item {w['n']}) is not in {urn}")
            return 1
    bounds = [index[loc] for loc, _ in starts]
    if bounds != sorted(bounds):
        print("  FAIL: the plan's start loci are not in document order")
        return 1
    head = index[vol["front_matter_before"]]
    # Optional: v7pt1 ends with Addenda et Corrigenda that would otherwise be
    # carved into its last work; v6 simply runs out of text, so its last work
    # ends at the last row.
    tail = index[vol["trailing_residual_from"]] if vol.get("trailing_residual_from") else len(rows)

    dropped = [r for r in rows if scan_of(r["locus"]) in drop_scans]
    buckets: dict[str, list[dict]] = {}
    for i, w in enumerate(vol["works"]):
        stop = bounds[i + 1] if i + 1 < len(bounds) else tail
        buckets[w["slug"]] = [r for r in rows[bounds[i]:stop]
                              if scan_of(r["locus"]) not in drop_scans]
    residual = [r for r in rows[:head] + rows[tail:]
                if scan_of(r["locus"]) not in drop_scans]

    assigned = sum(len(v) for v in buckets.values()) + len(residual) + len(dropped)
    if assigned != len(rows):
        print(f"  FAIL: partition covers {assigned} rows of {len(rows)}")
        return 1

    src_tokens = sum(tokens(r["text"]) for r in rows)
    out_tokens = sum(tokens(r["text"]) for v in buckets.values() for r in v)
    res_tokens = sum(tokens(r["text"]) for r in residual)
    drop_tokens = sum(tokens(r["text"]) for r in dropped)
    if out_tokens + res_tokens + drop_tokens != src_tokens:
        print(f"  FAIL: token conservation {out_tokens} + {res_tokens} + "
              f"{drop_tokens} != {src_tokens}")
        return 1

    # Incipit anchors. Checked on the row the plan names, which is usually the
    # start but need not be: a page that opens with a running head carries its
    # display title one row down, and the work still begins at the top of its
    # page. Naming the anchor row separately keeps the check strict rather than
    # weakening it to match whatever happens to be at the start.
    for w in vol["works"]:
        at = w.get("incipit_locus", w["start"])
        if at not in index:
            print(f"  FAIL: item {w['n']} anchor locus {at} is not in {urn}")
            return 1
        want, got = norm(w["incipit_check"]), norm(rows[index[at]]["text"])
        if want not in got:
            print(f"  FAIL: item {w['n']} anchor {w['incipit_check']!r} "
                  f"not in {at}: {rows[index[at]]['text'][:70]!r}")
            return 1

    zone_desc = (", ".join(f"scans {z['scans'][0]}-{z['scans'][1]} at -{z['offset']}"
                           for z in zones)
                 if zones else f"-{default_offset} throughout")
    print(f"{urn}: {len(rows):,} rows, {src_tokens:,} tokens (corpus tokenizer)")
    print(f"  offset {zone_desc}")
    if dropped:
        print(f"  dropping {len(dropped)} rows on duplicate scans "
              f"{sorted(drop_scans)} ({drop_tokens:,} tokens), archived in the audit")
    print(f"{'item':>4s} {'printed':>10s} {'rows':>7s} {'tokens':>9s}  slug")
    locus_map: dict[str, str] = {}
    written: list[tuple[str, list[dict]]] = []
    for w in vol["works"]:
        got = buckets[w["slug"]]
        new_rows, seen = [], set()
        for r in got:
            off = offset_for(scan_of(r["locus"]), zones, default_offset)
            if off is None:
                print(f"  FAIL: no offset zone covers scan {scan_of(r['locus'])}")
                return 1
            new_locus = f"{scan_of(r['locus']) - off}.{row_of(r['locus'])}"
            if new_locus in seen:
                print(f"  FAIL: duplicate target locus {new_locus} in {w['slug']}")
                return 1
            seen.add(new_locus)
            locus_map[r["locus"]] = f"{w['slug']}:{new_locus}"
            nr = dict(r)
            nr["locus"], nr["urn"] = new_locus, w["slug"]
            new_rows.append(nr)
        written.append((w["slug"], new_rows))
        t = sum(tokens(r["text"]) for r in got)
        first, last = new_rows[0]["locus"], new_rows[-1]["locus"]
        print(f"{w['n']:>4s} {first:>5s}-{last:<9s} {len(got):>6,} {t:>9,}  {w['slug']}")
    print(f"{'':>4s} {'residual':>10s} {len(residual):>7,} {res_tokens:>9,}  "
          f"stays in {urn}")

    # A printed page must not be produced twice anywhere in the volume. This is
    # the check that catches a wrong offset zone: v6's duplicate leaf and its
    # missing leaf cancel, so the offset is the same at both ends of the volume
    # and an endpoint check passes while the fourteen pages between them are
    # numbered two too high. Here that shows up as printed 564 and 565 existing
    # twice, which is not a thing a book does.
    seen_pages: dict[str, str] = {}
    for slug, new_rows in written:
        for r in new_rows:
            page = r["locus"].split(".")[0]
            owner = seen_pages.setdefault(page, slug)
            if owner != slug and page not in vol.get("shared_pages", []):
                print(f"  FAIL: printed page {page} is produced by both "
                      f"{owner} and {slug}")
                return 1

    if not apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return 0

    old_hash = hashlib.sha256(src.read_bytes()).hexdigest()
    for slug, new_rows in written:
        (CORPUS / f"{slug}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in new_rows),
            encoding="utf-8")
    src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in residual),
                   encoding="utf-8")

    audit = {
        "what": f"per-treatise carve of {urn}, driven by data/walz_carve_plan.json",
        "date": "2026-08-05",
        "issue": "open-greek/open-greek-corpus#10",
        "source_urn": urn,
        "source_sha256_before": old_hash,
        "source_sha256_after": hashlib.sha256(src.read_bytes()).hexdigest(),
        "offset_zones": zones or [{"scans": None, "offset": default_offset}],
        "dropped_scans": sorted(drop_scans),
        "dropped_rows": [{"locus": r["locus"], "text": r["text"]} for r in dropped],
        "rows_before": len(rows),
        "tokens_before": src_tokens,
        "works": [{"n": w["n"], "slug": w["slug"], "title": w["title"],
                   "tlg": w["tlg"], "printed_pages": w["printed_pages"],
                   "rows": len(buckets[w["slug"]]),
                   "tokens": sum(tokens(r["text"]) for r in buckets[w["slug"]])}
                  for w in vol["works"]],
        "residual_rows": len(residual),
        "residual_tokens": res_tokens,
        "dropped_tokens": drop_tokens,
        "locus_map": locus_map,
        "reverse": "restore by mapping each locus_map value back to its key and "
                   "concatenating the per-work files with the residual in locus order",
    }
    out = CHANGES / f"{urn}.per-treatise-carve.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"\ncarved {len(written)} works; audit -> {out.relative_to(REPO)}")
    print("run `make ids` to mint the ogc ids and rebuild the work index.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volume", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    vols = {v["volume"]: v for v in plan["volumes"]}
    if args.volume not in vols:
        raise SystemExit(f"no plan for {args.volume}; have {', '.join(sorted(vols))}")
    raise SystemExit(carve(vols[args.volume], args.apply))


if __name__ == "__main__":
    main()
