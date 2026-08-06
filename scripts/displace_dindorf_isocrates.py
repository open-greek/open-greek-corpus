#!/usr/bin/env python3
"""Move Dindorf's Isocrates section out of the Aeschines scholia.

data/corpus/scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera.jsonl is our
OCR of Dindorf 1852, and 24 of its 138 printed pages are not Aeschines at all:
printed 117-140 are the Isocrates material Dindorf prints in the same volume, the
Life, the hypotheses of the speeches, and the scholia proper. They have been
served under the Aeschines urn since ingest (issue #12).

The disposition is decided (issue #16): the whole block becomes a SECONDARY
witness on scholia-in-isocratem, not a primary work and not a row-level dedup.
63% of its Greek is already served there from the First1K TEI, so serving it
primary would double-serve; but keeping only the Dindorf-only rows would need a
row-level dedup that has to be exactly right or it silently drops text, and it
would throw away a witness to the text we do serve. Secondary keeps everything
and competes with nothing.

What is NOT moved, because it belongs to neither work: printed 141-147 is an
alphabetical index over the whole volume, indexing Aeschines and Isocrates alike
(its first entries are ἀβελτάρια and Αἰσχίνης Ἑλευσίνιος ῥήτωρ), and printed 148
is a corrigenda list whose page references run past 800, so it corrects a
different Dindorf volume altogether. Both stay where they are, flagged rather
than moved.

  displace_dindorf_isocrates.py           # check only
  displace_dindorf_isocrates.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
SECONDARY = DATA / "corpus_secondary"
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

SOURCE = "scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera"
TARGET = "scholia-in-isocratem.scholia-in-isocratem-scholia-vetera"
FIRST, LAST = 117, 140
REASON = ("Dindorf 1852 prints the Isocrates scholia in the same volume as the "
          "Aeschines; this is that section, printed 117-140, which had been "
          "served under the Aeschines urn. Kept as a witness rather than served: "
          "scholia-in-isocratem is served from the First1KGreek open TEI edition "
          "(source precedence: open_corpus over our own OCR of a public-domain "
          "edition), and 63% of this text is already there")


def page(locus: str) -> int:
    return int(locus.rsplit("_", 1)[1].split(".")[0])


def tokens(text: str) -> int:
    return len(_GK.findall(text or ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = CORPUS / f"{SOURCE}.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    move = [r for r in rows if FIRST <= page(r["locus"]) <= LAST]
    keep = [r for r in rows if not (FIRST <= page(r["locus"]) <= LAST)]

    if len(move) + len(keep) != len(rows):
        raise SystemExit("partition error")
    if not move:
        raise SystemExit(f"nothing in printed {FIRST}-{LAST}; already displaced?")

    # The block has to start where Dindorf starts it. If the first row moved is
    # not the Life's own title, the page range is wrong and everything after it
    # is mis-attributed in the other direction.
    head = move[0]["text"].strip()
    if "ΙΣΟΚΡΑΤ" not in head:
        raise SystemExit(f"first moved row is not the Isocrates title: {head[:60]!r}")

    t_move = sum(tokens(r["text"]) for r in move)
    t_keep = sum(tokens(r["text"]) for r in keep)
    print(f"{SOURCE}: {len(rows):,} rows, {t_move + t_keep:,} tokens")
    print(f"  move to secondary  {len(move):>5,} rows {t_move:>7,} tokens  "
          f"printed {FIRST}-{LAST}")
    print(f"  stays as Aeschines {len(keep):>5,} rows {t_keep:>7,} tokens")
    print(f"  first moved row: {head[:60]}")
    idx = [r for r in keep if 141 <= page(r["locus"]) <= 148]
    print(f"  NOT moved, flagged: {len(idx)} rows on printed 141-148, the "
          f"volume index and a corrigenda list for another volume")

    if not args.apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return

    before = hashlib.sha256(src.read_bytes()).hexdigest()
    out = []
    for r in move:
        nr = dict(r)
        nr["urn"] = TARGET
        nr["rank"] = "secondary"
        nr["secondary_reason"] = REASON
        out.append(nr)
    SECONDARY.mkdir(parents=True, exist_ok=True)
    dest = SECONDARY / f"{TARGET}.jsonl"
    existing = (dest.read_text(encoding="utf-8") if dest.exists() else "")
    dest.write_text(existing + "".join(json.dumps(r, ensure_ascii=False) + "\n"
                                       for r in out), encoding="utf-8")
    src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep),
                   encoding="utf-8")

    audit = {
        "what": f"Dindorf Isocrates section moved out of {SOURCE} to a secondary "
                f"witness on {TARGET}",
        "date": "2026-08-05",
        "issue": "open-greek/open-greek-corpus#12, disposition decided in #16",
        "source_urn": SOURCE,
        "target_urn": TARGET,
        "printed_pages": f"{FIRST}-{LAST}",
        "source_sha256_before": before,
        "source_sha256_after": hashlib.sha256(src.read_bytes()).hexdigest(),
        "rows_moved": len(move),
        "tokens_moved": t_move,
        "loci_moved": [r["locus"] for r in move],
        "not_moved": "printed 141-147 is an index over the whole volume and 148 "
                     "is a corrigenda list for a different Dindorf volume; both "
                     "remain under the Aeschines urn, flagged not moved",
        "reverse": "set urn back to the source, drop rank/secondary_reason, and "
                   "merge on locus order",
    }
    fp = CHANGES / f"{SOURCE}.isocrates-displacement.json"
    fp.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")
    print(f"\nmoved {len(move)} rows; audit -> {fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
