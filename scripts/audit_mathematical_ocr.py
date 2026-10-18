#!/usr/bin/env python3
"""Screen retained mathematical predictions without selecting or changing text."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from report_polytonic_loss import POLICY, detect, dump
from prepare_mathematical_ocr_retries import MANIFEST, MANIFEST_SHA256, REGIONS, FINDINGS, encode, sha

ROOT = Path(__file__).resolve().parents[1]


def read_prefix(path, limit=None):
    """A numbered complete prefix remains reproducible as a shard is appended."""
    lines = path.read_bytes().splitlines(keepends=True)
    selected = []
    count = 0
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if line == lines[-1] and not line.endswith(b"\n"):
                break
            raise
        if "_meta" not in record:
            if limit is not None and count == limit:
                break
            count += 1
        selected.append(line)
    if limit is not None and count != limit:
        raise ValueError("Requested retained shard prefix is not complete")
    return b"".join(selected)


def audit_predictions(path, manifest, prefix=None):
    raw = read_prefix(path, prefix)
    values = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not values or set(values[0]) != {"_meta"}:
        raise ValueError("Prediction metadata missing")
    metadata, rows = values[0]["_meta"], values[1:]
    if metadata.get("manifest_sha256") != MANIFEST_SHA256 or metadata.get("prompt") != manifest["prompt"]:
        raise ValueError("Screening request or transcription prompt changed")
    pages = {p["id"]: p for p in manifest["pages"]}
    results = []
    seen = set()
    for row in rows:
        identifier = row["id"]
        if identifier in seen or identifier not in pages:
            raise ValueError("Unknown or repeated mathematical page")
        seen.add(identifier)
        page = pages[identifier]
        if (row.get("source"), row.get("scan_page"), row.get("region")) != (page["source"], page["scan_page"], page.get("region", [0,0,1,1])):
            raise ValueError("Prediction no longer matches source geometry")
        text = row.get("raw_prediction", "")
        if not isinstance(text, str):
            raise ValueError("Prediction is not text")
        # Exploratory apparatus screen, separate from the locked mark detector.
        # Capital Latin-looking geometry labels do not match this expression.
        latin = re.findall(r"\b[A-Za-z]*[a-z][A-Za-z]{2,}\b", text)
        results.append({"id": identifier, "source": page["source"], "scan_page": page["scan_page"],
            "printed_page": page["printed_page"], "work": page["work"],
            "source_pdf_sha256": manifest["sources"][page["source"]]["sha256"],
            "image_sha256": row.get("image_sha256"), "prediction_sha256": sha(text.encode()),
            "finish_reason": row.get("finish_reason"), "failed": bool(row.get("error") or row.get("finish_reason") != "stop"),
            "characters": len(text), "detector": detect(text),
            "exploratory_apparatus_screen": {"candidate": len(latin) >= 2, "lowercase_latin_words": latin}})
    return {"path": "data/evaluation/ocr-fresh/" + path.name, "sha256": sha(raw),
        "artifact_scope": "exact complete JSONL prefix" if prefix is not None else "complete retained JSONL output",
        "prefix_records": prefix, "model": metadata.get("model"), "revision": metadata.get("revision"),
        "runner_sha256": metadata.get("runner_sha256"), "records": len(results),
        "finish_reasons": dict(Counter(r["finish_reason"] for r in results)),
        "flagged": sum(r["detector"]["flag"] for r in results),
        "inapplicable": sum(not r["detector"]["applicable"] for r in results),
        "apparatus_candidates": sum(r["exploratory_apparatus_screen"]["candidate"] for r in results),
        "pages": results}


def report(manifest_path, predictions, prefixes, out):
    manifest_raw = manifest_path.read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256:
        raise ValueError("Reviewed mathematical manifest changed")
    manifest = json.loads(manifest_raw)
    scans = {p["id"]: p for p in manifest["pages"]}
    reviews = [{"id": identifier, "scan_page": scans[identifier]["scan_page"],
        "printed_page": scans[identifier]["printed_page"],
        "source_pdf_sha256": manifest["sources"][scans[identifier]["source"]]["sha256"],
        "reviewed_at": "2026-10-18", "extent": "Complete source page and all retry crop boundaries inspected",
        "finding": FINDINGS[identifier],
        "decision": "request bounded retry; do not change or select predictions",
        "retry_request": "data/ingest_reviews/coverage/mathematical-qwen36-reviewed-retry.json"}
        for identifier in REGIONS]
    reviews.append({"id": "apolloniipergaei01apoluoft-pdf0208", "scan_page": 208, "printed_page": 190,
        "source_pdf_sha256": manifest["sources"]["apolloniipergaei01apoluoft"]["sha256"],
        "reviewed_at": "2026-10-18", "extent": "Complete source page inspected because both detector results are sparse and this pair has the largest relative length difference",
        "finding": "The printed body is only four short lines at the end of BookI, with visible marks; detector inapplicability is expected. Qwen3.6 additionally includes the isolated running header ΚΩΝΙΚΩΝ α'. Qwen3.8 starts the actual body. No apparatus was included by either model.",
        "decision": "No new OCR retry; remove only the source-verified running header through the separately audited ingestion rule."})
    from prepare_mathematical_qwen38_retry import OUTPUT as QWEN38_REQUEST, PAGE_ID, MODEL as QWEN38_MODEL
    qwen38 = json.loads((ROOT / QWEN38_REQUEST).read_text())
    page = scans[PAGE_ID]
    if qwen38["retry_of"]["sha256"] != MANIFEST_SHA256 or qwen38["sources"] != manifest["sources"]:
        raise ValueError("Additional Qwen3.8 source review no longer identifies the same edition")
    reviews.append({"id": PAGE_ID, "model": QWEN38_MODEL, "scan_page": page["scan_page"],
        "printed_page": page["printed_page"], "source_pdf_sha256": qwen38["review"]["source_pdf_sha256"],
        "reviewed_at": qwen38["review"]["recorded_at"], "extent": qwen38["review"]["extent"],
        "finding": qwen38["review"]["finding"], "decision": "Request bounded retry; preserve original shard and every model input",
        "retry_request": QWEN38_REQUEST})
    result = {"schema_version": 1, "reviewed_at": "2026-10-18",
        "manifest": {"path": MANIFEST, "sha256": sha(manifest_raw)},
        "frozen_polytonic_policy": POLICY, "policy_sha256": sha(dump(POLICY)),
        "exploratory_apparatus_policy": "At least two Latin words containing a lowercase letter, each at least three letters. This post-inference screen only locates cases for source inspection; it has no measured sensitivity and never changes text.",
        "inputs": [audit_predictions(p, manifest, prefixes.get(p.name)) for p in predictions],
        "source_reviews": reviews,
        "operating_limits": ["No independent complete transcription was made for these pages; source review confirms visible printed marks and layout, without reporting truth-aligned mark recall or error rates.",
            "All supplied predictions were screened; only the specifically listed source_reviews received complete pixel review. Remaining page pixels were not exhaustively reviewed for Greek-only apparatus leakage.",
            "Model disagreement and detector scores do not authorize witness selection. A retry requires a separate completed scan comparison bound to its exact bytes.",
            "A numbered shard prefix is a snapshot; later records must be screened separately before their admission."]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(encode(result))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=ROOT / MANIFEST)
    p.add_argument("--prediction", type=Path, action="append", required=True)
    p.add_argument("--prefix", action="append", default=[], help="FILE_NAME=RECORD_COUNT for an exact append-only shard snapshot")
    p.add_argument("--out", type=Path, default=ROOT / "data/evaluation/mathematical-source-review/report.json")
    a = p.parse_args()
    prefixes = {key: int(value) for key, value in (v.rsplit("=", 1) for v in a.prefix)}
    result = report(a.manifest, a.prediction, prefixes, a.out)
    print(json.dumps([{key: value for key, value in i.items() if key != "pages"} for i in result["inputs"]], ensure_ascii=False))


if __name__ == "__main__":
    main()
