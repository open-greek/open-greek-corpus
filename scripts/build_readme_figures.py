#!/usr/bin/env python3
"""Refresh README status and identity counts from checked corpus measurements.

Run build_public_corpus.py and build_work_index.py first. Eligible token totals
come from coverage.analysis_tokens; source categories include every primary
row.source label. Nested licensed-witness credits remain separate. This never
writes corpus data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(pattern, replacement, text, label):
    result, count = re.subn(pattern, replacement, text, flags=re.M)
    if count != 1:
        raise ValueError(f"README {label} sentence is missing or ambiguous")
    return result


def sync_identity_counts(text, works):
    counts = {key: sum(bool((work.get("work_anchors") or {}).get(key)) for work in works.values())
              for key in ("cts", "tlg", "wikidata")}
    without = sum(not any((work.get("work_anchors") or {}).values()) for work in works.values())
    text = replace_once(r"`cts` on [\d,]+ works, `tlg` on [\d,]+,\s*\n`wikidata` on [\d,]+\)",
        f"`cts` on {counts['cts']:,} works, `tlg` on {counts['tlg']:,},\n`wikidata` on {counts['wikidata']:,})",
        text, "identity-anchor")
    return replace_once(r"[\d,]+ of the [\d,]+ served works have no(\s+external id at all)",
        lambda match: f"{without:,} of the {len(works):,} served works have no" + match[1], text, "no-external-anchor")


def figure_values(data):
    coverage = json.loads((data / "coverage.json").read_text(encoding="utf-8"))
    works = json.loads((data / "work_index.json").read_text(encoding="utf-8"))["works"]
    if coverage.keys() != works.keys():
        raise ValueError("Coverage and Work index describe different served works; rebuild both")
    tokens, sources = 0, set()
    for slug, row in coverage.items():
        if (not isinstance(row.get("analysis_tokens"), int) or row["analysis_tokens"] < 0 or
                not isinstance(row.get("sources"), list) or not row["sources"] or
                any(not isinstance(source, str) or not source for source in row["sources"])):
            raise ValueError(f"Coverage lacks checked analysis/source totals for {slug}; run build_public_corpus.py")
        tokens += row["analysis_tokens"]
        sources.update(row["sources"])
    return {"works": len(works), "analysis_tokens": tokens, "sources": sorted(sources)}, works


def render(text, figures, works):
    text = sync_identity_counts(text, works)
    return replace_once(r"^- [\d,]+ works served, [\d.]+M Greek tokens[^\n]*(?:sources|source categories)\.$",
        f"- {figures['works']:,} works served, {figures['analysis_tokens'] / 1e6:.1f}M Greek tokens "
        f"in the checked lexical projection, {len(figures['sources'])} source categories.", text, "status")


def sync_duplicate_counts(text, leaf, pages):
    """Keep the duplicate-candidate prose bound to its generated diagnostics."""
    bands = {band["band"]: band for band in pages["served_droppable_by_containment"]}
    high, low = bands["0.90-0.99"], bands["0.80-0.90"]
    text = replace_once(
        r"[\d,]+ served pairs and [\d,]+ tokens sit\n\s*above 0\.90, another [\d,]+ pairs and [\d,]+ tokens between 0\.80 and 0\.90",
        f"{high['pairs']:,} served pairs and {high['tokens']:,} tokens sit\n"
        f"  above 0.90, another {low['pairs']:,} pairs and {low['tokens']:,} tokens between 0.80 and 0.90",
        text, "duplicate page bands")
    text = replace_once(
        r"same-item ones beside them, [\d,]+ pairs\n\s*and [\d,]+ tokens in the top band and [\d,]+ and [\d,]+ in the next",
        f"same-item ones beside them, {high['same_item_pairs']:,} pairs\n"
        f"  and {high['same_item_tokens']:,} tokens in the top band and "
        f"{low['same_item_pairs']:,} and {low['same_item_tokens']:,} in the next",
        text, "same-item duplicate bands")
    runs = pages["duplicate_runs"]
    text = replace_once(
        r"[\d,]+ runs are recorded in `duplicate_runs`, [\d,]+ of them touching served\n\s*text, and (?:about )?[\d,]+ tokens",
        f"{runs['runs']:,} runs are recorded in `duplicate_runs`, {runs['served_runs']:,} of them touching served\n"
        f"  text, and {runs['served_tokens_in_second_reads']:,} tokens", text, "duplicate runs")
    text = replace_once(r"lists [\d,]+ remaining pairs in [\d,]+ files",
        f"lists {leaf['candidates']:,} remaining pairs in {len(leaf['by_file']):,} files",
        text, "duplicate leaf candidates")
    text = replace_once(r"[\d,]+ pairs have\s+a side that holds nothing the other lacks, [\d,]+ tokens",
        f"{leaf['clean_second_copies']:,} pairs have\n  a side that holds nothing the other lacks, "
        f"{leaf['clean_second_copies_tokens']:,} tokens", text, "contained leaf readings")
    text = replace_once(r"of which [\d,]+ pairs and\n\s*[\d,]+ tokens are in served text",
        f"of which {leaf['clean_second_copies_served']:,} pairs and\n"
        f"  {leaf['clean_second_copies_served_tokens']:,} tokens are in served text",
        text, "served duplicate leaf candidates")
    return replace_once(r"the other [\d,]+ pairs, [\d,]+ tokens, cannot be\s+dropped from either side",
        f"the other {leaf['overlapping_not_copies']:,} pairs, {leaf['overlapping_not_copies_tokens']:,} tokens, cannot be\n"
        "  dropped from either side", text, "complementary leaf readings")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    figures, works = figure_values(args.root / "data")
    path = args.root / "README.md"
    original = path.read_text(encoding="utf-8")
    updated = render(original, figures, works)
    if "served pairs and" in original or "remaining pairs in" in original:
        diagnostics = {name: json.loads((args.root / "data" / (name + ".json")).read_bytes())
                       for name in ("duplicate_leaf_candidates", "duplicate_page_candidates")}
        updated = sync_duplicate_counts(updated, diagnostics["duplicate_leaf_candidates"],
                                        diagnostics["duplicate_page_candidates"])
    if args.check and updated != original:
        parser.exit(1, "README corpus figures are stale; run build_readme_figures.py --write\n")
    if args.write and updated != original:
        path.write_text(updated, encoding="utf-8")
    print(json.dumps({**figures, "token_basis": "coverage.analysis_tokens (checked lexical projection)"}, indent=2))


if __name__ == "__main__":
    main()
