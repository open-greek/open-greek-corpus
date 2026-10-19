"""Diagnostic alignment retains exact offsets, alternative paths, and source limits."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import assess_photius_historical as assess


def row(text, page=2, number=1, **kwargs):
    return {'urn':'photius.bibliotheca', 'locus':f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{number}',
            'text':text, 'source':'ocr', **kwargs}


def library(text='ὁ λόγος ἀληθής', page=2, extra=()):
    return {'id':'tlg4040.tlg001.local002', 'license':{'text':'CC BY-SA4.0'},
            'sections':[{'id':assess.SECTION_PREFIX+str(page+277), 'blocks':[{'text':text}]}, *extra]}


def assess_one(text, digital, **kwargs):
    return assess.candidates([row(text)],library(digital),**kwargs)


@pytest.mark.parametrize(('old','digital','classification'),[
    ('ὁ λόγος ἀληθής','ὁ λόγος ἀληθής','exact'),
    ('ο λογος αληθης','ὁ λόγος ἀληθής','mark-only'),
    ('ὁ λόγος ἀληθης','ὁ λόγος ἀληθής','mark-only'),
    ('ὁ λόγος ἀληθές','ὁ λόγος ἀληθής','substantive'),
    ('Ὁ λόγος ἀληθής','ὁ λόγος ἀληθής','substantive'),
])
def test_classification_compares_readings_without_claiming_an_admission(old,digital,classification):
    report=assess_one(old,digital)
    assert report['rows'][0]['classification']==classification
    assert not report['admission_authorized'] and 'not' not in report['kind']
    assert report['input_pins']['current_rows_sha256']==assess.sha(assess.canonical([row(old)]))
    assert report['pages'][0]['text']==digital
    assert 'scan-reviewed correction' in report['qualification']


def test_exact_raw_codepoint_offsets_survive_decomposed_marks_and_mixed_script():
    text='«α\u0313ληθής», εἰρῆkenai κα-\nλός δ’.'
    tokens=assess.tokens(text)
    assert [text[t['start']:t['end']] for t in tokens]==['α\u0313ληθής','εἰρῆkenai','κα','λός','δ’']
    assert tokens[2]['following_hyphen']=={'start':text.index('-'),'end':text.index('-')+1,'text':'-'}
    assert assess_one('α\u0313ληθής','ἀληθής')['rows'][0]['classification']=='mark-only'


def test_repeated_phrase_keeps_every_equally_good_digital_window_and_counterpart():
    digital='ὁ λόγος ἀληθής τέλος ὁ λόγος ἀληθής'
    report=assess_one('ο λογος αληθης',digital)
    result=report['rows'][0]
    assert result['ambiguous'] and result['fragments'][0]['possible_source_starts']==[0,4]
    assert [t['counterpart_indices'] for t in result['tokens']]==[[0,4],[1,5],[2,6]]
    materialized=assess.materialize(report,result['locus'])
    assert len(materialized['tokens'][0]['counterparts'])==2
    for token in materialized['tokens']:
        assert 'ο λογος αληθης'[token['original_span']['start']:token['original_span']['end']]==token['original_span']['original_text']
        for counterpart in token['counterparts']:
            assert digital[counterpart['start']:counterpart['end']]==counterpart['text']
            assert counterpart['original_text']==counterpart['text']
            assert counterpart['section']==assess.SECTION_PREFIX+'279'


def test_all_optimal_edges_preserve_deletion_and_alignment_ambiguity():
    alignment=assess._local_alignment(['λογοσ','λογοσ'],['λογοσ'])
    assert alignment['counterparts']==[[0],[0]]
    assert alignment['may_be_unaligned']==[True,True] and alignment['ambiguous']
    assert alignment['cost']==assess.GAP_COST


def brute_align(old,digital):
    paths=[]
    def visit(i,j,cost,start,pairs,deleted,inserted):
        if i==len(old):
            paths.append((cost,start,j,pairs,deleted,inserted));return
        visit(i+1,j,cost+assess.GAP_COST,start,pairs,deleted+[i],inserted)
        if j<len(digital):
            visit(i+1,j+1,cost+assess._substitution(old[i],digital[j]),start,pairs+[(i,j)],deleted,inserted)
            visit(i,j+1,cost+assess.GAP_COST,start,pairs,deleted,inserted+[j])
    for start in range(len(digital)+1):visit(0,start,0,start,[],[],[])
    best=min(p[0] for p in paths);winners=[p for p in paths if p[0]==best]
    return {'cost':best,'starts':sorted({p[1] for p in winners}),'ends':sorted({p[2] for p in winners}),
        'counterparts':[sorted({j for p in winners for i,j in p[3] if i==index}) for index in range(len(old))],
        'may_be_unaligned':[any(index in p[4] for p in winners) for index in range(len(old))],
        'digital_only':sorted({j for p in winners for j in p[5]})}


@pytest.mark.parametrize('old',[['α'],['β'],['α','α'],['α','β'],['β','α'],['α','β','α']])
@pytest.mark.parametrize('digital',[['α'],['β'],['α','β'],['β','α'],['α','β','α']])
def test_candidate_edge_union_matches_exhaustive_independent_path_enumeration(old,digital):
    actual=assess._local_alignment(old,digital)
    assert {key:actual[key] for key in brute_align(old,digital)}==brute_align(old,digital)


@pytest.mark.parametrize(('old','digital'),[
    (['λογοσ','λογοσ'],['λογοσ']), (['λογοσ','θεου','αληθησ'],['θεου','αληθησ','λογοσ']),
    (['α','β','α'],['β','α','β','α']), (['α'],[]),
    (['πρωτον','λαγοσ','τελοσ'],['αρχη','πρωτον','λογοσ','σαφησ','τελοσ']),
])
def test_optional_acceleration_and_standard_library_paths_are_identical(monkeypatch,old,digital):
    accelerated=assess._local_alignment(old,digital)
    monkeypatch.setattr(assess,'_np',None)
    assert assess._local_alignment(old,digital)==accelerated


def test_internal_digital_word_is_a_candidate_missing_span_not_an_approved_insertion():
    report=assess_one('ὁ λόγος τὸ τέλος','ὁ λόγος σαφής τὸ τέλος')
    result=report['rows'][0]
    assert result['classification']=='substantive'
    assert result['fragments'][0]['digital_only_candidates']==[2]
    assert report['pages'][0]['tokens'][2]['text']=='σαφής'
    assert result['current_row']['text']=='ὁ λόγος τὸ τέλος'


def test_rows_and_newline_fragments_can_arrive_in_reverse_source_order():
    digital='ὁ πρῶτος λόγος ὁ δεύτερος λόγος'
    values=[row('ὁ δεύτερος λόγος',number=1),row('ὁ πρῶτος λόγος',number=2)]
    report=assess.candidates(values,library(digital))
    assert [r['fragments'][0]['possible_source_starts'] for r in report['rows']]==[[3],[0]]
    fragmented=assess_one('ὁ δεύτερος λόγος\nὁ πρῶτος λόγος',digital)['rows'][0]
    assert [f['possible_source_starts'] for f in fragmented['fragments']]==[[3],[0]]
    assert fragmented['classification']=='substantive'
    assert fragmented['fragment_order_candidates'][0]['disposition']=='reverse-or-overlap-in-every-local-candidate'
    assert all(t['classification']=='exact' for t in fragmented['tokens'])


def test_independent_anchors_detect_reordered_blocks_without_newlines():
    digital='πρῶτον δεύτερον τρίτον τέταρτον πέμπτον ἕκτον'
    result=assess_one('τέταρτον πέμπτον ἕκτον πρῶτον δεύτερον τρίτον',digital)['rows'][0]
    assert len(result['fragments'])==2
    assert result['fragments'][1]['reason']=='independent-anchor-discontinuity'
    assert [f['possible_source_starts'] for f in result['fragments']]==[[3],[0]]
    assert result['classification']=='substantive'
    assert result['fragment_order_candidates']


def test_computational_chunks_cover_every_token_once_without_imposing_page_order(monkeypatch):
    monkeypatch.setattr(assess,'MAX_FRAGMENT_TOKENS',3)
    digital='πρῶτον δεύτερον τρίτον τέταρτον πέμπτον ἕκτον'
    result=assess_one(digital,digital)['rows'][0]
    assert [(f['token_start'],f['token_end']) for f in result['fragments']]==[(0,3),(3,6)]
    assert result['fragments'][1]['reason']=='computational-token-limit'


@pytest.mark.parametrize('physical',[169,170])
def test_known_wrong_source_windows_never_become_plausible_counterparts(physical):
    text='ὁ λόγος ἀληθής'
    report=assess.candidates([row(text,page=physical)],library(text,page=physical))
    result=report['rows'][0]
    assert result['classification']=='unaligned' and result['comparison_status']=='source-mapping-exception'
    assert report['pages'][0]['text']==text and report['pages'][0]['source_mapping_exception']
    assert not report['pages'][0]['usable_for_counterparts']
    assert all(t['counterpart_indices']==[] for t in result['tokens'])
    assert report['counts']['source_mapping_exception_pages']==1


def test_missing_digital_section_and_empty_current_row_remain_explicitly_unaligned():
    report=assess.candidates([row('λόγος',page=3),row('',page=2)],library())
    assert all(r['classification']=='unaligned' for r in report['rows'])
    assert next(r for r in report['rows'] if r['physical_page']==3)['comparison_status']=='digital-section-missing'
    assert report['counts']['missing_digital_sections']==1


def test_full_original_current_and_digital_inputs_are_pinned_without_mutation():
    current=[row('ὁ λόγος')];original=[row('ὁ λόγος 1 ἄλλος apparatus')];digital=library('ὁ λόγος')
    frozen=deepcopy((current,original,digital))
    raw=b'\n'.join(assess.canonical(r) for r in current)+b'\n'
    oldraw=b'\n'.join(assess.canonical(r) for r in original)+b'\n'
    compressed=gzip.compress(assess.canonical(digital),mtime=0)
    report=assess.candidates(raw,compressed,original_rows=oldraw,input_pins={'external':'pinned'})
    assert (current,original,digital)==frozen
    assert report['rows'][0]['current_row']==current[0] and report['rows'][0]['original_row']==original[0]
    assert report['input_pins']['digital_archive_sha256']==assess.sha(compressed)
    assert report['input_pins']['current_rows_sha256']==assess.sha(raw)
    assert report['input_pins']['original_rows_sha256']==assess.sha(oldraw)
    assert assess.encode(report)==assess.encode(assess.candidates(raw,compressed,original_rows=oldraw,input_pins={'external':'pinned'}))


def test_only_historical_rows_without_full_consensus_are_assessed():
    values=[row('λόγος'),row('λόγος',number=2,ocr_consensus={'slots':[]}),
            {'urn':'photius.bibliotheca','locus':'photius_bekker1824_0245.1','text':'λόγος'}]
    report=assess.candidates(values,library('λόγος'))
    assert report['counts']['rows']==1


def test_source_pins_cannot_be_overridden_and_required_originals_cannot_be_omitted():
    with pytest.raises(ValueError):assess_one('λόγος','λόγος',input_pins={'current_rows_sha256':'forged'})
    with pytest.raises(ValueError):assess_one('λόγος','λόγος',original_rows=[])


@pytest.mark.parametrize('defect',['duplicate-row','duplicate-original','duplicate-section','wrong-edition','wrong-work'])
def test_repeated_or_incompatible_identities_reject_before_reporting_candidates(defect):
    values=[row('λόγος')];digital=library('λόγος');kwargs={}
    if defect=='duplicate-row':values.append(deepcopy(values[0]))
    elif defect=='duplicate-original':kwargs['original_rows']=[row('λόγος'),row('λόγος')]
    elif defect=='duplicate-section':digital['sections'].append(deepcopy(digital['sections'][0]))
    elif defect=='wrong-edition':digital['id']='other'
    elif defect=='wrong-work':values[0]['urn']='other'
    with pytest.raises(ValueError):assess.candidates(values,digital,**kwargs)


def test_cli_write_check_are_limited_to_assessment_file_and_detect_changed_inputs(tmp_path,monkeypatch):
    report=assess_one('ὁ λόγος','ὁ λόγος')
    monkeypatch.setattr(assess,'ROOT',tmp_path)
    monkeypatch.setattr(assess,'build',lambda:deepcopy(report))
    monkeypatch.setattr(sys,'argv',['assessment','--write']);assess.main()
    assert list(p for p in tmp_path.rglob('*') if p.is_file())==[tmp_path/assess.OUT]
    monkeypatch.setattr(sys,'argv',['assessment','--check']);assess.main()
    report['input_pins']['current_rows_sha256']='changed'
    with pytest.raises(SystemExit):assess.main()


def root_fixture(tmp_path,monkeypatch):
    current=b'\n'.join(assess.canonical(r) for r in [row('ὁ λογος')])+b'\n'
    original=b'\n'.join(assess.canonical(r) for r in [row('ὁ λογος 1 apparatus')])+b'\n'
    digital=gzip.compress(assess.canonical(library('ὁ λόγος')),mtime=0)
    exceptions=[{'retained_legacy_scan_page':p,'authorial_printed_page':v['authorial_printed_page'],
        'combined_scan_printed_page':v['digital_scan_printed_page'],'logical_combined_position':p+277,
        'source':{'sha256':assess.SOURCE_PDF_SHA256}} for p,v in assess.MAPPING_EXCEPTIONS.items()]
    coverage={'source_scan_exceptions':exceptions,'legacy_source':{'sha256':assess.SOURCE_PDF_SHA256},
        'source_library':{'edition':'tlg4040.tlg001.local002','sha256':assess.sha(digital),
            'url':'https://example.org/licensed-digital.json.gz',
            'license':{'url':'https://creativecommons.org/licenses/by-sa/4.0/'},
            'rights':'Source Library transcription rights.',
            'separate_api_notice':{'tdm_reservation':1,'tdm_policy':'https://example.org/licensing'}}}
    for path,raw in ((assess.CORPUS,current),(assess.ORIGINAL,gzip.compress(original,mtime=0)),
                     (assess.LIBRARY,digital),(assess.COVERAGE,assess.encode(coverage))):
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True);(tmp_path/path).write_bytes(raw)
    monkeypatch.setattr(assess,'LIBRARY_SHA256',assess.sha(digital))
    monkeypatch.setattr(assess,'ORIGINAL_SHA256',assess.sha(original))
    return coverage


def test_build_records_exact_public_source_paths_and_never_writes_an_audit(tmp_path,monkeypatch):
    root_fixture(tmp_path,monkeypatch)
    before={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    report=assess.build(tmp_path)
    assert report['counts']['rows']==1 and report['rows'][0]['classification']=='mark-only'
    assert report['input_pins']['current_corpus']['path']==assess.CORPUS.as_posix()
    assert report['digital_source']['credit']['separate_api_notice']['tdm_reservation']==1
    assert report['digital_source']['credit']['rights']=='Source Library transcription rights.'
    assert report['input_pins']['recipe']['sha256']==assess.RECIPE_SHA256
    assert not (tmp_path/assess.OUT).exists()
    assert before=={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert str(tmp_path) not in assess.encode(report).decode()


@pytest.mark.parametrize('change',['digital','original','mapping','source','credit'])
def test_build_rejects_changed_frozen_sources_and_mapping_authority(tmp_path,monkeypatch,change):
    coverage=root_fixture(tmp_path,monkeypatch)
    if change=='digital':(tmp_path/assess.LIBRARY).write_bytes(gzip.compress(assess.encode(library('ἄλλος'))))
    elif change=='original':(tmp_path/assess.ORIGINAL).write_bytes(gzip.compress(b'changed'))
    else:
        if change=='mapping':coverage['source_scan_exceptions'][0]['combined_scan_printed_page']=434
        elif change=='credit':coverage['source_library']['sha256']='a'*64
        else:coverage['source_scan_exceptions'][0]['source']['sha256']='a'*64
        (tmp_path/assess.COVERAGE).write_bytes(assess.encode(coverage))
    with pytest.raises(ValueError):assess.build(tmp_path)


@pytest.mark.parametrize('when',['before-run','during-run'])
def test_changed_executable_recipe_cannot_be_claimed_as_the_assessment_recipe(tmp_path,monkeypatch,when):
    root_fixture(tmp_path,monkeypatch)
    original=Path.read_bytes;calls=0
    def changed_read(path):
        nonlocal calls
        if path==assess.RECIPE_FILE:
            calls+=1
            if when=='before-run' or calls>1:return b'Changed source after the running module was loaded.'
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',changed_read)
    with pytest.raises(ValueError,match='code changed'):assess.build(tmp_path)
    assert not (tmp_path/assess.OUT).exists()
