"""Exact occurrence and witness bindings for the additional historical review."""

from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unicodedata

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "photius_historical_observations_continued",
    ROOT / "scripts/photius_historical_observations_continued.py",
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.fixture(scope="module")
def before_rows():
    raw = (ROOT / "data/corpus_changes/photius-bekker-historical-readings/before-corpus.jsonl.gz").read_bytes()
    return {
        row["locus"]: row
        for row in map(json.loads, gzip.decompress(raw).decode().splitlines())
    }


@pytest.fixture(scope="module")
def sections():
    raw = (ROOT / "data/corpus_changes/photius-bekker-readings/source-library.json.gz").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_LIBRARY_SHA256
    data = json.loads(gzip.decompress(raw))
    return {
        section["id"]: "\n".join(block["text"] for block in section["blocks"] if block.get("text"))
        for section in data["sections"]
    }


def locate(text, needle, occurrence=None):
    hits = list(re.finditer(re.escape(needle), text))
    if occurrence is None:
        assert len(hits) == 1, (needle, len(hits))
        return hits[0].span()
    assert 0 <= occurrence < len(hits), (needle, occurrence, len(hits))
    return hits[occurrence].span()


def letter_or_mark(character):
    return unicodedata.category(character)[0] in "LM"


def test_source_pin_and_review_scope():
    raw = (ROOT / "data/corpus_changes/photius-bekker-readings/source-scan.pdf").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_SHA256
    assert M.REVIEW_SCOPE["pages"] == [4, 5, 6]
    assert Counter(record["page"] for record in M.observations()) == {4: 95, 5: 111, 6: 113}
    assert "no whole-row" in M.REVIEW_SCOPE["certification"]


@pytest.mark.parametrize("record", M.observations(), ids=lambda r: r["observation_id"])
def test_exact_historical_target_and_bounded_digital_counterpart(record, before_rows, sections):
    row = before_rows[record["locus"]]
    assert "ocr_consensus" not in row and "editorial_layer" not in row
    locate(row["text"], record["original_text"], record.get("occurrence"))
    section = sections[record["digital_section"]]
    start, end = locate(section, record["digital_text"], record.get("digital_occurrence"))
    assert not start or not letter_or_mark(section[start - 1])
    assert end == len(section) or not letter_or_mark(section[end])
    assert record["corrected_text"] != record["original_text"]
    x0, y0, x1, y1 = record["source_region"]
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    assert "Only this occurrence" in record["evidence"]


def test_same_row_occurrences_are_disjoint(before_rows):
    intervals = {}
    ids = set()
    for record in M.observations():
        assert record["observation_id"] not in ids
        ids.add(record["observation_id"])
        start, end = locate(before_rows[record["locus"]]["text"], record["original_text"], record.get("occurrence"))
        intervals.setdefault(record["locus"], []).append((start, end))
    for spans in intervals.values():
        for first, second in zip(sorted(spans), sorted(spans)[1:]):
            assert first[1] <= second[0]


def test_source_and_digital_disagreements_remain_literal():
    records = M.observations()
    record = next(r for r in records if r["page"] == 5 and r["original_text"] == "οἰκοδὲν")
    assert record["corrected_text"] == "οἴκοθεν"
    assert record["digital_text"] == "οἰκείαν"
    record = next(r for r in records if r["page"] == 4 and r["original_text"] == "τραυολογεῖν")
    assert record["corrected_text"] == "τρανολογοῦσα"
    assert record["digital_text"] == "τρανολογῦσα"


def test_omitted_line_is_bounded_by_existing_prefix_and_exact_digital_window(sections):
    record = next(r for r in M.observations() if r["page"] == 6 and r["original_text"] == "μὲν φῦσιν")
    assert record["locus"].endswith("0006.29")
    assert record["corrected_text"] == "Χριστόν, ἕνα υἱόν, ἕνα κύριον ὁμολογοῦμεν. εἶτα καὶ μίαν μὲν φύσιν"
    assert "complete intervening printed line" in record["evidence"]
    assert record["digital_text"] in sections[record["digital_section"]]


def test_return_values_do_not_mutate_source_table():
    first = M.observations()
    first[0]["source_region"][0] = 0.99
    assert M.observations()[0]["source_region"][0] == .078
