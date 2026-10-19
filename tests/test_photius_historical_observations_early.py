"""Check bounded scan observations against exact retained historical sources."""
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'photius_historical_observations_early',
    ROOT / 'scripts/photius_historical_observations_early.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def positions(text, needle):
    return [match.start() for match in re.finditer(re.escape(needle), text)]


def exact_position(text, needle, occurrence):
    hits = positions(text, needle)
    assert type(occurrence) is int and 0 <= occurrence < len(hits), (needle, hits, occurrence)
    return hits[occurrence]


@pytest.fixture(scope='module')
def originals():
    # This immutable earlier-layer preimage contains the complete original rows,
    # including existing correction history. Fresh-page voting did not rewrite
    # these retained historical rows.
    path = ROOT / 'data/corpus_changes/photius-bekker-readings/before-corpus.jsonl.gz'
    return {r['locus']: r for r in map(json.loads, gzip.decompress(path.read_bytes()).splitlines())}


@pytest.fixture(scope='module')
def library():
    path = ROOT / 'data/corpus_changes/photius-bekker-readings/source-library.json.gz'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_LIBRARY_SHA256
    return {s['id']: '\n'.join(b['text'] for b in s['blocks'])
            for s in json.loads(gzip.decompress(raw))['sections']}


def test_completed_scope_and_source_scan_pin():
    records = M.observations()
    assert len(records) == 325
    assert Counter(r['page'] for r in records) == {2: 118, 3: 105, 16: 102}
    assert len({r['locus'] for r in records}) == 148
    raw = (ROOT / 'data/corpus_changes/photius-bekker-readings/source-scan.pdf').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M.SOURCE_PDF_SHA256
    assert re.fullmatch('[0-9a-f]{64}', M.SOURCE_LIBRARY_SHA256)
    assert M.REVIEWED_AT


@pytest.mark.parametrize('record', M.observations(), ids=lambda r:
                         r['locus'] + ':' + r['original_text'] + ':' + str(r['occurrence']))
def test_exact_source_occurrence_and_full_original_row(record, originals, library):
    original = originals[record['locus']]
    frozen = deepcopy(original)
    assert not original.get('ocr_consensus') and not original.get('editorial_layer')
    assert not original.get('analysis_text')
    assert re.fullmatch(rf"helladius_chrestomathia_photius_bekker_v2_{record['page']:04d}[.]\d+",
                        record['locus'])
    exact_position(original['text'], record['original_text'], record['occurrence'])
    section = f"tlg4040-tlg001-local002-s{record['page'] + 277}"
    exact_position(library[section], record['corrected_text'], record['digital_occurrence'])
    assert record['original_text'] != record['corrected_text']
    box = record['source_region']
    assert len(box) == 4 and all(type(v) in (int, float) for v in box)
    assert 0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1
    assert 'Manual inspection' in record['evidence'] and 'not certified' in record['evidence']
    assert '/Users/' not in json.dumps(record, ensure_ascii=False)
    assert original == frozen


def test_original_spans_do_not_overlap_and_history_is_not_a_replacement(originals):
    grouped = {}
    for record in M.observations():
        original = originals[record['locus']]
        start = exact_position(original['text'], record['original_text'], record['occurrence'])
        grouped.setdefault(record['locus'], []).append((start, start + len(record['original_text'])))
        assert 'corrected_row' not in record and 'original_row' not in record
    for spans in grouped.values():
        ordered = sorted(spans)
        assert all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:]))
    # At least some reviewed rows already have an audit history. Observations
    # address only text spans and do not replace that complete row metadata.
    assert any(originals[locus].get('corrections') for locus in grouped)


def test_held_article_negative_and_initial_words_are_not_selected(originals):
    held, accepted = M.unresolved(), M.observations()
    assert len(held) == 5
    for item in held:
        assert item['original_text'] in originals[item['locus']]['text']
        assert item['reason']
        assert not any(r['locus'] == item['locus'] and r['original_text'] == item['original_text']
                       for r in accepted)
    rejected = {'τὸ ἐν ἁγίοις', 'ἐκ ἐπενεγκόντες τὸ σεσαρκωμένην',
                'ἐκεῖνον τὰς δύο φύσεις ἡ', 'ἑαυτὸν ἐκ εὐαγὲς'}
    assert not rejected & {r['corrected_text'] for r in accepted}
    assert not any(r['locus'].endswith('0016.32') and 'ὁκ εὐαγὲς' in r['original_text']
                   for r in accepted)


def test_source_tables_are_pure_and_callers_cannot_mutate_them(monkeypatch):
    def no_io(*args, **kwargs):
        raise AssertionError('An observation table must not read or rewrite corpus data')
    monkeypatch.setattr('builtins.open', no_io)
    monkeypatch.setattr(Path, 'write_text', no_io)
    monkeypatch.setattr(Path, 'write_bytes', no_io)
    first = M.observations()
    first[0]['source_region'][0] = .99
    assert M.observations()[0]['source_region'][0] != .99
    first[0]['corrected_text'] = 'changed'
    assert M.observations()[0]['corrected_text'] != 'changed'
    pending = M.unresolved()
    pending[0]['source_region'][0] = .99
    assert M.unresolved()[0]['source_region'][0] != .99


def test_historical_base_pins_complete_rows_before_application(originals):
    path = ROOT / 'data/corpus_changes/photius-bekker-historical-readings/before-corpus.jsonl.gz'
    # The production archive is available after application; before that stage,
    # the release corpus itself is the same exact compiler preimage.
    raw = gzip.decompress(path.read_bytes()) if path.exists() else (
        ROOT / 'data/corpus/photius.bibliotheca.jsonl').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '35573755011c78c4d4b050fe3998008783c392a787316ce1a4aab8016c3776d3'
    baseline = {r['locus']: r for r in map(json.loads, raw.splitlines())}
    for locus in {r['locus'] for r in M.observations()}:
        assert baseline[locus] == originals[locus]
