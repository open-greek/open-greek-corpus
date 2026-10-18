"""Registry rebuilds preserve reviewed scope, source credits, and licenses."""
import hashlib
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import reviewed_manifestations as reviewed
from source_identity import Registry
from test_meibom_repair import fixture as meibom_fixture
import repair_meibom_work_assignments as meibom


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def registry(*slugs):
    result = Registry()
    for slug in slugs:
        author = slug.split(".")[0]
        result.mint_author(author, slug=author)
        result.mint_work(author, "Unqualified Work title", slug=slug)
        result.mint_edition(slug, "base", "Existing source edition", provider="first1k",
            source="https://example.org/base", license="CC-BY-SA-4.0", make_default=True)
    return result


def test_meibom_all_nine_credits_survive_rebuild_with_jahn_default(tmp_path, monkeypatch):
    old, fresh = meibom_fixture(tmp_path, monkeypatch, "jahn1882")
    meibom.run_repair(tmp_path, "apply", fresh)
    names = {row[2] for row in meibom.RANGES}
    reg = registry(*names)
    metadata = reviewed.register_reviewed_manifestations(reg, tmp_path)
    assert set(metadata) == names
    assert reg.works[meibom.OLD].default_edition == meibom.OLD + "." + meibom.JAHN_EDITION
    for slug in names:
        work = reg.works[slug]
        assert work.title == "Unqualified Work title"
        assert work.editions[slug + ".qwen36-meibom-1652-legacy"].storage == "secondary"
        assert work.editions[slug + ".qwen36-meibom-1652-legacy"].license == "PD"
        if slug != meibom.OLD:
            assert work.default_edition == slug + ".base"
    output = tmp_path / "registry.json"
    reg.save(output)
    before = output.read_bytes()
    restored = Registry.load(output)
    reviewed.register_reviewed_manifestations(restored, tmp_path)
    restored.save(output)
    assert output.read_bytes() == before
    with (tmp_path / f"data/corpus/{meibom.OLD}.jsonl").open("ab") as stream:
        stream.write(b" \n")
    with pytest.raises(ValueError, match="evidence changed"):
        reviewed.reviewed_manifestation_metadata(tmp_path)


def test_missing_already_served_musical_identities_use_crosswalk_and_primary(tmp_path):
    crosswalk = {}
    for n, slug in enumerate(reviewed.MUSICAL_IDENTITIES):
        crosswalk[slug] = {"cts": f"urn:cts:greekLit:tlg{2135+n}.tlg001"}
        put(tmp_path, "data/corpus/" + slug + ".jsonl", {
            "urn": slug, "edition": "1st1K-grc1", "source": "first1k", "license": "CC-BY-SA-4.0", "text": "λόγος"})
    put(tmp_path, "data/tlg_crosswalk.json", crosswalk)
    reg = Registry()
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    assert set(reg.works) == set(reviewed.MUSICAL_IDENTITIES)
    assert all(reg.works[slug].aliases["cts"] == crosswalk[slug]["cts"] for slug in crosswalk)
    raw = {"authors": {}, "works": {}}
    reviewed.ensure_musical_work_records(raw, tmp_path)
    assert set(raw["works"]) == set(crosswalk)
    assert all(w["default_edition"].endswith(".1st1K-grc1") for w in raw["works"].values())


def test_admission_replay_accepts_derived_registry_credits_without_losing_audited_fields(tmp_path, monkeypatch):
    old, fresh = meibom_fixture(tmp_path, monkeypatch, "jahn1882")
    path = tmp_path / "data/source_registry.json"
    document = json.loads(path.read_text())
    document["authors"] = {}
    for slug, work in document["works"].items():
        author = slug.split(".")[0]
        document["authors"][author] = {"name": author, "aliases": {}}
        work.update(author=author, title="Canonical Work title", tags=[], best_source="open_corpus")
        for key, edition in work["editions"].items():
            edition.update(name="Historical edition")
    put(tmp_path, "data/source_registry.json", document)
    meibom.run_repair(tmp_path, "apply", fresh)
    reg = Registry.load(path)
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    reg.save(path)
    meibom.run_repair(tmp_path, "check")


def scan_fixture(root, slug):
    audit_dir = "data/corpus_changes/scan-example"
    source = {"url": "https://example.org/scan.pdf", "sha256": "source-digest",
              "license": "public-domain", "citation": "Checked printed edition"}
    manifest_sha = put(root, audit_dir + "/manifest.json", {"sources": {"scan": source}, "pages": [
        {"id": "primary", "work": slug, "source": "scan"},
        {"id": "comparison", "work": slug, "source": "scan", "admission": "comparative-paratext"}]})
    extension = f"data/corpus_extensions/{slug}.jsonl"
    extension_sha = put(root, extension, b'{"scan_region_id": "primary", "text": "opaque retained corpus network"}\n')
    corpus = f"data/corpus/{slug}.jsonl"
    corpus_sha = put(root, corpus, b'{"text":"base"}\n{"text":"addition"}\n')
    # Only its compressed hash is needed; no decompression or voting is allowed.
    network_sha = put(root, audit_dir + "/word-networks.json.gz", b"opaque compressed network")
    put(root, audit_dir + "/changes.json", {"manifest_sha256": manifest_sha,
        "word_networks_sha256": network_sha,
        "outputs": {extension: extension_sha, corpus: corpus_sha},
        "admitted_extensions_sha256": {slug: extension_sha}, "changes": [
            {"work": slug, "region_id": "primary", "destination": "primary"}]})
    put(root, "data/corpus_extension_index.json", {"works": {slug: {
        "path": extension, "sha256": extension_sha, "audit": audit_dir + "/changes.json",
        "edition": "scan-consensus-2026-10-18"}}})


@pytest.mark.parametrize("slug", sorted(reviewed.SCAN_WORKS))
def test_scan_unions_preserve_base_credit_and_exclude_comparison_counts(tmp_path, slug):
    scan_fixture(tmp_path, slug)
    reg = registry(slug)
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    work = reg.works[slug]
    assert work.title == "Unqualified Work title"
    assert work.default_edition == slug + ".base"
    composition = work.coverage_composition
    assert composition["base_passages"] == composition["added_primary_regions"] == 1
    assert composition["comparative_regions"] == 1
    assert composition["components"][0]["license"] == "CC-BY-SA-4.0"
    assert composition["components"][1]["licenses"] == ["public-domain"]
    assert composition["source_editions"][0]["citation"] == "Checked printed edition"
    assert work.editions[slug + ".scan-consensus-2026-10-18"].license == "PD"
    (tmp_path / "data/corpus_changes/scan-example/word-networks.json.gz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="evidence changed"):
        reviewed.register_reviewed_manifestations(reg, tmp_path)


@pytest.mark.parametrize("first", ["main", "letter"])
def test_additive_scan_admissions_preserve_all_manifests_and_each_reading_digest(tmp_path, first):
    slug = "apollonius-geom.conica"
    scan_fixture(tmp_path, slug)
    extension = f"data/corpus_extensions/{slug}.jsonl"
    corpus = f"data/corpus/{slug}.jsonl"
    previous_path = "data/corpus_changes/scan-example/changes.json"
    previous = json.loads((tmp_path / previous_path).read_text())
    original = (tmp_path / extension).read_bytes()
    addition = {"scan_region_id": first + "-region", "text": "second unchanged reading"}
    added_bytes = (json.dumps(addition, ensure_ascii=False) + "\n").encode()
    extension_sha = put(tmp_path, extension, original + added_bytes)
    corpus_sha = put(tmp_path, corpus, b'{"text":"base"}\n' + original + added_bytes)
    directory = "data/corpus_changes/second-" + first
    source = {"url": "https://example.org/second.pdf", "sha256": "second-scan",
              "license": "PD", "citation": "Book IV opening letter"}
    manifest_sha = put(tmp_path, directory + "/manifest.json", {"sources": {"second": source},
        "pages": [{"id": addition["scan_region_id"], "work": slug, "source": "second"}]})
    network_sha = put(tmp_path, directory + "/word-networks.json.gz", b"second immutable network")
    latest = directory + "/changes.json"
    audit = {"manifest_sha256": manifest_sha, "word_networks_sha256": network_sha,
        "outputs": {extension: extension_sha, corpus: corpus_sha},
        "admitted_extensions_sha256": {slug: hashlib.sha256(added_bytes).hexdigest()},
        "changes": [{"work": slug, "region_id": addition["scan_region_id"], "destination": "primary"}]}
    put(tmp_path, latest, audit)
    entry = {"path": extension, "sha256": extension_sha, "audit": latest,
        "audits": [previous_path, latest], "edition": "scan-consensus-2026-10-18"}
    put(tmp_path, "data/corpus_extension_index.json", {"works": {slug: entry}})
    reg = registry(slug)
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    composition = reg.works[slug].coverage_composition
    assert composition["added_primary_regions"] == 2
    assert composition["base_passages"] == 1
    assert composition["comparative_regions"] == 1
    assert [a["path"] for a in composition["admission_audits"]] == [previous_path, latest]
    assert len(composition["scan_manifests"]) == len(composition["source_editions"]) == 2
    assert reg.works[slug].default_edition == slug + ".base"
    # Old whole-file hashes describe the earlier admission, not consolidation.
    assert previous["outputs"][extension] != extension_sha
    # Updating the current index cannot conceal a changed earlier reading.
    changed = original.replace(b"opaque retained", b"changed retained") + added_bytes
    entry["sha256"] = put(tmp_path, extension, changed)
    audit["outputs"][extension] = entry["sha256"]
    put(tmp_path, latest, audit)
    put(tmp_path, "data/corpus_extension_index.json", {"works": {slug: entry}})
    with pytest.raises(ValueError, match="readings changed after consolidation"):
        reviewed.register_reviewed_manifestations(reg, tmp_path)


def photius_fixture(root):
    slug = "photius.bibliotheca"
    directory = "data/corpus_changes/photius-bekker-coverage"
    corpus_sha = put(root, f"data/corpus/{slug}.jsonl", b'{"text":"opaque"}\n' * 4155)
    library_sha = put(root, directory + "/source-library-local002.json.gz", b"licensed raw source")
    fresh = []
    for i in [36, 38]:
        path = directory + f"/witnesses/qwen{i}.jsonl"
        digest = put(root, path, b"retained raw OCR")
        fresh.append({"path": path, "sha256": digest, "model": f"Qwen3.{i%10}", "revision": "pinned"})
    put(root, directory + "/coverage.json", {"work": slug, "original_body_sha256": "before",
        "new_corpus_sha256": corpus_sha, "covered_authorial_scan_pages": 545, "added_passages": 309,
        "historical_body_passages": 3846, "preserved_index_passages": 501,
        "added_scan_ranges": [[13, 278], [379, 421]], "retained_scan_ranges": [[279, 378], [422, 557]],
        "fresh_ocr_files": fresh, "source_scan": {"url": "https://example.org/bekker", "license": "PD"},
        "legacy_source": {"url": "https://example.org/bekker1825", "sha256": "legacy-scan"},
        "source_scan_exceptions": [{"logical_combined_position": 446, "authorial_printed_page": 434}],
        "source_library": {"license": {"url": "https://creativecommons.org/licenses/by-sa/4.0/", "attribution": "Source Library"},
            "url": "https://example.org/local002", "sha256": library_sha, "rights": {"credit": "Source Library"},
            "separate_api_notice": {"tdm_reservation": 1, "ai_training": "reserved"},
            "primary_body_comparison_counts": {"bounded": 200, "held": 84}},
        "edition_scope": "545 source pages; physical citations preserve the edition's transmission."})
    return slug


def test_photius_retains_licensed_voting_component_and_pd_body_idempotently(tmp_path):
    slug = photius_fixture(tmp_path)
    reg = registry(slug)
    reg.works[slug].editions[slug + ".base"].license = "PD"
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    default = reg.works[slug].editions[reg.works[slug].default_edition]
    assert default.license == "CC-BY-SA-4.0"
    components = reg.works[slug].coverage_composition["components"]
    assert components[0]["edition"] == slug + ".base"
    assert components[0]["license"] == "PD"
    assert components[2]["license"]["attribution"] == "Source Library"
    assert components[2]["separate_api_notice"]["tdm_reservation"] == 1
    assert components[3]["license"] == "CC-BY-4.0"
    assert components[2]["primary_body_comparison_counts"] == {"bounded": 200, "held": 84}
    assert reg.works[slug].coverage_composition["source_editions"][1]["sha256"] == "legacy-scan"
    assert reg.works[slug].coverage_composition["source_scan_exceptions"][0]["authorial_printed_page"] == 434
    output = tmp_path / "registry.json"
    reg.save(output)
    before = output.read_bytes()
    restored = Registry.load(output)
    reviewed.register_reviewed_manifestations(restored, tmp_path)
    restored.save(output)
    assert output.read_bytes() == before


def test_dio_digital_participation_preserves_licensed_credits_and_raw_source_hash(tmp_path):
    slug = "cassius-dio.historiae-romanae"
    scan_fixture(tmp_path, slug)
    directory = "data/corpus_changes/scan-example"
    raw = b'{"retained":"licensed digital source"}'
    component = {"id": "tlg0385.tlg001.local003", "volume": 7,
        "json_sha256": hashlib.sha256(raw).hexdigest(), "url": "https://example.org/local003",
        "license": "CC-BY-SA-4.0", "attribution": "Source Library",
        "source_rights": {"original_print": "public-domain"}, "separate_api_notice": {"tdm_reservation": 1}}
    path = directory + "/digital-tlg0385.tlg001.local003.json.gz"
    put(tmp_path, path, gzip.compress(raw, mtime=0))
    index_path = tmp_path / "data/corpus_extension_index.json"
    index = json.loads(index_path.read_text())
    index["works"][slug]["digital_components"] = [component]
    put(tmp_path, str(index_path.relative_to(tmp_path)), index)
    audit_path = tmp_path / directory / "changes.json"
    audit = json.loads(audit_path.read_text())
    audit["digital_sources"] = {component["id"]: component}
    put(tmp_path, str(audit_path.relative_to(tmp_path)), audit)
    reg = registry(slug)
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    work = reg.works[slug]
    assert work.editions[slug + ".scan-consensus-2026-10-18"].license == "CC-BY-SA-4.0"
    assert work.coverage_composition["digital_components"][0]["separate_api_notice"]["tdm_reservation"] == 1
    assert work.editions[slug + ".source-library-local003"].storage == "audit"
    put(tmp_path, path, gzip.compress(b"changed source", mtime=0))
    with pytest.raises(ValueError, match="digital source changed"):
        reviewed.register_reviewed_manifestations(reg, tmp_path)


def test_cyril_complementary_volume_licenses_and_boundary_counts_survive(tmp_path):
    slug = "cyrillus-theology.commentarii-in-joannem"
    corpus = f"data/corpus/{slug}.jsonl"
    digest = put(tmp_path, corpus, b'{"text":"opaque"}\n' * 3109)
    put(tmp_path, "data/corpus_changes/cyril-john-coverage/changes.json", {
        "inputs": {corpus: "old"}, "outputs": {corpus: digest},
        "counts": {"added_pg73": 528, "retained_pg74_john": 2578,
            "added_pg74_missing_leaves": 3, "title_paratext": 4, "held_other_works": 474},
        "evidence": {"source_url": "https://example.org/calfa", "source_license": "CC-BY-4.0",
            "source_sha256": "pinned", "attribution": "Calfa PG073", "reference_scans": [
                {"url": "https://example.org/PG073"}, {"url": "https://example.org/PG074"}]}})
    reg = registry(slug)
    reviewed.register_reviewed_manifestations(reg, tmp_path)
    work = reg.works[slug]
    assert work.default_edition == slug + ".base"
    assert work.coverage_composition["counts"]["added_pg73"] == 528
    assert work.editions[slug + ".calfa-pg73-5895ab908dd4"].license == "CC-BY-4.0"
    assert work.editions[slug + ".migne-pg74-gap-consensus-2026-10"].license == "PD"
    assert "does not reconstruct lost" in work.coverage_composition["qualification"]
