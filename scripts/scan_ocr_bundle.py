#!/usr/bin/env python3
"""Retain exact OCR parts and manifests while combining disjoint checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

KIND = "scan-ocr-bundle"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def is_bundle(raw):
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return False
    return isinstance(value, dict) and value.get("kind") == KIND


def retained(raw):
    return {"sha256": sha(raw), "raw_utf8": raw.decode("utf-8")}


def unpack(value):
    raw = value["raw_utf8"].encode("utf-8")
    if value.get("sha256") != sha(raw):
        raise ValueError("Retained OCR artifact checksum changed")
    return raw


def inspect_leaf(raw, manifest_bytes):
    """Validate original metadata and geometry, retaining failed outcomes too."""
    manifest = json.loads(manifest_bytes)
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not records or set(records[0]) != {"_meta"} or any("_meta" in row for row in records[1:]):
        raise ValueError("OCR part has ambiguous original runtime metadata")
    meta, rows = records[0]["_meta"], records[1:]
    if (meta.get("manifest_sha256") != sha(manifest_bytes) or meta.get("prompt") != manifest["prompt"]
            or not meta.get("model") or not meta.get("revision") or not meta.get("runtime")
            or not re.fullmatch(r"[a-f0-9]{64}", meta.get("runner_sha256", ""))):
        raise ValueError("OCR part differs from its original manifest or pinned runtime")
    pages = {page["id"]: page for page in manifest["pages"]}
    if len(pages) != len(manifest["pages"]):
        raise ValueError("Repeated manifest identity")
    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids) or not set(ids) <= set(pages):
        raise ValueError("Repeated or unknown original OCR identity")
    selected = meta.get("shard", {}).get("selected_ids")
    if selected is not None and (len(set(selected)) != len(selected) or not set(ids) <= set(selected)
                                 or not set(selected) <= set(pages)
                                 or meta["shard"].get("selection_sha256") != sha(encode(selected))):
        raise ValueError("OCR shard selection differs from its pinned identities")
    for row in rows:
        page = pages[row["id"]]
        region = page.get("region", [0, 0, 1, 1])
        if (len(region) != 4 or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1)
                or not re.fullmatch(r"[a-f0-9]{64}", row.get("image_sha256", ""))):
            raise ValueError("OCR part lacks valid source image geometry or checksum")
        suffix = page.get("prompt_suffix", manifest["sources"][page["source"]].get("prompt_suffix", ""))
        prompt = manifest["prompt"] + (" " + suffix if suffix else "")
        if (row.get("source"), row.get("scan_page"), row.get("region")) != (
                page["source"], page["scan_page"], page.get("region", [0, 0, 1, 1])):
            raise ValueError("Original OCR part geometry changed")
        if row.get("prompt_sha256") != sha(prompt.encode()):
            raise ValueError("Original OCR part prompt changed")
    return meta, {row["id"]: row for row in rows}


def _relation(original_raw, effective_raw, reviews):
    if original_raw == effective_raw:
        return set()
    original, effective = json.loads(original_raw), json.loads(effective_raw)
    substitutions = effective.get("reviewed_substitutions", {})
    review_pin = substitutions.get("source_review", {})
    if substitutions.get("original_manifest_sha256") != sha(original_raw):
        raise ValueError("Manifest change lacks its exact original source pin")
    review_raw = reviews.get(review_pin.get("sha256"))
    if review_raw is None:
        raise ValueError("Reviewed substitutions lack their retained source review")
    review = json.loads(review_raw)
    if (review.get("kind") != "scan-region-body-review" or not review.get("reviewed_at")
            or review.get("original_manifest_sha256") != sha(original_raw)):
        raise ValueError("Invalid completed region source review")
    original_base = {k: v for k, v in original.items() if k not in {"pages", "reviewed_substitutions"}}
    effective_base = {k: v for k, v in effective.items() if k not in {"pages", "reviewed_substitutions"}}
    if original_base != effective_base:
        raise ValueError("Reviewed crop substitution changed other manifest fields")
    if [p["id"] for p in original["pages"]] != [p["id"] for p in effective["pages"]]:
        raise ValueError("Reviewed crop substitution changed manifest identities or order")
    entries = substitutions.get("regions", [])
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Repeated crop substitution")
    changed = set()
    for old, new in zip(original["pages"], effective["pages"]):
        if old == new:
            continue
        identifier = old["id"]
        allowed_fields = {"region", "prompt_suffix"}
        if {k: v for k, v in old.items() if k not in allowed_fields} != {k: v for k, v in new.items() if k not in allowed_fields}:
            raise ValueError("Reviewed substitution changes more than crop geometry or a page prompt suffix")
        entry = by_id.get(identifier, {})
        evidence = review.get("evidence", {}).get(entry.get("evidence_id"), {})
        expected = {"id": identifier, "source": old["source"], "scan_page": old["scan_page"],
                    "original_region": old.get("region", [0, 0, 1, 1]), "region": new.get("region", [0, 0, 1, 1])}
        prompt_changed = old.get("prompt_suffix") != new.get("prompt_suffix") or ("prompt_suffix" in old) != ("prompt_suffix" in new)
        if prompt_changed:
            prompt_fields = {"original_prompt_suffix": old.get("prompt_suffix"), "prompt_suffix": new.get("prompt_suffix")}
            if (any(key not in entry or key not in evidence for key in prompt_fields)
                    or any(value is not None and not isinstance(value, str) for value in prompt_fields.values())):
                raise ValueError("Page prompt change lacks exact original and reviewed suffix pins")
            expected.update(prompt_fields)
        source_sha = original["sources"][old["source"]]["sha256"]
        reviewed_source = review.get("sources", {}).get(old["source"], {})
        if (any(entry.get(k) != v or evidence.get(k) != v for k, v in expected.items())
                or not evidence.get("evidence") or not evidence.get("reviewed_at")
                or evidence.get("source_pdf_sha256") != source_sha
                or reviewed_source.get("sha256") != source_sha
                or reviewed_source.get("url") != original["sources"][old["source"]]["url"]
                or not re.fullmatch(r"[a-f0-9]{64}", evidence.get("contact_sheet_sha256", ""))):
            raise ValueError("Crop or page-prompt substitution differs from its source-reviewed evidence")
        changed.add(identifier)
    if changed != set(by_id):
        raise ValueError("Crop review does not describe exactly the changed identities")
    return changed


def load_bundle(raw, effective_manifest_bytes, leaf_loader=None):
    """Recursively validate exact parts; callbacks retain original artifact hashes.

    leaf_loader receives the ORIGINAL raw part and ORIGINAL manifest bytes and
    returns its prediction dictionary. Failed outcomes remain archiveable with
    no callback; an admission callback must apply its usual success checks.
    """
    authority_bytes, review_bytes = {}, {}

    def collect(value, depth=0):
        if depth > 16:
            raise ValueError("OCR bundle nesting is too deep")
        if not isinstance(value, dict) or value.get("kind") != KIND or value.get("schema_version") != 1:
            raise ValueError("Unknown OCR bundle format")
        found = [unpack(value["effective_manifest"])]
        found.extend(unpack(pin) for pin in value.get("authority_manifests", []))
        local_reviews = set()
        for pin in value.get("source_reviews", []):
            review_raw = unpack(pin)
            if pin["sha256"] in local_reviews:
                raise ValueError("Repeated source-review artifact")
            local_reviews.add(pin["sha256"])
            review_bytes[sha(review_raw)] = review_raw
        for part in value.get("parts", []):
            found.append(unpack(part["manifest"]))
            prediction = unpack(part["prediction"])
            if is_bundle(prediction):
                collect(json.loads(prediction), depth + 1)
        for authority in found:
            authority_bytes[sha(authority)] = authority

    collect(json.loads(raw))
    lineage_cache, changed_cache = {}, {}

    def lineage(value, trail=()):
        digest = sha(value)
        if digest in lineage_cache:
            return lineage_cache[digest]
        if digest in trail or len(trail) > 16:
            raise ValueError("Reviewed manifest authority chain is cyclic or too deep")
        request = json.loads(value)
        substitutions = request.get("reviewed_substitutions")
        if substitutions is None:
            result = [value]
        else:
            original = authority_bytes.get(substitutions.get("original_manifest_sha256"))
            if original is None:
                raise ValueError("Reviewed crop manifest lacks its exact original authority bytes")
            result = [*lineage(original, (*trail, digest)), value]
            changed_cache[digest] = _relation(original, value, review_bytes)
        lineage_cache[digest] = result
        return result

    def transitions(original, effective):
        chain = lineage(effective)
        start = next((i for i, value in enumerate(chain) if value == original), None)
        if start is None:
            raise ValueError("OCR part manifest is not an exact reviewed ancestor of the effective request")
        return [(chain[i-1], chain[i], changed_cache[sha(chain[i])]) for i in range(start + 1, len(chain))]

    def walk(value, effective_raw, depth):
        if depth > 16:
            raise ValueError("OCR bundle nesting is too deep")
        bundle = json.loads(value)
        if bundle.get("kind") != KIND or bundle.get("schema_version") != 1:
            raise ValueError("Unknown OCR bundle format")
        if unpack(bundle["effective_manifest"]) != effective_raw:
            raise ValueError("OCR bundle belongs to a different effective manifest")
        chain = lineage(effective_raw)
        used_reviews = {json.loads(value)["reviewed_substitutions"]["source_review"]["sha256"]
                        for value in chain if "reviewed_substitutions" in json.loads(value)}
        eligible, checkpoints, held, provenance = {}, set(), [], []
        effective = json.loads(effective_raw)
        effective_pages = {page["id"]: page for page in effective["pages"]}
        for part in bundle.get("parts", []):
            part_raw, original_raw = unpack(part["prediction"]), unpack(part["manifest"])
            original = json.loads(original_raw)
            pages = {page["id"]: page for page in original["pages"]}
            stages = transitions(original_raw, effective_raw)
            changed = set().union(*(stage[2] for stage in stages))
            if is_bundle(part_raw):
                predictions, audit = walk(part_raw, original_raw, depth + 1)
                checkpoints.update(tuple(checkpoint) for checkpoint in audit["checkpoints"])
                used_reviews.update(audit["source_review_sha256"])
                held.extend(audit["held_predictions"])
                provenance.extend(audit["parts"])
            else:
                meta, rows = inspect_leaf(part_raw, original_raw)
                checkpoints.add((meta["model"], meta["revision"]))
                predictions = leaf_loader(part_raw, original_raw) if leaf_loader else rows
                if set(predictions) != set(rows):
                    raise ValueError("Leaf loader changed original prediction identities")
                provenance.append({"raw_sha256": sha(part_raw), "manifest_sha256": sha(original_raw),
                                   "metadata": meta, "ids": list(rows)})
            for identifier, prediction in predictions.items():
                if identifier not in pages:
                    raise ValueError("Nested bundle yielded an unknown source identity")
                if identifier in changed:
                    applicable = []
                    for parent, child, changed_ids in stages:
                        if identifier not in changed_ids:
                            continue
                        substitutions = json.loads(child)["reviewed_substitutions"]
                        entry = next(e for e in substitutions["regions"] if e["id"] == identifier)
                        applicable.append({"original_manifest_sha256": sha(parent),
                                           "effective_manifest_sha256": sha(child),
                                           "source_review_sha256": substitutions["source_review"]["sha256"], **entry})
                    latest = applicable[-1]
                    decision = {"id": identifier, "raw_part_sha256": sha(part_raw),
                                 "original_manifest_sha256": sha(original_raw),
                                 "source_review_sha256": latest["source_review_sha256"],
                                 "source": pages[identifier]["source"], "scan_page": pages[identifier]["scan_page"],
                                 "original_region": pages[identifier].get("region", [0, 0, 1, 1]),
                                 "region": effective_pages[identifier].get("region", [0, 0, 1, 1]),
                                 "evidence_id": latest["evidence_id"],
                                 "reason": "Source-reviewed geometry or page prompt superseded; original remains held evidence."}
                    if any("prompt_suffix" in transition for transition in applicable):
                        decision["original_prompt_suffix"] = pages[identifier].get("prompt_suffix")
                        decision["prompt_suffix"] = effective_pages[identifier].get("prompt_suffix")
                    if len(stages) > 1:
                        decision["reviewed_transition_chain"] = applicable
                    held.append(decision)
                    continue
                if identifier in eligible:
                    raise ValueError("Duplicate eligible OCR identity; explicit review is required")
                eligible[identifier] = prediction
        if not bundle.get("parts") or len(checkpoints) != 1:
            raise ValueError("A bundle must contain exactly one model and revision")
        return eligible, {"effective_manifest_sha256": sha(effective_raw), "source_review_sha256": sorted(used_reviews),
                          "checkpoints": [list(checkpoint) for checkpoint in sorted(checkpoints)],
                          "parts": provenance, "held_predictions": held}
    return walk(raw, effective_manifest_bytes, 0)


def write_bundle(parts, effective_manifest_path, out, source_reviews=(), authority_manifests=()):
    effective_raw = effective_manifest_path.read_bytes()
    value = {"kind": KIND, "schema_version": 1, "effective_manifest": retained(effective_raw),
             "source_reviews": [retained(path.read_bytes()) for path in source_reviews],
             "authority_manifests": [retained(path.read_bytes()) for path in authority_manifests],
             "parts": [{"prediction": retained(raw_path.read_bytes()), "manifest": retained(manifest_path.read_bytes())}
                       for raw_path, manifest_path in parts]}
    raw = encode(value)
    load_bundle(raw, effective_raw)
    if len(raw) >= 100_000_000:
        raise ValueError("OCR bundle exceeds the 100 MB Git object limit")
    if out.exists() and out.read_bytes() != raw:
        raise ValueError("Refusing to replace a different retained OCR bundle")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return raw


def pending_partitions(manifest_bytes, completed_bundle, count, *, model, revision):
    if count < 1:
        raise ValueError("Shard count must be positive")
    completed, audit = load_bundle(completed_bundle, manifest_bytes) if completed_bundle else ({}, None)
    if audit and audit["checkpoints"] != [[model, revision]]:
        raise ValueError("Completed results belong to a different checkpoint")
    pages = json.loads(manifest_bytes)["pages"]
    remaining = [page["id"] for page in pages if page["id"] not in completed]
    return [remaining[index::count] for index in range(count)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    write = commands.add_parser("write")
    write.add_argument("--manifest", type=Path, required=True)
    write.add_argument("--part", type=Path, nargs=2, action="append", required=True, metavar=("RAW", "ORIGINAL_MANIFEST"))
    write.add_argument("--source-review", type=Path, action="append", default=[])
    write.add_argument("--authority-manifest", type=Path, action="append", default=[])
    write.add_argument("--out", type=Path, required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--completed-bundle", type=Path)
    plan.add_argument("--count", type=int, required=True)
    plan.add_argument("--model", required=True)
    plan.add_argument("--revision", required=True)
    plan.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "write":
        raw = write_bundle(args.part, args.manifest, args.out, args.source_review, args.authority_manifest)
        print(json.dumps({"bundle_sha256": sha(raw)}))
    else:
        groups = pending_partitions(args.manifest.read_bytes(),
            args.completed_bundle.read_bytes() if args.completed_bundle else None,
            args.count, model=args.model, revision=args.revision)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for index, ids in enumerate(groups):
            path = args.out_dir / f"shard-{index:02d}.json"
            raw = encode(ids)
            if path.exists() and path.read_bytes() != raw:
                raise ValueError("Refusing to change a pinned shard selection")
            path.write_bytes(raw)
        print(json.dumps({"pending": sum(map(len, groups)), "shards": list(map(len, groups))}))


if __name__ == "__main__":
    main()
