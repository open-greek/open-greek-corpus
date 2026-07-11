#!/usr/bin/env python3
"""Crosswalk-completeness report: how well each work/author/edition is linked to
external identifier systems, and whether each work has an edition-independent
canonical citation locus.

cog's identity spine is its own slug (author.work), with every external number
(TLG/CTS, Wikidata QID, VIAF/GND/ISNI, Trismegistos, ...) kept as a CROSSWALK
alias rather than the key (see docs/identity-and-citation.md). This report is to
that crosswalk what coverage_report.json is to text coverage: it shows, per
identifier namespace, how much of the registry is linked, and surfaces the
cheapest enrichment targets (e.g. works whose AUTHOR already has a Wikidata QID
but the work does not).

Input (read-only):
  data/source_registry.json   - authors + works + editions, each with an
                                `aliases` map and editions carrying a `scheme`

Output:
  data/crosswalk_report.json  - machine-readable completeness report
  stdout                      - human summary

Pure stdlib, deterministic (sorted, no wall-clock), so re-running is churn-free.
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from source_identity import scheme_depth, scheme_levels  # noqa: E402

REGISTRY = os.path.join(REPO, "data", "source_registry.json")
OUT_JSON = os.path.join(REPO, "data", "crosswalk_report.json")

# Target crosswalk namespaces per entity type (the design's alias schema). Listed
# even at 0% coverage so missing links read as gaps to fill, not silent absences.
WORK_NS = ["cts", "wikidata", "trismegistos", "perseus", "iowa"]
AUTHOR_NS = ["wikidata", "viaf", "gnd", "isni", "trismegistos"]
EDITION_NS = ["cts", "hathitrust", "trismegistos", "ldab", "doi", "isbn"]

# A citation scheme is edition-bound (physical) if it cites by a printed surface;
# otherwise it is a logical, edition-independent locus (book/chapter/section/line).
PHYSICAL_HINTS = ("page", "volume", "column", "folio")
CAP = 50  # max examples per enrichment list


def _pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def _is_logical(scheme):
    s = (scheme or "").strip().lower()
    return bool(s) and not any(h in s for h in PHYSICAL_HINTS)


def _ns_coverage(entities, namespaces):
    """count + pct of entities carrying each alias namespace, plus any namespace
    present in the data but not in the target list (so nothing is hidden)."""
    total = len(entities)
    present = {}
    for e in entities:
        for ns in e.get("aliases", {}):
            present[ns] = present.get(ns, 0) + 1
    cov = {}
    for ns in namespaces:
        cov[ns] = {"count": present.get(ns, 0), "pct": _pct(present.get(ns, 0), total)}
    for ns in sorted(present):
        if ns not in cov:
            cov[ns] = {"count": present[ns], "pct": _pct(present[ns], total),
                       "note": "present in data, not a target namespace"}
    return cov


def main():
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    authors, works = reg["authors"], reg["works"]
    author_list = list(authors.values())
    work_list = list(works.values())
    editions = [ed for w in work_list for ed in w.get("editions", {}).values()]
    nW, nA, nE = len(work_list), len(author_list), len(editions)

    # canonical-locus coverage: a work has a logical locus if any of its editions
    # cite by a logical (non-physical) scheme.
    by_scheme = {}
    works_logical = 0
    works_only_physical = []  # has editions, none logical
    for slug, w in works.items():
        schemes = [ed.get("scheme", "") for ed in w.get("editions", {}).values()]
        for s in schemes:
            by_scheme[s or "(none)"] = by_scheme.get(s or "(none)", 0) + 1
        if any(_is_logical(s) for s in schemes):
            works_logical += 1
        elif schemes:
            works_only_physical.append(slug)

    # Served canonical locus: the logical locus of the edition cog actually
    # renders bare citations against (default_edition). This is the Phase-2
    # measure - "one canonical logical locus per work" - and is stricter than the
    # any-edition view above, which counts a work logical even when only its
    # reference-only TLG edition carries a logical scheme. Depth comes from the
    # locus grammar (scheme_depth), and scheme_levels gives a cheap integrity
    # check for a malformed (empty-level) scheme.
    served_logical = 0
    served_physical = []     # default edition cites only by page/volume
    served_none = []         # no default edition, or it declares no scheme
    served_depths = {}
    malformed_schemes = 0
    for slug, w in works.items():
        de = w.get("default_edition")
        ed = w.get("editions", {}).get(de) if de else None
        for e in w.get("editions", {}).values():
            if any(x.strip() == "" for x in scheme_levels(e.get("scheme", ""))):
                malformed_schemes += 1
        sch = ed.get("scheme", "") if ed else ""
        if ed and _is_logical(sch):
            served_logical += 1
            d = scheme_depth(sch)
            served_depths[d] = served_depths.get(d, 0) + 1
        elif ed and sch:
            served_physical.append(slug)
        else:
            served_none.append(slug)

    # cheapest Wikidata enrichment: work lacks a QID but its author has one.
    author_qid = {slug: a["aliases"]["wikidata"]
                  for slug, a in authors.items() if "wikidata" in a.get("aliases", {})}
    qid_via_author = []
    for slug, w in works.items():
        if "wikidata" not in w.get("aliases", {}) and w.get("author") in author_qid:
            qid_via_author.append({"work": slug, "author": w.get("author"),
                                   "author_wikidata": author_qid[w["author"]],
                                   "cts": w.get("aliases", {}).get("cts", "")})
    authors_no_wd = sorted(slug for slug, a in authors.items()
                           if "wikidata" not in a.get("aliases", {}))
    works_any_author_qid = sum(1 for w in work_list if w.get("author") in author_qid)

    report = {
        "headline": {
            "works": nW, "authors": nA, "editions": nE,
            "pct_works_with_canonical_locus": _pct(works_logical, nW),
            "pct_works_with_logical_served_locus": _pct(served_logical, nW),
            "pct_works_with_work_qid": _pct(nW - sum(1 for w in work_list
                                            if "wikidata" not in w.get("aliases", {})), nW),
            "pct_works_with_author_qid": _pct(works_any_author_qid, nW),
            "pct_authors_with_wikidata": _pct(len(author_qid), nA),
        },
        "work_aliases": _ns_coverage(work_list, WORK_NS),
        "author_aliases": _ns_coverage(author_list, AUTHOR_NS),
        "edition_aliases": _ns_coverage(editions, EDITION_NS),
        "canonical_locus": {
            "works_with_logical_locus": works_logical,
            "pct": _pct(works_logical, nW),
            "works_only_physical_or_none": len(works_only_physical),
            "by_scheme": dict(sorted(by_scheme.items(), key=lambda kv: (-kv[1], kv[0]))),
        },
        "served_canonical_locus": {
            "what": "logical locus of the default_edition (what cog renders bare "
                    "citations against): the Phase-2 'one canonical logical locus "
                    "per work' measure, stricter than any-edition canonical_locus",
            "works_with_logical_served_locus": served_logical,
            "pct": _pct(served_logical, nW),
            "served_logical_depth_distribution": dict(sorted(served_depths.items())),
            "default_edition_physical_only": {
                "what": "default edition cites only by page/volume; promote a logical locus",
                "count": len(served_physical),
                "examples": sorted(served_physical)[:CAP],
            },
            "no_default_or_scheme": {
                "count": len(served_none),
                "examples": sorted(served_none)[:CAP],
            },
            "editions_with_malformed_scheme": malformed_schemes,
        },
        "enrichment_targets": {
            "work_qid_via_author": {
                "what": "work has no Wikidata QID but its author does (cheapest to fill)",
                "count": len(qid_via_author),
                "examples": sorted(qid_via_author, key=lambda r: r["work"])[:CAP],
            },
            "authors_missing_wikidata": {
                "count": len(authors_no_wd),
                "examples": authors_no_wd[:CAP],
            },
            "works_without_canonical_locus": {
                "what": "work's editions cite only by page/volume; needs a logical locus",
                "count": len(works_only_physical),
                "examples": sorted(works_only_physical)[:CAP],
            },
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")

    h = report["headline"]
    print(f"crosswalk report -> {os.path.relpath(OUT_JSON, REPO)}", file=sys.stderr)
    print(f"  works {nW} | authors {nA} | editions {nE}", file=sys.stderr)
    print(f"  work aliases:   " + ", ".join(
        f"{ns} {report['work_aliases'][ns]['pct']}%" for ns in WORK_NS), file=sys.stderr)
    print(f"  author aliases: " + ", ".join(
        f"{ns} {report['author_aliases'][ns]['pct']}%" for ns in AUTHOR_NS), file=sys.stderr)
    print(f"  canonical locus: {h['pct_works_with_canonical_locus']}% any-edition | "
          f"{h['pct_works_with_logical_served_locus']}% served (default edition) | "
          f"work-QID {h['pct_works_with_work_qid']}% (author-QID {h['pct_works_with_author_qid']}%)",
          file=sys.stderr)
    print(f"  enrichment: {len(qid_via_author)} works fillable via author QID; "
          f"{len(authors_no_wd)} authors missing wikidata; "
          f"{len(works_only_physical)} works lack a logical locus", file=sys.stderr)


if __name__ == "__main__":
    main()
