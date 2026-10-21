#!/usr/bin/env python3
"""Measure cold and repeated Photius validation without writing corpus data.

Run in a fresh Python process for each revision, against the same frozen inputs.
The first iteration includes cold process caches; later iterations retain them.
Output fingerprints must agree across iterations and compared revisions.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
import resource
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--scope", choices=("coverage", "observations"), default="coverage")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")

    # Import before wrapping the codec, consistently in every compared process.
    if args.scope == "coverage":
        from coverage_resolution import resolution
        def run():
            result = resolution(args.root, "photius.bibliotheca")
            raw = json.dumps(result, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode()
            return {"coverage": hashlib.sha256(raw).hexdigest()}
    else:
        from build_photius_review_observations import build
        def run():
            outputs, _ = build(args.root)
            for path, raw in outputs.items():
                if (args.root / path).read_bytes() != raw:
                    raise ValueError(f"Frozen observation artifact does not reproduce: {path}")
            return {path.as_posix(): hashlib.sha256(raw).hexdigest()
                    for path, raw in outputs.items()}

    codec = gzip.compress
    totals = {"calls": 0, "input_bytes": 0, "seconds": 0.0}
    def measured(raw, *positional, **keywords):
        start = time.perf_counter()
        try:
            return codec(raw, *positional, **keywords)
        finally:
            totals["calls"] += 1
            totals["input_bytes"] += len(raw)
            totals["seconds"] += time.perf_counter() - start
    gzip.compress = measured
    expected = None
    try:
        for iteration in range(1, args.repeat + 1):
            before, start = dict(totals), time.perf_counter()
            pins = run()
            elapsed = time.perf_counter() - start
            if expected is not None and pins != expected:
                raise ValueError("Validation output changed between benchmark iterations")
            expected = pins
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            print(json.dumps({
                "scope": args.scope, "iteration": iteration,
                "python": platform.python_version(), "platform": platform.system(),
                "seconds": round(elapsed, 3),
                "peak_rss_bytes": peak * (1 if sys.platform == "darwin" else 1024),
                "output_sha256": pins,
                "gzip_calls": totals["calls"] - before["calls"],
                "gzip_input_bytes": totals["input_bytes"] - before["input_bytes"],
                "gzip_seconds": round(totals["seconds"] - before["seconds"], 3),
            }, sort_keys=True), flush=True)
    finally:
        gzip.compress = codec


if __name__ == "__main__":
    main()
