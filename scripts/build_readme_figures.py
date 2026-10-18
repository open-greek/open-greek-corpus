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
    if args.check and updated != original:
        parser.exit(1, "README corpus figures are stale; run build_readme_figures.py --write\n")
    if args.write and updated != original:
        path.write_text(updated, encoding="utf-8")
    print(json.dumps({**figures, "token_basis": "coverage.analysis_tokens (checked lexical projection)"}, indent=2))


if __name__ == "__main__":
    main()
