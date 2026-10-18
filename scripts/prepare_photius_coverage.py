#!/usr/bin/env python3
"""Prepare the checked missing Bekker pages for independent scan transcription."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ocr_requests/photius-bekker-first-volume.json"
LATER_OUT = ROOT / "data/ocr_requests/photius-bekker-later-gap.json"
SCAN = "https://archive.org/download/bibliothecaexrec00photuoft/bibliothecaexrec00photuoft.pdf"
SHA256 = "d7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6"
PROMPT = """Transcribe the large Greek authorial text of this scanned page exactly,
preserving its polytonic accents, breathings, punctuation, headings, and codex
numbers. Read a full-width paragraph before moving to two-column text; read
two-column text down the left column and then down the right column. Omit the
running page header, page number, marginal reference numbers, printer signatures,
and the smaller critical apparatus at the foot of the page. Keep the Greek
prefatory letter when present. Do not complete broken words, modernize spelling,
correct the printed text, translate, or add explanations. Output only the
transcription, with paragraph and column boundaries as blank lines."""


def build():
    # The first four pages form a small sanity check before the longer batch.
    order = [13, 33, 278, 279] + [n for n in range(13, 280) if n not in {13, 33, 278, 279}]
    return {
        "schema_version": 1, "work": "photius.bibliotheca", "review_date": "2026-10-18",
        "purpose": "Recover the prefatory letter and codices 1-229; scan 279 is an overlap check for codex 230, not additional primary text.",
        "review": {
            "checked_scan_pages": [13, 278, 279, 557, 558],
            "evidence": [
                "Scan 13 begins the Greek prefatory letter and codex 1, including a transition from full-width text to two columns.",
                "Scan 278 is printed page 266 and ends codex 229. Scan 279 is printed page 267 and begins codex 230 (Eulogius), matching the current served incipit.",
                "Scan 557 is printed page 545 and ends codex 280. Scan 558 starts the edition INDEX.",
                "Current OCR page 0002 matches combined scan 279; current page 0280 matches scan 557; current page 0281 begins index material. Preserve these old passage identities when moving index rows."
            ],
            "geometry": "Full page retained because scan 13 mixes a full-width prefatory letter with two-column authorial text. The prompt excludes the smaller apparatus; predictions remain raw witnesses pending source comparison and review.",
            "accepted_for_primary_ingest": False,
        },
        "sources": {"photius-bekker-combined": {
            "url": SCAN, "sha256": SHA256, "edition": "Bekker 1824-1825, combined volumes",
            "license": "public-domain", "pdf_pages": 600,
            "bibliographic_url": "https://archive.org/details/bibliothecaexrec00photuoft"}},
        "prompt": PROMPT,
        "pages": [{"id": f"photius-bekker-{n:04d}", "source": "photius-bekker-combined",
                   "scan_page": n, "printed_page": n - 12, "region": [0, 0, 1, 1],
                   "max_side": 2800, "role": "overlap-check" if n == 279 else "missing-primary-text"}
                  for n in order],
    }


def build_later_gap():
    manifest = build()
    order = [379, 421, 400] + [n for n in range(379, 422) if n not in {379, 421, 400}]
    manifest["purpose"] = "Recover the missing later-volume printed pages 367-409, absent from all current historical OCR rows."
    manifest["review"]["checked_scan_pages"] = [378, 379, 400, 421, 422]
    manifest["review"]["evidence"] = [
        "Historical OCR page keys 0102-0144 are absent from the served body, with no matching records elsewhere in the corpus.",
        "The checked combined scan maps those missing keys to scan pages 379-421, printed pages 367-409.",
        "Manual inspection of scan pages 379 and 421 confirms continuous authorial Greek text, not index or blank pages. Adjacent scan pages 378 and 422 retain the same body layout."
    ]
    manifest["pages"] = [{"id": f"photius-bekker-{n:04d}", "source": "photius-bekker-combined",
                          "scan_page": n, "printed_page": n - 12, "region": [0, 0, 1, 1],
                          "max_side": 2800, "role": "missing-primary-text"} for n in order]
    return manifest


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
    LATER_OUT.write_text(json.dumps(build_later_gap(), ensure_ascii=False, indent=2) + "\n")
    print(f"Prepared {len(build()['pages'])} first-volume and {len(build_later_gap()['pages'])} later-gap scan pages; run a small sanity check first.")
