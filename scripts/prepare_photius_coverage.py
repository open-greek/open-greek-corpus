#!/usr/bin/env python3
"""Prepare the checked missing Bekker pages for independent scan transcription."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ocr_requests/photius-bekker-first-volume.json"
LATER_OUT = ROOT / "data/ocr_requests/photius-bekker-later-gap.json"
RETRY_OUT = ROOT / "data/ocr_requests/photius-bekker-page13-retry.json"
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


def build_page13_retry():
    """Pin complete source lines after the first model loops on lacuna dots."""
    original = build()
    original_sha = hashlib.sha256((json.dumps(original, ensure_ascii=False, indent=2) + "\n").encode()).hexdigest()
    strips = [
        ("upper-preface", [.04, .05, .985, .441], "The heading and the opening full-width prefatory letter. Read complete lines from left to right."),
        ("lacuna", [.04, .441, .985, .493], "Exactly three full-width printed lines containing dotted lacunae. Represent each separate printed series of omission dots with one ellipsis character (…). Do not expand a dot series or infer missing words."),
        ("lower-preface", [.04, .493, .985, .678], "The continuation and end of the full-width Greek prefatory letter. Read complete lines from left to right."),
        ("codex1-left", [.04, .681, .486, .804], "Only the left column of codex 1, including its printed codex number. Read down this column."),
        ("codex1-right", [.49, .681, .985, .804], "Only the right column continuing codex 1. Read down this column."),
    ]
    return {
        "schema_version": 1, "work": "photius.bibliotheca", "review_date": "2026-10-18",
        "purpose": "Retry the degenerate whole-page transcription of the prefatory letter and codex 1 as enlarged, source-reviewed strips; never add another model vote.",
        "retry_of": {"path": "data/ocr_requests/photius-bekker-first-volume.json", "sha256": original_sha,
                     "page_id": "photius-bekker-0013"},
        "sources": original["sources"], "prompt": PROMPT,
        "review": {
            "checked_scan_pages": [13], "accepted_for_primary_ingest": False,
            "evidence": "Manual inspection of the pinned scan at enlarged resolution: heading and opening letter precede three lines with printed dotted lacunae; the full-width letter ends before codex 1 begins in two columns. Every authorial line is included once. Vertical boundaries fall between complete lines; the codex crops end above the smaller critical apparatus.",
            "failure": "The first Qwen3.6 whole-page attempt loops on omission dots and terminates at its token limit before the rest of the letter and codex 1.",
            "reading_order": [name for name, _, _ in strips],
            "display_convention": "One ellipsis character represents each printed dotted lacuna in the reviewed lacuna strip; no missing Greek is supplied.",
            "admission_policy": "Retain every original whole-page attempt and raw retry strip. A separate completed source review must pin exact accepted predictions. Assemble one vote per original model family, with no extra vote for a retry or strip.",
        },
        "pages": [{"id": "photius-bekker-0013-" + name, "source": "photius-bekker-combined",
                   "scan_page": 13, "printed_page": 1, "region": region,
                   "max_side": 3600, "role": "reviewed-page-retry", "reading_order": order,
                   "prompt_suffix": suffix}
                  for order, (name, region, suffix) in enumerate(strips)],
    }


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
    LATER_OUT.write_text(json.dumps(build_later_gap(), ensure_ascii=False, indent=2) + "\n")
    RETRY_OUT.write_text(json.dumps(build_page13_retry(), ensure_ascii=False, indent=2) + "\n")
    print(f"Prepared {len(build()['pages'])} first-volume and {len(build_later_gap()['pages'])} later-gap scan pages; run a small sanity check first.")
