# Pinning discipline

One owner per fact. Every pin in the annotation supply chain is recorded in
exactly one place, by exactly one party. cog pins its upstreams; each consumer
pins cog. Neither re-pins the other's layer.

This keeps the chain reproducible without duplication: there is a single
authoritative record for each fact, and a single place to fix it if it is wrong.

## cog pins upstreams

For every ingested source, cog's per-source manifest records enough to
reconstruct the exact bytes it ingested.

- Zenodo (and other DOI) sources: the version DOI, never the concept DOI. The
  concept DOI floats to "latest" and is therefore not a pin at all. Record the
  Zenodo per-file checksums alongside it. Example: OGA's version DOI is
  `10.5281/zenodo.14206061`; the concept DOI would silently move to a future
  release and must not be used.
- git sources: the commit SHA, plus a retained local clone. A SHA pins bytes but
  not availability, the remote can disappear or force-push its history, so cog
  keeps its own clone at that SHA. The pin is the SHA and the clone together.

## Consumers pin cog

dilemma, and any other consumer, records only the export identity from the
export contract: "cog export vN, hash X" (the release id plus the content hash;
see `annotation-export-contract.md`). A consumer does not re-pin cog's upstreams;
that fact is owned by cog.

## Why one owner per fact

If both cog and a consumer pinned the same upstream DOI or SHA, the two records
could drift apart and it would become ambiguous which is authoritative. Splitting
the chain so the consumer pins cog and cog pins the upstream gives every fact a
single owner and a single place to correct it. cog is responsible for upstream
reproducibility; the consumer is responsible only for pinning the cog export it
built against.

## See also

- `source-policy.md` - which upstreams may be ingested in the first place.
- `annotation-export-contract.md` - where the export release id and content hash
  that consumers pin are defined.
