#!/usr/bin/env python3
"""Make every corpus row's `urn` field agree with the file it is in.

Two artifacts key their per-work rollups on the row's own `urn`, falling back to
the filename only when the field is missing:

    build_work_lemma_counts.py:100   counters.setdefault(rec.get("urn") or fp.stem, ...)
    build_provenance.py:55           out[rec.get("urn") or fp.stem] = rec

Everything else in this repo keys on the slug, which is the filename. For 3,913
of 3,914 served works those are the same string and the fallback never matters.
For one they are not: data/corpus/philodemus.tlg1595-tlg601.jsonl carries
`urn: tlg1595.tlg601` on all 1,761 of its rows, so the lemma table files that
work under a key no other artifact uses. data/work_token_totals.json has
tlg1595.tlg601 with 10,043 lemmatized tokens and no entry at all under
philodemus.tlg1595-tlg601, and any join against data/corpus_catalog.tsv drops
the work in silence. Nothing errors, the work simply is not there.

The field is not a second identifier. Where it disagrees with the filename it is
stale, and this rewrites it to the slug rather than teaching each consumer a
fallback, because a third consumer would have the same bug waiting for it.

This corrects text the upstream OCR pipeline delivered, so it is a correction
record like any other and reverses from its audit. The generator lives in
another repository and should stop emitting the stale value; until it does, this
is idempotent and re-running it after a delivery is safe.
tests/test_row_urns.py asserts the invariant so a new mismatch fails loudly
instead of quietly removing a work from every join.

  python3 scripts/align_row_urns_to_slugs.py
  python3 scripts/align_row_urns_to_slugs.py --apply
  python3 scripts/align_row_urns_to_slugs.py --unapply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
AUDIT = DATA / "corpus_changes" / "row-urn-slug-alignment.json"
# data/corpus ONLY. A witness file in data/corpus_secondary is named
# <slug>.<witness-kind>.jsonl, so its rows correctly carry the urn of the work
# they are a witness OF, not the filename. The first version of this swept both
# directories and proposed rewriting 7,653 rows across 46 witness files, which
# would have renamed every witness to a work that does not exist. The round trip
# is what showed it; the check output would have too, had it been read first.
DIRS = ("corpus",)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def mismatches() -> list[tuple[Path, str, dict[str, int]]]:
    """(file, slug, {stale urn: row count}) for every file that disagrees."""
    out = []
    for d in DIRS:
        for fp in sorted((DATA / d).glob("*.jsonl")):
            slug = fp.name[:-len(".jsonl")]
            counts: dict[str, int] = {}
            for line in fp.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                u = json.loads(line).get("urn")
                if u and u != slug:
                    counts[u] = counts.get(u, 0) + 1
            if counts:
                out.append((fp, slug, counts))
    return out


def rewrite(fp: Path, slug: str) -> int:
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    n = 0
    for r in rows:
        if r.get("urn") and r["urn"] != slug:
            r["urn"] = slug
            n += 1
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                  encoding="utf-8")
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    if args.unapply:
        if not AUDIT.exists():
            fail(f"{AUDIT.relative_to(REPO)} does not exist")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for blk in rec["files"]:
            fp = REPO / blk["file"]
            if sha(fp.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{blk['file']} is not in the state this audit recorded")
            rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
            # One stale value per file in every case seen; restore by index so a
            # file that carried more than one is still exact.
            for idx, u in blk["restore"]:
                rows[idx]["urn"] = u
            fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                  for r in rows), encoding="utf-8")
            if sha(fp.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {blk['file']} byte-for-byte")
        AUDIT.unlink()
        print(f"UNAPPLIED: {len(rec['files'])} file(s) restored byte-for-byte")
        return

    bad = mismatches()
    if not bad:
        print("every row's urn already matches its file's slug")
        return
    for fp, slug, counts in bad:
        for u, n in sorted(counts.items()):
            print(f"  {fp.relative_to(REPO)}: {n:,} rows say {u!r}, "
                  f"slug is {slug!r}")

    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")

    blocks = []
    for fp, slug, counts in bad:
        before = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in before.splitlines() if l.strip()]
        restore = [[i, r["urn"]] for i, r in enumerate(rows)
                   if r.get("urn") and r["urn"] != slug]
        n = rewrite(fp, slug)
        blocks.append({"file": fp.relative_to(REPO).as_posix(), "slug": slug,
                       "rows_rewritten": n, "stale_values": counts,
                       "restore": restore,
                       "sha256_before": sha(before),
                       "sha256_after": sha(fp.read_text(encoding="utf-8"))})

    AUDIT.write_text(json.dumps({
        "what": "the `urn` field on corpus rows rewritten to match the slug of "
                "the file holding them",
        "date": "2026-08-09",
        "found": "while triaging the backlog on 2026-08-09; it is not on the "
                 "tracker, because it was fixed and released in the same round "
                 "it was found in",
        "why": "build_work_lemma_counts.py and build_provenance.py key their "
               "per-work rollups on the row's urn and fall back to the filename "
               "only when it is absent, so a stale urn files the work under a "
               "key no other artifact uses and every join against "
               "corpus_catalog.tsv drops it without erroring. "
               "philodemus.tlg1595-tlg601's 10,043 lemmatized tokens were in "
               "work_token_totals.json under tlg1595.tlg601 and absent under "
               "their own slug.",
        "not_a_second_identifier": "where the field disagrees with the filename "
                                   "it is stale, not an alternative id. The slug "
                                   "is what the id layer, the catalog and every "
                                   "other artifact key on.",
        "upstream": "the OCR pipeline that delivers these rows lives in another "
                    "repository and still emits the stale value; this pass is "
                    "idempotent, so re-running it after a delivery is safe, and "
                    "tests/test_row_urns.py fails if one arrives.",
        "files": blocks,
        "rows_rewritten": sum(b["rows_rewritten"] for b in blocks),
        "reverse": "python3 scripts/align_row_urns_to_slugs.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {sum(b['rows_rewritten'] for b in blocks):,} rows in "
          f"{len(blocks)} file(s), audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
