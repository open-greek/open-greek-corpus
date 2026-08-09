#!/usr/bin/env python3
"""Carve a printed volume served as one dump into its per-treatise corpus files.

About 1.29M tokens of Byzantine rhetorical commentary sit in ten volumes under
fabricated urns of the form ocr.walz_rhetores_v7pt1, one per printed volume,
rather than as the roughly sixty distinct treatises they contain (issue #10).
Most of those treatises have no other open digital text, and under a volume urn
none of them can be cited, filtered or attributed.

Driven by a carve plan, data/walz_carve_plan.json by default and any other with
--plan. It was written for Walz and generalized when Spengel, Rhetores Graeci
vol. III turned out to have the same defect under a different urn (issue #22),
so nothing here is Walz-specific except that default. Two things about the plan
shape are deliberate.

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

A work whose slug this corpus already serves as primary from a better edition
carries rank "secondary" (issue #14) and is written to data/corpus_secondary/
with rank and secondary_reason on every row, never competing with the served
primary. In v3 that is 88,507 of 151,404 tokens, because 58% of the volume is
Hermogenes already served from Rabe. Filing them secondary visibly cuts the
published primary figure, and it should: serving the same work twice as primary
is a defect this project already tracks elsewhere.

A reversible audit lands in data/corpus_changes/, carrying the full locus map
old to new, so the carve can be undone and any correction record keyed to the
old locus can still be placed.

  carve_edition_volume.py --volume v7pt1                 # check only, writes nothing
  carve_edition_volume.py --volume v7pt1 --apply
  carve_edition_volume.py --plan data/spengel_carve_plan.json --volume rg3
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
SECONDARY = DATA / "corpus_secondary"
CHANGES = DATA / "corpus_changes"
DEFAULT_PLAN = DATA / "walz_carve_plan.json"

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


def _doc_key(locus: str) -> tuple:
    """(scan, row) as numbers where possible, for true reading order.

    Falls back to the raw string for an ordinal that is not a plain integer, so
    an unexpected locus shape sorts predictably instead of raising.
    """
    scan, _, row = locus.rsplit("_", 1)[1].partition(".")
    try:
        return (int(scan), 0, int(row))
    except ValueError:
        return (int(scan) if scan.isdigit() else 0, 1, row)


def scan_of(locus: str) -> int:
    return int(locus.rsplit("_", 1)[1].split(".")[0])


def row_of(locus: str) -> str:
    return locus.rsplit(".", 1)[1]


def carve(vol: dict, apply: bool, plan_path: Path) -> int:
    urn = vol["urn"]
    src = CORPUS / f"{urn}.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Document order, not file order. The partition below slices this list
    # between consecutive starts, so it has to be the order the text is READ in.
    # Five of the Walz files are written with their rows sorted lexicographically
    # inside a page - 1, 10, 11, ... 19, 2, 20 - which puts .9 last. A work
    # starting mid-page at .9 would then have taken that row alone and jumped to
    # the next page, leaving most of its first page in the previous work, and
    # nothing would have caught it: every row still lands in exactly one bucket,
    # so the partition is exact and token conservation passes. The five volumes
    # carved so far happened to be in numeric order, which is the only reason
    # this never fired (issue #10).
    scrambled = sorted({scan_of(r["locus"]) for a, b in zip(rows, rows[1:])
                        if _doc_key(a["locus"]) > _doc_key(b["locus"])
                        for r in (a,) if scan_of(a["locus"]) == scan_of(b["locus"])})
    rows.sort(key=lambda r: _doc_key(r["locus"]))
    if scrambled:
        print(f"  read order: {len(scrambled)} page(s) were not in numeric row "
              f"order in the file and have been sorted "
              f"({', '.join(str(p) for p in scrambled[:6])}"
              f"{', ...' if len(scrambled) > 6 else ''})")
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
            if w.get("rank") == "secondary":
                nr["rank"] = "secondary"
                nr["secondary_reason"] = w["secondary_reason"]
                # Names the edition this witness is, so several can sit under
                # one slug and a re-run replaces its own rows instead of the
                # other edition's. Four slugs here already carried a Walz
                # witness before Spengel arrived.
                nr["witness"] = vol["edition_title"]
            new_rows.append(nr)
        written.append((w["slug"], new_rows))
        t = sum(tokens(r["text"]) for r in got)
        first, last = new_rows[0]["locus"], new_rows[-1]["locus"]
        mark = " [secondary]" if w.get("rank") == "secondary" else ""
        print(f"{w['n']:>4s} {first:>5s}-{last:<9s} {len(got):>6,} {t:>9,}  "
              f"{w['slug']}{mark}")
    res_urn_shown = vol.get("residual_urn", urn)
    print(f"{'':>4s} {'residual':>10s} {len(residual):>7,} {res_tokens:>9,}  "
          f"{'stays in' if res_urn_shown == urn else 'moves to'} {res_urn_shown}")

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

    # Resolved here, above the first write. It is only a label in the audit,
    # but computing it afterwards is how a bad --plan path turned into a corpus
    # mutated with no record of it: every file had already been rewritten when
    # the audit raised. Anything that can fail belongs before the mutation.
    try:
        plan_name = str(plan_path.resolve().relative_to(REPO))
    except ValueError:
        plan_name = plan_path.name
    old_hash = hashlib.sha256(src.read_bytes()).hexdigest()
    rank_of = {w["slug"]: w.get("rank", "primary") for w in vol["works"]}
    for slug, new_rows in written:
        dest = SECONDARY if rank_of[slug] == "secondary" else CORPUS
        dest.mkdir(parents=True, exist_ok=True)
        fp = dest / f"{slug}.jsonl"
        keep: list[dict] = []
        if rank_of[slug] == "secondary" and fp.exists():
            # A work can be witnessed by more than one edition, so this adds a
            # witness rather than replacing the file. Rows from THIS edition go
            # first, which is what makes a re-run idempotent instead of piling
            # up copies.
            keep = [r for r in
                    (json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                     if l.strip())
                    if r.get("witness") != vol["edition_title"]]
            if keep:
                print(f"  {slug}: keeping {len(keep)} rows from another witness")
        fp.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n"
                    for r in keep + new_rows),
            encoding="utf-8")
    # The residual normally keeps the volume's own urn, because for Walz that
    # urn already names the volume. Spengel III did not: the whole book was
    # served under one treatise's slug, so leaving the front matter and the
    # index there would keep the defect the carve exists to remove, just
    # smaller. Where the plan gives a residual_urn, the leftovers move to it.
    res_urn = vol.get("residual_urn", urn)
    for r in residual:
        r["urn"] = res_urn
    res_fp = CORPUS / f"{res_urn}.jsonl"
    if residual:
        res_fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                  for r in residual), encoding="utf-8")
        if res_fp != src:
            src.unlink()
    else:
        # Nothing left over, so the volume urn stops existing rather than
        # becoming an empty served file. v7pt2 is the first volume carved end to
        # end with no front matter and no index, and a zero-row work in
        # data/corpus would be counted, catalogued and served as a work.
        src.unlink()
        if res_fp != src and res_fp.exists():
            res_fp.unlink()
        print(f"  residual is empty; {src.name} removed rather than left as a "
              f"zero-row work")

    audit = {
        "what": f"per-treatise carve of {urn}, driven by {plan_name}",
        "date": vol.get("date", "2026-08-05"),
        "issue": vol.get("issue", "open-greek/open-greek-corpus#10"),
        "source_urn": urn,
        "source_sha256_before": old_hash,
        # None when the volume was carved end to end and its urn no longer
        # exists. Computed from the file only if it is still there: reading it
        # unconditionally raised AFTER every work had been written, which is the
        # audit-after-mutation trap this script was already fixed for once.
        "source_sha256_after": (hashlib.sha256(res_fp.read_bytes()).hexdigest()
                                if res_fp.exists() else None),
        "residual_removed": not residual,
        "residual_urn": res_urn,
        "offset_zones": zones or [{"scans": None, "offset": default_offset}],
        "dropped_scans": sorted(drop_scans),
        "dropped_rows": [{"locus": r["locus"], "text": r["text"]} for r in dropped],
        "rows_before": len(rows),
        "tokens_before": src_tokens,
        "works": [{"n": w["n"], "slug": w["slug"], "title": w["title"],
                   "tlg": w["tlg"], "printed_pages": w["printed_pages"],
                   "rank": w.get("rank", "primary"),
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
    # A urn can be carved more than once: Walz III took its twelve non-Hermogenean
    # treatises in one pass and the four Hermogenean ones in another. Writing both
    # to the same filename silently replaced the first record, taking 3,507 locus
    # mappings with it and leaving that carve unreversible, so a later carve of the
    # same urn is named for the plan entry that produced it.
    out = CHANGES / f"{urn}.per-treatise-carve.json"
    if out.exists():
        try:
            prior = json.loads(out.read_text(encoding="utf-8"))
        except ValueError:
            prior = {}
        if (prior.get("issue"), prior.get("date")) != (audit["issue"], audit["date"]):
            out = CHANGES / f"{urn}.per-treatise-carve.{vol['volume']}.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")

    # Register the TLG ids this carve just claimed. Recording them in the audit
    # and nowhere else is what left nine Walz works published with no external
    # anchor although the plan had identified six of them all along: the id was
    # found and then lost between two scripts (21d77cd, issue #28). Same
    # behaviour and same guards as carve_cgpg_volume.update_crosswalk.
    xw = update_crosswalk(vol)
    if xw:
        print(f"crosswalk: {len(xw)} TLG anchor(s) registered "
              + ", ".join(f"{e['slug'].split('.')[-1][:28]}={e['tlg']}" for e in xw))

    print(f"\ncarved {len(written)} works; audit -> {out.relative_to(REPO)}")
    print("run `make ids` to mint the ogc ids and rebuild the work index.")
    return 0


def update_crosswalk(vol_plan: dict) -> list[dict]:
    """Publish each carved work's TLG id, mirroring carve_cgpg_volume.py.

    Refuses rather than overwrites: a slug already mapped to a different id, or
    an id already held by another slug, is a hard error. A work whose plan entry
    has no tlg is skipped, never guessed at.
    """
    cw_path = DATA / "tlg_crosswalk.json"
    cw = json.loads(cw_path.read_text(encoding="utf-8"))
    added = []
    for w in vol_plan["works"]:
        tlg = w.get("tlg")
        if not tlg or w.get("rank") == "secondary":
            continue
        a, b = tlg.split(".")
        tlg = f"{a}.{b}" if b.startswith("tlg") else f"{a}.tlg{b}"
        slug = w["slug"]
        cur = cw.get(slug)
        if cur:
            if cur.get("tlg") not in (None, "", tlg):
                raise SystemExit(f"crosswalk: {slug} already maps to {cur['tlg']}")
            continue
        for other, oe in cw.items():
            if isinstance(oe, dict) and oe.get("tlg") == tlg:
                raise SystemExit(f"crosswalk: {tlg} already claimed by {other}")
        cw[slug] = {"cts": f"urn:cts:greekLit:{tlg}", "tlg": tlg,
                    "author_slug": slug.split(".")[0], "title": w.get("title", "")}
        added.append({"slug": slug, "tlg": tlg})
    if added:
        cw_path.write_text(json.dumps(cw, ensure_ascii=False, indent=0) + "\n",
                           encoding="utf-8")
        with open(DATA / "tlg_crosswalk.tsv", "w", encoding="utf-8") as f:
            f.write("slug\tcts_urn\ttlg\n")
            for slug, d in sorted(cw.items()):
                other = next((f"{k}:{v}" for k, v in d.items()
                              if k not in ("cts", "tlg", "author_slug", "title")), "")
                f.write(f"{slug}\t{d.get('cts', '')}\t{d.get('tlg', other)}\n")
    return added


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volume", required=True)
    ap.add_argument("--plan", type=lambda p: Path(p).resolve(),
                    default=DEFAULT_PLAN)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    vols = {v["volume"]: v for v in plan["volumes"]}
    if args.volume not in vols:
        raise SystemExit(f"no plan for {args.volume}; have {', '.join(sorted(vols))}")
    raise SystemExit(carve(vols[args.volume], args.apply, args.plan))


if __name__ == "__main__":
    main()
