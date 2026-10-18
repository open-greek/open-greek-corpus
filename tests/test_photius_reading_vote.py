from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ocr_consensus import compact_corpus_consensus, merge_witnesses, restore_corpus_consensus
from photius_reading_vote import SL, SL_ARCHIVE_SHA256, encode, plan, sha

LOCUS = 'photius_bekker1824_0153.1'
REF = {'path': 'data/old/networks.json.gz', 'key': '153'}
OUT = {'path': 'data/new/networks.json.gz', 'key': LOCUS}
REVIEW = {'path': 'data/new/source-review.json', 'sha256': 'a' * 64}


def source(text='ἀρχὴ λόγον τέλος καταλείπει'):
    return {'id': SL, 'vote_group': SL, 'text': text, 'artifact_sha256': '3' * 64,
            'source_section': 'section153', 'source_file_sha256': SL_ARCHIVE_SHA256,
            'source_url': 'https://example.org/local002.json.gz', 'license': 'CC-BY-SA-4.0',
            'credit': {'attribution': 'Source Library', 'separate_api_notice': {'tdm_reservation': 1}}}


def project(witness, excluded_text):
    text = witness['text'];start = text.index(excluded_text);end = start + len(excluded_text)
    result = deepcopy(witness)
    result['voting_segments'] = [{'start': a, 'end': b, 'text': text[a:b]}
                                 for a, b in [(0, start), (end, len(text))] if a < b]
    result['abstention_audit'] = {'reviewed_text_sha256': sha(text.encode()), 'source_review': REVIEW,
        'excluded_spans': [{'start': start, 'end': end, 'text': text[start:end], 'reason': 'Earlier source-reviewed exclusion'}]}
    return result


def fixture(prior_sl=None, existing_model_mask=False):
    text = 'ΚΕΦΑΛΑΙΟΝ. ἀρχὴ λόγου τέλος'
    first = {'id': 'model-one', 'vote_group': 'model-one', 'model': 'Qwen-one', 'revision': 'pinned-one',
             'text': text, 'artifact_sha256': '1' * 64, 'raw_file_sha256': '5' * 64, 'image_sha256': '6' * 64,
             'raw_attempts': [{'text': 'retained failed attempt', 'finish_reason': 'length'}]}
    if existing_model_mask:
        first = project(first, 'λόγου')
    second = {'id': 'model-two', 'model': 'Qwen-two', 'revision': 'pinned-two',
              'artifact_sha256': '2' * 64, 'text': 'ἀρχὴ λογου τέλος'}
    witnesses = [first, second] + ([deepcopy(prior_sl)] if prior_sl is not None else [])
    full = merge_witnesses(witnesses)
    raw = gzip.compress(encode({'153': full}), mtime=0)
    row = {'urn': 'photius.bibliotheca', 'locus': LOCUS, 'edition': 'original-admission',
           'source': 'ocr', 'license': 'CC-BY-SA-4.0', 'physical_refs': {'scan_page': 153, 'printed_page': 141},
           **compact_corpus_consensus(full, REF)}
    digital = source()
    end = digital['text'].index(' καταλείπει')
    record = {'locus': LOCUS, 'scan_page': 153, 'printed_page': 141,
              'reviewed_at': '2026-10-18T00:00:00Z', 'evidence': 'Direct source comparison.',
              'source_section': {'id': 'section153', 'label': 'Page s153', 'artifact_sha256': '3' * 64,
                                 'full_original_text': digital['text'], 'full_text_sha256': sha(digital['text'].encode())},
              'voting_segments': [{'start': 0, 'end': end, 'text': digital['text'][:end]}],
              'held_spans': [{'start': end, 'end': len(digital['text']), 'original_text': digital['text'][end:],
                             'reason': 'Source-reviewed terminal fragment.'}],
              'first_boundary_policy': 'Only observed source text votes; unobserved prefix abstains.',
              'source_regions': {k: [.1, .1, .9, .8] for k in ('first', 'body', 'last')},
              'raw_witness_masks': []}
    original = next(w for w in full['ocr_consensus']['witnesses'] if w['id'] == 'model-one')
    pin = {k: original[k] for k in ('id', 'model', 'revision', 'artifact_sha256', 'text_sha256',
                                    'raw_file_sha256', 'image_sha256')}
    record['raw_witness_masks'] = [{'full_network': {**REF, 'archive_sha256': sha(raw)},
        'witness': pin, 'original_text': text, 'exclusions': [{'start': 0, 'end': len('ΚΕΦΑΛΑΙΟΝ. '),
            'original_text': 'ΚΕΦΑΛΑΙΟΝ. ', 'classification': 'running_header',
            'source_region': [.2, .01, .8, .08], 'evidence': 'Printed repeated page header above body.'}]}]
    return row, raw, full, digital, record


def run(values):
    row, raw, full, digital, record = values
    return plan(row, raw, digital, record, source_review=REVIEW, network_reference=OUT)


def test_adds_one_source_vote_preserves_ties_raws_and_original_metadata():
    values = fixture();frozen = deepcopy(values)
    updated, full, audit = run(values)
    assert values == frozen
    assert audit['model_witnesses_before'] == audit['model_witnesses_after'] == 2
    assert audit['source_library_votes_before'] == 0 and audit['source_library_votes_after'] == 1
    assert updated['edition'] == 'original-admission' and updated['source'] == 'ocr'
    assert updated['reading_repair']['source_library_action'] == 'added'
    assert 'ΚΕΦΑΛΑΙΟΝ' not in updated['text'] and 'καταλείπει' not in updated['text']
    assert set(full['ocr_consensus']['slots'][1]['tied_readings']) == {'λόγου', 'λογου', 'λόγον'}
    assert updated['analysis_text'] == 'ἀρχὴ τέλος'
    assert restore_corpus_consensus({k: updated[k] for k in ('text', 'analysis_text', 'ocr_consensus')}, full) == full
    assert audit['original_row'] == values[0]
    assert audit['mask_notes'][0]['original_text'] == 'ΚΕΦΑΛΑΙΟΝ. '
    for original in values[2]['ocr_consensus']['witnesses']:
        changed = next(w for w in full['ocr_consensus']['witnesses'] if w['id'] == original['id'])
        assert changed['text'] == original['text']
        if 'raw_attempts' in original:
            assert changed['raw_attempts'] == original['raw_attempts']
    sl = next(w for w in full['ocr_consensus']['witnesses'] if w['id'] == SL)
    assert sl['text'] == values[3]['text'] and sl['credit'] == values[3]['credit']


def test_model_existing_abstentions_are_not_reenabled():
    values = fixture(existing_model_mask=True)
    updated, result, audit = run(values)
    witness = result['ocr_consensus']['witnesses'][0]
    assert witness['abstention_audit']['prior_abstention_audit'] == values[2]['ocr_consensus']['witnesses'][0]['abstention_audit']
    assert any('λόγου' in span['text'] for span in witness['abstention_audit']['excluded_spans'])
    middle = result['ocr_consensus']['slots'][1]
    assert 'model-one' in middle['abstentions'] or any(x.startswith('model-one#') for x in middle['abstentions'])
    assert all('model-one' not in reading['support_groups'] for reading in middle['readings'])


def test_existing_digital_vote_is_replaced_once_and_its_abstentions_survive():
    prior = project(source(), 'λόγον')
    values = fixture(prior_sl=prior)
    updated, result, audit = run(values)
    assert audit['source_library_action'] == 'replaced'
    assert audit['source_library_votes_before'] == audit['source_library_votes_after'] == 1
    sl = next(w for w in result['ocr_consensus']['witnesses'] if w['id'] == SL)
    assert sl['retained_previous_readings'] == [values[2]['ocr_consensus']['witnesses'][-1]]
    assert any(span['text'] == 'λόγον' for span in sl['abstention_audit']['excluded_spans'])
    assert all(SL not in reading['support_groups'] for reading in result['ocr_consensus']['slots'][1]['readings'])


def test_same_digital_archive_under_an_alias_cannot_gain_a_second_vote():
    prior = source()
    prior.update(id='earlier-digital-label', vote_group='earlier-digital-label')
    updated, result, audit = run(fixture(prior_sl=prior))
    assert audit['source_library_votes_before'] == audit['source_library_votes_after'] == 1
    assert audit['source_library_action'] == 'replaced'
    assert len(result['ocr_consensus']['witnesses']) == 3


def test_missing_source_can_apply_model_mask_without_adding_digital_vote():
    values = list(fixture());values[3] = None;values[4]['source_section'] = None
    updated, result, audit = run(values)
    assert audit['source_library_action'] == 'unavailable' and audit['source_library_votes_after'] == 0
    assert len(result['ocr_consensus']['witnesses']) == 2 and 'ΚΕΦΑΛΑΙΟΝ' not in updated['text']
    values[4]['raw_witness_masks'] = []
    updated, result, audit = run(values)
    assert updated == values[0] and result == values[2] and audit['changed'] is False


def test_earlier_row_repair_metadata_remains_accessible():
    values = list(fixture())
    values[0]['reading_repair'] = {'source_review': {'path': 'data/earlier.json', 'sha256': 'd' * 64}}
    updated, result, audit = run(values)
    assert updated['reading_repair']['previous_reading_repair'] == values[0]['reading_repair']


def test_unobserved_digital_prefix_abstains_without_omission_vote():
    values = list(fixture());values[4]['raw_witness_masks'] = []
    # Retain a real source prefix in model witnesses, while digital begins later.
    row, raw, original, digital, record = values
    source_start = digital['text'].index('λόγον')
    old_end = record['voting_segments'][0]['end']
    record['voting_segments'] = [{'start': source_start, 'end': old_end, 'text': digital['text'][source_start:old_end]}]
    record['held_spans'].insert(0, {'start': 0, 'end': source_start,
        'original_text': digital['text'][:source_start], 'reason': 'Not observed at the source boundary.'})
    updated, full, audit = run(values)
    first = next(s for s in full['ocr_consensus']['slots'] if any(r['text'] == 'ἀρχὴ' for r in s['readings']))
    assert SL not in first['omission_groups']
    assert first['selected'] == 'ἀρχὴ'


@pytest.mark.parametrize('mutation', [
    lambda v: v[4].update(locus='different.row'),
    lambda v: v[4].update(scan_page=154),
    lambda v: v[4]['source_section'].update(full_text_sha256='f' * 64),
    lambda v: v[3].update(license='PD'),
    lambda v: v[3].update(artifact_sha256='f' * 64),
    lambda v: v[3].update(source_file_sha256='f' * 64),
    lambda v: v[3].update(source_section='different-section'),
    lambda v: v[4]['voting_segments'][0].update(text='unreviewed text'),
    lambda v: v[4]['held_spans'][0].update(original_text='unreviewed source'),
    lambda v: v[4].update(held_spans=[]),
    lambda v: v[4]['raw_witness_masks'][0]['witness'].update(model='different-model'),
    lambda v: v[4]['raw_witness_masks'][0]['full_network'].update(archive_sha256='f' * 64),
    lambda v: v[4]['raw_witness_masks'][0]['exclusions'][0].update(start=True),
    lambda v: v[4]['raw_witness_masks'][0]['exclusions'][0].update(source_region=[0, 0, 2, 1]),
    lambda v: v[4]['raw_witness_masks'][0]['exclusions'][0].update(original_text='wrong header'),
    lambda v: v[4]['raw_witness_masks'].append(deepcopy(v[4]['raw_witness_masks'][0])),
    lambda v: v[0].update(analysis_text='stale projection'),
])
def test_changed_pins_or_inexact_source_offsets_fail(mutation):
    values = list(fixture())
    mutation(values)
    with pytest.raises(ValueError):
        run(values)
