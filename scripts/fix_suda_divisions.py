#!/usr/bin/env python3
"""Repair the Suda's alphabetical divisions, which are keyed inconsistently.

The Suda is cited by alphabetic division and entry (alpha 1, pi 253), and the
served loci are `book.division.entry`. Two things are wrong with the division
component:

  script mixing   8,202 rows carry a LATIN capital where the Greek letter is
                  meant - A, B, E, H, I, K, M, N, O, P, T, X, Y are the letters
                  whose two scripts are visually identical, and exactly those
                  were keyed as Latin while the rest (Π, Σ, Δ, Λ, Γ, Φ, Ψ, Ω)
                  came through as Greek. So `Suda A.1` and `Suda Α.1` are
                  different strings for one citation, and neither resolves
                  reliably. `Aι` mixes both inside a single digraph division.

  a fused number  the entire omicron section, 1,092 entries, sits under the
                  division `Ο255` rather than `Ο`, with the entry number in the
                  third component: `3.Ο255.1` for what should be `3.Ο.1`. No
                  plain `Ο` division exists, so nothing collides when it is
                  repaired.

Corrections keyed to the old loci are re-keyed with the rows, so the overlay
does not strand. An audit lands in data/corpus_changes/ in the usual form.

  python3 scripts/fix_suda_divisions.py            # dry run
  python3 scripts/fix_suda_divisions.py --write
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
URN = "suda.lexicon"

# Greek capitals whose Latin lookalike is a different codepoint. Only these can
# be silently mis-keyed, which is why only these are wrong in the file.
LATIN_TO_GREEK = {"A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η", "I": "Ι",
                  "K": "Κ", "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ", "T": "Τ",
                  "X": "Χ", "Y": "Υ"}
FUSED = re.compile(r"^([Α-Ω])\d+$")     # a division letter with a number fused on


def fix_division(div: str) -> str:
    div = "".join(LATIN_TO_GREEK.get(c, c) for c in div)
    m = FUSED.match(div)
    return m.group(1) if m else div


def fix_locus(locus: str) -> str:
    parts = str(locus).split(".")
    if len(parts) < 2:
        return str(locus)
    parts[1] = fix_division(parts[1])
    return ".".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--corrections-dir", type=Path,
                    default=Path(os.path.expanduser("~/Documents/greek-ocr/data/corrections")))
    args = ap.parse_args()
    stamp = time.strftime("%Y-%m-%d")

    fp = DATA / "corpus" / f"{URN}.jsonl"
    rows = [json.loads(x) for x in fp.read_text(encoding="utf-8").splitlines() if x.strip()]
    n, mapping, collide = Counter(), {}, []
    seen = {str(r["locus"]) for r in rows}
    out = []
    for r in rows:
        old = str(r["locus"])
        new = fix_locus(old)
        if new != old:
            n["locus repaired"] += 1
            if new in seen and new != old:
                collide.append((old, new))
            mapping[old] = new
            r["locus"] = new
        out.append(r)
    for k in ("script mixing", "fused number"):
        pass
    n["divisions before"] = len({str(r["locus"]).split(".")[1] for r in rows
                                 if len(str(r["locus"]).split(".")) > 1})
    print(f"{len(rows):,} rows; {n['locus repaired']:,} loci repaired")
    print(f"distinct divisions after repair: "
          f"{len({str(r['locus']).split('.')[1] for r in out if len(str(r['locus']).split('.')) > 1})}")
    if collide:
        print(f"  ! {len(collide)} repaired loci collide with an existing one; "
              f"refusing to write")
        for a, b in collide[:5]:
            print(f"      {a} -> {b}")
        return

    corr_hits = 0
    stores = {}
    for name in ("freq", "confusion", "llm", "agent", "prosodia"):
        cf = args.corrections_dir / f"{name}.jsonl"
        if not cf.exists():
            continue
        recs = []
        for line in cf.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                recs.append(line)
                continue
            if isinstance(rec, dict) and rec.get("urn") == URN:
                old = str(rec["locus"])
                if old in mapping:
                    rec["locus"] = mapping[old]
                    corr_hits += 1
            recs.append(rec)
        stores[cf] = recs
    print(f"corrections re-keyed with the rows: {corr_hits}")

    if not args.write:
        print("\ndry run; nothing written. Re-run with --write.")
        for old, new in list(mapping.items())[:8]:
            print(f"   {old}  ->  {new}")
        return

    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out),
                  encoding="utf-8")
    for cf, recs in stores.items():
        cf.write_text("".join(
            (json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r) + "\n"
            for r in recs), encoding="utf-8")
    audit = DATA / "corpus_changes" / f"{URN}.division-rekey.json"
    audit.write_text(json.dumps({
        "_meta": {"change": "repair the alphabetical division component of the "
                            "served loci: Latin capitals keyed for their Greek "
                            "lookalikes, and the omicron section fused with a "
                            "number (O255 for O)",
                  "work": URN, "applied_by": "scripts/fix_suda_divisions.py",
                  "date": stamp,
                  "reversible": "the mapping below is one-to-one; invert it"},
        "n_rows": len(rows), "n_loci_repaired": n["locus repaired"],
        "n_corrections_rekeyed": corr_hits,
        "locus_map": mapping,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"audit -> {audit.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
