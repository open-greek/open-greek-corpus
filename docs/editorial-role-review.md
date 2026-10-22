# Herodas and Hipponax editorial roles

The source review separates dialogue and printed fragments from edition titles,
speaker labels, apparatus, external testimony, and commentary. It changes no
Greek spelling and supplies no missing text. Every original row is preserved in
the reversible archive under `data/corpus_changes/editorial-role-review/`.

These are the historical role partition's counts and source decisions. The
later [Herodas body recovery](herodas-body-recovery.md) preserves its 62 primary
passages and adds 22 missing source pages, producing 84 primary passages across
35 inventoried body pages. The editorial sidecars and existing aliases remain
unchanged. That separate recovery retains its recognition witnesses, source
readings, and correction audit; it does not retroactively turn this role review
into an OCR spelling review or change the accounting below.

## Sources and scope

Herodas uses Walter Headlam's notes, edited by A. D. Knox, *The Mimes and
fragments* (Cambridge, 1922), in the
[Internet Archive UCLA scan](https://archive.org/details/mimesfragments00hero).
The retained `source-herodas.pdf` has 542 PDF pages, 35,869,325 bytes, and SHA256
`6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a`.
The former catalog link, `herodasmimesfrag00hero`, identifies a different Columbia
microfilm copy of the same edition. Its spread images do not establish the
physical page references used by the existing OCR run.

All 136 existing Herodas rows were checked against PDF pages 72, 73, 74, 132,
133, 180, 182, 236, 238, 239, 290, 292, 294, 295, 344, 345, 346, 472, 474, 476,
and 477. In this portion of the scan, the printed page is the PDF page minus 70:
PDF page 72 is printed page 2, page 182 is printed page 112, and page 477 is
printed page 407. These are selected existing excerpts, not a complete Herodas
text. The review does not ingest additional pages from the 542-page volume.

Hipponax uses Paul Brandt's *Corpusculum Poesis Epicae Graecae Ludibundae*,
volume 1 (Leipzig, 1888), as encoded in
[First1KGreek at revision `4c9c843d80ee94b4371f52add5f7d68bbfe7ba4c`](https://github.com/OpenGreekAndLatin/First1KGreek/blob/4c9c843d80ee94b4371f52add5f7d68bbfe7ba4c/data/tlg0233/tlg001/tlg0233.tlg001.1st1K-grc1.xml).
The retained `source-hipponax.xml` has SHA256
`82415a5b06330fc223aa5d15080b078637ff6eb354efeef2ec7b85019be090b7`.
The digital source is licensed CC BY-SA 4.0. Its title is *Fragmentum (128)*;
keeping this fragment does not claim coverage of every surviving Hipponax
fragment.

## Role decisions

The Herodas packet assigns all original characters, including whitespace, to
147 nonoverlapping spans: 63 authorial spans, 45 speaker labels, seven titles,
two running headers, 24 apparatus spans, five commentary spans, and one
editorial source note. Nine rows contain more than one role. Sixty-two rows
contain authorial text, while 74 rows consist entirely of editorial material.

Two long rows require internal apparatus boundaries. In `herodas_hk_0180.3`,
the verse ends before `6 χαλκίνδα P.` In `herodas_hk_0182.1`, the printed
`ΛΑΜΠΡΙΣΚΟΣ` speaker label separates two dialogue spans; apparatus begins at
`33 πθι P.` Seven rows on PDF page 346 begin with speaker names that are
excluded without removing their following dialogue. Eligible spans on either
side of an excluded label are separated by a space; positional frequency
evidence retains the boundary between those spans.

On PDF page 472, rows `.4` and `.5` are the separately printed IX a and IX b
fragments and remain primary. Row `.6` is the small-type Zenobius source note
and attribution discussion. The edition's arrangement is preserved without
settling the disputed attribution. The commentary on pages 476–477 includes
explicitly identified quotations from Herodotus, Theognis, Bacchylides,
Diphilus, Moschion, Philo, and other authors. Those passages remain within
their original scholarly context; the review does not claim a separate
attribution analysis of every quotation.

Hipponax retains the unchanged `frag128` section. The TEI explicitly labels the
other four sections `HOMERI LOCI SIMILES`, `TESTIMONIVM`, `VARIETAS LECTIONIS`,
and `COMMENTARIVS`. The Homeric parallels, Athenaeus's report quoting Polemon,
attributed textual variants, and Brandt's commentary are retained outside
Hipponax's primary lexical totals. These decisions apply to this pinned
edition, not to every corpus section named `commentary` or `testimonium`.

## Accounting

| Work | Original rows | Primary rows | Retained editorial spans | Original analysis tokens | Primary analysis tokens | Excluded analysis tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Herodas | 136 | 62 | 84 | 2,846 | 2,036 | 810 |
| Hipponax | 5 | 1 | 4 | 154 | 25 | 129 |

Herodas has 2,850 original Greek-block surface runs, of which 814 occur in
retained material. Those figures differ from the analysis counts because the
Greek-block-only regex splits four extra runs at decomposed combining marks
in the title `herodas_hk_0236.1` and apparatus row `herodas_hk_0239.5`. The
analysis regex includes combining marks and counts 2,846 original tokens and
810 excluded tokens. Both methods count 2,036 surviving primary tokens.
These are token-accounting differences, not additional readings or OCR fixes.

Bracketed body supplies and existing critical readings remain unchanged. This
role review does not certify complete critical markup, correct OCR spelling,
resolve restorations, or establish new speaker attributions. The edition
itself notes disputed distributions of the dialogue in Mime IV.

## Replay, citations, and undo

`scripts/herodas_source_observations.py` generates the complete source-role
packet from the exact baseline rows.
`scripts/repair_editorial_roles.py` compiles that packet and the pinned
Hipponax section decisions, records the literal original and resulting rows,
and checks both sources and all output checksums. It refuses unreviewed source
changes, missing original identities, overlapping spans, and changed readings.

Editorial text remains in `data/paratext/herodas-headlam-knox.jsonl` and
`data/paratext/hipponax-brandt1888.jsonl`. Whole editorial rows retain their
original loci. Excluded spans from mixed Herodas rows carry derived
`.editorial.N` loci, their original locus, and exact original character ranges.
Passage aliases preserve all 141 original row identities. Retained material
does not enter primary coverage, lemma, or frequency exports.

On the current checkout, validate the archived role review through the checked
Herodas predecessor with:

```sh
python3 scripts/herodas_current_state.py --check
```

The wrapper verifies the later body recovery and exposes this review's exact
62-passage Herodas postimage for the frozen validator. The original
`repair_editorial_roles.py --check` command remains appropriate in the
historical state before body recovery. The frozen recipes and audit bytes are
unchanged.

If the later body recovery is active, unapply it first:

```sh
python3 scripts/repair_herodas_body.py --undo
```

Then restore this role review's exact original primary files and passage
aliases with:

```sh
python3 scripts/repair_editorial_roles.py --undo
```

Undo uses the archived literal preimages and remains available if a comparison
source is removed or invalidated. Derived reports must then be rebuilt through
the normal corpus pipeline.
