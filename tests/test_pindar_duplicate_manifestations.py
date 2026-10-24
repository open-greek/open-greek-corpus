"""Checked Pindar identities, edition credits and qualified chronology."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import repair_pindar_duplicate_primaries as repair
import pindar_duplicate_manifestations as credits
import build_registry
from source_identity import Registry


@pytest.fixture
def staged(tmp_path):
    audit = json.loads((ROOT / repair.AUDIT / "changes.json").read_bytes())
    names = {repair.AUDIT + "/changes.json", repair.AUDIT + "/before.json.gz",
        *(name for name, pin in audit["outputs"].items() if pin is not None),
        *("scripts/" + name for name in audit["recipe_sha256"]),
        "data/work_ids.json", "data/author_ids.json"}
    for name in names:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    return tmp_path


def test_four_exact_tei_identities_use_existing_collective_author_without_dates(staged):
    registry = Registry()
    registry.mint_author("Existing collective catalog name", slug=credits.AUTHOR)
    ledger_bytes = {name: (staged / "data" / name).read_bytes()
                    for name in ("work_ids.json", "author_ids.json")}
    result = credits.register(registry, staged)
    assert set(result) == {pair["canonical"] for pair in repair.PAIRS}
    assert set(registry.authors) == {credits.AUTHOR}
    assert registry.authors[credits.AUTHOR].name == "Existing collective catalog name"
    for slug, value in result.items():
        work = registry.works[slug]
        assert work.author == credits.AUTHOR
        assert work.title == value["source"]["title"]
        assert work.aliases["cts"] == value["edition_urn"].removesuffix(".1st1K-grc1")
        assert work.tags == []
        assert "composition" in value["attribution_qualification"]
    for name, raw in ledger_bytes.items():
        assert (staged / "data" / name).read_bytes() == raw


def test_primary_secondary_credits_and_retired_ids_match_verified_audit(staged):
    registry = Registry()
    result = credits.register(registry, staged)
    audit = repair.verify(staged)[0]
    for pair in repair.PAIRS:
        work = registry.works[pair["canonical"]]
        primary = work.editions[pair["canonical"] + ".1st1K-grc1"]
        secondary = work.editions[pair["canonical"] + "." + repair.SECONDARY_EDITION]
        assert (primary.provider, primary.license, primary.storage) == ("first1k", "CC-BY-SA-4.0", "primary")
        assert (secondary.provider, secondary.license, secondary.storage) == ("first1k", "CC-BY-SA-4.0", "secondary")
        assert primary.year == secondary.year == 1903  # edition year only
        assert primary.source == secondary.source == result[pair["canonical"]]["source"]["url"]
        assert primary.aliases["cts"] == "urn:cts:greekLit:" + pair["old"] + ".1st1K-grc1"
        review = work.coverage_composition["pindar_duplicate_review"]
        assert (review["canonical_id"], review["retired_source_id"]) == (pair["canonical_id"], pair["old_id"])
        assert review["retired_source"] == pair["old"]
        for component in review["components"]:
            assert component["sha256"] == audit["outputs"][component["path"]]
        assert review["components"][1]["independent_witness"] is False
        assert review["components"][1]["counts_toward_primary_frequency"] is False


@pytest.mark.parametrize("servable,storage,preserve", [(True, "primary", True), (False, "primary", False), (True, "secondary", False)])
def test_valid_defaults_and_unrelated_components_are_preserved(staged, servable, storage, preserve):
    registry = Registry()
    registry.mint_author("Collective", slug=credits.AUTHOR)
    slug = repair.PAIRS[0]["canonical"]
    registry.mint_work(credits.AUTHOR, "Existing title", slug=slug)
    previous = registry.mint_edition(slug, "other-edition", "Existing edition", servable=servable,
        license="CC-BY-SA-4.0", make_default=True)
    registry.works[slug].editions[previous].storage = storage
    registry.works[slug].coverage_composition = {"unrelated": {"retain": [1, 2, 3]}}
    credits.register(registry, staged)
    assert registry.works[slug].default_edition == (previous if preserve else slug + ".1st1K-grc1")
    assert registry.works[slug].coverage_composition["unrelated"] == {"retain": [1, 2, 3]}
    assert registry.works[slug].editions[previous].storage == storage


def test_registration_is_idempotent_and_corrupt_evidence_fails_closed(staged):
    registry = Registry()
    credits.register(registry, staged)
    state = {slug: asdict(work) for slug, work in registry.works.items()}
    credits.register(registry, staged)
    assert {slug: asdict(work) for slug, work in registry.works.items()} == state
    source = staged / repair.AUDIT / "sources" / (repair.PAIRS[0]["old"] + ".xml.gz")
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError):
        credits.register(Registry(), staged)


def test_oga_later_pass_preserves_source_readings_without_dating_units(staged, tmp_path, monkeypatch):
    registry = Registry()
    credits.register(registry, staged)
    upstream = json.loads((ROOT / "data/oga_dating.json").read_bytes())
    records = {pair["old"]: upstream["works"][pair["old"]] for pair in repair.PAIRS}
    assert all(record["century"] == -2 for record in records.values())
    path, report = tmp_path / "oga.json", tmp_path / "oga-report.json"
    path.write_text(json.dumps({"works": records}))
    monkeypatch.setattr(build_registry, "OGA_DATING", path)
    monkeypatch.setattr(build_registry, "OGA_DATING_REPORT", report)
    monkeypatch.setattr(build_registry, "OGA_DATING_ADJUDICATION", tmp_path / "absent-adjudication.json")
    build_registry.apply_oga_dating(registry)
    first = report.read_bytes()
    output = json.loads(first)
    assert output["_meta"]["counts"]["filled"] == 0
    assert output["_meta"]["counts"]["qualified_upstream_readings"] == 4
    for pair in repair.PAIRS:
        work = registry.works[pair["canonical"]]
        assert not any(tag.startswith(("century:", "era:")) for tag in work.tags)
        reading = work.coverage_composition["pindar_duplicate_review"]["upstream_date_readings"][0]
        assert reading["upstream_record"] == records[pair["old"]]
        assert reading["applied_to_unit"] is False
        assert reading["status"] == "unverified-unit-composition-date"
    state = {slug: asdict(work) for slug, work in registry.works.items()}
    credits.register(registry, staged)  # reviewed_manifestations --check must be stable too
    build_registry.apply_oga_dating(registry)
    assert {slug: asdict(work) for slug, work in registry.works.items()} == state
    assert report.read_bytes() == first


def test_chronology_guard_is_limited_to_verified_registered_pindar_units(tmp_path, monkeypatch):
    registry = Registry()
    registry.mint_author("Independent author", slug="independent")
    registry.mint_work("independent", "Independent work", slug="independent.work",
        aliases={"cts": "urn:cts:greekLit:tlg9999.tlg001"})
    path = tmp_path / "oga.json"
    path.write_text(json.dumps({"works": {"tlg9999.tlg001": {"century": 3}}}))
    monkeypatch.setattr(build_registry, "OGA_DATING", path)
    monkeypatch.setattr(build_registry, "OGA_DATING_REPORT", tmp_path / "report.json")
    monkeypatch.setattr(build_registry, "OGA_DATING_ADJUDICATION", tmp_path / "absent.json")
    build_registry.apply_oga_dating(registry)
    assert "century:3" in registry.works["independent.work"].tags
    assert credits.qualify_oga_date(registry, repair.PAIRS[0]["old"], {"century": -2}) is None
