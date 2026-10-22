"""Joint word authority is exact, source-pinned, and never a second attestation."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import photius_final_boundary_observations as boundary
import prepare_photius_editorial_continuation as prepare
import repair_photius_editorial_substitutions as previous


def literal(spec):
    return boundary._record(spec, spec['selection']['units'], boundary.REVIEWED_AT)


def by_id(suffix):
    return next(spec for spec in boundary.SPECS if spec['id'].endswith(suffix))


def inputs(monkeypatch):
    """A real parser/source-token fixture with two rows sharing one word."""
    raw = '<h3>247</h3><h2>419a</h2><td>πρῶτον συνάδει τέλος.</td>'.encode()
    units = prepare.source_document(raw)
    source = {'id': boundary.SOURCE_ID, 'edition': 'Henry', 'citation': 'Photius 4040.001',
              'sha256': hashlib.sha256(raw).hexdigest()}
    known = previous._source_tokens(raw, source)
    index, actual = list(known.values())[1]
    token = {'text': actual['text'], 'refs': deepcopy(actual['refs']), 'source_index': index}
    reading = prepare.attributed_span({'source_id': boundary.SOURCE_ID, 'role': 'chosen',
        'text': token['text'], 'tokens': [token], 'refs': deepcopy(token['refs'])}, units)
    rows = {'a': {'locus': 'a', 'text': 'λέγει συν-'}, 'b': {'locus': 'b', 'text': 'άδει τέλος'}}
    spec = deepcopy(boundary.SPECS[0])
    spec['id'] = 'fixture'
    spec['identities'] = [{'locus': 'b', 'segment_index': 0, 'start': 0, 'end': 4}]
    spec['edits'] = [
        {'locus': 'a', 'start': 6, 'end': 10, 'original_text': 'συν-', 'corrected_text': '',
         'original_row_sha256': boundary._digest(rows['a'])},
        {'locus': 'b', 'start': 0, 'end': 4, 'original_text': 'άδει', 'corrected_text': 'συνάδει',
         'original_row_sha256': boundary._digest(rows['b'])}]
    spec['selection'] = {'first': 0, 'stop': 1, 'units_sha256': boundary._digest(list(units)),
                         'units': list(units)}
    spec['reading'] = reading
    spec['surface_sha256'] = boundary._digest({k: reading[k]
        for k in ('surface', 'separators', 'boundary_suffix')})
    image = b'Exactly source-reviewed pixels.'
    spec['scan']['image_sha256'] = hashlib.sha256(image).hexdigest()
    monkeypatch.setattr(boundary, 'SPECS', [spec])
    monkeypatch.setattr(boundary, 'EXPECTED_SCOPE', frozenset({('b', 0)}))
    monkeypatch.setattr(boundary, 'SOURCE_SHA256', source['sha256'])
    return raw, rows, object(), lambda document, page, region: image


def test_all_fifteen_identities_and_twenty_five_edits_are_exactly_scoped():
    identities = [(i['locus'], i['segment_index']) for spec in boundary.SPECS for i in spec['identities']]
    assert len(identities) == len(set(identities)) == 15
    assert len(boundary.SPECS) == 13
    assert sum(len(s['edits']) for s in boundary.SPECS) == 25
    for spec in boundary.SPECS:
        assert spec['evidence'] and spec['scan'] and spec['contrary_readings']
        for identity in spec['identities']:
            assert len(identity['inherited_record_sha256']) == 64
            assert len(identity['original_segment_sha256']) == 64
            assert any(e['locus'] == identity['locus'] and e['start'] <= identity['start']
                       and identity['end'] <= e['end'] for e in spec['edits'])


def test_joint_words_have_one_owner_and_no_reused_source_tokens():
    refs, indices = [], []
    for spec in boundary.SPECS:
        record = literal(spec)
        assert boundary.validate_record(record) == record
        assert record['disposition'] == 'joint-editorial-word-choice'
        assert record['lexical_eligible'] is True and record['glyph_resolved'] is False
        tokens = record['word_source']['tokens']
        refs += [boundary._digest(t['refs']) for t in tokens]
        indices += [t['source_index'] for t in tokens]
        placed = [i for p in record['source_placements'] for i in p['source_indices']]
        assert placed == [t['source_index'] for t in tokens]
        assert record['superseded_source_refs'] == []
    assert len(refs) == len(set(refs)) == 20
    assert indices == sorted(set(indices))


def test_marginal_five_is_deleted_without_becoming_a_word_suffix():
    spec = by_id('0193.8')
    assert spec['identities'][1]['text_role'] == 'line-number'
    assert spec['identities'][1]['lexical_eligible'] is False
    assert [(e['original_text'], e['corrected_text']) for e in spec['edits']] == [
        ('ἀντι-', 'ἀνεῖται'), ('δ', '')]
    record = literal(spec)
    assert 'ἀνείδη' in str(record['contrary_readings'])
    assert record['word_source']['surface'] == 'ἀνεῖται'


def test_whole_held_row_repairs_missing_suffix_with_exact_source_punctuation():
    spec = by_id('0069.21')
    whole = spec['edits'][1]
    assert whole['start'] == 0 and whole['end'] == len(whole['original_text'])
    assert whole['corrected_text'] == 'σχίζεσθαι. Ἀλλ’ ὅμως, οὕτω μὲν χαρακώσαντες τὸν'
    assert spec['edits'][0]['original_text'] == 'χί-'
    assert len(literal(spec)['source_placements'][0]['source_indices']) == 7
    assert spec['reading']['tokens'][1]['text'] == 'Ἀλλ’'


def test_two_word_choice_is_distributed_without_repeating_its_prefix():
    spec = by_id('0044.26')
    record = literal(spec)
    assert [e['corrected_text'] for e in spec['edits']] == ['μᾶλλον', 'εὐφόρεσαν']
    assert [p['source_indices'] for p in record['source_placements']] == [[196924], [196925]]
    assert 'εἰσώ-' in str(record['contrary_readings'])


def test_false_fragment_is_replaced_without_touching_the_next_row():
    spec = by_id('0170.1')
    assert len(spec['edits']) == 1
    assert spec['edits'][0]['corrected_text'] == 'ἀδικεῖσθαι'
    assert 'next line starts τοῖς' in spec['evidence']


def test_unrelated_fragments_are_outside_authored_edits():
    for spec in boundary.SPECS:
        originals = [e['original_text'] for e in spec['edits']]
        assert all(value not in originals for value in ['ἐγκρατευσά-', 'μεναι', 'συμ-', 'με-'])


def test_fresh_live_sources_and_complete_literal_replay(monkeypatch):
    args = inputs(monkeypatch)
    records = boundary.review_final(*args)
    assert len(records) == 1
    assert boundary.validate_record(records[0]) == records[0]
    before = deepcopy(args[1])
    for edit in records[0]['edits']:
        row = before[edit['locus']]
        row['text'] = row['text'][:edit['start']] + edit['corrected_text'] + row['text'][edit['end']:]
    assert before['a']['text'] == 'λέγει '
    assert before['b']['text'] == 'συνάδει τέλος'
    assert sum(r['text'].count('συνάδει') for r in before.values()) == 1


@pytest.mark.parametrize('field', ['edit', 'row', 'identity', 'evidence', 'refs', 'index',
                                 'surface', 'separator', 'scan', 'contrary', 'role', 'placement'])
def test_public_literal_mutations_fail(monkeypatch, field):
    record = boundary.review_final(*inputs(monkeypatch))[0]
    damaged = deepcopy(record)
    if field == 'edit': damaged['edits'][1]['corrected_text'] = 'συνάδει συνάδει'
    elif field == 'row': damaged['edits'][0]['original_row_sha256'] = '0' * 64
    elif field == 'identity': damaged['identities'][0]['segment_index'] = 1
    elif field == 'evidence': damaged['evidence'] += ' Changed.'
    elif field == 'refs': damaged['readings'][0]['tokens'][0]['refs'][0]['start'] += 1
    elif field == 'index': damaged['readings'][0]['tokens'][0]['source_index'] += 1
    elif field == 'surface': damaged['readings'][0]['surface'] += '.'
    elif field == 'separator': damaged['readings'][0]['separators'].append({'rendered': ';'})
    elif field == 'scan': damaged['scan'][0]['image_sha256'] = '0' * 64
    elif field == 'contrary': damaged['contrary_readings'] = []
    elif field == 'role': damaged['lexical_eligible'] = False
    elif field == 'placement': damaged['source_placements'][0]['source_indices'] = [900]
    with pytest.raises(ValueError): boundary.validate_record(damaged)


def test_changed_source_html_fails_closed(monkeypatch):
    raw, *rest = inputs(monkeypatch)
    with pytest.raises(ValueError, match='HTML changed'):
        boundary.review_final(raw + b' ', *rest)


def test_changed_source_pixels_fail_closed(monkeypatch):
    raw, rows, document, crop = inputs(monkeypatch)
    with pytest.raises(ValueError, match='image changed'):
        boundary.review_final(raw, rows, document, lambda *args: b'Wrong pixels.')


def test_changed_current_preimage_fails_closed(monkeypatch):
    raw, rows, *rest = inputs(monkeypatch)
    rows['a']['text'] += '.'
    with pytest.raises(ValueError, match='row preimage'):
        boundary.review_final(raw, rows, *rest)


def test_changed_context_fails_literal_validation(monkeypatch):
    record = boundary.review_final(*inputs(monkeypatch))[0]
    record['source_context']['units'][0]['text'] += ' ἄλλο'
    with pytest.raises(ValueError, match='source units'):
        boundary.validate_record(record)


def test_duplicated_word_cannot_acquire_a_second_display_owner():
    spec = deepcopy(boundary.SPECS[0])
    spec['edits'][0]['corrected_text'] = spec['reading']['surface']
    with pytest.raises(ValueError, match='complete source words|duplicates or omits'):
        boundary._placements(spec)
