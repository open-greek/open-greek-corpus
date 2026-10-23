# Acharnians source pilot

The primary labeled as Acharnians scholia contains extracts from throughout the Dübner 1855 volume. This frozen ten-page assessment changes no served text or lexical exports.

The title page verifies *Scholia graeca in Aristophanem*, Friedrich Dübner, Paris, Ambroise Firmin-Didot, 1855. The University of Toronto scan is [publicly available](https://archive.org/details/scholiagraecaina00dbuoft). The pinned PDF has 776 access pages; source XML has 782 leaves, six excluded from access formats. The sampled PDF page numbers match the scan leaf numbers; printed pages are separate.

## Measured source scope

| Page region | Served pages | Rows | Greek tokens |
| --- | ---: | ---: | ---: |
| Front matter and grammatical prolegomena (PDF 1–42) | 28 | 649 | 10,909 |
| Acharnians hypotheses and scholia (PDF 43–73) | 31 | 1,490 | 21,078 |
| Subsequent plays' hypotheses and scholia (PDF 74–430) | 356 | 14,417 | 245,386 |
| Dübner's critical annotation (PDF 431–656) | 226 | 4,637 | 70,036 |
| Editorial indexes (PDF 657–776) | 101 | 3,792 | 6,646 |

All 24,985 rows and 354,055 Greek tokens are accounted for. 332,977 tokens (94.05%) are outside the Acharnians page block. The critical annotation and indexes contribute 76,682 tokens. This does not make the other plays' historical Greek noise. The regions are conservative source-scope measurements, not a finished carve: hypotheses, quoted poets, manuscript sigla, conjectures, and other intra-page roles still need occurrence-level classification.

## Ten inspected pages

Purposive source-role sample fixed before compiling metrics, not a random OCR accuracy sample: edition title; first, midpoint, and last Acharnians pages (43, (43+73)//2, 73); first subsequent play; midpoint of the later play block (74+429)//2; first and midpoint of the critical annotation (431, (431+656)//2); index title; last served page.

| PDF / printed page | Source role | Served rows | Greek tokens |
| --- | --- | ---: | ---: |
| [9 / unnumbered](../data/audits/acharnians-source-pilot/page-0009.png) | edition title | 0 | 0 |
| [43 / 1](../data/audits/acharnians-source-pilot/page-0043.png) | acharnians start | 40 | 530 |
| [58 / 16](../data/audits/acharnians-source-pilot/page-0058.png) | acharnians midpoint | 31 | 734 |
| [73 / 31](../data/audits/acharnians-source-pilot/page-0073.png) | acharnians end | 10 | 193 |
| [74 / 32](../data/audits/acharnians-source-pilot/page-0074.png) | next play start | 11 | 525 |
| [251 / 209](../data/audits/acharnians-source-pilot/page-0251.png) | later plays midpoint | 8 | 592 |
| [431 / 389](../data/audits/acharnians-source-pilot/page-0431.png) | annotation start | 11 | 189 |
| [543 / 501](../data/audits/acharnians-source-pilot/page-0543.png) | annotation midpoint | 50 | 254 |
| [657 / 615](../data/audits/acharnians-source-pilot/page-0657.png) | index title | 0 | 0 |
| [768 / 726](../data/audits/acharnians-source-pilot/page-0768.png) | last served page | 86 | 156 |

Ten purposively selected pages were visually inspected for source identity, roles, and extraction failures. They were not exhaustively transcribed or proofread. No population OCR error rate is estimated; 17.0507% unattested is a lookup diagnostic, not an error rate.

## Extraction findings

The sampled Acharnians rows retain a truncated heading, an omitted eta in Ἀθηναίοις, mixed Greek/Latin letters, and a false split of τήνελλα into τὴν ελλα. The annotation sample omits an entire printed note and attaches spurious numbers to Greek words. The final index uses three columns, while the old provenance describes a two-column mask. These are distinct problems; a dictionary-frequency correction would not repair the wrong work boundaries or restore omitted source notes.

Exact original strings, proposed readings where justified, scan evidence, review date, and baseline/source pins are in `report.json`. They are observations only. No correction was admitted, and no printed variant was selected by an arbitrary vote.

Qwen served text and Tesseract embedded PDF text are separate OCR passes of the same scan. Unaligned bag overlap is not textual agreement or an accuracy score. No independent public edition has been collated; the catalog's Wilson 1975 reference is not an eligible served witness.

## Reproduction

Offline verification uses only the standard library:

```sh
python3 scripts/audit_acharnians_source_pilot.py --check
python3 scripts/audit_acharnians_source_pilot.py --check-current
```

The first command verifies the frozen audit even after a future source repair. The second also requires the currently served primary to match the assessed baseline. To reproduce the retained images and PDF text layer, download the pinned PDF and scan XML URLs listed in the manifest, then use PyMuPDF 1.28.2:

```sh
python3 scripts/audit_acharnians_source_pilot.py --prepare \
  --source-pdf /path/to/scholiagraecaina00dbuoft.pdf \
  --scan-xml /path/to/scholiagraecaina00dbuoft_scandata.xml
python3 scripts/audit_acharnians_source_pilot.py --check
```

The PDF remains an external cache input; the ten rendered pages, same-scan OCR extracts, scan XML, frozen primary, and published baseline catalog row are retained with checksums. Preparation rejects changed sources, changed current primary or catalog row, or a different renderer; the normal checker needs neither network access nor PDF rendering.

## Admission design

The [published source-scope defect](https://github.com/open-greek/open-greek-corpus/issues/102) is the outstanding-work record. A safe repair should establish an edition-wide work/role inventory before spelling review: distinct play scholia and hypotheses; separately attributed grammatical prolegomena; and out-of-line critical annotation and indexes. Preserve all old loci through citation aliases and literal archives. Review intra-page quotations and variants, then measure deduplication against already served works before assigning new identities or counting tokens. Reuse the existing reversible source-role, citation-alias, and lexical-projection gates, with exact replay/undo and source invalidation; do not republish the entire volume under a newly invented author identity.

The pilot makes no completeness claim for the Acharnians text and provides no license to replace uncertain readings with a restricted digital edition.
