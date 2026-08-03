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
# Outputs are byte-stable (sorted, no wall-clock), so `make` is a no-op when no
# prerequisite changed and re-committing regenerated files is churn-free.
#
#   make            # full chain
#   make yardstick  # just the lexicon + lemma frequency
#   make sourcing   # just overrides + registry + coverage report
#   make reports    # just the per-corpus reports (quality, per-work lemmas,
#                   # the README provenance table)
#
# build_lemma_frequency needs the Dilemma lemmatiser importable; point DILEMMA at
# its checkout (default ../dilemma) or pre-set PYTHONPATH.

PY       ?= python3
MIN_COUNT ?= 5
DILEMMA  ?= ../dilemma

CORPUS_EDITIONS := data/corpus_editions.json
LEXICON         := data/public_lexicon.tsv
LEMMA_FREQ      := data/public_lemma_frequency.tsv
OVERRIDES       := data/source_overrides.json
REGISTRY        := data/source_registry.json
COVERAGE_REPORT := data/coverage_report.json
CROSSWALK_REPORT := data/crosswalk_report.json
CROSSWALK       := data/tlg_crosswalk.json
QUALITY_REPORT  := data/ocr_quality_report.json
WORK_LEMMAS     := data/work_lemma_counts.tsv.gz

# The served text itself. Several artifacts are functions of these files rather
# than of corpus_editions.json, and taking corpus_editions.json as their stand-in
# is what let them go stale: the upstream OCR pipeline delivers new text into
# data/corpus without touching it. ocr_quality_report.json sat 524 corpus-file
# changes behind, while the OCR pipeline gates on it.
CORPUS_FILES := $(wildcard data/corpus/*.jsonl)

# Only this repo's own (non-OCR) ingesters. The OCR text - calfa-co Patrologia
# Graeca and our own Migne/edition OCR - is produced, cleaned, and DELIVERED
# into data/corpus by the upstream OCR pipeline; this repo just rolls it up.
INGESTERS := scripts/build_corpus_loci.py scripts/build_byzantine_vernacular_corpus.py \
             scripts/build_byzantium_gr_corpus.py
SWEEPS    := data/pd_research/byzantium_sweep.json data/pd_research/cgpg_coverage.json

.PHONY: all yardstick sourcing ingest ids reports clean oga-metadata
all: yardstick sourcing reports

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
# PD editions - 913 works were served titleless). It is NOT a prerequisite here:
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
$(CORPUS_EDITIONS): $(INGESTERS) scripts/reconcile_corpus_editions.py scripts/build_id_registry.py scripts/build_work_index.py data/work_id_aliases.json
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
$(LEXICON): $(CORPUS_EDITIONS) scripts/build_public_corpus.py
	$(PY) scripts/build_public_corpus.py
$(LEMMA_FREQ): $(LEXICON) scripts/build_lemma_frequency.py
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_lemma_frequency.py --min-count $(MIN_COUNT)

# The whole OCR pipeline - ingesting the OCR output, cleaning it, and
# applying the corrections - lives in a separate upstream repository. It DELIVERS
# the corrected OCR text into data/corpus here, with a read-only audit mirror in
# data/corrections_log/. This repo holds only that output and rolls it up.

# 3. Source-precedence overrides, regenerated from the coverage sweeps.
$(OVERRIDES): scripts/build_source_overrides.py $(SWEEPS) data/inventory/sourcing_map.csv
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
reports: $(QUALITY_REPORT) $(WORK_LEMMAS) README.md

$(QUALITY_REPORT): $(CORPUS_FILES) scripts/build_ocr_quality_report.py
	$(PY) scripts/build_ocr_quality_report.py

# Needs the Dilemma lemmatiser, like $(LEMMA_FREQ). Writes the .tsv.gz and its
# stats sidecar; the persistent form->lemma cache is validated on load, so a bad
# entry cannot survive a rebuild (scripts/validate_lemma_map.py holds the checks).
$(WORK_LEMMAS): $(CORPUS_FILES) scripts/build_work_lemma_counts.py \
                scripts/validate_lemma_map.py $(LEMMA_FREQ)
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_work_lemma_counts.py

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
README.md: $(CORPUS_FILES) scripts/build_provenance.py $(CORPUS_EDITIONS) $(WORK_LEMMAS)
	$(PY) scripts/build_provenance.py

# The crosswalk's titles come from the vendored CTS metadata in a second pass.
# Keep the two together: build_id_crosswalk.py rewrites the file from the
# registry alone, so running it on its own drops every backfilled title.
$(CROSSWALK): $(REGISTRY) scripts/build_id_crosswalk.py scripts/backfill_crosswalk_titles.py
	$(PY) scripts/build_id_crosswalk.py
	$(PY) scripts/backfill_crosswalk_titles.py --write

clean:
	rm -f $(LEXICON) data/coverage.json $(LEMMA_FREQ) $(OVERRIDES) \
	      $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT) \
	      $(QUALITY_REPORT) $(WORK_LEMMAS)
