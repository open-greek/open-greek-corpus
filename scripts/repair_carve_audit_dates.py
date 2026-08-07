#!/usr/bin/env python3
"""Correct CGPG carve audits that inherited the plan file's authoring date.

carve_cgpg_volume.py used to fall back to `_meta.date` in the carve plan when a
volume entry carried no date of its own, and no entry ever did. That was
invisible while the carves and the plan were the same week. It stopped being
invisible once carving continued: PG067 ran on 2026-08-06 and PG113 and PG139 on
2026-08-07, and all three audit records claim 2026-07-31 (issue #29).

The date matters more in these files than in most. An audit record exists to let
someone reconstruct or reverse a change, and every other field in it can be
checked against the corpus - the hashes, the locus map, the token conservation.
The date is the one thing that cannot, so a wrong one is not self-correcting.

The plan now carries a real per-volume date, taken from the commit that first
added each audit, and the fallback is gone. This syncs the records to it and
keeps what they used to say, for the same reason the corrections themselves are
kept reversible: a record that quietly changes its own account of when it
happened is worth less than one that shows the correction.

  python3 scripts/repair_carve_audit_dates.py            # report
  python3 scripts/repair_carve_audit_dates.py --apply
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
PLAN = DATA / "cgpg_carve_plan.json"
CHANGES = DATA / "corpus_changes"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    wrong = []
    for vol_plan in plan["volumes"]:
        vol, want = vol_plan["volume"], vol_plan.get("date")
        fp = CHANGES / f"cogPG.{vol}.per-work-split.json"
        if not want or not fp.exists():
            continue
        rec = json.loads(fp.read_text(encoding="utf-8"))
        have = rec.get("_meta", {}).get("date")
        if have != want:
            wrong.append((vol, fp, rec, have, want))

    if not wrong:
        print("every carve audit's date matches its plan entry; nothing to do")
        return
    print(f"{len(wrong)} audit record(s) dated before the carve they record:")
    for vol, _, _, have, want in wrong:
        print(f"  {vol:<9} says {have}  ->  actually carved {want}")
    if not args.apply:
        print("\nreport only; re-run with --apply.")
        return

    for vol, fp, rec, have, want in wrong:
        rec.setdefault("superseded", []).append({
            "field": "_meta.date", "was": have, "now": want,
            "corrected": "2026-08-07",
            "issue": "open-greek/open-greek-corpus#29",
            "why": "carve_cgpg_volume.py fell back to the carve plan's _meta.date "
                   "when the volume entry had none, which no entry did, so this "
                   "record was stamped with the date the plan file was written "
                   "rather than the date the carve ran. The real date is the "
                   "commit that first added this audit.",
        })
        rec["_meta"]["date"] = want
        fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
        print(f"  {vol}: {have} -> {want}")
    print(f"\ncorrected {len(wrong)} record(s)")


if __name__ == "__main__":
    main()
