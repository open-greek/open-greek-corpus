"""Check reviewed raw spans and repeated-word digital pointers independently."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unicodedata

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import photius_body_source_observations as observations
from ocr_consensus import merge_witnesses, tokenize


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


@pytest.fixture(scope='module')
def inputs():
    library_raw = (ROOT / observations.SOURCE_LIBRARY['path']).read_bytes()
    assert sha(library_raw) == observations.SOURCE_LIBRARY['sha256']
    library = json.loads(gzip.decompress(library_raw))
    assert library['id'] == observations.SOURCE_LIBRARY['edition']
    assert library['license'] == observations.SOURCE_LIBRARY['license']
    sections = {section['id']: '\n'.join(block['text'] for block in section['blocks']
                if block.get('text')) for section in library['sections']}
    raw_inputs = {}
    for pin in observations.RAW_FILES:
        raw = (ROOT / pin['path']).read_bytes()
        assert sha(raw) == pin['sha256']
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        metadata = rows[0]['_meta']
        assert metadata['model'] == pin['model']
        assert metadata['revision'] == pin['revision']
        assert metadata['manifest_sha256'] == pin['manifest_sha256']
        predictions = {row['id']: row for row in rows[1:]}
        assert len(predictions) == len(rows) - 1 == 9
        raw_inputs[pin['model']] = predictions
    return sections, raw_inputs


@pytest.fixture(scope='module')
def ordinary_networks(inputs):
    """Independent ordinary three-way vote before any reviewed exclusions."""
    sections, raw_inputs = inputs
    networks = {}
    for page, column, section in ((66, 'left', 's343'), (73, 'right', 's350')):
        section = 'tlg4040-tlg001-local002-' + section
        window = observations.SOURCE_WINDOWS[section]
        prefix = f'photius-bekker-legacy-{page:04d}-{column}-part'
        witnesses = []
        for pin in observations.RAW_FILES:
            parts = raw_inputs[pin['model']]
            text = '\n'.join(parts[key]['raw_prediction'] for key in sorted(parts)
                             if key.startswith(prefix))
            witnesses.append({'id': pin['model'], 'vote_group': pin['model'], 'text': text,
                              'artifact_sha256': pin['sha256']})
        digital = sections[section][window['start']:window['end']]
        witnesses.append({'id': 'digital', 'text': digital,
                          'artifact_sha256': observations.SOURCE_LIBRARY['sha256']})
        merged = merge_witnesses(witnesses)
        supported = [slot for slot in merged['ocr_consensus']['slots'] if any(
            reading['text'] and 'digital' in reading['support'] for reading in slot['readings'])]
        assert len(supported) == len(tokenize(digital))
        networks[page] = supported
    return networks


@pytest.mark.parametrize('observation', observations.OBSERVATIONS,
                         ids=lambda item: item['observation_id'])
def test_exact_model_raw_and_context_bound_full_section_pointer(observation, inputs):
    sections, raw_inputs = inputs
    target = observation['digital_counterpart']
    context = observation['digital_context']
    text = sections[target['section']]
    window = observations.SOURCE_WINDOWS[target['section']]
    assert sha(text.encode()) == window['full_text_sha256']
    assert window['start'] <= target['start'] < target['end'] <= window['end']
    assert text[target['start']:target['end']] == target['original_text']
    assert text[context['start']:context['end']] == context['original_text']
    assert text.count(context['original_text']) == 1
    assert context['start'] <= target['start'] < target['end'] <= context['end']
    assert context['original_text'].count(target['original_text']) == 1
    # Counterparts are whole tokens, not spelling fragments or normalized copies.
    for adjacent in (text[target['start'] - 1:target['start']],
                     text[target['end']:target['end'] + 1]):
        assert not adjacent or not unicodedata.category(adjacent).startswith(('L', 'M'))
    assert len(tokenize(target['original_text'])) == 1
    assert observation['observed_printed_text'] and observation['evidence']
    assert len(observation['raw_spans']) == 2
    for span in observation['raw_spans']:
        pin = next(p for p in observations.RAW_FILES if p['model'] == span['model'])
        assert span['revision'] == pin['revision']
        assert span['model_suffix'] in {'36', '38'}
        assert 'Qwen3.' + span['model_suffix'][-1] + '-' in span['model']
        row = raw_inputs[span['model']][observation['id']]
        assert row['finish_reason'] == 'stop'
        assert sha(canonical(row)) == span['prediction_record_sha256']
        assert sha(row['raw_prediction'].encode()) == span['text_sha256']
        assert row['image_sha256'] == span['source_image_sha256']
        assert row['raw_prediction'][span['start']:span['end']] == span['original_text']
    assert len({span['model'] for span in observation['raw_spans']}) == 2
    assert len({span['source_image_sha256'] for span in observation['raw_spans']}) == 1


@pytest.mark.parametrize('observation', observations.OBSERVATIONS,
                         ids=lambda item: item['observation_id'])
def test_each_pointer_is_the_selected_shared_model_error(observation, inputs, ordinary_networks):
    sections, _ = inputs
    target = observation['digital_counterpart']
    window = observations.SOURCE_WINDOWS[target['section']]
    prefix = sections[target['section']][window['start']:target['start']]
    index = len(tokenize(prefix))
    slot = ordinary_networks[observation['scan_page']][index]
    digital = next(reading for reading in slot['readings'] if 'digital' in reading['support'])
    assert digital['text'] == tokenize(target['original_text'])[0][0]
    agreed = {tokenize(span['original_text'])[0][0] for span in observation['raw_spans']}
    assert len(agreed) == 1
    wrong = agreed.pop()
    assert wrong != digital['text']
    assert slot['selected'] == wrong
    reading = next(reading for reading in slot['readings'] if reading['text'] == wrong)
    assert set(reading['support']) == {span['model'] for span in observation['raw_spans']}


def test_repeated_genitives_and_kai_signs_have_distinct_reviewed_occurrences(inputs):
    sections, _ = inputs
    genitives = [item['digital_counterpart'] for item in observations.OBSERVATIONS
                 if item['digital_counterpart']['original_text'] == 'τοῦ']
    assert [(p['start'], p['end']) for p in genitives] == [(162, 165), (553, 556), (1496, 1499)]
    assert all(p['start'] != sections[p['section']].index('τοῦ') for p in genitives)
    kai = [item['digital_counterpart'] for item in observations.OBSERVATIONS
           if item['observed_printed_text'] == 'ϗ']
    assert [(p['section'].rsplit('-', 1)[1], p['start'], p['original_text']) for p in kai] == [
        ('s343', 712, 'καὶ'), ('s343', 738, 'καὶ'), ('s343', 778, 'καὶ'),
        ('s343', 938, 'καὶ'), ('s350', 3286, 'κὶ'), ('s350', 3399, 'κὶ')]


def test_digital_ligatures_and_line_breaks_stay_literal():
    by_id = {item['observation_id']: item for item in observations.OBSERVATIONS}
    assert by_id['photius-body-18']['digital_counterpart']['original_text'] == 'τῦ'
    wealth = by_id['photius-body-21']
    assert wealth['digital_counterpart']['original_text'] == 'πλῦτον'
    assert wealth['observed_printed_text'] == 'πλοῦτον'
    assert by_id['photius-body-25']['observed_printed_text'] == 'ἀκροα-\nτῶν'
    assert all(s['original_text'] == 'ἀκροω-\nτῶν' for s in by_id['photius-body-25']['raw_spans'])


def test_observation_scope_excludes_earlier_cases_and_masks_do_not_overlap():
    assert isinstance(observations.RECORDS, list)
    assert len(observations.RECORDS) == 25
    assert tuple(observations.RECORDS) == observations.OBSERVATIONS
    spans = {}
    for item in observations.OBSERVATIONS:
        assert item['scan_page'] in (66, 73)
        for span in item['raw_spans']:
            assert span['original_text'] not in {'τέχνης', 'ἰταλοῖς', '7Π.'}
            spans.setdefault((item['id'], span['model']), []).append((span['start'], span['end']))
    assert sum(map(len, spans.values())) == 50
    for values in spans.values():
        ordered = sorted(values)
        assert all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:]))
