#!/usr/bin/env python3
"""Recompute five-work boundary evidence without altering corpus text or loci."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from coverage_resolution import resolution

ROOT = Path(__file__).resolve().parents[1]
NS = {"t": "http://www.tei-c.org/ns/1.0"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(config, corpus, roots):
    decisions = json.loads(config.read_text())
    editions = json.loads((corpus / "data/corpus_editions.json").read_text())
    result = []
    for case in decisions["cases"]:
        slug = case["slug"]
        path = corpus / "data/corpus" / (slug + ".jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        current = resolution(corpus, slug)
        evidence = {**case, "historical_status": case["status"],
                    "status": current["status"], "resolution": current,
                    "corpus_file_sha256": sha(path), "edition": editions[slug],
                    "passages": len(rows), "opening": rows[:3], "ending": rows[-3:],
                    "locus_prefixes": dict(Counter(r["locus"].split(".")[0] for r in rows)),
                    "book_headings": [{"locus": r["locus"], "text": r["text"]} for r in rows
                        if len(r["text"]) < 120 and re.search("ΒΙΒΛ|Βιβλ|ΤΟΜΟΣ|Τόμος", r["text"])]}
        if "source_path" in case:
            source = roots[case["source_root"]] / case["source_path"]
            if sha(source) != case["source_sha256"]:
                raise ValueError(f"Source changed; review boundary evidence again: {slug}")
            root = ET.parse(source).getroot()
            description = root.find(".//t:sourceDesc", NS)
            evidence["tei_source_description"] = " ".join("".join(description.itertext()).split())
            evidence["tei_books"] = [{"n": node.get("n"),
                "headings": [" ".join("".join(h.itertext()).split()) for h in node.findall("t:head", NS)]}
                for node in root.findall(".//t:div[@subtype='book']", NS)]
        result.append(evidence)
    return {"schema_version": 1, "decisions_sha256": sha(config),
            "generated_by": "scripts/audit_completeness_batch.py", "cases": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "data/inventory/completeness-batch.json")
    parser.add_argument("--corpus-dir", type=Path, default=ROOT)
    parser.add_argument("--first1k-dir", type=Path, required=True)
    parser.add_argument("--perseus-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "data/inventory/completeness-batch-report.json")
    args = parser.parse_args()
    result = audit(args.config, args.corpus_dir, {"first1k": args.first1k_dir, "perseus": args.perseus_dir})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({r["slug"]: r["status"] for r in result["cases"]}, indent=2))


if __name__ == "__main__":
    main()
