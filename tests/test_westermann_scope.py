"""Source-scoped anthology routing retains all readings and rejects stale proof."""
import base64
from copy import deepcopy
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import repair_westermann_scope as repair
import westermann_manifestations as credits
import westermann_source_observations as observations
from source_identity import Registry


def install_sources(destination):
    capture = json.loads((ROOT / observations.CAPTURE_PATH).read_bytes())
    for name in (observations.CAPTURE_PATH, observations.REVIEW_PATH):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    # The evidence is immutable. A test that changes an image first replaces its
    # own symlink, so no shared source capture can be edited through a fixture.
    for item in capture["files"]:
        path = destination / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(ROOT / item["path"])
    for name in repair.recipe_pins():
        path = destination / "scripts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "scripts" / name, path)


@pytest.fixture(scope="module")
def frozen(tmp_path_factory):
    root = tmp_path_factory.mktemp("westermann-frozen")
    install_sources(root)
    authority = ROOT / repair.AUDIT / "changes.json"
    if authority.exists():
        audit = json.loads(authority.read_bytes())
        before = repair._before(ROOT, audit)
    else:
        before = {name: (ROOT / name).read_bytes() for name in repair.input_pins()}
    for name in repair.input_pins():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(before[name])
    repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    return root


@pytest.fixture
def applied(frozen, tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    install_sources(root)
    audit = json.loads((frozen / repair.AUDIT / "changes.json").read_bytes())
    for name in {*audit["outputs"], repair.AUDIT + "/changes.json", repair.AUDIT + "/before.json.gz"}:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(frozen / name, path)
    return root


def original_root(frozen, destination):
    destination.mkdir()
    install_sources(destination)
    before = repair._before(frozen)
    for name in repair.input_pins():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(before[name])
    return destination


def test_complete_source_scope_preserves_all_rows_characters_and_licenses(frozen):
    audit, before = repair.verify(frozen)
    assert (frozen / repair.LITERAL).read_bytes() == before[repair.PRIMARY]
    records = [json.loads(line) for line in gzip.decompress((frozen / repair.RECORDS).read_bytes()).splitlines()]
    originals = [json.loads(line) for line in before[repair.PRIMARY].splitlines()]
    assert len(records) == len(originals) == 7013
    assert {record["original_row"]["locus"] for record in records} == {row["locus"] for row in originals}
    destinations = {name: {row["locus"]: row for row in map(json.loads, (frozen / name).read_bytes().splitlines())}
        for name in audit["outputs"] if name.endswith(".jsonl")}
    for record in records:
        row = record["original_row"]
        assert record["original_text"] == record["corrected_text"] == row["text"]
        assert "".join(row["text"][part["start"]:part["end"]] for part in record["source_partitions"]) == row["text"]
        routed = [destinations[target["path"]][target["locus"]] for target in record["destinations"]]
        assert "".join(item["text"] for item in routed) == row["text"]
        assert all(item["source"] == "ocr" and item["license"] == "PD" for item in routed)
    counts = audit["counts"]
    assert counts["original_rows"] == counts["literal_rows"] == 7013
    assert sum(counts.get(role + "_greek_tokens", 0) for role in
               ("primary", "comparative", "held", "editorial")) == counts["original_greek_tokens"]
    assert len(audit["deduplication_evidence"]) == len(repair.EVIDENCE_PINS) == 28


def test_only_source_supported_bodies_enter_primary_counts_without_spelling_claims(frozen):
    audit, _ = repair.verify(frozen)
    definitions = repair.definitions()
    primary_slugs = {value["slug"] for value in definitions.values() if value["admission"] == "primary"}
    assert {Path(name).stem for name in audit["outputs"] if name.startswith("data/corpus/")} == primary_slugs
    assert repair.OLD in primary_slugs
    assert len(primary_slugs) == audit["counts"]["primary_works"]
    for name in audit["outputs"]:
        if not name.startswith("data/corpus/"):
            continue
        rows = [json.loads(line) for line in (frozen / name).read_bytes().splitlines()]
        for row in rows:
            assert row["source_role"] == "historical" and row["source_role_detail"] == "historical-body"
            assert row["analysis_text"] == row["text"]
            assert row["unreviewed_ocr_spellings"] is True
            # Catalog/provenance quality classifiers use correction stamps as
            # evidence of a spelling pass. Structural routing is not that pass.
            assert not row.get("corrections")
    anonymous = next(value for value in definitions.values() if value["author_name"] == "Anonymous")
    assert anonymous["author"] != "marcellinus"


def test_exact_undo_reapply_preserves_audit_and_unowned_evidence(applied):
    audit, before = repair.verify(applied)
    authority = (applied / repair.AUDIT / "changes.json").read_bytes()
    independent = next(iter(repair.EVIDENCE_PINS))
    path = applied / independent
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"later independently audited target bytes\n")
    repair.undo(applied)
    assert (applied / repair.PRIMARY).read_bytes() == before[repair.PRIMARY]
    assert not repair.active(applied) and repair.alias_fragment(applied) is None
    assert path.read_bytes() == b"later independently audited target bytes\n"
    assert all(not (applied / name).exists() for name in audit["outputs"] if name != repair.PRIMARY)
    repair.apply(applied)
    assert (applied / repair.AUDIT / "changes.json").read_bytes() == authority
    assert repair.verify(applied)[0] == audit
    assert path.read_bytes() == b"later independently audited target bytes\n"


def test_contradictory_frozen_reapply_timestamp_is_rejected(applied):
    repair.undo(applied)
    with pytest.raises(ValueError, match="cannot change its timestamp"):
        repair.apply(applied, recorded_at="different timestamp")


def test_missing_or_mistyped_comparative_target_is_rejected(frozen, monkeypatch):
    definitions = repair.definitions()
    definitions["homer-herodotean"]["canonical_target"] = "missing.primary"
    monkeypatch.setattr(repair, "definitions", lambda: definitions)
    with pytest.raises(ValueError, match="no frozen primary evidence"):
        repair.deduplication_evidence(repair._before(frozen))


def test_missing_declared_target_locus_is_rejected(frozen, monkeypatch):
    definitions = repair.definitions()
    definitions["photius-theopompus"]["related_primary_loci"] = ["unattested.locus"]
    monkeypatch.setattr(repair, "definitions", lambda: definitions)
    with pytest.raises(ValueError, match="source locus is missing"):
        repair.deduplication_evidence(repair._before(frozen))


def test_target_free_comparative_requires_explicit_recension_qualification(frozen, monkeypatch):
    definitions = repair.definitions()
    definitions["apollonius-a"].pop("admission_reason")
    monkeypatch.setattr(repair, "definitions", lambda: definitions)
    with pytest.raises(ValueError, match="qualified unaligned recension family"):
        repair.deduplication_evidence(repair._before(frozen))


@pytest.mark.parametrize("missing", [False, True])
def test_initial_apply_rejects_missing_or_changed_live_comparative_evidence(frozen, tmp_path, missing):
    root = original_root(frozen, tmp_path / "original")
    path = root / next(iter(repair.EVIDENCE_PINS))
    path.unlink() if missing else path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="input is missing|primary evidence changed"):
        repair.apply(root)
    assert not (root / repair.AUDIT / "changes.json").exists()


def test_joint_archive_and_audit_hash_forgery_cannot_change_evidence(applied):
    archive = applied / repair.AUDIT / "before.json.gz"
    before = json.loads(gzip.decompress(archive.read_bytes()))
    before[next(iter(repair.EVIDENCE_PINS))] = base64.b64encode(b"different target\n").decode()
    archive.write_bytes(gzip.compress(repair.encoded(before), mtime=0))
    authority = applied / repair.AUDIT / "changes.json"
    audit = json.loads(authority.read_bytes())
    audit["before_sha256"] = repair.sha(archive.read_bytes())
    authority.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="primary evidence changed"):
        repair.verify(applied)


def test_invented_non_null_output_preimage_cannot_be_restored_by_undo(applied):
    archive = applied / repair.AUDIT / "before.json.gz"
    before = json.loads(gzip.decompress(archive.read_bytes()))
    before[repair.COMPARATIVE] = base64.b64encode(b"invented preimage\n").decode()
    archive.write_bytes(gzip.compress(repair.encoded(before), mtime=0))
    authority = applied / repair.AUDIT / "changes.json"
    audit = json.loads(authority.read_bytes())
    audit["before_sha256"] = repair.sha(archive.read_bytes())
    authority.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="undo inventory changed"):
        repair.undo(applied)


def test_joint_output_and_audit_hash_forgery_fails_literal_replay(applied):
    path = applied / repair.COMPARATIVE
    path.write_bytes(path.read_bytes() + b" ")
    authority = applied / repair.AUDIT / "changes.json"
    audit = json.loads(authority.read_bytes())
    audit["outputs"][repair.COMPARATIVE] = repair.sha(path.read_bytes())
    authority.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="routing does not reproduce"):
        repair.verify(applied)


def test_changed_source_image_invalidates_cache_but_does_not_block_undo(applied):
    repair.checked_state(applied)
    capture = json.loads((applied / observations.CAPTURE_PATH).read_bytes())
    image = applied / capture["files"][0]["path"]
    original = image.read_bytes()
    image.unlink()  # replace the fixture symlink, never mutate the shared scan
    image.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="source image changed"):
        repair.checked_state(applied)
    repair.undo(applied)
    assert (applied / repair.PRIMARY).is_file()


def test_changed_recipe_is_rejected_and_exact_undo_remains_available(applied):
    recipe = applied / "scripts/repair_westermann_scope.py"
    recipe.write_bytes(recipe.read_bytes() + b"\n# changed recipe\n")
    with pytest.raises(ValueError, match="recipe source changed"):
        repair.verify(applied)
    repair.undo(applied)


def test_projection_rejects_marker_and_analysis_tampering(applied):
    row = json.loads((applied / repair.PRIMARY).read_bytes().splitlines()[0])
    assert repair.validate_projection(row, applied) == row["text"]
    for field in ("analysis_text", "westermann_scope_review", "edition"):
        changed = deepcopy(row)
        changed.pop(field)
        with pytest.raises(ValueError, match="lexical projection differs"):
            repair.validate_projection(changed, applied)


def test_cached_inventory_avoids_directory_walks_without_ignoring_declared_files(applied, monkeypatch):
    repair.checked_state(applied)

    def no_directory_walk(*args, **kwargs):
        raise AssertionError("Projection must not rediscover evidence with rglob")

    monkeypatch.setattr(Path, "rglob", no_directory_walk)
    row = json.loads((applied / repair.PRIMARY).read_bytes().splitlines()[0])
    repair.validate_projection(row, applied)
    path = applied / repair.PRIMARY
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="repaired output changed"):
        repair.validate_projection(row, applied)


def test_manifestation_registration_preserves_identity_and_is_idempotent(applied):
    registry = Registry()
    registry.mint_author("Marcellinus", slug="marcellinus")
    registry.mint_work("marcellinus", "Vita Thucydidis", slug=repair.OLD,
        aliases={"cts": "urn:cts:greekLit:tlg2585.tlg001", "wikidata": "Q19273831"})
    registry.mint_edition(repair.OLD, "migne-ocr-qwen36", "Former whole anthology",
        provider="ocr", license="PD", make_default=True)
    registry.mint_author("Unrelated", slug="unrelated")
    registry.mint_work("unrelated", "Unrelated work", slug="unrelated.work")
    unrelated = asdict(registry.works["unrelated.work"])
    result = credits.register(registry, applied)
    assert repair.OLD in result
    work = registry.works[repair.OLD]
    assert work.aliases["cts"] == "urn:cts:greekLit:tlg2585.tlg001"
    assert work.aliases["wikidata"] == "Q19273831"
    old = work.editions[repair.OLD + ".migne-ocr-qwen36"]
    assert not old.servable and old.storage == "audit"
    assert work.default_edition == repair.OLD + "." + repair.EDITION
    assert asdict(registry.works["unrelated.work"]) == unrelated
    for slug in result:
        current = registry.works[slug]
        edition = current.editions[current.default_edition]
        assert (edition.provider, edition.license, edition.storage) == ("ocr", "PD", "primary")
        assert edition.source == observations.SOURCE["url"]
        literal = current.coverage_composition["components"][1]
        assert literal["path"] == repair.LITERAL and not literal["counts_toward_primary_frequency"]
    state = {slug: asdict(work) for slug, work in registry.works.items()}
    credits.register(registry, applied)
    assert {slug: asdict(work) for slug, work in registry.works.items()} == state


def test_eustathius_reuses_canonical_author_without_merging_uncertain_attributions(applied):
    registry = Registry()
    registry.mint_author("Eustathius", slug="eustathius-philol", aliases={"wikidata": "Q453465"})
    result = credits.register(registry, applied)
    source_work = next(slug for slug, value in result.items()
        if value["author"] == "eustathius-thessalonicensis")
    work = registry.works[source_work]
    assert work.slug == source_work and work.author == "eustathius-philol"
    assert "eustathius-thessalonicensis" not in registry.authors
    assert registry.authors["eustathius-philol"].aliases["wikidata"] == "Q453465"
    assert work.coverage_composition["source_attribution"] == {
        "author_slug": "eustathius-thessalonicensis", "author_name": "Eustathius of Thessalonica"}
    assert work.coverage_composition["canonical_author"] == {"slug": "eustathius-philol", "name": "Eustathius"}
    definitions = repair.definitions()
    for key in ("antiphon-eudocia", "aristotle-ammonius"):
        value = definitions[key]
        assert registry.works[value["slug"]].author == value["author"]
        assert value["author"] not in ("eudocia-augusta", "ammonius-philosophy")
