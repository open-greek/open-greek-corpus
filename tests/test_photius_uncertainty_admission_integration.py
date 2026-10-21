"""Newest source authority preserves old stages and lexical gap boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from test_photius_uncertainty_admission import scope, saved
import repair_photius_uncertainty_admission as latest
import repair_photius_uncertainties as prior
import repair_photius_complete_review as complete
import repair_photius_context as context
import frequency_projection as frequency


def test_newest_authority_is_checked_before_each_old_restorer(scope, tmp_path, monkeypatch):
    files, _ = saved(scope, tmp_path)
    new = json.loads(files[latest.CORPUS])
    old = scope['old']
    assert prior._later_bytes(files[latest.CORPUS], tmp_path) == scope['before']
    assert prior._later_row(new, tmp_path) == old
    seen = []
    def old_restore(raw, root):
        assert root == tmp_path and raw == scope['before']
        seen.append('prior'); return b'context-stage'
    monkeypatch.setattr(prior, 'restore_before_bytes', old_restore)
    assert context._later_bytes(files[latest.CORPUS], tmp_path) == b'context-stage'
    assert seen == ['prior']
    monkeypatch.setattr(context, 'restore_before_bytes', lambda raw, root: raw)
    assert complete._later_bytes(files[latest.CORPUS], tmp_path) == b'context-stage'
    damaged = deepcopy(new); damaged['text'] += 'bad'
    with pytest.raises(ValueError, match='postimage'):
        complete._later_row(damaged, tmp_path)


def test_frequency_and_complete_dispatch_to_actual_latest_projection(scope, tmp_path, monkeypatch):
    files, _ = saved(scope, tmp_path)
    row = json.loads(files[latest.CORPUS])
    real = latest.lexical_segments
    monkeypatch.setattr(latest, 'lexical_segments', lambda rec, root=tmp_path: real(rec, root))
    assert frequency.lexical_text(row) == row['analysis_text']
    projection = frequency.FrequencyProjection(tmp_path/'data')
    runs = projection.segments(row)
    assert runs == complete.lexical_segments(row, tmp_path)
    assert 'ἀσαφέστατον μένει' in runs[0]
    assert all(not ('μένει' in run and 'τέλος' in run) for run in runs)
    damaged = deepcopy(row); damaged['analysis_text'] += ' forged'
    with pytest.raises(ValueError, match='postimage|projection'):
        projection.segments(damaged)


def metadata():
    identities = [{'locus': 'row', 'segment_index': i} for i in range(70)]
    return {'uncertainty_review': {'source_review': {'path':'old', 'sha256':'a'*64},
                'counts': {'baseline_uncertainty_spans':3069, 'current_uncertainty_spans':3047}},
            'uncertainty_admission': {'source_review': {'path':'new', 'sha256':'b'*64},
                'counts': {'baseline_uncertainty_spans':3047, 'current_uncertainty_spans':2977,
                           'resolved':70, 'resolved_changed':65, 'resolved_unchanged':5,
                           'resolved_identities':identities}}}


def test_current_measurement_advances_without_mutating_frozen_counts():
    later = metadata(); before = deepcopy(later)
    result = complete.current_uncertainty_measurement(later)
    assert result['current_uncertainty_spans'] == 2977
    assert result['resolved_uncertainty_spans'] == 92
    assert result['source_review'] == later['uncertainty_admission']['source_review']
    assert later == before and later['uncertainty_review']['counts']['current_uncertainty_spans'] == 3047


@pytest.mark.parametrize('defect', ['baseline', 'count', 'duplicate', 'missing-predecessor'])
def test_current_measurement_rejects_disconnected_or_duplicate_authority(defect):
    later = metadata(); counts = later['uncertainty_admission']['counts']
    if defect == 'baseline': counts['baseline_uncertainty_spans'] -= 1
    elif defect == 'count': counts['current_uncertainty_spans'] += 1
    elif defect == 'duplicate': counts['resolved_identities'][-1] = counts['resolved_identities'][0]
    else: del later['uncertainty_review']
    with pytest.raises(ValueError, match='predecessor|Current uncertainty'):
        complete.current_uncertainty_measurement(later)


def test_eligibility_recipe_covers_new_and_reused_mask_generators():
    pins = frequency.projection_recipe_pins()
    for name in ('repair_photius_uncertainty_admission.py', 'prepare_photius_uncertainty_pilot.py',
                 'check_photius_pilot_predecessor.py', 'photius_uncertainty_pilot_observations.py'):
        assert name in pins


def test_quality_publishes_current_measurement_beside_frozen_campaign(tmp_path, monkeypatch):
    import build_ocr_quality_report as quality
    import build_photius_review_observations as authored
    import prepare_photius_review_campaign as campaign
    review_raw = b'frozen complete review'
    for path, raw in ((campaign.MANIFEST,b'scope'),(campaign.OUT,review_raw),
                      (complete.AUDIT,b'frozen audit'),(campaign.CORPUS,b'current corpus')):
        target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    compiled={'campaign_id':'frozen','scope_complete':True,
              'counts':{'uncertainty_exclusion_candidates':3069},'complete_physical_pages':[169],
              'input_pins':{'corpus':{'sha256':'original corpus'}}}
    monkeypatch.setattr(authored,'build',lambda root:({campaign.OUT:review_raw},deepcopy(compiled)))
    monkeypatch.setattr(complete,'active_metadata',lambda root:{'source_review':{'sha256':latest.sha(review_raw)}})
    monkeypatch.setattr(complete,'later_metadata',lambda root:metadata())
    result=quality.complete_review_qualification(tmp_path)
    assert result['counts']['uncertainty_exclusion_candidates']==3069
    assert result['current_measurement']['current_uncertainty_spans']==2977
    assert result['current_measurement']['source_review']==metadata()['uncertainty_admission']['source_review']
    assert result['later_source_reviews']['uncertainty_review']['counts']['current_uncertainty_spans']==3047


def test_latest_measurement_does_not_double_count_source_component_passages():
    import reviewed_manifestations as manifestations
    current=complete.current_uncertainty_measurement(metadata())
    authority={'replaced_component_passages':{'retained':2},
               'counts':{'fully_source_reviewed_rows':2},
               'current_measurement':current,'later_reviews':metadata()}
    result=manifestations._complete_photius_components([
        {'edition':'old','role':'retained','passages':3}],authority)
    assert sum(c['passages'] for c in result)==3
    assert result[-1]['passages']==2
    assert result[-1]['current_measurement']['current_uncertainty_spans']==2977


def editorial_metadata():
    later=metadata()
    later['editorial_substitutions']={'source_review':{'path':'editorial','sha256':'c'*64},
        'counts':{'scan_uncertainty_spans':2977,'editorially_substituted_spans':2,
                  'unsubstituted_source_uncertainty_spans':2975,
                  'substituted_identities':[{'locus':'editorial-row','segment_index':0},
                                            {'locus':'editorial-row','segment_index':1}]}}
    return later


def test_served_uncertainty_count_falls_without_claiming_editorial_scan_verification():
    later=editorial_metadata();before=deepcopy(later)
    result=complete.current_uncertainty_measurement(later)
    assert result['current_uncertainty_spans']==2975
    assert result['scan_uncertainty_spans']==2977
    assert result['scan_resolved_uncertainty_spans']==result['resolved_uncertainty_spans']==92
    assert result['editorially_substituted_spans']==2
    assert result['unsubstituted_source_uncertainty_spans']==2975
    assert result['addressed_uncertainty_spans']==94
    assert result['scan_source_review']==later['uncertainty_admission']['source_review']
    assert result['source_review']==result['editorial_source_review']==later['editorial_substitutions']['source_review']
    assert later==before


@pytest.mark.parametrize('defect',['duplicate','count','scan-baseline','prior-resolved'])
def test_editorial_counts_require_distinct_previously_unresolved_source_occurrences(defect):
    later=editorial_metadata();counts=later['editorial_substitutions']['counts']
    if defect=='duplicate':counts['substituted_identities'][1]=counts['substituted_identities'][0]
    elif defect=='count':counts['unsubstituted_source_uncertainty_spans']+=1
    elif defect=='scan-baseline':counts['scan_uncertainty_spans']+=1
    else:counts['substituted_identities'][0]=later['uncertainty_admission']['counts']['resolved_identities'][0]
    with pytest.raises(ValueError,match='Editorial substitution'):
        complete.current_uncertainty_measurement(later)


def test_actual_editorial_layer_restores_admission_and_preserves_frequency_gaps(scope, tmp_path, monkeypatch):
    import repair_photius_editorial_substitutions as editorial
    from test_photius_uncertainty_admission import save
    scope=deepcopy(scope)
    old=scope['old']; start=old['text'].index('μένει')
    old['photius_uncertainty_review']['excluded_spans'].append({
        'start':start,'end':start+len('μένει'),'text':'μένει','classification':'nonbody-source-material'})
    scope['before']=latest.campaign.canonical(old)+b'\n'
    scope['review']['input_corpus_sha256']=latest.sha(scope['before'])
    scope['review']['pilot_metadata']['input_corpus_sha256']=latest.sha(scope['before'])
    for decision in scope['review']['records']:
        decision['original_row_sha256']=latest.prior.row_sha(old)
    files,_=saved(scope,tmp_path)
    frozen={path:(tmp_path/path).read_bytes() for path in files if path!=latest.CORPUS}
    before=files[latest.CORPUS];row=json.loads(before)
    start=row['text'].index('ἄλλο')
    review={'schema':editorial.SCHEMA,'work':'photius.bibliotheca',
        'input_corpus_sha256':editorial.sha(before),'reviewed_at':'2026-10-21T23:00:00Z',
        'source':{'id':'provided-greek','edition':'Independent Greek edition','citation':'Greek source'},
        'scan_uncertainty_spans':1,'records':[{
            'locus':row['locus'],'segment_index':2,'start':start,'end':start+len('ἄλλο'),
            'original_text':'ἄλλο','corrected_text':'ἕτερον','decision':'substitute',
            'original_row_sha256':editorial.prior.row_sha(row),
            'original_segment':deepcopy(scope['review']['records'][2]['original_segment']),
            'evidence':'Explicit editorial source choice, not a scan verification.'}]}
    outputs,audit=editorial.artifacts(before,scope['aliases'],editorial.encode(review),pins={},recipes={})
    save(tmp_path,outputs)
    after=outputs[editorial.CORPUS];new=json.loads(after)
    assert all((tmp_path/path).read_bytes()==raw for path,raw in frozen.items())
    assert editorial.restore_before_bytes(after,tmp_path)==before
    assert latest.restore_before_bytes(after,tmp_path)==scope['before']
    assert latest.restore_before_row(new,tmp_path)==old
    assert prior._later_bytes(after,tmp_path)==scope['before']
    assert latest.active_metadata(tmp_path)['counts']['resolved']==2
    assert editorial.active_metadata(tmp_path)['counts']['editorially_substituted_spans']==1
    real=editorial.lexical_segments
    monkeypatch.setattr(editorial,'lexical_segments',lambda record,root=tmp_path:real(record,root))
    assert frequency.lexical_text(new)==new['analysis_text']
    runs=frequency.FrequencyProjection(tmp_path/'data').segments(new)
    assert complete.lexical_segments(new,tmp_path)==runs
    assert all(not ('ἀσαφέστατον' in run and 'ἕτερον' in run) for run in runs)
    assert 'μένει' not in ''.join(runs)
    damaged=deepcopy(new);damaged['photius_editorial_substitution']['excluded_spans']=[]
    with pytest.raises(ValueError,match='postimage'):
        latest.restore_before_row(damaged,tmp_path)
