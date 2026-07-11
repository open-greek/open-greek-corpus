#!/usr/bin/env python3
"""Rename a served work's slug WITHOUT losing its identity.

The slug is a human-readable alias of an opaque, immutable ogc id (see
scripts/build_id_registry.py and docs/opaque-identifiers.md). A re-attribution or
edition re-scope changes the slug, but the work is the same work, so its ogc id
must stay put and the old slug must keep resolving to it (the data-side of a 301
redirect). This tool is the ONE supported way to rename a work; doing it by hand
(the old ad-hoc rescope scripts) risks minting a fresh id and orphaning every
citation, correction, and link keyed by the old slug.

What it does (with --write):
  1. moves data/corpus/<old>.jsonl -> <new>.jsonl and rewrites every row's
     ``urn`` field (and the same for data/corpus_secondary/ if present);
  2. rekeys the slug-keyed metadata it can: tlg_crosswalk.json (+ .tsv),
     source_registry.json (works entry + its edition-slug prefixes + author
     field), needs_ocr_cleanup.json, ocr_works.json - each only if the old slug
     is present;
  3. records the rename in data/work_id_aliases.json (the reproducible seed);
  4. re-runs the id ledger, corpus_editions reconcile, and the work index, so the
     ogc id follows the work and the old slug lands in its ``former_slugs``.

Idempotent inputs: the rename seed is append-only, so a second run is a no-op.
Derived artifacts (coverage, lexicon) are refreshed by ``make`` as usual.

    python3 scripts/rename_work.py OLD_SLUG NEW_SLUG            # dry-run
    python3 scripts/rename_work.py OLD_SLUG NEW_SLUG --write
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CORPUS_SECONDARY = DATA / "corpus_secondary"
CW = DATA / "tlg_crosswalk.json"
CW_TSV = DATA / "tlg_crosswalk.tsv"
REGISTRY = DATA / "source_registry.json"
NEEDS = DATA / "needs_ocr_cleanup.json"
OCR_WORKS = DATA / "ocr_works.json"
ALIASES = DATA / "work_id_aliases.json"
WORK_IDS = DATA / "work_ids.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _rewrite_jsonl(fp: Path, dst: Path, old: str, new: str) -> int:
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    for r in rows:
        if r.get("urn") == old:
            r["urn"] = new
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                   encoding="utf-8")
    return len(rows)


def _write_crosswalk_tsv(cw: dict) -> None:
    with CW_TSV.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):
                f.write(f"{s}\t{d['cts']}\t{d.get('tlg','')}\n")


def rename(old: str, new: str, write: bool) -> None:
    old_fp = CORPUS / f"{old}.jsonl"
    new_fp = CORPUS / f"{new}.jsonl"
    if not old_fp.exists():
        sys.exit(f"ABORT: {old_fp.name} not found (old slug not served)")
    if new_fp.exists():
        sys.exit(f"ABORT: {new_fp.name} already exists (new slug already served)")

    # Guard identity: the new slug must not already be a current/former slug of
    # some OTHER work in the ledger (that would be a merge, not a rename).
    wl = (_load(WORK_IDS) or {}).get("works", {})
    for i, e in wl.items():
        if e["slug"] == new or new in e.get("former_slugs", []):
            sys.exit(f"ABORT: new slug {new!r} already owned by {i}; use a merge "
                     f"tool, not rename")

    new_author = new.split(".", 1)[0]
    print(f"rename: {old} -> {new}  (author -> {new_author})")

    if not write:
        rows = sum(1 for l in old_fp.read_text(encoding='utf-8').splitlines()
                   if l.strip())
        print(f"  corpus rows to re-key: {rows}")
        sec = CORPUS_SECONDARY / f"{old}.jsonl"
        if sec.exists():
            print(f"  corpus_secondary present: {sec.name}")
        cw = _load(CW) or {}
        if old in cw:
            print(f"  tlg_crosswalk entry: {cw[old]}")
        reg = _load(REGISTRY) or {"works": {}}
        if old in reg["works"]:
            print(f"  source_registry works entry present "
                  f"({len(reg['works'][old].get('editions', {}))} editions)")
        print("  DRY RUN - nothing written (use --write)")
        return

    # 1. corpus file + rows
    n = _rewrite_jsonl(old_fp, new_fp, old, new)
    old_fp.unlink()
    print(f"  moved corpus file, re-keyed {n} rows")
    sec = CORPUS_SECONDARY / f"{old}.jsonl"
    if sec.exists():
        m = _rewrite_jsonl(sec, CORPUS_SECONDARY / f"{new}.jsonl", old, new)
        sec.unlink()
        print(f"  moved corpus_secondary file, re-keyed {m} rows")

    # 2a. tlg_crosswalk
    cw = _load(CW)
    if cw is not None and old in cw:
        entry = cw.pop(old)
        entry["author_slug"] = new_author
        cw[new] = entry
        CW.write_text(json.dumps(cw, ensure_ascii=False, indent=0), encoding="utf-8")
        _write_crosswalk_tsv(cw)
        print("  re-keyed tlg_crosswalk (+ tsv)")

    # 2b. source_registry: rekey work + reprefix its edition slugs + author
    reg = _load(REGISTRY)
    if reg is not None and old in reg.get("works", {}):
        w = reg["works"].pop(old)
        w["author"] = new_author
        eds = w.get("editions", {})
        w["editions"] = {
            (new + ek[len(old):] if ek.startswith(old) else ek): ev
            for ek, ev in eds.items()
        }
        if isinstance(w.get("default_edition"), str) and \
                w["default_edition"].startswith(old):
            w["default_edition"] = new + w["default_edition"][len(old):]
        reg["works"][new] = w
        REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1,
                                       sort_keys=False), encoding="utf-8")
        print("  re-keyed source_registry works entry")

    # 2c. needs_ocr_cleanup / ocr_works
    for path in (NEEDS, OCR_WORKS):
        d = _load(path)
        if isinstance(d, dict) and old in d:
            d[new] = d.pop(old)
            path.write_text(json.dumps(d, ensure_ascii=False, indent=1,
                                       sort_keys=True), encoding="utf-8")
            print(f"  re-keyed {path.name}")

    # 3. record the rename in the reproducible seed
    al = _load(ALIASES) or {"renames": []}
    al.setdefault("renames", [])
    if not any(r.get("from") == old and r.get("to") == new for r in al["renames"]):
        al["renames"].append({"from": old, "to": new,
                              "source": "scripts/rename_work.py",
                              "note": f"renamed {old} -> {new}"})
        ALIASES.write_text(json.dumps(al, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print("  recorded rename in work_id_aliases.json")

    # 4. re-derive: ledger (id follows the work) FIRST - it scans the corpus dir,
    #    so the moved file is already the served truth - then reconcile
    #    corpus_editions (injects the id) and the work index.
    import build_id_registry
    import build_work_index
    import reconcile_corpus_editions
    print("  rebuilding id ledger / corpus_editions / work_index ...")
    build_id_registry.build(write=True)
    reconcile_corpus_editions.main()
    build_work_index.build(write=True)

    # confirm the id survived
    wl2 = (_load(WORK_IDS) or {}).get("works", {})
    kept = next((i for i, e in wl2.items()
                 if e["slug"] == new and old in e.get("former_slugs", [])), None)
    if kept:
        print(f"  DONE: {new} keeps id {kept}; {old} redirects to it")
    else:
        print("  WARNING: could not confirm id preservation; inspect work_ids.json")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit("usage: rename_work.py OLD_SLUG NEW_SLUG [--write]")
    rename(args[0], args[1], write="--write" in sys.argv)


if __name__ == "__main__":
    main()
