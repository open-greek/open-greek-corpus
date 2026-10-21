#!/usr/bin/env python3
"""Prepare a later review of the 385 held Photius editorial occurrences.

The previous selection and all original alternatives remain immutable. This
review renders complete attributed Greek spans, including their internal
punctuation, instead of treating an uncertain transcription's punctuation as
an inviolable word boundary.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import importlib
import json
from pathlib import Path
import re
import unicodedata

import repair_photius_editorial_substitutions as previous

ROOT = previous.ROOT
CORPUS = previous.CORPUS
ARCHIVE = Path('data/corpus_changes/photius-bekker-editorial-continuation')
OUTPUT = ARCHIVE/'source-review.json'
BEFORE = ARCHIVE/'before-corpus.jsonl.gz'
SCHEMA = 'photius-editorial-continuation-review-v1'
BASELINE_SHA256 = 'ca9b4f853cf048a798b614e6d6ecd4a6650bf2a2c6d1536dd080d5bb3f604348'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
MANUAL_MODULES = tuple('photius_remaining_manual_'+letter for letter in 'abcd')


def manual_modules(root=ROOT):
    return [importlib.import_module(name) for name in MANUAL_MODULES
            if (Path(root)/'scripts'/(name+'.py')).exists()]


def scope(root=ROOT):
    """Translate the frozen held identities through the first editorial layer."""
    root = Path(root)
    before = gzip.decompress((root/BEFORE).read_bytes()) if (root/BEFORE).exists() else (root/CORPUS).read_bytes()
    if previous.sha(before) != BASELINE_SHA256:
        raise ValueError('Continuation requires the exact preceding published corpus')
    rows = {r['locus']:r for r in map(json.loads, before.splitlines())}
    review = json.loads(gzip.decompress((root/previous.REVIEW).read_bytes()))
    archived = {r['locus']:r for r in map(json.loads,
        gzip.decompress((root/previous.RECORDS).read_bytes()).splitlines())}
    grouped = defaultdict(list)
    for decision in review['records']:
        grouped[decision['locus']].append(decision)
    used={previous.sha(previous.campaign.canonical(t['refs'])) for d in review['records']
          if d['decision']=='substitute' for r in d['readings'] if r['role']=='chosen' for t in r['tokens']}
    result = {}
    for record in review['records']:
        if record['decision']=='substitute':
            continue
        a,b = record['start'],record['end']
        delta = sum(len(d['corrected_text'])-(d['end']-d['start'])
                    for d in grouped[record['locus']] if d['end']<=a)
        a,b = a+delta,b+delta
        row = rows[record['locus']]
        if row['text'][a:b] != record['original_text']:
            raise ValueError('A held source identity lost its exact current preimage')
        result[(record['locus'],record['segment_index'])] = {
            'row':row,'start':a,'end':b,'record':record,
            'excluded_spans':deepcopy(archived[record['locus']]['excluded_spans']),
            'previously_used_source_refs':used}
    complete=json.loads(gzip.decompress((root/previous.COMPILED).read_bytes()))
    positions={r['locus']:i for i,r in enumerate(complete['rows'])}
    contexts={}
    for target in result.values():
        locus=target['row']['locus']
        if locus not in contexts:
            i=positions[locus];neighbors=[]
            for record in complete['rows'][max(0,i-1):i+2]:
                row=rows[record['locus']]
                if not record.get('digital_counterparts_usable',True):continue
                masks=(archived[row['locus']]['excluded_spans'] if row.get(previous.TAG)
                       else previous._masks(row))
                neighbors.append({'row':row,'excluded_spans':deepcopy(masks),
                    'physical_page':record['physical_page'],'printed_page':record['printed_page']})
            contexts[locus]=neighbors
        target['context_rows']=contexts[locus]
    if len(result)!=385:
        raise ValueError('Continuation scope differs from its published 385 identities')
    if (root/'scripts/photius_remaining_words.py').exists():
        import photius_remaining_words
        result=photius_remaining_words.adjust_scopes(result)
    return before,result


class SourceUnits(list):
    """Original Greek unit identities plus every intervening body data node."""
    def __init__(self,units,nodes,node_for_unit):
        super().__init__(units);self.nodes=nodes;self.node_for_unit=node_for_unit


class PunctuationHTML(previous.edition.EditionHTML):
    def __init__(self):
        super().__init__();self.nodes=[];self.node_for_unit={};self.body_cell=False

    def handle_starttag(self,tag,attrs):
        if tag=='td':self.body_cell=dict(attrs).get('class')!='Y'
        elif tag in {'tr','th','h1','h2','h3','h4','h5','h6'}:self.body_cell=False
        super().handle_starttag(tag,attrs)

    def handle_data(self,data):
        if self.body_cell and not self.header and not self.ignore and self.bekker:
            if previous.edition.WORD.search(data):self.node_for_unit[len(self.units)]=len(self.nodes)
            self.nodes.append({'text':data,'html_line':self.getpos()[0],
                'html_column':self.getpos()[1],'node_index':len(self.nodes),
                'codex':self.codex,'bekker':self.bekker})
        super().handle_data(data)


def source_document(raw):
    parser = PunctuationHTML()
    parser.feed(raw.decode('utf-8-sig'))
    return SourceUnits(parser.units,parser.nodes,parser.node_for_unit)


def _slice_ref(unit,start,end):
    return {**{k:v for k,v in unit.items() if k!='text'},'start':start,'end':end}


def normalized_separator(raw,left,right):
    """Retain a word boundary when HTML cells omit their layout whitespace."""
    rendered=re.sub(r'\s+',' ',raw)
    if left['unit_index']!=right['unit_index']:
        if not rendered:rendered=' '
        elif rendered[-1] in '.;·:!?':rendered+=' '
    return rendered


def separator_witness(left,right,units):
    """Record every decoded character between consecutive Greek source tokens."""
    a,b = left['refs'][-1],right['refs'][0]
    if (a['unit_index'],a['end']) > (b['unit_index'],b['start']):
        raise ValueError('Source tokens overlap or cross')
    pieces=[]
    first,last=units.node_for_unit[a['unit_index']],units.node_for_unit[b['unit_index']]
    for i in range(first,last+1):
        unit=units.nodes[i]
        low=a['end'] if i==first else 0
        high=b['start'] if i==last else len(unit['text'])
        if low<high:
            text=unit['text'][low:high]
            if previous.edition.WORD.search(text) or any(c.isalnum() for c in text):
                raise ValueError('A punctuation witness contains omitted lexical or numeric material')
            pieces.append({'text':text,'ref':_slice_ref(unit,low,high)})
    raw=''.join(p['text'] for p in pieces)
    return {'pieces':pieces,'rendered':normalized_separator(raw,a,b)}


def boundary_suffix(core,last,units):
    """Carry an immediately following source closer for an internal opener.

    A pure-punctuation HTML node can carry a closing bracket or quotation mark;
    the earlier Greek-only parser intentionally did not retain such nodes.
    """
    pairs={'(':')','[':']','«':'»'};stack=[]
    for char in core:
        if char in pairs:stack.append(pairs[char])
        elif stack and char==stack[-1]:stack.pop()
    if not stack:return {'pieces':[],'rendered':''}
    pieces=[];pending=[];finished=False
    first=units.node_for_unit[last['unit_index']]
    for i in range(first,len(units.nodes)):
        node=units.nodes[i];low=last['end'] if i==first else 0
        for j,char in enumerate(node['text'][low:],low):
            if char.isspace():pending.append((node,j,char));continue
            if char!=stack[-1]:finished=True;break
            pending.append((node,j,char));pieces.extend(pending);pending=[];stack.pop()
            if not stack:finished=True;break
        if finished:break
    grouped=[]
    for node,j,char in pieces:
        if grouped and grouped[-1]['ref']['node_index']==node['node_index'] and grouped[-1]['ref']['end']==j:
            grouped[-1]['text']+=char;grouped[-1]['ref']['end']+=1
        else:grouped.append({'text':char,'ref':_slice_ref(node,j,j+1)})
    return {'pieces':grouped,'rendered':re.sub(r'\s+',' ',''.join(p['text'] for p in grouped))}


def attributed_span(reading,units):
    reading=deepcopy(reading)
    tokens=reading['tokens']
    if not tokens:
        raise ValueError('An empty comparison span needs an explicit omission decision')
    separators=[separator_witness(a,b,units) for a,b in zip(tokens,tokens[1:])]
    pieces=[]
    for i,token in enumerate(tokens):
        if i:pieces.append(separators[i-1]['rendered'])
        pieces.append(token['text'])
    core=''.join(pieces);suffix=boundary_suffix(core,tokens[-1]['refs'][-1],units)
    reading.update(surface=unicodedata.normalize('NFC',core+suffix['rendered']),
                   separators=separators,boundary_suffix=suffix)
    return reading


def render(original,current,start,end,reading,*,rendering=None):
    """Replace a full uncertain core while retaining external literal wrappers.

    Variant display brackets and abbreviation parentheses belong to the old
    uncertain reading. They are archived, not attached to the chosen full word.
    """
    rendering=rendering or {}
    words=list(previous.edition.WORD.finditer(original))
    if not words:
        if rendering.get('allow_non_greek_original') and original.isdecimal():
            return {'corrected_text':reading['surface'],'display_prefix':'','display_suffix':'',
                'trim':{'prefix':'','suffix':''},'retired_display_conventions':['source-reviewed-opaque-ocr-token'],
                'external_boundary_suffix':False}
        return None
    value=reading['surface'];prefix=suffix=''
    boundary=reading.get('boundary_suffix',{}).get('rendered','')
    external_boundary=bool(boundary.strip() and current[end:].lstrip().startswith(boundary.strip()))
    if external_boundary:value=value[:-len(boundary)]
    for word in previous.edition.WORD.finditer(current):
        if word.start()<start<word.end():prefix=current[word.start():start]
        if word.start()<end<word.end():suffix=current[end:word.end()]
    separate=rendering.get('separate_verified_suffix')
    if separate is not None:
        if suffix!=separate or rendering.get('boundary_after')!=' ':
            return None
        suffix=''
    prefix,suffix=map(lambda s:unicodedata.normalize('NFC',s),(prefix,suffix))
    if (prefix and not value.startswith(prefix) or suffix and not value.endswith(suffix)
            or len(prefix)+len(suffix)>=len(value)):
        return None
    trimmed=value[len(prefix):len(value)-len(suffix) if suffix else None]
    outer_left,outer_right=original[:words[0].start()],original[words[-1].end():]
    retired=[]
    for side,key in [('left','retire_prefix'),('right','retire_suffix')]:
        value_to_retire=rendering.get(key)
        if value_to_retire:
            if side=='left':
                if not outer_left.startswith(value_to_retire):return None
                outer_left=outer_left[len(value_to_retire):]
            else:
                if not outer_right.endswith(value_to_retire):return None
                outer_right=outer_right[:-len(value_to_retire)]
            retired.append('source-reviewed-nonlexical-wrapper')
    if '⟦' in outer_left and '∥' in original and '⟧' in outer_right:
        retired.append('uncertain-variant-display');outer_left=outer_left.replace('⟦','');outer_right=outer_right.replace('⟧','')
    for opening,closing in [('(',')'),('[',']')]:
        if closing in outer_right and opening in original[words[0].start():words[-1].end()]:
            retired.append('uncertain-abbreviation-wrapper');outer_right=outer_right.replace(closing,'',1)
    if outer_right and outer_right[0] in previous.edition.assess.APOSTROPHES:
        outer_right=outer_right[1:]
    elif outer_right and outer_right[0]==trimmed[-1] and not previous.edition.WORD.fullmatch(outer_right[0]):
        outer_right=outer_right[1:]
    return {'corrected_text':outer_left+trimmed+outer_right+rendering.get('boundary_after',''),
            'display_prefix':outer_left,'display_suffix':outer_right,
            'trim':{'prefix':prefix,'suffix':suffix},'retired_display_conventions':retired,
            'external_boundary_suffix':external_boundary}


def prepare(html_raw,root=ROOT,*,reviewed_at):
    root=Path(root);previous.campaign._timestamp(reviewed_at)
    if previous.sha(html_raw)!=SOURCE_SHA256:
        raise ValueError('Continuation comparison source changed')
    before,scopes=scope(root);units=source_document(html_raw)
    previous_doc=json.loads((root/previous.SOURCE_REVIEW).read_bytes())
    source=deepcopy(previous_doc['source'])
    suggestions={}
    helper=root/'scripts/photius_remaining_context.py'
    if helper.exists():
        import photius_remaining_context
        suggestions=photius_remaining_context.locate_remaining(html_raw,scopes)
    role_reviews={}
    if (root/'scripts/photius_remaining_roles.py').exists():
        import photius_remaining_roles
        role_reviews=photius_remaining_roles.review_roles(html_raw,scopes)
    word_reviews={}
    if (root/'scripts/photius_remaining_words.py').exists():
        import photius_remaining_words
        word_reviews=photius_remaining_words.review_words(html_raw,scopes)
    manual_reviews={}
    for module in manual_modules(root):
        for key,review in module.review_remaining(html_raw,scopes).items():
            if key in manual_reviews:
                raise ValueError('Two individual reviews repeat a held occurrence')
            manual_reviews[key]={'module':module.__name__,'review':review}
    records=[]
    for key,target in scopes.items():
        prior=target['record'];old=target['row']['text'][target['start']:target['end']]
        item={'locus':key[0],'segment_index':key[1],'original_text':old,'corrected_text':old,
              'decision':'retained','reason':'no-located-reading','readings':[],
              'evidence':'No uniquely bounded nonempty comparison reading is established.'}
        segment=prior['original_segment']
        role_review=role_reviews.get(key)
        word_review=word_reviews.get(key)
        manual=manual_reviews.get(key)
        if manual:item['manual_review']=deepcopy(manual)
        if word_review:item['word_review']=deepcopy(word_review)
        role_eligible=role_review and role_review['role'] in {'authorial-body','transmitted-historical-commentary'}
        if role_review:item['role_review']=deepcopy(role_review)
        if segment['text_role']!='authorial-body' and not role_eligible:
            item.update(reason='marginal-reference' if role_review and role_review['role']=='marginal-reference' else 'role-review',
                evidence=role_review['evidence'] if role_review else 'The previous heading, small-type, or marginal role needs an independent source review.')
        elif segment.get('fragments'):
            item.update(reason='split-word',evidence='The word crosses a retained passage boundary; preserve its fragment exclusion until a joint group is verified.')
        else:
            options=(deepcopy(word_review['readings']) if word_review else deepcopy(role_review['readings']) if role_eligible else
                deepcopy(prior['readings']) if prior['decision']=='retained-unmapped' and len(prior['readings'])==1 else [])
            method='the preceding uniquely located contextual candidate'
            if role_eligible:method='the independently reviewed source heading or explanatory paragraph'
            if word_review:method='the independently reviewed complete-word source occurrence'
            suggestion=suggestions.get(key)
            if suggestion:
                item['location_evidence']=deepcopy(suggestion.get('evidence',{}))
            blocked=bool(suggestion and suggestion.get('evidence',{}).get('block_prior_fallback'))
            located=bool(suggestion and suggestion.get('evidence',{}).get('status')=='located')
            if suggestion and not role_eligible and not word_review and (located or blocked):
                options=deepcopy(suggestion['readings']);method=suggestion['method']
                if blocked:
                    item.update(reason='blocked-location',evidence=str(suggestion.get('evidence')))
            if manual and not role_eligible and not word_review:
                options=deepcopy(manual['review']['readings'])
                method='the individually reviewed sentence position in its pinned source context'
                item.update(reason='individually-held-reading',evidence=manual['review']['evidence'])
            if len(options)==1:
                try:
                    reading=attributed_span(options[0],units)
                    result=render(old,target['row']['text'],target['start'],target['end'],reading,
                        rendering=word_review.get('rendering') if word_review else role_review.get('rendering') if role_eligible
                                  else manual['review'].get('rendering') if manual else None)
                except ValueError as exc:
                    result=None;item['evidence']=str(exc)
                if result:
                    reading.update(role='chosen',trim=result['trim'])
                    item.update(result,decision='substitute',reason='located-editorial-reading',readings=[reading],
                        evidence='Adopt the Greek span and its internal punctuation from '+method+'; this is an editorial preference, not scan certification.')
                else:item.update(reason='unrendered-reading',readings=options)
            elif len(options)>1:
                item.update(reason='tied-reading',readings=options,evidence='All supported source intervals remain alternatives.')
            elif not manual and prior['decision']=='retained-tied':
                item.update(reason='tied-reading',readings=deepcopy(prior['readings']))
            elif not manual and 'empty source gap' in prior['evidence']:
                item.update(reason='empty-gap',evidence=prior['evidence'])
        records.append(item)
    known=previous._source_tokens(html_raw,source)
    extras=[]
    if role_reviews:
        for review in photius_remaining_roles.review_corrections(html_raw,scopes):
            target=next(t for t in scopes.values() if t['row']['locus']==review['locus'])
            reading=attributed_span(review['readings'][0],units);reading['role']='chosen'
            rendered=render(review['original_text'],target['row']['text'],review['start'],review['end'],reading)
            if not rendered or rendered['corrected_text']!=review['corrected_text']:
                raise ValueError('A separately reviewed correction does not reproduce its exact source clause')
            extras.append({'source_review':deepcopy(review),'readings':[reading],**rendered})
    for item in records+extras:
        for reading in item['readings']:
            for token in reading['tokens']:
                index,actual=known[previous.sha(previous.campaign.canonical(token['refs']))]
                if previous._nfc(token['text'])!=previous._nfc(actual['text']):
                    raise ValueError('A proposed Greek reading differs from its fresh source token')
                token['source_index']=index
    inputs=(previous.AUDIT,previous.REVIEW,previous.RECORDS,previous.SOURCE_REVIEW,previous.COMPILED)
    extra_pins={}
    if role_reviews:extra_pins=photius_remaining_roles.SOURCE_PINS
    if word_reviews:extra_pins={**extra_pins,**photius_remaining_words.SOURCE_PINS}
    for module in manual_modules(root):extra_pins.update(module.SOURCE_PINS)
    return {'schema':SCHEMA,'reviewed_at':reviewed_at,'input_corpus_sha256':previous.sha(before),
            'source':source,'records':records,'extra_source_corrections':extras,
            'counts':dict(Counter(r['reason'] for r in records)),
            'input_pins':{**{p.as_posix():previous.sha((root/p).read_bytes()) for p in inputs},**extra_pins},
            'recipe_sha256':{n:previous.sha((root/'scripts'/n).read_bytes()) for n in recipe_names(root)}}


def recipe_names(root=ROOT):
    names={*previous.RECIPE_NAMES,Path(__file__).name}
    names.update(n for n in ('photius_remaining_context.py','photius_remaining_roles.py','photius_remaining_words.py') if (Path(root)/'scripts'/n).exists())
    names.update(module.__name__+'.py' for module in manual_modules(root))
    return sorted(names)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-html',type=Path,required=True)
    parser.add_argument('--reviewed-at',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/OUTPUT)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    raw=previous.encode(prepare(args.source_html.read_bytes(),reviewed_at=args.reviewed_at))
    if args.check:
        if args.output.read_bytes()!=raw:raise ValueError('Continuation decisions do not reproduce')
    else:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(raw)


if __name__=='__main__':main()
