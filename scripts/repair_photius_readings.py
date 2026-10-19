#!/usr/bin/env python3
"""Apply source-reviewed Photius reading repairs above the frozen admissions.

Every original row, raw vote network, source authority, and input file is
retained. Earlier admissions may verify their exact stage by unapplying this
fully reproduced layer in memory. No reading is selected merely for fluency.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path("data/corpus/photius.bibliotheca.jsonl")
ARCHIVE = Path("data/corpus_changes/photius-bekker-readings")
AUDIT = ARCHIVE / "changes.json"
BEFORE = ARCHIVE / "before-corpus.jsonl.gz"
NETWORKS = ARCHIVE / "networks.json.gz"
RECORDS = ARCHIVE / "records.jsonl.gz"
PARATEXT = Path("data/paratext/photius-bekker-reading-editorial-spans.jsonl")
REVIEW = Path("data/ingest_reviews/photius-bekker-reading-windows.json")
LIBRARY = Path("data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz")
SOURCE_SCAN = ARCHIVE / "source-scan.pdf"
SOURCE_SCAN_SHA = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
BODY_OUTCOMES = "data/ingest_reviews/photius-bekker-body-outcomes.json"
DIAGNOSTIC_FILES = ("data/ocr_requests/photius-bekker-body-recovery-pilot.json",
    "data/evaluation/ocr-fresh/photius-missing-body-pilot-qwen36-mlx.jsonl",
    "data/evaluation/ocr-fresh/photius-missing-body-pilot-qwen38-mlx.jsonl")
BASE_SHA = "d5b9470728b2e7e984b0a0e94b2d3f81dd10b7da22a959ae4f84e0e13a419cd3"
RECORDED_AT = "2026-10-18T21:56:02Z"
BODY_BATCHES = tuple({
    "request": f"data/ocr_requests/photius-bekker-body-recovery{suffix}.json",
    "review": f"data/ingest_reviews/photius-bekker-body-recovery{suffix}.json",
    "outcome_review": BODY_OUTCOMES,
    "raw_files": [f"data/evaluation/ocr-fresh/photius-missing-body{name}-qwen{model}-mlx.jsonl"
                  for model in (36, 38)]}
    for suffix, name in (("", ""), ("-remaining", "-remaining")))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def public_path(value):
    if (not isinstance(value, str) or not value or ":" in value or "\\" in value
            or PurePosixPath(value).is_absolute() or ".." in PurePosixPath(value).parts
            or not value.startswith("data/")):
        raise ValueError("Reading repair inputs require relative public data paths")
    return Path(value)


def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def _notes(old, record, reference, network):
    """Preserve newly excluded editorial spans as independently readable rows."""
    witnesses = {w["id"]: w for w in network["ocr_consensus"]["witnesses"]}
    notes = []
    for mask in record.get("raw_witness_masks", []):
        identifier = mask["witness"]["id"]
        witness = witnesses[identifier]
        for index, span in enumerate(mask["exclusions"], 1):
            start, end = span["start"], span["end"]
            text = witness["text"][start:end]
            if text != span["original_text"]:
                raise ValueError("An editorial note differs from its full raw witness")
            notes.append({"urn": "photius.bibliotheca", "language": "grc",
                "locus": old["locus"] + ".reading-editorial-" + str(len(notes) + 1),
                "class": "edition_editorial_matter", "classification": span["classification"],
                "text": text, "original_locus": old["locus"], "witness_id": identifier,
                "span": {"start": start, "end": end}, "source_review": reference,
                "source_region": span["source_region"], "evidence": span["evidence"],
                "physical_refs": old["physical_refs"], "source": old["source"],
                "edition": old["edition"], "license": witness.get("license", old["license"])})
    return notes


def _plan(before, review_raw, library_raw, network_inputs, body_inputs=(), source_pdf_raw=None):
    """Pure replay from exact original rows, authorities, and compressed sources."""
    from ingest_photius_coverage import SOURCE_LIBRARY_SHA256, SOURCE_URL
    from photius_reading_vote import plan as vote
    from ocr_consensus import restore_corpus_consensus

    if sha(before) != BASE_SHA or sha(library_raw) != SOURCE_LIBRARY_SHA256:
        raise ValueError("Reading repairs must start at the exact released Photius stage")
    document = json.loads(gzip.decompress(library_raw))
    if document["id"] != "tlg4040.tlg001.local002":
        raise ValueError("Reading repair digital edition changed")
    review = json.loads(review_raw)
    if (review.get("schema_version") != 1 or review.get("work") != "photius.bibliotheca"
            or not review.get("reviewed_at") or not review.get("records")):
        raise ValueError("Reading repairs require completed occurrence-level source review")
    rows = [json.loads(line) for line in before.splitlines()]
    by_locus = {r["locus"]: r for r in rows}
    sections = {s["id"]: s for s in document["sections"]}
    reference = {"path": (ARCHIVE / "reading-windows.json").as_posix(), "sha256": sha(review_raw)}
    replacements, full_networks, changes, notes = {}, {}, [], []
    for record in review["records"]:
        locus = record["locus"]
        if locus in replacements or locus not in by_locus:
            raise ValueError("Source review repeats or invents a current passage")
        old = by_locus[locus]
        original_ref = old["ocr_consensus"]["full_network"]
        source_path = public_path(original_ref["path"])
        compressed = network_inputs[source_path.as_posix()]
        section_pin = record.get("source_section")
        witness = None
        if section_pin:
            section = sections[section_pin["id"]]
            text = "\n".join(b["text"] for b in section["blocks"])
            witness = {"id": "source-library-local002", "vote_group": "source-library-local002",
                "text": text, "artifact_sha256": sha(encode(section)),
                "source_file_sha256": sha(library_raw), "source_section": section["id"],
                "source_url": SOURCE_URL, "license": "CC-BY-SA-4.0"}
        updated, full, detail = vote(old, compressed, witness, record,
            source_review=reference, network_reference={"path": NETWORKS.as_posix(), "key": locus})
        raw_boundary = detail.pop("boundary_raw_vote", None)
        if raw_boundary is not None:
            full_networks[locus + ":raw-vote"] = raw_boundary
        restore_corpus_consensus({k: updated[k] for k in ("text", "analysis_text", "ocr_consensus")}, full)
        replacements[locus], full_networks[locus] = updated, full
        # Compact rows retain every raw witness. The planner already verified
        # their exact round trip, so no second whole-archive decode is needed.
        notes.extend(_notes(old, record, reference, old))
        changes.append({"locus": locus, "original_row": old, "corrected_row": updated,
            "original_text": old["text"], "corrected_text": updated["text"],
            "original_row_sha256": row_sha(old), "corrected_row_sha256": row_sha(updated),
            "source_review": reference, "reviewed_at": record.get("reviewed_at", review["reviewed_at"]),
            "source_evidence": record.get("evidence", record.get("source_evidence")), "vote": detail})
    body = None
    additions = []
    if body_inputs:
        from photius_body_vote import plan as body_plan
        body = body_plan(rows, inputs=body_inputs, source_library_raw=library_raw,
                         network_archive=NETWORKS.as_posix(), source_pdf_raw=source_pdf_raw)
        if body["quality_review"]["requires_completed_review"]:
            raise ValueError("Body application requires completed paired/source outcome review")
        if set(replacements) & set(body["replacements"]) or set(full_networks) & set(body["networks"]):
            raise ValueError("Two reading repairs target the same original passage")
        replacements.update(body["replacements"])
        full_networks.update(body["networks"])
        changes.extend(body["changes"])
        additions = body["additions"]
    new_loci, before_rows, after_rows = set(), {}, {}
    for addition in additions:
        row = addition["row"]
        if row["locus"] in by_locus or row["locus"] in new_loci:
            raise ValueError("A recovered body region repeats a passage identity")
        new_loci.add(row["locus"])
        if ("before" in addition) == ("after" in addition):
            raise ValueError("A recovered region needs one reviewed insertion boundary")
        key = "before" if "before" in addition else "after"
        anchor = addition[key]
        if anchor not in by_locus:
            raise ValueError("A recovered body insertion lacks its original anchor")
        (before_rows if key == "before" else after_rows).setdefault(anchor, []).append(row)
    primary_parts = []
    for line in before.splitlines(keepends=True):
        locus = json.loads(line)["locus"]
        primary_parts.append(jsonl(before_rows.get(locus, [])))
        primary_parts.append(jsonl([replacements[locus]]) if locus in replacements else line)
        primary_parts.append(jsonl(after_rows.get(locus, [])))
    primary = b"".join(primary_parts)
    for change in changes:
        change["recorded_at"] = RECORDED_AT
    outputs = {CORPUS: primary, NETWORKS: gzip.compress(encode(full_networks), mtime=0),
               RECORDS: gzip.compress(jsonl(changes), mtime=0), PARATEXT: jsonl(notes)}
    counts = {"primary_rows_before": len(rows), "primary_rows_after": len(rows) + len(additions),
              "reviewed_rows": len(replacements) + len(additions), "editorial_spans": len(notes),
              "source_window_rows": len(review["records"]),
              "digital_voting_rows": sum(bool(r.get("source_section")) for r in review["records"])
                  + (body["counts"]["source_library_witnesses"] if body else 0),
              "before_consensus": {}, "after_consensus": {},
              "window_before_consensus": {}, "window_after_consensus": {}}
    for change in changes:
        for old_or_new, key in (("original_row", "before_consensus"), ("corrected_row", "after_consensus")):
            original = change.get(old_or_new)
            for status, count in (original or {}).get("ocr_consensus", {}).get("counts", {}).items():
                counts[key][status] = counts[key].get(status, 0) + count
                if change.get("kind") != "missing-body-region":
                    window_key = "window_" + key
                    counts[window_key][status] = counts[window_key].get(status, 0) + count
    body_metadata = {key: body[key] for key in
        ("counts", "logical_coverage_positions", "source_library_credit", "input_pins",
         "source_reviews", "quality_review", "source_scan", "ocr_witness_license")} if body else None
    return outputs, counts, reference, body_metadata


@lru_cache(maxsize=2)
def _cached_plan(before, review_raw, library_raw, network_items, body_packets, source_pdf_raw):
    bodies = [{"request": request, "review": review, "raw_files": list(raw_files),
               "outcome_review": outcome} for request, review, raw_files, outcome in body_packets]
    return _plan(before, review_raw, library_raw, dict(network_items), bodies, source_pdf_raw)


def plan(before, review_raw, library_raw, network_inputs, body_inputs=(), source_pdf_raw=None):
    # Every caller still verifies current files and exact frozen pins. Within
    # one process the same immutable inputs need only repeat their word vote
    # once, even when several historical admission checkers request reversal.
    packets = tuple((b["request"], b["review"], tuple(b["raw_files"]), b.get("outcome_review"))
                    for b in body_inputs)
    outputs, counts, reference, body = _cached_plan(before, review_raw, library_raw,
        tuple(sorted(network_inputs.items())), packets, source_pdf_raw)
    return dict(outputs), deepcopy(counts), deepcopy(reference), deepcopy(body)


def _freeze(before, review_raw, library_raw, networks):
    frozen = {BEFORE: gzip.compress(before, mtime=0), ARCHIVE / "reading-windows.json": review_raw,
              ARCHIVE / "source-library.json.gz": library_raw}
    sources = []
    for path, raw in sorted(networks.items()):
        target = ARCHIVE / "network-inputs" / (sha(raw) + ".json.gz")
        frozen[target] = raw
        sources.append({"path": path, "sha256": sha(raw), "frozen_path": target.as_posix()})
    return frozen, sources


def _inputs(root, require_current=True):
    if not (root / AUDIT).exists():
        before = (root / CORPUS).read_bytes()
        review_raw = (root / REVIEW).read_bytes()
        library_raw = (root / LIBRARY).read_bytes()
        by_locus = {r["locus"]: r for r in map(json.loads, before.splitlines())}
        paths = {public_path(by_locus[r["locus"]]["ocr_consensus"]["full_network"]["path"])
                 for r in json.loads(review_raw)["records"]}
        networks = {p.as_posix(): (root / p).read_bytes() for p in paths}
        return before, review_raw, library_raw, networks
    audit = json.loads((root / AUDIT).read_bytes())
    before = gzip.decompress((root / BEFORE).read_bytes())
    review_raw = (root / ARCHIVE / "reading-windows.json").read_bytes()
    library_raw = (root / ARCHIVE / "source-library.json.gz").read_bytes()
    if (sha(before) != audit["input_corpus_sha256"] or sha(review_raw) != audit["source_review"]["sha256"]
            or sha(library_raw) != audit["source_library_sha256"]):
        raise ValueError("Frozen reading repair inputs changed")
    if require_current and ((root / REVIEW).read_bytes() != review_raw or (root / LIBRARY).read_bytes() != library_raw):
        raise ValueError("A published reading source was changed or invalidated")
    networks = {}
    for pin in audit["network_inputs"]:
        path, frozen = public_path(pin["path"]), public_path(pin["frozen_path"])
        if frozen != ARCHIVE / "network-inputs" / (pin["sha256"] + ".json.gz"):
            raise ValueError("Unexpected frozen vote network path")
        raw = (root / frozen).read_bytes()
        if sha(raw) != pin["sha256"] or (require_current and (root / path).read_bytes() != raw):
            raise ValueError("An original or frozen vote network changed")
        networks[path.as_posix()] = raw
    return before, review_raw, library_raw, networks


def _body_inputs(root, require_current=True):
    """Retain exact production requests and raw runs, independently of pilots."""
    saved = json.loads((root / AUDIT).read_bytes()) if (root / AUDIT).exists() else None
    batches = saved.get("body_batches", []) if saved else list(BODY_BATCHES)
    if require_current and batches != list(BODY_BATCHES):
        raise ValueError("Published body recovery input membership changed")
    if saved:
        raw_files = {}
        for pin in saved.get("body_input_files", []):
            path, frozen = public_path(pin["path"]), public_path(pin["frozen_path"])
            target = ARCHIVE / "body-inputs" / (pin["sha256"] + "".join(path.suffixes))
            if frozen != target:
                raise ValueError("Unexpected frozen body input path")
            raw = (root / frozen).read_bytes()
            if sha(raw) != pin["sha256"] or (require_current and (root / path).read_bytes() != raw):
                raise ValueError("A body recovery source changed or was invalidated")
            raw_files[path.as_posix()] = raw
    else:
        paths = {path for b in batches for path in [b["request"], b["review"], b["outcome_review"], *b["raw_files"]]}
        if batches:
            paths.update(DIAGNOSTIC_FILES)
        raw_files = {p: (root / public_path(p)).read_bytes() for p in sorted(paths)}
    if require_current and batches:
        from prepare_photius_body_recovery import build as prepare_body, build_remaining
        canonical = {**prepare_body(root), **build_remaining(root)}
        if raw_files[DIAGNOSTIC_FILES[0]] != canonical[public_path(DIAGNOSTIC_FILES[0])]:
            raise ValueError("Diagnostic pilot request differs from its original reviewed geometry")
        for batch in batches:
            for key in ("request", "review"):
                if raw_files[batch[key]] != canonical[public_path(batch[key])]:
                    raise ValueError("Body source authority does not reproduce from reviewed geometry")
        from prepare_photius_body_outcomes import build as prepare_outcomes
        if raw_files[BODY_OUTCOMES] != encode(prepare_outcomes(root)):
            raise ValueError("Body outcome review does not reproduce from the exact retained predictions")
    inputs = [{"request": raw_files[b["request"]], "review": raw_files[b["review"]],
               "raw_files": [raw_files[p] for p in b["raw_files"]],
               "outcome_review": raw_files[b["outcome_review"]]} for b in batches]
    frozen = {ARCHIVE / "body-inputs" / (sha(raw) + "".join(Path(p).suffixes)): raw
              for p, raw in raw_files.items()}
    pins = [{"path": p, "sha256": sha(raw), "frozen_path":
             (ARCHIVE / "body-inputs" / (sha(raw) + "".join(Path(p).suffixes))).as_posix()}
            for p, raw in sorted(raw_files.items())]
    source_pdf_raw = None
    if batches:
        source_path = SOURCE_SCAN if saved else Path("data/cache/scan-ocr") / (SOURCE_SCAN_SHA + ".pdf")
        source_pdf_raw = (root / source_path).read_bytes()
        if sha(source_pdf_raw) != SOURCE_SCAN_SHA:
            raise ValueError("Frozen body recovery source scan changed")
        frozen[SOURCE_SCAN] = source_pdf_raw
    return inputs, frozen, pins, batches, source_pdf_raw


def build(root=ROOT, *, require_current=True):
    root = Path(root)
    before, review_raw, library_raw, networks = _inputs(root, require_current)
    if require_current:
        from prepare_photius_reading_windows import build as prepare
        if encode(prepare(root)) != review_raw:
            raise ValueError("Reading source authority does not reproduce from pinned evidence")
    body_inputs, body_frozen, body_pins, body_batches, source_pdf = _body_inputs(root, require_current)
    outputs, counts, reference, body = plan(before, review_raw, library_raw, networks, body_inputs, source_pdf)
    frozen, sources = _freeze(before, review_raw, library_raw, networks)
    frozen.update(body_frozen)
    audit = {"schema_version": 1, "work": "photius.bibliotheca",
             "operation": "merge-source-reviewed-photius-readings", "reviewed_at": json.loads(review_raw)["reviewed_at"],
             "recorded_at": RECORDED_AT,
             "input_corpus_sha256": sha(before), "source_review": reference,
             "source_library_sha256": sha(library_raw), "network_inputs": sources, "counts": counts,
             "body_input_files": body_pins, "body_batches": body_batches,
             "diagnostic_only_files": list(DIAGNOSTIC_FILES) if body_batches else [],
             "outputs": {p.as_posix(): sha(raw) for p, raw in outputs.items()},
             "frozen_inputs": {p.as_posix(): sha(raw) for p, raw in frozen.items()},
             "policy": "Source-reviewed bounds and masks only; one vote per source family, original readings and every tied alternative retained."}
    if body:
        audit["body_recovery"] = body
    return {**outputs, **frozen, AUDIT: encode(audit)}, audit


def check(root=ROOT):
    root = Path(root)
    artifacts, audit = build(root)
    if any(not (root / p).exists() or (root / p).read_bytes() != raw for p, raw in artifacts.items()):
        raise ValueError("A reading repair output differs from exact archived replay")
    return audit


@lru_cache(maxsize=2)
def _projection_pins(raw):
    return {r["locus"]: r["corrected_row_sha256"]
            for r in map(json.loads, gzip.decompress(raw).splitlines())}


def validate_projection(row, root=ROOT):
    """Check a counting row against its exact published occurrence audit."""
    root = Path(root)
    audit = json.loads((root / AUDIT).read_bytes())
    raw = (root / RECORDS).read_bytes()
    if (audit.get("work") != "photius.bibliotheca"
            or sha(raw) != audit["outputs"][RECORDS.as_posix()]
            or _projection_pins(raw).get(row.get("locus")) != row_sha(row)):
        raise ValueError("Photius reading or lexical projection differs from its exact occurrence audit")


def restore_before_bytes(raw, root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        return raw
    audit = json.loads((root / AUDIT).read_bytes())
    if sha(raw) == audit["input_corpus_sha256"]:
        return raw
    artifacts, reproduced = build(root)
    if raw != artifacts[CORPUS] or (root / AUDIT).read_bytes() != encode(reproduced):
        raise ValueError("Photius changed outside its exact reviewed reading repair")
    if any((root / p).read_bytes() != value for p, value in artifacts.items() if p != CORPUS):
        raise ValueError("Reading repair notes, networks, or input evidence changed")
    return gzip.decompress(artifacts[BEFORE])


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        return None
    audit = json.loads((root / AUDIT).read_bytes())
    if sha((root / CORPUS).read_bytes()) == audit["input_corpus_sha256"]:
        return None
    audit = check(root)
    return {"audit": {"path": AUDIT.as_posix(), "sha256": sha((root / AUDIT).read_bytes())},
            "source_review": audit["source_review"], "counts": audit["counts"],
            "networks": {"path": NETWORKS.as_posix(), "sha256": audit["outputs"][NETWORKS.as_posix()]},
            "paratext": {"path": PARATEXT.as_posix(), "sha256": audit["outputs"][PARATEXT.as_posix()]},
            **({"body_recovery": audit["body_recovery"]} if audit.get("body_recovery") else {})}


def apply(root=ROOT):
    root = Path(root)
    artifacts, audit = build(root)
    if sha((root / CORPUS).read_bytes()) not in {audit["input_corpus_sha256"], audit["outputs"][CORPUS.as_posix()]}:
        raise ValueError("Unreviewed corpus edits cannot enter a reading repair")
    for path, raw in artifacts.items():
        if path != CORPUS and (root / path).exists() and (root / path).read_bytes() != raw:
            raise ValueError("Refusing to replace a frozen reading repair artifact")
    for path, raw in artifacts.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
    return audit


def undo(root=ROOT):
    root = Path(root)
    artifacts, audit = build(root, require_current=False)
    if any((root / path).read_bytes() != raw for path, raw in artifacts.items()):
        raise ValueError("Unapply later or independent edits before undoing the reading repair")
    (root / CORPUS).write_bytes(gzip.decompress(artifacts[BEFORE]))
    (root / PARATEXT).unlink()
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--undo", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = (apply(args.root) if args.apply else check(args.root) if args.check else
              undo(args.root) if args.undo else build(args.root)[1])
    print(json.dumps(result["counts"]))
