#!/usr/bin/env python3
"""Admit the pinned DCLP 63141 edition without flattening its critical markup.

The unchanged EpiDoc in data/pilots/dclp63141/ is the authoritative source.
--apply and --check regenerate all artifacts from it; --undo removes only an
unchanged generated admission. Shared corpus metadata is rebuilt separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from critical_text import SCHEMA, annotate, finalize_tokens, render_html
from prepare_epidoc_pilot import NS, prepare

ROOT = Path(__file__).resolve().parents[1]
SLUG = "anonymous.p-herc-1026"
EDITION = "dclp63141-35b5e227"
PILOT = ROOT / "data/pilots/dclp63141"
SOURCE_SHA256 = "cd7cc2f997569f9469b7e99b52d1481cc8607ad7fcd2c791a2e3af3b0e8fcc25"
REVISION = "35b5e2279ad29c44824f6dc60d9fc748dc109305"
SOURCE_URL = f"https://raw.githubusercontent.com/papyri/idp.data/{REVISION}/DCLP/63/63141.xml"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def generate(source=PILOT / "source.xml"):
    raw = source.read_bytes()
    if digest(raw) != SOURCE_SHA256:
        raise ValueError("DCLP source differs from the reviewed revision")
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory)
        manifest = prepare(source, destination, source_url=SOURCE_URL, revision=REVISION)
        rows = [annotate(json.loads(line)) for line in (destination / "passages.jsonl").read_text().splitlines()]
        pilot_rows = (destination / "passages.jsonl").read_bytes()
        pilot_manifest = (destination / "manifest.json").read_bytes()
    xml = ET.fromstring(raw)
    events = []
    for event in xml.findall(".//t:custEvent", NS):
        events.append({"attributes": dict(event.attrib),
                       "references": [dict(graphic.attrib) for graphic in event.findall("t:graphic", NS)]})
    inventory = [" ".join(node.itertext()).strip() for node in xml.findall(".//t:idno[@type='invNo']", NS)]
    for row in rows:
        correspondence = {value for part in row["textparts"] for value in part["attributes"].get("corresp", "").split()}
        row.update({"urn": SLUG, "edition": EDITION, "source": "dclp",
                    "license": "CC-BY-3.0", "language": "grc", "source_url": SOURCE_URL,
                    "critical_markup": {"schema": SCHEMA, "source_sha256": SOURCE_SHA256,
                                        "source_path": "data/pilots/dclp63141/source.xml"},
                    "physical_refs": {"document": "P.Herc. 1026", "dclp": "63141",
                                      "textparts": row["textparts"], "line_attributes": row["line_attributes"],
                                      "custody_events": [event for event in events if correspondence.intersection(event["attributes"].get("corresp", "").split())]}})
    finalize_tokens(rows)
    payload = ("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode()
    manifest.update({"status": "served-critical-edition", "work": SLUG, "edition": EDITION,
                     "author": "anonymous", "author_name": "Anonymous",
                     "edition_name": "Digital Corpus of Literary Papyri 63141",
                     "provider": "dclp", "edition_identifiers": {"trismegistos": "63141", "ldab": "4345"},
                     "physical_citation_scheme": "column.line",
                     "language": "grc", "document_url": "https://papyri.info/dclp/63141",
                     "inventory_identifiers": inventory, "critical_markup_schema": SCHEMA,
                     "source_path": "data/pilots/dclp63141/source.xml",
                     "corpus_path": f"data/corpus/{SLUG}.jsonl",
                     "reader_path": "data/critical_editions/dclp63141/reader.html",
                     "source_editors": ["Vincenzo Damiani", "Holger Essler", "Antonia Di Tuccio", "Marzia D'Angelo"],
                     "counts": {"lines": len(rows), "surface_tokens": sum(len(r["tokens"]) for r in rows),
                                "lexical_tokens": sum(t["lexical_eligible"] for r in rows for t in r["tokens"]),
                                "unselected_spans": sum(not s["selected"] for r in rows for s in r["spans"])},
                     "corpus_sha256": digest(payload),
                     "token_policy": "Offsets are Unicode code points in reading_text. Surface tokens retain editorial status and source span IDs. Gaps produce no tokens. Unclear, supplied, apograph, corrected, variant, gap-adjacent, and line-fragment tokens do not contribute to analysis_text or lexical frequencies. Null lemma/analysis means unattested, not automatic annotation.",
                     "generated_by": "scripts/ingest_dclp63141.py"})
    audit = {"schema_version": 1, "operation": "admit-critical-edition", "work": SLUG,
             "date": "2026-10-18", "source_url": SOURCE_URL, "source_sha256": SOURCE_SHA256,
             "corpus_sha256": digest(payload), "text_corrections": [],
             "evidence": "The pinned source EpiDoc explicitly selects lem/corr readings and records the rejected rdg/sic, unclear letters, restorations, apograph evidence, gaps, line breaks, and physical references. No reading has been corrected or normalized.",
             "reversal": "Run scripts/ingest_dclp63141.py --undo to remove the unchanged admitted work and reader. The original EpiDoc stays in data/pilots/dclp63141/source.xml; --format tei exports its exact bytes. Rebuild shared corpus metadata after removal.",
             "generated_by": "scripts/ingest_dclp63141.py"}
    artifacts = {f"data/corpus/{SLUG}.jsonl": payload,
                 "data/pilots/dclp63141/passages.jsonl": pilot_rows,
                 "data/pilots/dclp63141/manifest.json": pilot_manifest,
                 "data/critical_editions/dclp63141/manifest.json": encoded(manifest),
                 "data/critical_editions/dclp63141/reader.html": render_html(rows, manifest).encode(),
                 "data/corpus_changes/dclp63141/changes.json": encoded(audit)}
    return rows, manifest, artifacts


def apply(artifacts, root=ROOT):
    for relative, raw in artifacts.items():
        path = root / relative
        # Existing payloads can only be replaced by reproducing this admission.
        if path.exists() and relative.startswith("data/corpus/") and path.read_bytes() != raw:
            audit_path = root / "data/corpus_changes/dclp63141/changes.json"
            audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
            if digest(path.read_bytes()) != audit.get("corpus_sha256"):
                raise ValueError("Refusing to overwrite an independently edited critical edition")
    for relative, raw in artifacts.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def undo(artifacts, root=ROOT):
    targets = {path: raw for path, raw in artifacts.items()
               if not path.startswith("data/pilots/") and not path.startswith("data/corpus_changes/")}
    for relative, raw in targets.items():
        path = root / relative
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("Cannot undo a critical edition changed since admission")
    for relative in targets:
        (root / relative).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--undo", action="store_true")
    parser.add_argument("--format", choices=("jsonl", "html", "tei"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if bool(args.format) != bool(args.out):
        parser.error("--format and --out are required together")
    if args.out and args.out.resolve().is_relative_to((ROOT / "data").resolve()):
        parser.error("Use --apply for repository artifacts; exports need a separate destination")
    rows, manifest, artifacts = generate()
    if args.apply:
        apply(artifacts)
    if args.check:
        drift = [path for path, raw in artifacts.items() if not (ROOT / path).exists() or (ROOT / path).read_bytes() != raw]
        if drift:
            parser.exit(1, "Critical edition drift: " + ", ".join(drift) + "\n")
    if args.undo:
        undo(artifacts)
    if args.out:
        exports = {"jsonl": artifacts[f"data/corpus/{SLUG}.jsonl"],
                   "html": artifacts["data/critical_editions/dclp63141/reader.html"],
                   "tei": (PILOT / "source.xml").read_bytes()}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(exports[args.format])
    print(json.dumps({"work": SLUG, **manifest["counts"], "corpus_sha256": manifest["corpus_sha256"]}))


if __name__ == "__main__":
    main()
