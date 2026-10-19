"""Occurrence corrections preserve exact originals and reject changed evidence."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_photius_historical_readings as authority
import repair_photius_historical_readings as layer


@pytest.fixture
def fixture_tree(tmp_path, monkeypatch):
    old = {'urn': 'photius.bibliotheca', 'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.2',
           'edition': 'historical', 'source': 'ocr', 'license': 'PD', 'text': 'ἡ Γώμης ἀρχὴ καὶ Γώμης.'}
    untouched = {**old, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.3', 'text': 'ἄλλο'}
    # Deliberately retain noncanonical JSON spacing in the unaffected row.
    before = (json.dumps(old, ensure_ascii=False)+'\n').encode() + (json.dumps(untouched, ensure_ascii=False, indent=None, separators=(',', ':'))+'\n').encode()
    monkeypatch.setattr(layer, 'BASE_SHA', layer.sha(before))
    changes = []
    for start in [2, 20]:
        start = old['text'].index('Γώμης', 0 if not changes else changes[-1]['end'])
        changes.append({'locus': old['locus'], 'original_row_sha256': layer.row_sha(old),
            'start': start, 'end': start+5, 'original_text': 'Γώμης', 'corrected_text': 'Ῥώμης',
            'digital_counterpart': {'path': layer.LIBRARY.as_posix(), 'sha256': layer.LIBRARY_SHA,
                'original_text': 'Ῥώμης'},
            'source': {'path': layer.SCAN.as_posix(), 'sha256': layer.SCAN_SHA, 'scan_page': 2,
                       'evidence': 'Direct inspection of the exact printed occurrence.'},
            'reviewed_at': '2026-10-19'})
    review = {'schema_version': 1, 'work': 'photius.bibliotheca',
              'input_corpus_sha256': layer.sha(before), 'reviewed_at': '2026-10-19', 'records': changes}
    monkeypatch.setattr(authority, 'build', lambda root: deepcopy(review))
    # Source hashes are verified independently; use small opaque fixture sources.
    for path, contents, constant in [(layer.SCAN, b'scan', 'SCAN_SHA'), (layer.LIBRARY, b'digital', 'LIBRARY_SHA')]:
        monkeypatch.setattr(layer, constant, layer.sha(contents))
        for change in changes:
            change['source' if constant == 'SCAN_SHA' else 'digital_counterpart']['sha256'] = layer.sha(contents)
        (tmp_path/path).parent.mkdir(parents=True, exist_ok=True); (tmp_path/path).write_bytes(contents)
    for path, raw in [(layer.CORPUS, before), (layer.REVIEW, layer.encode(review))]:
        (tmp_path/path).parent.mkdir(parents=True, exist_ok=True); (tmp_path/path).write_bytes(raw)
    return tmp_path, before, review


def test_exact_occurrences_untouched_bytes_and_reversible_lifecycle(fixture_tree):
    root, before, _ = fixture_tree
    audit = layer.apply(root)
    after = (root/layer.CORPUS).read_bytes()
    assert after.splitlines()[1] == before.splitlines()[1]
    row = json.loads(after.splitlines()[0])
    assert row['text'] == 'ἡ Ῥώμης ἀρχὴ καὶ Ῥώμης.'
    assert row['locus'] == json.loads(before.splitlines()[0])['locus']
    assert row['license'] == 'CC-BY-SA-4.0'
    assert 'ocr_consensus' not in row  # Partial review never certifies every word.
    assert audit['counts']['corrected_occurrences'] == 2
    assert audit['counts']['fully_assessed_rows'] == 0
    records = list(map(json.loads, gzip.decompress((root/layer.RECORDS).read_bytes()).splitlines()))
    assert records[0]['original_row'] == json.loads(before.splitlines()[0])
    assert layer.check(root) == audit
    layer.validate_projection(row, root)
    assert layer.restore_before_bytes(after, root) == before
    layer.undo(root); assert (root/layer.CORPUS).read_bytes() == before
    layer.apply(root); assert (root/layer.CORPUS).read_bytes() == after


@pytest.mark.parametrize('path', [layer.REVIEW, layer.SCAN, layer.LIBRARY])
def test_source_invalidation_does_not_prevent_exact_frozen_undo(fixture_tree, path):
    root, before, _ = fixture_tree
    layer.apply(root)
    (root/path).write_bytes(b'invalidated')
    with pytest.raises(ValueError):
        layer.check(root)
    layer.undo(root)
    assert (root/layer.CORPUS).read_bytes() == before


@pytest.mark.parametrize('field,value', [('start', 0), ('original_text', 'ἄλλο'),
    ('corrected_text', 'Γώμης'), ('original_row_sha256', '0'*64)])
def test_changed_span_or_original_is_rejected(fixture_tree, field, value):
    _, before, review = fixture_tree
    review['records'][0][field] = value
    with pytest.raises(ValueError):
        layer.plan(before, layer.encode(review))


def test_overlap_different_digital_reading_and_invented_identity_are_rejected(fixture_tree):
    _, before, review = fixture_tree
    variants = []
    repeated = deepcopy(review); repeated['records'].append(repeated['records'][0]); variants.append(repeated)
    changed = deepcopy(review); changed['records'][0]['digital_counterpart']['original_text'] = 'ῥώμης'; variants.append(changed)
    invented = deepcopy(review); invented['records'][0]['locus'] = 'missing'; variants.append(invented)
    for variant in variants:
        with pytest.raises(ValueError):
            layer.plan(before, layer.encode(variant))


def test_independent_reader_edits_block_check_apply_undo_and_projection(fixture_tree):
    root, _, _ = fixture_tree
    layer.apply(root)
    rows = list(map(json.loads, (root/layer.CORPUS).read_bytes().splitlines()))
    rows[0]['text'] += ' λάθος'
    (root/layer.CORPUS).write_bytes(b''.join((json.dumps(r, ensure_ascii=False)+'\n').encode() for r in rows))
    for action in (layer.check, layer.apply, layer.undo):
        with pytest.raises(ValueError):
            action(root)
    with pytest.raises(ValueError, match='occurrence audit'):
        layer.validate_projection(rows[0], root)


def test_exact_span_requires_explicit_disambiguation():
    with pytest.raises(ValueError, match='ambiguous'):
        authority.exact_span('ὁ καὶ ὁ', 'ὁ')
    assert authority.exact_span('ὁ καὶ ὁ', 'ὁ', 1) == (6, 7)
    for occurrence in (-1, 2, True):
        with pytest.raises(ValueError):
            authority.exact_span('ὁ καὶ ὁ', 'ὁ', occurrence)


def test_reconstruction_retains_ties_aliases_and_exact_alias_undo(fixture_tree):
    root, before, review = fixture_tree
    rows = list(map(json.loads, before.splitlines())); original = rows[1]
    group = {'page': 2, 'locus': 'photius_bekker1825_0002.reviewed-region',
        'replaces': [original['locus']], 'insert_after': rows[0]['locus'],
        'original_rows': [original], 'original_row_sha256': {original['locus']: layer.row_sha(original)},
        'scan_text': 'λόγος σπουδή.', 'digital_text': 'λόγος σπεδή.',
        'digital_counterpart': {'path': layer.LIBRARY.as_posix(), 'sha256': layer.LIBRARY_SHA,
            'section': 's279', 'original_text': 'λόγος σπεδή.'},
        'source': {'path': layer.SCAN.as_posix(), 'sha256': layer.SCAN_SHA},
        'source_region': [.1,.3,.8,.5], 'evidence': 'Complete bounded source region.',
        'transcription_convention': 'Expand constituent Greek ligature letters; retain differing readings.',
        'qualification': 'Source disagreement remains unresolved.'}
    review['reconstructions'] = [group]
    (root/layer.REVIEW).write_bytes(layer.encode(review))
    alias_before = b'{"schema_version":1,"aliases":{}}\n'
    (root/layer.ALIASES).write_bytes(alias_before)
    audit = layer.apply(root)
    after = (root/layer.CORPUS).read_bytes()
    new = json.loads(after.splitlines()[1])
    assert new['locus'] == group['locus']
    assert new['analysis_text'] == 'λόγος'
    assert 'σπουδή' in new['text'] and 'σπεδή' in new['text']
    assert new['ocr_consensus']['counts'] == {'agreement': 1, 'unresolved': 1}
    assert audit['counts']['replaced_fragment_rows'] == 1
    aliases = json.loads((root/layer.ALIASES).read_bytes())
    assert aliases['aliases']['photius.bibliotheca'][original['locus']]['locus'] == group['locus']
    archived = json.loads(gzip.decompress((root/layer.NETWORKS).read_bytes()))[group['locus']]
    assert [w['text'] for w in archived['ocr_consensus']['witnesses']] == [group['scan_text'], group['digital_text']]
    layer.validate_projection(new, root)
    assert layer.restore_before_alias_bytes((root/layer.ALIASES).read_bytes(), root) == alias_before
    layer.check(root)
    layer.undo(root)
    assert (root/layer.CORPUS).read_bytes() == before
    assert (root/layer.ALIASES).read_bytes() == alias_before
    layer.apply(root)
    assert (root/layer.CORPUS).read_bytes() == after
