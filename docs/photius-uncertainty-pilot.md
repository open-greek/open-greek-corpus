# Photius uncertainty pilot

The October 21, 2026 experiment visually assessed 100 of the 3,047 remaining
source uncertainties, grouped into 26 pinned Bekker crops on 26 physical pages.
It recorded 65 text corrections and five confirmed readings; 30 spans remained
uncertain. The original experiment is still an isolated candidate archive, with
an explicit nonadmitting identity. A later served admission applies its 70
resolved decisions and publishes the resulting count of **2,977** uncertainties.
Independent fragment, nonbody, and contrary-reading exclusions still apply.

The original complete campaign, occurrence-context layer, 33-span source review,
and experimental artifacts remain unchanged. The experiment is in
`data/corpus_changes/photius-bekker-uncertainty-pilot/`; the later admission is in
`data/corpus_changes/photius-bekker-uncertainty-admission/`. Both pin exact
preimages, source evidence, authored decisions, and postimages, with exact undo
without live correction sources. Historical counts remain frozen and are
reported separately from the current measurement.

## Selection and results

Within each comparison-location category, crop groups are ordered by the
SHA-256 of a fixed seed and geometry; spans within them use a separate stable
hash. At most six spans per crop per category are selected. The quotas below
approximately retain the common categories and deliberately oversample tied
locations. This clustered exploratory sample does **not** support extrapolating
a resolution rate to all remaining spans. The classification-only map covers
all 3,047 candidates and permits public replay of the selection without access
to the optional comparison edition.

| Comparison-location category | Remaining population | Reviewed | Resolved proposals | Retained uncertain |
| --- | ---: | ---: | ---: | ---: |
| One candidate, authorial body | 1,765 | 58 | 39 | 19 |
| No candidate, authorial body | 1,239 | 39 | 28 | 11 |
| Tied candidates, authorial body | 3 | 2 | 2 | 0 |
| Other text roles | 40 | 1 | 1 | 0 |
| Total | 3,047 | 100 | 70 | 30 |

The initial scan-only passes proposed 76 resolutions. Comparison-directed
reinspection and an additional glyph check withheld seven of them; one initially
uncertain clause became readable on reinspection. Thirty of the final 70
resolutions have no single agreeing comparison reading: 29 have no candidate,
and one preserves a different printed wording. Two more retain tied comparison
locations. Text location therefore cannot be used as a correction vote.

The repeated-word review exposed a packet usability problem: identifying only
a word and a long row can direct attention to its earlier occurrence. Every
sample record now includes exact character offsets and bounded before/target/
after windows for both display text and the scan transcription. The affected
case was rechecked at its declared later occurrence before freezing its decision.

## What TLG adds

The supplied local Photius HTML belongs to Henry's edition family, as does the
current web Bibliotheca. The optional matcher searched the whole remaining set
in 4.022 seconds, including parsing and indexing. It uses three to five verified
body words on each side, without using the uncertain spelling to select a
location. Search normalization preserves original readings, Bekker column labels,
distinct HTML data-node positions, and decoded-token offsets in the private diagnostic. All equally good locations
survive. A unique candidate is still provisional.

Three bounded web searches tested harder quotations. The clause at Bekker
296a4–5 also appears in Epiphanius, *Panarion*, Holl volume 2, page 495, lines
18–19 (TLG 2021.002). This guided a successful reinspection of the public scan.
The exact query around Bekker 296a41 returned only Photius and did not settle
the ending. Another search returned Photius and Damascius *Vita Isidori*
fragment 63 (TLG 4066.007), whose title explicitly identifies transmission
through Photius; those hits are not two independent witnesses. Queries,
citations, edition relationships, and outcomes are recorded without distributing
comparison text. These three searches were chosen for difficulty and do not
measure web-wide search coverage.

The practical sequence is to locate candidates locally, review each shared
scan crop once, and reserve web searches for uncertain quoted passages.
Comparison disagreements should trigger a glyph check, not automatic adoption
of the newer edition. No additional OCR run or GPU was needed for this pilot.

## Reproduction and timing

Run `python3 scripts/check_photius_pilot_predecessor.py --check`, or
`make check-photius-uncertainty-pilot`, to rebuild the historical experiment.
The adapter executes the archived original recipes and their complete local
import closure in an isolated directory, validates fresh public source crops,
and compares every output byte. Later restoration hooks therefore cannot
change the frozen experiment's code identity or results. The authored
`scripts/photius_uncertainty_pilot_observations.py` table remains unchanged.
This historical check does not modify the served corpus.

Optional retrieval requires the user's own comparison HTML. Keep excerpts
outside a public checkout:

```sh
python3 scripts/compare_photius_local_edition.py \
  --comparison-html "$PHOTIUS_COMPARISON_HTML" \
  --classification /tmp/photius-comparison-labels.json \
  --private-output /tmp/photius-comparison-private.json
```

Compare the resulting classification records and input pins with the frozen
map; elapsed time is a measurement rather than a byte-stable result. No
comparison text is needed to replay the public scan review or candidate undo.

Two parallel 34- and 33-span review intervals took 422.912 and 399.226 seconds,
with initial scan passes of 302.357 and 294.133 seconds. The remaining 33-span
initial interval was 112.761 seconds and excluded its first single-span crop;
additional comparison and independent spot-check time was not fully measured.
The intervals include tool and note preparation and overlap in wall time.
They are not a controlled throughput comparison or an estimate of human
proofreading speed. Grouping reduced 100 per-span crop visits to 26 distinct
crop inputs; narrow reinspection still added work.

## Served admission

`python3 scripts/repair_photius_uncertainty_admission.py --apply --admitted-at UTC_TIMESTAMP`
creates the later authority from the freshly checked source review. Subsequent
runs reuse the recorded timestamp. `--check` reproduces the served text and
admission records, including the historical source check; it is required by
`make check`. `--undo` restores the exact previous corpus and verifies unchanged
citation aliases without reading the live sources or the experimental archive.

The admission changes 65 spans in 28 display rows, confirms five unchanged
spans, and adds 86 eligible Greek tokens after preserving independent exclusions.
All 3,782 passage rows remain present. Its current uncertainty count is 2,977;
the frozen full campaign still records 3,069 and the preceding source review
still records 3,047. Quality, coverage, source-component, known-limitation, and
current historical-diagnostic outputs publish the effective measurement
separately from those historical counts.

The admission and tested release are tracked in
[issue #87](https://github.com/open-greek/open-greek-corpus/issues/87).
