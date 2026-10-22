"""Final dispositions preserve positive witnesses and exact reversible edits."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import photius_final_source_observations as final
import prepare_photius_editorial_continuation as prepare
import repair_photius_editorial_substitutions as previous


def case(monkeypatch, *, omission=False):
    spec = deepcopy(final.SPECS[4 if omission else 3])
    old = spec['edits'][0]['original_text']
    row = {'locus': spec['identities'][0]['locus'], 'text': 'ἀρχὴ ' + old + ' τέλος'}
    start = len('ἀρχὴ ')
    edit = {'locus': row['locus'], 'start': start, 'end': start + len(old),
            'original_text': old, 'corrected_text': '' if omission else 'σαφές',
            'original_row_sha256': final._digest(row)}
    spec['edits'] = [edit]
    spec['review_ranges'] = [{key: value for key, value in edit.items() if key != 'corrected_text'}]
    source_text = 'μὴ παύωνται' if omission else 'σαφές'
    raw = ('<h3>247</h3><h2>419a</h2><td>ἀρχὴ ' + source_text + ' τέλος</td>').encode()
    units = prepare.source_document(raw)
    source = {'id': final.SOURCE_ID, 'edition': 'Henry', 'citation': 'Photius 4040.001',
              'sha256': hashlib.sha256(raw).hexdigest()}
    known = previous._source_tokens(raw, source)
    indexed = list(known.values())[1:-1]
    tokens = [{'text': token['text'], 'refs': deepcopy(token['refs']), 'source_index': index}
              for index, token in indexed]
    spec.update(context=(0, 1), context_sha256=final._digest(list(units)))
    if omission:
        spec['omission_boundaries'] = tokens
    else:
        spec['word_selection'] = 'σαφές'
        spec['word_indices'] = [tokens[0]['source_index']]
        attributed = prepare.attributed_span({'tokens': tokens}, units)
        spec['word_surface'] = {key: attributed[key]
            for key in ('surface', 'separators', 'boundary_suffix')}
    image = b'Exact reviewed scan crop bytes.'
    for scan in spec['scan']:
        scan['image_sha256'] = hashlib.sha256(image).hexdigest()
    monkeypatch.setattr(final, 'SPECS', [spec])
    monkeypatch.setattr(final, 'SOURCE_SHA256', source['sha256'])
    return raw, {row['locus']: row}, object(), lambda document, page, region: image


def record(monkeypatch, *, omission=False):
    inputs = case(monkeypatch, omission=omission)
    return final.review_final(*inputs)[0]


def test_every_original_nonboundary_identity_has_one_exact_disposition():
    identities = [tuple(identity.values()) for spec in final.SPECS for identity in spec['identities']]
    assert len(identities) == len(set(identities)) == 12
    assert sum(spec['text_role'] in {'nonlexical-mark', 'marginal-reference', 'ocr-insertion'}
               for spec in final.SPECS) == 5
    for spec in final.SPECS:
        assert spec['edits'] and spec['scan'] and spec['evidence']
        assert spec['prior_identity_sha256']
        assert all(edit['original_text'] and len(edit['original_row_sha256']) == 64
                   for edit in spec['edits'])


def test_editorial_word_choices_do_not_claim_bekker_glyph_resolution():
    choices = [spec for spec in final.SPECS if spec['disposition'].startswith('editorial-word-choice')]
    assert len(choices) == 3
    assert all(spec['glyph_resolved'] is False for spec in choices)
    omission = next(spec for spec in choices if spec['omission_boundaries'])
    assert omission['edits'][0]['corrected_text'] == ''
    assert omission['residual_uncertainty']['glyph_resolved'] is False
    assert {alternative['text'] for alternative in omission['residual_uncertainty']['alternatives']} == {
        'ὁ', 'οὐ', 'ἐξ'}


def test_printed_variant_and_nonlexical_mark_are_retained():
    for suffix in ['0018-36-s3', '0037-4-s5']:
        spec = next(spec for spec in final.SPECS if spec['id'].endswith(suffix))
        assert spec['edits'][0]['original_text'] == spec['edits'][0]['corrected_text']
        assert spec['lexical_eligible'] is False


def test_reference_removal_keeps_a_boundary_and_broken_body_word():
    fused = next(spec for spec in final.SPECS if spec['id'].endswith('0158-5-s12'))
    edit = fused['edits'][0]
    assert edit['original_text'] == '682H.' and edit['corrected_text'] == ' '
    assert ('ἀθυμήσαντα' + edit['original_text'] + 'δὲ').replace(
        edit['original_text'], edit['corrected_text']) == 'ἀθυμήσαντα δὲ'
    broken = next(spec for spec in final.SPECS if spec['id'].endswith('0184-1-s4'))
    edit = broken['edits'][0]
    assert ('Μή-' + edit['original_text']).replace(edit['original_text'], edit['corrected_text']) == 'Μή-'


def test_whole_printed_bracket_group_is_reviewed_around_the_narrow_ocr_edit():
    spec = next(spec for spec in final.SPECS if spec['id'].endswith('0172-7-s3'))
    edit, reviewed = spec['edits'][0], spec['review_ranges'][0]
    assert reviewed['start'] < edit['start'] < edit['end'] < reviewed['end']
    a, b = edit['start'] - reviewed['start'], edit['end'] - reviewed['start']
    corrected = reviewed['original_text'][:a] + edit['corrected_text'] + reviewed['original_text'][b:]
    assert corrected == '[ἀναίσχυντον πάνυ τοῦτόν φασιν]'
    assert spec['text_role'] == 'printed-bracketed-reading' and not spec['lexical_eligible']


def test_orphan_has_positive_column_anchors_and_transmitted_variant_has_apparatus():
    orphan = next(spec for spec in final.SPECS if spec['id'].endswith('0179-2-s0'))
    assert orphan['edits'][0]['original_text'] == 'Ἀρξίλαος'
    assert orphan['edits'][0]['corrected_text'] == ''
    assert [scan['observed_text'] for scan in orphan['scan']] == [
        'εἰς τὸν Ἀχέ-', 'ροντα καὶ τὸν Ἅιδου τόπον.']
    variant = next(spec for spec in final.SPECS if spec['id'].endswith('0274-3-s23'))
    assert variant['edits'][0]['corrected_text'] == 'λούσασθαι'
    assert variant['scan'][1]['observed_text'] == 'b.34. λούσασθαι add B.'


@pytest.mark.parametrize('omission', [False, True])
def test_fresh_and_literal_review_agree_with_supplied_review_time(monkeypatch, omission):
    inputs = case(monkeypatch, omission=omission)
    timestamp = '2026-10-22T01:02:03Z'
    observed = final.review_final(*inputs, reviewed_at=timestamp)[0]
    assert observed['reviewed_at'] == timestamp
    assert final.validate_record(observed) == observed


@pytest.mark.parametrize('field', [
    'id', 'identities', 'edits', 'review_ranges', 'disposition', 'text_role',
    'lexical_eligible', 'glyph_resolved', 'evidence', 'qualification', 'scan',
    'residual_uncertainty', 'reviewed_at', 'prior_identity', 'source_context',
    'contrary_readings', 'readings', 'word_source',
])
def test_every_authored_authority_field_is_validated(monkeypatch, field):
    observed = record(monkeypatch)
    observed[field] = 'changed'
    with pytest.raises(ValueError):
        final.validate_record(observed)


@pytest.mark.parametrize('defect', ['extra-permission', 'source-unit', 'word-ref', 'word-index', 'surface'])
def test_added_permissions_and_source_witness_changes_fail(monkeypatch, defect):
    observed = record(monkeypatch)
    if defect == 'extra-permission':
        observed['allow_arbitrary_omission'] = True
    elif defect == 'source-unit':
        observed['source_context']['units'][0]['text'] += ' ἄλλο'
    elif defect == 'word-ref':
        observed['readings'][0]['tokens'][0]['refs'][0]['start'] += 1
    elif defect == 'word-index':
        observed['readings'][0]['tokens'][0]['source_index'] += 1
    else:
        observed['readings'][0]['surface'] += '.'
    with pytest.raises(ValueError):
        final.validate_record(observed)


@pytest.mark.parametrize('defect', ['boundary-index', 'boundary-text', 'intervening-word', 'discarded-variant'])
def test_explicit_omission_keeps_exact_empty_interval_and_archived_variants(monkeypatch, defect):
    observed = record(monkeypatch, omission=True)
    if defect == 'boundary-index':
        observed['omission_source']['boundaries'][1]['source_index'] += 1
    elif defect == 'boundary-text':
        observed['omission_source']['boundaries'][0]['text'] = 'ἄλλο'
    elif defect == 'intervening-word':
        observed['omission_source']['intervening_tokens'] = ['ἄλλο']
    else:
        observed['residual_uncertainty']['alternatives'] = []
    with pytest.raises(ValueError):
        final.validate_record(observed)


@pytest.mark.parametrize('defect', ['source', 'row', 'crop'])
def test_fresh_review_rejects_changed_inputs(monkeypatch, defect):
    raw, rows, document, crop = case(monkeypatch)
    if defect == 'source':
        raw += b' changed'
    elif defect == 'row':
        next(iter(rows.values()))['extra'] = 'changed'
    else:
        crop = lambda document, page, region: b'Changed crop'
    with pytest.raises(ValueError):
        final.review_final(raw, rows, document, crop)


@pytest.mark.parametrize('timestamp', [None, False, 'invalid', '2026-10-22T01:02:03',
                                      '2026-10-22T01:02:03+03:00'])
def test_invalid_or_unzoned_review_time_fails(monkeypatch, timestamp):
    inputs = case(monkeypatch)
    with pytest.raises(ValueError):
        final.review_final(*inputs, reviewed_at=timestamp)
