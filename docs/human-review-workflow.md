# Evidence-preserving human review

The remaining large defect classes are measured, but their current evidence
does not select a safe automatic edit. `scripts/build_human_review_queue.py`
turns those measurements into review packets without changing served text.

## Build a packet

```bash
python3 scripts/build_human_review_queue.py build --issue 31 --limit 100
python3 scripts/build_human_review_queue.py build --issue 33 --limit 100
python3 scripts/build_human_review_queue.py build --issue 33 \
  --run-extensions --require-scan --limit 25
python3 scripts/build_human_review_queue.py build --issue 2 --limit 100
python3 scripts/build_human_review_queue.py build --issue 2 --limit 100 \
  --require-scan --pages-per-work 5 --exclude data/review/issue-2.jsonl
python3 scripts/build_human_review_queue.py build --issue 2 --require-scan \
  --page adrianus-rhetor.meletai=530.2 \
  --page anonymi-in-hermogenis-de-statibus.peri-ton-staseon-walz-v-591=594.1
python3 scripts/build_human_review_queue.py build --issue 1 \
  --corrections-log data/corrections_log/applied.jsonl --limit 200
```

Use `--require-scan` when a batch must have exact Archive.org leaf images,
`--exclude` (repeatable) to omit IDs from earlier queue or sealed JSONL files,
and `--work SLUG` to build a targeted issue #2 packet. These controls make
review rounds resumable without changing stable item IDs.
Use repeatable `--page WORK=PAGE` for a small packet of already identified
issue #2 leaves. Every requested page must exist and have the required scan;
the build fails instead of silently substituting a different page.

Each command writes under `data/review/`:

- `issue-N.jsonl`: the packet to give reviewers.
- `issue-N.decisions.tsv`: the sheet reviewers complete.
- `issue-N.manifest.json`: commit, corpus/release pin, input hashes, and queue
  hash.
- `issue-1.audit.jsonl`: the hidden answer key and correction metadata for the
  blind rating. Do not give this file to raters.

Packets are local working data and gitignored. Select a different location with
`--output`. Stable item IDs make separately completed sheets mergeable.

For scan-first review, run the loopback-only browser interface:

```bash
python3 scripts/serve_human_review.py \
  --queue data/review/issue-31.jsonl --open
```

It shows the source page beside the served context and writes each completed
decision atomically to the packet's TSV sheet. It has no corpus-write endpoint.

## What each packet contains

- **#31 non-final graves:** exact served row and offset, masked context,
  competing mechanical readings, corpus evidence when available, page density,
  and an Archive.org page link when OCR provenance can identify the scan.
- **#33 duplicate pages:** both complete page texts and scan links, previous and
  next page context for both sides, containment and same-item signals, and the
  unique text each drop would lose. The paired scan view is side by side on
  desktop and stacked on narrow screens.
- **#1 correction precision:** a deterministic method-stratified sample. The
  original and applied readings are randomized as A/B, the target is masked,
  and method/confidence/evidence stay only in the separate audit key.
- **#2 raw OCR:** one substantive page from each of the largest raw-OCR works by
  default, or multiple ranked pages with `--pages-per-work`, prioritized toward
  pages with a source-scan link. The packet includes every
  current row on the page with its locus, line, text hash, and file hash. A
  transcription is entered as ordered per-locus segments whose newline join is
  the reviewed page text.

The scan link is a candidate leaf derived from the OCR run's page key. Reviewers
must confirm that the image and served row align before making a decisive call.
For #33, `--run-extensions` narrows the queue to pairs whose two leaves move in
lockstep within four page positions of a previously applied, scan-reviewed
duplicate pair. Its prior decision is included as a ranking signal, not an
inherited answer: both new page images still require independent review.

## Validate decisions

Every completed decision needs a reviewer and review date. Decisive changes also
need an evidence URL; replacement/transcription decisions need the reviewed
reading. A deferral needs a note.

```bash
python3 scripts/build_human_review_queue.py validate \
  --queue data/review/issue-31.jsonl \
  --decisions data/review/issue-31.decisions.tsv \
  --write data/review/issue-31.reviewed.jsonl
```

The sealed JSONL carries the queue hash. It is still not an edit list. Publish a
reviewed decision only through the issue-specific reversible repair tool, with
the packet manifest and sealed decisions named in its audit artifact. This
separation prevents a spreadsheet typo or a single unreviewed answer from
silently rewriting Greek.

For issue #31, the occurrence-specific applicator enforces that separation. It
requires a complete sealed packet and defaults to a dry run:

```bash
python3 scripts/apply_reviewed_nonfinal_graves.py
python3 scripts/apply_reviewed_nonfinal_graves.py --apply
```

The applied audit stores every exact row preimage, reviewed reading, evidence
URL, file hash, and the reverse command. A stale queue, shifted offset, changed
row, foreign decision, or partial review is rejected before any file is written.

Issue #33 has the same sealed apply boundary. Accepted `drop_a`/`drop_b`
decisions move the losing page into a pass-specific secondary-witness file;
they never delete a reading. Overlapping pairs are treated as a directed
component, cycles and competing winners are rejected, and every chain must end
at a page that remains served:

```bash
python3 scripts/apply_reviewed_duplicate_pages.py
python3 scripts/apply_reviewed_duplicate_pages.py --apply
```

Issue #2 now has the same sealed apply boundary. The applicator requires an
ordered segment for every current locus, checks the queued row and page hashes,
and defaults to a dry run. Applied audits preserve every exact JSONL preimage
and support byte-for-byte rollback:

```bash
python3 scripts/apply_reviewed_ocr_pages.py \
  --queue data/review/issue-2.jsonl \
  --reviewed data/review/issue-2.reviewed.jsonl \
  --manifest data/review/issue-2.manifest.json
python3 scripts/apply_reviewed_ocr_pages.py \
  --queue data/review/issue-2.jsonl \
  --reviewed data/review/issue-2.reviewed.jsonl \
  --manifest data/review/issue-2.manifest.json --apply
```

The tool never guesses how a page should be divided and does not stamp a whole
work as manually corrected from one reviewed leaf. A stale, partial, reordered,
or foreign transcription is rejected before any corpus file is written.
