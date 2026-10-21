"""Full-span editorial adoption preserves witnesses, exclusions, and exact undo."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_photius_editorial_continuation as prepare
import repair_photius_editorial_continuation as continuation


def fixture(original='⟦σαφὴς ∥ σαφές⟧',source='σαφές'):
    text='ἀρχὴ '+original+' τέλος';a=text.index(original);b=a+len(original)
    raw=('<h3>248</h3><h2>435a</h2><td>ἀρχὴ '+source+' τέλος</td>').encode()
    identity={'id':'tlg-photius-henry','edition':'Henry, Bibliothèque',
        'citation':'Photius, Bibliotheca 4040.001','sha256':continuation.sha(raw)}
    known=continuation.previous._source_tokens(raw,identity)
    tokens=[]
    for index,token in known.values():
        if index not in (0,len(known)-1):tokens.append({**deepcopy(token),'source_index':index})
    reading={'source_id':identity['id'],'role':'chosen','text':' '.join(t['text'] for t in tokens),'tokens':tokens}
    reading=prepare.attributed_span(reading,prepare.source_document(raw))
    rendered=prepare.render(original,text,a,b,reading);reading['trim']=rendered['trim']
    masks=[{'start':a,'end':b,'text':original,'classification':'unresolved-source-reading','qualification':'Uncertain printed reading.'}]
    row={'locus':'photius-example','urn':'urn:cts:greekLit:tlg4040.tlg001:1','text':text,'analysis_text':'ἀρχὴ τέλος',
        'complete_source_review':{'frozen':'original'},
        continuation.previous.TAG:{'excluded_spans':{'path':continuation.previous.RECORDS.as_posix(),
            'locus':'photius-example','sha256':continuation.sha(continuation.canonical(masks))}}}
    before=continuation.canonical(row)+b'\n'
    record={'physical_page':170,'printed_page':435,'original_segment':{'verification':'uncertain',
        'text_role':'authorial-body','uncertainty':'Uncertain printed reading.','fragments':[]}}
    scopes={('photius-example',0):{'row':row,'start':a,'end':b,'record':record,'excluded_spans':masks}}
    decision={'locus':row['locus'],'segment_index':0,'original_text':original,'decision':'substitute',
        'reason':'located-editorial-reading','evidence':'An attributed editorial preference.',
        'readings':[reading],**rendered}
    authored={'schema':prepare.SCHEMA,'reviewed_at':'2026-10-21T22:50:00Z','source':identity,
        'input_corpus_sha256':continuation.sha(before),'records':[decision]}
    return {'before':before,'scopes':scopes,'authored':authored,'raw':raw,'aliases':b'{}\n'}


def compile_case(case,*,literal=False):
    return continuation.compile_review(case['before'],case['scopes'],case['authored'],
        source_raw=None if literal else case['raw'])


def saved(case,root):
    review=compile_case(case)
    files,audit=continuation.artifacts(case['before'],case['aliases'],continuation.encode(review),pins={},recipes={})
    for p,raw in {**files,continuation.ALIASES:case['aliases']}.items():
        (root/p).parent.mkdir(parents=True,exist_ok=True);(root/p).write_bytes(raw)
    return files,audit


def test_variant_display_retires_without_losing_originals_or_frozen_tags(tmp_path):
    case=fixture();files,audit=saved(case,tmp_path);row=json.loads(files[continuation.CORPUS])
    assert row['text']=='ἀρχὴ σαφές τέλος'
    assert row['complete_source_review']=={'frozen':'original'}
    assert row[continuation.previous.TAG]==case['scopes'][('photius-example',0)]['row'][continuation.previous.TAG]
    assert audit['counts']['newly_editorially_substituted_spans']==1
    assert audit['counts']['current_uncertainty_spans']==0
    assert continuation.restore_before_bytes(files[continuation.CORPUS],tmp_path)==case['before']
    assert continuation.restore_before_row(row,tmp_path)['text']=='ἀρχὴ ⟦σαφὴς ∥ σαφές⟧ τέλος'
    assert continuation.lexical_segments(row,tmp_path)==['ἀρχὴ σαφές τέλος']


@pytest.mark.parametrize(('original','source','expected'),[
    ('κακὸν.λόγον','σαφές, ῥῆμα','σαφές, ῥῆμα'),
    ('ἀ.θενέστερα','ἀσθενέστερα','ἀσθενέστερα'),
    ('δινεῖ(ν)','δινεῖται','δινεῖται'),
    ('ἐβα-πτίσθησαν','ἐβαπτίσθησαν','ἐβαπτίσθησαν'),
    ('«κακὸν.λόγον»','σαφές· ῥῆμα','«σαφές· ῥῆμα»'),
    ('οὐδ’ ἐλέγην','οὐδὲ ἐσθίειν','οὐδὲ ἐσθίειν'),
])
def test_complete_greek_span_renders_source_punctuation_and_abbreviations(original,source,expected):
    case=fixture(original,source);review=compile_case(case)
    assert review['records'][0]['corrected_text']==expected
    assert compile_case(case,literal=True)==review


def test_line_division_in_source_word_is_joined_once():
    case=fixture('κακὸν.λόγον','πα‐\nράσχοι')
    assert compile_case(case)['records'][0]['corrected_text']=='παράσχοι'


@pytest.mark.parametrize(('source','expected'),[
    ('ἔφη <b>«τεθνᾶσι</b> τῷ δέει <i>τοὺς ἀποστόλους</i>»','ἔφη «τεθνᾶσι τῷ δέει τοὺς ἀποστόλους»'),
    ('μὴ ἡμῶν <b>[φείσεται</b>]','μὴ ἡμῶν [φείσεται]'),
])
def test_pure_punctuation_html_nodes_complete_source_quotes(source,expected):
    case=fixture('κακὸν.λόγον',source)
    review=compile_case(case)
    assert review['records'][0]['corrected_text']==expected
    assert compile_case(case,literal=True)==review


def test_new_parser_keeps_every_original_greek_unit_identity():
    raw=b'<h3>248</h3><h2>435a</h2><td>'+ 'ἀρχὴ <b>«σαφές</b>» τέλος'.encode()+b'</td>'
    parser=continuation.previous.edition.EditionHTML();parser.feed(raw.decode())
    units=prepare.source_document(raw)
    assert list(units)==parser.units
    assert any(n['text'].startswith('»') for n in units.nodes)


def test_recorded_punctuation_cannot_contain_an_extra_word():
    case=fixture('κακὸν.λόγον','σαφές, ῥῆμα')
    r=case['authored']['records'][0]['readings'][0]
    r['separators'][0]['pieces'][0]['text']='ἄλλο'
    with pytest.raises(ValueError):compile_case(case,literal=True)


@pytest.mark.parametrize('defect',['source','source-index','source-ref','source-text','punctuation','surface','tie','missing','duplicate','display'])
def test_rejects_unattributed_or_incomplete_decisions(defect):
    case=fixture('κακὸν.λόγον','σαφές, ῥῆμα');d=case['authored']['records'][0];r=d['readings'][0]
    if defect=='source':case['raw']+=b'changed'
    elif defect=='source-index':r['tokens'][0]['source_index']+=1
    elif defect=='source-ref':r['tokens'][0]['refs'][0]['start']+=1
    elif defect=='source-text':r['tokens'][0]['text']='ἕτερον'
    elif defect=='punctuation':r['separators'][0]['pieces'][0]['text']='; '
    elif defect=='surface':r['surface']='σαφές ῥῆμα'
    elif defect=='tie':d['readings'].append(deepcopy(r))
    elif defect=='missing':case['authored']['records']=[]
    elif defect=='duplicate':case['authored']['records'].append(deepcopy(d))
    else:d['corrected_text']='ἄλλο'
    with pytest.raises(ValueError):compile_case(case)


def test_source_token_cannot_be_adopted_twice_in_different_layers():
    case=fixture();target=next(iter(case['scopes'].values()))
    token=case['authored']['records'][0]['readings'][0]['tokens'][0]
    target['previously_used_source_refs']={continuation.sha(continuation.canonical(token['refs']))}
    with pytest.raises(ValueError,match='already admitted'):compile_case(case)


def test_fragment_and_unreviewed_nonbody_roles_cannot_be_promoted():
    for role in ['fragment','nonbody']:
        case=fixture();target=next(iter(case['scopes'].values()))
        if role=='fragment':target['record']['original_segment']['fragments']=[{'side':'trailing'}]
        else:target['record']['original_segment']['text_role']='unclassified-small-type'
        with pytest.raises(ValueError):compile_case(case)


def test_independent_exclusion_survives_an_editorial_reading(tmp_path):
    case=fixture();target=next(iter(case['scopes'].values()));masks=target['excluded_spans']
    masks.append({**masks[0],'classification':'nonbody-source-material','qualification':'An independent source decision.'})
    target['row'][continuation.previous.TAG]['excluded_spans']['sha256']=continuation.sha(continuation.canonical(masks))
    case['before']=continuation.canonical(target['row'])+b'\n';case['authored']['input_corpus_sha256']=continuation.sha(case['before'])
    files,_=saved(case,tmp_path);row=json.loads(files[continuation.CORPUS])
    assert row['text']=='ἀρχὴ σαφές τέλος'
    assert row['analysis_text'].split()==['ἀρχὴ','τέλος']


@pytest.mark.parametrize('path',[continuation.BEFORE,continuation.BEFORE_ALIASES,continuation.REVIEW,continuation.RECORDS])
def test_literal_undo_requires_unchanged_archive(tmp_path,path):
    case=fixture();files,_=saved(case,tmp_path)
    (tmp_path/path).write_bytes((tmp_path/path).read_bytes()+b'changed')
    with pytest.raises(ValueError,match='artifact changed'):
        continuation.restore_before_bytes(files[continuation.CORPUS],tmp_path)


@pytest.mark.parametrize('defect',['text','old-tag','new-mask','timestamp'])
def test_row_projection_rejects_any_unrecorded_postimage(tmp_path,defect):
    case=fixture();files,_=saved(case,tmp_path);row=json.loads(files[continuation.CORPUS])
    if defect=='text':row['text']+='x'
    elif defect=='old-tag':row['complete_source_review']={}
    elif defect=='new-mask':row[continuation.TAG]['excluded_spans']={}
    else:row[continuation.TAG]['reviewed_at']='changed'
    with pytest.raises(ValueError,match='postimage'):continuation.lexical_segments(row,tmp_path)


def test_exact_undo_works_without_live_comparison_source(tmp_path):
    case=fixture();files,_=saved(case,tmp_path)
    assert continuation.active_metadata(tmp_path)['counts']['current_uncertainty_spans']==0
    continuation.undo(tmp_path)
    assert (tmp_path/continuation.CORPUS).read_bytes()==case['before']
    assert continuation.active_metadata(tmp_path) is None
    with pytest.raises(ValueError):continuation.restore_before_bytes(case['before']+b'changed',tmp_path)


def test_direct_lexical_projection_requires_unchanged_compiled_authority(tmp_path):
    case=fixture();files,_=saved(case,tmp_path);row=json.loads(files[continuation.CORPUS])
    (tmp_path/continuation.REVIEW).write_bytes((tmp_path/continuation.REVIEW).read_bytes()+b'changed')
    with pytest.raises(ValueError,match='compiled authority'):
        continuation.lexical_segments(row,tmp_path)


def test_orphaned_metadata_cannot_be_ignored(tmp_path):
    with pytest.raises(ValueError,match='no authority'):
        continuation.restore_before_bytes(b'{"photius_editorial_continuation":{}}',tmp_path)


@pytest.mark.parametrize(('left','right','expected'), [
    ('καθάπερ','κληρονομίαν','καθάπερ κληρονομίαν'),
    ('γίνεται.','Ἀπαντήσειν','γίνεται. Ἀπαντήσειν'),
])
def test_distinct_html_cells_preserve_word_and_sentence_boundaries(left,right,expected):
    raw=('<h3>234</h3><h2>298a</h2><tr><td>'+left+
         '</td></tr><tr><td>'+right+'</td></tr>').encode()
    units=prepare.source_document(raw)
    tokens=prepare.previous.edition.tokenize(units)
    reading=prepare.attributed_span({'tokens':tokens},units)
    assert reading['surface']==expected
    separator=reading['separators'][0]
    assert continuation._punctuation(separator,tokens[0]['refs'][-1],tokens[1]['refs'][0])==separator['rendered']


def test_unknown_individual_review_cannot_authorize_substitution():
    case=fixture();before,scopes,authored,raw=(case[k] for k in ('before','scopes','authored','raw'))
    authored['records'][0]['manual_review']={'module':'unreviewed_source','review':{}}
    with pytest.raises(ValueError,match='unknown source authority'):
        continuation.compile_review(before,scopes,authored,source_raw=raw)


def test_individual_source_choice_must_match_adopted_interval(monkeypatch):
    from types import SimpleNamespace
    case=fixture();before,scopes,authored,raw=(case[k] for k in ('before','scopes','authored','raw'))
    expected={'original_text':authored['records'][0]['original_text'],
        'readings':[{'tokens':[{'text':'ἕτερος','refs':[]}]}],'rendering':{}}
    module=SimpleNamespace(__name__='photius_remaining_manual_test',
        validate_record=lambda key,record: expected)
    monkeypatch.setattr(prepare,'manual_modules',lambda root=prepare.ROOT:[module])
    authored['records'][0]['manual_review']={'module':module.__name__,'review':expected}
    with pytest.raises(ValueError,match='Individual adoption differs'):
        continuation.compile_review(before,scopes,authored,source_raw=raw)


@pytest.mark.parametrize('defect',['source-index','punctuation','decision','source-identity'])
def test_frozen_complete_witness_packet_rejects_coordinated_public_mutations(monkeypatch,defect):
    case=fixture(source='σαφές,ῥῆμα')
    monkeypatch.setattr(prepare,'BASELINE_SHA256',continuation.sha(case['before']))
    monkeypatch.setattr(continuation,'SOURCE_WITNESS_SHA256',continuation.witness_fingerprint(case['authored']))
    assert compile_case(case)==compile_case(case,literal=True)
    decision=case['authored']['records'][0];reading=decision['readings'][0]
    if defect=='source-index':reading['tokens'][0]['source_index']+=25
    elif defect=='punctuation':
        witness=reading['separators'][0]
        witness['pieces'][0]['text']=';';witness['rendered']=';'
        reading['surface']=reading['surface'].replace(',',';')
        decision['corrected_text']=decision['corrected_text'].replace(',',';')
    elif defect=='decision':
        decision.update(decision='retained',corrected_text=decision['original_text'])
    else:case['authored']['source']['sha256']='0'*64
    with pytest.raises(ValueError,match='complete source witness fingerprint changed'):
        compile_case(case,literal=True)
