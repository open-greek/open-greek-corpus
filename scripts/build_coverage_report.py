#!/usr/bin/env python3
"""Build a coverage report: what the open corpus has ACTUALLY ingested vs.
what is POTENTIALLY reachable, so the exact gap is visible.

Inputs (read-only):
  data/inventory/sourcing_map.csv  - per-TLG-work potential publish route
  data/corpus_editions.json        - what we actually have ingested

Output:
  data/coverage_report.json        - machine-readable report
  stdout                           - human summary

Join key for a sourcing_map row: f"{tlg_id}.tlg{work_id}"
  (e.g. tlg0012 + 001 -> tlg0012.tlg001)

Classification of each sourcing_map work:
  ingested               key present in corpus_editions.json
  reachable_not_ingested best_source is a publishable route but not ingested
  locked                 best_source == locked
  duplicate              best_source == duplicate

Pure stdlib. Re-runnable.
"""

import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from source_precedence import REACHABLE_SOURCES, load_overrides, resolve
from crosswalk import slug_for

SOURCING_MAP = os.path.join(REPO, "data", "inventory", "sourcing_map.csv")
CORPUS_EDITIONS = os.path.join(REPO, "data", "corpus_editions.json")
OUT_JSON = os.path.join(REPO, "data", "coverage_report.json")


def _int(s):
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return 0


def load_sourcing_map(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["word_count"] = _int(row.get("word_count"))
            row["key"] = slug_for(f"{row['tlg_id']}.tlg{row['work_id']}", warn=False)
            rows.append(row)
    return rows


def main():
    rows = load_sourcing_map(SOURCING_MAP)
    overrides = load_overrides()
    # apply cog's source-precedence overrides on top of the sourcing-map verdict
    n_overridden = 0
    for row in rows:
        eff, reason = resolve(row["tlg_id"], row["work_id"],
                              row["best_source"], overrides)
        if reason is not None:
            n_overridden += 1
        row["base_best_source"] = row["best_source"]
        row["best_source"] = eff
        row["override_reason"] = reason
    with open(CORPUS_EDITIONS, encoding="utf-8") as f:
        editions = json.load(f)

    edition_keys = set(editions)

    # CGPG keys most text per TLG work (urn "tlgAUTHOR.tlgWORK"), which lands
    # directly in corpus_editions.json and so is counted ingested via its own key
    # below. But a multi-work volume that can't be split safely stays VOLUME-keyed
    # (cogPG.*); credit the gap / locked works such a volume covers (from
    # cgpg_works.json) as ingested. Restrict this to cogPG.* units so per-work
    # units aren't double-handled.
    cgpg_covered = {}                       # work key -> covering volume urn
    cw_path = os.path.join(REPO, "data", "cgpg_works.json")
    if os.path.exists(cw_path):
        with open(cw_path, encoding="utf-8") as f:
            for vol in json.load(f):
                if not vol["urn"].startswith("cogPG."):
                    continue                # per-work unit: counted via its own key
                if vol["urn"] not in edition_keys:
                    continue                # volume not actually ingested
                for w in vol.get("works", []):
                    if w.get("status") in ("gap", "locked"):
                        cgpg_covered[slug_for(f"{w['tlg_id']}.tlg{w['work_id']}", warn=False)] = vol["urn"]

    buckets = {
        "ingested": [],
        "reachable_not_ingested": [],
        "locked": [],
        "duplicate": [],
    }
    other = []  # best_source not in any known category (defensive)

    matched_edition_keys = set()

    n_via_cgpg = 0
    for row in rows:
        key = row["key"]
        best = row["best_source"]
        via_cgpg = best == "migne_cgpg" and key in cgpg_covered
        if key in edition_keys:
            buckets["ingested"].append(row)
            matched_edition_keys.add(key)
        elif via_cgpg:
            row["ingested_via"] = cgpg_covered[key]
            buckets["ingested"].append(row)
            n_via_cgpg += 1
        elif best == "locked":
            buckets["locked"].append(row)
        elif best == "duplicate":
            buckets["duplicate"].append(row)
        elif best in REACHABLE_SOURCES:
            buckets["reachable_not_ingested"].append(row)
        else:
            other.append(row)

    # Proportional coverage: "ingested" is binary (a key is present or not), so a
    # fragment or an in-progress OCR counts a whole work as done. Compare each
    # ingested work's actual token count against its expected size to split
    # COMPLETE from PARTIAL, and credit only the words actually ingested.
    COMPLETE_RATIO = 0.5
    actual_ingested_words = 0
    for row in buckets["ingested"]:
        w = row["word_count"]
        if "ingested_via" in row:                 # CGPG volume holds the full work
            nt, ratio = w, 1.0
        else:
            nt = _int(editions.get(row["key"], {}).get("n_tokens"))
            ratio = (nt / w) if w else 1.0
        row["ingested_tokens"] = nt
        row["coverage_ratio"] = round(min(ratio, 9.99), 3)
        row["complete"] = ratio >= COMPLETE_RATIO
        actual_ingested_words += min(nt, w) if w else nt
    ingested_complete = [r for r in buckets["ingested"] if r["complete"]]
    ingested_partial = [r for r in buckets["ingested"] if not r["complete"]]

    def summarize(rs):
        return {"works": len(rs), "word_count": sum(r["word_count"] for r in rs)}

    bucket_summary = {name: summarize(rs) for name, rs in buckets.items()}
    bucket_summary["ingested_complete"] = summarize(ingested_complete)
    bucket_summary["ingested_partial"] = summarize(ingested_partial)
    if other:
        bucket_summary["other"] = summarize(other)

    # (2) breakdown of reachable_not_ingested by best_source
    reach = buckets["reachable_not_ingested"]
    by_source = {}
    for r in reach:
        s = r["best_source"]
        b = by_source.setdefault(s, {"works": 0, "word_count": 0})
        b["works"] += 1
        b["word_count"] += r["word_count"]
    by_source = dict(sorted(by_source.items(), key=lambda kv: -kv[1]["word_count"]))

    # (3) gap list: reachable_not_ingested sorted by word_count desc
    def gap_entry(r):
        e = {
            "tlg_id": r["tlg_id"],
            "work_id": r["work_id"],
            "author": r["author"],
            "title": r["title"],
            "word_count": r["word_count"],
            "best_source": r["best_source"],
        }
        if r.get("override_reason"):
            e["base_best_source"] = r["base_best_source"]
            e["override_reason"] = r["override_reason"]
        return e

    gap_list = [gap_entry(r) for r in sorted(reach, key=lambda r: -r["word_count"])]

    # (4) ingested editions NOT in the sourcing map (cogByz.*, ggm/ogl, etc.)
    extra_keys = sorted(edition_keys - matched_edition_keys)
    extra = []
    extra_tokens = 0
    for k in extra_keys:
        v = editions[k]
        toks = _int(v.get("n_tokens"))
        extra_tokens += toks
        extra.append(
            {
                "key": k,
                "edition": v.get("edition"),
                "source": v.get("source"),
                "license": v.get("license"),
                "n_passages": v.get("n_passages"),
                "n_tokens": toks,
            }
        )
    extra.sort(key=lambda e: -(e["n_tokens"] or 0))

    # (5) headline: total corpus words and percentage split
    total_words = sum(r["word_count"] for r in rows)

    def pct(name):
        w = bucket_summary[name]["word_count"]
        return round(100.0 * w / total_words, 2) if total_words else 0.0

    pct_actual = round(100.0 * actual_ingested_words / total_words, 2) if total_words else 0.0

    headline = {
        "total_works": len(rows),
        "total_words": total_words,
        "source_overrides_applied": n_overridden,
        "ingested_via_cgpg_volume": n_via_cgpg,
        "pct_ingested": pct("ingested"),
        # proportional: actual ingested words (a partial counts only its real text)
        "pct_ingested_actual": pct_actual,
        "ingested_words_actual": actual_ingested_words,
        "ingested_complete_works": len(ingested_complete),
        "ingested_partial_works": len(ingested_partial),
        "pct_reachable_not_ingested": pct("reachable_not_ingested"),
        "pct_locked": pct("locked"),
        "pct_duplicate": pct("duplicate"),
    }

    # partial works: ingested but incomplete (fragments / in-progress OCR), the
    # finish-this queue, sorted by how many words are still missing.
    partial_list = [
        {"tlg_id": r["tlg_id"], "work_id": r["work_id"], "author": r["author"],
         "title": r["title"], "word_count": r["word_count"],
         "ingested_tokens": r["ingested_tokens"], "coverage_ratio": r["coverage_ratio"],
         "source": editions.get(r["key"], {}).get("source", r["best_source"]),
         "missing_words": max(0, r["word_count"] - r["ingested_tokens"])}
        for r in sorted(ingested_partial, key=lambda r: -(r["word_count"] - r["ingested_tokens"]))
    ]

    report = {
        "headline": headline,
        "buckets": bucket_summary,
        "reachable_not_ingested_by_source": by_source,
        "gap_list": gap_list,
        "partial_ingestions": partial_list,
        "ingested_not_in_sourcing_map": {
            "works": len(extra),
            "n_tokens": extra_tokens,
            "items": extra,
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")

    print_summary(report)


def _fmt(n):
    return f"{n:,}"


def print_summary(report):
    h = report["headline"]
    b = report["buckets"]
    print("=" * 72)
    print("OPEN GREEK CORPUS - COVERAGE REPORT (F2)")
    print("=" * 72)
    print(
        f"Total TLG works in sourcing map: {_fmt(h['total_works'])}"
        f"   Total words: {_fmt(h['total_words'])}"
    )
    print()
    print(f"{'BUCKET':<26}{'WORKS':>10}{'WORDS':>16}{'% WORDS':>10}")
    print("-" * 62)
    order = ["ingested", "reachable_not_ingested", "locked", "duplicate"]
    if "other" in b:
        order.append("other")
    total_w = h["total_words"] or 1
    for name in order:
        s = b[name]
        p = 100.0 * s["word_count"] / total_w
        print(
            f"{name:<26}{_fmt(s['works']):>10}{_fmt(s['word_count']):>16}{p:>9.1f}%"
        )
    print()
    print("HEADLINE (by word_count):")
    print(f"  ingested (binary)      {h['pct_ingested']:>6.2f}%   "
          f"({_fmt(h['ingested_complete_works'])} complete, "
          f"{_fmt(h['ingested_partial_works'])} partial)")
    print(f"  ingested (actual words){h['pct_ingested_actual']:>6.2f}%   "
          f"({_fmt(h['ingested_words_actual'])} words actually ingested)")
    print(f"  reachable, not yet      {h['pct_reachable_not_ingested']:>6.2f}%")
    print(f"  locked                 {h['pct_locked']:>6.2f}%")
    print(f"  duplicate              {h['pct_duplicate']:>6.2f}%")
    print()
    pl = report["partial_ingestions"]
    if pl:
        miss = sum(p["missing_words"] for p in pl)
        print(f"PARTIAL INGESTIONS (started, not complete): {_fmt(len(pl))} works, "
              f"{_fmt(miss)} words still missing - top 8:")
        for p in pl[:8]:
            print(f"  {p['coverage_ratio']:>5.0%} {p['tlg_id']}.tlg{p['work_id']:<8} "
                  f"{p['ingested_tokens']:>8,}/{p['word_count']:<8,} {p['source']:<10} "
                  f"{(p['author']+' / '+p['title'])[:42]}")
        print()

    print("REACHABLE-NOT-INGESTED breakdown by best_source:")
    print(f"  {'best_source':<16}{'WORKS':>8}{'WORDS':>16}")
    for s, d in report["reachable_not_ingested_by_source"].items():
        print(f"  {s:<16}{_fmt(d['works']):>8}{_fmt(d['word_count']):>16}")
    print()

    extra = report["ingested_not_in_sourcing_map"]
    print(
        f"INGESTED but NOT in sourcing map: {_fmt(extra['works'])} works, "
        f"{_fmt(extra['n_tokens'])} tokens"
    )
    print()

    gap = report["gap_list"]
    print(f"GAP LIST (reachable, not ingested) - top 50 of {_fmt(len(gap))}:")
    print(
        f"  {'#':>3} {'WORDS':>10}  {'best_source':<12} {'KEY':<18} AUTHOR / TITLE"
    )
    for i, g in enumerate(gap[:50], 1):
        key = slug_for(f"{g['tlg_id']}.tlg{g['work_id']}", warn=False)
        at = f"{g['author']} / {g['title']}"
        if len(at) > 60:
            at = at[:57] + "..."
        print(
            f"  {i:>3} {_fmt(g['word_count']):>10}  {g['best_source']:<12} "
            f"{key:<18} {at}"
        )
    print("=" * 72)
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
