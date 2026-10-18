from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ocr_consensus import compact_corpus_consensus, merge_witnesses, restore_corpus_consensus
from repair_photius_fresh import (LOCUS, MODEL, ORIGINAL_NETWORK, PARATEXT, REVISION,
                                  SOURCE_SHA, correct, encode, row_sha, sha)

ARCHIVE = Path('data/corpus_changes/photius-bekker-apparatus')


def inputs(third=False):
    header = 'ΚΕΦΑΛΑΙΟΝ.\n\n'
    body = 'ἀρχὴ λόγου τέλος.'
    footer = '\na. 15. δοκιμή. libri.'
    text = header + body + footer
    first = {'id': MODEL + '@' + REVISION, 'model': MODEL, 'revision': REVISION,
             'artifact_sha256': '1' * 64, 'raw_file_sha256': '2' * 64,
             'image_sha256': '3' * 64, 'license': 'CC-BY-4.0', 'text': text}
    second = {'id': 'independent-checkpoint', 'model': 'Qwen/Qwen3.8-27B-FP8',
              'artifact_sha256': '4' * 64, 'text': body,
              'raw_attempts': [{'text': 'failed original retained', 'finish_reason': 'length'}]}
    witnesses = [first, second]
    if third:
        witnesses.append({'id': 'source-library-local002', 'artifact_sha256': '5' * 64,
                          'license': 'CC-BY-SA-4.0', 'text': body, 'credit': 'Source Library'})
    full = merge_witnesses(witnesses)
    raw = gzip.compress(encode({'245': full}), mtime=0)
    compact = compact_corpus_consensus(full, {'path': ORIGINAL_NETWORK.as_posix(), 'key': '245'})
    row = {'urn': 'photius.bibliotheca', 'locus': LOCUS, 'source': 'ocr',
           'edition': 'bekker1824-independent-ocr-consensus', 'language': 'grc',
           'license': 'CC-BY-SA-4.0', 'physical_refs': {'scan_sha256': SOURCE_SHA,
                                                     'scan_page': 245, 'printed_page': 233}, **compact}
    pin = {k: full['ocr_consensus']['witnesses'][0][k]
           for k in ('id', 'model', 'revision', 'artifact_sha256', 'text_sha256', 'image_sha256')}
    pin.update({'raw_file': {'path': 'data/retained.jsonl', 'sha256': '2' * 64},
                'prediction_record_sha256': '6' * 64, 'manifest_sha256': '7' * 64,
                'manifest_path': 'data/scan-request.json'})
    record = {'locus': LOCUS, 'scan_page': 245, 'printed_page': 233,
              'full_network': {'path': ORIGINAL_NETWORK.as_posix(), 'key': '245', 'sha256': sha(raw)},
              'witness': pin, 'original_text': text,
              'exclusions': [
                  {'start': 0, 'end': len(header), 'original_text': header,
                   'classification': 'running_header', 'source_region': [.1, .01, .9, .08],
                   'evidence': 'Source header above the continuing columns.'},
                  {'start': len(header + body), 'end': len(text), 'original_text': footer,
                   'classification': 'critical-apparatus', 'source_region': [.1, .8, .9, .9],
                   'evidence': 'Source smaller apparatus below both body columns.'}],
              'voting_segments': [{'start': len(header), 'end': len(header + body), 'text': body}],
              'evidence': 'Exact reviewed source boundaries.'}
    authority = {'schema_version': 1, 'kind': 'source-reviewed-fresh-editorial-spans',
                 'work': 'photius.bibliotheca', 'reviewed_at': '2026-10-18T15:00:00Z',
                 'source_scan': {'url': 'https://archive.org/verified.pdf', 'sha256': SOURCE_SHA},
                 'records': [record]}
    return authority, {LOCUS: row}, raw, full


@pytest.mark.parametrize('third', [False, True])
def test_remerge_preserves_every_vote_raw_and_network_roundtrip(third):
    authority, rows, raw, original = inputs(third)
    unchanged = deepcopy(rows)
    updated, report, artifacts = correct(encode(authority), rows, raw, ARCHIVE)
    assert rows == unchanged
    assert artifacts[ARCHIVE / 'fresh-before-networks.json.gz'] == raw
    assert artifacts[ARCHIVE / 'fresh-source-review.json'] == encode(authority)
    corrected = json.loads(gzip.decompress(artifacts[ARCHIVE / 'fresh-word-networks.json.gz']))['245']
    assert restore_corpus_consensus({k: updated[k] for k in ('text', 'analysis_text', 'ocr_consensus')}, corrected) == corrected
    assert restore_corpus_consensus({k: rows[LOCUS][k] for k in ('text', 'analysis_text', 'ocr_consensus')}, original) == original
    assert report['original_row'] == rows[LOCUS]
    assert report['corrected_row_sha256'] == row_sha(updated)
    assert report['counts']['witnesses_after'] == (3 if third else 2)
    original_witnesses = original['ocr_consensus']['witnesses']
    corrected_witnesses = corrected['ocr_consensus']['witnesses']
    assert len(original_witnesses) == len(corrected_witnesses)
    assert corrected_witnesses[1:] == original_witnesses[1:]
    for key, value in original_witnesses[0].items():
        assert corrected_witnesses[0][key] == value
    assert updated['analysis_text'] == 'ἀρχὴ λόγου τέλος'
    assert 'ΚΕΦΑΛΑΙΟΝ' not in updated['text'] and 'δοκιμή' not in updated['text']
    assert all(len(slot['readings'][0]['support_groups']) == len(corrected_witnesses)
               for slot in corrected['ocr_consensus']['slots'])
    notes = [json.loads(line) for line in artifacts[PARATEXT].splitlines()]
    assert [note['text'] for note in notes] == [span['original_text'] for span in authority['records'][0]['exclusions']]
    assert [note['classification'] for note in notes] == ['running_header', 'critical-apparatus']
    assert report['paratext']['sha256'] == sha(artifacts[PARATEXT])
    assert report['paratext']['license'] == 'CC-BY-4.0'


@pytest.mark.parametrize('field,value', [
    ('model', 'different-model'), ('revision', '8' * 40), ('artifact_sha256', '8' * 64),
    ('text_sha256', '8' * 64), ('image_sha256', '8' * 64),
    ('manifest_sha256', 'missing'), ('manifest_path', '../private.json'),
    ('prediction_record_sha256', None),
])
def test_changed_witness_pins_fail(field, value):
    authority, rows, raw, _ = inputs()
    authority['records'][0]['witness'][field] = value
    with pytest.raises(ValueError):
        correct(encode(authority), rows, raw, ARCHIVE)


def test_stale_compact_projection_and_network_archive_fail():
    authority, rows, raw, _ = inputs()
    rows[LOCUS]['analysis_text'] = 'silently changed'
    with pytest.raises(ValueError):
        correct(encode(authority), rows, raw, ARCHIVE)
    authority, rows, raw, full = inputs()
    changed = deepcopy(full)
    changed['ocr_consensus']['witnesses'][1]['text'] += ' ἄλλο'
    changed_raw = gzip.compress(encode({'245': changed}), mtime=0)
    authority['records'][0]['full_network']['sha256'] = sha(changed_raw)
    with pytest.raises(ValueError):
        correct(encode(authority), rows, changed_raw, ARCHIVE)


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(locus='another.row'),
    lambda r: r.update(scan_page=246),
    lambda r: r.update(original_text=r['original_text'] + ' '),
    lambda r: r['witness']['raw_file'].update(sha256='9' * 64),
    lambda r: r['exclusions'][0].update(original_text='unreviewed replacement'),
    lambda r: r['exclusions'][0].update(start=True),
    lambda r: r['exclusions'][0].update(source_region=[0, 0, 2, 1]),
    lambda r: r['exclusions'][1].update(classification='body'),
    lambda r: r['voting_segments'][0].update(text='selected a different reading'),
    lambda r: r['voting_segments'][0].update(start=r['voting_segments'][0]['start'] + 1),
])
def test_bad_scope_masks_and_offsets_fail(mutation):
    authority, rows, raw, _ = inputs()
    mutation(authority['records'][0])
    with pytest.raises(ValueError):
        correct(encode(authority), rows, raw, ARCHIVE)


def test_exact_partition_cannot_cut_inside_a_word():
    authority, rows, raw, _ = inputs()
    item = authority['records'][0]
    cut = item['exclusions'][0]['end'] + 1
    item['exclusions'][0].update(end=cut, original_text=item['original_text'][:cut])
    item['voting_segments'][0].update(start=cut,
        text=item['original_text'][cut:item['voting_segments'][0]['end']])
    with pytest.raises(ValueError, match='inside a word'):
        correct(encode(authority), rows, raw, ARCHIVE)
