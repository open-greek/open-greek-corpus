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
