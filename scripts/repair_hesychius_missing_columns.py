#!/usr/bin/env python3
"""Recover Hesychius columns 259–260 with reversible, source-pinned additions.

This bounded layer inserts two collated column records into the released
duplicate-reviewed Hesychius primary. Every predecessor byte remains unchanged.
Literal independent OCR predictions and the complete word networks remain
available. No dictionary supplies a substitute reading.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from hesychius_gap_observations import (
    AUDIT, BOUNDARY, EDITION, OCR_SHA256, PREDECESSOR_SHA256, PRIMARY, QUALIFICATION, SLUG, SOURCES,
)

ROOT = Path(__file__).resolve().parents[1]
NETWORKS = AUDIT + "/word-networks.json.gz"
RECORDS = AUDIT + "/records.jsonl.gz"
WITNESSES = f"data/corpus_secondary/{SLUG}.missing-columns-witnesses.jsonl"
AUTHORITY = AUDIT + "/changes.json"
PREIMAGE = AUDIT + "/before.json.gz"
OCR_FILES = tuple(AUDIT + f"/{checkpoint}.jsonl" for checkpoint in ("qwen36", "qwen38"))
OUTPUTS = frozenset((PRIMARY, WITNESSES, NETWORKS, RECORDS))
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def recipe_pins():
    scripts = Path(__file__).parent
    return {name: sha((scripts / name).read_bytes()) for name in (
        "repair_hesychius_missing_columns.py", "hesychius_gap_observations.py",
        "capture_hesychius_gap.py", "run_hesychius_gap_ocr.py", "ocr_consensus.py",
        "repair_reviewed_duplicate_blocks.py")}


def local_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not str(path).startswith("data/"):
        raise ValueError("Unsafe Hesychius artifact path")
    return Path(root) / path


def _word_character(char):
    return unicodedata.category(char).startswith(("L", "M")) or char in "'’ʼ᾽"


def source_role_spans(text, *, column=None):
    """Conservatively exclude printed editorial insertions and suspect lemmas.

    Parentheses and square brackets remain literal evidence, including complete
    parenthesized entries. A partial word touching an insertion is excluded in
    full. A dagger excludes the following lemma word. Unmatched signs fail
    closed, since OCR punctuation cannot establish a complete lexical scope.
    """
    spans, stack = [], []
    pairs = {"(": ")", "[": "]", "<": ">", "⟨": "⟩"}
    for index, char in enumerate(text):
        if char in pairs:
            stack.append((char, index))
        elif char in pairs.values():
            if not stack or pairs[stack[-1][0]] != char:
                raise ValueError("Unbalanced editorial scope in fresh Hesychius OCR")
            opening, start = stack.pop()
            if not stack:
                end = index + 1
                while start and _word_character(text[start - 1]):
                    start -= 1
                while end < len(text) and _word_character(text[end]):
                    end += 1
                spans.append((start, end, "editorial insertion or reference in printed parentheses/brackets or their OCR angle-bracket readings"))
    if stack:
        raise ValueError("Unclosed editorial scope in fresh Hesychius OCR")
    for match in re.finditer(r"[†‡+]\s*", text):
        end = match.end()
        while end < len(text) and _word_character(text[end]):
            end += 1
        if end > match.end():
            spans.append((match.start(), end, "printed dagger marks a suspect lemma"))
    if column == 260:
        # Both source images show a dagger before the first lemma. Some raw
        # predictions omit that small sign; its absence cannot create a vote.
        first = re.match(r"[^\n]*?[··:]", text)
        if first is None:
            raise ValueError("Missing first Hesychius column-260 lemma")
        spans.append((first.start(), first.end(),
            "source-reviewed column-260 first lemma has a printed dagger even when OCR omits it"))
    # Merge nested/overlapping exclusions into a complete offset partition.
    joined = []
    for start, end, reason in sorted(spans):
        if joined and start <= joined[-1][1]:
            old_start, old_end, old_reason = joined[-1]
            joined[-1] = (old_start, max(end, old_end), old_reason + "; " + reason)
        else:
            joined.append((start, end, reason))
    retained, excluded, cursor = [], [], 0
    for start, end, reason in joined:
        if cursor < start:
            retained.append({"start": cursor, "end": start, "text": text[cursor:start]})
        excluded.append({"start": start, "end": end, "text": text[start:end], "reason": reason})
        cursor = end
    if cursor < len(text):
        retained.append({"start": cursor, "end": len(text), "text": text[cursor:]})
    return retained, excluded


def checked_readings(root):
    from capture_hesychius_gap import check
    from run_hesychius_gap_ocr import MODELS, PROMPT
    root = Path(root)
    manifest = check(root)
    manifest_raw = (root / AUDIT / "source-evidence.json").read_bytes()
    columns = {column["id"]: column for column in manifest["columns"]}
    readings = {259: [], 260: []}
    source_pins = {AUDIT + "/source-evidence.json": sha(manifest_raw)}
    for path in OCR_FILES:
        raw = (root / path).read_bytes()
        source_pins[path] = sha(raw)
        rows = [json.loads(line) for line in raw.splitlines()]
        meta = rows[0]["_meta"]
        checkpoint = Path(path).stem
        if sha(raw) != OCR_SHA256[checkpoint]:
            raise ValueError("Pinned fresh Hesychius OCR artifact changed")
        if (meta.get("checkpoint") != checkpoint or (meta.get("model"), meta.get("revision")) != MODELS[checkpoint]
                or meta.get("prompt") != PROMPT or meta.get("prompt_sha256") != sha(PROMPT.encode())
                or meta.get("temperature") != 0 or meta.get("max_tokens") != 4500
                or meta.get("manifest_sha256") != sha(manifest_raw)
                or meta.get("runner_sha256") != recipe_pins()["run_hesychius_gap_ocr.py"]):
            raise ValueError("Fresh Hesychius OCR checkpoint, prompt, or image authority changed")
        observed = set()
        for row in rows[1:]:
            identity = row["id"]
            if identity not in columns or identity in observed:
                raise ValueError("Unknown or repeated Hesychius OCR column")
            observed.add(identity)
            column = columns[identity]
            if (row.get("image_sha256") != column["sha256"] or row.get("source") != column["source"]
                    or row.get("printed_column") != column["printed_column"]
                    or row.get("finish_reason") != "stop" or row.get("error")
                    or not row.get("raw_prediction", "").strip()):
                raise ValueError("Failed, truncated, or changed Hesychius OCR column")
            text = row["raw_prediction"]
            retained, excluded = source_role_spans(text, column=column["printed_column"])
            readings[column["printed_column"]].append({
                "id": checkpoint + ":" + identity, "vote_group": checkpoint,
                "artifact_sha256": sha(encode({"raw_ocr_sha256": sha(raw), "id": identity,
                    "image_sha256": column["sha256"], "text": text})),
                "source_artifact_sha256": sha(raw), "source": row["source"],
                "model": meta["model"], "revision": meta["revision"],
                "source_page": column, "text": text, "voting_segments": retained,
                "abstention_audit": {"source_review": {
                    "path": AUDIT + "/source-evidence.json", "sha256": sha(manifest_raw)},
                    "reviewed_text_sha256": sha(text.encode()),
                    "excluded_spans": excluded}})
        if observed != set(columns):
            raise ValueError("Both physical scans of both columns are required per checkpoint")
    for column, witnesses in readings.items():
        if len(witnesses) != 4 or {w["vote_group"] for w in witnesses} != {"qwen36", "qwen38"}:
            raise ValueError("Independent Hesychius checkpoint coverage changed")
    for row in [*manifest["images"], *manifest["columns"]]:
        source_pins[row["path"]] = row["sha256"]
    return readings, source_pins


def build(root, predecessor, *, recorded_at):
    from ocr_consensus import compact_corpus_consensus, merge_witnesses
    if sha(predecessor) != PREDECESSOR_SHA256:
        raise ValueError("Hesychius duplicate-reviewed predecessor changed")
    readings, source_pins = checked_readings(root)
    networks, records, additions, literal = {}, [], [], []
    for column in (259, 260):
        key = f"schmidt-1867.column-{column}"
        result = merge_witnesses(readings[column])
        # A single remaining checkpoint cannot establish a new lexical reading.
        # Keep its surface and raw support, but require both checkpoints in scalar counts.
        for slot in result["ocr_consensus"]["slots"]:
            if slot["lexical_eligible"] and slot["status"] == "single-witness":
                slot["lexical_eligible"] = False
                slot["lexical_exclusion"] = "recovery requires two independent checkpoints"
        result["analysis_text"] = " ".join(slot["selected"] for slot in result["ocr_consensus"]["slots"]
            if slot["lexical_eligible"])
        result["ocr_consensus"]["policy"] += " Newly recovered lexical readings require both checkpoint groups."
        networks[key] = result
        row = {"urn": SLUG, "cts": "urn:cts:greekLit:tlg4085.tlg002", "edition": EDITION,
            "source": "ocr", "license": "PD", "lang": "grc", "locus": key,
            **compact_corpus_consensus(result, {"path": NETWORKS, "key": key}),
            "source_printed_columns": [column], "corrections": ["source-recovery", "collation"],
            "hesychius_gap_recovery": {"authority": AUTHORITY, "key": key}}
        additions.append(row)
        for witness in readings[column]:
            literal.append({"urn": SLUG, "cts": row["cts"], "source": "ocr", "license": "PD",
                "edition": "schmidt-1867-gap-literal-2026-10", "locus": key + "." + witness["id"],
                "text": witness["text"], "source_role": "literal-gap-OCR-witness",
                "source_page": witness["source_page"], "model": witness["model"],
                "revision": witness["revision"], "vote_group": witness["vote_group"],
                "current_target": {"slug": SLUG, "path": PRIMARY, "locus": key}})
        records.append({"key": key, "recorded_at": recorded_at, "original_text": "",
            "corrected_text": result["text"], "analysis_text": result["analysis_text"],
            "operation": "insert previously absent printed column", "source_readings": readings[column],
            "source_evidence": AUDIT + "/source-evidence.json", "boundary": BOUNDARY,
            "qualification": QUALIFICATION})
    output, found, previous = [], False, None
    for raw in predecessor.splitlines(keepends=True):
        row = json.loads(raw)
        if row["locus"] == BOUNDARY["insert_before"]:
            if found or previous != BOUNDARY["insert_after"]:
                raise ValueError("Reviewed Hesychius insertion neighbors changed")
            output.append(jsonl(additions))
            found = True
        output.append(raw)
        previous = row["locus"]
    if not found:
        raise ValueError("Missing Hesychius insertion point")
    outputs = {PRIMARY: b"".join(output), WITNESSES: jsonl(literal),
        NETWORKS: gzip.compress(encode(networks), mtime=0),
        RECORDS: gzip.compress(jsonl(records), mtime=0)}
    counts = {"primary_columns_added": 2, "literal_witnesses": len(literal),
        "analysis_greek_tokens": sum(len(GREEK.findall(row["analysis_text"])) for row in additions),
        "surface_greek_tokens": sum(len(GREEK.findall(row["text"])) for row in additions),
        "reading_statuses": dict(sum((Counter(row["ocr_consensus"]["counts"]) for row in additions), Counter())),
        "column_reading_statuses": {str(row["source_printed_columns"][0]): row["ocr_consensus"]["counts"]
            for row in additions},
        "single_checkpoint_slots_excluded": sum(slot.get("lexical_exclusion") ==
            "recovery requires two independent checkpoints" for result in networks.values()
            for slot in result["ocr_consensus"]["slots"]),
        "source_role_excluded_raw_tokens_across_eight_witnesses": sum(
            len(GREEK.findall(span["text"])) for witnesses in readings.values() for witness in witnesses
            for span in witness["abstention_audit"]["excluded_spans"]),
        "predecessor_rows": len(predecessor.splitlines()), "current_rows": len(b"".join(output).splitlines())}
    return outputs, counts, source_pins


def archived_inputs(root):
    path = Path(root) / PREIMAGE
    if not path.exists():
        return {PRIMARY: (Path(root) / PRIMARY).read_bytes()}
    values = json.loads(gzip.decompress(path.read_bytes()))
    return {name: None if value is None else base64.b64decode(value, validate=True)
            for name, value in values.items()}


@lru_cache(maxsize=4)
def _active(root, signature):
    path = Path(root) / AUTHORITY
    archive = Path(root) / PREIMAGE
    if path.exists() != archive.exists():
        raise ValueError("Orphaned Hesychius authority or preimage")
    if not path.exists():
        return False
    current = (Path(root) / PRIMARY).read_bytes()
    if current == archived_inputs(root)[PRIMARY]:
        return False
    # Restoring both layers in reverse order is another independently pinned
    # inactive epoch. This check needs no still-valid new correction evidence.
    import repair_reviewed_duplicate_blocks as predecessor
    if sha(current) == predecessor.INPUTS[PRIMARY] and not predecessor.active(root):
        return False
    return True


def active(root=ROOT):
    root = Path(root)
    import repair_reviewed_duplicate_blocks as predecessor
    paths = [AUTHORITY, PREIMAGE, PRIMARY,
             predecessor.AUDIT + "/changes.json", predecessor.AUDIT + "/before.json.gz"]
    old_authority = root / predecessor.AUDIT / "changes.json"
    if old_authority.exists():
        paths.extend(json.loads(old_authority.read_bytes())["outputs"])
    signature = tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in paths)
    return _active(str(root), signature)


def verify(root=ROOT, *, replay=True, active_only=True):
    root = Path(root)
    audit_raw = (root / AUTHORITY).read_bytes()
    audit = json.loads(audit_raw)
    archive = (root / PREIMAGE).read_bytes()
    if (audit.get("schema_version") != 1 or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("qualification") != QUALIFICATION or audit.get("predecessor_sha256") != PREDECESSOR_SHA256
            or audit.get("before_encoding") != "base64"
            or audit.get("sources") != json.loads(encode(SOURCES)) or audit.get("boundary") != BOUNDARY
            or audit.get("before_sha256") != sha(archive) or set(audit.get("outputs", {})) != OUTPUTS):
        raise ValueError("Hesychius recovery recipe, qualification, or preimage changed")
    for name, expected in audit["recipe_sha256"].items():
        if sha((root / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Hesychius recovery recipe changed: " + name)
    before = archived_inputs(root)
    if (set(before) != OUTPUTS or sha(before[PRIMARY]) != PREDECESSOR_SHA256
            or any(before[name] is not None for name in OUTPUTS - {PRIMARY})):
        raise ValueError("Hesychius archived predecessor changed")
    for name, expected in audit["source_sha256"].items():
        if sha(local_path(root, name).read_bytes()) != expected:
            raise ValueError("Hesychius source evidence changed: " + name)
    for name, expected in audit["outputs"].items():
        if active_only and sha(local_path(root, name).read_bytes()) != expected:
            raise ValueError("Hesychius recovery output changed: " + name)
    if replay:
        outputs, counts, pins = build(root, before[PRIMARY], recorded_at=audit["recorded_at"])
        if ({name: sha(raw) for name, raw in outputs.items()} != audit["outputs"]
                or counts != audit["counts"] or pins != audit["source_sha256"]):
            raise ValueError("Hesychius source replay differs from authority")
    return audit, before


def authority_paths(root=ROOT):
    root = Path(root)
    if not (root / AUTHORITY).exists():
        return [AUTHORITY, PREIMAGE]
    audit = json.loads((root / AUTHORITY).read_bytes())
    return [AUTHORITY, PREIMAGE, *audit["source_sha256"], *audit["outputs"],
            *("scripts/" + name for name in recipe_pins())]


@lru_cache(maxsize=2)
def _verified(root, signature):
    audit, before = verify(root, replay=True)
    rows = {(row["urn"], row["locus"]): row for row in
        map(json.loads, (Path(root) / PRIMARY).read_bytes().splitlines()) if row.get("edition") == EDITION}
    return audit, before, rows


def _checked_state(root=ROOT):
    root = Path(root)
    signature = tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in authority_paths(root))
    return _verified(str(root), signature)


def checked_state(root=ROOT):
    return deepcopy(_checked_state(root))


def predecessor_bytes(root=ROOT):
    if not active(root):
        return None
    return _checked_state(root)[1][PRIMARY]


def validate_projection(row, root=ROOT):
    expected = _checked_state(root)[2].get((row.get("urn"), row.get("locus")))
    if expected != row:
        raise ValueError("Hesychius lexical projection differs from checked recovery")
    return row["analysis_text"]


def lexical_segments(row, root=ROOT):
    validate_projection(row, root)
    return []  # the word network does not establish punctuation or original adjacency


def publish(root, outputs):
    # Reuse only the generic atomic writer; no active predecessor authority is
    # consulted here and this helper is byte-for-byte pinned in recipe checks.
    from repair_reviewed_duplicate_blocks import publish as atomic_publish
    atomic_publish(root, outputs)


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    if active(root):
        raise ValueError("Hesychius recovery is already active")
    old = None
    if (root / AUTHORITY).exists():
        old, before = verify(root, replay=True, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Reapplying a frozen recovery cannot change its timestamp")
        recorded_at = old["recorded_at"]
    else:
        before = archived_inputs(root)
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, counts, pins = build(root, before[PRIMARY], recorded_at=recorded_at)
    for name in outputs:
        if name not in before:
            if (root / name).exists():
                raise ValueError("Refusing to overwrite an unowned Hesychius destination")
            before[name] = None
        current = (root / name).read_bytes() if (root / name).exists() else None
        if current != before[name]:
            raise ValueError("Recovery reapply found a later output change")
    archive = gzip.compress(encode({name: None if raw is None else base64.b64encode(raw).decode()
        for name, raw in before.items()}), mtime=0)
    audit = {"schema_version": 1, "issue": "https://github.com/open-greek/open-greek-corpus/issues/107",
        "recorded_at": recorded_at, "before_encoding": "base64", "before_sha256": sha(archive),
        "predecessor_sha256": PREDECESSOR_SHA256, "recipe_sha256": recipe_pins(),
        "source_sha256": pins, "sources": json.loads(encode(SOURCES)), "boundary": BOUNDARY,
        "outputs": {name: sha(raw) for name, raw in outputs.items()}, "counts": counts,
        "qualification": QUALIFICATION}
    if old is not None and encode(audit) != (root / AUTHORITY).read_bytes():
        raise ValueError("Recovery reapply must reproduce complete frozen audit")
    publish(root, {**outputs, PREIMAGE: archive, AUTHORITY: encode(audit)})
    return audit


def undo(root=ROOT):
    root = Path(root)
    audit = json.loads((root / AUTHORITY).read_bytes())
    if sha((root / PREIMAGE).read_bytes()) != audit["before_sha256"]:
        raise ValueError("Hesychius undo preimage changed")
    before = archived_inputs(root)
    if (set(before) != OUTPUTS or sha(before[PRIMARY]) != PREDECESSOR_SHA256
            or any(before[name] is not None for name in OUTPUTS - {PRIMARY})
            or set(audit["outputs"]) != OUTPUTS):
        raise ValueError("Hesychius undo predecessor changed")
    for name, expected in audit["outputs"].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError("Refusing to overwrite a later Hesychius change")
    publish(root, {name: before[name] for name in audit["outputs"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "verify", "undo"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored the exact duplicate-reviewed Hesychius predecessor")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"], sort_keys=True))
