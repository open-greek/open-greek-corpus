# Annotation export contract

## Role

cog standardizes external Greek annotation corpora into one format. Consumers,
dilemma and others, ingest cog's exports, not the upstream treebank formats
(CoNLL-U, PROIEL XML, per-project TSV, and so on). cog owns the normalization
described here; the consumer owns any further mapping into its own conventions.

What may be ingested is governed by `source-policy.md`. How upstreams and exports
are pinned is governed by `pinning-discipline.md`. This document defines the
shape of the export, the guarantees cog makes about it, and the order in which
sources are brought in.

## Record schema

An export is per-work and CTS-URN-keyed. Each work's annotation is a stream of
token records. Each token record carries:

| field | meaning |
|---|---|
| `form` | the token surface form as it appears in the text |
| `lemma` | the lemma, in the source's native convention (see "Lemma conventions") |
| `pos` / `morph` | part of speech and morphology in the source's native tagset, not remapped to any common scheme; consumers own tagset mapping |
| `head` | the governing token, where the source provides dependency syntax |
| `deprel` | the dependency relation to the head, where present |
| `locus` | the CTS logical locus of the token's passage |
| `sentence_id` | the source's sentence identifier (the annotation unit) |
| `analysis` | `manual` or `auto`: whether the annotation was human-made or model-produced |
| `provenance_tag` | the source / provenance tag: `oga`, `ptnk`, `pedalion`, `gorman`, `proiel-...`, and so on |

`head` and `deprel` appear only for syntactically annotated sources; a
morphology-only or lemma-only source omits them. The `pos` / `morph` values stay
in the source's own tagset on purpose: remapping to a shared scheme is a lossy
decision the consumer should own, not one cog should bake into the export.

## Encoding normalization (guaranteed by cog)

cog owns encoding; consumers own convention mapping. Every exported token is
normalized so a consumer can rely on it without re-checking:

- Unicode NFC.
- Apostrophes unified to U+2019 (right single quotation mark), covering elision
  marks and the like.
- Standard final and medial sigma (medial sigma mid-word, final sigma word-final;
  no lunate sigma, no stray final sigma mid-word).

## Lemma conventions (preserved verbatim)

cog does not normalize lemma conventions. Each source's lemma convention is
preserved exactly as the source wrote it, and documented per source. This
includes:

- homograph-disambiguation digits (a trailing index that distinguishes two
  lemmas spelled alike);
- Koine versus Attic headword choices;
- any other project-specific lemma spelling.

Rationale: the lemma convention is a linguistic decision the source owns, and
silently normalizing it would destroy exactly the homograph distinctions that
annotation exists to carry and would corrupt cross-source comparison. A consumer
that wants a single unified lemma space maps it itself, from the documented
per-source convention.

## Versioning

Every export carries a release id and a content hash. Consumers pin the pair,
"cog export vN, hash X" (see `pinning-discipline.md`). A new release id is minted
whenever exported content changes; the content hash lets a consumer detect drift
without having to trust the release id alone.

## Storage

Export payloads live on the Hugging Face Hub, not in git. The dataset repo is
`ciscoriordan/open-greek-corpus-annotation-exports`; each release is a
subdirectory named by its release id (`oga-v1/`, and as further queue items are
built, `ptnk-v1/` and so on) holding the per-work `works/*.jsonl.gz` files, the
release `manifest.json`, and any license audit. This applies to every queue
item, 1a through 1e.

git tracks the recipe and the pointer, never the payload:

- the exporter script (for 1a, `scripts/export_oga_annotations.py`) and the
  upload script, `scripts/upload_annotation_export.py`;
- a per-release pointer stub at `data/annotations/<source>/<release>.json`
  recording the release id, content hash, HF dataset repo and path in repo, and
  the upstream pin. The exporter writes the stub; the payload directory next to
  it is gitignored.

Consumers (dilemma and others) fetch the payload from the HF dataset repo by the
pinned release id and verify the content hash against their pin. The hash is
computed over the uncompressed per-work payloads, so it is independent of gzip
framing and of where the bytes are hosted; moving a payload between hosts never
changes its identity or invalidates an existing pin.

## Consumption-order worklists

Two queues live here on purpose, so both roadmaps sit in one place: the
annotation-consumption queue (which annotation corpora cog standardizes, and in
what order) and the text-source watchlist (which text sources cog ingests next).

### Annotation-consumption queue

| tier | source | scope and per-source note | status |
|---|---|---|---|
| 1a | OGA annotations | Full source: 1,998 works / 40.05M tokens (a superset of the 718-work / 16.25M-token dilemma-blocking subset). Highest value; blocks dilemma Phase 2. | built (`oga-v1`) |
| 1b | PTNK | preserve the UD (Universal Dependencies) train / dev / test split | queued |
| 1c | Pedalion trees | the per-token ref prefix *is* the provenance: `Leuven` / `PER` / `GORMAN` / `PRO1` / `PRO2` / `HARR`. Apply the source policy at ingest: drop `PRO1` / `PRO2` (tier-1 PROIEL), tag `GORMAN` rows `provenance=gorman`, pass the rest through. | queued |
| 1d | TAGNT | word-level annotation | queued |
| 1e | GLAUx + Diorisis | carry the per-sentence `analysis` (`manual` / `auto`) and the per-work `TREEBANK_ANNOTATIONS` provenance; drop the 25 PROIEL-marked GLAUx works (tier 1), tag the 40 Gorman-credited works `provenance=gorman`. | queued |

#### Built: OGA export `oga-v1`

Item 1a's payload lives on the Hub per "Storage" above, at
`ciscoriordan/open-greek-corpus-annotation-exports` under `oga-v1/` (per-work
`works/<cts-work-id>.jsonl.gz` plus `manifest.json` and `pta_license_audit.json`);
the git-tracked pointer stub is `data/annotations/oga/oga-v1.json`. The payload is
produced reproducibly by `scripts/export_oga_annotations.py` from the retained
OGA v0.2.0 clone. It exports the
whole source: 1,998 works / 40,051,080 tokens (2,232,948 sentences), which is a superset of
the 718-work dilemma-blocking subset. Encoding is normalized per this contract (NFC;
elision apostrophes -> U+2019; standard final/medial sigma); lemmas are verbatim (homograph
digits, Koine headwords). Every token is `analysis=auto`, `provenance_tag=oga` (OGA's whole
layer is Trankit/GreTa model output; tier-2 PROIEL-model output under `source-policy.md`, not
tier-1 PROIEL data and not Gorman-derived). The one NonCommercial file, `pta0036.pta001.pta-grc1`
(CC BY-NC-SA 3.0), is excluded; the exclusion is re-derived at run time from the PTA per-file
TEI licences. dilemma Phase 2 pins:

    cog export oga-v1, sha256:52e7e350692a3af1e391552db023dde00c5a7b1d655b146991d4dcae75e5db37

### Text-source watchlist

Endorsed ingest order for text sources (distinct from the annotation queue
above):

1. OGA metadata, now, under this policy (OGA is also the 1a annotation source).
2. Pedalion papyri, next.
3. TAGNT New Testament text, third.

Watchlist, not yet endorsed, track for maturity and license: Codex Alexandrinus,
TAGOT, CNTR.

## Forward-looking: a cog-side annotation runner (not implemented)

This section records intent only. Nothing here is built, and none of it should be
implemented off this document alone.

A future cog-side runner could produce first-pass annotation for genuinely new,
F3-OCR'd text that no external corpus covers, using OGA's published models,
Trankit for morphosyntax and GreTa for lemmatization (arXiv:2410.12055). Such
output would be tagged `provenance=oga-models` with `analysis=auto`.

Caveats to honor before building it:

- Output over Gorman-covered works inherits a Gorman-adjacent caveat: the OGA
  models are trained on Gorman, so their predictions are not independent of the
  held-out gold and must be tagged and treated accordingly.
- Longer term, run several annotators and ROVER-vote their output rather than
  trusting a single model.
- Prerequisite, currently unverified: the models' actual availability and
  downloadability. Only the OGA *data* release is confirmed. Verify the Trankit
  and GreTa weights are actually published and fetchable before committing to
  this work.

## See also

- `source-policy.md` - licensing, the PROIEL three tiers, and the Gorman
  tag-don't-delete rule that the worklist notes above apply.
- `pinning-discipline.md` - the release-id-and-hash pin consumers record against
  this export.
