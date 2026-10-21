#!/usr/bin/env python3
"""Replay and reverse exact source-confirmed historical OCR occurrences."""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import json
from pathlib import Path

from prepare_photius_historical_readings import (
    ROOT, CORPUS, ARCHIVE, OUT as REVIEW, SCAN, LIBRARY, BASE_SHA,
    SCAN_SHA, LIBRARY_SHA, REVIEWED_AT, DIAGNOSTIC, DIAGNOSTIC_SHA, encode, sha, row_sha)

AUDIT = ARCHIVE / 'changes.json'
BEFORE = ARCHIVE / 'before-corpus.jsonl.gz'
RECORDS = ARCHIVE / 'records.jsonl.gz'
FROZEN_REVIEW = ARCHIVE / 'source-review.json'
NETWORKS = ARCHIVE / 'networks.json.gz'
ALIASES = Path('data/passage_aliases.json')
BEFORE_ALIASES = ARCHIVE / 'before-passage-aliases.json.gz'
DIAGNOSTIC_FILES = (
    Path('data/ocr_requests/photius-historical-pilot.json'),
    Path('data/ocr_requests/photius-historical-reading-diagnostics.json'),
    Path('data/evaluation/ocr-fresh/photius-historical-pilot-qwen38-mlx.jsonl'),
    DIAGNOSTIC,
)
SCHEMA = 'photius-historical-occurrence-v1'


def plan(before, review_raw):
    """Pure exact-span replay; all untargeted JSONL bytes remain unchanged."""
    review = json.loads(review_raw)
    if (sha(before) != BASE_SHA or review.get('input_corpus_sha256') != BASE_SHA or
            review.get('schema_version') != 1 or review.get('work') != 'photius.bibliotheca'
            or not review.get('reviewed_at') or not review.get('records')):
        raise ValueError('Historical correction authority or original corpus changed')
    reference = {'path': FROZEN_REVIEW.as_posix(), 'sha256': sha(review_raw)}
    grouped = {}
    for record in review['records']:
        grouped.setdefault(record['locus'], []).append(record)
    parts, changes, pages = [], [], set()
    original_rows = {row['locus']: row for row in map(json.loads, before.splitlines())}
    removed, insertions = set(), {}
    for group in review.get('reconstructions', []):
        new, full = reconstruction(group, original_rows, reference)
        if (set(group['replaces']) & (set(grouped) | removed) or new['locus'] in original_rows
                or group['insert_after'] not in original_rows or group['insert_after'] in removed
                or group['insert_after'] in group['replaces'] or group['insert_after'] in insertions):
            raise ValueError('A reconstructed source region overlaps another correction or lacks its insertion boundary')
        removed.update(group['replaces']); insertions[group['insert_after']] = new
        pages.add(group['page'])
        changes.append({'kind': 'reconstructed-source-region', 'locus': new['locus'],
            'original_rows': group['original_rows'], 'corrected_row': new,
            'original_text': '\n'.join(r['text'] for r in group['original_rows']),
            'corrected_text': new['text'], 'corrected_row_sha256': row_sha(new),
            'source_review': reference, 'source_evidence': group, 'full_network': full,
            'recorded_at': REVIEWED_AT})
    for line in before.splitlines(keepends=True):
        old = json.loads(line); locus = old['locus']
        if locus in removed:
            continue
        if locus not in grouped:
            parts.append(line)
            if locus in insertions:
                parts.append((json.dumps(insertions[locus], ensure_ascii=False) + '\n').encode())
            continue
        observations = sorted(grouped.pop(locus), key=lambda r: r['start'])
        if old.get('ocr_consensus') or old.get('editorial_layer') or old.get('historical_reading_repair') or 'analysis_text' in old:
            raise ValueError('Historical occurrence repairs cannot overwrite another lexical projection')
        cursor, corrected = 0, []
        for item in observations:
            low, high = item['start'], item['end']
            counterpart = item.get('digital_counterpart') or item.get('scan_prediction_counterpart')
            source = item['source']
            expected_sha, expected_path = ((LIBRARY_SHA, LIBRARY.as_posix()) if 'digital_counterpart' in item
                                           else (DIAGNOSTIC_SHA, DIAGNOSTIC.as_posix()))
            if (item['original_row_sha256'] != row_sha(old) or type(low) is not int or type(high) is not int
                    or not cursor <= low < high <= len(old['text'])
                    or old['text'][low:high] != item['original_text']
                    or not item['corrected_text'] or item['corrected_text'] == item['original_text']
                    or counterpart['original_text'] != item['corrected_text']
                    or counterpart['sha256'] != expected_sha or counterpart['path'] != expected_path
                    or source['sha256'] != SCAN_SHA or source['path'] != SCAN.as_posix()
                    or not source.get('evidence') or not item.get('reviewed_at')):
                raise ValueError('A historical correction lacks its exact original span or paired source evidence')
            corrected.extend((old['text'][cursor:low], item['corrected_text'])); cursor = high
            pages.add(source['scan_page'])
        corrected.append(old['text'][cursor:])
        new = deepcopy(old)
        new.update(text=''.join(corrected), edition='bekker1825-reviewed-historical-readings',
                   license='CC-BY-SA-4.0', language='grc')
        new['historical_reading_repair'] = {'schema': SCHEMA, 'source_review': reference,
            'original_text_sha256': sha(old['text'].encode()), 'reviewed_occurrences': len(observations),
            'qualification': 'Partial source-reviewed occurrences; other historical text remains unassessed.'}
        changes.append({'locus': locus, 'original_row': old, 'corrected_row': new,
            'original_text': old['text'], 'corrected_text': new['text'],
            'original_row_sha256': row_sha(old), 'corrected_row_sha256': row_sha(new),
            'corrections': observations, 'source_review': reference, 'recorded_at': REVIEWED_AT})
        parts.append((json.dumps(new, ensure_ascii=False) + '\n').encode())
        if locus in insertions:
            parts.append((json.dumps(insertions[locus], ensure_ascii=False) + '\n').encode())
    if grouped:
        raise ValueError('Historical authority invents a passage identity')
    return b''.join(parts), changes, {'corrected_rows': sum('corrections' in c for c in changes),
        'corrected_occurrences': sum(len(c.get('corrections', [])) for c in changes),
        'reconstructed_regions': len(insertions), 'replaced_fragment_rows': len(removed),
        'primary_rows_before': len(original_rows), 'primary_rows_after': len(original_rows)-len(removed)+len(insertions),
        'scan_pages': sorted(pages), 'fully_assessed_rows': 0,
        'source_family': 'source-library-local002', 'source_scan_sha256': SCAN_SHA}


def reconstruction(group, rows, reference):
    """Vote the source region separately from its rejected historical halves."""
    from ocr_consensus import merge_witnesses, compact_corpus_consensus, restore_corpus_consensus
    originals = group['original_rows']
    if (not originals or {r['locus'] for r in originals} != set(group['replaces']) or
            any(rows.get(r['locus']) != r or row_sha(r) != group['original_row_sha256'][r['locus']] for r in originals)
            or group['digital_counterpart']['original_text'] != group['digital_text']
            or group['digital_counterpart']['sha256'] != LIBRARY_SHA or group['source']['sha256'] != SCAN_SHA
            or not group.get('evidence') or not group.get('transcription_convention')):
        raise ValueError('Reconstructed region differs from its original halves or reviewed sources')
    full = merge_witnesses([
        {'id': 'direct-scan-reading', 'vote_group': 'direct-scan-reading', 'text': group['scan_text'],
         'artifact_sha256': sha(group['scan_text'].encode()), 'source_review': reference,
         'source': group['source'], 'license': 'CC-BY-4.0', 'transcription_convention': group['transcription_convention']},
        {'id': 'source-library-local002', 'vote_group': 'source-library-local002', 'text': group['digital_text'],
         'artifact_sha256': sha(encode(group['digital_counterpart'])),
         'source_file_sha256': LIBRARY_SHA, 'source_section': group['digital_counterpart']['section'],
         'source_window': group['digital_counterpart'], 'license': 'CC-BY-SA-4.0'}])
    compact = compact_corpus_consensus(full, {'path': NETWORKS.as_posix(), 'key': group['locus']})
    restore_corpus_consensus(compact, full)
    new = {'urn': 'photius.bibliotheca', 'cts': originals[0].get('cts', 'urn:cts:greekLit:tlg4040.tlg001'),
        'locus': group['locus'], 'edition': 'bekker1825-reviewed-historical-readings', 'source': 'ocr',
        'license': 'CC-BY-SA-4.0', 'language': 'grc', **compact,
        'physical_refs': {'scan_page': group['page'], 'printed_page': group['page']+265,
            'edition': 'Bekker 1825', 'scan_sha256': SCAN_SHA, 'region': group['source_region']},
        'historical_source_reconstruction': {'schema': SCHEMA, 'source_review': reference,
            'original_loci': group['replaces'], 'qualification': group['qualification']}}
    return new, full


def build(root=ROOT, *, require_current=True):
    root = Path(root)
    saved = json.loads((root / AUDIT).read_bytes()) if (root / AUDIT).exists() else None
    before = gzip.decompress((root / BEFORE).read_bytes()) if saved else (root / CORPUS).read_bytes()
    review_raw = (root / FROZEN_REVIEW).read_bytes() if saved else (root / REVIEW).read_bytes()
    if require_current:
        from prepare_photius_historical_readings import build as prepare
        if encode(prepare(root)) != review_raw or (root / REVIEW).read_bytes() != review_raw:
            raise ValueError('Historical occurrence authority no longer reproduces')
    if sha(before) != BASE_SHA:
        raise ValueError('Historical corrections require the exact preceding release')
    after, changes, counts = plan(before, review_raw)
    records = b''.join((json.dumps(c, ensure_ascii=False) + '\n').encode() for c in changes)
    outputs = {CORPUS: after, RECORDS: gzip.compress(records, mtime=0)}
    frozen = {BEFORE: gzip.compress(before, mtime=0), FROZEN_REVIEW: review_raw}
    diagnostic_pins = []
    # Fixture authorities and ordinary occurrence-only consumers do not need
    # unrelated diagnostic attempts. The published authority includes the two
    # exact scan-only observations and freezes every attempted prediction.
    has_diagnostics = any('scan_prediction_counterpart' in r for r in json.loads(review_raw)['records'])
    if has_diagnostics:
        if saved:
            for pin in saved['diagnostic_inputs']:
                path, archive = Path(pin['path']), Path(pin['frozen_path'])
                if (not path.as_posix().startswith('data/') or '..' in path.parts
                        or archive != ARCHIVE / 'diagnostics' / (pin['sha256'] + ''.join(path.suffixes))):
                    raise ValueError('Unexpected historical diagnostic archive path')
                raw = (root / archive).read_bytes()
                if sha(raw) != pin['sha256'] or (require_current and (root / path).read_bytes() != raw):
                    raise ValueError('An original or frozen historical diagnostic changed')
                frozen[archive] = raw; diagnostic_pins.append(pin)
        else:
            paths = set(DIAGNOSTIC_FILES)
            for path in DIAGNOSTIC_FILES:
                if path.suffix == '.jsonl':
                    meta = json.loads((root / path).read_bytes().splitlines()[0])['_meta']
                    archive = path.parent / meta['manifest_archive']
                    if '..' in archive.parts or not archive.as_posix().startswith('data/evaluation/ocr-fresh/manifests/'):
                        raise ValueError('Unexpected diagnostic request reference')
                    paths.add(archive)
            for path in sorted(paths):
                raw = (root / path).read_bytes()
                archive = ARCHIVE / 'diagnostics' / (sha(raw) + ''.join(path.suffixes))
                frozen[archive] = raw
                diagnostic_pins.append({'path': path.as_posix(), 'sha256': sha(raw), 'frozen_path': archive.as_posix()})
        if require_current:
            from prepare_photius_historical_diagnostics import build as prepare_diagnostics
            if any((root / p).read_bytes() != raw for p, raw in prepare_diagnostics(root).items()):
                raise ValueError('Historical diagnostic requests no longer reproduce')
    reconstructed = [c for c in changes if c.get('kind') == 'reconstructed-source-region']
    if reconstructed:
        alias_raw = gzip.decompress((root / BEFORE_ALIASES).read_bytes()) if saved else (root / ALIASES).read_bytes()
        aliases = json.loads(alias_raw)
        own = aliases.setdefault('aliases', {}).setdefault('photius.bibliotheca', {})
        for change in reconstructed:
            for old in change['original_rows']:
                target = {'path': CORPUS.as_posix(), 'slug': 'photius.bibliotheca', 'locus': change['locus']}
                if old['locus'] in own and own[old['locus']] != target:
                    raise ValueError('Historical source citation already points elsewhere')
                own[old['locus']] = target
        outputs[ALIASES] = encode(aliases)
        outputs[NETWORKS] = gzip.compress(encode({c['locus']: c['full_network'] for c in reconstructed}), mtime=0)
        frozen[BEFORE_ALIASES] = gzip.compress(alias_raw, mtime=0)
    # The scan and digital source already have immutable public copies from the
    # preceding layer. Reference their exact bytes without duplicating the PDF.
    for path, expected in ((SCAN, SCAN_SHA), (LIBRARY, LIBRARY_SHA)):
        if require_current and sha((root / path).read_bytes()) != expected:
            raise ValueError('A historical correction source changed or was invalidated')
    audit = {'schema_version': 1, 'work': 'photius.bibliotheca', 'schema': SCHEMA,
        'recorded_at': REVIEWED_AT, 'input_corpus_sha256': BASE_SHA,
        'source_review': {'path': FROZEN_REVIEW.as_posix(), 'sha256': sha(review_raw)},
        'sources': [{'path': SCAN.as_posix(), 'sha256': SCAN_SHA},
                    {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA}]
                   + ([{'path': DIAGNOSTIC.as_posix(), 'sha256': DIAGNOSTIC_SHA}] if has_diagnostics else []),
        'diagnostic_inputs': diagnostic_pins,
        'counts': counts, 'outputs': {p.as_posix(): sha(raw) for p, raw in outputs.items()},
        'frozen_inputs': {p.as_posix(): sha(raw) for p, raw in frozen.items()},
        'qualification': 'Exact occurrence corrections, not a full historical word vote or accuracy estimate.'}
    return {**outputs, **frozen, AUDIT: encode(audit)}, audit


def check(root=ROOT):
    root = Path(root); artifacts, audit = build(root)
    from repair_photius_historical_batches import restore_before_bytes as restore_batches
    if any(not (root / p).exists() or
           (restore_batches((root / p).read_bytes(), root) if p == CORPUS else (root / p).read_bytes()) != raw
           for p, raw in artifacts.items()):
        raise ValueError('Historical occurrence outputs differ from exact replay')
    return audit


def restore_before_bytes(raw, root=ROOT):
    root = Path(root)
    from repair_photius_historical_batches import restore_before_bytes as restore_batches
    raw = restore_batches(raw, root)
    if not (root / AUDIT).exists() or sha(raw) == BASE_SHA:
        return raw
    artifacts, _ = build(root)
    if raw != artifacts[CORPUS] or any((root / p).read_bytes() != value
            for p, value in artifacts.items() if p != CORPUS):
        raise ValueError('Photius changed outside its historical occurrence audit')
    return gzip.decompress(artifacts[BEFORE])


def restore_before_alias_bytes(raw, root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists() or not (root / BEFORE_ALIASES).exists():
        return raw
    before = gzip.decompress((root / BEFORE_ALIASES).read_bytes())
    if raw == before:
        return raw
    artifacts, _ = build(root)
    if raw != artifacts.get(ALIASES) or any((root / p).read_bytes() != value
            for p, value in artifacts.items() if p != CORPUS):
        raise ValueError('Historical passage aliases changed outside their source reconstruction')
    return before


@lru_cache(maxsize=2)
def _projection_pins(raw):
    return {r['locus']: r['corrected_row_sha256'] for r in map(json.loads, gzip.decompress(raw).splitlines())}


def validate_projection(row, root=ROOT):
    if row.get('complete_source_review'):
        from repair_photius_complete_review import restore_before_row
        row = restore_before_row(row, root)
    if row.get('historical_reading_batches'):
        from repair_photius_historical_batches import restore_before_row
        row = restore_before_row(row, root)
    root = Path(root); audit = json.loads((root / AUDIT).read_bytes()); raw = (root / RECORDS).read_bytes()
    if (audit.get('schema') != SCHEMA or sha(raw) != audit['outputs'][RECORDS.as_posix()]
            or _projection_pins(raw).get(row.get('locus')) != row_sha(row)):
        raise ValueError('Historical reading differs from its exact occurrence audit')


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root / AUDIT).exists() or sha((root / CORPUS).read_bytes()) == BASE_SHA:
        return None
    audit = check(root)
    groups = json.loads((root / FROZEN_REVIEW).read_bytes()).get('reconstructions', [])
    return {'audit': {'path': AUDIT.as_posix(), 'sha256': sha((root / AUDIT).read_bytes())},
            'source_review': audit['source_review'], 'counts': audit['counts'], 'sources': audit['sources'],
            'logical_coverage_positions': {g['locus']: g['page']+277 for g in groups},
            **({'networks': {'path': NETWORKS.as_posix(), 'sha256': audit['outputs'][NETWORKS.as_posix()]}}
               if groups else {})}


def apply(root=ROOT):
    root = Path(root); artifacts, audit = build(root)
    if sha((root / CORPUS).read_bytes()) not in {BASE_SHA, sha(artifacts[CORPUS])}:
        raise ValueError('Independent Photius edits cannot enter historical occurrence repairs')
    if ALIASES in artifacts and (root / ALIASES).read_bytes() not in {
            artifacts[ALIASES], gzip.decompress(artifacts[BEFORE_ALIASES])}:
        raise ValueError('Independent historical passage alias edits cannot enter the correction')
    if any(p not in {CORPUS, ALIASES} and (root / p).exists() and (root / p).read_bytes() != raw for p, raw in artifacts.items()):
        raise ValueError('Refusing to overwrite a frozen historical correction artifact')
    for path, raw in artifacts.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True); (root / path).write_bytes(raw)
    return audit


def undo(root=ROOT):
    root = Path(root); artifacts, audit = build(root, require_current=False)
    if any((root / p).read_bytes() != raw for p, raw in artifacts.items()):
        raise ValueError('Unapply later or independent edits before reversing historical corrections')
    (root / CORPUS).write_bytes(gzip.decompress(artifacts[BEFORE]))
    if BEFORE_ALIASES in artifacts:
        (root / ALIASES).write_bytes(gzip.decompress(artifacts[BEFORE_ALIASES]))
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true'); action.add_argument('--check', action='store_true')
    action.add_argument('--undo', action='store_true'); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = (apply(args.root) if args.apply else undo(args.root) if args.undo else check(args.root)
              if args.check else build(args.root)[1])
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
