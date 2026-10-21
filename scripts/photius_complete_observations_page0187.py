"""Complete direct scan review of physical187, all retained lines and prose.

Manual line transcriptions preserve divided words and uncertain source glyphs.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:05:31.560479Z'
LINES={1: 'παροπτῶν ταύτην ἔχει προσφοράν. ἔχουσι δὲ ἔτοι κα-',
 2: 'κὸν ἄφυκτον, τοὺς ἐν τοῖς ἕλεσι λέοντας ἐπιτιθεμένους',
 3: 'αὐτοῖς. ὑπὸ δὲ τὴν ἐπιτολὴν τοῦ κυνὸς γίνεται τι κω-',
 4: 'νώπων πλῆθος ἄπλετον, τηλικαύτην ἔχον δύναμιν ὥστε',
 5: 'τὸν λαὸν εἰς τὰς λιμνώδεις ὑγρασίας ἀπελθόντα ἐκεῖ',
 6: 'μένειν ἀφανῆ. ὑφ’ ὧν καὶ οἱ λέοντες {u0}, οὐχ',
 7: 'ἥττως ὑπὸ τοῦ δηγμοῦ δηλούμενοι, καίπερ ὄντος ἐπαχθοῦς,',
 8: 'ὡς τὸν ὑπὸ τῆς φωνῆς ἦχον ἀλλόφυλον ἀδυνατοῦντες',
 9: 'φέρειν. ἀλλὰ ταῦτα μὲν ἀπηγγέλθω τοῦ παραδόξου χά-',
 10: 'ριν· τί γὰρ ἰδιώτερον ἢ λέοντας μὲν ἐκχωρεῖν κώνωψιν,',
 11: 'ἀνθρώπους δὲ {u0} ὑπὸ τοιούτου κινδύνου;',
 12: 'ὅτι τοῖς εἰρημένοις, φησί, τὸ τῶν ὑλοφάγων καὶ',
 13: 'τῶν τὰ σπέρματα σιτουμένων ἐγγίζει γένος, βραχεῖαν',
 14: 'ἔχον τὴν παραλλαγήν. οἱ μὲν γὰρ τὸν πίπτοντα καρ-',
 15: 'πὸν ἀπὸ τῶν δένδρων {u0} [καὶ] ὑπὸ τὴν θερείαν,',
 16: 'τὸ δὲ λοιπὸν τῆς πόας {u0} τῆς ἐν τοῖς σκιεροῖς',
 17: 'ἄγκεσι γινομένης ξηρᾶς τε τὴν φύσιν καὶ καυλὸν ἐκ-',
 18: 'τρεφούσης παρόμοιον ταῖς καλουμέναις {u0}· οἱ',
 19: 'δὲ τῆς ὕλης τὴν ἁπαλὴν {u0}. οὗτοι τὰς μὲν νύκτας',
 20: '{u0} τόπον ἀπὸ τῶν ἐκεῖ θηρίων πρὸς ὀχύρωσιν',
 21: 'ἐξειλεγμένοι καὶ φυλακήν, ἅμα δὲ ἡλίῳ μετὰ τέκνων',
 22: 'καὶ γυναικῶν ἐπὶ τὰ δένδρα πάντες ἀναβαίνουσι, σπου-',
 23: 'δῇ καταλαβεῖν ζητοῦντες τὰς ἄκρας κλῶνας· κἀκεῖθεν',
 24: 'τὴν ἁπαλωτάτην ὕλην ἀμέλγοντες εὐμαρῶς {u0}.',
 25: 'τοιαύτην δὲ ἐκ τοῦ παντὸς βίου {u0} τὴν ἕξιν,',
 26: 'ὥστε καὶ τὸ τῆς ἀναδρομῆς ἄπιστον ἔχειν τὴν θέαν καὶ',
 27: 'τὴν συντονίαν οὐ χειρῶν μόνον καὶ δακτύλων καὶ ποδῶν,',
 28: 'ἀλλὰ καὶ τῶν μερῶν τῶν ὑπολοίπων ἁπλῶς. μετα-',
 29: 'πηδῶσι γὰρ εὐπόρως ἀπ’ ἄλλου πρὸς ἕτερον ἀκρέμονα, καὶ',
 30: 'τοὺς κλάδους ἀλλήλων πολλάκις ἐν τοῖς ἐπισφαλεστάτοις',
 31: 'τόποις {u0}, καὶ τοιαῦτα {u1} ὥστε τὸν ἰδόντα',
 32: 'αὐτὸν μὲν {u0}, μὴ μέντοι θαῤῥεῖν εἰς τοὺς ἀπεί-',
 33: 'ρους ἐξαγγέλλειν. καὶ πάντα δὲ κλάδον τοῖς ὀδοῦσιν ἔγχυ-',
 34: 'λον {u0} καὶ ταῖς κοιλίαις εὐπόρως πέττουσι·',
 35: 'καὶ τὸ σφαλὲν ἄνωθεν σῶμα διὰ τὴν ἰχνότητα οὐ',
 36: 'βαρείας τυγχάνει τῆς πληγῆς. οὗτοι δὲ γυμνοὶ μέν εἰσι',
 37: 'πάντες, {u0} δὲ κοινοῖς καὶ τέκνοις καὶ γυναιξί, πο-',
 38: 'λεμοῦσι δὲ περὶ τῶν τόπων ἀλλήλοις, μεταλλάττουσι δὲ',
 39: 'οἱ πλεῖστοι λιμῷ πιεζόμενοι, γλαυκωμάτων περὶ τὰ πεν-',
 40: 'τήκοντα ἔτη τοῖς ὄμμασιν ἐπιτρεχόντων.',
 41: 'ὅτι μετὰ τοὺς εἰρημένους εἰσὶν οἱ παρὰ τοῖς',
 42: 'ἐγχωρίοις λεγόμενοι {u0}. οὗτοι διὰ τὴν τῶν θη-'}
PASSAGES={46: ('φοράν, ἣν ὁ τόπος',
      'τρόπον τῆς καταφορᾶς τυγχάνειν',
      [('φοράν,', 'ρίων φοράν,'),
       ('ταῦτα ποιοῦνται.', 'ταῦτα {u0}'),
       ('τὸν βίον ποιοῦνται. οἱ', 'τὸν βίον {u1}'),
       ('παραγίνονται', '{u2}'),
       ('εὐωχοῦνται', '{u3}'),
       ('τὸν ἔσχατον', 'τὸν {u4}'),
       ('τοῦ ἐσχάτου', 'τοῦ {u5}'),
       ('θηρῶσιν αὐτὰς', 'θηρῶσιν αὐτοὺς'),
       ('διαλύεται', '{u6}'),
       ('τὰς μὲν δύο πόδας', 'τοὺς μὲν δύο πόδας'),
       ('ὑπερείδεσθαι', '{u7}'),
       ('ὀχεῖσθαι', '{u8}'),
       ('τυγχάνειν', 'τυγχά-')])}
UNCERTAINTIES={(187, 6): [('ἐκποιῶσιν', 'ἐκτοπίζονται', 'The compact final consonants remain unresolved independently.')],
 (187, 11): [('σώζεσθαι',
              'σώζεσθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently.')],
 (187, 15): [('σιτοῦν', 'σιτοῦνται', 'The compact final consonants remain unresolved independently.')],
 (187, 16): [('ἁπτὸν', 'ἅπτονται', 'The compact final consonants remain unresolved independently.')],
 (187, 18): [('βασιλίαις',
              'ῥαφανίσιν / βανιάσιν',
              'The compact plant name remains unresolved independently; the digital witness differs.')],
 (187, 19): [('αἰτοῦν', 'σιτοῦνται', 'The compact final consonants remain unresolved independently.')],
 (187, 20): [('κοιμῶν', 'κοιμῶνται', 'The compact final consonants remain unresolved independently.')],
 (187, 24): [('σιτοῦν', 'σιτοῦνται', 'The compact final consonants remain unresolved independently.')],
 (187, 25): [('πεπαίδευται', 'πεποίηνται', 'The compact final consonants remain unresolved independently.')],
 (187, 31): [('ἀφαιρῶν', 'ἀφαιροῦνται', 'The compact final consonants remain unresolved independently.'),
             ('ἐνδείκνυν', 'ἐνδείκνυνται', 'The compact final consonants remain unresolved independently.')],
 (187, 32): [('ἐκπλήττεσθαι',
              'ἐκπλήττεσθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently.')],
 (187, 34): [('κατεργάζονται', 'κατεργάζονται', 'The compact final consonants remain unresolved independently.')],
 (187, 37): [('χρῶν', 'χρῶνται', 'The compact final consonants remain unresolved independently.')],
 (187, 42): [('κνηφῆς', 'κυνηγοί', 'The compact noun ending remains unresolved independently.')],
 (187, 46): [('ποιοῦσι.', 'ποιοῦνται.', 'The compact final consonants remain unresolved independently.'),
             ('ποιοῦσι. οἱ', 'ποιοῦνται. οἱ', 'The compact final consonants remain unresolved independently.'),
             ('παραγίγνεται', 'παραγίνονται', 'The compact final consonants remain unresolved independently.'),
             ('ἐκωχύνουσι', 'εὐωχοῦνται', 'The compact final consonants remain unresolved independently.'),
             ('ἕκατον', 'ἔσχατον', 'The compact sigma/theta or sigma/chi group remains unresolved independently.'),
             ('ἑκάστου', 'ἐσχάτου', 'The compact sigma/theta or sigma/chi group remains unresolved independently.'),
             ('διαλύεται', 'διαλύεται', 'The compact final consonants remain unresolved independently.'),
             ('ὑπερείδως',
              'ὑπερείδεσθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently.'),
             ('ὀχείλῃ', 'ὀχεῖσθαι', 'The compact sigma/theta or sigma/chi group remains unresolved independently.')]}
LEADING_FRAGMENTS={(187, 2): 'κὸν', (187, 4): 'νώπων', (187, 10): 'ριν', (187, 15): 'πὸν', (187, 18): 'τρεφούσης', (187, 23): 'δῇ', (187, 29): 'πηδῶσι', (187, 33): 'ρους', (187, 34): 'λον', (187, 38): 'λεμοῦσι', (187, 40): 'τήκοντα', (187, 46): 'ρίων'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    begin,end='παροπτῶν ταύτην','οὗτοι διὰ τὴν τῶν θηρίων'
    for number,target in LINES.items():
        region=[.20,.105,.65,.34]if number<=15 else[.20,.30,.65,.54]if number<=29 else[.20,.485,.65,.73]
        chunks=[(None,target,region,begin,end)]
        if number==35:chunks.insert(0,('1353B','',region,None,None,'marginal-reference','1353R.'))
        if number==41:chunks.insert(0,('73511','',region,None,None,'marginal-reference','735H.'))
        CHUNKS[(187,number)]=chunks
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,187,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        CHUNKS[(187,number)]=[(None,target,[.56,.105,.99,.73],begin,end)]
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
