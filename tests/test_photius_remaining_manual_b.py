"""Context-specific editorial readings never turn holds into source evidence."""
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import photius_remaining_manual_b as manual
import prepare_photius_editorial_continuation as prepare


@pytest.fixture
def example(monkeypatch):
    raw = '<h3>248</h3><h2>435a</h2><td>πρῶτον λέγει· ἔπειτα λέγει τέλος</td>'.encode()
    monkeypatch.setattr(manual, 'SOURCE_SHA256', manual.hashlib.sha256(raw).hexdigest())
    tokens = manual._tokens(raw)
    row = {'locus': 'reviewed-occurrence', 'text': 'ἔπειτα νομοθετεῖ τέλος'}
    start = row['text'].index('νομοθετεῖ')
    inherited = {'locus': row['locus'], 'segment_index': 7, 'original_text': 'νομοθετεῖ'}
    reading = {'source_id': 'tlg-photius-henry', 'role': 'alternative', 'text': 'λέγει',
               'tokens': [tokens[3]]}
    attributed = prepare.attributed_span(reading, prepare.source_document(raw))
    surface = {key: attributed[key] for key in ('surface', 'separators', 'boundary_suffix')}
    spec = {'locus': row['locus'], 'segment_index': 7, 'original_text': 'νομοθετεῖ',
            'start': start, 'end': start + len('νομοθετεῖ'),
            'original_row_sha256': manual._digest(row),
            'inherited_record_sha256': manual._digest(inherited),
            'context_start': 0, 'context_stop': len(tokens), 'context_sha256': manual._digest(tokens),
            'selection': [3, 4], 'expected_source_text': 'λέγει', 'rendering': {},
            'surface_sha256': manual._digest(surface),
            'evidence': 'Select the second λέγει, following ἔπειτα and preceding τέλος.'}
    monkeypatch.setattr(manual, 'SPECS', [spec])
    scopes = {(row['locus'], 7): {'row': row, 'record': inherited,
                                'start': spec['start'], 'end': spec['end']}}
    return raw, scopes, spec


def test_authored_batch_has_all_32_unique_cases_and_only_27_selected_intervals():
    assert len(manual.SPECS) == len({(s['locus'], s['segment_index']) for s in manual.SPECS}) == 32
    selected = [s for s in manual.SPECS if s['selection'] is not None]
    held = [s for s in manual.SPECS if s['selection'] is None]
    assert len(selected) == 27 and len(held) == 5
    assert all(len(s['surface_sha256']) == 64 for s in selected)
    assert all(s['surface_sha256'] is None for s in held)
    indices = [i for s in selected for i in range(*s['selection'])]
    assert len(indices) == len(set(indices))
    assert {(s['locus'].split('_')[-1], s['segment_index']) for s in held} == {
        ('0152.4', 9), ('0172.7', 3), ('0179.2', 0), ('0193.5', 0), ('0215.26', 0)}
    assert len([s for s in held if s['held_reason'] == 'source-word-boundary']) == 2


def test_repeated_source_word_is_selected_by_exact_context_not_target_spelling(example):
    raw, scopes, _ = example
    original = deepcopy(scopes)
    result = manual.review_remaining(raw, scopes)
    record = result['reviewed-occurrence', 7]
    assert record['readings'][0]['text'] == 'λέγει'
    assert record['readings'][0]['tokens'][0]['refs'][0]['start'] == len('πρῶτον λέγει· ἔπειτα ')
    assert record['source_context']['tokens'][1]['text'] == 'λέγει'
    assert record['readings'][0]['tokens'][0]['source_index'] == 3
    assert manual.validate_record(('reviewed-occurrence', 7), record) == record
    assert scopes == original
    record['source_context']['tokens'][0]['text'] = 'changed return value'
    assert scopes == original


def test_explicit_hold_has_no_reading_or_deletion_authority(example):
    raw, scopes, spec = example
    spec.update(selection=None, expected_source_text=None, held_reason='unlocated-orphan')
    spec['surface_sha256'] = None
    result = manual.review_remaining(raw, scopes)
    record = result['reviewed-occurrence', 7]
    assert record['readings'] == [] and record['original_text'] == 'νομοθετεῖ'
    assert record['held_reason'] == 'unlocated-orphan'
    assert record['surface_sha256'] is None
    assert manual.validate_record(('reviewed-occurrence', 7), record) == record


@pytest.mark.parametrize('defect', [
    'evidence', 'date', 'original', 'row-pin', 'inherited-pin', 'extent',
    'reading-text', 'reading-ref', 'source-pin', 'context-text', 'context-ref',
    'context-index', 'reading-index', 'surface-pin', 'rendering', 'held-reason', 'extra-field',
])
def test_literal_validation_reconstructs_every_field(example, defect):
    raw, scopes, _ = example
    record = manual.review_remaining(raw, scopes)['reviewed-occurrence', 7]
    if defect == 'evidence': record['evidence'] = 'Different association'
    elif defect == 'date': record['reviewed_at'] = '2026-01-01T00:00:00Z'
    elif defect == 'original': record['original_text'] = 'λέγει'
    elif defect == 'row-pin': record['original_row_sha256'] = '0' * 64
    elif defect == 'inherited-pin': record['inherited_record_sha256'] = '0' * 64
    elif defect == 'extent': record['reviewed_extent']['start'] += 1
    elif defect == 'reading-text': record['readings'][0]['text'] = 'ἕτερον'
    elif defect == 'reading-ref': record['readings'][0]['tokens'][0]['refs'][0]['start'] = 0
    elif defect == 'source-pin': record['source_context']['sha256'] = '0' * 64
    elif defect == 'context-text': record['source_context']['tokens'][0]['text'] = 'ἕτερον'
    elif defect == 'context-ref': record['source_context']['tokens'][0]['refs'][0]['start'] += 1
    elif defect == 'context-index': record['source_context']['tokens'][0]['source_index'] += 1
    elif defect == 'reading-index': record['readings'][0]['tokens'][0]['source_index'] = 1
    elif defect == 'surface-pin': record['surface_sha256'] = '0' * 64
    elif defect == 'rendering': record['rendering'] = {'retire_suffix': '?'}
    elif defect == 'held-reason': record['held_reason'] = 'new role permission'
    else: record['new'] = 'not authored'
    with pytest.raises(ValueError):
        manual.validate_record(('reviewed-occurrence', 7), record)


@pytest.mark.parametrize('defect', ['missing', 'row', 'record', 'start', 'end'])
def test_changed_target_scope_fails_before_any_proposal(example, defect):
    raw, scopes, _ = example
    scope = scopes['reviewed-occurrence', 7]
    if defect == 'missing': scopes.clear()
    elif defect == 'row': scope['row']['text'] += ' extra'
    elif defect == 'record': scope['record']['segment_index'] += 1
    else: scope[defect] += 1
    with pytest.raises(ValueError, match='baseline occurrence'):
        manual.review_remaining(raw, scopes)


def test_changed_source_fails_after_successful_cached_or_uncached_proposal(example):
    raw, scopes, _ = example
    manual.review_remaining(raw, scopes)
    with pytest.raises(ValueError, match='source changed'):
        manual.review_remaining(raw + b'changed', scopes)


def test_unknown_literal_identity_is_rejected(example):
    raw, scopes, _ = example
    record = manual.review_remaining(raw, scopes)['reviewed-occurrence', 7]
    with pytest.raises(ValueError, match='Unknown'):
        manual.validate_record(('another-occurrence', 7), record)


def test_co_mutated_surface_and_punctuation_cannot_replace_the_authored_surface_pin(example):
    raw, scopes, _ = example
    record = manual.review_remaining(raw, scopes)['reviewed-occurrence', 7]
    reading = record['readings'][0]
    attributed = prepare.attributed_span(reading, prepare.source_document(raw))
    original = {key: attributed[key] for key in ('surface', 'separators', 'boundary_suffix')}
    assert manual._digest(original) == record['surface_sha256']
    forged = deepcopy(original)
    forged['surface'] += ';'
    forged['boundary_suffix'] = {'rendered': ';', 'pieces': []}
    record['surface_sha256'] = manual._digest(forged)
    with pytest.raises(ValueError, match='exact source authority'):
        manual.validate_record(('reviewed-occurrence', 7), record)


@pytest.mark.skipif(not os.environ.get('PHOTIUS_COMPARISON_HTML'),
                    reason='Optional supplied comparison source is not configured')
def test_all_authored_occurrences_against_supplied_full_source():
    raw = Path(os.environ['PHOTIUS_COMPARISON_HTML']).read_bytes()
    _, scopes = prepare.scope()
    records = manual.review_remaining(raw, scopes)
    assert len(records) == 32 and sum(bool(r['readings']) for r in records.values()) == 27
    for key, record in records.items():
        assert manual.validate_record(key, record) == record
        if record['readings']:
            attributed = prepare.attributed_span(record['readings'][0], prepare.source_document(raw))
            surface = {k: attributed[k] for k in ('surface', 'separators', 'boundary_suffix')}
            assert manual._digest(surface) == record['surface_sha256']
            for token in record['readings'][0]['tokens']:
                assert record['source_context']['tokens'][token['source_index'] -
                    record['source_context']['tokens'][0]['source_index']] == token
    assert records['helladius_chrestomathia_photius_bekker_v2_0160.2', 5]['readings'][0]['text'] == 'μέμφεσθαι'
    assert records['helladius_chrestomathia_photius_bekker_v2_0160.2', 7]['readings'][0]['text'] == 'αἰσχύνεσθαί'
    assert records['helladius_chrestomathia_photius_bekker_v2_0215.26', 0]['readings'] == []
