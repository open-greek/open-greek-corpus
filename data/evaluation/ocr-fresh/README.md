# Fresh scan witnesses

These JSONL files preserve OCR requests and raw responses. The first record
identifies the checkpoint revision, runtime, runner, and checksum-pinned request
manifest. Each remaining record retains the image and prompt hashes, original
prediction, termination reason, and timing. Request manifests are archived by
SHA-256 under `manifests/`. A successful response is a source reading, not a
proofread transcription.

Only the inputs named by an admission audit under `data/corpus_changes/` or
`data/corpus_extensions/` participate in served consensus. The complete word
networks, exclusions, unresolved readings, and reversible before images live
with those audits. Sanity samples do not provide additional independent votes
when their checkpoint is also present in a complete run.

`meibom-qwen38-mlx.jsonl` preserves an early three-page trial whose narrow crop
clipped text. `meibom-qwen36.jsonl` preserves the abandoned partial trial of the
older Meibom printing. Neither is a primary voting witness. The Aristides
admission uses the reviewed Jahn 1882 body regions instead. Raw Meibom readings
remain available separately as historical secondary witnesses.

The `polytonic-*` files are the independent, frozen 60-page validation sample
for the polytonic-loss detector. Their gold-reference exclusions, calibration
and test split, and outcome reports are under `data/evaluation/polytonic-loss/`.
They are not corpus replacement text.
