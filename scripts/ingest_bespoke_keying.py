#!/usr/bin/env python3
"""Bespoke keying follow-up for the held masked re-OCR works.

scripts/ingest_held_reocr.py (commit 02641c2) ingested the held works that
needed only a straight page-carve, and FLAGGED four items that needed a genuine
content split or reconciliation. This tool resolves the two that ARE recoverable
from evidence on disk, and re-states the two that are not with the conclusive
evidence gathered here.

Resolved
--------
2. BUSSEMAKER Didot scan (public_id scholiaintheocri00buss) - the served
   scholia-in-oppianum (tlg5032.tlg001) conflated FOUR sections of the whole
   698-page scan under the Cynegetica-scholia urn. The masked re-OCR is carved by
   printed-section boundary (each boundary is a caps section header in the OCR):

     pp. 10-192  Theocritus scholia          tlg5038.tlg001  (replace served, keep-better)
     pp.195-264  Nicander scholia            DROP - COG already serves tlg5031.tlg001/002
                                             from First1K (a curated TEI edition, better than
                                             this OCR; a parallel OCR work would also break
                                             the id-layer's "exactly one work per TLG" rule).
     pp.265-281  Oppian Cynegetica scholia   tlg5032.tlg001  (the now-CLEAN scholia-in-oppianum)
     pp.282-385  Oppian Halieutica scholia   tlg5032.tlg002  (NEW work, registered)
     pp.386-692  Eutecnius paraphrases +     holding id ocr.oppian_bussemaker_paraphrases
                 Oppian poem + index         (FLAGGED - Eutecnius Halieutica paraphrase
                                             tlg0752.tlg005 + Cynegetica paraphrase tlg0752.tlg003
                                             + the already-served Oppian poem + a final index are
                                             interleaved; a canonical carve needs a bespoke pass,
                                             so the Greek is preserved under a holding id, not
                                             mis-keyed onto a scholia urn).

   NB the earlier flag guessed a "new Nicander work (tlg5030)"; tlg5030 is
   SCHOLIA IN LYCOPHRONEM. The Nicander scholia are tlg5031 and already served,
   so no Nicander work is minted - the genuinely new work here is the Oppian
   Halieutica scholia (tlg5032.tlg002).

3. DINDORF Demosthenes vol.8 (operaexrecension08demouoft) - Ulpian's Olynthiac +
   Philippic prolegomena (tlg2604.tlg001) are a contiguous front block, printed
   pp.53-69 of the scan (header "ΟΥΛΠΙΑΝΟΥ ..." at p53; the Life of Demosthenes /
   scholia proper begin p70 "ΒΙΟΣ ΔΗΜΟΣΘΕΝΟΥΣ"). The served ulpianus file already
   holds that block; the bug is that scholia-in-demosthenem ALSO carries pp.53-69
   (667 rows), double-covering it. Fix = dedup: drop pp.53-69 from
   scholia-in-demosthenem so the block lives only under ulpianus. The served
   ulpianus OCR (27053 Greek chars on pp.53-69) is richer than the masked re-OCR
   of the same pages (23072), so ulpianus is left on its better served text.

Still flagged (served text left unchanged; a split would mis-key)
----------------------------------------------------------------
1. SCHWABE atticists - the Schwabe 1890 edition prints the Aelii Dionysii ET
   Pausaniae fragments as ONE interleaved alphabetical series (fragment numbers
   1..451 run monotonically across the whole fragment section pp.99-276, there is
   no mid-book Pausanias section header, and BOTH atticists are cited throughout
   the range). Per-fragment Ael.D./Paus. attribution is therefore not recoverable
   from page ranges or reliably from the OCR text - it needs Erbse 1950. The two
   served files are two overlapping OCR passes of this same un-splittable series,
   so the double-coverage cannot be resolved without that attribution.

4. WALZ Rhetores Graeci v1/v4/v5/v7pt2/v9 - each bound volume is an anthology of
   many rhetorical treatises. The OCR section headers are present but garbled and
   numerous, and no curated per-volume TOC (printed->scan page map) is on disk, so
   a confident per-treatise canonical split is not establishable here. The
   keep-better OCR text already sits under the ocr.walz_* holding ids.

Every resolved change writes a reversible record to data/corpus_changes/ with the
old+new sha256 / row / Greek-char counts, the boundary evidence, a provenance
pointer and the git reversal path. Staging paths are passed on the command line;
this committed script hardcodes no local path and names no external repository.

Usage:
  ingest_bespoke_keying.py --staging <bucket_staging_dir> --cog <repo_root> [--apply]
      default: --check (validate + print, write nothing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DATE = "2026-07-13"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
PAGE_RE = re.compile(r"_(\d{3,4})\.\d+$")

# ---- Bussemaker Didot carve (inclusive printed-section page boundaries) --------
OPP_STAGE = ("scholia_oppianum_bussemaker_didot",
             "scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora.jsonl")
OPP_EDITION = "qwen36-scholia_oppianum_bussemaker_didot-masked"
# (page_lo, page_hi, action, urn, cts)
#   action: "replace" existing served file | "new" work | "holding" | "drop"
OPP_PARTS = [
    (10, 192, "replace", "scholia-in-theocritum.scholia-vetera-et-recentiora",
     "urn:cts:greekLit:tlg5038.tlg001"),
    (195, 264, "drop", "scholia-in-nicandrum (served from First1K, tlg5031)", None),
    (265, 281, "replace", "scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora",
     "urn:cts:greekLit:tlg5032.tlg001"),
    (282, 385, "new", "scholia-in-oppianum.scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora",
     "urn:cts:greekLit:tlg5032.tlg002"),
    (386, 692, "holding", "ocr.oppian_bussemaker_paraphrases", None),
]
# crosswalk row for the newly-served Halieutica scholia work
OPP_HAL_SLUG = "scholia-in-oppianum.scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora"
OPP_HAL_CROSSWALK = {
    "cts": "urn:cts:greekLit:tlg5032.tlg002",
    "tlg": "tlg5032.tlg002",
    "author_slug": "scholia-in-oppianum",
    "title": "Scholia et glossae in halieutica (scholia vetera et recentiora)",
}
# holding-id pseudo-author + work for the paraphrase tail
TAIL_SLUG = "ocr.oppian_bussemaker_paraphrases"
TAIL_AUTHOR_SLUG = "oppian-bussemaker-paraphrases"
TAIL_PSEUDO_AUTHOR = {
    "name": "Oppian paraphrases (Bussemaker Didot)",
    "aliases": {},
    "note": "Collective holding label for the paraphrase/index tail (pp.386-692) of "
            "Bussemaker's Didot scholia volume (public scan scholiaintheocri00buss): "
            "Eutecnius' paraphrase of Oppian's Halieutica (tlg0752.tlg005) and Cynegetica "
            "(tlg0752.tlg003), the Oppian poem text (already served under oppianus-* urns) and "
            "a final alphabetic index, interleaved. Per-work canonical split is a future pass; "
            "kept under a holding id so the Greek is preserved without mis-keying onto a scholia urn.",
}
TAIL_PSEUDO_WORK = {
    "author": TAIL_AUTHOR_SLUG,
    "title": "Oppian Halieutica/Cynegetica paraphrases + index (Bussemaker Didot tail, unsplit)",
    "slug": "oppian-bussemaker-paraphrases.paraphrase-tail",
    "tags": {"genre": ["paraphrase", "commentary"]},
    "attribution": "anthology (collective holding label)",
    "evidence": [
        "carved pp.386-692 of the Bussemaker Didot scholia scan; headers "
        "'ΟΠΠΙΑΝΟΥ ΑΛΙΕΥΤΙΚΩΝ ΕΞΗΓΗΣΙΣ' (p386) and 'ΕΥΤΕΚΝΙΟΥ ΠΑΡΑΦΡΑΣΙΣ ΕΙΣ ΚΥΝΗΓΕΤΙΚΑ' (p392); "
        "final alphabetic index with dotted leaders pp.~685-692",
        "edition: Bussemaker/Duebner, Scholia et paraphrases in Nicandrum et Oppianum (Didot 1849)",
    ],
}

# ---- Dindorf Demosthenes vol.8 dedup ------------------------------------------
DEM_SLUG = "scholia-in-demosthenem.scholia-demosthenem-dindorf-v8"
ULP_SLUG = "ulpianus.prolegomena-in-demosthenis-orationes-olynthiacas-et-philippicas"
ULP_PAGES = (53, 69)  # Ulpian Olynthiac+Philippic prolegomena block -> belongs to tlg2604.tlg001


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def page_of(locus: str) -> int:
    m = PAGE_RE.search(locus or "")
    return int(m.group(1)) if m else -1


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def dump_jsonl(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")


def stats(rows: list[dict]) -> tuple[int, int]:
    return len(rows), sum(greek_chars(r.get("text", "")) for r in rows)


def rekey(row: dict, urn: str, cts: str | None, edition: str) -> dict:
    nr = dict(row)
    nr["urn"] = urn
    if cts:
        nr["cts"] = cts
    else:
        nr.pop("cts", None)
    nr["edition"] = edition
    return nr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, type=Path)
    ap.add_argument("--cog", required=True, type=Path)
    ap.add_argument("--apply", action="store_true", help="write files; default is check-only")
    args = ap.parse_args()

    stage, cog = args.staging, args.cog
    corpus = cog / "data" / "corpus"
    changes = cog / "data" / "corpus_changes"
    do = args.apply
    log: list[str] = []
    errors: list[str] = []

    def archive(slug_dir: str, name: str, data: bytes):
        if do:
            (stage / slug_dir).mkdir(parents=True, exist_ok=True)
            (stage / slug_dir / name).write_bytes(data)

    def write_corpus(slug: str, rows: list[dict]):
        if do:
            (corpus / f"{slug}.jsonl").write_bytes(dump_jsonl(rows))

    def write_change(name: str, rec: dict):
        if do:
            (changes / name).write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")

    # =====================================================================
    # ITEM 2 - Bussemaker Didot 4-way carve (+ Nicander drop)
    # =====================================================================
    masked = read_jsonl(stage / OPP_STAGE[0] / OPP_STAGE[1])
    src_sha = sha256_bytes(dump_jsonl(masked))
    buckets: dict[str, list[dict]] = {}
    dropped_rows = dropped_gk = 0
    for r in masked:
        p = page_of(r.get("locus", ""))
        for lo, hi, action, urn, cts in OPP_PARTS:
            if lo <= p <= hi:
                if action == "drop":
                    dropped_rows += 1
                    dropped_gk += greek_chars(r.get("text", ""))
                else:
                    buckets.setdefault(urn, []).append(rekey(r, urn, cts, OPP_EDITION))
                break

    for lo, hi, action, urn, cts in OPP_PARTS:
        if action == "drop":
            log.append(f"  DROP  pp.{lo}-{hi}  Nicander (served via First1K tlg5031): "
                       f"{dropped_rows} rows / {dropped_gk} greek not ingested")
            continue
        rows = buckets.get(urn, [])
        new_rows_n, new_gk = stats(rows)
        served = corpus / f"{urn}.jsonl"
        old_bytes = served.read_bytes() if served.exists() else b""
        old_sha = sha256_bytes(old_bytes) if old_bytes else None
        old_rows_n = old_bytes.count(b"\n") if old_bytes else 0
        old_gk = sum(greek_chars(json.loads(l).get("text", ""))
                     for l in old_bytes.decode("utf-8").splitlines() if l.strip()) if old_bytes else 0
        if action == "replace" and not served.exists():
            errors.append(f"{urn}: expected served file to replace, missing")
            continue
        if action in ("new", "holding") and served.exists():
            errors.append(f"{urn}: expected NEW file but one already exists")
            continue
        if old_bytes:
            archive(OPP_STAGE[0], f"REPLACED.{urn}.jsonl", old_bytes)
        write_corpus(urn, rows)
        kind = {"replace": "reocr-swap", "new": "reocr-split", "holding": "reocr-holding"}[action]
        rec = {
            "_meta": {
                "change": {"replace": "replace served text (masked re-OCR keep-better swap; "
                                       "carved from the shared Bussemaker Didot scan by printed-section boundary)",
                           "new": "register NEW work carved from the shared Bussemaker Didot scan",
                           "holding": "preserve the paraphrase/index tail under a holding id (canonical split flagged)"}[action],
                "work": urn, "cts": cts, "run_slug": OPP_STAGE[0],
                "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE,
                "carved_pages": f"{lo}-{hi}",
                "shared_scan": "Bussemaker Didot scholia scan (public scholiaintheocri00buss): "
                               "Theocritus scholia pp.10-192 | Nicander scholia pp.195-264 (dropped, "
                               "served via First1K) | Oppian Cynegetica scholia pp.265-281 | Oppian "
                               "Halieutica scholia pp.282-385 | Eutecnius paraphrases+poem+index pp.386-692",
                "reversible": "git revert the ingest commit, or restore data/corpus/"
                              f"{urn}.jsonl from the parent commit; the pre-ingest served text (when "
                              "replaced) is archived offline as REPLACED.*.jsonl in the OCR staging area.",
            },
            "old": {"edition": "served corpus text (pre re-OCR)" if old_bytes else None,
                    "rows": old_rows_n, "greek_chars": old_gk, "sha256": old_sha},
            "new": {"edition": OPP_EDITION,
                    "source": "masked-column re-OCR (Qwen3.6-27B-FP8, geometric L/R + apparatus crops)",
                    "rows": new_rows_n, "greek_chars": new_gk,
                    "sha256": sha256_bytes(dump_jsonl(rows))},
            "evidence": (f"carved pp.{lo}-{hi} of the Bussemaker scan; "
                         f"rows {old_rows_n}->{new_rows_n}, greek {old_gk}->{new_gk}. "
                         + ("clean Cynegetica-only after de-conflation." if urn.endswith("cynegetica-scholia-vetera-et-recentiora")
                            else "keep-better vs served." if action == "replace"
                            else "new canonical work." if action == "new"
                            else "holding id; canonical Eutecnius/poem/index split flagged.")),
            "source_masked_jsonl_sha256": src_sha,
            "provenance": f"data/ocr_provenance/{urn}.json",
        }
        write_change(f"{urn}.{kind}.json", rec)
        log.append(f"  {action.upper():8} pp.{lo}-{hi}  {urn}  rows {old_rows_n}->{new_rows_n} greek {old_gk}->{new_gk}")

    # --- crosswalk: add the Halieutica-scholia work ---
    # tlg_crosswalk.json is serialized with indent=0 and NO trailing newline;
    # match it byte-for-byte so only the new key diffs (no whole-file reformat).
    tc_path = cog / "data" / "tlg_crosswalk.json"
    tc = json.loads(tc_path.read_text(encoding="utf-8"))
    if OPP_HAL_SLUG not in tc:
        if do:
            tc[OPP_HAL_SLUG] = OPP_HAL_CROSSWALK
            tc_path.write_text(json.dumps(tc, ensure_ascii=False, indent=0), encoding="utf-8")
        log.append(f"  crosswalk += {OPP_HAL_SLUG} -> {OPP_HAL_CROSSWALK['tlg']}")

    # --- pseudo-author for the holding-id tail ---
    # pseudo_author_attributions.json is hand-formatted (compact inline dicts for
    # short values), so a full json.dumps would reformat the whole file. Splice the
    # two new entries in as text at 2-space indent, leaving every existing entry
    # byte-for-byte unchanged.
    pa_path = cog / "data" / "pseudo_author_attributions.json"
    pa_text = pa_path.read_text(encoding="utf-8")
    pa = json.loads(pa_text)

    def _block(key: str, value: dict) -> str:
        """Render {key: value} as a 2-space-indented entry body (no outer braces)."""
        lines = json.dumps({key: value}, ensure_ascii=False, indent=1).splitlines()
        return "\n".join(" " + l for l in lines[1:-1])  # drop outer { }, shift 1->2 spaces

    changed_pa = False
    if TAIL_AUTHOR_SLUG not in pa["authors"]:
        anchor = '\n },\n "works": {'  # ' },' closes the authors object
        assert pa_text.count(anchor) == 1
        pa_text = pa_text.replace(anchor, ",\n" + _block(TAIL_AUTHOR_SLUG, TAIL_PSEUDO_AUTHOR) + anchor, 1)
        changed_pa = True
    if TAIL_SLUG not in pa["works"]:
        anchor = "\n }\n}\n"  # ' }' closes the works object at EOF
        assert pa_text.endswith(anchor)
        pa_text = pa_text[:-len(anchor)] + ",\n" + _block(TAIL_SLUG, TAIL_PSEUDO_WORK) + anchor
        changed_pa = True
    if changed_pa:
        json.loads(pa_text)  # guard: still valid JSON
        if do:
            pa_path.write_text(pa_text, encoding="utf-8")
        log.append(f"  pseudo-author += {TAIL_AUTHOR_SLUG}; pseudo-work += {TAIL_SLUG}")

    # --- item-2 outcome flag (resolution + narrowed tail flag) ---
    write_change("scholia_oppianum_bussemaker_didot.reocr-flag.json", {
        "_meta": {"change": "RESOLVED (4-way canonical carve) with a narrowed residual flag",
                  "run_slug": "scholia_oppianum_bussemaker_didot",
                  "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE,
                  "status": "resolved-except-tail"},
        "resolved": {
            "scholia-in-theocritum.scholia-vetera-et-recentiora (tlg5038.tlg001)": "pp.10-192, replaced served (keep-better)",
            "scholia-in-nicandrum (tlg5031.tlg001/002)": "pp.195-264 DROPPED - already served from First1K TEI",
            "scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora (tlg5032.tlg001)": "pp.265-281, now clean Cynegetica-only",
            "scholia-in-oppianum.scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora (tlg5032.tlg002)": "pp.282-385, NEW work registered",
        },
        "residual_flag": {
            "work": TAIL_SLUG,
            "reason": "pp.386-692 interleave Eutecnius' Halieutica paraphrase (tlg0752.tlg005), "
                      "Cynegetica paraphrase (tlg0752.tlg003), the Oppian poem (already served under "
                      "oppianus-* urns) and a final alphabetic index; a canonical per-work carve needs a "
                      "bespoke pass. Held under the holding id ocr.oppian_bussemaker_paraphrases so the "
                      "Greek is preserved without mis-keying.",
            "recommendation": "manual: split pp.386-391 (Halieutica paraphrase) / pp.392-~684 (Cynegetica "
                              "paraphrase + poem) / pp.~685-692 (index); dedup the poem against oppianus-apamensis.cynegetica.",
        },
        "correction_of_prior_flag": "the earlier flag guessed a new Nicander work at tlg5030; tlg5030 is "
                                    "SCHOLIA IN LYCOPHRONEM. Nicander scholia are tlg5031 and already served, so "
                                    "no Nicander work is minted; the new work is Oppian Halieutica scholia tlg5032.tlg002.",
        "source": "bespoke keying follow-up, " + DATE,
    })

    # =====================================================================
    # ITEM 3 - Dindorf Demosthenes vol.8: dedup Ulpian block out of the scholia
    # =====================================================================
    dem = corpus / f"{DEM_SLUG}.jsonl"
    dem_old = dem.read_bytes()
    dem_rows = [json.loads(l) for l in dem_old.decode("utf-8").splitlines() if l.strip()]
    lo, hi = ULP_PAGES
    kept = [r for r in dem_rows if not (lo <= page_of(r.get("locus", "")) <= hi)]
    removed = [r for r in dem_rows if lo <= page_of(r.get("locus", "")) <= hi]
    ulp = corpus / f"{ULP_SLUG}.jsonl"
    ulp_rows_n, ulp_gk = stats(read_jsonl(ulp)) if ulp.exists() else (0, 0)
    if not ulp.exists():
        errors.append(f"{ULP_SLUG}: served ulpianus file missing (needed as the Ulpian block's home)")
    kept_bytes = dump_jsonl(kept)
    archive(OPP_STAGE[0], "..", b"") if False else None
    if do:
        (stage / "scholia_demosthenem_dindorf_v8").mkdir(parents=True, exist_ok=True)
        (stage / "scholia_demosthenem_dindorf_v8" / f"REPLACED.{DEM_SLUG}.jsonl").write_bytes(dem_old)
        dem.write_bytes(kept_bytes)
    write_change(f"{DEM_SLUG}.reocr-dedup.json", {
        "_meta": {"change": "dedup: remove the Ulpian Olynthiac+Philippic prolegomena block "
                            f"(printed pp.{lo}-{hi}) from scholia-in-demosthenem so it lives only under ulpianus",
                  "work": DEM_SLUG, "cts": "urn:cts:greekLit:tlg5017.tlg001",
                  "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE,
                  "reversible": "git revert the ingest commit or restore from the parent commit; "
                                "the pre-dedup file is archived offline as REPLACED.*.jsonl in staging."},
        "old": {"rows": len(dem_rows), "greek_chars": sum(greek_chars(r.get('text', '')) for r in dem_rows),
                "sha256": sha256_bytes(dem_old)},
        "new": {"rows": len(kept), "greek_chars": sum(greek_chars(r.get('text', '')) for r in kept),
                "sha256": sha256_bytes(kept_bytes)},
        "removed_rows": len(removed),
        "moved_to": {"work": ULP_SLUG, "cts": "urn:cts:greekLit:tlg2604.tlg001",
                     "note": f"the removed pp.{lo}-{hi} block is Ulpian's prolegomena; the served ulpianus "
                             f"file already holds it ({ulp_rows_n} rows / {ulp_gk} greek), so no content is "
                             "lost - only the double-coverage is removed. ulpianus is left on its served OCR "
                             "(27053 greek on these pages) which is richer than the masked re-OCR (23072)."},
        "evidence": f"Ulpian header 'ΟΥΛΠΙΑΝΟΥ ...' at p{lo}; the Life of Demosthenes / scholia proper begin "
                    f"p{hi+1} ('ΒΙΟΣ ΔΗΜΟΣΘΕΝΟΥΣ'). {len(removed)} rows removed from the scholia file.",
        "source": "bespoke keying follow-up, " + DATE,
    })
    write_change("scholia_demosthenem_dindorf_v8.reocr-flag.json", {
        "_meta": {"change": "RESOLVED (dedup)", "run_slug": "scholia_demosthenem_dindorf_v8",
                  "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE, "status": "resolved"},
        "resolution": f"Ulpian's Olynthiac+Philippic prolegomena (tlg2604.tlg001) are a contiguous front "
                      f"block pp.{lo}-{hi}, already served under ulpianus. Removed the duplicate pp.{lo}-{hi} rows "
                      "from scholia-in-demosthenem; the two works no longer double-cover.",
        "note": "The masked re-OCR of pp.53-69 has LESS Greek than the served ulpianus OCR, so ulpianus is "
                "kept on its served text; only the demosthenem duplication is removed.",
        "source": "bespoke keying follow-up, " + DATE,
    })
    log.append(f"  DEDUP scholia-in-demosthenem: {len(dem_rows)} -> {len(kept)} rows (removed {len(removed)} Ulpian pp.{lo}-{hi})")

    # =====================================================================
    # ITEMS 1 & 4 - strengthen the flags (still genuinely un-splittable here)
    # =====================================================================
    write_change("aelius_dionysius_schwabe.reocr-flag.json", {
        "_meta": {"change": "HELD - not ingested (interleaved atticist series; per-fragment attribution "
                            "unrecoverable from OCR)", "work": "pausanias-attic.attikw-n-o-noma-twn-sunagwgh",
                  "cts": "urn:cts:greekLit:tlg1569.tlg001", "run_slug": "aelius_dionysius_schwabe",
                  "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE,
                  "status": "flagged-for-manual-followup"},
        "served_left_unchanged": True,
        "shared_scan_secondary_works": ["aelius-dionysius.attika-o-no-mata (tlg1323.tlg001)"],
        "conclusive_evidence_this_pass": [
            "Schwabe 1890 prints both atticists as ONE interleaved alphabetical series: fragment numbers "
            "run monotonically 1..451 across the whole fragment section (scan pp.99-276) with no reset.",
            "No mid-book Pausanias section header exists (searched both the whole-book served OCR and the "
            "masked re-OCR); the only 'ΠΑΥΣΑΝΙΟΥ' header is on the shared title page (p5).",
            "Both 'Αἴλιος Διονύσιος' (~100x) and 'Παυσανίας' (~117x) are cited across the ENTIRE range, "
            "early and late - the two authors are not front/back partitioned.",
        ],
        "why_not_resolved": "A page-range carve cannot separate the two authors, and the OCR does not carry "
                            "a reliable per-fragment siglum. Collapsing both to one urn would mis-attribute a "
                            "real TLG author; a heuristic split would mis-key. The double-coverage is intrinsic "
                            "to this un-splittable interleaving.",
        "recommendation": "manual: apply Erbse 1950 (Untersuchungen zu den attizistischen Lexika) per-fragment "
                          "Ael.D./Paus. attribution to the numbered Schwabe fragments, then carve; also reconcile "
                          "the mislabeled aelius 'migne-ocr-qwen36' whole-book edition.",
        "masked_reocr_available": "yes - staged (keep-better vs served), keyed as one combined jsonl; do NOT "
                                  "ingest until the per-fragment attribution is resolved.",
        "source": "bespoke keying follow-up, " + DATE,
    })
    log.append("  FLAG (strengthened) Schwabe atticists - interleaved series, per-fragment attribution needs Erbse 1950")

    write_change("walz-rhetores.per-treatise-split.flag.json", {
        "_meta": {"change": "DEFERRED - per-treatise canonical TLG split of the Walz Rhetores Graeci volumes",
                  "applied_by": "scripts/ingest_bespoke_keying.py", "date": DATE,
                  "status": "flagged-for-manual-followup"},
        "holding_ids_keep_better": [f"ocr.walz_rhetores_v{v}" for v in ("1", "4", "5", "7pt2", "9")],
        "reason_deferred": "Each volume is a bound anthology of many rhetorical treatises. The OCR section "
                           "headers are present but garbled and numerous (e.g. v5 front-matter TOC 'I. ΣΩΠΑΤΡΟΥ "
                           "ΣΧΟΛΙΑ ...' 'II. ΜΑΞΙΜΟΥ ΤΟΥ ΠΛΑΝΟΥΔΟΥ ...' with printed page refs; v9 ~180 caps "
                           "header lines). No curated per-volume TOC with a printed->scan page map is on disk, so "
                           "confident treatise boundaries are not establishable in this pass; forcing a split "
                           "would mis-key.",
        "recommendation": "manual per volume: reconstruct Walz's TOC (treatise -> printed page range) from the "
                          "front matter + a reference TOC, map printed pages to scan pages via the <pg>N</pg> "
                          "markers, match each treatise to its TLG urn in tlg_canon, then carve and key.",
        "note": "The keep-better OCR text is already improved under the ocr.walz_* holding ids (commit 02641c2); "
                "only the canonical split remains.",
        "source": "bespoke keying follow-up, " + DATE,
    })
    log.append("  FLAG (strengthened) Walz per-treatise split - needs a curated per-volume TOC")

    print(("APPLIED" if do else "CHECK") + ":")
    for l in log:
        print(l)
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
