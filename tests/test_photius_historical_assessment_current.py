"""The current diagnostic preserves its predecessor and binds live review bytes."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_photius_historical_assessment as current


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    def write(path, raw):
        path = tmp_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    baseline = b'{"text":"before"}\n'
    live = b'{"text":"after"}\n'
    corpus = {'path': current.assess.CORPUS.as_posix(), 'sha256': current.sha(live)}
    locus = 'helladius_chrestomathia_photius_bekker_v2_0003.1'
    old = {'input_pins': {'current_corpus': {**corpus, 'sha256': current.sha(baseline)},
                          'current_rows_sha256': current.sha(baseline)},
           'rows': [{'locus': locus}], 'counts': {'rows': 1}}
    old_raw = current.assess.encode(old)
    compressed = gzip.compress(baseline, mtime=0)
    audit = {'input_corpus_sha256': current.sha(baseline),
             'outputs': {current.context.BEFORE.as_posix(): current.sha(compressed)}}
    files = {current.PREDECESSOR: old_raw, current.assess.CORPUS: live,
             current.assess.LIBRARY: b'digital', current.assess.ORIGINAL: b'original',
             current.assess.COVERAGE: b'coverage',
             Path('data/passage_aliases.json'): b'{}',
             current.context.BEFORE: compressed,
             current.context.AUDIT: current.assess.encode(audit),
             current.uncertainties.AUDIT: b'{}'}
    for name in ('build_photius_historical_assessment.py', 'assess_photius_historical.py',
                 'audit_compression.py', 'repair_photius_context.py',
                 'repair_photius_uncertainties.py', 'repair_photius_uncertainty_admission.py',
                 'check_photius_pilot_predecessor.py', 'repair_photius_editorial_substitutions.py',
                 'prepare_photius_editorial_substitutions.py', 'photius_current_state.py',
                 'repair_photius_editorial_continuation.py', 'prepare_photius_editorial_continuation.py',
                 'photius_remaining_context.py', 'photius_remaining_roles.py', 'photius_remaining_words.py',
                 'repair_photius_final_review.py', 'photius_final_boundary_observations.py',
                 'photius_final_source_observations.py'):
        files[Path('scripts') / name] = name.encode()
    for path, raw in files.items():
        write(path, raw)
    monkeypatch.setattr(current, 'PREDECESSOR_SHA256', current.sha(old_raw))
    report = {'schema_version': 1, 'kind': 'diagnostic-historical-reading-comparison',
              'admission_authorized': False, 'scan_reviewed': False,
              'input_pins': {'current_corpus': corpus,
                             'current_rows_sha256': current.sha(live)},
              'rows': [{'locus': locus, 'current_row': {'text': 'after'}}],
              'counts': {'rows': 1, 'pages': 1}}
    monkeypatch.setattr(current.assess, 'build', lambda root: deepcopy(report))
    monkeypatch.setattr(current.context, 'active_metadata', lambda root: {'audit': 'context'})
    monkeypatch.setattr(current.uncertainties, 'active_metadata', lambda root: {
        'audit': 'uncertainties', 'source_review': {'path': 'old-review', 'sha256': 'a'*64},
        'counts': {'baseline_uncertainty_spans': 3069, 'current_uncertainty_spans': 3047}})
    return tmp_path, report, files, write


def test_write_and_check_reproduce_only_new_gzip_and_keep_predecessor(fixture):
    root, _, files, _ = fixture
    first = current.run(root, write=True)
    raw = (root / current.OUT).read_bytes()
    assert raw[:2] == b'\x1f\x8b' and raw[4:8] == bytes(4)
    assert current.run(root, check=True) == first
    assert current.run(root, write=True) == first
    assert raw == (root / current.OUT).read_bytes()
    assert all((root / path).read_bytes() == before for path, before in files.items())
    report = json.loads(gzip.decompress(raw))
    assert report['predecessor_diagnostic']['frozen'] is True
    assert report['predecessor_diagnostic']['sha256'] == current.PREDECESSOR_SHA256
    assert report['current_context_authority']['context'] == {'audit': 'context'}
    assert report['current_context_authority']['uncertainties']['audit'] == 'uncertainties'
    assert report['current_source_measurement']['current_uncertainty_spans'] == 3047
    assert 'comparison candidates only' in report['current_context_authority']['qualification']
    assert not report['admission_authorized'] and not report['scan_reviewed']
    assert not any(key in report for key in ('generated_at', 'timestamp', 'recorded_at'))


def test_default_summary_has_no_filesystem_side_effect(fixture):
    root, _, files, _ = fixture
    summary = current.run(root)
    assert summary['counts'] == {'rows': 1, 'pages': 1}
    assert not (root / current.OUT).exists()
    assert all((root / path).read_bytes() == raw for path, raw in files.items())


def test_check_detects_tampered_output(fixture):
    root, _, _, _ = fixture
    current.run(root, write=True)
    path = root / current.OUT
    path.write_bytes(path.read_bytes() + b'tampered')
    with pytest.raises(ValueError, match='does not reproduce'):
        current.run(root, check=True)


def test_frozen_predecessor_cannot_be_replaced(fixture):
    root, _, _, _ = fixture
    path = root / current.PREDECESSOR
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError, match='predecessor diagnostic changed'):
        current.build(root)


@pytest.mark.parametrize('defect', ['baseline', 'corpus-pin', 'duplicate', 'count'])
def test_predecessor_scope_and_context_baseline_are_exact(fixture, monkeypatch, defect):
    root, _, _, write = fixture
    old = json.loads((root / current.PREDECESSOR).read_bytes())
    if defect == 'baseline':
        write(current.context.BEFORE, gzip.compress(b'other baseline', mtime=0))
    elif defect == 'corpus-pin':
        old['input_pins']['current_corpus']['sha256'] = 'forged'
    elif defect == 'duplicate':
        old['rows'] *= 2
        old['counts']['rows'] = 2
    else:
        old['counts']['rows'] = 2
    raw = current.assess.encode(old)
    write(current.PREDECESSOR, raw)
    monkeypatch.setattr(current, 'PREDECESSOR_SHA256', current.sha(raw))
    with pytest.raises(ValueError, match='baseline|scope'):
        current.build(root)


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'count', 'corpus-pin'])
def test_current_diagnostic_cannot_lose_scope_or_relabel_live_bytes(fixture, defect):
    root, report, _, _ = fixture
    if defect == 'missing':
        report['rows'] = []
    elif defect == 'duplicate':
        report['rows'] *= 2
        report['counts']['rows'] = 2
    elif defect == 'count':
        report['counts']['rows'] = 2
    else:
        report['input_pins']['current_corpus']['sha256'] = 'forged'
    with pytest.raises(ValueError, match='scope|actual corpus'):
        current.build(root)


@pytest.mark.parametrize('name', ['context', 'uncertainties'])
def test_inactive_review_layer_cannot_claim_current_authority(fixture, monkeypatch, name):
    root, _, _, _ = fixture
    monkeypatch.setattr(getattr(current, name), 'active_metadata', lambda root: None)
    with pytest.raises(ValueError, match='both active'):
        current.build(root)


@pytest.mark.parametrize('path', [current.assess.CORPUS, current.assess.LIBRARY,
    current.context.BEFORE, current.uncertainties.ARCHIVE / 'new-source.png',
    Path('scripts/repair_photius_context.py')])
def test_inputs_are_checked_again_after_the_assessment(fixture, monkeypatch, path):
    root, report, _, write = fixture
    def changed_inputs(_):
        write(path, b'changed during build')
        return deepcopy(report)
    monkeypatch.setattr(current.assess, 'build', changed_inputs)
    with pytest.raises(ValueError, match='inputs changed'):
        current.build(root)


def test_underlying_source_validation_is_not_cached_or_bypassed(fixture, monkeypatch):
    root, _, _, _ = fixture
    def reject(_):
        raise ValueError('frozen digital source changed')
    monkeypatch.setattr(current.assess, 'build', reject)
    with pytest.raises(ValueError, match='frozen digital source'):
        current.build(root)


def test_write_and_check_are_mutually_exclusive(fixture):
    with pytest.raises(ValueError, match='Choose write or check'):
        current.run(fixture[0], write=True, check=True)
