"""Countable text for corpus frequency exports, with checked witness collation.

Reader text is never changed here. Unresolved readings remain in the collation
with lower and upper counts; only attested agreement enters scalar frequency
tables. Single-witness material outside collated leaves remains countable.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]")
ANALYSIS_COUNT_BASIS = (
    "Greek regex runs in the checked frequency projection: shared collated "
    "attestations count once; unresolved, damaged, restored, and incomplete "
    "readings are excluded where explicit lexical eligibility is supplied"
)
CONTEXT_COUNT_BASIS = (
    "New positional evidence uses unprojected primary rows with complete contextual "
    "text. Rows with explicit lexical projections or collated spans supply no "
    "position vote because omitted readings or unresolved punctuation can "
    "change the preceding context."
)


def projection_recipe_pins():
    """Pin the code that determines lexical eligibility, including imported layers."""
    scripts = Path(__file__).resolve().parent
    names = ("frequency_projection.py", "critical_text.py", "repair_photius_apparatus.py", "repair_photius_body.py",
             "repair_photius_readings.py", "photius_reading_vote.py", "photius_body_vote.py",
             "repair_photius_historical_readings.py", "repair_photius_historical_batches.py", "ocr_consensus.py")
    return {name: hashlib.sha256((scripts / name).read_bytes()).hexdigest() for name in names}


def lexical_text(rec: dict) -> str:
    if rec.get("historical_reading_batches"):
        from repair_photius_historical_batches import validate_projection
        validate_projection(rec)
    if rec.get("historical_reading_repair") or rec.get("historical_source_reconstruction"):
        from repair_photius_historical_readings import validate_projection
        validate_projection(rec)
    if rec.get("reading_repair") and rec.get("urn") == "photius.bibliotheca":
        from repair_photius_readings import validate_projection
        validate_projection(rec)
    if rec.get("source_body_correction"):
        from repair_photius_body import validate_projection
        validate_projection(rec)
    if rec.get("editorial_layer"):
        from repair_photius_apparatus import lexical_segments
        lexical_segments(rec)
    if "analysis_text" in rec:
        if not isinstance(rec["analysis_text"], str):
            raise ValueError("analysis_text must be an explicit string")
        return rec["analysis_text"]
    if rec.get("ocr_consensus"):
        if "analysis_text" not in rec:
            raise ValueError("OCR consensus record is missing its checked analysis_text")
        return rec["analysis_text"]
    if rec.get("critical_markup"):
        from critical_text import lexical_text as critical_lexical_text
        return critical_lexical_text(rec)
    return rec.get("text", "")


class FrequencyProjection:
    def __init__(self, data: Path):
        self.rows = {}
        self.digest = "none"
        self.recipe_digest = hashlib.sha256(json.dumps(
            projection_recipe_pins(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
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

    def segments(self, rec: dict) -> list[str]:
        """Eligible runs whose original adjacency is known, for bigram metrics.

        Joining ``analysis_text`` across excluded words would manufacture a
        bigram. Structured projections retain those boundaries; an opaque
        analysis-only projection supplies counts but no adjacency evidence.
        """
        key = rec.get("urn", "") + ":" + rec.get("locus", "")
        text = lexical_text(rec)  # validate even when no bigram is possible
        if key in self.rows:
            source = rec.get("text", "")
            runs, previous = [], None
            for start, end in self.rows[key]:
                if previous is not None and not _GREEK.search(source[previous:start]):
                    runs[-1] += source[previous:end]
                else:
                    runs.append(source[start:end])
                previous = end
            return runs
        if rec.get("editorial_layer"):
            from repair_photius_apparatus import lexical_segments
            return lexical_segments(rec)
        if rec.get("historical_reading_batches"):
            from repair_photius_historical_batches import lexical_segments
            return lexical_segments(rec)
        if rec.get("ocr_consensus"):
            if "slots" not in rec["ocr_consensus"]:
                return []  # an older compact projection supplies no adjacency evidence
            runs, current = [], []
            for slot in rec["ocr_consensus"]["slots"]:
                if slot["lexical_eligible"]:
                    current.append(slot["selected"])
                elif current:
                    runs.append(" ".join(current))
                    current = []
            if current:
                runs.append(" ".join(current))
            return runs
        if rec.get("critical_markup"):
            runs, current, previous = [], [], None
            for token in rec["tokens"]:
                gap = rec["reading_text"][previous:token["start"]] if previous is not None else ""
                if not token["lexical_eligible"] or "…" in gap:
                    if current:
                        runs.append(" ".join(current))
                        current = []
                if token["lexical_eligible"]:
                    current.append(token["form"])
                previous = token["end"]
            if current:
                runs.append(" ".join(current))
            return runs
        if "analysis_text" in rec and text != rec.get("text", ""):
            return []
        return [text]

    def contextual_text(self, rec: dict) -> str | None:
        """Conservative context for measurements that infer lexical case folds."""
        text = lexical_text(rec)
        key = rec.get("urn", "") + ":" + rec.get("locus", "")
        if key in self.rows or "analysis_text" in rec or rec.get("critical_markup") or rec.get("ocr_consensus"):
            return None
        return text
