#!/usr/bin/env python3
"""What is still wrong with the published lemma table, by token mass.

Three defects have been found here by looking at the top of the frequency list
and noticing something absurd: οὐ on a service-berry (294,404 tokens), the whole
article paradigm on the relative pronoun (8,926,058), δ standing as its own
lemma (281,109). Finding them one at a time by eye is not a method, and it
cannot say whether the next one is the last one.

So this asks the opposite question. Rather than hunting for a defect, it sorts
every lemma in the table into classes that a headword cannot belong to, and
reports how much of the corpus each class holds. What it does NOT flag is the
real output: the share of the corpus sitting on lemmas with nothing detectably
wrong with them.

The classes are deliberately cheap and mechanical. Each is a property of the
lemma string or of its relation to the corpus, not a judgement about Greek, so
a flag here is a candidate and not a verdict - the same discipline the
correction work needed, where the first cut of any rule flags a superset and
the discriminating condition is the actual work.

  python3 scripts/audit_lemma_table.py
  python3 scripts/audit_lemma_table.py --examples 12
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import PARTICLES, VARIA, deaccent  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
COUNTS = DATA / "work_lemma_counts.tsv.gz"
FREQ = DATA / "public_lemma_frequency.tsv"
TOTALS = DATA / "work_token_totals.json"

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
NON_GREEK = re.compile(r"[^Ͱ-Ͽἀ-῿0-9'ʹ᾿’\-\s]")

# A one-letter lemma is usually a numeral or an abbreviation mark, but not
# always, and the exceptions are the commonest words in the language. ὁ alone
# holds 9,587,163 tokens, so leaving it in the suspect class buys a headline
# number that is 15% wrong about itself.
SINGLE_LETTER_HEADWORDS = PARTICLES | {"ὁ", "ὅ", "ἥ", "ἦ", "ὦ", "ἆ", "ἡ", "ᾧ", "ᾗ"}


def classify(lemma: str, freq: dict[str, int]) -> str | None:
    """The first class the lemma falls into, or None if nothing is wrong.

    Ordered most-specific first, and each returns rather than accumulating, so
    the token masses below sum to the table and a lemma is counted once. That
    matters more than completeness per lemma: the point is a budget, not a
    diagnosis.
    """
    nfd = unicodedata.normalize("NFD", lemma)
    if not lemma:
        return "empty"
    if not GREEK.search(lemma):
        return "no Greek letter at all"
    if NON_GREEK.search(lemma):
        return "carries a non-Greek character"
    if any(ch.isdigit() for ch in lemma):
        return "homograph digit (a real distinction, not a defect)"
    if VARIA in nfd:
        return "carries a grave, which no headword does"
    if lemma[:1].isupper() and freq.get(lemma[:1].lower() + lemma[1:], 0) > freq.get(lemma, 0):
        return "capitalized where the lowercase is commoner"
    if len(deaccent(lemma)) == 1 and lemma not in SINGLE_LETTER_HEADWORDS:
        return "a single letter"
    if deaccent(lemma) in {deaccent(p) for p in PARTICLES} and lemma not in PARTICLES:
        return "a particle under a spelling that is not its headword"
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--examples", type=int, default=6)
    args = ap.parse_args()

    freq: dict[str, int] = {}
    for line in FREQ.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[1].isdigit():
            freq[p[0]] = int(p[1])

    mass: Counter[str] = Counter()
    with gzip.open(COUNTS, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                mass[p[1]] += int(p[2])

    by_class: Counter[str] = Counter()
    lemmas: Counter[str] = Counter()
    examples: dict[str, list[tuple[str, int]]] = {}
    for lemma, n in mass.items():
        cls = classify(lemma, freq) or "nothing detectably wrong"
        by_class[cls] += n
        lemmas[cls] += 1
        examples.setdefault(cls, []).append((lemma, n))

    total = sum(mass.values())
    corpus = sum(v.get("tokens", 0) for v in json.loads(
        TOTALS.read_text(encoding="utf-8")).values())
    unlemmatized = corpus - total

    print(f"corpus tokens          {corpus:>12,}")
    print(f"on a lemma             {total:>12,}  {total / corpus:6.1%}")
    print(f"unlemmatized           {unlemmatized:>12,}  {unlemmatized / corpus:6.1%}"
          f"   (no lemma at all, so no class below)")
    print(f"distinct lemmas        {len(mass):>12,}\n")
    print(f"{'tokens':>12s} {'share':>7s} {'lemmas':>8s}  class")
    for cls, n in by_class.most_common():
        print(f"{n:>12,} {n / total:>7.1%} {lemmas[cls]:>8,}  {cls}")
        if cls == "nothing detectably wrong":
            continue
        for lemma, c in sorted(examples[cls], key=lambda kv: -kv[1])[:args.examples]:
            print(f"{'':>21s} {c:>10,}  {lemma}")


if __name__ == "__main__":
    main()
