"""Later partial reviews must compose without weakening frozen release guards."""
from copy import deepcopy
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import repair_photius_historical_batches as layer
from audit_compression import _CACHE as compression_cache


PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0004.'


def stream(rows):
    return b''.join((json.dumps(row, ensure_ascii=False)+'\n').encode() for row in rows)


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    rows = [{'urn': 'photius.bibliotheca', 'locus': PREFIX+'1', 'text': 'πρὸ κακόν καὶ κακῶς τέλος',
             'source': 'ocr', 'license': 'PD'},
            {'urn': 'photius.bibliotheca', 'locus': PREFIX+'2', 'text': 'ἀκέραιον λοιπὸν',
             'source': 'ocr', 'license': 'PD'}]
    before = stream(rows)
    doc = pymupdf.open()
    for _ in range(4):
        page = doc.new_page(width=100, height=100)
        page.insert_text((15, 25), 'Source crop')
    scan = doc.tobytes(); doc.close()
    library = gzip.compress(layer.encode({'sections': [{'id': 'tlg4040-tlg001-local002-s281',
        'blocks': [{'text': 'πρὸ καλόν καὶ καλῶς τέλος ἀκήρατον ἀκήρατος νέον καὶ'}]}]}), mtime=0)
    monkeypatch.setattr(layer, 'BASE_SHA', layer.sha(before))
    monkeypatch.setattr(layer, 'SCAN_SHA', layer.sha(scan))
    monkeypatch.setattr(layer, 'LIBRARY_SHA', layer.sha(library))
    monkeypatch.setattr(layer, 'TABLES', ('fixture_batch_one', 'fixture_batch_two'))
    monkeypatch.setattr(layer, '_source_credit', lambda root: {'license': 'CC-BY-SA-4.0',
        'separate_api_notice': {'tdm_reservation': 1}})
    for path, raw in ((layer.CORPUS, before), (layer.SCAN, scan), (layer.LIBRARY, library)):
        (tmp_path/path).parent.mkdir(parents=True, exist_ok=True); (tmp_path/path).write_bytes(raw)
    return {'root': tmp_path, 'before': before, 'rows': rows, 'scan': scan, 'library': library}


def observation(original='κακόν', corrected='καλόν', **kwargs):
    return {'locus': PREFIX+'1', 'page': 4, 'original_text': original, 'corrected_text': corrected,
            'source_region': [.1, .1, .9, .8], 'evidence': 'The pinned crop shows this exact reading.', **kwargs}


def table(fixture, name, identity, observations, held=()):
    raw = (f"BATCH_ID = {identity!r}\nREVIEWED_AT = '2026-10-19T03:00:00Z'\n"
           f"def observations():\n    return {observations!r}\n"
           f"def unresolved():\n    return {list(held)!r}\n").encode()
    path = fixture['root']/f'scripts/{name}.py'
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    return raw


def authority(fixture, observations, identity='batch-one'):
    return layer.compile_review(fixture['before'], fixture['library'], fixture['scan'], observations,
        batch_id=identity, reviewed_at='2026-10-19T03:00:00Z',
        table_pin={'path': 'scripts/fixture.py', 'sha256': 'f'*64})


def test_compile_pins_exact_raw_offsets_digital_and_crop(fixture):
    review = authority(fixture, [observation()])
    item = review['records'][0]
    assert fixture['rows'][0]['text'][item['start']:item['end']] == 'κακόν'
    assert item['original_row_sha256'] == layer.row_sha(fixture['rows'][0])
    assert item['digital_counterpart']['original_text'] == 'καλόν'
    assert item['digital_counterpart']['section'].endswith('-s281')
    assert len(item['source']['image_sha256']) == 64
    assert review['input_corpus_sha256'] == layer.sha(fixture['before'])


@pytest.mark.parametrize('target', ['table', 'scan', 'library', 'records', 'before', 'corpus'])
def test_warm_compression_still_rejects_same_size_tampering_with_preserved_timestamps(fixture, target):
    compression_cache.cache_clear()
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    root = fixture['root']
    layer.apply(root)
    layer.check(root)
    hits = compression_cache.cache_info().hits
    layer.check(root)
    assert compression_cache.cache_info().hits > hits
    paths = layer.paths('batch-one')
    relative = {'table': paths['table'], 'scan': layer.SCAN, 'library': layer.LIBRARY,
                'records': paths['records'], 'before': paths['before'], 'corpus': layer.CORPUS}[target]
    path = root / relative
    stamp, raw = path.stat(), path.read_bytes()
    if target in {'library', 'records', 'before'}:
        # A valid gzip archive with identical payload but a different OS byte.
        changed = raw[:9] + bytes([raw[9] ^ 1]) + raw[10:]
        assert gzip.decompress(changed) == gzip.decompress(raw)
    elif target == 'table':
        changed = raw.replace(b'batch-one', b'batch-two')
    elif target == 'scan':
        changed = raw.replace(b'%PDF-1.', b'%PDF-2.', 1)
    else:
        changed = raw.replace('καλόν'.encode(), 'κακόν'.encode(), 1)
    assert changed != raw and len(changed) == len(raw)
    path.write_bytes(changed)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError):
        layer.check(root)


def test_mutating_a_replay_result_cannot_change_a_later_cached_replay(fixture):
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    root = fixture['root']
    layer.apply(root)
    outputs, audit = layer.build(root, batch_id='batch-one')
    expected = deepcopy(audit)
    outputs[layer.CORPUS] = b'independent mutation'
    audit['counts'].clear()
    replay, restored = layer.build(root, batch_id='batch-one')
    assert restored == expected
    assert replay[layer.CORPUS] == (root / layer.CORPUS).read_bytes()


def test_two_batches_exact_undo_reapply_and_memory_restore(fixture, monkeypatch):
    root = fixture['root']; before = fixture['before']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()], [{'reading': 'held only'}])
    first = layer.apply(root, batch_id='batch-one'); first_raw = (root/layer.CORPUS).read_bytes()
    first_archive = {p: (root/p).read_bytes() for p in layer.paths('batch-one').values()}
    table(fixture, 'fixture_batch_two', 'batch-two', [observation('κακῶς', 'καλῶς')])
    second = layer.apply(root, batch_id='batch-two'); second_raw = (root/layer.CORPUS).read_bytes()
    assert second['predecessor']['batch_id'] == 'batch-one'
    assert second['input_corpus_sha256'] == first['output_corpus_sha256']
    assert first['counts']['held_source_observations'] == 1
    assert layer.restore_before_bytes(second_raw, root) == before
    row = json.loads(second_raw.splitlines()[0])
    assert layer.restore_before_row(row, root) == fixture['rows'][0]
    assert len(row['historical_reading_batches']) == 2
    meta = layer.active_metadata(root)
    assert meta['counts']['unique_corrected_rows'] == meta['counts']['newly_corrected_rows'] == 1
    assert meta['counts']['reviewed_occurrences'] == 2
    assert all((root/p).read_bytes() == raw for p, raw in first_archive.items())
    assert len(layer.check(root)) == 2
    layer.undo(root); assert (root/layer.CORPUS).read_bytes() == first_raw
    monkeypatch.setattr(layer, 'TABLES', layer.TABLES+('fixture_batch_three',))
    with pytest.raises(ValueError, match='chain tip'):
        table(fixture, 'fixture_batch_three', 'batch-three', [observation('καλόν', 'νέον')])
        layer.build(root, batch_id='batch-three')
    layer.apply(root, batch_id='batch-two'); assert (root/layer.CORPUS).read_bytes() == second_raw
    layer.undo(root); layer.undo(root)
    assert (root/layer.CORPUS).read_bytes() == before
    with pytest.raises(ValueError, match='original order'):
        layer.apply(root, batch_id='batch-two')
    layer.apply(root, batch_id='batch-one'); layer.apply(root, batch_id='batch-two')
    assert (root/layer.CORPUS).read_bytes() == second_raw


def test_undo_survives_source_removal_and_current_table_invalidation(fixture):
    root = fixture['root']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    layer.apply(root, batch_id='batch-one')
    (root/'scripts/fixture_batch_one.py').write_text('invalid current source table')
    (root/layer.SCAN).unlink(); (root/layer.LIBRARY).unlink()
    with pytest.raises(ValueError, match='source table'):
        layer.check(root)
    assert layer.restore_before_bytes((root/layer.CORPUS).read_bytes(), root) == fixture['before']
    layer.undo(root)
    assert (root/layer.CORPUS).read_bytes() == fixture['before']


def test_partial_release_metadata_is_retained_and_not_double_counted(fixture, monkeypatch):
    rows = deepcopy(fixture['rows'])
    rows[0]['historical_reading_repair'] = {'schema': 'frozen-old', 'reviewed_occurrences': 4,
                                          'source_review': {'sha256': 'b'*64}}
    before = stream(rows); fixture['before'] = before
    (fixture['root']/layer.CORPUS).write_bytes(before)
    monkeypatch.setattr(layer, 'BASE_SHA', layer.sha(before))
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    layer.apply(fixture['root'], batch_id='batch-one')
    new = json.loads((fixture['root']/layer.CORPUS).read_bytes().splitlines()[0])
    assert new['historical_reading_repair'] == rows[0]['historical_reading_repair']
    assert layer.restore_before_row(new, fixture['root']) == rows[0]
    counts = layer.active_metadata(fixture['root'])['counts']
    assert counts['unique_corrected_rows'] == counts['previously_corrected_rows'] == 1
    assert counts['newly_corrected_rows'] == 0


def test_editorial_body_review_preserves_apparatus_and_excludes_source_ties(fixture, monkeypatch):
    from repair_photius_apparatus import lexical_segments
    rows = deepcopy(fixture['rows'])
    body = rows[0]['text']
    rows[0].update(analysis_text=body, editorial_layer={
        'schema': 'scan-reviewed-editorial-spans-v1', 'original_text': body+' apparatus',
        'body_spans': [{'start': 0, 'end': len(body), 'text': body}],
        'excluded_spans': [{'start': len(body), 'end': len(body)+10,
                            'original_text': ' apparatus', 'classification': 'critical-apparatus'}],
        'source_review': {'sha256': 'a'*64}, 'paratext': {'path': 'paratext.jsonl'},
    })
    fixture['before'] = stream(rows)
    (fixture['root']/layer.CORPUS).write_bytes(fixture['before'])
    monkeypatch.setattr(layer, 'BASE_SHA', layer.sha(fixture['before']))
    # An ordinary review still cannot replace an editorial projection.
    with pytest.raises(ValueError, match='lexical projection'):
        authority(fixture, [observation()])
    item = observation(digital_text='καλῶς', review_scope='retained-editorial-body')
    table(fixture, 'fixture_batch_one', 'batch-one', [item])
    layer.apply(fixture['root'], batch_id='batch-one')
    current = json.loads((fixture['root']/layer.CORPUS).read_bytes().splitlines()[0])
    assert current['editorial_layer'] == rows[0]['editorial_layer']
    assert lexical_segments(current, fixture['root']) == ['πρὸ ', ' καὶ κακῶς τέλος']
    assert 'apparatus' not in current['text'] and 'καλόν' not in current['analysis_text']
    assert layer.restore_before_row(current, fixture['root']) == rows[0]
    broken = deepcopy(current); broken['editorial_layer']['excluded_spans'] = []
    with pytest.raises(ValueError, match='postimage'):
        lexical_segments(broken, fixture['root'])
    layer.undo(fixture['root'])
    assert (fixture['root']/layer.CORPUS).read_bytes() == fixture['before']
    rows[0]['analysis_text'] = 'apparatus'
    fixture['before'] = stream(rows)
    with pytest.raises(ValueError, match='retained body spans'):
        authority(fixture, [item])


def test_contrary_word_ties_keep_agreement_and_all_raw_witnesses(fixture):
    review = authority(fixture, [observation('πρὸ κακόν καὶ κακῶς τέλος',
        'πρὸ καλόν καὶ καλῶς τέλος', digital_text='πρὸ καλόν καὶ καλῶς τέλος')])
    # A bounded independent reading disagrees at one word, while common words count.
    review['records'][0]['digital_counterpart']['original_text'] = 'πρὸ καλόν καὶ νέον τέλος'
    raw, changes, networks, counts = layer.plan(fixture['before'], layer.encode(review))
    row = json.loads(raw.splitlines()[0])
    assert '⟦' in row['text'] and 'καλῶς' in row['text'] and 'νέον' in row['text']
    assert 'πρὸ καλόν καὶ' in row['analysis_text'] and 'τέλος' in row['analysis_text']
    assert 'καλῶς' not in row['analysis_text'] and 'νέον' not in row['analysis_text']
    assert counts['unresolved_occurrences'] == 1
    witnesses = next(iter(networks.values()))['ocr_consensus']['witnesses']
    assert {w['text'] for w in witnesses} == {'πρὸ καλόν καὶ καλῶς τέλος', 'πρὸ καλόν καὶ νέον τέλος'}
    assert len(witnesses) == 2
    assert changes[0]['original_row'] == fixture['rows'][0]


def test_contrary_projection_blocks_false_bigrams_and_rebases_later_edits(fixture):
    root = fixture['root']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation('κακόν', 'καλόν', digital_text='καλῶς')])
    layer.apply(root, batch_id='batch-one')
    row = json.loads((root/layer.CORPUS).read_bytes().splitlines()[0])
    runs = layer.lexical_segments(row, root)
    assert len(runs) == 2 and runs[0] == 'πρὸ ' and runs[1] == ' καὶ κακῶς τέλος'
    table(fixture, 'fixture_batch_two', 'batch-two', [observation('πρὸ', 'νέον')])
    layer.apply(root, batch_id='batch-two')
    current = json.loads((root/layer.CORPUS).read_bytes().splitlines()[0])
    assert layer.lexical_segments(current, root)[0] == 'νέον '
    assert layer.restore_before_row(current, root) == fixture['rows'][0]


def test_prior_unresolved_spans_cannot_be_silently_selected(fixture):
    root = fixture['root']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation(digital_text='καλῶς')])
    layer.apply(root, batch_id='batch-one')
    table(fixture, 'fixture_batch_two', 'batch-two', [observation('καλόν', 'νέον')])
    with pytest.raises(ValueError, match='prior unresolved'):
        layer.build(root, batch_id='batch-two')


@pytest.mark.parametrize('change', ['tagged-text', 'removed-tags', 'records', 'audit'])
def test_tampered_postimages_or_frozen_artifacts_fail(fixture, change):
    root = fixture['root']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    layer.apply(root, batch_id='batch-one')
    if change in {'tagged-text', 'removed-tags'}:
        rows = list(map(json.loads, (root/layer.CORPUS).read_bytes().splitlines()))
        rows[0]['text'] += ' altered'
        if change == 'removed-tags':
            rows[0].pop('historical_reading_batches')
        (root/layer.CORPUS).write_bytes(stream(rows))
    elif change == 'records':
        (root/layer.paths('batch-one')['records']).write_bytes(gzip.compress(b'{}\n', mtime=0))
    else:
        path = root/layer.paths('batch-one')['audit']
        doc = json.loads(path.read_bytes()); doc['counts']['corrected_rows'] += 1
        path.write_bytes(layer.encode(doc))
    with pytest.raises(ValueError):
        layer.check(root)
    with pytest.raises(ValueError):
        layer.undo(root)


@pytest.mark.parametrize('kwargs,match', [
    ({'source_region': [0, .1, float('nan'), .5]}, 'rectangle'),
    ({'source_region': [0, .1, .8, 1.5]}, 'rectangle'),
    ({'evidence': ''}, 'source evidence'),
    ({'original_row_sha256': '0'*64}, 'row changed'),
    ({'digital_text': 'not in the source'}, 'absent or ambiguous'),
    ({'scan_text': 'κα-λόν'}, 'convention'),
    ({'scan_only': True}, 'qualification'),
    ({'scan_only': True, 'qualification': 'Reviewed only on scan', 'digital_text': 'καλόν'}, 'cannot hide'),
])
def test_invalid_source_reviews_reject(fixture, kwargs, match):
    with pytest.raises(ValueError, match=match):
        authority(fixture, [observation(**kwargs)])


def test_scan_only_is_explicit_not_an_automatic_digital_fallback(fixture):
    review = authority(fixture, [observation(corrected='source only', scan_only=True,
        qualification='The mapped digital scan is unrelated; this is a direct scan observation.')])
    assert review['records'][0]['digital_counterpart'] is None
    after, _, networks, counts = layer.plan(fixture['before'], layer.encode(review))
    assert 'source only' in json.loads(after.splitlines()[0])['text']
    assert networks == {} and counts['scan_only_occurrences'] == 1


def test_source_hyphen_join_keeps_literal_scan_and_convention(fixture):
    review = authority(fixture, [observation(scan_text='κα-λόν',
        transcription_convention='Join the source-confirmed internal printed line-end division.')])
    item = review['records'][0]
    assert item['source']['observed_text'] == 'κα-λόν'
    assert item['corrected_text'] == 'καλόν'
    assert item['source']['transcription_convention']


def test_overlaps_and_unknown_loci_reject(fixture):
    with pytest.raises(ValueError, match='overlap'):
        authority(fixture, [observation(), observation()])
    with pytest.raises(ValueError, match='existing retained'):
        authority(fixture, [observation(locus=PREFIX+'99')])


def test_repeated_digital_occurrences_require_explicit_index(fixture):
    with pytest.raises(ValueError, match='absent or ambiguous'):
        authority(fixture, [observation(corrected='καὶ')])
    review = authority(fixture, [observation(corrected='καὶ', digital_occurrence=1)])
    assert review['records'][0]['digital_counterpart']['start'] > 0


def test_quality_counts_unique_rows_across_old_and_new_layers():
    from build_ocr_quality_report import consensus_qualification
    row = {'historical_reading_repair': {'reviewed_occurrences': 3},
           'historical_reading_batches': [
               {'reviewed_occurrences': 2, 'scalar_corrections': 1, 'unresolved_occurrences': 1},
               {'reviewed_occurrences': 1, 'scalar_corrections': 1, 'unresolved_occurrences': 0}]}
    report = consensus_qualification([row, {}])
    assert report['historical_occurrence_review']['partially_corrected_rows'] == 1
    assert report['historical_occurrence_review']['corrected_occurrences'] == 5
    assert report['historical_occurrence_review']['reviewed_occurrences'] == 6
    assert report['historical_occurrence_review']['unresolved_occurrences'] == 1
    assert report['rows_with_counted_consensus'] == 0


def test_intra_word_unresolved_exclusion_does_not_count_false_fragments():
    text = 'πρὸ ἀ⟦φ ∥ β⟧αιρεῖ τέλος'
    start, end = text.index('⟦'), text.index('⟧')+1
    spans = layer._whole_word_exclusions(text, [{'start': start, 'end': end, 'text': text[start:end]}])
    assert layer._segments(text, spans) == ['πρὸ ', ' τέλος']


def test_reviewed_terminal_hyphen_fragment_keeps_display_but_never_counts(fixture):
    review = authority(fixture, [observation(corrected='ἐγκα-', scan_only=True,
        qualification='The physical source ends this retained row with a continued word.')])
    after, changes, _, counts = layer.plan(fixture['before'], layer.encode(review))
    row = json.loads(after.splitlines()[0])
    assert 'ἐγκα-' in row['text'] and 'ἐγκα' not in row['analysis_text']
    assert counts['scalar_corrections'] == counts['fragment_occurrences'] == 1
    assert counts['lexical_excluded_fragments'] == 1
    assert changes[0]['corrections'][0]['source_fragments'][0]['basis'] == 'reviewed-terminal-greek-hyphen'
    assert layer._segments(row['text'], row['historical_reading_batch_projection']['excluded_spans']) == [
        'πρὸ ', ' καὶ κακῶς τέλος']


@pytest.mark.parametrize('corrected,keyword', [('λόν καὶ', 'leading'), ('καλό', 'trailing')])
def test_intra_word_digital_windows_require_exact_fragment_qualification(fixture, corrected, keyword):
    with pytest.raises(ValueError, match='intra-word digital pointer'):
        authority(fixture, [observation(corrected=corrected)])
    review = authority(fixture, [observation(corrected=corrected,
        source_fragment={keyword: True, 'qualification': 'The source-reviewed historical boundary divides this printed word.'})])
    after, _, networks, counts = layer.plan(fixture['before'], layer.encode(review))
    row = json.loads(after.splitlines()[0])
    fragment = review['records'][0]['source_fragments'][0]['text']
    assert fragment in row['text'] and fragment not in row['analysis_text']
    assert counts['fragment_occurrences'] == 1
    full = next(iter(networks.values()))
    assert full['source_fragment_projection']['source_fragments'][0]['text'] == fragment
    ordinary = layer.restore_fragment_network(full)
    assert ordinary['ocr_consensus']['witnesses'] == full['ocr_consensus']['witnesses']
    assert ordinary['text'] == full['text']
    assert any(s['lexical_eligible'] for s in ordinary['ocr_consensus']['slots'])
    assert any(s['status'] == 'incomplete-reading' and not s['lexical_eligible'] for s in full['ocr_consensus']['slots'])
    if corrected == 'λόν καὶ':
        assert 'καὶ' in row['analysis_text'] and 'καὶ' in full['analysis_text']


def test_fragment_qualification_and_network_overlay_cannot_be_tampered(fixture):
    review = authority(fixture, [observation(corrected='λόν καὶ', source_fragment={
        'leading': True, 'qualification': 'The source divides this exact word at the column boundary.'})])
    altered = deepcopy(review); altered['records'][0]['source_fragments'][0]['text'] = 'καὶ'
    with pytest.raises(ValueError, match='fragment qualification'):
        layer.plan(fixture['before'], layer.encode(altered))
    _, _, networks, _ = layer.plan(fixture['before'], layer.encode(review))
    full = next(iter(networks.values()))
    full['ocr_consensus']['slots'][0]['lexical_eligible'] = True
    with pytest.raises(ValueError, match='eligibility overlay'):
        layer.restore_fragment_network(full)


def test_fragment_flags_need_completed_source_qualification(fixture):
    with pytest.raises(ValueError, match='source qualification'):
        authority(fixture, [observation(corrected='λόν καὶ', source_fragment={'leading': True})])


def test_eligibility_only_observation_preserves_text_and_casts_no_reading_vote(fixture):
    rows = deepcopy(fixture['rows']); rows[0]['text'] = 'πρὸ λόν καὶ τέλος'
    fixture['before'] = stream(rows)
    review = authority(fixture, [observation(original='λόν', corrected='λόν', projection_only=True,
        source_fragment={'leading': True, 'qualification': 'The retained row starts with the suffix of printed καλόν.'},
        digital_context_text='καλόν')])
    assert review['records'][0]['digital_counterpart'] is None
    assert review['records'][0]['digital_context']['original_text'] == 'καλόν'
    assert review['records'][0]['digital_context']['role'] == 'nonvoting-source-context'
    after, changes, networks, counts = layer.plan(fixture['before'], layer.encode(review))
    new = json.loads(after.splitlines()[0])
    assert new['text'] == rows[0]['text']
    assert 'λόν' not in new['analysis_text'] and 'καλόν' not in new['text']
    assert new['analysis_text'].split() == ['πρὸ', 'καὶ', 'τέλος']
    assert counts['scalar_corrections'] == counts['text_changed_rows'] == 0
    assert counts['projection_only_occurrences'] == counts['fragment_occurrences'] == 1
    assert changes[0]['original_text'] == changes[0]['corrected_text']
    assert changes[0]['corrections'][0]['disposition'] == 'source-reviewed-eligibility-only'
    assert networks == {}
    from build_ocr_quality_report import consensus_qualification
    quality = consensus_qualification([new])['historical_occurrence_review']
    assert quality['corrected_occurrences'] == 0
    assert quality['projection_only_occurrences'] == quality['reviewed_occurrences'] == 1


@pytest.mark.parametrize('changes,match', [
    ({'projection_only': False}, 'explicit eligibility-only'),
    ({'corrected_text': 'καλόν'}, 'explicit eligibility-only'),
    ({'source_fragment': {}}, 'qualified source fragment'),
    ({'digital_context_text': 'λόν'}, 'bounded complete'),
    ({'digital_text': 'καλόν'}, 'replacement voting witness'),
    ({'digital_context_text': None}, 'complete digital context'),
])
def test_eligibility_only_context_cannot_become_a_text_correction(fixture, changes, match):
    rows = deepcopy(fixture['rows']); rows[0]['text'] = 'πρὸ λόν καὶ τέλος'; fixture['before'] = stream(rows)
    spec = observation(original='λόν', corrected='λόν', projection_only=True,
        source_fragment={'leading': True, 'qualification': 'This is only a source-confirmed suffix.'},
        digital_context_text='καλόν')
    spec.update(changes)
    with pytest.raises(ValueError, match=match):
        authority(fixture, [spec])


def test_eligibility_only_batch_extends_prior_fragment_exclusions_without_editing_text(fixture, monkeypatch):
    root = fixture['root']; rows = deepcopy(fixture['rows'])
    rows[0]['text'] = 'λόν καὶ ἄγα-'; original = stream(rows)
    (root/layer.CORPUS).write_bytes(original); monkeypatch.setattr(layer, 'BASE_SHA', layer.sha(original))
    table(fixture, 'fixture_batch_one', 'batch-one', [observation(original='ἄγα-', corrected='ἐγκα-',
        scan_only=True, qualification='The scan prints a continued word at the retained boundary.')])
    layer.apply(root, batch_id='batch-one'); before = (root/layer.CORPUS).read_bytes()
    table(fixture, 'fixture_batch_two', 'batch-two', [observation(original='λόν', corrected='λόν',
        projection_only=True, source_fragment={'leading': True, 'qualification': 'Printed suffix of καλόν.'},
        digital_context_text='καλόν')])
    audit = layer.apply(root, batch_id='batch-two'); after = (root/layer.CORPUS).read_bytes()
    row = json.loads(after.splitlines()[0])
    assert row['text'] == json.loads(before.splitlines()[0])['text'] == 'λόν καὶ ἐγκα-'
    assert row['analysis_text'].split() == ['καὶ']
    assert len(row['historical_reading_batch_projection']['excluded_spans']) == 2
    assert layer.restore_before_bytes(after, root) == original
    assert layer.active_metadata(root)['counts']['projection_only_occurrences'] == 1
    assert audit['counts']['scalar_corrections'] == audit['counts']['text_changed_rows'] == 0
    layer.undo(root); assert (root/layer.CORPUS).read_bytes() == before
    layer.apply(root, batch_id='batch-two'); assert (root/layer.CORPUS).read_bytes() == after


@pytest.fixture(scope='module')
def released_inputs():
    """Actual source tables are tested against the exact .4 stage, after apply too."""
    root = Path(__file__).parents[1]
    if not (root/layer.SCAN).exists() or not (root/layer.LIBRARY).exists():
        pytest.skip('Frozen public source files are not available in this checkout')
    raw = layer.restore_before_bytes((root/layer.CORPUS).read_bytes(), root)
    assert layer.sha(raw) == layer.BASE_SHA
    return root, raw, (root/layer.LIBRARY).read_bytes(), (root/layer.SCAN).read_bytes()


@pytest.mark.parametrize('module_name,expected', [
    ('photius_historical_observations_continued', (319, 142, 19)),
    ('photius_historical_observations_orators', (197, 12, 8)),
    ('photius_historical_observations_pages0007_0008', (157, 7, 10)),
    ('photius_historical_observations_page0009', (105, 5, 11)),
    ('photius_historical_observations_page0010', (99, 4, 5)),
    ('photius_historical_observations_pages0011_0015', (432, 21, 77)),
])
def test_actual_paired_source_tables_replay_exactly_without_changing_row_boundaries(released_inputs, module_name, expected):
    root, before, library, scan = released_inputs
    path = Path('scripts')/(module_name+'.py')
    if not (root/path).exists():
        pytest.skip('The reviewed source table is not yet available')
    source_raw = (root/path).read_bytes(); module, held = layer._table(source_raw, path.as_posix())
    review = layer.compile_review(before, library, scan, module.observations(), batch_id=module.BATCH_ID,
        reviewed_at=module.REVIEWED_AT, table_pin={'path': path.as_posix(), 'sha256': layer.sha(source_raw)},
        held=held, source_credit=layer._source_credit(root))
    after, changes, networks, counts = layer.plan(before, layer.encode(review))
    assert (counts['reviewed_occurrences'], counts['corrected_rows'], counts['unresolved_occurrences']) == expected
    assert counts['fully_assessed_rows'] == 0
    assert counts['primary_rows_after'] == counts['primary_rows_before']
    by_locus = {r['locus']: r for r in map(json.loads, after.splitlines())}
    before_loci = [json.loads(line)['locus'] for line in before.splitlines()]
    assert list(by_locus) == before_loci
    for change in changes:
        # A raw rejected historical passage never acquires an omission vote.
        assert all(c['rejected_historical_reading_votes'] == 0 for c in change['corrections'])
        original = change['original_row']
        for key in ('historical_reading_repair', 'frequency_stamp'):
            if key in original:
                assert change['corrected_row'][key] == original[key]
    if module_name.endswith('continued'):
        assert by_locus[PREFIX.replace('0004', '0006')+'29']['text'].startswith(
            'Χριστόν, ἕνα υἱόν, ἕνα κύριον ὁμολογοῦμεν. εἶτα καὶ μίαν μὲν φύσιν')
    elif module_name.endswith('orators'):
        contrary = [c for change in changes for c in change['corrections']
                    if c['disposition'] == 'unresolved-source-variants']
        assert len(contrary) == 8
        assert any('Ἁρπάλου' in c['served_text'] and 'Ἁρπάλα' in c['served_text'] for c in contrary)
        # Common phrase words remain readable/countable, rather than enclosing
        # each entire source phrase in one unresolved bracket.
        assert any(len(networks[c['network_key']]['ocr_consensus']['slots']) > 1 and
                   any(s['lexical_eligible'] for s in networks[c['network_key']]['ocr_consensus']['slots'])
                   for c in contrary)
        fragment_change = next(change for change in changes if change['locus'].endswith('0231.3'))
        fragment = next(c for c in fragment_change['corrections'] if c['corrected_text'] == 'σίους τιθέασιν')
        assert fragment['source_fragments'][0]['text'] == 'σίους'
        assert counts['fragment_occurrences'] == 1
        full = networks[fragment['network_key']]
        slot = next(s for s in full['ocr_consensus']['slots'] if s['selected'] == 'σίους')
        assert slot['status'] == 'incomplete-reading' and not slot['lexical_eligible']
        assert full['analysis_text'] == 'τιθέασιν'
        ordinary = layer.restore_fragment_network(full)
        assert ordinary['text'] == full['text'] == 'σίους τιθέασιν'
        assert ordinary['analysis_text'] == 'σίους τιθέασιν'
    elif module_name.endswith('page0009'):
        first = by_locus[PREFIX.replace('0004', '0009')+'1']
        assert first['text'].startswith('πλίσατο, οὐκ αὐτὴ πρώτη τὰς τῆς εὐσεβείας')
        assert 'πλίσατο' not in first['analysis_text']
        assert counts['fragment_occurrences'] == counts['lexical_excluded_fragments'] == 1
        assert '⟦τέτων ∥ τούτων⟧' in first['text']
        last = by_locus[PREFIX.replace('0004', '0009')+'5']
        assert '⟦Βασίλειοί ∥ Βασιλείου⟧' in last['text']
        assert 'Βασιλείου' not in last['analysis_text']
        assert last['text'].endswith('κατάδηλον')
    elif module_name.endswith('page0010'):
        prefix = PREFIX.replace('0004', '0010')
        first = by_locus[prefix+'1']
        assert first['text'].startswith('οὖν ὡς πολλὴ καὶ ἄπειρος')
        assert 'Ἀλεξάνδρειαν, ἐπὶ τῆς οἰκουμενικῆς συγκροτηθείσης' in first['text']
        assert '⟦διώρισαι ∥ διώρισται⟧' in first['text']
        assert '⟦ὀστρακίζουσα ∥ ὑβρακίζουσα⟧' in first['text']
        second = by_locus[prefix+'2']
        assert 'φύσεις ⟦οὐκ ∥ ἐκ⟧ ἀνεχόμενον δέξασθαι' in second['text']
        assert '⟦εἰ ∥ οὐ⟧ τοίνυν' in second['text']
        third = by_locus[prefix+'3']
        assert '⟦ὥσε ∥ ὥστε⟧' in third['text']
        assert 'ὥσε' not in third['analysis_text'] and 'ὥστε' not in third['analysis_text']
        for change in changes:
            assert change['corrected_row'].get('ocr_consensus') is None
        assert all(not r['scan_only'] and r['digital_counterpart']['section'].endswith('-s287')
                   for r in review['records'])
    elif module_name.endswith('pages0011_0015'):
        assert counts['fragment_occurrences'] == counts['lexical_excluded_fragments'] == 10
        assert counts['projection_only_occurrences'] == counts['scan_only_occurrences'] == 1
        assert {r['source']['scan_page'] for r in review['records']} == {11, 12, 13, 14, 15}
        assert {r['source']['printed_page'] for r in review['records']} == {276, 277, 278, 279, 280}
        original_rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
        editorial_locus = PREFIX.replace('0004', '0011')+'5'
        assert by_locus[editorial_locus]['editorial_layer'] == original_rows[editorial_locus]['editorial_layer']
        assert all(r.get('review_scope') == 'retained-editorial-body'
                   for r in review['records'] if r['locus'] == editorial_locus)
        leading = next(r for r in review['records'] if r['original_text'] == 'φόριον')
        assert leading['scan_only'] and leading['digital_counterpart'] is None
        assert leading['source_fragments'][0]['text'] == 'στόριον'
        assert 'στόριον' not in by_locus[leading['locus']]['analysis_text']
        eligibility = next(r for r in review['records'] if r.get('projection_only'))
        assert eligibility['digital_context']['original_text'] == 'αἱρετικῶν'
        assert eligibility['digital_counterpart'] is None
        assert 'τικῶν' not in by_locus[eligibility['locus']]['analysis_text'].split()
        p13 = by_locus[PREFIX.replace('0004', '0013')+'2']
        assert '⟦τέμνεσα ∥ τέμνουσα⟧' in p13['text']
        assert '⟦ἐφ᾽ ∥ ἐφ’⟧' not in p13['text']
        p15 = by_locus[PREFIX.replace('0004', '0015')+'5']
        assert '⟦∅ ∥ διὰ⟧' in p15['text']
        assert '⟦παριστῶν ∥ παρισῶν⟧' in p15['text']
        assert p15['text'].endswith('καὶ')
    else:
        # A later occurrence review cannot replace the independently merged
        # ending of 7.5 or silently include its unreviewed historical prefix.
        prefix = PREFIX.replace('0004', '0007')
        original_rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
        assert by_locus[prefix+'5'] == original_rows[prefix+'5']
        assert by_locus[prefix+'1']['text'].startswith('εὐσεβῶν μὴ λίαν τὴν φωνὴν ἀσπαζόμενος')
        assert 'Διονύσιον' in by_locus[prefix+'3']['text']
        assert '⟦οὐχ ∥ ἐκ⟧ ἵνα' in by_locus[prefix+'4']['text']
        last = by_locus[PREFIX.replace('0004', '0008')+'3']
        # Preserve the actual witnesses even where their grammar is unusual.
        assert 'τὰς ἱερὰς ἡμῶν πατέρας' in last['text']
        assert '⟦ἕρπεσαν ∥ ἕρπουσαν⟧' in last['text']
        fragment = next(c for change in changes for c in change['corrections']
                        if c['original_text'] == 'ἄνθρω-')
        assert fragment['source_fragments'][0]['text'] == 'ἀνθω-'
        assert counts['fragment_occurrences'] == counts['lexical_excluded_fragments'] == 1
        full = networks[fragment['network_key']]
        assert not full['analysis_text']
        assert all(not s['lexical_eligible'] for s in full['ocr_consensus']['slots'])
        assert not last['analysis_text'].endswith(('ἀνθω', 'ἀνθω-'))


def test_actual_scan_only_mapping_exception_is_qualified(released_inputs):
    root, before, library, scan = released_inputs
    path = Path('scripts/photius_historical_observations_unpaired.py')
    if not (root/path).exists():
        pytest.skip('The source-reviewed mapping-exception table is not yet available')
    source_raw = (root/path).read_bytes(); module, held = layer._table(source_raw, path.as_posix())
    review = layer.compile_review(before, library, scan, module.observations(), batch_id=module.BATCH_ID,
        reviewed_at=module.REVIEWED_AT, table_pin={'path': path.as_posix(), 'sha256': layer.sha(source_raw)}, held=held)
    after, changes, networks, counts = layer.plan(before, layer.encode(review))
    row = next(r for r in map(json.loads, after.splitlines())
               if r['locus'] == 'helladius_chrestomathia_photius_bekker_v2_0169.1')
    assert 'ἀνάπαυσις' in row['text']
    assert counts['scan_only_occurrences'] == counts['reviewed_occurrences']
    assert all(c['digital_counterpart'] is None and c['qualification'] for c in review['records'])
    assert not networks and changes
    assert counts['fragment_occurrences'] == counts['lexical_excluded_fragments'] == 9
    changed = {c['locus']: c['corrected_row'] for c in changes}
    for suffix, word in (('4', 'ἐγκα'), ('5', 'αὐ'), ('15', 'τιμήσαν'), ('16', 'ἐτίμη'),
                         ('21', 'ἀμφο'), ('29', 'Εὔ'), ('40', 'Εὔ'), ('30', 'μηλον'), ('17', 'σεν')):
        current = changed['helladius_chrestomathia_photius_bekker_v2_0170.'+suffix]
        excluded = current['historical_reading_batch_projection']['excluded_spans']
        assert any(word in span['text'] and span['reason'] == 'source-confirmed-word-fragment' for span in excluded)
        # Compare exact word tokens: other legitimate occurrences may remain.
        assert len(layer._greek_words(current['text'])) > len(layer._greek_words(current['analysis_text']))
    assert changed['helladius_chrestomathia_photius_bekker_v2_0170.17']['text'].startswith('σεν')


def test_all_actual_batches_keep_projection_only_display_and_qualify_every_reviewed_fragment(released_inputs):
    root, before, library, scan = released_inputs
    raw = before; totals = Counter(); fourth_before = None
    all_changes = []
    # Freeze the five earlier batch results independently of later reviews.
    for name in layer.TABLES[:5]:
        path = Path('scripts')/(name+'.py')
        if not (root/path).exists():
            pytest.skip('The full reviewed source-table set is not yet available')
        table_raw = (root/path).read_bytes(); module, held = layer._table(table_raw, path.as_posix())
        review = layer.compile_review(raw, library, scan, module.observations(), batch_id=module.BATCH_ID,
            reviewed_at=module.REVIEWED_AT, table_pin={'path': path.as_posix(), 'sha256': layer.sha(table_raw)},
            held=held, source_credit=layer._source_credit(root))
        previous = raw
        raw, changes, networks, counts = layer.plan(raw, layer.encode(review))
        all_changes.extend(changes)
        totals.update({key: value for key, value in counts.items() if key in {
            'reviewed_occurrences', 'scalar_corrections', 'unresolved_occurrences',
            'fragment_occurrences', 'lexical_excluded_fragments', 'projection_only_occurrences'}})
        if name.endswith('_fragments'):
            fourth_before = list(map(json.loads, previous.splitlines()))
            current = list(map(json.loads, raw.splitlines()))
            assert [(r['locus'], r['text']) for r in current] == [(r['locus'], r['text']) for r in fourth_before]
            assert counts['projection_only_occurrences'] == counts['fragment_occurrences'] == 18
            assert counts['scalar_corrections'] == counts['text_changed_rows'] == counts['unresolved_occurrences'] == 0
            assert not networks
            assert sum(bool(r.get('digital_context')) for r in review['records']) == 13
            assert sum(r['scan_only'] for r in review['records']) == 5
            assert all(c['original_text'] == c['corrected_text'] for c in changes)
    assert fourth_before is not None
    assert totals == {'reviewed_occurrences': 945, 'scalar_corrections': 890,
        'unresolved_occurrences': 37, 'fragment_occurrences': 29,
        'lexical_excluded_fragments': 29, 'projection_only_occurrences': 18}
    # Counting is based on the final union of row masks, not batch event totals.
    final = {r['locus']: r for r in map(json.loads, raw.splitlines())}
    fragment_spans = [span for row in final.values()
        for span in row.get('historical_reading_batch_projection', {}).get('excluded_spans', [])
        if span['reason'] == 'source-confirmed-word-fragment']
    assert len(fragment_spans) == 29
    assert all(row.get('ocr_consensus') is None for row in final.values() if row.get('historical_reading_batches'))


def test_reviewed_prefix_preserves_exact_tail_and_is_reversible(released_inputs, tmp_path, monkeypatch):
    root, before, library, scan = released_inputs
    name = 'photius_historical_observations_prefix0007'
    relative = Path('scripts') / (name+'.py')
    table_raw = (root/relative).read_bytes()
    module, _ = layer._table(table_raw, relative.as_posix())
    original = next(r for r in map(json.loads, before.splitlines())
                    if r['locus'].endswith('_0007.5'))
    for path, raw in ((layer.CORPUS, before), (layer.SCAN, scan),
                      (layer.LIBRARY, library), (relative, table_raw)):
        (tmp_path/path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path/path).write_bytes(raw)
    credit = layer._source_credit(root)
    monkeypatch.setattr(layer, 'TABLES', (name,))
    monkeypatch.setattr(layer, '_source_credit', lambda root: credit)
    audit = layer.apply(tmp_path)
    after = (tmp_path/layer.CORPUS).read_bytes()
    changed = next(r for r in map(json.loads, after.splitlines()) if r['locus'] == original['locus'])
    old_tail = original['ocr_consensus']['span_networks']['replacement_tail']
    assert changed['ocr_consensus']['span_networks']['replacement_tail'] == old_tail
    assert changed['text'].endswith(original['source_body_correction']['replacement_text'])
    assert changed['ocr_consensus']['counts'] == {'agreement': 327, 'unresolved': 15}
    assert '⟦φάμενος ∥ φύμενος⟧' in changed['text']
    assert 'ἀδίστακτος' not in changed['analysis_text']
    assert 'ἀδίζακτος' not in changed['analysis_text']
    assert 'συγκρίματος' in changed['analysis_text']
    assert layer.restore_before_row(changed, tmp_path) == original
    runs = layer.lexical_segments(changed, tmp_path)
    assert not any('συγκρίματος ἑτεροειδῆ τὸ σῶμα' in run for run in runs)
    assert any('συγκρίματος ἑτεροειδῆ' in run for run in runs)
    archive = {p: (tmp_path/p).read_bytes() for p in layer.paths(module.BATCH_ID).values()}
    layer.undo(tmp_path)
    assert (tmp_path/layer.CORPUS).read_bytes() == before
    layer.apply(tmp_path, batch_id=module.BATCH_ID)
    assert (tmp_path/layer.CORPUS).read_bytes() == after
    assert all((tmp_path/p).read_bytes() == raw for p, raw in archive.items())
    broken = deepcopy(changed)
    broken['ocr_consensus']['span_networks']['replacement_tail']['text'] += ' changed'
    with pytest.raises(ValueError, match='postimage'):
        layer.validate_projection(broken, tmp_path)
    assert audit['counts']['fully_assessed_rows'] == 0


@pytest.mark.parametrize('change', ['partial-prefix', 'tail', 'scan-only', 'wrong-scope'])
def test_prefix_scope_cannot_expand_into_other_consensus_text(released_inputs, change):
    root, before, library, scan = released_inputs
    path = Path('scripts/photius_historical_observations_prefix0007.py')
    raw = (root/path).read_bytes(); module, _ = layer._table(raw, path.as_posix())
    observations = module.observations()
    item = observations[0]
    if change == 'partial-prefix':
        item['original_text'] = item['original_text'][1:]
    elif change == 'tail':
        item['original_text'] += ' συνεκφωνεῖσθαί'
    elif change == 'scan-only':
        item['scan_only'] = True
    else:
        item['review_scope'] = 'whole-page'
    with pytest.raises(ValueError, match='prefix|Prefix|scope'):
        layer.compile_review(before, library, scan, observations,
            batch_id=module.BATCH_ID, reviewed_at=module.REVIEWED_AT,
            table_pin={'path': path.as_posix(), 'sha256': layer.sha(raw)})


def test_frozen_release_checker_unapplies_later_batches_in_memory(fixture, monkeypatch):
    import repair_photius_historical_readings as earlier
    root = fixture['root']; before = fixture['before']
    table(fixture, 'fixture_batch_one', 'batch-one', [observation()])
    layer.apply(root, batch_id='batch-one'); after = (root/layer.CORPUS).read_bytes()
    original = b'exact earlier historical release\n'
    blob = gzip.compress(original, mtime=0)
    (root/earlier.BEFORE).parent.mkdir(parents=True, exist_ok=True)
    (root/earlier.BEFORE).write_bytes(blob)
    (root/earlier.AUDIT).write_text('{}')
    artifacts = {earlier.CORPUS: before, earlier.BEFORE: blob, earlier.AUDIT: b'{}'}
    monkeypatch.setattr(earlier, 'build', lambda root: (artifacts, {'frozen': True}))
    assert earlier.check(root) == {'frozen': True}
    assert earlier.restore_before_bytes(after, root) == original
    assert (root/layer.CORPUS).read_bytes() == after
