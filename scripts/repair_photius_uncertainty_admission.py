#!/usr/bin/env python3
"""Admit the checked 100-span source review above all frozen Photius layers.

The experimental archive remains unchanged. Source resolutions remove only
their exact uncertainty causes; fragments, nonbody text, and independent
disagreements retain their exclusions. Literal preimages support reversal even
when a correction source is later removed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path

from audit_compression import compress_gzip
import prepare_photius_review_campaign as campaign
import prepare_photius_uncertainty_pilot as pilot
import repair_photius_uncertainties as prior

ROOT = Path(__file__).resolve().parents[1]
CORPUS = campaign.CORPUS
ALIASES = Path('data/passage_aliases.json')
ARCHIVE = Path('data/corpus_changes/photius-bekker-uncertainty-admission')
AUDIT = ARCHIVE / 'changes.json'
BEFORE = ARCHIVE / 'before-corpus.jsonl.gz'
BEFORE_ALIASES = ARCHIVE / 'before-aliases.json.gz'
REVIEW = ARCHIVE / 'source-review.json'
RECORDS = ARCHIVE / 'records.jsonl.gz'
RECIPE_BUNDLE = ARCHIVE / 'frozen-pilot-recipes.json.gz'
PILOT_AUDIT = pilot.ARCHIVE / 'changes.json'
PILOT_REVIEW = pilot.ARCHIVE / 'source-review.json'
PILOT_AUDIT_SHA256 = '1ee50d4946acc0273342b2fc13e9ae12302d9f7f3eb7dc73b2e1686b3401b723'
BASELINE_SHA256 = 'd4193edddda4ba27e673dcaabdae26c4711399d3c514be505a2850c6d3ccbe2b'
ALIASES_SHA256 = '691bc8a6d9199cb59b68f888f724a3afb3390932c00bf6501e5057eacea9c5fd'
TAG = 'photius_uncertainty_admission'
SCHEMA = 'photius-source-uncertainty-admission-v1'
RECIPE_NAMES = ('repair_photius_uncertainty_admission.py',
    'check_photius_pilot_predecessor.py', 'prepare_photius_uncertainty_pilot.py',
    'prepare_photius_review_campaign.py', 'repair_photius_uncertainties.py',
    'audit_compression.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def _validate_predecessor(root):
    # This adapter rebuilds the complete frozen experiment in its checked
    # original recipe view, including fresh scan rendering and every output.
    from check_photius_pilot_predecessor import check
    check(root)


def _read_pilot(root):
    raw = (root / PILOT_AUDIT).read_bytes()
    if sha(raw) != PILOT_AUDIT_SHA256:
        raise ValueError('Frozen pilot admission predecessor changed')
    audit = json.loads(raw)
    outputs = {path: (root / prior._path(path)).read_bytes() for path in audit['outputs']}
    if any(sha(outputs[path]) != digest for path, digest in audit['outputs'].items()):
        raise ValueError('A frozen pilot source, observation, or candidate changed')
    before = gzip.decompress(outputs[(pilot.ARCHIVE / 'before-corpus.jsonl.gz').as_posix()])
    if sha(before) != BASELINE_SHA256 or audit['before_corpus_sha256'] != BASELINE_SHA256:
        raise ValueError('Pilot admission requires its exact served baseline')
    review_raw = outputs[PILOT_REVIEW.as_posix()]
    review = json.loads(review_raw)
    if review.get('admission_authorized') is not False or review.get('input_corpus_sha256') != sha(before):
        raise ValueError('Pilot observations lost their frozen experimental identity')
    return before, review, audit, {'audit': {'path': PILOT_AUDIT.as_posix(), 'sha256': sha(raw)},
        'source_review': {'path': PILOT_REVIEW.as_posix(), 'sha256': sha(review_raw)}}


def compile_review(before, observations, pilot_reference, *, admitted_at, bundle_pin,
                   baseline_remaining_uncertainties):
    """Promote checked source observations without changing the experiment."""
    campaign._timestamp(admitted_at)
    if observations.get('schema') != pilot.SCHEMA or observations.get('admission_authorized') is not False:
        raise ValueError('Admission requires the checked nonadmitting pilot observations')
    if observations['input_corpus_sha256'] != sha(before):
        raise ValueError('Source observations differ from the exact admission preimage')
    if type(baseline_remaining_uncertainties) is not int or baseline_remaining_uncertainties < 0:
        raise ValueError('The admission baseline needs an exact uncertainty count')
    return {'schema': SCHEMA, 'work': 'photius.bibliotheca', 'admission_authorized': True,
        'admitted_at': admitted_at, 'reviewed_at': observations['reviewed_at'],
        'input_corpus_sha256': sha(before), 'pilot': deepcopy(pilot_reference),
        'predecessor_recipe_bundle': deepcopy(bundle_pin),
        'baseline_uncertainty_spans': baseline_remaining_uncertainties,
        'pilot_metadata': {key: deepcopy(value) for key, value in observations.items() if key != 'records'},
        'records': deepcopy(observations['records']),
        'qualification': 'Served occurrence-scoped source admission. The experimental archive and all prior review authorities remain unchanged; unrelated exclusions remain effective.'}


def plan(before, review_raw):
    review = json.loads(review_raw)
    if (review.get('schema') != SCHEMA or review.get('work') != 'photius.bibliotheca'
            or review.get('admission_authorized') is not True or review['input_corpus_sha256'] != sha(before)):
        raise ValueError('Uncertainty admission differs from its exact source authority')
    campaign._timestamp(review['admitted_at'])
    observations = {**deepcopy(review['pilot_metadata']), 'records': deepcopy(review['records'])}
    if observations.get('reviewed_at') != review['reviewed_at']:
        raise ValueError('Admission changed the original source-review timestamp')
    candidate, changes = pilot.plan(before, observations)
    reference = {'path': REVIEW.as_posix(), 'sha256': sha(review_raw)}
    by_locus = {}
    for change in changes:
        old, new = change['original_row'], deepcopy(change['corrected_row'])
        if old.get(TAG) or old.get(pilot.TAG):
            raise ValueError('Admission cannot be applied twice or to experimental rows')
        experimental = new.pop(pilot.TAG)
        decisions = change['decisions']
        new[TAG] = {'schema': SCHEMA, 'admission_authorized': True,
            'source_review': reference, 'original_row_sha256': prior.row_sha(old),
            'admitted_at': review['admitted_at'],
            'excluded_spans': deepcopy(experimental['excluded_spans']),
            'decisions': len(decisions), 'resolved': sum(d['decision'] == 'resolved' for d in decisions),
            'retained_uncertain': sum(d['decision'] == 'retained-uncertain' for d in decisions),
            'qualification': 'Checked later source resolutions. Prior tags remain frozen, and all independent lexical exclusion causes survive.'}
        change = deepcopy(change)
        change.update(corrected_row=new, corrected_row_sha256=prior.row_sha(new),
                      admitted_at=review['admitted_at'])
        by_locus[change['locus']] = change
    output = []
    for line in before.splitlines(keepends=True):
        row = json.loads(line)
        change = by_locus.get(row['locus'])
        output.append(campaign.canonical(change['corrected_row']) + b'\n' if change else line)
    records = [by_locus[change['locus']] for change in changes]
    resolved = [{'locus': d['locus'], 'segment_index': d['segment_index']}
                for d in review['records'] if d['decision'] == 'resolved']
    remaining = review['baseline_uncertainty_spans'] - len(resolved)
    if remaining < 0:
        raise ValueError('Admission resolves more source spans than its exact baseline')
    counts = {'rows': len(records), 'decisions': len(review['records']), 'resolved': len(resolved),
        'resolved_changed': sum(d['decision'] == 'resolved' and d['corrected_text'] != d['original_text'] for d in review['records']),
        'resolved_unchanged': sum(d['decision'] == 'resolved' and d['corrected_text'] == d['original_text'] for d in review['records']),
        'retained_uncertain': sum(d['decision'] == 'retained-uncertain' for d in review['records']),
        'changed_display_rows': sum(c['original_row']['text'] != c['corrected_row']['text'] for c in records),
        'baseline_uncertainty_spans': review['baseline_uncertainty_spans'],
        'current_uncertainty_spans': remaining, 'resolved_identities': resolved,
        'primary_rows_before': len(before.splitlines()), 'primary_rows_after': len(output)}
    return b''.join(output), records, counts


def artifacts(before, aliases, review_raw, *, recipe_pins):
    review = json.loads(review_raw)
    after, changes, counts = plan(before, review_raw)
    files = {BEFORE: compress_gzip(before), BEFORE_ALIASES: compress_gzip(aliases),
             REVIEW: review_raw, RECORDS: compress_gzip(b''.join(campaign.canonical(change) + b'\n' for change in changes))}
    audit = {'schema': SCHEMA, 'work': 'photius.bibliotheca', 'admission_authorized': True,
        'admitted_at': review['admitted_at'], 'reviewed_at': review['reviewed_at'],
        'input_corpus_sha256': sha(before), 'output_corpus_sha256': sha(after),
        'aliases_sha256': sha(aliases), 'pilot': deepcopy(review['pilot']),
        'predecessor_recipe_bundle': deepcopy(review['predecessor_recipe_bundle']),
        'source_review': {'path': REVIEW.as_posix(), 'sha256': sha(review_raw)},
        'sources': deepcopy(review['pilot_metadata']['sources']),
        'recipe_sha256': deepcopy(recipe_pins), 'counts': counts,
        'outputs': {path.as_posix(): sha(raw) for path, raw in files.items()}}
    audit['outputs'][CORPUS.as_posix()] = sha(after)
    return {CORPUS: after, **files, AUDIT: encode(audit)}, audit


def build(root=ROOT, *, admitted_at=None):
    root = Path(root)
    recipes = {name: sha((root / 'scripts' / name).read_bytes()) for name in RECIPE_NAMES}
    _validate_predecessor(root)
    before, observations, pilot_audit, reference = _read_pilot(root)
    bundle_raw = (root / RECIPE_BUNDLE).read_bytes()
    bundle_pin = {'path': RECIPE_BUNDLE.as_posix(), 'sha256': sha(bundle_raw)}
    aliases = (root / ALIASES).read_bytes()
    if sha(aliases) != ALIASES_SHA256:
        raise ValueError('Admission requires the exact unchanged predecessor aliases')
    if (root / AUDIT).exists():
        previous = json.loads((root / AUDIT).read_bytes())
        if admitted_at is not None and admitted_at != previous['admitted_at']:
            raise ValueError('The immutable admission timestamp cannot change')
        admitted_at = previous['admitted_at']
    if admitted_at is None:
        raise ValueError('The first admission build requires an explicit admitted_at UTC timestamp')
    review = compile_review(before, observations, reference, admitted_at=admitted_at,
        bundle_pin=bundle_pin,
        baseline_remaining_uncertainties=pilot_audit['counts']['baseline_remaining_uncertain_spans'])
    files, audit = artifacts(before, aliases, encode(review), recipe_pins=recipes)
    source_pins = {name: digest for name, digest in observations.get('input_pins', {}).items()
                   if name != CORPUS.as_posix()}
    source_pins.update({value['path']: value['sha256'] for value in observations['sources'].values()})
    if (sha((root / PILOT_AUDIT).read_bytes()) != reference['audit']['sha256']
            or sha((root / PILOT_REVIEW).read_bytes()) != reference['source_review']['sha256']
            or (root / RECIPE_BUNDLE).read_bytes() != bundle_raw
            or (root / ALIASES).read_bytes() != aliases
            or any(sha((root / prior._path(name)).read_bytes()) != digest for name, digest in source_pins.items())
            or any(sha((root / prior._path(name)).read_bytes()) != digest for name, digest in pilot_audit['outputs'].items())
            or any(sha((root / 'scripts' / name).read_bytes()) != digest for name, digest in recipes.items())):
        raise ValueError('Admission inputs changed during validation')
    return files, audit


@lru_cache(maxsize=1)
def _literal_saved(audit_raw, before_raw, alias_raw, review_raw, records_raw):
    audit = json.loads(audit_raw)
    for path, raw in ((BEFORE, before_raw), (BEFORE_ALIASES, alias_raw), (REVIEW, review_raw), (RECORDS, records_raw)):
        if sha(raw) != audit['outputs'][path.as_posix()]:
            raise ValueError('Frozen uncertainty admission artifact changed')
    review = json.loads(review_raw)
    before, aliases = gzip.decompress(before_raw), gzip.decompress(alias_raw)
    after, records, counts = plan(before, review_raw)
    saved_records = [json.loads(line) for line in gzip.decompress(records_raw).splitlines()]
    if (audit.get('schema') != SCHEMA or audit.get('work') != 'photius.bibliotheca'
            or audit.get('admission_authorized') is not True
            or sha(before) != audit['input_corpus_sha256'] or sha(after) != audit['output_corpus_sha256']
            or sha(aliases) != audit['aliases_sha256'] or records != saved_records or counts != audit['counts']
            or audit['source_review'] != {'path': REVIEW.as_posix(), 'sha256': sha(review_raw)}
            or audit['outputs'][CORPUS.as_posix()] != sha(after)
            or any(audit[key] != review[key] for key in ('admitted_at', 'reviewed_at', 'pilot', 'predecessor_recipe_bundle'))
            or audit['sources'] != review['pilot_metadata']['sources']):
        raise ValueError('Frozen admission replay differs from its exact authority or postimage')
    return before, after, aliases, audit, {record['locus']: record for record in records}


def _saved(root):
    values = _literal_saved(*((Path(root) / path).read_bytes()
        for path in (AUDIT, BEFORE, BEFORE_ALIASES, REVIEW, RECORDS)))
    return (*values[:3], deepcopy(values[3]), values[4])


@lru_cache(maxsize=2)
def _record_map(raw):
    records = [json.loads(line) for line in gzip.decompress(raw).splitlines()]
    mapping = {record['locus']: record for record in records}
    if len(mapping) != len(records):
        raise ValueError('Uncertainty admission archive repeats a passage')
    return mapping


def _later_bytes(raw, root):
    if b'"photius_editorial_substitution"' in raw:
        from repair_photius_editorial_substitutions import restore_before_bytes as restore
        return restore(raw, root)
    return raw


def _later_row(row, root):
    if row.get('photius_editorial_substitution'):
        from repair_photius_editorial_substitutions import restore_before_row as restore
        return restore(row, root)
    return row


def restore_before_bytes(raw, root=ROOT):
    raw = _later_bytes(raw, root)
    root = Path(root)
    if not (root / AUDIT).exists():
        if b'"' + TAG.encode() + b'"' in raw:
            raise ValueError('Admitted source metadata has no frozen admission audit')
        return raw
    before, after, _, _, _ = _saved(root)
    if raw == before:
        return before
    if raw != after:
        raise ValueError('Admitted corpus differs from its exact postimage')
    return before


def restore_before_row(row, root=ROOT):
    row = _later_row(row, root)
    if not row.get(TAG):
        return deepcopy(row)
    root = Path(root)
    audit_raw, review_raw, records_raw = ((root / path).read_bytes() for path in (AUDIT, REVIEW, RECORDS))
    audit = json.loads(audit_raw)
    if (sha(review_raw) != audit['source_review']['sha256']
            or sha(records_raw) != audit['outputs'][RECORDS.as_posix()]):
        raise ValueError('Admitted row authority changed')
    change = _record_map(records_raw).get(row.get('locus'))
    if (not change or row != change['corrected_row'] or prior.row_sha(row) != change['corrected_row_sha256']
            or prior.row_sha(change['original_row']) != change['original_row_sha256']
            or json.loads(change['original_line']) != change['original_row']
            or row[TAG].get('schema') != SCHEMA or row[TAG].get('admission_authorized') is not True
            or row[TAG]['source_review'] != audit['source_review']
            or row[TAG]['original_row_sha256'] != change['original_row_sha256']
            or row[TAG]['admitted_at'] != audit['admitted_at']):
        raise ValueError('Admitted row differs from its exact source postimage')
    return deepcopy(change['original_row'])


def lexical_segments(row, root=ROOT):
    row = _later_row(row, root)
    if not row.get(TAG):
        raise ValueError('Admitted lexical projection has no source authority')
    restore_before_row(row, root)
    _, runs = prior._projection(row['text'], prior._flatten(row['text'], row[TAG]['excluded_spans']))
    if row.get('analysis_text') != ' '.join(runs):
        raise ValueError('Admitted lexical projection changed')
    return runs


def check(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        if b'"' + TAG.encode() + b'"' in (root / CORPUS).read_bytes():
            raise ValueError('Admitted source metadata has no frozen admission audit')
        return None
    outputs, audit = build(root)
    before, after, aliases, _, _ = _saved(root)
    current = _later_bytes((root / CORPUS).read_bytes(), root)
    if current not in {before, after} or (root / ALIASES).read_bytes() != aliases:
        raise ValueError('Current corpus or aliases changed outside uncertainty admission')
    if any((root / path).read_bytes() != raw for path, raw in outputs.items() if path != CORPUS):
        raise ValueError('Uncertainty admission no longer reproduces from current source evidence')
    return None if current == before else audit


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists():
        if b'"' + TAG.encode() + b'"' in (root / CORPUS).read_bytes():
            raise ValueError('Admitted source metadata has no frozen admission audit')
        return None
    before, after, aliases, audit, _ = _saved(root)
    current = _later_bytes((root / CORPUS).read_bytes(), root)
    if current not in {before, after} or (root / ALIASES).read_bytes() != aliases:
        raise ValueError('Current corpus or aliases differs from its exact uncertainty admission')
    if current == before:
        return None
    return {'audit': {'path': AUDIT.as_posix(), 'sha256': sha((root / AUDIT).read_bytes())},
        'source_review': deepcopy(audit['source_review']), 'pilot': deepcopy(audit['pilot']),
        'sources': deepcopy(audit['sources']), 'counts': deepcopy(audit['counts']),
        'qualification': 'Additional served source resolutions; prior source-review and experimental archives remain frozen. Independent exclusion causes still apply.'}


def apply(root=ROOT, *, admitted_at=None):
    root = Path(root)
    outputs, audit = build(root, admitted_at=admitted_at)
    if sha((root / CORPUS).read_bytes()) not in {audit['input_corpus_sha256'], audit['output_corpus_sha256']}:
        raise ValueError('Uncertainty admission requires its exact predecessor')
    for path, raw in outputs.items():
        if path != CORPUS and (root / path).exists() and (root / path).read_bytes() != raw:
            raise ValueError('Refusing to replace an immutable uncertainty admission artifact')
    for path, raw in outputs.items():
        if path != CORPUS:
            (root / path).parent.mkdir(parents=True, exist_ok=True); (root / path).write_bytes(raw)
    (root / CORPUS).write_bytes(outputs[CORPUS])
    return audit


def undo(root=ROOT):
    root = Path(root)
    before, after, aliases, _, _ = _saved(root)
    if (root / CORPUS).read_bytes() not in {before, after} or (root / ALIASES).read_bytes() != aliases:
        raise ValueError('Undo later changes before the uncertainty admission')
    (root / CORPUS).write_bytes(before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--undo', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--admitted-at')
    args = parser.parse_args()
    if args.undo:
        undo(); return
    audit = apply(admitted_at=args.admitted_at) if args.apply else check() if args.check else build(admitted_at=args.admitted_at)[1]
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == '__main__':
    main()
