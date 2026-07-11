#!/usr/bin/env python3
"""Displace a work from data/corpus/ to data/corpus_secondary/ (rank=secondary).

For a page-keyed OCR placeholder whose content is fully covered by served critical
editions (precedence ladder: open TEI > OCR), the placeholder must stop being a primary
edition but is preserved as a secondary witness, following the 2026-07-05 cutover
convention (commit a399a71): same records + "rank": "secondary", file moved to
data/corpus_secondary/.

  python3 scripts/displace_to_secondary.py <slug> --reason "covered by first1k galenus.*"

Page-level variant: --pages STEM1,STEM2,... displaces only the records whose locus
page-stem is listed (for a work that double-serves a few pages another work owns),
appending them to the work's corpus_secondary file while the rest stays primary.

Row-level variant: --loci LOCUS1,LOCUS2,... (or --loci @/path/file with one locus
per line) displaces only the exact records listed. Use it when duplication is not
page-aligned, e.g. an OCR remainder page that mixes rows covered by a served
critical edition with rows of apparatus/other authors that must stay primary.

--prune-crosswalk removes the slug's data/tlg_crosswalk.json entry: use it for
whole-work displacement of a MIS-INGESTED slug whose file never contained the
claimed work (the crosswalk reflects the delivered corpus; a rebuild via
build_id_crosswalk.py only includes works present in data/corpus, so pruning
matches what a rebuild would produce).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
SECONDARY = COG / "data" / "corpus_secondary"

_STEM = re.compile(r"^(.*?_\d{3,4})(?:\.|$)")


def stem_of(locus: str) -> str:
    m = _STEM.match(str(locus))
    return m.group(1) if m else str(locus)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--pages",
                    help="comma-separated page stems: displace only these pages' records "
                         "(the rest of the work stays primary)")
    ap.add_argument("--loci",
                    help="comma-separated exact loci, or @/path/file with one locus per "
                         "line: displace only these records (the rest stays primary)")
    ap.add_argument("--prune-crosswalk", action="store_true",
                    help="drop the slug's tlg_crosswalk.json entry (whole-work displacement "
                         "of a mis-ingested slug that never served the claimed work)")
    args = ap.parse_args()
    if args.prune_crosswalk and (args.pages or args.loci):
        raise SystemExit("--prune-crosswalk is whole-work only")
    if args.pages and args.loci:
        raise SystemExit("use --pages or --loci, not both")

    src = CORPUS / f"{args.slug}.jsonl"
    dst = SECONDARY / f"{args.slug}.jsonl"
    recs = [json.loads(l) for l in src.open() if l.strip()]
    if args.pages:
        stems = set(args.pages.split(","))
        missing = stems - {stem_of(r.get("locus", "")) for r in recs}
        if missing:
            raise SystemExit(f"ABORT: stems not in {args.slug}: {sorted(missing)}")
        keep = [r for r in recs if stem_of(r.get("locus", "")) not in stems]
        recs = [r for r in recs if stem_of(r.get("locus", "")) in stems]
    elif args.loci:
        if args.loci.startswith("@"):
            loci = {l.strip() for l in Path(args.loci[1:]).read_text().splitlines()
                    if l.strip()}
        else:
            loci = set(args.loci.split(","))
        missing = loci - {str(r.get("locus", "")) for r in recs}
        if missing:
            raise SystemExit(f"ABORT: loci not in {args.slug}: {sorted(missing)[:10]}")
        keep = [r for r in recs if str(r.get("locus", "")) not in loci]
        recs = [r for r in recs if str(r.get("locus", "")) in loci]
    else:
        keep = None
    for r in recs:
        r["rank"] = "secondary"
        r["secondary_reason"] = args.reason
    SECONDARY.mkdir(parents=True, exist_ok=True)
    prior = []
    if keep is not None and dst.exists():  # append to earlier partial displacements
        prior = [json.loads(l) for l in dst.open() if l.strip()]
    allsec = prior + recs
    allsec.sort(key=lambda r: str(r.get("locus", "")))
    if allsec:
        dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in allsec))
    else:
        print("  (no records selected; no secondary file written)")
    if keep is None:
        src.unlink()
    else:
        src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep))
    if args.prune_crosswalk:
        cw_path = COG / "data" / "tlg_crosswalk.json"
        cw = json.loads(cw_path.read_text(encoding="utf-8"))
        dropped = cw.pop(args.slug, None)
        if dropped is not None:
            cw_path.write_text(json.dumps(cw, ensure_ascii=False, indent=0))
        print(f"  crosswalk: {'dropped ' + str(dropped.get('tlg')) if dropped else 'no entry'}")
    part = ("pages " + args.pages if args.pages
            else f"{len(recs)} listed loci" if args.loci else "whole work")
    scope = f"{len(recs)} records ({part})"
    print(f"displaced {args.slug}: {scope} -> {dst.relative_to(COG)}"
          f"{'' if keep is None else f' ({len(keep)} records stay primary)'}")


if __name__ == "__main__":
    main()
