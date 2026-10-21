from concurrent.futures import ThreadPoolExecutor
import gzip
from pathlib import Path
import random
import sys
import zlib

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_compression import GzipCache


def test_warm_compression_preserves_exact_archive_bytes(monkeypatch):
    original = gzip.compress
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(gzip, "compress", counted)
    cache = GzipCache()
    raw = "λόγος\n".encode() * 100
    assert cache.compress(raw) == original(raw, mtime=0)
    assert cache.compress(bytes(bytearray(raw))) == original(raw, mtime=0)
    assert calls == [1]
    assert cache.cache_info().hits == 1


def test_same_size_mutated_input_cannot_reuse_previous_bytes():
    cache = GzipCache()
    raw = bytearray(b"original")
    first = cache.compress(raw)
    raw[:] = b"modified"
    second = cache.compress(raw)
    assert first != second
    assert gzip.decompress(second) == raw
    assert cache.cache_info().misses == 2


def test_compression_recipe_is_part_of_cache_identity(monkeypatch):
    cache = GzipCache()
    raw = b"source evidence" * 100
    assert cache.compress(raw, compresslevel=1) == gzip.compress(raw, compresslevel=1, mtime=0)
    assert cache.compress(raw, compresslevel=9) == gzip.compress(raw, compresslevel=9, mtime=0)
    original = gzip.compress
    calls = []
    def replaced(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(gzip, "compress", replaced)
    assert cache.compress(raw) == original(raw, mtime=0)
    assert calls == [1]
    assert cache.cache_info().misses == 3


def test_replaced_zlib_backend_cannot_inherit_a_warm_result(monkeypatch):
    cache = GzipCache()
    raw = b"source evidence" * 100
    expected = cache.compress(raw)
    original = zlib.compress
    calls = []
    def replaced(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(zlib, "compress", replaced)
    assert cache.compress(raw) == expected
    assert calls == [1]
    assert cache.cache_info().misses == 2


def test_invalid_arguments_do_not_hit_a_valid_cache_entry():
    cache = GzipCache()
    cache.compress(b"source", compresslevel=1)
    with pytest.raises(TypeError):
        cache.compress(b"source", compresslevel=1.0)
    with pytest.raises(TypeError):
        cache.compress(10)
    with pytest.raises(zlib.error):
        cache.compress(b"source", compresslevel=100)
    assert cache.cache_info().entries == 1


def test_lru_eviction_obeys_both_limits():
    cache = GzipCache(max_bytes=55, max_entries=2)
    values = [bytes([i]) * 100 for i in range(3)]
    for raw in values[:2]:
        assert cache.compress(raw) == gzip.compress(raw, mtime=0)
    cache.compress(values[0])  # retain this entry rather than the second one
    cache.compress(values[2])
    info = cache.cache_info()
    assert info.retained_bytes <= 55 and info.entries == 2
    cache.compress(values[0])
    assert cache.cache_info().hits == 2
    cache.compress(values[1])
    assert cache.cache_info().misses == 4


def test_oversized_and_disabled_entries_are_not_retained():
    raw = random.Random(80).randbytes(1000)
    for cache in (GzipCache(max_bytes=50), GzipCache(max_entries=0), GzipCache(max_bytes=0)):
        assert cache.compress(raw) == gzip.compress(raw, mtime=0)
        assert cache.compress(raw) == gzip.compress(raw, mtime=0)
        assert cache.cache_info().entries == cache.cache_info().retained_bytes == 0
        assert cache.cache_info().misses == 2


def test_parallel_requests_preserve_byte_budget_and_clear():
    cache = GzipCache(max_bytes=100, max_entries=3)
    payloads = [bytes([i % 10]) * 100 for i in range(40)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(cache.compress, payloads))
    assert [gzip.decompress(raw) for raw in results] == payloads
    assert cache.cache_info().retained_bytes <= 100
    assert cache.cache_info().entries <= 3
    cache.cache_clear()
    assert cache.cache_info().hits == cache.cache_info().entries == 0
    assert cache.cache_info().retained_bytes == 0
