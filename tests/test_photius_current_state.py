"""A strict current continuation exposes exact frozen predecessor views."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import photius_current_state as state
import repair_photius_editorial_continuation as continuation
import repair_photius_editorial_substitutions as previous
import check_photius_predecessor as gate
import frequency_projection as frequency


@pytest.fixture
def saved(tmp_path):
    text='ἀρχὴ λογος μένει τέλος'
    a=text.index('λογος'); b=a+len('λογος'); c=text.index('μένει')
    masks=[{'start':a,'end':b,'text':'λογος','classification':'unresolved-source-reading',
            'qualification':'Source marks are unclear.'},
           {'start':c,'end':c+len('μένει'),'text':'μένει','classification':'nonbody'}]
    old={'locus':'historical-row','urn':'photius.bibliotheca','text':text,
         'analysis_text':'ἀρχὴ     τέλος',previous.TAG:{'frozen':'old',
             'excluded_spans':{'path':previous.RECORDS.as_posix(),'locus':'historical-row',
                               'sha256':continuation.sha(continuation.canonical(masks))}}}
    before=(json.dumps(old,ensure_ascii=False)+'\n').encode()
    decision={'locus':old['locus'],'segment_index':5,'start':a,'end':b,'original_text':'λογος',
        'corrected_text':'λόγος','decision':'substitute','reason':'editorial-source',
        'original_row_sha256':continuation.prior.row_sha(old),
        'original_segment':{'verification':'uncertain','corrected_text':'λογος',
                            'uncertainty':'Source marks are unclear.'}}
    review={'schema':continuation.SCHEMA,'input_corpus_sha256':continuation.sha(before),
        'source':{'id':'Greek-source'},'reviewed_at':'2026-10-22T01:00:00Z','records':[decision],
        'prior_exclusions':{old['locus']:masks},'previous_current_uncertainty_spans':1}
    aliases=b'{"frozen":"aliases"}\n'
    outputs,audit=continuation.artifacts(before,aliases,continuation.encode(review),pins={},recipes={})
    for path,raw in {**outputs,state.ALIASES:aliases,Path('data/frozen-source'):b'actual source'}.items():
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    return tmp_path,before,outputs,audit,old


def test_exact_predecessor_corpus_only_overlay_and_no_repository_writes(saved):
    root,before,outputs,_,_=saved
    originals={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with state.predecessor_view(root) as view:
        assert view!=root
        assert (view/state.CORPUS).read_bytes()==before
        assert (root/state.CORPUS).read_bytes()==outputs[state.CORPUS]
        assert (view/'data/frozen-source').is_symlink()
        assert (view/state.ALIASES).read_bytes()==(root/state.ALIASES).read_bytes()
    assert not view.exists()
    assert all((root/path).read_bytes()==raw for path,raw in originals.items())


@pytest.mark.parametrize('defect',['text','tag','archive','aliases'])
def test_changed_postimage_or_authority_fails_even_after_successful_view(saved,defect):
    root,_,outputs,_,_=saved
    with state.predecessor_view(root):pass
    if defect in {'text','tag'}:
        row=json.loads(outputs[state.CORPUS])
        if defect=='text':row['text']+=' forged'
        else:row.pop(state.TAG)
        (root/state.CORPUS).write_bytes(continuation.canonical(row)+b'\n')
    else:
        path=root/(continuation.RECORDS if defect=='archive' else state.ALIASES)
        path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='changed|postimage|admission'):
        with state.predecessor_view(root):pass


def test_archive_change_during_old_validator_is_rejected(saved):
    root,_,_,_,_=saved
    with pytest.raises(ValueError,match='during predecessor'):
        with state.predecessor_view(root):
            (root/continuation.AUDIT).write_bytes(b'changed')


def test_absent_authority_rejects_new_tag_and_exact_predecessor_is_noop(saved,tmp_path):
    root,before,_,_,_=saved
    (root/state.CORPUS).write_bytes(before)
    with state.predecessor_view(root) as view:assert view==root
    (root/continuation.AUDIT).unlink()
    with state.predecessor_view(root) as view:assert view==root
    (root/state.CORPUS).write_bytes(b'{"photius_editorial_continuation":{}}\n')
    with pytest.raises(ValueError,match='no frozen authority'):
        with state.predecessor_view(root):pass


def test_old_gate_receives_checked_view_and_all_frozen_inputs(saved,monkeypatch):
    root,before,_,_,_=saved
    import repair_photius_historical_readings as old
    def check(view):
        assert (view/state.CORPUS).read_bytes()==before
        assert (view/'data/frozen-source').read_bytes()==b'actual source'
        return {'all-old-gates':'checked'}
    monkeypatch.setattr(old,'check',check)
    assert gate.check('historical-readings',root)=={'all-old-gates':'checked'}


def test_newest_lexical_dispatch_preserves_nonbody_bigram_boundary(saved,monkeypatch):
    root,_,outputs,_,_=saved; row=json.loads(outputs[state.CORPUS])
    real=continuation.lexical_segments
    monkeypatch.setattr(continuation,'lexical_segments',lambda row:real(row,root))
    assert frequency.lexical_text(row)==row['analysis_text']
    runs=frequency.FrequencyProjection(root/'data').segments(row)
    assert 'λόγος' in runs[0] and 'τέλος' in runs[1]
    assert not any('λόγος' in run and 'τέλος' in run for run in runs)


def metadata():
    earlier={'uncertainty_review':{'source_review':{'path':'old'},'counts':{
        'baseline_uncertainty_spans':3069,'current_uncertainty_spans':3047}},
        'uncertainty_admission':{'source_review':{'path':'scan'},'counts':{
            'baseline_uncertainty_spans':3047,'resolved':70,'resolved_changed':65,'resolved_unchanged':5,
            'current_uncertainty_spans':2977,'resolved_identities':[{'locus':'scan','segment_index':i} for i in range(70)]}},
        'editorial_substitutions':{'source_review':{'path':'editorial1'},'counts':{
            'scan_uncertainty_spans':2977,'editorially_substituted_spans':2592,
            'unsubstituted_source_uncertainty_spans':385,
            'substituted_identities':[{'locus':'first','segment_index':i} for i in range(2592)]}}}
    earlier['editorial_continuation']={'source_review':{'path':'editorial2'},'counts':{
        'previous_current_uncertainty_spans':385,'newly_editorially_substituted_spans':2,
        'editorially_substituted_spans':2594,'scan_uncertainty_spans':2977,
        'current_uncertainty_spans':383,'unsubstituted_source_uncertainty_spans':383,
        'substituted_identities':[{'locus':'later','segment_index':i} for i in range(2)]}}
    return earlier


def test_cumulative_measurement_preserves_scan_history_and_both_source_refs():
    values=metadata();frozen=deepcopy(values)
    result=state.current_uncertainty_measurement(values)
    assert result['current_uncertainty_spans']==383 and result['editorially_substituted_spans']==2594
    assert result['scan_uncertainty_spans']==2977 and result['scan_resolved_uncertainty_spans']==92
    assert result['source_review']=={'path':'editorial2'}
    assert result['previous_editorial_source_review']=={'path':'editorial1'}
    assert result['scan_source_review']=={'path':'scan'} and values==frozen


@pytest.mark.parametrize('defect',['previous','cumulative','repeat','old-identity'])
def test_disconnected_or_duplicate_continuation_counts_fail(defect):
    values=metadata();counts=values['editorial_continuation']['counts']
    if defect=='previous':counts['previous_current_uncertainty_spans']+=1
    elif defect=='cumulative':counts['editorially_substituted_spans']+=1
    elif defect=='repeat':counts['substituted_identities'][1]=counts['substituted_identities'][0]
    else:counts['substituted_identities'][0]={'locus':'first','segment_index':0}
    with pytest.raises(ValueError,match='Continuation counts'):
        state.current_uncertainty_measurement(values)
