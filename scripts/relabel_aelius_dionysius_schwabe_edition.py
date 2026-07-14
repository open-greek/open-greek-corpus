#!/usr/bin/env python3
"""Relabel the served Aelius Dionysius atticist work off the wrong Migne tag.

The served work aelius-dionysius.attika-o-no-mata (tlg1323.tlg001, ogc000074)
carries the edition tag "migne-ocr-qwen36", a delivery-side artifact from the
upstream OCR pipeline. Its text is NOT Migne: it is Ludwig Schwabe's 1890
atticist edition (Aelii Dionysii et Pausaniae Atticistarum fragmenta, archive.org
ailioudionysiouk00dionuoft), the same run that produced its sibling served work
pausanias-attic.attikw-n-o-noma-twn-sunagwgh (tlg1569.tlg001), which is correctly
tagged "qwen36-aelius_dionysius_schwabe-ocr". Every row's locus in this file
already carries the "aelius_dionysius_schwabe_" run prefix, and its provenance
(data/ocr_provenance/aelius-dionysius.attika-o-no-mata.json) records
run_slug "aelius_dionysius_schwabe"; only the served edition STRING is wrong.

This relabels that ONE file's rows from the shared Migne tag to the Schwabe run
family's served tag, mirroring the sibling. It is a pure relabel: no row text,
locus, urn, source, or license changes; the held Schwabe re-OCR text swap is a
SEPARATE, blocked step (per-fragment Ael.D./Paus. attribution needs Erbse 1950;
see data/corpus_changes/aelius_dionysius_schwabe.reocr-flag.json).

Scope guard: this touches ONLY this single work file plus its single
data/ocr_works.json entry (both matched by the exact urn). The "migne-ocr-qwen36"
tag is legitimately shared by hundreds of other Migne works; those are never
touched. Derived files (data/corpus_editions.json, data/coverage*.json) are NOT
written here: regenerate them with reconcile_corpus_editions.py and
build_coverage_report.py after applying.

The transform is idempotent (a second run is a no-op) and reversible (apply the
inverse mapping to the same file/entry, or git-revert the commit; the audit
records both sha256 hashes and the inverse mapping).

Usage:
  python scripts/relabel_aelius_dionysius_schwabe_edition.py            # dry run
  python scripts/relabel_aelius_dionysius_schwabe_edition.py --apply
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

URN = "aelius-dionysius.attika-o-no-mata"
CTS = "urn:cts:greekLit:tlg1323.tlg001"
RUN_SLUG = "aelius_dionysius_schwabe"
OLD_ED = "migne-ocr-qwen36"
NEW_ED = "qwen36-aelius_dionysius_schwabe-ocr"

CORPUS_FILE = DATA / "corpus" / f"{URN}.jsonl"
OCR_WORKS = DATA / "ocr_works.json"
AUDIT_OUT = DATA / "corpus_changes" / f"{URN}.edition-relabel.json"

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s or ""))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relabel_corpus_file(path: Path, apply: bool) -> dict:
    """Relabel OLD_ED -> NEW_ED on matching rows in one file.

    Preserves byte formatting on unchanged lines; re-serializes changed lines
    with the file's own separator convention (verified round-trip identical).
    Asserts row count, per-row text, and total Greek-char count are unchanged and
    that the ONLY per-row JSON difference is the edition field.
    """
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    out, changed = [], 0
    rows_before = rows_after = 0
    greek_before = greek_after = 0
    texts_before, texts_after = [], []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        obj = json.loads(line)
        rows_before += 1
        texts_before.append(obj.get("text", ""))
        greek_before += greek_chars(obj.get("text", ""))
        if obj.get("edition") == OLD_ED:
            new_obj = dict(obj)
            new_obj["edition"] = NEW_ED
            # only the edition field may differ
            assert {k: v for k, v in obj.items() if k != "edition"} == \
                   {k: v for k, v in new_obj.items() if k != "edition"}, \
                   f"{path}: non-edition field changed on locus {obj.get('locus')!r}"
            new_line = json.dumps(new_obj, ensure_ascii=False)
            out.append(new_line)
            changed += 1
            reparsed = json.loads(new_line)
        else:
            out.append(line)
            reparsed = obj
        rows_after += 1
        texts_after.append(reparsed.get("text", ""))
        greek_after += greek_chars(reparsed.get("text", ""))

    assert rows_after == rows_before, f"{path}: row count {rows_before}->{rows_after}"
    assert texts_after == texts_before, f"{path}: a text field changed"
    assert greek_after == greek_before, f"{path}: Greek chars {greek_before}->{greek_after}"

    new_raw = "\n".join(out) + ("\n" if raw.endswith("\n") else "")
    if apply and changed:
        path.write_text(new_raw, encoding="utf-8")
    return {"rows": rows_before, "greek_chars": greek_before, "relabeled": changed}


def relabel_ocr_works(apply: bool) -> int:
    """Sync the single ocr_works.json entry for this urn (strictly urn-scoped)."""
    if not OCR_WORKS.exists():
        return 0
    works = json.loads(OCR_WORKS.read_text(encoding="utf-8"))
    if not isinstance(works, list):
        return 0
    n = 0
    for w in works:
        if w.get("urn") == URN and (w.get("edition") or "") == OLD_ED:
            w["edition"] = NEW_ED
            n += 1
    assert n <= 1, f"ocr_works.json: expected at most one {URN} entry on {OLD_ED}, found {n}"
    if apply and n:
        OCR_WORKS.write_text(json.dumps(works, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the work file + its ocr_works.json entry (default: dry run)")
    args = ap.parse_args()

    if not CORPUS_FILE.exists():
        print(f"target corpus file missing: {CORPUS_FILE}", file=sys.stderr)
        return 2

    sha_before = sha256(CORPUS_FILE)

    # dry run first to report counts without writing
    dry = relabel_corpus_file(CORPUS_FILE, apply=False)
    ow_n = relabel_ocr_works(apply=False)

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"aelius-dionysius atticist edition relabel [{mode}]")
    print(f"  file: {CORPUS_FILE.relative_to(REPO)}")
    print(f"  {OLD_ED}  ->  {NEW_ED}")
    print(f"  rows in file: {dry['rows']}  relabeled: {dry['relabeled']}  "
          f"greek_chars: {dry['greek_chars']}")
    print(f"  ocr_works.json entries for this urn to sync: {ow_n}")

    if dry["relabeled"] == 0 and ow_n == 0:
        print("nothing to do (already relabeled): no-op")
        return 0
    if not args.apply:
        print("\ndry run only; rerun with --apply to write")
        return 0

    # ---- apply ----
    stats = relabel_corpus_file(CORPUS_FILE, apply=True)
    ow_applied = relabel_ocr_works(apply=True)
    sha_after = sha256(CORPUS_FILE)

    audit = {
        "_meta": {
            "change": "relabel served edition tag off the delivery-side Migne "
                      "mislabel to the Schwabe run family (pure relabel; no row "
                      "text/locus/urn/source/license changed)",
            "work": URN,
            "cts": CTS,
            "run_slug": RUN_SLUG,
            "applied_by": "scripts/relabel_aelius_dionysius_schwabe_edition.py --apply",
            "date": datetime.date.today().isoformat(),
            "reversible": (
                "apply the inverse mapping (NEW->OLD) to the same file + ocr_works "
                "entry, or git-revert the commit / restore the file from the parent "
                f"commit ('git checkout <parent> -- {CORPUS_FILE.relative_to(REPO)}') "
                f"and confirm its sha256 equals old.sha256 ({sha_before})."
            ),
        },
        "old": {
            "edition": OLD_ED,
            "rows": stats["rows"],
            "greek_chars": stats["greek_chars"],
            "sha256": sha_before,
        },
        "new": {
            "edition": NEW_ED,
            "rows": stats["rows"],
            "greek_chars": stats["greek_chars"],
            "sha256": sha_after,
            "rows_relabeled": stats["relabeled"],
        },
        "inverse_mapping": {NEW_ED: OLD_ED},
        "also_synced": {
            "data/ocr_works.json": f"{ow_applied} entry (urn {URN}) edition "
                                   f"{OLD_ED} -> {NEW_ED}",
        },
        "text_swapped": False,
        "evidence": (
            "Every row locus carries the 'aelius_dionysius_schwabe_' run prefix; "
            "provenance run_slug='aelius_dionysius_schwabe' "
            "(data/ocr_provenance/aelius-dionysius.attika-o-no-mata.json); source "
            "scan is Schwabe 1890 (archive.org ailioudionysiouk00dionuoft), an "
            "atticist lexicon, not Migne; the sibling atticist served work "
            "pausanias-attic.attikw-n-o-noma-twn-sunagwgh (tlg1569.tlg001) from the "
            "same run is already tagged 'qwen36-aelius_dionysius_schwabe-ocr'. The "
            "Migne mislabel was flagged in data/corpus_changes/atticist-tlg-id-"
            "keying.json ('the text is Schwabe 1890, not Migne')."
        ),
        "not_done_blocked": (
            "The 676-shared-loci de-dup between the two atticists and the held "
            "Schwabe re-OCR text swap are NOT done here: they need Erbse 1950 "
            "per-fragment attribution (external). See "
            "data/corpus_changes/aelius_dionysius_schwabe.reocr-flag.json."
        ),
        "provenance": "data/ocr_provenance/aelius-dionysius.attika-o-no-mata.json",
        "source": "edition-tag reconciliation vs served-sibling + locus/provenance evidence, "
                  + datetime.date.today().isoformat(),
        "regenerate_after": [
            "scripts/reconcile_corpus_editions.py",
            "scripts/build_coverage_report.py (make sourcing / make all)",
        ],
    }
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    print(f"\napplied. audit -> {AUDIT_OUT.relative_to(REPO)}")

    # idempotence proof
    again = relabel_corpus_file(CORPUS_FILE, apply=False)
    assert again["relabeled"] == 0, "non-idempotent: rerun still finds rows to relabel"
    assert relabel_ocr_works(apply=False) == 0, "non-idempotent: ocr_works still to sync"
    print("rescan clean: relabel is idempotent")
    print("regenerate derived files: reconcile_corpus_editions.py, build_coverage_report.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
