"""Countable text for corpus frequency exports, with checked witness collation.

Reader text is never changed here. Unresolved readings remain in the collation
with lower and upper counts; only attested agreement enters scalar frequency
tables. Single-witness material outside collated leaves remains countable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def lexical_text(rec: dict) -> str:
    if rec.get("critical_markup"):
        from critical_text import lexical_text as critical_lexical_text
        return critical_lexical_text(rec)
    return rec.get("text", "")


class FrequencyProjection:
    def __init__(self, data: Path):
        self.rows = {}
        self.digest = "none"
        path = data / "frequency_projection.json"
        if not path.exists():
            return
        raw = path.read_bytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        doc = json.loads(raw)
        for name, expected in doc["source_sha256"].items():
            actual = hashlib.sha256((data / "corpus" / name).read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"Frequency collation is stale for {name}; regenerate it")
        self.rows = doc["rows"]

    def text(self, rec: dict) -> str:
        key = rec.get("urn", "") + ":" + rec.get("locus", "")
        spans = self.rows.get(key)
        text = lexical_text(rec)
        if spans is None:
            return text
        return " ".join(text[start:end] for start, end in spans)
