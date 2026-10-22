"""Retained color captures stay tied to their original physical-page mapping."""
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_herodas_reading_sources as sources


@pytest.fixture
def retained(tmp_path):
    shutil.copytree(ROOT / sources.BUNDLE, tmp_path / sources.BUNDLE)
    return tmp_path


def test_retained_body_images_have_pinned_capture_identity():
    manifest = sources.check(ROOT)
    assert len(manifest["pages"]) == 35
    assert manifest["pages"]["72"]["printed_page"] == 2


def test_optional_native_image_rendering_preserves_capture_resolution():
    pytest.importorskip("PIL")
    assert sources.image(72).size == (1996, 3395)


def test_source_image_modification_is_rejected(retained):
    (retained / sources.BUNDLE / "page-0072.jp2").write_bytes(b"different capture")
    with pytest.raises(ValueError, match="page image changed"):
        sources.check(retained)


@pytest.mark.parametrize("field,value", [
    ("file", "../other.jp2"), ("rotate_clockwise", 0),
    ("printed_page", 3), ("crop_box", [0, 0, 1996, 3395]),
])
def test_manifest_cannot_redirect_a_physical_page(retained, monkeypatch, field, value):
    target = retained / sources.BUNDLE / "manifest.json"
    manifest = json.loads(target.read_bytes())
    manifest["pages"]["72"][field] = value
    raw = sources.encoded(manifest)
    target.write_bytes(raw)
    with pytest.raises(ValueError, match="pinned capture extraction"):
        sources.check(retained)
    # Even an accidentally revised manifest pin cannot change the frozen XML's
    # physical page, crop, or safe local filename.
    monkeypatch.setattr(sources, "MANIFEST_SHA256", sources.sha(raw))
    with pytest.raises(ValueError, match="mapping or crop changed"):
        sources.check(retained)


def test_scan_metadata_cannot_change_capture_alignment(retained):
    (retained / sources.BUNDLE / "scandata.xml").write_bytes(b"different metadata")
    with pytest.raises(ValueError, match="scan metadata changed"):
        sources.check(retained)
