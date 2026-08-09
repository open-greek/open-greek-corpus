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

CORPUS_EDITIONS := data/corpus_editions.json
LEXICON         := data/public_lexicon.tsv
GRAVE_RESIDUE   := data/grave_residue.json
DUP_LEAVES      = data/duplicate_leaf_candidates.json
DUP_PAGES       = data/duplicate_page_candidates.json
NONFINAL_GRAVES = data/nonfinal_graves.json
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
WORK_LEMMAS     := data/work_lemma_counts.tsv.gz
CATALOG         := data/corpus_catalog.tsv

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

.PHONY: all yardstick sourcing ingest ids reports check clean oga-metadata
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
$(CORPUS_EDITIONS): $(INGESTERS) scripts/reconcile_corpus_editions.py scripts/build_id_registry.py scripts/build_work_index.py data/work_id_aliases.json data/serving_deficits.json
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
reports: $(QUALITY_REPORT) $(WORK_LEMMAS) $(CATALOG) README.md $(GRAVE_RESIDUE) $(PG003_ALT) $(DUP_LEAVES) $(DUP_PAGES) $(PG003_HEADS) $(PG003_GEOM) $(NONFINAL_GRAVES)

$(QUALITY_REPORT): $(CORPUS_FILES) scripts/build_ocr_quality_report.py
	$(PY) scripts/build_ocr_quality_report.py

# The published per-work catalog. It had no rule at all and drifted nine commits
# behind, still serving titles that read `Ei)S` and `E)N` after the decoder had
# been fixed, and one work short of the index. It is a join over these five, so
# they are its prerequisites; corpus_editions.json alone would be the same
# stand-in mistake the CORPUS_FILES comment above describes.
# data/work_index.json is named as a plain file, not via the `ids` target: that
# target is deliberately phony (see its comment above) and depending on it would
# drag the whole ingest chain into `reports`.
$(CATALOG): $(CORPUS_FILES) data/work_index.json $(CORPUS_EDITIONS) \
            $(QUALITY_REPORT) data/work_token_totals.json \
            scripts/build_corpus_catalog.py
	$(PY) scripts/build_corpus_catalog.py

# Needs the Dilemma lemmatizer, like $(LEMMA_FREQ). Writes the .tsv.gz and its
# stats sidecar; the persistent form->lemma cache is validated on load, so a bad
# entry cannot survive a rebuild (scripts/validate_lemma_map.py holds the checks).
# data/capital_positions.json is a prerequisite because validate_lemma_map reads
# it as CAPITAL_FOLDS and applies it while this table is built. It was missing,
# so re-running the measurement changed the folds and `make` reported the table
# up to date, which is how a measured fold could sit on disk unapplied.
$(WORK_LEMMAS): $(CORPUS_FILES) scripts/build_work_lemma_counts.py \
                scripts/validate_lemma_map.py $(LEMMA_FREQ) \
                data/capital_positions.json
	PYTHONPATH=$(DILEMMA) $(PY) scripts/build_work_lemma_counts.py

# The grave-residue partition published on issue #4. It had no rule, so it went
# stale the moment anything changed the table it measures: composing the spacing
# breathings (issue #4, the same round) moved the residue from 8,105 lemmas /
# 32,593 tokens to 7,960 / 31,758 and the committed file still claimed the old
# figures, with nothing failing. That is the same failure the capital_positions
# prerequisite above was added for, one artifact over: a measurement quoted on
# the tracker has to be rebuilt by the thing that invalidates it.
$(GRAVE_RESIDUE): $(WORK_LEMMAS) scripts/measure_grave_residue.py \
                  scripts/validate_lemma_map.py
	$(PY) scripts/measure_grave_residue.py --write

# Same reasoning as $(GRAVE_RESIDUE) above: a measurement quoted on the tracker
# has to be rebuilt by whatever invalidates it. This one reads the PG003 rows, so
# any correction to that volume's text changes it.
# Same reasoning again. This one reads every cgpg row in the corpus, so any
# carve, split or drop changes it, and it is the only detector that would catch
# a leaf the OCR delivered twice with the columns read in a different order.
# Depends on the vendored second OCR as well as our rows: if either moves the
# head table has to be rebuilt, and it is quoted on issue #9.
$(PG003_HEADS): data/corpus/cogPG.PG003.jsonl data/pg003_blocks.json \
                data/cache/ia/PG003_djvu.txt scripts/recover_pg003_heads.py
	$(PY) scripts/recover_pg003_heads.py --write

# The same sweep over the line-level ocr source, where the unit is a scan page
# (a run of rows) rather than a row. Kept as its own artifact because the two
# sources answer the same question about different things.
# Quoted on issue #31, so it rebuilds whenever the text it counts changes.
$(NONFINAL_GRAVES): $(CORPUS_FILES) scripts/measure_nonfinal_graves.py
	$(PY) scripts/measure_nonfinal_graves.py --write

$(DUP_PAGES): $(CORPUS_FILES) scripts/sweep_duplicate_leaves.py
	$(PY) scripts/sweep_duplicate_leaves.py --source ocr --out $(DUP_PAGES) --write

$(DUP_LEAVES): $(CORPUS_FILES) scripts/sweep_duplicate_leaves.py
	$(PY) scripts/sweep_duplicate_leaves.py --write

$(PG003_ALT): data/corpus/cogPG.PG003.jsonl data/corpus_changes/cogPG.PG003.row-split.json \
                scripts/measure_pg003_alternation.py
	$(PY) scripts/measure_pg003_alternation.py --write

# Depends on the scan and on nothing of ours: it measures where Migne printed
# the paraphrase head, which is a fact about the volume, not about our rows. It
# is a prerequisite of the head table in reasoning rather than in make, since
# the two read different derivatives of the same scan, but if this one ever
# stops saying display head then the boundaries in $(PG003_HEADS) stop meaning
# what they say. tests/test_pg003_heads.py asserts the verdict for that reason.
$(PG003_GEOM): data/cache/ia/PG003_djvu.xml scripts/measure_pg003_head_geometry.py
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
README.md: $(CORPUS_FILES) scripts/build_provenance.py $(CORPUS_EDITIONS) $(WORK_LEMMAS)
	$(PY) scripts/build_provenance.py

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
check:
	$(PY) scripts/check_ocr_ledgers.py

clean:
	rm -f $(LEXICON) data/coverage.json $(LEMMA_FREQ) $(OVERRIDES) \
	      $(REGISTRY) $(COVERAGE_REPORT) $(CROSSWALK_REPORT) \
	      $(QUALITY_REPORT) $(WORK_LEMMAS)
