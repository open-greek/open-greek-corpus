"""The historical gate must compare its verified view, not later live bytes."""
import gzip
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_photius_uncertainties as gate


@pytest.fixture
def stage(tmp_path,monkeypatch):
    old=gate.historical
    outputs={old.CORPUS:b'historical-after',old.BEFORE:gzip.compress(b'historical-before'),
             old.AUDIT:b'frozen-audit'}
    for path,raw in outputs.items():
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True)
        (tmp_path/path).write_bytes(raw)
    (tmp_path/old.CORPUS).write_bytes(b'later-live-admission')
    monkeypatch.setattr(old,'build',lambda root:(outputs,{'verified':True}))
    def peel(raw,root):
        if raw!=b'later-live-admission':
            raise ValueError('Later admission changed')
        return b'historical-after'
    monkeypatch.setattr(old,'_later_bytes',peel)
    return tmp_path,old


def test_later_admission_is_checked_at_its_historical_predecessor(stage):
    root,_=stage
    assert gate.check(root)=={'verified':True}


def test_changed_later_corpus_is_rejected(stage):
    root,old=stage
    (root/old.CORPUS).write_bytes(b'tampered')
    with pytest.raises(ValueError,match='Later admission changed'):
        gate.check(root)


def test_original_artifacts_still_need_exact_reproduction(stage):
    root,old=stage
    (root/old.AUDIT).write_bytes(b'tampered')
    with pytest.raises(ValueError,match='source artifacts'):
        gate.check(root)


def test_unapplied_historical_stage_keeps_its_original_semantics(stage,monkeypatch):
    root,old=stage
    monkeypatch.setattr(old,'_later_bytes',lambda raw,root:b'historical-before')
    assert gate.check(root) is None
