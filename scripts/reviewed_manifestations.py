#!/usr/bin/env python3
"""Rebuild reviewed edition credits from active, hash-checked admission audits.

This reads metadata and hashes corpus bytes. It never recomputes OCR votes or
deserializes compressed word networks. Work titles and canonical identities
remain independent of the coverage of an individual manifestation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MUSICAL_IDENTITIES = {
    "alypius.isagoge-musica": ("Alypius", "Isagoge musica"),
    "gaudentius.harmonica-introductio": ("Gaudentius", "Harmonica introductio"),
    "bacchius-geron.isagoge": ("Bacchius Geron", "Isagoge artis musicae"),
}
SCAN_WORKS = {
    "pappus-mathematics.synagoge": ("Hultsch", "Books II–V", "Books VI–VIII"),
    "apollonius-geom.conica": ("Heiberg", "Book IV", "Books I–III and the opening letter of Book IV"),
    "cassius-dio.historiae-romanae": ("Cary", "Books 36–55 through 55.9.4", "Early fragments and remaining Greek transmission"),
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _path(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "data":
        raise ValueError("Reviewed edition evidence must use a repository-relative data path")
    return root / path


def _sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(root, relative, expected):
    path = _path(root, relative)
    if not path.exists() or _sha(path) != expected:
        raise ValueError("Reviewed edition evidence changed: " + str(relative))
    return path


def _count(path):
    with path.open("rb") as stream:
        return sum(bool(line.strip()) for line in stream)


def _verify_compressed_source(root, relative, expected):
    digest = hashlib.sha256()
    with gzip.open(_path(root, relative), "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("Reviewed digital source changed: " + relative)


def musical_identity_metadata(root):
    """Recover three already-served identities omitted by the Canon rebuild.

    The committed crosswalk supplies CTS identity; existing First1K rows supply
    their edition and license. No new bibliographic identity is inferred.
    """
    root = Path(root)
    crosswalk = _load(root / "data/tlg_crosswalk.json") if (root / "data/tlg_crosswalk.json").exists() else {}
    output = {}
    for slug, (author, title) in MUSICAL_IDENTITIES.items():
        path = root / "data/corpus" / (slug + ".jsonl")
        if not path.exists():
            continue
        entry = crosswalk.get(slug)
        if not entry or not entry.get("cts"):
            raise ValueError("Missing checked musical-work crosswalk: " + slug)
        with path.open(encoding="utf-8") as stream:
            row = next((json.loads(line) for line in stream if line.strip()), None)
        if not row or row.get("urn") != slug or row.get("source") != "first1k":
            raise ValueError("Musical identity no longer has its checked First1K primary: " + slug)
        output[slug] = {"author": slug.split(".")[0], "author_name": author,
            "title": title, "aliases": {"cts": entry["cts"]},
            "edition": row["edition"], "provider": row["source"], "license": row["license"]}
    return output


def ensure_musical_work_records(document, root):
    """The admission importer also needs these identities before its first run."""
    for slug, value in musical_identity_metadata(root).items():
        if slug in document["works"]:
            continue
        document.setdefault("authors", {}).setdefault(value["author"], {
            "name": value["author_name"], "aliases": {}})
        key = slug + "." + value["edition"]
        document["works"][slug] = {"author": value["author"], "title": value["title"],
            "aliases": value["aliases"], "default_edition": key, "best_source": "open_corpus", "tags": [],
            "editions": {key: {"name": "First1KGreek (" + value["edition"] + ")",
                "provider": value["provider"], "scheme": "", "editor": "", "year": None,
                "source": "", "servable": True, "license": value["license"],
                "scheme_inferred": False, "aliases": {}}}}


def _edition(key, name, *, provider="ocr", scheme="", source="", license="PD",
             editor="", year=None, storage="primary", servable=True, note=""):
    return {"key": key, "name": name, "provider": provider, "scheme": scheme,
        "source": source, "license": license, "editor": editor, "year": year,
        "storage": storage, "servable": servable, "note": note}


def _meibom(root):
    relative = "data/corpus_changes/meibom-musical-anthology/changes.json"
    path = root / relative
    if not path.exists():
        return {}
    audit = _load(path)
    from repair_meibom_work_assignments import OLD, INPUT_SHA256, HISTORICAL_NOTE
    primary = f"data/corpus/{OLD}.jsonl"
    if _sha(root / primary) == INPUT_SHA256:
        return {}  # audit retained after exact unapply
    _verify(root, primary, audit["outputs_sha256"][primary])
    network = "data/corpus_changes/meibom-musical-anthology/word-networks.json.gz"
    if network in audit["outputs_sha256"]:
        _verify(root, network, audit["outputs_sha256"][network])
    primary_source = audit["primary_source"]
    jahn = audit["primary_edition"].startswith("jahn-")
    expected = 97 if jahn else 164
    if len(audit["text_changes"]) != expected or _count(root / primary) != expected:
        raise ValueError("Aristides reviewed page count changed")
    counts = Counter()
    for change in audit["assignments"]:
        target = change["destination"].get("slug")
        if target:
            counts[target] += 1
    output = {}
    for slug, count in sorted(counts.items()):
        secondary = f"data/corpus_secondary/{slug}.jsonl"
        _verify(root, secondary, audit["outputs_sha256"][secondary])
        source = audit["source"]
        edition = _edition("qwen36-meibom-1652-legacy", "Meibom 1652, routed historical OCR witness",
            scheme="scan-page.line", source=source["url"], editor="Meibom, Marcus", year=1652,
            storage="secondary", note="Historical source readings; the independent primary edition remains separate.")
        output[slug] = {"editions": [edition], "coverage_composition": {
            "policy": "separate-primary-and-historical-secondary", "manifest": relative,
            "manifest_sha256": _sha(path), "secondary_passages": count,
            "components": [{"edition": edition["key"], "storage": "secondary", "passages": count,
                "source": source["url"], "source_sha256": source["pdf_sha256"], "license": "PD"}]}}
    if len(output) != 9:
        raise ValueError("The Meibom routing audit must credit all nine constituent works")
    chosen = _edition(audit["primary_edition"],
        "Jahn 1882, merged scan OCR with explicit variants" if jahn else "Meibom 1652, merged scan OCR with explicit variants",
        scheme="book.printed-page", source=primary_source["url"],
        editor="Jahn, Albert" if jahn else "Meibom, Marcus", year=1882 if jahn else 1652)
    output[OLD]["editions"].append(chosen)
    output[OLD]["default_edition"] = chosen["key"]
    output[OLD]["coverage_composition"]["components"].insert(0, {
        "edition": chosen["key"], "storage": "primary", "passages": expected,
        "source": primary_source["url"], "source_sha256": primary_source["sha256"], "license": primary_source["license"]})
    output[OLD]["disable_editions"] = ["qwen36-aristides_quintilianus_meibom"]
    output[OLD]["disable_note"] = HISTORICAL_NOTE
    return output


def _scan_extensions(root):
    index_path = root / "data/corpus_extension_index.json"
    if not index_path.exists():
        return {}
    output, comparative_ids = {}, {}
    catalog = _load(index_path)
    for slug, entry in sorted(catalog.get("works", {}).items()):
        if slug not in SCAN_WORKS:
            continue
        extension = _verify(root, entry["path"], entry["sha256"])
        audit_refs = entry.get("audits", [entry["audit"]])
        if not audit_refs or len(set(audit_refs)) != len(audit_refs) or audit_refs[-1] != entry["audit"]:
            raise ValueError("Reviewed scan admission audit sequence changed")
        primary_path = f"data/corpus/{slug}.jsonl"
        primary = root / primary_path
        pages, selected, sources_by_id, all_digital = {}, {}, {}, {}
        audit_records, manifest_records, admission_regions = [], [], []
        digital_counts = Counter()
        for relative in audit_refs:
            audit_path = _path(root, relative)
            audit = _load(audit_path)
            if audit.get("word_networks_sha256"):
                _verify(root, str((audit_path.parent / "word-networks.json.gz").relative_to(root)), audit["word_networks_sha256"])
            manifest_path = audit_path.parent / "manifest.json"
            if _sha(manifest_path) != audit["manifest_sha256"]:
                raise ValueError("Reviewed scan manifest changed")
            manifest = _load(manifest_path)
            work_pages = [p for p in manifest["pages"] if p["work"] == slug]
            admitted = [p for p in work_pages if p.get("admission") != "comparative-paratext"]
            ids = {p["id"] for p in admitted}
            decisions = [d for d in audit["changes"] if d["work"] == slug and d["destination"] == "primary"]
            if len(ids) != len(admitted) or len(decisions) != len(ids) or {d["region_id"] for d in decisions} != ids:
                raise ValueError("Reviewed scan admission lacks its complete primary region set")
            if set(pages) & ids:
                raise ValueError("Reviewed scan admissions repeat a primary region")
            pages.update((p["id"], p) for p in admitted)
            for page in work_pages:
                if page["id"] in selected and selected[page["id"]] != page:
                    raise ValueError("Reviewed scan region identity changed between admissions")
                selected[page["id"]] = page
                source = {"id": page["source"], **manifest["sources"][page["source"]]}
                if source["id"] in sources_by_id and sources_by_id[source["id"]] != source:
                    raise ValueError("Reviewed source identity changed between admissions")
                sources_by_id[source["id"]] = source
            for identifier, component in audit.get("digital_sources", {}).items():
                if identifier in all_digital and all_digital[identifier] != component:
                    raise ValueError("Reviewed digital source identity changed between admissions")
                all_digital[identifier] = component
                _verify_compressed_source(root, str((audit_path.parent / ("digital-" + identifier + ".json.gz")).relative_to(root)), component["json_sha256"])
            digital_counts.update(decision["status"] for change in audit["changes"] if change["work"] == slug
                for decision in change.get("decisions", []) if decision.get("generator") == "scripts/bound_comparison_witness.py")
            audit_records.append({"path": relative, "sha256": _sha(audit_path),
                "primary_regions": len(ids), "comparative_regions": len(work_pages) - len(ids)})
            manifest_records.append({"path": str(manifest_path.relative_to(root)), "sha256": audit["manifest_sha256"]})
            admission_regions.append((ids, audit.get("admitted_extensions_sha256", {}).get(slug)))
            if relative == entry["audit"]:
                # Earlier audits describe their then-current corpus. Only the
                # latest audit hashes the complete consolidated primary files.
                _verify(root, primary_path, audit["outputs"][primary_path])
                _verify(root, entry["path"], audit["outputs"][entry["path"]])
        active_ids, admission_digests = set(), [hashlib.sha256() for _ in admission_regions]
        with extension.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                identifier = row.get("scan_region_id")
                if identifier not in pages or identifier in active_ids:
                    raise ValueError("Reviewed scan extension region set changed")
                active_ids.add(identifier)
                for (ids, _), digest in zip(admission_regions, admission_digests):
                    if identifier in ids:
                        digest.update((json.dumps(row, ensure_ascii=False) + "\n").encode())
        if active_ids != set(pages):
            raise ValueError("Reviewed scan admission lacks its complete primary region set")
        for (_, expected), digest in zip(admission_regions, admission_digests):
            if expected and expected != digest.hexdigest():
                raise ValueError("Reviewed scan admission readings changed after consolidation")
        sources = [sources_by_id[key] for key in sorted(sources_by_id)]
        digital = entry.get("digital_components", [])
        for component in digital:
            if all_digital.get(component["id"]) != component:
                raise ValueError("Participating digital-source credits changed outside the admission audit")
        licenses = sorted({source["license"] for source in sources} | {component["license"] for component in digital})
        public_domain = {"PD", "public-domain", "CC0/PD"}
        edition_license = "PD" if set(licenses) <= public_domain else "; ".join(licenses)
        if any(c["license"] == "CC-BY-SA-4.0" for c in digital):
            edition_license = "CC-BY-SA-4.0"
        editor, base_scope, added_scope = SCAN_WORKS[slug]
        planned_scope = added_scope
        admitted_books = sorted({str(p["book"]) for p in pages.values() if p.get("book")},
            key=lambda value: (int(value) if value.isdigit() else 999, value))
        if slug == "apollonius-geom.conica":
            if set(admitted_books) == {"4"}:
                added_scope = "Opening letter of Book IV"
            elif set(admitted_books) == {"1", "2", "3"}:
                added_scope = "Books I–III"
        edition = _edition(entry["edition"], f"{editor}, reviewed Greek scan additions ({added_scope})",
            scheme="volume.printed-page" if editor == "Cary" else "book.printed-page",
            source="; ".join(source["url"] for source in sources), license=edition_license, editor=editor,
            note="Complements the existing primary edition; comparison quotations and modern apparatus are separate.")
        witness_editions = [_edition("source-library-" + component["id"].split(".")[-1],
            f"Source Library, Cary volume {component['volume']}, bounded comparison witness",
            provider="greek_library", source=component["url"], license=component["license"], storage="audit", servable=False,
            note="Only independently bounded same-scan Greek body readings participate. Full credits, rights statements, and separate API notices remain in the admission audit.") for component in digital]
        output[slug] = {"editions": [edition, *witness_editions], "base_note": "Retained base edition: " + base_scope + ". Reviewed scan additions are complementary primary regions.", "coverage_composition": {
            "policy": "reviewed-primary-region-union", "manifest": entry["audit"], "manifest_sha256": audit_records[-1]["sha256"],
            "scan_manifest": manifest_records[-1]["path"], "scan_manifest_sha256": manifest_records[-1]["sha256"],
            "scan_manifests": manifest_records, "admission_audits": audit_records,
            "base_scope": base_scope, "addition_scope": added_scope,
            "planned_addition_scope": planned_scope, "admitted_books": admitted_books,
            "base_passages": _count(primary) - len(pages), "added_primary_regions": len(pages),
            "comparative_regions": len(selected) - len(pages), "source_editions": sources,
            "digital_components": digital, "comparison_sources": all_digital,
            "digital_comparison_counts": dict(digital_counts),
            "components": [{"edition": entry["edition"], "storage": "primary", "passages": len(pages),
                "licenses": licenses}],
            "qualification": "Surviving Greek transmission only; ancient losses are not reconstructed. " +
                ("Dio's direct text, excerpt supplements, epitomes, and unassigned early fragments remain distinct; the direct-text lacuna after 55.9.4 remains qualified." if editor == "Cary" else
                 "This edition's surviving book coverage does not redefine the complete ancient Work.")}}
        comparative_ids[slug] = set(selected) - set(pages)
    _attach_scan_comparisons(root, catalog, output, comparative_ids)
    return output


def _attach_scan_comparisons(root, catalog, output, comparative_ids):
    """Credit separately served comparisons without claiming primary coverage."""
    for slug, entries in sorted(catalog.get("comparative_admissions", {}).items()):
        if slug not in SCAN_WORKS:
            continue
        seen, datasets, sources, components, licenses = set(), [], {}, {}, set()
        verified_digital = set()
        for entry in entries:
            dataset = _verify(root, entry["path"], entry["sha256"])
            audit_path = _path(root, entry["audit"])
            audit = _load(audit_path)
            manifest_path = audit_path.parent / "manifest.json"
            if _sha(manifest_path) != entry["manifest_sha256"] or audit["manifest_sha256"] != entry["manifest_sha256"]:
                raise ValueError("Comparison admission manifest changed")
            manifest = _load(manifest_path)
            selected = {p["id"]: p for p in manifest["pages"] if p["work"] == slug and p.get("admission") == "comparative-paratext"}
            expected = entry["regions"]
            if len(set(expected)) != len(expected) or set(expected) != set(selected) or seen & set(expected):
                raise ValueError("Comparison admission repeats or changes its source region set")
            if audit.get("comparative_admissions", {}).get(slug) != entry or audit["outputs"].get(entry["path"]) != entry["sha256"]:
                raise ValueError("Comparison dataset differs from its admission audit")
            decisions = [d for d in audit["changes"] if d["work"] == slug and d["destination"] == "paratext"]
            if len(decisions) != len(expected) or {d["region_id"] for d in decisions} != set(expected):
                raise ValueError("Comparison source decisions are incomplete")
            if audit.get("word_networks_sha256"):
                _verify(root, str((audit_path.parent / "word-networks.json.gz").relative_to(root)), audit["word_networks_sha256"])
            identities = []
            with dataset.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("urn") != slug:
                        continue
                    identifier = row["scan_region_id"]
                    if identifier not in selected or row.get("kind") != "comparative-quotation":
                        raise ValueError("Comparison source row changed its routing destination")
                    identities.append(identifier)
                    licenses.add(row["license"])
                    for component in row.get("component_attribution", []):
                        if audit.get("digital_sources", {}).get(component["id"]) != component:
                            raise ValueError("Comparison digital-source credits changed")
                        identity = (entry["audit"], component["id"])
                        if identity not in verified_digital:
                            _verify_compressed_source(root, str((audit_path.parent / ("digital-" + component["id"] + ".json.gz")).relative_to(root)), component["json_sha256"])
                            verified_digital.add(identity)
                        if component["id"] in components and components[component["id"]] != component:
                            raise ValueError("Comparison digital-source identity changed")
                        components[component["id"]] = component
            if identities != expected:
                raise ValueError("Comparison dataset region order or count changed")
            for page in selected.values():
                source = {"id": page["source"], **manifest["sources"][page["source"]]}
                if source["id"] in sources and sources[source["id"]] != source:
                    raise ValueError("Comparison source edition changed between admissions")
                sources[source["id"]] = source
            seen.update(expected)
            datasets.append({**entry, "audit_sha256": _sha(audit_path), "comparative_regions": len(expected)})
        if not datasets:
            continue
        source_editions = [sources[key] for key in sorted(sources)]
        public_domain = {"PD", "public-domain", "CC0/PD"}
        license = "PD" if licenses <= public_domain else "CC-BY-SA-4.0" if "CC-BY-SA-4.0" in licenses else "; ".join(sorted(licenses))
        edition = _edition("scan-consensus-2026-10-18-comparisons", "Reviewed scan comparison quotations (separate from primary text)",
            scheme="volume.printed-page", source="; ".join(s["url"] for s in source_editions), license=license,
            storage="paratext", servable=False,
            note="Comparative quotations retain their own authorship and transmission labels and do not extend primary Work coverage or ordinary frequency counts.")
        value = output.setdefault(slug, {"editions": [], "coverage_composition": {
            "policy": "reviewed-comparison-regions-only", "components": [],
            "qualification": "Only separate comparison quotations have been admitted; this does not add primary Work passages or reconstruct ancient losses."}})
        value["editions"].append(edition)
        composition = value["coverage_composition"]
        composition.update({"comparative_policy": "separate-comparison-datasets-excluded-from-primary-frequencies",
            "comparative_admissions": datasets, "comparative_regions": len(seen | comparative_ids.get(slug, set())),
            "comparative_source_editions": source_editions,
            "comparative_digital_components": [components[key] for key in sorted(components)]})
        composition["components"].append({"edition": edition["key"], "storage": "paratext", "passages": len(seen), "license": license})


def _photius(root):
    relative = "data/corpus_changes/photius-bekker-coverage/coverage.json"
    path = root / relative
    if not path.exists():
        return {}
    report = _load(path)
    slug = report["work"]
    primary = root / "data/corpus" / (slug + ".jsonl")
    index_path = root / "data/corpus_changes/photius-bekker-index/changes.json"
    original_hashes = {report["original_body_sha256"]}
    if index_path.exists():
        original_hashes.add(_load(index_path)["source_sha256"])
    if _sha(primary) in original_hashes:
        return {}
    _verify(root, str(primary.relative_to(root)), report["new_corpus_sha256"])
    if (report["covered_authorial_scan_pages"] != 545 or report["added_passages"] != 309 or
            report["historical_body_passages"] != 3846 or report["preserved_index_passages"] != 501 or
            report["added_scan_ranges"] != [[13, 278], [379, 421]] or
            report["retained_scan_ranges"] != [[279, 378], [422, 557]] or
            _count(primary) != report["historical_body_passages"] + report["added_passages"]):
        raise ValueError("Photius complete authorial coverage count changed")
    if index_path.exists():
        _verify(root, "data/paratext/photius-bekker-index.jsonl", _load(index_path)["paratext_sha256"])
    source_library = report["source_library"]
    license_url = source_library["license"].get("url")
    if license_url != "https://creativecommons.org/licenses/by-sa/4.0/":
        raise ValueError("Photius Source Library license changed")
    _verify(root, "data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz", source_library["sha256"])
    models = {(f["model"], f["revision"]) for f in report["fresh_ocr_files"]}
    if len(models) < 2:
        raise ValueError("Photius needs independently pinned OCR components")
    for witness in report["fresh_ocr_files"]:
        _verify(root, witness["path"], witness["sha256"])
    bounds = source_library.get("body_comparison_audit")
    if bounds:
        _verify(root, bounds["path"], bounds["sha256"])
    scan = report["source_scan"]
    merged = _edition("bekker1824-independent-ocr-consensus", "Bekker 1824–1825, combined Greek body with retained variants",
        scheme="scan-page.line", source=scan["url"], license="CC-BY-SA-4.0", editor="Bekker, Immanuel", year=1824,
        note="Retained PD body plus new licensed consensus; bounded Source Library CC-BY-SA body readings participate in the merge.")
    library = _edition("source-library-local002", "Source Library local002, same-scan comparison witness",
        provider="greek_library", source=source_library["url"], license="CC-BY-SA-4.0", storage="audit", servable=False,
        note="Retained comparison witness; only bounded matching body text may vote. Attribution, source rights, and the separate API reservation notice are preserved in the admission audit.")
    components = [{"role": "retained-primary", "license": "PD", "passages": report["historical_body_passages"],
        "scan_ranges": report["retained_scan_ranges"]},
        {"edition": merged["key"], "role": "new-primary-consensus", "license": "CC-BY-SA-4.0",
            "passages": report["added_passages"], "scan_ranges": report["added_scan_ranges"]},
        {**source_library, "edition": library["key"], "role": "bounded-voting-or-comparison-witness", "license": source_library["license"],
            "source": source_library["url"], "sha256": source_library["sha256"],
            "rights": source_library.get("rights"), "separate_api_notice": source_library.get("separate_api_notice")},
        {"role": "fresh-scan-ocr-witnesses", "license": "CC-BY-4.0",
            "checkpoints": [{"model": model, "revision": revision} for model, revision in sorted(models)]}]
    return {slug: {"editions": [merged, library], "default_edition": merged["key"],
        "base_note": "Retained PD body on source scan pages 279–378 and 422–557; earlier pages and the later gap come from a separately licensed consensus.", "coverage_composition": {
        "policy": "complementary-page-union-with-licensed-consensus", "manifest": relative, "manifest_sha256": _sha(path),
        "covered_authorial_scan_pages": 545, "index_passages_in_separate_paratext": report["preserved_index_passages"],
        "components": components,
        "source_editions": [scan] + ([report["legacy_source"]] if report.get("legacy_source") else []),
        "source_scan_exceptions": report.get("source_scan_exceptions", []),
        "qualification": report["edition_scope"]}}}


def _cyril(root):
    relative = "data/corpus_changes/cyril-john-coverage/changes.json"
    path = root / relative
    if not path.exists():
        return {}
    audit = _load(path)
    slug = "cyrillus-theology.commentarii-in-joannem"
    primary = f"data/corpus/{slug}.jsonl"
    if _sha(root / primary) == audit["inputs"][primary]:
        return {}
    _verify(root, primary, audit["outputs"][primary])
    for relative_output, digest in audit["outputs"].items():
        if relative_output.startswith(("data/paratext/", "data/ocr_witnesses/")):
            _verify(root, relative_output, digest)
    expected = {"added_pg73": 528, "retained_pg74_john": 2578, "added_pg74_missing_leaves": 3,
                "title_paratext": 4, "held_other_works": 474}
    if audit["counts"] != expected or _count(root / primary) != 3109:
        raise ValueError("Cyril complementary-volume count changed")
    evidence = audit["evidence"]
    editions = [_edition("calfa-pg73-5895ab908dd4", "Calfa PG073 OCR, complementary first volume", provider="cgpg",
        scheme="volume.marker-page", source=evidence["source_url"], license=evidence["source_license"],
        editor="Migne, Jacques-Paul", year=1859),
        _edition("migne-pg74-gap-consensus-2026-10", "PG074 missing leaves, independent scan OCR consensus",
            scheme="volume.reference-scan", source=evidence["reference_scans"][1]["url"], editor="Migne, Jacques-Paul", year=1859)]
    return {slug: {"editions": editions,
        "base_note": "PG074 continuation beginning John 10:18; Books VII and VIII are fragmentary. Acts and Romans are separate works.",
        "coverage_composition": {
        "manifest": relative, "manifest_sha256": _sha(path), "volumes": ["PG073", "PG074"],
        "policy": "complementary-volume-union", "counts": expected,
        "components": [{"edition": editions[0]["key"], "volume": "PG073", "passages": 528,
                "license": evidence["source_license"], "source": evidence["source_url"],
                "source_sha256": evidence["source_sha256"], "attribution": evidence["attribution"]},
            {"edition": "migne-ocr-qwen36", "volume": "PG074", "passages": 2578, "license": "PD"},
            {"edition": editions[1]["key"], "volume": "PG074", "passages": 3, "license": "PD"}],
        "source_editions": evidence["reference_scans"],
        "qualification": "PG074 Books VII and VIII survive as fragments in this edition; this does not reconstruct lost continuous books."}}}


def reviewed_manifestation_metadata(root=ROOT):
    root = Path(root)
    return {**_meibom(root), **_scan_extensions(root), **_photius(root), **_cyril(root)}


def register_reviewed_manifestations(registry, root=ROOT):
    """Idempotently add active reviewed components after ordinary identities."""
    root = Path(root)
    from critical_text import load_critical_editions, register_critical_editions
    register_critical_editions(registry, load_critical_editions(root / "data"))
    for slug, value in musical_identity_metadata(root).items():
        registry.mint_author(value["author_name"], slug=value["author"])
        registry.mint_work(value["author"], value["title"], slug=slug, aliases=value["aliases"])
        registry.works[slug].best_source = "open_corpus"
        registry.mint_edition(slug, value["edition"], "First1KGreek (" + value["edition"] + ")",
            provider=value["provider"], license=value["license"])
    metadata = reviewed_manifestation_metadata(root)
    for slug, value in metadata.items():
        if slug not in registry.works:
            raise ValueError("Reviewed admission has no canonical registry Work: " + slug)
        work = registry.works[slug]
        if "coverage_composition" not in work.__dataclass_fields__:
            raise ValueError("Registry Work must support reviewed coverage_composition")
        previous = work.default_edition
        previous_composition = work.coverage_composition
        for edition in value["editions"]:
            key = registry.mint_edition(slug, edition["key"], edition["name"])
            record = work.editions[key]
            for field, content in edition.items():
                if field != "key":
                    setattr(record, field, content)
        work.default_edition = slug + "." + value["default_edition"] if value.get("default_edition") else previous
        for edition in value.get("disable_editions", []):
            record = work.editions.get(slug + "." + edition)
            if record:
                record.servable = False
                record.note = value.get("disable_note", "Historical whole-anthology assignment; exact readings survive in the routing audit and secondary witnesses.")
        composition = value["coverage_composition"]
        base_key = previous
        if value.get("default_edition") and previous == work.default_edition:
            base_key = next((c.get("edition") for c in previous_composition.get("components", [])
                             if c.get("role") == "retained-primary"), None)
        if base_key and base_key in work.editions:
            base = work.editions[base_key]
            if value.get("base_note"):
                base.note = value["base_note"]
            component = {"edition": base_key, "storage": base.storage, "license": base.license,
                "source": base.source, "provider": base.provider, "name": base.name}
            retained = next((c for c in composition["components"] if c.get("role") == "retained-primary" or
                c.get("edition") in {base_key, base_key.removeprefix(slug + ".")}), None)
            if retained is not None:
                retained.update(component)
            elif not value.get("default_edition"):
                component["role"] = "retained-primary"
                if "base_passages" in composition:
                    component["passages"] = composition["base_passages"]
                composition["components"].insert(0, component)
        work.coverage_composition = composition
        work.best_source = "open_corpus"
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from source_identity import Registry
    path = args.registry or args.root / "data/source_registry.json"
    registry = Registry.load(path)
    before = {slug: {"default": work.default_edition, "coverage": getattr(work, "coverage_composition", {}),
        "editions": {key: dict(vars(value)) for key, value in work.editions.items()}} for slug, work in registry.works.items()}
    metadata = register_reviewed_manifestations(registry, args.root)
    if args.check:
        from critical_text import load_critical_editions
        critical = load_critical_editions(args.root / "data")
        drift = [slug for slug in set(metadata) | set(musical_identity_metadata(args.root)) | set(critical)
            if before.get(slug) != {"default": registry.works[slug].default_edition,
                "coverage": getattr(registry.works[slug], "coverage_composition", {}),
                "editions": {key: dict(vars(value)) for key, value in registry.works[slug].editions.items()}}]
        if drift:
            parser.exit(1, "Reviewed manifestation metadata differs: " + ", ".join(sorted(drift)) + "\n")
    elif args.write:
        registry.save(path)
    from critical_text import load_critical_editions
    print(json.dumps({"active_reviewed_works": sorted(metadata),
        "musical_identities": sorted(musical_identity_metadata(args.root)),
        "critical_editions": sorted(load_critical_editions(args.root / "data"))}, indent=2))


if __name__ == "__main__":
    main()
