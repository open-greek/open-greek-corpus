# Source policy for annotation corpora

cog is taking on a second role: alongside standardizing open Greek *texts*, it
now standardizes external Greek *annotation* corpora (treebanks, morphosyntactic
taggings, lemmatizations) into one export format. This policy governs which
annotation sources cog may ingest and re-export. Its companions are
`annotation-export-contract.md` (the export format and worklists) and
`pinning-discipline.md` (how upstreams are pinned).

The rule for texts already stated in the README, no non-commercial licenses,
carries over to annotation unchanged, plus two source-specific policies that only
arise for annotation: PROIEL provenance and Gorman provenance.

## Licensing: openly licensed only

Only openly-licensed sources are ingested, in any role. Any NonCommercial clause
(CC BY-NC, CC BY-NC-SA, or any other NC term) is banned. An annotation corpus
available only under an NC license counts as a gap, the same way an NC-only text
does; it is not ingested and not re-exported.

Named NC exclusions (do not ingest, in any role):

| source | what it is | why excluded |
|---|---|---|
| CGRN | Collection of Greek Ritual Norms | CC BY-NC-SA |
| OGA `pta0036` | Anonymus of Cyzicus (the single BY-NC-SA file in the OGA / PTA set) | CC BY-NC-SA |
| AGILe lemmatizer | a lemmatizer model trained on CGRN + PROIEL | doubly disqualified: its training data is NC (CGRN) and PROIEL, so its outputs are both NC-derived and PROIEL-model outputs; not used even as a tier-2 model (see below) |

## PROIEL provenance: three tiers

PROIEL-derived annotation carries an ingestion restriction cog honors. The policy
has three tiers, and they must not be flattened to "PROIEL is banned everywhere":
that over-bans, because the *output of a model trained on PROIEL* is legitimate
and is a different thing from PROIEL data itself.

### Tier 1 - PROIEL data: banned in every role

PROIEL treebank data may not be ingested or re-exported. This ban follows the
data through re-exports and revisions: a downstream corpus that re-exported or
hand-revised PROIEL trees is still PROIEL data and is still banned. Named tier-1
exclusions:

- AthDGC, its Koine reference set (arXiv 2606.15510).
- DiGreC, its Herodotus, New Testament, Septuagint, and Sphrantzes sections.
- GLAUx, the 25 works marked `TREEBANK_ANNOTATIONS='PROIEL'` in its
  `metadata.txt`.
- Pedalion, the rows whose per-token ref prefix is `PRO1` or `PRO2`.

### Tier 2 - outputs of PROIEL-trained models: acceptable but dispreferred

Annotation produced by a model that was trained on PROIEL is acceptable to
ingest, but dispreferred: when a non-PROIEL source covers the same work, prefer
it. Examples:

- DiGreC, its human-reviewed remainder (everything outside the tier-1 sections).
- GLAUx, its `analysis="auto"` sentences.

### Tier 3 (implicit) - non-PROIEL data

Everything that is neither PROIEL data nor PROIEL-model output is fine, subject
to the licensing rule above.

## Gorman provenance: tag, don't delete

At this standardization layer cog includes Gorman-derived annotation, tagged
`provenance=gorman`; it does not drop it. The Gorman-tagged sources are:

- the Gorman trees themselves;
- GLAUx's `analysis="manual"` sentences in the 40 works GLAUx credits to Gorman;
- Pedalion's rows whose ref prefix is `GORMAN`.

Rationale: Gorman is dilemma's held-out gold set, so dilemma filters
`provenance=gorman` at read time. That filtering is dilemma's consumption rule,
not cog's standardization policy. Other consumers may legitimately use
Gorman-tagged annotation, so cog's job is to standardize it and tag it accurately;
the consumer's job is to filter what it must not see. "Never ingest Gorman" is
dilemma's rule about its own reading, not a rule about what cog may hold.

For the text queue Gorman is moot: it is annotation over texts cog already holds,
not a new text source.

## See also

- `annotation-export-contract.md` - the record schema, encoding guarantees, and
  the consumption-order worklists (annotation queue plus the text-source
  watchlist).
- `pinning-discipline.md` - one owner per fact: cog pins upstreams, consumers pin
  cog.
