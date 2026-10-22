#!/usr/bin/env python3
"""Repair the Phoenix work boundary and its 21 scan-reviewed Coronistae verses.

The legacy file is a mixed OCR extraction of Crusius's 1894 volume. Its other
rows remain individually citable outside the primary corpus. Apply, replay,
and exact undo use archived preimages; no historical OCR witness is discarded.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re

from critical_text import SCHEMA, annotate, finalize_tokens, validate

ROOT = Path(__file__).resolve().parents[1]
WORK = "phoenix.fragmenta"
EDITION = "crusius-1894-source-reviewed"
PRIMARY = f"data/corpus/{WORK}.jsonl"
RETAINED = "data/paratext/crusius-1894-legacy.jsonl"
ALIASES = "data/passage_aliases.json"
AUDIT = "data/corpus_changes/phoenix-crusius-review"
ORIGINAL_SHA256 = "9015e9406b4c768489e014c1874c064c3913738aa4954433b7932ea3ee914ce9"
SOURCE_SHA256 = "999122f204d54ec0071749c354598adef4203ea6fc61b53e4a6b0f5df92aade1"
PRIMARY_LOCI = tuple(f"phoenix_choliambi_crusius_{page:04d}.{line}"
                     for page, lines in [(68, range(3, 18)), (69, range(1, 7))]
                     for line in lines)
ROLE = "outside-work-edition-material"
SCOPE = "Phoenix Coronistae, 21 verses"
QUALIFICATION = (
    "Crusius 1894 prints the 21 verses of Phoenix's Coronistae, not all surviving "
    "Phoenix fragments. The historical whole-volume OCR includes Herodas, "
    "editorial quotations, apparatus, and indexes. Those other rows are retained "
    "as an unseparated edition witness outside the primary corpus; their text "
    "and individual authorial attribution have not been certified by this review."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def recipe_pins():
    names = ("repair_phoenix_crusius.py", "phoenix_crusius_source_observations.py",
             "phoenix_crusius_witnesses.py", "critical_text.py")
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in names}


def parse_original(raw):
    if sha(raw) != ORIGINAL_SHA256:
        raise ValueError("The original Phoenix volume differs from its reviewed pin")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 2749 or len({row["locus"] for row in rows}) != len(rows):
        raise ValueError("The original volume must have 2,749 unique row identities")
    if any(row.get("urn") != WORK or row.get("edition") != "qwen36-phoenix_choliambi_crusius"
           or not re.fullmatch(r"phoenix_choliambi_crusius_\d{4}\.\d+", row["locus"])
           for row in rows):
        raise ValueError("Foreign work, edition, or locus in Phoenix source")
    if not set(PRIMARY_LOCI) <= {row["locus"] for row in rows}:
        raise ValueError("A reviewed Phoenix verse is missing")
    return rows


def _spans(text):
    """Represent printed angle supplies without promoting partially supplied words."""
    parts, cursor = [], 0
    for match in re.finditer(r"<([^<>]+)>", text):
        if match.start() > cursor:
            parts.append({"kind": "text", "text": text[cursor:match.start()],
                          "selected": True, "ancestors": []})
        parts.append({"kind": "text", "text": match[1], "selected": True,
                      "ancestors": [{"tag": "supplied", "attributes": {
                          "reason": "omitted", "evidence": "printed-editorial-supply"}}]})
        cursor = match.end()
    if cursor < len(text):
        parts.append({"kind": "text", "text": text[cursor:], "selected": True, "ancestors": []})
    if any("<" in part["text"] or ">" in part["text"] for part in parts):
        raise ValueError("Unbalanced or nested editorial supply in reviewed text")
    return parts


def build_primary_row(original, decision, review_sha256, reviewed_at):
    if (original["locus"] != decision["locus"]
            or original["text"] != decision["original_text"]):
        raise ValueError("A Phoenix scan decision lost its literal preimage")
    text = decision["corrected_text"]
    prefix, suffix = original["locus"].rsplit(".", 1)
    row = dict(original, edition=EDITION, text=text)
    if text != original["text"]:
        row["corrections"] = list(dict.fromkeys([*original.get("corrections", []), "manual"]))
    row.update(critical_markup={"schema": SCHEMA},
        textparts=[{"tag": "div", "attributes": {
            "type": "textpart", "subtype": "physical-scan", "n": prefix}}],
        line_attributes={"n": suffix}, spans=_spans(text),
        crusius_source_review={"schema_version": 1,
            "source_review": f"{AUDIT}/source-review.json", "source_review_sha256": review_sha256,
            "scan_sha256": SOURCE_SHA256, "reviewed_at": reviewed_at,
            "verse": decision["verse"], "scan_page": decision["scan_page"],
            "printed_page": decision["printed_page"], "scope": SCOPE})
    row["physical_refs"] = {"textparts": row["textparts"],
        "line_attributes": row["line_attributes"], "scan_page": decision["scan_page"],
        "printed_page": decision["printed_page"], "verse": decision["verse"]}
    # The print separates verses 17 and 18 with a divider. Preserve that fact
    # without inventing a lost word or a continuous positional context.
    if decision.get("gap_after"):
        row["source_gap_after"] = decision["gap_after"]
    annotate(row)
    finalize_tokens([row])
    return row


def build_outputs(raw, review, review_raw, aliases_raw):
    from phoenix_crusius_source_observations import build_source_review
    rows = parse_original(raw)
    expected_review = build_source_review(rows, reviewed_at=review["reviewed_at"])
    if review != expected_review:
        raise ValueError("Source review differs from the checked scan observations")
    if (review["source"]["sha256"] != SOURCE_SHA256
            or review["approved_primary_loci"] != list(PRIMARY_LOCI)
            or review["scope"] != SCOPE):
        raise ValueError("Source review changed its scan, order, or primary scope")
    decisions = {decision["locus"]: decision for decision in review["verses"]}
    if set(decisions) != set(PRIMARY_LOCI) or len(review["verses"]) != 21:
        raise ValueError("Review must account for exactly 21 Phoenix verses")
    original_by_locus = {row["locus"]: row for row in rows}
    primary = [build_primary_row(original_by_locus[locus], decisions[locus], sha(review_raw), review["reviewed_at"])
               for locus in PRIMARY_LOCI]
    retained = [dict(row, **{"class": ROLE}, lang="grc",
        why_not_served="Outside the scan-reviewed Phoenix Coronistae; mixed edition OCR retained without a constituent work attribution.")
        for row in rows if row["locus"] not in decisions]
    if len(retained) != 2728 or len(primary) + len(retained) != len(rows):
        raise ValueError("The work-boundary partition dropped or repeated a source row")
    aliases = json.loads(aliases_raw)
    if WORK in aliases["aliases"]:
        raise ValueError("Phoenix already has historical passage aliases; refusing to replace them")
    destinations = {row["locus"]: {"path": PRIMARY, "slug": WORK, "locus": row["locus"]}
                    for row in primary}
    destinations.update({row["locus"]: {"path": RETAINED, "locus": row["locus"]}
                         for row in retained})
    aliases["aliases"][WORK] = destinations
    corrected_by_locus = {row["locus"]: row for row in primary + retained}
    records = []
    for index, original in enumerate(rows):
        corrected = corrected_by_locus[original["locus"]]
        records.append({"original_line_number": index + 1, "locus": original["locus"],
            "original_text": original["text"], "corrected_text": corrected["text"],
            "original_row": original, "corrected_row": corrected,
            "destination": destinations[original["locus"]],
            "text_changed": original["text"] != corrected["text"],
            "source_review_sha256": sha(review_raw), "reviewed_at": review["reviewed_at"],
            "evidence": decisions.get(original["locus"], {
                "kind": "work-boundary-exclusion", "source": review["source"],
                "qualification": QUALIFICATION})})
    counts = {"original_rows": len(rows), "primary_rows": len(primary),
        "retained_outside_primary": len(retained),
        "changed_text_rows": sum(record["text_changed"] for record in records),
        "surface_tokens": sum(len(row["tokens"]) for row in primary),
        "lexical_tokens": sum(sum(token["lexical_eligible"] for token in row["tokens"]) for row in primary),
        "excluded_supplied_tokens": sum(sum(not token["lexical_eligible"] for token in row["tokens"]) for row in primary),
        "source_scan_pages": sorted({row["crusius_source_review"]["scan_page"] for row in primary})}
    alias_output = (json.dumps(aliases, ensure_ascii=False, indent=2) + "\n").encode()
    return {PRIMARY: jsonl(primary), RETAINED: jsonl(retained), ALIASES: alias_output}, records, counts


def _read_json_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def undo(root):
    """Unapply literal postimages even when their correction source is invalidated."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    core = {PRIMARY, RETAINED, ALIASES}
    if (audit.get("schema_version") != 1 or set(audit.get("inputs", {})) != core
            or audit["inputs"][PRIMARY] != ORIGINAL_SHA256 or audit["inputs"][RETAINED] is not None):
        raise ValueError("Phoenix literal undo has an unexpected original authority")
    before_raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(before_raw) != audit["outputs"][f"{AUDIT}/before.json.gz"]:
        raise ValueError("Phoenix archived preimage output changed")
    before = json.loads(gzip.decompress(before_raw))
    if set(before) != core:
        raise ValueError("Phoenix archived preimage paths changed")
    for relative, original in before.items():
        if (sha(original.encode()) if original is not None else None) != audit["inputs"][relative]:
            raise ValueError("Phoenix archived preimage changed: " + relative)
    current = {relative: sha((root / relative).read_bytes()) if (root / relative).is_file() else None
               for relative in core}
    if current == audit["inputs"]:
        print("Phoenix review is already exactly unapplied.")
        return
    for relative, actual in current.items():
        if actual != audit["outputs"][relative]:
            raise ValueError("Phoenix literal undo output changed: " + relative)
    for relative, original in before.items():
        target = root / relative
        if original is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(original)
    print("Restored exact served text and passage aliases; rebuild derived metadata.")


def verify(root, *, active=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit["schema_version"] != 1 or audit["inputs"][PRIMARY] != ORIGINAL_SHA256
            or audit["qualification"] != QUALIFICATION):
        raise ValueError("Phoenix audit schema, preimage, or qualification changed")
    if audit["recipe_sha256"] != recipe_pins():
        raise ValueError("Phoenix replay recipe changed; preserve the published authority")
    for relative, expected in audit["outputs"].items():
        if not active and relative in {PRIMARY, RETAINED, ALIASES}:
            continue
        path = root / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise ValueError("Phoenix repair output changed: " + relative)
    before = _read_json_gzip(root / AUDIT / "before.json.gz")
    for relative, expected in audit["inputs"].items():
        value = before[relative]
        if (sha(value.encode()) if value is not None else None) != expected:
            raise ValueError("Phoenix archived preimage changed: " + relative)
    review_raw = (root / AUDIT / "source-review.json").read_bytes()
    review = json.loads(review_raw)
    if audit["evidence"]["source"] != review["source"] or audit["evidence"]["source_review"] != {
            "path": f"{AUDIT}/source-review.json", "sha256": sha(review_raw)}:
        raise ValueError("Phoenix source authority changed")
    if sha((root / AUDIT / "source-scan.pdf").read_bytes()) != SOURCE_SHA256:
        raise ValueError("Phoenix scan differs from its source pin")
    from phoenix_crusius_witnesses import validate_packet
    validate_packet(_read_json_gzip(root / AUDIT / "ocr-witnesses.json.gz"))
    outputs, records, counts = build_outputs(before[PRIMARY].encode(), review, review_raw, before[ALIASES].encode())
    actual_records = [json.loads(line) for line in gzip.decompress((root / AUDIT / "records.jsonl.gz").read_bytes()).splitlines()]
    if counts != audit["counts"] or records != actual_records:
        raise ValueError("Phoenix audit does not reproduce its complete row partition")
    for relative, expected in outputs.items():
        if sha(expected) != audit["outputs"][relative]:
            raise ValueError("Phoenix replay differs from its recorded output pin: " + relative)
        if active and (root / relative).read_bytes() != expected:
            raise ValueError("Phoenix literal replay differs: " + relative)
    return audit, before, outputs


@lru_cache(maxsize=4)
def _projection_rows(root, signature):
    verify(Path(root))
    return {row["locus"]: row for row in
            map(json.loads, (Path(root) / PRIMARY).read_bytes().splitlines())}


def lexical_segments(row, root=None):
    """Validate the admitted postimage before exporting complete extant words."""
    root = Path(ROOT if root is None else root)
    paths = [PRIMARY, RETAINED, ALIASES, f"{AUDIT}/changes.json", f"{AUDIT}/source-review.json",
             f"{AUDIT}/before.json.gz", f"{AUDIT}/records.jsonl.gz", f"{AUDIT}/ocr-witnesses.json.gz",
             f"{AUDIT}/source-scan.pdf"]
    signature = tuple((path, (root / path).stat().st_size, (root / path).stat().st_mtime_ns) for path in paths)
    expected = _projection_rows(str(root), signature).get(row["locus"])
    if expected != row:
        raise ValueError("Phoenix lexical row differs from its scan-reviewed postimage")
    validate(row)
    runs, current = [], []
    for token in row["tokens"]:
        if token["lexical_eligible"]:
            current.append(token["form"])
        elif current:
            runs.append(" ".join(current)); current = []
    if current:
        runs.append(" ".join(current))
    return runs


def run(root, mode, *, source_pdf=None, witness_root=None, reviewed_at=None):
    root = Path(root)
    audit_path = root / AUDIT / "changes.json"
    if audit_path.exists():
        if mode == "undo":
            undo(root)
            return
        recorded = json.loads(audit_path.read_bytes())
        restored = all((sha((root / relative).read_bytes()) if (root / relative).is_file() else None) == expected
                       for relative, expected in recorded["inputs"].items())
        audit, before, outputs = verify(root, active=not restored)
        if restored:
            if mode == "apply":
                for relative, body in outputs.items():
                    (root / relative).write_bytes(body)
                verify(root)
                print("Reapplied the archived Phoenix review without external inputs.")
            else:
                print("Phoenix review is exactly unapplied; retained audit evidence verified.")
            return
        print(json.dumps(audit["counts"], sort_keys=True))
        return
    if mode in {"check", "undo"}:
        raise ValueError("The Phoenix review has not been applied")
    raw = (root / PRIMARY).read_bytes()
    rows = parse_original(raw)
    from phoenix_crusius_source_observations import build_source_review
    reviewed_at = reviewed_at or datetime.now(timezone.utc).isoformat()
    datetime.fromisoformat(reviewed_at)  # reject an unparseable review timestamp
    review = build_source_review(rows, reviewed_at=reviewed_at)
    review_raw = encoded(review)
    aliases_raw = (root / ALIASES).read_bytes()
    if (root / RETAINED).exists():
        raise ValueError("The retained edition witness already exists")
    outputs, records, counts = build_outputs(raw, review, review_raw, aliases_raw)
    print(json.dumps(counts, sort_keys=True))
    if mode != "apply":
        return
    if source_pdf is None or sha(Path(source_pdf).read_bytes()) != SOURCE_SHA256:
        raise ValueError("Apply requires the exact reviewed Crusius source PDF")
    if witness_root is None:
        raise ValueError("Apply requires the retained historical OCR witness root")
    from phoenix_crusius_witnesses import build_packet, validate_packet
    witnesses = build_packet(Path(witness_root))
    validate_packet(witnesses)
    before = {PRIMARY: raw.decode(), RETAINED: None, ALIASES: aliases_raw.decode()}
    artifacts = {f"{AUDIT}/before.json.gz": gzip.compress(encoded(before), mtime=0),
        f"{AUDIT}/source-review.json": review_raw,
        f"{AUDIT}/source-scan.pdf": Path(source_pdf).read_bytes(),
        f"{AUDIT}/ocr-witnesses.json.gz": gzip.compress(encoded(witnesses), mtime=0),
        f"{AUDIT}/records.jsonl.gz": gzip.compress(jsonl(records), mtime=0)}
    audit = {"schema_version": 1, "recorded_at": reviewed_at,
        "recipe_sha256": recipe_pins(),
        "generator": "scripts/repair_phoenix_crusius.py", "qualification": QUALIFICATION,
        "inputs": {path: sha(text.encode()) if text is not None else None for path, text in before.items()},
        "evidence": {"original_corpus_sha256": ORIGINAL_SHA256,
            "source": review["source"], "source_review": {
            "path": f"{AUDIT}/source-review.json", "sha256": sha(review_raw)}},
        "counts": counts, "outputs": {path: sha(body) for path, body in {**outputs, **artifacts}.items()},
        "reversal": "python3 scripts/repair_phoenix_crusius.py --undo; rebuild derived metadata"}
    # Validate every input and build every byte before the first write.
    for relative, body in {**artifacts, **outputs}.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    audit_path.write_bytes(encoded(audit))
    verify(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--witness-root", type=Path)
    parser.add_argument("--reviewed-at")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"),
        source_pdf=args.source_pdf, witness_root=args.witness_root, reviewed_at=args.reviewed_at)


if __name__ == "__main__":
    main()
