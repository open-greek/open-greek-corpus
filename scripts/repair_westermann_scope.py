#!/usr/bin/env python3
"""Reconstruct source-scoped Westermann biographies without changing a reading.

The former Marcellinus file is a whole anthology extraction. Every literal row
remains citable; printed work and editorial boundaries determine which exact
character ranges may enter primary lexical counts.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OLD = "marcellinus.vita-thucydidis"
PRIMARY = f"data/corpus/{OLD}.jsonl"
INPUT_SHA256 = "f981d2caff071cb9e88ffdf3784de725ff56a3b7a49de11a58d6b1d9180e2dd7"
EDITION = "westermann-1845-source-scoped"
AUDIT = "data/corpus_changes/westermann-1845-scope"
LITERAL = "data/ocr_witnesses/westermann-1845-original-rows.jsonl"
COMPARATIVE = "data/ocr_witnesses/westermann-1845-comparative.jsonl"
HELD = "data/ocr_witnesses/westermann-1845-uncertain.jsonl"
PARATEXT = "data/paratext/westermann-1845-editorial.jsonl"
FRAGMENT = AUDIT + "/passage-aliases.json"
RECORDS = AUDIT + "/records.jsonl.gz"
LOCUS = re.compile(r"marcellinus_westermann_(\d{4})\.(\d+)\Z")
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
QUALIFICATION = (
    "Printed work and editorial boundaries repair the historical whole-volume "
    "assignment. Every original row and exact character range remains available. "
    "Historical material already represented in another primary is comparative, "
    "not another lexical occurrence. Ambiguous text roles remain outside primary "
    "counts. This source-scope review does not certify unreviewed OCR spellings."
)


EVIDENCE_PINS = {
    "data/corpus/certamen-homeri-et-hesiodi.certamen-homeri-et-hesiodi.jsonl": "eb42409d53420a17843595b9e8a657fbfb36111ad055d761de362f984df38c5d",
    "data/corpus/dionysius-halicarnassensis-history.ad-ammaeum.jsonl": "29064922589595fedda14c7c2167d3729af5fa9f5466844fdfdb0e3091f9c6b3",
    "data/corpus/dionysius-halicarnassensis-history.de-dinarcho.jsonl": "3ec6fbff917e415e8708d0c3a2e18ed75489a7702a78cf33c3ffb64b09c7fd59",
    "data/corpus/dionysius-halicarnassensis-history.de-isaeo.jsonl": "98eb0795a73738bc205df9aa94f31630844e9f4aed00053f2fa8892abd1c7937",
    "data/corpus/dionysius-halicarnassensis-history.de-isocrate.jsonl": "7bd0c935bf310d9615f7f3e57a1b41978ddea71de12c3dd62fd98515545e6f39",
    "data/corpus/dionysius-halicarnassensis-history.de-lysia.jsonl": "115ef1d1685369374fb7d8f416f3e4e9de867b86ca705cc0aec15f0e1e056075",
    "data/corpus/kaibel-cgf-1899.volume-witness-r.jsonl": "c6f1dfa05739b357ec876bdda254fe76dd1a17dee2a160153b24ddd794994aa7",
    "data/corpus/photius.bibliotheca.jsonl": "64f37b6731e5d2429b865e499bb7919e3830f4ec7dfe31b192ce2552a27e6b58",
    "data/corpus/plutarchus.vitae-decem-oratorum-sp-832b-852e.jsonl": "5fae9f348c8b29abb085227e2aea54bd01e8e57eebac2a6a35c16065b6c0a166",
    "data/corpus/scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera.jsonl": "0635a7a4abaa22e760fdb8e71a55a4bcc294d07a52c080312a1eb3466792a55a",
    "data/corpus/scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera.jsonl": "1e20e9b5423e2ed14bc2e96ce564bca36a420590ed70c5b1292904bc8f2ab7ce",
    "data/corpus/scholia-in-demosthenem.scholia-demosthenem-dindorf-v8.jsonl": "d7911397bbea6f8d099f16dea492ee21841302e542436ff8807a485000bfe41e",
    "data/corpus/scholia-in-euripidem.vitae-euripidis.jsonl": "a45b6da04f31c2571fa9229d19f24bc28ea1753382d07c3ac22ed95797522f96",
    "data/corpus/scholia-in-isocratem.scholia-in-isocratem-scholia-vetera.jsonl": "886d952058aaf79b853fedab90acfa89699f94a5ea0ccf9927cb984af1c2192a",
    "data/corpus/scholia-in-nicandrum.scholia-et-glossae-in-nicandri-theriaca-scholia-vetera-et.jsonl": "0b810af18a09a64a1066e6f40846b9f39499abf44e23b07d6e93953821b50314",
    "data/corpus/scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora.jsonl": "fcc3010865660d3e1d94d0008b6e9b1ff8c3c863865c7e4f0d2be88dc12d7ce2",
    "data/corpus/scholia-in-theocritum.scholia-vetera-et-recentiora.jsonl": "96bc126f30b5f857da380d72ff90907994da4ed5f4e5d651d58502319e212234",
    "data/corpus/soranus.vita-hippocratis.jsonl": "4513abd8bdeaa51bbbc2fc8028d3e32d9c09130947b80a77d78a9755deb102eb",
    "data/corpus/suda.lexicon.jsonl": "ff6951bbc6959baf37b794c3232f669b6428e2d15a09057e17aab1cc17f599c9",
    "data/corpus/vitae-hesiodi-particula.vitae-hesiodi-particula.jsonl": "0d0573e65f450e554667b3d30ca8c9b7b8768432ea27a3508cea9bd12727a4e5",
    "data/corpus/vitae-homeri.plutarchi-vita.jsonl": "c305f883b2d52a3557e251b7e7ac63638cb02dcb90b58af0c3937599444c3615",
    "data/corpus/vitae-homeri.vita-herodotea.jsonl": "b74d8b62bade75c3fbebf198766b5190bdf2f8f64f94ec3dfae7d2297e745be5",
    "data/corpus/vitae-homeri.vita-proculea-e-chrestomathia.jsonl": "346f421ac9a4b13f02f4deb6ef5fbb01bcf28defe556ce3ce0c8d497a5184fd4",
    "data/corpus/vitae-homeri.vita-quarta.jsonl": "64b42d4885720d91700f8148d9e4ff809aad4cd8eca38e73b928c2666285adbb",
    "data/corpus/vitae-homeri.vita-quinta.jsonl": "dae8fcef87311a7bb5a45dd0fe16e7749c1abdf0d5aefa45c500193a9af30e20",
    "data/corpus/vitae-homeri.vita-sexta.jsonl": "25f55d8d2db33a1a5ce0a5f5dcdd27fbe95b1182683d8e4dc0f0740a5ce33d62",
    "data/corpus/vitae-pindari-et-varia-de-pindaro.vita-ambrosiana.jsonl": "e205ed723f440220922ff767e0b0d84a57ebd117df17492d2376afcf0149c16c",
    "data/corpus/vitae-pindari-et-varia-de-pindaro.vita-thomana-et-hypothesis-olympiorum.jsonl": "53a2f049e2e42e6213e0b4bd3ecc5e3354fc3b4156a9881fba880ea3725fd994"
}
_EVIDENCE_CONTENTS = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def local_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "data":
        raise ValueError("Unsafe Westermann artifact path: " + str(name))
    return Path(root) / path


def recipe_pins():
    return {name: sha((Path(__file__).parent / name).read_bytes()) for name in (
        "repair_westermann_scope.py", "westermann_source_observations.py",
        "capture_westermann_sources.py")}


def input_pins():
    return {PRIMARY: INPUT_SHA256, **EVIDENCE_PINS}


def deduplication_evidence(before, work_defs=None):
    """Verify archived independent primaries used to abstain from duplicate counts.

    These are historical admission inputs, not outputs owned by this repair.
    Replay reads the archived bytes so a later audited correction to a target
    does not rewrite this decision's original evidence. Initial apply requires
    those same bytes in the live primary files.
    """
    work_defs = definitions() if work_defs is None else work_defs
    links = defaultdict(list)
    for key, definition in work_defs.items():
        targets = [(field, definition[field]) for field in
                   ("canonical_target", "related_existing_primary") if definition.get(field)]
        if definition["admission"] == "comparative" and not targets:
            if not definition.get("parallel_recension_family") or not definition.get("admission_reason"):
                raise ValueError("Westermann comparative unit has neither an existing target nor a qualified unaligned recension family: " + key)
        for field, slug in targets:
            if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+\.[a-z0-9-]+", slug):
                raise ValueError("Invalid Westermann comparative target: " + key)
            path = f"data/corpus/{slug}.jsonl"
            if path not in EVIDENCE_PINS:
                raise ValueError("Westermann comparative target has no frozen primary evidence: " + slug)
            loci = definition.get("related_primary_loci", [])
            if not isinstance(loci, list) or any(not isinstance(locus, str) or not locus for locus in loci):
                raise ValueError("Invalid Westermann comparative source loci: " + key)
            links[path].append({"unit": key, "relation": field, "slug": slug, "loci": loci})
    if set(links) != set(EVIDENCE_PINS):
        raise ValueError("Westermann comparative evidence inventory differs from the declared source targets")
    result = {}
    for path, pin in EVIDENCE_PINS.items():
        raw = before.get(path)
        if not isinstance(raw, bytes) or sha(raw) != pin:
            raise ValueError("Westermann comparative primary evidence changed or is missing: " + path)
        cache_key = (path, pin)
        if cache_key not in _EVIDENCE_CONTENTS:
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
            slug = path.removeprefix("data/corpus/").removesuffix(".jsonl")
            if not rows or any(row.get("urn") != slug for row in rows):
                raise ValueError("Westermann comparative primary has a different work identity: " + path)
            _EVIDENCE_CONTENTS[cache_key] = {
                "loci": frozenset(row["locus"] for row in rows), "rows": len(rows),
                "sources": sorted({row.get("source", "") for row in rows}),
                "licenses": sorted({row.get("license", "") for row in rows})}
        contents = _EVIDENCE_CONTENTS[cache_key]
        for link in links[path]:
            if not set(link["loci"]).issubset(contents["loci"]):
                raise ValueError("Westermann comparative source locus is missing: " + link["unit"])
        result[path] = {"sha256": pin, "rows": contents["rows"],
            "sources": contents["sources"], "licenses": contents["licenses"],
            "units": sorted(links[path], key=lambda link: (link["unit"], link["relation"]))}
    return result


def definitions():
    from westermann_source_observations import work_definitions
    values = work_definitions()
    if not isinstance(values, dict) or not values:
        raise ValueError("Westermann source work definitions are absent")
    seen = set()
    for key, value in values.items():
        if value.get("admission") not in {"primary", "comparative", "held"}:
            raise ValueError("Westermann work has no explicit admission decision: " + key)
        if value["admission"] == "primary":
            if any(not value.get(field) for field in ("slug", "author", "author_name", "title")):
                raise ValueError("Westermann primary lacks source-supported identity: " + key)
            if not re.fullmatch(r"[a-z0-9-]+\.[a-z0-9-]+", value["slug"]):
                raise ValueError("Unsafe Westermann primary slug")
            if value["slug"] in seen:
                raise ValueError("Two Westermann source units claim one primary identity")
            seen.add(value["slug"])
    return values


def output_inventory(work_defs=None):
    work_defs = definitions() if work_defs is None else work_defs
    return {LITERAL, COMPARATIVE, HELD, PARATEXT, FRAGMENT, RECORDS,
        *(f"data/corpus/{value['slug']}.jsonl" for value in work_defs.values()
          if value["admission"] == "primary")}


def _capture(root):
    from capture_westermann_sources import check
    return check(root)


def _parts(row, work_defs):
    from westermann_source_observations import partitions
    parts = [dict(part) for part in partitions(row)]
    cursor = 0
    if not isinstance(parts, list) or not parts:
        raise ValueError("Westermann row has no reviewed source partition: " + row["locus"])
    for part in parts:
        observed_role = part.get("role")
        part["observed_role"] = observed_role
        part["role"] = ({"historical-body": "historical", "heading": "editorial",
                         "apparatus": "editorial", "index": "editorial"}.get(observed_role, observed_role))
        if (part.get("start") != cursor or not isinstance(part.get("end"), int)
                or not cursor < part["end"] <= len(row["text"])
                or part.get("role") not in {"historical", "editorial", "uncertain"}
                or not part.get("evidence")):
            raise ValueError("Westermann source partition is incomplete or unsupported: " + row["locus"])
        if part["role"] == "historical" and part.get("work") not in work_defs:
            raise ValueError("Westermann historical source partition has no work identity")
        if cursor and GREEK.fullmatch(row["text"][cursor - 1:cursor + 1]):
            raise ValueError("Westermann role boundary may not divide a Greek lexical run")
        cursor = part["end"]
    if cursor != len(row["text"]):
        raise ValueError("Westermann source partition loses characters")
    return parts


def build(root, before, *, recorded_at):
    raw = before.get(PRIMARY)
    if raw is None or sha(raw) != INPUT_SHA256:
        raise ValueError("Westermann literal source differs from its released pin")
    _capture(root)
    work_defs = definitions()
    deduplication_evidence(before, work_defs)
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != 7013 or len({row["locus"] for row in rows}) != len(rows):
        raise ValueError("Westermann original row accounting changed")
    for row in rows:
        if (row.get("urn") != OLD or not LOCUS.fullmatch(row["locus"])
                or row.get("source") != "ocr" or row.get("license") != "PD"):
            raise ValueError("Westermann original identity, source, or license changed")
    outputs = defaultdict(list)
    outputs[LITERAL] = rows  # Exact row contents; byte order is also archived.
    aliases, changes, summaries = {}, [], defaultdict(Counter)
    counts = Counter(original_rows=len(rows), original_greek_tokens=sum(
        len(GREEK.findall(row["text"])) for row in rows))
    for row in sorted(rows, key=lambda item: tuple(map(int, LOCUS.fullmatch(item["locus"]).groups()))):
        page, number = map(int, LOCUS.fullmatch(row["locus"]).groups())
        parts = _parts(row, work_defs)
        destinations = []
        for index, part in enumerate(parts, 1):
            text = row["text"][part["start"]:part["end"]]
            if not text:
                continue
            key, role = part.get("work"), part["role"]
            definition = work_defs.get(key, {})
            admission = definition.get("admission") if role == "historical" else role
            locus = f"westermann1845.{page:04d}.{number}.{index}"
            common = {"locus": locus, "source": "ocr", "license": "PD", "edition": EDITION,
                "text": text, "original_work": OLD, "original_locus": row["locus"],
                "original_edition": row.get("edition"), "source_pdf_page": page,
                "source_printed_page": page - 28 if 29 <= page <= 488 else None,
                "source_char_range": [part["start"], part["end"]],
                "source_role": role, "source_role_evidence": part["evidence"],
                "source_role_detail": part["observed_role"],
                "source_work_key": key,
                "westermann_scope_review": {"authority": AUDIT + "/changes.json"}}
            if admission == "primary":
                slug = definition["slug"]
                path = f"data/corpus/{slug}.jsonl"
                target_row = dict(common, urn=slug, lang="grc", analysis_text=text,
                    unreviewed_ocr_spellings=True)
                if definition.get("cts"):
                    target_row["cts"] = definition["cts"]
            elif role == "editorial":
                path = PARATEXT
                target_row = dict(common, urn="westermann-1845.edition-apparatus", lang="mul",
                    **{"class": "edition-apparatus"})
            else:
                path = COMPARATIVE if admission == "comparative" else HELD
                target_row = dict(common, urn=definition.get("slug", "westermann-1845.source-witness"),
                    lang="grc" if role == "historical" else "mul",
                    source_work_title=definition.get("title"),
                    **{"class": "comparative-historical-witness" if admission == "comparative"
                       else "uncertain-source-role"})
                if definition.get("canonical_target"):
                    target_row["canonical_target"] = definition["canonical_target"]
                if definition.get("related_existing_primary"):
                    target_row["related_existing_primary"] = definition["related_existing_primary"]
            outputs[path].append(target_row)
            destination = {"path": path, "locus": locus}
            if admission == "primary":
                destination["slug"] = definition["slug"]
            destinations.append(destination)
            counts[admission + "_rows"] += 1
            counts[admission + "_greek_tokens"] += len(GREEK.findall(text))
            if key:
                summaries[key][admission + "_rows"] += 1
                summaries[key][admission + "_greek_tokens"] += len(GREEK.findall(text))
        aliases[row["locus"]] = {"path": LITERAL, "locus": row["locus"],
            "partitions": destinations}
        changes.append({"original_row": row, "original_text": row["text"],
            "corrected_text": row["text"], "source_partitions": parts,
            "destinations": destinations, "recorded_at": recorded_at})
    if not outputs.get(PRIMARY):
        raise ValueError("Marcellinus must retain its authentic historical work and identity")
    for value in work_defs.values():
        if value["admission"] == "primary" and not outputs.get(f"data/corpus/{value['slug']}.jsonl"):
            raise ValueError("A Westermann primary work has no source-supported body: " + value["slug"])
    for path in (COMPARATIVE, HELD, PARATEXT):
        outputs.setdefault(path, [])
    files = {name: jsonl(values) for name, values in outputs.items()}
    files[LITERAL] = raw
    files[FRAGMENT] = encoded({"schema_version": 1, "aliases": {OLD: aliases}})
    files[RECORDS] = gzip.compress(jsonl(changes), mtime=0)
    if set(files) != output_inventory(work_defs):
        raise ValueError("Westermann output inventory differs from source work definitions")
    # Whitespace can join or separate Greek regex runs, so exact character
    # reconstruction is the conservation rule; token totals are role-specific.
    counts["primary_works"] = sum(name.startswith("data/corpus/") for name in files)
    counts["literal_rows"] = len(outputs[LITERAL])
    counts["partition_rows"] = sum(len(value["source_partitions"]) for value in changes)
    return files, {key: dict(value) for key, value in summaries.items()}, dict(counts)


def _before(root, audit=None):
    path = Path(root) / AUDIT / "before.json.gz"
    raw = path.read_bytes()
    if audit is not None and sha(raw) != audit.get("before_sha256"):
        raise ValueError("Westermann original-byte archive changed")
    values = json.loads(gzip.decompress(raw))
    return {name: None if value is None else base64.b64decode(value, validate=True)
            for name, value in values.items()}


def active(root=ROOT):
    root = Path(root)
    path = root / AUDIT / "changes.json"
    if path.is_file() != (root / AUDIT / "before.json.gz").is_file():
        raise ValueError("Westermann authority or exact preimage archive is missing")
    if not path.is_file():
        return False
    audit = json.loads(path.read_bytes())
    before = _before(root, audit)
    return not all((local_path(root, name).read_bytes() if local_path(root, name).is_file()
                    else None) == before[name] for name in audit["outputs"])


def verify(root=ROOT, *, active_only=True, replay=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema") != "westermann-source-scope-v1"
            or audit.get("inputs") != input_pins()
            or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("qualification") != QUALIFICATION):
        raise ValueError("Westermann repair recipe or source qualification changed")
    for name, expected in audit["recipe_sha256"].items():
        if sha((root / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Westermann recipe source changed: " + name)
    before = _before(root, audit)
    if (set(before) != set(audit["outputs"]) | set(input_pins()) or set(audit["outputs"]) != output_inventory()
            or before.get(PRIMARY) is None or sha(before[PRIMARY]) != INPUT_SHA256):
        raise ValueError("Westermann original inventory or source bytes changed")
    if any(value is not None for name, value in before.items() if name not in input_pins()):
        raise ValueError("Westermann repair may not overwrite another primary or witness")
    if deduplication_evidence(before) != audit.get("deduplication_evidence"):
        raise ValueError("Westermann archived comparative source evidence no longer reproduces")
    capture = _capture(root)
    if sha(encoded(capture)) != audit["source_capture_sha256"]:
        raise ValueError("Westermann source-capture authority changed")
    for name, expected in audit["outputs"].items():
        path = local_path(root, name)
        actual = sha(path.read_bytes()) if path.is_file() else None
        if active_only and actual != expected:
            raise ValueError("Westermann repaired output changed: " + name)
    if replay:
        outputs, summaries, counts = build(root, before, recorded_at=audit["recorded_at"])
        if ({name: sha(raw) for name, raw in outputs.items()} != audit["outputs"]
                or summaries != audit["works"] or counts != audit["counts"]):
            raise ValueError("Westermann literal source routing does not reproduce")
    return audit, before


def _stat_key(path):
    if not path.is_file():
        return None
    status = path.stat()
    return (status.st_size, status.st_mtime_ns, status.st_ctime_ns, status.st_ino)


@lru_cache(maxsize=4)
def _authority_inventory(root_name, manifest_signature):
    root = Path(root_name)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    from westermann_source_observations import CAPTURE_PATH, REVIEW_PATH
    capture = json.loads((root / CAPTURE_PATH).read_bytes())
    return frozenset({AUDIT + "/changes.json", AUDIT + "/before.json.gz", *audit["outputs"],
        CAPTURE_PATH, REVIEW_PATH, *(item["path"] for item in capture["files"]),
        *("scripts/" + name for name in recipe_pins())})


def authority_paths(root=ROOT):
    root = Path(root).absolute()
    from westermann_source_observations import CAPTURE_PATH, REVIEW_PATH
    manifests = (AUDIT + "/changes.json", CAPTURE_PATH, REVIEW_PATH)
    return _authority_inventory(str(root), tuple((name, _stat_key(root / name)) for name in manifests))


def _signature(root):
    return tuple((name, _stat_key(root / name)) for name in sorted(authority_paths(root)))


@lru_cache(maxsize=2)
def _checked(root_name, signature):
    audit, before = verify(Path(root_name), replay=True)
    rows = {(row["urn"], row["locus"]): row for name in audit["outputs"]
        if name.startswith("data/corpus/")
        for row in map(json.loads, (Path(root_name) / name).read_bytes().splitlines())}
    return audit, before, rows


def checked_state(root=ROOT):
    root = Path(root).absolute()
    audit, before, _ = _checked(str(root), _signature(root))
    return deepcopy(audit), dict(before)


def validate_projection(row, root=ROOT):
    root = Path(root).absolute()
    _, _, rows = _checked(str(root), _signature(root))
    if rows.get((row.get("urn"), row.get("locus"))) != row:
        raise ValueError("Westermann lexical projection differs from its source authority")
    return row["analysis_text"]


def alias_fragment(root=ROOT):
    if not active(root):
        return None
    checked_state(root)
    return {**json.loads((Path(root) / FRAGMENT).read_bytes()), "authority": {
        "path": AUDIT + "/changes.json", "sha256": sha((Path(root) / AUDIT / "changes.json").read_bytes())}}


def metadata(root=ROOT):
    if not active(root):
        return {}
    audit, _ = checked_state(root)
    return {value["slug"]: {**value, "counts": audit["works"].get(key, {}),
        "edition": EDITION, "qualification": QUALIFICATION,
        "authority": {"path": AUDIT + "/changes.json", "sha256": sha((Path(root) / AUDIT / "changes.json").read_bytes())}}
        for key, value in definitions().items() if value["admission"] == "primary"}


def _publish(root, values):
    originals = {name: local_path(root, name).read_bytes() if local_path(root, name).is_file()
                 else None for name in values}
    staged = {}
    changed = []
    try:
        for name, raw in values.items():
            path = local_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if raw is not None:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(raw)
                    staged[name] = Path(handle.name)
        try:
            for name, raw in values.items():
                path = local_path(root, name)
                path.unlink(missing_ok=True) if raw is None else os.replace(staged[name], path)
                changed.append(name)
        except OSError:
            for name in reversed(changed):
                path = local_path(root, name)
                path.unlink(missing_ok=True) if originals[name] is None else path.write_bytes(originals[name])
            raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    path = root / AUDIT / "changes.json"
    archive = root / AUDIT / "before.json.gz"
    if path.is_file() != archive.is_file():
        raise ValueError("Westermann authority or exact preimage archive is missing")
    if path.is_file():
        audit, before = verify(root, active_only=False, replay=True)
        if recorded_at is not None and recorded_at != audit["recorded_at"]:
            raise ValueError("Reapplying the frozen Westermann audit cannot change its timestamp")
        if active(root):
            raise ValueError("Westermann source repair is already active")
        outputs, _, _ = build(root, before, recorded_at=audit["recorded_at"])
        _publish(root, outputs)
        return verify(root)[0]
    before = {}
    for name in input_pins():
        if not local_path(root, name).is_file():
            raise ValueError("Westermann comparative or anthology input is missing: " + name)
        before[name] = local_path(root, name).read_bytes()
    stamp = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, summaries, counts = build(root, before, recorded_at=stamp)
    for name in outputs:
        if name != PRIMARY and local_path(root, name).exists():
            raise ValueError("Westermann destination already exists: " + name)
        before.setdefault(name, None)
    raw = gzip.compress(encoded({name: None if value is None else base64.b64encode(value).decode()
        for name, value in before.items()}), mtime=0)
    audit = {"schema": "westermann-source-scope-v1", "recorded_at": stamp,
        "inputs": input_pins(), "outputs": {name: sha(value) for name, value in outputs.items()},
        "before_sha256": sha(raw), "before_encoding": "base64", "recipe_sha256": recipe_pins(),
        "source_capture_sha256": sha(encoded(_capture(root))), "works": summaries,
        "counts": counts, "qualification": QUALIFICATION,
        "deduplication_evidence": deduplication_evidence(before)}
    _publish(root, {**outputs, AUDIT + "/before.json.gz": raw, AUDIT + "/changes.json": encoded(audit)})
    return verify(root)[0]


def undo(root=ROOT):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    before = _before(root, audit)
    if (set(before) != set(audit["outputs"]) | set(input_pins()) or set(audit["outputs"]) != output_inventory()
            or sha(before[PRIMARY]) != INPUT_SHA256
            or any(value is not None for name, value in before.items() if name not in input_pins())):
        raise ValueError("Westermann literal undo inventory changed")
    for name, expected in audit["outputs"].items():
        path = local_path(root, name)
        if (sha(path.read_bytes()) if path.is_file() else None) != expected:
            raise ValueError("Undo later changes before the Westermann repair: " + name)
    _publish(root, {name: before[name] for name in audit["outputs"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["apply", "verify", "undo"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--recorded-at")
    args = parser.parse_args()
    result = (apply(args.root, recorded_at=args.recorded_at) if args.mode == "apply" else
              verify(args.root)[0] if args.mode == "verify" else undo(args.root))
    if result:
        print(json.dumps(result["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
