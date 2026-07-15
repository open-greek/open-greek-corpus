#!/usr/bin/env python3
"""Extend Chrysostom In Genesim homiliae (tlg2062.tlg112) with PG53 homilies 1-41.

The served work joannes-chrysostomus.in-genesim-homiliae-1-67 held only the PG54
half (homilies 42-67, loci pg054_0011..pg054_0206, edition migne-ocr-qwen36) - a
third of the work. Migne's tome LIII (PG 53) carries the first half, "Homiliae in
Genesin" homilies 1-41 (the ELENCHUS of the scanned volume lists that work alone;
the volume ends "FINIS TOMI QUINQUAGESIMI TERTII" after homily 41). This ingest
keys that PG53 Greek to the same work, so it becomes homilies 1-67.

WHY 1-41, NOT 1-34: the scan's own running heads and the seam prove the physical
volume boundary is homily 41/42, not 34/35. In the PG53 OCR the last homily header
is ΟΜΙΛΙΑ ΜΑʹ / HOMILIA XLI (p.375-386) and the text ends with the doxology and
"FINIS TOMI QUINQUAGESIMI TERTII" on p.387; the served PG54 half opens on its
p.11 with homily 42's lemma "Ἐξαναστῶντες δὲ οἱ ἄνδρες" (Gen 18:16, ΟΜΙΛΙΑ ΜΒʹ).
So homilies 35-41 live ONLY in PG53: capping at 34 would drop them. There is no
overlap (PG53 has no homily 42) and no gap. The In Genesim SERMONES (a distinct
work, tlg2062.tlg113) are NOT in this tome - they sit in PG54's tail (p.207+),
already excluded from the served text at p.206 - so nothing here can mis-merge
them.

SOURCE MODEL: the served PG54 half is the Qwen3.6-27B redo (edition
migne-ocr-qwen36), so PG53 is taken from the matching Qwen3.6-27B-FP8 redo of the
same tome (one Greek paragraph per line of the run's *.grc.txt, exactly as the
PG54 half was delivered). The older CLLG/Qwen3VL-8B pass of this tome is NOT used.

Segmentation mirrors the delivered PG54 rows byte-for-byte in shape: one served
record per non-empty Greek line of pgVOL_PAGE.grc.txt over the body page range,
keyed pgVOL_PAGE.k (k 1-indexed within the page), {urn, source, license, edition,
locus, text}. The new pg053_* records are prepended (page order) to the untouched
pg054_* records, so the served bytes of the PG54 half do not change.

A reversible audit is written to data/corpus_changes/ and OCR provenance to
data/ocr_provenance/. Paths are passed on the command line; this committed script
hardcodes no local path and names no external repository.

Usage:
  ingest_chrysostom_ingenesim_pg53.py --ocr-run <pg53_redo_dir> --cog <repo_root> [--apply]
      default: --check (validate + print, write nothing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

DATE = "2026-07-14"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
TAG = re.compile(r"<[^>]*>")           # strip stray OCR markup (<note>, <tab/>, ...)
WS = re.compile(r"\s+")

URN = "joannes-chrysostomus.in-genesim-homiliae-1-67"
CTS = "urn:cts:greekLit:tlg2062.tlg112"
VOL = "pg053"
EDITION = "migne-ocr-qwen36"
SOURCE = "ocr"
LICENSE = "PD"
MODEL = "Qwen/Qwen3.6-27B-FP8"

# Homily body of PG 53 (homilies 1-41). Pages <= 22 are front matter (Google
# notice, general + Greek/Latin title, ELENCHUS/MONITUM, synoptic index); page
# 387 ends the tome ("FINIS TOMI QUINQUAGESIMI TERTII"); pages >= 388 are the
# back index. Both matter regions carry only negligible Greek (guarded below).
BODY_LO, BODY_HI = 23, 387


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def clean_line(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s.strip())).strip()


def git_head_blob_sha256(cog: Path, rel: str) -> str | None:
    try:
        blob = subprocess.run(["git", "-C", str(cog), "show", f"HEAD:{rel}"],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def page_greek_chars(run: Path, page: int) -> int:
    f = run / f"{VOL}_{page:04d}.grc.txt"
    if not f.exists():
        return 0
    return greek_chars(f.read_text(encoding="utf-8", errors="replace"))


def build_rows(run: Path) -> list[dict]:
    """One served record per non-empty Greek line of the body pages."""
    rows: list[dict] = []
    for p in range(BODY_LO, BODY_HI + 1):
        f = run / f"{VOL}_{p:04d}.grc.txt"
        if not f.exists():
            continue
        k = 0
        for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
            text = clean_line(raw)
            if not text or not GREEK.search(text):
                continue
            k += 1
            rows.append({
                "urn": URN,
                "source": SOURCE,
                "license": LICENSE,
                "edition": EDITION,
                "locus": f"{VOL}_{p:04d}.{k}",
                "text": text,
            })
    return rows


def dump_rows(rows: list[dict]) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def provenance_record(run: Path, new_rows: int, new_gc: int, new_tokens: int) -> dict:
    return {
        "urn": URN,
        "cts": CTS,
        "edition": EDITION,
        "run_slug": f"{VOL}_redo",
        "coverage_note": (
            "Two-part OCR delivery for one work. THIS record documents the PG53 "
            "half (homilies 1-41, loci pg053_0023..pg053_0387) added by "
            "scripts/ingest_chrysostom_ingenesim_pg53.py. The PG54 half (homilies "
            "42-67, loci pg054_0011..pg054_0206) was delivered earlier under the "
            "same edition tag; its served bytes are unchanged by this ingest."
        ),
        "source_scan": {
            "edition_printed": "Migne, Patrologia Graeca, tomus LIII (Chrysostom, "
            "Homiliae in Genesin 1-41), reprint Paris",
            "source": "Google Books scan (public domain)",
            "pages_in_run": 397,
            "body_pages_keyed": f"{BODY_LO}-{BODY_HI}",
        },
        "model": MODEL,
        "serving_stack": {
            "engine": "vLLM",
            "quantization": "fp8",
            "reasoning": "thinking disabled",
        },
        "layout_handling": {
            "method": "Migne two-column page, Greek text with facing Latin "
            "translation; the run's Greek-paragraph extraction (*.grc.txt) keeps "
            "the Greek and drops the Latin translation column",
            "columns": 2,
            "running_head_excluded": True,
            "apparatus": "editorial apparatus/variant notes not carried into the "
            "served Greek lines",
            "front_matter": f"pages < {BODY_LO} (Google notice, title, "
            "ELENCHUS/MONITUM, synoptic index) dropped",
            "back_matter": f"pages > {BODY_HI} (back index; the tome ends "
            "'FINIS TOMI QUINQUAGESIMI TERTII' on p.{BODY_HI}) dropped",
        },
        "segmentation": "one served record per non-empty Greek line of "
        "pgNNN_PAGE.grc.txt, keyed pgNNN_PAGE.k (k 1-indexed within the page); "
        "stray OCR markup tags stripped. Same shape as the delivered PG54 half.",
        "work_boundary": {
            "homilies": "1-41 (this PG53 half) + 42-67 (existing PG54 half) = 1-67",
            "seam_evidence": "PG53 last homily header ΟΜΙΛΙΑ ΜΑʹ / HOMILIA XLI "
            "(p.375-386), tome ends 'FINIS TOMI QUINQUAGESIMI TERTII' (p.387); "
            "PG54 opens on homily 42 (Gen 18:16 'Ἐξαναστῶντες δὲ οἱ ἄνδρες'). No "
            "overlap, no gap.",
            "sermones_not_included": "In Genesim SERMONES (tlg2062.tlg113) are not "
            "in this tome; they sit in PG54 p.207+, served separately.",
        },
        "counts": {"rows": new_rows, "greek_chars": new_gc, "tokens": new_tokens},
        "date": DATE,
        "note": "Derived reproducibly by scripts/ingest_chrysostom_ingenesim_pg53.py "
        "from the Qwen3.6-27B-FP8 redo of PG 53. Re-running the script on the same "
        "run reproduces these rows.",
    }


def audit_record(old_rows: int, old_gc: int, old_sha: str,
                 new_pg53_rows: int, new_pg53_gc: int, new_pg53_tokens: int,
                 combined_rows: int, combined_sha: str) -> dict:
    return {
        "_meta": {
            "change": "extend served text (append PG53 homilies 1-41 to the "
            "existing PG54 homilies 42-67, so the work is homilies 1-67)",
            "work": URN,
            "cts": CTS,
            "run_slug": f"{VOL}_redo",
            "applied_by": "scripts/ingest_chrysostom_ingenesim_pg53.py",
            "date": DATE,
            "model_note": "Taken from the Qwen3.6-27B-FP8 redo of PG 53 (matches "
            "the served PG54 edition migne-ocr-qwen36). The older CLLG/Qwen3VL-8B "
            "pass of this tome was deliberately not used.",
            "reversible": (
                "The PG54 half is byte-unchanged: the new pg053_* records are "
                "prepended to the untouched pg054_* records. To revert, drop every "
                "row whose locus starts 'pg053_' from "
                f"data/corpus/{URN}.jsonl (equivalently: git revert the ingest "
                "commit, or restore the file from the parent commit and confirm its "
                "sha256 equals old.sha256 below)."
            ),
        },
        "old": {
            "edition": EDITION,
            "scope": "PG54 half only (homilies 42-67)",
            "rows": old_rows,
            "greek_chars": old_gc,
            "sha256": old_sha,
        },
        "added": {
            "edition": EDITION,
            "scope": "PG53 half (homilies 1-41)",
            "source": f"Qwen3.6-27B-FP8 redo of Migne PG 53, body pages "
            f"{BODY_LO}-{BODY_HI}",
            "locus_prefix": f"{VOL}_",
            "rows": new_pg53_rows,
            "greek_chars": new_pg53_gc,
            "tokens": new_pg53_tokens,
        },
        "new": {
            "scope": "homilies 1-67 (PG53 + PG54)",
            "rows": combined_rows,
            "sha256": combined_sha,
        },
        "evidence": (
            "Seam verified: PG53 ends 'FINIS TOMI QUINQUAGESIMI TERTII' after "
            "homily 41 (ΟΜΙΛΙΑ ΜΑʹ, p.375-387); PG54 opens on homily 42 (Gen 18:16, "
            "served p.11). No pg053_* locus previously present; no other served work "
            "holds pg053 loci. Sermones in Genesim (tlg2062.tlg113) not in this tome."
        ),
        "provenance": f"data/ocr_provenance/{URN}.json",
        "source": "PG53 In Genesim homilies 1-41 keying, " + DATE,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr-run", required=True, type=Path,
                    help="PG53 Qwen3.6 redo output dir (holds pg053_NNNN.grc.txt)")
    ap.add_argument("--cog", required=True, type=Path, help="corpus repo root")
    ap.add_argument("--apply", action="store_true",
                    help="write files; default is check-only")
    args = ap.parse_args()

    run, cog = args.ocr_run, args.cog
    corpus = cog / "data" / "corpus"
    changes = cog / "data" / "corpus_changes"
    prov_dir = cog / "data" / "ocr_provenance"
    rel = f"data/corpus/{URN}.jsonl"
    served = corpus / f"{URN}.jsonl"
    errors: list[str] = []

    if not run.exists():
        errors.append(f"--ocr-run not found: {run}")
    if not served.exists():
        errors.append(f"served file missing: {served}")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    # --- guard: matter regions carry only negligible Greek (body range is right)
    front_gc = sum(page_greek_chars(run, p) for p in range(1, BODY_LO))
    back_gc = sum(page_greek_chars(run, p) for p in range(BODY_HI + 1, 500))
    if front_gc > 1000 or back_gc > 1000:
        errors.append(f"matter guard: front_gc={front_gc} back_gc={back_gc} "
                      "(>1000 Greek chars outside the body range - boundary shifted?)")

    old_bytes = served.read_bytes()
    old_sha = sha256_bytes(old_bytes)
    old_rows = [json.loads(l) for l in old_bytes.decode("utf-8").splitlines() if l.strip()]

    # --- guard: served file matches git HEAD (no uncommitted change)
    head_sha = git_head_blob_sha256(cog, rel)
    if head_sha is not None and head_sha != old_sha:
        errors.append(f"{URN}: served file != git HEAD blob (uncommitted change?)")

    # --- guard: idempotency + the served half really is PG54 only
    prefixes = {r["locus"].split("_")[0] for r in old_rows}
    if any(r["locus"].startswith(f"{VOL}_") for r in old_rows):
        errors.append(f"{URN}: pg053 loci already present (already ingested?)")
    if prefixes != {"pg054"}:
        errors.append(f"{URN}: served loci are not all pg054 (found {sorted(prefixes)})")

    rows = build_rows(run)
    if not rows:
        errors.append("no PG53 rows built (empty run?)")

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    new_gc = sum(greek_chars(r["text"]) for r in rows)
    new_tokens = sum(len(r["text"].split()) for r in rows)
    old_gc = sum(greek_chars(r["text"]) for r in old_rows)
    pg53_bytes = dump_rows(rows)
    combined_bytes = pg53_bytes + old_bytes         # PG53 (page order) then PG54, untouched
    combined_sha = sha256_bytes(combined_bytes)
    combined_rows = len(rows) + len(old_rows)

    pages = sorted({r["locus"].split("_")[1].split(".")[0] for r in rows}, key=int)
    print(f"PG53 rows={len(rows)}  greek_chars={new_gc}  ws_tokens={new_tokens}  "
          f"pages {pages[0]}..{pages[-1]} ({len(pages)} Greek pages)")
    print(f"served PG54 rows={len(old_rows)}  greek_chars={old_gc}")
    print(f"combined rows={combined_rows}  greek_chars={old_gc + new_gc}")
    print(f"matter guard: front_gc={front_gc} back_gc={back_gc}")

    if args.apply:
        served.write_bytes(combined_bytes)
        changes.mkdir(parents=True, exist_ok=True)
        prov_dir.mkdir(parents=True, exist_ok=True)
        (changes / f"{URN}.pg53-append.json").write_text(
            json.dumps(audit_record(len(old_rows), old_gc, old_sha,
                                    len(rows), new_gc, new_tokens,
                                    combined_rows, combined_sha),
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (prov_dir / f"{URN}.json").write_text(
            json.dumps(provenance_record(run, len(rows), new_gc, new_tokens),
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"APPLIED: wrote {rel} (+ audit + provenance)")
    else:
        print("CHECK only (pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
