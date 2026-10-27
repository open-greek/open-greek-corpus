# Open Greek Corpus

An openly reusable corpus of Ancient, Medieval, and Modern Greek texts from
public-domain editions and attributed open sources.

The current export contains **3,939 works**, **1,913,663 passages**, and
**65,218,778 eligible Greek tokens**. Correction quality varies by work.
Unresolved readings remain excluded from lexical counts.

## Reading the corpus

`data/corpus/` contains one UTF-8 JSON Lines file per work. Each row supplies
`urn`, `locus`, `edition`, `source`, `license`, and the corrected reader `text`.
An optional `analysis_text` supplies the eligible lexical projection.
`analysis_segments` preserves contiguous eligible runs where omitted text
breaks adjacency. `contextual_eligible: false` excludes a row from measurements
that depend on complete surrounding context.

`data/work_index.json` supplies stable work and author identities, display
metadata, bibliographic anchors, and historical citation mappings. Bare
external identifiers are work references, not additional text sources.
`data/source_registry.json` and `data/corpus_editions.json` describe the sources
and editions. Follow each source's stated license and attribution requirements.

## Pinning and verification

Pin a tagged release and the content hash in `data/public_export.json`.
The manifest records every primary file's SHA-256 and per-work lexical totals.
The checks also verify bibliography input hashes against the published files.
`data/corpus_release.json` records the release identity and corpus scope.
History maintenance changes Git commit identifiers; use the published content
manifest to verify the files you consume.

Run the self-contained export checks with Python 3:

```sh
make check
```

The public repository contains selected text, publication metadata, lexical
exports, and data validation. Source-processing implementations, comparison
inputs, and working review records are not distributed with this export.

## Lexical exports

[Download the surface-frequency table](https://github.com/open-greek/open-greek-corpus/releases/download/corpus-2026-10-27/public_lexicon.tsv.gz)
for this release. Its decompressed format is `form<TAB>count`; checksums and
counts are in `data/public_lexicon_release.json`. The surface-frequency
table excludes duplicate passages and filtered nonlexical forms, so its token
count is lower than the inclusive corpus total. The public lemma
frequency tables are derived from this corpus's lexical projection.
`data/work_lemma_counts.tsv.gz` provides per-work lemma counts. Experimental
Modern Greek frequencies are separate from these production exports.

## Citation and license

See `CITATION.cff` for citation metadata and `LICENSE` for the repository license.
Individual text sources retain their own public-domain or open-license status.
