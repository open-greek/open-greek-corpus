#!/usr/bin/env python3
"""Restore a public source cache only when its bytes match the published pin."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "pg003-text": {
        "path": "data/cache/ia/PG003_djvu.txt",
        "url": "https://archive.org/download/Patrologia_Graeca_vol_003/PG003_djvu.txt",
        "sha256": "c3f4056dcf99ef76ac08d0e16445f01bcd43b5a1d75a52b757b545d045ab855e",
    },
    "pg003-geometry": {
        "path": "data/cache/ia/PG003_djvu.xml",
        "url": "https://archive.org/download/Patrologia_Graeca_vol_003/PG003_djvu.xml",
        "sha256": "0507e8951bfb1531ab5c4f640c06c6debf29960abbc722a9fc20cf6b7549210a",
    },
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ensure_source(name, root=ROOT, *, opener=urlopen):
    source = SOURCES[name]
    target = Path(root) / source["path"]
    if target.exists():
        if digest(target) != source["sha256"]:
            raise ValueError(f"Cached source differs from the published pin: {source['path']}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            with opener(source["url"], timeout=300) as response:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
        if digest(temporary) != source["sha256"]:
            raise ValueError(f"Downloaded source differs from the published pin: {source['path']}")
        os.replace(temporary, target)
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=sorted(SOURCES))
    args = parser.parse_args()
    print(ensure_source(args.source).relative_to(ROOT))
