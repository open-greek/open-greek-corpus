# Open Greek Corpus

An open corpus of ancient Greek: openly-licensed digital editions where they
exist, our own OCR of public-domain editions where they don't. The goal is a
free counterpart to the subscription corpora, with every ancient Greek work
available one way or the other.

Companion repo:
[byzantine-early-modern-corpus](https://github.com/open-greek/byzantine-early-modern-corpus)
covers Byzantine and early modern vernacular Greek; this one covers Homer through
Byzantine literary Greek.

## Sources

| source | license | role |
|---|---|---|
| [First1KGreek](https://github.com/OpenGreekAndLatin/First1KGreek) | CC BY-SA 4.0 | first-millennium Greek TEI editions |
| [Perseus canonical-greekLit](https://github.com/PerseusDL/canonical-greekLit) | CC BY-SA 4.0 | the classical canon, TEI |
| [Galenus Verbatim](https://github.com/galenus-verbatim/galenus_cts) | CC BY-SA 4.0 | Galen and pseudo-Galen TEI (Sorbonne): verified Kuehn transcriptions plus revised First1K files (`galenus_verbatim`) |
| Byzantine and early modern | PD / CC BY-SA | late vernacular verse/prose, 12th-17th c. (`byzantine_vernacular`) |
| [byzantium.gr](https://byzantium.gr) | PD (Bonn/CSHB editions) | Byzantine historians, clean polytonic transcriptions (`byzantium_gr`) |
| [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | CC BY 4.0 | patristic gap: CC-BY OCR of public-domain Migne (`cgpg`) |
| [PTA](https://github.com/PatristicTextArchive/pta_data) | CC BY-SA / CC BY, per file | Patristic Text Archive (BBAW): critical patristic TEI incl. the Severian of Gabala corpus (`pta`); pta ids resolve via `scripts/build_pta_crosswalk.py`, the single BY-NC-SA file is excluded |
| [DFHG](https://dfhg-project.org) | CC BY-SA 4.0 | Mueller's Fragmenta Historicorum Graecorum vols 1-5 as corrected transcription (Berti/Leipzig), superseding our FHG OCR (`dfhg`); ingested by `scripts/ingest_dfhg.py`; the held-back specials (Diodorus' fragmentary books, homonym collisions) are resolved by `scripts/ingest_dfhg_specials.py`, and the carve slugs get TLG urns from the constrained canon pass `scripts/build_dfhg_canon_pass.py` (audit trail in `data/dfhg_canon_pass.json`) |
| [SAWS](https://ancientwisdoms.ac.uk) | CC BY 4.0 (2025 KCL figshare deposit, doi:10.18742/28259054.v1; supersedes the project's 2013 in-file CC BY-NC-SA notices) | Sharing Ancient Wisdoms born-digital editions (`saws`): Roueche's Kekaumenos, the Searby et al. Apophthegmata et gnomae secundum alphabetum, and diplomatic transcriptions of the Gnomologium Vaticanum (Vat. gr. 743) and Corpus Parisinum VI (Par. gr. 1168 + Bodl. Digby 6); ingested by `scripts/ingest_saws.py` (which re-verifies the deposit license against the figshare API on every fetch) |
| [Greek Wikisource](https://el.wikisource.org) | PD base text; contributor layer CC BY-SA 4.0 | Proclus, Institutio physica (tlg4036.tlg006): the proofread-page transcription of Ritzenfeld's Teubner 1912 edition (the TLG edition), ingested per DjVu page by `scripts/ingest_proclus_institutiones.py` (which also ingests the Institutio theologica, tlg4036.tlg005, from our Qwen3.6 OCR of the Didot 1855 Creuzer-Moser text - no clean open digital text exists - and writes a same-edition 29-page OCR witness of the physica to `corpus_secondary` with per-page agreement stats). Also serves the Septuagint Ecclesiastes (`septuaginta.ecclesiastes`, tlg0527.tlg030): the verse-keyed el.wikisource LXX transcription, ingested by `scripts/ingest_wikisource_ecclesiastes.py`. Ecclesiastes is the one LXX book absent from First1K (an empty `__cts__` stub upstream), and the Wikisource text is an ecclesiastical-recension LXX (Δαβίδ), so it differs orthographically from the First1K Swete siblings (Δαυείδ). Also serves Musaeus Grammaticus, Hero and Leander (`musaeus-grammaticus.hero-et-leander`, tlg4082.tlg001): the complete continuous-verse transcription, ingested by `scripts/ingest_musaeus_hero_leander.py`, replacing a broken redo OCR of Dilthey 1874 (the page names no printed edition, so it is the PD ancient poem, not a claim on Dilthey/Kost/Livrea) |
| [GLAUx](https://github.com/alekkeersmaekers/glaux) | PD base text; GLAUx corpus CC BY-SA 4.0 | Julius Pollux, Onomasticon (`julius-pollux.onomasticon`, tlg0542.tlg001): the full ten-book text (1,908 sections, ~115k Greek tokens), reconstructed from the GLAUx surface `<word>` forms in document order and keyed by GLAUx's `div_book`/`div_section` metadata, ingested by `scripts/ingest_glaux_pollux.py`, replacing a First1KGreek two-section sample (111 tokens). GLAUx is otherwise used only offline, for the Bekker concordance milestones below |
| our OCR of PD editions | PD | Migne PG and classical editions OCR'd from public-domain scans (`ocr`); per-work download links in the OCR provenance table below |
| [Opera Graeca Adnotata](https://doi.org/10.5281/zenodo.14206061) | CC BY-SA 4.0 | metadata only, no text (the OGA texts are the Perseus / First1KGreek / PTA editions above): per-work composition dating and the PTA/TLG duplicate map, ingested by `scripts/ingest_oga_metadata.py`; pinned by version DOI in `sources/oga/manifest.json` |

No non-commercial (CC BY-NC-SA) texts. A work only available under NC counts as
a gap and gets sourced from a public-domain edition instead
(`data/needs_pd_or_ocr.json`).

## Source precedence

When more than one open route covers a work, the served text is chosen by this
ladder (best first):

| rank | best_source | what it is |
|---|---|---|
| 1 | `open_corpus` | open TEI edition (First1KGreek / Perseus / Galenus Verbatim, CC BY-SA) |
| 2 | `byzantium_gr` | clean manual transcription of a PD edition (byzantium.gr, Bonn/CSHB) |
| 3 | `migne_cgpg` | CC-BY OCR of a PD edition (calfa-co Patrologia Graeca) |
| 4 | `pd_edition` | a PD edition we would OCR ourselves |
| 5 | `migne_pd` | Migne PD per the Canon's MPG pointer, text not yet in hand |

Two tie-breaks: a manual transcription beats OCR of the same text (byzantium.gr's
Bonn text wins over CGPG's Migne OCR for the Byzantine historians), and TLG text
is never served, only used offline as inventory and QA reference. Per-work
exceptions to the ladder live in `data/source_overrides.json` with their reason
and evidence; they win over the sourcing map.

The ladder ranks open TEI above OCR only for comparable coverage: when the open
corpora hold just a fragmentary stub of a work we serve in full from an OCR
delivery, the served text stays primary. `data/non_tei_authoritative.json` lists
those works explicitly (a TEI rebuild skips them), and `build_corpus_loci.py`
also refuses to overwrite any non-TEI work that has 1.5x the TEI candidate's
Greek tokens, reporting it in `data/corpus_loci_skips.json` for review instead
of clobbering it last-writer-wins.

```
scripts/build_source_overrides.py   pd_research sweeps -> data/source_overrides.json
scripts/source_precedence.py        the ladder + resolve(): applies overrides on top
                                     of sourcing_map.csv (used by coverage + registry)
```

`build_source_overrides.py` rebuilds the override list from the coverage sweeps
in `data/pd_research/`. Registry and coverage report both go through
`source_precedence.resolve()`, so they can't disagree. One correction it applies:
the vendored sourcing map credits CGPG for any work whose Migne volume number
matches, but CGPG only OCR'd 33 volumes/parts, so works in volumes CGPG never
digitised get demoted from `migne_cgpg` back to `migne_pd`. New sourcing
decisions go into a sweep (or the generator), then rerun; verdicts are never
hand-edited.

## What's here

```
Makefile                    the regenerate chain: ingest -> yardstick -> sourcing
scripts/
  build_corpus_loci.py      TEI -> per-work locus-keyed passages (ingest)
  build_bekker_concordance.py  GLAUX + el.wikisource + Bekker-1831 page OCR ->
                            data/bekker_concordance.json (Bekker pages for
                            tlg0086 works whose TEI lacks milestones;
                            content-aligned, consumed by the ingest)
  build_byzantine_vernacular_corpus.py  Byzantine and early modern -> locus-keyed passages (ingest)
  build_byzantium_gr_corpus.py byzantium.gr historians -> per-work passages (ingest)
  build_public_corpus.py    data/corpus/*.jsonl -> form lexicon + coverage (yardstick)
  build_lemma_frequency.py  lexicon -> per-lemma corpus frequency (via Dilemma)
  build_work_lemma_counts.py  data/corpus -> per-work x lemma matrix + lemma frequency,
                            INCREMENTAL via data/cache/ (only new/changed works
                            re-tokenize; only never-seen forms lemmatize). Split
                            phases for remote GPU: --emit-missing / --lemma-map
  lemmatize_forms.py        forms list -> form/lemma TSV (self-contained, for a
                            GPU box; resumable)
  rebuild_matrix_remote.sh  the whole incremental rebuild with the lemmatization
                            phase on CORSAIRONE (run from the Mac; SHARDS=N for
                            parallel GPU workers)
  build_provenance.py       OCR works -> the provenance table in this README
  build_ocr_quality_report.py  every OCR-source work -> data/ocr_quality_report.json:
                            unattested-token rate (the ocr_llm_correct.py suspect
                            filter) + witness-agreement estimates against
                            corpus_secondary, with a worst-first triage ranking
  reconcile_cgpg_works.py   re-derive each cgpg_works.json work-unit's serving
                            status from corpus_editions (cgpg_chosen /
                            superseded_by); the vendored file is never hand-edited
  build_source_overrides.py pd_research sweeps -> data/source_overrides.json
  source_precedence.py      the ladder + resolve() (used by registry + coverage)
  build_registry.py         inventory + overrides -> source_registry.json;
                            whole-volume corpus keys (ocr.*, cogPG.*: Migne
                            volumes, Walz Rhetores Graeci, Mansi acta, edition
                            remainders) are filed under their real authors via
                            the curated data/pseudo_author_attributions.json
                            (per-volume evidence inside), never under the old
                            anon-ocr / anon-cogPG pseudo-authors. Also applies
                            OGA dating (data/oga_dating.json): fills a missing
                            century/era tag, flags conflicts, audit in
                            data/oga_dating_report.json
  ingest_oga_metadata.py    Opera Graeca Adnotata v0.2.0 metadata -> per-work
                            dating (data/oga_dating.json), the PTA/TLG duplicate
                            map (data/oga_duplicates_tlg_pta.json), and the source
                            pin (sources/oga/manifest.json). Reads $OGA_ROOT
                            (default ~/Documents/oga); run after `make ids`
  export_oga_annotations.py OGA v0.2.0 clone -> the standardized annotation-export
                            payload (queue item 1a) + the git-tracked pointer stub
                            data/annotations/oga/<release>.json; the payload dir is
                            gitignored (docs/annotation-export-contract.md, "Storage")
  export_glaux_annotations.py  pinned GLAUx clone -> the standardized annotation-export
                            payload (queue item 1e, GLAUx half) + the pointer stub
                            data/annotations/glaux/<release>.json; drops the 25 PROIEL
                            works, excludes NC and unclear source licenses, tags Gorman
                            manual sentences provenance=gorman (docs/source-policy.md)
  export_diorisis_annotations.py  retained Diorisis figshare copy (pinned zip) ->
                            the standardized annotation-export payload (queue item
                            1e, Diorisis half) + the pointer stub
                            data/annotations/diorisis/<release>.json; Beta Code ->
                            Unicode, lemma+morphology only (no head/deprel), every
                            sentence analysis=auto (docs/source-policy.md tier 3)
  upload_annotation_export.py  publish an export release dir to the HF dataset repo
                            ciscoriordan/open-greek-corpus-annotation-exports under
                            <release-id>/ (Hub API, verified file list; never git-LFS)
  build_coverage_report.py  sourcing_map + overrides + corpus -> coverage_report.json
  build_crosswalk_report.py registry -> crosswalk_report.json (id-linkage completeness)
  build_id_registry.py      mint/maintain the opaque ogc/oga id ledgers
                            (work_ids.json / author_ids.json), append-only and
                            idempotent; replays the rename seed so ids survive
                            re-attribution (--check-stable asserts a no-op re-run)
  build_work_index.py       ledgers + crosswalk + registry + corpus_editions ->
                            work_index.json (reader-facing WEMI join + redirects)
  rename_work.py            the ONE id-preserving way to rename a work's slug
                            (moves file + rows + crosswalk/registry keys, records
                            the rename, re-derives the ledger); see
                            docs/opaque-identifiers.md
  validate_id_layer.py      assert every id-layer invariant (coverage, append-only,
                            anchor round-trip, variant pairs, redirects)
  normalize_edition_strings.py  collapse stacked qwen36 edition-tag repeats
                            (re-swap artifacts) across data/corpus[_secondary]/ +
                            ocr_works.json + ocr_edition_sources.json; dry-run by
                            default, --apply writes the audit mapping to
                            data/inventory/edition_string_normalization.json
  (OCR recognition, ingest and correction happen upstream and deliver text here)
docs/
  identity-and-citation.md  how cog identifies works/authors + cites passages
  opaque-identifiers.md     the ogc/oga id model, WEMI leveling, rename/redirect
                            layer, and the work_index.json schema a consumer needs
  source-policy.md          governance for external annotation corpora: openly-
                            licensed only, the PROIEL three-tier rule, and the
                            Gorman tag-don't-delete rule
  annotation-export-contract.md  cog's role as the annotation standardization
                            layer: the CTS-URN-keyed token record schema, encoding
                            guarantees, versioning, and the consumption worklists
  pinning-discipline.md     one owner per fact: cog pins upstreams (version DOI +
                            checksums / commit SHA + clone), consumers pin cog
                            (export vN + hash)
sources/                    cloned open corpora (gitignored; fetch with the commands below)
data/
  corpus/<work>.jsonl       one JSON record per citable passage (locus + text;
                            optional bekker[], text_lines[] - see record shape below)
  annotations/oga/oga-v1.json  pointer stub for the standardized OGA annotation
                            export (queue item 1a): release id, content hash, pin
                            line, HF location, upstream pin. The payload (per-work
                            works/<cts-id>.jsonl.gz token records + manifest.json +
                            pta_license_audit.json) lives on the HF dataset repo
                            ciscoriordan/open-greek-corpus-annotation-exports under
                            oga-v1/, never in git (docs/annotation-export-contract.md,
                            "Storage"); built by export_oga_annotations.py, published
                            by upload_annotation_export.py
  bekker_concordance.json   tlg0086 locus -> Bekker pages for works whose TEI has
                            no inline milestones (GLAUX + el.wikisource, CC BY-SA)
  work_ids.json             opaque ogc work-id ledger: id -> slug, former_slugs, status
  author_ids.json           opaque oga author-id ledger: id -> slug, former_slugs, status
  work_id_aliases.json      curated rename seed (former slug -> current); the source
                            of truth for renames, replayed by build_id_registry.py
  lettered_subedition_slugs.json  curated slugs for lettered TLG sub-edition ids
                            (tlg0007.tlg082a etc., split out of a parent canon work;
                            the canon has no entry for a lettered id), consumed by
                            build_id_crosswalk.py
  corpus_changes/           audit trail for editorial changes to the served corpus
                            (source swaps, drops, re-attributions): per change a JSON
                            with old/new + evidence + date + the script that applied it,
                            and the replaced/dropped rows archived verbatim (reversible).
                            A record with provenance.consolidated_from also STEERS the
                            TEI ingest: build_corpus_loci.py skips source works a served
                            consolidation consumed, so a rebuild cannot re-serve them
                            as raw-keyed duplicates
  work_index.json           reader-facing WEMI join: per work the ogc id, slug,
                            former slugs, CTS/TLG/Wikidata anchors, author (oga +
                            authorities), edition/source/tokens, plus a redirects map
  corpus_editions.json      per work: opaque id, winning edition/source/license, passages, tokens
  public_lexicon.tsv        form <TAB> count over the whole ingested corpus
  coverage.json             per work urn: source, license, tokens, passages
  public_lemma_frequency.tsv  lemma <TAB> corpus token count (the headline artifact)
  source_overrides.json     per-work source-precedence exceptions (+ reason)
  collection_serving_map.json  curated: sourcing-map collection URNs (e.g. Libanius
                            Orationes) served as per-part corpus files with no
                            shared TLG anchor; the coverage report credits the
                            summed parts instead of listing the URN as a gap
  partial_ceilings.json     curated + title rule: partial/underfilled works whose
                            missing words are copyright-capped (expected count
                            follows a locked modern edition); the coverage report
                            splits missing words into actionable vs structural
  non_tei_authoritative.json  works a TEI rebuild must never overwrite (a served
                            OCR/other delivery beats a fragmentary TEI copy)
  oga_dating.json           OGA per-work composition dating (CTS-URN -> ISO date +
                            date-label) resolved to cog slugs, with a derived
                            signed century + era; feeds build_registry.py
  oga_dating_report.json    audit of the OGA dating applied to the registry:
                            filled / agreed / conflicts (both readings kept)
  oga_duplicates_tlg_pta.json  OGA PTA<->TLG duplicate-work map, each side resolved
                            to a cog slug and flagged (same-slug / live-duplicate /
                            one-side / neither); a dedup reference, not a merge order
  corpus_loci_skips.json    ingest-run diagnostics: keep-list skips, clobber-guard
                            skips, foreign works a TEI edition replaced
  cgpg_works.json           CGPG Migne volume -> TLG works it covers
  byzantium_gr_works.json   byzantium.gr works ingested (per TLG work)
  corpus_loci_warnings.json works whose citation structure is not fully clean
  corpus_loci_disambiguated.json distinct readings that shared a locus, and the
                            loci they were split to (base -> [loci] + basis)
  crosswalk_report.json     per-namespace id-linkage coverage + enrichment targets,
                            both registry-wide and over the served set (the honest
                            denominators: served works joined to work_index anchors)
```

## Identity and citation

Every served work-unit and author carries an opaque, immutable, cog-minted id -
`ogc<NNNNNN>` for a work, `oga<NNNNNN>` for an author (Wikidata's Q-number move,
in our own namespace). The `author.work` slug (`homerus.ilias`) is demoted from
primary key to a human-readable, resolvable *alias* of that id: still the
filename and handle, no longer the identity. That split is what lets a
re-attribution change the slug without losing identity - the id stays put and the
old slug becomes a `former_slug` redirect (the data-side of a 301). The ledgers
are `data/work_ids.json` / `data/author_ids.json`, built idempotently and
append-only by `scripts/build_id_registry.py`; the reader-facing WEMI-leveled
join (id, slug, former slugs, CTS/TLG/Wikidata anchors, author authorities,
edition, source, tokens) is `data/work_index.json` via
`scripts/build_work_index.py`; renames go through the one id-preserving tool
`scripts/rename_work.py`; `scripts/validate_id_layer.py` checks every invariant.
Full model, WEMI leveling, and the index schema a consumer needs:
`docs/opaque-identifiers.md`.

External identifiers (TLG/CTS, Wikidata QID, VIAF/GND/ISNI, Trismegistos) are
kept as crosswalk aliases at their FRBR level, so nothing is anchored to the
proprietary TLG Canon: the bare TLG author.work number is a Work-level anchor
(the only external id with ~100% work coverage), and the opaque `ogc` id sits
one level finer at the Expression, so the 4 TLG variant-edition pairs are two
distinct `ogc` ids sharing one TLG anchor. 390 served works have no external id
at all (the exceed-TLG material) and rely on the `ogc` id alone. The TLG/CTS
crosswalk lives in `data/tlg_crosswalk.tsv` and in each work's `cts` field in
`corpus_editions.json` (which now also carries the `ogc` `id`), so joins against
citation and lexicon data still work. `build_crosswalk_report.py` reports how
complete the crosswalk is and where enrichment is cheapest (e.g. the author has a
Wikidata QID but the work doesn't). Why TLG numbers are kept as aliases rather
than dropped: `docs/identity-and-citation.md`.

Canon titles stored in beta-code (`*AI)GU/PTIOS`) are decoded to Unicode at
registry build (`Αἰγύπτιος`), including Greek glosses inside Latin titles
(`De Figuris (Περὶ σχημάτων)`). Slugs stay ASCII. Needs the `betacode` library
(see Build).

CGPG text is keyed by Migne volume (`cogPG.<vol>`, several works per volume, no
clean page split) and credited to its works via `cgpg_works.json`; byzantium.gr
historians are single works and key by their slug directly.

Passage citations follow CTS-URN logical-locus semantics (`source_identity.py`,
`parse_ref`): dot-separated levels (`book.chapter.line`), ranges with matching
depth on both ends (`5.84-5.116`, never `5.84-116`). `Locus` validates the
grammar on construction; `locus_for_citation(..., validate=True)` also checks
depth against the edition's declared citation scheme. The crosswalk report's
`served_canonical_locus` counts works whose bare citations resolve against an
edition we actually serve (`default_edition`); it runs well below the
any-edition count because most works' logical scheme sits on a reference-only
TLG edition.

## Build

```bash
python3 -m venv .venv && .venv/bin/pip install lxml betacode
git clone --depth 1 https://github.com/OpenGreekAndLatin/First1KGreek.git sources/first1k
git clone --depth 1 https://github.com/PerseusDL/canonical-greekLit.git   sources/perseus
git clone --depth 1 https://github.com/galenus-verbatim/galenus_cts.git   sources/galenus_verbatim
git clone --depth 1 https://github.com/PatristicTextArchive/pta_data.git  sources/pta
for v in volume_1 volume_2 volume_3 volume_4 volume_5_1 volume_5_2; do    # DFHG
  git clone --depth 1 "https://github.com/dfhg-project/$v.git" "sources/dfhg/$v"; done
python scripts/ingest_saws.py --fetch     # SAWS figshare deposit -> sources/saws (md5-verified)
python scripts/ingest_wikisource_ecclesiastes.py --fetch --apply   # LXX Ecclesiastes from el.wikisource
make                       # full chain; or a single stage:
make yardstick             # data/corpus/*.jsonl -> public_lexicon.tsv + lemma frequency
make sourcing              # source_overrides.json -> registry + coverage report
PY=.venv/bin/python DILEMMA=/path/to/dilemma make   # override interpreter / lemmatizer path
```

The chain is ingest, then the yardstick rollup, then the sourcing verdict (see
the Makefile header). Ingest (`build_corpus_loci.py`) walks each open TEI
edition, drops headers, editorial notes and apparatus, excludes NC/unknown
licenses, and dedups works that appear in more than one source: more tokens
wins, except part-editions covering disjoint book ranges get merged so a
multi-volume work isn't truncated to one part. When the same work+version id
arrives from two sources (Galenus Verbatim vendors First1K files, sometimes
revised), the live first1k copy is preferred unless the other carries at least
5% more Greek tokens - a material completion, never snapshot drift. Output is one record per citable
passage in `data/corpus/<work>.jsonl`, keyed by the dotted ref from the `div@n`
/ `<l n>` hierarchy (`1.1`, `1.327`, `4`, `21.6`). Drama and epic numbered every
fifth line are interpolated; text between numbered units lands at the next
coarser locus rather than being dropped. The winning CTS edition per work goes
to `corpus_editions.json`. `build_byzantine_vernacular_corpus.py` does the same
for the Byzantine and early modern texts. Text whose `@n` structure can't produce
a locus at all is listed in `corpus_loci_warnings.json` instead of being emitted
with garbage. When two passages resolve to the SAME locus the collision is
resolved by content, never dropped blindly: byte-identical repeats (a
re-presented figure poem, shared apparatus sigla) collapse to one row
(`collapsed_dup_loci`), while DISTINCT readings sharing a locus (a manuscript
recension like Dioscorides' RV redaction, an antilabe half-line, a nested-chapter
section clash) are kept as separate rows, the later one relocated to
`locus~tag` - `tag` a recension siglum where the text carries one, else a stable
ordinal - so no reading is lost (`disambiguated_dup_loci`; the base ->
[loci] + basis map is `corpus_loci_disambiguated.json`).

An oversized numbered div (more than 2,000 Greek tokens of passage text - the
CAG Aristotle commentaries, the NT catenae, the Chronicon Paschale, works
scholarship cites by edition page, not by whole-book div) whose TEI carries at
least two distinct numbered `<pb n=.../>` page breaks is served as one row per
edition page instead of a single blob: the locus becomes the div's citation
plus the page number (Simplicius In Physica book `1` -> `1.1` ... `1.226`),
text before the div's first page break files under the page already in effect
(or under `init` when none has begun), and a repeated page number within one
div gets a `-2`/`-3` suffix. Only the edition's own pagination splits: a `<pb>`
with `@ed` (an alternate edition's interleaved pages) is ignored, and a page
break falling inside a word (PTA's `break="no"` hyphenation breaks) switches at
the next word boundary so the straddling word stays on the page it starts on.
The per-page rows rejoin to the unsplit passage verbatim (checked at build; a
div that fails the check is served unsplit and reported). Split rows carry
neither `bekker` nor `text_lines`. The Bekker-cited Aristotle corpus is
excluded and keeps its current rows: page-level citability there is the
`bekker` field, whose concordance joins on the served locus.

Each record is `{urn, edition, locus, source, license, text}` plus, when
applicable, these additive optional fields (none affects locus keying):

- `bekker` - list of the Bekker canonical pages (with column letter, e.g.
  `["498a", "498b"]`) whose text falls in that passage, in first-appearance
  order, for the Aristotle corpus (`tlg0086`). It resolves a citation like
  `Arist.EN 1094a` even though the locus keying is `book.section`; a milestone
  can fall mid-section and a section can span several Bekker pages (~22% of
  Bekker-bearing rows span >1 page, up to 8 in the Metaphysics), so the full
  covered set is listed, not just the starting page. Two sources feed it: inline
  `<milestone unit="page" resp="Bekker">` markers in the source TEI (First1K and
  Perseus), and - for the 25 tlg0086 works whose TEI carries no such milestones
  (Historia animalium, De partibus/generatione animalium, Physica, De anima,
  Topica, the Parva naturalia, Magna Moralia, ...) -
  `data/bekker_concordance.json`, built by `build_bekker_concordance.py` from
  GLAUX and el.wikisource (both CC BY-SA) plus per-page OCR of the Bekker 1831
  edition itself (PD; the 8 works the first two miss: De sensu, De memoria, De
  somno, De insomniis, De longitudine, De juventute, De spiritu, Magna
  Moralia), all content-aligned (never chapter-number-aligned) to the served
  rows. Milestones take precedence per row; the concordance only fills rows a
  milestone left empty, so it never overrides. `Res publica Atheniensium`,
  `Divisiones Aristoteleae` (recorded not-a-gap in the concordance `_meta`),
  the Epistulae, and the two variant-recension texts have no Bekker pagination
  at all (not gaps).
- `text_lines` - the passage split into its printed/verse lines: a list of >=2
  segments cut at TEI `<lb/>` line breaks and at verse `<l>` lines that ride
  inside a coarse citable div (an inset quotation not cited as its own row).
  `' '.join(text_lines)` reconstructs `text` verbatim (a pure segmentation,
  asserted at emit; omitted otherwise), so `text` stays the flat citable string
  while the physical line structure is recoverable. Omitted when a passage is a
  single line.
- `base_locus`, `witness` - present on a row whose locus was disambiguated
  because a DISTINCT reading shared its citation. `base_locus` is the shared base
  citation (the served `locus` is `base_locus~tag`); `witness` is the recension
  siglum (e.g. `RV`) when the split was by witness rather than a bare ordinal.
  Split on `~` to recover the base citation; a non-colliding row has neither field.
- `ocr_dpi` - provenance on OCR-delivered rows (`source: ocr`), set by the OCR
  ingest, not by `build_corpus_loci.py`.
- `rank: "secondary"`, `secondary_reason` - present in
  `data/corpus_secondary/<work>.jsonl` on a displaced edition (see below).

`build_public_corpus.py` rolls the whole ingested corpus into
`public_lexicon.tsv` and `coverage.json`; it is the only lexicon builder, so new
ingests flow into the yardstick automatically. `build_lemma_frequency.py`
lemmatizes the vocabulary and sums form counts onto lemmas. For spot checks:
`python scripts/build_corpus_loci.py --only tlg0012`.

## OCR text and provenance

Part of the corpus is OCR: the calfa-co Patrologia Graeca (`cgpg`) and our own
OCR of PD editions (`ocr`). Recognition and manual correction happen upstream;
this repo holds the resulting text in `data/corpus`, raw where uncorrected,
corrected where correction has caught up. The rollup treats OCR text like any
other source.

### Why the OCR runs on Qwen3.6-27B (2026-07)

The first OCR pass ran on a smaller fine-tuned vision model. Inside its
training distribution it was good, but our sources are pre-1930 public-domain
editions, and that is where it looked least: its training styles were modern
digital fonts, and on the archaic faces in our scans it failed systematically,
worst on the 19th-century French Didot faces (Ruelle's Damascius, the
Bussemaker-Daremberg Oribasius, Miller's Etymologicum Genuinum), which print
pi as the variant glyph ϖ and use an archaic tau sort. The first-generation
pass read ϖ as σ and that tau as λ: σφὸς for πρὸς, Πέμπλον for Πέμπτον, about
130 corrupted tokens per 1,000 words. No median CER surfaces a failure like
that; the affected volumes were unusable.

Newer general VLMs read those sorts natively. On the same worst-case pages,
zero-shot Qwen3.6-27B
([Qwen/Qwen3.6-27B-FP8](https://huggingface.co/Qwen/Qwen3.6-27B-FP8)) cuts the
typeface-error rate about 96% (130.5 to 5.4 per 1,000 words).

Migration status (2026-07): the first-generation pass has been fully retired.
All ~217 edition volumes plus the Patrologia Graeca and the earlier tier-4
volumes were re-OCR'd with Qwen3.6-27B; the served text now comes from that
pass wherever OCR is the source. The re-ingest was loss-verified per work (no
page-stem or fragment carrying real Greek is dropped) and added roughly +15%
Greek to the served PG text - most of it real text the first pass had missed
on facing-translation and dense pages, a smaller share being hallucinated
Greek emitted on blank or Latin-index leaves that the new pass correctly
omits. Corrections keyed to the retired text were retired in place
(reversible), and the LLM corrector's auto-apply was disabled in favor of
adjudication after a measured 25-40% auto precision. A few works on substitute
or truncated re-scans keep their original OCR where the new scan covers less.

A dense-class follow-up pass re-read the corpus's two-column lexica and scholia
(Hesychius, Moeris, pseudo-Zonaras, Stephanus of Byzantium, the scholia corpora,
others) through a geometric-column-mask pipeline: each page is split at its
ink-minimum gutter and the columns are OCR'd separately at 430 dpi with
Qwen3.6-27B-FP8, so a gloss or line number cannot bleed across the gutter into
the next lemma. Those works are slugged `qwen36-*_masked` and carry a per-work
provenance record (source scan, render DPI, column geometry) in
`data/ocr_provenance/`; the table below lists them with a masked-pipeline note.

A related fix from the same pass: cross-checking the OCR corpus against
First1KGreek/Perseus surfaced 22 major patristic works (Eusebius, Gregory of
Nazianzus, Theodoret, Basil's letters, others) that were being served from Migne
OCR even though open CC-BY-SA critical editions existed but had never been
ingested - the OCR and open-TEI pipelines wrote the same files last-writer-wins,
without enforcing the source-precedence ladder. Those now serve the critical
editions, with the Migne OCR kept as a secondary edition.

### Secondary editions (`data/corpus_secondary/`)

When a work gains a better primary source (e.g. an open TEI critical edition
appears for a work we had OCR'd), the displaced text is not deleted: if its
quality is usable it moves to `data/corpus_secondary/<work>.jsonl`, same record
format plus `"rank": "secondary"` on every record. Secondary editions are NOT
served and are excluded from the lexicon, frequency and coverage rollups; they
exist as an independent witness (a different edition, often Migne where the
primary is a modern critical text) for collation and QA. First batch
(2026-07-05): 22 patristic works - Eusebius, Gregory of Nazianzus, Theodoret,
Basil's letters, and others - whose serving text switched from our Migne OCR to
First1KGreek/Perseus CC BY-SA editions.

The tool is `scripts/displace_to_secondary.py`: whole-work by default,
`--pages` to displace only a few page-stems that another work rightfully owns
(cross-slug page dedupe), or `--loci` (comma list or `@file`) to displace
exact records when the duplication is not page-aligned (e.g. an OCR remainder
page mixing rows covered by a served edition with apparatus rows that must
stay primary; row-level evidence for the DFHG dedup sheds is in
`data/dfhg_dedup_shed.json`). `--prune-crosswalk` additionally drops the slug's
`data/tlg_crosswalk.json` claim, for mis-ingested slugs whose file never
contained the claimed work (e.g. the Aeneas Tacticus volume that was serving as
Aeneas of Gaza, or the Parthenius volume serving as Antoninus Liberalis).

`scripts/dedup_fhg_containment.py` codifies the DFHG dedup shed's row-level
bigram-containment check (old FHG-scan work vs its served DFHG carve) as a
re-runnable tool; `--numfix` adds Greek-numeral normalization (keraia strip,
stigma/koppa/sampi letterforms). Passing rows displace via
`displace_to_secondary.py --loci` and append their evidence to
`data/dfhg_dedup_shed.json`.

### Reference material (`data/reference/`)

Alongside the served text corpus we keep a small amount of structured reference
material that is not running Greek text and so is not a served work (not in the
precedence ladder, not in the lexicon/frequency/coverage rollups, and it gets no
work id). First entry: Cunliffe's grammatical appendix, the conditional /
relative-sentence construction table at the end of Cunliffe's *A Lexicon of the
Homeric Dialect* (1924), which his lexicon entries cross-reference ("see Table
at end III.B.a") but which no digital edition reproduces. OCR'd from the
public-domain 1924 edition (archive.org `mdp.39015005687283`) and structured by
construction code, with every Homeric citation resolved (153 cells, 292
examples, 1,209 citations, cross-checked against the served Iliad). See
`data/reference/cunliffe-appendix/`.

`scripts/dissolve_pelagius_caag3.py` (2026-07-10) dissolved the pelagius
livraison-3 catch-all: the slug had served ALL of Berthelot-Ruelle, Collection
des anciens alchimistes grecs (texte grec, 1888) printed pp. 253-459, but only
pp. 253-261 are the Pelagius treatise (tlg2019.001). The other 76 canon works
of CAAG Parts IV-VI (Ostanes, Joannes Archiereus, Comarius, the Chimie de
Moise, the Part V recipes, Salmanas, the Philosophus Christianus, the
Anepigraphos, Cosmas, Hierotheus, Blemmydes, and the tlg1379 Fragmenta
alchemica) now serve under their own canon-derived registry slugs, boundaries
taken from the TLG canon's per-work CAAG page citations and asserted against
the section-head rows at runtime; the three zones already served by
First1KGreek TEI primaries (tlg4086.002, tlg2140.001, tlg2632.001) became
probe-verified secondary witnesses instead of new primaries.

`scripts/dissolve_svf3_catchalls.py` (2026-07-10) dissolved the TWO von Arnim
SVF vol. 3 volume-scope catch-alls: apollodorus-philosophy.fragmenta and
archedemus.fragmenta had each served a whole page-aligned scan of the same
1903 Teubner volume (printed pp. 3-269) under one successor's slug. The
Chrysippus zones (fragmenta moralia + both appendices) and the Diogenes
Babylonius and Antipater sections became probe-verified secondary witnesses
of their served First1KGreek TEI primaries (both scans); the true Apollodorus
Seleuciensis (printed 259-261) and Archedemus (262-264) zones keep their
slugs; Zeno Tarsensis (tlg2294.001), Basilides (tlg2398.001), Eudromus
(tlg2399.001) and Crinis (tlg1293.001) became new canon-verified primaries;
each zone's other-scan read is a same-print twin witness in corpus_secondary
(the dissolve_diels.py twin model); the Vol. II conspectus back matter went
to arnim-svf3-1903.paratexta. Audit + full row backups live in the upstream
OCR pipeline's data/corrections/svf3_catchall_dissolve/.

`scripts/rekey_novellae_by_novel.py` (2026-07-31) re-keyed the Justinian
Novellae (flavius-justinianus-imperator.novellae, the full Schoell-Kroll
Corpus Iuris Civilis III OCR) from scan-page loci to novel-number loci
(`<novel 1-168>.p<printed page>.<seg>`, plus `ed<1-13>.` for the Edicts,
`app.` for the Appendix and `praef.` for the Latin front matter), since every
citation scheme for the Novellae is novel-based (LSJ cites `Nov. 4.2`). Novel
boundaries come from a per-novel printed start page + line concordance
(structural headings of the TLG-E digitization of the same print, stigma/
koppa numeral repairs under strict monotonicity) embedded in the script and
confirmed against the OCR's own heading rows at a constant scan-printed
offset of 30; the 16 novels Schoell-Kroll transmits in Latin only have no
Greek heading, and their pages stay with the preceding novel. Text and row
order are untouched (asserted), the old keys are recoverable by formula
(scan = printed + 30), and the same run merged the stale `ocr_works.json`
rows left over from the contra-monophysitas mis-slug rescope. Audit:
`data/corpus_changes/flavius-justinianus-imperator.novellae.novel-rekey.json`.

After a work is renamed, re-scoped, or dissolved, run
`scripts/rekey_corrections_log.py --write`: it re-keys the read-only
`data/corrections_log/` audit mirror to the works now serving each row's page
locus (the upstream correction store lives in the separate OCR pipeline
repository and is not touched), so the audit linkage follows the rename. Page stems that boundary
splits left served by more than one work are adjudicated by a content
tiebreak (the correction's corrected/original text matched letter-boundary
against each candidate's rows at the exact locus, then anywhere on the stem,
then by sole locus holder); rows that stay genuinely ambiguous - e.g. a stem
double-served byte-identically by two works - are left unchanged and reported
AMBIGUOUS.

Per-work provenance (source scan, OCR model, correction status) is in the table
below; regenerate it with `python scripts/build_provenance.py`.

<!-- OCR-PROVENANCE:START -->
1158 OCR'd works/volumes: 39 manually corrected, 793 auto-corrected (deterministic glyph-confusion / frequency passes; edited but not hand-reviewed), 326 still raw OCR. Works are named by their author.work slug; the TLG/CTS mapping is in `data/tlg_crosswalk.tsv`.

| Work (slug) | Content | Downloaded | OCR model | Words | Correction |
|---|---|---|---|--:|---|
| achaeus.fragmenta | ΑΔΡΑΣΤΟΣ | nauck-tgf-ocr-frag | Qwen3.6-27B | 1,393 | raw OCR |
| acusilaus.testimonia-2 |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 456 | auto-corrected |
| aelius-dionysius.attika-o-no-mata |  | qwen36-aelius_dionysius_schwabe-ocr | Qwen3.6-27B | 32,071 | auto-corrected |
| aeneas-philosophy.epistulae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,842 | auto-corrected |
| aeneas-philosophy.theophrastus-sive-de-animarum-immortalitate-et-corporum-resurrectione | AENEAS GAZAEUS — Theophrastus sive de animarum immortalitate | qwen36-aeneasgazaeuset00zachgoog | Qwen3.6-27B | 24,806 | raw OCR |
| aeschines-socraticus.fragmenta |  | qwen36-aeschines_socr_dialogi_clericus | Qwen3.6-27B | 14,056 | auto-corrected |
| aeschylus-tragedy.fragmenta | ΩΣΦΡΑΖΟΜΕΝΟΝ ΡΟΨΙΝ ΖΗΤΩΝΤΑΣ ΨΥΧΗΝ ΞΕΝΩΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ ΤΟΥΤΟΝ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 16,868 | auto-corrected |
| agaclytus.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 147 | raw OCR |
| agathon-tragedy.fragmenta | ΑΛΚΜΕΩΝ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 897 | auto-corrected |
| alcaeus-comedy.fragmenta | ἈΔΕΛΦΑΙ ΜΟΙΧΕΤΟΜΕΝΑΙ | kock-caf1-ocr-frag | Qwen3.6-27B | 587 | raw OCR |
| alcaeus-lyric.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,251 | auto-corrected |
| alcmaeon.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 190 | raw OCR |
| alcmaeon.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,342 | auto-corrected |
| alcman.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,826 | auto-corrected |
| alexander-lyric.fragmenta |  | qwen36-alexander_aetolus_meineke | Qwen3.6-27B | 22,467 | auto-corrected |
| alexander-medicine.dedicatio-ad-cosman |  | qwen36-alex_trall_puschmann | Qwen3.6-27B | 43,278 | auto-corrected |
| alexander.fragmenta | ALEXANDER — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 225 | auto-corrected |
| alexis-comedy.fragmenta | ἈΓΩΝΙΣ Η ἸΠΠΙΣΚΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 10,170 | auto-corrected |
| ameinias.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 80 | raw OCR |
| amipsias.fragmenta | ἈΠΟΚΟΤΤΑΒΙΖΟΝΤΕΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 764 | raw OCR |
| amphis.fragmenta | ΑΛΕΙΠΤΡΙΑ | kock-caf2-ocr-frag | Qwen3.6-27B | 1,086 | auto-corrected |
| anacreon.fragmenta-2 |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 4,208 | auto-corrected |
| anacreontea.anacreontea |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,644 | auto-corrected |
| ananius.fragmenta | ANANIUS — Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 78 | raw OCR |
| anaxagoras.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,045 | auto-corrected |
| anaxandrides.fragmenta | ΑΝΑΞΑΝΔΡΙΔΗΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 2,566 | raw OCR |
| anaxarchus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,941 | auto-corrected |
| anaxilas.fragmenta | ΑΓΡΟΙΚΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 1,077 | auto-corrected |
| anaximander.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,482 | auto-corrected |
| anaximenes-philosophy.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,809 | auto-corrected |
| anaximenis-milesii-epistulae.epistulae |  | qwen36-aristaenetus_hercher_epistolographi-ocr | Qwen3.6-27B | 164 | raw OCR |
| anaxippus.fragmenta | ANAXIPPUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 613 | raw OCR |
| andreas.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 681 | raw OCR |
| andronicus-rhodius.de-passionibus-lib-1-sp |  | qwen36-andronicus_mullach_fpg3 | Qwen3.6-27B | 214,806 | auto-corrected |
| androtion.fragmenta | Fragmenta | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 119 | raw OCR |
| anonymi-in-oppiani-opera.in-oppiani-halieutica-exegesis-e-cod-paris-gr-2735 |  | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 430 dpi) | 4,653 | raw OCR |
| anthemius.dupuy-1777 |  | qwen36-anthemius_dupuy_1777 | Qwen3.6-27B | 2,413 | raw OCR |
| antidotus.fragmenta | ΑΔΗΛΟΥ ΔΡΑΜΑΤΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 91 | raw OCR |
| antigonus-paradoxography.historiarum-mirabilium-collectio |  | qwen36-antigonus_keller_rnsgm1 | Qwen3.6-27B | 24,618 | auto-corrected |
| antimachus-elegy.fragmenta |  | qwen36-antimachus_kinkel_egf1 | Qwen3.6-27B | 29,656 | auto-corrected |
| antiphanes.fragmenta | ΑΓΡΟΙΚΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 10,649 | auto-corrected |
| antiphon-soph.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,172 | auto-corrected |
| antiphon-tragedy.fragmenta | ΜΕΛΕΑΓΡΟΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 169 | raw OCR |
| antisthenes-atheniensis.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 68 | raw OCR |
| antisthenes.declamationes-fragmenta |  | qwen36-archytas_mullach_fpg2-ocr | Qwen3.6-27B | 8,550 | auto-corrected |
| antonius-diogenes.hercher |  | qwen36-antonius_diogenes_hercher | Qwen3.6-27B | 114,291 | auto-corrected |
| aphthonius.progymnasmata |  | qwen36-aphthonius_progymnasmata | Qwen3.6-27B | 14,490 | auto-corrected |
| apollodorus-cyzicenus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 36 | raw OCR |
| apollodorus-history.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 1,175 | auto-corrected |
| apollodorus-philosophy.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 712 | auto-corrected |
| apollodorus.fragmenta | APOLLODORUS — Fragmenta | kock-caf3-ocr | Qwen3.6-27B | 252 | raw OCR |
| apollodorus.fragmenta-2 | APOLLODORUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 68 | raw OCR |
| apollonius-philosophy.apollonii-epistulae-dub |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,380 | auto-corrected |
| apollonius-philosophy.apotelesmata-sp |  | qwen36-apollonius_parad_keller_v1 | Qwen3.6-27B | 22,908 | auto-corrected |
| apollonius-soph.lexicon-homericum |  | [archive.org](https://archive.org/details/apolloniisophis00bekkgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 47,144 | auto-corrected |
| apollophanes-comedy.fragmenta | ἈΠΟΛΛΟΦΆΝΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 322 | auto-corrected |
| apollophanes.fragmenta |  | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 105 | auto-corrected |
| aquila.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 14,656 | auto-corrected |
| araros.fragmenta | ΑΔΗΛΟΥ ΔΡΑΜΑΤΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 173 | raw OCR |
| arcadius.de-accentibus-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 46,716 | auto-corrected |
| arcesilaus-comedy.fragmentum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 16,762 | auto-corrected |
| archedemus.fragmenta |  | qwen36-archedemus_svf3 | Qwen3.6-27B | 610 | raw OCR |
| archedicus.fragmenta | ARCHEDICUS — Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 439 | raw OCR |
| archelaus-paradoxography.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 98 | raw OCR |
| archelaus-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,596 | auto-corrected |
| archestratus-parodius.fragmenta |  | qwen36-archestratus_brandt | Qwen3.6-27B | 16,607 | auto-corrected |
| archilochus.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 9,822 | auto-corrected |
| archippus-lysis-opsimus.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 331 | raw OCR |
| archippus.fragmenta | ἈΡΧΙΠΠΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 738 | raw OCR |
| archytas-philosophy.testimonia |  | qwen36-anaxagoras_diels_vs1 | Qwen3.6-27B | 6,887 | auto-corrected |
| aresas.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 589 | auto-corrected |
| aretades.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 178 | raw OCR |
| aristaenetus.epistulae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 200,293 | auto-corrected |
| aristaeus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 490 | auto-corrected |
| aristagoras-comedy.fragmenta | ἈΡΙΣΤΑΓΟΡΑΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 102 | raw OCR |
| aristarchus-ludwich |  | qwen36-aristarchus_ludwich | Qwen3.6-27B | 52,590 | auto-corrected |
| aristarchus.fragmenta |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 246 | raw OCR |
| aristias.fragmenta | ΚΤΚΑΩΨ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 243 | raw OCR |
| aristides-quintilianus-music.de-musica |  | qwen36-aristides_quintilianus_meibom | Qwen3.6-27B | 61,556 | auto-corrected |
| aristippus-cyrenaicus.sententiae-et-apophthegmata |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 6,852 | auto-corrected |
| aristobulus.fhg3 |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 39,438 | auto-corrected |
| aristocles-messanius.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 677 | auto-corrected |
| aristocles.fragmenta | Fragmenta | qwen36-nicostratus_fhg4 | Qwen3.6-27B | 678 | auto-corrected |
| aristomenes.fragmenta | ἈΡΙΣΤΟΜΕΝΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 364 | raw OCR |
| aristonicus-friedlaender |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,445 | auto-corrected |
| aristonymus.fragmenta | ἈΡΙΣΤΩΝΤΜΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 124 | raw OCR |
| aristophanes-byzantii-nauck |  | qwen36-aristophanes_byzantii_nauck | Qwen3.6-27B | 23,529 | auto-corrected |
| aristophanes-comedy.fragmenta-2 | ἈΡΙΣΤΟΦΆΝΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 17,558 | auto-corrected |
| aristophon.fragmenta | ΔΙΑΤΜΟΙ Η ΠΥΡΑΤΝΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 430 | raw OCR |
| arius-didymus.physica-fragmenta | ARIUS DIDYMUS — Physica (fragmenta, Diels Doxographi) | qwen36-doxographi-arius | Qwen3.6-27B | 7,947 | raw OCR |
| arnim-svf1-1905.paratexta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 95 | raw OCR |
| arnim-svf3-1903.paratexta |  | qwen36-archedemus_svf3 | Qwen3.6-27B | 77 | raw OCR |
| artemon-history.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 936 | auto-corrected |
| asclepiades.fragmenta | Fragmenta | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 1,409 | auto-corrected |
| asius.fragmentum-elegiacum |  | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 20 | raw OCR |
| astrampsychus-magus.astrampsychus-oracula-hercher |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,864 | auto-corrected |
| astydamas.fragmenta | ΕΡΜΗΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 447 | auto-corrected |
| athanasius-theology.de-corpore-et-anima-sp | 529 ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 987 | auto-corrected |
| athanasius-theology.de-incarnatione-contra-apollinarium-libri-ii-sp | 38 ΠΕΡΙ ΣΑΡΚΩΣΕΩΣ ΥΤΟΥ ΚΥΡΙΟΥ ΗΜΩΝ ΙΗΣΟΥ ΧΡΙΣΤΟΥ ΚΑΤΑ ΑΠΟΛΛΙΝΑΡΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,331 | auto-corrected |
| athanasius-theology.de-sabbatis-et-circumcisione-sp | ΠΕΡΙ ΣΑΒΒΑΤΩΝ ΚΑΙ ΠΕΡΙΤΟΜΗΣ, ΕΚ ΤΗΣ ΕΞΟΔΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,588 | raw OCR |
| athanasius-theology.de-sancta-trinitate-dialogi-1-3-5-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΔΙΑΛΟΓΟΣ ΠΕΡΙ ΤΗΣ ΤΡΙΑΔΟΣ, ΕΝ Ο ΔΙΑΛΕΓΟΝΤΑΙ ΟΡΘΟΔΟΞΟΣ ΚΑΙ ΑΝΟΜΟΙΟΣ ΑΡΕΙΑΝΙΣΤΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,989 | auto-corrected |
| athanasius-theology.de-sancta-trinitate-dialogi-2-and-4-sp | ΔΙΑΛΟΓΟΣ Εʹ ΠΕΡΙ ΑΓΙΑΣ ΤΡΙΑΔΟΣ, ΕΝ Ω ΔΙΑΛΕΓΟΝΤΑΙ ΟΜΟΙΩΣ ΟΡΘΟΔΟΞΟΣ ΚΑΙ ΑΝΟΜΟΙΟΣ ΑΡΕΙΑΝΙΣΤΗΣ (2). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,549 | auto-corrected |
| athanasius-theology.de-synodis-arimini-in-italia-et-seleuciae-in-isauria | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΕΠΙΣΤΟΛΗ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,145 | auto-corrected |
| athanasius-theology.de-virginitate-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΩΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,077 | auto-corrected |
| athanasius-theology.dialogi-duo-contra-macedonianos-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΚΑΤΑ ΑΙΡΕΣΕΩΝ ΔΙΑΦΟΡΩΝ ΛΟΓΟΙ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 19,792 | auto-corrected |
| athanasius-theology.disputatio-contra-arium-sp | 158 ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΔΙΑΛΟΓΟΣ ΕΝ ΤΗ ΚΑΤΑ ΝΙΚΑΙΑΝ ΣΥΝΟΔΩ ΠΡΟΣ ἈΡΕΙΟΝ (49). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,630 | auto-corrected |
| athanasius-theology.doctrina-ad-antiochum-ducem-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΔΙΔΑΣΚΑΛΙΑ ΠΡΟΣ ΑΝΤΙΟΧΟΝ ΔΟΥΚΑΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,624 | auto-corrected |
| athanasius-theology.doctrina-ad-monachos-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,128 | raw OCR |
| athanasius-theology.epistula-ad-adelphium | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ (77), ΕΠΙΣΤΟΛΗ ΠΡΟΣ ΑΔΕΛΦΙΟΝ ΕΠΙΣΚΟΠΟΝ ΚΑΙ ΟΜΟΛΟΓΗΤΗΝ, ΚΑΤΑ ΑΡΕΙΑΝΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,100 | auto-corrected |
| athanasius-theology.epistula-ad-afros-episcopos | ΚΑΙ ΤΟΥ ΜΑΚΑΡΙΟΥ ΑΘΑΝΑΣΙΟΥ ΚΑΤΑ ΑΡΙΑΝΩΝ ΠΡΟΣ ΤΟΥΣ ΕΝ ΤΗ ΑΦΡΙΚΗ ΤΙΜΙΩΤΑΤΟΥΣ ΕΠΙΣΚΟΠΟΥΣ 6 . | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,599 | auto-corrected |
| athanasius-theology.epistula-ad-epictetum | ΠΡΟΣ ΕΠΙΚΤΗΤΟΝ ΚΟΡΙΝΘΟΥ, ΚΑΤΑ ΤΟΝ ΑΙΡΕΤΙΚΟΝ ΕΠΙΣΤΟΛΑ (91). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,201 | raw OCR |
| athanasius-theology.epistula-ad-jovianum | 75 ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΠΡΟΣ ΙΟΒΙΑΝΟΝ ΠΕΡΙ ΠΙΣΤΕΩΣ 76 . | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,918 | raw OCR |
| athanasius-theology.epistula-ad-marcellinum-de-interpretatione-psalmorum | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΠΡΟΣ ΜΑΡΚΕΛΛΙΝΟΝ ΕΙΣ ΤΗΝ ΕΡΜΗΝΕΙΑΝ ΤΩΝ ΨΑΛΜΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,779 | auto-corrected |
| athanasius-theology.epistula-ad-maximum | ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΠΡΟΣ ΜΑΣΙΜΟΝ ΦΙΛΟΣΟΦΟΝ (21). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 959 | auto-corrected |
| athanasius-theology.epistula-ad-monachos-2 | ΤΟΥ ΕΝΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,422 | auto-corrected |
| athanasius-theology.epistula-ad-rufinianum | ΕΠΙΣΤΟΛΗ ΠΡΟΣ ΡΟΥΦΙΝΙΑΝΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 316 | raw OCR |
| athanasius-theology.epistula-catholica-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 438 | auto-corrected |
| athanasius-theology.epistula-festalis-xxxix-fragmentum-in-collectione-canonum | Epistula festalis xxxix (fragmentum in collectione canonum) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,316 | raw OCR |
| athanasius-theology.epistulae-ad-castorem-sp | ΤΟΥ ἈΥΤΟΥ ΜΕΓΑΛΟΥ ἈΘΑΝΑΣΙΟΥ ΠΡΟΣ ΚΑΣΤΟΡΑ ΤΟΝ ΜΑΚΑΡΙΟΤΑΤΟΝ ΠΕΡΙ ΤΟΝ ΚΑΝΟΝΙΚΟΝ ΤΟΝ ΚΟΙΝΟΒΙΟΝ ΔΙΑΤΥΠΩ‐ ΣΘΑΝ (37). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,831 | auto-corrected |
| athanasius-theology.epistulae-festales-ap-cosmam-indicopleustem | Epistulae festales (ap. Cosmam Indicopleustem) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 295 | auto-corrected |
| athanasius-theology.epistulae-quattuor-ad-serapionem | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΕΠΙΣΤΟΛΗ ΠΡΟΣ ΣΕΡΑΠΙΩΝΑ ΘΜΟΥΕΟΣ ΕΠΙΣΚΟΠΟΝ (71) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 22,675 | auto-corrected |
| athanasius-theology.expositiones-in-psalmos | ΤΟΥ ἉΓΙΟΥ ἈΘΑΝΑΣΙΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ ὙΠΟΘΕΣΙΣ ΕΙΣ ΤΟΥΣ ΨΑΛΜΟΥΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 207,275 | auto-corrected |
| athanasius-theology.fragmenta-varia | Fragmenta varia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,404 | auto-corrected |
| athanasius-theology.homilia-de-passione-et-cruce-domini-additamenta | ἈΘΑΝΑΣΙΟΥ ΕΙΣ ΤΟ ΠΑΘΟΣ (81) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 357 | raw OCR |
| athanasius-theology.homilia-de-passione-et-cruce-domini-sp | ΕΙΣ ΤΟ ΠΑΘΟΣ ΤΟΥ ΚΥΡΙΟΥ ΚΑΙ ΕΙΣ ΤΟΝ ΣΤΑΥΡΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,317 | auto-corrected |
| athanasius-theology.homilia-de-semente-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,034 | auto-corrected |
| athanasius-theology.homilia-in-occursum-domini-sp | ΧΟΙΟΣ ΕΙΣ ΤΗΝ ΥΠΑΝΤΗΝ ΤΟΥ ΚΥΡΙΟΥ, ΚΑΙ ΘΕΟΥ, ΚΑΙ ΣΩΤΗΡΟΣ ΗΜΩΝ ΙΗΣΟΥ ΧΡΙΣΤΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,941 | auto-corrected |
| athanasius-theology.homilia-in-passionem-domini-et-in-parasceve-sp | ΛΟΓΟΣ ΕΙΣ ΤΟ ΠΑΘΟΣ ΤΟΥ ΚΥΡΙΟΥ (20) ΤΗ ΑΓΙΑ ΠΑΡΑΣΚΕΥΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,365 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-andream-sp | ΕΓΚΩΜΙΟΝ ΕΙΣ ΤΟΝ ΑΓΙΟΝ ΑΝΔΡΕΑΝ ΤΟΝ ΑΠΟΣΤΟΛΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,038 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-pascha-et-in-recens-illuminatos-sp | ΕΙΣ ΤΟ ΑΓΙΟΝ ΠΑΣΧΑ ΚΑΙ ΕΙΣ ΤΟΥΣ ΝΕΟΦΘΙΣΤΟΥΣ ΤΩ ΣΑΒΒΑΤΩ ΤΗΣ ΑΠΟΛΥΣΙΜΟΥ ΛΟΓΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,959 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-pascha-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΔΟΓΟΣ ΕΙΣ ΤΟ ΑΓΙΟΝ ΠΑΣΧΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 945 | auto-corrected |
| athanasius-theology.in-caecum-nativitate-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,496 | auto-corrected |
| athanasius-theology.in-illud-profecti-in-pagum-invenietis-pullum-alligatum-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,691 | raw OCR |
| athanasius-theology.in-nativitatem-praecursoris-sp | ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,459 | auto-corrected |
| athanasius-theology.interpretatio-in-symbolum-sp | ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 311 | raw OCR |
| athanasius-theology.liber-de-definitionibus-sp | ΤΟΥΑΥΤΟΥΑΘΑΝΑΣΙΟΥ ΠΡΟΣ ΤΟΝ ΕΥΣΕΒΕ- ΣΤΑΤΟΝ ΒΑΣΙΛΕΑ ΙΟΒΙΑΝΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,126 | auto-corrected |
| athanasius-theology.narratio-de-cruce-seu-imagine-berytensi-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,965 | raw OCR |
| athanasius-theology.oratio-in-resurrectionem-et-in-recens-baptizatos-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,879 | raw OCR |
| athanasius-theology.orationes-tres-contra-arianos | ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 74,889 | auto-corrected |
| athanasius-theology.quaestiones-ad-antiochum-ducem-sp | C ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,388 | auto-corrected |
| athanasius-theology.quaestiones-aliae-sp | ΤΟΥ ΕΝ ΑΙΤΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΕΤΕΡΑΙ ΤΙΝΕΣ ΕΡΩΤΗΣΕΙΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,322 | auto-corrected |
| athanasius-theology.quaestiones-in-evangelia-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΡΗΕΙΕΣ ΚΑΙ ΕΡΜΗΝΕΙΑΙ ΠΑΡΑΒΟΛΩΝ ΤΟΥ ΑΓΙΟΥ ΕΥΑΓΓΕΛΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,491 | auto-corrected |
| athanasius-theology.quaestiones-in-scripturam-sacram-sp | ΕΚ ΤΟΥ ΠΑΛΑΙΟΥ ΔΙΑΦΟΡΟΙ ΕΡΜΗ‐ ΝΕΙΑΙ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,114 | auto-corrected |
| athanasius-theology.refutatio-hypocriseos-meletii-et-eusebii-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 604 | raw OCR |
| athanasius-theology.scholia-in-acta-fort-ex-libris-contra-novatianos | Scholia in Acta (fort. ex libris Contra Novatianos) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 520 | raw OCR |
| athanasius-theology.sermo-ad-antiochum-ducem-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΕΜΩΝ ΑΘΑΝΑΣΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ, ΠΡΟΣ ΑΝΤΙΟΧΟΝ ΑΡΧΟΝΤΑ (86) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,662 | auto-corrected |
| athanasius-theology.sermo-contra-latinos-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,851 | auto-corrected |
| athanasius-theology.sermo-contra-omnes-haereses-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΚΑΤΑ ΠΑΣΩΝ ΤΩΝ ΑΙΡΕΣΕΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,155 | auto-corrected |
| athanasius-theology.sermo-de-descriptione-deiparae-sp | ΕΙΣ ΑΠΟΓΡΑΦΗΝ (55) ΤΗΣ ΑΓΙΑΣ ΜΑΡΙΑΣ, ΚΑΙ ΕΙΣ ΤΟΝ ΙΟΣΗΦ, ΛΟΓΟΣ (56). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,639 | raw OCR |
| athanasius-theology.sermo-de-patientia-sp | ΤΟΥ ἈΥΤΟΥ ἈΘΑΝΑΣΙΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ, ΠΕΡΙ ΥΠΟΜΟΝΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,076 | auto-corrected |
| athanasius-theology.sermo-exhortatorius-sp-e-cod-paris-gr-769 | ΛΟΓΟΣ ΤΟΥ ΑΓΙΟΥ ΑΘΑΝΑΣΙΟΥ ΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,289 | auto-corrected |
| athanasius-theology.sermo-in-annuntiationem-deiparae-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,104 | auto-corrected |
| athanasius-theology.sermo-in-nativitatem-christi-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,627 | auto-corrected |
| athanasius-theology.sermo-pro-iis-qui-saeculo-renuntiarunt-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΤΟΥ ΜΕΓΑΛΟΥ ΠΑΤΡΙΑΡΧΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,820 | auto-corrected |
| athanasius-theology.symbolum-quicumque-sp | ΣΥΜΒΟΛΟΝ ΤΟΥ ΑΓΙΟΥ ΑΘΑΝΑΣΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,921 | auto-corrected |
| athanasius-theology.synopsis-scripturae-sacrae-sp | ΣΥΝΟΨΙΣ ἘΠΙΤΟΜΟΣ ΤΗΣ ΘΕΙΑΣ ΓΡΑΦΗΣ, ΠΑΛΑΙΑΣ ΚΑΙ ΝΕΑΣ ΔΙΑΘΗΚΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,130 | auto-corrected |
| athanasius-theology.syntagma-ad-monachos-e-cod-vossiano-gr-fol-46-sp | ΣΥΝΤΑΓΜΑ ΔΙΔΑΣΚΑΛΙΑΣ ΠΡΟΣ ΜΟΝΑΖΟΝΤΑΣ, ΚΑΙ ΠΑΝΤΑΣ ΧΡΙΣΤΙΑΝΟΥΣ, ΚΑΘΗΚΟΥΣ ΤΕ ΚΑΙ ΛΑΙΚΟΥΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,603 | raw OCR |
| athanasius-theology.syntagma-ad-quendam-politicum-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,901 | auto-corrected |
| athanasius-theology.testimonia-e-scriptura-de-communi-essentia-patris-et-filii-et-spiritus | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,680 | auto-corrected |
| athanasius-theology.vita-antonii | ΒΙΟΣ ΚΑΙ ΠΟΛΙΤΕΙΑ ΤΟΥ ΟΣΙΟΥ ΠΑΤΡΟΣ ΗΜΩΝ ΑΝΤΩΝΙΟΥ ΣΥΓΓΡΑΦΕΙΣ ΚΑΙ ΑΠΟΣΤΑΛΕΙΣ ΠΡΟΣ ΤΟΥΣ ΕΝ ΤΗ ΣΕΝΗ ΜΟΝΑΚΟΥΣ ΠΑΡΑ ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΑΘΑΝΑΣΙΟΥ ΕΠΙΣΚΟΠΟΥ ΑΛΕΧΑΝΔΡΕΙΑΣ (4). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,326 | auto-corrected |
| athanasius-theology.vita-sanctae-syncleticae-sp | ΒΙΟΣ ΚΑΙ ΠΟΛΙΤΕΙΑ ΤΩΣ ΑΓΙΑΣ ΚΑΙ ΜΑΚΑ- ΡΙΑΣ ΚΑΙ ΔΙΔΑΣΚΑΛΟΥ ΣΥΓΚΛΗΤΙΚΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,677 | auto-corrected |
| athanasius-theology.vitae-monasticae-institutio-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 726 | raw OCR |
| athenaeus-mechanics.de-machinis |  | qwen36-athenaeus_mech_wescher | Qwen3.6-27B | 46,412 | auto-corrected |
| atridarum-reditus.fragmenta |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 570 | auto-corrected |
| atridarum-reditus.fragmentum |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 5 | raw OCR |
| autocharis.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 82 | auto-corrected |
| autocrates-comedy.fragmenta | ΑΔΗΛΟΤ ΔΡΑΜΑΤΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 74 | raw OCR |
| axionicus.fragmenta | ΔΔΗΛΟΥ ΔΡΑΜΑΤΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 491 | raw OCR |
| basilides.fragmentum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33 | raw OCR |
| basilius-scr-eccl.de-vita-et-miraculis-sanctae-theclae-libri-ii-sp | ΛΟΓΟΣ ΜΑʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,678 | auto-corrected |
| basilius-scr-eccl.sermones-xli | A ΛΟΓΟΣ Α' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 69,629 | auto-corrected |
| basilius-theology.adversus-eunomium-libri-5 | ΒΑΣΙΛΙΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 45,481 | auto-corrected |
| basilius-theology.asceticon-magnum-sive-quaestiones-regulae-brevius | ΕΡΩΤΗΣΙΣ Γ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,567 | auto-corrected |
| basilius-theology.asceticon-magnum-sive-quaestiones-regulae-fusius | ΚΕΦΑΛΑΙΑ ΤΩΝ ΚΑΤΑ ΠΛΑΤΟΣ ΟΡΩΝ 39 . | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,063 | auto-corrected |
| basilius-theology.consolatoria-ad-aegrotum-sp-sub-auctore-proclo | ΤΟΥ ΑΥΤΟΥ (58) ΟΜΙΛΙΑ ΠΑΡΑΜΥΘΗΤΙΚΗ ΑΣΘΕΝΟΥΝΤΙ (59) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,791 | auto-corrected |
| basilius-theology.constitutiones-asceticae-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΒΑΣΙΛΕΙΟΥ· ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΑΙΣΑΡΕΙΑΣ ΚΑΠΠΑΔΟΚΙΑΣ· ΑΣΚΗΤΙΚΑΙ ΔΙΑΤΑΞΕΙΣ (55) , ΠΡΟΣ ΤΟΥΣ ΕΝ ΚΟΙΝΟΒΙΩ ΚΑΙ ΚΑΤΑΜΟΝΑΣ ΑΣΚΟΥΝΤΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,750 | auto-corrected |
| basilius-theology.contra-sabellianos-et-arium-et-anomoeos |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,681 | raw OCR |
| basilius-theology.de-baptismo-libri-duo | ΛΟΓΟΣ Αʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,638 | auto-corrected |
| basilius-theology.de-fide | De fide | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,017 | raw OCR |
| basilius-theology.de-humilitate |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,097 | auto-corrected |
| basilius-theology.de-jejunio-homilia-1 | ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΑΙΣΑΡΕΙΑΣ ΚΑΠΠΑΔΟΚΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,865 | auto-corrected |
| basilius-theology.de-jejunio-homilia-2 | ΠΕΡΙ ΝΗΣΤΕΙΑΣ ΛΟΓΟΣ Β’ 66 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,455 | auto-corrected |
| basilius-theology.de-jejunio-homilia-3-sp | ΤΟΥ ΑΥΤΟΥ ΠΕΡΙ ΝΗΣΤΕΙΑΣ ΛΟΓΟΣ Γ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,047 | auto-corrected |
| basilius-theology.de-spiritu-sancto | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΒΑΣΙΛΕΙΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΑΙΣΑΡΕΙΑΣ ΚΑΠΠΑΔΟΚΙΑΣ ΠΕΡΙ ΤΟΥ ΑΓΙΟΥ ΠΝΕΥΜΑΤΟΣ ΠΡΟΣ ΤΟΝ ΕΝ ΑΓΙΟΙΣ ΑΜΦΙΑΟΧΙΟΝ (19) ΕΠΙΣΚΟΠΟΝ ΙΚΟΝΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,720 | auto-corrected |
| basilius-theology.enarratio-in-prophetam-isaiam-dub | ΕἸΣ ΤΟΝ ΠΡΟΦΗΤΗΝ ΙΣΑΙΑΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 91,251 | auto-corrected |
| basilius-theology.epitimia-in-canonicas-epitimia-25-dub | ΚΕΦΑΛΑΙΑ ΔΙΑΤΑΞΕΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 814 | auto-corrected |
| basilius-theology.homilia-adversus-eos-qui-irascuntur | Homilia adversus eos qui irascuntur | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,221 | auto-corrected |
| basilius-theology.homilia-de-invidia | Homilia de invidia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,580 | auto-corrected |
| basilius-theology.homilia-de-misericordia-et-judicio-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,041 | raw OCR |
| basilius-theology.homilia-de-spiritu-sancto-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΒΑΣΙΛΕΙΟΥ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,526 | raw OCR |
| basilius-theology.homilia-dicta-in-lacisis | 87 ΟΜΙΛΙΑ ΦΗΘΕΙΣΑ ΕΝ ΛΑΚΙΖΟΙΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,184 | raw OCR |
| basilius-theology.homilia-dicta-tempore-famis-et-siccitatis | Homilia dicta tempore famis et siccitatis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,148 | auto-corrected |
| basilius-theology.homilia-exhortatoria-ad-sanctum-baptisma | Homilia exhortatoria ad sanctum baptisma | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,399 | auto-corrected |
| basilius-theology.homilia-in-divites | Homilia in divites | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,377 | auto-corrected |
| basilius-theology.homilia-in-illud-destruam-horrea-mea | ΕἸΣ ΤῸ ΠΤΟΝ ΤΟΥ ΚΑΤᾺ ΛΟΥΚΑΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,594 | auto-corrected |
| basilius-theology.homilia-in-illud-ne-dederis-somnum-oculis-tuis-sp | A ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΩΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,560 | auto-corrected |
| basilius-theology.homilia-in-principium-proverbiorum | Homilia in principium proverbiorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,969 | auto-corrected |
| basilius-theology.homilia-in-psalmum-37-sp | ΕἸΣ ἈΖʹ ΨΑΛΜΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,346 | auto-corrected |
| basilius-theology.homiliae-in-hexaemeron | ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΑΙΣΑΡΕΙΑΣ ΚΑΠΠΑΔΟΚΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,585 | auto-corrected |
| basilius-theology.homiliae-super-psalmos | ΟΜΙΛΙΑ ΕΙΣ ΤΟΝ ΠΡΩΤΟΝ ΨΑΛΜΟΝ (85) . | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 49,724 | auto-corrected |
| basilius-theology.in-barlaam-martyrem-sp | In Barlaam martyrem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 663 | auto-corrected |
| basilius-theology.in-ebriosos | In ebriosos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,427 | auto-corrected |
| basilius-theology.in-gordium-martyrem | In Gordium martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,480 | auto-corrected |
| basilius-theology.in-illud-in-principio-erat-verbum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,277 | raw OCR |
| basilius-theology.in-mamantem-martyrem | In Mamantem martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,697 | auto-corrected |
| basilius-theology.in-quadraginta-martyres-sebastenses | In quadraginta martyres Sebastenses | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,132 | auto-corrected |
| basilius-theology.in-sanctam-christi-generationem | ΟΜΙΛΙΑ ΕΙΣ ΤΗΝ ΑΓΙΑΝ ΤΟΥ ΧΡΙΣΤΟΥ ΓΕΝΝΗΣΙΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,803 | auto-corrected |
| basilius-theology.liturgia-recensio-brevior-vetusta | ΛΕΙΤΟΥΡΓΙΑ ΤΟΥ ΑΓΙΟΥ ΒΑΣΙΛΕΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,738 | auto-corrected |
| basilius-theology.orationes-sive-exorcismi-sp | ΕΥΧΑΙ ΗΤΟΙ ΕΞΟΡΚΙΣΜΟΙ ΤΟΥ ΜΕΓΑΛΟΥ ΒΑΣΙΛΕΙΟΥ ΠΡΟΣ ΤΟΥΣ ΠΑΣΧΟΝΤΑΣ ΥΠΟ ΔΑΙΜΟΝΩΝ, ΚΑΙ ΕΚΑΣΤΗΝ ΑΣΘΕΝΕΙΑΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,317 | auto-corrected |
| basilius-theology.poenae-in-monachos-delinquentes-epitimia-24-dub | ἘΠΙΤΙΜΙΑ ΕΙΣ ΤΑΣ ΚΑΝΟΝΙΚΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 268 | raw OCR |
| basilius-theology.prologus-3-prooemium-in-regulas-brevius-tractatas | 43 ΠΡΟΟΙΜΙΟΝ ΤΩΝ ΚΑΤ' ΕΠΙΤΟΜΗΝ ΟΡΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 587 | raw OCR |
| basilius-theology.prologus-4-prooemium-in-asceticum-magnum | ΤΟΥ ΑΥΤΟΥ ΟΡΟΙ ΚΑΤΑ ΠΛΑΤΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,940 | raw OCR |
| basilius-theology.prologus-5-sermo-asceticus-dub | ΤΟΥ ΑΥΤΟΥ ΛΟΓΟΣ ΑΣΚΗΤΙΚΟΣ (40) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,259 | auto-corrected |
| basilius-theology.prologus-7-de-judicio-dei |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,189 | raw OCR |
| basilius-theology.prologus-8-de-fide | TOY ΑΥΤΟΥ ΠΕΡΙ ΠΙΣΤΕΩΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,864 | auto-corrected |
| basilius-theology.quod-deus-non-est-auctor-malorum | Quod deus non est auctor malorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,800 | auto-corrected |
| basilius-theology.quod-rebus-mundanis-adhaerendum-non-sit | Quod rebus mundanis adhaerendum non sit | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,944 | auto-corrected |
| basilius-theology.regulae-morales | ἈΡΧῊ ΤΩΝ ΗΘΙΚΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,231 | auto-corrected |
| basilius-theology.sermo-10-praevia-institutio-ascetica-dub | Sermo 10 (praevia institutio ascetica) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 847 | auto-corrected |
| basilius-theology.sermo-11-sermo-asceticus-et-exhortatio-de-renuntiatione-mundi | Sermo 11 (sermo asceticus et exhortatio de renuntiatione mundi) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,675 | auto-corrected |
| basilius-theology.sermo-ob-sacerdotum-instructionem-recensio-brevior-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΒΑΣΙΛΕΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 598 | auto-corrected |
| basilius-theology.sermones-de-moribus-symeone-metaphrasta-collecti | ΔΙΑ ΣΥΜΕΩΝ ΤΟΥ ΜΑΓΙΣΤΡΟΥ ΚΑΙ ΛΟΓΟΘΕΤΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 47,824 | auto-corrected |
| beros-s-us.fragmenta |  | qwen36-demochares_fhg2-ocr | Qwen3.6-27B | 1,833 | auto-corrected |
| bion-history.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 55 | raw OCR |
| bion-mathematics.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 94 | raw OCR |
| bion-philosophy.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,670 | auto-corrected |
| blaesus.fragmentum | BLAESUS — Fragmentum | qwen36-sopater_kaibel_cgf-ocr | Qwen3.6-27B | 113 | raw OCR |
| boethus.fragmenta |  | qwen36-apollodorus_seleuc_svf3-ocr | Qwen3.6-27B | 588 | auto-corrected |
| boidas.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 84 | raw OCR |
| bolus.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 28 | raw OCR |
| brotinus.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 502 | auto-corrected |
| bryson.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 237 | raw OCR |
| butherus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 148 | raw OCR |
| callias.fragmenta | ΚΤΚΑΩΠΕΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 528 | raw OCR |
| callicratidas.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 1,325 | auto-corrected |
| callimachus.callimachea-schneider-v1 |  | qwen36-callimachea_schneider_v1 | Qwen3.6-27B | 18,215 | auto-corrected |
| callinus.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 149 | raw OCR |
| calliphon-et-democedes.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,463 | auto-corrected |
| callixenus.fragmenta |  | qwen36-fhg_vol3_mueller_diocles_rhodius-ocr | Qwen3.6-27B | 3,797 | auto-corrected |
| cantharus.fragmenta | ΚΑΝΘΑΡΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 149 | auto-corrected |
| carcinus-junior.fragmenta | ΑΜΦΙΑΡΕΩΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 665 | raw OCR |
| carmina-convivialia-pmg.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 4,944 | auto-corrected |
| carmina-popularia-pmg.fragmenta | CARMINA POPULARIA (PMG) — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,129 | auto-corrected |
| cephisodorus.fragmenta | ΚΗΦΙΣΟΔΩΡΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 288 | raw OCR |
| cercidas.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 351 | auto-corrected |
| cercops.testimonium |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 52 | raw OCR |
| chaeremon-history.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 929 | auto-corrected |
| chaeremon-tragedy.fragmenta | ΔΙΟΝΥΣΟΣ | nauck-tgf-ocr-frag | Qwen3.6-27B | 814 | raw OCR |
| charax.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 1,345 | auto-corrected |
| chariclides.fragmentum | CHARICLIDES — Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 103 | raw OCR |
| chionides.fragmenta | ΕΥΕΤΗΣ ΕΥΕΕΝΙΔΗΣ ΜΤΑΛΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 113 | raw OCR |
| choerilus-tragedy.fragmenta | 1 ΑΛΟΠΗ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 30 | raw OCR |
| choerilus.fragmenta-epica |  | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 826 | auto-corrected |
| choricius.opera |  | qwen36-choricius_boissonade | Qwen3.6-27B | 67,121 | auto-corrected |
| cinesias.fragmentum |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 100 | raw OCR |
| clearchus-comedy.fragmenta | ΚΙΘΑΡΩΙΔΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 177 | raw OCR |
| clearchus-philosophy.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 31,248 | auto-corrected |
| cleobulina-scriptor-aenigmatum.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 167 | raw OCR |
| cleostratus.testimonia | CLEOSTRATUS — Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 352 | auto-corrected |
| clidemus-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 314 | auto-corrected |
| clinias.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 165 | raw OCR |
| PG003 | Pseudo-Dionysius Areopagita v1 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 160,098 | manual |
| PG005 | Ignatius, Polycarp, Melito, 2nd-c. popes | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 47,775 | manual |
| PG006 | Justin, Tatian, Athenagoras, Theophilus, Hermias | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 213,721 | manual |
| PG067 | Socrates Scholasticus + Sozomen HE | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 220,457 | manual |
| PG087_1 | Procopius of Gaza v1 (OT catenae) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 207,880 | manual |
| PG101 | Photius (Amphilochia, NT commentary) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 232,210 | manual |
| PG107 | Leo VI the Wise (homilies, Tactica) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 196,722 | manual |
| PG109 | Theophanes Cont.; Cameniates; Symeon Logothete; Genesius | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 209,312 | manual |
| PG112 | Constantine VII v1 De ceremoniis | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 149,066 | manual |
| PG113 | Constantine VII v2 De them./De admin./Vita Basilii; Theodosius Diac. | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 146,028 | manual |
| PG118 | Oecumenius (catenae on Acts, Pauline & Catholic epistles) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 266,964 | manual |
| PG122 | Scylitzes continuatus + Psellus (Cedrenus v2 913-1057 split to georgius-cedrenus.compendium-historiarum / tlg3018.tlg001) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 153,769 | manual |
| PG123 | Theophylact of Ohrid v1 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 256,291 | manual |
| PG124 | Theophylact of Ohrid v2 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 261,046 | manual |
| PG125 | Theophylact of Ohrid v3 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 236,779 | manual |
| PG126 | Theophylact of Ohrid v4 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 225,938 | manual |
| PG134 | John Zonaras v1 Annales | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 287,809 | manual |
| PG139 | Joel; Nicetas Choniates (+Thesaurus); Isidore Thess.; Maroneia; John of Citrus | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 201,766 | manual |
| PG146 | Nicephorus Callistus Xanthopoulos HE 8-14 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 238,878 | manual |
| PG151 | Gregory Palamas v2; Acindynus; Barlaam | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 399,517 | manual |
| PG155 | Symeon of Thessalonica | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 199,763 | manual |
| PG157 | George Codinus; Ducas; Chronicon breve | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 123,822 | manual |
| PG158 | Michael Glycas Annales, Letters | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 197,345 | manual |
| comarius.peri-th-s-qei-as-kai-i-era-s-te-xnhs-tw-n-filoso-fwn-e |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 8 | raw OCR |
| comica-adespota-caf.fragmenta-incertorum-poetarum | Comica adespota — Fragmenta incertorum poetarum | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 54,261 | auto-corrected |
| commentaria-in-dionysii-thracis-artem-grammaticam.prolegomena-vossiana |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 229,211 | auto-corrected |
| constantinus-vii-porphyrogenitus-imperator.de-virtutibus-et-vitiis |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 212,432 | manual |
| corinna.fragmenta | CORINNA — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 636 | auto-corrected |
| cosmas-hieromonachus.ermhnei-th-s-e-pisth-mhs-th-s-xrusopoii-as-i-eromona-xou-tou |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,176 | auto-corrected |
| cougny-appendix-nova.didot-anthologia-v3 |  | qwen36-thomas_patricius_anthol_dubner_v3 | Qwen3.6-27B | 98,427 | auto-corrected |
| crates-comedy.fragmenta | ΓΕΙΤΟΝΕΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 1,020 | raw OCR |
| crates-poet-phil.fragmenta |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 4,259 | auto-corrected |
| cratinus-junior.fragmenta | ΘΗΡΑΜΕΝΗΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 266 | raw OCR |
| cratinus.fragmenta | ἈΡΧΙΔΟΧΟΙ | kock-caf1-ocr-frag | Qwen3.6-27B | 9,059 | auto-corrected |
| cratylus.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 681 | auto-corrected |
| crinis.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 281 | raw OCR |
| critias.fragmenta | ΣΙΣΤΦΟΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 662 | raw OCR |
| critias.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,706 | auto-corrected |
| crito-vel-damippus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 665 | raw OCR |
| critolaus-history.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 133 | raw OCR |
| crobylus.fragmenta | CROBYLUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 316 | raw OCR |
| ctesias.fragmenta |  | qwen36-ctesias_gilmore-ocr | Qwen3.6-27B | 31,042 | auto-corrected |
| cypria.cypria-fragmenta |  | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 2,643 | auto-corrected |
| cyrillus-scr-eccl.catecheses-ad-illuminandos-1-18 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,365 | auto-corrected |
| cyrillus-scr-eccl.epistula-ad-constantium-imperatorem | ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἹΕΡΟΣΟΛΥΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,737 | auto-corrected |
| cyrillus-scr-eccl.homilia-in-occursum-domini-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ (1) ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,244 | auto-corrected |
| cyrillus-scr-eccl.mystagogiae-1-5-sp | ΤΟΥ ΑΥΤΟΥ ΚΑΤΗΧΗΤΙΚΟΙ ΛΟΓΟΙ ΠΕΝΤΕ ΠΡΟΣ ΤΟΥΣ ΝΕΟΦΩΤΙΣΤΟΥΣ (1). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,705 | auto-corrected |
| cyrillus-scr-eccl.procatechesis | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,570 | auto-corrected |
| cyrillus-theology.ad-calosyrium-epist-83 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,320 | raw OCR |
| cyrillus-theology.ad-euoptium-episcopum-ptolemaidis-epist-84 | ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 822 | auto-corrected |
| cyrillus-theology.apologeticus-ad-theodosium-imperatorem | ΠΡΟΣ ΤΟΝ ΕΥΣΕΒΕΣΤΑΤΟΝ ΒΑΣΙΛΕΑ ΘΕΟΔΟΣΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,301 | auto-corrected |
| cyrillus-theology.apologia-xii-anathematismorum-contra-theodoretum | ΘΕΟΔΩΡΗΤΟΥ ΕΠΙΣΚΟΠΟΥ ΚΥΡΟΥ ΕΠΙΣΤΟΛΗ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,143 | auto-corrected |
| cyrillus-theology.apologia-xii-capitulorum-contra-orientales | ἈΠΟΛΟΓΗΤΙΚΟΣ ὙΠΕΡ ΤΩΝ ΔΩΔΕΚΑ ΚΕΦΑΛΑΙΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,242 | auto-corrected |
| cyrillus-theology.collectio-dictorum-veteris-testamenti-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,575 | auto-corrected |
| cyrillus-theology.commentarii-in-joannem | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΤΑ ΕΥΡΙΣΚΟΜΕΝΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178,539 | auto-corrected |
| cyrillus-theology.commentarii-in-lucam-in-catenis | ΕΞΗΓΗΣΙΣ ΕΙΣ ΤΟ ΚΑΤΑ ΛΟΥΚΑΝ ΕΥΑΓΓΕΛΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 86,834 | auto-corrected |
| cyrillus-theology.commentarius-in-isaiam-prophetam | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΕΞΗΓΗΣΙΣ ΥΠΟΜΝΗΜΑΤΙΚΗ ΕΙΣ ΤΟΝ ΠΡΟΦΗΤΗΝ ΗΣΑΙΑΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 293,159 | auto-corrected |
| cyrillus-theology.contra-julianum-lib-1-2 | ΤΟΥ ἉΓΙΟΥ ΚΥΡΙΛΛΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 120,657 | auto-corrected |
| cyrillus-theology.de-incarnatione-dei-verbi-homilia-diversa-15 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,121 | raw OCR |
| cyrillus-theology.de-incarnatione-unigeniti |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,118 | auto-corrected |
| cyrillus-theology.de-sancta-trinitate-dialogi-ivii |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 81,571 | auto-corrected |
| cyrillus-theology.de-sancta-trinitate-sp | ΚΕΦΑΛΑ Αʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 16,935 | auto-corrected |
| cyrillus-theology.dialogus-cum-nestorio-sp | ΤΟΥ ΑΥΤΟΥ ΑΓΙΟΥ ΚΥΡΙΛΛΟΥ ΔΙΑΛΕΞΙΣ ΠΡΟΣ ΝΕΣΤΟΡΙΟΝ (1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,236 | auto-corrected |
| cyrillus-theology.epistulae-paschales-sive-homiliae-paschales-epist-1-30 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΟΜΙΛΙΑΙ ΕΟΡΤΑΣΤΙΚΑΙ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 117,880 | auto-corrected |
| cyrillus-theology.explanatio-xii-capitulorum | ΕΠΙΛΥΣΙΣ ΤΩΝ ΔΩΔΕΚΑ ΚΕΦΑΛΑΙΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,012 | auto-corrected |
| cyrillus-theology.expositio-in-psalmos | 5 ΨΑΛΜΟΣ Αʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 95,492 | auto-corrected |
| cyrillus-theology.expositio-in-psalmos-prooemium | ΚΥΡΊΛΛΟΝ ἈΡΧΙΕΠΙΣΚΌΠΟΥ ἈΛΈΞΑΝ ΑΡΕΙΑϹΕΙϹΤΟΥϹ ΨΑΛΜΟΝϹ:: | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 367 | raw OCR |
| cyrillus-theology.fragmenta-in-canticum-canticorum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,679 | raw OCR |
| cyrillus-theology.fragmenta-in-libros-regum | ΕΚ ΤΗΣ ΕΡΜΗΝΕΙΑΣ ΤΟΥ ΑΓΙΟΥ ΚΥΡΙΛΛΟΥ ΕΙΣ ΤΑΣ ΒΑΣΙΛΕΙΩΝ ΒΙΒΛΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,747 | auto-corrected |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ad-hebraeos |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,318 | raw OCR |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ad-romanos | ΕΡΜΗΝΕΙΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΡΩΜΑΙΟΥΣ ΕΠΙΣΤΟΛΗΝ: | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,880 | auto-corrected |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ii-ad-corinthios | ΤΟΥ ἉΓΙΟΥ ΚΥΡΙΛΛΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,103 | auto-corrected |
| cyrillus-theology.libri-v-contra-nestorium | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ ΔΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΚΑΤΑ ΤΩΝ ΝΕΣΤΟΡΙΟΥ ΔΥΣΦΗΜΙΩΝ ΠΕΝΤΑΒΙΒΛΟΣ ΑΝΤΙΠΡΕΙΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 49,892 | auto-corrected |
| cyrillus-theology.oratio-ad-arcadiam-et-marinam-augustas-de-fide | ΚΥΡΙΛΛΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ ΠΡΟΣΦΩΝΗΤΙΚΟΣ ΤΑΙΣ ΕΥΣΕΒΕΣΤΑΤΑΙΣ ΒΑΣΙΛΙΣΣΑΙΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,361 | auto-corrected |
| cyrillus-theology.oratio-ad-pulcheriam-et-eudociam-augustas-de-fide | ΚΥΡΙΛΛΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ἈΛΕΞΑΝΔΡΕΙΑΣ ΛΟΓΟΣ ΔΕΥΤΕΡΟΣ ΠΡΟΣ ΧΡΗΣΤΙΚΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,836 | auto-corrected |
| cyrillus-theology.oratio-ad-theodosium-imperatorem-de-recta-fide | ΠΡΟΣ ΤΟΝ ΕΥΣΕΒΕΣΤΑΤΟΝ ΒΑΣΙΛΕΑ ΘΕΟΔΟΣΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,346 | auto-corrected |
| cyrillus-theology.quod-unus-sit-christus |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 18,703 | auto-corrected |
| cyrillus-theology.responsiones-ad-tiberium-diaconum-sociosque-suos | ΚΕΦΑΛΑΙΟΝ ΠΡΩΤΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,201 | auto-corrected |
| cyrillus-theology.scholia-de-incarnatione-unigeniti-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,008 | auto-corrected |
| cyrillus-theology.sermo-de-obitu-sanctorum-trium-puerorum-fragmenta-sp | ΛΟΓΟΣ ΕΙΣ ΤΗΝ ΤΕΛΕΥΤΗΝ ΤΩΝ ΑΓΙΩΝ ΠΡΩΝ ΠΑΙΔΩΝ ΚΑΙ ΤΟΥ ΠΑΝΣΟΦΟΥ ΔΑΝΙΗΛ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,178 | auto-corrected |
| cyrillus-theology.thesaurus-de-sancta-consubstantiali-trinitate | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΚΥΡΙΛΛΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΑΛΕΞΑΝΔΡΕΙΑΣ Η ΒΙΒΛΟΣ ΤΩΝ ΘΗΣΑΥΡΩΝ ΠΕΡΙ ΤΗΣ ΑΓΙΑΣ ΚΑΙ ΟΜΟΟΥΣΙΟΥ ΤΡΙΑΔΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 131,028 | auto-corrected |
| damascius.de-principiis | DAMASCIUS — De principiis (Ἀπορίαι καὶ λύσεις περὶ τῶν πρώτων ἀρχῶν) | [Damascius, ed. Ruelle (MDZ scan + HathiTrust, ROVER-merged; primary OCR Qwen3.6)](https://www.digitale-sammlungen.de/en/view/bsb00075170) | Qwen3.6-27B-FP8 | 119,092 | auto-corrected |
| damascius.in-parmenidem | DAMASCIUS — In Parmenidem | [Damascius, ed. Ruelle (MDZ scan + HathiTrust, ROVER-merged; primary OCR Qwen3.6)](https://www.digitale-sammlungen.de/en/view/bsb00075170) | Qwen3.6-27B-FP8 | 132,302 | auto-corrected |
| damascius.vita-isidori-ap-sudam-hesychium-photium-et-e-cod-vat | DAMASCIUS — Vita Isidori (fragmenta ap. Sudam etc.) | qwen36-damascius-boissonade | Qwen3.6-27B | 12,536 | raw OCR |
| damianus-scriptor-de-opticis.optica |  | qwen36-damianus_schoene | Qwen3.6-27B | 3,440 | auto-corrected |
| damon-et-phintias.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 308 | raw OCR |
| damoxenus.fragmenta | DAMOXENUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 290 | raw OCR |
| demetrius-comedy.fragmenta | ΔΗΜΗΤΡΙΟΤ ΣΙΚΕΛΙΑ 795 | kock-caf1-ocr-frag | Qwen3.6-27B | 226 | raw OCR |
| demetrius-poet-phil.demetrius-de-eloc-roberts |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,215 | auto-corrected |
| demetrius-poet-phil.fragmenta-et-titulus |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 144 | raw OCR |
| demochares.fhg2 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 111,139 | auto-corrected |
| demochares.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 1,356 | auto-corrected |
| democritus-history.fragmentum |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 135 | raw OCR |
| democritus-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 48,626 | auto-corrected |
| demodocus.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 2,005 | auto-corrected |
| demon.fragmenta |  | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 332 | raw OCR |
| demonax-philosophy.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,361 | auto-corrected |
| dercyllus.fragmenta |  | qwen36-staphylus_fhg4-ocr | Qwen3.6-27B | 124 | auto-corrected |
| diagoras.fragmenta | DIAGORAS — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 206 | auto-corrected |
| didymus.schmidt |  | qwen36-didymus_schmidt | Qwen3.6-27B | 38,807 | auto-corrected |
| diels-fdv2-1906-1.paratexta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 46 | auto-corrected |
| diels-fvs-1903.paratexta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 199 | raw OCR |
| diels-ppf-1901.paratexta |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 6,235 | auto-corrected |
| dindorf-hgm1.paratexta |  | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 8,508 | auto-corrected |
| dindorf-hgm2.paratexta |  | qwen36-menander_protector_dindorf_hgm | Qwen3.6-27B | 302 | auto-corrected |
| dinolochus.fragmentum | DINOLOCHUS — Fragmentum | qwen36-rhinthon_kaibel_cgf_1899-ocr | Qwen3.6-27B | 390 | auto-corrected |
| diocles-echecrates-polymnastus-phanton-arion.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 62 | raw OCR |
| diocles.fragmenta | ΚΤΚΑΩΠΕΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 212 | auto-corrected |
| diodorus-aspendius.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 16 | raw OCR |
| diodorus-comedy.fragmenta | ΕΠΙΚΛΗΡΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 152 | raw OCR |
| diogenes-apolloniates.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,567 | auto-corrected |
| diogenes-oenoandensis.diogenes-oenoanda-william |  | qwen36-diogenes_oenoanda_william | Qwen3.6-27B | 8,862 | auto-corrected |
| diogenes-philosophy.fragmenta | ΟΙΔΙΠΟΤΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 207 | raw OCR |
| diogenes-sinopensis.fragmenta-et-apophthegmata |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 11,156 | auto-corrected |
| diogenes-smyrnaeus.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 24 | raw OCR |
| diogenes.fragmentum |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 243 | auto-corrected |
| dionysius-chalcus.fragmenta | DIONYSIUS CHALCUS — Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 436 | raw OCR |
| dionysius-comedy.fragmenta | ἈΚΟΝΤΙΖΟΜΕΝΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 280 | raw OCR |
| dionysius-i-tragedy.fragmenta | ΔΙΜΟΣ (?) | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 456 | auto-corrected |
| dionysius-metaqemenos.fragmenta |  | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 492 | auto-corrected |
| dionysius-milesius.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 558 | raw OCR |
| dionysius-soph.epistulae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,325 | auto-corrected |
| dionysius-thrax-grammar.ars-grammatica | ΤΈΧΝΗ ΔΙΟΝΥΣΊΟΥ ΓΡΑΜΜΑΤΙΚΟΥ͂ | [Dionysius Thrax, Ars grammatica, ed. Uhlig (Grammatici Graeci I.1)](https://archive.org/search?query=Grammatici+Graeci+Uhlig+Dionysii+Thracis) | Qwen3.6-27B | 6,216 | auto-corrected |
| diophantus-mathematics.arithmeticorum-libri-sex | DIOPHANTUS — Arithmetica | qwen36-diophantialexan01plangoog | Qwen3.6-27B | 51,884 | raw OCR |
| dioscurides.fragmenta |  | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 757 | auto-corrected |
| diotimus-philosophy.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178 | raw OCR |
| dioxippus.fragmenta | DIOXIPPUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 31 | raw OCR |
| diphilus-comedy.fragmenta | ΔΙΦΙΛΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 3,352 | auto-corrected |
| diphilus-epic.fragmentum |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 130 | raw OCR |
| dius.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 361 | auto-corrected |
| dosiadas.fragmenta |  | qwen36-socrates_hist_fhg4-ocr | Qwen3.6-27B | 1 | raw OCR |
| dositheus-magister.ars-grammatica |  | [archive.org](https://archive.org/details/arsgrammaticarec00dosiuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 6,479 | auto-corrected |
| dromo.fragmenta | ΨΑΛΤΡΙΑ | kock-caf2-ocr-frag | Qwen3.6-27B | 43 | raw OCR |
| ecphantides.fragmenta | ἈΔΗΛΟΥ ΔΡΑΜΑΤΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 133 | raw OCR |
| ecphantus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 332 | raw OCR |
| elias-cretensis.commentarii-in-sancti-gregorii-nazianzeni-orationes-xix | Elias Cretensis — Commentarii in sancti Gregorii Nazianzeni orationes xix | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 38,577 | auto-corrected |
| empedocles.diels-ppf |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 23,663 | auto-corrected |
| empedocles.epigramma |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 5,444 | raw OCR |
| empedocles.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 40,541 | auto-corrected |
| ephippus.fragmenta | ἈΜΦΙΣΒΗΤΗΣΙΜΑ | kock-caf2-ocr-frag | Qwen3.6-27B | 1,023 | raw OCR |
| epicharmus-et-pseudepicharmea.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 5,211 | auto-corrected |
| epicrates.fragmenta | ΕΠΙΚΡΑΤΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 371 | raw OCR |
| epicurus.deperditorum-librorum-reliquiae | EPICURUS — Deperditorum librorum reliquiae (Usener, Epicurea) | qwen36-usener-epicurea-1887 | Qwen3.6-27B | 61,340 | raw OCR |
| epigenes.fragmenta | ΑΡΙΤΤΡΙΟΤ ΑΦΑΝΙΣΜΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 219 | raw OCR |
| epigonus-ap-cougny-v1 |  | qwen36-epigonus_ap_cougny_v1 | Qwen3.6-27B | 79,204 | auto-corrected |
| epilycus.fragmenta | ΚΩΡΑΛΙΣΚΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 269 | raw OCR |
| epimenides.testimonia-2 |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,962 | auto-corrected |
| epinicus.fragmenta | EPINICUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 172 | raw OCR |
| eratosthenes-et-eratosthenica.catasterismi |  | qwen36-eratosthenes_bernhardy | Qwen3.6-27B | 20,657 | auto-corrected |
| erinna.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,142 | auto-corrected |
| eriphus.fragmenta | ΜΕΛΙΒΟΙΑ | kock-caf2-ocr-frag | Qwen3.6-27B | 173 | raw OCR |
| erotianus.vocum-hippocraticarum-collectio |  | qwen36-erotianus_nachmanson_1918 | Qwen3.6-27B | 18,450 | auto-corrected |
| etymologicum-genuinum.etymologicum-genuinum-mwsge-pws |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 71,691 | auto-corrected |
| etymologicum-gudianum.etymologicum-gudianum-lion-zeiai | ETYMOLOGICUM GUDIANUM — Etymologicum Gudianum | qwen36-etym-gudianum-sturz-bsb | Qwen3.6-27B | 322,517 | raw OCR |
| euagon.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 213 | auto-corrected |
| euangelus.fragmentum | EUANGELUS — Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 158 | raw OCR |
| eubulides.fragmentum | ΔΙΣ ΕΞΑΠΑΤΩΜΕΝΟΣ ΕΠΙΚΛΗΡΟΣ ΘΩΡΤΚΙΟΝ (?) | kock-caf2-ocr-frag | Qwen3.6-27B | 71 | raw OCR |
| eubulus.fragmenta | ΕΥΒΟΥΛΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 4,363 | auto-corrected |
| eudemus-philosophy.fragmenta |  | qwen36-eudemus_spengel_1866 | Qwen3.6-27B | 39,643 | auto-corrected |
| eudoxus-astronomy.fragmenta |  | qwen36-eudoxus_ars_astronomica_blass | Qwen3.6-27B | 3,210 | auto-corrected |
| eudoxus.fragmenta | EUDOXUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 79 | raw OCR |
| eudromus.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 67 | raw OCR |
| euenus.fragmenta | EUENUS — Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 534 | raw OCR |
| euhemerus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,120 | auto-corrected |
| eumelus.fragmentum |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 1,140 | auto-corrected |
| eunicus.fragmentum | ΦΙΛΥΑΛΛΙΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 117 | raw OCR |
| euphorion.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,620 | auto-corrected |
| eupolis.fragmenta | ΕΤΗΟΛΙΔΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 9,453 | auto-corrected |
| euryphamus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 810 | auto-corrected |
| eurytus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 234 | auto-corrected |
| eurytus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 608 | raw OCR |
| eusebius-scr-eccl.antiquorum-martyriorum-collectio-fragmenta | ΤΩΝ ΑΡΧΑΙΩΝ ΜΑΡΤΥΡΙΩΝ ΣΥΝΑΓΩΓΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,696 | auto-corrected |
| eusebius-scr-eccl.de-solemnitate-paschali |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,628 | auto-corrected |
| eusebius-scr-eccl.de-vitis-prophetarum-fragmenta | ABΔΙΟΥ, Δ' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,495 | auto-corrected |
| eusebius-scr-eccl.epistula-ad-carpianum-ad-canones-evangeliorum-praemissa | A ΚΑΝΩΝ ΠΡΩΤΟΣ ΕΝ Ω ΟΙ ΤΕΣΣΑΡΕΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,083 | auto-corrected |
| eusebius-scr-eccl.fragmenta-in-lucam | ΕΥΣΕΒΙΟΥ ΚΑΙΣΑΡΕΙΑΣ ΕΙΣ ΤΟ ΚΑΤΑ ΛΟΥΚΑΝ ΕΥΑΓΓΕΛΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,427 | auto-corrected |
| eusebius-scr-eccl.quaestiones-evangelicae-ad-marinum | ἘΚΛΟΓΗ ἘΝ ΣΥΝΤΟΜΩ ἘΚ ΤΟΥ ἈΥΤΟΥ ΕΥΣΕΒΙΟΥ ΠΡΟΣ ΜΑΡΙΝΟΝ ΠΕΡΙ ΤΟΝ ΕΝ ΕΥΑΓΓΕΛΙΟΙΣ ΖΗΤΗΜΑΤΩΝ ΚΑΙ ΑΥΣΕΩΝ (24). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,142 | auto-corrected |
| eusebius-scr-eccl.quaestiones-evangelicae-ad-stephanum | ΕΚΛΟΓΗ ΕΝ ΣΥΝΤΟΜΩ ΕΚ ΤΩΝ ΣΥΝΤΕΘΕΝΤΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,795 | auto-corrected |
| eusebius-scr-eccl.supplementa-ad-quaestiones-ad-marinum | ἈΦΡΙΚΑΝΟΥ (48) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,483 | auto-corrected |
| eustathius-philol.commentarii-ad-homeri-iliadem | Eustathius Thessalonicensis — Commentarii ad Homeri Iliadem | qwen36-eustathius-iliad-stallbaum | Qwen3.6-27B | 1,065,178 | raw OCR |
| eustathius-philol.commentarii-ad-homeri-odysseam | EUSTATHIUS — Commentarii ad Homeri Odysseam (ed. Stallbaum) | [Eustathius, Commentarii ad Homeri Odysseam, ed. Stallbaum (Leipzig 1825-26), re-keyed by Stallbaum edition page](https://archive.org/details/commentariiadhom01eust) | Qwen3.6-27B-FP8 | 537,945 | manual |
| eustratius.in-aristotelis-analyticorum-posteriorum-librum-secundum-commentarium | EUSTRATIUS — In Aristotelis Analyticorum Posteriorum Librum Secundum Commentarium | qwen36-inanalyticorumpo00eust | Qwen3.6-27B | 110,701 | raw OCR |
| eutecnius.paraphrasis-in-oppiani-cynegetica-fort-auctore-eutecnio |  | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 430 dpi) | 3,962 | raw OCR |
| euthycles.fragmenta | EUTHYCLES — Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 83 | raw OCR |
| fhg-vol3-mueller-diocles-rhodius |  | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 88,967 | auto-corrected |
| flavius-justinianus-imperator.novellae |  | qwen36-justinian_novellae_schoell | Qwen3.6-27B | 233,631 | manual |
| fragmenta-alchemica.bafh-tou-i-ndikou-sidh-rou-grafei-sa-tw-au-tw-xro-nw |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 199 | raw OCR |
| fragmenta-alchemica.bafh-tou-para-pe-rsais-e-ceurhme-nou-xalkou-grafei-sa-po |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 269 | raw OCR |
| fragmenta-alchemica.de-margaritis-collectio-excerptorum-quae-incipit-vocibus |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 934 | auto-corrected |
| fragmenta-alchemica.de-quattuor-elementis-tractatus-qui-incipit-vocibus-rxh-th-s |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,546 | auto-corrected |
| fragmenta-alchemica.dia-gramma-th-s-mega-lhs-h-liourgi-as-paraballo-menon-ei-s-th-n |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 167 | raw OCR |
| fragmenta-alchemica.diaforai-moli-bdou-kai-xrusopeta-lou-e-cod-venet-marc |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 623 | auto-corrected |
| fragmenta-alchemica.ei-qe-leis-poih-sai-fou-rmas-kai-tu-lous-po-bronthsi-ou-poi-ei |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 456 | raw OCR |
| fragmenta-alchemica.eu-xh-ei-s-meli-ssion-e-cod-venet-marc-299-fol-3r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 194 | auto-corrected |
| fragmenta-alchemica.excerptum-de-mensibus-sine-titulo-e-cod-paris-b-n-gr-2327 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 99 | auto-corrected |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 49 | raw OCR |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-2 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 194 | auto-corrected |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-3 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 106 | raw OCR |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-4 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 51 | raw OCR |
| fragmenta-alchemica.fragmentum-peri-leukw-sews-xalkou-sine-titulo-e |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 240 | raw OCR |
| fragmenta-alchemica.h-gwgh-e-cod-venet-marc-299-101r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 27 | raw OCR |
| fragmenta-alchemica.h-oi-konomi-e-cod-venet-marc-299-fol-98v |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 196 | raw OCR |
| fragmenta-alchemica.h-poi-hsis-e-cod-venet-marc-299-fol-100v |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 35 | raw OCR |
| fragmenta-alchemica.katabafh-li-qwn-kai-smara-gdwn-kai-lixnitw-n-kai |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,642 | auto-corrected |
| fragmenta-alchemica.kinnaba-rews-skeuasi-e-cod-paris-b-n-gr-2327-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 285 | auto-corrected |
| fragmenta-alchemica.leu-kwsis-u-datos-di-ou-leukai-netai-oi-konomou-menon |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 66 | auto-corrected |
| fragmenta-alchemica.o-li-qos-th-s-filosofi-as-fort-auctore-zosimo-e-cod |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 206 | auto-corrected |
| fragmenta-alchemica.oi-konomi-th-s-sbe-stou-e-cod-venet-marc-299-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 126 | raw OCR |
| fragmenta-alchemica.oti-su-nqeton-kai-ou-x-plou-n-ei-dos-kai-ti-s-h |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 787 | auto-corrected |
| fragmenta-alchemica.peri-bafh-s-sidh-rou-e-cod-venet-marc-299-fol-104r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 839 | raw OCR |
| fragmenta-alchemica.peri-leukw-sews-tou-rsenikou-tou-sxistou-e-cod |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 96 | auto-corrected |
| fragmenta-alchemica.peri-th-s-qei-as-kai-i-era-s-te-xnhs-tw-n-filoso-fwn-e |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 830 | raw OCR |
| fragmenta-alchemica.peri-th-s-timiwta-ths-kai-polufh-mou-xrusoxoi-kh-s-e-cod |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 4,339 | auto-corrected |
| fragmenta-alchemica.peri-tou-li-qou-tw-n-filoso-fwn-e-cod-b-n-gr-2327-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 706 | auto-corrected |
| fragmenta-alchemica.peri-tou-o-reixa-lkou |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 52 | auto-corrected |
| fragmenta-alchemica.peri-tou-poih-sai-o-cuggosa-pounon-e-cod-paris-b-n-gr |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 98 | auto-corrected |
| fragmenta-alchemica.peri-tou-poih-sai-turo-kollan-e-cod-paris-b-n-gr-2327 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 173 | auto-corrected |
| fragmenta-alchemica.peri-tou-qei-ou-kau-stou-e-cod-paris-b-n-gr-2327 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 77 | raw OCR |
| fragmenta-alchemica.peri-tou-xrusw-sai-si-dhron-e-cod-paris-b-n-gr-2327 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 320 | auto-corrected |
| fragmenta-alchemica.peri-zu-qwn-poih-sews-e-cod-venet-marc-299-fol-162r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 105 | raw OCR |
| fragmenta-alchemica.po-sos-o-tw-n-baptome-nwn-e-ri-wn-staqmo-s-w-feilen-kai-po-sos-o |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 88 | auto-corrected |
| fragmenta-alchemica.poi-hsis-krustalli-wn-e-cod-venet-marc-299-fol-116r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 408 | raw OCR |
| fragmenta-alchemica.poi-hsis-ma-llon-tou-panto-s-e-cod-venet-marc-299-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 516 | raw OCR |
| fragmenta-alchemica.poi-hsis-rgu-rou-e-cod-venet-marc-299-fol-194v |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 140 | auto-corrected |
| fragmenta-alchemica.poi-hsis-sbe-stou-e-cod-venet-marc-299-fol-99v |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 119 | auto-corrected |
| fragmenta-alchemica.skeuasi-froni-trou-tou-zhtoume-nou-ei-s-ta-s-kollh-seis-xrusou |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 47 | auto-corrected |
| fragmenta-alchemica.sta-kths-poi-hsis-e-cod-venet-marc-299-fol-162v |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 286 | auto-corrected |
| fragmenta-alchemica.sumpe-rasma-th-s-poih-sews-e-cod-venet-marc-299-fol |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 63 | auto-corrected |
| fragmenta-alchemica.ti-s-h-meta-th-n-i-wsin-oi-konomi-e-cod-venet-marc |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 77 | auto-corrected |
| fragmenta-alchemica.ti-s-h-th-s-koma-rews-su-nqesis-e-cod-venet-marc-299 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 28 | raw OCR |
| fragmenta-alchemica.ti-s-h-tou-me-lanos-chri-ou-kataskeuh-e-cod-venet-marc |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 71 | raw OCR |
| fragmenta-alchemica.ti-s-h-tw-n-rxai-wn-sbestos-e-cod-venet-marc-299 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 208 | raw OCR |
| fragmenta-alchemica.xrh-sis-ioustinianou-basile-ws-sine-titulo-e-cod |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 726 | auto-corrected |
| fragmenta-alchemica.xrusou-poi-hsis-e-cod-paris-b-n-gr-2327-fol-232r |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 292 | raw OCR |
| fragmentum-stoicum.fragmentum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20 | auto-corrected |
| gaius-suetonius-tranquillus.peri-blasfhmiw-n-kai-po-qen-e-ka-sth |  | qwen36-suetonius_reliquiae_reifferscheid | Qwen3.6-27B | 11,460 | auto-corrected |
| geoponica.geoponica |  | qwen36-geoponica_beckh | Qwen3.6-27B | 123,977 | auto-corrected |
| georgius-cedrenus.compendium-historiarum |  | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 291,745 | manual |
| georgius-choeroboscus.prolegomena-et-scholia-in-theodosii-alexandrini-canones-isagogicos-de |  | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 142,225 | auto-corrected |
| georgius-monachus.chronicon-breve-lib-1-6-redactio-recentior | ΠΡΟΟΙΜΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 239,480 | auto-corrected |
| gorgias-rhetoric.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 979 | auto-corrected |
| gorgias-rhetoric.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,879 | auto-corrected |
| gregorius-nazianzenus.ad-eos-qui-ipsum-acciverant-nec-occurrerant-orat-3 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 784 | auto-corrected |
| gregorius-nazianzenus.ad-gregorium-nyssenum-orat-11 | ΛΟΓΟΣ ΙΑʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,530 | raw OCR |
| gregorius-nazianzenus.ad-julianum-tributorum-exaequatorem-orat-19 | ΛΟΓΟΣ ΙΘ' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,982 | auto-corrected |
| gregorius-nazianzenus.ad-patrem-orat-12 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,198 | auto-corrected |
| gregorius-nazianzenus.apologetica-orat-2 | ΛΟΓΟΣ Β. A | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,618 | auto-corrected |
| gregorius-nazianzenus.apologeticus-ad-patrem-orat-9 | ΛΟΓΟΣ Θʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,204 | auto-corrected |
| gregorius-nazianzenus.carmina-de-se-ipso | ΒΙΒΛΟΣ Βʹ. ΕΠΗ ΙΣΤΟΡΙΚΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 43,465 | auto-corrected |
| gregorius-nazianzenus.carmina-dogmatica | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΤΟΥ ΘΕΟΛΟΓΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 51,743 | auto-corrected |
| gregorius-nazianzenus.carmina-quae-spectant-ad-alios | TOMH B'. ΠΕΡΙ ΤΩΝ ΕΤΕΡΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,096 | auto-corrected |
| gregorius-nazianzenus.contra-arianos-et-de-seipso-orat-33 | ΛΟΓΟΣ ΛΓʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,172 | auto-corrected |
| gregorius-nazianzenus.contra-julianum-imperatorem-1-orat-4 | A ΛΟΓΟΣ Δ' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 25,352 | auto-corrected |
| gregorius-nazianzenus.de-dogmate-et-constitutione-episcoporum-orat-20 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,826 | raw OCR |
| gregorius-nazianzenus.de-martyribus-et-adversus-arianos-orat-35-sp | ΛΟΓΟΣ ΛΕʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,042 | auto-corrected |
| gregorius-nazianzenus.de-moderatione-in-disputando-orat-32 | ΛΟΓΟΣ ΛΒʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,869 | auto-corrected |
| gregorius-nazianzenus.de-pace-1-orat-6 | ΛΟΓΟΣ Ϛʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,460 | auto-corrected |
| gregorius-nazianzenus.de-pauperum-amore-orat-14 | ΛΟΓΟΣ ΙΔʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,153 | auto-corrected |
| gregorius-nazianzenus.de-seipso-et-ad-eos-qui-ipsum-cathedram-constantinopolitanam-affectare | ΛΟΓΟΣ ΛϚ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,401 | auto-corrected |
| gregorius-nazianzenus.epistulae | ΓΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΤΟΥ ΘΕΟΛΟΓΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 39,845 | auto-corrected |
| gregorius-nazianzenus.epistulae-theologicae | ΡΑ' ΠΡΟΣ ΚΑΔΙΟΝΙΟΝ ΠΡΕΣΒΥΤΕΡΟΝ ΚΑΤΑ ΑΠΟΛΛΙΝΑΡΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,016 | auto-corrected |
| gregorius-nazianzenus.fragmentum-ex-oratione-contra-astronomos-sp | Fragmentum ex oratione contra astronomos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 883 | raw OCR |
| gregorius-nazianzenus.funebris-in-laudem-caesarii-fratris-oratio-orat-7 | ΛΟΓΟΣ Ζ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,585 | auto-corrected |
| gregorius-nazianzenus.funebris-oratio-in-laudem-basilii-magni-caesareae-in-cappadocia | ΛΟΓΟΣ ΜΓʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,152 | auto-corrected |
| gregorius-nazianzenus.funebris-oratio-in-patrem-orat-18 | ΛΟΓΟΣ ΙΗʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,277 | auto-corrected |
| gregorius-nazianzenus.in-aegyptiorum-adventum-orat-34 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,709 | raw OCR |
| gregorius-nazianzenus.in-consecratione-eulalii-doarensium-episcopi-orat-13 | ΛΟΓΟΣ ΙΓ' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 331 | raw OCR |
| gregorius-nazianzenus.in-dictum-evangelii-cum-consummasset-jesus-hos-sermones-orat-37 | ΛΟΓΟΣ ΛΖʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,110 | auto-corrected |
| gregorius-nazianzenus.in-laudem-athanasii-orat-21 | ΛΟΓΟΣ ΚΑʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,307 | auto-corrected |
| gregorius-nazianzenus.in-laudem-heronis-philosophi-orat-25 | ΛΟΓΟΣ ΚΕʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,072 | auto-corrected |
| gregorius-nazianzenus.in-laudem-sororis-gorgoniae-orat-8 | ΛΟΓΟΣ Η | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,364 | auto-corrected |
| gregorius-nazianzenus.in-machabaeorum-laudem-orat-15 | ΛΟΓΟΣ ΙΕʹ (49) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,833 | auto-corrected |
| gregorius-nazianzenus.in-novam-dominicam-orat-44 | ΛΟΓΟΣ ΜΔʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,177 | auto-corrected |
| gregorius-nazianzenus.in-patrem-tacentem-orat-16 | ΛΟΓΟΣ ΙϚ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,325 | auto-corrected |
| gregorius-nazianzenus.in-sancta-lumina-orat-39 | ΛΟΓΟΣ ΙΖ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,593 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-baptisma-orat-40 | ΛΟΓΟΣ Μʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,418 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-pascha-et-in-tarditatem-orat-1 | ἘΝ ἉΓΙΟΙ͂Σ ΠΑΤΡῸΣ ἩΜΩ͂Ν ΓΡΗΓΟΡΙΟΥ͂ ΤΟΥ͂ ΘΕΟΛΟΓΟΥ͂ ἈΡΧΙΕΠΙΣΚΌΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΌΛΕΩΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 879 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-pascha-orat-45 | In sanctum pascha (orat. 45) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,184 | auto-corrected |
| gregorius-nazianzenus.in-seipsum-ad-patrem-et-basilium-magnum-orat-10 | ΛΟΓΟΣ Ιʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 662 | raw OCR |
| gregorius-nazianzenus.in-seipsum-cum-rure-rediisset-post-ea-quae-maximo-perpetrata | ΛΟΓΟΣ ΚϚʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,895 | auto-corrected |
| gregorius-nazianzenus.in-theophania-orat-38 | ΛΟΓΟΣ ΛΗ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,425 | auto-corrected |
| gregorius-nazianzenus.liturgia-sancti-gregorii-sp | Liturgia sancti Gregorii [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,648 | auto-corrected |
| gregorius-nazianzenus.significatio-in-ezechielem-sp | Significatio in Ezechielem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 521 | auto-corrected |
| gregorius-nazianzenus.supremum-vale-orat-42 | ΛΟΓΟΣ ΜΒ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,824 | auto-corrected |
| gregorius-nazianzenus.testamentum | ΤΟΥ ΑΓΙΟΥ ΓΡΗΓΟΡΙΟΥ ΤΟΥ ΘΕΟΛΟΓΟΥ ΙΣΟΝ ΤΗΣ ΔΙΑΘΗΚΗΣ ΜΕΤΑΓΡΑΦΕΝ ΕΚ ΤΟΥ ΑΡΧΕΤΥΠΟΥ ΔΙΚΑΙΩΜΑΤΟΣ, ΕΝ Ω ΙΑΙΟΧΕΙΡΟΙ ΥΠΟΓΡΑΦΑΙ ΣΩΖΟΝΤΑΙ ΥΠ' ΑΥΤΟΥ ΤΕ ΚΑΙ ΤΩΝ ΥΠΟΓΡΑΨΑΝΤΩΝ ΜΑΡΤΥΡΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,006 | raw OCR |
| gregorius-nyssenus.ad-ablabium-quod-non-sint-tres-dei | ΠΕΡΙ ΤΟΥ ΜΗ ΕΙΝΑΙ ΤΡΕΙΣ ΘΕΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,129 | auto-corrected |
| gregorius-nyssenus.ad-graecos-ex-communibus-notionibus | ΤΟΥ ΑΥΤΟΥ ΓΡΗΓΟΡΙΟΥ ΠΡΟΣ ΕΛΛΗΝΑΣ ΕΚ ΤΩΝ ΚΟΙΝΩΝ ΕΝΝΟΙΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,122 | auto-corrected |
| gregorius-nyssenus.ad-imaginem-dei-et-ad-similitudinem-sp | ΤΟΥ ΑΥΤΟΥ ΓΡΗΓΟΡΙΟΥ ΝΥΣΣΗΣ ΠΕΡΙ ΤΟΥ, ΤΙ ΕΣΤΙ ΤΟ, ΚΑΤ' ΕΙΚΟΝΑ ΘΕΟΥ ΚΑΙ ΚΑΘ' ΟΜΟΙΩΣΙΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,231 | auto-corrected |
| gregorius-nyssenus.ad-theophilum-adversus-apollinaristas | ΤΟΥ ΑΥΤΟΥ ΓΡΗΓΟΡΙΟΥ ΚΑΤΑ ΑΠΟΛΙΝΑΡΙΟΥ ΠΡΟΣ ΘΕΟΦΙΛΟΝ ΕΠΙΣΚΟΠΟΝ ΑΛΕΞΑΝΔΡΕΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,687 | auto-corrected |
| gregorius-nyssenus.adversus-arium-et-sabellium-de-patre-et-filio | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΛΟΓΟΣ ΚΑΤΑ ΑΡΕΙΟΥ ΚΑΙ ΣΑΒΕΛΛΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,428 | auto-corrected |
| gregorius-nyssenus.adversus-eos-qui-castigationes-aegre-ferunt | ΤΟΥ ΑΥΤΟΥ ΠΡΟΣ ΤΟΥΣ ΑΧΘΟΜΕΝΟΥΣ ΤΑΙΣ ΕΠΙΤΙΜΗΣΕΣΙ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,135 | auto-corrected |
| gregorius-nyssenus.adversus-macedonianos-de-spiritu-sancto | ΚΑΤΑ ΜΑΚΕΔΟΝΙΑΝΩΝ ΤΩΝ ΠΝΕΥΜΑΤΟΜΑΧΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,988 | auto-corrected |
| gregorius-nyssenus.antirrheticus-adversus-apollinarium | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΕΝΕ ΑΝΤΙΡΡΗΤΙΚΟΣ ΠΡΟΣ ΤΑ ΑΠΟΛΙΝΑΡΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,930 | auto-corrected |
| gregorius-nyssenus.apologia-in-hexaemeron | ΑΠΟΛΟΓΗΤΙΚΟΣ ΠΡΟΣ ΠΕΤΡΟΝ ΤΟΝ ΑΔΕΛΦΟΝ ΑΥΤΟΥ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,149 | auto-corrected |
| gregorius-nyssenus.contra-eunomium | ΠΡΟΣ ΤΟΝ ΑΔΕΛΦΟΝ ΑΥΤΟΥ ΠΕΤΡΟΝ ΕΠΙΣΚΟΠΟΝ ΣΕΒΑΣΤΕΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178,298 | auto-corrected |
| gregorius-nyssenus.contra-fatum | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,665 | auto-corrected |
| gregorius-nyssenus.contra-fornicarios | Ὁ ΔΕ ΠΟΡΝΕΙΩΝ, ΕΙΣ ΤΟ ΙΑΙΟΝ ΣΟΜΑ ΑΜΑΡΤΑΝΕΙ (1). | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 917 | auto-corrected |
| gregorius-nyssenus.contra-usurarios | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΕΝΕ ΚΑΤΑ ΤΩΝ ΤΟΚΙΖΟΝΤΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,705 | auto-corrected |
| gregorius-nyssenus.de-anima-sp | ΤΟΥ ΑΥΤΟΥ ΓΡΗΓΟΡΙΟΥ ΠΕΡΙ ΨΥΧΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,729 | auto-corrected |
| gregorius-nyssenus.de-beneficentia-vulgo-de-pauperibus-amandis-i | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΠΕΡΙ ΦΙΛΟΠΤΩΧΙΑΣ ΚΑΙ ΕΥΠΟΠΑΣ ΛΟΓΟΣ Αʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,715 | auto-corrected |
| gregorius-nyssenus.de-creatione-hominis-sermo-alter-sp | ΛΟΓΟΣ Βʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,290 | auto-corrected |
| gregorius-nyssenus.de-creatione-hominis-sermo-primus-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΝΥΣΣΗΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,693 | auto-corrected |
| gregorius-nyssenus.de-deitate-adversus-evagrium-vulgo-in-suam |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,862 | raw OCR |
| gregorius-nyssenus.de-deitate-filii-et-spiritus-sancti | ΠΕΡΙ ΘΕΟΤΗΤΟΣ ΥΙΟΥ ΚΑΙ ΠΝΕΥΜΑΤΟΣ ΛΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,716 | auto-corrected |
| gregorius-nyssenus.de-infantibus-praemature-abreptis | ΤΟΥ ΑΥΤΟΥ ΠΕΡΙ ΤΩΝ ΝΗΠΙΩΝ ΠΡΟ ΩΡΑΣ ΑΦΑΡΠΑΖΟΜΕΝΩΝ, ΠΡΟΣ ΙΕΡΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,725 | auto-corrected |
| gregorius-nyssenus.de-instituto-christiano | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΠΕΡΙ ΤΟΥ ΚΑΤΑ ΘΕΟΝ ΣΚΟΠΟΥ ΚΑΙ ΤΗΣ ΚΑΤΑ ΑΛΗΘΕΙΑΝ ΔΕΚΕΣΕΩΣ· ΚΑΙ ΠΡΟΣ ΤΟΥΣ ΑΠΑΙΤΗΣΑΝΤΑΣ ΔΕΚΗΤΑΣ ΠΕΡΙ ΤΗΣ ΕΥΣΕΒΕΙΑΣ ΣΚΟΠΟΥ· ΚΑΙ ΤΟΥ ΟΠΩΣ ΧΡΗ ΣΥΝΕΙΝΑΙ ΑΛΛΗΛΟΙΣ ΚΑΙ ΣΥΝΑΓΩΝΙΖΕΣΘΑΙ, ΥΠΟΤΥΠΩΣΙΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,672 | auto-corrected |
| gregorius-nyssenus.de-mortuis-non-esse-dolendum | ΤΟΥ ἈΥΤΟΥ ΔΙΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,988 | auto-corrected |
| gregorius-nyssenus.de-occursu-domini-sp | ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΗΝ ΥΠΑΠΑΝΤΗΝ ΤΟΥ ΚΥΡΙΟΥ, ΚΑΙ ΕΙΣ ΤΗΝ ΘΕΟΤΟΚΟΝ, ΚΑΙ ΕΙΣ ΤΟΝ ΔΙΚΑΙΟΝ ΣΥΜΕΟΝΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,420 | auto-corrected |
| gregorius-nyssenus.de-opificio-hominis | ΠΕΡΙ ΚΑΤΑΣΚΕΥΗΣ ΑΝΘΡΩΠΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,753 | auto-corrected |
| gregorius-nyssenus.de-oratione-dominica-orationes-v | ΓΡΗΓΟΡΙΟΥ ΝΥΣΣΗΣ ΕΙΣ ΤΗΝ ΠΡΟΣΕΥΧΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,075 | auto-corrected |
| gregorius-nyssenus.de-perfectione-christiana-ad-olympium-monachum | ΤΟΥ ΑΥΤΟΥ ΠΕΡΙ ΤΕΛΕΙΟΤΗΤΟΣ, ΚΑΙ ΟΠΟΙΟΝ ΧΡΗ ΕΙΝΑΙ ΤΟΝ ΧΡΙΣΤΙΑΝΟΝ, ΠΡΟΣ ΟΛΥΜΠΙΟΝ ΜΟΝΑΧΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,061 | auto-corrected |
| gregorius-nyssenus.de-professione-christiana-ad-harmonium | ΤΙ ΤΟ ΧΡΙΣΤΙΑΝΩΝ ΟΝΟΜΑ Η ΕΠΑΓΓΕΛΜΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,120 | raw OCR |
| gregorius-nyssenus.de-pythonissa-ad-theodosium-episcopum |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 672 | raw OCR |
| gregorius-nyssenus.de-sancto-theodoro | ΕΙΣ ΤΟΝ ΜΕΓΑΝ ΜΑΡΤΥΡΑ ΘΕΟΔΩΡΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,210 | auto-corrected |
| gregorius-nyssenus.de-spiritu-sancto-sive-in-pentecosten | ΤΟΥ ΑΥΤΟΥ ΛΟΓΟΣ ΕΙΣ ΤΟ ΑΓΙΟΝ ΠΝΕΥΜΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,061 | auto-corrected |
| gregorius-nyssenus.de-virginitate | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΠΕΡΙ ΠΑΡΘΕΝΙΑΣ ΕΠΙΣΤΟΛΗ ΠΡΟΤΡΕΠΤΙΚΗ ΕΙΣ ΤΟΝ ΚΑΤ' ΑΡΕΤΗΝ ΒΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 22,262 | auto-corrected |
| gregorius-nyssenus.de-vita-gregorii-thaumaturgi | ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΟΝ ΒΙΟΝ ΤΟΥ ΑΓΙΟΥ ΓΡΗΓΟΡΙΟΥ ΤΟΥ ΘΑΥΜΑΤΟΥΡΓΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,998 | auto-corrected |
| gregorius-nyssenus.de-vita-mosis | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΗΣ, ΠΕΡΙ ΤΟΥ ΒΙΟΥ ΜΩΣΕΩΣ, Η ΠΕΡΙ ΤΗΣ ΚΑΤ’ ΑΡΕΤΗΝ ΤΕΛΕΙΟΤΗΤΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,971 | auto-corrected |
| gregorius-nyssenus.decem-syllogismi-contra-manichaeos-sp | ΤΟΥ ΑΥΤΟΥ ΚΑΤΑ ΜΑΝΙΧΑΙΩΝ ΛΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 229 | raw OCR |
| gregorius-nyssenus.dialogus-de-anima-et-resurrectione | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΗΣ ΠΕΡΙ ΨΥΧΗΣ ΚΑΙ ΑΝΑΣΤΑΣΕΩΣ Ο ΛΟΓΟΣ Ο ΛΕΓΟΜΕΝΟΣ ΤΑ ΜΑΚΡΙΝΙΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,778 | auto-corrected |
| gregorius-nyssenus.encomium-in-sanctum-stephanum-protomartyrem-i | ΕΙΣ ΤΟΝ ΑΓΙΟΝ ΣΤΕΦΑΝΟΝ ΤΟΝ ΠΡΩΤΟΜΑΡΤΥΡΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,012 | auto-corrected |
| gregorius-nyssenus.encomium-in-xl-martyres-i | ΕΙΣ ΤΟΥΣ ΑΓΙΟΥΣ ΤΕΣΣΑΡΑΚΟΝΤΑ ΜΑΡΤΥΡΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,607 | auto-corrected |
| gregorius-nyssenus.encomium-in-xl-martyres-ii | ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΟΥΣ ΤΕΣΣΑΡΑΚΟΝΤΑ ΜΑΡΤΥΡΑΣ ΛΟΓΟΣ ΕΓΚΩΜΙΑΣΤΙΚΟΣ ΡΗΘΕΙΣ ΕΝ ΤΩ ΜΑΡΤΥΡΙΩ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,676 | auto-corrected |
| gregorius-nyssenus.epistula-canonica-ad-letoium | ΤΟΥ ΑΥΤΟΥ ΕΠΙΣΤΟΛΗ ΚΑΝΟΝΙΚΗ ΠΡΟΣ ΤΟΝ ΕΝ ΑΓΙΟΙΣ ΑΗΤΟΙΟΝ ΕΠΙΣΚΟΠΟΝ ΜΕΛΙΤΙΝΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,060 | auto-corrected |
| gregorius-nyssenus.epistulae | ΕΠΙΣΤΟΛΗ Ζ’ (29) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,144 | auto-corrected |
| gregorius-nyssenus.in-ascensionem-christi | ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΗΝ ΤΟΥ ΧΡΙΣΤΟΥ ΑΝΑΛΗΨΙΝ ΤΗΝ ΑΕΓΟΜΕΝΗΝ ΤΩ ΕΠΙΧΩΡΙΩ ΤΩΝ ΚΑΠΠΑΔΟΚΩΝ ΕΘΕΙ ΤΗΝ ΕΠΙΣΟΖΟΜΕΝΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,027 | auto-corrected |
| gregorius-nyssenus.in-basilium-fratrem | ΕΙΣ ΤΟΝ ΙΑΙΟΝ ΑΔΕΑΦΟΝ ΤΟΝ ΜΕΓΑΝ ΒΑΣΙΛΕΙΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,106 | auto-corrected |
| gregorius-nyssenus.in-canticum-canticorum-homiliae-15 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΗΣ ΕΞΗΓΗΣΙΣ ΑΚΡΙΒΗΣ ΕΙΣ ΤΑ ΑΣΜΑΤΑ ΤΩΝ ΑΣΜΑΤΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 74,943 | auto-corrected |
| gregorius-nyssenus.in-ecclesiasten-homiliae-8 | ΕΙΣ ΤΟΝ ΕΚΚΛΗΣΙΑΣΤΗΝ ΤΟΥ ΣΑΛΟΜΩΝΤΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,355 | auto-corrected |
| gregorius-nyssenus.in-illud-quatenus-uni-ex-his-fecistis-mihi-fecistis | ΤΟΥ ΑΥΤΟΥ ΓΡΗΓΟΡΙΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,549 | auto-corrected |
| gregorius-nyssenus.in-illud-tunc-et-ipse-filius | ΕΙΣ ΤΟ, ΟΤΑΝ ΥΠΟΤΑΓΗ ΑΥΤΩ ΤΑ ΠΑΝΤΑ, ΤΟΤΕ ΚΑΙ ΑΥΤΟΣ Ο ΥΙΟΣ ΥΠΟΤΑΓΗΣΕΤΑΙ ΤΩ ΥΠΟΤΑΞΑΝΤΙ ΑΥΤΩ ΤΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,786 | auto-corrected |
| gregorius-nyssenus.in-inscriptiones-psalmorum | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΠΙΣΚΟΠΟΥ ΝΥΣΣΕΝΕ ΠΡΩΤΟΝ ΒΙΒΛΙΟΝ ΕΙΣ ΤΗΝ ΕΠΙΓΡΑΦΗΝ ΤΩΝ ΨΑΛΜΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 39,786 | auto-corrected |
| gregorius-nyssenus.in-luciferam-sanctam-domini-resurrectionem-vulgo-in | ΛΟΓΟΣ Εʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,218 | raw OCR |
| gregorius-nyssenus.in-sanctum-ephraim | ΕΙΣ ΤΟΝ ΟΣΙΟΝ ΠΑΤΕΡΑ ΗΜΩΝ ΕΦΡΑΙΜ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,454 | auto-corrected |
| gregorius-nyssenus.in-sanctum-et-salutare-pascha-vulgo-in-christi | ΛΟΓΟΣ Δʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 389 | auto-corrected |
| gregorius-nyssenus.in-sanctum-pascha-vulgo-in-christi-resurrectionem-oratio | ΛΟΓΟΣ Β' | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,741 | auto-corrected |
| gregorius-nyssenus.oratio-catechetica-magna | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΓΡΗΓΟΡΙΟΥ ΕΥΕΣΚΟΠΟΥ ΝΥΣΣΕΝΣ ΛΟΓΟΣ ΚΑΤΗΧΗΤΙΚΟΣ Ο ΜΕΓΑΣ ΕΝ ΚΕΦΑΛΑΙΟΙΣ ΤΕΣΣΑΡΑΚΟΝΤΑ ΔΙΗΡΜΕΝΕΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,553 | auto-corrected |
| gregorius-nyssenus.oratio-consolatoria-in-pulcheriam | ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΠΟΥΛΧΕΡΙΑΝ ΛΟΓΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,797 | auto-corrected |
| gregorius-nyssenus.oratio-funebris-in-flacillam-imperatricem | ΤΟΥ ΑΥΤΟΥ ΕΠΙΤΑΦΙΟΣ ΛΟΓΟΣ ΕΙΣ ΠΛΑΚΙΛΛΑΝ ΒΑΣΙΛΙΣΣΑΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,865 | auto-corrected |
| gregorius-nyssenus.oratio-funebris-in-meletium-episcopum | ΤΟΥ ΑΥΤΟΥ ΕΠΙΤΑΦΙΟΣ ΛΟΓΟΣ ΕΙΣ ΤΟΝ ΜΕΓΑΝ ΜΕΛΕΤΙΟΝ ΕΠΙΣΚΟΠΟΝ ΑΝΤΙΟΧΕΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,341 | auto-corrected |
| gregorius-nyssenus.oratio-in-diem-natalem-christi | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΛΟΓΟΣ ΕΙΣ ΤΗΝ ΓΕΝΝΗΣΙΝ ΤΟΥ ΧΡΙΣΤΟΥ ΚΑΙ ΕΙΣ ΤΑ ΝΗΠΙΑ ΤΑ ΕΝ ΒΗΘΛΕΕΜ ΑΝΑΙΡΕΘΕΝΤΑ ΥΠΟ ΗΡΩΔΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,807 | auto-corrected |
| gregorius-nyssenus.orationes-viii-de-beatitudinibus | ΕΙΣ ΤΟΥΣ ΜΑΚΑΡΙΣΜΟΥΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,547 | auto-corrected |
| gregorius-nyssenus.testimonia-adversus-judaeos-sp | ΕΚΛΟΓΑΙ ΜΑΡΤΥΡΙΩΝ ΠΡΟΣ ΙΟΥΔΑΙΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,074 | auto-corrected |
| gregorius-nyssenus.vita-sanctae-macrinae | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΓΡΗΓΟΡΙΟΥ ΕΙΣ ΤΟΝ ΒΙΟΝ ΤΗΣ ΟΣΙΑΣ ΜΑΚΡΙΝΗΣ ΑΔΕΛΦΗΣ ΤΟΥ ΜΕΓΑΛΟΥ ΒΑΣΙΛΕΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,567 | auto-corrected |
| hecataeus-abderita.testimonia-2 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,188 | auto-corrected |
| hegemon-parodius.fragmentum | ἈΤΣΙΠΠΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 119 | raw OCR |
| hegesippus.fragmenta | HEGESIPPUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 164 | raw OCR |
| heliodorus.fragmenta | Fragmenta | qwen36-staphylus_fhg4 | Qwen3.6-27B | 157 | raw OCR |
| hellanicus.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 959 | auto-corrected |
| heniochus.fragmenta | ΠΟΛΤΙΠΡΑΓΜΩΝ | kock-caf2-ocr-frag | Qwen3.6-27B | 76 | raw OCR |
| heraclides-comedy.fragmentum | ΑΔΗΛΟΥ ΔΡΑΜΑΤΟΣ | [Kock, Comicorum Atticorum Fragmenta II](https://archive.org/search?query=Comicorum+Atticorum+Fragmenta+Kock) | Qwen3.6-27B | 130 | raw OCR |
| heraclides-ponticus-junior-grammar.fragmenta |  | qwen36-aelian_heraclid_tauchnitz_1829 | Qwen3.6-27B | 57,613 | auto-corrected |
| heraclitus-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 15,689 | auto-corrected |
| herillus.fragmenta |  | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 209 | raw OCR |
| hermes.ai-nigma-tou-filosofikou-li-qou-ermou-kai-agaqodai-monos |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 57 | raw OCR |
| hermesianax.fragmenta |  | qwen36-philetas_bach_1829-ocr | Qwen3.6-27B | 6,528 | auto-corrected |
| hermias-history.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 514 | auto-corrected |
| hermippus-comedy.fragmenta | 230 ΕΡΜΙΠΠΟΥ | kock-caf1-ocr-frag | Qwen3.6-27B | 1,948 | auto-corrected |
| hermippus-comedy.fragmenta-4 |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 310 | raw OCR |
| herodas.mimiambi | ΠΡΟΚΥΚΛΙΣ Η ΜΑΣΤΡΟΠΟΣ | [Herodas, ed. Headlam-Knox](https://archive.org/details/herodasmimesfrag00hero) | Qwen3.6-27B | 2,785 | auto-corrected |
| heron.definitiones |  | qwen36-heron_definitiones_teubner4 | Qwen3.6-27B | 56,023 | auto-corrected |
| heron.geometrica | HERO ALEXANDRINUS — Geometrica | qwen36-heron-heiberg-v4 | Qwen3.6-27B | 46,883 | raw OCR |
| hesiodus.fragmenta |  | qwen36-hesiod_rzach-ocr | Qwen3.6-27B | 15,873 | auto-corrected |
| hesychius-lexicography.epistula-ad-eulogium |  | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 571 | auto-corrected |
| hesychius-lexicography.lexicon-o |  | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 146,215 | raw OCR |
| hesychius-lexicography.lexicon-p-w |  | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 56,840 | raw OCR |
| hexapla-anonymi.lectiones |  | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 1,821 | auto-corrected |
| hicetas.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 34 | raw OCR |
| hierocles-philosophy.hqikh-stoixei-wsis |  | qwen36-hierocl_aureum_mullach_fpg1 | Qwen3.6-27B | 139,484 | auto-corrected |
| hieronymus.fragmenta |  | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 541 | auto-corrected |
| hierotheus-alchemy.ieroqe-ou-peri-th-s-i-era-s-te-xnhs-e-cod-paris-b-n-gr |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 371 | auto-corrected |
| himerius.declamationes-et-orationes |  | qwen36-himerius_dubner_didot | Qwen3.6-27B | 256,598 | auto-corrected |
| hipparchus-comedy.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 215 | raw OCR |
| hipparchus-philosophy.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 634 | auto-corrected |
| hippasus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,784 | raw OCR |
| hippias-soph.testimonia-2 |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,916 | auto-corrected |
| hippiatrica.appendices-ad-hippiatrica-berolinensia | Appendices ad Hippiatrica Berolinensia | [Oder-Hoppe, Corpus Hippiatricorum Graecorum vol. 1 (Berolinensia), Teubner 1924](https://digital.slub-dresden.de/werkansicht/dlf/303101) | Qwen3.6-27B | 2,771 | auto-corrected |
| hippiatrica.hippiatrica-berolinensia | Hippiatrica Berolinensia | [Oder-Hoppe, Corpus Hippiatricorum Graecorum vol. 1 (Berolinensia), Teubner 1924](https://digital.slub-dresden.de/werkansicht/dlf/303101) | Qwen3.6-27B | 94,442 | auto-corrected |
| hippocrates.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,424 | auto-corrected |
| hippodamus.fragmenta-sp |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,676 | auto-corrected |
| hippon.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,989 | auto-corrected |
| horapollo.hieroglyphica-translatio-philippi |  | qwen36-horapollo_leemans | Qwen3.6-27B | 17,836 | auto-corrected |
| hyperochus.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 83 | raw OCR |
| ibycus.fragmenta | IBYCUS — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 1,616 | raw OCR |
| iccus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 611 | raw OCR |
| idaeus-philosophy.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 765 | auto-corrected |
| ilias-parva.ilias-parva-fragmenta |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 1,894 | auto-corrected |
| iliu-persis.iliu-persis-fragmenta |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 368 | auto-corrected |
| ion-philosophy.fragmenta | ΑΓΑΜΕΜΝΩΝ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 1,894 | auto-corrected |
| ion-philosophy.testimonia-2 |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,309 | auto-corrected |
| iophon.fragmenta | ἈΤΑΩΙΔΟΙ ΣΑΤΤΡΟΙ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 285 | auto-corrected |
| isidorus-scholasticus-anthol-didot |  | qwen36-isidorus_scholasticus_anthol_didot | Qwen3.6-27B | 105,271 | auto-corrected |
| isyllus.fragmenta-ig-4-950 |  | ig-iv-950-fraenkel-1902-diplomatic | Qwen3.6-27B | 72 | manual |
| jacobs-anthologia-graeca-t13.appendix-epigrammatum |  | qwen36-claudianus_epigr_anthologia_graeca | Qwen3.6-27B | 17,097 | auto-corrected |
| joannes-archiereus.iwa-nnou-rxiere-ws-tou-e-n-ebeigi-peri-th-s-qei-as-te-xnhs |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,260 | raw OCR |
| joannes-chrysostomus.ad-demetrium-de-compunctione-lib-1 | 422 ΠΡΟΣ ΔΗΜΗΤΡΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,510 | auto-corrected |
| joannes-chrysostomus.ad-eos-qui-scandalizati-sunt | ΤΟΥ ΑΥΤΟΥ ΛΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,030 | auto-corrected |
| joannes-chrysostomus.ad-illuminandos-catecheses-1-2-series-prima-et-secunda | ΚΑΤΗΧΗΣΙΣ ΠΡΩΤΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,892 | auto-corrected |
| joannes-chrysostomus.ad-populum-antiochenum-homiliae-1-21 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 90,786 | auto-corrected |
| joannes-chrysostomus.ad-stagirium-daemone-vexatum-lib-1-3 | ΠΡΟΣ ΣΤΑΓΕΙΡΙΟΝ ΑΕΚΗΤΗΝ ΔΑΙΜΟΝΟΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 31,936 | auto-corrected |
| joannes-chrysostomus.ad-stelechium-de-compunctione-lib-2 | ΠΡΟΣ ΣΤΕΛΕΧΙΟΝ, ΚΑΙ ΠΕΡΙ ΚΑΤΑΝΥΣΕΩΣ ΛΟΓΟΣ ΔΕΥΤΕΡΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,593 | auto-corrected |
| joannes-chrysostomus.ad-theodorum-lapsum-lib-1 | ΛΟΓΟΣ ΠΑΡΑΙΝΕΤΙΚΟΣ ΕΙΣ ΘΕΟΔΩΡΟΝ ΕΚΠΕΣΟΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,810 | auto-corrected |
| joannes-chrysostomus.ad-theodorum-lapsum-lib-2-epistula-ad-theodorum | ΤΟΥ ΑΥΤΟΥ ΠΡΟΣ ΤΟΝ ΑΥΤΟΝ ΘΕΟΔΩΡΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,021 | auto-corrected |
| joannes-chrysostomus.ad-viduam-juniorem |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,184 | auto-corrected |
| joannes-chrysostomus.adversus-ebriosos-et-de-resurrectione-domini-nostri-jesu-christi | ΚΑΤΑ ΜΕΘΥΟΝΤΩΝ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,964 | auto-corrected |
| joannes-chrysostomus.adversus-judaeos-orationes-1-8 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 42,998 | auto-corrected |
| joannes-chrysostomus.adversus-oppugnatores-vitae-monasticae-lib-1-3 | ΤΟΙΣ ΕΠΙ ΤΟ ΜΟΝΑΖΕΙΝ ΕΝΑΓΟΥΣΙΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,063 | auto-corrected |
| joannes-chrysostomus.ascetam-facetiis-uti-non-debere-sp | 801 ὍΤΙ ΟΥ ΧΡΗ ΕΥΤΡΑΠΕΙΖΕΙΝ ΤΟΝ ΑΣΚΗΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,103 | auto-corrected |
| joannes-chrysostomus.commentarius-in-job | ΚΕΦΑΛΑΙΟΝ ΠΡΩΤΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 26,757 | auto-corrected |
| joannes-chrysostomus.comparatio-regis-et-monachi-dub | 116 ΣΥΓΚΡΙΣΙΣ ΒΑΣΙΛΙΚΗΣ ΔΥΝΑΣΤΕΙΑΣ ΚΑΙ ΠΛΟΥΤΟΥ ΚΑΙ ΥΠΕΡΟΧΗΣ, ΠΡΟΣ ΜΟΝΑΧΟΝ ΣΥΖΩΝ- ΤΑ ΤΗ ΑΛΗΘΕΣΤΑΤΗ ΚΑΙ ΚΑΤΑ ΧΡΙΣΤΟΝ ΦΙΛΟΣΟΦΙΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,195 | auto-corrected |
| joannes-chrysostomus.contra-anomoeos-homilia-11 | Contra Anomoeos (homilia 11) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,096 | auto-corrected |
| joannes-chrysostomus.contra-eos-qui-subintroductas-habent-virgines | ΠΡΟΣ ΤΟΥΣ ΕΧΟΝΤΑΣ ΠΑΡΘΕΝΟΥΣ ΣΥΝΕΙΣΑΚΤΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,364 | auto-corrected |
| joannes-chrysostomus.contra-judaeos-gentiles-et-haereticos-et-in-illud-vocatus-est-jesus | ΠΡΟΣ ΙΟΥΔΑΙΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,635 | auto-corrected |
| joannes-chrysostomus.contra-ludos-et-theatra | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΟΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,100 | auto-corrected |
| joannes-chrysostomus.de-anna-sermones-1-5 | ΛΟΓΟΣ Αʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,310 | auto-corrected |
| joannes-chrysostomus.de-babyla-contra-julianum-et-gentiles | ΛΟΓΟΣ ΕΙΣ ΤΟΝ ΜΑΚΑΡΙΟΝ ΒΑΒΥΛΑΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,493 | auto-corrected |
| joannes-chrysostomus.de-beato-abraham-sp | ΕΙΣ ΤΟΝ ΜΑΚΑΡΙΟΝ ΑΒΡΑΑΜ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,541 | auto-corrected |
| joannes-chrysostomus.de-chananaea-dub | ΕΙΣ ΤΗΝ ΕΠΙΛΥΣΙΝ ΤΗΣ ΧΑΝΑΝΑΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,293 | auto-corrected |
| joannes-chrysostomus.de-christi-divinitate-contra-anomoeos-homilia-12 | De Christi divinitate (%6 Contra Anomoeos, homilia 12) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,647 | auto-corrected |
| joannes-chrysostomus.de-christi-precibus-contra-anomoeos-homilia-10 | De Christi precibus (%6 Contra Anomoeos, homilia 10) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,308 | auto-corrected |
| joannes-chrysostomus.de-coemeterio-et-de-cruce | ΕΙΣ ΤΟ ΟΝΟΜΑ ΤΟΥ ΚΟΙΜΗΤΗΡΙΟΥ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,935 | auto-corrected |
| joannes-chrysostomus.de-confessione-pretiosae-crucis-sp | 825 ΤΟΥ ΑΥΤΟΥ ΛΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,861 | auto-corrected |
| joannes-chrysostomus.de-davide-et-saule-homiliae-1-3 | ΟΜΙΛΙΑ Βʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,760 | auto-corrected |
| joannes-chrysostomus.de-decem-millium-talentorum-debitore | 1 ΕἸΣ ΤῊΝ ΠΑΡΑΒΟΛΗ͂Ν | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,702 | auto-corrected |
| joannes-chrysostomus.de-eleemosyna | ΠΕΡΙ ΕΛΕΗΜΟΣΥΝΗΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,192 | auto-corrected |
| joannes-chrysostomus.de-fato-et-providentia-orationes-1-6 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΙΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,074 | auto-corrected |
| joannes-chrysostomus.de-fugienda-simulata-specie-sp | ὍΤΙ ἘΠΙΠΛΑΣΤῸΝ ΣΧΗΜᾺ ΚΑῚ ΜῊ ἈΛΗΘΈΣ ΦΕΥΓΕΙ͂Ν ΧΡῊ, ὉΜΙΛΊΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 805 | auto-corrected |
| joannes-chrysostomus.de-laudibus-sancti-pauli-apostoli-homiliae-1-7 | ΕΙΣ ΤΟΝ ΑΓΙΟΝ ΑΠΟΣΤΟΛΟΝ ΠΑΥΛΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,862 | auto-corrected |
| joannes-chrysostomus.de-lazaro-homiliae-1-7 | 691 ΠΕΡΙ ΤΟΥ ΜΗ ΔΕΙΝ ΑΝΑΘΕΜΑΤΙΖΕΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,497 | auto-corrected |
| joannes-chrysostomus.de-libello-repudii | 203 ΕἸΣ ΤΟ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,685 | auto-corrected |
| joannes-chrysostomus.de-maccabeis-homiliae-1-3 | ΕἸΣ ΤΟῪΣ ἉΓΊΟΥΣ ΜΑΚΚΑΒΑΙΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,579 | auto-corrected |
| joannes-chrysostomus.de-melchisedech-sp | ΤΟΥ ΑΥΤΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,848 | raw OCR |
| joannes-chrysostomus.de-non-iterando-conjugio | ΤΟΥ ΑΥΤΟΥ ΠΡΟΣ ΤΗΝ ΑΥΤΗΝ ΠΕΡΙ ΜΟΝΑΝΔΡΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,815 | auto-corrected |
| joannes-chrysostomus.de-occursu-domini-de-deipara-et-symeone-sp | 819 ΕΙΣ ΤΗΝ ΥΠΑΠΑΝΤΗΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,013 | auto-corrected |
| joannes-chrysostomus.de-paenitentia-homiliae-1-9 | ΛΟΓΟΣ ΠΕΡΙ ΜΕΤΑΝΟΙΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 37,530 | auto-corrected |
| joannes-chrysostomus.de-perfecta-caritate-sp | ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,855 | auto-corrected |
| joannes-chrysostomus.de-precatione-orat-1-2-sp | ΤΟΥ ΑΥΤΟΥ ΠΕΡΙ ΠΡΟΣΕΥΧΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,897 | auto-corrected |
| joannes-chrysostomus.de-proditione-judae-homiliae-1-2 | 721 ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΗΝ ΠΡΟΔΟΣΙΑΝ ΤΟΥ ΙΟΥΔΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,710 | auto-corrected |
| joannes-chrysostomus.de-profectu-evangelii | 500 ΠΡΟΣ ΤΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,335 | auto-corrected |
| joannes-chrysostomus.de-resurrectione-mortuorum | ΠΕΡΙ ΤΗΣ ΤΩΝ ΝΕΚΡΩΝ ΑΝΑΣΤΑΣΕΩΣ ΟΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,376 | auto-corrected |
| joannes-chrysostomus.de-sacerdotio-lib-1-6 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΠΕΡΙ ΙΕΡΩΣΥΝΗΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 31,561 | auto-corrected |
| joannes-chrysostomus.de-sacerdotio-lib-7-sp | 813 ΤΟΥ ΑΥΤΟΥ [ΧΡΥΣΟΣΤΟΜΟΥ] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,695 | auto-corrected |
| joannes-chrysostomus.de-sancta-droside-martyre | 688 ΕΓΚΩΜΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,844 | auto-corrected |
| joannes-chrysostomus.de-sancta-pelagia-virgine-et-martyre |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,434 | raw OCR |
| joannes-chrysostomus.de-sancta-pentecoste-homiliae-1-2 | ΕἸΣ ΤῊΝ ἈΓΙΑΝ ΠΕΝΤΗΚΟΣΤΗΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,818 | auto-corrected |
| joannes-chrysostomus.de-sancta-thecla-martyre-sp | ΕἸΣ ΤῊΝ ἉΓΊΑΝ ΠΡΩΤΟΜΑΡΤΥΡΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,010 | raw OCR |
| joannes-chrysostomus.de-sancta-trinitate-sp | 797 ΧΡΥΣΟΣΤΟΜΟΥ ΟΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,447 | auto-corrected |
| joannes-chrysostomus.de-sanctis-bernice-et-prosdoce | ΕΙΣ ΤΑΣ ΑΓΙΑΣ ΜΑΡΤΥΡΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,142 | auto-corrected |
| joannes-chrysostomus.de-sancto-hieromartyre-babyla |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,781 | raw OCR |
| joannes-chrysostomus.de-sancto-hieromartyre-phoca | 1704 ΕΙΣ ΤΟΝ ΑΓΙΟΝ ΙΕΡΟΜΑΡΤΥΡΑ ΦΩΚΑΝ, ΚΑΙ ΚΑΤΑ ΑΙΡΕΤΙΚΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,300 | auto-corrected |
| joannes-chrysostomus.de-sancto-meletio-antiocheno | ΟΜΙΛΙΑ ΕΓΚΩΜΙΑΣΤΙΚΗ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,713 | auto-corrected |
| joannes-chrysostomus.de-terrae-motu | 747 ΟΜΙΛΙΑ ΜΕΤΑ ΤΟΝ ΣΕΙΣΜΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 856 | auto-corrected |
| joannes-chrysostomus.de-virginitate | ἈΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΠΕΡΙ ΠΑΡΘΕΝΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,564 | auto-corrected |
| joannes-chrysostomus.eclogae-ixlviii-ex-diversis-homiliis-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΕΚΛΟΓΑΙ ΑΠΟ ΔΙΑΦΟΡΩΝ ΛΟΓΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 152,674 | auto-corrected |
| joannes-chrysostomus.epistula-ad-caesarium-sp | 736-742 ΙΩΑΝΝΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 515 | auto-corrected |
| joannes-chrysostomus.epistula-ad-cyriacum-epist-125-recensiones | ΠΡΟΣ ΚΥΡΙΑΚΟΝ ΕΠΙΣΚΟΠΟΝ ΕΝ ΕΞΟΡΙΑ ΩΝΤΑ ΚΑΙ ΑΥΤΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,863 | auto-corrected |
| joannes-chrysostomus.epistula-ad-episcopos-presbyteros-et-diaconos | ΤΩ ΑΓΑΠΗΤΩ ΑΔΕΛΦΩ ΙΩΑΝΝΗ ΙΝΝΟΚΕΝΤΙΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,447 | auto-corrected |
| joannes-chrysostomus.epistulae-18-242 | 699 ΤΟΥ ΑΥΤΟΥ ΠΡΟΣ ΔΙΑΦΟΡΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,023 | auto-corrected |
| joannes-chrysostomus.epistulae-ad-olympiadem-epist-1-17 | ΤΗ ΔΕΣΠΟΙΝΗ ΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 48,801 | auto-corrected |
| joannes-chrysostomus.expositiones-in-psalmos | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΤΑ ΕΥΡΙΣΚΟΜΕΝΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 197,688 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-epistulas-catholicas | A ΚΕΦΑΛΑΙΟΝ ΠΡΩΤΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,772 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-jeremiam-in-catenis | ΤΟΥ ἉΓΙΟΥ ΙΩΑΝΝΟΥ ἈΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΕΞΗΓΗΣΕΩΣ ΕΙΣ ΤΟΝ ΙΕΡΕΜΙΑΝ ΠΡΟΦΗΤΗΝ ΤΑ ΣΩΖΟΜΕΝΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 50,676 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-proverbia-in-catenis | ΚΕΦΑΛ. Β’. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,452 | auto-corrected |
| joannes-chrysostomus.homilia-dicta-in-templo-sanctae-anastasiae | 540 ΟΜΙΛΙΑ Α΄. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,940 | auto-corrected |
| joannes-chrysostomus.homilia-dicta-postquam-reliquiae-martyrum | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,885 | auto-corrected |
| joannes-chrysostomus.homilia-habita-postquam-presbyter-gothus-concionatus-fuerat | ΟΜΙΛΙΑ Ηʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,408 | auto-corrected |
| joannes-chrysostomus.homilia-in-martyres | ΕἸΣ ΜΑΡΤΥΡΑΣ ὉΜΙΛΊΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,500 | auto-corrected |
| joannes-chrysostomus.in-acta-apostolorum-homiliae-1-55 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΤΑ ΕΥΡΙΣΚΟΜΕΝΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 168,933 | auto-corrected |
| joannes-chrysostomus.in-annuntiationem-beatae-virginis-sp | ΕἸΣ ΤῸΝ ΕΥΑΓΓΕΛΙΣΜΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,077 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-domini-nostri-jesu-christi | 768 ΤΟΥ ΑΥΤΟΥ ΕΙΣ ΤΗΝ ΑΝΑΛΗΨΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,595 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-sermo-1-sp | ΕἸΣ ΤῊΝ ἈΝΑΛΗΨΊΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 320 | raw OCR |
| joannes-chrysostomus.in-ascensionem-sermo-2-sp | ΕἸΣ ΤῊΝ ἈΝΑΛΗΨΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,099 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-sermo-3-sp | ΕΙΣ ΤΗΝ ΑΝΑΛΗΨΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,024 | auto-corrected |
| joannes-chrysostomus.in-dictum-pauli-nolo-vos-ignorare | ΕἸΣ ΤῸ ἈΠΟΣΤΟΛΙΚῸΝ ΡΗΤῸΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,445 | auto-corrected |
| joannes-chrysostomus.in-dictum-pauli-oportet-haereses-esse | 240 ΕΙΣ ΤΟ ΑΠΟΣΤΟΛΙΚΟΝ ΙΗΤΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,691 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-ephesios-homiliae-1-24 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ ΤΑ ΕΥΡΙΣΚΟΜΕΝΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,778 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-galatas-commentarius | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 100,004 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-hebraeos-homiliae-1-34 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 99,048 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-philemonem-homiliae-1-3 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ. ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΦΙΛΗΜΟΝΑ ΕΠΙΣΤΟΛΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 41,420 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-philippenses-homiliae-1-15 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΦΙΛΙΠΠΗΣΙΟΥΣ ΕΠΙΣΤΟΛΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 50,095 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-romanos-homiliae-1-32 | ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΕΡΜΗΝΕΙΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΡΩΜΑΙΟΥΣ ΕΠΙΣΤΟΛΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 191,638 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-titum-homiliae-1-6 | ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΟΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΤΙΤΟΝ ΕΠΙΣΤΟΛΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 16,231 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-corinthios-homiliae-1-44 | ΙΩΑΝΝΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΥΠΟΘΕΣΙΣ ΤΗΣ ΠΡΟΣ ΚΟΡΙΝΘΙΟΥΣ ΠΡΩΤΗΣ ΕΠΙΣΤΟΛΗΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 169,023 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-thessalonicenses-homiliae-1-11 | ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΘΕΣΣΑΛΟΝΙΚΕΙΣ ΕΠΙΣΤΟΛΗΝ ΠΡΩΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,736 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-timotheum-homiliae-1-18 | ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΗΝ ΠΡΟΣ ΤΙΜΟΘΕΟΝ ΕΠΙΣΤΟΛΗΝ ΠΡΩΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 51,490 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-corinthios-homiliae-1-30 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 94,697 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-thessalonicenses-homiliae-1-5 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,017 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-timotheum-homiliae-1-10 | 678 ΟΜΙΛΙΑ Δ’ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,520 | auto-corrected |
| joannes-chrysostomus.in-eutropium | ΕΥΤΡΟΠΙΟΝ ΕΥΝΟΥΧΟΝ ΠΑΤΡΙΚΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,812 | auto-corrected |
| joannes-chrysostomus.in-genesim-homiliae-1-67 | 423 ΟΜΙΛΙΑ ΜΒʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 265,702 | auto-corrected |
| joannes-chrysostomus.in-genesim-sermones-1-9 | 644-645 ΛΟΓΟΣ Αʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,910 | auto-corrected |
| joannes-chrysostomus.in-heliam-et-viduam | 328 ΕΙΣ ΤΟΝ ΗΛΙΑΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,980 | auto-corrected |
| joannes-chrysostomus.in-illud-filius-ex-se-nihil-facit | 103 ΛΟΓΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,406 | auto-corrected |
| joannes-chrysostomus.in-illud-habentes-eundem-spiritum-homiliae-1-3 | 260 ΕΙΣ ΤΗΝ ΑΠΟΣΤΟΛΙΚΗΝ ΡΗΣΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,630 | auto-corrected |
| joannes-chrysostomus.in-illud-hoc-scitote-quod-in-novissimis-diebus | ὉΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,650 | auto-corrected |
| joannes-chrysostomus.in-illud-in-faciem-ei-restiti |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 948 | raw OCR |
| joannes-chrysostomus.in-illud-isaiae-ego-dominus-deus-feci-lumen | 145 ΕΙΣ ΤΗΝ ΠΡΟΦΗΤΙΚΗΝ ΡΗΣΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,323 | auto-corrected |
| joannes-chrysostomus.in-illud-ne-timueritis-cum-dives-factus-fuerit-homo | ΕἸΣ ΤῸ ῬΗΤῸΝ ΤΟΥ͂ ΠΡΟΦΗΤΟΥ͂ ΔΑΥΊΔ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,285 | auto-corrected |
| joannes-chrysostomus.in-illud-pater-meus-usque-modo-operatur | 582 ΟΜΙΛΙΑ Θʹ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,580 | auto-corrected |
| joannes-chrysostomus.in-illud-pater-si-possibile-est-transeat | ΕἸΣ ΤΟ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,600 | auto-corrected |
| joannes-chrysostomus.in-illud-propter-fornicationes-autem-unusquisque-suam-uxorem | 193 ΕΙΣ ΤΟ ΑΠΟΣΤΟΛΙΚΟΝ ΡΗΤΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,892 | auto-corrected |
| joannes-chrysostomus.in-illud-salutate-priscillam-et-aquilam-sermones-1-2 | 173 ΕΙΣ ΤΟ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,745 | auto-corrected |
| joannes-chrysostomus.in-illud-si-esurierit-inimicus | 157 ΠΡΟΣ ΤΟΥΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,465 | auto-corrected |
| joannes-chrysostomus.in-illud-utinam-sustineretis-modicum | 291 ΕἸΣ ΤΟ ἈΠΟΣΤΟΛΙΚΟΝ ΡΗΤΟΝ, | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,065 | auto-corrected |
| joannes-chrysostomus.in-illud-vidi-dominum-homiliae-1-6 | ΕΠΑΙΝΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 19,835 | auto-corrected |
| joannes-chrysostomus.in-illud-vidua-eligatur | 311 ΕἸΣ ΤΟ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,297 | auto-corrected |
| joannes-chrysostomus.in-isaiam | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 36,943 | auto-corrected |
| joannes-chrysostomus.in-joannem-homiliae-1-88 | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΤΑ ΕΥΡΙΣΚΟΜΕΝΑ ΠΑΝΤΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 214,942 | auto-corrected |
| joannes-chrysostomus.in-martyres-aegyptios | 699 ΕΓΚΩΜΙΟΝ ΕΙΣ ΜΑΡΤΥΡΑΣ ΑΙΓΥΠΤΙΟΥΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,924 | auto-corrected |
| joannes-chrysostomus.in-matthaeum-homiliae-1-90 |  | qwen36-pg57 | Qwen3.6-27B | 321,593 | manual |
| joannes-chrysostomus.in-novam-dominicam-et-in-apostolum-thomam-sp | ΕἸΣ ΤῊΝ ΚΑΙΝῊΝ ΚΥΡΙΑΚῊΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,562 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-1-sp | 975 ΣΒΥΝΙΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,563 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-2-sp | ΕἸΣ ΤῊΝ ἉΓΊΑΝ ΠΕΝΤΗΚΟΣΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,021 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-3-sp | 794 ΕἸΣ ΤῊΝ ἉΓΊΑΝ ΠΕΝΤΗΚΟΣΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,807 | auto-corrected |
| joannes-chrysostomus.in-principium-actorum-homiliae-1-4 | 48-50 ΟΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 43,339 | auto-corrected |
| joannes-chrysostomus.in-psalmos-101-107-sp | ΤΑΛΜ. ΡΑ'. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 38,806 | auto-corrected |
| joannes-chrysostomus.in-psalmum-100-sp | ΕΙΣ ΤΟΝ Π’ ΥΑΛΜΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,989 | auto-corrected |
| joannes-chrysostomus.in-psalmum-118-homiliae-1-3-sp | ΣΤΑΣΙΣ Γʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,972 | auto-corrected |
| joannes-chrysostomus.in-psalmum-139-sp | 719 ΕἸΣ ΤΟ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,998 | auto-corrected |
| joannes-chrysostomus.in-psalmum-145 | 528 ΟΜΙΛΙΑ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,610 | auto-corrected |
| joannes-chrysostomus.in-quatriduanum-lazarum | ΛΟΓΟΣ ΕΙΣ ΤΟΝ ΤΕΤΡΑΗΜΕΡΟΝ ΛΑΖΑΡΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,569 | auto-corrected |
| joannes-chrysostomus.in-quatriduanum-lazarum-contra-anomoeos-homilia-9-sp | In quatriduanum Lazarum (%6 Contra Anomoeos, homilia 9) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,338 | auto-corrected |
| joannes-chrysostomus.in-sanctos-petrum-et-heliam-sp | 730 ΛΟΓΟΣ ΕΙΣ ΠΕΤΡΟΝ ΤΟΝ ΑΠΟΣΤΟΛΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,715 | auto-corrected |
| joannes-chrysostomus.in-sanctum-barlaam-martyrem |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,952 | auto-corrected |
| joannes-chrysostomus.in-sanctum-eustathium-antiochenum | ET‘ΚΩΜΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,149 | auto-corrected |
| joannes-chrysostomus.in-sanctum-ignatium-martyrem | ΕΓΚΩΜΙΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,836 | auto-corrected |
| joannes-chrysostomus.in-sanctum-julianum-martyrem | ΕΓΚΩΜΙΟΝ ΕΙΣ ΤΟΝ ΑΓΙΟΝ ΜΑΡΤΥΡΑ ΙΟΥΛΙΑΝΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,935 | auto-corrected |
| joannes-chrysostomus.in-sanctum-lucianum-martyrem | 524 ΟΜΙΛΙΑ ΕΓΚΩΜΙΑΣΤΙΚΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,518 | auto-corrected |
| joannes-chrysostomus.in-sanctum-pascha | 750 ΕΙΣ ΤΟ ΑΓΙΟΝ ΠΑΣΧΑ ΛΟΓΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,736 | auto-corrected |
| joannes-chrysostomus.in-sanctum-romanum-homilia-1 | ΕἸΣ ΤῸΝ ἉΓΙΟΝ ΜΑΡΤΥΡΑ ῬΩΜΑΝΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,531 | auto-corrected |
| joannes-chrysostomus.in-triduanam-resurrectionem-domini-sp | ΕΙΣ ΤΗΝ ΤΡΙΗΜΕΡΟΝ ΑΝΑΣΤΑΣΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,729 | auto-corrected |
| joannes-chrysostomus.interpretatio-in-danielem-prophetam-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ, ΑΡΧΙΕΠΙΣΚΟΠΟΥ ΚΩΝΣΤΑΝΤΙΝΟΥΠΟΛΕΩΣ, ΕΡΜΗΝΕΙΑ ΕΙΣ ΤΟΝ ΔΑΝΙΗΛ ΠΡΟΦΗΤΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,858 | auto-corrected |
| joannes-chrysostomus.laus-diodori-episcopi | 747 ΕΓΚΩΜΙΟΝ ΕΙΣ ΔΙΟΔΩΡΟΝ ΕΠΙΣΚΟΠΟΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 976 | auto-corrected |
| joannes-chrysostomus.oratio-secunda-sp | ΕΥΧΗ ΔΕΥΤΕΡΑ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,727 | raw OCR |
| joannes-chrysostomus.peccata-fratrum-non-evulganda | 344 ΠΕΡΙ ΤΟΥ ΜΗ ΔΗΜΟΣΙΕΥΕΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,120 | auto-corrected |
| joannes-chrysostomus.pg048 | ΧΡΥΣΟΣΤΟΜΟΥ ὉΜΙΛΙΑ ΠΡΩΤΗ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 35,766 | auto-corrected |
| joannes-chrysostomus.pg052 | ΕἸΣ ΤῊΝ ἈΝΑΛΗΨΙΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,112 | auto-corrected |
| joannes-chrysostomus.post-reditum-priore-exsilio-sermo-2 | 426-427 ΤΟΥ ΑΥΤΟΥ ΕΠΑΝΕΛΘΟΝΤΟΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,942 | auto-corrected |
| joannes-chrysostomus.prooemia-in-psalmos-fragmenta-sp | ΠΡΟΟΙΜΙΑ ΤΩΝ ΨΑΛΜΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,506 | auto-corrected |
| joannes-chrysostomus.quales-ducendae-sint-uxores-encomium-ad-maximum | [314] ΕΓΚΩΜΙΟΝ ΕἸΣ ΜΑΞΊMΟN | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,130 | auto-corrected |
| joannes-chrysostomus.quod-regulares-feminae-viris-cohabitare-non-debeant | ΠΕΡΙ ΤΟΥ ΤΑΣ ΚΑΝΟΝΙΚΑΣ ΜΗ ΣΥΝΟΙΚΕΙΝ ΑΝΔΡΑΣΙΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,151 | auto-corrected |
| joannes-chrysostomus.sermo-antequam-iret-in-exsilium | ΟΜΙΛΙΑ ΠΡΟ ΤΗΣ ΕΞΟΡΙΑΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,863 | auto-corrected |
| joannes-chrysostomus.sermo-cum-iret-in-exsilium | 420-421 OTE ΑΠΗΕΙ ΕΝ ΤΗ ΕΕΟΠΙΑ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 833 | raw OCR |
| joannes-chrysostomus.synopsis-scripturae-sacrae-sp | ΤΟΥ ΕΝ ΑΓΙΟΙΣ ΠΑΤΡΟΣ ΗΜΩΝ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 38,959 | auto-corrected |
| joannes-damascenus.adversus-iconoclastas-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,083 | auto-corrected |
| joannes-damascenus.commentarii-in-epistulas-pauli-dub | ΙΩΑΝΝΟΥ ΤΟΥ ΔΑΜΑΣΚΗΝΟΥ ΕΚ ΤΗΣ ΚΑΘΟΛΟΥ ΕΡΜΗΝΕΙΑΣ ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ ΕΚΛΟΓΑΙ ΕΚΛΕΓΕΙΣΑΙ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 96,100 | auto-corrected |
| joannes-damascenus.contra-nestorianos | ΙΩΑΝΝΟΥ ΤΟΥ ΔΑΜΑΣΚΗΝΟΥ ΚΑΤΑ ΤΗΣ ΑΙΡΕΣΕΩΣ ΤΩΝ ΝΕΣΤΟΡΙΑΝΩΝ ΕΠΟΣ ΑΚΡΙΒΕΣΤΑΤΟΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,874 | auto-corrected |
| joannes-damascenus.de-azymis-fragmenta-duo-sp |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,274 | raw OCR |
| joannes-damascenus.de-duabus-in-christo-voluntatibus | ΚΕΦΑΛ. Ηʹ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,773 | auto-corrected |
| joannes-damascenus.de-immaculato-corpore-sp | ΕΠΙΣΤΟΛΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,281 | auto-corrected |
| joannes-damascenus.de-natura-composita-sive-contra-acephalos | ΕΠΙΔΕΙΞΙΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,273 | auto-corrected |
| joannes-damascenus.de-octo-spiritibus-nequitiae-fragmentum-sp | ΤΩΝ ΟΚΤΩ ΤΗΣ ΠΟΝΗΡΙΑΣ ΠΝΕΥΜΑΤΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,340 | auto-corrected |
| joannes-damascenus.de-sacris-imaginibus-contra-constantinum-cabalinum-sp | ΛΟΓΟΣ ἈΠΟΔΕΙΚΤΙΚΟΣ ΠΕΡΙ ΤΟΝ ΑΓΙΟΝ ΚΑΙ ΣΕΠΤΟΝ ΕΙΚΟΝΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,953 | auto-corrected |
| joannes-damascenus.de-sacris-jejuniis | ΙΩΑΝΝΟΥ ΠΡΕΣΒΥΤΕΡΟΥ ΔΑΜΑΣΚΗΝΟΥ ΙΕΠΙ ΤΩΝ ΑΓΙΩΝ ΝΗΣΤΕΙΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,456 | auto-corrected |
| joannes-damascenus.de-sancta-trinitate-fragmentum-dub |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,056 | raw OCR |
| joannes-damascenus.disputatio-christiani-et-saraceni-dub |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,727 | raw OCR |
| joannes-damascenus.epistula-de-hymno-trisagio | ΠΡΟΣ ΙΟΡΔΑΝΗΝ ΑΡΧΙΜΑΝΔΡΙΤΗΝ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,954 | auto-corrected |
| joannes-damascenus.institutio-elementaris |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,837 | raw OCR |
| joannes-damascenus.oratio-de-his-qui-in-fide-dormierunt-sp | ΟΝΟΣ ΑΙ ΥΠΕΡ ΑΥΤΟΝ ΓΙΝΟΜΕΝΑΙ ΑΕΙΟΥΡΓΙΑΙ ΚΑΙ ΕΥΠΟΙΙΑΙ ΤΟΥΤΟΥΣ ΟΝΟΜΑΖΙΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,979 | auto-corrected |
| joannes-damascenus.passio-sancti-artemii-dub |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,798 | auto-corrected |
| joannes-damascenus.quid-est-homo-fragmentum-dub | 580 ΠΑΣΧΑΛΙΟΝ ΤΟΥ ἉΓΙΟΥ ἸΩΑΝΝΟΥ ΤΟΥ ΔΑΜΑΣΚΗΝΟΥ. ΟΙ ΚΥΚΛΟΙ ΤΟΥ ἩΛΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,093 | auto-corrected |
| joannes-damascenus.sacra-parallela-recensiones-secundum-alphabeti-litteras-dispositae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 115,935 | auto-corrected |
| joannes-epiphaniensis.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 1,676 | auto-corrected |
| joannes-grammar.ekfrasis-tou-kosmikou-pi-nakos |  | qwen36-joannes_geometres_pg106 | Qwen3.6-27B | 200,423 | auto-corrected |
| joannes-laurentius-lydus.de-magistratibus-populi-romani |  | qwen36-lydus_mensibus_wuensch | Qwen3.6-27B | 43,809 | auto-corrected |
| joannes-stobaeus-anthologus.anthologium |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 434,198 | manual |
| joannes-tzetzes.tzetzes-historiae-kiessling |  | qwen36-tzetzes_historiae_kiessling | Qwen3.6-27B | 103,890 | auto-corrected |
| laetus.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 439 | auto-corrected |
| lamprocles.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,171 | auto-corrected |
| lesbonax-rhetoric.politiko-s | LESBONAX — De figuris | qwen36-lesbonax | Qwen3.6-27B | 970 | raw OCR |
| leucippus.testimonia | LEUCIPPUS — Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,614 | auto-corrected |
| lexicon-sabbaiticum.lexicon-sabbaiticum-e-cod-sabbaitico-137 |  | [archive.org](https://archive.org/details/lexicon-sabbaiticum-athanasios-papadopulos-kerameus) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 5,085 | auto-corrected |
| licymnius.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,119 | auto-corrected |
| limenius.paean-delphicus-ii-et-prosodium-in-apollinem |  | qwen36-limenius_delphic_fairbanks | Qwen3.6-27B | 7,151 | auto-corrected |
| lucius-annaeus-cornutus.cornutus-lang |  | qwen36-cornutus_lang | Qwen3.6-27B | 23,070 | auto-corrected |
| lycon-tarentinus-vel-iasensis.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 381 | raw OCR |
| lycophron-tragedy.fragmenta | ΜΕΝΕΔΗΜΟΣ ΣΑΤΤΡΟΙ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 302 | auto-corrected |
| lycophronides.fragmenta | LYCOPHRONIDES — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 20 | raw OCR |
| lynceus.fragmentum | LYNCEUS — Fragmentum | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 108 | raw OCR |
| lyrica-adespota-ca.fragmenta-lyrica |  | qwen36-lyrica_adespota_bergk_plg3 | Qwen3.6-27B | 58,464 | auto-corrected |
| lysippus.fragmenta | ΑΔΗΛΩΝ ΔΡΑΜΑΤΩΝ | kock-caf1-ocr-frag | Qwen3.6-27B | 333 | raw OCR |
| magnes.fragmenta | ΒΑΡΒΙΤΙΣΤΑΙ ΒΑΤΡΑΧΟΙ | kock-caf1-ocr-frag | Qwen3.6-27B | 62 | raw OCR |
| magnus.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 793 | auto-corrected |
| manetho.fragmenta | Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 3,012 | auto-corrected |
| mantissa-proverbiorum.mantissa-proverbiorum |  | [archive.org](https://archive.org/details/corpusparoemiogr02leutuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 167,247 | auto-corrected |
| marcellinus.vita-thucydidis |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 97,476 | auto-corrected |
| maximus-rhetoric.peri-tw-n-lu-twn-ntiqe-sewn-fort-auctore-maximo |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,985 | auto-corrected |
| melanippides.fragmenta | MELANIPPIDES — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 247 | raw OCR |
| melanthius-elegy.fragmentum |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 73 | raw OCR |
| melanthius.fragmentum |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 277 | auto-corrected |
| melissus.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,094 | auto-corrected |
| menander-comedy.fragmenta-2 | Menander — Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 26,967 | raw OCR |
| menecrates-elaita.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 573 | auto-corrected |
| menecrates-poet-phil.fragmentum-et-titulus |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 148 | raw OCR |
| menecrates.titulus | MENECRATES — Titulus | kock-caf3-ocr | Qwen3.6-27B | 92 | raw OCR |
| menestor.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 668 | auto-corrected |
| metagenes.fragmenta | ΜΕΤΑΓΕΝΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 493 | auto-corrected |
| metopus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 461 | raw OCR |
| metrodorus-koerte |  | qwen36-metrodorus_koerte | Qwen3.6-27B | 7,588 | auto-corrected |
| metrodorus-major.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 849 | raw OCR |
| metrodorus-philosophy.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,725 | auto-corrected |
| metrophanes.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 271 | raw OCR |
| michael.in-ethica-nicomachea-ixx-commentaria | MICHAEL EPHESIUS — In Ethica Nicomachea commentaria (CAG XX) | qwen36-commentariainari20bero | Qwen3.6-27B | 6,107 | raw OCR |
| milon.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 54 | auto-corrected |
| mimnermus-elegy.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 594 | auto-corrected |
| mimnermus-tragedy.fragmenta | MIMNERMUS TRAGICUS — Fragmenta (TGF Nauck) | qwen36-nauck-tgf-mimnermus | Qwen3.6-27B | 1,085 | raw OCR |
| mnesimachus-comedy.fragmenta | 436 ΜΝΗΣΙΜΑΧΟΥ | kock-caf2-ocr-frag | Qwen3.6-27B | 697 | raw OCR |
| moderatus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 608 | auto-corrected |
| moeris.lexicon-atticum |  | [archive.org](https://archive.org/details/moeridisatticis00moergoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 57,621 | auto-corrected |
| monimus-cynicus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 299 | auto-corrected |
| moschion.fragmenta | ΘΕΜΙΣΤΟΚΛΗΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 491 | raw OCR |
| moses.eu-poi-kai-eu-tuxi-tou-ktisame-nou-kai-e-pituxi-kama-tou-kai |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,735 | auto-corrected |
| mullach-fpg2.paratexta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 37,442 | auto-corrected |
| musaeus-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 834 | auto-corrected |
| myron.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 369 | auto-corrected |
| myrtilus.fragmenta | MYRTILUS — Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 139 | raw OCR |
| nausicrates.fragmenta | ΝΑΤΣΙΚΡΑΤΗΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 69 | raw OCR |
| nausiphanes.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,173 | auto-corrected |
| nechepso-petosiris-riess |  | qwen36-nechepso_petosiris_riess | Qwen3.6-27B | 831 | auto-corrected |
| neophron.fragmenta | ΜΗΔΕΙΑ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 332 | auto-corrected |
| neoptolemus.fragmenta | NEOPTOLEMUS — Fragmenta | qwen36-alexander_aetolus_meineke-ocr | Qwen3.6-27B | 144 | raw OCR |
| nessas.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 142 | auto-corrected |
| nestorianus.fragmenta |  | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 216 | raw OCR |
| nicephorus-blemmydes.aper-xrh-zei-h-parou-sa-kataskeuh-fort-auctore |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 318 | raw OCR |
| nicephorus-blemmydes.nikhfo-rou-tou-blemmu-dou-peri-th-s-xrusopoii-as-fort |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,581 | auto-corrected |
| nicetas-heracleensis.fragmenta-commentariorum-xvi-orationum-gregorii-nazianzeni | Nicetas Heracleensis — Fragmenta commentariorum XVI orationum Gregorii Nazianzeni | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,330 | auto-corrected |
| nicias-history.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 65 | raw OCR |
| nicochares.fragmenta | ΝΙΚΟΧΑΡΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 320 | raw OCR |
| nicolaus-history.nicolaus-progymnasmata-felten |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,207 | auto-corrected |
| nicolaus.fragmenta | NICOLAUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 141 | raw OCR |
| nicomachus.fragmenta | NICOMACHUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 158 | raw OCR |
| nicophon.fragmenta | ΑΦΡΟΔΙΤΗΣ ΓΟΝΑΙ | kock-caf1-ocr-frag | Qwen3.6-27B | 559 | raw OCR |
| nicostratus.fragmenta | ΝΙΚΟΣΤΡΑΤΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 966 | auto-corrected |
| nonnosus.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 880 | raw OCR |
| ocellus.de-universi-natura-sp |  | qwen36-hierocl_aureum_mullach_fpg1-ocr | Qwen3.6-27B | 5,416 | auto-corrected |
| ocr.walz_rhetores_v1 |  | [archive.org](https://archive.org/details/rhetoresgraeciem01walzuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 142,191 | manual |
| ocr.walz_rhetores_v4 |  | [archive.org](https://archive.org/details/rhetoresgraeciem04walzuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 226,107 | manual |
| ocr.walz_rhetores_v5 |  | [archive.org](https://archive.org/details/rhetoresgraeciem05walzuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 157,587 | manual |
| ocr.walz_rhetores_v7pt2 |  | [archive.org](https://archive.org/details/p2rhetoresgraeci07walzuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 163,069 | manual |
| ocr.walz_rhetores_v9 |  | [archive.org](https://archive.org/details/rhetoresgraeciem09walzuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 135,196 | manual |
| oenopides.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,449 | auto-corrected |
| onatas.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 425 | auto-corrected |
| ophelio.fragmenta | Ὠ Φ Ε Λ Ι Ὦ Ν | kock-caf2-ocr-frag | Qwen3.6-27B | 130 | auto-corrected |
| oracula-chaldaica.oracula-fragmenta-olim-sub-auctore-juliano-theurgo |  | qwen36-oracula_chaldaica_kroll | Qwen3.6-27B | 8,252 | auto-corrected |
| oribasius.collectiones-medicae-lib-1-16-24-25-43-50 |  | qwen36-bussemaker-daremberg-1851-rover | Qwen3.6-27B | 314,942 | manual |
| oribasius.collectiones-medicae-libri-incerti |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,777 | manual |
| oribasius.libri-ad-eunapium-lib-1-4 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,440 | auto-corrected |
| oribasius.synopsis-ad-eustathium-filium |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 78,515 | auto-corrected |
| orphica.argonautica | ORPHICA — Argonautica | qwen36-abel-orphica-argonautica | Qwen3.6-27B | 6,788 | raw OCR |
| orphica.hymni | ORPHICA — Hymni | qwen36-abel-orphica-hymni | Qwen3.6-27B | 5,509 | raw OCR |
| orphica.lithica | ORPHICA — Lithica | qwen36-abel-orphica-lithica | Qwen3.6-27B | 2,501 | raw OCR |
| orphica.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,779 | auto-corrected |
| ostanes-magus.osta-nou-filoso-fou-pro-s-peta-sion-peri-th-s-i-era-s-tau-ths-kai |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 415 | auto-corrected |
| pancrates-epigram.fragmenta | PANCRATES — Fragmenta | qwen36-oxyrhynchuspapyr08gren | Qwen3.6-27B | 157 | raw OCR |
| panyassis.fragmenta-epica |  | qwen36-panyassis_kinkel_egf | Qwen3.6-27B | 33,044 | auto-corrected |
| parmenides.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 18,838 | auto-corrected |
| parmiscus.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 133 | raw OCR |
| paron.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 183 | raw OCR |
| patrocles.fragmenta |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 131 | auto-corrected |
| paulus-medicine.epitomae-medicae-libri-septem |  | qwen36-paulus_aegineta_heiberg_cmg9 | Qwen3.6-27B | 118,783 | auto-corrected |
| paulus-silentiarius.descriptio-sanctae-sophiae |  | qwen36-paulsilent_descriptio_bekker | Qwen3.6-27B | 45,091 | auto-corrected |
| pausanias-attic.attikw-n-o-noma-twn-sunagwgh |  | qwen36-aelius_dionysius_schwabe-ocr | Qwen3.6-27B | 19,724 | auto-corrected |
| pelagius.pelagi-ou-filoso-fou-peri-th-s-qei-as-tau-ths-kai-i-era-s-te-xnhs |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 2,274 | auto-corrected |
| pempelus.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 227 | raw OCR |
| perictione.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 1,242 | auto-corrected |
| persaeus.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,635 | auto-corrected |
| petron.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 214 | raw OCR |
| phaenias.fragmenta |  | qwen36-demochares_fhg2-ocr | Qwen3.6-27B | 662 | raw OCR |
| phaleas-et-hippodamus.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,237 | raw OCR |
| phanocles.fragmenta |  | qwen36-philetas_bach_1829-ocr | Qwen3.6-27B | 2,447 | auto-corrected |
| pherecrates.fragmenta | ΦΕΡΕΚΡΑΤΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 5,105 | auto-corrected |
| pherecydes-mythography.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,262 | auto-corrected |
| philemon-junior.fragmenta | ΦΙΛΗΜΩΝ Ὁ ΝΕΩΤΕΡΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 111 | raw OCR |
| philemon.fragmenta | ἈΓΡΟΙΚΟΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 5,854 | auto-corrected |
| philetaerus.fragmenta | ΑΔΩΝΙΑΖΟΥΣΑΙ | kock-caf2-ocr-frag | Qwen3.6-27B | 413 | raw OCR |
| philetas.fragmenta |  | qwen36-philetas_bach_1829 | Qwen3.6-27B | 6,359 | auto-corrected |
| philippides.fragmenta | PHILIPPIDES — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 1,003 | raw OCR |
| philippus-history.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 159 | raw OCR |
| philiscus-comedy.fragmenta | ἈΔΏΝΙΣ ἈΡΤΕΜΙΔΟΣ ΚΑῚ ἈΠΟΛΛΩΝΟΣ ΓΟΝΑῚ ΔΙΟΣ ΓΟΝΑῚ | kock-caf2-ocr-frag | Qwen3.6-27B | 88 | raw OCR |
| philocles-tragedy.fragmenta | ΤΗΡΕΤΣ v. ΠΑΝΔΙΟΝΙΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 216 | auto-corrected |
| philodamus.paean-in-dionysum |  | qwen36-limenius_delphic_fairbanks-ocr | Qwen3.6-27B | 658 | auto-corrected |
| philodemus.tlg1595-tlg003 | PHILODEMUS — Index Stoicorum Herculanensis | qwen36-rivistadifilolog03-p469-576 | Qwen3.6-27B | 1,890 | raw OCR |
| philodemus.tlg1595-tlg241 | PHILODEMUS — De oeconomia | qwen36-philodemiperioik00phil | Qwen3.6-27B | 15,357 | raw OCR |
| philodemus.tlg1595-tlg267 | PHILODEMUS — De ira | qwen36-philodemiepicur00philgoog | Qwen3.6-27B | 7,657 | raw OCR |
| philodemus.tlg1595-tlg271 | PHILODEMUS — De libertate dicendi (Peri parrhesias) | qwen36-philodemiperipar00philuoft | Qwen3.6-27B | 7,162 | raw OCR |
| philodemus.tlg1595-tlg289 | PHILODEMUS — De poematis (Peri poiematon) | qwen36-philodemiperipoi00haus | Qwen3.6-27B | 1,661 | raw OCR |
| philodemus.tlg1595-tlg472 | PHILODEMUS — De signis (Peri semeion kai semeioseon) | qwen36-philodemberindu00gompgoog | Qwen3.6-27B | 3,348 | raw OCR |
| philodemus.tlg1595-tlg492 | PHILODEMUS — De bono rege secundum Homerum | qwen36-philodemiperitou00philuoft | Qwen3.6-27B | 6,928 | raw OCR |
| philodemus.tlg1595-tlg601 |  | [Philodemus, Academicorum index Herculanensis, ed. Mekler, Berlin 1902](https://archive.org/details/academicorumphil00mekluoft) | Qwen3.6-27B | 9,689 | auto-corrected |
| philodemus.volumina-rhetorica | De rhetorica (Volumina rhetorica) | [Philodemus, Volumina rhetorica vol.1, ed. Sudhaus, Teubner 1892](https://archive.org/details/philodemivolumi00schugoog) | Qwen3.6-27B | 73,196 | auto-corrected |
| philolaus.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,417 | auto-corrected |
| philonides.fragmenta | ΑΔΗΛΩΝ ΔΡΑΜΑΤΩΝ | kock-caf1-ocr-frag | Qwen3.6-27B | 118 | raw OCR |
| philosophus-anonymus.anepigra-fou-filoso-fou-kata-kolouqi-xrh-sews-e-mfai-non |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,004 | auto-corrected |
| philosophus-anonymus.anepigra-fou-filoso-fou-peri-qei-ou-u-datos-th-s-leukw-sews |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 830 | auto-corrected |
| philosophus-anonymus.anepigra-fou-filoso-fou-peri-th-s-qei-as-kai-i-era-s-te-xnhs |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 2,857 | auto-corrected |
| philosophus-christianus.anti-qesis-le-gousa-o-ti-qei-on-u-dwr-e-n-e-sti-tw-ei-dei |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 466 | raw OCR |
| philosophus-christianus.apori-e-n-bu-ssaion-u-dwr-e-n-tw-riqmw-deiknu-ein |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 431 | auto-corrected |
| philosophus-christianus.h-tou-muqikou-u-datos-poi-hsis-e-cod-venet-marc-299 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 856 | auto-corrected |
| philosophus-christianus.oti-tetraxw-s-diairoume-nhs-th-s-u-lhs-dia-foroi-pogi-nontai |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 219 | auto-corrected |
| philosophus-christianus.po-sai-ei-si-n-ai-kat-ei-dos-kai-ge-nos-diaforai-tw-n-poih-sewn |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 916 | auto-corrected |
| philosophus-christianus.pw-s-dei-noei-n-diafora-s-tw-n-poih-sewn-kai-sxh-masi-gewmetrikoi-s |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 243 | raw OCR |
| philosophus-christianus.ti-s-h-e-n-pokru-fois-tw-n-palaiw-n-e-kdidome-nh-ta-cis-e |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,408 | auto-corrected |
| philosophus-christianus.ti-s-h-kaqo-lou-tou-u-datos-oi-konomi-e-cod-venet |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 37 | auto-corrected |
| philosophus-christianus.ti-s-h-tw-n-rxai-wn-diafwni-e-cod-venet-marc-299 |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 263 | auto-corrected |
| philosophus-christianus.tou-xristianou-peri-eu-staqei-as-tou-xrusou-e-cod |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 949 | auto-corrected |
| philosophus-christianus.tou-xristianou-peri-tou-qei-ou-u-datos-e-cod-venet |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 134 | auto-corrected |
| philosophus-christianus.tou-xristianou-su-noyis-ti-s-h-ai-ti-th-s-prokeime-nhs |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 85 | raw OCR |
| philostephanus.fragmenta |  | qwen36-aristobulus_fhg3-ocr | Qwen3.6-27B | 96 | raw OCR |
| philoxenus.fragmenta | PHILOXENUS — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 977 | auto-corrected |
| philyllius.fragmenta | ΔΩΔΕΚΆΤΗ | kock-caf1-ocr-frag | Qwen3.6-27B | 559 | raw OCR |
| phintys.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 819 | auto-corrected |
| phocylides.sententiae | PHOCYLIDES — Sententiae | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 909 | auto-corrected |
| phoebammon.de-figuris-fort-auctore-phoebammone-alio |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 120,800 | auto-corrected |
| phoenicides.fragmenta | PHOENICIDES — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 285 | raw OCR |
| phoenix.fragmenta |  | qwen36-phoenix_choliambi_crusius | Qwen3.6-27B | 27,870 | auto-corrected |
| photius.bibliotheca |  | [archive.org](https://archive.org/details/bub_gb_NsiGxvHyQY0C) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 153,418 | auto-corrected |
| photius.lexicon |  | [archive.org](https://archive.org/details/photiipatriarch00nabegoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 102,580 | raw OCR |
| phrynichus-comedy.fragmenta | ΦΡΤΝΙΧΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 1,669 | auto-corrected |
| phrynichus-tragedy.fragmenta | ΑΙΓΥΠΤΙΟΙ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 642 | raw OCR |
| pigres.fragmentum |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 623 | raw OCR |
| pindarus.fragmenta |  | [Pindar, ed. Schroeder (Teubner)](https://archive.org/search?query=Pindari+carmina+Schroeder) | Qwen3.6-27B | 11,904 | auto-corrected |
| pisander-epic.heraclea-fragmenta |  | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 28 | raw OCR |
| plato-comedy.fragmenta | ΠΛΑΤΩΝ | kock-caf1-ocr-frag | Qwen3.6-27B | 5,836 | auto-corrected |
| platonius.fragmenta-de-comoedia-graeca |  | qwen36-platonius_duebner_scholaristoph1 | Qwen3.6-27B | 353,853 | auto-corrected |
| poliochus.fragmenta | POLIOCHUS — Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 192 | auto-corrected |
| polus-lucanus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 184 | raw OCR |
| polyclitus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 761 | auto-corrected |
| polystratus.peri-lo-gou-katafronh-sews-p-herc-336-1150 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,275 | auto-corrected |
| polyzelus.fragmenta | ΔΙΟΝΤΕΟΤ ΓΟΝΑΙ | kock-caf1-ocr-frag | Qwen3.6-27B | 312 | raw OCR |
| pompeius-macer.fragmentum |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 213 | raw OCR |
| porphyrius.chronica |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 2,162 | auto-corrected |
| porphyrius.contra-christianos-fragmenta | PORPHYRIUS — Contra Christianos (fragmenta, Harnack) | qwen36-harnack-porphyry | Qwen3.6-27B | 12,746 | raw OCR |
| porphyrius.ei-s-ta-rmonika-ptolemai-ou-u-po-mnhma | PORPHYRIUS — In Ptolemaei Harmonica commentarius | qwen36-porphyry-in-ptol-bub | Qwen3.6-27B | 64,042 | raw OCR |
| porphyrius.epistula-ad-anebonem | PORPHYRIUS — Epistula ad Anebonem | qwen36-parthey-anebonem | Qwen3.6-27B | 2,413 | raw OCR |
| posidippus.fragmenta | POSIDIPPUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 882 | raw OCR |
| potamon.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 43 | raw OCR |
| pratinas.fragmenta | ΔΤΣΜΑΙΝΑΙ Η ΚΑΡΤΑΤΙΔΕΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 107 | raw OCR |
| praxilla.fragmenta | PRAXILLA — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 228 | raw OCR |
| priscianus.metaphrasis-in-theophrastum |  | qwen36-priscianus_lydus_bywater | Qwen3.6-27B | 108,391 | auto-corrected |
| priscus-history.testimonia |  | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 157 | auto-corrected |
| proclus.in-platonis-timaeum-commentaria |  | qwen36-proclus_timaeus_v1 | Qwen3.6-27B | 551,839 | manual |
| proclus.institutio-theologica |  | qwen36-proclus_didot_et-1855 | Qwen3.6-27B | 29,018 | auto-corrected |
| procopius-rhetoric.epistulae-1-166 |  | qwen36-aristaenetus_hercher_epistolographi-ocr | Qwen3.6-27B | 24,009 | auto-corrected |
| prodicus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,708 | auto-corrected |
| proros-amyclas-clinias.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 329 | raw OCR |
| protagoras.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,472 | auto-corrected |
| pseudo-archytas.fragmenta |  | qwen36-archytas_mullach_fpg2-ocr | Qwen3.6-27B | 4,645 | auto-corrected |
| pseudo-zonaras.lexicon |  | [archive.org](https://archive.org/details/lexiconextribus00albegoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 163,286 | manual |
| ptolemaeus-grammar.ptolemaeus-gramm-valckenaer-ammonius |  | qwen36-ptolemaeus_gramm_valckenaer_ammonius | Qwen3.6-27B | 55,164 | auto-corrected |
| pythagoras.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 6,574 | auto-corrected |
| pythagoristae-d-k.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 23,856 | auto-corrected |
| rhianus.fragmenta |  | qwen36-alexander_aetolus_meineke-ocr | Qwen3.6-27B | 2,073 | auto-corrected |
| rhinthon.fragmenta |  | qwen36-rhinthon_kaibel_cgf_1899 | Qwen3.6-27B | 37,390 | auto-corrected |
| salmanas.me-qodos-di-h-s-potelei-tai-h-sfairoeidh-s-xa-laza |  | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 950 | raw OCR |
| sannyrion.fragmenta | ΔΑΝΑΗ | kock-caf1-ocr-frag | Qwen3.6-27B | 81 | raw OCR |
| sappho.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,087 | auto-corrected |
| satyrus.vita-euripidis-p-oxy-9-1176 | Vita Euripidis (P. Oxy. 9.1176) | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 449 | raw OCR |
| scholia-in-aelium-aristidem.scholia-in-aelium-aristidem-scholia-vetera |  | [archive.org](https://archive.org/details/scholiainaeliia00unkngoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 117,366 | auto-corrected |
| scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera |  | qwen36-schol_aeschin_dindorf | Qwen3.6-27B | 31,648 | auto-corrected |
| scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera |  | [archive.org](https://archive.org/details/bub_gb_aw-IxD1dCOwC) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 350 dpi) | 116,896 | auto-corrected |
| scholia-in-apollonium-rhodium.scholia-in-apollonii-rhodii-argonautica-scholia-vetera |  | [archive.org](https://archive.org/details/bub_gb_oBI-AAAAcAAJ) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 120,106 | auto-corrected |
| scholia-in-aratum.scholia-in-aratum-scholia-vetera |  | [archive.org](https://archive.org/details/Maass1898) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 156,497 | auto-corrected |
| scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii |  | [archive.org](https://archive.org/details/scholiagraecaina00dbuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 350,911 | auto-corrected |
| scholia-in-callimachum.schol-callim-schneider |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,499 | auto-corrected |
| scholia-in-demosthenem.scholia-demosthenem-dindorf-v8 |  | qwen36-scholia_demosthenem_dindorf_v8 | Qwen3.6-27B | 109,085 | auto-corrected |
| scholia-in-hesiodum.scholia-in-opera-et-dies-scholia-vetera |  | [archive.org](https://archive.org/details/poetaeminoresgra02gais) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 174,207 | auto-corrected |
| scholia-in-lycophronem.scholia-in-lycophronem-scholia-vetera-et-recentiora-partim-isaac-et |  | [archive.org](https://archive.org/details/lycophronisalexa02lycouoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 107,086 | auto-corrected |
| scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora |  | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 5,989 | auto-corrected |
| scholia-in-oppianum.scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora |  | qwen36-scholia_oppianum_bussemaker_didot-masked | Qwen3.6-27B-FP8 | 64,951 | raw OCR |
| scholia-in-platonem.scholia-in-platonem-scholia-vetera |  | [archive.org](https://archive.org/details/platonisoperaom03wincgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 177,306 | auto-corrected |
| scholia-in-theocritum.scholia-vetera-et-recentiora |  | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 92,305 | auto-corrected |
| scholia-in-xenophontem.scholia-in-anabasin-cyri-scholia-vetera | SCHOLIA IN XENOPHONTEM — Scholia in Xenophontis Anabasin | qwen36-expeditiocyri02xenogoog | Qwen3.6-27B | 4,180 | raw OCR |
| scythinus-poet-phil.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 315 | auto-corrected |
| scythinus-poet-phil.testimonia |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 249 | raw OCR |
| scythinus.peri-physios |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 44 | raw OCR |
| secundus-mullach-fpg1 |  | qwen36-secundus_mullach_fpg1 | Qwen3.6-27B | 151,676 | auto-corrected |
| semonides.fragmenta | SEMONIDES — Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 524 | raw OCR |
| serenus.de-sectione-cylindri |  | qwen36-serenus_heiberg_opuscula | Qwen3.6-27B | 34,300 | auto-corrected |
| simias.fragmenta |  | qwen36-simias_fraenkel | Qwen3.6-27B | 6,875 | auto-corrected |
| simonides-lyric.fragmenta-2 |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,746 | auto-corrected |
| simus-myonides-euphranor.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 104 | raw OCR |
| simylus.fragmentum | SIMYLUS — Fragmentum | kock-caf2-ocr-frag | Qwen3.6-27B | 35 | raw OCR |
| sminthes.titulus |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 34 | auto-corrected |
| socrates-rhodius.socrates-hist-fhg4 |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 51,616 | auto-corrected |
| solon.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 1,898 | auto-corrected |
| sopater-comedy.fragmenta |  | qwen36-sopater_kaibel_cgf | Qwen3.6-27B | 32,585 | auto-corrected |
| sophilus.fragmenta | ΑΝΔΡΟΚΛΗΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 179 | auto-corrected |
| sophron.fragmenta | SOPHRON — Fragmenta | qwen36-sopater_kaibel_cgf | Qwen3.6-27B | 5,476 | auto-corrected |
| sosicrates.fragmenta | SOSICRATES — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 80 | auto-corrected |
| sosipater.fragmentum | SOSIPATER — Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 270 | raw OCR |
| sosiphanes.fragmenta |  | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 366 | raw OCR |
| sositheus.fragmenta | ΔΑΦΝΙΣ Η ΑΙΤΤΕΡΣΗΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 447 | raw OCR |
| sosthenes.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 105 | auto-corrected |
| sosylus-bilabel-papyrus1922 |  | qwen36-sosylus_bilabel_papyrus1922 | Qwen3.6-27B | 4,133 | auto-corrected |
| sotades-comedy.fragmenta | ΑΔΗΛΩΝ ΔΡΑΜΑΤΩΝ | kock-caf2-ocr-frag | Qwen3.6-27B | 53 | raw OCR |
| sotion.leipsana |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 287 | auto-corrected |
| sphaerus.fragmenta |  | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 558 | auto-corrected |
| stephanus-grammar.ethnica-epitome |  | [archive.org](https://archive.org/details/bub_gb_0NIPAAAAQAAJ) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 144,357 | auto-corrected |
| stephanus.fragmentum | STEPHANUS — Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 99 | raw OCR |
| straton-philosophy.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 297 | raw OCR |
| strattis.fragmenta | ἈΡΓΥΡΙΟΤ ἈΦΑΝΙΣΜΟΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 2,271 | auto-corrected |
| susarion.fragmentum | ΣΟΤΣΑΡΙΩΝ | kock-caf1-ocr-frag | Qwen3.6-27B | 31 | raw OCR |
| symmachus.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 39,309 | auto-corrected |
| synesius-philosophy.epistulae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 32,687 | auto-corrected |
| teleclides.fragmenta | ΤΗΛΕΚΛΕΙΔΗΣ | kock-caf1-ocr-frag | Qwen3.6-27B | 1,311 | raw OCR |
| telephus.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 136 | raw OCR |
| telesilla.fragmenta |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,203 | auto-corrected |
| telestes.fragmenta | TELESTES — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 215 | auto-corrected |
| terpander.fragmenta-fort-auctore-terpandro |  | bergk-plg3-ocr-frag | Qwen3.6-27B | 45 | raw OCR |
| thales.fragmenta |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 3,997 | auto-corrected |
| thales.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 7,246 | auto-corrected |
| theagenes-philosophy.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 231 | raw OCR |
| theages.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,205 | auto-corrected |
| theano.fragmenta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 587 | auto-corrected |
| themison.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 2 | raw OCR |
| themistius.peri-filanqrwpi-as-h-kwnsta-ntios | THEMISTIUS — Orationes | qwen36-themistiioratio01dindgoog | Qwen3.6-27B | 157,489 | raw OCR |
| theodectas.fragmenta | ΑΑΚΜΕΩΝ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 1,045 | auto-corrected |
| theodoretus.commentaria-in-isaiam | ΤΟΥ ΜΑΚΑΡΙΟΥ ΘΕΟΔΩΡΗΤΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 44,599 | auto-corrected |
| theodoretus.de-providentia-orationes-decem | ΤΟΥ ΜΑΚΑΡΙΟΥ ΘΕΟΔΩΡΗΤΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 46,435 | auto-corrected |
| theodoretus.epistulae-collectio-sirmondiana-epistulae-1-95 | ΘΕΟΔΩΡΗΤΟΥ ἘΠΙΣΚΟΠΟΥ ΚΥΡΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 53,550 | auto-corrected |
| theodoretus.eranistes | ΕΡΑΝΙΣΤΗΣ ΗΤΟΙ ΠΟΛΥΜΟΡΦΟΣ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 52,370 | auto-corrected |
| theodoretus.explanatio-in-canticum-canticorum | ΕΡΜΗΝΕΙΑ ΕΙΣ ΤΟ ΑΣΜΑ ΤΩΝ ΑΣΜΑΤΩΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 32,440 | auto-corrected |
| theodoretus.graecarum-affectionum-curatio | ΘΕΟΔΩΡΗΤΟΥ ΕΠΙΣΚΟΠΟΥ ΚΥΡΟΥ ΕΛΛΗΝΙΚΩΝ ΠΑΘΗΜΑΤΩΝ ΘΕΡΑΠΕΥΤΙΚΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 70,039 | auto-corrected |
| theodoretus.haereticarum-fabularum-compendium | ΑΙΡΕΤΙΚΗΣ ΚΑΚΟΜΟΥΣΙΑΣ ΕΠΙΤΟΜΗ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 36,615 | auto-corrected |
| theodoretus.interpretatio-in-ezechielem | ΕΡΜΗΝΕΙΑ ΤΗΣ ΠΡΟΦΗΤΕΙΑΣ ΤΟΥ ΘΕΙΟΥ ΕΖΕΚΙΗΛ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 132,642 | auto-corrected |
| theodoretus.interpretatio-in-jeremiam | ΕΡΜΗΝΕΙΑ ΤΗΣ ΠΡΟΦΗΤΕΙΑΣ ΤΟΥ ΘΕΙΟΥ ΙΕΡΕΜΙΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 47,018 | auto-corrected |
| theodoretus.interpretatio-in-psalmos | ἘΡΜΗΝ. ΤΟΥ Βʹ ΨΑΛΜΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178,454 | auto-corrected |
| theodoretus.interpretatio-in-xii-prophetas-minores | ΥΠΟΜΝΗΜΑ ΕΙΣ ΤΟΥΣ ΔΩΔΕΚΑ ΠΡΟΦΗΤΑΣ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 74,605 | auto-corrected |
| theodoretus.interpretatio-in-xiv-epistulas-sancti-pauli | ΤΟΥ ΑΓΙΟΥ ΑΠΟΣΤΟΛΟΥ ΠΑΥΛΟΥ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 146,935 | auto-corrected |
| theodoretus.libellus-contra-nestorium-ad-sporacium-sp | ΕΠΙΣΚΟΠΟΥ ΚΥΡΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,433 | auto-corrected |
| theodoretus.quaestiones-in-libros-regnorum-et-paralipomenon | ΤΟΥ ΜΑΚΑΡΙΟΥ ΘΕΟΔΩΡΗΤΟΥ | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 58,179 | auto-corrected |
| theodoretus.quaestiones-in-octateuchum | ΤΟΥ ΜΑΚΑΡΙΟΥ ΘΕΟΔΩΡΗΤΟΥ, ΕΠΙΣΚΟΠΟΥ ΚΥΡΟΥ, ΤΑ ΑΠΟΡΑ ΤΗΣ ΘΕΙΑΣ ΓΡΑΦΗΣ. ΚΑΤ' ΕΚΛΟΓΗΝ. | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 66,557 | auto-corrected |
| theodorus-mathematics.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 351 | raw OCR |
| theodosius.canones-isagogici-de-flexione-nominum |  | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 14,109 | auto-corrected |
| theodosius.canones-isagogici-de-flexione-verborum |  | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 16,797 | auto-corrected |
| theodotion.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 23,151 | auto-corrected |
| theognetus.fragmenta | THEOGNETUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 135 | raw OCR |
| theognis-elegy.elegiae |  | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 3,233 | auto-corrected |
| theognis-history.fragmentum |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 239 | auto-corrected |
| theognis-tragedy.fragmentum |  | qwen36-nauck_tgf_1889 | Qwen3.6-27B | 113,096 | auto-corrected |
| theognostus.canones-sive-de-orthographia |  | [archive.org](https://archive.org/details/anecdotagrcaeco00fragoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 150,388 | auto-corrected |
| theophilus-comedy.fragmenta | ΘΕΟΦΙΛΟΥ ΒΟΙΩΤΙΣ | kock-caf2-ocr-frag | Qwen3.6-27B | 413 | raw OCR |
| theophylactus-simocatta.epistulae |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,554 | auto-corrected |
| theopompus-comedy.fragmenta | ἈΦΡΟΔΙΣΙΑ | kock-caf1-ocr-frag | Qwen3.6-27B | 1,876 | auto-corrected |
| theopompus-history.testimonia |  | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 23,292 | auto-corrected |
| thespis.fragmenta | ΠΕΝΘΕΤΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 262 | raw OCR |
| thrasymachus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,086 | auto-corrected |
| thugenides.fragmenta | THUGENIDES — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 144 | raw OCR |
| timaeus-philosophy.fragmenta-et-titulus-sp |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,691 | auto-corrected |
| timaeus-philosophy.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 134 | raw OCR |
| timaeus-sophista.lexicon-platonicum |  | [archive.org](https://archive.org/details/timaiousophistou00tima) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 33,929 | auto-corrected |
| timagenes.fragmenta |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 399 | auto-corrected |
| timagoras.fragmenta |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 318 | auto-corrected |
| timocles-comedy.fragmenta | ΑΙΓΤΙΠΙΟΙ | kock-caf2-ocr-frag | Qwen3.6-27B | 1,579 | raw OCR |
| timocreon.fragmenta | TIMOCREON — Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 261 | auto-corrected |
| timon.fragmenta-et-tituli |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 7,666 | auto-corrected |
| timosthenes-ggm1 |  | qwen36-timosthenes_ggm1 | Qwen3.6-27B | 104,454 | auto-corrected |
| timostratus.fragmenta | TIMOSTRATUS — Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 177 | raw OCR |
| timotheus-comedy.fragmenta | ΜΕΤΑΒΑΛΛΟΜΕΝΟΣ Η ΜΕΤΑΦΕΡΟΜΕΝΟΣ ΠΤΚΤΗΣ ΠΑΡΑΚΑΤΑΘΗΚΗ | kock-caf2-ocr-frag | Qwen3.6-27B | 80 | raw OCR |
| timotheus-grammar.timotheus-gaza-haupt-opuscula |  | qwen36-timotheus_gaza_haupt_opuscula | Qwen3.6-27B | 16,630 | auto-corrected |
| timotheus-history.timotheus-defluviis-ggm2 |  | qwen36-timotheus_defluviis_ggm2 | Qwen3.6-27B | 181,577 | auto-corrected |
| timotheus-lyric.fragmenta |  | qwen36-timotheus_perser_wilamowitz | Qwen3.6-27B | 5,050 | auto-corrected |
| titanomachia.titanomachia-fragmenta |  | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 452 | auto-corrected |
| tlg0129.fragmenta |  | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 2,186 | auto-corrected |
| tlg1140.tlg001 | ANTICLIDES — Fragmenta | qwen36-anticlides-bub | Qwen3.6-27B | 2,785 | raw OCR |
| tlg1235.fragmenta |  | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 98 | raw OCR |
| tlg1595.tlg003 | Stoicorum Historia / Index Stoicorum (P.Herc. 1018) | [Philodemus, Stoicorum Historia (Index Stoicorum), ed. Comparetti, Rivista di Filologia 3, 1875](https://archive.org/details/rivistadifilolog03toriuoft) | Qwen3.6-27B | 1,477 | auto-corrected |
| tlg1595.tlg120 | PHILODEMUS — De morte liber IV | qwen36-sitzungsbericht308klasgoog | Qwen3.6-27B | 5,107 | raw OCR |
| tlg1595.tlg210 | De musica lib. iv | [Philodemus, De musica, ed. Kemke, Teubner 1884](https://archive.org/details/philodemidemusic00phil) | Qwen3.6-27B | 9,652 | auto-corrected |
| tlg1595.tlg241 | De oeconomia | [Philodemus, De oeconomia, ed. Jensen, Teubner 1906](https://archive.org/details/philodemiperioik00phil) | Qwen3.6-27B | 9,431 | auto-corrected |
| tlg1595.tlg267 | De ira (Peri orges) | [Philodemus, De ira (editio princeps), ed. Gomperz 1864](https://archive.org/details/philodemiepicur00philgoog) | Qwen3.6-27B | 7,327 | auto-corrected |
| tlg1595.tlg271 | De libertate dicendi (Peri parrhesias) | [Philodemus, De libertate dicendi, ed. Olivieri, Teubner 1914](https://archive.org/details/philodemiperipar00philuoft) | Qwen3.6-27B | 5,670 | auto-corrected |
| tlg1595.tlg289 | De poematis lib. ii | [Philodemus, De poematis lib. ii, ed. Hausrath](https://archive.org/details/philodemiperipoi00haus) | Qwen3.6-27B | 1,473 | auto-corrected |
| tlg1595.tlg472 | De signis (Peri semeion kai semeioseon) | [Philodemus, De signis (Peri semeioseon), ed. Gomperz, Herkulanische Studien 1, 1865](https://archive.org/details/philodemberindu00gompgoog) | Qwen3.6-27B | 3,238 | auto-corrected |
| tlg1595.tlg492 | De bono rege secundum Homerum | [Philodemus, De bono rege secundum Homerum, ed. Olivieri, Teubner 1909](https://archive.org/details/philodemiperitou00philuoft) | Qwen3.6-27B | 4,723 | auto-corrected |
| tlg1598.fragmenta |  | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 78 | raw OCR |
| tlg2524.fragmenta |  | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 162 | auto-corrected |
| tlg2637.fragmenta |  | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 578 | auto-corrected |
| tlg4049.tlg001 | THOMAS MAGISTER — Ecloga nominum et verborum Atticorum | qwen36-thomaemagistrisi00thomuoft | Qwen3.6-27B | 77,130 | raw OCR |
| tlg4075.tlg001 | MARINUS — Vita Procli | qwen36-marinus-bub | Qwen3.6-27B | 21,475 | raw OCR |
| tragica-adespota.fragmenta | ΦΙΛΟΚΤΗΤΗΣ | nauck-tgf-ocr-frag | Qwen3.6-27B | 11,426 | auto-corrected |
| tyrtaeus.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 953 | auto-corrected |
| ulpianus.prolegomena-in-demosthenis-orationes-olynthiacas-et-philippicas |  | qwen36-scholia_demosthenem_dindorf_v8-ocr | Qwen3.6-27B | 5,209 | auto-corrected |
| xenarchus.fragmenta | ΒΟΥΤΑΛΙΩΝ | kock-caf2-ocr-frag | Qwen3.6-27B | 404 | raw OCR |
| xeniades.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 42 | auto-corrected |
| xenocles.fragmentum | ΛΙΚΥΜΝΙΟΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 143 | raw OCR |
| xenomedes.fragmenta |  | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 840 | auto-corrected |
| xenophanes.fragmenta |  | bergk-plg2-ocr-frag | Qwen3.6-27B | 491 | raw OCR |
| xenophanes.fragmenta-silli-et-de-natura |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 6,875 | auto-corrected |
| xenophanes.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 11,552 | auto-corrected |
| xenophilus.testimonia |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 110 | raw OCR |
| xuthus.testimonium |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 140 | raw OCR |
| zeno-citieus.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,958 | auto-corrected |
| zeno-philosophy.testimonia |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,738 | auto-corrected |
| zeno-tarsensis.fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 153 | raw OCR |
| zonaeus-walz-rg8 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 153,758 | auto-corrected |
| zosimus-alchemista.opera |  | qwen36-berthelot_alchimistes_grec-ocr | Qwen3.6-27B | 40,753 | auto-corrected |
<!-- OCR-PROVENANCE:END -->

## Status

- ~3,660 works ingested, ~67M Greek tokens, twelve sources.
- ~66% of the TLG inventory's words actually ingested (49.5M of 75M;
  `data/coverage_report.json` has the per-bucket breakdown).
- Per-lemma frequency is built from the whole corpus. Counts are facts, not
  copyrightable; use them freely.
- The byzantium.gr works now carry real citation loci read from each page's
  own markers (book/chapter, Psellos book.section, Theophanes annus mundi,
  Skylitzes reign.chapter, ...); only Attaliates, whose page prints no
  structure, keeps page-paragraph indices.
- Next: per-work loci for the multi-work CGPG Migne volumes (work-to-column
  mappings researched for all 18 volumes in data/pd_research/, carve pending).

## License

Aggregated open editions: CC BY-SA 4.0, with attribution to First1KGreek
(OpenGreekAndLatin) and Perseus; per-work source in `coverage.json`. Our OCR of
public-domain editions: CC BY 4.0. Derived tables (frequency, coverage) are
facts and carry no additional copyright. See `LICENSE`.
