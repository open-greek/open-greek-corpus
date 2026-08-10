# Paratext

Text captured from the OCR'd source volumes that is not part of the primary
served Greek corpus (`data/corpus/`). It exists so nothing printed in a
public-domain volume is silently dropped, and it is excluded from every Greek
coverage, lemma, and frequency rollup.

- `latin.jsonl` - Latin apparatus criticus, indices, and the Latin translation
  columns / Latin text-versions (e.g. the medieval Latin Oribasius). `lang: la`.
- `modern.jsonl` - editors' modern-language translations and introductions
  (German, French, English). `lang: de|fr|en`.
- `edition_apparatus.jsonl` - what Migne prints around the works rather than as
  them: the 1532 Verona editor's preface to Oecumenius, Migne's prefatory
  dissertation and testimonia for the Excerpta historians, a florilegium about
  Ignatius assembled from a dozen named authors, Nicephorus Callistus' table of
  contents, Leo Allatius' Latin dissertation. Each row carries `why_not_served`
  and keeps its `cogPG.<VOL>` slug and locus, so a correction record keyed to
  them still places. `lang: grc` is the script, not always the language: several
  blocks (PG124, PG109, most of PG125) are Latin read as Greek letter shapes,
  which is why they read as nonsense Greek. Moved 2026-08-10 on cisco's call;
  reversible from `data/corpus_changes/apparatus-to-paratext.json`.
- `recovered_greek.jsonl` - genuine Greek (quotations, note-wrapped columns)
  that the Greek-only extraction dropped from mixed Latin-typeset pages.
  `lang: grc`, `class: recovered_pending_merge`. These are CANDIDATES for
  folding into the served works after the normal normalize/mopup/align/verify
  QA - not yet served, because the OCR of Greek in Latin founts is error-prone.

Records: `{slug, page, lang, license, source, edition, text}` keyed by the OCR
source volume slug and printed page. All from the Qwen3.6-27B re-OCR.
