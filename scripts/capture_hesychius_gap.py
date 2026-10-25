#!/usr/bin/env python3
"""Capture pinned edition, neighboring leaves, and missing main-text columns."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

from hesychius_gap_observations import AUDIT, BOUNDARY, CAPTURE_SHA256, REVIEW_DATE, SOURCES

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def check(root=ROOT):
    """Verify retained evidence offline without depending on a PDF cache."""
    root = Path(root)
    raw = (root / AUDIT / "source-evidence.json").read_bytes()
    if sha(raw) != CAPTURE_SHA256:
        raise ValueError("Pinned Hesychius source capture changed")
    manifest = json.loads(raw)
    # JSON turns integer page/column keys into strings.
    literal = json.loads(encode({"sources": SOURCES, "boundary": BOUNDARY}))
    if (manifest["schema_version"] != 1 or manifest["reviewed_at"] != REVIEW_DATE
            or manifest["sources"] != literal["sources"] or manifest["boundary"] != literal["boundary"]
            or len(manifest["images"]) != 8 or len(manifest["columns"]) != 4):
        raise ValueError("Hesychius source review changed")
    expected = {(source, column) for source in SOURCES for column in (259, 260)}
    if {(r["source"], r["printed_column"]) for r in manifest["columns"]} != expected:
        raise ValueError("Hesychius column coverage changed")
    for row in [*manifest["images"], *manifest["columns"]]:
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts or not str(path).startswith(AUDIT + "/source-evidence/"):
            raise ValueError("Unsafe retained source path")
        if sha((root / path).read_bytes()) != row["sha256"]:
            raise ValueError("Retained Hesychius source image changed: " + str(path))
    return manifest


def download(url, path, expected):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=180) as response:
            path.write_bytes(response.read())
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError("Pinned source changed: " + url)
    return raw


def capture(root=ROOT, *, write=False):
    from PIL import Image
    import pymupdf
    root = Path(root)
    output = root / AUDIT / "source-evidence"
    cache = root / ".cache/hesychius-recovery"
    images, columns = [], []
    for identity, source in SOURCES.items():
        pages = [source["title_page"], *source["pages"]]
        if identity == "harvard":
            raw = download(source["artifact_url"], cache / source["filename"], source["sha256"])
            document = pymupdf.open(stream=raw, filetype="pdf")
            if len(document) != source["pdf_pages"]:
                raise ValueError("Pinned PDF page count changed")
        for page in pages:
            path = output / f"{identity}-{page}.png"
            if identity == "harvard":
                pix = document[page - 1].get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), alpha=False)
                image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                artifact_sha = source["sha256"]
            else:
                url = source["artifact_url"].format(leaf=page)
                raw = download(url, cache / f"ghent-{page}.jpg", source["image_sha256"][page])
                image = Image.open(io.BytesIO(raw)).convert("RGB")
                artifact_sha = sha(raw)
            stream = io.BytesIO()
            image.save(stream, format="PNG")
            body = stream.getvalue()
            images.append({"source": identity, "source_page": page, "path": path.relative_to(root).as_posix(),
                "sha256": sha(body), "source_artifact_sha256": artifact_sha,
                "printed_columns": source["pages"].get(page), "role": "edition-title" if page == source["title_page"] else "gap" if page == source["gap_page"] else "boundary"})
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            elif path.read_bytes() != body:
                raise ValueError("Retained source image changed: " + str(path))
            if page == source["gap_page"]:
                for column, region in source["regions"].items():
                    box = tuple(round(value * (image.width if n % 2 == 0 else image.height))
                                for n, value in enumerate(region))
                    crop = image.crop(box)
                    if max(crop.size) > 1600:
                        scale = 1600 / max(crop.size)
                        crop = crop.resize((round(crop.width * scale), round(crop.height * scale)),
                                           Image.Resampling.LANCZOS)
                    stream = io.BytesIO()
                    crop.save(stream, format="PNG")
                    crop_body = stream.getvalue()
                    crop_path = output / f"{identity}-column-{column}.png"
                    columns.append({"id": f"{identity}:{column}", "source": identity, "source_page": page,
                        "printed_column": column, "region": region, "pixel_box": box,
                        "crop_size": crop.size, "max_side": 1600,
                        "path": crop_path.relative_to(root).as_posix(), "sha256": sha(crop_body)})
                    if write:
                        crop_path.write_bytes(crop_body)
                    elif crop_path.read_bytes() != crop_body:
                        raise ValueError("Retained source column changed")
        if identity == "harvard":
            document.close()
    manifest = {"schema_version": 1, "reviewed_at": REVIEW_DATE, "sources": SOURCES,
        "boundary": BOUNDARY, "renderer": {"pymupdf": pymupdf.VersionBind,
            "pillow": Image.__version__, "scale": 2.2, "crop_policy": "rounded normalized source coordinates; RGB PNG; crop max side 1600 with Lanczos"},
        "images": images, "columns": columns}
    destination = root / AUDIT / "source-evidence.json"
    if write:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encode(manifest))
    elif destination.read_bytes() != encode(manifest):
        raise ValueError("Source capture manifest changed")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = check(args.root) if args.check else capture(args.root, write=args.write)
    print(json.dumps({"images": len(result["images"]), "columns": len(result["columns"])}))
