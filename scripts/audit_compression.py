"""Reuse deterministic gzip bytes without caching a filesystem validation.

Callers still read and verify their current files. Only compression of an exact
byte snapshot is memoized, with the zero timestamp used by the audit archives.
Keys retain digests rather than large uncompressed corpus buffers. Compressed
values have both a byte budget and an entry limit, local to this process.
"""
from __future__ import annotations

from collections import OrderedDict
import gzip
import hashlib
import operator
from threading import RLock
from typing import NamedTuple
import zlib


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    entries: int
    retained_bytes: int
    max_bytes: int
    max_entries: int


class GzipCache:
    def __init__(self, *, max_bytes=128 * 1024 * 1024, max_entries=128):
        max_bytes, max_entries = operator.index(max_bytes), operator.index(max_entries)
        if max_bytes < 0 or max_entries < 0:
            raise ValueError("Cache limits cannot be negative")
        self.max_bytes = max_bytes
        self.max_entries = max_entries
        self._values = OrderedDict()
        self._retained_bytes = self._hits = self._misses = 0
        self._lock = RLock()

    def compress(self, data, *, compresslevel=9):
        # Snapshot mutable buffers; reject integers rather than bytes(n)'s
        # unrelated interpretation as a request for n zero bytes.
        raw = data if type(data) is bytes else memoryview(data).tobytes()
        level = operator.index(compresslevel)
        compressor = gzip.compress
        # A replaced codec must not inherit the previous codec's cached result.
        recipe = (compressor, getattr(compressor, "__code__", None),
                  zlib.compress, zlib.ZLIB_RUNTIME_VERSION, level)
        key = (recipe, len(raw), hashlib.sha256(raw).digest())
        with self._lock:
            if key in self._values:
                self._hits += 1
                self._values.move_to_end(key)
                return self._values[key]
            self._misses += 1
        value = bytes(compressor(raw, compresslevel=level, mtime=0))
        with self._lock:
            if (not self.max_entries or len(value) > self.max_bytes
                    or key in self._values):
                return value
            while self._values and (len(self._values) >= self.max_entries
                    or self._retained_bytes + len(value) > self.max_bytes):
                _, removed = self._values.popitem(last=False)
                self._retained_bytes -= len(removed)
            self._values[key] = value
            self._retained_bytes += len(value)
        return value

    def cache_info(self):
        with self._lock:
            return CacheInfo(self._hits, self._misses, len(self._values),
                self._retained_bytes, self.max_bytes, self.max_entries)

    def cache_clear(self):
        with self._lock:
            self._values.clear()
            self._retained_bytes = self._hits = self._misses = 0


_CACHE = GzipCache()


def compress_gzip(data, *, compresslevel=9):
    """Return the exact gzip.compress(data, compresslevel, mtime=0) bytes."""
    return _CACHE.compress(data, compresslevel=compresslevel)
