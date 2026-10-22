#!/usr/bin/env python3
"""Proofread the published Herodas excerpt and adjudicate source glyph doubts.

The previous release remains a literal preimage. Printed damage, editorial
supplies, and source uncertainty remain excluded from scalar lexical counts.
This source review is an auditable layer, never an extra recognition vote.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "data/corpus/herodas.mimiambi.jsonl"
WORK = "herodas.mimiambi"
AUDIT = "data/corpus_changes/herodas-reading-review"
INPUT_SHA256 = "4f604f16151fdc8748dabdd973feacf040a8a6f49170870173df5c3c07fac939"
PDF = "data/corpus_changes/editorial-role-review/source-herodas.pdf"
PDF_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
QUALIFICATION = (
    "Source proofreading of all 62 older Herodas passages and occurrence-level "
    "review of the 43 archived uncertainty spans in the recovered pages. Original "
    "color captures and the pinned Headlam–Knox 1922 PDF establish the printed "
    "reading; the color captures are the same scan, not an independent edition. "
    "Earlier recognition witnesses, review decisions, and publication bytes remain "
    "recoverable. Printed supplies, cruces, incomplete words, and unresolved source "
    "glyphs stay outside scalar lexical counts. The review preserves the edition's "
    "dialect, all 84 passage identities, and the source-attribution holds."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def compressed(value):
    return gzip.compress(encoded(value), mtime=0)


def recipe_pins():
    names = ("repair_herodas_readings.py", "herodas_excerpt_readings_a.py",
        "herodas_excerpt_readings_b.py", "herodas_uncertainty_readings.py",
        "fetch_herodas_reading_sources.py", "ocr_consensus.py")
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in names}


def source_pins(root):
    from fetch_herodas_reading_sources import BUNDLE, check
    manifest = check(root)
    pins = {PDF: PDF_SHA256, f"{BUNDLE}/manifest.json": sha((Path(root) / BUNDLE / "manifest.json").read_bytes()),
        f"{BUNDLE}/scandata.xml": manifest["scandata"]["sha256"]}
    pins.update({f"{BUNDLE}/{page['file']}": page["sha256"] for page in manifest["pages"].values()})
    return pins


def authority_paths(root):
    import repair_herodas_body as body
    from fetch_herodas_reading_sources import BUNDLE
    paths = {PRIMARY, PDF, *body.authority_paths(root)}
    for directory in (AUDIT, BUNDLE):
        paths.update(path.relative_to(root).as_posix() for path in (Path(root) / directory).rglob("*") if path.is_file())
    paths.update("scripts/" + name for name in recipe_pins())
    return tuple(sorted(paths))


def _predecessor_signature(root):
    import repair_herodas_body as body
    return (tuple((path, sha((Path(root) / path).read_bytes()))
                  for path in body.authority_paths(root)), encoded(body.recipe_pins()))


def observations():
    from herodas_excerpt_readings_a import READINGS as a
    from herodas_excerpt_readings_b import READINGS as b
    from herodas_uncertainty_readings import DECISIONS, EXTRAS
    if set(a) & set(b):
        raise ValueError("Herodas excerpt reviews repeat a passage")
    return {"excerpt": deepcopy({**a, **b}), "uncertainty_decisions": deepcopy(DECISIONS),
            "additional_source_edits": deepcopy(EXTRAS)}


def zoned(value):
    if not isinstance(value, str) or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("A Herodas source decision requires a zoned timestamp")


def _validate_uncertainties(text, items):
    for item in items:
        start, end = item["start"], item["end"]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                or item.get("text", text[start:end]) != text[start:end] or not item.get("evidence")
                or not isinstance(item.get("alternatives"), list)
                or any(not isinstance(value, str) for value in item["alternatives"])):
            raise ValueError("Herodas uncertainty lacks exact corrected bounds and alternatives")


def _recovered_review(row, frozen, decisions, additional=()):
    """Address archived occurrences before applying any shifting character edits."""
    page = int(row["locus"].split("_")[-1].split(".")[0])
    text = row["text"]
    if text != frozen["text"]:
        raise ValueError("Herodas recovered reading differs from the frozen source review")
    pieces, cursor, length = [], 0, 0
    uncertainties, excluded, records = [], [], []
    events = []
    for index, old in enumerate(frozen["uncertainties"]):
        decision = decisions[(page, index)]
        if decision["source_char_range"] != [old["start"], old["end"]]:
            raise ValueError("Herodas source decision changed its archived occurrence")
        events.append(decision)
    events.extend(additional)
    for decision in sorted(events, key=lambda item: item["source_char_range"]):
        start, end = decision["source_char_range"]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                or start < cursor
                or decision["original_text"] != text[start:end] or not decision.get("evidence")):
            raise ValueError("Herodas source decision changed its archived occurrence")
        zoned(decision["reviewed_at"])
        replacement = decision["corrected_text"]
        alternatives = decision["remaining_alternatives"]
        disposition = decision["disposition"]
        if (disposition not in {"resolved", "printed-damage", "unresolved"}
                or not isinstance(replacement, str) or not replacement
                or not isinstance(alternatives, list) or any(not isinstance(x, str) for x in alternatives)
                or disposition == "resolved" and alternatives):
            raise ValueError("Invalid Herodas source-reading disposition")
        prefix = text[cursor:start]
        pieces.extend([prefix, replacement]); length += len(prefix)
        left, right = length, length + len(replacement)
        if disposition == "unresolved" or alternatives:
            uncertainties.append({"start": left, "end": right, "text": replacement,
                "alternatives": alternatives, "evidence": decision["evidence"]})
        if disposition == "printed-damage":
            excluded.append({"start": left, "end": right, "text": replacement,
                "evidence": decision["evidence"], "reason": "reviewed-printed-damage"})
        records.append(deepcopy(decision))
        length = right; cursor = end
    pieces.append(text[cursor:])
    corrected = "".join(pieces)
    return {"original_text": text, "corrected_text": corrected,
        "source_sha256": PDF_SHA256, "scan_page": page,
        "evidence": "Occurrence decisions against the original color capture and pinned PDF; unchanged text retains the frozen source review.",
        "reviewed_at": max((item["reviewed_at"] for item in records), default=frozen["reviewed_at"]),
        "uncertainties": uncertainties, "forced_exclusions": excluded, "decisions": records}


def reviews(before, observation):
    import repair_herodas_body as body
    if sha(before) != INPUT_SHA256:
        raise ValueError("Herodas reading review requires the exact published 84-row body")
    rows = [json.loads(line) for line in before.splitlines()]
    if len(rows) != 84 or len({row["locus"] for row in rows}) != 84:
        raise ValueError("Herodas reading review changed the passage inventory")
    older = {row["locus"] for row in rows if not row.get("herodas_body_recovery")}
    if len(older) != 62 or set(observation["excerpt"]) != older:
        raise ValueError("Herodas excerpt review must account for all 62 older passages")
    frozen = body.source_readings()
    decisions = {}
    for decision in observation["uncertainty_decisions"]:
        key = (decision["scan_page"], decision["uncertainty_index"])
        if key in decisions:
            raise ValueError("Herodas source uncertainty was reviewed twice")
        decisions[key] = decision
    expected = {(page, index) for page, review in frozen.items() for index in range(len(review["uncertainties"]))}
    if len(expected) != 43 or set(decisions) != expected:
        raise ValueError("Herodas uncertainty review must account for all 43 archived occurrences")
    result = {}
    for row in rows:
        locus = row["locus"]
        if locus in older:
            review = deepcopy(observation["excerpt"][locus])
            if review["original_text"] != row["text"]:
                raise ValueError("Herodas excerpt preimage changed: " + locus)
            review.setdefault("forced_exclusions", [])
            review.setdefault("decisions", [])
        else:
            page = body.page_number(row)
            additional = [item for item in observation.get("additional_source_edits", []) if item["scan_page"] == page]
            review = _recovered_review(row, frozen[page], decisions, additional)
        if (not review.get("evidence") or review.get("source_sha256") != PDF_SHA256
                or review["scan_page"] != body.page_number(row)
                or not isinstance(review["corrected_text"], str) or not review["corrected_text"].strip()):
            raise ValueError("Herodas reading lacks literal source-bounded evidence")
        zoned(review["reviewed_at"])
        _validate_uncertainties(review["corrected_text"], review["uncertainties"])
        result[locus] = review
    if any(item["scan_page"] not in frozen for item in observation.get("additional_source_edits", [])):
        raise ValueError("Additional Herodas source edit is outside the recovered body")
    return rows, result


def _source_flags(text, ranges):
    """Full ranges cross pages; an unfinished parenthesized word ends at its line."""
    import re
    pairs = {"[": "]", "<": ">", "⟨": "⟩", "(": ")"}
    marked, stack, obelized = set(), [], False
    for index, char in enumerate(text):
        if char == "\n":
            stack = [closer for closer in stack if closer != ")"]
        if char == "†":
            obelized = not obelized
            marked.add(index)
        if char in pairs:
            stack.append(pairs[char])
        if stack or obelized or char in pairs.values() or char == "\u0323":
            marked.add(index)
        if stack and char == stack[-1]:
            stack.pop()
    flags = []
    for _, start, end in ranges:
        reasons = []
        if any(index in marked for index in range(start, end)):
            reasons.append("printed-supply-or-unclear-reading")
        if (start and text[start - 1] in set(pairs.values()) | {"†", "-", "‐"}
                or end < len(text) and text[end] in set(pairs) | {"†", "-", "‐"}
                or "\u0323" in text[start:end]):
            reasons.append("printed-word-fragment")
        gap = r"(?:\.(?:[ \t]*\.)+|…)"
        if re.search(gap + r"$", text[:start].rstrip()) or re.match(gap, text[end:].lstrip()):
            reasons.append("source-gap-boundary")
        flags.append(reasons)
    return flags


def critical_slots(rows, review):
    """Carry printed critical ranges through speaker and physical-page splits."""
    from herodas_body_source_observations import BODY_PAGES
    from repair_herodas_body import _word_ranges, page_number
    mimes = {page["scan_page"]: page["mime"] for page in BODY_PAGES}
    groups = defaultdict(list)
    for row in rows:
        page = page_number(row)
        # IX, IXa and IXb are separately printed fragments on the same page.
        # A terminal loss in one fragment does not qualify its neighbor's words.
        group = row["locus"] if page == 472 else mimes[page]
        groups[group].append(row["locus"])
    result = {}
    for loci in groups.values():
        joined, bounds = "", {}
        for locus in loci:
            text = review[locus]["corrected_text"]
            bounds[locus] = (len(joined), len(joined) + len(text))
            joined += text + "\n"
        ranges = _word_ranges(joined)
        flags = _source_flags(joined, ranges)
        for locus in loci:
            offset, end = bounds[locus]
            selected = []
            for (word, start, stop), reasons in zip(ranges, flags, strict=True):
                if not offset <= start < end:
                    continue
                local_start, local_end = start - offset, stop - offset
                reasons = list(reasons)
                if (start and joined[start - 1] in "-‐" or stop < len(joined) and joined[stop] in "-‐"):
                    reasons.append("printed-word-fragment")
                for field, reason in (("uncertainties", "unresolved-source-reading"),
                                      ("forced_exclusions", "reviewed-printed-damage")):
                    if any(item["start"] < local_end and local_start < item["end"] for item in review[locus].get(field, [])):
                        reasons.append(reason)
                selected.append((word, local_start, local_end, sorted(set(reasons))))
            result[locus] = selected
    return result


def build_outputs(before, observation, recorded_at, image_manifest):
    from ocr_consensus import compact_corpus_consensus, lexical_eligible
    from repair_herodas_body import literal_edits, ANALYSIS_GREEK, page_number
    zoned(recorded_at)
    rows, review = reviews(before, observation)
    flags = critical_slots(rows, review)
    output, networks, records = [], {}, []
    for old in rows:
        locus = old["locus"]; current = review[locus]; text = current["corrected_text"]
        slots = []
        for index, (word, start, end, reasons) in enumerate(flags[locus]):
            eligible = not reasons and lexical_eligible(word)
            slots.append({"position": index, "selected": word,
                "status": "scan-reviewed" if eligible else "source-marked-reading",
                "lexical_eligible": eligible, "tied_readings": [], "readings": [],
                "lexical_exclusion": ";".join(reasons) or (None if eligible else "mixed-script-token"),
                "source_char_range": [start, end]})
        page = page_number(old)
        if current.get("source_image_sha256", image_manifest["pages"][str(page)]["sha256"]) != image_manifest["pages"][str(page)]["sha256"]:
            raise ValueError("Herodas reading decision changed its original image pin")
        full = {"text": text, "analysis_text": " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"]),
            "source_uncertainties": current["uncertainties"],
            "ocr_consensus": {"schema_version": 1,
                "policy": "Literal scan review above the frozen published reading; no added recognition vote. Printed damage and uncertain glyphs remain excluded.",
                "counts": dict(Counter(slot["status"] for slot in slots)), "slots": slots,
                "witnesses": deepcopy(old.get("ocr_consensus", {}).get("witnesses", [])),
                "predecessor_network": old.get("ocr_consensus", {}).get("full_network"),
                "predecessor": {"path": f"{AUDIT}/before.json.gz", "file": PRIMARY, "locus": locus},
                "source_review": {"path": f"{AUDIT}/observations.json", "locus": locus,
                    "pdf_sha256": PDF_SHA256, "original_image_sha256": image_manifest["pages"][str(page)]["sha256"],
                    "scan_page": page, "reviewed_at": current["reviewed_at"]}}}
        networks[locus] = full
        row = {**deepcopy(old), **compact_corpus_consensus(full, {"path": f"{AUDIT}/networks.json.gz", "key": locus}),
            "herodas_reading_review": {"schema_version": 1, "authority": f"{AUDIT}/changes.json", "recorded_at": recorded_at}}
        changes = literal_edits(old["text"], text, current, page, "published-predecessor")
        records.append({"locus": locus, "original_text": old["text"], "corrected_text": text,
            "original_analysis_text": old.get("analysis_text", old["text"]), "corrected_analysis_text": full["analysis_text"],
            "literal_edits": changes, "review": current,
            "source": "https://archive.org/details/mimesfragments00hero", "source_pdf_sha256": PDF_SHA256,
            "original_image_sha256": image_manifest["pages"][str(page)]["sha256"], "reviewed_at": current["reviewed_at"]})
        output.append(row)
    decisions = observation["uncertainty_decisions"]
    counts = {"passages": len(rows), "body_pages": 35, "older_passages_reviewed": 62,
        "older_changed_passages": sum(old["text"] != row["text"] for old, row in zip(rows, output) if not old.get("herodas_body_recovery")),
        "changed_passages": sum(old["text"] != row["text"] for old, row in zip(rows, output)),
        "literal_edits": sum(len(record["literal_edits"]) for record in records),
        "previous_analysis_tokens": sum(len(ANALYSIS_GREEK.findall(row.get("analysis_text", row["text"]))) for row in rows),
        "analysis_tokens": sum(len(ANALYSIS_GREEK.findall(row["analysis_text"])) for row in output),
        "analysis_tokens_by_origin": {name: {
            "previous": sum(len(ANALYSIS_GREEK.findall(row.get("analysis_text", row["text"])))
                for row in rows if bool(row.get("herodas_body_recovery")) == recovered),
            "current": sum(len(ANALYSIS_GREEK.findall(row["analysis_text"]))
                for old, row in zip(rows, output) if bool(old.get("herodas_body_recovery")) == recovered)}
            for name, recovered in (("older_excerpt", False), ("recovered_pages", True))},
        "archived_uncertainty_spans_reviewed": len(decisions), "archived_uncertainty_slots": 45,
        "additional_source_edits": len(observation.get("additional_source_edits", [])),
        "archived_decisions": dict(sorted(Counter(item["disposition"] for item in decisions).items())),
        "archived_uncertainty_spans_remaining": sum(item["disposition"] == "unresolved" or bool(item["remaining_alternatives"]) for item in decisions),
        "older_uncertainty_spans_remaining": sum(len(row["source_uncertainties"]) for old, row in zip(rows, output) if not old.get("herodas_body_recovery")),
        "remaining_uncertainty_spans": sum(len(row["source_uncertainties"]) for row in output),
        "remaining_uncertainty_slots": sum("unresolved-source-reading" in (slot.get("lexical_exclusion") or "") for full in networks.values() for slot in full["ocr_consensus"]["slots"]),
        "noncountable_slots": sum(not slot["lexical_eligible"] for full in networks.values() for slot in full["ocr_consensus"]["slots"])}
    raw = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in output)
    return raw, records, networks, counts


def _before(root, audit):
    raw = (Path(root) / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["outputs"][f"{AUDIT}/before.json.gz"]:
        raise ValueError("Herodas proofreading literal preimage archive changed")
    before = json.loads(gzip.decompress(raw))
    if (audit["inputs"] != {PRIMARY: INPUT_SHA256} or set(before) != {PRIMARY}
            or sha(before[PRIMARY].encode()) != INPUT_SHA256):
        raise ValueError("Herodas proofreading predecessor identity changed")
    return before[PRIMARY].encode()


@lru_cache(maxsize=4)
def _replay(before, observation, recorded_at, image_manifest, recipes):
    raw, records, networks, counts = build_outputs(before, json.loads(observation), recorded_at, json.loads(image_manifest))
    return raw, encoded(records), encoded(networks), encoded(counts)


def verify(root, *, active=True):
    import repair_herodas_body as body
    from fetch_herodas_reading_sources import BUNDLE
    root = Path(root); audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("qualification") != QUALIFICATION
            or audit.get("recipe_sha256") != recipe_pins() or audit.get("sources") != source_pins(root)):
        raise ValueError("Herodas proofreading source or recipe authority changed")
    before = _before(root, audit)
    _, _, old_output = body.verify(root, active=False)
    if old_output[PRIMARY] != before:
        raise ValueError("Herodas proofreading detached from the frozen body recovery")
    required = {PRIMARY, *(f"{AUDIT}/{name}" for name in ("before.json.gz", "observations.json", "records.json.gz", "networks.json.gz"))}
    if set(audit["outputs"]) != required:
        raise ValueError("Herodas proofreading output inventory changed")
    for path, digest in {**audit["sources"], **audit["outputs"]}.items():
        if path == PRIMARY and not active:
            continue
        if sha((root / path).read_bytes()) != digest:
            raise ValueError("Herodas proofreading source or output changed: " + path)
    observation = (root / AUDIT / "observations.json").read_bytes()
    if observation != encoded(observations()):
        raise ValueError("Herodas proofreading observations do not reproduce their source code")
    raw, records, networks, counts = _replay(before, observation, audit["recorded_at"],
        (root / BUNDLE / "manifest.json").read_bytes(), encoded(audit["recipe_sha256"]))
    if (sha(raw) != audit["outputs"][PRIMARY] or active and raw != (root / PRIMARY).read_bytes()
            or records != gzip.decompress((root / AUDIT / "records.json.gz").read_bytes())
            or networks != gzip.decompress((root / AUDIT / "networks.json.gz").read_bytes())
            or counts != encoded(audit["counts"])):
        raise ValueError("Herodas proofreading does not replay its exact source decisions")
    return audit, before, raw


@lru_cache(maxsize=4)
def _active_rows(root, signature):
    _, _, raw = verify(root)
    return {row["locus"]: row for row in map(json.loads, raw.splitlines())}


def lexical_segments(row, root=None):
    root = Path(ROOT if root is None else root)
    pins = tuple((path, sha((root / path).read_bytes())) for path in authority_paths(root))
    if _active_rows(str(root), pins).get(row["locus"]) != row:
        raise ValueError("Herodas lexical reading differs from its checked proofreading")
    return []


def manifestation_metadata(root):
    from herodas_review_state import review_is_unapplied
    root = Path(root)
    if not (root / AUDIT / "changes.json").exists() or review_is_unapplied(root):
        return {}
    audit, _, _ = verify(root)
    return {WORK: {"default_edition": "herodas-hk-ocr",
        "editions": [{"key": "herodas-hk-ocr", "name": "Headlam–Knox 1922, source-proofread Herodas body",
            "editor": "Headlam, Walter; Knox, Alfred", "year": 1922, "license": "PD", "provider": "ocr",
            "source": "https://archive.org/details/mimesfragments00hero", "scheme": "scan-page.row",
            "storage": "primary", "servable": True, "note": QUALIFICATION}],
        "coverage_composition": {"policy": "source-reviewed-reading-corrections",
            "manifest": f"{AUDIT}/changes.json", "manifest_sha256": sha((root / AUDIT / "changes.json").read_bytes()),
            "qualification": QUALIFICATION, "counts": audit["counts"],
            "primary_quality": {"status": "source-reviewed-with-critical-exclusions", "passages": 84, "note": QUALIFICATION},
            "components": [{"edition": "herodas-hk-ocr", "storage": "primary", "path": PRIMARY,
                "passages": 84, "role": "authorial-verse", "license": "PD", "source": "https://archive.org/details/mimesfragments00hero"}]}}}


def undo(root):
    from repair_herodas_body import _replace_bytes
    root = Path(root); audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    before = _before(root, audit); current = (root / PRIMARY).read_bytes()
    if current == before:
        return
    if sha(current) != audit["outputs"][PRIMARY]:
        raise ValueError("Cannot undo a modified Herodas proofreading output")
    _replace_bytes(root / PRIMARY, before)


def run(root, mode, recorded_at=None):
    from fetch_herodas_reading_sources import BUNDLE
    from herodas_review_state import review_is_unapplied
    from repair_herodas_body import _replace_bytes
    root = Path(root); target = root / AUDIT
    if mode == "undo":
        undo(root); return
    if (target / "changes.json").exists():
        current = (root / PRIMARY).read_bytes()
        audit, before, raw = verify(root, active=not review_is_unapplied(root))
        if mode == "apply" and current != raw:
            if current != before:
                raise ValueError("Reapply the earlier body recovery before Herodas proofreading")
            _replace_bytes(root / PRIMARY, raw)
        print(json.dumps(audit["counts"], sort_keys=True)); return
    if mode != "apply":
        raise ValueError("Herodas proofreading has not been admitted")
    import repair_herodas_body as body
    predecessor = _predecessor_signature(root)
    body.verify(root)
    before = (root / PRIMARY).read_bytes(); observation = encoded(observations())
    sources, recipes = source_pins(root), recipe_pins()
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    raw, records, networks, counts = _replay(before, observation, recorded_at,
        (root / BUNDLE / "manifest.json").read_bytes(), encoded(recipes))
    payloads = {f"{AUDIT}/before.json.gz": compressed({PRIMARY: before.decode()}),
        f"{AUDIT}/observations.json": observation,
        f"{AUDIT}/records.json.gz": gzip.compress(records, mtime=0),
        f"{AUDIT}/networks.json.gz": gzip.compress(networks, mtime=0), PRIMARY: raw}
    audit = {"schema_version": 1, "recorded_at": recorded_at, "qualification": QUALIFICATION,
        "inputs": {PRIMARY: INPUT_SHA256}, "sources": sources, "recipe_sha256": recipes,
        "outputs": {path: sha(value) for path, value in payloads.items()}, "counts": json.loads(counts)}
    if target.exists() and any(target.iterdir()):
        raise ValueError("Refusing to replace an incomplete Herodas proofreading authority")
    def unchanged():
        if (before != (root / PRIMARY).read_bytes() or source_pins(root) != sources
                or recipe_pins() != recipes or _predecessor_signature(root) != predecessor
                or any(sha((root / path).read_bytes()) != digest for path, digest in sources.items())):
            raise ValueError("Herodas proofreading inputs changed before admission")

    unchanged()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".herodas-reading-review-", dir=target.parent) as directory:
        staged = Path(directory) / "authority"; staged.mkdir()
        for path, value in payloads.items():
            if path != PRIMARY:
                (staged / Path(path).name).write_bytes(value)
        (staged / "changes.json").write_bytes(encoded(audit))
        unchanged()
        os.replace(staged, target)
    _replace_bytes(root / PRIMARY, raw)
    verify(root)
    print(json.dumps(audit["counts"], sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--recorded-at")
    args = parser.parse_args()
    mode = "apply" if args.apply else "undo" if args.undo else "check"
    run(args.root, mode, args.recorded_at)


if __name__ == "__main__":
    main()
