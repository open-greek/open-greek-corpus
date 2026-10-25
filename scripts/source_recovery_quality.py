"""Expose verified source recovery, source scope, and duplicate accounting.

Missing authorities are absent measurements. Changed or partial authorities
raise rather than becoming zero-valued measurements. These summaries are
derived from full source replays, never from previously generated reports.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _authority(root, path, before):
    current = (root / path).read_bytes()
    if current != before:
        raise ValueError("Source recovery authority changed during verification: " + path)
    return {"path": path, "sha256": _sha(current)}


def _hesychius(root):
    import repair_hesychius_missing_columns as repair
    if not repair.active(root):
        return None
    path = repair.AUTHORITY
    raw = (root / path).read_bytes()
    audit, _, _ = repair.checked_state(root)
    counts = deepcopy(audit["counts"])
    unresolved = counts["reading_statuses"].get("unresolved", 0)
    single_checkpoint = counts["single_checkpoint_slots_excluded"]
    capture = repair.AUDIT + "/source-evidence.json"
    return {
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/107",
        "repair_status": "missing-main-text-leaf-recovered",
        "authority": _authority(root, path, raw),
        "source_evidence": {"path": capture, "sha256": audit["source_sha256"][capture]},
        "recovered_printed_columns": deepcopy(audit["boundary"]["recovered_columns"]),
        "counts": counts,
        "remaining_reading_uncertainty": {
            "unresolved_alignment_slots": unresolved,
            "single_checkpoint_slots_excluded": single_checkpoint,
            "total_slots_excluded": unresolved + single_checkpoint,
            "count_basis": (
                "Unresolved exact-word alignment slots and singly supported readings in the "
                "two recovered main-text columns. These are not OCR error counts or an error rate."
            ),
        },
        "lexical_count_policy": (
            "A scalar lexical reading requires both independent checkpoint groups. Printed "
            "editorial or reference scopes, suspect lemmas, and unresolved readings are excluded. "
            "Literal predictions and contrary readings remain available. The word projection "
            "supplies no context n-grams or positional evidence."
        ),
        "qualification": audit["qualification"],
    }


def _westermann(root):
    import repair_westermann_scope as repair
    if not repair.active(root):
        return None
    from westermann_source_observations import CAPTURE_PATH, REVIEW_PATH, SOURCE
    path = repair.AUDIT + "/changes.json"
    raw = (root / path).read_bytes()
    audit, _ = repair.checked_state(root)
    # A role with no observations has no Counter key. Normalize only these
    # verified accounting categories; an inaccessible authority never gets here.
    counts = deepcopy(audit["counts"])
    for role in ("primary", "comparative", "editorial", "held"):
        counts.setdefault(role + "_rows", 0)
        counts.setdefault(role + "_greek_tokens", 0)
    return {
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/104",
        "repair_status": "anthology-partitioned-by-source-work-and-text-role",
        "authority": _authority(root, path, raw),
        "source_evidence": {
            "capture": {"path": CAPTURE_PATH, "sha256": _sha((root / CAPTURE_PATH).read_bytes())},
            "review": {"path": REVIEW_PATH, "sha256": _sha((root / REVIEW_PATH).read_bytes())},
        },
        "source": deepcopy(SOURCE),
        "counts": counts,
        "lexical_count_policy": (
            "Only source-supported historical primary units contribute lexical counts. "
            "Comparative witnesses of material already represented in a primary, modern "
            "editorial text, and held ambiguous text remain outside those counts. "
            "Every original row and exact character partition remains reversible."
        ),
        "qualification": audit["qualification"],
    }


def _pindar(root):
    import repair_pindar_duplicate_primaries as repair
    if not repair.active(root):
        return None
    path = repair.AUDIT + "/changes.json"
    raw = (root / path).read_bytes()
    audit, _ = repair.verify(root, replay=True)
    return {
        "repair_status": "identical-first1k-serializations-counted-once",
        "authority": _authority(root, path, raw),
        "source_revision": repair.REVISION,
        "source_license": repair.LICENSE,
        "counts": deepcopy(audit["counts"]),
        "lexical_count_policy": (
            "Exact duplicate serializations of one digital edition contribute one primary "
            "occurrence. Canonical primary bytes remain unchanged; original text, citations, "
            "source licenses, and retired identifiers remain available."
        ),
        "qualification": audit["qualification"],
    }


def measurement(root):
    """Return only currently active, source-verified recovery measurements."""
    root = Path(root)
    values = {}
    for name, producer in (
        ("hesychius_missing_columns", _hesychius),
        ("westermann_source_scope", _westermann),
        ("pindar_duplicate_primaries", _pindar),
    ):
        current = producer(root)
        if current is not None:
            values[name] = current
    return {"schema_version": 1, **values} if values else None


def limitations(root):
    """Qualify remaining readings without describing the repaired leaf as absent."""
    current = _hesychius(Path(root))
    if current is None or not current["remaining_reading_uncertainty"]["total_slots_excluded"]:
        return []
    return [{
        "key": "hesychius-recovered-columns-reading-uncertainty",
        "issue": current["issue"],
        "status": "accepted-measured-limitation",
        "current_measurement": current,
        "why_no_bulk_action_remains": (
            "The previously missing main-text leaf is recovered from two independent physical "
            "copies of the same edition. Both pinned OCR checkpoints have transcribed both "
            "columns in both copies. Exact voting and source-reviewed critical-scope exclusions "
            "exhaust this bounded automatic repair. Remaining disagreements require occurrence "
            "review of the printed source; a normalized form or dictionary match cannot select "
            "the edition's letters."
        ),
        "reopen_when": (
            "Reopen reading review when occurrence-level inspection of the pinned Harvard and "
            "Ghent columns, or a better independently retained transcription, establishes a "
            "specific unresolved reading. Reopen the missing-leaf defect only if the recovered "
            "edition identity, physical boundary, or source evidence is invalidated."
        ),
    }]
