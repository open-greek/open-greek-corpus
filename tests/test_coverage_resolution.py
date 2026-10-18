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


def photius_fresh_fixture(tmp_path, retry=False):
    manifests = [{"pages": [{"id": "photius-bekker-0013"}, {"id": "photius-bekker-0014"}]}]
    report = {"fresh_ocr_files": []}
    for number in (6, 8):
        raw = json.dumps({"model": f"qwen3.{number}", "revision": "pinned"}).encode()
        path = tmp_path / f"fresh-{number}.jsonl"
        path.write_bytes(raw)
        report["fresh_ocr_files"].append({"path": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
            **json.loads(raw)})
    if retry:
        def retained(name, raw):
            path = tmp_path / name
            path.write_bytes(raw)
            return {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}
        report["reviewed_retry"] = {
            "manifest": retained("retry-manifest.json", b'{"retry":"manifest"}'),
            "source_review": retained("retry-review.json", b'{"source":"verified strips"}'),
            "raw_files": [{**retained(f"retry-{number}.jsonl", str(number).encode()),
                "model": f"qwen3.{number}", "revision": "pinned"} for number in (6, 8)],
            "original_artifacts_sha256": ["original6", "original8"],
            "page_id": "photius-bekker-0013", "scan_page": 13}
    def prepare(paths, requests, *, retry_paths, retry_review):
        assert requests == manifests
        assert retry_paths == ([tmp_path / value["path"] for value in report["reviewed_retry"]["raw_files"]] if retry else [])
        assert retry_review == (tmp_path / "retry-review.json" if retry else None)
        inputs, models = [], {}
        for path in paths:
            raw = path.read_bytes()
            metadata = json.loads(raw)
            pages = {page["id"]: {} for request in requests for page in request["pages"]}
            inputs.append((raw, metadata, pages))
            models[(metadata["model"], metadata["revision"])] = pages
        evidence = None
        if retry:
            value = report["reviewed_retry"]
            evidence = {"manifest_sha256": value["manifest"]["sha256"],
                "source_review_sha256": value["source_review"]["sha256"],
                "review": {"original_artifacts_sha256": value["original_artifacts_sha256"]},
                "raw_files": [{"sha256": item["sha256"],
                    "metadata": {key: item[key] for key in ("model", "revision")}}
                    for item in value["raw_files"]]}
        return inputs, models, evidence
    return manifests, report, prepare


@pytest.mark.parametrize("retry", [False, True])
def test_photius_resolution_uses_canonical_original_and_retry_validation(tmp_path, retry):
    manifests, report, prepare = photius_fresh_fixture(tmp_path, retry)
    models = coverage._photius_fresh_witnesses(tmp_path, report, manifests, prepare)
    assert len(models) == 2 and all(len(rows) == 2 for rows in models.values())
    def strict_failure(*args, **kwargs):
        raise ValueError("failed original without a valid reviewed assembly")
    with pytest.raises(ValueError, match="failed original"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, strict_failure)
    if retry:
        (tmp_path / "retry-manifest.json").write_text("changed")
        with pytest.raises(ValueError, match="retry archive changed"):
            coverage._photius_fresh_witnesses(tmp_path, report, manifests, prepare)


def test_photius_resolution_rejects_forged_retry_identity_or_incomplete_models(tmp_path):
    manifests, report, prepare = photius_fresh_fixture(tmp_path, retry=True)
    def forged(*args, **kwargs):
        inputs, models, evidence = prepare(*args, **kwargs)
        evidence["raw_files"][0]["metadata"]["revision"] = "different checkpoint"
        return inputs, models, evidence
    with pytest.raises(ValueError, match="retry metadata differs"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, forged)
    def incomplete(*args, **kwargs):
        inputs, models, evidence = prepare(*args, **kwargs)
        next(iter(models.values())).pop("photius-bekker-0014")
        return inputs, models, evidence
    with pytest.raises(ValueError, match="complete independent witnesses"):
        coverage._photius_fresh_witnesses(tmp_path, report, manifests, incomplete)
