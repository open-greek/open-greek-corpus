#!/usr/bin/env python3
"""Admit a completed Photius source-review campaign with exact reversible audits.

The admission gate requires the entire frozen scope. Direct scan readings remain
distinct from diagnostic digital counterparts. Conflicting forms, uncertain
source spans, printed fragments, and unclassified material cannot enter scalar
lexical counts. No historical witness or earlier correction audit is discarded.
"""
from __future__ import annotations

from audit_compression import compress_gzip

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
ALIASES = Path("data/passage_aliases.json")
BEFORE_ALIASES = ARCHIVE / "before-passage-aliases.json.gz"
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
        if not edges and record["digital_counterparts_usable"]:
            # A completed scan review does not silently turn an unpaired span
            # into agreement with an available independent digital witness.
            exclusions.extend(_mask(t, offset, "unpaired-available-digital-witness")
                              for t in source_tokens)
            continue
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
            # Token-edge observations must break the same disputed adjacency
            # as bounded passage observations. Keep every optimal insertion
            # candidate and both possible neighboring source words.
            for insertion in alignment["digital_insertions"]:
                for token in insertion["review_spans"]:
                    exclusions.append(_mask(token, offset, "digital-insertion-boundary",
                        source_pointer={"kind": "digital", "section": alignment["section"],
                                        **deepcopy(insertion["digital_span"])}))
            continue
        for reading in edges:
            # Full bounded passage readings, rather than isolated token edges.
            digital = tokens(reading["text"])
            if not source_tokens:
                continue
            if not digital:
                exclusions.extend(_mask(t, offset, "unpaired-available-digital-witness",
                    source_pointer=deepcopy(reading)) for t in source_tokens)
                continue
            compared = _local_alignment([_key(t["text"]) for t in source_tokens],
                                         [_key(t["text"]) for t in digital])
            for i, token in enumerate(source_tokens):
                candidates = compared["counterparts"][i]
                if (compared["may_be_unaligned"][i] or not candidates or
                        any(not _exact(token["text"], digital[j]["text"]) or
                            any(fragment['start'] < digital[j]['end'] and digital[j]['start'] < fragment['end']
                                for fragment in reading.get('boundary_fragments', [])) for j in candidates)):
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
    authority = {"path": REVIEW.as_posix(), "sha256": campaign.sha(compress_gzip(review_raw)),
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
        if record.get("duplicate_of"):
            if text or record["duplicate_of"] == old["locus"]:
                raise ValueError("A duplicate citation requires an empty reviewed tombstone")
            new["complete_source_review"]["duplicate_of"] = record["duplicate_of"]
            new["complete_source_review"]["disposition"] = "duplicate-citation-tombstone"
        elif not text:
            if not record["segments"] or any(segment.get("text_role") not in {
                    "editorial-note", "marginal-reference", "unclassified-small-type", "unclassified-heading"}
                    for segment in record["segments"]):
                raise ValueError("An empty reviewed passage requires an explicit duplicate citation or nonbody disposition")
            new["complete_source_review"]["disposition"] = "nonbody-citation-tombstone"
        changes.append({"locus": old["locus"], "original_row": old, "corrected_row": new,
            "original_row_sha256": campaign.row_sha(old), "corrected_row_sha256": campaign.row_sha(new)})
        output.append(campaign.canonical(new) + b"\n")
    if by_locus or len(changes) != review["counts"]["passages"]:
        raise ValueError("Complete-review authority does not partition the exact frozen scope")
    return b"".join(output), changes


def _alias_postimage(aliases_before, changes):
    """Route only explicitly reviewed duplicates; preserve every unrelated alias."""
    aliases = json.loads(aliases_before)
    own = aliases.setdefault("aliases", {}).setdefault("photius.bibliotheca", {})
    by_locus = {change["locus"]: change for change in changes}
    dispositions = []
    for change in changes:
        row = change["corrected_row"]
        target = row["complete_source_review"].get("duplicate_of")
        if not target:
            continue
        destination = by_locus.get(target)
        if (row["text"] or target == row["locus"] or not destination
                or not destination["corrected_row"]["text"]
                or destination["corrected_row"]["complete_source_review"].get("duplicate_of")):
            raise ValueError("A duplicate citation lacks its complete retained canonical passage")
        pointer = {"path": CORPUS.as_posix(), "slug": "photius.bibliotheca", "locus": target}
        if row["locus"] in own and own[row["locus"]] != pointer:
            raise ValueError("A duplicate historical citation already points elsewhere")
        own[row["locus"]] = pointer
        dispositions.append({"locus": row["locus"], "duplicate_of": target,
            "disposition": "duplicate-citation-tombstone", "alias": pointer,
            "original_row_sha256": change["original_row_sha256"],
            "tombstone_row_sha256": change["corrected_row_sha256"],
            "canonical_row_sha256": destination["corrected_row_sha256"]})
    # Exact unchanged alias bytes matter to undo even when no duplicate occurs.
    return (campaign.encode(aliases) if dispositions else aliases_before), dispositions


def artifacts(before, review_raw, aliases_before=None):
    after, changes = plan(before, review_raw)
    if aliases_before is None:
        # Miniature independent authorities can omit an existing alias catalog.
        # The production builder always supplies its exact current preimage.
        aliases_before = campaign.encode({"schema_version": 1, "aliases": {}})
    aliases_after, dispositions = _alias_postimage(aliases_before, changes)
    records = compress_gzip(b"".join(campaign.canonical(r) + b"\n" for r in changes))
    review_archive = compress_gzip(review_raw)
    outputs = {CORPUS: after, RECORDS: records, REVIEW: review_archive,
        ALIASES: aliases_after, BEFORE_ALIASES: compress_gzip(aliases_before)}
    origins = Counter("reviewed-historical-reading-occurrences" if c["original_row"].get("historical_reading_repair")
        else "later-reviewed-historical-occurrences" if c["original_row"].get("historical_reading_batches")
        else "retained-primary" for c in changes)
    audit = {"schema_version": 1, "schema": SCHEMA, "work": "photius.bibliotheca",
        "edition": EDITION, "license": "CC-BY-SA-4.0", "replaced_component_passages": dict(sorted(origins.items())),
        "source_library": deepcopy(json.loads(review_raw)["source_library_credit"]),
        "source_pins": deepcopy(json.loads(review_raw)["input_pins"]),
        "campaign_id": json.loads(review_raw)["campaign_id"],
        "input_corpus_sha256": campaign.sha(before), "output_corpus_sha256": campaign.sha(after),
        "input_aliases_sha256": campaign.sha(aliases_before),
        "output_aliases_sha256": campaign.sha(aliases_after),
        "before_aliases": {"path": BEFORE_ALIASES.as_posix(),
            "sha256": campaign.sha(outputs[BEFORE_ALIASES]),
            "uncompressed_sha256": campaign.sha(aliases_before)},
        "duplicate_dispositions": dispositions,
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
def _saved_artifacts(audit_raw, baseline_raw, review_raw, records_raw, aliases_before_raw):
    """Restore literal frozen rows without re-adjudicating invalidated sources."""
    audit = json.loads(audit_raw)
    before = gzip.decompress(baseline_raw)
    aliases_before = gzip.decompress(aliases_before_raw)
    if (audit.get("schema") != SCHEMA or campaign.sha(before) != audit["input_corpus_sha256"]
            or audit["outputs"][CORPUS.as_posix()] != audit["output_corpus_sha256"]
            or audit["source_review"] != {"path": REVIEW.as_posix(), "sha256": campaign.sha(review_raw)}
            or campaign.sha(review_raw) != audit["outputs"][REVIEW.as_posix()]
            or campaign.sha(records_raw) != audit["outputs"][RECORDS.as_posix()]
            or audit["before_aliases"] != {"path": BEFORE_ALIASES.as_posix(),
                "sha256": campaign.sha(aliases_before_raw),
                "uncompressed_sha256": campaign.sha(aliases_before)}
            or campaign.sha(aliases_before_raw) != audit["outputs"][BEFORE_ALIASES.as_posix()]
            or campaign.sha(aliases_before) != audit["input_aliases_sha256"]):
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
    aliases_after, dispositions = _alias_postimage(aliases_before, list(changes.values()))
    if (campaign.sha(aliases_after) != audit["output_aliases_sha256"]
            or campaign.sha(aliases_after) != audit["outputs"][ALIASES.as_posix()]
            or dispositions != audit["duplicate_dispositions"]):
        raise ValueError("Complete-review duplicate citation aliases changed")
    return {CORPUS: after, AUDIT: audit_raw, REVIEW: review_raw, RECORDS: records_raw,
            ALIASES: aliases_after, BEFORE_ALIASES: aliases_before_raw}, audit, before


def _saved(root):
    root = Path(root)
    return _saved_artifacts(*((root / path).read_bytes()
        for path in (AUDIT, campaign.BASELINE, REVIEW, RECORDS, BEFORE_ALIASES)))


def build(root=ROOT):
    from build_photius_review_observations import build as compile_observations
    root = Path(root)
    outputs, review = compile_observations(root)
    review_raw = campaign.decoded_bytes(campaign.OUT, outputs[campaign.OUT])
    before = gzip.decompress((root / campaign.BASELINE).read_bytes())
    aliases_before = (gzip.decompress((root / BEFORE_ALIASES).read_bytes())
        if (root / AUDIT).exists() else (root / ALIASES).read_bytes())
    return artifacts(before, review_raw, aliases_before)


def _later_bytes(raw, root):
    """Verify and reverse later authorities before checking this frozen stage."""
    if b'"photius_editorial_substitution"' in raw:
        from repair_photius_editorial_substitutions import restore_before_bytes as restore
        raw = restore(raw, root)
    if b'"photius_uncertainty_admission"' in raw:
        from repair_photius_uncertainty_admission import restore_before_bytes as restore
        raw = restore(raw, root)
    if b'"photius_uncertainty_review"' in raw:
        from repair_photius_uncertainties import restore_before_bytes as restore
        raw = restore(raw, root)
    if b'"photius_context_review"' in raw:
        from repair_photius_context import restore_before_bytes as restore
        raw = restore(raw, root)
    return raw


def _later_row(row, root):
    if row.get('photius_editorial_substitution'):
        from repair_photius_editorial_substitutions import restore_before_row as restore
        row = restore(row, root)
    if row.get('photius_uncertainty_admission'):
        from repair_photius_uncertainty_admission import restore_before_row as restore
        row = restore(row, root)
    if row.get('photius_uncertainty_review'):
        from repair_photius_uncertainties import restore_before_row as restore
        row = restore(row, root)
    if row.get('photius_context_review'):
        from repair_photius_context import restore_before_row as restore
        row = restore(row, root)
    return row


def later_metadata(root=ROOT):
    """Publish later checked authorities separately from frozen review counts."""
    root = Path(root)
    result = {}
    if (root / 'data/corpus_changes/photius-bekker-context/changes.json').exists():
        from repair_photius_context import active_metadata as metadata
        current = metadata(root)
        if current:
            result['context_review'] = current
    if (root / 'data/corpus_changes/photius-bekker-uncertainties/changes.json').exists():
        from repair_photius_uncertainties import active_metadata as metadata
        current = metadata(root)
        if current:
            result['uncertainty_review'] = current
    if (root / 'data/corpus_changes/photius-bekker-uncertainty-admission/changes.json').exists():
        from repair_photius_uncertainty_admission import active_metadata as metadata
        current = metadata(root)
        if current:
            result['uncertainty_admission'] = current
    if (root / 'data/corpus_changes/photius-bekker-editorial-substitutions/changes.json').exists():
        from repair_photius_editorial_substitutions import active_metadata as metadata
        current = metadata(root)
        if current:
            result['editorial_substitutions'] = current
    return result


def current_uncertainty_measurement(later):
    """Expose current occurrence accounting beside immutable historical counts."""
    previous = later.get('uncertainty_review')
    latest = later.get('uncertainty_admission')
    editorial = later.get('editorial_substitutions')
    if (latest or editorial) and not previous:
        raise ValueError('The latest uncertainty admission has no active predecessor')
    if not previous:
        return None
    old = previous['counts']
    baseline, current = old['baseline_uncertainty_spans'], old['current_uncertainty_spans']
    authority = previous['source_review']
    if latest:
        new = latest['counts']
        resolved = new['resolved_changed'] + new['resolved_unchanged']
        identities = [(x['locus'], x['segment_index']) for x in new['resolved_identities']]
        if (new['baseline_uncertainty_spans'] != current or new['resolved'] != resolved
                or len(identities) != len(set(identities)) or len(identities) != resolved
                or new['current_uncertainty_spans'] != current - resolved):
            raise ValueError('Current uncertainty counts do not extend their exact predecessor')
        current, authority = new['current_uncertainty_spans'], latest['source_review']
    result = {'baseline_uncertainty_spans': baseline, 'current_uncertainty_spans': current,
            'resolved_uncertainty_spans': baseline-current, 'source_review': authority,
            'qualification': 'Current occurrence count after checked source admissions. Original campaign and earlier admission counts remain frozen historical measurements; other lexical exclusion causes remain independent.'}
    if editorial:
        counts = editorial['counts']
        count = counts['editorially_substituted_spans']
        identities = [(x['locus'], x['segment_index']) for x in counts['substituted_identities']]
        remaining = counts['unsubstituted_source_uncertainty_spans']
        if (type(count) is not int or not 0 <= count <= current
                or counts['scan_uncertainty_spans'] != current
                or remaining != current-count or len(identities) != len(set(identities))
                or len(identities) != count
                or latest and set(identities).intersection(
                    (x['locus'], x['segment_index']) for x in latest['counts']['resolved_identities'])):
            raise ValueError('Editorial substitution counts do not extend their exact scan predecessor')
        result.update(scan_uncertainty_spans=current, scan_resolved_uncertainty_spans=baseline-current,
            editorially_substituted_spans=count, unsubstituted_source_uncertainty_spans=remaining,
            current_uncertainty_spans=remaining, addressed_uncertainty_spans=baseline-remaining,
            scan_source_review=authority, source_review=editorial['source_review'],
            editorial_source_review=editorial['source_review'],
            qualification='Current served unresolved count after scan resolutions and explicit editorial source substitutions. Editorial choices do not verify ambiguous Bekker ink: the separate scan uncertainty count and original source readings remain historical evidence. Independent lexical exclusion causes survive.')
    return result


def check(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        if b'"complete_source_review"' in (root / CORPUS).read_bytes():
            raise ValueError("Complete-review corpus metadata has no frozen admission audit")
        return None
    expected, audit = build(root)
    current = _later_bytes((root / CORPUS).read_bytes(), root)
    inactive = (current == gzip.decompress((root / campaign.BASELINE).read_bytes())
        and (root / ALIASES).read_bytes() == gzip.decompress(expected[BEFORE_ALIASES]))
    if any((current if p == CORPUS else (root / p).read_bytes()) != raw for p, raw in expected.items()
           if not inactive or p not in {CORPUS, ALIASES}):
        raise ValueError("Complete-review corpus admission no longer reproduces")
    return None if inactive else audit


def active_metadata(root=ROOT):
    """Verify a frozen postimage without repeating source adjudication per row."""
    root = Path(root)
    if not (root / AUDIT).exists():
        return None
    expected, audit, before = _saved(root)
    current = _later_bytes((root / CORPUS).read_bytes(), root)
    aliases = (root / ALIASES).read_bytes()
    if current == before and aliases == gzip.decompress(expected[BEFORE_ALIASES]):
        return None
    if current != expected[CORPUS] or aliases != expected[ALIASES]:
        raise ValueError("Complete-review corpus differs from its frozen admission")
    return {"audit": {"path": AUDIT.as_posix(), "sha256": campaign.sha((root / AUDIT).read_bytes())},
        "source_review": audit["source_review"], "campaign_id": audit["campaign_id"],
        "counts": audit["counts"], "license": audit["license"],
        "source_library": audit["source_library"], "source_pins": audit["source_pins"],
        "replaced_component_passages": audit["replaced_component_passages"],
        "duplicate_dispositions": audit["duplicate_dispositions"],
        "qualification": "All retained historical passages have complete direct scan review. Explicit source uncertainties, fragments, and nonbody material remain outside scalar lexical counts; prior witnesses and correction layers remain reversible."}


def restore_before_bytes(raw, root=ROOT):
    raw = _later_bytes(raw, root)
    if b'"complete_source_review"' not in raw:
        return raw
    expected, _, before = _saved(root)
    if raw != expected[CORPUS]:
        raise ValueError("Complete-review corpus differs from its exact postimage")
    return before


def restore_before_alias_bytes(raw, root=ROOT):
    """Expose exact preceding aliases to immutable legacy audit validators."""
    if not (Path(root) / AUDIT).exists():
        return raw
    expected, _, _ = _saved(root)
    before = gzip.decompress(expected[BEFORE_ALIASES])
    if raw not in {before, expected[ALIASES]}:
        raise ValueError("Complete-review passage aliases differ from their exact postimage")
    return before


@lru_cache(maxsize=4)
def _record_map(raw):
    rows = list(map(json.loads, gzip.decompress(raw).splitlines()))
    result = {row["locus"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Complete-review frozen records repeat a locus")
    return result


def restore_before_row(row, root=ROOT):
    row = _later_row(row, root)
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
    if row.get('photius_editorial_substitution'):
        from repair_photius_editorial_substitutions import lexical_segments as latest
        return latest(row, root)
    if row.get('photius_uncertainty_admission'):
        from repair_photius_uncertainty_admission import lexical_segments as latest
        return latest(row, root)
    if row.get('photius_uncertainty_review'):
        from repair_photius_uncertainties import lexical_segments as latest
        return latest(row, root)
    if row.get('photius_context_review'):
        from repair_photius_context import lexical_segments as latest
        return latest(row, root)
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
    aliases = (root / ALIASES).read_bytes()
    before_aliases = gzip.decompress(outputs[BEFORE_ALIASES])
    if (current, aliases) not in {
            (gzip.decompress((root / campaign.BASELINE).read_bytes()), before_aliases),
            (outputs[CORPUS], outputs[ALIASES])}:
        raise ValueError("Complete review requires its exact preceding corpus stage")
    for path, raw in outputs.items():
        if path not in {CORPUS, ALIASES} and (root / path).exists() and (root / path).read_bytes() != raw:
            raise ValueError("An immutable complete-review admission artifact already differs")
    for path, raw in outputs.items():
        if path not in {CORPUS, ALIASES}:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_bytes(raw)
    (root / CORPUS).write_bytes(outputs[CORPUS])
    (root / ALIASES).write_bytes(outputs[ALIASES])
    return audit


def undo(root=ROOT):
    root = Path(root)
    expected, _, before = _saved(root)
    current, aliases = (root / CORPUS).read_bytes(), (root / ALIASES).read_bytes()
    alias_before = gzip.decompress(expected[BEFORE_ALIASES])
    if (current, aliases) not in {(expected[CORPUS], expected[ALIASES]), (before, alias_before)}:
        raise ValueError("Complete-review corpus and aliases are not one exact reversible stage")
    restored = restore_before_bytes((root / CORPUS).read_bytes(), root)
    (root / CORPUS).write_bytes(restored)
    (root / ALIASES).write_bytes(alias_before)


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
