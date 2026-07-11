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
import re
import sys
import unicodedata
from collections import Counter, defaultdict
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
MILESTONE_TAG = f"{{{TEI_NS}}}milestone"
LB_TAG = f"{{{TEI_NS}}}lb"

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


def iter_passages(root):
    """Yield (locus_parts, text, bekker, text_lines) for every citable passage of
    an edition. `text_lines` is passage_segments(): the passage split into its
    printed/verse lines (>=1); ' '.join reproduces `text`. Emitted by the caller
    only when it has >=2 segments.

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
    for e in body.iter():
        page_before[e] = _cur
        if is_bekker_page(e):
            _cur = e.get("n")

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
    claimed = set(line_locus) | set(numbered_divs)

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

    out = []
    for div in numbered_divs:
        out.append((ancestor_chain(div) + [div.get("n")], div, passage_text(div, claimed)))
    for ln, parts in line_locus.items():
        out.append((parts, ln, passage_text(ln, claimed)))

    # Reading order, drop passages with no Greek (empty interior divs, milestones).
    order = {el: i for i, el in enumerate(body.iter())}
    out.sort(key=lambda x: order.get(x[1], 0))
    return [(parts, text, bekker_pages(el), passage_segments(el, claimed))
            for parts, el, text in out if _GK.search(text)]


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
        key = slug_for(f"{m.group(1)}.{m.group(2)}")   # slug is the primary id, not the tlg
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
    # keep-max did). A single-edition work is byte-identical to the old output.
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
            psgs = [(parts, unicodedata.normalize("NFC", text), bekker,
                     [unicodedata.normalize("NFC", s) for s in lines])
                    for parts, text, bekker, lines in iter_passages(root)]
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

        foreign = _served_foreign(key)
        if foreign is not None:
            served_src, served_tok = foreign
            new_tok = sum(1 for _p, text, _b, _l, _s, _lic, _e in records
                          for t in text.split() if _GK.search(t))
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
        out_path = CORPUS / f"{key}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for parts, text, bekker, lines, source, lic, edition in records:
                locus = ".".join(parts)
                rec = {
                    "urn": key,
                    "edition": edition,
                    "locus": locus,
                    "source": source,
                    "license": lic,
                    "text": text,
                }
                # Bekker pages: the milestone-derived set when this row has one,
                # else the concordance's pages for this locus (fills the works
                # whose TEI has no milestones; never overrides a milestone row).
                pages = bekker if bekker else concord_work.get(locus)
                if pages:                        # additive, page-level Bekker loci;
                    rec["bekker"] = pages        # omitted when neither source has any
                # text_lines: the passage's printed/verse lines, emitted only when
                # there are >=2 and they concatenate back to `text` exactly (the
                # invariant that keeps it a pure segmentation, never a rewrite).
                if len(lines) >= 2 and " ".join(lines) == text:
                    rec["text_lines"] = lines
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
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
        # Report the two ways a work's citation structure can fail us:
        #   dropped_chars  Greek characters in the body(ies) that no passage
        #                  emitted - text under no numbered div and in no verse
        #                  line, so we could not assign it a locus (measured in
        #                  characters, as the running-text join differs from
        #                  body_text's spacing)
        #   dup_loci       the @n hierarchy is not a unique citation (deeply
        #                  nested scholia / shared apparatus sigla) so two
        #                  passages collide on one locus
        bad: dict[str, int] = {}
        if emitted_chars < body_chars_total:
            bad["dropped_chars"] = body_chars_total - emitted_chars
        seen = Counter(".".join(r[0]) for r in records)
        n_dup = sum(c - 1 for c in seen.values() if c > 1)
        if n_dup:
            bad["dup_loci"] = n_dup
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
    ce_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=0, sort_keys=True))
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
        path.write_text(json.dumps(mine, ensure_ascii=False, indent=1,
                                   sort_keys=True))

    if warnings or args.only:
        _report(DATA / "corpus_loci_warnings.json", warnings, nest=False)
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
    if any(skips.values()):
        print(f"non-TEI protections: {len(skips['keep_list'])} keep-list, "
              f"{len(skips['clobber_guard'])} clobber-guarded, "
              f"{len(skips['replaced_foreign'])} foreign works replaced by TEI "
              f"(see data/corpus_loci_skips.json)", file=sys.stderr)
    print("wrote data/corpus/*.jsonl, corpus_editions.json"
          + (", corpus_loci_warnings.json" if warnings else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
