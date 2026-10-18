"""Source-confirmed invented spans abstain without becoming omission votes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ocr_consensus import merge_witnesses, compact_corpus_consensus, restore_corpus_consensus


def witness(identifier, text):
    return {'id':identifier,'text':text,'model':'pinned-checkpoint',
            'artifact_sha256':hashlib.sha256(identifier.encode()).hexdigest()}


def exclude(witness, spans):
    witness = deepcopy(witness)
    text = witness['text']
    previous, retained, excluded = 0, [], []
    for start, end in spans:
        if previous < start:
            retained.append({'start':previous,'end':start,'text':text[previous:start]})
        excluded.append({'start':start,'end':end,'text':text[start:end],
                         'reason':'source-confirmed invented text'})
        previous = end
    if previous < len(text):
        retained.append({'start':previous,'end':len(text),'text':text[previous:]})
    witness['voting_segments'] = retained
    witness['abstention_audit'] = {
        'reviewed_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'source_review':{'path':'data/corpus_changes/example/source-review.json','sha256':'a'*64},
        'excluded_spans':excluded}
    return witness


def internal():
    text = 'ἡ ἀρχὴ νεώτερον ψευδές τὸ τέλος.'
    start = text.index('νεώτερον')
    return exclude(witness('a',text), [(start,start+len('νεώτερον ψευδές'))])


def selected(result, word):
    return next(s for s in result['ocr_consensus']['slots'] if s['selected'] == word)


def test_internal_abstention_uses_other_model_without_an_omission_tie():
    a = internal()
    b = witness('b','ἡ ἀρχὴ μένει τὸ τέλος.')
    result = merge_witnesses([a,b])
    assert result['analysis_text'] == 'ἡ ἀρχὴ μένει τὸ τέλος'
    slot = selected(result,'μένει')
    assert slot['status'] == 'single-witness'
    assert slot['omission_groups'] == []
    assert slot['readings'][0]['support'] == ['b']
    assert len(slot['abstentions']) == 2
    raw = next(w for w in result['ocr_consensus']['witnesses'] if w['id'] == 'a')
    assert raw['text'] == a['text'] and raw['model'] == 'pinned-checkpoint'
    assert raw['voting_segments'] == a['voting_segments']
    assert raw['abstention_audit'] == a['abstention_audit']
    assert 'νεώτερον' not in result['text']
    assert {f['vote_group'] for f in result['ocr_consensus']['voting_fragments']} == {'a'}


def test_repeated_fragments_keep_distinct_ordered_positions_and_one_family_vote():
    text = 'λόγος σοφός ψεῦδος λόγος σοφός'
    start = text.index('ψεῦδος')
    a = exclude(witness('a',text), [(start,start+len('ψεῦδος'))])
    result = merge_witnesses([a,witness('b','λόγος σαφής λόγος σαφής')])
    tied = [s for s in result['ocr_consensus']['slots'] if s['status']=='unresolved']
    assert len(tied) == 2
    assert result['analysis_text'] == 'λόγος λόγος'
    assert all(s['tied_readings'] == ['σαφής','σοφός'] for s in tied)
    assert all(len(r['support_groups']) == 1 for s in tied for r in s['readings'])
    assert len({f['id'] for f in result['ocr_consensus']['voting_fragments']}) == 2


def test_same_family_extra_fragment_witness_cannot_overrule_another_model():
    a = internal()
    a['vote_group'] = 'one-model'
    duplicate_reading = witness('a-other','ἡ ἀρχὴ μένει τὸ τέλος.')
    duplicate_reading['vote_group'] = 'one-model'
    b = witness('b','ἡ ἀρχὴ μένῃ τὸ τέλος.')
    result = merge_witnesses([a,duplicate_reading,b])
    assert any(s['tied_readings'] == ['μένει','μένῃ'] for s in result['ocr_consensus']['slots'])


def test_wholly_bad_witness_abstains_and_preserves_its_full_raw_reading():
    a = witness('a','νεώτερον ψευδές')
    a = exclude(a,[(0,len(a['text']))])
    result = merge_witnesses([a,witness('b','ὁ λόγος σαφής')])
    assert result['analysis_text'] == 'ὁ λόγος σαφής'
    assert all(s['status']=='single-witness' and s['abstentions']==['a']
               for s in result['ocr_consensus']['slots'])
    assert result['ocr_consensus']['witnesses'][0]['text'] == a['text']
    empty = merge_witnesses([a])
    assert empty['text'] == empty['analysis_text'] == ''
    assert empty['ocr_consensus']['slots'] == []


def test_real_omission_within_retained_fragment_still_votes():
    text = 'ὁ λόγος ψεῦδος τὸ τέλος'
    start = text.index('ψεῦδος')
    a = exclude(witness('a',text),[(start,start+len('ψεῦδος'))])
    result = merge_witnesses([a,witness('b','ὁ δὲ λόγος μένει τὸ τέλος')])
    omitted = next(s for s in result['ocr_consensus']['slots'] if 'δὲ' in s['tied_readings'])
    assert omitted['tied_readings'] == ['', 'δὲ']
    assert omitted['omission_groups'] == ['a']
    assert selected(result,'μένει')['omission_groups'] == []


def test_adjacent_retained_slices_do_not_invent_an_abstention_seam():
    a = exclude(witness('a','ὁ λόγος'),[])
    a['voting_segments'] = [{'start':0,'end':2,'text':'ὁ '},
                            {'start':2,'end':7,'text':'λόγος'}]
    result = merge_witnesses([a,witness('b','ὁ δὲ λόγος')])
    omitted = next(s for s in result['ocr_consensus']['slots'] if 'δὲ' in s['tied_readings'])
    assert omitted['omission_groups'] == ['a']
    assert len(result['ocr_consensus']['voting_fragments']) == 1


@pytest.mark.parametrize('damage', ['no-audit','hash','slice','gap','overlap','reorder',
    'no-reason','absolute-review','traversal-review','bad-review-hash','inside-word'])
def test_unreviewed_or_ambiguous_raw_projections_are_rejected(damage):
    a = internal()
    if damage == 'no-audit':
        del a['abstention_audit']
    elif damage == 'hash':
        a['abstention_audit']['reviewed_text_sha256'] = '0'*64
    elif damage == 'slice':
        a['voting_segments'][0]['text'] = 'invented replacement'
    elif damage == 'gap':
        a['abstention_audit']['excluded_spans'] = []
    elif damage == 'overlap':
        a['voting_segments'].append(a['voting_segments'][0])
    elif damage == 'reorder':
        a['voting_segments'].reverse()
    elif damage == 'no-reason':
        a['abstention_audit']['excluded_spans'][0]['reason'] = ''
    elif damage == 'absolute-review':
        a['abstention_audit']['source_review']['path'] = '/source-review.json'
    elif damage == 'traversal-review':
        a['abstention_audit']['source_review']['path'] = 'data/../source-review.json'
    elif damage == 'bad-review-hash':
        a['abstention_audit']['source_review']['sha256'] = 'not-a-hash'
    else:
        a = exclude(witness('a','λόγος'),[(1,3)])
    with pytest.raises(ValueError):
        merge_witnesses([a,witness('b','ἡ ἀρχὴ μένει τὸ τέλος.')])


def test_compaction_round_trips_raw_and_abstention_audit():
    result = merge_witnesses([internal(),witness('b','ἡ ἀρχὴ μένει τὸ τέλος.')])
    compact = compact_corpus_consensus(result,{'path':'data/example/networks.json.gz','key':'page'})
    assert restore_corpus_consensus(compact,result) == result
    assert compact['ocr_consensus']['witnesses'][0]['abstention_audit']['excluded_spans']


def test_one_artifact_cannot_receive_conflicting_review_masks():
    a = internal()
    b = witness('b',a['text'])
    b['artifact_sha256'] = a['artifact_sha256']
    with pytest.raises(ValueError,match='conflicting voting projections'):
        merge_witnesses([a,b])


@pytest.mark.parametrize('left,right,digest', [
    ('ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς','ὁ δὲ λόγος ἔχει πάντα καλῶς',
     'c3c014348525fbf77a4bf860dade36c643f602f7c588948834d9624b29bdba29'),
    ('ἀνдрῶν εἰρῆkenai.','ἀνδρῶν εἰρῆkenai.',
     '5a14b76be422c0abf7af5879053ad9f2b5999923db57409fe11018ba6992583c'),
    ('ὁ λόγος σαφής','ὁ λόγος σοφός',
     '4258dd5461666ffc5c9b5f6d52c67b152deb02c25aa719651f3a64ad546f8fbe'),
    ('λέ-\nγεται κατὰ τὸν λόγον','λέγεται κατὰ τὸν λόγον',
     'a80a55a1024b97f0638bf3b8e94086a8c007fa60b88bee3bb2de57af9395a239'),
    ('ἡ γραφὴ συνεχί-','ἡ γραφὴ συνεχί-',
     '3b235eae3027c4e9fd0341b6d14537a8ef62c65ad3a6a6e11f3dfde3f2a00f25'),
])
def test_ordinary_unsegmented_networks_remain_byte_identical(left,right,digest):
    inputs = [{'id':'a','text':left,'artifact_sha256':'a'*64},
              {'id':'b','text':right,'artifact_sha256':'b'*64}]
    result = merge_witnesses(inputs)
    assert hashlib.sha256(json.dumps(result,ensure_ascii=False).encode()).hexdigest() == digest
