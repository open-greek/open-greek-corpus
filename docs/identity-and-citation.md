# Identity and citation design

How cog identifies works and authors, and how it cites passages, without being
anchored to the proprietary TLG Canon. This is the design; `build_crosswalk_report.py`
measures progress against it (`data/crosswalk_report.json`).

## The problem with "just use CTS"

The obvious move, adopt the open CTS URN standard, does not actually free the
corpus from the TLG. The CTS `greekLit` namespace used by Perseus and
OpenGreekAndLatin is built on TLG numbering: the textgroup and work components
are the TLG (and PHI/STOA) Canon numbers, so `urn:cts:greekLit:tlg0012.tlg001`
just wraps "TLG author 0012, work 001" in a longer string.[1][2] Switching the
key from `tlg0012.tlg001` to the CTS URN re-embeds the TLG number as the
backbone.

The escape is not a different standard but a different anchor: an identifier cog
controls (its slug), with every external number, TLG included, demoted to a
crosswalk alias.

## What the data says (measured)

From `data/source_registry.json` via `build_crosswalk_report.py`:

| layer | identifier | coverage |
|---|---|---|
| work key | cog slug (`author.work`) | 100% (already the key) |
| work crosswalk | TLG/CTS number | 100% |
| work crosswalk | Wikidata QID | ~7% |
| author anchor | Wikidata QID | ~76% |
| author anchor | VIAF / GND / ISNI | ~74% / ~72% / ~41% |
| passage | logical locus on any edition | ~54% of works |
| passage | logical locus on the SERVED edition | ~14% of works |

The two passage rows differ by which edition the logical scheme sits on. The
~54% counts a work as having a logical locus if *any* of its editions does, but
for most of those works the logical scheme belongs to the reference-only TLG
edition cog never serves; the open edition cog actually renders bare citations
against (`default_edition`) carries a logical locus for only ~14% of works. That
~14% (`served_canonical_locus` in the report) is the honest Phase-2 yardstick.

The decisive numbers: Wikidata has QIDs for most ancient Greek authors (~76%)
but for almost no individual works (~7%), because it does not mint items for
fragments and minor treatises. So Wikidata can anchor authors but not works, and
the TLG number turns out to be the only identifier with full work-level coverage.
That is the empirical reason to keep it, as an alias.

## Design

### Work and author identity

- Primary key: an opaque, immutable, cog-minted id, `ogc<NNNNNN>` for a
  work-unit and `oga<NNNNNN>` for an author (Wikidata's move, applied to our own
  namespace). The slug (`author.work`) is demoted from key to a human-readable,
  resolvable *alias* of that id: still the filename and handle, but no longer the
  identity. This split is what lets a re-attribution change the slug without
  losing identity - the id stays put and the old slug becomes a `former_slug`
  redirect. The ledgers, the WEMI leveling, the rename mechanism, and the
  reader-facing index are documented in `opaque-identifiers.md`; the builder is
  `scripts/build_id_registry.py`.
- The slug stays 100% covered, human-readable, cog-governed, edition-independent,
  and immutable-by-policy (a rename appends the old slug to the id's
  `former_slugs`; `source_identity.py` also enforces alias-conflict immutability
  on the crosswalk side). It is now an alias of the opaque id rather than the key
  itself.
- Author anchor: Wikidata QID, with VIAF/GND/ISNI alongside. Authors are where
  open universal authorities have real coverage, so anchor there.
- Work crosswalk, not work anchor: there is no open universal work-level id, so
  keep the TLG number as the `cts` alias (it is the only 100% work id and the
  de-facto lingua franca), attach a Wikidata QID opportunistically where one
  exists, and mint cog slugs for the large class of works no canon enumerates
  (fragments, dubia, lost-by-title), the same move Perseus made with FHG/EGF/PLG.[2]

### Crosswalk schema

Each entity carries an `aliases` map (already in the registry) over a defined
namespace set per type:

- work: `cts` (the TLG number), `wikidata`, `trismegistos`, `perseus`, `iowa`
- author: `wikidata`, `viaf`, `gnd`, `isni`, `trismegistos`
- edition: `cts`, `hathitrust`, `trismegistos`, `ldab`, `doi`, `isbn`
  (matches `source_identity.EDITION_ALIAS_NS`)

### Passage citation

Two tiers, both partly present:

- Canonical logical locus per work: the edition-independent reference
  (`book.chapter.line`, `section.line`, `fragment.line`) cog derives in ingest.
  Adopt CTS-URN logical-locus semantics off the shelf, hierarchical levels and
  ranges requiring matching depth (`5.84-5.116`, not `5.84-116`).[3] This grammar
  is implemented in `source_identity.py` (`parse_ref` -> `Ref`, `scheme_depth`,
  `ref_matches_scheme`, `is_numeric_ref`): it parses a ref into levels, treats a
  '-' as a range delimiter only between two equal-depth numeric endpoints (so the
  hyphen inside a work-slug level such as `porfyrogen-administrato.1` is kept
  literal), and rejects the mismatched-depth shorthand. `Locus` validates its ref
  on construction; it parses 100% of the ~586k loci in the served corpus, of which
  ~91% are clean numeric loci.
- Edition-bound schemes as aliases: Stephanus, Bekker, Jebb, Kühn, volume.page,
  Migne page-column, etc. (already recorded per edition as `scheme`), each mapped
  to the canonical locus so a citation in any scheme resolves to the canonical one.

When cog serves an API, use DTS (Distributed Text Services), which is
identifier-agnostic and supports citation hierarchies that vary within a text,
rather than CTS, which would force CTS/TLG URNs back in as the required id.[4]

## Migration path

- Phase 0 (done): slug is the key; TLG lives as the `cts` alias; author
  authorities populated. Superseded by the opaque-id layer (below): the slug is
  now an alias of an `ogc`/`oga` id, not the key.
- Phase 0b (done): opaque, immutable `ogc`/`oga` ids minted for every served
  work-unit and author (`build_id_registry.py` -> `work_ids.json` /
  `author_ids.json`), WEMI-leveled outward anchors and a redirect layer exposed
  in `work_index.json`, and a single id-preserving rename tool
  (`rename_work.py`). See `opaque-identifiers.md`.
- Phase 1 (in progress): the crosswalk report (`build_crosswalk_report.py`).
  Then enrich: fill work-level Wikidata QIDs via the author link (~5,600 works
  are reachable that way), add `trismegistos`/`perseus`/`iowa` namespaces.
- Phase 2 (grammar landed): the logical-locus grammar is implemented and the
  crosswalk report now measures the served canonical locus (`served_canonical_locus`,
  ~14% of works). Remaining: promote one canonical logical locus per work, distinct
  from the edition schemes, and record edition-scheme to canonical-locus mappings.
  The sharper target is the ~551 works whose served (`default_edition`) text cites
  only by page/volume, plus the works served with no scheme at all; the ~3,300
  any-edition figure overcounts because it includes reference-only TLG editions.
- Phase 3 (optional): serve via a DTS endpoint keyed by cog slug.

## Pitfalls and policies

- Do not drop TLG: it is the only 100% work id (measured). Alias, do not delete.
  A bare author/work number is a fact, distinct from the licensable Canon text.
- Fragments / dubia / spuria: mint cog slugs (already done); track the Iowa Canon
  as it matures for the lost/fragmentary tail.[5]
- Recensions / multiple editions: use the edition (FRBR version) level, already
  modelled; the work stays single.[2]
- Conflicting numbering schemes: one canonical logical locus plus N edition-bound
  alias schemes, resolved against the canonical.
- Governance: cog owns and pins the slug namespace. Wikidata QIDs are open but
  community-mutable, fine as an anchor/alias, unsafe as the sole key.

## Caveats (unverified)

The Wikidata-anchor and Trismegistos/VIAF crosswalk choices rest on cog's
measured data plus the research framing, not on independently verified
governance/persistence evidence for those systems. The legality of publishing a
TLG-number crosswalk (bare numbers as uncopyrightable facts) is very likely fine
but unadjudicated. The Iowa Canon is still in development. Confirm DTS/CITE2
current syntax before building against them.

## References

1. OpenGreekAndLatin, "What is a CTS URN?" https://www.opengreekandlatin.org/what-is-a-cts-urn/
2. PerseusDL catalog wiki, "CTS URNs and Work Identifiers." https://github.com/PerseusDL/catalog_pending/wiki/CTS-URNs-and-Work-Identifiers:-Overview-and-Perseus-Catalog-Usage
3. CTS URN specification. https://cite-architecture.github.io/ctsurn_spec/
4. Almas, Cayless, Clérice et al., "Distributed Text Services," jTEI 2023. https://journals.openedition.org/jtei/4352
5. Iowa Canon of Ancient Authors and Works (ISAW Papers 20-9). http://dlib.nyu.edu/awdl/isaw/isaw-papers/20-9/
