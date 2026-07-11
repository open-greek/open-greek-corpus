#!/usr/bin/env python3
"""Re-key data/corrections_log/applied.jsonl rows to the works that serve their loci.

The corrections log is a read-only audit mirror written by the greek-ocr pipeline
(apply_corrections.py). When a COG work is renamed / re-scoped / dissolved (e.g.
thomas-patricius-anthol-dubner-v3 -> cougny-appendix-nova.didot-anthologia-v3, or the
Hercher Epistolographi catch-all rows moving to per-author works), the mirror's `urn`
keys go stale while the row loci (page stems) stay valid. This script restores the
audit linkage COG-side, without touching the greek-ocr store (read-only upstream):

  1. for every mirror row whose locus looks page-keyed (<base>_<NNNN>.<line>), find
     the work now serving that locus in data/corpus (preferred) or
     data/corpus_secondary;
  2. the row's honest key = the slug's tlg urn from data/tlg_crosswalk.json when it
     has one, else the slug itself (matching how the mirror keys works: canonical
     urns for crosswalked works, slugs/placeholders otherwise);
  3. rewrite rows whose key changed; regenerate provenance.json's corrected_works
     from the re-keyed rows (same formula as apply_corrections.py: urns with
     `by` in llm/agent).

Multi-owner stems (boundary pages split across works, e.g. a Diels FVS page
holding the end of one author and the start of the next) are adjudicated by
content: the correction's corrected/original text is matched (letter-boundary,
NFC) against each candidate work's served rows, first at the row's exact locus,
then anywhere on the stem; if content is indecisive, a locus held by exactly one
candidate decides (page splits give each work a disjoint locus range). A unique
winning key re-keys the row; anything still ambiguous (e.g. stems double-served
byte-identically by two works) is left unchanged and reported AMBIGUOUS. Rows
whose current key is itself one of the owners are kept as-is, as before.

Rows whose loci are not page-keyed (Migne cogPG.* rows keyed by bare column loci)
or whose loci no longer resolve anywhere (text later dropped/superseded) are left
unchanged - they document history and the next upstream mirror regeneration
supersedes them. Note the tlg4049.tlg001 (Cougny) rows this was written for are
also marked `retired` in the greek-ocr store (superseded by the 2026-07 qwen36
re-OCR), so they will drop out of the mirror at the next apply_corrections run;
until then the re-key keeps their audit linkage consistent with the rename.

Idempotent; re-run after any rename/dissolve batch.

  python3 scripts/rekey_corrections_log.py            # dry-run report
  python3 scripts/rekey_corrections_log.py --write
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
LOG = COG / "data" / "corrections_log" / "applied.jsonl"
PROV = COG / "data" / "corrections_log" / "provenance.json"
CW = COG / "data" / "tlg_crosswalk.json"

TIER_DIRS = ("corpus", "corpus_secondary")

_PAGE_LOCUS = re.compile(r"^(.*_\d{3,4})\.\d+$")


def stem_of(locus: str) -> str | None:
    m = _PAGE_LOCUS.match(str(locus))
    return m.group(1) if m else None


def _boundary_hit(needle: str, hay: str) -> bool:
    """Letter-boundary containment of a correction snippet in served text
    (NFC both sides; digits/punctuation count as boundaries, so a short
    snippet like 'τῇ' cannot hit inside a longer word)."""
    n = unicodedata.normalize("NFC", str(needle or "")).strip()
    if not n:
        return False
    pat = re.compile(r"(?<![^\W\d_])" + re.escape(n) + r"(?![^\W\d_])")
    return bool(pat.search(unicodedata.normalize("NFC", hay or "")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in LOG.open(encoding="utf-8") if l.strip()]
    wanted = {s for s in (stem_of(r.get("locus", "")) for r in rows) if s}
    print(f"{len(rows)} mirror rows, {len(wanted)} distinct page stems to resolve")

    # stem -> {slug} per tier; primary corpus wins over secondary
    tiers = []
    for d in TIER_DIRS:
        m: dict[str, set] = defaultdict(set)
        for fp in sorted((COG / "data" / d).glob("*.jsonl")):
            slug = fp.name[:-6]
            for line in fp.open(encoding="utf-8"):
                if not line.strip():
                    continue
                s = stem_of(json.loads(line).get("locus", ""))
                if s in wanted:
                    m[s].add(slug)
        tiers.append(m)

    cw = json.loads(CW.read_text(encoding="utf-8"))

    def key_for(slug: str) -> str:
        tlg = (cw.get(slug) or {}).get("tlg")
        return tlg or slug

    def tier_of(s: str) -> int | None:
        return 0 if tiers[0].get(s) else (1 if tiers[1].get(s) else None)

    # multi-owner stems that carry rows keyed outside the owner set need the
    # content tiebreak: load just those candidate works' served rows
    need: dict[str, int] = {}                       # stem -> owning tier
    for r in rows:
        s = stem_of(r.get("locus", ""))
        ti = tier_of(s) if s else None
        if ti is None:
            continue
        keys = {key_for(o) for o in tiers[ti][s]}
        if len(keys) > 1 and r["urn"] not in keys:
            need[s] = ti
    cand_rows: dict[tuple, dict[str, list]] = defaultdict(
        lambda: defaultdict(list))                  # (tier, slug) -> stem -> [(locus, text)]
    for ti, slug in sorted({(ti, slug) for s, ti in need.items()
                            for slug in tiers[ti][s]}):
        for line in (COG / "data" / TIER_DIRS[ti] / f"{slug}.jsonl"
                     ).open(encoding="utf-8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            s = stem_of(rec.get("locus", ""))
            if need.get(s) == ti:
                cand_rows[(ti, slug)][s].append(
                    (str(rec.get("locus")), rec.get("text", "")))

    def tiebreak(r: dict, s: str, ti: int, owners: set) -> tuple | None:
        """Adjudicate a multi-owner stem: (basis, winning key) or None."""
        loc = str(r.get("locus"))
        snippets = [x for x in (r.get("corrected"), r.get("original")) if x]
        at_locus, on_stem, holders = set(), set(), set()
        for slug in owners:
            recs = cand_rows[(ti, slug)].get(s, [])
            here = [t for l, t in recs if l == loc]
            if here:
                holders.add(slug)
            if any(_boundary_hit(sn, t) for sn in snippets for t in here):
                at_locus.add(slug)
            elif any(_boundary_hit(sn, t) for sn in snippets for _, t in recs):
                on_stem.add(slug)
        for basis, cands in (("content@locus", at_locus),
                             ("content@stem", at_locus | on_stem),
                             ("sole locus holder", holders)):
            ks = {key_for(o) for o in cands}
            if len(ks) == 1:
                return basis, ks.pop()
        return None

    changed = Counter()
    tiebroken = Counter()
    ambiguous = Counter()
    unresolved = 0
    for r in rows:
        s = stem_of(r.get("locus", ""))
        ti = tier_of(s) if s else None
        if not s:
            continue
        if ti is None:
            unresolved += 1
            continue
        owners = tiers[ti][s]
        keys = {key_for(o) for o in owners}
        if len(keys) > 1:
            if r["urn"] in keys:      # current key is one of the owners: keep it
                continue
            hit = tiebreak(r, s, ti, owners)
            if hit is None:
                ambiguous[(r["urn"], tuple(sorted(keys)))] += 1
                continue
            basis, new = hit
            tiebroken[(r["urn"], new, basis)] += 1
            r["urn"] = new
            continue
        new = keys.pop()
        if new != r["urn"]:
            changed[(r["urn"], new)] += 1
            r["urn"] = new

    print(f"unresolved loci (left unchanged): {unresolved}")
    for (old, new), n in sorted(changed.items()):
        print(f"  rekey {n:6d}  {old} -> {new}")
    for (old, new, basis), n in sorted(tiebroken.items()):
        print(f"  tiebreak {n:4d}  {old} -> {new} ({basis})")
    for (old, opts), n in sorted(ambiguous.items()):
        print(f"  AMBIGUOUS {n} rows keyed {old}: stem served by {opts} (unchanged)")

    if not args.write:
        print("DRY RUN - nothing written (use --write)")
        return
    rows.sort(key=lambda r: (r["urn"], str(r["locus"])))
    LOG.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                   encoding="utf-8")
    corrected = sorted({r["urn"] for r in rows if r.get("by") in ("llm", "agent")})
    PROV.write_text(json.dumps({"corrected_works": corrected},
                               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"rewrote {LOG.relative_to(COG)} "
          f"({sum(changed.values())} rows re-keyed, "
          f"{sum(tiebroken.values())} by content tiebreak) "
          f"and provenance.json ({len(corrected)} corrected works)")


if __name__ == "__main__":
    main()
