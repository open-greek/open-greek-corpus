#!/usr/bin/env python3
"""Reproduce reviewed early Dio body crops above retained editorial apparatus.

This is a second authority stage over the immutable late-body request. Existing
late predictions remain eligible; only changed early regions receive new crops.
All original panels, source credits and former predictions remain archived.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import json
from pathlib import Path

from prepare_dio_body_regions import ROOT, DIRECTORY, EFFECTIVE as BASE, encode, sha
from dio_early_body_review_evidence import OVERRIDES, CONTACTS, FULL_PAGE_IMAGES, FULL_PAGE_CHECKS, PROPOSALS_SHA256

EFFECTIVE = DIRECTORY / "cassius-dio-reviewed-ocr-jobs.json"
REVIEW = DIRECTORY / "cassius-dio-early-body-regions.json"
SHARDS = DIRECTORY / "cassius-dio-early-retry-shards"
DOCUMENTS = {}
REVIEW_DATE = "2026-10-18"


def proposal(task):
    import numpy as np
    import pymupdf
    page, path = task
    if path not in DOCUMENTS:
        DOCUMENTS[path] = pymupdf.open(path)
    source = DOCUMENTS[path][page["scan_page"] - 1]
    width, height = source.rect.width, source.rect.height
    region, lines = page["region"], []
    for block in source.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["bbox"][0] < width * .49
                and sum(c.isalpha() for c in s["text"]) >= 2
                and region[1] < (s["bbox"][1] + s["bbox"][3]) / 2 / height < region[3]]
            if not spans or sum(sum(c.isalpha() for c in s["text"]) for s in spans) < 4:
                continue
            font = float(np.median([s["size"] for s in spans for c in s["text"] if c.isalpha()]))
            lines.append({"y0": min(s["bbox"][1] / height for s in spans),
                "y1": max(s["bbox"][3] / height for s in spans), "font": font})
    groups = []
    for line in sorted(lines, key=lambda value: value["y0"]):
        if groups and line["y0"] - groups[-1]["y0"] < .006:
            groups[-1]["y1"] = max(groups[-1]["y1"], line["y1"])
            groups[-1]["font"] = max(groups[-1]["font"], line["font"])
        else:
            groups.append(dict(line))
    body = float(np.percentile([line["font"] for line in groups], 80)) if groups else 0
    candidates = [i for i, line in enumerate(groups) if line["font"] < body * .95
        and line["y0"] > region[1] + (region[3] - region[1]) * .3
        and not any(other["font"] >= body * .95 for other in groups[i:])]
    cut, method = region[3], "no-terminal-small-type"
    if candidates and min(candidates) > 0:
        index = min(candidates)
        left, right = groups[index - 1]["y1"], groups[index]["y0"]
        cut = round((left + right) / 2, 5) if left < right else round(right - .003, 5)
        method = "source-font-transition"
    return page["id"], (cut, method)


def build(pdf_dir, workers=8):
    base_raw = BASE.read_bytes()
    base, effective = json.loads(base_raw), json.loads(base_raw)
    early = [page for page in base["pages"] if page["source_volume"] in {1, 2}]
    if len(early) != 759 or any(page["panel_role"] != page["id"].split("-")[-1] for page in early):
        raise ValueError("Early source identity or panel role changed")
    paths = {}
    for page in early:
        key = page["source"]
        if key in paths:
            continue
        digest = base["sources"][key]["sha256"]
        options = [pdf_dir / (key + ".pdf"), pdf_dir / (digest + ".pdf")]
        path = next((p for p in options if p.exists()), options[0])
        if sha(path.read_bytes()) != digest:
            raise ValueError("Reviewed early Cary source changed")
        paths[key] = str(path)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        proposals = dict(pool.map(proposal, [(p, paths[p["source"]]) for p in early]))
    digest = sha(json.dumps(sorted([[key, value[0], value[1]] for key, value in proposals.items()]),
                            separators=(",", ":")).encode())
    if digest != PROPOSALS_SHA256:
        raise ValueError("Early font proposals differ from the completed source review")
    evidence, substitutions = {}, []
    for page in effective["pages"]:
        if page["source_volume"] not in {1, 2}:
            continue
        identifier = page["id"]
        cut, method = proposals[identifier]
        override = OVERRIDES.get(identifier)
        if override:
            cut, method = override["y1"], "source-reviewed-body-and-credit-boundary"
        old_region = list(page["region"])
        region = old_region[:3] + [cut]
        if not old_region[1] < cut <= old_region[3]:
            raise ValueError("Reviewed early body must stay inside its original panel")
        decision = {"id": identifier, "source": page["source"], "scan_page": page["scan_page"],
                    "original_region": old_region, "region": region}
        evidence_id = identifier.replace("dio-cary-", "dio-early-body-")
        record = dict(decision, source_pdf_sha256=base["sources"][page["source"]]["sha256"],
            contact_sheet_sha256=CONTACTS[identifier], reviewed_at=REVIEW_DATE,
            boundary_method=method, evidence=override["evidence"] if override else (
                "Source contact inspection verifies the entire original panel has no terminal apparatus to remove."
                if cut == old_region[3] else
                "Source contact inspection verifies the cut follows all main Greek paragraphs and attached transmission credits, before the first smaller editorial note. No note is promoted into primary or comparative reading text."))
        if identifier in FULL_PAGE_CHECKS:
            record["full_page_evidence"] = FULL_PAGE_CHECKS[identifier]
        if override:
            record["override_evidence"] = {key: value for key, value in override.items() if key not in {"evidence", "y1"}}
        evidence[evidence_id] = record
        if region != old_region:
            substitutions.append(dict(decision, evidence_id=evidence_id))
            page["region"] = region
    review = {"schema_version": 1, "kind": "scan-region-body-review", "reviewed_at": REVIEW_DATE,
        "generator": "scripts/prepare_dio_early_body_regions.py", "original_manifest_sha256": sha(base_raw),
        "method": "Every one of 759 early panels was source-reviewed. Font transitions are proposals only: numbered primary paragraphs, full comparative quotations and Latin transmission credits remain body; sparse/ambiguous panels received full-page checks. Only source-confirmed terminal apparatus is excluded by fresh paired crops.",
        "reviewed_early_regions": 759, "changed_early_regions": len(substitutions),
        "proposals_sha256": PROPOSALS_SHA256, "source_review_images": FULL_PAGE_IMAGES,
        "sources": {key: {"url": value["url"], "sha256": value["sha256"]} for key, value in base["sources"].items()},
        "evidence": evidence}
    effective["reviewed_substitutions"] = {"original_manifest_sha256": sha(base_raw),
        "source_review": {"path": REVIEW.relative_to(ROOT).as_posix(), "sha256": sha(encode(review))},
        "regions": substitutions}
    return effective, review


def shard_outputs(effective):
    ids = [entry["id"] for entry in effective["reviewed_substitutions"]["regions"]]
    middle = (len(ids) + 1) // 2
    return [ids[:middle], ids[middle:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    effective, review = build(args.pdf_dir, args.workers)
    outputs = [(EFFECTIVE, encode(effective)), (REVIEW, encode(review))]
    SHARDS.mkdir(parents=True, exist_ok=True)
    groups = shard_outputs(effective)
    outputs.append((SHARDS / "all.json", encode(groups[0] + groups[1])))
    for index, ids in enumerate(groups):
        outputs.append((SHARDS / f"shard-{index:02d}.json", encode(ids)))
    for path, raw in outputs:
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError("Early reviewed crop artifacts changed")
        else:
            path.write_bytes(raw)
    print(f"759 reviewed early panels; {review['changed_early_regions']} paired crop retries; late741 unchanged")


if __name__ == "__main__":
    main()
