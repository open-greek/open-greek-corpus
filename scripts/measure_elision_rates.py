#!/usr/bin/env python3
"""How often each candidate elided stem actually stands before an apostrophe.

Greek elides a final vowel before a following vowel and marks it with an
apostrophe, but the corpus tokenizer matches Greek letters only, so the
apostrophe is not part of the form: `δ'` arrives as the bare `δ`, which then
lemmatizes to itself instead of to δέ. 281,109 tokens sit there.

Length cannot decide which bare stems are elided particles. `ἀλλ` obviously is,
`δ` equally obviously is, and `γ` is not - it is the numeral and the abbreviation
mark at least as often. Guessing from the letter count is what the elision rule
did, excluding everything under two letters after `γ̅`, `χ̅` and `θ̅` turned into
particles, and that guard costs δ its 281,109 tokens to save a few hundred.

The corpus answers it directly: look at what follows the token on the page. A
stem that is really elided is written with the apostrophe nearly every time, and
one that is really a numeral is not. Measured over the whole corpus, δ comes out
at 87.3% and γ at 30.9%, which is the whole distinction.

The rate settles whether a stem is elided. It does not settle what from, and the
second column here is why that matters: the skeleton has dropped the accent and
the breathing, which is exactly what separates εἶτ (εἶτα) from εἴτ (εἴτε), and
those two are split 2,375 to 2,168. So a stem also has to have one lexeme behind
it, which `spellings_when_elided` is the evidence for.

Writes data/elision_rates.json, which validate_lemma_map.py reads. Re-run it
after a re-OCR or an ingest; the rates move with the text.

  python3 scripts/measure_elision_rates.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import PARTICLES, deaccent  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
OUT = DATA / "elision_rates.json"

_GLET = r"[Ͱ-Ͽἀ-῿]"
# Every apostrophe these editions use for elision. The acute accent and the
# backtick are in here because the OCR of a printed apostrophe often lands as
# one of them, and the sample says so: they are the commonest of the lot.
APOSTROPHES = "'’᾿´`ʼ‘՚′"


def candidates() -> dict[str, str]:
    """Bare stem -> the one particle it can be the elided form of.

    A stem qualifies only if it is a proper prefix of exactly ONE particle, so
    nothing here is a choice between two answers. That is what keeps τ out: it
    prefixes τε alone and would qualify, and it is the measurement below rather
    than this filter that rejects it.
    """
    out: dict[str, str] = {}
    for p in PARTICLES:
        skel = deaccent(p)
        for n in range(1, len(skel)):
            out.setdefault(skel[:n], set()).add(p)  # type: ignore[arg-type]
    return {stem: next(iter(ps)) for stem, ps in out.items() if len(ps) == 1}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-occurrences", type=int, default=200,
                    help="ignore a stem the corpus barely has; a rate over a "
                         "handful of tokens is noise (default 200)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    cand = candidates()
    seen: dict[str, int] = {s: 0 for s in cand}
    before: dict[str, int] = {s: 0 for s in cand}
    # How the stem is actually spelled where it stands elided. The rate says a
    # stem IS elided; it cannot say what from, and the skeleton has thrown away
    # the accent and breathing that decide it. εἶτ (εἶτα) against εἴτ (εἴτε) is
    # very nearly an even split, ὅτ is elided ὅτε and not ὅτι, and ἄλλ (ἄλλος)
    # hides inside the same skeleton as ἀλλ. This column is the evidence for
    # which stems have to be left alone despite a decisive rate.
    spellings: dict[str, dict[str, int]] = {s: {} for s in cand}
    # One pass over the tokens, comparing SKELETONS, rather than a regex per
    # stem. The stems are deaccented and the page is not, so matching the stem
    # against the text as written finds `δ` (which carries no diacritic and so
    # is its own skeleton) and misses `ἀλλ` almost entirely - it counted 1,212
    # of its 19,304 occurrences, all the unaccented misspellings, and reported a
    # rate for a sample that was not the word.
    token = re.compile(_GLET + "+")

    files = sorted(CORPUS.glob("*.jsonl"))
    for n, fp in enumerate(files, 1):
        with fp.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                text = json.loads(line).get("text", "")
                for m in token.finditer(text):
                    stem = deaccent(m.group(0))
                    if stem not in seen:
                        continue
                    seen[stem] += 1
                    if m.end() < len(text) and text[m.end()] in APOSTROPHES:
                        before[stem] += 1
                        w = m.group(0)
                        spellings[stem][w] = spellings[stem].get(w, 0) + 1
        if n % 400 == 0:
            print(f"  {n}/{len(files)} works", file=sys.stderr)

    rates = {stem: {"particle": cand[stem], "occurrences": seen[stem],
                    "before_apostrophe": before[stem],
                    "rate": round(before[stem] / seen[stem], 4),
                    "spellings_when_elided": dict(sorted(
                        spellings[stem].items(), key=lambda kv: -kv[1])[:6])}
             for stem in sorted(cand) if seen[stem] >= args.min_occurrences}
    args.out.write_text(json.dumps(
        {"min_occurrences": args.min_occurrences,
         "apostrophes": APOSTROPHES,
         "note": "rate = share of bare-stem occurrences written before an "
                 "apostrophe; validate_lemma_map.py folds a stem into its "
                 "particle only above its own threshold",
         "stems": rates}, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")

    print(f"{'stem':8s} {'occurrences':>12s} {'before ’':>10s} {'rate':>7s}  particle")
    for stem, r in sorted(rates.items(), key=lambda kv: -kv[1]["rate"]):
        print(f"  {stem:8s} {r['occurrences']:>10,} {r['before_apostrophe']:>10,} "
              f"{r['rate']:>7.1%}  {r['particle']}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
