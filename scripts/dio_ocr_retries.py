#!/usr/bin/env python3
"""Replace only explicitly source-reviewed Dio inputs, retaining all attempts.

The complete original bundle is inspected before any failure exception is
requested. Only exact pinned length failures may pass the private
loader exception, and every one must be replaced by successful reviewed strips.
Ordinary prediction loading and every other failure remain strict.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITIES = {family: ROOT / f"data/ingest_reviews/coverage/cassius-dio-{family}-retry-jobs.json"
               for family in ["qwen36", "qwen38"]}
CHECKPOINTS = {
    "qwen36": ("Qwen/Qwen3.6-27B-FP8", "e89b16ebf1988b3d6befa7de50abc2d76f26eb09", "qwen3.6-27b"),
    "qwen38": ("Qwen/Qwen3.8-27B-FP8", "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a", "qwen3.8-27b"),
}
KIND = "source-reviewed-dio-retry-bundle"
DECISION = "replace-only-explicit-source-reviewed-Dio-inputs"
MANIFEST_PATH = "data/ingest_reviews/coverage/cassius-dio-reviewed-ocr-jobs.json"
# This approval is separate from the original greedy transcription runner.
# Preserve the complete policy object and original runner hashes in every raw
# retry; a future decoder requires a separately reviewed policy version.
RETRY_RUNNER_SHA256 = "70f0361c5dfcb8a2ec2e91385a4bf881afa93777c088a48a0435a52782334125"
IMAGE_HELPER_SHA256 = "061455bce85cb1b770bbb68a2819b06e4da9e637856a05d402559c861154c5e4"
GENERATION_POLICY = {
    "id": "qwen-provider-instruct-retry-2026-10-18",
    "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
    "presence_penalty": 1.5, "repetition_penalty": 1.0, "seed": 20261018,
    "chat_template_kwargs": {"enable_thinking": False},
    "source_urls": ["https://huggingface.co/Qwen/Qwen3.6-27B#best-practices",
                    "https://huggingface.co/Qwen/Qwen3.8-27B-FP8#best-practices"],
    "scope": "Source-reviewed retry only; no automatic replacement or benchmark change.",
    "limits": "Provider settings may alter wording or mix scripts; every accepted outcome needs source comparison. A fixed seed does not guarantee identical results across hardware or batch schedules.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def retained(raw):
    return {"sha256": sha(raw), "encoding": "gzip-base64", "data": base64.b64encode(gzip.compress(raw, mtime=0)).decode()}


def unpack(item):
    if item.get("encoding") != "gzip-base64":
        raise ValueError("Unknown retained Dio artifact encoding")
    raw = gzip.decompress(base64.b64decode(item["data"], validate=True))
    if sha(raw) != item.get("sha256"):
        raise ValueError("Retained Dio artifact bytes changed")
    return raw


def records(raw):
    values = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not values or set(values[0]) != {"_meta"} or any("_meta" in row for row in values[1:]):
        raise ValueError("Dio OCR runtime metadata is missing or repeated")
    return values[0]["_meta"], values[1:]


def failed(row):
    return bool(row.get("error") or row.get("finish_reason") != "stop" or not row.get("raw_prediction", "").strip())


def authority(manifest_bytes, manifest, request_raw):
    matches = [key for key, path in AUTHORITIES.items() if path.exists() and path.read_bytes() == request_raw]
    if len(matches) != 1:
        raise ValueError("Dio retry differs from its committed checkpoint-specific source authority")
    key = matches[0]
    model, revision, family = CHECKPOINTS[key]
    request = json.loads(request_raw)
    request_pin = request["retry_of"]
    if (request_pin.get("path") != MANIFEST_PATH or request_pin.get("sha256") != sha(manifest_bytes)
            or (request_pin.get("model"), request_pin.get("revision")) != (model, revision)
            or len(manifest["pages"]) != 1500 or len({p["id"] for p in manifest["pages"]}) != 1500):
        raise ValueError("Dio complete request or pinned checkpoint changed")
    originals = request["review"]["original_predictions"]
    if not originals:
        raise ValueError("A Dio retry needs explicit source-reviewed original page artifacts")
    pages = {p["id"]: p for p in manifest["pages"]}
    groups, failed_ids = {}, set()
    for identifier, pin in originals.items():
        page = pages.get(identifier)
        if not page or page.get("work") != "cassius-dio.historiae-romanae":
            raise ValueError("Dio retry target changed its source identity")
        metadata, row = pin["original_metadata"], pin["original_prediction"]
        if (sha(encode({"metadata": metadata, "prediction": row})) != pin.get("artifact_sha256") or
                (metadata.get("model"), metadata.get("revision")) != (model, revision) or
                (row.get("id"), row.get("source"), row.get("scan_page")) !=
                (identifier, page["source"], page["scan_page"]) or
                not pin.get("source_evidence", "").strip()):
            raise ValueError("Dio original artifact lacks an exact source-reviewed pin")
        if row.get("finish_reason") == "length" and not row.get("error"):
            failed_ids.add(identifier)
        elif failed(row):
            raise ValueError("Dio source review does not authorize an unknown failure outcome")
        jobs = sorted((p for p in request["pages"] if p.get("reconstructs") == identifier), key=lambda p: p["reading_order"])
        if len(jobs) != 3 or [p["reading_order"] for p in jobs] != [1,2,3]:
            raise ValueError("Dio retry requires every reviewed strip exactly once")
        for job in jobs:
            if ((job["source"], job["scan_page"], job.get("source_volume")) !=
                    (page["source"], page["scan_page"], page["source_volume"]) or
                    request["sources"][job["source"]] != manifest["sources"][page["source"]]):
                raise ValueError("Dio strip changed the reviewed source edition")
        groups[identifier] = jobs
    if len(request["pages"]) != 3 * len(originals) or len({p["id"] for p in request["pages"]}) != len(request["pages"]):
        raise ValueError("Dio reviewed strip set changed")
    scope = {"key": key, "model": model, "revision": revision, "family": family,
             "targets": set(originals), "failed_ids": frozenset(failed_ids)}
    return request, originals, groups, scope


def inspect_original(original_raw, manifest_bytes, manifest, pins, scope):
    """Resolve exact eligible artifacts before authorizing exact private failures."""
    from scan_ocr_bundle import load_bundle as inspect
    eligible, audit = inspect(original_raw, manifest_bytes)
    if (set(eligible) != {p["id"] for p in manifest["pages"]} or len(eligible) != 1500 or
            audit["checkpoints"] != [[scope["model"], scope["revision"]]]):
        raise ValueError("Dio original bundle must retain all 1500 regions from the pinned checkpoint")
    held = {(p["raw_part_sha256"], p["original_manifest_sha256"], p["id"]) for p in audit["held_predictions"]}
    artifacts = {}
    for identifier, pin in pins.items():
        parts = [p for p in audit["parts"] if identifier in p["ids"] and
                 (p["raw_sha256"], p["manifest_sha256"], identifier) not in held]
        if len(parts) != 1:
            raise ValueError("Dio original source page does not have one eligible part")
        metadata, row = parts[0]["metadata"], eligible[identifier]
        artifact = sha(encode({"metadata": metadata, "prediction": row}))
        if metadata != pin["original_metadata"] or row != pin["original_prediction"] or artifact != pin["artifact_sha256"]:
            raise ValueError("Dio original page differs from its exact source-reviewed artifact")
        artifacts[identifier] = artifact
    failures = {identifier for identifier, row in eligible.items() if failed(row)}
    if failures != set(scope["failed_ids"]):
        raise ValueError("An unreviewed failed Dio input cannot be admitted")
    return eligible, audit, artifacts


def checked_retry(retry_raw, request_raw, request, groups, scope, load_leaf):
    metadata, rows = records(retry_raw)
    if (metadata.get("model"), metadata.get("revision"), metadata.get("manifest_sha256"), metadata.get("prompt")) != (scope["model"], scope["revision"], sha(request_raw), request["prompt"]):
        raise ValueError("Dio retry model, checkpoint, prompt or request changed")
    if (metadata.get("generation_policy") != GENERATION_POLICY or metadata.get("temperature") != GENERATION_POLICY["temperature"]
            or metadata.get("max_tokens") != 6000 or metadata.get("backend") != "http"
            or metadata.get("runner") != "scripts/run_reviewed_scan_retry.py"
            or metadata.get("runner_sha256") != RETRY_RUNNER_SHA256
            or metadata.get("image_helper_sha256") != IMAGE_HELPER_SHA256
            or (metadata.get("runtime", {}).get("model"), metadata.get("runtime", {}).get("revision")) !=
               (scope["model"], scope["revision"])):
        raise ValueError("Dio retry decoding policy, original image helper or server checkpoint changed")
    selected = {p["id"]: p for jobs in groups.values() for p in jobs}
    by_id = {p["id"]: p for p in rows}
    if len(rows) != len(selected) or set(by_id) != set(selected) or any(failed(row) for row in rows):
        raise ValueError("Dio retry requires every successful complete reviewed strip")
    # This ordinary loader supplies the existing exact prompt, image and crop
    # checks; no failed IDs are allowed on any retry strip.
    result, _ = load_leaf(retry_raw, request_raw, request)
    if set(result) != set(selected):
        raise ValueError("Dio strict retry loader changed region identities")
    return {identifier: [by_id[p["id"]] for p in jobs] for identifier, jobs in groups.items()}


def assemble(strips):
    return "\n".join(row["raw_prediction"].strip() for row in strips)


def load_bundle(raw, manifest_bytes, manifest, load_leaf):
    bundle = json.loads(raw)
    if bundle.get("kind") != KIND or bundle.get("schema_version") != 1:
        raise ValueError("Unrecognized reviewed Dio retry bundle")
    request_raw = unpack(bundle["request"])
    request, pins, groups, scope = authority(manifest_bytes, manifest, request_raw)
    original_raw, retry_raw, review_raw = unpack(bundle["original"]), unpack(bundle["retry"]), unpack(bundle["source_review"])
    review = json.loads(review_raw)
    if (review.get("decision") != DECISION or not review.get("reviewed_at") or
            review.get("manifest_sha256") != sha(manifest_bytes) or review.get("request_sha256") != sha(request_raw) or
            review.get("original_bundle_sha256") != sha(original_raw) or review.get("retry_sha256") != sha(retry_raw) or
            set(review.get("pages", {})) != scope["targets"]):
        raise ValueError("Dio retry lacks a completed source review of the exact inputs")
    eligible, _, artifacts = inspect_original(original_raw, manifest_bytes, manifest, pins, scope)
    strips = checked_retry(retry_raw, request_raw, request, groups, scope, load_leaf)
    for identifier in sorted(scope["targets"]):
        page_review = review["pages"][identifier]
        if (page_review.get("original_artifact_sha256") != artifacts[identifier] or
                not page_review.get("source_evidence", "").strip() or
                page_review.get("strip_sha256s") != [sha(encode(r)) for r in strips[identifier]] or
                page_review.get("image_sha256s") != [r["image_sha256"] for r in strips[identifier]] or
                page_review.get("assembled_text_sha256") != sha(assemble(strips[identifier]).encode())):
            raise ValueError("Dio completed page review refers to different artifacts or strips")
    # The exceptions are requested only after all exact artifact pins and
    # successful replacements passed. The ordinary default remains empty.
    result, _ = load_leaf(original_raw, manifest_bytes, manifest, allow_failed_ids=scope["failed_ids"])
    if set(result) != set(eligible):
        raise ValueError("Dio original loader changed the complete region set")
    for identifier in sorted(scope["targets"]):
        original = result[identifier]
        if original["artifact_sha256"] != artifacts[identifier] or original["text"] != eligible[identifier]["raw_prediction"]:
            raise ValueError("Dio loader changed the original artifact identity")
        text = assemble(strips[identifier])
        evidence = {"kind": "source-reviewed-strip-assembly", "original_text": original["text"], "corrected_text": text,
            "source_evidence": review["pages"][identifier]["source_evidence"], "reviewed_at": review["reviewed_at"],
            "original_outcome": {key: eligible[identifier].get(key) for key in ["finish_reason", "error", "generation_tokens"]},
            "original_artifact_sha256": artifacts[identifier], "original_bundle_sha256": sha(original_raw),
            "request_sha256": sha(request_raw), "retry_sha256": sha(retry_raw), "source_review_sha256": sha(review_raw),
            "source_pdf_sha256": request["sources"][groups[identifier][0]["source"]]["sha256"],
            "raw_strips": strips[identifier], "reading_order": [p["id"] for p in groups[identifier]],
            "nonlexical_source_regions": request.get("nonlexical_source_regions", {}).get(identifier, []),
            "policy": "Replace this pinned model input once with source-reviewed successful strips; retain the entire original bundle, failed attempts, source reviews and all independent model readings."}
        result[identifier] = {**original, "text": text,
            "artifact_sha256": sha(encode({"original": original, "reviewed_assembly": evidence})),
            "original_image_sha256": original["image_sha256"], "retry_image_sha256s": [r["image_sha256"] for r in strips[identifier]],
            "preprocessing": [*original.get("preprocessing", []), evidence]}
    if any(w.get("model") != scope["model"] or w.get("revision") != scope["revision"] or w.get("vote_group") != scope["family"] for w in result.values()):
        raise ValueError("Dio replacement changed the model or added a different voting family")
    return result, raw


def describe_bundle(raw):
    bundle = json.loads(raw)
    review = json.loads(unpack(bundle["source_review"]))
    request = json.loads(unpack(bundle["request"]))
    pin = request["retry_of"]
    originals = request["review"]["original_predictions"]
    return {"kind": KIND, "bundle_sha256": sha(raw), "model": pin["model"], "revision": pin["revision"],
        "original_bundle_sha256": bundle["original"]["sha256"], "retry_sha256": bundle["retry"]["sha256"],
        "request_sha256": bundle["request"]["sha256"], "source_review_sha256": bundle["source_review"]["sha256"],
        "reviewed_at": review["reviewed_at"], "replaced_page_ids": sorted(originals),
        "held_length_failure_ids": sorted(identifier for identifier, value in originals.items()
                                          if value["original_prediction"].get("finish_reason") == "length"),
        "policy": "One reviewed input per pinned model/page; full original source lineage and every failed attempt retained."}


def write_reviewed_bundle(original, retry, manifest_path, review_path, output, source_evidence, reviewed_at, load_leaf, *, request_path):
    if review_path.exists() or output.exists():
        raise ValueError("Refusing to replace an existing Dio source review or bundle")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    request_raw = request_path.read_bytes()
    request, pins, groups, scope = authority(manifest_bytes, manifest, request_raw)
    if set(source_evidence) != scope["targets"] or any(not str(value).strip() for value in source_evidence.values()):
        raise ValueError("Every Dio page needs its completed source comparison")
    original_raw, retry_raw = original.read_bytes(), retry.read_bytes()
    _, _, artifacts = inspect_original(original_raw, manifest_bytes, manifest, pins, scope)
    strips = checked_retry(retry_raw, request_raw, request, groups, scope, load_leaf)
    review = {"schema_version": 1, "decision": DECISION, "reviewed_at": reviewed_at,
        "manifest_sha256": sha(manifest_bytes), "request_sha256": sha(request_raw),
        "original_bundle_sha256": sha(original_raw), "retry_sha256": sha(retry_raw), "pages": {}}
    for identifier in sorted(scope["targets"]):
        review["pages"][identifier] = {"original_artifact_sha256": artifacts[identifier],
            "strip_sha256s": [sha(encode(r)) for r in strips[identifier]],
            "image_sha256s": [r["image_sha256"] for r in strips[identifier]],
            "assembled_text_sha256": sha(assemble(strips[identifier]).encode()), "source_evidence": source_evidence[identifier]}
    bundle = {"schema_version": 1, "kind": KIND, "request": retained(request_raw),
        "original": retained(original_raw), "retry": retained(retry_raw), "source_review": retained(encode(review))}
    raw = encode(bundle)
    if len(raw) >= 100_000_000:
        raise ValueError("Reviewed Dio bundle exceeds the 100 MB Git object limit")
    load_bundle(raw, manifest_bytes, manifest, load_leaf)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes(encode(review))
    output.write_bytes(raw)
    return describe_bundle(raw)


def main():
    from ingest_scan_coverage import load_predictions
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, required=True, help="Exact committed checkpoint-specific Dio retry request")
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--retry", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=ROOT / "data/ingest_reviews/coverage/cassius-dio-reviewed-ocr-jobs.json")
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-evidence", type=Path, required=True, help="JSON mapping every requested page ID to completed source-comparison evidence")
    a = p.parse_args()
    def leaf(raw, manifest_bytes, manifest, *, allow_failed_ids=frozenset()):
        return load_predictions(None, manifest_bytes, manifest, raw, allow_failed_ids=allow_failed_ids)
    print(json.dumps(write_reviewed_bundle(a.original, a.retry, a.manifest, a.review, a.out,
        json.loads(a.source_evidence.read_text()), datetime.now(timezone.utc).isoformat(), leaf, request_path=a.request), ensure_ascii=False))


if __name__ == "__main__":
    main()
