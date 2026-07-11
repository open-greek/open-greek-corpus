#!/usr/bin/env python3
"""Collapse stacked qwen36 edition-tag artifacts corpus-wide.

Each page-level re-swap in the greek-ocr pipeline used to PREPEND another
"qwen36-" (or, in reingest_pg, APPEND another "-qwen36") to a work's edition
string instead of recognizing the tag it had already applied, producing labels
like "qwen36-qwen36-qwen36-tzetzes_historiae_kiessling". The generators were
fixed (greek-ocr ba84169 + the 2026-07-10 follow-ups in swap_boundary_offset0
and reingest_pg); this script repairs the strings already in the corpus.

Malformed classes (the 2026-07-10 inventory found no other duplicate-marker
artifacts among the 259 distinct edition strings):

  A. leading prefix stack   ^(qwen36-){2,}<base>       -> qwen36-<base>
  B. trailing suffix stack  <base>(-qwen36){2,}$       -> <base>-qwen36
  C. prefix on suffix-form  ^(qwen36-)+<base>-qwen36$  -> <base>-qwen36
     (the migne-ocr family: its canonical tag is "migne-ocr-qwen36", so a
     stacked leading marker is dropped rather than kept)

Only the repeats collapse; nothing else about the string changes, and row
text/locus/urn are untouched. The transform is idempotent: a second run is a
no-op.

Dry run (default) prints the full old->new mapping with per-edition row counts
and the consumer-side JSON updates an apply would make. --apply rewrites the
rows in data/corpus/ + data/corpus_secondary/, refreshes the same strings in
data/ocr_works.json and data/inventory/ocr_edition_sources.json keys, and
writes the audit mapping to data/inventory/edition_string_normalization.json.

Collision guard: renaming a key in ocr_edition_sources.json onto an existing
key whose value differs, or any mapping that would change the marker-stripped
base of a string, is refused outright (exit 2, nothing written).

Derived artifacts (data/corpus_editions.json, data/coverage_report.json) are
NOT touched here: regenerate them with reconcile_corpus_editions.py and
build_coverage_report.py after applying.

Usage:
  python scripts/normalize_edition_strings.py            # dry run
  python scripts/normalize_edition_strings.py --apply
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
CORPUS_DIRS = [DATA / "corpus", DATA / "corpus_secondary"]
OCR_WORKS = DATA / "ocr_works.json"
ED_SOURCES = DATA / "inventory" / "ocr_edition_sources.json"
AUDIT_OUT = DATA / "inventory" / "edition_string_normalization.json"

MARKER = "qwen36"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s or ""))


def normalize(ed: str) -> str:
    """Collapse stacked qwen36 markers so the marker appears exactly once.

    Pure string normalization: strings without a stacked marker (including
    mid-string uses like "ruelle-qwen36-hathitrust-rover" and
    "eustathius-odyssey-stallbaum-qwen36-pagekey") come back unchanged.
    """
    if MARKER not in ed:
        return ed
    n = re.sub(rf"^({MARKER}-)+", f"{MARKER}-", ed)     # class A
    n = re.sub(rf"(-{MARKER})+$", f"-{MARKER}", n)      # class B
    # class C: a leading marker stacked onto a suffix-form edition
    # (qwen36-migne-ocr-qwen36 -> migne-ocr-qwen36)
    if n.startswith(f"{MARKER}-") and n.endswith(f"-{MARKER}") and n != f"{MARKER}-{MARKER}":
        n = n[len(MARKER) + 1:]
    return n


def stripped_base(ed: str) -> str:
    """The string with ALL leading/trailing markers removed (collision guard)."""
    b = re.sub(rf"^({MARKER}-)+", "", ed)
    return re.sub(rf"(-{MARKER})+$", "", b)


def scan_corpus() -> tuple[Counter, dict[str, set], dict[Path, bool]]:
    """One pass over both corpus dirs: edition -> row count, edition -> work
    files carrying it, and file -> has-malformed flag."""
    ed_rows: Counter = Counter()
    ed_files: dict[str, set] = defaultdict(set)
    file_dirty: dict[Path, bool] = {}
    for d in CORPUS_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.jsonl")):
            dirty = False
            for line in open(f, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    ed = json.loads(line).get("edition", "") or ""
                except Exception:
                    continue
                ed_rows[ed] += 1
                ed_files[ed].add(f)
                if normalize(ed) != ed:
                    dirty = True
            file_dirty[f] = dirty
    return ed_rows, ed_files, file_dirty


def check_collisions(mapping: dict[str, str], ed_sources) -> list[str]:
    problems = []
    for old, new in mapping.items():
        if stripped_base(old) != stripped_base(new):
            problems.append(f"base changed: {old!r} -> {new!r}")
        if normalize(new) != new:
            problems.append(f"not idempotent: {old!r} -> {new!r} -> {normalize(new)!r}")
    if isinstance(ed_sources, dict):
        for old, new in mapping.items():
            if old in ed_sources and new in ed_sources and ed_sources[old] != ed_sources[new]:
                problems.append(
                    f"ocr_edition_sources.json key merge conflict: {old!r} and {new!r} "
                    f"carry DIFFERENT source records; refusing to merge them")
    return problems


def rewrite_corpus_file(f: Path, mapping: dict[str, str]) -> int:
    """Rewrite one work file, relabeling mapped editions only. Asserts row
    count and Greek char count unchanged. Returns rows relabeled."""
    raw = f.read_text(encoding="utf-8")
    lines = raw.splitlines()
    n_rows_before, greek_before = 0, 0
    out, changed = [], 0
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        obj = json.loads(line)
        n_rows_before += 1
        greek_before += greek_chars(obj.get("text", ""))
        ed = obj.get("edition", "") or ""
        if ed in mapping:
            obj["edition"] = mapping[ed]
            out.append(json.dumps(obj, ensure_ascii=False))
            changed += 1
        else:
            out.append(line)
    new_raw = "\n".join(out) + ("\n" if raw.endswith("\n") else "")
    # invariants: same rows, same Greek, nothing but edition changed
    n_rows_after, greek_after = 0, 0
    for line in new_raw.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        n_rows_after += 1
        greek_after += greek_chars(obj.get("text", ""))
    assert n_rows_after == n_rows_before, f"{f}: row count changed {n_rows_before}->{n_rows_after}"
    assert greek_after == greek_before, f"{f}: Greek chars changed {greek_before}->{greek_after}"
    if changed:
        f.write_text(new_raw, encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true",
                    help="rewrite corpus rows + ocr_works.json + "
                         "ocr_edition_sources.json (default: dry run)")
    args = ap.parse_args()

    ed_rows, ed_files, file_dirty = scan_corpus()
    mapping = {ed: normalize(ed) for ed in ed_rows if normalize(ed) != ed and ed}

    ed_sources = json.loads(ED_SOURCES.read_text(encoding="utf-8")) if ED_SOURCES.exists() else None
    ocr_works = json.loads(OCR_WORKS.read_text(encoding="utf-8")) if OCR_WORKS.exists() else None

    # strings that appear only in the side JSONs, not in corpus rows
    side_only = {}
    if isinstance(ed_sources, dict):
        for k in ed_sources:
            if k not in mapping and normalize(k) != k:
                side_only[k] = normalize(k)
    if isinstance(ocr_works, list):
        for w in ocr_works:
            ed = w.get("edition", "") or ""
            if ed and ed not in mapping and normalize(ed) != ed:
                side_only[ed] = normalize(ed)
    full_mapping = {**mapping, **side_only}

    problems = check_collisions(full_mapping, ed_sources)
    if problems:
        print("COLLISION / SAFETY CHECK FAILED - refusing to proceed:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 2

    n_rows = sum(ed_rows[e] for e in mapping)
    files = sorted({f for e in mapping for f in ed_files[e]})
    works_changed = sorted({f"{f.parent.name}:{f.stem}" for f in files})
    ow_changes = sum(1 for w in (ocr_works or [])
                     if (w.get("edition", "") or "") in full_mapping) if isinstance(ocr_works, list) else 0
    es_renames = {k: full_mapping[k] for k in (ed_sources or {}) if k in full_mapping} \
        if isinstance(ed_sources, dict) else {}

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"edition-string normalization [{mode}]")
    print(f"  corpus dirs: {', '.join(str(d.relative_to(REPO)) for d in CORPUS_DIRS if d.is_dir())}")
    print(f"  distinct edition strings: {len(ed_rows)}  malformed: {len(mapping)}"
          f"{f' (+{len(side_only)} only in side JSONs)' if side_only else ''}")
    print()
    print("mapping (rows  old -> new):")
    for old in sorted(full_mapping):
        print(f"  {ed_rows.get(old, 0):7d}  {old}")
        print(f"           -> {full_mapping[old]}")
    print()
    print(f"totals: {n_rows} rows in {len(files)} work files would be relabeled"
          if not args.apply else
          f"totals: {n_rows} rows in {len(files)} work files relabeling ...")
    print(f"  ocr_works.json entries: {ow_changes}")
    print(f"  ocr_edition_sources.json key renames/merges: "
          f"{json.dumps(es_renames) if es_renames else 'none'}")
    if not mapping and not side_only:
        print("nothing to do: no malformed edition strings found")
        return 0
    if not args.apply:
        print("\ndry run only; rerun with --apply to rewrite")
        return 0

    # ---- apply ----
    relabeled = {}
    for f in files:
        n = rewrite_corpus_file(f, mapping)
        if n:
            relabeled[str(f.relative_to(REPO))] = n
    assert sum(relabeled.values()) == n_rows, \
        f"relabeled {sum(relabeled.values())} rows, expected {n_rows}"

    if isinstance(ocr_works, list) and ow_changes:
        for w in ocr_works:
            ed = w.get("edition", "") or ""
            if ed in full_mapping:
                w["edition"] = full_mapping[ed]
        OCR_WORKS.write_text(json.dumps(ocr_works, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    if isinstance(ed_sources, dict) and es_renames:
        merged = {}
        for k, v in ed_sources.items():
            nk = full_mapping.get(k, k)
            if nk in merged and merged[nk] != v:      # guarded above; belt and suspenders
                print(f"CONFLICT on {nk!r}; aborting side-JSON write", file=sys.stderr)
                return 2
            merged[nk] = v
        ED_SOURCES.write_text(json.dumps(merged, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")

    audit = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "description": "collapse stacked qwen36 edition-tag repeats (pure relabel; "
                       "no row content changed). Reverse by applying the inverse "
                       "mapping to the same files.",
        "mapping": full_mapping,
        "rows_relabeled_per_edition": {e: ed_rows[e] for e in sorted(mapping)},
        "rows_relabeled_total": n_rows,
        "files_changed": relabeled,
        "ocr_works_entries_changed": ow_changes,
        "ocr_edition_sources_renames": es_renames,
        "works": works_changed,
    }
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(f"\napplied. audit mapping -> {AUDIT_OUT.relative_to(REPO)}")
    print("regenerate derived files: reconcile_corpus_editions.py, build_coverage_report.py")

    # idempotence proof: rescan finds nothing
    ed_rows2, _, _ = scan_corpus()
    leftover = {e for e in ed_rows2 if normalize(e) != e}
    assert not leftover, f"non-idempotent: leftover malformed editions {leftover}"
    print("rescan clean: normalization is idempotent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
