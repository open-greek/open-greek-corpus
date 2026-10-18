"""A matching text hash must not hide changed public quality or catalog metadata."""
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_corpus_release as release
import build_source_components as components


@pytest.fixture
def record(tmp_path, monkeypatch):
    data = tmp_path / 'data'
    corpus = data / 'corpus'
    corpus.mkdir(parents=True)
    source = corpus / 'test.work.jsonl'
    source.write_text('{"text":"λόγος ἀληθής","source":"ocr","edition":"test","license":"PD"}\n')
    (data / components.NAME).write_bytes(components.encode(components.build(data)))
    catalog = data / 'corpus_catalog.tsv'
    row = {'slug':'test.work','source':'ocr','license':'PD','correction':'raw-ocr',
           'tokens':'2','passages':'1','tokens_lemmatized':'2',
           'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    with catalog.open('w', newline='') as sink:
        writer = csv.DictWriter(sink, fieldnames=list(row), delimiter='\t')
        writer.writeheader()
        writer.writerow(row)
    citation = tmp_path / 'CITATION.cff'
    citation.write_text('version: corpus-2026-10-18.1\ndate-released: "2026-10-18"\n')
    output = data / 'corpus_release.json'
    monkeypatch.setattr(release, 'REPO', tmp_path)
    monkeypatch.setattr(release, 'DATA', data)
    monkeypatch.setattr(release, 'CATALOG', catalog)
    monkeypatch.setattr(release, 'CITATION', citation)
    monkeypatch.setattr(release, 'OUT', output)
    monkeypatch.setattr(release, 'git', lambda *args: 'metadata-commit' if args[0]=='rev-parse'
                        else '2026-10-19' if args[0]=='show' else '')
    # Private correction stores and expensive source-validation fixtures have
    # their own tests; this exercises the real public catalog/release builder.
    monkeypatch.setattr(release, 'corrections_block', lambda *args: {'wrong_rows_estimate':7})
    monkeypatch.setattr(release, 'polytonic_quality', lambda **kwargs: {
        'report_sha256':'a'*64,'counts':{'flagged':1},'selection_rule':None})
    value = release.build([row], catalog, 'corpus-2026-10-18.1', '2026-10-18',
                          'corpus-commit', '2026-10-18', 0)
    output.write_text(json.dumps(value))
    return {'output':output,'citation':citation,'value':value}


def invoke(monkeypatch, *args):
    monkeypatch.setattr(sys, 'argv', ['build_corpus_release.py', *args])
    release.main()


def test_check_preserves_citation_suffix_across_metadata_commits(record, monkeypatch):
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check')
    assert outcome.value.code == 0
    assert json.loads(record['output'].read_text()) == record['value']


def test_explicit_suffixed_release_identity_passes(record, monkeypatch):
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check', '--release-id', 'corpus-2026-10-18.1', '--date', '2026-10-18')
    assert outcome.value.code == 0


def test_missing_release_is_blocking_before_build(record, monkeypatch, capsys):
    record['output'].unlink()
    monkeypatch.setattr(release, 'build', lambda *args: pytest.fail('Missing record must fail before building'))
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check')
    assert outcome.value.code == 1
    assert 'Missing release record' in capsys.readouterr().err


@pytest.mark.parametrize('path,value', [
    (('pin','catalog_sha256'),'0'*64),
    (('pin','catalog_rows'),99),
    (('corpus','tokens_lemmatized'),0),
    (('sources','ocr','tokens'),100),
    (('licenses','PD','works'),8),
    (('quality','raw_ocr','legacy_homogeneous_work_bucket','raw_share_of_corpus_tokens'),0),
    (('quality','raw_ocr','ocr_tokens'),99),
    (('quality','raw_ocr','global_raw_token_bounds'),[0,2]),
    (('quality','source_components','sha256'),'0'*64),
    (('quality','wrong_corrections','wrong_rows_estimate'),0),
    (('quality','polytonic_loss','counts','flagged'),0),
    (('quality','polytonic_loss','report_sha256'),'0'*64),
    (('quality','polytonic_loss','selection_rule'),'prefer model 3.8'),
    (('release_id',),'corpus-2026-10-18'),
    (('release_date',),'2026-10-17'),
    (('title',),'Different corpus'),
    (('generated_from','note'),'different claim'),
    (('generated_from','uncommitted_corpus_files'),1),
])
def test_all_stable_release_fields_are_checked(record, monkeypatch, capsys, path, value):
    edited = deepcopy(record['value'])
    target = edited
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    record['output'].write_text(json.dumps(edited))
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check')
    assert outcome.value.code == 1
    assert '.'.join(path) in capsys.readouterr().err


def test_changed_current_public_quality_is_blocking_even_for_identical_text(record, monkeypatch, capsys):
    monkeypatch.setattr(release, 'polytonic_quality', lambda **kwargs: {
        'report_sha256':'b'*64,'counts':{'flagged':3},'selection_rule':None})
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check')
    assert outcome.value.code == 1
    error = capsys.readouterr().err
    assert 'quality.polytonic_loss.counts.flagged' in error
    assert 'quality.polytonic_loss.report_sha256' in error
    assert 'pin.corpus_sha256' not in error


def test_explicit_identity_cannot_bypass_citation_declaration(record, monkeypatch, capsys):
    # Even if a caller passes the wrong suffix and edits the stored identity to
    # match, the declared citation version remains independently binding.
    value = record['value']
    value['release_id'] = 'corpus-2026-10-18'
    record['output'].write_text(json.dumps(value))
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check', '--release-id', 'corpus-2026-10-18', '--date', '2026-10-18')
    assert outcome.value.code == 1
    assert 'CITATION.cff version' in capsys.readouterr().err


def test_missing_citation_can_use_stored_identity_only_without_explicit_options(record, monkeypatch):
    record['citation'].unlink()
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check')
    assert outcome.value.code == 0
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check', '--release-id', 'corpus-2026-10-18.1')
    assert outcome.value.code == 1


def test_creation_default_remains_unsuffixed_without_explicit_release_id(record, monkeypatch):
    invoke(monkeypatch, '--date', '2026-10-18')
    assert json.loads(record['output'].read_text())['release_id'] == 'corpus-2026-10-18'


def test_print_cannot_bypass_verification(record, monkeypatch):
    with pytest.raises(SystemExit) as outcome:
        invoke(monkeypatch, '--check', '--print')
    assert outcome.value.code == 2


def test_boolean_cannot_replace_a_measured_number():
    assert release.release_differences({'quality':{'counts':[1]}}, {'quality':{'counts':[True]}}) == ['quality.counts[0] changed']
