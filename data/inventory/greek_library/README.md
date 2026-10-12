# Greek Library discovery audit

Initial inspection: 2026-10-10. Reconciled 2026-10-12. The reviewed Alexius
Studites pilot is now served; the remaining rows are discovery candidates.
No Source Library text has been promoted to `data/corpus`.

## Reproduce

```sh
python3 scripts/audit_greek_library.py --fetch  # explicitly refresh the catalog pin
python3 scripts/audit_greek_library.py          # deterministic offline rebuild
python3 -m pytest tests/test_greek_library_audit.py
```

`catalog-pin.json` records the exact compressed catalog hash, retrieval time,
upstream release metadata and retained local path. The source catalog and
pilot evidence are retained under gitignored `sources/greek_library`; do not
delete them. `pilot-evidence.json` records retrieval URLs and checksums for the
sample reading files, original scans, scan metadata and original DCLP XML.
The catalog's release date does not describe all later additions; pin bytes.

`edition-audit.tsv` contains all edition metadata and decisions. Excluded
editions are metadata only: the auditor does not retrieve their texts.
`source-library-gaps.tsv` contains explicit CC BY-SA 4.0 Source Library candidates
without served anchor matches or reviewed volume overlaps. `dclp-candidates.tsv`
and `ocr-candidates.tsv` are separate review lists. `summary.json` pins local
inputs and gives edition/work-key counts.

All rows still need review. No license/provenance label is a quality endorsement.
TLG-E, CLLG and Vesuvius origins are excluded; NC/ND edition licenses are excluded
even when a collection-level license is open. Source Library's catalog license
does not override its upstream restrictions on bulk extraction or database reuse.
Use these rows for discovery only until the individual edition has independently
verified reuse rights; otherwise transcribe a reusable institutional scan.

## Identity limitations

An unmatched work identifier is not proof of a missing work. Work-index anchors
and catalog anchors are checked separately: Euripides uses alternate numbering
in the two local tables. Title equality is only a flag and is capped at ten
displayed matches, with the full count retained. Generic titles such as
*Fragmenta* must not be merged automatically. Papyrus witnesses are not
automatically identified with literary works. Manuscripts and printed editions
must stay distinct manifestations.

The initial Source Library screen had 1,877 editions / 1,323 work keys. Pilot
review removed two overlapping editions, leaving 1,875 / 1,322 in that initial checkout (another edition
of one of the overlapping works remains unreviewed). These are candidates,
not 1,322 certified new texts. Reconciliation against the current main-branch inventory yields 1,979 Source Library
editions / 1,341 work keys, 162 DCLP entries, and 582 independent OCR candidates after the reviewed Alexius import.
The change in matches is an inventory difference, not proof of new coverage. The more detailed machine-readable review is `pilot-review.json`.

## Pilot findings

| Candidate | Result | Required action |
|---|---|---|
| Achmet, *Oneirocriticon*, 1603 | Hold for quality. The fragmentary opening is authentic to this edition. Scan order puts printed p. 27 between pp. 274 and 275; the reading file follows it. Recognition errors remain. | Reconstruct printed-page order, audit duplicated/missing leaves, correct against scans. |
| Zosimus, *De aqua divina composita* | Already present inside `zosimus-alchemista.opera` under a different work anchor. The local file also has fragmented OCR records. | Carve and compare witnesses against printed pp. 154-156; do not count as new coverage or replace wholesale. |
| *Aethiopis*, Evelyn-White 1920 | Proclus summary already present inside `panyassis.fragmenta-epica`. Candidate loses witness labels, leaves reference numbers in prose, and encodes prose as verse-like lines. | Reconcile identity and restore witness/prose structure before use. |
| Alexius Studites, *Decreta* additamentum | Imported after comparison of all 15 pages with Ficker 1911. The scan is public domain; the transcription is CC BY-SA 4.0. | One letter correction, two word joins across page boundaries, and folio-marker extraction are reversible in `data/corpus_changes/alexius-ficker-1911/`. |
| P.Herc. 1026 / DCLP 63141 | Original EpiDoc has explicit CC BY 3.0 and materially richer structure. An unserved 89-line pilot is prepared. | `data/pilots/dclp63141/` retains the unchanged source XML, all reading branches, and damage/restoration metadata. |

The three Source Library examples do not justify blanket ingestion. The pilot
is deliberately a spot check, not a claim that every token was proofread. The Alexius import
follows the completed 15-page review recorded on 2026-10-12, not the original
three-page spot check.
No TLG comparison text was used in validation.

For DCLP 63141, the original edition contains 89 line-break elements, 219 unclear
spans, 140 gaps, 86 supplied spans, and correction/variant markup. The derivative
reading file reduces this to two column paragraphs. A plain `itertext()` importer
would silently concatenate alternative readings and lose damage semantics; use
an EpiDoc-aware export with retained source XML. The sampled XML is pinned to
the upstream commit recorded in `pilot-review.json` and its exact file checksum.

## Sources

- [Greek Library downloads](https://thegreeklibrary.pages.lisn.upsaclay.fr/data/)
- [Provenance and rights](https://thegreeklibrary.pages.lisn.upsaclay.fr/sources-and-rights/)
- [Source Library Achmet volume](https://sourcelibrary.org/book/69bd9da16120d54bd03787c3)
- [Ficker scan](https://archive.org/details/erlasse-des-patriarchen-von-konstantinop)
- [Original DCLP repository](https://github.com/papyri/idp.data)
