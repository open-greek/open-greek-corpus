#!/usr/bin/env python3
"""Screen candidate text for exact normalized passages already in the corpus.

Nonoverlapping candidate windows are matched against every corpus window.
This identifies overlap for review; zero matches cannot exclude damaged OCR.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import zlib

MASK = (1 << 64) - 1
BASE = 1000003
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
FOLD = {i: "".join(c for c in unicodedata.normalize("NFD", chr(i)).casefold()
                   if not unicodedata.combining(c))
        for lo, hi in ((0x370, 0x400), (0x1f00, 0x2000)) for i in range(lo, hi)}


def words(text):
    return WORD.findall(text.translate(FOLD).casefold())


def windows(tokens, size):
    queue = deque()
    power = pow(BASE, size - 1, 1 << 64)
    value = 0
    for token in tokens:
        item = zlib.crc32(token.encode())
        if len(queue) == size:
            value = (value - queue.popleft()[1] * power) & MASK
        value = (value * BASE + item) & MASK
        queue.append((token, item))
        if len(queue) == size:
            yield value, queue


def audit(candidate, corpus, size=12):
    records = [json.loads(line) for line in candidate.read_text().splitlines() if line.strip()]
    own_slugs = {r["urn"] for r in records}
    text = " ".join(r["text"] for r in records)
    target = words(text)
    signatures = {}
    for i in range(0, len(target) - size + 1, size):
        block = tuple(target[i:i+size])
        key = next(windows(block, size))[0]
        signatures.setdefault(key, []).append((i, block))
    results = []
    files = [p for p in sorted(corpus.glob("*.jsonl")) if p.stem not in own_slugs]
    corpus_hash = hashlib.sha256()
    for number, path in enumerate(files, 1):
        raw = path.read_bytes()
        corpus_hash.update(f"{path.stem}\t{hashlib.sha256(raw).hexdigest()}\n".encode())
        text = " ".join(json.loads(line)["text"] for line in raw.decode().splitlines() if line.strip())
        hits = set()
        for key, window in windows(words(text), size):
            if key in signatures:
                block = tuple(t for t, _ in window)
                hits.update(i for i, expected in signatures[key] if block == expected)
        if hits:
            results.append({"work": path.stem, "matched_windows": len(hits),
                            "candidate_window_starts": sorted(hits)})
        if number % 500 == 0:
            print(f"screened {number}/{len(files)} works", flush=True)
    return {"schema_version": 1, "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            "corpus_sha256": corpus_hash.hexdigest(), "excluded_candidate_slugs": sorted(own_slugs),
            "window_words": size, "candidate_windows": (len(target) // size),
            "screened_works": len(files), "matches": sorted(results, key=lambda r: -r["matched_windows"]),
            "limitation": "Exact accent-insensitive word windows only. Quoted material can match; damaged OCR can fail to match. This report does not merge or reject works automatically.",
            "generated_by": "scripts/audit_candidate_overlap.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.candidate, args.corpus)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "matches"}))


if __name__ == "__main__":
    main()
