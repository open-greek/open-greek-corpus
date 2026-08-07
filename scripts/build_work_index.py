#!/usr/bin/env python3
"""Derive data/work_index.json: the reader-facing, WEMI-leveled join over the
opaque id ledgers and every identity/anchor source.

This is the one artifact a downstream consumer (the reader, the site, an API)
needs. It is DERIVED and byte-stable: rebuilt from the ledgers
(work_ids.json / author_ids.json), the crosswalk (tlg_crosswalk.json), the
registry (source_registry.json), the served metadata (corpus_editions.json) and
the curated author/title attributions (pseudo_author_attributions.json). Run it
after build_id_registry.py.

WEMI leveling (FRBR) of the id anchors it records, per served work-unit:

    Agent        author.id (oga...) + authorities (wikidata/viaf/gnd/isni)
    Work         work_anchors: cts + tlg (the bare TLG author.work number, the
                 only ~100%-coverage external work id) + work-level wikidata.
                 SHARED across variant editions of one Work.
    Expression   id (ogc...): OUR identity, the curated served work-unit. Finer
                 than the TLG Work anchor: the 4 variant-edition pairs are two
                 DISTINCT ogc ids that share ONE tlg/cts Work anchor.
    Manifestation edition + source + license (+ passage/token counts): the
                 concrete embodiment cog serves.

The index also carries a ``redirects`` map (former slug -> current slug) so a
citation of a renamed work still resolves, and keeps the opaque id as the
canonical anchor while the human-readable slug stays the resolvable handle /
filename.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_id_registry import (  # noqa: E402
    DATA, load_json, author_slug_for,
    CORPUS_EDITIONS, SOURCE_REGISTRY, PSEUDO_ATTR, WORK_IDS, AUTHOR_IDS,
)

TLG_CROSSWALK = DATA / "tlg_crosswalk.json"
WORK_INDEX = DATA / "work_index.json"


def _clean(d: dict) -> dict:
    """Drop empty values so the anchors block only lists what is actually known
    (a work with no external id gets an empty {} - that is the point)."""
    return {k: v for k, v in d.items() if v}


def _unbalanced(title: str) -> bool:
    """True if a bracket opens and never closes, so the title is cut short.

    Square brackets count as well as parentheses. The Canon uses them for
    editorial qualifiers, and exactly one served title is cut inside one:
    `Περὶ νοήσεως καὶ αἰσθήσεως. [ὅτι ἐν μόνῳ τῷ θεῷ τὸ`, whose tail the
    crosswalk holds. Counting only parens missed it.
    """
    t = title or ""
    return t.count("(") != t.count(")") or t.count("[") != t.count("]")


def _fold_words(title: str) -> list[str]:
    """Words only: diacritics, case and punctuation dropped.

    Loose on purpose, because the two sources differ in exactly those things -
    one prints `(= Περὶ διαφόρους` where the other has `(Περὶ διαφόρους`, and
    one Title-Cases where the other does not. The looseness is why the extension
    test alone is NOT enough to accept a title, and why the caller also requires
    the current one to be visibly truncated.
    """
    t = "".join(c for c in unicodedata.normalize("NFD", title or "")
                if not unicodedata.combining(c)).lower()
    return re.sub(r"[^0-9a-z\u03b1-\u03c9 ]+", " ", t).split()


def _completes(truncated: str, candidate: str) -> bool:
    """True if `candidate` is `truncated` with its tail restored.

    Both conditions matter. The candidate must be balanced, or it is truncated
    too and swapping one cut title for another gains nothing; and it must extend
    the current one word for word from the start, so a different work's title
    cannot take its place.
    """
    if not candidate or _unbalanced(candidate):
        return False
    a, b = _fold_words(truncated), _fold_words(candidate)
    return len(b) > len(a) and b[:len(a)] == a


def _title_from_desc(desc: str) -> str:
    """The title out of a ledger desc written "Author - Title (note)".

    The note is where the ledger records which volume and loci the unit came
    from ("(PG005 loci 331-373)"), which is provenance rather than title, so a
    trailing parenthetical is dropped. Anything without the separator is left
    alone: it is prose about the work, not its name.
    """
    if " - " not in desc:
        return ""
    tail = desc.split(" - ", 1)[1].strip()
    tail = re.sub(r"\s*\((?:PG|CPG|loci|cols?\.|pp?\.)[^()]*\)\s*$", "", tail)
    return tail.strip(" .")


def build(write: bool = True) -> dict:
    ce = load_json(CORPUS_EDITIONS, {})
    tc = load_json(TLG_CROSSWALK, {})
    reg = load_json(SOURCE_REGISTRY, {"works": {}, "authors": {}})
    reg_works = reg.get("works", {})
    reg_authors = reg.get("authors", {})
    pseudo = load_json(PSEUDO_ATTR, {})
    pseudo_works = pseudo.get("works", {})
    pseudo_authors = pseudo.get("authors", {})

    work_ids = load_json(WORK_IDS, {}).get("works", {})
    author_ids = load_json(AUTHOR_IDS, {}).get("authors", {})
    author_slug_to_id = {e["slug"]: i for i, e in author_ids.items()}

    def author_block(work_slug: str) -> dict:
        a_slug = author_slug_for(work_slug, reg_works, pseudo_works)
        auth = reg_authors.get(a_slug, {})
        name = auth.get("name")
        aliases = dict(auth.get("aliases", {}))
        if not name:  # curated pseudo-author label (collective volumes)
            pa = pseudo_authors.get(a_slug, {})
            name = pa.get("name") or a_slug
            for k, v in (pa.get("aliases") or {}).items():
                aliases.setdefault(k, v)
        return _clean({
            "id": author_slug_to_id.get(a_slug),
            "slug": a_slug,
            "name": name,
            "authorities": _clean({
                "wikidata": aliases.get("wikidata"),
                "viaf": aliases.get("viaf"),
                "gnd": aliases.get("gnd"),
                "isni": aliases.get("isni"),
            }),
        })

    # urn -> ledger row, for the OCR and CGPG works. These files are hand-kept
    # provenance records, so their `desc` is written "Author - Title (note)".
    ledgers: dict[str, dict] = {}
    for _fn in ("ocr_works.json", "cgpg_works.json"):
        _fp = DATA / _fn
        if _fp.exists():
            for _row in json.loads(_fp.read_text(encoding="utf-8")):
                if _row.get("urn"):
                    ledgers.setdefault(_row["urn"], _row)

    def _tidy(title: str) -> str:
        """Collapse the whitespace a vendored title brings with it.

        A CTS `ti:title` is pretty-printed XML, so two of them reach here with an
        embedded newline and the indent of the next line still attached. It is
        never part of the name, and it breaks any consumer that treats the index
        as tabular: build_corpus_catalog.py has to strip it again on the way into
        a TSV, where a raw newline would end the row.
        """
        return " ".join((title or "").split())

    def title_for(work_slug: str) -> str:
        w = reg_works.get(work_slug)
        if w and w.get("title"):
            # The Canon this repo vendors truncates: 84 of the 86 titles that
            # end mid-parenthesis are already cut in work_inventory.json before
            # any of our code reads them (issue #24). Where the crosswalk holds
            # the same title whole, take it - but ONLY where the registry's is
            # visibly truncated. Preferring the longer title generally would
            # change 58 titles instead of 22, and the extra 36 are not repairs:
            # `De Usu Partium` would become `De usu partium corporis humani
            # I-XI` and `Epistulae` would become `Epistulae, Decretum,
            # Orationes`, which is a different scope, not a restored tail.
            if _unbalanced(w["title"]):
                cw = (tc.get(work_slug) or {}).get("title")
                if _completes(w["title"], cw):
                    return _tidy(cw)
            return _tidy(w["title"])
        pa = pseudo_works.get(work_slug)
        if pa and pa.get("title"):
            return _tidy(pa["title"])
        # The registry only covers works the TLG Canon lists, so everything
        # ingested from elsewhere - carved CGPG volumes, byzantium.gr, the OCR'd
        # PD editions - reached the served index with an empty title, 913 of
        # them. The crosswalk already vends a title for most; use it rather than
        # publish a blank.
        cw = tc.get(work_slug)
        if cw and cw.get("title"):
            return _tidy(cw["title"])
        # Neither the registry nor the crosswalk covers a work with no TLG
        # anchor, which left 479 of them blank (issue #3). Two sources in this
        # repo do describe them, and neither invents anything.
        led = ledgers.get(work_slug)
        if led:
            if (led.get("title") or "").strip():
                return _tidy(led["title"].strip())
            from_desc = _title_from_desc(led.get("desc") or "")
            if from_desc:
                return _tidy(from_desc)
        # The FGrH/FHG authors are served as their collected fragments, and that
        # IS the work: `abas.fragmenta` is Abas' Fragmenta. Reading it off the
        # slug states what the slug already says rather than supplying a title
        # from outside.
        if re.search(r"\.fragmenta(-|$)", work_slug):
            return _tidy("Fragmenta")
        return _tidy("")

    works = {}
    redirects = {}
    n_anchor = n_no_anchor = 0
    for i, e in sorted(work_ids.items()):
        slug = e["slug"]
        if e["status"] != "served":
            # Retired ids are kept in the ledger but not in the served index;
            # their former slugs still redirect below.
            for fs in e.get("former_slugs", []):
                redirects[fs] = slug
            continue
        cw = tc.get(slug, {})
        rw = reg_works.get(slug, {})
        ral = rw.get("aliases", {})
        anchors = _clean({
            "cts": cw.get("cts") or ral.get("cts"),
            "tlg": cw.get("tlg"),
            "wikidata": ral.get("wikidata"),
        })
        if anchors:
            n_anchor += 1
        else:
            n_no_anchor += 1
        man = ce.get(slug, {})
        works[slug] = {
            "id": i,
            "slug": slug,
            "former_slugs": e.get("former_slugs", []),
            "title": title_for(slug),
            "author": author_block(slug),
            "work_anchors": anchors,
            "manifestation": _clean({
                "edition": man.get("edition"),
                "source": man.get("source"),
                "license": man.get("license"),
                "n_passages": man.get("n_passages"),
                "n_tokens": man.get("n_tokens"),
            }),
        }
        for fs in e.get("former_slugs", []):
            redirects[fs] = slug

    out = {
        "_meta": {
            "description": "Reader-facing WEMI-leveled index of served cog "
                           "work-units, keyed by current slug. The opaque `id` "
                           "(ogc...) is the canonical anchor; the slug is a "
                           "resolvable, mutable alias. `redirects` maps a former "
                           "slug to its current slug (the data-side of a 301).",
            "generated_by": "scripts/build_work_index.py",
            "levels": {
                "agent": "author.id (oga) + authorities",
                "work": "work_anchors (cts/tlg/wikidata), shared across variant "
                        "editions of one Work",
                "expression": "id (ogc): our served work-unit, finer than the "
                              "TLG Work anchor",
                "manifestation": "edition + source + license",
            },
            "counts": {
                "works": len(works),
                "with_external_anchor": n_anchor,
                "no_external_anchor": n_no_anchor,
                "redirects": len(redirects),
            },
        },
        "works": works,
        "redirects": {k: redirects[k] for k in sorted(redirects)},
    }
    if write:
        WORK_INDEX.write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"work_index: {len(works)} works "
          f"({n_anchor} with an external anchor, {n_no_anchor} without), "
          f"{len(redirects)} redirects")
    return out


if __name__ == "__main__":
    build(write=True)
