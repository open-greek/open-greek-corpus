import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_scan_ocr as runner


def test_duplicate_page_identity_fails_before_inference(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"pages": [{"id": "one"}, {"id": "one"}]}))
    with pytest.raises(ValueError, match="Repeated scan page"):
        runner.run(SimpleNamespace(manifest=path, limit=None))


def test_cached_scan_must_match_the_source_pin(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "pymupdf", SimpleNamespace())
    expected = runner.sha(b"original scan")
    (tmp_path / (expected + ".pdf")).write_bytes(b"different scan")
    manifest = {"sources": {"source": {"sha256": expected}},
                "pages": [{"source": "source", "id": "one", "scan_page": 1}]}
    with pytest.raises(ValueError, match="Corrupt scan cache"):
        runner.prepare_images(manifest, tmp_path)


def test_invalid_crop_is_rejected_instead_of_reading_another_region(tmp_path, monkeypatch):
    class Document:
        def __len__(self):
            return 1
    monkeypatch.setitem(sys.modules, "pymupdf", SimpleNamespace(open=lambda _: Document()))
    expected = runner.sha(b"pinned scan")
    (tmp_path / (expected + ".pdf")).write_bytes(b"pinned scan")
    manifest = {"sources": {"source": {"sha256": expected}},
                "pages": [{"source": "source", "id": "one", "scan_page": 1,
                           "region": [0.8, 0, 0.2, 1]}]}
    with pytest.raises(ValueError, match="Invalid page region"):
        runner.prepare_images(manifest, tmp_path)
