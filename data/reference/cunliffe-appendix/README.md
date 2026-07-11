# Cunliffe's Homeric grammatical appendix

Reference material, not a served text work. This directory holds a structured,
machine-readable copy of the conditional / relative-sentence construction table
printed at the end of Richard John Cunliffe's *A Lexicon of the Homeric Dialect*
(1924). Cunliffe's lexicon entries repeatedly defer to this table (for example,
"For the examples and constructions see Table at end III.B.a 1 2") instead of
listing citations inline, but no digital edition of Cunliffe reproduces the table
body. This is, as far as we can tell, the first usable machine-readable copy of it.

## Status: reference, not a served work

This is reference / bonus material alongside the corpus, not part of the served
running-text corpus. It is a lexicon-grammatical reference table, not a text
edition, so:

- It does not enter the source-precedence ladder.
- It is not assigned a served work-id, and is not listed in `corpus_editions.json`
  or the work-id registry.
- It lives under `data/reference/`, entirely separate from `data/corpus/`.

## Provenance

- Work: Richard John Cunliffe, *A Lexicon of the Homeric Dialect*, 1924. Public domain.
- Scan: archive.org item `mdp.39015005687283` (University of Michigan copy).
  See https://archive.org/details/mdp.39015005687283
- Appendix location: printed pages 431-452 = scan leaves 447-468 (22 pages).
- Page images: full-resolution via the archive.org IIIF endpoint,
  `https://iiif.archive.org/iiif/mdp.39015005687283$<LEAF>/full/full/0/default.jpg`
- OCR: Qwen3.6-27B, 8-bit MLX (Apple Silicon), the same OCR track this corpus uses
  for its own OCR of public-domain editions. The polytonic accents, breathings, and
  every citation code came through cleanly; the pre-existing Google OCR of this scan
  renders the Greek unusably.

## License

The underlying text is public domain (1924). The derived, structured, OCR'd dataset
is the corpus maintainers' to license and is released under CC BY-SA 4.0, matching
the corpus.

## How to read the table (code legend)

A construction code such as `III.B.a.1` decomposes by level:

| level | meaning |
|---|---|
| Roman `I` / `II` / `III` | logical type of the εἰ-clause. I = citing a fact in corroboration; II = introducing one of two opposed clauses ("even if"); III = the protasis of a conditional sentence |
| capital `A`-`D` | kind of supposition. A = Simple, B = General, C = Contrary to Fact, D = Future |
| lowercase `a` / `b` | time reference. a = Present, b = Past |
| number | the specific verb construction (mood/tense combination) in that cell |

`(D)` (Future Suppositions) is by far the largest section and is a long numbered
enumeration, which is why entries cite things like `(D) (56)`. Many cells also
contain "Relative Sentences" / "Conditional Relative Sentences" sub-blocks whose
examples are introduced by a relative word (ὅς, ὅτε, ὅπως, ὄφρα, ὅστις, ὁπότε, ...)
rather than by εἰ.

## Citation scheme

Citations use Greek-letter book codes:

- CAPITAL Α-Ω = Iliad books 1-24.
- lowercase α-ω = Odyssey books 1-24.
- Followed by a line number, so `Α 39` = Iliad 1.39.
- A leading `*` marks a double protasis.
- A bare number continues the previous book (`Ν 111, 316` = 13.111 and 13.316).

Every citation is resolved to `{corpus: il|od, book, line}` in the dataset.

## Totals and QA

- 153 construction cells, 292 examples, 1,209 resolved citations, 0 unparsed citation strings.
- Iliad citations were cross-validated against an independent Homeric dependency
  treebank (does the cited introducing word occur at the line the table cites?).
  Roughly 95% were independently confirmed; per-word rates: εἰ 84/85, ὄφρα 10/10,
  ἐπήν 6/6, ὅς 42/43, ἐπεί 23/24, ὅτε 34/41, with εὖτε, ὅθι, ὅστις, ὁπότε all 100%.
- The original review queue and full per-word counts are in `validation_report.txt`.

## Review-queue resolution (independent re-check against our served Iliad)

The handoff flagged a short review queue of Iliad citations the treebank could not
confirm (likely OCR line-number misreads). Each was re-verified independently by
reading the cited line and its neighbors in our own served Iliad
(`data/corpus/homerus-epic.ilias.jsonl`, Perseus grc2 edition), a second source
distinct from the treebank used in the original QA.

Outcome: all 10 reviewed citations are confirmed. Zero line-number corrections were
needed, and none remain flagged. The treebank had failed to confirm them for reasons
that are not OCR errors:

- ὅτε at 4.53, 6.524, 7.335, 9.101, 10.14, 12.286: the word is present at the cited
  line in elided form (ὅτʼ, and ὅθʼ before a rough breathing at 6.524), which the
  whole-token treebank check skipped.
- εἰ 21.556 and ἐπεί 17.658: the word and essentially the whole protasis are present
  at the cited line; the treebank tagged the clause differently.
- ὡς 9.26: ὡς is present ("ὡς ἂν ἐγὼ εἴπω"); the treebank read it as a comparative
  adverb rather than a conditional word.
- ὅς 9.140: a Cf. pointer grouped under the relative-pronoun lemma ὅς. Line 9.140 is
  a valid conditional-relative line ("αἴ κε ... ἔωσιν"); the relative pronoun itself
  sits at 9.143. The parallel Cf. citation ὅς 9.282 lands on the exactly parallel
  αἵ-κε line, so both point deliberately at the αἴ/αἵ-κε line rather than being a
  random digit misread. The line number is correct; only the ὅς word-label is a
  grouping artifact.

The one known false alarm, ὅτε 2.395, was not re-checked (a treebank scope-gate
artifact, not an OCR error, per the handoff).

The full audit for these items, including the exact served-Iliad line text used as
evidence for each, is in `manifest.json` under `review_queue_resolution`.

Known minor OCR slips (left as-is, known-minor; the Greek is otherwise faithful):
occasional accent errors such as `αἰ` for `αἴ` (visible in the leaf 447 title line,
"εἰ (αἰ)") and `μάλ'α` for `μάλα`.

## Files

- `cunliffe_appendix.json` - primary structured dataset (153 cells; see `manifest.json`
  for the field layout).
- `cunliffe_appendix_refs.json` - per-introducing-word citation index; answers what a
  cross-reference such as "see Table at end III.B.a" actually cites.
- `structured_pages.json` - intermediate per-page cells (provenance; the two files above
  are authoritative).
- `validation_report.txt` - QA summary and the original review queue.
- `leaves/leaf_447.md` ... `leaf_468.md` - raw per-page OCR (Markdown), the primary
  transcription the structured JSON is derived from.
- `manifest.json` - machine-readable manifest: provenance, license, code legend,
  citation scheme, totals, QA, the review-queue audit, and a checksummed file list.
