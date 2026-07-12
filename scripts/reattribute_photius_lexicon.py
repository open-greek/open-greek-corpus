#!/usr/bin/env python3
"""Reattribute the mis-keyed photius.bibliotheca served work to the Photius Lexicon.

The text served under photius.bibliotheca is NOT the Bibliotheca. It is our
Qwen3.6 OCR of the Naber Photius Lexicon (edition qwen36-photius_lexicon_naber;
S. A. Naber, Photii Patriarchae Lexicon, Leiden 1864-65) - an alphabetical lexicon
(Λέξεων Συναγωγή), not the codex-by-codex Bibliotheca. Photius = tlg4040; the
Bibliotheca is tlg4040.tlg001, while the Lexicon is tlg4040.tlg029 (Α-Δ, ed.
Theodoridis) + tlg4040.tlg030 (Ε-Ω, ed. Porson) - the current TLG canon splits
the one Lexicon across two work-ids purely by which modern edition covers each
alphabet range.

This script re-keys the served OCR from photius.bibliotheca to a neutral
photius.lexicon slug and points it at the primary Lexicon work-id tlg4040.tlg029.
The Naber edition is a single complete-alphabet (Α-Ω) text, so it is mapped to the
Lexicon head rather than to either half; a later re-OCR may split it Α-Δ / Ε-Ω onto
tlg029 / tlg030.

This is NOT a rename with redirect: the slug photius.bibliotheca legitimately
belongs to the Bibliotheca (a different work COG still tracks as a gap), so it is
left free rather than turned into a former_slug of the Lexicon. build_id_registry
retires the old served id (the mis-keyed capture) and mints a fresh one for
photius.lexicon.

Provenance note: the open Naber (and Porson) Lexicon predates the 1959 discovery
of the Zavorda codex (Cod. 95), so even a perfect OCR of it is inherently
INCOMPLETE against the modern complete text (Theodoridis, De Gruyter 1982-2013,
copyrighted). Naber is the best OPEN version only.

  python3 scripts/reattribute_photius_lexicon.py            # dry-run
  python3 scripts/reattribute_photius_lexicon.py --write
  then: make ids   (retires the old id, mints photius.lexicon, reconciles editions)
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
NEEDS_PATH = REPO / "data" / "needs_ocr_cleanup.json"
CHANGES = REPO / "data" / "corpus_changes"

OLD_SLUG = "photius.bibliotheca"
NEW_SLUG = "photius.lexicon"
LEXICON_CTS = "urn:cts:greekLit:tlg4040.tlg029"
LEXICON_TLG = "tlg4040.tlg029"
CW_NOTE = ("served text is the Naber Photius Lexicon (Λέξεων Συναγωγή), OCR of "
           "S.A. Naber, Leiden 1864-65; a single complete-alphabet (Α-Ω) edition "
           "mapped to the primary Lexicon work-id tlg4040.tlg029 (TLG splits the "
           "Lexicon tlg029 Α-Δ / tlg030 Ε-Ω by edition). Formerly mis-keyed as "
           "photius.bibliotheca (tlg4040.tlg001). Naber predates the 1959 Zavorda "
           "codex, so it is inherently incomplete vs Theodoridis (copyrighted).")


def _write_tsv(cw: dict) -> None:
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):
                f.write(f"{s}\t{d['cts']}\t{d.get('tlg', '')}\n")


def main() -> None:
    write = "--write" in sys.argv
    old_fp = CORPUS / f"{OLD_SLUG}.jsonl"
    new_fp = CORPUS / f"{NEW_SLUG}.jsonl"
    if not old_fp.exists():
        sys.exit(f"ABORT: {old_fp.name} not found (already reattributed?)")
    if new_fp.exists():
        sys.exit(f"ABORT: {new_fp.name} already exists")
    rows = [json.loads(l) for l in old_fp.read_text(encoding="utf-8").splitlines() if l.strip()]
    edition = rows[0].get("edition") if rows else None
    print(f"reattribute {OLD_SLUG} -> {NEW_SLUG}  (cts {LEXICON_TLG})")
    print(f"  {len(rows)} rows, edition {edition}")
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    print(f"  crosswalk {OLD_SLUG}: {cw.get(OLD_SLUG)}")

    if not write:
        print("DRY RUN - nothing written (use --write)")
        return

    sha = hashlib.sha256(old_fp.read_bytes()).hexdigest()
    for r in rows:
        if r.get("urn") == OLD_SLUG:
            r["urn"] = NEW_SLUG
    new_fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                      encoding="utf-8")
    old_fp.unlink()
    print(f"  moved corpus file, re-keyed {len(rows)} rows")

    # Add the Lexicon crosswalk entry; leave photius.bibliotheca -> tlg4040.tlg001
    # in place (it correctly names the Bibliotheca, now an unserved gap work).
    cw[NEW_SLUG] = {"cts": LEXICON_CTS, "tlg": LEXICON_TLG,
                    "author_slug": "photius", "title": "Lexicon", "note": CW_NOTE}
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0), encoding="utf-8")
    _write_tsv(cw)
    print(f"  added crosswalk {NEW_SLUG} -> {LEXICON_TLG} (+ tsv regenerated)")

    needs = json.loads(NEEDS_PATH.read_text(encoding="utf-8"))
    if OLD_SLUG in needs:
        needs[NEW_SLUG] = needs.pop(OLD_SLUG)
        NEEDS_PATH.write_text(json.dumps(needs, ensure_ascii=False, indent=1, sort_keys=True),
                              encoding="utf-8")
        print(f"  re-keyed needs_ocr_cleanup {OLD_SLUG} -> {NEW_SLUG}")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    CHANGES.mkdir(parents=True, exist_ok=True)
    audit = CHANGES / "photius-lexicon-reattribution.json"
    audit.write_text(json.dumps({
        "_meta": {
            "change": "reattribute mis-keyed served work (Bibliotheca -> Lexicon)",
            "applied_by": "scripts/reattribute_photius_lexicon.py", "date": date,
            "reversible": "move data/corpus/photius.lexicon.jsonl back and drop the crosswalk entry",
        },
        "old": {"slug": OLD_SLUG, "cts": "urn:cts:greekLit:tlg4040.tlg001",
                "claimed_work": "Bibliotheca", "edition": edition, "rows": len(rows),
                "sha256": sha},
        "new": {"slug": NEW_SLUG, "cts": LEXICON_CTS, "work": "Lexicon (Λέξεων Συναγωγή)",
                "edition": edition},
        "evidence": (
            "The served rows are the Naber Photius Lexicon (alphabetical entries), not the "
            "codex-by-codex Bibliotheca. Photius = tlg4040 (TLG canon); Bibliotheca = "
            "tlg4040.tlg001, Lexicon = tlg4040.tlg029 (Α-Δ, Theodoridis) + tlg4040.tlg030 "
            "(Ε-Ω, Porson). The complete-alphabet Naber edition is mapped to the primary "
            "Lexicon work-id tlg029; a later re-OCR may split it onto tlg029/tlg030."),
        "provenance_note": (
            "Naber (Leiden 1864-65) and Porson (Cambridge 1822) predate the 1959 Zavorda "
            "codex (Cod. 95); the open Lexicon text is therefore inherently incomplete vs "
            "the modern complete edition (Theodoridis, De Gruyter, copyrighted). Best OPEN "
            "version only."),
        "source": "tlg_canon.json (tlg4040 works); re-OCR worklist reattribute verdict",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote audit -> {audit.relative_to(REPO)}")
    print("now run `make ids` (retires the old served id, mints photius.lexicon)")


if __name__ == "__main__":
    main()
