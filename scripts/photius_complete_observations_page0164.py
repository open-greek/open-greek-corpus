"""Complete direct scan observations for retained historical physical page164.

Independent digital excerpts are retained as bounded alternatives. The authored
substitutions and glyph uncertainties record inspection of the full source.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:10:58.556927Z'
PASSAGES={
 1:('αἰτιολογίαν·','τοῦ ἐπιχειρήματος.',[]),
 2:('συνιδὼν ἐκεῖνος','οὐ μόνον τοῖς ὀφθαλμοῖς.',[('χρήσονθ’','{u0}'),('ὑφίεσθαι','{u1}'),('ὑποσχόμενος','{u2}'),('ἀνακτήσασθαι','{u3}'),('ἀλλ’ ἐκ αὐτὴν','ἀλλ’ οὐκ αὐτὴν'),('ἡγεμόνων ἢ ἡγεμόνες','ἡγεμόνων γὰρ ἡγεμόνες'),('τοῖς ἀκάσσοιν','{u4}'),('ὥςε','ὥστε'),('αὐτὰς ὥσπερ παῖδας','αὐτοὺς ὥσπερ παῖδας'),('ἀτρεμιζούσῃ τάττας','{u5}'),('ἑώσσιν','{u6}'),('σχῆμα','{u7}')]),
 3:('ἐκᾶν δεινόν,','εἶτα λέγεις ὡς οὐ πολλὰ τινὸς',[('ἐκᾶν δεινόν','{u0}'),('τὰς πολεμίας','τοὺς πολεμίους'),('καὶ ᾧ τῆς ἀρετῆς','καὶ {u1} ἀρετῆς'),('τάτοις','τούτοις'),('τὰν μέσῳ','τἀν μέσῳ'),('ἐπειγομένων','ἐπειγομένων'),('ὁπωσῶν','ὁπωσοῦν'),('οὐ πολλὰ','οὐ πολλοῦ')]),
 4:('ἡ σωτηρία ἄξιον.','ἄν τι δόξειε λέγειν.',[('ἄξιον','ἄξιον'),('ἔστι τό γε ἐκ τοῦ λόγου','ἔξεστι τό γε ἐκ τοῦ λόγου')]),
 7:('ἐγὼ δ’, εἰ μὲν','τοῦ μηδενός.',[('τότε ᾤμην τὰς λόγας','τότε ᾤμην τοὺς λόγους'),('ἐπινῶ πᾶ διακέκριται','{u0}'),('πολλὰ τινὸς','πολλοῦ τινὸς')]),
 9:('εἰ δ’ ἅπασα μὲν','ἀπὸ τῷ πύργῳ κρίνομεν;',[('ξεροῖς','στενοῖς'),('τὰς Ἀχαιὰς','τὰς Ἀχαιὰς')]),
 11:('μόνος δέ μοι δοκεῖ','ἀληθῆ τὸν λόγον',[])
}
UNCERTAINTIES={
 (164,2):[('χρήσοιντο','χρήσοινθ’ / χρήσονθ’','The compact final consonant group and ending remain unresolved independently.'),('ὑπέλαχε','ὑφίεσθαι','The compact sigma/theta group and preceding letters remain unresolved independently.'),('ἐποχόμενος','ὑποσχόμενος','The compact sigma/chi group remains unresolved independently.'),('ἀνακτήσασθαι','ἀνακτήσασθαι','The unchanged compact sigma/theta group remains unresolved independently.'),('τοῖς ἀκώσις','τοῖς ἀκάσσοιν','The compact noun ending remains unresolved independently; the digital alternative is retained separately.'),('ἀτερμιζόση τάτεις','ἀτρεμιζούσῃ τάττας','The compact participial ending and following verb remain unresolved independently.'),('ἐξῶσιν','ἑώσιν / ἑώσσιν','The compact verb and vowel group remain unresolved independently.'),('χῆμα','σχῆμα','The compact sigma/chi group remains unresolved independently.')],
 (164,3):[('ἄχον διττόν','ἄκων δεινόν / ἐκᾶν δεινόν','The compact opening connective and adjective remain unresolved independently.'),('ὁ τῆς','ᾧ τῆς / ὁ τῆς','The compact relative or article and its accent remain unresolved independently.')],
 (164,5):[('οἴδαμεν μὴ παραλαμβάνειν','οὐδεμῶς μὴ παραλαμβάνεται','The compact small-type opening words remain unresolved independently.'),('αὐτὸ','εἰ / αὐτό','The final short small-type word remains unresolved independently; it is separated typographically from the following large-type body.')],
 (164,6):[('διαλύεσθαι','διαλεγομένων / διαλέγεσθαι','The compact small-type final word and ending remain unresolved independently.')],
 (164,7):[('ἔχειν ἄν ἀπὸ τοῦ πῶ διακρίνειν','οὐκ ἐννοῶ πῶ διακέκριται','The compact verb and following verbal ending remain unresolved independently.')],
 (164,8):[('λαλεῖν','λέγειν','The initial small-type verb remains unresolved independently.'),('προαύσει τὴν παρακεφαλαιον','προσεῖπε τὴν περικεφαλαίαν','The compact small-type verb and following noun remain unresolved independently.')]
}
LEADING_FRAGMENTS={}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes) in PASSAGES.items():
        reading=_reading(sections,164,begin,end)[0]['text']
        for before,after in changes:
            if before not in reading:raise ValueError((number,before))
            reading=reading.replace(before,after)
        region=[.025,.105,.44,.34] if number==1 else [.025,.16,.44,.63] if number==2 else [.025,.485,.44,.73] if number==3 else [.39,.105,.81,.34] if number==4 else [.39,.265,.81,.54] if number==7 else [.39,.485,.81,.73]
        chunks=[(None,reading,region,begin,end)]
        if number==1:chunks[0]=(*chunks[0],'unclassified-small-type')
        CHUNKS[(164,number)]=chunks
    CHUNKS[(164,5)]=[
      ('αὐτὸ','“ἀντὶ τοῦ {u0} τὸ ἤ που ἐνταῦθα.” δι’ ὃ Ἀριστείδης ἀντὶ τοῦ πολλῷ πλέον ἔλαβεν. εἰρωνευόμενος δὲ τὸ πολλῷ πλέον ἔστω, οἷον οὐδ’ ὅλως, καὶ πολλάκις οὕτω τῷ ἤ που ἀντὶ τοῦ πολλῷ πλέον χρῆται, μᾶλλον δὲ σχεδὸν {u1}',[.39,.105,.81,.34],None,None,'unclassified-small-type'),
      (None,_reading(sections,164,'καὶ μὴν οὐχ ὅμοιον','Ἀθηναίους εἰς τὰς τριήρεις.')[0]['text'].replace('Θεμιστοκλέας','Θεμιστοκλέος'),[.39,.105,.81,.34],'καὶ μὴν οὐχ ὅμοιον','Ἀθηναίους εἰς τὰς τριήρεις.')]
    CHUNKS[(164,6)]=[(None,'παροιμία· τάττεται δὲ ἐπὶ τῶν ἄλλα ἀντ’ ἄλλων ποιούντων ἢ εἰρηκότων. παρῆκται δὲ ἀπὸ τοῦ τὸν Πρίαμον καὶ τὴν Ἑλένην ἐκ τοῦ τείχους θεωροῦντας τοὺς Ἕλληνας περὶ αὐτῶν {u0}.',[.39,.265,.81,.54],None,None,'unclassified-small-type')]
    CHUNKS[(164,8)]=[(None,'{u0} τὸ δὲ νομίζεσθαι. {u1} λέγει, βύρσαν δὲ τὸ δέρμα παρὰ τὸ δεῖν βύρσαν περὶ αὐτοῦ, νήϊα δὲ τὰ σχοινία, κωπέας δὲ τὰ ξύλα τὰ πρὸς πλοῦν ἐπιτήδεια.',[.39,.485,.81,.73],None,None,'unclassified-small-type')]
    CHUNKS[(164,10)]=[(None,'παροιμία· ὥσπερ ὁ Πρίαμος ἐκ τοῦ τείχους καὶ Ἑλένη.',[.39,.485,.81,.73],None,None,'unclassified-small-type')]
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
