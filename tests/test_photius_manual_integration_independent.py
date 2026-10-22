"""Independent integration checks for strict individual editorial authority."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import photius_remaining_manual_a as manual
import prepare_photius_editorial_continuation as prepare
import repair_photius_editorial_continuation as layer


def case(monkeypatch, *, held=False):
    original = 'κακὸν λόγον'
    text = 'ἀρχὴ ' + original + ' τέλος'
    start, end = len('ἀρχὴ '), len('ἀρχὴ ' + original)
    raw = '<h3>248</h3><h2>435a</h2><td>ἀρχὴ σαφές, ῥῆμα τέλος</td>'.encode()
    source = {'id': 'tlg-photius-henry', 'edition': 'Henry, Bibliothèque',
              'citation': 'Photius, Bibliotheca 4040.001', 'sha256': layer.sha(raw)}
    units = prepare.source_document(raw)
    known = layer.previous._source_tokens(raw, source)
    selected = list(known.values())[1:-1]
    source_reading = {'text': ' '.join(token['text'] for _, token in selected),
        'source_id': source['id'], 'role': 'alternative',
        'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs'])}
                   for _, token in selected]}
    attributed = prepare.attributed_span(source_reading, units)
    surface_sha = manual._digest({key: attributed[key]
        for key in ('surface', 'separators', 'boundary_suffix')})
    locus = 'independently-reviewed-manual-occurrence'
    mask = {'start': start, 'end': end, 'text': original,
            'classification': 'unresolved-source-reading',
            'qualification': 'Unclear original printed reading.'}
    row = {'locus': locus, 'urn': 'urn:cts:greekLit:tlg4040.tlg001:1',
        'text': text, 'analysis_text': 'ἀρχὴ τέλος',
        layer.previous.TAG: {'excluded_spans': {'path': layer.previous.RECORDS.as_posix(),
            'locus': locus, 'sha256': layer.sha(layer.canonical([mask]))}}}
    inherited = {'locus': locus, 'segment_index': 0, 'physical_page': 170,
        'printed_page': 435, 'original_segment': {'verification': 'uncertain',
            'text_role': 'authorial-body', 'uncertainty': mask['qualification'], 'fragments': []}}
    spec = deepcopy(manual.SPECS[0])
    spec.update(locus=locus, segment_index=0, start=start, end=end,
        original_text=original, row_sha256=manual._digest(row),
        inherited_record_sha256=manual._digest(inherited),
        selection=(0, 1, 'σαφές ῥῆμα'), context_sha256=manual._digest(list(units)),
        held_reason='cross-row-word' if held else None,
        surface_sha256=None if held else surface_sha,
        source_indices=[] if held else [index for index, _ in selected])
    monkeypatch.setattr(manual, 'SPECS', [spec])
    monkeypatch.setattr(manual, 'SOURCE_SHA256', source['sha256'])
    monkeypatch.setattr(prepare, 'manual_modules', lambda root=prepare.ROOT: [manual])
    key = locus, 0
    scope = {'row': row, 'start': start, 'end': end, 'record': inherited,
             'excluded_spans': [mask]}
    record = manual.review_remaining(raw, {key: scope})[key]
    reading = prepare.attributed_span((record['readings'] or record['diagnostic_readings'])[0], units)
    for token in reading['tokens']:
        token['source_index'] = known[layer.sha(layer.canonical(token['refs']))][0]
    reading['role'] = 'chosen'
    rendered = prepare.render(original, text, start, end, reading)
    reading['trim'] = rendered['trim']
    decision = {'locus': locus, 'segment_index': 0, 'original_text': original,
        'corrected_text': original, 'decision': 'retained', 'reason': 'individual-source-review',
        'evidence': 'Independently reviewed source sentence.', 'readings': [],
        'manual_review': {'module': manual.__name__, 'review': record}}
    if not held:
        decision.update(rendered, decision='substitute', readings=[reading])
    before = layer.canonical(row) + b'\n'
    authored = {'schema': prepare.SCHEMA, 'reviewed_at': '2026-10-21T23:55:00Z',
        'source': source, 'input_corpus_sha256': layer.sha(before), 'records': [decision]}
    return {'before': before, 'scopes': {key: scope}, 'authored': authored,
            'raw': raw, 'reading': reading, 'rendered': rendered}


def compile_case(inputs, *, literal):
    return layer.compile_review(inputs['before'], inputs['scopes'], inputs['authored'],
                                source_raw=None if literal else inputs['raw'])


def test_individual_source_and_literal_round_trip_preserve_authority(monkeypatch):
    inputs = case(monkeypatch)
    assert compile_case(inputs, literal=False) == compile_case(inputs, literal=True)


@pytest.mark.parametrize('literal', [False, True])
def test_changed_punctuation_cannot_hide_behind_valid_manual_context(monkeypatch, literal):
    inputs = case(monkeypatch)
    decision = inputs['authored']['records'][0]
    reading = decision['readings'][0]
    separator = reading['separators'][0]
    separator['pieces'][0]['text'] = separator['pieces'][0]['text'].replace(',', ';')
    separator['rendered'] = separator['rendered'].replace(',', ';')
    reading['surface'] = reading['surface'].replace(',', ';')
    decision['corrected_text'] = decision['corrected_text'].replace(',', ';')
    # The strict source context itself remains unchanged and valid.
    wrapper = decision['manual_review']
    assert manual.validate_record((decision['locus'], 0), wrapper['review']) == wrapper['review']
    with pytest.raises(ValueError):
        compile_case(inputs, literal=literal)


@pytest.mark.parametrize('literal', [False, True])
def test_uniformly_shifted_source_indices_are_rejected(monkeypatch, literal):
    inputs = case(monkeypatch)
    for token in inputs['authored']['records'][0]['readings'][0]['tokens']:
        token['source_index'] += 25
    with pytest.raises(ValueError):
        compile_case(inputs, literal=literal)


@pytest.mark.parametrize('literal', [False, True])
@pytest.mark.parametrize(('field', 'value'), [
    ('surface_sha256', 'missing'), ('surface_sha256', None),
    ('surface_sha256', 'g' * 64),
    ('source_indices', 'missing'), ('source_indices', None),
    ('source_indices', [False, 2]),
])
def test_engine_requires_complete_pins_even_from_a_future_helper(monkeypatch, literal, field, value):
    inputs = case(monkeypatch)
    wrapper = inputs['authored']['records'][0]['manual_review']
    bad_authority = deepcopy(wrapper['review'])
    if value == 'missing':
        del bad_authority[field]
    else:
        bad_authority[field] = value
    wrapper['review'] = bad_authority
    # Simulate a future source helper returning an incomplete authority. The
    # admission engine must enforce its own minimum provenance contract too.
    monkeypatch.setattr(manual, 'validate_record', lambda key, record: deepcopy(bad_authority))
    with pytest.raises(ValueError):
        compile_case(inputs, literal=literal)


@pytest.mark.parametrize('literal', [False, True])
def test_held_individual_review_cannot_admit_its_diagnostic_reading(monkeypatch, literal):
    inputs = case(monkeypatch, held=True)
    before = compile_case(inputs, literal=literal)
    assert before['records'][0]['decision'] == 'retained'
    decision = inputs['authored']['records'][0]
    decision.update(inputs['rendered'], decision='substitute', readings=[inputs['reading']])
    with pytest.raises(ValueError):
        compile_case(inputs, literal=literal)


@pytest.mark.parametrize('wrapper', [{}, None, [], {'module': '', 'review': {}}])
def test_present_malformed_manual_wrapper_cannot_be_ignored(monkeypatch, wrapper):
    inputs = case(monkeypatch)
    inputs['authored']['records'][0]['manual_review'] = wrapper
    with pytest.raises(ValueError):
        compile_case(inputs, literal=True)


@pytest.mark.parametrize('literal', [False, True])
def test_manual_wrapper_retirement_requires_exact_authored_permission(monkeypatch, literal):
    inputs = case(monkeypatch)
    inputs['authored']['records'][0]['manual_review']['review']['rendering'] = {
        'retire_prefix': 'κακὸν ', 'retire_suffix': 'λόγον'}
    with pytest.raises(ValueError):
        compile_case(inputs, literal=literal)


@pytest.mark.parametrize('literal', [False, True])
def test_individual_review_cannot_reuse_an_earlier_admitted_token(monkeypatch, literal):
    inputs = case(monkeypatch)
    token = inputs['authored']['records'][0]['readings'][0]['tokens'][0]
    next(iter(inputs['scopes'].values()))['previously_used_source_refs'] = {
        layer.sha(layer.canonical(token['refs']))}
    with pytest.raises(ValueError, match='already admitted'):
        compile_case(inputs, literal=literal)


def test_individual_module_source_pins_are_included_and_rechecked(tmp_path, monkeypatch):
    for path in (layer.previous.AUDIT, layer.previous.REVIEW, layer.previous.RECORDS,
                 layer.previous.SOURCE_REVIEW, layer.previous.COMPILED):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'Exact preceding source input.')
    source_path = 'data/review-source.json'
    source_bytes = b'Exact independent source evidence.'
    (tmp_path / source_path).write_bytes(source_bytes)
    module = SimpleNamespace(__name__='photius_remaining_manual_source_pin_test',
        SOURCE_PINS={source_path: layer.sha(source_bytes)})
    monkeypatch.setattr(prepare, 'manual_modules', lambda root=prepare.ROOT: [module])
    assert layer.input_pins(tmp_path)[source_path] == layer.sha(source_bytes)
    (tmp_path / source_path).write_bytes(source_bytes + b' changed')
    with pytest.raises(ValueError, match='individual review source pin changed'):
        layer.input_pins(tmp_path)
