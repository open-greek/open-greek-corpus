#!/usr/bin/env python3
"""Retain hash-pinned Greek panels for missing Dio transmitted material.

This prepares independent raw witnesses. Earlier fragments and their Zonaras
comparison panels require separate routing before admission, and the first
volume VI page must be collated against the existing paragraph prefix.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/ingest_reviews/coverage"
REVIEW = DIRECTORY / "cassius-dio-missing-material.json"
OUTPUT = DIRECTORY / "cassius-dio-ocr-jobs.json"
PROMPT = (
    "Transcribe the main Greek reading text in the image, in reading order, one line per printed line. "
    "Keep book headings, section numbers, summaries, and source attribution headings and credits "
    "such as Zonaras, Xiph., Suid., and Tzetzes, including their reference numbers. "
    "When a full-width horizontal rule separates a large lower Zonaras comparison panel from "
    "an upper Dio fragment panel, preserve BOTH panels and their attribution heading. "
    "Exclude the small critical apparatus beneath its SHORT horizontal rule, even if it is Greek. "
    "Exclude running headers, page numbers and English translation. "
    "Preserve accents, breathing marks, punctuation, editorial brackets and printed hyphens. "
    "Do not correct, expand, translate, summarize or explain. Return only the transcription."
)


def build():
    raw = REVIEW.read_bytes()
    review = json.loads(raw)
    sanity = {(p["volume"], p["pdf_page"]) for p in review["sanity_pages"]}
    first, rest = [], []
    for volume in review["volumes"]:
        for number in range(volume["first_pdf_page"], volume["last_pdf_page"] + 1):
            row = {"id": f"dio-cary-v{volume['volume']}-pdf{number:04d}",
                   "source": volume["source"], "scan_page": number,
                   "region": volume["reading_region"], "max_side": 2200,
                   "work": review["work"], "source_volume": volume["volume"],
                   "transmission": volume["transmission"], "admission": volume["admission"]}
            if volume["volume"] == 6 and number == 206:
                row["overlap"] = {"served_through": "55.9.4",
                    "existing_final_words": "βουληθεὶς δὲ δὴ τρόπον",
                    "action": "collate shared prefix before admitting missing continuation"}
            (first if (volume["volume"], number) in sanity else rest).append(row)
    return {"schema_version": 1, "generated_by": "scripts/prepare_dio_ocr.py",
            "review_sha256": hashlib.sha256(raw).hexdigest(),
            "sources": review["sources"], "prompt": PROMPT,
            "sanity_pages": len(first), "pages": first + rest,
            "status": review["status"], "panel_routing": review["panel_routing"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document = build()
    raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()
    if args.check:
        if args.out.read_bytes() != raw:
            raise SystemExit("Dio OCR jobs differ from reviewed source selection")
    else:
        args.out.write_bytes(raw)
    print(f"{len(document['pages'])} Greek panels; {document['sanity_pages']} sanity pages first")


if __name__ == "__main__":
    main()
