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
    if len(expected) != 3 or {p["scan_page"] for p in expected.values()} != {81}:
        raise ValueError("Unreviewed Jahn retry geometry")
    page = "8"
    originals = inputs["witnesses"][page]
    if set(review.get("original_artifacts_sha256", [])) != {w["artifact_sha256"] for w in originals}:
        raise ValueError("Retry source review does not identify every original attempt")
    original_models = {w["model"]: w for w in originals}
    if len(original_models) != len(originals):
        raise ValueError("Retry requires one archived original attempt per model")
    reviewed_runs = {r["sha256"]: r for r in review.get("reviewed_runs", [])}
    if len(reviewed_runs) != len(paths) or set(reviewed_runs) != {sha(path.read_bytes()) for path in paths}:
        raise ValueError("Retry source review does not identify the exact prediction files")
    witnesses, retained, images, used_models = [], [], {}, set()
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
        ordered = []
        for job in sorted(expected.values(), key=lambda p: p["reading_order"]):
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
        prediction = "\n".join(row["raw_prediction"].strip() for row in ordered)
        identity = {"model": model, "revision": meta["revision"], "prompt": meta["prompt"],
            "strips": ordered, "manifest_sha256": sha(authority_raw)}
        witnesses.append({"id": original["id"] + "-reviewed-strips", "vote_group": original["vote_group"],
            "text": prediction, "original_text": prediction,
            "artifact_sha256": sha(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()),
            "model": model, "revision": meta["revision"], "backend": meta.get("backend"),
            "source_artifact_sha256": sha(raw), "scan_page": 81, "prompt": meta["prompt"],
            "source": "Source-reviewed enlarged body strips from the same printed page",
            "preprocessing": [{"kind": "reviewed-strip-assembly", "reading_order": [r["id"] for r in ordered],
                "raw_strips": ordered, "source_evidence": review["source_evidence"],
                "timestamp": review["reviewed_at"], "policy": "Concatenate complete nonoverlapping source lines; retain original whole-page attempt without another vote."}]})
        retained.append({"sha256": sha(raw), "metadata": meta, "records": rows})
        used_models.add(model)
    if used_models != set(original_models) or len({w["vote_group"] for w in witnesses}) < 2:
        raise ValueError("Reviewed retries must retain both independent model families")
    inputs["held_primary_witnesses"] = {page: originals}
    inputs["witnesses"][page] = witnesses
    inputs["retry_evidence"] = {"manifest": manifest, "manifest_sha256": sha(authority_raw),
        "source_review": review, "source_review_sha256": sha(review_path.read_bytes()),
        "raw_files": retained, "policy": "Only the scan-reviewed strip assembly votes for each model; original attempts remain reversible evidence."}
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
        "original_artifacts_sha256": [w["artifact_sha256"] for w in inputs["witnesses"]["8"]],
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
    args = parser.parse_args()
    inputs = prepare_inputs(args.root, args.fresh)
    write_source_review(inputs, args.retry,
        Path(__file__).resolve().parents[1] / "data/ingest_reviews/jahn-aristides-page81-retry.json",
        args.out, args.source_evidence, datetime.now(timezone.utc).isoformat())
    print("Pinned completed source review; original attempts remain archived at admission")


if __name__ == "__main__":
    main()
