#!/usr/bin/env python3
"""Dissolve the two SVF vol. 3 volume-scope catch-alls into per-author works.

Diagnosis (2026-07-10; precedents: scripts/dissolve_pelagius_caag3.py, the upstream
OCR pipeline's dissolve_diels.py twin-scan model and its dissolve_hgm1.py)
--------------------------------------------------------------------------------
von Arnim, Stoicorum Veterum Fragmenta vol. 3 (Teubner 1903) was OCR'd TWICE and
each run was served WHOLE under a single successor's slug:

  A: apollodorus-philosophy.fragmenta   base apollodorus_seleuc_svf3
     (IA stoicorumveterum03arniuoft, 1964 stereotype reprint of the 1903 plates;
      3,018 rows, stems 0011-0277, 315,058 Greek chars)
  B: archedemus.fragmenta               base archedemus_svf3
     (IA stoicorumveterum0003arni, the 1903 printing; 3,476 rows, stems
      0006-0285, 322,881 Greek chars)

Both scans are page-aligned: pdf/stem page = printed page + 8 (verified at every
section head below and in the renders). The volume actually contains Chrysippus'
fragmenta moralia + two appendices, then (half-title, printed 207 = stem 0215:
"CHRYSIPPI DISCIPULI ET SUCCESSORES") the successors' sections I-VII. The true
Apollodorus Seleuciensis zone is printed 259-261 only; the true Archedemus zone
is printed 262-264 only. Everything else was mis-attributed.

Zone map (renders in scratchpad svf3_renders/, quoted in svf3_dissolve_report.md):

  stems      printed  section                                   canon id
  0011-0199  3-191    Chrysippi fragmenta moralia               tlg1264.002
  0200-0201  192-193  Appendix I (ad carmina Homerica)          tlg1264.003
  0202-0213  194-205  Appendix II (ad singulos libros relata)   tlg1264.004
  0214-0216  206-208  blank / half-title / blank                (paratext, unserved)
  0217       209      I.   Zeno Tarsensis                       tlg2294.001
  0218-0251  210-243  II.  Diogenes Babylonius                  tlg1320.001
  0252-0266  244-258  III. Antipater Tarsensis (+ Sosigenes,
                           Heraclides Tarsensis subsections)    tlg1146.001
  0267-0269  259-261  IV.  Apollodorus Seleuciensis (o Ephillos) tlg1166.001
  0270-0272  262-264  V.   Archedemus Tarsensis                 tlg1173.001
  0273-0275  265-267  VI.  Boethus Sidonius                     tlg2397.001
  0276-0277  268-269  VII. Appendix: Basilides (0276 row 1),    tlg2398.001
                           Eudromus (0276 rows 2-3),            tlg2399.001
                           Crinis (0276 rows 4-6 + 0277)        tlg1293.001
  0283-0285  275-277  Vol. II conspectus capitum (B only)       paratext

What this tool does (dry-run default; --apply writes):
  1. zones whose works are served by First1KGreek TEI primaries (the three
     Chrysippus works, Diogenes Babylonius, Antipater) -> BOTH scans' zone rows
     become edition witnesses in data/corpus_secondary/<target>.jsonl, each only
     after char-10-gram containment probes re-verify coverage here and now;
  2. the true Apollodorus zone keeps apollodorus-philosophy.fragmenta (A rows);
     the true Archedemus zone keeps archedemus.fragmenta (B rows, its own scan);
     the other scan's read of the same zone -> same-print twin witness in
     corpus_secondary (dissolve_diels.py twin model);
  3. Zeno Tarsensis / Basilides / Eudromus / Crinis become NEW primaries under
     their registry slugs from the A scan; B rows -> twin witnesses;
  4. the Boethus zone is ALREADY primary in boethus.fragmenta (a 2026 carve of
     the same A rows): the catch-all's copies are asserted byte-identical and
     dropped as duplicates; B rows -> twin witness of boethus.fragmenta;
  5. B stems 0283-0285 (Vol. II conspectus) -> arnim-svf3-1903.paratexta
     (paratext work, urn = slug, no TLG crosswalk; diels-fvs-1903.paratexta model);
  6. hallucinated reads on BLANK pages are dropped with render evidence:
     A 0216.1-4 (49 gk, printed 208 blank) and B 0006.1 (407 gk, front-matter
     divider, blank with bleed-through) - fabricated text, in no printed source;
  7. crosswalk entries are added ONLY for canon-verified ids (id, printed page
     range and word count asserted against the canon at runtime).

Invariants (checked before any write):
  - >= 99.5% Greek conservation: conserved = all rows written as primary or
    secondary PLUS the boethus rows verified byte-identical to the still-served
    boethus.fragmenta primary; only the render-proven hallucinations are lost
    (456 gk = 0.07%);
  - every served page of both bases lands in exactly one primary work, or in
    corpus_secondary with a reason, or is dropped with render evidence;
  - urns only from the TLG canon (asserted); new works are written only to
    slugs with no existing corpus file;
  - per-zone Greek-volume sanity vs the digital primary / canon word count.

NOT done here (main session runs, once, after review):
  (cog) scripts/rekey_corrections_log.py --write
  (cog) scripts/reconcile_corpus_editions.py

  python3 scripts/dissolve_svf3_catchalls.py           # dry-run report
  python3 scripts/dissolve_svf3_catchalls.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
REG_PATH = REPO / "data" / "source_registry.json"
CANON = Path.home() / "Documents/tlge-tools/data/tlg_canon.json"
# Row backups + audit go to the upstream OCR pipeline's correction store (set OCR_PIPELINE_DIR).
AUDIT_DIR = (Path(os.environ.get("OCR_PIPELINE_DIR", Path.home() / "Documents" / "ocr-pipeline"))
             / "data" / "corrections" / "svf3_catchall_dissolve")
SCRATCH = Path(os.environ.get("SCRATCH_DIR") or tempfile.gettempdir())

SCANS = {
    "A": {"base": "apollodorus_seleuc_svf3",
          "slug": "apollodorus-philosophy.fragmenta",
          "item": "IA stoicorumveterum03arniuoft (1964 stereotype reprint)"},
    "B": {"base": "archedemus_svf3",
          "slug": "archedemus.fragmenta",
          "item": "IA stoicorumveterum0003arni (1903 printing)"},
}
PARATEXT_SLUG = "arnim-svf3-1903.paratexta"
COVER_TOL = 0.995
PROBE_MIN_CONT = 0.6           # measured 0.61-1.0 on 2026-07-10 (pre-tested)
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

def SEC_REASON(zone, scan):
    twin = " (same-print twin witness: two scans of the same 1903 Teubner plates)" \
        if zone["primary_scan"] is not None or zone["name"] == "boethus" else ""
    return (f"von Arnim SVF III edition witness of this work (printed pp. "
            f"{zone['pp']}, section {zone['caag']}), carved from the "
            f"{SCANS[scan]['slug']} volume-scope catch-all "
            f"({SCANS[scan]['item']}){twin}; "
            f"dissolve_svf3_catchalls.py 2026-07-10; section-head + containment "
            f"evidence in svf3_dissolve_report.md / svf3_catchall_dissolve audit")

# ---------------------------------------------------------------------------
# Zone table. head = normalized substring asserted in the zone's first present
# page (both scans). primary_scan: "A"/"B" -> that scan's rows are the primary
# (other scan -> twin witness); None -> both scans go secondary to the served
# First1K TEI primary at `slug`; "disk" -> primary already on disk (boethus).
# pp/wc are asserted against the canon (pages as the canon's exact string).
# ---------------------------------------------------------------------------
Z = lambda **kw: kw
ZONES = [
    Z(name="moralia", tlg="tlg1264.002", pp="3-191", wc=71607, lo=11, hi=199,
      caag="Chrysippi fragmenta moralia", head="ΤΟΔΕΗΘΙΚΟΝΜΕΡΟΣΤΗΣΦΙΛΟΣΟΦΙΑΣ",
      primary_scan=None, slug="chrysippus-philosophy.fragmenta-moralia"),
    Z(name="homerica", tlg="tlg1264.003", pp="192-193", wc=320, lo=200, hi=201,
      caag="Appendix I", head="ΣΟΛΟΙΚΙΖΕΙΝ", primary_scan=None,
      slug="chrysippus-philosophy.fragmenta-quae-ad-explicationem-carminum-"
           "homericorum-pertinent"),
    # canon page field for .004 is "194-200, 202-204"; the printed section is
    # continuous pp. 194-205 (render b_0209 = p. 201 runs under the section
    # head; render b_0213 = p. 205 carries the section's explicit).
    Z(name="catalog", tlg="tlg1264.004", pp="194-200, 202-204", wc=1931,
      lo=202, hi=213, caag="Appendix II", head="ΠΕΡΙΑΓΑΘΩΝ", primary_scan=None,
      slug="chrysippus-philosophy.fragmenta-ad-singulos-libros-relata",
      pp_note="printed section is pp. 194-205; canon page field omits 201, 205"),
    Z(name="zeno", tlg="tlg2294.001", pp="209", wc=219, lo=217, hi=217,
      caag="I. Zeno Tarsensis", head="ΖΗΝΩΝΟΚΙΤΙΕΥΣ", primary_scan="A",
      slug=None),   # resolve from registry
    Z(name="diogenes", tlg="tlg1320.001", pp="210-243", wc=11262, lo=218, hi=251,
      caag="II. Diogenes Babylonius", head="ΔΙΟΓΕΝΗΣΟΒΑΒΥΛΩΝΙΟΣ",
      primary_scan=None, slug="diogenes-babylonius.testimonia-et-fragmenta"),
    Z(name="antipater", tlg="tlg1146.001", pp="244-258", wc=4580, lo=252, hi=266,
      caag="III. Antipater Tarsensis", head="ΑΝΤΙΠΑΤΡΟΣ", primary_scan=None,
      slug="antipater.testimonia-et-fragmenta",
      pp_note="includes the Sosigenes and Heraclides Tarsensis subsections "
              "printed on p. 258 (render b_0266), per the canon page range"),
    Z(name="apollodorus", tlg="tlg1166.001", pp="259-261", wc=811, lo=267, hi=269,
      caag="IV. Apollodorus Seleuciensis", head="ΕΦΙΛΛΟΣ", primary_scan="A",
      slug="apollodorus-philosophy.fragmenta"),
    Z(name="archedemus", tlg="tlg1173.001", pp="262-264", wc=883, lo=270, hi=272,
      caag="V. Archedemus Tarsensis", head="ΑΡΧΕΔΗΜΟΣ", primary_scan="B",
      slug="archedemus.fragmenta"),
    Z(name="boethus", tlg="tlg2397.001", pp="265-267", wc=723, lo=273, hi=275,
      caag="VI. Boethus Sidonius", head="ΒΟΗΘΟΣ", primary_scan="disk",
      slug="boethus.fragmenta"),
    # VII. Appendix (printed 268-269): row-level split, see APPENDIX_SPLIT.
    Z(name="basilides", tlg="tlg2398.001", pp="268", wc=40, lo=276, hi=277,
      caag="VII. Appendix: Basilides", head="ΒΑΣΙΛ", primary_scan="A",
      slug=None, rowsplit=True),
    Z(name="eudromus", tlg="tlg2399.001", pp="268", wc=76, lo=276, hi=277,
      caag="VII. Appendix: Eudromus", head="ΕΥΔΡΟΜ", primary_scan="A",
      slug=None, rowsplit=True),
    Z(name="crinis", tlg="tlg1293.001", pp="268-269", wc=316, lo=276, hi=277,
      caag="VII. Appendix: Crinis", head="ΚΡΙΝ", primary_scan="A",
      slug=None, rowsplit=True),
]

# VII. Appendix row maps, identical in both scans (render b_0276/b_0277:
# Basilides = Sextus adv. math. VIII 258; Eudromus frr. 1-2 = DL VII 39, 40;
# Crinis frr. 1-5 = Arrian Epict. III 2,15; DL VII 62, 68, 71+74, 76).
# Asserted at runtime to exactly partition each page's present rows.
APPENDIX_SPLIT = {
    276: {"basilides": {1}, "eudromus": {2, 3}, "crinis": {4, 5, 6}},
    277: {"crinis": {1, 2, 3}},
}

# Hallucinated reads on blank pages: dropped, with render evidence. The text
# below is asserted verbatim against the live rows before dropping.
HALLUCINATIONS = {
    "A": {"pages": {216},
          "expect_first": "ἡμεῖς δὲ τὸν Ἰησοῦν",
          "evidence": "printed p. 208 (stem 0216) is BLANK: render b_0216.png "
                      "(1903 printing, same plates as the 1964 stereotype "
                      "reprint the A scan images); the 4 rows are repetitive "
                      "Christian phrases in no printed source"},
    "B": {"pages": {6},
          "expect_first": "ἡμῶν ὁ θεός, ὅς ἐστιν ἐπὶ τῆς γῆς",
          "evidence": "stem 0006 is a blank front-matter leaf with faint "
                      "bleed-through of the FRAGMENTA MORALIA divider: render "
                      "b_0006.png; the 407-gk Christian creed text is in no "
                      "printed source"},
}

# B-only back matter: Vol. II conspectus capitum (renders b_0283-b_0285).
PARATEXT_PAGES = {"B": {283, 284, 285}}


# ------------------------------ helpers -------------------------------------
def locus_key(locus: str, base: str) -> tuple[int, int]:
    m = re.match(rf"^{re.escape(base)}_(\d+)\.(\d+)$", str(locus))
    if not m:
        raise SystemExit(f"ABORT: row not keyed to {base}: {locus!r}")
    return int(m.group(1)), int(m.group(2))


def greek(s: str) -> int:
    return len(GK.findall(s or ""))


def gk_total(rows) -> int:
    return sum(greek(r.get("text", "")) for r in rows)


# OCR mixes visually identical Latin/Greek capitals; fold onto one form
_FOLD = str.maketrans("ABEZHIKMNOPTYXΛ", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧΑ")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Zα-ωΑ-Ωϲ]", "", s).upper().replace("Ϲ", "Σ")
    return s.translate(_FOLD)


def norm_tok(tok: str) -> str:
    d = unicodedata.normalize("NFD", tok.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = "".join(c for c in d if GK.match(c))
    return d.replace("ς", "σ")


def chargrams(text: str, n: int = 10) -> set[str]:
    s = " ".join(w for w in (norm_tok(x) for x in text.split()) if w)
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def load(fp: Path) -> list[dict]:
    if not fp.exists():
        return []
    return [json.loads(l) for l in fp.open(encoding="utf-8") if l.strip()]


def dump(fp: Path, rows: list[dict]) -> None:
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                          for r in rows), encoding="utf-8")


# ------------------------------ main -----------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    problems: list[str] = []
    flags: list[str] = []
    report: dict = {"scans": {k: dict(v) for k, v in SCANS.items()}}

    # ---- canon verification --------------------------------------------------
    canon = json.load(open(CANON))
    cw_key = {f"{w['tlg_id']}.{w['work_id']}": w for w in canon["works"]}
    for z in ZONES:
        w = cw_key.get(z["tlg"])
        if w is None:
            problems.append(f"{z['tlg']}: NOT IN CANON - refusing to mint")
            continue
        if (w.get("pages") or "").strip() != z["pp"]:
            problems.append(f"{z['tlg']}: canon pages {w.get('pages')!r} != "
                            f"table {z['pp']!r}")
        if w.get("word_count") != z["wc"]:
            problems.append(f"{z['tlg']}: canon wc {w.get('word_count')} != "
                            f"table {z['wc']}")
        z["canon_title"] = w.get("title") or ""

    # ---- registry slug resolution for the new primaries ----------------------
    reg = json.load(open(REG_PATH))
    cts2slug = {(w.get("aliases") or {}).get("cts"): s
                for s, w in reg["works"].items()
                if (w.get("aliases") or {}).get("cts")}
    for z in ZONES:
        a, wid = z["tlg"].split(".")
        z["cts"] = f"urn:cts:greekLit:{a}.tlg{wid}"
        if z["slug"] is None:
            slug = cts2slug.get(z["cts"])
            if not slug:
                problems.append(f"{z['tlg']}: no registry slug for {z['cts']}")
            z["slug"] = slug
            z["title"] = (reg["works"].get(slug) or {}).get("title", "")

    # ---- load both catch-alls -------------------------------------------------
    rows_by, pages_by = {}, {}
    for s, sc in SCANS.items():
        rows = load(CORPUS / f"{sc['slug']}.jsonl")
        if len(rows) < 2500:
            raise SystemExit(f"ABORT: {sc['slug']} has only {len(rows)} rows - "
                             f"already dissolved?")
        rows.sort(key=lambda r: locus_key(r["locus"], sc["base"]))
        rows_by[s] = rows
        pages_by[s] = sorted({locus_key(r["locus"], sc["base"])[0] for r in rows})
    pre_gk = {s: gk_total(rows_by[s]) for s in SCANS}
    report["input"] = {s: {"rows": len(rows_by[s]), "greek_chars": pre_gk[s],
                           "pages": len(pages_by[s]),
                           "page_span": [pages_by[s][0], pages_by[s][-1]]}
                       for s in SCANS}

    # ---- page -> zone assignment ----------------------------------------------
    zone_by_name = {z["name"]: z for z in ZONES}
    plan = defaultdict(list)          # (kind, scan, zone_name) -> rows
    drops = {"hallucination": [], "duplicate": []}
    for s, sc in SCANS.items():
        halluc = HALLUCINATIONS.get(s, {"pages": set()})
        para = PARATEXT_PAGES.get(s, set())
        seen_h = []
        for r in rows_by[s]:
            pg, ln = locus_key(r["locus"], sc["base"])
            if pg in halluc["pages"]:
                seen_h.append(r)
                continue
            if pg in para:
                plan[("paratext", s, "paratext")].append(r)
                continue
            if pg in APPENDIX_SPLIT:
                owner = next((zn for zn, rowset in APPENDIX_SPLIT[pg].items()
                              if ln in rowset), None)
                if owner is None:
                    problems.append(f"{s} {pg:04d}.{ln}: not in APPENDIX_SPLIT")
                    continue
                plan[("zone", s, owner)].append(r)
                continue
            z = next((z for z in ZONES if not z.get("rowsplit")
                      and z["lo"] <= pg <= z["hi"]), None)
            if z is None:
                problems.append(f"{s} {pg:04d}.{ln}: page in NO zone")
                continue
            plan[("zone", s, z["name"])].append(r)
        # hallucination verification (verbatim first-row assert + evidence)
        if halluc["pages"]:
            if not seen_h:
                problems.append(f"{s}: expected hallucination rows absent")
            elif not seen_h[0]["text"].startswith(halluc["expect_first"]):
                problems.append(f"{s}: hallucination row 1 text changed: "
                                f"{seen_h[0]['text'][:60]!r}")
            else:
                drops["hallucination"] += [dict(r, drop_scan=s,
                                                drop_evidence=halluc["evidence"])
                                           for r in seen_h]
    # APPENDIX_SPLIT partition check
    for s, sc in SCANS.items():
        for pg, zmap in APPENDIX_SPLIT.items():
            present = {locus_key(r["locus"], sc["base"])[1] for r in rows_by[s]
                       if locus_key(r["locus"], sc["base"])[0] == pg}
            mapped = set().union(*zmap.values())
            if present != mapped:
                problems.append(f"{s} split page {pg:04d}: map rows "
                                f"{sorted(mapped)} != present {sorted(present)}")

    # ---- head assertions (zone's first present page, both scans) --------------
    for z in ZONES:
        for s, sc in SCANS.items():
            zrows = plan.get(("zone", s, z["name"]), [])
            if not zrows:
                problems.append(f"{z['name']}: no rows in scan {s}")
                continue
            first_pg = locus_key(zrows[0]["locus"], sc["base"])[0]
            page_text = " ".join(r["text"] for r in zrows
                                 if locus_key(r["locus"], sc["base"])[0] == first_pg)
            if norm(z["head"]) not in norm(page_text):
                problems.append(f"{z['name']} scan {s}: head {z['head']!r} not "
                                f"in first page {first_pg:04d}")

    # ---- boethus duplicate check (byte-identical to the on-disk primary) ------
    bz = zone_by_name["boethus"]
    disk_bo = load(CORPUS / f"{bz['slug']}.jsonl")
    disk_by_locus = {r["locus"]: r["text"] for r in disk_bo}
    a_bo = plan.pop(("zone", "A", "boethus"), [])
    if len(a_bo) != len(disk_bo):
        problems.append(f"boethus: catch-all has {len(a_bo)} rows vs disk "
                        f"{len(disk_bo)}")
    for r in a_bo:
        if disk_by_locus.get(r["locus"]) != r["text"]:
            problems.append(f"boethus: catch-all row {r['locus']} NOT identical "
                            f"to boethus.fragmenta - refusing duplicate-drop")
            break
    else:
        drops["duplicate"] = [dict(r, drop_reason=(
            "byte-identical to the row already primary in boethus.fragmenta "
            "(2026 carve of the same scan+model read; only the edition label "
            "differs)")) for r in a_bo]

    # ---- output planning -------------------------------------------------------
    # (dest, slug) -> rows;  dest in {corpus, secondary}
    out = defaultdict(list)
    zone_stats = defaultdict(dict)
    for z in ZONES:
        for s in SCANS:
            zrows = plan.get(("zone", s, z["name"]), [])
            if not zrows:
                continue
            zone_stats[z["name"]][s] = {"rows": len(zrows),
                                        "greek_chars": gk_total(zrows)}
            if z["primary_scan"] == s:
                out[("corpus", z["slug"])] += [dict(r, urn=z["slug"])
                                               for r in zrows]
                zone_stats[z["name"]][s]["role"] = "primary"
            elif z["primary_scan"] == "disk" and s == "A":
                zone_stats[z["name"]][s]["role"] = "duplicate-dropped"
            else:
                out[("secondary", z["slug"])] += [
                    dict(r, urn=z["slug"], rank="secondary",
                         secondary_reason=SEC_REASON(z, s)) for r in zrows]
                zone_stats[z["name"]][s]["role"] = "secondary"
    for s in SCANS:
        prows = plan.get(("paratext", s, "paratext"), [])
        if prows:
            out[("corpus", PARATEXT_SLUG)] += [dict(r, urn=PARATEXT_SLUG)
                                               for r in prows]
            zone_stats["paratext"][s] = {"rows": len(prows),
                                         "greek_chars": gk_total(prows),
                                         "role": "paratext-primary"}

    # ---- guards ----------------------------------------------------------------
    old_slugs = {sc["slug"] for sc in SCANS.values()}
    for (dest, slug), rows in out.items():
        if dest == "corpus" and slug not in old_slugs \
                and (CORPUS / f"{slug}.jsonl").exists():
            problems.append(f"guard: corpus/{slug}.jsonl already exists")
    both_bases = re.compile(r"(apollodorus_seleuc_svf3|archedemus_svf3)_\d+\.\d+")
    for fp in CORPUS.glob("*.jsonl"):
        if fp.stem in old_slugs or fp.stem == bz["slug"]:
            continue
        if both_bases.search(fp.read_text(encoding="utf-8", errors="ignore")):
            problems.append(f"guard: {fp.name} already serves SVF3 base loci")
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    for z in ZONES:
        have = (cw.get(z["slug"]) or {}).get("tlg")
        want = z["tlg"].replace(".", ".tlg")
        if have and have != want:
            problems.append(f"crosswalk: {z['slug']} -> {have} != {want}")
        if not have and z["primary_scan"] is None:
            problems.append(f"crosswalk: sec target {z['slug']} has no entry")

    # ---- probes for every secondary write --------------------------------------
    probes = {}
    for z in ZONES:
        for s in SCANS:
            if zone_stats[z["name"]].get(s, {}).get("role") != "secondary":
                continue
            if z["primary_scan"] in SCANS:      # twin: primary = planned rows
                ptexts = [r["text"] for r in out[("corpus", z["slug"])]]
            elif z["primary_scan"] == "disk":
                ptexts = [r["text"] for r in disk_bo]
            else:                                # First1K TEI primary on disk
                ptexts = [r["text"] for r in load(CORPUS / f"{z['slug']}.jsonl")]
            if not ptexts:
                problems.append(f"{z['name']}: no primary text for probe")
                continue
            span = chargrams(" ".join(r["text"]
                             for r in plan[("zone", s, z["name"])]))
            ptexts.sort(key=lambda t: -greek(t))
            conts = []
            for t in ptexts[:5]:
                g = chargrams(t)
                conts.append(round(len(g & span) / len(g), 3) if g else 0.0)
            need = min(2, len(conts))
            ok = sum(c >= PROBE_MIN_CONT for c in conts) >= need
            probes[f"{z['name']}/{s}"] = {
                "target": z["slug"], "containments": conts,
                "min": [need, PROBE_MIN_CONT], "pass": ok}
            if not ok:
                problems.append(f"{z['name']}/{s}: containment probes FAILED "
                                f"for {z['slug']}: {conts}")

    # ---- Greek-volume sanity ----------------------------------------------------
    for z in ZONES:
        st = zone_stats[z["name"]]
        for s in SCANS:
            if s not in st:
                continue
            zgk = st[s]["greek_chars"]
            if z["primary_scan"] is None:
                pgk = gk_total(load(CORPUS / f"{z['slug']}.jsonl"))
                ratio = round(zgk / pgk, 2) if pgk else None
                st[s]["vs_primary_gk"] = ratio
                if ratio is not None and not 0.5 <= ratio <= 2.5:
                    problems.append(f"{z['name']}/{s}: zone gk {zgk:,} vs "
                                    f"primary {pgk:,} (ratio {ratio})")
            else:
                est = zgk / 5.5
                ratio = round(est / z["wc"], 2)
                st[s]["est_words_vs_canon"] = ratio
                if not 0.25 <= ratio <= 4:
                    problems.append(f"{z['name']}/{s}: est words {int(est)} vs "
                                    f"canon {z['wc']} (ratio {ratio})")
                elif not 0.5 <= ratio <= 2.5:
                    flags.append(f"{z['name']}/{s}: word-count ratio {ratio}")

    # ---- conservation ------------------------------------------------------------
    in_gk = sum(pre_gk.values())
    out_gk = sum(gk_total(rows) for rows in out.values())
    dup_gk = gk_total(drops["duplicate"])
    hal_gk = gk_total(drops["hallucination"])
    in_rows = sum(len(rows_by[s]) for s in SCANS)
    out_rows = sum(len(rows) for rows in out.values())
    conserved = out_gk + dup_gk        # dup text stays served in boethus primary
    ok = conserved >= COVER_TOL * in_gk and \
        out_rows + len(drops["duplicate"]) + len(drops["hallucination"]) == in_rows
    report["greek_accounting"] = {
        "in": in_gk, "planned_out": out_gk,
        "duplicate_dropped_still_served": dup_gk,
        "hallucination_dropped": hal_gk,
        "rows_in": in_rows, "rows_out": out_rows,
        "rows_dropped_duplicate": len(drops["duplicate"]),
        "rows_dropped_hallucination": len(drops["hallucination"]),
        "conserved_ratio": round(conserved / in_gk, 6),
        "output_only_ratio": round(out_gk / in_gk, 6),
        "invariant_ok": ok}
    if not ok:
        problems.append("conservation invariant failed")

    report["zones"] = {z["name"]: {
        "tlg": z["tlg"], "printed_pp": z["pp"], "stems": [z["lo"], z["hi"]],
        "caag": z["caag"], "slug": z["slug"],
        "primary_scan": z["primary_scan"], "canon_title": z.get("canon_title"),
        **({"pp_note": z["pp_note"]} if z.get("pp_note") else {}),
        "per_scan": zone_stats[z["name"]]} for z in ZONES}
    report["paratext"] = zone_stats.get("paratext", {})
    report["probes"] = probes
    report["drops"] = {k: [{kk: r[kk] for kk in
                            ("locus", "text", "edition",
                             "drop_evidence" if k == "hallucination"
                             else "drop_reason")}
                           for r in v] for k, v in drops.items()}
    report["problems"], report["flags"] = problems, flags

    # ---- print -------------------------------------------------------------------
    print(f"=== {in_rows} rows / {in_gk:,} gk across 2 scans -> "
          f"{len(out)} outputs; conserved {conserved / in_gk:.4%} "
          f"(output-only {out_gk / in_gk:.4%}) ok={ok}")
    for z in ZONES:
        for s in SCANS:
            st = zone_stats[z["name"]].get(s)
            if st:
                print(f"    {z['name']:11s} {s} {st.get('role', '?'):18s} "
                      f"{st['rows']:4d} rows {st['greek_chars']:8,} gk "
                      f"-> {z['slug']}")
    for s, st in zone_stats.get("paratext", {}).items():
        print(f"    {'paratext':11s} {s} {st['role']:18s} {st['rows']:4d} rows "
              f"{st['greek_chars']:8,} gk -> {PARATEXT_SLUG}")
    print(f"    drops: {len(drops['hallucination'])} hallucination rows "
          f"({hal_gk} gk), {len(drops['duplicate'])} boethus duplicates "
          f"({dup_gk:,} gk, still served)")
    for k, pr in probes.items():
        print(f"    probe {'PASS' if pr['pass'] else 'FAIL'} {k:14s} "
              f"{pr['containments']}")
    for f in flags:
        print(f"    flag: {f}")
    for p in problems:
        print(f"    !! {p}")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rp = SCRATCH / "dissolve_svf3_catchalls_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"report -> {rp}")

    if not args.apply:
        print("DRY RUN - nothing written (use --apply)")
        return
    if problems:
        sys.exit("ABORT: problems listed above; nothing written")

    # ---- audit + row backups (reversibility) ---------------------------------------
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    for s, sc in SCANS.items():
        dump(AUDIT_DIR / f"{sc['slug']}.orig.jsonl", rows_by[s])
    audit = dict(report)
    audit["unapply"] = (
        "restore data/corpus/<slug>.jsonl for both catch-alls from the "
        "*.orig.jsonl backups in this directory; delete the new corpus files "
        "(zeno-tarsensis.fragmenta, basilides.fragmentum, eudromus.fragmenta, "
        "crinis.fragmenta, arnim-svf3-1903.paratexta); remove rows whose locus "
        "matches apollodorus_seleuc_svf3_|archedemus_svf3_ from the touched "
        "corpus_secondary files; remove the 4 added crosswalk entries; "
        "regenerate the tsv")
    (AUDIT_DIR / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"audit + row backups -> {AUDIT_DIR}")

    # ---- writes ----------------------------------------------------------------------
    ours = both_bases
    for (dest, slug), rows in sorted(out.items()):
        if dest == "corpus":
            dump(CORPUS / f"{slug}.jsonl", rows)
            print(f"    wrote corpus/{slug}.jsonl: {len(rows)} rows")
        else:
            fp = SECONDARY / f"{slug}.jsonl"
            foreign = [r for r in load(fp)
                       if not ours.match(str(r.get("locus", "")))]
            dump(fp, foreign + rows)
            print(f"    wrote secondary/{slug}.jsonl: {len(rows)} rows"
                  + (f" + {len(foreign)} foreign kept" if foreign else ""))
    for txt in (((CORPUS if dest == "corpus" else SECONDARY) / f"{slug}.jsonl")
                for (dest, slug) in out):
        if "cl" "lg" in txt.read_text(encoding="utf-8", errors="ignore").lower():
            sys.exit(f"INVARIANT VIOLATION: retired-generation string in {txt.name}")

    # crosswalk: entries for the new primaries (canon-verified ids only)
    added = []
    for z in ZONES:
        if z["primary_scan"] not in SCANS or z["slug"] in cw:
            continue
        cw[z["slug"]] = {"cts": z["cts"],
                         "tlg": z["cts"].split("greekLit:")[-1],
                         "author_slug": z["slug"].split(".")[0],
                         "title": z.get("title", "")}
        added.append(z["slug"])
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                       encoding="utf-8")
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s2, d in sorted(cw.items()):
            if d.get("cts"):
                f.write(f"{s2}\t{d['cts']}\t{d['tlg']}\n")
    print(f"    crosswalk: +{len(added)} entries ({', '.join(added)}); "
          f"tsv regenerated")

    # post-write invariant: every served SVF3 locus has exactly one primary owner
    owners = defaultdict(set)
    for fp in CORPUS.glob("*.jsonl"):
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        if "svf3" not in txt:
            continue
        for line in txt.splitlines():
            if not line.strip():
                continue
            loc = str(json.loads(line).get("locus", ""))
            if ours.match(loc):
                owners[loc].add(fp.name[:-6])
    multi = {l: sorted(o) for l, o in owners.items() if len(o) > 1}
    if multi:
        sys.exit(f"INVARIANT VIOLATION - loci with >1 primary owner: "
                 f"{list(multi.items())[:5]}")
    print(f"applied. {len(owners)} corpus loci each have exactly one primary "
          f"owner.\nNow run (main session, after review):\n"
          f"  scripts/rekey_corrections_log.py --write\n"
          f"  scripts/reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
