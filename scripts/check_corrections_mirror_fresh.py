#!/usr/bin/env python3
"""Fail when data/corrections_log/ claims a correction pass the text contradicts.

The corrections log is a read-only audit mirror of the upstream correction store:
`applied.jsonl` is one line per correction baked into data/corpus, and
`provenance.json` names the works that have had a correction pass. It is local and
gitignored, so a fresh clone has none of it and this check passes trivially.

Where it exists, two consumers read it. build_corpus_catalog.py and
build_provenance.py both take `provenance.json` as enrichment on top of the rows'
own `corrections` stamps, to cover the works whose stamps predate the stamping
convention. Enrichment from a STALE mirror is not neutral: it adds a claim the
served text no longer supports. When the 2026-08-21 confusion/accepted census
reverted 1,512 corrections, the mirror was left at its pre-revert state, and 12
works whose served text had gone back to raw OCR stayed in `auto_corrected_works`;
7 of them were published as `auto-corrected` in data/corpus_catalog.tsv while the
rebuilt README table already called them raw OCR. Nothing failed, because only the
upstream bake ever rewrote the mirror and a revert never did.

Two things fail here, neither of which needs the correction store:

  1. Internal consistency. provenance.json is a function of applied.jsonl - the
     works whose rows carry a hand/LLM `by` tag, against the rest - so it is
     recomputed and compared. A mismatch means one file was refreshed and the
     other was not.

  2. A work whose claim the text contradicts: provenance.json names it, and not
     one of its mirror rows has its corrected form standing in the row it names,
     while at least one has the UNCORRECTED reading standing instead. That second
     half is what makes this precise rather than noisy. A reverted row holds the
     original by construction, because the revert put it back, so this is the
     revert signature. A row whose correction was merely overwritten by a later
     fix, or whose loci were re-keyed by a carve, holds neither form and is not
     flagged - which is why the four walz_rhetores volumes and
     cyrillus-theology.collectio-dictorum, whose rows a per-treatise split
     re-keyed, do not make this permanently red.

Two things only warn, because the repair is not this repo's to make and a failing
build that stays red teaches everyone to ignore it: individual mirror rows that
show the uncorrected reading without their whole work doing so (a bake upstream
would settle those), and a mirror older than the served text, which is a hint
rather than evidence since a carve or a token repair moves the text without
touching the store.

The repair is upstream, in the pipeline that owns the store: run its
scripts/refresh_audit_mirror.py --write, then `make reports` so the catalog and
the README table are rebuilt from it.

  python3 scripts/check_corrections_mirror_fresh.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "data" / "corrections_log"
CORPUS = REPO / "data" / "corpus"

# Kept in step with the upstream refresh_audit_mirror.py, which is what writes
# the file this recomputes.
MANUAL = {"llm", "agent", "manual"}

# A Greek letter or combining diacritic, as corrections.py defines it: a form
# matches only as a whole token, never inside a longer word.
GLET = r"[Ͱ-Ͽἀ-῿̀-ͯ]"

REPAIR = ("refresh it by running `python3 scripts/refresh_audit_mirror.py "
          "--write` in the upstream OCR pipeline checkout, then rerun "
          "`make reports` so the catalog and the README table are rebuilt "
          "from it")


def standing(form: str, text: str) -> bool:
    if not form:
        return False
    return re.search(rf"(?<!{GLET}){re.escape(form)}(?!{GLET})", text) is not None


def served_rows(urn: str, cache: dict) -> dict[str, str] | None:
    if urn not in cache:
        fp = CORPUS / f"{urn}.jsonl"
        rows: dict[str, str] | None = None
        if fp.exists():
            rows = {}
            with fp.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        rows[str(row.get("locus"))] = row.get("text") or ""
        cache[urn] = rows
    return cache[urn]


def newest_corpus_mtime() -> tuple[str, float]:
    name, when = "", 0.0
    for fp in CORPUS.glob("*.jsonl"):
        mtime = fp.stat().st_mtime
        if mtime > when:
            name, when = fp.name, mtime
    return name, when


def main() -> None:
    applied = LOG / "applied.jsonl"
    prov_fp = LOG / "provenance.json"
    if not applied.exists() or not prov_fp.exists():
        print("no data/corrections_log mirror; the catalog falls back to the "
              "rows' own correction stamps")
        return

    by_urn: dict[str, list[dict]] = defaultdict(list)
    methods: dict[str, set] = defaultdict(set)
    records = 0
    with applied.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            by_urn[rec["urn"]].append(rec)
            methods[rec["urn"]].add(rec.get("by", "?"))
            records += 1

    rebuilt = {
        "corrected_works": sorted(u for u, m in methods.items() if m & MANUAL),
        "auto_corrected_works": sorted(u for u, m in methods.items()
                                       if not (m & MANUAL)),
    }
    stored = json.loads(prov_fp.read_text(encoding="utf-8"))

    problems: list[str] = []
    for key in ("corrected_works", "auto_corrected_works"):
        for slug in sorted(set(stored.get(key, [])) - set(rebuilt[key])):
            problems.append(f"provenance.json claims {slug} under {key}, but no "
                            f"row in applied.jsonl supports it")
        for slug in sorted(set(rebuilt[key]) - set(stored.get(key, []))):
            problems.append(f"applied.jsonl has {key} rows for {slug}, which "
                            f"provenance.json does not name")

    claimed = set(stored.get("corrected_works", []))
    claimed |= set(stored.get("auto_corrected_works", []))
    cache: dict = {}
    loose = 0
    for urn in sorted(claimed):
        rows = served_rows(urn, cache)
        if rows is None:
            continue                      # not served under this key; see the README
        alive = reverted = 0
        for rec in by_urn.get(urn, []):
            text = rows.get(str(rec["locus"]))
            if text is None:
                continue
            if standing(rec.get("corrected"), text):
                alive += 1
            elif standing(rec.get("original"), text):
                reverted += 1
        if reverted and not alive:
            problems.append(
                f"provenance.json calls {urn} corrected, but none of its "
                f"{len(by_urn.get(urn, []))} mirror rows is standing in the text "
                f"and {reverted} show the uncorrected reading, so its corrections "
                f"have been reverted since the mirror was written")
        elif reverted:
            loose += reverted

    warnings: list[str] = []
    if loose:
        warnings.append(
            f"{loose:,} mirror row(s) show the uncorrected reading in works that "
            f"still hold other corrections; an upstream bake would settle those")
    newest, when = newest_corpus_mtime()
    if newest and applied.stat().st_mtime < when:
        warnings.append(
            f"applied.jsonl is older than data/corpus/{newest}, which a carve or "
            f"a token repair can do without touching the store, so this is a hint "
            f"rather than evidence")

    if problems:
        print(f"data/corrections_log does not describe the served corpus "
              f"({records:,} records):", file=sys.stderr)
        for line in problems[:20]:
            print(f"    {line}", file=sys.stderr)
        if len(problems) > 20:
            print(f"    ... and {len(problems) - 20} more", file=sys.stderr)
        raise SystemExit(f"ERROR: {REPAIR}")

    print(f"corrections mirror current: {records:,} records over "
          f"{len(by_urn):,} works, provenance.json agrees with them, and every "
          f"work it calls corrected still holds a correction")
    for line in warnings:
        print(f"    note: {line}")


if __name__ == "__main__":
    main()
