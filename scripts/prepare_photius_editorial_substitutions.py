#!/usr/bin/env python3
"""Choose Greek readings from a supplied edition for unresolved Photius spans.

This is an editorial preference, not certification of the Bekker scan. Locations
come from verified surrounding words; an uncertain spelling never selects its
own counterpart. The source HTML stays outside the repository. Chosen Greek
readings and precise source references make every substitution reproducible.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

import compare_photius_local_edition as local
import repair_photius_context as context
import repair_photius_uncertainties as prior

ROOT = Path(__file__).resolve().parents[1]
COMPLETE = local.COMPLETE
PRIOR = local.PRIOR
SCAN_REVIEW = Path('data/corpus_changes/photius-bekker-uncertainty-admission/source-review.json')
CORPUS = Path('data/corpus/photius.bibliotheca.jsonl')
OUTPUT = Path('data/corpus_changes/photius-bekker-editorial-substitutions/source-review.json')
BEFORE = OUTPUT.parent/'before-corpus.jsonl.gz'
SCHEMA = 'photius-editorial-substitution-review-v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def nfc(text):
    return unicodedata.normalize('NFC', text)


def shifted(start, end, decisions):
    """Translate an unchanged interval through exact earlier substitutions."""
    for d in decisions:
        if d['start'] < end and start < d['end']:
            raise ValueError('An unresolved segment overlaps an earlier source resolution')
    delta = sum(len(d['corrected_text']) - (d['end']-d['start'])
                for d in decisions if d['end'] <= start)
    return start+delta, end+delta


def render_reading(original, current, start, end, reading):
    """Trim verified word affixes and preserve exact nonlexical wrappers."""
    words = list(local.WORD.finditer(original))
    if not words:
        return None
    core_start, core_end = words[0].start(), words[-1].end()
    if any(original[a.end():b.start()].strip() for a,b in zip(words,words[1:])):
        return None
    prefix = suffix = ''
    for word in local.WORD.finditer(current):
        if word.start() < start < word.end():
            prefix = current[word.start():start]
        if word.start() < end < word.end():
            suffix = current[end:word.end()]
    value = nfc(reading)
    prefix, suffix = nfc(prefix), nfc(suffix)
    if (prefix and not value.startswith(prefix) or suffix and not value.endswith(suffix)
            or len(prefix)+len(suffix) >= len(value)):
        return None
    trimmed = value[len(prefix):len(value)-len(suffix) if suffix else None]
    if not trimmed.strip() or not local.WORD.search(trimmed):
        return None
    before, after = original[:core_start], original[core_end:]
    # Elision belongs to the adopted Greek form. An older abbreviation mark
    # must not turn a newly expanded source word into a fictitious elision.
    if after and after[0] in local.assess.APOSTROPHES:
        after = after[1:]
    elif after and after[0]==trimmed[-1] and not local.WORD.fullmatch(after[0]):
        after = after[1:]
    return {'corrected_text': before+trimmed+after,
            'trim': {'prefix': prefix, 'suffix': suffix},
            'display_prefix': before, 'display_suffix': after,
            'applied_text': trimmed}


def candidate_tokens(matcher, page, candidate):
    tokens,_ = matcher.page_index(page)
    location = candidate['location']
    return deepcopy(tokens[location['token_start']:location['token_end']])


def ordered_fallback(tokens, neutral, reliable, digital):
    """Use all optimal whole-row paths when immediate flanks are interrupted."""
    aligned = context._context_alignment([t['key'] for t in tokens],
        [t['key'] for t in digital], neutral)
    anchors = [i for i in reliable if len(aligned['counterparts'][i]) == 1
        and not aligned['may_be_unaligned'][i]
        and tokens[i]['key'] == digital[aligned['counterparts'][i][0]]['key']]
    if (not aligned['aligned'] or len(anchors) < max(5, 0.7*len(reliable))
            or aligned['cost'] > 0.35*len(tokens)*context.GAP_COST):
        return None
    return aligned


def prepare(html_raw, root=ROOT, *, reviewed_at):
    root = Path(root)
    context._timestamp(reviewed_at)
    paths = (COMPLETE, PRIOR, SCAN_REVIEW, CORPUS)
    raw = {p: (root/p).read_bytes() for p in paths}
    if (root/BEFORE).exists():
        raw[CORPUS] = gzip.decompress((root/BEFORE).read_bytes())
    complete = json.loads(gzip.decompress(raw[COMPLETE]))
    previous, scanned = json.loads(raw[PRIOR]), json.loads(raw[SCAN_REVIEW])
    current = {r['locus']:r for r in map(json.loads,raw[CORPUS].splitlines())}
    resolved = {(d['locus'],d['segment_index']) for review in (previous,scanned)
                for d in review['records'] if d['decision']=='resolved'}
    parser = local.EditionHTML(); parser.feed(html_raw.decode('utf-8-sig'))
    edition_tokens = local.tokenize(parser.units)
    for token in edition_tokens:
        ref = token['refs'][-1]
        unit = parser.units[ref['unit_index']]['text']
        if ref['end'] < len(unit) and unit[ref['end']] in local.assess.APOSTROPHES:
            token['text'] += unit[ref['end']]
            ref['end'] += 1
    matcher = local.Matcher(edition_tokens)
    records = []
    for row in complete['rows']:
        locus = row['locus']; text = current[locus]['text']
        earlier = [[d for d in review['records'] if d['locus']==locus and d['decision']=='resolved']
                   for review in (previous,scanned)]
        pending = []
        for i,s in enumerate(row['segments']):
            if s['verification'] != 'uncertain' or (locus,i) in resolved:
                continue
            a,b = s['corrected_start'],s['corrected_end']
            for decisions in earlier:
                a,b = shifted(a,b,decisions)
            if text[a:b] != s['corrected_text']:
                raise ValueError('Current unresolved span differs from its exact original')
            pending.append((i,s,a,b))
        if not pending:
            continue
        tokens = [{**{'start':m.start(),'end':m.end(),'text':m.group()},
                   'key':local.normalize(m.group())} for m in local.WORD.finditer(text)]
        neutral = {j for j,t in enumerate(tokens)
                   if any(a<t['end'] and t['start']<b for _,s,a,b in pending)}
        for tag in ('photius_uncertainty_admission','photius_uncertainty_review','photius_context_review'):
            if tag in current[locus]:
                leaves = prior._flatten(text,current[locus][tag]['excluded_spans'])
                boundaries = [s for s in leaves
                    if s.get('classification')=='source-confirmed-word-fragment'
                    or s.get('text_role','authorial-body')!='authorial-body']
                neutral.update(j for j,t in enumerate(tokens) if any(
                    s['start']<t['end'] and t['start']<s['end'] for s in boundaries))
                break
        reliable = set(range(len(tokens)))-neutral
        page = int(row['printed_page']); digital,_ = matcher.page_index(page)
        aligned = None; fallback_done = False
        for i,segment,a,b in pending:
            item = {'locus':locus,'segment_index':i,'original_text':text[a:b],
                'corrected_text':text[a:b],'decision':'retained-unmapped','readings':[],
                'evidence':'No unambiguous nonempty reading at this occurrence.'}
            if segment['text_role'] != 'authorial-body':
                item.update(decision='retained-nonbody',evidence='Nonbody material keeps its independent exclusion.')
                records.append(item); continue
            if segment.get('fragments'):
                item['evidence']='This source word crosses a retained passage boundary; a whole comparison word cannot replace each fragment independently.'
                records.append(item); continue
            left,right = local.verified_flanks(tokens,reliable,a,b)
            result = matcher.match(page,left,right,min_side=3)
            if result['match_status']=='unmatched':
                result = matcher.match(page,left,right,min_side=2)
            options = [candidate_tokens(matcher,page,c) for c in result['candidates']]
            method = 'consecutive verified words around the uncertain span'
            if not options:
                if not fallback_done:
                    aligned = ordered_fallback(tokens,neutral,reliable,digital)
                    fallback_done = True
                target = [j for j,t in enumerate(tokens) if a<t['end'] and t['start']<b]
                if aligned and target and all(len(aligned['counterparts'][j])==1
                        and not aligned['may_be_unaligned'][j] for j in target):
                    indexes = [aligned['counterparts'][j][0] for j in target]
                    if indexes==list(range(indexes[0],indexes[-1]+1)) and not any(
                            indexes[0]<=j<=indexes[-1] for j in aligned['digital_only']):
                        options = [deepcopy(digital[indexes[0]:indexes[-1]+1])]
                        method = 'unique token counterparts across every optimal whole-passage alignment; at least five exact verified anchors'
            for option in options:
                if not option:
                    item['evidence']='The surrounding context selects an empty source gap; this does not authorize deleting the retained Greek text.'
                    continue
                value = ' '.join(t['text'] for t in option)
                item['readings'].append({'text':value,'source_id':'tlg-photius-henry',
                    'refs':[r for t in option for r in t['refs']],
                    'tokens':[{'text':t['text'],'refs':t['refs']} for t in option],
                    'role':'alternative'})
            if len(options)>1:
                item.update(decision='retained-tied',evidence='All equally supported locations remain recorded; none was chosen arbitrarily.')
            elif len(options)==1 and options[0]:
                rendering = render_reading(text[a:b],text,a,b,item['readings'][0]['text'])
                if rendering:
                    item.update({k:v for k,v in rendering.items() if k!='applied_text'})
                    item['readings'][0].update(role='chosen',trim=rendering['trim'],
                                              applied_text=rendering['applied_text'])
                    item.update(decision='substitute',evidence='Editorial adoption of the TLG Greek reading located by '+method+'. This does not certify what Bekker printed.')
            records.append(item)
    source = {'id':'tlg-photius-henry','edition':'René Henry, Photius. Bibliothèque, volumes 1–8 (1959–1977)',
        'citation':'Thesaurus Linguae Graecae, Photius, Bibliotheca, 4040.001; Henry edition',
        'url':'https://stephanus.tlg.uci.edu/Iris/indiv/browser.jsp#doc=tlg&aid=4040&wid=001',
        'sha256':sha(html_raw),
        'qualification':'Greek base text only; editorial substitution, not Bekker scan verification. TLG is acknowledged as the comparison text provider.'}
    return {'schema':SCHEMA,'reviewed_at':reviewed_at,'input_corpus_sha256':sha(raw[CORPUS]),
        'input_pins':{p.as_posix():sha(v) for p,v in raw.items()},
        'recipe_sha256':{name:sha((root/'scripts'/name).read_bytes()) for name in
            ('prepare_photius_editorial_substitutions.py','compare_photius_local_edition.py',
             'repair_photius_context.py','repair_photius_uncertainties.py','assess_photius_historical.py')},
        'source':source,'counts':dict(Counter(r['decision'] for r in records)),
        'records':records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-html',type=Path,required=True)
    parser.add_argument('--reviewed-at',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/OUTPUT)
    parser.add_argument('--check',action='store_true',help='Reproduce existing source decisions byte-for-byte')
    args = parser.parse_args()
    review = prepare(args.source_html.read_bytes(),reviewed_at=args.reviewed_at)
    encoded=(json.dumps(review,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    if args.check:
        if args.output.read_bytes()!=encoded:
            raise ValueError('Editorial preparation differs from its source, code, or pinned predecessor')
    else:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(encoded)
    print(json.dumps({'records':len(review['records']),'counts':review['counts']}))


if __name__=='__main__':
    main()
