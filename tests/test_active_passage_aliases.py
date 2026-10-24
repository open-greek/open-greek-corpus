"""Active citation extensions preserve the earlier migration's frozen bytes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_work_index as index


@pytest.fixture
def citations(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "REPO", tmp_path)
    data = tmp_path / "data"
    for directory in ("corpus", "corpus_secondary", "paratext", "ocr_witnesses"):
        destination = data / directory / "current.jsonl"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"locus":"1","text":"λόγος"}\n')
    path = data / "passage_aliases.json"
    old = {"path": "data/corpus/current.jsonl", "slug": "current", "locus": "1"}
    path.write_text(json.dumps({"aliases": {"old": {"old.1": old}}}))
    authority_path = "data/corpus_changes/example/changes.json"
    authority = tmp_path / authority_path
    authority.parent.mkdir(parents=True)
    authority.write_text('{"verified":"admission"}\n')
    fragment = {"aliases": {"old": {"old.2": old.copy()}},
        "authority": {"path": authority_path,
            "sha256": hashlib.sha256(authority.read_bytes()).hexdigest()}}
    works = {"current": {"former_slugs": ["old"]}}
    monkeypatch.setattr(index, "_active_passage_alias_fragments", lambda root: [fragment])
    return path, works, fragment


def test_active_extension_is_merged_without_changing_historical_authority(citations):
    path, works, fragment = citations
    original = path.read_bytes()
    expected_fragment = deepcopy(fragment)
    historical = index.load_passage_aliases(path, works)
    aliases, authorities = index.load_active_passage_aliases(path, works)
    assert set(historical["old"]) == {"old.1"}
    assert set(aliases["old"]) == {"old.1", "old.2"}
    assert authorities == [fragment["authority"]]
    assert fragment == expected_fragment
    assert path.read_bytes() == original
    assert index.resolve_citation({"works": works, "passage_aliases": aliases},
        "old", "old.2") == fragment["aliases"]["old"]["old.2"]


@pytest.mark.parametrize("different", [False, True])
def test_collision_cannot_replace_even_an_identical_historical_alias(citations, different):
    path, works, fragment = citations
    target = fragment["aliases"]["old"].pop("old.2")
    if different:
        target = {"path": "data/paratext/current.jsonl", "locus": "1"}
    fragment["aliases"]["old"]["old.1"] = target
    with pytest.raises(ValueError, match="alias collision"):
        index.load_active_passage_aliases(path, works)


def test_two_extensions_cannot_claim_the_same_citation(citations, monkeypatch):
    path, works, fragment = citations
    monkeypatch.setattr(index, "_active_passage_alias_fragments",
        lambda root: [fragment, deepcopy(fragment)])
    with pytest.raises(ValueError, match="alias collision"):
        index.load_active_passage_aliases(path, works)


@pytest.mark.parametrize("target", [
    {"path": "data/corpus_secondary/current.jsonl", "slug": "current", "storage": "secondary", "locus": "1"},
    {"path": "data/paratext/current.jsonl", "locus": "1"},
    {"path": "data/ocr_witnesses/current.jsonl", "locus": "1"},
])
def test_preserved_secondary_and_outside_primary_destinations_are_supported(citations, target):
    path, works, fragment = citations
    fragment["aliases"]["old"]["old.2"] = target
    aliases, _ = index.load_active_passage_aliases(path, works)
    assert aliases["old"]["old.2"] == target


@pytest.mark.parametrize("change,message", [
    ({"locus": "missing"}, "Missing passage alias destination"),
    ({"path": "../escape.jsonl"}, "Invalid passage alias path"),
    ({"path": "data/private/current.jsonl", "slug": None}, "Invalid passage alias destination"),
    ({"slug": "missing"}, "Invalid passage alias work"),
])
def test_active_destinations_receive_the_existing_strict_validation(citations, change, message):
    path, works, fragment = citations
    fragment["aliases"]["old"]["old.2"].update(change)
    with pytest.raises(ValueError, match=message):
        index.load_active_passage_aliases(path, works)


def test_extension_cannot_invent_a_historical_source_work(citations):
    path, works, fragment = citations
    fragment["aliases"]["unknown"] = fragment["aliases"].pop("old")
    with pytest.raises(ValueError, match="source is unknown"):
        index.load_active_passage_aliases(path, works)


@pytest.mark.parametrize("change", [
    {"path": "../changes.json"}, {"path": "/tmp/changes.json"},
    {"path": "data/corpus_changes/../changes.json"},
    {"path": "data/other/changes.json"}, {"sha256": "not-a-hash"},
])
def test_invalid_authority_reference_is_rejected(citations, change):
    path, works, fragment = citations
    fragment["authority"].update(change)
    with pytest.raises(ValueError, match="Invalid active passage alias authority"):
        index.load_active_passage_aliases(path, works)


@pytest.mark.parametrize("missing", [False, True])
def test_changed_or_missing_admission_authority_is_rejected(citations, missing):
    path, works, fragment = citations
    authority = index.REPO / fragment["authority"]["path"]
    if missing:
        authority.unlink()
    else:
        authority.write_bytes(authority.read_bytes() + b" ")
    with pytest.raises(ValueError, match="authority changed"):
        index.load_active_passage_aliases(path, works)


def test_no_extension_preserves_the_historical_map_and_metadata_shape(citations, monkeypatch):
    path, works, _ = citations
    monkeypatch.setattr(index, "_active_passage_alias_fragments", lambda root: [])
    aliases, authorities = index.load_active_passage_aliases(path, works)
    assert aliases == index.load_passage_aliases(path, works)
    assert authorities == []


def test_named_producer_receives_the_repository_and_can_recognize_undo(tmp_path, monkeypatch):
    observed = []
    def inactive(root):
        observed.append(root)
        return None
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(alias_fragment=inactive))
    assert index._active_passage_alias_fragments(tmp_path) == []
    assert observed == [tmp_path]


def test_failed_producer_validation_is_never_treated_as_no_extension(tmp_path, monkeypatch):
    def invalid(root):
        raise ValueError("changed source postimage")
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(alias_fragment=invalid))
    with pytest.raises(ValueError, match="changed source postimage"):
        index._active_passage_alias_fragments(tmp_path)


@pytest.fixture
def retired_citations(citations):
    path, works, fragment = citations
    identifier = "ogc002861"
    slug = "dissolved-volume"
    ledger_path = path.parent / "work_ids.json"
    ledger = {"works": {identifier: {"slug": slug, "status": "retired", "former_slugs": []}}}
    ledger_path.write_text(json.dumps(ledger))
    target = {"path": "data/ocr_witnesses/current.jsonl", "locus": "1"}
    fragment["aliases"][slug] = {"old.volume.1": target}
    fragment["retired_sources"] = {slug: identifier}
    return path, works, fragment, ledger_path, ledger


def test_retired_expression_can_supply_citations_without_becoming_a_current_work(retired_citations):
    path, works, fragment, ledger_path, _ = retired_citations
    ledger_before = ledger_path.read_bytes()
    aliases, authorities = index.load_active_passage_aliases(path, works)
    slug = "dissolved-volume"
    assert slug not in works
    assert authorities[0]["retired_sources"] == {slug: "ogc002861"}
    target = index.resolve_citation({"works": works, "passage_aliases": aliases}, slug, "old.volume.1")
    assert target == fragment["aliases"][slug]["old.volume.1"]
    assert ledger_path.read_bytes() == ledger_before
    with pytest.raises(ValueError, match="source is unknown"):
        index.validate_passage_aliases({slug: aliases[slug]}, works)


def test_retired_source_can_target_an_existing_works_secondary_witness(retired_citations):
    path, works, fragment, _, _ = retired_citations
    target = {"path": "data/corpus_secondary/current.jsonl", "slug": "current", "storage": "secondary", "locus": "1"}
    fragment["aliases"]["dissolved-volume"]["old.volume.1"] = target
    aliases, _ = index.load_active_passage_aliases(path, works)
    assert aliases["dissolved-volume"]["old.volume.1"] == target


@pytest.mark.parametrize("mutation", ["unknown-id", "wrong-slug", "served", "former-slug-only", "missing-ledger", "invalid-ledger"])
def test_retired_source_requires_the_original_retired_ledger_identity(retired_citations, mutation):
    path, works, fragment, ledger_path, ledger = retired_citations
    entry = ledger["works"]["ogc002861"]
    if mutation == "unknown-id":
        fragment["retired_sources"]["dissolved-volume"] = "ogc999999"
    elif mutation == "wrong-slug":
        entry["slug"] = "another-volume"
    elif mutation == "served":
        entry["status"] = "served"
    elif mutation == "former-slug-only":
        entry.update(slug="renamed-volume", former_slugs=["dissolved-volume"])
    if mutation == "missing-ledger":
        ledger_path.unlink()
    else:
        ledger_path.write_text(json.dumps([] if mutation == "invalid-ledger" else ledger))
    with pytest.raises(ValueError, match="retired passage aliases|Retired passage alias source"):
        index.load_active_passage_aliases(path, works)


def test_a_retired_ledger_entry_cannot_authorize_a_current_source_work(retired_citations):
    path, works, _, _, _ = retired_citations
    works["dissolved-volume"] = {}
    with pytest.raises(ValueError, match="differs from its ledger"):
        index.load_active_passage_aliases(path, works)


def test_a_retired_ledger_entry_cannot_authorize_a_current_rename(retired_citations):
    path, works, _, _, _ = retired_citations
    works["current"]["former_slugs"].append("dissolved-volume")
    with pytest.raises(ValueError, match="differs from its ledger"):
        index.load_active_passage_aliases(path, works)


@pytest.mark.parametrize("storage", ["primary", "secondary"])
def test_retired_source_authorization_never_authorizes_a_retired_destination(retired_citations, storage):
    path, works, fragment, _, _ = retired_citations
    directory = "corpus" if storage == "primary" else "corpus_secondary"
    target_path = f"data/{directory}/dissolved-volume.jsonl"
    (index.REPO / target_path).write_text('{"locus":"1","text":"λόγος"}\n')
    fragment["aliases"]["dissolved-volume"]["old.volume.1"] = {
        "path": target_path, "slug": "dissolved-volume", "storage": storage, "locus": "1"}
    with pytest.raises(ValueError, match="Invalid passage alias work"):
        index.load_active_passage_aliases(path, works)


def test_retired_source_without_a_declaration_remains_unknown(retired_citations):
    path, works, fragment, _, _ = retired_citations
    fragment.pop("retired_sources")
    with pytest.raises(ValueError, match="source is unknown"):
        index.load_active_passage_aliases(path, works)


def test_retired_source_aliases_still_cannot_collide(retired_citations, monkeypatch):
    path, works, fragment, _, _ = retired_citations
    second = deepcopy(fragment)
    second["aliases"] = {"dissolved-volume": second["aliases"]["dissolved-volume"]}
    monkeypatch.setattr(index, "_active_passage_alias_fragments", lambda root: [fragment, second])
    with pytest.raises(ValueError, match="alias collision"):
        index.load_active_passage_aliases(path, works)


def test_unused_retired_source_declaration_is_rejected(retired_citations):
    path, works, fragment, _, _ = retired_citations
    fragment["aliases"].pop("dissolved-volume")
    with pytest.raises(ValueError, match="has no declared aliases"):
        index.load_active_passage_aliases(path, works)
