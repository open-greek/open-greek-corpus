# Gutenberg identities and historical intake

The pinned GlossAPI artifact contains 214 documents. The reproducible audit
identifies every source through the official Greek catalog, bibliographic
records, and full-text fingerprints. It does not use the supplied variety
classifier as admission evidence.

## GlossAPI collection

`data/glossapi_gutenberg_sources.json` retains stable bibliographic facts and
the checksums of the downloaded catalog and reading editions. The discovery
catalog is retained under `data/reference/gutenberg/`; downloaded whole books
remain in the local cache. Bibliographic snapshots exclude changing download
statistics. The upstream dataset revision and Parquet checksum remain owned
solely by `data/glossapi_source_decisions.json`.

`data/glossapi_gutenberg_identity_report.json` records every Text Number, title,
catalog candidate, resolved URL, contributor, source comparison, quality
measurement, and disposition. Text Numbers are upstream identifiers, not row
positions or Gutenberg ebook numbers. The independent scope review is retained
in `data/glossapi_gutenberg_reviews.json`.

| Whole-document disposition | Documents |
|---|---:|
| Modern Greek composition or translation, excluded | 213 |
| Rouse's 1909 Lucian adaptation, quarantined | 1 |
| Eligible unaltered Ancient/Medieval whole text | 0 |

The primary evidence resolves misleading records: Ecclesiazusae is
Demetrakopoulos's 1910 verse paraphrase; Herodotus is Skalidis's 1874–1875
translation; the Vatican-manuscript New Testament is Pallis's 1902 translation.
Halima volume 1 is a 1921 printing whose transcriber replaced missing pages
65–80 with a new translation from English. A classical author's name, an old
story, or a Byzantine subject does not establish historical Greek wording.

Ordered word agreement and exact eight-word contexts distinguish text changes
from moved notes. Four documents (Text Numbers 17, 236, 324, 330) also need exact
32-letter contexts to match typographic letter spacing and relocated notes.
This source-identification comparison ignores word spacing and numeric note
references only in its own fingerprint. The original token counts and all
word-level differences remain in the report. No lexical normalization, spelling
repair, or silent correction is performed. Matching a source is not a quality
approval. Embedded quotations need separate identification before admission.

Reproduce after installing the optional audit dependencies:

```sh
python3 -m pip install -r scripts/requirements-glossapi.txt
python3 scripts/audit_glossapi_gutenberg.py --fetch
```

The approved Hugging Face account supplies the already pinned dataset. Cached
source bytes are checked; missing or changed sources fail explicitly. Initial
discovery uses `--pin --pins NEW_MANIFEST_PATH`; it refuses to overwrite an
existing manifest. A changed reading edition requires renewed assessment.

Edition records retain their stable ebook identifiers in the `gutenberg`
alias namespace. The bibliographic identifier does not replace the OGC work ID.

## Separate historical catalog discoveries

The broader Greek catalog also identifies three originals absent from the
GlossAPI artifact. They are independently pinned in
`data/gutenberg_historical_sources.json`, with unchanged catalog and reading
HTML retained in `data/reference/gutenberg/`. They do not add observations to
the GlossAPI coverage or frequency experiments.

| Gutenberg ebook | Work | Disposition |
|---|---|---|
| 37641 | Athanasius, *In illud: Omnia mihi tradita sunt* | Six native Greek sections admitted; Latin translation and notes stay outside lexical text. The cited edition is Gutenberg's 2011 digital transcription. Its unnamed printed exemplar is not represented as a particular Migne impression. |
| 66595 | *Res gestae divi Augusti*, Greek version | Fairley's 1898 Philadelphia edition admitted at 436 native lines across 19 inscription columns. The anonymous ancient Greek translation is distinguished from Fairley's modern English translation. |
| 32549 | *Expositio fidei*, CPG 2804 | Four native Greek sections admitted under OGC's existing Marcellian work key, with both the traditional Athanasian attribution and the disputed Marcellian catalog attribution retained explicitly. |

[BiblIndex's edition record](https://dapytains.biblindex.org/en/work-edition/7967)
identifies CPG 2804 with Nordberg's 1962 pages 49–56; the
[Pinakes work record](https://pinakes.irht.cnrs.fr/notices/oeuvre/id/6423)
identifies the same work. These bibliographic records establish the canonical
mapping, not the text source or a settlement of authorship. The Greek text is
the pinned Gutenberg 2010 digital edition. Both attribution readings and their
evidence remain structured in every passage and the work index. OGC's existing
work key does not turn a contested attribution into a certainty.

The duplicate scan compares exact accent-folded eight-word contexts at every
token position against all existing primary corpus files. It records all file
hashes, the corpus snapshot hash, candidate-token hashes, and passage witnesses.
Cross-work quotations are reported as overlaps, not automatically deleted.
Admission outputs are omitted from their own baseline comparison, making replay
and undo stable. A changed baseline or candidate extraction invalidates the scan.

The inscription uses OGC's existing critical-text schema and validator. Printed
restorations, gaps, and line continuations survive in the reader; complete,
certain words alone contribute to `analysis_text`. Three source-printed word
continuations cross columns. Their fragments remain uncounted rather than
being guessed into words. Spaced full stops mark lacunae; neighboring tokens
whose word boundaries are uncertain remain uncounted even when the HTML adds
whitespace. Reader credits and licenses come from the actual source metadata.
Apparatus readings are preserved in
`data/paratext/gutenberg/`; the publisher's 27 reported Greek corrections retain
both readings and their source references in the admission audit. OGC applies
no new text correction.

```sh
python3 scripts/ingest_gutenberg_historical.py --scan-corpus
python3 scripts/ingest_gutenberg_historical.py --apply
python3 scripts/ingest_gutenberg_historical.py --check
python3 scripts/ingest_gutenberg_historical.py --undo
```

`--apply` and `--undo` refuse independently modified outputs. The structured
audit in `data/corpus_changes/gutenberg-historical/changes.json` records source,
generator, duplicate-report and output hashes. Undo removes only unchanged
admission outputs and retains the source evidence and audit.
`--undo` verifies the recorded output hashes without reloading the source, so
an invalidated source can still be removed safely. Rebuild shared
IDs, registry, corpus statistics, quality reports, and public lexical exports
after applying or reversing admission. Historical intake remains OGC-owned;
experimental Modern Greek frequencies and Dilemma's production rankings are
unaffected.

After new independent identity evidence changes routing, `--refresh-review`
regenerates the review fields while checking that every retained source byte
is unchanged. Run `--scan-corpus` again before applying that revised admission.
