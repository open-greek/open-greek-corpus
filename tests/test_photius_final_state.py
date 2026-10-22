"""Final review preserves exact predecessors and separate lexical dispositions."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import photius_current_state as state
import repair_photius_final_review as final
import frequency_projection as frequency
import test_photius_current_state as prior_tests

@pytest.fixture
def stacked(tmp_path):
 root,old_before,old_outputs,_,_=prior_tests.saved.__wrapped__(tmp_path)
 before=old_outputs[state.CORPUS];row=json.loads(before);start=row['text'].index('μένει');end=start+len('μένει')
 prior_record=json.loads(final.gzip.decompress((root/final.previous.RECORDS).read_bytes()))
 identity={'locus':row['locus'],'segment_index':9}
 edit={'locus':row['locus'],'start':start,'end':end,'original_text':'μένει','corrected_text':'μένει','original_row_sha256':final.prior.row_sha(row)}
 record={'authority':'independent-fixture','identities':[identity],'edits':[edit],
         'disposition':'exclude-marginal-reference','text_role':'marginal-reference','lexical_eligible':False,
         'evidence':'An explicitly reviewed nonlexical fixture.','reviewed_at':'2026-10-22T00:30:00Z'}
 review={'schema':final.SCHEMA,'work':'photius.bibliotheca','source':{'id':'fixture'},'reviewed_at':record['reviewed_at'],
 'records':[record],'prior_exclusions':{row['locus']:prior_record['excluded_spans']},'previous_current_uncertainty_spans':1,
 'input_pins':{},'recipe_sha256':{},'identities':[{**identity,'start':start,'end':end,'original_segment':{'uncertainty':'Not an uncertainty cause.'}}],
 'input_corpus_sha256':final.sha(before)}
 files,audit=final.artifacts(before,(root/final.ALIASES).read_bytes(),final.encode(review),b'{}\n')
 for p,raw in files.items():(root/p).parent.mkdir(parents=True,exist_ok=True);(root/p).write_bytes(raw)
 return root,old_before,before,files,audit

def test_nested_exact_predecessor_views_and_no_actual_mutations(stacked):
 root,old_before,before,files,_=stacked
 originals={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
 with state.continuation_view(root) as view:
  assert (view/state.CORPUS).read_bytes()==before
  assert (root/state.CORPUS).read_bytes()==files[state.CORPUS]
 with state.predecessor_view(root) as view:assert (view/state.CORPUS).read_bytes()==old_before
 assert all((root/p).read_bytes()==raw for p,raw in originals.items())
 assert state.continuation_metadata(root)['counts']['newly_editorially_substituted_spans']==1
 assert state.final_metadata(root)['counts']['nonlexically_classified_spans']==1

@pytest.mark.parametrize('kind',['aliases','text','archive','orphan'])
def test_final_authority_or_postimage_tampering_is_rejected(stacked,kind):
 root,_,_,files,_=stacked
 with state.continuation_view(root):pass
 if kind=='orphan':(root/final.AUDIT).unlink()
 else:
  path=state.ALIASES if kind=='aliases' else state.CORPUS if kind=='text' else final.REVIEW
  target=root/path;target.write_bytes(target.read_bytes()+b'changed')
 with pytest.raises(ValueError):
  with state.continuation_view(root):pass

def test_final_archive_mutation_during_predecessor_validation_is_rejected(stacked):
 root,_,_,_,_=stacked
 with pytest.raises(ValueError,match='during predecessor'):
  with state.continuation_view(root):(root/final.SOURCE_REVIEW).write_bytes(b'changed')

def test_newest_frequency_projection_preserves_excluded_adjacency(stacked,monkeypatch):
 root,_,_,files,_=stacked;row=json.loads(files[state.CORPUS]);original=final.lexical_segments
 monkeypatch.setattr(final,'lexical_segments',lambda row:original(row,root))
 assert frequency.lexical_text(row)==row['analysis_text']
 runs=frequency.FrequencyProjection(root/'data').segments(row)
 assert len(runs)==2 and not any('λόγος' in run and 'τέλος' in run for run in runs)

def metadata():
 earlier=prior_tests.metadata()
 earlier['final_review']={'source_review':{'path':'final'},'counts':{
 'previous_current_uncertainty_spans':383,'current_uncertainty_spans':381,'resolved_uncertainty_spans':2,
 'resolved_identities':[{'locus':'new-body','segment_index':0},{'locus':'new-reference','segment_index':0}],
 'lexical_resolution_identities':[{'locus':'new-body','segment_index':0}],
 'nonlexical_resolution_identities':[{'locus':'new-reference','segment_index':0}],
 'lexical_admitted_identities':[],'newly_editorially_substituted_spans':1,
 'nonlexically_classified_spans':1,'editorially_substituted_spans':2595,'scan_uncertainty_spans':2977,
 'resolved_by_text_role':{'authorial-body':1,'marginal-reference':1}}}
 return earlier

def test_nonlexical_classification_never_increases_editorial_word_count():
 inputs=metadata();before=deepcopy(inputs);m=state.current_uncertainty_measurement(inputs)
 assert m['current_uncertainty_spans']==381 and m['editorially_substituted_spans']==2595
 assert m['scan_uncertainty_spans']==2977 and m['scan_resolved_uncertainty_spans']==92
 assert m['final_review_lexical_resolution_spans']==1 and m['final_review_lexically_admitted_spans']==0
 assert m['nonlexically_classified_spans']==1 and m['source_review']=={'path':'final'}
 assert inputs==before

def test_new_scan_backed_dispositions_remain_separate_from_historical_scan_counts():
 values=metadata();counts=values['final_review']['counts']
 counts['new_scan_backed_dispositions']=1
 counts['dispositions']={'editorial-word-choice':1,'exclude-marginal-reference':1,'held':381}
 result=state.current_uncertainty_measurement(values)
 assert result['final_review_scan_backed_dispositions']==1
 assert result['scan_uncertainty_spans']==2977 and result['scan_resolved_uncertainty_spans']==92
 assert result['final_review_dispositions']==counts['dispositions']
 result['final_review_dispositions']['editorial-word-choice']=9
 assert counts['dispositions']['editorial-word-choice']==1

@pytest.mark.parametrize('value',[-1,True,'3'])
def test_invalid_scan_backed_disposition_count_fails(value):
 values=metadata();values['final_review']['counts']['new_scan_backed_dispositions']=value
 with pytest.raises(ValueError):state.current_uncertainty_measurement(values)

@pytest.mark.parametrize('kind',['duplicate','partition','admission','old-id','roles','cumulative','bool','scan'])
def test_invalid_final_count_accounting_is_rejected(kind):
 values=metadata();c=values['final_review']['counts']
 if kind=='duplicate':c['resolved_identities'].append(c['resolved_identities'][0])
 elif kind=='partition':c['lexical_resolution_identities'].append(c['nonlexical_resolution_identities'][0])
 elif kind=='admission':c['lexical_admitted_identities']=c['nonlexical_resolution_identities']
 elif kind=='old-id':c['resolved_identities'][0]=c['lexical_resolution_identities'][0]={'locus':'first','segment_index':1}
 elif kind=='roles':c['resolved_by_text_role']['marginal-reference']=0
 elif kind=='cumulative':c['editorially_substituted_spans']+=1
 elif kind=='bool':c['newly_editorially_substituted_spans']=True
 else:c['scan_uncertainty_spans']-=1
 with pytest.raises(ValueError):state.current_uncertainty_measurement(values)
