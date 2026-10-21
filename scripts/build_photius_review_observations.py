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
    "photius_complete_observations_page0017",
    "photius_complete_observations_page0018",
    "photius_complete_observations_page0019",
    "photius_complete_observations_page0020",
    "photius_complete_observations_page0021",
    "photius_complete_observations_page0022",
    "photius_complete_observations_page0023",
    "photius_complete_observations_page0024",
    "photius_complete_observations_page0025",
    "photius_complete_observations_page0026",
    "photius_complete_observations_page0027",
    "photius_complete_observations_page0028",
    "photius_complete_observations_page0029",
    "photius_complete_observations_page0030",
    "photius_complete_observations_page0031",
    "photius_complete_observations_page0032",
    "photius_complete_observations_page0033",
    "photius_complete_observations_page0034",
    "photius_complete_observations_page0035",
    "photius_complete_observations_page0036",
    "photius_complete_observations_page0037",
    "photius_complete_observations_page0038",
    "photius_complete_observations_page0039",
    "photius_complete_observations_page0040",
    "photius_complete_observations_page0041",
    "photius_complete_observations_page0042",
    "photius_complete_observations_page0043",
    "photius_complete_observations_page0044",
    "photius_complete_observations_page0045",
    "photius_complete_observations_page0046",
    "photius_complete_observations_page0047",
    "photius_complete_observations_page0048",
    "photius_complete_observations_page0049",
    "photius_complete_observations_page0050",
    "photius_complete_observations_page0051",
    "photius_complete_observations_page0052",
    "photius_complete_observations_page0053",
    "photius_complete_observations_page0054",
    "photius_complete_observations_page0055",
    "photius_complete_observations_page0056",
    "photius_complete_observations_page0057",
    "photius_complete_observations_page0058",
    "photius_complete_observations_page0059",
    "photius_complete_observations_page0060",
    "photius_complete_observations_page0061",
    "photius_complete_observations_page0062",
    "photius_complete_observations_page0063",
    "photius_complete_observations_page0064",
    "photius_complete_observations_page0065",
    "photius_complete_observations_page0066",
    "photius_complete_observations_page0067",
    "photius_complete_observations_page0068",
    "photius_complete_observations_page0069",
    "photius_complete_observations_page0070",
    "photius_complete_observations_page0071",
    "photius_complete_observations_page0072",
    "photius_complete_observations_page0073",
    "photius_complete_observations_page0074",
    "photius_complete_observations_page0075",
    "photius_complete_observations_page0076",
    "photius_complete_observations_page0077",
    "photius_complete_observations_page0078",
    "photius_complete_observations_page0079",
    "photius_complete_observations_page0080",
    "photius_complete_observations_page0081",
    "photius_complete_observations_page0082",
    "photius_complete_observations_page0083",
    "photius_complete_observations_page0084",
    "photius_complete_observations_page0085",
    "photius_complete_observations_page0086",
    "photius_complete_observations_page0087",
    "photius_complete_observations_page0088",
    "photius_complete_observations_page0089",
    "photius_complete_observations_page0090",
    "photius_complete_observations_page0091",
    "photius_complete_observations_page0092",
    "photius_complete_observations_page0093",
    "photius_complete_observations_page0094",
    "photius_complete_observations_page0095",
    "photius_complete_observations_page0096",
    "photius_complete_observations_page0097",
    "photius_complete_observations_page0098",
    "photius_complete_observations_page0099",
    "photius_complete_observations_page0100",
    "photius_complete_observations_page0101",
    "photius_complete_observations_pages0145_0149",
    "photius_complete_observations_page0150",
    "photius_complete_observations_page0151",
    "photius_complete_observations_page0152",
    "photius_complete_observations_page0153",
    "photius_complete_observations_page0154",
    "photius_complete_observations_page0155",
    "photius_complete_observations_page0156",
    "photius_complete_observations_page0157",
    "photius_complete_observations_page0158",
    "photius_complete_observations_page0159",
    "photius_complete_observations_page0160",
    "photius_complete_observations_page0161",
    "photius_complete_observations_page0162",
    "photius_complete_observations_page0163",
    "photius_complete_observations_page0164",
    "photius_complete_observations_page0165",
    "photius_complete_observations_page0166",
    "photius_complete_observations_page0167",
    "photius_complete_observations_page0168",
    "photius_complete_observations_page0169",
    "photius_complete_observations_page0170",
    "photius_complete_observations_page0171",
    "photius_complete_observations_page0172",
    "photius_complete_observations_page0173",
    "photius_complete_observations_page0174",
    "photius_complete_observations_page0175",
    "photius_complete_observations_page0176",
    "photius_complete_observations_page0177",
    "photius_complete_observations_page0178",
    "photius_complete_observations_page0179",
    "photius_complete_observations_page0180",
    "photius_complete_observations_page0181",
    "photius_complete_observations_page0182",
    "photius_complete_observations_page0183",
    "photius_complete_observations_page0184",
    "photius_complete_observations_page0185",
    "photius_complete_observations_page0186",
    "photius_complete_observations_page0187",
    "photius_complete_observations_page0188",
    "photius_complete_observations_page0189",
    "photius_complete_observations_page0190",
    "photius_complete_observations_page0191",
    "photius_complete_observations_page0192",
    "photius_complete_observations_page0193",
    "photius_complete_observations_page0194",
    "photius_complete_observations_page0195",
    "photius_complete_observations_page0196",
    "photius_complete_observations_page0197",
    "photius_complete_observations_page0198",
    "photius_complete_observations_page0199",
    "photius_complete_observations_page0200",
    "photius_complete_observations_page0201",
    "photius_complete_observations_page0202",
    "photius_complete_observations_page0203",
    "photius_complete_observations_page0204",
    "photius_complete_observations_page0205",
    "photius_complete_observations_page0206",
    "photius_complete_observations_page0207",
    "photius_complete_observations_page0208",
    "photius_complete_observations_page0209",
    "photius_complete_observations_page0210",
    "photius_complete_observations_page0211",
    "photius_complete_observations_page0212",
    "photius_complete_observations_page0213",
    "photius_complete_observations_page0214",
    "photius_complete_observations_page0215",
    "photius_complete_observations_page0216",
    "photius_complete_observations_page0217",
    "photius_complete_observations_page0218",
    "photius_complete_observations_page0219",
    "photius_complete_observations_page0220",
    "photius_complete_observations_page0221",
    "photius_complete_observations_page0222",
    "photius_complete_observations_page0223",
    "photius_complete_observations_page0224",
    "photius_complete_observations_page0225",
    "photius_complete_observations_page0226",
    "photius_complete_observations_page0227",
    "photius_complete_observations_page0228",
    "photius_complete_observations_page0229",
    "photius_complete_observations_page0230",
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
    "photius_complete_observations_page0241",
    "photius_complete_observations_page0242",
    "photius_complete_observations_page0243",
    "photius_complete_observations_page0244",
    "photius_complete_observations_page0245",
    "photius_complete_observations_page0246",
    "photius_complete_observations_page0247",
    "photius_complete_observations_page0248",
    "photius_complete_observations_page0249",
    "photius_complete_observations_page0250",
    "photius_complete_observations_page0251",
    "photius_complete_observations_page0252",
    "photius_complete_observations_page0253",
    "photius_complete_observations_page0254",
    "photius_complete_observations_page0255",
    "photius_complete_observations_page0256",
    "photius_complete_observations_page0257",
    "photius_complete_observations_page0258",
    "photius_complete_observations_page0259",
    "photius_complete_observations_page0260",
    "photius_complete_observations_page0261",
    "photius_complete_observations_page0262",
    "photius_complete_observations_page0263",
    "photius_complete_observations_page0264",
    "photius_complete_observations_page0265",
    "photius_complete_observations_page0266",
    "photius_complete_observations_page0267",
    "photius_complete_observations_page0268",
    "photius_complete_observations_page0269",
    "photius_complete_observations_page0270",
    "photius_complete_observations_page0271",
    "photius_complete_observations_page0272",
    "photius_complete_observations_page0273",
    "photius_complete_observations_page0274",
    "photius_complete_observations_page0275",
    "photius_complete_observations_page0276",
    "photius_complete_observations_page0277",
    "photius_complete_observations_page0278",
    "photius_complete_observations_page0279",
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
