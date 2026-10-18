#!/usr/bin/env python3
"""Prepare exact source/row worksheets for occurrence-level apparatus review.

Rendering and candidate signals never classify or remove text. A completed
authority must contain a scan review for every historical page and exact
Unicode offsets for each separately confirmed apparatus span.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re

from repair_photius_index import ROOT, ARCHIVE as INDEX_ARCHIVE, generate as split_index

SOURCE_URL = "https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf"
SOURCE_SHA = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
BODY_SHA = "2682bb8db6d2ca096f4d8fb204ccafe49d1b086b4626ee4f4a7c27abd5c114d8"
PREFIX = "helladius_chrestomathia_photius_bekker_v2_"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def row_hash(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def historical_rows(root=ROOT):
    original = gzip.decompress((root / INDEX_ARCHIVE / "before.jsonl.gz").read_bytes())
    body, _, _, _ = split_index(original)
    if sha(body) != BODY_SHA:
        raise ValueError("Historical Photius source rows changed")
    pages = defaultdict(list)
    for line in body.splitlines():
        row = json.loads(line)
        match = re.fullmatch(PREFIX + r"(\d{4})[.]\d+", row["locus"])
        if match is None:
            raise ValueError("Unknown historical passage identity")
        pages[int(match[1])].append(row)
    return dict(sorted(pages.items()))


def worksheet(selected, root=ROOT):
    rows = historical_rows(root)
    if not set(selected) <= set(rows):
        raise ValueError("Requested page is outside the retained historical source")
    return {"schema_version": 1, "work": "photius.bibliotheca",
        "kind": "source-reviewed-apparatus-exclusions",
        "source": {"url": SOURCE_URL, "sha256": SOURCE_SHA},
        "historical_body_sha256": BODY_SHA, "reviewed_at": None,
        "pages": [{"scan_page": page, "printed_page": page + 265,
            "source_pdf_sha256": SOURCE_SHA, "source_url": SOURCE_URL,
            "reviewed_at": None, "evidence": "",
            "rows": [{"locus": row["locus"], "full_row_text": row["text"],
                      "row_sha256": row_hash(row), "exclusions": []} for row in rows[page]]}
            for page in sorted(selected)]}


def parse_pages(value):
    pages = set()
    for item in value.split(","):
        low, separator, high = item.partition("-")
        pages.update(range(int(low), int(high) + 1) if separator else [int(low)])
    return sorted(pages)


def view_region(page):
    """Use noisy text-layer boxes only to enlarge the viewing area, never as text."""
    w, h = page.rect.width, page.rect.height
    boxes = [span["bbox"] for block in page.get_text("dict")["blocks"] if block["type"] == 0
             for line in block["lines"] for span in line["spans"]
             if .04 < (span["bbox"][1] + span["bbox"][3]) / (2*h) < .86]
    if not boxes:
        return [0, 0, 1, 1]
    # Generous padding and lower extent retain unrecognized body/notes. The
    # full page remains available when a viewing crop omits meaningful ink.
    return [max(0, min(b[0] for b in boxes)/w - .025),
            max(0, min(b[1] for b in boxes)/h - .025),
            min(1, max(b[2] for b in boxes)/w + .025),
            min(1, max(.82, max(b[3] for b in boxes)/h + .025))]


def render(pdf_path, out, review):
    import fitz
    if sha(pdf_path.read_bytes()) != SOURCE_SHA:
        raise ValueError("Source PDF differs from the pinned legacy edition")
    document = fitz.open(pdf_path); out.mkdir(parents=True, exist_ok=True)
    for item in review["pages"]:
        number = item["scan_page"]; page = document[number - 1]
        w, h = page.rect.width, page.rect.height
        box = view_region(page)
        views = {"full": [0, 0, 1, 1], "view": box,
                 "lower": [box[0], max(box[1], box[3] - .45), box[2], box[3]]}
        item["viewing_regions"] = views
        for label, region in views.items():
            target = out / f"page-{number:04d}-{label}.png"
            if target.exists():
                continue
            scale = 1800 / (w * (region[2] - region[0]))
            clip = fitz.Rect(region[0]*w, region[1]*h, region[2]*w, region[3]*h)
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False).save(target)
        (out / f"page-{number:04d}-rows.json").write_bytes(encode(item))
        lines = []
        for row in item["rows"]:
            lines.extend([f"{row['locus']} [{len(row['full_row_text'])} code points]", row["full_row_text"], ""])
        (out / f"page-{number:04d}-rows.txt").write_text("\n".join(lines), encoding="utf-8")


def validate(review, *, root=ROOT, complete=False):
    original = historical_rows(root)
    if (review.get("schema_version") != 1 or review.get("kind") != "source-reviewed-apparatus-exclusions"
            or review.get("work") != "photius.bibliotheca"
            or review.get("source") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or review.get("historical_body_sha256") != BODY_SHA or not review.get("reviewed_at")):
        raise ValueError("Review lacks its exact source/snapshot authority and completed date")
    seen = set()
    for page in review["pages"]:
        number = page["scan_page"]
        if (number in seen or number not in original or page["printed_page"] != number+265
                or page["source_pdf_sha256"] != SOURCE_SHA or page["source_url"] != SOURCE_URL
                or not page.get("reviewed_at") or not page.get("evidence")):
            raise ValueError("Every physical page requires a completed source review")
        seen.add(number)
        expected = {row["locus"]: row for row in original[number]}
        rows = page["rows"]
        if len(rows) != len(expected) or {row["locus"] for row in rows} != set(expected):
            raise ValueError("Review must retain every historical row, including body-only rows")
        for row in rows:
            source = expected[row["locus"]]; text = source["text"]
            if row["full_row_text"] != text or row["row_sha256"] != row_hash(source):
                raise ValueError("Exact historical row identity/text changed")
            previous = 0
            for span in row["exclusions"]:
                low, high = span["start"], span["end"]
                box = span.get("source_region", [])
                if (type(low) is not int or type(high) is not int or not previous <= low < high <= len(text)
                        or span.get("original_text") != text[low:high]
                        or span.get("classification") not in {"critical-apparatus", "printer_signature", "ocr_markup", "running_header"}
                        or not span.get("evidence")
                        or len(box) != 4 or not all(type(v) in (int,float) for v in box)
                        or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1)):
                    raise ValueError("Apparatus exclusion lacks exact ordered offsets and source evidence")
                previous = high
    if complete and seen != set(original):
        raise ValueError("Apparatus authority must review all 236 historical pages")
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", help="Physical PDF page list/ranges, such as101,145-210")
    parser.add_argument("--scan-pdf", type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--merge", action="append", type=Path, default=[])
    args = parser.parse_args()
    if args.merge:
        reviews = [validate(json.loads(path.read_bytes())) for path in args.merge]
        review = {**reviews[0], "pages": sorted([p for r in reviews for p in r["pages"]], key=lambda p:p["scan_page"])}
        validate(review, complete=True)
    else:
        selected = parse_pages(args.pages) if args.pages else list(historical_rows())
        review = worksheet(selected)
        if args.render_dir:
            if args.scan_pdf is None:
                parser.error("Rendering requires --scan-pdf")
            render(args.scan_pdf, args.render_dir, review)
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_bytes(encode(review))
    print(json.dumps({"pages": len(review["pages"]), "rows": sum(len(p["rows"]) for p in review["pages"]),
                      "completed": bool(args.merge)}))


if __name__ == "__main__":
    main()
