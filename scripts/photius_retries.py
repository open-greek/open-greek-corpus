"""Assemble source-reviewed Photius strips without multiplying model votes."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

from prepare_photius_coverage import build_page13_retry
from prepare_photius_retries import REVIEWS, build_retry, manifest_path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def known_retry_manifests():
    values = [("data/ocr_requests/photius-bekker-page13-retry.json", build_page13_retry())]
    values.extend((manifest_path(page).as_posix(), build_retry(page)) for page in sorted(REVIEWS))
    return {sha(encode(manifest)): (path, manifest) for path, manifest in values}


def review_paths(value):
    return [] if value is None else [value] if isinstance(value, Path) else list(value)


def manifest_for_review(path):
    review = json.loads(path.read_bytes())
    authority = known_retry_manifests().get(review.get("manifest_sha256"))
    if authority is None:
        raise ValueError("Unknown source-reviewed retry authority")
    return authority


def checkpoint_selected(manifest, checkpoint):
    scope = manifest.get("checkpoints")
    return scope is None or checkpoint in {(item["model"], item["revision"]) for item in scope}


def allowed_retry_ids(checkpoint, reviews, preparing=False):
    manifests = [value[1] for value in known_retry_manifests().values()] if preparing else [manifest_for_review(path)[1] for path in reviews]
    return {manifest["retry_of"]["page_id"] for manifest in manifests if checkpoint_selected(manifest, checkpoint)}


def apply_all_reviewed_retries(models, paths, reviews):
    files = {sha(path.read_bytes()): path for path in paths}
    if len(files) != len(paths):
        raise ValueError("Repeated retry raw file")
    used_files, used_targets, evidence = set(), set(), []
    for review_path in sorted(reviews, key=lambda path: sha(path.read_bytes())):
        _, manifest = manifest_for_review(review_path)
        review = json.loads(review_path.read_bytes())
        wanted = [run["sha256"] for run in review.get("reviewed_runs", [])]
        if any(digest not in files or digest in used_files for digest in wanted):
            raise ValueError("Missing or reused reviewed retry file")
        targets = {(checkpoint, manifest["retry_of"]["page_id"]) for checkpoint in models if checkpoint_selected(manifest, checkpoint)}
        if targets & used_targets:
            raise ValueError("Repeated retry decision for a checkpoint and page")
        evidence.append(apply_reviewed_retries(models, [files[digest] for digest in wanted], review_path))
        used_files.update(wanted); used_targets.update(targets)
    if used_files != set(files):
        raise ValueError("Retry input lacks its exact completed review")
    return evidence


def apply_reviewed_retries(models, paths, review_path):
    """Keep original records intact and attach one accepted assembly per model."""
    authority_path, manifest = manifest_for_review(review_path)
    manifest_raw = encode(manifest)
    review_raw = review_path.read_bytes()
    review = json.loads(review_raw)
    source = manifest["sources"]["photius-bekker-combined"]
    expected = {page["id"]: page for page in manifest["pages"]}
    page_id = manifest["retry_of"]["page_id"]
    if (review.get("manifest_sha256") != sha(manifest_raw)
            or review.get("source_pdf_sha256") != source["sha256"]
            or review.get("decision") != "replace-source-reviewed-degraded-page"
            or not review.get("reviewed_at") or not review.get("source_evidence")):
        raise ValueError("Retry admission lacks an exact completed source review")
    strip_reviews = review.get("strip_reviews", [])
    if (len(strip_reviews) != len(expected) or {r.get("id") for r in strip_reviews} != set(expected)
            or any(not r.get("source_evidence") or r.get("reading_complete") is not True
                   or r.get("apparatus_excluded") is not True for r in strip_reviews)):
        raise ValueError("Every retry strip needs a completed source review")
    originals = {}
    for (model, revision), records in models.items():
        if not checkpoint_selected(manifest, (model, revision)):
            continue
        raw, meta, row = records[page_id]
        if model in originals or meta["manifest_sha256"] != manifest["retry_of"]["sha256"]:
            raise ValueError("Retry requires one original page attempt per model family")
        originals[model] = (raw, meta, row)
    if manifest.get("checkpoints") and set((item["model"], item["revision"]) for item in manifest["checkpoints"]) != {
            (model, value[1]["revision"]) for model, value in originals.items()}:
        raise ValueError("Retry requires every explicitly listed checkpoint")
    if (len(review.get("original_artifacts_sha256", [])) != len(originals)
            or set(review.get("original_artifacts_sha256", [])) != {r[2]["artifact_sha256"] for r in originals.values()}):
        raise ValueError("Retry review does not identify all original page attempts")
    reviewed_runs = review.get("reviewed_runs", [])
    runs = {run["sha256"]: run for run in reviewed_runs}
    if (len(runs) != len(reviewed_runs) or len(runs) != len(paths)
            or set(runs) != {sha(path.read_bytes()) for path in paths}):
        raise ValueError("Retry review does not identify the exact prediction files")
    images, used, retained = {}, set(), []
    for path in sorted(paths, key=lambda value: sha(value.read_bytes())):
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if not rows or "_meta" not in rows[0] or any("_meta" in row for row in rows[1:]):
            raise ValueError("Ambiguous retry prediction metadata")
        meta, records = rows[0]["_meta"], rows[1:]
        model = meta.get("model")
        original = originals.get(model)
        run = runs[sha(raw)]
        if (not original or model in used or run.get("model") != model
                or run.get("revision") != meta.get("revision") or meta.get("revision") != original[1]["revision"]
                or meta.get("prompt") != manifest["prompt"] or meta.get("manifest_sha256") != sha(manifest_raw)):
            raise ValueError("Retry differs from the original independently pinned checkpoint")
        if len(records) != len(expected) or {r.get("id") for r in records} != set(expected):
            raise ValueError("Retry must contain every reviewed strip exactly once")
        by_id = {row["id"]: row for row in records}
        ordered = []
        for job in sorted(expected.values(), key=lambda page: page["reading_order"]):
            row = by_id[job["id"]]
            if (row.get("source") != job["source"] or row.get("scan_page") != job["scan_page"]
                    or row.get("region") != job["region"]):
                raise ValueError("Retry used unreviewed source geometry")
            prompt = manifest["prompt"] + " " + job["prompt_suffix"]
            if row.get("prompt_sha256") != sha(prompt.encode()):
                raise ValueError("Retry strip prompt differs from the reviewed request")
            if (row.get("error") or row.get("finish_reason") != "stop"
                    or not isinstance(row.get("raw_prediction"), str)
                    or not any("\u0370" <= c <= "\u03ff" or "\u1f00" <= c <= "\u1fff" for c in row["raw_prediction"])):
                raise ValueError("Retry strip is failed, truncated, or lacks Greek text")
            image = row.get("image_sha256")
            if not isinstance(image, str) or len(image) != 64 or images.setdefault(job["id"], image) != image:
                raise ValueError("Retry checkpoints used different source images")
            ordered.append(row)
        text = "\n\n".join(row["raw_prediction"].strip() for row in ordered)
        identity = {"model": model, "revision": meta["revision"], "manifest_sha256": sha(manifest_raw),
                    "source_review_sha256": sha(review_raw), "raw_file_sha256": sha(raw), "strips": ordered}
        assembly = {**identity, "artifact_sha256": sha(encode(identity)), "accepted_text": text,
                    "reading_order": [row["id"] for row in ordered],
                    "original_record": original[2], "original_raw_file_sha256": sha(original[0]),
                    "source_evidence": review["source_evidence"], "reviewed_at": review["reviewed_at"],
                    "policy": "Only this strip assembly votes for its model family. The original whole-page attempt remains held evidence with no additional vote."}
        key = (model, meta["revision"])
        models[key][page_id] = (original[0], original[1], {**original[2], "reviewed_retry": assembly})
        retained.append({"raw": raw, "sha256": sha(raw), "metadata": meta})
        used.add(model)
    if used != set(originals) or not used:
        raise ValueError("Every selected model family needs a reviewed retry assembly")
    return {"manifest": manifest, "manifest_path": authority_path, "manifest_sha256": sha(manifest_raw),
            "review": review, "review_raw": review_raw, "source_review_sha256": sha(review_raw),
            "raw_files": retained}


def write_source_review(models, paths, output, source_evidence, strip_evidence, reviewed_at, manifest=None):
    """Pin a completed scan comparison; validation happens before any write."""
    if output.exists():
        raise ValueError("Refusing to replace an existing source review")
    manifest = manifest or build_page13_retry()
    if sha(encode(manifest)) not in known_retry_manifests():
        raise ValueError("Unknown source-reviewed retry authority")
    page_id = manifest["retry_of"]["page_id"]
    runs = []
    for path in sorted(paths, key=lambda value: sha(value.read_bytes())):
        raw = path.read_bytes()
        meta = json.loads(raw.splitlines()[0])["_meta"]
        runs.append({"sha256": sha(raw), "model": meta["model"], "revision": meta["revision"]})
    review = {"schema_version": 1, "manifest_sha256": sha(encode(manifest)),
              "source_pdf_sha256": manifest["sources"]["photius-bekker-combined"]["sha256"],
              "decision": "replace-source-reviewed-degraded-page", "reviewed_at": reviewed_at,
              "source_evidence": source_evidence,
              "strip_reviews": [{"id": page["id"], "source_evidence": strip_evidence[page["id"]],
                                 "reading_complete": True, "apparatus_excluded": True} for page in manifest["pages"]],
              "original_artifacts_sha256": [records[page_id][2]["artifact_sha256"] for checkpoint, records in models.items()
                                            if checkpoint_selected(manifest, checkpoint)],
              "reviewed_runs": runs}
    raw = encode(review)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "source-review.json"
        path.write_bytes(raw)
        apply_reviewed_retries(copy.deepcopy(models), paths, path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return review


def main():
    import argparse
    from ingest_photius_coverage import prepare_fresh_inputs, scan_manifest, build_later_gap
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh", type=Path, action="append", required=True)
    parser.add_argument("--retry", type=Path, action="append", required=True)
    parser.add_argument("--manifest", type=Path, help="Pinned retry request; defaults to the original page13 request")
    parser.add_argument("--source-evidence", required=True)
    parser.add_argument("--strip-evidence", type=Path, required=True,
                        help="JSON object mapping each strip ID to its completed scan-review evidence")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    _, models, _ = prepare_fresh_inputs(args.fresh, [scan_manifest(), build_later_gap()],
                                      allow_unreviewed_retry_preparation=True)
    write_source_review(models, args.retry, args.out, args.source_evidence,
                        json.loads(args.strip_evidence.read_text()), datetime.now(timezone.utc).isoformat(),
                        json.loads(args.manifest.read_bytes()) if args.manifest else None)
    print("Pinned completed source review; original attempts remain held evidence")


if __name__ == "__main__":
    main()
