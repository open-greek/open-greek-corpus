#!/usr/bin/env python3
"""Shared registry of works that need a PD source / OCR / OCR-cleanup.

The registry file (data/needs_pd_or_ocr.json) is written by MORE THAN ONE producer:
the corpus build flags works available only under NC/unknown licenses (so they need
a public-domain edition or OCR), and other local tools flag works whose text they
could not use and want OCR'd or cleaned. To let producers coexist, every producer
MERGES rather than overwrites - it replaces only the records tagged with its own
`by` name and leaves all other producers' records untouched.

Schema (one work -> a LIST of producer records):

    {
      "<work-urn>": [
        {"by": "<producer>", "needs": ["ocr", "ocr_cleanup", ...], ...extra},
        ...
      ]
    }

A legacy flat value ({"by": ..., "needs": ...}) is migrated to a single-element
list on the next merge, so older writers' output is preserved, not lost.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_needs(path: Path) -> dict:
    """Read the registry, normalising every value to a list of records and
    migrating any legacy flat record. Missing/corrupt file -> empty registry."""
    out: dict[str, list[dict]] = {}
    if not path.exists():
        return out
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return out
    for urn, val in raw.items():
        recs = val if isinstance(val, list) else [val]
        out[urn] = [r for r in recs if isinstance(r, dict)]
    return out


def merge_needs(path: Path, by: str, entries: dict, scope=None) -> dict:
    """Merge this producer's `entries` into the registry at `path`, preserving every
    OTHER producer's records, and write it back (sorted, deterministic).

    `by`       this producer's name (e.g. "build_corpus_loci"); it fully owns and
               replaces the records carrying this name and never touches others'.
    `entries`  {work-urn: record-dict}; `by` is injected, so pass just the payload
               (e.g. {"tlg0001.tlg001": {"needs": ["pd_or_ocr"], "license": "..."}}).
    `scope`    the set of work-urns this run actually examined, or None for a full
               run. A PARTIAL run (build_corpus_loci --only ...) must pass the keys
               it scanned: replace-all would silently delete this producer's records
               for every work outside the subset.
    Returns the merged registry.
    """
    merged = load_needs(path)
    for urn in list(merged):                       # drop this producer's stale records
        if scope is not None and urn not in scope:
            continue                               # not re-examined this run: keep
        kept = [r for r in merged[urn] if r.get("by") != by]
        if kept:
            merged[urn] = kept
        else:
            del merged[urn]
    for urn, rec in entries.items():               # add this producer's current records
        merged.setdefault(urn, []).append({"by": by, **rec})
    path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    return merged
