#!/usr/bin/env python3
"""Checked page routing for Meibom's 1652 musical anthology (issue 52).

The scan includes several Greek works, Latin translations, modern commentary,
and repeated scan leaves. This authority is also the OCR crop manifest; page
parity refers to the printed page, not an unchecked arithmetic scan offset.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from ocr_consensus import compact_corpus_consensus, merge_witnesses

ROOT = Path(__file__).resolve().parents[1]
OLD = "aristides-quintilianus-music.de-musica"
EDITION = "meibom-1652-consensus-2026-10"
JAHN_EDITION = "jahn-1882-consensus-2026-10"
AUDIT_DIR = "data/corpus_changes/meibom-musical-anthology"
PARATEXT = "data/paratext/meibom-1652.jsonl"
INPUT_SHA256 = "2d3e16932378cd1d0c1ea176eb0d6fbefbebea8303249f72c38c7e7808bd6526"
SOURCE = {
    "url": "https://archive.org/details/bub_gb_JgtAAAAAcAAJ",
    "pdf_sha256": "6e812c8c0647882881ff4f172eed9d92ba2248822d0481815f34b2e0f03754e8",
    "title": "Antiquae musicae auctores septem, Graece et Latine (Meibom 1652)",
    "checked_scan_pages": [5, 53, 60, 65, 138, 139, 197, 201, 222, 223, 246, 247,
        279, 306, 307, 319, 320, 339, 347, 411, 412, 427, 431, 451, 457, 458,
        463, 465, 466, 477, 481, 505, 506, 517, 525, 583, 608, 614, 642, 644,
        650, 700, 701],
    "evidence": "Manual inspection of the volume title, Greek work headings and explicit endings. Printed odd pages put Greek in the left column, even pages in the right. Scan 60 is blank with show-through; its repeated ἡμῖν OCR has no printed source. Gaudentius scan leaves 458-463 repeat 452-457. Aristides leaves 614-619 repeat 608-613 and 650-655 repeat 644-649. The Greek text ends at scan 700 (printed164); scan701 begins Martianus Capella's Latin text. Modern prefatory matter and Meibom's notes are not the ancient authors' text.",
}
RANGES = [
    (65, 138, "aristoxenus-music.elementa-harmonica", 64),
    (201, 222, "cleonides.introductio-harmonica", 200),
    (223, 246, "euclides-geom.sectio-canonis-sp", 200),
    (279, 306, "nicomachus-mathematics.harmonicum-enchiridion", 278),
    (307, 319, "nicomachus-mathematics.excerpta", 278),
    (347, 411, "alypius.isagoge-musica", 346),
    (431, 465, "gaudentius.harmonica-introductio", 430),
    (481, 505, "bacchius-geron.isagoge", 480),
    (525, 700, OLD, 524),
]


def page_assignment(scan_page):
    for start, end, slug, base in RANGES:
        if not start <= scan_page <= end:
            continue
        canonical = scan_page
        if slug == "gaudentius.harmonica-introductio" and scan_page >= 458:
            canonical = scan_page - 6
        if slug == OLD:
            if scan_page >= 614:
                canonical -= 6
            if scan_page >= 650:
                canonical -= 6
        printed = canonical - base
        book = (1 if printed <= 58 else 2 if printed <= 111 else 3) if slug == OLD else None
        return {"work": slug, "scan_page": scan_page, "printed_page": printed,
            "book": book, "greek_column": "left" if printed % 2 else "right",
            "duplicate_scan": (452 <= canonical <= 457 and 458 <= scan_page <= 463)
                or slug == OLD and (614 <= scan_page <= 619 or 650 <= scan_page <= 655)}
    return {"work": "paratext", "scan_page": scan_page,
        "class": "blank_scan" if scan_page in [1, 60] else "edition_paratext"}


def manifest():
    pages = [page_assignment(p) for p in range(1, 911)]
    return {"schema_version": 1, "source": SOURCE,
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/52",
        "pages": pages, "fresh_aristides_pages": [p for p in pages
            if p["work"] == OLD and not p.get("duplicate_scan")]}


def fresh_jobs():
    return {"schema_version": 1,
        "purpose": "Independent Greek-column witnesses for all 164 unique printed pages of Aristides Quintilianus in Meibom 1652; repeated source images are not independent pages.",
        "sources": {"meibom": {"url": "https://archive.org/download/bub_gb_JgtAAAAAcAAJ/bub_gb_JgtAAAAAcAAJ.pdf",
            "sha256": SOURCE["pdf_sha256"], "license": "PD (Meibom 1652)",
            "citation": "Marcus Meibom, Antiquae musicae auctores septem (Amsterdam, 1652)"}},
        "layout_evidence": SOURCE,
        "pages": [{"id": f"meibom-{p['scan_page']:04d}-greek", "source": "meibom",
            "scan_page": p["scan_page"], "printed_page": p["printed_page"],
            "book": p["book"], "greek_column": p["greek_column"],
            "region": [.02, .03, .59, .97] if p["greek_column"] == "left" else [.42, .03, .99, .97],
            "max_side": 2600} for p in manifest()["fresh_aristides_pages"]]}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


def scan_from_locus(locus):
    match = re.fullmatch(r"aristides_quintilianus_meibom_(\d+)\.(\d+)", locus)
    if not match:
        raise ValueError(f"Unreviewed Meibom locus: {locus}")
    return int(match[1])


def clean_jahn_running_headers(text, page):
    """Remove only isolated initial running heads on reviewed interior pages.

    Offsets address Unicode code points in the unchanged raw prediction.
    Actual book openings retain their printed title and author headings.
    """
    if page["scan_page"] in {74, 111, 141}:
        return text, []
    removals, offset, nonblank = [], 0, 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped:
            offset += len(line)
            continue
        nonblank += 1
        if nonblank > 3:
            break
        if stripped == str(page["printed_page"]):
            offset += len(line)
            continue
        folded = "".join(char for char in unicodedata.normalize("NFD", stripped)
                         if char.isalpha()).upper()
        is_title = re.fullmatch(r"ΠΕΡΙΜΟΥΣΙΚΗΣ[ΑΒΓABG]?", folded) is not None
        is_author = folded == "ΑΡΙΣΤΕΙΔΟΥΤΟΥΚΟΙΝΤΙΛΙΑΝΟΥ"
        if not (is_title or is_author):
            break  # never search through the authored body for a similar phrase
        removals.append({"kind": "initial-running-header", "start": offset, "end": offset + len(line),
            "original_text": line, "corrected_text": "", "timestamp": "2026-10-18",
            "source": "Manual inspection of Jahn 1882 page layout; data/ingest_reviews/jahn-layout-review.json",
            "scan_page": page["scan_page"], "printed_page": page["printed_page"], "authority_book": page["book"],
            "policy": "Remove the isolated initial running head only on an interior page. Retain the raw OCR book label without correcting it."})
        offset += len(line)
    cleaned, cursor = [], 0
    for change in removals:
        cleaned.append(text[cursor:change["start"]])
        cursor = change["end"]
    cleaned.append(text[cursor:])
    return "".join(cleaned), removals


def prepare_inputs(root, fresh_paths, original_dir=None, primary_source="jahn1882"):
    primary = root / f"data/corpus/{OLD}.jsonl"
    raw = primary.read_bytes()
    if sha(raw) != INPUT_SHA256:
        raise ValueError("The original Meibom file changed; review its assignment again")
    records = [json.loads(line) for line in raw.splitlines()]
    by_scan = defaultdict(list)
    for row in sorted(records, key=lambda r: (scan_from_locus(r["locus"]), int(r["locus"].rsplit(".", 1)[1]))):
        by_scan[scan_from_locus(row["locus"])].append(row)
    page_witnesses = defaultdict(list)
    for scan, rows in sorted(by_scan.items()):
        assignment = page_assignment(scan)
        if assignment["work"] != OLD:
            continue
        text = "\n".join(row["text"] for row in rows)
        record_sha = sha(jsonl(rows))
        witness = {"id": f"legacy-served-{scan:04d}", "vote_group": "legacy-served",
            "text": text, "artifact_sha256": record_sha, "model": "Qwen3.6-27B",
            "source": "Previously served OCR, with its recorded deterministic corrections",
            "scan_page": scan, "original_rows": rows}
        page_witnesses[assignment["printed_page"]].append(witness)
    if original_dir:
        for scan in range(525, 701):
            path = original_dir / f"aristides_quintilianus_meibom_{scan:04d}.grc.txt"
            if not path.exists():
                continue
            raw_original = path.read_bytes()
            assignment = page_assignment(scan)
            witness = {"id": f"legacy-original-{scan:04d}", "vote_group": "legacy-original",
                "text": raw_original.decode(), "artifact_sha256": sha(raw_original),
                "model": "Qwen3.6-27B", "source": "Original uncorrected page OCR",
                "scan_page": scan}
            page_witnesses[assignment["printed_page"]].append(witness)
    meibom_witnesses = dict(page_witnesses)
    if primary_source == "jahn1882":
        primary_manifest = json.loads((ROOT / "data/ingest_reviews/jahn-aristides-fresh-witnesses.json").read_text())
        expected = {p["scan_page"]: p for p in primary_manifest["pages"]}
        page_witnesses = defaultdict(list)
        primary_pages = 97
    elif primary_source == "meibom1652":
        primary_manifest = fresh_jobs()
        expected = {p["scan_page"]: p for p in primary_manifest["pages"]}
        primary_pages = 164
    else:
        raise ValueError(f"Unknown Aristides source edition: {primary_source}")
    models_by_page = defaultdict(set)
    for path in fresh_paths:
        meta = None
        artifact = path.read_bytes()
        for line in artifact.splitlines():
            record = json.loads(line)
            if "_meta" in record:
                meta = record["_meta"]
                continue
            scan = record["scan_page"]
            if scan not in expected:
                continue
            if meta is None or not all(isinstance(meta.get(field), str) and meta[field].strip()
                                       for field in ["model", "revision", "prompt"]):
                raise ValueError("Fresh OCR has no pinned model and prompt metadata")
            if record["region"] != expected[scan]["region"]:
                raise ValueError(f"Fresh OCR used an unchecked crop on page {scan}")
            if record.get("finish_reason") in {"length", "max_tokens"}:
                raise ValueError(f"Fresh OCR is truncated on page {scan}")
            if record.get("error") or record.get("finish_reason") != "stop":
                raise ValueError(f"Fresh OCR did not complete successfully on page {scan}")
            identifier = f"fresh-{meta['model'].rsplit('/', 1)[-1]}-{scan:04d}"
            prediction = record["raw_prediction"]
            if not isinstance(prediction, str) or not re.search(r"[Ͱ-Ͽἀ-῿]", prediction):
                raise ValueError(f"Fresh OCR has no Greek reading on page {scan}")
            identity = {k: meta.get(k) for k in ["model", "revision", "prompt", "backend"]}
            identity.update(image_sha256=record["image_sha256"], raw_prediction=prediction)
            cleaned, preprocessing = clean_jahn_running_headers(prediction, expected[scan]) if primary_source == "jahn1882" else (prediction, [])
            witness = {"id": identifier, "vote_group": meta["model"], "text": cleaned,
                "original_text": prediction, "preprocessing": preprocessing,
                "artifact_sha256": sha(dump(identity)), "model": meta["model"],
                "revision": meta.get("revision"), "backend": meta.get("backend"),
                "source_artifact_sha256": sha(artifact), "scan_page": scan,
                "source": "Fresh source-scan Greek-column OCR", "image_sha256": record["image_sha256"],
                "region": record["region"], "prompt": meta["prompt"]}
            page_witnesses[expected[scan]["printed_page"]].append(witness)
            models_by_page[expected[scan]["printed_page"]].add(meta["model"])
    missing = [p for p in range(1, primary_pages + 1) if len(models_by_page[p]) < 2]
    if missing:
        raise ValueError(f"Two fresh model witnesses are required for all printed pages; missing: {missing}")
    return {"schema_version": 1, "source": SOURCE, "primary_source": primary_source,
        "primary_manifest": primary_manifest,
        "original_corpus_sha256": sha(raw), "witnesses": {str(page): readings
            for page, readings in sorted(page_witnesses.items())},
        "meibom_source_witnesses": {str(page): readings for page, readings in sorted(meibom_witnesses.items())}}


def repaired_outputs(root, inputs, before):
    original_rows = [json.loads(line) for line in before[f"data/corpus/{OLD}.jsonl"].splitlines()]
    registry = json.loads(before["data/source_registry.json"])
    from reviewed_manifestations import ensure_musical_work_records
    ensure_musical_work_records(registry, root)
    aliases = json.loads(before["data/passage_aliases.json"])
    outputs, changes = defaultdict(list), []
    jahn_primary = inputs.get("primary_source") == "jahn1882"
    primary_edition = JAHN_EDITION if jahn_primary else EDITION
    primary_source = inputs["primary_manifest"]["sources"]["jahn1882"] if jahn_primary else {
        "url": SOURCE["url"], "citation": SOURCE["title"], "license": "PD", "sha256": SOURCE["pdf_sha256"]}
    for row in original_rows:
        scan = scan_from_locus(row["locus"])
        assignment = page_assignment(scan)
        corrected = dict(row)
        target = assignment["work"]
        corrected.update(source_page=assignment, evidence="data/source_layouts/meibom-1652.json")
        if target == "paratext":
            path = PARATEXT
            corrected.update(urn="meibom-1652.edition-paratext", lang="grc", **{"class": assignment["class"]})
            corrected.pop("cts", None)
            destination = {"path": path, "locus": row["locus"]}
        else:
            corrected.update(urn=target, edition="qwen36-meibom-1652-legacy",
                cts=registry["works"][target]["aliases"]["cts"])
            path = f"data/corpus_secondary/{target}.jsonl"
            destination = {"path": path, "locus": row["locus"], "slug": target, "storage": "secondary"}
            if target == OLD and not jahn_primary:
                printed = assignment["printed_page"]
                destination = {"path": f"data/corpus/{OLD}.jsonl", "slug": OLD,
                    "locus": f"{assignment['book']}.{printed}", "scope": "printed-page",
                    "preserved_original": {"path": path, "locus": row["locus"]}}
        outputs[path].append(corrected)
        aliases.setdefault("aliases", {}).setdefault(OLD, {})[row["locus"]] = destination
        changes.append({"original_row": row, "corrected_row": corrected,
            "destination": destination, "text_changed": False,
            "evidence": "data/source_layouts/meibom-1652.json"})
    summaries, full_networks = [], {}
    primary = []
    page_limit = 97 if jahn_primary else 164
    for page in range(1, page_limit + 1):
        result = merge_witnesses(inputs["witnesses"][str(page)])
        full_networks[str(page)] = result
        compact = compact_corpus_consensus(result, {"path": AUDIT_DIR + "/word-networks.json.gz", "key": str(page)})
        book = (1 if page <= 37 else 2 if page <= 67 else 3) if jahn_primary else (1 if page <= 58 else 2 if page <= 111 else 3)
        row = {"urn": OLD, "edition": primary_edition, "locus": f"{book}.{page}",
            "cts": registry["works"][OLD]["aliases"]["cts"], "source": "ocr", "license": "PD",
            **compact, "corrections": ["collation"], "source_printed_page": page,
            "evidence": "data/ingest_reviews/jahn-aristides-fresh-witnesses.json" if jahn_primary else "data/source_layouts/meibom-1652.json"}
        primary.append(row)
        summaries.append({"printed_page": page, "locus": row["locus"],
            "original_text": [{"witness": w["id"], "text": w.get("original_text", w["text"]),
                "collation_input_text": w["text"], "preprocessing": w.get("preprocessing", []),
                "artifact_sha256": w["artifact_sha256"]} for w in inputs["witnesses"][str(page)]],
            "corrected_text": result["text"], "analysis_text": result["analysis_text"],
            "counts": result["ocr_consensus"]["counts"],
            "evidence": "ROVER word vote over the retained original and independent fresh scan readings"})
    output_bytes = {}
    for path, rows in outputs.items():
        existing = before.get(path)
        prefix = [json.loads(line) for line in existing.splitlines()] if existing else []
        identities = {(r["edition"], r["locus"]) for r in prefix}
        if any((r["edition"], r["locus"]) in identities for r in rows):
            raise ValueError(f"Meibom secondary destination already contains a routed reading: {path}")
        output_bytes[path] = jsonl(prefix + rows)
    output_bytes[f"data/corpus/{OLD}.jsonl"] = jsonl(primary)
    output_bytes[AUDIT_DIR + "/word-networks.json.gz"] = gzip.compress(dump(full_networks), mtime=0)
    output_bytes["data/passage_aliases.json"] = dump(aliases)
    work = registry["works"][OLD]
    old_key = work["default_edition"]
    if old_key in work["editions"]:
        work["editions"][old_key].update(servable=False,
            note="Historical whole-anthology assignment; original rows are retained by the issue52 audit and routed secondary witnesses.")
    new_key = f"{OLD}.{primary_edition}"
    work["editions"][new_key] = {"name": "Jahn 1882, merged scan OCR with explicit variants" if jahn_primary else "Meibom 1652, merged scan OCR with explicit variants",
        "provider": "ocr", "scheme": "book.printed-page", "editor": "Jahn, Albert" if jahn_primary else "Meibom, Marcus",
        "year": 1882 if jahn_primary else 1652, "source": primary_source["url"], "servable": True, "license": "PD",
        "scheme_inferred": False, "aliases": {}}
    work.update(default_edition=new_key, best_source="open_corpus")
    for start, end, target, base in RANGES:
        if target == OLD and not jahn_primary:
            continue
        registry["works"][target]["editions"][f"{target}.qwen36-meibom-1652-legacy"] = {
            "name": "Meibom 1652, routed historical OCR witness", "provider": "ocr",
            "scheme": "scan-page.line", "editor": "Meibom, Marcus", "year": 1652,
            "source": SOURCE["url"], "servable": True, "storage": "secondary",
            "license": "PD", "scheme_inferred": False, "aliases": {}}
    output_bytes["data/source_registry.json"] = dump(registry)
    sources = json.loads(before["data/inventory/ocr_edition_sources.json"])
    sources[primary_edition] = {"label": f"Aristides Quintilianus, De musica ({'Jahn1882' if jahn_primary else 'Meibom1652'}); independent fresh OCR word vote, with unresolved readings preserved",
        "url": primary_source["url"], "model": "Qwen3.6-27B and Qwen3.8-27B"}
    sources["qwen36-meibom-1652-legacy"] = {"label": "Meibom1652, routed historical OCR witnesses",
        "url": SOURCE["url"], "model": "Qwen3.6-27B"}
    output_bytes["data/inventory/ocr_edition_sources.json"] = dump(sources)
    output_bytes[AUDIT_DIR + "/changes.json"] = dump({"schema_version": 1,
        "timestamp": "2026-10-18", "source": SOURCE, "primary_source": primary_source,
        "primary_edition": primary_edition,
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/52",
        "assignments": changes, "text_changes": summaries,
        "outputs_sha256": {name: sha(raw) for name, raw in output_bytes.items()},
        "undo": "python3 scripts/repair_meibom_work_assignments.py --undo; rebuild derived outputs"})
    return output_bytes


def run_repair(root, mode, fresh_paths=(), original_dir=None, primary_source="jahn1882"):
    audit = root / AUDIT_DIR
    before_path, inputs_path = audit / "before.json.gz", audit / "witnesses.json.gz"
    if mode == "undo":
        record = json.loads((audit / "changes.json").read_text())
        for name, expected in record["outputs_sha256"].items():
            if sha((root / name).read_bytes()) != expected:
                raise ValueError(f"Refusing to overwrite a later change: {name}")
        before = json.loads(gzip.decompress(before_path.read_bytes()))
        for name, text in before.items():
            path = root / name
            if text is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(text)
        return
    if before_path.exists():
        before = json.loads(gzip.decompress(before_path.read_bytes()))
        inputs = json.loads(gzip.decompress(inputs_path.read_bytes()))
        if mode == "apply":
            mode = "check"
    else:
        if mode == "check":
            raise ValueError("The Meibom repair has not been applied")
        inputs = prepare_inputs(root, fresh_paths, original_dir, primary_source)
        names = [f"data/corpus/{OLD}.jsonl", "data/source_registry.json", "data/passage_aliases.json",
            "data/inventory/ocr_edition_sources.json", PARATEXT]
        names += [f"data/corpus_secondary/{slug}.jsonl" for slug in {p[2] for p in RANGES}]
        before = {name: (root / name).read_text() if (root / name).exists() else None for name in names}
    outputs = repaired_outputs(root, inputs, before)
    if mode == "check":
        for name, expected in outputs.items():
            path = root / name
            if not path.exists():
                raise ValueError(f"Meibom repair output is missing: {name}")
            if name in {"data/source_registry.json", "data/passage_aliases.json", "data/inventory/ocr_edition_sources.json"}:
                check_changed_fields(json.loads(before[name]), json.loads(expected), json.loads(path.read_text()), name)
            elif path.read_bytes() != expected:
                raise ValueError(f"Meibom repair differs from its archived inputs: {name}")
    elif mode == "apply":
        audit.mkdir(parents=True, exist_ok=True)
        before_path.write_bytes(gzip.compress(dump(before), mtime=0))
        inputs_path.write_bytes(gzip.compress(dump(inputs), mtime=0))
        for name, raw in outputs.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f"{len(outputs)} reproducible outputs; {len(inputs['witnesses'])} merged Aristides pages; all original rows preserved")


def check_changed_fields(original, expected, current, path):
    """Check this repair's metadata changes while allowing unrelated additions."""
    if isinstance(expected, dict):
        original = original if isinstance(original, dict) else {}
        if not isinstance(current, dict):
            raise ValueError(f"Changed Meibom metadata: {path}")
        for key, value in expected.items():
            if key not in original or original[key] != value:
                if key not in current:
                    raise ValueError(f"Missing Meibom metadata: {path}.{key}")
                check_changed_fields(original.get(key), value, current[key], path + "." + key)
        for key in original.keys() - expected.keys():
            if key in current:
                raise ValueError(f"Removed Meibom metadata was restored: {path}.{key}")
    elif current != expected:
        raise ValueError(f"Changed Meibom metadata: {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-manifest", action="store_true")
    modes = ap.add_mutually_exclusive_group()
    for name in ["apply", "check", "undo"]:
        modes.add_argument("--" + name, action="store_true")
    ap.add_argument("--fresh", type=Path, action="append", default=[])
    ap.add_argument("--original-dir", type=Path)
    ap.add_argument("--primary-source", choices=["jahn1882", "meibom1652"], default="jahn1882")
    args = ap.parse_args()
    if args.write_manifest:
        path = ROOT / "data/source_layouts/meibom-1652.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest(), ensure_ascii=False, indent=1) + "\n")
        jobs = ROOT / "data/ingest_reviews/meibom-aristides-fresh-witnesses.json"
        jobs.parent.mkdir(parents=True, exist_ok=True)
        jobs.write_text(json.dumps(fresh_jobs(), ensure_ascii=False, indent=1) + "\n")
    if args.apply or args.check or args.undo:
        run_repair(ROOT, "apply" if args.apply else "check" if args.check else "undo", args.fresh, args.original_dir, args.primary_source)
    print(f"{len(manifest()['fresh_aristides_pages'])} unique Aristides leaves")


if __name__ == "__main__":
    main()
