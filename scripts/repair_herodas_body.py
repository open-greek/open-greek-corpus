#!/usr/bin/env python3
"""Recover source-disjoint Herodas body pages with retained OCR alternatives.

The published excerpt and its citation identities remain literal. All additions,
source-role cuts, votes, critical exclusions, and the complete preimage replay
from retained inputs. Undo needs no surviving comparison source.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import difflib
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
WORK = "herodas.mimiambi"
PRIMARY = f"data/corpus/{WORK}.jsonl"
CORE = {PRIMARY}
AUDIT = "data/corpus_changes/herodas-headlam-knox-body"
INPUT_SHA256 = "b50c5d810cac0a8a44a2acdd567aa1c7f7e7266e83698325122501b0656e68ef"
SCAN_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
SOURCE_FILES = {"data/corpus_changes/editorial-role-review/source-herodas.pdf": SCAN_SHA256}
SOURCE_URL = "https://archive.org/details/mimesfragments00hero"
QUALIFICATION = (
    "Source-page recovery of the admitted Headlam–Knox 1922 Herodas body. The "
    "62 published excerpt passages retain their exact readings and identities. "
    "New pages retain the merged usable Qwen3.6 and Qwen3.8 recognition witnesses "
    "and layer named scan-backed reading decisions above them. Unresolved source "
    "readings remain explicit. Only source-confirmed complete, unmarked readings "
    "enter new scalar lexical counts. This is not comprehensive proofreading of the "
    "old excerpt, a critical edition, or a claim to every surviving Herodas fragment."
)
ANALYSIS_GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def compressed(value):
    return gzip.compress(encoded(value), mtime=0)


def _replace_bytes(path, raw):
    """Replace one public file atomically; failed writes retain its preimage."""
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def recipe_pins():
    names = ("repair_herodas_body.py", "herodas_body_source_observations.py",
        "herodas_body_witnesses.py", "herodas_body_witness_observations.py",
        "herodas_body_readings_a.py", "herodas_body_readings_b.py", "herodas_body_readings_c.py",
        "prepare_herodas_body.py", "run_scan_ocr.py", "ocr_consensus.py", "scan_ocr_bundle.py")
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in names}


def authority_paths(root):
    return tuple(sorted({*CORE, *SOURCE_FILES,
        *(path.relative_to(root).as_posix() for path in (Path(root) / AUDIT).glob("*") if path.is_file()),
        *("scripts/" + name for name in recipe_pins())}))


def parse_original(raw):
    if sha(raw) != INPUT_SHA256:
        raise ValueError("Herodas body recovery needs the exact published 62-row excerpt")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 62 or len({row["locus"] for row in rows}) != 62 or any(row["urn"] != WORK for row in rows):
        raise ValueError("Published Herodas excerpt identities changed")
    return rows


def page_number(row):
    match = re.fullmatch(r"herodas_hk_([0-9]{4})\.[0-9]+", row["locus"])
    if not match:
        raise ValueError("Unexpected Herodas physical citation")
    return int(match[1])


def _word_ranges(text):
    """Use the vote tokenizer's exact lexical units with original character offsets."""
    from ocr_consensus import APOSTROPHES, greek_letter, tokenize
    result = []
    index = 0
    while index < len(text):
        if not unicodedata.category(text[index]).startswith(("L", "M")):
            index += 1
            continue
        start = index
        while index < len(text) and (unicodedata.category(text[index]).startswith(("L", "M"))
                                      or text[index] in APOSTROPHES):
            index += 1
        word = text[start:index]
        if any(greek_letter(char) for char in word):
            result.append((unicodedata.normalize("NFC", word), start, index))
    if [word for word, _, _ in result] != [word for word, _ in tokenize(text)]:
        raise ValueError("A printed word continuation needs an explicit source decision")
    return result


def _critical_flags(text, ranges, initial_brackets=None):
    """Conservative supplies, damaged letters, and source-gap boundaries."""
    pairs = {"[": "]", "<": ">", "⟨": "⟩", "(": ")"}
    closes = set(pairs.values())
    marked = set()
    stack = list(initial_brackets or [])
    if any(char not in closes for char in stack):
        raise ValueError("Unknown initial critical bracket state")
    obelized = False
    # A closing bracket before any opener can continue a preceding page's supply.
    first = next((char for char in text if char in pairs or char in closes), None)
    if initial_brackets is None and first in closes:
        stack = [first]
    for index, char in enumerate(text):
        if char == "†":
            obelized = not obelized
            marked.add(index)
        if char in pairs:
            stack.append(pairs[char])
        if stack or obelized or char in closes or char == "\u0323":
            marked.add(index)
        if char in closes and stack:
            if char == stack[-1]:
                stack.pop()
            else:
                marked.update(range(len(text)))
    flags = []
    for _, start, end in ranges:
        reasons = []
        if any(index in marked for index in range(start, end)):
            reasons.append("printed-supply-or-unclear-reading")
        if (start and text[start - 1] in closes | {"†"}
                or end < len(text) and text[end] in set(pairs) | {"†"}
                or "\u0323" in text[start:end]):
            reasons.append("printed-word-fragment")
        before, after = text[:start].rstrip(), text[end:].lstrip()
        if re.search(r"(?:\.{2,}|…)$", before) or re.match(r"(?:\.{2,}|…)", after):
            reasons.append("source-gap-boundary")
        flags.append(reasons)
    return flags


def _fresh_projection(text, speaker_labels, recognition_labels=None, recognition_sha256=None):
    """Retain exact crop text; only source-identified names are speaker candidates."""
    from ocr_consensus import greek_letter
    from ocr_consensus import alignment_key
    labels = {alignment_key(label) for label in speaker_labels}
    aliases = recognition_labels or {}
    if aliases and (recognition_sha256 != sha(text.encode())
            or any(value not in speaker_labels for value in aliases.values())):
        raise ValueError("Observed Herodas speaker aliases changed their raw prediction or printed role")
    spans, position = [], 0
    for line in text.splitlines(keepends=True):
        letters = [char for char in line if char.isalpha()]
        capitals = bool(letters) and all(char.isupper() for char in letters)
        observed = line.strip()
        speaker = capitals and (alignment_key("".join(letters)) in labels or observed in aliases)
        if capitals and not speaker:
            raise ValueError("Unreviewed capitalized Herodas line needs an occurrence-specific source role: " + line.strip())
        role = "speaker" if speaker else "authorial"
        spans.append({"start": position, "end": position + len(line), "text": line,
            "role": role, "evidence": "Reviewed body crop; separately printed capitalized speaker label." if speaker
                else "Within the scan-reviewed Greek verse crop."})
        position += len(line)
    return {"spans": spans, "authorial_spans": [part for part in spans if part["role"] == "authorial"],
        "excluded_spans": [dict(part, reason="Printed speaker name, not spoken verse")
                           for part in spans if part["role"] != "authorial"]}


def _body_text(projection):
    return "\n".join(part["text"].strip("\n") for part in projection["authorial_spans"])


def _display_slot(slot):
    if slot["selected"] is None:
        return "⟦" + " ∥ ".join(reading or "∅" for reading in slot["tied_readings"]) + "⟧"
    if slot["selected"] == "":
        return ""
    readings = next(reading for reading in slot["readings"] if reading["text"] == slot["selected"])
    surfaces = Counter(readings["surfaces"].values())
    best = max(surfaces.values())
    values = sorted(surface for surface, count in surfaces.items() if count == best)
    return values[0] if len(values) == 1 else "⟦" + " ∥ ".join(values) + "⟧"


def merge_page(number, historical, fresh, spec, reading_review):
    from herodas_body_witness_observations import project_qwen36
    from ocr_consensus import merge_witnesses
    raw36 = historical["qwen36"]["files"]["grc"]["text"]
    projections = {"qwen36": project_qwen36(number, raw36),
                   "qwen38": _fresh_projection(fresh["raw_prediction"], reading_review.get("speaker_labels", []),
                        reading_review.get("recognition_labels"), reading_review.get("recognition_sha256"))}
    witnesses, flags, ranges, texts = [], {}, {}, {}
    for identifier, raw in (("qwen36", raw36), ("qwen38", fresh["raw_prediction"])):
        body = _body_text(projections[identifier])
        if not body.strip():
            continue
        texts[identifier] = body
        ranges[identifier] = _word_ranges(body)
        flags[identifier] = _critical_flags(body, ranges[identifier])
        witnesses.append({"id": identifier, "text": body,
            "artifact_sha256": sha(encoded({"recognizer": identifier, "scan_page": number,
                "raw_prediction": raw})), "raw_text_sha256": sha(raw.encode()), "scan_page": number,
            "source_review": f"{AUDIT}/records.json.gz",
            "raw_archive": f"{AUDIT}/" + ("historical-witnesses.json.gz" if identifier == "qwen36" else "fresh-predictions.jsonl")})
    result = merge_witnesses(witnesses)
    positions = Counter()
    output, lexical, slot_records, gaps = [], [], [], []
    fresh_cursor = 0
    for slot in result["ocr_consensus"]["slots"]:
        source_flags = []
        for reading in slot["readings"]:
            for identifier in reading["support"]:
                index = positions[identifier]
                source_flags.extend(flags[identifier][index])
                if identifier == "qwen38":
                    _, start, end = ranges[identifier][index]
                    gap = texts[identifier][fresh_cursor:start]
                    if re.search(r"\.{2,}|…", gap):
                        output.append(gap.strip())
                        gaps.append({"slot": slot["position"], "text": gap,
                                     "evidence": "Retained recognition of a printed body lacuna; scan crop archived."})
                    fresh_cursor = end
                positions[identifier] += 1
        if slot["lexical_eligible"] and (slot["vote_status"] != "agreement" or source_flags):
            slot["lexical_eligible"] = False
            slot["lexical_exclusion"] = ";".join(sorted(set(source_flags))) or "unconfirmed-single-recognition"
        piece = _display_slot(slot)
        if piece:
            output.append(piece)
        if slot["lexical_eligible"]:
            lexical.append(slot["selected"])
        slot_records.append(slot)
    for identifier in texts:
        if positions[identifier] != len(ranges[identifier]):
            raise ValueError("Herodas vote lost a source token")
    tail = texts.get("qwen38", "")[fresh_cursor:]
    if re.search(r"\.{2,}|…", tail):
        output.append(tail.strip())
        gaps.append({"slot": len(slot_records), "text": tail,
                     "evidence": "Retained terminal source-gap recognition."})
    result["text"] = " ".join(output)
    result["analysis_text"] = " ".join(lexical)
    result["ocr_consensus"]["counts"] = dict(Counter(slot["status"] for slot in slot_records))
    result["ocr_consensus"]["policy"] += " New lexical counts require two agreeing usable recognizers and exclude printed supplies, unclear letters, and source-gap boundaries."
    result["source_gaps"] = gaps
    result["physical_refs"] = {"scan_page": number, "printed_page": number - 70,
        "mime": spec.get("mime"), "verses": spec.get("verses"), "region": spec["region"]}
    return result, projections


def source_readings():
    from herodas_body_readings_a import READINGS as a
    from herodas_body_readings_b import READINGS as b
    from herodas_body_readings_c import READINGS as c
    if set(a) & set(b) or set(a) & set(c) or set(b) & set(c):
        raise ValueError("Herodas reading reviews repeat a source page")
    return {**deepcopy(a), **deepcopy(b), **deepcopy(c)}


def literal_edits(original, corrected, review, number, identifier):
    """Record each literal edit; both directions reconstruct the complete text."""
    edits = []
    for kind, left, right, start, end in difflib.SequenceMatcher(None, original, corrected, autojunk=False).get_opcodes():
        if kind == "equal":
            continue
        edits.append({"witness": identifier, "original_char_range": [left, right],
            "corrected_char_range": [start, end], "original_text": original[left:right],
            "corrected_text": corrected[start:end], "source": SOURCE_URL,
            "source_pdf_sha256": SCAN_SHA256, "scan_page": number,
            "evidence": review["evidence"], "reviewed_at": review["reviewed_at"]})
    for text, source_key, replacement_key, expected in (
        (original, "original_char_range", "corrected_text", corrected),
        (corrected, "corrected_char_range", "original_text", original)):
        pieces, cursor = [], 0
        for edit in edits:
            start, end = edit[source_key]
            pieces.extend([text[cursor:start], edit[replacement_key]])
            cursor = end
        pieces.append(text[cursor:])
        if "".join(pieces) != expected:
            raise ValueError("A Herodas reading correction is not literally reversible")
    return edits


def apply_scan_review(raw_vote, review, number, spec):
    """Named source decisions above unchanged votes, never an extra recognizer."""
    from ocr_consensus import compact_corpus_consensus, lexical_eligible
    text = review["text"]
    if (not isinstance(text, str) or not text.strip() or not review.get("evidence")
            or datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00")).tzinfo is None):
        raise ValueError("Herodas reading decision needs literal text, source evidence, and zoned time")
    if (review.get("source_sha256", SCAN_SHA256) != SCAN_SHA256
            or review.get("scan_page", number) != number
            or review.get("region", spec["region"]) != spec["region"]):
        raise ValueError("Herodas reading decision changed its source or physical crop")
    ranges = _word_ranges(text)
    initial = review.get("initial_brackets")
    if initial is not None and (not isinstance(initial, list) or not review.get("initial_brackets_evidence")):
        raise ValueError("A continued Herodas critical bracket requires explicit source evidence")
    flags = _critical_flags(text, ranges, initial)
    uncertainties = review.get("uncertainties", [])
    for entry in uncertainties:
        start, end = entry["start"], entry["end"]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                or not entry.get("evidence") or not isinstance(entry.get("alternatives"), list)
                or any(not isinstance(value, str) for value in entry["alternatives"])
                or "text" in entry and entry["text"] != text[start:end]):
            raise ValueError("Unresolved Herodas reading lacks exact source bounds and alternatives")
        for index, (_, left, right) in enumerate(ranges):
            if left < end and start < right:
                flags[index].append("unresolved-source-reading")
    corrected = deepcopy(raw_vote)
    slots = []
    for index, ((word, start, end), reasons) in enumerate(zip(ranges, flags, strict=True)):
        eligible = not reasons and lexical_eligible(word)
        slots.append({"position": index, "selected": word, "status": "scan-reviewed" if eligible else "source-marked-reading",
            "lexical_eligible": eligible, "lexical_exclusion": ";".join(sorted(set(reasons))) or (None if eligible else "mixed-script-token"),
            "tied_readings": [], "readings": [], "vote_status": "source-adjudication",
            "scan_review": {"start": start, "end": end, "original_surface": text[start:end],
                "source_pdf_sha256": SCAN_SHA256, "scan_page": number, "region": spec["region"],
                "source_review": f"{AUDIT}/source-readings.json", "reviewed_at": review["reviewed_at"]}})
    key = f"herodas_hk_{number:04d}.1:raw"
    reference = compact_corpus_consensus(raw_vote, {"path": f"{AUDIT}/records.json.gz", "key": key})["ocr_consensus"]["full_network"]
    correction = {"generator": "scripts/repair_herodas_body.py", "source_kind": "manual-scan-review",
        "original_text": raw_vote["text"], "corrected_text": text,
        "original_analysis_text": raw_vote["analysis_text"],
        "corrected_analysis_text": " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"]),
        "source": SOURCE_URL, "source_pdf_sha256": SCAN_SHA256, "scan_page": number,
        "region": spec["region"], "evidence": review["evidence"], "reviewed_at": review["reviewed_at"],
        "raw_network": reference, "source_review_sha256": sha(encoded(review)),
        "policy": "Source-bounded reading above unchanged OCR alternatives; no artificial extra recognition vote.",
        "witness_edits": [edit for witness in raw_vote["ocr_consensus"]["witnesses"]
            for edit in literal_edits(witness["text"], text, review, number, witness["id"])],
        "reversal": {"function": "scripts.repair_herodas_body.unapply_scan_review", "raw_network_key": key}}
    corrected["text"] = text
    corrected["analysis_text"] = correction["corrected_analysis_text"]
    corrected["source_uncertainties"] = deepcopy(uncertainties)
    corrected["ocr_consensus"].update(slots=slots,
        counts=dict(Counter(slot["status"] for slot in slots)), raw_ocr_network=reference,
        reviewed_corrections=[correction])
    corrected["ocr_consensus"]["policy"] += " Named scan reading decisions preserve the printed text and critical marks above the archived diagnostic vote."
    return corrected, correction


def unapply_scan_review(result, raw_result):
    from ocr_consensus import compact_corpus_consensus
    reference = result["ocr_consensus"]["raw_ocr_network"]
    actual = compact_corpus_consensus(raw_result, {"path": reference["path"], "key": reference["key"]})["ocr_consensus"]["full_network"]
    if actual != reference:
        raise ValueError("Herodas source reading lost its exact pre-review vote")
    return deepcopy(raw_result)


def _fresh_rows(raw, request_raw):
    from scan_ocr_bundle import inspect_leaf
    meta, rows = inspect_leaf(raw, request_raw)
    if (meta["model"] != "mlx-community/Qwen3.8-27B-8bit"
            or meta["revision"] != "815b83c0df8ffd1d1b5244cf75fd6ef14fca9ef9"
            or meta["runner_sha256"] != sha((Path(__file__).parent / "run_scan_ocr.py").read_bytes())):
        raise ValueError("Herodas fresh recognition checkpoint changed")
    if any(row.get("finish_reason") != "stop" or not row.get("raw_prediction", "").strip() for row in rows.values()):
        raise ValueError("Failed or truncated Herodas recognition cannot enter the body")
    return rows


def build_outputs(before, packet, request_raw, predictions_raw, reviewed_at):
    from herodas_body_source_observations import BODY_PAGES
    from herodas_body_witnesses import validate_packet
    from ocr_consensus import compact_corpus_consensus
    from prepare_herodas_body import build_manifest
    validate_packet(packet)
    if datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("Herodas recovery time needs a time zone")
    original = parse_original(before[PRIMARY].encode())
    present = {page_number(row) for row in original}
    missing = [page for page in BODY_PAGES if page["scan_page"] not in present]
    if json.loads(request_raw) != build_manifest(missing):
        raise ValueError("Herodas OCR request differs from the complete missing-body inventory")
    fresh = _fresh_rows(predictions_raw, request_raw)
    expected = {f"herodas-hk-body-{page['scan_page']:04d}" for page in missing}
    if set(fresh) != expected or set(packet["pages"]) != {str(page["scan_page"]) for page in missing}:
        raise ValueError("Herodas recovery does not account for every missing source page")
    records, added = [], []
    readings = source_readings()
    if set(readings) != {page["scan_page"] for page in missing}:
        raise ValueError("Herodas scan reading review does not cover exactly the missing body pages")
    for spec in missing:
        number = spec["scan_page"]
        raw_vote, projections = merge_page(number, packet["pages"][str(number)], fresh[f"herodas-hk-body-{number:04d}"], spec, readings[number])
        vote, correction = apply_scan_review(raw_vote, readings[number], number, spec)
        locus = f"herodas_hk_{number:04d}.1"
        compact = compact_corpus_consensus(vote, {"path": f"{AUDIT}/records.json.gz", "key": locus})
        row = {"urn": WORK, "edition": "herodas-hk-ocr", "source": "ocr", "license": "PD",
            "locus": locus, **compact, "herodas_body_recovery": {"schema_version": 1,
                "authority": f"{AUDIT}/changes.json", "scan_sha256": SCAN_SHA256,
                "reviewed_at": reviewed_at}}
        added.append(row)
        records.append({"locus": locus, "original_text": None, "corrected_text": row["text"],
            "original_row": None, "corrected_row": row, "full_vote": vote, "raw_vote": raw_vote,
            "source_correction": correction,
            "source_projections": projections, "source": SOURCE_URL, "scan_sha256": SCAN_SHA256,
            "scan_page": number, "region": spec["region"], "reviewed_at": reviewed_at,
            "evidence": "Source-reviewed authorial page and crop; all usable independent recognition readings retained in the word vote."})
    rows = sorted(original + added, key=lambda row: (page_number(row), int(row["locus"].rsplit(".", 1)[1])))
    if len({row["locus"] for row in rows}) != len(rows):
        raise ValueError("Recovered Herodas identities collide with historical citations")
    if any(next(row for row in rows if row["locus"] == old["locus"]) != old for old in original):
        raise ValueError("Herodas recovery changed a published excerpt reading")
    original_tokens = sum(len(ANALYSIS_GREEK.findall(row.get("analysis_text", row["text"]))) for row in original)
    recovered_tokens = sum(len(ANALYSIS_GREEK.findall(row["analysis_text"])) for row in added)
    counts = {"original_passages": len(original), "original_body_pages": len(present),
        "recovered_passages": len(added), "primary_passages": len(rows), "body_pages": len(BODY_PAGES),
        "original_analysis_tokens": original_tokens, "recovered_analysis_tokens": recovered_tokens,
        "primary_analysis_tokens": original_tokens + recovered_tokens,
        "raw_ocr_unresolved_slots": sum(slot["status"] == "unresolved" for record in records for slot in record["raw_vote"]["ocr_consensus"]["slots"]),
        "unresolved_slots": sum("unresolved-source-reading" in (slot.get("lexical_exclusion") or "")
            for record in records for slot in record["full_vote"]["ocr_consensus"]["slots"]),
        "new_noncountable_slots": sum(not slot["lexical_eligible"] for record in records for slot in record["full_vote"]["ocr_consensus"]["slots"])}
    return {PRIMARY: jsonl(rows)}, records, counts


@lru_cache(maxsize=4)
def _rendered_image_pins(source_pdf, source_sha256, request_raw):
    import pymupdf
    document = pymupdf.open(source_pdf)
    pins = {}
    for spec in json.loads(request_raw)["pages"]:
        page = document[spec["scan_page"] - 1]
        rect = page.rect
        left, top, right, bottom = spec["region"]
        clip = pymupdf.Rect(left * rect.width, top * rect.height, right * rect.width, bottom * rect.height)
        scale = spec["max_side"] / max(clip.width, clip.height)
        pins[spec["id"]] = sha(page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False).tobytes("png"))
    document.close()
    return pins


def _verify_prediction_images(root, request_raw, prediction_raw):
    fresh = _fresh_rows(prediction_raw, request_raw)
    actual = _rendered_image_pins(str(Path(root) / next(iter(SOURCE_FILES))), SCAN_SHA256, request_raw)
    if any(identifier not in actual or row["image_sha256"] != actual[identifier] for identifier, row in fresh.items()):
        raise ValueError("Herodas recognition image differs from the pinned scan crop")


@lru_cache(maxsize=4)
def _replayed_outputs(before_raw, packet_raw, request_raw, prediction_raw, reviewed_at, recipe_digest):
    """Cache only complete immutable input bytes after their authority checks."""
    before = json.loads(gzip.decompress(before_raw))
    packet = json.loads(gzip.decompress(packet_raw))
    outputs, records, counts = build_outputs(before, packet, request_raw, prediction_raw, reviewed_at)
    return tuple(sorted(outputs.items())), encoded(records), encoded(counts)


def _before(root, audit):
    path = f"{AUDIT}/before.json.gz"
    raw = (Path(root) / path).read_bytes()
    if sha(raw) != audit["outputs"][path]:
        raise ValueError("Herodas literal preimage archive changed")
    before = json.loads(gzip.decompress(raw))
    if (set(before) != CORE or audit["inputs"] != {PRIMARY: INPUT_SHA256}
            or sha(before[PRIMARY].encode()) != INPUT_SHA256):
        raise ValueError("Herodas recovery literal predecessor changed")
    return before


def verify(root, *, active=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("qualification") != QUALIFICATION
            or audit.get("recipe_sha256") != recipe_pins() or audit.get("sources") != SOURCE_FILES):
        raise ValueError("Herodas body recovery authority or recipe changed")
    before = _before(root, audit)
    required = {*CORE, *(f"{AUDIT}/{name}" for name in (
        "before.json.gz", "historical-witnesses.json.gz", "request.json", "fresh-predictions.jsonl",
        "source-readings.json", "source-inventory.json", "records.json.gz"))}
    if set(audit["outputs"]) != required:
        raise ValueError("Herodas recovery output authority changed")
    for relative, digest in {**SOURCE_FILES, **audit["outputs"]}.items():
        if not active and relative in CORE:
            continue
        if sha((root / relative).read_bytes()) != digest:
            raise ValueError("Herodas recovery source or output changed: " + relative)
    from herodas_body_source_observations import build_inventory
    if ((root / AUDIT / "source-readings.json").read_bytes() != encoded(source_readings())
            or (root / AUDIT / "source-inventory.json").read_bytes() != encoded(build_inventory())):
        raise ValueError("Herodas source review document differs from its generating observations")
    request_raw = (root / AUDIT / "request.json").read_bytes()
    prediction_raw = (root / AUDIT / "fresh-predictions.jsonl").read_bytes()
    _verify_prediction_images(root, request_raw, prediction_raw)
    replay, records_raw, counts_raw = _replayed_outputs((root / AUDIT / "before.json.gz").read_bytes(),
        (root / AUDIT / "historical-witnesses.json.gz").read_bytes(), request_raw, prediction_raw,
        audit["recorded_at"], sha(encoded(audit["recipe_sha256"])))
    outputs = dict(replay)
    if records_raw != gzip.decompress((root / AUDIT / "records.json.gz").read_bytes()) or counts_raw != encoded(audit["counts"]):
        raise ValueError("Herodas body records do not replay their source decisions")
    if any(sha(raw) != audit["outputs"][path] or active and (root / path).read_bytes() != raw for path, raw in outputs.items()):
        raise ValueError("Herodas body literal output differs from its source replay")
    return audit, before, outputs


@lru_cache(maxsize=4)
def _active_rows(root, signature):
    _, _, outputs = verify(root)
    return {row["locus"]: row for row in map(json.loads, outputs[PRIMARY].splitlines())}


def lexical_segments(row, root=None):
    root = Path(ROOT if root is None else root)
    signature = tuple((path, sha((root / path).read_bytes())) for path in authority_paths(root))
    actual = _active_rows(str(root), signature).get(row["locus"])
    if actual != row or not row.get("herodas_body_recovery"):
        raise ValueError("Herodas lexical row differs from its checked recovery")
    # Supplies, uncertain words, and speaker cuts supply no invented adjacency.
    return []


def manifestation_metadata(root):
    root = Path(root)
    if not (root / AUDIT / "changes.json").exists():
        return {}
    from herodas_current_state import body_is_unapplied
    if body_is_unapplied(root):
        return {}
    audit, _, _ = verify(root)
    counts = audit["counts"]
    return {WORK: {"editions": [{"key": "herodas-hk-ocr",
        "name": "Headlam–Knox 1922, inventoried Herodas body with retained recognition alternatives",
        "editor": "Headlam, Walter; Knox, Alfred", "year": 1922, "license": "PD", "provider": "ocr",
        "source": SOURCE_URL, "note": QUALIFICATION, "scheme": "scan-page.row", "storage": "primary", "servable": True}],
        "default_edition": "herodas-hk-ocr", "coverage_composition": {
            "policy": "source-reviewed-body-recovery", "manifest": f"{AUDIT}/changes.json",
            "manifest_sha256": sha((root / AUDIT / "changes.json").read_bytes()),
            "qualification": QUALIFICATION, "counts": counts,
            "primary_quality": {"status": "source-role-reviewed-with-unresolved-recognition",
                "passages": counts["primary_passages"], "note": QUALIFICATION},
            "components": [{"edition": "herodas-hk-ocr", "storage": "primary", "path": PRIMARY,
                "passages": counts["primary_passages"], "role": "authorial-verse", "license": "PD", "source": SOURCE_URL}]}}}


def undo(root):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    before = _before(root, audit)
    raw = (root / PRIMARY).read_bytes()
    if sha(raw) == INPUT_SHA256:
        return
    if sha(raw) != audit["outputs"][PRIMARY]:
        raise ValueError("Cannot undo a modified Herodas recovery output")
    _replace_bytes(root / PRIMARY, before[PRIMARY].encode())


def run(root, mode, *, witnesses=None, request=None, predictions=None, reviewed_at=None):
    root = Path(root)
    target = root / AUDIT
    if (target / "changes.json").exists():
        if mode == "undo":
            undo(root)
            return
        audit = json.loads((target / "changes.json").read_bytes())
        from herodas_current_state import body_is_unapplied
        restored = body_is_unapplied(root)
        audit, _, outputs = verify(root, active=not restored)
        if restored and mode == "apply":
            if sha((root / PRIMARY).read_bytes()) != INPUT_SHA256:
                raise ValueError("Reapply the earlier Herodas source-role repair before body recovery")
            for path, raw in outputs.items():
                _replace_bytes(root / path, raw)
        print(json.dumps(audit["counts"], sort_keys=True))
        return
    if mode != "apply" or any(path is None for path in (witnesses, request, predictions)):
        raise ValueError("Initial Herodas recovery needs retained witnesses, request, and predictions")
    from herodas_body_witnesses import validate_packet
    before = {PRIMARY: (root / PRIMARY).read_text()}
    parse_original(before[PRIMARY].encode())
    for path, digest in SOURCE_FILES.items():
        if sha((root / path).read_bytes()) != digest:
            raise ValueError("Pinned Herodas scan changed")
    reviewed_at = reviewed_at or datetime.now(timezone.utc).isoformat()
    if datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("Herodas review time needs a time zone")
    packet_raw = Path(witnesses).read_bytes()
    packet = json.loads(gzip.decompress(packet_raw))
    validate_packet(packet)
    request_raw, prediction_raw = Path(request).read_bytes(), Path(predictions).read_bytes()
    pins = recipe_pins()
    _verify_prediction_images(root, request_raw, prediction_raw)
    replay, records_raw, counts_raw = _replayed_outputs(compressed(before), packet_raw,
        request_raw, prediction_raw, reviewed_at, sha(encoded(pins)))
    outputs, counts = dict(replay), json.loads(counts_raw)
    from herodas_body_source_observations import build_inventory
    payloads = {f"{AUDIT}/before.json.gz": compressed(before),
        f"{AUDIT}/historical-witnesses.json.gz": packet_raw,
        f"{AUDIT}/request.json": request_raw, f"{AUDIT}/fresh-predictions.jsonl": prediction_raw,
        f"{AUDIT}/source-readings.json": encoded(source_readings()),
        f"{AUDIT}/source-inventory.json": encoded(build_inventory()),
        f"{AUDIT}/records.json.gz": gzip.compress(records_raw, mtime=0), **outputs}
    audit = {"schema_version": 1, "recorded_at": reviewed_at, "qualification": QUALIFICATION,
        "inputs": {PRIMARY: INPUT_SHA256}, "sources": SOURCE_FILES, "recipe_sha256": pins,
        "outputs": {path: sha(raw) for path, raw in payloads.items()}, "counts": counts}
    if (recipe_pins() != pins or sha((root / PRIMARY).read_bytes()) != INPUT_SHA256
            or any(sha((root / path).read_bytes()) != digest for path, digest in SOURCE_FILES.items())):
        raise ValueError("Herodas recovery source, recipe, or predecessor changed before admission")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Refusing to replace an incomplete retained Herodas evidence directory")
    # Install the complete authority before changing public text. If the final
    # primary replacement fails, the exact predecessor remains and --apply can
    # replay the already installed authority without rerunning recognition.
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".herodas-body-", dir=target.parent) as temporary:
        staged = Path(temporary) / "authority"
        staged.mkdir()
        for path, raw in payloads.items():
            if path in CORE:
                continue
            relative = Path(path).relative_to(AUDIT)
            (staged / relative).write_bytes(raw)
        (staged / "changes.json").write_bytes(encoded(audit))
        os.replace(staged, target)
    for path, raw in outputs.items():
        _replace_bytes(root / path, raw)
    verify(root)
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("apply", "check", "undo"):
        action.add_argument("--" + name, action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--witnesses", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--reviewed-at")
    args = parser.parse_args()
    mode = "apply" if args.apply else "undo" if args.undo else "check"
    run(args.root, mode, witnesses=args.witnesses, request=args.request,
        predictions=args.predictions, reviewed_at=args.reviewed_at)
