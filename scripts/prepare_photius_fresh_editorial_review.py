#!/usr/bin/env python3
"""Reproduce the exact scan-reviewed fresh Photius245 editorial boundaries."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('data/ingest_reviews/photius-bekker-fresh-editorial-spans.json')
NETWORK = Path('data/corpus_changes/photius-bekker-coverage/full-networks.json.gz')
NETWORK_SHA = 'a7f867b2c83cdec5ebd77ad04837cbcf6916289adcf2fb1c40047a69db51abe5'
MANIFEST = Path('data/corpus_changes/photius-bekker-coverage/scan-request.json')
MANIFEST_SHA = '92bb67209eaa7dcca53800c499c68b4c1a085cbb2d62f2909b27da99c0acdcd6'
RAW_SHA = '97c8b2d4157128eb359474c413d84ac1f395f6e3dfca4830e645f2a3b3b396ce'
TEXT_SHA = '771d77a317f9c5df9e876ef7eb5c88d2273bf79e212e56b11304766fbd3ff895'
SOURCE_SHA = 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(root=ROOT):
    compressed = (root / NETWORK).read_bytes()
    if sha(compressed) != NETWORK_SHA:
        raise ValueError('Original full network changed')
    network = json.loads(gzip.decompress(compressed))['245']
    witness = next(w for w in network['ocr_consensus']['witnesses'] if w.get('raw_file_sha256') == RAW_SHA)
    text = witness['text']
    raw_path = Path('data/corpus_changes/photius-bekker-coverage/witnesses') / (RAW_SHA + '.jsonl')
    raw = (root / raw_path).read_bytes()
    if sha(raw) != RAW_SHA or sha(text.encode()) != TEXT_SHA:
        raise ValueError('Reviewed original outcome changed')
    lines = raw.splitlines(); metadata = json.loads(lines[0])['_meta']
    records = [line for line in lines[1:] if json.loads(line)['id'] == 'photius-bekker-0245']
    if len(records) != 1 or json.loads(records[0])['raw_prediction'] != text:
        raise ValueError('Reviewed witness differs from exact original prediction')
    prediction = json.loads(records[0])
    manifest_raw = (root / MANIFEST).read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA or metadata['manifest_sha256'] != MANIFEST_SHA:
        raise ValueError('Reviewed source request changed')
    manifest = json.loads(manifest_raw)
    request = next(p for p in manifest['pages'] if p['id'] == prediction['id'])
    source = manifest['sources'][request['source']]
    if (request['scan_page'] != 245 or source['sha256'] != SOURCE_SHA
            or metadata['model'] != witness['model']
            or metadata['revision'] != witness['revision']):
        raise ValueError('Reviewed source page/checkpoint changed')
    header = 'ΤΑ ΠΕΡΙ ΗΡΑΚΛΕΙΔΗΝ.\n\n'
    footer = '\na. 15. τετρακισχ.'
    if not text.startswith(header) or text.count(footer) != 1:
        raise ValueError('Reviewed header/footer boundaries changed')
    start, end = len(header), text.index(footer)
    exclusions = [
        {'start': 0, 'end': start, 'original_text': text[:start], 'classification': 'running_header',
         'source_region': [.2, .015, .7, .08],
         'evidence': 'The top centered ΤΑ ΠΕΡΙ ΗΡΑΚΛΕΙΑΝ is a running header above both continuing body columns. The original OCR variant and its blank lines remain archived.'},
        {'start': end, 'end': len(text), 'original_text': text[end:], 'classification': 'critical-apparatus',
         'source_region': [.035, .83, .965, .92],
         'evidence': 'The a.15/b.11 numbered readings, witness sigla, Stephanus/Schaeferus/Palmerus references, and Greek variants match the smaller footer below both body columns. Body ends above these notes. Greek-only consensus projection had hidden the Latin operators while retaining Greek apparatus alternatives in served slots.'}]
    return {'schema_version': 1, 'kind': 'source-reviewed-fresh-editorial-spans',
        'work': 'photius.bibliotheca', 'reviewed_at': '2026-10-18',
        'source_scan': {'url': 'https://archive.org/download/bibliothecaexrec00photuoft/bibliothecaexrec00photuoft.pdf', 'sha256': SOURCE_SHA},
        'records': [{'locus': 'photius_bekker1824_0245.1', 'scan_page': 245, 'printed_page': 233,
            'full_network': {'path': NETWORK.as_posix(), 'key': '245', 'sha256': NETWORK_SHA},
            'witness': {'id': witness['id'], 'model': witness['model'], 'revision': witness['revision'],
                'artifact_sha256': witness['artifact_sha256'], 'text_sha256': TEXT_SHA,
                'raw_file': {'path': raw_path.as_posix(), 'sha256': RAW_SHA},
                'prediction_record_sha256': sha(records[0]), 'image_sha256': prediction['image_sha256'],
                'manifest_sha256': metadata['manifest_sha256'],
                'manifest_path': MANIFEST.as_posix()},
            'original_text': text, 'exclusions': exclusions,
            'voting_segments': [{'start': start, 'end': end, 'text': text[start:end]}],
            'evidence': 'Manual inspection of combined Bekker PDF245/printed233 compared all footer notes and the top running header with the exact retained Qwen3.6 original. Only these editorial spans are excluded from its vote; substantial body word errors remain. The other checkpoint and every raw reading remain independent evidence.'}],
        'generated_by': 'scripts/prepare_photius_fresh_editorial_review.py'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    review = build(args.root)
    path = args.out if args.out.is_absolute() else args.root / args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
