#!/usr/bin/env python3
"""Recheck the frozen pilot with its original code and fresh source inputs.

The original experiment pins recipe bytes in its output. Later admission hooks
must not rewrite that experiment or claim those old hashes for changed code.
This adapter executes the archived recipe and its local import closure in an
isolated directory, then compares every freshly generated output byte.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from audit_compression import compress_gzip

ROOT = Path(__file__).resolve().parents[1]
BASE = '7fd6ef06'
BUNDLE = Path('data/corpus_changes/photius-bekker-uncertainty-admission/frozen-pilot-recipes.json.gz')
PILOT = Path('data/corpus_changes/photius-bekker-uncertainty-pilot')
EXPECTED_BUNDLE_SHA256 = 'ca5bc6866d44b33fd0766de828c84903b50d6794206a2f4b0d4d12030d6981e6'
RECIPES = {
    'assess_photius_historical.py': 'afd191d3c022f57e859bfa79d329e83db5237ad55db3906624e8eba088b67463',
    'audit_compression.py': 'd2504998f18d7d69fb009312eede80ffc83667e07e5450134eceb2361d101d21',
    'compare_photius_local_edition.py': '731878fda72dcab04d167ffb9ed8f453e129f62e315ce556e79155fc52ca92bf',
    'prepare_photius_review_campaign.py': '4ef586e6bb30bcb07a7e0222b851bb3b13c8cc7f6b99301f5c0698f7e5b6e516',
    'prepare_photius_uncertainty_pilot.py': '55f59e5e2ccd3125e435804fbcbecfc55c50c584b491125ba611f527438c8ed4',
    'repair_photius_uncertainties.py': 'e607f6df69a5c3a215916bb9038f0bd6a1c1f741b8e60ae277671d9fb7ef92c1',
}
CONTEXT_RECIPES = {**{name: RECIPES[name] for name in (
    'assess_photius_historical.py', 'prepare_photius_review_campaign.py', 'audit_compression.py')},
    'repair_photius_context.py': 'f19d398ea9976b954d8db57e8f31200776e3a23f175c4ff247b187a909f3af86',
    'repair_photius_complete_review.py': 'c48e2b98409eeea0f55edf123152f27aab4e0ee19dfd7dc2cfdd51fbc8c55b17'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def capture(root=ROOT):
    """Reproduce the immutable bundle from the published predecessor commit."""
    root = Path(root)
    def git(*args):
        return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True).stdout
    commit = git('rev-parse', BASE).decode().strip()
    available = {Path(p).name for p in git('ls-tree', '-r', '--name-only', BASE, 'scripts').decode().splitlines()
                 if p.endswith('.py') and len(Path(p).parts) == 2}
    sources, pending = {}, list(RECIPES)
    while pending:
        name = pending.pop()
        if name in sources:
            continue
        raw = git('show', f'{BASE}:scripts/{name}')
        sources[name] = {'sha256': sha(raw), 'text': raw.decode()}
        for node in ast.walk(ast.parse(raw)):
            names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                     else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            for module in names:
                dependency = module.split('.')[0] + '.py'
                if dependency in available and dependency not in sources:
                    pending.append(dependency)
    if any(sources[name]['sha256'] != digest for name, digest in RECIPES.items()):
        raise ValueError('Published predecessor differs from the frozen pilot recipes')
    doc = {'schema': 'photius-frozen-pilot-recipes-v1', 'commit': commit,
           'recipe_sha256': RECIPES, 'sources': sources}
    return compress_gzip((json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode())


def load_bundle(raw):
    if sha(raw) != EXPECTED_BUNDLE_SHA256:
        raise ValueError('Frozen pilot recipe bundle changed')
    doc = json.loads(gzip.decompress(raw))
    if doc.get('schema') != 'photius-frozen-pilot-recipes-v1' or doc.get('recipe_sha256') != RECIPES:
        raise ValueError('Frozen pilot recipe identity changed')
    for name, value in doc['sources'].items():
        if Path(name).name != name or not name.endswith('.py') or sha(value['text'].encode()) != value['sha256']:
            raise ValueError('Frozen pilot import source changed')
    if any(doc['sources'].get(n, {}).get('sha256') != digest for n, digest in RECIPES.items()):
        raise ValueError('Frozen pilot recipe closure is incomplete')
    return doc


def _execute(root, doc, *, module, skip_corpus=False):
    table = root/'scripts/photius_uncertainty_pilot_observations.py'
    table_raw = table.read_bytes()
    with tempfile.TemporaryDirectory(prefix='photius-pilot-replay-') as directory:
        view = Path(directory); scripts = view/'scripts'; scripts.mkdir()
        for name, value in doc['sources'].items():
            (scripts/name).write_text(value['text'])
        (scripts/table.name).write_bytes(table_raw)
        (view/'data').symlink_to(root/'data', target_is_directory=True)
        # Every local Python dependency is archived. Do not fall back to live
        # scripts whose later hooks could silently substitute changed behavior.
        command = """import importlib,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1])/'scripts'))
builder=importlib.import_module(sys.argv[2])
root=Path(sys.argv[1])
files,audit=builder.build(root)
if any((root/path).read_bytes()!=raw for path,raw in files.items()
       if not (sys.argv[3]=='skip-corpus' and path==builder.CORPUS)):
    raise ValueError('Frozen predecessor outputs do not reproduce with their original recipes')
print(json.dumps(audit['counts'],sort_keys=True))
"""
        result = subprocess.run([sys.executable, '-I', '-c', command, str(view), module,
                                 'skip-corpus' if skip_corpus else 'all-outputs'],
                                cwd=view, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('Frozen predecessor source replay failed: '+result.stderr.strip())


def check(root=ROOT):
    """Run the original full source check; return the unchanged pilot audit."""
    root = Path(root).resolve()
    bundle_raw = (root/BUNDLE).read_bytes()
    doc = load_bundle(bundle_raw)
    audit_raw = (root/PILOT/'changes.json').read_bytes()
    audit = json.loads(audit_raw)
    table = root/'scripts/photius_uncertainty_pilot_observations.py'
    table_raw = table.read_bytes()
    if (audit.get('recipe_sha256') != RECIPES or
            sha(table_raw) != audit['outputs'][(PILOT/'source-table.py').as_posix()]):
        raise ValueError('Frozen pilot audit or current source table changed')
    _execute(root, doc, module='prepare_photius_uncertainty_pilot')
    if ((root/BUNDLE).read_bytes() != bundle_raw or (root/PILOT/'changes.json').read_bytes() != audit_raw
            or table.read_bytes() != table_raw):
        raise ValueError('Pilot predecessor inputs changed during validation')
    return audit


def check_context_sources(root=ROOT):
    """Reproduce old context artifacts; the caller checks current corpus/aliases."""
    root = Path(root).resolve()
    bundle_raw = (root/BUNDLE).read_bytes(); doc = load_bundle(bundle_raw)
    audit_path = root/'data/corpus_changes/photius-bekker-context/changes.json'
    audit_raw = audit_path.read_bytes(); audit = json.loads(audit_raw)
    if (audit.get('recipe_sha256') != CONTEXT_RECIPES or
            any(doc['sources'].get(n, {}).get('sha256') != digest
                for n, digest in CONTEXT_RECIPES.items())):
        raise ValueError('Frozen context recipes do not match the predecessor bundle')
    _execute(root, doc, module='repair_photius_context', skip_corpus=True)
    if (root/BUNDLE).read_bytes() != bundle_raw or audit_path.read_bytes() != audit_raw:
        raise ValueError('Context predecessor inputs changed during validation')
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check', action='store_true')
    action.add_argument('--write-recipe-bundle', action='store_true')
    args = parser.parse_args()
    if args.write_recipe_bundle:
        raw = capture()
        load_bundle(raw)
        path = ROOT/BUNDLE
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('Refusing to replace a frozen pilot recipe bundle')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        print(json.dumps({'path': BUNDLE.as_posix(), 'sha256': sha(raw)}))
    else:
        print(json.dumps(check()['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
