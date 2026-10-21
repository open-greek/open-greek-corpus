#!/usr/bin/env python3
"""Reproduce authored complete-passage scan observations and their accounting.

Only the explicitly enumerated observations in the pinned source tables count
as review. Unlisted passages remain unreviewed; digital alignment never supplies
an implicit observation. This command does not change the corpus.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys
from types import ModuleType

import prepare_photius_review_campaign as campaign

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ("photius_complete_review_table",)
TABLES = (
    "photius_complete_observations_boundaries",
    "photius_complete_observations_page0003",
    "photius_complete_observations_page0004",
    "photius_complete_observations_page0005",
    "photius_complete_observations_page0006",
    "photius_complete_observations_page0007",
    "photius_complete_observations_page0008",
    "photius_complete_observations_page0009",
    "photius_complete_observations_page0010",
    "photius_complete_observations_page0011",
    "photius_complete_observations_page0012",
    "photius_complete_observations_page0013",
    "photius_complete_observations_page0014",
    "photius_complete_observations_page0015",
    "photius_complete_observations_page0016",
    "photius_complete_observations_page0060",
    "photius_complete_observations_page0061",
    "photius_complete_observations_page0062",
    "photius_complete_observations_page0063",
    "photius_complete_observations_pages0145_0149",
    "photius_complete_observations_page0150",
    "photius_complete_observations_page0151",
    "photius_complete_observations_page0152",
    "photius_complete_observations_page0153",
    "photius_complete_observations_page0154",
    "photius_complete_observations_page0155",
    "photius_complete_observations_page0231",
    "photius_complete_observations_page0232",
    "photius_complete_observations_page0233",
    "photius_complete_observations_page0234",
    "photius_complete_observations_page0235",
    "photius_complete_observations_page0236",
    "photius_complete_observations_page0237",
    "photius_complete_observations_page0238",
    "photius_complete_observations_page0239",
    "photius_complete_observations_page0240",
)


def build(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / campaign.MANIFEST).read_bytes())
    # The campaign preimage remains immutable after subsequent corpus repairs.
    frozen = root / campaign.BASELINE
    frozen_raw = frozen.read_bytes()
    before = gzip.decompress(frozen_raw)
    scan, library, original, coverage = (
        (root / path).read_bytes() for path in
        (campaign.SCAN, campaign.LIBRARY, campaign.ORIGINAL, campaign.COVERAGE)
    )
    campaign.validate_scope(manifest, before, scan, library, original, coverage,
                            frozen_corpus_raw=frozen_raw)
    rows = {row["locus"]: row for row in map(json.loads, before.splitlines())}
    sections = {section["id"]: "\n".join(block["text"] for block in section["blocks"])
                for section in json.loads(gzip.decompress(library))["sections"]}
    import pymupdf
    observations, pins, evidence = [], [], {}
    with pymupdf.open(stream=scan, filetype="pdf") as document:
        for name in (*HELPERS, *TABLES):
            path = Path("scripts") / (name + ".py")
            raw = (root / path).read_bytes()
            table = ModuleType(name)
            exec(compile(raw, path.as_posix(), "exec"), table.__dict__)
            # Later tables import shared functions from these exact pinned
            # bytes, rather than an earlier import or a cached Python module.
            sys.modules[name] = table
            if name in TABLES:
                observations.extend(table.records(rows, document, campaign.crop_png, sections))
            pins.append({"path": path.as_posix(), "sha256": campaign.sha(raw)})
            evidence[path.as_posix()] = raw
    reviews = {"schema": campaign.REVIEW_SCHEMA, "campaign_id": manifest["campaign_id"],
               "source_tables": pins, "records": observations}
    compiled = campaign.compile_campaign(manifest, reviews, before, scan, library,
                                         original, coverage, evidence_files=evidence,
                                         frozen_corpus_raw=frozen_raw)
    review_raw = campaign.artifact_bytes(campaign.REVIEWS, reviews)
    compiled_raw = campaign.artifact_bytes(campaign.OUT, compiled)
    summary = {key: value for key, value in compiled.items() if key != "rows"}
    summary["compiled_records"] = {"path": campaign.OUT.as_posix(), "sha256": campaign.sha(compiled_raw)}
    summary["authored_observations"] = {"path": campaign.REVIEWS.as_posix(), "sha256": campaign.sha(review_raw)}
    return {campaign.REVIEWS: review_raw, campaign.OUT: compiled_raw,
            campaign.SUMMARY: campaign.encode(summary)}, compiled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--require-complete-scope", action="store_true",
                        help="Fail unless every frozen passage has a complete direct scan review")
    args = parser.parse_args()
    outputs, result = build()
    if args.require_complete_scope and not result["scope_complete"]:
        raise SystemExit("The frozen Photius source-review scope is not complete")
    for path, raw in outputs.items():
        if args.write:
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(raw)
        elif args.check and (ROOT / path).read_bytes() != raw:
            raise SystemExit(f"Authored complete-passage observations do not reproduce: {path}")
    print(json.dumps({"scope_complete": result["scope_complete"], "counts": result["counts"]}))


if __name__ == "__main__":
    main()
