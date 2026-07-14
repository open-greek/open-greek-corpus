#!/usr/bin/env python3
"""De-interleave the Bussemaker Didot paraphrase tail into canonical works.

Background
----------
scripts/ingest_bespoke_keying.py (commit e8c716c) carved the shared Bussemaker
Didot scholia scan (public scan scholiaintheocri00buss) by printed-section
boundary and preserved the pp.386-692 tail under a single HOLDING id
``ocr.oppian_bussemaker_paraphrases`` (ogc003623, pseudo-author oga001420),
flagging a bespoke per-work split as future work. Its flag guessed the tail was
"Eutecnius Halieutica paraphrase + Cynegetica paraphrase + the Oppian poem + an
index, interleaved". A deep page-by-page recon corrected that: there is NO
duplicate Oppian poem, and the 2025 rows are five SEQUENTIAL (not interleaved)
components:

  (1) p.386 rows 1-36  : tail of the Halieutica SCHOLIA word-glosses (Hal. Bk5
                         vv.643-680) that spilled one page past the served
                         Halieutica-scholia work.        -> merge into tlg5032.tlg002
  (2) p.386(hdr)-391   : Halieutica prose EXEGESIS, header 'ΟΠΠΙΑΝΟΥ ΑΛΙΕΥΤΙΚΩΝ
                         ΕΞΗΓΗΣΙΣ', 5 books.              -> NEW tlg4171.tlg001
  (3) p.392-397        : Cynegetica prose PARAPHRASE, header 'ΕΥΤΕΚΝΙΟΥ ΠΑΡΑΦΡΑΣΙΣ
                         ... ΚΥΝΗΓΕΤΙΚΑ', Book 1 only.    -> NEW tlg0752.tlg003
  (4) p.399-~471       : Bussemaker's ADNOTATIONES (19th-c Latin+Greek apparatus). -> DROP
  (5) p.475-692        : INDICES.                                                   -> DROP

The registry already carries both canon works as un-served gaps with their
canonical slugs (from data/inventory/work_inventory.json via build_registry.py):
  tlg4171.tlg001 -> anonymi-in-oppiani-opera.in-oppiani-halieutica-exegesis-e-cod-paris-gr-2735
  tlg0752.tlg003 -> eutecnius.paraphrasis-in-oppiani-cynegetica-fort-auctore-eutecnio
so naming the served jsonl by those exact slugs attaches the OCR text to the
right canon Work (author, TLG anchor, authorities all resolve through the
existing registry). ANONYMI IN OPPIANI OPERA (tlg4171) is a new author minted
from the slug prefix; EUTECNIUS (tlg0752) already exists in the canon.

Why re-key (2) and (3) from the RAW single-column OCR, not the masked jsonl
--------------------------------------------------------------------------
The served scholia siblings come from the geometric 2-column masker. On the
single-column prose pages that masker fragments and TRUNCATES lines (e.g. p389
lost ~15% of its Greek). So the two new prose works are re-keyed from the
COMPLETE raw single-column run passed on the command line, which de-truncates
(adds Greek back). That run MUST be a Qwen3.6-27B pass; the CLLG/Qwen3-VL-8B
base run is refused (hard project rule: never serve CLLG). Component (1) stays on
the masked edition, because it is the continuation of the masked-sourced
Halieutica-scholia work.

Every change writes a reversible record to data/corpus_changes/ (old+new sha256 /
row / Greek-char counts, per-component disposition, archive pointer, git reversal
path); the full pre-change holding is archived verbatim so all five components -
including the dropped apparatus/index - are fully recoverable. OCR provenance for
the two new works is written to data/ocr_provenance/. No local path or external
repository is hardcoded; the raw OCR run dir is a command-line argument.

Usage:
  deinterleave_oppian_bussemaker.py --raw-run <single_col_run_dir> --cog <repo_root> [--apply]
      default: --check (validate + print, write nothing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DATE = "2026-07-14"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
LOCUS_RE = re.compile(r"_(\d{3,4})\.(\d+)$")
RUN_SLUG = "scholia_oppianum_bussemaker_didot"

# A running head like 'ΑΛΙΕΥΤ. IV — V.' (here OCR'd 'ΗΛΙΕΙΥΤ. IV — V.'): a short
# ALL-CAPS work abbreviation, a period, then roman-numeral book refs. Narrow
# enough that it never matches a real title header ('ΚΥΝΗΓΕΤΙΚΑ.', 'ΕΥΤΕΚΝΙΟΥ') or
# a book divider ('ΒΙΒΛΙΟΝ Α'.', 'βιβλίον πρῶτον.').
RUNNING_HEAD_RE = re.compile(r"^[Α-Ω]{3,12}\.\s*[IVX]+(\s*[—–-]\s*[IVX]+)*\.?$")

# ---- served / holding / new-work slugs ---------------------------------------
HOLDING_SLUG = "ocr.oppian_bussemaker_paraphrases"
HAL_SCHOLIA_SLUG = ("scholia-in-oppianum."
                    "scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora")
HAL_SCHOLIA_CTS = "urn:cts:greekLit:tlg5032.tlg002"
EDITION_MASKED = "qwen36-scholia_oppianum_bussemaker_didot-masked"
EDITION_SINGLECOL = "qwen36-scholia_oppianum_bussemaker_didot"

# component (2): Halieutica exegesis  (tlg4171.tlg001)
ANON_SLUG = ("anonymi-in-oppiani-opera."
             "in-oppiani-halieutica-exegesis-e-cod-paris-gr-2735")
ANON_CTS = "urn:cts:greekLit:tlg4171.tlg001"
ANON_TLG = "tlg4171.tlg001"
ANON_AUTHOR_SLUG = "anonymi-in-oppiani-opera"
ANON_TITLE = "In Oppiani halieutica exegesis (e cod. Paris. gr. 2735)"
# inclusive page range; on the first page keep only lines from the exegesis header
ANON_PAGES = (386, 391)

# component (3): Cynegetica paraphrase  (tlg0752.tlg003)
EUT_SLUG = "eutecnius.paraphrasis-in-oppiani-cynegetica-fort-auctore-eutecnio"
EUT_CTS = "urn:cts:greekLit:tlg0752.tlg003"
EUT_TLG = "tlg0752.tlg003"
EUT_AUTHOR_SLUG = "eutecnius"
EUT_TITLE = "Paraphrasis in Oppiani cynegetica (fort. auctore Eutecnio)"
EUT_PAGES = (392, 397)

# dropped editorial matter (components 4 + 5), by page range
DROP_PAGES = (399, 692)   # p.399-471 Adnotationes + p.475-692 Indices
EXEGESIS_HEADER_MARK = "ΕΞΗΓΗΣΙΣ"   # marks the start of comp (2) on p.386

# crosswalk rows for the two new works (byte-appended; consumed by build_work_index)
NEW_CROSSWALK = {
    ANON_SLUG: {"cts": ANON_CTS, "tlg": ANON_TLG,
                "author_slug": ANON_AUTHOR_SLUG,
                "title": "In Oppiani Halieutica Exegesis (E Cod. Paris. Gr. 2735)"},
    EUT_SLUG: {"cts": EUT_CTS, "tlg": EUT_TLG,
               "author_slug": EUT_AUTHOR_SLUG,
               "title": "Paraphrasis In Oppiani Cynegetica (Fort. Auctore Eutecnio)"},
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def parse_locus(locus: str) -> tuple[int, int]:
    m = LOCUS_RE.search(locus or "")
    return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def dump_jsonl(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")


def stats(rows: list[dict]) -> tuple[int, int]:
    return len(rows), sum(greek_chars(r.get("text", "")) for r in rows)


def raw_page_lines(run: Path, page: int) -> list[str]:
    """Non-empty, stripped lines of the raw single-column .grc.txt for a page."""
    fp = run / f"{RUN_SLUG}_{page:04d}.grc.txt"
    if not fp.exists():
        return []
    return [l.strip() for l in fp.read_text(encoding="utf-8").split("\n") if l.strip()]


def build_prose_rows(run: Path, urn: str, cts: str, lo: int, hi: int,
                     skip_before_header: bool) -> tuple[list[dict], int]:
    """Page-and-paragraph rows for a prose work from the raw single-column run.
    Returns (rows, running_head_lines_dropped). Loci are keyed
    <run>_<page>.<idx>, idx 1-based over the kept lines of each page."""
    rows: list[dict] = []
    dropped_heads = 0
    for page in range(lo, hi + 1):
        lines = raw_page_lines(run, page)
        if skip_before_header and page == lo:
            hdr = next((i for i, l in enumerate(lines)
                        if EXEGESIS_HEADER_MARK in l), None)
            if hdr is None:
                raise SystemExit(
                    f"{urn}: exegesis header '{EXEGESIS_HEADER_MARK}' not found on p{page}")
            lines = lines[hdr:]
        idx = 0
        for l in lines:
            if RUNNING_HEAD_RE.match(l):
                dropped_heads += 1
                continue
            idx += 1
            rows.append({
                "urn": urn,
                "cts": cts,
                "edition": EDITION_SINGLECOL,
                "locus": f"{RUN_SLUG}_{page:04d}.{idx}",
                "source": "ocr",
                "license": "PD",
                "text": l,
            })
    return rows, dropped_heads


def provenance_record(urn: str, cts: str, run_name: str, pages: str,
                      row_span: str) -> dict:
    return {
        "urn": urn,
        "cts": cts,
        "edition": EDITION_SINGLECOL,
        "run_slug": RUN_SLUG,
        "source_scan": {"public_id": "scholiaintheocri00buss",
                        "source": "archive.org", "pages_ocr": 698},
        "carved_pages": pages,
        "model": "Qwen/Qwen3.6-27B-FP8",
        "serving_stack": {
            "engine": "vLLM",
            "images": {"Ada (sm_89)": "vllm/vllm-openai:v0.24.0",
                       "Blackwell RTX PRO 6000 (sm_120)": "vllm/vllm-openai:latest"},
            "quantization": "fp8 (block-128; vision tower + embeddings bf16)",
            "flags": "--max-model-len 16384 --max-num-seqs 16 (Ada) / 48 (Blackwell) "
                     "--gpu-memory-utilization 0.92 --reasoning-parser qwen3 "
                     "--default-chat-template-kwargs {enable_thinking:false}",
        },
        "render_dpi": 430,
        "native_dpi": "see source scan",
        "render_is_native": False,
        "image_resolution": {"client_max_side": 6000, "jpeg_quality": 92,
                             "model_max_pixels": "16.78 MP (16384 visual tokens @ 32x32 px/token)"},
        "layout_handling": {
            "method": "single-column (full page, no geometric mask)",
            "columns": 1,
            "running_head_excluded": True,
            "running_head_rule": "short ALL-CAPS work-abbreviation + roman-numeral "
                                 "book refs (e.g. 'ΑΛΙΕΥΤ. IV - V.') dropped; title "
                                 "and book-division headers kept",
            "apparatus": "the volume's Latin adnotationes and the alphabetic indices "
                         "(pp.399-692) are NOT part of this work; dropped, archived in "
                         "data/corpus_changes/ (see the de-interleave record)",
            "marginal_line_numbers": "printed marginal line-numbers left inline as OCR'd",
        },
        "prompt_specials": {
            "printed_page_capture": "printed page/column number captured as <pg>N</pg> "
                                    "in the .md source; .grc.txt is the running text",
        },
        "keying": {
            "scheme": f"{RUN_SLUG}_<page>.<idx>",
            "unit": "one row per printed paragraph/line of the raw single-column .grc.txt",
            "row_span": row_span,
        },
        "reocr_note": "Re-keyed from the COMPLETE raw single-column Qwen3.6-27B run to "
                      "de-truncate the prose that the 2-column geometric masker had "
                      "fragmented; the CLLG/Qwen3-VL base run was NOT used (project rule).",
        "date": DATE,
        "note": "Derived reproducibly from run params + _timing.json. Metadata only.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-run", required=True, type=Path,
                    help="raw SINGLE-COLUMN Qwen3.6-27B OCR run dir (per-page .grc.txt)")
    ap.add_argument("--cog", required=True, type=Path, help="cog repo root")
    ap.add_argument("--apply", action="store_true", help="write files; default is check-only")
    args = ap.parse_args()

    run, cog = args.raw_run, args.cog
    corpus = cog / "data" / "corpus"
    changes = cog / "data" / "corpus_changes"
    prov = cog / "data" / "ocr_provenance"
    do = args.apply
    log: list[str] = []
    errors: list[str] = []

    def write_bytes(p: Path, data: bytes):
        if do:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)

    def write_json(p: Path, rec: dict):
        if do:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- guard: the raw run must be a Qwen3.6 pass, never CLLG -----------------
    timing = run / "_timing.json"
    if timing.exists():
        model = json.loads(timing.read_text(encoding="utf-8")).get("model", "")
        if "CLLG" in model or "Qwen3VL" in model or "Qwen3-VL" in model:
            errors.append(f"raw run model {model!r} is CLLG/Qwen3-VL - refused "
                          "(project rule: never serve CLLG). Point --raw-run at the "
                          "Qwen3.6-27B single-column run.")
        elif "Qwen3.6" not in model:
            errors.append(f"raw run model {model!r} is not Qwen3.6-27B - refused.")
        log.append(f"  raw run model: {model}")
    else:
        errors.append(f"no _timing.json in {run} - cannot verify the OCR model")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    # =====================================================================
    # Load the holding + split into the five components (page-based).
    # =====================================================================
    holding_fp = corpus / f"{HOLDING_SLUG}.jsonl"
    holding_bytes = holding_fp.read_bytes()
    holding = [json.loads(l) for l in holding_bytes.decode("utf-8").splitlines() if l.strip()]
    holding_sha = sha256_bytes(holding_bytes)

    # component (1): p.386 rows before the exegesis header -> masked scholia rows
    p386 = [(r, parse_locus(r["locus"])) for r in holding if parse_locus(r["locus"])[0] == 386]
    hdr_idx = next((i for (r, (_, ix)) in p386 for i in [ix]
                    if EXEGESIS_HEADER_MARK in r.get("text", "")), None)
    if hdr_idx is None:
        errors.append("masked holding: exegesis header row not found on p386")
        for e in errors:
            print("ERROR:", e)
        return 1
    comp1 = [r for (r, (_, ix)) in p386 if ix < hdr_idx]          # 36 scholia rows
    comp2_masked = [r for r in holding
                    if (parse_locus(r["locus"])[0] == 386 and parse_locus(r["locus"])[1] >= hdr_idx)
                    or (ANON_PAGES[0] < parse_locus(r["locus"])[0] <= ANON_PAGES[1])]
    comp3_masked = [r for r in holding
                    if EUT_PAGES[0] <= parse_locus(r["locus"])[0] <= EUT_PAGES[1]]
    dropped = [r for r in holding if DROP_PAGES[0] <= parse_locus(r["locus"])[0] <= DROP_PAGES[1]]

    accounted = len(comp1) + len(comp2_masked) + len(comp3_masked) + len(dropped)
    if accounted != len(holding):
        stray = [r["locus"] for r in holding
                 if r not in comp1 and r not in comp2_masked
                 and r not in comp3_masked and r not in dropped]
        errors.append(f"row accounting: {accounted} classified vs {len(holding)} in holding; "
                      f"stray e.g. {stray[:5]}")

    # =====================================================================
    # (1) merge the 36 spillover scholia rows into the served Halieutica scholia.
    # =====================================================================
    hal_fp = corpus / f"{HAL_SCHOLIA_SLUG}.jsonl"
    hal_old = hal_fp.read_bytes()
    hal_rows = [json.loads(l) for l in hal_old.decode("utf-8").splitlines() if l.strip()]
    on_386 = [r for r in hal_rows if parse_locus(r["locus"])[0] == 386]
    if on_386:
        errors.append(f"{HAL_SCHOLIA_SLUG}: already has {len(on_386)} rows on p386 - "
                      "spillover would double-count")
    merged_rows = []
    for r in comp1:
        nr = {"urn": HAL_SCHOLIA_SLUG, "cts": HAL_SCHOLIA_CTS,
              "edition": r.get("edition", EDITION_MASKED), "locus": r["locus"],
              "source": r.get("source", "ocr"), "license": r.get("license", "PD"),
              "text": r.get("text", "")}
        merged_rows.append(nr)
    hal_new_rows = hal_rows + merged_rows
    hal_new = dump_jsonl(hal_new_rows)
    c1_n, c1_gk = stats(merged_rows)

    # =====================================================================
    # (2) + (3) build the two new works from the RAW single-column run.
    # =====================================================================
    anon_rows, anon_heads = build_prose_rows(run, ANON_SLUG, ANON_CTS,
                                             ANON_PAGES[0], ANON_PAGES[1], True)
    eut_rows, eut_heads = build_prose_rows(run, EUT_SLUG, EUT_CTS,
                                           EUT_PAGES[0], EUT_PAGES[1], False)
    anon_fp = corpus / f"{ANON_SLUG}.jsonl"
    eut_fp = corpus / f"{EUT_SLUG}.jsonl"
    if anon_fp.exists():
        errors.append(f"{ANON_SLUG}: corpus file already exists (expected NEW)")
    if eut_fp.exists():
        errors.append(f"{EUT_SLUG}: corpus file already exists (expected NEW)")

    c2m_n, c2m_gk = stats(comp2_masked)
    c3m_n, c3m_gk = stats(comp3_masked)
    c2r_n, c2r_gk = stats(anon_rows)
    c3r_n, c3r_gk = stats(eut_rows)
    drop_n, drop_gk = stats(dropped)

    # =====================================================================
    # Report (always) + abort on any error before writing.
    # =====================================================================
    log.append(f"  holding {HOLDING_SLUG}: {len(holding)} rows, "
               f"{sum(greek_chars(r.get('text','')) for r in holding)} greek, sha {holding_sha[:12]}")
    log.append(f"  (1) spillover scholia -> {HAL_SCHOLIA_SLUG}: +{c1_n} rows / +{c1_gk} greek "
               f"(served {len(hal_rows)} -> {len(hal_new_rows)})")
    log.append(f"  (2) {ANON_SLUG} [{ANON_TLG}]: {c2r_n} rows / {c2r_gk} greek from raw "
               f"(masked was {c2m_n} rows / {c2m_gk} greek; de-trunc delta +{c2r_gk - c2m_gk}; "
               f"{anon_heads} running-head lines dropped)")
    log.append(f"  (3) {EUT_SLUG} [{EUT_TLG}]: {c3r_n} rows / {c3r_gk} greek from raw "
               f"(masked was {c3m_n} rows / {c3m_gk} greek; de-trunc delta +{c3r_gk - c3m_gk}; "
               f"{eut_heads} running-head lines dropped)")
    log.append(f"  (4)+(5) DROP pp.{DROP_PAGES[0]}-{DROP_PAGES[1]} (adnotationes + indices): "
               f"{drop_n} rows / {drop_gk} greek (archived, recoverable)")

    if errors:
        print("CHECK (NOT APPLIED - errors):")
        for l in log:
            print(l)
        for e in errors:
            print("ERROR:", e)
        return 1

    # =====================================================================
    # Write: corpus files, archive, crosswalk, pseudo-attr removal, records.
    # =====================================================================
    # (1) merged scholia
    write_bytes(hal_fp, hal_new)
    # (2)+(3) new works
    write_bytes(anon_fp, dump_jsonl(anon_rows))
    write_bytes(eut_fp, dump_jsonl(eut_rows))
    # archive the full holding verbatim, then retire it
    archive_name = f"{HOLDING_SLUG}.de-interleaved-original.jsonl"
    write_bytes(changes / archive_name, holding_bytes)
    if do:
        holding_fp.unlink()

    # crosswalk += the two new works (indent=0, no trailing newline: byte-match)
    tc_path = cog / "data" / "tlg_crosswalk.json"
    tc = json.loads(tc_path.read_text(encoding="utf-8"))
    for slug, row in NEW_CROSSWALK.items():
        if slug not in tc:
            tc[slug] = row
            log.append(f"  crosswalk += {slug} -> {row['tlg']}")
    if do:
        tc_path.write_text(json.dumps(tc, ensure_ascii=False, indent=0), encoding="utf-8")

    # remove the holding's pseudo-author + pseudo-work (reverse the prior insert,
    # byte-exact, so the rest of the hand-formatted file is untouched)
    pa_path = cog / "data" / "pseudo_author_attributions.json"
    pa_text = pa_path.read_text(encoding="utf-8")
    pa = json.loads(pa_text)

    def _block(key: str, value: dict) -> str:
        lines = json.dumps({key: value}, ensure_ascii=False, indent=1).splitlines()
        return "\n".join(" " + l for l in lines[1:-1])

    for key, table in ((HOLDING_SLUG, "works"),
                       ("oppian-bussemaker-paraphrases", "authors")):
        val = pa[table].get(key)
        if val is None:
            continue
        frag = ",\n" + _block(key, val)
        if pa_text.count(frag) != 1:
            errors.append(f"pseudo-attr: cannot uniquely locate {table}[{key}] for removal "
                          f"(found {pa_text.count(frag)})")
            continue
        pa_text = pa_text.replace(frag, "", 1)
        log.append(f"  pseudo-attr -= {table}[{key}] (holding retired)")
    if errors:
        print("ERROR during pseudo-attr removal (corpus files already staged):")
        for e in errors:
            print("  -", e)
        return 1
    json.loads(pa_text)  # guard: still valid JSON
    if do:
        pa_path.write_text(pa_text, encoding="utf-8")

    # ---- provenance for the two new works ----
    write_json(prov / f"{ANON_SLUG}.json",
               provenance_record(ANON_SLUG, ANON_CTS, run.name,
                                 "386(from exegesis header)-391",
                                 f"{RUN_SLUG}_0386.N .. _0391.N ({c2r_n} rows)"))
    write_json(prov / f"{EUT_SLUG}.json",
               provenance_record(EUT_SLUG, EUT_CTS, run.name,
                                 "392-397",
                                 f"{RUN_SLUG}_0392.N .. _0397.N ({c3r_n} rows)"))

    # ---- corpus_changes records ----
    reversible = ("git revert the ingest commit, or restore "
                  f"data/corpus_changes/{archive_name} (the verbatim pre-change holding, "
                  "all 5 components) to data/corpus/ and re-run the id build.")

    write_json(changes / f"{HAL_SCHOLIA_SLUG}.spillover-merge.json", {
        "_meta": {"change": "merge the 36 spillover Halieutica-scholia glosses "
                            "(Hal. Bk5 vv.643-680, printed p.386) that ran one page past "
                            "the served Halieutica-scholia work into it",
                  "work": HAL_SCHOLIA_SLUG, "cts": HAL_SCHOLIA_CTS,
                  "carved_from": HOLDING_SLUG, "carved_pages": "386 (rows before the exegesis header)",
                  "applied_by": "scripts/deinterleave_oppian_bussemaker.py", "date": DATE,
                  "reversible": reversible},
        "old": {"edition": EDITION_MASKED, "rows": len(hal_rows),
                "greek_chars": sum(greek_chars(r.get("text", "")) for r in hal_rows),
                "sha256": sha256_bytes(hal_old)},
        "new": {"edition": EDITION_MASKED, "rows": len(hal_new_rows),
                "greek_chars": sum(greek_chars(r.get("text", "")) for r in hal_new_rows),
                "sha256": sha256_bytes(hal_new)},
        "merged_rows": c1_n, "merged_greek_chars": c1_gk,
        "evidence": "the served work spanned pp.282-385 with 0 rows on p.386; the 36 word-glosses "
                    "on p.386 (vv.643-680) are the genuine continuation, not a duplicate. Rows kept "
                    "on their masked edition (same source as the rest of the work).",
        "source": "Bussemaker Didot de-interleave, " + DATE,
    })

    def new_work_record(slug, cts, tlg, title, pages, work_rows, gk, masked_n, masked_gk,
                        heads, author_new):
        return {
            "_meta": {"change": "register NEW work carved from the Bussemaker Didot paraphrase "
                                "tail and re-keyed from the raw single-column Qwen3.6-27B OCR",
                      "work": slug, "cts": cts, "tlg": tlg, "carved_from": HOLDING_SLUG,
                      "carved_pages": pages, "author_minted": author_new,
                      "applied_by": "scripts/deinterleave_oppian_bussemaker.py", "date": DATE,
                      "reversible": reversible},
            "old": {"edition": None, "rows": 0, "greek_chars": 0, "sha256": None},
            "new": {"edition": EDITION_SINGLECOL,
                    "source": "raw single-column re-OCR (Qwen3.6-27B-FP8, full page)",
                    "rows": len(work_rows), "greek_chars": gk,
                    "sha256": sha256_bytes(dump_jsonl(work_rows))},
            "supersedes_masked": {"rows": masked_n, "greek_chars": masked_gk,
                                  "de_truncation_greek_delta": gk - masked_gk,
                                  "note": "the 2-column masker fragmented/truncated these "
                                          "single-column prose pages; the raw single-column "
                                          "run restores the lost Greek (delta is de-truncation, "
                                          "not new content)."},
            "running_head_lines_dropped": heads,
            "title": title,
            "registry": "canon work already in data/inventory (best_source pd_edition); this "
                        "delivery serves it as OCR. Slug/author/CTS resolve through the existing "
                        "source_registry entry; a tlg_crosswalk row adds the bare-TLG Work anchor.",
            "evidence": f"printed section header on p.{pages.split('-')[0].split('(')[0]}; "
                        f"exact-edition match to TLG canon {tlg} (editor Bussemaker, U.C., "
                        "Didot 1849 / e cod. Paris. gr. 2735).",
            "provenance": f"data/ocr_provenance/{slug}.json",
            "source": "Bussemaker Didot de-interleave, " + DATE,
        }

    write_json(changes / f"{ANON_SLUG}.reocr-new.json",
               new_work_record(ANON_SLUG, ANON_CTS, ANON_TLG, ANON_TITLE,
                               "386(from exegesis header)-391", anon_rows, c2r_gk,
                               c2m_n, c2m_gk, anon_heads, "anonymi-in-oppiani-opera (tlg4171)"))
    write_json(changes / f"{EUT_SLUG}.reocr-new.json",
               new_work_record(EUT_SLUG, EUT_CTS, EUT_TLG, EUT_TITLE,
                               "392-397", eut_rows, c3r_gk, c3m_n, c3m_gk, eut_heads,
                               "existing canon author EUTECNIUS (tlg0752)"))

    write_json(changes / f"{HOLDING_SLUG}.de-interleave.json", {
        "_meta": {"change": "RESOLVED: de-interleave the pp.386-692 Bussemaker Didot tail into "
                            "canonical works; retire the holding id and its placeholder pseudo-author",
                  "work": HOLDING_SLUG, "retired_ids": {"work": "ogc003623", "author": "oga001420"},
                  "run_slug": RUN_SLUG,
                  "applied_by": "scripts/deinterleave_oppian_bussemaker.py", "date": DATE,
                  "status": "resolved",
                  "archived_full_holding": f"data/corpus_changes/{archive_name}",
                  "reversible": reversible},
        "old_holding": {"edition": EDITION_MASKED, "rows": len(holding),
                        "greek_chars": sum(greek_chars(r.get("text", "")) for r in holding),
                        "sha256": holding_sha},
        "disposition": {
            "(1) p.386 rows 1-36 - Halieutica scholia spillover (Bk5 vv.643-680)":
                {"action": "merged", "into": HAL_SCHOLIA_SLUG, "cts": HAL_SCHOLIA_CTS,
                 "rows": c1_n, "greek_chars": c1_gk, "edition": EDITION_MASKED},
            "(2) p.386(hdr)-391 - Halieutica exegesis 'ΟΠΠΙΑΝΟΥ ΑΛΙΕΥΤΙΚΩΝ ΕΞΗΓΗΣΙΣ' (5 books)":
                {"action": "new-work (re-keyed from raw single-col)", "into": ANON_SLUG,
                 "cts": ANON_CTS, "tlg": ANON_TLG, "rows": c2r_n, "greek_chars": c2r_gk,
                 "masked_rows": c2m_n, "masked_greek_chars": c2m_gk},
            "(3) p.392-397 - Cynegetica paraphrase 'ΕΥΤΕΚΝΙΟΥ ΠΑΡΑΦΡΑΣΙΣ ... ΚΥΝΗΓΕΤΙΚΑ' (Bk1)":
                {"action": "new-work (re-keyed from raw single-col)", "into": EUT_SLUG,
                 "cts": EUT_CTS, "tlg": EUT_TLG, "rows": c3r_n, "greek_chars": c3r_gk,
                 "masked_rows": c3m_n, "masked_greek_chars": c3m_gk},
            "(4) p.399-~471 - Bussemaker ADNOTATIONES (19th-c Latin+Greek critical apparatus)":
                {"action": "dropped (non-primary editorial matter)", "recoverable_from": archive_name},
            "(5) p.475-692 - INDICES (alphabetic, dotted leaders)":
                {"action": "dropped (non-primary editorial matter)", "recoverable_from": archive_name},
        },
        "dropped_total": {"pages": f"{DROP_PAGES[0]}-{DROP_PAGES[1]}",
                          "rows": drop_n, "greek_chars": drop_gk},
        "corrects_prior_flag": "ingest_bespoke_keying.py flagged the tail as 'Eutecnius Halieutica "
                               "paraphrase (tlg0752.tlg005) + Cynegetica paraphrase (tlg0752.tlg003) "
                               "+ the Oppian poem + an index, interleaved'. Page-by-page recon found "
                               "NO duplicate Oppian poem and five SEQUENTIAL components; the "
                               "Halieutica prose is the ANONYMOUS exegesis tlg4171.tlg001 (not "
                               "Eutecnius' tlg0752.tlg005), and only the Cynegetica paraphrase is "
                               "Eutecnius (tlg0752.tlg003).",
        "source": "Bussemaker Didot de-interleave, " + DATE,
    })

    print(("APPLIED" if do else "CHECK") + ":")
    for l in log:
        print(l)
    return 0


if __name__ == "__main__":
    sys.exit(main())
