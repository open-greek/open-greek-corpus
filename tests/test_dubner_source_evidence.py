"""Source evidence must reproduce the reviewed scans and reject artifact drift."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_dubner_sources as capture


@pytest.fixture
def small_bundle(tmp_path, monkeypatch):
    # Keep integrity tests independent of the optional renderer and large scans.
    image = b"retained full-page evidence fixture"
    monkeypatch.setattr(capture, "RETAINED_IMAGES", (
        ("toronto", 43, hashlib.sha256(image).hexdigest()),
    ))
    image_path = tmp_path / capture.image_path("toronto", 43)
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image)
    (tmp_path / capture.INVENTORY).write_bytes(capture.json_bytes(capture.inventory()))
    (tmp_path / capture.MANIFEST).write_bytes(capture.json_bytes(capture.expected_manifest()))
    return tmp_path


def test_offline_check_needs_neither_pdf_renderer_nor_source_cache(small_bundle, monkeypatch):
    monkeypatch.setitem(sys.modules, "pymupdf", None)
    monkeypatch.setattr(capture, "urlopen", lambda *a, **kw: pytest.fail("network access"))
    assert len(capture.check(small_bundle)["sources"]) == 2


@pytest.mark.parametrize("relative", [capture.image_path("toronto", 43), capture.INVENTORY])
def test_changed_or_missing_retained_evidence_fails(small_bundle, relative):
    path = small_bundle / relative
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Changed|differs"):
        capture.check(small_bundle)
    path.unlink()
    with pytest.raises((OSError, ValueError)):
        capture.check(small_bundle)


def test_manifest_cannot_redirect_to_an_unreviewed_scan_or_external_file(small_bundle):
    path = small_bundle / capture.MANIFEST
    data = json.loads(path.read_bytes())
    data["sources"][0]["sha256"] = "0" * 64
    data["files"][0]["path"] = "../../outside.json"
    path.write_bytes(capture.json_bytes(data))
    with pytest.raises(ValueError, match="manifest differs"):
        capture.check(small_bundle)


def test_inventory_is_regenerated_from_reviewed_observations(small_bundle, monkeypatch):
    units = deepcopy(capture.PROLEGOMENA_UNITS)
    units[0]["work"] = "wrong-author"
    monkeypatch.setattr(capture, "PROLEGOMENA_UNITS", units)
    with pytest.raises(ValueError, match="manifest differs"):
        capture.check(small_bundle)


def test_wrong_supplied_pdf_is_rejected_without_network_or_output_changes(tmp_path, monkeypatch):
    path = tmp_path / "changed.pdf"
    path.write_bytes(b"not the pinned scan")
    monkeypatch.setattr(capture, "urlopen", lambda *a, **kw: pytest.fail("network access"))
    with pytest.raises(ValueError, match="Changed toronto source PDF"):
        capture.resolve_pdf(capture.SOURCES[0], path, tmp_path / "cache")
    assert not (tmp_path / capture.AUDIT_DIR).exists()


def test_wrong_renderer_cannot_replace_retained_evidence(small_bundle, monkeypatch):
    before = (small_bundle / capture.MANIFEST).read_bytes()
    monkeypatch.setitem(sys.modules, "pymupdf", SimpleNamespace(VersionBind="unreviewed"))
    with pytest.raises(ValueError, match="requires reviewed PyMuPDF"):
        capture.capture(small_bundle)
    assert (small_bundle / capture.MANIFEST).read_bytes() == before
    capture.check(small_bundle)


def test_review_inventory_accounts_for_both_scans_and_every_play_transition():
    pages = {(source, page) for source, page, _ in capture.RETAINED_IMAGES}
    assert len(pages) == len(capture.RETAINED_IMAGES) == 93
    assert {("toronto", p) for p in range(23, 42)} <= pages
    assert {("harvard", p) for p in range(24, 43)} <= pages
    assert len(capture.PLAY_BOUNDARIES) == 11
    for _, start, end, scholia, _ in capture.PLAY_BOUNDARIES:
        assert {("toronto", start), ("toronto", end), ("toronto", scholia)} <= pages
    manifest = capture.expected_manifest()
    assert len(manifest["files"]) == 94
    assert all(not Path(item["path"]).is_absolute() for item in manifest["files"])
    assert all(".." not in Path(item["path"]).parts for item in manifest["files"])
    assert b"/Users/" not in capture.json_bytes(manifest)
    assert b"/tmp/" not in capture.json_bytes(capture.inventory())
