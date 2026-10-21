#!/usr/bin/env python3
"""Fetch or verify the exact public Hoeschel images used by source reviews."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from photius_uncertainty_observations import SOURCES, ARCHIVE

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(ARCHIVE) / 'sources.json'


def manifest():
    return (json.dumps({'schema': 'photius-uncertainty-comparison-sources-v1',
        'generated_by': 'scripts/fetch_photius_uncertainty_sources.py',
        'qualification': 'Earlier edition comparison images; not another Bekker scan or an independent manuscript vote.',
        'sources': SOURCES}, ensure_ascii=False, indent=2) + '\n').encode()


def verify(raw, source):
    from io import BytesIO
    from PIL import Image
    if hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('Pinned Hoeschel source image changed: ' + source['path'])
    with Image.open(BytesIO(raw)) as image:
        if list(image.size) != source['dimensions']:
            raise ValueError('Hoeschel image dimensions changed')
        image.verify()


def run(root=ROOT, *, write=False):
    root = Path(root)
    for source in SOURCES.values():
        path = root / source['path']
        if write and not path.exists():
            with urllib.request.urlopen(source['url'], timeout=60) as response:
                raw = response.read()
            verify(raw, source)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        else:
            verify(path.read_bytes(), source)
    expected = manifest()
    path = root / MANIFEST
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)
    elif path.read_bytes() != expected:
        raise ValueError('Hoeschel source manifest is stale')
    print('Four pinned public Hoeschel comparison images verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    run(write=args.write)


if __name__ == '__main__':
    main()
