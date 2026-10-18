"""Figures the README states in prose have to match the data it describes.

scripts/build_readme_figures.py rewrites these sentences. Tests independently
recompute eligible tokens and source categories from the served rows, so a
display alternative or restored fragment cannot silently inflate the headline.

A wrong count in the README is not cosmetic: it is the first number a reader
takes, and the corpus total is the one figure a consumer checks a download
against.
"""

from collections import Counter, defaultdict
from functools import lru_cache
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_public_corpus import _GK  # noqa: E402
from build_work_index import _raw_identifier_title  # noqa: E402
from frequency_projection import FrequencyProjection  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
README = (REPO / "README.md").read_text(encoding="utf-8")
WORKS = json.loads((REPO / "data" / "work_index.json")
                   .read_text(encoding="utf-8"))["works"]


def _n(s: str) -> int:
    return int(s.replace(",", ""))


def test_anchor_counts_match_work_index():
    m = re.search(r"`cts` on ([\d,]+) works, `tlg` on ([\d,]+),\s*\n"
                  r"`wikidata` on ([\d,]+)\)", README)
    assert m, "the anchor sentence moved; update this test with it"
    said_cts, said_tlg, said_wd = (_n(m.group(i)) for i in (1, 2, 3))
    have = lambda k: sum(1 for x in WORKS.values()  # noqa: E731
                         if (x.get("work_anchors") or {}).get(k))
    assert (said_cts, said_tlg, said_wd) == (have("cts"), have("tlg"),
                                            have("wikidata"))


def test_served_work_titles_do_not_publish_raw_tlg_identifiers():
    raw = [(slug, work.get("title")) for slug, work in WORKS.items()
           if _raw_identifier_title(work.get("title") or "")]
    assert raw == []


def test_no_external_anchor_sentence_matches_work_index():
    match = re.search(r"([\d,]+) of the ([\d,]+) served works have no\s+external id at all", README)
    assert match, "the no-anchor sentence moved; update this test with it"
    without = sum(not any((work.get("work_anchors") or {}).values()) for work in WORKS.values())
    assert tuple(_n(match[i]) for i in [1, 2]) == (without, len(WORKS))


@lru_cache(maxsize=1)
def independent_corpus_totals():
    frequency = FrequencyProjection(REPO / "data")
    totals, sources = Counter(), defaultdict(set)
    for path in sorted((REPO / "data/corpus").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            slug = row.get("urn") or path.stem
            totals[slug] += len(_GK.findall(frequency.text(row)))
            if row.get("source"):
                sources[slug].add(row["source"])
    return totals, sources


def test_status_line_matches_the_served_corpus():
    m = re.search(r"- ([\d,]+) works served, ([\d.]+)M Greek tokens in the checked lexical projection, ([\d,]+) source categories\.", README)
    assert m, "the Status line moved; update this test with it"
    assert _n(m.group(1)) == len(WORKS)

    totals, sources = independent_corpus_totals()
    total = sum(totals.values())
    assert set(totals) == set(WORKS)
    assert _n(m[3]) == len(set().union(*sources.values()))
    # One decimal place, so the assertion is as tight as the claim itself.
    assert f"{total / 1e6:.1f}" == m.group(2), \
        f"README says {m.group(2)}M, corpus holds {total:,}"


def test_coverage_analysis_and_source_totals_match_independent_projection():
    totals, sources = independent_corpus_totals()
    coverage = json.loads((REPO / "data/coverage.json").read_text())
    assert set(coverage) == set(totals)
    assert {slug: row.get("analysis_tokens") for slug, row in coverage.items()} == dict(totals)
    assert {slug: set(row.get("sources", [])) for slug, row in coverage.items()} == dict(sources)
