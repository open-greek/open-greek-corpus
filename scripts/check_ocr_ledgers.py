#!/usr/bin/env python3
"""Hold data/ocr_works.json and data/cgpg_works.json to the served text.

Neither file is generated. Both are ledgers that a dozen one-off rescope, rekey
and dissolve scripts edit in place, and their counts drift from the text they
describe: 803 of the 984 rows checkable against a derived total disagreed, 173 of
them by more than half, with Stobaeus' Anthologium claiming 181 tokens against an
actual 412,387. The README's Words column used to print those numbers.

They cannot simply be regenerated, because most of what they carry is provenance
that exists nowhere else: which scan a work came from, which pages were skipped
as collapsed duplicates, the human description of a carved unit, which CGPG
volume claimed it. That is the reason the files exist and it has to stay
hand-kept.

Two fields are not provenance at all. n_passages and n_tokens describe the served
text, which reconcile_corpus_editions.py derives from data/corpus into
corpus_editions.json, so the ledgers' copies are duplication and duplication is
what drifted. Those are checked and, with --write, replaced.

source, edition and license are NOT synced, and the reason is worth stating,
because syncing them is the obvious thing to do and it destroys provenance. 156
rows read license PD where the corpus reads CC-BY-SA-4.0, and 159 read source
`ocr` where the corpus reads dfhg or first1k. Those rows are not stale: they
record that we OCR'd the work from a public-domain edition, which stays true
after an openly-licensed digital text displaced it as the served version. The
ledger is describing the OCR run and corpus_editions.json is describing what is
served today, and they are allowed to differ. They are reported so the
divergence is visible, never rewritten.

  python3 scripts/check_ocr_ledgers.py            # report
  python3 scripts/check_ocr_ledgers.py --write    # sync the counts
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
EDITIONS = DATA / "corpus_editions.json"
LEDGERS = ("ocr_works.json", "cgpg_works.json")

# Describe the served text, so corpus_editions.json is authoritative and these
# can be replaced from it.
DERIVED = ("n_passages", "n_tokens")
# Describe the OCR run rather than the served text. Reported, never rewritten:
# a row reading source `ocr` / license PD against a corpus reading first1k /
# CC-BY-SA-4.0 is a work we OCR'd that an openly-licensed edition has since
# displaced, and both statements are true.
REPORTED = ("source", "edition", "license")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--tolerance", type=float, default=0.0,
                    help="ignore a token count within this fraction (default 0: "
                         "exact, because the derived number is the true one)")
    args = ap.parse_args()

    ce = json.loads(EDITIONS.read_text(encoding="utf-8"))
    bad = worst = 0
    for name in LEDGERS:
        fp = DATA / name
        rows = json.loads(fp.read_text(encoding="utf-8"))
        why: Counter[str] = Counter()
        diverged: Counter[str] = Counter()
        missing, examples = [], []
        for row in rows:
            urn = row.get("urn")
            served = ce.get(urn)
            if served is None:
                # A secondary witness or a carved-away unit has no served file
                # of its own; that is not drift, it is the ledger remembering
                # something the corpus no longer serves separately.
                missing.append(urn)
                continue
            for field in DERIVED + REPORTED:
                if field not in row or field not in served:
                    continue
                have, want = row[field], served[field]
                if have == want:
                    continue
                if field == "n_tokens" and want and args.tolerance:
                    if abs(have - want) / want <= args.tolerance:
                        continue
                why[field] += 1
                if field in REPORTED:
                    diverged[field] += 1
                    continue
                if field == "n_tokens" and want:
                    off = abs(have - want) / max(want, 1)
                    if off > 0.5:
                        worst += 1
                    if len(examples) < 8 and off > 0.5:
                        examples.append((urn, have, want))
                bad += 1
                if args.write:
                    row[field] = want
        print(f"{name}: {len(rows)} rows, {len(missing)} not served under their "
              f"own urn")
        for field, n in why.most_common():
            if field in REPORTED:
                continue
            print(f"    {field:12s} {n:>5} disagree, syncable")
        for field, n in diverged.most_common():
            print(f"    {field:12s} {n:>5} differ, left alone (OCR run vs served)")
        for urn, have, want in examples:
            print(f"      {urn}: ledger {have:,}, corpus {want:,}")
        if args.write:
            fp.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
            print(f"    wrote {fp.relative_to(REPO)}")

    print(f"\n{bad:,} count fields disagree with the corpus, "
          f"{worst:,} token counts off by more than half")
    if bad and not args.write:
        print("report only; re-run with --write to sync the derived fields.")
    raise SystemExit(1 if bad and not args.write else 0)


if __name__ == "__main__":
    main()
