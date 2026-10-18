#!/usr/bin/env python3
"""Expand reviewed Pappus/Apollonius scan selections for run_scan_ocr.py.

The first pages form a small boundary/layout sanity set. This manifest retains
full page images; the OCR prompt must omit small apparatus, headers, marginal
line numbers and diagrams before any prediction becomes candidate reading text.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "data/ingest_reviews/coverage"
OUTPUT = REVIEWS / "mathematical-ocr-jobs.json"
LETTER_OUTPUT = REVIEWS / "apollonius-conica-4-letter-jobs.json"
PROMPT = (
    "Transcribe only the main Greek reading text in the image, one line per printed line. "
    "Keep Greek book headings, epistolary prefaces, proposition labels and editorial brackets. "
    "Exclude running headers, page numbers, marginal line numbers, diagrams and diagram labels. "
    "Exclude ALL small critical apparatus beneath the horizontal rule, even when it is Greek. "
    "Exclude facing Latin translation and Latin words. Preserve accents, breathing marks, "
    "punctuation and printed hyphens. Do not correct, expand, translate, summarize or explain. "
    "Return only the transcription."
)


def build():
    sources, pages, sanity, inputs = {}, [], [], {}
    for filename in ("apollonius-conica-1-3.json", "pappus-6-7.json", "pappus-8.json"):
        path = REVIEWS / filename
        raw = path.read_bytes()
        inputs[filename] = hashlib.sha256(raw).hexdigest()
        review = json.loads(raw)
        candidates = review.get("pages")
        if candidates is None:
            source = review["source"]
            key = source["id"]
            review["sources"] = {key: source}
            candidates = [{"source": key, "pdf_page": page, "printed_page": page - 18,
                           "book": next(b["book"] for b in review["books"]
                               if b["first_pdf_page"] <= page <= b["last_pdf_page"])}
                          for page in review["greek_pages"]]
            sanity_keys = {(key, page) for page in review["sanity_pdf_pages"]}
        else:
            sanity_keys = {(p["source"], p["pdf_page"]) for p in review["sanity_pages"]}
        for key, source in review["sources"].items():
            sources[key] = {"url": source["pdf_url"], "sha256": source["pdf_sha256"],
                            "license": "public-domain", "citation": review.get("edition", source.get("edition")),
                            "rights_evidence": review.get("rights", source.get("rights")),
                            "catalog_url": source["url"]}
        for selected in candidates:
            key = selected["source"]
            row = {"id": f"{key}-pdf{selected['pdf_page']:04d}", "source": key,
                   "scan_page": selected["pdf_page"], "region": [0, 0, 1, 1],
                   "max_side": 2200, "work": review["work"], "book": selected["book"],
                   "printed_page": selected["printed_page"]}
            if selected.get("transmission"):
                row["transmission"] = selected["transmission"]
            (sanity if (key, selected["pdf_page"]) in sanity_keys else pages).append(row)
    result = {"schema_version": 1, "generated_by": "scripts/prepare_mathematical_ocr.py",
              "review_sha256": inputs, "sources": sources, "prompt": PROMPT,
              "sanity_pages": len(sanity), "pages": sanity + pages,
              "status": "OCR input; not served reading text",
              "admission": "Retain each model's raw predictions separately. Check sanity pages against the scan before a full run. Collate independent witnesses; preserve disagreements. Validate exclusion of apparatus and figures before serving."}
    if len({p["id"] for p in result["pages"]}) != len(result["pages"]):
        raise ValueError("A scan image has been selected twice")
    return result


def build_book4_letter():
    """The current Book IV TEI begins at proposition 1, after this letter."""
    key = "apolloniipergaei02apoluoft"
    return {"schema_version": 1, "generated_by": "scripts/prepare_mathematical_ocr.py --book4-letter",
        "sources": {key: {"url": f"https://archive.org/download/{key}/{key}.pdf",
            "sha256": "ab8f0c2dd0f4a13f16ba7415e66f571161c08a5004477b0305a6d2016779a9c0",
            "license": "public-domain", "citation": "Apollonius, Conica, edited by J. L. Heiberg, volume II, Leipzig: Teubner, 1893",
            "catalog_url": "https://archive.org/details/" + key,
            "rights_evidence": "Public-domain Greek print, 1893; volume title and Book IV opening inspected."}},
        "prompt": PROMPT, "sanity_pages": 2,
        "pages": [{"id": f"{key}-pdf{page:04d}-letter", "source": key, "scan_page": page,
            "region": region, "max_side": 2200, "work": "apollonius-geom.conica", "book": "4",
            "printed_page": printed, "text_role": "authorial-preface"}
            for page, printed, region in [(94, 2, [0, 0.17, 1, 0.825]),
                                           (96, 4, [0, 0.07, 1, 0.659])]],
        "boundary_review": {"date": "2026-10-18", "method": "Manual inspection of both cropped Greek leaves at enlarged resolution",
            "evidence": "PDF94 contains the opening Ἀπολλώνιος Ἀττάλῳ χαίρειν and ends with ὁμο-. PDF96 continues γενῆ and the letter ends δεχόμεθα. The crop ends at normalized y=0.659, in the blank space before proposition label α′, whose text is already served at 4.1. PDF94 stops above the short apparatus rule. No proposition text is selected.",
            "tei_source_sha256": "6d6d5bb17dea43ec238e777fb413af56137e49dcd76e8e02dbc515ae0a5db0eb",
            "analogous_openings": "Books I–III use all consecutive Greek leaves of Heiberg volume I (PDF20–208,210–334,336–468, step2). Their book-opening letters and continuation leaves are included in full, with no gap at a preface/proposition transition. Book IV propositions1–57 already include the closing continuation on printed96 (PDF188)."},
        "status": "Reviewed authorial preface supplement; queued 556-region jobs remain unchanged"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--book4-letter", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_book4_letter() if args.book4_letter else build()
    output = args.out or (LETTER_OUTPUT if args.book4_letter else OUTPUT)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    if args.check:
        if output.read_bytes() != raw:
            raise SystemExit("Mathematical OCR jobs differ from reviewed selections")
    else:
        output.write_bytes(raw)
    print(f"{len(result['pages'])} Greek pages, {result['sanity_pages']} sanity pages first")


if __name__ == "__main__":
    main()
