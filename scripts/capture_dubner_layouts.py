#!/usr/bin/env python3
"""Capture or verify the two source pages behind each Dübner layout decision."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import dubner_layout_observations as observations

ROOT = observations.ROOT


def check(root=ROOT):
    return observations.build(root)


def capture(root, pdfs, reviewed_at=None):
    import pymupdf
    from dubner_witness_alignment import SOURCE_SCANS
    if pymupdf.VersionBind != "1.28.2":
        raise ValueError("Reproduce these captures with PyMuPDF 1.28.2")
    root = Path(root)
    review = root / observations.REVIEW
    if reviewed_at is None:
        reviewed_at = (json.loads(review.read_bytes())["reviewed_at"] if review.is_file()
                       else datetime.now(timezone.utc).isoformat())
    files, outputs = [], {}
    for scan, column in (("toronto", 0), ("harvard", 1)):
        pdf = Path(pdfs[scan])
        if observations.sha(pdf.read_bytes()) != SOURCE_SCANS[scan]["sha256"]:
            raise ValueError("Dübner layout PDF differs from its source pin: " + scan)
        with pymupdf.open(pdf) as document:
            if len(document) != SOURCE_SCANS[scan]["pages"]:
                raise ValueError("Dübner layout source page count changed")
            for page in sorted({pages[column] for pages in observations.PAGES.values()}):
                name = observations.image_path(scan, page)
                raw = document[page - 1].get_pixmap(matrix=pymupdf.Matrix(1.25, 1.25),
                    alpha=False).tobytes("png")
                outputs[name] = raw
                files.append({"path": name, "sha256": observations.sha(raw)})
    files.sort(key=lambda item: item["path"])
    data = observations.compile_review(root, files, reviewed_at)
    # All source validation and compilation finish before publishing any file.
    from repair_dubner_scholias import publish
    publish(root, {**outputs, observations.REVIEW: observations.encoded(data)})
    return check(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--toronto-pdf", type=Path)
    parser.add_argument("--harvard-pdf", type=Path)
    parser.add_argument("--reviewed-at")
    args = parser.parse_args()
    if args.check:
        result = check(args.root)
    else:
        if not args.toronto_pdf or not args.harvard_pdf:
            parser.error("--capture requires both pinned PDF paths")
        result = capture(args.root, {"toronto": args.toronto_pdf, "harvard": args.harvard_pdf}, args.reviewed_at)
    print(json.dumps({"source_pages": len(result["files"]),
        "approved_layouts": len(result["decisions"]), "held_layouts": len(result["held"])}))


if __name__ == "__main__":
    main()
