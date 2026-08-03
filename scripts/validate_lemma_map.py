#!/usr/bin/env python3
"""Reject lemma-map entries that would overwrite a good lemma with a bad one.

data/lemma_map.tsv is produced by running dilemma over the forms the local cache
could not resolve, on a GPU box, and shipping the result back. Anything the
lemmatizer got wrong out there arrives here as a plain form/lemma pair with no
confidence attached, and build_work_lemma_counts.py used to merge it into the
cache unconditionally - so one bad row silently reassigns every occurrence of a
form. `οὐ -> οὖον` would move 658,075 occurrences of the commonest negative in
Greek onto a service-berry.

Three signatures, all measured against the corpus's own lemma frequencies:

  homograph capture   the form is itself an attested lemma (>= --min-lemma
                      occurrences) and the map proposes a different one. οὐ, εἰ,
                      αὖ, εὖ are the whole closed-class particle set here.
  capitalization      the proposed lemma is the form's own capitalized variant
                      and the lowercase lemma is commoner - εὔλογος -> Εὔλογος,
                      ἰατρικός -> Ἰατρικός, βασιλίς -> Βασιλίς. The same
                      capitalized/lowercase confusion the OCR correctors had.
  unattested target   the proposed lemma occurs nowhere in the corpus at all
                      (κβ -> κβʹ, οὕστ -> ουστ, ἀνωτάτω -> ἄνω2).

Reports by default; --write emits a filtered map. Nothing is deleted silently:
every rejected row is listed with the counts that condemned it.

  python3 scripts/validate_lemma_map.py
  python3 scripts/validate_lemma_map.py --write data/lemma_map.tsv
"""

from __future__ import annotations

import argparse
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# Closed-class function words are their own lemma, always. Frequency alone cannot
# defend them: ei -> eimi looks unremarkable because eimi is enormous, yet the
# conditional particle is not a form of "to be". Kept deliberately short - only
# words whose lemma is not in genuine doubt.
PARTICLES = {"οὐ", "εἰ", "αὖ", "εὖ", "μέν", "δέ", "γάρ", "τε", "ἄν", "μή",
             "ἤ", "ὡς", "εἴτε", "οὔτε", "μήτε", "ἀλλά", "καί", "ἵνα", "ὅτι"}


def deaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if not unicodedata.combining(c))


def is_elided(form: str, lemma: str) -> bool:
    """True if `form` is the elided stem of `lemma` - hin' for hina.

    These are the entries the map exists to supply, and they trip the
    homograph test hardest: an elided form acquires spurious lemma status of its
    own precisely BECAUSE nothing has mapped it yet, so `hin` shows 6,517
    occurrences "as a lemma" and the row that fixes that looks like the rows
    that break things.
    """
    a = "".join(c for c in unicodedata.normalize("NFD", form.lower())
                if not unicodedata.combining(c))
    b = "".join(c for c in unicodedata.normalize("NFD", lemma.lower())
                if not unicodedata.combining(c))
    if len(a) >= len(b):
        return False
    if b.startswith(a):
        return True
    deasp = {"θ": "τ", "φ": "π", "χ": "κ"}
    return bool(a) and a[-1] in deasp and b.startswith(a[:-1] + deasp[a[-1]])


def lower_initial(s: str) -> str:
    d = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", d[0].lower() + d[1:]) if d else s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", type=Path, default=DATA / "lemma_map.tsv")
    ap.add_argument("--freq", type=Path, default=DATA / "public_lemma_frequency.tsv")
    ap.add_argument("--min-lemma", type=int, default=1000,
                    help="how well attested a form must be AS A LEMMA before a "
                         "map row is allowed to reassign it (default 1000)")
    ap.add_argument("--write", type=Path, default=None,
                    help="write the filtered map here (may be the input path)")
    args = ap.parse_args()

    freq: dict[str, int] = {}
    for line in args.freq.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[1].isdigit():
            freq[p[0]] = int(p[1])
    print(f"{len(freq):,} lemma frequencies")

    kept, rejected, why = [], [], Counter()
    for line in args.map.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        form, _, lemma = line.partition("\t")
        lemma = lemma.strip()
        if not form or not lemma or form == lemma:
            kept.append(line)
            continue
        f_as_lemma, l_freq = freq.get(form, 0), freq.get(lemma, 0)
        reason = None
        if lemma != lower_initial(lemma) and lower_initial(lemma) == form \
                and freq.get(form, 0) > l_freq:
            reason = "capitalized variant of the form itself"
        elif form in PARTICLES and lemma not in PARTICLES:
            reason = "closed-class particle reassigned to another lemma"
        elif (f_as_lemma >= args.min_lemma and l_freq * 20 < f_as_lemma
              and not is_elided(form, lemma)
              and deaccent(form) != deaccent(lemma)):
            reason = "common form assigned a far rarer lemma"
        elif l_freq == 0 and f_as_lemma:
            reason = "proposed lemma occurs nowhere in the corpus"
        if reason:
            rejected.append((f_as_lemma, l_freq, form, lemma, reason))
            why[reason] += 1
        else:
            kept.append(line)

    print(f"kept {len(kept):,}, rejected {len(rejected):,}")
    for r, c in why.most_common():
        print(f"    {c:>4}  {r}")
    print()
    for f_as_lemma, l_freq, form, lemma, reason in sorted(rejected, reverse=True)[:30]:
        print(f"   {form:>14} ({f_as_lemma:>9,} as a lemma)  ->  "
              f"{lemma:<16} ({l_freq:,})   {reason}")

    if args.write:
        args.write.write_text("\n".join(kept) + "\n", encoding="utf-8")
        print(f"\nfiltered map -> {args.write}")
    else:
        print("\nreport only; pass --write PATH to emit the filtered map.")


if __name__ == "__main__":
    main()
