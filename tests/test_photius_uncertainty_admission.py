"""Served source admission preserves predecessors and exact reversible projections."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import repair_photius_uncertainty_admission as admission


@pytest.fixture
def scope():
    text = 'ἀρχὴ ἄσαφες μένει ἄλλο τέλος'
    locus = 'helladius_chrestomathia_photius_bekker_v2_0170.10'
    masks, decisions = [], []
    old = {'urn': 'photius.bibliotheca', 'locus': locus, 'text': text,
           'analysis_text': 'ἀρχὴ    τέλος'}
    for index, (original, corrected, decision) in enumerate([
            ('ἄσαφες', 'ἀσαφέστατον', 'resolved'), ('μένει', 'μένει', 'resolved'),
            ('ἄλλο', 'ἄλλο', 'retained-uncertain')]):
        start = text.index(original); end = start + len(original)
        qualification = f'The source group at index {index} was uncertain.'
        masks.append({'start': start, 'end': end, 'text': original,
                      'classification': 'unresolved-source-reading', 'qualification': qualification})
        decisions.append({'id': f'P{index+1:03d}', 'locus': locus, 'segment_index': index,
            'start': start, 'end': end, 'original_text': original, 'corrected_text': corrected,
            'decision': decision, 'evidence': 'Direct inspection of the pinned public source crop.',
            'original_segment': {'verification': 'uncertain', 'corrected_text': original,
                                 'uncertainty': qualification},
            'bekker': {'image': {'path': 'data/crop.png', 'sha256': admission.sha(b'crop')}},
            'comparisons': []})
    old.update(complete_source_review={'frozen': 'complete', 'excluded_spans': deepcopy(masks)},
               photius_context_review={'frozen': 'context', 'excluded_spans': deepcopy(masks)},
               photius_uncertainty_review={'frozen': 'prior33', 'excluded_spans': deepcopy(masks)})
    for decision in decisions:
        decision['original_row_sha256'] = admission.prior.row_sha(old)
    before = (json.dumps(old, ensure_ascii=False) + '\n').encode()  # deliberately noncanonical
    observations = {'schema': admission.pilot.SCHEMA, 'admission_authorized': False,
        'input_corpus_sha256': admission.sha(before), 'reviewed_at': '2026-10-21T20:25:23Z',
        'sources': {'bekker': {'path': 'data/scan.pdf', 'sha256': admission.sha(b'scan'), 'kind': 'pdf'}},
        'records': decisions}
    reference = {'audit': {'path': admission.PILOT_AUDIT.as_posix(), 'sha256': 'a'*64},
                 'source_review': {'path': admission.PILOT_REVIEW.as_posix(), 'sha256': 'b'*64}}
    review = admission.compile_review(before, observations, reference,
        admitted_at='2026-10-21T22:00:00Z', bundle_pin={'path': admission.RECIPE_BUNDLE.as_posix(),
            'sha256': admission.sha(b'bundle')}, baseline_remaining_uncertainties=3)
    return {'old': old, 'before': before, 'observations': observations, 'review': review,
            'aliases': b'{"alias":"unchanged"}\n'}


def save(root, files):
    for path, raw in files.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)


def saved(scope, root):
    files, audit = admission.artifacts(scope['before'], scope['aliases'],
                                      admission.encode(scope['review']), recipe_pins={'recipe': 'c'*64})
    save(root, files)
    save(root, {admission.ALIASES: scope['aliases']})
    return files, audit


def test_admits_changed_and_unchanged_resolutions_while_preserving_every_prior_tag(scope, tmp_path):
    files, audit = saved(scope, tmp_path)
    new = json.loads(files[admission.CORPUS])
    assert new['text'] == 'ἀρχὴ ἀσαφέστατον μένει ἄλλο τέλος'
    assert admission.pilot.TAG not in new
    assert new[admission.TAG]['admission_authorized'] is True
    for tag in ('complete_source_review', 'photius_context_review', 'photius_uncertainty_review'):
        assert new[tag] == scope['old'][tag]
    counts = audit['counts']
    assert counts['resolved'] == 2 and counts['resolved_changed'] == 1 and counts['resolved_unchanged'] == 1
    assert counts['retained_uncertain'] == 1 and counts['current_uncertainty_spans'] == 1
    assert counts['baseline_uncertainty_spans'] == 3 and len(counts['resolved_identities']) == 2
    assert admission.restore_before_bytes(files[admission.CORPUS], tmp_path) == scope['before']
    assert admission.restore_before_row(new, tmp_path) == scope['old']
    assert 'ἀσαφέστατον' in ' '.join(admission.lexical_segments(new, tmp_path))
    assert 'ἄλλο' not in ' '.join(admission.lexical_segments(new, tmp_path))
    assert (tmp_path / admission.ALIASES).read_bytes() == scope['aliases']


def test_source_invalidated_undo_and_metadata_need_only_frozen_admission_rows(scope, tmp_path):
    files, audit = saved(scope, tmp_path)
    assert not (tmp_path / 'data/scan.pdf').exists()
    assert not (tmp_path / admission.PILOT_AUDIT).exists()
    assert admission.active_metadata(tmp_path)['counts'] == audit['counts']
    admission.undo(tmp_path)
    assert (tmp_path / admission.CORPUS).read_bytes() == scope['before']
    assert admission.active_metadata(tmp_path) is None
    assert admission.restore_before_bytes(scope['before'], tmp_path) == scope['before']


def test_metadata_does_not_expose_mutable_cached_state(scope, tmp_path):
    _, audit = saved(scope, tmp_path)
    metadata = admission.active_metadata(tmp_path)
    metadata['counts']['resolved_identities'].clear()
    metadata['sources']['bekker']['sha256'] = 'mutated'
    assert admission.active_metadata(tmp_path)['counts'] == audit['counts']
    assert admission.active_metadata(tmp_path)['sources'] == audit['sources']


@pytest.mark.parametrize('path', [admission.BEFORE, admission.BEFORE_ALIASES,
                                admission.REVIEW, admission.RECORDS])
def test_literal_restoration_rejects_every_tampered_archive(scope, tmp_path, path):
    files, _ = saved(scope, tmp_path)
    target = tmp_path / path
    target.write_bytes(target.read_bytes() + b'tamper')
    with pytest.raises(ValueError, match='artifact changed'):
        admission.restore_before_bytes(files[admission.CORPUS], tmp_path)


@pytest.mark.parametrize('defect', ['text', 'mask', 'prior-tag', 'timestamp', 'source-review'])
def test_row_restoration_and_projection_reject_opaque_or_changed_postimages(scope, tmp_path, defect):
    files, _ = saved(scope, tmp_path)
    new = json.loads(files[admission.CORPUS])
    if defect == 'text':
        new['text'] += 'x'
    elif defect == 'mask':
        new[admission.TAG]['excluded_spans'] = []
    elif defect == 'prior-tag':
        new['complete_source_review'] = {}
    elif defect == 'timestamp':
        new[admission.TAG]['admitted_at'] = '2026-10-22T00:00:00Z'
    else:
        new[admission.TAG]['source_review']['sha256'] = 'forged'
    with pytest.raises(ValueError, match='postimage'):
        admission.lexical_segments(new, tmp_path)


def test_independent_fragment_and_nonbody_causes_survive_replacement(scope):
    old = scope['old']; masks = old['photius_uncertainty_review']['excluded_spans']
    masks.extend([{'start': 0, 'end': 3, 'text': old['text'][:3], 'classification': 'printed-fragment'},
        {'start': scope['observations']['records'][0]['start'],
         'end': scope['observations']['records'][0]['end'], 'text': 'ἄσαφες',
         'classification': 'nonbody-source-material'}])
    before = admission.campaign.canonical(old) + b'\n'
    review = deepcopy(scope['review']); review['input_corpus_sha256'] = admission.sha(before)
    review['pilot_metadata']['input_corpus_sha256'] = admission.sha(before)
    for decision in review['records']:
        decision['original_row_sha256'] = admission.prior.row_sha(old)
    after, records, _ = admission.plan(before, admission.encode(review))
    causes = records[0]['remaining_exclusion_causes']
    assert any(c['classification'] == 'printed-fragment' for c in causes)
    assert any(c['classification'] == 'nonbody-source-material' and c['text'] == 'ἀσαφέστατον' for c in causes)
    assert 'ἀσαφέστατον' not in json.loads(after)['analysis_text']


def test_contrary_source_reading_retains_lexical_exclusion(scope):
    scope['review']['records'][0]['comparisons'] = [{'role': 'contrary', 'text': 'another source reading'}]
    after, records, _ = admission.plan(scope['before'], admission.encode(scope['review']))
    assert any(c['classification'] == 'retained-contrary-source-reading' for c in records[0]['remaining_exclusion_causes'])
    assert 'ἀσαφέστατον' not in json.loads(after)['analysis_text']


def test_retained_subword_keeps_the_whole_word_uncertainty(scope):
    old = scope['old']; decision = scope['review']['records'][2]
    decision.update(start=decision['start']+1, end=decision['start']+2,
                    original_text='λ', corrected_text='λ')
    decision['original_segment']['corrected_text'] = 'λ'
    after, records, counts = admission.plan(scope['before'], admission.encode(scope['review']))
    assert counts['retained_uncertain'] == 1
    assert any(c['text'] == 'ἄλλο' and c['classification'] == 'unresolved-source-reading'
               for c in records[0]['remaining_exclusion_causes'])
    assert 'ἄλλο' not in json.loads(after)['analysis_text']
    decision.update(decision='resolved', corrected_text='ρ')
    with pytest.raises(ValueError, match='exact inherited'):
        admission.plan(scope['before'], admission.encode(scope['review']))


@pytest.mark.parametrize('defect', ['duplicate', 'overlap', 'wrong-text', 'held-change'])
def test_plan_rejects_invalid_occurrence_accounting(scope, defect):
    records = scope['review']['records']
    if defect == 'duplicate':
        records.append(deepcopy(records[0]))
    elif defect == 'overlap':
        records[1]['start'] = records[0]['start']
    elif defect == 'wrong-text':
        records[0]['original_text'] = 'other occurrence'
    else:
        records[2]['corrected_text'] = 'a hidden correction'
    with pytest.raises(ValueError):
        admission.plan(scope['before'], admission.encode(scope['review']))


def test_inactive_metadata_rejects_changed_corpus_and_aliases(scope, tmp_path):
    files, _ = saved(scope, tmp_path)
    (tmp_path / admission.CORPUS).write_bytes(scope['before'])
    assert admission.active_metadata(tmp_path) is None
    (tmp_path / admission.ALIASES).write_bytes(b'{}')
    with pytest.raises(ValueError, match='corpus or aliases'):
        admission.active_metadata(tmp_path)
    (tmp_path / admission.ALIASES).write_bytes(scope['aliases'])
    (tmp_path / admission.CORPUS).write_bytes(scope['before'] + b' ')
    with pytest.raises(ValueError, match='corpus or aliases'):
        admission.active_metadata(tmp_path)


def test_missing_audit_cannot_hide_an_active_admission(scope, tmp_path):
    files, _ = saved(scope, tmp_path)
    (tmp_path / admission.AUDIT).unlink()
    for operation in (admission.check, admission.active_metadata):
        with pytest.raises(ValueError, match='no frozen admission audit'):
            operation(tmp_path)
    with pytest.raises(ValueError, match='no frozen admission audit'):
        admission.restore_before_bytes(files[admission.CORPUS], tmp_path)


def build_fixture(scope, root, monkeypatch):
    candidate, changes = admission.pilot.plan(scope['before'], scope['observations'])
    files = {admission.PILOT_REVIEW: admission.encode(scope['observations']),
        admission.pilot.ARCHIVE / 'before-corpus.jsonl.gz': gzip.compress(scope['before'], mtime=0),
        admission.pilot.ARCHIVE / 'candidate-corpus.jsonl.gz': gzip.compress(candidate, mtime=0)}
    pilot_audit = {'before_corpus_sha256': admission.sha(scope['before']),
        'counts': {'baseline_remaining_uncertain_spans': 3},
        'outputs': {path.as_posix(): admission.sha(raw) for path, raw in files.items()}}
    files[admission.PILOT_AUDIT] = admission.encode(pilot_audit)
    save(root, {**files, admission.CORPUS: scope['before'], admission.ALIASES: scope['aliases'],
                admission.RECIPE_BUNDLE: b'bundle', Path('data/scan.pdf'): b'scan'})
    for name in admission.RECIPE_NAMES:
        save(root, {Path('scripts') / name: name.encode()})
    monkeypatch.setattr(admission, 'PILOT_AUDIT_SHA256', admission.sha(files[admission.PILOT_AUDIT]))
    monkeypatch.setattr(admission, 'BASELINE_SHA256', admission.sha(scope['before']))
    monkeypatch.setattr(admission, 'ALIASES_SHA256', admission.sha(scope['aliases']))
    called = []
    def verify_predecessor(path):
        called.append(path)
        if (path / 'data/scan.pdf').read_bytes() != b'scan':
            raise ValueError('Fresh public scan changed')
        if (path / admission.RECIPE_BUNDLE).read_bytes() != b'bundle':
            raise ValueError('Frozen predecessor recipes changed')
    monkeypatch.setattr(admission, '_validate_predecessor', verify_predecessor)
    return files, called


def test_apply_check_and_undo_use_fresh_predecessor_validation_without_writing_aliases(scope, tmp_path, monkeypatch):
    original_pilot, called = build_fixture(scope, tmp_path, monkeypatch)
    audit = admission.apply(tmp_path, admitted_at='2026-10-21T22:00:00Z')
    assert len(called) == 1
    assert admission.check(tmp_path) == audit and len(called) == 2
    assert all((tmp_path / path).read_bytes() == raw for path, raw in original_pilot.items())
    assert (tmp_path / admission.ALIASES).read_bytes() == scope['aliases']
    assert admission.apply(tmp_path) == audit
    with pytest.raises(ValueError, match='timestamp cannot change'):
        admission.build(tmp_path, admitted_at='2026-10-22T00:00:00Z')
    admission.undo(tmp_path)
    assert admission.check(tmp_path) is None


@pytest.mark.parametrize('path', ['data/scan.pdf', admission.RECIPE_BUNDLE])
def test_current_source_or_frozen_recipe_tamper_rejects_check_but_never_blocks_literal_undo(scope, tmp_path, monkeypatch, path):
    build_fixture(scope, tmp_path, monkeypatch)
    admission.apply(tmp_path, admitted_at='2026-10-21T22:00:00Z')
    (tmp_path / path).write_bytes(b'tampered')
    with pytest.raises(ValueError, match='changed'):
        admission.check(tmp_path)
    admission.undo(tmp_path)
    assert (tmp_path / admission.CORPUS).read_bytes() == scope['before']


def test_repeated_original_words_use_declared_offsets_not_first_match(scope):
    old = deepcopy(scope['old'])
    prefix = 'ἄσαφες earlier · '
    old['text'] = prefix + old['text']
    old['photius_uncertainty_review']['excluded_spans'] = [
        {**leaf, 'start': leaf['start']+len(prefix), 'end': leaf['end']+len(prefix)}
        for leaf in old['photius_uncertainty_review']['excluded_spans']]
    before = admission.campaign.canonical(old) + b'\n'
    review = deepcopy(scope['review'])
    review['input_corpus_sha256'] = admission.sha(before)
    review['pilot_metadata']['input_corpus_sha256'] = admission.sha(before)
    for decision in review['records']:
        decision['start'] += len(prefix); decision['end'] += len(prefix)
        decision['original_row_sha256'] = admission.prior.row_sha(old)
    after, _, _ = admission.plan(before, admission.encode(review))
    assert json.loads(after)['text'].startswith(prefix)
    assert 'ἀρχὴ ἀσαφέστατον' in json.loads(after)['text']
