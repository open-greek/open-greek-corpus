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
from collections import Counter, defaultdict
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
LOG = COG / "data" / "corrections_log" / "applied.jsonl"
PROV = COG / "data" / "corrections_log" / "provenance.json"
CW = COG / "data" / "tlg_crosswalk.json"

_PAGE_LOCUS = re.compile(r"^(.*_\d{3,4})\.\d+$")


def stem_of(locus: str) -> str | None:
    m = _PAGE_LOCUS.match(str(locus))
    return m.group(1) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in LOG.open(encoding="utf-8") if l.strip()]
    wanted = {s for s in (stem_of(r.get("locus", "")) for r in rows) if s}
    print(f"{len(rows)} mirror rows, {len(wanted)} distinct page stems to resolve")

    # stem -> {slug} per tier; primary corpus wins over secondary
    tiers = []
    for d in ("corpus", "corpus_secondary"):
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

    changed = Counter()
    ambiguous = Counter()
    unresolved = 0
    for r in rows:
        s = stem_of(r.get("locus", ""))
        if not s:
            continue
        owners = tiers[0].get(s) or tiers[1].get(s) or set()
        if not owners:
            unresolved += 1
            continue
        keys = {key_for(o) for o in owners}
        if len(keys) > 1:
            if r["urn"] in keys:      # current key is one of the owners: keep it
                continue
            ambiguous[(r["urn"], tuple(sorted(keys)))] += 1
            continue
        new = keys.pop()
        if new != r["urn"]:
            changed[(r["urn"], new)] += 1
            r["urn"] = new

    print(f"unresolved loci (left unchanged): {unresolved}")
    for (old, new), n in sorted(changed.items()):
        print(f"  rekey {n:6d}  {old} -> {new}")
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
    print(f"rewrote {LOG.relative_to(COG)} ({sum(changed.values())} rows re-keyed) "
          f"and provenance.json ({len(corrected)} corrected works)")


if __name__ == "__main__":
    main()
