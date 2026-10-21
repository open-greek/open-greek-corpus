"""Complete source review is explicit, scoped, reversible, and not admission."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_photius_review_campaign as campaign


def row(text='ὁ λόγος ἀληθές.\n', page=2, number=1, **kwargs):
    return {'urn': 'photius.bibliotheca',
        'locus': f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{number}',
        'text': text, 'language': 'grc', 'source': 'ocr', **kwargs}


@pytest.fixture
def fixture(monkeypatch):
    """Real miniature PDF and pinned archives; no production data is changed."""
    import pymupdf
    rows = [row(prior_audit={'original': 'unchanged', 'readings': ['α', 'β']})]
    digital = 'ὁ λόγος ἀληθής.\n'
    corpus = b''.join(campaign.canonical(r) + b'\n' for r in rows)
    originals = gzip.compress(corpus, mtime=0)
    library = gzip.compress(campaign.canonical({'id': 'tlg4040.tlg001.local002', 'sections': [
        {'id': campaign.SECTION_PREFIX + '279', 'blocks': [{'text': digital}]}]}), mtime=0)
    with pymupdf.open() as document:
        for _ in range(2):
            page = document.new_page(width=120, height=180)
            page.insert_text((15, 40), 'Printed source witness')
        scan = document.tobytes()
    monkeypatch.setattr(campaign, 'SCAN_SHA', campaign.sha(scan))
    monkeypatch.setattr(campaign, 'LIBRARY_SHA', campaign.sha(library))
    monkeypatch.setattr(campaign, 'ORIGINAL_SHA', campaign.sha(corpus))
    monkeypatch.setattr(campaign, 'EXPECTED_ROW_COUNT', 1)
    monkeypatch.setattr(campaign, 'EXPECTED_PAGES', (2,))
    # Small real renders keep rejection tests fast; production is fixed at3600.
    monkeypatch.setattr(campaign, 'MAX_SIDE', 120)
    credit = {'edition': 'tlg4040.tlg001.local002', 'sha256': campaign.sha(library),
              'license': {'url': 'https://creativecommons.org/licenses/by-sa/4.0/'}}
    coverage = campaign.canonical({'legacy_source': {'sha256': campaign.sha(scan)},
        'source_library': credit, 'source_scan_exceptions': [
            {'retained_legacy_scan_page': p, 'authorial_printed_page': v['authorial_printed_page'],
             'combined_scan_printed_page': v['digital_scan_printed_page'], 'logical_combined_position': p + 277,
             'source': {'sha256': campaign.sha(scan)}} for p, v in campaign.MAPPING_EXCEPTIONS.items()]})
    inputs = (corpus, scan, library, originals, coverage)
    manifest = campaign.freeze_scope(*inputs, campaign_id='historical-review-test',
        created_at='2026-10-21T10:00:00Z', baseline_commit='0' * 40)
    with pymupdf.open(stream=scan, filetype='pdf') as document:
        image_hash = campaign.sha(campaign.crop_png(document, 2, [0.1, 0.1, 0.9, 0.9]))
    segment = {'start': 0, 'end': len(rows[0]['text']), 'original_text': rows[0]['text'],
        'corrected_text': rows[0]['text'], 'verification': 'verified',
        'review_basis': 'direct-scan-inspection', 'reviewed_at': '2026-10-21T10:05:00Z',
        'evidence': 'Direct inspection of the pinned printed line, including punctuation and unchanged words.',
        'scan': {'physical_page': 2, 'region': [0.1, 0.1, 0.9, 0.9],
                 'image_sha256': image_hash, 'observed_text': rows[0]['text']},
        'readings': [], 'fragments': []}
    reviews = {'schema': campaign.REVIEW_SCHEMA, 'campaign_id': manifest['campaign_id'], 'records': [
        {'locus': rows[0]['locus'], 'original_row_sha256': campaign.row_sha(rows[0]),
         'status': 'reviewed-verified', 'segments': [segment]}]}
    return {'rows': rows, 'inputs': inputs, 'manifest': manifest, 'reviews': reviews, 'digital': digital}


def compile_fixture(fixture, *, evidence_files=None):
    return campaign.compile_campaign(fixture['manifest'], fixture['reviews'], *fixture['inputs'],
                                     evidence_files=evidence_files)


def segment(fixture):
    return fixture['reviews']['records'][0]['segments'][0]


def slice_segment(fixture, start, end):
    result = deepcopy(segment(fixture))
    result.update(start=start, end=end, original_text=fixture['rows'][0]['text'][start:end],
                  corrected_text=fixture['rows'][0]['text'][start:end])
    result['scan']['observed_text'] = result['corrected_text']
    return result


def test_frozen_scope_retains_full_preimages_and_every_source_pin(fixture):
    manifest = fixture['manifest']
    assert manifest['scope'] == {'passages': 1, 'physical_pages': [2], 'pages': 1,
        'characters': len(fixture['rows'][0]['text']), 'lexical_tokens': 3}
    assert not manifest['admission_authorized']
    frozen = manifest['rows'][0]
    assert frozen['status'] == 'unreviewed'
    assert frozen['original_row'] == fixture['rows'][0]
    assert frozen['original_row_sha256'] == campaign.row_sha(fixture['rows'][0])
    assert frozen['original_legacy_row_sha256'] == frozen['original_row_sha256']
    assert set(manifest['input_pins']) == {'corpus', 'frozen_corpus', 'scan', 'digital_archive', 'original_corpus', 'source_mapping_review'}
    assert manifest['input_pins']['corpus']['sha256'] == campaign.sha(fixture['inputs'][0])
    restored = campaign.restore_original_row(manifest, frozen['locus'])
    restored['prior_audit']['readings'].clear()
    assert frozen['original_row']['prior_audit']['readings'] == ['α', 'β']


def test_empty_review_keeps_scope_visible_and_completely_unreviewed(fixture):
    fixture['reviews']['records'] = []
    result = compile_fixture(fixture)
    assert not result['scope_complete'] and not result['admission_authorized']
    assert result['counts']['unreviewed_rows'] == 1
    assert result['counts']['fully_assessed_rows'] == 0
    assert result['counts']['reviewed_characters'] == 0
    assert result['rows'][0]['status'] == 'unreviewed'
    assert campaign.replay_text(result['rows'][0], fixture['rows'][0]['text']) == fixture['rows'][0]['text']


def test_authoring_placeholder_cannot_bypass_table_helper(fixture):
    segment(fixture)['corrected_text'] = '{u9}'
    segment(fixture)['scan']['observed_text'] = '{u9}'
    with pytest.raises(ValueError, match='placeholder'):
        compile_fixture(fixture)


def test_build_reproduces_from_immutable_archive_after_later_corpus_admission(fixture, tmp_path):
    frozen_raw = gzip.compress(fixture['inputs'][0], mtime=0)
    files = [(campaign.MANIFEST, campaign.encode(fixture['manifest'])),
             (campaign.REVIEWS, campaign.artifact_bytes(campaign.REVIEWS, fixture['reviews'])), (campaign.BASELINE, frozen_raw),
             *zip((campaign.CORPUS, campaign.SCAN, campaign.LIBRARY, campaign.ORIGINAL, campaign.COVERAGE),
                  fixture['inputs'])]
    for path, raw in files:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    expected = campaign.build(tmp_path)
    (tmp_path / campaign.CORPUS).write_bytes(b'later independently admitted corpus bytes\n')
    assert campaign.build(tmp_path) == expected
    (tmp_path / campaign.CORPUS).unlink()
    assert campaign.build(tmp_path) == expected
    (tmp_path / campaign.BASELINE).write_bytes(frozen_raw + b'changed')
    with pytest.raises((ValueError, gzip.BadGzipFile, EOFError)):
        campaign.build(tmp_path)


def test_unchanged_complete_source_review_counts_without_making_a_consensus(fixture):
    result = compile_fixture(fixture)
    assert result['scope_complete'] and not result['admission_authorized']
    assert result['counts']['verified_rows'] == result['counts']['complete_scan_review_rows'] == 1
    assert result['counts']['unchanged_segments'] == 1 and not result['counts']['corrected_segments']
    assert result['counts']['reviewed_lexical_tokens'] == 3
    assert result['complete_physical_pages'] == [2]
    assert result['rows'][0]['complete_scan_review']
    assert 'ocr_consensus' not in result['rows'][0]
    assert 'not unambiguous edition correctness' in result['qualification']


def test_corrected_full_review_replays_and_reverses_without_sources(fixture):
    original = fixture['rows'][0]['text']
    segment(fixture)['corrected_text'] = fixture['digital']
    segment(fixture)['scan']['observed_text'] = fixture['digital']
    segment(fixture)['readings'] = [{'kind': 'digital', 'text': fixture['digital'],
        'section': campaign.SECTION_PREFIX + '279', 'start': 0, 'end': len(fixture['digital'])}]
    result = compile_fixture(fixture)
    record = json.loads(json.dumps(result['rows'][0]))
    assert record['segments'][0]['readings'][0]['text'] == original
    assert record['segments'][0]['readings'][1]['kind'] == 'direct-scan'
    assert record['segments'][0]['readings'][2]['kind'] == 'digital'
    assert campaign.replay_text(record, original) == fixture['digital']
    assert campaign.restore_text(record, fixture['digital']) == original
    assert campaign.restore_original_row(fixture['manifest'], record['locus']) == fixture['rows'][0]
    assert result['counts']['corrected_segments'] == 1


def test_all_contrary_readings_survive_scan_review_without_an_arbitrary_vote(fixture):
    reviewed = segment(fixture)
    reviewed['corrected_text'] = 'ἄλλος λόγος.\n'
    reviewed['scan']['observed_text'] = reviewed['corrected_text']
    reviewed['readings'] = [{'kind': 'digital', 'text': fixture['digital'],
        'section': campaign.SECTION_PREFIX + '279', 'start': 0, 'end': len(fixture['digital'])}]
    result = compile_fixture(fixture)
    readings = result['rows'][0]['segments'][0]['readings']
    assert [r['text'] for r in readings] == [fixture['rows'][0]['text'], 'ἄλλος λόγος.\n', fixture['digital']]
    assert all('selected' not in r for r in readings)


def test_complete_uncertain_review_is_distinct_from_verified_and_keeps_display(fixture):
    reviewed = segment(fixture)
    reviewed.update(verification='uncertain', uncertainty='The damaged source preserves two possible readings.')
    reviewed['scan']['observed_text'] = fixture['digital']
    fixture['reviews']['records'][0]['status'] = 'reviewed-with-uncertainty'
    result = compile_fixture(fixture)
    assert result['scope_complete']
    assert result['counts']['rows_with_source_uncertainty'] == 1
    assert result['counts']['fully_assessed_rows'] == 1 and result['counts']['verified_rows'] == 0
    assert result['rows'][0]['corrected_text'] == fixture['rows'][0]['text']
    assert result['counts']['uncertainty_exclusion_candidates'] == 1


def test_uncertain_letter_exclusion_expands_to_whole_word_and_does_not_join_neighbors(fixture):
    text = fixture['rows'][0]['text']
    a = text.index('ό')
    pieces = [slice_segment(fixture, 0, a), slice_segment(fixture, a, a + 1), slice_segment(fixture, a + 1, len(text))]
    pieces[1].update(verification='uncertain', uncertainty='This printed vowel is unclear.')
    fixture['reviews']['records'][0].update(status='reviewed-with-uncertainty', segments=pieces)
    result = compile_fixture(fixture)
    excluded = result['rows'][0]['uncertainty_exclusion_candidates']
    assert excluded == [{'start': text.index('λόγος'), 'end': text.index('λόγος') + len('λόγος'),
        'text': 'λόγος', 'lexical_eligible': False, 'classification': 'unresolved-source-reading',
        'qualification': 'This printed vowel is unclear.', 'evidence': pieces[1]['evidence']}]
    assert result['counts']['reviewed_lexical_tokens'] == 3
    assert result['rows'][0]['corrected_text'] == text


@pytest.mark.parametrize('field,value', [('status', 'reviewed-verified'), ('status', 'unreviewed')])
def test_explicit_source_uncertainty_cannot_be_labeled_verified_or_unreviewed(fixture, field, value):
    segment(fixture).update(verification='uncertain', uncertainty='The source is unclear.')
    fixture['reviews']['records'][0][field] = value
    with pytest.raises(ValueError, match='status disagrees'):
        compile_fixture(fixture)


def test_uncertainty_cannot_silently_select_a_new_display_reading(fixture):
    segment(fixture).update(verification='uncertain', uncertainty='The source is unclear.', corrected_text='ἄλλο')
    with pytest.raises(ValueError, match='retain its original display'):
        compile_fixture(fixture)


@pytest.mark.parametrize('basis', ['digital-comparison', 'ocr-finished', '', True])
def test_comparison_or_completed_ocr_cannot_certify_source_inspection(fixture, basis):
    segment(fixture)['review_basis'] = basis
    with pytest.raises(ValueError, match='cannot certify'):
        compile_fixture(fixture)


def test_partial_review_retains_full_denominator_and_does_not_complete_page(fixture):
    fixture['reviews']['records'][0].update(status='unreviewed', segments=[slice_segment(fixture, 0, 1)])
    result = compile_fixture(fixture)
    assert result['counts']['partially_assessed_rows'] == 1
    assert result['counts']['unreviewed_rows'] == 0
    assert result['counts']['fully_assessed_rows'] == 0
    assert result['counts']['reviewed_characters'] == 1
    assert not result['scope_complete'] and not result['complete_physical_pages']


@pytest.mark.parametrize('mode', ['gap', 'whitespace-gap', 'overlap', 'duplicate', 'reverse-order'])
def test_complete_scope_requires_all_characters_once_in_order(fixture, mode):
    text = fixture['rows'][0]['text']
    if mode == 'gap':
        parts = [slice_segment(fixture, 0, 1), slice_segment(fixture, 3, len(text))]
    elif mode == 'whitespace-gap':
        parts = [slice_segment(fixture, 0, 1), slice_segment(fixture, 2, len(text))]
    elif mode == 'overlap':
        parts = [slice_segment(fixture, 0, 4), slice_segment(fixture, 3, len(text))]
    elif mode == 'duplicate':
        parts = [deepcopy(segment(fixture)), deepcopy(segment(fixture))]
    else:
        parts = [slice_segment(fixture, 2, len(text)), slice_segment(fixture, 0, 2)]
    fixture['reviews']['records'][0]['segments'] = parts
    with pytest.raises(ValueError, match='status disagrees|overlap|not in original source order'):
        compile_fixture(fixture)


def test_complete_character_review_counts_tokens_split_between_segments(fixture):
    text = fixture['rows'][0]['text']
    fixture['reviews']['records'][0]['segments'] = [slice_segment(fixture, 0, 4), slice_segment(fixture, 4, len(text))]
    result = compile_fixture(fixture)
    assert result['counts']['reviewed_lexical_tokens'] == 3
    assert result['counts']['reviewed_characters'] == len(text)


@pytest.mark.parametrize('change', ['corpus-whitespace', 'row-text', 'row-metadata', 'scope-count', 'scope-row-status',
                                    'scan-pin', 'digital-pin', 'original-pin', 'coverage-pin'])
def test_scope_and_input_pins_cannot_be_rewritten(fixture, change):
    if change == 'corpus-whitespace':
        fixture['inputs'] = (fixture['inputs'][0] + b'\n', *fixture['inputs'][1:])
    elif change == 'row-text':
        fixture['manifest']['rows'][0]['original_row']['text'] += ' '
    elif change == 'row-metadata':
        fixture['manifest']['rows'][0]['original_row']['prior_audit']['readings'] = ['α']
    elif change == 'scope-count':
        fixture['manifest']['scope']['passages'] = 0
    elif change == 'scope-row-status':
        fixture['manifest']['rows'][0]['status'] = 'reviewed-verified'
    else:
        key = {'scan-pin': 'scan', 'digital-pin': 'digital_archive', 'original-pin': 'original_corpus',
               'coverage-pin': 'source_mapping_review'}[change]
        fixture['manifest']['input_pins'][key]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='Frozen campaign scope'):
        compile_fixture(fixture)


@pytest.mark.parametrize('change', ['row-pin', 'original-span', 'crop-hash', 'wrong-page', 'crop-geometry',
                                    'time-missing', 'time-no-zone', 'time-non-UTC', 'evidence-missing',
                                    'unknown-certification', 'wrong-max-side'])
def test_review_metadata_cannot_hide_unchecked_or_changed_evidence(fixture, change):
    reviewed = segment(fixture)
    if change == 'row-pin':
        fixture['reviews']['records'][0]['original_row_sha256'] = '0' * 64
    elif change == 'original-span':
        reviewed['original_text'] = reviewed['original_text'].rstrip()
    elif change == 'crop-hash':
        reviewed['scan']['image_sha256'] = '0' * 64
    elif change == 'wrong-page':
        reviewed['scan']['physical_page'] = 1
    elif change == 'crop-geometry':
        reviewed['scan']['region'] = [0.1, float('nan'), 0.9, 0.9]
    elif change == 'time-missing':
        reviewed.pop('reviewed_at')
    elif change == 'time-no-zone':
        reviewed['reviewed_at'] = '2026-10-21T10:05:00'
    elif change == 'time-non-UTC':
        reviewed['reviewed_at'] = '2026-10-21T10:05:00-05:00'
    elif change == 'evidence-missing':
        reviewed['evidence'] = ' '
    elif change == 'wrong-max-side':
        reviewed['scan']['max_side'] = 2400
    else:
        reviewed['all_tokens_verified'] = True
    with pytest.raises(ValueError):
        compile_fixture(fixture)


def test_literal_scan_reading_requires_a_declared_transcription_convention(fixture):
    segment(fixture)['scan']['observed_text'] = 'ου ligature in the printed line'
    with pytest.raises(ValueError, match='transcription convention'):
        compile_fixture(fixture)
    segment(fixture)['transcription_convention'] = 'Expand the observed printed ου ligature as ου.'
    assert compile_fixture(fixture)['counts']['verified_rows'] == 1


@pytest.mark.parametrize('mode', ['duplicate', 'outside', 'wrong-schema', 'wrong-campaign'])
def test_reviews_cannot_repeat_escape_or_relabel_frozen_scope(fixture, mode):
    reviews = fixture['reviews']
    if mode == 'duplicate':
        reviews['records'].append(deepcopy(reviews['records'][0]))
    elif mode == 'outside':
        reviews['records'][0]['locus'] = row(page=3)['locus']
    elif mode == 'wrong-schema':
        reviews['schema'] = 'diagnostic-historical-reading-comparison'
    else:
        reviews['campaign_id'] = 'different-campaign'
    with pytest.raises(ValueError):
        compile_fixture(fixture)


def test_digital_reading_uses_exact_section_and_unicode_offsets(fixture):
    reading = {'kind': 'digital', 'text': 'λόγος', 'section': campaign.SECTION_PREFIX + '279', 'start': 2, 'end': 7}
    segment(fixture)['readings'] = [reading]
    assert compile_fixture(fixture)['rows'][0]['segments'][0]['readings'][-1]['text'] == 'λόγος'
    reading['start'] = 3
    with pytest.raises(ValueError, match='Digital reading'):
        compile_fixture(fixture)


def test_known_wrong_digital_pages_cannot_be_promoted_to_evidence(fixture):
    frozen = deepcopy(fixture['manifest']['rows'][0])
    frozen['digital_counterparts_usable'] = False
    with pytest.raises(ValueError, match='repeat unrelated'):
        campaign._digital_reading({'kind': 'digital', 'text': 'λόγος', 'section': frozen['digital_section'],
                                  'start': 2, 'end': 7}, frozen, {frozen['digital_section']: fixture['digital']},
                                  fixture['rows'][0]['text'])


def test_exact_frozen_ocr_reading_is_retained_but_never_certifies_a_segment(fixture):
    raw = campaign.canonical({'results': [{'prediction': 'ὁ λὸγος ἀληθές'}]})
    path = 'data/evaluation/ocr-fresh/example.json'
    reading = {'kind': 'ocr', 'text': 'λὸγος', 'artifact': {'path': path, 'sha256': campaign.sha(raw)},
        'json_pointer': ['results', 0, 'prediction'], 'start': 2, 'end': 7}
    segment(fixture)['readings'] = [reading]
    result = compile_fixture(fixture, evidence_files={path: raw})
    assert result['rows'][0]['segments'][0]['readings'][-1]['text'] == 'λὸγος'
    segment(fixture)['review_basis'] = 'ocr-finished'
    with pytest.raises(ValueError, match='cannot certify'):
        compile_fixture(fixture, evidence_files={path: raw})


def test_artifact_and_table_pins_are_resolved_against_real_supplied_bytes(fixture):
    raw = b'REVIEWED_AT = "2026-10-21T10:05:00Z"\n'
    path = 'scripts/source_review_example.py'
    fixture['reviews']['source_tables'] = [{'path': path, 'sha256': campaign.sha(raw)}]
    assert compile_fixture(fixture, evidence_files={path: raw})['source_tables'] == fixture['reviews']['source_tables']
    with pytest.raises(ValueError, match='artifact changed'):
        compile_fixture(fixture, evidence_files={path: raw + b'\n'})
    with pytest.raises(ValueError, match='supplied repository-relative'):
        compile_fixture(fixture)


@pytest.mark.parametrize('path', ['/private/example.json', '../example.json'])
def test_external_artifact_paths_cannot_leak_into_review_records(fixture, path):
    raw = b'{}'
    fixture['reviews']['source_tables'] = [{'path': path, 'sha256': campaign.sha(raw)}]
    with pytest.raises(ValueError, match='repository-relative'):
        compile_fixture(fixture, evidence_files={path: raw})


def test_printed_fragment_requires_explicit_exact_lexical_exclusion(fixture):
    reviewed = segment(fixture)
    reviewed['corrected_text'] = 'ὁ λόγος κα-'
    reviewed['scan']['observed_text'] = reviewed['corrected_text']
    with pytest.raises(ValueError, match='fragment needs an explicit lexical exclusion'):
        compile_fixture(fixture)
    a = reviewed['corrected_text'].index('κα-')
    reviewed['fragments'] = [{'start': a, 'end': a + 3, 'text': 'κα-', 'side': 'trailing',
        'qualification': 'The printed line ends with this incomplete word; no completion is supplied.'}]
    result = compile_fixture(fixture)
    excluded = result['rows'][0]['additional_lexical_exclusions']
    assert excluded[0]['text'] == 'κα-' and not excluded[0]['lexical_eligible']
    assert campaign.restore_text(result['rows'][0], 'ὁ λόγος κα-') == fixture['rows'][0]['text']


def test_fragment_exclusion_cannot_hide_multiple_complete_words(fixture):
    segment(fixture)['fragments'] = [{'start': 0, 'end': 7, 'text': 'ὁ λόγος', 'side': 'leading',
                                    'qualification': 'Unsupported multiword exclusion.'}]
    with pytest.raises(ValueError, match='one exact Greek token'):
        compile_fixture(fixture)


def test_two_boundary_fragments_keep_full_segment_offsets_and_terminal_check(fixture):
    reviewed = segment(fixture)
    text = 'λον καὶ κα-'
    reviewed['corrected_text'] = text
    reviewed['scan']['observed_text'] = text
    reviewed['fragments'] = [
        {'start': 0, 'end': 3, 'text': 'λον', 'side': 'leading',
         'qualification': 'Source-confirmed leading fragment.'},
        {'start': 8, 'end': 11, 'text': 'κα-', 'side': 'trailing',
         'qualification': 'Source-confirmed trailing fragment.'},
    ]
    assert len(compile_fixture(fixture)['rows'][0]['additional_lexical_exclusions']) == 2
    reviewed['fragments'].pop()
    with pytest.raises(ValueError, match='terminal printed Greek word fragment'):
        compile_fixture(fixture)


def test_partial_token_fragment_cannot_leave_letters_countable(fixture):
    reviewed = segment(fixture)
    reviewed['fragments'] = [{'start': 2, 'end': 4, 'text': 'λό', 'side': 'leading',
                             'qualification': 'Incorrect partial-token mask.'}]
    with pytest.raises(ValueError, match='one exact Greek token'):
        compile_fixture(fixture)


def test_empty_reviewed_replacement_is_reversible_and_not_silently_rejected(fixture):
    segment(fixture)['corrected_text'] = ''
    segment(fixture)['scan']['observed_text'] = ''
    result = compile_fixture(fixture)
    record = result['rows'][0]
    assert campaign.replay_text(record, fixture['rows'][0]['text']) == ''
    assert campaign.restore_text(record, '') == fixture['rows'][0]['text']


def test_replay_and_undo_refuse_changed_preimage_postimage_or_segment(fixture):
    record = compile_fixture(fixture)['rows'][0]
    with pytest.raises(ValueError, match='original passage text changed'):
        campaign.replay_text(record, record['original_text'] + ' ')
    with pytest.raises(ValueError, match='corrected passage changed'):
        campaign.restore_text(record, record['corrected_text'] + ' ')
    record['segments'][0]['original_text'] += ' '
    with pytest.raises(ValueError, match='restores the exact original'):
        campaign.restore_text(record, record['corrected_text'])


def test_complete_production_scope_is_exactly_the_previously_retained_rows():
    """Small read-only sanity check; no full OCR or alignment job is needed."""
    raw = (ROOT / campaign.CORPUS).read_bytes()
    selected = [r for r in map(json.loads, raw.splitlines())
                if campaign.PAGE.fullmatch(r['locus']) and not r.get('ocr_consensus')]
    assert len(selected) == campaign.EXPECTED_ROW_COUNT == 3462
    assert sorted({int(campaign.PAGE.fullmatch(r['locus'])[1]) for r in selected}) == list(campaign.EXPECTED_PAGES)


def attach_alignment(fixture):
    reviewed = segment(fixture)
    source = campaign.tokens(reviewed['scan']['observed_text'])
    digital = campaign.tokens(fixture['digital'])
    aligned = campaign._local_alignment([campaign._key(t['text']) for t in source],
                                        [campaign._key(t['text']) for t in digital])
    section = fixture['manifest']['rows'][0]['digital_section']
    reviewed['digital_alignment'] = {'section': section,
        'tokens': [{k: t[k] for k in ('start', 'end', 'text')} |
                   {'may_be_unaligned': aligned['may_be_unaligned'][i],
                    'counterpart_count': len(aligned['counterparts'][i])}
                   for i, t in enumerate(source)],
        **{k: aligned[k] for k in ('ambiguous', 'aligned', 'cost')}}
    reviewed['readings'] = [
        {'kind': 'digital', 'section': section, **{k: digital[j][k] for k in ('start', 'end', 'text')},
         'review_span': {k: source[i][k] for k in ('start', 'end', 'text')},
         'may_be_unaligned': aligned['may_be_unaligned'][i]}
        for i, candidates in enumerate(aligned['counterparts']) for j in candidates]
    return reviewed


def test_diagnostic_alignment_retains_exact_edges_without_admitting_them(fixture):
    attach_alignment(fixture)
    compiled = compile_fixture(fixture)
    observed = compiled['rows'][0]['segments'][0]
    assert not observed['digital_alignment']['admission_authorized']
    assert any(r.get('text') == 'ἀληθής' for r in observed['readings'])
    assert compiled['rows'][0]['corrected_text'] == fixture['rows'][0]['text']


@pytest.mark.parametrize('mutation', ['lost-edge', 'duplicate-edge', 'wrong-span', 'gap-flag', 'no-alignment'])
def test_digital_edge_accounting_rejects_lost_or_changed_evidence(fixture, mutation):
    reviewed = attach_alignment(fixture)
    if mutation == 'lost-edge':
        reviewed['readings'].pop()
    elif mutation == 'duplicate-edge':
        reviewed['readings'].append(deepcopy(reviewed['readings'][0]))
    elif mutation == 'wrong-span':
        reviewed['readings'][0]['review_span']['start'] += 1
    elif mutation == 'gap-flag':
        reviewed['digital_alignment']['tokens'][0]['may_be_unaligned'] = True
    else:
        reviewed.pop('digital_alignment')
    with pytest.raises(ValueError):
        compile_fixture(fixture)


@pytest.mark.parametrize('role', ['unclassified-small-type', 'unclassified-heading', 'editorial-note', 'marginal-reference', 'duplicate-heading'])
def test_full_source_review_does_not_implicitly_admit_nonbody_material(fixture, role):
    segment(fixture)['text_role'] = role
    compiled = compile_fixture(fixture)
    assert compiled['counts']['complete_scan_review_rows'] == 1
    assert compiled['counts']['nonbody_exclusion_candidates'] == 1
    excluded = compiled['rows'][0]['nonbody_exclusion_candidates'][0]
    assert excluded['text'] == fixture['rows'][0]['text']
    assert not excluded['lexical_eligible']


def test_unresolved_ocr_hyphen_is_not_certified_as_printed_fragment(fixture, monkeypatch):
    original = 'ὁ λόγος κα-'
    fixture['rows'][0]['text'] = original
    corpus = campaign.canonical(fixture['rows'][0]) + b'\n'
    inputs = list(fixture['inputs'])
    inputs[0], inputs[3] = corpus, gzip.compress(corpus, mtime=0)
    fixture['inputs'] = tuple(inputs)
    monkeypatch.setattr(campaign, 'ORIGINAL_SHA', campaign.sha(corpus))
    fixture['manifest'] = campaign.freeze_scope(*inputs, campaign_id='historical-review-test',
        created_at='2026-10-21T10:00:00Z', baseline_commit='0' * 40)
    review = fixture['reviews']['records'][0]
    review.update(original_row_sha256=campaign.row_sha(fixture['rows'][0]),
                  status='reviewed-with-uncertainty')
    item = segment(fixture)
    item.update(end=len(original), original_text=original, corrected_text=original,
                verification='uncertain', uncertainty='The OCR hyphen has no certified scan counterpart.')
    item['scan']['observed_text'] = 'ὁ λόγος κα[?]'
    compiled = compile_fixture(fixture)['rows'][0]
    assert compiled['segments'][0]['fragments'] == []
    assert compiled['additional_lexical_exclusions'] == []
    assert compiled['uncertainty_exclusion_candidates'][0]['text'] == original
    assert campaign.restore_text(compiled, original) == original
