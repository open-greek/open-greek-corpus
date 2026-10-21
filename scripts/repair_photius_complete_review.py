#!/usr/bin/env python3
"""Admit a completed Photius source-review campaign with exact reversible audits.

The admission gate requires the entire frozen scope. Direct scan readings remain
distinct from diagnostic digital counterparts. Conflicting forms, uncertain
source spans, printed fragments, and unclassified material cannot enter scalar
lexical counts. No historical witness or earlier correction audit is discarded.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import json
from pathlib import Path
from collections import Counter
import unicodedata

import prepare_photius_review_campaign as campaign
from assess_photius_historical import _key, _local_alignment, tokens

ROOT = Path(__file__).resolve().parents[1]
CORPUS = campaign.CORPUS
ARCHIVE = campaign.ARCHIVE / "admission"
AUDIT = ARCHIVE / "changes.json"
RECORDS = ARCHIVE / "records.jsonl.gz"
REVIEW = ARCHIVE / "source-review.json.gz"
SCHEMA = "photius-complete-source-review-admission-v1"
EDITION = "bekker1825-complete-source-reviewed"


def _exact(a, b):
    return unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b)


def _projection(text, exclusions):
    """Merge overlapping masks without joining text across a masked word."""
    merged = []
    for item in sorted(exclusions, key=lambda x: (x["start"], x["end"])):
        a, b = item["start"], item["end"]
        if (type(a) is not int or type(b) is not int or not 0 <= a <= b <= len(text)
                or text[a:b] != item["text"]):
            raise ValueError("Complete-review lexical exclusion changed")
        if a == b:
            continue
        if merged and a <= merged[-1]["end"]:
            previous = merged.pop()
            a, b = previous["start"], max(b, previous["end"])
            evidence = previous["evidence"] + [deepcopy(item)]
        else:
            evidence = [deepcopy(item)]
        merged.append({"start": a, "end": b, "text": text[a:b], "evidence": evidence})
    cursor, runs = 0, []
    for span in merged:
        runs.append(text[cursor:span["start"]])
        cursor = span["end"]
    runs.append(text[cursor:])
    return merged, runs


def _mask(token, offset, classification, **evidence):
    return {"start": offset + token["start"], "end": offset + token["end"],
            "text": token["text"], "classification": classification, **evidence}


def _digital_exclusions(record):
    """Preserve all optimal comparison variants without selecting a tied path."""
    exclusions = []
    for segment in record["segments"]:
        text = segment["corrected_text"]
        if not text or segment["verification"] == "uncertain":
            continue
        source_tokens = tokens(text)
        offset = segment["corrected_start"]
        edges = [r for r in segment["readings"] if r["kind"] == "digital"]
        alignment = segment.get("digital_alignment")
        if alignment:
            # Token edge coordinates address the literal observation. A changed
            # transcription convention must not silently rebase those masks.
            if segment["scan"]["observed_text"] != text:
                exclusions.extend(_mask(t, offset, "unmapped-transcription-convention") for t in source_tokens)
                continue
            for token in alignment["tokens"]:
                counterparts = [r for r in edges if r["review_span"] ==
                    {k: token[k] for k in ("start", "end", "text")}]
                if (token["may_be_unaligned"] or not counterparts or
                        any(not _exact(token["text"], r["text"]) for r in counterparts)):
                    exclusions.append(_mask(token, offset, "digital-reading-disagreement",
                        alternatives=[deepcopy(r) for r in counterparts],
                        may_be_unaligned=token["may_be_unaligned"]))
            continue
        for reading in edges:
            # Full bounded passage readings, rather than isolated token edges.
            digital = tokens(reading["text"])
            if not source_tokens or not digital:
                continue
            compared = _local_alignment([_key(t["text"]) for t in source_tokens],
                                         [_key(t["text"]) for t in digital])
            for i, token in enumerate(source_tokens):
                candidates = compared["counterparts"][i]
                if (compared["may_be_unaligned"][i] or not candidates or
                        any(not _exact(token["text"], digital[j]["text"]) for j in candidates)):
                    exclusions.append(_mask(token, offset, "digital-reading-disagreement",
                        alternatives=[deepcopy(digital[j]) for j in candidates],
                        source_pointer=deepcopy(reading)))
            # An inserted digital word supplies no known adjacency across its
            # position. Mask both neighboring source words conservatively.
            for j in compared["digital_only"]:
                for i, candidates in enumerate(compared["counterparts"]):
                    if j - 1 in candidates or j + 1 in candidates:
                        exclusions.append(_mask(source_tokens[i], offset, "digital-insertion-boundary",
                                                source_pointer=deepcopy(reading)))
    return exclusions


def _inherited_exclusions(old, text):
    """Earlier source ties survive a new review unless independently resolved."""
    previous = old.get("historical_reading_batch_projection", {}).get("excluded_spans", [])
    if not previous:
        return []
    before, after = tokens(old["text"]), tokens(text)
    if not after:
        return []
    aligned = _local_alignment([_key(t["text"]) for t in before], [_key(t["text"]) for t in after])
    result = []
    for span in previous:
        indices = [i for i, token in enumerate(before)
                   if token["start"] < span["end"] and span["start"] < token["end"]]
        candidates = {j for i in indices for j in aligned["counterparts"][i]}
        if not candidates:
            # The authority to replace a passage is not authority to erase an
            # unmapped earlier uncertainty. Withhold its complete lexical body.
            candidates = set(range(len(after)))
        result.extend(_mask(after[j], 0, "retained-prior-source-uncertainty",
                            original_exclusion=deepcopy(span)) for j in sorted(candidates))
    return result


def plan(before, review_raw):
    """Pure complete-scope admission; exact original rows remain reversible."""
    review = json.loads(review_raw)
    if (review.get("schema") != campaign.COMPILED_SCHEMA or not review.get("scope_complete")
            or review.get("admission_authorized") is not False
            or review["input_pins"]["corpus"]["sha256"] != campaign.sha(before)
            or review["counts"]["complete_scan_review_rows"] != review["counts"]["passages"]):
        raise ValueError("Admission requires the exact completely source-reviewed campaign")
    authority = {"path": REVIEW.as_posix(), "sha256": campaign.sha(gzip.compress(review_raw, mtime=0)),
                 "campaign_id": review["campaign_id"]}
    by_locus = {r["locus"]: r for r in review["rows"]}
    if len(by_locus) != len(review["rows"]):
        raise ValueError("Complete-review authority repeats a passage")
    output, changes = [], []
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        record = by_locus.pop(old["locus"], None)
        if record is None:
            output.append(line)
            continue
        if (not record["complete_scan_review"] or not record["complete"]
                or campaign.row_sha(old) != record["original_row_sha256"]
                or old.get("complete_source_review")):
            raise ValueError("Complete-review admission differs from an exact original row")
        text = campaign.replay_text(record, old["text"])
        masks = (deepcopy(record["additional_lexical_exclusions"])
                 + deepcopy(record["uncertainty_exclusion_candidates"])
                 + deepcopy(record["nonbody_exclusion_candidates"])
                 + _digital_exclusions(record) + _inherited_exclusions(old, text))
        exclusions, runs = _projection(text, masks)
        new = deepcopy(old)
        new.update(text=text, analysis_text=" ".join(runs), edition=EDITION,
                   license="CC-BY-SA-4.0")
        new.setdefault("language", "grc")
        new["complete_source_review"] = {"schema": SCHEMA, "source_review": authority,
            "record_sha256": campaign.sha(campaign.canonical(record)), "status": record["status"],
            "original_row_sha256": campaign.row_sha(old),
            "excluded_spans": exclusions,
            "qualification": "Complete direct scan review, separate from a recognition-error estimate. Every prior row and audit layer remains frozen. Diagnostic disagreements, source uncertainties, nonbody material, and printed fragments remain outside scalar lexical counts."}
        changes.append({"locus": old["locus"], "original_row": old, "corrected_row": new,
            "original_row_sha256": campaign.row_sha(old), "corrected_row_sha256": campaign.row_sha(new)})
        output.append(campaign.canonical(new) + b"\n")
    if by_locus or len(changes) != review["counts"]["passages"]:
        raise ValueError("Complete-review authority does not partition the exact frozen scope")
    return b"".join(output), changes


def artifacts(before, review_raw):
    after, changes = plan(before, review_raw)
    records = gzip.compress(b"".join(campaign.canonical(r) + b"\n" for r in changes), mtime=0)
    review_archive = gzip.compress(review_raw, mtime=0)
    outputs = {CORPUS: after, RECORDS: records, REVIEW: review_archive}
    origins = Counter("reviewed-historical-reading-occurrences" if c["original_row"].get("historical_reading_repair")
        else "later-reviewed-historical-occurrences" if c["original_row"].get("historical_reading_batches")
        else "retained-primary" for c in changes)
    audit = {"schema_version": 1, "schema": SCHEMA, "work": "photius.bibliotheca",
        "edition": EDITION, "license": "CC-BY-SA-4.0", "replaced_component_passages": dict(sorted(origins.items())),
        "source_library": deepcopy(json.loads(review_raw)["source_library_credit"]),
        "source_pins": deepcopy(json.loads(review_raw)["input_pins"]),
        "campaign_id": json.loads(review_raw)["campaign_id"],
        "input_corpus_sha256": campaign.sha(before), "output_corpus_sha256": campaign.sha(after),
        "before_corpus": {"path": campaign.BASELINE.as_posix(),
                          "uncompressed_sha256": campaign.sha(before)},
        "source_review": {"path": REVIEW.as_posix(), "sha256": campaign.sha(review_archive)},
        "counts": {"fully_source_reviewed_rows": len(changes),
            "changed_display_rows": sum(c["original_row"]["text"] != c["corrected_row"]["text"] for c in changes),
            "rows_with_source_uncertainty": sum(c["corrected_row"]["complete_source_review"]["status"] ==
                                               "reviewed-with-uncertainty" for c in changes)},
        "outputs": {p.as_posix(): campaign.sha(raw) for p, raw in outputs.items()}}
    return {**outputs, AUDIT: campaign.encode(audit)}, audit


@lru_cache(maxsize=2)
def _saved_artifacts(audit_raw, baseline_raw, review_raw, records_raw):
    """Restore literal frozen rows without re-adjudicating invalidated sources."""
    audit = json.loads(audit_raw)
    before = gzip.decompress(baseline_raw)
    if (audit.get("schema") != SCHEMA or campaign.sha(before) != audit["input_corpus_sha256"]
            or audit["outputs"][CORPUS.as_posix()] != audit["output_corpus_sha256"]
            or audit["source_review"] != {"path": REVIEW.as_posix(), "sha256": campaign.sha(review_raw)}
            or campaign.sha(review_raw) != audit["outputs"][REVIEW.as_posix()]
            or campaign.sha(records_raw) != audit["outputs"][RECORDS.as_posix()]):
        raise ValueError("Complete-review frozen artifacts changed")
    changes = _record_map(records_raw)
    output, seen = [], set()
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        change = changes.get(old["locus"])
        if change is None:
            output.append(line)
            continue
        new = change["corrected_row"]
        if (old != change["original_row"] or campaign.row_sha(old) != change["original_row_sha256"]
                or campaign.row_sha(new) != change["corrected_row_sha256"]):
            raise ValueError("Complete-review frozen original or corrected row changed")
        output.append(campaign.canonical(new) + b"\n")
        seen.add(old["locus"])
    after = b"".join(output)
    if seen != set(changes) or campaign.sha(after) != audit["output_corpus_sha256"]:
        raise ValueError("Complete-review literal postimage no longer restores exactly")
    return {CORPUS: after, AUDIT: audit_raw, REVIEW: review_raw, RECORDS: records_raw}, audit, before


def _saved(root):
    root = Path(root)
    return _saved_artifacts(*((root / path).read_bytes()
        for path in (AUDIT, campaign.BASELINE, REVIEW, RECORDS)))


def build(root=ROOT):
    from build_photius_review_observations import build as compile_observations
    root = Path(root)
    outputs, review = compile_observations(root)
    review_raw = campaign.decoded_bytes(campaign.OUT, outputs[campaign.OUT])
    before = gzip.decompress((root / campaign.BASELINE).read_bytes())
    return artifacts(before, review_raw)


def check(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        if b'"complete_source_review"' in (root / CORPUS).read_bytes():
            raise ValueError("Complete-review corpus metadata has no frozen admission audit")
        return None
    expected, audit = build(root)
    if any((root / p).read_bytes() != raw for p, raw in expected.items()):
        raise ValueError("Complete-review corpus admission no longer reproduces")
    return audit


def active_metadata(root=ROOT):
    """Verify a frozen postimage without repeating source adjudication per row."""
    root = Path(root)
    if not (root / AUDIT).exists():
        return None
    expected, audit, _ = _saved(root)
    if (root / CORPUS).read_bytes() != expected[CORPUS]:
        raise ValueError("Complete-review corpus differs from its frozen admission")
    return {"audit": {"path": AUDIT.as_posix(), "sha256": campaign.sha((root / AUDIT).read_bytes())},
        "source_review": audit["source_review"], "campaign_id": audit["campaign_id"],
        "counts": audit["counts"], "license": audit["license"],
        "source_library": audit["source_library"], "source_pins": audit["source_pins"],
        "replaced_component_passages": audit["replaced_component_passages"],
        "qualification": "All retained historical passages have complete direct scan review. Explicit source uncertainties, fragments, and nonbody material remain outside scalar lexical counts; prior witnesses and correction layers remain reversible."}


def restore_before_bytes(raw, root=ROOT):
    if b'"complete_source_review"' not in raw:
        return raw
    expected, _, before = _saved(root)
    if raw != expected[CORPUS]:
        raise ValueError("Complete-review corpus differs from its exact postimage")
    return before


@lru_cache(maxsize=4)
def _record_map(raw):
    rows = list(map(json.loads, gzip.decompress(raw).splitlines()))
    result = {row["locus"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Complete-review frozen records repeat a locus")
    return result


def restore_before_row(row, root=ROOT):
    if not row.get("complete_source_review"):
        return deepcopy(row)
    root = Path(root)
    audit = json.loads((root / AUDIT).read_bytes())
    raw = (root / RECORDS).read_bytes()
    if (audit.get("schema") != SCHEMA or campaign.sha(raw) != audit["outputs"][RECORDS.as_posix()]
            or row["complete_source_review"]["source_review"] != {
                **audit["source_review"], "campaign_id": audit["campaign_id"]}):
        raise ValueError("Complete-review row authority changed")
    change = _record_map(raw).get(row.get("locus"))
    if (not change or row != change["corrected_row"] or campaign.row_sha(row) != change["corrected_row_sha256"]
            or campaign.row_sha(change["original_row"]) != change["original_row_sha256"]):
        raise ValueError("Complete-review row differs from its exact postimage")
    return deepcopy(change["original_row"])


def lexical_segments(row, root=ROOT):
    if not row.get("complete_source_review"):
        raise ValueError("Complete-review lexical projection has no admission authority")
    restore_before_row(row, root)
    exclusions, runs = _projection(row["text"], row["complete_source_review"]["excluded_spans"])
    if row.get("analysis_text") != " ".join(runs):
        raise ValueError("Complete-review lexical projection changed")
    return runs


def apply(root=ROOT):
    root = Path(root)
    outputs, audit = build(root)
    current = (root / CORPUS).read_bytes()
    if campaign.sha(current) not in {audit["input_corpus_sha256"], audit["output_corpus_sha256"]}:
        raise ValueError("Complete review requires its exact preceding corpus stage")
    for path, raw in outputs.items():
        if path != CORPUS and (root / path).exists() and (root / path).read_bytes() != raw:
            raise ValueError("An immutable complete-review admission artifact already differs")
    for path, raw in outputs.items():
        if path != CORPUS:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_bytes(raw)
    (root / CORPUS).write_bytes(outputs[CORPUS])
    return audit


def undo(root=ROOT):
    root = Path(root)
    restored = restore_before_bytes((root / CORPUS).read_bytes(), root)
    (root / CORPUS).write_bytes(restored)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--undo", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.undo:
        undo()
        return
    result = apply() if args.apply else check() if args.check else build()[1]
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
