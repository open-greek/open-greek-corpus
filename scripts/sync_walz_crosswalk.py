#!/usr/bin/env python3
"""Publish the TLG anchors the Walz carve identified and then dropped.

carve_cgpg_volume.py registers a crosswalk entry for every work it carves that
carries a TLG id. carve_edition_volume.py, which carved the nine Walz volumes,
records the same id in its audit and never writes it anywhere a reader can see:
six Walz works have a TLG number sitting in data/walz_carve_plan.json and no
entry in data/tlg_crosswalk.json, so they publish with no external anchor at
all. The identification was done and then lost between two scripts.

This syncs the plan into the crosswalk, so what the plan claims is what the
catalog shows. It writes nothing the plan does not already assert: a work with
`tlg: null` is skipped, not guessed at, and an id already claimed by another
slug is a hard error rather than an overwrite.

  python3 scripts/sync_walz_crosswalk.py
  python3 scripts/sync_walz_crosswalk.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
PLAN = DATA / "walz_carve_plan.json"
CW = DATA / "tlg_crosswalk.json"
AUDIT = DATA / "corpus_changes" / "walz.crosswalk-sync.json"


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def norm(tlg: str) -> str:
    """tlg0598.008 and tlg0598.tlg008 are the same id; the crosswalk spells it
    the second way and a mixed file joins against neither."""
    a, b = tlg.split(".")
    return f"{a}.{b}" if b.startswith("tlg") else f"{a}.tlg{b}"


def plan_works() -> list[dict]:
    p = json.loads(PLAN.read_text(encoding="utf-8"))
    vols = p["volumes"] if isinstance(p, dict) and "volumes" in p else p
    out = []
    for v in (vols if isinstance(vols, list) else vols.values()):
        for w in (v.get("works", []) if isinstance(v, dict) else []):
            if w.get("slug") and w.get("tlg"):
                out.append(w)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cw = json.loads(CW.read_text(encoding="utf-8"))
    by_tlg = {v["tlg"]: k for k, v in cw.items()
              if isinstance(v, dict) and v.get("tlg")}
    served = {p.stem for p in (DATA / "corpus").glob("*.jsonl")}

    add, skip = [], []
    for w in plan_works():
        slug, tlg = w["slug"], norm(w["tlg"])
        if slug in cw:
            skip.append((slug, "already in the crosswalk"))
            continue
        if slug not in served:
            skip.append((slug, "not served under this slug"))
            continue
        owner = by_tlg.get(tlg)
        if owner and owner != slug:
            fail(f"{slug}: {tlg} is already claimed by {owner}")
        add.append({"slug": slug, "tlg": tlg,
                    "cts": f"urn:cts:greekLit:{tlg}",
                    "title": w.get("title", ""),
                    "author_slug": slug.split(".")[0],
                    "printed_pages": w.get("printed_pages", "")})

    print(f"walz plan works carrying a TLG id: {len(add) + len(skip)}")
    for a in add:
        print(f"    + {a['slug'][:52]:<52} {a['tlg']}  (printed {a['printed_pages']})")
    for s, why in skip:
        print(f"      {s[:52]:<52} skipped: {why}")
    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if not add:
        print("nothing to add")
        return

    for a in add:
        cw[a["slug"]] = {"cts": a["cts"], "tlg": a["tlg"],
                         "author_slug": a["author_slug"], "title": a["title"]}
    CW.write_text(json.dumps(cw, ensure_ascii=False, indent=0) + "\n",
                  encoding="utf-8")
    AUDIT.write_text(json.dumps({
        "what": "TLG anchors that data/walz_carve_plan.json already asserted "
                "published into data/tlg_crosswalk.json",
        "date": "2026-08-09",
        "issue": "open-greek/open-greek-corpus#28",
        "why": "carve_edition_volume.py records a carved work's TLG id in its "
               "audit but, unlike carve_cgpg_volume.py, never writes it to the "
               "crosswalk, so these works published with no external anchor "
               "although the plan identified them.",
        "reverse": "delete these slugs' entries from data/tlg_crosswalk.json",
        "added": add,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {len(add)} entries, audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
