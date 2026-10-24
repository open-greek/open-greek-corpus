"""The Dübner scope repair preserves literal evidence and checked countability."""
import gzip
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dubner_source_observations as observations
import frequency_projection
import repair_dubner_scholias as repair
from ocr_consensus import compact_corpus_consensus, restore_corpus_consensus


@pytest.fixture(scope="module")
def frozen_scope():
    before = repair.archived_inputs(ROOT)
    authority = ROOT / repair.AUDIT / "changes.json"
    recorded_at = json.loads(authority.read_bytes())["recorded_at"] if authority.exists() else "2026-10-24T00:00:00+00:00"
    records = repair.source_records(ROOT, before)
    partitions = repair.partitions(records)
    outputs, works, counts = repair.build(ROOT, before, recorded_at=recorded_at)
    changes = [json.loads(line) for line in gzip.decompress(outputs[repair.RECORDS]).splitlines()]
    networks = json.loads(gzip.decompress(outputs[repair.NETWORKS]))
    return {"before": before, "records": records, "partitions": partitions,
            "outputs": outputs, "works": works, "counts": counts,
            "changes": changes, "networks": networks, "recorded_at": recorded_at}


def jsonl(raw):
    return [json.loads(line) for line in raw.splitlines() if line]


def retained_admission(destination):
    """Copy the frozen authority and postimages without rerunning collation."""
    authority = ROOT / repair.AUDIT / "changes.json"
    if not authority.exists():
        pytest.skip("The source repair has not been applied yet")
    audit = json.loads(authority.read_bytes())
    capture = json.loads((ROOT / repair.AUDIT / "source-evidence.json").read_bytes())
    names = set(audit["outputs"]) | {
        repair.AUDIT + "/changes.json", repair.AUDIT + "/before.json.gz",
        repair.AUDIT + "/source-evidence.json"}
    names.update(item["path"] for item in capture["files"])
    for name in names:
        source = ROOT / name
        if source.is_file():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return audit, capture


def assert_exactly_unapplied(root, audit, before):
    for name in audit["outputs"]:
        path = root / name
        assert (path.read_bytes() if path.exists() else None) == before.get(name)


def test_all_literal_rows_and_characters_have_reversible_source_roles(frozen_scope):
    data = frozen_scope
    originals = {(r["path"], r["row"]["locus"]): r for r in data["records"] if not r["derived"]}
    assert len(originals) == 45380 == data["counts"]["original_rows"]
    assert len(data["changes"]) == len(originals)
    routed = {path: {row["locus"]: row for row in jsonl(raw)}
              for path, raw in data["outputs"].items() if raw is not None and path.endswith(".jsonl")}
    for change in data["changes"]:
        record = originals[(change["input"], change["original_row"]["locus"])]
        row = record["row"]
        assert change["original_row"] == row
        assert change["original_text"] == change["corrected_text"] == row["text"]
        cursor = 0
        for part, destination in zip(change["source_partitions"], change["destinations"], strict=True):
            assert part["start"] == cursor
            cursor = part["end"]
            assert routed[destination["path"]][destination["locus"]]["text"] == row["text"][part["start"]:cursor]
        assert cursor == len(row["text"])
    assert data["counts"]["constructed_fallback_rows"] == 476


def test_headings_apparatus_and_indexes_cannot_enter_historical_counting_lanes(frozen_scope):
    data = frozen_scope
    excluded_heading_ids = set()
    for record in data["records"]:
        kind = "toronto" if record["group"].endswith("toronto") else "harvard"
        if record["row"]["locus"] in observations.PLAY_HEADING_LOCI[kind]:
            parts = data["partitions"][record["id"]]
            assert all(not part["lexical_eligible"] and part["role"] == "edition-heading" for part in parts)
            excluded_heading_ids.add(record["id"])
    assert excluded_heading_ids
    lane_rows = set()
    for network in data["networks"].values():
        for witness in network["ocr_consensus"]["witnesses"]:
            lane_rows.update(witness["source_rows"])
    assert excluded_heading_ids.isdisjoint(lane_rows)
    for record in data["records"]:
        page = record["toronto_page"]
        if page is not None and page >= 431:
            assert record["id"] not in lane_rows


def test_overlapping_front_text_is_retained_as_historical_comparative_evidence(frozen_scope):
    data = frozen_scope
    comparative = jsonl(data["outputs"][repair.COMPARATIVE])
    assert comparative
    assert {row["admission"]["admission"] for row in comparative} == {"comparative", "secondary"}
    assert all(row["class"] == "comparative-historical-witness" and row["lang"] == "grc" for row in comparative)
    assert any(row["source_work_key"] == "platonius" for row in comparative)
    assert any(row["admission"].get("target") == "suda.lexicon" for row in comparative)
    assert any(row["admission"].get("target") == "anthologia-graeca.anthologia-graeca" for row in comparative)
    assert f"data/corpus/{repair.B}.jsonl" not in data["outputs"] or data["outputs"][f"data/corpus/{repair.B}.jsonl"] is None
    assert repair.B not in data["works"]


def test_scan_omissions_never_invent_an_independent_reading(frozen_scope):
    data = frozen_scope
    # Harvard is missing the last Frogs and first Assemblywomen source pages.
    for key in ("ranae:0356", "ecclesiazusae:0357"):
        network = data["networks"][key]["ocr_consensus"]
        assert {w["vote_group"] for w in network["witnesses"]} == {"dubner-1855-toronto"}
        assert not any(slot["status"] == "agreement" for slot in network["slots"])
    for result in data["networks"].values():
        network = result["ocr_consensus"]
        for slot in network["slots"]:
            selected = slot["selected"]
            assert selected is None or selected == "" or selected in {reading["text"] for reading in slot["readings"]}
        assert result["analysis_text"] == " ".join(slot["selected"] for slot in network["slots"] if slot["lexical_eligible"])


def test_repeated_leaves_and_constructed_alternatives_cannot_overweight_a_scan(frozen_scope):
    many_lanes = 0
    for result in frozen_scope["networks"].values():
        network = result["ocr_consensus"]
        many_lanes += len(network["witnesses"]) > 2
        groups = {w["vote_group"] for w in network["witnesses"]}
        assert groups <= {"dubner-1855-toronto", "dubner-1855-harvard"}
        for slot in network["slots"]:
            for reading in slot["readings"]:
                assert len(reading["support_groups"]) <= 2
                assert set(reading["support_groups"]) <= groups
                assert len(reading["support_groups"]) == len(set(reading["support_groups"]))
    assert many_lanes


def test_ties_survive_both_full_and_compact_archives_and_supply_no_scalar_tokens(frozen_scope):
    unresolved = 0
    for key, result in frozen_scope["networks"].items():
        compact = compact_corpus_consensus(result, {"path": repair.NETWORKS, "key": key})
        assert restore_corpus_consensus(compact, result) == result
        for full, short in zip(result["ocr_consensus"]["slots"], compact["ocr_consensus"]["slots"], strict=True):
            if full["status"] == "unresolved":
                unresolved += 1
                assert full["selected"] is None
                assert full["lexical_eligible"] is False
                assert len(full["tied_readings"]) >= 2
                assert short["tied_readings"] == full["tied_readings"]
    assert unresolved


@pytest.mark.parametrize("row", [
    {"text": "λόγος", "analysis_text": "forged", "dubner_scope_review": {}},
    {"text": "λόγος", "analysis_text": "forged", "dubner_scope_review": False},
    {"text": "λόγος", "analysis_text": "forged", "edition": "dubner-1855-collated"},
])
def test_frequency_projection_cannot_bypass_checked_admission_with_generic_analysis_text(row):
    with patch.object(repair, "validate_projection", side_effect=ValueError("checked admission")) as checked:
        with pytest.raises(ValueError, match="checked admission"):
            frequency_projection.lexical_text(row)
        checked.assert_called_once_with(row)


@pytest.mark.parametrize("marker", [{"dubner_scope_review": {}}, {"dubner_scope_review": False},
    {"edition": "dubner-1855-collated"}])
def test_page_word_projection_supplies_no_adjacency_after_source_role_filtering(tmp_path, marker):
    row = {"urn": "work", "locus": "1", "text": "λόγος ἄλλος", "analysis_text": "λόγος ἄλλος",
        "ocr_consensus": {"slots": [
            {"selected": "λόγος", "lexical_eligible": True},
            {"selected": "ἄλλος", "lexical_eligible": True}]}, **marker}
    projection = frequency_projection.FrequencyProjection(tmp_path / "data")
    with patch.object(repair, "validate_projection", return_value=row["analysis_text"]) as checked:
        assert projection.segments(row) == []
        checked.assert_called_once_with(row)
        assert projection.contextual_text(row) is None


def test_frequency_recipe_pins_every_dubner_admission_layer():
    pins = frequency_projection.projection_recipe_pins()
    assert {"repair_dubner_scholias.py", "dubner_source_observations.py",
            "dubner_witness_alignment.py", "dubner_dedup_observations.py",
            "capture_dubner_sources.py"}.issubset(pins)
    assert all(len(pins[name]) == 64 for name in pins if "dubner" in name)


def test_active_data_replays_from_originals(frozen_scope):
    if not (ROOT / repair.AUDIT / "changes.json").exists():
        pytest.skip("The source repair has not been applied yet")
    audit, _ = repair.verify(ROOT, replay=True)
    assert audit["works"] == frozen_scope["works"]
    assert audit["counts"] == frozen_scope["counts"]



def test_active_frequency_rows_reject_tampered_or_missing_admission(frozen_scope):
    if not (ROOT / repair.AUDIT / "changes.json").exists():
        pytest.skip("The source repair has not been applied yet")
    raw = next(raw for name, raw in frozen_scope["outputs"].items()
               if name.startswith("data/corpus/") and raw is not None)
    row = jsonl(raw)[0]
    assert frequency_projection.lexical_text(row) == row["analysis_text"]
    changed = dict(row, analysis_text=row["analysis_text"] + " πλαστός")
    with pytest.raises(ValueError, match="checked admission"):
        frequency_projection.lexical_text(changed)
    stripped = dict(row)
    stripped.pop("dubner_scope_review")
    with pytest.raises(ValueError, match="checked admission"):
        frequency_projection.lexical_text(stripped)


def test_literal_undo_and_reapply_survive_lost_evidence(frozen_scope, tmp_path):
    data = frozen_scope
    audit, capture = retained_admission(tmp_path)
    authority = tmp_path / repair.AUDIT / "changes.json"
    original_authority = authority.read_bytes()
    repair.verify(tmp_path)
    damaged = tmp_path / capture["files"][0]["path"]
    saved = damaged.read_bytes()
    damaged.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        repair.verify(tmp_path)
    repair.undo(tmp_path)  # Evidence loss must not prevent literal recovery.
    assert_exactly_unapplied(tmp_path, audit, data["before"])
    damaged.write_bytes(saved)
    # The module-wide build has already independently checked all collation.
    # Exercise writing and ownership checks without repeating the full alignment.
    with patch.object(repair, "build", return_value=(data["outputs"], data["works"], data["counts"])):
        repair.apply(tmp_path, recorded_at=data["recorded_at"])
    repair.verify(tmp_path)
    assert authority.read_bytes() == original_authority
    for name, expected in audit["outputs"].items():
        path = tmp_path / name
        assert (repair.sha(path.read_bytes()) if path.exists() else None) == expected


def test_partial_undo_cannot_hide_a_remaining_new_primary(frozen_scope, tmp_path):
    data = frozen_scope
    audit, _ = retained_admission(tmp_path)
    repair.undo(tmp_path)
    assert not repair.active(tmp_path)
    candidate = next(name for name, raw in data["outputs"].items()
        if name.startswith("data/corpus/") and name not in {repair.A_PATH, f"data/corpus/{repair.B}.jsonl"}
        and raw is not None)
    path = tmp_path / candidate
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data["outputs"][candidate])
    # Restoring just the two old volume files is not a complete unapply.
    assert repair.active(tmp_path)
    with pytest.raises(ValueError):
        repair.verify(tmp_path)
    assert path.read_bytes() == data["outputs"][candidate]
    assert (tmp_path / repair.A_PATH).read_bytes() == data["before"][repair.A_PATH]


@pytest.mark.parametrize("changed", ["recipe", "source-capture"])
def test_reapply_refuses_changed_frozen_authority_before_rebuilding(frozen_scope, tmp_path, changed):
    data = frozen_scope
    audit, _ = retained_admission(tmp_path)
    repair.undo(tmp_path)
    authority = tmp_path / repair.AUDIT / "changes.json"
    original_authority = authority.read_bytes()
    capture = tmp_path / repair.AUDIT / "source-evidence.json"
    changed_pins = {**repair.recipe_pins(), "repair_dubner_scholias.py": "0" * 64}
    if changed == "source-capture":
        capture.write_bytes(capture.read_bytes() + b"\n")
    with patch.object(repair, "build", side_effect=AssertionError("Invalid authority must not rerun collation")) as build:
        if changed == "recipe":
            with patch.object(repair, "recipe_pins", return_value=changed_pins):
                with pytest.raises(ValueError):
                    repair.apply(tmp_path)
        else:
            with pytest.raises(ValueError):
                repair.apply(tmp_path)
        build.assert_not_called()
    assert authority.read_bytes() == original_authority
    assert_exactly_unapplied(tmp_path, audit, data["before"])


def test_orphaned_preimage_archive_cannot_authorize_a_fresh_apply(frozen_scope, tmp_path):
    data = frozen_scope
    audit, _ = retained_admission(tmp_path)
    repair.undo(tmp_path)
    authority = tmp_path / repair.AUDIT / "changes.json"
    authority.unlink()
    archive = tmp_path / repair.AUDIT / "before.json.gz"
    original_archive = archive.read_bytes()
    with patch.object(repair, "build", side_effect=AssertionError("An orphaned archive must not authorize collation")) as build:
        with pytest.raises(ValueError):
            repair.apply(tmp_path)
        build.assert_not_called()
    assert not authority.exists()
    assert archive.read_bytes() == original_archive
    assert_exactly_unapplied(tmp_path, audit, data["before"])
