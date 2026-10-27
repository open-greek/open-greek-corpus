#!/usr/bin/env python3
"""Count every primary source component without assigning work-wide quality.

Generate this report before the catalog, provenance table and release. --check
recomputes all counts; ordinary consumers verify complete corpus and recipe pins.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from frequency_projection import ANALYSIS_COUNT_BASIS, FrequencyProjection, projection_recipe_pins

ROOT = Path(__file__).resolve().parents[1]
NAME = "source_component_tokens.json"
OCR_SOURCES = frozenset({"ocr", "cgpg", "greek_library"})
GK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
MIXED_STATUS = "mixed-unassessed"
SCOPE = (
    "Source, edition and license describe components. Correction stamps do not "
    "establish correction coverage of another component; mixed OCR/digital "
    "works have no assessed whole-work correction status."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode()


def corpus_pins(data):
    return {p.name: sha(p.read_bytes()) for p in sorted((data / "corpus").glob("*.jsonl"))}


def corpus_hash(pins):
    # Sort the canonical slug lines, as the release does. Filename ordering
    # differs when one slug prefixes another (work.jsonl versus work-extra.jsonl).
    text = "".join(sorted(f"{Path(name).stem}\t{digest}\n" for name, digest in pins.items()))
    return sha(text.encode())


def recipe_pins():
    path = Path(__file__)
    return {path.name: sha(path.read_bytes()), **projection_recipe_pins()}


def build(data):
    data = Path(data)
    projection = FrequencyProjection(data)
    works, by_source = {}, defaultdict(Counter)
    for path in sorted((data / "corpus").glob("*.jsonl")):
        components = defaultdict(Counter)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                source = row.get("source")
                if not isinstance(source, str) or not source:
                    raise ValueError("Source component requires an explicit row.source: " + path.name)
                # The masked-column pipeline is an OCR method, not a provider.
                # Match reconcile_corpus_editions for older unnormalized rows.
                source = "ocr" if source == "ocr-masked" else source
                key = (source, row.get("edition") or "", row.get("license") or "")
                components[key]["passages"] += 1
                components[key]["analysis_tokens"] += len(GK.findall(projection.text(row)))
        source_counts = defaultdict(Counter)
        entries = []
        for (source, edition, license_), counts in sorted(components.items()):
            entries.append({"source": source, "edition": edition, "license": license_, **counts})
            source_counts[source].update(counts)
        sources = set(source_counts)
        ocr_counts, non_ocr_counts = Counter(), Counter()
        for source, counts in source_counts.items():
            (ocr_counts if source in OCR_SOURCES else non_ocr_counts).update(counts)
            by_source[source].update(counts)
            by_source[source]["works"] += 1
        mixed = bool(sources & OCR_SOURCES and sources - OCR_SOURCES)
        works[path.stem] = {
            "components": entries,
            "sources": dict(source_counts),
            "passages": sum(c["passages"] for c in components.values()),
            "analysis_tokens": sum(c["analysis_tokens"] for c in components.values()),
            "ocr_passages": ocr_counts["passages"],
            "ocr_analysis_tokens": ocr_counts["analysis_tokens"],
            "non_ocr_passages": non_ocr_counts["passages"],
            "non_ocr_analysis_tokens": non_ocr_counts["analysis_tokens"],
            "mixed_ocr_digital": mixed,
            "correction_scope": SCOPE if mixed else (
                "Homogeneous OCR/digital source category; existing work-level "
                "correction classification applies."
            ),
        }
    pins = corpus_pins(data)
    return {
        "schema_version": 1,
        "generated_by": "scripts/build_source_components.py",
        "counting_basis": ANALYSIS_COUNT_BASIS,
        "ocr_source_labels": sorted(OCR_SOURCES),
        "input_corpus_files": pins,
        "corpus_sha256": corpus_hash(pins),
        "frequency_projection_sha256": projection.digest,
        "recipe_sha256": recipe_pins(),
        "scope": SCOPE,
        "works": works,
        "by_source": dict(by_source),
        "totals": {
            "works": len(works),
            "passages": sum(w["passages"] for w in works.values()),
            "analysis_tokens": sum(w["analysis_tokens"] for w in works.values()),
            "ocr_works": sum(w["ocr_passages"] > 0 for w in works.values()),
            "ocr_passages": sum(w["ocr_passages"] for w in works.values()),
            "ocr_analysis_tokens": sum(w["ocr_analysis_tokens"] for w in works.values()),
            "mixed_works": sum(w["mixed_ocr_digital"] for w in works.values()),
            "mixed_ocr_analysis_tokens": sum(
                w["ocr_analysis_tokens"] for w in works.values() if w["mixed_ocr_digital"]
            ),
        },
    }


def load_verified(data):
    data = Path(data)
    path = data / NAME
    if not path.is_file():
        raise ValueError("Missing source component report; run build_source_components.py")
    report = json.loads(path.read_bytes())
    if not same_measurements(report, build(data)):
        raise ValueError("Source component report is stale; run build_source_components.py")
    return report


def same_measurements(left, right):
    """Recompute public counts and input pins from the published lexical text."""
    fields = ("schema_version", "input_corpus_files", "corpus_sha256", "ocr_source_labels",
        "works", "by_source", "totals", "scope")
    return all(left.get(field) == right.get(field) for field in fields)


def summary(report, data):
    return {
        "artifact": "data/" + NAME,
        "sha256": sha((Path(data) / NAME).read_bytes()),
        "corpus_sha256": report["corpus_sha256"],
        "counting_basis": report["counting_basis"],
        "totals": report["totals"],
        "by_source": report["by_source"],
        "mixed_works": {slug: work for slug, work in report["works"].items()
                        if work["mixed_ocr_digital"]},
        "scope": SCOPE,
    }


def validate_catalog(report, rows):
    """Reject stale work totals/status even when compensating errors sum equally."""
    by_slug = {row["slug"]: row for row in rows}
    if set(by_slug) != set(report["works"]) or len(by_slug) != len(rows):
        raise ValueError("Catalog and source component report have different work sets")
    for slug, work in report["works"].items():
        row = by_slug[slug]
        if (int(row["tokens"]) != work["analysis_tokens"] or
                row["sha256"] != report["input_corpus_files"][slug + ".jsonl"] or
                int(row["passages"]) != work["passages"]):
            raise ValueError("Catalog and source component counts differ: " + slug)
        if work["mixed_ocr_digital"] and row["correction"] != MIXED_STATUS:
            raise ValueError("Mixed work requires mixed-unassessed correction status: " + slug)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = args.root / "data"
    result = build(data)
    raw = encode(result)
    path = data / NAME
    if args.check:
        if not path.is_file() or not same_measurements(json.loads(path.read_bytes()), result):
            parser.exit(1, "Source component counts differ; run build_source_components.py\n")
    else:
        path.write_bytes(raw)
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
