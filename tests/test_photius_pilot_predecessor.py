"""A frozen recipe reruns fresh inputs without accepting live code drift."""
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import check_photius_pilot_predecessor as replay


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    recipe = '''from pathlib import Path
import frozen_dependency
CORPUS=Path('data/current-corpus')
def build(root):
    text=(root/'data/source').read_bytes()
    audit=(root/'data/corpus_changes/photius-bekker-uncertainty-pilot/changes.json').read_bytes()
    return {Path('data/result'):frozen_dependency.project(text),
            Path('data/corpus_changes/photius-bekker-uncertainty-pilot/changes.json'):audit}, {'counts':{'checked':1}}
'''
    dependency = 'def project(raw):\n    return b"original:"+raw\n'
    sources = {name:{'text':text,'sha256':replay.sha(text.encode())} for name,text in (
        ('prepare_photius_uncertainty_pilot.py',recipe),('frozen_dependency.py',dependency))}
    recipes = {'prepare_photius_uncertainty_pilot.py':sources['prepare_photius_uncertainty_pilot.py']['sha256']}
    bundle = gzip.compress(json.dumps({'schema':'photius-frozen-pilot-recipes-v1',
        'recipe_sha256':recipes,'sources':sources}).encode(),mtime=0)
    monkeypatch.setattr(replay,'RECIPES',recipes)
    monkeypatch.setattr(replay,'EXPECTED_BUNDLE_SHA256',replay.sha(bundle))
    table = b'# exact original observations\n'
    audit = {'recipe_sha256':recipes,'outputs':{(replay.PILOT/'source-table.py').as_posix():replay.sha(table)}}
    files = {replay.BUNDLE:bundle,replay.PILOT/'changes.json':json.dumps(audit).encode(),
        Path('scripts/photius_uncertainty_pilot_observations.py'):table,
        Path('scripts/frozen_dependency.py'):b'raise Exception("live helper must not execute")',
        Path('scripts/prepare_photius_uncertainty_pilot.py'):b'raise Exception("live compiler must not execute")',
        Path('data/source'):b'source',Path('data/result'):b'original:source'}
    for path,raw in files.items():
        path=tmp_path/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return tmp_path,files,audit


def test_independent_original_recipe_executes_and_all_inputs_remain_unchanged(fixture):
    root,files,audit=fixture
    assert replay.check(root)==audit
    assert replay.check(root)==audit
    assert all((root/path).read_bytes()==raw for path,raw in files.items())


@pytest.mark.parametrize('target',[Path('data/source'),Path('data/result'),
    Path('scripts/photius_uncertainty_pilot_observations.py'),replay.BUNDLE,replay.PILOT/'changes.json'])
def test_changed_inputs_or_outputs_fail_after_successful_fresh_replay(fixture,target):
    root,_,_=fixture
    replay.check(root)
    path=root/target;path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises((ValueError,json.JSONDecodeError),match='changed|failed|Extra data'):
        replay.check(root)


def test_context_replay_skips_only_current_corpus_and_still_checks_aliases(fixture,monkeypatch):
    root,_,_=fixture
    def execute(root,doc,*,module,skip_corpus=False):
        assert module=='repair_photius_context' and skip_corpus
        assert (root/'data/current-corpus').read_bytes()==b'new admission corpus'
        if (root/'data/aliases').read_bytes()!=b'exact aliases':
            raise ValueError('alias output changed')
    monkeypatch.setattr(replay,'_execute',execute)
    monkeypatch.setattr(replay,'CONTEXT_RECIPES',{})
    for path,raw in [('data/current-corpus',b'new admission corpus'),('data/aliases',b'exact aliases'),
                     ('data/corpus_changes/photius-bekker-context/changes.json',b'{"recipe_sha256":{}}')]:
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    replay.check_context_sources(root)
    (root/'data/aliases').write_bytes(b'changed aliases')
    with pytest.raises(ValueError,match='alias output'):
        replay.check_context_sources(root)


def test_published_recipe_capture_is_exact_and_covers_transitive_helpers():
    raw=(ROOT/replay.BUNDLE).read_bytes()
    doc=replay.load_bundle(raw)
    assert {'prepare_photius_historical_readings.py','repair_photius_context.py',
            'repair_photius_complete_review.py'}<=set(doc['sources'])
    assert {name:doc['sources'][name]['sha256'] for name in replay.RECIPES}==replay.RECIPES
