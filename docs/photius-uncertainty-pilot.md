# Photius uncertainty pilot

The October 21, 2026 experiment visually assessed 100 of the 3,047 remaining
source uncertainties, grouped into 26 pinned Bekker crops on 26 physical pages.
It proposes 65 text corrections and confirms five existing readings; 30 spans
remain uncertain. These are isolated candidates, not served admissions. The
published corpus still has 3,047 uncertainties. Admitting these decisions would
leave 2,977 source uncertainties, while independent fragment, nonbody, and
contrary-reading exclusions would still apply.

The original complete campaign, occurrence-context layer, 33-span source review,
and every served corpus file remain unchanged. The structured experiment is in
`data/corpus_changes/photius-bekker-uncertainty-pilot/`. Its audit pins exact
preimages, source PDF and rendered images, authored decisions, code recipes,
and candidate postimages. It includes literal replay and undo without live
correction sources. The frozen preimage permits later checking even after a
subsequent corpus admission.

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

Run `python3 scripts/prepare_photius_uncertainty_pilot.py --check`, or
`make check-photius-uncertainty-pilot`, to rebuild and compare the public
experiment. `--write` creates its immutable archive from the authored
`scripts/photius_uncertainty_pilot_observations.py` table. The check is also
required by `make check`. Neither action modifies the served corpus.

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

Production admission remains a separate operation: it must add a later authority
without rewriting the frozen prior layers, preserve all independent exclusions,
rebuild the public lexical and quality exports, and pass the release checks.
The candidate archive does not satisfy those production gates by itself.
Production admission is tracked in [issue #87](https://github.com/open-greek/open-greek-corpus/issues/87).
