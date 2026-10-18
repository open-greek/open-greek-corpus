"""Pure plans for reviewed Photius source windows and witness exclusions.

The caller freezes source authorities and original network archives, and owns
application and reversal. This module never reads or writes a file, chooses a
winning witness, or supplies letters missing from the printed source.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
import math
from pathlib import PurePosixPath
import re

from ocr_consensus import (_reviewed_voting_parts, compact_corpus_consensus,
                           merge_witnesses, restore_corpus_consensus)

SL = 'source-library-local002'
SL_ARCHIVE_SHA256 = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{64}', value))


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


@lru_cache(maxsize=2)
def _network_archive(raw):
    # Hundreds of page plans share one large immutable archive. Decode it
    # once; each plan copies the selected witnesses before changing them.
    return json.loads(gzip.decompress(raw))


def public_reference(reference):
    path = reference.get('path') if isinstance(reference, dict) else None
    if (not isinstance(path, str) or not path or ':' in path or '\\' in path
            or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts
            or not digest(reference.get('sha256'))):
        raise ValueError('A reviewed source requires a relative public path and SHA256')


def bbox(value):
    return (isinstance(value, list) and len(value) == 4
            and all(type(v) in (int, float) and math.isfinite(v) for v in value)
            and 0 <= value[0] < value[2] <= 1 and 0 <= value[1] < value[3] <= 1)


def _project(witness, all_exclusions, source_review, prior=None):
    old = deepcopy(witness)
    text = old['text']
    points = sorted({0, len(text), *(p for s in all_exclusions for p in (s['start'], s['end']))})
    retained, excluded = [], []
    for start, end in zip(points, points[1:]):
        reasons = sorted({s['reason'] for s in all_exclusions if s['start'] <= start and end <= s['end']})
        item = {'start': start, 'end': end, 'text': text[start:end]}
        if reasons:
            excluded.append({**item, 'reason': '; '.join(reasons)})
        elif retained and retained[-1]['end'] == start:
            retained[-1].update(end=end, text=text[retained[-1]['start']:end])
        else:
            retained.append(item)
    updated = {**old, 'voting_segments': retained, 'abstention_audit': {
        'reviewed_text_sha256': sha(text.encode()), 'source_review': deepcopy(source_review),
        'excluded_spans': excluded}}
    if prior:
        updated['abstention_audit']['prior_abstention_audit'] = deepcopy(prior)
        updated['abstention_audit']['prior_voting_segments'] = deepcopy(old.get('voting_segments'))
    _reviewed_voting_parts(updated)
    return updated


def _mask(witness, exclusions, source_review):
    """Union reviewed exclusions with earlier abstentions, preserving raw text."""
    _reviewed_voting_parts(witness)  # Reject a malformed existing projection first.
    text = witness['text']
    prior = witness.get('abstention_audit', {})
    new, previous = [], 0
    for span in exclusions:
        start, end = span.get('start'), span.get('end')
        if (type(start) is not int or type(end) is not int
                or not previous <= start < end <= len(text)
                or span.get('original_text') != text[start:end]
                or span.get('classification') not in {'running_header', 'critical-apparatus', 'printer_signature', 'ocr_markup'}
                or not bbox(span.get('source_region')) or not span.get('evidence')):
            raise ValueError('A model exclusion needs exact ordered source-reviewed codepoint spans')
        new.append({'start': start, 'end': end, 'text': text[start:end],
                    'reason': span['classification'] + ': ' + span['evidence']})
        previous = end
    return _project(witness, [*prior.get('excluded_spans', []), *new], source_review, prior)


def _digital(source, record, source_review):
    section = record.get('source_section', {})
    if not isinstance(section, dict):
        raise ValueError('Available Source Library text requires a pinned section')
    text = source.get('text')
    if (source.get('id') != SL or source.get('vote_group', SL) != SL
            or source.get('license') != 'CC-BY-SA-4.0'
            or not source.get('source_url', '').startswith('https://')
            or source.get('source_file_sha256') != SL_ARCHIVE_SHA256
            or source.get('source_section') != section.get('id')
            or not digest(section.get('artifact_sha256'))
            or source.get('artifact_sha256') != section['artifact_sha256']
            or not isinstance(text, str) or not text
            or text != section.get('full_original_text')
            or sha(text.encode()) != section.get('full_text_sha256')):
        raise ValueError('Digital witness differs from its exact full-source section or credit pins')
    if not isinstance(record.get('first_boundary_policy'), str) or not record['first_boundary_policy'].strip():
        raise ValueError('A digital window needs an explicit observed-prefix boundary policy')
    regions = record.get('source_regions', {})
    if not all(bbox(regions.get(name)) for name in ('first', 'body', 'last')):
        raise ValueError('A digital window needs reviewed first/body/last source geometry')
    held = record.get('held_spans')
    if (not isinstance(held, list) or not isinstance(record.get('voting_segments'), list)
            or not record['voting_segments']):
        raise ValueError('Digital retained and held spans must be explicit')
    excluded = []
    for span in held:
        excluded.append({'start': span.get('start'), 'end': span.get('end'),
                         'text': span.get('original_text'), 'reason': span.get('reason')})
    updated = {**deepcopy(source), 'vote_group': SL,
               'voting_segments': deepcopy(record['voting_segments']),
               'abstention_audit': {'reviewed_text_sha256': sha(text.encode()),
                                   'source_review': deepcopy(source_review), 'excluded_spans': excluded},
               'first_boundary_policy': record['first_boundary_policy']}
    _reviewed_voting_parts(updated)
    return updated


def _is_sl(witness):
    return (witness['id'] == SL or witness.get('vote_group') == SL
            or (witness.get('source_file_sha256') == SL_ARCHIVE_SHA256
                and bool(witness.get('source_section'))))


def plan(current_row, current_network_archive_bytes, pinned_sl_witness, reviewed_record, *,
         source_review, network_reference):
    """Return (updated row, full merge result, audit) without side effects.

    Model masks address the current full raw witness. Earlier exclusions remain
    excluded even if a later review retains a wider window. An existing digital
    reading is retained as evidence and replaced once, rather than gaining an
    additional family vote. Missing source text can never become an omission.
    """
    public_reference(source_review)
    row, record = deepcopy(current_row), deepcopy(reviewed_record)
    locus = row.get('locus', '')
    if (row.get('urn') != 'photius.bibliotheca'
            or not re.fullmatch(r'photius_bekker1824_\d{4}\.1', locus)
            or record.get('locus') != locus or not record.get('reviewed_at') or not record.get('evidence')):
        raise ValueError('Reading review must identify the exact fresh Photius page and completed source comparison')
    physical = row.get('physical_refs', {})
    if (record.get('scan_page'), record.get('printed_page')) != (physical.get('scan_page'), physical.get('printed_page')):
        raise ValueError('Reviewed physical page differs from the corpus row')
    reference = row['ocr_consensus']['full_network']
    archive = _network_archive(current_network_archive_bytes)
    full = archive[reference['key']]
    restore_corpus_consensus({k: row[k] for k in ('text', 'analysis_text', 'ocr_consensus')}, full)
    original_witnesses = deepcopy(full['ocr_consensus']['witnesses'])
    witnesses = deepcopy(original_witnesses)
    by_id = {w['id']: w for w in witnesses}
    if len(by_id) != len(witnesses):
        raise ValueError('Current full network repeats witness identities')
    masks, notes, masked_ids = record.get('raw_witness_masks', []), [], set()
    for mask in masks:
        pin = mask.get('witness', {})
        identifier = pin.get('id')
        if identifier in masked_ids or identifier not in by_id or _is_sl(by_id[identifier]):
            raise ValueError('Each source mask must identify one original model witness exactly once')
        masked_ids.add(identifier)
        if mask.get('full_network') != {'path': reference['path'], 'key': reference['key'],
                                       'archive_sha256': sha(current_network_archive_bytes)}:
            raise ValueError('Model mask differs from the current frozen network archive')
        witness = by_id[identifier]
        for name in ('id', 'model', 'revision', 'artifact_sha256', 'text_sha256', 'raw_file_sha256', 'image_sha256'):
            if pin.get(name) != witness.get(name) or not pin.get(name):
                raise ValueError('Source mask model, checkpoint, raw artifact or image pin changed')
        if (mask.get('original_text') != witness['text']
                or sha(witness['text'].encode()) != pin['text_sha256']):
            raise ValueError('Source mask does not address the exact complete raw model text')
        exclusions = mask.get('exclusions')
        if not isinstance(exclusions, list) or not exclusions:
            raise ValueError('A source mask must explicitly identify nonempty exclusions')
        by_id[identifier] = _mask(witness, exclusions, source_review)
        notes.extend({'locus': locus, 'witness_id': identifier, **deepcopy(span),
                      'source_review': deepcopy(source_review), 'physical_refs': deepcopy(physical)}
                     for span in exclusions)
    witnesses = [by_id[w['id']] for w in witnesses]
    prior_sl = [w for w in witnesses if _is_sl(w)]
    if len(prior_sl) > 1 or any(w['id'].startswith('source-library') and not _is_sl(w) for w in witnesses):
        raise ValueError('The digital edition cannot contribute multiple aliased source votes')
    action = 'unavailable'
    if pinned_sl_witness is not None:
        digital = _digital(pinned_sl_witness, record, source_review)
        if prior_sl:
            prior = prior_sl[0]
            if 'voting_segments' in prior:
                _reviewed_voting_parts(prior)
                if (prior['text'] != digital['text']
                        or prior['artifact_sha256'] != digital['artifact_sha256']):
                    raise ValueError('Earlier digital abstentions need an exact shared raw-text coordinate system')
                digital = _project(digital, [*prior['abstention_audit']['excluded_spans'],
                    *digital['abstention_audit']['excluded_spans']], source_review, prior['abstention_audit'])
            digital['retained_previous_readings'] = deepcopy(prior_sl)
        if any(w['artifact_sha256'] == digital['artifact_sha256'] for w in witnesses if not _is_sl(w)):
            raise ValueError('A digital source cannot duplicate an existing model artifact')
        witnesses = [w for w in witnesses if not _is_sl(w)] + [digital]
        action = 'replaced' if prior_sl else 'added'
    elif record.get('source_section'):
        raise ValueError('An available reviewed digital section needs its exact pinned witness')
    if pinned_sl_witness is None and not masks:
        return row, deepcopy(full), {'changed': False, 'locus': locus, 'source_library_action': action,
                                    'source_review': deepcopy(source_review), 'mask_notes': []}
    result = merge_witnesses(witnesses)
    before_models = [w for w in original_witnesses if not _is_sl(w)]
    after_models = [w for w in result['ocr_consensus']['witnesses'] if not _is_sl(w)]
    if {w['id'] for w in before_models} != {w['id'] for w in after_models}:
        raise ValueError('Reading review changed the model-family membership')
    for original in before_models:
        updated = next(w for w in after_models if w['id'] == original['id'])
        for name, value in original.items():
            if name not in {'voting_segments', 'abstention_audit'} and updated.get(name) != value:
                raise ValueError('Reading review changed an original model raw reading or metadata')
    expected_sl_votes = 1 if pinned_sl_witness is not None else len(prior_sl)
    if sum(_is_sl(w) for w in result['ocr_consensus']['witnesses']) != expected_sl_votes:
        raise ValueError('The digital source was counted more than once')
    boundary, raw_boundary = None, None
    if record.get('printed_prefix_fragment'):
        from photius_body_vote import source_boundary_projection
        if pinned_sl_witness is None:
            raise ValueError('A reviewed prefix projection requires bounded complete comparison words')
        result, raw_boundary, boundary = source_boundary_projection(result, leading=True,
            evidence=record['evidence'] + ' Printed initial fragment: ' + record['printed_prefix_fragment'],
            source_review=source_review, reviewed_at=record['reviewed_at'],
            raw_network_reference={**network_reference, 'key': network_reference['key'] + ':raw-vote'},
            model_witness_ids=[w['id'] for w in after_models])
    compact = compact_corpus_consensus(result, network_reference)
    restore_corpus_consensus(compact, result)
    metadata = {'source_review': deepcopy(source_review), 'reviewed_record_sha256': sha(encode(record)),
                'original_full_network': deepcopy(reference), 'original_archive_sha256': sha(current_network_archive_bytes),
                'source_library_action': action, 'masked_witnesses': sorted(masked_ids),
                'first_boundary_policy': record.get('first_boundary_policy'), 'reviewed_at': record['reviewed_at']}
    if boundary:
        metadata['source_boundary_projection'] = boundary
    if 'reading_repair' in row:
        metadata['previous_reading_repair'] = deepcopy(row['reading_repair'])
    updated = {**row, **compact, 'reading_repair': metadata}
    audit = {'changed': True, 'locus': locus, **metadata, 'original_row': row, 'corrected_row': updated,
             'original_row_sha256': sha(encode(row)), 'corrected_row_sha256': sha(encode(updated)),
             'model_witnesses_before': len(before_models), 'model_witnesses_after': len(after_models),
             'source_library_votes_before': len(prior_sl),
             'source_library_votes_after': sum(_is_sl(w) for w in result['ocr_consensus']['witnesses']),
             'mask_notes': notes, 'source_library_reading': deepcopy(pinned_sl_witness),
             'full_network': compact['ocr_consensus']['full_network'],
             'reversal': 'Restore the exact original row and its frozen full-network archive; no original witness or earlier abstention is discarded.'}
    if raw_boundary is not None:
        audit['boundary_raw_vote'] = raw_boundary
    return updated, result, audit
