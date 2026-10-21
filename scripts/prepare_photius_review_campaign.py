#!/usr/bin/env python3
"""Freeze and validate complete-passage source reviews of historical Photius.

This is a review accounting gate, not a corpus admission command. A digital
match, successful OCR run, or occurrence correction cannot certify a passage.
Reviewers must account for every original Unicode codepoint, including unchanged
text, with explicit observations of pinned source crops. Uncertain readings and
printed word fragments remain explicit. The frozen rows and exact segment
preimages support reversal without any source files.

The validator checks recorded observations and coverage. It cannot establish that
someone actually inspected an image; that remains the responsibility of the
source reviewer making the direct-scan-inspection attestation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from assess_photius_historical import MAPPING_EXCEPTIONS, PAGE, SECTION_PREFIX, tokens, _key, _local_alignment
from prepare_photius_historical_readings import (
    CORPUS, LIBRARY, LIBRARY_SHA, ROOT, SCAN, SCAN_SHA, row_sha,
)

SCHEMA = 'photius-complete-passage-campaign-v1'
REVIEW_SCHEMA = 'photius-complete-passage-review-v1'
COMPILED_SCHEMA = 'photius-complete-passage-review-compiled-v1'
ORIGINAL = Path('data/corpus_changes/photius-bekker-index/before.jsonl.gz')
ORIGINAL_SHA = '95f5814a95ac9c0b26010c624dc605248f1937868d9fe1e15178ab6cd9f0ee68'
COVERAGE = Path('data/corpus_changes/photius-bekker-coverage/coverage.json')
ARCHIVE = Path('data/corpus_changes/photius-bekker-complete-review')
BASELINE = ARCHIVE / 'before-corpus.jsonl.gz'
MANIFEST = ARCHIVE / 'scope.json'
REVIEWS = ARCHIVE / 'source-review.json.gz'
OUT = ARCHIVE / 'review-status.json.gz'
SUMMARY = Path('data/audits/photius-complete-source-review.json')
EXPECTED_ROW_COUNT = 3462
EXPECTED_PAGES = tuple(range(2, 102)) + tuple(range(145, 281))
STATUSES = {'unreviewed', 'reviewed-with-uncertainty', 'reviewed-verified'}
MAX_SIDE = 3600


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def artifact_bytes(path, value):
    raw = encode(value)
    return gzip.compress(raw, mtime=0) if Path(path).suffix == '.gz' else raw


def decoded_bytes(path, raw):
    return gzip.decompress(raw) if Path(path).suffix == '.gz' else raw


def _text(value, name, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f'{name} must be explicit text')
    return value


def _timestamp(value):
    _text(value, 'Review timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Review timestamp must be an ISO8601 UTC timestamp') from exc
    if 'T' not in value or parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError('Review timestamp must be an ISO8601 UTC timestamp')
    return value


def _rows(raw):
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len({r['locus'] for r in rows}) != len(rows):
        raise ValueError('Corpus repeats a passage identity')
    return rows


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', value):
        raise ValueError('Campaign requires a safe stable identifier')
    return value


def _keys(value, allowed, label):
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError(f'{label} contains unknown fields or is not an object')


def _artifact_pin(value, evidence_files):
    _keys(value, {'path', 'sha256'}, 'Source artifact pin')
    path = value.get('path', '')
    if (not isinstance(path, str) or not path or Path(path).is_absolute()
            or '..' in Path(path).parts or path not in evidence_files):
        raise ValueError('A source reading or table requires a supplied repository-relative frozen artifact')
    raw = evidence_files[path]
    if value.get('sha256') != sha(raw):
        raise ValueError('A recorded source artifact changed')
    return raw


def _pin(path, raw):
    return {'path': path.as_posix(), 'sha256': sha(raw)}


def _sources(scan_raw, library_raw, original_raw, coverage_raw):
    original = gzip.decompress(original_raw)
    if sha(scan_raw) != SCAN_SHA or sha(library_raw) != LIBRARY_SHA or sha(original) != ORIGINAL_SHA:
        raise ValueError('Campaign requires the exact pinned scan, digital archive, and original corpus')
    library = json.loads(gzip.decompress(library_raw))
    if library.get('id') != 'tlg4040.tlg001.local002':
        raise ValueError('Campaign digital archive has a different edition identity')
    sections = {s['id']: '\n'.join(b['text'] for b in s['blocks']) for s in library['sections']}
    if len(sections) != len(library['sections']):
        raise ValueError('Digital archive repeats a section identity')
    coverage = json.loads(coverage_raw)
    credit = coverage['source_library']
    exceptions = {e['retained_legacy_scan_page']: e for e in coverage['source_scan_exceptions']}
    if (credit['sha256'] != LIBRARY_SHA or credit['edition'] != library['id']
            or credit['license']['url'] != 'https://creativecommons.org/licenses/by-sa/4.0/'
            or coverage['legacy_source']['sha256'] != SCAN_SHA
            or len(exceptions) != len(coverage['source_scan_exceptions'])
            or set(exceptions) != set(MAPPING_EXCEPTIONS)
            or any(exceptions[p]['authorial_printed_page'] != v['authorial_printed_page']
                   or exceptions[p]['combined_scan_printed_page'] != v['digital_scan_printed_page']
                   or exceptions[p]['logical_combined_position'] != p + 277
                   or exceptions[p]['source']['sha256'] != SCAN_SHA
                   for p, v in MAPPING_EXCEPTIONS.items())):
        raise ValueError('Campaign source credit or known page mapping exceptions changed')
    return original, sections, credit


def freeze_scope(corpus_raw, scan_raw, library_raw, original_raw, coverage_raw, *,
                 campaign_id, created_at, baseline_commit, frozen_corpus_raw=None):
    """Freeze all retained historical rows, without assigning completed reviews.

    Full immutable original rows make later undo independent of source access.
    Selection and expected accounting are the same historical scope as the
    diagnostic comparison; the diagnostic classifications confer no status.
    """
    _identifier(campaign_id)
    _timestamp(created_at)
    if not isinstance(baseline_commit, str) or not re.fullmatch(r'[0-9a-f]{40}', baseline_commit):
        raise ValueError('Campaign requires the exact baseline Git commit')
    original_raw_text, sections, credit = _sources(scan_raw, library_raw, original_raw, coverage_raw)
    frozen_corpus_raw = (gzip.compress(corpus_raw, mtime=0)
                         if frozen_corpus_raw is None else frozen_corpus_raw)
    if gzip.decompress(frozen_corpus_raw) != corpus_raw:
        raise ValueError('Frozen baseline archive does not restore the exact input corpus bytes')
    originals = {r['locus']: r for r in _rows(original_raw_text)}
    selected = []
    for row in _rows(corpus_raw):
        match = PAGE.fullmatch(row.get('locus', ''))
        if not match or row.get('ocr_consensus'):
            continue
        if row.get('urn') != 'photius.bibliotheca' or not isinstance(row.get('text'), str) or not row['text']:
            raise ValueError('Historical scope requires an unchanged Photius passage identity and nonempty text')
        if row['locus'] not in originals:
            raise ValueError('A retained historical passage is absent from the immutable original corpus')
        page, number = int(match[1]), int(match[2])
        section = SECTION_PREFIX + str(page + 277)
        if page not in MAPPING_EXCEPTIONS and section not in sections:
            raise ValueError('A retained passage has no expected pinned digital section')
        selected.append((page, number, {
            'locus': row['locus'], 'physical_page': page, 'printed_page': page + 265,
            'original_row_sha256': row_sha(row), 'original_text_sha256': sha(row['text'].encode()),
            'original_legacy_row_sha256': row_sha(originals[row['locus']]),
            'original_row': deepcopy(row), 'characters': len(row['text']),
            'lexical_tokens': len(tokens(row['text'])), 'status': 'unreviewed',
            'digital_section': section,
            'digital_counterparts_usable': page not in MAPPING_EXCEPTIONS,
            **({'source_mapping_exception': deepcopy(MAPPING_EXCEPTIONS[page])}
               if page in MAPPING_EXCEPTIONS else {}),
        }))
    selected.sort(key=lambda entry: entry[:2])
    rows = [entry[2] for entry in selected]
    pages = sorted({r['physical_page'] for r in rows})
    if len(rows) != EXPECTED_ROW_COUNT or pages != list(EXPECTED_PAGES):
        raise ValueError('Historical campaign scope differs from the frozen 3462 passages on236 source pages')
    return {
        'schema_version': 1, 'schema': SCHEMA, 'work': 'photius.bibliotheca',
        'campaign_id': campaign_id, 'created_at': created_at, 'baseline_commit': baseline_commit,
        'admission_authorized': False,
        'qualification': 'A frozen scope is unreviewed. Only explicitly recorded direct scan inspection can account for source review; digital agreement and OCR completion never certify text.',
        'input_pins': {'corpus': _pin(CORPUS, corpus_raw), 'scan': _pin(SCAN, scan_raw),
            'frozen_corpus': {**_pin(BASELINE, frozen_corpus_raw), 'uncompressed_sha256': sha(corpus_raw)},
            'digital_archive': _pin(LIBRARY, library_raw),
            'original_corpus': {**_pin(ORIGINAL, original_raw), 'uncompressed_sha256': sha(original_raw_text)},
            'source_mapping_review': _pin(COVERAGE, coverage_raw)},
        'source_library_credit': deepcopy(credit),
        'scope': {'passages': len(rows), 'physical_pages': pages, 'pages': len(pages),
            'characters': sum(r['characters'] for r in rows),
            'lexical_tokens': sum(r['lexical_tokens'] for r in rows)},
        'rows': rows,
    }


def validate_scope(manifest, corpus_raw, scan_raw, library_raw, original_raw, coverage_raw, *,
                   frozen_corpus_raw=None):
    expected = freeze_scope(corpus_raw, scan_raw, library_raw, original_raw, coverage_raw,
        campaign_id=manifest['campaign_id'], created_at=manifest['created_at'],
        baseline_commit=manifest['baseline_commit'], frozen_corpus_raw=frozen_corpus_raw)
    if canonical(manifest) != canonical(expected):
        raise ValueError('Frozen campaign scope, source pins, or exact row preimages changed')


def _box(value):
    if (not isinstance(value, list) or len(value) != 4
            or any(type(n) not in (int, float) or not math.isfinite(n) for n in value)
            or not 0 <= value[0] < value[2] <= 1 or not 0 <= value[1] < value[3] <= 1):
        raise ValueError('A scan review needs a finite normalized source rectangle')
    return value


_CROP_CACHE_DOCUMENT = None
_CROP_CACHE = {}


def crop_png(document, page, region):
    """Use the existing historical batch crop convention, with one-based pages."""
    import pymupdf
    if type(page) is not int or not 1 <= page <= len(document):
        raise ValueError('A scan review requires an existing physical PDF page')
    box = _box(region)
    # Many independently pinned passages share one source rectangle. Only the
    # most recently used document can own cached pixels. An identity comparison
    # prevents reuse across source files, even if their page geometry agrees.
    global _CROP_CACHE_DOCUMENT
    if _CROP_CACHE_DOCUMENT is not document:
        _CROP_CACHE.clear()
        _CROP_CACHE_DOCUMENT = document
    cache = _CROP_CACHE
    key = (page, tuple(box), MAX_SIDE)
    if key in cache:
        return cache[key]
    sheet = document[page - 1]
    rect = pymupdf.Rect(box[0] * sheet.rect.width, box[1] * sheet.rect.height,
                       box[2] * sheet.rect.width, box[3] * sheet.rect.height)
    scale = MAX_SIDE / max(rect.width, rect.height)
    raw = sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False).tobytes('png')
    if len(cache) >= 128:
        cache.pop(next(iter(cache)))
    cache[key] = raw
    return raw


def _span(full, start, end, text, label):
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(full)
            or not isinstance(text, str) or full[start:end] != text):
        raise ValueError(f'{label} has a changed or invalid exact Unicode span')


def _digital_reading(value, frozen, sections, observed):
    _keys(value, {'kind', 'text', 'section', 'start', 'end', 'review_span',
                  'may_be_unaligned'}, 'Digital reading')
    if not frozen['digital_counterparts_usable']:
        raise ValueError('The expected digital windows for physical169/170 repeat unrelated pages')
    if value.get('section') != frozen['digital_section']:
        raise ValueError('A digital reading must address the exact expected source section')
    full = sections[value['section']]
    _span(full, value.get('start'), value.get('end'), value.get('text'), 'Digital reading')
    if 'review_span' in value:
        span = value['review_span']
        _keys(span, {'start', 'end', 'text'}, 'Reviewed token counterpart')
        _span(observed, span.get('start'), span.get('end'), span.get('text'), 'Reviewed token counterpart')
        if type(value.get('may_be_unaligned')) is not bool:
            raise ValueError('A token counterpart must retain its unmatched-path status')
    elif 'may_be_unaligned' in value:
        raise ValueError('An unmatched-path flag requires its exact reviewed token span')
    return {**deepcopy(value), 'source': {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA},
            'role': 'recorded-source-reading'}


def _digital_alignment(value, observed, readings, frozen, sections):
    """Verify all candidate edges and gaps without converting comparison to review."""
    if not frozen['digital_counterparts_usable'] or value.get('section') != frozen['digital_section']:
        raise ValueError('Diagnostic token alignment requires the exact usable digital page')
    _keys(value, {'section', 'tokens', 'ambiguous', 'aligned', 'cost'}, 'Diagnostic token alignment')
    old = tokens(observed)
    digital = tokens(sections[value['section']])
    if not old or not digital:
        raise ValueError('A diagnostic token alignment requires nonempty Greek token sequences')
    alignment = _local_alignment([_key(t['text']) for t in old], [_key(t['text']) for t in digital])
    expected = {'section': value['section'], 'tokens': [
        {**token, 'may_be_unaligned': alignment['may_be_unaligned'][i],
         'counterpart_count': len(alignment['counterparts'][i])}
        for i, token in enumerate(old)],
        **{key: alignment[key] for key in ('ambiguous', 'aligned', 'cost')}}
    # following_hyphen belongs to the literal token, but the edge table uses only
    # exact lexical spans; fragment eligibility remains independently reviewed.
    for token in expected['tokens']:
        token.pop('following_hyphen', None)
    if canonical(value) != canonical(expected):
        raise ValueError('Diagnostic token alignment changed or omitted gaps and tied counterparts')
    expected_edges = []
    for i, source in enumerate(old):
        for j in alignment['counterparts'][i]:
            target = digital[j]
            expected_edges.append((source['start'], source['end'], source['text'],
                target['start'], target['end'], target['text'], alignment['may_be_unaligned'][i]))
    actual_edges = []
    for reading in readings:
        if reading.get('kind') != 'digital':
            continue
        span = reading.get('review_span')
        if span is None:
            raise ValueError('Aligned token readings must preserve each reviewed token edge')
        actual_edges.append((span['start'], span['end'], span['text'], reading['start'],
                             reading['end'], reading['text'], reading['may_be_unaligned']))
    if sorted(actual_edges) != sorted(expected_edges):
        raise ValueError('Digital token readings dropped, repeated, or changed optimal counterpart edges')
    return {**deepcopy(value), 'admission_authorized': False,
            'qualification': 'All optimal diagnostic token counterparts are retained; character similarity does not certify a source reading.'}


def _ocr_reading(value, evidence_files):
    """Resolve an exact JSON string/span in an explicitly supplied frozen file."""
    _keys(value, {'kind', 'text', 'artifact', 'json_pointer', 'start', 'end'}, 'OCR reading')
    raw = _artifact_pin(value.get('artifact', {}), evidence_files)
    pointer = value.get('json_pointer')
    if not isinstance(pointer, list) or not pointer:
        raise ValueError('An OCR reading needs its exact JSON pointer')
    selected = json.loads(raw)
    try:
        for component in pointer:
            if not (type(component) is int or isinstance(component, str)):
                raise ValueError('Invalid OCR JSON pointer component')
            selected = selected[component]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError('The recorded OCR JSON pointer changed') from exc
    if not isinstance(selected, str):
        raise ValueError('An OCR pointer must identify the original prediction string')
    _span(selected, value.get('start'), value.get('end'), value.get('text'), 'OCR reading')
    return {**deepcopy(value), 'role': 'recorded-source-reading'}


def _fragments(value, corrected):
    if not isinstance(value, list):
        raise ValueError('Source fragments must be explicit span records')
    result, cursor = [], 0
    words = tokens(corrected)
    for fragment in value:
        _keys(fragment, {'start', 'end', 'text', 'side', 'qualification'}, 'Printed word fragment')
        a, b, text = fragment.get('start'), fragment.get('end'), fragment.get('text')
        _span(corrected, a, b, text, 'Printed word fragment')
        if a < cursor or fragment.get('side') not in {'leading', 'trailing', 'internal'}:
            raise ValueError('Printed word fragments overlap or have no explicit side')
        matching = [word for word in words if word['start'] == a and
                    b == word.get('following_hyphen', {}).get('end', word['end'])]
        if len(matching) != 1:
            raise ValueError('A printed fragment must exclude one exact Greek token, including its hyphen')
        if ((fragment['side'] == 'leading' and matching[0] != words[0]) or
                (fragment['side'] == 'trailing' and matching[0] != words[-1])):
            raise ValueError('A leading or trailing fragment must address the source segment boundary')
        _text(fragment.get('qualification'), 'Printed fragment qualification')
        fragment_words = tokens(text)
        if (len(fragment_words) != 1 or fragment_words[0]['start'] != 0
                or (fragment_words[0].get('following_hyphen', {}).get('end', fragment_words[0]['end']) != len(text))):
            raise ValueError('A printed word fragment must exclude one exact Greek token, including its hyphen')
        result.append({**deepcopy(fragment), 'lexical_eligible': False,
            'classification': 'source-confirmed-word-fragment'})
        cursor = b
    # A terminal printed hyphen cannot silently become a complete lexical form.
    if words and words[-1].get('following_hyphen') and not corrected[words[-1]['end'] + 1:].strip():
        start, end = words[-1]['start'], words[-1]['end'] + 1
        if not any(f['start'] <= start and f['end'] >= end for f in result):
            raise ValueError('A terminal printed Greek word fragment needs an explicit lexical exclusion')
    return result


def _compile_segment(value, frozen, sections, document, images, evidence_files):
    _keys(value, {'start', 'end', 'original_text', 'corrected_text', 'verification',
        'review_basis', 'reviewed_at', 'evidence', 'scan', 'readings', 'fragments',
        'uncertainty', 'transcription_convention', 'digital_alignment', 'text_role'}, 'Source review segment')
    segment = deepcopy(value)
    original = frozen['original_row']['text']
    _span(original, segment.get('start'), segment.get('end'), segment.get('original_text'), 'Review segment')
    _text(segment.get('corrected_text'), 'Corrected text', empty=True)
    _timestamp(segment.get('reviewed_at'))
    _text(segment.get('evidence'), 'Direct scan evidence')
    if segment.get('review_basis') != 'direct-scan-inspection':
        raise ValueError('Digital comparison and finished OCR cannot certify direct source review')
    verification = segment.get('verification')
    if verification not in {'verified', 'uncertain'}:
        raise ValueError('A reviewed segment needs an explicit verification or uncertainty status')
    scan = segment.get('scan', {})
    _keys(scan, {'physical_page', 'region', 'image_sha256', 'observed_text', 'max_side'}, 'Scan observation')
    if scan.get('max_side', MAX_SIDE) != MAX_SIDE:
        raise ValueError('Scan observations must use the pinned3600pixel maximum crop dimension')
    if scan.get('physical_page') != frozen['physical_page']:
        raise ValueError('A source crop must belong to the passage physical page')
    region = _box(scan.get('region'))
    observed = _text(scan.get('observed_text'), 'Literal scan observation', empty=True)
    key = scan['physical_page'], tuple(region)
    if key not in images:
        images[key] = sha(crop_png(document, key[0], region))
    if scan.get('image_sha256') != images[key]:
        raise ValueError('A reviewed source crop image changed')
    if verification == 'verified':
        if segment.get('uncertainty'):
            raise ValueError('An explicitly uncertain source segment cannot be called verified')
        if observed != segment['corrected_text']:
            _text(segment.get('transcription_convention'), 'Differing literal scan transcription convention')
    else:
        _text(segment.get('uncertainty'), 'Source uncertainty')
        if segment['corrected_text'] != segment['original_text']:
            raise ValueError('An unresolved source reading must retain its original display and all alternatives')
    readings = [
        {'kind': 'original', 'text': segment['original_text'], 'source_row_sha256': frozen['original_row_sha256']},
        {'kind': 'direct-scan', 'text': observed, 'source': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA},
         'physical_page': frozen['physical_page'], 'region': region, 'image_sha256': images[key]},
    ]
    supplied_readings = segment.get('readings', [])
    if not isinstance(supplied_readings, list):
        raise ValueError('Alternative readings must remain an explicit list')
    for reading in supplied_readings:
        if reading.get('kind') == 'digital':
            readings.append(_digital_reading(reading, frozen, sections, observed))
        elif reading.get('kind') == 'ocr':
            readings.append(_ocr_reading(reading, evidence_files))
        else:
            raise ValueError('Additional source readings need an exact digital or frozen OCR pointer')
    segment['readings'] = readings
    if 'digital_alignment' in segment:
        segment['digital_alignment'] = _digital_alignment(segment['digital_alignment'], observed,
            supplied_readings, frozen, sections)
    elif any('review_span' in reading for reading in supplied_readings):
        raise ValueError('Token counterpart edges require their complete alignment accounting')
    role = segment.get('text_role', 'authorial-body')
    if role not in {'authorial-body', 'unclassified-small-type', 'unclassified-heading', 'editorial-note',
                    'marginal-reference', 'duplicate-heading'}:
        raise ValueError('A source review has an unknown text role')
    segment['text_role'] = role
    segment['scan'] = {**scan, 'source': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA},
                       'printed_page': frozen['printed_page'], 'max_side': MAX_SIDE}
    segment['fragments'] = _fragments(segment.get('fragments', []), segment['corrected_text'])
    return segment


def _compile_row(value, frozen, sections, document, images, evidence_files):
    _keys(value, {'locus', 'original_row_sha256', 'status', 'segments'}, 'Passage source review')
    if value.get('original_row_sha256') != frozen['original_row_sha256']:
        raise ValueError('Reviewed passage differs from its frozen original row')
    if value.get('status') not in STATUSES or not isinstance(value.get('segments'), list):
        raise ValueError('A review requires an explicit passage status and segment list')
    original = frozen['original_row']['text']
    segments, cursor, corrected_cursor, pieces, exclusions, uncertainties, nonbody = [], 0, 0, [], [], [], []
    for raw_segment in value['segments']:
        segment = _compile_segment(raw_segment, frozen, sections, document, images, evidence_files)
        if segment['start'] < cursor:
            raise ValueError('Reviewed source segments overlap, repeat, or are not in original source order')
        gap = original[cursor:segment['start']]
        pieces.extend((gap, segment['corrected_text']))
        corrected_cursor += len(gap)
        segment['corrected_start'] = corrected_cursor
        segment['corrected_end'] = corrected_cursor + len(segment['corrected_text'])
        for fragment in segment['fragments']:
            exclusions.append({**deepcopy(fragment), 'start': corrected_cursor + fragment['start'],
                               'end': corrected_cursor + fragment['end']})
        corrected_cursor = segment['corrected_end']
        if segment['text_role'] != 'authorial-body':
            nonbody.append({'start': segment['corrected_start'], 'end': segment['corrected_end'],
                'text': segment['corrected_text'], 'text_role': segment['text_role'],
                'lexical_eligible': False, 'evidence': segment['evidence'],
                'qualification': 'Source review does not admit this material as authorial lexical evidence.'})
        cursor = segment['end']
        segments.append(segment)
    pieces.append(original[cursor:])
    corrected = ''.join(pieces)
    for segment in segments:
        if segment['verification'] == 'uncertain':
            a, b = segment['corrected_start'], segment['corrected_end']
            # Expand uncertain intra-word source spans to complete raw words.
            # Downstream consumers must keep these as separate lexical segments;
            # concatenation across a gap would invent adjacency or join words.
            def word_character(char):
                return unicodedata.category(char)[0] in {'L', 'M'} or char in "’'ʼ᾽"
            while a and a < len(corrected) and word_character(corrected[a]) and word_character(corrected[a - 1]):
                a -= 1
            while b and b < len(corrected) and word_character(corrected[b - 1]) and word_character(corrected[b]):
                b += 1
            uncertainties.append({'start': a, 'end': b, 'text': corrected[a:b],
                'lexical_eligible': False, 'classification': 'unresolved-source-reading',
                'qualification': segment['uncertainty'], 'evidence': segment['evidence']})
    covered = sum(s['end'] - s['start'] for s in segments)
    complete = covered == len(original)
    status = ('reviewed-with-uncertainty' if any(s['verification'] == 'uncertain' for s in segments)
              else 'reviewed-verified') if complete else 'unreviewed'
    if value['status'] != status:
        raise ValueError('Passage status disagrees with exact character coverage or explicit source uncertainties')
    reviewed_tokens = sum(sum(max(0, min(t['end'], s['end']) - max(t['start'], s['start']))
                              for s in segments) == t['end'] - t['start'] for t in tokens(original))
    record = {
        'locus': frozen['locus'], 'original_row_sha256': frozen['original_row_sha256'],
        'physical_page': frozen['physical_page'], 'printed_page': frozen['printed_page'],
        'status': status, 'complete': complete, 'complete_scan_review': complete,
        'original_text': original, 'corrected_text': corrected,
        'original_text_sha256': sha(original.encode()), 'corrected_text_sha256': sha(corrected.encode()),
        'reviewed_characters': covered, 'characters': len(original),
        'reviewed_lexical_tokens': reviewed_tokens, 'lexical_tokens': len(tokens(original)),
        'segments': segments, 'additional_lexical_exclusions': exclusions,
        'uncertainty_exclusion_candidates': uncertainties,
        'nonbody_exclusion_candidates': nonbody,
    }
    if restore_text(record, corrected) != original:
        raise ValueError('Reviewed passage does not reverse to its exact original text')
    return record


def replay_text(record, original_text):
    """Replay exact reviewed spans. This does not authorize corpus admission."""
    if sha(original_text.encode()) != record['original_text_sha256'] or original_text != record['original_text']:
        raise ValueError('The original passage text changed before review replay')
    pieces, cursor = [], 0
    for segment in record['segments']:
        _span(original_text, segment['start'], segment['end'], segment['original_text'], 'Review replay')
        if segment['start'] < cursor:
            raise ValueError('Review replay spans overlap')
        pieces.extend((original_text[cursor:segment['start']], segment['corrected_text']))
        cursor = segment['end']
    pieces.append(original_text[cursor:])
    result = ''.join(pieces)
    if result != record['corrected_text'] or sha(result.encode()) != record['corrected_text_sha256']:
        raise ValueError('Review replay no longer reproduces the exact corrected text')
    return result


def restore_text(record, corrected_text):
    """Unapply a compiled review with no scan, digital archive, or live corpus."""
    if corrected_text != record['corrected_text'] or sha(corrected_text.encode()) != record['corrected_text_sha256']:
        raise ValueError('The corrected passage changed before exact review undo')
    pieces, cursor = [], 0
    for segment in record['segments']:
        a, b = segment['corrected_start'], segment['corrected_end']
        # Deletion of a reviewed artifact is a valid empty replacement.
        if (type(a) is not int or type(b) is not int or not cursor <= a <= b <= len(corrected_text)
                or corrected_text[a:b] != segment['corrected_text']):
            raise ValueError('Review undo has a changed corrected Unicode span')
        pieces.extend((corrected_text[cursor:a], segment['original_text']))
        cursor = b
    pieces.append(corrected_text[cursor:])
    result = ''.join(pieces)
    if result != record['original_text'] or sha(result.encode()) != record['original_text_sha256']:
        raise ValueError('Review undo no longer restores the exact original text')
    return result


def restore_original_row(manifest, locus):
    """Return the full frozen preimage, including every earlier audit layer."""
    matches = [r for r in manifest['rows'] if r['locus'] == locus]
    if len(matches) != 1 or row_sha(matches[0]['original_row']) != matches[0]['original_row_sha256']:
        raise ValueError('The frozen campaign passage preimage is missing, repeated, or changed')
    return deepcopy(matches[0]['original_row'])


def compile_campaign(manifest, reviews, corpus_raw, scan_raw, library_raw, original_raw,
                     coverage_raw, *, evidence_files=None, frozen_corpus_raw=None):
    """Validate direct observations and distinguish partial from complete scope.

    Unlisted passages remain unreviewed. A claimed completed passage must cover
    all characters exactly once; whitespace and unchanged text cannot be skipped.
    The output retains contradictory readings, not an arbitrarily selected vote.
    """
    validate_scope(manifest, corpus_raw, scan_raw, library_raw, original_raw, coverage_raw,
                   frozen_corpus_raw=frozen_corpus_raw)
    _keys(reviews, {'schema', 'campaign_id', 'records', 'source_tables'}, 'Campaign source reviews')
    if reviews.get('schema') != REVIEW_SCHEMA or reviews.get('campaign_id') != manifest['campaign_id']:
        raise ValueError('Source reviews belong to a different campaign schema or identity')
    supplied = reviews.get('records')
    if not isinstance(supplied, list):
        raise ValueError('Campaign source reviews need an explicit records list')
    by_locus = {r['locus']: r for r in supplied}
    scope = {r['locus'] for r in manifest['rows']}
    if len(by_locus) != len(supplied) or set(by_locus) - scope:
        raise ValueError('Campaign source reviews repeat a passage or include one outside the frozen scope')
    source_tables = reviews.get('source_tables', [])
    if not isinstance(source_tables, list):
        raise ValueError('Source tables require an explicit list of exact artifact pins')
    for pin in source_tables:
        _artifact_pin(pin, evidence_files or {})
    if len({p['path'] for p in source_tables}) != len(source_tables):
        raise ValueError('Campaign source table pins repeat an artifact')
    _, sections, _ = _sources(scan_raw, library_raw, original_raw, coverage_raw)
    import pymupdf
    rows, images = [], {}
    with pymupdf.open(stream=scan_raw, filetype='pdf') as document:
        for frozen in manifest['rows']:
            review = by_locus.get(frozen['locus'], {
                'original_row_sha256': frozen['original_row_sha256'], 'status': 'unreviewed', 'segments': []})
            rows.append(_compile_row(review, frozen, sections, document, images, evidence_files or {}))
    statuses = Counter(r['status'] for r in rows)
    complete = sum(r['complete'] for r in rows)
    pages_complete = [page for page in manifest['scope']['physical_pages']
                      if all(r['complete'] for r in rows if r['physical_page'] == page)]
    return {
        'schema_version': 1, 'schema': COMPILED_SCHEMA, 'work': manifest['work'],
        'campaign_id': manifest['campaign_id'], 'manifest_sha256': sha(canonical(manifest)),
        'source_reviews_sha256': sha(canonical(reviews)), 'input_pins': deepcopy(manifest['input_pins']),
        'source_library_credit': deepcopy(manifest['source_library_credit']),
        'source_tables': deepcopy(source_tables),
        'admission_authorized': False, 'scope_complete': complete == len(rows),
        'qualification': 'Complete source review accounts for the recorded scope; it is separate from consensus, corpus admission, lexical eligibility, and a tested tagged release. Reviewed-verified means an exact scan reading under declared transcription conventions, not unambiguous edition correctness. Uncertain source readings remain explicit.',
        'counts': {'passages': len(rows), 'pages': manifest['scope']['pages'],
            'status': {status: statuses[status] for status in sorted(STATUSES)},
            'fully_assessed_rows': complete, 'verified_rows': statuses['reviewed-verified'],
            'complete_scan_review_rows': complete,
            'rows_with_source_uncertainty': statuses['reviewed-with-uncertainty'],
            'partially_assessed_rows': sum(bool(r['segments']) and not r['complete'] for r in rows),
            'unreviewed_rows': sum(not r['segments'] for r in rows),
            'characters': manifest['scope']['characters'],
            'reviewed_characters': sum(r['reviewed_characters'] for r in rows),
            'lexical_tokens': manifest['scope']['lexical_tokens'],
            'reviewed_lexical_tokens': sum(r['reviewed_lexical_tokens'] for r in rows),
            'corrected_segments': sum(s['original_text'] != s['corrected_text'] for r in rows for s in r['segments']),
            'unchanged_segments': sum(s['original_text'] == s['corrected_text'] for r in rows for s in r['segments']),
            'source_fragment_exclusions': sum(len(r['additional_lexical_exclusions']) for r in rows),
            'uncertainty_exclusion_candidates': sum(len(r['uncertainty_exclusion_candidates']) for r in rows),
            'nonbody_exclusion_candidates': sum(len(r['nonbody_exclusion_candidates']) for r in rows),
            'complete_pages': len(pages_complete)},
        'complete_physical_pages': pages_complete, 'rows': rows,
    }


def _inputs(root):
    return tuple((Path(root) / p).read_bytes() for p in (CORPUS, SCAN, LIBRARY, ORIGINAL, COVERAGE))


def build(root=ROOT, *, manifest_path=MANIFEST, reviews_path=REVIEWS, evidence_files=None):
    root = Path(root)
    manifest = json.loads((root / manifest_path).read_bytes())
    pin = manifest['input_pins']['frozen_corpus']
    path = Path(pin['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('The frozen baseline requires a repository-relative archive path')
    frozen_raw = (root / path).read_bytes()
    corpus_raw = gzip.decompress(frozen_raw)
    if sha(frozen_raw) != pin['sha256'] or sha(corpus_raw) != pin['uncompressed_sha256']:
        raise ValueError('Frozen baseline corpus archive changed')
    # Reproduction remains independent of later admitted corpus changes.
    inputs = (corpus_raw, *((root / p).read_bytes() for p in (SCAN, LIBRARY, ORIGINAL, COVERAGE)))
    return compile_campaign(manifest, json.loads(decoded_bytes(reviews_path, (root / reviews_path).read_bytes())), *inputs,
        evidence_files=evidence_files, frozen_corpus_raw=frozen_raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--freeze', action='store_true', help='Write a new immutable scope; never overwrite one')
    action.add_argument('--write', action='store_true', help='Compile the explicitly authored source review records')
    action.add_argument('--check', action='store_true', help='Require exact reproduction of the compiled review status')
    parser.add_argument('--campaign-id')
    parser.add_argument('--created-at')
    parser.add_argument('--baseline-commit')
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--reviews', type=Path, default=REVIEWS)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--evidence-file', action='append', type=Path, default=[],
                        help='Repository-relative frozen JSON artifact used by an exact OCR reading pointer')
    parser.add_argument('--source-table', action='append', type=Path, default=[],
                        help='Repository-relative authored source table whose exact pin is recorded in source_tables')
    args = parser.parse_args()
    if args.freeze:
        inputs = _inputs(ROOT)
        frozen_raw = gzip.compress(inputs[0], mtime=0)
        result = freeze_scope(*inputs, campaign_id=args.campaign_id,
            created_at=args.created_at, baseline_commit=args.baseline_commit, frozen_corpus_raw=frozen_raw)
        path = ROOT / args.manifest
        baseline = ROOT / BASELINE
        if path.exists() or baseline.exists():
            raise SystemExit('The campaign scope or frozen baseline already exists; neither may be overwritten')
        path.parent.mkdir(parents=True, exist_ok=True)
        baseline.parent.mkdir(parents=True, exist_ok=True)
        with baseline.open('xb') as target:
            target.write(frozen_raw)
        try:
            with path.open('xb') as target:
                target.write(encode(result))
        except BaseException:
            baseline.unlink()
            raise
        print(json.dumps({'manifest': args.manifest.as_posix(), 'scope': result['scope']}))
        return
    evidence = {p.as_posix(): (ROOT / p).read_bytes() for p in (*args.evidence_file, *args.source_table)}
    result = build(ROOT, manifest_path=args.manifest, reviews_path=args.reviews, evidence_files=evidence)
    raw = artifact_bytes(args.output, result)
    path = ROOT / args.output
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    elif args.check and path.read_bytes() != raw:
        raise SystemExit('Complete-passage review accounting does not reproduce from its frozen inputs')
    print(json.dumps({'output': args.output.as_posix(), 'sha256': sha(raw),
                      'scope_complete': result['scope_complete'], 'counts': result['counts']}))


if __name__ == '__main__':
    main()
