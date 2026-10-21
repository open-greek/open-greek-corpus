"""The two authored word exceptions do not authorize general scope expansion."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import photius_remaining_words as words
import prepare_photius_editorial_continuation as preparer


@pytest.fixture(scope='module')
def scopes():
    values = preparer.scope(ROOT)[1]
    target = values[words._expanded_key()]
    if 'identity_preimage' in target:
        target = deepcopy(target)
        identity = target.pop('identity_preimage')
        target.update(start=identity['start'], end=identity['end'],
                      record=target.pop('inherited_record'))
        values = {**values, words._expanded_key(): target}
    return values


def test_only_theta_scope_expands_and_original_inputs_stay_literal(scopes):
    before = deepcopy(scopes)
    changed = words.adjust_scopes(scopes)
    theta = words._expanded_key()
    assert scopes == before
    assert set(changed) == set(scopes)
    assert changed[theta]['start'] == 0 and changed[theta]['end'] == 11
    assert changed[theta]['record']['original_text'] == 'Ἀνεγνώθησαν'
    assert changed[theta]['identity_preimage'] == {'start': 6, 'end': 7, 'original_text': 'θ'}
    assert changed[theta]['inherited_record'] == scopes[theta]['record']
    assert changed[theta]['record']['original_segment'] == scopes[theta]['record']['original_segment']
    assert all(changed[key] == value for key, value in scopes.items() if key != theta)
    assert words.adjust_scopes(changed) == changed


def test_wider_interval_must_be_inside_one_exact_inherited_mask(scopes):
    changed = deepcopy(scopes)
    key = words._expanded_key()
    # Keeping the original character excluded is insufficient authority for a
    # whole-word edit, even though a broad union envelope still covers it.
    for leaf in changed[key]['excluded_spans'][0]['evidence']:
        if leaf['classification'] == 'unresolved-source-reading':
            leaf.update(start=6, end=7, text='θ')
    with pytest.raises(ValueError, match='one exact inherited unresolved mask'):
        words.adjust_scopes(changed)


def test_same_inherited_qualification_is_required(scopes):
    changed = deepcopy(scopes)
    for leaf in changed[words._expanded_key()]['excluded_spans'][0]['evidence']:
        if leaf['classification'] == 'unresolved-source-reading':
            leaf['qualification'] = 'A different source review'
    with pytest.raises(ValueError, match='one exact inherited unresolved mask'):
        words.adjust_scopes(changed)


def test_expansion_cannot_borrow_another_held_identity(scopes):
    changed = dict(scopes)
    second = deepcopy(changed[words._expanded_key()])
    second.update(start=1, end=3)
    changed[(words._expanded_key()[0], 999)] = second
    with pytest.raises(ValueError, match='another held uncertainty'):
        words.adjust_scopes(changed)


def test_changed_baseline_row_or_original_identity_is_rejected(scopes):
    for mutation in ('row', 'record', 'coordinates'):
        changed = deepcopy(scopes)
        value = changed[words._expanded_key()]
        if mutation == 'row': value['row']['text'] += ' '
        elif mutation == 'record': value['record']['original_text'] = 'σθ'
        else: value['start'] = 5
        with pytest.raises(ValueError):
            words.adjust_scopes(changed)


def synthetic_case():
    spec = deepcopy(words.SPECS[1])
    units = [{'text': 'Ἀνεγνώσθη ', 'html_line': 1, 'html_column': 0,
              'unit_index': 0, 'codex': '269', 'bekker': '498a'}]
    spec.update(selection=(0, 1, 'Ἀνεγνώσθη'), context_sha256=words._digest(units))
    return spec, words._record(spec, units)


@pytest.mark.parametrize('field', ['kind', 'role', 'original_text', 'identity_preimage',
    'reviewed_extent', 'original_row_sha256', 'inherited_record_sha256',
    'inherited_mask_sha256', 'evidence', 'qualification', 'rendering', 'scan',
    'word_context', 'readings'])
def test_every_recorded_authority_field_is_pinned(monkeypatch, field):
    spec, record = synthetic_case()
    key = spec['locus'], spec['segment_index']
    monkeypatch.setattr(words, 'SPECS', [spec])
    assert words.validate_record(key, record) == record
    altered = deepcopy(record)
    altered[field] = 'changed'
    with pytest.raises(ValueError):
        words.validate_record(key, altered)


def test_no_extra_permission_or_context_reference_mutation(monkeypatch):
    spec, record = synthetic_case()
    key = spec['locus'], spec['segment_index']
    monkeypatch.setattr(words, 'SPECS', [spec])
    altered = deepcopy(record)
    altered['allow_arbitrary_word_replacement'] = True
    with pytest.raises(ValueError): words.validate_record(key, altered)
    altered = deepcopy(record)
    altered['word_context']['units'][0]['html_line'] += 1
    with pytest.raises(ValueError, match='context changed'): words.validate_record(key, altered)
    altered = deepcopy(record)
    altered['readings'][0]['tokens'][0]['refs'][0]['start'] += 1
    with pytest.raises(ValueError): words.validate_record(key, altered)


def test_candidate_is_unique_in_its_reviewed_context():
    spec, record = synthetic_case()
    repeated = deepcopy(record['word_context']['units'])
    repeated[0]['text'] *= 2
    with pytest.raises(ValueError, match='occur once'): words._reading(spec, repeated)


def test_unpinned_html_is_rejected_without_mutating_scopes(scopes):
    adjusted = words.adjust_scopes(scopes)
    snapshot = deepcopy(adjusted)
    with pytest.raises(ValueError, match='source changed'):
        words.review_words(b'<html>changed</html>', adjusted)
    assert adjusted == snapshot


def test_numeric_permission_is_exact_and_theta_is_explicit_editorial_variant():
    assert len(words.SPECS) == 2
    numeric, theta = words.SPECS
    assert numeric['original_text'] == '1469'
    assert numeric['rendering'] == {'allow_non_greek_original': True}
    assert theta['rendering'] == {}
    assert 'singular' in theta['qualification'] and 'plural' in theta['qualification']
    assert 'not a claim of agreement' in theta['qualification']


def test_published_source_inputs_are_pinned():
    for path, digest in words.SOURCE_PINS.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest
