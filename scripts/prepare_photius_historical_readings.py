#!/usr/bin/env python3
"""Compile occurrence-level scan observations into a pinned reading authority.

The source tables contain completed visual observations, not automatic spelling
rules. Digital text corroborates a bounded observation; it never supplies a
whole historical row. Unreviewed words and passage identities stay unchanged.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path('data/corpus/photius.bibliotheca.jsonl')
ARCHIVE = Path('data/corpus_changes/photius-bekker-historical-readings')
OUT = Path('data/ingest_reviews/photius-bekker-historical-readings.json')
LIBRARY = Path('data/corpus_changes/photius-bekker-readings/source-library.json.gz')
SCAN = Path('data/corpus_changes/photius-bekker-readings/source-scan.pdf')
BASE_SHA = '35573755011c78c4d4b050fe3998008783c392a787316ce1a4aab8016c3776d3'
LIBRARY_SHA = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
SCAN_SHA = 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'
TABLES = ('photius_historical_observations_early', 'photius_historical_observations_later')
REVIEWED_AT = '2026-10-19T00:36:00Z'
DIAGNOSTIC = Path('data/evaluation/ocr-fresh/photius-historical-reading-diagnostics-qwen38-mlx.jsonl')
DIAGNOSTIC_REQUEST = Path('data/ocr_requests/photius-historical-reading-diagnostics.json')
DIAGNOSTIC_SHA = '94e786f11798760bab01af7ab71dfa7c0c913017064a866da8f0139f161318b6'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def exact_span(text, needle, occurrence=None):
    if not isinstance(needle, str) or not needle:
        raise ValueError('An occurrence requires nonempty exact source text')
    starts = [m.start() for m in re.finditer(re.escape(needle), text)]
    if (occurrence is None and len(starts) != 1) or (occurrence is not None and
            (type(occurrence) is not int or not 0 <= occurrence < len(starts))):
        raise ValueError(f'Occurrence is absent or ambiguous: {needle!r}')
    start = starts[0 if occurrence is None else occurrence]
    return start, start + len(needle)


def compile_review(before, library_raw, scan_raw, observations, *, table_pins=None,
                   diagnostic_raw=None, diagnostic_request_raw=None):
    """Resolve exact offsets and verify source identity before producing changes."""
    if sha(before) != BASE_SHA or sha(library_raw) != LIBRARY_SHA or sha(scan_raw) != SCAN_SHA:
        raise ValueError('Historical reading review requires the exact released sources')
    import pymupdf
    rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
    sections = {s['id']: s for s in json.loads(gzip.decompress(library_raw))['sections']}
    source = pymupdf.open(stream=scan_raw, filetype='pdf')
    records, images, occupied = [], {}, {}
    for observation in observations:
        item = dict(observation)
        locus, page = item['locus'], item['page']
        old = rows[locus]
        if (type(page) is not int or not re.fullmatch(
                rf'helladius_chrestomathia_photius_bekker_v2_{page:04d}[.]\d+', locus)
                or old.get('ocr_consensus') or old.get('editorial_layer') or 'analysis_text' in old):
            raise ValueError('Observation requires an ordinary retained historical passage')
        if page in {169, 170} and not item.get('diagnostic_id'):
            raise ValueError('The digital counterpart repeats another source page')
        original, corrected = item['original_text'], item['corrected_text']
        observed = corrected
        if original == corrected or not corrected or not item.get('evidence'):
            raise ValueError('A correction requires a changed reading and completed scan evidence')
        start, end = exact_span(old['text'], original, item.get('occurrence'))
        if any(start < high and low < end for low, high in occupied.setdefault(locus, [])):
            raise ValueError('Reviewed corrections overlap in their original passage')
        occupied[locus].append((start, end))
        counterpart = None
        if item.get('diagnostic_id'):
            counterpart = diagnostic_counterpart(item, diagnostic_raw, diagnostic_request_raw, scan_raw)
            counterpart_field = 'scan_prediction_counterpart'
        else:
            section_id = f'tlg4040-tlg001-local002-s{page + 277}'
            full = '\n'.join(b['text'] for b in sections[section_id]['blocks'])
            digital_text = item.get('digital_text', corrected)
            if digital_text != corrected:
                joined = re.sub(r'(?<=[Ͱ-Ͽἀ-῿])[-‐](?=[Ͱ-Ͽἀ-῿])', '', corrected)
                if joined != digital_text:
                    raise ValueError('Differing source readings must remain held variants, not a scalar correction')
                corrected = joined
            low, high = exact_span(full, digital_text, item.get('digital_occurrence'))
            counterpart = {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA,
                'section': section_id, 'start': low, 'end': high, 'original_text': digital_text,
                'context_start': max(0, low-100), 'context_end': min(len(full), high+100),
                'context': full[max(0, low-100):min(len(full), high+100)]}
            counterpart_field = 'digital_counterpart'
        box = item['source_region']
        if (len(box) != 4 or not all(type(v) in (int, float) for v in box) or
                not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1):
            raise ValueError('Scan evidence requires a bounded physical source region')
        image_key = (page, tuple(box))
        if image_key not in images:
            sheet = source[page - 1]
            rect = pymupdf.Rect(box[0]*sheet.rect.width, box[1]*sheet.rect.height,
                                box[2]*sheet.rect.width, box[3]*sheet.rect.height)
            scale = 3600 / max(rect.width, rect.height)
            images[image_key] = sha(sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale),
                                                    clip=rect, alpha=False).tobytes('png'))
        records.append({'locus': locus, 'original_row_sha256': row_sha(old),
            'start': start, 'end': end, 'original_text': original, 'corrected_text': corrected,
            'source': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA, 'scan_page': page,
                'printed_page': page + 265, 'region': box, 'max_side': 3600,
                'image_sha256': images[image_key], 'evidence': item['evidence'],
                'observed_text': observed,
                **({'transcription_convention': 'Join the source-confirmed internal printed line-end hyphen. The literal divided scan reading remains here; no column-boundary completion is supplied.'}
                   if observed != corrected else {})},
            counterpart_field: counterpart,
            'reviewed_at': REVIEWED_AT,
            'policy': 'The occurrence was read on the pinned scan and corroborated by an exact bounded independent reading. The rejected historical reading remains in the reversible audit. This does not certify other text in the passage.'})
    source.close()
    if not records:
        raise ValueError('A completed authority requires occurrence-level observations')
    records.sort(key=lambda r: (r['locus'], r['start']))
    return {'schema_version': 1, 'work': 'photius.bibliotheca',
        'operation': 'source-reviewed-historical-occurrence-corrections',
        'input_corpus_sha256': BASE_SHA, 'reviewed_at': REVIEWED_AT,
        'source_table_pins': table_pins or [], 'records': records,
        'qualification': 'Only these exact occurrences are source reviewed. Historical passages remain outside the full word-consensus assessment; automated collation candidates are not accepted corrections.'}


def build(root=ROOT):
    root = Path(root)
    frozen = root / ARCHIVE / 'before-corpus.jsonl.gz'
    before = gzip.decompress(frozen.read_bytes()) if frozen.exists() else (root / CORPUS).read_bytes()
    observations, pins, reconstructions, held = [], [], [], []
    for name in TABLES:
        module = importlib.import_module(name)
        path = Path('scripts') / (name + '.py')
        observations.extend(module.observations())
        if hasattr(module, 'scan_only_observations'):
            observations.extend(module.scan_only_observations())
        if hasattr(module, 'epilogue'):
            reconstructions.append(module.epilogue())
        for function in ('unresolved', 'unapplied_source_observations'):
            if hasattr(module, function):
                held.extend(getattr(module, function)())
        pins.append({'path': path.as_posix(), 'sha256': sha((root / path).read_bytes())})
    library_raw, scan_raw = (root / LIBRARY).read_bytes(), (root / SCAN).read_bytes()
    result = compile_review(before, library_raw, scan_raw, observations, table_pins=pins,
        diagnostic_raw=(root / DIAGNOSTIC).read_bytes(),
        diagnostic_request_raw=(root / DIAGNOSTIC_REQUEST).read_bytes())
    if reconstructions:
        result['reconstructions'] = [compile_reconstruction(before, library_raw, scan_raw, item)
                                     for item in reconstructions]
    if held:
        # These are retained observations, not another list of outstanding
        # work. They confer no authority to change the current scalar text.
        original_rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
        result['held_source_observations'] = [{**item,
            'original_row_sha256': row_sha(original_rows[item['locus']]),
            'source_pdf': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA},
            'admission_authorized': False, 'reviewed_at': REVIEWED_AT} for item in held]
    return result


def diagnostic_counterpart(item, raw, request_raw, scan_raw):
    """Bind an exceptional-page observation to one exact raw source-only span."""
    import pymupdf
    if raw is None or sha(raw) != DIAGNOSTIC_SHA or request_raw is None:
        raise ValueError('A scan-only occurrence requires its exact retained prediction file')
    records = list(map(json.loads, raw.splitlines())); metadata = records[0]['_meta']
    request = json.loads(request_raw)
    if (metadata['model'] != 'mlx-community/Qwen3.8-27B-8bit'
            or metadata['revision'] != '815b83c0df8ffd1d1b5244cf75fd6ef14fca9ef9'
            or metadata['manifest_sha256'] != sha(request_raw) or metadata['temperature'] != 0
            or metadata['backend'] != 'mlx' or metadata['max_tokens'] != 2400
            or metadata['runner_sha256'] != '061455bce85cb1b770bbb68a2819b06e4da9e637856a05d402559c861154c5e4'
            or metadata['runtime'] != {'mlx': '0.31.2', 'mlx-vlm': '0.6.3', 'transformers': '5.12.1'}):
        raise ValueError('Scan-only prediction identity, source request, or runtime changed')
    prediction, = [r for r in records[1:] if r['id'] == item['diagnostic_id']]
    job, = [j for j in request['pages'] if j['id'] == item['diagnostic_id']]
    source = request['sources'][job['source']]
    if (prediction['finish_reason'] != 'stop' or job['scan_page'] != item['page']
            or prediction['scan_page'] != item['page'] or prediction['region'] != job['region']
            or source['sha256'] != SCAN_SHA):
        raise ValueError('Scan-only prediction did not finish on the exact reviewed source region')
    prompt = metadata['prompt'] + ' ' + job['prompt_suffix']
    if prediction['prompt_sha256'] != sha(prompt.encode()):
        raise ValueError('Scan-only source prompt changed')
    document = pymupdf.open(stream=scan_raw, filetype='pdf'); sheet = document[item['page']-1]
    box = job['region']; rect = pymupdf.Rect(box[0]*sheet.rect.width, box[1]*sheet.rect.height,
        box[2]*sheet.rect.width, box[3]*sheet.rect.height); scale = job['max_side']/max(rect.width, rect.height)
    image_sha = sha(sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False).tobytes('png'))
    document.close()
    if image_sha != prediction['image_sha256']:
        raise ValueError('Scan-only prediction image differs from its physical source crop')
    text = item.get('diagnostic_text', item['corrected_text'])
    if text != item['corrected_text']:
        raise ValueError('A differing diagnostic reading cannot corroborate a scalar correction')
    low, high = exact_span(prediction['raw_prediction'], text, item.get('diagnostic_occurrence'))
    return {'path': DIAGNOSTIC.as_posix(), 'sha256': DIAGNOSTIC_SHA,
        'id': prediction['id'], 'start': low, 'end': high, 'original_text': text,
        'full_raw_prediction': prediction['raw_prediction'], 'model': metadata['model'],
        'revision': metadata['revision'], 'runtime': metadata['runtime'], 'image_sha256': image_sha,
        'request': {'path': DIAGNOSTIC_REQUEST.as_posix(), 'sha256': sha(request_raw)},
        'qualification': 'Only this exact scan-confirmed span corroborates a correction. Other diagnostic output is not an admitted reading or an additional vote.'}


def compile_reconstruction(before, library_raw, scan_raw, item):
    """Pin an independently read source region whose old row order is broken."""
    import pymupdf
    if sha(before) != BASE_SHA or sha(library_raw) != LIBRARY_SHA or sha(scan_raw) != SCAN_SHA:
        raise ValueError('Source reconstruction requires the exact historical source stage')
    rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
    page = item['page']
    if (page != 280 or not item.get('evidence') or not item.get('transcription_convention')
            or not item.get('scan_text') or not item.get('digital_text')
            or item['locus'] in rows or len(set(item['replaces'])) != len(item['replaces'])):
        raise ValueError('Source reconstruction lacks a unique reviewed physical region')
    expected = {f'helladius_chrestomathia_photius_bekker_v2_0280.{n}' for n in (*range(13, 24), 26, 27)}
    if (set(item['replaces']) != expected or item['insert_after'] !=
            'helladius_chrestomathia_photius_bekker_v2_0280.25'):
        raise ValueError('The reviewed epilogue requires all detached old halves and its source boundary')
    old = [rows[locus] for locus in item['replaces']]
    if any(row.get('ocr_consensus') or row.get('editorial_layer') for row in old):
        raise ValueError('Source reconstruction cannot discard an existing reviewed network')
    sections = json.loads(gzip.decompress(library_raw))['sections']
    section = next(s for s in sections if s['id'] == 'tlg4040-tlg001-local002-s557')
    full = '\n'.join(b['text'] for b in section['blocks'])
    low, high = exact_span(full, item['digital_text'])
    box = item['source_region']
    if len(box) != 4 or not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1:
        raise ValueError('Epilogue reconstruction requires the complete bounded source image')
    document = pymupdf.open(stream=scan_raw, filetype='pdf'); sheet = document[page-1]
    rect = pymupdf.Rect(box[0]*sheet.rect.width, box[1]*sheet.rect.height,
                        box[2]*sheet.rect.width, box[3]*sheet.rect.height)
    scale = 3600/max(rect.width, rect.height)
    image_sha = sha(sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False).tobytes('png'))
    document.close()
    return {**item, 'original_rows': old, 'original_row_sha256': {r['locus']: row_sha(r) for r in old},
        'source': {'path': SCAN.as_posix(), 'sha256': SCAN_SHA, 'scan_page': page,
            'printed_page': 545, 'region': box, 'max_side': 3600, 'image_sha256': image_sha,
            'evidence': item['evidence']},
        'digital_counterpart': {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA,
            'section': section['id'], 'start': low, 'end': high, 'original_text': item['digital_text']},
        'reviewed_at': REVIEWED_AT,
        'qualification': 'The two independent readings retain all differing words and marks. Original detached halves are nonvoting history, not omission votes. Historical citations resolve to this complete reconstructed physical region.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true')
    action.add_argument('--check', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    review = build(args.root); raw = encode(review); path = args.root / OUT
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    elif args.check and path.read_bytes() != raw:
        parser.exit(1, 'Historical occurrence authority changed\n')
    print(json.dumps({'corrections': len(review['records']), 'rows': len({r['locus'] for r in review['records']}), 'sha256': sha(raw)}))


if __name__ == '__main__':
    main()
