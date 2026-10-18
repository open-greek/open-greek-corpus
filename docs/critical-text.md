# Critical text records

The P.Herc. 1026 admission uses `epidoc-spans-v1`. The corpus file is
`data/corpus/anonymous.p-herc-1026.jsonl`, one record per physical column/line.
The source EpiDoc remains unchanged at `data/pilots/dclp63141/source.xml`.
Its license is CC BY 3.0, credited to the Digital Corpus of Literary Papyri
and LDAB (Trismegistos); the manifest also records the source editors.

Do not reconstruct a critical edition from its `text` field. That field is
a display aid: unclear letters have underdots, restored letters have square
brackets, omitted letters have angle brackets, and letters surviving only
in apographs have upper half brackets. Damage and textual alternatives
cannot be represented adequately by a single ordinary string.

| Field | Meaning |
| --- | --- |
| `locus` | Physical column and line, matching the source's numbered textparts and `lb` elements. |
| `spans` | All source text, gap, and milestone spans, including unselected readings. Each has a stable local identifier, selection flag, and ordered source ancestors with element identifiers and exact attributes. |
| `reading_text` | The edition's explicit `lem`/`corr` reading, with source indentation collapsed and gaps represented by `…`; letters and diacritics remain unchanged. |
| `tokens` | Selected surface fragments with Unicode code point offsets into `reading_text`, source span identifiers, editorial status, lexical eligibility, and explicitly null lemma/analysis. |
| `analysis_text` | Only complete, certain, extant tokens. This is the frequency builders' lexical projection, not a reconstruction of the papyrus. |
| `physical_refs` | Document identifier, source textpart and line attributes, and matching custody events with image references. |
| `critical_markup` | Schema name, original source path, and source checksum. |

`supplied`, `apograph`, `unclear`, `corrected`, and `variant` token status
marks any token containing such a span. Tokens adjoining a gap are marked
`fragment`. When `lb break="no"` joins physical lines, the two visible
pieces remain separate tokens marked `line_fragment`. These are surface
fragments, not invented complete words; gaps create no tokens. None of
these classes enters the lexical projection. Alternative `rdg` and original
`sic` spans remain available without being concatenated into the selected
reading. Editorial notes and deletions are also excluded from that reading.

`scripts/ingest_dclp63141.py --apply` regenerates the corpus, manifest,
reader, and admission audit. `--check` verifies exact artifact reproduction.
`--undo` refuses independently edited output, then removes the admitted
work and reader while retaining the source and audit. Rebuild shared corpus
metadata after adding or removing the work.

The standalone reader in `data/critical_editions/dclp63141/reader.html`
distinguishes the editorial classes and exposes the source attributes,
alternative readings, token annotations, and physical references for each
line. Use `--format html --out reader.html` to export it, `--format jsonl
--out passages.jsonl` for all structured records, or `--format tei --out
source.xml` for the original EpiDoc bytes. The HTML uses no external scripts,
fonts, or network resources to display the edition. Its source links are
ordinary links opened only when selected.
