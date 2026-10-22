#!/usr/bin/env python3
"""Admit joint Photius word decisions and explicit nonlexical dispositions.

Every decision starts from the exact published continuation. Joint words have
one display owner, while original rows, source variants, and aliases survive in
an independently reversible archive. Older source judgments remain historical.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
import gzip
import importlib
import json
from pathlib import Path

from audit_compression import compress_gzip
import repair_photius_editorial_continuation as previous

ROOT = previous.ROOT
CORPUS, ALIASES = previous.CORPUS, previous.ALIASES
ARCHIVE = Path('data/corpus_changes/photius-bekker-final-review')
AUDIT = ARCHIVE/'changes.json'
SOURCE_REVIEW = ARCHIVE/'source-review.json'
REVIEW = ARCHIVE/'compiled-review.json.gz'
BEFORE = ARCHIVE/'before-corpus.jsonl.gz'
BEFORE_ALIASES = ARCHIVE/'before-aliases.json.gz'
RECORDS = ARCHIVE/'records.jsonl.gz'
TAG = 'photius_final_review'
SCHEMA = 'photius-final-source-review-v1'
BASELINE_SHA256 = 'aa39e3465387f5f192a509acbb7b8107c4641e3bf2a92bdf774d3253b2c7a1a0'
ALIASES_SHA256 = previous.ALIASES_SHA256
MODULES = ('photius_final_boundary_observations', 'photius_final_source_observations')
# Frozen after the complete authored source decisions pass fresh compilation.
SOURCE_WITNESS_SHA256 = '2ade1161a0a2a2b969e843ecf9a2b2a3e8258c21055fab527d77a1f57c2efa46'
sha, encode, canonical = previous.sha, previous.encode, previous.canonical
prior = previous.prior


def recipe_pins(root=ROOT):
    names = (Path(__file__).name, *(name+'.py' for name in MODULES))
    return {name:sha((Path(root)/'scripts'/name).read_bytes()) for name in names}


def input_pins(root=ROOT):
    root = Path(root)
    paths = [previous.AUDIT, previous.REVIEW, previous.RECORDS, previous.SOURCE_REVIEW,
             Path('data/corpus_changes/photius-bekker-readings/source-scan.pdf')]
    return {p.as_posix():sha((root/p).read_bytes()) for p in paths}


def scope(before, root=ROOT):
    """Translate every remaining identity to its literal released coordinates."""
    root = Path(root)
    if sha(before) != BASELINE_SHA256:
        raise ValueError('Final review requires the exact published continuation')
    rows = {r['locus']:r for r in map(json.loads,before.splitlines())}
    old = json.loads(gzip.decompress((root/previous.REVIEW).read_bytes()))
    grouped = defaultdict(list)
    for d in old['records']+old.get('extra_source_corrections',[]):
        grouped[d['locus']].append(d)
    result = {}
    for d in old['records']:
        if d['decision'] != 'retained':
            continue
        a,b = d['start'],d['end']
        delta = sum(len(v['corrected_text'])-(v['end']-v['start'])
                    for v in grouped[d['locus']] if v['end'] <= a)
        a,b = a+delta,b+delta
        row = rows[d['locus']]
        if row['text'][a:b] != d['original_text']:
            raise ValueError('A final identity lost its exact released preimage')
        result[(d['locus'],d['segment_index'])] = {
            'start':a,'end':b,'row':row,'record':deepcopy(d)}
    if len(result) != 27:
        raise ValueError('Final review must address the published 27 identities')
    return result


def _row_masks(row, root):
    for module in (previous, previous.previous):
        if row.get(module.TAG):
            record = module._checked_row_record(row,root)
            return deepcopy(record['excluded_spans'])
    return deepcopy(previous.previous._masks(row))


def witness_fingerprint(review):
    return sha(canonical({k:review[k] for k in ('source','records')}))


def _role_ranges(record):
    ranges = record.get('review_ranges',record['edits'])
    if not isinstance(ranges,list) or not ranges:
        raise ValueError('Final role ranges cannot be empty')
    edited_loci = {e['locus'] for e in record['edits']}
    if any(r['locus'] not in edited_loci for r in ranges):
        raise ValueError('Final role range has no corresponding edited row')
    if not record['lexical_eligible'] and any(not any(
            r['locus'] == e['locus'] and r['start'] <= e['start'] and e['end'] <= r['end']
            for r in ranges) for e in record['edits']):
        raise ValueError('Final role ranges must cover every nonlexical edit')
    return ranges


def _used_source_refs(root):
    """Do not count the same comparison token again in a later authority."""
    used = set()
    for module in (previous,previous.previous):
        path = Path(root)/module.REVIEW
        if not path.exists():
            continue
        old = json.loads(gzip.decompress(path.read_bytes()))
        for record in old['records']+old.get('extra_source_corrections',[]):
            if record.get('decision') == 'retained':
                continue
            for reading in record.get('readings',[]):
                if reading.get('role') == 'chosen':
                    used.update(sha(canonical(token['refs'])) for token in reading['tokens'])
    return used


def prepare(root=ROOT, *, source_html=None, reviewed_at):
    root = Path(root)
    pins,recipes = input_pins(root),recipe_pins(root)
    previous.previous.campaign._timestamp(reviewed_at)
    before = gzip.decompress((root/BEFORE).read_bytes()) if (root/BEFORE).exists() else (root/CORPUS).read_bytes()
    scope(before,root)
    raw = previous.previous._html_bytes(source_html)
    if sha(raw) != previous.preparer.SOURCE_SHA256:
        raise ValueError('Final review comparison source changed')
    rows = {r['locus']:r for r in map(json.loads,before.splitlines())}
    import fitz
    records = []
    with fitz.open(root/'data/corpus_changes/photius-bekker-readings/source-scan.pdf') as document:
        for name in MODULES:
            module = importlib.import_module(name)
            for record in module.review_final(raw,rows,document,previous.previous.campaign.crop_png,
                                              reviewed_at=reviewed_at):
                records.append({'authority':name,**record})
    if (input_pins(root) != pins or recipe_pins(root) != recipes
            or previous.previous._html_bytes(source_html) != raw):
        raise ValueError('Final review sources or recipes changed during preparation')
    return {'schema':SCHEMA,'work':'photius.bibliotheca','reviewed_at':reviewed_at,
            'input_corpus_sha256':sha(before),'source':{
                'id':'tlg-photius-henry','sha256':sha(raw),
                'edition':'Henry, Photius Bibliothèque, volumes 1–8 (1959–1977)',
                'citation':'Photius, Bibliotheca, TLG 4040.001'},
            'records':records,'input_pins':pins,'recipe_sha256':recipes}


def compile_review(before, authored, root=ROOT):
    """Validate authored decisions and freeze exact old exclusion leaves."""
    previous.previous._public(authored)
    if (authored.get('schema') != SCHEMA or authored.get('work') != 'photius.bibliotheca'
            or authored.get('input_corpus_sha256') != sha(before)):
        raise ValueError('Final review has an unknown predecessor or schema')
    previous.previous.campaign._timestamp(authored['reviewed_at'])
    if SOURCE_WITNESS_SHA256 is not None and witness_fingerprint(authored) != SOURCE_WITNESS_SHA256:
        raise ValueError('Final source witness fingerprint changed')
    if sha(before) == BASELINE_SHA256 and SOURCE_WITNESS_SHA256 is None:
        raise ValueError('Final source witness fingerprint is not frozen')
    scopes = scope(before,root)
    rows = {r['locus']:r for r in map(json.loads,before.splitlines())}
    seen, edits_by_row, records = set(), defaultdict(list), []
    used_source_refs = _used_source_refs(root)
    for value in authored['records']:
        record = deepcopy(value)
        authority = record.pop('authority')
        if authority not in MODULES:
            raise ValueError('Unknown final review authority')
        expected = importlib.import_module(authority).validate_record(record)
        if expected != record:
            raise ValueError('Final authored source decision changed')
        if record.get('reviewed_at') != authored['reviewed_at']:
            raise ValueError('Final review timestamp changed')
        for reading in record.get('readings',[]):
            if reading.get('role') != 'chosen':
                continue
            tokens = reading['tokens']
            indices = [t.get('source_index') for t in tokens]
            if (not tokens or reading.get('source_id') != authored['source']['id']
                    or any(type(i) is not int or i < 0 for i in indices)
                    or any(b != a+1 for a,b in zip(indices,indices[1:]))):
                raise ValueError('Final source tokens lack exact consecutive edition indices')
            for token in tokens:
                key = sha(canonical(token['refs']))
                if key in used_source_refs:
                    raise ValueError('Final review reuses an already adopted source token')
                used_source_refs.add(key)
        if not record.get('evidence') or not record.get('text_role') or type(record.get('lexical_eligible')) is not bool:
            raise ValueError('Final disposition lacks evidence or an explicit lexical role')
        _role_ranges(record)
        identities = record['identities']
        if not identities or not record.get('edits'):
            raise ValueError('Final disposition lacks identities or literal edits')
        for identity in identities:
            key = (identity['locus'],identity['segment_index'])
            if key not in scopes or key in seen:
                raise ValueError('Final review repeats or invents an identity')
            seen.add(key)
        for edit in record['edits']:
            row = rows[edit['locus']]
            a,b = edit['start'],edit['end']
            if (type(a) is not int or type(b) is not int or not 0 <= a <= b <= len(row['text'])
                    or row['text'][a:b] != edit['original_text']
                    or prior.row_sha(row) != edit['original_row_sha256']
                    or not isinstance(edit['corrected_text'],str)):
                raise ValueError('Final edit lost its exact released row or text')
            edits_by_row[edit['locus']].append(edit)
        for extent in record.get('review_ranges',[]):
            row = rows[extent['locus']]
            a,b = extent['start'],extent['end']
            if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(row['text'])
                    or row['text'][a:b] != extent['original_text']
                    or prior.row_sha(row) != extent['original_row_sha256']):
                raise ValueError('Final role review lost its exact source range')
        for identity in identities:
            target = scopes[(identity['locus'],identity['segment_index'])]
            owners = [e for e in record['edits'] if e['locus'] == identity['locus']
                      and e['start'] <= target['start'] and target['end'] <= e['end']]
            if not owners:
                raise ValueError('Final disposition does not cover its original identity')
            if (record['lexical_eligible'] and identity.get('text_role') in
                    {'marginal-reference','nonlexical-mark','modern-edition-reference','ocr-insertion','line-number'}
                    and any(previous.previous.edition.WORD.search(e['corrected_text']) for e in owners)):
                raise ValueError('A nonlexical group identity cannot supply a Greek replacement')
        records.append({'authority':authority,**record})
    if seen != set(scopes):
        raise ValueError('Final review must account for every held occurrence')
    for edits in edits_by_row.values():
        cursor = 0
        for edit in sorted(edits,key=lambda x:(x['start'],x['end'])):
            if edit['start'] < cursor:
                raise ValueError('Final edits overlap')
            cursor = edit['end']
    masks = {locus:_row_masks(rows[locus],root) for locus in edits_by_row}
    return {**deepcopy(authored),'records':records,'prior_exclusions':masks,
            'previous_current_uncertainty_spans':len(scopes),
            'identities':[{**dict(locus=k[0],segment_index=k[1]),
                           'start':v['start'],'end':v['end'],
                           'original_segment':deepcopy(v['record']['original_segment'])}
                          for k,v in scopes.items()]}


def _mapped(position, edits, *, end=False):
    """Rebase an untouched endpoint without inventing partial replacement text."""
    delta = 0
    for edit in sorted(edits,key=lambda e:e['start']):
        a,b = edit['start'],edit['end']
        if position >= b:
            delta += len(edit['corrected_text'])-(b-a)
        elif a < position < b:
            raise ValueError('An independent exclusion intersects an unreviewed replacement')
    return position+delta


def _identity_role(record, identity):
    return identity.get('text_role',record['text_role'])


def plan(before, review_raw):
    review = json.loads(review_raw)
    if review.get('schema') != SCHEMA or review.get('input_corpus_sha256') != sha(before):
        raise ValueError('Final authority differs from its exact preimage')
    grouped, decisions_by_row = defaultdict(list), defaultdict(list)
    targets = defaultdict(list)
    for identity in review['identities']:
        targets[identity['locus']].append(identity)
    for record in review['records']:
        _role_ranges(record)
        for edit in record['edits']:
            grouped[edit['locus']].append(edit)
            decisions_by_row[edit['locus']].append(record)
    changes, output = [], []
    for line in before.splitlines(keepends=True):
        old = json.loads(line);locus = old['locus']
        if locus not in grouped:
            output.append(line);continue
        if old.get(TAG):
            raise ValueError('Final review cannot apply twice')
        edits = sorted(grouped.pop(locus),key=lambda e:(e['start'],e['end']))
        records = list({sha(canonical(d)):d for d in decisions_by_row[locus]}.values())
        cursor, pieces = 0, []
        for edit in edits:
            a,b = edit['start'],edit['end']
            if (not cursor <= a <= b <= len(old['text']) or old['text'][a:b] != edit['original_text']
                    or prior.row_sha(old) != edit['original_row_sha256']):
                raise ValueError('Final replay lost a literal edit preimage')
            pieces.extend((old['text'][cursor:a],edit['corrected_text']));cursor = b
        pieces.append(old['text'][cursor:]);text = ''.join(pieces)
        retired, remaining = [], []
        for leaf in prior._flatten(old['text'],review['prior_exclusions'][locus]):
            matched = [v for v in targets[locus] if v['start'] < leaf['end'] and leaf['start'] < v['end']
                       and leaf.get('qualification') == v['original_segment'].get('uncertainty')]
            reviewed = [e for e in edits if e['start'] <= leaf['start'] and leaf['end'] <= e['end']]
            approved = any(r.get('lexical_eligible') and e in r['edits'] for e in reviewed for r in records)
            classes = {'source-confirmed-word-fragment','digital-reading-disagreement',
                       'digital-insertion-boundary','unpaired-available-digital-witness',
                       'unmapped-transcription-convention'}
            resolved_match = bool(matched) and all(any(r['disposition'] != 'held' and any(
                i['locus'] == locus and i['segment_index'] == v['segment_index']
                for i in r['identities']) for r in records) for v in matched)
            if leaf.get('classification') == 'unresolved-source-reading' and resolved_match:
                retired.append(leaf)
            elif approved and leaf.get('classification') in classes:
                retired.append(leaf)
            else:
                # A deletion can retire only a separately reviewed exact cause.
                a,b = leaf['start'],leaf['end']
                for edit in edits:
                    if edit['start'] < b and a < edit['end'] and edit['corrected_text'] != edit['original_text']:
                        if edit['start'] <= a and b <= edit['end']:
                            a,b = edit['start'],edit['end']
                            break
                        raise ValueError('Final edit would erase an independent exclusion cause')
                low,high = _mapped(a,edits),_mapped(b,edits,end=True)
                if low == high:
                    retired.append({**deepcopy(leaf),
                        'retirement_reason':'The independently reviewed source edit removed this entire display interval.'})
                else:
                    remaining.append({**deepcopy(leaf),'start':low,'end':high,'text':text[low:high]})
        for record in records:
            if not record['lexical_eligible']:
                ranges = _role_ranges(record)
                for edit in ranges:
                    if edit['locus'] != locus:
                        continue
                    start = _mapped(edit['start'],edits)
                    end = _mapped(edit['end'],edits,end=True)
                    if start == end:
                        continue
                    remaining.append({'start':start,'end':end,
                        'text':text[start:end],'classification':'source-reviewed-nonlexical-material',
                        'text_role':record['text_role'],'lexical_eligible':False,
                        'qualification':record['evidence'],'disposition':record['disposition']})
        exclusions,runs = prior._projection(text,remaining)
        new = deepcopy(old);new.update(text=text,analysis_text=' '.join(runs))
        new[TAG] = {'schema':SCHEMA,'reviewed_at':review['reviewed_at'],
            'source_review':{'path':REVIEW.as_posix(),'uncompressed_sha256':sha(review_raw)},
            'original_row_sha256':prior.row_sha(old),
            'excluded_spans':{'path':RECORDS.as_posix(),'locus':locus,'sha256':sha(canonical(exclusions))}}
        changes.append({'locus':locus,'original_line':line.decode(),'original_row':old,'corrected_row':new,
            'original_row_sha256':prior.row_sha(old),'corrected_row_sha256':prior.row_sha(new),
            'decisions':records,'edits':edits,'excluded_spans':exclusions,
            'retired_exclusion_causes':retired,'remaining_exclusion_causes':remaining,
            'reviewed_at':review['reviewed_at']})
        output.append(canonical(new)+b'\n')
    if grouped:
        raise ValueError('Final replay invents a corpus row')
    changed_rows = {c['locus']:c for c in changes}
    admitted_records = set()
    for record in review['records']:
        if not record['lexical_eligible'] or record['disposition'] == 'held':
            continue
        has_word, blocked = False, False
        for edit in record['edits']:
            matches = list(previous.previous.edition.WORD.finditer(edit['corrected_text']))
            if not matches:
                continue
            has_word = True
            change = changed_rows[edit['locus']]
            start = _mapped(edit['start'],change['edits'])
            for token in matches:
                low,high = start+token.start(),start+token.end()
                if any(mask['start'] < high and low < mask['end'] for mask in change['excluded_spans']):
                    blocked = True
        if has_word and not blocked:
            admitted_records.add(sha(canonical(record)))
    all_ids = [i for r in review['records'] for i in r['identities']]
    nonlexical = [i for r in review['records'] if r['disposition'] != 'held' for i in r['identities']
                  if _identity_role(r,i) in {'marginal-reference','nonlexical-mark',
                      'modern-edition-reference','ocr-insertion','line-number'}]
    nonlexical_keys = {(i['locus'],i['segment_index']) for i in nonlexical}
    editorial = [i for r in review['records'] if 'editorial-word-choice' in r['disposition']
                 for i in r['identities'] if (i['locus'],i['segment_index']) not in nonlexical_keys]
    held = [i for r in review['records'] if r['disposition'] == 'held' for i in r['identities']]
    held_keys = {(i['locus'],i['segment_index']) for i in held}
    resolved = [i for i in all_ids if (i['locus'],i['segment_index']) not in held_keys]
    lexical = [i for i in resolved if (i['locus'],i['segment_index']) not in nonlexical_keys]
    baseline = review['previous_current_uncertainty_spans']
    counts = {'rows':len(changes),'decisions':len(review['records']),'identities':len(all_ids),
        'previous_current_uncertainty_spans':baseline,'resolved_uncertainty_spans':len(resolved),
        'current_uncertainty_spans':len(held),'resolved_identities':resolved,
        'lexical_resolution_identities':lexical,'nonlexical_resolution_identities':nonlexical,
        'lexical_admitted_identities':[i for r in review['records'] if sha(canonical(r)) in admitted_records
                                       for i in r['identities'] if (i['locus'],i['segment_index']) not in nonlexical_keys],
        'newly_editorially_substituted_spans':len(editorial),'editorially_substituted_spans':2950+len(editorial),
        'new_scan_backed_dispositions':sum(len(r['identities']) for r in review['records']
                                         if r['disposition'] == 'correct-scan-reading'),
        'editorial_omissions':sum(len(r['identities']) for r in review['records']
                                 if r['disposition'] == 'editorial-word-choice-omission'),
        'scan_uncertainty_spans':2977,'nonlexically_classified_spans':len(nonlexical),
        'resolved_by_text_role':dict(Counter(_identity_role(r,i) for r in review['records'] if r['disposition'] != 'held'
                                           for i in r['identities'])),
        'dispositions':dict(Counter(r['disposition'] for r in review['records'] for i in r['identities'])),
        'changed_display_rows':sum(c['original_row']['text'] != c['corrected_row']['text'] for c in changes),
        'primary_rows_before':len(before.splitlines()),'primary_rows_after':len(output)}
    if (type(baseline) is not int or len(all_ids) != baseline
            or len({(i['locus'],i['segment_index']) for i in all_ids}) != baseline):
        raise ValueError('Final replay repeats or drops a held occurrence')
    return b''.join(output),changes,counts


def artifacts(before, aliases, review_raw, authored_raw):
    after,changes,counts = plan(before,review_raw)
    files = {BEFORE:compress_gzip(before),BEFORE_ALIASES:compress_gzip(aliases),
             REVIEW:compress_gzip(review_raw),SOURCE_REVIEW:authored_raw,
             RECORDS:compress_gzip(b''.join(canonical(c)+b'\n' for c in changes))}
    review = json.loads(review_raw)
    audit = {'schema':SCHEMA,'work':'photius.bibliotheca','reviewed_at':review['reviewed_at'],
        'input_corpus_sha256':sha(before),'output_corpus_sha256':sha(after),'aliases_sha256':sha(aliases),
        'source':review['source'],'input_pins':review['input_pins'],'recipe_sha256':review['recipe_sha256'],
        'counts':counts,'source_review':{'path':REVIEW.as_posix(),'sha256':sha(files[REVIEW]),
                                      'uncompressed_sha256':sha(review_raw)},
        'outputs':{p.as_posix():sha(raw) for p,raw in files.items()}}
    audit['outputs'][CORPUS.as_posix()] = sha(after)
    return {CORPUS:after,**files,AUDIT:encode(audit)},audit


def build(root=ROOT, *, source_html=None, reviewed_at=None):
    root = Path(root)
    if reviewed_at is None:
        reviewed_at = json.loads((root/SOURCE_REVIEW).read_bytes())['reviewed_at']
    authored = prepare(root,source_html=source_html,reviewed_at=reviewed_at)
    before = gzip.decompress((root/BEFORE).read_bytes()) if (root/BEFORE).exists() else (root/CORPUS).read_bytes()
    aliases = (root/ALIASES).read_bytes()
    if sha(aliases) != ALIASES_SHA256:
        raise ValueError('Final review aliases changed')
    review = compile_review(before,authored,root)
    return artifacts(before,aliases,encode(review),encode(authored))


@lru_cache(maxsize=1)
def _literal_saved(audit_raw,before_raw,aliases_raw,review_gzip,records_gzip,authored_raw):
    audit = json.loads(audit_raw)
    for path,raw in ((BEFORE,before_raw),(BEFORE_ALIASES,aliases_raw),(REVIEW,review_gzip),
                     (RECORDS,records_gzip),(SOURCE_REVIEW,authored_raw)):
        if sha(raw) != audit['outputs'][path.as_posix()]:
            raise ValueError('Frozen final review artifact changed')
    before,aliases,review_raw = gzip.decompress(before_raw),gzip.decompress(aliases_raw),gzip.decompress(review_gzip)
    review = json.loads(review_raw)
    after,changes,counts = plan(before,review_raw)
    if (audit['schema'] != SCHEMA or sha(before) != audit['input_corpus_sha256']
            or sha(after) != audit['output_corpus_sha256'] or sha(aliases) != audit['aliases_sha256']
            or counts != audit['counts'] or [json.loads(l) for l in gzip.decompress(records_gzip).splitlines()] != changes
            or audit['outputs'][CORPUS.as_posix()] != sha(after)
            or audit['source'] != review['source'] or audit['reviewed_at'] != review['reviewed_at']
            or audit['input_pins'] != review['input_pins'] or audit['recipe_sha256'] != review['recipe_sha256']
            or audit['source_review'] != {'path':REVIEW.as_posix(),'sha256':sha(review_gzip),'uncompressed_sha256':sha(review_raw)}):
        raise ValueError('Final review archive does not reproduce exact replay')
    return before,after,aliases,audit


def _saved(root):
    return _literal_saved(*((Path(root)/p).read_bytes() for p in
                          (AUDIT,BEFORE,BEFORE_ALIASES,REVIEW,RECORDS,SOURCE_REVIEW)))


def restore_before_bytes(raw,root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        if b'"'+TAG.encode()+b'"' in raw:
            raise ValueError('Final review metadata has no authority')
        return raw
    before,after,_,_ = _saved(root)
    if raw not in {before,after}:
        raise ValueError('Final review corpus differs from its exact postimage')
    return before


@lru_cache(maxsize=1)
def _record_map(raw):
    records = [json.loads(l) for l in gzip.decompress(raw).splitlines()]
    result = {r['locus']:r for r in records}
    if len(records) != len(result):
        raise ValueError('Final review repeats a corpus row')
    return result


@lru_cache(maxsize=1)
def _review_digest(raw):
    return sha(gzip.decompress(raw))


def _checked_row_record(row,root):
    root = Path(root);audit = json.loads((root/AUDIT).read_bytes())
    raw = (root/RECORDS).read_bytes();review = (root/REVIEW).read_bytes()
    if sha(raw) != audit['outputs'][RECORDS.as_posix()] or sha(review) != audit['source_review']['sha256']:
        raise ValueError('Final review row or compiled authority changed')
    record = _record_map(raw).get(row.get('locus'))
    if (not record or row != record['corrected_row'] or prior.row_sha(row) != record['corrected_row_sha256']
            or audit.get('schema') != SCHEMA or row[TAG].get('schema') != SCHEMA
            or audit.get('source_review') != {'path':REVIEW.as_posix(),'sha256':sha(review),
                                             'uncompressed_sha256':_review_digest(review)}
            or row[TAG].get('source_review') != {'path':REVIEW.as_posix(),
                                               'uncompressed_sha256':_review_digest(review)}
            or row[TAG].get('reviewed_at') != audit.get('reviewed_at')
            or prior.row_sha(record['original_row']) != record['original_row_sha256']
            or json.loads(record['original_line']) != record['original_row']
            or row[TAG]['excluded_spans'] != {'path':RECORDS.as_posix(),'locus':row['locus'],
                                             'sha256':sha(canonical(record['excluded_spans']))}):
        raise ValueError('Final review row differs from its exact attributed postimage')
    return record


def restore_before_row(row,root=ROOT):
    return deepcopy(_checked_row_record(row,root)['original_row']) if row.get(TAG) else deepcopy(row)


def lexical_segments(row,root=ROOT):
    record = _checked_row_record(row,root)
    _,runs = prior._projection(row['text'],prior._flatten(row['text'],record['excluded_spans']))
    if row.get('analysis_text') != ' '.join(runs):
        raise ValueError('Final review lexical projection changed')
    return runs


def active_metadata(root=ROOT):
    root = Path(root);raw = (root/CORPUS).read_bytes()
    if not (root/AUDIT).exists():
        restore_before_bytes(raw,root);return None
    before,after,aliases,audit = _saved(root)
    if raw not in {before,after} or (root/ALIASES).read_bytes() != aliases:
        raise ValueError('Final review corpus or aliases changed outside its admission')
    if raw == before:
        return None
    return {'audit':{'path':AUDIT.as_posix(),'sha256':sha((root/AUDIT).read_bytes())},
        'source_review':deepcopy(audit['source_review']),'source':deepcopy(audit['source']),
        'counts':deepcopy(audit['counts']),
        'qualification':'Joint editorial word choices and nonlexical classifications are distinct from historical scan verification.'}


def check_literal(root=ROOT):
    root = Path(root);metadata = active_metadata(root)
    if not (root/AUDIT).exists():
        return metadata
    before,_,_,audit = _saved(root)
    authored_raw = (root/SOURCE_REVIEW).read_bytes();authored = json.loads(authored_raw)
    if (audit['recipe_sha256'] != recipe_pins(root) or audit['input_pins'] != input_pins(root)
            or authored['recipe_sha256'] != audit['recipe_sha256']
            or authored['input_pins'] != audit['input_pins']):
        raise ValueError('Final source inputs or recipes changed')
    review = compile_review(before,authored,root)
    if compress_gzip(encode(review)) != (root/REVIEW).read_bytes():
        raise ValueError('Final source decisions no longer compile literally')
    return metadata


def check(root=ROOT, *, source_html=None):
    files,audit = build(root,source_html=source_html)
    metadata = active_metadata(root)
    if any((Path(root)/p).read_bytes() != raw for p,raw in files.items() if p != CORPUS):
        raise ValueError('Final review does not reproduce from its live sources')
    return audit if metadata else None


def apply(root=ROOT, *, source_html=None, reviewed_at=None):
    root = Path(root);files,audit = build(root,source_html=source_html,reviewed_at=reviewed_at)
    if sha((root/CORPUS).read_bytes()) not in {audit['input_corpus_sha256'],audit['output_corpus_sha256']}:
        raise ValueError('Final application needs its exact predecessor')
    if any((root/p).exists() and (root/p).read_bytes() != raw for p,raw in files.items() if p != CORPUS):
        raise ValueError('Refusing to replace an immutable final review archive')
    for p,raw in files.items():
        if p != CORPUS:
            (root/p).parent.mkdir(parents=True,exist_ok=True);(root/p).write_bytes(raw)
    (root/CORPUS).write_bytes(files[CORPUS]);return audit


def undo(root=ROOT):
    before,_,_,_ = _saved(root);active_metadata(root);(Path(root)/CORPUS).write_bytes(before)


def main():
    parser = argparse.ArgumentParser(description=__doc__);mode = parser.add_mutually_exclusive_group()
    for name in ('apply','undo','check','check-literal'):
        mode.add_argument('--'+name,action='store_true')
    parser.add_argument('--source-html',type=Path);parser.add_argument('--reviewed-at')
    args = parser.parse_args()
    if args.undo:
        undo();return
    result = (apply(source_html=args.source_html,reviewed_at=args.reviewed_at) if args.apply
              else check_literal() if args.check_literal else check(source_html=args.source_html) if args.check
              else build(source_html=args.source_html,reviewed_at=args.reviewed_at)[1])
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
