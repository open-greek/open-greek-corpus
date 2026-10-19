"""Reversible body voting, provenance guards, source fragments and raw variants."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import photius_body_vote as body
from ocr_consensus import compact_corpus_consensus, merge_witnesses, restore_corpus_consensus
from repair_photius_index import input_bytes

REF = {'path': 'data/review/source.json', 'sha256': 'a' * 64}
NETWORK = 'data/review/body-networks.json.gz'


def witness(identifier, text):
    return {'id': identifier, 'vote_group': identifier, 'text': text,
            'artifact_sha256': body.sha(identifier.encode())}


def boundary_fixture(first='λιὴν', last='πολ-'):
    models = [witness('qwen36', first + ' νομίζων λόγον ' + last),
              witness('qwen38', first + ' νομίζων λόγον ' + last)]
    full = merge_witnesses(models + [witness(body.SL, 'νομίζων λόγον')])
    return full


def project(full, **kwargs):
    return body.source_boundary_projection(full, leading=True, trailing=True,
        evidence='The source prints divided column-edge tokens.', source_review=REF,
        reviewed_at='2026-10-18', raw_network_reference={'path': NETWORK, 'key': 'raw'}, **kwargs)


def test_boundary_fragments_keep_display_raw_and_reverse_exactly():
    full = boundary_fixture();frozen = deepcopy(full)
    updated, raw, audit = project(full)
    assert full == frozen == raw
    assert updated['text'] == raw['text']
    assert updated['analysis_text'] == 'νομίζων λόγον'
    assert len(audit['changes']) == 2
    assert updated['ocr_consensus']['slots'][0]['lexical_exclusion'] == 'source-column-start-fragment'
    assert updated['ocr_consensus']['slots'][0]['status'] == 'incomplete-reading'
    assert body.unapply_boundary_projection(updated, raw) == raw
    compact = compact_corpus_consensus(updated, {'path': NETWORK, 'key': 'served'})
    assert restore_corpus_consensus(compact, updated) == updated
    changed = deepcopy(raw);changed['text'] += ' ἄλλο'
    with pytest.raises(ValueError):
        body.unapply_boundary_projection(updated, changed)


def test_omitted_prefix_never_excludes_first_complete_word():
    full = merge_witnesses([witness('one', 'νομίζων λόγον'), witness('two', 'νομίζων λόγον'),
                            witness(body.SL, 'νομίζων λόγον')])
    updated, raw, audit = project(full)
    assert not audit['changes'] and updated == raw
    assert updated['analysis_text'] == 'νομίζων λόγον'


def test_only_observed_edge_tokens_can_be_fragments_despite_alignment_gaps():
    full = merge_witnesses([witness('one', 'λιὴν πρῶτον δεύτερον τέλος'),
                            witness('two', 'λιὴν πρῶτον δεύτερον τέλος'), witness(body.SL, 'τέλος')])
    updated, raw, audit = project(full)
    assert [s['position'] for s in audit['changes']] == [0]
    assert 'πρῶτον δεύτερον' in updated['analysis_text']


def test_boundary_ties_remain_unresolved_and_ineligible():
    full = merge_witnesses([witness('one', 'λιὴν νομίζων'), witness('two', 'λιύγ νομίζων'),
                            witness(body.SL, 'νομίζων')])
    updated, _, audit = project(full)
    slot = updated['ocr_consensus']['slots'][0]
    assert slot['status'] == 'unresolved' and set(slot['tied_readings']) == {'λιὴν', 'λιύγ'}
    assert not slot['lexical_eligible'] and updated['text'] == full['text']
    assert len(audit['changes']) == 1


def test_missing_bounded_comparison_does_not_guess_prefix_or_suffix():
    full = merge_witnesses([witness('one', 'πρῶτον τέλος'), witness('two', 'πρῶτον τέλος')])
    updated, _, audit = project(full)
    assert updated == full and not audit['changes'] and audit['bounded_support'] is None


def exclusions(text, wrong='ἰταλοῖς', printed='ἑταίροις'):
    start = text.index(wrong)
    return [{'start': start, 'end': start + len(wrong), 'original_text': wrong,
        'observed_printed_text': printed, 'classification': 'source-confirmed-wrong-reading',
        'evidence': 'Exact source crop prints the independently matching digital word.',
        'source_image_sha256': 'b' * 64}]


def test_source_confirmed_wrong_agreement_abstains_without_substitution_or_extra_vote():
    text = 'τοῖς ἰταλοῖς ἔλεγεν τέλος'
    models = [body.apply_outcome_abstentions(witness(name, text), exclusions(text), source_review=REF)
              for name in ('one', 'two')]
    digital = witness(body.SL, 'τοῖς ἑταίροις ἔλεγεν τέλος')
    full = merge_witnesses(models + [digital])
    qualified = body._qualify_reviewed_single_readings(full, models + [digital], REF)
    assert 'ἑταίροις' in qualified['text'] and 'ἑταίροις' not in qualified['analysis_text']
    assert 'ἰταλοῖς' not in qualified['text']
    target = next(s for s in qualified['ocr_consensus']['slots'] if s['selected'] == 'ἑταίροις')
    assert target['status'] == 'single-witness' and not target['lexical_eligible']
    assert target['lexical_exclusion'] == 'source-reviewed-digital-only-reading'
    assert len(qualified['ocr_consensus']['witnesses']) == 3
    for model in qualified['ocr_consensus']['witnesses'][:2]:
        if model['id'] != body.SL:
            assert model['text'] == text and model['outcome_partitions']['before']['voting_segments'] is None
    assert qualified['ocr_consensus']['outcome_eligibility_review']['changes']


@pytest.mark.parametrize('mutate', [
    lambda s: s[0].update(start=True),
    lambda s: s[0].update(original_text='ἄλλο'),
    lambda s: s[0].update(observed_printed_text=''),
    lambda s: s[0].update(classification='arbitrary-correction'),
    lambda s: s[0].update(source_image_sha256='wrong'),
])
def test_wrong_word_abstention_requires_exact_source_review(mutate):
    model = witness('model', 'τοῖς ἰταλοῖς τέλος');spans = exclusions(model['text']);mutate(spans)
    with pytest.raises(ValueError):
        body.apply_outcome_abstentions(model, spans, source_review=REF)


@pytest.fixture
def synthetic(monkeypatch):
    before = list(map(json.loads, input_bytes(ROOT).splitlines()))
    earlier = json.loads((ROOT / 'data/corpus_changes/photius-bekker-apparatus/changes.json').read_bytes())
    masked = next(c['corrected_row'] for c in earlier['changes'] if c['locus'] == body.PREFIX + '0148.4')
    before = [masked if r['locus'] == masked['locus'] else r for r in before if r['locus'] != body.REMOVED_HEADER]
    library = (ROOT / 'data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz').read_bytes()
    pdf = b'fixture source PDF only; production renders the independently pinned source'
    monkeypatch.setattr(body, 'PDF_SHA', body.sha(pdf))
    def images(pdf_raw, pages_raw):
        return {p['id']: body.sha(body.encode(p)) for p in json.loads(pages_raw)}
    monkeypatch.setattr(body, '_rendered_hashes', images)
    items = []
    monkeypatch.setattr(body, 'AUTHORITIES', deepcopy(body.AUTHORITIES))
    for request_sha, (request_path, review_path, _) in list(body.AUTHORITIES.items()):
        request_raw = (ROOT / request_path).read_bytes();review_raw = (ROOT / review_path).read_bytes()
        request, review = json.loads(request_raw), json.loads(review_raw)
        # Synthetic source SHA must be pinned by synthetic request/review too.
        review['source_scan']['sha256'] = body.PDF_SHA
        for source in request['sources'].values():source['sha256'] = body.PDF_SHA
        review_raw = body.encode(review);request['source_review']['sha256'] = body.sha(review_raw)
        request_raw = body.encode(request)
        body.AUTHORITIES = {**body.AUTHORITIES, body.sha(request_raw): (request_path, review_path, body.sha(review_raw))}
        raw_files = []
        for model, revision in body.CHECKPOINTS.items():
            metadata = {'model': model, 'revision': revision, 'prompt': request['prompt'],
                'temperature': 0, 'max_tokens': 2000, 'backend': 'mlx', 'manifest_sha256': body.sha(request_raw),
                'runner_sha256': body.RUNNER_SHA, 'runtime': body.RUNTIME,
                'manifest_archive': 'manifests/' + body.sha(request_raw) + '.json',
                'prompt_policy': 'base prompt plus page prompt_suffix, falling back to the source prompt_suffix'}
            texts = {}
            for record in review['regions']:
                text = record['source_library_window']['original_text']
                if 'context_overlap' in record:
                    text = record['source_library_window']['held_spans'][0]['original_text'] + text
                fragment = record.get('leading_source_fragment')
                if fragment:text = ('λὴν' if fragment is True else fragment) + ' ' + text
                if record.get('trailing_source_fragment'):text += ' ' + record['trailing_source_fragment']
                words = text.split();pages = [p for p in request['pages'] if p['reconstructs'] == record['id']]
                for i, page in enumerate(pages):
                    texts[page['id']] = ' '.join(words[len(words)*i//len(pages):len(words)*(i+1)//len(pages)])
            rows = []
            for page in request['pages']:
                suffix = page.get('prompt_suffix', '')
                rows.append({'id': page['id'], 'source': page['source'], 'scan_page': page['scan_page'],
                    'region': page['region'], 'image_sha256': body.sha(body.encode(page)),
                    'prompt_sha256': body.sha((request['prompt'] + (' ' + suffix if suffix else '')).encode()),
                    'raw_prediction': texts[page['id']], 'generation_tokens': 100, 'finish_reason': 'stop', 'seconds': 1.0})
            raw_files.append(b'\n'.join(body.encode(r) for r in [{'_meta': metadata}, *rows]) + b'\n')
        items.append({'request': request_raw, 'review': review_raw, 'raw_files': raw_files})
    return before, items, library, pdf


def run(values):
    before, items, library, pdf = values
    return body.plan(before, items, library, source_pdf_raw=pdf, network_archive=NETWORK)


def test_all_eight_recoveries_are_reversible_source_qualified_plans(synthetic):
    frozen = deepcopy(synthetic)
    plan = run(synthetic)
    assert synthetic == frozen
    assert plan['counts']['added_rows'] == 7 and plan['counts']['replaced_rows'] == 1
    assert plan['counts']['raw_strips'] == 68
    assert plan['quality_review']['requires_completed_review']
    assert len(plan['networks']) == 16
    for addition in plan['additions']:
        row = addition['row']
        assert ('before' in addition) != ('after' in addition)
        assert row['locus'].startswith('photius_bekker1825_recovery_')
        assert row['reading_repair']['kind'] == 'missing-body-region'
        assert row['physical_refs']['scan_page'] + 277 == plan['logical_coverage_positions'][row['locus']]
        assert row['license'] == 'CC-BY-SA-4.0'
        full = plan['networks'][row['locus']]
        assert restore_corpus_consensus({k: row[k] for k in ('text','analysis_text','ocr_consensus')}, full) == full
        for model in [w for w in full['ocr_consensus']['witnesses'] if w['id'] != body.SL]:
            assert '\n'.join(p['original_text'] for p in model['raw_strips']) == model['text']
    locus = body.PREFIX + '0148.4';row = plan['replacements'][locus]
    assert 'editorial_layer' not in row
    assert row['reading_repair']['previous_row']['editorial_layer']['excluded_spans']
    assert row['reading_repair']['previous_editorial_layer']['original_text'].endswith('δ’')
    assert len(row['ocr_consensus']['witnesses']) == 3
    for witness in row['ocr_consensus']['witnesses']:
        if witness['id'] == body.SL:
            assert witness['full_source_text'] and witness['source_boundary_held']
        else:
            assert 'ἐκ μικρῶν' in witness['text']
            assert witness['abstention_audit']['excluded_spans']
    # Leading and terminal printed continuations never become standalone forms.
    for change in plan['changes']:
        for span in change['boundary_eligibility']['changes']:
            assert not span['corrected_slot']['lexical_eligible']


@pytest.mark.parametrize('change', ['revision','runner','runtime','image','missing','duplicate-checkpoint','length','prompt','source','anchor'])
def test_plan_rejects_unreviewed_provenance_or_incomplete_files(synthetic, change):
    before, items, library, pdf = deepcopy(synthetic)
    if change == 'source':pdf += b'changed'
    elif change == 'anchor':
        next(r for r in before if r['locus'] == body.PREFIX + '0066.1')['text'] += ' ἄλλο'
    elif change == 'duplicate-checkpoint':items[0]['raw_files'][1] = items[0]['raw_files'][0]
    else:
        rows = [json.loads(line) for line in items[0]['raw_files'][0].splitlines()]
        if change == 'revision':rows[0]['_meta']['revision'] = 'f' * 40
        elif change == 'runner':rows[0]['_meta']['runner_sha256'] = 'f' * 64
        elif change == 'runtime':rows[0]['_meta']['runtime'] = {'mlx': 'changed'}
        elif change == 'image':rows[1]['image_sha256'] = 'f' * 64
        elif change == 'prompt':rows[1]['prompt_sha256'] = 'f' * 64
        elif change == 'missing':rows.pop()
        else:rows[1]['finish_reason'] = 'length'
        items[0]['raw_files'][0] = b'\n'.join(body.encode(r) for r in rows) + b'\n'
    with pytest.raises(ValueError):
        run((before, items, library, pdf))


def test_outcome_masks_roundtrip_without_changing_raw_text():
    before = witness('one', 'τοῖς ἰταλοῖς τέλος')
    after = body.apply_outcome_abstentions(before, exclusions(before['text']), source_review=REF)
    assert body.unapply_outcome_abstentions(after) == before
    changed = deepcopy(after);changed['text'] += ' ἄλλο'
    with pytest.raises(ValueError):body.unapply_outcome_abstentions(changed)


def test_numeric_only_source_quarantine_needs_no_greek_digital_counterpart():
    before = witness('one', 'λόγος 7Π. ὅτι τέλος')
    start = before['text'].index('7Π.')
    spans = [{'start': start, 'end': start + 3, 'original_text': '7Π.',
              'observed_printed_text': '77.', 'classification': 'source-confirmed-wrong-reading',
              'evidence': 'The scan prints numeric subdivision77, not GreekΠ.', 'source_image_sha256': 'b' * 64}]
    masked = body.apply_outcome_abstentions(before, spans, source_review=REF)
    digital = witness(body.SL, 'λόγος ὅτι τέλος')
    full = merge_witnesses([masked, digital])
    qualified = body._qualify_reviewed_single_readings(full, [masked, digital], REF)
    assert qualified['text'] == 'λόγος ὅτι τέλος'
    assert body.unapply_outcome_abstentions(masked) == before


def outcome_fixture(values):
    before, items, library, pdf = deepcopy(values)
    items = items[:1]
    # One shared wrong word is retained exactly but excluded from both votes.
    for i, raw in enumerate(items[0]['raw_files']):
        records = [json.loads(line) for line in raw.splitlines()]
        for record in records[1:]:
            if 'ἑταίροις' in record['raw_prediction']:
                record['raw_prediction'] = record['raw_prediction'].replace('ἑταίροις', 'ἰταλοῖς')
        items[0]['raw_files'][i] = b'\n'.join(body.encode(r) for r in records) + b'\n'
    reviews = []
    for raw in items[0]['raw_files']:
        records = [json.loads(line) for line in raw.splitlines()];meta = records[0]['_meta']
        for row in records[1:]:
            text = row['raw_prediction'];spans = exclusions(text) if 'ἰταλοῖς' in text else []
            for span in spans:span['source_image_sha256'] = row['image_sha256']
            reviews.append({'id': row['id'], 'model': meta['model'], 'revision': meta['revision'],
                'raw_file_sha256': body.sha(raw), 'prediction_record_sha256': body.sha(body.encode(row)),
                'text_sha256': body.sha(text.encode()), 'image_sha256': row['image_sha256'],
                'evidence': 'Completed independent comparison of all source lines in this strip.',
                'decision': 'eligible-as-raw-witness', 'exclusions': spans})
    items[0]['outcome_review'] = body.encode({'schema_version':1, 'work':'photius.bibliotheca',
        'reviewed_at':'2026-10-18', 'policy':'Retain raw readings; exact reviewed errors abstain.', 'records':reviews})
    return before, items, library, pdf


def test_completed_exact_outcome_review_satisfies_gate_and_quarantines_wrong_agreement(synthetic):
    values = outcome_fixture(synthetic);plan = run(values)
    assert plan['quality_review']['requires_completed_review'] is False
    assert plan['quality_review']['completed_outcome_reviews']
    row = next(a['row'] for a in plan['additions'] if a['row']['locus'].endswith('.right'))
    assert row['reading_repair']['quality_review']['requires_completed_review'] is False
    assert 'ἑταίροις' in row['text'] and 'ἑταίροις' not in row['analysis_text']
    assert 'ἰταλοῖς' not in row['text']
    for w in row['ocr_consensus']['witnesses']:
        if w['id'] != body.SL and w.get('source_confirmed_wrong_readings'):
            assert 'ἰταλοῖς' in w['text'] and w['outcome_partitions']
            assert body.unapply_outcome_abstentions(w)['text'] == w['text']
    assert plan['input_pins']['requests'][0]['outcome_review']['sha256'] == body.sha(values[1][0]['outcome_review'])


def coverage_fixture(synthetic):
    values=outcome_fixture(synthetic)
    authority=json.loads(values[1][0]['outcome_review'])
    record=next(r for r in authority['records'] if r['id'].endswith('0066-left-part02'))
    rows=[json.loads(line) for line in values[1][0]['raw_files'][0].splitlines()]
    raw=next(r for r in rows[1:] if r['id']==record['id'])
    text=raw['raw_prediction'];word=next(key for key,_ in body.tokenize(text));start=text.index(word)
    record['exclusions']=[{'start':0,'end':len(text),'original_text':text,
        'observed_printed_text':'Ἐκ αὐτῆς τῆς μελέτης. τὸ προοίμιον.',
        'classification':'incomplete-source-coverage','digital_counterpart':None,
        'evidence':'The exact source has an authorial heading wholly absent from this reading.',
        'source_image_sha256':record['image_sha256']},
        {'start':start,'end':start+len(word),'original_text':word,
         'observed_printed_text':'H','classification':'marginal-reference','digital_counterpart':None,
         'evidence':'An independently reviewed marginal artifact overlaps the held strip.',
         'source_image_sha256':record['image_sha256']}]
    record['exclusions'].sort(key=lambda s:(s['start'],s['end']))
    values[1][0]['outcome_review']=body.encode(authority)
    return values,record


def test_full_strip_coverage_failure_abstains_without_omission_vote_and_retains_narrow_evidence(synthetic):
    values,record=coverage_fixture(synthetic);plan=run(values)
    row=next(a['row'] for a in plan['additions'] if a['row']['locus'].endswith('.left'))
    full=plan['networks'][row['locus']]
    model_id=record['model']+'@'+record['revision']
    model=next(w for w in full['ocr_consensus']['witnesses'] if w['id']==model_id)
    assert len(model['source_confirmed_wrong_readings'])==2
    assert body.unapply_outcome_abstentions(model)['text']==model['text']
    assert any('incomplete source coverage' in s['reason'] and 'marginal reference' in s['reason']
               for s in model['abstention_audit']['excluded_spans'])
    assert not any(model_id in s['omission_groups'] for s in full['ocr_consensus']['slots'])
    audit=full['ocr_consensus']['outcome_eligibility_review']
    assert len(audit['held_incomplete_source_readings'])==1 and audit['nonlexical_source_artifacts']
    assert plan['quality_review']['requires_completed_review'] is False


@pytest.mark.parametrize('change',['partial-coverage','duplicate-coverage','partial-overlap','counterpart'])
def test_coverage_abstention_rejects_unreviewed_partial_or_ambiguous_masks(synthetic,change):
    values,record=coverage_fixture(synthetic)
    coverage=next(s for s in record['exclusions'] if s['classification']=='incomplete-source-coverage')
    if change=='partial-coverage':coverage['end']-=1;coverage['original_text']=coverage['original_text'][:-1]
    elif change=='duplicate-coverage':record['exclusions'].append(deepcopy(coverage))
    elif change=='counterpart':coverage['digital_counterpart']={'section':'invented'}
    else:
        record['exclusions'].remove(coverage)
        record['exclusions'].append(deepcopy(record['exclusions'][0]))
    record['exclusions'].sort(key=lambda s:(s['start'],s['end']))
    authority=json.loads(values[1][0]['outcome_review'])
    authority['records']=[record if (r['model'],r['id'])==(record['model'],record['id']) else r for r in authority['records']]
    values[1][0]['outcome_review']=body.encode(authority)
    with pytest.raises(ValueError):run(values)


@pytest.mark.parametrize('held',[False,True])
def test_complete_outcome_fragment_hooks_keep_raw_source_pins_and_one_checkpoint_vote(synthetic,held):
    values,coverage=coverage_fixture(synthetic)
    authority=json.loads(values[1][0]['outcome_review'])
    if not held:
        record=next(r for r in authority['records'] if r['id']==coverage['id'] and r['model']==coverage['model'])
        record['exclusions']=[]
    else:
        record=next(r for r in authority['records'] if r['id']==coverage['id'] and r['model']==coverage['model'])
    rows=[json.loads(line) for line in values[1][0]['raw_files'][0].splitlines()]
    text=next(r['raw_prediction'] for r in rows[1:] if r['id']==record['id'])
    word=next(key for key,_ in body.tokenize(text));start=text.index(word)
    record['source_fragments']=[{'start':start,'end':start+len(word),'original_text':word,
        'classification':'source-split-word-fragment','observed_printed_text':'τερον',
        'evidence':'Source-reviewed split suffix; preserve raw display and exclude this occurrence from lexical counts.',
        'source_image_sha256':record['image_sha256']}]
    values[1][0]['outcome_review']=body.encode(authority)
    plan=run(values)
    row=next(a['row'] for a in plan['additions'] if a['row']['locus'].endswith('.left'))
    full=plan['networks'][row['locus']]
    assert len(full['ocr_consensus']['witnesses'])==3
    model=next(w for w in full['ocr_consensus']['witnesses'] if w.get('model')==record['model'])
    assert model['source_confirmed_fragments'][0]['raw_source_pin']['prediction_record_sha256']==record['prediction_record_sha256']
    audit=full['ocr_consensus']['outcome_eligibility_review']
    assert audit['source_fragments']
    if held:
        assert 'Already held' in audit['source_fragments'][0]['disposition']
    else:
        assert plan['counts']['internal_source_fragment_slots']==1
        assert any(not s['lexical_eligible'] and s.get('source_fragment_observations') for s in full['ocr_consensus']['slots'])
    ordinary=plan['networks'][row['locus']+':ordinary-vote']
    assert body.unapply_source_observation_projection(full,ordinary)==ordinary


@pytest.mark.parametrize('change', ['file', 'record', 'text', 'image', 'missing', 'duplicate', 'decision', 'span-image'])
def test_completed_outcomes_reject_stale_pins_or_missing_components(synthetic, change):
    values = outcome_fixture(synthetic);outcome = json.loads(values[1][0]['outcome_review'])
    target = next(r for r in outcome['records'] if r['exclusions'])
    if change == 'missing':outcome['records'].pop()
    elif change == 'duplicate':outcome['records'].append(deepcopy(target))
    elif change == 'decision':target['decision'] = 'not-reviewed'
    elif change == 'span-image':target['exclusions'][0]['source_image_sha256'] = 'f' * 64
    else:target[{'file':'raw_file_sha256','record':'prediction_record_sha256','text':'text_sha256','image':'image_sha256'}[change]] = 'f' * 64
    values[1][0]['outcome_review'] = body.encode(outcome)
    with pytest.raises(ValueError):run(values)


def pointed_fixture(*, observed='ϗ', digital_word='κὶ', digital_text=None, target_start=None, raw_word='ἡ'):
    digital_text = digital_text or ('λόγος ' + digital_word + ' τέλος')
    target_start = digital_text.index(digital_word) if target_start is None else target_start
    old_text = digital_text[:target_start] + raw_word + digital_text[target_start + len(digital_word):]
    pointer = {'section': 'section-one', 'start': target_start + len('unobserved '),
               'end': target_start + len('unobserved ') + len(digital_word), 'original_text': digital_word}
    models = []
    for name in ('one', 'two'):
        original = {'id': 'strip-one', 'raw_prediction': old_text, 'image_sha256': 'b' * 64}
        model = {**witness(name, old_text), 'model': name, 'revision': 'fixed', 'raw_file_sha256': 'c' * 64,
            'raw_strips': [{'id':'strip-one', 'start':0, 'end':len(old_text),
                'raw_prediction_record':original, 'image_sha256':'b' * 64}]}
        raw_span = {'start':target_start, 'end':target_start+len(raw_word), 'original_text':raw_word}
        span = {**raw_span, 'observed_printed_text':observed, 'classification':'source-confirmed-wrong-reading',
            'evidence':'The exact source crop explicitly prints this reviewed word or glyph.',
            'source_image_sha256':'b' * 64, 'digital_counterpart':deepcopy(pointer),
            'raw_source_span':deepcopy(raw_span), 'raw_source_pin':{
                'id':'strip-one', 'model':name, 'revision':'fixed', 'raw_file_sha256':'c' * 64,
                'prediction_record_sha256':body.sha(body.encode(original)),
                'text_sha256':body.sha(old_text.encode()), 'image_sha256':'b' * 64}}
        span['digital_context']={'start':len('unobserved '), 'end':len('unobserved ')+len(digital_text),
                                 'original_text':digital_text}
        models.append(body.apply_outcome_abstentions(model, [span], source_review=REF))
    digital = {**witness(body.SL, digital_text), 'source_section':'section-one',
        'full_source_text':'unobserved ' + digital_text + ' outside',
        'source_window':{'start':len('unobserved '), 'end':len('unobserved ')+len(digital_text)}}
    full = merge_witnesses([*models,digital])
    return full, [*models,digital], pointer


def qualify_pointed(values):
    full, witnesses, _ = values
    return body._qualify_reviewed_single_readings(full,witnesses,REF,
        raw_network_reference={'path':NETWORK,'key':'ordinary'})


@pytest.mark.parametrize(('observed','digital'), [('ϗ','κὶ'), ('ϗ','καὶ'), ('πλοῦτον','πλῦτον')])
def test_source_observation_retains_variant_with_zero_votes_and_exact_reversal(observed,digital):
    values=pointed_fixture(observed=observed,digital_word=digital)
    full,witnesses,_=values;frozen=deepcopy(values)
    updated=qualify_pointed(values)
    assert values==frozen
    assert f'⟦{digital} ∥ {observed}⟧' in updated['text'] or f'⟦{observed} ∥ {digital}⟧' in updated['text']
    slot=next(s for s in updated['ocr_consensus']['slots'] if s.get('source_observations'))
    original=full['ocr_consensus']['slots'][slot['position']]
    assert slot['status']=='unresolved' and slot['selected'] is None and not slot['lexical_eligible']
    assert set(slot['tied_readings'])=={observed,digital}
    assert slot['readings']==original['readings'] and slot['vote_status']==original['vote_status']
    assert all(x['vote_weight']==0 for x in slot['source_observations'])
    assert updated['ocr_consensus']['witnesses']==full['ocr_consensus']['witnesses']
    assert len(updated['ocr_consensus']['witnesses'])==3
    assert body.unapply_source_observation_projection(updated,full)==full
    changed=deepcopy(full);changed['text']+=' ἄλλο'
    with pytest.raises(ValueError):body.unapply_source_observation_projection(updated,changed)
    changed=deepcopy(updated);changed['ocr_consensus']['slots'][slot['position']]['selected']='ϗ'
    with pytest.raises(ValueError):body.unapply_source_observation_projection(changed,full)


def test_exact_pointer_disambiguates_repeated_words_without_spelling_search():
    text='τοῦ λόγου τοῦ θεοῦ συντάξεως συντάξεως'
    start=text.index('τοῦ',1)
    values=pointed_fixture(observed='τοῦ',digital_word='τοῦ',digital_text=text,target_start=start)
    updated=qualify_pointed(values)
    targets=[s for s in updated['ocr_consensus']['slots'] if s['selected']=='τοῦ']
    assert len(targets)==2 and targets[0]['lexical_eligible'] and not targets[1]['lexical_eligible']
    text='λόγος συντάξεως τέλος συντάξεως'
    start=text.rindex('συντάξεως')
    updated=qualify_pointed(pointed_fixture(observed='συντάξεως',digital_word='συντάξεως',digital_text=text,target_start=start))
    targets=[s for s in updated['ocr_consensus']['slots'] if s['selected']=='συντάξεως']
    assert targets[0]['lexical_eligible'] and not targets[1]['lexical_eligible']


def test_printed_line_division_does_not_invent_a_one_reading_unresolved_tie():
    values=pointed_fixture(observed='ἀκροα-\nτῶν',digital_word='ἀκροατῶν')
    updated=qualify_pointed(values)
    slot=next(s for s in updated['ocr_consensus']['slots'] if s['selected']=='ἀκροατῶν')
    assert slot['status']=='single-witness' and not slot['lexical_eligible']
    assert '⟦ἀκροατῶν⟧' not in updated['text']
    audit=updated['ocr_consensus']['outcome_eligibility_review']
    assert audit['source_observations'][0]['observed_printed_text']=='ἀκροα-\nτῶν'


def test_multiword_wrong_reading_can_point_to_one_source_token_without_extra_votes():
    values=pointed_fixture(observed='θεραπεύοντας',digital_word='ϑεραπεύοντας',raw_word='ὁ θεραπεύων')
    full,witnesses,_=values
    updated=qualify_pointed(values)
    slot=next(s for s in updated['ocr_consensus']['slots'] if s.get('source_observations'))
    assert set(slot['tied_readings'])=={'θεραπεύοντας','ϑεραπεύοντας'}
    assert all('ὁ θεραπεύων' in w['text'] for w in witnesses if w['id']!=body.SL)
    assert updated['ocr_consensus']['witnesses']==full['ocr_consensus']['witnesses']
    assert body.unapply_source_observation_projection(updated,full)==full


@pytest.mark.parametrize(('observed','classification'),[('H','marginal-reference'),('ἵ','marginal-reference'),('ὡς','neighboring-column-intrusion')])
def test_nonlexical_artifact_masks_need_no_authorial_digital_token(observed,classification):
    _,witnesses,_=pointed_fixture()
    models=[]
    for witness in witnesses[:-1]:
        span=deepcopy(witness['source_confirmed_wrong_readings'][0])
        span.update(classification=classification,digital_counterpart=None,observed_printed_text=observed)
        original=body.unapply_outcome_abstentions(witness)
        models.append(body.apply_outcome_abstentions(original,[span],source_review=REF))
    digital=deepcopy(witnesses[-1]);digital.update(text='λόγος τέλος',full_source_text='λόγος τέλος',source_window={'start':0,'end':11})
    full=merge_witnesses([*models,digital])
    updated=qualify_pointed((full,[*models,digital],None))
    assert updated['text']==full['text']=='λόγος τέλος'
    assert updated['analysis_text']==full['analysis_text']
    audit=updated['ocr_consensus']['outcome_eligibility_review']
    assert not audit['changes'] and len(audit['nonlexical_source_artifacts'])==2
    assert all(s['observed_printed_text']==observed for s in audit['nonlexical_source_artifacts'])
    assert all(s['classification']==classification for s in audit['nonlexical_source_artifacts'])
    assert body.unapply_source_observation_projection(updated,full)==full
    invalid=deepcopy(models[0]['source_confirmed_wrong_readings'][0]);invalid['digital_counterpart']={'section':'invented'}
    with pytest.raises(ValueError):body.apply_outcome_abstentions(body.unapply_outcome_abstentions(models[0]),[invalid],source_review=REF)


def fragment_fixture(raw_word='τερον'):
    _,witnesses,_=pointed_fixture(observed='τερον',digital_word='θεοῦ',raw_word=raw_word)
    models=[]
    for witness in witnesses[:-1]:
        span=deepcopy(witness['source_confirmed_wrong_readings'][0])
        span.update(classification='source-split-word-fragment',observed_printed_text='τερον')
        span.pop('digital_counterpart');span.pop('digital_context')
        original=body.unapply_outcome_abstentions(witness)
        original['source_confirmed_fragments']=[span]
        models.append(original)
    digital=deepcopy(witnesses[-1]);digital.update(text='λόγος τέλος',full_source_text='λόγος τέλος',source_window={'start':0,'end':11})
    full=merge_witnesses([*models,digital])
    return full,[*models,digital],None


def test_internal_source_fragments_keep_raw_display_but_are_lexically_ineligible():
    values=fragment_fixture();ordinary,witnesses,_=values
    updated=qualify_pointed(values)
    assert updated['text']==ordinary['text']=='λόγος τερον τέλος'
    slot=next(s for s in updated['ocr_consensus']['slots'] if s['selected']=='τερον')
    before=ordinary['ocr_consensus']['slots'][slot['position']]
    assert slot['status']=='incomplete-reading' and not slot['lexical_eligible']
    assert slot['lexical_exclusion']=='source-internal-split-word-fragment'
    assert slot['readings']==before['readings'] and slot['vote_status']==before['vote_status']
    assert updated['analysis_text']=='λόγος τέλος'
    assert updated['ocr_consensus']['witnesses']==ordinary['ocr_consensus']['witnesses']
    assert body.unapply_source_observation_projection(updated,ordinary)==ordinary
    changed=deepcopy(updated);changed['analysis_text']+=' τερον'
    with pytest.raises(ValueError):body.unapply_source_observation_projection(changed,ordinary)


def test_internal_source_fragment_ties_preserve_all_readings_without_a_selected_form():
    _,first,_=fragment_fixture('τερον');_,second,_=fragment_fixture('δτω')
    witnesses=[first[0],second[1],first[-1]];ordinary=merge_witnesses(witnesses)
    updated=qualify_pointed((ordinary,witnesses,None))
    assert updated['text']==ordinary['text']
    for slot in updated['ocr_consensus']['slots']:
        if slot.get('source_fragment_observations'):
            assert slot['status']=='unresolved' and slot['selected'] is None and not slot['lexical_eligible']
    assert body.unapply_source_observation_projection(updated,ordinary)==ordinary


@pytest.mark.parametrize('change',['partial','image','record','cross-boundary'])
def test_internal_source_fragment_projection_rejects_inexact_support_or_source_pins(change):
    values=fragment_fixture();ordinary,witnesses,_=values
    target=witnesses[0];span=target['source_confirmed_fragments'][0]
    if change=='image':span['source_image_sha256']='f'*64
    elif change=='record':span['raw_source_pin']['prediction_record_sha256']='f'*64
    elif change=='partial':
        span['end']-=1;span['original_text']=span['original_text'][:-1]
        span['raw_source_span']['end']-=1;span['raw_source_span']['original_text']=span['original_text']
    else:
        target['voting_segments']=[{'start':0,'end':span['start']+1,'text':target['text'][:span['start']+1]}]
        target['abstention_audit']={'reviewed_text_sha256':body.sha(target['text'].encode()),'source_review':REF,
            'excluded_spans':[{'start':span['start']+1,'end':len(target['text']),
                'text':target['text'][span['start']+1:],'reason':'Invalid cut inside the fragment.'}]}
    with pytest.raises(ValueError):qualify_pointed((ordinary,witnesses,None))


@pytest.mark.parametrize('change',['section','outside','partial','text','context','image','record','raw-span','missing-pin','display','no-archive'])
def test_source_observations_reject_inexact_pointers_or_missing_source_pins(change):
    values=pointed_fixture();full,witnesses,pointer=values
    spans=[w['source_confirmed_wrong_readings'][0] for w in witnesses if w['id']!=body.SL]
    if change=='display':full['text']='not the ordinary display'
    elif change=='no-archive':
        with pytest.raises(ValueError):body._qualify_reviewed_single_readings(full,witnesses,REF)
        return
    else:
        for span in spans:
            if change=='section':span['digital_counterpart']['section']='other'
            elif change=='outside':span['digital_counterpart']['start']=0
            elif change=='partial':
                span['digital_counterpart']['end']-=1;span['digital_counterpart']['original_text']='κ'
            elif change=='text':span['digital_counterpart']['original_text']='καὶ'
            elif change=='context':span['digital_context']['original_text']='Changed context'
            elif change=='image':span['source_image_sha256']='f'*64
            elif change=='record':span['raw_source_pin']['prediction_record_sha256']='f'*64
            elif change=='raw-span':span['raw_source_span']['start']+=1
            elif change=='missing-pin':span.pop('raw_source_pin')
    with pytest.raises(ValueError):qualify_pointed(values)


def test_source_observation_then_boundary_projection_unapply_in_order():
    values=pointed_fixture();ordinary,witnesses,_=values
    qualified=qualify_pointed(values)
    # A later eligibility layer can reference this already source-qualified merge.
    updated,raw,audit=body.source_boundary_projection(qualified,leading=True,trailing=True,
        evidence='Source edge evidence.',source_review=REF,reviewed_at='2026-10-18',
        raw_network_reference={'path':NETWORK,'key':'qualified'})
    assert raw==qualified
    if audit['changes']:
        restored=body.unapply_boundary_projection(updated,raw)
    else:restored=updated
    assert body.unapply_source_observation_projection(restored,ordinary)==ordinary
