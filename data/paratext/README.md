# Paratext

Text captured from the OCR'd source volumes that is not part of the primary
served Greek corpus (`data/corpus/`). It exists so nothing printed in a
public-domain volume is silently dropped, and it is excluded from every Greek
coverage, lemma, and frequency rollup.

- `latin.jsonl` - Latin apparatus criticus, indices, and the Latin translation
  columns / Latin text-versions (e.g. the medieval Latin Oribasius). `lang: la`.
- `modern.jsonl` - editors' modern-language translations and introductions
  (German, French, English). `lang: de|fr|en`.
- `recovered_greek.jsonl` - genuine Greek (quotations, note-wrapped columns)
  that the Greek-only extraction dropped from mixed Latin-typeset pages.
  `lang: grc`, `class: recovered_pending_merge`. These are CANDIDATES for
  folding into the served works after the normal normalize/mopup/align/verify
  QA - not yet served, because the OCR of Greek in Latin founts is error-prone.

Records: `{slug, page, lang, license, source, edition, text}` keyed by the OCR
source volume slug and printed page. All from the Qwen3.6-27B re-OCR.
