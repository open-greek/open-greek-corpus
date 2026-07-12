# Regenerate the open-corpus yardstick and the sourcing artifacts.
#
# The yardstick (public_lexicon.tsv + per-lemma frequency) is defined by cog's
# OWN ingested corpus, and must grow whenever a TLG-only work is replaced by an
# open/PD source. The chain is therefore:
#
#   ingest  -> data/corpus/*.jsonl + corpus_editions.json   (TEI/transcription works;
#              the OCR works arrive already-corrected from the greek-ocr pipeline)
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

# Only this repo's own (non-OCR) ingesters. The OCR text - calfa-co Patrologia
# Graeca and our own Migne/edition OCR - is produced, cleaned, and DELIVERED
# into data/corpus by the greek-ocr repo's pipeline; this repo just rolls it up.
INGESTERS := scripts/build_corpus_loci.py scripts/build_byzantine_vernacular_corpus.py \
             scripts/build_byzantium_gr_corpus.py
SWEEPS    := data/pd_research/byzantium_sweep.json data/pd_research/cgpg_coverage.json

.PHONY: all yardstick sourcing ingest ids clean oga-metadata
all: yardstick sourcing

# OGA (Opera Graeca Adnotata v0.2.0) metadata: per-work dating + the PTA/TLG
# duplicate map + the source pin. Reads the retained OGA clone ($OGA_ROOT, default
# ~/Documents/oga) and the id layer, so run it AFTER `make ids`. Its committed
# outputs (data/oga_dating.json etc.) feed build_registry.py; it is deliberately
# NOT in the auto DAG (it depends on the crosswalks the registry helps build).
oga-metadata:
	$(PY) scripts/ingest_oga_metadata.py

# Just the opaque-id layer: ledgers -> corpus_editions id injection -> WEMI index.
ids:
	$(PY) scripts/build_id_registry.py
	$(PY) scripts/reconcile_corpus_editions.py
	$(PY) scripts/build_work_index.py
	$(PY) scripts/validate_id_layer.py

# 1. Ingest this repo's open TEI + transcription sources into data/corpus/*.jsonl,
#    then DERIVE corpus_editions.json from the whole corpus (TEI + the OCR works
#    greek-ocr delivered). Deriving it, rather than each ingester read-modify-writing
#    the shared file, is race-safe: two writers (this build + a greek-ocr delivery)
#    can't drop each other's rows, because the per-work jsonl files never collide.
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
#    clean from greek-ocr, so there is no correction step here.
yardstick: $(LEMMA_FREQ)
$(LEXICON): $(CORPUS_EDITIONS) scripts/build_public_corpus.py
	$(PY) scripts/build_public_corpus.py
$(LEMMA_FREQ): $(LEXICON) scripts/build_lemma_frequency.py
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_lemma_frequency.py --min-count $(MIN_COUNT)

# The whole OCR pipeline - ingesting the OCR output, cleaning it, and
# applying the corrections - lives in the greek-ocr repo. It DELIVERS the corrected
# OCR text into data/corpus here, with a read-only audit mirror in
# data/corrections_log/. This repo holds only that output and rolls it up.

# 3. Source-precedence overrides, regenerated from the coverage sweeps.
$(OVERRIDES): scripts/build_source_overrides.py $(SWEEPS) data/inventory/sourcing_map.csv
	$(PY) scripts/build_source_overrides.py

# 4. Sourcing verdict + gap: registry and coverage report both apply the
#    overrides (via scripts/source_precedence.py) so they agree.
sourcing: $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT)
# data/oga_dating.json is a committed input (regenerated out-of-band by
# `make oga-metadata`); a change to it re-applies the OGA dating tags.
$(REGISTRY): $(OVERRIDES) scripts/build_registry.py scripts/source_precedence.py data/oga_dating.json
	$(PY) scripts/build_registry.py
$(COVERAGE_REPORT): $(OVERRIDES) $(CORPUS_EDITIONS) scripts/build_coverage_report.py scripts/source_precedence.py
	$(PY) scripts/build_coverage_report.py
# Crosswalk completeness: how well each work/author/edition is linked to external
# identifier systems, and which works lack an edition-independent logical locus.
$(CROSSWALK_REPORT): $(REGISTRY) scripts/build_crosswalk_report.py source_identity.py
	$(PY) scripts/build_crosswalk_report.py

clean:
	rm -f $(LEXICON) data/coverage.json $(LEMMA_FREQ) $(OVERRIDES) \
	      $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT)
