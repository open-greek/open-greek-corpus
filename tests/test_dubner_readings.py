"""A later reading review preserves the frozen scope authority and literal undo."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_dubner_readings as repair
import dubner_layers
from ocr_consensus import merge_witnesses, tokenize


def witness(identifier, text, source_rows=None):
    return {"id": identifier, "vote_group": "dubner-1855-" + identifier,
        "artifact_sha256": repair.sha(text.encode()), "text": text,
        "source_rows": source_rows or [identifier], "derived": False}


def observation(text, original, corrected, *, identifier="reading", scope="historical", start=None):
    start = text.index(original) if start is None else start
    return {"id": identifier, "claim_id": "claim-" + identifier, "scope": scope,
        "original": original, "corrected": corrected, "start": start,
        "end": start + len(original), "allowed_observed_readings": [original]}


def test_fallback_offsets_translate_explicit_edits_and_reject_partial_overlap():
    edits = [{"offset": 2, "original": "abc", "alternative": "longer"},
             {"offset": 8, "original": "xx", "alternative": "x"}]
    assert repair.translate_range(5, 8, edits) == (8, 11)
    assert repair.translate_range(2, 10, edits) == (2, 12)
    with pytest.raises(ValueError, match="partially overlaps"):
        repair.translate_range(3, 6, edits)
    with pytest.raises(ValueError, match="Overlapping"):
        repair.translate_range(0, 12, edits + [{"offset": 9, "original": "xx", "alternative": "x"}])


def test_token_trace_matches_frozen_dehyphenation_and_unicode_normalization():
    text = "λόγος ἀν-\nθρώπου τὴν ελλα λόγος."
    labels = [frozenset({"claim"}) if 6 <= i < 18 else frozenset() for i in range(len(text))]
    traced = repair.traced_tokens(text, labels)
    assert [form for form, _ in traced] == [form for form, _ in tokenize(text)]
    assert traced[1] == ("ἀνθρώπου", ["claim"])


def test_exact_source_patch_precedes_routing_and_retains_original_row():
    text = "ὁ | σήνελλα\nλόγος | τέλος"
    original = witness("harvard", text)
    item = observation(text, "σήνελλα", "τήνελλα")
    record = {"id": "harvard", "path": "data/original.jsonl", "row": {"locus": "1", "text": text},
              "derived": False, "alternatives": []}
    pieces = [{"record": record, "part": {"start": 0, "end": len(text)},
               "start": 0, "end": len(text), "text": text}]
    patched, edits, labels = repair.patch_witness(original, pieces, {(record["path"], "1"): [item]})
    routed, routing = repair.route_witness(patched, "fixture:0001", {"approved": True,
        "reading_order": [[1, "left"], [2, "left"], [1, "right"], [2, "right"]],
        "evidence": {"source": "inspected two-column fixture"}})
    trace = repair.traced_tokens(routed["text"], repair.routed_labels(labels, routing))
    assert trace == [("ὁ", []), ("λόγος", []), ("τήνελλα", ["reading"]), ("τέλος", [])]
    assert original["text"] == text and edits[0]["original"] == "σήνελλα"
    assert repair.restore_witness(routed, routing) == patched
    assert routed["vote_group"] == original["vote_group"]


def test_a_source_reading_cannot_cross_a_frozen_role_boundary():
    text = "λόγος τέλος"
    item = observation(text, "λόγος τέλος", "λόγος")
    record = {"id": "a", "path": "data/raw.jsonl", "row": {"locus": "1", "text": text}, "derived": False}
    pieces = [{"record": record, "part": {"start": 0, "end": 5}, "start": 0, "end": 5, "text": "λόγος"}]
    with pytest.raises(ValueError, match="source-role boundary"):
        repair.patch_witness(witness("a", "λόγος"), pieces, {(record["path"], "1"): [item]})


def test_derived_lane_requires_an_explicitly_allowed_observed_reading():
    record = {"id": "a-fallback", "path": "data/raw.jsonl", "row": {"locus": "1", "text": "ἄλλος"},
        "derived": True, "alternatives": [{"offset": 0, "original": "λόγος", "alternative": "ἄλλος"}]}
    pieces = [{"record": record, "part": {"start": 0, "end": 5}, "start": 0, "end": 5, "text": "ἄλλος"}]
    item = observation("λόγος", "λόγος", "λόγον")
    with pytest.raises(ValueError, match="occurrence-specific evidence"):
        repair.patch_witness(witness("a", "ἄλλος"), pieces, {(record["path"], "1"): [item]})
    item["allowed_observed_readings"].append("ἄλλος")
    patched, edits, _ = repair.patch_witness(witness("a", "ἄλλος"), pieces, {(record["path"], "1"): [item]})
    assert patched["text"] == "λόγον" and edits[0]["original"] == "ἄλλος"


def test_source_adjudication_retains_ties_votes_punctuation_and_contrary_readings():
    a, b = witness("toronto", "σίκυος,"), witness("harvard", "σίκος,")
    result = merge_witnesses([a, b])
    item = observation("σίχuos", "σίχuos", "σίκυος")
    traces = {"toronto": [("σίκυος", ["reading"])], "harvard": [("σίκος", [])]}
    reviewed, count = repair.adjudicate(result, traces, {"reading": item})
    slot = reviewed["ocr_consensus"]["slots"][0]
    assert count == 1 and slot["selected"] == "σίκυος" and slot["lexical_eligible"]
    assert slot["status"] == "source-reviewed" and slot["vote_status"] == "unresolved"
    assert slot["tied_readings"] == result["ocr_consensus"]["slots"][0]["tied_readings"]
    assert slot["readings"] == result["ocr_consensus"]["slots"][0]["readings"]
    assert slot["source_review"]["contrary_original_readings"] == ["σίχuos"]
    assert reviewed["text"] == "σίκυος," and reviewed["analysis_text"] == "σίκυος"
    assert result["ocr_consensus"]["slots"][0]["status"] == "unresolved"


def test_source_claims_that_align_to_conflicting_forms_fail_closed():
    a, b = witness("toronto", "λόγος"), witness("harvard", "λόγον")
    items = {key: observation(key, key, key, identifier=key) for key in ("λόγος", "λόγον")}
    with pytest.raises(ValueError, match="conflict"):
        repair.adjudicate(merge_witnesses([a, b]),
            {"toronto": [("λόγος", ["λόγος"])], "harvard": [("λόγον", ["λόγον"])]}, items)


@pytest.fixture
def lifecycle(tmp_path, monkeypatch):
    primary = "data/corpus/fixture.work.jsonl"
    original, current = b'original primary\n', b'reviewed primary\n'
    (tmp_path / primary).parent.mkdir(parents=True)
    (tmp_path / primary).write_bytes(original)
    authority = tmp_path / repair.base.AUDIT / "changes.json"
    authority.parent.mkdir(parents=True)
    authority.write_bytes(b'{"frozen":"scope"}\n')
    token = {"recipe": "first", "source": "first"}
    monkeypatch.setattr(repair, "recipe_pins", lambda: {"fixture.py": token["recipe"]})
    def evidence(root):
        if token["source"] != "first":
            raise ValueError("source evidence changed")
        return {}, {}, {"fixture-source": "first"}
    monkeypatch.setattr(repair, "evidence", evidence)
    monkeypatch.setattr(dubner_layers, "verify_scope", lambda *args, **kwargs: (
        {"outputs": {primary: repair.sha(original)}}, {}))
    generated = repair.ASSESSMENT
    def build(root, before, **kwargs):
        assert before[primary] == original
        return {primary: current, generated: b'{"assessment":true}\n'}, {"fixture.work": {}}, {"works": 1}
    monkeypatch.setattr(repair, "build", build)
    return tmp_path, primary, original, current, token


def test_literal_undo_and_reapply_are_byte_exact(lifecycle):
    root, primary, original, current, _ = lifecycle
    repair.apply(root, recorded_at="2026-10-24T12:00:00Z")
    authority = (root / repair.AUDIT / "changes.json").read_bytes()
    archive = (root / repair.AUDIT / "before.json.gz").read_bytes()
    assert repair.active(root) and (root / primary).read_bytes() == current
    repair.verify(root, replay=True)
    repair.undo(root)
    assert not repair.active(root) and (root / primary).read_bytes() == original
    assert not (root / repair.ASSESSMENT).exists()
    repair.apply(root)
    assert (root / repair.AUDIT / "changes.json").read_bytes() == authority
    assert (root / repair.AUDIT / "before.json.gz").read_bytes() == archive
    assert (root / primary).read_bytes() == current


@pytest.mark.parametrize("change", ["recipe", "source"])
def test_invalidated_evidence_or_recipe_blocks_reapply_but_allows_literal_undo(lifecycle, change):
    root, primary, original, _, token = lifecycle
    repair.apply(root)
    token[change] = "changed"
    with pytest.raises(ValueError):
        repair.verify(root)
    repair.undo(root)
    assert (root / primary).read_bytes() == original
    with pytest.raises(ValueError):
        repair.apply(root)


def test_partial_undo_stays_active_and_verification_fails(lifecycle):
    root, primary, original, _, _ = lifecycle
    repair.apply(root)
    (root / primary).write_bytes(original)
    assert repair.active(root)
    with pytest.raises(ValueError, match="output changed"):
        repair.verify(root)
    with pytest.raises(ValueError, match="already active"):
        repair.apply(root)


def test_orphaned_preimage_archive_cannot_authorize_apply(tmp_path):
    directory = tmp_path / repair.AUDIT
    directory.mkdir(parents=True)
    (directory / "before.json.gz").write_bytes(b"orphan")
    with pytest.raises(ValueError, match="orphaned"):
        repair.apply(tmp_path)


def test_unowned_new_destination_is_not_overwritten(lifecycle):
    root, _, original, _, _ = lifecycle
    path = root / repair.ASSESSMENT
    path.parent.mkdir(parents=True)
    path.write_bytes(b"unrelated")
    with pytest.raises(ValueError, match="unowned"):
        repair.apply(root)
    assert path.read_bytes() == b"unrelated"
    assert not (root / repair.AUDIT / "changes.json").exists()


def test_projection_first_cache_replays_the_authority_before_accepting_rows(tmp_path, monkeypatch):
    scope = tmp_path / repair.base.AUDIT / "changes.json"
    scope.parent.mkdir(parents=True)
    scope.write_bytes(repair.encoded({"outputs": {}}))
    calls = []
    def verify(root, **kwargs):
        calls.append(kwargs)
        return {"outputs": {}}, {}
    monkeypatch.setattr(repair, "verify", verify)
    repair._verified_rows.cache_clear()
    assert repair._verified_rows(str(tmp_path), ("first",)) == {}
    assert repair._verified_rows(str(tmp_path), ("first",)) == {}
    assert calls == [{"replay": True}]


def test_checked_state_replays_once_and_returns_defensive_copies(monkeypatch):
    calls = []
    signature = ["first"]
    monkeypatch.setattr(repair, "_state_signature", lambda root: tuple(signature))
    def verify(root, **kwargs):
        calls.append(kwargs)
        return {"counts": {"works": 14}}, {"primary": b"literal"}
    monkeypatch.setattr(repair, "verify", verify)
    repair._checked_state.cache_clear()
    audit, before = repair.checked_state("fixture")
    audit["counts"]["works"] = 0
    before["primary"] = b"changed"
    assert repair.checked_state("fixture") == ({"counts": {"works": 14}}, {"primary": b"literal"})
    assert calls == [{"replay": True}]
    signature[0] = "changed source"
    repair.checked_state("fixture")
    assert calls == [{"replay": True}, {"replay": True}]


def test_comprehensive_signature_includes_missing_outputs_capture_authority_and_recipes(tmp_path, monkeypatch):
    (tmp_path / repair.AUDIT).mkdir(parents=True)
    base_dir = tmp_path / repair.base.AUDIT
    base_dir.mkdir(parents=True)
    (tmp_path / repair.AUDIT / "changes.json").write_bytes(repair.encoded({
        "outputs": {"data/corpus/new.jsonl": "unused"}, "evidence_files": {"data/evidence.png": "unused"}}))
    (base_dir / "changes.json").write_bytes(repair.encoded({"outputs": {"data/corpus/old.jsonl": "unused"}}))
    (base_dir / "source-evidence.json").write_bytes(repair.encoded({"files": [{"path": "data/base-image.png"}]}))
    monkeypatch.setattr(repair, "recipe_pins", lambda: {"new-recipe.py": "unused"})
    monkeypatch.setattr(repair.base, "recipe_pins", lambda: {"frozen-recipe.py": "unused"})
    first = repair._state_signature(tmp_path)
    names = {name for name, _, _ in first}
    assert {repair.base.AUDIT + "/source-evidence.json", "data/base-image.png", "data/evidence.png",
        "data/corpus/new.jsonl", "data/corpus/old.jsonl", "scripts/new-recipe.py",
        "scripts/frozen-recipe.py"} <= names
    (tmp_path / "data/evidence.png").write_bytes(b"newly restored image")
    assert repair._state_signature(tmp_path) != first
