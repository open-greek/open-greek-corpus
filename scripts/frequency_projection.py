"""Read explicit lexical and contextual fields from a published corpus export."""
from __future__ import annotations

import hashlib
from pathlib import Path

ANALYSIS_COUNT_BASIS = "Greek regex runs in the published lexical projection; unresolved and ineligible readings are excluded."
CONTEXT_COUNT_BASIS = "Only explicitly contiguous eligible text supplies positional evidence."


def projection_recipe_pins():
    path = Path(__file__)
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}


def lexical_text(row):
    text = row.get("analysis_text", row.get("text", ""))
    if not isinstance(text, str):
        raise ValueError("Published lexical text must be a string")
    return text


class FrequencyProjection:
    def __init__(self, data):
        import json
        self.rows = {}
        self.digest = "none"
        self.recipe_digest = hashlib.sha256(json.dumps(projection_recipe_pins(), sort_keys=True).encode()).hexdigest()

    def text(self, row):
        return lexical_text(row)

    def segments(self, row):
        lexical_text(row)
        if "analysis_segments" in row:
            segments = row["analysis_segments"]
            if not isinstance(segments, list) or not all(isinstance(s, str) for s in segments):
                raise ValueError("Published contiguous segments must be a list of strings")
            return segments
        return [] if "analysis_text" in row else [row.get("text", "")]

    def contextual_text(self, row):
        if row.get("contextual_eligible") is False or "analysis_text" in row:
            return None
        return lexical_text(row)
