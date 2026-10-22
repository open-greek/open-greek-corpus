#!/usr/bin/env python3
"""Retain original color page images underlying the Headlam–Knox PDF.

The full capture archive stays in the ignored cache. Only the inventoried body
pages, original scan metadata, and their deterministic content pins are bundled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = "data/corpus_changes/herodas-reading-sources"
ARCHIVE_URL = "https://archive.org/download/mimesfragments00hero/mimesfragments00hero_orig_jp2.tar"
ARCHIVE_SHA256 = "a2226e05c486682e2214513156754b105dd918eb030d98521bb0be5bb7e589ed"
SCAN_URL = "https://ia601601.us.archive.org/24/items/mimesfragments00hero/mimesfragments00hero_scandata.xml"
SCAN_SHA256 = "17526b4dbec86c9db4f3057530e85b4908c25df4ae335042f4969ab049a8f776"
MANIFEST_SHA256 = "754fbe209019cf8771ad26bc882ae9d81a6986a466235deae8934cbf3d12e475"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _inventory(scan_raw):
    from herodas_body_source_observations import BODY_PAGES
    if sha(scan_raw) != SCAN_SHA256:
        raise ValueError("Original Herodas scan metadata changed")
    pages = [page for page in ET.fromstring(scan_raw).findall(".//pageData/page")
             if page.findtext("addToAccessFormats") != "false"]
    if len(pages) != 542:
        raise ValueError("Herodas access-page inventory changed")
    entries = {}
    for spec in BODY_PAGES:
        number = spec["scan_page"]
        page = pages[number - 1]
        leaf = int(page.attrib["leafNum"])
        if page.findtext("pageNumber") != str(number - 70):
            raise ValueError("Herodas original capture does not match the physical printed page")
        entries[str(number)] = {"leaf": leaf, "printed_page": number - 70,
            "member": f"mimesfragments00hero_orig_jp2/mimesfragments00hero_orig_{leaf:04d}.jp2",
            "file": f"page-{number:04d}.jp2",
            "rotate_clockwise": int(page.findtext("rotateDegree")),
            "crop_box": [int(page.findtext("cropBox/" + key)) for key in ("x", "y", "w", "h")]}
    return entries


def build(archive, scandata):
    if sha(Path(archive).read_bytes()) != ARCHIVE_SHA256:
        raise ValueError("Original Herodas capture archive changed")
    scan_raw = Path(scandata).read_bytes()
    entries = _inventory(scan_raw)
    files = {"scandata.xml": scan_raw}
    with tarfile.open(archive) as source:
        for entry in entries.values():
            raw = source.extractfile(entry["member"]).read()
            files[entry["file"]] = raw
            entry.update(sha256=sha(raw), bytes=len(raw))
    files["manifest.json"] = encoded({"schema_version": 1,
        "source": "https://archive.org/details/mimesfragments00hero", "license": "PD",
        "qualification": "Original color captures from the same scan as the pinned PDF; these are not an independent textual witness.",
        "archive": {"url": ARCHIVE_URL, "sha256": ARCHIVE_SHA256},
        "scandata": {"url": SCAN_URL, "sha256": sha(scan_raw)}, "pages": entries})
    return files


def check(root=ROOT):
    root = Path(root) / BUNDLE
    manifest_raw = (root / "manifest.json").read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256:
        raise ValueError("Herodas original-image manifest differs from the pinned capture extraction")
    manifest = json.loads(manifest_raw)
    if manifest["archive"] != {"url": ARCHIVE_URL, "sha256": ARCHIVE_SHA256}:
        raise ValueError("Herodas original-image source identity changed")
    if (manifest["scandata"] != {"url": SCAN_URL, "sha256": SCAN_SHA256}
            or sha((root / "scandata.xml").read_bytes()) != SCAN_SHA256):
        raise ValueError("Herodas original scan metadata changed")
    expected = _inventory((root / "scandata.xml").read_bytes())
    if set(manifest["pages"]) != set(expected):
        raise ValueError("Herodas original images do not cover the complete body inventory")
    for number, page in manifest["pages"].items():
        if ({key: page.get(key) for key in expected[number]} != expected[number]
                or set(page) != {*expected[number], "sha256", "bytes"}):
            raise ValueError("Herodas original page mapping or crop changed")
        raw = (root / page["file"]).read_bytes()
        if sha(raw) != page["sha256"] or len(raw) != page["bytes"]:
            raise ValueError("Herodas original page image changed")
    return manifest


def image(page, root=ROOT):
    """Render the original capture to the PDF's physical crop, without scaling."""
    from PIL import Image
    root = Path(root) / BUNDLE
    entry = json.loads((root / "manifest.json").read_bytes())["pages"][str(page)]
    im = Image.open(root / entry["file"])
    im = im.rotate(-entry["rotate_clockwise"], expand=True)
    x, y, width, height = entry["crop_box"]
    return im.crop((x, y, x + width, y + height))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--scandata", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check(args.root)
        print("Herodas original body images are current")
        return
    if not args.archive or not args.scandata:
        parser.error("Pass the pinned --archive and --scandata files")
    target = args.root / BUNDLE
    files = build(args.archive, args.scandata)
    target.mkdir(parents=True, exist_ok=True)
    for relative, raw in files.items():
        path = target / relative
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("Refusing to replace a different retained Herodas source: " + relative)
        path.write_bytes(raw)
    check(args.root)
    print(f"Retained {len(files) - 2} original body images")


if __name__ == "__main__":
    main()
