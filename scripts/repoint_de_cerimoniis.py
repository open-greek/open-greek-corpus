#!/usr/bin/env python3
"""Point the served De cerimoniis at the half of the work it actually serves.

The byzantium.gr transcription is served as
constantinus-vii-porphyrogenitus-imperator.de-cerimoniis-aulae-byzantinae-lib-1-84-2-56,
anchored to tlg3023.tlg010, whose Canon scope is lib. 1.84-2.56 (issue #8). The
text it serves is the OTHER half: it opens with the proem, verbatim identical to
PG112 locus 44, runs book 1 chapters 1-83, and contains nothing of 1.84-2.56.
That is tlg3023.011's scope (lib. 1.1-92, Vogt), which no slug claims. So the
slug's name, title and crosswalk all assert exactly the portion it does not
serve, and any consumer joining on tlg3023.010 gets book 1 instead.

How it happened is in the curated sweep itself. The researcher knew: the entry's
note reads 'byzantium hosts only "πρώτος τόμος" ... TLG splits the work into
.010 (gap) and .011 (locked); vol1 covers part of it', and the text was filed
under .010 anyway, because .010 was the gap being filled. The two halves' Canon
word counts nearly coincide (76,649 against 78,092), so nothing downstream
noticed. This script fixes the crosswalk; the sweep entry and the slug rename
are the same commit, so the whole identity moves together.

  python3 scripts/repoint_de_cerimoniis.py            # check only
  python3 scripts/repoint_de_cerimoniis.py --apply
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CW = DATA / "tlg_crosswalk.json"
CHANGES = DATA / "corpus_changes"

SLUG = ("constantinus-vii-porphyrogenitus-imperator."
        "de-cerimoniis-aulae-byzantinae-lib-1-84-2-56")
WAS = {"cts": "urn:cts:greekLit:tlg3023.tlg010", "tlg": "tlg3023.tlg010"}
NOW = {"cts": "urn:cts:greekLit:tlg3023.tlg011", "tlg": "tlg3023.tlg011",
       "title": "De cerimoniis aulae Byzantinae (lib. 1.1-92)"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cw = json.loads(CW.read_text(encoding="utf-8"))
    works = cw["works"] if isinstance(cw, dict) and "works" in cw else cw
    entry = works.get(SLUG)
    if entry is None:
        raise SystemExit(f"{SLUG} is not in the crosswalk (already renamed?)")
    if entry.get("tlg") == NOW["tlg"]:
        print("already repointed")
        raise SystemExit(0)
    for k, v in WAS.items():
        if entry.get(k) != v:
            raise SystemExit(f"refusing: {k} is {entry.get(k)!r}, expected {v!r}")
    clash = [s for s, e in works.items() if s != SLUG and e.get("tlg") == NOW["tlg"]]
    if clash:
        raise SystemExit(f"refusing: {NOW['tlg']} already claimed by {clash}")

    for k in ("cts", "tlg", "title"):
        print(f"  {k:<6} {entry.get(k)!r} -> {NOW[k]!r}")
    if not args.apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return

    entry.update(NOW)
    CW.write_text(json.dumps(cw, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")
    (CHANGES / "de-cerimoniis.anchor-repoint.json").write_text(json.dumps({
        "what": f"{SLUG} repointed from tlg3023.tlg010 to tlg3023.tlg011",
        "date": "2026-08-08",
        "issue": "open-greek/open-greek-corpus#8",
        "why": "the served text is the proem plus book 1 chapters 1-83, the "
               "tlg3023.011 (Vogt, lib. 1.1-92) scope, and holds nothing of "
               "lib. 1.84-2.56; its opening is verbatim identical to PG112 locus "
               "44 and ΚΕΦΑΛΑΙΟΝ ΠΡΩΤΟΝ falls where book 1 chapter 1 begins. "
               "The old anchor claimed exactly the half it does not serve.",
        "how_it_happened": "the curated sweep filed the page under .010 because "
               ".010 was the gap being filled, while its own note records that "
               "byzantium.gr hosts only the first volume; the halves' Canon "
               "word counts nearly coincide (76,649 vs 78,092), so mass checks "
               "could not catch it.",
        "was": WAS, "now": NOW,
        "reverse": "restore the `was` values on this slug's crosswalk entry and "
                   "revert the sweep entry and rename in the same commit.",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\naudit -> data/corpus_changes/de-cerimoniis.anchor-repoint.json")


if __name__ == "__main__":
    main()
