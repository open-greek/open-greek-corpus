#!/usr/bin/env python3
"""Pin enlarged, source-reviewed retries without changing original OCR attempts."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "data/ingest_reviews/coverage/mathematical-ocr-jobs.json"
MANIFEST_SHA256 = "5aae2940256591d8b0368c136e8b885eb6a294be48e877cded762f2aa40f7bf3"
ORIGINAL_SHA256 = "89906fcbfa14616a9031ebeb8b1cd35b949a2afa986ac64cbe3db726a45db3e8"
MODEL = "Qwen/Qwen3.6-27B"
REVISION = "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"
OUTPUT = "data/ingest_reviews/coverage/mathematical-qwen36-reviewed-retry.json"
# Every edge was inspected between complete printed lines. Diagram prose is
# ordered top block, right-hand continuation, then the full-width lower block.
REGIONS = {
    "apolloniipergaei01apoluoft-pdf0190": [[.10,.075,.97,.363],[.10,.363,.97,.6185],[.10,.6185,.97,.852]],
    "apolloniipergaei01apoluoft-pdf0232": [[.10,.065,.97,.35],[.10,.35,.97,.5861],[.10,.5861,.97,.842]],
    "pappialexandrin01pappgoog-pdf0039": [[.24,.15,.84,.297],[.24,.532,.84,.6978],[.24,.6978,.84,.815]],
    "pappialexandrin01pappgoog-pdf0281": [[.21,.15,.84,.365],[.21,.365,.84,.501],[.21,.501,.84,.684]],
    "pappialexandrin01pappgoog-pdf0459": [[.22,.15,.83,.391],[.58,.391,.83,.521],[.22,.521,.83,.731]],
}
FINDINGS = {
    "apolloniipergaei01apoluoft-pdf0190": "Printed172: accents and breathings are visible throughout the complete body, including Μὴ ἔστω δὴ ἡ δεδομένη γωνία ὀρθή. Original output has no accents and only two breathing marks.",
    "apolloniipergaei01apoluoft-pdf0232": "Printed214: accents and breathings are visible throughout, including δέ τι σημεῖον ἕτερον and Ἐὰν ἐν τῷ ἀφοριζομένῳ. Original output has no accents or breathings.",
    "pappialexandrin01pappgoog-pdf0039": "Printed496: both text blocks surrounding the diagram are polytonic, including ἄρα πόλῳ and καὶ ἐπεὶ τὸ Π σημεῖον. Original output has no accents or breathings. Diagram and its labels remain source-image material.",
    "pappialexandrin01pappgoog-pdf0281": "Printed738: breathings are visible throughout, including Ἐπεὶ γὰρ δέδεικται, ἴσον, and ὑπὸ. Original output retains some accent marks but no breathing marks. Apparatus below the rule is excluded.",
    "pappialexandrin01pappgoog-pdf0459": "Printed916: original output appends the small apparatus below the rule, beginning 4. ἀπὸ τῶν and containing add., corr., retinuit and recte. The body ends Γεγονέτω. ἐπεὶ οὖν ἴσον ἐστὶν τὸ ΖΓΗ τρίγωνον τῷ. Three regions retain the top body, right-of-diagram continuation, and bottom body, including the next proposition heading; apparatus and diagram labels are excluded.",
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def prepare(original, predictions, pdf_dir, output):
    raw = original.read_bytes()
    if sha(raw) != MANIFEST_SHA256 or sha(predictions.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError("Original mathematical request or complete Qwen3.6 run changed")
    prior = json.loads(raw)
    values = [json.loads(line) for line in predictions.read_bytes().splitlines() if line.strip()]
    metadata = values[0]["_meta"]
    if (metadata.get("model"), metadata.get("revision"), metadata.get("manifest_sha256"), metadata.get("prompt")) != (MODEL, REVISION, MANIFEST_SHA256, prior["prompt"]):
        raise ValueError("The reviewed checkpoint or prompt changed")
    originals = {r["id"]: r for r in values[1:]}
    pages = {p["id"]: p for p in prior["pages"]}
    if len(originals) != 556 or len(values) != 557 or set(originals) != set(pages):
        raise ValueError("Original complete556 run must remain immutable")
    jobs = []
    checked = {}
    for identifier, regions in REGIONS.items():
        page = pages[identifier]
        source = prior["sources"][page["source"]]
        pdf = pdf_dir / (page["source"] + ".pdf")
        if sha(pdf.read_bytes()) != source["sha256"]:
            raise ValueError("Reviewed mathematical source PDF changed")
        row = originals[identifier]
        if row.get("finish_reason") != "stop" or row.get("error"):
            raise ValueError("Reviewed original attempt differs from the complete run")
        checked[identifier] = {"original_prediction_sha256": sha(encode(row)),
            "original_image_sha256": row["image_sha256"], "source_pdf_sha256": source["sha256"],
            "source_evidence": FINDINGS[identifier], "original_text": row["raw_prediction"]}
        for order, region in enumerate(regions, 1):
            jobs.append({**page, "id": identifier + f"-reviewed-strip-{order}",
                "region": region, "max_side": 3200, "reading_order": order,
                "reconstructs": identifier, "text_role": "authorial-prose",
                "crop_evidence": "Source-inspected whitespace between complete printed lines; enlarged body only, excluding apparatus, running headers and diagram labels"})
    manifest = {"schema_version": 1, "purpose": "Source-reviewed Qwen3.6 retry after four severe polytonic-loss cases and one apparatus leak; original556 predictions remain immutable.",
        "sources": prior["sources"], "prompt": prior["prompt"],
        "retry_of": {"path": MANIFEST, "sha256": MANIFEST_SHA256,
            "original_predictions_sha256": ORIGINAL_SHA256, "model": MODEL, "revision": REVISION,
            "region_ids": list(REGIONS)},
        "review": {"recorded_at": "2026-10-18", "extent": "All five complete source pages, every printed body line, all diagram/apparatus boundaries and all15 retry crop edges inspected. The other551 Qwen3.6 pages were screened by the frozen detector and text anomalies, without exhaustive pixel review.",
            "findings": checked,
            "policy": "Do not change predictions or choose a model automatically. Retain every original and retry. Require an explicit source review of completed strips before one assembled Qwen3.6 vote replaces the original vote for these five pages. Other model inputs remain separate witnesses; no invented cross-region joined words."},
        "pages": jobs}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encode(manifest))
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, default=ROOT / MANIFEST)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / OUTPUT)
    a = p.parse_args()
    result = prepare(a.original, a.predictions, a.pdf_dir, a.out)
    print(f"Pinned {len(result['pages'])} reviewed regions from {len(REGIONS)} pages")


if __name__ == "__main__":
    main()
