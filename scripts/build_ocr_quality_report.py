#!/usr/bin/env python3
"""Per-work OCR quality report over the served corpus.

Two signals, both computed from this repo's own data (self-contained, stdlib
only, no prebuilt lexicon file):

1. Unattested-token rate, per OCR-source work (source `ocr` or `cgpg` in
   data/corpus_editions.json): the fraction of Greek tokens of >= 4 chars that
   are not attested anywhere in the clean (non-OCR) part of data/corpus
   (first1k, perseus, pta, galenus_verbatim, byzantium_gr, dfhg, ...). This
   mirrors the suspect-token filter of greek-ocr/scripts/ocr_llm_correct.py
   iter_passages exactly: tokens come from the same Greek-block regex, are
   NFC-normalized, all-uppercase tokens (headings) are excluded, and the
   attestation lookup is case-sensitive with accents kept (that script's
   _skeleton accent fold is only used when validating proposed fixes, not for
   attestation). A high rate means heavy OCR garble OR genuinely rare
   vocabulary (lexica, dialect glosses), so it is a triage signal, not a CER.

2. Witness agreement, where data/corpus_secondary/<work>.jsonl holds a
   displaced edition of the same work: occurrence-weighted word-bigram
   containment between the primary and the secondary text, both directions,
   after the same normalization scripts/dedup_fhg_containment.py uses (NFD,
   diacritics stripped, lowercased, Greek letters only, final sigma folded).
   Bigrams are taken inside a passage record, never across records. These are
   containment ESTIMATES, not aligned error rates: the two editions are not
   locus-aligned and often cover different spans, so a low number can mean
   coverage mismatch as well as OCR damage. Secondary rows whose
   secondary_reason marks a MIS-INGEST (a different work wrongly filed under
   the slug) are excluded from the witness and recorded in meta.skips.

For works whose PRIMARY is a clean (non-OCR) edition and whose secondary is
OCR, the same agreement stats are computed and summarized in the meta block:
OCR containment in a critical edition of the same work is a corpus-level
estimate of how much of the OCR text survives against a trusted reading.

Output: data/ocr_quality_report.json, deterministic (sorted keys, rounded
rates, no wall-clock anywhere), plus a human summary on stderr.

  python3 scripts/build_ocr_quality_report.py
  python3 scripts/build_ocr_quality_report.py --only hesychius-lexicography.lexicon-o
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EDITIONS = REPO / "data" / "corpus_editions.json"
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
OUT = REPO / "data" / "ocr_quality_report.json"

OCR_SOURCES = {"ocr", "cgpg"}
MIN_RANK_TOKENS = 2000          # worst_first / quartiles floor, so tiny fragmenta don't dominate
MIN_SUSPECT_LEN = 4             # same floor as ocr_llm_correct.py iter_passages

# Token regex identical to ocr_llm_correct.py / ocr_freq_correct.py (_GK).
_GK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
# Single Greek letter, for the witness normalization (dedup_fhg_containment.py).
_GK_CHAR = re.compile(r"[Ͱ-Ͽἀ-῿]")

_NFC = unicodedata.normalize


def iter_records(path: Path):
    """Yield the JSON record of every non-blank line of a corpus jsonl file."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def greek_tokens(text: str) -> list[str]:
    """NFC Greek tokens, exactly as ocr_llm_correct.py extracts them."""
    return [_NFC("NFC", t) for t in _GK.findall(text)]


def build_attestation(editions: dict) -> tuple[set[str], dict]:
    """One pass over the non-OCR works in data/corpus -> set of attested NFC
    forms. Matches reference_from_corpus() in greek-ocr (which excludes the
    NOISY_SOURCES {ocr, cgpg}), but self-contained here."""
    attested: set[str] = set()
    n_works = n_occ = 0
    sources = set()
    for slug in sorted(editions):
        info = editions[slug]
        if info["source"] in OCR_SOURCES:
            continue
        fp = CORPUS / f"{slug}.jsonl"
        if not fp.exists():
            continue
        n_works += 1
        sources.add(info["source"])
        for rec in iter_records(fp):
            toks = greek_tokens(rec.get("text") or "")
            n_occ += len(toks)
            attested.update(toks)
    stats = {
        "n_works": n_works,
        "n_token_occurrences": n_occ,
        "n_unique_forms": len(attested),
        "sources": sorted(sources),
        "excluded_sources": sorted(OCR_SOURCES),
    }
    return attested, stats


def unattested_stats(records: list[dict], attested: set[str]) -> dict:
    """Token counts and the unattested rate for one work's records."""
    n_tokens = n_checked = n_unattested = 0
    for rec in records:
        for t in greek_tokens(rec.get("text") or ""):
            n_tokens += 1
            if len(t) < MIN_SUSPECT_LEN or t.isupper():
                continue
            n_checked += 1
            if t not in attested:
                n_unattested += 1
    return {
        "n_tokens": n_tokens,
        "n_tokens_checked": n_checked,
        "n_unattested": n_unattested,
        "unattested_rate": round(n_unattested / n_checked, 6) if n_checked else None,
    }


def witness_norm(tok: str) -> str:
    """dedup_fhg_containment.py norm(): NFD, strip diacritics, lowercase,
    Greek letters only, final sigma folded."""
    d = unicodedata.normalize("NFD", tok.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = "".join(c for c in d if _GK_CHAR.match(c))
    return d.replace("ς", "σ")


def work_bigrams(records: list[dict]) -> Counter:
    """Occurrence counts of normalized word bigrams, adjacency taken inside
    each passage record only (no false bigrams across record boundaries)."""
    grams: Counter = Counter()
    for rec in records:
        t = [w for w in (witness_norm(x) for x in (rec.get("text") or "").split()) if w]
        grams.update(zip(t, t[1:]))
    return grams


def containment(a: Counter, b: Counter) -> float | None:
    """Fraction of a's bigram occurrences whose bigram occurs anywhere in b."""
    total = sum(a.values())
    if not total:
        return None
    hit = sum(c for g, c in a.items() if g in b)
    return round(hit / total, 6)


def secondary_profile(path: Path) -> tuple[list[dict], set[str], list[str], int]:
    """Records, source set and sorted edition list of a secondary file.

    Rows whose secondary_reason marks a MIS-INGEST (the displaced text is a
    DIFFERENT work that was wrongly filed under this slug, e.g. the Aeneas
    Tacticus volume once serving as Aeneas of Gaza) are dropped: they are not
    a witness of this work and would poison the agreement estimates. The
    number of dropped rows is returned so the skip is recorded."""
    records = list(iter_records(path))
    kept = [r for r in records
            if "mis-ingest" not in (r.get("secondary_reason") or "").lower()]
    n_dropped = len(records) - len(kept)
    sources = {r.get("source") for r in kept}
    eds = sorted({r.get("edition") or "" for r in kept})
    return kept, sources, eds, n_dropped


def quartile_summary(values: list[float]) -> dict | None:
    """min/q1/median/q3/max with linear interpolation; deterministic."""
    if not values:
        return None
    vals = sorted(values)

    def pct(p: float) -> float:
        k = p * (len(vals) - 1)
        f, c = math.floor(k), math.ceil(k)
        v = vals[f] if f == c else vals[f] + (vals[c] - vals[f]) * (k - f)
        return round(v, 4)

    return {"min": pct(0.0), "q1": pct(0.25), "median": pct(0.5),
            "q3": pct(0.75), "max": pct(1.0), "n": len(vals)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", metavar="SLUG",
                    help="sanity-check mode: compute and print stats for these "
                         "slugs only; the report file is NOT written")
    args = ap.parse_args()

    editions = json.loads(EDITIONS.read_text(encoding="utf-8"))
    attested, att_stats = build_attestation(editions)
    print(f"attestation set: {att_stats['n_unique_forms']} forms from "
          f"{att_stats['n_works']} non-OCR works "
          f"({att_stats['n_token_occurrences']} token occurrences)", file=sys.stderr)

    ocr_slugs = sorted(s for s, i in editions.items() if i["source"] in OCR_SOURCES)
    skips: list[dict] = []
    works: dict[str, dict] = {}

    todo = args.only if args.only else ocr_slugs
    for slug in todo:
        info = editions.get(slug)
        if info is None:
            skips.append({"slug": slug, "reason": "not in corpus_editions.json"})
            continue
        if args.only and info["source"] not in OCR_SOURCES:
            # sanity-check mode may name a TEI-primary work; handled below
            continue
        fp = CORPUS / f"{slug}.jsonl"
        if not fp.exists():
            skips.append({"slug": slug, "reason": "corpus file missing"})
            continue
        records = list(iter_records(fp))
        if not records:
            skips.append({"slug": slug, "reason": "corpus file empty"})
            continue
        stats = unattested_stats(records, attested)

        witness = None
        sfp = SECONDARY / f"{slug}.jsonl"
        if sfp.exists():
            sec_records, _, sec_eds, n_dropped = secondary_profile(sfp)
            if n_dropped:
                skips.append({"slug": slug,
                              "reason": f"{n_dropped} mis-ingested secondary rows "
                                        f"(different work) excluded from the witness"})
            if sec_records:
                p_grams = work_bigrams(records)
                s_grams = work_bigrams(sec_records)
                witness = {
                    "secondary_edition": " + ".join(sec_eds),
                    "agreement_primary_in_secondary": containment(p_grams, s_grams),
                    "agreement_secondary_in_primary": containment(s_grams, p_grams),
                    "n_bigrams_primary": sum(p_grams.values()),
                    "n_bigrams_secondary": sum(s_grams.values()),
                }
            else:
                skips.append({"slug": slug, "reason": "secondary file empty; witness null"})
        works[slug] = {
            "source": info["source"],
            "edition": info["edition"],
            "witness": witness,
            **stats,
        }

    # TEI-primary works whose displaced secondary is OCR: the OCR containment
    # in the trusted primary is a corpus-level OCR quality estimate.
    tei_pairs: dict[str, dict] = {}
    for sfp in sorted(SECONDARY.glob("*.jsonl")):
        slug = sfp.stem
        info = editions.get(slug)
        if info is None:
            skips.append({"slug": slug,
                          "reason": "secondary file has no primary in corpus_editions.json "
                                    "(fully displaced or renamed slug); not paired"})
            continue
        if info["source"] in OCR_SOURCES:
            continue                       # already handled as an OCR-primary witness
        if args.only and slug not in args.only:
            continue
        sec_records, sec_sources, sec_eds, n_dropped = secondary_profile(sfp)
        if n_dropped:
            skips.append({"slug": slug,
                          "reason": f"{n_dropped} mis-ingested secondary rows "
                                    f"(different work) excluded from the witness"})
        if not sec_records:
            skips.append({"slug": slug, "reason": "secondary file empty; not paired"})
            continue
        if not sec_sources <= OCR_SOURCES:
            skips.append({"slug": slug,
                          "reason": f"secondary is not OCR (sources: "
                                    f"{', '.join(sorted(str(s) for s in sec_sources))}); "
                                    f"not an OCR-error pair"})
            continue
        pfp = CORPUS / f"{slug}.jsonl"
        if not pfp.exists():
            skips.append({"slug": slug, "reason": "corpus file missing"})
            continue
        p_grams = work_bigrams(list(iter_records(pfp)))
        s_grams = work_bigrams(sec_records)
        agree = containment(s_grams, p_grams)
        if agree is None:
            skips.append({"slug": slug, "reason": "no bigrams on the OCR side; not paired"})
            continue
        tei_pairs[slug] = {
            "primary_source": info["source"],
            "primary_edition": info["edition"],
            "secondary_edition": " + ".join(sec_eds),
            "agreement_ocr_in_tei": agree,
            "agreement_tei_in_ocr": containment(p_grams, s_grams),
            "n_bigrams_ocr": sum(s_grams.values()),
        }

    skips.sort(key=lambda s: (s["slug"], s["reason"]))

    # Ranking and distributions, restricted to non-tiny works.
    ranked = [(s, w) for s, w in works.items()
              if w["n_tokens"] >= MIN_RANK_TOKENS and w["unattested_rate"] is not None]
    ranked.sort(key=lambda kv: (-kv[1]["unattested_rate"], -kv[1]["n_tokens"], kv[0]))
    worst_first = [s for s, _ in ranked]
    rate_quartiles = quartile_summary([w["unattested_rate"] for _, w in ranked])

    tei_big = [p["agreement_ocr_in_tei"] for p in tei_pairs.values()
               if p["n_bigrams_ocr"] >= MIN_RANK_TOKENS]
    tei_all = [p["agreement_ocr_in_tei"] for p in tei_pairs.values()]
    tei_block = {
        "n_pairs": len(tei_pairs),
        "n_pairs_summarized": len(tei_big),
        "agreement_ocr_in_tei_quartiles": quartile_summary(tei_big),
        "agreement_ocr_in_tei_quartiles_all_pairs": quartile_summary(tei_all),
        "note": "containment of the displaced OCR edition's word bigrams in the served "
                "clean edition of the same work; 1 - median is a rough corpus-level OCR "
                "error ESTIMATE, inflated by span/recension mismatch between editions. "
                f"Summarized pairs have >= {MIN_RANK_TOKENS} OCR-side bigrams.",
    }

    report = {
        "meta": {
            "generated_by": "scripts/build_ocr_quality_report.py",
            "inputs": ["data/corpus_editions.json", "data/corpus/*.jsonl",
                       "data/corpus_secondary/*.jsonl"],
            "methodology": "unattested rate = share of NFC Greek tokens >= 4 chars "
                           "(all-caps excluded) absent from the non-OCR corpus, per "
                           "ocr_llm_correct.py iter_passages; witness agreement = "
                           "occurrence-weighted normalized word-bigram containment "
                           "ESTIMATES between unaligned editions, per "
                           "dedup_fhg_containment.py normalization",
            "attestation": att_stats,
            "counts": {
                "ocr_works": len(works),
                "ocr_works_with_witness": sum(1 for w in works.values() if w["witness"]),
                "ocr_works_ranked": len(ranked),
                "tei_primary_ocr_secondary_pairs": len(tei_pairs),
                "secondary_files": len(list(SECONDARY.glob("*.jsonl"))),
                "skipped": len(skips),
            },
            "min_rank_tokens": MIN_RANK_TOKENS,
            "unattested_rate_quartiles": rate_quartiles,
            "tei_primary_ocr_error_estimate": tei_block,
            "skips": skips,
        },
        "works": works,
        "worst_first": worst_first,
    }

    if args.only:
        for slug in args.only:
            if slug in works:
                print(f"{slug}: {json.dumps(works[slug], ensure_ascii=False)}",
                      file=sys.stderr)
            elif slug in tei_pairs:
                print(f"{slug} (TEI-primary pair): "
                      f"{json.dumps(tei_pairs[slug], ensure_ascii=False)}", file=sys.stderr)
            else:
                print(f"{slug}: skipped or not an OCR/witnessed work", file=sys.stderr)
        print("--only mode: report NOT written", file=sys.stderr)
        return

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT} ({len(works)} OCR works)", file=sys.stderr)

    print(f"\nunattested-rate distribution over the {len(ranked)} OCR works with >= "
          f"{MIN_RANK_TOKENS} Greek tokens:", file=sys.stderr)
    if rate_quartiles:
        print(f"  min {rate_quartiles['min']}  q1 {rate_quartiles['q1']}  "
              f"median {rate_quartiles['median']}  q3 {rate_quartiles['q3']}  "
              f"max {rate_quartiles['max']}", file=sys.stderr)
    print("\n15 worst (unattested rate, Greek tokens):", file=sys.stderr)
    for slug in worst_first[:15]:
        w = works[slug]
        print(f"  {w['unattested_rate']:.3f}  {w['n_tokens']:>8}  {slug}", file=sys.stderr)
    q = tei_block["agreement_ocr_in_tei_quartiles"]
    if q:
        print(f"\nTEI-primary OCR-error estimate ({tei_block['n_pairs_summarized']} of "
              f"{tei_block['n_pairs']} pairs with >= {MIN_RANK_TOKENS} OCR-side bigrams):",
              file=sys.stderr)
        print(f"  OCR-in-TEI agreement median {q['median']} (q1 {q['q1']}, q3 {q['q3']}); "
              f"rough OCR error estimate ~{round(1 - q['median'], 4)} "
              f"(inflated by edition span mismatch)", file=sys.stderr)
    if skips:
        print(f"\n{len(skips)} skips recorded in meta.skips", file=sys.stderr)


if __name__ == "__main__":
    main()
