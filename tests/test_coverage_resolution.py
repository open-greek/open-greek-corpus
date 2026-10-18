import json
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
