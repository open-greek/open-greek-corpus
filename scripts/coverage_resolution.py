"""Derive five reviewed coverage repairs from auditable current admissions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from scan_coverage_extensions import coverage_scope


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _publication(root):
    citation = root / "CITATION.cff"
    match = re.search(r'^version:\s*["\']?([^"\'\s]+)', citation.read_text(), re.M) if citation.exists() else None
    return {"declared_release": match[1] if match else None,
        "tracker_close_criterion": "Close only after these audited corpus bytes are in a tagged release; name that tag in the closing comment.",
        "reopen_when": "A newly identified surviving Greek source, missing edition page, incorrect work boundary, or invalidated source/reading audit changes this coverage evidence."}


def _pending(root, reason, **evidence):
    return {"complete": False, "status": "open-coverage-work", "reason": reason,
            **evidence, "publication": _publication(root)}


def _resolved(root, qualification, **evidence):
    return {"complete": True, "status": "coverage-repaired-with-transmission-qualification",
            "qualification": qualification, **evidence, "publication": _publication(root)}


def _check_mathematical_citations(root, slug):
    from repair_mathematical_citations import AUDIT, RULES
    audit_path = root / AUDIT / "changes.json"
    if not audit_path.exists():
        raise ValueError("The scan-checked mathematical citation audit is missing")
    audit = json.loads(audit_path.read_text())
    corpus_path = root / "data/corpus" / (slug + ".jsonl")
    rows = {row["locus"]: row for row in map(json.loads, corpus_path.read_text().splitlines())}
    scheme = json.loads((root / "data/citation_aliases.json").read_text())["schemes"][RULES[slug]["scheme"]]
    changes = audit["changes"][slug]
    if set(scheme["aliases"]) != {change["original_locus"] for change in changes}:
        raise ValueError("Historical mathematical citation destinations changed")
    for change in changes:
        row = rows[change["corrected_locus"]]
        expected = {"slug": slug, "path": f"data/corpus/{slug}.jsonl", "locus": row["locus"]}
        if (scheme["aliases"][change["original_locus"]] != expected or
                hashlib.sha256(row["text"].encode()).hexdigest() != change["text_sha256"] or
                row.get("source_citation") != {"scheme": RULES[slug]["scheme"], "locus": change["original_locus"]}):
            raise ValueError("A mathematical reading or historical citation changed outside its audit")
    return {"path": str(audit_path.relative_to(root)), "sha256": _sha(audit_path),
            "preserved_historical_citations": len(changes)}


def _scan_resolution(root, slug):
    scope = coverage_scope(root, slug)
    if (not scope or scope["status"] != "reviewed-primary-regions-admitted"
            or scope.get("remaining_reviewed_comparative_regions", 0)):
        return _pending(root, "Reviewed missing Greek scan regions have not all been admitted.", scope=scope)
    from ingest_scan_coverage import verify_integrity
    audited = []
    for relative in dict.fromkeys(scope["admission_audits"] + scope.get("comparative_admission_audits", [])):
        audit = root / relative
        verify_integrity(audit.parent, root)
        audited.append({"path": str(audit.relative_to(root)), "sha256": _sha(audit)})
    citation = _check_mathematical_citations(root, slug) if slug != "cassius-dio.historiae-romanae" else None
    return _resolved(root, scope["transmission_limit"], scope=scope,
        admission_audits=audited,
        **({"citation_audit": citation} if citation else {}))


def _photius_fresh_witnesses(root, report, manifests, prepare_report):
    """Delegate all original/retry/supplement pins to the canonical authority."""
    inputs, models, evidence = prepare_report(root, report, manifests)
    retained = {value["sha256"]: (value["model"], value["revision"])
                for value in report["fresh_ocr_files"]}
    if len(retained) != len(report["fresh_ocr_files"]):
        raise ValueError("Repeated Photius raw witness archive")
    if {hashlib.sha256(raw).hexdigest(): (metadata["model"], metadata["revision"])
            for raw, metadata, predictions in inputs} != retained:
        raise ValueError("Photius retained witness identity differs from its validated source")
    expected = {page["id"] for request in manifests for page in request["pages"]}
    if len(models) < 2 or any(set(pages) != expected for pages in models.values()):
        raise ValueError("Photius coverage lacks complete independent witnesses")
    return models


def _photius_coverage_position(row, mapping):
    from repair_photius_index import PAGE
    legacy = PAGE.fullmatch(row["locus"])
    if legacy:
        # This logical position is distinct from the legacy physical citation,
        # which a later reviewed correction may now state explicitly.
        return int(legacy[1]) + mapping["logical_combined_position_offset"]
    physical = row.get("physical_refs", {}).get("scan_page")
    if type(physical) is not int:
        raise ValueError("Photius row lacks a reviewed physical citation")
    return physical


def _photius_resolution(root):
    path = root / "data/corpus_changes/photius-bekker-coverage/coverage.json"
    if not path.exists():
        return _pending(root, "The complete Bekker authorial page-range admission has not been applied.")
    report = json.loads(path.read_text())
    full_networks = report.get("full_networks", {})
    if (report.get("covered_authorial_scan_pages") != 545 or report.get("added_passages") != 309 or
            report.get("added_scan_ranges") != [[13, 278], [379, 421]] or
            report.get("retained_scan_ranges") != [[279, 378], [422, 557]] or
            full_networks.get("entries") != 310):
        return _pending(root, "Photius admission does not cover all 545 checked authorial scan pages.")
    if _sha(root / full_networks["path"]) != full_networks["sha256"]:
        raise ValueError("Photius archived full word networks changed")
    from ingest_photius_coverage import prepare_report_inputs, load_source_library, LEGACY_SOURCE, SOURCE_SCAN_EXCEPTIONS
    mapping = report.get("retained_page_mapping", {})
    if (report.get("legacy_source") != LEGACY_SOURCE or report.get("source_scan_exceptions") != SOURCE_SCAN_EXCEPTIONS or
            mapping.get("exceptions") != SOURCE_SCAN_EXCEPTIONS or mapping.get("printed_page_offset") != 265 or
            mapping.get("logical_combined_position_offset") != 277 or mapping.get("logical_positions_are_physical_citations") is not False or
            report.get("covered_authorial_printed_pages") != 545):
        raise ValueError("Photius composite scan citations or duplicate-page exceptions changed")
    comparison_audit = report["source_library"]["body_comparison_audit"]
    if _sha(root / comparison_audit["path"]) != comparison_audit["sha256"]:
        raise ValueError("Photius comparison body-window evidence changed")
    manifests = [json.loads((path.parent / name).read_text()) for name in
                 ("scan-request.json", "later-gap-request.json")]
    _photius_fresh_witnesses(root, report, manifests, prepare_report_inputs)
    load_source_library(path.parent / "source-library-local002.json.gz")
    primary = root / "data/corpus/photius.bibliotheca.jsonl"
    from repair_photius_apparatus import restore_legacy_bytes, active_metadata
    legacy = restore_legacy_bytes(primary.read_bytes(), root)
    if hashlib.sha256(legacy).hexdigest() != report["new_corpus_sha256"]:
        raise ValueError("Photius primary text differs from its coverage admission")
    rows = [json.loads(line) for line in primary.read_text().splitlines()]
    covered = {_photius_coverage_position(row, mapping) for row in rows}
    if covered != set(range(13, 558)):
        raise ValueError("Photius authorial scan range is incomplete")
    from repair_photius_index import check as check_index
    index_report = check_index(root)
    if index_report["index_rows"] != report["preserved_index_passages"]:
        raise ValueError("Photius index preservation count changed")
    return _resolved(root,
        "The 545 checked Bekker authorial printed pages are represented across the combined and retained legacy scans, including the prefatory letter. Two repeated pages in the combined scan are supplied by the correct retained legacy pages, with explicit source exceptions. Greek index matter remains separate paratext. Physical scan citations do not invent codex-level paragraph mappings, and unresolved OCR readings remain explicit.",
        admission_audit={"path": str(path.relative_to(root)), "sha256": _sha(path)},
        **({"editorial_layer": active_metadata(root)} if primary.read_bytes() != legacy else {}),
        covered_authorial_scan_pages=report["covered_authorial_scan_pages"],
        covered_authorial_printed_pages=report["covered_authorial_printed_pages"],
        coverage_position_meaning=report["coverage_position_meaning"],
        source_scan_exceptions=report["source_scan_exceptions"],
        added_passages=report["added_passages"],
        preserved_index_passages=report["preserved_index_passages"])


def _john_resolution(root):
    path = root / "data/corpus_changes/cyril-john-coverage/changes.json"
    if not path.exists():
        return _pending(root, "Complementary PG 73, the PG 74 missing leaves and the work-boundary repair have not all been applied.")
    report = json.loads(path.read_text())
    expected = {"added_pg73": 528, "retained_pg74_john": 2578,
                "added_pg74_missing_leaves": 3, "title_paratext": 4, "held_other_works": 474}
    if report.get("counts") != expected:
        return _pending(root, "Cyril admission does not contain every reviewed complementary-volume and boundary component.")
    from repair_john_coverage import CORPUS, PARATEXT, WITNESS, SOURCE, RAW_SHA, fresh_blobs
    import gzip
    for relative in (CORPUS, PARATEXT, WITNESS):
        if _sha(root / relative) != report["outputs"][relative]:
            raise ValueError("Cyril primary text or preserved witness changed: " + relative)
    if hashlib.sha256(gzip.decompress((root / SOURCE).read_bytes())).hexdigest() != RAW_SHA:
        raise ValueError("Calfa PG 73 source changed")
    fresh = json.loads(gzip.decompress((path.parent / "fresh-witnesses.json.gz").read_bytes()))
    if fresh_blobs(root, [value["raw_jsonl"].encode() for value in fresh["archives"]]) != fresh:
        raise ValueError("Cyril independent missing-leaf witnesses changed")
    rows = [json.loads(line) for line in (root / CORPUS).read_text().splitlines()]
    if (sum(row["locus"].startswith("PG073.") for row in rows) != 528 or
            sum(row["locus"].startswith("pg074_") for row in rows) != 2578 or
            sum(row["locus"].startswith("PG074.reference-scan") for row in rows) != 3 or len(rows) != 3109):
        raise ValueError("Cyril current primary rows lack a reviewed volume or missing leaf")
    return _resolved(root,
        "The complementary PG 73 and PG 74 commentary material is represented, including three missing PG 74 leaves. Volume title matter is separate paratext, and Acts/Romans readings retain their distinct work identities. Books VII and VIII survive as fragments in this edition; no lost continuous text is reconstructed. The PG 73 witness remains identified as Calfa OCR rather than corrected text.",
        admission_audit={"path": str(path.relative_to(root)), "sha256": _sha(path)},
        counts=report["counts"])


def resolution(root: Path, slug: str):
    root = Path(root)
    if slug in {"pappus-mathematics.synagoge", "apollonius-geom.conica", "cassius-dio.historiae-romanae"}:
        return _scan_resolution(root, slug)
    if slug == "photius.bibliotheca":
        return _photius_resolution(root)
    if slug == "cyrillus-theology.commentarii-in-joannem":
        return _john_resolution(root)
    return _pending(root, "This work has no reviewed completion check.")
