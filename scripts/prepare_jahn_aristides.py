#!/usr/bin/env python3
"""Pin source-checked Greek body crops for Jahn's 1882 Aristides edition.

Use the first thin apparatus separator below the main Greek text; modern
editorial notes below it are outside the work. The final printed page's index
has its own reviewed boundary. Original scans remain unmodified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "8ccfbe7e5c43dd4210235296fae29d2b8ffdce2f910e50a80c822e7eee5539c6"
OUTPUT = ROOT / "data/ingest_reviews/jahn-aristides-fresh-witnesses.json"


def body_bottom(page):
    import numpy as np
    import pymupdf
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), colorspace=pymupdf.csGRAY)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
    image = image[:, int(pixmap.width * .1):int(pixmap.width * .89)]
    active = np.where((image < 150).sum(1) > 4)[0]
    groups = []
    for y in active:
        if groups and y - groups[-1][-1] <= 2:
            groups[-1].append(int(y))
        else:
            groups.append([int(y)])
    for group in groups:
        if not .45 * pixmap.height <= group[0] < .9 * pixmap.height or group[-1] - group[0] > 3:
            continue
        longest = max(len(run) for y in group for run in
            "".join("1" if pixel < 150 else "0" for pixel in image[y]).split("0"))
        if longest >= pixmap.width * .045:
            return round(group[0] / pixmap.height - .003, 4), "thin apparatus or section-ending rule"
    return .92, "complete Greek body; no apparatus separator found"


def prepare(pdf_path, output=OUTPUT):
    import pymupdf
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Jahn source PDF differs from the reviewed edition")
    doc = pymupdf.open(pdf_path)
    pages = []
    for scan in range(74, 171):
        printed = scan - 73
        bottom, evidence = body_bottom(doc[scan - 1])
        if scan == 170:
            bottom, evidence = .40, "Manual scan inspection: the Greek work ends above the rule; the separately headed INDEX below is excluded"
        pages.append({"id": f"jahn-1882-{scan:04d}-greek", "source": "jahn1882",
            "scan_page": scan, "printed_page": printed,
            "book": 1 if printed <= 37 else 2 if printed <= 67 else 3,
            "region": [.04, .04, .95, bottom], "max_side": 2600,
            "crop_evidence": evidence})
    manifest = {"schema_version": 1,
        "purpose": "Independent model witnesses for the complete Greek work in Jahn 1882, with modern editorial apparatus and final index excluded from primary text.",
        "sources": {"jahn1882": {"url": "https://archive.org/download/demusicanuncpri00quingoog/demusicanuncpri00quingoog.pdf",
            "sha256": SOURCE_SHA256, "license": "PD (Jahn 1882)",
            "citation": "Aristidis Quintiliani De musica libri III, edited by Albert Jahn (Berlin: Calvary, 1882)"}},
        "layout_evidence": {"checked_scan_pages": [74, 75, 76, 77, 91, 93, 97, 109, 110, 111, 140, 141, 169, 170],
            "evidence": "The Greek body occupies scan pages74-170, printed1-97; bookII begins printed38 and bookIII printed68. Clear nineteenth-century Greek type replaces the difficult Meibom ligatures. The apparatus separator is checked against the scan layout; page170 has the final Greek paragraph followed by a separately headed index. Meibom page numbers in the margins are edition concordance labels, not authorial Greek text."},
        "pages": pages}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    sanity = {**manifest, "purpose": "Four source-layout and OCR sanity pages before the full Jahn run",
        "pages": [page for page in pages if page["scan_page"] in [74, 111, 141, 170]]}
    output.with_name("jahn-aristides-sanity.json").write_text(json.dumps(sanity, ensure_ascii=False, indent=1) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUTPUT)
    args = ap.parse_args()
    manifest = prepare(args.pdf, args.out)
    print(f"Pinned {len(manifest['pages'])} Greek body pages")


if __name__ == "__main__":
    main()
