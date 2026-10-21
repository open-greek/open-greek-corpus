"""Pilot sampling and source decisions remain exact, public, and nonadmitting."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_photius_uncertainty_pilot as pilot


@pytest.fixture
def scope(monkeypatch):
    text = 'ἀρχὴ ἀσαφές τέλος'
    a, b = text.index('ἀσαφές'), text.index(' τέλος')
    locus = 'helladius_chrestomathia_photius_bekker_v2_0004.17'
    source = {'path': 'data/scan.pdf', 'sha256': pilot.sha(b'scan')}
    segment = {'verification': 'uncertain', 'text_role': 'authorial-body',
        'corrected_start': a, 'corrected_end': b, 'corrected_text': text[a:b],
        'uncertainty': 'The accent is unclear.',
        'scan': {'region': [0.1, 0.2, 0.8, 0.4], 'max_side': 3600,
                 'observed_text': text[a:b], 'image_sha256': pilot.sha(b'crop')}}
    mask = {'start': a, 'end': b, 'text': text[a:b],
            'classification': 'unresolved-source-reading', 'qualification': segment['uncertainty']}
    old = {'urn': 'photius.bibliotheca', 'locus': locus, 'text': text,
           'analysis_text': 'ἀρχὴ  τέλος',
           'complete_source_review': {'excluded_spans': [mask]},
           'photius_context_review': {'excluded_spans': [mask]}}
    before = pilot.campaign.canonical(old) + b'\n'
    compiled = {'schema': pilot.campaign.COMPILED_SCHEMA, 'scope_complete': True,
        'input_pins': {'scan': source}, 'rows': [{'locus': locus, 'physical_page': 4,
            'printed_page': 269, 'segments': [segment]}]}
    previous = {'records': []}
    classification = {'records': [{'locus': locus, 'segment_index': 0,
        'match_status': 'unique', 'match_count': 1, 'anchor_count': 6,
        'local_candidates': ['restricted comparison text'], 'crop_path': '/Users/example/private.png'}]}
    chosen = pilot.select_sample(pilot.population(compiled, previous, classification), quotas={'unique': 1})
    decisions = [{'id': chosen[0]['id'], 'locus': locus, 'segment_index': 0,
        'original_text': text[a:b], 'corrected_text': 'ἀσαφής',
        'decision': 'resolved', 'evidence': 'The accent is visible in the pinned scan crop.'}]
    def pin(sources, files, source_id, page, region, max_side, images, rendered):
        path = pilot.ARCHIVE / 'source-images' / (pilot.sha(b'crop') + '.png')
        images[path] = b'crop'
        return {'source_id': source_id, 'source': sources[source_id], 'scan_page': page,
                'region': region, 'max_side': max_side,
                'image': {'path': path.as_posix(), 'sha256': pilot.sha(b'crop')}}
    monkeypatch.setattr(pilot, '_source_pin', pin)
    return {'before': before, 'compiled': compiled, 'previous': previous,
        'classification': classification, 'decisions': decisions,
        'reviewed_at': '2026-10-21T20:00:00Z', 'source_files': {'data/scan.pdf': b'scan'},
        'quotas': {'unique': 1}}


def compile_scope(scope):
    return pilot.compile_review(**scope)


def test_public_sample_and_exact_candidate_undo_preserve_prior_tags(scope):
    sample, review, classification, images = compile_scope(scope)
    public = pilot.encode([sample, review, classification]).decode()
    assert 'restricted comparison text' not in public
    assert '/Users/' not in public and 'local_candidates' not in public and 'crop_path' not in public
    assert sample['count'] == 1 and sample['crops'] == 1
    assert images and review['admission_authorized'] is False
    after, changes = pilot.plan(scope['before'], review)
    old, new = json.loads(scope['before']), json.loads(after)
    assert old['text'] == 'ἀρχὴ ἀσαφές τέλος' and new['text'] == 'ἀρχὴ ἀσαφής τέλος'
    assert new['complete_source_review'] == old['complete_source_review']
    assert new['photius_context_review'] == old['photius_context_review']
    assert new[pilot.TAG]['admission_authorized'] is False
    assert not new[pilot.TAG]['excluded_spans']
    assert pilot.unapply(after, changes, before_sha256=pilot.sha(scope['before'])) == scope['before']
    assert pilot.replay(scope['before'], changes, before_sha256=pilot.sha(scope['before']),
                        after_sha256=pilot.sha(after)) == after
    assert compile_scope(scope) == (sample, review, classification, images)


def test_candidate_undo_restores_noncanonical_original_bytes(scope):
    scope['before'] = (json.dumps(json.loads(scope['before']), ensure_ascii=False, indent=None) + '\n').encode()
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    assert pilot.unapply(after, changes, before_sha256=pilot.sha(scope['before'])) == scope['before']


def test_retained_uncertainty_keeps_exact_text_and_mask(scope):
    decision = scope['decisions'][0]
    decision.update(decision='retained-uncertain', corrected_text=decision['original_text'],
                    alternatives=['ἀσαφές', 'ἀσαφής'])
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    row = json.loads(after)
    assert row['text'] == json.loads(scope['before'])['text']
    assert changes[0]['removed_uncertainty_causes'] == []
    assert row[pilot.TAG]['excluded_spans'][0]['evidence'][0]['classification'] == 'unresolved-source-reading'


def test_unrelated_overlapping_exclusion_remains_and_is_rebased(scope):
    old = json.loads(scope['before'])
    inherited = {'start': 0, 'end': len(old['text']), 'text': old['text'],
                 'classification': 'independent-digital-disagreement'}
    old['photius_context_review']['excluded_spans'].append(inherited)
    scope['before'] = pilot.campaign.canonical(old) + b'\n'
    scope['decisions'][0]['corrected_text'] = 'ἀσαφέστατος'
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    new = json.loads(after)
    assert new['analysis_text'].strip() == ''
    assert changes[0]['remaining_exclusion_causes'][0]['classification'] == 'independent-digital-disagreement'
    assert changes[0]['remaining_exclusion_causes'][0]['text'] == new['text']
    assert changes[0]['remaining_exclusion_causes'][0]['rebase']['original_exclusion'] == inherited


@pytest.mark.parametrize('defect', ['missing', 'extra', 'duplicate', 'false-label'])
def test_classification_requires_complete_and_consistent_scope(scope, defect):
    items = scope['classification']['records']
    if defect == 'missing':
        items.clear()
    elif defect == 'extra':
        items.append({**items[0], 'segment_index': 19})
    elif defect == 'duplicate':
        items.append(deepcopy(items[0]))
    else:
        items[0]['match_count'] = 2
    with pytest.raises(ValueError, match='Classification'):
        compile_scope(scope)


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'wrong-id', 'wrong-original', 'silent-retained-change', 'private'])
def test_reviews_account_for_every_selected_span_without_silent_changes(scope, defect):
    records = scope['decisions']
    if defect == 'missing':
        records.clear()
    elif defect == 'duplicate':
        records.append(deepcopy(records[0]))
    elif defect == 'wrong-id':
        records[0]['id'] = 'P999'
    elif defect == 'wrong-original':
        records[0]['original_text'] = 'another reading'
    elif defect == 'silent-retained-change':
        records[0]['decision'] = 'retained-uncertain'
    else:
        records[0]['evidence'] = '/Users/example/private.png'
    with pytest.raises(ValueError):
        compile_scope(scope)


def test_only_remaining_segments_are_eligible_and_prior_offset_changes_are_preserved(scope):
    old = json.loads(scope['before'])
    text = old['text']; delta = len('προοίμιον ') - len('ἀρχὴ ')
    old['text'] = text.replace('ἀρχὴ ', 'προοίμιον ', 1)
    old['photius_uncertainty_review'] = {'frozen': 'prior-tag',
        'excluded_spans': [{**mask, 'start': mask['start'] + delta, 'end': mask['end'] + delta}
                           for mask in old['photius_context_review']['excluded_spans']]}
    scope['before'] = pilot.campaign.canonical(old) + b'\n'
    scope['previous']['records'] = [{'locus': old['locus'], 'segment_index': 19,
        'decision': 'resolved', 'start': 0, 'end': len('ἀρχὴ '), 'corrected_text': 'προοίμιον '}]
    _, review, _, _ = compile_scope(scope)
    assert review['records'][0]['start'] == text.index('ἀσαφές') + delta
    after, changes = pilot.plan(scope['before'], review)
    assert json.loads(after)['photius_uncertainty_review'] == old['photius_uncertainty_review']
    assert pilot.unapply(after, changes, before_sha256=pilot.sha(scope['before'])) == scope['before']


def test_selection_is_order_independent_and_enforces_six_per_crop_per_stratum():
    values = [{'locus': f'row-{i:03d}', 'segment_index': 0, 'stratum': 'unique',
               'physical_page': 1, 'group': 'same-crop'} for i in range(7)]
    chosen = pilot.select_sample(values, quotas={'unique': 6})
    assert chosen == pilot.select_sample(list(reversed(values)), quotas={'unique': 6})
    assert len(chosen) == 6
    with pytest.raises(ValueError, match='cannot meet'):
        pilot.select_sample(values, quotas={'unique': 7})


def test_primary_crop_hash_is_checked_against_frozen_review(scope, monkeypatch):
    scope['compiled']['rows'][0]['segments'][0]['scan']['image_sha256'] = 'forged'
    with pytest.raises(ValueError, match='crop does not reproduce'):
        compile_scope(scope)


@pytest.mark.parametrize('defect', ['postimage', 'preimage', 'raw-preimage', 'missing-row'])
def test_undo_rejects_tampered_or_incomplete_candidates(scope, defect):
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    if defect == 'postimage':
        row = json.loads(after); row['text'] += 'x'; after = pilot.campaign.canonical(row) + b'\n'
    elif defect == 'preimage':
        changes[0]['original_row']['text'] += 'x'
    elif defect == 'raw-preimage':
        changes[0]['original_line'] = '{}\n'
    else:
        after = b''
    with pytest.raises(ValueError, match='Pilot undo'):
        pilot.unapply(after, changes, before_sha256=pilot.sha(scope['before']))


def test_independent_nonbody_exclusion_cannot_be_removed_by_source_resolution(scope):
    old = json.loads(scope['before'])
    mask = deepcopy(old['photius_context_review']['excluded_spans'][0])
    mask.update(classification='nonbody-source-material', qualification='Source heading.')
    old['photius_context_review']['excluded_spans'].append(mask)
    scope['before'] = pilot.campaign.canonical(old) + b'\n'
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    assert changes[0]['remaining_exclusion_causes'][0]['classification'] == 'nonbody-source-material'
    assert 'ἀσαφής' not in json.loads(after)['analysis_text']


def test_real_crop_renderer_checks_source_bytes_and_exact_png():
    pymupdf = pytest.importorskip('pymupdf')
    with pymupdf.open() as document:
        page = document.new_page(width=200, height=300)
        page.insert_text((20, 50), 'source evidence')
        raw = document.tobytes()
    source = {'path': 'data/scan.pdf', 'kind': 'pdf', 'sha256': pilot.sha(raw)}
    images, cache = {}, {}
    pin = pilot._source_pin({'bekker': source}, {'data/scan.pdf': raw}, 'bekker', 1,
                           [0, 0, 1, 1], 400, images, cache)
    assert pilot.sha(next(iter(images.values()))) == pin['image']['sha256']
    assert len(cache) == 1
    with pytest.raises(ValueError, match='source changed'):
        pilot._source_pin({'bekker': source}, {'data/scan.pdf': raw + b'x'}, 'bekker', 1,
                          [0, 0, 1, 1], 400, images, cache)


def build_fixture(scope, tmp_path, monkeypatch):
    def write(path, raw):
        path = tmp_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    inputs = {pilot.CORPUS.as_posix(): scope['before'],
        pilot.COMPILED.as_posix(): gzip.compress(pilot.encode(scope['compiled']), mtime=0),
        pilot.CONTEXT.as_posix(): b'frozen-context',
        pilot.prior.REVIEW.as_posix(): pilot.encode(scope['previous']),
        'data/scan.pdf': b'scan'}
    for name, raw in inputs.items():
        write(name, raw)
    monkeypatch.setattr(pilot, 'PINNED_INPUTS', {name: pilot.sha(raw) for name, raw in inputs.items()})
    monkeypatch.setattr(pilot, 'QUOTAS', scope['quotas'])
    table = ('REVIEWED_AT = ' + repr(scope['reviewed_at']) + '\n'
             'TIMING = {"scan_review_seconds": 12.5}\n'
             'def records():\n    return ' + repr(scope['decisions']) + '\n').encode()
    write(pilot.TABLE, table)
    for name in ('prepare_photius_uncertainty_pilot.py', 'prepare_photius_review_campaign.py',
                 'repair_photius_uncertainties.py', 'audit_compression.py',
                 'compare_photius_local_edition.py', 'assess_photius_historical.py'):
        write(Path('scripts') / name, name.encode())
    classification = deepcopy(scope['classification'])
    classification.update(pins={'compiled_sha256': pilot.sha(inputs[pilot.COMPILED.as_posix()]),
        'context_sha256': pilot.sha(inputs[pilot.CONTEXT.as_posix()]),
        'prior_uncertainties_sha256': pilot.sha(inputs[pilot.prior.REVIEW.as_posix()]),
        'local_html_sha256': 'a' * 64}, elapsed_seconds=0.25)
    classification_path = tmp_path / 'private-input.json'
    write('private-input.json', pilot.encode(classification))
    return inputs, classification_path, write


def test_build_is_deterministic_only_emits_pilot_paths_and_preserves_baseline(scope, tmp_path, monkeypatch):
    inputs, classification_path, _ = build_fixture(scope, tmp_path, monkeypatch)
    files, audit = pilot.build(tmp_path, classification_path=classification_path)
    assert (files, audit) == pilot.build(tmp_path, classification_path=classification_path)
    assert all(path.is_relative_to(pilot.ARCHIVE) for path in files)
    assert all((tmp_path / name).read_bytes() == raw for name, raw in inputs.items())
    assert not (tmp_path / pilot.ARCHIVE).exists()
    assert audit['admission_authorized'] is False
    assert audit['counts']['served_corpus_changes'] == 0
    assert audit['counts']['sampled_spans'] == 1 and audit['counts']['resolved_changed'] == 1
    public = json.loads(files[pilot.CLASSIFICATION])
    assert public['elapsed_seconds'] == 0.25 and public['pins']['local_html_sha256'] == 'a' * 64
    assert 'local_candidates' not in files[pilot.CLASSIFICATION].decode()
    review = json.loads(files[pilot.ARCHIVE / 'source-review.json'])
    assert review['reviewer_timing'] == {'scan_review_seconds': 12.5}
    candidate = gzip.decompress(files[pilot.ARCHIVE / 'candidate-corpus.jsonl.gz'])
    changes = [json.loads(line) for line in gzip.decompress(files[pilot.ARCHIVE / 'records.jsonl.gz']).splitlines()]
    assert pilot.unapply(candidate, changes, before_sha256=audit['before_corpus_sha256']) == scope['before']
    assert pilot.replay(scope['before'], changes, before_sha256=audit['before_corpus_sha256'],
                        after_sha256=audit['candidate_corpus_sha256']) == candidate


def test_build_rejects_changed_public_authority_before_compilation(scope, tmp_path, monkeypatch):
    _, classification_path, write = build_fixture(scope, tmp_path, monkeypatch)
    write(pilot.CONTEXT, b'changed')
    with pytest.raises(ValueError, match='prior review authority changed'):
        pilot.build(tmp_path, classification_path=classification_path)


def test_build_rejects_classifier_labels_from_other_public_authorities(scope, tmp_path, monkeypatch):
    _, classification_path, _ = build_fixture(scope, tmp_path, monkeypatch)
    diagnostic = json.loads(classification_path.read_bytes())
    diagnostic['pins']['compiled_sha256'] = 'forged'
    classification_path.write_bytes(pilot.encode(diagnostic))
    with pytest.raises(ValueError, match='classifications differ'):
        pilot.build(tmp_path, classification_path=classification_path)


def test_build_rereads_inputs_and_recipes_after_compilation(scope, tmp_path, monkeypatch):
    _, classification_path, write = build_fixture(scope, tmp_path, monkeypatch)
    real_compile = pilot.compile_review
    def changed(*args, **kwargs):
        result = real_compile(*args, **kwargs)
        write(Path('scripts/prepare_photius_uncertainty_pilot.py'), b'changed during compile')
        return result
    monkeypatch.setattr(pilot, 'compile_review', changed)
    with pytest.raises(ValueError, match='inputs changed during'):
        pilot.build(tmp_path, classification_path=classification_path)


def test_literal_replay_rejects_changed_prior_tags_even_with_recomputed_row_hash(scope):
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    changes[0]['corrected_row']['complete_source_review'] = {'changed': True}
    changes[0]['corrected_row_sha256'] = pilot.prior.row_sha(changes[0]['corrected_row'])
    altered = pilot.campaign.canonical(changes[0]['corrected_row']) + b'\n'
    with pytest.raises(ValueError, match='frozen prior tags'):
        pilot.replay(scope['before'], changes, before_sha256=pilot.sha(scope['before']),
                     after_sha256=pilot.sha(altered))


def test_review_windows_identify_the_exact_repeated_occurrence(scope):
    old = json.loads(scope['before'])
    text = 'ἀσαφές πρῶτον · ἄλλο ἀσαφές δεύτερον'
    a = text.rindex('ἀσαφές'); b = a+len('ἀσαφές')
    old['text'] = text
    leaf = {'start': a, 'end': b, 'text': text[a:b], 'classification': 'unresolved-source-reading',
            'qualification': 'The accent is unclear.'}
    old['complete_source_review']['excluded_spans'] = [deepcopy(leaf)]
    old['photius_context_review']['excluded_spans'] = [deepcopy(leaf)]
    scope['before'] = pilot.campaign.canonical(old)+b'\n'
    row = scope['compiled']['rows'][0]; segment = row['segments'][0]
    segment.update(corrected_start=a, corrected_end=b)
    row['segments'] = [{'scan': {'observed_text': text[:a]}, 'verification': 'verified',
                        'text_role': 'authorial-body'}, segment,
                       {'scan': {'observed_text': text[b:]}, 'verification': 'verified',
                        'text_role': 'authorial-body'}]
    scope['classification']['records'][0]['segment_index'] = 1
    scope['decisions'][0]['segment_index'] = 1
    sample, _, _, _ = compile_scope(scope)
    window = sample['records'][0]['display_window']
    assert window['start'] == a
    assert window['before'].endswith('ἄλλο ')
    assert window['after'].startswith(' δεύτερον')
    assert window['target'] == 'ἀσαφές'
    assert sample['records'][0]['scan_window'] == window


@pytest.mark.parametrize('change', [
    {'blind_decision': 'resolved'},
    {'blind_decision': 'retained-uncertain', 'blind_corrected_text': 'changed'},
    {'comparison_result': 'certified-correction'},
    {'comparison_effect': 'imported-without-scan'},
])
def test_comparison_measurements_cannot_invent_review_categories(scope, change):
    scope['decisions'][0].update(change)
    with pytest.raises(ValueError):
        compile_scope(scope)


def test_comparison_measurements_preserve_a_downgraded_blind_reading(scope):
    d = scope['decisions'][0]
    d.update(blind_decision='resolved', blind_corrected_text=d['corrected_text'],
             decision='retained-uncertain', corrected_text=d['original_text'],
             comparison_result='different', comparison_effect='guided-reinspection')
    _, review, _, _ = compile_scope(scope)
    assert review['records'][0]['blind_corrected_text'] == 'ἀσαφής'
    after, _ = pilot.plan(scope['before'], review)
    assert json.loads(after)['text'] == json.loads(scope['before'])['text']


def test_retained_subword_preserves_an_expanded_whole_word_cause(scope):
    old = json.loads(scope['before'])
    segment = scope['compiled']['rows'][0]['segments'][0]
    segment.update(corrected_start=7, corrected_end=8, corrected_text=old['text'][7:8])
    d = scope['decisions'][0]
    d.update(original_text=segment['corrected_text'], corrected_text=segment['corrected_text'],
             decision='retained-uncertain')
    _, review, _, _ = compile_scope(scope)
    after, changes = pilot.plan(scope['before'], review)
    assert json.loads(after)['analysis_text'].split() == old['analysis_text'].split()
    assert changes[0]['remaining_exclusion_causes'] == old['photius_context_review']['excluded_spans']
    assert changes[0]['removed_uncertainty_causes'] == []
    review['records'][0].update(decision='resolved', corrected_text='ά')
    with pytest.raises(ValueError, match='exact inherited'):
        pilot.plan(scope['before'], review)


def test_frozen_experiment_reproduces_after_a_later_served_admission(scope, tmp_path, monkeypatch):
    _, classification_path, write = build_fixture(scope, tmp_path, monkeypatch)
    files, audit = pilot.build(tmp_path, classification_path=classification_path)
    for path, raw in files.items():
        write(path, raw)
    write(pilot.CORPUS, b'a later served corpus with its own admission')
    again, later_audit = pilot.build(tmp_path)
    assert again == files
    assert later_audit == audit
