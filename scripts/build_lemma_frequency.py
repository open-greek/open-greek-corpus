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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import validate_cache  # noqa: E402

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
    ap.add_argument("--no-cache", action="store_true",
                    help="ignore and do not update the persistent form->lemma "
                         "cache (force a full from-scratch lemmatization)")
    args = ap.parse_args()
    LEXICON, OUT = args.lexicon, args.out

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

    # Persistent form -> lemma cache. Lemmatization is type-wise and
    # deterministic per Dilemma version, so a form's lemma never changes once
    # computed. Caching it means a corpus regenerate only pays the (slow,
    # transformer-tail) lemmatization for forms it has never seen, turning the
    # ~40-min full pass into seconds on a mostly-unchanged corpus. Append-only,
    # so no form is ever recomputed. DELETE data/cache/lemma_cache.tsv after a
    # Dilemma upgrade to rebuild it against the new model.
    CACHE = DATA / "cache" / "lemma_cache.tsv"
    cache: dict[str, str] = {}
    if not args.no_cache and CACHE.exists():
        for line in CACHE.read_text().splitlines():
            f, sep, lem = line.partition("\t")
            if sep:
                cache[f] = lem
    # Same checks the other pipeline applies to its cache, for the same reason:
    # this one is append-only, so a bad entry can never be displaced by a good
    # one. It held 16 forms of the οὖον family (ὁὐ, ὀὐ, οὐα, ...); it happened
    # not to hold the plain οὐ, which is why this table looked clean while
    # data/cache/form_lemma.tsv.gz published a service-berry at #27.
    #
    # The reference here is this script's own previous output, so the frequency
    # tests bootstrap off the last generation. That is sound while the reference
    # is, and the repairs that carry the load - a closed-class word is its own
    # lemma - need no frequency at all.
    rejected: set[str] = set()
    if cache:
        repaired, rejected = validate_cache(cache, OUT, label="lemma_cache")
        if (repaired or rejected) and not args.no_cache:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text("".join(f"{f}\t{lem}\n" for f, lem in cache.items()),
                             encoding="utf-8")

    # Dropped forms stay out of this run's lemmatization: re-deriving one gets
    # the same wrong answer back and undoes the drop.
    misses = [f for f in forms if f not in cache and f not in rejected]
    print(f"lemmatizing {len(forms):,} distinct forms "
          f"(skipped {n_skipped:,} rarer than {args.min_count} of {n_total:,}); "
          f"cache: {len(forms) - len(misses):,} hit / {len(misses):,} to compute",
          file=sys.stderr)

    if misses:
        from dilemma import Dilemma  # noqa: PLC0415
        d = Dilemma(lang="grc")
        CH = 50000
        for i in range(0, len(misses), CH):
            chunk = misses[i:i + CH]
            lemmas = d.lemmatize_batch(chunk)
            for f, lemma in zip(chunk, lemmas):
                cache[f] = (lemma or "").strip()
            if (i // CH) % 5 == 0:
                print(f"  {i + len(chunk):,}/{len(misses):,} new forms",
                      file=sys.stderr)
        if not args.no_cache:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            with CACHE.open("a", encoding="utf-8") as cf:  # append the new forms
                for f in misses:
                    cf.write(f"{f}\t{cache[f]}\n")

    lemma_freq: Counter[str] = Counter()
    form_tokens = 0
    for f, cnt in zip(forms, counts):
        lem = cache.get(f, "")
        if lem:
            lemma_freq[lem] += cnt
            form_tokens += cnt

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
