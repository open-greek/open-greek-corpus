"""Occurrence-specific ties cannot expand into the following verified clause."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import photius_remaining_manual_d as manual


def case(monkeypatch):
    spec=deepcopy(manual.SPECS[0])
    units=[{'text':'παιδὸς βεβίασται. Ἀλλ’ ὦ πολέμου', 'html_line':1,
            'html_column':0,'unit_index':0,'codex':'243','bekker':'359b'}]
    spec.update(selection=(0,1,'βεβίασται'),context_sha256=manual._digest(units))
    monkeypatch.setattr(manual,'SPECS',[spec])
    return (spec['locus'],spec['segment_index']),manual._record(spec,units)


def test_short_word_excludes_following_address(monkeypatch):
    key,record=case(monkeypatch)
    assert manual.validate_record(key,record)==record
    assert [t['text'] for t in record['readings'][0]['tokens']]==['βεβίασται']


@pytest.mark.parametrize('field',['kind','role','reviewed_at','original_text',
    'original_row_sha256','inherited_record_sha256','evidence','readings',
    'rendering','manual_context','surface_sha256','source_indices'])
def test_all_authority_fields_are_pinned(monkeypatch,field):
    key,record=case(monkeypatch)
    record[field]='changed'
    with pytest.raises(ValueError):manual.validate_record(key,record)


def test_extra_permissions_and_source_ref_changes_fail(monkeypatch):
    key,record=case(monkeypatch)
    extra=deepcopy(record);extra['allow_fragment']=True
    with pytest.raises(ValueError):manual.validate_record(key,extra)
    record['manual_context']['units'][0]['html_line']=2
    with pytest.raises(ValueError):manual.validate_record(key,record)


def test_unknown_identity_and_ambiguous_context_fail(monkeypatch):
    key,record=case(monkeypatch)
    with pytest.raises(ValueError):manual.validate_record((key[0],999),record)
    spec=manual.SPECS[0];units=record['manual_context']['units']
    units[0]['text']+=' βεβίασται';spec['context_sha256']=manual._digest(units)
    with pytest.raises(ValueError,match='exactly once'):manual._record(spec,units)


def test_right_context_distinguishes_enumerated_term_from_later_explanation(monkeypatch):
    spec=deepcopy(manual.SPECS[-1])
    units=[{'text':'ἁδρόν, τὸ δὲ ἰσχνόν, τὸ δὲ μέσον. τὸ δὲ ἰσχνὸν τὴν τροπικὴν',
            'html_line':1,'html_column':0,'unit_index':0,'codex':'239','bekker':'318b'}]
    spec.update(selection=(0,1,'ἰσχνόν'),context_sha256=manual._digest(units))
    monkeypatch.setattr(manual,'SPECS',[spec])
    record=manual._record(spec,units)
    token=record['readings'][0]['tokens'][0]
    assert token['refs'][0]['start']==units[0]['text'].index('ἰσχνόν')
    assert manual.validate_record((spec['locus'],spec['segment_index']),record)==record
