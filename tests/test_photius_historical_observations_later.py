"""Validate source bindings, occurrence choices, and bounded review scope."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "photius_historical_observations_later",
    ROOT / "scripts/photius_historical_observations_later.py",
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.fixture(scope="module")
def originals():
    path = ROOT / "data/corpus_changes/photius-bekker-readings/before-corpus.jsonl.gz"
    return {
        row["locus"]: row
        for row in map(json.loads, gzip.decompress(path.read_bytes()).decode().splitlines())
    }


@pytest.fixture(scope="module")
def library():
    raw = (ROOT / "data/corpus_changes/photius-bekker-readings/source-library.json.gz").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_LIBRARY_SHA256
    data = json.loads(gzip.decompress(raw))
    return {
        section["id"]: "\n".join(block["text"] for block in section["blocks"] if block.get("text"))
        for section in data["sections"]
    }


def positions(text, needle):
    return [match.start() for match in re.finditer(re.escape(needle), text)]


def exact_position(text, needle, occurrence):
    hits = positions(text, needle)
    if occurrence is None:
        assert len(hits) == 1, (needle, hits)
        return hits[0]
    assert 0 <= occurrence < len(hits)
    return hits[occurrence]


def test_source_scan_pin():
    raw = (ROOT / "data/corpus_changes/photius-bekker-readings/source-scan.pdf").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_SHA256


@pytest.mark.parametrize("record", M.observations(), ids=lambda r: r["observation_id"])
def test_exact_original_and_digital_counterpart(record, originals, library):
    original = originals[record["locus"]]
    assert "ocr_consensus" not in original and "editorial_layer" not in original
    exact_position(original["text"], record["original_text"], record.get("occurrence"))
    exact_position(library[record["digital_section"]], record["digital_text"], record.get("digital_occurrence"))
    assert record["original_text"] != record["corrected_text"]
    assert record["corrected_text"].replace("-", "") == record["digital_text"]
    x0, y0, x1, y1 = record["source_region"]
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    assert record["evidence"]


def test_observations_do_not_overlap_or_patch_replaced_epilogue(originals):
    grouped = {}
    replaced = set(M.epilogue()["replaces"])
    for record in M.observations():
        assert record["locus"] not in replaced
        text = originals[record["locus"]]["text"]
        start = exact_position(text, record["original_text"], record.get("occurrence"))
        grouped.setdefault(record["locus"], []).append((start, start + len(record["original_text"])))
    for spans in grouped.values():
        for a, b in zip(sorted(spans), sorted(spans)[1:]):
            assert a[1] <= b[0]


def test_epilogue_preserves_complete_digital_and_all_old_ids(library, originals):
    e = M.epilogue()
    assert e["locus"] == "photius_bekker1825_0280.epilogue"
    assert len(e["replaces"]) == 13 and len(set(e["replaces"])) == 13
    assert all(locus in originals for locus in e["replaces"])
    assert e["insert_after"] not in e["replaces"]
    assert all(not locus.endswith((".24", ".25")) for locus in e["replaces"])
    source = library[e["digital_section"]]
    assert source.count(e["digital_text"]) == 1
    assert e["digital_text"].endswith("δόξα εἰς αἰῶνας αἰώνων. Ἀμήν.")
    assert e["scan_text"].count("Τέλος") == 1
    assert len(e["scan_text"].splitlines()) == 11
    assert "διανοῦντα" in e["scan_text"] and "διανοοῦντα" in e["digital_text"]
    assert "ϗ" in e["scan_text"] and "κὲ" in e["digital_text"]
    assert "σπουδὴ" in e["scan_text"] and "σπεδὴ" in e["digital_text"]
    assert "1623R" not in e["scan_text"]
    assert "unresolved" in e["source_uncertainties"][0]["evidence"]


def test_two_scan_only_observations_are_exact_independent_diagnostic_matches(originals):
    records = M.scan_only_observations()
    assert len(records) == 2
    path = ROOT / records[0]["diagnostic_file"]
    raw = path.read_bytes()
    predictions = [json.loads(line) for line in raw.decode().splitlines()]
    for record in records:
        assert "digital_section" not in record and "digital_text" not in record
        assert hashlib.sha256(raw).hexdigest() == record["diagnostic_file_sha256"]
        prediction = next(p for p in predictions if p.get("id") == record["diagnostic_id"])
        canonical = json.dumps(prediction, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(canonical).hexdigest() == record["diagnostic_record_sha256"]
        assert hashlib.sha256(prediction["raw_prediction"].encode()).hexdigest() == record["diagnostic_text_sha256"]
        assert prediction["image_sha256"] == record["diagnostic_image_sha256"]
        assert record["diagnostic_text"] == record["corrected_text"]
        assert prediction["raw_prediction"].count(record["diagnostic_text"]) == 1
        assert originals[record["locus"]]["text"].count(record["original_text"]) == 1


def test_pending_mapping_exception_is_not_authorized_as_a_correction():
    authorized = M.observations() + M.scan_only_observations()
    for pending in M.unapplied_source_observations():
        assert not any(
            record["locus"] == pending["locus"]
            and record["original_text"] == pending["original_text"]
            for record in authorized
        )


def test_callers_cannot_mutate_shared_review_table():
    first = M.observations()
    first[0]["source_region"][0] = 0.9
    assert M.observations()[0]["source_region"][0] != 0.9
