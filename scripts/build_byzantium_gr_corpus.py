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
chapters). Any page/work with no detectable structure - or whose detected loci
would collide across pages (a source numbering slip) - falls back to the original
"<pagestem>.<paragraph-index>" scheme, so we never emit a guessed locus. Merges
into corpus_editions.json like the other ingesters.

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
_KER = ("ʹʹ’'´΄′`‘‵׳")
_GK_LETTER = re.compile(r"[Ά-ϡ]")     # basic + accented + archaic letters
_NUM = {"α": 1, "β": 2, "γ": 3, "δ": 4, "ε": 5, "ϛ": 6, "ϝ": 6, "ζ": 7,
        "η": 8, "θ": 9, "ι": 10, "κ": 20, "λ": 30, "μ": 40, "ν": 50,
        "ξ": 60, "ο": 70, "π": 80, "ϟ": 90, "ϙ": 90, "ρ": 100, "σ": 200,
        "τ": 300, "υ": 400, "φ": 500, "χ": 600, "ψ": 700, "ω": 800, "ϡ": 900}

# a numeral token: a Greek letter then more letters / keraia / space / dot
_NUMERAL = r"[Ά-ϡ][Ά-ϡ" + _KER + r"\s.]{0,9}"
# a book opener: ΛΟΓΟΣ / ΒΙΒΛΙΟΝ / ΒΙΒΛΙΟ / ΤΟΜΟΣ / ΙΣΤΟΡΙΑ followed by a numeral
_BOOK_KW = re.compile(
    r"(?:ΛΟΓΟΣ|ΒΙΒΛΙΟΝ|ΒΙΒΛΙΟ|ΤΟΜΟΣ|ΙΣΤΟΡΙΑ)\s+(" + _NUMERAL + r")")


def greek_numeral(s: str):
    """Decode a Greek-letter numeral (αʹ=1, ιβʹ=12, ΙΣτʹ=16) to int, else None.
    Requires a keraia/apostrophe mark, so ordinary words never parse as numbers."""
    s = unicodedata.normalize("NFC", s)
    if not any(c in _KER for c in s):
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
    """Book number from a heading like 'ΛΟΓΟΣ Α'.' / 'ΒΙΒΛΙΟΝ Βʹ', else None."""
    m = _BOOK_KW.search(unicodedata.normalize("NFC", text))
    return greek_numeral(m.group(1)) if m else None


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


def extract_loci(html: str, stem: str):
    """Return (loci, structured) for a byzantium.gr page, nav removed.

    `loci` is a list of (locus, text). We walk the cleaned HTML in document order
    keeping a running book/chapter context: <h*>/<b> headers matching a book
    opener set the book (and reset the chapter); short <u> Greek-letter numerals
    set the chapter (accepting only a forward step inside the current book, so a
    stray underlined numeral in the prose can't restart the count). A kept line
    is keyed "<book>.<chapter>" when both are known, "<book>" with book only;
    lines with no book context (and pages with no markers at all) fall back to
    "<stem>.<n>". `structured` is True iff at least one line got a book locus.
    The same polytonic-length filter as before keeps only running prose.
    """
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
    book = chapter = None
    buf: list[str] = []

    def flush():
        line = unicodedata.normalize("NFC", " ".join("".join(buf).split()))
        buf.clear()
        if not line:
            return
        gk = sum(1 for c in line if _GK.match(c))
        # keep running prose: enough Greek AND polytonic (drops monotonic modern-
        # Greek editorial notes and the short all-caps headers / menu remnants)
        if gk >= MIN_GREEK and _POLY.search(line):
            # a confident locus needs a book context; a bare chapter (no book) is
            # ambiguous in multi-book works whose chapters restart, so fall back
            if book is not None and chapter is not None:
                base = f"{book}.{chapter}"
            elif book is not None:
                base = f"{book}"
            else:
                base = None
            rows.append([base, line])

    for p in parts:
        if isinstance(p, tuple):
            flush()
            if p[0] == "BK":
                bn = book_num(p[1])
                if bn is not None:
                    book, chapter = bn, None
            else:
                cn = greek_numeral(p[1])
                if cn is not None and (chapter is None or cn > chapter):
                    chapter = cn
        elif p == "\n":
            flush()
        else:
            buf.append(p)
    flush()

    structured = any(r[0] is not None for r in rows)
    if not structured:
        return [(f"{stem}.{i}", t) for i, (_, t) in enumerate(rows, 1)], False

    for r in rows:                           # preamble lines -> page fallback
        if r[0] is None:
            r[0] = stem
    counts: dict = {}
    for base, _ in rows:
        counts[base] = counts.get(base, 0) + 1
    seen: dict = {}
    out = []
    for base, text in rows:                  # base alone if unique, else .para
        if counts[base] == 1:
            out.append((base, text))
        else:
            seen[base] = seen.get(base, 0) + 1
            out.append((f"{base}.{seen[base]}", text))
    return out, True


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
    """Collect (loci, structured, pages) for a work, combining all its pages.

    Loci from extract_loci are book/chapter based where detectable. If any page is
    structured but the combined loci collide across pages (a source numbering slip
    such as kantakouzen labelling two books 'ΙΣΤΟΡΙΑ Γ'), the whole work falls back
    to the per-page "<stem>.<n>" scheme so loci stay unique and unguessed.
    In dry_run we read only the on-disk cache and never touch the network.
    """
    pages = []                                       # (stem, [(locus, text)], structured)
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
            loci, structured = extract_loci(html, stem)
        except Exception as e:                       # noqa: BLE001
            print(f"  ! {url}: {e}", file=sys.stderr)
            continue
        pages.append((stem, loci, structured))

    structured = any(s for _, _, s in pages)
    combined = [(loc, txt) for _, loci, _ in pages for (loc, txt) in loci]
    if structured:
        locs = [loc for loc, _ in combined]
        if len(locs) != len(set(locs)):              # cross-page collision
            combined = [(f"{stem}.{i}", txt)
                        for stem, loci, _ in pages
                        for i, (_, txt) in enumerate(loci, 1)]
            structured = False
    return combined, structured, [s for s, _, _ in pages]


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
        combined, structured, pages = work_loci(w, refetch, dry_run)
        if not combined:
            print(f"  ! {key}: no text extracted", file=sys.stderr)
            continue
        records, n_tok = [], 0
        for locus, text in combined:
            n_tok += sum(1 for _ in _GK_TOK.finditer(text))
            records.append({"urn": key, "edition": EDITION, "locus": locus,
                            "source": SOURCE, "license": LICENSE, "text": text})
        n_struct += structured

        if dry_run:
            tag = "book/chapter" if structured else "pagestem.para (fallback)"
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
                          "loci": "book/chapter" if structured else "pagestem.para",
                          "n_passages": len(records), "n_tokens": n_tok,
                          "pages": pages})
        n_ok += 1
        print(f"  {key:18} {n_tok:>8,} tokens  {len(records):>5} passages  "
              f"{'[bk/ch]' if structured else '[stem ]'}  ({w['author'][:22]})")

    if dry_run:
        print(f"\nbyzantium_gr dry-run: {n_struct}/{len(works)} works got "
              f"book/chapter loci (no files written)")
        return

    CE.write_text(json.dumps(ce, ensure_ascii=False, indent=0, sort_keys=True),
                  encoding="utf-8")
    WORKS_OUT.write_text(json.dumps(out_works, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"byzantium_gr: {n_ok}/{len(works)} works ingested "
          f"({n_struct} with book/chapter loci), "
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
