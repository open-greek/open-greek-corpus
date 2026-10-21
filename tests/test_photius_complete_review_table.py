"""Qualifications in authored source tables must not silently disappear."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from photius_complete_review_table import compile_table


def build(**changes):
    values = dict(rows={
        'helladius_chrestomathia_photius_bekker_v2_0240.1': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0240.1', 'text': 'κεφαλή'},
        'helladius_chrestomathia_photius_bekker_v2_0240.2': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0240.2', 'text': 'λέξις λέξις'},
        'helladius_chrestomathia_photius_bekker_v2_0240.3': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0240.3', 'text': 'τέλος'},
    }, document=object(), crop_png=lambda *args: b'pinned-source-crop',
        sections={'tlg4040-tlg001-local002-s517': 'λέξις λέξις τέλος'},
        page=240, reviewed_at='2026-10-21T12:00:00Z',
        text={1:'κεφαλή',2:'λέξις λέξις',3:'τέλος'},
        regions={n:[0,0,1,1] for n in (1,2,3)},
        digital_starts={1:None,2:0,3:'τέλος'})
    values.update(changes)
    return compile_table(**values)


def test_absent_digital_header_does_not_steal_body_window():
    records = build(roles={1:'editorial-note'})
    assert 'readings' not in records[0]['segments'][0]
    assert records[0]['segments'][0]['text_role'] == 'editorial-note'
    assert records[1]['segments'][0]['readings'][0]['text'] == 'λέξις λέξις '
    assert records[2]['segments'][0]['readings'][0]['text'] == 'τέλος'


def test_exact_offset_preserves_one_of_repeated_uncertain_forms():
    records = build(text={1:'κεφαλή',2:'λέξις {u0}',3:'τέλος'},
        uncertainties={2:[({'start':6,'text':'λέξις'},'λέξις/λέξης',{'start':6,'text':'λέξις'},'Indistinct ending.')]})
    assert records[1]['status'] == 'reviewed-with-uncertainty'
    assert records[1]['segments'][1]['start'] == 6
    assert records[1]['segments'][1]['corrected_text'] == 'λέξις'
    assert records[1]['segments'][1]['scan']['observed_text'] == 'λέξις/λέξης'
    assert records[1]['segments'][1]['readings'][0]['start'] == 6
    assert records[1]['segments'][0]['readings'][0]['text'] == 'λέξις '


def test_changed_digital_uncertainty_offset_fails():
    with pytest.raises(ValueError, match='digital uncertainty offset'):
        build(text={1:'κεφαλή',2:'λέξις {u0}',3:'τέλος'},
            uncertainties={2:[({'start':6,'text':'λέξις'},'λέξις?',{'start':5,'text':'λέξις'},'Indistinct ending.')]})


def test_changed_explicit_uncertainty_offset_fails():
    with pytest.raises(ValueError, match='offset changed'):
        build(text={1:'κεφαλή',2:'λέξις {u0}',3:'τέλος'},
            uncertainties={2:[({'start':5,'text':'λέξις'},'λέξις?','λέξις','Indistinct ending.')]})


def test_unrecorded_uncertainty_cannot_become_verified_text():
    with pytest.raises(ValueError, match='placeholder'):
        build(text={1:'κεφαλή',2:'λέξις {u0}',3:'τέλος'})


@pytest.mark.parametrize('field', ['uncertainties','fragments','roles'])
def test_qualification_for_missing_passage_fails(field):
    with pytest.raises(ValueError, match='unenumerated passage'):
        build(**{field:{99:[]}})


from test_photius_review_campaign import fixture, compile_fixture
import prepare_photius_review_campaign as campaign


def authored(fixture, **extra):
    import pymupdf
    row = fixture['rows'][0]
    section = fixture['manifest']['rows'][0]['digital_section']
    with pymupdf.open(stream=fixture['inputs'][1], filetype='pdf') as document:
        return compile_table({row['locus']: row}, document, campaign.crop_png,
            {section: fixture['digital']}, page=2, reviewed_at='2026-10-21T10:00:00Z',
            text={1:'ὁ {u0} ἀληθές.\n'}, regions={1:[.1,.1,.9,.9]},
            digital_starts={1:0}, uncertainties={1:[('λόγος','[λόγος/λόγου]','λόγος',
                'The final printed letters are damaged and cannot be certified.')]}, **extra)


def test_literal_uncertainty_preserves_original_and_both_source_witnesses(fixture):
    fixture['reviews']['records'] = authored(fixture)
    row = compile_fixture(fixture)['rows'][0]
    assert row['status'] == 'reviewed-with-uncertainty'
    assert campaign.replay_text(row, fixture['rows'][0]['text']) == fixture['rows'][0]['text']
    uncertain = row['segments'][1]
    assert uncertain['scan']['observed_text'] == '[λόγος/λόγου]'
    assert uncertain['corrected_text'] == 'λόγος'
    assert next(r for r in uncertain['readings'] if r['kind']=='digital')['text'] == 'λόγος'
    assert next(r for r in row['segments'][-1]['readings'] if r['kind']=='digital')['text'] == ' ἀληθής.\n'


def test_unknown_fragment_row_is_rejected(fixture):
    with pytest.raises(ValueError, match='unenumerated'):
        authored(fixture, fragments={2:[('λόγος','leading')]})


def test_crop_cache_cannot_reuse_pixels_from_another_pdf(fixture):
    import pymupdf
    with pymupdf.open(stream=fixture['inputs'][1], filetype='pdf') as first:
        a = campaign.crop_png(first, 2, [.1,.1,.9,.9])
        assert campaign.crop_png(first, 2, [.1,.1,.9,.9]) is a
    with pymupdf.open() as second:
        for _ in range(2):
            page = second.new_page(width=120, height=180)
            page.insert_text((15,40), 'Different source witness')
        assert campaign.crop_png(second, 2, [.1,.1,.9,.9]) != a
