# Photius editorial continuation

This authority starts from `corpus-2026-10-21.6` and accounts for all 385
occurrence identities held by the first editorial substitution. It preserves
that release's original text, variants, source judgments, corpus row order,
citation aliases, and correction archives. The current admitted and held counts
are generated in `data/corpus_changes/photius-bekker-editorial-continuation/changes.json`
and exposed in the existing quality and known-limitations reports.

## Source selection and rendering

The first review already located 192 of the held readings. Most were blocked by
internal punctuation, line-division hyphens, or literal variant-display brackets.
The continuation renders complete attributed Greek source spans. Every Greek
token and intervening punctuation piece has an exact decoded-node reference.
The new parser preserves the original Greek unit identities while also retaining
standalone punctuation nodes. Line-number table headings and edition labels do
not become body text. Original variants and retired display conventions remain
in the structured records.
Distinct Greek tokens separated by HTML cells retain their word boundary even
when the decoded cells omit layout whitespace; sentence-ending punctuation at
such a boundary receives a following space. This normalization is reproduced
from the recorded source-token references.

For absent or tied locations, elastic ordered alignment uses only eligible
surrounding words. Both the spelling and token count of excluded intervals have
zero locating cost. A selected gap needs uniquely fixed immediate boundary
anchors across all optimal paths, at least five exact verified anchors, at least
70% anchor coverage, a bounded cost, and no reused source tokens. Optional
three-passage windows are supplied in frozen source order; source mapping
exceptions, missing boundaries, cross-codex ambiguity, empty gaps, and conflicting
locations remain held.

Individually reviewed locations can resolve cases with insufficient automatic
anchors. Each such decision pins the exact original row and uncertainty record,
the decoded source context, the chosen token interval, and the reason that the
context identifies this occurrence. Public replay reconstructs every field from
the authored decision and its hashed source context. A longer tied interval
cannot silently repeat already retained neighboring text. Different word orders
between editions require a separate passage-level decision.

## Source roles and fresh corrections

Individual scan and comparison-edition reviews distinguish reading announcements,
transmitted explanatory commentary, and marginal edition references. Transmitted
commentary is not thereby attributed personally to Photius or independently dated.
Only the exactly reviewed role intervals lose their corresponding old exclusion;
other causes and uncovered portions survive. A specifically inspected paragraph
boundary can separate an OCR word that was fused to the next quotation.

Clear errors discovered in previously verified text have separate source
correction records. Their old verified observations remain frozen; their current
original and corrected text, scan crops, comparison witnesses, and exact offsets
are retained. These corrections do not reduce the 385-identity uncertainty count.
Printed fragments keep their independent exclusions without a jointly verified
word-boundary decision. An edition omission does not silently delete Greek text.

## Reproduction and reversal

```sh
python3 scripts/prepare_photius_editorial_continuation.py \
  --source-html "$PHOTIUS_COMPARISON_HTML" --reviewed-at UTC_TIMESTAMP
python3 scripts/repair_photius_editorial_continuation.py \
  --apply --source-html "$PHOTIUS_COMPARISON_HTML"
make check-photius-editorial-continuation
PHOTIUS_COMPARISON_HTML="$PHOTIUS_COMPARISON_HTML" \
  make check-photius-editorial-continuation-source
python3 scripts/repair_photius_editorial_continuation.py --undo
```

Fresh application repeats preparation, validates source identities and exact
witnesses, and recreates the inspected role crops. Public literal checking needs
only the recorded witnesses and immutable archives. Undo needs no live correction
source and restores the exact original bytes. Reverse this layer before the
first editorial substitution, the 70-span source admission, the 33-span review,
the occurrence-context layer, and the complete historical campaign.
