# OGA and GLAUx date comparison

This directory retains Mark G. Bilby's three original CSV files from
*OGA v0.2.0 (2024-11-24) and GLAUx v1.0 (2024-04-09) Compared*, version 0.1,
published December 1, 2024, [version DOI 10.5281/zenodo.14254073](https://doi.org/10.5281/zenodo.14254073).
The files are © 2024 Mark G. Bilby, distributed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
The source citation, creator ORCID, original MD5 checksums, SHA-256 checksums,
byte lengths, and download URLs are in `manifest.json`.

The comparison also retains `glaux-metadata.txt` from the same pinned GLAUx
commit used by the annotation exporter. It contains bibliographic metadata;
no GLAUx text or annotations are imported here. The original metadata bytes
and checksum remain intact. OGA dates come from `data/oga_dating.json`,
whose source is the pinned OGA v0.2.0 chronology. Its existing estimated
dates, formatted dates, temporary flags, date labels, bibliography, and
source links remain verbatim in the derived comparison's `raw` readings.
Source wording is preserved even where it uses different era abbreviations.

Run `python3 scripts/compare_oga_glaux_dates.py --fetch` from the repository
root to retrieve and verify the original CSV and GLAUx metadata files and
regenerate `data/oga_glaux_date_comparison.json`. Subsequent builds need no
network access. Without `--fetch`, the script verifies the retained source
bytes and regenerates the comparison; `--check` detects output drift.

The output is keyed by the exact source CTS work identifier. Every CSV row
has its filename and row number, and repeated CTS keys remain separate
readings. The two GLAUx Aesop collections `tlg0096.tlg002a` and
`tlg0096.tlg002b` never become OGA's `tlg0096.tlg002`. Exact catalog matches
are exposed as candidates; a shared title does not authorize an identity
merge.

Each reading includes the original fields and normalized date intervals.
Endpoints record year, month, day, precision, and BCE/CE labels. OGA and
Bilby's ISO-style fields are interpreted using astronomical numbering:
year `+0000` is 1 BCE and year `-0001` is 2 BCE. GLAUx's signed integers
do not declare their year-zero convention in this metadata file, so both
astronomical and historical interpretations are retained for negative years.
Historical numbering skips year zero; a historical year of `-1` therefore
normalizes to astronomical year zero. These are explicit interpretations,
not corrections to either source's chronology.

Distinct intervals stay separate. Unsupported or ambiguous dates remain
unresolved with their original value and reason; they are never replaced
by a midpoint or a guessed century. The `available_intervals` collection
lists all candidates with references to the readings and interpretations
that produced them. `bilby_source_comparisons` distinguishes equality,
different intervals, and matches that depend on a year-numbering convention.
These relations are observations about metadata, not claims of a defect.

Bilby's files are derived from OGA and GLAUx, not an independent third
dating witness. In particular, the matched CSV exposes one date field,
not two separately attributed source dates. The output records that
dependency and does not vote, choose a preferred date, overwrite registry
tags, or silently collapse disagreements.
