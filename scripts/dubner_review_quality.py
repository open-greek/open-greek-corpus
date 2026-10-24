"""Expose checked Dübner review boundaries and remaining reading uncertainty."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def measurement(root):
    import repair_dubner_readings as readings
    root = Path(root)
    authority = root / readings.AUDIT / "changes.json"
    if not authority.is_file() or not readings.active(root):
        return None
    audit, _ = readings.checked_state(root)
    assessment_path = root / readings.ASSESSMENT
    assessment = json.loads(assessment_path.read_bytes())
    return {"authority": {"path": readings.AUDIT + "/changes.json",
                "sha256": hashlib.sha256(authority.read_bytes()).hexdigest()},
        "assessment": {"path": readings.ASSESSMENT,
                "sha256": hashlib.sha256(assessment_path.read_bytes()).hexdigest()},
        "counts": audit["counts"], "review_scope": assessment["review_scope"],
        "held_layouts": [{"page_key": record["page_key"], "reason": record["reason"]}
                         for record in assessment["held_layouts"]],
        "reopen_when": assessment["reopening_circumstances"],
        "qualification": ("Reading-disagreement slots are not an OCR error count or an accuracy rate. "
            "The orthographic-only category folds case, combining marks, final sigma, and elision "
            "using the frozen alignment key. The one-group count overlaps the other three categories. "
            "All contrary readings remain available; unreviewed spellings are not certified.")}


def limitation(root):
    current = measurement(root)
    if current is None:
        return []
    return [{"key": "dubner-1855-unresolved-readings",
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/105",
        "status": "accepted-measured-limitation", "current_measurement": current,
        "why_no_bulk_action_remains": (
            "All ten delimiter-bearing candidate pages were inspected in both scans. Seven exact "
            "cell permutations exhaust that approved repair class. Three partial duplicate-column "
            "layouts require fragment-level occurrence association. Other disagreements need "
            "source-specific reading review; a normalized form or a lexicon match cannot decide "
            "the edition's printed letters."),
        "reopen_when": " ".join(current["reopen_when"])}]
