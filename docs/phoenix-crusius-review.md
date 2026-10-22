# Phoenix: work boundary and source review

The former `phoenix.fragmenta` file was a mixed extraction of Crusius's second
edition of *Herondae Mimiambi* (Leipzig, Teubner, 1894), including its appended
*Phoenicis Coronistae* and *Mattii Mimiamborum fragmenta*. It contained 2,749
rows and 29,998 Greek regex tokens. Most of those rows were not Phoenix.

The title on physical scan page 9 identifies the edition. The scan images are
two-page spreads. The right side of physical page 68, printed page 83, begins
`PHOENIX COLOPHONIVS / ΚΟΡΩΝΙΣΤΑΙ`; its left side still contains Herodas's
disputed material. The left side of physical page 69, printed page 84,
concludes Phoenix before its apparatus. Its right side begins Mattius.
The registered Phoenix body is exactly 21 verses: the old loci
`phoenix_choliambi_crusius_0068.3` through `.17`, then
`phoenix_choliambi_crusius_0069.1` through `.6`, in numeric order.

The scan is [Internet Archive item herondaemimiamb01hero](https://archive.org/details/herondaemimiamb01hero).
Its bundled PDF has SHA-256
`999122f204d54ec0071749c354598adef4203ea6fc61b53e4a6b0f5df92aade1`.
`scripts/phoenix_crusius_source_observations.py` records the exact old and
scan-reviewed readings, printed references, boundaries, supplies, and the
printed omission divider after verse 17. Eighteen verse rows change; three
are retained. The review does not normalize the source's dialect or replace
its readings with another edition.

The 2,728 other original rows are preserved, with unchanged text and prior
correction metadata, in `data/paratext/crusius-1894-legacy.jsonl`. This storage
contains unseparated other-work body, quotations, apparatus, and index matter;
it does not classify all of that material as modern paratext. It assigns no
new authorial identity and contributes nothing to primary lexical exports.
Every original locus resolves to either a current Phoenix verse or its retained
outside-work row. Phoenix keeps its existing work identity and expression ID
`ogc002809`. Herodas and other constituent primary files are unchanged.

Two historical OCR predictions survive in `ocr-witnesses.json.gz` under the
audit directory, with complete tagged predictions, Greek extractions, model
metadata, and original artifact hashes for scan pages 68–69. The historical
aligned output is a copy of the replacement prediction and is explicitly not
a third independent witness. No fresh OCR run is used as a substitute for
source inspection.

Printed angle supplies remain visible. Structured critical-text spans exclude
four supplied tokens from scalar counts, including the complete partially
supplied `<τού>τῳ`. The resulting 133 displayed structured tokens contribute
129 eligible lexical tokens. The quality report's Greek regex counts 134
surface runs because it splits that marked token; those two surface measures
have different counting bases. The source's divider between verses 17 and 18
is retained without assigning a length to the missing intervening material.

The quality report measures the whole historical file separately from the
same 21 verses before and after source correction. The original whole-volume
unattested rate was 7,082/17,001 checked tokens (41.66%). Within the actual
Phoenix verses it was 16/87 (18.39%), and after review it is 1/87 (1.15%).
The remaining flagged form, `Ἐσθλοί`, agrees with the scan. These are
case-sensitive comparisons against the non-OCR corpus, not recognition-error
rates. The large change in total served tokens is a work-boundary repair,
not a claim to have corrected the other rows.

## Reproduction and reversal

```sh
python3 scripts/repair_phoenix_crusius.py --apply \
  --source-pdf SOURCE.pdf --witness-root OCR_ROOT \
  --reviewed-at 2026-10-22T03:40:59Z
make check-phoenix-crusius
python3 scripts/repair_phoenix_crusius.py --undo
```

`OCR_ROOT` contains the historical `runs/editions` inputs named in
`scripts/phoenix_crusius_witnesses.py`. Initial application requires the pinned
scan and witnesses. The complete bundled authority then supports literal
replay, exact undo, and reapplication without external files. Undo restores
the primary and passage aliases byte-for-byte, removes the new outside-work
file, and retains the audit. Rebuild derived metadata and exports afterward.
Changed postimages, source evidence, or recipe files cause validation to fail.
Literal undo requires only the checked preimage archive, audit, and unchanged
served postimages, so invalidating or removing a correction source does not
prevent its corrections from being removed.

The audit in `data/corpus_changes/phoenix-crusius-review/` stores every original
and corrected row, destination, source evidence, and review timestamp, plus
compressed exact preimages and pinned outputs. Published audit and recipe
files must remain frozen; a later correction needs a new reversible layer.
This manifestation contains *Coronistae* only and does not claim coverage of
all surviving Phoenix fragments.
