"""Validate incremental remaining-body observations against exact retained inputs."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unicodedata

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import photius_body_source_observations_remaining as observations
from ocr_consensus import merge_witnesses, tokenize


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


@pytest.fixture(scope='module')
def inputs():
    raw = (ROOT / observations.SOURCE_LIBRARY['path']).read_bytes()
    assert sha(raw) == observations.SOURCE_LIBRARY['sha256']
    library = json.loads(gzip.decompress(raw))
    assert library['id'] == observations.SOURCE_LIBRARY['edition']
    sections = {s['id']: '\n'.join(b['text'] for b in s['blocks'] if b.get('text'))
                for s in library['sections']}
    raw_inputs = {}
    for pin in observations.RAW_FILES:
        raw = (ROOT / pin['path']).read_bytes()
        assert sha(raw) == pin['sha256']
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        metadata = records[0]['_meta']
        assert metadata['model'] == pin['model']
        assert metadata['revision'] == pin['revision']
        assert metadata['manifest_sha256'] == pin['manifest_sha256']
        predictions = {r['id']: r for r in records[1:]}
        assert len(predictions) == len(records) - 1
        raw_inputs[pin['model']] = predictions
    return sections, raw_inputs


@pytest.mark.parametrize('record', observations.RECORDS, ids=lambda r: r['observation_id'])
def test_full_section_context_token_and_all_model_pins(record, inputs):
    sections, raw_inputs = inputs
    target = record['digital_counterpart']
    context = record.get('digital_context')
    if target is not None:
        _check_digital_pointer(target, context, sections)
    else:
        assert record['classification'] in {'marginal-reference', 'neighboring-column-intrusion', 'incomplete-source-coverage'}
    _check_raw_spans(record, raw_inputs)


def _check_digital_pointer(target, context, sections):
    text = sections[target['section']]
    window = observations.SOURCE_WINDOWS[target['section']]
    assert sha(text.encode()) == window['full_text_sha256']
    assert window['start'] <= target['start'] < target['end'] <= window['end']
    assert text[target['start']:target['end']] == target['original_text']
    assert text[context['start']:context['end']] == context['original_text']
    assert text.count(context['original_text']) == 1
    assert context['start'] <= target['start'] < target['end'] <= context['end']
    assert context['original_text'].count(target['original_text']) == 1
    assert len(tokenize(target['original_text'])) == 1
    for adjacent in (text[target['start'] - 1:target['start']], text[target['end']:target['end'] + 1]):
        assert not adjacent or not unicodedata.category(adjacent).startswith(('L', 'M'))


def _check_raw_spans(record, raw_inputs):
    assert 1 <= len(record['raw_spans']) <= 2
    for span in record['raw_spans']:
        pin = next(p for p in observations.RAW_FILES if p['model'] == span['model'])
        assert span['revision'] == pin['revision']
        row = raw_inputs[span['model']][record['id']]
        assert row['finish_reason'] == 'stop'
        assert sha(canonical(row)) == span['prediction_record_sha256']
        assert sha(row['raw_prediction'].encode()) == span['text_sha256']
        assert row['image_sha256'] == span['source_image_sha256']
        assert row['raw_prediction'][span['start']:span['end']] == span['original_text']
    assert len({s['source_image_sha256'] for s in record['raw_spans']}) == 1


@pytest.fixture(scope='module')
def networks(inputs):
    sections, raw_inputs = inputs
    authority = json.loads((ROOT / 'data/ingest_reviews/photius-bekker-body-recovery-remaining.json').read_bytes())
    results = {}
    for region in authority['regions']:
        if region['scan_page'] not in observations.REVIEWED_PAGES:
            continue
        witnesses = []
        for pin in observations.RAW_FILES:
            parts = raw_inputs[pin['model']]
            ids = sorted(key for key in parts if key.startswith(region['id'] + '-part'))
            assert len(ids) == len(region['strip_regions'])
            witnesses.append({'id': pin['model'], 'vote_group': pin['model'],
                'artifact_sha256': sha(pin['model'].encode()),
                'text': '\n'.join(parts[key]['raw_prediction'] for key in ids)})
        bounded = region['source_library_window']
        digital = sections[bounded['section']][bounded['start']:bounded['end']]
        witnesses.append({'id': 'digital', 'text': digital,
                          'artifact_sha256': observations.SOURCE_LIBRARY['sha256']})
        slots = merge_witnesses(witnesses)['ocr_consensus']['slots']
        supported = [s for s in slots if any(r['text'] and 'digital' in r['support'] for r in s['readings'])]
        assert len(supported) == len(tokenize(digital))
        results[region['scan_page']] = (slots, supported)
    return results


@pytest.mark.parametrize('record', observations.RECORDS, ids=lambda r: r['observation_id'])
def test_counterpart_maps_to_the_shared_selected_wrong_reading(record, inputs, networks):
    sections, _ = inputs
    target = record['digital_counterpart']
    if target is None:
        return
    window = observations.SOURCE_WINDOWS[target['section']]
    index = len(tokenize(sections[target['section']][window['start']:target['start']]))
    slots, supported = networks[record['scan_page']]
    slot = supported[index]
    digital = next(r for r in slot['readings'] if 'digital' in r['support'])
    assert digital['text'] == tokenize(target['original_text'])[0][0]
    shared = {tuple(w for w, _ in tokenize(s['original_text'])) for s in record['raw_spans']}
    if len(shared) != 1:
        assert record['scan_page'] == 189
        assert all(len(words) == 1 for words in shared)
        assert all(any(r['text'] == tokenize(span['original_text'])[0][0] and span['model'] in r['support'] for r in slot['readings']) for span in record['raw_spans'])
        return
    words = shared.pop()
    observed_slots = slots[slot['position'] - len(words) + 1:slot['position'] + 1]
    if record['id'].endswith('0100-left-part02') and words == ('Σαρὸν',):
        assert slot['selected'] == 'καΣαρὸν'
        return
    assert [s['selected'] for s in observed_slots] == list(words)
    for s, word in zip(observed_slots, words):
        reading = next(r for r in s['readings'] if r['text'] == word)
        assert set(reading['support']) == {span['model'] for span in record['raw_spans']}


def test_raw_masks_do_not_overlap_and_digital_encodings_remain_literal():
    spans = {}
    for record in observations.RECORDS:
        for span in record['raw_spans']:
            spans.setdefault((record['id'], span['model']), []).append((span['start'], span['end']))
    for values in spans.values():
        ordered = sorted(values)
        for a, b in zip(ordered, ordered[1:]):
            assert a[1] <= b[0] or (a[0] == 0 and a[1] >= b[1])
    digital = {r['digital_counterpart']['original_text'] for r in observations.RECORDS if r['digital_counterpart'] is not None}
    assert {'ϑεραπεύοντας', 'τὲ', 'ἠπείρδ', 'τᾶ', 'ϰὲ'} <= digital
    multi = next(r for r in observations.RECORDS if r['observed_printed_text'] == 'θεραπεύοντας')
    assert {s['original_text'] for s in multi['raw_spans']} == {'ὁ θεραπεύων'}


@pytest.mark.parametrize('record', observations.FRAGMENTS, ids=lambda r: r['observation_id'])
def test_source_fragments_pin_display_without_inventing_complete_words(record, inputs):
    _, raw_inputs = inputs
    assert record['classification'] == 'source-split-word-fragment'
    assert 'digital_counterpart' not in record
    _check_raw_spans(record, raw_inputs)
    if record['scan_page'] == 189:
        assert record['observed_printed_text'] in {'οὕ-', 'τω'}
        assert all(span['original_text'] not in {'οὕτω', 'οὕτως'} for span in record['raw_spans'])
    else:
        assert record['observed_printed_text'] == 'τερον'
        assert all(span['original_text'] == 'τερον' for span in record['raw_spans'])


def test_only_omitted_heading_has_a_complete_strip_hold(inputs):
    _, raw_inputs = inputs
    whole = [r for r in observations.RECORDS if r.get('classification') == 'incomplete-source-coverage']
    assert len(whole) == 1 and whole[0]['id'].endswith('0090-right-part05')
    assert len(whole[0]['raw_spans']) == 1
    span = whole[0]['raw_spans'][0]
    assert span['model_suffix'] == '36'
    assert span['start'] == 0
    assert span['end'] == len(raw_inputs[span['model']][whole[0]['id']]['raw_prediction'])
    assert 'Ἐκ αὐτῆς τῆς μελέτης' in whole[0]['observed_printed_text']


def test_review_covers_all_six_regions_and_preserves_fused_reference_tokens():
    assert observations.REVIEWED_PAGES == (79, 90, 100, 148, 154, 189)
    assert len(observations.RECORDS) == 73 and len(observations.FRAGMENTS) == 3
    fused = [r for r in observations.RECORDS if r['scan_page'] == 189
             and r['observed_printed_text'] in {'χειμῶνα', 'πάντας'}]
    assert len(fused) == 2
    assert [{s['original_text'] for s in r['raw_spans']} for r in fused] == [
        {'Εχίμβρα', 'Πχυμδνα'}, {'ὀλπῶντας', 'Ὀλπίαντας'}]
    assert [r['digital_counterpart']['original_text'] for r in fused] == ['χειμῶνα', 'πάντας']
    edges = [r for r in observations.RECORDS if r.get('classification') == 'neighboring-column-intrusion']
    assert len(edges) == 1 and edges[0]['scan_page'] == 148
    assert {s['original_text'] for s in edges[0]['raw_spans']} == {'ὡς', 'ἵ'}
