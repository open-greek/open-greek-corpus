#!/usr/bin/env python3
"""Admit the later Photius editorial review with exact replay and reversal."""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from copy import deepcopy
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re

from audit_compression import compress_gzip
import prepare_photius_editorial_continuation as preparer
import repair_photius_editorial_substitutions as previous

ROOT=previous.ROOT
CORPUS,ALIASES=previous.CORPUS,previous.ALIASES
ARCHIVE=preparer.ARCHIVE
SOURCE_REVIEW=preparer.OUTPUT
REVIEW=ARCHIVE/'compiled-review.json.gz'
AUDIT=ARCHIVE/'changes.json'
BEFORE=preparer.BEFORE
BEFORE_ALIASES=ARCHIVE/'before-aliases.json.gz'
RECORDS=ARCHIVE/'records.jsonl.gz'
TAG='photius_editorial_continuation'
SCHEMA='photius-editorial-continuation-admission-v1'
BASELINE_SHA256=preparer.BASELINE_SHA256
ALIASES_SHA256=previous.ALIASES_SHA256
# Freeze only after the complete source-backed campaign has passed compilation.
# Recipe pins make this authority independent of the editable audit payload.
SOURCE_WITNESS_SHA256='e5e8317be0ed09e0c6587311856182fc5de233bf5a74fd252eed33dd7db08d97'
sha,encode=previous.sha,previous.encode
canonical=previous.campaign.canonical
prior=previous.prior


def witness_fingerprint(authored):
    return sha(canonical({key:authored.get(key,[]) for key in
        ('source','records','extra_source_corrections')}))


def input_pins(root):
    pins={p.as_posix():sha((Path(root)/p).read_bytes()) for p in
            (previous.AUDIT,previous.REVIEW,previous.RECORDS,previous.SOURCE_REVIEW,previous.COMPILED)}
    if (Path(root)/'scripts/photius_remaining_roles.py').exists():
        import photius_remaining_roles
        for p,expected in photius_remaining_roles.SOURCE_PINS.items():
            value=sha((Path(root)/p).read_bytes())
            if value!=expected:raise ValueError('A role-review source pin changed')
            pins[p]=value
    if (Path(root)/'scripts/photius_remaining_words.py').exists():
        import photius_remaining_words
        for p,expected in photius_remaining_words.SOURCE_PINS.items():
            value=sha((Path(root)/p).read_bytes())
            if value!=expected:raise ValueError('A complete-word source pin changed')
            pins[p]=value
    for module in preparer.manual_modules(root):
        for p,expected in module.SOURCE_PINS.items():
            value=sha((Path(root)/p).read_bytes())
            if value!=expected:raise ValueError('An individual review source pin changed')
            pins[p]=value
    return pins


def _source_index(authored,raw):
    if raw is not None:return previous._source_tokens(raw,authored['source'])
    recorded={**authored,'records':authored['records']+authored.get('extra_source_corrections',[])}
    values=previous._recorded_tokens(recorded)
    for key,(_,token) in list(values.items()):
        index=token.get('source_index')
        if type(index) is not int or index<0:
            raise ValueError('Recorded source tokens need their complete-edition index')
        values[key]=(index,token)
    if len({v[0] for v in values.values()})!=len(values):
        raise ValueError('Recorded source indices collide')
    return values


def _reading(value,target,source,known,units):
    witness=deepcopy(value);witness.pop('trim',None);witness.pop('applied_text',None)
    previous._reading(witness,source,known,{
        'record':target['record'],'row':target['row'],'start':target['start'],'end':target['end']})
    for token in value['tokens']:
        if token.get('source_index')!=known[sha(canonical(token['refs']))][0]:
            raise ValueError('A continuation source-token index changed')
    if units is not None:
        expected=preparer.attributed_span(value,units)
        if any(value.get(k)!=expected[k] for k in ('surface','separators','boundary_suffix')):
            raise ValueError('Source punctuation does not reproduce its decoded HTML witnesses')
    else:
        separators=value.get('separators')
        if not isinstance(separators,list) or len(separators)!=len(value['tokens'])-1:
            raise ValueError('Recorded source punctuation has incomplete boundaries')
        parts=[]
        for i,token in enumerate(value['tokens']):
            if i:
                left=value['tokens'][i-1]['refs'][-1];right=token['refs'][0]
                parts.append(_punctuation(separators[i-1],left,right))
            parts.append(token['text'])
        parts.append(_punctuation(value.get('boundary_suffix',{}),value['tokens'][-1]['refs'][-1]))
        if value.get('surface')!=previous._nfc(''.join(parts)):
            raise ValueError('Recorded source surface does not reproduce its witness pieces')
    return value


def _punctuation(witness,left,right=None):
    """Validate recorded nonlexical nodes bounded by exact Greek source refs."""
    raw='';positions=[]
    low=(left['html_line'],left['html_column'],left['end'])
    high=None if right is None else (right['html_line'],right['html_column'],right['start'])
    for piece in witness.get('pieces',[]):
        text,ref=piece['text'],piece['ref']
        if (set(ref)!={'html_line','html_column','node_index','start','end','codex','bekker'}
            or any(type(ref[k]) is not int for k in ('html_line','html_column','node_index','start','end'))
            or ref['start']<0 or ref['end']<=ref['start'] or ref['end']-ref['start']!=len(text)
            or previous.edition.WORD.search(text) or any(c.isalnum() for c in text)):
            raise ValueError('Recorded punctuation includes unsupported text or malformed source references')
        start=(ref['html_line'],ref['html_column'],ref['start']);end=(*start[:2],ref['end'])
        if start<low or high is not None and end>high or positions and start<positions[-1]:
            raise ValueError('Recorded punctuation no longer lies between its exact source tokens')
        positions.append(end);raw+=text
    rendered=(preparer.normalized_separator(raw,left,right) if right is not None
              else re.sub(r'\s+',' ',raw))
    if witness.get('rendered')!=rendered:raise ValueError('Recorded punctuation normalization changed')
    return rendered


def compile_review(before,scopes,authored,*,source_raw=None):
    previous._public(authored)
    if authored.get('schema')!=preparer.SCHEMA or authored.get('input_corpus_sha256')!=sha(before):
        raise ValueError('Continuation decisions have an unknown exact predecessor')
    previous.campaign._timestamp(authored['reviewed_at'])
    if sha(before)==preparer.BASELINE_SHA256:
        if SOURCE_WITNESS_SHA256 is None:
            if source_raw is None:
                raise ValueError('The complete source witness fingerprint is not frozen')
        elif witness_fingerprint(authored)!=SOURCE_WITNESS_SHA256:
            raise ValueError('The complete source witness fingerprint changed')
    known=_source_index(authored,source_raw)
    manual_modules={module.__name__:module for module in preparer.manual_modules()}
    units=preparer.source_document(source_raw) if source_raw is not None else None
    roles={}
    if any(d.get('role_review') for d in authored['records']):
        import photius_remaining_roles
        if source_raw is not None:roles=photius_remaining_roles.review_roles(source_raw,scopes)
        else:
            for d in authored['records']:
                if d.get('role_review'):
                    key=previous.pilot._key(d)
                    roles[key]=photius_remaining_roles.validate_record(key,d['role_review'])
    seen=set();records=[];used={}
    for raw in authored['records']:
        item=deepcopy(raw);key=previous.pilot._key(item)
        if key in seen or key not in scopes:raise ValueError('Continuation repeats or invents a held identity')
        seen.add(key);target=scopes[key];row=target['row'];a,b=target['start'],target['end']
        segment=target['record']['original_segment']
        if (item['original_text']!=row['text'][a:b] or item['decision'] not in {'substitute','retained'}
                or not isinstance(item.get('evidence'),str) or not item['evidence'].strip()):
            raise ValueError('Continuation lost an exact original or decision evidence')
        word_review=item.get('word_review')
        if word_review:
            import photius_remaining_words
            expected_word=photius_remaining_words.validate_record(key,word_review)
            if expected_word!=word_review:raise ValueError('Complete-word review changed')
        manual=item.get('manual_review')
        manual_review=None
        if 'manual_review' in item:
            if (not isinstance(manual,dict) or set(manual)!={'module','review'}
                    or manual.get('module') not in manual_modules):
                raise ValueError('An individual review has an unknown source authority')
            manual_review=manual_modules[manual['module']].validate_record(key,manual['review'])
            if manual_review['original_text']!=item['original_text']:
                raise ValueError('An individual review changed its exact original')
        readings=item.get('readings',[])
        if item['decision']=='substitute':
            if segment.get('fragments'):raise ValueError('Fragments need a jointly sourced boundary review')
            role_review=item.get('role_review')
            if segment['text_role']!='authorial-body':
                if (not role_review or roles.get(key)!=role_review
                        or role_review['role'] not in {'authorial-body','transmitted-historical-commentary'}
                        or role_review['original_role']!=segment['text_role']):
                    raise ValueError('Nonbody material needs an exact independent eligible role review')
            if len(readings)!=1 or readings[0].get('role')!='chosen':
                raise ValueError('Continuation needs one uniquely located chosen reading')
            reading=_reading(readings[0],target,authored['source'],known,units)
            if role_review:
                expected=role_review['readings']
                observed=[{'text':t['text'],'refs':t['refs']} for t in reading['tokens']]
                if len(expected)!=1 or observed!=expected[0]['tokens']:
                    raise ValueError('An adopted role reading differs from its independently reviewed source interval')
            if word_review:
                observed=[{'text':t['text'],'refs':t['refs']} for t in reading['tokens']]
                if len(word_review['readings'])!=1 or observed!=word_review['readings'][0]['tokens']:
                    raise ValueError('Complete-word adoption differs from its independently reviewed source interval')
            if manual_review:
                observed=[{'text':t['text'],'refs':t['refs']} for t in reading['tokens']]
                expected_tokens=(manual_review['readings'][0]['tokens'] if len(manual_review['readings'])==1 else [])
                if observed!=[{'text':t['text'],'refs':t['refs']} for t in expected_tokens]:
                    raise ValueError('Individual adoption differs from its reviewed source interval')
                indices=manual_review.get('source_indices',
                    [t.get('source_index') for t in expected_tokens])
                if (not isinstance(indices,list) or len(indices)!=len(expected_tokens)
                        or any(type(index) is not int or index<0 for index in indices)
                        or indices!=[t['source_index'] for t in reading['tokens']]):
                    raise ValueError('Individual source-token indices changed')
                surface={k:reading[k] for k in ('surface','separators','boundary_suffix')}
                if (not isinstance(manual_review.get('surface_sha256'),str)
                        or not re.fullmatch('[0-9a-f]{64}',manual_review['surface_sha256'])
                        or sha(canonical(surface))!=manual_review['surface_sha256']):
                    raise ValueError('Individual source punctuation or surface changed')
            rendered=preparer.render(item['original_text'],row['text'],a,b,reading,
                rendering=word_review.get('rendering') if word_review else role_review.get('rendering') if role_review
                          else manual_review.get('rendering') if manual_review else None)
            if rendered is None or any(item.get(k)!=v for k,v in rendered.items()):
                raise ValueError('Continuation display is not the attributed full-span rendering')
            trim=item['trim'];low=a-len(trim['prefix']);high=b+len(trim['suffix'])
            if any(other_key!=key and other['row']['locus']==row['locus']
                    and (other['start']<a and low<other['end'] or other['start']<high and b<other['end'])
                    for other_key,other in scopes.items()):
                raise ValueError('Continuation borrows another uncertain word fragment')
            for token in reading['tokens']:
                token_key=sha(canonical(token['refs']))
                if token_key in used:raise ValueError('Continuation reuses a source token for two held identities')
                if token_key in target.get('previously_used_source_refs',set()):
                    raise ValueError('Continuation reuses an already admitted source reading')
                used[token_key]=key
        elif item['corrected_text']!=item['original_text']:
            raise ValueError('A retained decision silently changes the display')
        records.append({**item,'start':a,'end':b,'original_row_sha256':prior.row_sha(row),
            'original_segment':deepcopy(segment),'physical_page':target['record']['physical_page'],
            'printed_page':target['record']['printed_page'],
            **({'identity_preimage':deepcopy(target['identity_preimage'])} if target.get('identity_preimage') else {})})
    if seen!=set(scopes):raise ValueError('Continuation must account for every held identity')
    extras=[];extra_ids=set()
    for extra in authored.get('extra_source_corrections',[]):
        import photius_remaining_roles
        source_review=photius_remaining_roles.validate_correction_record(extra['source_review'])
        if source_review['id'] in extra_ids:raise ValueError('A separately reviewed source correction repeats')
        extra_ids.add(source_review['id'])
        target=next((t for t in scopes.values() if t['row']['locus']==source_review['locus']),None)
        if target is None:raise ValueError('A fresh source correction invents a passage')
        row=target['row'];a,b=source_review['start'],source_review['end']
        if (prior.row_sha(row)!=source_review['original_row_sha256'] or row['text'][a:b]!=source_review['original_text']
                or any(t['row']['locus']==row['locus'] and t['start']<b and a<t['end'] for t in scopes.values())):
            raise ValueError('A fresh source correction lost its exact independently reviewed preimage')
        if len(extra['readings'])!=1:raise ValueError('A fresh correction needs one chosen source clause')
        reading=extra['readings'][0]
        observed=[{'text':t['text'],'refs':t['refs']} for t in reading['tokens']]
        if observed!=source_review['readings'][0]['tokens']:
            raise ValueError('A fresh correction no longer selects its exact corroborating source clause')
        for token in reading['tokens']:
            token_key=sha(canonical(token['refs']))
            if token_key in used or token_key in target.get('previously_used_source_refs',set()):
                raise ValueError('A fresh correction reuses another admitted source token')
            used[token_key]=('source-correction',source_review['id'])
        extra_target={**target,'start':a,'end':b}
        _reading(reading,extra_target,authored['source'],known,units)
        rendered=preparer.render(source_review['original_text'],row['text'],a,b,reading)
        if rendered is None or any(extra.get(k)!=v for k,v in rendered.items()) or rendered['corrected_text']!=source_review['corrected_text']:
            raise ValueError('A fresh correction no longer reproduces its exact reviewed display')
        anchor=next((d['role_review'] for d in records if d['locus']==row['locus'] and d.get('role_review')
            and d['role_review']['role']=='transmitted-historical-commentary'),None)
        if not anchor:raise ValueError('A fresh commentary correction needs its separately reviewed paragraph role')
        extras.append({**deepcopy(extra),'id':source_review['id'],'locus':row['locus'],'start':a,'end':b,
            'original_text':source_review['original_text'],'corrected_text':source_review['corrected_text'],
            'decision':'source-correction','original_row_sha256':prior.row_sha(row),
            'original_segment':{'verification':'verified','text_role':anchor['original_role']},
            'role_review':{'role':anchor['role'],'original_role':anchor['original_role'],
                'basis':'Same independently reviewed transmitted explanatory paragraph.'}})
    masks={t['row']['locus']:deepcopy(t['excluded_spans']) for t in scopes.values()}
    return {'schema':SCHEMA,'work':'photius.bibliotheca','input_corpus_sha256':sha(before),
        'source':deepcopy(authored['source']),'reviewed_at':authored['reviewed_at'],
        'records':records,'extra_source_corrections':extras,
        'prior_exclusions':masks,'previous_current_uncertainty_spans':len(scopes)}


def plan(before,review_raw):
    review=json.loads(review_raw)
    if review.get('schema')!=SCHEMA or review.get('input_corpus_sha256')!=sha(before):
        raise ValueError('Continuation authority does not identify its exact predecessor')
    grouped=defaultdict(list);keys=[]
    for d in review['records']:grouped[d['locus']].append(d);keys.append(previous.pilot._key(d))
    for d in review.get('extra_source_corrections',[]):grouped[d['locus']].append(d)
    if len(set(keys))!=len(keys) or len(keys)!=review['previous_current_uncertainty_spans']:
        raise ValueError('Continuation repeats or omits a predecessor occurrence')
    output=[];changes=[]
    for line in before.splitlines(keepends=True):
        old=json.loads(line);locus=old['locus']
        if locus not in grouped:output.append(line);continue
        if old.get(TAG):raise ValueError('Continuation cannot apply twice')
        decisions=sorted(grouped.pop(locus),key=lambda d:d['start'])
        exclusions=review['prior_exclusions'][locus]
        reference=old[previous.TAG]['excluded_spans']
        if reference!={'path':previous.RECORDS.as_posix(),'locus':locus,'sha256':sha(canonical(exclusions))}:
            raise ValueError('Continuation changed the predecessor exclusion authority')
        leaves=prior._flatten(old['text'],exclusions);remaining=[];retired=[];retired_roles=[]
        for leaf in leaves:
            associated=[d for d in decisions if d['start']<leaf['end'] and leaf['start']<d['end']]
            belongs=any(leaf.get('qualification')==d['original_segment'].get('uncertainty') for d in associated)
            if (leaf.get('classification')=='unresolved-source-reading' and belongs and associated
                    and all(d['decision']=='substitute' for d in associated)):
                retired.append(leaf)
            elif leaf.get('text_role') and leaf.get('qualification')=='Source review does not admit this material as authorial lexical evidence.':
                approved=[d for d in associated if d['decision'] in {'substitute','source-correction'}
                    and d.get('role_review',{}).get('role') in {'authorial-body','transmitted-historical-commentary'}
                    and d['role_review']['original_role']==leaf['text_role']]
                intervals=sorted((max(leaf['start'],d['start']),min(leaf['end'],d['end'])) for d in approved)
                if not intervals:remaining.append(leaf);continue
                cursor=leaf['start'];pieces=[]
                for low,high in intervals:
                    if cursor<low:pieces.append((cursor,low))
                    cursor=max(cursor,high)
                if cursor<leaf['end']:pieces.append((cursor,leaf['end']))
                for low,high in pieces:
                    remaining.append({**deepcopy(leaf),'start':low,'end':high,'text':old['text'][low:high],
                        'role_review_remainder':'Only the separately reviewed occurrence interval was reclassified.'})
                retired_roles.append({'original_exclusion':deepcopy(leaf),'reviewed_intervals':[list(i) for i in intervals]})
            else:remaining.append(leaf)
        cursor=0;pieces=[]
        for d in decisions:
            a,b=d['start'],d['end']
            if (type(a) is not int or type(b) is not int or not cursor<=a<b<=len(old['text'])
                    or old['text'][a:b]!=d['original_text'] or prior.row_sha(old)!=d['original_row_sha256']
                    or d['decision'] not in {'substitute','retained','source-correction'}
                    or d['decision']=='retained' and d['corrected_text']!=d['original_text']):
                raise ValueError('Continuation decision does not reproduce its exact preimage')
            if d['decision']!='source-correction' and not any(leaf.get('classification')=='unresolved-source-reading'
                and leaf['start']<=a<b<=leaf['end'] and leaf.get('qualification')==d['original_segment'].get('uncertainty') for leaf in leaves):
                raise ValueError('Continuation has no inherited uncertainty cause')
            pieces.extend((old['text'][cursor:a],d['corrected_text']));cursor=b
        pieces.append(old['text'][cursor:]);text=''.join(pieces)
        remaining=[prior._rebase(leaf,decisions,text) for leaf in remaining]
        exclusions,runs=prior._projection(text,remaining)
        new=deepcopy(old);new.update(text=text,analysis_text=' '.join(runs))
        new[TAG]={'schema':SCHEMA,'reviewed_at':review['reviewed_at'],
            'source_review':{'path':REVIEW.as_posix(),'uncompressed_sha256':sha(review_raw)},
            'original_row_sha256':prior.row_sha(old),'editorial_source':deepcopy(review['source']),
            'excluded_spans':{'path':RECORDS.as_posix(),'locus':locus,'sha256':sha(canonical(exclusions))},
            'substituted':sum(d['decision']=='substitute' for d in decisions)}
        changes.append({'locus':locus,'original_line':line.decode(),'original_row':old,'corrected_row':new,
            'original_row_sha256':prior.row_sha(old),'corrected_row_sha256':prior.row_sha(new),
            'decisions':decisions,'excluded_spans':exclusions,'retired_uncertainty_causes':retired,
            'retired_role_causes':retired_roles,'remaining_exclusion_causes':remaining,'reviewed_at':review['reviewed_at']})
        output.append(canonical(new)+b'\n')
    if grouped:raise ValueError('Continuation invents a corpus passage')
    substituted=[{'locus':d['locus'],'segment_index':d['segment_index']} for d in review['records'] if d['decision']=='substitute']
    n=len(substituted);baseline=review['previous_current_uncertainty_spans']
    counts={'rows':len(changes),'decisions':len(keys),'previous_current_uncertainty_spans':baseline,
        'newly_editorially_substituted_spans':n,'editorially_substituted_spans':2592+n,
        'scan_uncertainty_spans':2977,'current_uncertainty_spans':baseline-n,
        'unsubstituted_source_uncertainty_spans':baseline-n,'substituted_identities':substituted,
        'changed_display_rows':sum(c['original_row']['text']!=c['corrected_row']['text'] for c in changes),
        'changed_spans':sum(d['decision']=='substitute' and d['original_text']!=d['corrected_text'] for d in review['records']),
        'source_reviewed_role_spans':sum(d['decision']=='substitute' and bool(d.get('role_review')) for d in review['records']),
        'fresh_source_corrections':len(review.get('extra_source_corrections',[])),
        'remaining_by_reason':dict(Counter(d['reason'] for d in review['records'] if d['decision']=='retained')),
        'primary_rows_before':len(before.splitlines()),'primary_rows_after':len(output)}
    return b''.join(output),changes,counts


def artifacts(before,aliases,review_raw,*,pins,recipes):
    after,changes,counts=plan(before,review_raw)
    files={BEFORE:compress_gzip(before),BEFORE_ALIASES:compress_gzip(aliases),REVIEW:compress_gzip(review_raw),
        RECORDS:compress_gzip(b''.join(canonical(c)+b'\n' for c in changes))}
    review=json.loads(review_raw)
    audit={'schema':SCHEMA,'work':'photius.bibliotheca','reviewed_at':review['reviewed_at'],
        'input_corpus_sha256':sha(before),'output_corpus_sha256':sha(after),'aliases_sha256':sha(aliases),
        'source':review['source'],'input_pins':pins,'recipe_sha256':recipes,'counts':counts,
        'source_review':{'path':REVIEW.as_posix(),'sha256':sha(files[REVIEW]),'uncompressed_sha256':sha(review_raw)},
        'outputs':{p.as_posix():sha(raw) for p,raw in files.items()}}
    audit['outputs'][CORPUS.as_posix()]=sha(after)
    return {CORPUS:after,**files,AUDIT:encode(audit)},audit


def build(root=ROOT,*,source_html=None):
    root=Path(root);raw=previous._html_bytes(source_html)
    authored_raw=(root/SOURCE_REVIEW).read_bytes();authored=json.loads(authored_raw)
    before,scopes=preparer.scope(root)
    aliases=(root/ALIASES).read_bytes()
    if sha(aliases)!=ALIASES_SHA256:raise ValueError('Continuation aliases changed')
    if preparer.prepare(raw,root,reviewed_at=authored['reviewed_at'])!=authored:
        raise ValueError('Continuation decisions do not reproduce from their source and code')
    pins=input_pins(root);pins[SOURCE_REVIEW.as_posix()]=sha(authored_raw)
    if authored['input_pins']!={k:v for k,v in pins.items() if k!=SOURCE_REVIEW.as_posix()}:
        raise ValueError('Continuation preparation inputs differ from the current exact source pins')
    recipes={**authored['recipe_sha256'],Path(__file__).name:sha((root/'scripts'/Path(__file__).name).read_bytes())}
    review=compile_review(before,scopes,authored,source_raw=raw)
    if any(d.get('role_review') for d in authored['records']):
        import fitz
        import photius_remaining_roles
        with fitz.open(root/'data/corpus_changes/photius-bekker-readings/source-scan.pdf') as document:
            photius_remaining_roles.validate_scan(document,previous.campaign.crop_png)
            if (root/'scripts/photius_remaining_words.py').exists():
                import photius_remaining_words
                photius_remaining_words.validate_scan(document,previous.campaign.crop_png)
            for module in preparer.manual_modules(root):
                if hasattr(module,'validate_scan'):
                    module.validate_scan(document,previous.campaign.crop_png)
    files,audit=artifacts(before,aliases,encode(review),pins=pins,recipes=recipes)
    if (input_pins(root)!={k:v for k,v in pins.items() if k!=SOURCE_REVIEW.as_posix()}
        or (root/SOURCE_REVIEW).read_bytes()!=authored_raw or (root/ALIASES).read_bytes()!=aliases
        or previous._html_bytes(source_html)!=raw
        or any(sha((root/'scripts'/n).read_bytes())!=v for n,v in recipes.items())):
        raise ValueError('Continuation inputs changed during validation')
    return files,audit


@lru_cache(maxsize=1)
def _literal_saved(audit_raw,before_raw,aliases_raw,review_gzip,records_gzip):
    audit=json.loads(audit_raw)
    for p,raw in ((BEFORE,before_raw),(BEFORE_ALIASES,aliases_raw),(REVIEW,review_gzip),(RECORDS,records_gzip)):
        if sha(raw)!=audit['outputs'][p.as_posix()]:raise ValueError('Frozen continuation artifact changed')
    before,aliases,review_raw=gzip.decompress(before_raw),gzip.decompress(aliases_raw),gzip.decompress(review_gzip)
    after,changes,counts=plan(before,review_raw)
    if (audit['schema']!=SCHEMA or sha(before)!=audit['input_corpus_sha256']
        or sha(after)!=audit['output_corpus_sha256'] or sha(aliases)!=audit['aliases_sha256']
        or audit['outputs'].get(CORPUS.as_posix())!=sha(after)
        or audit.get('source_review')!={'path':REVIEW.as_posix(),'sha256':sha(review_gzip),'uncompressed_sha256':sha(review_raw)}
        or audit.get('source')!=json.loads(review_raw).get('source')
        or audit.get('reviewed_at')!=json.loads(review_raw).get('reviewed_at')
        or counts!=audit['counts'] or [json.loads(l) for l in gzip.decompress(records_gzip).splitlines()]!=changes):
        raise ValueError('Continuation archive does not reproduce its exact replay')
    return before,after,aliases,audit


def _saved(root):
    return _literal_saved(*((Path(root)/p).read_bytes() for p in (AUDIT,BEFORE,BEFORE_ALIASES,REVIEW,RECORDS)))


def restore_before_bytes(raw,root=ROOT):
    root=Path(root)
    if not (root/AUDIT).exists():
        if b'"'+TAG.encode()+b'"' in raw:raise ValueError('Continuation metadata has no authority')
        return raw
    before,after,_,_=_saved(root)
    if raw not in {before,after}:raise ValueError('Continuation corpus differs from its exact postimage')
    return before


@lru_cache(maxsize=2)
def _record_map(raw):
    values=[json.loads(l) for l in gzip.decompress(raw).splitlines()]
    result={v['locus']:v for v in values}
    if len(values)!=len(result):raise ValueError('Continuation row authority repeats a passage')
    return result


def _checked_row_record(row,root):
    root=Path(root);audit=json.loads((root/AUDIT).read_bytes());raw=(root/RECORDS).read_bytes()
    review=(root/REVIEW).read_bytes()
    if (sha(raw)!=audit['outputs'][RECORDS.as_posix()] or sha(review)!=audit['source_review']['sha256']):
        raise ValueError('Continuation row or compiled authority changed')
    record=_record_map(raw).get(row.get('locus'))
    if (not record or row!=record['corrected_row'] or prior.row_sha(row)!=record['corrected_row_sha256']
        or prior.row_sha(record['original_row'])!=record['original_row_sha256']
        or json.loads(record['original_line'])!=record['original_row']
        or audit.get('schema')!=SCHEMA or row[TAG].get('schema')!=SCHEMA
        or row[TAG].get('source_review')!={'path':REVIEW.as_posix(),'uncompressed_sha256':audit['source_review']['uncompressed_sha256']}
        or row[TAG]['excluded_spans']!={'path':RECORDS.as_posix(),'locus':row['locus'],'sha256':sha(canonical(record['excluded_spans']))}):
        raise ValueError('Continuation row differs from its exact attributed postimage')
    return record


def restore_before_row(row,root=ROOT):
    return deepcopy(_checked_row_record(row,root)['original_row']) if row.get(TAG) else deepcopy(row)


def lexical_segments(row,root=ROOT):
    record=_checked_row_record(row,root)
    _,runs=prior._projection(row['text'],prior._flatten(row['text'],record['excluded_spans']))
    if row.get('analysis_text')!=' '.join(runs):raise ValueError('Continuation lexical projection changed')
    return runs


def active_metadata(root=ROOT):
    root=Path(root);current=(root/CORPUS).read_bytes()
    if not (root/AUDIT).exists():
        restore_before_bytes(current,root);return None
    before,after,aliases,audit=_saved(root)
    if current not in {before,after} or (root/ALIASES).read_bytes()!=aliases:
        raise ValueError('Continuation corpus or aliases changed outside its admission')
    if current==before:return None
    return {'audit':{'path':AUDIT.as_posix(),'sha256':sha((root/AUDIT).read_bytes())},
        'source_review':deepcopy(audit['source_review']),'source':deepcopy(audit['source']),
        'counts':deepcopy(audit['counts']),
        'qualification':'Editorial preferences remain distinct from the immutable scan-review measurements.'}


def check_literal(root=ROOT):
    root=Path(root)
    metadata=active_metadata(root)
    if not (root/AUDIT).exists():return metadata
    before,_,_,audit=_saved(root)
    if sha(before)!=BASELINE_SHA256:raise ValueError('Continuation predecessor changed')
    pins=input_pins(root);pins[SOURCE_REVIEW.as_posix()]=sha((root/SOURCE_REVIEW).read_bytes())
    if pins!=audit['input_pins']:raise ValueError('Continuation public source inputs changed')
    for name,digest in audit['recipe_sha256'].items():
        if sha((root/'scripts'/name).read_bytes())!=digest:raise ValueError('Continuation source recipe changed')
    authored=json.loads((root/SOURCE_REVIEW).read_bytes());_,scopes=preparer.scope(root)
    expected_recipes={n:sha((root/'scripts'/n).read_bytes()) for n in preparer.recipe_names(root)+[Path(__file__).name]}
    if (audit['recipe_sha256']!=expected_recipes
            or authored['recipe_sha256']!={k:v for k,v in expected_recipes.items() if k!=Path(__file__).name}
            or authored['input_pins']!={k:v for k,v in pins.items() if k!=SOURCE_REVIEW.as_posix()}):
        raise ValueError('Continuation recipe or preparation pin accounting changed')
    review=compile_review(before,scopes,authored)
    if compress_gzip(encode(review))!=(root/REVIEW).read_bytes():
        raise ValueError('Recorded continuation witnesses do not reproduce their authority')
    return metadata


def check(root=ROOT,*,source_html=None):
    files,audit=build(root,source_html=source_html);metadata=active_metadata(root)
    if any((Path(root)/p).read_bytes()!=raw for p,raw in files.items() if p!=CORPUS):
        raise ValueError('Continuation does not reproduce from its supplied comparison source')
    return audit if metadata else None


def apply(root=ROOT,*,source_html=None):
    root=Path(root);files,audit=build(root,source_html=source_html)
    if sha((root/CORPUS).read_bytes()) not in {audit['input_corpus_sha256'],audit['output_corpus_sha256']}:
        raise ValueError('Continuation application needs its exact predecessor')
    if any((root/p).exists() and (root/p).read_bytes()!=raw for p,raw in files.items() if p!=CORPUS):
        raise ValueError('Refusing to replace an immutable continuation archive')
    for p,raw in files.items():
        if p!=CORPUS:(root/p).parent.mkdir(parents=True,exist_ok=True);(root/p).write_bytes(raw)
    (root/CORPUS).write_bytes(files[CORPUS]);return audit


def undo(root=ROOT):
    root=Path(root);before,_,_,_=_saved(root)
    active_metadata(root);(root/CORPUS).write_bytes(before)


def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group()
    for name in ('apply','undo','check','check-literal'):mode.add_argument('--'+name,action='store_true')
    parser.add_argument('--source-html',type=Path);args=parser.parse_args()
    if args.undo:undo();return
    result=(apply(source_html=args.source_html) if args.apply else check_literal() if args.check_literal
            else check(source_html=args.source_html) if args.check else build(source_html=args.source_html)[1])
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
