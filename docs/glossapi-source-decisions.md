# GlossAPI historical-source intake decisions

This record evaluates three permissively licensed GlossAPI datasets as possible
Ancient/Medieval text sources.  It does **not** treat a permissive dataset
license as sufficient evidence that every row is correctly identified, belongs
to the target historical variety, or is new to OGC.

The machine-readable authority is
`data/glossapi_source_decisions.json`.  It pins each Hugging Face dataset to a
full commit and the selected artifact to its size and SHA-256, following
`docs/pinning-discipline.md`.

## Decisions

| source | decision | why |
|---|---|---|
| Project Gutenberg Greek | hold for identity recovery | The collection mixes four varieties, lacks per-document source URLs, and uses an automatically generated variety label.  Recover a stable Gutenberg identity and edition/translation status before using any row. |
| Ekklisiastika Keimena | blocked pending GOARCH rights and identity | The material is in scope, but it includes structural rubrics, run-together boundaries, and heavily repeated service books, biblical readings, and hymn cycles.  More importantly, GlossAPI's dataset declaration does not establish rights for the GOARCH source text; obtain written permission or an independently licensed edition before any admission. |
| Archetai | OCR quarantine | Each row is volume-level OCR from publications spanning 1837-present.  Separate historical primary text from Modern commentary, apparatus, bibliography, and foreign-language material, then apply OGC's OCR quality and dedup gates per segment. |

## Dilemma boundary

These datasets do not flow directly into Dilemma.  OGC owns their upstream
pins, identity resolution, provenance, deduplication, and quality decisions.
Once an admitted source has passed the normal corpus build, it contributes to
`public_lexicon.tsv` through `scripts/build_public_corpus.py`.  Dilemma then
pins the OGC release/content hash and consumes that deduplicated public export,
as required by `docs/pinning-discipline.md`.

Raw historical frequencies, supplied classifier labels, quarantined OCR, and
duplicate-only rows are therefore outside the Dilemma input boundary.
Ekklisiastika's raw token and n-gram counts are also excluded: its repeated
Oktoechos cycles would overstate distinct language even after basic token
cleaning.

## Ekklisiastika staging

`scripts/stage_glossapi_ekklisiastika.py` is the first intake step for the
pinned Ekklisiastika artifact.  It verifies the pinned byte size and SHA-256
before reading the parquet, retains its title/category/subcategory and the
GOARCH collection URL as provenance, and assigns deterministic staging-only
row and passage loci.  Those loci do not claim an edition or a source page.

The stage removes explicit service and reading rubrics, repairs only known
structural labels joined to a following word, and keeps unresolved joins in
quarantine.  Any lower-case Greek letter immediately followed by an upper-case
Greek letter inside one token (for example `ΘεοτοκίονὉ`) is an unresolved welded
boundary: the stage records the affected forms and counts, then quarantines the
row rather than guessing a split.  It also removes the exact inline performance
marker `ΤΟ ΑΚΟΥΤΕ`, recording every removal separately in the intake report.
It marks labelled biblical readings and quotations, and compares
cleaned passages for exact and conservative near duplicates both within the
artifact and against `data/corpus`.  Duplicate-only witnesses remain outside
the corpus pending an edition-precedence decision.

Run the complete, non-admitting audit with:

```sh
python3 scripts/stage_glossapi_ekklisiastika.py
```

It writes `data/glossapi_ekklisiastika_intake_report.json`.  The report is an
audit artifact, not corpus data: every row stays quarantined until an editor
supplies a citable per-record GOARCH URL, stable work and edition identity,
and an explicit locus mapping.  The script never writes `data/corpus` or
rebuilds `public_lexicon.tsv`; those normal OGC paths remain unavailable until
that evidence exists.

## Underlying-text rights

The GlossAPI artifact declares CC-BY-4.0, but it identifies GOARCH as the
underlying text collection.  On 2026-09-21, OGC checked GOARCH's [Terms of
Use](https://www.goarch.org/-/terms-of-use), which require prior written
permission to reproduce, distribute, repurpose, or save site material.  That
does not establish the commercial redistribution required by downstream users
such as Tonos.

`data/glossapi_source_decisions.json` therefore records this source as
`blocked_pending_written_permission`.  No row can be admitted, and no Dilemma
NOTICE or Tonos credit can be authored, until written permission (or an
independently licensed replacement edition) supplies both an explicit reuse
basis and its exact required attribution text.

## Classifier evidence

The GlossAPI variety classifier is useful only as a triage signal.  In a
separate Dilemma-side evaluation at its pinned model revision, it scored 14/16
chunks across small independent Classical, Katharevousa, and Standard Modern
fixtures (87.5%): 75% on Classical, 75% on Katharevousa, and 100% on the Modern
fixtures.  Its model card reports Wiki data in training, so the Modern result
has source-family leakage risk; it also exposes no Medieval class.  For these
reasons no OGC gate above accepts a row solely from its classifier label.
