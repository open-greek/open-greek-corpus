#!/usr/bin/env python3
"""Reproduce source-reviewed body crops without replacing original OCR jobs.

The original 1,500 requests remain immutable. This writes an effective manifest
and completed review authority; earlier predictions from changed regions remain
held evidence in scan_ocr_bundle rather than silently entering the body vote.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/ingest_reviews/coverage"
ORIGINAL = DIRECTORY / "cassius-dio-ocr-jobs.json"
EFFECTIVE = DIRECTORY / "cassius-dio-body-ocr-jobs.json"
REVIEW = DIRECTORY / "cassius-dio-body-regions.json"
COMPARISON = DIRECTORY / "cassius-dio-late-comparison-jobs.json"
REVIEW_DATE = "2026-10-18"
DETECTOR_BOUNDS_SHA256 = "947b222f0877cc964456f48a5a691efe21219e8c93a13f026021be782d664eb4"
EDITOR = re.compile(r"\b(?:Bk|Bs|Rk|Reim|Reimar|Dind|Pflugk?|Leuncl|Mss|MSS|Bekker|Cobet|Naber|Boiss|Bois|Capp|Boissevain)\b|supplied|omitted|inserted|deleted|rejected|See Vol|See p\.")
FINITE_DOT_PAGES = {187, 188, 192, 196, 200, 201, 205, 208, 210, 212, 215, 216, 219, 225, 230}
FINITE_DOT_SUFFIX = (
    "On this reviewed page, each printed lacuna-dot series is finite. Copy its visible dots once, "
    "then continue immediately with the next visible Greek words. Never extend a dot sequence or repeat a line."
)
# Source inspection overrides are maintained in code, above the generated
# manifests. Each coordinate is a verified gap, not a change to an OCR reading.
from dio_body_review_evidence import OVERRIDES, CONTACT_SHEETS, FULL_PAGE_CHECKS
_PROPOSAL_DOCUMENTS = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def text_lines(page):
    height, width = page.rect.height, page.rect.width
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["bbox"][0] < width * .49]
            text = "".join(s["text"] for s in spans)
            if sum(c.isalpha() for c in text) < 5:
                continue
            y0 = min(s["bbox"][1] for s in spans) / height
            y1 = max(s["bbox"][3] for s in spans) / height
            if .1 < y0 < .9:
                lines.append({"y0": y0, "y1": y1, "text": text})
    groups = []
    for line in sorted(lines, key=lambda value: value["y0"]):
        if groups and line["y0"] - groups[-1]["y0"] < .006:
            groups[-1]["y1"] = max(groups[-1]["y1"], line["y1"])
            groups[-1]["text"] += " " + line["text"]
        else:
            groups.append(line.copy())
    return groups


def detected_boundary(page):
    """Propose font-size transitions; the complete contact review is authority."""
    import cv2
    import numpy as np
    import pymupdf
    from scipy.ndimage import gaussian_filter1d
    from scipy.signal import find_peaks
    cv2.setNumThreads(1)
    rect = page.rect
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2200 / rect.height, 2200 / rect.height),
                         clip=pymupdf.Rect(0, 0, rect.width * .5, rect.height), alpha=False)
    raster = np.frombuffer(pix.samples, dtype="uint8").reshape(pix.height, pix.width, pix.n)[:, :, :3].mean(axis=2).astype("uint8")
    height, width = raster.shape
    binary = (raster < 160).astype("uint8")
    binary[:, :int(width * .15)] = 0
    binary[:, int(width * .93):] = 0
    projection = binary.sum(axis=1).astype(float)
    smooth = gaussian_filter1d(projection, 1.2)
    peaks, _ = find_peaks(smooth, distance=height * .013,
                         prominence=width * .015, height=width * .04)
    _, _, stats, centers = cv2.connectedComponentsWithStats(binary, 8)
    good = ((stats[:, 4] >= 20) & (stats[:, 3] >= height * .0055)
            & (stats[:, 3] < height * .045) & (stats[:, 2] >= 2) & (stats[:, 2] < width * .1))
    lines = []
    for i, peak in enumerate(peaks):
        y0 = 0 if i == 0 else (peaks[i - 1] + peak) / 2
        y1 = height if i + 1 == len(peaks) else (peak + peaks[i + 1]) / 2
        indexes = np.where(good & (centers[:, 1] >= y0) & (centers[:, 1] < y1))[0]
        if len(indexes) < 6 or peak / height < .10 or peak / height > .90:
            continue
        lines.append({"peak": float(peak / height),
                      "q25": float(np.percentile(stats[indexes, 3], 25) / height)})
    body = np.percentile([line["q25"] for line in lines], 80)
    for line in lines:
        line["small"] = line["q25"] < body * .91
    anchored = []
    for line in text_lines(page):
        if line["y0"] <= .45 or not EDITOR.search(line["text"]):
            continue
        center = (line["y0"] + line["y1"]) / 2
        index = min(range(len(lines)), key=lambda i: abs(lines[i]["peak"] - center))
        if abs(lines[index]["peak"] - center) < .03 and (lines[index]["small"] or any(v["small"] for v in lines[index + 1:index + 3])):
            anchored.append(index)
    candidates = [i for i, line in enumerate(lines) if line["peak"] > .48 and line["small"]
                  and not any(not other["small"] for other in lines[i:])]
    if anchored:
        candidates = [min(anchored)]
    if not candidates:
        return .91, "no-apparatus-step"
    index = min(candidates)
    while index > 0 and lines[index - 1]["small"] and lines[index - 1]["peak"] > .4 and lines[index]["peak"] - lines[index - 1]["peak"] < .026:
        index -= 1
    if index == 0:
        return .91, "ambiguous"
    left, right = lines[index - 1]["peak"] * height, lines[index]["peak"] * height
    lo, hi = int(left + (right - left) * .25), int(right - (right - left) * .25)
    band = projection[lo:hi]
    ys = np.where(band <= min(band) + 2)[0] + lo
    cut = float(np.median(ys) / height) if len(ys) else float((left + right) / 2 / height)
    return round(cut, 5), "rendered-glyph-size-and-note-anchor"


def proposal(task):
    import pymupdf
    identifier, path, number = task
    if path not in _PROPOSAL_DOCUMENTS:
        _PROPOSAL_DOCUMENTS[path] = pymupdf.open(path)
    return identifier, detected_boundary(_PROPOSAL_DOCUMENTS[path][number - 1])


def build(pdf_dir, original_raw=None, review_path=None, workers=8):
    import pymupdf
    original_raw = ORIGINAL.read_bytes() if original_raw is None else original_raw
    original = json.loads(original_raw)
    effective = deepcopy(original)
    documents = {}
    evidence, substitutions, detected = {}, [], []
    late = sorted((p for p in original["pages"] if p["source_volume"] >= 6),
                  key=lambda page: (page["source_volume"], page["scan_page"]))
    if len(late) != 741:
        raise ValueError("The reviewed late Dio selection changed")
    for page in late:
        source = page["source"]
        if source in documents:
            continue
        expected = original["sources"][source]["sha256"]
        candidates = [pdf_dir / (source + ".pdf"), pdf_dir / (expected + ".pdf")]
        path = next((p for p in candidates if p.exists()), candidates[0])
        if sha(path.read_bytes()) != expected:
            raise ValueError("The reviewed Cary source PDF changed")
        documents[source] = path
    ranks = {page["id"]: i for i, page in enumerate(late)}
    tasks = [(page["id"], str(documents[page["source"]]), page["scan_page"]) for page in late]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        proposals = dict(pool.map(proposal, tasks))
    for page in effective["pages"]:
        if page["source_volume"] < 6:
            continue
        key = (page["source_volume"], page["scan_page"])
        cut, method = proposals[page["id"]]
        detected.append([page["id"], cut])
        override = OVERRIDES.get(key)
        if override:
            cut, method = override["y1"], "source-reviewed-blank-gap-override"
        old_region, region = page["region"], [0, 0, .5, cut]
        identifier = page["id"]
        evidence_id = identifier.replace("dio-cary-", "dio-body-")
        decision = {"id": identifier, "source": page["source"], "scan_page": page["scan_page"],
                    "original_region": old_region, "region": region}
        entry = dict(decision, evidence_id=evidence_id)
        note = override["evidence"] if override else (
            "The complete source contact review verified all main Greek body and transmission credits above this boundary. "
            + ("No Greek apparatus occurs below the body; the crop excludes only the page footer." if method == "no-apparatus-step"
               else "The boundary follows the last full-size body/source-credit line and excludes the smaller editorial apparatus."))
        check = FULL_PAGE_CHECKS.get(key)
        if check:
            note += " " + check
        record = dict(decision, evidence=note, reviewed_at=REVIEW_DATE,
                      source_pdf_sha256=original["sources"][page["source"]]["sha256"],
                      contact_sheet_sha256=CONTACT_SHEETS[ranks[identifier] // 48],
                      boundary_method=method, original_ocr_retention="Exact old-geometry predictions remain held in the input bundle.")
        if key[0] == 9 and key[1] in FINITE_DOT_PAGES:
            suffix = {"original_prompt_suffix": page.get("prompt_suffix"), "prompt_suffix": FINITE_DOT_SUFFIX}
            page["prompt_suffix"] = FINITE_DOT_SUFFIX
            entry.update(suffix)
            record.update(suffix)
            record["evidence"] += " Source inspection confirms a finite printed lacuna-dot series; the suffix prevents extending dots or repeating lines without changing the visible text."
        page["region"] = region
        evidence[evidence_id] = record
        substitutions.append(entry)
    ordered_detected = sorted(detected, key=lambda row: ranks[row[0]])
    if sha(json.dumps(ordered_detected, ensure_ascii=False, separators=(",", ":")).encode()) != DETECTOR_BOUNDS_SHA256:
        raise ValueError("Rendered body proposals differ from the completed source review")
    review = {"schema_version": 1, "kind": "scan-region-body-review", "reviewed_at": REVIEW_DATE,
              "generator": "scripts/prepare_dio_body_regions.py", "original_manifest_sha256": sha(original_raw),
              "method": "All 741 late Greek panels were inspected on 16 contact sheets. Font-size proposals were corrected against source pixels, and short/blank contacts were checked on full pages. No OCR reading is silently trimmed.",
              "sources": {key: {"url": value["url"], "sha256": value["sha256"]} for key, value in original["sources"].items()},
              "contact_sheet_sha256": CONTACT_SHEETS, "evidence": evidence}
    comparison_source = next(page["source"] for page in late if page["source_volume"] == 9)
    review["held_comparison_regions"] = [{"source": comparison_source, "scan_page": 240,
        "source_pdf_sha256": original["sources"][comparison_source]["sha256"],
        "region": [.095, .615, .43, .880], "printed_page": 470,
        "classification": "comparative-quotation", "license": "PD",
        "credits": ["Leo/Cedrenus: Ἄβιτος, ὡς φησι Δίων…", "Petrus Patricius, Exc. Vat. 152"],
        "evidence": "Full-size comparative Greek below the full-width rule is excluded from the upper main body and retained as a separately attributed comparison. It is not small critical apparatus.",
        "reviewed_at": REVIEW_DATE}]
    review_raw = encode(review)
    effective["reviewed_substitutions"] = {"original_manifest_sha256": sha(original_raw),
        "source_review": {"path": review_path or REVIEW.relative_to(ROOT).as_posix(), "sha256": sha(review_raw)},
        "regions": substitutions}
    return effective, review


def comparison_manifest(effective, review):
    region = review["held_comparison_regions"][0]
    return {"schema_version": 1, "generated_by": "scripts/prepare_dio_body_regions.py",
        "review_sha256": sha(encode(review)), "sources": effective["sources"],
        "prompt": effective["prompt"], "pages": [{
            "id": "dio-cary-v9-pdf0240-comparison", "source": region["source"], "scan_page": 240,
            "region": region["region"], "max_side": 2200, "work": "cassius-dio.historiae-romanae",
            "source_volume": 9, "printed_page": 470, "transmission": "comparative-quotation",
            "admission": "comparative-paratext", "panel_role": "comparison",
            "attribution_heading": "; ".join(region["credits"])}]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=EFFECTIVE)
    parser.add_argument("--review", type=Path, default=REVIEW)
    parser.add_argument("--comparison-out", type=Path, default=COMPARISON)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    effective, review = build(args.pdf_dir, review_path=args.review.relative_to(ROOT).as_posix(), workers=args.workers)
    for path, value in ((args.review, review), (args.out, effective),
                        (args.comparison_out, comparison_manifest(effective, review))):
        raw = encode(value)
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError("Reviewed Dio body artifacts differ from the reproducible build")
        else:
            path.write_bytes(raw)
    print(f"{len(effective['pages'])} regions retained; {len(review['evidence'])} reviewed late crops; 15 finite-dot suffixes")


if __name__ == "__main__":
    main()
