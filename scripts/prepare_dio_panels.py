#!/usr/bin/env python3
"""Separate Cary's Dio fragment panels from comparative quotations.

The full-width rule separates the fragment stream above from comparative
quotations below. A short apparatus rule is not a panel boundary. Pages filled
entirely by comparisons have an explicit source heading. Original scans and
the rule coordinates remain hash-pinned evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/ingest_reviews/coverage"
REVIEW = DIRECTORY / "cassius-dio-missing-material.json"
LAYOUT = DIRECTORY / "cassius-dio-early-panels.json"
COMPARISON = re.compile(r"Zo[nm]|Tzetz|Labb|Ioan|Joan|Eustath|Euseb|Syncel|Malal|Cedren|Suid|Suda|Photi", re.I)


def full_rules(page):
    """Find straight separators longer than 43% of a Greek half-sheet."""
    import numpy as np
    import pymupdf
    from scipy.ndimage import maximum_filter1d
    rect = page.rect
    pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), colorspace=pymupdf.csGRAY,
                         clip=pymupdf.Rect(0, 0, rect.width / 2, rect.height))
    raster = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    dark = maximum_filter1d(raster < 150, size=3, axis=0)
    length = int(.43 * pix.width)
    zeros = np.pad(np.cumsum(~dark, axis=1), ((0, 0), (1, 0)))
    # Faint scanned rules contain tiny white gaps. Printed words still leave
    # much larger spaces, so a two-percent tolerance does not turn a text line
    # into a separator. This also recovers the checked volume I pages 50/181.
    runs = (zeros[:, length:] - zeros[:, :-length] <= .02 * length).any(axis=1)
    indexes = np.flatnonzero(runs)
    indexes = indexes[(indexes > .13 * pix.height) & (indexes < .93 * pix.height)]
    if not len(indexes):
        return []
    groups = np.split(indexes, np.where(np.diff(indexes) > 4)[0] + 1)
    return [round(float(np.mean(group)) / pix.height, 4) for group in groups]


def text_lines(page):
    import pymupdf
    rect = page.rect
    lines = []
    for block in page.get_text("dict", clip=pymupdf.Rect(0, 0, rect.width / 2, rect.height))["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            y = line["bbox"][1] / rect.height
            if y > .065 and text:
                lines.append({"y": round(y, 4), "text": text})
    return lines


def prepare(pdf_dir):
    import pymupdf
    review = json.loads(REVIEW.read_text())
    result = []
    for volume in review["volumes"]:
        if volume["volume"] not in {1, 2}:
            continue
        source = review["sources"][volume["source"]]
        candidates = [pdf_dir / (volume["source"] + ".pdf"), pdf_dir / (source["sha256"] + ".pdf")]
        path = next((p for p in candidates if p.exists()), candidates[0])
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("The scanned edition changed before panel routing")
        document = pymupdf.open(path)
        for number in range(volume["first_pdf_page"], volume["last_pdf_page"] + 1):
            page = document[number - 1]
            rules, lines = full_rules(page), text_lines(page)
            heading = " ".join(line["text"] for line in lines[:3])
            if len(rules) > 1:
                raise ValueError(f"Review multiple full rules: volume {volume['volume']} PDF {number}")
            kind = "split" if rules else "comparison" if COMPARISON.search(heading) else "fragment"
            result.append({"source_volume": volume["volume"], "source": volume["source"],
                "scan_page": number, "kind": kind, "full_rules": rules,
                "source_heading_text_layer": heading,
                "panels": ([
                    {"role": "fragment", "region": [0, .065, .5, round(rules[0] - .003, 4)]},
                    {"role": "comparison", "region": [0, round(rules[0] + .003, 4), .5, .94]},
                ] if rules else [{"role": kind, "region": [0, .065, .5, .94]}])})
        document.close()
    return {"schema_version": 1, "generated_by": "scripts/prepare_dio_panels.py",
        "review_sha256": hashlib.sha256(REVIEW.read_bytes()).hexdigest(),
        "policy": "Full rules separate Dio's fragment stream from comparative quotations; short apparatus rules do not. Explicit comparison headings identify full comparison pages. All original scans and heading evidence remain pinned.",
        "pages": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=LAYOUT)
    args = parser.parse_args()
    result = prepare(args.pdf_dir)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(result['pages'])} physical pages; {sum(len(p['panels']) for p in result['pages'])} separately routed panels")


if __name__ == "__main__":
    main()
