"""Source decisions remain occurrence-specific, reversible, and conservative."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_herodas_readings as review


def decision(start, end, original, corrected, disposition="resolved", alternatives=None):
    return {"scan_page": 78, "uncertainty_index": 0,
        "source_char_range": [start, end], "original_text": original,
        "corrected_text": corrected, "disposition": disposition,
        "remaining_alternatives": alternatives or [],
        "evidence": "Native source pixels distinguish the printed mark.",
        "reviewed_at": "2026-10-22T19:00:00Z"}


def test_source_addresses_survive_a_length_changing_earlier_correction():
    text = "ὦνα’ λόγος λόγος"
    frozen = {"text": text, "reviewed_at": "2026-10-22T17:00:00Z", "uncertainties": [
        {"start": 0, "end": 4}, {"start": 11, "end": 16}]}
    first = decision(0, 4, "ὦνα’", "ὤνα ’")
    second = decision(11, 16, "λόγος", "λογός", "unresolved", ["λόγος"])
    second["uncertainty_index"] = 1
    result = review._recovered_review({"locus": "herodas_hk_0078.1", "text": text}, frozen,
                                    {(78, 0): first, (78, 1): second})
    assert result["corrected_text"] == "ὤνα ’ λόγος λογός"
    item = result["uncertainties"][0]
    assert result["corrected_text"][item["start"]:item["end"]] == "λογός"
    assert item["start"] == 12 and item["alternatives"] == ["λόγος"]


def test_printed_damage_is_assessed_without_becoming_a_complete_word():
    text = "λόγος τ( μένει"
    frozen = {"text": text, "reviewed_at": "2026-10-22T17:00:00Z", "uncertainties": [{"start": 6, "end": 8}]}
    result = review._recovered_review({"locus": "herodas_hk_0078.1", "text": text}, frozen,
        {(78, 0): decision(6, 8, "τ(", "τ(", "printed-damage")})
    assert result["uncertainties"] == []
    assert result["forced_exclusions"][0]["text"] == "τ("


def test_adjacent_source_edit_cannot_overlap_an_archived_uncertainty():
    text = "λόγος μένει"
    frozen = {"text": text, "reviewed_at": "2026-10-22T17:00:00Z", "uncertainties": [{"start": 0, "end": 5}]}
    edit = decision(0, 5, "λόγος", "λογός")
    with pytest.raises(ValueError, match="archived occurrence"):
        review._recovered_review({"locus": "herodas_hk_0078.1", "text": text}, frozen,
                                 {(78, 0): edit}, [deepcopy(edit)])


@pytest.mark.parametrize("change", [
    {"source_char_range": [1, 5]}, {"original_text": "other"},
    {"disposition": "preferred"}, {"remaining_alternatives": "λογός"},
    {"remaining_alternatives": ["λογός"]}, {"evidence": ""},
    {"reviewed_at": "2026-10-22T19:00:00"},
])
def test_invalid_decision_never_overrides_a_source_occurrence(change):
    text = "λόγος μένει"
    frozen = {"text": text, "reviewed_at": "2026-10-22T17:00:00Z", "uncertainties": [{"start": 0, "end": 5}]}
    edit = {**decision(0, 5, "λόγος", "λόγος"), **change}
    with pytest.raises(ValueError):
        review._recovered_review({"locus": "herodas_hk_0078.1", "text": text}, frozen, {(78, 0): edit})


def source_review(text):
    return {"corrected_text": text, "uncertainties": [], "forced_exclusions": []}


def test_printed_bracket_carries_through_nested_page_opening():
    rows = [{"locus": "herodas_hk_0440.1"}, {"locus": "herodas_hk_0442.1"}]
    observations = {rows[0]["locus"]: source_review("λόγος [θεός"),
                    rows[1]["locus"]: source_review("μένει [καλός]] τέλος")}
    slots = review.critical_slots(rows, observations)
    assert not slots[rows[0]["locus"]][0][3]
    assert slots[rows[1]["locus"]][0][3]
    assert slots[rows[1]["locus"]][1][3]
    assert not slots[rows[1]["locus"]][2][3]


def test_separate_fragments_do_not_inherit_each_others_critical_state():
    rows = [{"locus": "herodas_hk_0472.3"}, {"locus": "herodas_hk_0472.4"}]
    observations = {rows[0]["locus"]: source_review("λόγος ..."),
                    rows[1]["locus"]: source_review("μένει τέλος")}
    slots = review.critical_slots(rows, observations)
    assert not slots[rows[1]["locus"]][0][3]


def test_unfinished_parenthesized_word_does_not_swallow_the_next_source_page():
    rows = [{"locus": "herodas_hk_0442.1"}, {"locus": "herodas_hk_0444.1"}]
    observations = {rows[0]["locus"]: source_review("τ(\n. . . . ."),
                    rows[1]["locus"]: source_review("ἁγνά μένει")}
    slots = review.critical_slots(rows, observations)
    assert slots[rows[0]["locus"]][0][3]
    assert "printed-supply-or-unclear-reading" not in slots[rows[1]["locus"]][0][3]
    assert not slots[rows[1]["locus"]][1][3]


@pytest.mark.parametrize("gap", ["...", ". . .", "…"])
def test_printed_gap_boundaries_do_not_depend_on_dot_spacing(gap):
    assert review._source_flags("λόγος " + gap, [("λόγος", 0, 5)]) == [["source-gap-boundary"]]
    text = gap + " λόγος"
    assert review._source_flags(text, [("λόγος", len(gap) + 1, len(text))]) == [["source-gap-boundary"]]


@pytest.mark.parametrize("entry", [
    {"start": -1, "end": 3, "alternatives": [], "evidence": "source"},
    {"start": 0, "end": 5, "text": "other", "alternatives": [], "evidence": "source"},
    {"start": 0, "end": 5, "alternatives": []},
])
def test_uncertain_excerpt_readings_need_literal_occurrence_bounds(entry):
    with pytest.raises(ValueError, match="exact corrected bounds"):
        review._validate_uncertainties("λόγος μένει", [entry])


@pytest.mark.skipif(not (ROOT / review.AUDIT / "changes.json").exists(), reason="Proofreading not yet admitted")
def test_published_review_networks_and_literal_undo(tmp_path):
    from ocr_consensus import compact_corpus_consensus, restore_corpus_consensus
    audit, before, raw = review.verify(ROOT)
    assert audit["counts"]["older_passages_reviewed"] == 62
    assert audit["counts"]["archived_uncertainty_spans_reviewed"] == 43
    rows = [json.loads(line) for line in raw.splitlines()]
    originals = [json.loads(line) for line in before.splitlines()]
    assert [row["locus"] for row in rows] == [row["locus"] for row in originals]
    networks = json.loads(gzip.decompress((ROOT / review.AUDIT / "networks.json.gz").read_bytes()))
    for row in rows:
        reference = row["ocr_consensus"]["full_network"]
        full = networks[reference["key"]]
        compact = compact_corpus_consensus(full, reference)
        assert all(row[key] == value for key, value in compact.items())
        assert restore_corpus_consensus(compact, full) == full
    target = tmp_path / review.AUDIT; target.mkdir(parents=True)
    for name in ["before.json.gz", "changes.json"]:
        shutil.copyfile(ROOT / review.AUDIT / name, target / name)
    primary = tmp_path / review.PRIMARY; primary.parent.mkdir(parents=True)
    primary.write_bytes(raw)
    review.undo(tmp_path)
    assert primary.read_bytes() == before
    review.undo(tmp_path)
    primary.write_bytes(b"modified")
    with pytest.raises(ValueError, match="modified"):
        review.undo(tmp_path)
