#!/usr/bin/env python3
"""Build data/bekker_concordance.json: a locus -> [Bekker pages] map for the
Aristotle (tlg0086) works whose open TEI in COG carries NO inline Bekker
milestones, so build_corpus_loci.py can fill their empty `bekker` field.

Why this exists
---------------
`is_bekker_page()` in build_corpus_loci.py reads Bekker pagination straight off
`<milestone unit="page" resp="Bekker" n="498b"/>` markers in the served TEI. 18
of the ~40 tlg0086 works carry those markers; the rest (Historia animalium, the
biological and logical works, ...) do not, so an LSJ citation like `HA 498b32`
never resolves. Two OPEN, license-compatible (CC BY-SA) sources DO carry the
Bekker pagination for these works:

  GLAUX      the local treebank clone (~/Documents/glaux): every token has a
             div_bekker_page attribute. Used for De caelo, De generatione
             animalium, De partibus animalium, Physica.
  el.wikisource  the Bekker-1831 Greek text with inline page anchors in three
             forms: {{χ|498b}} template, (704a.) parenthetical, [471a] bracket
             (the last two may carry a trailing line number we truncate to the
             page+column). Used for 13 works incl. Historia animalium; Categoriae
             is a ProofreadPage transclusion whose anchors we read from the
             parsed HTML.
  bekker1831 raw per-page OCR of the Bekker 1831 edition itself (IA scans
             aristotelisopera01/02arisuoft, Qwen3.6-27B, 2026-07-09; see
             greek-ocr runs/editions/bekker1831_*_raw and their _manifest.json).
             One printed page = one Bekker number, columns a/b within it. Used
             for the 8 works neither GLAUX nor el.wikisource covers: the Parva
             Naturalia minus De divinatione/De respiratione, De spiritu, and
             Magna Moralia. Each page yields an "Na" marker from its first body
             tokens (page starts are exact) and an "Nb" marker from the tokens
             at the midpoint of its body stream (the two columns are set at
             equal height, so the token midpoint estimates the column break;
             emitted only on full pages - a short final page gets no b marker).
             Page headers, running titles, and the critical-apparatus footer
             (the '||'-separated variant block) are stripped before tokenizing.

Alignment is by CONTENT, never by chapter number. el.wikisource's chapter/book
divisions do NOT reliably match First1K's book.chapter loci, so we do not trust
them. Instead every Bekker marker carries the run of Greek words that follow it;
we locate that word run in the SERVED COG text (normalized, monotonic best-window
match) to find which served row the page begins in, then attribute each page to
the rows its text overlaps - exactly the model build_corpus_loci already uses for
milestone-derived pages. GLAUX markers are generated the same way (one marker per
div_bekker_page transition, carrying the following GLAUX word forms), so both
routes run through one aligner.

Each work is validated with spot probes (a matched marker's following words must
be found in the row it was attached to). A work below the match/probe thresholds
is FLAGGED and excluded from the concordance rather than force-shipped.

Output (data/bekker_concordance.json):
  {"<slug>": {"<locus>": ["498a","498b"], ...},
   "_meta": {"<slug>": {source, method, markers, matched, rows_anchored,
                        probes, confidence, license, revid|commit}, ...}}

The concordance NEVER overrides milestone-derived pages; build_corpus_loci unions
it in only for works whose milestones produced nothing.

  python scripts/build_bekker_concordance.py [--cache DIR] [--glaux DIR]

Wikisource wikitext is cached under --cache (default: a temp dir; the session
scratchpad is used when present) and re-fetched from the MediaWiki API when
absent, so the build is reproducible. Revision ids are recorded for provenance.
License: GLAUX and el.wikisource are both CC BY-SA (attribution + share-alike),
compatible with COG's First1K/Perseus content.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
OUT = REPO / "data" / "bekker_concordance.json"

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
UA = {"User-Agent": "COG-bekker-concordance/1.0 (corpus-of-open-greek build; "
                    "contact via repo)"}
API = "https://el.wikisource.org/w/api.php"

PROBE_K = 8               # Greek words carried after each marker for locating it
MATCH_THR_FRAC = 0.6      # a window scores a match at >= this fraction of K
STRONG_FRAC = 0.7         # a "strong" (probe-quality) match
MIN_MATCHED_FRAC = 0.60   # keep a work only if this fraction of markers matched
MIN_STRONG_PROBES = 3     # ... and at least this many strong probes pass

SLUG = "aristoteles-et-corpus-aristotelicum"

# el.wikisource works: subpages in reading order. mode "raw" = inline wikitext
# anchors; mode "parse" = ProofreadPage, anchors only in the rendered HTML.
WIKISOURCE = {
    f"{SLUG}.analytica-priora-et-posteriora": {
        "tlg": "tlg001", "mode": "raw",
        "pages": ["Αναλυτικών προτέρων/1", "Αναλυτικών προτέρων/2",
                  "Αναλυτικών υστέρων/1", "Αναλυτικών υστέρων/2"]},
    f"{SLUG}.de-anima": {
        "tlg": "tlg002", "mode": "raw",
        "pages": ["Περί ψυχής/Α", "Περί ψυχής/Β", "Περί ψυχής/Γ"]},
    f"{SLUG}.categoriae": {
        "tlg": "tlg006", "mode": "parse", "pages": ["Κατηγορίαι"]},
    f"{SLUG}.de-divinatione-per-somnum": {
        "tlg": "tlg008", "mode": "raw",
        "pages": ["Περί της καθ΄ ύπνον μαντικής"]},
    f"{SLUG}.de-generatione-et-corruptione": {
        "tlg": "tlg013", "mode": "raw",
        "pages": ["Περί Γενέσεως και Φθοράς/1", "Περί Γενέσεως και Φθοράς/2"]},
    f"{SLUG}.historia-animalium": {
        "tlg": "tlg014", "mode": "raw",
        "pages": [f"Των περί τα ζώα ιστοριών/{i}" for i in range(1, 11)]},
    f"{SLUG}.de-incessu-animalium": {
        "tlg": "tlg015", "mode": "raw", "pages": ["Περί πορείας ζώων"]},
    f"{SLUG}.de-interpretatione": {
        "tlg": "tlg017", "mode": "raw", "pages": ["Περί ερμηνείας"]},
    f"{SLUG}.de-motu-animalium": {
        "tlg": "tlg021", "mode": "raw", "pages": ["Περί ζώων κινήσεως"]},
    f"{SLUG}.meteorologica": {
        "tlg": "tlg026", "mode": "raw",
        "pages": ["Μετεωρολογικά/Α", "Μετεωρολογικά/Β",
                  "Μετεωρολογικά/Γ", "Μετεωρολογικά/Δ"]},
    f"{SLUG}.de-respiratione": {
        "tlg": "tlg037", "mode": "raw", "pages": ["Περί αναπνοής"]},
    f"{SLUG}.sophistici-elenchi": {
        "tlg": "tlg040", "mode": "raw",
        "pages": ["Σοφιστικοί Έλεγχοι/1", "Σοφιστικοί Έλεγχοι/2",
                  "Σοφιστικοί Έλεγχοι/3"]},
    f"{SLUG}.topica": {
        "tlg": "tlg044", "mode": "raw",
        "pages": [f"Τοπικά/{i}" for i in range(1, 9)]},
}

# GLAUX works: local treebank file id (xml/<id>.xml).
GLAUX = {
    f"{SLUG}.de-caelo": "0086-005",
    f"{SLUG}.de-generatione-animalium": "0086-012",
    f"{SLUG}.de-partibus-animalium": "0086-030",
    f"{SLUG}.physica": "0086-031",
}

# Bekker-1831 raw OCR works: run dir under --bekker1831, volume (fixes the
# pdf->printed page map), and the work's Bekker span from the run manifest
# (verified by rendered-page inspection there). span[0] seeds the page active
# at the work's first row, since a work starting mid-page/mid-column has no
# in-work anchor before its first tokens.
OCR_PROBE_K = 10          # longer probes than the anchor routes: OCR garbles
                          # tokens, the fraction thresholds stay the same
BEKKER1831 = {
    f"{SLUG}.de-sensu-et-sensibilibus": {
        "tlg": "tlg041", "dir": "bekker1831_de_sensu_raw", "vol": 1,
        "span": ("436a", "449a")},
    f"{SLUG}.de-memoria-et-reminiscentia": {
        "tlg": "tlg024", "dir": "bekker1831_de_memoria_raw", "vol": 1,
        "span": ("449b", "453b")},
    f"{SLUG}.de-somno-et-vigilia": {
        "tlg": "tlg042", "dir": "bekker1831_de_somno_raw", "vol": 1,
        "span": ("453b", "458a")},
    f"{SLUG}.de-insomniis": {
        "tlg": "tlg016", "dir": "bekker1831_de_insomniis_raw", "vol": 1,
        "span": ("458a", "462b")},
    f"{SLUG}.de-longitudine-et-brevitate-vitae": {
        "tlg": "tlg020", "dir": "bekker1831_de_longitudine_raw", "vol": 1,
        "span": ("464b", "467b")},
    f"{SLUG}.de-juventute-et-senectute-de-vita-et-morte": {
        "tlg": "tlg018", "dir": "bekker1831_de_juventute_raw", "vol": 1,
        "span": ("467b", "470b")},
    f"{SLUG}.de-spiritu": {
        "tlg": "tlg043", "dir": "bekker1831_de_spiritu_raw", "vol": 1,
        "span": ("481a", "486b")},
    f"{SLUG}.magna-moralia": {
        "tlg": "tlg022", "dir": "bekker1831_magna_moralia_raw", "vol": 2,
        "span": ("1181a", "1213b")},
}
BEKKER1831_IDENT = {1: "aristotelisopera01arisuoft", 2: "aristotelisopera02arisuoft"}
# pdf = printed + 14 (vol 1, uniform in the 436-500 range; the +18 anomaly is
# confined to printed 149-156) / printed - 782 (vol 2, uniform). From the IA
# scandata.xml pageNumber assertions + rendered-page verification (run report).
BEKKER1831_PRINTED = {1: (lambda pdf: pdf - 14), 2: (lambda pdf: pdf + 782)}


def norm(t: str) -> str:
    """Bare-letter, de-accented, lowercased Greek form of a token."""
    d = unicodedata.normalize("NFD", t.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return "".join(c for c in d if _GK.match(c))


# ---------------------------------------------------------------------------
# Fetch + cache
# ---------------------------------------------------------------------------
def _api(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8"))


def fetch_raw(title: str):
    """(wikitext, revid, timestamp) for a page via the MediaWiki API."""
    d = _api({"action": "query", "prop": "revisions",
              "rvprop": "ids|content|timestamp", "rvslots": "main",
              "format": "json", "formatversion": "2", "redirects": "1",
              "titles": title})
    pg = d["query"]["pages"][0]
    if pg.get("missing"):
        return None, None, None
    rev = pg["revisions"][0]
    return rev["slots"]["main"]["content"], rev["revid"], rev["timestamp"]


def fetch_parsed(title: str):
    """(rendered HTML, revid) for a page - expands ProofreadPage transclusions."""
    d = _api({"action": "parse", "page": title, "prop": "text",
              "format": "json", "formatversion": "2", "disablelimitreport": "1"})
    return d["parse"]["text"], d["parse"].get("revid")


def cached(cache: Path, title: str, mode: str):
    """Return (content, revid, timestamp). Read the cache; on a miss fetch and
    write cache + a sidecar .meta.json with the revid."""
    safe = title.replace("/", "__").replace(" ", "_")
    ext = "html" if mode == "parse" else "wiki"
    fp = cache / f"{safe}.{ext}"
    mp = cache / f"{safe}.{ext}.meta.json"
    if fp.exists() and mp.exists():
        meta = json.loads(mp.read_text(encoding="utf-8"))
        return fp.read_text(encoding="utf-8"), meta.get("revid"), meta.get("timestamp")
    if mode == "parse":
        content, revid = fetch_parsed(title)
        ts = None
    else:
        content, revid, ts = fetch_raw(title)
    if content is None:
        return None, None, None
    cache.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    mp.write_text(json.dumps({"title": title, "revid": revid, "timestamp": ts},
                             ensure_ascii=False), encoding="utf-8")
    time.sleep(0.25)
    return content, revid, ts


# ---------------------------------------------------------------------------
# Marker extraction
# ---------------------------------------------------------------------------
# Three inline anchor forms, each capturing the page+column (\d+[ab]); a trailing
# line number (.20 / 3 / 18) is discarded so the field stays page-level.
_ANCHOR = re.compile(
    r"\{\{\s*χ\s*\|\s*(?P<t>\d{1,4}[ab])[^}]*\}\}"       # {{χ|498b}} / {{χ|338a.20}}
    r"|\(\s*(?P<p>\d{1,4}[ab])\.?\d*\.?\s*\)"            # (704a.) / (498a)
    r"|\[\s*(?P<b>\d{1,4}[ab])\d*\s*\]")                 # [471a] / [100a18]

_SENT = "\x00%s\x00"
_TOKENIZER = re.compile(r"\x00(\d{1,4}[ab])\x00|([Ͱ-Ͽἀ-῿]+)")


def _strip_markup(text: str) -> str:
    """Drop TEI/wiki decoration whose Greek text (headers, links, refs) would
    pollute the token stream. Anchors are already sentinels by now."""
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)                 # any HTML/self-closing tag
    for _ in range(6):                                   # nested templates
        new = re.sub(r"\{\{[^{}]*\}\}", " ", text)
        if new == text:
            break
        text = new
    text = re.sub(r"\[\[[^\]]*\]\]", " ", text)          # wiki links (drop entirely)
    text = re.sub(r"^=+.*?=+\s*$", " ", text, flags=re.M)  # == headers ==
    return text


def markers_from_text(text: str) -> list[tuple[str, list[str]]]:
    """Parse inline-anchor wikitext/HTML-text into (page, following_words) markers
    in document order. following_words = the next PROBE_K normalized Greek tokens
    after the anchor (used to locate the page start in the COG text)."""
    def sent(m):
        return " " + (_SENT % (m.group("t") or m.group("p") or m.group("b"))) + " "
    text = _ANCHOR.sub(sent, text)
    text = _strip_markup(text)

    stream = []                        # ("P", page) | ("W", norm_tok)
    for m in _TOKENIZER.finditer(text):
        if m.group(1) is not None:
            stream.append(("P", m.group(1)))
        else:
            w = norm(m.group(2))
            if w:
                stream.append(("W", w))
    markers = []
    for i, (kind, val) in enumerate(stream):
        if kind != "P":
            continue
        probe = [v for k, v in stream[i + 1:] if k == "W"][:PROBE_K]
        markers.append((val, probe))
    return markers


_VALID_PAGE = re.compile(r"\d{1,4}[ab]")


def markers_from_glaux(xml_path: Path):
    """(markers, invalid_pages): one marker per div_bekker_page transition,
    carrying the following word forms - the GLAUX analogue of an inline anchor.
    Bekker columns are only a/b; GLAUX carries a few stray ids (physica has
    226c and 235c, with 235a absent), which we EXCLUDE rather than emit: the
    tokens under them attach to the neighboring valid page, and the exclusion
    is reported in _meta as invalid_pages."""
    words = []                         # (norm_form, bekker_page)
    invalid: dict[str, int] = {}
    for m in re.finditer(r'<word\b[^>]*>', xml_path.read_text(encoding="utf-8")):
        tag = m.group(0)
        fm = re.search(r'\bform="([^"]*)"', tag)
        pm = re.search(r'\bdiv_bekker_page="([^"]*)"', tag)
        if not fm or not pm:
            continue
        page = pm.group(1)
        if not _VALID_PAGE.fullmatch(page):
            invalid[page] = invalid.get(page, 0) + 1
            continue
        w = norm(fm.group(1))
        words.append((w, page))
    markers = []
    cur = None
    for i, (w, page) in enumerate(words):
        if page != cur:
            cur = page
            probe = [ww for ww, _p in words[i:] if ww][:PROBE_K]
            markers.append((page, probe))
    return markers, invalid


_APPARATUS_START = re.compile(r"^\s*(Codices\b|Tit\.)|^\s*\d+\.\s[^|]*\]")


def bekker1831_page_tokens(md_text: str) -> list[str]:
    """Normalized Greek body tokens of one OCR'd Bekker page, in reading order
    (column a then column b - the OCR transcribes the columns in sequence).
    Markdown headers (# running titles / section titles, incl. those of a next
    work beginning mid-page) and tags are dropped; the critical-apparatus
    footer ends the body: its first line (a '||'-separated variant block, or a
    'Codices'/'Tit.'/numbered-lemma line) and everything after it is cut."""
    toks: list[str] = []
    for line in md_text.splitlines():
        if "||" in line or _APPARATUS_START.match(line):
            break
        s = re.sub(r"<[^>]+>", " ", line)
        if s.lstrip().startswith("#"):
            continue
        for t in s.split():
            w = norm(t)
            if w:
                toks.append(w)
    return toks


def markers_from_bekker1831(run_dir: Path, vol: int, span: tuple[str, str]):
    """(markers, page_stats) for one work's raw page dir. Per page: an 'Na'
    marker from the first OCR_PROBE_K body tokens (page starts are exact) and,
    on full pages only, an 'Nb' marker from the tokens at the body midpoint
    (Bekker's columns are set at equal height, so the token midpoint estimates
    the a/b column break; a short page - the span's final page when the print
    stops early - gets no b marker rather than a misplaced one). Each run dir
    deliberately includes the work-boundary pages, so columns OUTSIDE the
    work's manifest span belong to the neighboring work by construction: those
    markers are not emitted (reported as foreign_columns_skipped) rather than
    counted as alignment failures. An in-span column whose text still starts
    inside the neighbor (a work beginning mid-column) simply fails to match
    and is dropped by the aligner; `initial` covers its attribution."""
    per_page = []
    for md in sorted(run_dir.glob("*.md")):
        m = re.search(r"_(\d{4})$", md.stem)
        if not m:
            continue
        per_page.append((int(m.group(1)), bekker1831_page_tokens(
            md.read_text(encoding="utf-8", errors="ignore"))))
    lens = sorted(len(t) for _p, t in per_page if t)
    median = lens[len(lens) // 2] if lens else 0
    lo, hi = _page_val(span[0]), _page_val(span[1])
    markers, b_skipped, foreign = [], [], []
    for pdf, toks in per_page:
        printed = BEKKER1831_PRINTED[vol](pdf)
        for col, probe_ok, probe in (
                ("a", len(toks) >= OCR_PROBE_K, toks[:OCR_PROBE_K]),
                ("b", len(toks) >= max(2 * OCR_PROBE_K + 10, round(0.8 * median)),
                 toks[len(toks) // 2:len(toks) // 2 + OCR_PROBE_K])):
            page = f"{printed}{col}"
            if not probe_ok:
                if col == "b":
                    b_skipped.append(printed)
                continue
            if not lo <= _page_val(page) <= hi:
                foreign.append(page)
                continue
            markers.append((page, probe))
    stats = {"pages": len(per_page), "median_page_tokens": median,
             "b_markers_skipped_short_pages": b_skipped,
             "foreign_columns_skipped": foreign}
    return markers, stats


# ---------------------------------------------------------------------------
# COG side + alignment
# ---------------------------------------------------------------------------
def load_cog_rows(slug: str):
    """Served rows in reading order -> (loci, tokens, row_start, row_of_tok).
    tokens is the flat normalized token array; row_start[r] is r's first token
    index; row_of_tok[i] is the row owning token i."""
    fp = CORPUS / f"{slug}.jsonl"
    loci, tokens, row_start, row_of = [], [], [], []
    with fp.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            loci.append(r["locus"])
            row_start.append(len(tokens))
            ridx = len(loci) - 1
            for t in r["text"].split():
                w = norm(t)
                if w:
                    tokens.append(w)
                    row_of.append(ridx)
    return loci, tokens, row_start, row_of


def _index(tokens: list[str]) -> dict:
    idx: dict = {}
    for i, t in enumerate(tokens):
        idx.setdefault(t, []).append(i)
    return idx


def _page_val(page: str) -> int:
    """Orderable value of a Bekker page: 498a -> 996, 498b -> 997, so a page
    sequence is a monotone integer sequence through a work."""
    m = re.match(r"(\d+)([ab])", page)
    return int(m.group(1)) * 2 + (m.group(2) == "b")


def _lis_keep(matched):
    """Given (index, pos, score, pval) for the above-threshold matches in marker
    order, return the subset of indices to KEEP: the longest run that is
    non-decreasing in BOTH text position AND page value (ties broken by total
    score). Two artifacts are dropped this way:
      - a false content match that jumps far ahead (physica 201b hit a book-8
        coincidence): off the position order.
      - a mislabeled page whose text sits at the right place but whose printed
        number is a transcription typo (de-anima's {{χ|4310a10}} for 431a):
        on the position order but a spike in page value.
    Neither can reorder the concordance nor (as the old greedy floor did) poison
    later markers. Pages are printed in ascending order through a work, so the
    kept sequence must ascend in both axes."""
    n = len(matched)
    if n == 0:
        return set()
    best_len = [1] * n
    best_sc = [matched[i][2] for i in range(n)]
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if matched[j][1] <= matched[i][1] and matched[j][3] <= matched[i][3]:
                cand_len = best_len[j] + 1
                cand_sc = best_sc[j] + matched[i][2]
                if (cand_len > best_len[i]
                        or (cand_len == best_len[i] and cand_sc > best_sc[i])):
                    best_len[i] = cand_len
                    best_sc[i] = cand_sc
                    prev[i] = j
    end = max(range(n), key=lambda i: (best_len[i], best_sc[i]))
    keep = set()
    while end != -1:
        keep.add(matched[end][0])
        end = prev[end]
    return keep


def align(markers, tokens, idx):
    """Locate each marker's page start in `tokens`. Returns a list parallel to
    markers of (page, pos|None, score). For each marker we take the GLOBAL best
    scoring window (seeded from the first probe tokens so we score only a handful
    of candidate positions, not all N); markers scoring below the threshold are
    unmatched. A longest non-decreasing-by-position pass then drops any matched
    marker that is out of document order (a coincidental match elsewhere in the
    text), which the served edition's local divergences from the anchor source
    can produce."""
    N = len(tokens)
    prelim = []                      # (page, pos|None, score)
    for page, probe in markers:
        if not probe:
            prelim.append((page, None, 0))
            continue
        K = len(probe)
        cands = set()
        for j in range(min(4, K)):
            for p in idx.get(probe[j], ()):
                if p - j >= 0:
                    cands.add(p - j)
        best_s, best_p = -1, None
        pc: dict = {}
        for t in probe:
            pc[t] = pc.get(t, 0) + 1
        for p in cands:
            # bag-of-tokens score over a K+3 window: an OCR'd probe token that
            # the served text spells as one-off (hyphen split, particle merge)
            # shifts its neighbors, which zeroed the old strictly-positional
            # score; counting probe tokens anywhere in the slack window keeps
            # the match while the LIS pass still enforces document order.
            win: dict = {}
            for t in tokens[p:p + K + 3]:
                win[t] = win.get(t, 0) + 1
            s = sum(min(c, win.get(t, 0)) for t, c in pc.items())
            if s > best_s or (s == best_s and (best_p is None or p < best_p)):
                best_s, best_p = s, p
        thr = max(3, round(MATCH_THR_FRAC * K))
        if best_p is not None and best_s >= thr:
            prelim.append((page, best_p, best_s))
        else:
            prelim.append((page, None, best_s))

    matched = [(i, pos, s, _page_val(pg))
               for i, (pg, pos, s) in enumerate(prelim) if pos is not None]
    keep = _lis_keep(matched)
    return [(pg, (pos if i in keep else None), s)
            for i, (pg, pos, s) in enumerate(prelim)]


def attribute(anchors, loci, row_start, tokens, initial=None):
    """Turn located page starts into locus -> [pages]. A row gets the page in
    effect at its first token (its text continues from the prior page) plus every
    page that starts within it, in first-appearance order - mirroring
    build_corpus_loci's own per-row Bekker model. `initial` (the work's span
    start from the run manifest) is the page active from token 0, for works
    that begin mid-page/mid-column and so have no in-work anchor before their
    first tokens (bekker1831 route only)."""
    matched = sorted((pos, page) for page, pos, _s in anchors if pos is not None)
    if initial is not None:
        matched = [(-1, initial)] + matched
    N = len(tokens)
    row_end = row_start[1:] + [N]
    concord: dict[str, list[str]] = {}
    for r, locus in enumerate(loci):
        a, b = row_start[r], row_end[r]
        pages: list[str] = []
        # page active at row start (last anchor at or before a)
        active = None
        for pos, page in matched:
            if pos <= a:
                active = page
            else:
                break
        if active is not None:
            pages.append(active)
        for pos, page in matched:
            if a <= pos < b and page not in pages:
                pages.append(page)
        # de-dup preserving order (active may repeat a starts-in-row page)
        seen, out = set(), []
        for p in pages:
            if p not in seen:
                seen.add(p)
                out.append(p)
        if out:
            concord[locus] = out
    return concord


def probes(anchors, markers, loci, row_start, tokens, row_of):
    """Pick up to 5 matched anchors spread across the work and report, per probe,
    the page, the locus it landed in, whether the match is strong, and the first
    few following words - the audit that a page really attaches where claimed."""
    N = len(tokens)
    matched_idx = [i for i, (_p, pos, _s) in enumerate(anchors) if pos is not None]
    if not matched_idx:
        return [], 0
    picks = sorted({matched_idx[round(f * (len(matched_idx) - 1))]
                    for f in (0.05, 0.28, 0.5, 0.72, 0.95)})
    out = []
    strong = 0
    for i in picks:
        page, pos, score = anchors[i]
        K = len(markers[i][1])
        ok = score >= round(STRONG_FRAC * K)
        strong += ok
        out.append({"page": page, "locus": loci[row_of[pos]],
                    "score": f"{score}/{K}", "strong": ok,
                    "words": " ".join(markers[i][1][:4])})
    return out, strong


def strong_count(anchors, markers) -> int:
    return sum(1 for (page, pos, s), (_pg, probe) in zip(anchors, markers)
               if pos is not None and s >= round(STRONG_FRAC * len(probe)))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def build_work(slug, markers, tokens, idx, loci, row_start, row_of, initial=None):
    anchors = align(markers, tokens, idx)
    n_matched = sum(1 for _p, pos, _s in anchors if pos is not None)
    concord = attribute(anchors, loci, row_start, tokens, initial=initial)
    prb, _ = probes(anchors, markers, loci, row_start, tokens, row_of)
    n_strong = strong_count(anchors, markers)
    matched_frac = n_matched / len(markers) if markers else 0.0
    strong_probes = sum(1 for p in prb if p["strong"])
    keep = matched_frac >= MIN_MATCHED_FRAC and strong_probes >= MIN_STRONG_PROBES
    stats = {
        "markers": len(markers), "matched": n_matched,
        "matched_frac": round(matched_frac, 3),
        "strong_matches": n_strong,
        "rows_anchored": len(concord),
        "rows_total": len(loci),
        "probes": prb,
        "confidence": round(matched_frac, 3),
        "kept": keep,
    }
    return concord, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    default_cache = os.environ.get("BEKKER_CACHE")
    if not default_cache:
        default_cache = str(Path(tempfile.gettempdir()) / "cog_bekker_ws_cache")
    ap.add_argument("--cache", default=default_cache,
                    help="wikisource wikitext cache dir (fetched if absent)")
    ap.add_argument("--glaux", default=str(Path.home() / "Documents" / "glaux"),
                    help="local GLAUX clone (xml/<id>.xml)")
    ap.add_argument("--bekker1831",
                    default=str(Path.home() / "Documents" / "greek-ocr" / "runs"
                                / "editions"),
                    help="dir holding the bekker1831_*_raw OCR run dirs")
    args = ap.parse_args()
    cache = Path(args.cache)
    glaux = Path(args.glaux)
    bek_root = Path(args.bekker1831)

    concordance: dict = {}
    meta: dict = {}

    # GLAUX route -------------------------------------------------------------
    glaux_commit = None
    head = glaux / ".git" / "HEAD"
    try:
        ref = head.read_text().strip()
        if ref.startswith("ref:"):
            glaux_commit = (glaux / ".git" / ref.split(" ", 1)[1]).read_text().strip()
        else:
            glaux_commit = ref
    except OSError:
        pass
    for slug, gid in GLAUX.items():
        xmlp = glaux / "xml" / f"{gid}.xml"
        if not xmlp.exists():
            print(f"  SKIP {slug}: GLAUX {gid}.xml not found", file=sys.stderr)
            meta[slug] = {"source": f"glaux:{gid}", "kept": False,
                          "reason": "GLAUX file missing"}
            continue
        markers, invalid = markers_from_glaux(xmlp)
        loci, tokens, row_start, row_of = load_cog_rows(slug)
        idx = _index(tokens)
        concord, stats = build_work(slug, markers, tokens, idx, loci,
                                    row_start, row_of)
        meta[slug] = {"source": f"glaux:{gid}", "method": "glaux-content-align",
                      "glaux_commit": glaux_commit,
                      "license": "CC BY-SA (GLAUX; source el.wikisource CC-BY-SA)",
                      **({"invalid_pages": invalid} if invalid else {}),
                      **stats}
        if stats["kept"]:
            concordance[slug] = concord
            print(f"  GLAUX  {slug}: {stats['matched']}/{stats['markers']} markers, "
                  f"{stats['rows_anchored']} rows anchored", file=sys.stderr)
        else:
            print(f"  FLAG   {slug}: excluded ({stats['matched']}/{stats['markers']} "
                  f"matched)", file=sys.stderr)

    # el.wikisource route -----------------------------------------------------
    for slug, cfg in WIKISOURCE.items():
        text_parts = []
        revids = []
        missing = False
        for title in cfg["pages"]:
            content, revid, _ts = cached(cache, title, cfg["mode"])
            if content is None:
                missing = True
                print(f"  MISSING page {title} for {slug}", file=sys.stderr)
                continue
            text_parts.append(content)
            revids.append({"title": title, "revid": revid})
        markers = []
        for content in text_parts:
            markers.extend(markers_from_text(content))
        loci, tokens, row_start, row_of = load_cog_rows(slug)
        idx = _index(tokens)
        concord, stats = build_work(slug, markers, tokens, idx, loci,
                                    row_start, row_of)
        meta[slug] = {"source": "el.wikisource", "mode": cfg["mode"],
                      "revids": revids,
                      "method": "el.wikisource-content-align",
                      "license": "CC BY-SA 4.0 (el.wikisource)",
                      "missing_pages": missing, **stats}
        if stats["kept"] and not missing:
            concordance[slug] = concord
            print(f"  WS     {slug}: {stats['matched']}/{stats['markers']} markers, "
                  f"{stats['rows_anchored']} rows anchored", file=sys.stderr)
        else:
            print(f"  FLAG   {slug}: excluded ({stats['matched']}/{stats['markers']} "
                  f"matched, missing={missing})", file=sys.stderr)

    # Bekker-1831 raw OCR route --------------------------------------------
    for slug, cfg in BEKKER1831.items():
        d = bek_root / cfg["dir"]
        if not d.exists():
            print(f"  SKIP {slug}: {d} not found", file=sys.stderr)
            meta[slug] = {"source": "bekker1831-ocr", "kept": False,
                          "reason": f"run dir {cfg['dir']} missing"}
            continue
        markers, pstats = markers_from_bekker1831(d, cfg["vol"], cfg["span"])
        loci, tokens, row_start, row_of = load_cog_rows(slug)
        idx = _index(tokens)
        concord, stats = build_work(slug, markers, tokens, idx, loci,
                                    row_start, row_of, initial=cfg["span"][0])
        meta[slug] = {"source": "bekker1831-ocr",
                      "method": "bekker1831-content-align",
                      "ident": BEKKER1831_IDENT[cfg["vol"]],
                      "run_dir": cfg["dir"], "tlg": f"tlg0086.{cfg['tlg']}",
                      "span": f"{cfg['span'][0]}-{cfg['span'][1]}",
                      "initial_page": cfg["span"][0],
                      "page_map": ("pdf = printed + 14 (vol 1)" if cfg["vol"] == 1
                                   else "pdf = printed - 782 (vol 2)"),
                      "b_marker_note": "column-b anchors are token-midpoint "
                                       "estimates on full pages (equal-height "
                                       "columns); short pages get none",
                      "license": "PD (Bekker 1831; Qwen3.6-27B OCR, 2026-07-09)",
                      **pstats, **stats}
        if stats["kept"]:
            concordance[slug] = concord
            print(f"  B1831  {slug}: {stats['matched']}/{stats['markers']} markers, "
                  f"{stats['rows_anchored']} rows anchored", file=sys.stderr)
        else:
            print(f"  FLAG   {slug}: excluded ({stats['matched']}/{stats['markers']} "
                  f"matched)", file=sys.stderr)

    # Divisiones Aristoteleae: verified NOT-A-GAP (2026-07-09). No Bekker
    # pagination exists for it anywhere: the work is not in Bekker's 1831
    # vols 1-2 (the Greek text ends with Poetica at 1462); it survives via
    # Diogenes Laertius V and cod. Marcianus (first full edition Mutschmann
    # 1906). Recorded so the empty bekker field is known-complete.
    meta[f"{SLUG}.divisiones-aristoteleae"] = {
        "source": "bekker1831", "kept": False, "not_a_gap": True,
        "reason": "no Bekker pagination exists for this work: absent from "
                  "Bekker 1831 vols 1-2 (Greek text ends with Poetica at "
                  "1462); transmitted via Diogenes Laertius V and cod. "
                  "Marcianus, first full edition Mutschmann 1906. Verified "
                  "2026-07-09; the missing bekker field is not a gap."}

    concordance["_meta"] = {
        "description": "locus -> [Bekker page/column] for tlg0086 works whose "
                       "served TEI carries no inline Bekker milestones; consumed "
                       "by build_corpus_loci.py (unioned in, never overriding "
                       "milestone-derived pages).",
        "generator": "scripts/build_bekker_concordance.py",
        "granularity": "page/column (498a/498b); marker line numbers truncated",
        "sources": {
            "glaux": "GLAUX treebank (CC BY-SA), div_bekker_page attributes",
            "el.wikisource": "el.wikisource.org Bekker-1831 text (CC BY-SA 4.0), "
                             "inline {{χ|..}} / (..) / [..] anchors",
            "bekker1831": "per-page Qwen3.6-27B OCR of the Bekker 1831 edition "
                          "itself (PD; IA aristotelisopera01/02arisuoft, "
                          "2026-07-09): page starts + column-midpoint anchors, "
                          "content-aligned like the other routes",
        },
        "license": "CC BY-SA 4.0 (attribution + share-alike); bekker1831-route "
                   "pages derive from PD scans",
        "works": meta,
    }
    OUT.write_text(json.dumps(concordance, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    kept = [k for k in concordance if k != "_meta"]
    print(f"\nwrote {OUT.relative_to(REPO)}: {len(kept)} works anchored",
          file=sys.stderr)


if __name__ == "__main__":
    main()
