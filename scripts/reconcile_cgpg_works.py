#!/usr/bin/env python3
"""Reconcile data/cgpg_works.json against the served corpus.

cgpg_works.json is a vendored delivery (baseline commit): per CGPG volume, the
TLG works it covers and, for kind="work" units, whether calfa-co's text is the
chosen serving route (cgpg_chosen). The corpus has moved since the baseline
(e.g. Cyril, Commentarii in Joannem is served from our own PG 74 Qwen OCR, so
calfa's PG073 text was never ingested), and nothing regenerated the file.

This script re-derives the serving status of every kind="work" entry from
data/corpus_editions.json: an entry whose work is served from a non-cgpg source
gets cgpg_chosen=false plus a superseded_by block naming what actually serves
it; an entry whose work is served from cgpg keeps (or regains) cgpg_chosen.
Volume units (cogPG.*) are left untouched. Idempotent and deterministic; the
file is never hand-edited.

  python3 scripts/reconcile_cgpg_works.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from crosswalk import slug_for  # noqa: E402

CGPG_WORKS = os.path.join(REPO, "data", "cgpg_works.json")
CORPUS_EDITIONS = os.path.join(REPO, "data", "corpus_editions.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(CGPG_WORKS, encoding="utf-8") as f:
        vols = json.load(f)
    with open(CORPUS_EDITIONS, encoding="utf-8") as f:
        editions = json.load(f)

    changed = []
    for vol in vols:
        if vol.get("kind") != "work":
            continue
        slug = slug_for(vol["urn"], warn=False)
        served = editions.get(slug)
        served_src = (served or {}).get("source")
        if served_src == "cgpg":
            if not vol.get("cgpg_chosen"):
                vol["cgpg_chosen"] = True
                vol.pop("superseded_by", None)
                changed.append((vol["volume"], "restored cgpg_chosen"))
            continue
        note = (
            f"served from source '{served_src}' edition "
            f"'{served.get('edition')}'" if served else "work not served"
        )
        superseded = {
            "slug": slug,
            "source": served_src,
            "edition": (served or {}).get("edition"),
            "n_tokens": (served or {}).get("n_tokens"),
        } if served else {"slug": slug}
        if vol.get("cgpg_chosen") or vol.get("superseded_by") != superseded:
            vol["cgpg_chosen"] = False
            vol["superseded_by"] = superseded
            changed.append((vol["volume"], note))
        for w in vol.get("works", []):
            if w.get("cgpg_chosen"):
                w["cgpg_chosen"] = False

    if changed:
        for volume, note in changed:
            print(f"  {volume}: {note}")
    else:
        print("  nothing to reconcile")

    if not args.dry_run and changed:
        with open(CGPG_WORKS, "w", encoding="utf-8") as f:
            json.dump(vols, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"wrote {os.path.relpath(CGPG_WORKS, REPO)}")


if __name__ == "__main__":
    main()
