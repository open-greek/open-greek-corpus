#!/usr/bin/env python3
"""Retain all original Qwen3.8 math parts and one reviewed page replacement."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from mathematical_ocr_retries import KIND, _decode, _pack, assemble, validate_retry_records, values
from prepare_mathematical_ocr_retries import MANIFEST, MANIFEST_SHA256, encode, sha
from prepare_mathematical_qwen38_retry import MODEL, REVISION, PAGE_ID, REGIONS, OUTPUT, SOURCE_PART_SHA256

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / OUTPUT
FAMILY = "qwen3.8-27b"
DECISION = "replace-only-source-reviewed-Qwen3.8-page345-attempt"


def _checked(raw, manifest_bytes, manifest, load_leaf):
    bundle = json.loads(raw)
    if bundle.get("kind") != KIND or bundle.get("retry_family") != FAMILY or bundle.get("schema_version") != 1:
        raise ValueError("Unrecognized Qwen3.8 mathematical retry bundle")
    request_raw = _decode(bundle["request"])
    if request_raw != AUTHORITY.read_bytes() or sha(manifest_bytes) != MANIFEST_SHA256:
        raise ValueError("Qwen3.8 mathematical source authority changed")
    request = json.loads(request_raw)
    original_raw, source_raw = _decode(bundle["original"]), _decode(bundle["source_part"])
    retry_raw, review_raw = _decode(bundle["retry"]), _decode(bundle["source_review"])
    review = json.loads(review_raw)
    if (sha(source_raw) != SOURCE_PART_SHA256 or request["retry_of"]["source_part_sha256"] != SOURCE_PART_SHA256
            or request["retry_of"]["sha256"] != MANIFEST_SHA256 or request["sources"] != manifest["sources"]
            or request["prompt"] != manifest["prompt"]):
        raise ValueError("Original complete shard or source edition changed")
    if (review.get("decision") != DECISION or not review.get("reviewed_at") or not review.get("source_evidence", "").strip()
            or review.get("original_sha256") != sha(original_raw) or review.get("source_part_sha256") != sha(source_raw)
            or review.get("retry_sha256") != sha(retry_raw) or review.get("manifest_sha256") != sha(manifest_bytes)
            or review.get("retry_manifest_sha256") != sha(request_raw)):
        raise ValueError("Qwen3.8 retry lacks a completed source review of the exact inputs")
    metadata, source_rows = values(source_raw)
    source_by_id = {r["id"]: r for r in source_rows}
    if (len(source_rows) != 102 or len(source_by_id) != 102 or PAGE_ID not in source_by_id or
            (metadata.get("model"), metadata.get("revision"), metadata.get("prompt"), metadata.get("manifest_sha256")) !=
            (MODEL, REVISION, manifest["prompt"], MANIFEST_SHA256)):
        raise ValueError("Pinned original Qwen3.8 shard identity changed")
    source_row = source_by_id[PAGE_ID]
    if (sha(encode(source_row)) != request["review"]["original_prediction_sha256"] or
            source_row["image_sha256"] != request["review"]["original_image_sha256"] or
            source_row["raw_prediction"] != request["review"]["original_text"]):
        raise ValueError("Original degraded source page changed")
    _, strips = validate_retry_records(retry_raw, request_raw, request, model=MODEL, revision=REVISION)
    jobs = sorted(request["pages"], key=lambda p: p["reading_order"])
    if [p["region"] for p in jobs] != REGIONS or [p["reading_order"] for p in jobs] != [1,2,3] or {p["reconstructs"] for p in jobs} != {PAGE_ID}:
        raise ValueError("Unreviewed Qwen3.8 crop geometry")
    strips_by_id = {r["id"]: r for r in strips}
    ordered = [strips_by_id[p["id"]] for p in jobs]
    if (review.get("strip_sha256s") != [sha(encode(r)) for r in ordered] or
            review.get("image_sha256s") != [r["image_sha256"] for r in ordered] or
            review.get("assembled_text_sha256") != sha(assemble(ordered).encode())):
        raise ValueError("Qwen3.8 source review refers to different strip readings or images")
    result, _ = load_leaf(original_raw, manifest_bytes, manifest)
    source, _ = load_leaf(source_raw, manifest_bytes, manifest)
    load_leaf(retry_raw, request_raw, request)
    if (len(result) != 556 or set(result) != {p["id"] for p in manifest["pages"]}
            or any(w.get("model") != MODEL or w.get("revision") != REVISION or w.get("vote_group") != FAMILY for w in result.values())
            or result[PAGE_ID] != source[PAGE_ID]):
        raise ValueError("Complete Qwen3.8 input does not retain the exact original page artifact once")
    return result, request_raw, request, original_raw, source_raw, retry_raw, review_raw, review, ordered


def load_bundle(raw, manifest_bytes, manifest, load_leaf):
    result, request_raw, request, original_raw, source_raw, retry_raw, review_raw, review, strips = _checked(raw, manifest_bytes, manifest, load_leaf)
    original = result[PAGE_ID]
    text = assemble(strips)
    evidence = {"kind": "source-reviewed-strip-assembly", "original_text": original["text"], "corrected_text": text,
        "source_evidence": review["source_evidence"], "reviewed_at": review["reviewed_at"],
        "source_pdf_sha256": request["review"]["source_pdf_sha256"],
        "original_artifact_sha256": original["artifact_sha256"], "original_bundle_sha256": sha(original_raw),
        "source_part_sha256": sha(source_raw), "retry_run_sha256": sha(retry_raw),
        "retry_manifest_sha256": sha(request_raw), "source_review_sha256": sha(review_raw),
        "reading_order": [p["id"] for p in sorted(request["pages"], key=lambda p: p["reading_order"])], "raw_strips": strips,
        "policy": "One reviewed assembly replaces the same Qwen3.8 input. The full original bundle, degraded source shard, all retries and review remain archived; other model witnesses are not selected or changed."}
    result[PAGE_ID] = {**original, "text": text,
        "artifact_sha256": sha(encode({"original": original, "reviewed_assembly": evidence})),
        "original_image_sha256": original["image_sha256"], "retry_image_sha256s": [p["image_sha256"] for p in strips],
        "preprocessing": [*original.get("preprocessing", []), evidence]}
    return result, raw


def describe_bundle(raw):
    bundle = json.loads(raw)
    review = json.loads(_decode(bundle["source_review"]))
    return {"kind": KIND, "retry_family": FAMILY, "bundle_sha256": sha(raw), "model": MODEL, "revision": REVISION,
        "original_sha256": bundle["original"]["sha256"], "source_part_sha256": bundle["source_part"]["sha256"],
        "retry_sha256": bundle["retry"]["sha256"], "retry_manifest_sha256": bundle["request"]["sha256"],
        "source_review_sha256": bundle["source_review"]["sha256"], "reviewed_at": review["reviewed_at"],
        "replaced_page_ids": [PAGE_ID], "policy": "One reviewed Qwen3.8 input; all original attempts retained."}


def write_reviewed_bundle(original, source_part, retry, manifest, review_path, output, evidence, reviewed_at, load_leaf):
    if output.exists() or review_path.exists():
        raise ValueError("Refusing to replace an existing reviewed Qwen3.8 artifact")
    if not evidence.strip():
        raise ValueError("Describe the completed source comparison of all three strips")
    request_raw = AUTHORITY.read_bytes()
    request = json.loads(request_raw)
    original_raw, source_raw, retry_raw = original.read_bytes(), source_part.read_bytes(), retry.read_bytes()
    _, strips = validate_retry_records(retry_raw, request_raw, request, model=MODEL, revision=REVISION)
    by_id = {r["id"]: r for r in strips}
    ordered = [by_id[p["id"]] for p in sorted(request["pages"], key=lambda p: p["reading_order"])]
    review = {"schema_version": 1, "decision": DECISION, "reviewed_at": reviewed_at, "source_evidence": evidence,
        "original_sha256": sha(original_raw), "source_part_sha256": sha(source_raw), "retry_sha256": sha(retry_raw),
        "manifest_sha256": MANIFEST_SHA256, "retry_manifest_sha256": sha(request_raw),
        "strip_sha256s": [sha(encode(r)) for r in ordered], "image_sha256s": [r["image_sha256"] for r in ordered],
        "assembled_text_sha256": sha(assemble(ordered).encode())}
    bundle = {"schema_version": 1, "kind": KIND, "retry_family": FAMILY,
        "request": _pack(request_raw), "original": _pack(original_raw), "source_part": _pack(source_raw),
        "retry": _pack(retry_raw), "source_review": _pack(encode(review))}
    raw, manifest_raw = encode(bundle), manifest.read_bytes()
    load_bundle(raw, manifest_raw, json.loads(manifest_raw), load_leaf)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes(encode(review))
    output.write_bytes(raw)
    return describe_bundle(raw)


def main():
    from datetime import datetime, timezone
    from ingest_scan_coverage import load_predictions
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, required=True, help="Complete original Qwen3.8 556-page bundle")
    p.add_argument("--source-part", type=Path, required=True, help="Unchanged original shard03")
    p.add_argument("--retry", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=ROOT / MANIFEST)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-evidence", required=True)
    a = p.parse_args()
    def leaf(raw, manifest_raw, manifest):
        return load_predictions(None, manifest_raw, manifest, raw)
    print(json.dumps(write_reviewed_bundle(a.original, a.source_part, a.retry, a.manifest, a.review, a.out,
        a.source_evidence, datetime.now(timezone.utc).isoformat(), leaf), ensure_ascii=False))


if __name__ == "__main__":
    main()
