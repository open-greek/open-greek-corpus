# Photius final occurrence review

This authority reviews the 27 identities held by
`corpus-2026-10-21.7`. Each occurrence has an exact released preimage,
an attributed source disposition, and a separately checked lexical role.
The generated counts are in
`data/corpus_changes/photius-bekker-final-review/changes.json` and the existing
quality reports. Original scan observations and all earlier editorial choices
remain immutable.

The completed review has 25 decisions covering all 27 identities and leaves
zero served held identities. It changes 35 displayed rows and annotates 37,
retaining all 3,782 rows. By source role, the dispositions cover 17 historical
body readings, four printed bracketed readings, three marginal references,
one line number, one nonlexical mark, and one OCR insertion. Seventeen new
editorial choices include the explicitly reviewed omission; three additional
decisions are backed by scan readings. These counts do not replace the frozen
historical scan measurements.

## Complete words and retained citations

Joint decisions reconstruct complete words once across retained passage
boundaries. One passage owns the complete displayed word; exact edits remove
the corresponding continuation fragments from their old passages. Every row,
locus, and citation alias remains present. A marginal line number recognized
within one joint group receives its own nonlexical identity role.

Each complete source word has exact decoded HTML references and complete-edition
token indices. Chosen tokens cannot be reused from the two earlier editorial
layers or another decision in this review. An authored placement records which
replacement owns the source word. Contrary scan and digital readings remain in
the structured decision.

Only exclusion causes wholly covered by a separately reviewed replacement are
retired. Unrelated causes survive. A preserved independent exclusion can keep
a corrected word out of counts; the admission measurement tests the effective
projection rather than trusting a requested eligibility flag. A nonlexical role
can cover a complete reviewed bracketed insertion even when its character
correction is narrower.

## References, bracketed readings, and omissions

Marginal references and a nonlexical high mark are classified separately from
historical Greek words. A standalone OCR name is reviewed against the positive
column-boundary anchors on either side, preserving its original row and audit
when its unsupported insertion is removed.

Readable printed bracketed material remains visible and excluded from lexical
counts. Printed brackets and a comparison edition's omission do not independently
establish who supplied the material or when. At one separately reviewed uncertain
bracketed occurrence, an explicit Henry omission is bounded by consecutive source
tokens. Adopting that edition's empty interval does not certify the uncertain
Bekker glyphs: all original spellings and proposed readings survive as contrary
source evidence. A transmitted variant supported by Bekker's body and apparatus
is retained even though Henry omits it.

The quality reports separate historical scan uncertainties, attributed editorial
choices, Greek reading dispositions, nonlexical classifications, and effective
lexical admissions. Completing an occurrence disposition does not make the
historical scan-resolution measurement larger.

## Reproduction and reversal

```sh
python3 scripts/repair_photius_final_review.py --apply \
  --source-html "$PHOTIUS_COMPARISON_HTML" \
  --reviewed-at '2026-10-22T00:59:50.180849Z'
make check-photius-final-review
PHOTIUS_COMPARISON_HTML="$PHOTIUS_COMPARISON_HTML" \
  make check-photius-final-review-source
python3 scripts/repair_photius_final_review.py --undo
```

The frozen decision packet includes its UTC review timestamp. Reproduction from
the exact predecessor uses that timestamp. A later application can reuse
the timestamp in the immutable generated source review. Fresh validation repeats
the source selections and renders the pinned scan crops. Public literal checking
uses recorded witnesses, exact authored decisions, recipe pins, and the frozen
complete decision fingerprint. It does not require the unbundled comparison
HTML.

Undo requires no live source file and restores the exact preceding corpus bytes.
Reverse this authority before the editorial continuation and then all older
layers. Historical validators receive checked predecessor views; they continue
to validate their original published recipes and archives.
