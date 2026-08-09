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
import hashlib
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
# Per-volume, under the audit directory, and created if absent. It used to be a
# single data/dfhg_dedup_shed.json that has never existed in this repo: --apply
# displaced the rows through a subprocess FIRST and only then read that file, so
# the one batch that most needed a record would have mutated the corpus and died
# with FileNotFoundError, leaving no reversal trail at all.
CHANGES = COG / "data" / "corpus_changes"
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
    ap.add_argument("--min-containment", type=float, default=None,
                    help="override the codified gate with a flat floor. The "
                         "0.6/20-word arm is right for matching fragment "
                         "collections; taking a row OUT of the served corpus is "
                         "a stronger claim, and PG113 kept Theophylact primary "
                         "at 0.697 on exactly that reasoning.")
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
        ok = (cont >= args.min_containment and w >= 20
              if args.min_containment is not None else passes(cont, w))
        if ok:
            shed_rows.append({"locus": r["locus"], "containment": round(cont, 3),
                              "words": w, "greek_chars": gk,
                              "edition": r.get("edition", "")})
        elif 0.45 <= cont < 0.7:
            band.append((r["locus"], round(cont, 3), w))

    print(f"{args.old}: {len(old)} rows vs {args.carve} "
          f"(numfix={'on' if args.numfix else 'off'})")
    gate_label = (f">={args.min_containment}/20w"
                  if args.min_containment is not None
                  else ">=0.7/4w or >=0.6/20w")
    print(f"  pass gate ({gate_label}): {len(shed_rows)} rows, "
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

    shed_fp = CHANGES / f"{args.old}.containment-shed.json"
    src = COG / "data" / "corpus" / f"{args.old}.jsonl"
    sha_before = hashlib.sha256(src.read_bytes()).hexdigest()

    loci_file = COG / "data" / f"_shed_loci_{args.old.replace('.', '_')}.txt"
    loci_file.write_text("\n".join(r["locus"] for r in shed_rows) + "\n")
    floor = args.min_containment if args.min_containment is not None else 0.7
    reason = (f"row verified >= {floor} word-bigram containment in {args.carve}, "
              f"which this corpus serves; kept verbatim as a witness rather than "
              f"served twice"
              f"{' (Greek numerals normalized)' if args.numfix else ''}. "
              f"Measurements per row in "
              f"data/corpus_changes/{args.old}.containment-shed.json")
    subprocess.run([sys.executable, str(COG / "scripts" / "displace_to_secondary.py"),
                    args.old, "--loci", f"@{loci_file}", "--reason", reason],
                   check=True)
    loci_file.unlink()

    shed = (json.loads(shed_fp.read_text(encoding="utf-8"))
            if shed_fp.exists() else
            {"what": f"rows of {args.old} displaced to data/corpus_secondary "
                     f"because a served work already carries them",
             "issue": "open-greek/open-greek-corpus#8",
             "reverse": "restore the rows from the witness file to "
                        f"data/corpus/{args.old}.jsonl and delete them there",
             "sheds": {}})
    key = f"{args.carve}:{date.today().isoformat()}"
    shed["sheds"][key] = {
        "covered_by": args.carve,
        "gate": (f"flat containment floor {args.min_containment}"
                 if args.min_containment is not None
                 else "codified: >=0.7/4w or >=0.6/20w"),
        "numeral_normalized": bool(args.numfix),
        "n_rows": len(shed_rows),
        "greek_chars": sum(r["greek_chars"] for r in shed_rows),
        "sha256_before": sha_before,
        "sha256_after": hashlib.sha256(src.read_bytes()).hexdigest(),
        "rows": shed_rows,
    }
    shed_fp.write_text(json.dumps(shed, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    print(f"displaced {len(shed_rows)} rows; recorded in "
          f"{shed_fp.relative_to(COG)} under {key}")


if __name__ == "__main__":
    main()
