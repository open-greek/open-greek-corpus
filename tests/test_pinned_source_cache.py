import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_pinned_source as cache


def test_source_pins_match_the_published_measurements():
    for name, report in (("pg003-text", "pg003_heads.json"), ("pg003-geometry", "pg003_head_geometry.json")):
        witness = json.loads((ROOT / "data" / report).read_text())["witness"]
        assert cache.SOURCES[name]["path"] == witness["file"]
        assert cache.SOURCES[name]["sha256"] == witness["sha256"]


def test_missing_cache_downloads_once_and_rejects_independent_changes(tmp_path, monkeypatch):
    raw = b"pinned source bytes"
    monkeypatch.setitem(cache.SOURCES, "fixture", {"path": "cache/source.txt", "url": "https://example.org/source", "sha256": hashlib.sha256(raw).hexdigest()})
    calls = []
    def fetch(url, timeout):
        calls.append(url)
        return io.BytesIO(raw)
    target = cache.ensure_source("fixture", tmp_path, opener=fetch)
    assert target.read_bytes() == raw
    assert cache.ensure_source("fixture", tmp_path, opener=fetch) == target
    assert len(calls) == 1
    target.write_bytes(b"independent edit")
    with pytest.raises(ValueError, match="Cached source differs"):
        cache.ensure_source("fixture", tmp_path, opener=fetch)
    assert target.read_bytes() == b"independent edit"
    assert len(calls) == 1


def test_bad_download_never_publishes_a_partial_cache(tmp_path, monkeypatch):
    monkeypatch.setitem(cache.SOURCES, "fixture", {"path": "cache/source.txt", "url": "https://example.org/source", "sha256": "0" * 64})
    with pytest.raises(ValueError, match="Downloaded source differs"):
        cache.ensure_source("fixture", tmp_path, opener=lambda *a, **kw: io.BytesIO(b"wrong source"))
    assert list((tmp_path / "cache").iterdir()) == []
