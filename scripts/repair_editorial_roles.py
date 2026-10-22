#!/usr/bin/env python3
"""Separate Herodas and Hipponax editorial material with literal replay and undo.

The review changes source roles and boundaries, not Greek spellings. Every
original row, excluded span, citation destination, and source is archived.
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

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/editorial-role-review"
ALIASES = "data/passage_aliases.json"
WORKS = ("herodas.mimiambi", "hipponax.fragmenta")
PRIMARY = {work: f"data/corpus/{work}.jsonl" for work in WORKS}
RETAINED = {WORKS[0]: "data/paratext/herodas-headlam-knox.jsonl",
            WORKS[1]: "data/paratext/hipponax-brandt1888.jsonl"}
ORIGINAL_SHA256 = {
    WORKS[0]: "266915ced62896c3503c2ae0bb59bfc202a7e25dfe6c8ff1035313cdfaa00274",
    WORKS[1]: "6177c705abade229dbfcaa8f01bd555b46393d8f62c6f3853c6f5fc5dc89bf68",
}
CORE = {ALIASES, *PRIMARY.values(), *RETAINED.values()}
ORIGINAL_ALIASES_SHA256 = "4fe8acad64c0922a71d72a5434b34dd58ca044731d6ad6451b1a54edf891d74e"
HERODAS_SCAN_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
HIP_PONAX_TEI_SHA256 = "82415a5b06330fc223aa5d15080b078637ff6eb354efeef2ec7b85019be090b7"
SOURCE_FILES = {"source-herodas.pdf": HERODAS_SCAN_SHA256,
                "source-hipponax.xml": HIP_PONAX_TEI_SHA256}
QUALIFICATION = (
    "This review separates the source roles of the existing 136 Herodas rows and "
    "five Hipponax rows. It does not supply missing Herodas pages, certify every "
    "OCR spelling, resolve editorial restorations, or claim a complete corpus of "
    "either author's surviving fragments. Excluded material remains citable with "
    "its literal source text and attribution."
)
GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]+")
ANALYSIS_GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def recipe_pins():
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in
            ("repair_editorial_roles.py", "herodas_source_observations.py", "editorial_roles.py")}


def parse_original(work, raw):
    if sha(raw) != ORIGINAL_SHA256[work]:
        raise ValueError("Editorial role review original pin changed: " + work)
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if (len(rows) != (136 if work == WORKS[0] else 5)
            or len({row["locus"] for row in rows}) != len(rows)
            or any(row["urn"] != work for row in rows)):
        raise ValueError("Editorial role review row identities changed: " + work)
    return rows


def marker(work):
    return {"schema_version": 1, "authority": f"{AUDIT}/changes.json", "work": work}


def compile_herodas(rows, review):
    """Partition complete literal character spans; never correct a spelling."""
    from herodas_source_observations import build_source_review
    if review != build_source_review(rows, reviewed_at=review["reviewed_at"]):
        raise ValueError("Herodas packet differs from the checked source observations")
    decisions = review["rows"]
    if [item["locus"] for item in decisions] != [row["locus"] for row in rows]:
        raise ValueError("Herodas source review does not account for every original row")
    primary, retained, records, aliases = [], [], [], {}
    for row, decision in zip(rows, decisions, strict=True):
        if row["text"] != decision["original_text"]:
            raise ValueError("Herodas row lost its literal text preimage")
        cursor = 0
        for part in decision["spans"]:
            if (part["start"] != cursor or not cursor < part["end"] <= len(row["text"])
                    or part["text"] != row["text"][cursor:part["end"]]
                    or type(part["lexical_eligible"]) is not bool):
                raise ValueError("Herodas source spans overlap, drop text, or change a reading")
            cursor = part["end"]
        if cursor != len(row["text"]):
            raise ValueError("Herodas source spans do not cover their complete original text")
        kept = [part for part in decision["spans"] if part["lexical_eligible"]]
        excluded = [part for part in decision["spans"] if not part["lexical_eligible"]]
        body = " ".join(part["text"].strip() for part in kept if part["text"].strip())
        corrected = None
        if body:
            corrected = dict(row)
            if excluded:
                corrected.update(text=body, editorial_role_review=marker(WORKS[0]),
                    source_spans=[{key: part[key] for key in ("start", "end", "role")}
                                  for part in kept])
            primary.append(corrected)
        routed = []
        for ordinal, part in enumerate(excluded, 1):
            locus = row["locus"] if not body else f"{row['locus']}.editorial.{ordinal}"
            item = dict(row, locus=locus, text=part["text"], **{"class": "edition-apparatus"},
                lang="mul", editorial_role=part["role"], original_locus=row["locus"],
                source_char_range=[part["start"], part["end"]],
                editorial_role_review=marker(WORKS[0]),
                role_evidence=part.get("evidence", decision.get("evidence")),
                why_not_served="Headlam–Knox edition heading, speaker label, apparatus, or commentary; not Herodas's authorial verse.")
            retained.append(item); routed.append(item)
        target = ({"path": PRIMARY[WORKS[0]], "slug": WORKS[0], "locus": row["locus"]}
                  if body else {"path": RETAINED[WORKS[0]], "locus": row["locus"]})
        aliases[row["locus"]] = target
        records.append({"work": WORKS[0], "locus": row["locus"], "original_row": row,
            "original_text": row["text"], "corrected_text": body,
            "corrected_row": corrected, "retained_rows": routed, "destination": target,
            "source_spans": decision["spans"], "evidence": decision.get("evidence"),
            "reviewed_at": review["reviewed_at"]})
    return primary, retained, records, aliases


def build_outputs(before, review):
    from editorial_roles import partition_editorial_rows
    originals = {work: parse_original(work, before[PRIMARY[work]].encode()) for work in WORKS}
    primary, retained, records, aliases = compile_herodas(originals[WORKS[0]], review)
    hip_primary, hip_retained = partition_editorial_rows(WORKS[1], originals[WORKS[1]])
    destinations = {row["locus"]: {"path": PRIMARY[WORKS[1]], "slug": WORKS[1], "locus": row["locus"]}
                    for row in hip_primary}
    destinations.update({row["locus"]: {"path": RETAINED[WORKS[1]], "locus": row["locus"]}
                         for row in hip_retained})
    hip_by_locus = {row["locus"]: row for row in hip_retained}
    for row in originals[WORKS[1]]:
        outside = hip_by_locus.get(row["locus"])
        records.append({"work": WORKS[1], "locus": row["locus"], "original_row": row,
            "original_text": row["text"], "corrected_text": "" if outside else row["text"],
            "corrected_row": None if outside else row,
            "retained_rows": [outside] if outside else [], "destination": destinations[row["locus"]],
            "evidence": outside.get("editorial_role_authority") if outside else {"TEI_section": "frag128"},
            "reviewed_at": review["reviewed_at"]})
    if sha(before[ALIASES].encode()) != ORIGINAL_ALIASES_SHA256:
        raise ValueError("Editorial role review preceding citation aliases changed")
    old_aliases = json.loads(before[ALIASES])
    if any(work in old_aliases["aliases"] for work in WORKS):
        raise ValueError("Editorial work already has passage aliases; refusing replacement")
    old_aliases["aliases"].update({WORKS[0]: aliases, WORKS[1]: destinations})
    outputs = {PRIMARY[WORKS[0]]: jsonl(primary), RETAINED[WORKS[0]]: jsonl(retained),
        PRIMARY[WORKS[1]]: jsonl(hip_primary), RETAINED[WORKS[1]]: jsonl(hip_retained),
        ALIASES: (json.dumps(old_aliases, ensure_ascii=False, indent=2) + "\n").encode()}
    counts = {}
    for work, kept, outside in ((WORKS[0], primary, retained), (WORKS[1], hip_primary, hip_retained)):
        counts[work] = {"original_rows": len(originals[work]), "primary_rows": len(kept),
            "retained_spans": len(outside), "original_surface_tokens": sum(len(GREEK.findall(r["text"])) for r in originals[work]),
            "primary_surface_tokens": sum(len(GREEK.findall(r["text"])) for r in kept),
            "retained_surface_tokens": sum(len(GREEK.findall(r["text"])) for r in outside),
            "original_analysis_tokens": sum(len(ANALYSIS_GREEK.findall(r["text"])) for r in originals[work]),
            "primary_analysis_tokens": sum(len(ANALYSIS_GREEK.findall(r["text"])) for r in kept),
            "retained_analysis_tokens": sum(len(ANALYSIS_GREEK.findall(r["text"])) for r in outside)}
        if any(counts[work][f"original_{basis}_tokens"] != counts[work][f"primary_{basis}_tokens"]
               + counts[work][f"retained_{basis}_tokens"] for basis in ("surface", "analysis")):
            raise ValueError("Editorial role partition changed token boundaries")
    return outputs, records, counts


def _before(root, audit):
    raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["outputs"][f"{AUDIT}/before.json.gz"]:
        raise ValueError("Editorial role review preimage archive changed")
    before = json.loads(gzip.decompress(raw))
    if set(before) != CORE or set(audit["inputs"]) != CORE:
        raise ValueError("Editorial role review core paths changed")
    for path, value in before.items():
        if (sha(value.encode()) if value is not None else None) != audit["inputs"][path]:
            raise ValueError("Editorial role review literal preimage changed: " + path)
    for work in WORKS:
        parse_original(work, before[PRIMARY[work]].encode())
        if before[RETAINED[work]] is not None:
            raise ValueError("Editorial role review unexpected retained preimage")
    if sha(before[ALIASES].encode()) != ORIGINAL_ALIASES_SHA256:
        raise ValueError("Editorial role review preceding aliases differ from the published authority")
    return before


def verify(root, *, active=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("qualification") != QUALIFICATION
            or audit.get("recipe_sha256") != recipe_pins()):
        raise ValueError("Editorial role review authority or replay recipe changed")
    before = _before(root, audit)
    for name, expected in SOURCE_FILES.items():
        if sha((root / AUDIT / name).read_bytes()) != expected:
            raise ValueError("Editorial role review source changed: " + name)
    required = {*CORE, *(f"{AUDIT}/{name}" for name in SOURCE_FILES),
                f"{AUDIT}/before.json.gz", f"{AUDIT}/source-review.json", f"{AUDIT}/records.jsonl.gz"}
    if set(audit["outputs"]) != required:
        raise ValueError("Editorial role review output authority changed")
    for path, expected in audit["outputs"].items():
        if not active and path in CORE:
            continue
        if not (root / path).is_file() or sha((root / path).read_bytes()) != expected:
            raise ValueError("Editorial role review output changed: " + path)
    review = json.loads((root / AUDIT / "source-review.json").read_bytes())
    if audit.get("recorded_at") != review["reviewed_at"]:
        raise ValueError("Editorial role review timestamp changed")
    outputs, records, counts = build_outputs(before, review)
    archived_records = [json.loads(line) for line in gzip.decompress((root / AUDIT / "records.jsonl.gz").read_bytes()).splitlines()]
    if records != archived_records or counts != audit["counts"]:
        raise ValueError("Editorial role review records do not reproduce their partition")
    for path, raw in outputs.items():
        if sha(raw) != audit["outputs"][path] or active and (root / path).read_bytes() != raw:
            raise ValueError("Editorial role review literal replay differs: " + path)
    return audit, before, outputs


@lru_cache(maxsize=4)
def _projection_rows(root, signature):
    audit, before, outputs = verify(Path(root))
    records = [json.loads(line) for line in gzip.decompress(
        (Path(root) / AUDIT / "records.jsonl.gz").read_bytes()).splitlines()]
    return {record["locus"]: record for record in records if record["work"] == WORKS[0]}


def lexical_segments(row, root=None):
    """Keep positional contexts separate across an excluded source span."""
    root = Path(ROOT if root is None else root)
    paths = [*sorted(CORE), *(f"{AUDIT}/{name}" for name in SOURCE_FILES),
             f"{AUDIT}/changes.json", f"{AUDIT}/source-review.json",
             f"{AUDIT}/records.jsonl.gz", f"{AUDIT}/before.json.gz"]
    signature = tuple((path, (root / path).stat().st_size, (root / path).stat().st_mtime_ns)
                      for path in paths)
    record = _projection_rows(str(root), signature).get(row["locus"])
    if record is None or row != record["corrected_row"]:
        raise ValueError("Herodas lexical row differs from its reviewed role postimage")
    return [part["text"].strip() for part in record["source_spans"]
            if part["lexical_eligible"] and part["text"].strip()]


def undo(root):
    """Restore exact originals even after an evidence source is invalidated."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    before = _before(root, audit)
    current = {path: sha((root / path).read_bytes()) if (root / path).is_file() else None for path in CORE}
    if current == audit["inputs"]:
        return
    if current != {path: audit["outputs"][path] for path in CORE}:
        raise ValueError("Cannot undo modified editorial review core outputs")
    for path, value in before.items():
        if value is None:
            (root / path).unlink(missing_ok=True)
        else:
            (root / path).write_bytes(value.encode())


def run(root, mode, *, source_pdf=None, source_tei=None, reviewed_at=None):
    root = Path(root)
    audit_path = root / AUDIT / "changes.json"
    if audit_path.exists():
        if mode == "undo":
            undo(root); return
        audit = json.loads(audit_path.read_bytes())
        restored = all((sha((root / path).read_bytes()) if (root / path).is_file() else None) == expected
                       for path, expected in audit["inputs"].items())
        audit, before, outputs = verify(root, active=not restored)
        if restored and mode == "apply":
            for path, raw in outputs.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(raw)
            verify(root)
        print(json.dumps(audit["counts"], sort_keys=True)); return
    if mode in {"check", "undo"}:
        raise ValueError("Editorial role review has not been applied")
    before = {path: (root / path).read_text() if (root / path).exists() else None for path in CORE}
    if any(before[path] is not None for path in RETAINED.values()):
        raise ValueError("Editorial retained outputs already exist")
    from herodas_source_observations import build_source_review
    reviewed_at = reviewed_at or datetime.now(timezone.utc).isoformat()
    datetime.fromisoformat(reviewed_at)
    review = build_source_review(parse_original(WORKS[0], before[PRIMARY[WORKS[0]]].encode()), reviewed_at=reviewed_at)
    outputs, records, counts = build_outputs(before, review)
    print(json.dumps(counts, sort_keys=True))
    if mode != "apply":
        return
    sources = {"source-herodas.pdf": source_pdf, "source-hipponax.xml": source_tei}
    source_bytes = {name: Path(path).read_bytes() if path is not None else None for name, path in sources.items()}
    if any(raw is None or sha(raw) != SOURCE_FILES[name] for name, raw in source_bytes.items()):
        raise ValueError("Apply requires both exact reviewed sources")
    artifacts = {f"{AUDIT}/before.json.gz": gzip.compress(encoded(before), mtime=0),
        f"{AUDIT}/source-review.json": encoded(review),
        f"{AUDIT}/records.jsonl.gz": gzip.compress(jsonl(records), mtime=0),
        **{f"{AUDIT}/{name}": raw for name, raw in source_bytes.items()}}
    audit = {"schema_version": 1, "recorded_at": reviewed_at, "recipe_sha256": recipe_pins(),
        "generator": "scripts/repair_editorial_roles.py", "qualification": QUALIFICATION,
        "inputs": {path: sha(value.encode()) if value is not None else None for path, value in before.items()},
        "counts": counts, "outputs": {path: sha(raw) for path, raw in {**outputs, **artifacts}.items()},
        "reversal": "python3 scripts/repair_editorial_roles.py --undo; rebuild derived metadata"}
    for path, raw in {**artifacts, **outputs}.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
    audit_path.write_bytes(encoded(audit))
    verify(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--source-tei", type=Path)
    parser.add_argument("--reviewed-at")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"),
        source_pdf=args.source_pdf, source_tei=args.source_tei, reviewed_at=args.reviewed_at)


if __name__ == "__main__":
    main()
