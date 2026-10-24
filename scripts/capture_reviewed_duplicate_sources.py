#!/usr/bin/env python3
"""Capture or verify the pinned scan evidence for reviewed duplicate blocks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from reviewed_duplicate_block_observations import (
    AUDIT, GROUPS, PHYSICAL_SEQUENCE, QUALIFICATION, RENDERER_VERSION,
    RENDER_SCALE, RETAINED_IMAGES, REVIEW_DATE, SOURCES, UPSTREAM_TEXTS,
)

MANIFEST = AUDIT + "/source-evidence.json"
INVENTORY = AUDIT + "/source-observations.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def image_path(source, page):
    return f"{AUDIT}/source-evidence/{source}-{page:04d}.png"


def inventory():
    return {"review_date": REVIEW_DATE, "groups": GROUPS, "upstream_texts": UPSTREAM_TEXTS,
            "physical_sequence": PHYSICAL_SEQUENCE, "qualification": QUALIFICATION}


def expected_manifest():
    return {"schema_version": 1, "review_date": REVIEW_DATE,
        "renderer": {"name": "PyMuPDF", "version": RENDERER_VERSION,
                     "scale": RENDER_SCALE, "color": "RGB", "alpha": False},
        "sources": list(SOURCES),
        "files": [{"path": INVENTORY, "sha256": sha(encoded(inventory()))}] + [
            {"path": image_path(source, page), "sha256": digest}
            for source, page, digest in RETAINED_IMAGES]}


def check(root):
    root = Path(root)
    expected = expected_manifest()
    if (root / MANIFEST).read_bytes() != encoded(expected):
        raise ValueError("Reviewed duplicate source manifest differs from its observations")
    for entry in expected["files"]:
        if sha((root / entry["path"]).read_bytes()) != entry["sha256"]:
            raise ValueError("Reviewed duplicate source evidence changed: " + entry["path"])
    return expected


def capture(root, *, cache, pdf_paths=None):
    import pymupdf
    if pymupdf.VersionBind != RENDERER_VERSION:
        raise ValueError("Source capture requires PyMuPDF " + RENDERER_VERSION)
    root, cache = Path(root), Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    pdf_paths = pdf_paths or {}
    outputs = {INVENTORY: encoded(inventory())}
    for source in SOURCES:
        path = Path(pdf_paths.get(source["id"], cache / source["filename"]))
        if not path.exists():
            with urlopen(source["artifact_url"]) as response:
                raw = response.read()
            if sha(raw) != source["sha256"]:
                raise ValueError("Downloaded source PDF differs from its reviewed pin")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sha(path.read_bytes()) != source["sha256"]:
            raise ValueError("Source PDF differs from its reviewed pin: " + source["id"])
        with pymupdf.open(path) as document:
            if len(document) != source["pdf_pages"]:
                raise ValueError("Source PDF page count changed")
            for source_id, page, digest in RETAINED_IMAGES:
                if source_id != source["id"]:
                    continue
                raw = document[page - 1].get_pixmap(
                    matrix=pymupdf.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False).tobytes("png")
                if sha(raw) != digest:
                    raise ValueError("Source rendering changed: " + image_path(source_id, page))
                outputs[image_path(source_id, page)] = raw
    outputs[MANIFEST] = encoded(expected_manifest())
    # Validate every byte before publishing any captured authority.
    for name, raw in outputs.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return check(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/ogc/reviewed-duplicates")
    parser.add_argument("--cyril-pdf", type=Path)
    parser.add_argument("--hesychius-pdf", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check(args.root) if args.check else capture(args.root, cache=args.cache,
        pdf_paths={k: v for k, v in (("cyril-pg73", args.cyril_pdf),
                                   ("hesychius", args.hesychius_pdf)) if v is not None})
    print(json.dumps({"sources": len(result["sources"]), "evidence_files": len(result["files"])}))


if __name__ == "__main__":
    main()
