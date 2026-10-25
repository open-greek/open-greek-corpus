"""Release measurements come from active, checked source authorities."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import source_recovery_quality as quality
import repair_hesychius_missing_columns as hesychius
import repair_pindar_duplicate_primaries as pindar


@pytest.fixture
def sources(tmp_path):
    for repair in (hesychius, pindar):
        authority = repair.AUDIT + "/changes.json"
        audit = json.loads((ROOT / authority).read_bytes())
        names = {authority, repair.AUDIT + "/before.json.gz",
            *(name for name, pin in audit["outputs"].items() if pin is not None),
            *("scripts/" + name for name in audit["recipe_sha256"])}
        names.update(audit.get("source_sha256", {}))
        for name in names:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if repair is hesychius and name == hesychius.PRIMARY:
                from hesychius_gap_state import recovery_postimage_bytes
                path.write_bytes(recovery_postimage_bytes(ROOT))
            else:
                shutil.copyfile(ROOT / name, path)
    return tmp_path


def test_absent_measurements_are_absent_not_zero(tmp_path):
    assert quality.measurement(tmp_path) is None
    assert quality.limitations(tmp_path) == []


def test_real_current_measurements_replay_their_source_authorities():
    current = quality.measurement(ROOT)
    assert current["schema_version"] == 1
    reading = current["hesychius_missing_columns"]
    from hesychius_gap_state import current_metadata
    metadata = current_metadata(ROOT)
    assert reading["counts"] == metadata["counts"]
    assert reading["recovered_printed_columns"] == [259, 260]
    assert reading["repair_status"] == "missing-main-text-leaf-recovered"
    assert reading["counts"]["analysis_greek_tokens"] == 252
    assert reading["remaining_reading_uncertainty"] == {
        "unresolved_alignment_slots": 0, "single_checkpoint_slots_excluded": 0,
        "total_slots_excluded": 0, "editorially_adopted_slots": 1, "unverified_schmidt_slots": 1,
        "count_basis": "Unresolved exact-word alignment slots and singly supported readings in the "
            "two recovered main-text columns. These are not OCR error counts or an error rate."}
    assert reading["authority"]["sha256"] == hesychius.sha((ROOT / metadata["authority"]).read_bytes())
    exact = current["pindar_duplicate_primaries"]
    assert exact["counts"] == pindar.verify(ROOT)[0]["counts"]
    assert exact["counts"]["pairs"] == 4
    assert exact["counts"]["duplicate_analysis_tokens_removed"] == 1445
    import repair_westermann_scope as westermann
    if westermann.active(ROOT):
        scope = current["westermann_source_scope"]
        audited_counts = westermann.checked_state(ROOT)[0]["counts"]
        assert all(scope["counts"][key] == value for key, value in audited_counts.items())
        assert scope["counts"]["original_rows"] == 7013
        assert scope["counts"]["primary_works"] > 1
        assert scope["counts"]["literal_rows"] == 7013
        assert scope["counts"]["held_rows"] >= 0
    else:
        assert "westermann_source_scope" not in current


def test_only_residual_readings_create_a_limitation(sources):
    result = quality.limitations(sources)
    assert len(result) == 1
    row = result[0]
    assert row["key"] == "hesychius-recovered-columns-reading-uncertainty"
    assert row["current_measurement"]["repair_status"] == "missing-main-text-leaf-recovered"
    assert row["current_measurement"]["remaining_reading_uncertainty"]["total_slots_excluded"] == 45
    assert "not OCR error counts or an error rate" in row["current_measurement"]["remaining_reading_uncertainty"]["count_basis"]
    assert "occurrence" in row["reopen_when"]
    assert "missing-leaf defect only if" in row["reopen_when"]
    assert row["status"] == "accepted-measured-limitation"


def test_returned_measurements_cannot_mutate_the_verified_cache(sources):
    first = quality.measurement(sources)
    first["hesychius_missing_columns"]["counts"]["analysis_greek_tokens"] = -1
    first["pindar_duplicate_primaries"]["counts"]["pairs"] = -1
    fresh = quality.measurement(sources)
    assert fresh["hesychius_missing_columns"]["counts"]["analysis_greek_tokens"] == 209
    assert fresh["pindar_duplicate_primaries"]["counts"]["pairs"] == 4


def test_changed_evidence_invalidates_existing_measurements(sources):
    quality.measurement(sources)
    path = sources / hesychius.AUDIT / "source-evidence/ghent-column-259.png"
    path.write_bytes(path.read_bytes() + b"invalidated")
    with pytest.raises(ValueError, match="source evidence changed"):
        quality.measurement(sources)
    with pytest.raises(ValueError, match="source evidence changed"):
        quality.limitations(sources)


def test_changed_duplicate_postimage_is_rejected(sources):
    quality.measurement(sources)
    pair = pindar.PAIRS[0]
    path = sources / pindar.primary(pair["canonical"])
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="neither fully active nor exactly unapplied"):
        quality.measurement(sources)


def test_partial_authority_is_not_treated_as_absent(tmp_path):
    path = tmp_path / hesychius.AUTHORITY
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ValueError, match="Orphaned Hesychius"):
        quality.measurement(tmp_path)


def test_undo_removes_only_its_measurement_and_reading_limitation(sources):
    hesychius.undo(sources)
    current = quality.measurement(sources)
    assert "hesychius_missing_columns" not in current
    assert current["pindar_duplicate_primaries"]["counts"]["pairs"] == 4
    assert quality.limitations(sources) == []
