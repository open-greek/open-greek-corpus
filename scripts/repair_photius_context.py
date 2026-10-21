#!/usr/bin/env python3
"""Repair digital occurrence annotations without selecting a source reading.

Each comparison uses an entire retained observed row. Short or unsupported
contexts remain explicitly unmatched; every optimal alignment edge survives.
Display text and the earlier source-review authority remain immutable. Only a
new, reversible annotation and lexical projection layer is admitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
import gzip
import json
from pathlib import Path

from audit_compression import compress_gzip
from assess_photius_historical import GAP_COST, _key, _local_alignment, _np, _substitution, tokens
import prepare_photius_review_campaign as campaign
import repair_photius_complete_review as complete

ROOT = Path(__file__).resolve().parents[1]
CORPUS, ALIASES = complete.CORPUS, complete.ALIASES
ARCHIVE = Path('data/corpus_changes/photius-bekker-context')
AUDIT = ARCHIVE / 'changes.json'
BEFORE = ARCHIVE / 'before-corpus.jsonl.gz'
BEFORE_ALIASES = ARCHIVE / 'before-aliases.json.gz'
PRIOR_REVIEW = ARCHIVE / 'prior-source-review.json.gz'
REVIEW = ARCHIVE / 'source-review.json.gz'
RECORDS = ARCHIVE / 'records.jsonl.gz'
SCHEMA = 'photius-contextual-digital-review-v1'
TAG = 'photius_context_review'
MIN_CONTEXT_TOKENS = 4
MIN_RELIABLE_ANCHORS = 3
DIGITAL_MASKS = frozenset({'digital-reading-disagreement', 'digital-insertion-boundary',
    'unpaired-available-digital-witness', 'unmapped-transcription-convention'})
RECIPE_NAMES = ('repair_photius_context.py', 'assess_photius_historical.py',
    'repair_photius_complete_review.py', 'prepare_photius_review_campaign.py', 'audit_compression.py')


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError('The first context admission requires an explicit recorded_at timestamp')
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Context admission time must be an ISO8601 UTC timestamp') from exc
    if 'T' not in value or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('Context admission time must be an ISO8601 UTC timestamp')
    return value


def _path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not value.startswith('data/'):
        raise ValueError('Context evidence requires a repository-relative data path')
    return path


def _observed(record):
    pieces, spans, cursor = [], [], 0
    for index, segment in enumerate(record['segments']):
        text = segment['scan']['observed_text']
        pieces.append(text)
        spans.append((cursor, cursor + len(text), index))
        cursor += len(text)
    return ''.join(pieces), spans


def _context_alignment(source,digital,neutral):
    """All optimal row paths with zero spelling cost for unresolved tokens.

    Neutral tokens retain position/gap accounting, but their tentative spelling
    cannot favor one occurrence over another. Only verified surrounding words
    can establish the contextual reliability anchors below.
    """
    if not neutral:
        return _local_alignment(source,digital)
    m,n=len(source),len(digital)
    exact=[j for j in range(n-m+1) if all(i in neutral or word==digital[j+i] for i,word in enumerate(source))]
    if exact:
        return {'cost':0,'starts':exact,'ends':[j+m for j in exact],
            'counterparts':[sorted(j+i for j in exact) for i in range(m)],
            'may_be_unaligned':[False]*m,'digital_only':[], 'ambiguous':len(exact)>1,'aligned':True}
    previous=[0]*(n+1)
    back=[bytearray(n+1)]
    for i,word in enumerate(source,1):
        if _np is not None and n:
            prior=_np.asarray(previous,dtype=_np.int64)
            costs=(_np.zeros(n,dtype=_np.int64) if i-1 in neutral else
                _np.fromiter((_substitution(word,other) for other in digital),dtype=_np.int64,count=n))
            diagonal,deletion=prior[:-1]+costs,prior[1:]+GAP_COST
            positions=_np.arange(n+1,dtype=_np.int64)*GAP_COST
            current=_np.minimum.accumulate(_np.r_[i*GAP_COST,
                _np.minimum(diagonal,deletion)-positions[1:]])+positions
            directions=bytearray(n+1);directions[0]=2
            directions[1:]=((diagonal==current[1:]).astype(_np.uint8)|
                ((deletion==current[1:]).astype(_np.uint8)<<1)|
                ((current[:-1]+GAP_COST==current[1:]).astype(_np.uint8)<<2)).tobytes()
        else:
            current=[i*GAP_COST]+[0]*n
            directions=bytearray(n+1);directions[0]=2
            for j,other in enumerate(digital,1):
                diagonal=previous[j-1]+(0 if i-1 in neutral else _substitution(word,other))
                deletion,insertion=previous[j]+GAP_COST,current[j-1]+GAP_COST
                best=min(diagonal,deletion,insertion)
                current[j]=best
                directions[j]=(int(diagonal==best)|int(deletion==best)<<1|int(insertion==best)<<2)
        back.append(directions);previous=current
    best=int(min(previous));ends=[j for j,v in enumerate(previous) if v==best]
    pending=[(m,j) for j in ends];seen=set();starts=set();inserted=set()
    candidates=[set() for _ in source];unmatched=[False]*m;ambiguous=len(ends)>1
    while pending:
        i,j=pending.pop()
        if (i,j) in seen:
            continue
        seen.add((i,j))
        if i==0:
            starts.add(j);continue
        direction=back[i][j]
        ambiguous |= direction not in (1,2,4)
        if direction&1:
            candidates[i-1].add(j-1);pending.append((i-1,j-1))
        if direction&2:
            unmatched[i-1]=True;pending.append((i-1,j))
        if direction&4:
            inserted.add(j-1);pending.append((i,j-1))
    return {'cost':best,'starts':sorted(starts),'ends':ends,
        'counterparts':[sorted(v) for v in candidates],'may_be_unaligned':unmatched,
        'digital_only':sorted(inserted),'ambiguous':bool(ambiguous),'aligned':best<m*GAP_COST}


def contextualize(record, full, *, digital_source=None):
    """Return effective segment pointers and a complete whole-row comparison.

    This is diagnostic association authority only. No token, neighboring row,
    grammatical preference, or exact word at a distant location can establish
    an isolated segment's occurrence independently of the entire observed row.
    """
    effective = deepcopy(record)
    digital_source = digital_source or next((r['source'] for s in record['segments']
        for r in s['readings'] if r['kind']=='digital'), {})
    observed, spans = _observed(record)
    source, digital = tokens(observed), tokens(full)
    section = next((r['section'] for s in record['segments'] for r in s['readings']
                    if r['kind'] == 'digital'), campaign.SECTION_PREFIX + str(record['physical_page'] + 277))
    reliable,neutral = [],set()
    for i, token in enumerate(source):
        if any(token['start']<b and a<token['end'] and
               (record['segments'][index]['verification']=='uncertain' or
                record['segments'][index]['text_role']!='authorial-body') for a,b,index in spans):
            neutral.add(i)
        owners = [index for a, b, index in spans if a <= token['start'] and token['end'] <= b]
        if len(owners) == 1:
            segment = record['segments'][owners[0]]
            if (segment['verification'] == 'verified' and segment['text_role'] == 'authorial-body'
                    and segment['scan']['observed_text'] == segment['corrected_text']):
                reliable.append(i)
    anchors = []
    if not record['digital_counterparts_usable']:
        status, aligned = 'source-mapping-exception', None
    elif not source or not digital:
        status, aligned = 'no-comparable-tokens', None
    elif len(source) < MIN_CONTEXT_TOKENS:
        status, aligned = 'insufficient-context', None
    else:
        aligned = _context_alignment([_key(t['text']) for t in source], [_key(t['text']) for t in digital],neutral)
        anchors = [i for i in reliable if aligned['counterparts'][i] and
            not aligned['may_be_unaligned'][i] and
            all(_key(source[i]['text']) == _key(digital[j]['text']) for j in aligned['counterparts'][i])]
        if (len(anchors) < MIN_RELIABLE_ANCHORS or not aligned['aligned']
                or aligned['cost'] > (len(source) - MIN_RELIABLE_ANCHORS) * GAP_COST):
            status = 'insufficient-context'
        else:
            status = 'ambiguous-context' if aligned['ambiguous'] else 'aligned-context'
    accepted = status in {'aligned-context', 'ambiguous-context'}
    context = {'basis': 'entire-ordered-observed-row', 'observed_text': observed,
        'observed_text_sha256': campaign.sha(observed.encode()), 'source_record_sha256': campaign.sha(campaign.canonical(record)),
        'section': section, 'section_sha256': campaign.sha(full.encode()),
        'status': status, 'minimum_context_tokens': MIN_CONTEXT_TOKENS,
        'minimum_reliable_anchors': MIN_RELIABLE_ANCHORS, 'reliable_source_indices': reliable,
        'exact_context_anchor_indices':anchors,
        'neutral_source_indices':sorted(neutral),
        'neutral_spelling_cost':0,
        'alignment': deepcopy(aligned), 'admission_authorized': False}
    annotations = []
    for a, b, index in spans:
        original = record['segments'][index]
        segment = effective['segments'][index]
        new_edges, projected = [], []
        local = tokens(segment['scan']['observed_text'])
        for token in local:
            owners = [i for i, item in enumerate(source)
                if item['start'] < a + token['end'] and a + token['start'] < item['end']]
            candidates = sorted({j for i in owners for j in aligned['counterparts'][i]}) if accepted else []
            unmatched = (not accepted or not owners or any(aligned['may_be_unaligned'][i] for i in owners))
            span = {k:token[k] for k in ('start', 'end', 'text')}
            projected.append({**span, 'may_be_unaligned': unmatched, 'counterpart_count':len(candidates),
                              'context_token_indices':owners})
            for j in candidates:
                target = digital[j]
                new_edges.append({'kind':'digital', 'section':section,
                    **{k:target[k] for k in ('start','end','text')}, 'review_span':span,
                    'may_be_unaligned':unmatched, 'source':deepcopy(digital_source),
                    'role':'context-bound-source-reading'})
        insertions = []
        if accepted:
            for j in aligned['digital_only']:
                adjacent = [t for t, p in zip(local, projected)
                    if any(j - 1 in aligned['counterparts'][i] or j + 1 in aligned['counterparts'][i]
                           for i in p['context_token_indices'])]
                if adjacent:
                    insertions.append({'digital_span':{k:digital[j][k] for k in ('start','end','text')},
                        'review_spans':[{k:t[k] for k in ('start','end','text')} for t in adjacent]})
        alignment = {'section':section, 'tokens':projected, 'ambiguous':bool(aligned and aligned['ambiguous']),
            'aligned':accepted, 'cost':aligned['cost'] if aligned else None, 'digital_insertions':insertions,
            'admission_authorized':False, 'context_status':status,
            'qualification':'Every optimal whole-row edge is retained; association does not resolve source uncertainty.'}
        original_edges = [deepcopy(r) for r in original['readings'] if r['kind']=='digital']
        segment['readings'] = [r for r in segment['readings'] if r['kind']!='digital'] + new_edges
        if record['digital_counterparts_usable']:
            segment['digital_alignment'] = alignment
        else:
            # Known unrelated comparison pages have explicit source-only
            # eligibility. An unmatched alignment must not create a new veto.
            segment.pop('digital_alignment',None)
            alignment = None
        annotations.append({'segment_index':index, 'original_span':{k:original[k] for k in ('start','end','original_text')},
            'original_span_sha256':campaign.sha(original['original_text'].encode()),
            'observed_text_sha256':campaign.sha(original['scan']['observed_text'].encode()),
            'original_digital_readings':original_edges, 'corrected_digital_readings':deepcopy(new_edges),
            'original_alignment':deepcopy(original.get('digital_alignment')), 'corrected_alignment':deepcopy(alignment)})
    return effective, {'locus':record['locus'], 'physical_page':record['physical_page'],
        'source_record_sha256':campaign.sha(campaign.canonical(record)), 'context':context,
        'segments':annotations, 'text_correction_authorized':False}


def _retained_masks(old):
    result = []
    for span in old['complete_source_review']['excluded_spans']:
        for evidence in span.get('evidence', [span]):
            if evidence.get('classification') not in DIGITAL_MASKS:
                result.append(deepcopy(evidence))
    return result


def plan(before, compiled_raw, library_raw, *, recorded_at):
    """Pure new-layer replay; retain exact prior rows and annotation preimages."""
    _timestamp(recorded_at)
    compiled = json.loads(compiled_raw)
    if compiled.get('schema') != campaign.COMPILED_SCHEMA or not compiled.get('scope_complete'):
        raise ValueError('Context review requires the completed frozen source campaign')
    pin = compiled['input_pins']['digital_archive']
    if campaign.sha(library_raw) != pin['sha256']:
        raise ValueError('Context comparison digital archive changed')
    document = json.loads(gzip.decompress(library_raw))
    sections = {s['id']:'\n'.join(b['text'] for b in s['blocks']) for s in document['sections']}
    if len(sections) != len(document['sections']):
        raise ValueError('Context digital sections repeat an identity')
    by_locus = {r['locus']:r for r in compiled['rows']}
    if len(by_locus) != len(compiled['rows']):
        raise ValueError('Context source review repeats a passage')
    outputs, changes, reviews = [], [], []
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        record = by_locus.pop(old['locus'], None)
        if record is None:
            outputs.append(line)
            continue
        if (old.get(TAG) or not old.get('complete_source_review') or
                old['complete_source_review']['record_sha256'] != campaign.sha(campaign.canonical(record))
                or old['text'] != record['corrected_text']):
            raise ValueError('Context annotation differs from its exact complete-review row')
        section = campaign.SECTION_PREFIX + str(record['physical_page'] + 277)
        if record['digital_counterparts_usable'] and section not in sections:
            raise ValueError('A usable context comparison section is missing')
        effective, review = contextualize(record, sections.get(section, ''),
            digital_source={k:pin[k] for k in ('path','sha256')})
        masks = _retained_masks(old) + complete._digital_exclusions(effective)
        masks += deepcopy(effective['additional_lexical_exclusions'])
        masks += deepcopy(effective['uncertainty_exclusion_candidates'])
        masks += deepcopy(effective['nonbody_exclusion_candidates'])
        unique = {campaign.canonical(m):m for m in masks}
        exclusions, runs = complete._projection(old['text'], list(unique.values()))
        new = deepcopy(old)
        new['analysis_text'] = ' '.join(runs)
        new[TAG] = {'schema':SCHEMA, 'audit':AUDIT.as_posix(), 'recorded_at':recorded_at,
            'review_sha256':campaign.sha(campaign.canonical(review)),
            'original_row_sha256':campaign.row_sha(old), 'context_status':review['context']['status'],
            'excluded_spans':exclusions, 'text_correction_authorized':False}
        changes.append({'locus':old['locus'], 'original_row':old, 'corrected_row':new,
            'original_row_sha256':campaign.row_sha(old), 'corrected_row_sha256':campaign.row_sha(new),
            'original_text':old['text'], 'corrected_text':new['text'],
            'recorded_at':recorded_at, 'annotation':review})
        reviews.append(review)
        outputs.append(campaign.canonical(new) + b'\n')
    if by_locus:
        raise ValueError('Context annotation does not cover its frozen rows')
    return b''.join(outputs), changes, reviews


def artifacts(before, compiled_raw, library_raw, aliases_before, *, recorded_at, pins, recipes):
    after, changes, reviews = plan(before, compiled_raw, library_raw, recorded_at=recorded_at)
    if len(after)>=100_000_000:
        raise ValueError('The context-annotated corpus exceeds the 100 MB Git object limit')
    review = {'schema':SCHEMA, 'recorded_at':recorded_at, 'source_pins':pins,
        'recipe_sha256':recipes, 'text_correction_authorized':False, 'rows':reviews}
    review_raw = compress_gzip(campaign.encode(review))
    records = compress_gzip(b''.join(campaign.canonical(c) + b'\n' for c in changes))
    outputs = {CORPUS:after, BEFORE:compress_gzip(before), BEFORE_ALIASES:compress_gzip(aliases_before),
        PRIOR_REVIEW:compress_gzip(compiled_raw), REVIEW:review_raw, RECORDS:records}
    counts = Counter(r['context']['status'] for r in reviews)
    audit = {'schema':SCHEMA, 'work':'photius.bibliotheca', 'recorded_at':recorded_at,
        'text_correction_authorized':False, 'input_corpus_sha256':campaign.sha(before),
        'output_corpus_sha256':campaign.sha(after), 'aliases_sha256':campaign.sha(aliases_before),
        'source_pins':pins, 'recipe_sha256':recipes,
        'counts':{'rows':len(changes), 'context_status':dict(sorted(counts.items())),
            'changed_display_rows':sum(c['original_text']!=c['corrected_text'] for c in changes),
            'changed_lexical_rows':sum(c['original_row']['analysis_text']!=c['corrected_row']['analysis_text'] for c in changes),
            'recompiled_pointer_segments':sum(s['original_digital_readings']!=s['corrected_digital_readings'] for r in reviews for s in r['segments'])},
        'outputs':{p.as_posix():campaign.sha(raw) for p,raw in outputs.items()}}
    return {**outputs,AUDIT:campaign.encode(audit)}, audit


def _recipe_pins(root):
    return {name:campaign.sha((Path(root)/'scripts'/name).read_bytes()) for name in RECIPE_NAMES}


def build(root=ROOT, *, recorded_at=None):
    root = Path(root)
    prior, _, original_before = complete._saved(root)
    before, compiled_raw = prior[CORPUS], gzip.decompress(prior[complete.REVIEW])
    compiled = json.loads(compiled_raw)
    if (root/AUDIT).exists():
        saved = json.loads((root/AUDIT).read_bytes())
        if recorded_at is not None and recorded_at != saved['recorded_at']:
            raise ValueError('A frozen context admission timestamp cannot change')
        recorded_at = saved['recorded_at']
    _timestamp(recorded_at)
    pins, sources = {}, {}
    for name,pin in compiled['input_pins'].items():
        path = _path(pin['path'])
        raw = original_before if name=='corpus' else (root/path).read_bytes()
        if campaign.sha(raw) != pin['sha256']:
            raise ValueError('A context source changed or was invalidated: '+name)
        pins[name] = deepcopy(pin)
        sources[name] = raw
    for path in (complete.AUDIT,complete.REVIEW,complete.RECORDS):
        raw = (root/path).read_bytes()
        pins[path.as_posix()] = {'path':path.as_posix(),'sha256':campaign.sha(raw)}
    aliases = (root/ALIASES).read_bytes()
    if aliases != prior[ALIASES]:
        raise ValueError('Context review requires its exact prior aliases')
    return artifacts(before,compiled_raw,sources['digital_archive'],aliases,
        recorded_at=recorded_at,pins=pins,recipes=_recipe_pins(root))


def _later_bytes(raw, root):
    if b'"photius_uncertainty_review"' in raw:
        from repair_photius_uncertainties import restore_before_bytes as restore
        return restore(raw,root)
    return raw


def _later_row(row, root):
    if row.get('photius_uncertainty_review'):
        from repair_photius_uncertainties import restore_before_row as restore
        return restore(row,root)
    return row


@lru_cache(maxsize=1)
def _literal_saved(audit_raw,before_raw,alias_raw,prior_raw,review_raw,raw_records):
    """Pure literal replay; callers reread every frozen byte before using it."""
    audit = json.loads(audit_raw)
    for path,raw in zip((BEFORE,BEFORE_ALIASES,PRIOR_REVIEW,REVIEW,RECORDS),
                       (before_raw,alias_raw,prior_raw,review_raw,raw_records)):
        if campaign.sha(raw)!=audit['outputs'][path.as_posix()]:
            raise ValueError('Frozen context annotation artifact changed')
    before = gzip.decompress(before_raw)
    aliases = gzip.decompress(alias_raw)
    changes = list(map(json.loads,gzip.decompress(raw_records).splitlines()))
    review = json.loads(gzip.decompress(review_raw))
    original_review = json.loads(gzip.decompress(prior_raw))
    original_records = {r['locus']:r for r in original_review['rows']}
    by_locus = {c['locus']:c for c in changes}
    if (audit.get('schema')!=SCHEMA or audit.get('text_correction_authorized') is not False or
            len(by_locus)!=len(changes) or campaign.sha(before)!=audit['input_corpus_sha256'] or
            len(original_records)!=len(original_review['rows']) or
            campaign.sha(aliases)!=audit['aliases_sha256'] or
            audit['outputs'][CORPUS.as_posix()]!=audit['output_corpus_sha256'] or
            review.get('schema')!=SCHEMA or review.get('text_correction_authorized') is not False or
            any(review.get(k)!=audit[k] for k in ('recorded_at','source_pins','recipe_sha256')) or
            review.get('rows')!=[c['annotation'] for c in changes] or
            audit['counts']['rows']!=len(changes)):
        raise ValueError('Frozen context admission identity changed')
    output,seen = [],set()
    for line in before.splitlines(keepends=True):
        old = json.loads(line)
        change = by_locus.get(old['locus'])
        if change is None:
            output.append(line)
            continue
        new = change['corrected_row']
        annotation = change['annotation']
        original_record = original_records.get(old['locus'])
        allowed = deepcopy(old)
        allowed.update(analysis_text=new['analysis_text'],**{TAG:new[TAG]})
        if (old!=change['original_row'] or campaign.row_sha(old)!=change['original_row_sha256'] or
                campaign.row_sha(new)!=change['corrected_row_sha256'] or old['text']!=new['text'] or
                new!=allowed or new[TAG].get('schema')!=SCHEMA or new[TAG].get('text_correction_authorized') is not False or
                new[TAG]['original_row_sha256']!=change['original_row_sha256'] or
                new[TAG]['recorded_at']!=audit['recorded_at'] or new[TAG]['audit']!=AUDIT.as_posix() or
                old['complete_source_review']!=new['complete_source_review'] or
                new[TAG]['review_sha256']!=campaign.sha(campaign.canonical(annotation)) or
                not original_record or annotation['source_record_sha256']!=campaign.sha(campaign.canonical(original_record)) or
                annotation['context']['observed_text']!=_observed(original_record)[0] or
                annotation['context']['observed_text_sha256']!=campaign.sha(annotation['context']['observed_text'].encode())):
            raise ValueError('Context row preimage, postimage, or annotation changed')
        if len(annotation['segments'])!=len(original_record['segments']):
            raise ValueError('Context annotation omitted an original source segment')
        for index,(item,original) in enumerate(zip(annotation['segments'],original_record['segments'])):
            if (item['segment_index']!=index or item['original_span']!={k:original[k] for k in ('start','end','original_text')} or
                    item['original_span_sha256']!=campaign.sha(original['original_text'].encode()) or
                    item['original_alignment']!=original.get('digital_alignment') or
                    item['original_digital_readings']!=[r for r in original['readings'] if r['kind']=='digital']):
                raise ValueError('Context annotation original span or pointer preimage changed')
        _,runs = complete._projection(new['text'],new[TAG]['excluded_spans'])
        if new['analysis_text']!=' '.join(runs):
            raise ValueError('Frozen context lexical projection changed')
        output.append(campaign.canonical(new)+b'\n')
        seen.add(old['locus'])
    after = b''.join(output)
    if seen!=set(by_locus) or campaign.sha(after)!=audit['output_corpus_sha256']:
        raise ValueError('Context admission literal replay changed')
    return before,after,aliases,audit,by_locus


def _saved(root):
    before,after,aliases,audit,rows = _literal_saved(*((Path(root)/p).read_bytes()
        for p in (AUDIT,BEFORE,BEFORE_ALIASES,PRIOR_REVIEW,REVIEW,RECORDS)))
    return before,after,aliases,deepcopy(audit),rows


@lru_cache(maxsize=2)
def _record_map(raw):
    records = list(map(json.loads,gzip.decompress(raw).splitlines()))
    result = {c['locus']:c for c in records}
    if len(result)!=len(records):
        raise ValueError('Context annotation records repeat a passage')
    return result


def restore_before_bytes(raw,root=ROOT):
    raw = _later_bytes(raw,root)
    if b'"'+TAG.encode()+b'"' not in raw:
        return raw
    before,after,_,_,_ = _saved(root)
    if raw!=after:
        raise ValueError('Context corpus differs from its exact postimage')
    return before


def restore_before_row(row,root=ROOT):
    row = _later_row(row,root)
    if not row.get(TAG):
        return deepcopy(row)
    root = Path(root)
    audit = json.loads((root/AUDIT).read_bytes())
    raw = (root/RECORDS).read_bytes()
    if (audit.get('schema')!=SCHEMA or audit.get('text_correction_authorized') is not False or
            campaign.sha(raw)!=audit['outputs'][RECORDS.as_posix()] or
            row[TAG].get('schema')!=SCHEMA or row[TAG].get('text_correction_authorized') is not False or
            row[TAG]['recorded_at']!=audit['recorded_at']):
        raise ValueError('Context row annotation authority changed')
    changes = _record_map(raw)
    change = changes.get(row.get('locus'))
    if (not change or row!=change['corrected_row'] or
            campaign.row_sha(row)!=change['corrected_row_sha256'] or
            campaign.row_sha(change['original_row'])!=change['original_row_sha256'] or
            row[TAG]['review_sha256']!=campaign.sha(campaign.canonical(change['annotation']))):
        raise ValueError('Context row differs from its exact postimage')
    return deepcopy(change['original_row'])


def lexical_segments(row,root=ROOT):
    row = _later_row(row,root)
    if not row.get(TAG):
        raise ValueError('Context lexical projection has no annotation authority')
    restore_before_row(row,root)
    _,runs = complete._projection(row['text'],row[TAG]['excluded_spans'])
    if row['analysis_text']!=' '.join(runs):
        raise ValueError('Context lexical projection changed')
    return runs


def check(root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        if b'"'+TAG.encode()+b'"' in (root/CORPUS).read_bytes():
            raise ValueError('Context annotations have no frozen audit')
        return None
    outputs,audit = build(root)
    before,after,aliases,_,_ = _saved(root)
    current = _later_bytes((root/CORPUS).read_bytes(),root)
    if current not in {before,after} or (root/ALIASES).read_bytes()!=aliases:
        raise ValueError('Context corpus or aliases changed outside its annotation audit')
    if any((root/p).read_bytes()!=raw for p,raw in outputs.items() if p!=CORPUS):
        raise ValueError('Context annotations no longer reproduce from current source evidence')
    return None if current==before else audit


def active_metadata(root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        return None
    before,after,aliases,audit,_ = _saved(root)
    current = _later_bytes((root/CORPUS).read_bytes(),root)
    if (root/ALIASES).read_bytes()!=aliases or current not in {before,after}:
        raise ValueError('Current context corpus or aliases differs from its exact admission')
    if current==before:
        return None
    return {'audit':{'path':AUDIT.as_posix(),'sha256':campaign.sha((root/AUDIT).read_bytes())},
        'source_review':{'path':REVIEW.as_posix(),'sha256':audit['outputs'][REVIEW.as_posix()]},
        'counts':deepcopy(audit['counts']),'text_correction_authorized':False}


def apply(root=ROOT,*,recorded_at=None):
    root = Path(root)
    outputs,audit = build(root,recorded_at=recorded_at)
    before = gzip.decompress(outputs[BEFORE])
    if (root/CORPUS).read_bytes() not in {before,outputs[CORPUS]}:
        raise ValueError('Context admission requires its exact preceding stage')
    for path,raw in outputs.items():
        if path!=CORPUS and (root/path).exists() and (root/path).read_bytes()!=raw:
            raise ValueError('Refusing to overwrite a frozen context annotation artifact')
    for path,raw in outputs.items():
        if path!=CORPUS:
            (root/path).parent.mkdir(parents=True,exist_ok=True)
            (root/path).write_bytes(raw)
    (root/CORPUS).write_bytes(outputs[CORPUS])
    return audit


def undo(root=ROOT):
    root = Path(root)
    before,after,aliases,audit,_ = _saved(root)
    if (root/CORPUS).read_bytes()!=after or (root/ALIASES).read_bytes()!=aliases:
        raise ValueError('Undo later layers before restoring context annotations')
    (root/CORPUS).write_bytes(before)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--recorded-at')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apply',action='store_true')
    group.add_argument('--undo',action='store_true')
    group.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.apply:
        result = apply(args.root,recorded_at=args.recorded_at)
    elif args.undo:
        result = undo(args.root)
    elif args.check:
        result = check(args.root)
    else:
        _,result = build(args.root,recorded_at=args.recorded_at)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
