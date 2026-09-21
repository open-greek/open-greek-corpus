#!/usr/bin/env python3
"""Roll up the form-frequency lexicon (the "yardstick") from the WHOLE ingested
open corpus in data/corpus/*.jsonl, not from the TEI alone.

The yardstick must be defined by cog's own corpus, and must grow automatically
every time a TLG-only work is replaced by an open/PD source. So the lexicon is a
rollup over every ingested passage in data/corpus/*.jsonl: the open TEI editions
(written by build_corpus_loci.py), the Byzantine vernacular texts
(build_byzantine_vernacular_corpus.py), and the PD/CC ingests that fill the gaps
(calfa-co Patrologia Graeca,
byzantium.gr historians). Each ingester writes its passages to data/corpus and
merges into corpus_editions.json; this script is the single lexicon builder over
the union, so a new ingest flows into the yardstick with no extra step.

The TEI-parsing helpers below (body_text, detect_license, the drop set, the Greek
regex) remain the shared library that build_corpus_loci.py imports for ingest;
only the lexicon rollup moved here off the TEI and onto the ingested corpus.

Outputs (under data/):
  public_lexicon.tsv     form<TAB>count over every ingested passage
  public_lexicon_exclusions.tsv
                         nonlexical marked forms kept out of the lexicon
  public_elision_stem_candidates.tsv
                         bare/marked form pairs needing lemma-level review
  coverage.json          per work urn: source, license, tokens, passages

  python build_public_corpus.py      # run AFTER the ingesters populate data/corpus
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources"
DATA = REPO / "data"
CORPUS = DATA / "corpus"
TEI_NS = "http://www.tei-c.org/ns/1.0"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
# The corpus-wide matcher above deliberately remains broad: many measurement and
# ingest callers use it as an inclusive Greek-run counter.  The public lexicon
# needs a stricter boundary, though.  A trailing apostrophe is part of an elided
# form (``δ’``, ``κατ'``), not punctuation to discard before frequency
# aggregation.  Keep the three non-Greek spacing forms here; U+1FBD/U+1FBF are
# already in the Greek ranges and are canonicalized below when trailing.
_LEXICON_GK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+(?:['’ʼ´`ʹ])?")
_TRAILING_ELISION_MARKS = frozenset(("'", "’", "ʼ", "´", "`", "ʹ", "᾽", "᾿", "̓"))
_ELISION_CANONICAL = "’"
# These are not independent lexical forms.  A source that emits one without a
# trailing elision mark has lost or detached the mark; treating it as evidence
# is precisely how a frequency rollup makes a Hunspell dictionary accept junk.
# Keep this aligned with Dilemma's export-side guard.  Valid unaccented forms
# such as τε and περ are deliberately absent.
_BARE_ELISION_STEMS = frozenset((
    "δ", "ἀλλ", "δι", "καθ", "κατ", "παρ", "ἐπ", "ἐφ", "οὐδ", "ὑπ", "ἀπ", "μεθ", "τ",
))
# A one-letter form followed by a mark is generally a Greek numeral.  These are
# the small set of unaccented one-letter elisions that the source can attest as
# lexical forms.  Keep this conservative: the lexicon is evidence for a spell
# checker, and an omitted rare form is safer than a spurious accepted word.
_SINGLE_LETTER_ELISIONS = frozenset(("δ", "τ", "θ", "γ", "μ", "σ", "κ", "ῥ"))
_GREEK_NUMERAL_VALUES = {
    "α": 1, "β": 2, "γ": 3, "δ": 4, "ε": 5, "ϛ": 6, "ζ": 7, "η": 8, "θ": 9,
    "ι": 10, "κ": 20, "λ": 30, "μ": 40, "ν": 50, "ξ": 60, "ο": 70, "π": 80,
    "ϟ": 90, "ρ": 100, "σ": 200, "τ": 300, "υ": 400, "φ": 500, "χ": 600,
    "ψ": 700, "ω": 800, "ϡ": 900,
}
_ELISION_CANDIDATE_MIN_MARKED = 100
_ELISION_CANDIDATE_RATIO = 10
# elements whose text is NOT the running edition text
DROP = {f"{{{TEI_NS}}}{t}" for t in ("note", "rdg", "bibl", "ref", "title",
                                     "speaker", "label", "head", "gap", "del")}
# The work part allows a single letter suffix: First1K splits some works into
# lettered sub-editions (tlg5034.tlg001a-d = Drachmann's Pindar scholia per
# ode-book), which the digits-only pattern silently skipped - 3.2MB of scholia
# TEI sat unserved because the filename never matched.
_WORK_RE = re.compile(r"((?:tlg|pta)\d+)\.((?:tlg|pta)\d+[a-z]?)\.")

# Per-source repo default license (all three TEI repos are CC BY-SA 4.0). Inline
# <licence> overrides this. NC licenses are EXCLUDED from the corpus (public-
# path: no non-commercial restriction); their works fall to the PD/OCR track.
# pta has NO repo default: its licensing is per file (147 BY-SA / 65 BY / 1
# BY-NC-SA), so a pta file without an inline <licence> stays "unknown" (excluded).
REPO_DEFAULT_LICENSE = {"first1k": "CC-BY-SA-4.0", "perseus": "CC-BY-SA-4.0",
                        "galenus_verbatim": "CC-BY-SA-4.0"}

_SIC = f"{{{TEI_NS}}}sic"
_CHOICE = f"{{{TEI_NS}}}choice"
_CORR = f"{{{TEI_NS}}}corr"


def is_dropped(el) -> bool:
    """True for elements whose text is NOT the running edition text: the DROP
    set, plus a <sic> whose parent <choice> also carries a <corr> (emit only the
    corrected reading, never both). A standalone <sic> outside such a pair IS
    the text (it just flags a printed anomaly) and is kept."""
    if el.tag in DROP:
        return True
    if el.tag == _SIC:
        parent = el.getparent()
        return (parent is not None and parent.tag == _CHOICE
                and parent.find(_CORR) is not None)
    return False


def detect_license(root, source: str) -> str:
    """License id for a TEI edition: inline <licence> target/text if present,
    else the source repo default."""
    for lic in root.iter(f"{{{TEI_NS}}}licence"):
        blob = ((lic.get("target") or "") + " " + "".join(lic.itertext())).lower()
        if "by-nc" in blob or "noncommercial" in blob:
            return "CC-BY-NC-SA"
        if "by-sa" in blob or "sharealike" in blob:
            return "CC-BY-SA-4.0"
        if "publicdomain" in blob or "cc0" in blob:
            return "CC0/PD"
        if "licenses/by/" in blob or "/by/4" in blob:
            return "CC-BY-4.0"
    return REPO_DEFAULT_LICENSE.get(source, "unknown")


def is_acceptable(lic: str) -> bool:
    """Exclude non-commercial (and unknown) licenses from the public corpus."""
    return "NC" not in lic and lic != "unknown"


def body_text(root) -> str:
    """Greek running text of a TEI edition: <body>, minus header/notes/variants."""
    body = root.find(f".//{{{TEI_NS}}}text/{{{TEI_NS}}}body")
    if body is None:
        return ""
    parts = []

    def walk(el):
        if not isinstance(el.tag, str):
            # comment/PI node: its content (e.g. commented-out apparatus divs)
            # is not body text, but the tail after it is
            if el.tail:
                parts.append(el.tail)
            return
        if is_dropped(el) or (el.tag == f"{{{TEI_NS}}}div"
                              and el.get("type") == "praefatio"):
            # praefatio: modern editorial front matter (PTA's German/English
            # introductions quoting Greek), a sibling of the edition div. A
            # denylist, not an edition-div allowlist, because some files keep
            # textpart divs OUTSIDE the edition wrapper (tlg5031.tlg001).
            if el.tail:
                parts.append(el.tail)
            return
        if el.text:
            parts.append(el.text)
        for ch in el:
            walk(ch)
        if el.tail:
            parts.append(el.tail)

    walk(body)
    return " ".join(parts)


def _has_final_grave(token: str) -> bool:
    """Whether the final letter before a mark carries a grave accent.

    In a genuine elision the accent moves back as an acute.  A grave directly
    before a terminal quote is therefore punctuation, not a lexical elision.
    """
    return unicodedata.normalize("NFD", token).endswith("\u0300")


def _is_single_greek_letter(token: str) -> bool:
    """True for one Greek letter with optional breathing/accent marks."""
    return sum(char.isalpha() for char in unicodedata.normalize("NFD", token)) == 1


def _is_greek_numeral_sequence(token: str) -> bool:
    """Recognize unaccented multi-letter Greek numerals before lexicon entry.

    Greek numerals descend from hundreds through tens to units.  This accepts
    forms such as ``ιε’`` and ``λε’`` but not lexical elisions like ``κατ’``
    (20, 1, 300) or ``δι’`` (4, 10).  The final-sigma spelling of stigma is
    accepted because it is common in the source material.
    """
    decomposed = unicodedata.normalize("NFD", token)
    if any(unicodedata.combining(char) for char in decomposed):
        return False
    letters = token.casefold().replace("ς", "ϛ")
    values = [_GREEK_NUMERAL_VALUES.get(char) for char in letters]
    return len(values) > 1 and all(value is not None for value in values) \
        and all(left > right for left, right in zip(values, values[1:]))


def public_lexicon_tokenization(text: str) -> tuple[list[str], Counter[tuple[str, str]]]:
    """Return lexical forms and classified nonlexical marked-form exclusions.

    Final apostrophe-like marks are normalized to U+2019 for genuine elisions.
    Numerals, final-sigma quote/numeral forms, and grave-before-quote forms are
    recorded separately instead of becoming durable spell-checker evidence.
    An initial U+1FBF can carry real aphaeresis (``᾿ς``), so it is untouched.
    """
    out = []
    exclusions: Counter[tuple[str, str]] = Counter()
    for raw in _LEXICON_GK.findall(text):
        # The broad Greek blocks include spacing breathings/koronis.  A mark by
        # itself is not a word and must not become a public-lexicon entry.
        if not any(char.isalpha() for char in raw):
            continue
        token = unicodedata.normalize("NFC", raw)
        if token[-1] in _TRAILING_ELISION_MARKS:
            token = token[:-1] + _ELISION_CANONICAL
            stem = token[:-1]
            # A final sigma cannot precede a lost vowel.  These are closing
            # quotation marks or numeral notation, never elisions.
            if stem.endswith("ς"):
                exclusions[("final_sigma_mark", token)] += 1
                continue
            if _has_final_grave(stem):
                exclusions[("grave_before_mark", token)] += 1
                continue
            if _is_single_greek_letter(stem):
                if stem not in _SINGLE_LETTER_ELISIONS:
                    exclusions[("greek_numeral", token)] += 1
                    continue
            elif _is_greek_numeral_sequence(stem):
                exclusions[("greek_numeral", token)] += 1
                continue
        if token in _BARE_ELISION_STEMS:
            exclusions[("bare_elision_stem", token)] += 1
            continue
        out.append(token)
    return out, exclusions


def public_lexicon_tokens(text: str) -> list[str]:
    """NFC public-lexicon forms, retaining only lexical final elision marks."""
    return public_lexicon_tokenization(text)[0]


def public_elision_stem_candidates(lex: Counter[str]) -> list[tuple[str, int, str, int]]:
    """Bare/marked pairs whose frequency asymmetry merits lemma-level review.

    The public corpus does not know whether the two surface forms share a
    lemma.  This function deliberately *does not* exclude them.  Dilemma's
    exporter can validate that identity against its lookup data before deciding
    whether a bare stem is nonlexical.
    """
    candidates = []
    for marked, marked_count in lex.items():
        if not marked.endswith(_ELISION_CANONICAL):
            continue
        bare = marked[:-1]
        bare_count = lex.get(bare, 0)
        if bare_count and marked_count >= _ELISION_CANDIDATE_MIN_MARKED \
                and marked_count >= bare_count * _ELISION_CANDIDATE_RATIO:
            candidates.append((bare, bare_count, marked, marked_count))
    return sorted(candidates, key=lambda row: (-row[3], row[0]))


def main() -> None:
    files = sorted(CORPUS.glob("*.jsonl"))
    if not files:
        sys.exit(f"no ingested corpus in {CORPUS} - run the ingesters first "
                 "(build_corpus_loci.py, build_byzantine_vernacular_corpus.py, ...)")
    print(f"rolling up {len(files)} ingested works in data/corpus/ ...",
          file=sys.stderr)

    # Yardstick dedup: a frequency yardstick must not count the same text twice.
    # Two duplication modes are excluded from the LEXICON (coverage.json still
    # lists every work, marked): (1) DUPLICATE-EDITION - several primary works
    # crosswalk to the same TLG id (variant editions / different fragment scopes
    # of one canonical work); count only the token-fullest. (2) SUBSET-WORK - a
    # smaller work whose substantial rows are (near-)entirely byte-contained in a
    # larger one (a canonical sub-collection like the theological letters inside
    # the full letters, under a DIFFERENT work id so (1) misses it); count only
    # the superset. Cross-work formulaic overlap (repeated epic verses, parallel
    # gnomologia) is NOT a subset and is left counted - those are real, distinct
    # attestations. One hash pre-pass over all rows drives both.
    lex_excluded: dict[str, str] = {}    # excluded work stem -> kept work stem
    SUBSET_MIN, SUBSET_HASHES = 0.95, 20     # >=95% contained, >=20 rows to judge
    work_hashes: dict[str, set] = {}
    work_gk: dict[str, int] = {}
    for fp in files:
        hs, gk = set(), 0
        for line in fp.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            t = json.loads(line).get("text", "")
            gk += len(_GK.findall(t))
            if len(t) >= 40 and _GK.search(t):
                hs.add(hashlib.md5(t.encode("utf-8")).digest())
        work_hashes[fp.stem], work_gk[fp.stem] = hs, gk

    cw_path = DATA / "tlg_crosswalk.json"
    if cw_path.exists():
        cw = json.loads(cw_path.read_text(encoding="utf-8"))
        by_tlg = defaultdict(list)
        for slug, e in cw.items():
            t = e.get("tlg") if isinstance(e, dict) else e
            if t and (CORPUS / f"{slug}.jsonl").exists():
                by_tlg[str(t)].append(slug)
        for t, slugs in by_tlg.items():
            if len(slugs) < 2:
                continue
            for stem in sorted(slugs, key=lambda s: work_gk.get(s, 0),
                               reverse=True)[1:]:
                lex_excluded[stem] = max(slugs, key=lambda s: work_gk.get(s, 0))

    # subset detection: only among works that share >=1 substantial row (cheap
    # candidate gate via an inverted hash index), then the containment test.
    hash_index: dict = defaultdict(list)
    for stem, hs in work_hashes.items():
        for h in hs:
            hash_index[h].append(stem)
    candidates: set = set()
    for stems in hash_index.values():
        if len(stems) > 1:
            for a in stems:
                for b in stems:
                    if a != b:
                        candidates.add(tuple(sorted((a, b))))
    for a, b in candidates:
        big, small = (a, b) if work_gk.get(a, 0) >= work_gk.get(b, 0) else (b, a)
        hs, hb = work_hashes[small], work_hashes[big]
        if small in lex_excluded or len(hs) < SUBSET_HASHES:
            continue
        if len(hs & hb) / len(hs) >= SUBSET_MIN:
            lex_excluded[small] = big
    if lex_excluded:
        print(f"  lexicon dedup: {len(lex_excluded)} duplicate-edition / subset "
              f"works counted via their fuller siblings only", file=sys.stderr)

    lex: Counter[str] = Counter()
    lex_exclusions: Counter[tuple[str, str]] = Counter()
    coverage: dict[str, dict] = {}      # work urn -> {source, license, tokens, passages}
    for i, fp in enumerate(files):
        # An excluded work still contributes its rows that the keeper does NOT
        # carry (unique fragments of a variant edition), just not the shared
        # ones - so each distinct served text is counted exactly once without
        # dropping real coverage. A 100%-subset work (gregorius) contributes
        # nothing; a byte-different variant edition keeps its unique lines.
        keeper = lex_excluded.get(fp.stem)
        keeper_hashes = work_hashes.get(keeper, set()) if keeper else None
        excluded_shared = 0
        with fp.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                text = rec.get("text", "")
                toks, exclusions = public_lexicon_tokenization(text)
                if keeper_hashes is not None and len(text) >= 40 and _GK.search(text) \
                        and hashlib.md5(text.encode("utf-8")).digest() in keeper_hashes:
                    excluded_shared += 1          # shared with keeper: don't recount
                else:
                    lex.update(toks)
                    lex_exclusions.update(exclusions)
                key = rec.get("urn") or fp.stem
                cov = coverage.setdefault(
                    key, {"source": rec.get("source"),
                          "license": rec.get("license"), "tokens": 0, "passages": 0})
                # coverage.json is the inclusive corpus-count metric.  The
                # public lexicon is intentionally stricter about bare marks and
                # detached elision stems, so its token list is not the coverage
                # accounting unit.
                cov["tokens"] += len(_GK.findall(text))
                cov["passages"] += 1
        if keeper and fp.stem in coverage:
            coverage[fp.stem]["lexicon_dedup"] = {
                "keeper": keeper, "shared_rows_not_recounted": excluded_shared}
        if i % 300 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)

    DATA.mkdir(exist_ok=True)
    with (DATA / "public_lexicon.tsv").open("w", encoding="utf-8") as f:
        for form, n in lex.most_common():
            f.write(f"{form}\t{n}\n")
    with (DATA / "public_lexicon_exclusions.tsv").open("w", encoding="utf-8") as f:
        f.write("reason\tform\tcount\n")
        for (reason, form), n in sorted(lex_exclusions.items(),
                                        key=lambda item: (item[0][0], -item[1], item[0][1])):
            f.write(f"{reason}\t{form}\t{n}\n")
    with (DATA / "public_elision_stem_candidates.tsv").open("w", encoding="utf-8") as f:
        f.write("bare_form\tbare_count\tmarked_form\tmarked_count\tmarked_to_bare_ratio"
                "\trequires_same_lemma_validation\n")
        for bare, bare_count, marked, marked_count in public_elision_stem_candidates(lex):
            ratio = marked_count / bare_count
            f.write(f"{bare}\t{bare_count}\t{marked}\t{marked_count}\t{ratio:.2f}\tyes\n")
    (DATA / "coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=0, sort_keys=True))

    total_tokens = sum(v["tokens"] for v in coverage.values())
    print(f"\nworks: {len(coverage)} | total Greek tokens: {total_tokens:,}",
          file=sys.stderr)
    print(f"distinct forms: {len(lex):,}", file=sys.stderr)
    bysource = defaultdict(int)
    for v in coverage.values():
        bysource[v["source"]] += 1
    print(f"works by source: {dict(bysource)}", file=sys.stderr)
    print("wrote data/public_lexicon.tsv, public_lexicon_exclusions.tsv, "
          "public_elision_stem_candidates.tsv, coverage.json", file=sys.stderr)


if __name__ == "__main__":
    main()
