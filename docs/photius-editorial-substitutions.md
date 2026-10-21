# Photius editorial substitutions

This layer adopts the Greek reading supplied by the TLG version of René Henry's
*Photius. Bibliothèque*, volumes 1–8 (1959–1977), where the Bekker-based corpus
still has an uncertain reading. It is an editorial preference between editions,
not a new claim about what the Bekker scan prints. TLG is the comparison text
provider; modern commentary and apparatus are not imported.

The preparation accounts for every one of the 2,977 remaining segment identities.
It selects 2,602 substitutions and holds 375: 330 unmapped spans, six tied
occurrences, and 39 spans outside the authorial body. The served unresolved count
therefore becomes 375. The separate scan measurement remains 2,977; the 92
earlier scan-supported resolutions remain distinct from editorial choices.

## Locating readings

The first search uses three verified words on each side, falling back to two
when the immediate context is shorter. All equally supported locations remain
alternatives. The uncertain word itself never selects a location.

Where another uncertainty interrupts the immediate flanks, the complete ordered
passage is aligned against the same Bekker page and its two neighbors. Uncertain
words have neutral spelling costs. A fallback requires at least five exact
verified anchors, at least 70% of the available reliable words, bounded alignment
cost, and the same unique contiguous counterpart on every optimal path. Missing
readings and empty gaps do not authorize deletion.

Verified prefixes and suffixes are trimmed from whole-word counterparts before
replacing a partial-word uncertainty. Existing outer punctuation is preserved;
elision marks follow the adopted Greek form, and numeral marks occur only once.
Unmapped internal punctuation remains held. Nonbody and fragment exclusions,
independent source disagreements, and all earlier source variants survive.

## Reproduction and reversal

`scripts/prepare_photius_editorial_substitutions.py` creates the occurrence
decisions from the supplied HTML. The raw file remains outside the repository;
its checksum, bibliographic identity, chosen Greek tokens, and exact decoded
HTML-node references are recorded in structured JSON under
`data/corpus_changes/photius-bekker-editorial-substitutions/`.

For the first generation, supply the source file and a UTC timestamp:

```sh
python3 scripts/prepare_photius_editorial_substitutions.py \
  --source-html "$PHOTIUS_COMPARISON_HTML" --reviewed-at UTC_TIMESTAMP
python3 scripts/repair_photius_editorial_substitutions.py \
  --apply --source-html "$PHOTIUS_COMPARISON_HTML"
```

The admission freshly repeats preparation and validates every source token and
reference before changing the corpus. All original and corrected rows, removed
uncertainty causes, remaining independent exclusions, timestamps, and recipe
pins are archived. Compact row references point to the complete exclusion
records; they do not duplicate those records throughout the served corpus.

```sh
make check-photius-editorial-substitutions
PHOTIUS_COMPARISON_HTML="$PHOTIUS_COMPARISON_HTML" make check-photius-editorial-source
python3 scripts/repair_photius_editorial_substitutions.py --undo
```

The first check validates the public recorded witnesses and exact replay. The
second freshly verifies the full supplied source and contextual selection.
Literal undo requires no live correction source. Reverse this layer before the
70-span admission, the prior 33-span review, the occurrence-context layer, and
the complete source campaign. Passage aliases and other works are unchanged.
