#!/usr/bin/env python3
"""Prepare hash-pinned Herodas body crops; this command admits no corpus text."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from herodas_source_observations import SOURCE_SHA256, SOURCE

PROMPT = (
    "Transcribe the printed ancient Greek verse in this image, one line per printed "
    "line. Preserve accents, breathing marks, punctuation, incomplete words, dots, "
    "and all printed critical brackets and supplies exactly. Include separately "
    "printed speaker names on their own lines. Exclude Arabic verse numbers and "
    "small marginal reference letters. Do not correct, restore, modernize, translate, "
    "or add explanations. Return only the transcription."
)
PILOT = [
    {"scan_page": 76, "region": [0.20, 0.082, 0.90, 0.790]},
    {"scan_page": 78, "region": [0.20, 0.082, 0.90, 0.545]},
]


def build_manifest(pages):
    if not pages or len({page["scan_page"] for page in pages}) != len(pages):
        raise ValueError("Herodas body pages must be nonempty and unique")
    result = []
    for page in pages:
        number, region = page["scan_page"], page.get("ocr_region", page["region"])
        if (type(number) is not int or not 1 <= number <= SOURCE["pdf_pages"]
                or len(region) != 4
                or not 0 <= region[0] < region[2] <= 1
                or not 0 <= region[1] < region[3] <= 1):
            raise ValueError("Invalid reviewed Herodas page or body crop")
        result.append({"id": f"herodas-hk-body-{number:04d}", "source": "herodas-headlam-knox",
            "scan_page": number, "region": region, "max_side": 1800})
    return {"schema_version": 1, "purpose": "Herodas body recovery witness; no automatic admission",
        "prompt": PROMPT,
        "sources": {"herodas-headlam-knox": {"url": SOURCE["download_url"],
            "sha256": SOURCE_SHA256, "title": SOURCE["title"], "year": SOURCE["year"],
            "license": "PD"}}, "pages": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--missing-only", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.pilot:
        pages = PILOT
    else:
        from herodas_body_source_observations import BODY_PAGES
        pages = BODY_PAGES
    if args.missing_only:
        raw = (args.root / "data/corpus/herodas.mimiambi.jsonl").read_bytes()
        if hashlib.sha256(raw).hexdigest() != "b50c5d810cac0a8a44a2acdd567aa1c7f7e7266e83698325122501b0656e68ef":
            raise ValueError("Missing-page request needs the exact published Herodas excerpt")
        present = {int(re.fullmatch(r"herodas_hk_([0-9]{4})\.[0-9]+", json.loads(line)["locus"])[1])
                   for line in raw.splitlines() if line.strip()}
        pages = [page for page in pages if page["scan_page"] not in present]
    raw = (json.dumps(build_manifest(pages), ensure_ascii=False, indent=2) + "\n").encode()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists() and args.out.read_bytes() != raw:
        raise ValueError("Refusing to replace a different OCR request")
    args.out.write_bytes(raw)


if __name__ == "__main__":
    main()
