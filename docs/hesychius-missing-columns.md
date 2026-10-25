# Hesychius columns 259–260

The original Schmidt scan, Internet Archive
[`hesychiialexand00schmgoog`](https://archive.org/details/hesychiialexand00schmgoog),
repeats printed columns 247–258 and then advances to 261–262. The missing leaf
is present in two other copies of Schmidt's 1867 *editio altera, indice glossarum
ethnicarum aucta*:

| Copy | Edition title | Preceding leaf | Recovered leaf | Following leaf |
| --- | --- | --- | --- | --- |
| [Harvard](https://archive.org/details/bub_gb_R-zVabafOucC) | PDF page 8 | PDF page 150: 257–258 | PDF page 151: 259–260 | PDF page 152: 261–262 |
| [Ghent](https://archive.org/details/bub_gb_PNI9AAAAcAAJ) | IA leaf 10 | IA leaf 178: 257–258 | IA leaf 179: 259–260 | IA leaf 180: 261–262 |

Internet Archive leaf numbers in the Ghent row are zero-based. They are not
printed page or column numbers. Source artifact hashes, full-page evidence,
exact crop coordinates, renderer versions, and source review are retained in
`data/corpus_changes/hesychius-missing-columns/source-evidence.json`.

The preceding column ends with **αὐθέκαστα**; column 259 starts
**αὐθέκαστος**. Column 260 ends with **αὐλώνων** and a Euripides reference,
without a printed definition on that main-text line. Column 261 starts
**αὐλωπίαι**. The recovery does not invent a definition, promote a definition
from the editorial apparatus, or replace existing neighboring corpus readings.

Two pinned OCR checkpoints each transcribe both physical copies. The two
copies processed by one checkpoint share one vote group. Exact contrary
readings, omissions, raw predictions, and complete word networks remain
available. Parentheses, square brackets, and dagger-marked suspect lemmas
remain literal evidence but do not supply lexical votes. A recovered scalar
reading requires support from both checkpoint groups. Unresolved readings
remain variants; this disagreement count is not an OCR error rate.

The two main-text column records are inserted between historical extraction
loci `hesychius_masked_0149.75` and `hesychius_masked_0156.1`. The existing
duplicate-reviewed primary is an exact hash-pinned predecessor, and every old
row remains byte-for-byte unchanged. The new edition is
`schmidt-1867-gap-consensus-2026-10`; the eight literal OCR witnesses remain in
`data/corpus_secondary/hesychius-lexicography.lexicon-o.missing-columns-witnesses.jsonl`.

The printed `COD.` and `HES.` apparatus below the main columns remains visible
in both retained full-page images. It is outside this bounded main-text
addition. Context n-grams and positional evidence are not inferred from the
word projection.

Reproduce the retained source capture and check it offline:

```sh
python3 scripts/capture_hesychius_gap.py --write
python3 scripts/capture_hesychius_gap.py --check
```

Fresh OCR requires the MLX runtime and the pinned model revisions recorded by
`scripts/run_hesychius_gap_ocr.py`. Run each checkpoint with the retained source
manifest; generated raw OCR artifacts are hash pinned before admission. The
recovery itself replays from those retained predictions and images without
requiring a model or network connection:

```sh
python3 scripts/repair_hesychius_missing_columns.py apply
python3 scripts/repair_hesychius_missing_columns.py verify
python3 scripts/repair_hesychius_missing_columns.py undo
```

The structured addition audit records the empty original passage, added
surface and analysis readings, all source witnesses, boundaries, evidence,
timestamp, recipe hashes, and exact preimages. Undo removes the additions and
restores the complete predecessor byte-for-byte even if a new correction
source has been invalidated. Unapply this layer before unapplying the older
reviewed-duplicate layer.

## Reading review

The later review in `data/corpus_changes/hesychius-gap-reading-review/` inspects
all 45 excluded alignment slots against both retained Schmidt column images.
It resolves 44 slots: 42 supply newly admitted words and two are duplicate
fragments belonging to words reconstructed once at the adjacent slot. The
columns therefore supply 251 eligible Greek tokens, up from 209. Reviewing the
same entries also corrects 16 shared OCR mistakes, including missing accents,
`αὐλίζαι` for printed `αὐλίξαι`, and `αὐλίσχοι` for printed `αὐλίσκοι`.

The scan review leaves the second headword inside the `αὐΐαχοι` entry unresolved at column 259,
slot 84. The retained copies do not establish its breathing and iota marks
confidently. Its original alternatives remain visible and excluded from scalar
frequency counts. The 45-slot figure measures the original alignment campaign,
not 45 independent erroneous words or an OCR error rate.

TLG's `4085.002` was consulted on October 24, 2026. It presents Latte's
1953/1966 edition for Α–Ο. Its alpha entries 8257–8317 identify the corresponding
material and help interpret rare headwords; they are comparison references,
not a new OCR vote. Every reading admitted by this scan-review layer comes from independent inspection
of both Schmidt images. In particular, Schmidt's `σπεῖραν`, `διῶρυξ`, and
`αὐοὶ` are retained despite different Latte readings. No later edition's dagger,
apparatus, or definition is transferred into Schmidt's main text.

The review observations are reproducible inputs in
`scripts/hesychius_gap_reading_observations.py`. Each generated change record
retains the original slot and surface, corrected reading or explicit hold,
both image paths and hashes, printed entry, TLG comparison citation, explanation,
and timestamp. All original checkpoint readings, support groups, omissions,
abstentions, and critical-scope exclusions remain unchanged. Neither model
agreement nor scan review supplies contextual adjacency for this projection.

```sh
python3 scripts/repair_hesychius_gap_readings.py apply
python3 scripts/hesychius_gap_state.py --check
python3 scripts/repair_hesychius_gap_readings.py undo
```

Undo restores the complete pre-review recovery byte-for-byte without requiring
the correction evidence to remain valid. Reapplying reproduces the frozen
postimage and audit. Unapply this reading layer before undoing the missing-leaf
recovery. The current-state verifier composes these authorities without editing
the frozen recovery recipe or waiving any of its other output checks.
Per-work frequency counters revalidate the source-recovery authorities before
reuse, so a cached count cannot bypass invalidation of a retained scan.

## Adopted Latte reading

On October 25, 2026, the owner selected Latte's `ἀΐαχοι` (alpha 8275, TLG
`4085.002`) for column 259, slot 84. The separate producer
`scripts/adopt_hesychius_latte_reading.py` adds it above the frozen scan review.
The occurrence is marked `editorially-adopted`, with the later edition's exact
citation and the owner's decision. It is not labeled as a confirmed Schmidt
reading: the uncertain printed diacritics and the original held decision remain
in the full word network alongside all original OCR votes and alternatives.

The columns now supply 252 eligible Greek tokens. No uncertain recovered-column
occurrences remain excluded from lexical counts; the two duplicate fragment
slots stay omitted. The quality report still identifies
one unverified Schmidt reading and one credited editorial adoption. The earlier
review's 44 scan-resolved slots, two merged fragments, and 16 shared-error
corrections retain their original records.

```sh
python3 scripts/adopt_hesychius_latte_reading.py apply
python3 scripts/hesychius_gap_state.py --check
python3 scripts/adopt_hesychius_latte_reading.py undo
```

`data/corpus_changes/hesychius-latte-reading/changes.json` records the original
and adopted text, source citation, timestamp, recipe and source hashes, and
exact preimage. Undo restores the complete pre-adoption primary byte-for-byte,
including its excluded slot, without requiring the adoption's evidence to
remain valid. Unapply this layer before unapplying the earlier scan review.
