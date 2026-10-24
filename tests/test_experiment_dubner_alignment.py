"""A reviewed layout permutation is reversible and never supplies another voter."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import experiment_dubner_alignment as experiment
from ocr_consensus import merge_witnesses


def witness(identifier, text):
    return {"id": identifier, "vote_group": "dubner-1855-" + identifier,
        "artifact_sha256": experiment.sha(text.encode()), "text": text,
        "source_rows": [identifier + str(i) for i, _ in enumerate(text.splitlines())]}


def decision(order):
    return {"approved": True, "reading_order": order, "evidence": {"source": "reviewed source fixture"}}


def test_all_original_characters_and_source_row_refs_remain_reconstructible():
    original = witness("harvard", "ὁ δὲ | ἔχει πάντα\nλόγος | σαφῶς\n")
    order = [[1, "left"], [2, "left"], [1, "right"], [2, "right"]]
    routed, record = experiment.route_witness(original, "fixture:0001", decision(order))
    assert experiment.restore_witness(routed, record) == original
    assert "".join(part["text"] for part in record["parts"]) == original["text"]
    assert {part["source_row"] for part in record["parts"]} == set(original["source_rows"])
    assert routed["id"] == original["id"] and routed["vote_group"] == original["vote_group"]
    assert routed["artifact_sha256"] != original["artifact_sha256"]
    assert record["generated_separator"] == "\n"


@pytest.mark.parametrize("order", [
    [[1, "left"], [1, "right"]],
    [[1, "left"], [2, "left"], [1, "right"], [2, "right"], [1, "left"]],
    [[1, "left"], [2, "left"], [1, "right"], [3, "right"]],
])
def test_a_permutation_cannot_drop_repeat_or_invent_a_nonblank_cell(order):
    with pytest.raises(ValueError):
        experiment.route_witness(witness("harvard", "ὁ | λόγος\nδὲ | ἔχει"), "fixture", decision(order))


def test_layout_delimiters_alone_do_not_authorize_reading_order():
    original = witness("harvard", "ὁ | λόγος\nδὲ | ἔχει")
    with pytest.raises(ValueError, match="source-review"):
        experiment.route_witness(original, "fixture", {"reading_order": []})


def test_sparse_right_cells_require_manual_routing_even_if_every_line_has_a_pipe():
    original = witness("harvard", "\n".join(["ὁ | λόγος"] + ["δὲ |"] * 8))
    assert experiment.candidate(original)["uniform_two_column_candidate"] is False
    with pytest.raises(ValueError, match="Sparse"):
        experiment.column_order(original)


def test_layout_can_recover_an_agreement_without_creating_a_vote_group():
    a = witness("toronto", "ὁ δὲ λόγος\nἔχει πάντα σαφῶς")
    b = witness("harvard", "ὁ δὲ | ἔχει πάντα\nλόγος | σαφῶς")
    old = merge_witnesses([a, b])
    result = experiment.realign_page(old, "fixture", {
        b["id"]: decision([[1, "left"], [2, "left"], [1, "right"], [2, "right"]])})
    assert result["new_counts"] == {"agreement": 6}
    assert len(result["network"]["ocr_consensus"]["witnesses"]) == 2
    assert {w["vote_group"] for w in result["network"]["ocr_consensus"]["witnesses"]} == {
        "dubner-1855-toronto", "dubner-1855-harvard"}


def test_source_routing_preserves_real_lexical_disagreement():
    a = witness("toronto", "ὁ δὲ λόγος\nἔχει πάντα σαφῶς")
    b = witness("harvard", "ὁ δὲ | ἔχει πάντα\nλόγος | κακῶς")
    result = experiment.realign_page(merge_witnesses([a, b]), "fixture", {
        b["id"]: decision([[1, "left"], [2, "left"], [1, "right"], [2, "right"]])})
    slot = next(slot for slot in result["network"]["ocr_consensus"]["slots"] if slot["status"] == "unresolved")
    assert set(slot["tied_readings"]) == {"σαφῶς", "κακῶς"}
    assert not slot["lexical_eligible"] and slot["selected"] is None


def test_changed_routing_postimage_is_rejected():
    original = witness("harvard", "ὁ | λόγος\nδὲ | ἔχει")
    routed, record = experiment.route_witness(original, "fixture", decision(
        [[1, "left"], [2, "left"], [1, "right"], [2, "right"]]))
    changed = deepcopy(routed)
    changed["text"] += " πλαστός"
    with pytest.raises(ValueError, match="postimage"):
        experiment.restore_witness(changed, record)
