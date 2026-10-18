"""Pin the inspected middle leaves to their exact retained source readings."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from photius_reading_windows_middle import (
    FIRST_FRAGMENTS,
    HEADER_PREFIXES,
    HELD_PREFIXES,
    HELD_SUFFIXES,
    IMAGE_SHAS,
    REGIONS,
    SPECS,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'data/corpus_changes/photius-bekker-coverage'
LIBRARY_SHA = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
NETWORK_SHA = 'a7f867b2c83cdec5ebd77ad04837cbcf6916289adcf2fb1c40047a69db51abe5'


@pytest.fixture(scope='module')
def library_texts():
    raw = (ARCHIVE / 'source-library-local002.json.gz').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == LIBRARY_SHA
    sections = json.loads(gzip.decompress(raw))['sections']
    return {
        int(section['label'].removeprefix('Page s')):
        '\n'.join(block['text'] for block in section['blocks'])
        for section in sections
    }


def test_only_complete_inspected_middle_range_is_registered():
    # Page153 already has a separately reviewed canonical authority.
    assert set(SPECS) == set(range(131, 226)) - {153}
    assert set(IMAGE_SHAS) == set(REGIONS) == set(SPECS)
    assert set(HELD_SUFFIXES) <= set(SPECS)
    assert set(HELD_PREFIXES) <= set(FIRST_FRAGMENTS) <= set(SPECS)
    for page, (_, _, evidence) in SPECS.items():
        assert evidence.strip()
        assert len(IMAGE_SHAS[page]) == 64
        assert set(IMAGE_SHAS[page]) <= set('0123456789abcdef')
        assert set(REGIONS[page]) == {'first', 'body', 'last'}
        for x0, y0, x1, y1 in REGIONS[page].values():
            assert 0 <= x0 < x1 <= 1
            assert 0 <= y0 < y1 <= 1


@pytest.mark.parametrize('page', sorted(SPECS))
def test_windows_address_original_codepoints_without_normalization(page, library_texts):
    text = library_texts[page]
    end, total, _ = SPECS[page]
    prefix = HELD_PREFIXES.get(page, '')
    suffix = HELD_SUFFIXES.get(page, '')
    assert len(text) == total
    assert 0 <= len(prefix) < end <= total
    assert text.startswith(prefix)
    assert text[end:] == suffix
    assert text[len(prefix):end].strip()


def test_literal_initial_suffixes_are_held_and_raw_text_remains(library_texts):
    assert HELD_PREFIXES == {212: 'σεθαι. ', 217: 'λαβεῖν '}
    assert library_texts[212].startswith('σεθαι. καὶ ἐπιλύει')
    assert library_texts[217].startswith('λαβεῖν τὸν ἡμῶν σωτῆρα')
    assert HELD_SUFFIXES[211] == ' ὀφθῆναι.'
    assert HELD_SUFFIXES[217] == ' συνεπομένης.'


def test_partial_digital_coverage_is_not_extended_to_the_leaf_end(library_texts):
    assert library_texts[171].endswith('τοῖς εὐσεβέσι τὸ ἀγώνισμα.')
    assert 'subsequent printed196 Ephraim' in SPECS[171][2]
    # The complete printed line missing from both fresh readings is observable
    # in this independent witness and is retained, without reconstructing words.
    assert library_texts[214].endswith("Ἰουδαίους καὶ Ἕλληνας πάντας ὑφ' ἁμαρτίαν εἶναι,")
    assert 214 not in HELD_SUFFIXES


def test_header_masks_are_exact_original_witness_prefixes():
    raw = (ARCHIVE / 'full-networks.json.gz').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == NETWORK_SHA
    networks = json.loads(gzip.decompress(raw))
    assert len(HEADER_PREFIXES) == 17
    for (page, model), prefix in HEADER_PREFIXES.items():
        assert model == 'Qwen/Qwen3.6-27B'
        witnesses = networks[str(page)]['ocr_consensus']['witnesses']
        witness, = [item for item in witnesses if item['model'] == model]
        assert witness['text'].startswith(prefix)
        assert prefix == witness['text'].split('\n\n', 1)[0] + '\n\n'
        assert prefix.endswith('\n\n')
