"""Source identity: owned, edition-aware ids for authors, works, and editions.

The model separates three FRBR-style levels so that "which work" never
implies "which edition" the way a bare TLG id does:

    author    homer
    work      homer.iliad                 (= author.work)
    edition   homer.iliad.west-1998       (= work.edition)

The dotted slug is the identity and it is the only thing we compute on.
Every external identifier (Wikidata QID, VIAF, GND, TLG, CTS, Trismegistos,
LDAB, HathiTrust, ...) is a swappable cross-reference hanging off a level in
an ``aliases`` map, never load-bearing. A QID is preferred for display and is
a high-confidence dedup signal when present, but coverage is uneven so the
slug, not the QID, is the key.

Two invariants make references trustworthy:

  * Identity is immutable and append-only. A minted slug never changes; if a
    rename is unavoidable the old slug survives as an alias. Numeric
    disambiguation suffixes (``-2``) are permanent and never reused.
  * Display / resolution is mutable policy. A work's ``default_edition`` (used
    to render and resolve bare citations) can change anytime because every
    stored locus always carries its own real edition slug, so changing the
    default rewrites nothing.

Dedup resolves an incoming record to a slug by Wikidata QID first
(authoritative), then the union of any other aliases, then a normalized
name fallback that is flagged for human confirmation.

Pure stdlib: no torch, no DB, no network. The registry is a plain JSON file.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Alias namespaces, ordered by how much we stress them (display + dedup).
# tlg/cts are kept as quiet aliases: recorded, never surfaced or relied on.
# --------------------------------------------------------------------------
AUTHOR_ALIAS_NS = ("wikidata", "viaf", "gnd", "isni", "tlg", "cts")
WORK_ALIAS_NS = ("wikidata", "viaf", "tlg", "cts", "perseus")
EDITION_ALIAS_NS = ("cts", "hathitrust", "trismegistos", "ldab", "doi", "isbn")

# An edition's ``provider`` is either "print" or one of the digital corpora we
# ingest a per-work text/annotation from. Naming matches the attestation
# builders (build_*_freq.py / build_*_attestation.py) so an edition slug like
# ``homer.iliad.glaux`` means "GLAUx's text of the Iliad".
CORPUS_PROVIDERS = ("glaux", "diorisis", "first1k", "pta", "pg", "byzantine_vernacular")

# --------------------------------------------------------------------------
# Tags: faceted ``dimension:value`` labels on a work. A controlled set of
# dimensions (extend deliberately), open values per dimension. ``century`` is a
# SIGNED INTEGER (century:-1 = 1st c. BCE, century:14 = 14th c. CE) so tags sort
# and compare numerically and match the -8 = 8th-c.-BCE convention used elsewhere;
# render_century() turns it back into "1st c. BCE" for display. Other dimensions take
# a lowercase-hyphen value (era:byzantine, register:vernacular, genre:epic,
# dialect:cretan, language:medieval-greek).
# --------------------------------------------------------------------------
TAG_DIMENSIONS = frozenset({
    "era", "century", "register", "genre", "dialect", "language",
})


def canon_tag(dim: str, val) -> str:
    """Canonical ``dimension:value`` tag string. Validates the dimension,
    coerces century to a signed int, lowercase-hyphenates other values."""
    dim = dim.strip().lower()
    if dim not in TAG_DIMENSIONS:
        raise IdentityError(f"unknown tag dimension {dim!r} (allowed: "
                            f"{sorted(TAG_DIMENSIONS)})")
    if dim == "century":
        c = int(val)
        if c == 0:
            raise IdentityError("century has no year/century 0")
        return f"century:{c}"
    v = re.sub(r"[^a-z0-9]+", "-", str(val).strip().lower()).strip("-")
    if not v:
        raise IdentityError(f"empty value for tag {dim!r}")
    return f"{dim}:{v}"


def render_century(c: int) -> str:
    """century:-1 -> '1st c. BCE', century:14 -> '14th c. CE'."""
    n = abs(c)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf} c. {'BCE' if c < 0 else 'CE'}"


# Coarse era from a signed century, when not tagged explicitly.
def era_for_century(c: int) -> str:
    if c <= -6:
        return "archaic"
    if c <= -4:
        return "classical"
    if c <= -1:
        return "hellenistic"
    if c <= 3:
        return "imperial"
    if c <= 6:
        return "late-antique"
    if c <= 15:
        return "byzantine"
    if c <= 18:
        return "early-modern"
    return "modern"


# Namespaces that authoritatively pin identity when two records share a value.
AUTHORITATIVE_NS = ("wikidata",)

# How a locus learned which edition it belongs to (most to least certain).
ASSERTED = "asserted"               # source named or clearly used the edition
INFERRED_SCHEME = "inferred-scheme"  # citation scheme implied the edition
INFERRED_DEFAULT = "inferred-default"  # fell back to the work's default_edition
CERTAINTY = (ASSERTED, INFERRED_SCHEME, INFERRED_DEFAULT)

# Names known to be shared across the corpus: always minted with their
# conventional qualifier so a bare ambiguous slug never gets claimed first.
ALWAYS_QUALIFY = frozenset({
    "john", "basil", "gregory", "dionysius", "apollonius", "heraclides",
    "apollodorus", "philo", "theodore", "athenaeus", "nicander", "ptolemy",
    "zeno", "diogenes", "aristides", "eusebius", "maximus", "philostratus",
})

# Leading connectives dropped when slugging a name ("Basil of Caesarea").
_DROP_WORDS = frozenset({"the", "a", "an", "of", "the-younger-of", "ho", "he", "to"})

_SLUG_OK = re.compile(r"[^a-z0-9-]+")


class IdentityError(ValueError):
    """Raised on an attempt that would violate slug immutability/uniqueness."""


def normalize_slug(text: str) -> str:
    """Fold a name to a slug segment: ASCII, lowercase, diacritic-free,
    hyphen-joined, with leading articles/connectives dropped.

    Deterministic so two spellings of one name cannot mint two ids. Operates
    on Latin-script conventional names (the scholarly form); Greek input is
    stripped to its ASCII skeleton and will usually need an explicit slug.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("'", "").replace("’", "")
    t = re.sub(r"[\s_]+", "-", t.strip())
    t = _SLUG_OK.sub("-", t)
    parts = [p for p in t.split("-") if p and p not in _DROP_WORDS]
    return "-".join(parts)


def _merge_aliases(existing: dict, incoming: dict, ns: tuple[str, ...]) -> dict:
    """Union two alias maps; a namespace already set to a different value is a
    conflict (immutability of an asserted cross-reference)."""
    out = dict(existing)
    for k, v in (incoming or {}).items():
        if k not in ns:
            raise IdentityError(f"unknown alias namespace {k!r} (allowed: {ns})")
        if not v:
            continue
        if k in out and out[k] != v:
            raise IdentityError(
                f"alias {k} conflict: {out[k]!r} vs {v!r}")
        out[k] = v
    return out


@dataclass
class Edition:
    slug: str                       # full work.edition slug
    name: str                       # display name, e.g. "West (1998)"
    provider: str = "print"         # corpus name (glaux/diorisis/...) or "print"
    scheme: str = ""                # citation scheme, e.g. "book.line"
    editor: str = ""
    year: int | None = None
    source: str = ""                # repo / where we ingested the text
    servable: bool = True           # False = reference-only, e.g. the TLG-keyed
                                     # edition: we record its bibliography but never
                                     # ship its text. Only servable editions can be
                                     # auto-chosen as a work's default_edition.
    license: str = ""               # license id when known (CC-BY-SA-4.0, CC0/PD)
    aliases: dict = field(default_factory=dict)


@dataclass
class Work:
    slug: str                       # author.work
    author: str                     # author slug
    title: str
    aliases: dict = field(default_factory=dict)
    default_edition: str | None = None   # mutable display/resolution policy
    best_source: str = ""           # the sourcing-map verdict (open_corpus / Migne /
                                     # TLG-PD-edition / locked / ...): lowest-risk
                                     # publishable route, independent of default_edition
    tags: list = field(default_factory=list)      # sorted "dimension:value" facets
    editions: dict = field(default_factory=dict)  # edition-slug -> Edition


@dataclass
class Author:
    slug: str
    name: str
    aliases: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# Logical-locus grammar (CTS-URN passage semantics).
#
# A citation reference is a hierarchy of dot-separated levels (book.chapter.line),
# optionally a RANGE of two endpoints joined by '-'. Per the design
# (docs/identity-and-citation.md) cog adopts CTS-URN logical-locus semantics: a
# range requires MATCHING DEPTH on both endpoints (``5.84-5.116``, never the
# ``5.84-116`` shorthand), so a range is unambiguous and edition-independent.
#
# Real cog loci embed '-' inside a single level (a work-slug section such as
# ``porfyrogen-administrato.1``), so '-' is read as a range delimiter ONLY when it
# splits the reference into exactly two NUMERIC endpoints; otherwise it is an
# ordinary character of a level. Levels are otherwise unconstrained (numerals, a
# Stephanus/Bekker page like ``327a``, a Greek book letter ``Α``, a roman numeral,
# a scholion key ``sch_Ph``) - matching what the open corpora actually cite by.
# --------------------------------------------------------------------------
_LOCUS_NUMERIC = re.compile(r"[0-9]+[a-zA-Z]?[0-9]*")  # 327, 327a, 1094a4


def _split_levels(point: str) -> tuple[str, ...]:
    """Split a single (non-range) reference into its dot levels, rejecting an
    empty/blank level (a leading/trailing/double dot)."""
    levels = point.split(".")
    if any(lv.strip() == "" for lv in levels):
        raise IdentityError(f"empty level in citation reference {point!r}")
    return tuple(levels)


def _is_numeric_point(point: str) -> bool:
    """True if every level of a (non-range) reference is a numeric citation value,
    so a surrounding '-' is a range delimiter rather than a slug character."""
    levels = point.split(".")
    return "" not in levels and all(_LOCUS_NUMERIC.fullmatch(lv) for lv in levels)


@dataclass(frozen=True)
class Ref:
    """A parsed citation reference: a point (``levels``) or a range
    (``levels`` .. ``end``, both the same depth)."""
    levels: tuple[str, ...]
    end: tuple[str, ...] | None = None

    @property
    def is_range(self) -> bool:
        return self.end is not None

    @property
    def depth(self) -> int:
        return len(self.levels)

    def __str__(self) -> str:
        a = ".".join(self.levels)
        return f"{a}-{'.'.join(self.end)}" if self.end is not None else a


def parse_ref(ref: str) -> Ref:
    """Parse a citation reference into a Ref, enforcing CTS logical-locus rules.

    A range (two numeric endpoints joined by '-') must have matching depth:
    ``5.84-5.116`` parses, ``5.84-116`` is rejected. A '-' that does not join two
    numeric endpoints stays an ordinary level character (cog's work-slug loci,
    e.g. ``porfyrogen-administrato.1``). Empty/blank refs and empty levels are
    rejected.
    """
    if ref is None:
        raise IdentityError("citation reference is None")
    s = ref.strip()
    if not s:
        raise IdentityError("empty citation reference")
    if "-" in s:
        bits = s.split("-")
        if len(bits) == 2 and _is_numeric_point(bits[0]) and _is_numeric_point(bits[1]):
            a, b = _split_levels(bits[0]), _split_levels(bits[1])
            if len(a) != len(b):
                raise IdentityError(
                    f"range endpoints must have matching depth: {ref!r} "
                    f"(CTS wants e.g. 5.84-5.116, not 5.84-116)")
            return Ref(a, b)
    return Ref(_split_levels(s))


def scheme_levels(scheme: str) -> tuple[str, ...]:
    """Ordered logical levels a citation scheme names
    (``book.chapter.line`` -> ('book', 'chapter', 'line')); () for an unknown one."""
    s = (scheme or "").strip()
    return tuple(p for p in s.split(".")) if s else ()


def scheme_depth(scheme: str) -> int:
    """Number of hierarchical levels a citation scheme declares (0 if unknown)."""
    return len(scheme_levels(scheme))


def ref_matches_scheme(ref, scheme: str) -> bool:
    """Whether a reference has the depth its edition's scheme declares. An unknown
    scheme (depth 0) cannot disprove a reference, so this returns True."""
    d = scheme_depth(scheme)
    if d == 0:
        return True
    r = ref if isinstance(ref, Ref) else parse_ref(ref)
    return r.depth == d


def is_numeric_ref(ref) -> bool:
    """True if every level (both endpoints of a range) is a plain numeric citation
    value (1, 327, 327a) - the clean numeric logical locus, as opposed to a
    work-slug, Greek/roman letter, or page-key level."""
    try:
        r = ref if isinstance(ref, Ref) else parse_ref(ref)
    except IdentityError:
        return False
    levels = r.levels + (r.end or ())
    return bool(levels) and all(_LOCUS_NUMERIC.fullmatch(lv) for lv in levels)


@dataclass
class Locus:
    """A passage reference, always scoped to a concrete edition."""
    edition: str
    ref: str
    certainty: str = ASSERTED

    def __post_init__(self):
        if self.certainty not in CERTAINTY:
            raise IdentityError(f"bad certainty {self.certainty!r}")
        parse_ref(self.ref)        # validate the citation grammar (raises if malformed)

    @property
    def parsed(self) -> Ref:
        """The reference parsed into hierarchical levels / range (CTS semantics)."""
        return parse_ref(self.ref)


@dataclass
class ResolveResult:
    slug: str | None
    method: str          # "wikidata" | "alias:<ns>" | "name" | "none"
    needs_confirm: bool  # True for the fuzzy name fallback


class Registry:
    """Load/mint/resolve the owned identity namespace, backed by one JSON file."""

    def __init__(self, authors=None, works=None):
        self.authors: dict[str, Author] = authors or {}
        self.works: dict[str, Work] = works or {}

    # ---- persistence -----------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "Registry":
        p = Path(path)
        if not p.exists():
            return cls()
        d = json.loads(p.read_text(encoding="utf-8"))
        authors = {s: Author(slug=s, **a) for s, a in d.get("authors", {}).items()}
        works = {}
        for s, w in d.get("works", {}).items():
            eds = {es: Edition(slug=es, **e) for es, e in w.pop("editions", {}).items()}
            works[s] = Work(slug=s, editions=eds, **w)
        return cls(authors, works)

    def save(self, path: str | Path) -> None:
        out = {
            "authors": {
                s: {"name": a.name, "aliases": a.aliases}
                for s, a in sorted(self.authors.items())
            },
            "works": {
                s: {
                    "author": w.author, "title": w.title, "aliases": w.aliases,
                    "default_edition": w.default_edition,
                    "best_source": w.best_source,
                    "tags": w.tags,
                    "editions": {
                        es: {k: v for k, v in vars(e).items() if k != "slug"}
                        for es, e in sorted(w.editions.items())
                    },
                }
                for s, w in sorted(self.works.items())
            },
        }
        Path(path).write_text(
            json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False),
            encoding="utf-8")

    # ---- minting (append-only) ------------------------------------------
    def mint_author(self, name: str, *, slug: str | None = None,
                    aliases: dict | None = None) -> str:
        """Register an author and return its slug. Idempotent: re-minting the
        same identity unions aliases. A shared-name slug must be qualified."""
        s = slug or normalize_slug(name)
        if not s:
            raise IdentityError(f"empty slug for author {name!r}")
        head = s.split("-")[0]
        if head in ALWAYS_QUALIFY and "-" not in s:
            raise IdentityError(
                f"author {s!r}: name {head!r} is shared, mint a qualified slug "
                f"(e.g. {head}-<epithet>)")
        if s in self.authors:
            a = self.authors[s]
            a.aliases = _merge_aliases(a.aliases, aliases or {}, AUTHOR_ALIAS_NS)
            return s
        self.authors[s] = Author(slug=s, name=name,
                                 aliases=_merge_aliases({}, aliases or {}, AUTHOR_ALIAS_NS))
        return s

    def mint_work(self, author_slug: str, title: str, *, slug: str | None = None,
                  aliases: dict | None = None) -> str:
        if author_slug not in self.authors:
            raise IdentityError(f"unknown author {author_slug!r}")
        s = slug or f"{author_slug}.{normalize_slug(title)}"
        if s in self.works:
            w = self.works[s]
            w.aliases = _merge_aliases(w.aliases, aliases or {}, WORK_ALIAS_NS)
            return s
        self.works[s] = Work(slug=s, author=author_slug, title=title,
                             aliases=_merge_aliases({}, aliases or {}, WORK_ALIAS_NS))
        return s

    def mint_edition(self, work_slug: str, edition_slug: str, name: str, *,
                     provider: str = "print", scheme: str = "", editor: str = "",
                     year: int | None = None, source: str = "",
                     servable: bool = True, license: str = "",
                     aliases: dict | None = None,
                     make_default: bool = False) -> str:
        if work_slug not in self.works:
            raise IdentityError(f"unknown work {work_slug!r}")
        w = self.works[work_slug]
        full = f"{work_slug}.{edition_slug}"
        if full in w.editions:
            e = w.editions[full]
            e.aliases = _merge_aliases(e.aliases, aliases or {}, EDITION_ALIAS_NS)
        else:
            w.editions[full] = Edition(
                slug=full, name=name, provider=provider, scheme=scheme,
                editor=editor, year=year, source=source, servable=servable,
                license=license,
                aliases=_merge_aliases({}, aliases or {}, EDITION_ALIAS_NS))
        # Only a servable edition may auto-fill the default: a reference-only
        # (e.g. TLG-keyed) edition must never become the thing we render/resolve
        # bare citations against. An explicit make_default still wins.
        if make_default or (w.default_edition is None and servable):
            w.default_edition = full
        return full

    # ---- resolution / dedup ---------------------------------------------
    def resolve_author(self, *, qid: str | None = None, aliases: dict | None = None,
                       name: str | None = None) -> ResolveResult:
        return self._resolve(self.authors, AUTHORITATIVE_NS, qid, aliases, name)

    def resolve_work(self, *, qid: str | None = None, aliases: dict | None = None,
                     name: str | None = None) -> ResolveResult:
        return self._resolve(self.works, AUTHORITATIVE_NS, qid, aliases, name, work=True)

    def _resolve(self, table, auth_ns, qid, aliases, name, work=False) -> ResolveResult:
        aliases = dict(aliases or {})
        if qid:
            aliases.setdefault("wikidata", qid)
        # 1. authoritative (Wikidata) match
        for ns in auth_ns:
            v = aliases.get(ns)
            if not v:
                continue
            for slug, rec in table.items():
                if rec.aliases.get(ns) == v:
                    return ResolveResult(slug, ns, False)
        # 2. any other alias match
        for ns, v in aliases.items():
            if ns in auth_ns or not v:
                continue
            for slug, rec in table.items():
                if rec.aliases.get(ns) == v:
                    return ResolveResult(slug, f"alias:{ns}", False)
        # 3. normalized-name fallback (needs human confirmation)
        if name:
            cand = normalize_slug(name)
            for slug in table:
                tail = slug.split(".")[-1] if work else slug
                if tail == cand or slug == cand:
                    return ResolveResult(slug, "name", True)
        return ResolveResult(None, "none", True)

    def same_work(self, a: dict, b: dict) -> bool:
        """True if two incoming work records resolve to the same work slug."""
        ra, rb = self.resolve_work(**a), self.resolve_work(**b)
        return ra.slug is not None and ra.slug == rb.slug

    # ---- tags ------------------------------------------------------------
    def add_tag(self, work_slug: str, dim: str, val) -> str:
        """Add a canonical ``dimension:value`` tag to a work (dedup + sorted).
        Returns the canonical tag string."""
        w = self.works[work_slug]
        t = canon_tag(dim, val)
        if t not in w.tags:
            w.tags = sorted(set(w.tags) | {t})
        return t

    def works_with_tag(self, dim: str, val) -> list[str]:
        """Work slugs carrying a given tag."""
        t = canon_tag(dim, val)
        return sorted(s for s, w in self.works.items() if t in w.tags)

    # ---- locus -----------------------------------------------------------
    def locus_for_citation(self, work_slug: str, ref: str, *,
                           edition: str | None = None,
                           scheme: str | None = None,
                           validate: bool = False) -> Locus:
        """Build a Locus for a citation. An explicit edition is ASSERTED; a
        recognized citation scheme picks that edition (INFERRED_SCHEME);
        otherwise fall back to the work's default_edition (INFERRED_DEFAULT).

        The ref is always parsed for grammar (a malformed ref or a bad-depth range
        raises). With ``validate=True`` the ref's depth must also match the chosen
        edition's declared scheme (e.g. a 3-level ref against a 2-level
        book.line scheme is rejected); a scheme-less edition imposes no such check.
        """
        w = self.works[work_slug]
        if edition:
            full = edition if edition.startswith(work_slug) else f"{work_slug}.{edition}"
            if full not in w.editions:
                raise IdentityError(f"unknown edition {full!r}")
            loc = Locus(full, ref, ASSERTED)
        else:
            loc = None
            if scheme:
                for es, e in w.editions.items():
                    if e.scheme == scheme:
                        loc = Locus(es, ref, INFERRED_SCHEME)
                        break
            if loc is None:
                if not w.default_edition:
                    raise IdentityError(f"work {work_slug!r} has no default_edition")
                loc = Locus(w.default_edition, ref, INFERRED_DEFAULT)
        if validate:
            ed = w.editions[loc.edition]
            if ed.scheme and not ref_matches_scheme(loc.parsed, ed.scheme):
                raise IdentityError(
                    f"citation {ref!r} (depth {loc.parsed.depth}) does not match "
                    f"scheme {ed.scheme!r} (depth {scheme_depth(ed.scheme)}) of "
                    f"edition {loc.edition}")
        return loc

    # ---- display ---------------------------------------------------------
    def preferred_id(self, slug: str) -> str | None:
        """The cross-reference we surface for a slug. Wikidata QID is the
        favourite (it's also the authoritative dedup key); the rest are
        fallbacks, in descending usefulness."""
        rec = self.authors.get(slug) or self.works.get(slug)
        if not rec:
            return None
        for ns in ("wikidata", "viaf", "gnd", "isni"):
            if rec.aliases.get(ns):
                return f"{ns}:{rec.aliases[ns]}"
        return None
