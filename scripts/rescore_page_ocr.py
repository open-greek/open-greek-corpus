#!/usr/bin/env python3
"""Rescore single-column PAGE crops in geometric line order without editing OCR.

The Calfa benchmark crops contain one printed column, but XML element order is
not always reading order. Retain the original XML and predictions and record
every reference-order repair before producing derived scores.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from benchmark_page_ocr import page_gold, score, sha256, summarize


def ordered_gold(path):
    root = ET.parse(path).getroot()
    ns = {"p": root.tag.split("}")[0][1:]}
    if root.find(".//p:ReadingOrder", ns) is not None:
        raise ValueError(f"Explicit PAGE reading order needs a separate evaluator: {path}")
    lines = []
    for line in root.findall(".//p:TextLine", ns):
        alternatives = sorted(line.findall("p:TextEquiv", ns),
                              key=lambda node: int(node.get("index", "0")))
        text = alternatives[0].findtext("p:Unicode", default="", namespaces=ns).strip() if alternatives else ""
        if not text:
            continue
        coords = line.find("p:Coords", ns)
        if coords is None:
            raise ValueError(f"Missing line coordinates: {path}, {line.get('id')}")
        points = [tuple(map(int, point.split(","))) for point in coords.get("points", "").split()]
        if not points:
            raise ValueError(f"Empty line coordinates: {path}, {line.get('id')}")
        xs, ys = zip(*points)
        lines.append({"id": line.get("id"), "text": text,
                      "bounds": [min(xs), min(ys), max(xs), max(ys)]})
    if not lines:
        raise ValueError(f"No transcribed lines: {path}")
    # Refuse side-by-side text lines instead of interleaving two columns.
    for i, left in enumerate(lines):
        x1, y1, x2, y2 = left["bounds"]
        for right in lines[i + 1:]:
            a1, b1, a2, b2 = right["bounds"]
            overlap = min(y2, b2) - max(y1, b1)
            if overlap > 0.5 * min(y2 - y1, b2 - b1) and (x2 < a1 or a2 < x1):
                raise ValueError(f"Side-by-side lines require column ordering: {path}")
    ordered = sorted(lines, key=lambda line: (line["bounds"][1], line["bounds"][0]))
    return "\n".join(line["text"] for line in ordered), lines, ordered


def build_reference(root, manifest_path, audit_path):
    manifest = json.loads(manifest_path.read_text())
    references, corrections = {}, []
    for page in manifest["pages"]:
        xml, image = root / page["xml"], root / page["image"]
        if sha256(xml) != page["xml_sha256"] or sha256(image) != page["image_sha256"]:
            raise ValueError(f"Changed benchmark input: {page['id']}")
        _, original = page_gold(xml)
        if hashlib.sha256(original.encode()).hexdigest() != page["gold_sha256"]:
            raise ValueError(f"Original reference differs from manifest: {page['id']}")
        corrected, old_lines, new_lines = ordered_gold(xml)
        references[page["id"]] = corrected
        if corrected != original:
            corrections.append({"id": page["id"], "xml": page["xml"],
                "xml_sha256": page["xml_sha256"], "image_sha256": page["image_sha256"],
                "original_text": original, "corrected_text": corrected,
                "evidence": "Single-column scan crop and PAGE line polygon coordinates; sort top to bottom, then left to right. No characters or line contents changed.",
                "original_line_ids": [line["id"] for line in old_lines],
                "corrected_line_ids": [line["id"] for line in new_lines],
                "line_bounds": [{k: line[k] for k in ("id", "bounds")} for line in old_lines]})
    audit = {"schema_version": 1, "source_manifest_sha256": sha256(manifest_path),
             "method": "single-column PAGE line polygon order",
             "generator": "scripts/rescore_page_ocr.py", "generator_sha256": sha256(__file__),
             "pages_checked": len(references), "corrections": corrections}
    previous = json.loads(audit_path.read_text()) if audit_path.exists() else {}
    audit["recorded_at"] = previous.get("recorded_at", datetime.now(timezone.utc).isoformat())
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    return manifest, references


def rescore(root, manifest_path, audit_path, source, output):
    manifest, references = build_reference(root, manifest_path, audit_path)
    records = [json.loads(line) for line in source.read_text().splitlines()]
    metadata, rows = records[0]["_meta"], records[1:]
    if metadata["manifest_sha256"] != sha256(manifest_path):
        raise ValueError("Predictions do not belong to this benchmark")
    pages = {page["id"]: page for page in manifest["pages"]}
    if len(rows) != len(pages) or {row["id"] for row in rows} != set(pages):
        raise ValueError("Rescoring requires every benchmark page exactly once")
    repaired = []
    for row in rows:
        page = pages[row["id"]]
        if row["split"] != page["split"] or row["volume"] != page["volume"]:
            raise ValueError(f"Changed benchmark identity: {row['id']}")
        repaired.append({**row, "metrics": score(references[row["id"]], row["raw_prediction"])})
    metadata = {**metadata, "reference_audit_sha256": sha256(audit_path),
                "source_prediction_sha256": sha256(source),
                "scorer": "scripts/rescore_page_ocr.py", "scorer_sha256": sha256(__file__)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False)
                      for row in [{"_meta": metadata}, *repaired]) + "\n")
    summary = {"_meta": metadata, "metrics": summarize(repaired)}
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["metrics"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "manifest", "audit", "source", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.out.resolve():
        parser.error("Derived scores must not overwrite the original predictions")
    rescore(args.root, args.manifest, args.audit, args.source, args.out)


if __name__ == "__main__":
    main()
