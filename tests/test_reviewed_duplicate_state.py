"""The later missing-leaf authority must preserve every frozen duplicate gate."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import repair_reviewed_duplicate_blocks as old
import repair_hesychius_missing_columns as recovery
import reviewed_duplicate_state as state
import hesychius_gap_manifestations as credits
from source_identity import Registry


@pytest.fixture
def layers(tmp_path):
    audit_path = old.AUDIT + "/changes.json"
    audit = json.loads((ROOT / audit_path).read_bytes())
    capture = json.loads((ROOT / old.AUDIT / "source-evidence.json").read_bytes())
    names = {audit_path, old.AUDIT + "/before.json.gz", old.AUDIT + "/source-evidence.json",
        *audit["inputs"], *audit["outputs"], *(row["path"] for row in capture["files"]),
        *("scripts/" + name for name in audit["recipe_sha256"])}
    capture = json.loads((ROOT / recovery.AUDIT / "source-evidence.json").read_bytes())
    names.update({recovery.AUDIT + "/source-evidence.json", *recovery.OCR_FILES,
        *(row["path"] for row in [*capture["images"], *capture["columns"]]),
        *("scripts/" + name for name in recovery.recipe_pins()),
        "scripts/reviewed_duplicate_state.py", "scripts/hesychius_gap_manifestations.py"})
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name in audit["outputs"]:
            path.write_bytes(state.duplicate_postimage_bytes(ROOT, name))
        else:
            shutil.copyfile(ROOT / name, path)
    recovery.apply(tmp_path, recorded_at="2026-10-24T00:00:00+00:00")
    return tmp_path


def registry():
    result = Registry()
    author = recovery.SLUG.split(".")[0]
    result.mint_author("Hesychius", slug=author)
    result.mint_work(author, "Existing canonical title", slug=recovery.SLUG)
    result.mint_edition(recovery.SLUG, "qwen36-hesychius_schmidt_masked", "Existing base edition",
        provider="ocr", license="PD", source="https://example.org/existing", make_default=True)
    result.mint_edition(recovery.SLUG, old.EDITION, "Existing duplicate-reviewed edition",
        provider="ocr", license="PD", source="https://archive.org/details/hesychiialexand00schmgoog")
    result.works[recovery.SLUG].coverage_composition = {
        "policy": "existing coverage policy", "components": [{"edition": "existing", "passages": 32118}],
        "later_duplicate_review": {"counts": {"primary_rows": 1, "literal_witness_rows": 111}},
        "unrelated": {"retain": [1, 2, 3]}}
    return result


def test_frozen_predecessor_and_historical_bytes_are_fully_verified(layers):
    audit, original_before = state.verify(layers)
    assert audit == json.loads((ROOT / old.AUDIT / "changes.json").read_bytes())
    assert state.active(layers)
    new_before = recovery.predecessor_bytes(layers)
    assert state.duplicate_postimage_bytes(layers, recovery.PRIMARY) == new_before
    assert old.sha(new_before) == audit["outputs"][recovery.PRIMARY]
    for name in old.PRIMARY:
        assert state.historical_bytes(layers, name) == original_before[name]
        assert old.sha(original_before[name]) == old.INPUTS[name]
    assert state.historical_bytes(layers, "data/corpus/not-owned.jsonl") is None
    with pytest.raises(ValueError, match="does not own"):
        state.duplicate_postimage_bytes(layers, "data/corpus/not-owned.jsonl")
    for name in old.PRIMARY:
        for row in map(json.loads, (layers / name).read_bytes().splitlines()):
            if row.get("edition") == old.EDITION:
                assert state.validate_projection(row, layers) == row["analysis_text"]
                changed = dict(row, analysis_text=row["analysis_text"] + " πλαστόν")
                with pytest.raises(ValueError, match="lexical projection differs"):
                    state.validate_projection(changed, layers)


@pytest.mark.parametrize("authority", ["old", "new"])
def test_changed_evidence_invalidates_cached_predecessor(layers, authority):
    state.verify(layers)
    if authority == "old":
        capture = json.loads((layers / old.AUDIT / "source-evidence.json").read_bytes())
        path = layers / capture["files"][-1]["path"]
    else:
        path = layers / recovery.AUDIT / "source-evidence/ghent-column-259.png"
    path.write_bytes(path.read_bytes() + b"invalidated")
    with pytest.raises(ValueError, match="source evidence"):
        state.verify(layers)


def test_unowned_cyril_postimage_is_never_overlaid_or_waived(layers):
    state.verify(layers)
    path = layers / old.PRIMARY[0]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="duplicate output changed"):
        state.verify(layers)


def test_jointly_rehashed_later_output_still_needs_source_replay(layers):
    state.verify(layers)
    path = layers / recovery.PRIMARY
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    next(row for row in rows if row.get("edition") == recovery.EDITION)["analysis_text"] += " πλαστόν"
    path.write_bytes(recovery.jsonl(rows))
    audit_path = layers / recovery.AUTHORITY
    audit = json.loads(audit_path.read_bytes())
    audit["outputs"][recovery.PRIMARY] = recovery.sha(path.read_bytes())
    audit_path.write_bytes(recovery.encode(audit))
    with pytest.raises(ValueError, match="source replay differs"):
        state.verify(layers)


def test_registry_addition_retains_existing_credits_default_and_composition(layers):
    reg = registry()
    work = reg.works[recovery.SLUG]
    before = asdict(work)
    value = credits.register(reg, layers)
    assert work.default_edition == before["default_edition"]
    assert work.title == before["title"] and work.best_source == before["best_source"]
    assert {key: asdict(work.editions[key]) for key in before["editions"]} == before["editions"]
    assert {key: work.coverage_composition[key] for key in before["coverage_composition"]} == before["coverage_composition"]
    assert len(work.editions) == len(before["editions"]) + 1
    assert work.coverage_composition["missing_columns_recovery"] == value
    assert value["counts"]["primary_columns_added"] == 2
    assert value["counts"]["analysis_greek_tokens"] == 209
    assert set(value["sources"]) == {"harvard", "ghent"}
    assert value["primary"]["loci"] == ["schmidt-1867.column-259", "schmidt-1867.column-260"]
    assert value["primary"]["sha256"] == recovery.sha((layers / recovery.PRIMARY).read_bytes())
    assert value["literal_witnesses"]["path"] == recovery.WITNESSES
    assert value["literal_witnesses"]["counts_toward_primary_frequency"] is False
    edition = work.editions[recovery.SLUG + "." + recovery.EDITION]
    assert (edition.provider, edition.license, edition.year, edition.storage, edition.servable) == ("ocr", "PD", 1867, "primary", True)
    assert edition.source == "https://archive.org/details/bub_gb_R-zVabafOucC"


def test_registry_round_trip_is_idempotent_and_empty_default_is_preserved(layers):
    reg = registry()
    reg.works[recovery.SLUG].default_edition = None
    credits.register(reg, layers)
    assert reg.works[recovery.SLUG].default_edition is None
    path = layers / "registry.json"
    reg.save(path)
    before = path.read_bytes()
    reg = Registry.load(path)
    credits.register(reg, layers)
    reg.save(path)
    assert path.read_bytes() == before


def test_invalidated_evidence_cannot_mutate_registry(layers):
    reg = registry()
    credits.metadata(layers)
    before = deepcopy(reg.works)
    path = layers / recovery.AUDIT / "source-evidence/harvard-column-260.png"
    path.write_bytes(path.read_bytes() + b"invalidated")
    with pytest.raises(ValueError, match="source evidence"):
        credits.register(reg, layers)
    assert reg.works == before


def test_undone_or_absent_recovery_has_no_registry_side_effects(layers, tmp_path):
    recovery.undo(layers)
    reg = registry()
    before = deepcopy(reg.works)
    assert credits.register(reg, layers) is None
    assert credits.register(reg, tmp_path / "absent") is None
    assert reg.works == before


def test_missing_canonical_work_is_rejected_before_mutation(layers):
    reg = Registry()
    with pytest.raises(ValueError, match="canonical Work"):
        credits.register(reg, layers)
    assert not reg.works and not reg.authors
