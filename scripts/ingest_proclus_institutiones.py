#!/usr/bin/env python3
"""Ingest Proclus, Institutio theologica (tlg4036.tlg005) + Institutio physica
(tlg4036.tlg006) - the 2026-07-10 net-new additions (see greek-ocr final run).

Institutio theologica: NO clean open digital text exists (the eulogikon "CC0" dump is
provenance-laundered Dodds 1963 and was rejected; see proclus_sourcing notes). Source =
fresh Qwen3.6-27B OCR of the Didot 1855 volume (Plotini Enneades... accedunt Porphyrii
et Procli Institutiones, ed. Creuzer/Moser; archive.org pltinoscummarsi00dbgoog, IA
leaves n57-n123 = printed LI-CXVII, Greek LEFT column of the two-column Greek|Latin
layout), OCR'd at dpi 400 / max-side 3500 into greek-ocr runs/editions/
proclus_didot_et_out (client pages 58-124 = leaf+1). Loci = proposition numbers: the
print numbers each proposition with Greek numerals (Αʹ..ΣΙΑʹ) = TLG Section 1-211;
front matter before prop 1 = locus "t".

Institutio physica: an open digital text EXISTS - el.wikisource "Στοιχείωσις φυσική"
(books 1-2), transcluded from the proofread-page transcription of the Commons DjVu of
Ritzenfeld's Teubner 1912 edition (the exact TLG edition). Base text PD (pd_us,
Teubner 1912); Wikisource contributor layer CC BY-SA 4.0 (no NC). Served as PRIMARY
from the per-page wikitext (DjVu pages 16-42 even = Book 1, 44-72 even = Book 2; odd
pages are Ritzenfeld's facing German translation, not part of the text). Loci =
Book.section per the TLG cit scheme: "{book}.horoi" for the definition block,
"{book}.{prop}" for propositions (Book 1: 1-31, Book 2: 1-21), "{book}.t" titles.

Verification witness (multi-source rule): a fresh 29-page Qwen3.6-27B OCR pass over
the SAME edition's scan (archive.org ritzenfeld-institutio-physica-gr-lat-1912, IA
leaf = DjVu page - 1; greek-ocr runs/editions/ritzenfeld_phys_out, client page = DjVu
page) is diffed per page against the wikisource text (same edition, ROVER-valid) and
written to data/corpus_secondary/ as a rank=secondary witness. Agreement stats are
printed and saved with the audit.

  python3 scripts/ingest_proclus_institutiones.py            # dry run + report
  python3 scripts/ingest_proclus_institutiones.py --fetch    # (re)fetch wikisource pages
  python3 scripts/ingest_proclus_institutiones.py --apply    # write corpus files

Does NOT run reconcile_corpus_editions.py / build_id_crosswalk.py (run once at the end
of the delivery batch) and does NOT commit.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
GO = Path("/Users/cisco/Documents/greek-ocr")
ED = GO / "runs" / "editions"
CORPUS = COG / "data" / "corpus"
SECONDARY = COG / "data" / "corpus_secondary"
CACHE = COG / "data" / "cache" / "wikisource" / "proclus_physica"
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

ET_SLUG = "proclus.institutio-theologica"
PH_SLUG = "proclus.institutio-physica"
ET_DIR = ED / "proclus_didot_et_out"
PH_DIR = ED / "ritzenfeld_phys_out"
ET_PAGES = list(range(58, 125))
PH_PAGES = sorted(set(range(16, 43, 2)) | set(range(44, 73, 2)))
BOOK1_PAGES = set(range(16, 43, 2))
DJVU_INDEX = ("Σελίδα:Proclus (ed. Ritzenfeld) - Πρόκλου Διαδόχου Λυκίου "
              "Στοιχείωσις φυσική.djvu")

# Greek numeral (Didot prop numbers Αʹ..ΣΙΑʹ). The OCR renders Greek capitals with
# Latin lookalikes and confusable glyph pairs (survey of all 211 printed headers in
# this volume: E'/S'/PB'/RE'/MG'/PAA'/ΠΙΓ'/ΡΗΓ'...), so each character maps to a SET
# of plausible values: Σ/S/C = 200 or stigma 6; A/Α = 1 or a misread Λ (30);
# H/Η = 8 or a misread Π (80); Π = 80 or a misread Ρ (100); O/Ο = 70 or a misread
# Θ (9); G = stigma (6); F = a misread Γ (3); D = Δ (4); P/R = Ρ (100).
# greek_numeral returns every combination; the caller's strictly-increasing chain
# (LIS over all header candidates) picks the value that fits the print sequence.
CHAR_VALS = {
    "Α": {1, 30}, "A": {1, 30}, "Β": {2}, "B": {2}, "Γ": {3}, "F": {3, 6},
    "Δ": {4}, "D": {4}, "Ε": {5}, "E": {5}, "Ϛ": {6}, "G": {6},
    "Σ": {200, 6, 60}, "S": {200, 6, 60}, "C": {200, 6},   # Ξ also OCRs as Σ
    "Ζ": {7, 90, 6}, "Z": {7, 90, 6},   # koppa (90) AND stigma (6) both OCR as Ζ
    "Η": {8, 80}, "H": {8, 80}, "Θ": {9}, "Ι": {10}, "I": {10},
    "Κ": {20}, "K": {20}, "Λ": {30}, "Μ": {40}, "M": {40}, "Ν": {50},
    "N": {50}, "Ξ": {60}, "Ο": {70, 9}, "O": {70, 9}, "Π": {80, 100},
    "Ϟ": {90}, "Ϙ": {90}, "Ρ": {100}, "P": {100}, "R": {100},
}


def greek_numeral(s: str) -> set[int]:
    """All plausible values of an OCR'd Greek numeral token."""
    s = s.strip().upper()
    if s in ("ΣΤ", "СΤ", "ST"):
        return {6}
    outs = {0}
    for ch in s:
        vals = CHAR_VALS.get(ch)
        if not vals:
            return set()
        outs = {o + v for o in outs for v in vals}
        if len(outs) > 32:
            return set()
    outs |= {90 + o for o in outs if 1 <= o <= 9}   # dropped koppa: Β' printed ϞΒ'
    return {o for o in outs if o}


def gwords(t: str) -> int:
    return len([w for w in (t or "").split() if GK.search(w)])


def _bg(t: str) -> set:
    w = "".join(c for c in unicodedata.normalize("NFD", t or "")
                if not unicodedata.combining(c))
    clean = "".join(c if ("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿") else " " for c in w.lower())
    toks = [x for x in clean.split() if len(x) >= 2]
    return set(zip(toks, toks[1:]))


def contain(a: str, b: str) -> float:
    ab = _bg(a)
    return len(ab & _bg(b)) / len(ab) if ab else 0.0


# ------------------------- Institutio theologica (OCR) -------------------------

PROP_RE = re.compile(r"^\s*([ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤϚϘϞABEZHIKMNOPTXYSCDFGRV]{1,3})"
                     r"[ʹ'’΄´]\s*\.?\s*(.*)$")
# apostrophe lost by the OCR ("KA Περὶ τοῦ..."): only trusted as the EXACT successor
PROP_RE_BARE = re.compile(r"^\s*([ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤϚϘϞABEZHIKMNOPTXYSCDFGRV]{1,3})"
                          r"\s*\.?\s+(.*)$")


HEADERISH = re.compile(r"^\s*[ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤϚϘϞABEZHIKMNOPTXYSCDFGRV]{1,4}"
                       r"\s*[ʹ'’΄´.]{0,2}\s+(.*)$")

# Headers the OCR dropped or garbled beyond parsing, pinned manually: each line was
# verified against the printed sequence (strictly 1..211) and its enunciation text.
# (22: numeral lost, enunciation opens mid-page 0066; 47: 'MZ Ἡἵν τὸ αὐθυπόστατον
#  ἀμερές...' - Πᾶν misread as Ἡἵν defeats the Π filter; 167-169: page 0111 prints
#  the numerals in the margin and the OCR dropped all three.)
HEADER_OVERRIDES: list[tuple[str, int]] = [
    ("Πᾶν τὸ πρῶτως καὶ ἀρχικῶς ὃν", 22),
    ("τὸ αὐθυπόστατον ἀμερὲς ἐστι", 47),
    ("Πᾶς νοῦς ἑαυτὸν νοεῖ", 167),
    ("Πᾶς νοῦς κατ’ ἐνέργειαν οἶδεν", 168),
    ("Πᾶς νοῦς ἐν αἰῶνι τὴν τε οὐσίαν", 169),
]


def parse_theologica() -> tuple[list[dict], dict]:
    """Two-pass segmentation. Props are printed strictly 1..211 in order, so:
    pass 1 anchors on CONFIDENT headers (numeral + apostrophe + capital enunciation)
    chained by a longest-increasing-subsequence over their parsed values (garbled or
    stray matches fall off the chain); pass 2 fills each gap between consecutive
    anchors from the header-LOOKING lines in between - a run of k missing props must
    show exactly k such lines, in order (counts mismatch -> left missing, reported)."""
    missing = [p for p in ET_PAGES
               if not (ET_DIR / f"proclus_didot_et_{p:04d}.grc.txt").exists()]
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} theologica pages missing from "
                         f"{ET_DIR}: {missing[:8]}")
    lines: list[str] = []
    for p in ET_PAGES:
        txt = (ET_DIR / f"proclus_didot_et_{p:04d}.grc.txt").read_text(encoding="utf-8")
        lines += [l.strip() for l in txt.splitlines() if l.strip()]

    def cap_ok(rest: str) -> bool:
        return (not rest) or rest[0].isupper() or not rest[0].isalpha()

    # header candidates in stream order: line-initial short numeral-charset token
    # (Latin lookalikes included), optional separator, capital enunciation. Lowercase
    # or digit-led lines (marginalia, continuations) are excluded.
    cands: list[tuple[int, set[int]]] = []   # (line index, candidate values)
    seen_ov: set[int] = set()
    for i, raw in enumerate(lines):
        ov = next((n for sub, n in HEADER_OVERRIDES
                   if sub in raw and n not in seen_ov), None)
        if ov is not None:
            cands.append((i, {ov}))
            seen_ov.add(ov)
            continue
        # marginal Arabic line numbers may precede a header ("20 Α'. Πᾶν τὸ ...")
        l = re.sub(r"^\d{1,3}\s+", "", raw)
        m = PROP_RE.match(l)
        if not (m and cap_ok(m.group(2))):
            mb = HEADERISH.match(l)
            m = mb if (mb and cap_ok(mb.group(1))) else None
        if m:
            num = re.match(r"^\s*([ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤϚϘϞABEZHIKMNOPTXYSCDFGRV]{1,4})"
                           r"[ʹ'’΄´.\s]", l)
            if not num:
                continue
            rest = m.group(m.lastindex) or ""
            # every Didot proposition enunciation (and the occasional inter-prop
            # subtitle) opens with Π (Πᾶν/Πᾶσα/Πάντα/Περὶ...); anything else at a
            # header-shaped line start is a stray (marginal letter + proof text)
            if not rest.lstrip("([.·,;:’ʹ'΄´ ").startswith(("Π", "Ἐπὶ")):
                continue
            cands.append((i, {v for v in greek_numeral(num.group(1)) if 1 <= v <= 211}))

    # global alignment of the candidate sequence against the reference 1..211
    # (propositions are printed strictly in order): match when the parsed value-set
    # contains the reference number; shape-only assignment scores lower; skipping a
    # stray candidate or a lost header costs. DP over (candidate, reference).
    NC, NR = len(cands), 211
    M, SHAPE, SKIP_C, SKIP_R = 4.0, 0.5, -0.25, -1.0
    import numpy as _np
    score = _np.full((NC + 1, NR + 1), -1e9)
    move = _np.zeros((NC + 1, NR + 1), dtype=_np.int8)   # 1=assign 2=skip-cand 3=skip-ref
    score[0, 0] = 0.0
    for ci in range(NC + 1):
        for ri in range(NR + 1):
            s0 = score[ci, ri]
            if s0 <= -1e8:
                continue
            if ci < NC and ri < NR:
                gain = M if (ri + 1) in cands[ci][1] else SHAPE
                if s0 + gain > score[ci + 1, ri + 1]:
                    score[ci + 1, ri + 1] = s0 + gain
                    move[ci + 1, ri + 1] = 1
            if ci < NC and s0 + SKIP_C > score[ci + 1, ri]:
                score[ci + 1, ri] = s0 + SKIP_C
                move[ci + 1, ri] = 2
            if ri < NR and s0 + SKIP_R > score[ci, ri + 1]:
                score[ci, ri + 1] = s0 + SKIP_R
                move[ci, ri + 1] = 3
    assigned: dict[int, int] = {}     # prop number -> header line index
    ci, ri = NC, NR
    shape_only: list[int] = []
    while ci > 0 or ri > 0:
        mv = move[ci, ri]
        if mv == 1:
            assigned[ri] = cands[ci - 1][0]
            if ri not in cands[ci - 1][1]:
                shape_only.append(ri)
            ci, ri = ci - 1, ri - 1
        elif mv == 2:
            ci -= 1
        else:
            ri -= 1
    anchors = {r: i for r, i in assigned.items()}   # for the report fields

    # segment the stream at assigned header lines
    order = sorted(assigned.items(), key=lambda kv: kv[1])
    props: dict[int, list[str]] = {}
    head = lines[:order[0][1]]
    for (n, j), nxt in zip(order, [j for _, j in order[1:]] + [len(lines)]):
        m = PROP_RE.match(lines[j]) or HEADERISH.match(lines[j])
        first = m.group(m.lastindex) if m else lines[j]
        props[n] = ([first] if first else []) + lines[j + 1:nxt]
    missing_props = [n for n in range(1, 212) if n not in props]
    rows = []
    if head:
        rows.append({"urn": ET_SLUG, "edition": "qwen36-proclus_didot_et-1855",
                     "locus": "t", "source": "ocr", "license": "PD",
                     "text": " ".join(head)})
    for n in sorted(props):
        rows.append({"urn": ET_SLUG, "edition": "qwen36-proclus_didot_et-1855",
                     "locus": str(n), "source": "ocr", "license": "PD",
                     "text": " ".join(props[n])})
    words = sum(gwords(r["text"]) for r in rows)
    report = {"props_found": len(props), "missing_props": missing_props,
              "aligned": len(assigned), "shape_only_assignments": sorted(shape_only),
              "greek_words": words, "tlg_word_count": 28278,
              "coverage_vs_tlg": round(words / 28278, 3)}
    return rows, report


# ------------------------- Institutio physica (wikisource) -------------------------

def fetch_wikisource() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for p in PH_PAGES:
        title = urllib.parse.quote(f"{DJVU_INDEX}/{p}")
        url = f"https://el.wikisource.org/wiki/{title}?action=raw"
        req = urllib.request.Request(url, headers={"User-Agent": "cog-ingest/1.0"})
        raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
        (CACHE / f"{p}.wiki").write_text(raw, encoding="utf-8")
        print(f"  fetched Σελίδα .../{p} ({len(raw)} bytes)")


TEMPLATE_RE = re.compile(r"\{\{[^{}|]*\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}")
BARE_TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
LINK_RE = re.compile(r"\[\[([^\]|]*\|)?([^\]]*)\]\]")


def clean_wikitext(raw: str) -> str:
    t = re.sub(r"<noinclude>.*?</noinclude>", "", raw, flags=re.S)
    t = re.sub(r"<section[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\[\[(?:File|Αρχείο|Image):[^\]]*\]\]", "", t)
    for _ in range(6):  # unwrap nested formatting templates, keep last-arg content
        t2 = TEMPLATE_RE.sub(lambda m: m.group(1).rsplit("|", 1)[-1]
                             if "|" in m.group(1) else m.group(1), t)
        if t2 == t:
            break
        t = t2
    t = BARE_TEMPLATE_RE.sub("", t)
    t = LINK_RE.sub(lambda m: m.group(2), t)
    t = t.replace("&#x2329;", "⟨").replace("&#x232A;", "⟩")
    t = re.sub(r"''+", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t


WPROP_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")


def parse_physica() -> tuple[list[dict], dict[int, str], dict]:
    missing = [p for p in PH_PAGES if not (CACHE / f"{p}.wiki").exists()]
    if missing:
        raise SystemExit(f"ABORT: wikisource cache incomplete ({missing}); run --fetch")
    page_text: dict[int, str] = {}
    for p in PH_PAGES:
        page_text[p] = clean_wikitext((CACHE / f"{p}.wiki").read_text(encoding="utf-8"))
    rows = []
    stats = {}
    for book in (1, 2):
        pages = [p for p in PH_PAGES if (p in BOOK1_PAGES) == (book == 1)]
        stream = "\n".join(page_text[p] for p in pages)
        paras = [pp.strip() for pp in re.split(r"\n\s*\n", stream) if pp.strip()]
        head: list[str] = []
        horoi: list[str] = []
        props: dict[int, list[str]] = {}
        cur = None
        mode = "head"
        for pp in paras:
            one = " ".join(pp.split())
            m = WPROP_RE.match(one)
            if one.startswith("Ὅροι τοῦ"):
                mode, cur = "horoi", None
                horoi.append(one)
            elif m and (cur is None or 0 < int(m.group(1)) - cur <= 2):
                cur = int(m.group(1))
                mode = "prop"
                props[cur] = [one]
            elif mode == "head":
                head.append(one)
            elif mode == "horoi" and cur is None:
                horoi.append(one)
            else:
                props[cur].append(one)
        ed = "wikisource-ritzenfeld-1912"
        lic = "PD (Teubner 1912); Wikisource transcription CC BY-SA 4.0"
        if head:
            rows.append({"urn": PH_SLUG, "edition": ed, "locus": f"{book}.t",
                         "source": "wikisource", "license": lic, "text": " ".join(head)})
        if horoi:
            rows.append({"urn": PH_SLUG, "edition": ed, "locus": f"{book}.horoi",
                         "source": "wikisource", "license": lic, "text": " ".join(horoi)})
        for n in sorted(props):
            rows.append({"urn": PH_SLUG, "edition": ed, "locus": f"{book}.{n}",
                         "source": "wikisource", "license": lic,
                         "text": " ".join(props[n])})
        stats[f"book{book}_props"] = sorted(props)
    words = sum(gwords(r["text"]) for r in rows)
    report = {"greek_words": words, "tlg_word_count": 7688,
              "coverage_vs_tlg": round(words / 7688, 3), **stats}
    return rows, page_text, report


def witness_rows_and_agreement(page_text: dict[int, str]) -> tuple[list[dict], dict]:
    missing = [p for p in PH_PAGES
               if not (PH_DIR / f"ritzenfeld_phys_{p:04d}.grc.txt").exists()]
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} witness OCR pages missing: {missing}")
    rows, agree = [], {}
    reason = ("same-edition OCR verification witness (Qwen3.6-27B over the Ritzenfeld "
              "1912 Teubner scan, archive.org ritzenfeld-institutio-physica-gr-lat-1912"
              "); the primary text is served from the el.wikisource transcription of "
              "the same edition")
    for p in PH_PAGES:
        stem = f"ritzenfeld_phys_{p:04d}"
        ocr = (PH_DIR / f"{stem}.grc.txt").read_text(encoding="utf-8")
        ws = page_text.get(p, "")
        agree[p] = {"ws_in_ocr": round(contain(ws, ocr), 3),
                    "ocr_in_ws": round(contain(ocr, ws), 3)}
        i = 0
        for line in ocr.splitlines():
            line = line.strip()
            if line and GK.search(line):
                i += 1
                rows.append({"urn": PH_SLUG, "edition": "qwen36-ritzenfeld_phys",
                             "locus": f"{stem}.{i}", "source": "ocr", "license": "PD",
                             "text": line, "rank": "secondary",
                             "secondary_reason": reason})
    vals = [v["ws_in_ocr"] for v in agree.values()]
    report = {"pages": len(agree), "ws_in_ocr_min": min(vals),
              "ws_in_ocr_mean": round(sum(vals) / len(vals), 3),
              "low_pages": {p: v for p, v in agree.items() if v["ws_in_ocr"] < 0.75},
              "per_page": agree}
    return rows, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="(re)fetch wikisource pages")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--skip-theologica", action="store_true")
    args = ap.parse_args()

    if args.fetch:
        fetch_wikisource()

    audit = {"timestamp": datetime.now(timezone.utc).isoformat(), "applied": args.apply}

    ph_rows, page_text, ph_report = parse_physica()
    audit["physica"] = ph_report
    print(f"physica (wikisource): {len(ph_rows)} rows, {ph_report['greek_words']} Greek "
          f"words ({ph_report['coverage_vs_tlg']:.1%} of TLG), book1 props "
          f"{len(ph_report['book1_props'])}, book2 props {len(ph_report['book2_props'])}")

    wit_rows, wit_report = witness_rows_and_agreement(page_text)
    audit["witness"] = wit_report
    print(f"witness OCR: {wit_report['pages']} pages, ws-in-ocr containment mean "
          f"{wit_report['ws_in_ocr_mean']}, min {wit_report['ws_in_ocr_min']}, "
          f"low pages: {list(wit_report['low_pages'])}")

    if not args.skip_theologica:
        et_rows, et_report = parse_theologica()
        audit["theologica"] = et_report
        print(f"theologica (Didot OCR): {len(et_rows)} rows, props "
              f"{et_report['props_found']}/211, missing {et_report['missing_props']}, "
              f"{et_report['greek_words']} Greek words "
              f"({et_report['coverage_vs_tlg']:.1%} of TLG count)")

    if args.apply:
        (CORPUS / f"{PH_SLUG}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ph_rows),
            encoding="utf-8")
        SECONDARY.mkdir(exist_ok=True)
        (SECONDARY / f"{PH_SLUG}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in wit_rows),
            encoding="utf-8")
        if not args.skip_theologica:
            (CORPUS / f"{ET_SLUG}.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in et_rows),
                encoding="utf-8")
        print("APPLIED: corpus files written")
    out = COG / "data" / "cache" / "proclus_ingest_audit.json"
    json.dump(audit, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"audit -> {out}")


if __name__ == "__main__":
    main()
