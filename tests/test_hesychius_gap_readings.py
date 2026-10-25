"""Reading admission, source replay, and exact reversal of the 45-slot review."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_hesychius_gap_readings as review
import hesychius_gap_state as state
import repair_hesychius_missing_columns as original


@pytest.fixture
def reviewed(tmp_path):
    for name in state.authority_paths(ROOT):
        if (ROOT / name).is_file():
            destination = tmp_path / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
    import adopt_hesychius_latte_reading as adoption
    if adoption.active(tmp_path):
        adoption.undo(tmp_path)
        (tmp_path / adoption.AUTHORITY).unlink()
        (tmp_path / adoption.PREIMAGE).unlink()
    return tmp_path


def test_complete_campaign_preserves_votes_and_excluded_roles(reviewed):
    audit, before, rows = review.checked_state(reviewed)
    assert audit["counts"]["reading_review"] == {
        "initial_uncertain_slots": 45, "remaining_uncertain_slots": 1,
        "merged_fragment_slots": 2, "newly_admitted_lexical_slots": 42,
        "shared_errors_corrected": 16}
    assert audit["counts"]["analysis_greek_tokens"] == 251
    old = json.loads(gzip.decompress((reviewed / original.NETWORKS).read_bytes()))
    new = json.loads(gzip.decompress((reviewed / review.NETWORKS).read_bytes()))
    records = [json.loads(line) for line in gzip.decompress((reviewed / review.RECORDS).read_bytes()).splitlines()]
    assert len(records) == 61
    assert sum(r["category"] == "uncertain" for r in records) == 45
    for key, previous in old.items():
        current = new[key]
        assert len(previous["ocr_consensus"]["slots"]) == len(current["ocr_consensus"]["slots"])
        assert current["ocr_consensus"]["witnesses"] == previous["ocr_consensus"]["witnesses"]
        for left, right in zip(previous["ocr_consensus"]["slots"], current["ocr_consensus"]["slots"]):
            assert left["readings"] == right["readings"]
            assert left["omission_support"] == right["omission_support"]
            assert left["vote_status"] == right["vote_status"]
            if "source_review" not in right:
                assert left == right
    for record in records:
        assert record["original_text"]
        assert record["recorded_at"] == audit["recorded_at"]
        assert len(record["source_evidence"]) == 2
        assert {Path(e["path"]).name.split("-")[0] for e in record["source_evidence"]} == {"harvard", "ghent"}
        assert all(len(e["sha256"]) == 64 for e in record["source_evidence"])
        assert record["comparison"]["work"] == "4085.002"
    old_rows = before[review.PRIMARY].splitlines(keepends=True)
    new_rows = (reviewed / review.PRIMARY).read_bytes().splitlines(keepends=True)
    assert len(new_rows) == len(old_rows)
    assert sum(a != b for a, b in zip(old_rows, new_rows)) == 2
    for row in rows.values():
        assert state.validate_projection(row, reviewed) == row["analysis_text"]
        assert state.lexical_segments(row, reviewed) == []


def test_fragments_are_joined_once_and_schmidt_differences_survive(reviewed):
    _, _, rows = review.checked_state(reviewed)
    networks = json.loads(gzip.decompress((reviewed / review.NETWORKS).read_bytes()))
    left = networks["schmidt-1867.column-259"]["ocr_consensus"]["slots"]
    right = networks["schmidt-1867.column-260"]["ocr_consensus"]["slots"]
    assert left[29]["selected"] == "" and left[30]["selected"] == "αὐθίξας"
    assert right[49]["selected"] == "" and right[50]["selected"] == "ἐλαυνομένων"
    assert right[9]["selected"] == "σπεῖραν"
    assert left[121]["selected"] == "διῶρυξ"
    assert left[84]["selected"] is None and not left[84]["lexical_eligible"]
    assert right[119]["selected"] == "αὐλώνων"
    assert rows[(original.SLUG, "schmidt-1867.column-260")]["analysis_text"].endswith("διάγουσα αὐλώνων")


def test_exact_undo_reapply_and_source_independent_reversal(reviewed):
    audit, before = review.verify(reviewed)
    frozen = (reviewed / review.AUTHORITY).read_bytes()
    review.undo(reviewed)
    assert not review.active(reviewed)
    assert (reviewed / review.PRIMARY).read_bytes() == before[review.PRIMARY]
    assert original.verify(reviewed)[0]["counts"]["analysis_greek_tokens"] == 209
    review.apply(reviewed)
    assert (reviewed / review.AUTHORITY).read_bytes() == frozen
    assert {name: original.sha((reviewed / name).read_bytes()) for name in review.OUTPUTS} == audit["outputs"]
    evidence = reviewed / original.AUDIT / "source-evidence/harvard-column-259.png"
    evidence.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        state.current_metadata(reviewed)
    review.undo(reviewed)
    assert (reviewed / review.PRIMARY).read_bytes() == before[review.PRIMARY]


def test_tampered_source_or_recipe_invalidates_cached_projection(reviewed):
    row = next(iter(review.checked_state(reviewed)[2].values()))
    state.validate_projection(row, reviewed)
    path = reviewed / "scripts/hesychius_gap_reading_observations.py"
    path.write_bytes(path.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError, match="recipe changed"):
        state.validate_projection(row, reviewed)
    review.undo(reviewed)


def test_rehashed_outputs_cannot_forge_reviewed_readings(reviewed):
    review.checked_state(reviewed)
    path = reviewed / review.PRIMARY
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    next(r for r in rows if r.get("hesychius_gap_reading_review"))["analysis_text"] += " πλαστόν"
    path.write_bytes(original.jsonl(rows))
    path = reviewed / review.AUTHORITY
    audit = json.loads(path.read_bytes())
    audit["outputs"][review.PRIMARY] = original.sha((reviewed / review.PRIMARY).read_bytes())
    path.write_bytes(original.encode(audit))
    with pytest.raises(ValueError, match="source replay differs"):
        state.current_metadata(reviewed)


def test_stripped_marker_or_changed_row_cannot_bypass_projection(reviewed):
    row = next(iter(review.checked_state(reviewed)[2].values()))
    for change in (lambda r: r.pop("hesychius_gap_reading_review"),
                   lambda r: r.update(analysis_text="πλαστόν")):
        altered = deepcopy(row)
        change(altered)
        with pytest.raises(ValueError, match="lexical projection differs"):
            state.validate_projection(altered, reviewed)


def test_unowned_base_output_is_still_checked(reviewed):
    review.checked_state(reviewed)
    path = reviewed / original.WITNESSES
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="recovery output changed"):
        state.current_metadata(reviewed)


def test_cached_word_counts_cannot_bypass_invalidated_scan(reviewed, monkeypatch):
    import build_work_lemma_counts as counts
    import frequency_projection as projection
    # This fixture deliberately exercises the frozen pre-adoption review.
    # Its rows must be checked against that fixture rather than the live corpus.
    live_text = projection.lexical_text
    monkeypatch.setattr(projection, "lexical_text", lambda row:
        state.validate_projection(row, reviewed) if row.get("hesychius_gap_recovery") else live_text(row))
    monkeypatch.setattr(counts, "DATA", reviewed / "data")
    monkeypatch.setattr(counts, "MANIFEST", reviewed / "counter-manifest.json")
    monkeypatch.setattr(counts, "WORK_FORMS", reviewed / "counter-cache")
    files = [reviewed / review.PRIMARY]
    expected = counts.load_work_forms(files, use_cache=True)
    assert counts.load_work_forms(files, use_cache=True) == expected
    (reviewed / original.AUDIT / "source-evidence/ghent-column-259.png").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        counts.load_work_forms(files, use_cache=True)
