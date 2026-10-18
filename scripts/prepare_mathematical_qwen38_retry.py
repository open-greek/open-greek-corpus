#!/usr/bin/env python3
"""Pin the confirmed Qwen3.8 mark-loss page without modifying any raw shard."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from prepare_mathematical_ocr_retries import MANIFEST, MANIFEST_SHA256, encode, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PART_SHA256 = "75883f461b16d281042c444ab4b6f9cda96db89fde78f5addaa6c302063e7daa"
MODEL = "Qwen/Qwen3.8-27B-FP8"
REVISION = "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"
PAGE_ID = "pappialexandrin01pappgoog-pdf0345"
REGIONS = [[.22,.15,.83,.23], [.22,.425,.83,.59], [.22,.59,.83,.723]]
OUTPUT = "data/ingest_reviews/coverage/mathematical-qwen38-reviewed-retry.json"


def prepare(original, predictions, pdf_dir, output):
    manifest_raw, original_raw = original.read_bytes(), predictions.read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256 or sha(original_raw) != SOURCE_PART_SHA256:
        raise ValueError("Original mathematical request or completed Qwen3.8 shard03 changed")
    prior = json.loads(manifest_raw)
    values = [json.loads(line) for line in original_raw.splitlines() if line.strip()]
    meta = values[0]["_meta"]
    if (meta.get("model"), meta.get("revision"), meta.get("prompt"), meta.get("manifest_sha256")) != (MODEL, REVISION, prior["prompt"], MANIFEST_SHA256):
        raise ValueError("Reviewed Qwen3.8 checkpoint or request changed")
    rows = {r["id"]: r for r in values[1:]}
    if len(rows) != 102 or len(values) != 103 or PAGE_ID not in rows:
        raise ValueError("The completed original shard must remain intact")
    page = next(p for p in prior["pages"] if p["id"] == PAGE_ID)
    source = prior["sources"][page["source"]]
    if sha((pdf_dir / (page["source"] + ".pdf")).read_bytes()) != source["sha256"]:
        raise ValueError("Reviewed Pappus source PDF changed")
    row = rows[PAGE_ID]
    result = {"schema_version": 1,
        "purpose": "Source-reviewed retry for Qwen3.8 systematic mark loss on Pappus printed802; preserve the complete original shard and all other model inputs.",
        "sources": prior["sources"], "prompt": prior["prompt"],
        "retry_of": {"path": MANIFEST, "sha256": MANIFEST_SHA256,
            "source_part": "data/evaluation/ocr-fresh/mathematical-qwen38-shard-03.jsonl",
            "source_part_sha256": SOURCE_PART_SHA256, "model": MODEL, "revision": REVISION,
            "region_ids": [PAGE_ID]},
        "review": {"recorded_at": "2026-10-18", "extent": "Complete PDF345/printed802, both prose blocks, the intervening diagram, apparatus separator and all three crop boundaries inspected.",
            "finding": "The original prediction has781 Greek letters and no accents or breathings. The scan visibly prints polytonic marks throughout, including μείζων ἐστὶν ἡ ΑΔ, Λέγω δὲ ὅτι καὶ μόνον, and Ἵνα δὲ καὶ ἐπιγνῶμεν. Three enlarged regions retain every body line in order, excluding the running header, diagram labels and small apparatus below the rule.",
            "original_prediction_sha256": sha(encode(row)), "original_image_sha256": row["image_sha256"],
            "source_pdf_sha256": source["sha256"], "original_text": row["raw_prediction"],
            "policy": "Retain all original and retry bytes. Require completed scan comparison of the three strips before replacing this Qwen3.8 input once. Never select Qwen3.6 instead or count the same model twice."},
        "pages": [{**page, "id": PAGE_ID + f"-reviewed-strip-{order}", "region": region,
            "max_side": 3200, "reading_order": order, "reconstructs": PAGE_ID,
            "text_role": "authorial-prose", "crop_evidence": "Source-inspected complete lines and whitespace; top prose followed by two lower-body strips around the excluded diagram"}
            for order, region in enumerate(REGIONS, 1)]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encode(result))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, default=ROOT / MANIFEST)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / OUTPUT)
    a = p.parse_args()
    result = prepare(a.original, a.predictions, a.pdf_dir, a.out)
    print(f"Pinned {len(result['pages'])} Qwen3.8 retry strips")


if __name__ == "__main__":
    main()
