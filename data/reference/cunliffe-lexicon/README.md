# Cunliffe's Homeric Lexicon (structured)

Reference material, not a served text work. This directory holds a structured,
machine-readable copy of the main body of Richard John Cunliffe's *A Lexicon of
the Homeric Dialect* (1924, public domain): every headword with its senses,
sub-senses, definitions, and Homeric citations, with each citation linked to a
canonical CTS URN and resolved to Iliad/Odyssey book and line.

It complements the grammatical appendix already in this repo under
`data/reference/cunliffe-appendix/` (Cunliffe's conditional / relative-sentence
table). The lexicon body here and the appendix table there are the two
public-domain parts of Cunliffe; together they make his 1924 work usable as
structured reference data.

## Status: reference, not a served work

This is reference / bonus material alongside the corpus, not part of the served
running-text corpus. It is a lexicon (reference), not a text edition, so:

- It does not enter the source-precedence ladder.
- It is not assigned a served work-id, and is not listed in `corpus_editions.json`
  or the work-id registry.
- It lives under `data/reference/`, entirely separate from `data/corpus/`.

## Provenance

- Work: Richard John Cunliffe, *A Lexicon of the Homeric Dialect* (London: Blackie
  and Son, 1924). The 1924 text is public domain (US public domain since 2020).
- Digital encoding: TEI EpiDoc by the Perseus Digital Library (Perseus Project,
  Tufts University), edited by Gregory Crane, "with many, many corrections by
  Helma Dik." Source TEI: https://github.com/gregorycrane/Homerica
  (`cunliffe.lexentries.unicode.xml`).
- Structuring: the Scaife-Viewer "Beyond Translation" project restructured the TEI
  into citable ATLAS JSON, with every Homer citation linked to a canonical CTS URN.
  Source JSON: https://github.com/scaife-viewer/beyond-translation-site
  (`backend/data/annotations/dictionaries/cunliffe-1-lex.json`).
- This directory is a faithful re-serialization of that structured data into COG's
  reference layout; see `manifest.json` for the exact source checksum.

An independent flattened plain-text transcription of the same 1924 lexicon also
exists (archive.org item `CunliffeHomericLexicon`, file `cunliffe.html`). It is a
markup-stripped export of the same Perseus text and is useful only as a
cross-check, not as a source: the structured Perseus/Scaife data used here keeps
the sense structure and resolves every citation to an exact book and line, which
the flat export cannot.

## Scope: lexicon only

Cunliffe's companion index of Homeric proper and place names is a separate, later
work still under United States copyright (public domain only from 1 January 2027).
It is deliberately not included in this public repository.

## License

- Underlying text: public domain (Cunliffe 1924).
- Digital encoding and Helma Dik's corrections: released by the Perseus Digital
  Library under Creative Commons Attribution-ShareAlike 4.0 International
  (CC BY-SA 4.0), the license Perseus applies to its TEI text corpora and lexica
  (cf. `PerseusDL/canonical-greekLit` and `PerseusDL/lexica`, both CC BY-SA 4.0).
  The 1924 text is public domain; the TEI encoding and the corrections are the
  licensed derived scholarly layer.
- Share-alike: CC BY-SA 4.0 requires attribution (Perseus Digital Library / Tufts
  University; ed. Gregory Crane; corrections Helma Dik; ATLAS structuring by the
  Scaife-Viewer Beyond Translation project) and share-alike on derivatives. This is
  compatible with COG's own CC BY-SA 4.0 license.

## Structure

Each entry in `cunliffe_lexicon.json`:

- `headword` - the lemma, Greek verbatim (digamma ϝ and metrical breve/macron
  preserved).
- `headword_raw` - the headword as encoded, including any leading marker.
- `dagger` / `asterisk` - Cunliffe's leading markers as booleans: `†` marks a word
  attested only in inflected forms; `*` marks a reconstructed / assumed form. These
  follow Cunliffe's TEI; a later Beyond-Translation extraction dropped them from the
  headword field, so they are restored here as explicit flags.
- `content_html` / `content_text` - the head block as encoded by Perseus
  (inflectional endings, gender, etymology bracket, and cross-references), in the
  original HTML and as plain text.
- `senses[]` - each sense has `label`, `definition`, `citations[]`, an optional
  `subsenses[]` (nested to depth 6), and its `source_urn`.
- `source_urn` - the entry's ATLAS URN, for traceability back to the source.

Each citation:

- `ref` - the human-readable reference (e.g. `Il. 14.113`).
- `quote` - the quoted Greek phrase, when the source provides one.
- `corpus` / `book` / `line` - derived from the CTS URN (`il` = Iliad, `od` =
  Odyssey), matching the citation format used by `cunliffe-appendix`.
- `cts_urn` - the canonical CTS URN
  (`urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:BOOK.LINE` for the Iliad,
  `tlg0012.tlg002` for the Odyssey).

## Totals

- 9,783 entries (9,783 with a headword; 5,228 with explicit numbered senses).
- 19,925 senses including sub-senses (nested to depth 6).
- 67,792 Homeric citations; 67,790 resolved to an exact book and line (the two
  unresolved are empty citations in the source). Iliad 36,012 / Odyssey 31,778.
- 745 entries carry Cunliffe's `†` marker, 1 the `*` marker.

Exact counts and source checksums are in `manifest.json`.

## Files

- `cunliffe_lexicon.json` - the structured entries (authoritative).
- `cunliffe_lexicon_index.json` - headword -> entry-id index for lookup.
- `manifest.json` - machine-readable provenance, license, structure, totals, and a
  checksummed file list.

## Rebuild

`cunliffe_lexicon.json` is generated by `scripts/build_cunliffe_lexicon.py` from
the public Beyond-Translation ATLAS JSON:

```
python3 scripts/build_cunliffe_lexicon.py --lex /path/to/cunliffe-1-lex.json
```

Obtain `cunliffe-1-lex.json` from the Beyond-Translation repository linked above.
