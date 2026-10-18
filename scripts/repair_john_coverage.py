#!/usr/bin/env python3
"""Restore Cyril's PG 73 commentary and preserve PG 74 work boundaries.

The Calfa witness complements PG 74; it never competes with that volume in a
whole-work source ranking. No OCR spelling is corrected by this migration.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SLUG = "cyrillus-theology.commentarii-in-joannem"
CORPUS = f"data/corpus/{SLUG}.jsonl"
AUDIT = "data/corpus_changes/cyril-john-coverage"
SOURCE = "data/reference/calfa-pg73/PG073_text.txt.gz"
PARATEXT = "data/paratext/cyril-pg74-title.jsonl"
WITNESS = "data/ocr_witnesses/cyril-pg74-other-works.jsonl"
NETWORKS = f"{AUDIT}/full-networks.json.gz"
RAW_SHA = "353b31b6ca09f0e1639267da976e13171b8426352ea2d8ba648a1d1c43758104"
ORIGINAL_SHA = "b21757e5ce20209046ea548b25f1ffbaf31bb2666835657a4180a831d9e1a10e"
JOBS = "data/ocr_requests/cyril-john-missing-pg74.json"
URL = "https://raw.githubusercontent.com/calfa-co/Patrologia-Graeca/5895ab908dd4cac5ee06cfc0e36f2ef77723e143/PG073/PG073_text.txt"
EDITION = "calfa-pg73-5895ab908dd4"
MARKER = re.compile(r"^\$0=073(?:\s+\$[1-7]=\S+)*\s+\$8=(\S+)\s+\$9=(\S+)\s*$")
OLD_LOCUS = re.compile(r"pg074_(\d+)\.(\d+)$")
EVIDENCE = {
    "issue": "https://github.com/open-greek/open-greek-corpus/issues/42",
    "date": "2026-10-18", "source_url": URL, "source_sha256": RAW_SHA,
    "source_license": "CC-BY-4.0", "attribution": "Calfa, Patrologia Graeca OCR, PG073",
    "reference_scans": [
        {"url": "https://archive.org/details/patrologiaecurs43hopfgoog",
         "sha256": "9de7832e644fd6f9436f15b51c940f7601738a90339c29f3350210ffad2802ab",
         "description": "Migne PG 73, 1859; scan 12 begins the commentary's prooimion; scan 569 ends John 10:17 above the Latin index."},
        {"url": "https://archive.org/details/patrologiaecurs25hopfgoog",
         "sha256": "0150e7ffadcf5836ba6198cebdec113effe9e655b652a54388f1e8e8802b2005",
         "description": "Migne PG 74, 1859; scan 12 begins Books VII/VIII fragments; scan 473 ends John at columns 755–756; scan 474 begins Acts; scan 482 begins Romans below the end of Acts."}],
    "boundary": "Calfa PG073 marker pages 10–537 end at John 10:17. The retained PG074 begins John 10:18. Historical PG074 loci are OCR image keys, not Migne columns; nonlinear image offsets and repeated images prohibit arithmetic page conversion.",
    "policy": "Keep complementary volumes in reading order. Preserve all original readings; exclude volume title matter and other works from John's primary text. Held Acts and Romans readings remain independently accessible with their source identities, without counting them again as John."
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


def pg73_records(raw):
    if sha(raw) != RAW_SHA:
        raise ValueError("Calfa PG073 bytes differ from the pinned source")
    blocks, current, lines = [], None, []
    for line in raw.decode("utf-8").splitlines():
        match = MARKER.fullmatch(line)
        if match:
            if current is not None and lines:
                blocks.append((current, lines))
            current, lines = (match[1], match[2]), []
        elif line.startswith("$0="):
            raise ValueError("Unreviewed Calfa source marker")
        elif line.strip():
            if current is None:
                raise ValueError("Text precedes its source marker")
            lines.append(line.strip())
    if current is not None and lines:
        blocks.append((current, lines))
    seen, rows = Counter(), []
    for (page, start), text_lines in blocks:
        n = seen[page]
        seen[page] += 1
        key = f"PG073.{page}" + (f".{n}" if n else "")
        rows.append({"urn": SLUG, "cts": "urn:cts:greekLit:tlg4090.tlg002",
            "edition": EDITION, "source": "cgpg", "license": "CC-BY-4.0", "locus": key,
            "text": unicodedata.normalize("NFC", " ".join(text_lines)),
            "source_location": {"volume": "PG073", "marker_page": page, "start_line": start},
            "evidence": f"{AUDIT}/changes.json"})
    if len(rows) != 528 or list(seen)[0] != "10" or list(seen)[-1] != "537":
        raise ValueError("The reviewed PG073 boundaries changed")
    return rows


def pg74_assignment(locus):
    match = OLD_LOCUS.fullmatch(locus)
    if not match:
        raise ValueError("Unreviewed PG074 source locus")
    page, line = map(int, match.groups())
    if page == 7 and 1 <= line <= 4:
        return "volume_title"
    if 9 <= page <= 398:
        return "john"
    if 399 <= page <= 408 or page == 409 and line <= 8:
        return "acts"
    if page == 409 and line >= 10 or 410 <= page <= 441:
        return "romans"
    raise ValueError("PG074 boundary was not reviewed")


def fresh_inputs(root, paths):
    return fresh_blobs(root, [Path(path).read_bytes() for path in paths])


def fresh_blobs(root, blobs):
    manifest_bytes = (root / JOBS).read_bytes()
    manifest = json.loads(manifest_bytes)
    pages = {page["id"]: page for page in manifest["pages"]}
    checkpoints, readings, archives = set(), {key: [] for key in pages}, []
    for blob in blobs:
        records = [json.loads(line) for line in blob.decode().splitlines()]
        meta = records[0]["_meta"]
        model = meta["model"]
        family = "qwen36" if "Qwen3.6-27B" in model else "qwen38" if "Qwen3.8-27B" in model else None
        allowed = {"6a9e13bd6fc8f0983b9b99948120bc37f49c13e9", "e89b16ebf1988b3d6befa7de50abc2d76f26eb09"} if family == "qwen36" else {"017b9c7af6b5689d5dd426a76e0bc077eb5ca20a", "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"}
        if family is None or family in checkpoints or meta["revision"] not in allowed or meta["manifest_sha256"] != sha(manifest_bytes):
            raise ValueError("Need distinct pinned Qwen3.6 and Qwen3.8 witnesses of the reviewed leaves")
        checkpoints.add(family)
        seen = set()
        for row in records[1:]:
            identity = row["id"]
            if identity not in pages or identity in seen:
                raise ValueError("Unknown or repeated Cyril page")
            page = pages[identity]
            if any(row.get(k) != page[k] for k in ("source", "scan_page", "region")) or row.get("error") or row.get("finish_reason") != "stop" or not row["raw_prediction"].strip() or row.get("prompt_sha256") != sha(manifest["prompt"].encode()):
                raise ValueError("Failed, truncated or changed Cyril page geometry")
            seen.add(identity)
            readings[identity].append({"id": family, "vote_group": family,
                "text": row["raw_prediction"], "artifact_sha256": sha(blob),
                "model": model, "revision": meta["revision"], "source_page": page})
        if seen != set(pages):
            raise ValueError("Incomplete Cyril missing-page witness")
        archives.append({"artifact_sha256": sha(blob), "raw_jsonl": blob.decode()})
    if checkpoints != {"qwen36", "qwen38"}:
        raise ValueError("Both independent checkpoints are required")
    return {"manifest_sha256": sha(manifest_bytes), "pages": readings, "archives": archives}


def outputs(before, raw, fresh):
    if sha(before[CORPUS].encode()) != ORIGINAL_SHA:
        raise ValueError("The historical Cyril source bytes changed; review the partition again")
    rows = [json.loads(line) for line in before[CORPUS].splitlines()]
    body, titles, held, changes = [], [], [], []
    aliases = json.loads(before["data/passage_aliases.json"])
    own_aliases = aliases.setdefault("aliases", {}).setdefault(SLUG, {})
    for row in rows:
        if row["urn"] != SLUG or row["edition"] != "migne-ocr-qwen36":
            raise ValueError("Unreviewed Cyril source identity")
        kind = pg74_assignment(row["locus"])
        if kind == "john":
            body.append(row)
            continue
        result = dict(row, source_work_class=kind, language="grc")
        path = PARATEXT if kind == "volume_title" else WITNESS
        result["class"] = "volume_title" if kind == "volume_title" else "held-authorial-witness"
        result["why_not_served"] = "Volume title page" if kind == "volume_title" else (
            "PG074 contains this separate work after John; repeated source images and partial coverage require source-level collation before independent primary admission.")
        if kind != "volume_title":
            result["identified_work"] = (
                "cyrillus-theology.fragmenta-in-acta-apostolorum-et-in-epistulas-catholicas" if kind == "acts"
                else "cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ad-romanos")
        result.pop("cts", None)
        (titles if kind == "volume_title" else held).append(result)
        destination = {"path": path, "locus": row["locus"]}
        if row["locus"] in own_aliases:
            raise ValueError("Cyril historical passage already has a destination")
        own_aliases[row["locus"]] = destination
        changes.append({"original_row": row, "preserved_row": result, "destination": destination,
                        "original_text": row["text"], "corrected_text": row["text"], "text_changed": False})
    if (len(body), len(titles), len(held)) != (2578, 4, 474):
        raise ValueError("The reviewed PG074 partition changed")
    additions = pg73_records(raw)
    from ocr_consensus import merge_witnesses, compact_corpus_consensus
    fresh_rows, networks = {}, {}
    for identity, witnesses in fresh["pages"].items():
        source_page = witnesses[0]["source_page"]
        old_page = int(source_page["historical_missing_key"].split("_")[-1])
        merged = merge_witnesses(witnesses)
        networks[identity] = merged
        compact = compact_corpus_consensus(merged, {"path": NETWORKS, "key": identity})
        fresh_rows[old_page] = {"urn": SLUG, "cts": "urn:cts:greekLit:tlg4090.tlg002",
            "edition": "migne-pg74-gap-consensus-2026-10", "source": "ocr", "license": "PD",
            "locus": f"PG074.reference-scan{source_page['scan_page']}", **compact,
            "source_location": source_page, "corrections": ["collation"], "evidence": f"{AUDIT}/changes.json"}
        changes.append({"original_text": [{"witness": w["id"], "text": w["text"]} for w in witnesses],
            "corrected_text": merged["text"], "analysis_text": merged["analysis_text"],
            "destination": {"path": CORPUS, "locus": fresh_rows[old_page]["locus"]},
            "evidence": "Independent OCR of the pinned Greek column, with unresolved word readings retained as variants."})
    if set(fresh_rows) != {10, 90, 297}:
        raise ValueError("Missing-page geometry changed")
    complete_body = []
    for page in range(9, 399):
        if page in fresh_rows:
            complete_body.append(fresh_rows[page])
        complete_body.extend(row for row in body if int(OLD_LOCUS.fullmatch(row["locus"])[1]) == page)
    result = {CORPUS: jsonl(additions + complete_body), PARATEXT: jsonl(titles), WITNESS: jsonl(held),
              NETWORKS: gzip.compress(dump(networks), mtime=0),
              "data/passage_aliases.json": dump(aliases)}
    registry = json.loads(before["data/source_registry.json"])
    work = registry["works"][SLUG]
    work["editions"][f"{SLUG}.{EDITION}"] = {
        "name": "Calfa PG073 OCR, complementary first volume", "provider": "cgpg", "scheme": "volume.marker-page",
        "editor": "Migne, Jacques-Paul", "year": 1859, "source": URL, "servable": True,
        "license": "CC-BY-4.0", "scheme_inferred": False, "aliases": {}}
    work["coverage_composition"] = {"manifest": f"{AUDIT}/changes.json",
        "volumes": ["PG073", "PG074"], "policy": "complementary-volume-union",
        "qualification": "PG074 Books VII and VIII survive as fragments in this edition; this does not reconstruct lost continuous books."}
    work["editions"][f"{SLUG}.migne-pg74-gap-consensus-2026-10"] = {
        "name": "PG074 missing leaves, independent scan OCR consensus", "provider": "ocr",
        "scheme": "volume.reference-scan", "editor": "Migne, Jacques-Paul", "year": 1859,
        "source": EVIDENCE["reference_scans"][1]["url"], "servable": True, "license": "PD",
        "scheme_inferred": False, "aliases": {}}
    result["data/source_registry.json"] = dump(registry)
    ledger = json.loads(before["data/cgpg_works.json"])
    for entry in ledger:
        if entry.get("volume") == "PG073":
            entry.pop("superseded_by", None)
            entry.update(urn=SLUG, kind="complementary-volume", cgpg_chosen=True,
                         edition=EDITION, n_passages=len(additions),
                         coverage_note="PG073 complements the PG074 continuation; whole-work source replacement is invalid.")
            for component in entry.get("works", []):
                if component.get("tlg_id") == "tlg4090" and component.get("work_id") == "002":
                    component["cgpg_chosen"] = True
    result["data/cgpg_works.json"] = dump(ledger)
    return result, changes


def apply(root=ROOT, source=None, fresh_paths=()):
    root = Path(root)
    audit_dir = root / AUDIT
    if (audit_dir / "changes.json").exists():
        before, (generated, _) = replay(root)
        current_is_original = all(((root / path).read_bytes() if (root / path).exists() else None) == (text.encode() if text is not None else None)
                                  for path, text in before.items())
        if current_is_original:
            for path, data in generated.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(data)
        return check(root)
    raw = Path(source).read_bytes() if source else urlopen(URL, timeout=180).read()
    pg73_records(raw)
    paths = [CORPUS, PARATEXT, WITNESS, NETWORKS, "data/passage_aliases.json", "data/source_registry.json", "data/cgpg_works.json"]
    before = {p: (root / p).read_text() if (root / p).exists() else None for p in paths}
    if before[PARATEXT] is not None or before[WITNESS] is not None:
        raise ValueError("Cyril destinations already exist without this audit")
    fresh = fresh_inputs(root, fresh_paths)
    generated, changes = outputs(before, raw, fresh)
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "before.json.gz").write_bytes(gzip.compress(dump(before), mtime=0))
    (audit_dir / "fresh-witnesses.json.gz").write_bytes(gzip.compress(dump(fresh), mtime=0))
    target = root / SOURCE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(gzip.compress(raw, mtime=0))
    for path, data in generated.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(data)
    audit = {"schema_version": 1, "date": "2026-10-18", "generator": "scripts/repair_john_coverage.py",
        "evidence": EVIDENCE, "inputs": {p: sha(v.encode()) if v is not None else None for p, v in before.items()},
        "outputs": {p: sha(v) for p, v in generated.items()}, "changes": changes,
        "counts": {"added_pg73": 528, "retained_pg74_john": 2578, "added_pg74_missing_leaves": 3, "title_paratext": 4, "held_other_works": 474},
        "normalization": "NFC and join source lines by one space; raw bytes and marker positions preserved. No OCR spelling corrections.",
        "reversal": "Unapply later changes, then run scripts/repair_john_coverage.py --undo; exact input files are archived."}
    (audit_dir / "changes.json").write_bytes(dump(audit))
    return audit


def replay(root):
    before = json.loads(gzip.decompress((root / AUDIT / "before.json.gz").read_bytes()))
    raw = gzip.decompress((root / SOURCE).read_bytes())
    fresh = json.loads(gzip.decompress((root / AUDIT / "fresh-witnesses.json.gz").read_bytes()))
    if fresh["manifest_sha256"] != sha((root / JOBS).read_bytes()):
        raise ValueError("Missing-page source request changed")
    blobs = [entry["raw_jsonl"].encode() for entry in fresh["archives"]]
    if any(sha(blob) != entry["artifact_sha256"] for blob, entry in zip(blobs, fresh["archives"])) or fresh_blobs(root, blobs) != fresh:
        raise ValueError("Archived independent Cyril witnesses changed")
    return before, outputs(before, raw, fresh)


def check(root=ROOT):
    root = Path(root)
    before, (generated, changes) = replay(root)
    audit = json.loads((root / AUDIT / "changes.json").read_text())
    for path in (CORPUS, PARATEXT, WITNESS, NETWORKS):
        if (root / path).read_bytes() != generated[path]:
            raise ValueError(f"Cyril reading differs from its reproducible source: {path}")
    expected = json.loads(generated["data/passage_aliases.json"])["aliases"][SLUG]
    actual = json.loads((root / "data/passage_aliases.json").read_text())["aliases"][SLUG]
    if expected != actual or audit["changes"] != changes or audit["evidence"] != EVIDENCE:
        raise ValueError("Cyril audit or historical destinations changed")
    expected_work = json.loads(generated["data/source_registry.json"])["works"][SLUG]
    actual_work = json.loads((root / "data/source_registry.json").read_text())["works"][SLUG]
    if any(actual_work.get("coverage_composition", {}).get(key) != value
           for key, value in expected_work["coverage_composition"].items()):
        raise ValueError("Cyril complementary-volume metadata changed")
    for key in (f"{SLUG}.{EDITION}", f"{SLUG}.migne-pg74-gap-consensus-2026-10"):
        if actual_work.get("editions", {}).get(key) != expected_work["editions"][key]:
            raise ValueError("Cyril source-edition metadata changed")
    expected_ledger = [entry for entry in json.loads(generated["data/cgpg_works.json"]) if entry.get("volume") == "PG073"]
    actual_ledger = [entry for entry in json.loads((root / "data/cgpg_works.json").read_text()) if entry.get("volume") == "PG073"]
    if expected_ledger != actual_ledger:
        raise ValueError("Cyril complementary-volume source ledger changed")
    return audit


def undo(root=ROOT):
    root = Path(root)
    before, (generated, _) = replay(root)
    for path, data in generated.items():
        if (root / path).read_bytes() != data:
            raise ValueError(f"Unapply later changes before undo: {path}")
    for path, text in before.items():
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)


def refresh_consensus(root=ROOT):
    """Replay an unreleased collation change without overwriting later metadata."""
    root = Path(root)
    path = root / AUDIT / "changes.json"
    audit = json.loads(path.read_text())
    _, (generated, changes) = replay(root)
    owned = (CORPUS, PARATEXT, WITNESS, NETWORKS)
    for name in owned:
        if sha((root / name).read_bytes()) != audit["outputs"][name]:
            raise ValueError(f"Unreviewed Cyril output changed before consensus refresh: {name}")
    if all((root / name).read_bytes() == generated[name] for name in owned):
        return check(root)
    previous = {item["destination"]["locus"]: item for item in audit["changes"]
                if isinstance(item.get("original_text"), list)}
    revisions = []
    for item in changes:
        old = previous.get(item["destination"]["locus"])
        if old and any(old.get(key) != item.get(key) for key in ("corrected_text", "analysis_text")):
            revisions.append({"locus": item["destination"]["locus"],
                "original_text": old["corrected_text"], "corrected_text": item["corrected_text"],
                "original_analysis_text": old.get("analysis_text"), "analysis_text": item.get("analysis_text")})
    audit.setdefault("consensus_revisions", []).append({
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source": "Printed terminal hyphens retained in the archived raw independent witnesses",
        "evidence": "scripts/ocr_consensus.py preserves terminal hyphens and excludes source-page-end fragments from lexical counts; every earlier source reading remains archived.",
        "previous_output_sha256": {name: audit["outputs"][name] for name in owned},
        "changes": revisions,
        "reversal": "The original pre-admission files remain in before.json.gz; --undo removes the entire collation. Previous unreleased consensus bytes are pinned in commit 1821e484."})
    audit["changes"] = changes
    audit["outputs"].update({name: sha(raw) for name, raw in generated.items()})
    for name in owned:
        (root / name).write_bytes(generated[name])
    path.write_bytes(dump(audit))
    return check(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    for mode in ("apply", "check", "undo", "refresh-consensus"):
        action.add_argument("--" + mode, action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--fresh", type=Path, action="append", default=[])
    args = parser.parse_args()
    result = (apply(source=args.source, fresh_paths=args.fresh) if args.apply else check() if args.check
              else refresh_consensus() if args.refresh_consensus else undo())
    if result:
        print(json.dumps(result["counts"]))
