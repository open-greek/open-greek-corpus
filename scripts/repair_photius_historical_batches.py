#!/usr/bin/env python3
"""Append, check, and reverse bounded historical Photius reading reviews.

Each batch freezes its immediate preimage and its authored source table. Earlier
release artifacts are never rewritten. These are partial occurrence reviews,
not a full row consensus or an estimate of recognition accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import gzip
import json
import math
from pathlib import Path
import re
from types import ModuleType
import unicodedata

from prepare_photius_historical_readings import (
    ROOT, CORPUS, SCAN, SCAN_SHA, LIBRARY, LIBRARY_SHA,
    encode, sha, row_sha, exact_span,
)

BASE_SHA = 'd7ba127a54e18726edd960db8a25ca85a91aae51735d67b7917f9d8cdd0aa748'
ARCHIVE = Path('data/corpus_changes/photius-bekker-historical-batches')
SCHEMA = 'photius-historical-batch-v1'
TABLES = (
    'photius_historical_observations_unpaired',
    'photius_historical_observations_continued',
    'photius_historical_observations_orators',
    'photius_historical_observations_fragments',
    'photius_historical_observations_pages0007_0008',
    'photius_historical_observations_prefix0007',
    'photius_historical_observations_page0009',
    'photius_historical_observations_page0010',
    'photius_historical_observations_pages0011_0015',
)
QUALIFICATION = 'Only the recorded occurrences are source reviewed; other historical text remains unassessed.'
_CROP_HASHES = {}


def _prefix_scope(row, item):
    """Permit only the complete retained prefix of the separately merged 7.5.

    This does not authorize general edits to consensus rows. The earlier tail
    network is a disjoint source range and must survive without a new vote.
    """
    scope = item.get('review_scope')
    if scope in (None, 'retained-editorial-body'):
        return False
    if scope != 'retained-historical-prefix':
        raise ValueError('Unknown historical review scope')
    from repair_photius_body import LOCUS7, validate_projection
    if (row.get('locus') != LOCUS7 or not row.get('source_body_correction')
            or row.get('historical_reading_batches') or row.get('editorial_layer')
            or item.get('scan_only') or item.get('projection_only') or item.get('source_fragment')):
        raise ValueError('Prefix review requires the original separately merged 7.5')
    validate_projection(row)
    prefix = row['source_body_correction']['retained_prefix']
    tail = row['ocr_consensus'].get('span_networks', {}).get('replacement_tail')
    if (not prefix or prefix == prefix.rstrip() or item['original_text'] != prefix.rstrip()
            or not tail or tail['text'] != row['source_body_correction']['replacement_text']):
        raise ValueError('Prefix review must preserve the exact independent tail boundary')
    return True


def _editorial_body_scope(row, item):
    """Review a validated contiguous body without changing its apparatus audit."""
    if item.get('review_scope') != 'retained-editorial-body':
        return False
    from repair_photius_apparatus import lexical_segments
    if (not row.get('editorial_layer') or row.get('ocr_consensus') or
            row.get('historical_reading_batches')):
        raise ValueError('Editorial body review requires an unchanged apparatus projection')
    segments = lexical_segments(row)
    if len(segments) != 1 or segments[0] != row['text']:
        raise ValueError('Editorial body review requires one contiguous retained source span')
    return True


def paths(batch_id):
    if not isinstance(batch_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', batch_id):
        raise ValueError('A batch requires a safe stable identifier')
    base = ARCHIVE / batch_id
    return {name: base / file for name, file in (
        ('audit', 'changes.json'), ('before', 'before-corpus.jsonl.gz'),
        ('review', 'source-review.json'), ('table', 'source-table.py'),
        ('records', 'records.jsonl.gz'), ('networks', 'word-networks.json.gz'))}


def _table(raw, relative):
    """Execute the exact pinned bytes, rather than a stale imported module."""
    module = ModuleType('historical_batch_source')
    exec(compile(raw, relative, 'exec'), module.__dict__)
    paths(module.BATCH_ID)
    if not isinstance(module.REVIEWED_AT, str) or not module.REVIEWED_AT:
        raise ValueError('A source table requires its actual review timestamp')
    held = []
    for name in ('unresolved', 'unapplied_source_observations'):
        if hasattr(module, name):
            held.extend(getattr(module, name)())
    return module, held


def catalog(root=ROOT):
    result = {}
    for name in TABLES:
        path = Path('scripts') / (name + '.py')
        if not (Path(root) / path).exists():
            continue
        raw = (Path(root) / path).read_bytes()
        module, _ = _table(raw, path.as_posix())
        if module.BATCH_ID in result:
            raise ValueError('Two source tables claim the same batch identity')
        result[module.BATCH_ID] = (path, raw)
    return result


def _box(box):
    if (not isinstance(box, (list, tuple)) or len(box) != 4 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in box) or
            not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1):
        raise ValueError('A source observation requires a normalized finite rectangle')
    return list(box)


def _sections(raw):
    return {section['id']: '\n'.join(b['text'] for b in section['blocks'])
            for section in json.loads(gzip.decompress(raw))['sections']}


def _source_credit(root):
    coverage = json.loads((Path(root)/'data/corpus_changes/photius-bekker-coverage/coverage.json').read_bytes())
    credit = coverage['source_library']
    if credit['sha256'] != LIBRARY_SHA:
        raise ValueError('Historical batch digital source credit no longer identifies the pinned file')
    return {key: deepcopy(credit.get(key)) for key in ('edition', 'url', 'sha256', 'license',
        'rights', 'api_notice_url', 'api_notice_checked_date', 'separate_api_notice')}


def _word_character(char):
    return unicodedata.category(char)[0] in {'L', 'M'} or char in "’'ʼ᾽"


def _greek_words(text):
    """Raw codepoint spans, including an adjacent printed continuation hyphen."""
    from ocr_consensus import greek_letter
    words, index = [], 0
    while index < len(text):
        if not _word_character(text[index]):
            index += 1; continue
        start = index
        while index < len(text) and _word_character(text[index]):
            index += 1
        end = index + (index < len(text) and text[index] in '-‐')
        if any(greek_letter(char) for char in text[start:index]):
            words.append((start, end, text[start:end]))
    return words


def _fragments(item):
    corrected = item['corrected_text']; words = _greek_words(corrected)
    flag = item.get('source_fragment', {})
    if (not isinstance(flag, dict) or set(flag)-{'leading', 'trailing', 'qualification'} or
            any(type(flag.get(side, False)) is not bool for side in ('leading', 'trailing')) or
            flag and (not (flag.get('leading') or flag.get('trailing')) or
                      not isinstance(flag.get('qualification'), str) or not flag['qualification'].strip())):
        raise ValueError('A source fragment requires an explicit side and completed source qualification')
    automatic = bool(words and words[-1][2].endswith(('-', '‐')) and not corrected[words[-1][1]:].strip())
    result = []
    for side, index in (('leading', 0), ('trailing', -1)):
        if not flag.get(side) and not (side == 'trailing' and automatic):
            continue
        if not words:
            raise ValueError('A qualified source fragment must name a retained Greek token')
        start, end, text = words[index]
        result.append({'side': side, 'start': start, 'end': end, 'text': text,
            'qualification': flag.get('qualification') if flag.get(side) else
                'The reviewed printed continuation hyphen marks an incomplete word; no completion is supplied.',
            'evidence': item['evidence'],
            'classification': 'source-confirmed-word-fragment',
            'basis': 'explicit-source-qualification' if flag.get(side) else 'reviewed-terminal-greek-hyphen'})
    return result


def _fragment_positions(full, fragments):
    positions = [i for i, slot in enumerate(full['ocr_consensus']['slots'])
        if any('direct-scan-reading' in r['support'] for r in slot['readings'])]
    if fragments and not positions:
        raise ValueError('A source fragment lost its direct scan reading support')
    return {positions[0 if f['side'] == 'leading' else -1] for f in fragments}


def _project_fragment_network(full, fragments, reference):
    """Eligibility-only overlay; every original slot and raw witness survives."""
    if not fragments:
        return
    if full.get('source_fragment_projection'):
        raise ValueError('A word network cannot receive the fragment projection twice')
    original = deepcopy(full)
    positions = sorted(_fragment_positions(full, fragments))
    projection = {'source_review': reference, 'source_fragments': deepcopy(fragments),
        'original_sha256': sha(encode(original)), 'original_text': full['text'],
        'original_analysis_text': full['analysis_text'],
        'original_counts': deepcopy(full['ocr_consensus']['counts']),
        'original_slots': [deepcopy(full['ocr_consensus']['slots'][i]) for i in positions]}
    for position in positions:
        slot = full['ocr_consensus']['slots'][position]
        slot['lexical_eligible'] = False
        slot['lexical_exclusion'] = 'source-confirmed-word-fragment'
        if slot['status'] not in {'unresolved', 'omission'}:
            slot['status'] = 'incomplete-reading'
    full['analysis_text'] = ' '.join(s['selected'] for s in full['ocr_consensus']['slots'] if s['lexical_eligible'])
    full['ocr_consensus']['counts'] = dict(Counter(s['status'] for s in full['ocr_consensus']['slots']))
    full['source_fragment_projection'] = projection
    from photius_body_vote import _render_slots
    if _render_slots(full['ocr_consensus']['slots']) != original['text']:
        raise ValueError('Fragment eligibility projection changed the observed display')


def restore_fragment_network(full):
    """Exactly recover the ordinary vote before reviewed fragment eligibility."""
    if not full.get('source_fragment_projection'):
        return deepcopy(full)
    restored = deepcopy(full); projection = restored.pop('source_fragment_projection')
    for slot in projection['original_slots']:
        restored['ocr_consensus']['slots'][slot['position']] = slot
    restored['text'] = projection['original_text']
    restored['analysis_text'] = projection['original_analysis_text']
    restored['ocr_consensus']['counts'] = projection['original_counts']
    if sha(encode(restored)) != projection['original_sha256']:
        raise ValueError('Ordinary fragment network differs from its exact original')
    projected = deepcopy(restored)
    _project_fragment_network(projected, projection['source_fragments'], projection['source_review'])
    if projected != full:
        raise ValueError('Fragment network differs from its exact eligibility overlay')
    return restored


def compile_review(before, library_raw, scan_raw, observations, *, batch_id,
                   reviewed_at, table_pin, held=(), source_credit=None):
    """Resolve exact old spans and independently pin every physical source crop."""
    paths(batch_id)
    if sha(scan_raw) != SCAN_SHA or sha(library_raw) != LIBRARY_SHA:
        raise ValueError('Historical batches require the exact released source files')
    if not reviewed_at or not table_pin.get('path') or not table_pin.get('sha256'):
        raise ValueError('Historical batches require a timestamp and exact source-table pin')
    import pymupdf
    rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
    sections = _sections(library_raw)
    records, occupied, images = [], {}, {}
    with pymupdf.open(stream=scan_raw, filetype='pdf') as source:
        for observation in observations:
            item = deepcopy(observation)
            locus, page = item['locus'], item['page']
            if (type(page) is not int or not 1 <= page <= len(source) or not re.fullmatch(
                    rf'helladius_chrestomathia_photius_bekker_v2_{page:04d}[.]\d+', locus)
                    or locus not in rows):
                raise ValueError('Observation requires an existing retained historical passage')
            old = rows[locus]
            prefix_scope = _prefix_scope(old, item)
            editorial_scope = _editorial_body_scope(old, item)
            if not (prefix_scope or editorial_scope) and (old.get('ocr_consensus') or old.get('editorial_layer') or (
                    'analysis_text' in old and not old.get('historical_reading_batch_projection'))):
                raise ValueError('Occurrence batches cannot replace another full lexical projection')
            if item.get('original_row_sha256', row_sha(old)) != row_sha(old):
                raise ValueError('The reviewed historical row changed')
            original, corrected = item['original_text'], item['corrected_text']
            projection_only = item.get('projection_only', False)
            if (type(projection_only) is not bool or not isinstance(corrected, str) or not corrected or
                    (corrected == original) != projection_only or
                    not isinstance(item.get('evidence'), str) or not item['evidence'].strip()):
                raise ValueError('A correction needs a changed reading, or an explicit eligibility-only review, and completed source evidence')
            start, end = exact_span(old['text'], original, item.get('occurrence'))
            if any(start < b and a < end for a, b in occupied.setdefault(locus, [])):
                raise ValueError('Reviewed occurrences overlap')
            occupied[locus].append((start, end))
            if prefix_scope and len(occupied[locus]) != 1:
                raise ValueError('A prefix review is one complete bounded source range')
            scan_text = item.get('scan_text', corrected)
            if scan_text != corrected and not item.get('transcription_convention'):
                raise ValueError('A differing literal scan transcription requires an explicit convention')
            fragments = _fragments(item)
            if projection_only and not fragments:
                raise ValueError('Eligibility-only observations require a qualified source fragment')
            if not projection_only and any(k in item for k in ('digital_context_text', 'digital_context_occurrence')):
                raise ValueError('Nonvoting digital context is reserved for eligibility-only observations')
            box = _box(item['source_region'])
            key = page, tuple(box)
            if key not in images:
                cache_key = SCAN_SHA, page, tuple(box), pymupdf.VersionBind
                if cache_key not in _CROP_HASHES:
                    sheet = source[page - 1]
                    rect = pymupdf.Rect(box[0]*sheet.rect.width, box[1]*sheet.rect.height,
                                        box[2]*sheet.rect.width, box[3]*sheet.rect.height)
                    scale = 3600 / max(rect.width, rect.height)
                    if len(_CROP_HASHES) >= 256:
                        _CROP_HASHES.clear()
                    _CROP_HASHES[cache_key] = sha(sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale),
                                                      clip=rect, alpha=False).tobytes('png'))
                images[key] = _CROP_HASHES[cache_key]
            counterpart, context = None, None
            if projection_only:
                if any(k in item for k in ('digital_text', 'digital_counterpart', 'digital_occurrence')):
                    raise ValueError('Eligibility-only context must never become a replacement voting witness')
                if item.get('digital_context_text'):
                    if page in {169, 170} or item.get('scan_only'):
                        raise ValueError('Unrelated digital pages cannot supply fragment context')
                    section = f'tlg4040-tlg001-local002-s{page+277}'
                    full, digital = sections[section], item['digital_context_text']
                    low, high = exact_span(full, digital, item.get('digital_context_occurrence'))
                    if (low and _word_character(full[low-1])) or (high < len(full) and _word_character(full[high])):
                        raise ValueError('Fragment context requires a bounded complete digital word or phrase')
                    context = {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA, 'section': section,
                        'start': low, 'end': high, 'original_text': digital,
                        'role': 'nonvoting-source-context'}
                elif not item.get('scan_only') or not item.get('qualification'):
                    raise ValueError('Eligibility-only observations need complete digital context or qualified scan-only evidence')
            elif item.get('scan_only'):
                if not item.get('qualification') or any(k in item for k in (
                        'digital_text', 'digital_counterpart', 'digital_occurrence')):
                    raise ValueError('Scan-only review needs qualification and cannot hide a digital reading')
            else:
                if page in {169, 170}:
                    raise ValueError('These digital windows repeat unrelated printed source pages')
                section = f'tlg4040-tlg001-local002-s{page+277}'
                full = sections[section]
                digital = item.get('digital_text', corrected)
                pointer = item.get('digital_counterpart')
                if pointer is None:
                    low, high = exact_span(full, digital, item.get('digital_occurrence'))
                else:
                    low, high = pointer['start'], pointer['end']
                    if (pointer.get('section') != section or pointer.get('original_text') != digital or
                            type(low) is not int or type(high) is not int or
                            not 0 <= low < high <= len(full) or full[low:high] != digital):
                        raise ValueError('The exact digital source pointer changed')
                for side, split in (('leading', low > 0 and _word_character(full[low-1])),
                                    ('trailing', high < len(full) and _word_character(full[high]))):
                    if split and not item.get('source_fragment', {}).get(side):
                        raise ValueError('An intra-word digital pointer requires explicit source_fragment qualification')
                counterpart = {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA,
                    'section': section, 'start': low, 'end': high, 'original_text': digital,
                    'context_start': max(0, low-80), 'context_end': min(len(full), high+80),
                    'context': full[max(0, low-80):min(len(full), high+80)]}
            records.append({'locus': locus, 'original_row_sha256': row_sha(old),
                'start': start, 'end': end, 'original_text': original, 'corrected_text': corrected,
                'source': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA,
                    'scan_page': page, 'printed_page': page+265, 'region': box, 'max_side': 3600,
                    'image_sha256': images[key], 'observed_text': scan_text, 'evidence': item['evidence'],
                    **({'transcription_convention': item['transcription_convention']}
                       if item.get('transcription_convention') else {})},
                'digital_counterpart': counterpart, 'scan_only': bool(item.get('scan_only')),
                'source_fragment': deepcopy(item.get('source_fragment', {})),
                'source_fragments': fragments,
                **({'projection_only': True, 'digital_context': context} if projection_only else {}),
                'qualification': item.get('qualification', QUALIFICATION),
                **({'review_scope': item['review_scope']} if prefix_scope or editorial_scope else {}),
                'raw_witnesses': item.get('raw_witnesses', []), 'reviewed_at': reviewed_at})
    if not records:
        raise ValueError('A batch needs completed source observations')
    return {'schema_version': 1, 'schema': SCHEMA, 'work': 'photius.bibliotheca',
        'batch_id': batch_id, 'reviewed_at': reviewed_at, 'input_corpus_sha256': sha(before),
        'source_table': table_pin, 'sources': [{'path': SCAN.as_posix(), 'sha256': SCAN_SHA},
            {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA}],
        'source_library_credit': deepcopy(source_credit),
        'records': sorted(records, key=lambda r: (r['locus'], r['start'])),
        'held_source_observations': deepcopy(list(held)), 'qualification': QUALIFICATION}


def _excluded(row):
    projection = row.get('historical_reading_batch_projection')
    if not projection:
        return []
    cursor = 0
    for span in projection['excluded_spans']:
        a, b = span['start'], span['end']
        if (type(a) is not int or type(b) is not int or not cursor <= a < b <= len(row['text'])
                or row['text'][a:b] != span['text']):
            raise ValueError('Historical batch lexical exclusion changed')
        cursor = b
    return deepcopy(projection['excluded_spans'])


def _segments(text, spans):
    cursor, result = 0, []
    for span in spans:
        result.append(text[cursor:span['start']]); cursor = span['end']
    result.append(text[cursor:])
    return result


def _whole_word_exclusions(text, spans):
    """Never count word fragments beside an unresolved intra-word correction."""
    def letter(char):
        return _word_character(char)
    result = []
    for source in sorted(spans, key=lambda s: s['start']):
        span = deepcopy(source); a, b = span['start'], span['end']
        while a and letter(text[a-1]):
            a -= 1
        while b < len(text) and letter(text[b]):
            b += 1
        span.update(start=a, end=b, text=text[a:b])
        if result and a <= result[-1]['end']:
            previous = result.pop()
            span.update(start=previous['start'], end=max(b, previous['end']))
            span['text'] = text[span['start']:span['end']]
            span['combined_evidence'] = previous.get('combined_evidence', [previous]) + [deepcopy(source)]
        result.append(span)
    return result


def _preserve_tail(old, new, decisions, networks, archive, reference):
    """Combine a reviewed prefix with the byte-identical earlier tail vote."""
    from ocr_consensus import compact_corpus_consensus
    if len(decisions) != 1 or not _prefix_scope(old, decisions[0]):
        raise ValueError('A prefix review cannot include another source range')
    item = decisions[0]
    prefix = networks[item['network_key']]
    tail = deepcopy(old['ocr_consensus']['span_networks']['replacement_tail'])
    boundary = len(old['source_body_correction']['retained_prefix'])
    separator = old['text'][item['end']:boundary]
    if (item['start'] != 0 or not separator.isspace()
            or new['text'] != prefix['text'] + separator + tail['text']):
        raise ValueError('Prefix review changed the independently merged ending')
    witnesses = prefix['ocr_consensus']['witnesses'] + tail['ocr_consensus']['witnesses']
    prefix_ids = {w['id'] for w in prefix['ocr_consensus']['witnesses']}
    tail_ids = {w['id'] for w in tail['ocr_consensus']['witnesses']}
    if prefix_ids & tail_ids:
        raise ValueError('Disjoint prefix and tail witnesses need distinct identities')
    slots = []
    for region, outside in ((prefix, tail_ids), (tail, prefix_ids)):
        for original in region['ocr_consensus']['slots']:
            slot = deepcopy(original)
            slot['position'] = len(slots)
            slot['abstentions'] = sorted(set(slot.get('abstentions', [])) | outside)
            slots.append(slot)
    full = {'text': new['text'],
        'analysis_text': ' '.join(s['selected'] for s in slots if s['lexical_eligible']),
        'ocr_consensus': {'schema_version': 1,
            'policy': 'Independently reviewed historical prefix followed by the unchanged earlier tail consensus. Disjoint source ranges align separately; superseded historical words cast no vote. Preserve every source disagreement.',
            'witnesses': witnesses, 'slots': slots,
            'counts': dict(Counter(s['status'] for s in slots)),
            'span_networks': {'reviewed_historical_prefix': deepcopy(prefix), 'replacement_tail': tail}}}
    key = old['locus'] + ':prefix-and-tail'
    networks[key] = full
    new.update(compact_corpus_consensus(full, {'path': archive.as_posix(), 'key': key}))
    new['historical_prefix_review'] = {'source_review': reference,
        'original_prefix_characters': boundary, 'retained_tail_sha256': sha(encode(tail)),
        'original_consensus': deepcopy(old['ocr_consensus']['full_network']),
        'qualification': 'Only the prefix is newly reviewed. The earlier tail network and all of its alternatives are unchanged.'}


def _slot_segments(row):
    runs, current = [], []
    for slot in row['ocr_consensus']['slots']:
        if slot['lexical_eligible']:
            current.append(slot['selected'])
        elif current:
            runs.append(' '.join(current)); current = []
    if current:
        runs.append(' '.join(current))
    return runs


def plan(before, review_raw):
    """Pure exact-span replay, including all prior partial-review metadata."""
    review = json.loads(review_raw)
    p = paths(review['batch_id'])
    if (review.get('schema') != SCHEMA or review.get('schema_version') != 1 or
            review.get('work') != 'photius.bibliotheca' or review.get('input_corpus_sha256') != sha(before)
            or not review.get('reviewed_at') or not review.get('records')):
        raise ValueError('Historical batch authority differs from its exact preimage')
    reference = {'path': p['review'].as_posix(), 'sha256': sha(review_raw)}
    grouped, changes, networks, output = {}, [], {}, []
    for item in review['records']:
        grouped.setdefault(item['locus'], []).append(item)
    for line in before.splitlines(keepends=True):
        old = json.loads(line); locus = old['locus']
        if locus not in grouped:
            output.append(line); continue
        prefix_scope = any(item.get('review_scope') == 'retained-historical-prefix' for item in grouped[locus])
        editorial_scope = any(item.get('review_scope') == 'retained-editorial-body' for item in grouped[locus])
        if prefix_scope and (len(grouped[locus]) != 1 or not _prefix_scope(old, grouped[locus][0])):
            raise ValueError('A prefix review requires one complete bounded source range')
        if editorial_scope and not all(_editorial_body_scope(old, item) for item in grouped[locus]):
            raise ValueError('Every editorial body occurrence requires its explicit retained scope')
        if not (prefix_scope or editorial_scope) and (old.get('ocr_consensus') or old.get('editorial_layer') or
                ('analysis_text' in old and not old.get('historical_reading_batch_projection'))):
            raise ValueError('A batch cannot overwrite an unrelated lexical projection')
        previous = old.get('historical_reading_batches', [])
        if any(t['batch_id'] == review['batch_id'] for t in previous):
            raise ValueError('A historical batch cannot be applied twice')
        exclusions = _excluded(old)
        items = sorted(grouped.pop(locus), key=lambda r: r['start'])
        cursor, text, length, mapped, decisions = 0, [], 0, [], []
        for index, item in enumerate(items):
            a, b = item['start'], item['end']
            source, digital = item['source'], item.get('digital_counterpart')
            projection_only = item.get('projection_only', False)
            if (type(projection_only) is not bool or type(a) is not int or type(b) is not int or not cursor <= a < b <= len(old['text'])
                    or old['text'][a:b] != item['original_text'] or row_sha(old) != item['original_row_sha256']
                    or not item['corrected_text'] or
                    (item['corrected_text'] == item['original_text']) != projection_only
                    or source.get('path') != SCAN.as_posix() or source.get('sha256') != SCAN_SHA
                    or not source.get('evidence') or not source.get('image_sha256') or not item.get('reviewed_at')):
                raise ValueError('Historical batch lacks its exact original or source evidence')
            _box(source['region'])
            if any(a < s['end'] and s['start'] < b for s in exclusions):
                raise ValueError('Re-review a prior unresolved reading explicitly before replacing it')
            if projection_only:
                context = item.get('digital_context')
                if (digital or not item.get('source_fragments') or (context and
                        (context.get('path') != LIBRARY.as_posix() or context.get('sha256') != LIBRARY_SHA
                         or context.get('role') != 'nonvoting-source-context' or not context.get('original_text')
                         or source['scan_page'] in {169, 170})) or
                        (not context and (not item.get('scan_only') or not item.get('qualification')))):
                    raise ValueError('Eligibility-only observation lacks its exact qualified nonvoting source context')
            elif item.get('scan_only'):
                if digital is not None or not item.get('qualification'):
                    raise ValueError('Scan-only source qualification is missing')
            elif (not digital or digital.get('path') != LIBRARY.as_posix() or
                    digital.get('sha256') != LIBRARY_SHA or not digital.get('original_text')
                    or source['scan_page'] in {169, 170}):
                raise ValueError('A bounded digital counterpart or qualified scan-only review is required')
            unchanged = old['text'][cursor:a]; text.append(unchanged); length += len(unchanged)
            replacement = item['corrected_text']
            contrary = bool(digital and digital['original_text'] != replacement)
            occurrence_exclusions = []
            if digital:
                from ocr_consensus import merge_witnesses
                scan_id = 'historical-prefix-scan' if prefix_scope else 'direct-scan-reading'
                digital_id = 'historical-prefix-digital' if prefix_scope else 'source-library-local002'
                full = merge_witnesses([
                    {'id': scan_id, 'vote_group': scan_id,
                     'text': replacement, 'artifact_sha256': sha(encode(source)),
                     'source': source, 'source_review': reference, 'license': 'CC-BY-4.0'},
                    {'id': digital_id, 'vote_group': digital_id,
                     'text': digital['original_text'], 'artifact_sha256': sha(encode(digital)),
                     'source_window': digital, 'license': 'CC-BY-SA-4.0'}])
                networks[f'{locus}:{index}'] = full
            if contrary:
                from photius_body_vote import _render_slots
                replacement = full['text']
                position = 0
                surfaces = []
                for slot in full['ocr_consensus']['slots']:
                    surface = _render_slots([slot])
                    if not surface:
                        continue
                    if surfaces:
                        position += 1
                    if not slot['lexical_eligible'] or '⟦' in surface:
                        occurrence_exclusions.append({'start': position, 'end': position+len(surface),
                            'text': surface, 'reason': 'contrary-source-readings',
                            'source_review': reference, 'network_key': f'{locus}:{index}',
                            'slot_position': slot['position']})
                    surfaces.append(surface); position += len(surface)
                if ' '.join(surfaces) != replacement:
                    raise ValueError('Historical occurrence network lost its exact rendered surfaces')
            fragments = item.get('source_fragments', [])
            if fragments != _fragments({'corrected_text': item['corrected_text'],
                    'evidence': source['evidence'], 'source_fragment': item.get('source_fragment', {})}):
                raise ValueError('Historical source fragment qualification changed')
            for fragment in fragments:
                if contrary:
                    selected = next(iter(_fragment_positions(full, [fragment])))
                    offset = 0
                    for i, slot in enumerate(full['ocr_consensus']['slots']):
                        surface = _render_slots([slot])
                        if not surface:
                            continue
                        if i == selected:
                            occurrence_exclusions.append({'start': offset, 'end': offset+len(surface),
                                'text': surface, 'reason': 'source-confirmed-word-fragment',
                                'source_fragment': fragment, 'source_review': reference})
                            break
                        offset += len(surface)+1
                else:
                    occurrence_exclusions.append({'start': fragment['start'], 'end': fragment['end'],
                        'text': fragment['text'], 'reason': 'source-confirmed-word-fragment',
                        'source_fragment': fragment, 'source_review': reference})
            if digital:
                _project_fragment_network(full, fragments, reference)
            for exclusion in occurrence_exclusions:
                mapped.append({**exclusion, 'start': length+exclusion['start'], 'end': length+exclusion['end']})
            decisions.append({**deepcopy(item), 'served_text': replacement,
                'disposition': 'source-reviewed-eligibility-only' if projection_only else
                    'unresolved-source-variants' if contrary else 'source-reviewed-scalar-occurrence',
                'rejected_historical_reading_votes': 0,
                **({'network_key': f'{locus}:{index}'} if digital else {})})
            text.append(replacement); length += len(replacement); cursor = b
        text.append(old['text'][cursor:]); corrected = ''.join(text)
        for span in exclusions:
            delta = sum(len(d['served_text'])-(d['end']-d['start']) for d in decisions if d['end'] <= span['start'])
            mapped.append({**span, 'start': span['start']+delta, 'end': span['end']+delta})
        mapped = _whole_word_exclusions(corrected, mapped)
        new = deepcopy(old)
        new.update(text=corrected, edition='bekker1825-reviewed-historical-readings',
                   license='CC-BY-SA-4.0', language='grc')
        if editorial_scope:
            new['analysis_text'] = corrected
        new['historical_reading_batches'] = previous + [{'schema': SCHEMA, 'batch_id': review['batch_id'],
            'source_review': reference, 'original_row_sha256': row_sha(old),
            'reviewed_occurrences': len(items),
            'unresolved_occurrences': sum(d['disposition'] == 'unresolved-source-variants' for d in decisions),
            'scalar_corrections': sum(d['disposition'] == 'source-reviewed-scalar-occurrence' for d in decisions),
            'fragment_occurrences': sum(bool(d.get('source_fragments')) for d in decisions),
            'lexical_excluded_fragments': sum(len(d.get('source_fragments', [])) for d in decisions),
            **({'projection_only_occurrences': sum(bool(d.get('projection_only')) for d in decisions)}
               if any(d.get('projection_only') for d in decisions) else {}),
            'qualification': QUALIFICATION}]
        if mapped:
            new['historical_reading_batch_projection'] = {'schema': SCHEMA, 'excluded_spans': mapped}
            new['analysis_text'] = ' '.join(_segments(corrected, mapped))
        if prefix_scope:
            _preserve_tail(old, new, decisions, networks, p['networks'], reference)
        changes.append({'locus': locus, 'original_row': old, 'corrected_row': new,
            'original_row_sha256': row_sha(old), 'corrected_row_sha256': row_sha(new),
            'original_text': old['text'], 'corrected_text': corrected,
            'corrections': decisions, 'source_review': reference, 'recorded_at': review['reviewed_at']})
        output.append((json.dumps(new, ensure_ascii=False)+'\n').encode())
    if grouped:
        raise ValueError('Historical batch invents a passage identity')
    counts = {'corrected_rows': len(changes), 'reviewed_occurrences': len(review['records']),
        'unresolved_occurrences': sum(d['disposition'] == 'unresolved-source-variants' for c in changes for d in c['corrections']),
        'scan_only_occurrences': sum(bool(d['scan_only']) for d in review['records']),
        'fully_assessed_rows': 0, 'primary_rows_before': len(before.splitlines()),
        'primary_rows_after': len(output), 'held_source_observations': len(review.get('held_source_observations', []))}
    projection_count = sum(bool(d.get('projection_only')) for d in review['records'])
    counts['scalar_corrections'] = counts['reviewed_occurrences'] - counts['unresolved_occurrences'] - projection_count
    if projection_count:
        counts['projection_only_occurrences'] = projection_count
        counts['text_changed_rows'] = sum(c['original_text'] != c['corrected_text'] for c in changes)
    counts['fragment_occurrences'] = sum(bool(d.get('source_fragments')) for d in review['records'])
    counts['lexical_excluded_fragments'] = sum(len(d.get('source_fragments', [])) for d in review['records'])
    return b''.join(output), changes, networks, counts


def _artifacts(before, review_raw, table_raw, predecessor=None):
    review = json.loads(review_raw); p = paths(review['batch_id'])
    if sha(table_raw) != review['source_table']['sha256']:
        raise ValueError('The frozen source table changed')
    module, _ = _table(table_raw, review['source_table']['path'])
    if module.BATCH_ID != review['batch_id'] or module.REVIEWED_AT != review['reviewed_at']:
        raise ValueError('The batch source identity or timestamp changed')
    after, changes, networks, counts = plan(before, review_raw)
    records = b''.join((json.dumps(c, ensure_ascii=False)+'\n').encode() for c in changes)
    frozen = {p['before']: gzip.compress(before, mtime=0), p['review']: review_raw, p['table']: table_raw}
    outputs = {p['records']: gzip.compress(records, mtime=0), p['networks']: gzip.compress(encode(networks), mtime=0)}
    audit = {'schema_version': 1, 'schema': SCHEMA, 'work': 'photius.bibliotheca',
        'batch_id': review['batch_id'], 'recorded_at': review['reviewed_at'],
        'input_corpus_sha256': sha(before), 'output_corpus_sha256': sha(after),
        'predecessor': predecessor, 'source_review': {'path': p['review'].as_posix(), 'sha256': sha(review_raw)},
        'source_table': review['source_table'], 'sources': review['sources'],
        'source_library_credit': review.get('source_library_credit'), 'counts': counts,
        'outputs': {path.as_posix(): sha(raw) for path, raw in outputs.items()},
        'frozen_inputs': {path.as_posix(): sha(raw) for path, raw in frozen.items()},
        'qualification': QUALIFICATION}
    return {CORPUS: after, **frozen, **outputs, p['audit']: encode(audit)}, audit


def _chain(root):
    root = Path(root); audits, by_input, cursor, chain = {}, {}, BASE_SHA, []
    for path in sorted((root / ARCHIVE).glob('*/changes.json')):
        raw = path.read_bytes(); audit = json.loads(raw)
        p = paths(audit['batch_id'])
        if path.relative_to(root) != p['audit'] or audit.get('schema') != SCHEMA:
            raise ValueError('Historical batch archive identity changed')
        if audit['input_corpus_sha256'] in by_input or audit['batch_id'] in audits:
            raise ValueError('Historical batch archives branch or repeat an identity')
        audits[audit['batch_id']] = (audit, raw)
        by_input[audit['input_corpus_sha256']] = audit['batch_id']
    while cursor in by_input:
        identity = by_input.pop(cursor); audit, raw = audits[identity]
        predecessor = None if not chain else {'batch_id': chain[-1][0]['batch_id'], 'sha256': sha(chain[-1][1])}
        if audit['predecessor'] != predecessor:
            raise ValueError('Historical batch predecessor pin changed')
        chain.append((audit, raw)); cursor = audit['output_corpus_sha256']
    if by_input:
        raise ValueError('Historical batch chain does not descend from the frozen release')
    return chain


def _active_chain(raw, chain):
    digest = sha(raw)
    if digest == BASE_SHA:
        return []
    for index, (audit, _) in enumerate(chain):
        if digest == audit['output_corpus_sha256']:
            return chain[:index+1]
    if any(json.loads(line).get('historical_reading_batches') for line in raw.splitlines()):
        raise ValueError('Historical batch postimage changed outside its audit')
    return []  # earlier legacy layers retain their own strict identity checks


def _validate_saved(root, audit, *, require_current=False):
    root = Path(root); p = paths(audit['batch_id'])
    before = gzip.decompress((root / p['before']).read_bytes())
    review_raw, table_raw = (root / p['review']).read_bytes(), (root / p['table']).read_bytes()
    artifacts, expected = _artifacts(before, review_raw, table_raw, audit['predecessor'])
    if expected != audit or any((root / path).read_bytes() != raw for path, raw in artifacts.items() if path != CORPUS):
        raise ValueError('Frozen historical batch no longer replays exactly')
    if require_current:
        pin = audit['source_table']; relative = Path(pin['path'])
        if relative not in {Path('scripts')/(name+'.py') for name in TABLES} or (root / relative).read_bytes() != table_raw:
            raise ValueError('The current historical source table changed or was removed')
        module, held = _table(table_raw, relative.as_posix())
        regenerated = compile_review(before, (root/LIBRARY).read_bytes(), (root/SCAN).read_bytes(),
            module.observations(), batch_id=module.BATCH_ID, reviewed_at=module.REVIEWED_AT,
            table_pin=pin, held=held, source_credit=_source_credit(root))
        if encode(regenerated) != review_raw:
            raise ValueError('The source-reviewed historical batch no longer reproduces')
    return artifacts


def build(root=ROOT, *, batch_id=None):
    """Plan a new batch, or replay an existing immutable batch, without writing."""
    root = Path(root); before = (root/CORPUS).read_bytes(); chain = _chain(root)
    if b'"complete_source_review"' in before:
        raise ValueError('Undo the complete-passage admission before appending an earlier occurrence layer')
    active = _active_chain(before, chain)
    for audit, _ in active:
        _validate_saved(root, audit, require_current=True)
    tables = catalog(root)
    if batch_id is None:
        batch_id = next((identity for identity in tables if identity not in {a['batch_id'] for a, _ in active}), None)
    if batch_id is None:
        raise ValueError('No unapplied completed source table is available')
    saved = next((a for a, _ in chain if a['batch_id'] == batch_id), None)
    if saved:
        artifacts = _validate_saved(root, saved, require_current=True)
        if sha(before) not in {saved['input_corpus_sha256'], saved['output_corpus_sha256']}:
            raise ValueError('Reapply or unapply batches in their exact original order')
        return artifacts, saved
    expected = active[-1][0]['output_corpus_sha256'] if active else BASE_SHA
    if sha(before) != expected or len(active) != len(chain):
        raise ValueError('New batches must append to the exact current chain tip')
    path, table_raw = tables[batch_id]; module, held = _table(table_raw, path.as_posix())
    review = compile_review(before, (root/LIBRARY).read_bytes(), (root/SCAN).read_bytes(),
        module.observations(), batch_id=batch_id, reviewed_at=module.REVIEWED_AT,
        table_pin={'path': path.as_posix(), 'sha256': sha(table_raw)}, held=held,
        source_credit=_source_credit(root))
    predecessor = None if not active else {'batch_id': active[-1][0]['batch_id'], 'sha256': sha(active[-1][1])}
    return _artifacts(before, encode(review), table_raw, predecessor)


def check(root=ROOT, *, require_current=True):
    root = Path(root); raw = (root/CORPUS).read_bytes(); chain = _chain(root)
    from repair_photius_complete_review import restore_before_bytes as restore_complete
    raw = restore_complete(raw, root)
    if require_current and chain and sha(raw) not in {BASE_SHA, *(a['output_corpus_sha256'] for a, _ in chain)}:
        raise ValueError('Current historical corpus is not an exact known batch stage')
    active = _active_chain(raw, chain)
    for audit, _ in active:
        _validate_saved(root, audit, require_current=require_current)
    return [audit for audit, _ in active]


def restore_before_bytes(raw, root=ROOT):
    """Verify later batches in memory, then expose the unchanged .4 postimage."""
    from repair_photius_complete_review import restore_before_bytes as restore_complete
    raw = restore_complete(raw, root)
    root = Path(root); active = _active_chain(raw, _chain(root))
    for audit, _ in reversed(active):
        artifacts = _validate_saved(root, audit)
        if raw != artifacts[CORPUS]:
            raise ValueError('Historical batch postimage differs from exact replay')
        raw = gzip.decompress(artifacts[paths(audit['batch_id'])['before']])
    return raw


@lru_cache(maxsize=32)
def _record_map(raw):
    return {r['locus']: r for r in map(json.loads, gzip.decompress(raw).splitlines())}


def restore_before_row(row, root=ROOT):
    """Check every exact row postimage before exposing its preceding .4 row."""
    from repair_photius_complete_review import restore_before_row as restore_complete
    row = restore_complete(row, root)
    current = deepcopy(row)
    for tag in reversed(row.get('historical_reading_batches', [])):
        p = paths(tag['batch_id']); audit_raw = (Path(root)/p['audit']).read_bytes()
        audit = json.loads(audit_raw); records = (Path(root)/p['records']).read_bytes()
        review_raw = (Path(root)/p['review']).read_bytes()
        if (audit.get('schema') != SCHEMA or audit['batch_id'] != tag['batch_id'] or
                sha(records) != audit['outputs'][p['records'].as_posix()] or
                sha(review_raw) != audit['source_review']['sha256'] or
                tag['source_review'] != audit['source_review']):
            raise ValueError('Historical row batch pins changed')
        change = _record_map(records).get(row['locus'])
        if (not change or current != change['corrected_row'] or row_sha(current) != change['corrected_row_sha256']
                or row_sha(change['original_row']) != change['original_row_sha256']
                or tag['original_row_sha256'] != change['original_row_sha256']):
            raise ValueError('Historical row differs from its exact batch postimage')
        current = deepcopy(change['original_row'])
    if current.get('historical_reading_batches'):
        raise ValueError('Historical row batch chain is incomplete')
    return current


def validate_projection(row, root=ROOT):
    if row.get('complete_source_review'):
        from repair_photius_complete_review import lexical_segments as complete_segments, restore_before_row as restore_complete_row
        complete_segments(row, root)
        row = restore_complete_row(row, root)
    if not row.get('historical_reading_batches'):
        raise ValueError('Historical projection lacks its batch references')
    restore_before_row(row, root)
    spans = _excluded(row)
    if row.get('historical_prefix_review'):
        expected = ' '.join(s['selected'] for s in row['ocr_consensus']['slots'] if s['lexical_eligible'])
        if row.get('analysis_text') != expected:
            raise ValueError('Historical prefix lexical projection changed')
        return
    if spans and row.get('analysis_text') != ' '.join(_segments(row['text'], spans)):
        raise ValueError('Historical batch lexical text changed')


def lexical_segments(row, root=ROOT):
    if row.get('complete_source_review'):
        from repair_photius_complete_review import lexical_segments as complete_segments
        return complete_segments(row, root)
    validate_projection(row, root)
    if row.get('historical_prefix_review'):
        return _slot_segments(row)
    return _segments(row['text'], _excluded(row))


def active_metadata(root=ROOT):
    from repair_photius_complete_review import restore_before_bytes as restore_complete
    root = Path(root); raw = restore_complete((root/CORPUS).read_bytes(), root)
    active = _active_chain(raw, _chain(root))
    if not active:
        return None
    audits = check(root)
    loci, newly, occurrences, unresolved, fragments, excluded, projection_only = set(), set(), 0, 0, 0, 0, 0
    for audit in audits:
        p = paths(audit['batch_id'])
        for change in _record_map((root/p['records']).read_bytes()).values():
            loci.add(change['locus'])
            old = change['original_row']
            if not old.get('historical_reading_repair') and not old.get('historical_reading_batches'):
                newly.add(change['locus'])
        occurrences += audit['counts']['reviewed_occurrences']
        unresolved += audit['counts']['unresolved_occurrences']
        fragments += audit['counts']['fragment_occurrences']
        excluded += audit['counts']['lexical_excluded_fragments']
        projection_only += audit['counts'].get('projection_only_occurrences', 0)
    return {'schema': SCHEMA, 'batches': [{'audit': {'path': paths(a['batch_id'])['audit'].as_posix(),
                'sha256': sha(raw)}, 'source_review': a['source_review'], 'counts': a['counts']} for a, raw in active],
        'counts': {'batches': len(audits), 'unique_corrected_rows': len(loci),
            'newly_corrected_rows': len(newly), 'previously_corrected_rows': len(loci-newly),
            'reviewed_occurrences': occurrences, 'scalar_corrections': occurrences-unresolved-projection_only,
            **({'projection_only_occurrences': projection_only} if projection_only else {}),
            'fragment_occurrences': fragments, 'lexical_excluded_fragments': excluded,
            'unresolved_occurrences': unresolved, 'fully_assessed_rows': 0},
        'corrected_loci': sorted(loci), 'newly_corrected_loci': sorted(newly), 'qualification': QUALIFICATION}


def apply(root=ROOT, *, batch_id=None):
    root = Path(root); artifacts, audit = build(root, batch_id=batch_id)
    for path, raw in artifacts.items():
        if path != CORPUS and (root/path).exists() and (root/path).read_bytes() != raw:
            raise ValueError('Refusing to overwrite an immutable historical batch artifact')
    for path, raw in artifacts.items():
        if path == CORPUS:
            continue
        (root/path).parent.mkdir(parents=True, exist_ok=True); (root/path).write_bytes(raw)
    (root/CORPUS).write_bytes(artifacts[CORPUS])
    return audit


def undo(root=ROOT):
    root = Path(root); raw = (root/CORPUS).read_bytes(); active = _active_chain(raw, _chain(root))
    if not active:
        raise ValueError('No historical batch is currently applied')
    audit = active[-1][0]; artifacts = _validate_saved(root, audit)
    if artifacts[CORPUS] != raw:
        raise ValueError('Cannot unapply an independently changed historical row')
    (root/CORPUS).write_bytes(gzip.decompress(artifacts[paths(audit['batch_id'])['before']]))
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    for name in ('apply', 'check', 'undo'):
        action.add_argument('--'+name, action='store_true')
    parser.add_argument('--batch'); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = (apply(args.root, batch_id=args.batch) if args.apply else undo(args.root) if args.undo
              else check(args.root) if args.check else build(args.root, batch_id=args.batch)[1])
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
