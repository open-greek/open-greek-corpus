"""Complete campaign admission preserves evidence, masks, and exact preimages."""
from copy import deepcopy
import gzip
import json

import pytest

from test_photius_review_campaign import fixture, compile_fixture, segment, slice_segment
import prepare_photius_review_campaign as campaign
import repair_photius_complete_review as layer
import reviewed_manifestations
import build_ocr_quality_report as quality
import build_photius_review_observations as driver


def save(tmp_path, before, compiled):
    outputs, audit = layer.artifacts(before, campaign.encode(compiled))
    for path, raw in {campaign.BASELINE: gzip.compress(before, mtime=0), **outputs}.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(raw)
    return outputs, audit


def test_partial_campaign_cannot_be_admitted(fixture):
    fixture['reviews']['records'] = []
    compiled = compile_fixture(fixture)
    with pytest.raises(ValueError, match='completely source-reviewed'):
        layer.plan(fixture['inputs'][0], campaign.encode(compiled))


def test_exact_replay_and_undo_need_no_live_source_files(fixture, tmp_path):
    compiled = compile_fixture(fixture)
    before = fixture['inputs'][0]
    outputs, audit = save(tmp_path, before, compiled)
    after = outputs[campaign.CORPUS]
    assert layer.restore_before_bytes(after, tmp_path) == before
    row = json.loads(after)
    assert layer.restore_before_row(row, tmp_path) == fixture['rows'][0]
    assert row['prior_audit'] == fixture['rows'][0]['prior_audit']
    assert not campaign.tokens(' '.join(layer.lexical_segments(row, tmp_path)))
    assert audit['counts']['fully_source_reviewed_rows'] == 1
    layer.undo(tmp_path)
    assert (tmp_path / campaign.CORPUS).read_bytes() == before


def test_conflicting_digital_forms_remain_recorded_and_outside_scalar_counts(fixture, tmp_path):
    reviewed = segment(fixture)
    reviewed['readings'] = [{'kind': 'digital', 'section': fixture['manifest']['rows'][0]['digital_section'],
        'start': 0, 'end': len(fixture['digital']), 'text': fixture['digital']}]
    compiled = compile_fixture(fixture)
    outputs, _ = save(tmp_path, fixture['inputs'][0], compiled)
    row = json.loads(outputs[campaign.CORPUS])
    assert 'ἀληθές' in row['text']
    assert 'ἀληθές' not in row['analysis_text'] and 'ἀληθής' not in row['analysis_text']
    stored = json.loads(gzip.decompress(outputs[layer.REVIEW]))
    assert stored['rows'][0]['segments'][0]['readings'][-1]['text'] == fixture['digital']
    assert layer.restore_before_row(row, tmp_path) == fixture['rows'][0]


def test_source_uncertainty_breaks_adjacency_without_changing_original_display(fixture, tmp_path):
    first, middle, last = (slice_segment(fixture, 0, 2), slice_segment(fixture, 2, 7),
                           slice_segment(fixture, 7, len(fixture['rows'][0]['text'])))
    middle.update(verification='uncertain', uncertainty='The source word is damaged.')
    middle['scan']['observed_text'] = '[λόγος?]'
    for item in (first, last):
        item['readings'] = [{'kind':'digital',
            'section':fixture['manifest']['rows'][0]['digital_section'],
            'start':0,'end':len(fixture['digital']),'text':fixture['digital']}]
    fixture['reviews']['records'][0].update(status='reviewed-with-uncertainty', segments=[first, middle, last])
    outputs, _ = save(tmp_path, fixture['inputs'][0], compile_fixture(fixture))
    row = json.loads(outputs[campaign.CORPUS])
    assert row['text'] == fixture['rows'][0]['text']
    runs = layer.lexical_segments(row, tmp_path)
    assert 'λόγος' not in ''.join(runs)
    assert 'ἀληθές' not in ''.join(runs)
    assert not any('ὁ ἀληθές' in run for run in runs)
    assert row['complete_source_review']['status'] == 'reviewed-with-uncertainty'


@pytest.mark.parametrize('role', ['unclassified-small-type', 'unclassified-heading', 'editorial-note', 'marginal-reference'])
def test_source_review_does_not_admit_unclassified_or_editorial_words(fixture, tmp_path, role):
    segment(fixture)['text_role'] = role
    outputs, _ = save(tmp_path, fixture['inputs'][0], compile_fixture(fixture))
    row = json.loads(outputs[campaign.CORPUS])
    assert row['text'] == fixture['rows'][0]['text']
    assert not row['analysis_text'].strip()
    assert not any(run.strip() for run in layer.lexical_segments(row, tmp_path))


def test_changed_corpus_row_or_record_authority_cannot_restore(fixture, tmp_path):
    outputs, _ = save(tmp_path, fixture['inputs'][0], compile_fixture(fixture))
    row = json.loads(outputs[campaign.CORPUS])
    changed = deepcopy(row)
    changed['text'] += 'x'
    with pytest.raises(ValueError, match='postimage'):
        layer.restore_before_row(changed, tmp_path)
    with pytest.raises(ValueError, match='postimage'):
        layer.restore_before_bytes(outputs[campaign.CORPUS] + b'\n', tmp_path)
    changed = deepcopy(row)
    changed['complete_source_review']['source_review']['campaign_id'] = 'other-campaign'
    with pytest.raises(ValueError, match='authority changed'):
        layer.restore_before_row(changed, tmp_path)


def test_prior_tied_readings_cannot_silently_regain_lexical_eligibility():
    old = {'text': 'ὁ ⟦λόγος ∥ λόγου⟧ τέλος',
           'historical_reading_batch_projection': {'excluded_spans': [
               {'start': 2, 'end': 17, 'text': '⟦λόγος ∥ λόγου⟧'}]}}
    new = 'ὁ λόγος τέλος'
    exclusions = layer._inherited_exclusions(old, new)
    _, runs = layer._projection(new, exclusions)
    assert runs == ['ὁ ', ' τέλος']
    assert all(s['classification'] == 'retained-prior-source-uncertainty' for s in exclusions)


def test_source_component_ownership_moves_once_without_double_counting_audits():
    components = [{'role': 'retained-primary', 'passages': 3},
                  {'role': 'reviewed-historical-reading-occurrences', 'passages': 2},
                  {'role': 'later-reviewed-historical-occurrences', 'passages': 4},
                  {'role': 'comparison-witness', 'license': 'CC-BY-SA-4.0'}]
    complete = {'counts': {'fully_source_reviewed_rows': 7},
                'replaced_component_passages': {'retained-primary': 2,
                    'reviewed-historical-reading-occurrences': 2,
                    'later-reviewed-historical-occurrences': 3}}
    updated = reviewed_manifestations._complete_photius_components(components, complete)
    assert [c.get('passages', 0) for c in updated] == [1, 0, 1, 0, 7]
    assert sum(c.get('passages', 0) for c in updated) == 9
    assert [c.get('passages', 0) for c in components] == [3, 2, 4, 0]
    complete['replaced_component_passages']['retained-primary'] = 4
    with pytest.raises(ValueError, match='partition earlier'):
        reviewed_manifestations._complete_photius_components(components, complete)


def test_quality_report_refuses_stale_review_accounting(fixture, tmp_path, monkeypatch):
    compiled = compile_fixture(fixture)
    outputs = {campaign.OUT: campaign.artifact_bytes(campaign.OUT, compiled),
               campaign.REVIEWS: campaign.artifact_bytes(campaign.REVIEWS, fixture['reviews'])}
    for path, raw in {campaign.MANIFEST: b'{}', campaign.CORPUS: fixture['inputs'][0], **outputs}.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(raw)
    monkeypatch.setattr(driver, 'build', lambda root: (outputs, compiled))
    monkeypatch.setattr(layer, 'active_metadata', lambda root: None)
    report = quality.complete_review_qualification(tmp_path)
    assert report['counts']['complete_scan_review_rows'] == 1
    assert not report['corpus_admission_complete']
    (tmp_path / campaign.REVIEWS).write_bytes(b'changed observations')
    with pytest.raises(ValueError, match='accounting is stale'):
        quality.complete_review_qualification(tmp_path)


def test_missing_review_scope_is_unavailable_rather_than_zero_coverage(tmp_path):
    assert quality.complete_review_qualification(tmp_path) is None


def test_unpaired_available_witness_cannot_silently_supply_scalar_lexical_evidence(fixture):
    record = compile_fixture(fixture)['rows'][0]
    assert record['digital_counterparts_usable']
    masks = layer._digital_exclusions(record)
    assert masks and all(m['classification']=='unpaired-available-digital-witness' for m in masks)
    assert not campaign.tokens(' '.join(layer._projection(record['corrected_text'], masks)[1]))
    # Known mismapped digital sections are explicitly unavailable. Complete
    # source review remains usable without pretending those sections agree.
    record['digital_counterparts_usable'] = False
    assert layer._digital_exclusions(record) == []
