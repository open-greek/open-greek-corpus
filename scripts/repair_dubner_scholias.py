#!/usr/bin/env python3
"""Separate two mislabeled Dübner volume extractions without losing a reading.

The original inputs remain literal, citable witnesses. Source-role decisions
precede collation; repeated scan leaves and constructed alternative lanes share
their original extraction's vote group. This is an edition-scope repair, not a
claim that the remaining OCR has been proofread.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/dubner-1855-scope"
EDITION = "dubner-1855-collated"
SECONDARY_EDITION = "dubner-1855-legacy-witnesses"
A = "scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii"
B = "platonius.fragmenta-de-comoedia-graeca"
A_PATH = f"data/corpus/{A}.jsonl"
A_SHA = "14736ad45cb79e53f6f6eb64160dc92d1aebe9b2f26ed28ae5ab2490834f38e3"
FRAGMENT = f"{AUDIT}/passage-aliases.json"
NETWORKS = f"{AUDIT}/word-networks.json.gz"
RECORDS = f"{AUDIT}/records.jsonl.gz"
COLLATIONS = f"{AUDIT}/collations.jsonl.gz"
PARATEXT = "data/paratext/dubner-1855-editorial.jsonl"
HELD = "data/ocr_witnesses/dubner-1855-unassigned.jsonl"
COMPARATIVE = "data/ocr_witnesses/dubner-1855-comparative-prolegomena.jsonl"
MIXED = "data/ocr_witnesses/dubner-1855-mixed-rows.jsonl"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
PAGE = re.compile(r"scholia_aristoph_dubner_(\d{4})\.(\d+)\Z")
PLAYS = (
    (43, 73, "acharnians", "Acharnians"),
    (74, 118, "equites", "Knights"),
    (119, 176, "nubes", "Clouds"),
    (177, 210, "vespae", "Wasps"),
    (211, 250, "pax", "Peace"),
    (251, 289, "aves", "Birds"),
    (290, 305, "lysistrata", "Lysistrata"),
    (306, 314, "thesmophoriazusae", "Thesmophoriazusae"),
    (315, 356, "ranae", "Frogs"),
    (357, 364, "ecclesiazusae", "Assemblywomen"),
    (365, 429, "plutus", "Wealth"),
)
QUALIFICATION = (
    "Source-supported work and text-role boundaries, followed by a word collation "
    "of two OCR extractions of Dübner's 1855 edition. They are not independent "
    "textual editions or independent model families. Every literal input and "
    "contrary reading remains available; unresolved readings do not enter scalar "
    "lexical counts. The merged Greek-word display is a reading projection, not "
    "a diplomatic transcription: original punctuation, Latin sigla, verse numbers, "
    "and row order remain in the citable secondary witnesses. Source omissions "
    "and OCR spellings have not been exhaustively repaired."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def local_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "data":
        raise ValueError("Unsafe Dübner artifact path: " + name)
    return Path(root) / path


def publish(root, outputs):
    """Stage all bytes before mutation, and restore preimages on an I/O failure."""
    root = Path(root)
    originals = {name: local_path(root, name).read_bytes()
                 if local_path(root, name).is_file() else None for name in outputs}
    staged = {}
    try:
        for name, raw in outputs.items():
            path = local_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if raw is not None:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(raw)
                    staged[name] = Path(handle.name)
        changed = []
        try:
            for name, raw in outputs.items():
                path = local_path(root, name)
                if raw is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(staged[name], path)
                changed.append(name)
        except OSError:
            for name in reversed(changed):
                path = local_path(root, name)
                if originals[name] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(originals[name])
            raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def recipe_pins():
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in (
        "repair_dubner_scholias.py", "dubner_source_observations.py",
        "dubner_witness_alignment.py", "dubner_dedup_observations.py",
        "capture_dubner_sources.py", "ocr_consensus.py")}


def input_pins():
    from dubner_witness_alignment import PINS
    from dubner_dedup_observations import EVIDENCE_PINS
    return {A_PATH: A_SHA, **PINS, **EVIDENCE_PINS}


def archived_inputs(root):
    """Return exact input bytes, independent of the current serving layout."""
    path = Path(root) / AUDIT / "before.json.gz"
    if path.exists():
        values = json.loads(gzip.decompress(path.read_bytes()))
        return {name: None if text is None else text.encode() for name, text in values.items()}
    return {name: (Path(root) / name).read_bytes() for name in input_pins()}


def check_inputs(before):
    for name, expected in input_pins().items():
        if before.get(name) is None or sha(before[name]) != expected:
            raise ValueError("Dübner input differs from its published source pin: " + name)


def source_records(root, before):
    from dubner_witness_alignment import source_rows
    check_inputs(before)
    output = []
    for row in map(json.loads, before[A_PATH].splitlines()):
        match = PAGE.fullmatch(row["locus"])
        if not match or row["urn"] != A:
            raise ValueError("Unexpected Toronto row identity")
        output.append({"id": A_PATH + "#" + row["locus"],
            "group": "dubner-1855-toronto", "path": A_PATH, "sha256": A_SHA,
            "row": row, "source_page": int(match.group(1)),
            "toronto_page": int(match.group(1)), "derived": False, "alternatives": []})
    output.extend(source_rows(Path(root), before))
    return output


def work_definitions():
    """Source-scoped expressions do not inherit an unverified modern recension."""
    definitions = {}
    for first, last, key, title in PLAYS:
        slug = A if key == "acharnians" else f"scholia-in-aristophanem.scholia-in-{key}-dubner-1855"
        definitions[key] = {"slug": slug, "author": "scholia-in-aristophanem",
            "author_name": "Scholia In Aristophanem",
            "title": f"Hypotheses and scholia to {title} (Dübner 1855)",
            "cts": "urn:cts:greekLit:tlg5014.tlg001" if key == "acharnians" else None,
            "scope": f"Dübner 1855, printed pages {first - 42}–{last - 42}; surviving OCR extraction"}
    from dubner_source_observations import PROLEGOMENA_UNITS
    for item in PROLEGOMENA_UNITS:
        key = item["work"]
        if key in definitions:
            continue
        slug = B if key == "platonius" else f"scholia-in-aristophanem.{key}-dubner-1855"
        definitions[key] = {"slug": slug,
            "author": "platonius" if key == "platonius" else "scholia-in-aristophanem",
            "author_name": "Platonius" if key == "platonius" else "Scholia In Aristophanem",
            "title": item["title"] + " (Dübner 1855 source witness)",
            "cts": "urn:cts:greekLit:tlg1615.tlg001" if key == "platonius" else None,
            "scope": item["evidence"]}
    from dubner_dedup_observations import FRONT_DISPOSITIONS
    for key, disposition in FRONT_DISPOSITIONS.items():
        if key in definitions:
            definitions[key]["admission"] = disposition
    return definitions


def partitions(records):
    """Expand the authored source decisions and reject uncovered characters."""
    from dubner_source_observations import build, build_harvard
    toronto = build([record["row"] for record in records if record["group"].endswith("toronto")])
    harvard = build_harvard([record["row"] for record in records
        if record["group"].endswith("harvard") and not record["derived"]])
    from dubner_source_observations import PLAY_HEADING_LOCI
    output = {}
    for record in records:
        row, page = record["row"], record["toronto_page"]
        if page is not None and page < 43:
            parts = toronto[row["locus"]] if record["group"].endswith("toronto") else harvard[row["locus"]]
        elif page is not None and 43 <= page <= 429:
            work = next(key for first, last, key, _ in PLAYS if first <= page <= last)
            parts = [{"start": 0, "end": len(row["text"]), "work": work,
                "role": "hypotheses-and-scholia", "lexical_eligible": True,
                "evidence": f"toronto-pdf-{page:04}; verified printed-page concordance"}]
            if row["locus"] in PLAY_HEADING_LOCI["toronto" if record["group"].endswith("toronto") else "harvard"]:
                parts[0].update(role="edition-heading", lexical_eligible=False)
        else:
            role = "critical-annotation" if page is not None and 431 <= page <= 656 else "editorial-index-or-front-matter"
            parts = [{"start": 0, "end": len(row["text"]), "work": "editorial-material",
                "role": role, "lexical_eligible": False,
                "evidence": "Dübner edition section and source-specific page inventory"}]
        cursor = 0
        for part in parts:
            if (part["start"] != cursor or not cursor < part["end"] <= len(row["text"])
                    or type(part["lexical_eligible"]) is not bool):
                raise ValueError("Incomplete or overlapping Dübner source-role partition: " + record["id"])
            cursor = part["end"]
        if cursor != len(row["text"]):
            raise ValueError("A Dübner source-role partition lost literal text")
        output[record["id"]] = parts
    return output


def build(root, before, *, recorded_at):
    from ocr_consensus import merge_witnesses, compact_corpus_consensus
    records = source_records(root, before)
    roles = partitions(records)
    definitions = work_definitions()
    raw_outputs, group_inputs, changes = defaultdict(list), defaultdict(list), []
    aliases = {A: {}, B: {}}
    for record in records:
        row, parts = record["row"], roles[record["id"]]
        destinations = []
        for index, part in enumerate(parts):
            text = row["text"][part["start"]:part["end"]]
            key = part["work"]
            eligible = part["lexical_eligible"]
            definition = definitions.get(key)
            if eligible and definition is None:
                raise ValueError("A historical Dübner region lacks a source-backed identity: " + key)
            slug = definition["slug"] if definition else None
            admission = definition.get("admission", {}) if definition else {}
            comparative = eligible and admission.get("admission") in {"comparative", "secondary"}
            if comparative:
                path = COMPARATIVE
                current = None
            elif eligible:
                path = f"data/corpus_secondary/{slug}.jsonl"
                current = {"slug": slug, "path": f"data/corpus/{slug}.jsonl",
                    "locus": f"dubner1855.{record['toronto_page']:04d}"}
                group_inputs[(key, record["toronto_page"], record["group"], record["path"], record["source_page"], record["derived"])].append(
                    {"record": record, "part": part, "text": text})
            else:
                path = HELD if part["role"] == "unresolved-diagram" else PARATEXT
                current = None
            if record["derived"]:
                continue  # a constructed comparison lane is not a new citable occurrence
            locus = row["locus"] if len(parts) == 1 else f"{row['locus']}.part.{index + 1}"
            routed = dict(row, locus=locus, edition=SECONDARY_EDITION,
                original_locus=row["locus"], original_work=row["urn"], original_edition=row["edition"],
                source_char_range=[part["start"], part["end"]], text=text,
                source_role=part["role"], source_role_evidence=part["evidence"],
                witness_group=record["group"], source_pdf_page=record["source_page"],
                dubner_source_scope={"authority": AUDIT + "/changes.json"})
            routed.pop("cts", None)
            if eligible and not comparative:
                routed["urn"] = slug
                if definition.get("cts"):
                    routed["cts"] = definition["cts"]
                target = {"path": path, "slug": slug, "storage": "secondary", "locus": locus,
                    "current": current}
            else:
                routed.update(urn=slug if comparative else "dubner-1855.edition-witness",
                    lang="grc" if comparative else "mul",
                    **{"class": "comparative-historical-witness" if comparative else
                       "unresolved-source-region" if path == HELD else "edition-apparatus"})
                if comparative:
                    routed.update(source_work_key=key, source_work_title=definition["title"],
                        admission=admission)
                    if admission.get("target"):
                        routed["canonical_target"] = {"slug": admission["target"],
                            "loci": admission["target_loci"], "storage": "primary"}
                target = {"path": path, "locus": locus}
            raw_outputs[path].append(routed)
            destinations.append(target)
        if not record["derived"]:
            if len(destinations) != 1:
                full = dict(row, urn="dubner-1855.edition-witness", lang="mul",
                    source_role="mixed-historical-and-editorial", partition_destinations=destinations,
                    **{"class": "literal-mixed-source-witness"})
                full.pop("cts", None)
                raw_outputs[MIXED].append(full)
                target = {"path": MIXED, "locus": row["locus"], "partitions": destinations}
            else:
                target = destinations[0]
            old = row["urn"]
            existing = aliases[old].get(row["locus"])
            if existing is not None:
                raise ValueError("Two original inputs claim the same historical locus")
            aliases[old][row["locus"]] = target
            changes.append({"input": record["path"], "input_sha256": record["sha256"],
                "original_row": row, "original_text": row["text"],
                "corrected_text": row["text"], "source_partitions": parts,
                "destinations": destinations, "recorded_at": recorded_at})
    by_page = defaultdict(list)
    for (work, page, group, path, scan_page, derived), pieces in sorted(group_inputs.items()):
        pieces.sort(key=lambda item: tuple(map(int, item["record"]["row"]["locus"].rsplit("_", 1)[1].split(".")[:2])))
        text = "\n".join(piece["text"] for piece in pieces)
        lane = {"id": f"{group}:{path}:{scan_page:04d}:{'fallback' if derived else 'literal'}",
            "vote_group": group, "artifact_sha256": sha(encoded({"input": pieces[0]["record"]["sha256"],
                "loci": [piece["record"]["id"] for piece in pieces], "text": text})),
            "text": text, "source_rows": [piece["record"]["id"] for piece in pieces],
            "derived": derived,
            "qualification": "Constructed rejected-fallback lane; not an independent reading" if derived else "Retained OCR witness"}
        by_page[(work, page)].append(lane)
    networks, primary, summaries, collations = {}, defaultdict(list), {}, []
    for (work, page), witnesses in sorted(by_page.items()):
        definition = definitions[work]
        result = merge_witnesses(witnesses)
        key = f"{work}:{page:04d}"
        networks[key] = result
        collations.append({"key": key, "recorded_at": recorded_at,
            "original_texts": [{"witness": w["id"], "text": w["text"],
                "sha256": sha(w["text"].encode()), "source_rows": w["source_rows"],
                "derived": w["derived"]} for w in witnesses],
            "corrected_text": result["text"], "analysis_text": result["analysis_text"],
            "evidence": {"source_capture": AUDIT + "/source-evidence.json",
                "word_network": NETWORKS, "key": key},
            "qualification": QUALIFICATION})
        compact = compact_corpus_consensus(result, {"path": NETWORKS, "key": key})
        row = {"urn": definition["slug"], "locus": f"dubner1855.{page:04d}",
            "source": "ocr", "license": "PD", "lang": "grc", "edition": EDITION, **compact,
            "source_printed_page": page - 42 if page >= 43 else None,
            "source_pdf_page": page, "corrections": ["structural", "collation"],
            "dubner_scope_review": {"authority": AUDIT + "/changes.json", "network_key": key}}
        if definition.get("cts"):
            row["cts"] = definition["cts"]
        primary[definition["slug"]].append(row)
    from dubner_witness_alignment import B_PRIMARY, B_CROSSWORK, B_DUPLICATE
    outputs = {B_PRIMARY: None, B_CROSSWORK: None, B_DUPLICATE: None}
    outputs.update({path: jsonl(rows) for path, rows in raw_outputs.items()})
    for slug, rows in primary.items():
        outputs[f"data/corpus/{slug}.jsonl"] = jsonl(rows)
        counts = Counter()
        for row in rows:
            counts.update(row["ocr_consensus"]["counts"])
        summaries[slug] = {"primary_rows": len(rows),
            "secondary_rows": len(raw_outputs[f"data/corpus_secondary/{slug}.jsonl"]),
            "analysis_tokens": sum(len(GREEK.findall(row["analysis_text"])) for row in rows),
            "surface_tokens": sum(len(GREEK.findall(row["text"])) for row in rows),
            "counts": dict(counts)}
    outputs[FRAGMENT] = encoded({"schema_version": 1, "aliases": aliases,
        "retired_sources": {B: "ogc002861"}})
    outputs[NETWORKS] = gzip.compress(encoded(networks), mtime=0)
    outputs[RECORDS] = gzip.compress(jsonl(changes), mtime=0)
    outputs[COLLATIONS] = gzip.compress(jsonl(collations), mtime=0)
    if A not in primary:
        raise ValueError("Acharnians must retain its actual surviving scholia")
    return outputs, summaries, {"original_rows": len(changes),
        "original_primary_rows": sum(len(before[name].splitlines()) for name in (A_PATH, B_PRIMARY)),
        "original_primary_greek_tokens": sum(len(GREEK.findall(json.loads(line)["text"]))
            for name in (A_PATH, B_PRIMARY) for line in before[name].splitlines()),
        "partition_rows": sum(len(record["source_partitions"]) for record in changes),
        "mixed_original_rows": len(raw_outputs.get(MIXED, [])),
        "historical_witness_rows": sum(len(rows) for path, rows in raw_outputs.items() if "/corpus_secondary/" in path),
        "editorial_rows": len(raw_outputs.get(PARATEXT, [])),
        "held_historical_rows": len(raw_outputs.get(HELD, [])),
        "comparative_historical_rows": len(raw_outputs.get(COMPARATIVE, [])),
        "constructed_fallback_rows": sum(record["derived"] for record in records),
        "primary_rows": sum(map(len, primary.values())), "works": len(primary),
        "analysis_tokens": sum(item["analysis_tokens"] for item in summaries.values()),
        "reading_statuses": dict(sum((Counter(item["counts"]) for item in summaries.values()), Counter()))}


def active(root):
    root = Path(root)
    path = root / AUDIT / "changes.json"
    if not path.exists():
        return False
    audit = json.loads(path.read_bytes())
    before = archived_inputs(root)
    # Every created, replaced, and deleted output participates in literal undo.
    # Restoring only the two original volumes must not hide residual primaries.
    return not all(((local_path(root, name).read_bytes() if local_path(root, name).is_file()
                     else None) == before[name]) for name in audit["outputs"])


def verify(root=ROOT, *, active_only=True, replay=False):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("inputs") != input_pins()
            or audit.get("recipe_sha256") != recipe_pins() or audit.get("qualification") != QUALIFICATION):
        raise ValueError("Dübner repair recipe or source qualification changed")
    before_raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(before_raw) != audit["before_sha256"]:
        raise ValueError("Dübner literal preimage archive changed")
    before = archived_inputs(root)
    check_inputs(before)
    capture_path = root / AUDIT / "source-evidence.json"
    if sha(capture_path.read_bytes()) != audit["source_capture_sha256"]:
        raise ValueError("Dübner source-capture authority changed")
    from capture_dubner_sources import check as check_capture
    capture = check_capture(root)
    if audit["sources"] != capture["sources"]:
        raise ValueError("Dübner source metadata differs from the reviewed captures")
    for item in capture["files"]:
        if sha(local_path(root, item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("Dübner source capture changed: " + item["path"])
    for name, expected in audit["outputs"].items():
        path = local_path(root, name)
        actual = sha(path.read_bytes()) if path.is_file() else None
        if active_only and actual != expected:
            raise ValueError("Dübner repaired output changed: " + name)
    if replay:
        outputs, summaries, counts = build(root, before, recorded_at=audit["recorded_at"])
        if set(outputs) != set(audit["outputs"]):
            raise ValueError("Dübner output inventory no longer reproduces")
        if summaries != audit["works"] or counts != audit["counts"]:
            raise ValueError("Dübner accounting no longer reproduces")
        for name, raw in outputs.items():
            if (sha(raw) if raw is not None else None) != audit["outputs"][name]:
                raise ValueError("Dübner literal replay differs: " + name)
        from dubner_dedup_observations import measurements
        if measurements(root, before) != audit["overlap_measurements"]:
            raise ValueError("Dübner overlap measurements no longer reproduce")
    return audit, before


def alias_fragment(root):
    root = Path(root)
    if not active(root):
        return None
    verify(root)
    fragment = json.loads((root / FRAGMENT).read_bytes())
    ledger = json.loads((root / "data/work_ids.json").read_bytes())["works"]
    if ledger.get("ogc002861", {}).get("slug") != B or ledger["ogc002861"]["status"] != "retired":
        raise ValueError("The retired Platonius identity must remain in its immutable ledger")
    return {**fragment,
        "authority": {"path": AUDIT + "/changes.json", "sha256": sha((root / AUDIT / "changes.json").read_bytes())}}


def metadata(root):
    root = Path(root)
    if not active(root):
        return {}
    audit, _ = verify(root)
    definitions = {entry["slug"]: entry for entry in work_definitions().values()}
    return {slug: {**definitions[slug], **counts, "edition": EDITION,
        "authority": {"path": AUDIT + "/changes.json", "sha256": sha((root / AUDIT / "changes.json").read_bytes())},
        "sources": audit["sources"], "qualification": QUALIFICATION}
        for slug, counts in audit["works"].items()}


@lru_cache(maxsize=2)
def _verified_rows(root, signature):
    audit, _ = verify(root)
    rows = {}
    for name in audit["outputs"]:
        if name.startswith("data/corpus/") and audit["outputs"][name] is not None:
            for row in map(json.loads, (Path(root) / name).read_bytes().splitlines()):
                rows[(row["urn"], row["locus"])] = row
    return rows


def validate_projection(row, root=ROOT):
    root = Path(root)
    authority = root / AUDIT / "changes.json"
    audit = json.loads(authority.read_bytes())
    capture_path = AUDIT + "/source-evidence.json"
    capture = json.loads((root / capture_path).read_bytes())
    paths = [AUDIT + "/changes.json", AUDIT + "/before.json.gz", capture_path,
             *audit["outputs"], *(entry["path"] for entry in capture["files"])]
    paths += ["scripts/" + name for name in recipe_pins()]
    signature = tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
                      if (root / name).is_file() else (name, None, None) for name in paths)
    expected = _verified_rows(str(root), signature).get((row["urn"], row["locus"]))
    if expected != row:
        raise ValueError("Dübner lexical projection differs from its checked admission")
    return row["analysis_text"]


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    existing = root / AUDIT / "changes.json"
    archive = root / AUDIT / "before.json.gz"
    if existing.exists() != archive.exists():
        raise ValueError("An orphaned Dübner authority or preimage archive cannot authorize an apply")
    if existing.exists() and active(root):
        raise ValueError("A Dübner repair is already active")
    before = archived_inputs(root)
    old = None
    if existing.exists():
        # Validate frozen authority before alignment, even while unapplied.
        # Source or recipe revisions require a new admission layer.
        old, _ = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Reapplying a frozen Dübner audit cannot change its timestamp")
        recorded_at = old["recorded_at"]
        for name in old["outputs"]:
            current = (root / name).read_bytes() if (root / name).exists() else None
            if current != before[name]:
                raise ValueError("Dübner reapply found a later change: " + name)
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, works, counts = build(root, before, recorded_at=recorded_at)
    # Save every overwritten file and every newly created destination before
    # publishing any output. Derived registry/index/frequency artifacts rebuild.
    for name in outputs:
        if name not in before:
            if local_path(root, name).exists():
                raise ValueError("Refusing to overwrite an unowned Dübner destination: " + name)
            before[name] = None
    before_raw = gzip.compress(encoded({name: None if raw is None else raw.decode() for name, raw in before.items()}), mtime=0)
    evidence = root / AUDIT / "source-evidence.json"
    if not evidence.exists():
        raise ValueError("Capture and review the pinned Dübner source boundaries first")
    from capture_dubner_sources import check as check_capture
    capture = check_capture(root)
    sources = capture["sources"]
    for item in capture["files"]:
        path = item["path"]
        if sha(local_path(root, path).read_bytes()) != item["sha256"]:
            raise ValueError("Dübner source capture changed: " + path)
    from dubner_dedup_observations import measurements
    audit = {"schema_version": 1, "recorded_at": recorded_at,
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/102",
        "recipe_sha256": recipe_pins(), "before_sha256": sha(before_raw),
        "inputs": input_pins(), "outputs": {name: sha(raw) if raw is not None else None for name, raw in outputs.items()},
        "source_capture_sha256": sha(evidence.read_bytes()), "sources": sources,
        "works": works, "counts": counts, "qualification": QUALIFICATION,
        "overlap_measurements": measurements(root, before)}
    if old is not None and encoded(audit) != existing.read_bytes():
        raise ValueError("Reapplying Dübner must reproduce the complete frozen audit exactly")
    publish(root, {**outputs, AUDIT + "/before.json.gz": before_raw,
                   AUDIT + "/changes.json": encoded(audit)})
    return audit


def undo(root=ROOT):
    """Literal undo needs only frozen pre/postimages, even if evidence is lost."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["before_sha256"]:
        raise ValueError("Dübner undo archive changed")
    before = json.loads(gzip.decompress(raw))
    for name, expected in audit["outputs"].items():
        actual = sha((root / name).read_bytes()) if (root / name).is_file() else None
        if actual != expected:
            raise ValueError("Refusing to overwrite a later Dübner output: " + name)
    publish(root, {name: None if before[name] is None else before[name].encode()
                   for name in audit["outputs"]})


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
        print("Dübner original source files restored exactly")
    elif args.apply:
        print(json.dumps(apply(args.root, recorded_at=args.recorded_at)["counts"], sort_keys=True))
    else:
        print(json.dumps(verify(args.root, replay=True)[0]["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
