"""Duplicate-review credits supplement existing volume and edition metadata."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import repair_reviewed_duplicate_blocks as repair
import reviewed_duplicate_state as duplicate_state
import reviewed_duplicate_manifestations as credits
from source_identity import Registry


def registry_with_existing_credits():
    registry = Registry()
    for slug, author_name, edition, provider, license_value in (
        (repair.CYRIL, "Cyril", "migne-ocr-qwen36", "ocr", "PD"),
        (repair.HESYCHIUS, "Hesychius", "qwen36-hesychius_schmidt_masked", "ocr", "PD")):
        author = slug.split(".")[0]
        registry.mint_author(author_name, slug=author)
        registry.mint_work(author, "Existing canonical title", slug=slug)
        registry.mint_edition(slug, edition, "Existing base edition", provider=provider,
            license=license_value, source="https://example.org/base", make_default=True)
        registry.works[slug].coverage_composition = {
            "policy": "complementary-volume-union", "volumes": ["PG073", "PG074"],
            "counts": {"added_pg73": 528, "retained_pg74_john": 2578},
            "components": [{"edition": edition, "passages": 2578, "license": license_value}],
            "source_editions": [{"url": "https://example.org/base", "sha256": "a" * 64}],
            "unrelated": {"retain": [1, 2, 3]}}
    registry.mint_edition(repair.CYRIL, "calfa-pg73-5895ab908dd4", "Existing Calfa first volume",
        provider="cgpg", source="https://example.org/original-calfa-credit", license="CC-BY-4.0")
    return registry


def staged_admission(destination):
    audit_path = repair.AUDIT + "/changes.json"
    audit = json.loads((ROOT / audit_path).read_bytes())
    capture = json.loads((ROOT / repair.AUDIT / "source-evidence.json").read_bytes())
    names = {audit_path, repair.AUDIT + "/before.json.gz", repair.AUDIT + "/source-evidence.json",
        *audit["inputs"], *audit["outputs"], *(item["path"] for item in capture["files"]),
        *("scripts/" + name for name in audit["recipe_sha256"])}
    for name in names:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name in audit["outputs"]:
            path.write_bytes(duplicate_state.duplicate_postimage_bytes(ROOT, name))
        else:
            shutil.copyfile(ROOT / name, path)
    return destination


def test_registration_preserves_defaults_existing_editions_and_all_base_composition():
    registry = registry_with_existing_credits()
    before = {slug: asdict(work) for slug, work in registry.works.items()}
    result = credits.register(registry, ROOT)
    assert set(result) == {repair.CYRIL, repair.HESYCHIUS}
    for slug, original in before.items():
        work = registry.works[slug]
        assert work.default_edition == original["default_edition"]
        assert work.title == original["title"] and work.best_source == original["best_source"]
        assert {key: work.coverage_composition[key] for key in original["coverage_composition"]} == original["coverage_composition"]
        assert {key: asdict(work.editions[key]) for key in original["editions"]} == original["editions"]
        assert len(work.editions) == len(original["editions"]) + 2


def test_source_license_attribution_pins_and_counts_are_scoped_to_reviewed_passages():
    registry = registry_with_existing_credits()
    credits.register(registry, ROOT)
    for slug, provider, license_value, count, witnesses, original_tokens, scalar_tokens in (
        (repair.CYRIL, "cgpg", "CC-BY-4.0", 4, 8, 3537, 1666),
        (repair.HESYCHIUS, "ocr", "PD", 1, 111, 452, 266)):
        work = registry.works[slug]
        primary = work.editions[slug + "." + repair.EDITION]
        secondary = work.editions[slug + "." + credits.WITNESS_EDITION]
        assert (primary.provider, primary.license, primary.storage) == (provider, license_value, "primary")
        assert (secondary.provider, secondary.license, secondary.storage) == (provider, license_value, "secondary")
        review = work.coverage_composition["later_duplicate_review"]
        assert review["counts"]["primary_rows"] == count
        assert review["counts"]["literal_witness_rows"] == witnesses
        assert review["counts"]["original_greek_tokens"] == original_tokens
        assert review["counts"]["analysis_greek_tokens"] == scalar_tokens
        assert len(review["groups"]) == count
        component, literal = review["components"]
        assert component["passages"] == len(component["loci"]) == count
        assert literal["passages"] == witnesses
        assert literal["path"] == f"data/corpus_secondary/{slug}.reviewed-duplicate-witnesses.jsonl"
        assert literal["counts_toward_primary_frequency"] is False
        audit = json.loads((ROOT / repair.AUDIT / "changes.json").read_bytes())
        assert review["authority"]["sha256"] == repair.sha((ROOT / repair.AUDIT / "changes.json").read_bytes())
        assert component["source_pins"][f"data/corpus/{slug}.jsonl"] == audit["inputs"][f"data/corpus/{slug}.jsonl"]
        assert component["source_preimage_archive"]["sha256"] == audit["before_sha256"]
        assert literal["sha256"] == audit["outputs"][literal["path"]]
        assert len(review["sources"]) == 1 and len(review["sources"][0]["sha256"]) == 64
        if slug == repair.CYRIL:
            assert primary.source.startswith("https://raw.githubusercontent.com/calfa-co/")
            assert "Calfa" in review["attribution"]
            assert review["upstream_texts"][0]["license"] == "CC-BY-4.0"
            assert literal["original_editions"] == ["calfa-pg73-5895ab908dd4"]
        else:
            assert primary.source == "https://archive.org/details/hesychiialexand00schmgoog"
            assert not review["upstream_texts"]
            assert literal["original_editions"] == ["qwen36-hesychius_schmidt_masked"]


def test_registration_is_byte_stable_and_never_auto_fills_an_empty_default(tmp_path):
    registry = registry_with_existing_credits()
    registry.works[repair.HESYCHIUS].default_edition = None
    credits.register(registry, ROOT)
    assert registry.works[repair.HESYCHIUS].default_edition is None
    path = tmp_path / "registry.json"
    registry.save(path)
    first = path.read_bytes()
    registry = Registry.load(path)
    credits.register(registry, ROOT)
    registry.save(path)
    assert path.read_bytes() == first
    for work in registry.works.values():
        assert len(work.coverage_composition["later_duplicate_review"]["components"]) == 2


def test_absent_admission_has_no_registry_side_effects(tmp_path):
    registry = registry_with_existing_credits()
    before = deepcopy(registry)
    assert credits.register(registry, tmp_path) == {}
    assert registry.works == before.works and registry.authors == before.authors


def test_partial_authority_is_rejected(tmp_path):
    path = tmp_path / repair.AUDIT / "changes.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ValueError, match="predecessor archive"):
        credits.metadata(tmp_path)


def test_cached_metadata_is_invalidated_by_changed_source_evidence(tmp_path):
    root = staged_admission(tmp_path)
    assert credits.metadata(root)
    capture = json.loads((root / repair.AUDIT / "source-evidence.json").read_bytes())
    path = root / capture["files"][-1]["path"]
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="source evidence"):
        credits.metadata(root)


def test_missing_work_is_rejected_before_any_registry_mutation():
    registry = registry_with_existing_credits()
    del registry.works[repair.HESYCHIUS]
    before = deepcopy(registry.works)
    with pytest.raises(ValueError, match="canonical registry Work"):
        credits.register(registry, ROOT)
    assert registry.works == before
