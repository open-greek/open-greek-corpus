"""Exact source-only occurrence bindings for the two unpaired historical leaves."""
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'photius_historical_observations_unpaired',
    ROOT / 'scripts/photius_historical_observations_unpaired.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
RECORDS = M.observations()


@pytest.fixture(scope='module')
def original_rows():
    # Reconstruct the released immediate preimage, including its two earlier
    # corrections on169.1, without depending on later live corpus changes.
    raw = gzip.decompress((ROOT / 'data/corpus_changes/photius-bekker-historical-readings/before-corpus.jsonl.gz').read_bytes())
    rows = {row['locus']: row for row in map(json.loads, raw.splitlines())}
    prior = gzip.decompress((ROOT / 'data/corpus_changes/photius-bekker-historical-readings/records.jsonl.gz').read_bytes())
    for record in map(json.loads, prior.splitlines()):
        if record.get('corrected_row'):
            rows[record['locus']] = record['corrected_row']
    return rows


def span(row, record):
    hits = list(re.finditer(re.escape(record['original_text']), row['text']))
    return hits[record.get('occurrence', 0)].span()


def test_pinned_source_and_scope():
    raw = (ROOT / 'data/corpus_changes/photius-bekker-readings/source-scan.pdf').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_PDF_SHA256
    assert M.REVIEW_SCOPE['physical_pages'] == [169, 170]
    assert M.REVIEW_SCOPE['printed_pages'] == [434, 435]
    assert 'unrelated' in M.REVIEW_SCOPE['source_disagreement']
    assert Counter(r['page'] for r in RECORDS) == {169: 92, 170: 162}
    assert len({r['locus'] for r in RECORDS}) == 49


@pytest.mark.parametrize('record', RECORDS,
    ids=[f"{r['locus']}-{i}" for i, r in enumerate(RECORDS)])
def test_exact_original_occurrence_and_source_only_qualification(record, original_rows):
    row = original_rows[record['locus']]
    digest = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    assert digest == record['original_row_sha256']
    assert not row.get('ocr_consensus') and not row.get('editorial_layer')
    start, end = span(row, record)
    assert row['text'][start:end] == record['original_text']
    assert record['corrected_text'] and record['corrected_text'] != record['original_text']
    assert record['scan_only'] is True
    assert not any(k in record for k in ('digital_text', 'digital_counterpart', 'digital_occurrence'))
    assert 'no digital counterpart' in record['evidence']
    assert 'unrelated' in record['qualification']
    assert record['reviewed_at'] == M.REVIEWED_AT
    assert record['raw_witnesses'][0]['text'] == record['original_text']
    x0, y0, x1, y1 = record['source_region']
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    assert 'ligatures' in record['transcription_convention']


def test_exact_occurrences_do_not_overlap(original_rows):
    occupied = {}
    for record in RECORDS:
        start, end = span(original_rows[record['locus']], record)
        assert not any(start < b and a < end for a, b in occupied.get(record['locus'], []))
        occupied.setdefault(record['locus'], []).append((start, end))


def test_distinct_repeated_occurrences_are_preserved():
    twins = [r for r in RECORDS if r['page'] == 170 and r['original_text'] == 'ἰσῶςιν']
    assert len(twins) == 2 and {r['occurrence'] for r in twins} == {0, 1}
    assert {r['corrected_text'] for r in twins} == {'ἔσωζον'}


def test_explicit_source_readings_are_not_grammatically_replaced():
    readings = {r['original_text']: r['corrected_text'] for r in RECORDS}
    assert readings['ἀνάπνοις'] == 'ἀνάπαυσις'
    assert readings['βελτίους τε ἡ βελτίστας'] == 'βελτίους τε καὶ βελτίστης'
    assert readings['τῷ Θῖι'] == 'τῷ θεῷ'
    assert readings['ἀγωνιώσ τε περιεδόθησεν'] == 'ἀγωνίᾳ τε περιεδρύφθη'


def test_uncertain_readings_are_exact_but_unselected(original_rows):
    held = M.unapplied_source_observations()
    assert len(held) == 14
    for record in held:
        assert record['original_text'] in original_rows[record['locus']]['text']
        assert record['classification'] == 'unresolved-source-reading'
        assert record['qualification']
        assert 'corrected_text' not in record
        assert not any(r['locus'] == record['locus'] and
            r['original_text'] == record['original_text'] for r in RECORDS)


def test_callers_cannot_mutate_source_observations():
    altered = M.observations()
    altered[0]['source_region'][0] = .99
    altered[0]['raw_witnesses'][0]['text'] = 'changed'
    assert M.observations()[0]['source_region'][0] == .235
    assert M.observations()[0]['raw_witnesses'][0]['text'] == RECORDS[0]['original_text']
