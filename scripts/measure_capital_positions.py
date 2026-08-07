#!/usr/bin/env python3
"""Decide, from the corpus itself, which capitalized lemmas are only positional.

3,973 lemmas in the per-work table are a capitalized spelling of a word whose
lowercase form is commoner, so the two split the word's occurrences between them
(issue #19). Capitalization is not lexical in a Greek headword, which makes them
look like the same word entered twice, and lowercasing the lot is the obvious
fix. It is also wrong. Λέων the emperor is not λέων the lion, and Θεός is a
capital the editions print on purpose.

The way to tell them apart is the one this repo already uses for the grave
accent: ask whether the feature is POSITIONAL. A grave appears only before a
pause, so it cannot distinguish two words. A capital appears wherever any word
would be capitalized, at the head of a sentence or a verse line, and there it
says nothing about the word either. What it says something about is a capital in
the MIDDLE of a sentence, where nothing but the word itself put it there.

So this measures, for every capitalized form, the share of its occurrences that
are mid-sentence, and the split is clean:

    Θεός       97.8% mid    a deliberate capital, keep
    Ἀβραάμ     96.9% mid    a name, keep
    Λόγος      90.1% mid    the Logos, keep
    Λέων       82.5% mid    the name, keep, and this is the one lowercasing ruins
    Πᾶς        25.3% mid
    Ἀνάγκη     18.7% mid
    Πῶς         9.1% mid    just a sentence opener, fold

Only the low end folds, at MID_MAX with at least MIN_OCCURRENCES to measure. The
threshold is deliberately far from the middle of the distribution, because the
two errors are not symmetrical: leaving a split costs a divided count, and
folding a proper noun into a common one destroys the distinction for good.

That conservatism is also the finding. Of the 207,583 tokens the audit flags,
154,648 sit above 60% mid-sentence, so they are lexical capitals and not a
defect at all; the genuinely positional residue is about a tenth of the total.

  python3 scripts/measure_capital_positions.py            # report
  python3 scripts/measure_capital_positions.py --write    # -> data/capital_positions.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
OUT = DATA / "capital_positions.json"
FREQ = DATA / "public_lemma_frequency.tsv"
WORK_LEMMAS = DATA / "work_lemma_counts.tsv.gz"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from validate_lemma_map import VARIA, lower_initial, to_acute  # noqa: E402

MID_MAX = 0.25
MIN_OCCURRENCES = 10

# What can stand before a capital without the capital meaning anything: the end
# of the previous sentence, or a bracket or quote that opens one.
CLOSERS = set(".;·:!?»)]’\"'")
# An all-caps run capitalizes every word by typography, so it is evidence about
# neither the word nor its position. Headings and inscriptions are full of them.
ALLCAPS_SHARE, ALLCAPS_MIN = 0.8, 3


def load_work_lemma_totals() -> dict[str, int]:
    """lemma -> tokens, rolled up from the per-work table.

    This is the table CAPITAL_FOLDS is actually applied to, and it is not the
    same set as public_lemma_frequency.tsv: that one is built by a different
    script from a different cache with its own min-count, and carries 1,224
    grave lemmas where this carries 9,306. A capitalized lemma absent from the
    frequency table was therefore invisible here no matter how large it was.
    `Διὸ` is 6,270 tokens, 12.3% of the whole grave residue, and it is not in
    the frequency table at all (issue #4).
    """
    out: dict[str, int] = {}
    with gzip.open(WORK_LEMMAS, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[2].isdigit():
                out[parts[1]] = out.get(parts[1], 0) + int(parts[2])
    return out


def load_frequencies() -> dict[str, int]:
    freq: dict[str, int] = {}
    for line in FREQ.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].isdigit():
            freq[parts[0]] = int(parts[1])
    return freq


def target_twin(form: str, freq: dict[str, int]) -> str | None:
    """The lowercase headword this capitalized lemma would fold into, or None.

    Normally that is the lowercase spelling, and only when it is COMMONER: the
    other direction is a word that really is usually capitalized, and folding it
    down would be the same destruction in reverse.

    A lemma carrying a GRAVE is the exception, and gets the weaker test of
    merely being attested. No headword carries a grave, so such an entry is the
    lemmatizer echoing a surface form back rather than a citation form, and its
    count is large for exactly that reason: it swallowed the tokens its own
    headword is missing. Χωρὶς stands at 13,884 against χωρίς at 876, so
    demanding the twin be commoner asks the split to have healed itself before
    it may be healed. That is the argument validate_lemma_map.grave_lemma_repair
    already makes for not requiring the acute to be commoner either.
    """
    lower = lower_initial(form)
    # The commoner-than test still requires the form to be IN the frequency
    # table. Defaulting a missing count to 0 would make every absent capital
    # look rarer than its lowercase twin and fold it, which is exactly the
    # proper-noun destruction #19 exists to prevent. Out-of-table forms reach
    # only the grave branch below, where the argument does not need a count.
    if lower != form and form in freq and freq.get(lower, 0) > freq[form]:
        return lower
    if VARIA in unicodedata.normalize("NFD", form):
        acute = to_acute(lower)
        if acute != form and freq.get(acute, 0):
            return acute
    return None


def count_positions() -> tuple[Counter[str], Counter[str]]:
    """(sentence-initial, mid-sentence) counts per capitalized surface form."""
    initial: Counter[str] = Counter()
    mid: Counter[str] = Counter()
    for fp in sorted(CORPUS.glob("*.jsonl")):
        with fp.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                text = json.loads(line).get("text") or ""
                spans = list(_GK.finditer(text))
                if len(spans) >= ALLCAPS_MIN and sum(
                        1 for m in spans if m.group().isupper()
                ) / len(spans) > ALLCAPS_SHARE:
                    continue
                for i, m in enumerate(spans):
                    form = unicodedata.normalize("NFC", m.group())
                    if form == lower_initial(form):
                        continue
                    before = text[:m.start()].rstrip()
                    at_start = i == 0 or (before and before[-1] in CLOSERS)
                    (initial if at_start else mid)[form] += 1
    return initial, mid


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    freq = load_frequencies()
    # Membership and token counts come from the per-work table, which is what
    # the folds are applied to. The old gate was `form not in freq`, and it hid
    # every capitalized lemma the frequency table happens not to carry.
    totals = load_work_lemma_totals()
    initial, mid = count_positions()

    folds, kept, thin = {}, 0, 0
    for form in set(initial) | set(mid):
        if form not in totals:
            continue
        lower = target_twin(form, freq)
        if not lower:
            continue
        n = initial[form] + mid[form]
        rate = mid[form] / n if n else 1.0
        if n < MIN_OCCURRENCES:
            thin += 1
            continue
        if rate >= MID_MAX:
            kept += 1
            continue
        folds[form] = {"folds_to": lower, "mid_sentence_rate": round(rate, 4),
                       "occurrences": n, "tokens": totals[form]}

    tokens = sum(v["tokens"] for v in folds.values())
    print(f"{len(folds):,} capitalized lemmas are positional only "
          f"({tokens:,} tokens), folding to their lowercase twin")
    print(f"{kept:,} kept: the capital is mid-sentence at least "
          f"{MID_MAX:.0%} of the time, so it is lexical")
    print(f"{thin:,} left alone: fewer than {MIN_OCCURRENCES} occurrences to "
          f"measure")
    for form, v in sorted(folds.items(), key=lambda kv: -kv[1]["tokens"])[:12]:
        print(f"    {form:14} -> {v['folds_to']:14} {v['tokens']:>6,} tokens, "
              f"mid {v['mid_sentence_rate']:.1%} of {v['occurrences']:,}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    # Merged, never overwritten, for the same reason the tombstones are kept:
    # this reads the frequency table that the previous folds have already been
    # applied to, so a fold once made is invisible to the next run. Πῶς is gone
    # from the table and χωρίς has grown, and re-deriving from that would drop
    # every earlier decision on the floor and let the next build make it again.
    kept_before = json.loads(OUT.read_text(encoding="utf-8"))["folds"] \
        if OUT.exists() else {}
    new = {k: v for k, v in folds.items() if k not in kept_before}
    kept_before.update(folds)
    OUT.write_text(json.dumps(
        {"mid_sentence_max": MID_MAX, "min_occurrences": MIN_OCCURRENCES,
         "folds": dict(sorted(kept_before.items()))},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(new)} new, {len(kept_before)} folds recorded in total")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
