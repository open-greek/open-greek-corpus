#!/usr/bin/env python3
"""Flag suspected systematic loss of printed polytonic marks, without selecting text.

The fresh validation sample excludes both earlier OCR evaluation manifests by
physical page identity, source-image/XML hashes, and ground-truth text hashes.
Detector and truth-label thresholds are pinned before fresh inference.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import unicodedata

import benchmark_page_ocr as benchmark

ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS = ["data/evaluation/ocr-pages.json", "data/evaluation/ocr-preflight/manifest.json"]
DEFAULT_OUT = ROOT / "data/evaluation/polytonic-loss"
POLICY = {"schema_version": 1, "locked_date": "2026-10-18",
    "purpose": "Review flag only; no automatic witness selection or corpus text changes.",
    "selection_seed": 20261018, "calibration_pages": 20, "test_pages": 40,
    "detector": {"minimum_greek_letters": 200, "maximum_uppercase_fraction": .8,
        "minimum_accented_letter_rate": .06, "minimum_breathing_letter_rate": .012,
        "flag_when": "either mark rate is below its minimum on an applicable page"},
    "truth_label": {"minimum_matched_greek_letters": 200,
        "minimum_base_text_recall": .7, "minimum_accent_opportunities": 25,
        "minimum_breathing_opportunities": 15, "systematic_loss_mark_recall_below": .5,
        "label_when": "accent or breathing recall below the threshold on matching base-letter positions"},
    "selection_policy": "No model or reading is selected. All raw predictions, failed pages, false positives and missed cases remain in the report.",
    "operating_limits": ["Counts alone cannot distinguish damaged polytonic text from intentional monotonic or all-capital orthography.",
        "Sparse pages and pages with too little base-letter alignment need a source review rather than a diacritic-loss label.",
        "Character-level reference order is checked separately; text-order errors are not diacritic loss.",
        "This fixed sample is bounded by the available editions and does not establish corpus-wide error rates."]}


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def physical_key(name):
    """Recognize old/new labels for the same PG or Gregory scan page."""
    return (("gregory-nazianzus-orations" if "grna" in name.lower() else "pg"),
        *re.findall(r"\d+", name))


def prepare(source_root, out, exclusions=None):
    exclusion_docs = [(ROOT / name, json.loads((ROOT / name).read_text()))
        for name in (exclusions or EXCLUSIONS)]
    old_pages = [p for path, doc in exclusion_docs for p in doc["pages"]]
    keys = {physical_key(page["id"]) for page in old_pages}
    hashes = {page.get(key) for page in old_pages
        for key in ["image_sha256", "xml_sha256", "gold_sha256"]} - {None}
    candidates, rejected, invalid = [], [], []
    for xml in sorted(source_root.rglob("*.xml")):
        try:
            image_name, text = benchmark.page_gold(xml)
        except Exception as error:
            invalid.append({"xml": xml.relative_to(source_root).as_posix(),
                "reason": f"{type(error).__name__}: no usable line-level transcription"})
            continue
        image = xml.parent / image_name
        if not image.is_file():
            image = next((xml.with_suffix(ext) for ext in [".jpg", ".png", ".jpeg", ".tif"]
                if xml.with_suffix(ext).is_file()), None)
        if image is None:
            invalid.append({"xml": xml.relative_to(source_root).as_posix(), "reason": "missing source image"})
            continue
        page = {"id": xml.relative_to(source_root).with_suffix("").as_posix(),
            "xml": xml.relative_to(source_root).as_posix(),
            "image": image.relative_to(source_root).as_posix(),
            "xml_sha256": benchmark.sha256(xml), "image_sha256": benchmark.sha256(image),
            "gold_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "gold_chars": len(benchmark.normalize(text)), "volume": benchmark.edition_group(xml.stem)}
        reasons = []
        if physical_key(page["id"]) in keys:
            reasons.append("previous physical page identity")
        if hashes & {page[key] for key in ["xml_sha256", "image_sha256", "gold_sha256"]}:
            reasons.append("previous image, XML or gold-text hash")
        if reasons:
            rejected.append({"id": page["id"], "reasons": reasons})
        else:
            candidates.append(page)
    rng = random.Random(POLICY["selection_seed"])
    groups = defaultdict(list)
    for page in candidates:
        groups[page["volume"]].append(page)
    for group in groups.values():
        rng.shuffle(group)
    selected = []
    while groups and len(selected) < 60:
        for volume in sorted(list(groups)):
            if len(selected) >= 60:
                break
            selected.append(groups[volume].pop())
            if not groups[volume]:
                del groups[volume]
    if len(selected) != 60:
        raise ValueError(f"Need 60 fresh pages; only {len(selected)} are available")
    by_volume = defaultdict(list)
    for page in selected:
        by_volume[page["volume"]].append(page)
    allocation = {volume: len(pages) // 3 for volume, pages in by_volume.items()}
    remaining = 20 - sum(allocation.values())
    ranked = sorted(by_volume, key=lambda volume: (-(len(by_volume[volume]) % 3),
        hashlib.sha256(f"{POLICY['selection_seed']}:{volume}".encode()).hexdigest()))
    for volume in ranked:
        if not remaining:
            break
        if allocation[volume] < len(by_volume[volume]) - 1:
            allocation[volume] += 1
            remaining -= 1
    if remaining:
        raise ValueError("Cannot create the pinned 20/40 split")
    for volume, pages in by_volume.items():
        for i, page in enumerate(pages):
            page["split"] = "calibration" if i < allocation[volume] else "test"
    policy_bytes = dump(POLICY)
    manifest = {"schema_version": 1, "source": benchmark.SOURCE, "license": "CC-BY-4.0",
        "selection_seed": POLICY["selection_seed"], "available_pages": len(candidates),
        "normalization": "NFC and whitespace only for generic CER; NFD mark counts and base-letter alignment are separate detector metrics.",
        "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(),
        "prior_evaluations_excluded": [{"path": path.relative_to(ROOT).as_posix(),
            "sha256": benchmark.sha256(path), "pages": len(doc["pages"])} for path, doc in exclusion_docs],
        "edition_counts": dict(sorted(Counter(p["volume"] for p in selected).items())),
        "pages": sorted(selected, key=lambda page: (page["volume"], page["id"]))}
    out.mkdir(parents=True, exist_ok=True)
    (out / "policy.json").write_bytes(policy_bytes)
    (out / "manifest.json").write_bytes(dump(manifest))
    (out / "selection-audit.json").write_bytes(dump({"schema_version": 1,
        "excluded_prior_pages": rejected, "unusable_source_files": invalid,
        "selected_pages": len(selected), "eligible_pages": len(candidates),
        "split_counts": dict(Counter(page["split"] for page in selected))}))
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    if args.command == "prepare":
        result = prepare(args.root, args.out)
        print(json.dumps({"pages": len(result["pages"]), "by_edition": result["edition_counts"]}))


if __name__ == "__main__":
    main()
