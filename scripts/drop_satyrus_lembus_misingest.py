#!/usr/bin/env python3
"""Drop the 47 wrong-work rows from the Satyrus secondary witness.

data/corpus_secondary/satyrus.vita-euripidis-p-oxy-9-1176.jsonl mixed two row
populations: 89 rows of the gen-1 FHG vol. 3 read of the actual P.Oxy 9.1176
Satyros pages (superseded by DFHG, a real same-edition witness of the served
qwen36 primary) and 47 rows marked "rows mis-ingested ...": fhg_vol3
pp. 177-196, which are Heraclides Lembus (Excerpta Politiarum) and Posidonius,
not Satyrus at all. Those 47 rows are not a witness of anything served under
this slug (their content was ceded to the fhg-vol3 placeholder in the
2026-07-10 crosswork dedup, with a row backup in the upstream OCR pipeline),
so the OCR quality report dropped them every run and recorded a meta.skip.
This script removes them for good; the 89 real witness rows stay untouched.

Selection is exactly the quality report's marker: "mis-ingest" in
secondary_reason, case-insensitive (build_ocr_quality_report.py
secondary_profile), asserted to match the expected Heraclides Lembus reason
and row count before anything is written. Kept rows pass through as their
original raw lines, byte-identical.

Audit (data/corpus_changes/):
  satyrus.vita-euripidis-p-oxy-9-1176.lembus-misingest-drop.json  change record
  satyrus.vita-euripidis-p-oxy-9-1176.pre-lembus-misingest-drop.jsonl
                                                    the whole pre-change file

Reverse: restore the archived pre-lembus-misingest-drop.jsonl to its
corpus_secondary path (sha256 of the original is in the audit record).

Idempotent: exits 0 without writing if no marked rows remain.

  python3 scripts/drop_satyrus_lembus_misingest.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLUG = "satyrus.vita-euripidis-p-oxy-9-1176"
TARGET = REPO / "data" / "corpus_secondary" / f"{SLUG}.jsonl"
CHANGES = REPO / "data" / "corpus_changes"
ARCHIVE = CHANGES / f"{SLUG}.pre-lembus-misingest-drop.jsonl"
AUDIT = CHANGES / f"{SLUG}.lembus-misingest-drop.json"

DATE = "2026-08-01"
EXPECTED_DROPS = 47
EXPECTED_REASON_SNIPPET = "actually Heraclides Lembus"


def main() -> None:
    raw = TARGET.read_text(encoding="utf-8")
    lines = [l for l in raw.splitlines() if l.strip()]
    keep_lines: list[str] = []
    drop_lines: list[str] = []
    drop_rows: list[dict] = []
    for line in lines:
        r = json.loads(line)
        if "mis-ingest" in (r.get("secondary_reason") or "").lower():
            drop_lines.append(line)
            drop_rows.append(r)
        else:
            keep_lines.append(line)

    if not drop_rows:
        if AUDIT.exists():
            print("already applied; nothing to do")
            return
        raise SystemExit("ABORT: no marked rows found and no applied state")
    if len(drop_rows) != EXPECTED_DROPS:
        raise SystemExit(f"ABORT: expected {EXPECTED_DROPS} marked rows, "
                         f"found {len(drop_rows)}; inspect before dropping")
    off_profile = [r for r in drop_rows
                   if EXPECTED_REASON_SNIPPET not in (r.get("secondary_reason") or "")]
    if off_profile:
        raise SystemExit(f"ABORT: {len(off_profile)} marked rows do not carry "
                         f"the Heraclides Lembus reason; inspect before dropping")

    CHANGES.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_text(raw, encoding="utf-8")
    TARGET.write_text("".join(l + "\n" for l in keep_lines), encoding="utf-8")

    stems = sorted({str(r.get("locus", "")).rsplit(".", 1)[0] for r in drop_rows})
    audit = {
        "_meta": {
            "change": "remove the wrong-work rows (Heraclides Lembus / "
                      "Posidonius, fhg_vol3 pp. 177-196) from the Satyrus "
                      "secondary witness; the 89 true witness rows stay",
            "work": SLUG,
            "tlg": "tlg0608.tlg001",
            "date": DATE,
            "applied_by": "scripts/drop_satyrus_lembus_misingest.py",
            "reversible": "restore data/corpus_changes/" + SLUG +
                          ".pre-lembus-misingest-drop.jsonl to "
                          "data/corpus_secondary/" + SLUG + ".jsonl "
                          "(verbatim copy of the pre-change file; sha256 below)",
        },
        "before": {"rows": len(lines),
                   "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()},
        "after": {"rows": len(keep_lines)},
        "rows_removed": len(drop_rows),
        "removed_page_stems": stems,
        "removed_reason": drop_rows[0].get("secondary_reason"),
        "evidence": "the rows' own secondary_reason (2026-07-10 crosswork "
                    "dedup): content is Heraclides Lembus, Excerpta "
                    "Politiarum + Posidonius, not the P.Oxy 9.1176 Satyros; "
                    "byte-identical copy ceded to the fhg-vol3 placeholder, "
                    "row backup in the upstream OCR pipeline's "
                    "data/corrections/crosswork_dedup/. Not a witness of "
                    "this work, so build_ocr_quality_report.py excluded "
                    "them every run (meta.skips)",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    print(f"dropped {len(drop_rows)} rows from {SLUG} "
          f"({len(keep_lines)} witness rows stay)\n"
          f"  archive {ARCHIVE.relative_to(REPO)}\n"
          f"  audit   {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
