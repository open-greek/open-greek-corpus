# Reviewed repeated Cyril and Hesychius passages

Two OCR extractions counted physical passages more than once. Cyril's PG073
markers 483–486 recur as 487–490. The pinned reference scan and its surrounding
leaves establish the continuous text. Hesychius's extraction page 143 contains
38 lines repeated at the beginning of page 150, which also has 35 additional
lines. Both scan frames reproduce printed columns 247–248. The merged passage
belongs before the retained page 145, preserving the physical reading sequence.

`scripts/repair_reviewed_duplicate_blocks.py` collates the five passages with
one upstream vote group per source. Disagreements remain explicit alternatives;
no lexicon chooses a winner. The five primary records replace 119 literal rows.
Those exact originals remain in two attributed secondary witness files, and
every old passage citation resolves to its literal text with a current target.
The audit stores original and merged text, full networks, source evidence,
timestamps, and exact preimages for reversal.

The original repeated blocks contain 3,989 Greek tokens. Their merged surface
contains 2,241 tokens; the checked scalar projection contains 1,932. These are
different accounting bases: excluded uncertainties are not described as duplicate
words removed. The network retains 149 unresolved slots and one damaged slot.

```sh
python3 scripts/capture_reviewed_duplicate_sources.py --check
python3 scripts/repair_reviewed_duplicate_blocks.py verify
```

The capture producer verifies pinned PDFs and reconstructs the retained page
images and source observations. The repair's `undo` action restores every exact
preimage even if source evidence is removed; `apply` reproduces the frozen
repair. Both refuse to overwrite later changes. Rebuild derived metadata and
frequencies after applying or undoing. Older Cyril coverage and Hesychius
assignment validators use only the verified historical preimages.

The refreshed diagnostics recognize dotted PG markers as page runs and flag
asymmetric partial overlaps. No served clean CGPG duplicate pairs or repeated
runs remain. Unrelated similarity candidates remain visible as review indexes.
The source scan omits Hesychius's printed columns 259–260; this separate coverage
gap is not recovered by deduplication.
