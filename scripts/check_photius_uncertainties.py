#!/usr/bin/env python3
"""Check the frozen 33-span review beneath later served admissions.

The original recipe remains byte-pinned by subsequent source archives. Its
stage-local checker compares the live file even after peeling later layers.
This adapter freshly rebuilds every original source artifact, then compares
the checked predecessor view for the corpus and live bytes for other outputs.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import repair_photius_uncertainties as historical


def check(root=historical.ROOT):
    root=Path(root)
    if not (root/historical.AUDIT).exists():
        return historical.check(root)
    outputs,audit=historical.build(root)
    current=historical._later_bytes((root/historical.CORPUS).read_bytes(),root)
    before=gzip.decompress(outputs[historical.BEFORE])
    for path,expected in outputs.items():
        if path==historical.CORPUS and current==before:
            continue
        observed=current if path==historical.CORPUS else (root/path).read_bytes()
        if observed!=expected:
            raise ValueError('Historical uncertainty review differs from its checked source artifacts or predecessor corpus')
    return None if current==before else audit


if __name__=='__main__':
    print(json.dumps(check(),ensure_ascii=False))
