#!/usr/bin/env python3
"""Retain the historical Phoenix OCR witnesses without promoting a prediction.

``source_root`` is the directory containing ``runs/editions``. The old and
replacement runs are separate predictions of the same scan. The aligned output
is only a copy of the replacement run, not a third independent witness. This
module reads existing artifacts; it does not run or recommend the older model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


BASE = "phoenix_choliambi_crusius"
PREFIX = "runs/editions/"
OLD = PREFIX + BASE + "_out/"
REDO = PREFIX + BASE + "_redo_out/"
ALIGNED = PREFIX + BASE + "_aligned_out/"
PAGES = (68, 69)
PURPOSE = "Historical OCR comparison evidence; the printed scan determines the admitted reading."
WITNESSES = (
    {"id": "historical-original", "model": "CLLG/Qwen3VL-8B-synth_real", "directory": OLD},
    {"id": "historical-replacement", "model": "Qwen/Qwen3.6-27B-FP8", "directory": REDO},
)
EXPECTED_SHA256 = {
    OLD + "_timing.json": "18c53c5819b6ed64e5102332ba70ea5460e70cd4c25ae507624016b37a48f19e",
    OLD + BASE + "_0068.md": "db586588a449aaaf8c63ea40e74f6113ec76a9a2394ff690ae486b9843d7716b",
    OLD + BASE + "_0068.grc.txt": "7aaefbaf7496f4a627f4d8e72e5769e14cffd8cdeee9b1bb10bfcb2694c971dd",
    OLD + BASE + "_0069.md": "f7ce11c896cf522ace9154786b7c6c5d8d9570a2a4522068d6f3f44290ac98b3",
    OLD + BASE + "_0069.grc.txt": "6072618b02abcfade8189b3a3f5fea00e72b61f53b76f94210848abd2e642884",
    REDO + "_timing.json": "35ad86ed1a34e064a1b302bf5ad8fdeb7d0f7a73c356d54db4c552db5945afea",
    REDO + BASE + "_0068.md": "199916cd3530b1a88b5f018f78c9a7a7b99069e1c49bdcd3ffe7f2cb2c21f811",
    REDO + BASE + "_0068.grc.txt": "b5b1ae34fd04d98b7a74c916d2f66f18e10d8a7c30e2d94ed4f5636ef332bb76",
    REDO + BASE + "_0069.md": "c9d9ed2724eff1f28970bc2e156fac397e0671f948ef7e96fc2f3b5f09a948d9",
    REDO + BASE + "_0069.grc.txt": "1fd185e91906d513e7690385c58763facf131b6921b66e2524528fc75b20fd9f",
    ALIGNED + "_alignment.json": "7a8498081885c4a488b7e0531a08f7ca4a6acf2e3e47fb8812fafa653bc325d3",
}
for _page in PAGES:
    for _suffix in (".md", ".grc.txt"):
        _name = f"{BASE}_{_page:04d}{_suffix}"
        EXPECTED_SHA256[ALIGNED + _name] = EXPECTED_SHA256[REDO + _name]


def _witnesses():
    return [
        {
            **witness,
            "historical_only": True,
            "model_metadata_path": witness["directory"] + "_timing.json",
            "pages": [
                {
                    "scan_page": page,
                    "tagged_prediction_path": witness["directory"] + f"{BASE}_{page:04d}.md",
                    "greek_extraction_path": witness["directory"] + f"{BASE}_{page:04d}.grc.txt",
                }
                for page in PAGES
            ],
        }
        for witness in WITNESSES
    ]


def _copies():
    return {
        "directory": ALIGNED,
        "derived_from": "historical-replacement",
        "independent_witness": False,
        "alignment_metadata_path": ALIGNED + "_alignment.json",
        "copied_files": {
            ALIGNED + f"{BASE}_{page:04d}{suffix}": REDO + f"{BASE}_{page:04d}{suffix}"
            for page in PAGES
            for suffix in (".md", ".grc.txt")
        },
    }


def build_packet(source_root: str | Path) -> dict:
    """Read the pinned full predictions and extractions into a portable packet."""
    root = Path(source_root)
    files = {}
    for relative, expected in EXPECTED_SHA256.items():
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Missing historical OCR input: {relative}")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Historical OCR input changed: {relative}")
        files[relative] = {"sha256": expected, "bytes": len(raw), "text": raw.decode("utf-8")}
    packet = {
        "schema_version": 1,
        "purpose": PURPOSE,
        "witnesses": _witnesses(),
        "derived_copy": _copies(),
        "input_sha256": dict(EXPECTED_SHA256),
        "files": files,
    }
    validate_packet(packet)
    return packet


def validate_packet(packet: dict, source_root: str | Path | None = None) -> None:
    """Reject missing evidence, revised predictions, or false witness independence.

    Archived validation requires no external source directory. Supplying
    ``source_root`` additionally verifies the retained packet against live files.
    """
    if set(packet) != {"schema_version", "purpose", "witnesses", "derived_copy", "input_sha256", "files"}:
        raise ValueError("Historical OCR packet fields changed")
    if packet["schema_version"] != 1 or packet["purpose"] != PURPOSE:
        raise ValueError("Historical OCR packet schema or scope changed")
    if packet["witnesses"] != _witnesses() or packet["derived_copy"] != _copies():
        raise ValueError("Historical OCR witness identity or independence changed")
    if packet["input_sha256"] != EXPECTED_SHA256 or set(packet["files"]) != set(EXPECTED_SHA256):
        raise ValueError("Historical OCR input accounting changed")
    for relative, expected in EXPECTED_SHA256.items():
        record = packet["files"][relative]
        if set(record) != {"sha256", "bytes", "text"} or not isinstance(record["text"], str):
            raise ValueError(f"Historical OCR file record changed: {relative}")
        raw = record["text"].encode("utf-8")
        if record["sha256"] != expected or record["bytes"] != len(raw) or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Historical OCR prediction changed: {relative}")
        if source_root is not None:
            path = Path(source_root) / relative
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError(f"Live historical OCR input changed: {relative}")
    for witness in packet["witnesses"]:
        metadata = json.loads(packet["files"][witness["model_metadata_path"]]["text"])
        if metadata.get("model") != witness["model"]:
            raise ValueError("Historical OCR model differs from its retained metadata")
    for copied, original in packet["derived_copy"]["copied_files"].items():
        if packet["files"][copied]["text"] != packet["files"][original]["text"]:
            raise ValueError("Aligned OCR is not the recorded replacement copy")
