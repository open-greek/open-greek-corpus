#!/usr/bin/env python3
"""Pin source-reviewed strips for particular failed Photius checkpoints."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_photius_coverage import ROOT, build, build_later_gap

CHECKPOINT38 = {"model": "Qwen/Qwen3.8-27B-FP8", "revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}
REVIEWS = {
    47: {"cut": .458, "top": .065, "bottom": .848,
         "evidence": "Printed page 35 begins codex 70, continues codex 71 from the left-column foot into the right-column top, then begins codex 72. The four crop boundaries retain complete authorial lines and stop above the smaller apparatus. The horizontal split at .458 lies in a blank interline gap in both columns.",
         "failure": "Qwen3.8 repeats Greek function words and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    50: {"cut": .456, "top": .062, "bottom": .835,
         "evidence": "Printed page 38 continues codex 72 in two columns. The four crops include every large Greek body line; the last right-column line ends with the opening of Xerxes' campaign against the Greeks. The horizontal split at .456 lies between complete lines; the lower boundary excludes the smaller apparatus.",
         "failure": "Qwen3.8 repeats καὶ and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build_retry(page):
    review = REVIEWS[page]
    original = build() if page <= 279 else build_later_gap()
    source_page = next(p for p in original["pages"] if p["scan_page"] == page)
    cut, top, bottom = review["cut"], review["top"], review["bottom"]
    strips = [("left-upper", [.045, top, .495, cut]),
              ("left-lower", [.045, cut, .495, bottom]),
              ("right-upper", [.505, top, .97, cut]),
              ("right-lower", [.505, cut, .97, bottom])]
    return {"schema_version": 1, "work": "photius.bibliotheca", "review_date": "2026-10-18",
            "purpose": "Replace only a failed checkpoint's whole-page attempt with a separately reviewed strip assembly; retain successful checkpoint readings and all failed originals.",
            "retry_of": {"path": "data/ocr_requests/photius-bekker-first-volume.json" if page <= 279 else "data/ocr_requests/photius-bekker-later-gap.json",
                         "sha256": hashlib.sha256(encode(original)).hexdigest(), "page_id": source_page["id"]},
            "checkpoints": review.get("checkpoints", [CHECKPOINT38]), "sources": original["sources"], "prompt": original["prompt"],
            "review": {"checked_scan_pages": [page], "accepted_for_primary_ingest": False,
                       "evidence": review["evidence"], "failure": review["failure"],
                       "admission_policy": "Only the listed checkpoint receives an assembled replacement vote after a completed output-to-scan review. Keep every original and retry prediction; no extra votes or arbitrary choice."},
            "pages": [{"id": source_page["id"] + "-" + name, "source": source_page["source"],
                       "scan_page": page, "printed_page": source_page["printed_page"], "region": region,
                       "max_side": 3600, "role": "reviewed-page-retry", "reading_order": order,
                       "prompt_suffix": "This crop contains one complete part of a single Greek body column. Read every complete line from left to right, then down. Preserve any codex heading; do not repeat words or complete text beyond the crop."}
                      for order, (name, region) in enumerate(strips)]}


def manifest_path(page):
    return Path(f"data/ocr_requests/photius-bekker-page{page:04d}-retry.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=int, action="append", choices=sorted(REVIEWS))
    args = parser.parse_args()
    for page in args.page or sorted(REVIEWS):
        path = ROOT / manifest_path(page)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(build_retry(page)))
        print(f"Pinned scan {page}: four strips, listed checkpoint only")
