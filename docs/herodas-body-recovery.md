# Herodas body recovery

The recovery adds the missing authorial body pages from Headlam–Knox's 1922
edition to `herodas.mimiambi`. It preserves every reading and identity in the
62 previously published passages. The work remains `ogc001716`, with edition
`herodas-hk-ocr`; existing passage aliases and the editorial sidecars remain
unchanged. A new passage represents one recovered physical source page, not one
metrical verse.

| Scope | Physical body pages | Primary passages | Analysis tokens |
| --- | ---: | ---: | ---: |
| Published excerpt, preserved literally | 13 | 62 | 2,036 |
| Missing pages recovered | 22 | 22 | 2,918 |
| Combined primary text | 35 | 84 | 4,954 |

This covers the inventoried body printed as Mimes I–VIII, IX with IXa/IXb, X,
and XI. It does not imply that the ancient works survive complete, settle every
fragment attribution, or certify the OCR spelling of the old excerpt.

## Source boundaries and attribution

The source is Walter Headlam's notes, edited by A. D. Knox, *The Mimes and
fragments* (Cambridge, 1922), in the
[Internet Archive UCLA scan](https://archive.org/details/mimesfragments00hero).
The PDF is retained at
`data/corpus_changes/editorial-role-review/source-herodas.pdf`, with SHA256
`6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a`.
It contains 542 PDF pages. In the reviewed body, the printed page is the PDF
page minus 70.

`scripts/herodas_body_source_observations.py` records the 35 body regions,
verse boundaries, 13 already represented pages, and separate attribution holds.
The 22 additions are disjoint from those existing pages. Facing English,
running headings, speaker labels, and apparatus do not become authorial text.
Printed losses remain, including the damaged passages of VIII and XI's terminal
eight-dot loss. On PDF page 486, the full XI region includes that loss; the
separately pinned recognition crop ends above it. The loss is documented by
direct scan review, without claiming it occurred in that recognition output.

The inventory keeps the IXc source note and conjectural Xa, Xb, XIa, and XIb
quotations on attribution hold. Greek renderings of Latin Mattius by Headlam
and Knox are modern editorial compositions and remain excluded. The unplaced
papyrus on PDF page 493 supplies only a letter remnant, not an admitted lexical
form. These decisions concern this edition's evidence; Greek language or
body-sized type alone does not establish Herodas authorship.

## Recognition evidence and source readings

Historical Qwen3.6 predictions and fresh, revision-pinned Qwen3.8 predictions
are preserved as distinct recognition witnesses. The earlier 8B predictions
remain diagnostic evidence and cast no vote. Historical model revisions and
prompt hashes that were not recorded remain explicitly unknown.

`scripts/herodas_body_witness_observations.py` separates authorial spans from
the historical recognition's other source roles. Fresh speaker exclusions also
require source-identified labels; any accepted recognition variant is tied to
its literal prediction hash. The merger retains conflicting readings and the
original predictions. Agreement between recognizers does not prove a printed
reading is correct.

The source readings in `scripts/herodas_body_readings_a.py`,
`scripts/herodas_body_readings_b.py`, and `scripts/herodas_body_readings_c.py`
form a separate review layer above that unchanged merged evidence. The compiler
records original and corrected text, literal character edits in both directions,
source page and scan hash, evidence, and review time. This is a named source
decision, not an extra recognition vote. The merged result before source review
remains recoverable.

Unclear glyphs have exact occurrence offsets and retained alternatives, or an
explicit abstention. Printed supplies, cruces, damaged and incomplete words,
and words adjoining source losses stay outside the new scalar lexical counts.
Bracket state crossing a page boundary is source evidence: VIII's outer range
opens on PDF page 440, continues before a nested opener on page 442, and closes
at the printed double bracket. It is not silently reset at a page boundary.
New recovery rows provide checked `analysis_text` for scalar counts. They
supply no positional or bigram evidence.

The counts distinguish `raw_ocr_unresolved_slots` in the original merged
recognition, `unresolved_slots` in the source-reading review, and
`new_noncountable_slots`, which also includes critical exclusions. These are
different scopes, not measurements of character error rate. The quality report
keeps the older source-role partition's historical counts and exposes the later
body recovery separately.

The recovered pages contain 45 unresolved source-reading slots. There are 155
noncountable slots in total, including printed supplies, damage, and critical
exclusions. The raw merged recognitions retain 856 unresolved slots separately;
source review resolves most of those disagreements without discarding them.

## Retained authority and replay

`data/corpus_changes/herodas-headlam-knox-body/` contains `changes.json`, the
literal `before.json.gz`, historical witnesses, the recognition request and raw
fresh predictions, generated source inventory and source readings, and
reversible occurrence records. The audit pins these files and the replay
recipes. Verification also rerenders the pinned scan crops and checks the
recognition image hashes.
Initial admission installs the complete audit authority before atomically
replacing the primary file. An interrupted primary replacement leaves the
literal predecessor available and can resume through archived `--apply`.

Before first admission, build a missing-page recognition request from the exact
published excerpt with:

```sh
python3 scripts/prepare_herodas_body.py --missing-only --out REQUEST.json
```

This command prepares a request and admits no text. A pilot is available with
`--pilot`. Archive historical witnesses with
`scripts/herodas_body_witnesses.py --legacy-root LEGACY_ROOT --redo-root REDO_ROOT
--pages PDF_PAGES --out WITNESSES.json.gz`, where `PDF_PAGES` is the explicit
comma-separated missing-page inventory. Recognition runs use
`scripts/run_scan_ocr.py`; their model, revision, runner, prompt, and image
metadata are retained. Initial admission requires those checked inputs:

```sh
python3 scripts/repair_herodas_body.py --apply \
  --witnesses WITNESSES.json.gz --request REQUEST.json \
  --predictions PREDICTIONS.jsonl --reviewed-at ISO_TIMESTAMP
```

The current checkout replays its retained authority without new recognition:

```sh
python3 scripts/repair_herodas_body.py --check
python3 scripts/herodas_current_state.py --check
make check-herodas-body check-editorial-roles check-phoenix-crusius
```

`herodas_current_state.py` verifies the later recovery before exposing the exact
62-passage predecessor to the frozen editorial-role validator. The citation,
Phoenix, and Photius adapters compose with that view. Source, recipe, or core
changes invalidate the proof; earlier published repair recipes and audit bytes
are not rewritten.

## Undo and the earlier role review

Restore the exact published excerpt with:

```sh
python3 scripts/repair_herodas_body.py --undo
```

Undo checks the literal preimage archive and current output before writing. It
does not need the source PDF, recognition witnesses, or source-reading packet to
remain valid. It changes only the Herodas primary and refuses a modified
postimage. With sources still valid, `--apply` replays the archived additions.

To undo earlier repairs too, remove this body layer first, then follow the
[editorial-role review](editorial-role-review.md). Its 136-row Herodas partition
and Hipponax decisions remain separate historical facts. Current metadata also
recognizes verified chronological undo of those earlier layers. After undo or
reapply, rebuild the derived coverage, registry, quality reports, and lexical
exports through the [normal corpus pipeline](../README.md#build) before
publishing.
