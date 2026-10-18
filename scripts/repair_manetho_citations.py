#!/usr/bin/env python3
"""Use Koechly's printed book headings for Manetho, retaining source citations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = "manetho-astrology.apotelesmatica"
EDITION = "1st1K-grc1"
SCHEME = "manetho-first1k-book-attributes"
BOOKS = {"1": "1", "2": "2", "3": "3", "4": "6", "5": "4", "6": "5"}
SOURCE_SHA256 = "30a6b06394f8f50a544805055c3ac68b02f02dd12fb1672940a593b2e3e39d0e"
TEI_SHA256 = "2ada16526f10454abddc46b7c043d11b7eb03d2e7c31113d9162ab1e9062d471"
AUDIT = "data/corpus_changes/manetho-citations-51"
ALIASES = "data/citation_aliases.json"
CORPUS_PATH = f"data/corpus/{WORK}.jsonl"
TEXT_RULES = "data/corpus_text_corrections.json"
PRIOR_AUDIT = "data/corpus_changes/nonfinal_grave_tranche_thirdparty.applied.json"
EVIDENCE = {
    "issue": "https://github.com/open-greek/open-greek-corpus/issues/51",
    "tei_url": "https://github.com/OpenGreekAndLatin/First1KGreek/blob/master/data/tlg2583/tlg001/tlg2583.tlg001.1st1K-grc1.xml",
    "tei_sha256": TEI_SHA256,
    "scan_url": "https://archive.org/details/apotelesmaticoru00maneuoft",
    "pdf_sha256": "2e23238a3d7a6ae47b556ec3c58163d07da72fa30a686f0f90c1e7b84566d725",
    "book_boundaries": [
        {"source_book": "2", "printed_book": "2", "heading": "ΒΙΒΛΙΟΝ Β. [Α.]", "printed_page": 3, "scan_page": 37},
        {"source_book": "3", "printed_book": "3", "heading": "ΒΙΒΛΙΟΝ Γ. [Β.]", "printed_page": 20, "scan_page": 54},
        {"source_book": "4", "printed_book": "6", "heading": "ΒΙΒΛΙΟΝ Ϛ. [Γ.]", "printed_page": 36, "scan_page": 70},
        {"source_book": "5", "printed_book": "4", "heading": "ΒΙΒΛΙΟΝ Δ.", "printed_page": 62, "scan_page": 96},
        {"source_book": "1", "printed_book": "1", "heading": "ΒΙΒΛΙΟΝ Α. [Ε.]", "printed_page": 84, "scan_page": 118},
        {"source_book": "6", "printed_book": "5", "heading": "ΒΙΒΛΙΟΝ Ε. [Ϛ.]", "printed_page": 99, "scan_page": 133},
    ],
    "evidence": "Manual inspection of all six book openings and printed page 75 (scan 109), where Book IV verse 358 contains τριβάδας. Use the principal printed numeral, preserving the bracketed alternative in this evidence. First1K's book attributes disagree with those headings for 4, 5, and 6; this is a permutation, not a global offset. Verse numbering, section levels, document order, and all readings remain unchanged.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def validate_source(work, edition, source, path):
    """Fail before writing if the edition underlying a reviewed mapping changes."""
    if (work, edition, source) == (WORK, EDITION, "first1k"):
        if sha(Path(path).read_bytes()) != TEI_SHA256:
            raise ValueError("Manetho TEI changed; review the book boundaries again")


def remap_record(row):
    """Apply the simultaneous source-to-heading permutation exactly once."""
    if (row.get("urn"), row.get("edition"), row.get("source")) != (WORK, EDITION, "first1k"):
        return row
    if "source_citation" in row:
        raise ValueError("Manetho source citations have already been mapped")
    book, separator, tail = row["locus"].partition(".")
    if book not in BOOKS or not separator:
        raise ValueError(f"Unreviewed Manetho locus: {row['locus']}")
    return dict(row, locus=BOOKS[book] + "." + tail,
                source_citation={"scheme": SCHEME, "locus": row["locus"]})


def route(raw):
    rows, aliases, changes, seen = [], {}, [], set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result = remap_record(row)
        if result is row:
            raise ValueError("Unreviewed Manetho source row")
        if result["locus"] in seen or row["locus"] in aliases:
            raise ValueError("Repeated Manetho citation")
        seen.add(result["locus"])
        target = {"slug": WORK, "path": CORPUS_PATH, "locus": result["locus"]}
        aliases[row["locus"]] = target
        changes.append({"original_locus": row["locus"], "corrected_locus": result["locus"],
                        "text_sha256": sha(row["text"].encode()), "text_changed": False,
                        "evidence": "koechly-1858-book-headings"})
        rows.append(result)
    if {row["source_citation"]["locus"].split(".")[0] for row in rows} != set(BOOKS):
        raise ValueError("The reviewed Manetho source must contain all six books")
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode(), changes, aliases


def preserve_prior_text_rules(root, raw):
    """Replay the four already published accent decisions at source loci.

    This generates ingest rules from the original audit, not new text edits.
    That audit's after-hash is exactly this migration's pinned input.
    """
    prior = json.loads((root / PRIOR_AUDIT).read_text())
    block = next(b for b in prior["files"] if b["file"] == CORPUS_PATH)
    if block["sha256_after"] != sha(raw):
        raise ValueError("Prior Manetho text audit no longer describes this input")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    rules = json.loads((root / TEXT_RULES).read_text())
    for edit in block["edits"]:
        row = rows[edit["index"]]
        for offset, original in edit["was"]:
            corrected = prior["substitutions"][original]
            if row["text"][offset:offset + len(corrected)] != corrected:
                raise ValueError("Prior Manetho correction does not match its archived offset")
            rule = {"work": WORK, "locus": row["locus"], "original": original,
                    "correction": corrected, "expected_occurrences": 1,
                    "evidence": f"Replay the existing decision in {PRIOR_AUDIT}, row index {edit['index']}; its after-hash matches the archived input for issue 51. Apply at the original First1K locus before mapping book numbers.",
                    "date": prior["date"], "audit_source": PRIOR_AUDIT,
                    "reversible": "restore the original token recorded in the source audit"}
            if not any(r["work"] == WORK and r["locus"] == row["locus"]
                       and r["original"] == original for r in rules["corrections"]):
                rules["corrections"].append(rule)
    return dump(rules)


def run(root, mode):
    audit_dir = root / AUDIT
    audit_path = audit_dir / "changes.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
        if mode == "undo":
            for path, expected in audit["outputs"].items():
                current = sha((root / path).read_bytes()) if (root / path).exists() else None
                if current != expected:
                    raise ValueError(f"Output changed since repair; refusing to overwrite: {path}")
            for path, text in snapshots.items():
                target = root / path
                if text is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_text(text)
            print("Restored exact Manetho inputs; rebuild derived reports.")
            return
        raw = snapshots[CORPUS_PATH].encode()
        if sha(raw) != SOURCE_SHA256 or audit["evidence"] != EVIDENCE:
            raise ValueError("Manetho source pin or evidence changed")
        output, changes, aliases = route(raw)
        if (root / CORPUS_PATH).read_bytes() != output or changes != audit["changes"]:
            raise ValueError("Manetho corpus or audit differs from replay")
        if json.loads((root / ALIASES).read_text())["schemes"][SCHEME]["aliases"] != aliases:
            raise ValueError("Manetho citation aliases differ from replay")
        # Recreate the ingest rules against their original configuration too.
        # Later unrelated rules may be added without invalidating this audit.
        current_rules = json.loads((root / TEXT_RULES).read_text())["corrections"]
        expected_rules = json.loads(audit["ingest_rules"])["corrections"]
        if any(rule not in current_rules for rule in expected_rules):
            raise ValueError("Previously audited text corrections are missing from ingest")
        print(f"Verified {len(changes)} Manetho source citations; all text is unchanged.")
        return
    if mode in {"check", "undo"}:
        raise ValueError("The Manetho repair has not been applied")
    raw = (root / CORPUS_PATH).read_bytes()
    if sha(raw) != SOURCE_SHA256:
        raise ValueError("Manetho source changed; review it again")
    output, changes, aliases = route(raw)
    moved = sum(r["original_locus"] != r["corrected_locus"] for r in changes)
    print(f"Map {moved} citations; preserve all {len(changes)} source destinations.")
    if mode != "apply":
        return
    paths = [CORPUS_PATH, ALIASES, "data/work_index.json", TEXT_RULES]
    snapshots = {path: (root / path).read_text() if (root / path).exists() else None for path in paths}
    alias_data = json.loads(snapshots[ALIASES]) if snapshots[ALIASES] else {"schema_version": 1, "schemes": {}}
    if SCHEME in alias_data["schemes"]:
        raise ValueError("Manetho citation scheme already exists")
    alias_data["schemes"][SCHEME] = {
        "work": WORK, "source_edition": EDITION, "canonical_scheme": "book.section.line",
        "description": "First1K's original book attributes, used in corpus releases through corpus-2026-10-17. Qualify historical citations with this scheme; unqualified citations use the printed headings.",
        "aliases": aliases,
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "before.json.gz").write_bytes(gzip.compress(dump(snapshots), mtime=0))
    ingest_rules = preserve_prior_text_rules(root, raw)
    (root / TEXT_RULES).write_bytes(ingest_rules)
    (root / CORPUS_PATH).write_bytes(output)
    (root / ALIASES).write_bytes(dump(alias_data))
    import build_work_index
    build_work_index.build(write=True)
    audit_path.write_bytes(dump({"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/repair_manetho_citations.py", "sources": {WORK: SOURCE_SHA256},
        "evidence": EVIDENCE, "changes": changes,
        "ingest_rules": ingest_rules.decode(),
        "reversal": "python3 scripts/repair_manetho_citations.py --undo; rebuild derived reports",
        "outputs": {path: sha((root / path).read_bytes()) for path in paths}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"))
