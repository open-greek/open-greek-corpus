#!/usr/bin/env python3
"""Pin source-confirmed unrelated OCR readings without inventing replacement text."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_photius_geometry import ROOT, SOURCE_SHA, SOURCE_URL, known_geometry_supplement_manifests

AUTHORITY = Path("data/ocr_requests/photius-source-abstentions.json")
REVIEWED = {
    "photius-bekker-0252-left-lower-gutter-part01": {
        "text_sha256": "b429d6110d43dc9874835b1f84d17ae592b1fb2010d5aaf2e49ee163e53ccdd3",
        "reason": "Source comparison confirms five faint continuous theological body lines. The outcome instead invents December25, a first-person vision, and a shield. The smaller finite remedy still does not transcribe this source span."},
    "photius-bekker-0252-left-lower-gutter-part02": {
        "text_sha256": "d6b27642beb07cfbc9ca26bcc80002e09f815b7b4f64baca0de595e15b27d15d",
        "reason": "Source comparison confirms the next five continuous body lines. The outcome instead invents repeated church clauses and Anglophones. Accents and breathing marks do not establish correspondence to the printed source."},
    "photius-bekker-0252-left-lower-gutter-part03": {
        "text_sha256": "cadea384fbbf7839622c028d73e6b46c3c25382237865c1cb903542d75ada129",
        "reason": "Source comparison confirms the final five lowercase continuous body lines. The outcome instead invents an uppercase decree with an unprinted heading. It cannot supply a reading or an omission vote."},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build(paths):
    catalog = known_geometry_supplement_manifests()
    found = {}
    for path in paths:
        raw = path.read_bytes(); lines = raw.splitlines()
        if not lines:
            continue
        meta = json.loads(lines[0]).get("_meta", {})
        authority = catalog.get(meta.get("manifest_sha256"))
        if authority is None:
            continue
        manifest = authority[1]
        jobs = {job["id"]: job for job in manifest["pages"]}
        for line in lines[1:]:
            row = json.loads(line); identifier = row.get("id")
            if identifier not in REVIEWED:
                continue
            review = REVIEWED[identifier]; text = row.get("raw_prediction")
            job = jobs[identifier]
            checkpoint = {"model": meta.get("model"), "revision": meta.get("revision")}
            prompt = manifest["prompt"] + " " + job["prompt_suffix"]
            if (identifier in found or checkpoint not in manifest["checkpoints"]
                    or not isinstance(text, str) or sha(text.encode()) != review["text_sha256"]
                    or row.get("finish_reason") != "stop" or row.get("error")
                    or row.get("region") != job["region"] or row.get("source") != job["source"]
                    or row.get("scan_page") != job["scan_page"] or row.get("prompt_sha256") != sha(prompt.encode())):
                raise ValueError("Abstention differs from its exact source-reviewed reading")
            found[identifier] = {"id": identifier, **checkpoint, "manifest_sha256": meta["manifest_sha256"],
                "scan_page": row["scan_page"], "region": row["region"], "source": row["source"],
                "source_pdf_sha256": SOURCE_SHA, "image_sha256": row["image_sha256"],
                "raw_file_sha256": sha(raw), "prediction_record_sha256": sha(line),
                "raw_prediction_sha256": review["text_sha256"], "finish_reason": row["finish_reason"],
                "original_text": text, "voting_text": "", "reason": review["reason"],
                "reviewed_at": "2026-10-18", "classification": "source-confirmed-unrelated-reading"}
    if set(found) != set(REVIEWED):
        raise ValueError("Every source-reviewed abstention needs its exact retained outcome")
    return {"schema_version": 1, "kind": "photius-source-confirmed-abstentions",
        "source_pdf": {"url": SOURCE_URL, "sha256": SOURCE_SHA}, "reviewed_at": "2026-10-18",
        "records": [found[key] for key in sorted(found)],
        "policy": "Retain the complete original readings and every ancestor. These exact source-confirmed unrelated spans abstain rather than vote for a reading or omission; all other independent readings retain their actual support. No corrected text or token majority is invented.",
        "generated_by": "scripts/photius_source_abstentions.py"}


def source_authority():
    path = ROOT / AUTHORITY
    return (AUTHORITY.as_posix(), path.read_bytes()) if path.exists() else (None, None)


def known_abstentions():
    _, raw = source_authority()
    if raw is None:
        return {}
    authority = json.loads(raw)
    if (authority.get("kind") != "photius-source-confirmed-abstentions"
            or authority.get("source_pdf") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or {r["id"] for r in authority["records"]} != set(REVIEWED)):
        raise ValueError("Unknown source-confirmed abstention authority")
    result = {}
    for row in authority["records"]:
        review = REVIEWED[row["id"]]
        if (row["voting_text"] != "" or row["reason"] != review["reason"]
                or sha(row["original_text"].encode()) != review["text_sha256"]
                or row["raw_prediction_sha256"] != review["text_sha256"]):
            raise ValueError("Source abstention changes its original reading or reason")
        key = (row["model"], row["revision"], row["manifest_sha256"], row["id"])
        if key in result:
            raise ValueError("Repeated source-confirmed abstention")
        result[key] = row
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build(sorted(args.raw_dir.rglob("*.jsonl")))
    raw = encode(report); path = ROOT / AUTHORITY
    if args.write:
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("Refusing to change an already pinned abstention authority")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps({"source_confirmed_abstentions": len(report["records"]), "written": args.write}))


if __name__ == "__main__":
    main()
