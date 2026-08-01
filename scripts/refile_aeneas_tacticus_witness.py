#!/usr/bin/env python3
"""Re-file the Aeneas Tacticus OCR witness under its own slug.

data/corpus_secondary/aeneas-philosophy.theophrastus-sive-de-animarum-
immortalitate-et-corporum-resurrectione.jsonl held 996 rows ALL marked
MIS-INGEST: the volume is Aeneas TACTICUS, Poliorcetica ed. Hug (Teubner
1874, scan aeneaecommentar01huggoog), not Aeneas of Gaza's Theophrastus.
The slug has since gained a real Theophrastus primary
(qwen36-aeneasgazaeuset00zachgoog), so the file was dead weight there: the
OCR quality report dropped every row and recorded two meta.skips.

The rows ARE a witness, just of the wrong slug's neighbor:
aeneas-tactics.poliorcetica is served from perseus-grc2, and this OCR is a
different edition of that same work (verified 2026-07-08 by contiguous
verbatim phrases; re-verified here by word-bigram containment, which the
script computes and asserts before moving anything). So the file re-files to
data/corpus_secondary/aeneas-tactics.poliorcetica.jsonl as a real secondary
witness: urn set to the new slug, the delivery-side "migne-ocr-qwen36"
edition mislabel corrected to qwen36-aeneaecommentar01huggoog (the volume is
a Teubner, not Migne; same relabel precedent as
relabel_aelius_dionysius_schwabe_edition.py), and secondary_reason rewritten
to a witness note (the old MIS-INGEST marker would make
build_ocr_quality_report.py drop the rows again). Text, locus, source and
license are untouched; rows are locus-sorted per the corpus_secondary
convention (displace_to_secondary.py).

Audit (data/corpus_changes/):
  aeneas-tactics.poliorcetica.witness-refile.json   change record + evidence
  aeneas-philosophy.theophrastus-...-resurrectione.pre-witness-refile.jsonl
                                                    the source file, verbatim

Reverse: delete data/corpus_secondary/aeneas-tactics.poliorcetica.jsonl and
restore the archived pre-witness-refile.jsonl to its corpus_secondary path
(sha256 of the original is in the audit record).

Idempotent: exits 0 without writing if already applied.

  python3 scripts/refile_aeneas_tacticus_witness.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_ocr_quality_report import (containment, iter_records,  # noqa: E402
                                      greek_tokens, work_bigrams)

SRC_SLUG = ("aeneas-philosophy.theophrastus-sive-de-animarum-immortalitate"
            "-et-corporum-resurrectione")
DST_SLUG = "aeneas-tactics.poliorcetica"
SRC = REPO / "data" / "corpus_secondary" / f"{SRC_SLUG}.jsonl"
DST = REPO / "data" / "corpus_secondary" / f"{DST_SLUG}.jsonl"
PRIMARY = REPO / "data" / "corpus" / f"{DST_SLUG}.jsonl"
CHANGES = REPO / "data" / "corpus_changes"
ARCHIVE = CHANGES / f"{SRC_SLUG}.pre-witness-refile.jsonl"
AUDIT = CHANGES / f"{DST_SLUG}.witness-refile.json"

DATE = "2026-08-01"
OLD_EDITION = "migne-ocr-qwen36"
NEW_EDITION = "qwen36-aeneaecommentar01huggoog"
# Identity guard: most of the served perseus text must be present in the
# witness volume, or the re-file premise is wrong and nothing is written.
MIN_TEI_IN_OCR = 0.5

NEW_REASON = (
    "displaced witness of the served perseus-grc2 text: Qwen3.6 OCR of "
    "Aeneas Tacticus, Poliorcetica ed. Hug (Teubner 1874, scan "
    "aeneaecommentar01huggoog), a different edition of the same work, "
    "including Hug's Latin prolegomena, apparatus criticus and index "
    "paratext. Wrongly filed under " + SRC_SLUG + " until " + DATE +
    "; re-filed by scripts/refile_aeneas_tacticus_witness.py (audit: "
    "data/corpus_changes/" + DST_SLUG + ".witness-refile.json)."
)


def n_greek(records: list[dict]) -> int:
    return sum(len(greek_tokens(r.get("text") or "")) for r in records)


def main() -> None:
    if not SRC.exists():
        if DST.exists() and AUDIT.exists():
            print("already applied; nothing to do")
            return
        raise SystemExit(f"ABORT: {SRC} missing and no applied state found")
    if DST.exists():
        raise SystemExit(f"ABORT: {DST} already exists; merge is not "
                         f"expected for this re-file, inspect by hand")

    raw = SRC.read_text(encoding="utf-8")
    rows = list(iter_records(SRC))
    not_marked = [r for r in rows
                  if "mis-ingest" not in (r.get("secondary_reason") or "").lower()]
    if not_marked:
        raise SystemExit(f"ABORT: {len(not_marked)} rows lack the MIS-INGEST "
                         f"marker; the file is not the expected all-displaced set")
    bad = [r for r in rows if r.get("urn") != SRC_SLUG
           or r.get("edition") != OLD_EDITION or r.get("rank") != "secondary"]
    if bad:
        raise SystemExit(f"ABORT: {len(bad)} rows deviate from the expected "
                         f"urn/edition/rank profile")

    primary = list(iter_records(PRIMARY))
    if not primary:
        raise SystemExit(f"ABORT: served primary {PRIMARY} missing or empty")
    p_grams, s_grams = work_bigrams(primary), work_bigrams(rows)
    tei_in_ocr = containment(p_grams, s_grams)
    ocr_in_tei = containment(s_grams, p_grams)
    if tei_in_ocr is None or tei_in_ocr < MIN_TEI_IN_OCR:
        raise SystemExit(f"ABORT: served-text containment in the witness is "
                         f"{tei_in_ocr}, below {MIN_TEI_IN_OCR}; identity not "
                         f"confirmed, nothing written")

    old_reason = rows[0]["secondary_reason"]
    moved = []
    for r in rows:
        nr = dict(r)
        nr["urn"] = DST_SLUG
        nr["edition"] = NEW_EDITION
        nr["secondary_reason"] = NEW_REASON
        moved.append(nr)
    moved.sort(key=lambda r: str(r.get("locus", "")))

    CHANGES.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(raw, encoding="utf-8")
    DST.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                           for r in moved), encoding="utf-8")
    SRC.unlink()

    audit = {
        "_meta": {
            "change": "re-file the whole displaced OCR witness from the "
                      "wrong slug to the work it actually transmits",
            "from_file": f"data/corpus_secondary/{SRC_SLUG}.jsonl (removed)",
            "to_file": f"data/corpus_secondary/{DST_SLUG}.jsonl (created)",
            "work": DST_SLUG,
            "tlg": "tlg0058.tlg001",
            "date": DATE,
            "applied_by": "scripts/refile_aeneas_tacticus_witness.py",
            "reversible": "delete data/corpus_secondary/" + DST_SLUG +
                          ".jsonl and restore data/corpus_changes/" +
                          SRC_SLUG + ".pre-witness-refile.jsonl to "
                          "data/corpus_secondary/" + SRC_SLUG + ".jsonl "
                          "(verbatim copy of the removed file; sha256 below)",
        },
        "rows_moved": len(moved),
        "greek_tokens": n_greek(rows),
        "old": {
            "urn": SRC_SLUG,
            "edition": OLD_EDITION,
            "secondary_reason": old_reason,
            "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        },
        "new": {
            "urn": DST_SLUG,
            "edition": NEW_EDITION,
            "secondary_reason": NEW_REASON,
        },
        "edition_relabel": {
            "note": "delivery-side Migne family mislabel corrected to the "
                    "actual scan; the volume is Hug's Teubner 1874, not "
                    "Migne PG (precedent: "
                    "relabel_aelius_dionysius_schwabe_edition.py)",
            "inverse_mapping": {NEW_EDITION: OLD_EDITION},
        },
        "evidence": {
            "prior": "MIS-INGEST note of 2026-07-08 on every row: contiguous "
                     "phrases verbatim in perseus aeneas-tactics.poliorcetica; "
                     "misses are Hug apparatus-criticus paratext",
            "computed": {
                "method": "normalized word-bigram containment, "
                          "build_ocr_quality_report.py functions",
                "agreement_tei_in_ocr": tei_in_ocr,
                "agreement_ocr_in_tei": ocr_in_tei,
                "n_bigrams_tei": sum(p_grams.values()),
                "n_bigrams_ocr": sum(s_grams.values()),
                "threshold_tei_in_ocr": MIN_TEI_IN_OCR,
            },
            "conclusion": "the rows are a displaced witness of the served "
                          "Aeneas Tacticus Poliorcetica, not junk "
                          "duplication: no other copy of the Hug OCR exists "
                          "in the repo and the served primary is a different "
                          "source (perseus TEI)",
        },
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    print(f"re-filed {len(moved)} rows {SRC_SLUG} -> {DST_SLUG}\n"
          f"  tei_in_ocr {tei_in_ocr}  ocr_in_tei {ocr_in_tei}\n"
          f"  archive {ARCHIVE.relative_to(REPO)}\n"
          f"  audit   {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
