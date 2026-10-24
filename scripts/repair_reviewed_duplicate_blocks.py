#!/usr/bin/env python3
"""Collate source-verified repeated Cyril and Hesychius blocks reversibly.

Literal rows move to secondary witnesses; a word network represents each
physical passage once. The repair never selects a spelling using a lexicon.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from reviewed_duplicate_block_observations import (
    AUDIT, CALFA_RAW_SHA256, CYRIL, GROUPS, HESYCHIUS, INPUTS, QUALIFICATION,
)

ROOT = Path(__file__).resolve().parents[1]
EDITION = "reviewed-duplicate-block-consensus-2026-10"
NETWORKS = AUDIT + "/word-networks.json.gz"
RECORDS = AUDIT + "/records.jsonl.gz"
FRAGMENT = AUDIT + "/passage-aliases.json"
PRIMARY = tuple(f"data/corpus/{slug}.jsonl" for slug in (CYRIL, HESYCHIUS))
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def local_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "data":
        raise ValueError("Unsafe reviewed duplicate artifact path: " + name)
    return Path(root) / path


def publish(root, outputs):
    """Stage all bytes before mutation and restore preimages on an I/O failure."""
    originals = {name: local_path(root, name).read_bytes()
                 if local_path(root, name).is_file() else None for name in outputs}
    staged = {}
    try:
        for name, raw in outputs.items():
            path = local_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if raw is not None:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(raw)
                    staged[name] = Path(handle.name)
        changed = []
        try:
            for name, raw in outputs.items():
                path = local_path(root, name)
                if raw is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(staged[name], path)
                changed.append(name)
        except OSError:
            for name in reversed(changed):
                path = local_path(root, name)
                if originals[name] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(originals[name])
            raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def recipe_pins():
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in (
        "repair_reviewed_duplicate_blocks.py", "reviewed_duplicate_block_observations.py",
        "capture_reviewed_duplicate_sources.py", "ocr_consensus.py")}


def check_inputs(before):
    for name, expected in INPUTS.items():
        if before.get(name) is None or sha(before[name]) != expected:
            raise ValueError("Reviewed duplicate source preimage changed: " + name)
    if sha(gzip.decompress(before["data/reference/calfa-pg73/PG073_text.txt.gz"])) != CALFA_RAW_SHA256:
        raise ValueError("Calfa source text differs from its pinned upstream revision")


def archived_inputs(root):
    archive = Path(root) / AUDIT / "before.json.gz"
    if archive.exists():
        values = json.loads(gzip.decompress(archive.read_bytes()))
        return {name: None if text is None else base64.b64decode(text, validate=True)
                for name, text in values.items()}
    return {name: local_path(root, name).read_bytes() for name in INPUTS}


def build(root, before, *, recorded_at):
    from ocr_consensus import compact_corpus_consensus, merge_witnesses
    check_inputs(before)
    rows = {name: [json.loads(line) for line in before[name].splitlines()] for name in PRIMARY}
    by_id = {(row["urn"], row["locus"]): row for values in rows.values() for row in values}
    networks, records, replacements, removed, secondary, aliases = {}, [], {}, set(), defaultdict(list), defaultdict(dict)
    summaries = []
    for group in GROUPS:
        slug, key = group["slug"], group["key"]
        path = f"data/corpus/{slug}.jsonl"
        witness_path = f"data/corpus_secondary/{slug}.reviewed-duplicate-witnesses.jsonl"
        current = {"slug": slug, "path": path, "locus": group["locus"]}
        lanes, originals = [], []
        for index, loci in enumerate(group["lanes"]):
            original = [by_id[(slug, locus)] for locus in loci]
            text = "\n".join(row["text"] for row in original)
            lane_id = key + f":reading:{index + 1}"
            # Different fragments of one pinned artifact need distinct fragment
            # identities, while their shared vote group prevents false majority.
            lanes.append({"id": lane_id, "vote_group": group["vote_group"],
                "artifact_sha256": sha(encoded({"input_sha256": INPUTS[path],
                    "loci": loci, "text": text})), "text": text,
                "source_rows": list(loci), "source_path": path,
                "source_sha256": INPUTS[path]})
            for row in original:
                identity = (slug, row["locus"])
                if identity in removed:
                    raise ValueError("A literal source row occurs in two duplicate collations")
                removed.add(identity)
                originals.append(row)
                secondary[ witness_path ].append(dict(row,
                    source_role="literal-duplicate-reading",
                    source_role_evidence=group["evidence"], current_target=current,
                    reviewed_duplicate_witness={"authority": AUDIT + "/changes.json", "key": key}))
                aliases[slug][row["locus"]] = {"path": witness_path, "slug": slug,
                    "storage": "secondary", "locus": row["locus"], "current": current}
        result = merge_witnesses(lanes)
        networks[key] = result
        compact = compact_corpus_consensus(result, {"path": NETWORKS, "key": key})
        canonical = {"urn": slug, "cts": originals[0]["cts"], "source": originals[0]["source"],
            "license": originals[0]["license"], "lang": "grc", "edition": EDITION,
            "locus": group["locus"], **compact,
            "source_printed_columns": list(group["printed_columns"]),
            "corrections": ["structural", "collation"],
            "reviewed_duplicate_block": {"authority": AUDIT + "/changes.json", "key": key}}
        replacements[(slug, group["insert_before"])] = canonical
        records.append({"key": key, "recorded_at": recorded_at,
            "original_rows": originals, "original_texts": lanes,
            "corrected_text": result["text"], "analysis_text": result["analysis_text"],
            "canonical_target": current, "evidence": group,
            "source_capture": AUDIT + "/source-evidence.json", "word_network": NETWORKS,
            "qualification": QUALIFICATION})
        summaries.append({"key": key, "slug": slug,
            "original_rows": len(originals), "primary_rows": 1,
            "original_greek_tokens": sum(len(GREEK.findall(row["text"])) for row in originals),
            "surface_greek_tokens": len(GREEK.findall(result["text"])),
            "analysis_greek_tokens": len(GREEK.findall(result["analysis_text"])),
            "reading_statuses": result["ocr_consensus"]["counts"],
            "literal_witness_rows": len(originals)})
    outputs = {name: jsonl(values) for name, values in secondary.items()}
    for name in PRIMARY:
        output = []
        for raw in before[name].splitlines(keepends=True):
            row = json.loads(raw)
            identity = (row["urn"], row["locus"])
            if identity in replacements:
                output.append(jsonl([replacements[identity]]))
            if identity not in removed:
                output.append(raw)
        outputs[name] = b"".join(output)
    outputs[NETWORKS] = gzip.compress(encoded(networks), mtime=0)
    outputs[RECORDS] = gzip.compress(jsonl(records), mtime=0)
    outputs[FRAGMENT] = encoded({"schema_version": 1, "aliases": aliases})
    counts = {"original_rows": len(removed), "literal_witness_rows": sum(map(len, secondary.values())),
        "collated_passages": len(networks), "primary_rows_removed": len(removed) - len(networks),
        "original_greek_tokens": sum(item["original_greek_tokens"] for item in summaries),
        "surface_greek_tokens": sum(item["surface_greek_tokens"] for item in summaries),
        "analysis_greek_tokens": sum(item["analysis_greek_tokens"] for item in summaries),
        "reading_statuses": dict(sum((Counter(item["reading_statuses"]) for item in summaries), Counter()))}
    if counts["original_rows"] != 119 or counts["collated_passages"] != 5:
        raise ValueError("Reviewed duplicate corpus accounting changed")
    return outputs, summaries, counts


def active(root):
    path = Path(root) / AUDIT / "changes.json"
    if not path.exists():
        return False
    audit = json.loads(path.read_bytes())
    before = archived_inputs(root)
    return not all((local_path(root, name).read_bytes() if local_path(root, name).is_file()
                    else None) == before[name] for name in audit["outputs"])


def verify(root=ROOT, *, active_only=True, replay=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("before_encoding") != "base64"
            or audit.get("inputs") != INPUTS
            or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("qualification") != QUALIFICATION):
        raise ValueError("Reviewed duplicate recipe or source qualification changed")
    for name, expected in audit["recipe_sha256"].items():
        if sha((root / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Reviewed duplicate recipe file changed: " + name)
    raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["before_sha256"]:
        raise ValueError("Reviewed duplicate preimage archive changed")
    before = archived_inputs(root)
    check_inputs(before)
    for name in set(INPUTS) - set(PRIMARY):
        if sha(local_path(root, name).read_bytes()) != INPUTS[name]:
            raise ValueError("Reviewed duplicate pinned source artifact changed: " + name)
    from capture_reviewed_duplicate_sources import check as check_capture
    capture = check_capture(root)
    if (sha((root / AUDIT / "source-evidence.json").read_bytes()) != audit["source_capture_sha256"]
            or capture["sources"] != audit["sources"]):
        raise ValueError("Reviewed duplicate source authority changed")
    for name, expected in audit["outputs"].items():
        actual = sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
        if active_only and actual != expected:
            raise ValueError("Reviewed duplicate output changed: " + name)
    if replay:
        outputs, summaries, counts = build(root, before, recorded_at=audit["recorded_at"])
        if ({name: sha(raw) if raw is not None else None for name, raw in outputs.items()} != audit["outputs"]
                or summaries != audit["groups"] or counts != audit["counts"]):
            raise ValueError("Reviewed duplicate literal replay differs")
    return audit, before


def historical_bytes(root, path):
    """The two exact primary preimages, after verifying the active authority."""
    if path not in PRIMARY or not active(root):
        return None
    _, before = verify(root, replay=False)
    return before[path]


def alias_fragment(root):
    if not active(root):
        return None
    verify(root, replay=True)
    return {**json.loads((Path(root) / FRAGMENT).read_bytes()), "authority": {
        "path": AUDIT + "/changes.json", "sha256": sha((Path(root) / AUDIT / "changes.json").read_bytes())}}


@lru_cache(maxsize=2)
def _verified_rows(root, signature):
    # The cached first admission must reproduce the five source collations,
    # not merely trust a jointly edited audit/output hash table.
    verify(root, replay=True)
    return {(row["urn"], row["locus"]): row for name in PRIMARY
            for row in map(json.loads, (Path(root) / name).read_bytes().splitlines())
            if row.get("edition") == EDITION}


def validate_projection(row, root=ROOT):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    capture = json.loads((root / AUDIT / "source-evidence.json").read_bytes())
    paths = [AUDIT + "/changes.json", AUDIT + "/before.json.gz", AUDIT + "/source-evidence.json",
        *audit["outputs"], *INPUTS, *(entry["path"] for entry in capture["files"]),
        *("scripts/" + name for name in recipe_pins())]
    signature = tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in paths)
    expected = _verified_rows(str(root), signature).get((row["urn"], row["locus"]))
    if expected != row:
        raise ValueError("Reviewed duplicate lexical projection differs from its checked authority")
    return row["analysis_text"]


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    manifest, archive = root / AUDIT / "changes.json", root / AUDIT / "before.json.gz"
    if manifest.exists() != archive.exists():
        raise ValueError("An orphaned duplicate authority or preimage cannot authorize an apply")
    if manifest.exists() and active(root):
        raise ValueError("Reviewed duplicate repair is already active")
    before = archived_inputs(root)
    old = None
    if manifest.exists():
        old, _ = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Reapplying a frozen duplicate audit cannot change its timestamp")
        recorded_at = old["recorded_at"]
        for name in old["outputs"]:
            if (local_path(root, name).read_bytes() if local_path(root, name).exists() else None) != before[name]:
                raise ValueError("Duplicate reapply found a later change: " + name)
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, summaries, counts = build(root, before, recorded_at=recorded_at)
    for name in outputs:
        if name not in before:
            if local_path(root, name).exists():
                raise ValueError("Refusing to overwrite an unowned duplicate destination: " + name)
            before[name] = None
    raw = gzip.compress(encoded({name: None if value is None else base64.b64encode(value).decode("ascii")
        for name, value in before.items()}), mtime=0)
    from capture_reviewed_duplicate_sources import check as check_capture
    capture = check_capture(root)
    audit = {"schema_version": 1, "recorded_at": recorded_at, "before_encoding": "base64",
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/33",
        "recipe_sha256": recipe_pins(), "before_sha256": sha(raw), "inputs": INPUTS,
        "outputs": {name: sha(value) if value is not None else None for name, value in outputs.items()},
        "groups": summaries, "counts": counts, "qualification": QUALIFICATION,
        "source_capture_sha256": sha((root / AUDIT / "source-evidence.json").read_bytes()),
        "sources": capture["sources"]}
    if old is not None and encoded(audit) != manifest.read_bytes():
        raise ValueError("Duplicate reapply must reproduce the complete frozen audit")
    publish(root, {**outputs, AUDIT + "/before.json.gz": raw, AUDIT + "/changes.json": encoded(audit)})
    return audit


def undo(root=ROOT):
    """Restore literal preimages even when source evidence has been invalidated."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["before_sha256"]:
        raise ValueError("Reviewed duplicate undo archive changed")
    before = json.loads(gzip.decompress(raw))
    for name, expected in audit["outputs"].items():
        actual = sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
        if actual != expected:
            raise ValueError("Refusing to overwrite a later duplicate output: " + name)
    publish(root, {name: None if before[name] is None else base64.b64decode(before[name], validate=True)
                   for name in audit["outputs"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("action", choices=("apply", "verify", "undo"))
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored literal duplicate-block preimages")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
