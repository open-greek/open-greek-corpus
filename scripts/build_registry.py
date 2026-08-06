"""Populate the owned source-identity registry from the vendored TLG inventory
and the open-source corpora's own catalogs.

This is the real first population of source_identity (the toy seed is gone). It
reads only SHAREABLE bibliographic facts, never any licensed text. The inventory
files are vendored under data/inventory/ (bibliographic facts only: authors,
works, the keyed edition's editor/year/scheme/pd_status, per-work open coverage,
and the lowest-risk publish route). Refresh them by re-copying the inventory
outputs; this script never reaches outside the repo.

  data/inventory/work_inventory.json       authors + works + the keyed edition
  data/inventory/open_source_coverage.csv  per-work First1K / Perseus availability
  data/inventory/sourcing_map.csv          per-work best_source (lowest-risk route)

For each work it mints author.work slugs (Wikidata-ready) keyed to the inventory
and corpus by a single quiet CTS work alias (the TLG number lives inside the URN,
never as its own field), records the keyed critical edition as reference-only
(servable=False, so it can never be the default), adds the open First1K/Perseus
editions as servable WITH their exact CTS version id as the edition slug (+ CTS-URN
alias and editor/year from the corpus catalogs), sets default_edition to a servable
open edition when one exists, and stores the sourcing verdict (best_source) on the
work. A registry work the corpus serves from any other source (DFHG, OCR, CGPG,
PTA, byzantium_gr, GLAUx, SAWS, wikisource) gets its servable default minted
straight from its data/corpus_editions.json record, so every served in-registry
work resolves to a servable default edition. The TLG number is a join key only,
never a text source.

    python scripts/build_registry.py

Writes data/source_registry.json. Idempotent. Wikidata QIDs remain an enrichment
pass (no clean crosswalk yet); absent aliases are the honest default.

Whole-volume corpus keys (ocr.*, cogPG.*: Migne volumes, Walz's Rhetores
Graeci, Mansi conciliar acta, edition remainders) are re-attributed to their
real authors via the curated data/pseudo_author_attributions.json (per-volume
evidence inside), instead of the anon-ocr / anon-cogPG pseudo-authors the
slug-prefix fallback used to mint.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from source_identity import (  # noqa: E402
    Registry, IdentityError, normalize_slug, ALWAYS_QUALIFY, era_for_century)
from source_precedence import load_overrides, resolve  # noqa: E402


# Full names for the TLG Canon's genre abbreviations (a leading "2" = a second
# genre epithet; stripped before lookup). Unmapped codes fall through as-is.
GENRE_FULL = {
    "homilet": "homiletics", "hist": "history", "phil": "philosophy",
    "exeget": "exegesis", "theol": "theology", "comic": "comedy",
    "med": "medicine", "epist": "epistolography", "epigr": "epigram",
    "orat": "oratory", "comm": "commentary", "rhet": "rhetoric",
    "alchem": "alchemy", "caten": "catena", "gramm": "grammar",
    "hagiogr": "hagiography", "schol": "scholia", "encom": "encomium",
    "eccl": "ecclesiastical", "biogr": "biography", "test": "testimonia",
    "epic": "epic", "trag": "tragedy", "dialog": "dialogue", "hymn": "hymn",
    "lyr": "lyric", "lexicogr": "lexicography", "hexametr": "hexameter",
    "narr-fict": "narrative-fiction", "nat-hist": "natural-history",
    "iamb": "iambic", "relig": "religion", "eleg": "elegy",
    "math": "mathematics", "apol": "apologetics", "poem": "poetry",
    "gnom": "gnomology", "chronogr": "chronography", "hypoth": "hypothesis",
    "astron": "astronomy", "apocryph": "apocrypha", "satura": "satire",
    "astrol": "astrology", "satyr": "satyr-play", "paradox": "paradoxography",
    "geogr": "geography", "myth": "mythography", "pseudepigr": "pseudepigrapha",
    "perieg": "periegesis", "apocalyp": "apocalypse", "mus": "music",
    "metrolog": "metrology", "paroem": "paroemiography", "acta": "acta",
    "mech": "mechanics", "liturg": "liturgy", "evangel": "gospel",
    "fab": "fable", "prophet": "prophecy", "parod": "parody",
    "doxogr": "doxography", "tact": "tactics", "bucol": "bucolic",
    "onir": "oneirocritica", "physiognom": "physiognomy", "magica": "magic",
    "orac": "oracles", "invectiv": "invective", "concil": "conciliar",
    "anthol": "anthology", "polyhist": "polyhistory", "coq": "cookery",
    "mim": "mime", "jurisprud": "jurisprudence", "ignotum": "unknown",
}


def _genre_full(code: str) -> str:
    code = re.sub(r"[^a-z0-9]+", "-", code.strip().lower()).strip("-")
    code = re.sub(r"^\d+-?", "", code)              # strip a leading "2" marker
    return GENRE_FULL.get(code, code)


# --- name cleaning ---------------------------------------------------------
# The TLG Canon's author "name" and work "title" fields carry leaked beta-code
# typesetting markup and are ALL-CAPS, which otherwise pollutes both the display
# name and the immutable slug ([2ARISTOMBROTUS]2 -> "2aristombrotus-2"). Strip
# the small-caps font wrappers ([2..]2 / {2..}2 plus the bare brackets they
# leave), the * / %<n> / #<n> beta markers, and any stray "2" font-number still
# glued to the start/end of the text, then Title-Case. Run BEFORE slugging so
# the slug and the stored display name are both clean.
_BETA_PCT = re.compile(r"%\d*")
_BETA_HASH = re.compile(r"#\d+")
_TITLE_WORD = re.compile(r"[^\W\d_][\w'’]*", re.UNICODE)


def _titlecase(s: str) -> str:
    """Capitalize each word's first letter, lowercasing the rest, without
    breaking on an apostrophe (so a name keeps its interior structure)."""
    return _TITLE_WORD.sub(
        lambda m: m.group(0)[:1].upper() + m.group(0)[1:].lower(), s)


def clean_name(raw: str) -> str:
    """Strip beta-code formatting markup from a Canon name/title and Title-Case
    it. Bracket markers are removed by JOINING the text (so a bracket splitting
    one word, e.g. [ATH]ENODORUS, rejoins as Athenodorus)."""
    if not raw:
        return ""
    s = raw
    # small-caps font wrappers: a bracket/brace glued to the font-number "2".
    s = re.sub(r"[\[\]{}]2", "", s)
    # leftover bare brackets/braces.
    s = re.sub(r"[\[\]{}]", "", s)
    # other beta typesetting markers: #<n>, %<n>, and * (uppercase marker).
    s = _BETA_HASH.sub("", s)
    s = _BETA_PCT.sub("", s)
    s = s.replace("*", "")
    # ` is the Canon's numeric escape, and it reads two ways. Between two
    # alphanumerics it is a range dash - "Problemata (Lib. 1`2)" is books 1-2,
    # "Ad Principem Ineruditum (779d`782f)" is a Stephanus range. Standing before
    # a number it is only a marker that one follows - "(P. Oxy. `15.1795)". Left
    # in, it surfaced in 143 served titles as "Catecheses Ad Illuminandos 1`18".
    #
    # The slugs settle the reading rather than a guess: slugging maps any
    # non-alphanumeric to "-", so these works have long been served at
    # problemata-lib-1-2-sp, ad-principem-ineruditum-779d-782f and
    # p-oxy-15-1795. Both branches are needed to keep it that way - dropping the
    # dash branch for letter-digit boundaries would move 77 published slugs.
    s = re.sub(r"(?<=\w)`(?=\w)", "-", s)
    s = s.replace("`", "")
    # a stray font-number "2" still glued (no space) to the start/end of the
    # text: drop it. A space-separated number is a real work number
    # (e.g. "Olynthiaca 2") and is kept.
    s = re.sub(r"^2(?=[^\W\d_])", "", s)
    s = re.sub(r"(?<=[^\W\d_])2$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return _titlecase(s)


try:
    from betacode import conv as _betacode_conv      # type: ignore
except ImportError:                                  # pragma: no cover
    _betacode_conv = None

# A Canon title is TLG beta-code GREEK (not Latin) when it carries the "*" capital
# marker or an accent (/ \ =) glued to a letter - markup a Latin title never has.
# (Bare breathings ) ( are ambiguous with a Latin parenthesis, so are not a signal.)
_BETA_GREEK = re.compile(r"\*[A-Za-z()/\\=]|[A-Za-z][/\\=]|[/\\=][A-Za-z]"
                         r"|(?:^|\s)\*?(?:[AEHIOUWaehiouw]{1,2}|[Rr])[()]")


# Within a title, a whitespace token is beta-code Greek iff it carries an accent /
# grave / circumflex (/ \ =) or the * capital marker - none of which a Latin word
# ever has. So decode those tokens and leave Latin words (De, Sub, Olim, Sp.) and
# parenthetical notes untouched. This handles a pure Greek title, a Greek title
# with a trailing Latin note, and a Latin title with an embedded Greek gloss alike.
_BETA_TOKEN = re.compile(r"[/\\=*]")

# A token whose only beta marker is a BREATHING - `H(` for ἡ, `O(` for ὁ, `E)N`
# for ἐν - used to read as Latin and survive undecoded, because a trailing `)` is
# ambiguous between a smooth breathing and a closing paren. Paren depth is not
# what settles it, though, since the counterexamples carry no opening paren at
# all. Greek orthography settles it: a breathing sits on the word-INITIAL vowel,
# or on a rho, and nowhere else. So `H(` is a breathing on eta and `EU)` one on a
# diphthong, while the list marker `B)` puts it on a beta, the siglum `HILPQ)`
# five letters in, and the page reference `607A)` after digits - none of them a
# place a breathing can be. Digits are refused outright.
_BETA_BREATHING = re.compile(r"^\*?(?:[AEHIOUWaehiouw]{1,2}|[Rr])[()]")


# The other unmarked case: a preposition or conjunction elided before a vowel
# writes only an apostrophe, no accent and no breathing, so `KAT\'` and `DI\'`
# read as Latin the same way `H(` did. Here the apostrophe is genuinely
# ambiguous - Italian edition titles in this registry carry `dall\'`, `dell\'`
# and `un\'` - and no orthographic rule separates them, because both languages
# elide. What does separate them is that Greek elision of this kind is a CLOSED
# class: these are all of the words it can be. Anything else keeps its apostrophe.
# Bare `D\'` is deliberately absent even though δ\' is the commonest elision in
# Greek: elision drops the FINAL vowel, so δέ writes `D\'` and never `DE\'`, and
# `D\'` alone is indistinguishable from the French article in an edition title.
_BETA_ELIDED = {"KAT", "KAQ", "DI", "MET", "MEQ", "PAR", "EP", "EF", "AP", "AF",
                "UP", "UF", "ANT", "ANQ", "OUD", "MHD", "ALL", "TAUT"}


# A capital carries its breathing and accent BEFORE the letter and behind the
# `*` marker: `*(/ELLHSI` is Ἕλλησι. Where the Canon writes the diacritics
# without the marker the converter has nowhere to put them and leaves them
# standing, so `(/ELLHSI` comes out `(/ελλησι`. Restoring the marker is safe
# because two diacritics in a row can only be that: a single leading `(` before
# a LETTER is an ordinary parenthesis, as in `(A)NA/BLHSIS)`, and is left alone.
_BETA_CAPITAL_DIACRITICS = re.compile(r"^[()][/\\=]")


def _restore_capital_marker(tok: str) -> str:
    # Only where there is still beta-code to convert. A token whose letters are
    # already Unicode Greek has nothing for the converter to do, and the marker
    # would just hide the diacritics from _apply_stranded_diacritics below.
    if not _BETA_CAPITAL_DIACRITICS.match(tok) or not re.search(r"[A-Za-z]", tok):
        return tok
    return "*" + tok


# The same diacritics also turn up in front of a letter that is ALREADY Unicode
# Greek, because the vendored title was decoded upstream by something that could
# not place them: `(/Ελλησι` for Ἕλλησι, `(/Ωρῳ` for Ὥρῳ. There is no beta-code
# left to convert there, so they are applied as combining marks to the letter
# they belong to. Only a leading run before a Greek capital counts; anything
# before a Latin letter is still beta-code and goes the ordinary way.
_BETA_MARKS = {"(": "\u0314", ")": "\u0313", "/": "\u0301",
               "\\": "\u0300", "=": "\u0342", "|": "\u0345"}
_STRANDED = re.compile(r"^([()/\\=|]+)([\u0370-\u03ff\u1f00-\u1fff])")


def _apply_stranded_diacritics(text: str) -> str:
    """Attach beta-code diacritics left standing before an already-Greek letter."""
    def fix(m: re.Match) -> str:
        marks = "".join(_BETA_MARKS[c] for c in m.group(1) if c in _BETA_MARKS)
        return unicodedata.normalize("NFC", m.group(2) + marks)
    # Two marks minimum. A single leading `(` before Greek is an ordinary
    # opening parenthesis - `De Figuris (περὶ σχημάτων)` - and eating it would
    # put a rough breathing on the pi. Two in a row cannot be punctuation.
    # `*` may lead the run, since it is how beta-code marks a capital and the
    # letter here already is one; it carries no diacritic of its own, so the
    # composer skips it.
    return re.sub(r"(?:(?<=\s)|^)(\*?[()/\\=|]{2,})([\u0370-\u03ff\u1f00-\u1fff])",
                  fix, text)


def _is_beta_token(tok: str) -> bool:
    """True if this whitespace token is beta-code Greek rather than Latin."""
    if _BETA_TOKEN.search(tok):
        return True
    if tok.endswith("'") and tok[:-1].upper() in _BETA_ELIDED:
        return True
    return bool(_BETA_BREATHING.match(tok)) and not any(c.isdigit() for c in tok)


def _decode_beta_range(tok: str) -> str:
    """Decode a beta-code range token like `(*A_*O)` or `(A)NA/BLHSIS_BW/TORES)`.

    `_` is TLG's range separator and becomes a plain hyphen `-`. The literal
    wrapping parentheses are peeled off before conversion: fed a `)`/`(` glued to
    a vowel the betacode converter reads it as a breathing, eating the paren and
    leaving a stray diacritic (`*W)` -> `Ὠ`, dropping the close paren). Each side
    is converted on its own so a bare capital stays bare (`*O` -> `Ο`, not `Ὀ`)."""
    lead = trail = ""
    if tok.startswith("("):
        lead, tok = "(", tok[1:]
    if tok.endswith(")"):
        trail, tok = ")", tok[:-1]
    sides = tok.split("_", 1)
    return lead + "-".join(_betacode_conv.beta_to_uni(s) for s in sides) + trail


def decode_betacode_title(raw: str) -> str | None:
    """Decode the beta-code Greek tokens of a Canon work title to Unicode Greek
    (`*AI)GU/PTIOS` -> `Αἰγύπτιος`; `De Figuris (Peri\\ Sxhma/Twn)` -> `De Figuris
    (περὶ σχημάτων)`), for the stored DISPLAY title only (the slug keeps its ASCII
    form via clean_name). Returns None for a Latin-only title, or when the betacode
    library is absent, so the build degrades to the old behaviour rather than break."""
    if not raw or _betacode_conv is None or not _BETA_GREEK.search(raw):
        return None
    # strip font wrappers ([2..]2) and TLG typeset markup (#n %n `); keep [Sp.]/[Dub.].
    # ` between two alphanumerics is a range dash, as in clean_name.
    s = re.sub(r"[\[\]{}]2|[{}]|#\d+|%\d*", "", raw)
    s = re.sub(r"(?<=\w)`(?=\w)", "-", s).replace("`", "")
    toks, changed = [], False
    for tok in s.split(" "):
        if "_" in tok:                       # beta-code range: `*A_*O`, `word_word`
            toks.append(_decode_beta_range(tok))
            changed = True
        elif _is_beta_token(tok):
            toks.append(_betacode_conv.beta_to_uni(_restore_capital_marker(tok)))
            changed = True
        else:
            toks.append(_titlecase(tok))     # Latin word/note: Title-Case like clean_name
    if not changed:
        return None
    out = re.sub(r"\s+", " ", " ".join(toks)).strip()
    out = re.sub(r"\(\s+", "(", out).replace(" )", ")")   # tidy "( x )" spacing
    out = _apply_stranded_diacritics(out)
    return out or None


def _signed_century(date: str) -> int | None:
    """Signed century from a Canon author_date string: '3 B.C' -> -3,
    'A.D. 3' -> 3 (first era token wins for ranges)."""
    bc = re.search(r"(\d+)\s*B\.?\s*C", date or "")
    ad = re.search(r"A\.?\s*D\.?\s*(\d+)", date or "")
    if bc and (not ad or bc.start() < ad.start()):
        return -int(bc.group(1))
    if ad:
        return int(ad.group(1))
    return None


def _year_to_century(y: int | None) -> int | None:
    """Signed proleptic year -> signed century (-428 -> -5, 14 -> 1, no year 0)."""
    if not y:
        return None
    return (y + 99) // 100 if y > 0 else -((abs(y) + 99) // 100)


def _author_century(ids: dict) -> int | None:
    """Best signed century from an authority record's Wikidata dates: floruit,
    else the birth/death midpoint, else whichever single date is present."""
    fl, b, d = ids.get("floruit"), ids.get("birth"), ids.get("death")
    if fl is not None:
        return _year_to_century(fl)
    if b is not None and d is not None:
        return _year_to_century((b + d) // 2)
    return _year_to_century(d if d is not None else b)


INV = REPO / "data" / "inventory"
CANON = INV / "work_inventory.json"
COVERAGE = INV / "open_source_coverage.csv"
SOURCING = INV / "sourcing_map.csv"
SOURCES = REPO / "sources"
OUT = REPO / "data" / "source_registry.json"
# Optional external authority crosswalk (wikidata/viaf/gnd/isni), keyed by tlgNNNN.
# Produced by a sibling pass; the build is a graceful no-op when it is absent.
AUTHORITY = REPO / "data" / "author_authority.json"
# Optional work-level Wikidata crosswalk (works of TLG authors), keyed by the
# author's tlgNNNN -> [{qid, label, genres[], langs[]}]. Matched to Canon works
# by normalized title within the author. Graceful no-op when absent.
WORK_AUTHORITY = REPO / "data" / "work_authority.json"
# Curated author attributions for whole-volume / anthology corpus keys
# (ocr.*, cogPG.*) that the ingested-works pass would otherwise file under a
# pseudo-author minted from the slug prefix (anon-ocr, anon-cogPG). Keyed by
# the corpus_editions slug; verified against the served rows and the standard
# volume bibliography (see the file's _meta). Graceful no-op when absent.
PSEUDO_ATTRIB = REPO / "data" / "pseudo_author_attributions.json"
# OGA (Opera Graeca Adnotata v0.2.0) per-work composition dating, resolved to cog
# slugs by scripts/ingest_oga_metadata.py (version DOI 10.5281/zenodo.14206061,
# CC BY-SA 4.0). Committed, so this build applies it without the OGA clone. Absent
# file -> no dating tags (graceful no-op). The applied audit is written to
# OGA_DATING_REPORT.
OGA_DATING = REPO / "data" / "oga_dating.json"
OGA_DATING_REPORT = REPO / "data" / "oga_dating_report.json"
# Curated adjudication of the genuine (|delta| >= 2 centuries) OGA-vs-cog dating
# divergences (data/oga_dating_adjudication.json). Per work: decision a (keep cog,
# reject OGA), b (take OGA's chosen_century), or c (disputed, keep both). Absent
# file -> no adjudication (graceful no-op): every conflict falls back to the
# fill-gaps/flag-conflict behavior, which is exactly the reverse operation.
OGA_DATING_ADJUDICATION = REPO / "data" / "oga_dating_adjudication.json"


def _norm_title(s: str) -> str:
    """Fold a title for cross-source matching: drop diacritics/punctuation/case,
    a leading article, and ALL spaces, so the Canon's 'Respublica' matches
    Wikidata's Latin label 'Res publica' and 'Ilias' matches 'Ilias'."""
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "")
                if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"^(the|de|a|an|le|la|el)\s+", "", s.strip())
    return re.sub(r"\s+", "", s)

_URN_RE = re.compile(r"(tlg\d+\.tlg\d+|[a-z]+\d+\.[a-z]+\d+)\.([A-Za-z0-9-]+)$")

# Human-readable provider labels for served edition titles in the registry:
# the open TEI corpora, plus the sources whose served editions are minted
# straight from corpus_editions.json (the served-defaults pass).
PROVIDER_LABELS = {"first1k": "First1KGreek",
                   "perseus": "Perseus canonical-greekLit",
                   "galenus_verbatim": "Galenus Verbatim (Sorbonne)",
                   "dfhg": "Digital Fragmenta Historicorum Graecorum",
                   "ocr": "cog OCR",
                   "cgpg": "calfa-co Patrologia Graeca",
                   "pta": "Patristic Text Archive",
                   "byzantium_gr": "byzantium.gr",
                   "glaux": "GLAUx",
                   "saws": "Sharing Ancient Wisdoms",
                   "wikisource": "Wikisource"}


def load_open_editions() -> tuple[dict, dict]:
    """Map each work id -> list of available open editions, from the corpora's
    own catalogs, plus per-edition editor/year metadata. Returns
    (editions_by_work, meta_by_urn). Each edition: (provider, version, urn).
    """
    by_work: dict[str, list] = {}
    meta: dict[str, dict] = {}

    def add(work, provider, version, urn):
        by_work.setdefault(work, [])
        if (provider, version) not in [(p, v) for p, v, _ in by_work[work]]:
            by_work[work].append((provider, version, urn))

    # Editions are the actual XML files on disk (the ground truth F1 ingests),
    # NOT a catalog/tracking metadata file, which lags behind the tree (e.g.
    # Perseus's tracking.json omits newer -grc2 editions that exist as files).
    # Filename stem = <textgroup>.<work>.<version>, e.g. tlg0004.tlg001.perseus-grc2.
    for provider, sub in (("first1k", "first1k"), ("perseus", "perseus"),
                          ("galenus_verbatim", "galenus_verbatim")):
        root = SOURCES / sub / "data"
        if not root.exists():
            continue
        for f in root.rglob("*.xml"):
            parts = f.stem.split(".")
            if len(parts) < 3:
                continue
            work = f"{parts[0]}.{parts[1]}"
            version = ".".join(parts[2:])
            if "grc" not in version.lower():
                continue
            add(work, provider, version, f"{work}.{version}")

    # Per-edition editor/year/scheme metadata, keyed by work.version, where the
    # catalogs provide it (First1K CSV; Perseus tracking last_editor).
    csvp = SOURCES / "first1k" / "new_edition_metadata.csv"
    if csvp.exists():
        for row in csv.DictReader(csvp.open(encoding="utf-8"), delimiter="\t"):
            full = (row.get("Suggested Full URN") or "").split("greekLit:")[-1]
            if full:
                meta[full] = {
                    "editor": (row.get("Editor") or "").strip(),
                    "year": _roman_or_int(row.get("Publication Year")),
                    "scheme": (row.get("Citation Scheme") or "").strip().lower(),
                }
    trk = SOURCES / "perseus" / "canonical-greekLit.tracking.json"
    if trk.exists():
        for urn, info in json.loads(trk.read_text(encoding="utf-8")).items():
            tail = urn.split(":")[-1]
            ed = (info.get("last_editor") or "").strip()
            if tail.count(".") >= 2 and ed and tail not in meta:
                meta[tail] = {"editor": ed, "year": None, "scheme": ""}
    return by_work, meta


def _roman_or_int(s: str):
    """Publication years in the metadata are sometimes mangled roman (XDCCC...);
    take a plain 4-digit year if present, else None (honest)."""
    s = (s or "").strip()
    m = re.search(r"\b(1[0-9]{3}|20[0-2][0-9])\b", s)
    return int(m.group(1)) if m else None


def _first1k_catalog_names() -> dict:
    """work_cts -> (group_name, work_name) from the First1K catalog, for the
    open works the TLG canon doesn't list."""
    out = {}
    cat = SOURCES / "first1k" / "catalog.json"
    if cat.exists():
        for e in json.loads(cat.read_text(encoding="utf-8")).get("catalog", []):
            urn = e.get("urn", "")
            if ":greekLit:" not in urn:
                continue
            tail = urn.split(":")[-1]
            m = _URN_RE.match(tail)
            if m:
                out.setdefault(m.group(1),
                               (e.get("group_name", ""), e.get("work_name", "")))
    return out


def _author_qualifiers(a: dict) -> list:
    """Meaningful homonym disambiguators for an author, in priority order:
    epithet as a full genre word (Trag. -> tragedy), then geo/toponym, then the
    floruit century. Used instead of a bare numeric suffix."""
    out = []
    for ep in (a.get("epithet") or []):
        q = _genre_full(normalize_slug(clean_name(ep)))
        if q and q not in out:
            out.append(q)
    for g in (a.get("geo") or []):
        q = normalize_slug(clean_name(g))
        if q and q not in out:
            out.append(q)
    c = _signed_century((a.get("date") or [""])[0])
    if c:
        out.append(f"{abs(c)}bce" if c < 0 else f"{c}ce")
    return out


def _plan_author_slugs(authors: dict) -> dict:
    """anum -> final author slug. A unique name keeps the bare slug; homonyms
    (and ALWAYS_QUALIFY names) are qualified by a meaningful epithet/geo/century
    trait. A numeric suffix is the last resort, only when no trait separates two
    same-named authors. Deterministic (sorted), and the result is collision-free."""
    base = {}
    for anum, a in authors.items():
        bs = normalize_slug(clean_name(a.get("name", "")))
        if bs:
            base[anum] = bs
    groups: dict = {}
    for anum, bs in base.items():
        groups.setdefault(bs, []).append(anum)
    final, used = {}, set()
    for bs in sorted(groups):
        anums = sorted(groups[bs])
        if len(anums) == 1 and bs.split("-")[0] not in ALWAYS_QUALIFY:
            final[anums[0]] = bs
            used.add(bs)
            continue
        for anum in anums:                       # homonyms -> qualify each
            slug = next((f"{bs}-{q}" for q in _author_qualifiers(authors[anum])
                         if f"{bs}-{q}" not in used), None)
            if slug is None:                     # no distinguishing trait
                n = 2
                while f"{bs}-{n}" in used:
                    n += 1
                slug = f"{bs}-{n}"
            used.add(slug)
            final[anum] = slug
    return final


def _edition_slug(work: dict) -> str:
    """A stable slug for the TLG-keyed reference edition: editor surname + year."""
    ed = normalize_slug((work.get("editor") or "").split(",")[0]) or "ed"
    yr = work.get("pub_year")
    return f"{ed}-{yr}" if yr else ed


def _truthy(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def _set_century(reg: Registry, slug: str, century: int) -> None:
    """Replace a work's century/era tags with a single chosen century (+ its era).
    Used only to APPLY an adjudicated (b) decision; add_tag re-sorts the tag list."""
    w = reg.works[slug]
    w.tags = [t for t in w.tags
              if not (t.startswith("century:") or t.startswith("era:"))]
    reg.add_tag(slug, "century", century)
    reg.add_tag(slug, "era", era_for_century(century))


def apply_oga_dating(reg: Registry) -> None:
    """FILL missing century/era tags from OGA's per-work dating, and resolve a
    per-work disagreement via the curated adjudication file (or flag it when
    unadjudicated). Reads the committed data/oga_dating.json (produced by
    scripts/ingest_oga_metadata.py from the pinned OGA chronology) and the curated
    data/oga_dating_adjudication.json; writes the audit to
    data/oga_dating_report.json.

    Policy (task + Multi-Source Data rule): fill gaps, never clobber a tag on an
    UNADJUDICATED conflict (keep the existing century, record both readings). For a
    conflict the adjudication file rules on, apply the decision: (a) keep cog and
    mark the OGA reading adjudicated-rejected (no longer an open conflict); (b) set
    century/era to OGA's chosen_century; (c) keep cog but record both readings as
    adjudicated=disputed. Removing the adjudication file restores the old
    flag-conflict behavior (reversible); removing data/oga_dating.json drops all
    OGA dating (fully reverse)."""
    if not OGA_DATING.exists():
        print("  ! data/oga_dating.json absent; no OGA dating applied "
              "(run scripts/ingest_oga_metadata.py)", file=sys.stderr)
        return
    od = json.loads(OGA_DATING.read_text(encoding="utf-8"))
    # curated adjudication of the |delta| >= 2 conflicts, keyed by cog slug. Absent
    # file -> empty -> every conflict is flagged (the reverse operation).
    adj = {}
    if OGA_DATING_ADJUDICATION.exists():
        adj = json.loads(OGA_DATING_ADJUDICATION.read_text(
            encoding="utf-8")).get("decisions", {})
    # index registry works by their CTS-URN tail (the OGA key), churn-proof.
    by_cts = {}
    for slug, w in reg.works.items():
        cts = w.aliases.get("cts")
        if cts:
            by_cts.setdefault(cts.split(":")[-1], slug)

    filled, agreed, conflicts, no_home, adjudicated = [], [], [], [], []
    adj_seen = set()
    for urn, e in sorted(od.get("works", {}).items()):
        c = e.get("century")
        if c is None:
            continue
        # match by the registry work's own CTS alias first (survives slug
        # renames), else by the slug the ingester resolved (covers pta / renumbered
        # works whose registry alias is a synthetic slug-form CTS).
        slug = by_cts.get(urn)
        if slug is None:
            cog = e.get("cog_slug")
            slug = cog if cog in reg.works else None
        if slug is None:
            no_home.append(urn)
            continue
        existing = sorted(int(t.split(":")[1]) for t in reg.works[slug].tags
                          if t.startswith("century:"))
        if not existing:
            reg.add_tag(slug, "century", c)
            reg.add_tag(slug, "era", era_for_century(c))
            filled.append({"urn": urn, "slug": slug, "century": c,
                           "era": era_for_century(c)})
        elif c in existing:
            agreed.append(slug)
        elif slug in adj:
            # a curated verdict on this genuine divergence; apply it and record
            # the adjudication rather than leaving it an open conflict.
            d = adj[slug]
            adj_seen.add(slug)
            dec = d["decision"]
            rec = {"urn": urn, "slug": slug, "decision": dec,
                   "cog_century": existing,
                   "oga_century": c, "oga_era": era_for_century(c),
                   "oga_date_label": e.get("date_label"),
                   "oga_estimated": e.get("estimated_work_date"),
                   "delta": min(abs(c - x) for x in existing),
                   "basis": d.get("basis", "")}
            if dec == "a":                       # cog correct, OGA rejected
                rec["applied"] = "cog"
                rec["registry_century"] = existing
                rec["oga_status"] = "adjudicated-rejected"
            elif dec == "b":                     # OGA correct, cog updated
                chosen = d["chosen_century"]
                _set_century(reg, slug, chosen)
                rec["applied"] = "oga"
                rec["chosen_century"] = chosen
                rec["chosen_era"] = era_for_century(chosen)
                rec["registry_century"] = [chosen]
                rec["cog_status"] = "adjudicated-superseded"
            elif dec == "c":                     # disputed, keep both readings
                rec["applied"] = "cog"
                rec["adjudicated"] = "disputed"
                rec["readings"] = [
                    {"century": existing, "era": era_for_century(existing[0]),
                     "source": "cog"},
                    {"century": c, "era": era_for_century(c), "source": "oga"}]
                rec["registry_century"] = existing
            else:
                raise ValueError(
                    f"oga_dating_adjudication: unknown decision {dec!r} for {slug}")
            adjudicated.append(rec)
        else:
            # unadjudicated: keep the existing tag; record both readings for review.
            # Most of these are an author-floruit century vs a per-work composition
            # century that straddle a century boundary (|delta| == 1).
            conflicts.append({"urn": urn, "slug": slug,
                              "existing_century": existing,
                              "oga_century": c, "oga_era": era_for_century(c),
                              "oga_date_label": e.get("date_label"),
                              "oga_estimated": e.get("estimated_work_date"),
                              "delta": min(abs(c - x) for x in existing)})
    # a curated decision whose slug was not seen as a live conflict is stale (a
    # slug rename or an upstream date change); surface it, don't silently drop it.
    stale = sorted(set(adj) - adj_seen)
    if stale:
        print(f"  ! {len(stale)} adjudication entr{'y' if len(stale)==1 else 'ies'} "
              f"did not match a live conflict (stale slug or changed OGA date): "
              f"{stale}", file=sys.stderr)
    from collections import Counter
    delta_hist = dict(sorted(Counter(x["delta"] for x in conflicts).items()))
    adj_counts = dict(sorted(Counter(x["decision"] for x in adjudicated).items()))
    report = {
        "_meta": {
            "description": "Audit of OGA (Opera Graeca Adnotata v0.2.0) dating "
                           "applied to source_registry.json century/era tags. "
                           "`filled` = a work that had no century tag and got the "
                           "OGA one; `conflicts` = an UNADJUDICATED disagreement "
                           "(existing tag kept, both readings recorded, NOT "
                           "overwritten); `adjudicated` = a genuine (|delta| >= 2) "
                           "divergence resolved by the curated "
                           "data/oga_dating_adjudication.json (decision a = cog "
                           "kept / OGA rejected, b = cog updated to OGA, c = "
                           "disputed / both readings kept). Reverse by re-running "
                           "build_registry.py after removing "
                           "data/oga_dating_adjudication.json (restores the flag) "
                           "or data/oga_dating.json (drops OGA dating).",
            "source": "Opera Graeca Adnotata v0.2.0",
            "version_doi": "10.5281/zenodo.14206061",
            "license": "CC-BY-SA-4.0",
            "generated_by": "scripts/build_registry.py",
            "adjudication": "data/oga_dating_adjudication.json",
            "policy": "fill gaps, never clobber; adjudicate genuine divergences, "
                      "flag the rest (Multi-Source Data)",
            "counts": {
                "filled": len(filled), "agreed": len(agreed),
                "conflicts": len(conflicts),
                "adjudicated": len(adjudicated),
                "adjudicated_by_decision": adj_counts,
                "resolved_no_registry_home": len(no_home),
                "conflict_delta_century_histogram": delta_hist,
            },
        },
        "filled": filled,
        "adjudicated": adjudicated,
        "conflicts": conflicts,
        "resolved_no_registry_home": sorted(no_home),
    }
    OGA_DATING_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  + OGA dating: {len(filled)} filled, {len(agreed)} agreed, "
          f"{len(adjudicated)} adjudicated {adj_counts}, {len(conflicts)} "
          f"conflicts flagged, {len(no_home)} resolved w/o a registry home "
          f"(audit: data/oga_dating_report.json)", file=sys.stderr)


def build() -> Registry:
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    authors = canon["authors"]                      # {"0001": {...}}
    works = canon["works"]                           # [ {...}, ... ]

    coverage = {}
    if COVERAGE.exists():
        for row in csv.DictReader(COVERAGE.open(encoding="utf-8")):
            coverage[(row["tlg_id"], row["work_id"])] = row
    # per-work best_source, with cog's source-precedence overrides applied so
    # the registry verdict matches the coverage report (byzantium_gr / CGPG wins).
    overrides = load_overrides()
    sourcing = {}
    if SOURCING.exists():
        for row in csv.DictReader(SOURCING.open(encoding="utf-8")):
            eff, _ = resolve(row["tlg_id"], row["work_id"],
                             row.get("best_source", ""), overrides)
            sourcing[(row["tlg_id"], row["work_id"])] = eff
    # external author authority ids (wikidata/viaf/gnd/isni), keyed by tlgNNNN.
    # Absent file -> empty map -> no aliases added (the build still succeeds).
    authority = {}
    if AUTHORITY.exists():
        authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    # work-level Wikidata crosswalk: author tlg -> {normalized title -> [recs]}
    work_auth = {}
    if WORK_AUTHORITY.exists():
        for tlg, recs in json.loads(WORK_AUTHORITY.read_text(encoding="utf-8")).items():
            by_title = {}
            for rc in recs:
                # index under every label form (English + Latin + Greek) plus
                # the altLabel variants (the Latinized scholarly titles often
                # live only there); the Latin label is the Canon's title form.
                # Dedup a rec per norm key.
                forms = {_norm_title(rc[k]) for k in ("label", "la", "grc", "el")
                         if rc.get(k)}
                forms |= {_norm_title(a) for a in rc.get("alts", [])}
                forms.discard("")
                for nt in forms:
                    lst = by_title.setdefault(nt, [])
                    if rc["qid"] not in {x["qid"] for x in lst}:
                        lst.append(rc)
            work_auth[tlg] = by_title
    # curated re-attributions for ocr.* / cogPG.* whole-volume corpus keys:
    # {corpus slug -> work record} + {author slug -> author record}. Absent
    # file -> empty maps -> the old anon-<prefix> fallback (build still succeeds).
    attrib_authors: dict = {}
    attrib_works: dict = {}
    if PSEUDO_ATTRIB.exists():
        _att = json.loads(PSEUDO_ATTRIB.read_text(encoding="utf-8"))
        attrib_authors = _att.get("authors", {})
        attrib_works = _att.get("works", {})
    open_eds, ed_meta = load_open_editions()
    # which edition F1 actually ingested per work (the dedup winner), so the
    # default points at the text we really have in hand, not just the first
    # version the catalog lists.
    ingested = {}
    served_src = {}          # work key -> corpus source actually serving it
    corpus_records = {}      # served slug -> full corpus record (defaults pass)
    ce = REPO / "data" / "corpus_editions.json"
    if ce.exists():
        # corpus_editions is now keyed by slug; recover the tlg-stem keying this
        # function's downstream logic expects from each work's cts alias (non-tlg
        # works - cogByz/cogPG/ocr - keep their native key).
        for slug, info in json.loads(ce.read_text(encoding="utf-8")).items():
            cts = info.get("cts")
            work_cts = cts.split("greekLit:")[-1] if cts else slug
            ingested[work_cts] = info.get("edition")
            served_src[work_cts] = info.get("source")
            corpus_records[slug] = info

    reg = Registry()

    # --- authors ---------------------------------------------------------
    slug_by_anum: dict[str, str] = {}
    wd_century_by_anum: dict[str, int] = {}   # precise century from Wikidata dates
    n_authority = 0
    planned_slugs = _plan_author_slugs(authors)   # epithet/geo/century disambiguated
    for anum, a in authors.items():
        name = clean_name(a["name"])              # strip beta markup, Title-Case
        slug = planned_slugs.get(anum)
        if not slug:
            continue
        s = reg.mint_author(name, slug=slug)
        slug_by_anum[anum] = s
        # attach external authority ids as aliases when we have them. tlg is
        # deliberately NOT added; mint_author is idempotent and unions aliases.
        ids = authority.get(a.get("tlg_id", ""))
        if ids:
            al = {k: ids[k] for k in ("wikidata", "viaf", "gnd", "isni")
                  if ids.get(k)}
            if al:
                reg.mint_author(name, slug=s, aliases=al)
                n_authority += 1
            wc = _author_century(ids)
            if wc is not None:
                wd_century_by_anum[anum] = wc

    # --- works + editions ------------------------------------------------
    if _betacode_conv is None:
        print("  ! betacode not installed; beta-code Greek titles left undecoded "
              "(pip install betacode)", file=sys.stderr)
    n_work_qid = 0
    wd_work_proposals: dict[str, dict] = {}   # work_slug -> Wikidata work record
    for w in works:
        anum = w["tlg_id"][3:]                        # tlg0001 -> 0001
        author_slug = slug_by_anum.get(anum)
        raw_title = w.get("title") or ""
        title = clean_name(raw_title)                  # ASCII: drives the slug + QID matching
        display = decode_betacode_title(raw_title) or title   # Greek display for beta-code titles
        if not author_slug or not title:
            continue
        ck = (w["tlg_id"], w["work_id"])
        cts = f"{w['tlg_id']}.tlg{w['work_id']}"
        scheme = ".".join(s.lower() for s in (w.get("cit_scheme") or []))
        # same-author works that share a normalized title get a numeric suffix
        # (permanent, never reused), keyed off the distinct TLG work id.
        base_ws = f"{author_slug}.{normalize_slug(title)}"
        # the CTS work id is the single join key (the TLG number lives inside it).
        ws, n = base_ws, 1
        while True:
            try:
                work_slug = reg.mint_work(
                    author_slug, display, slug=ws,
                    aliases={"cts": f"urn:cts:greekLit:{cts}"})
                break
            except IdentityError:
                n += 1
                ws = f"{base_ws}-{n}"
        reg.works[work_slug].best_source = sourcing.get(ck, "")

        # tags: genre from the Canon genres; century + era from the author date
        for g in (w.get("genres") or []):
            reg.add_tag(work_slug, "genre", _genre_full(g))
        # century: prefer the precise Wikidata date over the Canon's coarse date
        c = wd_century_by_anum.get(anum) or _signed_century(w.get("author_date", ""))
        if c:
            reg.add_tag(work_slug, "century", c)
            reg.add_tag(work_slug, "era", era_for_century(c))
        # work-level Wikidata: propose an UNAMBIGUOUS normalized-title match under
        # this author. Attached after the loop, and only if MUTUALLY unique (a QID
        # claimed by several works is dropped from all) so one item never becomes
        # the identity of multiple works.
        cands = work_auth.get(w["tlg_id"], {}).get(_norm_title(title), [])
        if len(cands) == 1:
            wd_work_proposals[work_slug] = cands[0]

        # the keyed critical edition: reference-only, never servable / never default
        reg.mint_edition(
            work_slug, _edition_slug(w),
            w.get("edition_title") or "keyed critical edition",
            provider="tlg-e-reference", scheme=scheme,
            editor=w.get("editor", ""), year=w.get("pub_year"),
            servable=False)

        # open editions (servable), keyed by their exact CTS version id. Gate on
        # the inventory's coverage flags (consistent with the sourcing map), take
        # the version + editor/year from the corpus catalogs. first1k editions
        # are preferred as the default, then perseus. galenus_verbatim editions
        # are gated on the corpus actually serving the work from that source
        # (corpus_editions.json), the sourcing map having no column for them.
        cov = coverage.get(ck, {})
        avail = open_eds.get(cts, [])
        order = {"first1k": 0, "perseus": 1, "galenus_verbatim": 2}
        avail = sorted(avail, key=lambda x: (order.get(x[0], 9), x[1]))
        n_cts = 0
        seen_versions: set[str] = set()
        for provider, version, urn in avail:
            if provider == "first1k" and not _truthy(cov.get("first1kgreek", "")):
                continue
            if provider == "perseus" and not _truthy(cov.get("perseus", "")):
                continue
            if provider == "galenus_verbatim" and served_src.get(work_slug) != "galenus_verbatim":
                continue
            if version in seen_versions:
                continue          # same version id vendored by a second source
            seen_versions.add(version)
            m = ed_meta.get(urn, {})
            label = PROVIDER_LABELS.get(provider, provider)
            reg.mint_edition(
                work_slug, version, f"{label} ({version})",
                provider=provider, scheme=m.get("scheme") or scheme,
                editor=m.get("editor", ""), year=m.get("year"),
                servable=True, license="CC-BY-SA-4.0",
                aliases={"cts": f"urn:cts:greekLit:{urn}"},
                make_default=(n_cts == 0))
            n_cts += 1
        # coverage says open but the catalog had no parseable grc version: keep a
        # provider-named servable edition so the work still resolves as open.
        if not n_cts and _truthy(cov.get("first1kgreek", "")):
            reg.mint_edition(work_slug, "first1k", "First1KGreek",
                             provider="first1k", scheme=scheme, servable=True,
                             license="CC-BY-SA-4.0", make_default=True)
        elif not n_cts and _truthy(cov.get("perseus", "")):
            reg.mint_edition(work_slug, "perseus", "Perseus canonical-greekLit",
                             provider="perseus", scheme=scheme, servable=True,
                             license="CC-BY-SA-4.0", make_default=True)
        # point the default at the edition F1 actually ingested, when known
        win = ingested.get(cts)
        if win and f"{work_slug}.{win}" in reg.works[work_slug].editions:
            reg.works[work_slug].default_edition = f"{work_slug}.{win}"

    # --- ingested open works not matched to a canon work ----------------
    # Two kinds: First1K's non-TLG textgroups (ggm/ogl/stoa/...), and works the
    # corpora number by CTS where TLG-E numbers them differently (the Euripides
    # 034-052 vs CTS 001-019 remap class). Both are served, so they belong in the
    # registry. Mint under the canon author when the textgroup is known, else a
    # catalog/anon author; key by CTS (NOT tlg, to avoid implying a canon match).
    # A later work-number remap pass should reconcile the CTS-numbered ones with
    # their canon twins.
    by_key = set()
    for w in reg.works.values():
        if w.aliases.get("tlg"):
            by_key.add(w.aliases["tlg"])
        if w.aliases.get("cts"):
            by_key.add(w.aliases["cts"].split("greekLit:")[-1])
    names = _first1k_catalog_names()
    n_added = 0
    n_attributed = 0
    for work_cts, win in sorted(ingested.items()):
        if work_cts in by_key or work_cts.startswith("cogByz."):
            continue  # cogByz.* are minted by the Byzantine pass below
        tg = work_cts.split(".")[0]
        group, title = names.get(work_cts, ("", ""))
        anum = tg[3:] if tg.startswith("tlg") else ""
        author_slug = slug_by_anum.get(anum)
        att = attrib_works.get(work_cts)
        if att:
            # curated attribution: file the volume under its real author (reuse
            # the canon author entry when present; mint_author is idempotent and
            # unions aliases), or under a documented collective label. Never the
            # anon-<prefix> pseudo-author.
            a_slug = att["author"]
            a_rec = attrib_authors.get(a_slug, {})
            a_name = (reg.authors[a_slug].name if a_slug in reg.authors
                      else a_rec.get("name", a_slug))
            author_slug = reg.mint_author(a_name, slug=a_slug,
                                          aliases=a_rec.get("aliases") or {})
            title = att["title"]
            n_attributed += 1
        elif not author_slug:
            a_base = normalize_slug(group) or f"anon-{tg}"
            try:
                author_slug = reg.mint_author(group or a_base, slug=a_base)
            except IdentityError:
                author_slug = reg.mint_author(group or a_base, slug=f"{a_base}-{tg}")
        # curated whole-volume works are keyed by their SERVED corpus key: the
        # reader resolves works[<corpus_editions slug>] directly (registry ->
        # crosswalk -> slug-prefix fallback), so a pretty re-slug would land the
        # whole set back on the pseudo-author. att["slug"] stays as documentation.
        base_ws = (work_cts if att else None) or \
            f"{author_slug}.{normalize_slug(title) or work_cts.replace('.', '-')}"
        # a fresh slug (never merge into a canon twin that shares a title); the
        # distinct CTS work id keeps them apart, remap reconciles them later.
        ws, n = base_ws, 1
        while ws in reg.works:
            n += 1
            ws = f"{base_ws}-{n}"
        work_slug = reg.mint_work(author_slug, title or work_cts, slug=ws,
                                  aliases={"cts": f"urn:cts:greekLit:{work_cts}"})
        reg.works[work_slug].best_source = "open_corpus"
        if att:
            att_tags = att.get("tags") or {}
            c = att_tags.get("century")
            if c:
                reg.add_tag(work_slug, "century", c)
                reg.add_tag(work_slug, "era", era_for_century(c))
            for g in att_tags.get("genre", []):
                reg.add_tag(work_slug, "genre", g)
        for provider, version, urn in open_eds.get(work_cts, []):
            label = PROVIDER_LABELS.get(provider, provider)
            reg.mint_edition(work_slug, version, f"{label} ({version})",
                             provider=provider, scheme="", servable=True,
                             license="CC-BY-SA-4.0",
                             aliases={"cts": f"urn:cts:greekLit:{urn}"},
                             make_default=(version == win))
        n_added += 1
    print(f"  + {n_added} ingested works not in the canon numbering "
          f"(non-TLG + CTS-renumbered; remap TODO)", file=sys.stderr)
    print(f"  + {n_attributed} whole-volume corpus keys re-attributed via "
          f"data/pseudo_author_attributions.json (no anon-ocr/anon-cogPG)",
          file=sys.stderr)

    # --- Byzantine vernacular works (merged-in `byzantine_vernacular` source) -------------
    # Open PD/CC-BY-SA medieval and early-modern vernacular verse, no TLG/CTS id;
    # cog-native key. Key each work by its SERVED corpus slug (cogByz.<stem>), NOT
    # by author.title: the id ledger (build_id_registry) and the reader-facing
    # manifest (build_work_index) resolve a served work-unit by its corpus-file
    # slug, so an author.title key leaves all of them unresolved under a junk
    # "cogByz" pseudo-author with humanized underscore titles. This mirrors how
    # the whole-volume ocr.*/cogPG.* corpus keys stay their own work slug (with an
    # explicit `author`), which is what author_slug_for reads.
    bw = REPO / "data" / "byzantine_vernacular_works.json"
    n_byz = 0
    if bw.exists():
        for w in json.loads(bw.read_text(encoding="utf-8")):
            author_slug = reg.mint_author(w["author_name"], slug=w["author_slug"])
            work_slug = reg.mint_work(
                author_slug, w["title"], slug=w["key"],
                aliases={"cts": f"urn:cts:cogGreek:{w['key']}"})
            reg.works[work_slug].best_source = "open_corpus"
            licl = w["license"].lower()
            lic = "CC0/PD" if (licl.startswith("public domain")
                               and "cc by" not in licl) else "CC-BY-SA-4.0"
            reg.mint_edition(work_slug, w["edition"], w["title_el"] or w["title"],
                             provider="byzantine_vernacular", scheme=w.get("scheme", "line"),
                             servable=True, license=lic, make_default=True)
            for dim, val in w.get("facets", []):
                reg.add_tag(work_slug, dim, val)
            cents = [v for d, v in w.get("facets", []) if d == "century"]
            reg.add_tag(work_slug, "era",
                        era_for_century(cents[0]) if cents else "byzantine")
            n_byz += 1
    print(f"  + {n_byz} Byzantine vernacular works (byzantine_vernacular)", file=sys.stderr)

    # --- servable defaults for the rest of the served set ----------------
    # The passes above mint servable editions only for First1K / Perseus /
    # galenus_verbatim / byzantine_vernacular texts, so a registry work served
    # from any other source (DFHG, OCR, CGPG, PTA, byzantium_gr, GLAUx, SAWS,
    # wikisource) still carries only its reference-only TLG edition and no
    # default_edition at all. Mint the served edition from the corpus record
    # itself: edition slug from its `edition`, provider from its `source`,
    # license as recorded, servable, and made the work's default. Guards: a
    # work whose default_edition is already set keeps it untouched (never
    # demoted or replaced), and nothing is minted for a work the corpus does
    # not serve. The scheme is left empty here; the inference pass below fills
    # it (marked scheme_inferred) when the served loci classify
    # logical-numeric. Deterministic (sorted) and idempotent like the rest.
    n_corpus_default = 0
    corpus_default_by_source: dict[str, int] = {}
    for slug in sorted(corpus_records):
        w = reg.works.get(slug)
        if w is None:
            continue                     # served, but not a registry work
        if w.default_edition is not None:
            continue                     # existing default: hands off
        info = corpus_records[slug]
        ed_slug = info.get("edition") or ""
        provider = info.get("source") or ""
        if not ed_slug:
            continue
        full = f"{slug}.{ed_slug}"
        if full in w.editions and not w.editions[full].servable:
            # the served edition slug collides with a reference-only record;
            # promoting one would break the servable-default invariant.
            print(f"  ! {full}: served edition slug collides with a "
                  f"reference-only edition; no default minted", file=sys.stderr)
            continue
        label = PROVIDER_LABELS.get(provider, provider)
        reg.mint_edition(slug, ed_slug, f"{label} ({ed_slug})",
                         provider=provider, scheme="", servable=True,
                         license=info.get("license", ""), make_default=True)
        n_corpus_default += 1
        corpus_default_by_source[provider] = \
            corpus_default_by_source.get(provider, 0) + 1
    print(f"  + {n_corpus_default} served works gained a servable default "
          f"edition minted from corpus_editions.json ("
          + ", ".join(f"{k} {n}" for k, n in
                      sorted(corpus_default_by_source.items())) + ")",
          file=sys.stderr)

    # apply work-level Wikidata matches that are MUTUALLY unique (a QID claimed by
    # more than one work is dropped from all, so one item is never two works).
    qid_use: dict[str, int] = {}
    for rc in wd_work_proposals.values():
        qid_use[rc["qid"]] = qid_use.get(rc["qid"], 0) + 1
    for work_slug, rc in wd_work_proposals.items():
        if qid_use[rc["qid"]] != 1:
            continue
        wk = reg.works[work_slug]
        reg.mint_work(wk.author, wk.title, slug=work_slug,
                      aliases={"wikidata": rc["qid"]})
        for g in rc.get("genres", []):
            reg.add_tag(work_slug, "genre", g)
        for la in rc.get("langs", []):
            reg.add_tag(work_slug, "language", la)
        n_work_qid += 1
    print(f"  + {n_work_qid} works matched to a Wikidata QID (work-level)",
          file=sys.stderr)

    # OGA per-work composition dating: fill missing century/era tags, flag
    # conflicts. Runs last, after every work (canon + ingested + Byzantine) is
    # minted, so it can tag any of them.
    apply_oga_dating(reg)

    # Served-scheme inference (scripts/infer_served_schemes.py): a served work
    # whose default edition declares NO scheme but whose actual loci are
    # dominantly logical numerics gets the inferred scheme (canon cit_scheme
    # when its depth matches, else generic ref/sub labels), marked inferred.
    # Fills only EMPTY schemes; a declared scheme, physical or logical, wins.
    inf_path = REPO / "data" / "served_scheme_inference.json"
    n_inferred = 0
    if inf_path.exists():
        inferred = json.loads(inf_path.read_text(encoding="utf-8"))["works"]
        for ws, w in reg.works.items():
            de = w.default_edition
            ed = w.editions.get(de) if de else None
            rec = inferred.get(ws)
            if (ed is not None and not (ed.scheme or "").strip()
                    and rec and rec.get("class") == "logical-numeric"):
                ed.scheme = rec["scheme"]
                ed.scheme_inferred = True
                n_inferred += 1
        print(f"  + {n_inferred} served default editions gained an inferred "
              f"scheme (data/served_scheme_inference.json)", file=sys.stderr)

    print(f"  + {n_authority} authors gained external authority aliases "
          f"(wikidata/viaf/gnd/isni){' [author_authority.json absent]' if not authority else ''}",
          file=sys.stderr)
    # every pass that mints a default counts here (canon open editions, ingested
    # non-canon works, Byzantine vernacular, and the corpus-served defaults), so
    # this is the true works-with-a-servable-default figure.
    n_servable = sum(1 for w in reg.works.values()
                     if w.default_edition
                     and w.editions[w.default_edition].servable)
    print(f"authors {len(reg.authors)}  works {len(reg.works)}  "
          f"editions {sum(len(w.editions) for w in reg.works.values())}  "
          f"servable-default {n_servable} "
          f"({100*n_servable/max(1,len(reg.works)):.0f}%)", file=sys.stderr)
    return reg


if __name__ == "__main__":
    if not CANON.exists():
        sys.exit(f"inventory not found: {CANON} (vendor it into data/inventory/)")
    reg = build()
    OUT.parent.mkdir(exist_ok=True)
    reg.save(OUT)
    print(f"wrote {OUT}")
