"""Mixed works cannot disappear from OCR denominators or inherit manual review."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_source_components as components
import build_corpus_catalog as catalog
import build_corpus_release as release
import build_provenance as provenance
import build_known_limitations as limitations


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


def test_corpus_pin_uses_release_slug_order_for_prefix_collisions():
    pins = {'sample.work-extra.jsonl': 'b' * 64,
            'sample.work.jsonl': 'a' * 64,
            'sample.work.part.jsonl': 'c' * 64}
    canonical = ('sample.work\t' + 'a' * 64 + '\n'
                 'sample.work-extra\t' + 'b' * 64 + '\n'
                 'sample.work.part\t' + 'c' * 64 + '\n')
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert components.corpus_hash(pins) == expected
    assert components.corpus_hash(dict(reversed(list(pins.items())))) == expected


@pytest.fixture
def corpus(tmp_path):
    data = tmp_path / 'data'
    rows = {
        'cassius-dio.historiae-romanae': [
            {'source':'perseus','edition':'old','text':'λόγος θεός ἀνήρ'},
            {'source':'ocr','edition':'new','text':'⟦καί∥δέ⟧ ἔπος','analysis_text':'ἔπος'}],
        'apollonius-geom.conica': [
            {'source':'first1k','edition':'old','text':'λόγος'},
            {'source':'ocr-masked','edition':'new','text':'ἀρχή τέλος','corrections':['manual']}],
        'pappus-mathematics.synagoge': [
            {'source':'first1k','edition':'old','text':'λόγος'},
            {'source':'ocr','edition':'new','text':'[ἀνήρ] βίος','analysis_text':'βίος',
             'critical_markup':{'schema':'epidoc-spans-v1'},'corrections':['manual']}],
        'homogeneous.work': [{'source':'ocr','edition':'one','text':'θεός'}],
    }
    for slug, records in rows.items():
        path = data / 'corpus' / (slug+'.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps({**r,'license':'PD','urn':slug,'locus':str(i)}, ensure_ascii=False)+'\n'
                                for i,r in enumerate(records)))
    report = components.build(data)
    (data / components.NAME).write_bytes(components.encode(report))
    return tmp_path, data, report


def catalog_rows(report):
    rows = []
    for slug, work in report['works'].items():
        source = 'perseus' if slug.startswith('cassius') else 'ocr'
        rows.append({'slug':slug,'source':source,'license':'PD',
            'correction':components.MIXED_STATUS if work['mixed_ocr_digital'] else 'raw-ocr',
            'tokens':str(work['analysis_tokens']),'tokens_lemmatized':'0',
            'passages':str(work['passages']),
            'sha256':report['input_corpus_files'][slug+'.jsonl']})
    return rows


def write_catalog(data, rows):
    path = data / 'corpus_catalog.tsv'
    with path.open('w', newline='') as sink:
        writer = csv.DictWriter(sink, fieldnames=list(rows[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_every_ocr_component_counts_despite_dominant_digital_and_manual_stamps(corpus):
    _, data, report = corpus
    assert report['totals']['ocr_analysis_tokens'] == 5
    assert report['totals']['mixed_works'] == 3
    assert report['totals']['mixed_ocr_analysis_tokens'] == 4
    assert report['totals']['analysis_tokens'] == 10
    assert report['works']['cassius-dio.historiae-romanae']['ocr_analysis_tokens'] == 1
    assert report['by_source']['ocr']['analysis_tokens'] == 5
    assert 'ocr-masked' not in report['by_source']
    assert components.load_verified(data) == report
    for slug in report['works']:
        if report['works'][slug]['mixed_ocr_digital']:
            assert catalog.correction_status(slug, 'perseus', {'manual'}, 1,
                                             {slug}, {slug}, mixed=True) == 'mixed-unassessed'


@pytest.mark.parametrize('change', ['modify','add','remove','projection','recipe'])
def test_consumers_reject_any_corpus_or_eligibility_drift(corpus, monkeypatch, change):
    _, data, _ = corpus
    path = data / 'corpus/homogeneous.work.jsonl'
    if change == 'modify':
        path.write_text(path.read_text().replace('θεός','θεοῦ'))
    elif change == 'add':
        (path.parent / 'new.work.jsonl').write_bytes(path.read_bytes())
    elif change == 'remove':
        path.unlink()
    elif change == 'projection':
        write_json(data/'frequency_projection.json', {'source_sha256':{},'rows':{}})
    else:
        monkeypatch.setattr(components, 'recipe_pins', lambda: {'different.py':'0'*64})
    with pytest.raises(ValueError, match='stale'):
        components.load_verified(data)


def test_report_check_recomputes_counts_instead_of_trusting_hashes(corpus, monkeypatch):
    root, data, report = corpus
    report['totals']['ocr_analysis_tokens'] += 1
    (data / components.NAME).write_bytes(components.encode(report))
    monkeypatch.setattr(sys, 'argv', ['build_source_components.py','--root',str(root),'--check'])
    with pytest.raises(SystemExit) as outcome:
        components.main()
    assert outcome.value.code == 1


def test_positional_frequency_projection_and_critical_eligibility_are_counted(corpus):
    _, data, _ = corpus
    path = data/'corpus/homogeneous.work.jsonl'
    row = json.loads(path.read_text())
    row['text'] = 'θεός λόγος'
    path.write_text(json.dumps(row)+'\n')
    write_json(data/'frequency_projection.json', {'source_sha256':{path.name:components.sha(path.read_bytes())},
        'rows':{'homogeneous.work:0':[[5,10]]}})
    report = components.build(data)
    assert report['works']['homogeneous.work']['analysis_tokens'] == 1
    assert report['works']['pappus-mathematics.synagoge']['ocr_analysis_tokens'] == 1
    assert report['frequency_projection_sha256'] != 'none'


@pytest.mark.parametrize('damage', ['status','tokens','sha','work-set'])
def test_catalog_must_match_each_component_work(corpus, damage):
    _, _, report = corpus
    rows = catalog_rows(report)
    if damage == 'status':
        rows[0]['correction'] = 'manual'
    elif damage == 'tokens':
        rows[0]['tokens'] = str(int(rows[0]['tokens'])+1)
        rows[1]['tokens'] = str(int(rows[1]['tokens'])-1)  # total remains identical
    elif damage == 'sha':
        rows[0]['sha256'] = '0'*64
    else:
        rows.pop()
    with pytest.raises(ValueError):
        components.validate_catalog(report, rows)


def test_catalog_assigns_mixed_status_before_component_manual_claims(corpus, monkeypatch):
    _, data, report = corpus
    rows = catalog_rows(report)
    for name in ('DATA','CORPUS'):
        monkeypatch.setattr(catalog, name, data if name=='DATA' else data/'corpus')
    write_json(data/'work_index.json', {'works':{r['slug']:{} for r in rows}})
    write_json(data/'corpus_editions.json', {r['slug']:{'source':r['source'],'edition':'dominant',
        'license':'PD','n_passages':int(r['passages'])} for r in rows})
    write_json(data/'work_token_totals.json', {r['slug']:{'tokens':int(r['tokens']),'tokens_lemmatized':0} for r in rows})
    for filename in ('ocr_quality_report.json','served_scheme_inference.json'):
        write_json(data/filename, {'works':{}})
    result, _ = catalog.build_rows()
    by_slug = {r[0]:dict(zip(catalog.COLUMNS,r)) for r in result}
    for slug in report['works']:
        if report['works'][slug]['mixed_ocr_digital']:
            assert by_slug[slug]['correction'] == 'mixed-unassessed'
    assert by_slug['cassius-dio.historiae-romanae']['source'] == 'perseus'


def test_release_publishes_exact_denominator_and_withholds_global_raw_bounds(corpus, monkeypatch):
    _, data, report = corpus
    rows = catalog_rows(report)
    path = write_catalog(data, rows)
    monkeypatch.setattr(release, 'DATA', data)
    monkeypatch.setattr(release, 'corrections_block', lambda *args: {})
    monkeypatch.setattr(release, 'polytonic_quality', lambda **kwargs: None)
    value = release.build(rows, path, 'corpus-2026-10-18.1','2026-10-18',None,None,0)
    raw = value['quality']['raw_ocr']
    assert raw['ocr_tokens'] == 5 and raw['ocr_works'] == 4
    assert raw['mixed_works'] == 3 and raw['mixed_ocr_tokens'] == 4
    assert raw['global_raw_token_bounds'] is None
    assert raw['legacy_homogeneous_work_bucket']['raw_tokens'] == 1
    assert value['sources']['perseus']['tokens'] == 4  # descriptive dominant rollup retained
    assert len(value['quality']['source_components']['mixed_works']) == 3


def test_provenance_includes_mixed_dio_and_does_not_promote_math_to_manual(corpus, monkeypatch):
    root, data, report = corpus
    rows = catalog_rows(report)
    write_json(data/'corpus_editions.json', {r['slug']:{'source':r['source'],'edition':'dominant',
        'n_analysis_tokens':int(r['tokens'])} for r in rows})
    write_json(data/'work_index.json', {'works':{r['slug']:{} for r in rows}})
    readme = root/'README.md'
    readme.write_text('1 of the 4 served works have no external id at all.\n'
        '`cts` on 0 works, `tlg` on 0,\n`wikidata` on 0)\n'+provenance.START+'\n'+provenance.END)
    monkeypatch.setattr(provenance,'DATA',data)
    monkeypatch.setattr(provenance,'README',readme)
    provenance.main()
    result = readme.read_text()
    assert '3 mixed/unassessed' in result
    for slug in report['works']:
        line = next(line for line in result.splitlines() if line.startswith('| '+slug+' |'))
        assert line.endswith('| mixed-unassessed |') if report['works'][slug]['mixed_ocr_digital'] else line.endswith('| raw OCR |')
    assert '0 manually corrected' in result


def test_known_limitations_share_denominator_and_reject_stale_catalog(corpus, monkeypatch):
    root, data, report = corpus
    rows = catalog_rows(report)
    path = write_catalog(data, rows)
    stamp = data/'correction_stamp_gap.json'
    graves = data/'nonfinal_graves.json'
    complete = data/'inventory/completeness-batch-report.json'
    write_json(stamp, {'raw_ocr':{'upper_bound_works':1,'upper_bound_tokens':1,
        'lower_bound_works':1,'lower_bound_tokens':1,'lower_bound_share_of_corpus_tokens':.1,
        'upper_bound_share_of_corpus_tokens':.1,'works_in_doubt':0,'tokens_in_doubt':0},
        'measured_against':{'catalog_sha256':components.sha(path.read_bytes()),
            'corpus_sha256':report['corpus_sha256'],'catalog':'data/corpus_catalog.tsv'}})
    write_json(graves, {'served_tokens':10,'forms':0,'tokens':0,'share':0,'works_touched':0})
    write_json(complete, {'cases':[]})
    for name, value in {'DATA':data,'REPO':root,'CATALOG':path,'STAMP_GAP':stamp,
                        'NONFINAL_GRAVES':graves,'COMPLETENESS':complete}.items():
        monkeypatch.setattr(limitations,name,value)
    value = limitations.build()
    measured = value['limitations'][1]['current_measurement']
    assert measured['ocr_component_tokens'] == 5
    assert measured['global_raw_token_bounds'] is None
    assert measured['legacy_homogeneous_work_bucket']['upper_bound_tokens'] == 1
    rows[0]['correction'] = 'manual'
    write_catalog(data, rows)
    with pytest.raises(ValueError, match='Mixed work'):
        limitations.build()
