#!/usr/bin/env python3
"""Per-lemma corpus token frequency from a form-frequency lexicon.

Real token frequency (how often a word actually occurs), the thing lsj10's
word-profile feature wants instead of the LSJ-attestation proxy. Built type-wise
for speed: every distinct surface form is lemmatized once with Dilemma (a
12.5M-form O(1) lookup carries the bulk; only the rare tail hits the
transformer), then each form's already-counted token frequency is added to its
lemma. Counts are facts, freely usable downstream.

DEFAULT SOURCE is the PUBLIC corpus lexicon (public_corpus/public_lexicon.tsv,
from the open TEI corpora) per the public-path-only directive. The TLG-E lexicon
(data/tlg_lexicon.tsv) may be passed with --lexicon ONLY as a private coverage
benchmark, never for served data.

Outputs (next to the lexicon's stem):
  <out>.tsv          lemma<TAB>token_count, sorted desc
  <out>_stats.json

  python build_lemma_frequency.py                       # public corpus (default)
  python build_lemma_frequency.py --lexicon data/tlg_lexicon.tsv --out data/tlg_lemma_frequency.tsv
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", type=Path, default=DATA / "public_lexicon.tsv")
    ap.add_argument("--out", type=Path,
                    default=DATA / "public_lemma_frequency.tsv")
    ap.add_argument("--min-count", type=int, default=2,
                    help="skip forms rarer than this before lemmatizing. Hapax "
                         "forms (count 1) are dominated by OCR noise and each "
                         "misses the O(1) lookup -> the slow transformer; dropping "
                         "them barely moves any lemma's total. Use 1 for full "
                         "(slow) coverage.")
    args = ap.parse_args()
    LEXICON, OUT = args.lexicon, args.out
    from dilemma import Dilemma  # noqa: PLC0415
    d = Dilemma(lang="grc")

    forms, counts = [], []
    n_total = n_skipped = 0
    for line in LEXICON.read_text().splitlines():
        form, _, c = line.partition("\t")
        if form and c.isdigit():
            n_total += 1
            if int(c) < args.min_count:
                n_skipped += 1
                continue
            forms.append(form)
            counts.append(int(c))
    print(f"lemmatizing {len(forms):,} distinct forms "
          f"(skipped {n_skipped:,} rarer than {args.min_count} of {n_total:,}) ...",
          file=sys.stderr)

    lemma_freq: Counter[str] = Counter()
    form_tokens = 0
    CH = 50000
    for i in range(0, len(forms), CH):
        chunk = forms[i:i + CH]
        lemmas = d.lemmatize_batch(chunk)
        for lemma, cnt in zip(lemmas, counts[i:i + CH]):
            lem = (lemma or "").strip()
            if lem:
                lemma_freq[lem] += cnt
                form_tokens += cnt
        if (i // CH) % 5 == 0:
            print(f"  {i + len(chunk):,}/{len(forms):,} forms", file=sys.stderr)

    items = lemma_freq.most_common()
    with OUT.open("w") as f:
        for lemma, c in items:
            f.write(f"{lemma}\t{c}\n")

    total_tokens = sum(counts)
    stats = {
        "distinct_forms": len(forms),
        "min_count": args.min_count,
        "forms_skipped_below_min": n_skipped,
        "distinct_lemmas": len(items),
        "total_tokens": total_tokens,
        "tokens_lemmatized": form_tokens,
        "coverage_pct": round(100 * form_tokens / total_tokens, 1),
        "top30": [[w, c] for w, c in items[:30]],
    }
    OUT.with_name(OUT.stem + "_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1))
    print(f"\ndistinct lemmas: {len(items):,} | tokens lemmatized: "
          f"{form_tokens:,} ({stats['coverage_pct']}%)", file=sys.stderr)
    print("top 15 lemmas:", file=sys.stderr)
    for w, c in items[:15]:
        print(f"  {c:>10,}  {w}", file=sys.stderr)
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
