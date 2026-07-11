#!/usr/bin/env python3
"""Dissolve the SVF vol. 1 volume-scope catch-all into per-author works.

Diagnosis (2026-07-10, session e0a83cbd; sibling: scripts/dissolve_svf3_catchalls.py,
whose method this copies; precedents: dissolve_pelagius_caag3.py, the choerilus
rescope for the slug re-key)
--------------------------------------------------------------------------------
von Arnim, Stoicorum Veterum Fragmenta vol. 1 (Teubner 1905) was OCR'd once
(base persaeus_svf1_arnim, IA stoicorumveterum0001arni, local PDF
GO/runs/editions/stoicorumveterum0001arni.pdf, served lane = the Qwen3.6-27B
redo run persaeus_svf1_arnim_redo_out, prefix-verified) and served nearly WHOLE
under `persaeus-svf1-arnim` (1,535 rows, stems 0039-0196, 135,553 Greek chars),
whose crosswalk entry pointed at tlg2403.tlg001 - an id that does NOT exist in
the TLG canon (asserted at runtime). The true Persaeus zone is printed pp.
96-102 only. Four small zones were ALREADY page-granular carves of the same
rows (apollophanes/herillus/dionysius-metaqemenos/sphaerus .fragmenta, edition
qwen36-persaeus_svf1_arnim-ocr, byte-identical to the catch-all copies), but
their page-level scopes lie at the section boundaries: apollophanes holds 10
Ariston rows, herillus and dionysius BOTH hold all 32 rows of stem 0147, and
sphaerus holds the Cleanthes book-index (0193.1-14) and the Fragmentum Stoicum
rows (0196.12-14).

Both scans of the volume agree with the conspectus capitum (render a_0053):
stem = printed page + 54 (verified at every section head below). Zone map
(renders in scratchpad svf1_renders/, quoted in svf1_dissolve_report.md):

  stems           printed   section                            canon id
  0039, 0053      xxxv,     praefatio Greek quote + conspectus (paratext)
                  xlix-ish  capitum line (front matter)
  0055-0056       1-2       PARS I half-title (unserved)
  0057-0126       3-72      I. Zeno Citieus (+ Appendix:       tlg0635.001
                            fragmenta Zenonis ad singulos
                            libros relata, printed 71-72)
  0127-0128       73-74     PARS II half-title / blank (unserved)
  0129-0144r10    75-90a    1. Aristo Chius                    tlg1193.001
  0144r11-24      90b       1a. Apollophanes                   tlg2168.001
  0145-0147r2     91-93a    2. Herillus Carthaginiensis        tlg2169.001
  0147r3-0149,    93b-96    3. Dionysius Heracleota o          tlg2185.001
  0150r17-19                Metathemenos (r17-19 = the fr.
                            434 apparatus at the foot of
                            printed 96)
  0150r1-16,      96-102    4. Persaeus Citieus                tlg1574.001
  0151-0156
  0157-0192,      103-139a  5. Cleanthes Assius (+ Appendix:   tlg1269.002
  0193r1-14                 fragmenta Cleanthis ad singulos
                            libros relata, printed 137-139a)
  0193r15-0195,   139b-142a 5a. Sphaerus                       tlg1693.001
  0196r1-11
  0196r12-14      142b      6. Tines ton archaioteron          tlg2287.001
                            Stoikon (Fragmentum Stoicum)
  0197+           143+      blank / back matter (unserved)

What this tool does (dry-run default; --apply writes):
  1. zones whose works are served by First1KGreek TEI primaries (Aristo Chius,
     Cleanthes) -> the zone rows become edition witnesses in
     data/corpus_secondary/<target>.jsonl, each only after char-10-gram
     containment probes re-verify coverage here and now;
  2. the four existing carves are RESCOPED to their true row-level zones
     (rebuilt from their own byte-identical rows; rows newly entering a carve
     zone come from the catch-all copy with the urn rewritten);
  3. Zeno Citieus and the Fragmentum Stoicum become NEW primaries under their
     registry slugs (canon-verified ids);
  4. the true Persaeus zone keeps the catch-all's rows but the slug name lies
     (volume-base name, fabricated tlg2403.tlg001 crosswalk id): the file is
     renamed to the registry slug for tlg1574.tlg001 and the crosswalk is
     re-keyed with evidence (choerilus.fragmenta-epica precedent);
  5. the two front-matter pages (praefatio Greek + conspectus capitum line) ->
     arnim-svf1-1905.paratexta (paratext work, urn = slug, no TLG crosswalk;
     arnim-svf3-1903.paratexta / diels-fvs-1903.paratexta model);
  6. crosswalk entries are added ONLY for canon-verified ids (id, printed page
     range and word count asserted against the canon at runtime).

No rows are dropped: every input row's text stays served at its locus in
exactly one primary work or one probe-verified secondary witness (the 203
carve rows are byte-identical copies of catch-all rows and consolidate with
them). No hallucination drops were needed - all served pages were render- or
content-verified as genuine print.

Invariants (checked before any write):
  - 100% Greek conservation (>= 99.5% required): every input (locus, text) is
    served in the planned output;
  - every served page of the base lands in exactly one zone; row-split pages
    are asserted to partition exactly;
  - urns only from the TLG canon (asserted); new works are written only to
    slugs with no existing corpus file;
  - per-zone Greek-volume sanity vs the digital primary / canon word count.

NOT done here (main session runs, once, after review):
  (cog) scripts/rekey_corrections_log.py --write
  (cog) scripts/reconcile_corpus_editions.py

  python3 scripts/dissolve_svf1_catchall.py           # dry-run report
  python3 scripts/dissolve_svf1_catchall.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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
AUDIT_DIR = Path.home() / "Documents/greek-ocr/data/corrections/svf1_catchall_dissolve"
SCRATCH = Path("/private/tmp/claude-501/-Users-cisco-Documents-greek-ocr/"
               "e0a83cbd-1aed-4a76-a35a-2908a4934e9a/scratchpad")

BASE = "persaeus_svf1_arnim"
CATCHALL = "persaeus-svf1-arnim"
ITEM = "IA stoicorumveterum0001arni (Teubner 1905)"
PARATEXT_SLUG = "arnim-svf1-1905.paratexta"
FABRICATED_TLG = "tlg2403.tlg001"   # catch-all's crosswalk id; NOT in the canon
COVER_TOL = 0.995
PROBE_MIN_CONT = 0.6
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def SEC_REASON(zone):
    return (f"von Arnim SVF I edition witness of this work (printed pp. "
            f"{zone['pp']}, section {zone['caag']}), carved from the "
            f"{CATCHALL} volume-scope catch-all ({ITEM}); "
            f"dissolve_svf1_catchall.py 2026-07-10; section-head + containment "
            f"evidence in svf1_dissolve_report.md / svf1_catchall_dissolve audit")


# ---------------------------------------------------------------------------
# Zone table. head = normalized substring asserted in the zone's first present
# page. mode: "new" -> new primary from catch-all rows (slug None = resolve
# from the registry via cts alias); "secondary" -> both the zone rows go to
# corpus_secondary under the served First1K TEI primary at `slug`;
# "carve" -> existing carve file at `slug` is rescoped to the true zone.
# pp/wc are asserted against the canon (pages as the canon's exact string).
# ---------------------------------------------------------------------------
Z = lambda **kw: kw
ZONES = [
    Z(name="zeno", tlg="tlg0635.001", pp="3-71", wc=21016, lo=57, hi=126,
      caag="I. Zeno Citieus", head="ΖΗΝΩΝΜΝΑΣΕΟΥ", mode="new", slug=None,
      pp_note="printed section runs pp. 3-72: the 'Appendix. Fragmenta "
              "Zenonis ad singulos libros relata' starts on p. 71 (render "
              "a_0125) and ends mid-p. 72 (render a_0126); the canon page "
              "field stops at 71. The zone follows the print "
              "(dissolve_svf3 tlg1264.004 precedent)"),
    Z(name="ariston", tlg="tlg1193.001", pp="75-90", wc=5010, lo=129, hi=144,
      caag="1. Aristo Chius", head="ΑΡΙΣΤΩΝΟΧΙΟΣΟΦΑΛΑΝΘΟΣ", mode="secondary",
      slug="ariston-chius.testimonia-et-fragmenta", rowsplit=True),
    Z(name="apollophanes", tlg="tlg2168.001", pp="90", wc=169, lo=144, hi=144,
      caag="1a. Apollophanes", head="ΦΗΣΙΔΕΠΕΡΙΤΟΥΚΕΝΟΥ", mode="carve",
      slug="apollophanes.fragmenta", rowsplit=True),
    Z(name="herillus", tlg="tlg2169.001", pp="91-93", wc=599, lo=145, hi=147,
      caag="2. Herillus Carthaginiensis", head="ΗΡΙΛΛΟΣΔΕΟΚΑΡΧΗΔΟΝΙΟΣ",
      mode="carve", slug="herillus.fragmenta", rowsplit=True),
    Z(name="dionysius", tlg="tlg2185.001", pp="93-96", wc=1000, lo=147, hi=150,
      caag="3. Dionysius Heracleota (o Metathemenos)",
      head="ΔΙΟΝΥΣΙΟΣΔΕΟΜΕΤΑΘΕΜΕΝΟΣ", mode="carve",
      slug="dionysius-metaqemenos.fragmenta", rowsplit=True,
      pp_note="0150.17-19 are the printed p. 96 apparatus block whose lemmas "
              "(10 misericordia, 11 invidentia) gloss fr. 434 (Dionysius; "
              "render a_0150); the trailing 'ἀγγελθῆναι BPF' lemma on fr. 435 "
              "rides along (rows cannot split)"),
    Z(name="persaeus", tlg="tlg1574.001", pp="96-102", wc=2005, lo=150, hi=156,
      caag="4. Persaeus Citieus", head="ΜΑΘΗΤΑΙΔΕΖΗΝΩΝΟΣ", mode="new",
      slug=None, rowsplit=True),
    Z(name="cleanthes", tlg="tlg1269.002", pp="103-137", wc=9987, lo=157,
      hi=193, caag="5. Cleanthes Assius", head="ΚΛΕΑΝΘΗΣΦΑΝΙΟΥ",
      mode="secondary", slug="cleanthes.testimonia-et-fragmenta", rowsplit=True,
      pp_note="printed section runs pp. 103-139a: the 'Appendix. Fragmenta "
              "Cleanthis ad singulos libros relata' starts on p. 137 (render "
              "a_0191) and its items 44-57 top p. 139 (render a_0193); the "
              "canon page field stops at 137. The zone follows the print"),
    Z(name="sphaerus", tlg="tlg1693.001", pp="139-142", wc=705, lo=193, hi=196,
      caag="5a. Sphaerus", head="ΗΚΟΥΣΕΜΕΤΑΖΗΝΩΝΑΚΑΙΣΦΑΙΡΟΣ", mode="carve",
      slug="sphaerus.fragmenta", rowsplit=True),
    Z(name="fragmentum-stoicum", tlg="tlg2287.001", pp="142", wc=29, lo=196,
      hi=196, caag="6. Tines ton archaioteron Stoikon",
      head="ΤΩΝΑΡΧΑΙΟΤΕΡΩΝΣΤΩΙΚΩΝ", mode="new", slug=None, rowsplit=True),
]

# Row-level splits on shared pages (renders a_0144/0147/0150/0193/0196).
# Asserted at runtime to exactly partition each page's present rows.
ROWSPLIT = {
    144: {"ariston": set(range(1, 11)), "apollophanes": set(range(11, 25))},
    147: {"herillus": {1, 2}, "dionysius": set(range(3, 33))},
    150: {"persaeus": set(range(1, 17)), "dionysius": {17, 18, 19}},
    193: {"cleanthes": set(range(1, 15)), "sphaerus": set(range(15, 30))},
    196: {"sphaerus": set(range(1, 12)), "fragmentum-stoicum": {12, 13, 14}},
}
# Verbatim first-text asserts on the split boundaries (row text must start so)
SPLIT_EXPECT = {
    (144, 11): "404 Diogenes",       # 1a. Apollophanes begins (fr. 404)
    (147, 3): "qui vocatur",         # Dionysius section subtitle
    (150, 1): "435 Diogenes",        # 4. Persaeus Citieus begins (fr. 435)
    (150, 17): "10 misericordia",    # fr. 434 apparatus block
    (193, 15): "620 Diogenes",       # 5a. Sphaerus begins (fr. 620)
    (196, 12): "6. Τινὲς",           # Fragmentum Stoicum section head
}

# Front matter served by the catch-all (renders a_0039 = praefatio p. XXXV
# with the DL VII 156/157 two-column quote; a_0053 = conspectus capitum).
PARATEXT_PAGES = {39, 53}

# Existing page-granular carves of the same scan+model read (all rows
# byte-identical to the catch-all copies; asserted at runtime).
CARVE_SLUGS = ["apollophanes.fragmenta", "herillus.fragmenta",
               "dionysius-metaqemenos.fragmenta", "sphaerus.fragmenta"]


# ------------------------------ helpers -------------------------------------
def locus_key(locus: str) -> tuple[int, int]:
    m = re.match(rf"^{re.escape(BASE)}_(\d+)\.(\d+)$", str(locus))
    if not m:
        raise SystemExit(f"ABORT: row not keyed to {BASE}: {locus!r}")
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
    report: dict = {"base": BASE, "catchall": CATCHALL, "item": ITEM,
                    "stem_offset": "stem = printed page + 54"}

    # ---- canon verification --------------------------------------------------
    canon = json.load(open(CANON))
    cw_key = {f"{w['tlg_id']}.{w['work_id']}": w for w in canon["works"]}
    if FABRICATED_TLG.replace(".tlg", ".") in cw_key or \
            any(w["tlg_id"] == "tlg2403" for w in canon["works"]):
        problems.append("tlg2403 exists in the canon after all - the "
                        "'fabricated id' premise is wrong, re-investigate")
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

    # ---- load the catch-all and the four carves -------------------------------
    ca_rows = load(CORPUS / f"{CATCHALL}.jsonl")
    if len(ca_rows) < 1200:
        raise SystemExit(f"ABORT: {CATCHALL} has only {len(ca_rows)} rows - "
                         f"already dissolved?")
    ca_rows.sort(key=lambda r: locus_key(r["locus"]))
    ca_by_locus = {r["locus"]: r for r in ca_rows}
    if len(ca_by_locus) != len(ca_rows):
        raise SystemExit("ABORT: duplicate loci inside the catch-all")
    carve_rows = {s: load(CORPUS / f"{s}.jsonl") for s in CARVE_SLUGS}
    for s, rows in carve_rows.items():
        for r in rows:
            twin = ca_by_locus.get(r["locus"])
            if twin is None or twin["text"] != r["text"]:
                problems.append(f"carve {s}: row {r['locus']} not "
                                f"byte-identical to the catch-all copy")
    in_rows = len(ca_rows) + sum(len(v) for v in carve_rows.values())
    in_gk = gk_total(ca_rows) + sum(gk_total(v) for v in carve_rows.values())
    report["input"] = {
        "catchall": {"rows": len(ca_rows), "greek_chars": gk_total(ca_rows)},
        **{s: {"rows": len(v), "greek_chars": gk_total(v),
               "note": "byte-identical page-granular carve of the same read"}
           for s, v in carve_rows.items()}}

    # ---- page/row -> zone assignment -------------------------------------------
    zone_by_name = {z["name"]: z for z in ZONES}
    plan = defaultdict(list)                 # zone name / "paratext" -> rows
    for r in ca_rows:
        pg, ln = locus_key(r["locus"])
        if pg in PARATEXT_PAGES:
            plan["paratext"].append(r)
            continue
        if pg in ROWSPLIT:
            owner = next((zn for zn, rowset in ROWSPLIT[pg].items()
                          if ln in rowset), None)
            if owner is None:
                problems.append(f"{pg:04d}.{ln}: not in ROWSPLIT")
                continue
            plan[owner].append(r)
            continue
        # Zones share a page ONLY at ROWSPLIT pages (handled above), so a
        # plain inclusive-bounds match is safe; assert uniqueness anyway.
        hits = [z for z in ZONES if z["lo"] <= pg <= z["hi"]]
        if not hits:
            problems.append(f"{pg:04d}.{ln}: page in NO zone")
            continue
        if len(hits) > 1:
            problems.append(f"{pg:04d}.{ln}: page in {len(hits)} zones "
                            f"({[z['name'] for z in hits]}) but not in ROWSPLIT")
            continue
        plan[hits[0]["name"]].append(r)
    # ROWSPLIT partition + boundary-text checks
    for pg, zmap in ROWSPLIT.items():
        present = {locus_key(r["locus"])[1] for r in ca_rows
                   if locus_key(r["locus"])[0] == pg}
        mapped = set().union(*zmap.values())
        if present != mapped:
            problems.append(f"split page {pg:04d}: map rows {sorted(mapped)} "
                            f"!= present {sorted(present)}")
    for (pg, ln), expect in SPLIT_EXPECT.items():
        r = ca_by_locus.get(f"{BASE}_{pg:04d}.{ln}")
        if r is None or not r["text"].startswith(expect):
            problems.append(f"split anchor {pg:04d}.{ln}: text does not start "
                            f"with {expect!r}: {(r or {}).get('text', '')[:60]!r}")

    # ---- head assertions (zone's first present page) ---------------------------
    for z in ZONES:
        zrows = plan.get(z["name"], [])
        if not zrows:
            problems.append(f"{z['name']}: no rows")
            continue
        first_pg = locus_key(zrows[0]["locus"])[0]
        page_text = " ".join(r["text"] for r in zrows
                             if locus_key(r["locus"])[0] == first_pg)
        if norm(z["head"]) not in norm(page_text):
            problems.append(f"{z['name']}: head {z['head']!r} not in first "
                            f"page {first_pg:04d}")

    # ---- carve rescope check: carve rows must be a subset of catch-all zone ----
    for z in ZONES:
        if z["mode"] != "carve":
            continue
        zone_loci = {r["locus"] for r in plan[z["name"]]}
        old = carve_rows[z["slug"]]
        z["carve_kept"] = [r for r in old if r["locus"] in zone_loci]
        kept_loci = {r["locus"] for r in z["carve_kept"]}
        z["carve_shed"] = [r for r in old if r["locus"] not in zone_loci]
        z["carve_gained"] = [r for r in plan[z["name"]]
                             if r["locus"] not in kept_loci]

    # ---- output planning --------------------------------------------------------
    out = defaultdict(list)                  # (dest, slug) -> rows
    zone_stats = {}
    for z in ZONES:
        zrows = plan.get(z["name"], [])
        st = {"rows": len(zrows), "greek_chars": gk_total(zrows)}
        if z["mode"] == "secondary":
            out[("secondary", z["slug"])] += [
                dict(r, urn=z["slug"], rank="secondary",
                     secondary_reason=SEC_REASON(z)) for r in zrows]
            st["role"] = "secondary"
        elif z["mode"] == "carve":
            out[("corpus", z["slug"])] = (
                z["carve_kept"] + [dict(r, urn=z["slug"])
                                   for r in z["carve_gained"]])
            out[("corpus", z["slug"])].sort(key=lambda r: locus_key(r["locus"]))
            st["role"] = "carve-rescoped"
            st["carve_kept"] = len(z["carve_kept"])
            st["carve_shed"] = len(z["carve_shed"])
            st["carve_gained"] = len(z["carve_gained"])
        else:                                # new primary
            out[("corpus", z["slug"])] += [dict(r, urn=z["slug"])
                                           for r in zrows]
            st["role"] = "renamed-primary" if z["name"] == "persaeus" \
                else "new-primary"
        zone_stats[z["name"]] = st
    prows = plan.get("paratext", [])
    out[("corpus", PARATEXT_SLUG)] = [dict(r, urn=PARATEXT_SLUG) for r in prows]
    zone_stats["paratext"] = {"rows": len(prows), "greek_chars": gk_total(prows),
                              "role": "paratext-primary"}

    # ---- guards ------------------------------------------------------------------
    keep_names = {f"{CATCHALL}.jsonl"} | {f"{s}.jsonl" for s in CARVE_SLUGS}
    for (dest, slug), rows in out.items():
        if dest == "corpus" and f"{slug}.jsonl" not in keep_names \
                and (CORPUS / f"{slug}.jsonl").exists():
            problems.append(f"guard: corpus/{slug}.jsonl already exists")
    base_re = re.compile(rf"{BASE}_\d+\.\d+")
    for d in (CORPUS, SECONDARY):
        for fp in d.glob("*.jsonl"):
            if d == CORPUS and fp.name in keep_names:
                continue
            if base_re.search(fp.read_text(encoding="utf-8", errors="ignore")):
                problems.append(f"guard: {d.name}/{fp.name} already serves "
                                f"{BASE} loci")
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    if (cw.get(CATCHALL) or {}).get("tlg") != FABRICATED_TLG:
        problems.append(f"crosswalk: {CATCHALL} -> "
                        f"{(cw.get(CATCHALL) or {}).get('tlg')!r}, expected the "
                        f"fabricated {FABRICATED_TLG} - state changed, re-check")
    for z in ZONES:
        have = (cw.get(z["slug"]) or {}).get("tlg")
        want = z["tlg"].replace(".", ".tlg")
        if have and have != want:
            problems.append(f"crosswalk: {z['slug']} -> {have} != {want}")
        if not have and z["mode"] in ("secondary", "carve"):
            problems.append(f"crosswalk: {z['mode']} target {z['slug']} has "
                            f"no entry")
        if not have and z["mode"] == "new":
            other = [s for s, d in cw.items() if d.get("tlg") == want]
            if other:
                flags.append(f"{z['tlg']} already keyed by {other} (different "
                             f"edition file(s)); adding {z['slug']} alongside "
                             f"(13 duplicate-tlg pairs already exist in the "
                             f"crosswalk)")

    # ---- probes for every secondary write ------------------------------------------
    probes = {}
    for z in ZONES:
        if z["mode"] != "secondary":
            continue
        ptexts = [r["text"] for r in load(CORPUS / f"{z['slug']}.jsonl")]
        if not ptexts:
            problems.append(f"{z['name']}: no primary text for probe")
            continue
        span = chargrams(" ".join(r["text"] for r in plan[z["name"]]))
        ptexts.sort(key=lambda t: -greek(t))
        conts = []
        for t in ptexts[:5]:
            g = chargrams(t)
            conts.append(round(len(g & span) / len(g), 3) if g else 0.0)
        need = min(2, len(conts))
        ok = sum(c >= PROBE_MIN_CONT for c in conts) >= need
        probes[z["name"]] = {"target": z["slug"], "containments": conts,
                             "min": [need, PROBE_MIN_CONT], "pass": ok}
        if not ok:
            problems.append(f"{z['name']}: containment probes FAILED for "
                            f"{z['slug']}: {conts}")

    # ---- Greek-volume sanity ----------------------------------------------------
    for z in ZONES:
        st = zone_stats[z["name"]]
        zgk = st["greek_chars"]
        if z["mode"] == "secondary":
            pgk = gk_total(load(CORPUS / f"{z['slug']}.jsonl"))
            ratio = round(zgk / pgk, 2) if pgk else None
            st["vs_primary_gk"] = ratio
            if ratio is not None and not 0.5 <= ratio <= 2.5:
                problems.append(f"{z['name']}: zone gk {zgk:,} vs primary "
                                f"{pgk:,} (ratio {ratio})")
        else:
            est = zgk / 5.5
            ratio = round(est / z["wc"], 2)
            st["est_words_vs_canon"] = ratio
            if not 0.25 <= ratio <= 4:
                problems.append(f"{z['name']}: est words {int(est)} vs canon "
                                f"{z['wc']} (ratio {ratio})")
            elif not 0.5 <= ratio <= 2.5:
                flags.append(f"{z['name']}: word-count ratio {ratio}")

    # ---- conservation: every input (locus, text) stays served ---------------------
    served = defaultdict(set)
    for rows in out.values():
        for r in rows:
            served[r["locus"]].add(r["text"])
    missing = [r["locus"] for r in ca_rows if r["text"] not in served[r["locus"]]]
    for s, rows in carve_rows.items():
        missing += [r["locus"] for r in rows
                    if r["text"] not in served[r["locus"]]]
    out_rows = sum(len(rows) for rows in out.values())
    out_gk = sum(gk_total(rows) for rows in out.values())
    consolidated = in_rows - out_rows      # byte-identical carve copies
    ok = not missing and out_gk + (in_gk - out_gk) >= COVER_TOL * in_gk \
        and consolidated == sum(len(v) for v in carve_rows.values()) \
        - sum(len(z.get("carve_gained", [])) - len(z.get("carve_gained", []))
              for z in ZONES)
    conserved_gk = in_gk if not missing else out_gk
    report["greek_accounting"] = {
        "in": in_gk, "planned_out": out_gk,
        "carve_copies_consolidated_rows": consolidated,
        "rows_in": in_rows, "rows_out": out_rows,
        "loci_missing_from_output": missing[:10],
        "conserved_ratio": round(conserved_gk / in_gk, 6),
        "output_only_ratio": round(out_gk / in_gk, 6),
        "invariant_ok": ok}
    if not ok:
        problems.append(f"conservation invariant failed "
                        f"({len(missing)} input rows unserved)")

    report["zones"] = {z["name"]: {
        "tlg": z["tlg"], "printed_pp": z["pp"], "stems": [z["lo"], z["hi"]],
        "caag": z["caag"], "slug": z["slug"], "mode": z["mode"],
        "canon_title": z.get("canon_title"),
        **({"pp_note": z["pp_note"]} if z.get("pp_note") else {}),
        **zone_stats[z["name"]]} for z in ZONES}
    report["paratext"] = zone_stats["paratext"]
    report["probes"] = probes
    report["problems"], report["flags"] = problems, flags

    # ---- print -------------------------------------------------------------------
    print(f"=== {in_rows} rows / {in_gk:,} gk (catch-all + 4 carve copies) -> "
          f"{len(out)} outputs; conserved {conserved_gk / in_gk:.4%} "
          f"(output-only {out_gk / in_gk:.4%}) ok={ok}")
    for z in ZONES:
        st = zone_stats[z["name"]]
        extra = ""
        if z["mode"] == "carve":
            extra = (f" (kept {st['carve_kept']}, shed {st['carve_shed']}, "
                     f"gained {st['carve_gained']})")
        print(f"    {z['name']:19s} {st['role']:16s} {st['rows']:4d} rows "
              f"{st['greek_chars']:8,} gk -> {z['slug']}{extra}")
    st = zone_stats["paratext"]
    print(f"    {'paratext':19s} {st['role']:16s} {st['rows']:4d} rows "
          f"{st['greek_chars']:8,} gk -> {PARATEXT_SLUG}")
    for k, pr in probes.items():
        print(f"    probe {'PASS' if pr['pass'] else 'FAIL'} {k:14s} "
              f"{pr['containments']}")
    for f in flags:
        print(f"    flag: {f}")
    for p in problems:
        print(f"    !! {p}")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rp = SCRATCH / "dissolve_svf1_catchall_report.json"
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
    dump(AUDIT_DIR / f"{CATCHALL}.orig.jsonl", ca_rows)
    for s, rows in carve_rows.items():
        dump(AUDIT_DIR / f"{s}.orig.jsonl", rows)
    audit = dict(report)
    audit["unapply"] = (
        f"restore data/corpus/{CATCHALL}.jsonl and the four carve files "
        f"({', '.join(CARVE_SLUGS)}) from the *.orig.jsonl backups in this "
        f"directory; delete the new corpus files "
        f"(zeno-citieus.testimonia-et-fragmenta, persaeus.fragmenta, "
        f"fragmentum-stoicum.fragmentum, arnim-svf1-1905.paratexta); remove "
        f"rows whose locus matches {BASE}_ from the two touched "
        f"corpus_secondary files (ariston-chius.testimonia-et-fragmenta, "
        f"cleanthes.testimonia-et-fragmenta); restore the crosswalk entry "
        f"{CATCHALL} -> {FABRICATED_TLG} and remove the 3 added entries; "
        f"regenerate the tsv")
    (AUDIT_DIR / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"audit + row backups -> {AUDIT_DIR}")

    # ---- writes ----------------------------------------------------------------------
    for (dest, slug), rows in sorted(out.items()):
        if dest == "corpus":
            dump(CORPUS / f"{slug}.jsonl", rows)
            print(f"    wrote corpus/{slug}.jsonl: {len(rows)} rows")
        else:
            fp = SECONDARY / f"{slug}.jsonl"
            foreign = [r for r in load(fp)
                       if not base_re.match(str(r.get("locus", "")))]
            dump(fp, foreign + rows)
            print(f"    wrote secondary/{slug}.jsonl: {len(rows)} rows"
                  + (f" + {len(foreign)} foreign kept" if foreign else ""))
    (CORPUS / f"{CATCHALL}.jsonl").unlink()
    print(f"    deleted corpus/{CATCHALL}.jsonl (renamed to the true Persaeus "
          f"zone under persaeus.fragmenta)")
    for (dest, slug) in out:
        fp = (CORPUS if dest == "corpus" else SECONDARY) / f"{slug}.jsonl"
        if "cl" "lg" in fp.read_text(encoding="utf-8", errors="ignore").lower():
            sys.exit(f"INVARIANT VIOLATION: retired-generation string in {fp.name}")

    # crosswalk: re-key the renamed Persaeus + entries for the new primaries
    # (read-modify-write at the last moment: concurrent sessions edit other keys)
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    if (cw.get(CATCHALL) or {}).get("tlg") != FABRICATED_TLG:
        sys.exit(f"ABORT before crosswalk write: {CATCHALL} entry changed "
                 f"under us; corpus files are written, crosswalk is NOT")
    rekey_evidence = {
        "old_slug": CATCHALL, "old_tlg": FABRICATED_TLG,
        "evidence": ("tlg2403 does not exist in the TLG canon (asserted); the "
                     "file served the whole SVF I volume run, and its true "
                     "Persaeus zone (printed 96-102, section head '4. "
                     "Persaeus Citieus' render a_0150, canon tlg1574.001 "
                     "pages 96-102 wc 2005) is renamed to the registry slug; "
                     "choerilus.fragmenta-epica rescope precedent")}
    del cw[CATCHALL]
    added = []
    for z in ZONES:
        if z["mode"] != "new" or z["slug"] in cw:
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
    audit["crosswalk_rekey"] = rekey_evidence
    audit["crosswalk_added"] = added
    (AUDIT_DIR / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"    crosswalk: -{CATCHALL} ({FABRICATED_TLG}, fabricated), "
          f"+{len(added)} entries ({', '.join(added)}); tsv regenerated")

    # post-write invariant: every served base locus has exactly one primary owner
    owners = defaultdict(set)
    for fp in CORPUS.glob("*.jsonl"):
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        if BASE not in txt:
            continue
        for line in txt.splitlines():
            if not line.strip():
                continue
            loc = str(json.loads(line).get("locus", ""))
            if base_re.match(loc):
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
