#!/usr/bin/env python3
"""Collate reviewed mathematical and Dio scan regions into reversible additions.

Run with retained run_scan_ocr.py outputs and the exact input manifest. All raw
predictions, layout decisions, word votes, ties and removed running headers are
archived. --apply writes only new citation destinations; no existing reading is
replaced. Early Dio comparison regions become comparative paratext, and the
first volume VI region is trimmed only at the audited shared paragraph anchor.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
WORKS = {"pappus-mathematics.synagoge", "apollonius-geom.conica", "cassius-dio.historiae-romanae"}
EXTENSION_INDEX = "data/corpus_extension_index.json"
EDITION = "scan-consensus-2026-10-18"
PAPPUS_HEADER = re.compile(r"^\s*ΠΑΠΠΟΥ\s+ΣΥΝΑΓΩΓΗΣ\s+\S+\s*$", re.I)
OVERLAP_ANCHOR = "βουληθεὶς δὲ δὴ τρόπον"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def records(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def jsonl_bytes(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


def vote_group(model):
    match = re.search(r"qwen3[.-](\d+).*?(\d+)b", model.lower())
    return f"qwen3.{match[1]}-{match[2]}b" if match else model


def load_predictions(path, manifest_bytes, manifest, raw=None):
    raw = path.read_bytes() if raw is None else raw
    values = records(raw)
    if not values or set(values[0]) != {"_meta"}:
        raise ValueError("OCR output is missing its retained runtime metadata")
    metadata = values[0]["_meta"]
    if metadata.get("manifest_sha256") != sha(manifest_bytes):
        raise ValueError("OCR predictions belong to a different manifest")
    if metadata.get("prompt") != manifest["prompt"]:
        raise ValueError("OCR predictions used a different transcription prompt")
    if not metadata.get("model") or not metadata.get("revision"):
        raise ValueError("OCR checkpoint and revision must be pinned")
    selected = {p["id"]: p for p in manifest["pages"]}
    result = {}
    for row in values[1:]:
        identifier = row["id"]
        if identifier not in selected or identifier in result:
            raise ValueError("Repeated or unknown OCR region identity")
        page = selected[identifier]
        suffix = page.get("prompt_suffix", manifest["sources"][page["source"]].get("prompt_suffix", ""))
        prompt = manifest["prompt"] + (" " + suffix if suffix else "")
        if row.get("prompt_sha256") != sha(prompt.encode()):
            raise ValueError("OCR region prompt differs from the reviewed request")
        if (row.get("source"), row.get("scan_page"), row.get("region")) != (
                page["source"], page["scan_page"], page.get("region", [0, 0, 1, 1])):
            raise ValueError("OCR prediction geometry differs from the reviewed region")
        if row.get("error") or row.get("finish_reason") != "stop" or not row.get("raw_prediction", "").strip():
            raise ValueError("Failed, empty or truncated OCR region cannot be admitted")
        result[identifier] = {"id": metadata["model"] + "@" + metadata["revision"],
            "model": metadata["model"], "revision": metadata["revision"],
            "vote_group": vote_group(metadata["model"]), "text": row["raw_prediction"],
            "artifact_sha256": sha(encoded({"metadata": metadata, "prediction": row})),
            "image_sha256": row["image_sha256"]}
    return result, raw


def clean_running_headers(text, work):
    """Remove only the checked short running heading, retaining real titles."""
    kept, removed = [], []
    offset = 0
    for line in text.splitlines(keepends=True):
        if work == "pappus-mathematics.synagoge" and PAPPUS_HEADER.fullmatch(line.strip()):
            removed.append({"offset": offset, "original_text": line, "corrected_text": "",
                "evidence": "The short ΠΑΠΠΟΥ ΣΥΝΑΓΩΓΗΣ heading is the edition's repeated running header. The full book title includes ΑΛΕΞΑΝΔΡΕΩΣ and is preserved."})
        else:
            kept.append(line)
        offset += len(line)
    return "".join(kept), removed


def trim_shared_prefix(text):
    """Locate the existing paragraph's final words without choosing a reading."""
    normalized = unicodedata.normalize("NFC", text)
    # Keep offsets in the retained prediction; the consensus tokenizer may join
    # line-end hyphens and intentionally does not expose source character spans.
    spans = []
    start = None
    for index, char in enumerate(normalized + " "):
        if unicodedata.category(char).startswith(("L", "M")) or char in "'’ʼ᾽":
            if start is None:
                start = index
        elif start is not None:
            spans.append((start, index))
            start = None
    def key(word):
        return "".join(char for char in unicodedata.normalize("NFD", word.casefold())
                       if not unicodedata.combining(char)).replace("ς", "σ").rstrip("'’ʼ᾽")
    words = [key(normalized[start:end]) for start, end in spans]
    anchor = [key(word) for word in OVERLAP_ANCHOR.split()]
    locations = [i for i in range(len(words) - len(anchor) + 1)
                 if words[i:i + len(anchor)] == anchor]
    if len(locations) != 1:
        raise ValueError("The shared Dio prefix does not have a unique checked anchor")
    end = spans[locations[0] + len(anchor) - 1][1]
    return normalized[end:].lstrip(), {"normalization": "NFC", "end_offset": end,
        "original_text": normalized[:end], "corrected_text": "",
        "evidence": "Cary volume VI printed page 402 (PDF206) overlaps the already served text through 55.9.4, whose last words are " + OVERLAP_ANCHOR + ". Remove only that shared prefix and retain every original prediction in the audit."}


def locus(page):
    if page["work"] == "pappus-mathematics.synagoge":
        return f"{page['book']}.hultsch-p{page['printed_page']:04d}"
    if page["work"] == "apollonius-geom.conica":
        return f"{page['book']}.heiberg-p{page['printed_page']:04d}"
    suffix = "-" + page["panel_role"] if page.get("panel_role") else ""
    return f"cary-v{page['source_volume']}-p{page['printed_page']:04d}{suffix}"


def collate_overlaps(manifest, inputs, root):
    """Retain a three-way shared-prefix comparison without changing old rows."""
    from ocr_consensus import merge_witnesses
    comparisons = {}
    for page in manifest["pages"]:
        if not page.get("overlap"):
            continue
        work = page["work"]
        rows = records((Path(root) / f"data/corpus/{work}.jsonl").read_bytes())
        selected = [row for row in rows if row["locus"] in {"55.9.2", "55.9.3", "55.9.4"}]
        if [row["locus"] for row in selected] != ["55.9.2", "55.9.3", "55.9.4"]:
            raise ValueError("The checked Dio overlap passages are missing or reordered")
        baseline = " ".join(row["text"] for row in selected)
        if not baseline.endswith(OVERLAP_ANCHOR):
            raise ValueError("The existing Dio ending no longer matches the checked overlap")
        witnesses = [{"id": "perseus-cary-existing-55.9.2-4", "vote_group": "perseus-cary",
            "text": baseline, "artifact_sha256": sha(encoded(selected)),
            "source_passages": [row["locus"] for row in selected]}]
        decisions = []
        for source in inputs:
            value = source.get(page["id"])
            if value is None:
                raise ValueError("A fresh Dio overlap witness is missing")
            continuation, decision = trim_shared_prefix(value["text"])
            decisions.append({"witness": value["id"], **decision})
            witnesses.append({**value, "text": decision["original_text"], "original_text": value["text"]})
        comparisons[page["id"]] = {"page": page, "existing_passages": selected,
            "prefix_decisions": decisions, "consensus": merge_witnesses(witnesses),
            "policy": "Comparison evidence only. Preserve existing 55.9.2–55.9.4 readings and references; count only the separately trimmed missing continuation as new text.",
            "coverage_note": "Existing 55.9.2 begins on the previous printed page. Fresh page witnesses abstain before their observed span rather than voting to remove that existing prefix."}
    return comparisons


def collate(manifest, inputs, allow_partial=False, network_path=None, digital=None):
    from ocr_consensus import merge_witnesses, compact_corpus_consensus
    network_path = network_path or "data/corpus_changes/scan-coverage-preview/word-networks.json.gz"
    digital = digital or {"sources": {}, "pages": {}, "originals": {}}
    primary, paratext, audits, networks = {}, [], [], {}
    for page in manifest["pages"]:
        if page["work"] not in WORKS:
            raise ValueError("This importer accepts only the three reviewed coverage works")
        values = [source.get(page["id"]) for source in inputs]
        if any(value is None for value in values):
            if allow_partial:
                continue
            raise ValueError(f"An OCR witness is missing region {page['id']}")
        if len({v["image_sha256"] for v in values}) != 1:
            raise ValueError("Independent OCR witnesses do not describe the same image")
        witnesses, decisions = [], []
        for value in values:
            cleaned, removed = clean_running_headers(value["text"], page["work"])
            decisions.extend({"witness": value["id"], **edit} for edit in removed)
            if page.get("overlap"):
                cleaned, edit = trim_shared_prefix(cleaned)
                decisions.append({"witness": value["id"], **edit})
            witnesses.append(dict(value, text=cleaned, original_text=value["text"]))
        component = None
        comparison = digital["pages"].get((page.get("source_volume"), page["scan_page"]))
        if comparison is not None:
            from bound_comparison_witness import bound_comparison_witness
            bounded, decision = bound_comparison_witness(witnesses, comparison)
            decisions.append(decision)
            if bounded is not None:
                witnesses.append(bounded)
                component = digital["sources"][comparison["source_id"]]
        merged = merge_witnesses(witnesses)
        if not merged["text"].strip():
            raise ValueError("A reviewed Greek region has no surviving reading words")
        key = page["id"]
        source = manifest["sources"][page["source"]]
        from scan_title_reviews import reviewed_title
        merged, raw_review, review = reviewed_title(merged, page, source, witnesses, network_path)
        if raw_review is not None:
            networks[raw_review[0]] = raw_review[1]
            decisions.append(review)
        networks[key] = merged
        compact = compact_corpus_consensus(merged, {"path": network_path, "key": key})
        row = {"urn": page["work"], "edition": EDITION, "locus": locus(page),
            "source": "ocr", "license": "PD", "language": "grc",
            **compact, "scan_region_id": key,
            "source_scan": {"url": source["url"], "sha256": source["sha256"],
                "scan_page": page["scan_page"], "region": page["region"]},
            "printed_page": page["printed_page"],
            "transmission": page.get("transmission", "direct-text")}
        if page.get("text_role"):
            row["text_role"] = page["text_role"]
        if review is not None:
            row["corrections"] = ["manual"]
            row["correction_sources"] = [review["review_id"]]
        if component is not None:
            row["license"] = "CC-BY-SA-4.0"
            row["component_attribution"] = [component]
        if page.get("attribution_heading"):
            row["attribution_heading"] = page["attribution_heading"]
        # The Greek word-voting layer excludes Latin credits and numeric book
        # references. Retain these source lines separately, with every witness's
        # spelling, rather than dropping transmission evidence from the row.
        if page["work"] == "cassius-dio.historiae-romanae":
            reference_lines = {value["id"]: [{"line_number": number, "text": line}
                for number, line in enumerate(value["text"].splitlines(), 1)
                if re.search(r"[A-Za-z0-9]", line)] for value in values}
            row["reference_line_witnesses"] = {key: lines for key, lines in reference_lines.items() if lines}
        if page.get("overlap"):
            row["continues"] = "55.9.4"
            row["transmission"] = "excerpt-supplement-after-direct-text-lacuna"
        if page.get("source_volume") == 6 and page["scan_page"] == 207:
            row["transmission"] = "excerpt-supplement-after-direct-text-lacuna"
        if page.get("source_volume") == 6 and page["scan_page"] in {206, 207, 208}:
            row["transmission_evidence"] = {
                "source": "Cary volume VI, printed page 402, footnote 4",
                "scope": "The lost direct-text folios extend from after τρόπον at 55.9.4 through the beginning of 55.10.2. Printed 402–404 continue through epitomes/excerpts; printed 406 has Xiphilinus and index supplements above the return of direct text at 55.10.2.",
                "review": "Manual inspection of PDF pages 206–208 in the hash-pinned volume VI scan."}
        if page.get("admission") == "comparative-paratext":
            row["kind"] = "comparative-quotation"
            paratext.append(row)
        elif page.get("admission", "candidate-reading-pending-collation") == "candidate-reading-pending-collation":
            primary.setdefault(page["work"], []).append(row)
        else:
            raise ValueError("The reviewed region has no approved routing destination")
        audits.append({"region_id": key, "work": row["urn"], "locus": row["locus"],
            "destination": "paratext" if row.get("kind") else "primary",
            "original_texts": {v["id"]: v["text"] for v in values},
            "corrected_text": row["text"], "analysis_text": row["analysis_text"],
            "decisions": decisions, "source": row["source_scan"],
            "evidence": "Independent retained OCR witnesses collated by scripts/ocr_consensus.py; all readings, support and unresolved ties remain in the word network."})
    return primary, paratext, audits, networks


def apply(root, manifest_bytes, raw_inputs, primary, paratext, audits, networks, run_id, digital=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,70}", run_id):
        raise ValueError("Unsafe scan admission run identifier")
    archive = root / "data/corpus_changes" / run_id
    digital = digital or {"sources": {}, "pages": {}, "originals": {}}
    if archive.exists():
        raise ValueError("This admission audit already exists; do not replace its evidence")
    from ocr_consensus import compact_corpus_consensus
    network_path = str((archive / "word-networks.json.gz").relative_to(root))
    for row in [value for rows in primary.values() for value in rows] + paratext:
        key = row["scan_region_id"]
        if "raw_ocr_network" in networks[key]["ocr_consensus"]:
            networks[key]["ocr_consensus"]["raw_ocr_network"]["path"] = network_path
        row.update(compact_corpus_consensus(networks[key], {"path": network_path, "key": key}))
    paths = [EXTENSION_INDEX, "data/corpus_editions.json"]
    paths += [f"data/corpus/{work}.jsonl" for work in primary]
    paths += [f"data/corpus_extensions/{work}.jsonl" for work in primary]
    paratext_path = f"data/paratext/{run_id}.jsonl"
    if paratext:
        paths.append(paratext_path)
    before = {path: (root / path).read_text() if (root / path).exists() else None for path in paths}
    extensions = json.loads(before[EXTENSION_INDEX]) if before[EXTENSION_INDEX] else {"schema_version": 1, "works": {}}
    editions = json.loads(before["data/corpus_editions.json"])
    outputs, addition_hashes = {}, {}
    for work, rows in primary.items():
        old = records(before[f"data/corpus/{work}.jsonl"].encode())
        seen = {row["locus"] for row in old}
        if len({row["locus"] for row in rows}) != len(rows) or any(row["locus"] in seen for row in rows):
            raise ValueError("Refusing to replace an existing passage with scan coverage")
        extension_path = f"data/corpus_extensions/{work}.jsonl"
        from scan_coverage_extensions import combine_rows, reading_digest
        previous = extensions["works"].get(work)
        previous_rows = records(before[extension_path].encode()) if before[extension_path] is not None else []
        if previous_rows:
            if not previous or sha(before[extension_path].encode()) != previous["sha256"]:
                raise ValueError("Existing scan extension lacks its unchanged audit index")
            current_rows = {row["locus"]: row for row in old}
            if any(current_rows.get(row["locus"]) != row for row in previous_rows):
                raise ValueError("An existing admitted scan reading changed")
        previous_loci = {row["locus"] for row in previous_rows}
        base = [row for row in old if row["locus"] not in previous_loci]
        if previous and reading_digest(base) != previous["base_readings_sha256"]:
            raise ValueError("The underlying edition changed before extension consolidation")
        rows = combine_rows(work, [], rows)
        combined = combine_rows(work, previous_rows, rows)
        addition_hashes[work] = sha(jsonl_bytes(rows))
        outputs[extension_path] = jsonl_bytes(combined)
        outputs[f"data/corpus/{work}.jsonl"] = jsonl_bytes(combine_rows(work, old, rows))
        audit_reference = str(archive.relative_to(root) / "changes.json")
        previous_audits = previous.get("audits", [previous["audit"]]) if previous else []
        extensions["works"][work] = {"path": extension_path, "sha256": sha(outputs[extension_path]),
            "audit": audit_reference, "audits": previous_audits + [audit_reference], "edition": EDITION,
            "base_readings_sha256": reading_digest(base)}
        components = {component["id"]: component for row in combined for component in row.get("component_attribution", [])}
        if components:
            extensions["works"][work]["digital_components"] = [components[key] for key in sorted(components)]
        from build_public_corpus import _GK
        editions[work]["n_passages"] = len(old) + len(rows)
        editions[work]["n_tokens"] = sum(len(_GK.findall(r.get("analysis_text", r["text"]))) for r in old + rows)
        editions[work]["scan_extensions"] = [EDITION]
        editions[work]["scan_extension_licenses"] = sorted({row["license"] for row in combined})
    outputs[EXTENSION_INDEX] = encoded(extensions)
    outputs["data/corpus_editions.json"] = encoded(editions)
    if paratext:
        if before[paratext_path] is not None:
            raise ValueError("Refusing to replace an existing comparison dataset")
        outputs[paratext_path] = ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in paratext)).encode()
    archive.mkdir(parents=True)
    before_bytes = gzip.compress(encoded(before), mtime=0)
    (archive / "before.json.gz").write_bytes(before_bytes)
    (archive / "manifest.json").write_bytes(manifest_bytes)
    for index, raw in enumerate(raw_inputs, 1):
        (archive / f"witness-{index}.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    for identifier, raw in digital["originals"].items():
        (archive / f"digital-{identifier}.json.gz").write_bytes(gzip.compress(raw, mtime=0))
    overlap = collate_overlaps(json.loads(manifest_bytes),
        [load_predictions(None, manifest_bytes, json.loads(manifest_bytes), raw)[0] for raw in raw_inputs], root)
    overlap_bytes = gzip.compress(encoded(overlap), mtime=0)
    (archive / "overlap-comparisons.json.gz").write_bytes(overlap_bytes)
    network_bytes = gzip.compress(encoded(networks), mtime=0)
    (archive / "word-networks.json.gz").write_bytes(network_bytes)
    for path, raw in outputs.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (archive / "changes.json").write_bytes(encoded({"schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(), "generator": "scripts/ingest_scan_coverage.py",
        "manifest_sha256": sha(manifest_bytes), "witness_sha256": [sha(raw) for raw in raw_inputs],
        "word_networks_sha256": sha(network_bytes),
        "before_archive_sha256": sha(before_bytes),
        "overlap_comparisons": {"path": str((archive / "overlap-comparisons.json.gz").relative_to(root)),
            "sha256": sha(overlap_bytes), "regions": len(overlap)},
        "digital_sources": digital["sources"],
        "digital_comparison_counts": dict(Counter(decision["status"] for change in audits
            for decision in change["decisions"] if decision.get("generator") == "scripts/bound_comparison_witness.py")),
        "consensus_generator_sha256": sha(Path(__import__("ocr_consensus").__file__).read_bytes()),
        "changes": audits, "outputs": {path: sha(raw) for path, raw in outputs.items()},
        "admitted_extensions_sha256": addition_hashes,
        "reversal": "Use --undo with this audit directory. Every previous file byte and original OCR prediction is archived; the word networks retain all tied alternatives."}))


def undo(directory, root):
    audit = json.loads((directory / "changes.json").read_text())
    for path, expected in audit["outputs"].items():
        if not (root / path).exists() or sha((root / path).read_bytes()) != expected:
            raise ValueError("Output changed after scan admission; refusing to overwrite: " + path)
    before = json.loads(gzip.decompress((directory / "before.json.gz").read_bytes()))
    for path, original in before.items():
        if original is None:
            (root / path).unlink(missing_ok=True)
        else:
            (root / path).write_text(original)


def verify(directory, root):
    directory, root = Path(directory).resolve(), Path(root).resolve()
    verify_integrity(directory, root)
    audit = json.loads((directory / "changes.json").read_text())
    raw_manifest = (directory / "manifest.json").read_bytes()
    if sha(raw_manifest) != audit["manifest_sha256"]:
        raise ValueError("Archived scan selection changed")
    manifest = json.loads(raw_manifest)
    loaded = []
    for index, expected in enumerate(audit["witness_sha256"], 1):
        raw = gzip.decompress((directory / f"witness-{index}.jsonl.gz").read_bytes())
        if sha(raw) != expected:
            raise ValueError("Archived raw OCR witness changed")
        loaded.append(load_predictions(None, raw_manifest, manifest, raw)[0])
    digital = archived_digital_sources(directory, audit)
    primary, paratext, changes, networks = collate(manifest, loaded,
        network_path=str((directory / "word-networks.json.gz").relative_to(root)), digital=digital)
    if changes != audit["changes"] or networks != json.loads(gzip.decompress((directory / "word-networks.json.gz").read_bytes())):
        raise ValueError("Scan consensus differs from its retained original witnesses")
    overlap = collate_overlaps(manifest, loaded, root)
    if overlap != json.loads(gzip.decompress((directory / "overlap-comparisons.json.gz").read_bytes())):
        raise ValueError("Dio overlap comparison differs from its original readings")
    from scan_coverage_extensions import combine_rows
    for work, expected in primary.items():
        expected = combine_rows(work, [], expected)
        extension = root / f"data/corpus_extensions/{work}.jsonl"
        identifiers = {row["scan_region_id"] for row in expected}
        selected = [row for row in records(extension.read_bytes()) if row["scan_region_id"] in identifiers]
        if selected != expected:
            raise ValueError("Scan extension differs from reproducible consensus")
        current = records((root / f"data/corpus/{work}.jsonl").read_bytes())
        if any(row not in current for row in expected):
            raise ValueError("An admitted scan reading is missing or changed")
    if paratext and records((root / f"data/paratext/{directory.name}.jsonl").read_bytes()) != paratext:
        raise ValueError("Comparative source panels differ from their OCR evidence")


def verify_integrity(directory, root):
    """Check complete coverage and immutable evidence without repeating voting.

    Use verify/--check once after admission to recompute all word networks. This
    check is suitable for repeatedly building release metadata and limitations.
    """
    directory, root = Path(directory), Path(root)
    audit = json.loads((directory / "changes.json").read_text())
    archived_digital_sources(directory, audit)
    manifest_bytes = (directory / "manifest.json").read_bytes()
    if sha(manifest_bytes) != audit["manifest_sha256"]:
        raise ValueError("Archived scan selection changed")
    if sha((directory / "word-networks.json.gz").read_bytes()) != audit["word_networks_sha256"]:
        raise ValueError("Archived word network changed")
    if sha((root / audit["overlap_comparisons"]["path"]).read_bytes()) != audit["overlap_comparisons"]["sha256"]:
        raise ValueError("Archived overlap comparison changed")
    before_bytes = (directory / "before.json.gz").read_bytes()
    if sha(before_bytes) != audit["before_archive_sha256"]:
        raise ValueError("Archived original corpus bytes changed")
    before = json.loads(gzip.decompress(before_bytes))
    manifest = json.loads(manifest_bytes)
    pages = {page["id"]: page for page in manifest["pages"]}
    groups, images = set(), {}
    for index, expected in enumerate(audit["witness_sha256"], 1):
        raw = gzip.decompress((directory / f"witness-{index}.jsonl.gz").read_bytes())
        if sha(raw) != expected:
            raise ValueError("Archived raw OCR witness changed")
        source, _ = load_predictions(None, manifest_bytes, manifest, raw)
        if set(source) != set(pages):
            raise ValueError("An admitted OCR witness lacks reviewed scan regions")
        groups.update(value["vote_group"] for value in source.values())
        for identity, value in source.items():
            previous = images.setdefault(identity, value["image_sha256"])
            if previous != value["image_sha256"]:
                raise ValueError("OCR witnesses describe different scan images")
    if len(groups) < 2:
        raise ValueError("Two independent OCR model families are required")
    if {change["region_id"] for change in audit["changes"]} != set(pages):
        raise ValueError("Scan admission audit lacks reviewed region decisions")
    works = {page["work"] for page in pages.values()
             if page.get("admission") != "comparative-paratext"}
    for work in works:
        relative = f"data/corpus_extensions/{work}.jsonl"
        raw = (root / relative).read_bytes()
        active = json.loads((root / EXTENSION_INDEX).read_text())["works"][work]
        if sha(raw) != active["sha256"]:
            raise ValueError("Scan extension differs from its active audit index")
        all_extensions = records(raw)
        expected = {page["id"] for page in pages.values() if page["work"] == work
                    and page.get("admission") != "comparative-paratext"}
        additions = [row for row in all_extensions if row["scan_region_id"] in expected]
        if sha(jsonl_bytes(additions)) != audit["admitted_extensions_sha256"][work]:
            raise ValueError("An admission's scan extension readings changed")
        if {row["scan_region_id"] for row in additions} != expected or len(additions) != len(expected):
            raise ValueError("Scan extension does not cover every reviewed primary region")
        current_rows = records((root / f"data/corpus/{work}.jsonl").read_bytes())
        current = {row["locus"]: row for row in current_rows}
        if any(current.get(row["locus"]) != row for row in additions):
            raise ValueError("An admitted scan reading is missing or changed")
        from scan_coverage_extensions import reading_digest
        new_loci = {row["locus"] for row in all_extensions}
        base = [row for row in current_rows if row["locus"] not in new_loci]
        original = records(before[f"data/corpus/{work}.jsonl"].encode())
        old_extensions = records(before[relative].encode()) if before[relative] is not None else []
        old_loci = {row["locus"] for row in old_extensions}
        original = [row for row in original if row["locus"] not in old_loci]
        if reading_digest(base) != reading_digest(original):
            raise ValueError("Historical source readings changed after scan admission")
    comparisons = [page for page in pages.values() if page.get("admission") == "comparative-paratext"]
    if comparisons:
        relative = f"data/paratext/{directory.name}.jsonl"
        raw = (root / relative).read_bytes()
        if sha(raw) != audit["outputs"][relative] or len(records(raw)) != len(comparisons):
            raise ValueError("Comparative source panels differ from their admission")
    return audit


def archived_digital_sources(directory, audit):
    from dio_comparison_witnesses import load
    identifiers = sorted(audit.get("digital_sources", {}))
    result = load([Path(directory) / f"digital-{identifier}.json.gz" for identifier in identifiers])
    if result["sources"] != audit.get("digital_sources", {}):
        raise ValueError("Archived digital source rights or identity changed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--witness", type=Path, action="append", default=[])
    parser.add_argument("--digital-witness", type=Path, action="append", default=[])
    parser.add_argument("--run-id")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--undo", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    if args.undo:
        undo(args.undo, ROOT)
        return
    if args.check:
        verify(args.check, ROOT)
        print("Every scan addition and word vote matches the retained witnesses.")
        return
    if not args.manifest or not args.witness or (args.apply and (not args.run_id or args.allow_partial)):
        parser.error("Provide a manifest and witnesses; --apply requires a run ID and complete output")
    raw_manifest = args.manifest.read_bytes()
    manifest = json.loads(raw_manifest)
    loaded = [load_predictions(path, raw_manifest, manifest) for path in args.witness]
    from dio_comparison_witnesses import load as load_digital, PINS
    digital = load_digital(args.digital_witness)
    if args.apply and len({value["vote_group"] for source, _ in loaded
                           for value in source.values()}) < 2:
        parser.error("--apply requires at least two independent OCR model families")
    if args.apply and any(page["work"] == "cassius-dio.historiae-romanae" for page in manifest["pages"]) and set(digital["sources"]) != set(PINS):
        parser.error("Dio admission requires all three reviewed Source Library VII–IX comparison exports")
    result = collate(manifest, [item[0] for item in loaded], args.allow_partial, digital=digital)
    if args.apply:
        apply(ROOT, raw_manifest, [item[1] for item in loaded], *result, args.run_id, digital=digital)
    print(json.dumps({"primary_passages": {work: len(rows) for work, rows in result[0].items()},
                      "comparative_paratext": len(result[1]), "applied": args.apply}))


if __name__ == "__main__":
    main()
