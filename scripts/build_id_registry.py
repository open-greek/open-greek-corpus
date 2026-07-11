#!/usr/bin/env python3
"""Mint and maintain cog's opaque, immutable work/author identifiers.

Why this exists
---------------
Until now the slug (``author-slug.work-slug``) was the primary key everywhere:
the corpus filename, the per-row ``urn`` field, and the key in every registry.
But the slug is SEMANTIC, so it churns whenever a work is re-attributed or an
edition is re-scoped (this project renamed many). A semantic primary key means a
rename silently breaks identity: old citations, corrections keyed by the old
slug, and any downstream link all dangle.

This builder introduces a stable, opaque layer UNDER the slug, the same move
Wikidata makes with its Q-numbers:

    ogc<NNNNNN>   an opaque work-unit id  (Open Greek Corpus work)   ~= Expression
    oga<NNNNNN>   an opaque agent id      (Open Greek Agent/author)

The id is never derived from anything mutable (not the slug, not the title, not
the content). The slug is demoted to a human-readable, resolvable ALIAS of the
id. When a work is renamed the id stays put and the old slug is remembered as a
``former_slug`` (the data-side of a 301 redirect), so identity is never lost.

Id format
---------
``ogc`` / ``oga`` + a zero-padded 6-digit sequential integer (ogc000001 ..).
Sequential like a Wikidata QID (assignment ORDER carries no meaning; the id,
once assigned, is immutable and opaque). Zero-padded to a fixed width so ids sort
and align cleanly in a UI. Six digits gives a 1,000,000 capacity, ~130x the
whole TLG canon (~7,200 works) and far beyond cog's exceed-TLG ambition, so the
width never has to change. The counter is monotonic: the next id is always one
past the highest ever minted (active OR retired), so a retired id is tombstoned,
never recycled.

Invariants (all enforced + validated)
-------------------------------------
  * Append-only: re-running never reassigns an existing work's id. Only a
    genuinely new slug (one that is neither a current nor a former slug of any
    existing id) mints a new id.
  * Never reused: a work that leaves the served set is marked ``retired`` in
    place; its id is kept and the counter never falls back onto it.
  * Deterministic persistence: an existing work keeps its id across rebuilds, so
    running the builder twice is byte-identical (validated by
    tests + ``--check-stable``).

Persistent state vs reproducible input
--------------------------------------
``data/work_ids.json`` and ``data/author_ids.json`` are the persistent LEDGERS
(like Wikidata's item table). They are committed and must never be deleted:
their id<->slug assignments are historical state that cannot be regenerated from
scratch (rebuilding from an empty ledger would re-number everything). What IS
reproducible is every UPDATE to them: the served set (from
``corpus_editions.json``) drives minting/retiring, and the curated rename seed
(``data/work_id_aliases.json``) drives former-slug attribution. Given the
existing ledger plus those inputs, this builder is idempotent.

Usage
-----
    python3 scripts/build_id_registry.py            # mint/maintain the ledgers
    python3 scripts/build_id_registry.py --check-stable   # assert a re-run is a no-op
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS_EDITIONS = DATA / "corpus_editions.json"
SOURCE_REGISTRY = DATA / "source_registry.json"
PSEUDO_ATTR = DATA / "pseudo_author_attributions.json"
WORK_ALIASES = DATA / "work_id_aliases.json"
WORK_IDS = DATA / "work_ids.json"
AUTHOR_IDS = DATA / "author_ids.json"

WORK_PREFIX = "ogc"
AUTHOR_PREFIX = "oga"
ID_WIDTH = 6


# --------------------------------------------------------------------------
# Shared derivation helpers (also imported by build_work_index.py).
# --------------------------------------------------------------------------
def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def served_slugs() -> set[str]:
    """The served work-units: one per data/corpus/<slug>.jsonl file. Reading the
    corpus directory directly (rather than corpus_editions.json) makes the id
    ledger independent of when corpus_editions is reconciled - so a rename that
    moves a file is reflected immediately, no build-order coupling. This, not
    source_registry, is the authoritative universe of things that need an id
    (many served works are not in the registry)."""
    return {fp.name[:-6] for fp in (DATA / "corpus").glob("*.jsonl")}


def author_slug_for(work_slug: str, reg_works: dict, pseudo_works: dict) -> str:
    """The author slug a served work belongs to. Prefer the registry's explicit
    ``author`` field (it fixes whole-volume keys like ``ocr.pg036`` ->
    ``gregorius-nazianzenus``), then the curated pseudo-author attribution for
    OCR/anthology volumes, then the slug's own author segment (before the first
    dot)."""
    w = reg_works.get(work_slug)
    if w and w.get("author"):
        return w["author"]
    pa = pseudo_works.get(work_slug)
    if pa and pa.get("author"):
        return pa["author"]
    return work_slug.split(".", 1)[0]


def author_slugs_for_served(served: set[str], reg_works: dict,
                            pseudo_works: dict) -> set[str]:
    return {author_slug_for(s, reg_works, pseudo_works) for s in served}


# --------------------------------------------------------------------------
# Ledger machinery.
# --------------------------------------------------------------------------
def _fmt_id(prefix: str, n: int) -> str:
    return f"{prefix}{n:0{ID_WIDTH}d}"


def _num(id_str: str, prefix: str) -> int:
    return int(id_str[len(prefix):])


class Ledger:
    """An append-only id<->slug ledger for one entity type."""

    def __init__(self, prefix: str, entries: dict | None = None):
        self.prefix = prefix
        # id -> {"slug": str, "former_slugs": [str], "status": str}
        self.entries: dict[str, dict] = entries or {}

    @classmethod
    def load(cls, path: Path, prefix: str) -> "Ledger":
        d = load_json(path, {})
        return cls(prefix, dict(d.get("works") or d.get("authors") or {}))

    # -- indexes --
    def slug_to_id(self) -> dict[str, str]:
        """Every slug (current AND former) -> its id. A former slug resolving to
        the same id is exactly the redirect."""
        m: dict[str, str] = {}
        for i, e in self.entries.items():
            m[e["slug"]] = i
            for fs in e.get("former_slugs", []):
                m[fs] = i
        return m

    def current_slug_to_id(self) -> dict[str, str]:
        return {e["slug"]: i for i, e in self.entries.items()}

    def _next_num(self) -> int:
        if not self.entries:
            return 1
        return max(_num(i, self.prefix) for i in self.entries) + 1

    # -- mutations --
    def apply_renames(self, renames: list[dict]) -> list[str]:
        """Replay curated 1:1 renames so a work keeps its id across a slug change.
        Idempotent, and safe to call both before and after minting:

          * LIVE rename (the old slug still owns an id, e.g. rename_work.py just
            moved the data and appended to the seed): move that id onto the new
            slug and remember the old one. Must run BEFORE minting so the new
            slug reuses the id instead of getting a fresh one.
          * HISTORICAL rename (the old slug never had an id because it was
            already retired before the ledger existed, e.g. a rescope recovered
            from an audit trail): attach the old slug as a former_slug of the new
            slug's id. Runs AFTER minting, once the new slug has an id.
        """
        msgs = []
        for r in renames:
            frm, to = r.get("from"), r.get("to")
            if not frm or not to:
                continue
            cur = self.current_slug_to_id()
            s2id = self.slug_to_id()
            if s2id.get(frm) and self.entries[s2id[frm]]["slug"] == to:
                continue  # already applied (from is a former slug of to's id)
            if frm in cur:
                i = cur[frm]
                if to in cur and cur[to] != i:
                    msgs.append(
                        f"CONFLICT rename {frm} -> {to}: both are distinct "
                        f"served works ({i} vs {cur[to]}); not auto-merging")
                    continue
                e = self.entries[i]
                e["slug"] = to
                if frm not in e["former_slugs"]:
                    e["former_slugs"].append(frm)
                    e["former_slugs"].sort()
                msgs.append(f"renamed {i}: {frm} -> {to}")
            elif to in cur:
                e = self.entries[cur[to]]
                if frm not in e["former_slugs"]:
                    e["former_slugs"].append(frm)
                    e["former_slugs"].sort()
                    msgs.append(f"aliased {cur[to]}: {frm} -> {to} (historical)")
            # else: neither slug owns an id yet; resolves on the post-mint pass.
        return msgs

    def mint_missing(self, universe: set[str]) -> list[str]:
        """Mint an id for every slug in ``universe`` that no id yet covers
        (current or former). Deterministic: new slugs assigned in sorted order."""
        have = set(self.slug_to_id())
        new = sorted(universe - have)
        minted = []
        n = self._next_num()
        for slug in new:
            i = _fmt_id(self.prefix, n)
            self.entries[i] = {"slug": slug, "former_slugs": [], "status": "served"}
            minted.append(i)
            n += 1
        return minted

    def refresh_status(self, universe: set[str]) -> None:
        """A work is ``served`` iff its current slug is in the served universe,
        else ``retired`` (tombstoned in place; its id is never recycled)."""
        for e in self.entries.values():
            e["status"] = "served" if e["slug"] in universe else "retired"

    def to_json(self, key: str) -> dict:
        active = sum(1 for e in self.entries.values() if e["status"] == "served")
        retired = sum(1 for e in self.entries.values() if e["status"] == "retired")
        return {
            "_meta": {
                "scheme": self.prefix,
                "id_format": f"{self.prefix} + zero-padded {ID_WIDTH}-digit "
                             f"sequential integer",
                "generated_by": "scripts/build_id_registry.py",
                "policy": "opaque, immutable, append-only, never reused, "
                          "never derived from mutable data",
                "counts": {"active": active, "retired": retired,
                           "next": self._next_num()},
            },
            key: {i: self.entries[i] for i in sorted(self.entries)},
        }


# --------------------------------------------------------------------------
# Build.
# --------------------------------------------------------------------------
def build(write: bool = True) -> dict:
    reg = load_json(SOURCE_REGISTRY, {"works": {}, "authors": {}})
    reg_works = reg.get("works", {})
    pseudo_works = load_json(PSEUDO_ATTR, {}).get("works", {})
    aliases = load_json(WORK_ALIASES, {})
    renames = aliases.get("renames", [])

    served = served_slugs()
    author_universe = author_slugs_for_served(served, reg_works, pseudo_works)

    log: list[str] = []

    # --- works ---
    wl = Ledger.load(WORK_IDS, WORK_PREFIX)
    log += wl.apply_renames(renames)     # live moves (before mint)
    minted_w = wl.mint_missing(served)
    log += wl.apply_renames(renames)     # historical aliases (after mint)
    wl.refresh_status(served)

    # --- authors ---
    al = Ledger.load(AUTHOR_IDS, AUTHOR_PREFIX)
    minted_a = al.mint_missing(author_universe)
    al.refresh_status(author_universe)

    work_out = wl.to_json("works")
    author_out = al.to_json("authors")

    if write:
        WORK_IDS.write_text(
            json.dumps(work_out, ensure_ascii=False, indent=1), encoding="utf-8")
        AUTHOR_IDS.write_text(
            json.dumps(author_out, ensure_ascii=False, indent=1), encoding="utf-8")

    for m in log:
        print("  " + m)
    print(f"works:   {work_out['_meta']['counts']['active']} served, "
          f"{work_out['_meta']['counts']['retired']} retired, "
          f"+{len(minted_w)} minted this run")
    print(f"authors: {author_out['_meta']['counts']['active']} served, "
          f"{author_out['_meta']['counts']['retired']} retired, "
          f"+{len(minted_a)} minted this run")
    return {"works": work_out, "authors": author_out,
            "minted_works": minted_w, "minted_authors": minted_a}


def check_stable() -> int:
    """Assert a re-run reassigns nothing: the on-disk ledger already covers every
    served slug and author, and re-emitting it is byte-identical."""
    if not WORK_IDS.exists():
        print("no ledger yet; run without --check-stable first")
        return 1
    before_w = WORK_IDS.read_text(encoding="utf-8")
    before_a = AUTHOR_IDS.read_text(encoding="utf-8")
    res = build(write=False)
    after_w = json.dumps(res["works"], ensure_ascii=False, indent=1)
    after_a = json.dumps(res["authors"], ensure_ascii=False, indent=1)
    ok = True
    if res["minted_works"] or res["minted_authors"]:
        print(f"NOT STABLE: would mint {len(res['minted_works'])} works, "
              f"{len(res['minted_authors'])} authors")
        ok = False
    if before_w != after_w:
        print("NOT STABLE: work_ids.json would change")
        ok = False
    if before_a != after_a:
        print("NOT STABLE: author_ids.json would change")
        ok = False
    print("stable: re-run reassigns nothing" if ok else "UNSTABLE")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--check-stable" in sys.argv:
        raise SystemExit(check_stable())
    build(write=True)
