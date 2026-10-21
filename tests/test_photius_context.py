"""Context annotation never supplies source-text correction authority."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import prepare_photius_review_campaign as campaign
import repair_photius_complete_review as complete
import repair_photius_context as layer

STAMP = '2026-10-21T20:00:00Z'


def record(text, *, observed=None, uncertain=None):
    observed = observed or text
    assert observed==text or uncertain is None
    original = {'urn':'photius.bibliotheca','locus':'helladius_chrestomathia_photius_bekker_v2_0003.1',
        'text':text,'language':'grc','source':'ocr','prior_audit':{'readings':['α','β']}}
    ranges = [(0,len(text))] if uncertain is None else [(0,uncertain[0]),uncertain,(uncertain[1],len(text))]
    segments = []
    for a,b in ranges:
        if a==b:
            continue
        segments.append({'start':a,'end':b,'original_text':text[a:b],'corrected_text':text[a:b],
            'corrected_start':a,'corrected_end':b,'verification':'uncertain' if (a,b)==uncertain else 'verified',
            'text_role':'authorial-body','scan':{'observed_text':observed[a:b]},
            'readings':[],'fragments':[]})
    result = {'locus':original['locus'],'original_row_sha256':campaign.row_sha(original),
        'physical_page':3,'printed_page':268,'digital_counterparts_usable':True,
        'status':'reviewed-with-uncertainty' if uncertain else 'reviewed-verified',
        'complete':True,'complete_scan_review':True,'original_text':text,'corrected_text':text,
        'original_text_sha256':campaign.sha(text.encode()),'corrected_text_sha256':campaign.sha(text.encode()),
        'segments':segments,'additional_lexical_exclusions':[],
        'uncertainty_exclusion_candidates':[],'nonbody_exclusion_candidates':[]}
    if uncertain:
        a,b=uncertain
        result['uncertainty_exclusion_candidates']=[{'start':a,'end':b,'text':text[a:b],
            'classification':'unresolved-source-reading','qualification':'The source glyph is unresolved.'}]
    return original,result


def compiled_case(text, digital, *, uncertain=None):
    original,review = record(text,uncertain=uncertain)
    before = campaign.canonical(original)+b'\n'
    library = gzip.compress(campaign.encode({'id':'tlg4040.tlg001.local002','sections':[
        {'id':campaign.SECTION_PREFIX+'280','blocks':[{'text':digital}]}]}),mtime=0)
    pin = {'path':campaign.LIBRARY.as_posix(),'sha256':campaign.sha(library)}
    # Deliberately preserve a wrong isolated association in the frozen fixture.
    target = campaign.tokens(digital)[-2]
    for segment in review['segments']:
        segment['readings']=[{'kind':'digital','section':campaign.SECTION_PREFIX+'280',
            **{k:target[k] for k in ('start','end','text')},'source':pin}]
    baseline = gzip.compress(before,mtime=0)
    compiled = {'schema':campaign.COMPILED_SCHEMA,'scope_complete':True,'admission_authorized':False,
        'campaign_id':'context-fixture','source_library_credit':{'edition':'fixture','sha256':pin['sha256']},
        'input_pins':{'corpus':{'path':campaign.CORPUS.as_posix(),'sha256':campaign.sha(before)},
            'digital_archive':pin,'scan':{'path':campaign.SCAN.as_posix(),'sha256':campaign.sha(b'fixture scan')},
            'frozen_corpus':{'path':campaign.BASELINE.as_posix(),'sha256':campaign.sha(baseline)}},
        'counts':{'passages':1,'complete_scan_review_rows':1},'rows':[review]}
    outputs,audit=complete.artifacts(before,campaign.encode(compiled))
    return {'compiled':compiled,'library':library,'before':before,'baseline':baseline,
            'complete_outputs':outputs,'complete_audit':audit}


@pytest.fixture
def installed(tmp_path):
    data=compiled_case('πρῶτος λόγος σαφὴς καὶ δεύτερος λόγος τέλος.',
                      'πρῶτος λόγος σαφὴς καὶ δεύτερος λόγος τέλος. ἄλλος λόγος τέλος.')
    files={**data['complete_outputs'],campaign.BASELINE:data['baseline'],campaign.LIBRARY:data['library'],
           campaign.SCAN:b'fixture scan'}
    for path,raw in files.items():
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True)
        (tmp_path/path).write_bytes(raw)
    for name in layer.RECIPE_NAMES:
        (tmp_path/'scripts').mkdir(exist_ok=True)
        (tmp_path/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    return tmp_path,data


def test_entire_row_context_beats_a_distant_exact_word():
    _,source=record('πρῶτος ἀπαγγέλλεσθαι λόγος σαφὴς τέλος.')
    full='πρῶτος ἀπαγγέλλεθαι λόγος σαφὴς τέλος. ἄλλος ἀπαγγέλλεσθαι μακρός.'
    effective,annotation=layer.contextualize(source,full)
    target=[r for r in effective['segments'][0]['readings'] if r['review_span']['text']=='ἀπαγγέλλεσθαι']
    assert {r['text'] for r in target}=={'ἀπαγγέλλεθαι'}
    assert annotation['context']['basis']=='entire-ordered-observed-row'
    assert annotation['text_correction_authorized'] is False
    assert source['segments'][0]['readings']==[]


def test_every_legitimate_tied_whole_context_is_retained():
    text='πρῶτος λόγος σαφὴς τέλος'
    _,source=record(text)
    effective,annotation=layer.contextualize(source,text+'· ἄλλος. '+text)
    assert annotation['context']['status']=='ambiguous-context'
    assert all(t['counterpart_count']==2 for t in effective['segments'][0]['digital_alignment']['tokens'])
    assert len(annotation['context']['alignment']['starts'])==2


def test_tied_deletion_paths_keep_both_edges_and_unmatched_flags():
    _,source=record('πρῶτος λόγος λόγος σαφὴς τέλος')
    effective,annotation=layer.contextualize(source,'πρῶτος λόγος σαφὴς τέλος')
    projected=effective['segments'][0]['digital_alignment']['tokens']
    repeated=[t for t in projected if t['text']=='λόγος']
    assert annotation['context']['status']=='ambiguous-context'
    assert all(t['may_be_unaligned'] and t['counterpart_count']==1 for t in repeated)
    assert len([r for r in effective['segments'][0]['readings'] if r['text']=='λόγος'])==2


def test_short_repeated_words_cannot_supply_context_authority():
    _,source=record('λόγος τέλος')
    effective,annotation=layer.contextualize(source,'λόγος τέλος καὶ ἄλλος λόγος τέλος')
    assert annotation['context']['status']=='insufficient-context'
    assert not effective['segments'][0]['readings']
    assert all(t['may_be_unaligned'] for t in effective['segments'][0]['digital_alignment']['tokens'])


def test_uncertain_spelling_cannot_prefer_the_distant_exact_occurrence():
    text='πρῶτος λόγος σαφὴς τέλος'
    a,b=text.index('λόγος'),text.index('λόγος')+len('λόγος')
    _,source=record(text,uncertain=(a,b))
    full='πρῶτος μῦθος σαφὴς τέλος. ἄλλος. '+text
    effective,annotation=layer.contextualize(source,full)
    assert annotation['context']['status']=='ambiguous-context'
    middle=effective['segments'][1]
    assert {r['text'] for r in middle['readings']}=={'μῦθος','λόγος'}
    assert annotation['context']['neutral_source_indices']==[1]


def test_neutral_alignment_matches_standard_library_fallback(monkeypatch):
    source=['πρῶτος','λόγος','σαφὴς','τέλος','ἄλλος']
    digital=['πρῶτος','μῦθος','σαφὴς','καί','τέλος','ἄλλος']
    fast=layer._context_alignment(source,digital,{1})
    monkeypatch.setattr(layer,'_np',None)
    assert layer._context_alignment(source,digital,{1})==fast


def test_unrelated_long_context_remains_explicitly_unmatched():
    _,source=record('ἄλφα βῆτα γάμμα δέλτα ἔψιλον')
    effective,annotation=layer.contextualize(source,'λόγος θεὸς ἀνὴρ ἄνθρωπος βασιλεύς')
    assert annotation['context']['status']=='insufficient-context'
    assert not effective['segments'][0]['readings']


def test_known_source_mapping_exception_is_not_filled_from_another_page():
    _,source=record('πρῶτος λόγος σαφὴς καὶ τέλος')
    source['digital_counterparts_usable']=False
    effective,annotation=layer.contextualize(source,'πρῶτος λόγος σαφὴς καὶ τέλος')
    assert annotation['context']['status']=='source-mapping-exception'
    assert not effective['segments'][0]['readings']
    assert 'digital_alignment' not in effective['segments'][0]


def test_source_only_mapping_exception_keeps_existing_lexical_eligibility():
    text='πρῶτος λόγος σαφὴς καὶ δεύτερος λόγος τέλος.'
    data=compiled_case(text,text)
    source=data['compiled']['rows'][0]
    source['digital_counterparts_usable']=False
    for segment in source['segments']:
        segment['readings']=[]
    outputs,_=complete.artifacts(data['before'],campaign.encode(data['compiled']))
    old=json.loads(outputs[campaign.CORPUS])
    after,_,_=layer.plan(outputs[campaign.CORPUS],campaign.encode(data['compiled']),data['library'],recorded_at=STAMP)
    new=json.loads(after)
    assert new[layer.TAG]['context_status']=='source-mapping-exception'
    assert new['analysis_text']==old['analysis_text']==text


def test_uncertainty_and_prior_noncontext_masks_survive_pointer_repair():
    text='πρῶτος λόγος σαφὴς καὶ δεύτερος λόγος τέλος.'
    a,b=text.index('σαφὴς'),text.index('σαφὴς')+len('σαφὴς')
    data=compiled_case(text,text,uncertain=(a,b))
    admitted=data['complete_outputs'][campaign.CORPUS]
    after,changes,_=layer.plan(admitted,campaign.encode(data['compiled']),data['library'],recorded_at=STAMP)
    old,new=json.loads(admitted),json.loads(after)
    assert new['text']==old['text']
    assert new['complete_source_review']==old['complete_source_review']
    assert 'σαφὴς' not in new['analysis_text']
    assert any(e['classification']=='unresolved-source-reading'
        for span in new[layer.TAG]['excluded_spans'] for e in span['evidence'])
    assert changes[0]['original_text']==changes[0]['corrected_text']


def test_digital_insertion_breaks_both_source_adjacencies():
    text='πρῶτος λόγος σαφὴς καὶ δεύτερος τέλος.'
    digital='πρῶτος λόγος σαφὴς ἄλλος καὶ δεύτερος τέλος.'
    _,source=record(text)
    effective,_=layer.contextualize(source,digital)
    masks=complete._digital_exclusions(effective)
    assert {'σαφὴς','καὶ'} <= {m['text'] for m in masks if m['classification']=='digital-insertion-boundary'}


def test_noncontext_fragment_masks_remain_even_with_exact_digital_agreement():
    text='πρῶτος λόγος σαφὴς καὶ δεύτερος λόγος τέλος.'
    data=compiled_case(text,text)
    a,b=text.index('δεύτερος'),text.index('δεύτερος')+len('δεύτερος')
    data['compiled']['rows'][0]['additional_lexical_exclusions']=[{
        'start':a,'end':b,'text':text[a:b],'classification':'source-confirmed-word-fragment'}]
    outputs,_=complete.artifacts(data['before'],campaign.encode(data['compiled']))
    after,_,_=layer.plan(outputs[campaign.CORPUS],campaign.encode(data['compiled']),data['library'],recorded_at=STAMP)
    new=json.loads(after)
    assert text[a:b] not in new['analysis_text']
    assert any(m['classification']=='source-confirmed-word-fragment'
        for span in new[layer.TAG]['excluded_spans'] for m in span['evidence'])


def test_apply_check_literal_undo_without_current_sources(installed):
    root,data=installed
    with pytest.raises(ValueError,match='timestamp'):
        layer.build(root)
    audit=layer.apply(root,recorded_at=STAMP)
    after=(root/campaign.CORPUS).read_bytes()
    old=data['complete_outputs'][campaign.CORPUS]
    assert audit['counts']['changed_display_rows']==0
    assert layer.check(root)==audit
    assert layer.restore_before_bytes(after,root)==old
    row=json.loads(after)
    assert layer.restore_before_row(row,root)==json.loads(old)
    assert layer.lexical_segments(row,root)
    restored=layer.restore_before_row(row,root)
    restored['prior_audit']['readings'].clear()
    assert layer.restore_before_row(row,root)['prior_audit']['readings']==['α','β']
    (root/campaign.SCAN).unlink()
    (root/campaign.LIBRARY).unlink()
    with pytest.raises(FileNotFoundError):
        layer.check(root)
    layer.undo(root)
    assert (root/campaign.CORPUS).read_bytes()==old
    assert layer.active_metadata(root) is None


@pytest.mark.parametrize('target',['scan','library','prior','records','before','aliases','corpus','recipe'])
def test_source_context_row_and_recipe_tampering_fails_after_warm_replay(installed,target):
    root,_=installed
    layer.apply(root,recorded_at=STAMP)
    layer.check(root)
    path={'scan':campaign.SCAN,'library':campaign.LIBRARY,'prior':complete.REVIEW,
        'records':layer.RECORDS,'before':layer.BEFORE,'aliases':complete.ALIASES,
        'corpus':campaign.CORPUS,'recipe':Path('scripts/repair_photius_context.py')}[target]
    p=root/path
    raw=p.read_bytes()
    p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises((ValueError,gzip.BadGzipFile,EOFError,KeyError,UnicodeDecodeError)):
        layer.check(root)


def test_changed_literal_postimage_cannot_bypass_projection_validation(installed):
    root,_=installed
    layer.apply(root,recorded_at=STAMP)
    row=json.loads((root/campaign.CORPUS).read_bytes())
    row['analysis_text']+=' invented'
    with pytest.raises(ValueError,match='postimage'):
        layer.lexical_segments(row,root)


def test_saved_annotation_and_record_disagreement_blocks_literal_undo(installed):
    root,_=installed
    layer.apply(root,recorded_at=STAMP)
    source=json.loads(gzip.decompress((root/layer.REVIEW).read_bytes()))
    source['rows'][0]['context']['observed_text']+=' independent change'
    raw=layer.compress_gzip(campaign.encode(source))
    (root/layer.REVIEW).write_bytes(raw)
    audit=json.loads((root/layer.AUDIT).read_bytes())
    audit['outputs'][layer.REVIEW.as_posix()]=campaign.sha(raw)
    (root/layer.AUDIT).write_bytes(campaign.encode(audit))
    with pytest.raises(ValueError,match='identity'):
        layer.undo(root)


def test_frozen_admission_timestamp_cannot_be_replaced(installed):
    root,_=installed
    layer.apply(root,recorded_at=STAMP)
    with pytest.raises(ValueError,match='timestamp'):
        layer.build(root,recorded_at='2026-10-22T20:00:00Z')


def test_five_confirmed_production_occurrences_use_their_local_context():
    # Small read-only regression; no source image rendering or corpus mutation.
    raw=(ROOT/campaign.OUT).read_bytes()
    rows={r['locus']:r for r in json.loads(gzip.decompress(raw))['rows']}
    library=json.loads(gzip.decompress((ROOT/campaign.LIBRARY).read_bytes()))
    sections={s['id']:'\n'.join(b['text'] for b in s['blocks']) for s in library['sections']}
    examples=[('0003.1',27,'ἀπαγγέλλεθαι'),('0005.6',26,'οὐδὲ'),
              ('0008.1',432,'εἰρήθη'),('0008.1',532,'ἔστω'),('0008.2',1427,'ἔστω')]
    effective={}
    for suffix,start,expected in examples:
        locus='helladius_chrestomathia_photius_bekker_v2_'+suffix
        source=rows[locus]
        if locus not in effective:
            section=campaign.SECTION_PREFIX+str(source['physical_page']+277)
            effective[locus]=layer.contextualize(source,sections[section])[0]
        segment=next(s for s in effective[locus]['segments'] if s['start']==start)
        assert {r['text'] for r in segment['readings'] if r['kind']=='digital'}=={expected}
