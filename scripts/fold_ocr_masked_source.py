#!/usr/bin/env python3
"""Fold the top-level `source` category "ocr-masked" into "ocr" corpus-wide.

Both "ocr" and "ocr-masked" are OGC's OWN OCR: the masked-column re-OCR fleet
(geometric column mask + FP8 serving) is one pipeline within OGC OCR, not a
separate provenance. Carrying it as a distinct top-level `source` split the
reader's "OGC OCR" bucket in two and surfaced a stray "OCR Masked" source. This
collapses the category so every OGC-OCR'd row reads `source: "ocr"`.

The masked-pipeline DETAIL is NOT lost: it lives in the edition slug
(`qwen36-*-masked` / `qwen36-*_masked` / the `-singlecol` masked variant) and in
the per-work record under `data/ocr_provenance/` (model, source scan, render DPI,
column geometry). Those are deliberately untouched. build_provenance.py detects
masked works from the edition slug + provenance record, so the README provenance
table still labels them with their masked-column pipeline.

Pure relabel: only the value of the `source` field flips, and only for rows that
carried exactly "ocr-masked". Row count, text, locus, urn, edition and license are
asserted unchanged. Idempotent: a second run finds nothing to do.

Reversible: the audit at data/inventory/ocr_masked_source_fold.json records every
edition string whose rows were folded. To reconstruct the pre-fold state, set
`source` back to "ocr-masked" on rows whose `edition` is one of those strings (an
edition maps to a single source, so the mapping is exact).

Usage:
  python scripts/fold_ocr_masked_source.py            # dry run
  python scripts/fold_ocr_masked_source.py --apply
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
AUDIT_OUT = DATA / "inventory" / "ocr_masked_source_fold.json"

OLD_SOURCE = "ocr-masked"
NEW_SOURCE = "ocr"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s or ""))


def scan() -> tuple[dict[Path, int], Counter]:
    """file -> #rows carrying ocr-masked; and edition -> #folded rows."""
    per_file: dict[Path, int] = {}
    per_edition: Counter = Counter()
    for d in CORPUS_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.jsonl")):
            n = 0
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("source") == OLD_SOURCE:
                    n += 1
                    per_edition[r.get("edition", "") or ""] += 1
            if n:
                per_file[f] = n
    return per_file, per_edition


def rewrite_file(f: Path) -> int:
    """Relabel ocr-masked -> ocr in one file. Asserts nothing but the source
    value of those rows changed (row count + Greek chars + every other field are
    preserved). Returns rows relabeled."""
    raw = f.read_text(encoding="utf-8")
    lines = raw.splitlines()
    out, changed = [], 0
    rows_before = greek_before = 0
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        obj = json.loads(line)
        rows_before += 1
        greek_before += greek_chars(obj.get("text", ""))
        if obj.get("source") == OLD_SOURCE:
            # Rebuild the row identically except for the one field, preserving
            # key order so the diff is exactly source: ocr-masked -> ocr.
            new_obj = {k: (NEW_SOURCE if k == "source" else v) for k, v in obj.items()}
            out.append(json.dumps(new_obj, ensure_ascii=False))
            changed += 1
        else:
            out.append(line)
    new_raw = "\n".join(out) + ("\n" if raw.endswith("\n") else "")
    # invariants: same rows, same Greek, no residual ocr-masked source
    rows_after = greek_after = residual = 0
    for line in new_raw.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rows_after += 1
        greek_after += greek_chars(obj.get("text", ""))
        if obj.get("source") == OLD_SOURCE:
            residual += 1
    assert rows_after == rows_before, f"{f}: row count changed {rows_before}->{rows_after}"
    assert greek_after == greek_before, f"{f}: Greek chars changed {greek_before}->{greek_after}"
    assert residual == 0, f"{f}: {residual} ocr-masked rows survived"
    if changed:
        f.write_text(new_raw, encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true",
                    help="rewrite corpus rows (default: dry run)")
    args = ap.parse_args()

    per_file, per_edition = scan()
    total = sum(per_file.values())
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"fold source {OLD_SOURCE!r} -> {NEW_SOURCE!r} [{mode}]")
    print(f"  corpus dirs: {', '.join(str(d.relative_to(REPO)) for d in CORPUS_DIRS if d.is_dir())}")
    print(f"  rows to relabel: {total} across {len(per_file)} files, "
          f"{len(per_edition)} distinct masked editions")
    for ed in sorted(per_edition):
        print(f"    {per_edition[ed]:7d}  {ed}")
    if not per_file:
        print("nothing to do: no ocr-masked rows found")
        return 0
    if not args.apply:
        print("\ndry run only; rerun with --apply to rewrite")
        return 0

    relabeled: dict[str, int] = {}
    for f in sorted(per_file):
        n = rewrite_file(f)
        if n:
            relabeled[str(f.relative_to(REPO))] = n
    assert sum(relabeled.values()) == total, \
        f"relabeled {sum(relabeled.values())} rows, expected {total}"

    audit = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "description": "collapse the top-level OCR source category 'ocr-masked' into "
                       "'ocr' (both are OGC's own OCR; the masked-column pipeline is "
                       "one OGC-OCR pipeline, not a separate source). Pure relabel: "
                       "only the `source` field flipped. Masked detail is retained in "
                       "the edition slug and data/ocr_provenance/.",
        "mapping": {OLD_SOURCE: NEW_SOURCE},
        "rows_relabeled_total": total,
        "rows_relabeled_per_file": relabeled,
        "folded_editions": {ed: per_edition[ed] for ed in sorted(per_edition)},
        "reverse": "set source back to 'ocr-masked' on rows whose `edition` is one of "
                   "folded_editions (edition -> source is 1:1, so this is exact).",
    }
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(f"\napplied. audit -> {AUDIT_OUT.relative_to(REPO)}")
    print("regenerate derived files: reconcile_corpus_editions.py (make ids), "
          "build_provenance.py")

    # idempotence proof: rescan finds nothing
    per_file2, _ = scan()
    assert not per_file2, f"non-idempotent: ocr-masked rows survived in {list(per_file2)}"
    print("rescan clean: fold is idempotent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
