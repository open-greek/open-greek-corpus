"""Register source-qualified credits for the reviewed duplicate passages.

This layer supplements existing edition composition. It does not change a
Work's default edition or reinterpret its complementary-volume components.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

import repair_reviewed_duplicate_blocks as repair
from reviewed_duplicate_block_observations import CYRIL, HESYCHIUS, UPSTREAM_TEXTS

ROOT = Path(__file__).resolve().parents[1]
WITNESS_EDITION = "reviewed-duplicate-block-literal-witnesses-2026-10"


def _signature(root):
    authority = root / repair.AUDIT / "changes.json"
    audit = json.loads(authority.read_bytes())
    capture_path = repair.AUDIT + "/source-evidence.json"
    capture = json.loads((root / capture_path).read_bytes())
    names = {repair.AUDIT + "/changes.json", repair.AUDIT + "/before.json.gz",
        capture_path, *audit["inputs"], *audit["outputs"],
        *(item["path"] for item in capture["files"]),
        *("scripts/" + name for name in audit["recipe_sha256"])}
    return tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in sorted(names))


def _edition(key, name, *, provider, license_value, source, scheme, storage, note):
    return {"key": key, "name": name, "provider": provider, "license": license_value,
        "source": source, "scheme": scheme, "storage": storage,
        "editor": "", "year": None, "servable": True, "note": note}


@lru_cache(maxsize=2)
def _verified_metadata(root_name, signature):
    root = Path(root_name)
    audit, before = repair.verify(root, replay=True)
    authority = {"path": repair.AUDIT + "/changes.json",
                 "sha256": repair.sha((root / repair.AUDIT / "changes.json").read_bytes())}
    output = {}
    for slug in (CYRIL, HESYCHIUS):
        primary_path = f"data/corpus/{slug}.jsonl"
        witness_path = f"data/corpus_secondary/{slug}.reviewed-duplicate-witnesses.jsonl"
        primary_file = [json.loads(line) for line in (root / primary_path).read_bytes().splitlines()]
        primary = [row for row in primary_file if row.get("edition") == repair.EDITION]
        witnesses = [json.loads(line) for line in (root / witness_path).read_bytes().splitlines()]
        groups = [deepcopy(group) for group in audit["groups"] if group["slug"] == slug]
        counts = {field: sum(group[field] for group in groups) for field in (
            "original_rows", "primary_rows", "literal_witness_rows", "original_greek_tokens",
            "surface_greek_tokens", "analysis_greek_tokens")}
        counts.update(collated_passages=len(groups),
            primary_rows_removed=counts["original_rows"] - counts["primary_rows"],
            reading_statuses=dict(sum((Counter(group["reading_statuses"]) for group in groups), Counter())))
        provider, license_value, source_id = ("cgpg", "CC-BY-4.0", "cyril-pg73") if slug == CYRIL else ("ocr", "PD", "hesychius")
        if (len(primary) != counts["primary_rows"] or len(witnesses) != counts["literal_witness_rows"]
                or any(row["source"] != provider or row["license"] != license_value for row in primary + witnesses)):
            raise ValueError("Reviewed duplicate manifestation source or passage counts changed: " + slug)
        sources = [deepcopy(source) for source in audit["sources"] if source["id"] == source_id]
        if len(sources) != 1:
            raise ValueError("Reviewed duplicate manifestation lacks its pinned reference scan")
        upstream_texts = deepcopy(list(UPSTREAM_TEXTS)) if slug == CYRIL else []
        source = upstream_texts[0]["url"] if upstream_texts else sources[0]["url"]
        attribution = ("Calfa, Patrologia Graeca OCR, PG073" if slug == CYRIL else
            "Retained qwen36-hesychius_schmidt_masked OCR extraction of the pinned Hesychius scan")
        source_pins = {primary_path: audit["inputs"][primary_path]}
        for upstream in upstream_texts:
            source_pins[upstream["local_artifact"]] = audit["inputs"][upstream["local_artifact"]]
        primary_note = (
            f"Only {len(primary)} reviewed physical passages in {primary_path}; "
            "derived from repeated readings of one upstream extraction. " + audit["qualification"])
        witness_note = (
            f"Only {len(witnesses)} literal original rows in {witness_path}. "
            "The original edition fields remain on these rows; this registry record identifies "
            "their secondary storage and does not replace the existing source edition. " + audit["qualification"])
        primary_edition = _edition(repair.EDITION,
            "Reviewed duplicate-block collation of Calfa PG073 readings" if slug == CYRIL else
            "Reviewed duplicate-block collation of Hesychius OCR readings",
            provider=provider, license_value=license_value, source=source,
            scheme="reviewed-duplicate.source.block", storage="primary", note=primary_note)
        witness_edition = _edition(WITNESS_EDITION,
            "Calfa PG073, retained literal duplicate readings" if slug == CYRIL else
            "Hesychius, retained literal duplicate OCR readings",
            provider=provider, license_value=license_value, source=source,
            scheme="volume.marker-page" if slug == CYRIL else "source-page.row",
            storage="secondary", note=witness_note)
        common = {"provider": provider, "license": license_value, "source": source,
                  "attribution": attribution, "source_pins": source_pins,
                  "source_preimage_archive": {"path": repair.AUDIT + "/before.json.gz",
                      "sha256": audit["before_sha256"]},
                  "sources": sources, "upstream_texts": upstream_texts}
        components = [
            {**deepcopy(common), "edition": repair.EDITION, "storage": "primary",
             "path": primary_path, "sha256": audit["outputs"][primary_path],
             "role": "reviewed-duplicate-block-projection", "passages": len(primary),
             "loci": [row["locus"] for row in primary],
             "surface_greek_tokens": counts["surface_greek_tokens"],
             "analysis_greek_tokens": counts["analysis_greek_tokens"]},
            {**deepcopy(common), "edition": WITNESS_EDITION, "storage": "secondary",
             "path": witness_path, "sha256": audit["outputs"][witness_path],
             "role": "literal-duplicate-readings", "passages": len(witnesses),
             "original_editions": sorted({row["edition"] for row in witnesses}),
             "original_greek_tokens": counts["original_greek_tokens"],
             "counts_toward_primary_frequency": False},
        ]
        output[slug] = {"editions": [primary_edition, witness_edition],
            "later_duplicate_review": {"authority": deepcopy(authority), "groups": groups,
                "counts": counts, "sources": sources, "upstream_texts": upstream_texts,
                "attribution": attribution, "qualification": audit["qualification"],
                "components": components, "work_file_accounting": {
                    "original_primary_rows": len(before[primary_path].splitlines()),
                    "current_primary_rows": len(primary_file)}}}
    return output


def metadata(root=ROOT):
    root = Path(root)
    authority = root / repair.AUDIT / "changes.json"
    archive = root / repair.AUDIT / "before.json.gz"
    if authority.is_file() != archive.is_file():
        raise ValueError("Reviewed duplicate authority or predecessor archive is missing")
    if not authority.is_file() or not repair.active(root):
        return {}
    return deepcopy(_verified_metadata(str(root), _signature(root)))


def register(registry, root=ROOT):
    """Supplement source credits while preserving defaults and base components."""
    reviewed = metadata(root)
    missing = set(reviewed) - set(registry.works)
    if missing:
        raise ValueError("Reviewed duplicate admission has no canonical registry Work: " + ", ".join(sorted(missing)))
    for slug, value in reviewed.items():
        work = registry.works[slug]
        previous_default = work.default_edition
        composition = deepcopy(work.coverage_composition)
        for edition in value["editions"]:
            key = registry.mint_edition(slug, edition["key"], edition["name"])
            record = work.editions[key]
            for field, content in edition.items():
                if field != "key":
                    setattr(record, field, deepcopy(content))
        # mint_edition auto-fills an empty default; registration must not do so.
        work.default_edition = previous_default
        composition["later_duplicate_review"] = deepcopy(value["later_duplicate_review"])
        work.coverage_composition = composition
    return reviewed
