#!/usr/bin/env python3
"""Compile a reversible, nonadmitting 100-span source-review experiment.

The frozen classification map contains diagnostic labels only. It permits
replaying the sample without distributing any optional comparison edition.
Candidate text and lexical projections never replace the served corpus.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
from types import ModuleType

from audit_compression import compress_gzip
import prepare_photius_review_campaign as campaign
import repair_photius_uncertainties as prior

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path('data/corpus_changes/photius-bekker-uncertainty-pilot')
TABLE = Path('scripts/photius_uncertainty_pilot_observations.py')
CLASSIFICATION = ARCHIVE / 'population-diagnostics.json'
COMPILED = Path('data/corpus_changes/photius-bekker-complete-review/review-status.json.gz')
CONTEXT = Path('data/corpus_changes/photius-bekker-context/source-review.json.gz')
CORPUS = campaign.CORPUS
SEED = 'photius-source-pilot-100-v1'
QUOTAS = {'unique': 58, 'unmatched': 39, 'tied': 2, 'nonbody': 1}
SCHEMA = 'photius-uncertainty-pilot-v1'
TAG = 'photius_uncertainty_pilot_candidate'
PINNED_INPUTS = {
    CORPUS.as_posix(): 'd4193edddda4ba27e673dcaabdae26c4711399d3c514be505a2850c6d3ccbe2b',
    COMPILED.as_posix(): '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
    CONTEXT.as_posix(): '0fd53207d99beb240439a39cf4679f4c220a02b8a96c4964991e2af2e5ee3fea',
    'data/corpus_changes/photius-bekker-context/changes.json': '440278070d34471e516a6bcc986162e62a6e1d8e2ed001fa9e759a726c3082a3',
    prior.REVIEW.as_posix(): 'b25d2ec1e7e91f64b2f3926271489c7d588a0466b239550e8e64023411982bf3',
    prior.AUDIT.as_posix(): 'af121815be1d95624e999daec6c59493044b0f7aa523c49775485bc9e0b7d408',
    'data/corpus_changes/photius-bekker-readings/source-scan.pdf': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def _public(value):
    raw = encode(value).decode()
    if any(marker in raw for marker in ('/Users/', '/home/', 'file://', 'local_candidates', 'crop_path')):
        raise ValueError('Public pilot data contains a private field or local path')


def _key(value):
    if (not isinstance(value.get('locus'), str) or type(value.get('segment_index')) is not int
            or value['segment_index'] < 0):
        raise ValueError('A pilot record needs an exact locus and segment index')
    return value['locus'], value['segment_index']


def _remaining(compiled, previous):
    resolved = {_key(d) for d in previous['records'] if d['decision'] == 'resolved'}
    values = {}
    for row in compiled['rows']:
        for index, segment in enumerate(row['segments']):
            key = row['locus'], index
            if segment['verification'] == 'uncertain' and key not in resolved:
                if key in values:
                    raise ValueError('Frozen campaign repeats a pilot candidate')
                values[key] = row, segment
    return values


def population(compiled, previous, classification):
    """Join classification-only metadata to the complete remaining scope."""
    remaining = _remaining(compiled, previous)
    raw_records = classification['records'] if isinstance(classification, dict) else classification
    records = {}
    for entry in raw_records:
        key = _key(entry)
        status, count, anchors = entry.get('match_status'), entry.get('match_count'), entry.get('anchor_count')
        if (key in records or key not in remaining or status not in {'unique', 'unmatched', 'tied'}
                or type(count) is not int or type(anchors) is not int
                or not (status == 'unique' and count == 1 and 6 <= anchors <= 10
                        or status == 'unmatched' and count == 0 and anchors == -1
                        or status == 'tied' and count >= 2 and 6 <= anchors <= 10)):
            raise ValueError('Classification labels are inconsistent or repeat a candidate')
        row, segment = remaining[key]
        scan = segment['scan']
        group = f"{row['physical_page']}:{scan['region']}:{scan['max_side']}"
        records[key] = {'locus': key[0], 'segment_index': key[1],
            'match_status': status, 'match_count': count, 'anchor_count': anchors,
            'stratum': status if segment['text_role'] == 'authorial-body' else 'nonbody',
            'group': group, 'physical_page': row['physical_page']}
    if set(records) != set(remaining):
        raise ValueError('Classification map must cover every remaining uncertain segment')
    return list(records.values())


def select_sample(values, *, seed=SEED, quotas=None):
    """Replay the stratified, crop-clustered sample, with at most six per group."""
    quotas = QUOTAS if quotas is None else quotas
    if len({_key(v) for v in values}) != len(values):
        raise ValueError('Sample population repeats a segment')
    digest = lambda value: sha(value.encode())
    selected = []
    for stratum, count in quotas.items():
        if type(count) is not int or count < 0:
            raise ValueError('Sampling quotas must be nonnegative integers')
        candidates = sorted((v for v in values if v['stratum'] == stratum), key=lambda v:
            (digest(seed + v['group']), digest(seed + v['locus'] + ':' + str(v['segment_index']))))
        used = Counter()
        chosen = []
        for value in candidates:
            if len(chosen) == count:
                break
            if used[value['group']] < 6:
                chosen.append(deepcopy(value)); used[value['group']] += 1
        if len(chosen) != count:
            raise ValueError('Frozen diagnostic population cannot meet the sample quotas')
        selected.extend(chosen)
    selected.sort(key=lambda v: (v['physical_page'], v['group'], v['locus'], v['segment_index']))
    for index, value in enumerate(selected, 1):
        value['id'] = f'P{index:03d}'
    return selected


def _current_span(row, segment, previous):
    start, end = segment['corrected_start'], segment['corrected_end']
    for decision in sorted((d for d in previous['records'] if d['locus'] == row['locus']), key=lambda d: d['start']):
        a, b = decision['start'], decision['end']
        if a < end and start < b and (a, b) != (start, end):
            raise ValueError('A prior correction partially overlaps a pilot segment')
    delta = sum(len(d['corrected_text']) - (d['end'] - d['start'])
                for d in previous['records'] if d['locus'] == row['locus'] and d['end'] <= start)
    return start + delta, end + delta


def _source_pin(sources, source_files, source_id, page, region, max_side, images, rendered):
    source = sources[source_id]
    path = prior._path(source['path']).as_posix()
    if source['kind'] not in {'pdf', 'image'} or sha(source_files[path]) != source['sha256']:
        raise ValueError('A pilot source changed or was invalidated')
    box = prior._box(region)
    if type(page) is not int or page < 1 or type(max_side) is not int or not 1 <= max_side <= 3600:
        raise ValueError('A pilot crop needs a bounded rendering recipe')
    key = source_id, page, tuple(box), max_side
    if key not in rendered:
        if source['kind'] == 'pdf':
            import pymupdf
            with pymupdf.open(stream=source_files[path], filetype='pdf') as document:
                rendered[key] = campaign._render_crop_png(document, page, box, max_side)
        else:
            if page != 1 or max_side != 3600:
                raise ValueError('Comparison images use physical page one and max_side3600')
            rendered[key] = prior._crop(source_files[path], 'image', page, box)
    raw = rendered[key]
    target = ARCHIVE / 'source-images' / (sha(raw) + '.png')
    images[target] = raw
    return {'source_id': source_id, 'source': deepcopy(source), 'scan_page': page,
            'region': box, 'max_side': max_side,
            'image': {'path': target.as_posix(), 'sha256': sha(raw)}}


def compile_review(before, compiled, previous, classification, decisions, *, reviewed_at,
                   source_files, sources=None, quotas=None):
    """Compile public observations and exact candidate row changes, without admission."""
    campaign._timestamp(reviewed_at)
    if compiled.get('schema') != campaign.COMPILED_SCHEMA or not compiled.get('scope_complete'):
        raise ValueError('Pilot review requires the complete frozen source campaign')
    values = population(compiled, previous, classification)
    selected = select_sample(values, quotas=quotas)
    by_id = {item['id']: item for item in selected}
    by_key = {_key(item): item for item in selected}
    rows = {row['locus']: row for row in map(json.loads, before.splitlines())}
    if len(rows) != len(before.splitlines()):
        raise ValueError('Candidate baseline repeats or omits a row')
    remaining = _remaining(compiled, previous)
    # A repeated reading must be reviewed at its declared occurrence. Expose
    # both exact display and scan-transcription windows before source review.
    for chosen in selected:
        record, segment = remaining[_key(chosen)]
        a, b = _current_span(record, segment, previous)
        text = rows[chosen['locus']]['text']
        observed = ''.join(s['scan']['observed_text'] for s in record['segments'])
        start = sum(len(s['scan']['observed_text']) for s in record['segments'][:chosen['segment_index']])
        end = start + len(segment['scan']['observed_text'])
        def window(value, low, high):
            return {'start': low, 'end': high, 'before': value[max(0, low-120):low],
                    'target': value[low:high], 'after': value[high:high+120]}
        chosen['display_window'] = window(text, a, b)
        chosen['scan_window'] = window(observed, start, end)
    scan = {**compiled['input_pins']['scan'], 'kind': 'pdf'}
    if sources and 'bekker' in sources:
        raise ValueError('The frozen primary scan cannot be overridden')
    all_sources = {'bekker': scan, **deepcopy(sources or {})}
    images, rendered, reviews, seen = {}, {}, [], set()
    allowed = {'id', 'locus', 'segment_index', 'original_text', 'corrected_text',
               'decision', 'evidence', 'observed_text', 'alternatives', 'source_observations',
               'blind_decision', 'blind_corrected_text', 'comparison_result', 'comparison_effect'}
    for raw in decisions:
        if set(raw) - allowed:
            raise ValueError('Pilot observations contain an undeclared public field')
        item = deepcopy(raw); _public(item)
        key = _key(item)
        selected_item = by_id.get(item.get('id'))
        if key in seen or key not in by_key or selected_item != by_key[key]:
            raise ValueError('Pilot decisions must identify the selected sample exactly once')
        seen.add(key)
        record, segment = remaining[key]
        old = rows.get(key[0])
        if old is None:
            raise ValueError('A sampled pilot passage is absent from the exact baseline')
        a, b = _current_span(record, segment, previous)
        original = segment['corrected_text']
        if old['text'][a:b] != original or item.get('original_text') != original:
            raise ValueError('A pilot observation differs from its exact current source span')
        if (item.get('decision') not in {'resolved', 'retained-uncertain'}
                or not isinstance(item.get('corrected_text'), str) or not item['corrected_text'].strip()
                or not isinstance(item.get('evidence'), str) or not item['evidence'].strip()
                or item['decision'] == 'retained-uncertain' and item['corrected_text'] != original):
            raise ValueError('A pilot decision must resolve from evidence or retain its original text')
        if 'alternatives' in item and (not isinstance(item['alternatives'], list)
                or any(not isinstance(v, str) or not v.strip() for v in item['alternatives'])):
            raise ValueError('Observed alternatives must preserve nonempty textual readings')
        if 'blind_decision' in item or 'blind_corrected_text' in item:
            if (item.get('blind_decision') not in {'resolved', 'retained-uncertain'}
                    or not isinstance(item.get('blind_corrected_text'), str)
                    or not item['blind_corrected_text'].strip()
                    or item['blind_decision'] == 'retained-uncertain' and item['blind_corrected_text'] != original):
                raise ValueError('Blind observations must preserve the exact initial decision')
        if ('comparison_result' in item and item['comparison_result'] not in
                {'matching', 'different', 'mixed', 'unavailable'} or
                'comparison_effect' in item and item['comparison_effect'] not in
                {'none', 'guided-reinspection'}):
            raise ValueError('Comparison measurements must use declared diagnostic categories')
        pin = _source_pin(all_sources, source_files, 'bekker', record['physical_page'],
            segment['scan']['region'], segment['scan']['max_side'], images, rendered)
        if pin['image']['sha256'] != segment['scan']['image_sha256']:
            raise ValueError('Pilot scan crop does not reproduce the frozen reviewed image')
        comparisons = []
        for comparison in item.pop('source_observations', []):
            if (set(comparison) - {'source_id', 'text', 'role', 'region', 'scan_page', 'evidence'}
                    or comparison.get('source_id') not in all_sources or comparison.get('role') not in prior.ROLES
                    or not isinstance(comparison.get('text'), str) or not comparison['text'].strip()):
                raise ValueError('An additional public source needs an exact reading and role')
            if comparison['role'] == 'corroborating' and comparison['text'] != item['corrected_text']:
                raise ValueError('Corroborating source text must match the proposed reading')
            comparisons.append({**comparison, **_source_pin(all_sources, source_files,
                comparison['source_id'], comparison['scan_page'], comparison['region'], 3600, images, rendered)})
        reviews.append({**item, 'start': a, 'end': b, 'original_row_sha256': prior.row_sha(old),
            'original_segment': deepcopy(segment), 'bekker': pin, 'comparisons': comparisons,
            'classification': deepcopy(selected_item)})
    if seen != set(by_key):
        raise ValueError('Every selected pilot segment needs one completed review decision')
    public_classification = {'schema': 'photius-pilot-classification-labels-v1',
        'qualification': 'Frozen diagnostic labels only. Optional edition matching is not correction authority and no comparison text is distributed.',
        'records': [{k: item[k] for k in ('locus', 'segment_index', 'match_status', 'match_count', 'anchor_count')}
                    for item in sorted(values, key=lambda v: (v['locus'], v['segment_index']))]}
    sample = {'schema': SCHEMA + '-sample', 'seed': SEED, 'quotas': QUOTAS if quotas is None else quotas,
        'max_per_crop_per_stratum': 6, 'population': dict(sorted(Counter(v['stratum'] for v in values).items())),
        'count': len(selected), 'crops': len({v['group'] for v in selected}),
        'pages': len({v['physical_page'] for v in selected}), 'records': selected,
        'qualification': 'Exploratory crop-clustered stratified sample; tied diagnostic matches are oversampled. Sample resolution fractions do not estimate population resolution rates.'}
    review = {'schema': SCHEMA, 'reviewed_at': reviewed_at, 'admission_authorized': False,
        'input_corpus_sha256': sha(before), 'sample_sha256': sha(encode(sample)),
        'sources': all_sources, 'records': sorted(reviews, key=lambda v: v['id']),
        'qualification': 'Proposed source decisions and isolated candidate projections only. Served text and all frozen prior authorities are unchanged.'}
    _public((public_classification, sample, review))
    return sample, review, public_classification, images


def plan(before, review):
    """Create reversible isolated candidates while preserving every inherited cause."""
    if review.get('schema') != SCHEMA or review.get('admission_authorized') is not False or review['input_corpus_sha256'] != sha(before):
        raise ValueError('Pilot review does not identify its exact nonadmitting baseline')
    campaign._timestamp(review['reviewed_at'])
    grouped = defaultdict(list)
    keys = []
    for decision in review['records']:
        keys.append(_key(decision)); grouped[decision['locus']].append(decision)
    if len(keys) != len(set(keys)):
        raise ValueError('Pilot review repeats a segment')
    changes, output = [], []
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        if old['locus'] not in grouped:
            output.append(line); continue
        if TAG in old:
            raise ValueError('Pilot candidates cannot be applied twice')
        decisions = sorted(grouped.pop(old['locus']), key=lambda d: d['start'])
        leaves = prior._flatten(old['text'], prior._masks(old))
        cursor, pieces, removed = 0, [], []
        for decision in decisions:
            a, b = decision['start'], decision['end']
            segment = decision['original_segment']
            if (type(a) is not int or type(b) is not int or not cursor <= a < b <= len(old['text'])
                    or old['text'][a:b] != decision['original_text'] or prior.row_sha(old) != decision['original_row_sha256']
                    or segment.get('verification') != 'uncertain' or segment['corrected_text'] != decision['original_text']
                    or decision.get('decision') not in {'resolved', 'retained-uncertain'}
                    or not isinstance(decision.get('corrected_text'), str) or not decision['corrected_text'].strip()
                    or not decision.get('evidence') or not decision.get('bekker')
                    or decision['decision'] == 'retained-uncertain' and decision['corrected_text'] != decision['original_text']):
                raise ValueError('Pilot candidate changed a source decision or exact preimage')
            matches = [leaf for leaf in leaves if leaf['start'] == a and leaf['end'] == b
                and leaf.get('classification') == 'unresolved-source-reading'
                and leaf.get('qualification') == segment.get('uncertainty')]
            if not matches:
                # The context layer can expand a subword uncertainty to the
                # entire lexical word. A retained subword leaves that cause
                # untouched; it cannot authorize removing the larger mask.
                enclosing = [leaf for leaf in leaves if leaf['start'] <= a < b <= leaf['end']
                    and leaf.get('classification') == 'unresolved-source-reading'
                    and leaf.get('qualification') == segment.get('uncertainty')]
                if decision['decision'] != 'retained-uncertain' or not enclosing:
                    raise ValueError('The pilot segment has no exact inherited uncertainty cause')
            if decision['decision'] == 'resolved':
                removed.extend(matches); leaves = [leaf for leaf in leaves if leaf not in matches]
            pieces.extend((old['text'][cursor:a], decision['corrected_text'])); cursor = b
        pieces.append(old['text'][cursor:]); text = ''.join(pieces)
        remaining = [prior._rebase(leaf, decisions, text) for leaf in leaves]
        for decision in decisions:
            if any(comparison['role'] == 'contrary' for comparison in decision['comparisons']):
                start = decision['start'] + sum(len(d['corrected_text']) - (d['end'] - d['start'])
                    for d in decisions if d['end'] <= decision['start'])
                remaining.append({'start': start, 'end': start + len(decision['corrected_text']),
                    'text': decision['corrected_text'], 'classification': 'retained-contrary-source-reading',
                    'alternatives': deepcopy(decision['comparisons'])})
        exclusions, runs = prior._projection(text, remaining)
        new = deepcopy(old); new.update(text=text, analysis_text=' '.join(runs))
        new[TAG] = {'schema': SCHEMA, 'admission_authorized': False,
            'review_sha256': sha(encode(review)), 'excluded_spans': exclusions,
            'qualification': 'Isolated experimental candidate; not a served corpus admission.'}
        changes.append({'locus': old['locus'], 'original_row': old, 'corrected_row': new,
            'original_line': line.decode(),
            'original_row_sha256': prior.row_sha(old), 'corrected_row_sha256': prior.row_sha(new),
            'decisions': decisions, 'removed_uncertainty_causes': removed,
            'remaining_exclusion_causes': remaining, 'reviewed_at': review['reviewed_at']})
        output.append(campaign.canonical(new) + b'\n')
    if grouped:
        raise ValueError('Pilot review invents a passage')
    return b''.join(output), changes


def unapply(after, changes, *, before_sha256):
    """Restore exact original rows from checked candidate postimages."""
    by_locus = {change['locus']: change for change in changes}
    if len(by_locus) != len(changes):
        raise ValueError('Pilot undo repeats a passage')
    result = []
    for line in after.splitlines(keepends=True):
        row = json.loads(line); change = by_locus.pop(row['locus'], None)
        if change is None:
            result.append(line); continue
        if (row != change['corrected_row'] or prior.row_sha(row) != change['corrected_row_sha256']
                or prior.row_sha(change['original_row']) != change['original_row_sha256']
                or json.loads(change['original_line']) != change['original_row']):
            raise ValueError('Pilot undo differs from its exact row preimage or postimage')
        result.append(change['original_line'].encode())
    restored = b''.join(result)
    if by_locus or sha(restored) != before_sha256:
        raise ValueError('Pilot undo does not reconstruct its exact baseline bytes')
    return restored


def replay(before, changes, *, before_sha256, after_sha256):
    """Replay literal archived candidate rows without consulting correction sources."""
    if sha(before) != before_sha256:
        raise ValueError('Pilot replay does not identify its exact baseline')
    by_locus = {change['locus']: change for change in changes}
    if len(by_locus) != len(changes):
        raise ValueError('Pilot replay repeats a passage')
    result = []
    for line in before.splitlines(keepends=True):
        old = json.loads(line); change = by_locus.pop(old['locus'], None)
        if change is None:
            result.append(line); continue
        new = change['corrected_row']
        allowed = deepcopy(old)
        allowed.update(text=new['text'], analysis_text=new['analysis_text'], **{TAG: new[TAG]})
        if (line.decode() != change['original_line'] or old != change['original_row']
                or prior.row_sha(old) != change['original_row_sha256']
                or prior.row_sha(new) != change['corrected_row_sha256'] or new != allowed
                or new[TAG].get('admission_authorized') is not False):
            raise ValueError('Pilot replay changed its exact original, candidate, or frozen prior tags')
        result.append(campaign.canonical(new) + b'\n')
    result = b''.join(result)
    if by_locus or sha(result) != after_sha256:
        raise ValueError('Pilot replay does not reconstruct its exact candidate bytes')
    return result


def build(root=ROOT, *, classification_path=None, table_path=TABLE):
    root = Path(root)
    recipe_names = ('prepare_photius_uncertainty_pilot.py', 'prepare_photius_review_campaign.py',
                    'repair_photius_uncertainties.py', 'audit_compression.py',
                    'compare_photius_local_edition.py', 'assess_photius_historical.py')
    recipes = {name: sha((root / 'scripts' / name).read_bytes()) for name in recipe_names}
    baseline_snapshot = root / ARCHIVE / 'before-corpus.jsonl.gz'
    frozen_baseline = baseline_snapshot.exists()
    def read_input(name):
        if name == CORPUS.as_posix() and frozen_baseline:
            return gzip.decompress(baseline_snapshot.read_bytes())
        return (root / name).read_bytes()
    inputs = {name: read_input(name) for name in PINNED_INPUTS}
    if any(sha(inputs[name]) != digest for name, digest in PINNED_INPUTS.items()):
        raise ValueError('Pinned pilot baseline or prior review authority changed')
    table_path = prior._path(table_path)
    table_raw = (root / table_path).read_bytes(); _public(table_raw.decode())
    module = ModuleType('photius_pilot_observations')
    exec(compile(table_raw, table_path.as_posix(), 'exec'), module.__dict__)
    classification_path = root / CLASSIFICATION if classification_path is None else Path(classification_path)
    classification_raw = classification_path.read_bytes()
    classification = json.loads(classification_raw)
    expected_diagnostic_pins = {
        'compiled_sha256': sha(inputs[COMPILED.as_posix()]),
        'context_sha256': sha(inputs[CONTEXT.as_posix()]),
        'prior_uncertainties_sha256': sha(inputs[prior.REVIEW.as_posix()])}
    diagnostic_pins = classification.get('pins', {})
    if any(diagnostic_pins.get(name) != digest for name, digest in expected_diagnostic_pins.items()):
        raise ValueError('Diagnostic classifications differ from their pinned public review inputs')
    opaque_digest = diagnostic_pins.get('local_html_sha256')
    if opaque_digest is not None and (not isinstance(opaque_digest, str) or len(opaque_digest) != 64
            or any(character not in '0123456789abcdef' for character in opaque_digest)):
        raise ValueError('Optional comparison edition needs a checksum, never a local path')
    compiled = json.loads(gzip.decompress(inputs[COMPILED.as_posix()]))
    previous = json.loads(inputs[prior.REVIEW.as_posix()])
    sources = getattr(module, 'SOURCES', {})
    source_files = {value['path']: (root / prior._path(value['path'])).read_bytes() for value in sources.values()}
    scan = compiled['input_pins']['scan']; source_files[scan['path']] = inputs[scan['path']]
    sample, review, public_classification, images = compile_review(inputs[CORPUS.as_posix()], compiled,
        previous, classification, module.records(), reviewed_at=module.REVIEWED_AT,
        source_files=source_files, sources=sources)
    public_classification['pins'] = {**expected_diagnostic_pins,
        **({'local_html_sha256': opaque_digest} if opaque_digest is not None else {})}
    timing = getattr(module, 'TIMING', {})
    if (not isinstance(timing, dict) or any(not isinstance(key, str)
            or type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for key, value in timing.items())):
        raise ValueError('Reviewer timing must contain named finite nonnegative measurements')
    diagnostic_seconds = classification.get('elapsed_seconds')
    if diagnostic_seconds is not None:
        if type(diagnostic_seconds) not in (int, float) or not math.isfinite(diagnostic_seconds) or diagnostic_seconds < 0:
            raise ValueError('Diagnostic timing must be a finite nonnegative measured duration')
        public_classification['elapsed_seconds'] = diagnostic_seconds
    consultations = getattr(module, 'WEB_CONSULTATIONS', [])
    if not isinstance(consultations, list):
        raise ValueError('Bounded web consultations must be a list')
    _public(consultations)
    review['web_consultations'] = deepcopy(consultations)
    review['reviewer_timing'] = deepcopy(timing)
    review['input_pins'] = deepcopy(PINNED_INPUTS)
    review['source_table'] = {'path': table_path.as_posix(), 'sha256': sha(table_raw)}
    classification_output = encode(public_classification)
    review['classification'] = {'path': CLASSIFICATION.as_posix(), 'sha256': sha(classification_output)}
    before = inputs[CORPUS.as_posix()]
    after, changes = plan(before, review)
    if unapply(after, changes, before_sha256=sha(before)) != before:
        raise ValueError('Pilot candidate does not undo exactly')
    if replay(before, changes, before_sha256=sha(before), after_sha256=sha(after)) != after:
        raise ValueError('Pilot candidate does not replay exactly')
    by_stratum = {}
    for stratum in QUOTAS:
        decisions = [d for d in review['records'] if d['classification']['stratum'] == stratum]
        by_stratum[stratum] = dict(sorted(Counter(d['decision'] for d in decisions).items()))
    counts = {'sampled_spans': len(review['records']), 'candidate_rows': len(changes),
        'resolved_changed': sum(d['decision'] == 'resolved' and d['original_text'] != d['corrected_text'] for d in review['records']),
        'resolved_unchanged': sum(d['decision'] == 'resolved' and d['original_text'] == d['corrected_text'] for d in review['records']),
        'retained_uncertain': sum(d['decision'] == 'retained-uncertain' for d in review['records']),
        'by_stratum': by_stratum, 'served_corpus_changes': 0,
        'baseline_remaining_uncertain_spans': len(population(compiled, previous, classification)),
        'candidate_remaining_uncertain_spans': len(population(compiled, previous, classification))
            - sum(d['decision'] == 'resolved' for d in review['records']),
        'blind_resolved': sum(d.get('blind_decision') == 'resolved' for d in review['records']),
        'blind_resolutions_withheld': sum(d.get('blind_decision') == 'resolved'
            and d['decision'] == 'retained-uncertain' for d in review['records']),
        'comparison_guided_resolutions': sum(d.get('blind_decision') == 'retained-uncertain'
            and d['decision'] == 'resolved' and d.get('comparison_effect') == 'guided-reinspection'
            for d in review['records']),
        'resolved_comparison_relationship': dict(sorted(Counter(d.get('comparison_result', 'unmeasured')
            for d in review['records'] if d['decision'] == 'resolved').items()))}
    files = {ARCHIVE / 'sample.json': encode(sample), ARCHIVE / 'source-review.json': encode(review),
        CLASSIFICATION: classification_output, ARCHIVE / 'source-table.py': table_raw,
        ARCHIVE / 'before-corpus.jsonl.gz': compress_gzip(before),
        ARCHIVE / 'candidate-corpus.jsonl.gz': compress_gzip(after),
        ARCHIVE / 'records.jsonl.gz': compress_gzip(b''.join(campaign.canonical(d) + b'\n' for d in changes)), **images}
    audit = {'schema': SCHEMA, 'admission_authorized': False, 'reviewed_at': module.REVIEWED_AT,
        'input_pins': deepcopy(PINNED_INPUTS), 'recipe_sha256': recipes,
        'before_corpus_sha256': sha(before), 'candidate_corpus_sha256': sha(after),
        'counts': counts, 'outputs': {p.as_posix(): sha(raw) for p, raw in files.items()},
        'qualification': 'Exploratory source review only. Candidate reductions are planned, not served or population estimates. Existing corpus and all prior audits remain unchanged.'}
    files[ARCHIVE / 'changes.json'] = encode(audit)
    if (any(read_input(name) != raw for name, raw in inputs.items())
            or (root / table_path).read_bytes() != table_raw
            or classification_path.read_bytes() != classification_raw
            or any((root / prior._path(name)).read_bytes() != raw for name, raw in source_files.items())
            or any(sha((root / 'scripts' / name).read_bytes()) != digest for name, digest in recipes.items())):
        raise ValueError('Pilot inputs changed during compilation')
    return files, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true')
    action.add_argument('--check', action='store_true')
    parser.add_argument('--classification', type=Path)
    args = parser.parse_args()
    files, audit = build(classification_path=args.classification)
    if args.write:
        for path, raw in files.items():
            if (ROOT / path).exists() and (ROOT / path).read_bytes() != raw:
                raise ValueError('Refusing to replace a frozen pilot artifact: ' + path.as_posix())
        for path, raw in files.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True); (ROOT / path).write_bytes(raw)
    elif args.check:
        if any((ROOT / path).read_bytes() != raw for path, raw in files.items()):
            raise ValueError('Pilot artifacts do not reproduce')
    print(json.dumps(audit['counts'], ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
