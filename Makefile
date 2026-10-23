# Regenerate the open-corpus yardstick and the sourcing artifacts.
#
# The yardstick (public_lexicon.tsv + per-lemma frequency) is defined by cog's
# OWN ingested corpus, and must grow whenever a TLG-only work is replaced by an
# open/PD source. The chain is therefore:
#
#   ingest  -> data/corpus/*.jsonl + corpus_editions.json   (TEI/transcription works;
#              the OCR works arrive already-corrected from the upstream OCR pipeline)
#   roll up -> public_lexicon.tsv + coverage.json           (the yardstick)
#           -> public_lemma_frequency.tsv                    (per-lemma counts)
#   source  -> source_overrides.json                         (precedence overrides)
#           -> source_registry.json + coverage_report.json   (verdict + the gap)
#
# Outputs are byte-stable (sorted, no wall-clock), so re-committing regenerated
# files is churn-free. That is a property of the OUTPUTS, not a promise that a
# target is cheap to ask for: no goal here is a leaf, and `make reports` is the
# one to watch. Its chain runs back through corpus_editions.json to the three
# ingesters and the id layer, then forward through the yardstick, before any
# report runs - twelve commands, and one of them
# (scripts/build_byzantium_gr_corpus.py) goes to byzantium.gr over the network
# for any page missing from data/cache/byzantium_gr/, which is gitignored and so
# is empty in a fresh clone. Whether that happens turns on mtimes, not content,
# and a clone stamps every file at checkout time in no useful order, so run
# `make -n <goal>` first if the network matters. To rebuild one report without
# the chain, run its script directly.
#
#   make            # full chain
#   make yardstick  # just the lexicon + lemma frequency
#   make sourcing   # just overrides + registry + coverage report
#   make reports    # the per-corpus reports (quality, per-work lemmas, the
#                   # README provenance table), plus whatever of the ingest
#                   # chain and the yardstick is out of date ahead of them
#
# build_lemma_frequency needs the Dilemma lemmatizer importable; point DILEMMA at
# its checkout (default ../dilemma) or pre-set PYTHONPATH.

PY       ?= python3
MIN_COUNT ?= 5
DILEMMA  ?= ../dilemma
FIRST1K_DIR ?= sources/first1k
PERSEUS_DIR ?= sources/perseus

CORPUS_EDITIONS := data/corpus_editions.json
LEXICON         := data/public_lexicon.tsv
ELISION_RATES   := data/elision_rates.json
GRAVE_RESIDUE   := data/grave_residue.json
DUP_LEAVES      = data/duplicate_leaf_candidates.json
DUP_PAGES       = data/duplicate_page_candidates.json
NONFINAL_GRAVES = data/nonfinal_graves.json
KNOWN_LIMITATIONS = data/known_limitations.json
LATIN_IN_GREEK  := data/latin_in_greek_script.json
SPACING_MARKS   := data/spacing_mark_classes.json
MERGE_SAMPLE    := data/duplicate_read_merge_sample.json
MERGE_GUESSES   := data/duplicate_read_merge_guesses.json
PG003_HEADS     = data/pg003_heads.json
PG003_GEOM      := data/pg003_head_geometry.json
PG003_ALT       := data/pg003_alternation.json
LEMMA_FREQ      := data/public_lemma_frequency.tsv
OVERRIDES       := data/source_overrides.json
REGISTRY        := data/source_registry.json
COVERAGE_REPORT := data/coverage_report.json
CROSSWALK_REPORT := data/crosswalk_report.json
CROSSWALK       := data/tlg_crosswalk.json
QUALITY_REPORT  := data/ocr_quality_report.json
PHOTIUS_CURRENT_ASSESSMENT := data/audits/photius-historical-readings-current.json.gz
PHOTIUS_REVIEW_STATUS := data/corpus_changes/photius-bekker-complete-review/review-status.json.gz
PHOTIUS_REVIEW_INPUTS := scripts/build_photius_review_observations.py \
    scripts/photius_complete_review_table.py \
    scripts/prepare_photius_review_campaign.py scripts/audit_compression.py \
    scripts/assess_photius_historical.py \
    $(wildcard scripts/photius_complete_observations_*.py) \
    data/corpus_changes/photius-bekker-complete-review/scope.json \
    data/corpus_changes/photius-bekker-complete-review/before-corpus.jsonl.gz
PHOTIUS_LATER_INPUTS := scripts/repair_photius_context.py \
    scripts/repair_photius_uncertainties.py scripts/photius_uncertainty_observations.py \
    scripts/repair_photius_uncertainty_admission.py scripts/check_photius_pilot_predecessor.py \
    scripts/repair_photius_editorial_substitutions.py scripts/prepare_photius_editorial_substitutions.py \
    scripts/repair_photius_editorial_continuation.py scripts/prepare_photius_editorial_continuation.py \
    scripts/photius_remaining_context.py scripts/photius_remaining_roles.py scripts/photius_remaining_words.py \
    $(wildcard scripts/photius_remaining_manual_*.py) \
    scripts/photius_current_state.py scripts/check_photius_predecessor.py \
    scripts/repair_photius_final_review.py scripts/photius_final_boundary_observations.py \
    scripts/photius_final_source_observations.py \
    scripts/prepare_photius_uncertainty_pilot.py scripts/photius_uncertainty_pilot_observations.py \
    scripts/fetch_photius_uncertainty_sources.py \
    $(wildcard data/corpus_changes/photius-bekker-context/* \
               data/corpus_changes/photius-bekker-uncertainties/* \
               data/corpus_changes/photius-bekker-uncertainties/sources/* \
               data/corpus_changes/photius-bekker-uncertainties/source-images/* \
               data/corpus_changes/photius-bekker-uncertainty-admission/* \
               data/corpus_changes/photius-bekker-editorial-substitutions/* \
               data/corpus_changes/photius-bekker-editorial-continuation/* \
               data/corpus_changes/photius-bekker-final-review/*)
SOURCE_COMPONENTS := data/source_component_tokens.json
WORK_LEMMAS     := data/work_lemma_counts.tsv.gz
CATALOG         := data/corpus_catalog.tsv
POLYTONIC_REPORT := data/polytonic_loss_report.json
POLYTONIC_PAGES  := data/quality/polytonic-loss-pages.jsonl.gz
COMPLETENESS_REPORT := data/inventory/completeness-batch-report.json
DATE_COMPARISON := data/oga_glaux_date_comparison.json

# The served text itself. Several artifacts are functions of these files rather
# than of corpus_editions.json, and taking corpus_editions.json as their stand-in
# is what let them go stale: the upstream OCR pipeline delivers new text into
# data/corpus without touching it. ocr_quality_report.json sat 524 corpus-file
# changes behind, while the OCR pipeline gates on it.
CORPUS_FILES := $(wildcard data/corpus/*.jsonl)
HERODAS_READING_INPUTS := scripts/herodas_review_state.py scripts/repair_herodas_readings.py \
                         scripts/fetch_herodas_reading_sources.py scripts/herodas_uncertainty_readings.py \
                         $(wildcard scripts/herodas_excerpt_readings*.py) \
                         $(wildcard data/corpus_changes/herodas-reading-review/*) \
                         $(wildcard data/corpus_changes/herodas-reading-sources/*)
# Count eligibility can change while every served surface byte stays identical.
FREQUENCY_INPUTS := scripts/frequency_projection.py \
                    $(HERODAS_READING_INPUTS) \
                    scripts/repair_phoenix_crusius.py scripts/phoenix_crusius_source_observations.py \
                    scripts/phoenix_crusius_witnesses.py \
                    scripts/citation_alias_state.py scripts/phoenix_current_state.py \
                    scripts/repair_editorial_roles.py scripts/herodas_source_observations.py scripts/editorial_roles.py \
                    scripts/herodas_current_state.py scripts/repair_herodas_body.py \
                    scripts/herodas_body_source_observations.py scripts/herodas_body_witnesses.py \
                    scripts/herodas_body_witness_observations.py scripts/prepare_herodas_body.py scripts/scan_ocr_bundle.py scripts/run_scan_ocr.py \
                    $(wildcard scripts/herodas_body_readings*.py) \
                    $(wildcard data/corpus_changes/herodas-headlam-knox-body/*) \
                    $(wildcard data/corpus_changes/editorial-role-review/*) \
                    $(wildcard data/corpus_changes/phoenix-crusius-review/*) \
                    $(PHOTIUS_LATER_INPUTS) \
                    scripts/repair_photius_apparatus.py \
                    scripts/repair_photius_body.py \
                    scripts/repair_photius_readings.py scripts/photius_reading_vote.py \
                    scripts/photius_body_vote.py \
                    scripts/repair_photius_historical_readings.py \
                    scripts/repair_photius_historical_batches.py \
                    scripts/repair_photius_complete_review.py scripts/assess_photius_historical.py \
                    scripts/ocr_consensus.py scripts/audit_compression.py \
                    scripts/prepare_photius_review_campaign.py \
                    $(wildcard data/corpus_changes/photius-bekker-historical-batches/*/changes.json) \
                    $(wildcard scripts/critical_text.py data/frequency_projection.json)
REVIEWED_MANIFESTATIONS := scripts/reviewed_manifestations.py \
    $(HERODAS_READING_INPUTS) \
    scripts/repair_phoenix_crusius.py scripts/phoenix_crusius_source_observations.py \
    scripts/citation_alias_state.py scripts/phoenix_current_state.py \
    scripts/repair_editorial_roles.py scripts/herodas_source_observations.py scripts/editorial_roles.py \
    scripts/editorial_role_manifestations.py \
    scripts/herodas_current_state.py scripts/repair_herodas_body.py \
    scripts/herodas_body_source_observations.py scripts/herodas_body_witnesses.py \
    scripts/herodas_body_witness_observations.py scripts/prepare_herodas_body.py scripts/scan_ocr_bundle.py scripts/run_scan_ocr.py \
    $(wildcard scripts/herodas_body_readings*.py) \
    $(wildcard data/corpus_changes/herodas-headlam-knox-body/*) \
    $(wildcard data/corpus_changes/editorial-role-review/*) \
    $(wildcard data/corpus_changes/phoenix-crusius-review/*) \
    $(PHOTIUS_LATER_INPUTS) \
    scripts/repair_photius_apparatus.py \
    scripts/repair_photius_readings.py scripts/photius_reading_vote.py \
    scripts/photius_body_vote.py \
    scripts/repair_photius_historical_readings.py \
    scripts/repair_photius_historical_batches.py \
    scripts/repair_photius_complete_review.py \
    $(wildcard data/corpus_changes/photius-bekker-historical-batches/*/changes.json) \
    $(wildcard data/corpus_changes/meibom-musical-anthology/changes.json \
               data/corpus_changes/photius-bekker-coverage/coverage.json \
               data/corpus_changes/photius-bekker-apparatus/changes.json \
               data/corpus_changes/photius-bekker-readings/changes.json \
               data/corpus_changes/photius-bekker-historical-readings/changes.json \
               data/ingest_reviews/photius-bekker-reading-windows.json \
               data/ingest_reviews/photius-bekker-body-recovery*.json \
               data/ingest_reviews/photius-bekker-apparatus.json \
               data/corpus_changes/cyril-john-coverage/changes.json \
               data/corpus_extension_index.json data/critical_editions/*/manifest.json)

# Only this repo's own (non-OCR) ingesters. The OCR text - calfa-co Patrologia
# Graeca and our own Migne/edition OCR - is produced, cleaned, and DELIVERED
# into data/corpus by the upstream OCR pipeline; this repo just rolls it up.
INGESTERS := scripts/build_corpus_loci.py scripts/build_byzantine_vernacular_corpus.py \
             scripts/build_byzantium_gr_corpus.py
SWEEPS    := data/pd_research/byzantium_sweep.json data/pd_research/cgpg_coverage.json

.PHONY: all yardstick sourcing ingest ids reports check clean oga-metadata \
        capital-positions
all: yardstick sourcing reports check

# OGA (Opera Graeca Adnotata v0.2.0) metadata: per-work dating + the PTA/TLG
# duplicate map + the source pin. Reads the retained OGA clone ($OGA_ROOT, default
# ~/Documents/oga) and the id layer, so run it AFTER `make ids`. Its committed
# outputs (data/oga_dating.json etc.) feed build_registry.py; it is deliberately
# NOT in the auto DAG (it depends on the crosswalks the registry helps build).
oga-metadata:
	$(PY) scripts/ingest_oga_metadata.py

# Just the opaque-id layer: ledgers -> corpus_editions id injection -> WEMI index.
# build_work_index.py reads the committed $(CROSSWALK) for the title of any work
# the registry does not cover (the carved CGPG volumes, byzantium.gr, the OCR'd
# PD editions - 913 works were served titleless, and the crosswalk titled 484 of
# them; the 429 still blank are FGrH/FHG fragment authors with no TLG anchor, for
# which no file in the repo holds a title). It is NOT a prerequisite here:
# the crosswalk is a committed artifact, `sourcing` rebuilds it when the registry
# moves, and making it one would drag the whole ingest chain into this target.
ids:
	$(PY) scripts/build_id_registry.py
	$(PY) scripts/reconcile_corpus_editions.py
	$(PY) scripts/build_work_index.py
	$(PY) scripts/validate_id_layer.py

# 1. Ingest this repo's open TEI + transcription sources into data/corpus/*.jsonl,
#    then DERIVE corpus_editions.json from the whole corpus (TEI + the OCR works
#    the upstream OCR pipeline delivered). Deriving it, rather than each ingester
#    read-modify-writing the shared file, is race-safe: two writers (this build +
#    an upstream OCR delivery) can't drop each other's rows, because the per-work
#    jsonl files never collide.
ingest: $(CORPUS_EDITIONS)
$(CORPUS_EDITIONS): $(INGESTERS) scripts/corpus_order_overrides.py scripts/reconcile_corpus_editions.py scripts/build_id_registry.py scripts/build_work_index.py data/corpus_order_overrides.json data/corpus_text_corrections.json data/work_id_aliases.json data/serving_deficits.json $(FREQUENCY_INPUTS)
	$(PY) scripts/build_corpus_loci.py
	$(PY) scripts/build_byzantine_vernacular_corpus.py
	$(PY) scripts/build_byzantium_gr_corpus.py   # cache-first; fetches missing pages
	$(PY) scripts/build_id_registry.py           # mint/maintain the ogc/oga id ledgers (reads the corpus dir)
	$(PY) scripts/reconcile_corpus_editions.py   # corpus_editions := data/corpus (race-safe; injects the ogc id)
	$(PY) scripts/build_work_index.py            # work_index.json: reader-facing WEMI join + redirects
	$(PY) scripts/validate_id_layer.py           # assert the id-layer invariants

# 2. Yardstick: roll the whole corpus (TEI + the delivered, already-corrected OCR)
#    up into the lexicon + coverage, then per-lemma frequency. The OCR text arrives
#    clean from the upstream OCR pipeline, so there is no correction step here.
yardstick: $(LEMMA_FREQ)
$(LEXICON): $(CORPUS_FILES) $(CORPUS_EDITIONS) scripts/build_public_corpus.py $(FREQUENCY_INPUTS)
	$(PY) scripts/build_public_corpus.py
$(ELISION_RATES): $(CORPUS_FILES) scripts/measure_elision_rates.py \
                  scripts/validate_lemma_map.py $(FREQUENCY_INPUTS)
	$(PY) scripts/measure_elision_rates.py
$(LEMMA_FREQ): $(LEXICON) scripts/build_lemma_frequency.py \
               scripts/validate_lemma_map.py data/capital_positions.json $(ELISION_RATES)
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_lemma_frequency.py --min-count $(MIN_COUNT)

# The whole OCR pipeline - ingesting the OCR output, cleaning it, and
# applying the corrections - lives in a separate upstream repository. It DELIVERS
# the corrected OCR text into data/corpus here, with a read-only audit mirror in
# data/corrections_log/. This repo holds only that output and rolls it up.

# 3. Source-precedence overrides, regenerated from the coverage sweeps.
$(OVERRIDES): scripts/build_source_overrides.py $(SWEEPS) data/inventory/sourcing_map.csv
$(OVERRIDES): scripts/gutenberg_source_metadata.py data/corpus_changes/gutenberg-historical/changes.json
	$(PY) scripts/build_source_overrides.py

# 4. Sourcing verdict + gap: registry and coverage report both apply the
#    overrides (via scripts/source_precedence.py) so they agree.
sourcing: $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT)
# data/oga_dating.json is a committed input (regenerated out-of-band by
# `make oga-metadata`); a change to it re-applies the OGA dating tags. The curated
# data/oga_dating_adjudication.json resolves the genuine (|delta| >= 2) OGA-vs-cog
# divergences; a change to it re-applies those decisions.
data/served_scheme_inference.json: $(CORPUS_EDITIONS) scripts/infer_served_schemes.py
	$(PY) scripts/infer_served_schemes.py

$(REGISTRY): $(OVERRIDES) $(CORPUS_EDITIONS) scripts/build_registry.py scripts/source_precedence.py data/oga_dating.json data/oga_dating_adjudication.json data/author_authority.json data/work_authority.json data/pseudo_author_attributions.json data/served_scheme_inference.json source_identity.py
$(REGISTRY): $(REVIEWED_MANIFESTATIONS) $(CORPUS_FILES)
$(REGISTRY): scripts/gutenberg_source_metadata.py data/gutenberg_historical_sources.json \
             data/corpus_changes/gutenberg-historical/changes.json
	$(PY) scripts/build_registry.py
$(COVERAGE_REPORT): $(OVERRIDES) $(CORPUS_EDITIONS) scripts/build_coverage_report.py scripts/source_precedence.py
	$(PY) scripts/build_coverage_report.py
# Crosswalk completeness: how well each work/author/edition is linked to external
# identifier systems, and which works lack an edition-independent logical locus.
$(CROSSWALK_REPORT): $(REGISTRY) $(CORPUS_EDITIONS) data/work_index.json scripts/build_crosswalk_report.py source_identity.py
	$(PY) scripts/build_crosswalk_report.py

# 5. Reports over the served text. Each reads data/corpus directly, so each takes
#    the corpus files as its prerequisite. All three were previously outside the
#    build graph entirely and were regenerated by hand, which is why the README's
#    provenance header, ocr_quality_report.json and the per-work lemma counts had
#    each drifted from the text they describe.
reports: $(QUALITY_REPORT) $(WORK_LEMMAS) $(CATALOG) README.md $(GRAVE_RESIDUE) $(PG003_ALT) $(DUP_LEAVES) $(DUP_PAGES) $(PG003_HEADS) $(PG003_GEOM) $(NONFINAL_GRAVES) data/nonfinal_grave_tranche_thirdparty.json $(KNOWN_LIMITATIONS) $(LATIN_IN_GREEK) $(SPACING_MARKS) $(MERGE_SAMPLE) $(MERGE_GUESSES)
reports: $(POLYTONIC_REPORT) $(POLYTONIC_PAGES) $(COMPLETENESS_REPORT) $(DATE_COMPARISON)
reports: $(SOURCE_COMPONENTS) $(PHOTIUS_CURRENT_ASSESSMENT)

# Keep the earlier diagnostic frozen; the current diagnostic includes the later
# occurrence annotations and is compressed separately from its predecessor.
$(PHOTIUS_CURRENT_ASSESSMENT): scripts/build_photius_historical_assessment.py \
    scripts/assess_photius_historical.py scripts/audit_compression.py $(PHOTIUS_LATER_INPUTS) \
    data/corpus/photius.bibliotheca.jsonl data/audits/photius-historical-readings.json \
    data/passage_aliases.json \
    data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz \
    data/corpus_changes/photius-bekker-coverage/coverage.json \
    data/corpus_changes/photius-bekker-index/before.jsonl.gz
	$(PY) scripts/build_photius_historical_assessment.py --write

# These reports reuse pinned source evidence. Fresh model inference remains an
# explicit evaluation run; changing the corpus never re-runs that experiment.
$(POLYTONIC_REPORT): $(CORPUS_FILES) scripts/report_polytonic_loss.py \
                    scripts/benchmark_page_ocr.py data/evaluation/polytonic-loss/policy.json
	$(PY) scripts/report_polytonic_loss.py corpus
$(POLYTONIC_PAGES): $(POLYTONIC_REPORT)
	@test -f $@ || $(PY) scripts/report_polytonic_loss.py corpus

$(COMPLETENESS_REPORT): $(CORPUS_FILES) $(CORPUS_EDITIONS) CITATION.cff \
    data/inventory/completeness-batch.json scripts/audit_completeness_batch.py \
    scripts/coverage_resolution.py scripts/scan_coverage_extensions.py \
    scripts/ingest_scan_coverage.py scripts/ingest_photius_coverage.py \
    scripts/repair_john_coverage.py $(REVIEWED_MANIFESTATIONS) \
    $(wildcard data/corpus_changes/*/changes.json data/corpus_changes/*/coverage.json \
               data/ingest_reviews/coverage/*.json data/ocr_requests/photius-*.json)
	$(PY) scripts/audit_completeness_batch.py --first1k-dir $(FIRST1K_DIR) --perseus-dir $(PERSEUS_DIR)

$(DATE_COMPARISON): $(REGISTRY) $(CROSSWALK) data/oga_dating.json \
    scripts/compare_oga_glaux_dates.py $(wildcard data/reference/bilby-oga-glaux-2024/*)
	$(PY) scripts/compare_oga_glaux_dates.py

$(PHOTIUS_REVIEW_STATUS): $(PHOTIUS_REVIEW_INPUTS)
	$(PY) scripts/build_photius_review_observations.py --write

$(QUALITY_REPORT): $(CORPUS_FILES) $(CORPUS_EDITIONS) scripts/build_ocr_quality_report.py $(FREQUENCY_INPUTS) $(PHOTIUS_REVIEW_STATUS)
	$(PY) scripts/build_ocr_quality_report.py

# A work can combine OCR and digital text. Count each served row's source
# before assigning quality labels or publishing an OCR denominator.
$(SOURCE_COMPONENTS): $(CORPUS_FILES) scripts/build_source_components.py $(FREQUENCY_INPUTS)
	$(PY) scripts/build_source_components.py

# The published per-work catalog. It had no rule at all and drifted nine commits
# behind, still serving titles that read `Ei)S` and `E)N` after the decoder had
# been fixed, and one work short of the index. It is a join over these five, so
# they are its prerequisites; corpus_editions.json alone would be the same
# stand-in mistake the CORPUS_FILES comment above describes.
# data/work_index.json is named as a plain file, not via the `ids` target: that
# target is deliberately phony (see its comment above) and depending on it would
# drag the whole ingest chain into `reports`.
$(CATALOG): $(CORPUS_FILES) data/work_index.json $(CORPUS_EDITIONS) \
            $(QUALITY_REPORT) $(SOURCE_COMPONENTS) data/work_token_totals.json \
            scripts/build_corpus_catalog.py
	$(PY) scripts/build_corpus_catalog.py

# Needs the Dilemma lemmatizer, like $(LEMMA_FREQ). Writes the .tsv.gz and its
# stats sidecar; the persistent form->lemma cache is validated on load, so a bad
# entry cannot survive a rebuild (scripts/validate_lemma_map.py holds the checks).
# data/capital_positions.json is a prerequisite because validate_lemma_map reads
# it as CAPITAL_FOLDS and applies it while this table is built. It was missing,
# so re-running the measurement changed the folds and `make` reported the table
# up to date, which is how a measured fold could sit on disk unapplied.
#
# The prerequisite fixed make's ORDER and not the staleness itself: nothing here
# builds capital_positions.json, and nothing can, because the measurement reads
# work_lemma_counts.tsv.gz and would close a cycle that make resolves by dropping
# an edge without erroring. So it is a phony target run on purpose, and `check`
# is what notices it has gone stale. It sat unbuilt from 2026-08-06 to
# 2026-08-09 with three measured folds unapplied (Κόσμος 80 tokens, Ἐπιστάτης
# 18, Ἐγχειρίδιον 10).
$(WORK_LEMMAS): $(CORPUS_FILES) scripts/build_work_lemma_counts.py \
                scripts/validate_lemma_map.py $(LEMMA_FREQ) \
                data/capital_positions.json $(FREQUENCY_INPUTS)
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_work_lemma_counts.py

# The grave-residue partition published on issue #4. It had no rule, so it went
# stale the moment anything changed the table it measures: composing the spacing
# breathings (issue #4, the same round) moved the residue from 8,105 lemmas /
# 32,593 tokens to 7,960 / 31,758 and the committed file still claimed the old
# figures, with nothing failing. That is the same failure the capital_positions
# prerequisite above was added for, one artifact over: a measurement quoted on
# the tracker has to be rebuilt by the thing that invalidates it.
# $(CATALOG) too, since the by_correction_status block reads its `correction`
# column: that column can move from an OCR-ledger edit that leaves the corpus
# files alone, and this artifact is quoted on issue #4.
$(GRAVE_RESIDUE): $(WORK_LEMMAS) $(CATALOG) scripts/measure_grave_residue.py \
                  scripts/validate_lemma_map.py
	PYTHONPATH=$(DILEMMA) $(PY) scripts/measure_grave_residue.py --write

# Same reasoning as $(GRAVE_RESIDUE) above: a measurement quoted on the tracker
# has to be rebuilt by whatever invalidates it. This one reads the PG003 rows, so
# any correction to that volume's text changes it.
# Same reasoning again. This one reads every cgpg row in the corpus, so any
# carve, split or drop changes it, and it is the only detector that would catch
# a leaf the OCR delivered twice with the columns read in a different order.
# Depends on the vendored second OCR as well as our rows: if either moves the
# head table has to be rebuilt, and it is quoted on issue #9.
# The volume file is gone: its text is in the carved works and its apparatus in
# data/paratext. Both PG003 measurements read the carve audit's archived rows
# instead, which is the volume as it stood before any of this.
data/cache/ia/PG003_djvu.txt: scripts/fetch_pinned_source.py
	$(PY) scripts/fetch_pinned_source.py pg003-text

data/cache/ia/PG003_djvu.xml: scripts/fetch_pinned_source.py
	$(PY) scripts/fetch_pinned_source.py pg003-geometry

$(PG003_HEADS): data/corpus_changes/cogPG.PG003.row-split.json data/pg003_blocks.json \
                data/cache/ia/PG003_djvu.txt scripts/recover_pg003_heads.py scripts/fetch_pinned_source.py
	$(PY) scripts/recover_pg003_heads.py --write

# The same sweep over the line-level ocr source, where the unit is a scan page
# (a run of rows) rather than a row. Kept as its own artifact because the two
# sources answer the same question about different things.
# Quoted on issue #31, so it rebuilds whenever the text it counts changes.
# Writes data/nonfinal_grave_tranche.json alongside it: the proposed repair,
# not applied, whose figures are quoted on issue #31 and so must not go stale.
$(NONFINAL_GRAVES) data/nonfinal_grave_tranche.json \
data/nonfinal_grave_tranche_marks.json \
data/nonfinal_grave_tranche_thirdparty.json: $(CORPUS_FILES) \
                scripts/measure_nonfinal_graves.py $(FREQUENCY_INPUTS)
	$(PY) scripts/measure_nonfinal_graves.py --write

$(KNOWN_LIMITATIONS): $(NONFINAL_GRAVES) $(CATALOG) \
                data/correction_stamp_gap.json $(SOURCE_COMPONENTS) scripts/build_known_limitations.py \
                scripts/build_corpus_release.py $(COMPLETENESS_REPORT) scripts/coverage_resolution.py
	$(PY) scripts/build_known_limitations.py --write

# Quoted on issue #34, so it rebuilds whenever the text it counts changes.
$(LATIN_IN_GREEK): $(CORPUS_FILES) scripts/measure_latin_in_greek_script.py
	$(PY) scripts/measure_latin_in_greek_script.py --write

# Both quoted on the tracker, both added without a rule, which is the failure
# this Makefile already documents three times over (capital_positions, the
# grave residue, the README figures). data/spacing_mark_classes.json was worse
# than unruled: it was produced from a shell heredoc and so could not be
# rebuilt at all.
$(SPACING_MARKS): $(CORPUS_FILES) scripts/measure_spacing_marks.py $(FREQUENCY_INPUTS)
	$(PY) scripts/measure_spacing_marks.py --write

# Depends on the candidates too: the merge is only attempted inside a leaf-run,
# so a change to which pages form one changes what this samples. Both artifacts
# come out of one run. Once the merge is applied the script reports from its
# audit and leaves these two alone, because the pages it merged no longer exist
# as separate pages and recomputing would blank the record rather than rebuild
# it; that is also what keeps a second `make reports` byte-identical.
$(MERGE_SAMPLE) $(MERGE_GUESSES): $(CORPUS_FILES) $(DUP_PAGES) \
                scripts/merge_duplicate_reads.py
	$(PY) scripts/merge_duplicate_reads.py

$(DUP_PAGES): $(CORPUS_FILES) scripts/sweep_duplicate_leaves.py
	$(PY) scripts/sweep_duplicate_leaves.py --source ocr --out $(DUP_PAGES) --write

$(DUP_LEAVES): $(CORPUS_FILES) scripts/sweep_duplicate_leaves.py
	$(PY) scripts/sweep_duplicate_leaves.py --write

$(PG003_ALT): data/corpus_changes/cogPG.PG003.row-split.json \
                scripts/measure_pg003_alternation.py
	$(PY) scripts/measure_pg003_alternation.py --write

# Depends on the scan and on nothing of ours: it measures where Migne printed
# the paraphrase head, which is a fact about the volume, not about our rows. It
# is a prerequisite of the head table in reasoning rather than in make, since
# the two read different derivatives of the same scan, but if this one ever
# stops saying display head then the boundaries in $(PG003_HEADS) stop meaning
# what they say. tests/test_pg003_heads.py asserts the verdict for that reason.
$(PG003_GEOM): data/cache/ia/PG003_djvu.xml scripts/measure_pg003_head_geometry.py scripts/fetch_pinned_source.py
	$(PY) scripts/measure_pg003_head_geometry.py --write

# build_provenance.py rewrites the table between the OCR-PROVENANCE markers, so
# README.md is genuinely its output file. A hand edit to the README also updates
# the mtime, so editing prose does not trigger a spurious corpus-wide rescan.
#
# $(WORK_LEMMAS) is a prerequisite because the Words column reads the per-work
# token totals it derives. The order matters, and getting it wrong is not a
# no-op: a stale totals file predates the CGPG carves and the July re-OCR, so it
# would report the whole Hesychius lexicon under the slug of its prefatory
# letter. Build the totals first and the column is right; trust them stale and
# it is worse than the ledger it replaces.
README.md: $(CORPUS_FILES) scripts/build_provenance.py scripts/build_readme_figures.py \
           data/work_index.json $(CORPUS_EDITIONS) $(WORK_LEMMAS) $(SOURCE_COMPONENTS) \
           data/ocr_works.json data/inventory/ocr_edition_sources.json
	$(PY) scripts/build_provenance.py
	$(PY) scripts/build_readme_figures.py --write

# The crosswalk's titles come from the vendored CTS metadata in a second pass.
# Keep the two together: build_id_crosswalk.py rewrites the file from the
# registry alone, so running it on its own drops every backfilled title.
$(CROSSWALK): $(REGISTRY) scripts/build_id_crosswalk.py scripts/backfill_crosswalk_titles.py
	$(PY) scripts/build_id_crosswalk.py
	$(PY) scripts/backfill_crosswalk_titles.py --write

# 6. Consistency checks that have no output of their own. These FAIL rather than
#    repair, because the repair is not always the right move: check_ocr_ledgers
#    syncs the two ledgers' passage and token counts to the served text, but
#    deliberately leaves source/edition/license alone, since a row reading
#    `ocr` / PD against a corpus reading first1k / CC-BY-SA-4.0 is a work we
#    OCR'd that an open edition later displaced, and both are true.
#    check_corrections_mirror_fresh is here for the same reason one target over:
#    data/corrections_log/ is a local mirror of the upstream correction store that
#    this repo cannot rebuild, and the catalog and the README table both read its
#    provenance.json as enrichment. A mirror older than the served text therefore
#    adds claims the text no longer supports - the 2026-08-21 confusion/accepted
#    revert left 12 works published as auto-corrected after their corrections had
#    gone - and the repair is upstream, so this reports and fails.
# Rebuild the capital folds. Phony on purpose, see the note above $(WORK_LEMMAS):
# a real rule would be a cycle. Run it, then `make` to carry the folds through.
capital-positions:
	$(PY) scripts/measure_capital_positions.py --write

# These validators read the frozen artifacts independently; use make -j4 check
# to check them concurrently. Every command remains a required prerequisite.
.PHONY: check-ocr-ledgers \
        check-phoenix-crusius \
        check-editorial-roles \
        check-herodas-body \
        check-herodas-readings \
        check-acharnians-source-pilot \
        check-photius-apparatus-repair \
        check-photius-readings \
        check-photius-historical-readings \
        check-photius-historical-batches \
        check-photius-review-observations \
        check-photius-complete-review \
        check-photius-context check-photius-uncertainties check-photius-uncertainty-sources \
        check-photius-historical-assessment check-photius-uncertainty-pilot \
        check-photius-uncertainty-admission check-photius-editorial-substitutions \
        check-photius-editorial-source check-photius-editorial-continuation check-photius-editorial-continuation-source \
        check-photius-final-review check-photius-final-review-source \
        check-photius-apparatus-audit \
        check-source-components \
        check-capital-positions \
        check-corrections-mirror \
        check-known-limitations \
        check-oga-glaux-dates

# Start the longest measured checks first so they do not wait behind short ones
# when the independent prerequisites run concurrently.
check: check-photius-complete-review \
       check-phoenix-crusius \
       check-editorial-roles \
       check-herodas-body \
       check-herodas-readings \
       check-acharnians-source-pilot \
       check-photius-context check-photius-uncertainties check-photius-uncertainty-sources \
       check-photius-review-observations \
       check-known-limitations \
       check-ocr-ledgers \
       check-photius-apparatus-repair \
       check-photius-readings \
       check-photius-historical-readings \
       check-photius-historical-batches \
       check-photius-historical-assessment check-photius-uncertainty-admission \
       check-photius-editorial-substitutions check-photius-editorial-continuation check-photius-final-review \
       check-photius-apparatus-audit \
       check-source-components \
       check-capital-positions \
       check-corrections-mirror \
       check-oga-glaux-dates

check-ocr-ledgers:
	$(PY) scripts/check_ocr_ledgers.py

check-phoenix-crusius:
	$(PY) scripts/phoenix_current_state.py --check

check-editorial-roles:
	$(PY) scripts/herodas_current_state.py --check
	$(PY) scripts/editorial_role_manifestations.py --check

check-herodas-body:
	$(PY) scripts/herodas_current_state.py --check-body

check-herodas-readings:
	$(PY) scripts/herodas_review_state.py --check

check-acharnians-source-pilot:
	$(PY) scripts/audit_acharnians_source_pilot.py --check

check-photius-apparatus-repair:
	$(PY) scripts/check_photius_predecessor.py --stage apparatus

check-photius-readings:
	$(PY) scripts/check_photius_predecessor.py --stage readings

check-photius-historical-readings:
	$(PY) scripts/check_photius_predecessor.py --stage historical-readings

check-photius-historical-batches:
	$(PY) scripts/check_photius_predecessor.py --stage historical-batches

check-photius-review-observations:
	$(PY) scripts/check_photius_predecessor.py --stage review-observations

check-photius-complete-review:
	$(PY) scripts/check_photius_predecessor.py --stage complete-review

check-photius-context:
	$(PY) scripts/check_photius_predecessor.py --stage context

check-photius-uncertainties:
	$(PY) scripts/check_photius_predecessor.py --stage uncertainties

check-photius-uncertainty-sources:
	$(PY) scripts/fetch_photius_uncertainty_sources.py --check

check-photius-historical-assessment:
	$(PY) scripts/build_photius_historical_assessment.py --check

check-photius-uncertainty-pilot:
	$(PY) scripts/check_photius_predecessor.py --stage uncertainty-pilot

check-photius-uncertainty-admission:
	$(PY) scripts/check_photius_predecessor.py --stage uncertainty-admission

check-photius-editorial-substitutions:
	$(PY) scripts/check_photius_predecessor.py --stage editorial-substitutions

check-photius-editorial-source:
	$(PY) scripts/check_photius_predecessor.py --stage editorial-source

check-photius-editorial-continuation:
	$(PY) scripts/check_photius_predecessor.py --stage editorial-continuation

check-photius-editorial-continuation-source:
	$(PY) scripts/check_photius_predecessor.py --stage editorial-continuation-source

check-photius-final-review:
	$(PY) scripts/check_photius_predecessor.py --stage final-review

check-photius-final-review-source:
	$(PY) scripts/check_photius_predecessor.py --stage final-review-source

check-photius-apparatus-audit:
	$(PY) scripts/check_photius_predecessor.py --stage apparatus-audit

check-source-components:
	$(PY) scripts/build_source_components.py --check

check-capital-positions:
	$(PY) scripts/check_capital_positions_fresh.py

check-corrections-mirror:
	$(PY) scripts/check_corrections_mirror_fresh.py

check-known-limitations:
	$(PY) scripts/build_known_limitations.py --check

check-oga-glaux-dates:
	$(PY) scripts/compare_oga_glaux_dates.py --check

clean:
	rm -f $(LEXICON) data/coverage.json $(LEMMA_FREQ) $(OVERRIDES) \
	      $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT) \
	      $(QUALITY_REPORT) $(SOURCE_COMPONENTS) $(WORK_LEMMAS) $(KNOWN_LIMITATIONS)
