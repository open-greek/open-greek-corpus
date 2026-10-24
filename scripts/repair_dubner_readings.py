#!/usr/bin/env python3
"""Admit bounded Dübner scan readings and source-reviewed column permutations.

The scope repair remains frozen. This layer archives its exact replaced
postimages, preserves every original witness and contrary reading, and gives
neither extraction another vote. Source adjudications identify occurrences;
they are not a third OCR witness or an assertion of exhaustive proofreading.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re
import unicodedata

import repair_dubner_scholias as base
from experiment_dubner_alignment import route_witness, restore_witness, diagnostics
from ocr_consensus import (APOSTROPHES, GREEK, compact_corpus_consensus, greek_letter,
                           lexical_eligible, merge_witnesses, tokenize)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/dubner-1855-readings"
NETWORKS = AUDIT + "/word-networks.json.gz"
RECORDS = AUDIT + "/records.jsonl.gz"
OUTSIDE = AUDIT + "/outside-primary-readings.jsonl.gz"
ASSESSMENT = AUDIT + "/assessment.json"
READING_REVIEW = "data/corpus_changes/dubner-reading-review/source-review.json"
LAYOUT_REVIEW = "data/corpus_changes/dubner-layout-review/source-review.json"
QUALIFICATION = (base.QUALIFICATION + " A later bounded scan review corrects explicitly anchored "
    "historical occurrences and seven source-reviewed column permutations. Named source "
    "adjudications retain prior vote status and all contrary readings; they add no voter. "
    "Three partial duplicate-column layouts remain held. Outside-primary corrections are "
    "separate reading overlays and do not alter the frozen editorial witness display. "
    "The unresolved inventory measures extraction disagreement, not an OCR error rate.")
sha, encoded, jsonl, local_path, publish = base.sha, base.encoded, base.jsonl, base.local_path, base.publish


def recipe_pins():
    directory = Path(__file__).resolve().parent
    names = ("repair_dubner_readings.py", "dubner_layers.py", "experiment_dubner_alignment.py",
             "dubner_layout_observations.py", "capture_dubner_layouts.py",
             "dubner_reading_observations.py", "capture_dubner_readings.py")
    return {name: sha((directory / name).read_bytes()) for name in names}


def evidence(root):
    from capture_dubner_layouts import check as layouts_check
    from capture_dubner_readings import check as readings_check
    from dubner_reading_observations import build as readings_build
    layouts = layouts_check(root)
    captures = readings_check(root)
    readings = readings_build(root)
    files = {item["path"]: item["sha256"] for item in [*layouts["files"], *captures["files"]]}
    files.update({name: sha((Path(root) / name).read_bytes()) for name in (
        READING_REVIEW, LAYOUT_REVIEW, "data/corpus_changes/dubner-reading-review/capture.json")})
    for name, expected in files.items():
        if sha(local_path(root, name).read_bytes()) != expected:
            raise ValueError("Dübner reading evidence changed: " + name)
    return readings, layouts, dict(sorted(files.items()))


def archived_inputs(root):
    raw = (Path(root) / AUDIT / "before.json.gz").read_bytes()
    document = json.loads(gzip.decompress(raw))
    return {name: None if value is None else value.encode() for name, value in document.items()}


def translate_range(start, end, alternatives):
    """Translate literal row offsets through explicitly retained fallback edits."""
    edits = sorted(alternatives, key=lambda item: item["offset"])
    previous = -1
    for edit in edits:
        a, b = edit["offset"], edit["offset"] + len(edit["original"])
        if a < previous:
            raise ValueError("Overlapping fallback alternatives cannot translate an occurrence")
        previous = b
        if start < b and a < end and not (start <= a and b <= end):
            raise ValueError("A source occurrence partially overlaps a fallback alternative")
    delta = lambda position: sum(len(item["alternative"]) - len(item["original"])
        for item in edits if item["offset"] + len(item["original"]) <= position)
    return start + delta(start), end + delta(end)


def lane_pieces(witness, work, records, roles):
    """Prove original lane characters against exact exhaustive scope partitions."""
    consumed, pieces, cursor = Counter(), [], 0
    for identifier in witness["source_rows"]:
        record = records[identifier]
        possible = [part for part in roles[identifier]
                    if part["work"] == work and part["lexical_eligible"]]
        offset = consumed[identifier]
        if offset >= len(possible):
            raise ValueError("A witness row lacks its admitted source partition")
        part = possible[offset]
        consumed[identifier] += 1
        text = record["row"]["text"][part["start"]:part["end"]]
        pieces.append({"record": record, "part": part, "start": cursor,
                       "end": cursor + len(text), "text": text})
        cursor += len(text) + 1
    if "\n".join(item["text"] for item in pieces) != witness["text"]:
        raise ValueError("Frozen witness no longer reconstructs from literal source rows")
    return pieces


def patch_witness(witness, pieces, observations):
    """Correct identified occurrences before layout routing; keep exact preimages."""
    edits = []
    for piece in pieces:
        record, part = piece["record"], piece["part"]
        for observation in observations.get((record["path"], record["row"]["locus"]), []):
            if observation["scope"] != "historical":
                continue
            start, end = observation["start"], observation["end"]
            if record["derived"]:
                start, end = translate_range(start, end, record["alternatives"])
            if start < part["end"] and part["start"] < end:
                if not (part["start"] <= start < end <= part["end"]):
                    raise ValueError("A source reading crosses a frozen source-role boundary")
                observed = record["row"]["text"][start:end]
                allowed = set(observation["allowed_observed_readings"]) | {observation["original"]}
                if observed not in allowed:
                    raise ValueError("A fallback reading lacks occurrence-specific evidence: " +
                                     observation["id"] + " observed " + repr(observed))
                corrected = observation["corrected"]
                if any(char in observed + corrected for char in "\n\r|"):
                    raise ValueError("A spelling observation cannot change layout boundaries")
                edits.append({"start": piece["start"] + start - part["start"],
                    "end": piece["start"] + end - part["start"],
                    "original": observed, "corrected": corrected,
                    "observation": deepcopy(observation), "record_id": record["id"],
                    "source_row_char_range": [start, end], "derived": record["derived"]})
    edits.sort(key=lambda item: (item["start"], item["end"]))
    if any(left["end"] > right["start"] for left, right in zip(edits, edits[1:])):
        raise ValueError("Two source observations overlap in one literal witness")
    if not edits:
        return deepcopy(witness), [], [frozenset() for _ in witness["text"]]
    chunks, labels, cursor, length = [], [], 0, 0
    for edit in edits:
        a, b = edit["start"], edit["end"]
        if witness["text"][a:b] != edit["original"]:
            raise ValueError("Source reading no longer matches the exact lane preimage")
        unchanged = witness["text"][cursor:a]
        chunks.extend((unchanged, edit["corrected"]))
        labels.extend([frozenset()] * len(unchanged))
        labels.extend([frozenset({edit["observation"]["id"]})] * len(edit["corrected"]))
        length += len(unchanged)
        edit["corrected_range"] = [length, length + len(edit["corrected"])]
        length += len(edit["corrected"])
        cursor = b
    chunks.append(witness["text"][cursor:])
    labels.extend([frozenset()] * (len(witness["text"]) - cursor))
    patched = deepcopy(witness)
    patched["text"] = "".join(chunks)
    patched["source_artifact_sha256"] = witness["artifact_sha256"]
    patched["source_reading_edits"] = deepcopy(edits)
    patched["artifact_sha256"] = sha(encoded({"source": witness["artifact_sha256"], "edits": edits}))
    patched.pop("text_sha256", None)
    if len(labels) != len(patched["text"]):
        raise ValueError("Reading annotation lost corrected character positions")
    return patched, edits, labels


def routed_labels(labels, routing):
    if routing is None:
        return labels
    parts = {(part["line"], part["cell"]): part for part in routing["parts"]}
    output = []
    for index, reference in enumerate(routing["reading_order"]):
        if index:
            output.append(frozenset())
        part = parts[tuple(reference)]
        output.extend(labels[part["start"]:part["end"]])
    return output


def traced_tokens(text, labels):
    """Mirror the frozen tokenizer while carrying source occurrence identities."""
    if len(text) != len(labels):
        raise ValueError("Token evidence and routed text lengths differ")
    pattern = re.compile(r"([" + GREEK + r"])[-‐]\s*\n\s*([" + GREEK + r"])")
    chunks, traced, cursor = [], [], 0
    for match in pattern.finditer(text):
        chunks.extend((text[cursor:match.start()], match.group(1), match.group(2)))
        traced.extend(labels[cursor:match.start()])
        traced.extend((labels[match.start(1)], labels[match.start(2)]))
        cursor = match.end()
    chunks.append(text[cursor:]); traced.extend(labels[cursor:])
    normalized = "".join(chunks)
    result, index = [], 0
    while index < len(normalized):
        if not unicodedata.category(normalized[index]).startswith(("L", "M")):
            index += 1; continue
        start = index
        while index < len(normalized) and (unicodedata.category(normalized[index]).startswith(("L", "M"))
                                          or normalized[index] in APOSTROPHES):
            index += 1
        raw = normalized[start:index]
        if any(greek_letter(char) for char in raw):
            claims = sorted(set().union(*traced[start:index]))
            result.append((unicodedata.normalize("NFC", raw), claims))
    if [form for form, _ in result] != [form for form, _ in tokenize(text)]:
        raise ValueError("Source token tracing differs from the frozen tokenizer")
    return result


def render_network(result):
    """Render the frozen policy, with explicit source adjudications where present."""
    display, lexical, counts = [], [], Counter()
    for slot in result["ocr_consensus"]["slots"]:
        status, selected = slot["status"], slot["selected"]
        if status == "unresolved":
            display.append("⟦" + " ∥ ".join(word or "∅" for word in slot["tied_readings"]) + "⟧")
        elif status != "omission":
            reading = next(item for item in slot["readings"] if item["text"] == selected)
            surfaces = Counter(reading["surfaces"].values())
            maximum = max(surfaces.values())
            winners = sorted(text for text, count in surfaces.items() if count == maximum)
            display.append(winners[0] if len(winners) == 1 else "⟦" + " ∥ ".join(winners) + "⟧")
        if slot["lexical_eligible"]:
            lexical.append(selected)
        counts[status] += 1
    return {**result, "text": " ".join(display), "analysis_text": " ".join(lexical),
            "ocr_consensus": {**result["ocr_consensus"], "counts": dict(counts)}}


def adjudicate(result, traces, observations):
    """Name source-certified tokens without altering the original vote result."""
    if render_network(result) != result:
        raise ValueError("The source-review renderer differs from the frozen merge")
    result = deepcopy(result)
    cursors = Counter()
    touched = 0
    for slot in result["ocr_consensus"]["slots"]:
        certified = defaultdict(set)
        for reading in slot["readings"]:
            for identifier in reading["support"]:
                form, claims = traces[identifier][cursors[identifier]]
                cursors[identifier] += 1
                if form != reading["text"]:
                    raise ValueError("Source token order differs from merged witness support")
                if claims:
                    certified[form].update(claims)
        if not certified:
            continue
        if len(certified) != 1:
            raise ValueError("Source-certified readings conflict at one aligned position")
        form, claim_ids = next(iter(certified.items()))
        slot["pre_source_review"] = {key: deepcopy(slot[key]) for key in (
            "status", "vote_status", "selected", "tied_readings", "lexical_eligible", "lexical_exclusion")}
        slot["status"] = "source-reviewed"
        slot["vote_status_qualification"] = ("Frozen merger vote after the explicit source-reading "
            "observations and layout routing; the uncorrected network remains a separate authority.")
        slot["selected"] = form
        slot["source_review"] = {"observations": sorted(claim_ids),
            "claims": sorted({observations[name]["claim_id"] for name in claim_ids}),
            "contrary_original_readings": sorted({reading for name in claim_ids
                for reading in observations[name]["allowed_observed_readings"]}),
            "authority": AUDIT + "/changes.json"}
        # A source review of letters cannot complete a terminal page fragment.
        slot["lexical_eligible"] = lexical_eligible(form) and not slot["terminal_fragment_support"]
        slot["lexical_exclusion"] = ("source-page-end-fragment" if slot["terminal_fragment_support"]
                                     else None if lexical_eligible(form) else "mixed-script-token")
        touched += 1
    if any(cursors[name] != len(tokens) for name, tokens in traces.items()):
        raise ValueError("Merged network did not retain every source token")
    return render_network(result), touched


def _validate_observations(observations, records):
    literal = {(record["path"], record["row"]["locus"]): record for record in records if not record["derived"]}
    identifiers = set()
    for item in observations:
        if item["id"] in identifiers:
            raise ValueError("Repeated source occurrence identity")
        identifiers.add(item["id"])
        record = literal[(item["path"], item["locus"])]
        text = record["row"]["text"]
        if (sha(text.encode()) != item["row_sha256"] or record["sha256"] != item["input_sha256"]
                or record["group"] != item["group"] or record["toronto_page"] != item["toronto_page"]
                or text[item["start"]:item["end"]] != item["original"]
                or not 0 <= item["start"] < item["end"] <= len(text)):
            raise ValueError("A source occurrence no longer matches its literal original row")


def build(root, before, *, recorded_at, reviewed=None):
    root = Path(root)
    readings, layouts, _ = reviewed if reviewed is not None else evidence(root)
    records_list = base.source_records(root, base.archived_inputs(root))
    _validate_observations(readings["observations"], records_list)
    roles = base.partitions(records_list)
    records = {record["id"]: record for record in records_list}
    indexed, by_id = defaultdict(list), {}
    for item in readings["observations"]:
        indexed[(item["path"], item["locus"])].append(item)
        by_id[item["id"]] = item
    old_networks = json.loads(gzip.decompress((root / base.NETWORKS).read_bytes()))
    networks, changes, reviewed_ids = deepcopy(old_networks), [], set()
    changed_pages, reviewed_slots = set(), 0
    for key, old_result in old_networks.items():
        work = key.rsplit(":", 1)[0]
        witnesses, patches, routes, traces = [], [], [], {}
        decisions = layouts["decisions"].get(key, {})
        known = {w["id"] for w in old_result["ocr_consensus"]["witnesses"]}
        if set(decisions) - known:
            raise ValueError("A layout decision refers to a missing witness")
        for witness in old_result["ocr_consensus"]["witnesses"]:
            pieces = lane_pieces(witness, work, records, roles)
            patched, edits, labels = patch_witness(witness, pieces, indexed)
            routing = None
            if witness["id"] in decisions:
                patched, routing = route_witness(patched, key, decisions[witness["id"]])
                restore_witness(patched, routing)  # verify the exact inverse before admitting it
                routes.append(routing)
            if edits:
                patches.append({"witness_id": witness["id"], "vote_group": witness["vote_group"],
                    "original_witness": deepcopy(witness), "edits": edits,
                    "corrected_witness": deepcopy(routing["original_witness"] if routing else patched)})
                reviewed_ids.update(edit["observation"]["id"] for edit in edits)
            witnesses.append(patched)
            traces[witness["id"]] = traced_tokens(patched["text"], routed_labels(labels, routing))
        if not (patches or routes):
            continue
        vote_result = merge_witnesses(witnesses)
        expected_groups = {(w["id"], w["vote_group"]) for w in old_result["ocr_consensus"]["witnesses"]}
        if {(w["id"], w["vote_group"]) for w in vote_result["ocr_consensus"]["witnesses"]} != expected_groups:
            raise ValueError("Source review changed extraction identities or vote groups")
        result, count = adjudicate(vote_result, traces, by_id)
        reviewed_slots += count
        networks[key] = result
        changed_pages.add(key)
        changes.append({"page_key": key, "recorded_at": recorded_at,
            "original_network": {"path": base.NETWORKS, "key": key,
                "sha256": sha(encoded(old_result))}, "patches": patches, "routings": routes,
            "vote_result_before_source_adjudication": vote_result,
            "corrected_text": result["text"], "analysis_text": result["analysis_text"]})
    if set(layouts["decisions"]) - changed_pages:
        raise ValueError("An approved layout was not applied")
    outside = []
    for item in readings["observations"]:
        if item["id"] not in reviewed_ids:
            if item["scope"] == "historical":
                raise ValueError("A historical source observation has no admitted occurrence: " + item["id"])
            outside.append({**deepcopy(item), "recorded_at": recorded_at,
                "projection": "outside-primary-reading-overlay",
                "qualification": "The frozen editorial/heading witness remains literal; this overlay adds no lexical occurrence."})
    definitions = base.work_definitions()
    outputs, summaries = {}, {}
    for work, definition in definitions.items():
        slug = definition["slug"]
        name = f"data/corpus/{slug}.jsonl"
        if not any(key.rsplit(":", 1)[0] == work for key in old_networks):
            continue  # comparative definitions have no admitted primary
        raw = before.get(name, (root / name).read_bytes())
        rows = [json.loads(line) for line in raw.splitlines()]
        for row in rows:
            key = row["dubner_scope_review"]["network_key"]
            if key not in changed_pages:
                continue
            compact = compact_corpus_consensus(networks[key], {"path": NETWORKS, "key": key})
            row.update(compact)
            row["dubner_reading_review"] = {"authority": AUDIT + "/changes.json", "network_key": key}
            if any(slot["status"] == "source-reviewed" for slot in compact["ocr_consensus"]["slots"]):
                row["corrections"] = sorted(set(row.get("corrections", [])) | {"manual"})
        new_raw = jsonl(rows)
        if new_raw != raw:
            outputs[name] = new_raw
        counts = sum((Counter(row["ocr_consensus"]["counts"]) for row in rows), Counter())
        secondary = root / f"data/corpus_secondary/{slug}.jsonl"
        summaries[slug] = {"primary_rows": len(rows), "secondary_rows": len(secondary.read_bytes().splitlines()),
            "analysis_tokens": sum(len(base.GREEK.findall(row["analysis_text"])) for row in rows),
            "surface_tokens": sum(len(base.GREEK.findall(row["text"])) for row in rows), "counts": dict(counts)}
    assessment = diagnostics(networks)
    assessment.pop("candidates", None)
    assessment.update(qualification="Remaining aligned extraction disagreements; categories are not proof of OCR error. Omission ties, accent/case/elision-only ties, and different-word readings are mutually exclusive; the one-group diagnostic overlaps them.",
        approved_layouts=[{"page_key": key, "witnesses": deepcopy(decisions),
            "baseline_counts": old_networks[key]["ocr_consensus"]["counts"],
            "current_counts": networks[key]["ocr_consensus"]["counts"]}
            for key, decisions in sorted(layouts["decisions"].items())],
        held_layouts=layouts["held"], source_review_deferred=readings.get("deferred", []),
        review_scope="All ten delimiter-bearing candidate pages were inspected in both scans. Seven exact cell permutations exhaust the approved layout decisions; three partial duplicate-column cases have no admitted fragment decision.",
        reopening_circumstances=[
            "A source capture or occurrence anchor is invalidated; remove this layer by literal undo before replacing its authority.",
            "A new source review establishes exact fragment identities on a held partial-duplicate page; admit it in a separate reversible layer without another vote group.",
            "New occurrence-specific scan evidence resolves a remaining reading; preserve its contrary readings and original locus in a later review."])

    outputs.update({NETWORKS: gzip.compress(encoded(networks), mtime=0),
        RECORDS: gzip.compress(jsonl(changes), mtime=0),
        OUTSIDE: gzip.compress(jsonl(outside), mtime=0), ASSESSMENT: encoded(assessment)})
    statuses = sum((Counter(item["counts"]) for item in summaries.values()), Counter())
    old_statuses = sum((Counter(result["ocr_consensus"]["counts"]) for result in old_networks.values()), Counter())
    counts = {"works": len(summaries), "primary_rows": sum(item["primary_rows"] for item in summaries.values()),
        "changed_pages": len(changed_pages), "approved_layout_pages": len(layouts["decisions"]),
        "held_layout_pages": len(layouts["held"]), "source_observations": len(readings["observations"]),
        "primary_source_observations": len(reviewed_ids), "outside_primary_observations": len(outside),
        "source_reviewed_slots": reviewed_slots,
        "lane_occurrence_edits": sum(len(patch["edits"]) for change in changes for patch in change["patches"]),
        "analysis_tokens": sum(item["analysis_tokens"] for item in summaries.values()),
        "reading_statuses": dict(statuses), "baseline_reading_statuses": dict(old_statuses),
        "unresolved_reduction": old_statuses["unresolved"] - statuses["unresolved"],
        "remaining_unresolved_categories": assessment["unresolved_categories"]}
    return outputs, summaries, counts


def _archive(root):
    authority, archive = (Path(root) / AUDIT / name for name in ("changes.json", "before.json.gz"))
    if authority.is_file() != archive.is_file():
        raise ValueError("An orphaned Dübner reading authority or preimage cannot authorize changes")
    return authority, archive


def active(root=ROOT):
    authority, _ = _archive(root)
    if not authority.is_file():
        return False
    audit = json.loads(authority.read_bytes())
    before = archived_inputs(root)
    if set(before) != set(audit["outputs"]):
        raise ValueError("Dübner reading output and preimage inventories differ")
    return not all((local_path(root, name).read_bytes() if local_path(root, name).is_file() else None)
                   == before[name] for name in audit["outputs"])


def verify(root=ROOT, *, active_only=True, replay=False):
    root = Path(root)
    authority, archive = _archive(root)
    audit = json.loads(authority.read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("qualification") != QUALIFICATION):
        raise ValueError("Dübner reading recipe or qualification changed")
    if sha(archive.read_bytes()) != audit["before_sha256"]:
        raise ValueError("Dübner reading preimage archive changed")
    before = archived_inputs(root)
    if set(before) != set(audit["outputs"]):
        raise ValueError("Dübner reading preimage and output inventories differ")
    from dubner_layers import verify_scope
    scope, _ = verify_scope(root, replacements=before, replay=replay)
    if audit["scope_authority_sha256"] != sha((root / base.AUDIT / "changes.json").read_bytes()):
        raise ValueError("Dübner predecessor authority changed")
    reviewed = evidence(root)
    if audit["evidence_files"] != reviewed[2]:
        raise ValueError("Dübner reading source evidence inventory changed")
    for name, expected in audit["outputs"].items():
        actual = sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
        if active_only and actual != expected:
            raise ValueError("Dübner reading output changed: " + name)
        if name.startswith("data/corpus/"):
            if name not in scope["outputs"] or sha(before[name]) != scope["outputs"][name]:
                raise ValueError("Dübner reading predecessor is not a frozen primary postimage")
        elif not name.startswith(AUDIT + "/") or before[name] is not None:
            raise ValueError("Dübner reading layer claims an unowned destination")
    if replay:
        outputs, works, counts = build(root, before, recorded_at=audit["recorded_at"], reviewed=reviewed)
        if ({name: sha(raw) for name, raw in outputs.items()} != audit["outputs"]
                or works != audit["works"] or counts != audit["counts"]):
            raise ValueError("Dübner reading replay differs from its complete frozen audit")
    return audit, before


def _state_signature(root):
    """Inventory every authority, recipe, current output, and retained source image."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    scope = json.loads((root / base.AUDIT / "changes.json").read_bytes())
    capture = json.loads((root / base.AUDIT / "source-evidence.json").read_bytes())
    files = [AUDIT + "/changes.json", AUDIT + "/before.json.gz", *audit["outputs"],
             *audit["evidence_files"], base.AUDIT + "/changes.json", base.AUDIT + "/before.json.gz",
             *scope["outputs"], base.AUDIT + "/source-evidence.json",
             *("scripts/" + name for name in recipe_pins()),
             *("scripts/" + name for name in base.recipe_pins()),
             *(item["path"] for item in capture["files"])]
    recipe_paths = {"scripts/" + name for name in (*recipe_pins(), *base.recipe_pins())}
    signature = []
    for name in sorted(set(files)):
        path = root / name if name in recipe_paths else local_path(root, name)
        if path.is_file():
            stat = path.stat()
            signature.append((name, stat.st_size, stat.st_mtime_ns))
        else:
            signature.append((name, None, None))
    return tuple(signature)


@lru_cache(maxsize=2)
def _checked_state(root, signature):
    return verify(root, replay=True)


def checked_state(root=ROOT):
    """Replay once per complete dependency state; never expose mutable cached data."""
    root = str(Path(root))
    return deepcopy(_checked_state(root, _state_signature(root)))


@lru_cache(maxsize=2)
def _verified_rows(root, signature):
    _checked_state(root, signature)
    rows = {}
    scope = json.loads((Path(root) / base.AUDIT / "changes.json").read_bytes())
    for name in scope["outputs"]:
        if name.startswith("data/corpus/") and scope["outputs"][name] is not None:
            for row in map(json.loads, (Path(root) / name).read_bytes().splitlines()):
                rows[(row["urn"], row["locus"])] = row
    return rows


def validate_projection(row, root=ROOT):
    root = str(Path(root))
    if _verified_rows(root, _state_signature(root)).get((row["urn"], row["locus"])) != row:
        raise ValueError("Dübner reading projection differs from its checked admission")
    return row["analysis_text"]


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    authority, archive = _archive(root)
    old = None
    if authority.is_file():
        if active(root):
            raise ValueError("The Dübner reading layer is already active")
        old, before = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Reapplying a frozen reading audit cannot change its timestamp")
        recorded_at = old["recorded_at"]
        for name in old["outputs"]:
            current = local_path(root, name).read_bytes() if local_path(root, name).is_file() else None
            if current != before[name]:
                raise ValueError("Reapply found a later Dübner reading change: " + name)
    else:
        from dubner_layers import verify_scope
        scope, _ = verify_scope(root, replacements={})
        before = {name: local_path(root, name).read_bytes() for name, expected in scope["outputs"].items()
                  if name.startswith("data/corpus/") and expected is not None}
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    reviewed = evidence(root)
    outputs, works, counts = build(root, before, recorded_at=recorded_at, reviewed=reviewed)
    preimages = {}
    for name in outputs:
        if name in before:
            preimages[name] = before[name]
        else:
            if local_path(root, name).exists():
                raise ValueError("Refusing to overwrite an unowned reading destination: " + name)
            preimages[name] = None
    before_raw = gzip.compress(encoded({name: None if raw is None else raw.decode()
        for name, raw in preimages.items()}), mtime=0)
    audit = {"schema_version": 1, "recorded_at": recorded_at,
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/105",
        "scope_authority_sha256": sha((root / base.AUDIT / "changes.json").read_bytes()),
        "recipe_sha256": recipe_pins(), "before_sha256": sha(before_raw),
        "evidence_files": reviewed[2], "outputs": {name: sha(raw) for name, raw in outputs.items()},
        "works": works, "counts": counts, "qualification": QUALIFICATION}
    if old is not None and encoded(audit) != authority.read_bytes():
        raise ValueError("Reapply must reproduce the complete frozen reading audit")
    publish(root, {**outputs, AUDIT + "/before.json.gz": before_raw, AUDIT + "/changes.json": encoded(audit)})
    return audit


def undo(root=ROOT):
    """Restore exact predecessor bytes even after evidence or a recipe is invalidated."""
    root = Path(root)
    authority, archive = _archive(root)
    audit = json.loads(authority.read_bytes())
    if sha(archive.read_bytes()) != audit["before_sha256"]:
        raise ValueError("Dübner reading undo archive changed")
    before = archived_inputs(root)
    if set(before) != set(audit["outputs"]):
        raise ValueError("Dübner reading undo inventory changed")
    for name, expected in audit["outputs"].items():
        actual = sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
        if actual != expected:
            raise ValueError("Refusing to overwrite a later reading output: " + name)
    publish(root, before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--undo", action="store_true")
    parser.add_argument("--recorded-at")
    args = parser.parse_args()
    if args.undo:
        undo(args.root)
        print("Exact frozen scope postimages restored")
    else:
        audit = apply(args.root, recorded_at=args.recorded_at) if args.apply else verify(args.root, replay=True)[0]
        print(json.dumps(audit["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
