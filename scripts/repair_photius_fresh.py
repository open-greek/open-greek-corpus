"""Plan the exact source-reviewed page245 fresh-OCR editorial separation.

This pure helper does not rewrite the immutable coverage admission. The final
Photius reversible layer archives its inputs and applies the returned one-row
plan. Whole raw witnesses remain present; reviewed header/footer spans abstain.
"""
from __future__ import annotations

from audit_compression import compress_gzip

from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

from ocr_consensus import compact_corpus_consensus, merge_witnesses, restore_corpus_consensus

REVIEW = Path('data/ingest_reviews/photius-bekker-fresh-editorial-spans.json')
ORIGINAL_NETWORK = Path('data/corpus_changes/photius-bekker-coverage/full-networks.json.gz')
PARATEXT = Path('data/paratext/photius-bekker-fresh-editorial-spans.jsonl')
LOCUS = 'photius_bekker1824_0245.1'
SOURCE_SHA = 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6'
MODEL = 'Qwen/Qwen3.6-27B'
REVISION = '6a9e13bd6fc8f0983b9b99948120bc37f49c13e9'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def row_sha(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def _path(value):
    return (isinstance(value, str) and value and ':' not in value and '\\' not in value
            and not PurePosixPath(value).is_absolute() and '..' not in PurePosixPath(value).parts)


def _digest(value):
    return isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{64}', value))


def _bbox(value):
    return (isinstance(value, list) and len(value) == 4
            and all(type(x) in (int, float) and math.isfinite(x) for x in value)
            and 0 <= value[0] < value[2] <= 1 and 0 <= value[1] < value[3] <= 1)


def correct(authority_raw, original_rows_by_locus, original_network_bytes, archive):
    """Return (updated_row, report, artifacts) from exact retained inputs.

    Raw-record and request digests are checked by the authority preparer against
    their original files. This helper additionally verifies every pin available
    in the full network and both compact/full round trips before returning.
    """
    archive = Path(archive)
    if not _path(archive.as_posix()):
        raise ValueError('Fresh correction archive must be a relative public path')
    review = json.loads(authority_raw)
    if (review.get('schema_version') != 1 or review.get('work') != 'photius.bibliotheca'
            or review.get('kind') != 'source-reviewed-fresh-editorial-spans'
            or not review.get('reviewed_at') or len(review.get('records', [])) != 1):
        raise ValueError('Fresh correction requires the one completed page245 source authority')
    source = review.get('source_scan', {})
    if source.get('sha256') != SOURCE_SHA or not source.get('url', '').startswith('https://'):
        raise ValueError('Fresh correction source differs from the original Bekker scan')
    item = review['records'][0]
    if (item.get('locus') != LOCUS or item.get('scan_page') != 245
            or item.get('printed_page') != 233 or not item.get('evidence')):
        raise ValueError('Only the reviewed fresh page245 correction is authorized')
    old = deepcopy(original_rows_by_locus[LOCUS])
    if old.get('physical_refs', {}).get('scan_sha256') != SOURCE_SHA:
        raise ValueError('Fresh corpus row has a different physical source')
    reference = old['ocr_consensus']['full_network']
    authority_network = item.get('full_network', {})
    if (reference['path'] != ORIGINAL_NETWORK.as_posix() or reference['key'] != '245'
            or authority_network != {'path': reference['path'], 'key': reference['key'],
                                     'sha256': sha(original_network_bytes)}):
        raise ValueError('Reviewed original full network differs from the corpus row')
    original_networks = json.loads(gzip.decompress(original_network_bytes))
    original = original_networks[reference['key']]
    projection = {field: old[field] for field in ('text', 'analysis_text', 'ocr_consensus')}
    restore_corpus_consensus(projection, original)
    witness_pin = item.get('witness', {})
    if witness_pin.get('model') != MODEL or witness_pin.get('revision') != REVISION:
        raise ValueError('Fresh correction cannot substitute another model or checkpoint')
    witnesses = deepcopy(original['ocr_consensus']['witnesses'])
    selected = [w for w in witnesses if w['id'] == witness_pin.get('id')]
    if len(selected) != 1:
        raise ValueError('Reviewed witness must identify exactly one existing vote')
    witness = selected[0]
    for name in ('model', 'revision', 'artifact_sha256', 'text_sha256', 'image_sha256'):
        if witness.get(name) != witness_pin.get(name) or (name.endswith('sha256') and not _digest(witness_pin.get(name))):
            raise ValueError('Fresh witness identity or source-image pin changed')
    raw_file = witness_pin.get('raw_file', {})
    if (not _path(raw_file.get('path')) or raw_file.get('sha256') != witness.get('raw_file_sha256')
            or not _digest(witness_pin.get('prediction_record_sha256'))
            or not _digest(witness_pin.get('manifest_sha256'))
            or not _path(witness_pin.get('manifest_path'))):
        raise ValueError('Fresh raw-record or request pins are missing or inconsistent')
    text = witness['text']
    if item.get('original_text') != text or sha(text.encode()) != witness_pin['text_sha256']:
        raise ValueError('Reviewed fresh text differs from the complete original witness')
    if 'voting_segments' in witness or 'abstention_audit' in witness:
        raise ValueError('This one fresh correction cannot replace an existing source mask')
    excluded = item.get('exclusions', [])
    retained = item.get('voting_segments', [])
    if (len(excluded) != 2 or len(retained) != 1
            or excluded[0].get('start') != 0 or excluded[1].get('end') != len(text)
            or {s.get('classification') for s in excluded} != {'running_header', 'critical-apparatus'}):
        raise ValueError('Page245 requires exactly the reviewed outer header and footer masks')
    for span in excluded:
        if (not _bbox(span.get('source_region')) or not span.get('evidence')
                or type(span.get('start')) is not int or type(span.get('end')) is not int
                or not 0 <= span['start'] < span['end'] <= len(text)
                or span.get('original_text') != text[span['start']:span['end']]):
            raise ValueError('Fresh exclusion lacks exact codepoint offsets or source evidence')
    source_review = {'path': (archive / 'fresh-source-review.json').as_posix(), 'sha256': sha(authority_raw)}
    witness['voting_segments'] = retained
    witness['abstention_audit'] = {
        'reviewed_text_sha256': sha(text.encode()), 'source_review': source_review,
        'excluded_spans': [{'start': s['start'], 'end': s['end'], 'text': s['original_text'],
                            'reason': s['classification'] + ': ' + s['evidence']} for s in excluded]}
    corrected = merge_witnesses(witnesses)  # Validates exact partition and word/mark boundaries.
    if ([w['id'] for w in corrected['ocr_consensus']['witnesses']]
            != [w['id'] for w in original['ocr_consensus']['witnesses']]):
        raise ValueError('Fresh correction changed the original witness votes')
    network_path = archive / 'fresh-word-networks.json.gz'
    compact = compact_corpus_consensus(corrected, {'path': network_path.as_posix(), 'key': '245'})
    if restore_corpus_consensus(compact, corrected) != corrected:
        raise ValueError('Corrected compact projection failed its full-network round trip')
    updated = {**old, **compact, 'fresh_editorial_layer': {
        'schema': 'source-reviewed-fresh-editorial-spans-v1', 'source_review': source_review,
        'original_full_network': reference, 'exclusions': deepcopy(excluded),
        'physical_refs': deepcopy(old['physical_refs'])}}
    before_path = archive / 'fresh-before-networks.json.gz'
    artifacts = {archive / 'fresh-source-review.json': authority_raw,
                 before_path: original_network_bytes,
                 network_path: compress_gzip(encode({'245': corrected}))}
    paratext = [{'urn': 'photius.bibliotheca', 'language': 'grc',
                 'locus': f'{LOCUS}.witness-editorial-{index + 1}',
                 'class': 'edition_editorial_matter', 'classification': span['classification'],
                 'text': span['original_text'], 'source': old['source'], 'edition': old['edition'],
                 'license': witness.get('license', old['license']),
                 'original_locus': LOCUS, 'witness_id': witness['id'],
                 'span': {'start': span['start'], 'end': span['end']},
                 'source_region': span['source_region'], 'physical_refs': old['physical_refs'],
                 'source_scan': source, 'source_review': source_review,
                 'raw_file': raw_file, 'evidence': span['evidence']}
                for index, span in enumerate(excluded)]
    artifacts[PARATEXT] = b''.join((json.dumps(row, ensure_ascii=False) + '\n').encode() for row in paratext)
    report = {
        'operation': 'separate-source-reviewed-fresh-photius-editorial-spans',
        'work': 'photius.bibliotheca', 'locus': LOCUS, 'reviewed_at': review['reviewed_at'],
        'source_review': source_review, 'source_scan': source,
        'original_networks': {'path': before_path.as_posix(), 'sha256': sha(original_network_bytes)},
        'full_network': compact['ocr_consensus']['full_network'],
        'network_archive': {'path': network_path.as_posix(), 'sha256': sha(artifacts[network_path])},
        'paratext': {'path': PARATEXT.as_posix(), 'sha256': sha(artifacts[PARATEXT]), 'rows': len(paratext),
                     'license': witness.get('license', old['license'])},
        'original_row_sha256': row_sha(old), 'corrected_row_sha256': row_sha(updated),
        'original_row': old, 'corrected_row': updated,
        'original_text': old['text'], 'corrected_text': updated['text'],
        'counts': {'changed_rows': 1, 'excluded_spans': 2,
                   'excluded_characters': sum(s['end'] - s['start'] for s in excluded),
                   'witnesses_before': len(witnesses), 'witnesses_after': len(witnesses),
                   'slots_before': len(original['ocr_consensus']['slots']),
                   'slots_after': len(corrected['ocr_consensus']['slots'])},
        'exclusions': deepcopy(excluded),
        'pin_validation': 'Exact compact/full networks, raw text, model, revision, artifact, file and image pins are verified here. The source-review preparer verifies raw-record and request hashes against their retained files.',
        'reversal': 'Restore original_row and the original compact network reference; original coverage archives and all raw readings remain unchanged.'}
    return updated, report, artifacts
