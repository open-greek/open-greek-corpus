#!/usr/bin/env python3
"""Apply reversible scan-reviewed readings above the frozen missing-leaf repair."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import json
from pathlib import Path
import tempfile

import repair_hesychius_missing_columns as base
from hesychius_gap_reading_observations import SHARED_ERRORS, TLG, UNCERTAIN

ROOT = base.ROOT
PRIMARY = base.PRIMARY
AUDIT = "data/corpus_changes/hesychius-gap-reading-review"
AUTHORITY = AUDIT + "/changes.json"
PREIMAGE = AUDIT + "/before.json.gz"
NETWORKS = AUDIT + "/word-networks.json.gz"
RECORDS = AUDIT + "/records.jsonl.gz"
OUTPUTS = frozenset((PRIMARY, NETWORKS, RECORDS))
PREDECESSOR_SHA256 = "22e558269963ad917d9e452e87ce5e7df9811853ac0b511e6f0b2873518a632c"
QUALIFICATION = (
    "Occurrence readings verified against both physical Schmidt 1867 copies. "
    "TLG's Latte edition identifies comparison entries but supplies no lexical vote. "
    "Unclear diacritics remain alternatives. Original OCR votes and critical-scope "
    "exclusions remain available; this word projection establishes no contextual adjacency."
)


def recipe_pins():
    return {name: base.sha((Path(__file__).parent / name).read_bytes()) for name in (
        "repair_hesychius_gap_readings.py", "hesychius_gap_reading_observations.py",
        "ocr_consensus.py", "citation_alias_state.py")}


def archived_inputs(root):
    values = json.loads(gzip.decompress((Path(root) / PREIMAGE).read_bytes()))
    before = {name: None if raw is None else base64.b64decode(raw, validate=True)
              for name, raw in values.items()}
    if (set(before) != OUTPUTS or base.sha(before[PRIMARY]) != PREDECESSOR_SHA256
            or any(before[name] is not None for name in OUTPUTS - {PRIMARY})):
        raise ValueError("Hesychius reading review predecessor changed")
    return before


@contextmanager
def original_view(root, predecessor):
    """Replace only the later-owned primary with its exact frozen predecessor."""
    if base.sha(predecessor) != PREDECESSOR_SHA256:
        raise ValueError("Hesychius reading review predecessor changed")
    from citation_alias_state import _overlay
    with tempfile.TemporaryDirectory(prefix="hesychius-reading-predecessor-") as directory:
        view = Path(directory)
        _overlay(Path(root), view, {Path(PRIMARY).parts: predecessor})
        yield view


def _render(slot):
    review = slot.get("source_review")
    if review and review["decision"] != "held":
        return review["corrected_text"]
    if slot["status"] == "unresolved":
        return "⟦" + " ∥ ".join(t or "∅" for t in slot["tied_readings"]) + "⟧"
    if slot["status"] == "omission":
        return ""
    reading = next(r for r in slot["readings"] if r["text"] == slot["selected"])
    surfaces = Counter(reading["surfaces"].values())
    best = max(surfaces.values())
    winners = sorted(s for s, count in surfaces.items() if count == best)
    return winners[0] if len(winners) == 1 else "⟦" + " ∥ ".join(winners) + "⟧"


def build(root, predecessor, *, recorded_at):
    root = Path(root)
    with original_view(root, predecessor) as view:
        old_audit, _ = base.verify(view, replay=True)
    source_pins = {name: base.sha((root / name).read_bytes())
                   for name in base.authority_paths(root) if name != PRIMARY}
    networks = json.loads(gzip.decompress((root / base.NETWORKS).read_bytes()))
    records = []
    for column in (259, 260):
        key = f"schmidt-1867.column-{column}"
        result = networks[key]
        slots = result["ocr_consensus"]["slots"]
        uncertain = {s["position"] for s in slots if not s["lexical_eligible"]}
        if uncertain != {r[0] for r in UNCERTAIN[column]}:
            raise ValueError("The reviewed 45-slot Hesychius campaign changed")
        seen = set()
        for category, observations in (("uncertain", UNCERTAIN), ("shared-error", SHARED_ERRORS)):
            for position, corrected, entry, comparison_entry, note in observations[column]:
                if position in seen or (category == "shared-error" and position in uncertain):
                    raise ValueError("Overlapping Hesychius source observations")
                seen.add(position)
                slot = slots[position]
                before = deepcopy(slot)
                evidence = [{"path": f"{base.AUDIT}/source-evidence/{copy}-column-{column}.png",
                             "printed_column": column, "entry": entry} for copy in ("harvard", "ghent")]
                for item in evidence:
                    item["sha256"] = source_pins[item["path"]]
                decision = "held" if corrected is None else "merged-fragment" if not corrected else "scan-confirmed"
                review = {"decision": decision, "corrected_text": corrected,
                    "source": "manual inspection of both retained Schmidt 1867 scans",
                    "source_evidence": evidence, "comparison": {**TLG, "alpha_entry": comparison_entry},
                    "note": note, "recorded_at": recorded_at}
                records.append({"key": key, "position": position, "category": category,
                    "original_text": _render(before), "original_slot": before, **review})
                slot["source_review"] = review
                if corrected is not None:
                    slot["selected"] = corrected
                    slot["status"] = "source-reviewed" if corrected else "reviewed-omission"
                    slot["lexical_eligible"] = bool(corrected)
                    slot["lexical_exclusion"] = None if corrected else "printed word reconstructed once at adjacent reviewed slot"
        result["text"] = " ".join(t for slot in slots if (t := _render(slot)))
        result["analysis_text"] = " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"])
        result["ocr_consensus"]["counts"] = dict(Counter(s["status"] for s in slots))
        result["ocr_consensus"]["policy"] += " Later scan review is separate from, and does not alter, the original checkpoint votes."
    from ocr_consensus import compact_corpus_consensus
    output = []
    changed = set()
    for raw in predecessor.splitlines(keepends=True):
        row = json.loads(raw)
        key = row.get("locus")
        if row.get("edition") == base.EDITION and key in networks:
            if key in changed:
                raise ValueError("Repeated Hesychius recovery locus")
            changed.add(key)
            row.update(compact_corpus_consensus(networks[key], {"path": NETWORKS, "key": key}))
            row["hesychius_gap_reading_review"] = {"authority": AUTHORITY, "key": key}
            row["corrections"] = [*row["corrections"], "scan-reading-review"]
            output.append(base.jsonl([row]))
        else:
            output.append(raw)
    if changed != set(networks):
        raise ValueError("Missing reviewed Hesychius column")
    counts = deepcopy(old_audit["counts"])
    counts.update({
        "analysis_greek_tokens": sum(len(base.GREEK.findall(r["analysis_text"])) for r in networks.values()),
        "surface_greek_tokens": sum(len(base.GREEK.findall(r["text"])) for r in networks.values()),
        "reading_statuses": dict(sum((Counter(r["ocr_consensus"]["counts"]) for r in networks.values()), Counter())),
        "column_reading_statuses": {key.rsplit("-", 1)[1]: r["ocr_consensus"]["counts"] for key, r in networks.items()},
        "single_checkpoint_slots_excluded": 0,
        "reading_review": {"initial_uncertain_slots": len([r for r in records if r["category"] == "uncertain"]),
            "remaining_uncertain_slots": len([r for r in records if r["decision"] == "held"]),
            "merged_fragment_slots": len([r for r in records if r["decision"] == "merged-fragment"]),
            "shared_errors_corrected": len([r for r in records if r["category"] == "shared-error"]),
            "newly_admitted_lexical_slots": len([r for r in records if r["category"] == "uncertain" and r["decision"] == "scan-confirmed"])}})
    outputs = {PRIMARY: b"".join(output), NETWORKS: gzip.compress(base.encode(networks), mtime=0),
               RECORDS: gzip.compress(base.jsonl(records), mtime=0)}
    return outputs, counts, source_pins


def active(root=ROOT):
    root = Path(root)
    if (root / AUTHORITY).exists() != (root / PREIMAGE).exists():
        raise ValueError("Orphaned Hesychius reading review authority or preimage")
    if not (root / AUTHORITY).exists():
        return (root / PRIMARY).exists() and b'"hesychius_gap_reading_review"' in (root / PRIMARY).read_bytes()
    raw = (root / PRIMARY).read_bytes()
    if base.sha(raw) == PREDECESSOR_SHA256:
        return False
    if base.sha(raw) == base.PREDECESSOR_SHA256 or not base.active(root):
        return False
    return True


def authority_paths(root=ROOT):
    root = Path(root)
    names = {AUTHORITY, PREIMAGE, *OUTPUTS, *("scripts/" + n for n in recipe_pins())}
    names.update(base.authority_paths(root))
    return names


def signature(root):
    root = Path(root)
    return tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
                 if (root / name).is_file() else (name, None, None) for name in sorted(authority_paths(root)))


def verify(root=ROOT, *, active_only=True):
    root = Path(root)
    audit = json.loads((root / AUTHORITY).read_bytes())
    before = archived_inputs(root)
    if (audit.get("schema_version") != 1 or audit.get("predecessor_sha256") != PREDECESSOR_SHA256
            or audit.get("qualification") != QUALIFICATION or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("before_sha256") != base.sha((root / PREIMAGE).read_bytes())
            or set(audit.get("outputs", {})) != OUTPUTS):
        raise ValueError("Hesychius reading review authority changed")
    for name, expected in audit["recipe_sha256"].items():
        if base.sha((root / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Hesychius reading review recipe changed: " + name)
    if active_only:
        for name, expected in audit["outputs"].items():
            if base.sha((root / name).read_bytes()) != expected:
                raise ValueError("Hesychius reading review output changed: " + name)
    outputs, counts, pins = build(root, before[PRIMARY], recorded_at=audit["recorded_at"])
    if ({name: base.sha(raw) for name, raw in outputs.items()} != audit["outputs"]
            or counts != audit["counts"] or pins != audit["source_sha256"]):
        raise ValueError("Hesychius reading source replay differs from authority")
    return audit, before


@lru_cache(maxsize=2)
def _checked(root_name, initial):
    root = Path(root_name)
    audit, before = verify(root)
    rows = {(r["urn"], r["locus"]): r for r in map(json.loads, (root / PRIMARY).read_bytes().splitlines())
            if r.get("edition") == base.EDITION}
    if signature(root) != initial:
        raise ValueError("Hesychius reading authority changed during verification")
    return audit, before, rows


def checked_state(root=ROOT):
    root = Path(root).absolute()
    return deepcopy(_checked(str(root), signature(root)))


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    if active(root):
        raise ValueError("Hesychius reading review is already active")
    old = None
    if (root / AUTHORITY).exists():
        old, before = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Frozen Hesychius reading review timestamp changed")
        recorded_at = old["recorded_at"]
    else:
        before = {name: (root / name).read_bytes() if (root / name).exists() else None for name in OUTPUTS}
        if before[NETWORKS] is not None or before[RECORDS] is not None:
            raise ValueError("Unowned Hesychius reading output")
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, counts, pins = build(root, before[PRIMARY], recorded_at=recorded_at)
    for name in OUTPUTS:
        current = (root / name).read_bytes() if (root / name).exists() else None
        if current != before[name]:
            raise ValueError("Refusing to overwrite a later Hesychius change")
    archive = gzip.compress(base.encode({name: None if raw is None else base64.b64encode(raw).decode()
                                        for name, raw in before.items()}), mtime=0)
    audit = {"schema_version": 1, "recorded_at": recorded_at, "before_encoding": "base64",
        "before_sha256": base.sha(archive), "predecessor_sha256": PREDECESSOR_SHA256,
        "recipe_sha256": recipe_pins(), "source_sha256": pins,
        "outputs": {name: base.sha(raw) for name, raw in outputs.items()},
        "counts": counts, "qualification": QUALIFICATION}
    if old is not None and base.encode(audit) != (root / AUTHORITY).read_bytes():
        raise ValueError("Hesychius reapply must reproduce the frozen reading review")
    base.publish(root, {**outputs, PREIMAGE: archive, AUTHORITY: base.encode(audit)})
    return audit


def undo(root=ROOT):
    root = Path(root)
    audit = json.loads((root / AUTHORITY).read_bytes())
    if base.sha((root / PREIMAGE).read_bytes()) != audit["before_sha256"] or set(audit["outputs"]) != OUTPUTS:
        raise ValueError("Hesychius reading undo authority changed")
    before = archived_inputs(root)
    for name, pin in audit["outputs"].items():
        if base.sha((root / name).read_bytes()) != pin:
            raise ValueError("Refusing to overwrite a later Hesychius change")
    base.publish(root, before)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "verify", "undo"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored the exact pre-review Hesychius recovery")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"], sort_keys=True))
