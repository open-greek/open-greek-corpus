#!/usr/bin/env python3
"""Build a per-work, LOCUS-KEYED public Ancient Greek corpus from the open TEI
corpora (First1KGreek CC BY-SA, Perseus canonical-greekLit CC).

This is the locus-preserving superset of build_public_corpus.py. That script
flattens every edition to a form-frequency lexicon and a work-level coverage
table, throwing away two things we now want back: the citation structure (which
book/line/section each word sits in) and which edition won the per-work dedup.

For every Greek edition we walk the TEI <body>, drop the same non-text material
(teiHeader, editorial <note>s, apparatus <rdg> variants - keeping the chosen
reading), and emit one JSON record per citable passage, keyed to the canonical
citation so it joins the TLG inventory on tlgAUTHOR.tlgWORK:locus:

  {"urn": "tlg0012.tlg001", "edition": "perseus-grc2", "locus": "1.1",
   "source": "perseus", "license": "CC-BY-SA-4.0",
   "text": "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"}

The locus is the dotted citation ref. We derive it from the div@type=textpart /
<l> hierarchy: a verse line (<l n=...>) is a leaf keyed by its ancestor textpart
@n values plus its own @n (Iliad -> book.line "1.1"); a prose textpart div with
no finer textpart/line below it is a leaf keyed by its ancestor chain (Republic
-> book.section "1.327", a chapter work -> "4"). <l> without @n (and any other
non-numbered structure) is treated as ordinary running text of its enclosing
citable div, never emitted as a garbage row-index locus. Works whose leaves have
no derivable @n are reported, not silently emitted.

Dedup per tlgAuthor.tlgWork: the largest edition (most Greek tokens) is the
primary; any OTHER edition whose books are disjoint from it AND whose text barely
overlaps (word 5-gram shingles) is merged in, so a work split across part-editions
by book range (Diodorus, the Anthologia Graeca) is unioned rather than truncated,
while an alternate edition of the same text is dropped (never double-counted). We
record the primary's CTS version, and the full set in `merged_editions` when more
than one edition contributes.

Outputs (under data/):
  corpus/<tlgAuthor>.<tlgWork>.jsonl   one record per citable passage
  corpus_editions.json                 work -> {edition, source, license,
                                               n_passages, n_tokens}
  public_lexicon.tsv                   form<TAB>count rollup (same as
                                               build_public_corpus, recomputed
                                               from the winning editions)

  python build_corpus_loci.py [--only tlg0012] [--only tlg0012.tlg001]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import lxml.etree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosswalk import slug_for  # noqa: E402

# Reuse build_public_corpus's license detection, Greek-token regex, drop set and
# whole-body text extraction so dedup and the lexicon rollup stay byte-identical.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import (  # noqa: E402
    DROP,
    TEI_NS,
    _GK,
    _WORK_RE,
    body_text,
    detect_license,
    is_acceptable,
    is_dropped,
)

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources"
DATA = REPO / "data"
CORPUS = DATA / "corpus"

L_TAG = f"{{{TEI_NS}}}l"
DIV_TAG = f"{{{TEI_NS}}}div"
# Unnumbered textpart subtypes served as citable rows (locus = the subtype
# name). Only transmitted front matter; see the curation note in iter_passages.
SERVED_UNNUMBERED_SUBTYPES = {"hypothesis"}
MILESTONE_TAG = f"{{{TEI_NS}}}milestone"
LB_TAG = f"{{{TEI_NS}}}lb"
PB_TAG = f"{{{TEI_NS}}}pb"

# A citable numbered div whose passage exceeds this many Greek tokens is served
# split at edition-page boundaries when its own content carries at least two
# distinct numbered <pb n=.../> page breaks (the page-split in iter_passages).
# The CAG Aristotle commentaries, the NT catenae, the Chronicon Paschale etc.
# arrive as whole-book divs (Simplicius In Physica: eight divs, 425k tokens)
# that scholarship cites by edition page, and the TEI carries that pagination
# as numbered <pb> milestones; serving one row per page makes the loci citable.
OVERSIZE_TOKENS = 2000

# Sentinel marking a line boundary inside a passage's part list (see
# passage_segments): flushed into a separate text_lines segment.
_LINE_BREAK = object()


def is_bekker_page(el) -> bool:
    """True for a Bekker canonical-page milestone, e.g.
    <milestone unit="page" resp="Bekker" n="498b"/>. These sit inline in the
    running text of the Aristotle editions (First1K + Perseus) at the point the
    Bekker page begins; the value carries the column letter (498a/498b). We gate
    on resp=Bekker (case-insensitive: De virtutibus tags resp="bekker") so other
    page milestones - Plato's resp="Stephanus", say - never produce a Bekker
    locus. unit is "page" everywhere except De virtutibus's unit="section"
    (same page+column values); unit="line" milestones are excluded so the field
    stays page-level."""
    return (el.tag == MILESTONE_TAG and el.get("unit") in ("page", "section")
            and (el.get("resp") or "").lower() == "bekker")

# The sources this ingester is authoritative for. When it merges into the shared
# corpus_editions.json it refreshes only these and leaves the other ingesters'
# entries (ocr / cgpg / byzantium_gr / byzantine_vernacular) untouched.
# The source name of a TEI file is its directory under sources/ (first1k,
# perseus, galenus_verbatim, pta); anything under an unlisted directory is
# skipped. pta ids resolve to slugs via build_pta_crosswalk.py aliases.
OWN_SOURCES = {"first1k", "perseus", "galenus_verbatim", "pta"}

# When the SAME work+version id is present in more than one source (the Galenus
# Verbatim repo vendors First1K files, sometimes revised), prefer the live
# first1k copy unless another source's copy carries at least this factor more
# Greek tokens - a material completion (e.g. Galenus Verbatim restored the
# truncated book 1 of tlg0057.tlg095, +19%), not snapshot drift. Near-ties must
# never flip a served work to a stale or structurally worse vendored copy.
SAME_VERSION_WIN = 1.05

# A TEI edition never silently replaces a work served by another ingester (ocr /
# cgpg / byzantium_gr / byzantine_vernacular). The precedence ladder does put open
# TEI above OCR, but only for comparable coverage: first1k carries fragmentary
# stubs of works we hold in full from an OCR delivery (tlg1595.tlg370 is a ~9.7k
# token fragment of the 76k-token Sudhaus Volumina rhetorica), and a full rebuild
# used to clobber the larger text last-writer-wins. Two protections:
#   data/non_tei_authoritative.json  explicit keep-list: skip the TEI write, the
#                                    listed source stays primary until delisted
#   NON_TEI_KEEP_RATIO               unlisted collisions where the served non-TEI
#                                    text has this many times the TEI candidate's
#                                    Greek word tokens are skipped and reported
#                                    (add to the keep-list or displace explicitly)
# A collision below the ratio is a genuine TEI takeover (same-or-better coverage):
# the TEI wins as before, and the replacement is reported for audit.
# Skips/replacements land in data/corpus_loci_skips.json.
NON_TEI_KEEP = DATA / "non_tei_authoritative.json"
NON_TEI_KEEP_RATIO = 1.5

# Bekker page concordance for tlg0086 works whose served TEI carries no inline
# Bekker milestones (built by scripts/build_bekker_concordance.py from GLAUX +
# el.wikisource, content-aligned to the served rows). Unioned in per-locus below.
BEKKER_CONCORD = DATA / "bekker_concordance.json"

# Two editions of one work are MERGED only when they are genuinely complementary
# part-editions: their top-level loci (books) are disjoint AND their text barely
# overlaps. Either signal alone is unsafe - book labels can differ for the same
# text (Aristotle's Analytica as "priora"/"posteriora" vs "1"/"2", the Hippocratic
# Oath as "oath" vs "1"), and a relabelled recension can share text under new
# labels - so both must hold or the smaller edition is dropped (keep-max), never
# double-counted. Overlap is on word 5-gram shingles, near-unique to a text.
MERGE_OVERLAP_MAX = 0.10
_SHINGLE_N = 5
_GK_LETTER = re.compile(r"[Ͱ-Ͽἀ-῿]")

# Delimiter that separates a base citation from a disambiguation tag when two
# DISTINCT readings share one locus (see the collision resolution in main). It is
# guaranteed absent from every native locus, so a consumer recovers the base
# citation by splitting a served locus on it: "1.66.68.90~RV".split("~")[0].
DUP_LOCUS_SEP = "~"

# Recension sigla that appear as an in-text prefix and identify a DISTINCT witness
# sharing another reading's locus - used as the MEANINGFUL disambiguation tag so a
# variant reads as e.g. "1.66.68.90~RV" rather than an opaque ordinal. "RV" is
# Wellmann's alphabetical recension of Dioscorides (codices RV), printed inline as
# "<chapter-no> RV: ...". Extend this list as other structured recension markers
# turn up; anything unmatched falls back to a stable ordinal tag.
_RECENSION_RE = re.compile(r"^\s*\d*\s*(RV)\s*:")


def _recension_tag(text: str) -> str | None:
    """The recension siglum a reading carries as an in-text prefix, else None."""
    m = _RECENSION_RE.match(text)
    return m.group(1) if m else None


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text to path atomically: fill a sibling temp file then os.replace it
    (an atomic rename on the same filesystem), so a concurrent reader - a gold
    annotation pass reads data/corpus/ while this ingest rewrites it - never sees a
    half-written file."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _book_sort_key(books: set[str]):
    """Sort key for a fragment's set of top-level loci (its 'books'): numeric
    books first by their lowest number, named books after, so a work merged from
    several part-editions reads in citation order."""
    nums = [int(b) for b in books if b.isdigit()]
    if nums:
        return (0, min(nums), "")
    return (1, 0, min(books) if books else "")


def _norm_tok(t: str) -> str:
    """De-accent + lowercase a token to its bare Greek letters, so two editions'
    shingles match despite accent/case/punctuation differences."""
    d = unicodedata.normalize("NFD", t.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return "".join(c for c in d if _GK_LETTER.match(c))


def _shingles(psgs, n: int = _SHINGLE_N) -> set:
    """Set of word n-gram shingles over a passage list's normalized tokens."""
    toks = [w for _parts, text, *_ in psgs for t in text.split() if (w := _norm_tok(t))]
    if len(toks) < n:
        return {tuple(toks)} if toks else set()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def edition_id(path: Path, root) -> str:
    """CTS version of an edition, e.g. perseus-grc2 / 1st1K-grc1. Prefer the
    URN on the edition <div>, fall back to the filename's third dotted field."""
    for div in root.iter(DIV_TAG):
        if div.get("type") == "edition":
            urn = div.get("n") or ""
            tail = urn.rsplit(":", 1)[-1]            # tlg0012.tlg001.perseus-grc2
            bits = tail.split(".")
            if len(bits) >= 3:
                return ".".join(bits[2:])
            break
    bits = path.stem.split(".")                      # tlg0012.tlg001.perseus-grc2
    return ".".join(bits[2:]) if len(bits) >= 3 else path.stem


def passage_text(el, claimed=frozenset()) -> str:
    """Running Greek text of one passage element: its own text + descendants,
    minus the dropped material (notes, apparatus variants, headers) and minus any
    descendant in `claimed` (a finer citable unit - a numbered sub-div or a verse
    line - that emits its own passage), so each token is emitted exactly once.
    Excludes el's own tail (that belongs to the next passage)."""
    parts: list[str] = []

    def proc_children(e):
        for ch in e:
            if not is_dropped(ch) and ch not in claimed:
                if ch.text:
                    parts.append(ch.text)
                proc_children(ch)
            if ch.tail:                 # tail text sits at e's level, keep it
                parts.append(ch.tail)

    if el.text:
        parts.append(el.text)
    proc_children(el)
    return " ".join("".join(parts).split())


def passage_segments(el, claimed=frozenset()) -> list[str]:
    """The passage's text split into its physical/verse lines, for the additive
    text_lines field. It walks el IDENTICALLY to passage_text (same drop/claimed
    exclusions, same tail handling) but flushes a new segment at each line
    boundary the flat text otherwise loses:
      - a TEI <lb/> milestone (a printed line break inside a prose passage);
      - a verse <l> that RIDES inside this passage (an inset line not emitted as
        its own citable row, i.e. not in `claimed`).
    Because the split points are exactly the boundaries passage_text already
    walks past, ' '.join(segments) reconstructs passage_text's output verbatim -
    the concatenation invariant the caller asserts before emitting text_lines. A
    claimed (separately-cited) <l> is NOT a segment here; only its tail rides
    along, matching passage_text."""
    parts: list = []

    def proc_children(e):
        for ch in e:
            if ch.tag == LB_TAG and not is_dropped(ch):
                parts.append(_LINE_BREAK)          # printed line break
                if ch.tail:
                    parts.append(ch.tail)
                continue
            if (ch.tag == L_TAG and ch not in claimed and not is_dropped(ch)):
                parts.append(_LINE_BREAK)          # inset verse line rides here
                if ch.text:
                    parts.append(ch.text)
                proc_children(ch)
                parts.append(_LINE_BREAK)
                if ch.tail:
                    parts.append(ch.tail)
                continue
            if not is_dropped(ch) and ch not in claimed:
                if ch.text:
                    parts.append(ch.text)
                proc_children(ch)
            if ch.tail:
                parts.append(ch.tail)

    if el.text:
        parts.append(el.text)
    proc_children(el)

    segments: list[str] = []
    cur: list[str] = []
    for p in parts:
        if p is _LINE_BREAK:
            s = " ".join("".join(cur).split())
            if s:
                segments.append(s)
            cur = []
        else:
            cur.append(p)
    s = " ".join("".join(cur).split())
    if s:
        segments.append(s)
    return segments


def _is_textpart(el) -> bool:
    return el.tag == DIV_TAG and el.get("type") == "textpart"


def iter_passages(root, split_fallbacks=None, page_split=True):
    """Yield (locus_parts, text, bekker, text_lines) for every citable passage of
    an edition. `text_lines` is passage_segments(): the passage split into its
    printed/verse lines (>=1); ' '.join reproduces `text`. Emitted by the caller
    only when it has >=2 segments.

    Page split: a numbered div whose passage exceeds OVERSIZE_TOKENS Greek
    tokens AND whose own unclaimed content carries >= 2 distinct numbered
    <pb n=.../> page breaks is served as one row per edition page instead of a
    single whole-book blob: locus = the div's locus parts + the page number, in
    document order (see page_rows). Split rows carry no bekker and no
    text_lines. A div whose per-page reassembly fails the concatenation
    invariant is served unsplit and its locus appended to `split_fallbacks`
    (when given) for the caller's run summary.

    The Bekker-cited Aristotle corpus is excluded, keeping its current rows: an
    edition carrying inline Bekker milestones never page-splits (its canonical
    page layer is the `bekker` field, and its <pb> stream, where present, is
    just a print volume's pages), and the caller passes page_split=False for
    the tlg0086 works whose Bekker pages come from the concordance instead -
    that concordance is keyed by the served locus, so re-keying those rows
    would break the very page citability they already have.

    `bekker` is the list of distinct Bekker canonical pages whose text falls in
    this passage, in first-appearance order (e.g. ["498a", "498b"]); empty for
    editions with no Bekker milestones. The Aristotle editions carry the Bekker
    pagination LSJ cites as inline <milestone unit="page" resp="Bekker" n="498b"/>
    markers that the locus keying (book.section for Perseus, book.chapter for
    First1K) never exposes; emitting the covered pages per row lets a downstream
    resolver find an Aristotle passage by its Bekker page. A milestone can fall
    mid-section and a section can span several pages (measured: ~22% of
    Bekker-bearing rows span >1 page, up to 8 in the Metaphysics), so this is the
    full covered set, not just the starting page - a page-level lookup for any
    page the section overlaps then hits. Locus keying is unchanged; `bekker` is
    an additive per-row field, omitted from the emitted record when empty.

    The citable units are (a) every numbered textpart div and (b) every verse
    line. A numbered div emits the Greek directly under it MINUS whatever a finer
    unit claims, so each token is emitted exactly once and nothing is silently
    dropped: a prose chapter's loose intro paragraphs cite at the chapter locus,
    its sections at the section locus, and a section that mixes prose <p> with
    verse <l> emits the prose at its own locus and each line one level finer.

    Verse lines: every <l> inside a "verse container" (a textpart/edition div
    holding at least one numbered <l>). Greek editions number drama/epic lines
    only every fifth line, leaving the rest bare, so we number sequentially and
    snap the counter onto each explicit @n. locus = the container's @n chain +
    the line number. A bare <l> with no numbered sibling (an inset prose
    quotation) is NOT a verse line: it rides along in its div's passage text.
    """
    body = root.find(f".//{{{TEI_NS}}}text/{{{TEI_NS}}}body")
    if body is None:
        return []

    # Bekker page in effect just before each element (pre-order = document order).
    # A passage that starts mid-page inherits this as its opening page; one that
    # opens exactly on a page milestone picks the new page up from the walk below.
    page_before: dict = {}
    _cur = None
    has_bekker_milestones = False
    for e in body.iter():
        page_before[e] = _cur
        if is_bekker_page(e):
            _cur = e.get("n")
            has_bekker_milestones = True

    # Edition page in effect just before each element, over the numbered
    # <pb n=.../> page breaks (the CAG/GCS-style print pagination). Exactly
    # analogous to the Bekker page_before above; page_rows uses it to file an
    # oversized div's opening text under the page it actually sits on. A <pb>
    # carrying @ed records ANOTHER edition's pagination (First1K Clemens
    # interleaves Stählin and Potter pages as ed="alt"; Origen adds ed="r"),
    # often several streams at once, so only the edition's own un-@ed page
    # breaks define the page stream here and in page_rows below.
    pb_before: dict = {}
    _cur_pb = None
    for e in body.iter():
        pb_before[e] = _cur_pb
        if e.tag == PB_TAG and e.get("n") and e.get("ed") is None:
            _cur_pb = e.get("n")

    def ancestor_chain(el):
        # Walk ALL ancestors up to <body>, not just an unbroken run of <div>s:
        # citable <l>/divs are often wrapped in <q>/<sp>/<said>/<lg>, and we must
        # still pick up the book/section textpart above the wrapper. Unnumbered
        # intermediate levels (an act/scene div with no @n) are simply skipped.
        parts = []
        for cur in el.iterancestors():
            if cur is body:
                break
            if cur.tag == DIV_TAG and cur.get("type") == "textpart":
                n = cur.get("n")
                if n is not None:
                    parts.append(n)
        parts.reverse()
        return parts

    def verse_container(ln):
        # Nearest ancestor that anchors the locus prefix: a textpart div or the
        # edition div. Wrappers like <sp>/<q>/<lg> are transparent.
        for cur in ln.iterancestors():
            if cur.tag == DIV_TAG and cur.get("type") in ("textpart", "edition"):
                return cur
        return body

    # Classify <l> elements: group by verse container, keep only containers with
    # at least one numbered line. Those lines become citable units; assign loci.
    groups: dict = {}
    for ln in body.iter(L_TAG):
        groups.setdefault(verse_container(ln), []).append(ln)

    line_locus: dict = {}                              # <l> element -> locus_parts
    for cont, lines in groups.items():
        if not any(ln.get("n") is not None for ln in lines):
            continue                                   # inset quotation, not verse
        prefix = ancestor_chain(cont)
        if _is_textpart(cont) and cont.get("n") is not None:
            prefix = prefix + [cont.get("n")]
        counter = 0
        for ln in lines:
            n = ln.get("n")
            if n is not None and n.isdigit():
                counter = int(n)                       # snap to the explicit number
                num = n
            elif n is not None:
                num = n                                 # non-numeric label, keep
            else:
                counter += 1                            # bare line: interpolate
                num = str(counter)
            line_locus[ln] = prefix + [num]

    # `claimed` = every emitted unit; a div's passage text excludes these so a
    # token is never counted twice (once for the div, once for the finer unit).
    numbered_divs = [d for d in body.iter(DIV_TAG)
                     if _is_textpart(d) and d.get("n") is not None]
    # Transmitted front matter under an UNNUMBERED subtype div: the drama
    # hypotheseis (First1K Aeschylus). A curated set, not every subtype:
    # unnumbered subtypes are overwhelmingly drama-structure containers
    # (episode/choral/anapests/...) whose text is already served via their
    # verse lines, and serving those as rows would emit junk residue.
    subtype_divs = [d for d in body.iter(DIV_TAG)
                    if _is_textpart(d) and d.get("n") is None
                    and d.get("subtype") in SERVED_UNNUMBERED_SUBTYPES]
    claimed = set(line_locus) | set(numbered_divs) | set(subtype_divs)

    def bekker_pages(el):
        """Distinct Bekker pages that have Greek text in this passage, in
        first-appearance order. Walk el mirroring passage_text's traversal (same
        drop/claimed exclusions, so it sees exactly the passage's own text),
        tracking the current page across inline Bekker milestones; a page is
        recorded the first time Greek text is emitted under it. Starts from the
        page in effect at el (page_before), so a passage that opens mid-page still
        reports it; a page milestone with no following text in this passage (a
        page boundary right at a section edge) is not recorded, avoiding
        over-claiming an adjacent section's page."""
        cur = page_before.get(el)
        seen: set = set()
        ordered: list = []

        def mark(t):
            if cur is not None and t and _GK.search(t) and cur not in seen:
                seen.add(cur)
                ordered.append(cur)

        def walk(e, is_root):
            nonlocal cur
            if is_root and e.text:
                mark(e.text)
            for ch in e:
                if is_bekker_page(ch):
                    cur = ch.get("n")
                elif not is_dropped(ch) and ch not in claimed:
                    if ch.text:
                        mark(ch.text)
                    walk(ch, False)
                if ch.tail:
                    mark(ch.tail)

        walk(el, True)
        return ordered

    def page_rows(div, parts, full_text):
        """Per-page rows for an OVERSIZED numbered div: [(page_label, text)]
        covering the div's passage in document order, or None when the div is
        not splittable (fewer than 2 distinct numbered <pb n=.../> breaks in
        its own unclaimed content, or all its text on one page) or when the
        reassembly fails the concatenation invariant below (a <pb> mid-word
        would do it; the div is then served unsplit and reported). The walk
        mirrors passage_text EXACTLY (same is_dropped/claimed exclusions, same
        tail handling), switching the accumulation bucket at each numbered
        <pb>; text before the div's first <pb> files under the page in effect
        at the div's start (pb_before), or under the literal label 'init' when
        no page has begun yet. A page number repeating within the div (a
        pagination restart) gets '-2', '-3' suffixes so the loci stay unique.

        Only the edition's own page breaks switch buckets: a <pb> with @ed is
        an alternate edition's pagination (see pb_before above) and is walked
        past like any other milestone. A page break that falls INSIDE a word
        (PTA writes <pb n="192" break="no"/> at the printed hyphenation) defers
        the switch to the next whitespace, so the straddling word stays whole
        on the page it starts on and the concatenation invariant holds."""
        buckets: list[list] = [[pb_before.get(div) or "init", []]]
        switched: set = set()
        pending: list[str] = []       # switches awaiting a word boundary

        def cur_open_word() -> bool:
            for s in reversed(buckets[-1][1]):
                if s:
                    return not s[-1].isspace()
            return False

        def switch(page):
            switched.add(page)
            buckets.append([page, []])

        def add(t):
            while pending and t:
                m = re.search(r"\s", t)
                if m is None:         # word still not finished: stay put
                    buckets[-1][1].append(t)
                    return
                buckets[-1][1].append(t[:m.start()])
                switch(pending.pop(0))
                t = t[m.start():]
            if t:
                buckets[-1][1].append(t)

        def proc_children(e):
            for ch in e:
                if not is_dropped(ch) and ch not in claimed:
                    if ch.tag == PB_TAG and ch.get("n") and ch.get("ed") is None:
                        if cur_open_word():
                            pending.append(ch.get("n"))
                        else:
                            switch(ch.get("n"))
                    if ch.text:
                        add(ch.text)
                    proc_children(ch)
                if ch.tail:
                    add(ch.tail)

        if div.text:
            add(div.text)
        proc_children(div)
        for page in pending:          # pb at the very end: empty bucket, dropped
            switch(page)
        if len(switched) < 2:
            return None
        rows = [(page, " ".join("".join(chunk).split())) for page, chunk in buckets]
        rows = [(page, t) for page, t in rows if t]
        if len(rows) < 2:
            return None
        # Invariant: the split is a pure segmentation - the rows, rejoined,
        # reproduce the unsplit passage text verbatim (both sides are already
        # whitespace-normalized). On failure serve the div unsplit and let the
        # caller record it, rather than ever rewriting text.
        if " ".join(t for _page, t in rows) != full_text:
            if split_fallbacks is not None:
                split_fallbacks.append(".".join(parts))
            return None
        seen_pages: dict[str, int] = {}
        labeled: list[tuple[str, str]] = []
        for page, t in rows:
            seen_pages[page] = seen_pages.get(page, 0) + 1
            label = page if seen_pages[page] == 1 else f"{page}-{seen_pages[page]}"
            labeled.append((label, t))
        return labeled

    out = []
    for div in numbered_divs:
        out.append((ancestor_chain(div) + [div.get("n")], div, passage_text(div, claimed)))
    seen_subtype: dict = {}
    for div in subtype_divs:
        parts = ancestor_chain(div) + [div.get("subtype")]
        k = tuple(parts)
        seen_subtype[k] = seen_subtype.get(k, 0) + 1
        if seen_subtype[k] > 1:                      # repeated at one prefix
            parts = parts[:-1] + [f"{div.get('subtype')}-{seen_subtype[k]}"]
        out.append((parts, div, passage_text(div, claimed)))
    # Loose Greek directly under the edition div BEFORE its first citable
    # content (the Libanius declamation themata): direct children up to the
    # first child holding a claimed unit, emitted once under locus "pr".
    for ed in body.iter(DIV_TAG):
        if ed.get("type") != "edition":
            continue
        pre: list = []
        for ch in ed:
            if not isinstance(ch.tag, str):
                continue
            if ch in claimed or any(d in claimed for d in ch.iter()):
                break
            if is_dropped(ch):
                continue
            t = passage_text(ch, claimed)
            if t:
                pre.append(t)
        text = " ".join(pre)
        if _GK.search(text):
            out.append((["pr"], ed, text))
    for ln, parts in line_locus.items():
        out.append((parts, ln, passage_text(ln, claimed)))

    # Reading order, drop passages with no Greek (empty interior divs, milestones).
    order = {el: i for i, el in enumerate(body.iter())}
    out.sort(key=lambda x: order.get(x[1], 0))
    numbered_set = set(numbered_divs)
    do_page_split = page_split and not has_bekker_milestones
    result = []
    for parts, el, text in out:
        if not _GK.search(text):
            continue
        if (do_page_split and el in numbered_set
                and sum(1 for _ in _GK.finditer(text)) > OVERSIZE_TOKENS):
            rows = page_rows(el, parts, text)
            if rows is not None:
                # One row per edition page, no bekker / text_lines on split rows;
                # a page bucket with no Greek is dropped like any other passage.
                result.extend((parts + [label], t, [], [])
                              for label, t in rows if _GK.search(t))
                continue
        result.append((parts, text, bekker_pages(el), passage_segments(el, claimed)))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default=None,
                    help="restrict to works whose key starts with this prefix, "
                         "e.g. tlg0012 or tlg0012.tlg001")
    args = ap.parse_args()

    files = sorted(SRC.glob("*/data/*/*/*grc*.xml"))
    if args.only:
        files = [p for p in files if _WORK_RE.search(p.name)
                 and f"{_WORK_RE.search(p.name).group(1)}."
                 f"{_WORK_RE.search(p.name).group(2)}".startswith(args.only)]
    print(f"scanning {len(files)} TEI grc editions ...", file=sys.stderr)

    # Source works consumed by a served consolidation (e.g. the four First1K
    # Pindar-scholia files merged into the tlg5034.tlg001 slug, commit 3f8e8a8):
    # re-serving them would duplicate the consolidated text under a raw key. The
    # corpus_changes audit records are the source of truth: skip a work whose urn
    # a record lists in provenance.consolidated_from, as long as the consolidated
    # work itself is still served.
    consumed_by_consolidation: dict[str, str] = {}     # urn stem -> consolidated slug
    for rec_path in sorted((DATA / "corpus_changes").glob("*.json")):
        try:
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        meta = rec.get("_meta", {}) if isinstance(rec, dict) else {}
        prov = rec.get("provenance") if isinstance(rec, dict) else None
        merged = prov.get("consolidated_from", []) if isinstance(prov, dict) else []
        work = meta.get("work", "") if isinstance(meta, dict) else ""
        if merged and work and (CORPUS / f"{work}.jsonl").exists():
            for fn in merged:
                consumed_by_consolidation[fn[:-6] if fn.endswith(".jsonl") else fn] = work

    # Pass 1: gather EVERY acceptable edition per work. Most works have one, but
    # some (Diodorus, the Anthologia Graeca) are split across Perseus editions by
    # disjoint book range; Pass 2 keeps the largest as primary and merges in any
    # other edition covering DIFFERENT books, instead of dropping it (keep-max).
    cands: dict[str, list] = defaultdict(list)   # key -> [(ntok, source, lic, path, edition), ...]
    dropped_nc: dict[str, str] = {}    # key -> NC/unknown license, if no clean edition
    scanned: set[str] = set()          # every work key seen (winner or not)
    n_nc = n_empty = n_unmapped_pta = 0
    for i, p in enumerate(files):
        m = _WORK_RE.search(p.name)
        if not m:
            continue
        source = p.relative_to(SRC).parts[0]   # sources/<name>/data/... -> <name>
        if source not in OWN_SOURCES:
            continue
        urn = f"{m.group(1)}.{m.group(2)}"
        if urn in consumed_by_consolidation:
            continue
        key = slug_for(urn)                    # slug is the primary id, not the tlg
        if re.fullmatch(r"pta\d+\.pta\d+", key):
            # an unresolved pta id: deliberately unmapped in the pta crosswalk
            # (pta9999 = the PTA's vendored Septuaginta, handled by the LXX
            # sourcing track, not this ingest). Never serve raw pta ids.
            n_unmapped_pta += 1
            continue
        scanned.add(key)
        try:
            root = ET.parse(str(p)).getroot()
        except ET.XMLSyntaxError:
            continue
        lic = detect_license(root, source)
        if not is_acceptable(lic):
            n_nc += 1
            dropped_nc.setdefault(key, lic)
            continue
        ntok = sum(1 for _ in _GK.finditer(body_text(root)))
        if ntok == 0:
            n_empty += 1
            continue
        cands[key].append((ntok, source, lic, p, edition_id(p, root)))
        if i % 300 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)

    # Same-version dedup: when one work+version id arrived from several sources
    # (galenus_verbatim vendors First1K files, sometimes revised), keep a single
    # copy per version: the live first1k one, unless another source's copy has at
    # least SAME_VERSION_WIN times its Greek tokens (a material completion). This
    # runs BEFORE keep-max so a +2-token vendored near-tie can never displace the
    # canonical first1k text.
    for key, eds in cands.items():
        by_ver: dict[str, list] = defaultdict(list)
        for c in eds:
            by_ver[c[4]].append(c)                      # c = (ntok, source, lic, path, edition)
        if all(len(g) == 1 for g in by_ver.values()):
            continue
        kept = []
        for group in by_ver.values():
            best = max(group, key=lambda c: c[0])
            f1k = [c for c in group if c[1] == "first1k"]
            if f1k and best[0] < SAME_VERSION_WIN * max(f1k, key=lambda c: c[0])[0]:
                best = max(f1k, key=lambda c: c[0])
            kept.append(best)
        cands[key] = kept

    # Pass 2: extract locus-keyed passages. Keep the largest edition as primary
    # and merge in any other edition whose top-level loci (books) are DISJOINT
    # from what is already covered, so complementary part-editions are unioned but
    # two editions of the same book never double-count (the smaller is dropped, as
    # keep-max did). A single-edition work with unique loci is byte-identical to the
    # old output; one that repeats a locus (a re-presented passage) loses only the
    # repeat, via the per-locus dedup below.
    CORPUS.mkdir(parents=True, exist_ok=True)
    keep_list = (json.loads(NON_TEI_KEEP.read_text(encoding="utf-8"))
                 if NON_TEI_KEEP.exists() else {})
    skips: dict[str, dict] = {"keep_list": {}, "clobber_guard": {},
                              "replaced_foreign": {}}
    # Bekker concordance (scripts/build_bekker_concordance.py): {slug: {locus:
    # [pages]}} for tlg0086 works whose served TEI has NO inline Bekker
    # milestones. Consumed per-locus below: a row keeps its milestone-derived
    # `bekker` when it has one, and only falls back to the concordance when it has
    # none - the concordance fills works milestones left empty, never overriding.
    bekker_concord = (json.loads(BEKKER_CONCORD.read_text(encoding="utf-8"))
                      if BEKKER_CONCORD.exists() else {})

    def _served_foreign(key: str):
        """(source, greek_word_tokens) of the served corpus file when it belongs
        to ANOTHER ingester, else None. The file on disk is the source of truth
        (corpus_editions.json can be stale between reconciles)."""
        fp = CORPUS / f"{key}.jsonl"
        if not fp.exists():
            return None
        src = ntok = None
        with fp.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if src is None:
                    src = r.get("source")
                    if src in OWN_SOURCES:
                        return None
                    ntok = 0
                ntok += sum(1 for t in r["text"].split() if _GK.search(t))
        return (src, ntok) if src is not None else None

    editions: dict[str, dict] = {}
    warnings: dict[str, dict] = {}
    disambiguations: dict[str, dict] = {}   # work -> {base_locus: {basis, loci}}
    split_fallbacks: dict[str, list[str]] = {}   # work -> oversized divs served
    # unsplit because the page reassembly failed the concatenation invariant
    total_passages = 0
    for key in sorted(cands):
        if key in keep_list:
            skips["keep_list"][key] = {
                "kept_source": keep_list[key].get("kept_source"),
                "tei_candidates": [c[4] for c in cands[key]],
            }
            continue
        eds = sorted(cands[key], key=lambda c: (-c[0], c[4]))    # most tokens first
        # Near-tie anchor preference: when the top editions differ by <2% Greek
        # tokens, prefer the one carrying Bekker milestones - Poetica's Kassel
        # perseus-grc2 (222 anchors) loses keep-max to the Bekker-1837-text
        # digicorpus-grc2 by 65 tokens, throwing away the citation anchors for
        # a negligible token delta. A materially larger edition still wins.
        if len(eds) > 1 and eds[0][0] - eds[1][0] < 0.02 * eds[0][0]:
            def _has_bekker(c):
                try:
                    raw = c[3].read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    return False
                return 'resp="Bekker"' in raw or 'resp="bekker"' in raw
            if not _has_bekker(eds[0]):
                anchored = next((c for c in eds[1:]
                                 if eds[0][0] - c[0] < 0.02 * eds[0][0]
                                 and _has_bekker(c)), None)
                if anchored is not None:
                    eds.remove(anchored)
                    eds.insert(0, anchored)

        # Build the fragments that make up this work. A fragment is one edition's
        # passages; a non-primary edition joins only if its books don't overlap
        # what is already covered. Capture each kept edition's body-char count for
        # the dropped-chars diagnostic (computed only over editions we keep).
        multi = len(eds) > 1          # only the few multi-edition works pay for shingling
        frags = []            # (sort_key, edition, source, lic, [(parts,text,bekker,lines),...], ntok, body_chars)
        covered: set = set()          # 5-gram shingles already taken (tracked only when multi)
        covered_books: set[str] = set()
        for ntok, source, lic, path, edition in eds:
            root = ET.parse(str(path)).getroot()
            fb: list[str] = []
            psgs = [(parts, unicodedata.normalize("NFC", text), bekker,
                     [unicodedata.normalize("NFC", s) for s in lines])
                    for parts, text, bekker, lines in iter_passages(
                        root, fb,
                        # Concordance-covered tlg0086 works: their Bekker pages
                        # join on the served locus, so never page-split them
                        # (see the exclusion note in iter_passages).
                        page_split=key not in bekker_concord)]
            books = {parts[0] for parts, _t, _b, _l in psgs if parts}
            if multi:
                sh = _shingles(psgs)
                if frags:               # a supplement: merge only if truly complementary
                    overlap = len(sh & covered) / len(sh) if sh else 1.0
                    if overlap > MERGE_OVERLAP_MAX or not (books and books.isdisjoint(covered_books)):
                        continue        # alternate edition of the same text: drop (keep-max)
                covered |= sh
                covered_books |= books
            body_chars = sum(len(t) for t in
                             _GK.findall(unicodedata.normalize("NFC", body_text(root))))
            frags.append((_book_sort_key(books), edition, source, lic, psgs, ntok, body_chars))
            if fb:                       # only for editions actually served
                split_fallbacks.setdefault(key, []).extend(fb)

        # Order fragments by lowest book so a merged work reads in citation order
        # (Diodorus 1-5, 11-17, 18-20). A single-edition work is unaffected.
        frags.sort(key=lambda fr: fr[0])
        primary_edition, primary_source, primary_lic = frags[0][1], frags[0][2], frags[0][3]
        merged_eds = [fr[1] for fr in frags]
        n_tokens = sum(fr[5] for fr in frags)
        body_chars_total = sum(fr[6] for fr in frags)

        records = []          # (parts, text, bekker, lines, source, lic, edition)
        emitted_chars = 0
        for _sk, edition, source, lic, psgs, _nt, _bc in frags:
            for parts, text, bekker, lines in psgs:
                emitted_chars += sum(len(t) for t in _GK.findall(text))
                records.append((parts, text, bekker, lines, source, lic, edition))

        # Resolve same-locus collisions so the corpus stays strictly locus-keyed
        # (one served locus -> one row) WITHOUT ever discarding a distinct reading.
        # A locus repeats two ways, classified per colliding group by whether the
        # colliding rows carry the same text:
        #   EXACT  - byte-identical text (after whitespace-normalizing the already
        #            NFC text) presented twice under one @n. The Simmias figure poems
        #            in AG book 15 encode each verse line once in shape order under
        #            the div and again, reordered, inside a <quote> "to be read
        #            thus"; nested scholia and shared apparatus sigla collide the
        #            same way. Collapse to the FIRST occurrence and drop the repeats
        #            (counted as collapsed_dup_loci) - the dropped row added nothing.
        #   DISTINCT - different text under one citation. This is a real second
        #            reading, never a repeat: a manuscript recension (Dioscorides'
        #            RV alphabetical redaction printed beside the vulgate chapter),
        #            an antilabe / extra-metrical half-line the every-fifth-line @n
        #            numbering could not separate from the next numbered verse, or a
        #            nested-chapter section number that resolves onto an earlier
        #            chain. Multi-Source rule: keep BOTH. The first occurrence keeps
        #            the bare citation; each later distinct reading is disambiguated
        #            to base + DUP_LOCUS_SEP + tag, tag being a MEANINGFUL recension
        #            siglum when the text carries one (RV) and otherwise a stable
        #            1-based ordinal in emission order. Deterministic (emission order
        #            is fixed) and recorded in data/corpus_loci_disambiguated.json.
        # Emission order is preserved: only exact repeats are dropped and only the
        # later distinct readings are relocated; every other row is byte-identical.
        # emitted_chars above stays the PRE-resolution total on purpose - every body
        # char got a locus, so the dropped-chars diagnostic stays honest.
        idx_by_locus: dict[str, list[int]] = defaultdict(list)
        for i, rec in enumerate(records):
            idx_by_locus[".".join(rec[0])].append(i)
        final_locus: list = [None] * len(records)   # per-row served locus, None=drop
        base_of: list = [None] * len(records)        # disambiguated rows: base citation
        witness_of: list = [None] * len(records)     # disambiguated rows: recension tag
        n_collapsed = 0
        disamb_map: dict[str, dict] = {}
        for base, idxs in idx_by_locus.items():
            if len(idxs) == 1:
                final_locus[idxs[0]] = base
                continue
            # Collapse exact-text repeats, keeping the first (lowest-index) copy.
            seen_text: dict[str, bool] = {}
            distinct_idxs: list[int] = []
            for i in idxs:
                t = " ".join(records[i][1].split())
                if t in seen_text:
                    n_collapsed += 1
                    continue                          # exact repeat -> drop (locus None)
                seen_text[t] = True
                distinct_idxs.append(i)
            if len(distinct_idxs) == 1:
                final_locus[distinct_idxs[0]] = base
                continue
            # DISTINCT collision -> disambiguate, keep every reading in place.
            used_tags: set = set()
            loci_made: list[str] = []
            kinds: set = set()
            ordinal = 2
            for rank, i in enumerate(distinct_idxs):
                if rank == 0:
                    final_locus[i] = base                 # first keeps the bare citation
                    loci_made.append(base)
                    continue
                tag = _recension_tag(records[i][1])
                if tag and tag not in used_tags:
                    witness_of[i] = tag                   # meaningful recension basis
                    kinds.add("recension")
                else:
                    tag = str(ordinal); ordinal += 1
                    kinds.add("ordinal")
                while tag in used_tags:                    # guarantee uniqueness
                    tag = str(ordinal); ordinal += 1; kinds.add("ordinal")
                used_tags.add(tag)
                nl = f"{base}{DUP_LOCUS_SEP}{tag}"
                final_locus[i] = nl
                base_of[i] = base
                loci_made.append(nl)
            disamb_map[base] = {
                "basis": ("recension" if kinds == {"recension"}
                          else "mixed" if "recension" in kinds else "ordinal"),
                "loci": loci_made,
            }
        records = [(final_locus[i], text, bekker, lines, source, lic, edition,
                    base_of[i], witness_of[i])
                   for i, (parts, text, bekker, lines, source, lic, edition)
                   in enumerate(records) if final_locus[i] is not None]
        n_disambiguated = sum(len(v["loci"]) - 1 for v in disamb_map.values())

        foreign = _served_foreign(key)
        if foreign is not None:
            served_src, served_tok = foreign
            new_tok = sum(1 for r in records
                          for t in r[1].split() if _GK.search(t))
            if served_tok >= NON_TEI_KEEP_RATIO * new_tok:
                skips["clobber_guard"][key] = {
                    "kept_source": served_src, "kept_tokens": served_tok,
                    "tei_edition": primary_edition, "tei_tokens": new_tok,
                    "hint": "served text is materially larger than the TEI "
                            "candidate: add to non_tei_authoritative.json to "
                            "keep it, or displace it explicitly to let TEI win",
                }
                print(f"  CLOBBER-GUARD {key}: kept {served_src} "
                      f"({served_tok:,} tok) over {primary_edition} "
                      f"({new_tok:,} tok)", file=sys.stderr)
                continue
            # TEI takeover: preserve the displaced delivery as a secondary
            # witness (rank=secondary, per the corpus_secondary convention)
            sec_dir = DATA / "corpus_secondary"
            sec_dir.mkdir(parents=True, exist_ok=True)
            with (sec_dir / f"{key}.jsonl").open("a", encoding="utf-8") as sf, \
                    (CORPUS / f"{key}.jsonl").open(encoding="utf-8") as inf:
                for line in inf:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    r["rank"] = "secondary"
                    r["secondary_reason"] = (f"superseded by open TEI "
                                             f"{primary_edition} (build_corpus_loci)")
                    sf.write(json.dumps(r, ensure_ascii=False) + "\n")
            skips["replaced_foreign"][key] = {
                "replaced_source": served_src, "replaced_tokens": served_tok,
                "tei_edition": primary_edition, "tei_tokens": new_tok,
            }
            print(f"  TEI-TAKEOVER {key}: {served_src} ({served_tok:,} tok) -> "
                  f"secondary; {primary_edition} ({new_tok:,} tok) now primary",
                  file=sys.stderr)

        concord_work = bekker_concord.get(key, {})   # {} for non-tlg0086 works
        out_lines: list[str] = []
        for (locus, text, bekker, lines, source, lic, edition,
             base_locus, witness) in records:
            rec = {
                "urn": key,
                "edition": edition,
                "locus": locus,
                "source": source,
                "license": lic,
                "text": text,
            }
            # A disambiguated reading (a DISTINCT second reading that shared this
            # citation) carries its base citation, and the recension siglum when the
            # disambiguation was by witness rather than a bare ordinal - both
            # additive, absent from every non-colliding row.
            if base_locus is not None:
                rec["base_locus"] = base_locus
                if witness is not None:
                    rec["witness"] = witness
            # Bekker pages: the milestone-derived set when this row has one,
            # else the concordance's pages for this locus (fills the works
            # whose TEI has no milestones; never overrides a milestone row). A
            # disambiguated row looks the concordance up by its base citation.
            pages = bekker if bekker else concord_work.get(base_locus or locus)
            if pages:                        # additive, page-level Bekker loci;
                rec["bekker"] = pages        # omitted when neither source has any
            # text_lines: the passage's printed/verse lines, emitted only when
            # there are >=2 and they concatenate back to `text` exactly (the
            # invariant that keeps it a pure segmentation, never a rewrite).
            if len(lines) >= 2 and " ".join(lines) == text:
                rec["text_lines"] = lines
            out_lines.append(json.dumps(rec, ensure_ascii=False))
        _atomic_write_text(CORPUS / f"{key}.jsonl",
                           "".join(line + "\n" for line in out_lines))
        if disamb_map:
            disambiguations[key] = disamb_map
        total_passages += len(records)
        editions[key] = {
            "edition": primary_edition,
            "source": primary_source,
            "license": primary_lic,
            "n_passages": len(records),
            "n_tokens": n_tokens,
        }
        if len(merged_eds) > 1:
            editions[key]["merged_editions"] = merged_eds
        # Report the ways a work's citation structure can fail us. Both dup fields
        # describe a RESOLVED condition - the written file always has one row per
        # served locus - and are mutually exclusive per collision (exact vs
        # distinct):
        #   dropped_chars           Greek characters in the body(ies) that no passage
        #                           emitted - text under no numbered div and in no
        #                           verse line, so we could not assign it a locus
        #                           (measured in characters, as the running-text join
        #                           differs from body_text's spacing)
        #   collapsed_dup_loci      exact repeats of a passage that shared a locus and
        #                           were dropped (a re-presented figure poem, nested
        #                           scholia, shared apparatus sigla); count of drops.
        #   disambiguated_dup_loci  DISTINCT readings that shared a locus and were
        #                           relocated to base~tag so both survive (a manuscript
        #                           recension, an antilabe half-line, a nested-chapter
        #                           section clash); count of relocated readings. The
        #                           base -> [loci] + basis map is in
        #                           data/corpus_loci_disambiguated.json.
        bad: dict[str, int] = {}
        if emitted_chars < body_chars_total:
            bad["dropped_chars"] = body_chars_total - emitted_chars
        if n_collapsed:
            bad["collapsed_dup_loci"] = n_collapsed
        if n_disambiguated:
            bad["disambiguated_dup_loci"] = n_disambiguated
        if bad:
            warnings[key] = {"edition": primary_edition, **bad}

    # Merge into the shared corpus_editions.json rather than overwriting it: keep
    # the other ingesters' entries (ocr / cgpg / byzantium_gr / byzantine_vernacular)
    # and refresh only OUR sources, dropping any of ours that scanned this run but
    # no longer wins. This keeps a base rebuild idempotent and stops it clobbering
    # the other sources (the Makefile chain runs this first, the rest merge on top).
    ce_path = DATA / "corpus_editions.json"
    existing = json.loads(ce_path.read_text(encoding="utf-8")) if ce_path.exists() else {}
    merged = {k: v for k, v in existing.items()
              if v.get("source") not in OWN_SOURCES or k not in scanned}
    merged.update(editions)
    _atomic_write_text(
        ce_path, json.dumps(merged, ensure_ascii=False, indent=0, sort_keys=True))
    # works available ONLY under NC/unknown (no clean winner) -> PD/OCR track.
    # needs_pd_or_ocr.json is a SHARED registry that other local producers also
    # write, so MERGE (replace only our own "build_corpus_loci" records, preserve
    # the rest) rather than overwrite. See scripts/needs_registry.py.
    from needs_registry import merge_needs
    mine = {k: {"needs": ["pd_or_ocr"], "license": v}
            for k, v in sorted(dropped_nc.items()) if k not in cands}
    merge_needs(DATA / "needs_pd_or_ocr.json", "build_corpus_loci", mine,
                scope=scanned if args.only else None)
    # The warnings and skips reports are rebuilt wholesale by a full run; a
    # PARTIAL run (--only) merges over the existing file instead - it only
    # re-examined a subset, so wholesale would delete every other work's rows.
    def _report(path: Path, mine: dict, nest: bool) -> None:
        if args.only and path.exists():
            prev = json.loads(path.read_text(encoding="utf-8"))
            if nest:                    # {section: {work: row}}
                for sec, rows in mine.items():
                    kept = {k: v for k, v in prev.get(sec, {}).items()
                            if k not in scanned}
                    mine[sec] = {**kept, **rows}
            else:                       # {work: row}
                kept = {k: v for k, v in prev.items() if k not in scanned}
                mine.update(kept)
        empty = not (any(mine.values()) if nest else mine)
        if empty and not path.exists():
            return
        _atomic_write_text(path, json.dumps(mine, ensure_ascii=False, indent=1,
                                            sort_keys=True))

    if warnings or args.only:
        _report(DATA / "corpus_loci_warnings.json", warnings, nest=False)
    # Durable audit of the distinct same-locus readings we disambiguated (base
    # citation -> the loci it became + the basis), so the split is reversible and a
    # downstream consumer can re-key its per-locus annotations onto the new loci.
    if disambiguations or args.only:
        _report(DATA / "corpus_loci_disambiguated.json", disambiguations, nest=False)
    # Run diagnostics for the non-TEI protections (the durable record is the
    # keep-list itself).
    if any(skips.values()) or args.only:
        _report(DATA / "corpus_loci_skips.json", skips, nest=True)

    bylic = defaultdict(int)
    for v in editions.values():
        bylic[v["license"]] += 1
    print(f"\nworks: {len(editions)} | passages: {total_passages:,} | "
          f"Greek tokens: {sum(v['n_tokens'] for v in editions.values()):,}",
          file=sys.stderr)
    print(f"NC/unknown excluded: {n_nc} | empty: {n_empty}"
          + (f" | unmapped pta skipped: {n_unmapped_pta}" if n_unmapped_pta else ""),
          file=sys.stderr)
    print(f"works by license: {dict(bylic)}", file=sys.stderr)
    print(f"works with locus warnings: {len(warnings)}", file=sys.stderr)
    if split_fallbacks:
        print("page-split invariant fallbacks (served unsplit): "
              + "; ".join(f"{k} [{', '.join(v)}]"
                          for k, v in sorted(split_fallbacks.items())),
              file=sys.stderr)
    if any(skips.values()):
        print(f"non-TEI protections: {len(skips['keep_list'])} keep-list, "
              f"{len(skips['clobber_guard'])} clobber-guarded, "
              f"{len(skips['replaced_foreign'])} foreign works replaced by TEI "
              f"(see data/corpus_loci_skips.json)", file=sys.stderr)
    print("wrote data/corpus/*.jsonl, corpus_editions.json"
          + (", corpus_loci_warnings.json" if warnings else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
