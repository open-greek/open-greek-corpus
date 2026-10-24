#!/usr/bin/env python3
"""Bounded, non-admitting experiments over the frozen Dübner witness networks.

Source-reviewed cell permutations preserve every original character in their
routing record. They change neither the frozen producer nor its artifacts and
add no voter. Candidate delimiters alone do not authorize a layout decision.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from ocr_consensus import alignment_key, merge_witnesses, tokenize

ROOT = Path(__file__).resolve().parents[1]
NETWORKS = "data/corpus_changes/dubner-1855-scope/word-networks.json.gz"
SCHEMA = "dubner-lane-cell-permutation-v1"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def line_cells(witness):
    """Partition exact lane characters into cells, delimiters, and line endings."""
    text = witness["text"]
    lines = text.splitlines(keepends=True)
    row_ids = witness.get("source_rows", [])
    one_row_per_line = len(lines) == len(row_ids)
    parts, cursor = [], 0
    for number, line in enumerate(lines, 1):
        body = line.rstrip("\r\n")
        if body.count("|") > 1:
            raise ValueError("Multiple delimiters need a separately reviewed partition")
        source = row_ids[number - 1] if one_row_per_line else None
        if "|" in body:
            split = body.index("|")
            ranges = [("left", 0, split), ("delimiter", split, split + 1),
                      ("right", split + 1, len(body))]
        else:
            ranges = [("whole", 0, len(body))]
        ranges.append(("line-ending", len(body), len(line)))
        for cell, start, end in ranges:
            if start == end:
                continue
            parts.append({"line": number, "cell": cell, "start": cursor + start,
                "end": cursor + end, "text": line[start:end], "source_row": source})
        cursor += len(line)
    if cursor != len(text) or "".join(part["text"] for part in parts) != text:
        raise ValueError("Layout partition lost original characters")
    return parts


def candidate(witness):
    """Describe delimiter coverage without deciding the source's reading order."""
    if not witness.get("vote_group", "").endswith("harvard"):
        return None
    lines = [line for line in witness["text"].splitlines() if line.strip()]
    piped = [line for line in lines if line.count("|") == 1]
    if len(piped) < 5:
        return None
    nonempty_left = sum(bool(line.split("|")[0].strip()) for line in piped)
    nonempty_right = sum(bool(line.split("|")[1].strip()) for line in piped)
    return {"lane_id": witness["id"], "vote_group": witness["vote_group"],
        "derived": witness.get("derived", False), "source_rows": witness.get("source_rows", []),
        "nonblank_lines": len(lines), "piped_lines": len(piped),
        "unmarked_lines": len(lines) - len(piped),
        "nonempty_left_cells": nonempty_left, "nonempty_right_cells": nonempty_right,
        "uniform_two_column_candidate": len(piped) == len(lines)
            and min(nonempty_left, nonempty_right) >= .75 * len(lines),
        "first_line": lines[0], "last_line": lines[-1]}


def column_order(witness):
    """Propose a uniform left-then-right order; approval remains external."""
    description = candidate(witness)
    if not description or not description["uniform_two_column_candidate"]:
        raise ValueError("Sparse or partial delimiters cannot establish uniform columns")
    cells = line_cells(witness)
    return [[part["line"], side] for side in ("left", "right")
            for part in cells if part["cell"] == side and part["text"].strip()]


def route_witness(witness, page_key, decision):
    """Apply an approved exact cell permutation, retaining its complete preimage.

    ``reading_order`` contains one-based ``[line, cell]`` references. Every
    nonblank content cell must appear once. Delimiters, original line endings,
    and empty cells remain in the record; generated newlines are explicit.
    """
    if decision.get("approved") is not True or not decision.get("evidence"):
        raise ValueError("A layout permutation requires explicit source-review evidence")
    parts = line_cells(witness)
    cells = {(part["line"], part["cell"]): part for part in parts
             if part["cell"] not in {"delimiter", "line-ending"}}
    order = [tuple(reference) for reference in decision["reading_order"]]
    if len(set(order)) != len(order) or any(reference not in cells for reference in order):
        raise ValueError("Layout order repeats or invents a source cell")
    omitted = [part for key, part in cells.items() if key not in order and part["text"].strip()]
    if omitted:
        raise ValueError("Layout order omitted a nonblank original cell")
    text = "\n".join(cells[reference]["text"] for reference in order)
    # All visible source characters survive. Only the layout delimiters and
    # whitespace may be held outside the new word-alignment projection.
    visible = lambda value: Counter(char for char in value if not char.isspace() and char != "|")
    if visible(text) != visible(witness["text"]):
        raise ValueError("Layout routing changed a visible original character")
    record = {"schema": SCHEMA, "page_key": page_key, "witness_id": witness["id"],
        "vote_group": witness["vote_group"], "original_witness": deepcopy(witness),
        "original_text_sha256": sha(witness["text"].encode()), "parts": parts,
        "reading_order": [list(reference) for reference in order], "generated_separator": "\n",
        "evidence": deepcopy(decision["evidence"]), "routed_text_sha256": sha(text.encode())}
    routed = deepcopy(witness)
    routed["text"] = text
    routed["source_artifact_sha256"] = witness["artifact_sha256"]
    routed["artifact_sha256"] = sha(encoded(record))
    routed["layout_routing"] = {"schema": SCHEMA, "routing_sha256": routed["artifact_sha256"],
        "original_text_sha256": record["original_text_sha256"]}
    return routed, record


def restore_witness(routed, record):
    """Verify the permutation and return the literal complete source witness."""
    original = record["original_witness"]
    text = "".join(part["text"] for part in record["parts"])
    if text != original["text"] or sha(text.encode()) != record["original_text_sha256"]:
        raise ValueError("Original layout preimage changed")
    decision = {"approved": True, "reading_order": record["reading_order"], "evidence": record["evidence"]}
    expected, expected_record = route_witness(original, record["page_key"], decision)
    if routed != expected or record != expected_record:
        raise ValueError("Routed layout postimage changed")
    return deepcopy(original)


def realign_page(base_result, page_key, decisions):
    """Re-run the frozen merger on checked permutations without adding a voter."""
    witnesses, routes = [], []
    known = {witness["id"] for witness in base_result["ocr_consensus"]["witnesses"]}
    if set(decisions) - known:
        raise ValueError("A layout decision names an unknown witness")
    for witness in base_result["ocr_consensus"]["witnesses"]:
        if witness["id"] in decisions:
            routed, record = route_witness(witness, page_key, decisions[witness["id"]])
            assert restore_witness(routed, record) == witness
            witnesses.append(routed); routes.append(record)
        else:
            witnesses.append(deepcopy(witness))
    result = merge_witnesses(witnesses)
    if {(w["id"], w["vote_group"]) for w in witnesses} != {
            (w["id"], w["vote_group"]) for w in base_result["ocr_consensus"]["witnesses"]}:
        raise ValueError("Alignment changed the original voter identities")
    old_counts, counts = base_result["ocr_consensus"]["counts"], result["ocr_consensus"]["counts"]
    return {"page_key": page_key, "network": result, "routings": routes,
        "old_counts": old_counts, "new_counts": counts,
        "unresolved_reduction": old_counts.get("unresolved", 0) - counts.get("unresolved", 0),
        "agreement_gain": counts.get("agreement", 0) - old_counts.get("agreement", 0)}


def diagnostics(networks):
    categories, candidates = Counter(), []
    for key, result in networks.items():
        network = result["ocr_consensus"]
        for slot in network["slots"]:
            if slot["status"] != "unresolved":
                continue
            if "" in slot["tied_readings"]:
                categories["omission_tie"] += 1
            elif len({alignment_key(reading["text"]) for reading in slot["readings"]}) == 1:
                categories["accent_case_or_elision_only"] += 1
            else:
                categories["different_word_readings"] += 1
            if len({group for reading in slot["readings"] for group in reading["support_groups"]}) == 1:
                categories["one_group_internal_disagreement"] += 1
        for witness in network["witnesses"]:
            description = candidate(witness)
            if description:
                candidates.append({"page_key": key, **description})
    return {"pages": len(networks), "unresolved_categories": dict(categories), "candidates": candidates}


def pilot_decisions(result, page_key):
    """Return only source-inspected permutations, never a score-selected order."""
    decisions = {}
    approved = {"equites:0101": 102, "equites:0109": 110, "plutus:0415": 440, "aves:0254": 281}
    for witness in result["ocr_consensus"]["witnesses"]:
        if page_key not in approved or not witness["vote_group"].endswith("harvard"):
            continue
        if page_key == "aves:0254":
            if len(witness["text"].splitlines()) != 103:
                raise ValueError("The reviewed Birds lane no longer has its 103 source rows")
            order = [[line, "left"] for line in range(1, 54)]
            order += [[line, "right"] for line in (1, 2)]
            order += [[line, "left"] for line in range(54, 104)]
        else:
            order = column_order(witness)
        decisions[witness["id"]] = {"approved": True, "reading_order": order,
            "evidence": {"method": "Direct inspection of the two printed columns and their gutter",
                "source_pdf_sha256": "61c07b9dbde80569c6e54238f2cbb0897d8bb33386a9ecad389836bd67e0c600",
                "source_pdf_page": approved[page_key], "reviewed_at": "2026-10-24",
                "qualification": "Ordering only; this observation does not correct OCR spellings."}}
    return decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = (args.root / NETWORKS).read_bytes()
    networks = json.loads(gzip.decompress(raw))
    report = diagnostics(networks)
    pilot = {}
    for key in ("equites:0101", "equites:0109", "plutus:0415", "aves:0254"):
        pilot[key] = realign_page(networks[key], key, pilot_decisions(networks[key], key))
    report.update(schema_version=1, baseline={"path": NETWORKS, "sha256": sha(raw)},
        pilot={key: {k: v for k, v in result.items() if k not in {"network", "routings"}}
               for key, result in pilot.items()})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_bytes(encoded(report))
    (args.out / "pilot-networks-and-routings.json.gz").write_bytes(gzip.compress(encoded(pilot), mtime=0))
    print(json.dumps({"report": str(args.out / "report.json"), "pages": len(pilot),
        "unresolved_reduction": sum(result["unresolved_reduction"] for result in pilot.values()),
        "agreement_gain": sum(result["agreement_gain"] for result in pilot.values())}, sort_keys=True))


if __name__ == "__main__":
    main()
