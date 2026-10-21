#!/usr/bin/env python3
"""Apply attributed editorial readings without certifying the original scan.

Exact segment identities and source-token references bind every substitution.
The original source uncertainties remain historical facts; this layer records
the choice of another edition. All prior tags, alternatives, and independent
exclusion causes survive in the reversible audit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

from audit_compression import compress_gzip
import compare_photius_local_edition as edition
import prepare_photius_review_campaign as campaign
import prepare_photius_uncertainty_pilot as pilot
import prepare_photius_editorial_substitutions as preparer
import repair_photius_uncertainties as prior
import repair_photius_uncertainty_admission as admission

ROOT = Path(__file__).resolve().parents[1]
CORPUS, ALIASES = campaign.CORPUS, admission.ALIASES
ARCHIVE = Path('data/corpus_changes/photius-bekker-editorial-substitutions')
SOURCE_REVIEW = ARCHIVE / 'source-review.json'
REVIEW = ARCHIVE / 'compiled-review.json.gz'
AUDIT = ARCHIVE / 'changes.json'
BEFORE = ARCHIVE / 'before-corpus.jsonl.gz'
BEFORE_ALIASES = ARCHIVE / 'before-aliases.json.gz'
RECORDS = ARCHIVE / 'records.jsonl.gz'
COMPILED = pilot.COMPILED
TAG = 'photius_editorial_substitution'
INPUT_SCHEMA = 'photius-editorial-substitution-review-v1'
SCHEMA = 'photius-editorial-substitution-admission-v1'
BASELINE_SHA256 = '270cb8947e122abeba1ce8a7b7e484d0b8025852a5e3296c387d175fed17c72f'
ALIASES_SHA256 = admission.ALIASES_SHA256
INPUT_SHA256 = {
    COMPILED: '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
    prior.REVIEW: 'b25d2ec1e7e91f64b2f3926271489c7d588a0466b239550e8e64023411982bf3',
    admission.REVIEW: '675e9b0a86ceb2356966771914d66308cfd3d81e2cef851d7ecacd5670ca45ac',
}
DECISIONS = {'substitute', 'retained-unmapped', 'retained-tied', 'retained-nonbody'}
END_MARKS = edition.assess.APOSTROPHES + '\u02b9\u0374'
RECIPE_NAMES = ('repair_photius_editorial_substitutions.py', 'compare_photius_local_edition.py',
    'prepare_photius_review_campaign.py', 'prepare_photius_uncertainty_pilot.py',
    'repair_photius_uncertainties.py', 'repair_photius_uncertainty_admission.py', 'audit_compression.py',
    'prepare_photius_editorial_substitutions.py', 'repair_photius_context.py', 'assess_photius_historical.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def _nfc(text):
    return unicodedata.normalize('NFC', text)


def _public(value):
    pilot._public(value)
    if re.search(r'[A-Za-z]:\\\\', encode(value).decode()):
        raise ValueError('Editorial audit cannot contain a personal filesystem path')


def _shift(a, b, decisions):
    for decision in decisions:
        low, high = decision['start'], decision['end']
        if low < b and a < high and (low, high) != (a, b):
            raise ValueError('A preceding source correction partially overlaps an editorial segment')
    delta = sum(len(d['corrected_text']) - (d['end'] - d['start']) for d in decisions if d['end'] <= a)
    return a + delta, b + delta


def scope(before, complete, prior_review, admitted_review):
    """Locate remaining complete-review identities after both preceding stages."""
    rows = {row['locus']: row for row in map(json.loads, before.splitlines())}
    if len(rows) != len(before.splitlines()):
        raise ValueError('Editorial baseline repeats or omits a passage')
    resolved = {pilot._key(d) for document in (prior_review, admitted_review)
                for d in document['records'] if d['decision'] == 'resolved'}
    stages = []
    for document in (prior_review, admitted_review):
        grouped = defaultdict(list)
        for decision in document['records']:
            grouped[decision['locus']].append(decision)
        stages.append(grouped)
    values = {}
    for record in complete['rows']:
        old = rows.get(record['locus'])
        if old is None:
            raise ValueError('A source campaign passage is absent from the editorial baseline')
        for index, segment in enumerate(record['segments']):
            key = record['locus'], index
            if segment['verification'] != 'uncertain' or key in resolved:
                continue
            a, b = segment['corrected_start'], segment['corrected_end']
            for stage in stages:
                a, b = _shift(a, b, stage.get(record['locus'], []))
            if key in values or not 0 <= a < b <= len(old['text']) or old['text'][a:b] != segment['corrected_text']:
                raise ValueError('A remaining editorial segment lost its exact current preimage')
            values[key] = {'record': record, 'segment': segment, 'row': old, 'start': a, 'end': b}
    return values


def _source_tokens(raw, source):
    if sha(raw) != source.get('sha256'):
        raise ValueError('The attributed comparison HTML changed or was invalidated')
    for name in ('id', 'edition', 'citation'):
        if not isinstance(source.get(name), str) or not source[name].strip():
            raise ValueError('Editorial readings need an exact source identity and edition citation')
    _public(source)
    parser = edition.EditionHTML(); parser.feed(raw.decode('utf-8-sig'))
    tokens = edition.tokenize(parser.units)
    for token in tokens:
        ref = token['refs'][-1]
        unit = parser.units[ref['unit_index']]['text']
        if ref['end'] < len(unit) and unit[ref['end']] in edition.assess.APOSTROPHES:
            token['text'] += unit[ref['end']]
            ref['end'] += 1
    by_refs = {sha(campaign.canonical(token['refs'])): (index, token) for index, token in enumerate(tokens)}
    if len(by_refs) != len(tokens):
        raise ValueError('Comparison token references are not unique')
    return by_refs


def _reading(reading, source, source_tokens, target):
    if (reading.get('source_id') != source['id'] or reading.get('role') not in {'chosen', 'alternative'}
            or not isinstance(reading.get('tokens'), list) or not reading['tokens']):
        raise ValueError('An editorial reading needs attributed Greek tokens and an explicit role')
    indices, texts = [], []
    for value in reading['tokens']:
        known = source_tokens.get(sha(campaign.canonical(value.get('refs'))))
        if known is None or not isinstance(value.get('text'), str) or _nfc(value['text']) != _nfc(known[1]['text']):
            raise ValueError('Editorial source token text or exact HTML-node references changed')
        for ref in value['refs']:
            match = re.fullmatch(r'(\d+)[ab]?', str(ref.get('bekker', '')))
            if not match or abs(int(match[1]) - target['record']['printed_page']) > 1:
                raise ValueError('Editorial source occurrence is outside the bounded Bekker context')
        indices.append(known[0]); texts.append(value['text'])
    if any(right != left + 1 for left, right in zip(indices, indices[1:])):
        raise ValueError('Editorial source reading skips or reorders Greek tokens')
    text = ' '.join(texts)
    if not isinstance(reading.get('text'), str) or _nfc(reading['text']) != _nfc(text):
        raise ValueError('Editorial reading does not reproduce its exact source tokens')
    if 'refs' in reading and reading['refs'] != [ref for value in reading['tokens'] for ref in value['refs']]:
        raise ValueError('Editorial reading flattened references changed')
    text = _nfc(text)
    trim = reading.get('trim', {})
    if not isinstance(trim, dict) or set(trim) - {'prefix', 'suffix'}:
        raise ValueError('Partial-word trimming needs explicit verified prefix and suffix')
    prefix, suffix = trim.get('prefix', ''), trim.get('suffix', '')
    if not isinstance(prefix, str) or not isinstance(suffix, str):
        raise ValueError('Partial-word trim affixes must be exact strings')
    if not text.startswith(prefix) or not text.endswith(suffix) or len(prefix) + len(suffix) >= len(text):
        raise ValueError('Trim affixes do not leave a nonempty exact source reading')
    a, b, row_text = target['start'], target['end'], target['row']['text']
    if (a < len(prefix) or _nfc(row_text[a-len(prefix):a]) != prefix
            or _nfc(row_text[b:b+len(suffix)]) != suffix):
        raise ValueError('Trim affixes differ from the verified current surrounding text')
    result = text[len(prefix):len(text)-len(suffix) if suffix else len(text)]
    if 'applied_text' in reading and reading['applied_text'] != result:
        raise ValueError('Trimmed editorial reading differs from its declared applied text')
    return result


def _wrapper(value):
    return isinstance(value, str) and not edition.WORD.search(value)


def compile_review(before, complete, prior_review, admitted_review, authored, source_raw, *, _recorded_tokens=None):
    """Validate every remaining identity and exact optional-edition Greek reading."""
    _public(authored)
    if (authored.get('schema') != INPUT_SCHEMA or authored.get('input_corpus_sha256') != sha(before)
            or not complete.get('scope_complete')):
        raise ValueError('Editorial review differs from its exact complete-campaign baseline')
    campaign._timestamp(authored['reviewed_at'])
    remaining = scope(before, complete, prior_review, admitted_review)
    source = authored['source']
    source_tokens = _source_tokens(source_raw, source) if _recorded_tokens is None else _recorded_tokens
    records, seen = [], set()
    for raw in authored['records']:
        item = deepcopy(raw); _public(item); key = pilot._key(item)
        if key in seen or key not in remaining:
            raise ValueError('Editorial review repeats or invents a remaining segment')
        seen.add(key); target = remaining[key]
        segment, old, a, b = target['segment'], target['row'], target['start'], target['end']
        if (item.get('original_text') != old['text'][a:b] or item.get('decision') not in DECISIONS
                or not isinstance(item.get('corrected_text'), str) or not item['corrected_text'].strip()
                or not isinstance(item.get('evidence'), str) or not item['evidence'].strip()):
            raise ValueError('Editorial decision has no exact preimage or explicit justification')
        readings = item.get('readings', [])
        if not isinstance(readings, list):
            raise ValueError('Editorial alternatives must be an explicit list')
        values = [_reading(reading, source, source_tokens, target) for reading in readings]
        prefix, suffix = item.get('display_prefix', ''), item.get('display_suffix', '')
        if (not _wrapper(prefix) or not _wrapper(suffix) or not item['original_text'].startswith(prefix)
                or not item['original_text'].endswith(suffix)):
            raise ValueError('Display wrappers must preserve exact original nonlexical characters')
        if item['decision'] == 'substitute':
            if (segment['text_role'] != 'authorial-body' or not values or len(set(values)) != 1
                    or not any(reading['role'] == 'chosen' for reading in readings)
                    or item['corrected_text'] != prefix + values[0] + suffix):
                raise ValueError('Editorial substitution needs an unambiguous attributed body reading')
            words = list(edition.WORD.finditer(item['original_text']))
            if not words:
                raise ValueError('Editorial substitution has no original Greek text')
            expected_prefix = item['original_text'][:words[0].start()]
            expected_suffix = item['original_text'][words[-1].end():]
            if expected_suffix and (expected_suffix[0] in edition.assess.APOSTROPHES
                    or expected_suffix[0] in END_MARKS and _nfc(values[0][-1]) == _nfc(expected_suffix[0])):
                expected_suffix = expected_suffix[1:]
            if prefix != expected_prefix or suffix != expected_suffix:
                raise ValueError('Editorial substitution drops an original display wrapper')
        elif item['corrected_text'] != item['original_text']:
            raise ValueError('A retained editorial decision cannot silently change display')
        if segment['text_role'] != 'authorial-body' and item['decision'] != 'retained-nonbody':
            raise ValueError('Nonbody source material cannot be substituted as ancient body text')
        for reading in readings:
            trim = reading.get('trim', {})
            low, high = a-len(trim.get('prefix', '')), b+len(trim.get('suffix', ''))
            if any(other_key != key and value['row']['locus'] == old['locus'] and
                   (value['start'] < a and low < value['end'] or value['start'] < high and b < value['end'])
                   for other_key, value in remaining.items()):
                raise ValueError('Partial-word trim borrows another uncertain source segment')
        records.append({**item, 'start': a, 'end': b, 'original_segment': deepcopy(segment),
            'original_row_sha256': prior.row_sha(old), 'physical_page': target['record']['physical_page'],
            'printed_page': target['record']['printed_page'], 'verification': 'editorial-substitution-not-scan-verification'})
    if seen != set(remaining):
        raise ValueError('Editorial review must account for every remaining source uncertainty')
    return {'schema': SCHEMA, 'work': 'photius.bibliotheca', 'reviewed_at': authored['reviewed_at'],
        'input_corpus_sha256': sha(before), 'source': deepcopy(source), 'records': records,
        'scan_uncertainty_spans': len(remaining),
        'qualification': 'Attributed substitution of another edition; original scan uncertainties and all earlier review facts remain unchanged.'}


def _masks(row):
    return row[admission.TAG]['excluded_spans'] if row.get(admission.TAG) else prior._masks(row)


def plan(before, review_raw):
    review = json.loads(review_raw)
    if review.get('schema') != SCHEMA or review.get('input_corpus_sha256') != sha(before):
        raise ValueError('Editorial authority does not identify its exact preimage')
    campaign._timestamp(review['reviewed_at'])
    grouped = defaultdict(list); keys = []
    for decision in review['records']:
        keys.append(pilot._key(decision)); grouped[decision['locus']].append(decision)
    if len(keys) != len(set(keys)) or review['scan_uncertainty_spans'] != len(keys):
        raise ValueError('Editorial authority repeats or drops a source identity')
    output, changes = [], []
    reference = {'path': REVIEW.as_posix(), 'uncompressed_sha256': sha(review_raw)}
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        if old['locus'] not in grouped:
            output.append(line); continue
        if old.get(TAG):
            raise ValueError('Editorial substitution cannot apply twice')
        decisions = sorted(grouped.pop(old['locus']), key=lambda d: d['start'])
        leaves = prior._flatten(old['text'], _masks(old)); removed, remaining = [], []
        for leaf in leaves:
            associated = [d for d in decisions if d['start'] < leaf['end'] and leaf['start'] < d['end']]
            belongs = any(leaf.get('qualification') == d['original_segment'].get('uncertainty') for d in associated)
            if (leaf.get('classification') == 'unresolved-source-reading' and belongs
                    and associated and all(d['decision'] == 'substitute' for d in associated)):
                removed.append(leaf)
            else:
                remaining.append(leaf)
        cursor, pieces = 0, []
        for decision in decisions:
            a, b = decision['start'], decision['end']
            if (type(a) is not int or type(b) is not int or not cursor <= a < b <= len(old['text'])
                    or old['text'][a:b] != decision['original_text'] or prior.row_sha(old) != decision['original_row_sha256']
                    or decision.get('decision') not in DECISIONS
                    or decision['decision'] != 'substitute' and decision['corrected_text'] != decision['original_text']):
                raise ValueError('Editorial decision changed its exact source preimage')
            if not any(leaf.get('classification') == 'unresolved-source-reading'
                    and leaf['start'] <= a < b <= leaf['end']
                    and leaf.get('qualification') == decision['original_segment'].get('uncertainty') for leaf in leaves):
                raise ValueError('Editorial segment has no inherited source uncertainty cause')
            pieces.extend((old['text'][cursor:a], decision['corrected_text'])); cursor = b
        pieces.append(old['text'][cursor:]); text = ''.join(pieces)
        remaining = [prior._rebase(leaf, decisions, text) for leaf in remaining]
        exclusions, runs = prior._projection(text, remaining)
        new = deepcopy(old); new.update(text=text, analysis_text=' '.join(runs))
        new[TAG] = {'schema': SCHEMA, 'source_review': reference,
            'original_row_sha256': prior.row_sha(old), 'reviewed_at': review['reviewed_at'],
            'editorial_source': deepcopy(review['source']),
            'excluded_spans': {'path': RECORDS.as_posix(), 'locus': old['locus'],
                               'sha256': sha(campaign.canonical(exclusions))},
            'substituted': sum(d['decision'] == 'substitute' for d in decisions),
            'qualification': 'Another edition supplies these readings. This does not verify or change the historical scan-review status.'}
        changes.append({'locus': old['locus'], 'original_row': old, 'corrected_row': new,
            'original_line': line.decode(), 'original_row_sha256': prior.row_sha(old),
            'corrected_row_sha256': prior.row_sha(new), 'decisions': decisions,
            'excluded_spans': exclusions,
            'retired_uncertainty_causes': removed, 'remaining_exclusion_causes': remaining,
            'reviewed_at': review['reviewed_at']})
        output.append(campaign.canonical(new) + b'\n')
    if grouped:
        raise ValueError('Editorial substitution invents a passage')
    substituted = [{'locus': d['locus'], 'segment_index': d['segment_index']}
                   for d in review['records'] if d['decision'] == 'substitute']
    counts = {'rows': len(changes), 'decisions': len(keys), 'scan_uncertainty_spans': len(keys),
        'editorially_substituted_spans': len(substituted),
        'unsubstituted_source_uncertainty_spans': len(keys)-len(substituted),
        'substituted_identities': substituted,
        'changed_display_rows': sum(c['original_row']['text'] != c['corrected_row']['text'] for c in changes),
        'changed_spans': sum(d['decision'] == 'substitute' and d['original_text'] != d['corrected_text'] for d in review['records']),
        'decisions_by_status': dict(sorted(Counter(d['decision'] for d in review['records']).items())),
        'primary_rows_before': len(before.splitlines()), 'primary_rows_after': len(output)}
    return b''.join(output), changes, counts


def artifacts(before, aliases, review_raw, *, pins, recipes):
    after, changes, counts = plan(before, review_raw)
    files = {BEFORE: compress_gzip(before), BEFORE_ALIASES: compress_gzip(aliases),
        REVIEW: compress_gzip(review_raw),
        RECORDS: compress_gzip(b''.join(campaign.canonical(c)+b'\n' for c in changes))}
    review = json.loads(review_raw)
    audit = {'schema': SCHEMA, 'work': 'photius.bibliotheca', 'reviewed_at': review['reviewed_at'],
        'input_corpus_sha256': sha(before), 'output_corpus_sha256': sha(after),
        'aliases_sha256': sha(aliases), 'source': deepcopy(review['source']),
        'source_review': {'path': REVIEW.as_posix(), 'sha256': sha(files[REVIEW]),
                          'uncompressed_sha256': sha(review_raw)},
        'input_pins': deepcopy(pins), 'recipe_sha256': deepcopy(recipes), 'counts': counts,
        'outputs': {path.as_posix(): sha(raw) for path, raw in files.items()}}
    audit['outputs'][CORPUS.as_posix()] = sha(after)
    return {CORPUS: after, **files, AUDIT: encode(audit)}, audit


def _html_bytes(value):
    value = os.environ.get('PHOTIUS_COMPARISON_HTML') if value is None else value
    if value is None:
        raise ValueError('Fresh editorial validation requires --source-html or PHOTIUS_COMPARISON_HTML')
    return value if isinstance(value, bytes) else Path(value).read_bytes()


def build(root=ROOT, *, source_html=None):
    root = Path(root)
    recipes = {name: sha((root/'scripts'/name).read_bytes()) for name in RECIPE_NAMES}
    raw_html = _html_bytes(source_html)
    authored_raw = (root/SOURCE_REVIEW).read_bytes()
    before = gzip.decompress((root/BEFORE).read_bytes()) if (root/AUDIT).exists() else (root/CORPUS).read_bytes()
    aliases = (root/ALIASES).read_bytes()
    if sha(before) != BASELINE_SHA256 or sha(aliases) != ALIASES_SHA256:
        raise ValueError('Editorial substitution requires its exact preceding corpus and aliases')
    input_paths = (COMPILED, prior.REVIEW, admission.REVIEW)
    inputs = {path: (root/path).read_bytes() for path in input_paths}
    if any(sha(raw) != INPUT_SHA256[path] for path, raw in inputs.items()):
        raise ValueError('Frozen source-review inputs changed')
    authored = json.loads(authored_raw)
    if preparer.prepare(raw_html, root, reviewed_at=authored['reviewed_at']) != authored:
        raise ValueError('Editorial source decisions do not reproduce their contextual selection')
    complete = json.loads(gzip.decompress(inputs[COMPILED]))
    review = compile_review(before, complete, json.loads(inputs[prior.REVIEW]),
        json.loads(inputs[admission.REVIEW]), authored, raw_html)
    pins = {path.as_posix(): sha(raw) for path, raw in inputs.items()}
    pins[SOURCE_REVIEW.as_posix()] = sha(authored_raw)
    files, audit = artifacts(before, aliases, encode(review), pins=pins, recipes=recipes)
    if ((root/SOURCE_REVIEW).read_bytes() != authored_raw or (root/ALIASES).read_bytes() != aliases
            or any((root/path).read_bytes() != raw for path, raw in inputs.items())
            or _html_bytes(source_html) != raw_html
            or any(sha((root/'scripts'/name).read_bytes()) != digest for name, digest in recipes.items())):
        raise ValueError('Editorial inputs changed during source validation')
    return files, audit


@lru_cache(maxsize=1)
def _literal_saved(audit_raw, before_raw, aliases_raw, review_gzip, records_gzip):
    audit = json.loads(audit_raw)
    for path, raw in ((BEFORE, before_raw), (BEFORE_ALIASES, aliases_raw), (REVIEW, review_gzip), (RECORDS, records_gzip)):
        if sha(raw) != audit['outputs'][path.as_posix()]:
            raise ValueError('Frozen editorial admission artifact changed')
    before, aliases, review_raw = gzip.decompress(before_raw), gzip.decompress(aliases_raw), gzip.decompress(review_gzip)
    review = json.loads(review_raw)
    after, changes, counts = plan(before, review_raw)
    if (audit.get('schema') != SCHEMA or sha(before) != audit['input_corpus_sha256']
            or sha(after) != audit['output_corpus_sha256'] or sha(aliases) != audit['aliases_sha256']
            or audit['outputs'][CORPUS.as_posix()] != sha(after) or counts != audit['counts']
            or [json.loads(line) for line in gzip.decompress(records_gzip).splitlines()] != changes
            or audit['source_review'] != {'path': REVIEW.as_posix(), 'sha256': sha(review_gzip), 'uncompressed_sha256': sha(review_raw)}
            or audit.get('source') != review.get('source') or audit.get('work') != review.get('work')
            or audit.get('reviewed_at') != review.get('reviewed_at')):
        raise ValueError('Editorial archive does not reproduce its exact preimages and postimages')
    return before, after, aliases, audit


def _saved(root):
    before, after, aliases, audit = _literal_saved(*((Path(root)/p).read_bytes()
        for p in (AUDIT, BEFORE, BEFORE_ALIASES, REVIEW, RECORDS)))
    return before, after, aliases, deepcopy(audit)


@lru_cache(maxsize=2)
def _record_map(raw):
    values = [json.loads(line) for line in gzip.decompress(raw).splitlines()]
    result = {value['locus']: value for value in values}
    if len(result) != len(values):
        raise ValueError('Editorial row archive repeats a passage')
    return result


def restore_before_bytes(raw, root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        if b'"'+TAG.encode()+b'"' in raw:
            raise ValueError('Editorial metadata has no frozen authority')
        return raw
    before, after, _, _ = _saved(root)
    if raw not in {before, after}:
        raise ValueError('Editorial corpus differs from its exact postimage')
    return before


def _checked_row_record(row, root):
    root = Path(root); audit = json.loads((root/AUDIT).read_bytes())
    records_raw, review_raw = (root/RECORDS).read_bytes(), (root/REVIEW).read_bytes()
    if sha(records_raw) != audit['outputs'][RECORDS.as_posix()] or sha(review_raw) != audit['source_review']['sha256']:
        raise ValueError('Editorial row authority changed')
    change = _record_map(records_raw).get(row.get('locus'))
    if (not change or row != change['corrected_row'] or prior.row_sha(row) != change['corrected_row_sha256']
            or prior.row_sha(change['original_row']) != change['original_row_sha256']
            or json.loads(change['original_line']) != change['original_row']
            or row[TAG].get('schema') != SCHEMA
            or row[TAG]['source_review']['uncompressed_sha256'] != audit['source_review']['uncompressed_sha256']
            or row[TAG]['excluded_spans'] != {'path': RECORDS.as_posix(), 'locus': row['locus'],
                'sha256': sha(campaign.canonical(change['excluded_spans']))}):
        raise ValueError('Editorial row differs from its exact attributed postimage')
    return change


def restore_before_row(row, root=ROOT):
    if not row.get(TAG):
        return deepcopy(row)
    return deepcopy(_checked_row_record(row, root)['original_row'])


def lexical_segments(row, root=ROOT):
    if not row.get(TAG):
        raise ValueError('Editorial lexical projection has no authority')
    change = _checked_row_record(row, root)
    _, runs = prior._projection(row['text'], prior._flatten(row['text'], change['excluded_spans']))
    if row.get('analysis_text') != ' '.join(runs):
        raise ValueError('Editorial lexical projection changed')
    return runs


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        if b'"'+TAG.encode()+b'"' in (root/CORPUS).read_bytes():
            raise ValueError('Editorial metadata has no frozen authority')
        return None
    before, after, aliases, audit = _saved(root)
    current = (root/CORPUS).read_bytes()
    if current not in {before, after} or (root/ALIASES).read_bytes() != aliases:
        raise ValueError('Editorial corpus or aliases changed outside its recorded admission')
    if current == before:
        return None
    return {'audit': {'path': AUDIT.as_posix(), 'sha256': sha((root/AUDIT).read_bytes())},
        'source_review': deepcopy(audit['source_review']), 'source': deepcopy(audit['source']),
        'counts': deepcopy(audit['counts']),
        'qualification': 'Editorial substitutions are distinct from scan verification. Original scan uncertainties remain in the frozen source review.'}


def check(root=ROOT, *, source_html=None):
    root = Path(root)
    if not (root/AUDIT).exists():
        return active_metadata(root)
    files, audit = build(root, source_html=source_html)
    before, after, aliases, _ = _saved(root)
    current = (root/CORPUS).read_bytes()
    if current not in {before, after} or (root/ALIASES).read_bytes() != aliases:
        raise ValueError('Editorial corpus or aliases changed outside its recorded admission')
    if any((root/path).read_bytes() != raw for path, raw in files.items() if path != CORPUS):
        raise ValueError('Editorial substitution does not reproduce from its attributed source')
    return None if current == before else audit


def _recorded_tokens(authored):
    """Check the archived Greek witness pieces, without claiming a fresh HTML check."""
    values = {}
    for record in authored['records']:
        for reading in record.get('readings', []):
            for token in reading['tokens']:
                text, refs = token['text'], token['refs']
                if (not isinstance(text, str) or not edition.WORD.fullmatch(text.rstrip(END_MARKS))
                        or not isinstance(refs, list) or not refs):
                    raise ValueError('Recorded editorial witness is not Greek base text with exact references')
                for ref in refs:
                    if (set(ref) != {'html_line', 'html_column', 'unit_index', 'codex', 'bekker', 'start', 'end'}
                            or any(type(ref[k]) is not int for k in ('html_line','html_column','unit_index','start','end'))
                            or ref['html_line'] < 1 or min(ref['html_column'], ref['unit_index'], ref['start']) < 0
                            or ref['end'] <= ref['start'] or not isinstance(ref['codex'], str)
                            or not isinstance(ref['bekker'], str)):
                        raise ValueError('Recorded editorial HTML-node reference is malformed')
                lengths = {len(text), len(_nfc(text)), len(unicodedata.normalize('NFD', text))}
                positions = [(r['unit_index'], r['start'], r['end']) for r in refs]
                if sum(r['end']-r['start'] for r in refs) not in lengths or positions != sorted(set(positions)):
                    raise ValueError('Recorded editorial token does not account for its complete references')
                key = sha(campaign.canonical(refs))
                if key in values and values[key] != token:
                    raise ValueError('Recorded editorial witnesses disagree at one exact source token')
                values[key] = deepcopy(token)
    ordered = sorted(values.items(), key=lambda item: [(r['unit_index'],r['start'],r['end']) for r in item[1]['refs']])
    return {key: (i, token) for i, (key, token) in enumerate(ordered)}


def check_literal(root=ROOT):
    """Replay recorded witness pieces and all public pins; do not reopen source HTML."""
    root = Path(root)
    if not (root/AUDIT).exists():
        return active_metadata(root)
    before, after, aliases, audit = _saved(root)
    if sha(before) != BASELINE_SHA256 or sha(aliases) != ALIASES_SHA256:
        raise ValueError('Editorial archive has an unknown predecessor')
    for name, digest in audit['recipe_sha256'].items():
        if sha((root/'scripts'/name).read_bytes()) != digest:
            raise ValueError('Editorial recipe changed')
    if set(audit['recipe_sha256']) != set(RECIPE_NAMES):
        raise ValueError('Editorial recipe accounting changed')
    inputs = {path: (root/path).read_bytes() for path in (*INPUT_SHA256, SOURCE_REVIEW)}
    if (audit['input_pins'] != {p.as_posix():sha(raw) for p,raw in inputs.items()}
            or any(sha(inputs[p]) != digest for p,digest in INPUT_SHA256.items())):
        raise ValueError('Editorial public input pins changed')
    authored = json.loads(inputs[SOURCE_REVIEW])
    for path, digest in authored['input_pins'].items():
        raw = before if path == CORPUS.as_posix() else (root/path).read_bytes()
        if sha(raw) != digest:
            raise ValueError('Editorial preparation input changed')
    for name, digest in authored['recipe_sha256'].items():
        if sha((root/'scripts'/name).read_bytes()) != digest:
            raise ValueError('Editorial preparation recipe changed')
    if authored['counts'] != dict(Counter(d['decision'] for d in authored['records'])):
        raise ValueError('Editorial preparation decision accounting changed')
    review = compile_review(before, json.loads(gzip.decompress(inputs[COMPILED])),
        json.loads(inputs[prior.REVIEW]), json.loads(inputs[admission.REVIEW]), authored, None,
        _recorded_tokens=_recorded_tokens(authored))
    if compress_gzip(encode(review)) != (root/REVIEW).read_bytes():
        raise ValueError('Editorial recorded readings do not reproduce their compiled authority')
    if (root/CORPUS).read_bytes() not in {before, after} or (root/ALIASES).read_bytes() != aliases:
        raise ValueError('Editorial corpus or aliases changed outside its recorded admission')
    if restore_before_bytes(after, root) != before:
        raise ValueError('Editorial literal undo does not reproduce its exact preimage')
    return None if (root/CORPUS).read_bytes() == before else audit


def apply(root=ROOT, *, source_html=None):
    root = Path(root); files, audit = build(root, source_html=source_html)
    if sha((root/CORPUS).read_bytes()) not in {audit['input_corpus_sha256'], audit['output_corpus_sha256']}:
        raise ValueError('Editorial application requires its exact predecessor')
    if any((root/path).exists() and (root/path).read_bytes() != raw for path, raw in files.items() if path != CORPUS):
        raise ValueError('Refusing to replace an immutable editorial admission artifact')
    for path, raw in files.items():
        if path != CORPUS:
            (root/path).parent.mkdir(parents=True, exist_ok=True); (root/path).write_bytes(raw)
    (root/CORPUS).write_bytes(files[CORPUS])
    return audit


def undo(root=ROOT):
    root = Path(root); before, after, aliases, _ = _saved(root)
    if (root/CORPUS).read_bytes() not in {before, after} or (root/ALIASES).read_bytes() != aliases:
        raise ValueError('Undo later layers before the editorial admission')
    (root/CORPUS).write_bytes(before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true'); mode.add_argument('--undo', action='store_true')
    mode.add_argument('--check', action='store_true'); parser.add_argument('--source-html', type=Path)
    mode.add_argument('--check-literal', action='store_true', help='Replay public recorded witnesses without reopening the comparison HTML')
    args = parser.parse_args()
    if args.undo:
        undo(); return
    audit = (apply(source_html=args.source_html) if args.apply else check_literal() if args.check_literal
             else check(source_html=args.source_html) if args.check else build(source_html=args.source_html)[1])
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == '__main__':
    main()
