#!/usr/bin/env python3
"""Point the served Nicolaus Progymnasmata at the right author and work id.

`nicolaus-history.nicolaus-progymnasmata-felten` publishes
`urn:cts:greekLit:tlg0577.tlg001` under author `nicolaus-history`, wikidata
Q313924 (issue #30). Two things are wrong with that and neither is a judgment
call.

tlg0577 is Nicolaus of Damascus, the Augustan historian, birth -63 death 4 in
this repo's own data/author_authority.json, and his FHG fragments sit on the
sibling slug `nicolaus-history.fragmenta` as tlg0577.tlg003. The Progymnasmata is
a rhetorical handbook by Nicolaus Sophista, tlg2904 in the vendored Canon, birth
430 death 500, Q11938736. So 17,289 served tokens are filed under a man who died
four centuries before their author was born, and anyone filtering by period gets
them in the wrong place.

And tlg0577.001 does not exist. The vendored Canon carries exactly one work for
tlg0577, `.003` Fragmenta. The anchor points at nothing, so any join through it
silently drops the work rather than mismatching loudly.

The target is not invented either: the Canon has tlg2904.001 Progymnasmata at
13,337 words against our 17,289 served tokens, and this repo already carries an
author slug for him, `nicolaus-rhetoric`, carrying exactly tlg2904's wikidata id
and currently serving nothing.

That the served text really is the Progymnasmata was the question #26 asked and
left open. It is settled by a second witness rather than by this script: the
Spengel III witness on the same slug agrees with the served text at 45.7% of
4-grams and 77.6% of vocabulary. Two independent editions of one work.

The slug still says `nicolaus-history` after this runs. Renaming it is
scripts/rename_work.py's job, which keeps the ogc id and leaves the old slug
resolving; this script only fixes what the work is anchored to.

  python3 scripts/repoint_nicolaus_progymnasmata.py            # check only
  python3 scripts/repoint_nicolaus_progymnasmata.py --apply
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CW = DATA / "tlg_crosswalk.json"
CHANGES = DATA / "corpus_changes"

SLUG = "nicolaus-history.nicolaus-progymnasmata-felten"
WAS = {"cts": "urn:cts:greekLit:tlg0577.tlg001", "tlg": "tlg0577.tlg001",
       "author_slug": "nicolaus-history", "title": "nicolaus_progymnasmata_felten"}
NOW = {"cts": "urn:cts:greekLit:tlg2904.tlg001", "tlg": "tlg2904.tlg001",
       "author_slug": "nicolaus-rhetoric", "title": "Progymnasmata"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cw = json.loads(CW.read_text(encoding="utf-8"))
    works = cw["works"] if isinstance(cw, dict) and "works" in cw else cw
    entry = works.get(SLUG)
    if entry is None:
        raise SystemExit(f"{SLUG} is not in the crosswalk")
    if entry.get("tlg") == NOW["tlg"]:
        print("already repointed")
        raise SystemExit(0)
    for k, v in WAS.items():
        if entry.get(k) != v:
            raise SystemExit(f"refusing: {k} is {entry.get(k)!r}, expected {v!r}; "
                             f"this is not the entry that was measured")
    # The target must be free, or repointing would put two works on one anchor.
    clash = [s for s, e in works.items()
             if s != SLUG and e.get("tlg") == NOW["tlg"]]
    if clash:
        raise SystemExit(f"refusing: {NOW['tlg']} is already claimed by {clash}")

    for k in WAS:
        print(f"  {k:<12} {entry.get(k)!r}\n  {'':<12} -> {NOW[k]!r}")
    if not args.apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return

    entry.update(NOW)
    CW.write_text(json.dumps(cw, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")
    (CHANGES / "nicolaus-progymnasmata.anchor-repoint.json").write_text(json.dumps({
        "what": f"{SLUG} repointed from tlg0577.tlg001 to tlg2904.tlg001",
        "date": "2026-08-07",
        "issue": "open-greek/open-greek-corpus#30",
        "why": "tlg0577 is Nicolaus of Damascus (d. 4 CE), whose fragments are on "
               "the sibling slug as tlg0577.tlg003; the Progymnasmata is by "
               "Nicolaus Sophista, tlg2904 (b. 430). tlg0577.001 also does not "
               "exist in the vendored Canon, so the old anchor pointed at nothing.",
        "target_evidence": "Canon tlg2904.001 Progymnasmata, 13,337 words against "
                           "17,289 served tokens; author slug nicolaus-rhetoric "
                           "already carries tlg2904's wikidata Q11938736.",
        "identity_evidence": "that the served text is the Progymnasmata (the open "
                             "question in #26) rests on the Spengel III witness on "
                             "the same slug agreeing with it at 45.7% of 4-grams "
                             "and 77.6% of vocabulary",
        "was": WAS, "now": NOW,
        "reverse": "restore the `was` values on this slug's entry in "
                   "data/tlg_crosswalk.json and rebuild.",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\naudit -> data/corpus_changes/nicolaus-progymnasmata.anchor-repoint.json")


if __name__ == "__main__":
    main()
