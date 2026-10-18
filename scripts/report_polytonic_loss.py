#!/usr/bin/env python3
"""Flag suspected systematic loss of printed polytonic marks, without selecting text.

The fresh validation sample excludes both earlier OCR evaluation manifests by
physical page identity, source-image/XML hashes, and ground-truth text hashes.
Detector and truth-label thresholds are pinned before fresh inference.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import difflib
import gzip
import hashlib
import io
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
    name = Path(name).stem
    if "grna" in name.lower():
        return "gregory-nazianzus-orations", int(re.findall(r"\d+", name)[-1])
    match = re.search(r"(?:mpg|PG[_ -]*)(\d+)[_-](\d+)", name, flags=re.I)
    if match:
        return "pg", int(match[1]), int(match[2])
    return "unresolved", name


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


ACCENTS = frozenset(("\u0300", "\u0301", "\u0342"))
BREATHINGS = frozenset(("\u0313", "\u0314"))


def greek_letters(text):
    """Greek base letters plus their NFD marks; spacing marks are not letters."""
    result = []
    for char in unicodedata.normalize("NFD", text):
        if unicodedata.combining(char):
            if result and result[-1] is not None:
                result[-1]["marks"].add(char)
        elif char.isalpha() and ("\u0370" <= char <= "\u03ff" or "\u1f00" <= char <= "\u1fff"):
            result.append({"base": char.casefold().replace("ς", "σ"), "uppercase": char.isupper(), "marks": set()})
        else:
            # A combining mark after punctuation must not migrate to a letter.
            result.append(None)
    return [letter for letter in result if letter is not None]


def detect(text, policy=POLICY):
    letters = greek_letters(text)
    count = len(letters)
    uppercase = sum(letter["uppercase"] for letter in letters)
    accents = sum(bool(letter["marks"] & ACCENTS) for letter in letters)
    breathings = sum(bool(letter["marks"] & BREATHINGS) for letter in letters)
    rules = policy["detector"]
    applicable = count >= rules["minimum_greek_letters"] and uppercase / max(1, count) < rules["maximum_uppercase_fraction"]
    reasons = []
    if applicable and accents / count < rules["minimum_accented_letter_rate"]:
        reasons.append("low-accented-letter-rate")
    if applicable and breathings / count < rules["minimum_breathing_letter_rate"]:
        reasons.append("low-breathing-letter-rate")
    return {"greek_letters": count, "uppercase_letters": uppercase,
            "accented_letters": accents, "breathing_letters": breathings,
            "accented_letter_rate": accents / count if count else None,
            "breathing_letter_rate": breathings / count if count else None,
            "uppercase_fraction": uppercase / count if count else None,
            "applicable": applicable, "flag": bool(reasons), "reasons": reasons,
            "review_state": "independent-witness-needed" if reasons else "not-flagged" if applicable else "insufficient-text-or-uppercase"}


def truth_label(gold, prediction, policy=POLICY):
    reference, output = greek_letters(gold), greek_letters(prediction)
    blocks = difflib.SequenceMatcher(None, [l["base"] for l in reference],
                                   [l["base"] for l in output], autojunk=False).get_matching_blocks()
    pairs = [(i + offset, j + offset) for i, j, length in blocks for offset in range(length)]
    rules = policy["truth_label"]
    result = {"reference_greek_letters": len(reference), "matched_greek_letters": len(pairs),
              "base_text_recall": len(pairs) / max(1, len(reference)), "classes": {}}
    positive, assessed = [], []
    for name, marks, minimum in (("accent", ACCENTS, rules["minimum_accent_opportunities"]),
                                  ("breathing", BREATHINGS, rules["minimum_breathing_opportunities"])):
        opportunities = [(i, j) for i, j in pairs if reference[i]["marks"] & marks]
        retained = sum(bool(output[j]["marks"] & marks) for i, j in opportunities)
        exact = sum((reference[i]["marks"] & marks) == (output[j]["marks"] & marks) for i, j in opportunities)
        recall = retained / len(opportunities) if opportunities else None
        result["classes"][name] = {"opportunities": len(opportunities), "retained": retained,
                                    "mark_presence_recall": recall, "exact_marks_retained": exact}
        if len(opportunities) >= minimum:
            assessed.append(name)
            if recall < rules["systematic_loss_mark_recall_below"]:
                positive.append(name)
    applicable = (len(pairs) >= rules["minimum_matched_greek_letters"] and
                  result["base_text_recall"] >= rules["minimum_base_text_recall"] and bool(assessed))
    result.update({"assessable": applicable, "systematic_loss": bool(positive) if applicable else None,
                   "loss_classes": positive if applicable else [], "assessed_classes": assessed,
                   "label": "systematic-loss" if applicable and positive else "no-systematic-loss" if applicable else "source-review-required"})
    return result


def verify_manifest(manifest_path, policy_path):
    manifest = json.loads(manifest_path.read_text())
    policy = json.loads(policy_path.read_text())
    if benchmark.sha256(policy_path) != manifest["policy_sha256"] or policy != POLICY:
        raise ValueError("Fresh detector policy differs from the locked pre-inference policy")
    if len({p["id"] for p in manifest["pages"]}) != len(manifest["pages"]):
        raise ValueError("Repeated fresh page identity")
    if Counter(p["split"] for p in manifest["pages"]) != Counter({"calibration": 20, "test": 40}):
        raise ValueError("Fresh calibration/test split changed")
    return manifest, policy


def confusion(rows):
    counts = Counter()
    for row in rows:
        if row["failed"]:
            counts["failed_or_truncated"] += 1
        if not row["truth"]["assessable"]:
            counts["unassessable"] += 1
            continue
        truth, flag = row["truth"]["systematic_loss"], row["detector"]["flag"]
        counts["true_positive" if truth and flag else "false_negative" if truth else "false_positive" if flag else "true_negative"] += 1
    for key in ("true_positive", "false_negative", "false_positive", "true_negative", "failed_or_truncated", "unassessable"):
        counts.setdefault(key, 0)
    tp, fp, fn, tn = [counts[k] for k in ("true_positive", "false_positive", "false_negative", "true_negative")]
    return {**dict(counts), "pages": len(rows), "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "specificity": tn / (tn + fp) if tn + fp else None}


def archive_prediction(source, destination):
    """Retain the exact raw run, refusing to replace another recorded attempt."""
    raw = source.read_bytes()
    if destination.exists() and destination.read_bytes() != raw:
        raise ValueError("A different raw prediction archive already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return destination


def validate_fresh(source_root, manifest_path, policy_path, predictions, review_path=None):
    manifest, policy = verify_manifest(manifest_path, policy_path)
    gold = {}
    for page in manifest["pages"]:
        xml, image = source_root / page["xml"], source_root / page["image"]
        if benchmark.sha256(xml) != page["xml_sha256"] or benchmark.sha256(image) != page["image_sha256"]:
            raise ValueError("Fresh validation source changed")
        text = benchmark.page_gold(xml)[1]
        if hashlib.sha256(text.encode()).hexdigest() != page["gold_sha256"]:
            raise ValueError("Fresh validation transcription changed")
        gold[page["id"]] = text
    review = json.loads(review_path.read_text()) if review_path else None
    if review is not None:
        if review["manifest_sha256"] != benchmark.sha256(manifest_path):
            raise ValueError("Scan review belongs to another fresh manifest")
        if {p["id"] for p in review["pages"]} != set(gold) or not all(p["scan_reviewed"] is True for p in review["pages"]):
            raise ValueError("Every fresh source page needs a recorded scan review")
        if len(review["pages"]) != len(gold):
            raise ValueError("Repeated scan-review page")
        selected = {p["id"]: p for p in manifest["pages"]}
        for page in review["pages"]:
            if any(page.get(key) != selected[page["id"]][key]
                   for key in ("image_sha256", "xml_sha256", "gold_sha256")):
                raise ValueError("Scan-review source hashes changed")
    reviewed = {page["id"]: page for page in review["pages"]} if review else {}
    runs = []
    for path in predictions:
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        metadata, pages = records[0]["_meta"], records[1:]
        if metadata["manifest_sha256"] != benchmark.sha256(manifest_path):
            raise ValueError("Fresh predictions belong to another evaluation")
        if metadata.get("prompt") != benchmark.PROMPT or not metadata.get("revision"):
            raise ValueError("Fresh predictions need the pinned transcription prompt and model revision")
        benchmark.validate_page_rows(manifest, pages, complete=True)
        rows = []
        for page in pages:
            text = page["raw_prediction"]
            failed = page.get("finish_reason") != "stop" or not text.strip()
            truth = truth_label(gold[page["id"]], text, policy)
            if failed:
                truth.update({"assessable": False, "systematic_loss": None, "label": "failed-or-truncated-output"})
            if page["id"] in reviewed and reviewed[page["id"]].get("reference_order") != "verified":
                truth.update({"assessable": False, "systematic_loss": None, "label": "reference-order-review-required"})
            elif page["id"] in reviewed and reviewed[page["id"]].get("reference_coverage") != "verified":
                truth.update({"assessable": False, "systematic_loss": None, "label": "reference-coverage-review-required"})
            rows.append({"id": page["id"], "split": page["split"], "volume": page["volume"],
                         "raw_prediction": text, "finish_reason": page.get("finish_reason"), "failed": failed,
                         "generation_tokens": page.get("generation_tokens"), "error": page.get("error"),
                         "detector": detect(text, policy), "truth": truth,
                         "metrics": benchmark.score(gold[page["id"]], text)})
        try:
            archive_path = path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            archive_path = None
        all_outcomes = confusion(rows)
        measurement_limits = []
        if all_outcomes["true_positive"] + all_outcomes["false_negative"] == 0:
            measurement_limits.append("No assessable systematic-loss case was observed; this run cannot estimate sensitivity or recall.")
        if all_outcomes["true_positive"] + all_outcomes["false_positive"] == 0:
            measurement_limits.append("No assessable page was flagged; this run cannot estimate positive predictive precision.")
        runs.append({"metadata": metadata, "predictions_sha256": benchmark.sha256(path),
                     "predictions_path": archive_path,
                     "measurement_limits": measurement_limits,
                     "by_split": {split: confusion([r for r in rows if r["split"] == split]) for split in ("calibration", "test")},
                     "false_positives": [r["id"] for r in rows if r["truth"]["assessable"] and not r["truth"]["systematic_loss"] and r["detector"]["flag"]],
                     "missed_cases": [r["id"] for r in rows if r["truth"]["assessable"] and r["truth"]["systematic_loss"] and not r["detector"]["flag"]],
                     "unassessable_pages": [r["id"] for r in rows if not r["truth"]["assessable"]], "pages": rows})
    return {"schema_version": 1, "manifest_sha256": benchmark.sha256(manifest_path),
            "policy_sha256": benchmark.sha256(policy_path), "scan_review_sha256": benchmark.sha256(review_path) if review_path else None,
            "scan_review_complete": review is not None, "selection_rule": None,
            "operating_limits": policy["operating_limits"], "runs": runs,
            "generated_by": "scripts/report_polytonic_loss.py validate"}


def page_identity(row):
    refs = row.get("physical_refs", {})
    if refs.get("scan_page") is not None:
        source = refs.get("scan_sha256") or refs.get("source") or refs.get("edition")
        # The same page number in two volumes is two different physical pages.
        if source:
            return f"{source}:{refs['scan_page']}", "explicit-scan-page"
        return str(row.get("locus", refs["scan_page"])), "unresolved-physical-page"
    refs = row.get("source_location", {})
    if refs.get("scan_page") is not None and refs.get("source"):
        return f"{refs['source']}:{refs['scan_page']}:{refs.get('region', 'whole-page')}", "explicit-source-region"
    locus = str(row.get("locus", ""))
    if re.search(r"_\d+[.]\d+$", locus):
        return locus.rsplit(".", 1)[0], "edition-page-prefix"
    if re.fullmatch(r"\d+[.]\d+", locus):
        return locus.split(".", 1)[0], "source-numeric-page"
    return locus, "unresolved-physical-page"


def corpus_report(corpus, out, summary_path):
    """Measure each physical OCR reading; never count consensus alternatives twice."""
    out.parent.mkdir(parents=True, exist_ok=True)
    counts, by_source, input_hashes, corpus_pin_lines = Counter(), defaultdict(Counter), {}, []
    flags = []
    stream = (io.TextIOWrapper(gzip.GzipFile(filename="", fileobj=out.open("wb"), mode="wb", mtime=0), encoding="utf-8")
              if out.suffix == ".gz" else out.open("w"))
    with stream:
        for path in sorted(corpus.glob("*.jsonl")):
            groups = defaultdict(lambda: {"parts": [], "loci": []})
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            corpus_pin_lines.append(f"{path.stem}\t{digest}\n")
            for line in raw.decode().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("source") not in {"ocr", "cgpg", "greek_library"}:
                    continue
                page, basis = page_identity(row)
                readings = row.get("ocr_consensus", {}).get("witnesses")
                if readings is None:
                    readings = [{"id": row.get("edition", "unknown"), "text": row["text"]}]
                for witness in readings:
                    key = (page, witness["id"], basis)
                    groups[key]["parts"].append(witness["text"])
                    groups[key]["loci"].append(row["locus"])
                    groups[key]["source"] = row["source"]
            if not groups:
                continue
            input_hashes[path.name] = digest
            for (page, witness, basis), value in sorted(groups.items()):
                result = detect("\n".join(value["parts"]))
                if basis == "unresolved-physical-page":
                    result.update({"flag": False, "applicable": False,
                                   "review_state": "physical-page-mapping-required", "reasons": []})
                record = {"work": path.stem, "page": page, "witness": witness,
                          "page_basis": basis, "source": value["source"], "loci": value["loci"], **result}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                counts["readings"] += 1
                counts["flagged" if result["flag"] else "unflagged" if result["applicable"] else "unassessable"] += 1
                by_source[value["source"]]["readings"] += 1
                by_source[value["source"]]["flagged"] += result["flag"]
                if result["flag"]:
                    flags.append({k: record[k] for k in ("work", "page", "witness", "accented_letter_rate", "breathing_letter_rate", "reasons")})
    summary = {"schema_version": 1, "policy": POLICY, "policy_sha256": hashlib.sha256(dump(POLICY)).hexdigest(),
               "corpus_sha256": hashlib.sha256("".join(sorted(corpus_pin_lines)).encode()).hexdigest(),
               "corpus_pin_policy": "SHA256 over sorted '<slug>\\t<per-work file SHA256>\\n' lines for every corpus JSONL file, including sources outside the detector scope; matches the release corpus pin.",
               "input_corpus_files": input_hashes, "page_readings_sha256": benchmark.sha256(out),
               "counts": dict(counts), "by_source": {name: dict(c) for name, c in sorted(by_source.items())},
               "flagged_pages": flags, "selection_rule": None,
               "scope": "Review candidates from OCR sources, grouped by recoverable physical page and witness. A flag is not proof of damaged text. This report never selects a model, changes text, or admits a correction.",
               "generated_by": "scripts/report_polytonic_loss.py corpus"}
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_bytes(dump(summary))
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p = commands.add_parser("validate")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=DEFAULT_OUT / "manifest.json")
    p.add_argument("--policy", type=Path, default=DEFAULT_OUT / "policy.json")
    p.add_argument("--predictions", type=Path, action="append", required=True)
    p.add_argument("--archive-predictions", type=Path,
                   help="Archive the exact single raw input before validating; refuses replacement")
    p.add_argument("--scan-review", type=Path, required=True)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT / "validation.json")
    p = commands.add_parser("corpus")
    p.add_argument("--corpus", type=Path, default=ROOT / "data/corpus")
    p.add_argument("--out", type=Path, default=ROOT / "data/quality/polytonic-loss-pages.jsonl.gz")
    p.add_argument("--summary", type=Path, default=ROOT / "data/polytonic_loss_report.json")
    args = ap.parse_args()
    if args.command == "prepare":
        result = prepare(args.root, args.out)
        print(json.dumps({"pages": len(result["pages"]), "by_edition": result["edition_counts"]}))
    elif args.command == "validate":
        predictions = args.predictions
        if args.archive_predictions:
            if len(predictions) != 1:
                ap.error("--archive-predictions requires exactly one raw run")
            predictions = [archive_prediction(predictions[0], args.archive_predictions)]
        result = validate_fresh(args.root, args.manifest, args.policy, predictions, args.scan_review)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(dump(result))
        print(json.dumps({run["metadata"]["model"]: run["by_split"] for run in result["runs"]}))
    elif args.command == "corpus":
        print(json.dumps(corpus_report(args.corpus, args.out, args.summary)["counts"]))


if __name__ == "__main__":
    main()
