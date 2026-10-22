"""Editorial choices retain source uncertainty and can be removed without the source."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys
import unicodedata

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import repair_photius_editorial_substitutions as editorial


def fixture(text='ἀρχὴ ἄσαφες μένει ἄλλο τέλος', values=None,
            html='<h3>248</h3><h2>435a</h2><td>ἀρχὴ σαφές μένει ἄλλο ἕτερον τέλος</td>'):
    values = values or [('ἄσαφες', 'σαφές', 'substitute'), ('μένει', 'μένει', 'substitute'),
                        ('ἄλλο', 'ἄλλο', 'retained-tied')]
    locus = 'helladius_chrestomathia_photius_bekker_v2_0170.10'
    masks, segments, decisions = [], [], []
    source_raw = html.encode()
    source = {'id':'tlg-photius-henry', 'edition':'Henry, Bibliothèque',
              'citation':'Photius, Bibliotheca 4040.001', 'sha256':editorial.sha(source_raw)}
    tokens = [value[1] for value in editorial._source_tokens(source_raw, source).values()]
    for index, (original, corrected, status) in enumerate(values):
        a = text.index(original); b = a+len(original); note = f'Uncertain source group {index}.'
        segments.append({'verification':'uncertain', 'corrected_start':a, 'corrected_end':b,
            'corrected_text':original, 'uncertainty':note, 'text_role':'authorial-body'})
        masks.append({'start':a,'end':b,'text':original,'classification':'unresolved-source-reading',
                      'qualification':note})
        choices = [corrected] if status == 'substitute' else ['ἄλλο','ἕτερον']
        readings = []
        for choice in choices:
            token = next(deepcopy(t) for t in tokens if unicodedata.normalize('NFC',t['text']) == choice)
            readings.append({'text':token['text'],'source_id':source['id'], 'tokens':[token],
                             'role':'chosen' if status == 'substitute' else 'alternative'})
        decisions.append({'locus':locus,'segment_index':index,'original_text':original,
            'corrected_text':corrected,'decision':status,'evidence':'Editorial preference; source scan remains uncertain.',
            'readings':readings})
    old = {'locus':locus,'urn':'photius.bibliotheca','text':text,'analysis_text':'ἀρχὴ τέλος',
        'complete_source_review':{'frozen':'complete'},'photius_context_review':{'frozen':'context'},
        'photius_uncertainty_review':{'frozen':'prior33'},
        'photius_uncertainty_admission':{'excluded_spans':masks,'frozen':'source70'}}
    before = (json.dumps(old,ensure_ascii=False)+'\n').encode()
    complete = {'scope_complete':True,'rows':[{'locus':locus,'physical_page':170,'printed_page':435,'segments':segments}]}
    authored = {'schema':editorial.INPUT_SCHEMA,'reviewed_at':'2026-10-21T21:15:00Z',
        'input_corpus_sha256':editorial.sha(before),'source':source,'records':decisions,
        'input_pins':{},'recipe_sha256':{},'counts':dict(editorial.Counter(d['decision'] for d in decisions))}
    return {'before':before,'old':old,'complete':complete,'previous':{'records':[]},
            'admitted':{'records':[]},'authored':authored,'source_raw':source_raw,'aliases':b'{}\n'}


def compile_case(case):
    return editorial.compile_review(case['before'],case['complete'],case['previous'],case['admitted'],
                                    case['authored'],case['source_raw'])


@pytest.fixture
def case():
    return fixture()


def save(root, files):
    for path, raw in files.items():
        (root/path).parent.mkdir(parents=True,exist_ok=True); (root/path).write_bytes(raw)


def saved(case, root):
    review = compile_case(case)
    files, audit = editorial.artifacts(case['before'],case['aliases'],editorial.encode(review),pins={},recipes={})
    save(root,files); save(root,{editorial.ALIASES:case['aliases']})
    return files,audit


def test_editorial_adoption_preserves_every_previous_fact_and_counts_confirmations(case,tmp_path):
    files,audit = saved(case,tmp_path)
    new = json.loads(files[editorial.CORPUS])
    assert new['text'] == 'ἀρχὴ σαφές μένει ἄλλο τέλος'
    for tag in ('complete_source_review','photius_context_review','photius_uncertainty_review','photius_uncertainty_admission'):
        assert new[tag] == case['old'][tag]
    counts = audit['counts']
    assert (counts['scan_uncertainty_spans'],counts['editorially_substituted_spans'],
            counts['unsubstituted_source_uncertainty_spans'],counts['changed_spans']) == (3,2,1,1)
    assert editorial.restore_before_bytes(files[editorial.CORPUS],tmp_path) == case['before']
    assert editorial.restore_before_row(new,tmp_path) == case['old']
    assert 'σαφές' in ' '.join(editorial.lexical_segments(new,tmp_path))
    assert 'ἄλλο' not in ' '.join(editorial.lexical_segments(new,tmp_path))
    assert (tmp_path/editorial.ALIASES).read_bytes() == case['aliases']


def test_source_invalidated_exact_undo_and_inactive_baseline(case,tmp_path):
    _,audit = saved(case,tmp_path)
    assert editorial.active_metadata(tmp_path)['counts'] == audit['counts']
    editorial.undo(tmp_path)
    assert (tmp_path/editorial.CORPUS).read_bytes() == case['before']
    assert editorial.active_metadata(tmp_path) is None
    (tmp_path/editorial.ALIASES).write_bytes(b'{"unrecorded":true}')
    with pytest.raises(ValueError,match='aliases'):
        editorial.active_metadata(tmp_path)


@pytest.mark.parametrize('path',[editorial.BEFORE,editorial.BEFORE_ALIASES,editorial.REVIEW,editorial.RECORDS])
def test_literal_undo_rejects_tampered_archive(case,tmp_path,path):
    files,_ = saved(case,tmp_path)
    (tmp_path/path).write_bytes((tmp_path/path).read_bytes()+b'changed')
    with pytest.raises(ValueError,match='artifact changed'):
        editorial.restore_before_bytes(files[editorial.CORPUS],tmp_path)


@pytest.mark.parametrize('defect',['text','mask','old-tag','timestamp','reading-ref'])
def test_projection_rejects_mutated_postimage(case,tmp_path,defect):
    files,_ = saved(case,tmp_path); row=json.loads(files[editorial.CORPUS])
    if defect=='text': row['text']+='x'
    elif defect=='mask': row[editorial.TAG]['excluded_spans']=[]
    elif defect=='old-tag': row['complete_source_review']={}
    elif defect=='timestamp': row[editorial.TAG]['reviewed_at']='2026-10-21T21:16:00Z'
    else: row[editorial.TAG]['source_review']['uncompressed_sha256']='forged'
    with pytest.raises(ValueError,match='postimage'):
        editorial.lexical_segments(row,tmp_path)


@pytest.mark.parametrize('defect',['source','refs','text','distant','tie','missing','duplicate','private','wrapper'])
def test_source_and_occurrence_accounting_reject_invalid_decisions(case,defect):
    first=case['authored']['records'][0]
    if defect=='source': case['source_raw']+=b'changed'
    elif defect=='refs': first['readings'][0]['tokens'][0]['refs'][0]['start']+=1
    elif defect=='text': first['readings'][0]['tokens'][0]['text']='ἕτερον'
    elif defect=='distant': case['complete']['rows'][0]['printed_page']=400
    elif defect=='tie': first['readings']+=deepcopy(case['authored']['records'][2]['readings'])
    elif defect=='missing': case['authored']['records'].pop()
    elif defect=='duplicate': case['authored']['records'].append(deepcopy(first))
    elif defect=='private': case['authored']['private_path']='/Users/person/private.html'
    else: first['display_suffix']=','
    with pytest.raises(ValueError): compile_case(case)


def test_nonbody_cannot_be_substituted(case):
    case['complete']['rows'][0]['segments'][0]['text_role']='editorial-heading'
    with pytest.raises(ValueError,match='body reading'):
        compile_case(case)


def test_printed_fragments_cannot_each_adopt_the_same_complete_source_word(case):
    # A digital whole word can legitimately face two printed fragments. Adopting
    # it independently for each fragment would duplicate a word across rows.
    segment=case['complete']['rows'][0]['segments'][0]
    segment['fragments']=[{'start':0,'end':len(segment['corrected_text']),
                           'classification':'source-confirmed-word-fragment'}]
    with pytest.raises(ValueError,match='separate jointly reviewed source group'):
        compile_case(case)
    decision=case['authored']['records'][0]
    decision.update(decision='retained-unmapped',corrected_text=decision['original_text'],readings=[])
    review=compile_case(case)
    after,records,counts=editorial.plan(case['before'],editorial.encode(review))
    assert json.loads(after)['text']==case['old']['text']
    assert any(c['text']==decision['original_text'] and c['classification']=='unresolved-source-reading'
               for c in records[0]['remaining_exclusion_causes'])
    assert counts['editorially_substituted_spans']==1


def test_independent_fragment_and_nonbody_exclusions_survive(case):
    old=case['old']; masks=old['photius_uncertainty_admission']['excluded_spans']
    a,b=masks[0]['start'],masks[0]['end']
    masks.extend([{'start':0,'end':3,'text':old['text'][:3],'classification':'source-confirmed-word-fragment'},
                  {'start':a,'end':b,'text':old['text'][a:b],'classification':'nonbody-source-material'}])
    case['before']=editorial.campaign.canonical(old)+b'\n'
    case['authored']['input_corpus_sha256']=editorial.sha(case['before'])
    after,records,_=editorial.plan(case['before'],editorial.encode(compile_case(case)))
    assert {c['classification'] for c in records[0]['remaining_exclusion_causes']} >= {
        'source-confirmed-word-fragment','nonbody-source-material','unresolved-source-reading'}
    assert 'σαφές' not in json.loads(after)['analysis_text']


def test_trimmed_partial_word_can_restore_its_complete_uncertainty_mask():
    case=fixture('λαγος',[('α','λόγος','substitute')],'<h3>248</h3><h2>435a</h2><td>λόγος</td>')
    decision=case['authored']['records'][0]
    decision['corrected_text']='ό'
    token=next(iter(editorial._source_tokens(case['source_raw'],case['authored']['source']).values()))[1]
    decision['readings']=[{'source_id':'tlg-photius-henry','role':'chosen','text':'λόγος',
        'tokens':[token],'trim':{'prefix':'λ','suffix':'γος'},'applied_text':'ό'}]
    case['old']['photius_uncertainty_admission']['excluded_spans'][0].update(start=0,end=5,text='λαγος')
    case['before']=editorial.campaign.canonical(case['old'])+b'\n'
    case['authored']['input_corpus_sha256']=editorial.sha(case['before'])
    after,records,_=editorial.plan(case['before'],editorial.encode(compile_case(case)))
    assert json.loads(after)['analysis_text']=='λόγος'
    assert len(records[0]['retired_uncertainty_causes'])==1


def test_shared_whole_word_mask_is_retained_when_one_uncertain_piece_is_held(case):
    review=compile_case(case)
    old=case['old']; first=review['records'][0]; held=review['records'][2]
    old['photius_uncertainty_admission']['excluded_spans'][0].update(
        end=held['end'],text=old['text'][first['start']:held['end']])
    before=editorial.campaign.canonical(old)+b'\n'; review['input_corpus_sha256']=editorial.sha(before)
    for d in review['records']: d['original_row_sha256']=editorial.prior.row_sha(old)
    after,records,_=editorial.plan(before,editorial.encode(review))
    assert any(c['qualification']==first['original_segment']['uncertainty']
               for c in records[0]['remaining_exclusion_causes'])
    assert 'σαφές' not in json.loads(after)['analysis_text']


def test_elision_is_preserved_once_and_decomposed_source_is_normalized():
    case=fixture('κατ’',[('κατ’','κατ’','substitute')],'<h3>248</h3><h2>435a</h2><td>κατ’</td>')
    after,_,_=editorial.plan(case['before'],editorial.encode(compile_case(case)))
    assert json.loads(after)['text']=='κατ’'
    case=fixture('ἄσαφες',[('ἄσαφες','σαφές','substitute')],
        '<h3>248</h3><h2>435a</h2><td>'+unicodedata.normalize('NFD','σαφές')+'</td>')
    assert compile_case(case)['records'][0]['corrected_text']=='σαφές'


def test_expanded_source_reading_does_not_inherit_old_elision_apostrophe():
    case=fixture('εἴρη’',[('εἴρη’','εἴρηται','substitute')],'<h3>248</h3><h2>435a</h2><td>εἴρηται</td>')
    after,_,_=editorial.plan(case['before'],editorial.encode(compile_case(case)))
    assert json.loads(after)['text']=='εἴρηται'


def test_numeral_keraia_is_not_doubled_after_nfc_normalization():
    case=fixture('γʹ',[('γʹ','γʹ','substitute')],'<h3>248</h3><h2>435a</h2><td>γʹ</td>')
    assert compile_case(case)['records'][0]['corrected_text']=='γʹ'


def test_compact_masks_are_bound_to_the_full_frozen_projection(case,tmp_path):
    files,_=saved(case,tmp_path); row=json.loads(files[editorial.CORPUS])
    reference=row[editorial.TAG]['excluded_spans']
    assert reference['path']==editorial.RECORDS.as_posix()
    assert reference['locus']==row['locus']
    assert isinstance(reference['sha256'],str)
    records=[json.loads(line) for line in gzip.decompress(files[editorial.RECORDS]).splitlines()]
    assert reference['sha256']==editorial.sha(editorial.campaign.canonical(records[0]['excluded_spans']))
    assert len(records[0]['excluded_spans'])==1
    assert 'ἄλλο' not in ' '.join(editorial.lexical_segments(row,tmp_path))


def test_deterministic_archives_and_mutable_metadata_isolation(case,tmp_path):
    files,audit=saved(case,tmp_path)
    assert files==editorial.artifacts(case['before'],case['aliases'],editorial.encode(compile_case(case)),pins={},recipes={})[0]
    metadata=editorial.active_metadata(tmp_path); metadata['counts']['substituted_identities'].clear()
    assert editorial.active_metadata(tmp_path)['counts']==audit['counts']


def public_inputs(case,root,monkeypatch):
    compiled=editorial.compress_gzip(editorial.encode(case['complete']))
    inputs={editorial.COMPILED:compiled,editorial.prior.REVIEW:editorial.encode(case['previous']),
            editorial.admission.REVIEW:editorial.encode(case['admitted'])}
    pins={path:editorial.sha(raw) for path,raw in inputs.items()}
    monkeypatch.setattr(editorial,'INPUT_SHA256',pins)
    monkeypatch.setattr(editorial,'BASELINE_SHA256',editorial.sha(case['before']))
    monkeypatch.setattr(editorial,'ALIASES_SHA256',editorial.sha(case['aliases']))
    monkeypatch.setattr(editorial,'RECIPE_NAMES',('recipe.py',))
    save(root,{**inputs,editorial.CORPUS:case['before'],editorial.ALIASES:case['aliases'],Path('scripts/recipe.py'):b'recipe'})
    authored=case['authored']; authored['input_pins']={p.as_posix():editorial.sha(r) for p,r in inputs.items()}
    authored['input_pins'][editorial.CORPUS.as_posix()]=editorial.sha(case['before'])
    authored['recipe_sha256']={'recipe.py':editorial.sha(b'recipe')}
    save(root,{editorial.SOURCE_REVIEW:editorial.encode(authored)})
    monkeypatch.setattr(editorial.preparer,'prepare',lambda *args,**kwargs:deepcopy(authored))


def test_fresh_build_and_public_literal_check_have_distinct_source_contracts(case,tmp_path,monkeypatch):
    public_inputs(case,tmp_path,monkeypatch)
    files,audit=editorial.build(tmp_path,source_html=case['source_raw']); save(tmp_path,files)
    assert editorial.check_literal(tmp_path)==audit
    assert editorial.check(tmp_path,source_html=case['source_raw'])==audit
    monkeypatch.delenv('PHOTIUS_COMPARISON_HTML',raising=False)
    with pytest.raises(ValueError,match='requires --source-html'):
        editorial.check(tmp_path)
    source=tmp_path/'edition.html'; source.write_bytes(case['source_raw']+b'changed')
    with pytest.raises(ValueError,match='HTML changed'):
        editorial.check(tmp_path,source_html=source)
    editorial.undo(tmp_path)
    assert editorial.check_literal(tmp_path) is None


@pytest.mark.parametrize('defect',['input','recipe','source-review','corpus'])
def test_literal_check_detects_changed_public_inputs(case,tmp_path,monkeypatch,defect):
    public_inputs(case,tmp_path,monkeypatch)
    files,_=editorial.build(tmp_path,source_html=case['source_raw']); save(tmp_path,files)
    path={'input':editorial.COMPILED,'recipe':Path('scripts/recipe.py'),
          'source-review':editorial.SOURCE_REVIEW,'corpus':editorial.CORPUS}[defect]
    (tmp_path/path).write_bytes((tmp_path/path).read_bytes()+b'changed')
    with pytest.raises(ValueError): editorial.check_literal(tmp_path)


def test_fresh_build_rechecks_source_after_context_selection(case,tmp_path,monkeypatch):
    public_inputs(case,tmp_path,monkeypatch)
    path=tmp_path/'edition.html'; path.write_bytes(case['source_raw'])
    def mutate(*args,**kwargs):
        path.write_bytes(b'changed'); return deepcopy(case['authored'])
    monkeypatch.setattr(editorial.preparer,'prepare',mutate)
    with pytest.raises(ValueError,match='changed during'):
        editorial.build(tmp_path,source_html=path)


def test_fresh_build_reproduces_context_choices_instead_of_trusting_pointers(case,tmp_path,monkeypatch):
    public_inputs(case,tmp_path,monkeypatch)
    other=deepcopy(case['authored']); other['records'][0]['evidence']='A changed contextual choice.'
    monkeypatch.setattr(editorial.preparer,'prepare',lambda *a,**kw:other)
    with pytest.raises(ValueError,match='contextual selection'):
        editorial.build(tmp_path,source_html=case['source_raw'])
