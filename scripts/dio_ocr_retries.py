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
AUTHORITIES.update({family + "-supplementary": ROOT / f"data/ingest_reviews/coverage/cassius-dio-{family}-supplementary-retry-jobs.json"
                    for family in ["qwen36", "qwen38"]})
CHILD_AUTHORITIES = {family: ROOT / f"data/ingest_reviews/coverage/cassius-dio-{family}-child-strip-retry-jobs.json"
                     for family in ["qwen36", "qwen38"]}
CHECKPOINTS = {
    "qwen36": ("Qwen/Qwen3.6-27B-FP8", "e89b16ebf1988b3d6befa7de50abc2d76f26eb09", "qwen3.6-27b"),
    "qwen38": ("Qwen/Qwen3.8-27B-FP8", "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a", "qwen3.8-27b"),
}
AUTHORITY_REGISTRY = ROOT / "data/ingest_reviews/coverage/cassius-dio-retry-authorities.json"
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


def authority_catalog(group):
    result = dict(AUTHORITIES if group == "page_requests" else CHILD_AUTHORITIES)
    if AUTHORITY_REGISTRY.exists():
        result = {}
        registry = json.loads(AUTHORITY_REGISTRY.read_bytes())
        if registry.get("schema_version") != 1:
            raise ValueError("Unknown Dio source authority registry version")
        for key, item in registry[group].items():
            relative = item if isinstance(item, str) else item["path"]
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts or path.parts[:3] != ("data", "ingest_reviews", "coverage"):
                raise ValueError("Dio source authority must be a repository-relative reviewed request")
            target = ROOT / path
            if not target.is_file() or (isinstance(item, dict) and sha(target.read_bytes()) != item.get("sha256")):
                raise ValueError("Dio source authority registry refers to changed request bytes")
            result[key] = target
    return result


def authority(manifest_bytes, manifest, request_raw):
    matches = [(key, path) for key, path in authority_catalog("page_requests").items() if path.exists() and path.read_bytes() == request_raw]
    if len(matches) != 1:
        raise ValueError("Dio retry differs from its committed checkpoint-specific source authority")
    key, request_path = matches[0]
    request = json.loads(request_raw)
    checkpoints = [(key, value) for key, value in CHECKPOINTS.items()
                   if value[:2] == (request["retry_of"].get("model"), request["retry_of"].get("revision"))]
    if len(checkpoints) != 1:
        raise ValueError("Dio retry does not use a pinned checkpoint")
    checkpoint_key, (model, revision, family) = checkpoints[0]
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
    scope = {"key": checkpoint_key, "authority_key": key, "request_path": request_path, "model": model, "revision": revision, "family": family,
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


def checked_retry(retry_raw, request_raw, request, groups, scope, load_leaf, *, allow_failed_ids=frozenset()):
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
    if len(rows) != len(selected) or set(by_id) != set(selected) or any(failed(row) and (row["id"] not in allow_failed_ids or row.get("finish_reason") != "length" or row.get("error")) for row in rows):
        raise ValueError("Dio retry requires every successful complete reviewed strip")
    # This ordinary loader supplies the existing exact prompt, image and crop
    # checks. A child request can authorize only its exact pinned parent
    # length failures, and every such parent strip must be replaced below.
    result, _ = load_leaf(retry_raw, request_raw, request, allow_failed_ids=allow_failed_ids)
    if set(result) != set(selected):
        raise ValueError("Dio strict retry loader changed region identities")
    return {identifier: [by_id[p["id"]] for p in jobs] for identifier, jobs in groups.items()}


def assemble(strips):
    return "\n".join(row["raw_prediction"].strip() for row in strips)


def child_authority(parent_raw, parent, parent_scope, request_raw):
    matches = [(key, path) for key, path in authority_catalog("child_requests").items() if path.exists() and path.read_bytes() == request_raw]
    if len(matches) != 1:
        raise ValueError("Dio child retry differs from its committed checkpoint-specific source authority")
    request = json.loads(request_raw)
    pin = request["retry_of"]
    parent_path = "data/ingest_reviews/coverage/" + parent_scope["request_path"].name
    if (pin.get("path") != parent_path or pin.get("sha256") != sha(parent_raw) or
            (pin.get("model"), pin.get("revision")) != (parent_scope["model"], parent_scope["revision"])):
        raise ValueError("Dio child request changed its exact parent request or checkpoint")
    originals = request["review"]["original_predictions"]
    parent_jobs = {p["id"]: p for p in parent["pages"]}
    groups, failed_ids = {}, set()
    for identifier, original in originals.items():
        job = parent_jobs.get(identifier)
        metadata, row = original["original_metadata"], original["original_prediction"]
        if (job is None or not original.get("source_evidence", "").strip() or
                sha(encode({"metadata": metadata, "prediction": row})) != original.get("artifact_sha256") or
                (metadata.get("model"), metadata.get("revision"), metadata.get("manifest_sha256")) !=
                (parent_scope["model"], parent_scope["revision"], sha(parent_raw)) or
                (row.get("id"), row.get("source"), row.get("scan_page"), row.get("region")) !=
                (identifier, job["source"], job["scan_page"], job["region"])):
            raise ValueError("Dio child request lacks the exact source-reviewed parent strip artifact")
        if row.get("finish_reason") == "length" and not row.get("error"):
            failed_ids.add(identifier)
        elif failed(row):
            raise ValueError("Dio child request cannot authorize an unknown parent failure")
        jobs = sorted((p for p in request["pages"] if p.get("reconstructs") == identifier), key=lambda p: p["reading_order"])
        if len(jobs) < 2 or [p["reading_order"] for p in jobs] != list(range(1, len(jobs) + 1)):
            raise ValueError("Dio child retry lacks its complete reviewed reading order")
        x0, y0, x1, y1 = job["region"]
        edge = y0
        for child in jobs:
            region = child["region"]
            if ((child["source"], child["scan_page"], child.get("source_volume")) !=
                    (job["source"], job["scan_page"], job.get("source_volume")) or
                    request["sources"][child["source"]] != parent["sources"][job["source"]] or
                    region[0] != x0 or region[2] != x1 or abs(region[1] - edge) > 1e-10 or
                    not region[1] < region[3] <= y1):
                raise ValueError("Dio child strips do not partition the exact reviewed parent crop")
            edge = region[3]
        if abs(edge - y1) > 1e-10:
            raise ValueError("Dio child strips omit part of the reviewed parent crop")
        groups[identifier] = jobs
    if (not originals or len(request["pages"]) != sum(map(len, groups.values())) or
            len({p["id"] for p in request["pages"]}) != len(request["pages"])):
        raise ValueError("Dio child request changed the source-reviewed strip set")
    return request, originals, groups, {**parent_scope, "request_path": matches[0][1], "targets": set(originals), "failed_ids": frozenset(failed_ids)}


def review_header(review, manifest_sha, request_sha, original_sha, retry_sha, targets, *, child=False):
    if (review.get("decision") != (DECISION + "-child-strips" if child else DECISION) or not review.get("reviewed_at") or
            review.get("manifest_sha256") != manifest_sha or review.get("request_sha256") != request_sha or
            review.get("original_bundle_sha256") != original_sha or review.get("retry_sha256") != retry_sha or
            set(review.get("pages", {})) != set(targets)):
        raise ValueError("Dio retry lacks a completed source review of the exact inputs")


def page_review(artifact, strips, evidence):
    return {"original_artifact_sha256": artifact,
            "strip_sha256s": [sha(encode(r)) for r in strips],
            "image_sha256s": [r["image_sha256"] for r in strips],
            "assembled_text_sha256": sha(assemble(strips).encode()), "source_evidence": evidence}


def verify_pages(review, artifacts, strips):
    for identifier, artifact in artifacts.items():
        actual = review["pages"][identifier]
        if (not actual.get("source_evidence", "").strip() or
                actual != page_review(artifact, strips[identifier], actual["source_evidence"])):
            raise ValueError("Dio completed page review refers to different artifacts or strips")


def bundle_parts(bundle):
    if bundle.get("kind") != KIND:
        raise ValueError("Unrecognized reviewed Dio retry bundle")
    if bundle.get("schema_version") == 1:
        return [{key: bundle[key] for key in ["request", "retry", "source_review"]}]
    if bundle.get("schema_version") == 2 and isinstance(bundle.get("parts"), list) and bundle["parts"]:
        return bundle["parts"]
    raise ValueError("Unrecognized reviewed Dio retry bundle")


def inspect_parts(parts, manifest_bytes, manifest):
    if not parts:
        raise ValueError("A Dio retry bundle needs at least one complete source-reviewed request")
    prepared, all_pins, scope = [], {}, None
    for part in parts:
        request_raw = unpack(part["request"])
        request, pins, groups, current_scope = authority(manifest_bytes, manifest, request_raw)
        if all_pins.keys() & pins.keys():
            raise ValueError("Dio retry requests cannot repeat a model/page target")
        if scope is not None and (scope["model"], scope["revision"]) != (current_scope["model"], current_scope["revision"]):
            raise ValueError("Dio retry requests cannot mix checkpoints or voting families")
        all_pins.update(pins)
        scope = current_scope if scope is None else {**scope,
            "targets": scope["targets"] | current_scope["targets"],
            "failed_ids": scope["failed_ids"] | current_scope["failed_ids"]}
        prepared.append((part, request_raw, request, pins, groups, current_scope))
    required = set()
    for path in authority_catalog("page_requests").values():
        if path.is_file():
            candidate = path.read_bytes()
            parent = json.loads(candidate).get("retry_of", {})
            if (parent.get("sha256"), parent.get("model"), parent.get("revision")) == (
                    sha(manifest_bytes), scope["model"], scope["revision"]):
                required.add(sha(candidate))
    if not required <= {sha(item[1]) for item in prepared}:
        raise ValueError("Every committed source-required Dio page retry must be supplied")
    return prepared, all_pins, scope


def checked_part(part, request_raw, request, groups, scope, load_leaf, *, make_reviews=None, reviewed_at=None):
    """Validate every child before allowing any exact parent-strip failure."""
    retry_raw = unpack(part["retry"])
    parent_meta, parent_rows = records(retry_raw)
    parent_rows = {r["id"]: r for r in parent_rows}
    replacements, child_failed, child_descriptors = {}, set(), []
    # A committed source review that identifies residual loss or a stopped loop
    # is mandatory even when the parent runner reports successful completion.
    required = set()
    for candidate in authority_catalog("child_requests").values():
        if candidate.is_file():
            reviewed = json.loads(candidate.read_bytes())
            if reviewed.get("retry_of", {}).get("sha256") == sha(request_raw):
                required.update(reviewed["review"]["original_predictions"])
    for index, child in enumerate(part.get("children", [])):
        child_raw = unpack(child["request"])
        child_request, pins, child_groups, child_scope = child_authority(request_raw, request, scope, child_raw)
        if replacements.keys() & pins.keys():
            raise ValueError("Dio child requests cannot replace the same parent strip twice")
        for identifier, pin in pins.items():
            if parent_meta != pin["original_metadata"] or parent_rows.get(identifier) != pin["original_prediction"]:
                raise ValueError("Dio child request refers to a different parent retry artifact")
        child_retry_raw = unpack(child["retry"])
        config = make_reviews[index] if make_reviews is not None else None
        child_strips, nested_descriptors = checked_part(child, child_raw, child_request, child_groups, child_scope, load_leaf,
            make_reviews=config.get("children", []) if config is not None else None, reviewed_at=reviewed_at)
        artifacts = {identifier: pin["artifact_sha256"] for identifier, pin in pins.items()}
        if make_reviews is not None:
            evidence = config["source_evidence"]
            child_review = make_review(sha(request_raw), sha(child_raw), sha(retry_raw), sha(child_retry_raw),
                                       artifacts, child_strips, evidence, reviewed_at, child=True)
            if nested_descriptors:
                child_review["child_retries"] = nested_descriptors
            child["source_review"] = retained(encode(child_review))
        child_review_raw = unpack(child["source_review"])
        child_review = json.loads(child_review_raw)
        review_header(child_review, sha(request_raw), sha(child_raw), sha(retry_raw), sha(child_retry_raw), pins, child=True)
        if child_review.get("child_retries", []) != nested_descriptors:
            raise ValueError("Dio child review changed its retained descendant retry lineage")
        verify_pages(child_review, artifacts, child_strips)
        replacements.update(child_strips)
        child_failed.update(child_scope["failed_ids"])
        child_descriptors.append({"request_sha256": sha(child_raw), "retry_sha256": sha(child_retry_raw),
            "source_review_sha256": sha(child_review_raw), "replaced_strip_ids": sorted(pins),
            "child_retries": nested_descriptors})
    if not required <= replacements.keys():
        raise ValueError("A source-confirmed degraded or looping Dio strip needs its reviewed child replacement")
    base = checked_retry(retry_raw, request_raw, request, groups, scope, load_leaf,
                         allow_failed_ids=frozenset(child_failed))
    effective = {identifier: [r for parent in strips for r in replacements.get(parent["id"], [parent])]
                 for identifier, strips in base.items()}
    return effective, child_descriptors


def load_bundle(raw, manifest_bytes, manifest, load_leaf):
    bundle = json.loads(raw)
    parts = bundle_parts(bundle)
    prepared, pins, scope = inspect_parts(parts, manifest_bytes, manifest)
    original_raw = unpack(bundle["original"])
    eligible, _, artifacts = inspect_original(original_raw, manifest_bytes, manifest, pins, scope)
    replacements = []
    for part, request_raw, request, part_pins, groups, part_scope in prepared:
        retry_raw, review_raw = unpack(part["retry"]), unpack(part["source_review"])
        review = json.loads(review_raw)
        review_header(review, sha(manifest_bytes), sha(request_raw), sha(original_raw), sha(retry_raw), part_pins)
        strips, child_descriptors = checked_part(part, request_raw, request, groups, part_scope, load_leaf)
        if review.get("child_retries", []) != child_descriptors:
            raise ValueError("Dio completed review changed its retained child retry lineage")
        verify_pages(review, {identifier: artifacts[identifier] for identifier in part_pins}, strips)
        replacements.append((request_raw, request, groups, strips, retry_raw, review_raw, review, child_descriptors))
    # Only the union of source-pinned failed original pages can pass; all have
    # complete source-reviewed replacements before the ordinary loader is called.
    result, _ = load_leaf(original_raw, manifest_bytes, manifest, allow_failed_ids=scope["failed_ids"])
    if set(result) != set(eligible):
        raise ValueError("Dio original loader changed the complete region set")
    for request_raw, request, groups, strips, retry_raw, review_raw, review, child_descriptors in replacements:
        for identifier in sorted(strips):
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
                "raw_strips": strips[identifier], "reading_order": [r["id"] for r in strips[identifier]],
                "child_retries": child_descriptors,
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
    parts = bundle_parts(bundle)
    descriptions, targets, failed_ids = [], set(), set()
    for part in parts:
        review = json.loads(unpack(part["source_review"]))
        request = json.loads(unpack(part["request"]))
        pin = request["retry_of"]
        originals = request["review"]["original_predictions"]
        targets.update(originals)
        failed_ids.update(identifier for identifier, value in originals.items()
                          if value["original_prediction"].get("finish_reason") == "length")
        descriptions.append({"retry_sha256": part["retry"]["sha256"], "request_sha256": part["request"]["sha256"],
            "source_review_sha256": part["source_review"]["sha256"], "reviewed_at": review["reviewed_at"],
            "replaced_page_ids": sorted(originals), "child_retries": review.get("child_retries", [])})
    result = {"kind": KIND, "bundle_sha256": sha(raw), "model": pin["model"], "revision": pin["revision"],
        "original_bundle_sha256": bundle["original"]["sha256"], "parts": descriptions,
        "replaced_page_ids": sorted(targets), "held_length_failure_ids": sorted(failed_ids),
        "policy": "One reviewed input per pinned model/page; full original source lineage and every failed attempt retained."}
    if len(descriptions) == 1:
        result.update({key: descriptions[0][key] for key in ["retry_sha256", "request_sha256", "source_review_sha256", "reviewed_at"]})
    return result


def make_review(manifest_sha, request_sha, original_sha, retry_sha, artifacts, strips, evidence, reviewed_at, *, child=False):
    if set(evidence) != set(artifacts) or any(not isinstance(value, str) or not value.strip() for value in evidence.values()):
        raise ValueError("Every Dio page needs its completed source comparison")
    return {"schema_version": 1, "decision": DECISION + "-child-strips" if child else DECISION, "reviewed_at": reviewed_at,
        "manifest_sha256": manifest_sha, "request_sha256": request_sha, "original_bundle_sha256": original_sha,
        "retry_sha256": retry_sha, "pages": {identifier: page_review(artifacts[identifier], strips[identifier], evidence[identifier])
                                             for identifier in sorted(artifacts)}}


def write_reviewed_bundles(original, manifest_path, parts, output, reviewed_at, load_leaf, *, legacy_single=False):
    """Retain disjoint page requests and optional child-strip attempts exactly.

    Each part supplies request_path, retry_path, review_path, source_evidence,
    and optional children with the same four fields. Review paths and output
    must be new; every retained original and retry remains byte-identical.
    """
    def flatten(configs):
        return [c for p in configs for c in [p, *flatten(p.get("children", []))]]
    configs = flatten(parts)
    pending_paths = [output] + [p["review_path"] for p in configs]
    if len(set(pending_paths)) != len(pending_paths) or any(path.exists() for path in pending_paths):
        raise ValueError("Refusing to replace an existing Dio source review or bundle")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    original_raw = original.read_bytes()
    def retain_config(config):
        return {"request": retained(config["request_path"].read_bytes()), "retry": retained(config["retry_path"].read_bytes()),
                "children": [retain_config(c) for c in config.get("children", [])]}
    retained_parts = [retain_config(p) for p in parts]
    prepared, pins, scope = inspect_parts(retained_parts, manifest_bytes, manifest)
    _, _, artifacts = inspect_original(original_raw, manifest_bytes, manifest, pins, scope)
    for config, (part, request_raw, request, part_pins, groups, part_scope) in zip(parts, prepared):
        strips, child_descriptors = checked_part(part, request_raw, request, groups, part_scope, load_leaf,
            make_reviews=config.get("children", []), reviewed_at=reviewed_at)
        review = make_review(sha(manifest_bytes), sha(request_raw), sha(original_raw), part["retry"]["sha256"],
            {identifier: artifacts[identifier] for identifier in part_pins}, strips, config["source_evidence"], reviewed_at)
        if child_descriptors:
            review["child_retries"] = child_descriptors
        part["source_review"] = retained(encode(review))
    bundle = {"schema_version": 2, "kind": KIND, "original": retained(original_raw), "parts": retained_parts}
    if legacy_single:
        assert len(retained_parts) == 1 and not retained_parts[0]["children"]
        bundle = {"schema_version": 1, "kind": KIND, "original": retained(original_raw),
                  **{key: retained_parts[0][key] for key in ["request", "retry", "source_review"]}}
    raw = encode(bundle)
    if len(raw) >= 100_000_000:
        raise ValueError("Reviewed Dio bundle exceeds the 100 MB Git object limit")
    load_bundle(raw, manifest_bytes, manifest, load_leaf)
    def write_reviews(config, part):
        config["review_path"].parent.mkdir(parents=True, exist_ok=True)
        config["review_path"].write_bytes(unpack(part["source_review"]))
        for child_config, child in zip(config.get("children", []), part["children"]):
            write_reviews(child_config, child)
    for config, part in zip(parts, retained_parts):
        write_reviews(config, part)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return describe_bundle(raw)


def write_reviewed_bundle(original, retry, manifest_path, review_path, output, source_evidence, reviewed_at, load_leaf, *, request_path):
    return write_reviewed_bundles(original, manifest_path,
        [{"request_path": request_path, "retry_path": retry, "review_path": review_path, "source_evidence": source_evidence}],
        output, reviewed_at, load_leaf, legacy_single=True)


def main():
    from ingest_scan_coverage import load_predictions
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, help="Exact committed checkpoint-specific Dio retry request")
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--retry", type=Path)
    p.add_argument("--manifest", type=Path, default=ROOT / MANIFEST_PATH)
    p.add_argument("--review", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-evidence", type=Path, help="JSON mapping every requested page to completed source-comparison evidence")
    p.add_argument("--parts", type=Path, help="JSON list of request_path/retry_path/review_path/source_evidence and optional recursive children")
    a = p.parse_args()
    def leaf(raw, manifest_bytes, manifest, *, allow_failed_ids=frozenset()):
        return load_predictions(None, manifest_bytes, manifest, raw, allow_failed_ids=allow_failed_ids)
    if a.parts:
        if any([a.request, a.retry, a.review, a.source_evidence]):
            p.error("Use --parts or the single-request options, not both")
        def config(value):
            return {**value, **{key: Path(value[key]) for key in ["request_path", "retry_path", "review_path"]},
                    "children": [config(child) for child in value.get("children", [])]}
        parts = [config(value) for value in json.loads(a.parts.read_text())]
        descriptor = write_reviewed_bundles(a.original, a.manifest, parts, a.out,
            datetime.now(timezone.utc).isoformat(), leaf)
    else:
        if not all([a.request, a.retry, a.review, a.source_evidence]):
            p.error("Supply --parts or all single-request options")
        descriptor = write_reviewed_bundle(a.original, a.retry, a.manifest, a.review, a.out,
            json.loads(a.source_evidence.read_text()), datetime.now(timezone.utc).isoformat(), leaf, request_path=a.request)
    print(json.dumps(descriptor, ensure_ascii=False))


if __name__ == "__main__":
    main()
