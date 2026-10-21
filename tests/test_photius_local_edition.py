import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import compare_photius_local_edition as subject


def edition(text, column='435b'):
    parser = subject.EditionHTML()
    parser.feed(f'<h3>248</h3><h2>{column}</h2><table><td class="Y">25</td><td>{text}</td></table>')
    return subject.tokenize(parser.units)


def keys(text):
    return [subject.normalize(m.group()) for m in subject.WORD.finditer(text)]


def test_column_labels_and_original_offsets_survive():
    ts = edition('λέξις ἑτέρα')
    assert ts[0]['refs'][0]['bekker'] == '435b'
    assert ts[0]['refs'][0]['codex'] == '248'
    assert ts[0]['refs'][0]['start'] == 0
    assert ts[1]['refs'][0]['start'] == 6
    assert len(ts) == 2


def test_line_number_cells_do_not_become_greek_tokens():
    parser = subject.EditionHTML()
    parser.feed('<h2>435a</h2><td class="Y">κε</td><td>λόγος</td><td class="Y">κϛ</td><td>ἄλλος</td>')
    assert [t['text'] for t in subject.tokenize(parser.units)] == ['λόγος', 'ἄλλος']


def test_printed_line_hyphen_joins_and_preserves_both_offsets():
    parser = subject.EditionHTML()
    parser.feed('<h2>435a</h2><td>ἐπι-</td><td class="Y">25</td><td>φαίνεσθαι λέξις</td>')
    tokens = subject.tokenize(parser.units)
    assert tokens[0]['text'] == 'ἐπιφαίνεσθαι'
    assert len(tokens[0]['refs']) == 2
    assert tokens[1]['text'] == 'λέξις'


def test_normalization_is_search_only():
    tokens = edition('ΛΌΓΟΣ')
    assert tokens[0]['text'] == 'ΛΌΓΟΣ'
    assert tokens[0]['key'] == 'λογοσ'


def test_match_uses_only_flanks_and_returns_exact_candidate():
    m = subject.Matcher(edition('ἕνα δύο τρία Διαφορά τέσσερα πέντε ἕξ'))
    result = m.match(435, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))
    assert result['match_status'] == 'unique'
    assert result['candidates'][0]['reading'] == 'Διαφορά'
    assert result['anchor_count'] == 6


def test_equal_best_occurrences_remain_tied():
    phrase = 'ἕνα δύο τρία λέξις τέσσερα πέντε ἕξ'
    m = subject.Matcher(edition(phrase+' · '+('ἄλλος '*13)+phrase))
    result = m.match(435, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))
    assert result['match_status'] == 'tied'
    assert result['match_count'] == 2
    assert len(result['candidates']) == 2


def test_short_context_and_distant_page_fail_closed():
    m = subject.Matcher(edition('ἕνα δύο τρία λέξις τέσσερα πέντε ἕξ'))
    assert m.match(435, keys('δύο τρία'), keys('τέσσερα πέντε ἕξ'))['match_status'] == 'unmatched'
    assert m.match(439, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))['match_status'] == 'unmatched'
    assert m.match(435, keys('δύο τρία'), keys('τέσσερα πέντε'), min_side=2)['match_status'] == 'unique'


def test_gap_limit_and_order():
    text = 'ἕνα δύο τρία '+('λέξις '*13)+'τέσσερα πέντε ἕξ'
    m = subject.Matcher(edition(text))
    assert m.match(435, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))['match_status'] == 'unmatched'
    m = subject.Matcher(edition('τέσσερα πέντε ἕξ λέξις ἕνα δύο τρία'))
    assert m.match(435, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))['match_status'] == 'unmatched'


def test_anchors_do_not_jump_over_unverified_words():
    ts = [{'text': str(i), 'key': str(i), 'start': i*2, 'end': i*2+1} for i in range(9)]
    left, right = subject.verified_flanks(ts, {0, 1, 3, 5, 7, 8}, 8, 9)
    assert left == ['3']  # index2 interrupts the left flank
    assert right == ['5']  # index6 interrupts the right flank


def test_compilation_ignores_uncertain_target_spelling_and_strips_private_text():
    def compiled(target):
        segments = [{'verification': 'verified', 'scan': {'observed_text': 'ἕνα δύο τρία '}},
                    {'verification': 'uncertain', 'scan': {'observed_text': target}},
                    {'verification': 'verified', 'scan': {'observed_text': ' τέσσερα πέντε ἕξ'}}]
        return gzip.compress(json.dumps({'rows': [{'locus': 'test.1', 'printed_page': 435,
                                                  'segments': segments}]}).encode())
    context = gzip.compress(json.dumps({'rows': [{'locus': 'test.1', 'context': {
        'reliable_source_indices': [0, 1, 2, 4, 5, 6]}}]}).encode())
    prior = json.dumps({'records': []}).encode()
    html = '<h3>248</h3><h2>435b</h2><td>ἕνα δύο τρία Διαφορά τέσσερα πέντε ἕξ</td>'.encode()
    public, private = subject.compare(html, compiled('ἄγνωστο'), context, prior)
    changed, _ = subject.compare(html, compiled('θόρυβος'), context, prior)
    assert public['records'] == changed['records']
    assert public['records'][0]['match_status'] == 'unique'
    assert 'Διαφορά' not in json.dumps(public, ensure_ascii=False)
    assert private['records'][0]['candidates'][0]['reading'] == 'Διαφορά'
    assert private['records'][0]['candidates'][0]['refs'][0]['bekker'] == '435b'
    public_after, _ = subject.compare(html, compiled('ἄγνωστο'), context,
        json.dumps({'records': [{'locus': 'test.1', 'segment_index': 1, 'decision': 'resolved'}]}).encode())
    assert public_after['records'] == []


def test_rejects_unsupported_anchor_policy():
    with pytest.raises(ValueError, match='two or three'):
        subject.Matcher([]).match(435, [], [], min_side=1)


def test_same_line_data_nodes_have_distinct_recoverable_positions():
    parser = subject.EditionHTML()
    parser.feed('<h2>435a</h2><td>λόγος</td><td>ἄλλος</td>')
    tokens = subject.tokenize(parser.units)
    first, second = [t['refs'][0] for t in tokens]
    assert first['html_line'] == second['html_line'] == 1
    assert first['start'] == second['start'] == 0
    assert first['html_column'] != second['html_column']
    assert first['unit_index'] != second['unit_index']


def test_tied_empty_gaps_retain_locations_and_both_anchor_pointers():
    phrase = 'ἕνα δύο τρία τέσσερα πέντε ἕξ'
    matcher = subject.Matcher(edition(phrase+' '+('ἄλλος '*13)+phrase))
    result = matcher.match(435, keys('ἕνα δύο τρία'), keys('τέσσερα πέντε ἕξ'))
    assert result['match_count'] == 2
    a, b = result['candidates']
    assert a['reading'] == b['reading'] == ''
    assert a['refs'] == b['refs'] == []
    assert a['location']['token_start'] == a['location']['token_end']
    assert b['location']['token_start'] == b['location']['token_end']
    assert a['location'] != b['location']
    assert a['left_refs'] != b['left_refs']
    assert a['right_refs'] != b['right_refs']
