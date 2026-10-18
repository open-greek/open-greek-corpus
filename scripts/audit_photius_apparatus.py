#!/usr/bin/env python3
"""Screen unchanged historical Photius rows without changing their readings."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from repair_photius_index import CORPUS, ROOT, generate, input_bytes, is_index_locus

REPORT = Path("data/audits/photius-historical-apparatus.json")
PATTERNS = {
    "latin_editorial_operator": r"(?<![A-Za-z])(?:om|add|corr|cf|del)\b\.?",
    "latin_page_reference": r"(?<![A-Za-z])p\.\s*\d+",
    "numbered_lemma_bracket": r"(?<!\d)\d{1,3}[.,]\s*\d{1,3}\.\s*[^\n]{0,80}\]",
    "literal_note_markup": r"</?note(?:\s|>)",
}
PREFIX = "helladius_chrestomathia_photius_bekker_v2_"
SOURCE_SHA = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
SOURCE_URL = "https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build(root=ROOT, source_scan=None):
    original = input_bytes(root)
    body, _, _, index_audit = generate(original)
    historical = [json.loads(line) for line in body.splitlines()]
    from repair_photius_apparatus import restore_legacy_bytes
    served_raw = restore_legacy_bytes((root / CORPUS).read_bytes(), root)
    served = [json.loads(line) for line in served_raw.splitlines()]
    retained_rows = [row for row in served if row["locus"].startswith(PREFIX) and not is_index_locus(row["locus"])]
    retained = {row["locus"]: row for row in retained_rows}
    if (len(retained_rows) != len(retained) or len(retained) != len(historical)
            or any(retained.get(row["locus"]) != row for row in historical)):
        raise ValueError("The historical body changed; source review must be revisited")
    if source_scan is not None and sha(source_scan.read_bytes()) != SOURCE_SHA:
        raise ValueError("Unexpected source scan")
    candidates, pattern_counts = [], {}
    for name, pattern in PATTERNS.items():
        matching = [row for row in historical if re.search(pattern, row["text"])]
        pattern_counts[name] = {
            "rows": len(matching),
            "pages": len({row["locus"].rsplit(".", 1)[0] for row in matching}),
        }
    for row in historical:
        signals = [name for name, pattern in PATTERNS.items() if re.search(pattern, row["text"])]
        if signals:
            candidates.append({"locus": row["locus"], "signals": signals, "original_text": row["text"]})
    confirmed = [row for row in historical if re.fullmatch(PREFIX + r"0069\.4[0-9]", row["locus"])]
    if len(confirmed) != 10:
        raise ValueError("The source-reviewed block changed")
    return {
        "schema_version": 1,
        "work": "photius.bibliotheca",
        "scope": "Unchanged historical edition rows after index separation; fresh additions are outside this screen.",
        "source_snapshot_sha256": sha(original),
        "historical_body_sha256": sha(body),
        "historical_rows": len(historical),
        "historical_pages": len({row["locus"].rsplit(".", 1)[0] for row in historical}),
        "preserved_index_rows_outside_scope": index_audit["index_rows"],
        "source_scan": {"url": SOURCE_URL, "sha256": SOURCE_SHA, "pdf_page": 69, "printed_page": 334},
        "confirmed_apparatus": {
            "reviewed_at": "2026-10-18T06:56:27Z",
            "rows": len(confirmed),
            "text_characters": sum(len(row["text"]) for row in confirmed),
            "greek_letter_runs_including_sigla": sum(len(re.findall(r"[\u0370-\u03ff\u1f00-\u1fff]+", row["text"])) for row in confirmed),
            "evidence": "Visual comparison against the smaller critical apparatus below both main Greek columns on the pinned PDF page. The preceding body ends at row 39; rows 40-49 contain line references, variant readings, witness sigla, and Latin editorial operators.",
            "original_rows": confirmed,
            "qualification": "Confirmed lower bound, not the total apparatus in this edition.",
        },
        "candidate_screen": {
            "patterns": PATTERNS,
            "by_pattern": pattern_counts,
            "rows": len(candidates),
            "pages": len({row["locus"].rsplit(".", 1)[0] for row in candidates}),
            "qualification": "Candidates only, not a measured apparatus total. False positives and mixed body/apparatus rows require occurrence-level scan review. Apparatus without these signals is not counted. Do not delete candidates by pattern.",
            "candidates": candidates,
        },
        "changes_made": [],
        "generated_by": "scripts/audit_photius_apparatus.py",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-scan", type=Path, help="Optionally verify the downloaded source PDF hash")
    args = parser.parse_args()
    result = build(args.root, args.source_scan)
    path, raw = args.root / REPORT, encode(result)
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    elif args.check and (not path.exists() or path.read_bytes() != raw):
        parser.exit(1, "Historical Photius apparatus audit drift\n")
    print(json.dumps({"confirmed_rows": result["confirmed_apparatus"]["rows"],
                      "candidate_rows": result["candidate_screen"]["rows"],
                      "candidate_pages": result["candidate_screen"]["pages"]}))
