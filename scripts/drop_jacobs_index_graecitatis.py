#!/usr/bin/env python3
"""Drop the broken jacobs-anthologia-graeca-t13.index-graecitatis served capture.

The served work is a broken redo OCR (edition qwen36-claudianus_epigr_anthologia_graeca,
527 rows, bleed 0.82) of the word-INDEX volume of Jacobs' Anthologia Graeca
(F. Jacobs, Anthologia Graeca, Tom. XIII "Index graecitatis et animadversiones",
Leipzig 1814): apparatus, a garbled table of contents of the anthology's books,
and Brunck collation notes wrapped in stray <note> tags. It is an edition-scoped
apparatus with no TLG urn and no corpus value of its own.

The Greek Anthology itself (tlg7000.tlg001) is already served cleanly and in full
as anthologia-graeca.anthologia-graeca from Perseus (best_source open_corpus,
CC BY-SA 4.0; ~21k passages across the perseus-grc6..grc10 + beckby editions), so
the epigram content this index points at is not lost. The index apparatus is
therefore redundant and is removed rather than re-OCR'd.

This is a DROP with no successor slug (not a rename): the retired work has no
single work it becomes, so build_id_registry tombstones its ogc id in place
(status -> retired; the id is never recycled) rather than redirecting it. The
sibling jacobs-anthologia-graeca-t13.appendix-epigrammatum (actual epigram text)
is a different work and is left untouched.

  python3 scripts/drop_jacobs_index_graecitatis.py            # dry-run
  python3 scripts/drop_jacobs_index_graecitatis.py --write
  then: make ids   (tombstones the id + reconciles corpus_editions)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
NEEDS_PATH = REPO / "data" / "needs_ocr_cleanup.json"
OCR_WORKS_PATH = REPO / "data" / "ocr_works.json"
CHANGES = REPO / "data" / "corpus_changes"

SLUG = "jacobs-anthologia-graeca-t13.index-graecitatis"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _write_tsv(cw: dict) -> None:
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):
                f.write(f"{s}\t{d['cts']}\t{d.get('tlg', '')}\n")


def main() -> None:
    write = "--write" in sys.argv
    fp = CORPUS / f"{SLUG}.jsonl"
    if not fp.exists():
        sys.exit(f"ABORT: {fp.name} not found (already dropped?)")
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]
    gk = sum(len(_GK.findall(r.get("text", ""))) for r in rows)
    edition = rows[0].get("edition") if rows else None
    print(f"drop {SLUG}: {len(rows)} rows, edition {edition}, {gk:,} Greek chars")

    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    print(f"  crosswalk entry present: {SLUG in cw}")
    needs = json.loads(NEEDS_PATH.read_text(encoding="utf-8"))

    if not write:
        print("DRY RUN - nothing written (use --write)")
        return

    CHANGES.mkdir(parents=True, exist_ok=True)
    archive = CHANGES / f"{SLUG}.dropped-ocr.jsonl"
    archive.write_text(fp.read_text(encoding="utf-8"), encoding="utf-8")
    sha = hashlib.sha256(fp.read_bytes()).hexdigest()
    fp.unlink()
    print(f"  archived + removed corpus file (-> {archive.relative_to(REPO)})")

    if SLUG in cw:
        cw.pop(SLUG)
        CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0), encoding="utf-8")
        _write_tsv(cw)
        print("  removed crosswalk entry (+ tsv regenerated)")

    for path in (NEEDS_PATH, OCR_WORKS_PATH):
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict) and SLUG in d:
            d.pop(SLUG)
            path.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True),
                            encoding="utf-8")
            print(f"  removed {SLUG} from {path.name}")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit = CHANGES / "jacobs-index-graecitatis-drop.json"
    audit.write_text(json.dumps({
        "_meta": {
            "change": "drop served work (broken OCR of a word-index, redundant)",
            "work": SLUG, "tlg": None,
            "applied_by": "scripts/drop_jacobs_index_graecitatis.py",
            "date": date,
            "reversible": (f"restore {archive.name} (in this directory) to "
                           f"data/corpus/{SLUG}.jsonl and re-add the crosswalk entry"),
        },
        "old": {"edition": edition, "rows": len(rows), "greek_chars": gk, "sha256": sha,
                "archived_to": str(archive.relative_to(REPO))},
        "evidence": (
            "Broken redo OCR (bleed 0.82) of Jacobs, Anthologia Graeca Tom. XIII, the "
            "'Index graecitatis et animadversiones' apparatus (Leipzig 1814): word index, "
            "garbled book table-of-contents, Brunck collation notes in stray <note> tags. "
            "No TLG urn, no independent corpus value. The Anthologia Graeca poems it indexes "
            "are already served cleanly as anthologia-graeca.anthologia-graeca "
            "(tlg7000.tlg001, Perseus, CC BY-SA 4.0, ~21k passages)."),
        "source": "re-OCR worklist audit (drop verdict); Perseus tlg7000 coverage check",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote audit -> {audit.relative_to(REPO)}")
    print("now run `make ids` (tombstones the id + reconciles corpus_editions)")


if __name__ == "__main__":
    main()
