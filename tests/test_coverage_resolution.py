import json
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import coverage_resolution as coverage
from build_known_limitations import coverage_findings


def test_reviewed_but_unadmitted_scans_do_not_resolve_coverage():
    for slug in ("pappus-mathematics.synagoge", "apollonius-geom.conica", "cassius-dio.historiae-romanae"):
        value = coverage.resolution(ROOT, slug)
        if not (ROOT / "data/corpus_extension_index.json").exists():
            assert not value["complete"] and value["status"] == "open-coverage-work"
        assert value["publication"]["tracker_close_criterion"]


def test_missing_or_partial_photius_and_cyril_admissions_stay_open(tmp_path):
    for slug, relative, partial in [
        ("photius.bibliotheca", "photius-bekker-coverage/coverage.json", {"covered_authorial_scan_pages": 544}),
        ("cyrillus-theology.commentarii-in-joannem", "cyril-john-coverage/changes.json",
         {"counts": {"added_pg73": 528, "retained_pg74_john": 2578}}),
    ]:
        assert not coverage.resolution(tmp_path, slug)["complete"]
        target = tmp_path / "data/corpus_changes" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(partial))
        assert not coverage.resolution(tmp_path, slug)["complete"]


def test_cyril_coverage_survives_verified_duplicate_collation(monkeypatch):
    slug = "cyrillus-theology.commentarii-in-joannem"
    result = coverage.resolution(ROOT, slug)
    assert result["complete"]
    assert result["counts"]["added_pg73"] == 528
    review = result["later_duplicate_review"]
    assert review["counts"]["primary_rows"] == 4
    assert review["counts"]["literal_witness_rows"] == 8
    assert review["work_file_accounting"] == {
        "original_primary_rows": 3109, "current_primary_rows": 3105}
    import repair_reviewed_duplicate_blocks as duplicate_review
    monkeypatch.setattr(duplicate_review, "historical_bytes", lambda *args: b"wrong predecessor\n")
    with pytest.raises(ValueError, match="primary text or preserved witness changed"):
        coverage.resolution(ROOT, slug)


def test_mathematical_resolution_preserves_every_historical_citation():
    for slug, count in [("pappus-mathematics.synagoge", 304), ("apollonius-geom.conica", 57)]:
        assert coverage._check_mathematical_citations(ROOT, slug)["preserved_historical_citations"] == count


def test_coverage_partition_never_labels_pending_pages_as_resolved():
    pending = {"complete": False, "status": "open-coverage-work"}
    repaired = {"complete": True, "status": "coverage-repaired-with-transmission-qualification",
                "qualification": "Ancient losses remain; all reviewed surviving pages are admitted."}
    cases = [{"slug": str(i), "edition": {"id": i}, "resolution": value,
        "historical_status": "partial-volume", "status": value["status"], "evidence": ["checked scan"],
        "issue": f"https://example.org/issues/{i}", "corpus_file_sha256": "a" * 64}
        for i, value in enumerate([pending, repaired])]
    active, resolved = coverage_findings(cases)
    assert [value["slug"] for value in active] == ["0"]
    assert [value["slug"] for value in resolved] == ["1"]
    assert resolved[0]["historical_status"] == "partial-volume"


def test_changed_archived_word_network_cannot_count_as_completed_admission(tmp_path):
    from ingest_scan_coverage import verify_integrity, sha
    directory = tmp_path / "audit"
    directory.mkdir()
    manifest = b'{"pages": []}'
    (directory / "manifest.json").write_bytes(manifest)
    (directory / "word-networks.json.gz").write_bytes(b"changed")
    (directory / "changes.json").write_text(json.dumps({"manifest_sha256": sha(manifest),
        "word_networks_sha256": sha(b"original")}))
    with pytest.raises(ValueError, match="word network changed"):
        verify_integrity(directory, tmp_path)


def photius_fresh_fixture(tmp_path):
    manifests = [{"pages": [{"id": "photius-bekker-0013"}, {"id": "photius-bekker-0014"}]}]
    report = {"fresh_ocr_files": [], "reviewed_retries": [{"page_id": "photius-bekker-0050", "supplements": []}]}
    inputs, models = [], {}
    for number in (6, 8):
        raw = json.dumps({"model": f"qwen3.{number}", "revision": "pinned"}).encode()
        metadata = json.loads(raw)
        report["fresh_ocr_files"].append({"sha256": hashlib.sha256(raw).hexdigest(), **metadata})
        pages = {page["id"]: {} for request in manifests for page in request["pages"]}
        inputs.append((raw, metadata, pages))
        models[(metadata["model"], metadata["revision"])] = pages
    def prepare(root, supplied_report, requests):
        assert root == tmp_path and supplied_report is report and requests == manifests
        return inputs, models, [{"canonical_review": "source-verified retries and supplements"}]
    return manifests, report, prepare


def test_photius_resolution_delegates_all_report_pins_to_canonical_validator(tmp_path):
    manifests, report, prepare = photius_fresh_fixture(tmp_path)
    models = coverage._photius_fresh_witnesses(tmp_path, report, manifests, prepare)
    assert len(models) == 2 and all(len(rows) == 2 for rows in models.values())
    def strict_failure(*args, **kwargs):
        raise ValueError("changed retry supplement archive")
    with pytest.raises(ValueError, match="changed retry supplement"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, strict_failure)


def test_photius_resolution_rejects_forged_original_identity_or_incomplete_models(tmp_path):
    manifests, report, prepare = photius_fresh_fixture(tmp_path)
    def forged(*args, **kwargs):
        inputs, models, evidence = prepare(*args, **kwargs)
        inputs[0][1]["revision"] = "different checkpoint"
        return inputs, models, evidence
    with pytest.raises(ValueError, match="retained witness identity"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, forged)
    manifests, report, prepare = photius_fresh_fixture(tmp_path)
    def incomplete(*args, **kwargs):
        inputs, models, evidence = prepare(*args, **kwargs)
        next(iter(models.values())).pop("photius-bekker-0014")
        return inputs, models, evidence
    with pytest.raises(ValueError, match="complete independent witnesses"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, incomplete)


def test_legacy_photius_physical_citation_is_not_a_combined_scan_position():
    mapping = {"logical_combined_position_offset": 277}
    legacy = {"locus": "helladius_chrestomathia_photius_bekker_v2_0255.6",
              "physical_refs": {"scan_page": 255, "printed_page": 520}}
    assert coverage._photius_coverage_position(legacy, mapping) == 532
    assert legacy["physical_refs"]["scan_page"] == 255
    fresh = {"locus": "photius_bekker1824_0245.1", "physical_refs": {"scan_page": 245}}
    assert coverage._photius_coverage_position(fresh, mapping) == 245
    with pytest.raises(ValueError, match="physical citation"):
        coverage._photius_coverage_position({"locus": "unreviewed.1"}, mapping)


def test_recovered_photius_positions_require_the_replayed_body_authority():
    mapping = {"logical_combined_position_offset": 277}
    row = {"locus": "photius_bekker1825_recovery_0066.left",
           "physical_refs": {"scan_page": 66}}
    with pytest.raises(ValueError, match="exactly replayed"):
        coverage._photius_coverage_position(row, mapping)
    with pytest.raises(ValueError, match="exactly replayed"):
        coverage._photius_coverage_position(row, mapping, {row["locus"]: 66})
    assert coverage._photius_coverage_position(row, mapping, {row["locus"]: 343}) == 343
