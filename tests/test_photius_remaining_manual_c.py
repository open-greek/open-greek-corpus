"""Manual batch C locations bind every byte of their later source authority."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import photius_remaining_manual_c as manual
import prepare_photius_editorial_continuation as continuation


@pytest.fixture(scope='module')
def scopes():
    return continuation.scope(ROOT)[1]


def test_all_thirty_authored_scopes_are_exact_and_nonfragment(scopes):
    assert len(manual.SPECS) == 30
    assert len({(s['locus'], s['segment_index']) for s in manual.SPECS}) == 30
    for spec in manual.SPECS:
        target = scopes[spec['locus'], spec['segment_index']]
        assert manual._digest(target['row']) == spec['row_sha256']
        assert manual._digest(target['record']) == spec['inherited_record_sha256']
        assert target['row']['text'][spec['start']:spec['end']] == spec['original_text']
        assert target['record']['original_segment']['text_role'] == 'authorial-body'
        assert not target['record']['original_segment']['fragments']
        assert len(spec['context_sha256']) == len(spec['surface_sha256']) == 64
        assert spec['source_indices'] == list(range(spec['source_indices'][0],
            spec['source_indices'][0] + len(spec['source_indices'])))


def test_only_four_source_reviewed_display_rules_are_authorized():
    actual = {(s['locus'].rsplit('_', 1)[1], s['segment_index']): s['rendering']
              for s in manual.SPECS if s['rendering']}
    assert actual == {('0227.18', 1): {'retire_suffix': '),', 'boundary_after': ','},
                      ('0261.1', 5): {'retire_suffix': ')'},
                      ('0268.1', 13): {'retire_suffix': '....'},
                      ('0275.31', 0): {'retire_prefix': '30'}}
    ellipsis = next(s for s in manual.SPECS if s['locus'].endswith('_0268.1'))
    assert 'explicit editorial fill' in ellipsis['evidence']
    assert 'not a transcription' in ellipsis['evidence']
    assert ellipsis['selection'][2] == 'ὤμιλλαν οἱ Ἀττικοὶ διὰ τοῦ ο'


def synthetic_case():
    spec = deepcopy(manual.SPECS[0])
    units = [{'text': 'τὸν ἀποδίδωσι θρόνον', 'html_line': 1, 'html_column': 0,
              'unit_index': 0, 'codex': '258', 'bekker': '482a'}]
    spec.update(selection=(0, 1, 'ἀποδίδωσι'), context_sha256=manual._digest(units),
                source_indices=[47], surface_sha256='1' * 64)
    return spec, manual._record(spec, units)


@pytest.mark.parametrize('field', ['kind', 'role', 'original_text', 'current_extent',
    'original_row_sha256', 'inherited_record_sha256', 'surface_sha256', 'readings',
    'rendering', 'evidence', 'reviewed_at', 'scan', 'qualification', 'source_context'])
def test_every_public_field_is_reconstructed_from_the_authored_spec(monkeypatch, field):
    spec, record = synthetic_case()
    key = spec['locus'], spec['segment_index']
    monkeypatch.setattr(manual, 'SPECS', [spec])
    assert manual.validate_record(key, record) == record
    changed = deepcopy(record)
    changed[field] = 'changed'
    with pytest.raises(ValueError):
        manual.validate_record(key, changed)


@pytest.mark.parametrize('mutation', ['unit-text', 'unit-order', 'source-index',
                                     'token-text', 'token-ref', 'source-id', 'extra'])
def test_nested_source_and_index_mutations_are_rejected(monkeypatch, mutation):
    spec, record = synthetic_case()
    key = spec['locus'], spec['segment_index']
    monkeypatch.setattr(manual, 'SPECS', [spec])
    changed = deepcopy(record)
    if mutation == 'unit-text': changed['source_context']['units'][0]['text'] += ' '
    elif mutation == 'unit-order': changed['source_context']['units'][0]['unit_index'] += 1
    elif mutation == 'source-index': changed['readings'][0]['tokens'][0]['source_index'] += 1
    elif mutation == 'token-text': changed['readings'][0]['tokens'][0]['text'] = 'ἄλλο'
    elif mutation == 'token-ref': changed['readings'][0]['tokens'][0]['refs'][0]['start'] += 1
    elif mutation == 'source-id': changed['readings'][0]['source_id'] = 'another-source'
    else: changed['allow_arbitrary_deletion'] = True
    with pytest.raises(ValueError):
        manual.validate_record(key, changed)


def test_phrase_cannot_choose_a_global_first_occurrence():
    spec, record = synthetic_case()
    units = deepcopy(record['source_context']['units'])
    units[0]['text'] += ' ἀποδίδωσι'
    with pytest.raises(ValueError, match='occur once'):
        manual._reading(spec, units)
    units[0]['text'] = 'ἀποδίδωσι'
    with pytest.raises(ValueError, match='context changed'):
        manual._record(spec, units)


def test_source_indices_are_consecutive_exact_integer_occurrences():
    spec, record = synthetic_case()
    units = record['source_context']['units']
    spec['source_indices'] = [True]
    with pytest.raises(ValueError, match='token indices'):
        manual._reading(spec, units)
    spec['source_indices'] = [47, 48]
    with pytest.raises(ValueError, match='token indices'):
        manual._reading(spec, units)


def test_invalidated_live_source_is_rejected_but_recorded_context_stays_usable(monkeypatch, scopes):
    spec, record = synthetic_case()
    key = spec['locus'], spec['segment_index']
    monkeypatch.setattr(manual, 'SPECS', [spec])
    assert manual.validate_record(key, record) == record
    with pytest.raises(ValueError, match='source changed'):
        manual.review_remaining(b'<html>invalidated source</html>', scopes)
    assert manual.validate_record(key, record) == record


def test_live_scope_baseline_is_checked_without_mutation(monkeypatch, scopes):
    spec = deepcopy(manual.SPECS[0])
    raw = b'<h3>258</h3><h2>482a</h2><td>another source</td>'
    monkeypatch.setattr(manual, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(manual, 'SPECS', [spec])
    changed = deepcopy(scopes)
    target = changed[spec['locus'], spec['segment_index']]
    target['row']['text'] += ' '
    snapshot = deepcopy(changed)
    with pytest.raises(ValueError, match='exact original scope'):
        manual.review_remaining(raw, changed)
    assert changed == snapshot


def test_rendering_scans_are_exact_and_independently_checkable(monkeypatch):
    scans = [s for s in manual.SPECS if s.get('scan')]
    assert len(scans) == 4
    assert {s['scan']['physical_page'] for s in scans} == {227, 261, 268, 275}
    with pytest.raises(ValueError, match='source image changed'):
        manual.validate_scan(None, lambda *args: b'wrong-image')
    for path, expected in manual.SOURCE_PINS.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected


def test_partial_theta_only_uses_its_own_exact_complete_word():
    spec = next(s for s in manual.SPECS if s['locus'].endswith('_0233.30'))
    assert spec['original_text'] == 'σθ' and spec['start'] == 6 and spec['end'] == 8
    assert spec['selection'][2] == 'Ἀνεγνώσθη'
    assert spec['rendering'] == {}


@pytest.mark.parametrize('suffix,reading,expected', [
    ('_0227.18', 'ἐξάγονται', 'ἐξάγονται,'),
    ('_0261.1', 'πνίγεται', 'πνίγεται'),
    ('_0268.1', 'ὤμιλλαν οἱ Ἀττικοὶ διὰ τοῦ ο', 'ὤμιλλαν οἱ Ἀττικοὶ διὰ τοῦ ο'),
    ('_0275.31', 'σφαγιασθέντος', 'σφαγιασθέντος'),
])
def test_exact_scanned_wrapper_rules_produce_the_reviewed_display(scopes, suffix, reading, expected):
    spec = next(s for s in manual.SPECS if s['locus'].endswith(suffix) and s['rendering'])
    target = scopes[spec['locus'], spec['segment_index']]
    rendered = continuation.render(spec['original_text'], target['row']['text'],
        spec['start'], spec['end'], {'surface': reading}, rendering=spec['rendering'])
    assert rendered is not None and rendered['corrected_text'] == expected
