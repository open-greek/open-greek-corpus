"""Credit the two recovered Hesychius columns without replacing older credits."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import repair_hesychius_missing_columns as repair

ROOT = Path(__file__).resolve().parents[1]


def metadata(root=ROOT):
    root = Path(root)
    if not repair.active(root):
        return None
    from hesychius_gap_observations import SOURCES, BOUNDARY
    audit, _, rows = repair.checked_state(root)
    return {"authority": {"path": repair.AUTHORITY,
            "sha256": repair.sha((root / repair.AUTHORITY).read_bytes())},
        "counts": deepcopy(audit["counts"]), "sources": deepcopy(SOURCES),
        "boundary": deepcopy(BOUNDARY), "qualification": repair.QUALIFICATION,
        "primary": {"path": repair.PRIMARY, "sha256": audit["outputs"][repair.PRIMARY],
                    "loci": [row["locus"] for row in rows.values()] if isinstance(rows, dict)
                            else [row["locus"] for row in rows]},
        "literal_witnesses": {"path": repair.WITNESSES,
            "sha256": audit["outputs"][repair.WITNESSES],
            "counts_toward_primary_frequency": False}}


def register(registry, root=ROOT):
    value = metadata(root)
    if value is None:
        return None
    if repair.SLUG not in registry.works:
        raise ValueError("Recovered Hesychius columns lack their canonical Work")
    work = registry.works[repair.SLUG]
    previous_default = work.default_edition
    key = registry.mint_edition(repair.SLUG, repair.EDITION,
        "Schmidt 1867, recovered main-text columns 259–260")
    edition = work.editions[key]
    edition.provider, edition.license = "ocr", "PD"
    edition.editor, edition.year = "Schmidt, Moritz", 1867
    edition.source = value["sources"]["harvard"]["url"]
    edition.scheme, edition.storage, edition.servable = "printed-column", "primary", True
    edition.note = value["qualification"]
    work.default_edition = previous_default
    composition = deepcopy(work.coverage_composition)
    composition["missing_columns_recovery"] = deepcopy(value)
    work.coverage_composition = composition
    return value
