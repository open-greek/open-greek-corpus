#!/usr/bin/env python3
"""Ingest the Greek texts of SAWS (Sharing Ancient Wisdoms, KCL/Uppsala/Vienna,
ancientwisdoms.ac.uk) from the 2025 KCL figshare deposit.

Source deposit: "Sharing Ancient Wisdoms: The texts", KCL figshare,
doi:10.18742/28259054.v1 (article 28259054, published 2025-02-05), 163 TEI XML
files. LICENSE: the deposit is CC BY 4.0 - verified against the figshare API
(GET api.figshare.com/v2/articles/28259054 -> license {"value": 52, "name":
"CC BY", "url": "https://creativecommons.org/licenses/by/4.0/"}). The TEI
headers inside the files still carry the project's 2013 CC BY-NC-SA 3.0
notice; the 2025 institutional deposit of the same texts under CC BY 4.0
supersedes it (the depositor's own later, more permissive grant). --fetch
re-verifies the API license on every run and aborts if it ever changes.

Works ingested (all net-new; none clobbers a served work):

  kekaumenos.consilia-et-narrationes   <- tlg3017.Syno298.sawsGrc01.xml
    Charlotte Roueche's born-digital critical edition (2013) of Kekaumenos
    (11th c. CE), based on the unique ms Moscow Synodalis gr. 298 with the
    conjectures of Wassiliewsky-Jernstedt (1896) and later scholarship; the
    <lem> reading text is served. One record per WJ line (the standard
    page.line citation, from <lb type="WJ" n="p.ll"/>); the manuscript pinax
    and the later vernacular prologue are one record each ("pinax",
    "prologue") with text_lines. The editor's Latin section headings
    (I. POLITICA etc.) and the in-text ms chapter rubrics that Roueche marks
    <surplus> (they duplicate the pinax) are not served as text.

  apophthegmata-et-gnomae.secundum-alphabetum  <- sawsEdGr.*.sawsEd01.xml (28)
    "Apophthegmata et gnomae secundum alphabetum" - the SAWS critical edition
    (Denis Searby and colleagues, Uppsala) of the alphabetical Greek
    apophthegmata collection, from 16 manuscripts. Only the Greek edition
    files (sawsEd01) are served; sawsEd02 files are the English translation,
    sawsEd_App the apparatus, sawsEd_Comm the commentary (all skipped).
    Loci are the edition's own per-figure numbering ("alexander.1",
    "aeschines.2", ...). Cross-reference-only items (e.g. "Democritus 1 =
    Demetrius 4", no text of their own) are skipped and counted.

  gnomologium-vaticanum.gnomologium-vaticanum  <- VatGr743.GV.saws01.xml
    SAWS diplomatic transcription of Vat. gr. 743, the unique witness of the
    Gnomologium Vaticanum (= TLG tlg2945.tlg001; Sternbach's edition numbers
    GV 1-577 are carried in the file and used as loci). The regularized layer
    (<reg>) is served as `text`; the diplomatic layer (<orig>) is kept per
    record in `text_orig`. NOT the same work as the served
    epicurus.gnomologium-vaticanum-epicureum (tlg0537.014, from Vat. gr.
    1950): different manuscript, different collection, no overlap.

  corpus-parisinum.pars-vi-cod-par-gr-1168     <- ParGr1168.CPVI_Par.saws01.xml
  corpus-parisinum.pars-vi-cod-digby-6         <- BodlDig6.CPVI_Dig.saws01.xml
    SAWS transcriptions of Corpus Parisinum pars VI (the "Ekloge
    apophthegmaton kata alphabeton Demokritou, Epiktetou, Isokratous kai
    heteron philosophon"; item numbers CPVI 1-228) in its two witnesses,
    Paris. gr. 1168 and Bodl. Digby 6. The two manuscripts are kept as two
    distinct works (no critical edition exists to merge them); reg/orig
    layers as for the GV. No TLG id exists for the Corpus Parisinum.

Skipped deposit content (verified 2026-07-10):
  - tlg4036.tlg005/006 (Proclus, Elements of Theology / Physics): EXCERPTS
    only (~1.5k / ~1.2k Greek words of 28k / 7.7k-word works), kept by SAWS
    for alignment with the Arabic tradition. COG does not yet serve these
    works at all; serving a 5% excerpt under the canonical work id would
    misrepresent coverage. Flagged for sourcing from a full edition instead.
  - tlg2934.tlg0018 (Sacra Parallela): chapter HEADINGS only; the full text
    is already served (joannes-damascenus.sacra-parallela-..., PG96 OCR).
  - max.PalLXXIII / MelA.Patmos6: chapter headings (pinakes) of Ps.-Maximus
    Loci communes and the Melissa Augustana, a few hundred words each.
  - tlg0086.tlg010-SA (Summa Alexandrinorum): no Greek text (Arabic tradition
    of the Nicomachean Ethics epitome).
  - The Arabic and Arabic-Spanish files (AS2450, CBAr3702, EE1933, HME5683,
    Hun, MAH.*, Misk, MSH.*): not Greek.
  - The gnomologium manuscript-witness transcriptions behind the sawsEdGr
    critical edition (LaurGr86_8/ParSupplGr690/VatGr742 = ApG; BarGr111,
    ChisGrRIV_11, MonGr8, NeapGrII_E_5, VatGr872, VindGrPhil154, VossGrQ13 =
    the F-florilegia; VindGrTheol149 = WA; VatGr1144 = AV I-II): witness
    layer under the served critical edition; substantial Greek, revisit if a
    witness-level serving is ever wanted.

Crosswalk: gnomologium-vaticanum.gnomologium-vaticanum -> tlg2945.tlg001
(verified in the vendored 1999 TLG canon; the registry already pre-mints this
slug for that urn). kekaumenos.consilia-et-narrationes -> AUTHOR-level
tlg3017 only: author 3017 is verified (Wikidata P3576 for Kekaumenos, and
SAWS's own file naming), but author 3017 is absent from the vendored 1999
disc canon and no accessible registry attests the work number, so none is
fabricated; flagged for the next canon pass. The apophthegmata and Corpus
Parisinum works have no TLG identity.

  python scripts/ingest_saws.py --fetch    # download deposit -> sources/saws (md5-verified)
  python scripts/ingest_saws.py            # dry-run: report only
  python scripts/ingest_saws.py --write    # write data/corpus/*.jsonl + crosswalk
  then: python scripts/reconcile_corpus_editions.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "saws"
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
CROSSWALK = REPO / "data" / "tlg_crosswalk.json"

FIGSHARE_ARTICLE = 28259054
FIGSHARE_DOI = "10.18742/28259054.v1"
FIGSHARE_API = f"https://api.figshare.com/v2/articles/{FIGSHARE_ARTICLE}"
EXPECT_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
LICENSE = "CC-BY-4.0"
SOURCE = "saws"

TEI = "{http://www.tei-c.org/ns/1.0}"
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
NS = {"t": "http://www.tei-c.org/ns/1.0"}
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

KEK_SLUG = "kekaumenos.consilia-et-narrationes"
KEK_EDITION = "saws-roueche-2013"
APO_SLUG = "apophthegmata-et-gnomae.secundum-alphabetum"
APO_EDITION = "saws-searby-edgr"
GV_SLUG = "gnomologium-vaticanum.gnomologium-vaticanum"
GV_EDITION = "saws-vatgr743"
CP_PAR_SLUG = "corpus-parisinum.pars-vi-cod-par-gr-1168"
CP_PAR_EDITION = "saws-pargr1168"
CP_DIG_SLUG = "corpus-parisinum.pars-vi-cod-digby-6"
CP_DIG_EDITION = "saws-digby6"

# Greek-alphabet position of each sawsEdGr section, to order the merged
# collection; named-figure files sort before their letter's remainder file
# (the collection opens with Alexander: its item 1 is FP 1).
_LETTER = {
    "A-Apophthegmata": (1, 9), "Alexander": (1, 0), "Anacharsis": (1, 1),
    "Antisthenes": (1, 2), "Aristippus": (1, 3), "Aristoteles": (1, 4),
    "B-Apophthegmata": (2, 9),
    "G-Apophthegmata": (3, 9),
    "D-Apophthegmata": (4, 9), "Demades": (4, 0), "Demetrius": (4, 1),
    "Democrates": (4, 2), "Democritus": (4, 3), "Demosthenes": (4, 4),
    "Diogenes": (4, 5),
    "E-Apophthegmata": (5, 9),
    "Z-Apophthegmata": (6, 9),
    "Ê-Apophthegmata": (7, 9),
    "Th-Apophthegmata": (8, 9), "Thales": (8, 0), "Theocritus": (8, 1),
    "Nicocles": (13, 0),
    "X-Apophthegmata": (14, 9),
    "O-Apophthegmata": (15, 9),
    "P-Apophthegmata": (16, 9), "Plato": (16, 0),
    "Romulus": (17, 0),
    "Socrates": (18, 0),
}

# figure labels occasionally start with a Greek homoglyph (Βasilius) or carry
# the Ê digraph; normalize before slugging
_TRANSLIT = str.maketrans({"Β": "B", "β": "b", "Ê": "E", "ê": "e"})


def fig_slug(name: str) -> str:
    d = unicodedata.normalize("NFD", name.translate(_TRANSLIT).lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", d).strip("-")


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", " ".join(s.split()))


def gk_tokens(text: str) -> int:
    return sum(1 for w in text.split() if GK.search(w))


def local(el) -> str | None:
    return ET.QName(el.tag).localname if isinstance(el.tag, str) else None


LB = object()   # line-break sentinel in collected part streams


def collect(el, drop: frozenset, parts: list, lb_type: str | None = None) -> None:
    """Append el's text content to parts in document order, skipping `drop`
    tags (their tails are kept), inserting the LB sentinel at each <lb> whose
    @type matches lb_type (or at every <lb> when lb_type is '*')."""
    if el.text:
        parts.append(el.text)
    for ch in el:
        name = local(ch)
        if name == "lb" and (lb_type == "*" or (lb_type and ch.get("type") == lb_type)):
            parts.append(LB)
        elif name and name not in drop:
            collect(ch, drop, parts, lb_type)
        if ch.tail:
            parts.append(ch.tail)


def flush_lines(parts: list) -> list[str]:
    lines, cur = [], []
    for p in parts + [LB]:
        if p is LB:
            s = norm("".join(cur))
            if s:
                lines.append(s)
            cur = []
        else:
            cur.append(p)
    return lines


def text_of(el, drop: frozenset) -> str:
    parts: list = []
    collect(el, drop, parts)
    return norm("".join(parts))


# --------------------------------------------------------------- fetch

def fetch() -> None:
    art = json.loads(urllib.request.urlopen(FIGSHARE_API, timeout=60).read())
    lic = art.get("license") or {}
    if lic.get("url") != EXPECT_LICENSE_URL:
        sys.exit(f"ABORT: figshare license changed: {lic!r} (expected CC BY 4.0)")
    if art.get("doi") != FIGSHARE_DOI:
        sys.exit(f"ABORT: figshare DOI mismatch: {art.get('doi')!r}")
    SRC.mkdir(parents=True, exist_ok=True)
    (SRC / "_figshare_article.json").write_text(
        json.dumps(art, indent=1), encoding="utf-8")
    files = [f for f in art["files"] if f["name"] != ".DS_Store"]

    def dl(f):
        dst = SRC / f["name"]
        if dst.exists() and hashlib.md5(dst.read_bytes()).hexdigest() == f["computed_md5"]:
            return f["name"], "cached"
        data = urllib.request.urlopen(f["download_url"], timeout=180).read()
        if hashlib.md5(data).hexdigest() != f["computed_md5"]:
            return f["name"], "MD5 FAIL"
        dst.write_bytes(data)
        return f["name"], "ok"

    with ThreadPoolExecutor(10) as ex:
        results = list(ex.map(dl, files))
    fails = [n for n, st in results if st == "MD5 FAIL"]
    if fails:
        sys.exit(f"ABORT: md5 failures: {fails}")
    print(f"fetched {len(files)} files into {SRC.relative_to(REPO)} "
          f"(license re-verified: {lic.get('name')} {lic.get('url')})")


# --------------------------------------------------------------- kekaumenos

def build_kekaumenos(warnings: list[str]) -> list[dict]:
    body = ET.parse(SRC / "tlg3017.Syno298.sawsGrc01.xml").getroot() \
             .find(".//t:text/t:body", NS)
    recs: list[dict] = []
    drop_common = frozenset({"note", "rdg"})

    def rec(locus, text, section, lines=None):
        r = {"urn": KEK_SLUG, "edition": KEK_EDITION, "locus": locus,
             "source": SOURCE, "license": LICENSE, "text": text,
             "section": section}
        if lines and len(lines) >= 2:
            r["text_lines"] = lines
        return r

    pinax, edition = body.findall("t:div", NS)[:2]
    assert pinax.get("type") == "Pinax" and edition.get("type") == "edition"

    parts: list = []
    collect(pinax, drop_common, parts, lb_type="*")   # keep <surplus>: it wraps the whole pinax
    lines = flush_lines(parts)
    recs.append(rec("pinax", " ".join(lines), "pinax", lines))

    for div in edition.findall("t:div", NS):
        dtype, dn = div.get("type"), div.get("n") or ""
        if dtype in ("Prologue", "Epilogue"):
            # own div, no WJ lineation, wholly inside <surplus> (the later
            # vernacular prologue; the scribal colophon on the 1204 capture
            # of Constantinople): one record each
            locus = dtype.lower()
            parts = []
            collect(div, drop_common, parts, lb_type="*")
            lines = flush_lines(parts)
            recs.append(rec(locus, " ".join(lines), locus, lines))
            continue
        section = dn.replace("divsection", "")
        # main text: drop the editor's Latin <head>s and the ms chapter
        # rubrics marked <surplus>; one record per WJ line
        parts = []
        collect(div, drop_common | {"head", "surplus"}, parts, lb_type="WJ")
        # locus stream parallel to the LB sentinels
        loci = [lb.get("n") for lb in div.findall(f".//{TEI}lb")
                if lb.get("type") == "WJ"]
        pre, *line_texts = _split_stream(parts)
        if pre:
            warnings.append(f"kekaumenos {dn}: text before first WJ lb kept "
                            f"on first line: {pre[:40]!r}")
            if line_texts:
                line_texts[0] = norm(pre + " " + line_texts[0])
            else:
                line_texts = [pre]
        for n, text in zip(loci, line_texts, strict=True):
            if text:
                recs.append(rec(n, text, section))
    # locus sanity
    seen = Counter(r["locus"] for r in recs)
    for dup, k in seen.items():
        if k > 1:
            warnings.append(f"kekaumenos: duplicate locus {dup} x{k}")
    return recs


def _split_stream(parts: list) -> list[str]:
    """[pre-first-LB text, line1, line2, ...] with whitespace normalized;
    empty lines preserved as '' to stay parallel with the lb list."""
    chunks, cur = [], []
    for p in parts + [LB]:
        if p is LB:
            chunks.append(norm("".join(cur)))
            cur = []
        else:
            cur.append(p)
    return chunks


# --------------------------------------------------------------- apophthegmata

_APO_LABEL = re.compile(r"^\s*([^\d(=]+?)\s*(\d+[a-z]?)?\s*(?:[(=].*)?$", re.S)


def build_apophthegmata(warnings: list[str]) -> tuple[list[dict], int]:
    def sect(p: Path) -> str:            # macOS filenames are NFD (Ê)
        return unicodedata.normalize("NFC", p.name.split(".")[1])
    files = sorted(SRC.glob("sawsEdGr.*.sawsEd01.xml"),
                   key=lambda p: (_LETTER[sect(p)], p.name))
    if len(files) != 28:
        warnings.append(f"apophthegmata: expected 28 sawsEd01 files, found {len(files)}")
    recs, skipped_crossrefs = [], 0
    for fn in files:
        body = ET.parse(fn).getroot().find(".//t:text/t:body", NS)
        per_fig_unnumbered: Counter = Counter()
        for seg in body.findall(f".//{TEI}seg"):
            note = seg.find("t:note[@type='source']", NS)
            label = norm(" ".join(note.itertext())) if note is not None else ""
            m = _APO_LABEL.match(label)
            figure = norm(m.group(1)) if m else ""
            num = m.group(2) if m else None
            text = text_of(seg, frozenset({"note"}))
            if not GK.search(text):
                skipped_crossrefs += 1      # "Democritus 1 = Demetrius 4" etc.
                continue
            if not figure:
                warnings.append(f"apophthegmata {fn.name} {seg.get('n')}: "
                                f"unparsed label {label[:40]!r}")
                figure = fn.name.split(".")[1]
            fslug = fig_slug(figure)
            if not num:
                per_fig_unnumbered[fslug] += 1
                locus = f"{fslug}.u{per_fig_unnumbered[fslug]}"
            else:
                locus = f"{fslug}.{num}"
            recs.append({"urn": APO_SLUG, "edition": APO_EDITION,
                         "locus": locus, "source": SOURCE, "license": LICENSE,
                         "text": text, "figure": figure})
    seen = Counter(r["locus"] for r in recs)
    for dup, k in seen.items():
        if k > 1:
            warnings.append(f"apophthegmata: duplicate locus {dup} x{k}")
    return recs, skipped_crossrefs


# --------------------------------------------------------------- gv / cp

_SRC_LABEL = re.compile(r"^\((?:GV|CPVI)(?:\s+([^)]+?))?\s*\)$")
# a "(GV 515b)" / "(CPVI 14)" citation that survives as BARE TEXT inside <reg>
# (a second item supplied within the same seg, or a label not wrapped in
# <note>): it starts its own numbered item
_INLINE_LABEL = re.compile(r"\((?:GV|CPVI)\s+([^)\s]+)\s*\)")


def _split_items(text: str, num: str | None) -> list[tuple[str | None, str]]:
    """[(num, text), ...]: split at inline (GV n)/(CPVI n) labels; `num` is
    the seg's own structured-note number (None for dividers)."""
    pieces = _INLINE_LABEL.split(text)
    items = []
    if norm(pieces[0]):
        items.append((num, norm(pieces[0])))
        num = None
    for lbl, t in zip(pieces[1::2], pieces[2::2]):
        t = norm(t)
        if num is None and not items:
            items.append((lbl, t))     # leading bare label: the seg's number
        elif t:
            items.append((lbl, t))
    if not items and num is not None:
        items.append((num, ""))
    return items


def build_ms_transcription(fname: str, slug: str, edition: str,
                           warnings: list[str]) -> list[dict]:
    body = ET.parse(SRC / fname).getroot().find(".//t:text/t:body", NS)
    drop = frozenset({"note", "del"})
    recs: list[dict] = []
    for top in body.findall("t:div", NS):
        if (top.get("n") or "").startswith("Relations"):
            continue                       # SAWS linkage metadata, no text
        for seg in top.findall(f".//{TEI}seg"):
            reg = seg.find("t:choice/t:reg", NS)
            orig = seg.find("t:choice/t:orig", NS)
            if reg is None:
                warnings.append(f"{slug}: seg {seg.get(XMLID)} has no <reg>")
                continue
            note = reg.find("t:note[@type='source']", NS)
            label = norm(" ".join(note.itertext())) if note is not None else ""
            m = _SRC_LABEL.match(label)
            if label and not m:
                warnings.append(f"{slug}: odd source label {label!r}")
            num = m.group(1) if m else None
            text = text_of(reg, drop)
            text_orig = text_of(orig, drop) if orig is not None else ""
            text_orig = norm(_INLINE_LABEL.sub(" ", text_orig))
            xid = seg.get(XMLID) or ""
            comps = xid.split(".")
            fig_div = comps[-2] if len(comps) >= 2 else ""
            figure = re.sub(r"\d+$", "", fig_div)
            if not text and not text_orig:
                continue
            for k, (inum, itext) in enumerate(_split_items(text, num)):
                if inum:
                    if recs and recs[-1].get("_num") == inum:
                        # one item split over two segs (ms seam): merge
                        recs[-1]["text"] = norm(recs[-1]["text"] + " " + itext)
                        if k == 0 and text_orig:
                            recs[-1]["text_orig"] = norm(
                                recs[-1].get("text_orig", "") + " " + text_orig)
                        continue
                    locus = inum
                else:
                    locus = f"{fig_slug(fig_div) or 'div'}.{seg.get('n') or 't'}"
                r = {"urn": slug, "edition": edition, "locus": locus,
                     "source": SOURCE, "license": LICENSE, "text": itext,
                     "figure": figure, "_num": inum}
                if k == 0 and text_orig:
                    r["text_orig"] = text_orig
                recs.append(r)
    seen: Counter = Counter()
    for r in recs:
        r.pop("_num", None)
        seen[r["locus"]] += 1
        if seen[r["locus"]] > 1:
            old = r["locus"]
            r["locus"] = f"{old}-{seen[old]}"
            warnings.append(f"{slug}: non-consecutive duplicate locus {old} "
                            f"-> {r['locus']}")
    return recs


# --------------------------------------------------------------- write

def add_crosswalk_entries(write: bool) -> list[str]:
    cw = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    added = []
    entries = {
        GV_SLUG: {
            "cts": "urn:cts:greekLit:tlg2945.tlg001",
            "tlg": "tlg2945.tlg001",
            "author_slug": "gnomologium-vaticanum",
            "title": "Gnomologium Vaticanum",
        },
        KEK_SLUG: {
            "cts": "urn:cts:greekLit:tlg3017",
            "tlg": "tlg3017",
            "author_slug": "kekaumenos",
            "title": "Consilia et Narrationes",
            "note": ("author-level id only: 3017 verified (current TLG; "
                     "Wikidata P3576), absent from the vendored 1999 disc "
                     "canon; work number pending a canon pass"),
        },
    }
    for slug, entry in entries.items():
        if slug not in cw:
            cw[slug] = entry
            added.append(slug)
    if added and write:
        # match build_id_crosswalk.py's exact serialization (indent=0, no
        # trailing newline) so re-runs of either writer produce no churn
        CROSSWALK.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                             encoding="utf-8")
    return added


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="download the figshare deposit into sources/saws")
    ap.add_argument("--write", action="store_true",
                    help="write corpus jsonl files and crosswalk entries")
    args = ap.parse_args()

    if args.fetch:
        fetch()
        return

    if not (SRC / "tlg3017.Syno298.sawsGrc01.xml").exists():
        sys.exit("sources/saws is empty - run with --fetch first")

    warnings: list[str] = []
    works: list[tuple[str, list[dict]]] = []

    kek = build_kekaumenos(warnings)
    works.append((KEK_SLUG, kek))
    apo, skipped = build_apophthegmata(warnings)
    works.append((APO_SLUG, apo))
    works.append((GV_SLUG, build_ms_transcription(
        "VatGr743.GV.saws01.xml", GV_SLUG, GV_EDITION, warnings)))
    works.append((CP_PAR_SLUG, build_ms_transcription(
        "ParGr1168.CPVI_Par.saws01.xml", CP_PAR_SLUG, CP_PAR_EDITION, warnings)))
    works.append((CP_DIG_SLUG, build_ms_transcription(
        "BodlDig6.CPVI_Dig.saws01.xml", CP_DIG_SLUG, CP_DIG_EDITION, warnings)))

    mode = "WRITE" if args.write else "DRY"
    print(f"[{mode}] SAWS ingest (figshare {FIGSHARE_DOI}, {LICENSE})")
    for slug, recs in works:
        toks = sum(gk_tokens(r["text"]) for r in recs)
        clobber = "  ** FOREIGN WORK AT SLUG - NOT WRITTEN **" \
            if _foreign(slug) else ""
        print(f"  {slug}: {len(recs)} records, {toks:,} Greek tokens "
              f"(edition {recs[0]['edition']}){clobber}")
    print(f"  apophthegmata cross-reference-only items skipped: {skipped}")
    for w in warnings:
        print(f"  WARN: {w}")

    added = add_crosswalk_entries(args.write)
    print(f"  crosswalk entries {'added' if args.write else 'to add'}: {added}")

    if not args.write:
        return
    for slug, recs in works:
        dst = CORPUS / f"{slug}.jsonl"
        if _foreign(slug):
            print(f"  SKIP {slug}: a non-saws work is served at this slug "
                  f"(clobber guard)")
            continue
        with dst.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  wrote {dst.relative_to(REPO)}")
    print("now run: python scripts/reconcile_corpus_editions.py")


def _foreign(slug: str) -> bool:
    """True when the slug is already served by a NON-saws work (never
    overwrite silently); re-runs may freely rewrite this script's own
    output (source == saws all rows)."""
    for base in (CORPUS, SECONDARY):
        p = base / f"{slug}.jsonl"
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                if line.strip() and json.loads(line).get("source") != SOURCE:
                    return True
    return False


if __name__ == "__main__":
    main()
