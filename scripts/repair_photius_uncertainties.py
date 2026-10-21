#!/usr/bin/env python3
"""Resolve explicitly reviewed Photius uncertainties above the context layer.

Only exact uncertain segments may change. Every unrelated exclusion cause is
retained; overlapping causes conservatively cover the replacement. Frozen rows
and authorities support exact reversal without live correction sources.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
from types import ModuleType

from audit_compression import compress_gzip
import prepare_photius_review_campaign as campaign

ROOT = Path(__file__).resolve().parents[1]
CORPUS = campaign.CORPUS
ARCHIVE = Path('data/corpus_changes/photius-bekker-uncertainties')
AUDIT = ARCHIVE / 'changes.json'
BEFORE = ARCHIVE / 'before-corpus.jsonl.gz'
REVIEW = ARCHIVE / 'source-review.json'
RECORDS = ARCHIVE / 'records.jsonl.gz'
TABLE = Path('scripts/photius_uncertainty_observations.py')
FROZEN_TABLE = ARCHIVE / 'source-table.py'
COMPILED = ARCHIVE / 'complete-review.json.gz'
TAG = 'photius_uncertainty_review'
SCHEMA = 'photius-source-uncertainty-resolution-v1'
ROLES = {'corroborating', 'contrary', 'edition-variant', 'context'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def row_sha(row):
    return sha(campaign.canonical(row))


def _path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Source requires a repository-relative path')
    return path


def _box(value):
    if (not isinstance(value, (tuple, list)) or len(value) != 4 or
            any(type(x) not in (int, float) for x in value) or
            not 0 <= value[0] < value[2] <= 1 or not 0 <= value[1] < value[3] <= 1):
        raise ValueError('Source region must be an exact normalized rectangle')
    return list(value)


def _flatten(text, spans):
    """Expose each independent cause beneath merged exclusion envelopes."""
    result = []
    for span in spans:
        a, b = span['start'], span['end']
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text) or text[a:b] != span['text']:
            raise ValueError('Inherited exclusion does not match its exact source span')
        children = span.get('evidence')
        if isinstance(children, list):
            leaves = _flatten(text, children)
            if not leaves or any(x['start'] < a or x['end'] > b for x in leaves):
                raise ValueError('Merged exclusion lost its independent causes')
            result.extend(leaves)
        else:
            result.append(deepcopy(span))
    return result


def _projection(text, leaves):
    merged = []
    for leaf in sorted(leaves, key=lambda x: (x['start'], x['end'])):
        a, b = leaf['start'], leaf['end']
        if not 0 <= a < b <= len(text) or text[a:b] != leaf['text']:
            raise ValueError('Rebased exclusion changed')
        if merged and a <= merged[-1]['end']:
            old = merged.pop(); a, b = old['start'], max(b, old['end'])
            evidence = old['evidence']+[deepcopy(leaf)]
        else:
            evidence = [deepcopy(leaf)]
        merged.append({'start': a, 'end': b, 'text': text[a:b], 'evidence': evidence})
    cursor, runs = 0, []
    for span in merged:
        runs.append(text[cursor:span['start']]); cursor = span['end']
    runs.append(text[cursor:])
    return merged, runs


def _masks(row):
    if TAG in row:
        return row[TAG]['excluded_spans']
    context = row.get('photius_context_review')
    if context is not None:
        if 'excluded_spans' not in context:
            raise ValueError('Context review must expose its effective excluded_spans')
        return context['excluded_spans']
    return row['complete_source_review']['excluded_spans']


def _crop(raw, kind, page, box):
    import pymupdf
    with pymupdf.open(stream=raw, filetype='pdf' if kind == 'pdf' else None) as source:
        if kind != 'pdf':
            pdf = pymupdf.open('pdf', source.convert_to_pdf())
            try:
                return campaign._render_crop_png(pdf, 1, box, 3600)
            finally:
                pdf.close()
        if not 1 <= page <= len(source):
            raise ValueError('Source physical page is outside its pinned PDF')
        return campaign._render_crop_png(source, page, box, 3600)


def compile_review(before, compiled_raw, table_raw, *, reviewed_at, decisions, sources,
                   source_files, expected_scope=None):
    """Compile exact source decisions; source_files contains immutable byte snapshots."""
    campaign._timestamp(reviewed_at)
    compiled = json.loads(compiled_raw)
    if compiled.get('schema') != campaign.COMPILED_SCHEMA or not compiled.get('scope_complete'):
        raise ValueError('Uncertainty resolution requires a complete frozen review')
    by_review = {r['locus']: r for r in compiled['rows']}
    rows = {r['locus']: r for r in map(json.loads, before.splitlines())}
    scope = {(r['locus'], i) for r in compiled['rows'] if r['physical_page'] in {169, 170}
             for i, s in enumerate(r['segments']) if s['verification'] == 'uncertain'}
    keys = [(d['locus'], d['segment_index']) for d in decisions]
    if len(keys) != len(set(keys)) or (expected_scope is not None and
            (set(map(tuple, expected_scope)) != scope or set(keys) != scope)):
        raise ValueError('Decisions must account for every declared uncertain segment exactly once')
    scan = {**compiled['input_pins']['scan'], 'kind': 'pdf'}
    all_sources = {'bekker': scan, **deepcopy(sources)}
    if sources.get('bekker'):
        raise ValueError('The frozen Bekker source cannot be overridden')
    for value in all_sources.values():
        path = _path(value['path']).as_posix()
        if value.get('kind') not in {'pdf', 'image'} or sha(source_files[path]) != value['sha256']:
            raise ValueError('A reviewed source changed or was invalidated')
    images, records, rendered = {}, [], {}
    def pin(source_id, page, region):
        value = all_sources[source_id]; box = _box(region)
        if type(page) is not int or page < 1 or value['kind'] == 'image' and page != 1:
            raise ValueError('Source crop requires a positive physical page')
        key = value['sha256'], value['kind'], page, tuple(box)
        if key not in rendered:
            rendered[key] = _crop(source_files[value['path']], value['kind'], page, box)
        raw = rendered[key]
        path = ARCHIVE / 'source-images' / (sha(raw)+'.png'); images[path] = raw
        return {'source_id': source_id, 'source': value, 'scan_page': page, 'region': box,
                'max_side': 3600, 'image': {'path': path.as_posix(), 'sha256': sha(raw)}}
    for item in decisions:
        item = deepcopy(item); locus, index = item['locus'], item['segment_index']
        if type(index) is not int or (locus, index) not in scope or locus not in rows:
            raise ValueError('Only named uncertain segments on pages 169 and 170 may be reviewed')
        record, old = by_review[locus], rows[locus]
        segment = record['segments'][index]; a, b = segment['corrected_start'], segment['corrected_end']
        if (not old.get('complete_source_review') or old.get(TAG) or
                old['text'][a:b] != item['original_text'] or segment['corrected_text'] != item['original_text']):
            raise ValueError('Uncertainty decision differs from the exact served segment')
        if (item['decision'] not in {'resolved', 'retained-uncertain'} or
                not isinstance(item.get('corrected_text'), str) or not item['corrected_text'].strip() or
                not isinstance(item.get('evidence'), str) or not item['evidence'].strip() or
                item['decision'] == 'retained-uncertain' and item['corrected_text'] != item['original_text']):
            raise ValueError('A decision needs a retained or explicitly source-resolved reading and evidence')
        bekker = pin('bekker', record['physical_page'], item['bekker_region'])
        comparisons = []
        for comparison in item.get('comparisons', []):
            if (comparison.get('role') not in ROLES or comparison.get('source_id') not in sources or
                    not isinstance(comparison.get('text'), str) or not comparison['text'].strip() or
                    not comparison.get('printed_page')):
                raise ValueError('Comparison requires exact source text, edition role, and printed page')
            if comparison['role'] == 'corroborating' and comparison['text'] != item['corrected_text']:
                raise ValueError('A corroborating comparison must match the reviewed reading exactly')
            source = sources[comparison['source_id']]
            page = comparison.get('scan_page', 1 if source['kind'] == 'image' else None)
            comparisons.append({**comparison, **pin(comparison['source_id'], page, comparison['region'])})
        records.append({**item, 'start': a, 'end': b, 'original_row_sha256': row_sha(old),
            'original_segment': segment, 'bekker': bekker, 'comparisons': comparisons})
    if not records:
        raise ValueError('No completed uncertainty decisions were supplied')
    review = {'schema_version': 1, 'schema': SCHEMA, 'work': 'photius.bibliotheca',
        'reviewed_at': reviewed_at, 'input_corpus_sha256': sha(before),
        'source_table': {'path': TABLE.as_posix(), 'sha256': sha(table_raw)},
        'compiled_review': {'path': COMPILED.as_posix(), 'uncompressed_sha256': sha(compiled_raw)},
        'sources': all_sources, 'records': records,
        'baseline_uncertainty_spans': sum(s.get('verification') == 'uncertain'
            for r in compiled['rows'] for s in r['segments'])}
    return review, images


def _rebase(leaf, decisions, text):
    original = deepcopy(leaf); a, b = leaf['start'], leaf['end']
    def boundary(position, right):
        delta = 0
        for d in decisions:
            x, y, n = d['start'], d['end'], len(d['corrected_text'])
            if position >= y:
                delta += n-(y-x)
            elif position > x:
                return x+delta+(n if right else 0)
            else:
                break
        return position+delta
    low, high = boundary(a, False), boundary(b, True)
    leaf = deepcopy(leaf); leaf.update(start=low, end=high, text=text[low:high])
    if any(d['start'] < b and a < d['end'] and d['corrected_text'] != d['original_text'] for d in decisions):
        leaf['rebase'] = {'policy': 'overlap-covers-whole-reviewed-replacement', 'original_exclusion': original}
    return leaf


def plan(before, review_raw):
    review = json.loads(review_raw)
    if (review.get('schema') != SCHEMA or review.get('schema_version') != 1 or
            review.get('work') != 'photius.bibliotheca' or review.get('input_corpus_sha256') != sha(before)):
        raise ValueError('Uncertainty authority differs from its exact preimage')
    campaign._timestamp(review['reviewed_at'])
    reference = {'path': REVIEW.as_posix(), 'sha256': sha(review_raw)}
    grouped = {}
    for d in review['records']:
        grouped.setdefault(d['locus'], []).append(d)
    output, changes = [], []
    for line in before.splitlines(keepends=True):
        old = json.loads(line); locus = old['locus']
        if locus not in grouped:
            output.append(line); continue
        if old.get(TAG):
            raise ValueError('Uncertainty layer cannot apply twice')
        decisions = sorted(grouped.pop(locus), key=lambda d:d['start'])
        leaves = _flatten(old['text'], _masks(old)); cursor, pieces = 0, []
        removed = []
        for d in decisions:
            a, b = d['start'], d['end']
            if (type(a) is not int or type(b) is not int or not cursor <= a < b <= len(old['text']) or
                    old['text'][a:b] != d['original_text'] or row_sha(old) != d['original_row_sha256'] or
                    d['decision'] not in {'resolved', 'retained-uncertain'} or
                    not isinstance(d['corrected_text'], str) or not d['corrected_text'].strip() or
                    d['original_segment'].get('verification') != 'uncertain' or
                    d['original_segment'].get('corrected_text') != d['original_text'] or
                    not d.get('evidence') or not d.get('bekker')):
                raise ValueError('Uncertainty record changed its exact original or source decision')
            matches = [x for x in leaves if x['start']==a and x['end']==b and
                x.get('classification')=='unresolved-source-reading' and
                x.get('qualification')==d['original_segment'].get('uncertainty')]
            if not matches:
                raise ValueError('The exact source uncertainty cause is missing')
            if d['decision']=='resolved':
                removed.extend(matches); leaves = [x for x in leaves if x not in matches]
            elif d['corrected_text'] != d['original_text']:
                raise ValueError('Retained uncertainty cannot silently change display')
            pieces.extend((old['text'][cursor:a],d['corrected_text'])); cursor=b
        pieces.append(old['text'][cursor:]); text=''.join(pieces)
        remaining = [_rebase(x,decisions,text) for x in leaves]
        for d in decisions:
            if any(c['role']=='contrary' for c in d['comparisons']):
                start = d['start']+sum(len(x['corrected_text'])-(x['end']-x['start']) for x in decisions if x['end']<=d['start'])
                remaining.append({'start':start,'end':start+len(d['corrected_text']), 'text':d['corrected_text'],
                    'classification':'retained-contrary-source-reading','alternatives':deepcopy(d['comparisons']),
                    'evidence':d['evidence']})
        exclusions,runs=_projection(text,remaining)
        new=deepcopy(old);new.update(text=text,analysis_text=' '.join(runs))
        new[TAG]={'schema':SCHEMA,'source_review':reference,'original_row_sha256':row_sha(old),
            'excluded_spans':exclusions,'decisions':len(decisions),
            'resolved':sum(d['decision']=='resolved' for d in decisions),
            'retained_uncertain':sum(d['decision']=='retained-uncertain' for d in decisions),
            'qualification':'Occurrence-scoped scan resolutions; frozen campaign and context annotations remain unchanged. Other exclusion causes and all comparison readings survive.'}
        changes.append({'locus':locus,'original_row':old,'corrected_row':new,
            'original_row_sha256':row_sha(old),'corrected_row_sha256':row_sha(new),
            'decisions':decisions,'removed_uncertainty_causes':removed,
            'remaining_exclusion_causes':remaining,'reviewed_at':review['reviewed_at']})
        output.append(campaign.canonical(new)+b'\n')
    if grouped:
        raise ValueError('Uncertainty review invents a passage')
    ds=review['records']
    counts={'rows':len(changes),'decisions':len(ds),
        'resolved_changed':sum(d['decision']=='resolved' and d['original_text']!=d['corrected_text'] for d in ds),
        'resolved_unchanged':sum(d['decision']=='resolved' and d['original_text']==d['corrected_text'] for d in ds),
        'retained_uncertain':sum(d['decision']=='retained-uncertain' for d in ds),
        'baseline_uncertainty_spans':review['baseline_uncertainty_spans'],
        'current_uncertainty_spans':review['baseline_uncertainty_spans']-sum(d['decision']=='resolved' for d in ds),
        'inherited_remaining_uncertainties':sum(x.get('classification')=='unresolved-source-reading'
             for c in changes for x in c['remaining_exclusion_causes']),
        'remaining_exclusion_causes':sum(len(c['remaining_exclusion_causes']) for c in changes),
        'primary_rows_before':len(before.splitlines()),'primary_rows_after':len(output)}
    return b''.join(output),changes,counts


def artifacts(before,review_raw,table_raw,compiled_raw,images):
    review=json.loads(review_raw)
    if sha(table_raw)!=review['source_table']['sha256'] or sha(compiled_raw)!=review['compiled_review']['uncompressed_sha256']:
        raise ValueError('Frozen source table or compiled authority changed')
    after,changes,counts=plan(before,review_raw)
    records=compress_gzip(b''.join(campaign.canonical(c)+b'\n' for c in changes))
    files={BEFORE:compress_gzip(before),REVIEW:review_raw,RECORDS:records,FROZEN_TABLE:table_raw,
           COMPILED:compress_gzip(compiled_raw),**images}
    audit={'schema_version':1,'schema':SCHEMA,'work':'photius.bibliotheca',
        'reviewed_at':review['reviewed_at'],'input_corpus_sha256':sha(before),'output_corpus_sha256':sha(after),
        'source_review':{'path':REVIEW.as_posix(),'sha256':sha(review_raw)},'sources':review['sources'],
        'counts':counts,'outputs':{p.as_posix():sha(raw) for p,raw in files.items()}}
    return {CORPUS:after,**files,AUDIT:encode(audit)},audit


def build(root=ROOT):
    root=Path(root)
    before=gzip.decompress((root/BEFORE).read_bytes()) if (root/AUDIT).exists() else (root/CORPUS).read_bytes()
    table_raw=(root/TABLE).read_bytes();module=ModuleType('photius_uncertainty_source_table')
    exec(compile(table_raw,TABLE.as_posix(),'exec'),module.__dict__)
    from repair_photius_complete_review import REVIEW as complete_review
    compiled_raw=gzip.decompress((root/complete_review).read_bytes())
    compiled=json.loads(compiled_raw)
    sources={'bekker':{**compiled['input_pins']['scan'],'kind':'pdf'},**module.SOURCES}
    source_files={v['path']:(root/_path(v['path'])).read_bytes() for v in sources.values()}
    expected=getattr(module,'EXPECTED_SCOPE',None)
    if expected is None:
        raise ValueError('The production source table must declare its complete EXPECTED_SCOPE')
    decisions=module.records()
    targets={d['locus'] for d in decisions}
    for row in map(json.loads,before.splitlines()):
        if row['locus'] in targets:
            if not row.get('photius_context_review'):
                raise ValueError('The uncertainty layer requires its exact context predecessor')
            from repair_photius_context import lexical_segments as context_segments
            context_segments(row,root)
    review,images=compile_review(before,compiled_raw,table_raw,reviewed_at=module.REVIEWED_AT,
        decisions=decisions,sources=module.SOURCES,source_files=source_files,expected_scope=expected)
    return artifacts(before,encode(review),table_raw,compiled_raw,images)


@lru_cache(maxsize=2)
def _record_map(raw):
    records=list(map(json.loads,gzip.decompress(raw).splitlines()))
    if len({r['locus'] for r in records})!=len(records):
        raise ValueError('Uncertainty archive repeats a passage')
    return {r['locus']:r for r in records}


def _row_archive(root):
    root=Path(root);audit_raw=(root/AUDIT).read_bytes();audit=json.loads(audit_raw)
    records=(root/RECORDS).read_bytes();review=(root/REVIEW).read_bytes()
    if (audit.get('schema')!=SCHEMA or sha(records)!=audit['outputs'][RECORDS.as_posix()] or
            audit['source_review']!={'path':REVIEW.as_posix(),'sha256':sha(review)}):
        raise ValueError('Uncertainty row archive changed')
    return audit,_record_map(records)


def _saved(root):
    root=Path(root);audit,records=_row_archive(root)
    for path,digest in audit['outputs'].items():
        if sha((root/_path(path)).read_bytes())!=digest:
            raise ValueError('Frozen uncertainty artifact changed')
    before=gzip.decompress((root/BEFORE).read_bytes())
    after,changes,counts=plan(before,(root/REVIEW).read_bytes())
    if (sha(before)!=audit['input_corpus_sha256'] or sha(after)!=audit['output_corpus_sha256'] or
            {c['locus']:c for c in changes}!=records or counts!=audit['counts']):
        raise ValueError('Frozen uncertainty replay differs from its exact postimage')
    return before,after,audit


def restore_before_bytes(raw,root=ROOT):
    if b'"photius_uncertainty_review"' not in raw:
        return raw
    before,after,_=_saved(root)
    if raw!=after:
        raise ValueError('Uncertainty corpus differs from its exact postimage')
    return before


def restore_before_row(row,root=ROOT):
    if not row.get(TAG):
        return deepcopy(row)
    audit,records=_row_archive(root);change=records.get(row.get('locus'))
    if (not change or row!=change['corrected_row'] or row_sha(row)!=change['corrected_row_sha256'] or
            row_sha(change['original_row'])!=change['original_row_sha256'] or
            row[TAG]['source_review']!=audit['source_review'] or
            row[TAG]['original_row_sha256']!=change['original_row_sha256']):
        raise ValueError('Uncertainty row differs from its exact postimage')
    return deepcopy(change['original_row'])


def lexical_segments(row,root=ROOT):
    if not row.get(TAG):
        raise ValueError('Uncertainty projection has no source authority')
    restore_before_row(row,root)
    _,runs=_projection(row['text'],_flatten(row['text'],row[TAG]['excluded_spans']))
    if row.get('analysis_text')!=' '.join(runs):
        raise ValueError('Uncertainty lexical projection changed')
    return runs


def check(root=ROOT):
    root=Path(root)
    if not (root/AUDIT).exists():
        if b'"photius_uncertainty_review"' in (root/CORPUS).read_bytes():
            raise ValueError('Uncertainty metadata has no admission audit')
        return None
    outputs,audit=build(root);current=(root/CORPUS).read_bytes()
    before=gzip.decompress(outputs[BEFORE])
    for path,raw in outputs.items():
        if path==CORPUS and current==before:
            continue
        if (root/path).read_bytes()!=raw:
            raise ValueError('Uncertainty admission no longer reproduces')
    return None if current==before else audit


def active_metadata(root=ROOT):
    root=Path(root)
    if not (root/AUDIT).exists():
        return None
    before,after,audit=_saved(root);current=(root/CORPUS).read_bytes()
    if current==before:
        return None
    if current!=after:
        raise ValueError('Uncertainty corpus differs from its frozen admission')
    return {'audit':{'path':AUDIT.as_posix(),'sha256':sha((root/AUDIT).read_bytes())},
        'source_review':audit['source_review'],'counts':audit['counts'],'sources':audit['sources'],
        'qualification':'Later occurrence-scoped source resolutions; original complete-review statuses and all old audits remain frozen.'}


def apply(root=ROOT):
    root=Path(root);outputs,audit=build(root)
    if sha((root/CORPUS).read_bytes()) not in {audit['input_corpus_sha256'],audit['output_corpus_sha256']}:
        raise ValueError('Uncertainty application requires its exact context predecessor')
    for path,raw in outputs.items():
        if path!=CORPUS and (root/path).exists() and (root/path).read_bytes()!=raw:
            raise ValueError('Refusing to replace an immutable uncertainty artifact')
    for path,raw in outputs.items():
        if path!=CORPUS:
            (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_bytes(raw)
    (root/CORPUS).write_bytes(outputs[CORPUS])
    return audit


def undo(root=ROOT):
    root=Path(root);before,after,_=_saved(root)
    if (root/CORPUS).read_bytes() not in {before,after}:
        raise ValueError('Undo later layers before the uncertainty layer')
    (root/CORPUS).write_bytes(before)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--apply',action='store_true');group.add_argument('--undo',action='store_true')
    group.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.undo:
        undo();return
    print(json.dumps(apply() if args.apply else check() if args.check else build()[1],ensure_ascii=False))

if __name__=='__main__':
    main()
