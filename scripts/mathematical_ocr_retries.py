#!/usr/bin/env python3
"""Admit only explicitly source-reviewed mathematical retry assemblies.

A bundle embeds every byte of the original full run, the bounded retry, its
request and the completed review. It changes one input per model, never adds
an independent vote and never selects a reading by a detector score.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path

from prepare_mathematical_ocr_retries import (
    MODEL, REVISION, MANIFEST_SHA256, ORIGINAL_SHA256, OUTPUT, REGIONS, encode, sha)

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / OUTPUT
KIND = "source-reviewed-mathematical-retry-bundle"
DECISION = "replace-only-source-reviewed-Qwen3.6-attempts"


def values(raw):
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not rows or set(rows[0]) != {"_meta"} or any("_meta" in r for r in rows[1:]):
        raise ValueError("Prediction metadata is missing or repeated")
    return rows[0]["_meta"], rows[1:]


def _decode(item):
    raw = base64.b64decode(item["raw_base64"], validate=True)
    if sha(raw) != item["sha256"]:
        raise ValueError("Archived mathematical retry bytes changed")
    return raw


def _pack(raw):
    return {"sha256": sha(raw), "raw_base64": base64.b64encode(raw).decode()}


def validate_retry_records(raw, request_raw, request, *, model=MODEL, revision=REVISION):
    metadata, rows = values(raw)
    if (metadata.get("model"), metadata.get("revision"), metadata.get("prompt"), metadata.get("manifest_sha256")) != (model, revision, request["prompt"], sha(request_raw)):
        raise ValueError("Mathematical retry model, checkpoint, prompt or request changed")
    jobs = {p["id"]: p for p in request["pages"]}
    if len(rows) != len(jobs) or {r["id"] for r in rows} != set(jobs):
        raise ValueError("Every reviewed strip must occur exactly once")
    for row in rows:
        job = jobs[row["id"]]
        if row.get("error") or row.get("finish_reason") != "stop" or not row.get("raw_prediction", "").strip():
            raise ValueError("Failed, empty or truncated OCR strip cannot receive a completed source review")
        if (row.get("source"), row.get("scan_page"), row.get("region")) != (job["source"], job["scan_page"], job["region"]):
            raise ValueError("Unchecked source geometry in mathematical retry")
        if row.get("prompt_sha256") != sha(request["prompt"].encode()) or not isinstance(row.get("image_sha256"), str) or len(row["image_sha256"]) != 64:
            raise ValueError("Retry strip prompt or source-image identity changed")
    return metadata, rows


def _checked(raw, manifest_bytes, manifest):
    bundle = json.loads(raw)
    if bundle.get("kind") != KIND or bundle.get("schema_version") != 1:
        raise ValueError("Unrecognized mathematical retry bundle")
    request_raw = _decode(bundle["request"])
    if request_raw != AUTHORITY.read_bytes():
        raise ValueError("Mathematical retry request differs from its committed source authority")
    request = json.loads(request_raw)
    original_raw, retry_raw = _decode(bundle["original"]), _decode(bundle["retry"])
    review_raw = _decode(bundle["source_review"])
    review = json.loads(review_raw)
    if (sha(manifest_bytes) != MANIFEST_SHA256 or sha(original_raw) != ORIGINAL_SHA256 or
            request["retry_of"]["sha256"] != MANIFEST_SHA256 or
            request["retry_of"]["original_predictions_sha256"] != ORIGINAL_SHA256 or
            request["sources"] != manifest["sources"] or request["prompt"] != manifest["prompt"]):
        raise ValueError("Original request, source editions or complete556 attempt changed")
    if (review.get("decision") != DECISION or not review.get("reviewed_at") or
            review.get("original_sha256") != sha(original_raw) or
            review.get("retry_sha256") != sha(retry_raw) or
            review.get("manifest_sha256") != sha(manifest_bytes) or
            review.get("retry_manifest_sha256") != sha(request_raw)):
        raise ValueError("Retry lacks a completed review of these exact input bytes")
    original_meta, originals = values(original_raw)
    retry_meta, retries = validate_retry_records(retry_raw, request_raw, request)
    for meta in (original_meta, retry_meta):
        if (meta.get("model"), meta.get("revision"), meta.get("prompt")) != (MODEL, REVISION, manifest["prompt"]):
            raise ValueError("Mathematical retry model, checkpoint or prompt changed")
    if original_meta.get("manifest_sha256") != sha(manifest_bytes) or retry_meta.get("manifest_sha256") != sha(request_raw):
        raise ValueError("A mathematical attempt used the wrong request")
    original_by_id = {p["id"]: p for p in originals}
    jobs = {p["id"]: p for p in request["pages"]}
    retry_by_id = {p["id"]: p for p in retries}
    if (len(originals) != 556 or len(original_by_id) != 556 or
            set(original_by_id) != {p["id"] for p in manifest["pages"]} or
            len(retries) != len(jobs) or set(retry_by_id) != set(jobs) or
            set(review.get("pages", {})) != set(REGIONS)):
        raise ValueError("Original complete pages or reviewed retry strip set changed")
    for identifier, regions in REGIONS.items():
        ordered = sorted((p for p in jobs.values() if p["reconstructs"] == identifier), key=lambda p: p["reading_order"])
        if [p["region"] for p in ordered] != regions or [p["reading_order"] for p in ordered] != [1,2,3]:
            raise ValueError("Unreviewed mathematical crop geometry")
        original = original_by_id[identifier]
        finding = request["review"]["findings"][identifier]
        page_review = review["pages"][identifier]
        strips = [retry_by_id[p["id"]] for p in ordered]
        if (sha(encode(original)) != finding["original_prediction_sha256"] or
                original["image_sha256"] != finding["original_image_sha256"] or
                original["raw_prediction"] != finding["original_text"] or
                page_review.get("original_prediction_sha256") != sha(encode(original)) or
                not page_review.get("source_evidence", "").strip()):
            raise ValueError("Page review does not identify the original attempt and source evidence")
        if page_review.get("strip_sha256s") != [sha(encode(p)) for p in strips] or page_review.get("image_sha256s") != [p["image_sha256"] for p in strips]:
            raise ValueError("Source review refers to different strip predictions or images")
        if page_review.get("assembled_text_sha256") != sha(assemble(strips).encode()):
            raise ValueError("Reviewed assembled text changed")
    return bundle, request_raw, request, original_raw, retry_raw, review_raw, review, original_by_id, retry_by_id


def assemble(strips):
    return "\n".join(row["raw_prediction"].strip() for row in strips)


def load_bundle(raw, manifest_bytes, manifest, load_leaf):
    """Return the ordinary loader's witness mapping plus unchanged bundle bytes.

    load_leaf(raw, manifest_bytes, manifest) validates ordinary OCR records and
    returns (witnesses, raw). Calling it on both embedded files keeps this
    helper independent of the corpus admission module.
    """
    if json.loads(raw).get("retry_family") == "qwen3.8-27b":
        from mathematical_qwen38_retry import load_bundle as load_qwen38
        return load_qwen38(raw, manifest_bytes, manifest, load_leaf)
    bundle, request_raw, request, original_raw, retry_raw, review_raw, review, originals, retries = _checked(raw, manifest_bytes, manifest)
    result, _ = load_leaf(original_raw, manifest_bytes, manifest)
    load_leaf(retry_raw, request_raw, request)
    for identifier in REGIONS:
        jobs = sorted((p for p in request["pages"] if p["reconstructs"] == identifier), key=lambda p: p["reading_order"])
        strips = [retries[p["id"]] for p in jobs]
        original = result[identifier]
        text = assemble(strips)
        evidence = {"kind": "source-reviewed-strip-assembly",
            "original_text": originals[identifier]["raw_prediction"], "corrected_text": text,
            "source_evidence": review["pages"][identifier]["source_evidence"],
            "reviewed_at": review["reviewed_at"],
            "source_pdf_sha256": request["sources"][jobs[0]["source"]]["sha256"],
            "original_artifact_sha256": original["artifact_sha256"],
            "original_run_sha256": sha(original_raw), "retry_run_sha256": sha(retry_raw),
            "retry_manifest_sha256": sha(request_raw), "source_review_sha256": sha(review_raw),
            "reading_order": [p["id"] for p in jobs], "raw_strips": strips,
            "policy": "The reviewed assembly replaces this model's original input once; every original and retry byte remains in the admission bundle. No other model is selected or removed."}
        result[identifier] = {**original, "text": text,
            "artifact_sha256": sha(encode({"original": original, "reviewed_assembly": evidence})),
            "original_image_sha256": original["image_sha256"],
            "retry_image_sha256s": [p["image_sha256"] for p in strips],
            "preprocessing": [*original.get("preprocessing", []), evidence]}
    return result, raw


def describe_bundle(raw):
    bundle = json.loads(raw)
    if bundle.get("retry_family") == "qwen3.8-27b":
        from mathematical_qwen38_retry import describe_bundle as describe_qwen38
        return describe_qwen38(raw)
    review = json.loads(_decode(bundle["source_review"]))
    return {"kind": KIND, "bundle_sha256": sha(raw), "model": MODEL, "revision": REVISION,
        "original_sha256": bundle["original"]["sha256"], "retry_sha256": bundle["retry"]["sha256"],
        "retry_manifest_sha256": bundle["request"]["sha256"],
        "source_review_sha256": bundle["source_review"]["sha256"],
        "reviewed_at": review["reviewed_at"], "replaced_page_ids": list(REGIONS),
        "policy": "One reviewed assembly per original model input; all original attempts retained."}


def write_review(original, retry, source_evidence, output, reviewed_at):
    """Record a completed pixel comparison, never infer approval from scores."""
    if output.exists():
        raise ValueError("Refusing to replace an existing completed source review")
    original_raw, retry_raw, request_raw = original.read_bytes(), retry.read_bytes(), AUTHORITY.read_bytes()
    request = json.loads(request_raw)
    _, rows = values(original_raw)
    _, retries = validate_retry_records(retry_raw, request_raw, request)
    originals, strips = {r["id"]: r for r in rows}, {r["id"]: r for r in retries}
    if set(source_evidence) != set(REGIONS) or any(not str(e).strip() for e in source_evidence.values()):
        raise ValueError("Every reviewed page needs its completed source comparison")
    review = {"schema_version": 1, "decision": DECISION, "reviewed_at": reviewed_at,
        "original_sha256": sha(original_raw), "retry_sha256": sha(retry_raw),
        "manifest_sha256": MANIFEST_SHA256, "retry_manifest_sha256": sha(request_raw), "pages": {}}
    for identifier in REGIONS:
        jobs = sorted((p for p in request["pages"] if p["reconstructs"] == identifier), key=lambda p: p["reading_order"])
        selected = [strips[p["id"]] for p in jobs]
        review["pages"][identifier] = {"original_prediction_sha256": sha(encode(originals[identifier])),
            "strip_sha256s": [sha(encode(p)) for p in selected],
            "image_sha256s": [p["image_sha256"] for p in selected],
            "assembled_text_sha256": sha(assemble(selected).encode()),
            "source_evidence": source_evidence[identifier]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encode(review))
    return review


def write_bundle(original, retry, review, manifest, output, load_leaf):
    if output.exists():
        raise ValueError("Refusing to replace an existing mathematical retry bundle")
    bundle = {"schema_version": 1, "kind": KIND, "original": _pack(original.read_bytes()),
        "retry": _pack(retry.read_bytes()), "request": _pack(AUTHORITY.read_bytes()),
        "source_review": _pack(review.read_bytes())}
    raw, manifest_raw = encode(bundle), manifest.read_bytes()
    load_bundle(raw, manifest_raw, json.loads(manifest_raw), load_leaf)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return describe_bundle(raw)


def main():
    from datetime import datetime, timezone
    from ingest_scan_coverage import load_predictions
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--retry", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/ingest_reviews/coverage/mathematical-ocr-jobs.json")
    parser.add_argument("--source-evidence", type=Path, help="JSON object mapping all five page IDs to completed scan-comparison evidence")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.source_evidence:
        write_review(args.original, args.retry, json.loads(args.source_evidence.read_text()), args.review, datetime.now(timezone.utc).isoformat())
    def leaf(raw, manifest_raw, manifest):
        return load_predictions(None, manifest_raw, manifest, raw)
    print(json.dumps(write_bundle(args.original, args.retry, args.review, args.manifest, args.out, leaf), ensure_ascii=False))


if __name__ == "__main__":
    main()
