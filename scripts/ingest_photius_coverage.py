#!/usr/bin/env python3
"""Merge independent witnesses of Bekker's missing Photius first volume.

All fresh predictions and the same-scan Source Library transcription survive.
The full first-volume page range and a second-volume overlap are required;
failed or truncated outputs cannot silently count as completed coverage.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re

from ocr_consensus import compact_corpus_consensus, merge_witnesses
from bound_comparison_witness import bound_comparison_witness
from photius_retries import allowed_retry_ids, apply_all_reviewed_retries, review_paths
from prepare_photius_coverage import build as scan_manifest, build_later_gap
from repair_photius_index import ROOT, SLUG, CORPUS, ARCHIVE as INDEX_ARCHIVE, generate as index_split
from audit_photius_fresh import audit as audit_outcomes

ARCHIVE = Path("data/corpus_changes/photius-bekker-coverage")
SOURCE_LIBRARY_SHA256 = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
REPORT = ARCHIVE / "coverage.json"
SOURCE_URL = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg4040/tlg001/local002.json.gz"
LEGACY_SOURCE = {
    "url": "https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf",
    "sha256": "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb",
    "edition": "Bekker 1825, second volume", "license": "public-domain", "pdf_pages": 321}
SOURCE_SCAN_EXCEPTIONS = [
    {"logical_combined_position": 446, "authorial_printed_page": 434,
     "combined_scan_printed_page": 334, "retained_legacy_scan_page": 169,
     "source": LEGACY_SOURCE,
     "evidence": "Combined scan 446 repeats printed page 334 from scan 346. The retained historical page 169 matches printed page 434 in the separate second-volume scan."},
    {"logical_combined_position": 447, "authorial_printed_page": 435,
     "combined_scan_printed_page": 335, "retained_legacy_scan_page": 170,
     "source": LEGACY_SOURCE,
     "evidence": "Combined scan 447 repeats printed page 335 from scan 347. The retained historical page 170 matches printed page 435 in the separate second-volume scan."}]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def load_prediction(path, manifests, allowed_failed_ids=frozenset()):
    raw = path.read_bytes()
    lines = raw.decode().splitlines()
    if not lines:
        raise ValueError("Empty OCR witness")
    metadata = json.loads(lines[0])["_meta"]
    requests = {sha(encode(manifest)): manifest for manifest in manifests}
    manifest = requests.get(metadata["manifest_sha256"])
    if manifest is None or metadata["prompt"] != manifest["prompt"]:
        raise ValueError("OCR witness belongs to another scan manifest or prompt")
    rows = {}
    expected = {page["id"]: page for page in manifest["pages"]}
    for line in lines[1:]:
        row = json.loads(line)
        identifier = row["id"]
        if identifier in rows or identifier not in expected:
            raise ValueError("Repeated or unknown OCR page")
        if (row["scan_page"] != expected[identifier]["scan_page"] or row["source"] != expected[identifier]["source"]
                or row.get("region", [0, 0, 1, 1]) != expected[identifier]["region"]):
            raise ValueError("OCR page geometry differs from the pinned request")
        suffix = expected[identifier].get("prompt_suffix", manifest["sources"][row["source"]].get("prompt_suffix", ""))
        prompt = manifest["prompt"] + (" " + suffix if suffix else "")
        if row.get("prompt_sha256") != sha(prompt.encode()):
            raise ValueError("OCR page prompt differs from the pinned request")
        if identifier not in allowed_failed_ids and (row.get("error") or row.get("finish_reason") != "stop"
                or not isinstance(row.get("raw_prediction"), str) or not row["raw_prediction"].strip()):
            raise ValueError("Failed, empty, or truncated Photius prediction")
        if identifier not in allowed_failed_ids and len(re.findall(r"[Ͱ-Ͽἀ-῿]+", row["raw_prediction"])) < 20:
            raise ValueError("Photius page lacks a substantive Greek transcription")
        rows[identifier] = {**row, "artifact_sha256": sha((sha(raw) + ":" + identifier).encode()),
                            "prediction_record_sha256": sha(line.encode())}
    if set(rows) != set(expected):
        raise ValueError("Photius witness does not cover all requested pages")
    return raw, metadata, rows


def load_source_library(path):
    raw = path.read_bytes()
    if sha(raw) != SOURCE_LIBRARY_SHA256:
        raise ValueError("Source Library comparison witness changed")
    document = json.loads(gzip.decompress(raw))
    if (document["id"] != "tlg4040.tlg001.local002" or document["origin"]["id"] != "source-library"
            or document["license"]["url"] != "https://creativecommons.org/licenses/by-sa/4.0/"):
        raise ValueError("Source Library identity or edition license changed")
    rows = {}
    for section in document["sections"]:
        page = int(section["label"].removeprefix("Page s"))
        if section.get("children") or any(block["type"] != "paragraph" for block in section["blocks"]):
            raise ValueError("Unreviewed Source Library structure")
        if page in rows:
            raise ValueError("Repeated Source Library page")
        text = "\n".join(block["text"] for block in section["blocks"])
        rows[page] = {"id": "source-library-local002", "text": text,
                      "artifact_sha256": sha(encode(section)), "vote_group": "source-library-local002",
                      "source_file_sha256": SOURCE_LIBRARY_SHA256,
                      "license": "CC-BY-SA-4.0", "source_url": SOURCE_URL,
                      "source_section": section["id"]}
    return raw, document, rows


def prepare_fresh_inputs(paths, manifests, retry_paths=(), retry_review=None, *,
                         allow_unreviewed_retry_preparation=False, supplement_paths=()):
    """Validate complete original runs and any separately reviewed retry."""
    reviews = review_paths(retry_review)
    if bool(retry_paths) != bool(reviews):
        raise ValueError("Retry predictions require a separate completed source review")
    if supplement_paths and not reviews:
        raise ValueError("Retry supplements require a separate completed source review")
    all_pages = {page["id"]: page for request in manifests for page in request["pages"]}
    def load(path):
        meta = json.loads(path.read_bytes().splitlines()[0])["_meta"]
        allowed = allowed_retry_ids((meta["model"], meta["revision"]), reviews, allow_unreviewed_retry_preparation)
        return load_prediction(path, manifests, allowed)
    inputs = sorted((load(path) for path in paths),
                    key=lambda item: (item[1]["model"], item[1]["revision"], item[1]["manifest_sha256"], sha(item[0])))
    models = {}
    for raw, metadata, rows in inputs:
        identity = (metadata["model"], metadata["revision"])
        destination = models.setdefault(identity, {})
        for key, row in rows.items():
            if key in destination:
                raise ValueError("Repeated checkpoint/page attempt needs an explicit review choice")
            destination[key] = (raw, metadata, row)
    if len(models) < 2:
        raise ValueError("Two independently pinned model checkpoints are required")
    if any(set(rows) != set(all_pages) for rows in models.values()):
        raise ValueError("Each checkpoint must cover both missing-volume requests")
    retry_evidence = apply_all_reviewed_retries(models, retry_paths, reviews, supplement_paths) if reviews else []
    return inputs, models, retry_evidence


def prepare_report_inputs(root, report, manifests):
    """Replay exact archived original, retry, and supplement authority from a report."""
    def checked(pin):
        relative = Path(pin["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Archive pins must use repository-relative paths")
        path = root / relative
        if sha(path.read_bytes()) != pin["sha256"]:
            raise ValueError("Archived Photius input differs from its report pin")
        return path
    originals = [checked(pin) for pin in report["fresh_ocr_files"]]
    reported = report.get("reviewed_retries")
    if reported is None:
        reported = [report["reviewed_retry"]] if report.get("reviewed_retry") else []
    retry_paths, reviews, supplement_paths = [], [], []
    for retry in reported:
        checked(retry["manifest"])
        reviews.append(checked(retry["source_review"]))
        retry_paths.extend(checked(pin) for pin in retry["raw_files"])
        for supplement in retry.get("supplements", []):
            checked(supplement["manifest"])
            supplement_paths.extend(checked(pin) for pin in supplement["raw_files"])
    inputs, models, evidence = prepare_fresh_inputs(originals, manifests, retry_paths, reviews,
                                                  supplement_paths=supplement_paths)
    actual_originals = {sha(raw): (meta["model"], meta["revision"]) for raw, meta, _ in inputs}
    if (len(actual_originals) != len(report["fresh_ocr_files"])
            or actual_originals != {p["sha256"]: (p["model"], p["revision"]) for p in report["fresh_ocr_files"]}):
        raise ValueError("Photius original metadata differs from its validated source")
    if len(evidence) != len(reported):
        raise ValueError("Photius report omits a canonical retry review")
    for retry in reported:
        matches = [item for item in evidence if item["source_review_sha256"] == retry["source_review"]["sha256"]]
        if len(matches) != 1:
            raise ValueError("Repeated or absent Photius review in report")
        item = matches[0]
        def runs(values):
            return sorted((r["sha256"], r["model"], r["revision"]) for r in values)
        def retained(values):
            return sorted((r["sha256"], r["metadata"]["model"], r["metadata"]["revision"]) for r in values)
        if (retry["manifest"]["sha256"] != item["manifest_sha256"]
                or retry["page_id"] != item["manifest"]["retry_of"]["page_id"]
                or retry["scan_page"] != item["manifest"]["pages"][0]["scan_page"]
                or runs(retry["raw_files"]) != retained(item["raw_files"])
                or sorted((p["model"], p["revision"]) for p in retry["checkpoints"]) !=
                   sorted((r["metadata"]["model"], r["metadata"]["revision"]) for r in item["raw_files"])
                or sorted(retry["original_artifacts_sha256"]) != sorted(item["review"]["original_artifacts_sha256"])):
            raise ValueError("Photius retry report differs from its canonical review")
        expected = {s["manifest_sha256"]: s for s in item["supplements"]}
        supplied = retry.get("supplements", [])
        if len(supplied) != len(expected) or {s["manifest"]["sha256"] for s in supplied} != set(expected):
            raise ValueError("Photius supplement report differs from its canonical review")
        for supplement in supplied:
            if runs(supplement["raw_files"]) != retained(expected[supplement["manifest"]["sha256"]]["raw_files"]):
                raise ValueError("Photius supplement raw metadata differs from its canonical review")
    if report.get("fresh_outcome_quality") is not None:
        checked(report["fresh_outcome_quality"])
        reproduced = outcome_quality([*originals, *retry_paths, *supplement_paths], models)
        if sha(encode(reproduced)) != report["fresh_outcome_quality"]["sha256"]:
            raise ValueError("Photius outcome quality audit differs from the archived source readings")
    return inputs, models, evidence


def outcome_quality(paths, models):
    """Keep all screened outcomes and distinguish held attempts from voting parts."""
    report = audit_outcomes(paths)
    dispositions = {}
    for checkpoint, records in models.items():
        for identifier, (_, metadata, row) in records.items():
            key = (*checkpoint, metadata["manifest_sha256"], identifier)
            assembly = row.get("reviewed_retry")
            if assembly is None:
                dispositions[key] = {"admission_disposition": "retained-original-vote"}
                continue
            review = {"completed_source_review_sha256": assembly["source_review_sha256"]}
            dispositions[key] = {**review, "admission_disposition": "held-original-attempt"}
            supplemental_ids = {p["id"]: s["manifest_sha256"] for s in assembly.get("supplements", []) for p in s["records"]}
            for part in assembly["strips"]:
                request = supplemental_ids.get(part["id"], assembly["manifest_sha256"])
                dispositions[(*checkpoint, request, part["id"])] = {
                    **review, "admission_disposition": "accepted-source-reviewed-assembly-part"}
            for part in assembly.get("held_retry_strips", []):
                source = next((s for s in assembly.get("held_retry_strip_sources", []) if s["id"] == part["id"]), {})
                request = source.get("manifest_sha256", assembly["manifest_sha256"])
                dispositions[(*checkpoint, request, part["id"])] = {
                    **review, "admission_disposition": ("held-source-confirmed-degraded-retry-strip"
                        if part.get("finish_reason") == "stop" and not part.get("error") else "held-failed-retry-strip")}
    for row in report["outcomes"]:
        key = (row["model"], row["revision"], row["manifest_sha256"], row["id"])
        if key not in dispositions:
            raise ValueError("An OCR outcome lacks an explicit admission disposition")
        row.update(dispositions[key])
    report["policy"] = "Every original and retry outcome remains screened. Source-reviewed assemblies contribute once per checkpoint; held attempts never add votes. Review flags preserve uncertainty and select no reading."
    return report


def generate(paths, source_library, root=ROOT, *, retry_paths=(), retry_review=None, supplement_paths=()):
    manifest = scan_manifest()
    manifests = [manifest, build_later_gap()]
    all_pages = {page["id"]: page for request in manifests for page in request["pages"]}
    inputs, models, retry_evidence = prepare_fresh_inputs(paths, manifests, retry_paths, retry_review,
                                                       supplement_paths=supplement_paths)
    source_raw, source_document, source_rows = load_source_library(source_library)
    original = gzip.decompress((root / INDEX_ARCHIVE / "before.jsonl.gz").read_bytes())
    body, index, aliases, index_audit = index_split(original)
    artifacts, added, page_reports, networks, comparisons = {}, [], [], {}, {}
    network_path = ARCHIVE / "full-networks.json.gz"
    for raw, metadata, rows in inputs:
        artifacts[ARCHIVE / "witnesses" / (sha(raw) + ".jsonl")] = raw
    artifacts[ARCHIVE / "source-library-local002.json.gz"] = source_raw
    artifacts[ARCHIVE / "scan-request.json"] = encode(manifest)
    artifacts[ARCHIVE / "later-gap-request.json"] = encode(manifests[1])
    quality_path = ARCHIVE / "fresh-outcome-quality.json"
    quality = outcome_quality([*paths, *retry_paths, *supplement_paths], models)
    artifacts[quality_path] = encode(quality)
    retry_reports = []
    for evidence in retry_evidence:
        retry_directory = ARCHIVE / "retry" / evidence["manifest"]["retry_of"]["page_id"] / evidence["source_review_sha256"]
        retry_manifest = retry_directory / "scan-request.json"
        retry_source_review = retry_directory / "source-review.json"
        artifacts[retry_manifest] = encode(evidence["manifest"])
        artifacts[retry_source_review] = evidence["review_raw"]
        retained_runs = []
        for run in evidence["raw_files"]:
            path = retry_directory / (run["sha256"] + ".jsonl")
            artifacts[path] = run["raw"]
            retained_runs.append({"path": path.as_posix(), "sha256": run["sha256"],
                                  "model": run["metadata"]["model"], "revision": run["metadata"]["revision"]})
        supplemental_reports = []
        for supplement in evidence["supplements"]:
            directory = retry_directory / "supplement" / supplement["manifest_sha256"]
            request = directory / "scan-request.json"
            artifacts[request] = encode(supplement["manifest"])
            supplemental_runs = []
            for run in supplement["raw_files"]:
                path = directory / (run["sha256"] + ".jsonl")
                artifacts[path] = run["raw"]
                supplemental_runs.append({"path": path.as_posix(), "sha256": run["sha256"],
                                          "model": run["metadata"]["model"], "revision": run["metadata"]["revision"]})
            supplemental_reports.append({"manifest": {"path": request.as_posix(), "sha256": supplement["manifest_sha256"]},
                                         "raw_files": supplemental_runs})
        retry_reports.append({"manifest": {"path": retry_manifest.as_posix(), "sha256": evidence["manifest_sha256"]},
                        "source_review": {"path": retry_source_review.as_posix(), "sha256": evidence["source_review_sha256"]},
                        "raw_files": retained_runs,
                        "supplements": supplemental_reports,
                        "original_artifacts_sha256": evidence["review"]["original_artifacts_sha256"],
                        "page_id": evidence["manifest"]["retry_of"]["page_id"],
                        "scan_page": evidence["manifest"]["pages"][0]["scan_page"],
                        "checkpoints": sorted(({"model": run["metadata"]["model"], "revision": run["metadata"]["revision"]}
                                               for run in evidence["raw_files"]), key=lambda value: (value["model"], value["revision"])),
                        "policy": "Original full-page attempts remain held evidence. Only selected checkpoint/page pairs receive one assembled replacement vote."})
    for page in sorted(all_pages.values(), key=lambda p: p["scan_page"]):
        witnesses = []
        for checkpoint, rows in sorted(models.items()):
            raw, metadata, row = rows[page["id"]]
            identity = metadata["model"] + "@" + metadata["revision"]
            witness = {"id": identity, "text": row["raw_prediction"],
                              "artifact_sha256": row["artifact_sha256"],
                              "vote_group": identity, "model": metadata["model"],
                              "revision": metadata["revision"], "image_sha256": row["image_sha256"],
                              "raw_file_sha256": sha(raw), "license": "CC-BY-4.0"}
            if row.get("reviewed_retry") is not None:
                assembly = row["reviewed_retry"]
                witness.update(text=assembly["accepted_text"], artifact_sha256=assembly["artifact_sha256"],
                               raw_file_sha256=assembly["raw_file_sha256"],
                               whole_page_image_sha256=witness.pop("image_sha256"),
                               reviewed_retry=assembly)
            witnesses.append(witness)
        if page["scan_page"] in source_rows:
            bounded, decision = bound_comparison_witness(witnesses, source_rows[page["scan_page"]])
            comparisons[str(page["scan_page"])] = {"scan_page": page["scan_page"],
                "role": page["role"],
                "source_file_sha256": SOURCE_LIBRARY_SHA256, "date": "2026-10-18", **decision}
            if bounded is not None:
                witnesses.append(bounded)
        consensus = merge_witnesses(witnesses)
        network_key = str(page["scan_page"])
        networks[network_key] = consensus
        compact = compact_corpus_consensus(consensus, {"path": network_path.as_posix(), "key": network_key})
        page_reports.append({"scan_page": page["scan_page"], "printed_page": page["printed_page"],
                             "role": page["role"], "witnesses": len(witnesses),
                             "counts": consensus["ocr_consensus"]["counts"],
                             "surface_sha256": sha(consensus["text"].encode())})
        if page["role"] == "overlap-check":
            artifacts[ARCHIVE / "codex230-overlap.json"] = encode({"scan_page": page["scan_page"], **consensus})
            continue
        row = {"urn": SLUG, "cts": "urn:cts:greekLit:tlg4040.tlg001",
               "edition": "bekker1824-independent-ocr-consensus", "source": "ocr", "license": "CC-BY-SA-4.0",
               "language": "grc", "locus": f"photius_bekker1824_{page['scan_page']:04d}.1",
               "physical_refs": {"scan_page": page["scan_page"], "printed_page": page["printed_page"],
                                 "edition": "Bekker 1824-1825", "scan_sha256": manifest["sources"][page["source"]]["sha256"]},
               **compact}
        added.append(row)
    prefix = ("\n".join(json.dumps(r, ensure_ascii=False) for r in added) + "\n").encode()
    existing_lines = body.decode().splitlines(keepends=True)
    existing = [(int(re.search(r"_(\d{4})[.]", json.loads(line)["locus"])[1]) + 277, line) for line in existing_lines]
    if [page for page, line in existing] != sorted(page for page, line in existing):
        raise ValueError("Historical Photius body is not in physical page order")
    new = [(row["physical_refs"]["scan_page"], json.dumps(row, ensure_ascii=False) + "\n") for row in added]
    if {page for page, line in existing}.intersection(page for page, line in new):
        raise ValueError("New Photius page would duplicate an existing primary page")
    if {page for page, line in existing + new} != set(range(13, 558)):
        raise ValueError("Photius still lacks pages from the checked authorial range")
    output = "".join(line for page, line in sorted(existing + new, key=lambda pair: pair[0])).encode()
    if len(output) >= 100_000_000:
        raise ValueError("The compact Photius corpus exceeds the 100 MB Git object limit")
    network_raw = gzip.compress(encode(networks), mtime=0)
    artifacts[network_path] = network_raw
    comparison_path = ARCHIVE / "source-library-body-windows.json.gz"
    comparison_raw = gzip.compress(encode(comparisons), mtime=0)
    artifacts[comparison_path] = comparison_raw
    comparison_counts = dict(Counter(value["status"] for value in comparisons.values()))
    primary_comparison_counts = dict(Counter(value["status"] for value in comparisons.values()
        if value["role"] == "missing-primary-text"))
    totals = Counter()
    for row in page_reports:
        if row["role"] == "missing-primary-text":
            totals.update(row["counts"])
    report = {"schema_version": 1, "work": SLUG, "date": "2026-10-18",
              "edition_scope": "Complete Bekker authorial printed-page range, including prefatory letter, across the combined scan and retained second-volume source. Combined scans 446/447 repeat pages 334/335; genuine printed pages 434/435 remain in the unchanged legacy witness. No codex-level paragraph mapping is invented.",
              "source_scan": manifest["sources"]["photius-bekker-combined"],
              "legacy_source": LEGACY_SOURCE, "source_scan_exceptions": SOURCE_SCAN_EXCEPTIONS,
              "retained_page_mapping": {"source": "legacy_source", "physical_page_rule": "Historical OCR page key is the 1-based scan page in legacy_source.",
                  "printed_page_offset": 265, "logical_combined_position_offset": 277,
                  "logical_positions_are_physical_citations": False,
                  "exceptions": SOURCE_SCAN_EXCEPTIONS},
              "added_scan_ranges": [[13, 278], [379, 421]],
              "retained_scan_ranges": [[279, 378], [422, 557]], "covered_authorial_scan_pages": 545,
              "coverage_position_meaning": "Ranges use logical combined-edition positions to place the authorial printed pages. Physical citations for retained rows use legacy_source, including the two explicit combined-scan exceptions.",
              "covered_authorial_printed_pages": 545,
              "index_scan_pages": [558, 595], "added_passages": len(added),
              "historical_body_passages": index_audit["body_rows"], "preserved_index_passages": index_audit["index_rows"],
              "original_body_sha256": sha(body), "new_corpus_sha256": sha(output),
              "fresh_ocr_files": [{"path": (ARCHIVE / "witnesses" / (sha(raw) + ".jsonl")).as_posix(),
                                   "sha256": sha(raw), "model": metadata["model"], "revision": metadata["revision"]}
                                  for raw, metadata, rows in inputs],
              "reviewed_retries": retry_reports,
              "fresh_outcome_quality": {"path": quality_path.as_posix(), "sha256": sha(artifacts[quality_path]),
                                        "outcomes": quality["outcome_count"], "flagged_outcomes": quality["flagged_outcomes"],
                                        "selection_rule": None},
              "reviewed_retry": retry_reports[0] if len(retry_reports) == 1 and retry_reports[0]["scan_page"] == 13 else None,
              "full_networks": {"path": network_path.as_posix(), "sha256": sha(network_raw),
                                "entries": len(networks), "key": "physical scan page as a decimal string"},
              "source_library": {"edition": source_document["id"], "url": SOURCE_URL,
                                 "sha256": SOURCE_LIBRARY_SHA256, "license": source_document["license"],
                                 "rights": source_document["sourceRights"],
                                 "role": "Same-scan comparison witness, never used as model input. Only a body window bounded by unique shared beginnings and endings in both independent fresh witnesses may vote; unmatched full pages remain comparison-only.",
                                 "body_comparison_counts": comparison_counts,
                                 "primary_body_comparison_counts": primary_comparison_counts,
                                 "body_comparison_audit": {"path": comparison_path.as_posix(), "sha256": sha(comparison_raw), "entries": len(comparisons)},
                                 "api_notice_url": "https://sourcelibrary.org/api/books/6955801057e3b773024f5030/quote?page=13",
                                 "api_notice_checked_date": "2026-10-18",
                                 "separate_api_notice": {"spdx": "CC-BY-SA-4.0",
                                                         "url": "https://creativecommons.org/licenses/by-sa/4.0/",
                                                         "attribution": "Source Library (https://sourcelibrary.org)",
                                                         "terms": "https://sourcelibrary.org/terms",
                                                         "original_texts": "public-domain", "tdm_reservation": 1,
                                                         "tdm_policy": "https://sourcelibrary.org/licensing",
                                                         "ai_training": "reserved — standard license available, see tdm_policy"}},
              "consensus_counts": dict(totals), "pages": page_reports,
              "policy": "Merge all independently retained readings. Exact word ties stay explicit in text and out of scalar analysis_text. Preserve every supplied raw reading; no arbitrary source preference or silent correction. Existing later-volume passages remain byte-for-byte unchanged.",
              "reversal": "Run scripts/ingest_photius_coverage.py --undo to remove the unchanged addition, then scripts/repair_photius_index.py --undo to recover the original full delivery.",
              "generated_by": "scripts/ingest_photius_coverage.py"}
    artifacts[REPORT] = encode(report)
    artifacts[ARCHIVE / "added-passages.jsonl.gz"] = gzip.compress(prefix, mtime=0)
    artifacts[CORPUS] = output
    return artifacts, report


def apply(artifacts, report, root=ROOT):
    current = (root / CORPUS).read_bytes()
    if sha(current) not in (report["original_body_sha256"], report["new_corpus_sha256"]):
        raise ValueError("Photius body changed outside this audited addition")
    for relative, raw in artifacts.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def undo(root=ROOT):
    report = json.loads((root / REPORT).read_text())
    current = (root / CORPUS).read_bytes()
    prefix = gzip.decompress((root / ARCHIVE / "added-passages.jsonl.gz").read_bytes())
    if sha(current) != report["new_corpus_sha256"]:
        raise ValueError("Photius addition changed after admission")
    added = {json.loads(line)["locus"]: line for line in prefix.decode().splitlines(keepends=True)}
    retained = []
    for line in current.decode().splitlines(keepends=True):
        locus = json.loads(line)["locus"]
        if locus in added:
            if line != added.pop(locus):
                raise ValueError("An admitted Photius passage changed")
        else:
            retained.append(line)
    if added:
        raise ValueError("An admitted Photius passage disappeared")
    body = "".join(retained).encode()
    if sha(body) != report["original_body_sha256"]:
        raise ValueError("Historical body differs from its original bytes")
    (root / CORPUS).write_bytes(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr", type=Path, action="append", default=[])
    parser.add_argument("--source-library", type=Path)
    parser.add_argument("--retry", type=Path, action="append", default=[])
    parser.add_argument("--supplement", type=Path, action="append", default=[])
    parser.add_argument("--retry-review", type=Path, action="append", default=[])
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--undo", action="store_true")
    args = parser.parse_args()
    if args.undo:
        undo()
    else:
        if len(args.ocr) < 2 or args.source_library is None:
            parser.error("Supply at least two --ocr files and the pinned --source-library witness")
        artifacts, report = generate(args.ocr, args.source_library, retry_paths=args.retry, retry_review=args.retry_review,
                                    supplement_paths=args.supplement)
        if args.apply:
            apply(artifacts, report)
        if args.check:
            drift = [str(path) for path, raw in artifacts.items() if not (ROOT / path).exists() or (ROOT / path).read_bytes() != raw]
            if drift:
                parser.exit(1, "Photius coverage drift: " + ", ".join(drift) + "\n")
        print(json.dumps({key: report[key] for key in ("work", "added_passages", "historical_body_passages", "new_corpus_sha256", "consensus_counts")}))
