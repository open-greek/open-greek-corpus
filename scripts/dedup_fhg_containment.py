#!/usr/bin/env python3
"""Row-level bigram-containment dedup check of an old FHG-scan work against its
DFHG carve, with Greek-numeral normalization.

Codifies the method recorded in data/dfhg_dedup_shed.json (2026-07-09 batch):
per-row word-bigram containment of the OCR row in the served carve text, after
NFD-strip-diacritics / lowercase / final-sigma normalization; a row is shed when
containment >= 0.7 with >= 4 words, or >= 0.6 with >= 20 words. Shed rows move to
data/corpus_secondary via displace_to_secondary.py --loci.

Adds --numfix: Greek-numeral normalization on BOTH sides before tokenizing -
  - keraia / prime marks stripped: U+0374 (greek numeral sign, inside the Greek
    block so the Greek-only filter otherwise KEEPS it), U+0375, U+02B9, ASCII
    apostrophe and U+2019 (these three are outside the Greek block and were
    already dropped by the base filter; listed for completeness);
  - stigma (U+03DA/U+03DB) -> the digraph "στ", so "ϛʹ" matches an OCR "στ'";
  - archaic koppa U+03D9 -> koppa U+03DF; archaic sampi U+0372/U+0373 -> U+03E1.

Measured on manetho.fragmenta vs manetho-sebennyta.fragmenta (2026-07-09): the
numeral normalization moves ZERO of the 0.45-0.7-band rows over the 0.7 gate.
The dynasty king-list rows fail on character-level OCR damage in the royal
names (e.g. "ἐδασίλευσεν Ἥραιστος" for "ἐβασίλευσεν Ἥφαιστος") and on genuine
recension-variant year numerals (OCR row "υδ'" vs carve "δʹ"), not on numeral
FORMATTING: the old Greek-only filter already stripped both sides' keraia
(U+02B9 in the DFHG text, ASCII "'" in the OCR rows), so "ψκζʹ" == "ψκζ'"
held before this flag existed. Those rows stay primary; nothing is displaced
on a failed gate.

  python3 scripts/dedup_fhg_containment.py --old manetho.fragmenta \
      --carve manetho-sebennyta.fragmenta --numfix            # dry-run report
  ... --apply    # displace passing rows via displace_to_secondary.py --loci
                 # and append the verdict batch to data/dfhg_dedup_shed.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
SHED = COG / "data" / "dfhg_dedup_shed.json"
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

KERAIA = dict.fromkeys(map(ord, "ʹ͵ʹ'’"))
NUMFORMS = str.maketrans({"Ϛ": "στ", "ϛ": "στ",     # stigma -> digraph
                          "ϙ": "ϟ",                  # archaic koppa -> koppa
                          "Ͳ": "ϡ", "ͳ": "ϡ"})  # archaic sampi


def norm(tok: str, numfix: bool) -> str:
    if numfix:
        tok = tok.translate(KERAIA).translate(NUMFORMS)
    d = unicodedata.normalize("NFD", tok.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = "".join(c for c in d if GK.match(c))
    return d.replace("ς", "σ")


def bigrams(text: str, numfix: bool):
    t = [w for w in (norm(x, numfix) for x in (text or "").split()) if w]
    return {(t[i], t[i + 1]) for i in range(len(t) - 1)}, len(t)


def passes(cont: float, words: int) -> bool:
    return (cont >= 0.7 and words >= 4) or (cont >= 0.6 and words >= 20)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="old page-keyed OCR slug (rows checked)")
    ap.add_argument("--carve", required=True, help="served carve slug (coverage text)")
    ap.add_argument("--numfix", action="store_true", help="Greek-numeral normalization")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    old = [json.loads(l) for l in (CORPUS / f"{args.old}.jsonl").open() if l.strip()]
    carve = [json.loads(l) for l in (CORPUS / f"{args.carve}.jsonl").open() if l.strip()]
    ctext = set()
    for r in carve:
        b, _ = bigrams(r.get("text", ""), args.numfix)
        ctext |= b

    shed_rows, band = [], []
    for r in old:
        b, w = bigrams(r.get("text", ""), args.numfix)
        cont = len(b & ctext) / len(b) if b else 0.0
        gk = len(GK.findall(r.get("text", "")))
        if passes(cont, w):
            shed_rows.append({"locus": r["locus"], "containment": round(cont, 3),
                              "words": w, "greek_chars": gk,
                              "edition": r.get("edition", "")})
        elif 0.45 <= cont < 0.7:
            band.append((r["locus"], round(cont, 3), w))

    print(f"{args.old}: {len(old)} rows vs {args.carve} "
          f"(numfix={'on' if args.numfix else 'off'})")
    print(f"  pass gate (>=0.7/4w or >=0.6/20w): {len(shed_rows)} rows, "
          f"{sum(r['greek_chars'] for r in shed_rows)} greek chars")
    print(f"  0.45-0.7 band (still primary):     {len(band)} rows")
    for loc, c, w in band[:15]:
        print(f"    band {loc} cont={c} words={w}")

    if not args.apply:
        print("DRY RUN - nothing displaced (use --apply)")
        return
    if not shed_rows:
        print("nothing passes the gate; no displacement, shed file untouched")
        return

    loci_file = COG / "data" / f"_shed_loci_{args.old.replace('.', '_')}.txt"
    loci_file.write_text("\n".join(r["locus"] for r in shed_rows) + "\n")
    reason = (f"row verified >= 0.7 bigram containment in {args.carve} "
              f"({'numeral-normalized, ' if args.numfix else ''}"
              f"method: data/dfhg_dedup_shed.json)")
    subprocess.run([sys.executable, str(COG / "scripts" / "displace_to_secondary.py"),
                    args.old, "--loci", f"@{loci_file}", "--reason", reason],
                   check=True)
    loci_file.unlink()

    shed = json.loads(SHED.read_text(encoding="utf-8"))
    key = f"{args.old}:numfix-{date.today().isoformat()}"
    shed["sheds"][key] = {
        "covered_by": args.carve,
        "note": ("re-verification with Greek-numeral normalization "
                 "(keraia strip + stigma/koppa/sampi mapping)"),
        "n_rows": len(shed_rows),
        "greek_chars": sum(r["greek_chars"] for r in shed_rows),
        "rows": shed_rows,
    }
    SHED.write_text(json.dumps(shed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"displaced {len(shed_rows)} rows; shed entry {key} appended")


if __name__ == "__main__":
    main()
