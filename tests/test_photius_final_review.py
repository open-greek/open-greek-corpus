"""Joint words count once, independent causes survive, and exact undo is literal."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import repair_photius_final_review as final


def case():
    rows = [{'locus':'a','text':'λόγος κατα-','analysis_text':'λόγος ',
             'complete_source_review':{'unchanged':'source judgment'}},
            {'locus':'b','text':'σκευασθεῖσαι τέλος','analysis_text':' τέλος'}]
    identities = [{'locus':'a','segment_index':0},{'locus':'b','segment_index':0}]
    edits = [{'locus':'a','start':6,'end':11,'original_text':'κατα-',
              'corrected_text':'κατασκευασθεῖσαι','original_row_sha256':final.prior.row_sha(rows[0])},
             {'locus':'b','start':0,'end':12,'original_text':'σκευασθεῖσαι',
              'corrected_text':'','original_row_sha256':final.prior.row_sha(rows[1])}]
    # Use source lengths, including polytonic code points, as literal offsets.
    edits[1]['end'] = len(edits[1]['original_text'])
    masks = {}
    for edit in edits:
        masks[edit['locus']] = [{'start':edit['start'],'end':edit['end'],
            'text':edit['original_text'],'classification':'unresolved-source-reading',
            'qualification':'Uncertain original.'},
            {'start':edit['start'],'end':edit['end'],'text':edit['original_text'],
             'classification':'source-confirmed-word-fragment','side':'trailing'}]
    record = {'authority':'authored-test','identities':identities,'edits':edits,
              'disposition':'joint-editorial-word-choice','text_role':'authorial-body',
              'lexical_eligible':True,'evidence':'An exact two-row source word.',
              'reviewed_at':'2026-10-22T00:30:00Z'}
    review = {'schema':final.SCHEMA,'work':'photius.bibliotheca','source':{'id':'test'},
        'reviewed_at':record['reviewed_at'],'records':[record],'prior_exclusions':masks,
        'previous_current_uncertainty_spans':2,'input_pins':{},'recipe_sha256':{},
        'identities':[{**i,'start':e['start'],'end':e['end'],
                       'original_segment':{'uncertainty':'Uncertain original.'}}
                      for i,e in zip(identities,edits)]}
    before = b''.join(final.canonical(r)+b'\n' for r in rows)
    review['input_corpus_sha256'] = final.sha(before)
    return before,review


def save(tmp_path,before,review):
    authored = {k:v for k,v in review.items() if k not in
                {'prior_exclusions','identities','previous_current_uncertainty_spans'}}
    files,audit = final.artifacts(before,b'{}\n',final.encode(review),final.encode(authored))
    for p,raw in {**files,final.ALIASES:b'{}\n'}.items():
        (tmp_path/p).parent.mkdir(parents=True,exist_ok=True)
        (tmp_path/p).write_bytes(raw)
    return files,audit


def test_joint_word_has_one_owner_and_literal_reversal(tmp_path):
    before,review = case();files,audit = save(tmp_path,before,review)
    rows = list(map(json.loads,files[final.CORPUS].splitlines()))
    assert [r['text'] for r in rows] == ['λόγος κατασκευασθεῖσαι',' τέλος']
    assert ' '.join(r['analysis_text'] for r in rows).split().count('κατασκευασθεῖσαι') == 1
    assert rows[0]['complete_source_review'] == {'unchanged':'source judgment'}
    assert audit['counts']['resolved_uncertainty_spans'] == 2
    assert audit['counts']['current_uncertainty_spans'] == 0
    assert audit['counts']['primary_rows_after'] == 2
    assert final.restore_before_bytes(files[final.CORPUS],tmp_path) == before
    assert final.restore_before_row(rows[0],tmp_path) == json.loads(before.splitlines()[0])
    assert final.lexical_segments(rows[0],tmp_path) == ['λόγος κατασκευασθεῖσαι']
    final.undo(tmp_path)
    assert (tmp_path/final.CORPUS).read_bytes() == before
    assert final.active_metadata(tmp_path) is None


def test_unrelated_exclusion_is_rebased_and_preserved():
    before,review = case()
    review['prior_exclusions']['b'].append({'start':13,'end':18,'text':'τέλος',
                                          'classification':'independent-editorial-supply'})
    # The literal final token starts after the full source suffix and a space.
    leaf = review['prior_exclusions']['b'][-1]
    row = json.loads(before.splitlines()[1]);leaf['start'] = row['text'].index('τέλος')
    leaf['end'] = len(row['text'])
    after,changes,_ = final.plan(before,final.encode(review))
    assert json.loads(after.splitlines()[1])['analysis_text'].strip() == ''
    leaves = changes[1]['remaining_exclusion_causes']
    assert leaves == [{**leaf,'start':1,'end':6}]


def test_reference_is_classified_without_becoming_a_greek_word(tmp_path):
    before,review = case();r = review['records'][0]
    r.update(disposition='exclude-marginal-reference',text_role='marginal-reference',lexical_eligible=False)
    for edit in r['edits']:
        edit['corrected_text'] = edit['original_text']
    files,audit = save(tmp_path,before,review)
    assert audit['counts']['nonlexically_classified_spans'] == 2
    assert audit['counts']['newly_editorially_substituted_spans'] == 0
    assert audit['counts']['lexical_admitted_identities'] == []
    for row in map(json.loads,files[final.CORPUS].splitlines()):
        assert 'κατα-' not in row['analysis_text'] and 'σκευασθεῖσαι' not in row['analysis_text']


def test_removed_nonlexical_interval_retires_zero_width_causes_with_evidence():
    before,review = case();record = review['records'][0]
    record.update(disposition='exclude-marginal-reference',text_role='marginal-reference',lexical_eligible=False)
    for edit in record['edits']:
        edit['corrected_text'] = ''
    after,changes,counts = final.plan(before,final.encode(review))
    assert [r['text'] for r in map(json.loads,after.splitlines())] == ['λόγος ',' τέλος']
    assert counts['nonlexically_classified_spans'] == 2
    for change in changes:
        assert not change['excluded_spans']
        assert any(c.get('retirement_reason') for c in change['retired_exclusion_causes'])


@pytest.mark.parametrize('defect',['missing','duplicate','overlap','original','row-hash'])
def test_replay_rejects_broken_identity_or_preimage(defect):
    before,review = case();r = review['records'][0]
    if defect == 'missing':r['identities'].pop()
    elif defect == 'duplicate':r['identities'].append(deepcopy(r['identities'][0]))
    elif defect == 'overlap':r['edits'].append(deepcopy(r['edits'][0]))
    elif defect == 'original':r['edits'][0]['original_text'] = 'ἄλλο'
    else:r['edits'][0]['original_row_sha256'] = '0'*64
    with pytest.raises(ValueError):
        final.plan(before,final.encode(review))


@pytest.mark.parametrize('path',[final.BEFORE,final.BEFORE_ALIASES,final.REVIEW,final.RECORDS,final.SOURCE_REVIEW])
def test_undo_rejects_modified_archive(tmp_path,path):
    before,review = case();files,_ = save(tmp_path,before,review)
    (tmp_path/path).write_bytes((tmp_path/path).read_bytes()+b'changed')
    with pytest.raises(ValueError,match='artifact changed'):
        final.restore_before_bytes(files[final.CORPUS],tmp_path)


@pytest.mark.parametrize('defect',['text','analysis','old-source-judgment','new-tag'])
def test_projection_rejects_unrecorded_row_mutation(tmp_path,defect):
    before,review = case();files,_ = save(tmp_path,before,review)
    row = json.loads(files[final.CORPUS].splitlines()[0])
    if defect == 'text':row['text'] += ' ἄλλο'
    elif defect == 'analysis':row['analysis_text'] += ' ἄλλο'
    elif defect == 'old-source-judgment':row['complete_source_review'] = {}
    else:row[final.TAG]['reviewed_at'] = 'changed'
    with pytest.raises(ValueError,match='postimage'):
        final.lexical_segments(row,tmp_path)


def test_independent_partial_cause_cannot_be_silently_retired():
    before,review = case()
    review['prior_exclusions']['a'].append({'start':0,'end':9,'text':'λόγος κατ',
                                          'classification':'independent-source-cause'})
    with pytest.raises(ValueError,match='independent exclusion'):
        final.plan(before,final.encode(review))


def test_missing_authority_and_unrecognized_postimage_are_rejected(tmp_path):
    with pytest.raises(ValueError,match='no authority'):
        final.restore_before_bytes(b'{"photius_final_review":{}}',tmp_path)
    before,review = case();save(tmp_path,before,review)
    with pytest.raises(ValueError,match='postimage'):
        final.restore_before_bytes(before+b'changed',tmp_path)


def compile_case(monkeypatch):
    from types import SimpleNamespace
    before,review = case()
    authored = {k:v for k,v in review.items() if k not in
                {'prior_exclusions','identities','previous_current_uncertainty_spans'}}
    rows = {r['locus']:r for r in map(json.loads,before.splitlines())}
    scopes = {(i['locus'],i['segment_index']):{'start':i['start'],'end':i['end'],
        'row':rows[i['locus']],'record':{'original_segment':i['original_segment']}}
        for i in review['identities']}
    expected = deepcopy(authored['records'][0]);expected.pop('authority')
    module = SimpleNamespace(validate_record=lambda r:deepcopy(expected))
    monkeypatch.setitem(sys.modules,'authored-test',module)
    monkeypatch.setattr(final,'MODULES',('authored-test',))
    monkeypatch.setattr(final,'scope',lambda *args:deepcopy(scopes))
    monkeypatch.setattr(final,'_row_masks',lambda r,root:deepcopy(review['prior_exclusions'][r['locus']]))
    monkeypatch.setattr(final,'SOURCE_WITNESS_SHA256',final.witness_fingerprint(authored))
    return before,authored


def test_compile_binds_full_authored_decision_packet(monkeypatch):
    before,authored = compile_case(monkeypatch)
    result = final.compile_review(before,authored)
    assert result['previous_current_uncertainty_spans'] == 2
    assert len(result['prior_exclusions']) == 2


@pytest.mark.parametrize('defect',['source','spelling','punctuation','source-index','timestamp'])
def test_coordinated_source_packet_changes_fail(monkeypatch,defect):
    before,authored = compile_case(monkeypatch)
    if defect == 'source':authored['source']['id'] = 'other'
    elif defect == 'spelling':authored['records'][0]['edits'][0]['corrected_text'] = 'ἕτερος'
    elif defect == 'punctuation':authored['records'][0]['edits'][0]['corrected_text'] += '.'
    elif defect == 'source-index':authored['records'][0]['source_index'] = 12345
    else:authored['records'][0]['reviewed_at'] = '2026-10-22T00:40:00Z'
    with pytest.raises(ValueError,match='fingerprint'):
        final.compile_review(before,authored)
