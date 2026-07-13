#!/usr/bin/env python3
"""Ingest the second batch of held dense-class re-OCR works (bucket_staging_held).

The first held batch (scripts/ingest_held_reocr.py, commit 02641c2) keyed the
works that needed only local keying and flagged the ambiguous shared-scan splits.
This tool ingests the four works that were held for a quality-vs-volume review,
now that the review has resolved:

  INGEST (3):
    photius.bibliotheca                      RE-KEY + keep-better (winner=geo)
        The served garbage full-page redo helladius-chrestomathia-photius-bekker-v2
        (50% of loci start with a bled Bekker column number; Greek volume inflated
        by duplicated columns + Latin/apparatus bleed) is deprecated and its urn
        removed. The coherent geometric 2-col re-OCR is installed under the correct
        canonical urn photius.bibliotheca (tlg4040.tlg001). This is DISTINCT from
        photius.lexicon (Naber, tlg4040.tlg029, commit f87a7ec/02641c2): separate
        files, separate work-ids - no collision. make ids revives the Bibliotheca's
        own tombstoned id and retires the helladius id.

    proclus.in-platonis-timaeum-commentaria  COVERAGE add + keep-better
        The served work was essentially vol.1 only (qwen36-proclus_timaeus_v1) with
        two near-empty stub editions for vols 2-3. Replace the v2 (8910-char) and v3
        (2082-char) stubs with the full single-column re-OCR of Diehl Teubner vol.2
        (books II-III, +450477 Greek) and vol.3 (books IV-V, +507429 Greek); keep
        vol.1 untouched. Full 3-volume coverage.

    scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera  keep-better swap
        The served scholia are fragmented OCR (25115 rows, mid-word line breaks,
        dropped accents, un-accented broken blocks; its higher raw Greek/unique-word
        counts are garbage inflation). Replace with the clean, accented, coherent
        single-column re-OCR (11414 rows, mean 49.4 Greek chars/line vs 23.5).

  SKIP (1):
    scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera  LATERAL - left as-is
        The served text is already an adequate full-page redo (Greek 171125 vs the
        candidate's 170532, near-identical quality signals). Swapping buys nothing,
        so the served file is left untouched; a skip record documents the decision.

Every ingest writes a reversible record to data/corpus_changes/ carrying the old
and new sha256 / row / Greek-char counts, the keep-better evidence, a pointer to
data/ocr_provenance, and the git-based reversal path. The pre-ingest served text
is archived offline in the staging tree first. Paths are passed on the command
line, so this committed script hardcodes no local path and names no external
repository.

Usage:
  ingest_held_reocr_batch2.py --staging <bucket_staging_held> --cog <repo_root>
      default: --check (validate + print, write nothing); pass --apply to write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

DATE = "2026-07-13"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")

# Editions of the two near-empty stub volumes the Proclus coverage add replaces.
PROCLUS_STUB_EDITIONS = {"qwen36-proclus_timaeus_v2", "qwen36-proclus_timaeus_v3"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def dump_jsonl(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")


def jsonl_greek(rows: list[dict]) -> int:
    return sum(greek_chars(r.get("text", "")) for r in rows)


def git_head_blob_sha256(cog: Path, rel: str) -> str | None:
    try:
        blob = subprocess.run(["git", "-C", str(cog), "show", f"HEAD:{rel}"],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, type=Path)
    ap.add_argument("--cog", required=True, type=Path)
    ap.add_argument("--apply", action="store_true", help="write files; default is check-only")
    args = ap.parse_args()

    stage, cog = args.staging, args.cog
    corpus = cog / "data" / "corpus"
    changes = cog / "data" / "corpus_changes"
    provdir = cog / "data" / "ocr_provenance"
    do = args.apply
    errors: list[str] = []
    log: list[str] = []

    def head_guard(rel: str, cur: bytes) -> bool:
        """True if the working-tree file still matches git HEAD (no uncommitted edit)."""
        head = git_head_blob_sha256(cog, rel)
        if head is not None and head != sha256_bytes(cur):
            errors.append(f"{rel}: working tree != git HEAD (uncommitted change?)")
            return False
        return True

    # ------------------------------------------------------------------ Photius
    # RE-KEY: deprecate garbage helladius urn, install photius.bibliotheca.
    hel_slug = "helladius-chrestomathia-photius-bekker-v2"
    hel_rel = f"data/corpus/{hel_slug}.jsonl"
    hel_file = corpus / f"{hel_slug}.jsonl"
    ph_rows = read_jsonl(stage / "helladius_chrestomathia_photius_bekker_v2" / "photius.bibliotheca.jsonl")
    ph_bytes = dump_jsonl(ph_rows)
    if not hel_file.exists():
        errors.append(f"{hel_rel}: served helladius file missing")
    else:
        hel_bytes = hel_file.read_bytes()
        if head_guard(hel_rel, hel_bytes):
            old_rows = hel_bytes.decode("utf-8").count("\n")
            old_gc = jsonl_greek([json.loads(l) for l in hel_bytes.decode("utf-8").splitlines() if l.strip()])
            new_rows, new_gc = len(ph_rows), jsonl_greek(ph_rows)
            rec = {
                "_meta": {
                    "change": "re-key + keep-better swap: replace the garbage full-page "
                    "redo (helladius-chrestomathia-photius-bekker-v2) with the coherent "
                    "geometric 2-col re-OCR, correctly keyed as photius.bibliotheca",
                    "work": "photius.bibliotheca",
                    "cts": "urn:cts:greekLit:tlg4040.tlg001",
                    "id": "ogc002810",
                    "former_urn": hel_slug,
                    "run_slug": "helladius_chrestomathia_photius_bekker_v2",
                    "applied_by": "scripts/ingest_held_reocr_batch2.py",
                    "date": DATE,
                    "tier": "keep-better",
                    "reconciliation": "photius.bibliotheca (Bibliotheca, tlg4040.tlg001) "
                    "is DISTINCT from photius.lexicon (Naber Lexicon, tlg4040.tlg029, "
                    "commits f87a7ec/02641c2). No collision: separate corpus files and "
                    "work-ids. make ids revives the Bibliotheca's own tombstoned id "
                    "ogc002810 (retired -> served) and retires the helladius id ogc001680 "
                    "(served -> retired); no new id is minted.",
                    "reversible": "git revert the ingest commit; or restore "
                    f"{hel_rel} and delete data/corpus/photius.bibliotheca.jsonl from the "
                    "parent commit ('git checkout <parent> -- ...'), then re-run 'make ids' "
                    "(ogc002810 re-retires, ogc001680 revives). The pre-ingest garbage text "
                    f"is archived offline as DEPRECATED.{hel_slug}.jsonl in the OCR staging "
                    "area; the new text carries per-line loci.",
                },
                "old": {
                    "edition": "qwen36-helladius_chrestomathia_photius_bekker_v2 (served full-page redo, GARBAGE)",
                    "urn": hel_slug,
                    "rows": old_rows,
                    "greek_chars": old_gc,
                    "sha256": sha256_bytes(hel_bytes),
                    "note": "50% of loci start with a bled Bekker column number; the "
                    "1797580-char Greek volume is inflated by duplicated columns + "
                    "Latin/apparatus bleed.",
                },
                "new": {
                    "edition": "qwen36-helladius_chrestomathia_photius_bekker_v2-masked",
                    "urn": "photius.bibliotheca",
                    "source": "geometric 2-col masked re-OCR (Qwen3.6-27B-FP8, L/R + "
                    "separate bottom-apparatus crops) of Photius Bibliotheca vol.2 "
                    "(Bekker 1825, archive.org bub_gb_NsiGxvHyQY0C)",
                    "rows": new_rows,
                    "greek_chars": new_gc,
                    "sha256": sha256_bytes(ph_bytes),
                },
                "evidence": "keep-better (winner=geo): the coherent 2-col re-OCR reads "
                "cleanly (174.6 Greek chars/line, 9% digit-start lines, 2% bare-diacritic) "
                "where the served full-page redo is garbage (50% column-number-led rows, "
                "1797580 Greek inflated from duplicated columns). Correctly re-keyed to the "
                "canonical Bibliotheca urn. FOLLOW-UP (noted, not done here): extract codex "
                "279 -> Helladius; source Bekker vol.1 for codd. 1-165.",
                "provenance": "data/ocr_provenance/photius.bibliotheca.json",
                "source": "held-works batch-2 re-key ingest (VALIDATION.json + audit_trail.json), " + DATE,
            }
            if do:
                (stage / "helladius_chrestomathia_photius_bekker_v2" /
                 f"DEPRECATED.{hel_slug}.jsonl").write_bytes(hel_bytes)
                (corpus / "photius.bibliotheca.jsonl").write_bytes(ph_bytes)
                subprocess.run(["git", "-C", str(cog), "rm", "-q", hel_rel], check=True)
                (changes / "photius.bibliotheca.reocr-rekey.json").write_text(
                    json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
            log.append(f"{'INGEST' if do else 'CHECK '} RE-KEY  {hel_slug} ({old_rows} rows) "
                       f"-> photius.bibliotheca ({new_rows} rows, {new_gc} greek)")

    # ------------------------------------------------------------------ Proclus
    # COVERAGE: keep vol.1, drop the near-empty v2/v3 stubs, append the full re-OCR.
    pr_slug = "proclus.in-platonis-timaeum-commentaria"
    pr_rel = f"data/corpus/{pr_slug}.jsonl"
    pr_file = corpus / f"{pr_slug}.jsonl"
    v2 = read_jsonl(stage / "proclus_timaeus_v2" / f"{pr_slug}.jsonl")
    v3 = read_jsonl(stage / "proclus_timaeus_v3" / f"{pr_slug}.jsonl")
    if not pr_file.exists():
        errors.append(f"{pr_rel}: served proclus file missing")
    else:
        pr_bytes = pr_file.read_bytes()
        if head_guard(pr_rel, pr_bytes):
            served = read_jsonl(pr_file)
            kept = [r for r in served if r.get("edition") not in PROCLUS_STUB_EDITIONS]
            dropped = len(served) - len(kept)
            new_rows_list = kept + v2 + v3
            new_bytes = dump_jsonl(new_rows_list)
            old_gc = jsonl_greek(served)
            new_gc = jsonl_greek(new_rows_list)
            if dropped != 338:
                errors.append(f"{pr_slug}: dropped {dropped} stub rows (expected 338)")
            rec = {
                "_meta": {
                    "change": "add coverage (masked re-OCR keep-better): install Diehl "
                    "Teubner vols 2-3, replacing the near-empty served v2/v3 stubs; keep vol.1",
                    "work": pr_slug,
                    "cts": "urn:cts:greekLit:tlg4036.tlg010",
                    "id": "ogc003048",
                    "run_slug": "proclus_timaeus_v2 + proclus_timaeus_v3",
                    "applied_by": "scripts/ingest_held_reocr_batch2.py",
                    "date": DATE,
                    "tier": "keep-better",
                    "coverage_addition": True,
                    "reversible": "git revert the ingest commit, or restore "
                    f"{pr_rel} from the parent commit ('git checkout <parent> -- ...') and "
                    "confirm its sha256 equals old.sha256 below. The pre-ingest served file "
                    f"is archived offline as REPLACED.{pr_slug}.jsonl in the OCR staging area.",
                },
                "old": {
                    "edition": "qwen36-proclus_timaeus_v1 (vol.1) + near-empty "
                    "qwen36-proclus_timaeus_v2/v3 stubs",
                    "rows": len(served),
                    "greek_chars": old_gc,
                    "sha256": sha256_bytes(pr_bytes),
                    "note": "v2 stub 186 rows / 8910 Greek and v3 stub 152 rows / 2082 "
                    "Greek were replaced; the 12558-row vol.1 was kept unchanged.",
                },
                "new": {
                    "edition": "qwen36-proclus_timaeus_v2-singlecol + "
                    "qwen36-proclus_timaeus_v3-singlecol (added); qwen36-proclus_timaeus_v1 kept",
                    "source": "geometric single-column re-OCR (Qwen3.6-27B-FP8, whole body "
                    "one crop; running head + page number dropped; bottom apparatus inline) "
                    "of Diehl Teubner vol.2 (books II-III) and vol.3 (books IV-V)",
                    "rows": len(new_rows_list),
                    "greek_chars": new_gc,
                    "sha256": sha256_bytes(new_bytes),
                    "coverage_detail": {
                        "v2_rows": len(v2), "v2_greek_added": jsonl_greek(v2),
                        "v3_rows": len(v3), "v3_greek_added": jsonl_greek(v3),
                        "served_v2_stub_greek": 8910, "served_v3_stub_greek": 2082,
                        "kept": "qwen36-proclus_timaeus_v1 (vol.1) untouched",
                    },
                },
                "evidence": "keep-better: fresh coverage - 957906 Greek chars added (Diehl "
                "vol.2 books II-III +450477, vol.3 books IV-V +507429) replacing 10992-char "
                "stubs, for full 3-volume coverage. Single-column crops read as complete "
                "lines (mean 265.3 / 232.8 Greek chars/line) vs the truncated stubs.",
                "provenance": "data/ocr_provenance/proclus.in-platonis-timaeum-commentaria.json",
                "source": "held-works batch-2 coverage ingest (VALIDATION.json + audit_trail.json), " + DATE,
            }
            if do:
                (stage / "proclus_timaeus_v2" / f"REPLACED.{pr_slug}.jsonl").write_bytes(pr_bytes)
                pr_file.write_bytes(new_bytes)
                (changes / f"{pr_slug}.reocr-coverage.json").write_text(
                    json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
                # provenance: augment the per-urn record with the vol.2/3 coverage add.
                update_proclus_provenance(provdir, stage)
            log.append(f"{'INGEST' if do else 'CHECK '} COVER   {pr_slug}: kept {len(kept)} "
                       f"(dropped {dropped} stubs) + v2 {len(v2)} + v3 {len(v3)} = "
                       f"{len(new_rows_list)} rows, {new_gc} greek")

    # ------------------------------------------------------------------ Aeschylus
    ae_slug = "scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera"
    ae_rel = f"data/corpus/{ae_slug}.jsonl"
    ae_file = corpus / f"{ae_slug}.jsonl"
    ae_rows = read_jsonl(stage / "scholia_aeschylum_depauw_stanley" / f"{ae_slug}.jsonl")
    ae_new = dump_jsonl(ae_rows)
    if not ae_file.exists():
        errors.append(f"{ae_rel}: served aeschylus file missing")
    else:
        ae_bytes = ae_file.read_bytes()
        if head_guard(ae_rel, ae_bytes):
            served = read_jsonl(ae_file)
            old_gc = jsonl_greek(served)
            new_gc = jsonl_greek(ae_rows)
            rec = {
                "_meta": {
                    "change": "replace served text (masked re-OCR keep-better swap)",
                    "work": ae_slug,
                    "cts": "urn:cts:greekLit:tlg5010.tlg001",
                    "id": "ogc003140",
                    "run_slug": "scholia_aeschylum_depauw_stanley",
                    "applied_by": "scripts/ingest_held_reocr_batch2.py",
                    "date": DATE,
                    "tier": "keep-better",
                    "reversible": "git revert the ingest commit, or restore "
                    f"{ae_rel} from the parent commit ('git checkout <parent> -- ...') and "
                    "confirm its sha256 equals old.sha256 below. The pre-ingest served text "
                    f"is archived offline as REPLACED.{ae_slug}.jsonl in the OCR staging area.",
                },
                "old": {
                    "edition": "qwen36-scholia_aeschylum_depauw_stanley (served, fragmented)",
                    "rows": len(served),
                    "greek_chars": old_gc,
                    "sha256": sha256_bytes(ae_bytes),
                    "note": "25115 fragmented rows (mean 23.5 Greek chars/line) with mid-word "
                    "line breaks, dropped accents, and un-accented broken blocks; its higher "
                    "raw Greek (591090) and unique-word (50269) totals are OCR-garbage inflation.",
                },
                "new": {
                    "edition": "qwen36-scholia_aeschylum_depauw_stanley-singlecol",
                    "source": "geometric single-column re-OCR (Qwen3.6-27B-FP8, whole body "
                    "one crop) of De Pauw/Stanley 1745 (archive.org bub_gb_aw-IxD1dCOwC)",
                    "rows": len(ae_rows),
                    "greek_chars": new_gc,
                    "sha256": sha256_bytes(ae_new),
                },
                "evidence": "keep-better: clean, accented, coherent single-column scholia "
                "(11414 rows, mean 49.4 Greek chars/line, bare-diacritic 2.6%) vs the "
                "fragmented served OCR (25115 rows, mean 23.5, bare-diacritic 6.6%). The "
                "served file's larger raw volume is fragmentation inflation, not real text; "
                "1745 archaic typeface caps the OCR ceiling for any method.",
                "provenance": "data/ocr_provenance/scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera.json",
                "source": "held-works batch-2 keep-better ingest (VALIDATION.json + audit_trail.json), " + DATE,
            }
            if do:
                (stage / "scholia_aeschylum_depauw_stanley" /
                 f"REPLACED.{ae_slug}.jsonl").write_bytes(ae_bytes)
                ae_file.write_bytes(ae_new)
                (changes / f"{ae_slug}.reocr-swap.json").write_text(
                    json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
                # provenance: the winning candidate is the single-column run, not the
                # superseded 2-col masked record currently on disk. Install the staged one.
                staged_prov = json.loads(
                    (stage / "scholia_aeschylum_depauw_stanley" /
                     f"{ae_slug}.provenance.json").read_text())
                (provdir / f"{ae_slug}.json").write_text(
                    json.dumps(staged_prov, ensure_ascii=False, indent=1) + "\n")
            log.append(f"{'INGEST' if do else 'CHECK '} SWAP    {ae_slug}: "
                       f"{len(served)} -> {len(ae_rows)} rows, {new_gc} greek")

    # ------------------------------------------------------------------ Aeschines
    # SKIP: lateral swap, served file left UNCHANGED. Record the decision only.
    asc_slug = "scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera"
    asc_file = corpus / f"{asc_slug}.jsonl"
    asc_pre_sha = sha256_bytes(asc_file.read_bytes()) if asc_file.exists() else None
    skip_rec = {
        "_meta": {
            "change": "HELD-DECIDED - not ingested (lateral swap; served text left unchanged)",
            "work": asc_slug,
            "cts": "urn:cts:greekLit:tlg5009.tlg001",
            "run_slug": "schol_aeschin_dindorf",
            "applied_by": "scripts/ingest_held_reocr_batch2.py",
            "date": DATE,
            "status": "reviewed-not-swapped",
        },
        "served_left_unchanged": True,
        "served_sha256": asc_pre_sha,
        "decision": "The served text is already an adequate full-page redo; the "
        "single-column candidate is near-identical in quality and volume (candidate "
        "Greek 170532 vs served 171125, mean line 56.1 vs 55.4, matched digit-start "
        "and bare-diacritic fractions). A swap would be lateral and buys nothing, so "
        "the served file is retained.",
        "candidate_available": "yes - staged and keep-better vs the truncated 2-col "
        "re-OCR, but not vs the served full-page redo; do not swap.",
        "followup": "The shared Dindorf 1852 scan also holds the Isocrates scholia; "
        "carve those out separately if/when needed.",
        "source": "held-works batch-2 review, " + DATE,
    }
    if do:
        (changes / f"{asc_slug}.reocr-skip.json").write_text(
            json.dumps(skip_rec, ensure_ascii=False, indent=2) + "\n")
    log.append(f"{'WROTE ' if do else 'CHECK '} SKIP    {asc_slug}: served unchanged "
               f"(sha {(asc_pre_sha or 'MISSING')[:12]})")

    for line in log:
        print(line)
    n_ingest = sum(1 for l in log if " RE-KEY " in l or " COVER   " in l or " SWAP    " in l)
    print(f"\n{'APPLIED' if do else 'CHECK'}: {n_ingest} ingested (photius re-key + proclus "
          f"coverage + aeschylus swap), 1 skipped (aeschines), {len(errors)} errors.")
    for e in errors:
        print("ERROR:", e)
    return 1 if errors or n_ingest != 3 else 0


def update_proclus_provenance(provdir: Path, stage: Path) -> None:
    """Augment the per-urn Proclus provenance with the vol.2/3 single-column coverage
    add. The top-level (vol.1) fields are kept so build_provenance still links a scan;
    a `volumes` array documents all three Diehl volumes."""
    fp = provdir / "proclus.in-platonis-timaeum-commentaria.json"
    rec = json.loads(fp.read_text())
    v2 = json.loads((stage / "proclus_timaeus_v2" /
                     "proclus.in-platonis-timaeum-commentaria.provenance.json").read_text())
    v3 = json.loads((stage / "proclus_timaeus_v3" /
                     "proclus.in-platonis-timaeum-commentaria.provenance.json").read_text())

    def vol(label: str, src: dict) -> dict:
        return {
            "volume": label,
            "edition": src["edition"],
            "run_slug": src["run_slug"],
            "source_scan": src["source_scan"],
            "render_dpi": src.get("render_dpi"),
            "layout_columns": src.get("layout_handling", {}).get("columns"),
            "layout_method": src.get("layout_handling", {}).get("method"),
            "throughput_pages_per_hr": src.get("throughput", {}).get("pages_per_hr"),
        }

    rec["volumes"] = [
        {
            "volume": "vol.1 (books I; Diehl Teubner t.1, 1903)",
            "edition": rec["edition"],
            "run_slug": rec["run_slug"],
            "source_scan": rec["source_scan"],
            "render_dpi": rec.get("render_dpi"),
            "layout_columns": rec.get("layout_handling", {}).get("columns"),
            "layout_method": rec.get("layout_handling", {}).get("method"),
            "throughput_pages_per_hr": rec.get("throughput", {}).get("pages_per_hr"),
        },
        vol("vol.2 (books II-III; Diehl Teubner t.2, 1904)", v2),
        vol("vol.3 (books IV-V; Diehl Teubner t.3, 1906)", v3),
    ]
    rec["date"] = DATE
    rec["note"] = ("3-volume work (Diehl Teubner I-III). Vol.1 was masked 2-col "
                   "re-OCR; vols 2-3 are the single-column coverage add (batch-2 held "
                   "ingest, 2026-07-13), replacing near-empty stubs. See the `volumes` "
                   "array for per-volume run params. Metadata only; derived reproducibly "
                   "from run params + _timing.json.")
    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    sys.exit(main())
