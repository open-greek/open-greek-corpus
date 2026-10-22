"""Elastic occurrence evidence cannot choose by unknown spelling or length."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import photius_remaining_context as remaining


LEFT = 'ἀρχὴ μέση θεὸς'
RIGHT = 'τέλος κύριος λόγος ζωή'


def html(text, codex='230'):
    return (f'<table><tr><td><h3>{codex}</h3><h2>300a</h2><td>{text}'
            '<td class="Y">Μοντέρνα σημείωση</table>').encode()


def scope(text, target, *, locus='row', index=0):
    start = text.index(target)
    row = {'locus': locus, 'urn': 'photius.bibliotheca', 'text': text}
    leaf = {'start': start, 'end': start + len(target), 'text': target,
            'classification': 'unresolved-source-reading'}
    record = {'locus': locus, 'segment_index': index, 'original_text': target,
              'printed_page': 300, 'readings': [],
              'original_segment': {'text_role': 'authorial-body', 'fragments': []}}
    return {'row': row, 'record': record, 'start': start, 'end': start + len(target),
            'excluded_spans': [leaf]}


def locate(value, digital):
    key = value['row']['locus'], value['record']['segment_index']
    return remaining.locate_remaining(html(digital), {key: value})[key]


def test_many_to_many_gap_uses_boundaries_without_unknown_length_vote():
    digital = LEFT + ' νέα λέξις ἄλλη ' + RIGHT
    for target in ['ἄσαφες', 'ἄσαφες φθορά', 'ἄσαφες φθορά χαλεπόν']:
        value = scope(LEFT + ' ' + target + ' ' + RIGHT, target)
        result = locate(value, digital)
        assert result['evidence']['status'] == 'located'
        assert result['readings'][0]['text'] == 'νέα λέξις ἄλλη'
        assert result['readings'][0]['role'] == 'chosen'
        assert result['evidence']['cost'] == 0


def test_equal_anchor_repeats_keep_different_length_gaps_ambiguous():
    text = LEFT + ' ἄσαφες ' + RIGHT
    digital = LEFT + ' νέα ' + RIGHT + ' ' + LEFT + ' νέα λέξις ἄλλη ' + RIGHT
    value = scope(text, 'ἄσαφες')
    value['record']['readings'] = [{'source_id': remaining.SOURCE_ID, 'text': 'νέα', 'refs': []},
                                   {'source_id': remaining.SOURCE_ID, 'text': 'νέα λέξις ἄλλη', 'refs': []}]
    result = locate(value, digital)
    assert all(reading['role'] == 'alternative' for reading in result['readings'])
    assert result['evidence']['status'] != 'located'


def test_nonGreek_unread_interval_is_an_elastic_placeholder():
    result = locate(scope(LEFT + ' 1469 ' + RIGHT, '1469'), LEFT + ' θʹ ' + RIGHT)
    assert result['readings'][0]['text'] == 'θʹ'
    assert result['evidence']['status'] == 'located'


def test_empty_gap_is_retained_as_an_explicit_alternative():
    result = locate(scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες'), LEFT + ' ' + RIGHT)
    assert result['evidence']['status'] == 'held-empty-source-gap'
    assert result['readings'][0]['text'] == ''
    assert result['readings'][0]['role'] == 'alternative'


def test_fewer_than_five_reliable_anchors_are_held():
    value = scope('ἀρχὴ μέση ἄσαφες τέλος ζωή', 'ἄσαφες')
    assert locate(value, 'ἀρχὴ μέση νέα τέλος ζωή')['evidence']['status'] != 'located'


def test_less_than_seventy_percent_reliable_coverage_is_held():
    value = scope(LEFT + ' ἄσαφες τέλος κύριος λόγος ξένος δεύτερος τρίτος τέταρτος', 'ἄσαφες')
    result = locate(value, LEFT + ' νέα τέλος κύριος λόγος')
    assert result['evidence']['status'] != 'located'


def test_clipped_context_still_meets_declared_cost_and_coverage_guards():
    value = scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες')
    digital = 'ἀρχὴ ' + 'πολύς ' * 12 + 'μέση θεὸς νέα ' + RIGHT
    result = locate(value, digital)
    if result['evidence']['status'] == 'located':
        proof = result['evidence']
        assert proof['cost'] * 100 <= 35 * proof['source_tokens'] * remaining.context.GAP_COST
        assert proof['exact_unique_anchors'] * 10 >= 7 * proof['reliable_tokens']


def test_fragment_and_nonbody_cannot_be_expanded_into_whole_words():
    value = scope(LEFT + ' ἀντι- ' + RIGHT, 'ἀντι-')
    value['record']['original_segment']['fragments'] = [{'text': 'ἀντι-'}]
    result = locate(value, LEFT + ' ἀνεῖται ' + RIGHT)
    assert result['readings'] == []
    assert result['evidence']['status'] == 'held-fragment-or-nonbody'
    value['record']['original_segment'].update(fragments=[], text_role='unclassified-small-type')
    assert locate(value, LEFT + ' ἀνεῖται ' + RIGHT)['readings'] == []


def test_a_second_held_interval_is_not_copied_into_the_first():
    text = LEFT + ' ἄσαφες φθορά ' + RIGHT
    first, second = scope(text, 'ἄσαφες'), scope(text, 'φθορά', index=1)
    masks = first['excluded_spans'] + second['excluded_spans']
    first['excluded_spans'] = second['excluded_spans'] = masks
    results = remaining.locate_remaining(html(LEFT + ' νέα λέξις ' + RIGHT),
                                        {('row', 0): first, ('row', 1): second})
    assert all(value['evidence']['status'] != 'located' for value in results.values())


def test_partial_word_returns_whole_extent_without_mutating_source():
    text = LEFT + ' ἄνθρωπον ' + RIGHT
    value = scope(text, 'ἄν')
    original = deepcopy(value)
    result = locate(value, text)
    assert result['readings'][0]['text'] == 'ἄνθρωπον'
    assert result['evidence']['source_extent'] == [value['start'], value['start'] + len('ἄνθρωπον')]
    assert value == original


def test_source_ordered_neighborhood_can_supply_a_missing_left_boundary():
    target = scope('ἄσαφες ' + RIGHT, 'ἄσαφες')
    target['context_rows'] = [{'row': {'locus': 'previous', 'text': LEFT},
                              'excluded_spans': [], 'printed_page': 300},
                             {'row': target['row'], 'excluded_spans': target['excluded_spans'],
                              'printed_page': 300}]
    result = locate(target, LEFT + ' νέα λέξις ' + RIGHT)
    assert result['evidence']['status'] == 'located'
    assert result['evidence']['neighborhood']
    assert result['readings'][0]['text'] == 'νέα λέξις'


def test_wrong_neighborhood_order_does_not_certify_a_target():
    target = scope('ἄσαφες ' + RIGHT, 'ἄσαφες')
    target['context_rows'] = [{'row': target['row'], 'excluded_spans': target['excluded_spans'],
                              'printed_page': 300},
                             {'row': {'locus': 'previous', 'text': LEFT},
                              'excluded_spans': [], 'printed_page': 300}]
    assert locate(target, LEFT + ' νέα ' + RIGHT)['evidence']['status'] != 'located'


def test_unusable_target_omitted_from_optional_neighborhood_stays_held():
    target = scope('ἄσαφες ' + RIGHT, 'ἄσαφες')
    target['context_rows'] = [{'row': {'locus': 'previous', 'text': LEFT},
                              'excluded_spans': [], 'printed_page': 300}]
    assert locate(target, LEFT + ' νέα ' + RIGHT)['evidence']['status'] != 'located'


def test_source_token_already_adopted_cannot_be_used_by_a_second_occurrence():
    target = scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες')
    digital = LEFT + ' νέα ' + RIGHT
    first = locate(target, digital)['readings'][0]
    target['previously_used_source_refs'] = {remaining._sha(first['tokens'][0]['refs'])}
    target['record']['readings'] = [first]
    held = locate(target, digital)
    assert held['readings'] == []
    assert held['evidence']['status'] == 'held-already-admitted-source-ref'
    assert held['evidence']['block_prior_fallback']


def test_two_new_scopes_cannot_claim_one_source_word_twice():
    first = scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες', locus='first')
    second = scope(LEFT + ' φθορά ' + RIGHT, 'φθορά', locus='second')
    result = remaining.locate_remaining(html(LEFT + ' νέα ' + RIGHT),
        {('first', 0): first, ('second', 0): second})
    assert {answer['evidence']['status'] for answer in result.values()} == {'held-reused-new-source-ref'}
    assert all(answer['readings'] == [] and answer['evidence']['block_prior_fallback']
               for answer in result.values())


def test_cross_codex_boundary_is_held():
    raw = (f'<h3>230</h3><h2>300a</h2><td>{LEFT} νέα '
           f'<h3>231</h3><h2>300b</h2><td>{RIGHT}').encode()
    value = scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες')
    result = remaining.locate_remaining(raw, {('row', 0): value})[('row', 0)]
    assert result['evidence']['status'] == 'held-cross-codex-boundaries'


def test_exact_masks_and_current_occurrence_coordinates_are_required():
    value = scope(LEFT + ' ἄσαφες ' + RIGHT, 'ἄσαφες')
    del value['excluded_spans']
    with pytest.raises(ValueError, match='effective masks'):
        locate(value, LEFT + ' νέα ' + RIGHT)


def test_numpy_and_standard_library_preserve_identical_all_optimal_paths(monkeypatch):
    source = ['a', 'b', 'c', 'unknown', 'd', 'e', 'f']
    digital = ['a', 'b', 'c', 'one', 'd', 'e', 'f', 'a', 'b', 'c', 'two', 'three', 'd', 'e', 'f']
    accelerated = remaining.elastic_alignment(source, digital, {3})
    monkeypatch.setattr(remaining.context, '_np', None)
    assert remaining.elastic_alignment(source, digital, {3}) == accelerated
