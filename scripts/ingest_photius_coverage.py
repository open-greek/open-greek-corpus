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

from ocr_consensus import merge_witnesses
from prepare_photius_coverage import build as scan_manifest, build_later_gap
from repair_photius_index import ROOT, SLUG, CORPUS, ARCHIVE as INDEX_ARCHIVE, generate as index_split

ARCHIVE = Path("data/corpus_changes/photius-bekker-coverage")
SOURCE_LIBRARY_SHA256 = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
REPORT = ARCHIVE / "coverage.json"
SOURCE_URL = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg4040/tlg001/local002.json.gz"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def load_prediction(path, manifests):
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
        if row.get("finish_reason") != "stop" or not row.get("raw_prediction", "").strip():
            raise ValueError("Failed, empty, or truncated Photius prediction")
        if len(re.findall(r"[Ͱ-Ͽἀ-῿]+", row["raw_prediction"])) < 20:
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


def generate(paths, source_library, root=ROOT):
    manifest = scan_manifest()
    manifests = [manifest, build_later_gap()]
    all_pages = {page["id"]: page for request in manifests for page in request["pages"]}
    inputs = sorted((load_prediction(path, manifests) for path in paths),
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
    source_raw, source_document, source_rows = load_source_library(source_library)
    original = gzip.decompress((root / INDEX_ARCHIVE / "before.jsonl.gz").read_bytes())
    body, index, aliases, index_audit = index_split(original)
    artifacts, added, page_reports = {}, [], []
    for raw, metadata, rows in inputs:
        artifacts[ARCHIVE / "witnesses" / (sha(raw) + ".jsonl")] = raw
    artifacts[ARCHIVE / "source-library-local002.json.gz"] = source_raw
    artifacts[ARCHIVE / "scan-request.json"] = encode(manifest)
    artifacts[ARCHIVE / "later-gap-request.json"] = encode(manifests[1])
    for page in sorted(all_pages.values(), key=lambda p: p["scan_page"]):
        witnesses = []
        for checkpoint, rows in sorted(models.items()):
            raw, metadata, row = rows[page["id"]]
            identity = metadata["model"] + "@" + metadata["revision"]
            witnesses.append({"id": identity, "text": row["raw_prediction"],
                              "artifact_sha256": row["artifact_sha256"],
                              "vote_group": identity, "model": metadata["model"],
                              "revision": metadata["revision"], "image_sha256": row["image_sha256"],
                              "raw_file_sha256": sha(raw), "license": "CC-BY-4.0"})
        if page["scan_page"] in source_rows:
            witnesses.append(source_rows[page["scan_page"]])
        consensus = merge_witnesses(witnesses)
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
               **consensus}
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
    totals = Counter()
    for row in page_reports:
        if row["role"] == "missing-primary-text":
            totals.update(row["counts"])
    report = {"schema_version": 1, "work": SLUG, "date": "2026-10-18",
              "edition_scope": "Complete Bekker authorial page range, including prefatory letter; physical scan citations are retained without inventing codex-level paragraph mappings.",
              "source_scan": manifest["sources"]["photius-bekker-combined"],
              "added_scan_ranges": [[13, 278], [379, 421]],
              "retained_scan_ranges": [[279, 378], [422, 557]], "covered_authorial_scan_pages": 545,
              "index_scan_pages": [558, 595], "added_passages": len(added),
              "historical_body_passages": index_audit["body_rows"], "preserved_index_passages": index_audit["index_rows"],
              "original_body_sha256": sha(body), "new_corpus_sha256": sha(output),
              "fresh_ocr_files": [{"path": (ARCHIVE / "witnesses" / (sha(raw) + ".jsonl")).as_posix(),
                                   "sha256": sha(raw), "model": metadata["model"], "revision": metadata["revision"]}
                                  for raw, metadata, rows in inputs],
              "source_library": {"edition": source_document["id"], "url": SOURCE_URL,
                                 "sha256": SOURCE_LIBRARY_SHA256, "license": source_document["license"],
                                 "rights": source_document["sourceRights"],
                                 "role": "Same-scan comparison witness; retained in each consensus, never used as model input.",
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
        artifacts, report = generate(args.ocr, args.source_library)
        if args.apply:
            apply(artifacts, report)
        if args.check:
            drift = [str(path) for path, raw in artifacts.items() if not (ROOT / path).exists() or (ROOT / path).read_bytes() != raw]
            if drift:
                parser.exit(1, "Photius coverage drift: " + ", ".join(drift) + "\n")
        print(json.dumps({key: report[key] for key in ("work", "added_passages", "historical_body_passages", "new_corpus_sha256", "consensus_counts")}))
