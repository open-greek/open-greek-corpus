# Evidence-preserving human review

The remaining large defect classes are measured, but their current evidence
does not select a safe automatic edit. `scripts/build_human_review_queue.py`
turns those measurements into review packets without changing served text.

## Build a packet

```bash
python3 scripts/build_human_review_queue.py build --issue 31 --limit 100
python3 scripts/build_human_review_queue.py build --issue 33 --limit 100
python3 scripts/build_human_review_queue.py build --issue 2 --limit 100
python3 scripts/build_human_review_queue.py build --issue 1 \
  --corrections-log data/corrections_log/applied.jsonl --limit 200
```

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
- **#33 duplicate pages:** both complete page texts, both scan links when
  available, containment and same-item signals, and the unique text each drop
  would lose.
- **#1 correction precision:** a deterministic method-stratified sample. The
  original and applied readings are randomized as A/B, the target is masked,
  and method/confidence/evidence stay only in the separate audit key.
- **#2 raw OCR:** one substantive page from each of the largest raw-OCR works,
  prioritized toward pages with a source-scan link.

The scan link is a candidate leaf derived from the OCR run's page key. Reviewers
must confirm that the image and served row align before making a decisive call.

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

A #2 page transcription is upstream evidence, not automatically a corpus edit.
The packet identifies the complete scan page and its current loci but does not
invent offsets for distributing a replacement among those loci. Publish the
sealed transcription in `data/corpus_changes/`, then re-ingest that page with
explicit logical boundaries. This keeps a correct page transcription from
becoming an incorrectly segmented corpus patch.
