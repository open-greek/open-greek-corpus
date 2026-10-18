# Calfa PG 73 source witness

`PG073_text.txt.gz` contains the exact UTF-8 bytes published by Calfa in
`calfa-co/Patrologia-Graeca`, commit
`5895ab908dd4cac5ee06cfc0e36f2ef77723e143`.

- Source: https://github.com/calfa-co/Patrologia-Graeca/blob/5895ab908dd4cac5ee06cfc0e36f2ef77723e143/PG073/PG073_text.txt
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Attribution: Calfa, Patrologia Graeca OCR, PG073.
- Uncompressed SHA-256: `353b31b6ca09f0e1639267da976e13171b8426352ea2d8ba648a1d1c43758104`.

The 528 marker blocks complement the PG 74 continuation of Cyril's commentary
on John. `scripts/repair_john_coverage.py` verifies the source hash, retains
marker locations, and joins lines with one space after NFC normalization. It
makes no spelling corrections. The reversible admission and scan-boundary
evidence are in `data/corpus_changes/cyril-john-coverage/`.
