#!/usr/bin/env python3
"""Per-work x lemma token counts over the ingested corpus (data/corpus/*.jsonl),
INCREMENTAL: reruns only touch what changed since the last run.

The per-lemma rollup build_lemma_frequency.py does corpus-wide, broken out by
work, so downstream consumers can join works to their metadata (composition
date, genre, author birthplace) and build per-lemma usage profiles. All
inflected forms roll up to the lemma: every distinct surface form is
lemmatized once with Dilemma; each work's form counts are mapped through that
table.

Two caches under data/cache/ make reruns cheap:

  work_forms/<file>.tsv.gz + work_forms_manifest.json
      per-work form counts, keyed by the corpus file's (size, mtime). Only
      new or changed corpus files are re-tokenized; everything else loads
      from the cache.
  form_lemma.tsv.gz + form_lemma_meta.json
      the persistent form -> lemma table. Only forms never seen before are
      lemmatized (the expensive Dilemma-transformer step); known forms are
      free. The meta file records the Dilemma version the cache was built
      with; a version change prints a loud warning (delete the cache file to
      relemmatize everything).

The lemmatization phase can also run on a remote GPU box:

  python build_work_lemma_counts.py --emit-missing missing.tsv
      tokenize (incrementally), then write the forms that still need
      lemmatizing (one per line) and STOP.
  # remotely: scripts/lemmatize_forms.py missing.tsv lemma_map.tsv
  python build_work_lemma_counts.py --lemma-map lemma_map.tsv
      merge the returned map into the cache, then finish the build (any
      forms still missing are lemmatized locally; normally none).

Outputs (under data/):
  work_lemma_counts.tsv.gz    work_urn<TAB>lemma<TAB>count
  work_token_totals.json      work_urn -> {tokens, tokens_lemmatized}
  work_lemma_counts_stats.json
  public_lemma_frequency.tsv (+ _stats.json)   same schema as before

  python build_work_lemma_counts.py                 # full/incremental build
  python build_work_lemma_counts.py --limit 20      # sanity slice, no writes
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
CACHE = DATA / "cache"
WORK_FORMS = CACHE / "work_forms"
MANIFEST = CACHE / "work_forms_manifest.json"
LEMMA_CACHE = CACHE / "form_lemma.tsv.gz"
LEMMA_META = CACHE / "form_lemma_meta.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402


def file_key(fp: Path) -> dict:
    st = fp.stat()
    return {"size": st.st_size, "mtime": int(st.st_mtime)}


def tokenize_file(fp: Path) -> dict[str, Counter[str]]:
    """Per-URN form counters for one corpus file (a file may carry several
    URNs in principle; in practice one)."""
    counters: dict[str, Counter[str]] = {}
    with fp.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            # sys.intern: the same form recurs across thousands of works, and
            # every per-work counter stays in memory at once.
            toks = [sys.intern(unicodedata.normalize("NFC", t))
                    for t in _GK.findall(rec.get("text", ""))]
            counters.setdefault(rec.get("urn") or fp.stem, Counter()).update(toks)
    return counters


def load_work_forms(files: list[Path], use_cache: bool) -> dict[str, Counter[str]]:
    """Per-URN form counters for every corpus file, re-tokenizing only files
    absent from or stale in the work_forms cache."""
    manifest = json.loads(MANIFEST.read_text()) if (use_cache and MANIFEST.exists()) else {}
    if use_cache:
        WORK_FORMS.mkdir(parents=True, exist_ok=True)

    out: dict[str, Counter[str]] = {}
    fresh = 0
    for i, fp in enumerate(files):
        key = file_key(fp)
        cache_fp = WORK_FORMS / (fp.stem + ".tsv.gz")
        if use_cache and manifest.get(fp.name) == key and cache_fp.exists():
            with gzip.open(cache_fp, "rt", encoding="utf-8") as f:
                for line in f:
                    urn, form, n = line.rstrip("\n").split("\t")
                    out.setdefault(urn, Counter())[sys.intern(form)] = int(n)
        else:
            counters = tokenize_file(fp)
            fresh += 1
            if use_cache:
                with gzip.open(cache_fp, "wt", encoding="utf-8") as f:
                    for urn, c in counters.items():
                        for form, n in c.most_common():
                            f.write(f"{urn}\t{form}\t{n}\n")
                manifest[fp.name] = key
            for urn, c in counters.items():
                out.setdefault(urn, Counter()).update(c)
        if i % 300 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)
    if use_cache:
        MANIFEST.write_text(json.dumps(manifest, indent=0, sort_keys=True))
    print(f"  tokenized {fresh} new/changed files, "
          f"{len(files) - fresh} from cache", file=sys.stderr)
    return out


def dilemma_version() -> str:
    try:
        version = (Path(__import__("dilemma").__file__).parent.parent / "VERSION")
        return version.read_text().strip() if version.exists() else "unknown"
    except Exception:
        return "unknown"


def validate_cache(cache: dict[str, str]) -> None:
    """Apply the lemma-map checks to the persistent cache, in place.

    Filtering the incoming map is not enough. The merge below fills gaps and
    never overrides, by design - so an entry that got into the cache before the
    checks existed can never be displaced by a good one, and the checks give the
    reassuring answer while the damage sits upstream of them. This cache had
    `οὐ -> οὖον` in it, which put 294,404 occurrences of the commonest negative
    in Greek onto a service-berry and published it at #27 in the top-30.

    The corpus's own per-lemma frequencies are the reference, so this is a no-op
    until data/public_lemma_frequency.tsv exists.
    """
    freq_path = DATA / "public_lemma_frequency.tsv"
    if not freq_path.exists():
        print("no public_lemma_frequency.tsv; skipping cache validation",
              file=sys.stderr)
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_lemma_map import (load_lemma_frequencies,  # noqa: PLC0415
                                    particle_capture, rejection_reason)

    freq = load_lemma_frequencies(freq_path)
    repaired, dropped = [], []
    for form, lemma in list(cache.items()):
        particle = particle_capture(form, lemma, freq)
        if particle:
            repaired.append((form, lemma, particle))
            cache[form] = particle
            continue
        reason = rejection_reason(form, lemma, freq)
        if reason:
            dropped.append((form, lemma, reason))
            del cache[form]
    for form, lemma, particle in sorted(repaired):
        print(f"  cache repair: {form} -> {lemma} is now {particle}",
              file=sys.stderr)
    for form, lemma, reason in sorted(dropped)[:40]:
        print(f"  cache drop: {form} -> {lemma} ({reason})", file=sys.stderr)
    if repaired or dropped:
        print(f"cache validated: {len(repaired):,} repaired, "
              f"{len(dropped):,} dropped", file=sys.stderr)


def load_lemma_cache() -> dict[str, str]:
    if not LEMMA_CACHE.exists():
        return {}
    if LEMMA_META.exists():
        meta = json.loads(LEMMA_META.read_text())
        current = dilemma_version()
        if meta.get("dilemma_version") not in ("unknown", current):
            print(f"WARNING: form_lemma cache built with Dilemma "
                  f"{meta.get('dilemma_version')}, current is {current}. "
                  f"Delete {LEMMA_CACHE} to relemmatize.", file=sys.stderr)
    cache: dict[str, str] = {}
    with gzip.open(LEMMA_CACHE, "rt", encoding="utf-8") as f:
        for line in f:
            form, _, lemma = line.rstrip("\n").partition("\t")
            if form and lemma:
                cache[form] = lemma
    return cache


def save_lemma_cache(cache: dict[str, str]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    with gzip.open(LEMMA_CACHE, "wt", encoding="utf-8") as f:
        for form, lemma in cache.items():
            f.write(f"{form}\t{lemma}\n")
    LEMMA_META.write_text(json.dumps(
        {"dilemma_version": dilemma_version(), "entries": len(cache)}, indent=1))


def lemmatize_local(forms: list[str], cache: dict[str, str]) -> None:
    """Lemmatize `forms` with local Dilemma, filling `cache` in place.
    Forms Dilemma can't resolve (empty lemma) are left out of the cache, so
    they retry on the next run (e.g. after a Dilemma upgrade)."""
    from dilemma import Dilemma  # noqa: PLC0415
    d = Dilemma(lang="grc")
    CH = 50000
    for i in range(0, len(forms), CH):
        chunk = forms[i:i + CH]
        for form, lemma in zip(chunk, d.lemmatize_batch(chunk)):
            lem = (lemma or "").strip()
            if lem:
                cache[form] = lem
        print(f"  {min(i + CH, len(forms)):,}/{len(forms):,} forms",
              file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=2,
                    help="lemmatize only forms with corpus-wide count >= this "
                         "(hapax forms are dominated by OCR noise; same "
                         "default as build_lemma_frequency.py)")
    ap.add_argument("--limit", type=int, default=0,
                    help="process only the first N works, bypass all caches, "
                         "print stats WITHOUT writing outputs (sanity slice)")
    ap.add_argument("--emit-missing", type=Path, metavar="FILE",
                    help="after tokenizing, write the forms that need "
                         "lemmatizing (one per line) to FILE and stop -- for "
                         "remote GPU lemmatization via lemmatize_forms.py")
    ap.add_argument("--lemma-map", type=Path, metavar="FILE",
                    help="merge a form<TAB>lemma map (from lemmatize_forms.py) "
                         "into the cache before deciding what is missing")
    ap.add_argument("--write-lemma-frequency", action="store_true",
                    help="also overwrite data/public_lemma_frequency.tsv and its "
                         "stats. Off by default: build_lemma_frequency.py owns "
                         "that file, uses a different cache and a different "
                         "--min-count, and validate_cache reads it as a reference")
    args = ap.parse_args()

    files = sorted(CORPUS.glob("*.jsonl"))
    if not files:
        sys.exit(f"no ingested corpus in {CORPUS} - run the ingesters first")
    if args.limit:
        files = files[:args.limit]
    use_cache = not args.limit

    print(f"tokenizing {len(files)} works ...", file=sys.stderr)
    works = load_work_forms(files, use_cache)

    corpus_forms: Counter[str] = Counter()
    for c in works.values():
        corpus_forms.update(c)
    keep = [f for f, n in corpus_forms.items() if n >= args.min_count]
    skipped = len(corpus_forms) - len(keep)

    lemma_cache = load_lemma_cache() if use_cache else {}
    if args.lemma_map:
        n_new = n_kept = 0
        for line in args.lemma_map.read_text(encoding="utf-8").splitlines():
            form, _, lemma = line.partition("\t")
            if form and lemma.strip():
                if form in lemma_cache:
                    # Fill gaps, never override. The map is whatever dilemma
                    # returned on a remote box, with no confidence attached, so
                    # one bad row used to silently reassign every occurrence of a
                    # form - `ou -> ooun` would have moved 658,075 occurrences of
                    # the commonest negative in Greek onto a service-berry.
                    n_kept += 1
                    continue
                n_new += 1
                lemma_cache[form] = lemma.strip()
        print(f"merged {args.lemma_map}: +{n_new} new cache entries, "
              f"{n_kept} existing entries left as they were",
              file=sys.stderr)

    # After the merge, so both sources are covered by one pass: the cache may
    # carry entries older than these checks, and the map may carry new ones.
    if lemma_cache:
        validate_cache(lemma_cache)

    missing = [f for f in keep if f not in lemma_cache]
    print(f"{len(keep):,} forms above min-count "
          f"(skipped {skipped:,} rarer than {args.min_count} of "
          f"{len(corpus_forms):,}); {len(missing):,} not in lemma cache",
          file=sys.stderr)

    if args.emit_missing:
        args.emit_missing.write_text("\n".join(missing) + ("\n" if missing else ""),
                                     encoding="utf-8")
        print(f"wrote {len(missing):,} forms to {args.emit_missing}; "
              f"lemmatize remotely, then rerun with --lemma-map",
              file=sys.stderr)
        return

    if missing:
        print(f"lemmatizing {len(missing):,} forms locally ...", file=sys.stderr)
        lemmatize_local(missing, lemma_cache)
    if use_cache:
        save_lemma_cache(lemma_cache)

    print("rolling up per-work lemma counts ...", file=sys.stderr)
    lemma_freq: Counter[str] = Counter()
    totals: dict[str, dict[str, int]] = {}
    n_pairs = 0
    keep_set = set(keep)
    sink = (gzip.open(DATA / "work_lemma_counts.tsv.gz", "wt", encoding="utf-8")
            if use_cache else None)
    try:
        for urn in sorted(works):
            forms = works[urn]
            lemmas: Counter[str] = Counter()
            tokens = lemmatized = 0
            for form, n in forms.items():
                tokens += n
                if form not in keep_set:
                    continue
                lem = lemma_cache.get(form)
                if lem:
                    lemmas[lem] += n
                    lemmatized += n
            lemma_freq.update(lemmas)
            totals[urn] = {"tokens": tokens, "tokens_lemmatized": lemmatized}
            n_pairs += len(lemmas)
            if sink:
                for lem, n in lemmas.most_common():
                    sink.write(f"{urn}\t{lem}\t{n}\n")
    finally:
        if sink:
            sink.close()

    total_tokens = sum(t["tokens"] for t in totals.values())
    total_lemmatized = sum(t["tokens_lemmatized"] for t in totals.values())
    stats = {
        "works": len(totals),
        "distinct_forms": len(corpus_forms),
        "forms_above_min": len(keep),
        "min_count": args.min_count,
        "distinct_lemmas": len(lemma_freq),
        "work_lemma_pairs": n_pairs,
        "total_tokens": total_tokens,
        "tokens_lemmatized": total_lemmatized,
        "coverage_pct": round(100 * total_lemmatized / total_tokens, 1) if total_tokens else 0,
        "top30": [[w, c] for w, c in lemma_freq.most_common(30)],
    }
    if args.limit:
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        print(f"\n--limit {args.limit}: sanity slice only, nothing written",
              file=sys.stderr)
        return

    (DATA / "work_token_totals.json").write_text(
        json.dumps(totals, ensure_ascii=False, indent=0, sort_keys=True))
    (DATA / "work_lemma_counts_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1))
    # Off by default: build_lemma_frequency.py is the Makefile's declared
    # producer of the per-lemma table ($(LEMMA_FREQ)), and writing it from here
    # too made whichever ran last win. They do not agree - different caches, and
    # --min-count 2 here against the Makefile's 5, so 282,974 lemmas against
    # 85,184. Worse, validate_cache above reads that file as its reference, so
    # writing it here closes a loop: the validator would be graded against the
    # output of the thing it validates.
    if not args.write_lemma_frequency:
        print("skipping public_lemma_frequency.tsv (build_lemma_frequency.py "
              "owns it; pass --write-lemma-frequency to override)",
              file=sys.stderr)
        print(f"\nworks: {len(totals):,} | work-lemma pairs: {n_pairs:,} | "
              f"lemmas: {len(lemma_freq):,} | tokens lemmatized: "
              f"{total_lemmatized:,}/{total_tokens:,} ({stats['coverage_pct']}%)",
              file=sys.stderr)
        print("wrote data/work_lemma_counts.tsv.gz, work_token_totals.json, "
              "work_lemma_counts_stats.json", file=sys.stderr)
        return
    with (DATA / "public_lemma_frequency.tsv").open("w", encoding="utf-8") as f:
        for lemma, c in lemma_freq.most_common():
            f.write(f"{lemma}\t{c}\n")
    freq_stats = {
        "distinct_forms": len(keep),
        "min_count": args.min_count,
        "forms_skipped_below_min": skipped,
        "distinct_lemmas": len(lemma_freq),
        "total_tokens": total_tokens,
        "tokens_lemmatized": total_lemmatized,
        "coverage_pct": round(100 * total_lemmatized / total_tokens, 1) if total_tokens else 0,
        "top30": [[w, c] for w, c in lemma_freq.most_common(30)],
    }
    (DATA / "public_lemma_frequency_stats.json").write_text(
        json.dumps(freq_stats, ensure_ascii=False, indent=1))
    print(f"\nworks: {len(totals):,} | work-lemma pairs: {n_pairs:,} | "
          f"lemmas: {len(lemma_freq):,} | tokens lemmatized: "
          f"{total_lemmatized:,}/{total_tokens:,} ({stats['coverage_pct']}%)",
          file=sys.stderr)
    print("wrote data/work_lemma_counts.tsv.gz, work_token_totals.json, "
          "work_lemma_counts_stats.json, public_lemma_frequency.tsv",
          file=sys.stderr)


if __name__ == "__main__":
    main()
