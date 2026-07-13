#!/usr/bin/env python3
"""Rebuild data/corpus_editions.json from the corpus files themselves.

corpus_editions is DERIVED metadata - one row per work (edition / source / license,
passage count, token count). Deriving it from data/corpus/*.jsonl, the source of truth,
rather than having every ingester read-modify-write the shared file, avoids losing rows
when two writers race: this repo's own ingest and the upstream OCR pipeline's delivery both
touch it, and an interleaved write silently dropped ~90 delivered OCR works (~15M tokens).
Run this after any ingest (or delivery) instead of trusting incremental updates.

  python scripts/reconcile_corpus_editions.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
CE = REPO / "data" / "corpus_editions.json"
WORK_IDS = REPO / "data" / "work_ids.json"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _load_work_ids() -> dict:
    """Map served slug -> opaque ogc id from the persistent ledger, if present.
    A brand-new work not yet minted simply gets no id here until
    build_id_registry.py runs; re-running this reconcile then fills it in."""
    if not WORK_IDS.exists():
        return {}
    works = json.loads(WORK_IDS.read_text(encoding="utf-8")).get("works", {})
    return {e["slug"]: i for i, e in works.items() if e.get("status") == "served"}


def main() -> None:
    from collections import defaultdict

    slug_to_id = _load_work_ids()
    ce = {}
    for fp in sorted(CORPUS.glob("*.jsonl")):
        n_pass = n_tok = 0
        # A file can carry more than one edition (page-level upgrades leave a
        # work mostly on the new edition with a few pages on another). Label the
        # work by the edition serving the MOST Greek tokens (its dominant served
        # text), not by whichever record happens to sort first; this is only the
        # single per-work rollup label.
        by_ed_tok = defaultdict(int)
        ed_meta = {}
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            n_pass += 1
            gk = sum(1 for t in r["text"].split() if _GK.search(t))
            n_tok += gk
            ed = r.get("edition")
            by_ed_tok[ed] += gk
            ed_meta.setdefault(ed, (r.get("source"), r.get("license")))
        if n_pass and by_ed_tok:
            # dominant edition = most Greek tokens; ties break on first-seen (dict order)
            edition = max(by_ed_tok, key=lambda e: by_ed_tok[e])
            source, license_ = ed_meta[edition]
            slug = fp.name[:-6]
            row = {"edition": edition, "license": license_, "source": source,
                   "n_passages": n_pass, "n_tokens": n_tok}
            # The opaque work id (from the ledger) is the canonical anchor; keep
            # it alongside the derived edition metadata so consumers of this file
            # get the stable id without a second join.
            if slug in slug_to_id:
                row["id"] = slug_to_id[slug]
            ce[slug] = row
    # Atomic write (temp + rename) so a concurrent reader - a gold annotation pass
    # reads this file while an ingest reconciles it - never sees a half-written file.
    _tmp = CE.with_name(CE.name + ".tmp")
    _tmp.write_text(json.dumps(ce, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    os.replace(_tmp, CE)
    print(f"reconciled corpus_editions: {len(ce)} works, "
          f"{sum(m['n_tokens'] for m in ce.values()):,} tokens")


if __name__ == "__main__":
    main()
