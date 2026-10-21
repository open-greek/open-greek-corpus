"""Occurrence matching must not duplicate affixes or choose repeated passages."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_photius_editorial_substitutions as preparation


def test_partial_word_trims_verified_suffix():
    result=preparation.render_reading('ἄν','ἄνθρωπον',0,2,'ἄνθρωπον')
    assert result['corrected_text']=='ἄν'
    assert result['trim']=={'prefix':'','suffix':'θρωπον'}


def test_partial_word_retains_verified_prefix_and_suffix():
    text='Ἀνεγνώθησαν'; start=len('Ἀνεγνώ')
    result=preparation.render_reading('θ',text,start,start+1,'Ἀνεγνώσθησαν')
    assert result['corrected_text']=='σθ'


def test_incompatible_verified_affix_is_not_overwritten():
    assert preparation.render_reading('ἄν','ἄνθρωπον',0,2,'ἄνθρωπος') is None


def test_outer_punctuation_survives():
    result=preparation.render_reading('[λέγει]','[λέγει]',0,7,'λέγεις')
    assert result['corrected_text']=='[λέγεις]'


def test_elision_is_not_doubled_or_dropped():
    result=preparation.render_reading('κατ’','κατ’',0,4,'κατ’')
    assert result['corrected_text']=='κατ’'


def test_full_source_ending_consumes_old_abbreviation_mark():
    result=preparation.render_reading('εἴρη’','εἴρη’',0,5,'εἴρηται')
    assert result['corrected_text']=='εἴρηται'


def test_source_numeral_mark_is_not_doubled_by_normalization():
    original='ἐτῶν γʹ'
    result=preparation.render_reading(original,original,0,len(original),'ἔτη γʹ')
    assert result['corrected_text']=='ἔτη γʹ'
    result=preparation.render_reading('κατα','κατα',0,4,'κατ’')
    assert result['corrected_text']=='κατ’'


def test_empty_match_does_not_authorize_deletion():
    assert preparation.render_reading('μή','μή',0,2,'') is None


def test_internal_punctuation_needs_explicit_mapping():
    assert preparation.render_reading('γένηται. Ὁ','γένηται. Ὁ',0,10,'γένηται Ὁ') is None


def test_coordinate_translation_uses_exact_prior_lengths():
    decision={'start':0,'end':2,'corrected_text':'τέσσερα'}
    assert preparation.shifted(3,5,[decision])==(8,10)


def test_whole_passage_neutral_spelling_cannot_select_a_repeat():
    keys=['alpha','beta','gamma','unknown','delta','epsilon']
    source=[{'key':x} for x in keys]
    digital=[{'key':x} for x in keys[:3]+['one']+keys[4:]+keys[:3]+['two']+keys[4:]]
    assert preparation.ordered_fallback(source,{3},{0,1,2,4,5},digital) is None


def test_whole_passage_unique_mapping_ignores_uncertain_spelling():
    keys=['alpha','beta','gamma','unknown','delta','epsilon','zeta']
    source=[{'key':x} for x in keys]
    digital=[{'key':x} for x in keys[:3]+['chosen']+keys[4:]]
    result=preparation.ordered_fallback(source,{3},{0,1,2,4,5,6},digital)
    assert result['counterparts'][3]==[3]
