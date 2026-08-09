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
| [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | CC BY 4.0 | patristic gap: CC-BY OCR of public-domain Migne (`cgpg`); 21 multi-work volumes are carved into per-work files by `scripts/carve_cgpg_volume.py` (plan: `data/cgpg_carve_plan.json`), and 12 `cogPG.*` files still serve volume-keyed |
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
  measure_capital_positions.py  data/corpus -> data/capital_positions.json, which
                            capitalized lemmas are only a sentence opening
                            (Πῶς, 9.1% mid-sentence) and which are the word
                            itself (Θεός, 97.8%). validate_lemma_map.py folds
                            the first kind into its lowercase twin
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
  carve_edition_volume.py   split a printed volume served as one dump into its
                            per-treatise files, per data/walz_carve_plan.json or
                            another via --plan (data/spengel_carve_plan.json).
                            Works carry a START locus and no end, so the
                            partition is exact and a gap is not expressible;
                            loci key to the printed page; duplicate scanned
                            leaves are dropped and archived; a treatise already
                            served from a better edition is written to
                            corpus_secondary as a witness instead
  carve_cgpg_volume.py      split a multi-work CGPG Migne volume dump into
                            per-work corpus files per data/cgpg_carve_plan.json
                            (incipit-verified row ranges, token-exact, reversible
                            corpus_changes audit; secondary rank for works served
                            from a better source)
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
  issue-policy.md           what the issue tracker holds: every known defect in
                            the published data and every outstanding piece of
                            work, with the labels and the close criterion
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
  cgpg_works.json           CGPG Migne volume -> TLG works it covers, plus one
                            kind="work" unit per carved per-work file
  cgpg_carve_plan.json      curated carve plan for the multi-work CGPG volumes
                            (slugs, row ranges, shared-row assignments, incipit
                            anchors, duplicate-scan drops, secondary ranks)
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

A served work can also carry a `serving_deficit` block in `work_index.json`
(and a `serving_deficit` column in the catalog): the served text is known to be
shorter than a fuller text of the same work held in this repo, and the serving
is meant to eventually grow into it. The curated decisions live in
`data/serving_deficits.json`; every number is derived at build time from the
named files, and the build fails if an entry's slug is not served, its fuller
text is missing, or the fuller text is no longer larger, so a resolved deficit
must be cleared in the same change that resolves it. The file is empty as of
2026-08-08: its first entry, on De cerimoniis, turned out to rest on a misread
of the TLG Canon and was removed the next day, which is recorded in the file.

A work the TLG never numbered gets a CTS id in this repo's own namespace,
`urn:cts:cogGreek:<key>`, not in Perseus/OGL's `greekLit`. 3,880 of the 11,074
CTS aliases are cog-native that way, and `data/crosswalk_report.json` splits the
count by namespace so "100% cts" is not read as 100% externally identified.
Until 2026-08-08 those ids claimed `greekLit` and 29 of them were published as
work anchors, along with a `tlg` field holding the corpus key itself; both
resolved nowhere (issue #32).

External identifiers (TLG/CTS, Wikidata QID, VIAF/GND/ISNI, Trismegistos) are
kept as crosswalk aliases at their FRBR level, so nothing is anchored to the
proprietary TLG Canon: the bare TLG author.work number is a Work-level anchor
(the only external id with ~100% work coverage), and the opaque `ogc` id sits
one level finer at the Expression, so the 4 TLG variant-edition pairs are two
distinct `ogc` ids sharing one TLG anchor. 488 of the 3,822 served works have no
external id at all (the exceed-TLG material) and rely on the `ogc` id alone. The
TLG/CTS crosswalk lives in `data/tlg_crosswalk.tsv` and, per work, in
`work_index.json` under `work_anchors` (`cts` on 3,334 works, `tlg` on 3,322,
`wikidata` on 503), so joins against citation and lexicon data still work.
`corpus_editions.json` is not where to look for it: that file is derived from
`data/corpus` on every build and carries only the manifestation (edition,
source, license, counts) plus the `ogc` `id`. `build_crosswalk_report.py`
reports how complete the crosswalk is and where enrichment is cheapest (e.g.
the author has a Wikidata QID but the work doesn't). Why TLG numbers are kept as aliases rather
than dropped: `docs/identity-and-citation.md`.

Canon titles stored in beta-code (`*AI)GU/PTIOS`) are decoded to Unicode at
registry build (`Αἰγύπτιος`), including Greek glosses inside Latin titles
(`De Figuris (Περὶ σχημάτων)`). Slugs stay ASCII. Needs the `betacode` library
(see Build).

CGPG text arrived keyed by Migne volume (`cogPG.<vol>`, several works per
volume). The multi-work volumes are now carved into per-work slug files by
`scripts/carve_cgpg_volume.py`, driven by the curated
`data/cgpg_carve_plan.json` (work-to-row ranges with incipit anchors, from the
`data/pd_research/` column mappings); a carved row keeps its Migne page
identity as locus `<VOL>.<page>` (`PG157.225`), the Cedrenus-split convention.
A work already served from a better source per the precedence ladder is carved
to `data/corpus_secondary/` as a witness instead of competing. Each carve
leaves a reversible audit in `data/corpus_changes/cogPG.<VOL>.per-work-split.json`
(token-exact partition, dropped rescan leaves archived verbatim), and
`cgpg_works.json` credits the per-work units. A volume can be carved more than
once: `--pass N` runs over what the previous pass left, so a block whose
attribution firms up later is not stranded by the first carve having already
run. Each pass writes its own audit (`.pass2.json` and so on), because writing
one over another would destroy the earlier carve's reconstruction record while
appearing to succeed. 22 volumes have been carved so
far, and 11 `cogPG.*` files are still volume-keyed, holding 250,174 Greek
tokens. PG151 was finished on 2026-08-08 and its file is gone: its last two
works, Gregory Palamas' Homologia and the confined archbishops' report to Anna
Palaiologina, had every seam inside a row, and `scripts/split_carved_row.py`
cuts a row at a character offset. Ten of the eleven remaining files are carved
volumes' leftovers, 89,914 tokens between them, and 75,862 of that is PG112's
uncarved half alone (the Vogt text byzantium.gr already serves, left
volume-keyed pending a disposition). The rest is small: PG005, PG101, PG107,
PG109, PG118, PG124 and PG125 hold 2 to 13 rows each, every one identified in
its plan entry's residual note, and the largest are Greek apparatus rather than
the Latin monita an earlier summary called them, the Ignatius testimonia in
PG005 and the Oecumenius prefatory matter in PG118. PG113 keeps 3,039 after its Theophylact block was
carved on 2026-08-08, and PG139 a 1,349-token table of contents. Only one whole volume remains uncarved, PG003
at 160,260 tokens. They are listed with their token counts
in the OCR provenance table below. Of those two, PG003 is uncarved on the
evidence, and the reason recorded for it has been corrected twice, in opposite
directions. It originally said the Dionysius text interleaves passage-by-passage
with Pachymeres' paraphrase and that no display titles survive in the OCR. The
second half was wrong: 26 heads do survive, unfindable by a Greek search because
the OCR read Migne's Latin as Greek letter shapes, so PARAPHRASIS PACHYMERAE sits
at locus 151 as `ΡΑΗΑΡΗΚΑΘ ΡΑΩΙΥΜΕΛ`. That discovery then produced a second wrong
reason, recorded here until 2026-08-07: that the interleave was block scale and an
ordinary locus carve could express it. It came from a detector that read only the
first four words of each row, so it could not have found a mid-row head if one
existed, and reporting that the heads it found all opened rows was circular.
Scanning whole rows, 15 of the 26 heads fall mid-row, including an author switch
at locus 481, character 1,713 of a 2,018-character row. So the original reason
stands: the boundaries fall inside rows, `carve_cgpg_volume.py` moves whole rows,
and a carve on loci would cut mid-block. On top of that the OCR dropped most of
the heads, which needs the PG 3 page images
(`scripts/measure_pg003_blocks.py`, `data/pg003_blocks.json`,
`data/corpus_changes/cogPG.PG003.split-deferred.json`). Its attribution has
been corrected in the meantime: Dionysius holds about 37% of the volume's
160,260 tokens against the paraphrase's 63%, so it carries a collective author
label and NO century, the two being some 700 years apart. A consumer filtering
PG003 by period will no longer see it, which is deliberate: the previous tag
dated roughly 100,000 tokens of 13th-century paraphrase to the 6th. The other five are not
in the plan at all, which covers 18 volumes; the column research for them has
not been done. byzantium.gr historians are single works and key by their slug
directly.

Passage citations follow CTS-URN logical-locus semantics (`source_identity.py`,
`parse_ref`): dot-separated levels (`book.chapter.line`), ranges with matching
depth on both ends (`5.84-5.116`, never `5.84-116`). `Locus` validates the
grammar on construction; `locus_for_citation(..., validate=True)` also checks
depth against the edition's declared citation scheme. Every served in-registry
work carries a servable `default_edition`: when no open TEI edition exists,
`build_registry.py` mints one straight from the work's `corpus_editions.json`
record (DFHG, OCR, CGPG, PTA, byzantium.gr, GLAUx, SAWS, Wikisource), with the
citation scheme inferred from the served loci when they are clean logical
numerics (marked `scheme_inferred`). The crosswalk report's
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
make reports               # quality report, per-work lemma counts, this README's
                           # provenance table (see the Makefile header: this goal
                           # re-runs the ingest chain when it is stale, and that
                           # chain can go to the network)
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

### How good are the corrections?

Measured by blind philological rating of stratified samples of the corrections
actually present in the served text (first pass 2026-08-02, largest cell
remeasured at n=295 on 2026-08-03). By corrector: `confusion` 93%, `freq`/auto
85%, `freq`/accepted 80% (95% CI 74-87), `llm`/auto 78%. Weighted overall,
roughly 40,000 of the corrections are wrong; the `freq`/accepted term of that is
measured to ~13,000 (range 9,000-17,600) and the other cells still rest on their
original n≈30 samples.

The measurement's own noise floor is known: independent raters shown identical
items disagree on 8.6% of them (kappa 0.78), so no figure here is finer than a
few points. That floor cannot explain away the one revert taken on these
numbers: for `llm`/accepted's 10-of-30 to have come from an acceptable cell,
rater error would have to be several times what was measured (P < 1e-4 at every
plausible rate).

The worst cell, `llm`/accepted, measured 33% and has been reverted to its OCR
readings and requeued. A full-population check found 48% of it produced strings
unattested in 1.17M clean Greek forms. The 2,496 of its fixes that turned an
unattested string into an attested one were restored, since that is positive
evidence; the rest await re-adjudication behind a lexicon gate.

`prosodia`/accepted looked like a second such cell at 43% unattested, but it is
not: that pass normalizes sigma (medial to `σ`, final to `ς`, lunate to either),
which is correct Greek orthography whatever else is wrong with the token, so
applying it to an already-broken word leaves the word broken and unattested
without making it worse. None of its corrections made a token rarer.

`freq`/accepted remains the largest single block of damage (~13,000 wrong rows)
purely by size. A ten-stratum analysis found no slice of it bad enough to revert
wholesale and no factor (edit kind, target rarity, genre) that gates it, so what
remains needs per-record judgment or nothing.

The overlay is also kept honest about its own reach. 35,008 corrections marked
active could no longer apply at all - the July 2026 re-OCR or a later carve had
replaced or dropped the text they targeted - and were retired on proof (text
absent AND a redo dir or an audit accounting for the removal); everything a
`data/corpus_changes/` audit can still place is re-keyed through that audit's
own map rather than retired. What remains claims only what the text carries:
of 192,151 records still marked active, 120,894 are verifiably present, spread
over 890 works. Of the rest, three are simply not in the text and the other
71,254 are all one thing, a carve orphan: every one is keyed to a `cogPG.<vol>`
volume that no longer holds the row, because the per-work carve moved it. An
earlier count split them in two, 41,873 whose file was gone and 29,381 whose
locus was gone, as though those were different failures. They are not. The only
difference is whether the carve left a residual file behind: the ten volumes
carved to nothing (PG006, PG087_1, PG122, PG123, PG126, PG134, PG146, PG155,
PG157, PG158) have no file for a record to miss, while the seven that kept 2 to
20 unclaimed rows (PG005, PG101, PG107, PG109, PG118, PG124, PG125) still have a
file, so the same orphan reports a missing locus instead.

Being an orphan is not being lost. Replaying the loci through the carve audits
in `data/corpus_changes/` places 68,744 of the 71,254 on exactly one surviving
row, across 176 carved works; the remaining 2,510 are all PG122 rows that the
earlier Cedrenus split had already moved, and that split's own audit places
every one of them. So the whole block is recoverable, and none of it has been
re-keyed or counted above.

That is a smaller number of works than the provenance table's 985 (155 manually
corrected, 830 auto), and the gap is real rather than a discrepancy: the table
counts what each row's own `corrections` stamp says, so it also sees works edited
by passes that never went through this overlay.

Corrections keep the edition's own capitalization. An upstream corrector used to
resolve a capitalized token to the frequent lowercase form and so lowercase the
capital the edition prints - after a full stop, at the head of a lexicon's lemma
register, on a divine name - with no evidence behind the case change at all. That is
now blocked at the source, where each edition's convention is measured from its own
rows and from its own usage of the word. Two passes put the capitals back: 6,423 rows
across 178 works on 2026-08-01, and a further 1,183 rows across 65 works on 2026-08-02
once the per-word evidence was added (`Θεοῦ`, `Ἐκκλησίας`, `Υἱοῦ`, `Γραφαῖς`). 18,242
correction records retired, 4,945 replaced with the case-preserving fix; audits
upstream in `data/corrections/recase_2026-08-0{1,2}.json`, and
`data/corrections_log/applied.jsonl` reflects the result.

A third pass on 2026-08-02 restored the referential capitals - `Θεοῦ`, `Θεόν`,
`Θεός` and the like - from a hand-curated, adversarially audited list of 80 forms
these editions capitalize for their referent rather than their position.

Roughly 7,700 lowercasings remain unresolved, and are flagged upstream rather than
silently blessed. They fall in classes the evidence genuinely cannot reach: verse
lines in blocks the edition sets line by line (the corpus rows carry no newlines, so
the structure is gone), dash-introduced rubrics, and words whose case tracks their
sense - `υἱός` the Son against a man's son, `ἥλιος` the god against the sun - where
a blanket rule would corrupt the majority of occurrences.

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

`scripts/refile_aeneas_tacticus_witness.py` (2026-08-01) re-filed the
996-row Aeneas Tacticus OCR (Poliorcetica ed. Hug, Teubner 1874, scan
aeneaecommentar01huggoog) that had sat mis-ingest-marked in corpus_secondary
under aeneas-philosophy.theophrastus-...: it is a real witness of the served
perseus-grc2 `aeneas-tactics.poliorcetica` (bigram containment of the served
text in the OCR 0.76, asserted by the script), so it now lives at
`data/corpus_secondary/aeneas-tactics.poliorcetica.jsonl`, with the
delivery-side `migne-ocr-qwen36` edition mislabel corrected to the actual
scan. `scripts/drop_satyrus_lembus_misingest.py` (same date) removed the 47
wrong-work rows (Heraclides Lembus, Excerpta Politiarum + Posidonius,
fhg_vol3 pp. 177-196) from the `satyrus.vita-euripidis-p-oxy-9-1176`
secondary, keeping its 89 true witness rows. Both are audited and reversible
in `data/corpus_changes/` (verbatim pre-change files archived).

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
1393 OCR'd works/volumes: 191 manually corrected, 867 auto-corrected (deterministic glyph-confusion / frequency passes; edited but not hand-reviewed), 335 still raw OCR. Works are named by their author.work slug; the TLG/CTS mapping is in `data/tlg_crosswalk.tsv`.

| Work (slug) | Content | Downloaded | OCR model | Words | Correction |
|---|---|---|---|--:|---|
| achaeus.fragmenta | Achaeus - Fragmenta | nauck-tgf-ocr-frag | Qwen3.6-27B | 1,396 | raw OCR |
| acta-justini-et-septem-sodalium.acta-justini-et-septem-sodalium-recensio-b | Acta Justini et septem sodalium - Martyrium SS. Justini, Charitonis, Charitus, Euelpisti, Hieracis, Paeonis et Liberiani (recensio B proxima) (PG006 loci 790-792) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 653 | auto-corrected |
| acusilaus.testimonia-2 | Acusilaus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 456 | auto-corrected |
| adrianus-rhetor.meletai |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 1,501 | auto-corrected |
| aelius-dionysius.attika-o-no-mata | Aelius Dionysius - Ἀττικὰ ὀνόματα | qwen36-aelius_dionysius_schwabe-ocr | Qwen3.6-27B | 32,229 | auto-corrected |
| aeneas-philosophy.epistulae | Aeneas - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,870 | auto-corrected |
| aeneas-philosophy.theophrastus-sive-de-animarum-immortalitate-et-corporum-resurrectione | AENEAS GAZAEUS - Theophrastus sive de animarum immortalitate | qwen36-aeneasgazaeuset00zachgoog | Qwen3.6-27B | 24,881 | raw OCR |
| aeschines-socraticus.fragmenta | Aeschines Socraticus - Fragmenta | qwen36-aeschines_socr_dialogi_clericus | Qwen3.6-27B | 14,099 | auto-corrected |
| aeschylus-tragedy.fragmenta | Aeschylus - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 16,985 | auto-corrected |
| agaclytus.fragmentum | Agaclytus - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 147 | raw OCR |
| agathon-tragedy.fragmenta | Agathon - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 897 | auto-corrected |
| alcaeus-comedy.fragmenta | Alcaeus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 587 | raw OCR |
| alcaeus-lyric.fragmenta | Alcaeus - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,308 | auto-corrected |
| alcmaeon.fragmenta | Alcmaeon - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 190 | raw OCR |
| alcmaeon.testimonia | Alcmaeon - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,345 | auto-corrected |
| alcman.fragmenta | Alcman - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,854 | auto-corrected |
| alexander-lyric.fragmenta | Alexander - Fragmenta | qwen36-alexander_aetolus_meineke | Qwen3.6-27B | 21,656 | auto-corrected |
| alexander-medicine.dedicatio-ad-cosman | Alexander - Dedicatio Ad Cosman | qwen36-alex_trall_puschmann | Qwen3.6-27B | 43,309 | auto-corrected |
| alexander-rhetoric.ek-ton-alexandrou |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,345 | raw OCR |
| alexander.fragmenta | ALEXANDER - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 225 | auto-corrected |
| alexis-comedy.fragmenta | Alexis - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 10,197 | auto-corrected |
| ameinias.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 80 | raw OCR |
| amipsias.fragmenta | Amipsias - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 766 | raw OCR |
| amphis.fragmenta | Amphis - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 1,086 | auto-corrected |
| anacreon.fragmenta-2 | Anacreon - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 4,215 | auto-corrected |
| anacreontea.anacreontea | Anacreontea - Anacreontea | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,647 | auto-corrected |
| ananius.fragmenta | ANANIUS - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 78 | raw OCR |
| anaphora-archiereon-ad-annam-palaeologinam.anaphora-archiereon | Archiereis Constantinopolitani - Anaphora archiereorum ad Annam Palaeologinam (PG151 loci 391-394, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,844 | manual |
| anaxagoras.testimonia | Anaxagoras - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,079 | auto-corrected |
| anaxandrides.fragmenta | Anaxandrides - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 2,581 | auto-corrected |
| anaxarchus.testimonia | Anaxarchus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,944 | auto-corrected |
| anaxilas.fragmenta | Anaxilas - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 1,084 | auto-corrected |
| anaximander.testimonia | Anaximander - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,482 | auto-corrected |
| anaximenes-philosophy.testimonia | Anaximenes - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,812 | auto-corrected |
| anaximenis-milesii-epistulae.epistulae | Anaximenis Milesii Epistulae - Epistulae | qwen36-aristaenetus_hercher_epistolographi-ocr | Qwen3.6-27B | 164 | raw OCR |
| anaxippus.fragmenta | ANAXIPPUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 613 | raw OCR |
| andreas.fragmentum | Andreas - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 681 | auto-corrected |
| andronicus-rhodius.de-passionibus-lib-1-sp | Andronicus Rhodius - De Passionibus (Lib. 1) [Sp.] | qwen36-andronicus_mullach_fpg3 | Qwen3.6-27B | 215,269 | manual |
| androtion.fragmenta | Fragmenta | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 119 | raw OCR |
| anonymi-de-essentia-et-operatione-dei.de-essentia-et-operatione-dei | Anonymi - De essentia et operatione Dei (PG151 loci 603-628) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,989 | manual |
| anonymi-delectus-legum.delectus-legum-compendiarius | Anonymi - Delectus legum compendiarius (PG113 loci 238-283) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 17,645 | manual |
| anonymi-in-aphthonium.peri-ton-tou-aphthoniou-progymnasmaton |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 2,113 | auto-corrected |
| anonymi-in-aphthonium.prolegomena-kai-scholia-eis-ta-progymnasmata |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,225 | manual |
| anonymi-in-aphthonium.scholia-eis-ta-progymnasmata-walz-ii-565 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,757 | manual |
| anonymi-in-artem-rhetoricam.eisagoge-scholion-eis-ta-prolegomena-tes-hermogenous-rhetorikes |  | qwen36-walz_rhetores_v4 | Qwen3.6-27B | 9,242 | auto-corrected |
| anonymi-in-artem-rhetoricam.ektheseis-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,663 | manual |
| anonymi-in-artem-rhetoricam.epitome-rhetorikes-walz-iii-610 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 858 | auto-corrected |
| anonymi-in-artem-rhetoricam.epitome-rhetorikes-walz-iii-615 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,154 | auto-corrected |
| anonymi-in-artem-rhetoricam.excerpta-de-arte-rhetorica |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 348 | auto-corrected |
| anonymi-in-artem-rhetoricam.peri-poietikon-tropon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,048 | manual |
| anonymi-in-artem-rhetoricam.peri-schematon-hon-hermogenes-emnemoneusen |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,276 | auto-corrected |
| anonymi-in-artem-rhetoricam.peri-schematon-walz-viii-694 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 704 | manual |
| anonymi-in-artem-rhetoricam.peri-synekdoches |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 141 | raw OCR |
| anonymi-in-artem-rhetoricam.peri-ton-okto-meron-tou-rhetorikou-logou |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,046 | manual |
| anonymi-in-artem-rhetoricam.peri-ton-schematon-tou-logou-walz-viii-698 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,789 | auto-corrected |
| anonymi-in-artem-rhetoricam.peri-ton-tessaron-meron-tou-teleiou-logou |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,263 | manual |
| anonymi-in-artem-rhetoricam.peri-ton-tou-logou-schematon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,384 | manual |
| anonymi-in-artem-rhetoricam.peri-tropon-walz-viii-779 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 412 | raw OCR |
| anonymi-in-artem-rhetoricam.problemata-rhetorika-eis-staseis |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,152 | manual |
| anonymi-in-artem-rhetoricam.progymnasmata-walz-i-597 |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 12,390 | auto-corrected |
| anonymi-in-artem-rhetoricam.prolegomena-eis-ten-rhetoriken-doxopatri |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,669 | auto-corrected |
| anonymi-in-artem-rhetoricam.prolegomena-tes-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,958 | auto-corrected |
| anonymi-in-artem-rhetoricam.prolegomena-tes-rhetorikes-walz-v-606 |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 1,301 | raw OCR |
| anonymi-in-artem-rhetoricam.synopseis-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 699 | auto-corrected |
| anonymi-in-hermogenis-de-ideis.kephalaia-tou-protou-bibliou-ton-ideon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,727 | manual |
| anonymi-in-hermogenis-de-ideis.scholia-walz-vii-863 |  | qwen36-walz_rhetores_v7pt2 | Qwen3.6-27B | 57,803 | auto-corrected |
| anonymi-in-hermogenis-de-inventione.eis-to-peri-eureseos-epistasis-anepigraphos |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,351 | auto-corrected |
| anonymi-in-hermogenis-de-inventione.prolegomena-ton-eureseon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 515 | auto-corrected |
| anonymi-in-hermogenis-de-inventione.scholia-walz-vii-697 |  | qwen36-walz_rhetores_v7pt2 | Qwen3.6-27B | 43,287 | auto-corrected |
| anonymi-in-hermogenis-de-inventione.semeiodes-eis-tas-eureseis |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 595 | raw OCR |
| anonymi-in-hermogenis-de-statibus.hetera-prolegomena-ton-staseon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 600 | auto-corrected |
| anonymi-in-hermogenis-de-statibus.peri-ton-staseon-walz-v-591 |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 1,592 | raw OCR |
| anonymi-in-hermogenis-de-statibus.prolegomena-ton-staseon-walz-i |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,516 | manual |
| anonymi-in-hermogenis-de-statibus.prolegomena-ton-staseon-walz-ii |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,373 | manual |
| anonymi-in-hermogenis-de-statibus.scholia-eis-tas-hermogenous-staseis |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 144,816 | manual |
| anonymi-in-oppiani-opera.in-oppiani-halieutica-exegesis-e-cod-paris-gr-2735 | Anonymi In Oppiani Opera - In Oppiani Halieutica Exegesis (E Cod. Paris. Gr. 2735) | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 430 dpi) | 4,696 | raw OCR |
| anonymi-logoi-duo.logoi-duo | Anonymi - Λόγοι δύο (PG151 loci 577-600) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 20,680 | manual |
| anonymus-de-vita-mohammedis.narratio-de-vita-mohammedis | Anonymus - Narratio de vita Mohammedis (on Muhammad the pseudo-prophet) (PG158 loci 574-575) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,214 | auto-corrected |
| anthemius.dupuy-1777 |  | qwen36-anthemius_dupuy_1777 | Qwen3.6-27B | 2,563 | raw OCR |
| antidotus.fragmenta | Antidotus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 91 | raw OCR |
| antigonus-paradoxography.historiarum-mirabilium-collectio | Antigonus - Historiarum Mirabilium Collectio | qwen36-antigonus_keller_rnsgm1 | Qwen3.6-27B | 24,737 | auto-corrected |
| antimachus-elegy.fragmenta | Antimachus - Fragmenta | qwen36-antimachus_kinkel_egf1 | Qwen3.6-27B | 29,708 | auto-corrected |
| antiphanes.fragmenta | Antiphanes - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 10,679 | auto-corrected |
| antiphon-soph.testimonia | Antiphon - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,196 | auto-corrected |
| antiphon-tragedy.fragmenta | Antiphon - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 169 | raw OCR |
| antisthenes-atheniensis.testimonia | Antisthenes - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 68 | raw OCR |
| antisthenes.declamationes-fragmenta | Declamationes (fragmenta) | qwen36-archytas_mullach_fpg2-ocr | Qwen3.6-27B | 8,562 | auto-corrected |
| antonius-diogenes.hercher |  | qwen36-antonius_diogenes_hercher | Qwen3.6-27B | 114,457 | auto-corrected |
| aphthonius.progymnasmata | Aphthonius - Progymnasmata | qwen36-aphthonius_progymnasmata | Qwen3.6-27B | 14,810 | auto-corrected |
| apollodorus-cyzicenus.testimonia | Apollodorus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 37 | raw OCR |
| apollodorus-history.fragmenta | Apollodorus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 1,175 | auto-corrected |
| apollodorus-philosophy.fragmenta | Apollodorus - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 712 | auto-corrected |
| apollodorus.fragmenta | APOLLODORUS - Fragmenta | kock-caf3-ocr | Qwen3.6-27B | 252 | raw OCR |
| apollodorus.fragmenta-2 | APOLLODORUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 68 | raw OCR |
| apollonius-philosophy.apollonii-epistulae-dub | Apollonius - Apollonii Epistulae [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,393 | auto-corrected |
| apollonius-philosophy.apotelesmata-sp | Apollonius - Apotelesmata [Sp.] | qwen36-apollonius_parad_keller_v1 | Qwen3.6-27B | 23,053 | auto-corrected |
| apollonius-scr-eccl.fragmenta-ex-libro-adversus-cataphrygas-seu-montanistas | Apollonius - Fragmenta ex libro adversus Cataphrygas seu Montanistas (PG005 loci 700-703) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 557 | auto-corrected |
| apollonius-soph.lexicon-homericum | Apollonius - Lexicon Homericum | [archive.org](https://archive.org/details/apolloniisophis00bekkgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 47,301 | auto-corrected |
| apollophanes-comedy.fragmenta | Apollophanes - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 322 | auto-corrected |
| apollophanes.fragmenta | Fragmenta | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 117 | auto-corrected |
| aquila.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 14,764 | auto-corrected |
| araros.fragmenta | Araros - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 173 | raw OCR |
| arcadius.de-accentibus-sp | Arcadius - De Accentibus [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 47,077 | auto-corrected |
| arcesilaus-comedy.fragmentum | Arcesilaus - Fragmentum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,932 | auto-corrected |
| archedemus.fragmenta | Archedemus - Fragmenta | qwen36-archedemus_svf3 | Qwen3.6-27B | 616 | raw OCR |
| archedicus.fragmenta | ARCHEDICUS - Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 439 | raw OCR |
| archelaus-paradoxography.fragmenta | Archelaus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 101 | raw OCR |
| archelaus-philosophy.testimonia | Archelaus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,603 | auto-corrected |
| archestratus-parodius.fragmenta | Archestratus - Fragmenta | qwen36-archestratus_brandt | Qwen3.6-27B | 16,626 | auto-corrected |
| archilochus.fragmenta | Archilochus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 9,865 | auto-corrected |
| archippus-lysis-opsimus.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 331 | raw OCR |
| archippus.fragmenta | Archippus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 738 | raw OCR |
| archytas-philosophy.testimonia | Archytas - Testimonia | qwen36-anaxagoras_diels_vs1 | Qwen3.6-27B | 6,905 | auto-corrected |
| aresas.fragmentum | Aresas - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 591 | auto-corrected |
| aretades.fragmenta | Aretades - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 178 | raw OCR |
| aristaenetus.epistulae | Aristaenetus - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 201,613 | auto-corrected |
| aristaeus.fragmenta | Aristaeus - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 490 | auto-corrected |
| aristagoras-comedy.fragmenta | Aristagoras - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 102 | raw OCR |
| aristarchus-ludwich |  | qwen36-aristarchus_ludwich | Qwen3.6-27B | 52,926 | auto-corrected |
| aristarchus.fragmenta | Fragmenta | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 246 | raw OCR |
| aristias.fragmenta | Aristias - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 243 | raw OCR |
| aristides-quintilianus-music.de-musica | Aristides Quintilianus - De Musica | qwen36-aristides_quintilianus_meibom | Qwen3.6-27B | 64,826 | auto-corrected |
| aristippus-cyrenaicus.sententiae-et-apophthegmata |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 6,866 | auto-corrected |
| aristobulus.fhg3 |  | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 39,530 | auto-corrected |
| aristocles-messanius.fragmenta | Aristocles - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 684 | auto-corrected |
| aristocles.fragmenta | Fragmenta | qwen36-nicostratus_fhg4 | Qwen3.6-27B | 680 | auto-corrected |
| aristomenes.fragmenta | Aristomenes - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 367 | raw OCR |
| aristonicus-friedlaender |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,713 | auto-corrected |
| aristonymus.fragmenta | Aristonymus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 124 | raw OCR |
| aristophanes-byzantii-nauck |  | qwen36-aristophanes_byzantii_nauck | Qwen3.6-27B | 23,606 | auto-corrected |
| aristophanes-comedy.fragmenta-2 | Aristophanes - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 17,598 | auto-corrected |
| aristophon.fragmenta | Aristophon - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 430 | raw OCR |
| arius-didymus.physica-fragmenta | ARIUS DIDYMUS - Physica (fragmenta, Diels Doxographi) | qwen36-doxographi-arius | Qwen3.6-27B | 7,965 | raw OCR |
| arnim-svf1-1905.paratexta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 95 | raw OCR |
| arnim-svf3-1903.paratexta |  | qwen36-archedemus_svf3 | Qwen3.6-27B | 77 | raw OCR |
| artemon-history.fragmenta | Artemon - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 938 | auto-corrected |
| asclepiades.fragmenta | Fragmenta | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 1,414 | auto-corrected |
| asius.fragmentum-elegiacum | Asius - Fragmentum Elegiacum | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 20 | raw OCR |
| astrampsychus-magus.astrampsychus-oracula-hercher |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,885 | auto-corrected |
| astydamas.fragmenta | Astydamas - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 449 | auto-corrected |
| athanasius-theology.de-corpore-et-anima-sp | Athanasius - De Corpore Et Anima [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 987 | auto-corrected |
| athanasius-theology.de-incarnatione-contra-apollinarium-libri-ii-sp | Athanasius - De Incarnatione Contra Apollinarium Libri Ii [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,352 | auto-corrected |
| athanasius-theology.de-sabbatis-et-circumcisione-sp | Athanasius - De Sabbatis Et Circumcisione [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,600 | raw OCR |
| athanasius-theology.de-sancta-trinitate-dialogi-1-3-5-sp | Athanasius - De Sancta Trinitate (Dialogi 1, 3, 5) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,009 | auto-corrected |
| athanasius-theology.de-sancta-trinitate-dialogi-2-and-4-sp | Athanasius - De Sancta Trinitate (Dialogi 2 And 4) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,560 | auto-corrected |
| athanasius-theology.de-synodis-arimini-in-italia-et-seleuciae-in-isauria | Athanasius - De Synodis Arimini In Italia Et Seleuciae In Isauria | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,193 | auto-corrected |
| athanasius-theology.de-virginitate-sp | Athanasius - De Virginitate [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,095 | auto-corrected |
| athanasius-theology.dialogi-duo-contra-macedonianos-sp | Athanasius - Dialogi Duo Contra Macedonianos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 19,828 | auto-corrected |
| athanasius-theology.disputatio-contra-arium-sp | Athanasius - Disputatio Contra Arium [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,666 | auto-corrected |
| athanasius-theology.doctrina-ad-antiochum-ducem-sp | Athanasius - Doctrina Ad Antiochum Ducem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,628 | auto-corrected |
| athanasius-theology.doctrina-ad-monachos-sp | Athanasius - Doctrina Ad Monachos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,128 | raw OCR |
| athanasius-theology.epistula-ad-adelphium | Athanasius - Epistula Ad Adelphium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,106 | auto-corrected |
| athanasius-theology.epistula-ad-afros-episcopos | Athanasius - Epistula Ad Afros Episcopos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,600 | auto-corrected |
| athanasius-theology.epistula-ad-epictetum | Athanasius - Epistula Ad Epictetum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,204 | raw OCR |
| athanasius-theology.epistula-ad-jovianum | Athanasius - Epistula Ad Jovianum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,935 | raw OCR |
| athanasius-theology.epistula-ad-marcellinum-de-interpretatione-psalmorum | Athanasius - Epistula Ad Marcellinum De Interpretatione Psalmorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,824 | auto-corrected |
| athanasius-theology.epistula-ad-maximum | Athanasius - Epistula Ad Maximum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 959 | auto-corrected |
| athanasius-theology.epistula-ad-monachos-2 | Athanasius - Epistula Ad Monachos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,422 | auto-corrected |
| athanasius-theology.epistula-ad-rufinianum | Athanasius - Epistula Ad Rufinianum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 316 | raw OCR |
| athanasius-theology.epistula-catholica-sp | Athanasius - Epistula Catholica [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 438 | auto-corrected |
| athanasius-theology.epistula-festalis-xxxix-fragmentum-in-collectione-canonum | Epistula festalis xxxix (fragmentum in collectione canonum) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,318 | raw OCR |
| athanasius-theology.epistulae-ad-castorem-sp | Athanasius - Epistulae Ad Castorem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,872 | auto-corrected |
| athanasius-theology.epistulae-festales-ap-cosmam-indicopleustem | Epistulae festales (ap. Cosmam Indicopleustem) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 295 | auto-corrected |
| athanasius-theology.epistulae-quattuor-ad-serapionem | Athanasius - Epistulae Quattuor Ad Serapionem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 22,684 | auto-corrected |
| athanasius-theology.expositiones-in-psalmos | Athanasius - Expositiones In Psalmos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 207,612 | auto-corrected |
| athanasius-theology.fragmenta-varia | Fragmenta varia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,425 | auto-corrected |
| athanasius-theology.homilia-de-passione-et-cruce-domini-additamenta | Athanasius - Homilia De Passione Et Cruce Domini (Additamenta) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 357 | raw OCR |
| athanasius-theology.homilia-de-passione-et-cruce-domini-sp | Athanasius - Homilia De Passione Et Cruce Domini [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,362 | auto-corrected |
| athanasius-theology.homilia-de-semente-sp | Athanasius - Homilia De Semente [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,035 | auto-corrected |
| athanasius-theology.homilia-in-occursum-domini-sp | Athanasius - Homilia In Occursum Domini [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,947 | auto-corrected |
| athanasius-theology.homilia-in-passionem-domini-et-in-parasceve-sp | Athanasius - Homilia In Passionem Domini Et In Parasceve [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,365 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-andream-sp | Athanasius - Homilia In Sanctum Andream [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,038 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-pascha-et-in-recens-illuminatos-sp | Athanasius - Homilia In Sanctum Pascha Et In Recens Illuminatos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,962 | auto-corrected |
| athanasius-theology.homilia-in-sanctum-pascha-sp | Athanasius - Homilia In Sanctum Pascha [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 946 | auto-corrected |
| athanasius-theology.in-caecum-nativitate-sp | Athanasius - In Caecum A Nativitate [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,516 | auto-corrected |
| athanasius-theology.in-illud-profecti-in-pagum-invenietis-pullum-alligatum-sp | Athanasius - In Illud: Profecti In Pagum Invenietis Pullum Alligatum [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,691 | raw OCR |
| athanasius-theology.in-nativitatem-praecursoris-sp | Athanasius - In Nativitatem Praecursoris [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,461 | auto-corrected |
| athanasius-theology.interpretatio-in-symbolum-sp | Athanasius - Interpretatio In Symbolum [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 311 | raw OCR |
| athanasius-theology.liber-de-definitionibus-sp | Athanasius - Liber De Definitionibus [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,144 | auto-corrected |
| athanasius-theology.narratio-de-cruce-seu-imagine-berytensi-sp | Athanasius - Narratio De Cruce Seu Imagine Berytensi [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,980 | raw OCR |
| athanasius-theology.oratio-in-resurrectionem-et-in-recens-baptizatos-sp | Athanasius - Oratio In Resurrectionem Et In Recens Baptizatos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,889 | raw OCR |
| athanasius-theology.orationes-tres-contra-arianos | Athanasius - Orationes Tres Contra Arianos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 74,999 | auto-corrected |
| athanasius-theology.quaestiones-ad-antiochum-ducem-sp | Athanasius - Quaestiones Ad Antiochum Ducem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,459 | auto-corrected |
| athanasius-theology.quaestiones-aliae-sp | Athanasius - Quaestiones Aliae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,322 | auto-corrected |
| athanasius-theology.quaestiones-in-evangelia-sp | Athanasius - Quaestiones In Evangelia [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,493 | auto-corrected |
| athanasius-theology.quaestiones-in-scripturam-sacram-sp | Athanasius - Quaestiones In Scripturam Sacram [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,128 | auto-corrected |
| athanasius-theology.refutatio-hypocriseos-meletii-et-eusebii-sp | Athanasius - Refutatio Hypocriseos Meletii Et Eusebii [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 604 | raw OCR |
| athanasius-theology.scholia-in-acta-fort-ex-libris-contra-novatianos | Scholia in Acta (fort. ex libris Contra Novatianos) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 520 | raw OCR |
| athanasius-theology.sermo-ad-antiochum-ducem-sp | Athanasius - Sermo Ad Antiochum Ducem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,682 | auto-corrected |
| athanasius-theology.sermo-contra-latinos-sp | Athanasius - Sermo Contra Latinos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,853 | auto-corrected |
| athanasius-theology.sermo-contra-omnes-haereses-sp | Athanasius - Sermo Contra Omnes Haereses [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,185 | auto-corrected |
| athanasius-theology.sermo-de-descriptione-deiparae-sp | Athanasius - Sermo De Descriptione Deiparae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,640 | auto-corrected |
| athanasius-theology.sermo-de-patientia-sp | Athanasius - Sermo De Patientia [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,078 | auto-corrected |
| athanasius-theology.sermo-exhortatorius-sp-e-cod-paris-gr-769 | Athanasius - Sermo Exhortatorius [Sp.] (E Cod. Paris. Gr. 769) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,290 | auto-corrected |
| athanasius-theology.sermo-in-annuntiationem-deiparae-sp | Athanasius - Sermo In Annuntiationem Deiparae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,105 | auto-corrected |
| athanasius-theology.sermo-in-nativitatem-christi-sp | Athanasius - Sermo In Nativitatem Christi [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,627 | auto-corrected |
| athanasius-theology.sermo-pro-iis-qui-saeculo-renuntiarunt-sp | Athanasius - Sermo Pro Iis Qui Saeculo Renuntiarunt [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,836 | auto-corrected |
| athanasius-theology.symbolum-quicumque-sp | Athanasius - Symbolum "Quicumque" [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,921 | auto-corrected |
| athanasius-theology.synopsis-scripturae-sacrae-sp | Athanasius - Synopsis Scripturae Sacrae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,187 | auto-corrected |
| athanasius-theology.syntagma-ad-monachos-e-cod-vossiano-gr-fol-46-sp | Athanasius - Syntagma Ad Monachos (E Cod. Vossiano Gr., Fol. 46) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,633 | raw OCR |
| athanasius-theology.syntagma-ad-quendam-politicum-sp | Athanasius - Syntagma Ad Quendam Politicum [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,903 | auto-corrected |
| athanasius-theology.testimonia-e-scriptura-de-communi-essentia-patris-et-filii-et-spiritus | Athanasius - Testimonia E Scriptura (De Communi Essentia Patris Et Filii Et Spiritus Sancti) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,702 | auto-corrected |
| athanasius-theology.vita-antonii | Athanasius - Vita Antonii | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,358 | auto-corrected |
| athanasius-theology.vita-sanctae-syncleticae-sp | Athanasius - Vita Sanctae Syncleticae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,741 | auto-corrected |
| athanasius-theology.vitae-monasticae-institutio-sp | Athanasius - Vitae Monasticae Institutio [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 726 | raw OCR |
| athenaeus-mechanics.de-machinis | Athenaeus - De Machinis | qwen36-athenaeus_mech_wescher | Qwen3.6-27B | 46,656 | auto-corrected |
| atridarum-reditus.fragmenta | Atridarum Reditus - Fragmenta | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 570 | auto-corrected |
| atridarum-reditus.fragmentum | Atridarum Reditus - Fragmentum | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 5 | raw OCR |
| autocharis.fragmentum | Autocharis - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 82 | auto-corrected |
| autocrates-comedy.fragmenta | Autocrates - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 74 | raw OCR |
| axionicus.fragmenta | Axionicus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 491 | raw OCR |
| basilides.fragmentum | Basilides - Fragmentum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33 | raw OCR |
| basilius-i-macedo.altera-paraenesis-ad-leonem-filium | Basilius I Macedo imperator - Altera paraenesis ad Leonem filium (PG107 loci 38-39) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 531 | auto-corrected |
| basilius-i-macedo.paraenesis-ad-leonem-filium | Basilius I Macedo imperator (revera fort. Photius) - Paraenesis ad Leonem filium (Exhortationum capita LXVI) (PG107 loci 20-37) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 6,491 | manual |
| basilius-scr-eccl.de-vita-et-miraculis-sanctae-theclae-libri-ii-sp | Basilius - De Vita Et Miraculis Sanctae Theclae Libri Ii [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,777 | auto-corrected |
| basilius-scr-eccl.sermones-xli | Basilius - Sermones Xli | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 69,840 | auto-corrected |
| basilius-theology.adversus-eunomium-libri-5 | Basilius - Adversus Eunomium (Libri 5) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 45,618 | auto-corrected |
| basilius-theology.asceticon-magnum-sive-quaestiones-regulae-brevius | Basilius - Asceticon Magnum Sive Quaestiones (Regulae Brevius Tractatae) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,709 | auto-corrected |
| basilius-theology.asceticon-magnum-sive-quaestiones-regulae-fusius | Basilius - Asceticon Magnum Sive Quaestiones (Regulae Fusius Tractatae) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,219 | auto-corrected |
| basilius-theology.consolatoria-ad-aegrotum-sp-sub-auctore-proclo | Basilius - Consolatoria Ad Aegrotum [Sp.] (Sub Auctore Proclo) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,800 | auto-corrected |
| basilius-theology.constitutiones-asceticae-sp | Basilius - Constitutiones Asceticae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,864 | auto-corrected |
| basilius-theology.contra-sabellianos-et-arium-et-anomoeos | Basilius - Contra Sabellianos Et Arium Et Anomoeos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,681 | raw OCR |
| basilius-theology.de-baptismo-libri-duo | Basilius - De Baptismo Libri Duo | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,741 | auto-corrected |
| basilius-theology.de-fide | De fide | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,017 | raw OCR |
| basilius-theology.de-humilitate | Basilius - De Humilitate | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,097 | auto-corrected |
| basilius-theology.de-jejunio-homilia-1 | Basilius - De Jejunio (Homilia 1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,866 | auto-corrected |
| basilius-theology.de-jejunio-homilia-2 | Basilius - De Jejunio (Homilia 2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,460 | auto-corrected |
| basilius-theology.de-jejunio-homilia-3-sp | Basilius - De Jejunio (Homilia 3) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,049 | auto-corrected |
| basilius-theology.de-spiritu-sancto | Basilius - De Spiritu Sancto | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,765 | auto-corrected |
| basilius-theology.enarratio-in-prophetam-isaiam-dub | Basilius - Enarratio In Prophetam Isaiam [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 91,458 | auto-corrected |
| basilius-theology.epitimia-in-canonicas-epitimia-25-dub | Basilius - Epitimia In Canonicas (Epitimia 25) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 814 | auto-corrected |
| basilius-theology.homilia-adversus-eos-qui-irascuntur | Homilia adversus eos qui irascuntur | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,221 | auto-corrected |
| basilius-theology.homilia-de-invidia | Homilia de invidia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,581 | auto-corrected |
| basilius-theology.homilia-de-misericordia-et-judicio-sp | Basilius - Homilia De Misericordia Et Judicio [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,043 | raw OCR |
| basilius-theology.homilia-de-spiritu-sancto-sp | Basilius - Homilia De Spiritu Sancto [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,534 | raw OCR |
| basilius-theology.homilia-dicta-in-lacisis | Basilius - Homilia Dicta In Lacisis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,185 | raw OCR |
| basilius-theology.homilia-dicta-tempore-famis-et-siccitatis | Homilia dicta tempore famis et siccitatis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,164 | auto-corrected |
| basilius-theology.homilia-exhortatoria-ad-sanctum-baptisma | Homilia exhortatoria ad sanctum baptisma | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,426 | auto-corrected |
| basilius-theology.homilia-in-divites | Homilia in divites | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,383 | auto-corrected |
| basilius-theology.homilia-in-illud-destruam-horrea-mea | Basilius - Homilia In Illud: Destruam Horrea Mea | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,594 | auto-corrected |
| basilius-theology.homilia-in-illud-ne-dederis-somnum-oculis-tuis-sp | Basilius - Homilia In Illud: Ne Dederis Somnum Oculis Tuis [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,560 | auto-corrected |
| basilius-theology.homilia-in-principium-proverbiorum | Homilia in principium proverbiorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,994 | auto-corrected |
| basilius-theology.homilia-in-psalmum-37-sp | Basilius - Homilia In Psalmum 37 [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,380 | auto-corrected |
| basilius-theology.homiliae-in-hexaemeron | Basilius - Homiliae In Hexaemeron | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,668 | auto-corrected |
| basilius-theology.homiliae-super-psalmos | Basilius - Homiliae Super Psalmos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 49,924 | auto-corrected |
| basilius-theology.in-barlaam-martyrem-sp | In Barlaam martyrem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 670 | auto-corrected |
| basilius-theology.in-ebriosos | In ebriosos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,427 | auto-corrected |
| basilius-theology.in-gordium-martyrem | In Gordium martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,483 | auto-corrected |
| basilius-theology.in-illud-in-principio-erat-verbum | Basilius - In Illud: In Principio Erat Verbum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,277 | raw OCR |
| basilius-theology.in-mamantem-martyrem | In Mamantem martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,698 | auto-corrected |
| basilius-theology.in-quadraginta-martyres-sebastenses | In quadraginta martyres Sebastenses | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,155 | auto-corrected |
| basilius-theology.in-sanctam-christi-generationem | Basilius - In Sanctam Christi Generationem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,806 | auto-corrected |
| basilius-theology.liturgia-recensio-brevior-vetusta | Basilius - Liturgia (Recensio Brevior Vetusta) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,761 | auto-corrected |
| basilius-theology.orationes-sive-exorcismi-sp | Basilius - Orationes Sive Exorcismi [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,318 | auto-corrected |
| basilius-theology.poenae-in-monachos-delinquentes-epitimia-24-dub | Basilius - Poenae In Monachos Delinquentes (Epitimia 24) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 268 | raw OCR |
| basilius-theology.prologus-3-prooemium-in-regulas-brevius-tractatas | Basilius - Prologus 3 (Prooemium In Regulas Brevius Tractatas) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 588 | raw OCR |
| basilius-theology.prologus-4-prooemium-in-asceticum-magnum | Basilius - Prologus 4 (Prooemium In Asceticum Magnum) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,941 | raw OCR |
| basilius-theology.prologus-5-sermo-asceticus-dub | Basilius - Prologus 5 (Sermo Asceticus) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,259 | auto-corrected |
| basilius-theology.prologus-7-de-judicio-dei | Basilius - Prologus 7 (De Judicio Dei) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,190 | raw OCR |
| basilius-theology.prologus-8-de-fide | Basilius - Prologus 8 (De Fide) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,867 | auto-corrected |
| basilius-theology.quod-deus-non-est-auctor-malorum | Quod deus non est auctor malorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,805 | auto-corrected |
| basilius-theology.quod-rebus-mundanis-adhaerendum-non-sit | Quod rebus mundanis adhaerendum non sit | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,945 | auto-corrected |
| basilius-theology.regulae-morales | Basilius - Regulae Morales | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,318 | auto-corrected |
| basilius-theology.sermo-10-praevia-institutio-ascetica-dub | Sermo 10 (praevia institutio ascetica) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 848 | auto-corrected |
| basilius-theology.sermo-11-sermo-asceticus-et-exhortatio-de-renuntiatione-mundi | Sermo 11 (sermo asceticus et exhortatio de renuntiatione mundi) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,710 | auto-corrected |
| basilius-theology.sermo-ob-sacerdotum-instructionem-recensio-brevior-sp | Basilius - Sermo Ob Sacerdotum Instructionem (Recensio Brevior) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 598 | auto-corrected |
| basilius-theology.sermones-de-moribus-symeone-metaphrasta-collecti | Basilius - Sermones De Moribus A Symeone Metaphrasta Collecti | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 47,923 | auto-corrected |
| beros-s-us.fragmenta | Beros(S)Us - Fragmenta | qwen36-demochares_fhg2-ocr | Qwen3.6-27B | 1,842 | auto-corrected |
| bion-history.fragmenta | Bion - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 55 | raw OCR |
| bion-mathematics.testimonia | Bion - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 94 | raw OCR |
| bion-philosophy.fragmenta | Bion - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,673 | auto-corrected |
| blaesus.fragmentum | BLAESUS - Fragmentum | qwen36-sopater_kaibel_cgf-ocr | Qwen3.6-27B | 113 | raw OCR |
| boethus.fragmenta | Fragmenta | qwen36-apollodorus_seleuc_svf3-ocr | Qwen3.6-27B | 588 | auto-corrected |
| boidas.testimonium | Boïdas - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 84 | raw OCR |
| bolus.testimonium | Bolus - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 28 | raw OCR |
| brotinus.testimonia | Brotinus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 502 | auto-corrected |
| bryson.fragmentum | Bryson - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 238 | raw OCR |
| butherus.fragmentum | Butherus - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 148 | raw OCR |
| callias.fragmenta | Callias - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 529 | raw OCR |
| callicratidas.fragmenta | Callicratidas - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 1,336 | auto-corrected |
| callimachus.callimachea-schneider-v1 |  | qwen36-callimachea_schneider_v1 | Qwen3.6-27B | 18,253 | auto-corrected |
| callinus.fragmenta | Callinus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 149 | raw OCR |
| calliphon-et-democedes.testimonia | Calliphon Et Democedes - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,465 | auto-corrected |
| callixenus.fragmenta | Callixenus - Fragmenta | qwen36-fhg_vol3_mueller_diocles_rhodius-ocr | Qwen3.6-27B | 3,805 | auto-corrected |
| cantharus.fragmenta | Cantharus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 149 | auto-corrected |
| carcinus-junior.fragmenta | Carcinus Junior - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 665 | raw OCR |
| carmina-convivialia-pmg.fragmenta | Carmina Convivialia (Pmg) - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 4,946 | auto-corrected |
| carmina-popularia-pmg.fragmenta | CARMINA POPULARIA (PMG) - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,141 | auto-corrected |
| castor-rhetor.peri-metron-rhetorikon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,421 | auto-corrected |
| cephisodorus.fragmenta | Cephisodorus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 288 | raw OCR |
| cercidas.fragmenta | Cercidas - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 351 | auto-corrected |
| cercops.testimonium | Cercops - Testimonium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 52 | raw OCR |
| chaeremon-history.fragmenta | Chaeremon - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 929 | auto-corrected |
| chaeremon-tragedy.fragmenta | Chaeremon - Fragmenta | nauck-tgf-ocr-frag | Qwen3.6-27B | 814 | raw OCR |
| charax.fragmenta | Charax - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 1,375 | auto-corrected |
| chariclides.fragmentum | CHARICLIDES - Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 103 | raw OCR |
| chionides.fragmenta | Chionides - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 113 | raw OCR |
| choerilus-tragedy.fragmenta | Choerilus - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 30 | raw OCR |
| choerilus.fragmenta-epica | Fragmenta epica | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 830 | auto-corrected |
| choricius.opera | Choricius - Opera | qwen36-choricius_boissonade | Qwen3.6-27B | 67,386 | auto-corrected |
| cinesias.fragmentum | Cinesias - Fragmentum | bergk-plg3-ocr-frag | Qwen3.6-27B | 119 | raw OCR |
| claudius-apollinarius.fragmenta | Claudius Apollinarius Hierapolitanus - Fragmenta (PG005 loci 657-660) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 346 | auto-corrected |
| clearchus-comedy.fragmenta | Clearchus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 181 | raw OCR |
| clearchus-philosophy.fragmenta | Clearchus - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 31,491 | auto-corrected |
| cleobulina-scriptor-aenigmatum.fragmenta | Cleobulina Scriptor Aenigmatum - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 167 | raw OCR |
| cleostratus.testimonia | CLEOSTRATUS - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 352 | auto-corrected |
| clidemus-philosophy.testimonia | Clidemus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 314 | auto-corrected |
| clinias.fragmenta | Clinias - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 165 | raw OCR |
| cocondrius.peri-tropon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,481 | manual |
| PG003 | Pseudo-Dionysius Areopagita v1 | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 160,260 | manual |
| PG005 | Ignatius, Polycarp, Melito, 2nd-c. popes (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,534 | manual |
| PG101 | Photius (Amphilochia, NT commentary) (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 515 | manual |
| PG107 | Leo VI the Wise (homilies, Tactica) (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,050 | manual |
| PG109 | Theophanes Cont.; Cameniates; Symeon Logothete; Genesius (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 7 | manual |
| PG112 | Constantine VII v1 De ceremoniis (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 75,862 | manual |
| PG113 | Constantine VII v2 De them./De admin./Vita Basilii; Theodosius Diac. (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,039 | manual |
| PG118 | Oecumenius (catenae on Acts, Pauline & Catholic epistles) (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,830 | manual |
| PG124 | Theophylact of Ohrid v2 (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 99 | manual |
| PG125 | Theophylact of Ohrid v3 (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,629 | manual |
| PG139 | Joel; Nicetas Choniates (+Thesaurus); Isidore Thess.; Maroneia; John of Citrus (split per-work by scripts/carve_cgpg_volume.py; residual rows only) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,349 | manual |
| comarius.peri-th-s-qei-as-kai-i-era-s-te-xnhs-tw-n-filoso-fwn-e | Comarius - Περὶ τῆς θείας καὶ ἱερᾶς τέχνης τῶν φιλοσόφων (E Cod. Paris. B.N. Gr. 2327, Fol. 79V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 8 | raw OCR |
| comica-adespota-caf.fragmenta-incertorum-poetarum | Comica adespota - Fragmenta incertorum poetarum | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 54,499 | raw OCR |
| commentaria-in-dionysii-thracis-artem-grammaticam.prolegomena-vossiana | Commentaria In Dionysii Thracis Artem Grammaticam - Prolegomena Vossiana | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 229,685 | auto-corrected |
| constantinus-siculus.versus-in-leonem-philosophum | Constantinus Siculus - Versus in Leonem Philosophum (carmina de apostasia Leonis, cum responsione) (PG107 loci 40-41) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 257 | manual |
| constantinus-vii-porphyrogenitus-imperator.de-cerimoniis-aulae-byzantinae-lib-1-84-2-56-reiske | Constantinus VII Porphyrogenitus - De cerimoniis aulae Byzantinae (lib. 1.84-2.56) (PG112 loci 354-730) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 73,431 | manual |
| constantinus-vii-porphyrogenitus-imperator.de-virtutibus-et-vitiis | Constantinus VII Porphyrogenitus Imperator - De Virtutibus Et Vitiis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 212,990 | manual |
| constantinus-vii-porphyrogenitus-imperator.narratio-de-imagine-edessena | Constantinus VII Porphyrogenitus Imperator - Narratio de imagine Edessena (PG113 loci 223-237) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,761 | manual |
| constantinus-vii-porphyrogenitus-imperator.novellae-constitutiones | Constantinus VII Porphyrogenitus Imperator - Novellae constitutiones (PG113 loci 286-313) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,084 | manual |
| corinna.fragmenta | CORINNA - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 636 | auto-corrected |
| cosmas-hieromonachus.ermhnei-th-s-e-pisth-mhs-th-s-xrusopoii-as-i-eromona-xou-tou | Cosmas Hieromonachus - Ἑρμηνεία τῆς ἐπιστήμης τῆς χρυσοποιίας ἱερομονάχου τοῦ Κοσμᾶ (E Cod. Paris. B.N. Gr. 2327, Fol. 159R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,176 | auto-corrected |
| cougny-appendix-nova.didot-anthologia-v3 | Appendix nova epigrammatum (Didot Anthologia Graeca vol. 3) | qwen36-thomas_patricius_anthol_dubner_v3 | Qwen3.6-27B | 101,426 | auto-corrected |
| crates-comedy.fragmenta | Crates - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 1,024 | raw OCR |
| crates-poet-phil.fragmenta | Crates - Fragmenta | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 4,268 | auto-corrected |
| cratinus-junior.fragmenta | Cratinus Junior - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 266 | raw OCR |
| cratinus.fragmenta | Cratinus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 9,074 | auto-corrected |
| cratylus.testimonia | Cratylus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 681 | auto-corrected |
| crinis.fragmenta | Crinis - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 281 | raw OCR |
| critias.fragmenta | Critias - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 663 | raw OCR |
| critias.testimonia | Critias - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,715 | auto-corrected |
| crito-vel-damippus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 665 | raw OCR |
| critolaus-history.fragmenta | Critolaus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 134 | raw OCR |
| crobylus.fragmenta | CROBYLUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 316 | raw OCR |
| ctesias.fragmenta | Ctesias - Fragmenta | qwen36-ctesias_gilmore-ocr | Qwen3.6-27B | 31,082 | auto-corrected |
| cypria.cypria-fragmenta | Cypria - Cypria (Fragmenta) | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 2,651 | auto-corrected |
| cyrillus-scr-eccl.catecheses-ad-illuminandos-1-18 | Cyrillus - Catecheses Ad Illuminandos 1-18 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,603 | auto-corrected |
| cyrillus-scr-eccl.epistula-ad-constantium-imperatorem | Cyrillus - Epistula Ad Constantium Imperatorem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,737 | auto-corrected |
| cyrillus-scr-eccl.homilia-in-occursum-domini-sp | Cyrillus - Homilia In Occursum Domini [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,251 | auto-corrected |
| cyrillus-scr-eccl.mystagogiae-1-5-sp | Cyrillus - Mystagogiae 1-5 [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,718 | auto-corrected |
| cyrillus-scr-eccl.procatechesis | Cyrillus - Procatechesis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,577 | auto-corrected |
| cyrillus-theology.ad-calosyrium-epist-83 | Cyrillus - Ad Calosyrium (Epist. 83) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,320 | raw OCR |
| cyrillus-theology.ad-euoptium-episcopum-ptolemaidis-epist-84 | Cyrillus - Ad Euoptium Episcopum Ptolemaidis (Epist. 84) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 822 | auto-corrected |
| cyrillus-theology.apologeticus-ad-theodosium-imperatorem | Cyrillus - Apologeticus Ad Theodosium Imperatorem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,309 | auto-corrected |
| cyrillus-theology.apologia-xii-anathematismorum-contra-theodoretum | Cyrillus - Apologia Xii Anathematismorum Contra Theodoretum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,192 | auto-corrected |
| cyrillus-theology.apologia-xii-capitulorum-contra-orientales | Cyrillus - Apologia Xii Capitulorum Contra Orientales | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,271 | auto-corrected |
| cyrillus-theology.collectio-dictorum-veteris-testamenti-sp | Cyrillus - Collectio Dictorum Veteris Testamenti [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,583 | auto-corrected |
| cyrillus-theology.commentarii-in-joannem | Cyrillus - Commentarii In Joannem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 179,007 | auto-corrected |
| cyrillus-theology.commentarii-in-lucam-in-catenis | Cyrillus - Commentarii In Lucam (In Catenis) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 86,969 | auto-corrected |
| cyrillus-theology.commentarius-in-isaiam-prophetam | Cyrillus - Commentarius In Isaiam Prophetam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 293,813 | auto-corrected |
| cyrillus-theology.contra-julianum-lib-1-2 | Cyrillus - Contra Julianum (Lib. 1-2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 121,002 | auto-corrected |
| cyrillus-theology.de-incarnatione-dei-verbi-homilia-diversa-15 | Cyrillus - De Incarnatione Dei Verbi (Homilia Diversa 15) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,122 | raw OCR |
| cyrillus-theology.de-incarnatione-unigeniti | Cyrillus - De Incarnatione Unigeniti | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,121 | auto-corrected |
| cyrillus-theology.de-sancta-trinitate-dialogi-ivii | Cyrillus - De Sancta Trinitate Dialogi I-Vii | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 81,358 | auto-corrected |
| cyrillus-theology.de-sancta-trinitate-sp | Cyrillus - De Sancta Trinitate [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 16,997 | auto-corrected |
| cyrillus-theology.dialogus-cum-nestorio-sp | Cyrillus - Dialogus Cum Nestorio [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,252 | auto-corrected |
| cyrillus-theology.epistulae-paschales-sive-homiliae-paschales-epist-1-30 | Cyrillus - Epistulae Paschales Sive Homiliae Paschales (Epist. 1-30) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 118,202 | auto-corrected |
| cyrillus-theology.explanatio-xii-capitulorum | Cyrillus - Explanatio Xii Capitulorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,016 | auto-corrected |
| cyrillus-theology.expositio-in-psalmos | Cyrillus - Expositio In Psalmos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 95,623 | auto-corrected |
| cyrillus-theology.expositio-in-psalmos-prooemium | Cyrillus - Expositio In Psalmos (Prooemium) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 367 | raw OCR |
| cyrillus-theology.fragmenta-in-canticum-canticorum | Cyrillus - Fragmenta In Canticum Canticorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,680 | raw OCR |
| cyrillus-theology.fragmenta-in-libros-regum | Cyrillus - Fragmenta In Libros Regum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,753 | auto-corrected |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ad-hebraeos | Cyrillus - Fragmenta In Sancti Pauli Epistulam Ad Hebraeos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,318 | raw OCR |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ad-romanos | Cyrillus - Fragmenta In Sancti Pauli Epistulam Ad Romanos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 27,999 | auto-corrected |
| cyrillus-theology.fragmenta-in-sancti-pauli-epistulam-ii-ad-corinthios | Cyrillus - Fragmenta In Sancti Pauli Epistulam Ii Ad Corinthios | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,107 | auto-corrected |
| cyrillus-theology.libri-v-contra-nestorium | Cyrillus - Libri V Contra Nestorium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 50,043 | auto-corrected |
| cyrillus-theology.oratio-ad-arcadiam-et-marinam-augustas-de-fide | Cyrillus - Oratio Ad Arcadiam Et Marinam Augustas De Fide | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,398 | auto-corrected |
| cyrillus-theology.oratio-ad-pulcheriam-et-eudociam-augustas-de-fide | Cyrillus - Oratio Ad Pulcheriam Et Eudociam Augustas De Fide | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,879 | auto-corrected |
| cyrillus-theology.oratio-ad-theodosium-imperatorem-de-recta-fide | Cyrillus - Oratio Ad Theodosium Imperatorem De Recta Fide | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,351 | auto-corrected |
| cyrillus-theology.quod-unus-sit-christus | Cyrillus - Quod Unus Sit Christus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 18,713 | auto-corrected |
| cyrillus-theology.responsiones-ad-tiberium-diaconum-sociosque-suos | Cyrillus - Responsiones Ad Tiberium Diaconum Sociosque Suos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,229 | auto-corrected |
| cyrillus-theology.scholia-de-incarnatione-unigeniti-fragmenta | Cyrillus - Scholia De Incarnatione Unigeniti (Fragmenta) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,008 | auto-corrected |
| cyrillus-theology.sermo-de-obitu-sanctorum-trium-puerorum-fragmenta-sp | Cyrillus - Sermo De Obitu Sanctorum Trium Puerorum (Fragmenta) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,178 | auto-corrected |
| cyrillus-theology.thesaurus-de-sancta-consubstantiali-trinitate | Cyrillus - Thesaurus De Sancta Consubstantiali Trinitate | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 131,280 | auto-corrected |
| cyrus-rhetor.peri-diaphoras-staseos |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,360 | manual |
| damascius.de-principiis | DAMASCIUS - De principiis (Ἀπορίαι καὶ λύσεις περὶ τῶν πρώτων ἀρχῶν) | [Damascius, ed. Ruelle (MDZ scan + HathiTrust, ROVER-merged; primary OCR Qwen3.6)](https://www.digitale-sammlungen.de/en/view/bsb00075170) | Qwen3.6-27B-FP8 | 119,302 | auto-corrected |
| damascius.in-parmenidem | DAMASCIUS - In Parmenidem | [Damascius, ed. Ruelle (MDZ scan + HathiTrust, ROVER-merged; primary OCR Qwen3.6)](https://www.digitale-sammlungen.de/en/view/bsb00075170) | Qwen3.6-27B-FP8 | 132,536 | auto-corrected |
| damascius.vita-isidori-ap-sudam-hesychium-photium-et-e-cod-vat | DAMASCIUS - Vita Isidori (fragmenta ap. Sudam etc.) | qwen36-damascius-boissonade | Qwen3.6-27B | 12,624 | raw OCR |
| damianus-scriptor-de-opticis.optica | Damianus Scriptor De Opticis - Optica | qwen36-damianus_schoene | Qwen3.6-27B | 3,447 | auto-corrected |
| damon-et-phintias.testimonium | Damon Et Phintias - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 308 | raw OCR |
| damoxenus.fragmenta | DAMOXENUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 291 | auto-corrected |
| demetrius-comedy.fragmenta | Demetrius - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 226 | raw OCR |
| demetrius-cydones.occisorum-thessalonicae-monodia | Demetrius Cydones - Occisorum Thessalonicae monodia (PG109 loci 325-331) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,526 | manual |
| demetrius-poet-phil.demetrius-de-eloc-roberts |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,272 | auto-corrected |
| demetrius-poet-phil.fragmenta-et-titulus | Demetrius - Fragmenta Et Titulus | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 144 | raw OCR |
| demochares.fhg2 |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 111,581 | auto-corrected |
| demochares.fragmenta | Demochares - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 1,356 | auto-corrected |
| democritus-history.fragmentum | Democritus - Fragmentum | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 135 | raw OCR |
| democritus-philosophy.testimonia | Democritus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 48,936 | auto-corrected |
| demodocus.fragmenta | Demodocus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 2,007 | auto-corrected |
| demon.fragmenta | Demon - Fragmenta | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 334 | raw OCR |
| demonax-philosophy.fragmenta | Demonax - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,374 | auto-corrected |
| dercyllus.fragmenta | Dercyllus - Fragmenta | qwen36-staphylus_fhg4-ocr | Qwen3.6-27B | 124 | auto-corrected |
| diagoras.fragmenta | DIAGORAS - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 206 | auto-corrected |
| didymus.schmidt |  | qwen36-didymus_schmidt | Qwen3.6-27B | 39,037 | auto-corrected |
| diels-fdv2-1906-1.paratexta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 46 | auto-corrected |
| diels-fvs-1903.paratexta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 199 | raw OCR |
| diels-ppf-1901.paratexta |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 6,403 | auto-corrected |
| dindorf-hgm1.paratexta |  | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 8,535 | auto-corrected |
| dindorf-hgm2.paratexta |  | qwen36-menander_protector_dindorf_hgm | Qwen3.6-27B | 302 | auto-corrected |
| dinolochus.fragmentum | DINOLOCHUS - Fragmentum | qwen36-rhinthon_kaibel_cgf_1899-ocr | Qwen3.6-27B | 391 | auto-corrected |
| diocles-echecrates-polymnastus-phanton-arion.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 62 | raw OCR |
| diocles.fragmenta | Diocles - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 213 | auto-corrected |
| diodorus-aspendius.fragmentum | Diodorus - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 16 | raw OCR |
| diodorus-comedy.fragmenta | Diodorus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 152 | raw OCR |
| diogenes-apolloniates.testimonia | Diogenes - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,568 | auto-corrected |
| diogenes-oenoandensis.diogenes-oenoanda-william |  | qwen36-diogenes_oenoanda_william | Qwen3.6-27B | 10,112 | auto-corrected |
| diogenes-philosophy.fragmenta | Diogenes - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 208 | raw OCR |
| diogenes-sinopensis.fragmenta-et-apophthegmata | Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 11,181 | auto-corrected |
| diogenes-smyrnaeus.testimonium | Diogenes - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 24 | raw OCR |
| diogenes.fragmentum | Fragmentum | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 243 | auto-corrected |
| dionysius-chalcus.fragmenta | DIONYSIUS CHALCUS - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 436 | raw OCR |
| dionysius-comedy.fragmenta | Dionysius - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 280 | raw OCR |
| dionysius-i-tragedy.fragmenta | Dionysius I - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 457 | auto-corrected |
| dionysius-metaqemenos.fragmenta | Fragmenta | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 515 | auto-corrected |
| dionysius-milesius.fragmenta | Dionysius - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 559 | raw OCR |
| dionysius-soph.epistulae | Dionysius - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,346 | auto-corrected |
| dionysius-thrax-grammar.ars-grammatica | Dionysius Thrax - Ars Grammatica | [Dionysius Thrax, Ars grammatica, ed. Uhlig (Grammatici Graeci I.1)](https://archive.org/search?query=Grammatici+Graeci+Uhlig+Dionysii+Thracis) | Qwen3.6-27B | 6,232 | auto-corrected |
| diophantus-mathematics.arithmeticorum-libri-sex | DIOPHANTUS - Arithmetica | qwen36-diophantialexan01plangoog | Qwen3.6-27B | 52,458 | raw OCR |
| dioscurides.fragmenta | Dioscurides - Fragmenta | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 757 | auto-corrected |
| diotimus-philosophy.testimonia | Diotimus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178 | raw OCR |
| dioxippus.fragmenta | DIOXIPPUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 31 | raw OCR |
| diphilus-comedy.fragmenta | Diphilus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 3,360 | auto-corrected |
| diphilus-epic.fragmentum | Diphilus - Fragmentum | bergk-plg2-ocr-frag | Qwen3.6-27B | 130 | raw OCR |
| dius.fragmenta | Dius - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 361 | auto-corrected |
| dosiadas.fragmenta | Fragmenta | qwen36-socrates_hist_fhg4-ocr | Qwen3.6-27B | 1 | raw OCR |
| dositheus-magister.ars-grammatica | Dositheus Magister - Ars Grammatica | [archive.org](https://archive.org/details/arsgrammaticarec00dosiuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 6,492 | raw OCR |
| dromo.fragmenta | Dromo - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 43 | raw OCR |
| ducas.historia-turcobyzantina | Ducas - Historia Turcobyzantina (PG157 loci 382-590) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 68,757 | manual |
| ecphantides.fragmenta | Ecphantides - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 133 | raw OCR |
| ecphantus.testimonia | Ecphantus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 335 | raw OCR |
| elias-cretensis.commentarii-in-sancti-gregorii-nazianzeni-orationes-xix | Elias Cretensis - Commentarii in sancti Gregorii Nazianzeni orationes xix | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 38,707 | auto-corrected |
| empedocles.diels-ppf |  | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 23,715 | auto-corrected |
| empedocles.epigramma | Empedocles - Epigramma | bergk-plg2-ocr-frag | Qwen3.6-27B | 5,446 | raw OCR |
| empedocles.testimonia | Empedocles - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 40,656 | auto-corrected |
| ephippus.fragmenta | Ephippus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 1,026 | raw OCR |
| epicharmus-et-pseudepicharmea.testimonia | Epicharmus Et Pseudepicharmea - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 5,241 | auto-corrected |
| epicrates.fragmenta | Epicrates - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 373 | raw OCR |
| epicurus.deperditorum-librorum-reliquiae | EPICURUS - Deperditorum librorum reliquiae (Usener, Epicurea) | qwen36-usener-epicurea-1887 | Qwen3.6-27B | 64,436 | raw OCR |
| epigenes.fragmenta | Epigenes - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 219 | raw OCR |
| epigonus-ap-cougny-v1 |  | qwen36-epigonus_ap_cougny_v1 | Qwen3.6-27B | 79,311 | auto-corrected |
| epilycus.fragmenta | Epilycus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 272 | auto-corrected |
| epimenides.testimonia-2 | Epimenides - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,983 | auto-corrected |
| epinicus.fragmenta | EPINICUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 172 | raw OCR |
| epistula-ecclesiarum-apud-lugdunum-et-viennam.epistula-ecclesiarum-apud-lugdunum-et-viennam | Epistula ecclesiarum apud Lugdunum et Viennam - Epistula ecclesiarum apud Lugdunum et Viennam (cum appendicibus ap. Eus. HE 5.1-4) (PG005 loci 715-736) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,668 | manual |
| eratosthenes-et-eratosthenica.catasterismi | Eratosthenes Et Eratosthenica - Catasterismi | qwen36-eratosthenes_bernhardy | Qwen3.6-27B | 20,736 | auto-corrected |
| erinna.fragmenta | Erinna - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,148 | auto-corrected |
| eriphus.fragmenta | Eriphus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 173 | raw OCR |
| erotianus.vocum-hippocraticarum-collectio | Erotianus - Vocum Hippocraticarum Collectio | qwen36-erotianus_nachmanson_1918 | Qwen3.6-27B | 18,499 | auto-corrected |
| esaias-cyprius.epistola-de-processione-spiritus-sancti | Esaias Cyprius - Epistola (anti-Latin, on the procession of the Holy Spirit) (PG158 loci 521-523) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 707 | auto-corrected |
| etymologicum-genuinum.etymologicum-genuinum-mwsge-pws | Etymologicum Genuinum - Etymologicum Genuinum (α-ἁμωσγέπως) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 71,823 | auto-corrected |
| etymologicum-gudianum.etymologicum-gudianum-lion-zeiai | ETYMOLOGICUM GUDIANUM - Etymologicum Gudianum | qwen36-etym-gudianum-sturz-bsb | Qwen3.6-27B | 323,254 | raw OCR |
| euagon.fragmenta | Euagon - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 213 | auto-corrected |
| euangelus.fragmentum | EUANGELUS - Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 158 | raw OCR |
| eubulides.fragmentum | Eubulides - Fragmentum | kock-caf2-ocr-frag | Qwen3.6-27B | 72 | raw OCR |
| eubulus.fragmenta | Eubulus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 4,383 | auto-corrected |
| eudemus-philosophy.fragmenta | Eudemus - Fragmenta | qwen36-eudemus_spengel_1866 | Qwen3.6-27B | 39,732 | auto-corrected |
| eudoxus-astronomy.fragmenta | Eudoxus - Fragmenta | qwen36-eudoxus_ars_astronomica_blass | Qwen3.6-27B | 3,807 | auto-corrected |
| eudoxus.fragmenta | EUDOXUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 79 | raw OCR |
| eudromus.fragmenta | Eudromus - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 67 | raw OCR |
| euenus.fragmenta | EUENUS - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 534 | raw OCR |
| euhemerus.fragmenta | Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,136 | auto-corrected |
| eumelus.fragmentum | Eumelus - Fragmentum | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 1,142 | auto-corrected |
| eunicus.fragmentum | Eunicus - Fragmentum | kock-caf1-ocr-frag | Qwen3.6-27B | 117 | raw OCR |
| euphorion.fragmenta | Euphorion - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,688 | auto-corrected |
| eupolis.fragmenta | Eupolis - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 9,473 | auto-corrected |
| euryphamus.fragmentum | Euryphamus - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 811 | auto-corrected |
| eurytus.fragmentum | Eurytus - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 234 | auto-corrected |
| eurytus.testimonia | Eurytus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 608 | raw OCR |
| eusebius-scr-eccl.antiquorum-martyriorum-collectio-fragmenta | Eusebius - Antiquorum Martyriorum Collectio (Fragmenta) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,698 | auto-corrected |
| eusebius-scr-eccl.de-solemnitate-paschali | Eusebius - De Solemnitate Paschali | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,629 | auto-corrected |
| eusebius-scr-eccl.de-vitis-prophetarum-fragmenta | Eusebius - De Vitis Prophetarum (Fragmenta) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,496 | auto-corrected |
| eusebius-scr-eccl.epistula-ad-carpianum-ad-canones-evangeliorum-praemissa | Eusebius - Epistula Ad Carpianum Ad Canones Evangeliorum Praemissa | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,084 | auto-corrected |
| eusebius-scr-eccl.fragmenta-in-lucam | Eusebius - Fragmenta In Lucam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,432 | auto-corrected |
| eusebius-scr-eccl.quaestiones-evangelicae-ad-marinum | Eusebius - Quaestiones Evangelicae Ad Marinum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,142 | auto-corrected |
| eusebius-scr-eccl.quaestiones-evangelicae-ad-stephanum | Eusebius - Quaestiones Evangelicae Ad Stephanum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,796 | auto-corrected |
| eusebius-scr-eccl.supplementa-ad-quaestiones-ad-marinum | Eusebius - Supplementa Ad Quaestiones Ad Marinum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,492 | auto-corrected |
| eustathius-philol.commentarii-ad-homeri-iliadem | Eustathius Thessalonicensis - Commentarii ad Homeri Iliadem | qwen36-eustathius-iliad-stallbaum | Qwen3.6-27B | 1,069,461 | raw OCR |
| eustathius-philol.commentarii-ad-homeri-odysseam | EUSTATHIUS - Commentarii ad Homeri Odysseam (ed. Stallbaum) | [Eustathius, Commentarii ad Homeri Odysseam, ed. Stallbaum (Leipzig 1825-26), re-keyed by Stallbaum edition page](https://archive.org/details/commentariiadhom01eust) | Qwen3.6-27B-FP8 | 539,821 | auto-corrected |
| eustratius.in-aristotelis-analyticorum-posteriorum-librum-secundum-commentarium | EUSTRATIUS - In Aristotelis Analyticorum Posteriorum Librum Secundum Commentarium | qwen36-inanalyticorumpo00eust | Qwen3.6-27B | 110,851 | raw OCR |
| eutecnius.paraphrasis-in-oppiani-cynegetica-fort-auctore-eutecnio | Eutecnius - Paraphrasis In Oppiani Cynegetica (Fort. Auctore Eutecnio) | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 430 dpi) | 3,965 | raw OCR |
| euthalius-diaconus.apodemiai-pauli | Euthalius Diaconus - Apodemiae Pauli (PG118 loci 165-167, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,027 | manual |
| euthalius-diaconus.martyrium-pauli | Euthalius Diaconus - Martyrium Pauli (PG118 loci 167, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 67 | manual |
| euthalius-diaconus.prologus-in-epistulas-pauli | Euthalius Diaconus - Prologus in epistulas Pauli (PG118 loci 163-165, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 643 | manual |
| euthycles.fragmenta | EUTHYCLES - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 83 | raw OCR |
| fhg-vol3-mueller-diocles-rhodius |  | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 89,233 | auto-corrected |
| flavius-justinianus-imperator.novellae | Flavius Justinianus Imperator - Novellae | qwen36-justinian_novellae_schoell | Qwen3.6-27B | 234,311 | auto-corrected |
| fragmenta-alchemica.bafh-tou-i-ndikou-sidh-rou-grafei-sa-tw-au-tw-xro-nw | Fragmenta Alchemica - Βαφὴ τοῦ Ἰνδικοῦ σιδήρου, γραφεῖσα τῷ αὐτῷ χρόνῳ | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 199 | raw OCR |
| fragmenta-alchemica.bafh-tou-para-pe-rsais-e-ceurhme-nou-xalkou-grafei-sa-po | Fragmenta Alchemica - Βαφὴ τοῦ παρὰ Πέρσαις ἐξευρημένου χαλκοῦ γραφεῖσα ἀπὸ ἀρχῆς Φιλίππου (E Cod. Venet. Marc. 299, Fol. 118R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 269 | raw OCR |
| fragmenta-alchemica.de-margaritis-collectio-excerptorum-quae-incipit-vocibus | Fragmenta Alchemica - De Margaritis (Collectio Excerptorum Quae Incipit A Vocibus Σμῆξις καὶ λάμπρυνσις μαργάρων ᾗ πολλάκις ὁ δεδωκὼς ἔλεγε χρῆσθαι) (E Cod. Paris. B.N. Gr. 2327, Fol. 143V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 934 | auto-corrected |
| fragmenta-alchemica.de-quattuor-elementis-tractatus-qui-incipit-vocibus-rxh-th-s | Fragmenta Alchemica - De Quattuor Elementis (Tractatus Qui Incipit A Vocibus ἀρχὴ τῆς κατὰ πλάτος τοῦ ἔργου ἐξηγήσεως) (E Cod. Paris. B.N. Gr. 2327, Fol. 227R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,548 | auto-corrected |
| fragmenta-alchemica.dia-gramma-th-s-mega-lhs-h-liourgi-as-paraballo-menon-ei-s-th-n | Fragmenta Alchemica - Διάγραμμα τῆς μεγάλης ἡλιουργίας παραβαλλόμενον εἰς τὴν οἰκονομίαν τοῦ παντός (E Cod. Venet. Marc. 299, Fol. 62R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 167 | raw OCR |
| fragmenta-alchemica.diaforai-moli-bdou-kai-xrusopeta-lou-e-cod-venet-marc | Fragmenta Alchemica - Διαφοραὶ μολίβδου καὶ χρυσοπετάλου (E Cod. Venet. Marc. 299, Fol. 130R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 623 | auto-corrected |
| fragmenta-alchemica.ei-qe-leis-poih-sai-fou-rmas-kai-tu-lous-po-bronthsi-ou-poi-ei | Fragmenta Alchemica - Εἰ θέλεις ποιῆσαι φούρμας καὶ τύλους ἀπὸ βροντησίου, ποίει οὕτως (E Cod. Venet. Marc. 299, Fol. 128V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 456 | raw OCR |
| fragmenta-alchemica.eu-xh-ei-s-meli-ssion-e-cod-venet-marc-299-fol-3r | Fragmenta Alchemica - Εὐχὴ εἰς τὸ μελίσσιον (E Cod. Venet. Marc. 299, Fol. 3R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 195 | auto-corrected |
| fragmenta-alchemica.excerptum-de-mensibus-sine-titulo-e-cod-paris-b-n-gr-2327 | Fragmenta Alchemica - Excerptum De Mensibus (Sine Titulo) (E Cod. Paris. B.N. Gr. 2327, Fol. 240V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 99 | auto-corrected |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol | Fragmenta Alchemica - Fragmentum Alchemicum (Sine Titulo) (E Cod. Venet. Marc. 299, Fol. 99V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 49 | raw OCR |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-2 | Fragmenta Alchemica - Fragmentum Alchemicum (Sine Titulo) (E Cod. Venet. Marc. 299, Fol. 100R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 194 | auto-corrected |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-3 | Fragmenta Alchemica - Fragmentum Alchemicum (Sine Titulo) (E Cod. Venet. Marc. 299, Fol. 100V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 107 | raw OCR |
| fragmenta-alchemica.fragmentum-alchemicum-sine-titulo-e-cod-venet-marc-299-fol-4 | Fragmenta Alchemica - Fragmentum Alchemicum (Sine Titulo) (E Cod. Venet. Marc. 299, Fol. 100V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 51 | raw OCR |
| fragmenta-alchemica.fragmentum-peri-leukw-sews-xalkou-sine-titulo-e | Fragmenta Alchemica - Fragmentum περὶ λευκώσεως (χαλκοῦ) (Sine Titulo) (E Cod. Paris. Gr. 2327, Fol. 231V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 240 | raw OCR |
| fragmenta-alchemica.h-gwgh-e-cod-venet-marc-299-101r | Fragmenta Alchemica - Ἡ ἀγωγή (E Cod. Venet. Marc. 299, 101R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 27 | raw OCR |
| fragmenta-alchemica.h-oi-konomi-e-cod-venet-marc-299-fol-98v | Fragmenta Alchemica - Ἡ οἰκονομία (E Cod. Venet. Marc. 299, Fol. 98V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 196 | raw OCR |
| fragmenta-alchemica.h-poi-hsis-e-cod-venet-marc-299-fol-100v | Fragmenta Alchemica - Ἡ ποίησις (E Cod. Venet. Marc. 299, Fol. 100V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 35 | raw OCR |
| fragmenta-alchemica.katabafh-li-qwn-kai-smara-gdwn-kai-lixnitw-n-kai | Fragmenta Alchemica - Καταβαφὴ λίθων καὶ σμαράγδων καὶ λιχνιτῶν καὶ ὑακίνθων (E Cod. Paris. B.N. Gr. 2327, Fol. 147R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,650 | auto-corrected |
| fragmenta-alchemica.kinnaba-rews-skeuasi-e-cod-paris-b-n-gr-2327-fol | Fragmenta Alchemica - Κινναβάρεως σκευασία (E Cod. Paris. B.N. Gr. 2327, Fol. 232R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 286 | auto-corrected |
| fragmenta-alchemica.leu-kwsis-u-datos-di-ou-leukai-netai-oi-konomou-menon | Fragmenta Alchemica - Λεύκωσις ὕδατος, δῑ οὗ λευκαίνεται οἰκονομούμενον τὸ ἀρσενικὸν καὶ ἡ σανδαράχη (E Cod. Paris. B.N. Gr. 2327, Fol. 279V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 66 | auto-corrected |
| fragmenta-alchemica.o-li-qos-th-s-filosofi-as-fort-auctore-zosimo-e-cod | Fragmenta Alchemica - Ὁ λίθος τῆς φιλοσοφίας (Fort. Auctore Zosimo) (E Cod. B.N. Gr. 2327, Fol. 215V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 206 | auto-corrected |
| fragmenta-alchemica.oi-konomi-th-s-sbe-stou-e-cod-venet-marc-299-fol | Fragmenta Alchemica - Οἰκονομία τῆς ἀσβέστου (E Cod. Venet. Marc. 299, Fol. 99V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 126 | raw OCR |
| fragmenta-alchemica.oti-su-nqeton-kai-ou-x-plou-n-ei-dos-kai-ti-s-h | Fragmenta Alchemica - Ὅτι σύνθετον καὶ οὐχ ἁπλοῦν τὸ εἶδος καὶ τίς ἡ οἰκονομία (E Cod. Venet. Marc. 299, Fol. 96R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 787 | auto-corrected |
| fragmenta-alchemica.peri-bafh-s-sidh-rou-e-cod-venet-marc-299-fol-104r | Fragmenta Alchemica - Περὶ βαφῆς σιδήρου (E Cod. Venet. Marc. 299, Fol. 104R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 839 | raw OCR |
| fragmenta-alchemica.peri-leukw-sews-tou-rsenikou-tou-sxistou-e-cod | Fragmenta Alchemica - Περὶ λευκώσεως τοῦ ἀρσενικοῦ τοῦ σχιστοῦ (E Cod. Paris. B.N. Gr. 2327, Fol. 279V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 96 | auto-corrected |
| fragmenta-alchemica.peri-th-s-qei-as-kai-i-era-s-te-xnhs-tw-n-filoso-fwn-e | Fragmenta Alchemica - Περὶ τῆς θείας καὶ ἱερᾶς τέχνης τῶν φιλοσόφων (E Cod. Paris. B.N. Gr. 2327, Fol. 230R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 830 | raw OCR |
| fragmenta-alchemica.peri-th-s-timiwta-ths-kai-polufh-mou-xrusoxoi-kh-s-e-cod | Fragmenta Alchemica - Περὶ τῆς τιμιωτάτης καὶ πολυφήμου χρυσοχοϊκῆς (E Cod. Paris. B.N. Gr. 2327, Fol. 280R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 4,344 | auto-corrected |
| fragmenta-alchemica.peri-tou-li-qou-tw-n-filoso-fwn-e-cod-b-n-gr-2327-fol | Fragmenta Alchemica - Περὶ τοῦ λίθου τῶν φιλοσόφων (E Cod. B.N. Gr. 2327, Fol. 216R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 708 | auto-corrected |
| fragmenta-alchemica.peri-tou-o-reixa-lkou | Fragmenta Alchemica - Περὶ τοῦ ὀρειχάλκου | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 52 | auto-corrected |
| fragmenta-alchemica.peri-tou-poih-sai-o-cuggosa-pounon-e-cod-paris-b-n-gr | Fragmenta Alchemica - Περὶ τοῦ ποιῆσαι ὀξυγγοσάπουνον (E Cod. Paris. B.N. Gr. 2327, Fol. 7V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 98 | auto-corrected |
| fragmenta-alchemica.peri-tou-poih-sai-turo-kollan-e-cod-paris-b-n-gr-2327 | Fragmenta Alchemica - Περὶ τοῦ ποιῆσαι τυρόκολλαν (E Cod. Paris. B.N. Gr. 2327, Fol. 7R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 173 | auto-corrected |
| fragmenta-alchemica.peri-tou-qei-ou-kau-stou-e-cod-paris-b-n-gr-2327 | Fragmenta Alchemica - Περὶ τοῦ θείου ἀκαύστου (E Cod. Paris. B.N. Gr. 2327, Fol. 279R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 77 | raw OCR |
| fragmenta-alchemica.peri-tou-xrusw-sai-si-dhron-e-cod-paris-b-n-gr-2327 | Fragmenta Alchemica - Περὶ τοῦ χρυσῶσαι σίδηρον (E Cod. Paris. B.N. Gr. 2327, Fol. 295R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 323 | auto-corrected |
| fragmenta-alchemica.peri-zu-qwn-poih-sews-e-cod-venet-marc-299-fol-162r | Fragmenta Alchemica - Περὶ ζύθων ποιήσεως (E Cod. Venet. Marc. 299, Fol. 162R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 105 | raw OCR |
| fragmenta-alchemica.po-sos-o-tw-n-baptome-nwn-e-ri-wn-staqmo-s-w-feilen-kai-po-sos-o | Fragmenta Alchemica - Πόσος ὁ τῶν βαπτομένων ἐρίων σταθμὸς ὤφειλεν καὶ πόσος ὁ τῆς κομάρεως καὶ πόσος ὁ τῶν βεβαμμένων ὑδάτων (E Cod. Venet. Marc. 299, Fol. 127V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 88 | auto-corrected |
| fragmenta-alchemica.poi-hsis-krustalli-wn-e-cod-venet-marc-299-fol-116r | Fragmenta Alchemica - Ποίησις κρυσταλλίων (E Cod. Venet. Marc. 299, Fol. 116R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 408 | raw OCR |
| fragmenta-alchemica.poi-hsis-ma-llon-tou-panto-s-e-cod-venet-marc-299-fol | Fragmenta Alchemica - Ποίησις μᾶλλον τοῦ παντός (E Cod. Venet. Marc. 299, Fol. 97R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 516 | raw OCR |
| fragmenta-alchemica.poi-hsis-rgu-rou-e-cod-venet-marc-299-fol-194v | Fragmenta Alchemica - Ποίησις ἀργύρου (E Cod. Venet. Marc. 299, Fol. 194V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 140 | auto-corrected |
| fragmenta-alchemica.poi-hsis-sbe-stou-e-cod-venet-marc-299-fol-99v | Fragmenta Alchemica - Ποίησις ἀσβέστου (E Cod. Venet. Marc. 299, Fol. 99V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 119 | auto-corrected |
| fragmenta-alchemica.skeuasi-froni-trou-tou-zhtoume-nou-ei-s-ta-s-kollh-seis-xrusou | Fragmenta Alchemica - Σκευασία ἀφρονίτρου τοῦ ζητουμένου εἰς τὰς κολλήσεις χρυσοῦ καὶ ἀργύρου καὶ χαλκοῦ (E Cod. Paris. B.N. Gr. 2327, Fol. 232R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 47 | auto-corrected |
| fragmenta-alchemica.sta-kths-poi-hsis-e-cod-venet-marc-299-fol-162v | Fragmenta Alchemica - Στάκτης ποίησις (E Cod. Venet. Marc. 299, Fol. 162V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 286 | auto-corrected |
| fragmenta-alchemica.sumpe-rasma-th-s-poih-sews-e-cod-venet-marc-299-fol | Fragmenta Alchemica - Συμπέρασμα τῆς ποιήσεως (E Cod. Venet. Marc. 299, Fol. 101R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 63 | auto-corrected |
| fragmenta-alchemica.ti-s-h-meta-th-n-i-wsin-oi-konomi-e-cod-venet-marc | Fragmenta Alchemica - Τίς ἡ μετὰ τὴν ἴωσιν οἰκονομία (E Cod. Venet. Marc. 299, Fol. 128R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 77 | auto-corrected |
| fragmenta-alchemica.ti-s-h-th-s-koma-rews-su-nqesis-e-cod-venet-marc-299 | Fragmenta Alchemica - Τίς ἡ τῆς κομάρεως σύνθεσις (E Cod. Venet. Marc. 299, Fol. 128R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 28 | raw OCR |
| fragmenta-alchemica.ti-s-h-tou-me-lanos-chri-ou-kataskeuh-e-cod-venet-marc | Fragmenta Alchemica - Τίς ἡ τοῦ μέλανος ξηρίου κατασκευή (E Cod. Venet. Marc. 299, Fol. 128R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 71 | raw OCR |
| fragmenta-alchemica.ti-s-h-tw-n-rxai-wn-sbestos-e-cod-venet-marc-299 | Fragmenta Alchemica - Τίς ἡ τῶν ἀρχαίων ἄσβεστος (E Cod. Venet. Marc. 299, Fol. 99R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 208 | raw OCR |
| fragmenta-alchemica.xrh-sis-ioustinianou-basile-ws-sine-titulo-e-cod | Fragmenta Alchemica - Χρῆσις Ἰουστινιανοῦ βασιλέως (Sine Titulo) (E Cod. Paris. B.N. Gr. 2327, Fol. 240V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 726 | auto-corrected |
| fragmenta-alchemica.xrusou-poi-hsis-e-cod-paris-b-n-gr-2327-fol-232r | Fragmenta Alchemica - Χρυσοῦ ποίησις (E Cod. Paris. B.N. Gr. 2327, Fol. 232R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 292 | raw OCR |
| fragmentum-stoicum.fragmentum | Fragmentum Stoicum - Fragmentum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20 | auto-corrected |
| fragmentum-synodicae-epistulae-concilii-caesariensis.fragmentum-epistulae | Theophilus Caesariensis et synodus Caesariensis - Fragmentum synodicae epistulae concilii Caesariensis (de paschate) (PG005 loci 694-695) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 54 | raw OCR |
| gaius-suetonius-tranquillus.peri-blasfhmiw-n-kai-po-qen-e-ka-sth | Gaius Suetonius Tranquillus - Περὶ βλασφημιῶν καὶ πόθεν ἑκάστη | qwen36-suetonius_reliquiae_reifferscheid | Qwen3.6-27B | 11,498 | auto-corrected |
| geoponica.geoponica | Geoponica - Geoponica | qwen36-geoponica_beckh | Qwen3.6-27B | 124,636 | auto-corrected |
| georgius-cedrenus.compendium-historiarum | Georgius Cedrenus - Compendium Historiarum | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 291,998 | manual |
| georgius-choeroboscus.peri-tropon-poietikon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,179 | auto-corrected |
| georgius-choeroboscus.prolegomena-et-scholia-in-theodosii-alexandrini-canones-isagogicos-de | Georgius Choeroboscus - Prolegomena Et Scholia In Theodosii Alexandrini Canones Isagogicos De Flexione Nominum | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 143,024 | auto-corrected |
| georgius-diaeretes.scholia-eis-to-peri-eureseos-hermogenous |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,352 | auto-corrected |
| georgius-gemistus-pletho.syntome-peri-tinon-meron-tes-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,891 | auto-corrected |
| georgius-monachus-continuatus.chronicon-continuatio-redactio | Georgius Monachus Continuatus - Chronicon (continuatio) (redactio A) / Vitae imperatorum recentiorum (PG109 loci 417-497) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 29,808 | manual |
| georgius-monachus.chronicon-breve-lib-1-6-redactio-recentior | Georgius Monachus - Chronicon Breve (Lib. 1-6) (Redactio Recentior) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 240,537 | auto-corrected |
| georgius-pachymeres.progymnasmata |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 11,036 | auto-corrected |
| gorgias-rhetoric.fragmenta | Gorgias - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 982 | auto-corrected |
| gorgias-rhetoric.testimonia | Gorgias - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,888 | auto-corrected |
| gregorius-corinthius.exegesis-in-peri-methodou-deinotetos |  | qwen36-walz_rhetores_v7pt2 | Qwen3.6-27B | 61,182 | auto-corrected |
| gregorius-nazianzenus.ad-eos-qui-ipsum-acciverant-nec-occurrerant-orat-3 | Gregorius Nazianzenus - Ad Eos Qui Ipsum Acciverant Nec Occurrerant (Orat. 3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 785 | auto-corrected |
| gregorius-nazianzenus.ad-gregorium-nyssenum-orat-11 | Gregorius Nazianzenus - Ad Gregorium Nyssenum (Orat. 11) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,542 | raw OCR |
| gregorius-nazianzenus.ad-julianum-tributorum-exaequatorem-orat-19 | Gregorius Nazianzenus - Ad Julianum Tributorum Exaequatorem (Orat. 19) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,992 | auto-corrected |
| gregorius-nazianzenus.ad-patrem-orat-12 | Gregorius Nazianzenus - Ad Patrem (Orat. 12) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,198 | auto-corrected |
| gregorius-nazianzenus.apologetica-orat-2 | Gregorius Nazianzenus - Apologetica (Orat. 2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,634 | auto-corrected |
| gregorius-nazianzenus.apologeticus-ad-patrem-orat-9 | Gregorius Nazianzenus - Apologeticus Ad Patrem (Orat. 9) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,207 | auto-corrected |
| gregorius-nazianzenus.carmina-de-se-ipso | Gregorius Nazianzenus - Carmina De Se Ipso | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 43,522 | auto-corrected |
| gregorius-nazianzenus.carmina-dogmatica | Gregorius Nazianzenus - Carmina Dogmatica | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 51,964 | auto-corrected |
| gregorius-nazianzenus.carmina-quae-spectant-ad-alios | Gregorius Nazianzenus - Carmina Quae Spectant Ad Alios | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,109 | auto-corrected |
| gregorius-nazianzenus.contra-arianos-et-de-seipso-orat-33 | Gregorius Nazianzenus - Contra Arianos Et De Seipso (Orat. 33) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,177 | auto-corrected |
| gregorius-nazianzenus.contra-julianum-imperatorem-1-orat-4 | Gregorius Nazianzenus - Contra Julianum Imperatorem 1 (Orat. 4) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 25,381 | auto-corrected |
| gregorius-nazianzenus.de-dogmate-et-constitutione-episcoporum-orat-20 | Gregorius Nazianzenus - De Dogmate Et Constitutione Episcoporum (Orat. 20) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,827 | raw OCR |
| gregorius-nazianzenus.de-martyribus-et-adversus-arianos-orat-35-sp | Gregorius Nazianzenus - De Martyribus Et Adversus Arianos (Orat. 35) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,043 | auto-corrected |
| gregorius-nazianzenus.de-moderatione-in-disputando-orat-32 | Gregorius Nazianzenus - De Moderatione In Disputando (Orat. 32) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,899 | auto-corrected |
| gregorius-nazianzenus.de-pace-1-orat-6 | Gregorius Nazianzenus - De Pace 1 (Orat. 6) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,473 | auto-corrected |
| gregorius-nazianzenus.de-pauperum-amore-orat-14 | Gregorius Nazianzenus - De Pauperum Amore (Orat. 14) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,216 | auto-corrected |
| gregorius-nazianzenus.de-seipso-et-ad-eos-qui-ipsum-cathedram-constantinopolitanam-affectare | Gregorius Nazianzenus - De Seipso Et Ad Eos Qui Ipsum Cathedram Constantinopolitanam Affectare Dicebant (Orat. 36) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,403 | auto-corrected |
| gregorius-nazianzenus.epistulae | Gregorius Nazianzenus - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 39,905 | auto-corrected |
| gregorius-nazianzenus.epistulae-theologicae | Gregorius Nazianzenus - Epistulae Theologicae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,036 | auto-corrected |
| gregorius-nazianzenus.fragmentum-ex-oratione-contra-astronomos-sp | Fragmentum ex oratione contra astronomos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 883 | raw OCR |
| gregorius-nazianzenus.funebris-in-laudem-caesarii-fratris-oratio-orat-7 | Gregorius Nazianzenus - Funebris In Laudem Caesarii Fratris Oratio (Orat. 7) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,608 | auto-corrected |
| gregorius-nazianzenus.funebris-oratio-in-laudem-basilii-magni-caesareae-in-cappadocia | Gregorius Nazianzenus - Funebris Oratio In Laudem Basilii Magni Caesareae In Cappadocia Episcopi (Orat. 43) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,189 | auto-corrected |
| gregorius-nazianzenus.funebris-oratio-in-patrem-orat-18 | Gregorius Nazianzenus - Funebris Oratio In Patrem (Orat. 18) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,324 | auto-corrected |
| gregorius-nazianzenus.in-aegyptiorum-adventum-orat-34 | Gregorius Nazianzenus - In Aegyptiorum Adventum (Orat. 34) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,709 | raw OCR |
| gregorius-nazianzenus.in-consecratione-eulalii-doarensium-episcopi-orat-13 | Gregorius Nazianzenus - In Consecratione Eulalii Doarensium Episcopi (Orat. 13) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 332 | raw OCR |
| gregorius-nazianzenus.in-dictum-evangelii-cum-consummasset-jesus-hos-sermones-orat-37 | Gregorius Nazianzenus - In Dictum Evangelii: Cum Consummasset Jesus Hos Sermones (Orat. 37) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,112 | auto-corrected |
| gregorius-nazianzenus.in-laudem-athanasii-orat-21 | Gregorius Nazianzenus - In Laudem Athanasii (Orat. 21) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,348 | auto-corrected |
| gregorius-nazianzenus.in-laudem-heronis-philosophi-orat-25 | Gregorius Nazianzenus - In Laudem Heronis Philosophi (Orat. 25) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,086 | auto-corrected |
| gregorius-nazianzenus.in-laudem-sororis-gorgoniae-orat-8 | Gregorius Nazianzenus - In Laudem Sororis Gorgoniae (Orat. 8) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,365 | auto-corrected |
| gregorius-nazianzenus.in-machabaeorum-laudem-orat-15 | Gregorius Nazianzenus - In Machabaeorum Laudem (Orat. 15) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,833 | auto-corrected |
| gregorius-nazianzenus.in-novam-dominicam-orat-44 | Gregorius Nazianzenus - In Novam Dominicam (Orat. 44) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,177 | auto-corrected |
| gregorius-nazianzenus.in-patrem-tacentem-orat-16 | Gregorius Nazianzenus - In Patrem Tacentem (Orat. 16) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,364 | auto-corrected |
| gregorius-nazianzenus.in-sancta-lumina-orat-39 | Gregorius Nazianzenus - In Sancta Lumina (Orat. 39) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,596 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-baptisma-orat-40 | Gregorius Nazianzenus - In Sanctum Baptisma (Orat. 40) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,429 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-pascha-et-in-tarditatem-orat-1 | Gregorius Nazianzenus - In Sanctum Pascha Et In Tarditatem (Orat. 1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 882 | auto-corrected |
| gregorius-nazianzenus.in-sanctum-pascha-orat-45 | In sanctum pascha (orat. 45) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,189 | auto-corrected |
| gregorius-nazianzenus.in-seipsum-ad-patrem-et-basilium-magnum-orat-10 | Gregorius Nazianzenus - In Seipsum Ad Patrem Et Basilium Magnum (Orat. 10) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 662 | raw OCR |
| gregorius-nazianzenus.in-seipsum-cum-rure-rediisset-post-ea-quae-maximo-perpetrata | Gregorius Nazianzenus - In Seipsum, Cum Rure Rediisset, Post Ea Quae A Maximo Perpetrata Fuerant (Orat. 26) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,896 | auto-corrected |
| gregorius-nazianzenus.in-theophania-orat-38 | Gregorius Nazianzenus - In Theophania (Orat. 38) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,425 | auto-corrected |
| gregorius-nazianzenus.liturgia-sancti-gregorii-sp | Liturgia sancti Gregorii [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,674 | auto-corrected |
| gregorius-nazianzenus.significatio-in-ezechielem-sp | Significatio in Ezechielem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 521 | auto-corrected |
| gregorius-nazianzenus.supremum-vale-orat-42 | Gregorius Nazianzenus - Supremum Vale (Orat. 42) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,830 | auto-corrected |
| gregorius-nazianzenus.testamentum | Gregorius Nazianzenus - Testamentum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,014 | raw OCR |
| gregorius-nyssenus.ad-ablabium-quod-non-sint-tres-dei | Gregorius Nyssenus - Ad Ablabium Quod Non Sint Tres Dei | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,130 | auto-corrected |
| gregorius-nyssenus.ad-graecos-ex-communibus-notionibus | Gregorius Nyssenus - Ad Graecos Ex Communibus Notionibus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,123 | auto-corrected |
| gregorius-nyssenus.ad-imaginem-dei-et-ad-similitudinem-sp | Gregorius Nyssenus - Ad Imaginem Dei Et Ad Similitudinem [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,252 | auto-corrected |
| gregorius-nyssenus.ad-theophilum-adversus-apollinaristas | Gregorius Nyssenus - Ad Theophilum Adversus Apollinaristas | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,689 | auto-corrected |
| gregorius-nyssenus.adversus-arium-et-sabellium-de-patre-et-filio | Gregorius Nyssenus - Adversus Arium Et Sabellium De Patre Et Filio | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,432 | auto-corrected |
| gregorius-nyssenus.adversus-eos-qui-castigationes-aegre-ferunt | Gregorius Nyssenus - Adversus Eos Qui Castigationes Aegre Ferunt | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,137 | auto-corrected |
| gregorius-nyssenus.adversus-macedonianos-de-spiritu-sancto | Gregorius Nyssenus - Adversus Macedonianos De Spiritu Sancto | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,007 | auto-corrected |
| gregorius-nyssenus.antirrheticus-adversus-apollinarium | Gregorius Nyssenus - Antirrheticus Adversus Apollinarium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 25,016 | auto-corrected |
| gregorius-nyssenus.apologia-in-hexaemeron | Gregorius Nyssenus - Apologia In Hexaemeron | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,190 | auto-corrected |
| gregorius-nyssenus.contra-eunomium | Gregorius Nyssenus - Contra Eunomium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178,664 | auto-corrected |
| gregorius-nyssenus.contra-fatum | Gregorius Nyssenus - Contra Fatum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,707 | auto-corrected |
| gregorius-nyssenus.contra-fornicarios | Gregorius Nyssenus - Contra Fornicarios | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 918 | auto-corrected |
| gregorius-nyssenus.contra-usurarios | Gregorius Nyssenus - Contra Usurarios | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,712 | auto-corrected |
| gregorius-nyssenus.de-anima-sp | Gregorius Nyssenus - De Anima [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,730 | auto-corrected |
| gregorius-nyssenus.de-beneficentia-vulgo-de-pauperibus-amandis-i | Gregorius Nyssenus - De Beneficentia (Vulgo De Pauperibus Amandis I) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,724 | auto-corrected |
| gregorius-nyssenus.de-creatione-hominis-sermo-alter-sp | Gregorius Nyssenus - De Creatione Hominis Sermo Alter [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,294 | auto-corrected |
| gregorius-nyssenus.de-creatione-hominis-sermo-primus-sp | Gregorius Nyssenus - De Creatione Hominis Sermo Primus [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,697 | auto-corrected |
| gregorius-nyssenus.de-deitate-adversus-evagrium-vulgo-in-suam | Gregorius Nyssenus - De Deitate Adversus Evagrium (Vulgo In Suam Ordinationem) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,862 | raw OCR |
| gregorius-nyssenus.de-deitate-filii-et-spiritus-sancti | Gregorius Nyssenus - De Deitate Filii Et Spiritus Sancti | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,744 | auto-corrected |
| gregorius-nyssenus.de-infantibus-praemature-abreptis | Gregorius Nyssenus - De Infantibus Praemature Abreptis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,739 | auto-corrected |
| gregorius-nyssenus.de-instituto-christiano | Gregorius Nyssenus - De Instituto Christiano | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,681 | auto-corrected |
| gregorius-nyssenus.de-mortuis-non-esse-dolendum | Gregorius Nyssenus - De Mortuis Non Esse Dolendum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,028 | auto-corrected |
| gregorius-nyssenus.de-occursu-domini-sp | Gregorius Nyssenus - De Occursu Domini [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,443 | auto-corrected |
| gregorius-nyssenus.de-opificio-hominis | Gregorius Nyssenus - De Opificio Hominis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,801 | auto-corrected |
| gregorius-nyssenus.de-oratione-dominica-orationes-v | Gregorius Nyssenus - De Oratione Dominica Orationes V | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,096 | auto-corrected |
| gregorius-nyssenus.de-perfectione-christiana-ad-olympium-monachum | Gregorius Nyssenus - De Perfectione Christiana Ad Olympium Monachum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,079 | auto-corrected |
| gregorius-nyssenus.de-professione-christiana-ad-harmonium | Gregorius Nyssenus - De Professione Christiana Ad Harmonium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,120 | raw OCR |
| gregorius-nyssenus.de-pythonissa-ad-theodosium-episcopum | Gregorius Nyssenus - De Pythonissa Ad Theodosium Episcopum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 672 | raw OCR |
| gregorius-nyssenus.de-sancto-theodoro | Gregorius Nyssenus - De Sancto Theodoro | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,212 | auto-corrected |
| gregorius-nyssenus.de-spiritu-sancto-sive-in-pentecosten | Gregorius Nyssenus - De Spiritu Sancto Sive In Pentecosten | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,061 | auto-corrected |
| gregorius-nyssenus.de-virginitate | Gregorius Nyssenus - De Virginitate | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 22,317 | auto-corrected |
| gregorius-nyssenus.de-vita-gregorii-thaumaturgi | Gregorius Nyssenus - De Vita Gregorii Thaumaturgi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,024 | auto-corrected |
| gregorius-nyssenus.de-vita-mosis | Gregorius Nyssenus - De Vita Mosis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 28,095 | auto-corrected |
| gregorius-nyssenus.decem-syllogismi-contra-manichaeos-sp | Gregorius Nyssenus - Decem Syllogismi Contra Manichaeos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 229 | raw OCR |
| gregorius-nyssenus.dialogus-de-anima-et-resurrectione | Gregorius Nyssenus - Dialogus De Anima Et Resurrectione | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,844 | auto-corrected |
| gregorius-nyssenus.encomium-in-sanctum-stephanum-protomartyrem-i | Gregorius Nyssenus - Encomium In Sanctum Stephanum Protomartyrem I | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,030 | auto-corrected |
| gregorius-nyssenus.encomium-in-xl-martyres-i | Gregorius Nyssenus - Encomium In Xl Martyres I | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,611 | auto-corrected |
| gregorius-nyssenus.encomium-in-xl-martyres-ii | Gregorius Nyssenus - Encomium In Xl Martyres Ii | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,691 | auto-corrected |
| gregorius-nyssenus.epistula-canonica-ad-letoium | Gregorius Nyssenus - Epistula Canonica Ad Letoium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,070 | auto-corrected |
| gregorius-nyssenus.epistulae | Gregorius Nyssenus - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,181 | auto-corrected |
| gregorius-nyssenus.in-ascensionem-christi | Gregorius Nyssenus - In Ascensionem Christi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,028 | auto-corrected |
| gregorius-nyssenus.in-basilium-fratrem | Gregorius Nyssenus - In Basilium Fratrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,111 | auto-corrected |
| gregorius-nyssenus.in-canticum-canticorum-homiliae-15 | Gregorius Nyssenus - In Canticum Canticorum (Homiliae 15) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 75,182 | auto-corrected |
| gregorius-nyssenus.in-ecclesiasten-homiliae-8 | Gregorius Nyssenus - In Ecclesiasten (Homiliae 8) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,424 | auto-corrected |
| gregorius-nyssenus.in-illud-quatenus-uni-ex-his-fecistis-mihi-fecistis | Gregorius Nyssenus - In Illud: Quatenus Uni Ex His Fecistis Mihi Fecistis (Vulgo De Pauperibus Amandis Ii) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,549 | auto-corrected |
| gregorius-nyssenus.in-illud-tunc-et-ipse-filius | Gregorius Nyssenus - In Illud: Tunc Et Ipse Filius | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,800 | auto-corrected |
| gregorius-nyssenus.in-inscriptiones-psalmorum | Gregorius Nyssenus - In Inscriptiones Psalmorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 39,897 | auto-corrected |
| gregorius-nyssenus.in-luciferam-sanctam-domini-resurrectionem-vulgo-in | Gregorius Nyssenus - In Luciferam Sanctam Domini Resurrectionem (Vulgo In Christi Resurrectionem Oratio V) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,229 | raw OCR |
| gregorius-nyssenus.in-sanctum-ephraim | Gregorius Nyssenus - In Sanctum Ephraim | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,458 | auto-corrected |
| gregorius-nyssenus.in-sanctum-et-salutare-pascha-vulgo-in-christi | Gregorius Nyssenus - In Sanctum Et Salutare Pascha (Vulgo In Christi Resurrectionem Oratio Iv) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 389 | auto-corrected |
| gregorius-nyssenus.in-sanctum-pascha-vulgo-in-christi-resurrectionem-oratio | Gregorius Nyssenus - In Sanctum Pascha (Vulgo In Christi Resurrectionem Oratio Iii) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,794 | auto-corrected |
| gregorius-nyssenus.oratio-catechetica-magna | Gregorius Nyssenus - Oratio Catechetica Magna | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,627 | auto-corrected |
| gregorius-nyssenus.oratio-consolatoria-in-pulcheriam | Gregorius Nyssenus - Oratio Consolatoria In Pulcheriam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,800 | auto-corrected |
| gregorius-nyssenus.oratio-funebris-in-flacillam-imperatricem | Gregorius Nyssenus - Oratio Funebris In Flacillam Imperatricem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,868 | auto-corrected |
| gregorius-nyssenus.oratio-funebris-in-meletium-episcopum | Gregorius Nyssenus - Oratio Funebris In Meletium Episcopum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,343 | auto-corrected |
| gregorius-nyssenus.oratio-in-diem-natalem-christi | Gregorius Nyssenus - Oratio In Diem Natalem Christi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,809 | auto-corrected |
| gregorius-nyssenus.orationes-viii-de-beatitudinibus | Gregorius Nyssenus - Orationes Viii De Beatitudinibus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,619 | auto-corrected |
| gregorius-nyssenus.testimonia-adversus-judaeos-sp | Gregorius Nyssenus - Testimonia Adversus Judaeos [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,087 | auto-corrected |
| gregorius-nyssenus.vita-sanctae-macrinae | Gregorius Nyssenus - Vita Sanctae Macrinae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,592 | auto-corrected |
| gregorius-palamas.confessio-fidei | Gregorius Palamas - Confessio fidei (PG151 loci 389-391, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,547 | manual |
| gregorius-palamas.homiliae | Gregorius Palamas - Homiliae (PG151 loci 10-282) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 118,734 | manual |
| hecataeus-abderita.testimonia-2 | Hecataeus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,190 | auto-corrected |
| hegemon-parodius.fragmentum | Hegemon - Fragmentum | kock-caf1-ocr-frag | Qwen3.6-27B | 119 | raw OCR |
| hegesippus-scr-eccl.fragmenta-ex-incerto-libro | Hegesippus - Fragmenta (ex incerto libro / Hypomnemata) (PG005 loci 663-673) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,511 | auto-corrected |
| hegesippus.fragmenta | HEGESIPPUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 164 | raw OCR |
| heliodorus.fragmenta | Fragmenta | qwen36-staphylus_fhg4 | Qwen3.6-27B | 157 | raw OCR |
| hellanicus.fragmenta | Hellanicus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 981 | auto-corrected |
| heniochus.fragmenta | Heniochus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 76 | raw OCR |
| heraclides-comedy.fragmentum | Heraclides - Fragmentum | [Kock, Comicorum Atticorum Fragmenta II](https://archive.org/search?query=Comicorum+Atticorum+Fragmenta+Kock) | Qwen3.6-27B | 130 | raw OCR |
| heraclides-ponticus-junior-grammar.fragmenta | Heraclides Ponticus Junior - Fragmenta | qwen36-aelian_heraclid_tauchnitz_1829 | Qwen3.6-27B | 57,798 | auto-corrected |
| heraclitus-philosophy.testimonia | Heraclitus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 15,745 | auto-corrected |
| herillus.fragmenta | Herillus - Fragmenta | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 219 | raw OCR |
| hermes.ai-nigma-tou-filosofikou-li-qou-ermou-kai-agaqodai-monos | Hermes - Αἴνιγμα τοῦ φιλοσοφικοῦ λίθου Ἑρμοῦ καὶ Ἀγαθοδαίμονος (E Cod. Paris. B.N. Gr. 2327, Fol. 234R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 57 | raw OCR |
| hermesianax.fragmenta | Fragmenta | qwen36-philetas_bach_1829-ocr | Qwen3.6-27B | 6,546 | auto-corrected |
| hermias-apologetics.irrisio-gentilium-philosophorum | Hermias - Irrisio gentilium philosophorum (PG006 loci 592-597) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,818 | auto-corrected |
| hermias-history.fragmenta | Hermias - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 515 | auto-corrected |
| hermippus-comedy.fragmenta | Hermippus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 1,960 | auto-corrected |
| hermippus-comedy.fragmenta-4 | Hermippus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 310 | raw OCR |
| herodas.mimiambi | Herodas - Mimiambi | [Herodas, ed. Headlam-Knox](https://archive.org/details/herodasmimesfrag00hero) | Qwen3.6-27B | 2,846 | auto-corrected |
| heron.definitiones | Heron - Definitiones | qwen36-heron_definitiones_teubner4 | Qwen3.6-27B | 56,184 | auto-corrected |
| heron.geometrica | HERO ALEXANDRINUS - Geometrica | qwen36-heron-heiberg-v4 | Qwen3.6-27B | 47,029 | raw OCR |
| hesiodus.fragmenta | Hesiodus - Fragmenta | qwen36-hesiod_rzach-ocr | Qwen3.6-27B | 16,011 | auto-corrected |
| hesychius-lexicography.epistula-ad-eulogium | Hesychius - Epistula Ad Eulogium | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 577 | raw OCR |
| hesychius-lexicography.lexicon-o | Hesychius - Lexicon (Α-Ο) | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 150,437 | auto-corrected |
| hesychius-lexicography.lexicon-p-w | Hesychius - Lexicon (Π-Ω) | [archive.org](https://archive.org/details/hesychiialexand00schmgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 58,547 | auto-corrected |
| hexapla-anonymi.lectiones |  | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 1,837 | auto-corrected |
| hicetas.testimonia | Hicetas - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 34 | raw OCR |
| hierocles-grammaticus.synecdemus | Hierocles Grammaticus - Synecdemus (PG113 loci 82-89) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,600 | manual |
| hierocles-philosophy.hqikh-stoixei-wsis | Hierocles - Ἠθικὴ στοιχείωσις | qwen36-hierocl_aureum_mullach_fpg1 | Qwen3.6-27B | 139,938 | auto-corrected |
| hieronymus.fragmenta | Fragmenta | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 542 | auto-corrected |
| hierotheus-alchemy.ieroqe-ou-peri-th-s-i-era-s-te-xnhs-e-cod-paris-b-n-gr | Hierotheus - Ἱεροθέου περὶ τῆς ἱερᾶς τέχνης (E Cod. Paris. B.N. Gr. 2249, Fol. 94R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 372 | auto-corrected |
| hilarion-monachus.oratio-dialectica-de-pane-mystico | Hilarion monachus - Logos dialektikos / Oratio dialectica de pane mystico Graecorum et azymo Latinorum (PG158 loci 524-527) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,414 | manual |
| himerius.declamationes-et-orationes | Himerius - Declamationes Et Orationes | qwen36-himerius_dubner_didot | Qwen3.6-27B | 257,196 | auto-corrected |
| hipparchus-comedy.fragmenta | Hipparchus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 216 | raw OCR |
| hipparchus-philosophy.fragmentum | Hipparchus - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 634 | auto-corrected |
| hippasus.testimonia | Hippasus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,786 | raw OCR |
| hippias-soph.testimonia-2 | Hippias - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,920 | auto-corrected |
| hippiatrica.appendices-ad-hippiatrica-berolinensia | Appendices ad Hippiatrica Berolinensia | [Oder-Hoppe, Corpus Hippiatricorum Graecorum vol. 1 (Berolinensia), Teubner 1924](https://digital.slub-dresden.de/werkansicht/dlf/303101) | Qwen3.6-27B | 2,800 | auto-corrected |
| hippiatrica.hippiatrica-berolinensia | Hippiatrica Berolinensia | [Oder-Hoppe, Corpus Hippiatricorum Graecorum vol. 1 (Berolinensia), Teubner 1924](https://digital.slub-dresden.de/werkansicht/dlf/303101) | Qwen3.6-27B | 94,957 | auto-corrected |
| hippocrates.testimonia | Hippocrates - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,425 | auto-corrected |
| hippodamus.fragmenta-sp | Hippodamus - Fragmenta [Sp.] | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,677 | auto-corrected |
| hippon.testimonia | Hippon - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,993 | auto-corrected |
| horapollo.hieroglyphica-translatio-philippi | Horapollo - Hieroglyphica (Translatio Philippi) | qwen36-horapollo_leemans | Qwen3.6-27B | 17,898 | auto-corrected |
| hyperochus.fragmenta | Hyperochus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 83 | raw OCR |
| ibycus.fragmenta | IBYCUS - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 1,628 | auto-corrected |
| iccus.testimonia | Iccus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 611 | raw OCR |
| idaeus-philosophy.testimonium | Idaeus - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 765 | auto-corrected |
| ignatius-scr-eccl.fragmenta-ex-epistolis | Ignatius Antiochenus - Fragmenta ex epistolis (excerpts quoted in later writers; PG 5 fragment section) (PG005 loci 483-489) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,281 | manual |
| ilias-parva.ilias-parva-fragmenta | Ilias Parva - Ilias Parva (Fragmenta) | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 1,894 | auto-corrected |
| iliu-persis.iliu-persis-fragmenta | Iliu Persis - Iliu Persis (Fragmenta) | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 379 | auto-corrected |
| ion-philosophy.fragmenta | Ion - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 1,898 | auto-corrected |
| ion-philosophy.testimonia-2 | Ion - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,313 | auto-corrected |
| iophon.fragmenta | Iophon - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 285 | auto-corrected |
| isidorus-scholasticus-anthol-didot |  | qwen36-isidorus_scholasticus_anthol_didot | Qwen3.6-27B | 105,423 | auto-corrected |
| isidorus-thessalonicensis.sermones-in-deiparam | Isidorus Thessalonicensis - Sermones in Deiparam (PG139 loci 13-89) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 24,029 | manual |
| isyllus.fragmenta-ig-4-950 | Isyllus - Fragmenta (Ig 4.950) | ig-iv-950-fraenkel-1902-diplomatic | Qwen3.6-27B | 75 | raw OCR |
| jacobs-anthologia-graeca-t13.appendix-epigrammatum | Appendix epigrammatum (ed. Jacobs) | qwen36-claudianus_epigr_anthologia_graeca | Qwen3.6-27B | 17,153 | auto-corrected |
| joannes-archiereus.iwa-nnou-rxiere-ws-tou-e-n-ebeigi-peri-th-s-qei-as-te-xnhs | Joannes Archiereus - Ἰωάννου ἀρχιερέως τοῦ ἐν Ἐβειγίᾳ περὶ τῆς θείας τέχνης (E Cod. Paris. B.N. Gr. 2327, Fol. 243R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,261 | raw OCR |
| joannes-argyropulus.de-processione-spiritus-sancti-ad-magnum-ducem | Joannes Argyropulus - De processione Spiritus Sancti ad magnum ducem (Lucam Notaram), cum explanatione decreti synodi Florentinae (PG158 loci 531-539) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,552 | manual |
| joannes-cameniates.de-expugnatione-thessalonicae | Joannes Cameniates - De expugnatione Thessalonicae (PG109 loci 268-324) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 22,490 | manual |
| joannes-chrysostomus.ad-demetrium-de-compunctione-lib-1 | Joannes Chrysostomus - Ad Demetrium De Compunctione (Lib. 1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,512 | auto-corrected |
| joannes-chrysostomus.ad-eos-qui-scandalizati-sunt | Joannes Chrysostomus - Ad Eos Qui Scandalizati Sunt | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,044 | auto-corrected |
| joannes-chrysostomus.ad-illuminandos-catecheses-1-2-series-prima-et-secunda | Joannes Chrysostomus - Ad Illuminandos Catecheses 1-2 (Series Prima Et Secunda) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,937 | auto-corrected |
| joannes-chrysostomus.ad-populum-antiochenum-homiliae-1-21 | Joannes Chrysostomus - Ad Populum Antiochenum (Homiliae 1-21) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 90,964 | auto-corrected |
| joannes-chrysostomus.ad-stagirium-daemone-vexatum-lib-1-3 | Joannes Chrysostomus - Ad Stagirium A Daemone Vexatum (Lib. 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 32,026 | auto-corrected |
| joannes-chrysostomus.ad-stelechium-de-compunctione-lib-2 | Joannes Chrysostomus - Ad Stelechium De Compunctione (Lib. 2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,597 | auto-corrected |
| joannes-chrysostomus.ad-theodorum-lapsum-lib-1 | Joannes Chrysostomus - Ad Theodorum Lapsum (Lib. 1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,865 | auto-corrected |
| joannes-chrysostomus.ad-theodorum-lapsum-lib-2-epistula-ad-theodorum | Joannes Chrysostomus - Ad Theodorum Lapsum (Lib. 2) (= Epistula Ad Theodorum Monachum) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,021 | auto-corrected |
| joannes-chrysostomus.ad-viduam-juniorem | Joannes Chrysostomus - Ad Viduam Juniorem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,184 | auto-corrected |
| joannes-chrysostomus.adversus-ebriosos-et-de-resurrectione-domini-nostri-jesu-christi | Joannes Chrysostomus - Adversus Ebriosos Et De Resurrectione Domini Nostri Jesu Christi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,972 | auto-corrected |
| joannes-chrysostomus.adversus-judaeos-orationes-1-8 | Joannes Chrysostomus - Adversus Judaeos (Orationes 1-8) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 43,094 | auto-corrected |
| joannes-chrysostomus.adversus-oppugnatores-vitae-monasticae-lib-1-3 | Joannes Chrysostomus - Adversus Oppugnatores Vitae Monasticae (Lib. 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,122 | auto-corrected |
| joannes-chrysostomus.ascetam-facetiis-uti-non-debere-sp | Joannes Chrysostomus - Ascetam Facetiis Uti Non Debere [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,108 | auto-corrected |
| joannes-chrysostomus.commentarius-in-job | Joannes Chrysostomus - Commentarius In Job | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 26,820 | auto-corrected |
| joannes-chrysostomus.comparatio-regis-et-monachi-dub | Joannes Chrysostomus - Comparatio Regis Et Monachi [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,198 | auto-corrected |
| joannes-chrysostomus.contra-anomoeos-homilia-11 | Contra Anomoeos (homilia 11) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,096 | auto-corrected |
| joannes-chrysostomus.contra-eos-qui-subintroductas-habent-virgines | Joannes Chrysostomus - Contra Eos Qui Subintroductas Habent Virgines | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,403 | auto-corrected |
| joannes-chrysostomus.contra-judaeos-gentiles-et-haereticos-et-in-illud-vocatus-est-jesus | Joannes Chrysostomus - Contra Judaeos, Gentiles Et Haereticos Et In Illud: Vocatus Est Jesus Ad Nuptias [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,636 | auto-corrected |
| joannes-chrysostomus.contra-ludos-et-theatra | Joannes Chrysostomus - Contra Ludos Et Theatra | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,101 | auto-corrected |
| joannes-chrysostomus.de-anna-sermones-1-5 | Joannes Chrysostomus - De Anna (Sermones 1-5) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 24,330 | auto-corrected |
| joannes-chrysostomus.de-babyla-contra-julianum-et-gentiles | Joannes Chrysostomus - De Babyla Contra Julianum Et Gentiles | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,509 | auto-corrected |
| joannes-chrysostomus.de-beato-abraham-sp | Joannes Chrysostomus - De Beato Abraham [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,542 | auto-corrected |
| joannes-chrysostomus.de-chananaea-dub | Joannes Chrysostomus - De Chananaea [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,333 | auto-corrected |
| joannes-chrysostomus.de-christi-divinitate-contra-anomoeos-homilia-12 | De Christi divinitate (%6 Contra Anomoeos, homilia 12) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,649 | auto-corrected |
| joannes-chrysostomus.de-christi-precibus-contra-anomoeos-homilia-10 | De Christi precibus (%6 Contra Anomoeos, homilia 10) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,345 | auto-corrected |
| joannes-chrysostomus.de-coemeterio-et-de-cruce | Joannes Chrysostomus - De Coemeterio Et De Cruce | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,940 | auto-corrected |
| joannes-chrysostomus.de-confessione-pretiosae-crucis-sp | Joannes Chrysostomus - De Confessione Pretiosae Crucis [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,861 | auto-corrected |
| joannes-chrysostomus.de-davide-et-saule-homiliae-1-3 | Joannes Chrysostomus - De Davide Et Saule (Homiliae 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,762 | auto-corrected |
| joannes-chrysostomus.de-decem-millium-talentorum-debitore | Joannes Chrysostomus - De Decem Millium Talentorum Debitore | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,703 | auto-corrected |
| joannes-chrysostomus.de-eleemosyna | Joannes Chrysostomus - De Eleemosyna | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,195 | auto-corrected |
| joannes-chrysostomus.de-fato-et-providentia-orationes-1-6 | Joannes Chrysostomus - De Fato Et Providentia (Orationes 1-6) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,078 | auto-corrected |
| joannes-chrysostomus.de-fugienda-simulata-specie-sp | Joannes Chrysostomus - De Fugienda Simulata Specie [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 837 | auto-corrected |
| joannes-chrysostomus.de-laudibus-sancti-pauli-apostoli-homiliae-1-7 | Joannes Chrysostomus - De Laudibus Sancti Pauli Apostoli (Homiliae 1-7) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,893 | auto-corrected |
| joannes-chrysostomus.de-lazaro-homiliae-1-7 | Joannes Chrysostomus - De Lazaro (Homiliae 1-7) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,586 | auto-corrected |
| joannes-chrysostomus.de-libello-repudii | Joannes Chrysostomus - De Libello Repudii | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,685 | auto-corrected |
| joannes-chrysostomus.de-maccabeis-homiliae-1-3 | Joannes Chrysostomus - De Maccabeis (Homiliae 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,671 | auto-corrected |
| joannes-chrysostomus.de-melchisedech-sp | Joannes Chrysostomus - De Melchisedech [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,849 | raw OCR |
| joannes-chrysostomus.de-non-iterando-conjugio | Joannes Chrysostomus - De Non Iterando Conjugio | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,816 | auto-corrected |
| joannes-chrysostomus.de-occursu-domini-de-deipara-et-symeone-sp | Joannes Chrysostomus - De Occursu Domini, De Deipara Et Symeone [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,014 | auto-corrected |
| joannes-chrysostomus.de-paenitentia-homiliae-1-9 | Joannes Chrysostomus - De Paenitentia (Homiliae 1-9) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 37,560 | auto-corrected |
| joannes-chrysostomus.de-perfecta-caritate-sp | Joannes Chrysostomus - De Perfecta Caritate [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,855 | auto-corrected |
| joannes-chrysostomus.de-precatione-orat-1-2-sp | Joannes Chrysostomus - De Precatione (Orat. 1-2) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,900 | auto-corrected |
| joannes-chrysostomus.de-proditione-judae-homiliae-1-2 | Joannes Chrysostomus - De Proditione Judae (Homiliae 1-2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,746 | auto-corrected |
| joannes-chrysostomus.de-profectu-evangelii | Joannes Chrysostomus - De Profectu Evangelii | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,337 | auto-corrected |
| joannes-chrysostomus.de-resurrectione-mortuorum | Joannes Chrysostomus - De Resurrectione Mortuorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,435 | auto-corrected |
| joannes-chrysostomus.de-sacerdotio-lib-1-6 | Joannes Chrysostomus - De Sacerdotio (Lib. 1-6) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 31,674 | auto-corrected |
| joannes-chrysostomus.de-sacerdotio-lib-7-sp | Joannes Chrysostomus - De Sacerdotio (Lib. 7) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,695 | auto-corrected |
| joannes-chrysostomus.de-sancta-droside-martyre | Joannes Chrysostomus - De Sancta Droside Martyre | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,844 | auto-corrected |
| joannes-chrysostomus.de-sancta-pelagia-virgine-et-martyre | Joannes Chrysostomus - De Sancta Pelagia Virgine Et Martyre | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,435 | raw OCR |
| joannes-chrysostomus.de-sancta-pentecoste-homiliae-1-2 | Joannes Chrysostomus - De Sancta Pentecoste (Homiliae 1-2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,821 | auto-corrected |
| joannes-chrysostomus.de-sancta-thecla-martyre-sp | Joannes Chrysostomus - De Sancta Thecla Martyre [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,013 | raw OCR |
| joannes-chrysostomus.de-sancta-trinitate-sp | Joannes Chrysostomus - De Sancta Trinitate [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,448 | auto-corrected |
| joannes-chrysostomus.de-sanctis-bernice-et-prosdoce | Joannes Chrysostomus - De Sanctis Bernice Et Prosdoce | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,143 | auto-corrected |
| joannes-chrysostomus.de-sancto-hieromartyre-babyla | Joannes Chrysostomus - De Sancto Hieromartyre Babyla | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,781 | raw OCR |
| joannes-chrysostomus.de-sancto-hieromartyre-phoca | Joannes Chrysostomus - De Sancto Hieromartyre Phoca | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,304 | auto-corrected |
| joannes-chrysostomus.de-sancto-meletio-antiocheno | Joannes Chrysostomus - De Sancto Meletio Antiocheno | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,714 | auto-corrected |
| joannes-chrysostomus.de-terrae-motu | Joannes Chrysostomus - De Terrae Motu | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 856 | auto-corrected |
| joannes-chrysostomus.de-virginitate | Joannes Chrysostomus - De Virginitate | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 29,611 | auto-corrected |
| joannes-chrysostomus.eclogae-ixlviii-ex-diversis-homiliis-sp | Joannes Chrysostomus - Eclogae I-Xlviii Ex Diversis Homiliis [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 152,854 | auto-corrected |
| joannes-chrysostomus.epistula-ad-caesarium-sp | Joannes Chrysostomus - Epistula Ad Caesarium [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 517 | auto-corrected |
| joannes-chrysostomus.epistula-ad-cyriacum-epist-125-recensiones | Joannes Chrysostomus - Epistula Ad Cyriacum (Epist. 125 + Recensiones) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,869 | auto-corrected |
| joannes-chrysostomus.epistula-ad-episcopos-presbyteros-et-diaconos | Joannes Chrysostomus - Epistula Ad Episcopos, Presbyteros Et Diaconos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,448 | auto-corrected |
| joannes-chrysostomus.epistulae-18-242 | Joannes Chrysostomus - Epistulae 18-242 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,036 | auto-corrected |
| joannes-chrysostomus.epistulae-ad-olympiadem-epist-1-17 | Joannes Chrysostomus - Epistulae Ad Olympiadem (Epist. 1-17) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 48,926 | auto-corrected |
| joannes-chrysostomus.expositiones-in-psalmos | Joannes Chrysostomus - Expositiones In Psalmos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 198,129 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-epistulas-catholicas | Joannes Chrysostomus - Fragmenta In Epistulas Catholicas | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,774 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-jeremiam-in-catenis | Joannes Chrysostomus - Fragmenta In Jeremiam (In Catenis) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 50,737 | auto-corrected |
| joannes-chrysostomus.fragmenta-in-proverbia-in-catenis | Joannes Chrysostomus - Fragmenta In Proverbia (In Catenis) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,478 | auto-corrected |
| joannes-chrysostomus.homilia-dicta-in-templo-sanctae-anastasiae | Joannes Chrysostomus - Homilia Dicta In Templo Sanctae Anastasiae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,946 | auto-corrected |
| joannes-chrysostomus.homilia-dicta-postquam-reliquiae-martyrum | Joannes Chrysostomus - Homilia Dicta Postquam Reliquiae Martyrum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,897 | auto-corrected |
| joannes-chrysostomus.homilia-habita-postquam-presbyter-gothus-concionatus-fuerat | Joannes Chrysostomus - Homilia Habita Postquam Presbyter Gothus Concionatus Fuerat | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,438 | auto-corrected |
| joannes-chrysostomus.homilia-in-martyres | Joannes Chrysostomus - Homilia In Martyres | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,503 | auto-corrected |
| joannes-chrysostomus.in-acta-apostolorum-homiliae-1-55 | Joannes Chrysostomus - In Acta Apostolorum (Homiliae 1-55) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 169,228 | auto-corrected |
| joannes-chrysostomus.in-annuntiationem-beatae-virginis-sp | Joannes Chrysostomus - In Annuntiationem Beatae Virginis [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,080 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-domini-nostri-jesu-christi | Joannes Chrysostomus - In Ascensionem Domini Nostri Jesu Christi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,601 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-sermo-1-sp | Joannes Chrysostomus - In Ascensionem (Sermo 1) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 321 | raw OCR |
| joannes-chrysostomus.in-ascensionem-sermo-2-sp | Joannes Chrysostomus - In Ascensionem (Sermo 2) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,135 | auto-corrected |
| joannes-chrysostomus.in-ascensionem-sermo-3-sp | Joannes Chrysostomus - In Ascensionem (Sermo 3) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,025 | auto-corrected |
| joannes-chrysostomus.in-dictum-pauli-nolo-vos-ignorare | Joannes Chrysostomus - In Dictum Pauli: Nolo Vos Ignorare | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,447 | auto-corrected |
| joannes-chrysostomus.in-dictum-pauli-oportet-haereses-esse | Joannes Chrysostomus - In Dictum Pauli: Oportet Haereses Esse | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,740 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-ephesios-homiliae-1-24 | Joannes Chrysostomus - In Epistulam Ad Ephesios (Homiliae 1-24) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 72,934 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-galatas-commentarius | Joannes Chrysostomus - In Epistulam Ad Galatas Commentarius | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 100,091 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-hebraeos-homiliae-1-34 | Joannes Chrysostomus - In Epistulam Ad Hebraeos (Homiliae 1-34) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 99,169 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-philemonem-homiliae-1-3 | Joannes Chrysostomus - In Epistulam Ad Philemonem (Homiliae 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 41,554 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-philippenses-homiliae-1-15 | Joannes Chrysostomus - In Epistulam Ad Philippenses (Homiliae 1-15) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 50,248 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-romanos-homiliae-1-32 | Joannes Chrysostomus - In Epistulam Ad Romanos (Homiliae 1-32) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 192,110 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ad-titum-homiliae-1-6 | Joannes Chrysostomus - In Epistulam Ad Titum (Homiliae 1-6) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 16,323 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-corinthios-homiliae-1-44 | Joannes Chrysostomus - In Epistulam I Ad Corinthios (Homiliae 1-44) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 169,261 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-thessalonicenses-homiliae-1-11 | Joannes Chrysostomus - In Epistulam I Ad Thessalonicenses (Homiliae 1-11) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 33,980 | auto-corrected |
| joannes-chrysostomus.in-epistulam-i-ad-timotheum-homiliae-1-18 | Joannes Chrysostomus - In Epistulam I Ad Timotheum (Homiliae 1-18) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 51,667 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-corinthios-homiliae-1-30 | Joannes Chrysostomus - In Epistulam Ii Ad Corinthios (Homiliae 1-30) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 94,961 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-thessalonicenses-homiliae-1-5 | Joannes Chrysostomus - In Epistulam Ii Ad Thessalonicenses (Homiliae 1-5) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 15,026 | auto-corrected |
| joannes-chrysostomus.in-epistulam-ii-ad-timotheum-homiliae-1-10 | Joannes Chrysostomus - In Epistulam Ii Ad Timotheum (Homiliae 1-10) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,561 | auto-corrected |
| joannes-chrysostomus.in-eutropium | Joannes Chrysostomus - In Eutropium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 11,854 | auto-corrected |
| joannes-chrysostomus.in-genesim-homiliae-1-67 | Joannes Chrysostomus - In Genesim (Homiliae 1-67) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 265,963 | auto-corrected |
| joannes-chrysostomus.in-genesim-sermones-1-9 | Joannes Chrysostomus - In Genesim (Sermones 1-9) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,945 | auto-corrected |
| joannes-chrysostomus.in-heliam-et-viduam | Joannes Chrysostomus - In Heliam Et Viduam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,983 | auto-corrected |
| joannes-chrysostomus.in-illud-filius-ex-se-nihil-facit | Joannes Chrysostomus - In Illud: Filius Ex Se Nihil Facit | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,410 | auto-corrected |
| joannes-chrysostomus.in-illud-habentes-eundem-spiritum-homiliae-1-3 | Joannes Chrysostomus - In Illud: Habentes Eundem Spiritum (Homiliae 1-3) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,663 | auto-corrected |
| joannes-chrysostomus.in-illud-hoc-scitote-quod-in-novissimis-diebus | Joannes Chrysostomus - In Illud: Hoc Scitote Quod In Novissimis Diebus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,650 | auto-corrected |
| joannes-chrysostomus.in-illud-in-faciem-ei-restiti | Joannes Chrysostomus - In Illud: In Faciem Ei Restiti | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 948 | raw OCR |
| joannes-chrysostomus.in-illud-isaiae-ego-dominus-deus-feci-lumen | Joannes Chrysostomus - In Illud Isaiae: Ego Dominus Deus Feci Lumen | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 21,362 | auto-corrected |
| joannes-chrysostomus.in-illud-ne-timueritis-cum-dives-factus-fuerit-homo | Joannes Chrysostomus - In Illud: Ne Timueritis Cum Dives Factus Fuerit Homo (Homiliae 1-2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,289 | auto-corrected |
| joannes-chrysostomus.in-illud-pater-meus-usque-modo-operatur | Joannes Chrysostomus - In Illud: Pater Meus Usque Modo Operatur | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,582 | auto-corrected |
| joannes-chrysostomus.in-illud-pater-si-possibile-est-transeat | Joannes Chrysostomus - In Illud: Pater, Si Possibile Est, Transeat | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,601 | auto-corrected |
| joannes-chrysostomus.in-illud-propter-fornicationes-autem-unusquisque-suam-uxorem | Joannes Chrysostomus - In Illud: Propter Fornicationes Autem Unusquisque Suam Uxorem Habeat | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,895 | auto-corrected |
| joannes-chrysostomus.in-illud-salutate-priscillam-et-aquilam-sermones-1-2 | Joannes Chrysostomus - In Illud: Salutate Priscillam Et Aquilam (Sermones 1-2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,750 | auto-corrected |
| joannes-chrysostomus.in-illud-si-esurierit-inimicus | Joannes Chrysostomus - In Illud: Si Esurierit Inimicus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,468 | auto-corrected |
| joannes-chrysostomus.in-illud-utinam-sustineretis-modicum | Joannes Chrysostomus - In Illud: Utinam Sustineretis Modicum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,069 | auto-corrected |
| joannes-chrysostomus.in-illud-vidi-dominum-homiliae-1-6 | Joannes Chrysostomus - In Illud: Vidi Dominum (Homiliae 1-6) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 19,875 | auto-corrected |
| joannes-chrysostomus.in-illud-vidua-eligatur | Joannes Chrysostomus - In Illud: Vidua Eligatur | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,298 | auto-corrected |
| joannes-chrysostomus.in-isaiam | Joannes Chrysostomus - In Isaiam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 37,111 | auto-corrected |
| joannes-chrysostomus.in-joannem-homiliae-1-88 | Joannes Chrysostomus - In Joannem (Homiliae 1-88) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 215,521 | auto-corrected |
| joannes-chrysostomus.in-martyres-aegyptios | Joannes Chrysostomus - In Martyres Aegyptios | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,973 | auto-corrected |
| joannes-chrysostomus.in-matthaeum-homiliae-1-90 | Joannes Chrysostomus - In Matthaeum (Homiliae 1-90) | qwen36-pg57 | Qwen3.6-27B | 322,179 | manual |
| joannes-chrysostomus.in-novam-dominicam-et-in-apostolum-thomam-sp | Joannes Chrysostomus - In Novam Dominicam Et In Apostolum Thomam [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,562 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-1-sp | Joannes Chrysostomus - In Pentecosten (Sermo 1) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,567 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-2-sp | Joannes Chrysostomus - In Pentecosten (Sermo 2) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,021 | auto-corrected |
| joannes-chrysostomus.in-pentecosten-sermo-3-sp | Joannes Chrysostomus - In Pentecosten (Sermo 3) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,807 | auto-corrected |
| joannes-chrysostomus.in-principium-actorum-homiliae-1-4 | Joannes Chrysostomus - In Principium Actorum (Homiliae 1-4) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 43,405 | auto-corrected |
| joannes-chrysostomus.in-psalmos-101-107-sp | Joannes Chrysostomus - In Psalmos 101-107 [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 38,993 | auto-corrected |
| joannes-chrysostomus.in-psalmum-100-sp | Joannes Chrysostomus - In Psalmum 100 [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,989 | auto-corrected |
| joannes-chrysostomus.in-psalmum-118-homiliae-1-3-sp | Joannes Chrysostomus - In Psalmum 118 (Homiliae 1-3) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,014 | auto-corrected |
| joannes-chrysostomus.in-psalmum-139-sp | Joannes Chrysostomus - In Psalmum 139 [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,998 | auto-corrected |
| joannes-chrysostomus.in-psalmum-145 | Joannes Chrysostomus - In Psalmum 145 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,610 | auto-corrected |
| joannes-chrysostomus.in-quatriduanum-lazarum | Joannes Chrysostomus - In Quatriduanum Lazarum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,611 | auto-corrected |
| joannes-chrysostomus.in-quatriduanum-lazarum-contra-anomoeos-homilia-9-sp | In quatriduanum Lazarum (%6 Contra Anomoeos, homilia 9) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,340 | auto-corrected |
| joannes-chrysostomus.in-sanctos-petrum-et-heliam-sp | Joannes Chrysostomus - In Sanctos Petrum Et Heliam [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,717 | auto-corrected |
| joannes-chrysostomus.in-sanctum-barlaam-martyrem | Joannes Chrysostomus - In Sanctum Barlaam Martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,952 | auto-corrected |
| joannes-chrysostomus.in-sanctum-eustathium-antiochenum | Joannes Chrysostomus - In Sanctum Eustathium Antiochenum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,152 | auto-corrected |
| joannes-chrysostomus.in-sanctum-ignatium-martyrem | Joannes Chrysostomus - In Sanctum Ignatium Martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,840 | auto-corrected |
| joannes-chrysostomus.in-sanctum-julianum-martyrem | Joannes Chrysostomus - In Sanctum Julianum Martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,939 | auto-corrected |
| joannes-chrysostomus.in-sanctum-lucianum-martyrem | Joannes Chrysostomus - In Sanctum Lucianum Martyrem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,519 | auto-corrected |
| joannes-chrysostomus.in-sanctum-pascha | Joannes Chrysostomus - In Sanctum Pascha | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,736 | auto-corrected |
| joannes-chrysostomus.in-sanctum-romanum-homilia-1 | Joannes Chrysostomus - In Sanctum Romanum (Homilia 1) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,535 | auto-corrected |
| joannes-chrysostomus.in-triduanam-resurrectionem-domini-sp | Joannes Chrysostomus - In Triduanam Resurrectionem Domini [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,729 | auto-corrected |
| joannes-chrysostomus.interpretatio-in-danielem-prophetam-sp | Joannes Chrysostomus - Interpretatio In Danielem Prophetam [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 20,891 | auto-corrected |
| joannes-chrysostomus.laus-diodori-episcopi | Joannes Chrysostomus - Laus Diodori Episcopi | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 976 | auto-corrected |
| joannes-chrysostomus.oratio-secunda-sp | Joannes Chrysostomus - Oratio Secunda [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,727 | raw OCR |
| joannes-chrysostomus.peccata-fratrum-non-evulganda | Joannes Chrysostomus - Peccata Fratrum Non Evulganda | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 13,122 | auto-corrected |
| joannes-chrysostomus.pg048 | Joannes Chrysostomus - pg048 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 35,870 | auto-corrected |
| joannes-chrysostomus.pg052 | Joannes Chrysostomus - pg052 | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,114 | auto-corrected |
| joannes-chrysostomus.post-reditum-priore-exsilio-sermo-2 | Joannes Chrysostomus - Post Reditum A Priore Exsilio (Sermo 2) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,948 | auto-corrected |
| joannes-chrysostomus.prooemia-in-psalmos-fragmenta-sp | Joannes Chrysostomus - Prooemia In Psalmos (Fragmenta) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,506 | auto-corrected |
| joannes-chrysostomus.quales-ducendae-sint-uxores-encomium-ad-maximum | Joannes Chrysostomus - Quales Ducendae Sint Uxores (= Encomium Ad Maximum) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,142 | auto-corrected |
| joannes-chrysostomus.quod-regulares-feminae-viris-cohabitare-non-debeant | Joannes Chrysostomus - Quod Regulares Feminae Viris Cohabitare Non Debeant | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,158 | auto-corrected |
| joannes-chrysostomus.sermo-antequam-iret-in-exsilium | Joannes Chrysostomus - Sermo Antequam Iret In Exsilium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,863 | auto-corrected |
| joannes-chrysostomus.sermo-cum-iret-in-exsilium | Joannes Chrysostomus - Sermo Cum Iret In Exsilium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 833 | raw OCR |
| joannes-chrysostomus.synopsis-scripturae-sacrae-sp | Joannes Chrysostomus - Synopsis Scripturae Sacrae [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 39,066 | auto-corrected |
| joannes-damascenus.adversus-iconoclastas-sp | Joannes Damascenus - Adversus Iconoclastas [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,083 | auto-corrected |
| joannes-damascenus.commentarii-in-epistulas-pauli-dub | Joannes Damascenus - Commentarii In Epistulas Pauli [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 96,410 | auto-corrected |
| joannes-damascenus.contra-nestorianos | Joannes Damascenus - Contra Nestorianos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,878 | auto-corrected |
| joannes-damascenus.de-azymis-fragmenta-duo-sp | Joannes Damascenus - De Azymis (Fragmenta Duo) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,274 | raw OCR |
| joannes-damascenus.de-duabus-in-christo-voluntatibus | Joannes Damascenus - De Duabus In Christo Voluntatibus | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,800 | auto-corrected |
| joannes-damascenus.de-immaculato-corpore-sp | Joannes Damascenus - De Immaculato Corpore [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,283 | auto-corrected |
| joannes-damascenus.de-natura-composita-sive-contra-acephalos | Joannes Damascenus - De Natura Composita Sive Contra Acephalos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,298 | auto-corrected |
| joannes-damascenus.de-octo-spiritibus-nequitiae-fragmentum-sp | Joannes Damascenus - De Octo Spiritibus Nequitiae (Fragmentum) [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,340 | auto-corrected |
| joannes-damascenus.de-sacris-imaginibus-contra-constantinum-cabalinum-sp | Joannes Damascenus - De Sacris Imaginibus Contra Constantinum Cabalinum [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 12,955 | auto-corrected |
| joannes-damascenus.de-sacris-jejuniis | Joannes Damascenus - De Sacris Jejuniis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,468 | auto-corrected |
| joannes-damascenus.de-sancta-trinitate-fragmentum-dub | Joannes Damascenus - De Sancta Trinitate (Fragmentum) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,057 | raw OCR |
| joannes-damascenus.disputatio-christiani-et-saraceni-dub | Joannes Damascenus - Disputatio Christiani Et Saraceni [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,746 | raw OCR |
| joannes-damascenus.epistula-de-hymno-trisagio | Joannes Damascenus - Epistula De Hymno Trisagio | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,956 | auto-corrected |
| joannes-damascenus.institutio-elementaris | Joannes Damascenus - Institutio Elementaris | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,838 | raw OCR |
| joannes-damascenus.oratio-de-his-qui-in-fide-dormierunt-sp | Joannes Damascenus - Oratio De His Qui In Fide Dormierunt [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 4,980 | auto-corrected |
| joannes-damascenus.passio-sancti-artemii-dub | Joannes Damascenus - Passio Sancti Artemii [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 10,805 | auto-corrected |
| joannes-damascenus.quid-est-homo-fragmentum-dub | Joannes Damascenus - Quid Est Homo? (Fragmentum) [Dub.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,094 | auto-corrected |
| joannes-damascenus.sacra-parallela-recensiones-secundum-alphabeti-litteras-dispositae | Joannes Damascenus - Sacra Parallela (Recensiones Secundum Alphabeti Litteras Dispositae, Quae Tres Libros Conflant) (Fragmenta E Cod. Vat. Gr. 1236) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 116,283 | auto-corrected |
| joannes-diaconus-hadrianopolitanus.carmen-politicum | Joannes Diaconus Hadrianopolitanus - Carmen politicum (encomiastic political verses to the emperor Palaiologos) (PG158 loci 515-520) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,075 | manual |
| joannes-doxopatres.prolegomena-tes-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,607 | manual |
| joannes-doxopatres.rhetorikai-homiliai-eis-ta-progymnasmata |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 121,656 | manual |
| joannes-epiphaniensis.fragmentum | Joannes Epiphaniensis - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 1,699 | auto-corrected |
| joannes-grammar.ekfrasis-tou-kosmikou-pi-nakos | Joannes - Ἔκφρασις τοῦ κοσμικοῦ πίνακος | qwen36-joannes_geometres_pg106 | Qwen3.6-27B | 199,397 | auto-corrected |
| joannes-hierosolymitanus.adversus-iconoclastas-olim-sub-auctore-joanne-damasceno | Joannes (olim sub auctore Joanne Damasceno) - Adversus iconoclastas (PG109 loci 256-263) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,938 | manual |
| joannes-hierosolymitanus.narratio | Joannes Hierosolymitanus monachus - Narratio (de origine haereseos iconomachorum) (PG109 loci 264-265) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 555 | auto-corrected |
| joannes-laurentius-lydus.de-magistratibus-populi-romani | Joannes Laurentius Lydus - De Magistratibus Populi Romani | qwen36-lydus_mensibus_wuensch | Qwen3.6-27B | 44,112 | auto-corrected |
| joannes-siceliota.exegesis-eis-tas-ideas-prolegomena |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,029 | auto-corrected |
| joannes-siceliota.scholia-eis-tas-ideas-tou-hermogenous |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 105,227 | manual |
| joannes-stobaeus-anthologus.anthologium | Joannes Stobaeus Anthologus - Anthologium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 435,325 | manual |
| joannes-tzetzes.epitome-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,453 | raw OCR |
| joannes-tzetzes.tzetzes-historiae-kiessling |  | qwen36-tzetzes_historiae_kiessling | Qwen3.6-27B | 103,943 | auto-corrected |
| joannes-zonaras.epitome-historiarum-lib-12-clausula-varia-dub | Joannes Zonaras - Epitome historiarum (lib. 12, clausula varia) [Dub.] (PG134 loci 568-569) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 775 | auto-corrected |
| joannes-zonaras.epitome-historiarum-lib-13-18 | Joannes Zonaras - Epitome historiarum (lib. 13-18) - only lib. 13-15 in this volume (PG134 loci 570-734) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 57,628 | manual |
| job-monachus.prooemium-in-psalmos | Job monachus ('Iob peccator') - Prooemium (to an exposition of the Psalms) (PG158 loci 562-563) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 340 | auto-corrected |
| joel.chronographia-compendiaria | Joel - Chronographia compendiaria (PG139 loci 119-151) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 12,528 | manual |
| josephus-genesius.basilei-ai | Josephus Genesius - Basileiai (Regum libri quattuor) (PG109 loci 501-583) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 22,703 | manual |
| josephus-ii-patriarcha.confessio-fidei | Josephus II patriarcha Constantinopolitanus - Confessio fidei ('He teleutaia gnome tou patriarchou', Florence, 9 June 1439) (PG158 loci 561-561) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 237 | auto-corrected |
| josephus-rhacendyta.synopsis-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 23,967 | manual |
| justinus-martyr.fragmenta-operum-deperditorum | Justinus Martyr - Fragmenta operum deperditorum (ex Irenaeo et Methodio) (PG006 loci 803-804) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 338 | auto-corrected |
| laetus.fragmenta | Laetus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 442 | auto-corrected |
| lamprocles.fragmenta | Lamprocles - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,193 | auto-corrected |
| laudatio-sancti-demetrii.narratio-de-capta-thessalonica | Anonymus (laudatio S. Demetrii) - Ex laudatione martyris Demetrii narratio (on the 904 capture of Thessalonica) (PG109 loci 266-267) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 624 | auto-corrected |
| leo-vi-sapiens.carmen-compunctorium | Leo VI Sapiens imperator - Carmen compunctorium (anacreonticum de extremo iudicio) (PG107 loci 196-198) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 796 | manual |
| leo-vi-sapiens.carmina-et-epigrammata-varia | Leo VI Sapiens imperator (et Leo Philosophus attrib.) - Carmina et epigrammata varia (iambi; carmen hexametricum de mensibus; excerpta de S. Clemente) (PG107 loci 371-375) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,429 | auto-corrected |
| leo-vi-sapiens.exapostilaria-anastasima | Leo VI Sapiens imperator (attrib.) - Exapostilaria anastasima (cum theotokiis) (PG107 loci 191-195) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,707 | manual |
| leo-vi-sapiens.notitiae-episcopatuum-et-documenta-de-praecedentia | Leo VI Sapiens imperator et alii (documenta ecclesiastica) - Notitiae episcopatuum et documenta de praecedentia (Diatyposis Leonis; ps.-Epiphanii Ekthesis; Notitia patriarchatuum; Ekthesis nea) (PG107 loci 206-250) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 8,767 | manual |
| leo-vi-sapiens.novellae-constitutiones | Leo VI Sapiens imperator - Novellae constitutiones (cum prooemio; const. I-CXIII et diataxeis additae ad CXVII) (PG107 loci 252-370) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 37,074 | manual |
| leo-vi-sapiens.oracula | Leo VI Sapiens imperator (attrib.) - Oracula (cum vaticinio prosaico appendice) (PG107 loci 606-616) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,594 | manual |
| leo-vi-sapiens.orationes | Leo VI Sapiens imperator - Orationes (homiliae et panegyrici) I-XX (collectio Combefis) (PG107 loci 42-188) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 50,226 | manual |
| leo-vi-sapiens.tactica | Leo VI Sapiens imperator - Tactica (cum pinace et prooemio) (PG107 loci 377-601) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 85,962 | manual |
| lesbonax-rhetoric.politiko-s | LESBONAX - De figuris | qwen36-lesbonax | Qwen3.6-27B | 970 | raw OCR |
| leucippus.testimonia | LEUCIPPUS - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,626 | auto-corrected |
| lexicon-sabbaiticum.lexicon-sabbaiticum-e-cod-sabbaitico-137 | Lexicon Sabbaiticum - Lexicon Sabbaiticum (E Cod. Sabbaitico 137) | [archive.org](https://archive.org/details/lexicon-sabbaiticum-athanasios-papadopulos-kerameus) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 5,134 | auto-corrected |
| licymnius.fragmenta | Licymnius - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 2,161 | auto-corrected |
| limenius.paean-delphicus-ii-et-prosodium-in-apollinem | Limenius - Paean Delphicus Ii Et Prosodium In Apollinem | qwen36-limenius_delphic_fairbanks | Qwen3.6-27B | 7,448 | auto-corrected |
| lucius-annaeus-cornutus.cornutus-lang |  | qwen36-cornutus_lang | Qwen3.6-27B | 23,228 | auto-corrected |
| lycon-tarentinus-vel-iasensis.testimonia | Lycon - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 383 | raw OCR |
| lycophron-tragedy.fragmenta | Lycophron - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 302 | auto-corrected |
| lycophronides.fragmenta | LYCOPHRONIDES - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 20 | raw OCR |
| lynceus.fragmentum | LYNCEUS - Fragmentum | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 108 | raw OCR |
| lyrica-adespota-ca.fragmenta-lyrica | Lyrica Adespota (Ca) - Fragmenta Lyrica | qwen36-lyrica_adespota_bergk_plg3 | Qwen3.6-27B | 58,849 | auto-corrected |
| lysippus.fragmenta | Lysippus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 333 | raw OCR |
| magnes.fragmenta | Magnes - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 62 | raw OCR |
| magnus.fragmentum | Magnus - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 793 | auto-corrected |
| manetho.fragmenta | Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 3,034 | auto-corrected |
| mantissa-proverbiorum.mantissa-proverbiorum | Mantissa Proverbiorum - Mantissa Proverbiorum | [archive.org](https://archive.org/details/corpusparoemiogr02leutuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 167,532 | auto-corrected |
| marcellinus.vita-thucydidis | Marcellinus - Vita Thucydidis | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 97,683 | auto-corrected |
| martyrium-ignatii.martyrium-ignatii-antiocheni-martyrium-antiochenum | Martyrium Ignatii - Martyrium Ignatii Antiocheni (martyrium Antiochenum, 'Colbertinum') (PG005 loci 499-503) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,280 | auto-corrected |
| matthaeus-camariota.rhetorikes-epitome |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,874 | auto-corrected |
| maximus-planudes.peri-ton-alyton-antitheseon |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 3,022 | auto-corrected |
| maximus-planudes.scholia-eis-ten-hermogenous-technen |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 86,789 | auto-corrected |
| maximus-rhetoric.peri-tw-n-lu-twn-ntiqe-sewn-fort-auctore-maximo | Maximus - Περὶ τῶν ἀλύτων ἀντιθέσεων (Fort. Auctore Maximo Byzantio) | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,999 | auto-corrected |
| maximus-theology.fragmentum-ex-libro-de-materia | Maximus - Fragmentum ex libro de materia (PG005 loci 679-687) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,066 | auto-corrected |
| melanippides.fragmenta | MELANIPPIDES - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 268 | raw OCR |
| melanthius-elegy.fragmentum | Melanthius - Fragmentum | bergk-plg2-ocr-frag | Qwen3.6-27B | 73 | raw OCR |
| melanthius.fragmentum | Fragmentum | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 277 | auto-corrected |
| melissus.testimonia | Melissus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 9,146 | auto-corrected |
| melito-apologetics.fragmenta | Melito Sardensis - Fragmenta (PG005 loci 614-620) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 931 | manual |
| menander-comedy.fragmenta-2 | Menander - Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 27,049 | raw OCR |
| menecrates-elaita.fragmenta | Menecrates - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 573 | auto-corrected |
| menecrates-poet-phil.fragmentum-et-titulus | Menecrates - Fragmentum Et Titulus | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 148 | raw OCR |
| menecrates.titulus | MENECRATES - Titulus | kock-caf3-ocr | Qwen3.6-27B | 92 | raw OCR |
| menestor.testimonia | Menestor - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 668 | auto-corrected |
| metagenes.fragmenta | Metagenes - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 494 | auto-corrected |
| metopus.fragmenta | Metopus - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 461 | raw OCR |
| metrodorus-koerte |  | qwen36-metrodorus_koerte | Qwen3.6-27B | 8,673 | auto-corrected |
| metrodorus-major.testimonia | Metrodorus Major - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 850 | raw OCR |
| metrodorus-philosophy.testimonia | Metrodorus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,740 | auto-corrected |
| metrophanes.fragmentum | Metrophanes - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 273 | raw OCR |
| michael-glycas.annales | Michael Glycas - Annales (PG158 loci 49-347) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 114,679 | manual |
| michael-glycas.epistolae | Michael Glycas - Epistolae (I-XXIX; chapters of Eis tas aporias tes Theias Graphes) (PG158 loci 359-514) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 55,726 | manual |
| michael-psellus.characteres-gregorii-theologi-basilii-magni-chrysostomi-et-gregorii-nysseni | Michael Psellus - Characteres Gregorii Theologi, Basilii Magni, Chrysostomi et Gregorii Nysseni (PG122 loci 461-463) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,240 | manual |
| michael-psellus.commentarius-in-psychogoniam-platonicam | Michael Psellus - Commentarius in Psychogoniam Platonicam (on the soul-generation in Plato's Timaeus) (PG122 loci 550-589) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 6,512 | manual |
| michael-psellus.de-actionum-nominibus | Michael Psellus - De actionum nominibus (Attic legal antiquities) (PG122 loci 514-521) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,907 | manual |
| michael-psellus.de-anima-celebres-opiniones | Michael Psellus - De anima celebres opiniones (PG122 loci 525-548) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,381 | manual |
| michael-psellus.de-lapidum-virtutibus | Michael Psellus - De lapidum virtutibus (PG122 loci 454-460) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 902 | manual |
| michael-psellus.de-legum-nominibus | Michael Psellus - De legum nominibus (glossary of Roman-law terms and Latin legal loanwords) (PG122 loci 522-524) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 752 | auto-corrected |
| michael-psellus.de-locis-et-nominibus-atticis-sp | Pseudo-Michael Psellus - De locis et nominibus Atticis (PG122 loci 610-612) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,032 | auto-corrected |
| michael-psellus.de-mortis-determinatione | Michael Psellus - De mortis determinatione (Antigraphe on whether the term of life is fixed) (PG122 loci 468-469) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 732 | manual |
| michael-psellus.de-omnifaria-doctrina | Michael Psellus - De omnifaria doctrina (Didaskalia pantodape) (PG122 loci 351-400) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 20,335 | manual |
| michael-psellus.de-operatione-daemonum-sp | Pseudo-Michael Psellus - De operatione daemonum dialogus (Timotheus; now held spurious) (PG122 loci 419-447) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 6,758 | manual |
| michael-psellus.epistulae | Michael Psellus - Epistolae (numbered PG selection, with the In equum aereum epigram at the head of the first row) (PG122 loci 613-625) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,195 | manual |
| michael-psellus.in-mercurii-trismegisti-pimandrum | Michael Psellus - In Mercurii Trismegisti Pimandrum (brief note) (PG122 loci 609-609) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 305 | auto-corrected |
| michael-psellus.monodia-in-sanctae-sophiae-collapsam | Michael Psellus - Monodia in Sanctae Sophiae (partem) collapsam (PG122 loci 466-467) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 757 | manual |
| michael-psellus.opuscula-psychologica-theologica-daemonologica | Michael Psellus - Expositio in oracula Chaldaica + Expositio brevis dogmatum Chaldaicorum (the two Chaldaica of O'Meara's Philosophica minora II, partial) (PG122 loci 594-608) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,287 | manual |
| michael-psellus.peri-rhetorikes |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,564 | auto-corrected |
| michael-psellus.peri-synthekes-ton-tou-logou-meron |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 812 | raw OCR |
| michael-psellus.poemata | Michael Psellus - Poemata (PG 122 selection: In Canticum canticorum paraphrasis cum exegesi = poem 2; Versus de dogmate; Synopsis canonum; Synopsis legum = poem 8, first pages only) (PG122 loci 275-475) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 31,969 | manual |
| michael-psellus.quaenam-sunt-graecorum-opiniones-de-daemonibus-sp | Pseudo-Michael Psellus - Quaenam sunt Graecorum opiniones de daemonibus (PG122 loci 448-451) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,430 | auto-corrected |
| michael-psellus.quaestionum-naturalium-solutiones-sp | Pseudo-Michael Psellus - Quaestionum naturalium solutiones (anonymous compendium, Migne's title; akin to Symeon Seth) (PG122 loci 401-414) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,699 | manual |
| michael-psellus.synopsis-ton-rhetorikon-meron |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 1,138 | auto-corrected |
| michael-psellus.versus-in-sanctos-tres-hierarchas-sp | Pseudo-Michael Psellus (fort. Joannes Mauropous) - Versus in sanctos tres hierarchas with epigrams (signed by a John, probably Mauropous; printed as Joannis Pselli) (PG122 loci 464-465) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 480 | manual |
| michael.in-ethica-nicomachea-ixx-commentaria | MICHAEL EPHESIUS - In Ethica Nicomachea commentaria (CAG XX) | qwen36-commentariainari20bero | Qwen3.6-27B | 6,111 | raw OCR |
| milon.fragmentum | Milon - Fragmentum | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 54 | auto-corrected |
| mimnermus-elegy.fragmenta | Mimnermus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 594 | auto-corrected |
| mimnermus-tragedy.fragmenta | MIMNERMUS TRAGICUS - Fragmenta (TGF Nauck) | qwen36-nauck-tgf-mimnermus | Qwen3.6-27B | 1,088 | raw OCR |
| minucianus.peri-epicheirematon |  | qwen36-walz_rhetores_v9 | Qwen3.6-27B | 2,297 | auto-corrected |
| mnesimachus-comedy.fragmenta | Mnesimachus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 697 | raw OCR |
| moderatus.fragmenta | Moderatus - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 609 | auto-corrected |
| moeris.lexicon-atticum | Moeris - Lexicon Atticum | [archive.org](https://archive.org/details/moeridisatticis00moergoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 58,061 | auto-corrected |
| monimus-cynicus.fragmenta | De Monimo + Monimi fragmenta (Cynic) | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 299 | auto-corrected |
| moschion.fragmenta | Moschion - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 491 | raw OCR |
| moses.eu-poi-kai-eu-tuxi-tou-ktisame-nou-kai-e-pituxi-kama-tou-kai | Moses - Εὐποία καὶ εὐτυχία τοῦ κτισαμένου καὶ ἐπιτυχία καμάτου καὶ μακροχρονία βίου (E Cod. Paris. B.N. Gr. 2327, Fol. 268V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,753 | auto-corrected |
| mullach-fpg2.paratexta |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 37,591 | auto-corrected |
| musaeus-philosophy.testimonia | Musaeus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 857 | auto-corrected |
| myron.fragmenta | Myron - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 371 | auto-corrected |
| myrtilus.fragmenta | MYRTILUS - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 143 | raw OCR |
| nausicrates.fragmenta | Nausicrates - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 69 | raw OCR |
| nausiphanes.testimonia | Nausiphanes - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 2,195 | auto-corrected |
| nechepso-petosiris-riess |  | qwen36-nechepso_petosiris_riess | Qwen3.6-27B | 842 | auto-corrected |
| neophron.fragmenta | Neophron - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 336 | auto-corrected |
| neoptolemus.fragmenta | NEOPTOLEMUS - Fragmenta | qwen36-alexander_aetolus_meineke-ocr | Qwen3.6-27B | 144 | raw OCR |
| nessas.testimonia | Nessas - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 142 | auto-corrected |
| nestorianus.fragmenta | Fragmenta | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 216 | raw OCR |
| nicephorus-basilaces.progymnasmata |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 25,181 | auto-corrected |
| nicephorus-blemmydes.aper-xrh-zei-h-parou-sa-kataskeuh-fort-auctore | Nicephorus Blemmydes - Ἅπερ χρῄζει ἡ παροῦσα κατασκευή (Fort. Auctore Nicephoro Blemmyde Alio) (E Cod. Paris. B.N. Gr. 2509, Fol. 139R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 321 | raw OCR |
| nicephorus-blemmydes.nikhfo-rou-tou-blemmu-dou-peri-th-s-xrusopoii-as-fort | Nicephorus Blemmydes - Νικηφόρου τοῦ Βλεμμύδου περὶ τῆς χρυσοποιίας (Fort. Auctore Nicephoro Blemmyde Alio) (E Cod. Paris. B.N. Gr. 2509, Fol. 137R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,582 | auto-corrected |
| nicephorus-callistus-xanthopulus.historia-ecclesiastica-lib-8-14 | Nicephorus Callistus Xanthopulus - Historia ecclesiastica, libri VIII-XIV (PG 146; books 1-7 and 15-18 are in PG 145/147, not served) (PG146 loci 12-644) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 239,129 | manual |
| nicetas-heracleensis.fragmenta-commentariorum-xvi-orationum-gregorii-nazianzeni | Nicetas Heracleensis - Fragmenta commentariorum XVI orationum Gregorii Nazianzeni | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,346 | auto-corrected |
| nicetas-maroniensis.dialogi-de-processione-spiritus-sancti | Nicetas Maroniensis - Dialogi de processione Spiritus Sancti (PG139 loci 92-118) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 9,885 | manual |
| nicias-history.fragmentum | Nicias - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 65 | raw OCR |
| nicochares.fragmenta | Nicochares - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 320 | raw OCR |
| nicolaus-rhetoric.progymnasmata | Nicolaus - Progymnasmata | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 17,289 | auto-corrected |
| nicolaus.fragmenta | NICOLAUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 141 | raw OCR |
| nicomachus.fragmenta | NICOMACHUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 158 | raw OCR |
| nicophon.fragmenta | Nicophon - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 560 | raw OCR |
| nicostratus.fragmenta | Nicostratus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 969 | auto-corrected |
| nonnosus.fragmenta | Nonnosus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 881 | raw OCR |
| ocellus.de-universi-natura-sp | Ocellus - De Universi Natura [Sp.] | qwen36-hierocl_aureum_mullach_fpg1-ocr | Qwen3.6-27B | 5,422 | auto-corrected |
| oecumenius.commentarius-in-acta-apostolorum | Pseudo-Oecumenius - Commentarius in Acta apostolorum (catena-derived commentary printed under Oecumenius' name, CPG C151 sphere) (PG118 loci 29-162) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 53,570 | manual |
| oecumenius.fragmenta-in-epistulam-ad-ephesios-in-catenis | Oecumenius - Fragmenta in epistulam ad Ephesios (in catenis) [served text = full catena commentary] (PG118 loci 594-638) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 18,393 | manual |
| oecumenius.fragmenta-in-epistulam-ad-galatas-in-catenis | Oecumenius - Fragmenta in epistulam ad Galatas (in catenis) [served text = full catena commentary] (PG118 loci 556-593) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 15,415 | manual |
| oecumenius.fragmenta-in-epistulam-ad-philippenses-in-catenis | Oecumenius - Fragmenta in epistulam ad Philippenses (in catenis) [served text = full catena commentary] (PG118 loci 639-674) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 14,427 | manual |
| oecumenius.fragmenta-in-epistulam-ad-romanos-in-catenis | Oecumenius (ps.-Oecumenius catena) - Fragmenta in epistulam ad Romanos (in catenis) [served text = full ps.-Oecumenius catena commentary on Romans] (PG118 loci 168-326) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 66,155 | manual |
| oecumenius.fragmenta-in-epistulam-i-ad-corinthios-in-catenis | Oecumenius - Fragmenta in epistulam i ad Corinthios (in catenis) [served text = full catena commentary] (PG118 loci 327-461) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 55,233 | manual |
| oecumenius.fragmenta-in-epistulam-ii-ad-corinthios-in-catenis | Oecumenius - Fragmenta in epistulam ii ad Corinthios (in catenis) [served text = full catena commentary] (PG118 loci 462-555) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 37,734 | manual |
| oenopides.testimonia | Oenopides - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,451 | auto-corrected |
| onatas.fragmenta | Onatas - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 425 | auto-corrected |
| ophelio.fragmenta | Ophelio - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 132 | auto-corrected |
| oracula-chaldaica.oracula-fragmenta-olim-sub-auctore-juliano-theurgo | Oracula Chaldaica - Oracula (Fragmenta) (Olim Sub Auctore Juliano Theurgo) | qwen36-oracula_chaldaica_kroll | Qwen3.6-27B | 8,267 | auto-corrected |
| oribasius.collectiones-medicae-lib-1-16-24-25-43-50 | Oribasius - Collectiones Medicae (Lib. 1-16, 24-25, 43-50) | qwen36-bussemaker-daremberg-1851-rover | Qwen3.6-27B | 315,754 | manual |
| oribasius.collectiones-medicae-libri-incerti | Oribasius - Collectiones Medicae (Libri Incerti) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 30,793 | manual |
| oribasius.libri-ad-eunapium-lib-1-4 | Oribasius - Libri Ad Eunapium (Lib. 1-4) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,499 | auto-corrected |
| oribasius.synopsis-ad-eustathium-filium | Oribasius - Synopsis Ad Eustathium Filium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 78,632 | auto-corrected |
| orphica.argonautica | ORPHICA - Argonautica | qwen36-abel-orphica-argonautica | Qwen3.6-27B | 6,794 | auto-corrected |
| orphica.hymni | ORPHICA - Hymni | qwen36-abel-orphica-hymni | Qwen3.6-27B | 5,519 | auto-corrected |
| orphica.lithica | ORPHICA - Lithica | qwen36-abel-orphica-lithica | Qwen3.6-27B | 2,518 | raw OCR |
| orphica.testimonia | Orphica - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,796 | auto-corrected |
| ostanes-magus.osta-nou-filoso-fou-pro-s-peta-sion-peri-th-s-i-era-s-tau-ths-kai | Ostanes Magus - Ὀστάνου φιλοσόφου πρὸς Πετάσιον περὶ τῆς ἱερᾶς ταύτης καὶ θείας τέχνης (E Cod. Venet. Marc. 299, Fol. 66R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 416 | auto-corrected |
| pancrates-epigram.fragmenta | PANCRATES - Fragmenta | qwen36-oxyrhynchuspapyr08gren | Qwen3.6-27B | 211 | raw OCR |
| pantaenus.fragmenta | Pantaenus Alexandrinus - Fragmenta (PG005 loci 674-675) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 225 | raw OCR |
| panyassis.fragmenta-epica | Panyassis - Fragmenta Epica | qwen36-panyassis_kinkel_egf | Qwen3.6-27B | 33,197 | auto-corrected |
| papias.fragmenta | Papias Hierapolitanus - Fragmenta (PG005 loci 637-640) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 708 | manual |
| parmenides.testimonia | Parmenides - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 18,863 | auto-corrected |
| parmiscus.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 133 | raw OCR |
| paron.testimonium | Paron - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 184 | raw OCR |
| patria-constantinopoleos.de-sepulcris-imperatorum-quae-sunt-in-templo-sanctorum-apostolorum | Patria Constantinopoleos (anonymous, printed under Codinus) - De sepulcris imperatorum quae sunt in templo sanctorum apostolorum (PG157 loci 370-377) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 746 | manual |
| patria-constantinopoleos.parasta-seis-su-ntomoi-xronikai | Patria Constantinopoleos (anonymous, printed under Codinus) - Parastaseis syntomoi chronikai (with Peri theamaton section) (PG157 loci 333-369) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 7,797 | manual |
| patrocles.fragmenta | Fragmenta | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 131 | auto-corrected |
| paulus-medicine.epitomae-medicae-libri-septem | Paulus - Epitomae Medicae Libri Septem | qwen36-paulus_aegineta_heiberg_cmg9 | Qwen3.6-27B | 119,239 | auto-corrected |
| paulus-silentiarius.descriptio-sanctae-sophiae | Paulus Silentiarius - Descriptio Sanctae Sophiae | qwen36-paulsilent_descriptio_bekker | Qwen3.6-27B | 45,173 | auto-corrected |
| pausanias-attic.attikw-n-o-noma-twn-sunagwgh | Pausanias - Ἀττικῶν ὀνομάτων συναγωγή | qwen36-aelius_dionysius_schwabe-ocr | Qwen3.6-27B | 19,814 | auto-corrected |
| pelagius.pelagi-ou-filoso-fou-peri-th-s-qei-as-tau-ths-kai-i-era-s-te-xnhs | Pelagius - Πελαγίου φιλοσόφου περὶ τῆς θείας ταύτης καὶ ἱερᾶς τέχνης (E Cod. Venet. Marc. 299, Fol. 62V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 2,274 | auto-corrected |
| pempelus.fragmenta | Pempelus - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 227 | raw OCR |
| perictione.fragmenta | Perictione - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 1,259 | auto-corrected |
| persaeus.fragmenta | Persaeus - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,739 | auto-corrected |
| petron.testimonium | Petron - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 214 | raw OCR |
| phaenias.fragmenta | Phaenias - Fragmenta | qwen36-demochares_fhg2-ocr | Qwen3.6-27B | 666 | raw OCR |
| phaleas-et-hippodamus.testimonia-et-fragmenta |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,237 | raw OCR |
| phanocles.fragmenta | Phanocles - Fragmenta | qwen36-philetas_bach_1829-ocr | Qwen3.6-27B | 2,451 | auto-corrected |
| pherecrates.fragmenta | Pherecrates - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 5,117 | auto-corrected |
| pherecydes-mythography.testimonia | Pherecydes - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,268 | auto-corrected |
| philemon-junior.fragmenta | Philemon Junior - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 111 | raw OCR |
| philemon.fragmenta | Philemon - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 5,863 | auto-corrected |
| philetaerus.fragmenta | Philetaerus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 413 | raw OCR |
| philetas.fragmenta | Philetas - Fragmenta | qwen36-philetas_bach_1829 | Qwen3.6-27B | 6,371 | auto-corrected |
| philippides.fragmenta | PHILIPPIDES - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 1,020 | raw OCR |
| philippus-history.fragmenta | Philippus - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 159 | raw OCR |
| philiscus-comedy.fragmenta | Philiscus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 88 | raw OCR |
| philocles-tragedy.fragmenta | ΤΗΡΕΤΣ v. ΠΑΝΔΙΟΝΙΣ | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 216 | auto-corrected |
| philodamus.paean-in-dionysum | Philodamus - Paean In Dionysum | qwen36-limenius_delphic_fairbanks-ocr | Qwen3.6-27B | 814 | auto-corrected |
| philodemus.tlg1595-tlg003 | PHILODEMUS - Index Stoicorum Herculanensis | qwen36-rivistadifilolog03-p469-576 | Qwen3.6-27B | 2,744 | raw OCR |
| philodemus.tlg1595-tlg241 | PHILODEMUS - De oeconomia | qwen36-philodemiperioik00phil | Qwen3.6-27B | 17,894 | raw OCR |
| philodemus.tlg1595-tlg267 | PHILODEMUS - De ira | qwen36-philodemiepicur00philgoog | Qwen3.6-27B | 8,279 | raw OCR |
| philodemus.tlg1595-tlg271 | PHILODEMUS - De libertate dicendi (Peri parrhesias) | qwen36-philodemiperipar00philuoft | Qwen3.6-27B | 9,795 | raw OCR |
| philodemus.tlg1595-tlg289 | PHILODEMUS - De poematis (Peri poiematon) | qwen36-philodemiperipoi00haus | Qwen3.6-27B | 2,053 | raw OCR |
| philodemus.tlg1595-tlg472 | PHILODEMUS - De signis (Peri semeion kai semeioseon) | qwen36-philodemberindu00gompgoog | Qwen3.6-27B | 4,581 | raw OCR |
| philodemus.tlg1595-tlg492 | PHILODEMUS - De bono rege secundum Homerum | qwen36-philodemiperitou00philuoft | Qwen3.6-27B | 9,500 | raw OCR |
| philodemus.tlg1595-tlg601 |  | [Philodemus, Academicorum index Herculanensis, ed. Mekler, Berlin 1902](https://archive.org/details/academicorumphil00mekluoft) | Qwen3.6-27B | 9,689 | auto-corrected |
| philodemus.volumina-rhetorica | De rhetorica (Volumina rhetorica) | [Philodemus, Volumina rhetorica vol.1, ed. Sudhaus, Teubner 1892](https://archive.org/details/philodemivolumi00schugoog) | Qwen3.6-27B | 99,394 | auto-corrected |
| philolaus.testimonia | Philolaus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 8,426 | auto-corrected |
| philonides.fragmenta | Philonides - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 118 | raw OCR |
| philosophus-anonymus.anepigra-fou-filoso-fou-kata-kolouqi-xrh-sews-e-mfai-non | Philosophus Anonymus - Ἀνεπιγράφου φιλοσόφου κατὰ ἀκολουθίαν χρήσεως ἐμφαῖνον τὸ τῆς χρυσοποιίας συνεπτυγμένον σὺν θεῷ (E Cod. Venet. Marc. 299, Fol.79R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 3,011 | auto-corrected |
| philosophus-anonymus.anepigra-fou-filoso-fou-peri-qei-ou-u-datos-th-s-leukw-sews | Philosophus Anonymus - Ἀνεπιγράφου φιλοσόφου περὶ θείου ὕδατος τῆς λευκώσεως (E Cod. Venet. Marc. 299, Fol. 78R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 832 | auto-corrected |
| philosophus-anonymus.anepigra-fou-filoso-fou-peri-th-s-qei-as-kai-i-era-s-te-xnhs | Philosophus Anonymus - Ἀνεπιγράφου φιλοσόφου περὶ τῆς θείας καὶ ἱερᾶς τέχνης φιλοσόφων (E Codd. Venet. Marc. 299, Fol. 181R Paris. B.N. Gr. 2329,Fol. 180V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 2,863 | auto-corrected |
| philosophus-christianus.anti-qesis-le-gousa-o-ti-qei-on-u-dwr-e-n-e-sti-tw-ei-dei | Philosophus Christianus - Ἀντίθεσις λέγουσα ὅτι τὸ θεῖον ὕδωρ ἕν ἐστι τῷ εἴδει καὶ ἡ λύσις αὐτῆς (E Cod. Venet. Marc. 299, Fol. 119R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 466 | raw OCR |
| philosophus-christianus.apori-e-n-bu-ssaion-u-dwr-e-n-tw-riqmw-deiknu-ein | Philosophus Christianus - Ἀπορία. Τὸ ἓν ἀβύσσαιον ὕδωρ ἐν τῷ ἀριθμῷ δεικνύειν ἐθέλουσα ἡ τούτου ἐπίλυσις (E Cod. Venet. Marc. 299, Fol. 120R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 431 | auto-corrected |
| philosophus-christianus.h-tou-muqikou-u-datos-poi-hsis-e-cod-venet-marc-299 | Philosophus Christianus - Ἡ τοῦ μυθικοῦ ὕδατος ποίησις (E Cod. Venet. Marc. 299, Fol. 102R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 861 | auto-corrected |
| philosophus-christianus.oti-tetraxw-s-diairoume-nhs-th-s-u-lhs-dia-foroi-pogi-nontai | Philosophus Christianus - Ὅτι τετραχῶς διαιρουμένης τῆς ὕλης, διάφοροι ἀπογίνονται τῶν ποιήσεων αἱ τάξεις (E Cod. Venet. Marc. 299, Fol. 121V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 219 | auto-corrected |
| philosophus-christianus.po-sai-ei-si-n-ai-kat-ei-dos-kai-ge-nos-diaforai-tw-n-poih-sewn | Philosophus Christianus - Πόσαι εἰσὶν αἱ κατ’ εἶδος καὶ γένος διαφοραὶ τῶν ποιήσεων (E Cod. Venet. Marc. 299, Fol. 122R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 916 | auto-corrected |
| philosophus-christianus.pw-s-dei-noei-n-diafora-s-tw-n-poih-sewn-kai-sxh-masi-gewmetrikoi-s | Philosophus Christianus - Πῶς δεῖ νοεῖν διαφορὰς τῶν ποιήσεων καὶ σχήμασι γεωμετρικοῖς (E Cod. Venet. Marc. 299, Fol. 124R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 243 | raw OCR |
| philosophus-christianus.ti-s-h-e-n-pokru-fois-tw-n-palaiw-n-e-kdidome-nh-ta-cis-e | Philosophus Christianus - Τίς ἡ ἐν ἀποκρύφοις τῶν παλαιῶν ἐκδιδομένη τάξις (E Cod. Venet. Marc. 299, Fol. 124V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 1,417 | auto-corrected |
| philosophus-christianus.ti-s-h-kaqo-lou-tou-u-datos-oi-konomi-e-cod-venet | Philosophus Christianus - Τίς ἡ καθόλου τοῦ ὕδατος οἰκονομία (E Cod. Venet. Marc. 299, Fol. 102R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 37 | auto-corrected |
| philosophus-christianus.ti-s-h-tw-n-rxai-wn-diafwni-e-cod-venet-marc-299 | Philosophus Christianus - Τίς ἡ τῶν ἀρχαίων διαφωνία (E Cod. Venet. Marc. 299, Fol. 101V) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 263 | auto-corrected |
| philosophus-christianus.tou-xristianou-peri-eu-staqei-as-tou-xrusou-e-cod | Philosophus Christianus - Τοῦ Χριστιανοῦ περὶ εὐσταθείας τοῦ χρυσοῦ (E Cod. Venet. Marc. 299, Fol. 110R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 949 | auto-corrected |
| philosophus-christianus.tou-xristianou-peri-tou-qei-ou-u-datos-e-cod-venet | Philosophus Christianus - Τοῦ Χριστιανοῦ περὶ τοῦ θείου ὕδατος (E Cod. Venet. Marc. 299, Fol. 101R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 134 | auto-corrected |
| philosophus-christianus.tou-xristianou-su-noyis-ti-s-h-ai-ti-th-s-prokeime-nhs | Philosophus Christianus - Τοῦ Χριστιανοῦ σύνοψις. τίς ἡ αἰτία τῆς προκειμένης συγγραφῆς (E Cod. Venet. Marc. 299, Fol. 121R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 85 | raw OCR |
| philostephanus.fragmenta | Fragmenta | qwen36-aristobulus_fhg3-ocr | Qwen3.6-27B | 96 | raw OCR |
| philotheus-constantinopolitanus.antirrhetici-contra-gregoram | Philotheus Constantinopolitanus - Antirrhetici contra Gregoram (PG151 loci 394-576) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 160,979 | manual |
| philotheus-constantinopolitanus.encomium-gregorii-palamae | Philotheus Constantinopolitanus - Encomium Gregorii Palamae (PG151 loci 283-346) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 54,429 | manual |
| philoxenus.fragmenta | PHILOXENUS - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 977 | auto-corrected |
| philyllius.fragmenta | Philyllius - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 559 | raw OCR |
| phintys.fragmenta | Phintys - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 820 | auto-corrected |
| phocylides.sententiae | PHOCYLIDES - Sententiae | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 909 | auto-corrected |
| phoebammon.scholia-peri-schematon-rhetorikon-walz-viii |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,587 | auto-corrected |
| phoenicides.fragmenta | PHOENICIDES - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 285 | raw OCR |
| phoenix.fragmenta | Phoenix - Fragmenta | qwen36-phoenix_choliambi_crusius | Qwen3.6-27B | 29,998 | auto-corrected |
| photius.amphilochia | Photius - Amphilochia (Migne main series: prooemium + quaestiones I-CCCXXI+, truncated) (PG101 loci 44-611) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 215,610 | manual |
| photius.amphilochia-supplementum | Photius - Amphilochia, supplementum: fuller recensions of selected quaestiones (PG101 loci 664-673) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,884 | manual |
| photius.bibliotheca | Photius - Bibliotheca | [archive.org](https://archive.org/details/bub_gb_NsiGxvHyQY0C) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 154,191 | raw OCR |
| photius.commentarii-in-joannem-in-catenis | Photius - Commentarii in Joannem (in catenis) - Migne/Mai fragment series (PG101 loci 641-641) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 336 | auto-corrected |
| photius.commentarii-in-matthaeum-in-catenis | Photius - Commentarii in Matthaeum (in catenis) - Migne/Mai fragment series (PG101 loci 620-630) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,601 | manual |
| photius.fragmenta-in-epistulam-ad-romanos-in-catenis | Photius - Fragmenta in epistulam ad Romanos (in catenis) - Migne/Mai fragment series (PG101 loci 642-651) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,207 | manual |
| photius.fragmenta-in-epistulam-ii-ad-corinthios-in-catenis | Photius - Fragmenta in epistulam ii ad Corinthios (in catenis) - Migne/Mai fragment series, truncated (PG101 loci 652-652) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 366 | raw OCR |
| photius.fragmenta-in-lucam-in-catenis | Photius - Fragmenta in Lucam (in catenis) (PG101 loci 632-640) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,657 | manual |
| photius.fragmenta-in-marcum-in-catenis | Photius - Fragmenta in Marcum (in catenis) (PG101 loci 631-631) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 383 | raw OCR |
| photius.lexicon | Photius - Lexicon | [archive.org](https://archive.org/details/photiipatriarch00nabegoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 102,751 | auto-corrected |
| phrynichus-comedy.fragmenta | Phrynichus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 1,672 | auto-corrected |
| phrynichus-tragedy.fragmenta | Phrynichus - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 642 | raw OCR |
| pigres.fragmentum | Pigres - Fragmentum | bergk-plg2-ocr-frag | Qwen3.6-27B | 628 | raw OCR |
| pindarus.fragmenta | Pindarus - Fragmenta | [Pindar, ed. Schroeder (Teubner)](https://archive.org/search?query=Pindari+carmina+Schroeder) | Qwen3.6-27B | 12,139 | auto-corrected |
| pisander-epic.heraclea-fragmenta | Pisander - Heraclea (Fragmenta) | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 28 | raw OCR |
| plato-comedy.fragmenta | Plato - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 5,848 | auto-corrected |
| platonius.fragmenta-de-comoedia-graeca | Platonius - Fragmenta De Comoedia Graeca | qwen36-platonius_duebner_scholaristoph1 | Qwen3.6-27B | 355,282 | auto-corrected |
| poliochus.fragmenta | POLIOCHUS - Fragmenta | qwen36-comica_adespota_caf3 | Qwen3.6-27B | 193 | auto-corrected |
| polus-lucanus.fragmentum |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 184 | raw OCR |
| polybius-sardianus.peri-schematismou |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 756 | auto-corrected |
| polyclitus.testimonia | Polyclitus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 761 | auto-corrected |
| polystratus.peri-lo-gou-katafronh-sews-p-herc-336-1150 | Polystratus - Περὶ ἀλόγου καταφρονήσεως (P. Herc. 336-1150) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 5,072 | auto-corrected |
| polyzelus.fragmenta | Polyzelus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 312 | raw OCR |
| pompeius-macer.fragmentum | Pompeius Macer - Fragmentum | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 213 | raw OCR |
| porphyrius.chronica | Porphyrius - Chronica | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 2,163 | auto-corrected |
| porphyrius.contra-christianos-fragmenta | PORPHYRIUS - Contra Christianos (fragmenta, Harnack) | qwen36-harnack-porphyry | Qwen3.6-27B | 12,792 | raw OCR |
| porphyrius.ei-s-ta-rmonika-ptolemai-ou-u-po-mnhma | PORPHYRIUS - In Ptolemaei Harmonica commentarius | qwen36-porphyry-in-ptol-bub | Qwen3.6-27B | 64,280 | raw OCR |
| porphyrius.epistula-ad-anebonem | PORPHYRIUS - Epistula ad Anebonem | qwen36-parthey-anebonem | Qwen3.6-27B | 2,415 | raw OCR |
| posidippus.fragmenta | POSIDIPPUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 886 | raw OCR |
| potamon.fragmenta | Potamon - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 43 | raw OCR |
| pratinas.fragmenta | Pratinas - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 107 | raw OCR |
| praxilla.fragmenta | PRAXILLA - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 228 | raw OCR |
| priscianus.metaphrasis-in-theophrastum | Priscianus - Metaphrasis In Theophrastum | qwen36-priscianus_lydus_bywater | Qwen3.6-27B | 108,867 | auto-corrected |
| priscus-history.testimonia | Priscus - Testimonia | qwen36-priscus_dindorf_hgm1 | Qwen3.6-27B | 157 | auto-corrected |
| proclus.in-platonis-timaeum-commentaria | Proclus - In Platonis Timaeum Commentaria | qwen36-proclus_timaeus_v1 | Qwen3.6-27B | 553,283 | manual |
| proclus.institutio-theologica | Proclus - Institutio Theologica | qwen36-proclus_didot_et-1855 | Qwen3.6-27B | 29,050 | auto-corrected |
| procopius-rhetoric.commentarii-in-octateuchum | Procopius Gazaeus - Commentarii in Octateuchum (catena-epitome, CPG 7430; as served: Genesis through Judges) (PG087_1 loci 18-546) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 121,734 | manual |
| procopius-rhetoric.epistulae-1-166 | Procopius - Epistulae 1-166 | qwen36-aristaenetus_hercher_epistolographi-ocr | Qwen3.6-27B | 24,070 | auto-corrected |
| procopius-rhetoric.in-libros-regum-et-paralipomenon-scholia | Procopius Gazaeus - In libros Regum et Paralipomenon scholia (CPG 7431) (PG087_1 loci 547-617) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 24,504 | manual |
| procopius-rhetoric.in-proverbia | Procopius Gazaeus (attribution of the PG edition) - In Proverbia (catena-epitome, CPG 7432; Procopian authorship of the epitome doubted) (PG087_1 loci 618-779) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 61,870 | manual |
| prodicus.testimonia | Prodicus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 2,709 | auto-corrected |
| proros-amyclas-clinias.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 329 | raw OCR |
| protagoras.testimonia | Protagoras - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 4,474 | auto-corrected |
| pseudo-archytas.fragmenta | Pseudo-Archytas - Fragmenta | qwen36-archytas_mullach_fpg2-ocr | Qwen3.6-27B | 4,651 | auto-corrected |
| pseudo-codinus.de-annis-ab-orbe-condito | Pseudo-Codinus - De annis ab orbe condito (Chronicon breve, from Adam to 1453) (PG157 loci 325-332) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,653 | manual |
| pseudo-codinus.de-officiis-officia-palatii-constantinopoleos | Pseudo-Codinus - De officiis (De officialibus palatii Constantinopolitani et de officiis magnae ecclesiae) (PG157 loci 20-68) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 18,747 | manual |
| pseudo-codinus.patria-constantinopoleos | Pseudo-Codinus - Patria Constantinopoleos (Excerpta de antiquitatibus Constantinopolitanis) (PG157 loci 225-324) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 25,162 | manual |
| pseudo-justinus-martyr.cohortatio-ad-gentiles | Pseudo-Justinus Martyr - Cohortatio ad gentiles (PG006 loci 128-163) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,716 | manual |
| pseudo-justinus-martyr.confutatio-dogmatum-quorundam-aristotelicorum | Pseudo-Justinus Martyr - Confutatio dogmatum quorundam Aristotelicorum (PG006 loci 753-789) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 15,140 | manual |
| pseudo-justinus-martyr.de-monarchia | Pseudo-Justinus Martyr - De monarchia (PG006 loci 164-170) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,825 | auto-corrected |
| pseudo-justinus-martyr.de-resurrectione | Pseudo-Justinus Martyr - De resurrectione (PG006 loci 793-802) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,434 | manual |
| pseudo-justinus-martyr.epistula-ad-zenam-et-serenum | Pseudo-Justinus Martyr - Epistula ad Zenam et Serenum (PG006 loci 599-609) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,479 | auto-corrected |
| pseudo-justinus-martyr.expositio-rectae-fidei | Pseudo-Justinus Martyr - Expositio rectae fidei (PG006 loci 611-627) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,806 | manual |
| pseudo-justinus-martyr.fragmenta | Pseudo-Justinus Martyr - Fragmenta (PG006 loci 805-807) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 852 | auto-corrected |
| pseudo-justinus-martyr.oratio-ad-gentiles | Pseudo-Justinus Martyr - Oratio ad gentiles (PG006 loci 122-127) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,047 | auto-corrected |
| pseudo-justinus-martyr.quaestiones-christianorum-ad-gentiles | Pseudo-Justinus Martyr - Quaestiones Christianorum ad gentiles (PG006 loci 708-738) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 13,131 | manual |
| pseudo-justinus-martyr.quaestiones-et-responsiones-ad-orthodoxos | Pseudo-Justinus Martyr - Quaestiones et responsiones ad orthodoxos (PG006 loci 632-707) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 28,135 | manual |
| pseudo-justinus-martyr.quaestiones-gentilium-ad-christianos | Pseudo-Justinus Martyr - Quaestiones gentilium ad Christianos (PG006 loci 739-752) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,292 | manual |
| pseudo-symeon.chronographia-partim-edita-e-cod-paris-gr-1712 | Pseudo-Symeon (Symeon Magister ac Logothetes) - Chronographia / Annales a Leone Armenio ad Nicephorum Phocam (PG109 loci 337-416) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 30,963 | manual |
| pseudo-zonaras.lexicon | Pseudo-Zonaras - Lexicon | [archive.org](https://archive.org/details/lexiconextribus00albegoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 164,809 | manual |
| ptolemaeus-grammar.ptolemaeus-gramm-valckenaer-ammonius |  | qwen36-ptolemaeus_gramm_valckenaer_ammonius | Qwen3.6-27B | 55,321 | auto-corrected |
| pythagoras.testimonia | Pythagoras - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 6,587 | auto-corrected |
| pythagoristae-d-k.testimonia-et-fragmenta | Pythagoristae (D-K) - Testimonia Et Fragmenta | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 23,896 | auto-corrected |
| quadratus-apologeta.fragmentum-apologiae | Quadratus Apologeta - Fragmentum apologiae (apud Eusebium, HE 4.3) (PG005 loci 642-642) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 48 | raw OCR |
| rhianus.fragmenta | Rhianus - Fragmenta | qwen36-alexander_aetolus_meineke-ocr | Qwen3.6-27B | 2,075 | auto-corrected |
| rhinthon.fragmenta | Rhinthon - Fragmenta | qwen36-rhinthon_kaibel_cgf_1899 | Qwen3.6-27B | 37,598 | auto-corrected |
| rhodon.fragmenta | Rhodon - Fragmenta (ex libro adversus Marcionem, apud Eusebium HE 5.13) (PG005 loci 676-678) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 343 | auto-corrected |
| salmanas.me-qodos-di-h-s-potelei-tai-h-sfairoeidh-s-xa-laza | Salmanas - Μέθοδος δῑ ἧς ἀποτελεῖται ἡ σφαιροειδὴς χάλαζα κατασκευασθεῖσα παρὰ τοῦ ἐν τεχνουργίᾳ περιβοήτου Ἄραβος τοῦ Σαλμανᾶ (E Cod.Paris. B.N. Gr. 2327, Fol. 141R) | qwen36-berthelot_alchimistes_grec | Qwen3.6-27B | 955 | raw OCR |
| sannyrion.fragmenta | Sannyrion - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 81 | raw OCR |
| sappho.fragmenta | Sappho - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 5,099 | auto-corrected |
| satyrus.vita-euripidis-p-oxy-9-1176 | Vita Euripidis (P. Oxy. 9.1176) | qwen36-fhg_vol3_mueller_diocles_rhodius | Qwen3.6-27B | 451 | raw OCR |
| scholia-in-aelium-aristidem.scholia-in-aelium-aristidem-scholia-vetera | Scholia In Aelium Aristidem - Scholia In Aelium Aristidem (Scholia Vetera) | [archive.org](https://archive.org/details/scholiainaeliia00unkngoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 117,962 | auto-corrected |
| scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera | Scholia In Aeschinem - Scholia In Aeschinem (Scholia Vetera) | qwen36-schol_aeschin_dindorf | Qwen3.6-27B | 25,750 | auto-corrected |
| scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera | Scholia In Aeschylum - Scholia In Aeschylum (Scholia Vetera) | [archive.org](https://archive.org/details/bub_gb_aw-IxD1dCOwC) | Qwen3.6-27B-FP8 (masked 1-col pipeline, 350 dpi) | 119,911 | auto-corrected |
| scholia-in-apollonium-rhodium.scholia-in-apollonii-rhodii-argonautica-scholia-vetera | Scholia In Apollonium Rhodium - Scholia In Apollonii Rhodii Argonautica (Scholia Vetera) | [archive.org](https://archive.org/details/bub_gb_oBI-AAAAcAAJ) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 120,592 | auto-corrected |
| scholia-in-aratum.scholia-in-aratum-scholia-vetera | Scholia In Aratum - Scholia In Aratum (Scholia Vetera) | [archive.org](https://archive.org/details/Maass1898) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 157,686 | auto-corrected |
| scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii | Scholia In Aristophanem - Scholia In Acharnenses (Scholia Vetera Et Recentiora Triclinii) | [archive.org](https://archive.org/details/scholiagraecaina00dbuoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 354,055 | auto-corrected |
| scholia-in-callimachum.schol-callim-schneider |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 34,582 | auto-corrected |
| scholia-in-demosthenem.scholia-demosthenem-dindorf-v8 |  | qwen36-scholia_demosthenem_dindorf_v8 | Qwen3.6-27B | 109,808 | auto-corrected |
| scholia-in-hesiodum.scholia-in-opera-et-dies-scholia-vetera | Scholia In Hesiodum - Scholia In Opera Et Dies (Scholia Vetera) | [archive.org](https://archive.org/details/poetaeminoresgra02gais) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 174,839 | auto-corrected |
| scholia-in-lycophronem.scholia-in-lycophronem-scholia-vetera-et-recentiora-partim-isaac-et | Scholia In Lycophronem - Scholia In Lycophronem (Scholia Vetera Et Recentiora Partim Isaac Et Joannis Tzetzae) | [archive.org](https://archive.org/details/lycophronisalexa02lycouoft) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 107,688 | auto-corrected |
| scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora | Scholia In Oppianum - Scholia Et Glossae In Cynegetica (Scholia Vetera Et Recentiora) | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 6,032 | auto-corrected |
| scholia-in-oppianum.scholia-et-glossae-in-halieutica-scholia-vetera-et-recentiora | Scholia In Oppianum - Scholia Et Glossae In Halieutica (Scholia Vetera Et Recentiora) | qwen36-scholia_oppianum_bussemaker_didot-masked | Qwen3.6-27B-FP8 | 65,351 | auto-corrected |
| scholia-in-platonem.scholia-in-platonem-scholia-vetera | Scholia In Platonem - Scholia In Platonem (Scholia Vetera) | [archive.org](https://archive.org/details/platonisoperaom03wincgoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 177,660 | auto-corrected |
| scholia-in-theocritum.scholia-vetera-et-recentiora | Scholia In Theocritum - Scholia vetera et recentiora | [archive.org](https://archive.org/details/scholiaintheocri00buss) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 92,656 | auto-corrected |
| scholia-in-theonem.scholia-in-progymnasmata |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 1,138 | auto-corrected |
| scholia-in-xenophontem.scholia-in-anabasin-cyri-scholia-vetera | SCHOLIA IN XENOPHONTEM - Scholia in Xenophontis Anabasin | qwen36-expeditiocyri02xenogoog | Qwen3.6-27B | 4,214 | raw OCR |
| scythinus-poet-phil.fragmenta | Scythinus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 315 | auto-corrected |
| scythinus-poet-phil.testimonia | Scythinus - Testimonia | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 249 | raw OCR |
| scythinus.peri-physios |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 44 | raw OCR |
| secundus-mullach-fpg1 |  | qwen36-secundus_mullach_fpg1 | Qwen3.6-27B | 152,132 | auto-corrected |
| semonides.fragmenta | SEMONIDES - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 524 | raw OCR |
| serapion-scr-eccl.fragmenta | Serapion Antiochenus - Fragmenta (PG005 loci 696-697) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 194 | auto-corrected |
| serenus.de-sectione-cylindri | Serenus - De Sectione Cylindri | qwen36-serenus_heiberg_opuscula | Qwen3.6-27B | 34,332 | auto-corrected |
| severus-rhetor.diegemata-kai-ethopoiiai |  | qwen36-walz_rhetores_v1 | Qwen3.6-27B | 2,265 | auto-corrected |
| simias.fragmenta | Simias - Fragmenta | qwen36-simias_fraenkel | Qwen3.6-27B | 6,904 | auto-corrected |
| simonides-lyric.fragmenta-2 | Simonides - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,763 | auto-corrected |
| simus-myonides-euphranor.testimonia-et-fragmenta |  | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 104 | raw OCR |
| simylus.fragmentum | SIMYLUS - Fragmentum | kock-caf2-ocr-frag | Qwen3.6-27B | 35 | raw OCR |
| sminthes.titulus | Sminthes - Titulus | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 34 | auto-corrected |
| socrates-rhodius.socrates-hist-fhg4 |  | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 51,835 | auto-corrected |
| solon.fragmenta | Solon - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 1,900 | auto-corrected |
| sopater-comedy.fragmenta | Sopater - Fragmenta | qwen36-sopater_kaibel_cgf | Qwen3.6-27B | 32,797 | auto-corrected |
| sopater-rhetor.diairesis-zetematon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 90,079 | manual |
| sopater-rhetor.hypomnema-eis-ten-hermogenous-technen |  | qwen36-walz_rhetores_v5 | Qwen3.6-27B | 54,333 | auto-corrected |
| sophilus.fragmenta | Sophilus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 183 | auto-corrected |
| sophron.fragmenta | SOPHRON - Fragmenta | qwen36-sopater_kaibel_cgf | Qwen3.6-27B | 5,497 | auto-corrected |
| sosicrates.fragmenta | SOSICRATES - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 81 | auto-corrected |
| sosipater.fragmentum | SOSIPATER - Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 270 | raw OCR |
| sosiphanes.fragmenta | Sosiphanes - Fragmenta | qwen36-nauck_tgf_1889-ocr | Qwen3.6-27B | 366 | raw OCR |
| sositheus.fragmenta | Sositheus - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 448 | raw OCR |
| sosthenes.fragmenta | Sosthenes - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 106 | auto-corrected |
| sosylus-bilabel-papyrus1922 |  | qwen36-sosylus_bilabel_papyrus1922 | Qwen3.6-27B | 5,170 | auto-corrected |
| sotades-comedy.fragmenta | Sotades - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 53 | raw OCR |
| sotion.leipsana |  | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 288 | auto-corrected |
| sphaerus.fragmenta | Sphaerus - Fragmenta | qwen36-persaeus_svf1_arnim-ocr | Qwen3.6-27B | 558 | auto-corrected |
| stephanus-grammar.ethnica-epitome | Stephanus - Ethnica (Epitome) | [archive.org](https://archive.org/details/bub_gb_0NIPAAAAQAAJ) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 145,712 | raw OCR |
| stephanus.fragmentum | STEPHANUS - Fragmentum | kock-caf3-ocr-frag | Qwen3.6-27B | 99 | raw OCR |
| straton-philosophy.fragmenta | Straton - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 298 | raw OCR |
| strattis.fragmenta | Strattis - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 2,279 | auto-corrected |
| susarion.fragmentum | Susarion - Fragmentum | kock-caf1-ocr-frag | Qwen3.6-27B | 31 | raw OCR |
| symeon-thessalonicensis.de-matrimonio | Symeon Thessalonicensis - De honesto et legitimo matrimonio (chs. 276-281 of the dialogue) (PG155 loci 257-261) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,049 | manual |
| symeon-thessalonicensis.de-ordine-sepulturae | Symeon Thessalonicensis - De fine et exsequiarum ordine (De ordine sepulturae; chs. ~359-373 of the dialogue) (PG155 loci 341-353) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,652 | manual |
| symeon-thessalonicensis.de-poenitentia | Symeon Thessalonicensis - De poenitentia (chs. 251-275 of the dialogue) (PG155 loci 240-256) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 6,992 | manual |
| symeon-thessalonicensis.de-sacerdotio | Symeon Thessalonicensis - De sacerdotio (epistle to a devout monk) (PG155 loci 482-493) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,486 | manual |
| symeon-thessalonicensis.de-sacra-liturgia | Symeon Thessalonicensis - De sacra liturgia (chs. ~78-100 of the dialogue) (PG155 loci 132-157) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 11,486 | manual |
| symeon-thessalonicensis.de-sacra-precatione | Symeon Thessalonicensis - De sacra precatione (on the divine office; chs. 296-ca.358 of the dialogue) (PG155 loci 273-340) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 30,193 | manual |
| symeon-thessalonicensis.de-sacramentis | Symeon Thessalonicensis - De sacramentis (chs. 33-70 of the dialogue) (PG155 loci 94-124) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 13,518 | manual |
| symeon-thessalonicensis.de-sacris-ordinationibus | Symeon Thessalonicensis - De sacris ordinationibus (chs. 156-250 of the dialogue) (PG155 loci 186-239) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 22,031 | manual |
| symeon-thessalonicensis.de-sacro-templo | Symeon Thessalonicensis - De sacro templo et eius consecratione (chs. 101-155 of the dialogue) (PG155 loci 158-185) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 11,848 | manual |
| symeon-thessalonicensis.de-sancto-chrismate | Symeon Thessalonicensis - De sancto chrismate (chs. 71-77 of the dialogue) (PG155 loci 125-131) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,106 | manual |
| symeon-thessalonicensis.de-sancto-euchelaeo | Symeon Thessalonicensis - De sancto oleo / euchelaeo (chs. ~282-295 of the dialogue) (PG155 loci 262-272) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,654 | manual |
| symeon-thessalonicensis.dialogus-contra-haereses | Symeon Thessalonicensis - Dialogus in Christo adversus omnes haereses (chs. 1-32 of the great dialogue) (PG155 loci 22-93) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 32,146 | manual |
| symeon-thessalonicensis.expositio-de-divino-templo | Symeon Thessalonicensis - Expositio de divino templo (sent to the pious in Crete) (PG155 loci 354-380) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,460 | manual |
| symeon-thessalonicensis.expositio-de-sacri-symboli-dictionibus | Symeon Thessalonicensis - Expositio necessaria de sacri symboli dictionibus (PG155 loci 407-419) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,386 | manual |
| symeon-thessalonicensis.expositio-de-sacro-symbolo | Symeon Thessalonicensis - Expositio de sacro symbolo (exposition of the Creed) (PG155 loci 381-406) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 11,426 | manual |
| symeon-thessalonicensis.responsa-ad-gabrielem-pentapolitanum | Symeon Thessalonicensis - Responsa ad Gabrielem Pentapolitanum (questions and answers on liturgical and canonical matters) (PG155 loci 420-481) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 25,609 | manual |
| symmachus.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 39,549 | auto-corrected |
| synesius-philosophy.epistulae | Synesius - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 32,822 | auto-corrected |
| syrianus-sopater-marcellinus.scholia-eis-staseis-tou-hermogenous |  | qwen36-walz_rhetores_v4 | Qwen3.6-27B | 206,971 | auto-corrected |
| syrianus.eis-to-peri-ideon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,199 | auto-corrected |
| tatianus.fragmenta | Tatianus - Fragmenta (Tatiani fragmenta, PG 6, 1601-1608) (PG006 loci 808-809) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 290 | auto-corrected |
| teleclides.fragmenta | Teleclides - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 1,311 | raw OCR |
| telephus.fragmenta | Telephus - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 136 | raw OCR |
| telesilla.fragmenta | Telesilla - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 3,207 | auto-corrected |
| telestes.fragmenta | TELESTES - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 243 | auto-corrected |
| terpander.fragmenta-fort-auctore-terpandro | Terpander - Fragmenta (Fort. Auctore Terpandro) | bergk-plg3-ocr-frag | Qwen3.6-27B | 45 | raw OCR |
| thales.fragmenta | Thales - Fragmenta | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 4,008 | auto-corrected |
| thales.testimonia | Thales - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 7,246 | auto-corrected |
| theagenes-philosophy.testimonia | Theagenes - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 231 | raw OCR |
| theages.fragmenta | Theages - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 2,220 | auto-corrected |
| theano.fragmenta | Theano - Fragmenta | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 587 | auto-corrected |
| themison.fragmentum | Themison - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 2 | raw OCR |
| themistius.peri-filanqrwpi-as-h-kwnsta-ntios | THEMISTIUS - Orationes | qwen36-themistiioratio01dindgoog | Qwen3.6-27B | 157,937 | raw OCR |
| theodectas.fragmenta | Theodectas - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 1,046 | auto-corrected |
| theodoretus.commentaria-in-isaiam | Theodoretus - Commentaria In Isaiam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 44,728 | auto-corrected |
| theodoretus.de-providentia-orationes-decem | Theodoretus - De Providentia Orationes Decem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 46,560 | auto-corrected |
| theodoretus.epistulae-collectio-sirmondiana-epistulae-1-95 | Theodoretus - Epistulae: Collectio Sirmondiana (Epistulae 1-95) | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 53,742 | auto-corrected |
| theodoretus.eranistes | Theodoretus - Eranistes | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 52,470 | auto-corrected |
| theodoretus.explanatio-in-canticum-canticorum | Theodoretus - Explanatio In Canticum Canticorum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 32,516 | auto-corrected |
| theodoretus.graecarum-affectionum-curatio | Theodoretus - Graecarum Affectionum Curatio | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 70,301 | auto-corrected |
| theodoretus.haereticarum-fabularum-compendium | Theodoretus - Haereticarum Fabularum Compendium | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 36,689 | auto-corrected |
| theodoretus.interpretatio-in-ezechielem | Theodoretus - Interpretatio In Ezechielem | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 132,992 | auto-corrected |
| theodoretus.interpretatio-in-jeremiam | Theodoretus - Interpretatio In Jeremiam | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 47,139 | auto-corrected |
| theodoretus.interpretatio-in-psalmos | Theodoretus - Interpretatio In Psalmos | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 178,942 | auto-corrected |
| theodoretus.interpretatio-in-xii-prophetas-minores | Theodoretus - Interpretatio In Xii Prophetas Minores | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 74,748 | auto-corrected |
| theodoretus.interpretatio-in-xiv-epistulas-sancti-pauli | Theodoretus - Interpretatio In Xiv Epistulas Sancti Pauli | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 147,306 | auto-corrected |
| theodoretus.libellus-contra-nestorium-ad-sporacium-sp | Theodoretus - Libellus Contra Nestorium Ad Sporacium [Sp.] | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 1,433 | auto-corrected |
| theodoretus.quaestiones-in-libros-regnorum-et-paralipomenon | Theodoretus - Quaestiones In Libros Regnorum Et Paralipomenon | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 58,252 | auto-corrected |
| theodoretus.quaestiones-in-octateuchum | Theodoretus - Quaestiones In Octateuchum | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 66,747 | auto-corrected |
| theodorus-agallianus.refutatio-contra-joannem-argyropulum | Theodorus Agallianus - Refutatio (dialogus) contra Ioannem Argyropulum (PG158 loci 541-560) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 16,597 | manual |
| theodorus-mathematics.testimonia | Theodorus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 352 | raw OCR |
| theodosius.canones-isagogici-de-flexione-nominum | Canones isagogici de flexione nominum | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 14,153 | raw OCR |
| theodosius.canones-isagogici-de-flexione-verborum | Canones isagogici de flexione verborum | [archive.org](https://archive.org/details/GrammaticiGraeciVolume4) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 16,890 | raw OCR |
| theodotion.fragmenta | Fragmenta (Hexapla, Greek columns) | [Field, Origenis Hexaplorum quae supersunt](https://archive.org/details/origenishexaplor01orig) | Qwen3.6-27B | 23,323 | auto-corrected |
| theognetus.fragmenta | THEOGNETUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 135 | raw OCR |
| theognis-elegy.elegiae | Theognis - Elegiae | [Bergk, Poetae Lyrici Graeci II (elegiac+iambic)](https://archive.org/search?query=Poetae+Lyrici+Graeci+Bergk) | Qwen3.6-27B | 3,239 | auto-corrected |
| theognis-history.fragmentum | Theognis - Fragmentum | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 239 | auto-corrected |
| theognis-tragedy.fragmentum | Theognis - Fragmentum | qwen36-nauck_tgf_1889 | Qwen3.6-27B | 113,477 | auto-corrected |
| theognostus.canones-sive-de-orthographia | Theognostus - Canones Sive De Orthographia | [archive.org](https://archive.org/details/anecdotagrcaeco00fragoog) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 150,818 | auto-corrected |
| theophanes-continuatus.chronographia-lib-1-6 | Theophanes Continuatus - Chronographia (lib. 1-6) (PG109 loci 13-255) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 95,235 | manual |
| theophilus-comedy.fragmenta | Theophilus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 414 | raw OCR |
| theophylactus-achridensis.de-iis-quorum-latini-incusantur | Theophylactus Achridensis - De iis quorum Latini incusantur (Allocutio cuidam ex suis familiaribus) (PG126 loci 118-132) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,352 | manual |
| theophylactus-achridensis.enarratio-in-evangelium-joannis | Theophylactus Achridensis - Enarratio in Evangelium Joannis (complete across two volumes: PG123 John 1-7 + PG124 John 7:52-21:25) (PG124 loci 10-164) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 117,346 | manual |
| theophylactus-achridensis.enarratio-in-evangelium-lucae | Theophylactus Achridensis - Enarratio in Evangelium Lucae (with prefatory vitae, hypothesis and kephalaia) (PG123 loci 347-568) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 97,447 | manual |
| theophylactus-achridensis.enarratio-in-evangelium-marci | Theophylactus Achridensis - Enarratio in Evangelium Marci (with prefatory vitae and kephalaia) (PG123 loci 249-346) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 38,996 | manual |
| theophylactus-achridensis.enarratio-in-evangelium-matthaei | Theophylactus Achridensis - Enarratio in Evangelium Matthaei (with prefatory Ps.-Sophronius vita and kephalaia) (PG123 loci 75-248) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 71,475 | manual |
| theophylactus-achridensis.epistulae | Theophylactus Achridensis - Epistulae (collected letters, ca. 75 in the PG numbering) (PG126 loci 161-286) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 45,441 | manual |
| theophylactus-achridensis.expositio-in-acta-apostolorum-sp | Pseudo-Theophylactus - Expositio in Acta apostolorum (third, compendious text: brief scholia) (PG125 loci 538-572) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 29,243 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-colossenses | Theophylactus Achridensis - Expositio in Epistolam ad Colossenses (with prefixed hypothesis) (PG124 loci 608-644) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 13,841 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-ephesios | Theophylactus Achridensis - Expositio in Epistolam ad Ephesios (with prefixed hypothesis, its opening words lost in the OCR) (PG124 loci 521-574) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 20,495 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-galatas | Theophylactus Achridensis - Expositio in Epistolam ad Galatas (with prefixed hypothesis) (PG124 loci 481-520) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 15,170 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-hebraeos | Theophylactus Achridensis - Expositio in epistolam ad Hebraeos (PG125 loci 100-209) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 42,985 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-philemonem | Theophylactus Achridensis - Expositio in epistolam ad Philemonem (PG125 loci 93-99) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,298 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-philippenses | Theophylactus Achridensis - Expositio in Epistolam ad Philippenses (with prefixed hypothesis) (PG124 loci 575-607) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 12,018 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-romanos | Theophylactus Achridensis - Expositio in Epistolam ad Romanos (with prefixed hypothesis) (PG124 loci 173-284) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 43,313 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ad-titum | Theophylactus Achridensis - Expositio in epistolam ad Titum (PG125 loci 78-92) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,116 | manual |
| theophylactus-achridensis.expositio-in-epistolam-catholicam-jacobi | Theophylactus Achridensis (attributed) - Expositio in epistolam catholicam S. Jacobi (PG125 loci 573-601) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,189 | manual |
| theophylactus-achridensis.expositio-in-epistolam-i-ad-corinthios | Theophylactus Achridensis - Expositio in Epistolam I ad Corinthios (with prefixed hypothesis) (PG124 loci 285-402) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 44,314 | manual |
| theophylactus-achridensis.expositio-in-epistolam-i-ad-thessalonicenses | Theophylactus Achridensis - Expositio in Epistolam I ad Thessalonicenses (PG124 loci 645-668) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 8,530 | manual |
| theophylactus-achridensis.expositio-in-epistolam-i-ad-timotheum | Theophylactus Achridensis - Expositio in epistolam I ad Timotheum (PG125 loci 12-50) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 13,974 | manual |
| theophylactus-achridensis.expositio-in-epistolam-i-joannis | Theophylactus Achridensis - Expositio in epistolam I Joannis (PG126 loci 12-40) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 12,372 | manual |
| theophylactus-achridensis.expositio-in-epistolam-i-petri | Theophylactus Achridensis (attributed) - Expositio in epistolam I S. Petri (PG125 loci 602-633) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 12,115 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ii-ad-corinthios | Theophylactus Achridensis - Expositio in Epistolam II ad Corinthios (with prefixed hypothesis) (PG124 loci 403-480) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 28,922 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ii-ad-thessalonicenses | Theophylactus Achridensis - Expositio in Epistolam II ad Thessalonicenses (with prefixed hypothesis) (PG124 loci 669-684) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,925 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ii-ad-timotheum | Theophylactus Achridensis - Expositio in epistolam II ad Timotheum (PG125 loci 51-77) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 9,606 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ii-joannis | Theophylactus Achridensis - Expositio in epistolam II Joannis (PG126 loci 41-46) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,169 | manual |
| theophylactus-achridensis.expositio-in-epistolam-ii-petri | Theophylactus Achridensis (attributed) - Expositio in epistolam II S. Petri (PG125 loci 634-651) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 6,563 | manual |
| theophylactus-achridensis.expositio-in-epistolam-iii-joannis | Theophylactus Achridensis - Expositio in epistolam III Joannis (PG126 loci 47-49) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 829 | manual |
| theophylactus-achridensis.expositio-in-epistolam-judae | Theophylactus Achridensis - Expositio in epistolam Judae (PG126 loci 50-59) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,492 | manual |
| theophylactus-achridensis.expositio-in-prophetam-habacuc | Theophylactus Achridensis - Expositio in prophetam Habacuc (PG126 loci 417-459) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 15,641 | manual |
| theophylactus-achridensis.expositio-in-prophetam-jonam | Theophylactus Achridensis - Expositio in prophetam Jonam (PG126 loci 460-491) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 11,936 | manual |
| theophylactus-achridensis.expositio-in-prophetam-michaeam | Theophylactus Achridensis - Expositio in prophetam Michaeam (PG126 loci 532-602) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 25,424 | manual |
| theophylactus-achridensis.expositio-in-prophetam-nahum | Theophylactus Achridensis - Expositio in prophetam Nahum (PG126 loci 492-531) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 14,641 | manual |
| theophylactus-achridensis.expositio-in-prophetam-oseam | Theophylactus Achridensis - Expositio in prophetam Oseam (with dedicatory prologue and Prooemium in prophetas) (PG126 loci 289-416) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 46,997 | manual |
| theophylactus-achridensis.historia-martyrii-xv-martyrum-tiberiopolitanorum | Theophylactus Achridensis - Historia martyrii XV martyrum Tiberiopolitanorum (BHG 1199) (PG126 loci 83-117) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 12,879 | manual |
| theophylactus-achridensis.in-acta-apostolorum-commentarius-alter-sp | Pseudo-Theophylactus - In Acta apostolorum commentarius alter (second text, with ΠΡΟΛΟΓΟΣ ΘΕΟΦΥΛΑΚΤΟΥ; TEXTUS/ΕΡΜΗΝΕΙΑ alternation) (PG125 loci 432-537) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 40,312 | manual |
| theophylactus-achridensis.in-acta-apostolorum-commentarius-sp | Pseudo-Theophylactus - In Acta apostolorum commentarius (first, longer text; catena compiled largely from Chrysostom; Theophylact attribution rejected) (PG125 loci 249-431) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 63,165 | manual |
| theophylactus-achridensis.institutio-regia | Theophylactus Achridensis - Institutio regia (Paideia basilike, ad Constantinum Ducam porphyrogenitum) (PG126 loci 134-150) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,019 | manual |
| theophylactus-achridensis.oratio-in-imperatorem-alexium-i-comnenum | Theophylactus Achridensis - Oratio in imperatorem Alexium I Comnenum (PG126 loci 151-160) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 3,639 | manual |
| theophylactus-achridensis.oratio-in-praesentationem-deiparae | Theophylactus Achridensis - Oratio in praesentationem Deiparae (PG126 loci 72-79) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 2,639 | manual |
| theophylactus-achridensis.oratio-in-venerationem-crucis | Theophylactus Achridensis - Oratio in venerationem crucis (mid-Lent sermon; conventional title) (PG126 loci 60-71) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,289 | manual |
| theophylactus-achridensis.supplementum-in-evangelium-joannis | Theophylactus Achridensis (attributed) - Conclusion-fragment of a commentary on the Gospel of John (Jo 21:22-25 with account of John's death; supplement to the In Joannem) (PG126 loci 80-82) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 867 | auto-corrected |
| theophylactus-achridensis.vita-clementis-ohridensis | Theophylactus Achridensis - Vita Clementis Ohridensis (the long life, BHG 355) (PG126 loci 604-633) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 10,012 | manual |
| theophylactus-simocatta.epistulae | Theophylactus Simocatta - Epistulae | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 7,582 | auto-corrected |
| theophylactus-simocatta.excerpta-de-legationibus | Theophylactus Simocatta - Excerpta de legationibus (PG113 loci 475-487, cut at a character offset) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 4,782 | manual |
| theopompus-comedy.fragmenta | Theopompus - Fragmenta | kock-caf1-ocr-frag | Qwen3.6-27B | 1,876 | auto-corrected |
| theopompus-history.testimonia | Theopompus - Testimonia | qwen36-theopompus_hist_fhg1 | Qwen3.6-27B | 23,594 | auto-corrected |
| thespis.fragmenta | Thespis - Fragmenta | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 262 | raw OCR |
| thrasymachus.testimonia | Thrasymachus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 1,086 | auto-corrected |
| thugenides.fragmenta | THUGENIDES - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 144 | raw OCR |
| tiberianus.epistula-ad-trajanum-de-christianis | Tiberianus (praeses Palaestinae, pseudepigraphon ap. Joannem Malalam) - Epistula Tiberiani ad Trajanum de Christianis (PG005 loci 505-505) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 59 | auto-corrected |
| timaeus-philosophy.fragmenta-et-titulus-sp | Timaeus - Fragmenta Et Titulus [Sp.] | qwen36-archytas_mullach_fpg2 | Qwen3.6-27B | 3,691 | auto-corrected |
| timaeus-philosophy.testimonia | Timaeus - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 135 | raw OCR |
| timaeus-sophista.lexicon-platonicum | Timaeus Sophista - Lexicon Platonicum (e cod. Coislin. 345) | [archive.org](https://archive.org/details/timaiousophistou00tima) | Qwen3.6-27B-FP8 (masked 2-col pipeline, 430 dpi) | 34,586 | auto-corrected |
| timagenes.fragmenta | Timagenes - Fragmenta | qwen36-aristobulus_fhg3 | Qwen3.6-27B | 399 | auto-corrected |
| timagoras.fragmenta | Timagoras - Fragmenta | qwen36-socrates_hist_fhg4 | Qwen3.6-27B | 319 | auto-corrected |
| timocles-comedy.fragmenta | Timocles - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 1,581 | raw OCR |
| timocreon.fragmenta | TIMOCREON - Fragmenta | bergk-plg3-ocr-frag | Qwen3.6-27B | 261 | auto-corrected |
| timon.fragmenta-et-tituli | Timon - Fragmenta Et Tituli | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 7,676 | auto-corrected |
| timosthenes-ggm1 |  | qwen36-timosthenes_ggm1 | Qwen3.6-27B | 104,827 | auto-corrected |
| timostratus.fragmenta | TIMOSTRATUS - Fragmenta | kock-caf3-ocr-frag | Qwen3.6-27B | 182 | raw OCR |
| timotheus-comedy.fragmenta | Timotheus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 80 | raw OCR |
| timotheus-grammar.timotheus-gaza-haupt-opuscula |  | qwen36-timotheus_gaza_haupt_opuscula | Qwen3.6-27B | 16,665 | auto-corrected |
| timotheus-history.timotheus-defluviis-ggm2 |  | qwen36-timotheus_defluviis_ggm2 | Qwen3.6-27B | 181,964 | auto-corrected |
| timotheus-lyric.fragmenta | Timotheus - Fragmenta | qwen36-timotheus_perser_wilamowitz | Qwen3.6-27B | 5,430 | auto-corrected |
| titanomachia.titanomachia-fragmenta | Titanomachia - Titanomachia (Fragmenta) | qwen36-panyassis_kinkel_egf-ocr | Qwen3.6-27B | 452 | auto-corrected |
| tlg0129.fragmenta | Fragmenta | [Kinkel, Epicorum Graecorum Fragmenta I](https://archive.org/search?query=Epicorum+Graecorum+Fragmenta+Kinkel) | Qwen3.6-27B | 2,199 | auto-corrected |
| tlg1140.tlg001 | ANTICLIDES - Fragmenta | qwen36-anticlides-bub | Qwen3.6-27B | 2,785 | raw OCR |
| tlg1235.fragmenta | Fragmenta | qwen36-clearchus_soli_fhg2-ocr | Qwen3.6-27B | 98 | raw OCR |
| tlg1595.tlg003 | Stoicorum Historia / Index Stoicorum (P.Herc. 1018) | [Philodemus, Stoicorum Historia (Index Stoicorum), ed. Comparetti, Rivista di Filologia 3, 1875](https://archive.org/details/rivistadifilolog03toriuoft) | Qwen3.6-27B | 2,256 | auto-corrected |
| tlg1595.tlg120 | PHILODEMUS - De morte liber IV | qwen36-sitzungsbericht308klasgoog | Qwen3.6-27B | 7,204 | raw OCR |
| tlg1595.tlg210 | De musica lib. iv | [Philodemus, De musica, ed. Kemke, Teubner 1884](https://archive.org/details/philodemidemusic00phil) | Qwen3.6-27B | 13,240 | auto-corrected |
| tlg1595.tlg241 | De oeconomia | [Philodemus, De oeconomia, ed. Jensen, Teubner 1906](https://archive.org/details/philodemiperioik00phil) | Qwen3.6-27B | 11,598 | auto-corrected |
| tlg1595.tlg267 | De ira (Peri orges) | [Philodemus, De ira (editio princeps), ed. Gomperz 1864](https://archive.org/details/philodemiepicur00philgoog) | Qwen3.6-27B | 7,946 | auto-corrected |
| tlg1595.tlg271 | De libertate dicendi (Peri parrhesias) | [Philodemus, De libertate dicendi, ed. Olivieri, Teubner 1914](https://archive.org/details/philodemiperipar00philuoft) | Qwen3.6-27B | 7,690 | auto-corrected |
| tlg1595.tlg289 | De poematis lib. ii | [Philodemus, De poematis lib. ii, ed. Hausrath](https://archive.org/details/philodemiperipoi00haus) | Qwen3.6-27B | 1,856 | auto-corrected |
| tlg1595.tlg472 | De signis (Peri semeion kai semeioseon) | [Philodemus, De signis (Peri semeioseon), ed. Gomperz, Herkulanische Studien 1, 1865](https://archive.org/details/philodemberindu00gompgoog) | Qwen3.6-27B | 4,471 | auto-corrected |
| tlg1595.tlg492 | De bono rege secundum Homerum | [Philodemus, De bono rege secundum Homerum, ed. Olivieri, Teubner 1909](https://archive.org/details/philodemiperitou00philuoft) | Qwen3.6-27B | 6,428 | auto-corrected |
| tlg1598.fragmenta | Fragmenta | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 78 | raw OCR |
| tlg2524.fragmenta | Fragmenta | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 162 | auto-corrected |
| tlg2637.fragmenta | Fragmenta | qwen36-nicostratus_fhg4-ocr | Qwen3.6-27B | 578 | auto-corrected |
| tlg4049.tlg001 | THOMAS MAGISTER - Ecloga nominum et verborum Atticorum | qwen36-thomaemagistrisi00thomuoft | Qwen3.6-27B | 77,512 | raw OCR |
| tlg4075.tlg001 | MARINUS - Vita Procli | qwen36-marinus-bub | Qwen3.6-27B | 21,561 | raw OCR |
| tomus-synodalis-anni-1351.tomus-synodalis-anni-1351 | Tomus synodalis anni 1351 - Tomus synodalis anni 1351 (PG151 loci 366-389) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 15,194 | manual |
| tomus-synodalis-contra-prochorum-cydonem.tomus-synodalis-contra-prochorum-cydonem | Tomus synodalis contra Prochorum Cydonem - Tomus synodalis contra Prochorum Cydonem (PG151 loci 354-365) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 9,938 | manual |
| tomus-synodicus-contra-barlaam-et-acindynum.tomus-synodicus-contra-barlaam-et-acindynum | Tomus synodicus contra Barlaam et Acindynum - Tomus synodicus contra Barlaam et Acindynum (PG151 loci 347-353) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 5,379 | manual |
| tragica-adespota.fragmenta | Tragica Adespota - Fragmenta | nauck-tgf-ocr-frag | Qwen3.6-27B | 11,439 | auto-corrected |
| troilus-sophista.prolegomena-tes-rhetorikes-hermogenous |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,254 | manual |
| tyrtaeus.fragmenta | Tyrtaeus - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 953 | auto-corrected |
| ulpianus.prolegomena-in-demosthenis-orationes-olynthiacas-et-philippicas | Ulpianus - Prolegomena In Demosthenis Orationes Olynthiacas Et Philippicas | qwen36-scholia_demosthenem_dindorf_v8-ocr | Qwen3.6-27B | 5,231 | auto-corrected |
| vita-basilii-iunioris.excerpta | Anonymus (hagiographus) - Excerpta e Vita S. Basilii iunioris (BHG 263) (PG109 loci 332-336) | [calfa-co Patrologia Graeca](https://github.com/calfa-co/Patrologia-Graeca) | calfa-co | 1,727 | manual |
| xenarchus.fragmenta | Xenarchus - Fragmenta | kock-caf2-ocr-frag | Qwen3.6-27B | 407 | raw OCR |
| xeniades.testimonium | Xeniades - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 43 | auto-corrected |
| xenocles.fragmentum | Xenocles - Fragmentum | [Nauck, Tragicorum Graecorum Fragmenta 2nd ed.](https://archive.org/search?query=Tragicorum+Graecorum+Fragmenta+Nauck) | Qwen3.6-27B | 143 | raw OCR |
| xenomedes.fragmenta | Xenomedes - Fragmenta | qwen36-clearchus_soli_fhg2 | Qwen3.6-27B | 840 | auto-corrected |
| xenophanes.fragmenta | Xenophanes - Fragmenta | bergk-plg2-ocr-frag | Qwen3.6-27B | 491 | raw OCR |
| xenophanes.fragmenta-silli-et-de-natura | Xenophanes - Fragmenta (Silli Et De Natura) | qwen36-empedocles_diels_ppf | Qwen3.6-27B | 6,887 | auto-corrected |
| xenophanes.testimonia | Xenophanes - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 11,571 | auto-corrected |
| xenophilus.testimonia | Xenophilus - Testimonia | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 110 | raw OCR |
| xuthus.testimonium | Xuthus - Testimonium | qwen36-nausiphanes_diels_fvs2 | Qwen3.6-27B | 140 | raw OCR |
| zeno-citieus.testimonia-et-fragmenta | Zeno - Testimonia Et Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 14,161 | auto-corrected |
| zeno-philosophy.testimonia | Zeno - Testimonia | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 6,751 | auto-corrected |
| zeno-tarsensis.fragmenta | Zeno - Fragmenta | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 174 | raw OCR |
| zonaeus.peri-schematon-ton-kata-logon |  | [Migne PG scans](https://www.roger-pearse.com/weblog/patrologia-graeca-pg-pdfs/) | Qwen3.6-27B | 3,305 | auto-corrected |
| zosimus-alchemista.opera | Opera | qwen36-berthelot_alchimistes_grec-ocr | Qwen3.6-27B | 40,877 | auto-corrected |
<!-- OCR-PROVENANCE:END -->

## Status

- ~3,820 works ingested, ~66.7M Greek tokens, twelve sources.
- ~66% of the TLG inventory's words actually ingested (49.5M of 75M;
  `data/coverage_report.json` has the per-bucket breakdown).
- Per-lemma frequency is built from the whole corpus. Counts are facts, not
  copyrightable; use them freely.
- The byzantium.gr works now carry real citation loci read from each page's
  own markers (book/chapter, Psellos book.section, Theophanes annus mundi,
  Skylitzes reign.chapter, ...); only Attaliates, whose page prints no
  structure, keeps page-paragraph indices.
- A printed leaf the upstream OCR delivered twice is dropped by
  scripts/drop_duplicate_leaf.py, with the scan page cited and every run of 3+
  words the dropped copy has and the kept copy lacks enumerated in
  data/duplicate_leaves.json; an unlisted run stops the run, so what is removed
  is duplicated text rather than text. PG118 pages 21-22 were the first case,
  1,063 tokens that had been served and counted twice.
  scripts/sweep_duplicate_leaves.py looks for the rest, and is the first search
  for them: the drop_duplicates list inside carve_cgpg_volume.py is curated by
  hand (ten groups in two volumes) and its difflib test only verifies pairs
  somebody already named. The sweep compares every pair of page-level OCR rows
  inside a file by word-bigram containment, which ignores reading order, because
  a second read that walks the columns differently scores 0.482 by difflib and
  0.841 by containment. Its output,
  data/duplicate_leaf_candidates.json, lists 49 remaining pairs in 17 files and
  splits them by what dropping one would cost, in BOTH directions. 19 pairs have
  a side that holds nothing the other lacks, 7,007 tokens, of which 12 pairs and
  4,361 tokens are in served text; the other 30 pairs, 11,469 tokens, cannot be
  dropped from either side, because each holds text the other does not. Which
  side to drop is never the earlier one by default: in PG126 the earlier copy
  was the stray and the later was the page that continues the text. Each pair
  still needs its page read.
- The multi-work CGPG Migne volumes are carved into per-work files: 21 of the
  22 researched volumes split (~167 primary works incl. the Theophylact of
  Ohrid corpus, Symeon of Thessalonica, Nicephorus Callistus' church history,
  Leo VI, the Psellus opuscula; 18 displaced witnesses to corpus_secondary),
  each with a reversible token-exact audit in data/corpus_changes/. 12
  `cogPG.*` files remain volume-keyed (11 files): ten leftovers of carved volumes
  (PG113, PG139 and PG112 among them, so 89,914 tokens between them, 75,862 of
  that PG112's uncarved half) and one uncarved volume (PG003, 160,260 tokens).
  Where a work's boundary falls inside a row, which whole-row carving cannot
  express, scripts/split_carved_row.py cuts the row at a character offset; it
  served PG118's three Euthalian pieces and then finished PG151, whose last row
  was column-interleaved and needed two separate pieces of one row joined. PG003 is deferred on the
  evidence (Dionysius/Pachymeres, blocked on display heads the OCR dropped, not
  on the passage-level interleave the record used to claim; see the
  split-deferred flag record). PG112 is CARVED as of 2026-08-08, but only half:
  the Canon splits De cerimoniis by edition, tlg3023.011 being Vogt (lib. 1.1-92
  in his numbering) and tlg3023.010 Reiske (lib. 1.84-2.56 in his), and Vogt's 92
  book-1 chapters are Reiske's 83, so the two are complementary halves rather
  than overlapping scopes. Loci 354-730 are the Reiske half and are now served
  as a work in their own right; loci 44-353 are the same text byzantium.gr
  already serves and stay volume-keyed until the rank call on issue #8 says
  whether to keep them as an edition witness.
  PG067 carved to TWO SECONDARY witnesses and no primary, so the published
  primary corpus is 220,569 tokens smaller than before it: the volume is
  Socrates Scholasticus and Sozomen end to end, and both histories are already
  served from First1KGreek, so the precedence ladder keeps the Migne OCR as a
  witness rather than serving it twice. That is the ladder working, not text
  going missing, but it does move every downstream count.
- Next: settle PG112's rank, then per-work citation loci for the carved CGPG
  works (now page-keyed `<VOL>.<page>`). PG003 is NOT a carve-on-loci job, which
  an earlier version of this line said it was: its boundaries fall inside rows
  and the splitter moves whole rows, so it needs intra-row segmentation as well
  as a re-OCR that keeps the display heads.

## License

Aggregated open editions: CC BY-SA 4.0, with attribution to First1KGreek
(OpenGreekAndLatin) and Perseus; per-work source in `coverage.json`. Our OCR of
public-domain editions: CC BY 4.0. Derived tables (frequency, coverage) are
facts and carry no additional copyright. See `LICENSE`.
