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
| 1b | PTNK | preserve the UD (Universal Dependencies) train / dev / test split | built (`ptnk-v1`) |
| 1c | Pedalion trees | the per-token ref prefix *is* the provenance: `Leuven` / `PER` / `GORMAN` / `PRO1` / `PRO2` / `HARR`. Apply the source policy at ingest: drop `PRO1` / `PRO2` (tier-1 PROIEL), tag `GORMAN` rows `provenance=gorman`, pass the rest through. | built (`pedalion-v1`) |
| 1d | TAGNT | word-level annotation | built (`tagnt-v1`) |
| 1e | GLAUx | carry the per-sentence `analysis` (`manual` / `auto`) and the per-work `TREEBANK_ANNOTATIONS` provenance; drop the 25 PROIEL-marked works (tier 1), exclude NC and unclear source licenses, tag the Gorman-credited works' manual sentences `provenance=gorman`. | built (`glaux-v1`, pending publish) |
| 1e | Diorisis | the other half of item 1e; carry its per-sentence annotation with the same policy screens. | queued |

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

#### Built: Pedalion export `pedalion-v1`

Item 1c's payload lives on the Hub under `pedalion-v1/` (per-work
`works/<work_key>.jsonl.gz` plus `manifest.json` and `pedalion_scope_audit.json`);
the git-tracked pointer stub is `data/annotations/pedalion/pedalion-v1.json`. It is
produced reproducibly by `scripts/export_pedalion_annotations.py` from the retained
Pedalion clone (source commit `112c106b`, CC BY-SA 4.0, verified from
`TREEBANK_LICENSE` at run time). Scope: 123 works / 80,840 tokens (6,417 sentences) =
8 literary works GLAUx does not subsume, the three Pedalion example-sentence
collections, and 112 papyri (per Trismegistos id). Every token is `analysis=manual`.
The per-token ref prefix drives the source policy: `PRO1`/`PRO2` (tier-1 PROIEL,
937 tokens) dropped; `GORMAN` (1,872 tokens) kept as `provenance_tag=gorman`;
`Leuven`/`PER`/`HARR` (78,968 tokens) kept as `provenance_tag=pedalion` with the
ref prefix in `ref_provenance`. The Menander Dyskolos file (1958 Bodmer edition) is
excluded on edition-rights grounds, and the literary scope (works not already in
GLAUx) is re-verified against GLAUx's `metadata.txt` at run time. dilemma pins:

    cog export pedalion-v1, sha256:ec549294330f0dafdc826fd7e44ec6eaa176cb4d76a5f542003b8d75c370edea

#### Built: GLAUx export `glaux-v1` (pending publish)

Item 1e's GLAUx half. The payload lives on the Hub per "Storage" above, under
`glaux-v1/` (per-work `works/<cts-work-id>.jsonl.gz` plus `manifest.json` and
`glaux_scope_audit.json`); the git-tracked pointer stub is
`data/annotations/glaux/glaux-v1.json`. It is produced reproducibly by
`scripts/export_glaux_annotations.py` from the retained GLAUx clone (commit
`b077d8f6`, corpus CC BY-SA). Scope: 1,375 CTS works (1,387 GLAUx documents;
letter-suffix parts merged into their base work with a per-token `doc` field),
19,383,236 tokens, 941,208 sentences. GLAUx's native per-sentence `analysis`
(`manual` / `auto`) is carried per token and the per-work `TREEBANK_ANNOTATIONS`
credit in the manifest. Policy screens, all re-derived from `metadata.txt` at
run time: the 25 PROIEL-marked works (tier 1, 364,200 tokens) are dropped; the
7 NonCommercial SOURCE_LICENSE works (107,200 tokens, largest Aesop `0096-002a`)
are excluded; 2 unclear-license works (6,380 tokens: `0237-003` OpenEdition
Books License, `2034-006` GPL) are excluded because the aggregate is published
under CC BY-SA and unknown or unclear per-work licenses are excluded rather
than served. Manual sentences in the 40 Gorman-credited works are
`provenance_tag=gorman` (19,891 sentences / 490,511 tokens); everything else is
`provenance_tag=glaux`. Encoding is normalized per this contract. dilemma pins:

    cog export glaux-v1, sha256:dda362b02dd980b26d44deb01f62a726b168ebb2d84ddff7842fb9265daca83c

Gorman coverage ruling (diffed against vgorman1/Greek-Dependency-Trees): all 40
Gorman-credited GLAUx works appear in the Gorman repo, so `glaux-v1` subsumes
the Gorman trees at work level, with the `gorman` tag marking exactly their
manual sentences. Gorman trees NOT subsumed, a possible small future item:
Herodotus book 1 (GLAUx's Herodotus is PROIEL-marked and dropped), Andocides 1
(partial, sections 1-75), Demosthenes 7 / 17 / 27 / 36 / 37 / 39 / 42 / 45 /
51 / 54 / 57, Isaeus 3, Isocrates 18, Plutarch `0007-087`, and Xenophon
Anabasis books 1 and 3 (all auto-only in GLAUx), plus Plato's Crito (in the
Gorman repo, but GLAUx credits its manual layer to Pedalion). License finding:
the Gorman repo's `TREEBANK LICENSE` is CC BY-SA 4.0 with no NonCommercial
term; the GLAUx README's "CC BY-NC-SA 4.0" claim for the Gorman trees is stale
against upstream.

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
