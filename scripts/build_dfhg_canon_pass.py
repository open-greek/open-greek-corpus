#!/usr/bin/env python3
"""Canon pass for the DFHG carve slugs: assign TLG/CTS urns where canon-clean.

The DFHG ingest (ingest_dfhg.py, commit 33c1a3d) minted ~400 per-author carve
slugs (<author>.fragmenta[-fhgN]) without crosswalk entries, deferring urn
assignment to "a later canon pass". This is that pass. It is CONSTRAINED
matching against the vendored TLG canon (~/Documents/tlge-tools/data/
tlg_canon.json: per-author Latin names + epithet/geo + work titles + word
counts); a urn is assigned ONLY when

  (a) exactly ONE canon author matches the Mueller author name: every canon
      name token must match a Mueller token, and every Mueller token must be
      accounted for by the canon name, geo, or epithet (Latin adjective
      variants are stem-matched: Solensis/Soleus; VEL/SIVE alternates are
      optional); pure-poetry canon authors (Lyr/Trag/Comic/...) are excluded -
      Mueller FHG carves are prose fragment collections, and the vol-4
      THEOCLES is a historian, not the canon lyricist (tlg0206); and
  (b) that author has an appropriate work: a single work whose title is
      fragmenta/testimonia-like, or - among several works - a unique exact
      "Fragmenta" (falling back to a unique title containing "fragment"); and
  (c) the urn is not already claimed by another slug (the crosswalk is 1:1;
      claimed cases are reported, not reassigned); and
  (d) the DFHG size is plausible against the canon word count (a carve much
      larger than the canon work means a wrong match).

Anything ambiguous or absent stays slug-only and is listed in the report.
NEVER fabricate: no urn is ever invented, and existing entries are never
overwritten by the bulk pass.

Two hand-verified tables complement the bulk pass (evidence inline; findings
from the 2026-07-09 eponym/content investigation, session e0a83cbd):

  MANUAL   eponym rekeys the bulk matcher cannot decide (bare-name canon
           homonyms, geo spelling gaps) plus corrections of fabricated work
           ids from the earlier FHG dissolution (work ids that do not exist
           in the canon for that author). Corrections apply only while the
           documented stale value is still in place (idempotent).
  SKIP     slugs that must stay slug-only even though a name match exists:
           measured duplicates of TEI-served text (De insidiis excerpts),
           canon-absent homonyms, and complementary slices of a canon work
           whose urn is already correctly held by a sibling slug.

Writes:
  data/tlg_crosswalk.json    merged entries (cts/tlg/author_slug/title)
  data/tlg_crosswalk.tsv     regenerated, sorted (same format as
                             build_id_crosswalk.py)
  data/dfhg_canon_pass.json  full report: assigned / corrections / skipped /
                             urn_claimed / ambiguous_author / ambiguous_work /
                             absent (the audit trail for every entry this
                             pass added, so the pass is reversible)

Re-runnable and byte-stable: a second run changes nothing.

  python3 scripts/build_dfhg_canon_pass.py            # dry-run report
  python3 scripts/build_dfhg_canon_pass.py --write    # apply
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
CANON = Path("~/Documents/tlge-tools/data/tlg_canon.json").expanduser()
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
MAPPING = REPO / "data" / "dfhg_mapping.json"
EDITIONS = REPO / "data" / "corpus_editions.json"
REPORT = REPO / "data" / "dfhg_canon_pass.json"

EVIDENCE_RUN = "dfhg canon pass 2026-07-09 (session e0a83cbd)"

# ---------------------------------------------------------------------------
# MANUAL: hand-verified assignments and corrections. Every row carries its
# evidence. "add" entries assign a urn to a carve slug; "fix" entries replace
# a fabricated work id with the canon one; "remove" entries drop a fabricated
# claim. All are no-ops once applied.
# ---------------------------------------------------------------------------
MANUAL_ADD = {
    "theopompus.fragmenta": ("tlg0566.tlg002", (
        "Mueller FHG I Theopompus = the Chian historian (canon tlg0566 Hist "
        "Chius; bare-name homonyms tlg0513 Comic / tlg1726 Epic excluded by "
        "content: the carve is his numbered FHG fragments). Canon tlg0566."
        "tlg002 Fragmenta (23,521 w) vs carve ~75.9k Greek chars. tlg001 "
        "Testimonia stays with the FHG-1 scan remainder work "
        "(theopompus-history.testimonia).")),
    "manetho-sebennyta.fragmenta": ("tlg1477.tlg003", (
        "Mueller FHG II 'MANETHO SEBENNYTA' = Manetho Hist Aegyptius "
        "(tlg1477, unique historian; tlg2583 Astrol excluded). Canon lists "
        "ONLY work 003 Fragmenta (9,777 w); the DFHG carve is the corrected "
        "transcription of those FHG fragments. See also the removal of the "
        "fabricated manetho.fragmenta claim below.")),
    "clearchus-solensis.fragmenta": ("tlg1270.tlg001", (
        "Mueller FHG II 'CLEARCHUS SOLENSIS' = Clearchus Phil Soleus "
        "(tlg1270, unique; tlg0432 Comic excluded). Canon tlg1270.tlg001 "
        "Fragmenta (10,511 w) vs carve ~41k Greek chars. Urn MIGRATED from "
        "clearchus-philosophy.fragmenta, a whole-FHG-II-scan remainder "
        "(~200k Greek chars, 1,778 rows) that misclaimed the specific canon "
        "work; only 126/1,778 of its rows are Clearchus text (bigram check).")),
}

# fix: slug -> (stale tlg, canon tlg, evidence). Applied only while the stale
# value is in place.
MANUAL_FIX = {
    "cornelius-alexander.fragmenta": ("tlg0697.tlg001", "tlg0697.tlg003", (
        "canon tlg0697 (Cornelius Alexander Polyhistor) has ONLY work 003 "
        "Fragmenta (12,623 w); tlg001 was fabricated by the FHG dissolution.")),
    "hesychius-illustrius.fragmenta": ("tlg2274.tlg001", "tlg2274.tlg007", (
        "canon tlg2274 (Hesychius Illustrius Milesius) has works 004-007; "
        "Fragmenta = tlg007 (10,345 w); tlg001 was fabricated.")),
}

# remove: slug -> (stale tlg, evidence). Entry dropped while it carries the
# stale value.
MANUAL_REMOVE = {
    "manetho.fragmenta": ("tlg1477.tlg001", (
        "fabricated work id: canon tlg1477 has only work 003 (assigned to the "
        "DFHG carve manetho-sebennyta.fragmenta above). manetho.fragmenta is "
        "the old page-keyed Mueller OCR of the same section (512 rows, 183 "
        "of them bigram-duplicated by the DFHG carve) and keeps serving "
        "slug-only until a page-level shed pass.")),
    "clearchus-philosophy.fragmenta": ("tlg1270.tlg001", (
        "urn migrated to clearchus-solensis.fragmenta (see MANUAL_ADD): this "
        "slug is the whole-FHG-II-scan remainder, not the canon work.")),
}

# ---------------------------------------------------------------------------
# SKIP: stay slug-only despite a possible name match. Documented per slug.
# ---------------------------------------------------------------------------
SKIP = {
    "polybius-megalopolitanus.fragmenta": (
        "duplicate of TEI-served text: the single De insidiis excerpt "
        "(Polyb. 15.25) is 92% bigram-contained in the served perseus "
        "polybius-history.historiae (measured 2026-07-09); flagged for a "
        "displacement pass, must not claim a canon urn."),
    "dionysius-halicarnassensis.fragmenta": (
        "duplicate of TEI-served text: all 4 De insidiis excerpts (Ant. Rom. "
        "12.1, 15.3, 15.4, 20.4) are 84-91% bigram-contained in the served "
        "perseus antiquitates-romanae (measured 2026-07-09); flagged for a "
        "displacement pass, must not claim a canon urn."),
    "priscus.fragmenta": (
        "complementary FHG V addenda (sieges of Nobidounon and Naissus) of "
        "the same canon work tlg2946.tlg002, whose urn is correctly held by "
        "priscus-history.fragmenta; the crosswalk is 1:1."),
    "joannes-antiochenus.fragmenta-fhg4": (
        "complementary FHG IV slice of canon tlg4394.tlg001 (single Fragmenta "
        "work), whose urn is held by joannes-antiochenus.fragmenta; 1:1."),
    "joannes-antiochenus.fragmenta-fhg5": (
        "complementary FHG V (De insidiis) slice of canon tlg4394.tlg001, "
        "whose urn is held by joannes-antiochenus.fragmenta; 1:1."),
    "antipater.fragmenta-fhg": (
        "Antipater the historian of Rhodes (Peri Rhodou, Steph. Byz.); the "
        "only canon ANTIPATER is tlg1146, the Stoic of Tarsus - a different "
        "person. Canon-absent."),
    "demades.fragmenta-fhg": (
        "mythographic scholion citation (Schol. Hes. Theog. 913); canon "
        "tlg0535 DEMADES is the Athenian orator whose speech fragments are "
        "perseus-served under demades.* - unsafe to equate. Canon-absent."),
    "dinarchus.fragmenta-fhg": (
        "Dinarchus the poet/mythographer (Demetrius Magnes ap. Dion. Hal. "
        "De Dinarcho 1 distinguishes him from the orator); canon tlg0029 is "
        "the orator. Canon-absent."),
    "xenocrates.fragmenta-fhg": (
        "Xenocrates the chronicler (Chronika, Etym. M.); canon tlg0634 is "
        "the Academic philosopher of Chalcedon. Canon-absent."),
}

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

# canon authors whose every epithet is pure poetry are not candidates for an
# FHG prose-fragment carve (the Theocles lesson: Mueller's vol-4 historian
# would otherwise match the canon lyricist tlg0206 and its Ithyphalli).
POETRY_EPITHETS = {"lyr", "trag", "comic", "epic", "eleg", "epigr", "iamb",
                   "bucol", "mim", "parod", "satyr", "poeta"}
# a BARE single-token Mueller name has no geo/epithet to confirm the person,
# so the unique canon candidate must itself be a plausible FHG author
# (historian/mythographer/...) or carry no epithet at all. Without this,
# Mueller's Meliton (Peri ton Athenesi genon, canon-absent) lands on Melito
# of Sardis the apologist once the tragedian homonym is excluded.
HIST_EPITHETS = {"hist", "myth", "mythogr", "perieg", "geogr", "chronogr",
                 "polyhist", "paradox", "biogr"}
CONNECTIVES = {"vel", "sive", "et"}
# Latin geo/ethnic adjective endings, longest first, for stem comparison
GEO_SUFFIXES = ("iensis", "ensis", "itanus", "ianus", "inus", "anus", "ius",
                "eus", "ita", "ota", "es", "is", "us", "a", "e")


def clean_beta(raw: str) -> str:
    """Strip TLG beta-code typesetting markup from a canon name."""
    s = re.sub(r"[\[\]{}]2", "", raw or "")
    s = re.sub(r"[\[\]{}]", "", s)
    s = re.sub(r"#\d+|%\d*", "", s).replace("*", "")
    s = re.sub(r"^2(?=[^\W\d_])", "", s)
    s = re.sub(r"(?<=[^\W\d_])2$", "", s)
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    d = unicodedata.normalize("NFD", s.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return d.replace("j", "i")


def toks(s: str) -> list[str]:
    return [t for t in re.split(r"[^a-z]+", norm(s)) if t]


def dedouble(t: str) -> str:
    """Collapse doubled letters (Latin orthographic variants: Berosus /
    Berossus)."""
    return re.sub(r"(.)\1", r"\1", t)


def tok_eq(a: str, b: str) -> bool:
    """Name-token equality with -o/-on style ending tolerance (Androtio(n),
    Antileo(n), Polemo(n)) and doubled-letter collapse. The ending tolerance
    is ONE character: two chars already conflates distinct names
    (Timon/Timonax)."""
    if a == b or dedouble(a) == dedouble(b):
        return True
    a2, b2 = dedouble(a), dedouble(b)
    if min(len(a2), len(b2)) >= 5 and abs(len(a2) - len(b2)) <= 1:
        return a2.startswith(b2) or b2.startswith(a2)
    return False


def geo_stem(t: str) -> str:
    for suf in GEO_SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: -len(suf)]
    return t


def geo_eq(a: str, b: str) -> bool:
    """Geo/ethnic adjective equality tolerant of Latin suffix variation
    (Solensis/Soleus, Sigeensis/Sigeus, Magnesius/Magnes): equal stems, or
    one stem a prefix of the other (both toponym-length)."""
    if tok_eq(a, b):
        return True
    s1, s2 = geo_stem(a), geo_stem(b)
    if s1 == s2:
        return True
    return (min(len(s1), len(s2)) >= 4
            and (s1.startswith(s2) or s2.startswith(s1)))


def load_canon():
    c = json.loads(CANON.read_text(encoding="utf-8"))
    authors = {}
    for a in c["authors"].values():
        name = clean_beta(a.get("name", ""))
        eps = [norm(clean_beta(e)) for e in (a.get("epithet") or [])]
        authors[a["tlg_id"]] = {
            "name": name,
            "name_toks": toks(name),
            "extra_toks": [t for g in (a.get("geo") or []) + (a.get("epithet") or [])
                           for t in toks(clean_beta(g))],
            "poetry_only": bool(eps) and all(
                any(e.startswith(p) for p in POETRY_EPITHETS) for e in eps),
            "hist_ok": not eps or any(
                any(e.startswith(h) for h in HIST_EPITHETS) for e in eps),
        }
    works = defaultdict(list)
    for w in c["works"]:
        works[w["tlg_id"]].append(w)
    return authors, works


def match_author(mueller_name: str, cauth: dict) -> list[str]:
    raw = mueller_name.replace("(", " ").replace(")", " ").replace(",", " ")
    mtoks_all = toks(raw)
    optional = set()                       # tokens adjacent to VEL / SIVE
    for i, t in enumerate(mtoks_all):
        if t in ("vel", "sive"):
            if i > 0:
                optional.add(mtoks_all[i - 1])
            if i + 1 < len(mtoks_all):
                optional.add(mtoks_all[i + 1])
    mtoks = [t for t in mtoks_all if t not in CONNECTIVES]
    bare = len(mtoks) == 1
    cands = []
    for tlg_id, a in cauth.items():
        nt = a["name_toks"]
        if not nt or a["poetry_only"] or (bare and not a["hist_ok"]):
            continue
        if not all(any(tok_eq(n, t) for t in mtoks) for n in nt):
            continue
        for t in mtoks:                    # every Mueller token accounted for
            if any(tok_eq(t, n) for n in nt):
                continue
            if any(geo_eq(t, x) for x in a["extra_toks"]):
                continue
            if t in optional:
                continue
            break
        else:
            cands.append(tlg_id)
    return cands


def pick_work(ws: list[dict]) -> tuple[dict | None, str]:
    if len(ws) == 1:
        t = ws[0]["title"].lower()
        if "fragment" in t or "testimon" in t:
            return ws[0], "single-work"
        return None, f"single work is not fragmenta-like: {ws[0]['title']!r}"
    exact = [w for w in ws if w["title"].strip().lower() == "fragmenta"]
    if len(exact) == 1:
        return exact[0], "unique-fragmenta"
    fragish = [w for w in ws if "fragment" in w["title"].lower()]
    if len(fragish) == 1:
        return fragish[0], "unique-fragmenta-ish"
    return None, f"no unique fragmenta among {[w['title'] for w in ws]}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="apply to the crosswalk")
    args = ap.parse_args()

    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    editions = json.loads(EDITIONS.read_text(encoding="utf-8"))
    cauth, cworks = load_canon()

    slug_author = {}                       # dfhg slug -> Mueller author name
    slug_greek = {}
    for rec in mapping["authors"].values():
        ls = rec.get("leftover_slug")
        if ls:
            slug_author[ls] = rec["author"]
            slug_greek[ls] = rec.get("leftover_greek", 0)

    dfhg_slugs = sorted(s for s, v in editions.items()
                        if v.get("source") == "dfhg")

    rep = {"assigned": {}, "corrections": [], "skipped": {}, "urn_claimed": {},
           "ambiguous_author": {}, "ambiguous_work": {}, "absent": []}

    def entry_for(slug: str, tlg: str, title: str) -> dict:
        return {"cts": f"urn:cts:greekLit:{tlg}", "tlg": tlg,
                "author_slug": slug.split(".")[0], "title": title}

    # slugs this pass assigned on an earlier run: still reported (the report
    # is the audit trail of everything the pass owns, stable across re-runs)
    prior = (json.loads(REPORT.read_text(encoding="utf-8"))
             if REPORT.exists() else {})
    prior_assigned = set(prior.get("assigned", {}))

    # --- manual corrections first (idempotent: applied only while the stale
    # value is in place; an already-applied op is re-reported, not re-done) --
    for slug, (stale, fresh, why) in MANUAL_FIX.items():
        state = None
        if cw.get(slug, {}).get("tlg") == stale:
            cw[slug]["tlg"] = fresh
            cw[slug]["cts"] = f"urn:cts:greekLit:{fresh}"
            state = "applied-now"
        elif cw.get(slug, {}).get("tlg") == fresh:
            state = "applied"
        if state:
            rep["corrections"].append({"slug": slug, "op": "fix", "from": stale,
                                       "to": fresh, "state": state, "why": why})
    for slug, (stale, why) in MANUAL_REMOVE.items():
        state = None
        if cw.get(slug, {}).get("tlg") == stale:
            del cw[slug]
            state = "applied-now"
        elif slug not in cw:
            state = "applied"
        if state:
            rep["corrections"].append({"slug": slug, "op": "remove",
                                       "from": stale, "state": state, "why": why})
    for slug, (tlg, why) in MANUAL_ADD.items():
        state = None
        if cw.get(slug, {}).get("tlg") == tlg:
            state = "applied"
        elif slug not in cw:
            holder = next((s for s, d in cw.items() if d.get("tlg") == tlg), None)
            if holder:
                print(f"  MANUAL BLOCKED {slug}: {tlg} still claimed by "
                      f"{holder}", file=sys.stderr)
                continue
            title = next((w["title"] for w in cworks[tlg.split(".")[0]]
                          if f"{w['tlg_id']}.tlg{w['work_id']}" == tlg), "")
            cw[slug] = entry_for(slug, tlg, title)
            state = "applied-now"
        if state:
            rep["corrections"].append({"slug": slug, "op": "add", "to": tlg,
                                       "state": state, "why": why})

    claimed = {d.get("tlg") for d in cw.values() if d.get("tlg")}

    # --- bulk constrained pass ------------------------------------------------
    manual_slugs = set(MANUAL_ADD) | set(MANUAL_FIX) | set(MANUAL_REMOVE)
    for slug in dfhg_slugs:
        if slug in manual_slugs:
            continue                       # handled above
        if slug in cw and slug not in prior_assigned:
            continue                       # pre-existing entry: not ours
        if slug in SKIP:
            rep["skipped"][slug] = SKIP[slug]
            continue
        name = slug_author.get(slug)
        if not name:
            rep["absent"].append({"slug": slug,
                                  "author": "(not a dfhg_mapping leftover)"})
            continue
        cands = match_author(name, cauth)
        if not cands:
            rep["absent"].append({"slug": slug, "author": name})
            continue
        if len(cands) > 1:
            rep["ambiguous_author"][slug] = {"author": name,
                                             "candidates": sorted(cands)}
            continue
        tlg_id = cands[0]
        pick, how = pick_work(cworks.get(tlg_id, []))
        if pick is None:
            rep["ambiguous_work"][slug] = {"author": name, "canon_author": tlg_id,
                                           "why": how}
            continue
        tlg = f"{tlg_id}.tlg{pick['work_id']}"
        if tlg in claimed:
            holder = next((s for s, d in cw.items() if d.get("tlg") == tlg), "?")
            if holder != slug:             # own entry from an earlier run is fine
                rep["urn_claimed"][slug] = {"author": name, "tlg": tlg,
                                            "claimed_by": holder}
                continue
        wc = pick.get("word_count") or 0
        est_words = slug_greek.get(slug, 0) / 6      # rough Greek chars->words
        if wc and est_words > 4 * wc and est_words - wc > 500:
            rep["ambiguous_work"][slug] = {
                "author": name, "canon_author": tlg_id, "why":
                f"size mismatch: carve ~{est_words:.0f} words vs canon "
                f"{tlg} {wc} words"}
            continue
        cw[slug] = entry_for(slug, tlg, pick["title"])
        claimed.add(tlg)
        rep["assigned"][slug] = {
            "author": name, "tlg": tlg, "title": pick["title"], "how": how,
            "canon_name": cauth[tlg_id]["name"], "canon_words": wc,
            "dfhg_greek_chars": slug_greek.get(slug, 0)}

    rep["meta"] = {
        "run": EVIDENCE_RUN,
        "counts": {"assigned": len(rep["assigned"]),
                   "corrections": len(rep["corrections"]),
                   "skipped": len(rep["skipped"]),
                   "urn_claimed": len(rep["urn_claimed"]),
                   "ambiguous_author": len(rep["ambiguous_author"]),
                   "ambiguous_work": len(rep["ambiguous_work"]),
                   "absent": len(rep["absent"])}}

    print("canon pass:", json.dumps(rep["meta"]["counts"]))
    for r in rep["corrections"]:
        print(f"  {r['op']:>6}  {r['slug']}: {r.get('from', '')} -> {r.get('to', '')}")
    REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=1,
                                 sort_keys=True) + "\n", encoding="utf-8")
    if not args.write:
        print(f"(dry-run: report -> {REPORT.relative_to(REPO)}; crosswalk "
              f"untouched; use --write)")
        return

    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                       encoding="utf-8")
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for slug, d in sorted(cw.items()):
            if d.get("cts"):            # pta-alias-only entries have no urn
                f.write(f"{slug}\t{d['cts']}\t{d['tlg']}\n")
    print(f"wrote {CW_PATH.relative_to(REPO)} ({len(cw)} works), "
          f"{TSV_PATH.relative_to(REPO)}, {REPORT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
