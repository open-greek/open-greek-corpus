"""Complete direct scan observations for retained historical physical page166.

Digital passages are independently bounded alternatives. Every retained word in
both source columns was inspected, including unchanged text and word fragments.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:14:31.786460Z'
PASSAGES={
 1:('σεσωσμένος ὑπ’ αὐτοῦ','προσεῖναι προσήκει.',[
 ('μέγιστον δύνασθαι ἄλλος','{u0}'),('ἀνίσχοντος','{u1}'),('τοιούτῳ ὄντι ἐκ ἱκανὴ','τοιούτῳ ὄντι οὐκ ἱκανὴ'),('φυλάξασθαι','{u2}'),('γενέσθαι','{u3}'),('ἀφείσθω','{u4}'),('δέχεσθαι','{u5}'),('κέχρηται','{u6}'),('διεξέρχεται','{u7}'),('ὁμολογεῖται','{u8}'),('πραγματεύεσθαι','{u9}'),('ὁρίζω','{u10}'),('καταισχύνειν','{u11}')]),
 2:('Ἐκ τῆς κοινῆς ἀπολογίας.','Ἐκ τῆς κοινῆς ἀπολογίας.',[]),
 3:('τὸ προοίμιον. Ἃ μὲν','τὸ προοίμιον. Ἃ μὲν',[(' Ἃ μὲν','')]),
 4:('Ἃ μὲν τοίνυν','ἐκείνοις χρώμενοι κατώρθουν,',[
 ('εἰρῆσθαι','{u0}'),('ἰχυρίζετο','{u1}'),('ἡγεῖσθαι','{u2}'),('ἐδ’ ἡμᾶς','οὐδ’ ἡμᾶς'),('ἀπέχεσθαι','{u3}'),('βέλτισον','βέλτιστον'),('κατώρθουν,','κα-')]),
 5:('κατώρθουν, οὐδὲν','ἐξέφυγε καὶ ἐνέμεινε',[
 ('κατώρθουν','τώρθουν'),('τὰ δοκουντά','τὰ δοκοῦντά'),('αὐτὰς ἐκείνας','αὐτοὺς ἐκείνους'),('τὰς γραμματιστάς','τοὺς γραμματιστάς'),('ὅταν ἔξω','οὐκ ἂν ἐξ ὧν'),('ἀφ’ οὗ πείθοντες','ἄρ’ οἱ πείθοντες'),('ὡς οὐδ’ αὐτοὶ βελτίους ἦσαν ἐδενὸς','ὡς οὐδ’ αὐτοὶ βελτίους οὐδενὸς ἦσαν'),('ἐκ ἀγαπᾷς','οὐκ ἀγαπᾷς'),('ἐξί σοι','ἐξέσοι'),('κατασχεῖν','{u0}'),('μηδ’ ἀθάνατα','μηδ’ ἀθανάτους'),('μὴ ἐδυνήθησαν','μὴ ἠδυνήθησαν'),('οὐκ ἐφικνέμενοι','οὐκ ἐφικνούμενοι')])
}
UNCERTAINTIES={
 (166,1):[('μείγνον ὄντος','μέγιστον δύνασθαι ἄλλος','The compact verb and its sigma/theta group remain unresolved independently.'),('ἀνύχοντος','ἀνίσχοντος','The compact sigma/chi group remains unresolved independently.'),('φιλάγαθῳ','φυλάξασθαι','The compact medial letters and sigma/theta group remain unresolved independently.'),('γενέσθαι','γενέσθαι','The unchanged compact sigma/theta group remains unresolved independently.'),('ἀφειδῶ','ἀφείσθω','The compact sigma/theta group remains unresolved independently.'),('δέχασθαι','δέχεσθαι','The compact sigma/theta group remains unresolved independently.'),('κέχρη','κέχρησθαι / κέχρηται','The compact final group and ending remain unresolved independently; preserve the differing digital reading.'),('διεξέρχεσθαι','διεξέρχεσθαι / διεξέρχεται','The compact final group remains unresolved independently; the digital ending differs.'),('ὁμολογεῖ','ὁμολογεῖσθαι','The compact final sigma/theta group remains unresolved independently.'),('πραγματευσθαι','πραγματεύεσθαι','The compact sigma/theta group and preceding ending remain unresolved independently.'),('ἄρξιν','ὁρίζω','The compact verb remains unresolved independently.'),('κατασχόντων','καταισχύνειν','The compact sigma/chi group and medial letters remain unresolved independently.')],
 (166,4):[('εἰρήθη','εἰρῆσθαι','The compact sigma/theta group remains unresolved independently.'),('ἰχνῶσι','ἰσχυρίζεσθ’ / ἰσχυρίζετο','The compact sigma/chi group and ending remain unresolved independently; the digital reading differs.'),('ἡγεῖτο','ἡγεῖσθαι','The compact sigma/theta group remains unresolved independently.'),('ἀπέχεσθαι','ἀπέχεσθαι','The unchanged compact sigma/theta group remains unresolved independently.')],
 (166,5):[('καταχεῖν','κατασχεῖν','The compact sigma/chi group remains unresolved independently.')]
}
LEADING_FRAGMENTS={(166,5):'τώρθουν'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,166,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[.025,.105,.44,.56]if number==1 else[.025,.37,.44,.73]if number<=4 else[.39,.105,.81,.73]
        item=(None,target,region,begin,end)
        if number in(2,3):item=(*item,'unclassified-heading')
        CHUNKS[(166,number)]=[item]
    return _records(rows,document,crop_png,sections)


def _row_sha(row):
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _reading(sections,page,begin,end):
    if begin is None:return []
    section=f'tlg4040-tlg001-local002-s{page+277}'; full=sections[section]
    starts=[m.start()for m in re.finditer(re.escape(begin),full)]
    if len(starts)!=1:raise ValueError(f'Ambiguous digital bound {page}: {begin!r}')
    a=starts[0];b=full.index(end,a)+len(end)
    return [{'kind':'digital','section':section,'start':a,'end':b,'text':full[a:b]}]


def _records(rows,document,crop_png,sections):
    result=[];image_hashes={}
    for (page,number),chunks in sorted(CHUNKS.items()):
        locus=f'helladius_chrestomathia_photius_bekker_v2_{page:04}.{number}'
        row=rows[locus]; original=row['text']; cursor=0; segments=[]
        for chunk in chunks:
            anchor,target,region,begin,last,*role_info=chunk
            end=len(original)if anchor is None else original.index(anchor,cursor)+len(anchor)
            role=role_info[0]if role_info else None
            literal=role_info[1]if len(role_info)>1 else None
            key=(page,tuple(region))
            if key not in image_hashes:image_hashes[key]=hashlib.sha256(crop_png(document,page,region)).hexdigest()
            reading=_reading(sections,page,begin,last)
            ranges=[]
            for i,(old,observed,reason)in enumerate(UNCERTAINTIES.get((page,number),[])):
                marker='{u'+str(i)+'}'
                if marker in target:
                    a=original.index(old,cursor,end); ranges.append((a,a+len(old),observed,reason,marker))
            ranges.sort();part_cursor=cursor;target_cursor=0
            def add(a,b,text,observed=None,reason=None):
                if a==b:
                    if text:raise ValueError('Unattached insertion')
                    return
                fragments=[]
                leading=LEADING_FRAGMENTS.get((page,number))
                if a==0 and leading:
                    if not text.startswith(leading):raise ValueError('Changed printed leading fragment')
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
                if text.endswith('-'):
                    m=re.search(r'[^\W\d_]+-$',text)
                    fragments.append({'start':m.start(),'end':m.end(),'text':m.group(),'side':'trailing','qualification':'This retained passage ends within a visibly divided printed word; preserve the source fragment and exclude it from lexical counts.'})
                segment={'start':a,'end':b,'original_text':original[a:b],'corrected_text':text,
                    'verification':'uncertain'if reason else'verified','review_basis':'direct-scan-inspection',
                    'reviewed_at':REVIEWED_AT,'evidence':'Direct inspection of every word and punctuation mark, including unchanged text, in this contiguous passage. The overlapping pinned crops cover the full retained source. Independent digital readings remain bounded alternatives, not automatic authority.',
                    'scan':{'physical_page':page,'region':region,'max_side':3600,'image_sha256':image_hashes[key],'observed_text':observed if observed is not None else literal if literal is not None else text},
                    'readings':deepcopy(reading),'fragments':fragments,
                    'transcription_convention':'Expand clearly visible printed ου, στ, and καί ligatures. Reflow complete words visibly divided between lines within a retained passage. Preserve incomplete passage boundaries; omit marginal references and printed line numbers from body transcription.'}
                if reason:segment['uncertainty']=reason
                if role:
                    segment['text_role']=role
                    segment['evidence']+=(' This is an isolated marginal reference label; the body projection omits it.'if role=='marginal-reference'else' This is part of the centered, letter-spaced source-identification heading between extracts. Its placement and type establish the heading boundary without establishing authorship; preserve its literal text and exclude it from lexical admission pending attribution.'if role=='unclassified-heading'else' This inset small-type explanatory paragraph follows the large-type body and precedes the lower apparatus; its typography establishes boundaries without establishing authorship. Exclude it pending attribution.')
                segments.append(segment)
            for a,b,observed,reason,marker in ranges:
                mark=target.index(marker,target_cursor)
                add(part_cursor,a,target[target_cursor:mark]);add(a,b,original[a:b],observed,reason)
                part_cursor=b;target_cursor=mark+len(marker)
            add(part_cursor,end,target[target_cursor:]);cursor=end
        if cursor!=len(original):raise ValueError('Incomplete reviewed row')
        result.append({'locus':locus,'original_row_sha256':_row_sha(row),'status':'reviewed-with-uncertainty'if any(s['verification']=='uncertain'for s in segments)else'reviewed-verified','segments':segments})
    return result


def occurrence_observations(rows, document, crop_png, sections):
    """Project only exact, unambiguous, paired occurrences already source-reviewed.

    This creates no new review status. Uncertain glyphs, source-disagreement
    changes, marginal references, unclassified small type, and printed fragments
    cannot enter this conservative projection for the existing batch schema.
    """
    from difflib import SequenceMatcher
    from assess_photius_historical import tokens
    output = []
    for record in records(rows, document, crop_png, sections):
        row = rows[record['locus']]
        page = int(record['locus'].split('_')[-1].split('.')[0])
        section = f'tlg4040-tlg001-local002-s{page+277}'
        digital = sections[section]
        digital_tokens = tokens(digital)
        boundaries = {(word['start'], word['end']) for word in digital_tokens}
        for segment in record['segments']:
            if segment['verification'] != 'verified' or segment.get('text_role'):
                continue
            before, after = segment['original_text'], segment['corrected_text']
            old_words, new_words = tokens(before), tokens(after)
            matcher = SequenceMatcher(None, [w['text'] for w in old_words],
                [w['text'] for w in new_words], autojunk=False)
            for action, a, b, c, d in matcher.get_opcodes():
                if action != 'replace' or not a < b or not c < d:
                    continue
                old_start, old_end = old_words[a]['start'], old_words[b-1]['end']
                new_start, new_end = new_words[c]['start'], new_words[d-1]['end']
                if any(new_start < fragment['end'] and new_end > fragment['start']
                       for fragment in segment['fragments']):
                    continue
                old, new = before[old_start:old_end], after[new_start:new_end]
                positions = set()
                for reading in segment['readings']:
                    if reading.get('kind') != 'digital':
                        continue
                    for match in re.finditer(re.escape(new), reading['text']):
                        start = reading['start'] + match.start()
                        end = start + len(new)
                        # Multiword spans need exact token boundaries at both ends.
                        if (any(w['start'] == start for w in digital_tokens)
                                and any(w['end'] == end for w in digital_tokens)):
                            positions.add(start)
                if len(positions) != 1:
                    continue
                chosen = positions.pop()
                old_matches = [m.start() for m in re.finditer(re.escape(old), row['text'])]
                new_matches = [m.start() for m in re.finditer(re.escape(new), digital)]
                original_start = segment['start'] + old_start
                if original_start not in old_matches or chosen not in new_matches:
                    raise ValueError('Reviewed occurrence projection changed an exact span')
                item = {'locus': record['locus'], 'page': page,
                    'original_text': old, 'corrected_text': new,
                    'source_region': segment['scan']['region'],
                    'evidence': 'Direct inspection of the complete retained passage on the pinned Bekker scan confirms this exact occurrence; its corrected reading also agrees with one explicitly bounded digital counterpart. This projection excludes unresolved glyphs, differing witness readings, word fragments, and unclassified material.'}
                if len(old_matches) != 1:
                    item['occurrence'] = old_matches.index(original_start)
                if len(new_matches) != 1:
                    item['digital_occurrence'] = new_matches.index(chosen)
                output.append(item)
    return output
