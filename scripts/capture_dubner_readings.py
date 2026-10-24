#!/usr/bin/env python3
"""Capture or verify source evidence for bounded Dübner reading corrections.

Capture requires the two already pinned PDF scans and PyMuPDF 1.28.2. Offline
checking uses the standard library and committed evidence only; PDFs and model
weights are not downloaded, copied into git, or needed for that check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import dubner_reading_observations as observations

ROOT = Path(__file__).resolve().parents[1]
PILOT_MANIFEST = "data/audits/acharnians-source-pilot/manifest.json"
PILOT_MANIFEST_SHA256 = "70ada1a9cbe310641aa05b61e27fb60e957f0c98456aadc27a941a599d20f20c"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


def recipe_pins():
    scripts = Path(__file__).resolve().parent
    return {name: sha((scripts / name).read_bytes()) for name in (
        "dubner_reading_observations.py", "capture_dubner_readings.py")}


def _pilot_files(root):
    raw = (root / PILOT_MANIFEST).read_bytes()
    if sha(raw) != PILOT_MANIFEST_SHA256:
        raise ValueError("The frozen ten-page pilot evidence changed")
    manifest = json.loads(raw)
    result = [{"path": PILOT_MANIFEST, "sha256": PILOT_MANIFEST_SHA256,
               "kind": "frozen-pilot-manifest"}]
    parent = str(Path(PILOT_MANIFEST).parent)
    for page, _, _ in observations.PAGE_REVIEWS:
        name = f"page-{page:04d}.png"
        result.append({"path": parent + "/" + name,
                       "sha256": manifest["files"][name]["sha256"],
                       "kind": "frozen-pilot-page", "source_pdf": "toronto",
                       "source_pdf_page": page})
    return result


def _expected_manifest(root, review_raw):
    if set(observations.CROPS) != set(observations.CROP_SHA256):
        raise ValueError("A reviewed reading crop lacks its pinned image hash")
    files = [{"path": observations.REVIEW_PATH, "sha256": sha(review_raw),
              "kind": "source-reading-review"}]
    for name, (source, page, rect) in observations.CROPS.items():
        files.append({"path": f"{observations.OUTPUT}/source-evidence/{name}.png",
            "sha256": observations.CROP_SHA256[name], "kind": "source-reading-crop",
            "source_pdf": source, "source_pdf_page": page,
            "source_pdf_sha256": observations.SOURCE_PDFS[source]["sha256"],
            "normalized_pdf_rectangle": list(rect)})
    files.extend(_pilot_files(root))
    return {"schema_version": 1, "reviewed_at": observations.REVIEWED_AT,
        "sources": observations.SOURCE_PDFS,
        "render": {"provider": "PyMuPDF", "version": observations.RENDERER_VERSION,
                   "dpi": observations.RENDER_DPI, "images_retouched": False},
        "recipe_sha256": recipe_pins(), "files": files,
        "qualification": "Bounded reading review of the frozen ten-page pilot. Each source image is a direct PDF rendering; both scans reproduce one printed 1855 edition, not independent textual editions. The full original OCR and contrary readings remain in the archived inputs."}


def check(root=ROOT):
    """Verify every source image, authored observation, pin, and exact preimage."""
    root = Path(root)
    review_raw = encoded(observations.build(root))
    if (root / observations.REVIEW_PATH).read_bytes() != review_raw:
        raise ValueError("Dübner source-reading observations no longer reproduce")
    expected = _expected_manifest(root, review_raw)
    if (root / observations.CAPTURE_PATH).read_bytes() != encoded(expected):
        raise ValueError("Dübner reading capture metadata or recipe changed")
    for item in expected["files"]:
        if sha((root / item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("Dübner reading evidence changed: " + item["path"])
    return expected


def capture(root, toronto_pdf, harvard_pdf):
    """Render staged evidence only after both original PDF pins validate."""
    root = Path(root)
    paths = {"toronto": Path(toronto_pdf), "harvard": Path(harvard_pdf)}
    for source, path in paths.items():
        if sha(path.read_bytes()) != observations.SOURCE_PDFS[source]["sha256"]:
            raise ValueError("Dübner reading PDF pin mismatch: " + source)
    import pymupdf
    if pymupdf.VersionBind != observations.RENDERER_VERSION:
        raise ValueError("Capture requires the reviewed PyMuPDF renderer version")
    review_raw = encoded(observations.build(root))
    expected = _expected_manifest(root, review_raw)
    rendered = {}
    with tempfile.TemporaryDirectory(prefix="dubner-reading-capture-") as temporary:
        docs = {source: pymupdf.open(path) for source, path in paths.items()}
        try:
            for source, doc in docs.items():
                if len(doc) != observations.SOURCE_PDFS[source]["pages"]:
                    raise ValueError("Dübner source PDF page count changed")
            for name, (source, page, rect) in observations.CROPS.items():
                leaf = docs[source][page - 1]
                width, height = leaf.rect.width, leaf.rect.height
                clip = pymupdf.Rect(rect[0] * width, rect[1] * height,
                                    rect[2] * width, rect[3] * height)
                path = Path(temporary) / (name + ".png")
                leaf.get_pixmap(dpi=observations.RENDER_DPI, clip=clip).save(path)
                raw = path.read_bytes()
                if sha(raw) != observations.CROP_SHA256[name]:
                    raise ValueError("The reviewed source crop no longer reproduces: " + name)
                rendered[f"{observations.OUTPUT}/source-evidence/{name}.png"] = raw
        finally:
            for doc in docs.values():
                doc.close()
    rendered[observations.REVIEW_PATH] = review_raw
    rendered[observations.CAPTURE_PATH] = encoded(expected)
    for name, raw in rendered.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return check(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--toronto-pdf", type=Path)
    parser.add_argument("--harvard-pdf", type=Path)
    args = parser.parse_args()
    if args.capture:
        if args.toronto_pdf is None or args.harvard_pdf is None:
            parser.error("--capture requires both pinned PDF paths")
        result = capture(args.root, args.toronto_pdf, args.harvard_pdf)
    else:
        result = check(args.root)
    print(json.dumps({"verified_files": len(result["files"]),
                      "reviewed_at": result["reviewed_at"]}, sort_keys=True))


if __name__ == "__main__":
    main()
