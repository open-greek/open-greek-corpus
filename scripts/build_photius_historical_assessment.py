#!/usr/bin/env python3
"""Build the current diagnostic without replacing its frozen predecessor.

Fragment-local similarities remain diagnostic candidates. The later contextual
review, followed by occurrence-scoped source resolutions, owns effective
counterpart associations and lexical exclusions.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

import assess_photius_historical as assess
from audit_compression import compress_gzip
import repair_photius_context as context
import repair_photius_uncertainties as uncertainties

ROOT = Path(__file__).resolve().parents[1]
RECIPE = Path(__file__).resolve()
PREDECESSOR = Path('data/audits/photius-historical-readings.json')
PREDECESSOR_SHA256 = '2ede01c5be9501d968f53acd1a27c45354118c92bdf98f8b933782f3669ecb13'
OUT = Path('data/audits/photius-historical-readings-current.json.gz')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _snapshot(root):
    paths = {assess.CORPUS, assess.LIBRARY, assess.ORIGINAL, assess.COVERAGE,
             PREDECESSOR, Path('data/passage_aliases.json')}
    paths.update(path.relative_to(root) for directory in (context.ARCHIVE, uncertainties.ARCHIVE)
                 for path in (root / directory).rglob('*') if path.is_file())
    scripts = {Path('scripts') / name for name in
               ('build_photius_historical_assessment.py', 'assess_photius_historical.py',
                'audit_compression.py', 'repair_photius_context.py',
                'repair_photius_uncertainties.py')}
    paths.update(scripts)
    return {path.as_posix(): sha((root / path).read_bytes()) for path in sorted(paths)}


def _predecessor(root):
    raw = (root / PREDECESSOR).read_bytes()
    if sha(raw) != PREDECESSOR_SHA256:
        raise ValueError('Frozen predecessor diagnostic changed')
    saved = json.loads(raw)
    before = (root / context.BEFORE).read_bytes()
    audit = json.loads((root / context.AUDIT).read_bytes())
    corpus_pin = saved['input_pins']['current_corpus']
    if (sha(before) != audit['outputs'][context.BEFORE.as_posix()]
            or sha(gzip.decompress(before)) != audit['input_corpus_sha256']
            or corpus_pin != {'path': assess.CORPUS.as_posix(),
                              'sha256': audit['input_corpus_sha256']}
            or saved['input_pins']['current_rows_sha256'] != corpus_pin['sha256']):
        raise ValueError('Frozen predecessor does not identify the exact context baseline')
    loci = [row['locus'] for row in saved['rows']]
    if len(loci) != len(set(loci)) or saved['counts']['rows'] != len(loci):
        raise ValueError('Frozen predecessor diagnostic repeats or omits its scope')
    return ({'path': PREDECESSOR.as_posix(), 'sha256': PREDECESSOR_SHA256,
             'frozen': True, 'current_corpus': deepcopy(corpus_pin),
             'qualification': 'Preserved pre-context fragment-local diagnostic; not current counterpart association authority.'},
            set(loci))


def _authority(root):
    metadata = {'context': context.active_metadata(root),
                'uncertainties': uncertainties.active_metadata(root)}
    if any(value is None for value in metadata.values()):
        raise ValueError('Current diagnostic requires both active later review layers')
    return metadata


def build(root=ROOT):
    root = Path(root)
    before = _snapshot(root)
    predecessor, loci = _predecessor(root)
    authority = _authority(root)
    report = assess.build(root)
    current_loci = [row['locus'] for row in report['rows']]
    if (len(current_loci) != len(set(current_loci)) or set(current_loci) != loci
            or report['counts']['rows'] != len(current_loci)):
        raise ValueError('Current diagnostic differs from the frozen passage scope')
    actual_corpus = before[assess.CORPUS.as_posix()]
    if (report['input_pins']['current_corpus'] !=
            {'path': assess.CORPUS.as_posix(), 'sha256': actual_corpus}
            or report['input_pins']['current_rows_sha256'] != actual_corpus):
        raise ValueError('Current diagnostic does not identify the actual corpus bytes')
    report['predecessor_diagnostic'] = predecessor
    report['current_context_authority'] = {
        **authority,
        'qualification': 'Use these later reviews for effective counterpart associations and lexical exclusions. Fragment-local edges in this diagnostic are comparison candidates only.'}
    report['current_diagnostic_recipe'] = {
        'path': 'scripts/build_photius_historical_assessment.py',
        'sha256': before['scripts/build_photius_historical_assessment.py']}
    if _snapshot(root) != before:
        raise ValueError('Current diagnostic inputs changed during validation')
    return report


def encode(report):
    return compress_gzip(assess.encode(report))


def run(root=ROOT, *, write=False, check=False):
    if write and check:
        raise ValueError('Choose write or check')
    root = Path(root)
    report = build(root)
    expected = encode(report)
    if write:
        (root / OUT).parent.mkdir(parents=True, exist_ok=True)
        (root / OUT).write_bytes(expected)
    elif check and (root / OUT).read_bytes() != expected:
        raise ValueError('Current historical diagnostic does not reproduce')
    return {'output': OUT.as_posix(), 'sha256': sha(expected),
            'compressed_bytes': len(expected), 'counts': report['counts'],
            'predecessor_diagnostic': report['predecessor_diagnostic'],
            'admission_authorized': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true')
    action.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(write=args.write, check=args.check), ensure_ascii=False))


if __name__ == '__main__':
    main()
