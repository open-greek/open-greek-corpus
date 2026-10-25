# Dübner's Aristophanes scholia

The Acharnians and Platonius files formerly served two OCR extractions of
Dübner's entire 1855 *Scholia graeca in Aristophanem* under individual work
identities. `scripts/repair_dubner_scholias.py` separates their historical texts,
editorial matter, and comparative witnesses using reviewed source boundaries.
The source review does not certify the surviving OCR spellings.

## Source evidence and scope

The [Toronto scan](https://archive.org/details/scholiagraecaina00dbuoft) and
[Harvard scan](https://archive.org/details/scholiagraecain01dbgoog) reproduce the
same printed edition. Their exact PDF hashes, reviewed page images, and boundary
inventory are retained under `data/corpus_changes/dubner-1855-scope/`.
`scripts/capture_dubner_sources.py` reproduces the images from the pinned PDFs;
its offline check requires neither a network connection nor a PDF renderer.
To recapture the evidence, install `PyMuPDF==1.28.2` and run
`python3 scripts/capture_dubner_sources.py --cache CACHE_DIRECTORY`. The command
downloads either missing PDF into that external cache and verifies every PDF
and image checksum before publishing the retained evidence.

The eleven play sections are separate source-scoped expressions. Acharnians
retains its existing identity. The other plays have descriptive Dübner edition
identities, without invented TLG recension identifiers. Andronicus's poet-order
piece and two Triclinius units have separate identities. The Andronicus heading
and Dübner's conflicting Tzetzes attribution are both preserved in the source
qualification. Missing OCR passages are not reconstructed from another play.

The front matter is partitioned at the original row or character boundary.
Historical prolegomena already represented in the Kaibel or Westermann
compilations remain attributed comparative witnesses, outside additional scalar
counts. The Suda excerpt and Anthologia epigrams retain explicit canonical
work and passage links. They are stored as comparative secondary readings in
`data/ocr_witnesses/dubner-1855-comparative-prolegomena.jsonl` rather than counted
again. Ambiguous historical diagrams remain historical evidence in
`data/ocr_witnesses/dubner-1855-unassigned.jsonl`. They are not described as
modern editorial prose. Editorial notes, headings, critical annotation, and
indexes are preserved separately in `data/paratext/`.

## Readings and counts

Every literal original row survives, including the displaced duplicate-page
readings and the earlier merged Harvard track. The Harvard page concordance
accounts for repeated and missing leaves. Constructed lanes retain the earlier
merge's rejected fallback readings at their exact audited offsets. These lanes
are labeled derived and share the original Harvard vote group; they cannot add
independent votes.

Primary page records use the existing word-alignment and consensus producer.
Each extraction supplies one vote group. The two scans are neither independent
editions nor independent OCR model families. Tied readings retain all variants
and contribute no scalar lexical token. Single-witness readings remain marked
as such. This process establishes neither an OCR accuracy score nor diplomatic
punctuation: the primary is a merged Greek-word projection. Original punctuation,
Latin sigla, verse numbers, and row order remain in the citable secondary text.

`changes.json` publishes the original and current accounting, reading-status
counts, work totals, recipe hashes, and deduplication measurements. Its compressed
`records.jsonl.gz` records every original row and destination partition;
`collations.jsonl.gz` records original and merged text with timestamps and
source evidence. `word-networks.json.gz` retains every aligned reading and vote.
The ordinary public lexicon uses only the strictly verified lexical projection.
The page-word projection supplies no bigram or positional votes: it cannot
establish adjacency across source material excluded before alignment.
Experimental Dilemma frequencies are not part of this repair.

## Citations and reversibility

The audit owns an alias fragment composed into `work_index.json`; the older
shared `data/passage_aliases.json` remains unchanged. An old citation resolves
to its literal reading, with a link to the current merged page where admitted.
A mixed row resolves to its full original and lists its exact partitions.
The former Platonius whole-volume identity, `ogc002861`, is retired in the
immutable identifier ledger. It has no single successor and is not redirected
to one arbitrarily. Its individual historical citations remain resolvable.

```sh
python3 scripts/capture_dubner_sources.py --check
python3 scripts/dubner_current_state.py --check
```

The repair can be reproduced from its frozen preimages and reviewed source
observations. In an isolated checkout, `--undo` restores the exact original
corpus and secondary bytes; `--apply` reapplies the partition. Undo requires only
the frozen preimages and postimage hashes, so invalidating a correction's source
does not prevent literal recovery. Both operations refuse later changes to
their owned files. Derived indexes, registries, and frequency artifacts must
then be rebuilt normally. The earlier Acharnians ten-page pilot remains a
historical audit of the pre-repair release.

## Later occurrence and layout review

`repair_dubner_readings.py` adds a separately reversible reading layer. Its
45 historical occurrence corrections retain exact raw source offsets, printed
evidence, original and corrected text, and contrary readings. Seven reviewed
cell permutations restore column order without adding or removing a visible
source character or introducing another vote group. Three partial duplicated
column layouts remain held because a permutation cannot establish their
physical word identities.

The layer reduces unresolved slots from 75,797 to 72,390, with 199,421 eligible
Greek tokens. The remaining nonoverlapping categories are 10,228 omission ties,
19,796 normalized-form disagreements, and 42,366 different-word readings. A
separate count of 10,238 disagreements within one extraction overlaps those
categories. These measurements describe extraction disagreement, not recognition
accuracy. Four heading or editorial corrections remain separate outside-primary
reading overlays; they do not change the frozen paratext display or admit text.

The scan reads `ἐν Ληναίοις διὰ Καλλιστράτου` at the pilot's proposed missing-eta
example. The new occurrence authority explicitly supersedes the old proposed
`Ἀθηναίοις` while retaining that historical observation unchanged.

```sh
python3 scripts/capture_dubner_readings.py --check
python3 scripts/capture_dubner_layouts.py --check
python3 scripts/repair_dubner_readings.py --check
```

Source captures and generated observations are under
`data/corpus_changes/dubner-reading-review/` and `dubner-layout-review/`;
the reading preimages, networks, records, and complete remaining assessment are
under `data/corpus_changes/dubner-1855-readings/`. The generator code contains
the reviewed decisions. The ordinary current-state checker proves every frozen
scope output against either its unchanged bytes or the checked later preimage.
Undo the reading layer before undoing the source partition. Literal undo remains
possible after a correction source is invalidated; a new source decision must
be admitted in another layer rather than rewriting either frozen authority.

## Continued evidence review

`scripts/review_dubner_evidence.py` adds a third, separately reversible layer.
The source review identifies the full-column extracts on the three previously
held pages: Toronto PDF 94 / Harvard 95, Toronto 107 / Harvard 108, and Toronto
271 / Harvard 298. Their 144 narrow overlapping snippets remain literal,
attributed evidence in the full networks and routing records. They supply no
additional historical occurrence, reading vote, or omission vote. The complete
column projections still merge the Toronto and Harvard extraction groups;
unresolved full-column alternatives remain excluded from scalar lexical counts.
This layout decision does not certify the snippets' individual spellings or
claim a word-by-word alignment of their truncated readings.

Forty-nine occurrence decisions correct printed readings on those three pages
and the index-linked Wasps passage on Toronto PDF 190 / Harvard 199. The Greek
index on printed page 725 points from φορβειά to Wasps 582 and Birds 861, 15,
and from φόρβιον to Birds 861. Both body passages were inspected directly;
their accents and inflections follow the print, not the index OCR. The critical
note on Knights 527 helps locate ἀφελῶν / ἀφελές. Its quoted manuscript variants
and modern additions remain editorial evidence. The Corrigenda correct
annotations and references; this layer adopts no editorial emendation.

The continued review reduces unresolved slots from 72,390 to 72,086 and raises
eligible Greek tokens from 199,421 to 199,482. Layout separation accounts for
255 fewer unresolved slots and 12 additional eligible tokens; the 49 printed
reading decisions account for the remainder. These are alignment and lexical
accounting measurements, not an OCR accuracy estimate.

The generated assessment inventories exact κ/χ disagreements before and after
review, with named page and slot positions. It also preserves the source-specific
annotation and index OCR locators used during this review. The baseline has
3,283 candidate slots on 380 pages; valid pairs such as οὐκ / οὐχ demonstrate
why this inventory cannot authorize a global substitution. Further source
decisions require a later layer with occurrence evidence. Remaining uncertainty
is published through the existing known-limitations registry.

```sh
python3 scripts/capture_dubner_evidence.py --capture \
  --toronto-pdf /path/to/scholiagraecaina00dbuoft.pdf \
  --harvard-pdf /path/to/scholiagraecain01dbgoog.pdf
python3 scripts/capture_dubner_evidence.py --check
python3 scripts/dubner_current_state.py --check
```

Capture requires PyMuPDF 1.28.2 and both checksum-pinned PDFs. The ordinary
checks are offline and require no renderer. The continuation's `apply`,
`verify`, and `undo` commands reproduce or reverse its exact primary bytes.
Undo it before undoing the older reading and scope layers. Old source receipts
and citation aliases remain frozen and are checked against exact predecessor
views; the continuation cannot waive a missing or changed earlier output.
