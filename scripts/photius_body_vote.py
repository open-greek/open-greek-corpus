"""Pure, reversible plans for source-reviewed missing Photius body regions.

No files are read or written. The caller archives exact inputs and owns completed
outcome review, application, and reversal. Ordinary word voting and compact
storage come from ocr_consensus; source boundaries only change eligibility.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import PurePosixPath
import re

from ocr_consensus import (alignment_key, compact_corpus_consensus, merge_witnesses,
                           restore_corpus_consensus, tokenize)
from photius_reading_vote import public_reference

SL = 'source-library-local002'
PDF_SHA = 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'
SL_SHA = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
RUNNER_SHA = '061455bce85cb1b770bbb68a2819b06e4da9e637856a05d402559c861154c5e4'
CHECKPOINTS = {
    'mlx-community/Qwen3.6-27B-8bit': 'c5a593c1475a746e43a543b0a02bd2b357e5745f',
    'mlx-community/Qwen3.8-27B-8bit': '815b83c0df8ffd1d1b5244cf75fd6ef14fca9ef9',
}
RUNTIME = {'mlx': '0.31.2', 'mlx-vlm': '0.6.3', 'transformers': '5.12.1'}
AUTHORITIES = {
    'd6bc981eca155c51d7a4aa74d2f0c28e1adf71b4bebedee3297f4f7749e03d4d':
        ('data/ocr_requests/photius-bekker-body-recovery.json',
         'data/ingest_reviews/photius-bekker-body-recovery.json',
         '30d95520f05f2b8d397ab8ccd05d6e4f4f09ada6f58cd156ebd492c213d2cad4'),
    '388c6ce0fd537126cd4fc818cd60b87af742445272705401165a761dc55e49af':
        ('data/ocr_requests/photius-bekker-body-recovery-remaining.json',
         'data/ingest_reviews/photius-bekker-body-recovery-remaining.json',
         'a345e6ca96c5f20a5d48eee84c94989740c0e5ba4a3a0f3c44d3749e183a2dc0'),
}
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_'
MASKED_148_SHA = 'aefdaffde74688ecbd7bb4eab85d5597b3c03a600827bffce558dc1db0143554'
REMOVED_HEADER = PREFIX + '0189.3'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def _supports(slot, identifier):
    return any(s == identifier or s.startswith(identifier + '#voting-segment-')
               for reading in slot['readings'] for s in reading['support'])


def source_boundary_projection(result, *, leading=False, trailing=False, evidence,
        source_review, reviewed_at, raw_network_reference, model_witness_ids=None,
        boundary_witness_id=SL):
    """Return (corrected full network, exact raw network, eligibility audit).

    Only model-supported slots outside the bounded comparison witness's observed
    support may be source fragments. If models omit a prefix, its first complete
    word is never excluded. Every spelling, tie and display character survives.
    """
    public_reference(source_review)
    if (type(leading) is not bool or type(trailing) is not bool or not evidence
            or not reviewed_at or not boundary_witness_id):
        raise ValueError('Source-boundary eligibility requires explicit flags and reviewed evidence')
    raw = deepcopy(result)
    reference = compact_corpus_consensus(raw, raw_network_reference)['ocr_consensus']['full_network']
    network = raw['ocr_consensus']
    witnesses = network['witnesses']
    ids = set(model_witness_ids) if model_witness_ids is not None else {
        w['id'] for w in witnesses if w['id'] != boundary_witness_id}
    if not ids or not ids <= {w['id'] for w in witnesses} or boundary_witness_id in ids:
        raise ValueError('Source-boundary model identities differ from the vote network')
    bounded = [i for i, slot in enumerate(network['slots']) if _supports(slot, boundary_witness_id)]
    positions = set()
    if bounded:
        for identifier in ids:
            observed = [i for i, slot in enumerate(network['slots']) if _supports(slot, identifier)]
            if observed and leading and min(observed) < min(bounded):
                positions.add(min(observed))
            if observed and trailing and max(observed) > max(bounded):
                positions.add(max(observed))
    positions = sorted(positions)
    updated = deepcopy(raw)
    changes = []
    for position in positions:
        original = deepcopy(updated['ocr_consensus']['slots'][position])
        slot = updated['ocr_consensus']['slots'][position]
        side = 'start' if position < min(bounded) else 'end'
        slot.update(lexical_eligible=False, lexical_exclusion='source-column-' + side + '-fragment')
        if slot.get('selected') and slot['status'] != 'unresolved':
            slot['status'] = 'incomplete-reading'
        changes.append({'position': position, 'source_side': side,
                        'original_slot': original, 'corrected_slot': deepcopy(slot)})
    updated['analysis_text'] = ' '.join(slot['selected'] for slot in updated['ocr_consensus']['slots']
                                      if slot['lexical_eligible'])
    updated['ocr_consensus']['counts'] = dict(Counter(s['status'] for s in updated['ocr_consensus']['slots']))
    audit = {'kind': 'source-boundary-lexical-eligibility', 'reviewed_at': reviewed_at,
        'source_review': deepcopy(source_review), 'evidence': evidence, 'leading': leading,
        'trailing': trailing, 'boundary_witness_id': boundary_witness_id,
        'bounded_support': [min(bounded), max(bounded)] if bounded else None,
        'original_text': raw['text'], 'corrected_text': updated['text'],
        'original_analysis_text': raw['analysis_text'], 'corrected_analysis_text': updated['analysis_text'],
        'changes': changes, 'raw_network': reference,
        'policy': 'Only raw model support outside bounded complete comparison words is excluded. Preserve raw source fragments without joining them or supplying letters.',
        'reversal': 'Restore the exact hash-linked pre-eligibility vote network.'}
    if changes:
        if 'source_boundary_projection' in raw['ocr_consensus']:
            audit['previous_projection'] = deepcopy(raw['ocr_consensus']['source_boundary_projection'])
        updated['ocr_consensus']['source_boundary_projection'] = deepcopy(audit)
    return updated, raw, audit


def unapply_boundary_projection(result, raw):
    """Verify and restore the ordinary merge before its eligibility-only layer."""
    audit = result['ocr_consensus']['source_boundary_projection']
    reference = audit['raw_network']
    compact = compact_corpus_consensus(raw, reference)
    if compact['ocr_consensus']['full_network'] != reference:
        raise ValueError('Original boundary vote network changed')
    restored = deepcopy(result)
    for change in audit['changes']:
        position = change['position']
        if restored['ocr_consensus']['slots'][position] != change['corrected_slot']:
            raise ValueError('Reviewed boundary eligibility projection changed')
        restored['ocr_consensus']['slots'][position] = deepcopy(change['original_slot'])
    if 'previous_projection' in audit:
        restored['ocr_consensus']['source_boundary_projection'] = deepcopy(audit['previous_projection'])
    else:
        del restored['ocr_consensus']['source_boundary_projection']
    restored['analysis_text'] = audit['original_analysis_text']
    restored['ocr_consensus']['counts'] = deepcopy(raw['ocr_consensus']['counts'])
    if restored != raw:
        raise ValueError('Boundary review changes more than its exact eligibility projection')
    return deepcopy(raw)


@lru_cache(maxsize=4)
def _rendered_hashes(pdf_raw, pages_raw):
    """Match run_scan_ocr.prepare_images in memory; cache immutable crop bytes."""
    import pymupdf
    pages = json.loads(pages_raw)
    result = {}
    with pymupdf.open(stream=pdf_raw, filetype='pdf') as document:
        for page in pages:
            sheet = document[page['scan_page'] - 1]
            region, rect = page['region'], sheet.rect
            clip = pymupdf.Rect(region[0] * rect.width, region[1] * rect.height,
                                region[2] * rect.width, region[3] * rect.height)
            scale = page['max_side'] / max(clip.width, clip.height)
            pix = sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
            result[page['id']] = sha(pix.tobytes('png'))
    return result


def _load_raw(raw, request_raw, request, image_hashes):
    from ingest_scan_coverage import load_predictions
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    values, _ = load_predictions(None, request_raw, request, raw)
    metadata = records[0]['_meta']
    if (CHECKPOINTS.get(metadata.get('model')) != metadata.get('revision')
            or metadata.get('runner_sha256') != RUNNER_SHA
            or metadata.get('backend') != 'mlx' or metadata.get('temperature') != 0
            or metadata.get('max_tokens') != 2000 or metadata.get('runtime') != RUNTIME
            or metadata.get('manifest_archive') != 'manifests/' + sha(request_raw) + '.json'
            or metadata.get('prompt_policy') != 'base prompt plus page prompt_suffix, falling back to the source prompt_suffix'):
        raise ValueError('Missing-body OCR model, runtime, decoding or runner provenance changed')
    if set(values) != {p['id'] for p in request['pages']}:
        raise ValueError('Missing-body OCR requires every requested strip exactly once')
    raw_rows = {row['id']: row for row in records[1:]}
    for identifier, row in raw_rows.items():
        count = row.get('generation_tokens')
        if (row.get('image_sha256') != image_hashes[identifier]
                or type(count) is not int or not 0 < count < metadata['max_tokens']):
            raise ValueError('Missing-body image or successful generation token pin changed')
    return metadata, values, raw_rows


def _first_anchor_start(text, phrase):
    """Locate an exact accent-insensitive two-word source boundary once."""
    import unicodedata
    words, start = [], None
    for position, char in enumerate(text + ' '):
        if unicodedata.category(char).startswith(('L', 'M')) or char in "'’ʼ᾽":
            if start is None:
                start = position
        elif start is not None:
            words.append((alignment_key(text[start:position]), start, position))
            start = None
    keys = [alignment_key(key) for key, _ in tokenize(phrase)]
    locations = [i for i in range(len(words) - len(keys) + 1)
                 if [w[0] for w in words[i:i + len(keys)]] == keys]
    if len(locations) != 1 or not 0 < locations[0] < 40:
        raise ValueError('Contextual overlap needs one exact reviewed source boundary in the initial body lines')
    return words[locations[0]][1]


def _assemble(metadata, values, raw_rows, pages, reference, request_sha, raw_sha, record, outcomes=None, outcome_reference=None):
    parts, pieces, offset = [], [], 0
    for page in sorted(pages, key=lambda p: p['reading_order']):
        value, raw = values[page['id']], raw_rows[page['id']]
        text = value['text']
        if pieces:
            offset += 1
        pieces.append(text)
        parts.append({'id': page['id'], 'start': offset, 'end': offset + len(text),
            'original_text': text, 'request': deepcopy(page), 'raw_prediction_record': deepcopy(raw),
            'artifact_sha256': value['artifact_sha256'], 'image_sha256': value['image_sha256']})
        offset += len(text)
    text = '\n'.join(pieces)
    identifier = metadata['model'] + '@' + metadata['revision']
    witness = {'id': identifier, 'model': metadata['model'], 'revision': metadata['revision'],
        'vote_group': identifier, 'text': text, 'text_sha256': sha(text.encode()), 'license': 'CC-BY-4.0',
        'artifact_sha256': sha(encode({'metadata': metadata, 'request_sha256': request_sha,
                                    'parts': [p['artifact_sha256'] for p in parts]})),
        'raw_file_sha256': raw_sha, 'raw_metadata': deepcopy(metadata), 'raw_strips': parts,
        'assembly': {'joiner': '\n', 'policy': 'Exact raw strip texts in physical source order; one checkpoint vote.'}}
    context = record.get('context_overlap')
    if context:
        start = _first_anchor_start(text, context['missing_start_anchor'])
        witness['voting_segments'] = [{'start': start, 'end': len(text), 'text': text[start:]}]
        witness['abstention_audit'] = {'reviewed_text_sha256': sha(text.encode()),
            'source_review': deepcopy(reference), 'excluded_spans': [{'start': 0, 'end': start,
                'text': text[:start], 'reason': 'Source-reviewed complete-line context already represented in ' + context['existing_locus']}]}
    spans, fragments, reviews = [], [], []
    for part in parts:
        outcome = (outcomes or {}).get((metadata['model'], metadata['revision'], part['id']))
        if outcome:
            reviews.append(deepcopy(outcome))
            for field, target in (('exclusions', spans), ('source_fragments', fragments)):
                for span in outcome.get(field, []):
                    target.append({**deepcopy(span), 'start': part['start'] + span['start'],
                        'end': part['start'] + span['end'], 'raw_source_pin': {
                            key: deepcopy(outcome[key]) for key in ('id', 'model', 'revision',
                                'raw_file_sha256', 'prediction_record_sha256', 'text_sha256', 'image_sha256')},
                        'raw_source_span': {key: deepcopy(span[key]) for key in ('start', 'end', 'original_text')}})
    if reviews:
        witness['completed_outcome_reviews'] = reviews
    if fragments:
        witness['source_confirmed_fragments'] = fragments
    if spans:
        witness = apply_outcome_abstentions(witness, spans, source_review=outcome_reference)
    return witness


def _digital(document, record, reference, credit):
    window = record['source_library_window']
    sections = {s['id']: s for s in document['sections']}
    section = sections[window['section']]
    text = '\n'.join(b['text'] for b in section['blocks'])
    start, end = window['start'], window['end']
    if (window['sha256'] != SL_SHA or sha(encode(section)) != window['section_sha256']
            or not 0 <= start < end <= len(text) or text[start:end] != window['original_text']):
        raise ValueError('Bounded digital witness differs from its exact source window')
    for held in window['held_spans']:
        other = sections[held.get('section', window['section'])]
        original = '\n'.join(b['text'] for b in other['blocks'])
        lo, hi = held['start'], held['end']
        if (held.get('section_sha256', sha(encode(other))) != sha(encode(other))
                or original[lo:hi] != held['original_text'] or not held['reason']
                or (other['id'] == section['id'] and max(lo, start) < min(hi, end))):
            raise ValueError('Held digital whole-word completion or contextual overlap changed')
    excluded = [{'start': lo, 'end': hi, 'text': text[lo:hi],
        'reason': 'Outside the source-reviewed missing-body window; unobserved text abstains.'}
        for lo, hi in ((0, start), (end, len(text))) if lo < hi]
    # Only the observed window participates in alignment. Unobserved full-page
    # context remains exact evidence rather than an alignment scaffold.
    return {'id': SL, 'vote_group': SL, 'text': text[start:end], 'artifact_sha256': sha(encode(section)),
        'source_file_sha256': SL_SHA, 'source_section': section['id'],
        'source_url': credit['url'], 'license': 'CC-BY-SA-4.0', 'credit': deepcopy(credit),
        'full_source_text': text, 'source_window': {'start': start, 'end': end},
        'source_boundary_held': deepcopy(window['held_spans']),
        'source_excluded_spans': excluded, 'source_review': deepcopy(reference)}


def _anchors(before, record):
    retained = []
    for anchor in record['legacy_anchors']:
        original, locus = anchor['original_row'], anchor['locus']
        if original['locus'] != locus or sha(encode(original)) != anchor['row_sha256']:
            raise ValueError('Missing-body historical source anchor changed')
        current = before.get(locus)
        if locus == REMOVED_HEADER and current is None:
            retained.append({'original_row': deepcopy(original), 'current_row': None,
                             'disposition': 'Previously removed running header; not a body omission.'})
            continue
        allowed = {anchor['row_sha256']}
        if locus == PREFIX + '0148.4':
            allowed = {MASKED_148_SHA}
        if current is None or sha(encode(current)) not in allowed:
            raise ValueError('Current Photius body boundary differs from the frozen original or authorized editorial projection')
        retained.append({'original_row': deepcopy(original), 'current_row': deepcopy(current),
                         'current_row_sha256': sha(encode(current))})
    return retained


def plan(before_rows, inputs, source_library_raw, *, source_pdf_raw, network_archive):
    """Plan one or both immutable requests, without file access or corpus writes.

    inputs=[{request:bytes, review:bytes, raw_files:[bytes,bytes]}]. Additions are
    {row,before?/after?}; replacements map the retained locus to its new row.
    networks includes each served locus and its ':raw-vote' pre-boundary key;
    ':ordinary-vote' retains any merge changed by source observations.
    All output remains pending a separate completed paired/source outcome review.
    """
    # Validate the archive path before retaining any large source/render caches.
    public_reference({'path': network_archive, 'sha256': '0' * 64})
    if sha(source_pdf_raw) != PDF_SHA or sha(source_library_raw) != SL_SHA:
        raise ValueError('Missing-body source PDF or digital archive changed')
    document = json.loads(gzip.decompress(source_library_raw))
    if document.get('id') != 'tlg4040.tlg001.local002':
        raise ValueError('Missing-body digital edition identity changed')
    original = list(before_rows.values()) if isinstance(before_rows, dict) else list(before_rows)
    before = {r['locus']: r for r in original}
    if len(before) != len(original) or not inputs:
        raise ValueError('Missing-body input rows repeat identities or no complete request was supplied')
    additions, replacements, networks, changes, input_pins, review_refs, outcomes = [], {}, {}, [], [], [], []
    seen_requests, seen_regions, checkpoint_scope = set(), set(), None
    credit = None
    for item in inputs:
        request_raw, review_raw = item['request'], item['review']
        request_sha = sha(request_raw)
        if request_sha in seen_requests or request_sha not in AUTHORITIES:
            raise ValueError('Missing-body request is repeated, diagnostic-only or not an approved frozen authority')
        seen_requests.add(request_sha)
        request_path, review_path, review_sha = AUTHORITIES[request_sha]
        if sha(review_raw) != review_sha:
            raise ValueError('Missing-body source review changed')
        request, review = json.loads(request_raw), json.loads(review_raw)
        reference = {'path': review_path, 'sha256': review_sha}
        if request['source_review'] != reference or request['work'] != 'photius.bibliotheca':
            raise ValueError('Missing-body request is detached from its source review')
        if review['source_scan']['sha256'] != PDF_SHA or any(s['sha256'] != PDF_SHA for s in request['sources'].values()):
            raise ValueError('Missing-body source scan differs from its reviewed request')
        if credit is not None and credit != review['source_library_credit']:
            raise ValueError('Missing-body requests disagree on source rights or attribution')
        credit = deepcopy(review['source_library_credit'])
        if credit['sha256'] != SL_SHA or credit['license']['url'] != 'https://creativecommons.org/licenses/by-sa/4.0/':
            raise ValueError('Missing-body digital credit or license changed')
        image_hashes = _rendered_hashes(source_pdf_raw, encode(request['pages']))
        loaded, raw_pins, checkpoints = [], [], set()
        if len(item['raw_files']) != 2:
            raise ValueError('Each missing-body request needs exactly two independent checkpoint files')
        for raw in item['raw_files']:
            metadata, values, raw_rows = _load_raw(raw, request_raw, request, image_hashes)
            checkpoint = (metadata['model'], metadata['revision'])
            if checkpoint in checkpoints:
                raise ValueError('A missing-body checkpoint cannot vote twice')
            checkpoints.add(checkpoint)
            loaded.append((metadata, values, raw_rows, sha(raw)))
            raw_pins.append({'sha256': sha(raw), 'metadata': deepcopy(metadata), 'records': len(values)})
        if checkpoints != set(CHECKPOINTS.items()) or (checkpoint_scope is not None and checkpoints != checkpoint_scope):
            raise ValueError('Missing-body requests must retain the same two independent frozen checkpoints')
        checkpoint_scope = checkpoints
        outcomes_by_id, outcome_reference = _outcomes(item.get('outcome_review'), request, loaded)
        pin = {'request': {'path': request_path, 'sha256': request_sha}, 'source_review': reference,
               'raw_files': sorted(raw_pins, key=lambda v: v['metadata']['model'])}
        if outcome_reference:
            pin['outcome_review'] = outcome_reference
        input_pins.append(pin)
        for ref in (reference, outcome_reference):
            if ref is not None and ref not in review_refs:
                review_refs.append(ref)
        for record in review['regions']:
            if record['id'] in seen_regions:
                raise ValueError('A missing-body source region is requested twice')
            seen_regions.add(record['id'])
            page, column = record['scan_page'], record['column']
            pages = [p for p in request['pages'] if p['reconstructs'] == record['id']]
            if (not pages or [p['region'] for p in sorted(pages, key=lambda p: p['reading_order'])] != record['strip_regions']
                    or sorted(p['reading_order'] for p in pages) != list(range(1, len(pages) + 1))):
                raise ValueError('Missing-body source strips do not reproduce the complete reviewed region')
            historical = _anchors(before, record)
            witnesses = [_assemble(meta, values, rows, pages, reference, request_sha, raw_sha, record, outcomes_by_id, outcome_reference)
                         for meta, values, rows, raw_sha in sorted(loaded, key=lambda v: v[0]['model'])]
            witnesses.append(_digital(document, record, reference, credit))
            action = record.get('legacy_action')
            if action is None:
                action = {'kind': 'insert-before' if page == 66 else 'insert-after',
                          'locus': PREFIX + ('0066.1' if page == 66 else '0073.1')}
            replacement = action['kind'] == 'replace-incomplete-row'
            locus = action['locus'] if replacement else f'photius_bekker1825_recovery_{page:04d}.{column}'
            if locus in networks or (not replacement and locus in before):
                raise ValueError('Missing-body addition/replacement identity already exists')
            ordinary_vote = merge_witnesses(witnesses)
            raw_network = _qualify_reviewed_single_readings(ordinary_vote, witnesses, outcome_reference,
                raw_network_reference={'path': network_archive, 'key': locus + ':ordinary-vote'})
            if raw_network != ordinary_vote:
                networks[locus + ':ordinary-vote'] = ordinary_vote
            result, raw_network, boundary = source_boundary_projection(raw_network,
                leading=bool(record.get('leading_source_fragment')), trailing=bool(record.get('trailing_source_fragment')),
                evidence=record['start_evidence'] + ' ' + record['end_evidence'], source_review=reference,
                reviewed_at=review['reviewed_at'], raw_network_reference={'path': network_archive, 'key': locus + ':raw-vote'},
                model_witness_ids=[w['id'] for w in witnesses[:-1]])
            networks[locus + ':raw-vote'] = raw_network
            networks[locus] = result
            compact = compact_corpus_consensus(result, {'path': network_archive, 'key': locus})
            restore_corpus_consensus(compact, result)
            old = before.get(locus) if replacement else None
            physical = {**review['source_scan'], 'scan_page': page, 'printed_page': record['printed_page'],
                        'region': deepcopy(record['region']), 'column': column}
            repair = {'kind': 'missing-body-region', 'reviewed_at': review['reviewed_at'],
                'source_review': reference, 'logical_coverage_position': page + 277,
                'original_region_record_sha256': sha(encode(record)), 'request': deepcopy(pin['request']),
                'raw_inputs': deepcopy(pin['raw_files']), 'legacy_action': deepcopy(action),
                'retained_historical_readings': historical, 'boundary_eligibility': boundary,
                'quality_review': {'requires_completed_review': outcome_reference is None, 'completed_outcome_review': deepcopy(outcome_reference), 'protocol_complete': True,
                    'source_completeness_claim': False, 'policy': 'Stop termination verifies protocol only; a separate completed paired/source review must authorize application.'}}
            if old is not None:
                repair['previous_row'] = deepcopy(old)
                repair['previous_editorial_layer'] = deepcopy(old.get('editorial_layer'))
                repair['held_historical_policy'] = 'The old incomplete source artifact is retained as a historical variant, not an additional reading or omission vote. Earlier apparatus exclusions remain archived.'
            row = {'urn': 'photius.bibliotheca', 'cts': 'urn:cts:greekLit:tlg4040.tlg001',
                'locus': locus, 'language': 'grc', 'source': 'ocr',
                'edition': 'bekker1825-reviewed-body-consensus', 'license': 'CC-BY-SA-4.0',
                'physical_refs': physical, 'reading_repair': repair, 'body_review_refs': [ref for ref in (reference, outcome_reference) if ref is not None],
                'component_credits': [{'source': 'Independent retained Qwen OCR witnesses', 'license': 'CC-BY-4.0'},
                                      {'source': 'Bekker1825 source scan', 'license': 'PD', 'url': physical['url'], 'sha256': PDF_SHA},
                                      {'source': SL, 'license': 'CC-BY-SA-4.0', 'credit': deepcopy(credit)}], **compact}
            if replacement:
                replacements[locus] = row
            else:
                direction = 'before' if action['kind'] == 'insert-before' else 'after'
                additions.append({'row': row, direction: action['locus']})
            change = {'kind': 'missing-body-region', 'locus': locus, 'source_review': reference,
                'reviewed_at': review['reviewed_at'], 'original_row': deepcopy(old), 'corrected_row': deepcopy(row),
                'original_text': old['text'] if old else '', 'corrected_text': row['text'],
                'original_row_sha256': sha(encode(old)) if old else None, 'corrected_row_sha256': sha(encode(row)),
                'legacy_action': deepcopy(action), 'physical_refs': physical, 'boundary_eligibility': boundary,
                'source_evidence': {'start': record['start_evidence'], 'end': record['end_evidence'], 'evidence': record['evidence']},
                'reversal': 'Remove the added row or restore original_row exactly; preserve every frozen historical mask, raw strip and vote network.'}
            changes.append(change)
            for witness in witnesses[:-1]:
                for part in witness['raw_strips']:
                    outcomes.append({'locus': locus, 'model': witness['model'], 'revision': witness['revision'],
                        'id': part['id'], 'artifact_sha256': part['artifact_sha256'],
                        'image_sha256': part['image_sha256'], 'finish_reason': part['raw_prediction_record']['finish_reason'],
                        'requires_completed_paired_source_review': outcome_reference is None})
    primary = [a['row'] for a in additions] + list(replacements.values())
    return {'additions': additions, 'replacements': replacements, 'networks': networks, 'changes': changes,
        'logical_coverage_positions': {r['locus']: r['reading_repair']['logical_coverage_position'] for r in primary},
        'source_library_credit': credit, 'body_review_refs': review_refs, 'source_reviews': review_refs,
        'source_scan': deepcopy(review['source_scan']), 'ocr_witness_license': 'CC-BY-4.0',
        'input_pins': {'before_rows_sha256': sha(encode(original)), 'source_pdf_sha256': PDF_SHA,
                       'source_library_sha256': SL_SHA, 'requests': input_pins},
        'quality_review': {'requires_completed_review': any('outcome_review' not in pin for pin in input_pins),
                          'completed_outcome_reviews': [ref for ref in review_refs if ref['path'].endswith('body-outcomes.json')], 'component_outcomes': outcomes,
                          'policy': 'A reproducible consensus plan is not a claim that every source word is correct.'},
        'counts': {'added_rows': len(additions), 'replaced_rows': len(replacements),
            'regions': len(primary), 'model_witnesses': len(primary) * 2,
            'source_library_witnesses': len(primary), 'raw_strips': len(outcomes),
            'unresolved_slots': sum(r['ocr_consensus']['counts'].get('unresolved', 0) for r in primary),
            'source_fragment_slots': sum(len(c['boundary_eligibility']['changes']) for c in changes),
            'source_observation_slots': sum(bool(s.get('source_observations')) for r in primary for s in networks[r['locus']]['ocr_consensus']['slots']),
            'internal_source_fragment_slots': sum(bool(s.get('source_fragment_observations')) for r in primary for s in networks[r['locus']]['ocr_consensus']['slots'])}}


def apply_outcome_abstentions(witness, reviewed_spans, *, source_review):
    """Mask exact source-confirmed wrong words, keeping full raw text/partitions."""
    from ocr_consensus import _reviewed_voting_parts
    from photius_reading_vote import _project
    public_reference(source_review)
    _reviewed_voting_parts(witness)
    text, previous_start, exclusions, checked = witness['text'], 0, [], []
    for span in reviewed_spans:
        start, end = span.get('start'), span.get('end')
        if (type(start) is not int or type(end) is not int or not previous_start <= start < end <= len(text)
                or text[start:end] != span.get('original_text')
                or span.get('classification') not in ('source-confirmed-wrong-reading', 'marginal-reference', 'neighboring-column-intrusion', 'incomplete-source-coverage')
                or (span.get('classification') in ('marginal-reference', 'neighboring-column-intrusion', 'incomplete-source-coverage')
                    and span.get('digital_counterpart') is not None)
                or not span.get('observed_printed_text') or not span.get('evidence')
                or not re.fullmatch('[0-9a-f]{64}', span.get('source_image_sha256', ''))):
            raise ValueError('Outcome abstention requires exact ordered wrong-reading spans and source evidence')
        if span['classification'] == 'incomplete-source-coverage':
            pin = span.get('raw_source_pin')
            if pin is None:
                complete = start == 0 and end == len(text)
            else:
                parts = [p for p in witness.get('raw_strips', []) if p['id'] == pin.get('id')]
                local = span.get('raw_source_span', {})
                complete = (len(parts) == 1 and local.get('start') == 0
                    and local.get('end') == len(parts[0]['raw_prediction_record']['raw_prediction'])
                    and start == parts[0]['start'] and end == parts[0]['end'])
            if not complete:
                raise ValueError('An incomplete-coverage abstention must hold one exact complete raw strip')
        for old in checked:
            if max(start, old['start']) >= min(end, old['end']):
                continue
            container = span if span['classification'] == 'incomplete-source-coverage' else old
            contained = old if container is span else span
            if (container['classification'] != 'incomplete-source-coverage'
                    or contained['classification'] == 'incomplete-source-coverage'
                    or not container['start'] <= contained['start'] < contained['end'] <= container['end']):
                raise ValueError('Outcome spans may overlap only inside a complete-strip coverage abstention')
        previous_start = start
        checked.append(span)
        label = {'marginal-reference': 'Source-confirmed marginal reference: ',
                 'neighboring-column-intrusion': 'Source-confirmed neighboring-column intrusion: ',
                 'incomplete-source-coverage': 'Source-confirmed incomplete source coverage: ',
                 'source-confirmed-wrong-reading': 'Source-confirmed wrong reading: '}[span['classification']]
        exclusions.append({'start': start, 'end': end, 'text': text[start:end],
            'reason': label + span['evidence']})
    prior = deepcopy(witness.get('abstention_audit'))
    updated = _project(witness, [*(prior or {}).get('excluded_spans', []), *exclusions], source_review, prior)
    if 'outcome_partitions' in witness:
        raise ValueError('A completed source outcome projection cannot be applied twice')
    updated['source_confirmed_wrong_readings'] = deepcopy(reviewed_spans)
    updated['outcome_partitions'] = {'before_witness_sha256': sha(encode(witness)), 'before': {'voting_segments': deepcopy(witness.get('voting_segments')),
                                               'abstention_audit': deepcopy(witness.get('abstention_audit'))},
                                    'after': {'voting_segments': deepcopy(updated['voting_segments']),
                                              'abstention_audit': deepcopy(updated['abstention_audit'])}}
    return updated


def _outcomes(raw, request, loaded):
    if raw is None:
        return {}, None
    authority = json.loads(raw)
    reference = {'path': 'data/ingest_reviews/photius-bekker-body-outcomes.json', 'sha256': sha(raw)}
    if (authority.get('schema_version') != 1 or authority.get('work') != 'photius.bibliotheca'
            or not authority.get('reviewed_at') or not authority.get('policy')
            or not isinstance(authority.get('records'), list)):
        raise ValueError('Body outcome review requires a complete structured source authority')
    current = {p['id'] for p in request['pages']}
    by_id = {}
    for record in authority['records']:
        key = (record.get('model'), record.get('revision'), record.get('id'))
        if record.get('id') not in current:
            continue
        if key in by_id:
            raise ValueError('Body outcome authority repeats a model/strip identity')
        matches = [(meta, rows, digest) for meta, _, rows, digest in loaded
                   if (meta['model'], meta['revision']) == key[:2]]
        if len(matches) != 1:
            raise ValueError('Body outcome authority changed its frozen checkpoint')
        metadata, rows, digest = matches[0]
        original = rows[key[2]]
        if (record.get('raw_file_sha256') != digest
                or record.get('prediction_record_sha256') != sha(encode(original))
                or record.get('text_sha256') != sha(original['raw_prediction'].encode())
                or record.get('image_sha256') != original['image_sha256']
                or record.get('decision') != 'eligible-as-raw-witness' or not record.get('evidence')
                or not isinstance(record.get('exclusions'), list)):
            raise ValueError('Body outcome review differs from its exact raw file, record, text, image or completed decision')
        for span in record['exclusions']:
            if span.get('source_image_sha256') != original['image_sha256']:
                raise ValueError('Body wrong-word evidence refers to a different source crop')
        fragments = record.get('source_fragments', [])
        if not isinstance(fragments, list):
            raise ValueError('Body fragment evidence must be an explicit list')
        previous = 0
        for span in fragments:
            _validate_fragment_span(original['raw_prediction'], span, original['image_sha256'])
            if span['start'] < previous:
                raise ValueError('Body fragment evidence must be ordered and nonoverlapping')
            previous = span['end']
        # Span validation also runs after codepoint offsets enter the assembly.
        if record['exclusions']:
            apply_outcome_abstentions({'id': 'validation', 'text': original['raw_prediction']},
                                      record['exclusions'], source_review=reference)
        by_id[key] = deepcopy(record)
    expected = {(meta['model'], meta['revision'], identifier)
                for meta, _, _, _ in loaded for identifier in current}
    if set(by_id) != expected:
        raise ValueError('Body outcome review must cover both checkpoints of every requested strip')
    return by_id, reference


def _validate_fragment_span(text, span, image_sha256):
    """Validate an exact raw suffix/prefix without inventing its missing letters."""
    start, end = span.get('start'), span.get('end')
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
            or text[start:end] != span.get('original_text')
            or span.get('classification') != 'source-split-word-fragment'
            or not span.get('observed_printed_text') or not span.get('evidence')
            or span.get('source_image_sha256') != image_sha256
            or len(tokenize(text[start:end])) != 1):
        raise ValueError('A source fragment needs one exact raw token and its reviewed source image')


def _render_slots(slots):
    """Reproduce the existing consensus display rules without changing votes."""
    display = []
    for slot in slots:
        if slot['status'] == 'unresolved':
            display.append('⟦' + ' ∥ '.join(key or '∅' for key in slot['tied_readings']) + '⟧')
        elif slot['status'] != 'omission':
            key = slot['selected']
            reading = next((r for r in slot['readings'] if r['text'] == key), None)
            if reading is None or not reading['surfaces']:
                raise ValueError('A selected consensus reading lost its original raw surfaces')
            surfaces = Counter(reading['surfaces'].values())
            best = max(surfaces.values())
            winners = sorted(surface for surface, count in surfaces.items() if count == best)
            display.append(winners[0] if len(winners) == 1 else '⟦' + ' ∥ '.join(winners) + '⟧')
    return ' '.join(display)


def _digital_pointer(digital, pointer, support):
    """Map one exact full-section token span to its original ordered SL support."""
    import unicodedata
    if not isinstance(pointer, dict) or pointer.get('section') != digital.get('source_section'):
        raise ValueError('A digital counterpart must pin the exact full Source Library section')
    full = digital.get('full_source_text')
    window = digital.get('source_window', {})
    start, end = pointer.get('start'), pointer.get('end')
    lo, hi = window.get('start'), window.get('end')
    if (not isinstance(full, str) or type(start) is not int or type(end) is not int
            or type(lo) is not int or type(hi) is not int or not 0 <= lo <= start < end <= hi <= len(full)
            or full[start:end] != pointer.get('original_text') or full[lo:hi] != digital['text']):
        raise ValueError('A digital counterpart differs from its exact retained full-section slice')
    def letter(char):
        return unicodedata.category(char).startswith(('L', 'M')) or char in "'’ʼ᾽"
    if ((start and letter(full[start - 1]) and letter(full[start]))
            or (end < len(full) and letter(full[end - 1]) and letter(full[end]))):
        raise ValueError('A digital counterpart cannot cut inside a source word or combining mark')
    before = tokenize(full[lo:start])
    word = tokenize(full[start:end])
    after = tokenize(full[end:hi])
    complete = tokenize(digital['text'])
    if len(word) != 1 or [k for k, _ in before + word + after] != [k for k, _ in complete]:
        raise ValueError('A digital counterpart must identify one complete token under the frozen tokenizer')
    if len(support) != len(complete):
        raise ValueError('Reviewed digital token positions differ from their retained source order')
    return support[len(before)], word[0][0]


def _observation_source_pin(witness, span):
    """Require the exact raw strip and image pins already checked by the loader."""
    pin, source_span = span.get('raw_source_pin', {}), span.get('raw_source_span', {})
    parts = [part for part in witness.get('raw_strips', []) if part['id'] == pin.get('id')]
    if len(parts) != 1:
        raise ValueError('A source observation needs its exact original model strip identity')
    part = parts[0]
    original = part['raw_prediction_record']
    start, end = source_span.get('start'), source_span.get('end')
    if (pin.get('model') != witness.get('model') or pin.get('revision') != witness.get('revision')
            or pin.get('raw_file_sha256') != witness.get('raw_file_sha256')
            or pin.get('prediction_record_sha256') != sha(encode(original))
            or pin.get('text_sha256') != sha(original['raw_prediction'].encode())
            or pin.get('image_sha256') != part['image_sha256']
            or span.get('source_image_sha256') != part['image_sha256']
            or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(original['raw_prediction'])
            or original['raw_prediction'][start:end] != source_span.get('original_text')
            or source_span.get('original_text') != span['original_text']
            or part['start'] + start != span['start'] or part['start'] + end != span['end']):
        raise ValueError('A source observation differs from its exact raw record, image or codepoint span')
    return {'witness_id': witness['id'], 'raw_source_pin': deepcopy(pin),
            'raw_source_span': deepcopy(source_span), 'source_image_sha256': part['image_sha256'],
            'evidence': span['evidence'], 'original_text': span['original_text']}


def _fragment_support(result, witness, span):
    """Locate one retained raw fragment by exact codepoints and support order."""
    from ocr_consensus import _reviewed_voting_parts
    _validate_fragment_span(witness['text'], span, span.get('source_image_sha256'))
    pin = _observation_source_pin(witness, span)
    parts = _reviewed_voting_parts(witness)
    if parts is None:
        parts = [(0, len(witness['text']), True, None, witness['text'])]
    matches = [p for p in parts if p[0] <= span['start'] < span['end'] <= p[1]]
    if len(matches) != 1:
        raise ValueError('A source fragment cannot cross a retained/held voting boundary')
    start, end, retained, index, raw = matches[0]
    item = {'observed_printed_text': span['observed_printed_text'], **pin}
    if not retained:
        return None, None, {**item, 'disposition': 'Already held by an exact source abstention; no fragment vote.'}
    lo, hi = span['start'] - start, span['end'] - start
    before, word, after = tokenize(raw[:lo]), tokenize(raw[lo:hi]), tokenize(raw[hi:])
    complete = tokenize(raw)
    if (len(word) != 1 or [key for key, _ in before + word + after] != [key for key, _ in complete]):
        raise ValueError('A source fragment must identify one whole retained token under the frozen tokenizer')
    identifier = witness['id'] if index is None else f"{witness['id']}#voting-segment-{index:04d}"
    support = [i for i, slot in enumerate(result['ocr_consensus']['slots']) if _supports(slot, identifier)]
    if len(support) != len(complete):
        raise ValueError('Source fragment support differs from the exact retained raw token order')
    position = support[len(before)]
    return position, word[0][0], {**item, 'position': position,
        'raw_reading': word[0][0], 'disposition': 'Preserve raw displayed fragment; exclude it from lexical counts.'}


def _qualify_reviewed_single_readings(result, witnesses, reference, *, raw_network_reference=None):
    """Qualify sole digital readings and retain explicit source observations.

    Full-section counterpart offsets identify repeated occurrences. A conflicting
    source observation adds a visible variant with zero votes, never a new witness
    or an arbitrary winner. The exact ordinary merge remains hash-linked.
    """
    spans = [(witness, span) for witness in witnesses
             for span in witness.get('source_confirmed_wrong_readings', [])]
    fragments = [(witness, span) for witness in witnesses
                 for span in witness.get('source_confirmed_fragments', [])]
    if not spans and not fragments:
        return result
    public_reference(reference)
    if _render_slots(result['ocr_consensus']['slots']) != result['text']:
        raise ValueError('Ordinary source-observation input differs from the frozen display rules')
    updated = deepcopy(result)
    digital = next(w for w in witnesses if w['id'] == SL)
    words = [key for key, _ in tokenize(digital['text'])]
    support = [i for i, slot in enumerate(updated['ocr_consensus']['slots']) if _supports(slot, SL)]
    if len(support) != len(words):
        raise ValueError('Reviewed digital token positions differ from their retained source order')
    positions, observations, evidence, artifacts, incomplete = set(), {}, [], [], []
    for witness, span in spans:
        if span.get('classification') in ('marginal-reference', 'neighboring-column-intrusion', 'incomplete-source-coverage'):
            if span.get('digital_counterpart') is not None:
                raise ValueError('A held reference or incomplete strip cannot designate one authorial digital token')
            held = {'classification': span['classification'],
                'observed_printed_text': span['observed_printed_text'],
                'source_review': deepcopy(reference), **_observation_source_pin(witness, span)}
            (incomplete if span['classification'] == 'incomplete-source-coverage' else artifacts).append(held)
            continue
        phrase = span['observed_printed_text']
        observed = [key for key, _ in tokenize(phrase)]
        if not observed:
            continue  # Numeric/Latin references do not create Greek source readings.
        pointer = span.get('digital_counterpart')
        if pointer is not None:
            if len(observed) != 1:
                raise ValueError('An exact source observation must describe one lexical token')
            position, digital_word = _digital_pointer(digital, pointer, support)
            context = span.get('digital_context')
            if context is not None:
                lo, hi = context.get('start'), context.get('end')
                full = digital['full_source_text']
                if (type(lo) is not int or type(hi) is not int
                        or not 0 <= lo <= pointer['start'] < pointer['end'] <= hi <= len(full)
                        or full[lo:hi] != context.get('original_text')):
                    raise ValueError('A source observation differs from its exact full-section context')
            raw_pin = _observation_source_pin(witness, span)
            positions.add(position)
            item = {'observed_printed_text': phrase, 'observed_reading': observed[0],
                'digital_counterpart': deepcopy(pointer), 'source_review': deepcopy(reference),
                **raw_pin, 'vote_weight': 0}
            if context is not None:
                item['digital_context'] = deepcopy(context)
            evidence.append(item)
            if observed[0] != digital_word:
                observations.setdefault(position, []).append(item)
            continue
        # Compatibility for earlier one-off words, never a repeated-occurrence
        # or source-glyph lookup. New reviewed occurrences use exact pointers.
        keys = [alignment_key(key) for key in observed]
        starts = [i for i in range(len(words) - len(keys) + 1)
                  if [alignment_key(w) for w in words[i:i + len(keys)]] == keys]
        if len(starts) != 1:
            raise ValueError('A source-confirmed wrong-word exclusion needs one unambiguous bounded digital counterpart')
        positions.update(support[i] for i in range(starts[0], starts[0] + len(keys)))
    digital_positions = set(positions)
    fragment_observations, fragment_readings, fragment_evidence = {}, {}, []
    for witness, span in fragments:
        position, reading, item = _fragment_support(result, witness, span)
        item['source_review'] = deepcopy(reference)
        fragment_evidence.append(item)
        if position is not None:
            fragment_observations.setdefault(position, []).append(item)
            fragment_readings.setdefault(position, set()).add(reading)
            positions.add(position)
    if (observations or fragments) and raw_network_reference is None:
        raise ValueError('A source-observation variant requires its hash-linked ordinary vote network')
    original_slots = deepcopy(result['ocr_consensus']['slots'])
    for position in sorted(positions):
        slot = updated['ocr_consensus']['slots'][position]
        if position in observations:
            items = observations[position]
            old = slot['tied_readings'] if slot['selected'] is None else [slot['selected']]
            slot.update(status='unresolved', selected=None, lexical_eligible=False,
                tied_readings=sorted(set(old + [item['observed_reading'] for item in items])),
                lexical_exclusion='source-observed-reading-disagreement', source_observations=deepcopy(items))
        elif position in digital_positions and slot['status'] == 'single-witness' and slot['lexical_eligible']:
            slot.update(lexical_eligible=False, lexical_exclusion='source-reviewed-digital-only-reading')
        if position in fragment_observations:
            slot['source_fragment_observations'] = deepcopy(fragment_observations[position])
            if slot['selected'] is None or slot['selected'] in fragment_readings[position]:
                slot.update(lexical_eligible=False, lexical_exclusion='source-internal-split-word-fragment')
                if slot['selected'] is not None and slot['status'] != 'unresolved':
                    slot['status'] = 'incomplete-reading'
    updated['text'] = _render_slots(updated['ocr_consensus']['slots'])
    updated['analysis_text'] = ' '.join(s['selected'] for s in updated['ocr_consensus']['slots'] if s['lexical_eligible'])
    updated['ocr_consensus']['counts'] = dict(Counter(s['status'] for s in updated['ocr_consensus']['slots']))
    changes = [{'position': i, 'original_slot': old, 'corrected_slot': deepcopy(new)}
               for i, (old, new) in enumerate(zip(original_slots, updated['ocr_consensus']['slots'])) if old != new]
    raw_reference = (compact_corpus_consensus(result, raw_network_reference)['ocr_consensus']['full_network']
                     if raw_network_reference is not None else None)
    audit = {'kind': 'source-observation-and-eligibility', 'source_review': deepcopy(reference),
        'original_text': result['text'], 'corrected_text': updated['text'],
        'original_analysis_text': result['analysis_text'], 'corrected_analysis_text': updated['analysis_text'],
        'original_counts': deepcopy(result['ocr_consensus']['counts']),
        'corrected_counts': deepcopy(updated['ocr_consensus']['counts']), 'changes': changes,
        'raw_network': raw_reference, 'ordinary_result_sha256': sha(encode(result)),
        'source_observations': evidence, 'nonlexical_source_artifacts': artifacts,
        'held_incomplete_source_readings': incomplete,
        'source_fragments': fragment_evidence,
        'policy': 'Source-rejected raw readings abstain. Sole digital readings stay visible and ineligible. Explicit source-image observations retain conflicting readings without adding a source-family vote.',
        'reversal': 'Restore the exact hash-linked ordinary merge before these source qualifications.'}
    if 'outcome_eligibility_review' in result['ocr_consensus']:
        audit['previous_projection'] = deepcopy(result['ocr_consensus']['outcome_eligibility_review'])
    updated['ocr_consensus']['outcome_eligibility_review'] = audit
    return updated


def unapply_source_observation_projection(result, ordinary_result):
    """Restore and verify the exact ordinary vote before source observations."""
    audit = result['ocr_consensus']['outcome_eligibility_review']
    reference = audit['raw_network']
    if reference is None:
        raise ValueError('A source observation has no retained ordinary network reference')
    if compact_corpus_consensus(ordinary_result, reference)['ocr_consensus']['full_network'] != reference:
        raise ValueError('The ordinary source-observation network changed')
    if sha(encode(ordinary_result)) != audit['ordinary_result_sha256']:
        raise ValueError('The source observation ordinary preimage changed')
    if (result['text'] != audit['corrected_text']
            or result['analysis_text'] != audit['corrected_analysis_text']
            or result['ocr_consensus']['counts'] != audit['corrected_counts']):
        raise ValueError('The source observation text, analysis or counts changed after projection')
    restored = deepcopy(result)
    for change in audit['changes']:
        position = change['position']
        if restored['ocr_consensus']['slots'][position] != change['corrected_slot']:
            raise ValueError('The source observation slot projection changed')
        restored['ocr_consensus']['slots'][position] = deepcopy(change['original_slot'])
    restored['text'] = audit['original_text']
    restored['analysis_text'] = audit['original_analysis_text']
    restored['ocr_consensus']['counts'] = deepcopy(audit['original_counts'])
    if 'previous_projection' in audit:
        restored['ocr_consensus']['outcome_eligibility_review'] = deepcopy(audit['previous_projection'])
    else:
        del restored['ocr_consensus']['outcome_eligibility_review']
    if restored != ordinary_result:
        raise ValueError('Source-observation reversal changes more than its exact reviewed projection')
    return deepcopy(ordinary_result)


def unapply_outcome_abstentions(witness):
    """Reconstruct the exact assembled witness before its reviewed word masks."""
    current = deepcopy(witness)
    audit = current.pop('outcome_partitions')
    if ({'voting_segments': current.get('voting_segments'), 'abstention_audit': current.get('abstention_audit')}
            != audit['after']):
        raise ValueError('Reviewed outcome voting partitions changed')
    del current['source_confirmed_wrong_readings']
    for key, value in audit['before'].items():
        if value is None:
            current.pop(key, None)
        else:
            current[key] = deepcopy(value)
    if sha(encode(current)) != audit['before_witness_sha256']:
        raise ValueError('Restored outcome witness differs from its frozen preimage')
    return current
