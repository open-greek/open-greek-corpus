#!/usr/bin/env python3
"""Reproduce the retained historical scan-only diagnostic requests.

These attempts locate recognition problems. They contribute no primary text or
vote. The seed source object is retained exactly; each job's physical and
printed page fields identify the actual diagnostic region.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = Path('data/ocr_requests/photius-bekker-body-recovery.json')
SEED_SHA = 'd6bc981eca155c51d7a4aa74d2f0c28e1adf71b4bebedee3297f4f7749e03d4d'
PILOT = Path('data/ocr_requests/photius-historical-pilot.json')
STRIPS = Path('data/ocr_requests/photius-historical-reading-diagnostics.json')
BOXES = {2: [.055,.131,.413,.294], 3: [.235,.108,.58,.273],
         16: [.086,.112,.435,.282], 169: [.234,.111,.582,.279],
         230: [.068,.111,.414,.276], 280: [.06,.122,.412,.292]}


def build(root=ROOT):
    raw = (Path(root)/SEED).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SEED_SHA:
        raise ValueError('Original diagnostic request seed changed')
    seed = json.loads(raw); seed.pop('source_review')
    pilot = deepcopy(seed)
    pilot['purpose'] = 'Diagnostic pilot for historical body reading assessment; never a primary corpus admission.'
    pilot['pages'] = [{'id': 'photius-historical-0002-left-pilot', 'source': 'photius-bekker-legacy',
        'scan_page': 2, 'printed_page': 267, 'region': [.06,.139,.413,.727], 'max_side': 3600,
        'role': 'diagnostic-historical-body',
        'prompt_suffix': 'This is a single body column. Preserve the original complete line sequence.'}]
    strips = deepcopy(seed)
    strips['purpose'] = 'Diagnostic source-only comparison for occurrence-level historical reading review. Predictions never enter primary text without a completed exact occurrence authority.'
    strips['pages'] = [{'id': f'photius-historical-{n:04d}-left-upper', 'source': 'photius-bekker-legacy',
        'scan_page': n, 'printed_page': n+265, 'region': box, 'max_side': 3600,
        'role': 'diagnostic-historical-body',
        'prompt_suffix': 'This is a diagnostic source-only transcription. Preserve literal printed word fragments and complete source line order.'}
        for n, box in BOXES.items()]
    strips['review']['pilot_policy'] = 'First one-column diagnostic finished with stop but had poor recognition; use shorter enlarged source strips, and retain all predictions as diagnostics rather than extra votes.'
    return {path: (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()
            for path, value in ((PILOT, pilot), (STRIPS, strips))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true'); action.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build()
    if args.write:
        for path, raw in outputs.items(): (ROOT/path).write_bytes(raw)
    elif args.check and any((ROOT/path).read_bytes() != raw for path, raw in outputs.items()):
        parser.exit(1, 'Historical diagnostic request changed\n')
    print(json.dumps({'diagnostic_requests': len(outputs), 'primary_votes': 0}))
