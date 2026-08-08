#!/usr/bin/env python3
"""Ingest the Byzantine historians from byzantium.gr as the `byzantium_gr` source:
clean public-domain transcriptions of the Bonn / CSHB editions, the preferred
route (over CGPG's Migne OCR) for the works in the byzantium.gr sweep.

The work -> page-URL mapping comes from data/pd_research/byzantium_sweep.json
(gap matches + locked-unlock candidates). Each work is one or more .php pages of
continuous polytonic Greek with nav menus in <a> links. We fetch (and cache) each
page, drop the navigation, and keep the substantial polytonic lines - the length
+ polytonic filter cleanly excludes the menu remnants and the monotonic
modern-Greek editorial summaries. Because these are single TLG works (unlike the
Migne volumes), we key directly by the TLG work so the text fills the gap:

  data/corpus/<author.work slug>.jsonl   {urn: "<author.work slug>",
      edition: "byzantium-gr", locus: "1.2.3", source: "byzantium_gr",
      license: "PD", text: "..."}

Pages are cached under data/cache/byzantium_gr/ (gitignored); re-runs reuse the
cache. Per the project note, the byzantium.gr text is trusted as-is (not diffed
against scans).

Loci follow the page's own citation structure where it is detectable. Many pages
carry real book/chapter markup: <h2>/<h3> headers like "ΛΟΓΟΣ Α'", "ΒΙΒΛΙΟΝ Α'"
or "ΤΟΜΟΣ ..." open a book, and short underlined <u> Greek-letter numerals
("αʹ", "βʹ", ...) open a chapter. We decode those Greek-letter numerals to arabic
integers and emit "<book>.<chapter>" (or "<book>.<chapter>.<para>" when several
paragraphs sit under one chapter, "<book>.<para>" when a work has books but no
chapters). On top of that generic scheme, WORK_RULES below teaches the ingester
each page family's own citation layer - inline "[1.1]" chapter.section tags
(Sphrantzes), TLG-style "[Mich1.2]" reign tags (Skylitzes), bracketed edition
pages (Scylitzes Continuatus), leading "2.14" book.section tags (Psellos),
arabic chapter numbers (De administrando), "ασια.5" theme tags (De thematibus),
"1.29" volume.page marks (De cerimoniis), "Κόσμου ἔτη ..." annus-mundi headers
(Theophanes), and the reign/tome headings of Choniates and the ordinal-word
book headings of Pachymeres. Every rule reads
markers the source itself prints; a marker that steps backward out of sequence
(a stray number) is ignored rather than guessed at. A repeated book label on a
later page whose chapters restart is the one exception: kantakouzen4 opens
"[ΙΣΤΟΡΙΑ Γ’]" again after kantakouzen3, so we renumber it as the next book (see
_bump_books for the evidence). Any page/work with no detectable structure falls
back to the original "<pagestem>.<paragraph-index>" scheme, so we never emit a
guessed locus. Merges into corpus_editions.json like the other ingesters.

  python scripts/build_byzantium_gr_corpus.py [--work tlg4145.001] [--refetch]
  python scripts/build_byzantium_gr_corpus.py --dry-run [--work ...]   # print loci, no writes
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

import lxml.html

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
sys.path.insert(0, str(REPO / "scripts"))
from crosswalk import slug_for  # noqa: E402
CORPUS = DATA / "corpus"
CE = DATA / "corpus_editions.json"
SWEEP = DATA / "pd_research" / "byzantium_sweep.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose_spacing_breathings import compose as _compose_breathings  # noqa: E402
WORKS_OUT = DATA / "byzantium_gr_works.json"
CACHE = DATA / "cache" / "byzantium_gr"
BASE = "https://byzantium.gr/keimena/"

EDITION = "byzantium-gr"
SOURCE = "byzantium_gr"
LICENSE = "PD"
UA = "cog-byzantium-gr-ingest/1.0 (open Greek corpus; contact via repo)"

MIN_GREEK = 40                              # a real paragraph, not a nav remnant
_GK = re.compile(r"[Ͱ-Ͽἀ-῿Ά-ώ]")           # any Greek (incl. monotonic)
_POLY = re.compile(r"[ἀ-῿]")                # polytonic block: marks the ancient text
_GK_TOK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")       # token for counting
_BLOCK = {"br", "p", "div", "hr", "tr", "li", "td", "h1", "h2", "h3",
          "h4", "h5", "h6", "blockquote"}
_HEAD = {"h1", "h2", "h3", "h4", "h5", "h6"}

# --- Greek-letter numeral -> int -------------------------------------------
# keraia / numeral-sign / apostrophe variants that mark a Greek-letter numeral
_KER = ("ʹʹ’'´΄′`‘‵׳")
_GK_LETTER = re.compile(r"[Ά-ϡ]")     # basic + accented + archaic letters
_NUM = {"α": 1, "β": 2, "γ": 3, "δ": 4, "ε": 5, "ϛ": 6, "ϝ": 6, "ζ": 7,
        "η": 8, "θ": 9, "ι": 10, "κ": 20, "λ": 30, "μ": 40, "ν": 50,
        "ξ": 60, "ο": 70, "π": 80, "ϟ": 90, "ϙ": 90, "ρ": 100, "σ": 200,
        "τ": 300, "υ": 400, "φ": 500, "χ": 600, "ψ": 700, "ω": 800, "ϡ": 900}

# a numeral token: a Greek letter then more letters / keraia / space / dot
_NUMERAL = r"[Ά-ϡ][Ά-ϡ" + _KER + r"\s.]{0,9}"
# a book opener: ΛΟΓΟΣ / ΒΙΒΛΙΟΝ / ΒΙΒΛΙΟ / ΤΟΜΟΣ / ΙΣΤΟΡΙΑ (also the genitives
# ΙΣΤΟΡΙΑΣ / ΙΣΤΟΡΙΩΝ used by Leo Diaconus and Chalcocondyles) plus a numeral;
# the (?!ΛΟΓ...) lookahead keeps a stacked keyword ("ΙΣΤΟΡΙΑΣ ΒΙΒΛΙΟΝ Αʹ",
# Simocatta) from being swallowed as a huge letter-numeral - the inner keyword
# must win, giving book 1, not ΒΙΒΛΙΟΝΑ = 175
_BOOK_KW = r"(?:ΛΟΓΟΣ|ΒΙΒΛΙΟΝ|ΒΙΒΛΙΟ|ΤΟΜΟΣ|ΙΣΤΟΡΙΩΝ|ΙΣΤΟΡΙΑΣ|ΙΣΤΟΡΙΑ)"
_BOOK_NUM = re.compile(_BOOK_KW + r"\s+(?!" + _BOOK_KW + r")(" + _NUMERAL + r")")
# the relaxed variant for headings whose numeral has no keraia: a short bare
# letter run closing the heading, "ΒΙΒΛΙΟΝ Α." / "ΛΑΟΝΙΚΟΥ ... ΙΣΤΟΡΙΩΝ Στ"
_BOOK_BARE = re.compile(_BOOK_KW + r"\s+([Ά-ϡ]{1,3})\s*\.?\s*$")


def greek_numeral(s: str, keraia: bool = True):
    """Decode a Greek-letter numeral (αʹ=1, ιβʹ=12, ΙΣτʹ=16) to int, else None.
    By default requires a keraia/apostrophe mark, so ordinary words never parse
    as numbers; keraia=False decodes a bare letter run (heading context only)."""
    s = unicodedata.normalize("NFC", s)
    if keraia and not any(c in _KER for c in s):
        return None
    letters = "".join(_GK_LETTER.findall(s))
    letters = letters.replace("ς", "ϛ")     # final sigma ς -> stigma (6)
    letters = letters.casefold()
    letters = "".join(c for c in unicodedata.normalize("NFD", letters)
                      if unicodedata.category(c) != "Mn")
    letters = letters.replace("στ", "ϛ")   # στ ligature -> stigma (6)
    if not letters:
        return None
    total = 0
    for c in letters:
        v = _NUM.get(c)
        if v is None:
            return None
        total += v
    return total or None


def book_num(text: str):
    """Book number from a heading like 'ΛΟΓΟΣ Α'.' / 'ΒΙΒΛΙΟΝ Βʹ', else None.
    Falls back to a bare (keraia-less) numeral only when it closes the heading."""
    text = unicodedata.normalize("NFC", text)
    m = _BOOK_NUM.search(text)
    n = greek_numeral(m.group(1)) if m else None
    if n is None:
        m = _BOOK_BARE.search(text)
        n = greek_numeral(m.group(1), keraia=False) if m else None
    return n


def page_url(p: str) -> str:
    return p if p.startswith("http") else BASE + p


def page_stem(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0]


def fetch(url: str, refetch: bool = False) -> str:
    """Fetch a page as UTF-8, caching to data/cache/byzantium_gr/."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / (page_stem(url) + ".html")
    if cached.exists() and not refetch:
        return cached.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", errors="replace")
    cached.write_text(html, encoding="utf-8")
    time.sleep(1.0)                          # be polite between live fetches
    return html


# --- per-work citation rules -----------------------------------------------
# Each rule teaches extract_loci one page family's own citation layer. A rule
# may provide "line" (called on every flushed paragraph; returns the base for
# that paragraph when a citation tag opens it, and advances the running context
# in st) and/or "mark" (called on <h*>/<b> [BK] and <u> [CH] marker texts).
# All tags are printed by the source itself and stay verbatim in the text; the
# rules only READ them. Out-of-sequence tags (a stray number) are ignored.
# "scheme" labels the resulting citation scheme in byzantium_gr_works.json.

def _tag_line(rx, decode):
    """Line rule for inline citation tags: a tag at the very start keys the
    line; every accepted tag advances the running context, but a mid-line tag
    (a break falling inside a paragraph) only applies from the next line on."""
    def line_fn(line, st):
        row_base = st.get("base")
        for m in rx.finditer(line):
            base = decode(m, st)             # None: out of sequence / mid-line
            if base is None:
                continue
            if m.start() == 0:
                row_base = base
            st["base"] = base
        return row_base
    return line_fn


# Sphrantzes, Chronicon Minus: literal "[1.1]" ... "[48.4]" chapter.section
# tags at paragraph starts ("[t.1]" for the title). Monotonic in (ch, sec).
_SFR_RX = re.compile(r"\[(t|\d{1,2})\.(\d{1,2})\]")

def _dec_sphrantzes(m, st):
    v = (0 if m.group(1) == "t" else int(m.group(1)), int(m.group(2)))
    if v < st.get("cur", (0, 0)):
        return None
    st["cur"] = v
    return f"{m.group(1)}.{m.group(2)}"


# Skylitzes, Synopsis: TLG-style bracketed reign tags "[Mich1.2]" ("[pro.1]"
# for the prooimion, "[X.t]" for a title; "[Mich1.2.30]" adds an edition line
# ref inside the chapter, so only the first two parts key the passage).
_SKY_RX = re.compile(r"\[([A-Za-z][A-Za-z0-9]{1,11})\.(t|\d{1,3})(?:\.\d{1,3})?\]")

def _dec_skylitzes(m, st):
    reign, sec = m.group(1), m.group(2)
    n = 0 if sec == "t" else int(sec)
    if reign == st.get("reign") and n < st.get("sec", 0):
        return None                          # backward within a reign: stray
    st["reign"], st["sec"] = reign, n
    return f"{reign}.{sec}"


# Scylitzes Continuatus: bracketed edition pages "[103]" ... "[186]" (the
# continuation fills pp. 103-186 in Tsolakes' 1968 edition, the page range the
# source's own marks cover). Monotonic; a passage is keyed by the page it opens on.
_SKY0_RX = re.compile(r"\[(\d{2,3})\]")

def _dec_scyl_cont(m, st):
    n = int(m.group(1))
    if n < st.get("page", 0):
        return None
    st["page"] = n
    return str(n)


# Psellos, Chronographia: every section opens with the source's own printed
# "2.14"-style book.section tag ("1.5τ" marks a section title, "2.τ" a book
# title). The continuation parts carry Greek-keyboard transliterations of the
# standard part labels: "6 τηεοδ" (Theodora) = 6a, "7 ξονστ" (Constantine X)
# = 7a, "7 ευδ,ρομ" (Eudocia + Romanos IV) = 7b, "7 μιξη" (Michael VII) = 7c.
_PS_RX = re.compile(                         # "\. ?": the source types "τηεοδ. 1τ"
    r"([1-7])(?:\s+(τηεοδ|ξονστ|ευδ,ρομ|μιξη))?\. ?(τ|\d{1,3})τ?")
_PS_PART = {"τηεοδ": "6a", "ξονστ": "7a", "ευδ,ρομ": "7b", "μιξη": "7c"}
_PS_ORDER = {p: i for i, p in enumerate(
    ["1", "2", "3", "4", "5", "6", "6a", "7", "7a", "7b", "7c"])}

def _dec_psellus(m, st):
    if m.start() != 0:                       # tags only open paragraphs
        return None
    part = _PS_PART[m.group(2)] if m.group(2) else m.group(1)
    sec = 0 if m.group(3) == "τ" else int(m.group(3))
    v = (_PS_ORDER[part], sec)
    if v < st.get("cur", (0, 0)):
        return None
    st["cur"] = v
    return f"{part}.{sec}" if sec else part


# De administrando imperio: arabic chapter numbers 1-53 open the chapters
# inline ("1 Περὶ τῶν Πατζινακιτῶν ..."); the proem sits under <h3>Προοίμιον.
# Chapter 12 is a single sentence glued to chapter 11's paragraph (no break in
# the source), so it rides inside the 11-keyed passage; 13 re-syncs. The
# "ὁ\s*" prefix absorbs a stray bold ὁ the source drops before chapter 31.
_DAI_RX = re.compile(r"(?:ὁ\s*)?(\d{1,2})\s+[Ά-ϡἀ-῿]")

def _dec_administrando(m, st):
    if m.start() != 0:
        return None
    n = int(m.group(1))
    if n <= st.get("ch", 0):
        return None
    st["ch"] = n
    return str(n)

def _mark_administrando(kind, text, st):
    if kind == "BK" and text.rstrip(".") == "Προοίμιον":
        st["base"] = "pr"


# De thematibus: the source prints its own theme tags - "προλογ.1", then
# "ασια.2" ... "ασια.17" (book 1, Asia) and "ευροπ.1" ... "ευροπ.12" (book 2,
# Europe) - usually as standalone lines, sometimes glued to the surrounding
# text. We transliterate the tag and keep its numbering; a tag not opening its
# line applies from the next paragraph (the theme starts after it).
_THEMA_RX = re.compile(r"(προλογ|ασια|ευροπ)\.(\d{1,2})")
_THEMA_BOOK = {"προλογ": "prol", "ασια": "asia", "ευροπ": "europ"}

def _line_thematibus(line, st):
    row_base = st.get("base")
    m = _THEMA_RX.search(line)
    if m:
        base = f"{_THEMA_BOOK[m.group(1)]}.{m.group(2)}"
        if m.start() == 0:
            row_base = base                  # short tag lines are dropped anyway
        st["base"] = base
    return row_base


# De cerimoniis: the source marks Vogt's volume.page throughout - "1.3" ...
# "1.175" then "2.1" ... "2.186" - as <u> page breaks and as prefixes on the
# chapter-title <h3>s. The Greek chapter numerals on this page carry a dual
# (Vogt/Reiske) numbering with several typos, so the clean monotonic page
# marks are the citation we trust. Typos like "12.94" or ".154" fall out of
# sequence and are ignored (the paragraph keeps the previous page context).
_CER_RX = re.compile(r"(\d{1,2})\.(\d{1,3})(?=\s|$)")

def _dec_cerimoniis(m, st):
    if m.start() != 0:
        return None
    v = (int(m.group(1)), int(m.group(2)))
    cur = st.get("cur", (1, 0))
    if v == cur:                             # the same page marked twice
        return f"{v[0]}.{v[1]}"
    if not (v > cur and (v[0] == cur[0] or (v[0] == cur[0] + 1 and v[1] <= 40))):
        return None
    st["cur"] = v
    return f"{v[0]}.{v[1]}"


# Theophanes, Chronographia: the annals open with the source's own year-of-
# the-world headers, "Κόσμου ἔτη ͵εψοζʹ." (AM 5777) ... "͵ϛτδʹ" (6304) - the
# standard citation for the work (de Boor keys his margins by AM). The lower
# keraia ͵ multiplies the following letter by 1000. Paragraphs without a
# header continue the open year. Preamble/regnal-list rows keep the stem.
_THEO_RX = re.compile(r"Κόσμου ἔτη (͵[Ά-ϡ][Ά-ϡ" + _KER + r"]*)")

def _dec_theophanes(m, st):
    tok = m.group(1)
    thousands = greek_numeral(tok[1], keraia=False)
    rest = tok[2:]
    units = greek_numeral(rest) if _GK_LETTER.search(rest) else 0
    if thousands is None or units is None:
        return None
    n = thousands * 1000 + units
    if n < st.get("am", 0):
        return None
    st["am"] = n
    return str(n)


# Acropolites, Annales: arabic section numbers 1-89 in <u>, no books.
def _mark_acropolites(kind, text, st):
    if kind == "CH" and re.fullmatch(r"\d{1,2}", text) \
            and int(text) > st.get("sec", 0):
        st["sec"] = int(text)
        st["base"] = text

# Acropolites, Contra Latinos: dotted "1.1" ... "2.28" logos.section in <u>.
def _mark_contra_latinos(kind, text, st):
    if kind != "CH":
        return
    m = re.fullmatch(r"([12])\.(\d{1,2})", text)
    if m:
        v = (int(m.group(1)), int(m.group(2)))
        if v >= st.get("cur", (0, 0)):
            st["cur"] = v
            st["base"] = text


# Choniates, Historia: the source divides the work by reign (and by ΤΟΜΟΣ
# within a reign), the CSHB's own book divisions. Exact heading -> base.
_CHONIATES = {
    "ΠΡΟΟΙΜΙΟΝ": "pr",
    "ΒΑΣΙΛΕΙΑ ΚΥΡ ΙΩΑΝΝΟΥ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Io",
    "ΒΑΣΙΛΕΙΑ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.1",
    "ΤΟΜΟΣ ΠΡΩΤΟΣ": "Man.1",                 # the <b> right under the heading
    "ΤΟΜΟΣ ΔΕΥΤΕΡΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.2",
    "ΤΟΜΟΣ ΤΡΙΤΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.3",
    "ΤΟΜΟΣ ΤΕΤΑΡΤΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.4",
    "ΤΟΜΟΣ ΠΕΜΠΤΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.5",
    "ΤΟΜΟΣ ΕΚΤΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.6",
    "ΤΟΜΟΣ ΕΒΔΟΜΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Man.7",
    "ΒΑΣΙΛΕΙΑ ΑΛΕΞΙΟΥ ΤΟΥ ΠΟΡΦΥΡΟΓΕΝΝΗΤΟΥ ΤΟΥ ΥΙΟΥ ΤΟΥ ΒΑΣΙΛΕΩΣ "
    "ΜΑΝΟΥΗΛ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Alex2",
    "ΒΑΣΙΛΕΙΑ ΑΝΔΡΟΝΙΚΟΥ ΤΟΥ ΚΟΜΝΗΝΟΥ ΕΝ ΤΟΜΟΙΣ ΔΥΣΙ": "Andr.1",
    "ΤΟΜΟΣ ΔΕΥΤΕΡΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΑΝΔΡΟΝΙΚΟΥ ΤΟΥ ΚΟΜΝΗΝΟΥ": "Andr.2",
    "ΒΑΣΙΛΕΙΑ ΙΣΑΑΚΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ": "Isaac.1",
    "ΤΟΜΟΣ ΔΕΥΤΕΡΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΙΣΑΑΚΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ": "Isaac.2",
    "ΤΟΜΟΣ ΤΡΙΤΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΙΣΑΑΚΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ": "Isaac.3",
    "ΒΑΣΙΛΕΙΑ ΑΛΕΞΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ ΤΟΜΟΣ ΠΡΩΤΟΣ": "Alex3.1",
    "ΤΟΜΟΣ ΔΕΥΤΕΡΟΣ ΤΗΣ ΒΑΣΙΛΕΙΑΣ ΑΛΕΞΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ": "Alex3.2",
    "ΒΑΣΙΛΕΙΑ ΔΕΥΤΕΡΑ ΙΣΑΑΚΙΟΥ ΤΟΥ ΑΓΓΕΛΟΥ ΚΑΙ ΤΟΥ ΥΙΟΥ ΑΥΤΟΥ ΑΛΕΞΙΟΥ":
        "IsaacAlex4",
    "ΒΑΣΙΛΕΙΑ ΑΛΕΞΙΟΥ ΤΟΥ ΔΟΥΚΑ ΤΟΥ ΚΑΙ ΜΟΥΡΤΖΟΥΦΛΟΥ": "Murtz",
    "ΤΟΥ ΑΥΤΟΥ ΧΩΝΙΑΤΟΥ ΤΑ ΜΕΤΑ ΤΗΝ ΑΛΩΣΙΝ ΤΗΣ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ "
    "ΣΥΜΒΑΝΤΑ ΤΟΙΣ ΡΩΜΑΙΟΙΣ": "Halosis",
}

def _mark_choniates(kind, text, st):
    base = _CHONIATES.get(text.strip(" ."))
    if base:
        st["base"] = base


# Pachymeres, De Michaele Palaeologo: six kephalaia tables ("ΚΕΦΑΛΑΙΑ ΤΟΥ
# <ordinal> ΛΟΓΟΥ" -> "<n>.t") precede six books ("{ΣΥΓΓΡΑΦΙΚΩΝ ΙΣΤΟΡΙΩΝ
# <ordinal>}"). Each book's text opens directly in chapter 1 (the source
# underlines chapter numerals only from βʹ on), then <u> numerals advance it.
_ORD = {"ΠΡΩΤ": 1, "ΔΕΥΤΕΡ": 2, "ΤΡΙΤ": 3, "ΤΕΤΑΡΤ": 4, "ΠΕΜΠΤ": 5, "ΕΚΤ": 6}
_PACH_TOC = re.compile(r"ΚΕΦΑΛΑΙΑ ΤΟΥ (\w+) ΛΟΓΟΥ")
_PACH_BOOK = re.compile(r"ΣΥΓΓΡΑΦΙΚΩΝ ΙΣΤΟΡΙΩΝ (\w+)")

def _ordinal(word):
    for stem, n in _ORD.items():
        if word.startswith(stem):
            return n
    return None

def _mark_pachymeres(kind, text, st):
    if kind == "BK":
        m = _PACH_TOC.search(text)
        n = _ordinal(m.group(1)) if m else None
        if n:
            st.update(base=f"{n}.t", book=None, chapter=None)
            return
        m = _PACH_BOOK.search(text)
        n = _ordinal(m.group(1)) if m else None
        if n:
            st.update(base=None, book=n, chapter=1)
    else:
        _gen_chapter(text, st)


def _gen_chapter(text, st):
    """Generic <u> chapter numeral: accept only a forward step inside the
    current book, so a stray underlined numeral can't restart the count."""
    cn = greek_numeral(text)
    if cn is not None and (st.get("chapter") is None or cn > st["chapter"]):
        st["chapter"] = cn


# tlg key -> rule. Works without a rule use the generic book/chapter logic.
WORK_RULES = {
    "tlg3143.001": {"scheme": "chapter.section",     # Sphrantzes, Chron. Minus
                    "line": _tag_line(_SFR_RX, _dec_sphrantzes)},
    "tlg3063.001": {"scheme": "reign.chapter",       # Skylitzes, Synopsis
                    "line": _tag_line(_SKY_RX, _dec_skylitzes)},
    "tlg3064.002": {"scheme": "edition-page",        # Scylitzes Continuatus
                    "line": _tag_line(_SKY0_RX, _dec_scyl_cont)},
    "tlg2702.001": {"scheme": "book.section",        # Psellos, Chronographia
                    "line": _tag_line(_PS_RX, _dec_psellus)},
    "tlg4046.001": {"scheme": "annus mundi",         # Theophanes, Chronographia
                    "line": _tag_line(_THEO_RX, _dec_theophanes)},
    "tlg3023.008": {"scheme": "chapter",             # De administrando imperio
                    "line": _tag_line(_DAI_RX, _dec_administrando),
                    "mark": _mark_administrando},
    "tlg3023.009": {"scheme": "book.theme",          # De thematibus
                    "line": _line_thematibus},
    "tlg3023.010": {"scheme": "vol.page (Vogt)",     # De cerimoniis
                    "line": _tag_line(_CER_RX, _dec_cerimoniis)},
    "tlg3141.002": {"scheme": "section",             # Acropolites, Annales
                    "mark": _mark_acropolites},
    "tlg3141.010": {"scheme": "book.section",        # Acropolites, C. Latinos
                    "mark": _mark_contra_latinos},
    "tlg3094.001": {"scheme": "reign/tome",          # Choniates, Historia
                    "mark": _mark_choniates},
    "tlg3142.001": {"scheme": "book.chapter",        # Pachymeres, De Michaele
                    "mark": _mark_pachymeres},
}


def extract_loci(html: str, stem: str, rule=None, st=None):
    """Return rows [[base, text], ...] for a byzantium.gr page, nav removed.

    We walk the cleaned HTML in document order keeping a running citation
    context in `st` (threaded across a work's pages by work_loci): <h*>/<b>
    headers matching a book opener set the book (and reset the chapter), and
    short <u> Greek-letter numerals set the chapter. A per-work rule overrides
    that generic reading with the page family's own citation layer (see
    WORK_RULES). A row's base is a (book[, chapter]) tuple from the generic
    logic, a string from a rule, or None for preamble text before any marker
    (work_loci keys those to the page stem). The polytonic-length filter keeps
    only running prose, exactly as before.
    """
    st = {} if st is None else st
    doc = lxml.html.fromstring(html)
    for bad in doc.xpath("//script|//style|//comment()|//a"):
        if bad.tag == "a":
            bad.drop_tree()                  # remove the nav link, keep its tail
        else:
            parent = bad.getparent()
            if parent is not None:
                parent.remove(bad)

    # serialise to a stream of text fragments + structural markers, in doc order
    parts: list = []

    def walk(el):
        if el.tag in _BLOCK:
            parts.append("\n")
        if el.tag in _HEAD or el.tag == "b":
            parts.append(("BK", " ".join((el.text_content() or "").split())))
        elif el.tag == "u":
            parts.append(("CH", " ".join((el.text_content() or "").split())))
        if el.text:
            parts.append(el.text)
        for ch in el:
            walk(ch)
            if ch.tail:
                parts.append(ch.tail)
        if el.tag in _BLOCK:
            parts.append("\n")

    walk(doc)

    rows: list = []                          # [base_or_None, text]
    buf: list[str] = []

    def flush():
        line = unicodedata.normalize("NFC", " ".join("".join(buf).split()))
        buf.clear()
        if not line:
            return
        if rule and "line" in rule:
            base = rule["line"](line, st)    # the rule's verdict is final
        else:
            base = st.get("base")
            if base is None and st.get("book") is not None:
                base = (st["book"], st["chapter"]) \
                    if st.get("chapter") is not None else (st["book"],)
        gk = sum(1 for c in line if _GK.match(c))
        # keep running prose: enough Greek AND polytonic (drops monotonic modern-
        # Greek editorial notes and the short all-caps headers / menu remnants)
        if gk >= MIN_GREEK and _POLY.search(line):
            rows.append([base, line])

    for p in parts:
        if isinstance(p, tuple):
            flush()
            text = unicodedata.normalize("NFC", p[1])
            if rule and "mark" in rule:
                rule["mark"](p[0], text, st)
            elif rule:
                pass                         # tag-driven works ignore headings
            elif p[0] == "BK":
                bn = book_num(text)
                if bn is not None:
                    st["book"], st["chapter"] = bn, None
            else:
                _gen_chapter(text, st)
        elif p == "\n":
            flush()
        else:
            buf.append(p)
    flush()
    return rows


def _bump_books(pages):
    """Disambiguate a repeated book label across a work's pages.

    kantakouzen4 opens "[ΙΣΤΟΡΙΑ Γ’]" although kantakouzen3 already carried
    ΙΣΤΟΡΙΑ Γ’: page 3's book runs αʹ to ρʹ (100 chapters) and page 4 restarts
    at αʹ and runs to νʹ (50), exactly the shape of Historiarum book 4 in the
    Bonn edition (book III has 100 chapters, book IV has 50). So a later page
    that reopens an already-seen book number with its chapters RESTARTING is
    the source repeating a label, and we renumber that page's books to continue
    the sequence. A page whose chapters continue forward is a genuine
    continuation and is left alone.
    """
    opened: dict = {}                        # book -> last chapter seen (0: none)
    for _, rows in pages:
        tb = [r for r in rows if isinstance(r[0], tuple)]
        if not tb:
            continue
        b0 = tb[0][0][0]
        c0 = tb[0][0][1] if len(tb[0][0]) > 1 else 0
        off = max(opened) + 1 - b0 if b0 in opened and c0 <= opened[b0] else 0
        for r in tb:
            if off:
                r[0] = (r[0][0] + off,) + r[0][1:]
            b = r[0][0]
            c = r[0][1] if len(r[0]) > 1 else 0
            opened[b] = max(opened.get(b, 0), c)


def load_works():
    """Uniform [{tlg_id, work_id, urls[], title, author}] from the sweep."""
    d = json.loads(SWEEP.read_text(encoding="utf-8"))
    works = []
    for w in d["gap_works_recoverable_as_text"]:
        works.append({"tlg_id": w["tlg_id"], "work_id": str(w["work_id"]).zfill(3),
                      "urls": [page_url(u) for u in w["byzantium_urls"]],
                      "title": w.get("title", ""), "author": w.get("author", "")})
    for w in d["byzantium_locked_unlock_candidates"]:
        works.append({"tlg_id": w["tlg_id"], "work_id": str(w["work_id"]).zfill(3),
                      "urls": [page_url(p) for p in w["pages"]],
                      "title": w.get("work", ""), "author": ""})
    return works


def work_loci(w, refetch=False, dry_run=False):
    """Collect (loci, scheme, pages) for a work, combining all its pages.

    The citation context is threaded across the work's pages, so a page that
    continues a book (or a Choniates reign) keeps its context instead of
    falling back. After _bump_books resolves repeated book labels, bases are
    formatted and de-duplicated work-wide: a base alone if unique, else with a
    .para index. Preamble rows (no context yet) key to their page stem. If the
    final loci still collide, the whole work falls back to the per-page
    "<stem>.<n>" scheme so loci stay unique and unguessed. `scheme` is the
    citation scheme achieved, or None for the fallback. In dry_run we read only
    the on-disk cache and never touch the network.
    """
    rule = WORK_RULES.get(f"{w['tlg_id']}.{w['work_id']}")
    st: dict = {}
    pages = []                                       # (stem, [[base, text], ...])
    for url in w["urls"]:
        stem = page_stem(url)
        try:
            if dry_run:
                cached = CACHE / (stem + ".html")
                if not cached.exists():
                    print(f"  ! {stem}: not cached (dry-run skips fetch)",
                          file=sys.stderr)
                    continue
                html = cached.read_text(encoding="utf-8")
            else:
                html = fetch(url, refetch)
            rows = extract_loci(html, stem, rule, st)
        except Exception as e:                       # noqa: BLE001
            print(f"  ! {url}: {e}", file=sys.stderr)
            continue
        pages.append((stem, rows))

    _bump_books(pages)
    stems = [s for s, _ in pages]

    def fallback():
        return [(f"{stem}.{i}", txt)
                for stem, rows in pages
                for i, (_, txt) in enumerate(rows, 1)], None, stems

    if not any(base is not None for _, rows in pages for base, _ in rows):
        return fallback()

    keyed = [(stem if base is None else
              ".".join(str(x) for x in base) if isinstance(base, tuple) else base,
              txt)
             for stem, rows in pages for base, txt in rows]
    counts: dict = {}
    for base, _ in keyed:
        counts[base] = counts.get(base, 0) + 1
    seen: dict = {}
    out = []
    for base, text in keyed:                 # base alone if unique, else .para
        if counts[base] == 1:
            out.append((base, text))
        else:
            seen[base] = seen.get(base, 0) + 1
            out.append((f"{base}.{seen[base]}", text))
    if len({loc for loc, _ in out}) != len(out):     # never emit ambiguous loci
        return fallback()
    return out, (rule["scheme"] if rule else "book/chapter"), stems


def build(only=None, refetch=False, dry_run=False):
    works = load_works()
    if only:
        works = [w for w in works if f"{w['tlg_id']}.{w['work_id']}" == only
                 or w["tlg_id"] == only]
    if not dry_run:
        CORPUS.mkdir(parents=True, exist_ok=True)
    ce = json.loads(CE.read_text(encoding="utf-8")) if CE.exists() and not dry_run \
        else {}

    out_works, n_ok, n_struct = [], 0, 0
    for w in works:
        key = slug_for(f"{w['tlg_id']}.tlg{w['work_id']}")   # slug is the primary id
        combined, scheme, pages = work_loci(w, refetch, dry_run)
        if not combined:
            print(f"  ! {key}: no text extracted", file=sys.stderr)
            continue
        records, n_tok = [], 0
        for locus, text in combined:
            n_tok += sum(1 for _ in _GK_TOK.finditer(text))
            records.append({"urn": key, "edition": EDITION, "locus": locus,
                            "source": SOURCE, "license": LICENSE,
                            # same composition the TEI ingester applies; see the
                            # note in build_corpus_loci.py (issue #4 regression)
                            "text": _compose_breathings(text)[0]})
        n_struct += scheme is not None

        if dry_run:
            tag = scheme or "pagestem.para (fallback)"
            print(f"\n  {key}  [{tag}]  {len(records)} passages  "
                  f"pages={pages}  ({w.get('author', '')[:22]})")
            for r in records[:6]:
                print(f"      {r['locus']:14} {r['text'][:60]}")
            if len(records) > 6:
                print(f"      ... last locus: {records[-1]['locus']}")
            continue

        (CORPUS / f"{key}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
            encoding="utf-8")
        ce[key] = {"edition": EDITION, "license": LICENSE, "source": SOURCE,
                   "n_passages": len(records), "n_tokens": n_tok}
        out_works.append({"key": key, "tlg_id": w["tlg_id"],
                          "work_id": w["work_id"], "title": w["title"],
                          "author": w["author"], "edition": EDITION,
                          "license": LICENSE, "source": SOURCE,
                          "loci": scheme or "pagestem.para",
                          "n_passages": len(records), "n_tokens": n_tok,
                          "pages": pages})
        n_ok += 1
        print(f"  {key:18} {n_tok:>8,} tokens  {len(records):>5} passages  "
              f"[{(scheme or 'stem')[:14]:14}]  ({w['author'][:22]})")

    if dry_run:
        print(f"\nbyzantium_gr dry-run: {n_struct}/{len(works)} works got "
              f"citation loci (no files written)")
        return

    CE.write_text(json.dumps(ce, ensure_ascii=False, indent=0, sort_keys=True),
                  encoding="utf-8")
    WORKS_OUT.write_text(json.dumps(out_works, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"byzantium_gr: {n_ok}/{len(works)} works ingested "
          f"({n_struct} with citation loci), "
          f"{sum(w['n_tokens'] for w in out_works):,} tokens "
          f"-> data/corpus/*.jsonl, data/byzantium_gr_works.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", default=None, help="only this work (tlg4145.001 or tlg4145)")
    ap.add_argument("--refetch", action="store_true", help="ignore the page cache")
    ap.add_argument("--dry-run", action="store_true",
                    help="print proposed loci from the cached pages; write nothing")
    args = ap.parse_args()
    build(args.work, args.refetch, args.dry_run)
