"""Assemble scan-reviewed OCR retry strips without adding model votes.

The original page predictions remain archived comparison attempts. A separate
review must name the exact retry bytes and original page artifacts it accepts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def apply_reviewed_retries(inputs, paths, review_path, authority_path):
    if not paths or review_path is None:
        raise ValueError("Retry admission requires predictions and a separate source review")
    if inputs["primary_source"] != "jahn1882":
        raise ValueError("These reviewed retry strips apply only to Jahn 1882")
    authority_raw = authority_path.read_bytes()
    known = Path(__file__).resolve().parent.parent / "data/ingest_reviews"
    if sha(authority_raw) not in {sha((known / name).read_bytes()) for name in
            ["jahn-aristides-page81-retry.json", "jahn-aristides-length-retry.json", "jahn-aristides-notation-retry.json"]}:
        raise ValueError("Retry authority must be an explicitly pinned source-reviewed request")
    manifest = json.loads(authority_raw)
    review = json.loads(review_path.read_text())
    if (review.get("manifest_sha256") != sha(authority_raw) or
            review.get("source_pdf_sha256") != manifest["sources"]["jahn1882"]["sha256"] or
            review.get("decision") != "replace-source-reviewed-degraded-page" or
            not review.get("reviewed_at") or not review.get("source_evidence")):
        raise ValueError("Retry admission lacks an exact source-reviewed decision")
    expected = {page["id"]: page for page in manifest["pages"]}
    if inputs.get("primary_manifest_sha256") != manifest["retry_of"]["sha256"] or inputs["primary_manifest"]["sources"] != manifest["sources"]:
        raise ValueError("Retry no longer identifies the original source request")
    scans = {p["scan_page"] for p in expected.values()}
    if (scans, len(expected)) not in [({81}, 3), ({90, 112}, 5), ({82, 87, 91}, 10)]:
        raise ValueError("Unreviewed Jahn retry geometry")
    pages = sorted({str(p["printed_page"]) for p in expected.values()}, key=int)
    originals = {page: inputs["witnesses"][page] for page in pages}
    if any(page in inputs.get("held_primary_witnesses", {}) for page in pages):
        raise ValueError("The same original page cannot be replaced twice")
    if set(review.get("original_artifacts_sha256", [])) != {w["artifact_sha256"] for ws in originals.values() for w in ws}:
        raise ValueError("Retry source review does not identify every original attempt")
    original_models = {w["model"]: w for w in originals[pages[0]]}
    if any(len(ws) != len(original_models) or {w["model"] for w in ws} != set(original_models) for ws in originals.values()):
        raise ValueError("Retry requires one archived original attempt per model and page")
    reviewed_runs = {r["sha256"]: r for r in review.get("reviewed_runs", [])}
    if len(reviewed_runs) != len(paths) or set(reviewed_runs) != {sha(path.read_bytes()) for path in paths}:
        raise ValueError("Retry source review does not identify the exact prediction files")
    witnesses, retained, images, used_models = {page: [] for page in pages}, [], {}, set()
    for path in paths:
        raw = path.read_bytes()
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if not records or "_meta" not in records[0] or any("_meta" in row for row in records[1:]):
            raise ValueError("Retry prediction metadata is missing or ambiguous")
        meta, rows = records[0]["_meta"], records[1:]
        model = meta.get("model")
        original = original_models.get(model)
        decision = reviewed_runs[sha(raw)]
        if (not original or model in used_models or decision.get("model") != model or
                decision.get("revision") != meta.get("revision") or
                meta.get("revision") != original["revision"] or meta.get("prompt") != original["prompt"] or
                meta.get("manifest_sha256") != sha(authority_raw)):
            raise ValueError("Retry does not match the independently pinned original model")
        if len(rows) != len(expected) or {r.get("id") for r in rows} != set(expected):
            raise ValueError("Retry lacks every reviewed strip exactly once")
        by_id = {row["id"]: row for row in rows}
        for page in pages:
            jobs = sorted((p for p in expected.values() if str(p["printed_page"]) == page), key=lambda p: p["reading_order"])
            ordered = []
            for job in jobs:
                record = by_id[job["id"]]
                if record.get("scan_page") != job["scan_page"] or record.get("region") != job["region"]:
                    raise ValueError("Retry used unchecked source crop geometry")
                if record.get("finish_reason") != "stop" or record.get("error"):
                    raise ValueError("Retry strip did not complete successfully")
                prediction = record.get("raw_prediction")
                if not isinstance(prediction, str) or not any("\u0370" <= c <= "\u03ff" or "\u1f00" <= c <= "\u1fff" for c in prediction):
                    raise ValueError("Retry strip has no Greek reading")
                image = record.get("image_sha256")
                if not image or images.setdefault(job["id"], image) != image:
                    raise ValueError("Retry models describe different source images")
                ordered.append(record)
            original = next(w for w in originals[page] if w["model"] == model)
            prediction = "\n".join(row["raw_prediction"].strip() for row in ordered)
            identity = {"model": model, "revision": meta["revision"], "prompt": meta["prompt"],
                "strips": ordered, "manifest_sha256": sha(authority_raw)}
            witnesses[page].append({"id": original["id"] + "-reviewed-strips", "vote_group": original["vote_group"],
                "text": prediction, "original_text": prediction,
                "artifact_sha256": sha(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()),
                "model": model, "revision": meta["revision"], "backend": meta.get("backend"),
                "source_artifact_sha256": sha(raw), "scan_page": jobs[0]["scan_page"], "prompt": meta["prompt"],
                "source_image_sha256s": [r["image_sha256"] for r in ordered], "attempt_status": "successful",
                "source": "Source-reviewed enlarged body strips from the same printed page",
                "preprocessing": [{"kind": "reviewed-strip-assembly", "reading_order": [r["id"] for r in ordered],
                    "raw_strips": ordered, "source_evidence": review["source_evidence"],
                    "timestamp": review["reviewed_at"], "policy": "Concatenate complete nonoverlapping source lines; retain original whole-page attempt without another vote."}]})
        retained.append({"sha256": sha(raw), "metadata": meta, "records": rows})
        used_models.add(model)
    if used_models != set(original_models) or len({w["vote_group"] for w in witnesses[pages[0]]}) < 2:
        raise ValueError("Reviewed retries must retain both independent model families")
    inputs.setdefault("held_primary_witnesses", {}).update(originals)
    inputs["witnesses"].update(witnesses)
    for page in pages:
        inputs.setdefault("page_text_roles", {})[page] = [p.get("text_role", "authorial-prose") for p in
            sorted((p for p in expected.values() if str(p["printed_page"]) == page), key=lambda p: p["reading_order"])]
    evidence = inputs.setdefault("retry_evidence", {"requests": [], "source_reviews": [], "raw_files": [],
        "policy": "Only the scan-reviewed strip assembly votes for each model; original attempts remain reversible evidence."})
    evidence["requests"].append({"manifest": manifest, "manifest_sha256": sha(authority_raw),
        "source_review_sha256": sha(review_path.read_bytes())})
    evidence["source_reviews"].append(review)
    evidence["raw_files"].extend(retained)
    for region_id, regions in manifest.get("nonlexical_source_regions", {}).items():
        job = next(p for p in expected.values() if p["reconstructs"] == region_id)
        source = manifest["sources"][job["source"]]
        inputs.setdefault("nonlexical_source_regions", {})[str(job["printed_page"])] = [
            {**region, "source": {**source, "scan_page": job["scan_page"], "printed_page": job["printed_page"]},
             "original_page_image_sha256": sorted({w["image_sha256"] for w in originals[str(job["printed_page"])]})}
            for region in regions]
    return inputs


def write_source_review(inputs, paths, authority_path, output, source_evidence, reviewed_at):
    """Record an explicit completed scan review, then validate before saving."""
    import copy
    import tempfile
    if output.exists():
        raise ValueError("Refusing to replace an existing source review")
    if not source_evidence.strip():
        raise ValueError("Describe the completed source inspection")
    authority_raw = authority_path.read_bytes()
    manifest = json.loads(authority_raw)
    runs = []
    for path in paths:
        raw = path.read_bytes()
        meta = json.loads(raw.splitlines()[0])["_meta"]
        runs.append({"sha256": sha(raw), "model": meta["model"], "revision": meta["revision"]})
    review = {"manifest_sha256": sha(authority_raw),
        "source_pdf_sha256": manifest["sources"]["jahn1882"]["sha256"],
        "decision": "replace-source-reviewed-degraded-page", "reviewed_at": reviewed_at,
        "source_evidence": source_evidence,
        "original_artifacts_sha256": [w["artifact_sha256"] for page in sorted({str(p["printed_page"]) for p in manifest["pages"]}, key=int) for w in inputs["witnesses"][page]],
        "reviewed_runs": runs}
    raw = (json.dumps(review, ensure_ascii=False, indent=1) + "\n").encode()
    with tempfile.TemporaryDirectory() as temporary:
        candidate = Path(temporary) / "review.json"
        candidate.write_bytes(raw)
        apply_reviewed_retries(copy.deepcopy(inputs), paths, candidate, authority_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return review


def main():
    import argparse
    from datetime import datetime, timezone
    from repair_meibom_work_assignments import prepare_inputs
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--fresh", type=Path, action="append", required=True)
    parser.add_argument("--retry", type=Path, action="append", required=True)
    parser.add_argument("--source-evidence", required=True,
        help="Describe the completed comparison of every retry strip with the source scan")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "data/ingest_reviews/jahn-aristides-page81-retry.json")
    args = parser.parse_args()
    inputs = prepare_inputs(args.root, args.fresh, allow_pending_retries=True)
    write_source_review(inputs, args.retry,
        args.manifest, args.out, args.source_evidence, datetime.now(timezone.utc).isoformat())
    print("Pinned completed source review; original attempts remain archived at admission")


if __name__ == "__main__":
    main()
