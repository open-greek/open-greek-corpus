"""Dübner source identities and credits survive a complete registry rebuild."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import reviewed_manifestations as reviewed
from source_identity import Registry

ACHARNIANS, PLATONIUS = reviewed.DUBNER_HISTORICAL_EDITIONS
NEW_PLAY = "scholia-in-aristophanem.scholia-in-equites"
NAMED = "demetrius-triclinius.de-metris"


@pytest.fixture
def identities(monkeypatch):
    shared = {"scope": "Source-reviewed historical body only", "primary_rows": 3,
        "secondary_rows": 11, "analysis_tokens": 17, "counts": {"unresolved_slots": 4},
        "edition": "dubner-1855-collated",
        "authority": {"path": "data/corpus_changes/dubner-1855-scope/changes.json", "sha256": "a" * 64},
        "sources": [{"url": "https://example.org/toronto.pdf", "sha256": "b" * 64, "label": "Toronto scan"},
            {"url": "https://example.org/second.pdf", "sha256": "c" * 64, "label": "Second scan"}],
        "qualification": "The same 1855 printed edition has explicit unresolved OCR alternatives."}
    records = {
        ACHARNIANS: {"author": "scholia-in-aristophanem", "author_name": "Scholia in Aristophanem",
            "title": "Scholia in Acharnians, Dübner source scope", "cts": "urn:cts:greekLit:tlg5014.tlg001"},
        NEW_PLAY: {"author": "scholia-in-aristophanem", "author_name": "Scholia in Aristophanem",
            "title": "Scholia in Knights", "cts": None},
        NAMED: {"author": "demetrius-triclinius", "author_name": "Demetrius Triclinius",
            "title": "Printed Triclinius metrical text", "cts": None},
    }
    records = {slug: {**deepcopy(shared), **record} for slug, record in records.items()}
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias",
        SimpleNamespace(metadata=lambda root: deepcopy(records)))
    return records


def historical_registry(identities):
    registry = Registry()
    registry.mint_author("Scholia in Aristophanem", slug="scholia-in-aristophanem")
    registry.mint_author("Platonius", slug="platonius")
    for slug in (ACHARNIANS, PLATONIUS):
        value = identities.get(slug, {"author": "platonius", "cts": "urn:cts:greekLit:tlg5046.tlg001"})
        registry.mint_work(value["author"], "Incorrect whole-volume scope", slug=slug,
            aliases={"cts": value["cts"]})
        registry.mint_edition(slug, reviewed.DUBNER_HISTORICAL_EDITIONS[slug],
            "Misassigned whole-volume OCR", provider="ocr", make_default=True)
        registry.mint_edition(slug, "reference-only", "Separate critical reference",
            provider="tlg-e-reference", servable=False)
    return registry


def test_current_source_scope_preserves_existing_work_and_author_identities(tmp_path, identities):
    registry = historical_registry(identities)
    before_works = {slug: registry.works[slug] for slug in registry.works}
    before_authors = dict(registry.authors)
    metadata = reviewed.register_reviewed_manifestations(registry, tmp_path)
    assert set(metadata) == set(identities)
    for slug, original in before_works.items():
        work = registry.works[slug]
        assert work is original
        if slug in identities:
            assert work.author == identities[slug]["author"]
            assert work.title == identities[slug]["title"]
            assert work.aliases["cts"] == identities[slug]["cts"]
        else:
            assert slug == PLATONIUS
            assert work.author == "platonius"
            assert work.default_edition is None
        assert not work.editions[slug + "." + reviewed.DUBNER_HISTORICAL_EDITIONS[slug]].servable
        assert not work.editions[slug + ".reference-only"].servable
    assert all(registry.authors[slug] is original for slug, original in before_authors.items())
    assert registry.works[NEW_PLAY].author == "scholia-in-aristophanem"
    assert registry.works[NAMED].author == "demetrius-triclinius"
    assert registry.works[NEW_PLAY].aliases == registry.works[NAMED].aliases == {}


def test_primary_and_raw_witness_credits_name_the_actual_edition(tmp_path, identities):
    registry = Registry()
    reviewed.register_reviewed_manifestations(registry, tmp_path)
    for slug, value in identities.items():
        work = registry.works[slug]
        assert work.default_edition == slug + ".dubner-1855-collated"
        primary = work.editions[work.default_edition]
        assert (primary.provider, primary.editor, primary.year, primary.license, primary.storage) == (
            "ocr", "Dübner, Friedrich", 1855, "PD", "primary")
        assert primary.servable
        secondary = work.editions[slug + ".dubner-1855-legacy-witnesses"]
        assert secondary.storage == "secondary" and secondary.license == "PD"
        assert "do not establish independent textual editions" in secondary.note
        coverage = work.coverage_composition
        assert coverage["scope"] == value["scope"]
        assert coverage["counts"] == value["counts"]
        assert coverage["sources"] == value["sources"]
        assert coverage["manifest_sha256"] == value["authority"]["sha256"]
        assert coverage["primary_quality"]["analysis_tokens"] == 17
        assert "not comprehensive proofreading" in coverage["primary_quality"]["note"]
        primary_component, witness_component = coverage["components"]
        assert primary_component["passages"] == 3 and witness_component["passages"] == 11
        assert primary_component["path"] == f"data/corpus/{slug}.jsonl"
        assert witness_component["path"] == f"data/corpus_secondary/{slug}.jsonl"


def test_rebuilding_reviewed_credits_is_byte_stable(tmp_path, identities):
    registry = historical_registry(identities)
    reviewed.register_reviewed_manifestations(registry, tmp_path)
    path = tmp_path / "registry.json"
    registry.save(path)
    first = path.read_bytes()
    restored = Registry.load(path)
    reviewed.register_reviewed_manifestations(restored, tmp_path)
    restored.save(path)
    assert path.read_bytes() == first


def test_initial_admission_helper_registers_the_same_scoped_identities(tmp_path, identities):
    path = tmp_path / "registry.json"
    registry = historical_registry(identities)
    registry.save(path)
    document = json.loads(path.read_bytes())
    reviewed.ensure_dubner_work_records(document, tmp_path)
    for slug, value in identities.items():
        assert document["works"][slug]["author"] == value["author"]
        assert document["works"][slug]["title"] == value["title"]
        assert document["works"][slug]["aliases"].get("cts") == value["cts"]
        assert value["author"] in document["authors"]
    retired = document["works"][PLATONIUS]
    assert retired["default_edition"] is None
    assert not retired["editions"][PLATONIUS + "." + reviewed.DUBNER_HISTORICAL_EDITIONS[PLATONIUS]]["servable"]
    first = deepcopy(document)
    reviewed.ensure_dubner_work_records(document, tmp_path)
    assert document == first


def test_initial_admission_cannot_replace_a_conflicting_cts_identity(tmp_path, identities):
    document = {"authors": {}, "works": {ACHARNIANS: {
        "aliases": {"cts": "urn:cts:greekLit:foreign.work"}}}}
    with pytest.raises(ValueError, match="CTS identity conflicts"):
        reviewed.ensure_dubner_work_records(document, tmp_path)


def test_unapplied_admission_has_no_identities_or_credits(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(metadata=lambda root: {}))
    document = {"authors": {}, "works": {}}
    reviewed.ensure_dubner_work_records(document, tmp_path)
    assert document == {"authors": {}, "works": {}}
    registry = Registry()
    assert reviewed.register_reviewed_manifestations(registry, tmp_path) == {}
    assert registry.works == registry.authors == {}


def test_source_validation_failure_cannot_become_an_unapplied_admission(tmp_path, monkeypatch):
    def invalid(root):
        raise ValueError("Dübner source changed")
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(metadata=invalid))
    with pytest.raises(ValueError, match="source changed"):
        reviewed.register_reviewed_manifestations(Registry(), tmp_path)


def test_retired_whole_volume_is_never_recreated_as_an_admitted_primary(tmp_path, identities):
    registry = Registry()
    metadata = reviewed.register_reviewed_manifestations(registry, tmp_path)
    assert PLATONIUS not in registry.works
    assert PLATONIUS not in metadata
    assert reviewed.dubner_retired_work_slugs(tmp_path) == {PLATONIUS}
    document = {"authors": {}, "works": {}}
    reviewed.ensure_dubner_work_records(document, tmp_path)
    assert PLATONIUS not in document["works"]


def test_retired_registry_reference_cannot_keep_a_servable_whole_volume(tmp_path, identities):
    registry = historical_registry(identities)
    original = registry.works[PLATONIUS]
    original_aliases = deepcopy(original.aliases)
    reviewed.register_reviewed_manifestations(registry, tmp_path)
    retired = registry.works[PLATONIUS]
    assert retired is original and retired.aliases == original_aliases
    assert retired.default_edition is None
    old_edition = retired.editions[PLATONIUS + "." + reviewed.DUBNER_HISTORICAL_EDITIONS[PLATONIUS]]
    assert not old_edition.servable and old_edition.storage != "primary"
    assert old_edition.year == 1855
    coverage = retired.coverage_composition
    assert coverage["primary_rows"] == coverage["analysis_tokens"] == 0
    assert "no single successor" in coverage["qualification"]
    assert coverage["components"][0]["path"] == reviewed.DUBNER_COMPARATIVE
    assert all(component["storage"] != "primary" for component in coverage["components"])


def test_metadata_cannot_readmit_the_retired_whole_volume(tmp_path, identities, monkeypatch):
    values = deepcopy(identities)
    values[PLATONIUS] = deepcopy(values[ACHARNIANS])
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(metadata=lambda root: values))
    with pytest.raises(ValueError, match="retired.*cannot be a primary"):
        reviewed.register_reviewed_manifestations(Registry(), tmp_path)


def test_unapplied_review_does_not_retire_an_earlier_registry(tmp_path, identities, monkeypatch):
    registry = historical_registry(identities)
    original = registry.works[PLATONIUS].default_edition
    monkeypatch.setitem(sys.modules, "repair_dubner_scholias", SimpleNamespace(metadata=lambda root: {}))
    reviewed.register_reviewed_manifestations(registry, tmp_path)
    assert registry.works[PLATONIUS].default_edition == original
    assert registry.works[PLATONIUS].editions[original].servable
    assert reviewed.dubner_retired_work_slugs(tmp_path) == set()
