# Herodas reading review

This layer proofreads the 62 older passages in `herodas.mimiambi` and reviews
the recovered pages' 43 archived source-uncertainty spans. Those spans occupied
45 lexical slots in the preceding body release; a source span and a token slot
are different counting units. Current remaining uncertainties and lexical
counts come from the generated reading audit rather than replacing those
historical measurements.

The completed review changes 49 passages through 202 reversible character
edits. Of the 43 archived uncertainty spans, 32 have source-clear readings and
11 retain printed damage or critical exclusions. No source-glyph uncertainty
remains. The analysis projection contains 4,916 eligible words and excludes
193 marked word slots. The recovered pages increase from 2,918 to 2,950 eligible
words; the older excerpt decreases from 2,036 to 1,966 after the same critical
exclusion rules are applied throughout. The lower combined total measures
lexical eligibility, not missing source pages.

All 84 passage identities across the 35 inventoried body pages are preserved.
Work, edition, citation aliases, speaker-separated passage boundaries, and
editorial sidecars remain as established by the
[source-role review](editorial-role-review.md) and
[body recovery](herodas-body-recovery.md). Attribution holds remain in force.
The review concerns the admitted Headlam–Knox printing, not every surviving
fragment attributed to Herodas.

## Printed readings and evidence

The source is Headlam–Knox, *The Mimes and fragments* (Cambridge, 1922), in the
[Internet Archive scan](https://archive.org/details/mimesfragments00hero).
The pinned PDF remains in
`data/corpus_changes/editorial-role-review/source-herodas.pdf`.
Original color captures and scan metadata are retained under
`data/corpus_changes/herodas-reading-sources/`; its manifest identifies each
physical page, printed page, capture member, rotation, crop, byte count, and
SHA-256. The archive and scan metadata also have content pins. These captures
underlie the same PDF and contribute no independent edition or recognition
vote.

`scripts/herodas_excerpt_readings_a.py` and
`scripts/herodas_excerpt_readings_b.py` account for every older passage,
including passages whose literal text is unchanged. Observations retain the
released original text, corrected source reading, source pins, page evidence,
and review time. `scripts/herodas_uncertainty_readings.py` addresses the
recovered pages' archived uncertain occurrences by their original character
ranges and records the resulting source decisions.

The governing evidence is the printed glyph. A familiar spelling, expected
grammar, another edition, or agreement between recognizers does not authorize
normalizing the text. Ionic forms, crasis, accents, and breathing marks remain
as printed. Where the scan cannot settle a glyph, the observation retains
alternatives at exact offsets in the corrected text. Printed supplies, obeli,
partial words, and dotted losses remain literal and outside scalar lexical
counts. Critical bracket state follows the source across passages and pages;
a passage boundary does not silently end a restoration.

## Reproduction and validation

The source helper reconstructs the retained image bundle from the pinned
[original capture archive](https://archive.org/download/mimesfragments00hero/mimesfragments00hero_orig_jp2.tar)
and scan metadata. It verifies the complete archive before selecting the body
images; the large download may remain in an ignored local cache.

```sh
python3 scripts/fetch_herodas_reading_sources.py \
  --archive ORIGINAL_CAPTURE_ARCHIVE.tar --scandata SCANDATA.xml
python3 scripts/fetch_herodas_reading_sources.py --check
python3 scripts/repair_herodas_readings.py --apply
make check-herodas-readings check-herodas-body check-editorial-roles
```

Initial application requires the exact published body predecessor. Later
`--apply` replays the retained authority. `--check` on the reading repair, or
`make check-herodas-readings`, checks the current layer without new OCR.
`make check-herodas-body` uses
`scripts/herodas_current_state.py --check-body` to validate the frozen body
release through its exact predecessor view. The role, Phoenix, and Photius
validators compose with that checked view.

`data/corpus_changes/herodas-reading-review/` retains the literal preimage,
generated observations, reversible character edits, complete lexical networks,
and a manifest pinning sources, recipes, outputs, and counts. Earlier body
votes, source decisions, and publication bytes remain recoverable from their
existing audits. Source, recipe, or primary changes invalidate an active proof,
including during nested citation views and cached frequency projections.

The current quality metadata keeps the historical role partition under
`source_role_review`, the preceding body scope under `body_recovery`, and the
new reading scope at the current coverage level. The quality report exposes
the later body and reading reviews separately. These counts describe source
review and lexical eligibility; they are not character-error-rate estimates.

## Undo and reapply

Remove layers in chronological reverse order:

```sh
python3 scripts/repair_herodas_readings.py --undo
python3 scripts/repair_herodas_body.py --undo
python3 scripts/repair_editorial_roles.py --undo
```

Each undo checks its literal archive and refuses a modified postimage. Undo
does not require the correction source to remain present or valid. The
compatibility views recognize these literal earlier epochs without treating
them as an active, source-certified reading review.

Reapply the source-role repair, body recovery, and reading repair in that order,
using their retained inputs and authorities. Rebuild registry, coverage,
quality reports, and lexical exports through the
[normal corpus pipeline](../README.md#build) before publishing. The issue
policy closes a repaired published defect only after a tagged release contains
the tested result.
