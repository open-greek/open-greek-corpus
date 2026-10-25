"""A later-edition adoption never becomes a scan-confirmed OCR vote."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import adopt_hesychius_latte_reading as adoption
import hesychius_gap_state as state
import repair_hesychius_gap_readings as review


@pytest.fixture
def adopted(tmp_path):
    for name in state.authority_paths(ROOT):
        if (ROOT / name).is_file():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
    return tmp_path


def test_adoption_keeps_votes_and_schmidt_uncertainty_separate(adopted):
    audit, predecessor, rows = adoption.checked_state(adopted)
    assert audit["counts"]["analysis_greek_tokens"] == 252
    assert audit["counts"]["editorial_adoption"] == {"adopted_lexical_slots": 1, "unverified_schmidt_slots": 1}
    assert audit["counts"]["reading_statuses"].get("unresolved", 0) == 0
    record, = audit["changes"]
    assert record["corrected_text"] == "ἀΐαχοι"
    assert record["source"]["entry"] == 8275
    assert record["source"]["consulted_on"] == "2026-10-25"
    assert record["recorded_at"] == audit["recorded_at"]
    assert record["schmidt_reading_confirmed"] is False
    assert record["original_slot"]["source_review"]["decision"] == "held"
    original = json.loads(gzip.decompress((adopted / review.NETWORKS).read_bytes()))[adoption.KEY]
    current = json.loads(gzip.decompress((adopted / adoption.NETWORKS).read_bytes()))[adoption.KEY]
    for before, after in zip(original["ocr_consensus"]["slots"], current["ocr_consensus"]["slots"]):
        if before["position"] == adoption.POSITION:
            assert after["readings"] == before["readings"]
            assert after["vote_status"] == before["vote_status"] == "unresolved"
            assert after["source_review"] == before["source_review"]
            assert after["status"] == "editorially-adopted" and after["lexical_eligible"]
        else:
            assert before == after
    before_lines = predecessor.splitlines(keepends=True)
    after_lines = (adopted / adoption.PRIMARY).read_bytes().splitlines(keepends=True)
    assert len(before_lines) == len(after_lines) == 32120
    assert sum(left != right for left, right in zip(before_lines, after_lines)) == 1
    for row in rows.values():
        assert state.validate_projection(row, adopted) == row["analysis_text"]
        assert state.lexical_segments(row, adopted) == []


def test_exact_undo_reapply_and_frozen_prior_review(adopted):
    audit, predecessor = adoption.verify(adopted)
    frozen = (adopted / adoption.AUTHORITY).read_bytes()
    old_audit = (adopted / review.AUTHORITY).read_bytes()
    adoption.undo(adopted)
    assert not adoption.active(adopted)
    assert (adopted / adoption.PRIMARY).read_bytes() == predecessor
    assert review.verify(adopted)[0]["counts"]["analysis_greek_tokens"] == 251
    adoption.apply(adopted)
    assert (adopted / adoption.AUTHORITY).read_bytes() == frozen
    assert (adopted / review.AUTHORITY).read_bytes() == old_audit
    assert adoption.verify(adopted)[0] == audit


def test_invalidated_source_blocks_counts_but_not_exact_reversal(adopted):
    import build_work_lemma_counts as counts
    from unittest.mock import patch
    with patch.object(counts, "DATA", adopted / "data"), patch.object(counts, "MANIFEST", adopted / "cache.json"), patch.object(counts, "WORK_FORMS", adopted / "forms"):
        files = [adopted / adoption.PRIMARY]
        expected = counts.load_work_forms(files, use_cache=True)
        assert counts.load_work_forms(files, use_cache=True) == expected
        (adopted / review.base.AUDIT / "source-evidence/ghent-column-259.png").unlink()
        with pytest.raises((ValueError, FileNotFoundError)):
            counts.load_work_forms(files, use_cache=True)
        adoption.undo(adopted)
        assert review.base.sha((adopted / adoption.PRIMARY).read_bytes()) == adoption.PREDECESSOR_SHA256


def test_rehashed_postimage_cannot_forge_an_adoption(adopted):
    path = adopted / adoption.PRIMARY
    rows = [json.loads(raw) for raw in path.read_bytes().splitlines()]
    next(row for row in rows if row.get("hesychius_latte_adoption"))["analysis_text"] += " πλαστόν"
    path.write_bytes(review.base.jsonl(rows))
    path = adopted / adoption.AUTHORITY
    audit = json.loads(path.read_bytes())
    audit["outputs"][adoption.PRIMARY] = review.base.sha((adopted / adoption.PRIMARY).read_bytes())
    path.write_bytes(review.base.encode(audit))
    with pytest.raises(ValueError, match="source replay differs"):
        state.current_metadata(adopted)


def test_changed_citation_recipe_and_stripped_marker_fail_closed(adopted):
    row = next(row for row in adoption.checked_state(adopted)[2].values() if row.get("hesychius_latte_adoption"))
    altered = deepcopy(row)
    altered.pop("hesychius_latte_adoption")
    with pytest.raises(ValueError, match="lexical projection differs"):
        state.validate_projection(altered, adopted)
    path = adopted / "scripts/adopt_hesychius_latte_reading.py"
    path.write_bytes(path.read_bytes() + b"\n# changed citation or reading\n")
    with pytest.raises(ValueError, match="recipe changed"):
        state.current_metadata(adopted)
    adoption.undo(adopted)


def test_quality_keeps_the_unverified_schmidt_reading_visible(adopted):
    import source_recovery_quality as quality
    reading = quality.measurement(adopted)["hesychius_missing_columns"]
    assert reading["remaining_reading_uncertainty"]["total_slots_excluded"] == 0
    assert reading["remaining_reading_uncertainty"]["unverified_schmidt_slots"] == 1
    assert reading["editorial_adoption"]["source"]["reading"] == "ἀΐαχοι"
    assert reading["editorial_adoption"]["schmidt_reading_confirmed"] is False
    limitation, = quality.limitations(adopted)
    assert "explicitly adopted" in limitation["why_no_bulk_action_remains"]
