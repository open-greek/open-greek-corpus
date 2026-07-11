# Opaque identifiers and WEMI leveling

How cog gives every served work-unit and author a stable, opaque, immutable id
that survives re-attribution, and how those ids map onto the FRBR/WEMI levels and
outward to CTS/TLG/Wikidata.

## Why the slug could not stay the primary key

Until this layer, the slug (`author-slug.work-slug`) was the primary key
everywhere: the corpus filename `data/corpus/<slug>.jsonl`, the per-row `urn`
field (which holds the slug, not a CTS URN), and the key in
`corpus_editions.json`, `source_registry.json`, and `tlg_crosswalk.json`.

The slug is deliberately *semantic* (human-readable, edition-aware). That is
good for people and bad for a key: a semantic key churns. Re-attributing a work,
re-scoping a mis-labeled scan, or splitting a catch-all all change the slug, and
because the slug was the identity, every citation, correction, and downstream
link keyed by the old slug silently dangled. This project renamed many works, so
the churn was real, not hypothetical.

## Why not an external authority as the key

Measured over the 3,619 served works: 88% have a TLG id and a CTS URN, only ~12%
have a work-level Wikidata QID, and 390 (11%) have *no* external id at all,
because they are exactly the exceed-TLG material cog exists to add (papyri,
post-1453 and Katharevousa texts, PG works absent from the TLG, fresh OCR). No
external authority covers the corpus, so none can be the primary key. And TLG
granularity is *coarser* than ours: 4 TLG ids each map to two distinct cog
works (variant editions of one text). An external id can only ever be an anchor,
never the key. (Full argument: `identity-and-citation.md`.)

## The scheme

Mint our own opaque ids, the same move Wikidata makes with Q-numbers:

| prefix | entity | example | ~WEMI level |
|---|---|---|---|
| `ogc` | work-unit (Open Greek Corpus work) | `ogc000017` | Expression |
| `oga` | agent / author | `oga000001` | Agent |

Format: prefix + a zero-padded 6-digit sequential integer. Sequential like a
QID, so assignment *order* carries no meaning; the id, once assigned, is
immutable and opaque (never derived from the slug, title, or content). Zero-padded
to a fixed width so ids sort and align in a UI. Six digits is a 1,000,000
capacity, ~130x the whole TLG canon and far beyond cog's ambition, so the width
never has to change; the counter is monotonic, so a retired id is tombstoned and
never recycled.

The slug is *demoted to a resolvable alias* of the id. We keep the slug as the
filename and handle (it is readable and already wired through the corpus); the
opaque id is the canonical anchor in the registry and index. We do **not** rename
files or rewrite corpus rows to opaque ids: that would trade a readable handle
for an unreadable one and rewrite the whole corpus for no gain. The id lives in
the registry/index; the slug resolves to it.

## Invariants

- Append-only: re-running the builder never reassigns an existing work's id.
  Only a genuinely new slug (neither a current nor a former slug of any id) mints
  a new id.
- Never reused: a work that leaves the served set is marked `retired` in place;
  its id is kept and the counter never falls back onto it.
- Deterministic persistence: an existing work keeps its id across rebuilds, so a
  re-run is byte-identical (`build_id_registry.py --check-stable`; test coverage
  in `tests/test_id_layer.py`).

## WEMI leveling

Each served work-unit records anchors at four FRBR levels
(`data/work_index.json`):

- Agent - `author.id` (`oga...`) plus its authorities
  (`wikidata`/`viaf`/`gnd`/`isni`). Authors are where open universal authorities
  actually have coverage.
- Work - `work_anchors`: the CTS URN and the bare TLG author.work number (the
  only external id with ~100% work-level coverage), plus a work-level Wikidata
  QID where one exists. This is the level shared across variant editions.
- Expression - our `ogc` id: the curated served work-unit. It is *finer* than the
  TLG Work anchor. The 4 variant-edition pairs (e.g. `clearchus-solensis.fragmenta`
  and `clearchus-philosophy.fragmenta`) are two distinct `ogc` ids that share one
  `tlg1270.tlg001` Work anchor. That is the whole point of owning the id: our
  identity can be more precise than the external one.
- Manifestation - `edition` + `source` + `license` (with passage/token counts):
  the concrete embodiment cog serves (e.g. Müller's FHG 4 via DFHG, a Migne PG
  volume). A work can carry more than one; `corpus_editions.json` labels it by
  the edition serving the most Greek.

The 390 works with no external id still get a distinct `ogc` id and an empty
`work_anchors`. That is the value of a self-owned id: it anchors material no
external canon enumerates.

## The rename / redirect layer

Every id carries a `former_slugs` list. When a work is renamed, its id stays put
and the old slug is appended there, so the old slug still resolves to the same
work (the data-side of a 301 redirect). `work_index.json` exposes this as a
`redirects` map (former slug -> current slug).

Renames go through **one** tool, `scripts/rename_work.py`, which moves the file,
rewrites row `urn`s, rekeys the crosswalk/registry, records the rename in the
reproducible seed `data/work_id_aliases.json`, and re-derives the ledger so the
id follows the work. Renaming by hand risks minting a fresh id and orphaning the
old slug; don't. The seed also carries historical renames recovered from the
rescope/dissolve audit trails, so past churn is reconstructable.

Catch-all *dissolves* (one slug fanned out into many per-author works, e.g. the
SVF Arnim volumes) are not renames: the retired slug has no single successor, so
its id is tombstoned rather than redirected.

## Files and build order

Persistent ledgers (committed, never deleted - their id assignments are
historical state that cannot be regenerated from scratch):

- `data/work_ids.json` - `ogc` id -> current slug, former_slugs, status.
- `data/author_ids.json` - `oga` id -> current slug, former_slugs, status.

Reproducible inputs / derived views:

- `data/work_id_aliases.json` - curated rename seed (the source of truth for
  renames; `build_id_registry.py` replays it, `rename_work.py` appends to it).
- `data/work_index.json` - derived, reader-facing WEMI join (rebuild anytime).
- `corpus_editions.json` - now also carries each work's `id`.

Pipeline: build the corpus, then

```
python3 scripts/build_id_registry.py        # mint/maintain the ledgers
python3 scripts/reconcile_corpus_editions.py # derive corpus_editions (+ inject id)
python3 scripts/build_work_index.py          # derive the WEMI index
python3 scripts/validate_id_layer.py         # assert every invariant
```

`build_id_registry.py` reads the served set straight from the corpus directory,
so it is independent of when `corpus_editions.json` is reconciled.

## What a consumer (reader / site / API) needs

Read `data/work_index.json`. Per served work, keyed by current slug:

```jsonc
{
  "works": {
    "<current-slug>": {
      "id": "ogc000017",              // canonical opaque anchor
      "slug": "<current-slug>",       // resolvable human handle / filename stem
      "former_slugs": ["<old-slug>"], // redirect sources
      "title": "…",
      "author": {
        "id": "oga000001", "slug": "…", "name": "…",
        "authorities": { "wikidata": "Q…", "viaf": "…", "gnd": "…", "isni": "…" }
      },
      "work_anchors": {               // Work level; {} for the 390 exceed-TLG works
        "cts": "urn:cts:greekLit:tlg…", "tlg": "tlg….tlg…", "wikidata": "Q…"
      },
      "manifestation": {              // Manifestation level
        "edition": "…", "source": "…", "license": "…",
        "n_passages": 0, "n_tokens": 0
      }
    }
  },
  "redirects": { "<old-slug>": "<current-slug>" }
}
```

To resolve a possibly-stale slug: look it up in `works`; if absent, follow
`redirects` to the current slug, then `works`. The `id` is stable across every
rename, so persist the `id`, not the slug, in any external link.
