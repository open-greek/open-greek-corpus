"""Reproduce the retained Dübner continuation-review crops from pinned PDFs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import dubner_evidence_observations as observations
from dubner_witness_alignment import SOURCE_SCANS
from repair_dubner_scholias import encoded, local_path, publish, sha

MANIFEST = observations.AUDIT + "/source-captures.json"
SCALE = 4
RENDERER = "1.28.2"


def capture_path(identifier):
    return observations.AUDIT + "/sources/" + identifier + ".png"


def capture(root, pdfs):
    import pymupdf
    if pymupdf.VersionBind != RENDERER:
        raise ValueError("Reproduce Dübner crops with PyMuPDF " + RENDERER)
    outputs, files = {}, []
    for scan in ("toronto", "harvard"):
        pdf = Path(pdfs[scan])
        if sha(pdf.read_bytes()) != SOURCE_SCANS[scan]["sha256"]:
            raise ValueError("Dübner PDF checksum changed: " + scan)
        with pymupdf.open(pdf) as document:
            if len(document) != SOURCE_SCANS[scan]["pages"]:
                raise ValueError("Dübner PDF page accounting changed")
            for identifier, (source, page, box) in sorted(observations.CAPTURES.items()):
                if source != scan:
                    continue
                sheet = document[page - 1]
                rect = pymupdf.Rect(*(a*b for a,b in zip(box,
                    (sheet.rect.width,sheet.rect.height,sheet.rect.width,sheet.rect.height))))
                raw = sheet.get_pixmap(matrix=pymupdf.Matrix(SCALE,SCALE),
                    clip=rect,alpha=False).tobytes("png")
                name = capture_path(identifier)
                outputs[name] = raw
                files.append({"id":identifier,"path":name,"sha256":sha(raw),
                    "scan":source,"pdf_page":page,"rectangle":list(box),
                    "pdf_sha256":SOURCE_SCANS[scan]["sha256"]})
    manifest = {"schema_version":1,"renderer":RENDERER,"scale":SCALE,
        "files":sorted(files,key=lambda item:item["id"])}
    outputs[MANIFEST] = encoded(manifest)
    if sha(outputs[MANIFEST]) != observations.CAPTURE_MANIFEST_SHA256:
        raise ValueError("Re-rendered Dübner captures differ from the reviewed authority; no files were published")
    publish(Path(root),outputs)
    return manifest


def check(root=observations.ROOT):
    root = Path(root)
    raw = local_path(root,MANIFEST).read_bytes()
    if sha(raw) != observations.CAPTURE_MANIFEST_SHA256:
        raise ValueError("Dübner source capture authority changed")
    manifest = json.loads(raw)
    if (manifest["schema_version"] != 1 or manifest["renderer"] != RENDERER
            or manifest["scale"] != SCALE or len(manifest["files"]) != len(observations.CAPTURES)):
        raise ValueError("Dübner source capture recipe changed")
    seen = set()
    for item in manifest["files"]:
        identifier = item["id"]
        if identifier in seen:
            raise ValueError("Repeated Dübner capture identity")
        seen.add(identifier)
        scan,page,box = observations.CAPTURES[identifier]
        if item != {"id":identifier,"path":capture_path(identifier),
                "sha256":sha(local_path(root,capture_path(identifier)).read_bytes()),
                "scan":scan,"pdf_page":page,"rectangle":list(box),
                "pdf_sha256":SOURCE_SCANS[scan]["sha256"]}:
            raise ValueError("Dübner captured evidence changed: " + identifier)
    if seen != set(observations.CAPTURES):
        raise ValueError("Incomplete Dübner source evidence")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture",action="store_true")
    mode.add_argument("--check",action="store_true")
    parser.add_argument("--root",type=Path,default=observations.ROOT)
    parser.add_argument("--toronto-pdf",type=Path)
    parser.add_argument("--harvard-pdf",type=Path)
    args = parser.parse_args()
    if args.capture:
        if not args.toronto_pdf or not args.harvard_pdf:
            parser.error("--capture requires both pinned PDFs")
        result = capture(args.root,{"toronto":args.toronto_pdf,"harvard":args.harvard_pdf})
    else:
        result = check(args.root)
    print(json.dumps({"captures":len(result["files"])}))
