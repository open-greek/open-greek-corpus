#!/usr/bin/env python3
"""Replay scan-checked book citations for Pappus and Apollonius.

Text and document order are unchanged. Original First1K destinations remain
available through edition-qualified citation schemes, including collisions
between a former book number and a corrected book number.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/mathematical-citations-43-44"
ALIASES = "data/citation_aliases.json"
TEXT_RULES = "data/corpus_text_corrections.json"
EDITION = "1st1K-grc1"
RULES = {
    "pappus-mathematics.synagoge": {
        "books": {"1": "2", "2": "3", "3": "4", "4": "5"},
        "scheme": "pappus-first1k-book-attributes",
        "corpus_sha256": "3ca2c31f5ed68da0929451312d3de552e20f9d975a7f06618f8e17f70e61a043",
        "tei_sha256": "97c19de67ffa6f15ca01bb0f47eae655354d4e1e3bfb7d9fb8837f572d40fe78",
        "tei_url": "https://github.com/OpenGreekAndLatin/First1KGreek/blob/master/data/tlg2032/tlg001/tlg2032.tlg001.1st1K-grc1.xml",
        "scan_url": "https://archive.org/details/pappialexandrin00hultgoog",
        "pdf_sha256": "5e665adaedc86e15393dfafd8fbef1c67f8fc1b1bf671bb40e190e4a036414f2",
        "checked_boundaries": [
            {"source_book": "1", "printed_book": "2", "pdf_page": 35, "printed_page": 2},
            {"source_book": "2", "printed_book": "3", "pdf_page": 63, "printed_page": 30},
            {"source_book": "3", "printed_book": "4", "pdf_page": 211, "printed_page": 178},
            {"source_book": "4", "printed_book": "5", "pdf_page": 337, "printed_page": 304},
        ],
        "evidence": "Manual inspection of Hultsch volume I title (PDF12: Librorum II, III, IV, V reliquiae), the surviving opening at printed2, and the Greek running/book headings at printed30,178,304. The unheaded first division is the surviving part of BookII, not BookI. Chapters retain the source's numbers; no lost text is reconstructed.",
    },
    "apollonius-geom.conica": {
        "book": "4",
        "scheme": "apollonius-first1k-unqualified-sections",
        "corpus_sha256": "13a58ea70cd050f803334d7d9ca2ee0d89e449030ac1597ade22eb16aabcba6e",
        "tei_sha256": "6d6d5bb17dea43ec238e777fb413af56137e49dcd76e8e02dbc515ae0a5db0eb",
        "tei_url": "https://github.com/OpenGreekAndLatin/First1KGreek/blob/master/data/tlg0550/tlg001/tlg0550.tlg001.1st1K-grc1.xml",
        "scan_url": "https://archive.org/details/apolloniipergaei02apoluoft",
        "pdf_sha256": "ab8f0c2dd0f4a13f16ba7415e66f571161c08a5004477b0305a6d2016779a9c0",
        "checked_boundaries": [
            {"printed_book": "4", "pdf_page": 94, "printed_page": 2},
            {"source_section": "1", "pdf_page": 96, "printed_page": 4},
            {"source_section": "57", "pdf_page": 186, "printed_page": 94},
        ],
        "evidence": "Manual inspection of the Greek BookIV opening and epistle at printed2, proposition1 at printed4 and proposition57 at printed94. The facing Latin headings independently read Conicorum Liber IV. First1K's section headings alpha through nu-zeta are retained under BookIV; missing BooksI–III require volumeI, not an offset within this source.",
    },
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def validate_source(work, edition, source, path):
    if work in RULES and (edition, source) == (EDITION, "first1k"):
        if sha(Path(path).read_bytes()) != RULES[work]["tei_sha256"]:
            raise ValueError("Mathematical TEI changed; review its citation mapping again")


def remap_record(row):
    rule = RULES.get(row.get("urn"))
    if not rule or (row.get("edition"), row.get("source")) != (EDITION, "first1k"):
        return row
    if "source_citation" in row:
        raise ValueError("Mathematical source citations have already been mapped")
    old = row["locus"]
    if "book" in rule:
        if not old.isdigit() or not 1 <= int(old) <= 57:
            raise ValueError(f"Unreviewed Apollonius section: {old}")
        new = rule["book"] + "." + old
    else:
        book, separator, rest = old.partition(".")
        if book not in rule["books"]:
            raise ValueError(f"Unreviewed Pappus citation: {old}")
        new = rule["books"][book] + ("." + rest if separator else "")
    return dict(row, locus=new, source_citation={"scheme": rule["scheme"], "locus": old})


def route(raw):
    rows, aliases, changes = [], {}, []
    for line in raw.splitlines():
        row = json.loads(line)
        result = remap_record(row)
        if result is row:
            raise ValueError("Unreviewed mathematical source row")
        if row["locus"] in aliases:
            raise ValueError("Repeated mathematical source citation")
        aliases[row["locus"]] = {"slug": row["urn"],
            "path": f"data/corpus/{row['urn']}.jsonl", "locus": result["locus"]}
        changes.append({"work": row["urn"], "original_locus": row["locus"],
            "corrected_locus": result["locus"], "text_sha256": sha(row["text"].encode()),
            "text_changed": False, "evidence": RULES[row["urn"]]["scheme"]})
        rows.append(result)
    if len({r["locus"] for r in rows}) != len(rows):
        raise ValueError("The reviewed mapping creates a collision")
    return ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode(),
            aliases, changes)


def preserve_prior_text_rules(root, snapshot, configuration):
    """Keep previously audited accents reproducible at the original source loci."""
    work = "pappus-mathematics.synagoge"
    path = f"data/corpus/{work}.jsonl"
    rows = [json.loads(line) for line in snapshot[path].splitlines()]
    prior_paths = ["data/corpus_changes/nonfinal_grave_tranche_thirdparty.applied.json",
        "data/corpus_changes/nonfinal_grave_tranche_thirdparty.completing-2026-08-11.applied.json"]
    for prior_path in prior_paths:
        prior = json.loads((root / prior_path).read_text())
        block = next(b for b in prior["files"] if b["file"] == path)
        for edit in block["edits"]:
            row = rows[edit["index"]]
            for offset, original in edit["was"]:
                corrected = prior["substitutions"][original]
                if row["text"][offset:offset + len(corrected)] != corrected:
                    raise ValueError("Existing Pappus accent audit no longer matches")
                rule = {"work": work, "locus": row["locus"], "original": original,
                    "correction": corrected, "expected_occurrences": 1,
                    "evidence": f"Replay the existing decision in {prior_path}, row index {edit['index']}; apply at the First1K source locus before changing book numbers.",
                    "date": prior["date"], "audit_source": prior_path,
                    "reversible": "restore the original token recorded in the source audit"}
                if rule not in configuration["corrections"]:
                    configuration["corrections"].append(rule)
    return configuration


def run(root, mode):
    directory = root / AUDIT
    audit_path = directory / "changes.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        snapshots = json.loads(gzip.decompress((directory / "before.json.gz").read_bytes()))
        if mode == "undo":
            for path, expected in audit["outputs"].items():
                if (sha((root / path).read_bytes()) if (root / path).exists() else None) != expected:
                    raise ValueError(f"Output changed since repair; refusing to overwrite: {path}")
            for path, original in snapshots.items():
                if original is None:
                    (root / path).unlink(missing_ok=True)
                else:
                    (root / path).write_text(original)
            print("Restored exact mathematical citation inputs; rebuild derived reports.")
            return
        if audit["evidence"] != RULES:
            raise ValueError("Mathematical citation evidence changed")
        current_schemes = json.loads((root / ALIASES).read_text())["schemes"]
        for work, rule in RULES.items():
            path = f"data/corpus/{work}.jsonl"
            raw = snapshots[path].encode()
            if sha(raw) != rule["corpus_sha256"]:
                raise ValueError("Archived mathematical source changed")
            output, aliases, changes = route(raw)
            # Later independently sourced books may extend the same work.
            current = [json.loads(line) for line in (root / path).read_text().splitlines()]
            expected_rows = [json.loads(line) for line in output.splitlines()]
            if any(row not in current for row in expected_rows) or audit["changes"][work] != changes:
                raise ValueError(f"Mathematical corpus or audit differs from replay: {work}")
            if current_schemes[rule["scheme"]]["aliases"] != aliases:
                raise ValueError("Mathematical citation aliases differ from replay")
        current_rules = json.loads((root / TEXT_RULES).read_text())["corrections"]
        if any(rule not in current_rules for rule in audit["ingest_rules"]["corrections"]):
            raise ValueError("Previously audited accent decisions are missing")
        print("Verified every mathematical source citation; all text is unchanged.")
        return
    if mode in {"check", "undo"}:
        raise ValueError("The mathematical citation repair has not been applied")
    paths = [f"data/corpus/{w}.jsonl" for w in RULES] + [ALIASES, TEXT_RULES, "data/work_index.json"]
    snapshots = {p: (root / p).read_text() if (root / p).exists() else None for p in paths}
    schemes = json.loads(snapshots[ALIASES])
    changes = {}
    outputs = {}
    for work, rule in RULES.items():
        path = f"data/corpus/{work}.jsonl"
        raw = snapshots[path].encode()
        if sha(raw) != rule["corpus_sha256"]:
            raise ValueError(f"Mathematical corpus changed; review it again: {work}")
        output, aliases, changes[work] = route(raw)
        outputs[path] = output
        if rule["scheme"] in schemes["schemes"]:
            raise ValueError("Mathematical citation scheme already exists")
        schemes["schemes"][rule["scheme"]] = {"work": work, "source_edition": EDITION,
            "canonical_scheme": "book.section",
            "description": "First1K citations used through corpus-2026-10-18. Qualify historical citations with this scheme; current citations use the scan-checked book heading.",
            "aliases": aliases}
    print(f"Map {sum(len(v) for v in changes.values())} mathematical citations without changing text.")
    if mode != "apply":
        return
    configuration = preserve_prior_text_rules(root, snapshots, json.loads(snapshots[TEXT_RULES]))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "before.json.gz").write_bytes(gzip.compress(dump(snapshots), mtime=0))
    outputs[ALIASES] = dump(schemes)
    outputs[TEXT_RULES] = dump(configuration)
    for path, raw in outputs.items():
        (root / path).write_bytes(raw)
    import build_work_index
    build_work_index.build(write=True)
    outputs["data/work_index.json"] = (root / "data/work_index.json").read_bytes()
    audit_path.write_bytes(dump({"schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/repair_mathematical_citations.py", "evidence": RULES,
        "changes": changes, "ingest_rules": configuration,
        "reversal": "python3 scripts/repair_mathematical_citations.py --undo; rebuild derived reports",
        "outputs": {p: sha(raw) for p, raw in outputs.items()}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"))
