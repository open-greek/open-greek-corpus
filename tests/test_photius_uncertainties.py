"""Occurrence resolutions preserve independent mask causes and exact old layers."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import repair_photius_uncertainties as layer


@pytest.fixture
def fixture():
    import pymupdf
    pdf=pymupdf.open()
    for _ in range(169):
        pdf.new_page(width=40,height=40)
    scan=pdf.tobytes();pdf.close()
    text='ὁ λογος καὶ τέλος'
    leaf={'start':2,'end':7,'text':'λογος','classification':'unresolved-source-reading',
          'qualification':'The printed marks need another source.','evidence':'Prior direct scan review.'}
    row={'urn':'photius.bibliotheca','locus':'helladius_chrestomathia_photius_bekker_v2_0169.1',
        'text':text,'analysis_text':'ὁ   καὶ τέλος','source':'ocr','edition':'complete-reviewed',
        'complete_source_review':{'status':'reviewed-with-uncertainty','excluded_spans':[
            {'start':2,'end':7,'text':'λογος','evidence':[deepcopy(leaf)]}]},
        'historical_reading_batches':[{'batch_id':'immutable-old'}]}
    segment={'verification':'uncertain','corrected_start':2,'corrected_end':7,'corrected_text':'λογος',
             'uncertainty':leaf['qualification']}
    compiled={'schema':layer.campaign.COMPILED_SCHEMA,'scope_complete':True,
        'input_pins':{'scan':{'path':'data/source.pdf','sha256':layer.sha(scan)}},
        'rows':[{'locus':row['locus'],'physical_page':169,'segments':[segment]}]}
    decision={'locus':row['locus'],'segment_index':0,'original_text':'λογος','corrected_text':'λόγος',
              'decision':'resolved','bekker_region':[.1,.1,.9,.9],
              'evidence':'The directly reviewed printed acute is clear.','comparisons':[]}
    return {'row':row,'leaf':leaf,'compiled':compiled,'decision':decision,
        'scan':scan,'source_files':{'data/source.pdf':scan},'sources':{},'table':b'# exact authored table\n'}


def authority(fixture, *, row=None, decision=None, scope=None):
    row=fixture['row'] if row is None else row
    decision=fixture['decision'] if decision is None else decision
    before=layer.campaign.canonical(row)+b'\n'
    compiled_raw=layer.encode(fixture['compiled'])
    review,images=layer.compile_review(before,compiled_raw,fixture['table'],
        reviewed_at='2026-10-21T18:10:00Z',decisions=[decision],sources=fixture['sources'],
        source_files=fixture['source_files'],expected_scope=scope)
    return before,layer.encode(review),compiled_raw,images


def save(tmp_path,fixture,*,row=None,decision=None):
    before,review,compiled,images=authority(fixture,row=row,decision=decision)
    outputs,audit=layer.artifacts(before,review,fixture['table'],compiled,images)
    for path,raw in outputs.items():
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True);(tmp_path/path).write_bytes(raw)
    return outputs,audit


def test_resolves_exact_segment_and_preserves_old_tags(fixture,tmp_path):
    outputs,audit=save(tmp_path,fixture)
    row=json.loads(outputs[layer.CORPUS])
    assert row['text']=='ὁ λόγος καὶ τέλος'
    assert row['analysis_text']==row['text']
    assert row['complete_source_review']==fixture['row']['complete_source_review']
    assert row['historical_reading_batches']==fixture['row']['historical_reading_batches']
    assert layer.restore_before_row(row,tmp_path)==fixture['row']
    assert layer.lexical_segments(row,tmp_path)==[row['text']]
    assert audit['counts']['resolved_changed']==1
    assert audit['counts']['baseline_uncertainty_spans']==1
    assert audit['counts']['current_uncertainty_spans']==0
    assert audit['counts']['inherited_remaining_uncertainties']==0
    assert audit['counts']['primary_rows_before']==audit['counts']['primary_rows_after']==1


@pytest.mark.parametrize('classification',['source-fragment','nonbody','digital-reading-disagreement',
    'retained-prior-source-uncertainty','unresolved-source-reading'])
def test_resolving_one_merged_cause_keeps_all_other_causes(fixture,tmp_path,classification):
    row=deepcopy(fixture['row'])
    other={**fixture['leaf'],'classification':classification,'qualification':'Independent cause.'}
    row['complete_source_review']['excluded_spans'][0]['evidence'].append(other)
    outputs,_=save(tmp_path,fixture,row=row)
    new=json.loads(outputs[layer.CORPUS])
    assert 'λόγος' not in new['analysis_text']
    leaves=layer._flatten(new['text'],new[layer.TAG]['excluded_spans'])
    assert len(leaves)==1 and leaves[0]['classification']==classification
    assert leaves[0]['qualification']=='Independent cause.'
    assert leaves[0]['text']=='λόγος'
    assert layer.restore_before_row(new,tmp_path)==row


def test_rebases_following_and_overlapping_masks_without_fabricating_adjacency(fixture,tmp_path):
    row=deepcopy(fixture['row'])
    extra=[{'start':4,'end':7,'text':'γος','classification':'source-fragment'},
           {'start':12,'end':17,'text':'τέλος','classification':'nonbody'}]
    row['complete_source_review']['excluded_spans'].extend(extra)
    decision={**fixture['decision'],'corrected_text':'ἀληθινὸς λόγος'}
    outputs,_=save(tmp_path,fixture,row=row,decision=decision)
    new=json.loads(outputs[layer.CORPUS]);runs=layer.lexical_segments(new,tmp_path)
    assert new['text']=='ὁ ἀληθινὸς λόγος καὶ τέλος'
    assert 'ἀληθινὸς' not in ''.join(runs) and 'τέλος' not in ''.join(runs)
    assert new['analysis_text']==' '.join(runs)
    spans=layer._flatten(new['text'],new[layer.TAG]['excluded_spans'])
    assert spans[0]['text']=='ἀληθινὸς λόγος'
    assert spans[1]['text']=='τέλος'
    assert spans[0]['rebase']['original_exclusion']['text']=='γος'
    assert not any('ὁ καὶ' in s for s in runs)


def test_retained_uncertainty_preserves_every_original_character(fixture,tmp_path):
    d={**fixture['decision'],'decision':'retained-uncertain','corrected_text':'λογος'}
    outputs,audit=save(tmp_path,fixture,decision=d)
    row=json.loads(outputs[layer.CORPUS])
    assert row['text']==fixture['row']['text'] and 'λογος' not in row['analysis_text']
    assert audit['counts']['retained_uncertain']==1
    assert audit['counts']['inherited_remaining_uncertainties']==1


def test_resolved_unchanged_can_release_only_its_reviewed_mask(fixture,tmp_path):
    outputs,audit=save(tmp_path,fixture,decision={**fixture['decision'],'corrected_text':'λογος'})
    row=json.loads(outputs[layer.CORPUS])
    assert row['text']==fixture['row']['text'] and row['analysis_text']==row['text']
    assert audit['counts']['resolved_unchanged']==1


def test_contrary_comparison_is_retained_outside_scalar_counts(fixture,tmp_path):
    import pymupdf
    pix=pymupdf.Pixmap(pymupdf.csRGB,pymupdf.IRect(0,0,40,40));pix.clear_with(0)
    raw=pix.tobytes('png')
    fixture['sources']={'other':{'path':'data/other.png','sha256':layer.sha(raw),'kind':'image'}}
    fixture['source_files']['data/other.png']=raw
    d={**fixture['decision'],'comparisons':[{'source_id':'other','printed_page':1,
          'region':[0,0,1,1],'text':'λόγου','role':'contrary'}]}
    outputs,_=save(tmp_path,fixture,decision=d)
    row=json.loads(outputs[layer.CORPUS])
    assert 'λόγος' in row['text'] and 'λόγος' not in row['analysis_text']
    archive=json.loads(gzip.decompress(outputs[layer.RECORDS]))
    assert archive['decisions'][0]['comparisons'][0]['text']=='λόγου'
    assert len([p for p in outputs if 'source-images' in p.parts])==2


@pytest.mark.parametrize('change',[{'original_text':'λόγος'}, {'segment_index':1},
    {'decision':'retained-uncertain'}, {'evidence':''}, {'bekker_region':[.5,0,.4,1]}])
def test_unreviewed_or_invalid_authority_rejected(fixture,change):
    with pytest.raises((ValueError,KeyError)):
        authority(fixture,decision={**fixture['decision'],**change})


def test_all_declared_uncertainties_must_be_accounted_for(fixture):
    key=(fixture['row']['locus'],0)
    authority(fixture,scope=[key])
    with pytest.raises(ValueError,match='every declared'):
        authority(fixture,scope=[key,(fixture['row']['locus'],1)])
    decision=fixture['decision'];before=layer.campaign.canonical(fixture['row'])+b'\n'
    with pytest.raises(ValueError,match='every declared'):
        layer.compile_review(before,layer.encode(fixture['compiled']),fixture['table'],
            reviewed_at='2026-10-21T18:10:00Z',decisions=[decision,decision],
            sources={},source_files=fixture['source_files'])


def test_changed_source_rejected_before_crops_or_admission(fixture):
    fixture['source_files']['data/source.pdf']+=b'invalidated'
    with pytest.raises(ValueError,match='invalidated'):
        authority(fixture)


def test_missing_exact_uncertainty_cause_cannot_release_a_fragment(fixture):
    row=deepcopy(fixture['row'])
    row['complete_source_review']['excluded_spans'][0]['evidence'][0]['classification']='source-fragment'
    before,review,_,_=authority(fixture,row=row)
    with pytest.raises(ValueError,match='uncertainty cause'):
        layer.plan(before,review)


def test_reversal_and_saved_replay_need_no_live_sources(fixture,tmp_path):
    outputs,audit=save(tmp_path,fixture)
    assert not (tmp_path/'data/source.pdf').exists()
    before=layer.restore_before_bytes(outputs[layer.CORPUS],tmp_path)
    assert before==layer.campaign.canonical(fixture['row'])+b'\n'
    metadata=layer.active_metadata(tmp_path)
    assert metadata['counts']==audit['counts']
    layer.undo(tmp_path)
    assert (tmp_path/layer.CORPUS).read_bytes()==before
    assert layer.active_metadata(tmp_path) is None
    with pytest.raises(FileNotFoundError):
        layer.check(tmp_path)


@pytest.mark.parametrize('field',['text','analysis_text','tag'])
def test_changed_row_or_projection_cannot_restore(fixture,tmp_path,field):
    outputs,_=save(tmp_path,fixture);row=json.loads(outputs[layer.CORPUS])
    if field=='tag': row[layer.TAG]['resolved']=42
    else: row[field]+='x'
    with pytest.raises(ValueError,match='postimage'):
        layer.restore_before_row(row,tmp_path)


def test_different_current_stage_and_frozen_artifact_corruption_rejected(fixture,tmp_path):
    outputs,_=save(tmp_path,fixture)
    (tmp_path/layer.CORPUS).write_bytes(outputs[layer.CORPUS]+b'\n')
    with pytest.raises(ValueError,match='later layers'):
        layer.undo(tmp_path)
    (tmp_path/layer.REVIEW).write_bytes(outputs[layer.REVIEW]+b' ')
    with pytest.raises(ValueError,match='archive changed'):
        layer.restore_before_row(json.loads(outputs[layer.CORPUS]),tmp_path)


def test_unchanged_passages_remain_byte_identical_and_no_new_loci(fixture):
    before,review,_,_=authority(fixture)
    untouched=b'{"locus":"unrelated.1", "text":"unchanged spacing"}\n'
    full=before+untouched;authority_json=json.loads(review)
    authority_json['input_corpus_sha256']=layer.sha(full)
    after,changes,counts=layer.plan(full,layer.encode(authority_json))
    assert after.endswith(untouched) and len(changes)==1
    assert counts['primary_rows_after']==counts['primary_rows_before']==2


def production_fixture(tmp_path,fixture,monkeypatch):
    import repair_photius_context as context
    row=deepcopy(fixture['row'])
    row['photius_context_review']={'excluded_spans':deepcopy(row['complete_source_review']['excluded_spans']),
                                 'authority':'frozen-context'}
    monkeypatch.setattr(context,'lexical_segments',lambda r,root: layer._projection(r['text'],
        layer._flatten(r['text'],r['photius_context_review']['excluded_spans']))[1])
    module=("REVIEWED_AT='2026-10-21T18:10:00Z'\nSOURCES={}\nEXPECTED_SCOPE="+
        repr([(row['locus'],0)])+"\ndef records():\n    return "+repr([fixture['decision']])+"\n").encode()
    from repair_photius_complete_review import REVIEW as complete_review
    for path,raw in {layer.CORPUS:layer.campaign.canonical(row)+b'\n',layer.TABLE:module,
        complete_review:gzip.compress(layer.encode(fixture['compiled']),mtime=0),
        Path('data/source.pdf'):fixture['scan']}.items():
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True);(tmp_path/path).write_bytes(raw)
    return row


def test_production_apply_check_reapply_and_invalidated_source_undo(fixture,tmp_path,monkeypatch):
    old=production_fixture(tmp_path,fixture,monkeypatch)
    before=(tmp_path/layer.CORPUS).read_bytes()
    audit=layer.apply(tmp_path)
    after=(tmp_path/layer.CORPUS).read_bytes()
    assert layer.check(tmp_path)==audit
    assert layer.apply(tmp_path)==audit
    assert (tmp_path/layer.CORPUS).read_bytes()==after
    new=json.loads(after)
    assert new['photius_context_review']==old['photius_context_review']
    (tmp_path/'data/source.pdf').write_bytes(fixture['scan']+b'invalidated source')
    with pytest.raises(ValueError,match='invalidated'):
        layer.check(tmp_path)
    layer.undo(tmp_path)
    assert (tmp_path/layer.CORPUS).read_bytes()==before
    (tmp_path/'data/source.pdf').write_bytes(fixture['scan'])
    assert layer.check(tmp_path) is None
    assert layer.apply(tmp_path)==audit
    assert (tmp_path/layer.CORPUS).read_bytes()==after


def test_production_empty_table_and_missing_context_fail_closed(fixture,tmp_path,monkeypatch):
    production_fixture(tmp_path,fixture,monkeypatch)
    source=(tmp_path/layer.TABLE).read_text()
    (tmp_path/layer.TABLE).write_text(source[:source.index('def records():')]+'def records():\n    return []\n')
    with pytest.raises(ValueError,match='every declared'):
        layer.build(tmp_path)
    (tmp_path/layer.TABLE).write_text(source)
    (tmp_path/layer.CORPUS).write_bytes(layer.campaign.canonical(fixture['row'])+b'\n')
    with pytest.raises(ValueError,match='context predecessor'):
        layer.build(tmp_path)


def test_corresponding_source_crop_pins_change_with_pixels(fixture,monkeypatch):
    import pymupdf
    pdf=pymupdf.open(stream=fixture['scan'],filetype='pdf')
    pdf[168].draw_rect(pymupdf.Rect(5,5,35,35),fill=(0,0,0))
    modified=pdf.tobytes();pdf.close()
    _,first,_,_=authority(fixture)
    fixture['scan']=modified;fixture['source_files']['data/source.pdf']=modified
    fixture['compiled']['input_pins']['scan']['sha256']=layer.sha(modified)
    _,second,_,_=authority(fixture)
    assert json.loads(first)['records'][0]['bekker']['image']['sha256']!=json.loads(second)['records'][0]['bekker']['image']['sha256']


def test_compilation_crop_cache_is_fresh_and_geometry_scoped(fixture,monkeypatch):
    calls=[];real=layer._crop
    def wrapped(raw,kind,page,box):
        calls.append((layer.sha(raw),kind,page,tuple(box)))
        return real(raw,kind,page,box)
    monkeypatch.setattr(layer,'_crop',wrapped)
    authority(fixture);authority(fixture)
    assert len(calls)==2


def test_missing_audit_rejects_published_layer_tag(fixture,tmp_path):
    row=deepcopy(fixture['row']);row[layer.TAG]={'schema':layer.SCHEMA}
    (tmp_path/layer.CORPUS).parent.mkdir(parents=True)
    (tmp_path/layer.CORPUS).write_bytes(layer.campaign.canonical(row)+b'\n')
    with pytest.raises(ValueError,match='no admission audit'):
        layer.check(tmp_path)


def test_same_geometry_with_same_source_bytes_renders_once_per_compilation(fixture,monkeypatch):
    fixture['sources']={'matching':{'path':'data/source.pdf','sha256':layer.sha(fixture['scan']),'kind':'pdf'}}
    d={**fixture['decision'],'comparisons':[{'source_id':'matching','scan_page':169,
        'printed_page':434,'region':fixture['decision']['bekker_region'],
        'text':'λόγος','role':'corroborating'}]}
    calls=[];real=layer._crop
    def wrapped(*args):
        calls.append(args[1:]);return real(*args)
    monkeypatch.setattr(layer,'_crop',wrapped)
    _,review,_,images=authority(fixture,decision=d)
    assert len(calls)==len(images)==1
    record=json.loads(review)['records'][0]
    assert record['bekker']['image']==record['comparisons'][0]['image']
    assert record['bekker']['source_id']!=record['comparisons'][0]['source_id']


def test_renderer_change_invalidates_live_check_without_blocking_undo(fixture,tmp_path,monkeypatch):
    production_fixture(tmp_path,fixture,monkeypatch)
    layer.apply(tmp_path)
    real=layer._crop
    monkeypatch.setattr(layer,'_crop',lambda *args:real(*args)+b'changed renderer recipe')
    with pytest.raises(ValueError,match='no longer reproduces'):
        layer.check(tmp_path)
    layer.undo(tmp_path)


def test_corroborating_label_cannot_conceal_a_different_reading(fixture):
    fixture['sources']={'other':{'path':'data/source.pdf','sha256':layer.sha(fixture['scan']),'kind':'pdf'}}
    d={**fixture['decision'],'comparisons':[{'source_id':'other','scan_page':169,'printed_page':434,
        'region':[0,0,1,1],'text':'λόγου','role':'corroborating'}]}
    with pytest.raises(ValueError,match='corroborating'):
        authority(fixture,decision=d)
