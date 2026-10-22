"""Manual source choices retain exact scope, provenance, and boundary holds."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import photius_remaining_manual_a as manual


def case(monkeypatch, *, held=None, repeated=False):
    spec = deepcopy(manual.SPECS[10])
    text = 'εἰ δὲ αὐτός ἐστι ταῦτα, ὅτε γίνεται, τὴν σύστασιν ἔχει.'
    if repeated:
        text += ' γίνεται δὲ ταῦτα πρὸς ἀνθρώπων.'
    units = [{'text': text, 'html_line': 12, 'html_column': 0,
              'unit_index': 0, 'codex': '235', 'bekker': '306a'}]
    spec.update(selection=(0, 1, 'γίνεται'), context_sha256=manual._digest(units),
                held_reason=held)
    if held:
        spec.update(surface_sha256=None, source_indices=[])
    monkeypatch.setattr(manual, 'SPECS', [spec])
    return (spec['locus'], spec['segment_index']), manual._record(spec, units)


def test_repeated_verb_selected_by_exact_sentence_flanks(monkeypatch):
    key, record = case(monkeypatch, repeated=True)
    assert manual.validate_record(key, record) == record
    selected = record['readings'][0]['tokens']
    assert [token['text'] for token in selected] == ['γίνεται']
    ref = selected[0]['refs'][0]
    source = record['source_context']['units'][0]['text']
    assert source[ref['end']:].startswith(', τὴν σύστασιν')


def test_four_holds_cannot_authorize_complete_word_or_mark_deletion():
    holds = [spec for spec in manual.SPECS if spec['held_reason']]
    assert len(holds) == 4
    assert {spec['held_reason'] for spec in holds} == {
        'punctuation-only', 'cross-row-word', 'omitted-leading-word-fragment'}
    assert next(spec for spec in holds if spec['held_reason'] == 'punctuation-only')['original_text'] == '“'


def test_held_counterpart_stays_diagnostic(monkeypatch):
    key, record = case(monkeypatch, held='cross-row-word')
    assert manual.validate_record(key, record)['readings'] == []
    assert record['diagnostic_readings'][0]['text'] == 'γίνεται'
    record['readings'] = record['diagnostic_readings']
    with pytest.raises(ValueError):
        manual.validate_record(key, record)


@pytest.mark.parametrize('field', [
    'kind', 'status', 'role', 'reviewed_at', 'original_text',
    'original_row_sha256', 'inherited_record_sha256', 'evidence',
    'qualification', 'held_reason', 'readings', 'diagnostic_readings',
    'rendering', 'source_context', 'surface_sha256', 'source_indices',
])
def test_every_public_authority_field_is_pinned(monkeypatch, field):
    key, record = case(monkeypatch)
    record[field] = 'tampered'
    with pytest.raises(ValueError):
        manual.validate_record(key, record)


@pytest.mark.parametrize('field', ['text', 'html_line', 'html_column', 'unit_index', 'codex', 'bekker'])
def test_decoded_source_context_and_refs_are_pinned(monkeypatch, field):
    key, record = case(monkeypatch)
    record['source_context']['units'][0][field] = 'tampered'
    with pytest.raises(ValueError):
        manual.validate_record(key, record)


def test_extra_permissions_ref_changes_and_unknown_identity_fail(monkeypatch):
    key, record = case(monkeypatch)
    added = deepcopy(record)
    added['allow_fragment'] = True
    with pytest.raises(ValueError):
        manual.validate_record(key, added)
    record['readings'][0]['tokens'][0]['refs'][0]['start'] += 1
    with pytest.raises(ValueError):
        manual.validate_record(key, record)
    with pytest.raises(ValueError):
        manual.validate_record((key[0], 999), record)


def test_only_exact_bracketed_occurrence_retires_wrappers():
    permissions = [(spec['original_text'], spec['rendering'])
                   for spec in manual.SPECS if spec.get('rendering')]
    assert permissions == [('[καὶ ἄρχοντα]', {'retire_prefix': '[', 'retire_suffix': ']'})]


def test_source_elision_and_cross_node_word_keep_exact_refs():
    units = [{'text': 'Μεθ’ ὧν και‐', 'html_line': 1, 'html_column': 0,
              'unit_index': 10, 'codex': '238', 'bekker': '316b'},
             {'text': 'ρίαν δέχεται', 'html_line': 2, 'html_column': 0,
              'unit_index': 11, 'codex': '238', 'bekker': '316b'}]
    tokens = manual._source_tokens(units)
    assert tokens[0]['text'] == 'Μεθ’'
    assert units[0]['text'][tokens[0]['refs'][0]['start']:tokens[0]['refs'][0]['end']] == 'Μεθ’'
    assert tokens[2]['text'] == 'καιρίαν'
    assert [ref['unit_index'] for ref in tokens[2]['refs']] == [10, 11]


def test_fresh_review_rejects_changed_source_and_baseline(monkeypatch):
    raw = '<h3>235</h3><h2>306a</h2><td>ὅτε γίνεται τὴν σύστασιν</td>'.encode()
    parser = manual.edition.EditionHTML()
    parser.feed(raw.decode())
    spec = deepcopy(manual.SPECS[10])
    row = {'locus': spec['locus'], 'text': 'ἀρχὴ ἕτε γένοιτο τέλος'}
    inherited = {'locus': spec['locus'], 'segment_index': spec['segment_index']}
    start = row['text'].index('ἕτε')
    spec.update(selection=(0, 1, 'γίνεται'), boundaries={'left': 'ὅτε', 'right': 'τὴν σύστασιν'},
                start=start, end=start + len(spec['original_text']),
                context_sha256=manual._digest(parser.units), row_sha256=manual._digest(row),
                inherited_record_sha256=manual._digest(inherited), source_indices=[1])
    monkeypatch.setattr(manual, 'SPECS', [spec])
    monkeypatch.setattr(manual, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    key = spec['locus'], spec['segment_index']
    scopes = {key: {'row': row, 'record': inherited, 'start': spec['start'], 'end': spec['end']}}
    assert manual.review_remaining(raw, scopes)[key]['readings'][0]['text'] == 'γίνεται'
    with pytest.raises(ValueError):
        manual.review_remaining(raw + b' ', scopes)
    for field in ['row', 'record', 'start', 'end']:
        changed = deepcopy(scopes)
        if field in {'row', 'record'}:
            changed[key][field]['extra'] = 'changed'
        else:
            changed[key][field] += 1
        with pytest.raises(ValueError):
            manual.review_remaining(raw, changed)


def test_located_records_require_source_punctuation_and_indices(monkeypatch):
    key, record = case(monkeypatch)
    assert len(record['surface_sha256']) == 64
    assert len(record['source_indices']) == len(record['readings'][0]['tokens'])
    spec = manual.SPECS[0]
    for field, value in [('surface_sha256', None), ('source_indices', []),
                         ('source_indices', [False])]:
        changed = deepcopy(spec)
        changed[field] = value
        with pytest.raises(ValueError, match='pins are incomplete'):
            manual._record(changed, record['source_context']['units'])
