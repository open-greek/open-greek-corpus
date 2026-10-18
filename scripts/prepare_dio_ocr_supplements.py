#!/usr/bin/env python3
"""Pin additional Dio retries while retaining the first retry request unchanged."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from prepare_dio_ocr_retries import (ROOT, DIRECTORY, MANIFEST, MANIFEST_SHA256,
    CHECKPOINTS, STRIP_PROMPT, encode, sha, load_originals)

PARENT = DIRECTORY + "/cassius-dio-qwen38-retry-jobs.json"
PARENT_SHA256 = "d97e081912f3b45da68370f59eed1768d8c911af44b0323258443aaeb63ac029"
PINS = {
    "qwen36": {
        "dio-cary-v2-pdf0195-comparison": "e01fb452490b22127dd2040ea5b13b3170a49d16cc65e623eded354ab68dfbe5",
        "dio-cary-v7-pdf0107": "0dda261fedaa188608e2cf5583930075bca72516bfc63de68974528567f8a3d2",
    },
    "qwen38": {
        "dio-cary-v2-pdf0195-comparison": "ea38b9a5a2f1b89ca6b8bcfa676f9111d40064f374338920e20fa455e538426f",
    },
    "child": {
        "dio-cary-v6-pdf0206-reviewed-strip-1": "0f332d19b88c4c71af15e48fd34e87880b76fed25d00c6c39a1f349976da1a40",
    },
}
REGIONS = {
    "dio-cary-v2-pdf0195-comparison": [[.04,.4542,.47,.6115], [.04,.6115,.47,.737], [.04,.737,.47,.882]],
    "dio-cary-v7-pdf0107": [[.04,.105,.47,.326], [.04,.326,.47,.5385], [.04,.5385,.47,.7625]],
    "dio-cary-v6-pdf0206-reviewed-strip-1": [[.04,.065,.47,.1558], [.04,.1558,.47,.2255], [.04,.2255,.47,.27083]],
}
FINDINGS = {
    "dio-cary-v2-pdf0195-comparison": "Cary II printed378, the lower Zonaras9.27 comparative panel, is polytonic throughout. Both original checkpoint readings lose nearly all accents and breathings. Three enlarged strips retain the Zonaras reference, every Greek paragraph and the final printed ὁ. The bottom edge lies below that line and above the printed page number; no apparatus or dot band occurs in this panel.",
    "dio-cary-v7-pdf0107": "Cary VII printed204 contains full Greek prose and one finite dot sequence following θύων εἶδεν ἀποστρεφόμενον. The pinned Qwen3.6 attempt reaches its length limit. All body lines, the Xiphilinus reference and the finite dot row remain in the three enlarged strips. The top edge excludes the English running header; the prior bottom apparatus boundary is preserved.",
    "dio-cary-v6-pdf0206-reviewed-strip-1": "The first enlarged Qwen3.8 retry strip of Cary VI printed402 still loses printed breathings:293 Greek letters retain only one breathing mark. The source visibly prints them in πόλει, ἄλλα, ὕπατον, ἐφήβους, ὁποία and other words. Three narrower child strips exactly partition this parent strip at gaps between complete printed lines. Successful sibling strips2/3 remain unchanged; no word is invented or joined across a strip edge.",
}
EVIDENCE = {"sha256": "4d5e269c4bf4f2ff2ce5205091cdfb32ef1a107f02c550bc3d89c27de3e0d4e2",
    "description": "Source-rendered details of both internal boundaries for Cary II195 comparison, VII107 and VI206 first-strip children; all six edges inspected in the pixels."}


def prepare(root, original_paths, pdf_dir, output_dir):
    manifest_raw, parent_raw = (root / MANIFEST).read_bytes(), (root / PARENT).read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256 or sha(parent_raw) != PARENT_SHA256:
        raise ValueError("The original Dio or first retry authority changed")
    manifest, parent = json.loads(manifest_raw), json.loads(parent_raw)
    main_pages = {p["id"]: p for p in manifest["pages"]}
    parent_pages = {p["id"]: p for p in parent["pages"]}
    originals = load_originals(original_paths)
    results = {}
    for key, pins in PINS.items():
        family = "qwen38" if key == "child" else key
        model, revision = CHECKPOINTS[family]
        prior, pages = (parent, parent_pages) if key == "child" else (manifest, main_pages)
        checked, jobs = {}, []
        for identifier, artifact in pins.items():
            if artifact not in originals:
                raise ValueError("Missing exact supplemental original artifact: " + identifier)
            metadata, row = originals[artifact]
            page = pages[identifier]
            if ((metadata.get("model"), metadata.get("revision")) != (model, revision)
                    or (row.get("id"), row.get("source"), row.get("scan_page"), row.get("region")) !=
                    (identifier, page["source"], page["scan_page"], page["region"])):
                raise ValueError("Supplemental source identity changed")
            if row.get("error") or row.get("finish_reason") != ("length" if identifier == "dio-cary-v7-pdf0107" else "stop"):
                raise ValueError("Supplemental reviewed outcome changed")
            source = prior["sources"][page["source"]]
            if sha((pdf_dir / (page["source"] + ".pdf")).read_bytes()) != source["sha256"]:
                raise ValueError("Supplemental source PDF changed")
            checked[identifier] = {"artifact_sha256": artifact, "original_metadata": metadata,
                "original_prediction": row, "source_evidence": FINDINGS[identifier],
                "source_pdf_sha256": source["sha256"], "original_region": page["region"],
                "retry_regions": REGIONS[identifier]}
            for order, region in enumerate(REGIONS[identifier], 1):
                jobs.append({**page, "id": identifier + f"-supplement-strip-{order}",
                    "reconstructs": identifier, "reading_order": order,
                    "region": region, "max_side": 3200, "prompt_suffix": STRIP_PROMPT})
        request = {"schema_version": 1, "generated_by": "scripts/prepare_dio_ocr_supplements.py",
            "purpose": "Additional source-reviewed attempts; retain the unchanged first retry request and every original outcome.",
            "sources": prior["sources"], "prompt": prior["prompt"],
            "retry_of": {"path": PARENT if key == "child" else MANIFEST,
                "sha256": PARENT_SHA256 if key == "child" else MANIFEST_SHA256,
                "model": model, "revision": revision, "region_ids": list(pins)},
            "review": {"reviewed_at": "2026-10-18", "original_predictions": checked,
                "source_rendered_evidence": [EVIDENCE],
                "policy": "Require every complete successful strip and a completed source comparison. Retain the exact original prediction and all successful siblings. Replace this checkpoint's input once; never add a second vote or invent joined spelling."},
            "nonlexical_source_regions": {}, "pages": jobs}
        suffix = "qwen38-child-strip" if key == "child" else family + "-supplementary"
        path = output_dir / f"cassius-dio-{suffix}-retry-jobs.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(request))
        results[key] = request
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, action="append", required=True)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / DIRECTORY)
    args = parser.parse_args()
    result = prepare(ROOT, args.original, args.pdf_dir, args.output_dir)
    print(json.dumps({key: len(value["pages"]) for key, value in result.items()}))


if __name__ == "__main__":
    main()
