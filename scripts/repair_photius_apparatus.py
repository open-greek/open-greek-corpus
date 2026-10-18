#!/usr/bin/env python3
"""Separate scan-reviewed Photius editorial spans with exact reversible replay.

Historical admissions remain immutable. Their checks may restore this one
verified later layer in memory; independent corpus edits still fail closed.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

from repair_photius_index import ROOT, CORPUS, ALIASES, SLUG, PAGE, generate as split_index, input_bytes

REVIEW = Path("data/ingest_reviews/photius-bekker-apparatus.json")
PARATEXT = Path("data/paratext/photius-bekker-apparatus.jsonl")
ARCHIVE = Path("data/corpus_changes/photius-bekker-apparatus")
AUDIT = ARCHIVE / "changes.json"
SCHEMA = "scan-reviewed-editorial-spans-v1"
SOURCE_SHA = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
SOURCE_URL = "https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf"
CLASSES = {"critical-apparatus", "printer_signature", "ocr_markup", "running_header"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def _bbox(value):
    return (isinstance(value, list) and len(value) == 4
            and all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in value)
            and 0 <= value[0] < value[2] <= 1 and 0 <= value[1] < value[3] <= 1)


def _historical(root):
    raw = split_index(input_bytes(root))[0]
    rows = [json.loads(line) for line in raw.splitlines()]
    return raw, {row["locus"]: row for row in rows}


def validate_review(raw, historical_raw, historical):
    review = json.loads(raw)
    if (review.get("schema_version") != 1 or review.get("work") != SLUG
            or review.get("kind") != "source-reviewed-apparatus-exclusions"
            or review.get("source") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or review.get("historical_body_sha256") != sha(historical_raw) or not review.get("reviewed_at")):
        raise ValueError("Apparatus review differs from its pinned historical edition")
    pages = review.get("pages", [])
    expected_pages = {int(PAGE.fullmatch(locus)[1]) for locus in historical}
    if len(pages) != len(expected_pages) or {p.get("scan_page") for p in pages} != expected_pages:
        raise ValueError("Every historical physical page needs a source review, including pages without exclusions")
    decisions = {}
    for page in pages:
        number = page["scan_page"]
        if (page.get("source_pdf_sha256") != SOURCE_SHA or page.get("source_url") != SOURCE_URL
                or page.get("printed_page") != number + 265 or not page.get("reviewed_at") or not page.get("evidence")):
            raise ValueError("Historical page lacks its exact physical source and completed review")
        rows = page.get("rows", [])
        expected = {locus for locus in historical if int(PAGE.fullmatch(locus)[1]) == number}
        if len(rows) != len(expected) or {r.get("locus") for r in rows} != expected:
            raise ValueError("Every historical row on a reviewed page must be identified exactly once")
        for item in rows:
            locus = item["locus"]
            old = historical[locus]
            text = old["text"]
            if item.get("full_row_text") != text or item.get("row_sha256") != row_sha(old):
                raise ValueError("Apparatus review differs from the full original row or its exact text")
            exclusions, previous = item.get("exclusions"), 0
            if not isinstance(exclusions, list):
                raise ValueError("Rows without editorial spans must explicitly declare exclusions: []")
            for span in exclusions:
                start, end = span.get("start"), span.get("end")
                if (not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool)
                        or not previous <= start < end <= len(text) or span.get("original_text") != text[start:end]
                        or span.get("classification") not in CLASSES or not _bbox(span.get("source_region"))
                        or not (span.get("evidence") or page["evidence"])):
                    raise ValueError("Editorial exclusion lacks an exact nonoverlapping source-reviewed span")
                previous = end
            decisions[locus] = (page, item)
    # This physically reviewed ten-row block is the issue's confirmed lower
    # bound; a complete authority cannot silently relabel it as authorial body.
    for locus, (_, item) in decisions.items():
        match = PAGE.fullmatch(locus)
        if int(match[1]) == 69 and 40 <= int(match[2]) <= 49:
            retained = retain_spans(item["full_row_text"], item["exclusions"])
            if any(s["text"].strip() for s in retained) or not any(
                    s["classification"] == "critical-apparatus" for s in item["exclusions"]):
                raise ValueError("The confirmed apparatus lower bound must remain classified by its source review")
    return review, decisions


def retain_spans(text, exclusions):
    retained, position = [], 0
    for span in exclusions:
        if position < span["start"]:
            retained.append({"start": position, "end": span["start"], "text": text[position:span["start"]]})
        position = span["end"]
    if position < len(text):
        retained.append({"start": position, "end": len(text), "text": text[position:]})
    return retained


def _reading(retained):
    # Separate source spans remain separate adjacency observations. A newline
    # prevents the removal of intervening notes from manufacturing a new word.
    return "\n".join(span["text"] for span in retained)


def plan(before, aliases_before, review_raw, historical_raw, historical):
    review, decisions = validate_review(review_raw, historical_raw, historical)
    rows = [json.loads(line) for line in before.splitlines()]
    by_locus = {row["locus"]: row for row in rows}
    if (len(by_locus) != len(rows) or any(by_locus.get(locus) != row for locus, row in historical.items())
            or {locus for locus in by_locus if PAGE.fullmatch(locus)} != set(historical)):
        raise ValueError("The apparatus layer requires every unchanged historical body row")
    aliases = copy.deepcopy(json.loads(aliases_before))
    own_aliases = aliases.setdefault("aliases", {}).setdefault(SLUG, {})
    review_pin = {"path": (ARCHIVE / "source-review.json").as_posix(), "sha256": sha(review_raw)}
    primary, notes, changes, moved, mixed = [], [], [], 0, 0
    classifications = {}
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        locus = old["locus"]
        decision = decisions.get(locus)
        if decision is None or not decision[1]["exclusions"]:
            primary.append(line)
            continue
        page, item = decision
        excluded = item["exclusions"]
        retained = retain_spans(old["text"], excluded)
        body_text = _reading(retained)
        target = {"path": PARATEXT.as_posix(), "locus": locus}
        source = {"url": SOURCE_URL, "sha256": SOURCE_SHA, "scan_page": page["scan_page"], "printed_page": page["printed_page"]}
        note = {**old, "slug": SLUG, "language": "grc", "class": "edition_editorial_matter",
                "text": "\n".join(span["original_text"] for span in excluded),
                "full_row_text": old["text"], "body_spans": retained, "editorial_spans": excluded,
                "classifications": sorted({span["classification"] for span in excluded}),
                "physical_refs": source, "source_review": review_pin,
                "why_not_served": "Source-reviewed editorial material and OCR markup are retained separately from authorial reading and lexical counts."}
        notes.append(note)
        if body_text.strip():
            updated = {**old, "text": body_text, "analysis_text": body_text,
                "editorial_layer": {"schema": SCHEMA, "original_text": old["text"], "body_spans": retained,
                    "excluded_spans": excluded, "paratext": target, "source_review": review_pin, "physical_refs": source}}
            primary.append(jsonl([updated]))
            mixed += 1
            after = updated
        else:
            note["text"] = old["text"]  # Whole editorial rows retain their exact historical reading.
            if locus in own_aliases:
                raise ValueError("An editorial passage already has an independent alias")
            own_aliases[locus] = target
            moved += 1
            after = None
        for name in note["classifications"]:
            classifications[name] = classifications.get(name, 0) + 1
        changes.append({"locus": locus, "original_text": old["text"], "corrected_text": body_text if after else "",
                        "original_row_sha256": row_sha(old), "corrected_row_sha256": row_sha(after) if after else None,
                        "original_row": old, "corrected_row": after, "paratext": target,
                        "exclusions": excluded, "source": source, "source_review": review_pin,
                        "evidence": page["evidence"], "reviewed_at": page["reviewed_at"]})
    outputs = {CORPUS: b"".join(primary), PARATEXT: jsonl(notes), ALIASES: encode(aliases)}
    audit = {"schema_version": 1, "operation": "separate-source-reviewed-photius-editorial-spans", "work": SLUG,
             "reviewed_at": review["reviewed_at"], "source_review": review_pin,
             "source": review["source"], "historical_body_sha256": sha(historical_raw),
             "inputs": {CORPUS.as_posix(): sha(before), ALIASES.as_posix(): sha(aliases_before)},
             "outputs": {path.as_posix(): sha(raw) for path, raw in outputs.items()},
             "counts": {"reviewed_pages": len(review["pages"]), "reviewed_historical_rows": len(historical),
                 "changed_rows": len(changes), "moved_rows": moved, "mixed_rows": mixed,
                 "paratext_rows": len(notes), "primary_rows_before": len(rows), "primary_rows_after": len(rows) - moved,
                 "rows_by_classification": classifications,
                 "excluded_spans": sum(len(change["exclusions"]) for change in changes),
                 "excluded_characters": sum(span["end"] - span["start"] for change in changes for span in change["exclusions"])},
             "changes": changes,
             "reversal": "Run scripts/repair_photius_apparatus.py --undo before undoing the earlier coverage or index admissions.",
             "generated_by": "scripts/repair_photius_apparatus.py"}
    return outputs, audit


def _preimages(root):
    archive = root / ARCHIVE
    if (archive / "before-corpus.jsonl.gz").exists():
        return (gzip.decompress((archive / "before-corpus.jsonl.gz").read_bytes()),
                gzip.decompress((archive / "before-aliases.json.gz").read_bytes()))
    return (root / CORPUS).read_bytes(), (root / ALIASES).read_bytes()


def build(root=ROOT):
    root = Path(root)
    before, aliases_before = _preimages(root)
    historical_raw, historical = _historical(root)
    review_raw = (root / REVIEW).read_bytes()
    outputs, audit = plan(before, aliases_before, review_raw, historical_raw, historical)
    artifacts = {**outputs, AUDIT: encode(audit), ARCHIVE / "source-review.json": review_raw,
                 ARCHIVE / "before-corpus.jsonl.gz": gzip.compress(before, mtime=0),
                 ARCHIVE / "before-aliases.json.gz": gzip.compress(aliases_before, mtime=0)}
    return artifacts, audit


def _validated_archive(root, require_current_review=True):
    root = Path(root)
    audit_raw = (root / AUDIT).read_bytes()
    audit = json.loads(audit_raw)
    before, aliases_before = _preimages(root)
    if (sha(before) != audit["inputs"][CORPUS.as_posix()]
            or sha(aliases_before) != audit["inputs"][ALIASES.as_posix()]):
        raise ValueError("Apparatus preimages differ from their frozen audit")
    review_raw = (root / ARCHIVE / "source-review.json").read_bytes()
    if sha(review_raw) != audit["source_review"]["sha256"]:
        raise ValueError("Archived apparatus source review changed")
    if require_current_review and (root / REVIEW).read_bytes() != review_raw:
        raise ValueError("Published apparatus authority changed or was invalidated")
    historical_raw, historical = _historical(root)
    outputs, reproduced = plan(before, aliases_before, review_raw, historical_raw, historical)
    if encode(reproduced) != audit_raw:
        raise ValueError("Apparatus audit does not reproduce from its exact preimages and source review")
    return before, aliases_before, outputs, audit


def check(root=ROOT):
    root = Path(root)
    _, _, outputs, audit = _validated_archive(root)
    if any(not (root / path).exists() or (root / path).read_bytes() != raw for path, raw in outputs.items()):
        raise ValueError("A source-reviewed apparatus output changed independently")
    return audit


def restore_legacy_bytes(raw, root=ROOT):
    """Read-only unapply of this exact layer for earlier immutable admissions."""
    root = Path(root)
    if not (root / AUDIT).exists():
        return raw
    audit = json.loads((root / AUDIT).read_bytes())
    if sha(raw) == audit["inputs"][CORPUS.as_posix()]:
        return raw  # The later layer has been explicitly unapplied.
    before, _, outputs, _ = _validated_archive(root)
    if raw != outputs[CORPUS]:
        raise ValueError("Photius changed outside the exact authorized apparatus layer")
    if any((root / path).read_bytes() != value for path, value in outputs.items() if path != CORPUS):
        raise ValueError("Apparatus paratext or historical aliases changed independently")
    return before


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        return None
    audit = json.loads((root / AUDIT).read_bytes())
    if sha((root / CORPUS).read_bytes()) == audit["inputs"][CORPUS.as_posix()]:
        return None
    audit = check(root)
    return {"audit": {"path": AUDIT.as_posix(), "sha256": sha((root / AUDIT).read_bytes())},
            "source_review": audit["source_review"],
            "paratext": {"path": PARATEXT.as_posix(), "sha256": audit["outputs"][PARATEXT.as_posix()]},
            "counts": audit["counts"], "source": audit["source"]}


def lexical_segments(row):
    layer = row.get("editorial_layer", {})
    if layer.get("schema") != SCHEMA or not isinstance(layer.get("original_text"), str):
        raise ValueError("Unsupported source-reviewed editorial layer")
    expected = retain_spans(layer["original_text"], layer["excluded_spans"])
    text = _reading(expected)
    if layer.get("body_spans") != expected or row.get("text") != text or row.get("analysis_text") != text:
        raise ValueError("Editorial lexical projection differs from its retained body spans")
    return [span["text"] for span in expected]


def apply(root=ROOT):
    root = Path(root)
    artifacts, audit = build(root)
    if sha((root / CORPUS).read_bytes()) not in {audit["inputs"][CORPUS.as_posix()], audit["outputs"][CORPUS.as_posix()]}:
        raise ValueError("Photius changed outside the reviewed apparatus correction")
    if sha((root / ALIASES).read_bytes()) not in {audit["inputs"][ALIASES.as_posix()], audit["outputs"][ALIASES.as_posix()]}:
        raise ValueError("Historical aliases changed outside the reviewed apparatus correction")
    if (root / PARATEXT).exists() and (root / PARATEXT).read_bytes() != artifacts[PARATEXT]:
        raise ValueError("Apparatus paratext was independently edited")
    for path, raw in artifacts.items():
        target = root / path
        if path.is_relative_to(ARCHIVE) and target.exists() and target.read_bytes() != raw:
            raise ValueError("Refusing to replace a frozen apparatus audit artifact")
    for path, raw in artifacts.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return audit


def undo(root=ROOT):
    root = Path(root)
    before, aliases_before, outputs, audit = _validated_archive(root, require_current_review=False)
    if any((root / path).read_bytes() != raw for path, raw in outputs.items()):
        raise ValueError("Unapply later edits before undoing the apparatus layer")
    (root / CORPUS).write_bytes(before)
    (root / ALIASES).write_bytes(aliases_before)
    (root / PARATEXT).unlink()
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--undo", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = apply(args.root) if args.apply else check(args.root) if args.check else undo(args.root) if args.undo else build(args.root)[1]
    print(json.dumps(result["counts"]))
