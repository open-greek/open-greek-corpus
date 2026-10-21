"""Complete direct scan observations for retained historical physical page168.

Source lines and inset boundaries were directly inspected in overlapping crops.
Bounded digital context preserves its independent readings and defects.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:17:45.440486Z'
LINES={
 3:'δείξῃ· ἀλλὰ καὶ ἡνίοχοι καὶ πωλοδάμναι καὶ διδάσκαλοι',
 4:'μειζόνως εὐδοκιμοῦσιν, ὅταν τῶν αὐτῶν ἕτεροι κύριοι',
 5:'καθεστῶτες μὴ τῶν ἴσων ἄξιοι γένωνται, καὶ νὴ Δί’ ἄν',
 6:'γε καὶ κατὰ τοὺς αὐτοὺς χρόνους. φέρε δὴ καὶ περὶ',
 7:'τῶν συμβεβηκότων αὐτῶν τοῖς ἀνδράσι σκεψώμεθα',
 8:'καὶ διέλθωμεν. οὐ γὰρ ἁπάντων ὁ δῆμος οὑτωσὶ κατε-',
 9:'ψηφίσατο, οὐκ ἀπὸ κοινοῦ δόγματος ταῦτα ἔπαθον, ἀρ-',
 10:'χὴν δὲ οὐδὲ ταῦτα πάντες· πόθεν; ἀλλὰ Θεμιστοκλῆς',
 11:'μὲν καὶ Κίμων {u0}· “τοῦτο δ’ ἦν οὐ μῖσος',
 12:'οὐδ’ ἀλλοτρίωσις τῷ δήμῳ πρὸς αὐτούς, ἀλλ’ ἦν νόμος',
 13:'αὐτοῖς περὶ ταῦτα, ἔχων μὲν ὁπωσδήποτε (ἐῶ γάρ,',
 14:'εἰ μὴ σφόδρα ἄν τις ἐπαινέσαι τὸν νόμον), τὸ δ’ ἂν',
 15:'ἁμάρτημα οὐκ ἀπαραίτητον αὐτῶν, ἀλλ’ ἔχον ὡς ἐν',
 16:'τοιούτοις εὐπρέπειαν· νόμῳ γάρ, ὥσπερ εἶπον, ἐγίνετο.',
 17:'ἦν δὲ οὗτος ὁ νόμος· {u0} τοὺς ὑπερέχοντας μεθι-',
 18:'στάντες ἔτη δέκα, ἄλλο δὲ οὐδὲν ἔγκλημα προσῆν, οὐδ’',
 19:'ὡς ἐπὶ ἐλέγχῳ πραγμάτων ὀργή. καίτοι πῶς οὐ δει-',
 20:'νόν, εἰ ἃς οὐδ’ αὐτοὶ οἱ μεθιστάντες εἶχον {u0},',
 21:'τούτους αἰτιασόμεθα ἡμεῖς διὰ τοὺς μεταστήσαντας;',
 22:'ὥσπερ οἱ βέβαιον μὲν οὐδ’ ὁτιοῦν ἐπιστάμενοι, ἀκοὴν δέ',
 23:'τινα κατηγοροῦντες, καὶ ταῦτ’ οὐδ’ αὐτὴν σαφῆ τὴν',
 24:'ἀκοήν. ἀλλ’ ἐκεῖσε ἐπάνειμι, ὅτι ὑπὲρ τοῦ τὰ φρονή-',
 25:'ματα {u0} τοῦτο τὸ εἶδος τῆς φυγῆς ἐνόμισαν. οὔκουν',
 26:'τούτῳ μεγίστῳ δῆλόν ἐστιν ὅσον κολακείας οἱ ἄνδρες',
 27:'ἀπεῖχον, οὕς γε ὅπως ὑφεῖντο τοῦ φρονήματος διὰ τοῦτο',
 28:'μεθίστασαν, οὐδενὸς ἄλλου τῶν πάντων ἕνεκα. ὥστε τοῦτό',
 29:'γε οὐ κατ’ αὐτῶν ἀλλ’ ὑπὲρ αὐτῶν ἔλαθες εἰρηκώς, ὡς',
 30:'δεινὸς σὺ τηρεῖν τὰ λεγόμενα καὶ τοὺς ἄλλους ἐλέγχειν.',
 31:'δοκοῦσι γάρ μοι τὰς συμφορὰς ἐνθυμηθέντας τὰς ἐπὶ',
 32:'τῶν Πεισιστρατιδῶν γενομένας ἑαυτοῖς μηδένα {u0}',
 33:'μεῖζον ἐᾶν τῶν πολλῶν φρονεῖν, ἀλλ’ ἐξ ἴσου εἰς δύ-',
 34:'ναμιν εἶναι. δίκαια ἄρα ἐποίουν ἐλαύνοντες Κίμωνα καὶ',
 35:'Θεμιστοκλέα; οὐ λέγω ταῦτα, ἀλλ’ οὐδ’ {u0} γε',
 36:'παντελῶς, ἀλλὰ καὶ αὐτοῖς ἔχοντα παραίτησιν κἀκεί-',
 37:'νοις οὐκ {u0} τὴν συμφοράν. Περικλῆς δέ,',
 38:'ἕως μὲν εἰρήνην ἡ πόλις ἦγεν, οὐδεμίαν οὔτε μείζω οὔτε',
 39:'ἐλάττω παρ’ αὐτοῖς αἰτίαν εἶχεν, ἀλλ’ ἐξ ἴσου τοῖς θεοῖς',
 40:'ἐθαυμάζετο. καὶ ἔτι πρότερον στρατιὰς πολλὰς ἐξα-',
 41:'γαγὼν Ἀθηναίων ἐπὶ τοὺς οὐκ ἐθέλοντας τοῖς δικαίοις'
}
UNCERTAINTIES={
 (168,2):[('ἠγαλῆθ','ἡγεῖσθαι','The compact sigma/theta group and preceding letters remain unresolved independently.'),('ἡμῶν τις φείσῃ','ἡμῶν τις φείσεσθαι','The compact sigma/theta group and verbal ending remain unresolved independently; the digital witness has φείσεται.'),('μηδ’ ἡμῶν φείσῃ','μηδ’ ἡμῶν φείσεσθαι','The compact sigma/theta group and verbal ending remain unresolved independently; the digital witness has φείσεται.'),('γίγνῃ','γίνεσθαι','The compact sigma/theta group remains unresolved independently.'),('δίκαιος ἡμῖν','δίκαιος ἦσθα','The compact sigma/theta group and ending remain unresolved independently.')],
 (168,11):[('ἐξωγρακίσθησαν','ἐξωστρακίσθησαν','The compact sigma/theta group and preceding consonants remain unresolved independently.')],
 (168,17):[('ἐκὼλον','ἐκόλυον / ἐκάλουν','The compact verbal vowel and ending remain unresolved independently.')],
 (168,25):[('ἐπαχὼν','ἐπισχεῖν','The compact sigma/chi group remains unresolved independently.')],
 (168,20):[('αἰτιώμενοι','αἰτιάσασθαι','The compact sigma/theta group remains unresolved independently.')],
 (168,32):[('βέλτιον','βούλεσθαι','The compact vowel and sigma/theta group remain unresolved independently; digital βέλεσθαι differs.')],
 (168,35):[('ἀναίχυντα','ἀναίσχυντά','The compact sigma/chi group remains unresolved independently.')],
 (168,37):[('ἀκήμονα','ἀσχήμονα','The compact sigma/chi group remains unresolved independently.')]
}
LEADING_FRAGMENTS={(168,3):'δείξῃ',(168,9):'ψηφίσατο',(168,10):'χὴν',(168,18):'στάντες',(168,20):'νόν',(168,25):'ματα',(168,34):'ναμιν',(168,37):'νοις',(168,41):'γαγὼν'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    def source(begin,end,changes=()):
        target=_reading(sections,168,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError(before)
            target=target.replace(before,after)
        return target
    region=[.025,.105,.44,.73]
    CHUNKS[(168,2)]=[
     ('Τεῦκρος ἐφη τινὶ',source('καὶ τῶν ἐχθρῶν','Τεῦκρος ἔφη τινί·',[
      ('σαυτᾶ','σαυτοῦ'),('ἡγεῖσθαι','{u0}'),('σοὶ δ’ ἐκ','σοὶ δ’ οὐχ'),('ἡμῶν τις φείσεται','{u1}'),('μηδ’ ἡμῶν φείσεται','{u2}'),('γίνεσθαι','{u3}')]),region,'καὶ τῶν ἐχθρῶν','Τεῦκρος ἔφη τινί·'),
     ('ὑπ’ ὀδόν.','τῷ Ἀγαμέμνονι ὀνειδίσαντι τὸ γένος ὅτι νόθος.',[.025,.30,.44,.54],'τῷ Ἀγαμέμνονι','τὸ γένος ὅτι νόθος.','unclassified-small-type'),
     (None,source('καὶ μὴ βάλε','παραλαβὼν κακίας ἀποδείξῃ·',[
      ('βάλε','βούλου'),('ἐκ ἂν ὠκνήσαμεν','οὐκ ἂν ὠκνήσαμεν'),('ἐβελήθης','ἐβουλήθης'),('ἐκεῖν’ ἕτεροι','οὔκουν ἕτεροι'),('ἐκεῖν’ ὅτ’ ἀμφοτέρων','οὔκουν ὅτ’ ἀμφότερ’ ἂν'),('τοῖς πεπολιτευμένοις','τοὺς πεπολιτευμένους'),('μειζόνως τὰ πρὸς','μείζονος τὰ πρὸς'),('δίκαιος ἦσθα','{u4}'),('πᾶν δίκαιον μόνος','πῇ δίκαιον μόνους'),('τὰς ἐκ μόνος','τοὺς οὐ μόνους'),('ἔκουν τάς γε ἡνιόχας','οὔκουν τοὺς γε ἡνιόχους'),('τὰς ἐξ ἀρχῆς','τοὺς ἐξ ἀρχῆς'),('ἵππες','ἵππους'),('κακίας ἀποδείξῃ·','κακῶς ἀπο-')]),region,'καὶ μὴ βάλε','παραλαβὼν κακίας ἀποδείξῃ·')]
    for number,target in LINES.items():
        region=[.39,.105,.81,.34]if number<=16 else[.39,.30,.81,.54]if number<=29 else[.39,.485,.81,.73]
        chunks=[(None,target,region,'ἀποδείξῃ· ἀλλὰ καὶ','τοῖς δικαίοις')]
        for line_number,label in[(7,'5'),(12,'10'),(17,'15'),(22,'20'),(27,'25'),(32,'30'),(37,'35')]:
            if number==line_number:chunks.insert(0,(label,'',region,None,None,'marginal-reference',label))
        CHUNKS[(168,number)]=chunks
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
                if leading and not role and (a==0 or all(s.get('text_role')for s in segments)):
                    if not text.startswith(leading):raise ValueError('Changed printed leading fragment')
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source line or page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
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
