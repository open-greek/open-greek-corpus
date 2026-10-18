#!/usr/bin/env python3
"""Reproduce completed Dio source reviews over exact retained retry artifacts.

These constants record completed visual source inspections, not an automatic
approval of new OCR. Changed predictions require a new explicit source review.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from prepare_dio_ocr_retries import ROOT, DIRECTORY, MANIFEST, encode, sha
from dio_ocr_retries import write_reviewed_bundles
from ingest_scan_coverage import load_predictions

REVIEWED_AT = '2026-10-18T09:25:32.068324+00:00'
RAW_PINS = {'cassius-dio-strips-provider-qwen36.jsonl': 'b9f29e5ffd9e797e6aa2a9148eb9e7df36a8332db790d8e5acc47ed9f87fc2c8',
 'cassius-dio-strips-provider-qwen38.jsonl': 'a1192f51e148a482d3439b69cfc127607f7365f20d1b6bea865017c46d94bd6b',
 'cassius-dio-supplementary-provider-qwen36.jsonl': '1e016984ca55dda1901044ed503bf90d2b160c8b0a3514344516a194ebe9a782',
 'cassius-dio-supplementary-provider-qwen38.jsonl': 'f8a83d56c66f74dd47fcc363b767341ab506b21ea0c84ef999fc788873250705',
 'cassius-dio-child-strip-provider-qwen38.jsonl': '4349058050f5b68dc2f61e7104e9571c30041e22b2fdd9287a0e5ec3c4b70a6f',
 'cassius-dio-main-finer-child-provider-qwen38.jsonl': '0c4c369da761848af82aa6d5f2bad2deb1e831bd1b4204a170d8b9d95dde22ac',
 'cassius-dio-supplementary-finer-child-provider-qwen36.jsonl': 'f3e7ce937619af7539cd85010d962ed1092777d0e8d6908d3620f784b8c41707',
 'cassius-dio-supplementary-finer-child-provider-qwen38.jsonl': '17bb6f8337e218e245b11a70c7829a8e3047d437485d5e247dc9d7fac9525cc3',
 'cassius-dio-vi206-grandchild-provider-qwen38.jsonl': '6d80def4a12d5ad3350a1f2733c063f38f1d0cf02351e2a8ee216b60ebcef602'}
ORIGINAL_PINS = {
    "qwen36": "9c3fb470b0aee5407521a4ca05e6ee8c640bca826551e5bc250b6a0b4dfef821",
    "qwen38": "14c578f1017a566f698d3689685a1b87fb6069ecb91ac1126a705e759f61804f",
}


def evidence(identifier, request, correction_sha):
    base = ("Compared every selected complete strip with the pinned Cary source: "
        "all printed body lines and Greek fragments are represented in source order; "
        "finite lacuna bands and reference credits remain. Known looping or degraded "
        "parents are held and replaced only by their exact reviewed descendants. "
        "Local OCR errors, mixed-script readings and differing dot counts remain "
        "raw variants for the independent consensus; this is not full proofreading. ")
    if identifier.startswith("dio-cary-v2-pdf0195"):
        return base + ("Residual polytonic loss in the first34-letter line remains "
            "explicit raw evidence. Admission requires the separately named merged "
            "scan review cary-zonaras-378-first-line-2026-10-18, authority "
            "data/ingest_reviews/coverage/dio-zonaras-378-line-review.json SHA256 " + correction_sha +
            ". That layer preserves the raw network, corrects only the inspected "
            "first line, and excludes initial τριος continuing preceding μέ- "
            "without inventing a joined spelling. It adds no model vote.")
    if identifier.startswith("dio-cary-v6-pdf0206"):
        return base + ("The first three printed lines still contain missing accents "
            "and a mixed-script reading in Qwen3.8 after finer attempts. Those exact "
            "lines lie wholly inside the already served55.9.2–55.9.4 prefix, which "
            "the unique βουληθεὶς δὲ δὴ τρόπον anchor removes before new primary "
            "admission. Their mark quality is not certified. They remain held "
            "overlap evidence alongside unchanged historical passages; the missing "
            "continuation after the anchor was checked separately for full body.")
    if "finer" in identifier or "child" in identifier:
        return base + ("The narrower source crop restores the Greek after the "
            "parent's unprinted repetition or lost marks. A single ellipsis per "
            "printed dot run is an explicit request-level punctuation normalization; "
            "the finite original dot runs remain in the pinned image and earlier raw.")
    return base


def prepare(root, raw_dir, output_dir, review_dir):
    for name, expected in RAW_PINS.items():
        if sha((raw_dir / name).read_bytes()) != expected:
            raise ValueError("A completed source-reviewed Dio retry artifact changed: " + name)
    correction_sha = sha((root / "data/ingest_reviews/coverage/dio-zonaras-378-line-review.json").read_bytes())
    directory = root / DIRECTORY
    def config(request_name, raw_name, children=()):
        request_path = directory / request_name
        request = json.loads(request_path.read_bytes())
        return {"request_path": request_path, "retry_path": raw_dir / raw_name,
            "review_path": review_dir / (Path(request_name).stem + "-completed.json"),
            "source_evidence": {identifier: evidence(identifier, request, correction_sha)
                for identifier in request["review"]["original_predictions"]},
            "children": list(children)}
    parts = {
        "qwen36": [config("cassius-dio-qwen36-retry-jobs.json", "cassius-dio-strips-provider-qwen36.jsonl"),
            config("cassius-dio-qwen36-supplementary-retry-jobs.json", "cassius-dio-supplementary-provider-qwen36.jsonl", [
                config("cassius-dio-qwen36-supplementary-finer-child-jobs.json", "cassius-dio-supplementary-finer-child-provider-qwen36.jsonl")])],
        "qwen38": [config("cassius-dio-qwen38-retry-jobs.json", "cassius-dio-strips-provider-qwen38.jsonl", [
                config("cassius-dio-qwen38-child-strip-retry-jobs.json", "cassius-dio-child-strip-provider-qwen38.jsonl", [
                    config("cassius-dio-qwen38-vi206-grandchild-jobs.json", "cassius-dio-vi206-grandchild-provider-qwen38.jsonl")]),
                config("cassius-dio-qwen38-main-finer-child-jobs.json", "cassius-dio-main-finer-child-provider-qwen38.jsonl")]),
            config("cassius-dio-qwen38-supplementary-retry-jobs.json", "cassius-dio-supplementary-provider-qwen38.jsonl", [
                config("cassius-dio-qwen38-supplementary-finer-child-jobs.json", "cassius-dio-supplementary-finer-child-provider-qwen38.jsonl")])],
    }
    def load(raw, manifest_bytes, manifest, *, allow_failed_ids=frozenset()):
        return load_predictions(None, manifest_bytes, manifest, raw, allow_failed_ids=allow_failed_ids)
    output = {}
    for family, configs in parts.items():
        original = root / "data/evaluation/ocr-fresh" / f"cassius-dio-original-{family}.bundle.json"
        if sha(original.read_bytes()) != ORIGINAL_PINS[family]:
            raise ValueError("The complete original Dio bundle changed")
        path = output_dir / f"cassius-dio-reviewed-{family}.bundle.json"
        output[family] = write_reviewed_bundles(original, root / MANIFEST, configs, path, REVIEWED_AT, load)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/evaluation/ocr-fresh")
    parser.add_argument("--review-dir", type=Path, default=ROOT / DIRECTORY / "completed-dio-retries")
    args = parser.parse_args()
    result = prepare(ROOT, args.raw_dir, args.output_dir, args.review_dir)
    print(json.dumps({key: {"pages": len(value["replaced_page_ids"]), "sha256": value["bundle_sha256"]}
        for key,value in result.items()}))
