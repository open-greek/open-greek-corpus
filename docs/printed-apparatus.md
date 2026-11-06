# Printed apparatus readings

Athenaeus, *De Machinis*, locus `athenaeus_mech_wescher_0088.4`, retains two
typographic readings from Wescher's 1867 printed page 34. The
[standalone apparatus reader](../data/critical_editions/athenaeus-wescher-apparatus/reader.html)
places the elevated theta above its printed rho anchor and keeps P's iota on
the baseline.

The dimension `Γ̅` retains the horizontal bar printed above Gamma in both
independently retained copies of this page. It is a numeral with value 3,
not an expanded Greek word.

The passage uses `critical_markup.schema = "printed-apparatus-v1"`.
`critical_markup.readings` records each manuscript siglum, diplomatic display,
Unicode code point offsets, source image checksum, and bounded printed region.
For the V reading, `baseline_text` preserves `ἀρεμβολεῖται`; `raised_letter`
records theta above rho at base code point index 1. `linearized_boundary: null`
explicitly declines to select an ordinary-letter insertion order. The plain
`text` field uses modifier theta in `ἀρᶿεμβολεῖται` as a display convention;
readers must retain the structured position rather than normalize that string.

P's reading is `ὧι`: omega with rough breathing and circumflex followed by
adscript iota. It remains distinct from the apparatus lemma `ᾧ`, whose iota
is subscript. No nu is printed in P's reading.

Both entries retain `normalized_reading: null`, `preferred: false`, and
`lexical_eligible: false`. Their complete forms remain visible in `reading_text`
and `tokens`; the explicit `analysis_text` excludes them. `analysis_segments`
breaks the surrounding lexical text at each excluded form, and
`contextual_eligible: false` prevents positional measurements from treating
the row as an ordinary continuous reading. These fields retain source
uncertainty without selecting a canonical variant.

The optional `critical_markup.numerals` array records the separately verified
numeric annotation. Its entry uses `kind: "greek-numeral"`, `base_letter: "Γ"`,
`value: 3`, and the literal display `Γ̅` with U+0305 COMBINING OVERLINE. The
`overbar` object records that mark's position above the letter. It retains
`normalized_reading: null`, `expanded_word: null`, and
`lexical_eligible: false`, with code point offsets and bounded source regions
from both printed copies. This is separate from the two uncertain entries in
`readings`; their identities, typography, and qualifications remain unchanged.
The numeral's token has status `numeral` and `numeral_ids`, remains visible in
`reading_text`, and is excluded from `analysis_text`. Its exclusion adds another
break in `analysis_segments`, so the row has 38 eligible Greek tokens and four
contiguous runs. Historical rows without the optional numeral annotation keep
the same schema and byte-for-byte projection behavior.

`scripts/athenaeus_apparatus_markup.py` validates the public representation
without processing inputs or external packages. The source links and manuscript
roles remain available in the reader's expandable metadata.
