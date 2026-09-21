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
| Ekklisiastika Keimena | conditional ingest after cleaning and deduplication | The material is in scope, but it includes structural rubrics, run-together boundaries, and heavily repeated service books, biblical readings, and hymn cycles.  Strip non-text structure, quarantine unresolved joins, map works/loci, and admit only unique or genuinely preferable witnesses. |
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

## Classifier evidence

The GlossAPI variety classifier is useful only as a triage signal.  In a
separate Dilemma-side evaluation at its pinned model revision, it scored 14/16
chunks across small independent Classical, Katharevousa, and Standard Modern
fixtures (87.5%): 75% on Classical, 75% on Katharevousa, and 100% on the Modern
fixtures.  Its model card reports Wiki data in training, so the Modern result
has source-family leakage risk; it also exposes no Medieval class.  For these
reasons no OGC gate above accepts a row solely from its classifier label.
