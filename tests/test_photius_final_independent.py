"""Independent final-layer checks for effective eligibility and source identity."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import repair_photius_final_review as final
from test_photius_final_review import case, save


def test_preserved_independent_exclusion_is_not_reported_as_lexical_admission():
    before, review = case()
    leaf = deepcopy(review['prior_exclusions']['a'][0])
    leaf.update(classification='independent-source-cause',
                qualification='A separate exclusion survives this source choice.')
    review['prior_exclusions']['a'].append(leaf)
    after, changes, counts = final.plan(before, final.encode(review))
    assert 'κατασκευασθεῖσαι' not in ' '.join(json.loads(line)['analysis_text'] for line in after.splitlines())
    assert any(e['classification'] == 'independent-source-cause'
               for e in changes[0]['remaining_exclusion_causes'])
    assert len(counts['lexical_resolution_identities']) == 2
    assert counts['lexical_admitted_identities'] == []


@pytest.mark.parametrize('field', ['schema', 'review-path', 'uncompressed-pin'])
def test_warmed_projection_rejects_changed_authority_metadata(tmp_path, field):
    before, review = case()
    files, audit = save(tmp_path, before, review)
    row = json.loads(files[final.CORPUS].splitlines()[0])
    final.lexical_segments(row, tmp_path)
    if field == 'schema':
        audit['schema'] = 'unknown-source-authority'
    elif field == 'review-path':
        audit['source_review']['path'] = 'data/wrong-source.json.gz'
    else:
        audit['source_review']['uncompressed_sha256'] = '0' * 64
    (tmp_path / final.AUDIT).write_bytes(final.encode(audit))
    with pytest.raises(ValueError):
        final.lexical_segments(row, tmp_path)


def test_exact_undo_preserves_noncanonical_json_escapes_and_line_endings(tmp_path, monkeypatch):
    before, review = case()
    rows = [json.loads(line) for line in before.splitlines()]
    before = b''.join((json.dumps(row, ensure_ascii=True, separators=(', ', ': ')) + '\r\n').encode()
                      for row in rows)
    review['input_corpus_sha256'] = final.sha(before)
    files, _ = save(tmp_path, before, review)
    monkeypatch.setattr(final, 'prepare', lambda *args, **kwargs:
                        (_ for _ in ()).throw(ValueError('Source unavailable')))
    assert final.restore_before_bytes(files[final.CORPUS], tmp_path) == before
    final.undo(tmp_path)
    assert (tmp_path / final.CORPUS).read_bytes() == before


def test_held_identities_do_not_enter_resolution_partitions_or_role_totals():
    before, review = case()
    record = review['records'][0]
    record.update(disposition='held', lexical_eligible=False)
    for edit in record['edits']:
        edit['corrected_text'] = edit['original_text']
    _, _, counts = final.plan(before, final.encode(review))
    assert counts['current_uncertainty_spans'] == 2
    assert counts['resolved_identities'] == []
    assert counts['lexical_resolution_identities'] == []
    assert counts['nonlexical_resolution_identities'] == []
    assert counts['lexical_admitted_identities'] == []
    assert counts['resolved_by_text_role'] == {}


def test_empty_review_ranges_cannot_admit_material_classified_nonlexical():
    before, review = case()
    record = review['records'][0]
    record.update(disposition='exclude-marginal-reference', text_role='marginal-reference',
                  lexical_eligible=False, review_ranges=[])
    for edit in record['edits']:
        edit['corrected_text'] = edit['original_text']
    # Keep only the uncertainty causes that a resolved decision will retire.
    for locus in review['prior_exclusions']:
        review['prior_exclusions'][locus] = review['prior_exclusions'][locus][:1]
    try:
        after, _, _ = final.plan(before, final.encode(review))
    except ValueError:
        return  # Rejecting unsupported ranges is a safe contract.
    lexical = ' '.join(json.loads(line)['analysis_text'] for line in after.splitlines())
    assert 'κατα-' not in lexical and 'σκευασθεῖσαι' not in lexical


def test_nonlexical_review_range_in_another_row_cannot_be_silently_ignored():
    before, review = case()
    extra = {'locus': 'reviewed-neighbor', 'text': 'παράγραφος', 'analysis_text': 'παράγραφος'}
    before += final.canonical(extra) + b'\n'
    review['input_corpus_sha256'] = final.sha(before)
    record = review['records'][0]
    record.update(disposition='exclude-marginal-reference', text_role='marginal-reference', lexical_eligible=False)
    for edit in record['edits']:
        edit['corrected_text'] = edit['original_text']
    record['review_ranges'] = [
        {key: edit[key] for key in ('locus', 'start', 'end', 'original_text', 'original_row_sha256')}
        for edit in record['edits']]
    record['review_ranges'].append({'locus': extra['locus'], 'start': 0, 'end': len(extra['text']),
        'original_text': extra['text'], 'original_row_sha256': final.prior.row_sha(extra)})
    review['prior_exclusions'][extra['locus']] = []
    try:
        after, _, _ = final.plan(before, final.encode(review))
    except ValueError:
        return  # Rejecting a row without a literal edit is also safe.
    rows = {row['locus']: row for row in map(json.loads, after.splitlines())}
    assert rows[extra['locus']]['analysis_text'].strip() == ''


def source_case(monkeypatch, *, groups=False):
    """Freeze exact fixture decisions, leaving cross-record checks to the engine."""
    before, review = case()
    records = deepcopy(review['records'])
    if groups:
        original = records.pop()
        records = [{**deepcopy(original), 'identities': [identity], 'edits': [edit]}
                   for identity, edit in zip(original['identities'], original['edits'])]
    for record in records:
        record['readings'] = [{'source_id': 'test', 'role': 'chosen',
            'text': 'κατασκευασθεῖσαι', 'tokens': [{'text': 'κατασκευασθεῖσαι', 'source_index': 100,
                'refs': [{'unit_index': 100, 'html_line': 50, 'html_column': 10,
                          'codex': '250', 'bekker': '449a', 'start': 0, 'end': 16}]}]}]
    authored = {key: deepcopy(value) for key, value in review.items()
                if key not in {'records', 'prior_exclusions', 'identities', 'previous_current_uncertainty_spans'}}
    authored['records'] = records
    rows = {row['locus']: row for row in map(json.loads, before.splitlines())}
    scopes = {(i['locus'], i['segment_index']): {'start': i['start'], 'end': i['end'],
        'row': rows[i['locus']], 'record': {'original_segment': i['original_segment']}}
        for i in review['identities']}
    monkeypatch.setitem(sys.modules, 'authored-test', SimpleNamespace(validate_record=lambda r: deepcopy(r)))
    monkeypatch.setattr(final, 'MODULES', ('authored-test',))
    monkeypatch.setattr(final, 'scope', lambda *args: deepcopy(scopes))
    monkeypatch.setattr(final, '_row_masks', lambda row, root:
                        deepcopy(review['prior_exclusions'][row['locus']]))
    monkeypatch.setattr(final, '_used_source_refs', lambda root: set())
    monkeypatch.setattr(final, 'SOURCE_WITNESS_SHA256', final.witness_fingerprint(authored))
    return before, authored


def test_same_source_word_cannot_be_adopted_by_two_final_groups(monkeypatch):
    before, authored = source_case(monkeypatch, groups=True)
    with pytest.raises(ValueError, match='already adopted source token'):
        final.compile_review(before, authored)


def test_previously_adopted_source_word_cannot_vote_again(monkeypatch):
    before, authored = source_case(monkeypatch)
    ref = authored['records'][0]['readings'][0]['tokens'][0]['refs']
    monkeypatch.setattr(final, '_used_source_refs', lambda root: {final.sha(final.canonical(ref))})
    with pytest.raises(ValueError, match='already adopted source token'):
        final.compile_review(before, authored)


@pytest.mark.parametrize('defect', ['wrong-source', 'boolean-index', 'nonconsecutive'])
def test_frozen_source_packet_still_needs_valid_source_token_accounting(monkeypatch, defect):
    before, authored = source_case(monkeypatch)
    reading = authored['records'][0]['readings'][0]
    if defect == 'wrong-source':
        reading['source_id'] = 'another-source'
    elif defect == 'boolean-index':
        reading['tokens'][0]['source_index'] = True
    else:
        second = deepcopy(reading['tokens'][0])
        second['source_index'] += 2
        second['refs'][0]['start'] = 20
        second['refs'][0]['end'] = 36
        reading['tokens'].append(second)
    monkeypatch.setattr(final, 'SOURCE_WITNESS_SHA256', final.witness_fingerprint(authored))
    with pytest.raises(ValueError, match='consecutive edition indices'):
        final.compile_review(before, authored)
