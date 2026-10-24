"""Register only verified historical units from the Westermann source split."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import repair_westermann_scope as repair

ROOT = Path(__file__).resolve().parents[1]
# The printed Pindar commentator is the same person already represented by the
# corpus's Eustathius philological works. This does not authorize an identity
# guess for the Ionia's Eudocia or the bracketed Ammonius attribution.
CANONICAL_AUTHORS = {
    "eustathius-thessalonicensis": ("eustathius-philol", "Eustathius"),
}


def identity_metadata(root=ROOT):
    return repair.metadata(root)


def register_identities(registry, root=ROOT, *, identities=None):
    identities = identity_metadata(root) if identities is None else identities
    for slug, value in identities.items():
        author, author_name = CANONICAL_AUTHORS.get(value["author"],
            (value["author"], value["author_name"]))
        registry.mint_author(author_name, slug=author)
        aliases = {"cts": value["cts"]} if value.get("cts") else {}
        registry.mint_work(author, value["title"], slug=slug, aliases=aliases)
        work = registry.works[slug]
        work.author, work.title, work.best_source = author, value["title"], "open_corpus"
    return identities


def register(registry, root=ROOT):
    root = Path(root)
    identities = register_identities(registry, root)
    if not identities:
        return identities
    from westermann_source_observations import SOURCE
    audit, _ = repair.checked_state(root)
    for slug, value in identities.items():
        work = registry.works[slug]
        if slug == repair.OLD:
            old = work.editions.get(slug + ".migne-ocr-qwen36")
            if old is not None:
                old.servable, old.storage = False, "audit"
                old.source = SOURCE["url"]
                old.name = "Westermann 1845, historical whole-anthology assignment"
                old.note = (
                    "This former primary contained the entire biography anthology. "
                    "Its exact original rows remain at " + repair.LITERAL + ". " + repair.QUALIFICATION)
        key = registry.mint_edition(slug, repair.EDITION,
            value["title"] + " (Westermann 1845, source-scoped OCR)")
        edition = work.editions[key]
        edition.provider, edition.license, edition.source = "ocr", "PD", SOURCE["url"]
        edition.editor, edition.year = "Westermann, Antonius", 1845
        edition.scheme, edition.storage, edition.servable = "source-page.row.region", "primary", True
        edition.note = repair.QUALIFICATION
        work.default_edition = key
        path = f"data/corpus/{slug}.jsonl"
        work.coverage_composition = {
            "policy": "source-supported-anthology-partition-with-comparative-witnesses",
            "manifest": value["authority"]["path"], "manifest_sha256": value["authority"]["sha256"],
            "qualification": repair.QUALIFICATION, "source_scope": deepcopy(value["source_scope"]),
            "attribution_qualification": value["attribution_qualification"],
            "source_attribution": {"author_slug": value["author"], "author_name": value["author_name"]},
            "canonical_author": {"slug": work.author, "name": registry.authors[work.author].name},
            "source_editions": [deepcopy(SOURCE)], "counts": deepcopy(value["counts"]),
            "components": [
                {"edition": repair.EDITION, "role": "source-supported-historical-body",
                 "provider": "ocr", "license": "PD", "source": SOURCE["url"],
                 "storage": "primary", "path": path, "sha256": audit["outputs"][path],
                 "passages": value["counts"].get("primary_rows", 0)},
                {"role": "literal-original-anthology-witness", "license": "PD",
                 "storage": "audit", "path": repair.LITERAL,
                 "sha256": audit["outputs"][repair.LITERAL],
                 "selection": "Use the original loci and character ranges recorded on each scoped primary row.",
                 "counts_toward_primary_frequency": False},
            ]}
    return identities
