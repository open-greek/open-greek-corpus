#!/usr/bin/env python3
"""Archive existing Herodas body-page OCR witnesses without rerunning recognition.

The legacy 8B output is diagnostic evidence, never a counted vote. The existing
Qwen3.6 output is a comparison witness whose readings still require the pinned
Headlam–Knox scan. Raw Markdown and Greek-only text are retained byte for byte;
historical metadata is reduced to relevant, nonpersonal facts and raw file
checksums. Model weight revisions and prompt hashes were not recorded.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "data/corpus_changes/herodas-headlam-knox-body/historical-witnesses.json.gz"
GENERATOR = "scripts/herodas_body_witnesses.py"
SOURCE = {
    "id": "headlam-knox-1922",
    "title": "Herodas: The Mimes and fragments",
    "editor": "Headlam, Walter; Knox, Alfred",
    "year": 1922,
    "license": "PD",
    "url": "https://archive.org/details/mimesfragments00hero",
    "sha256": "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a",
    "pdf_pages": 542,
}
RUNS = {
    "legacy": {
        "id": "headlam-knox-1922-cllg-legacy",
        "model": "CLLG/Qwen3VL-8B-synth_real",
        "role": "diagnostic-only",
        "counted_vote": False,
        "qualification": "Historical legacy recognizer output only. Retain disagreements for diagnosis; do not use it as a counted vote or as a new recognition fallback.",
    },
    "qwen36": {
        "id": "headlam-knox-1922-qwen36",
        "model": "Qwen/Qwen3.6-27B-FP8",
        "role": "comparison-witness",
        "counted_vote": True,
        "qualification": "Existing historical recognition, not a new run. Agreement is evidence, not automatic admission; source roles, gaps, and uncertain readings require the pinned scan and explicit alternatives.",
    },
}
METADATA_FILES = ("_timing.json", "manifest.jsonl", "_retry.json", "_qa.json", "_alignment.json")
NUMERIC_FIELDS = frozenset({
    "pages", "seconds", "pages_per_sec", "collapsed", "recovered", "failed",
    "batch_size", "concurrency", "expected", "greek_tokens", "old_greek_tokens",
    "vocab_overlap", "guns_per_1k", "old_guns_per_1k", "offset", "anchors_matched", "sampled",
})
ENUM_FIELDS = {
    "dtype": {"bfloat16", "float16", "float32"},
    "quantization": {"fp8", "bf16", "none"},
    "verdict": {"OK", "FAIL", "WARNING"},
    "class": {"identical", "offset", "messy", "undetectable"},
}
MANIFEST_FIELDS = frozenset({"page", "chars", "greek_chars", "looped", "truncated", "tiled"})
HEX = re.compile(r"[0-9a-f]{64}\Z")
GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
PROVENANCE_QUALIFICATION = (
    "The archived run records identify the model names but do not record weight revisions, "
    "historical prompt hashes, exact serving revisions, or complete per-request settings. "
    "Current driver defaults are not evidence of historical execution. Metadata metrics "
    "describe the entire annotated volume, not body coverage or a body recognition-error rate."
)
ARCHIVE_QUALIFICATION = "Historical raw readings only; this archive neither admits text nor chooses a winner when recognizers disagree."


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(packet: dict) -> bytes:
    return (json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=1, allow_nan=False) + "\n").encode()


def selected_pages(pages=None) -> list[int]:
    if pages is None:
        from herodas_body_source_observations import BODY_PAGES
        pages = [page["scan_page"] for page in BODY_PAGES]
    pages = list(pages)
    if (not pages or any(type(page) is not int or not 1 <= page <= SOURCE["pdf_pages"] for page in pages)
            or len(set(pages)) != len(pages)):
        raise ValueError("Historical witnesses require unique, explicit PDF page numbers within the pinned source")
    return sorted(pages)


def _facts(value, model):
    """Whitelist values; never archive raw logs, paths, hosts, or arbitrary strings."""
    facts = {}
    for field in NUMERIC_FIELDS:
        if field in value:
            number = value[field]
            if type(number) not in (int, float) or not math.isfinite(number):
                raise ValueError("Historical metadata has a nonnumeric run metric")
            facts[field] = number
    for field, accepted in ENUM_FIELDS.items():
        if field in value and isinstance(value[field], str) and value[field] in accepted:
            facts[field] = value[field]
    if "model" in value:
        if value["model"] != model:
            raise ValueError("Historical timing metadata names a different recognizer")
        facts["model"] = model
    return facts


def _manifest_entries(raw, pages):
    """Preserve every selected attempt; retries are not independent witnesses."""
    entries = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        page_name = entry.get("page")
        if not isinstance(page_name, str) or not re.fullmatch(r"herodas_hk_\d{4}", page_name):
            raise ValueError("Historical manifest has an unexpected page identity")
        page = int(page_name.rsplit("_", 1)[1])
        if page not in pages:
            continue
        item = {"page": page_name}
        for field in MANIFEST_FIELDS - {"page"}:
            if field not in entry:
                continue
            value = entry[field]
            if field in {"looped", "truncated", "tiled"}:
                if type(value) is not bool:
                    raise ValueError("Historical manifest has a nonboolean recognition flag")
            elif type(value) is not int or value < 0:
                raise ValueError("Historical manifest has an invalid character count")
            item[field] = value
        entries.setdefault(page, []).append(item)
    if set(entries) != set(pages):
        raise ValueError("Historical manifest does not account for every selected page")
    return [entry for page in pages for entry in entries[page]]


def _run_packet(root, kind, pages, snapshots):
    spec = deepcopy(RUNS[kind])
    metadata = {}
    for name in METADATA_FILES:
        path = root / name
        if not path.is_file():
            if name in {"_timing.json", "manifest.jsonl"}:
                raise ValueError("Historical witness is missing required run metadata: " + name)
            continue
        raw = path.read_bytes()
        snapshots[path] = sha(raw)
        if name == "manifest.jsonl":
            selected = {"selected_entries": _manifest_entries(raw, pages)}
        else:
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Historical run metadata must be an object")
            selected = {"facts": _facts(value, spec["model"])}
            if name == "_timing.json" and selected["facts"].get("model") != spec["model"]:
                raise ValueError("Historical timing metadata must identify its recognizer")
        metadata[name] = {"raw_sha256": sha(raw), "raw_bytes": len(raw), **selected}
    spec.update(model_revision=None, historical_prompt_sha256=None,
                serving_revision=None, metadata=metadata,
                provenance_qualification=PROVENANCE_QUALIFICATION)
    return spec


def build_packet(legacy_root, redo_root, pages=None) -> dict:
    """Read selected historical page files once, then check they stayed unchanged.

    ``packet['pages']`` is keyed by decimal page strings. Each value contains
    ``legacy`` and ``qwen36`` witnesses, each with raw ``md`` and ``grc`` files.
    Supplied runtime roots are never serialized into the public packet.
    """
    pages = selected_pages(pages)
    roots = {"legacy": Path(legacy_root), "qwen36": Path(redo_root)}
    if roots["legacy"].resolve() == roots["qwen36"].resolve():
        raise ValueError("Historical recognizers must use their distinct run directories")
    snapshots = {}
    runs = {kind: _run_packet(root, kind, pages, snapshots) for kind, root in roots.items()}
    records = {}
    for page in pages:
        record = {}
        for kind, root in roots.items():
            files = {}
            for label, suffix in (("md", ".md"), ("grc", ".grc.txt")):
                name = f"herodas_hk_{page:04}{suffix}"
                path = root / name
                raw = path.read_bytes()
                snapshots[path] = sha(raw)
                text = raw.decode("utf-8")
                files[label] = {"name": name, "sha256": sha(raw), "bytes": len(raw),
                                "text": text, "has_greek": bool(GREEK.search(text))}
            record[kind] = {"id": f"{runs[kind]['id']}-p{page:04}", "pdf_page": page, "files": files}
        records[str(page)] = record
    for path, expected in snapshots.items():
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise ValueError("A historical witness input changed during archival preparation: " + path.name)
    packet = {"schema_version": 1, "generator": GENERATOR, "source": deepcopy(SOURCE),
              "selected_pages": pages, "runs": runs, "pages": records,
              "qualification": ARCHIVE_QUALIFICATION}
    validate_packet(packet)
    return packet


def validate_packet(packet: dict) -> None:
    if (set(packet) != {"schema_version", "generator", "source", "selected_pages", "runs", "pages", "qualification"}
            or packet.get("schema_version") != 1 or packet.get("generator") != GENERATOR
            or packet.get("qualification") != ARCHIVE_QUALIFICATION
            or packet.get("source") != SOURCE or set(packet.get("runs", {})) != set(RUNS)):
        raise ValueError("Historical witness authority changed")
    pages = selected_pages(packet["selected_pages"])
    if pages != packet["selected_pages"] or set(packet["pages"]) != {str(page) for page in pages}:
        raise ValueError("Historical witness page accounting changed")
    for kind, spec in RUNS.items():
        run = packet["runs"][kind]
        if (set(run) != set(spec) | {"model_revision", "historical_prompt_sha256", "serving_revision", "metadata", "provenance_qualification"}
                or any(run.get(key) != value for key, value in spec.items())
                or run.get("model_revision") is not None or run.get("historical_prompt_sha256") is not None
                or run.get("serving_revision") is not None
                or run.get("provenance_qualification") != PROVENANCE_QUALIFICATION):
            raise ValueError("Historical witness recognizer or voting qualification changed")
        if not {"_timing.json", "manifest.jsonl"} <= set(run["metadata"]) <= set(METADATA_FILES):
            raise ValueError("Historical witness metadata accounting changed")
        for name, metadata in run["metadata"].items():
            if set(metadata) != {"raw_sha256", "raw_bytes", "selected_entries" if name == "manifest.jsonl" else "facts"}:
                raise ValueError("Historical metadata contains unreviewed fields")
            if not HEX.fullmatch(metadata["raw_sha256"]) or type(metadata["raw_bytes"]) is not int or metadata["raw_bytes"] <= 0:
                raise ValueError("Historical metadata has no valid raw-file pin")
            if name == "manifest.jsonl":
                entries = metadata["selected_entries"]
                if (any(set(entry) - MANIFEST_FIELDS for entry in entries)
                        or _manifest_entries(b"\n".join(json.dumps(entry).encode() for entry in entries), pages) != entries):
                    raise ValueError("Historical manifest selected entries changed")
            else:
                facts = metadata["facts"]
                if _facts(facts, spec["model"]) != facts:
                    raise ValueError("Historical metadata contains unreviewed facts")
                if name == "_timing.json" and facts.get("model") != spec["model"]:
                    raise ValueError("Historical timing lacks its recorded model")
    for page in pages:
        record = packet["pages"][str(page)]
        if set(record) != set(RUNS):
            raise ValueError("Historical page lacks a recognizer witness")
        for kind in RUNS:
            witness = record[kind]
            if (set(witness) != {"id", "pdf_page", "files"}
                    or witness["id"] != f"{RUNS[kind]['id']}-p{page:04}" or witness["pdf_page"] != page
                    or set(witness["files"]) != {"md", "grc"}):
                raise ValueError("Historical witness page identity changed")
            for label, suffix in (("md", ".md"), ("grc", ".grc.txt")):
                item = witness["files"][label]
                raw = item["text"].encode("utf-8")
                if (set(item) != {"name", "sha256", "bytes", "text", "has_greek"}
                        or item["name"] != f"herodas_hk_{page:04}{suffix}" or item["sha256"] != sha(raw)
                        or type(item["bytes"]) is not int or type(item["has_greek"]) is not bool
                        or item["bytes"] != len(raw) or item["has_greek"] != bool(GREEK.search(item["text"]))):
                    raise ValueError("Historical raw transcription or file identity changed")


def compressed(packet: dict) -> bytes:
    validate_packet(packet)
    return gzip.compress(encoded(packet), mtime=0)


def load_packet(path) -> dict:
    packet = json.loads(gzip.decompress(Path(path).read_bytes()))
    validate_packet(packet)
    return packet


def write_packet(packet: dict, out) -> dict:
    raw = compressed(packet)
    out = Path(out)
    if out.exists() and out.read_bytes() != raw:
        raise ValueError("Historical witness archive already contains different source readings")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=out.parent, prefix=out.name + ".", delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    temporary.replace(out)
    return {"pages": packet["selected_pages"], "sha256": sha(raw), "json_sha256": sha(encoded(packet)), "bytes": len(raw)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--redo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / OUTPUT)
    parser.add_argument("--pages", help="Optional comma-separated PDF pages; default is the reviewed BODY_PAGES")
    args = parser.parse_args()
    pages = [int(page) for page in args.pages.split(",")] if args.pages is not None else None
    packet = build_packet(args.legacy_root, args.redo_root, pages)
    print(json.dumps(write_packet(packet, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
