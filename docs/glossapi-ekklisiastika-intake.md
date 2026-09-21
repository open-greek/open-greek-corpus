# GlossAPI Ekklisiastika Intake

The pinned `glossAPI/Ekklisiastika_Keimena` artifact is an auditable discovery
source, not yet an OGC edition.  The dataset has a CC-BY-4.0 declaration and
title/category/subcategory metadata, but it identifies the GOARCH collection
root rather than a source URL and edition for each row.  It cannot enter
`data/corpus` on that evidence alone.

## Pinned artifact

- Revision: `e3e66c08c7a51beb96dc642e012c5ed3de946100`
- Artifact: `litourgical_texts.parquet`
- Size: `17,520,011` bytes
- SHA-256: `ec4d18951392d90650f96fe5232d2527aa4deed2164b171a8501e50b408593ae`
- Collection source: `https://glt.goarch.org/#02`

The complete pin and required admission gates live in
`data/glossapi_source_decisions.json`.

## Staging workflow

Run the deterministic staging audit from the repository root:

```sh
python3 scripts/stage_glossapi_ekklisiastika.py
```

The tool verifies the artifact before it reads it and produces
`data/glossapi_ekklisiastika_intake_report.json`.  It retains row provenance,
uses provisional `row:NNNN` and `row:NNNN.pNNNN` loci for review, removes
recognized rubrics, and repairs only explicit structural-label joins.  Any
unknown glued boundary stays quarantined rather than being guessed at.

It also marks labelled readings and quotations, checks exact and conservative
near duplicates within the source, and checks the same candidate passages
against the existing biblical, patristic, hymnographic, and liturgical corpus
families.  The Oktoechos tone cycles are therefore counted as witnesses to
review, not as fresh lexical evidence.

## Admission boundary

The staging command cannot admit rows.  It does not write `data/corpus`, does
not change corpus counts, and does not rebuild `public_lexicon.tsv`.  An editor
must first supply each accepted passage's per-record source URL, stable work
and edition identity, explicit locus mapping, and duplicate-witness precedence
decision.  Only then may the cleaned, identified passage enter the normal OGC
corpus build and subsequently the public lexicon.
