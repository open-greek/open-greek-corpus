"""Complete direct scan observations for retained historical physical page 184.

All retained lines and both longer passages were inspected directly. Authored
line readings preserve fragments, uncertain endings, and digital alternatives.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T13:57:11.305070Z'
LINES={1: 'ὧν καὶ τὰ Μεμνόνεια {u0} φασί), ποτὲ δὲ Μή-',
 2: 'δων καὶ Περσῶν ἐπικρατησάντων. {u0} δὲ ἔτι καὶ',
 3: 'καθ’ ἡμᾶς ἐν τοῖς χρυσείοις τοῖς ὑπ’ ἐκείνων κατα-',
 4: '{u0} “λατομίδες μὲν χαλκαῖ, διὰ τὸ μήπω τὴν',
 5: 'τοῦ σιδήρου κατ’ ἐκεῖνον τὸν χρόνον {u0} χρείαν,',
 6: 'ὀστᾶ δὲ ἀνθρώπων ἄπιστα τῷ πλήθει, πτωμάτων (ὅπερ',
 7: 'εἰκὸς {u0}) οὐκ ὀλίγων ἐν τοῖς χαύνοις καὶ πλακώ-',
 8: 'δεσιν ὑπονόμοις γενομένων, τηλικαῦτα δὲ ὀρυγμάτων',
 9: 'μεγέθη, καὶ διατείνοντα βάθεσιν ἐπικαρσίοις ἐπ’ αὐ-',
 10: 'τὴν τὴν θάλασσαν.',
 11: 'ὅτι παρὰ τὴν νότιον τῆς Αἰγύπτου κλίσιν τέσσαρά',
 12: 'ἐστι φῦλα τὰ μέγιστα, τὸ μὲν τοῖς ποταμοῖς παρεζευγμέ-',
 13: 'νον, ὃ σπείρει σήσαμον καὶ κέγχρον, τὸ δὲ περὶ τὰς',
 14: 'λίμνας οἰκῶν, ὃ τῷ καλάμῳ καὶ τῆς ὕλης ἅπτεται τῆς',
 15: 'ἁπαλῆς, τὸ δὲ εἰκῇ πλανώμενον, ὃ σαρκὶ καὶ γάλακτι',
 16: 'παραπέμπει τὸν βίον, τὸ δὲ ἐκ τῆς παραλίας ὁρμώ-',
 17: 'μενον, τοὺς ἰχθύας ἀγρεῦον. τοῦτο δὲ τὸ γένος ἔχει μὲν',
 18: 'οὔτε πόλεις οὔτε χώρας ἔτ’ ἄλλης ἐντέχνου κατασκευῆς',
 19: 'ὑπογραφὴν οὐδεμίαν, ἐστὶ δὲ τῶν ὑπολοίπων, ὡς ἔνιοί',
 20: 'φασι, μέγιστον ἀπὸ γὰρ Αὐταίων, οἳ τὸν {u0} μυχὸν',
 21: 'κατοικοῦσιν, ὃν τῇ μεγάλῃ συμβέβηκε {u0} θα-',
 22: 'λάττῃ, μέχρι τῆς Ἰνδικῆς καὶ Κεδρωσίας, ἔτι δὲ Γερ-',
 23: 'μανίας καὶ Περσῶν καὶ τῶν τοῖς εἰρημένοις γένεσιν',
 24: 'ὑποκειμένων νήσων, ἰχθυοφάγοι πάντη κατοικοῦσι,',
 25: 'γυμνοὶ μὲν ὄντες αὐτοί, γυμνὰς δὲ ἔχοντες τὰς γυναῖ-',
 26: 'κας, κοινὴν δὲ τέκνων γένεσιν, ἔτι δὲ ἡδονῆς μὲν καὶ',
 27: 'πόνου φυσικὴν ἔχοντες γνῶσιν, {u0} δὲ καὶ καλῶν',
 28: 'οὐδὲ τὴν ἐλαχίστην εἰσφερόμενοι ἔννοιαν. τούτοις δὲ τὰ',
 29: 'μὲν ἀγχιβαθῆ πάντ’ ἐστὶ πρὸς τὸν βίον ἀλλότρια, παρα-',
 30: 'πλησίως δὲ τὰ παρακείμενα μακραῖς ἠϊόσι· θήραν γὰρ',
 31: 'οὔτε ἰχθύος οὔτ’ ἄλλου γένους ὁμοιοπαθοῦς ἁδροτέραν',
 32: 'παραδίδωσιν ἡ τοιάδε χέρσος. αἱ δὲ οἰκήσεις πᾶσιν',
 33: 'ἐκείνοις τοῖς εἰρημένοις παρὰ τὰς ῥαχίας, αἳ καὶ κοι-',
 34: 'λάδας βαθείας ἔχουσι καὶ φάραγγας ἀνωμάλους καὶ',
 35: 'στενὰς αὐλῶνας καὶ σκολιὰς ἐκτροπάς. ὧν πρὸς τὴν',
 36: 'χρείαν ὑποκειμένων οἰκείως, ἀναθέμενοι πέτρας αὐτο-',
 37: 'παγεῖς ἐπὶ τῆς κοιλίας οἱονεί τινας ἑρκούς. ὅταν οὖν',
 38: 'ἐκ πελάγους ἡ πλημμυρὶς ἐπὶ τὴν χέρσον φέροιτο (ὃ',
 39: 'ποιεῖ δὶς ἑκάστης ἡμέρας, πρὸς ὥραν ἐνάτην τε καὶ'}
PASSAGES={48: ('τρίτην), ἡ μὲν',
      'ἑκάστου βούλησιν καὶ χάριν.',
      [('ἐκ ὀλίγους', 'οὐκ ὀλίγους'),
       ("γίνονθ'", '{u0}'),
       ("καταγωνίζονθ'", '{u1}'),
       ("γίνεθ'", '{u2}'),
       ("λάβωνθ'", '{u3}'),
       ("ὁρῶνθ'", '{u4}'),
       ('ἐκ ὀλίγον', 'οὐκ ὀλίγον'),
       ('τοῦ παλιούρ.', 'τοῦ παλιούρου.'),
       ('πολὺ μᾶλλον {u2}', '{u6}'),
       ("εὐωχοῦνθ'", '{u5}')]),
 49: ('ὅτι πρὸς τὰς αἰφνιδίους',
      'ἰχθύων τῶν ἐλασσόνων',
      [("ἀφαιροῦνθ'", '{u0}'), ("μηχανῶνθ'", '{u1}'), ('ἐλασσόνων', 'ἐλασ-')])}
UNCERTAINTIES={(184, 1): [('συντετελέσθαι',
             'συντετελέσθαι',
             'The unchanged compact sigma/theta group remains unresolved independently.'),
            ('134',
             '',
             'The isolated truncated numeral at the original row end cannot be assigned securely to a source position. '
             'A nearby marginal reference exists, but no exact correspondence is asserted; preserve the original and '
             'exclude this uncertain reference fragment.')],
 (184, 2): [('εὑρίσκον', 'εὑρίσκονται / εὑρίσκονθ’', 'The compact final consonants remain unresolved independently.')],
 (184, 4): [('σκευασθεῖσαι', 'σκευασθεῖσι', 'The compact sigma/theta group remains unresolved independently.')],
 (184, 5): [('ἠγνωρίσθι', 'ἐγνωρίσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (184, 7): [('γίνεται', 'γίνεσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (184, 20): [('ἰχθὸν', 'ἔσχατον', 'The compact sigma/chi group remains unresolved independently.')],
 (184, 21): [('συγκλειδὴ', 'συγκλείεσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (184, 27): [('ἀρχοὺν', 'αἰσχρῶν', 'The compact sigma/chi group remains unresolved independently.')],
 (184, 48): [("γίνοντ'", 'γίνονται / γίνονθ’', 'The compact final consonants remain unresolved independently.'),
             ('καταφωτίζουσι',
              'καταγωνίζονται / καταγωνίζονθ’',
              'The compact final consonants remain unresolved independently.'),
             ('γίνεσθ', 'γίνεται / γίνεθ’', 'The compact final consonants remain unresolved independently.'),
             ('λάβωσι', 'λάβωνται / λάβωνθ’', 'The compact final consonants remain unresolved independently.'),
             ('ὁρῶν', 'ὁρῶνται / ὁρῶνθ’', 'The compact final consonants remain unresolved independently.'),
             ('ἐναχθῶσι', 'εὐωχοῦνται / εὐωχοῦνθ’', 'The compact final consonants remain unresolved independently.'),
             ('πολὺ μᾶλλον γίνεσθ',
              'πολὺ μᾶλλον γίνεται / γίνεθ’',
              'The compact final consonants remain unresolved independently.')],
 (184, 49): [('ἀφαιρῶσι', 'ἀφαιροῦνται / ἀφαιροῦνθ’', 'The compact final consonants remain unresolved independently.'),
             ('μηχανῶν', 'μηχανῶνται / μηχανῶνθ’', 'The compact final consonants remain unresolved independently.')]}
LEADING_FRAGMENTS={(184, 2): 'δων', (184, 4): 'σκευασθεῖσαι', (184, 8): 'δεσιν', (184, 10): 'τὴν', (184, 13): 'νον', (184, 17): 'μενον', (184, 22): 'λάττῃ', (184, 23): 'μανίας', (184, 26): 'κας', (184, 30): 'πλησίως', (184, 34): 'λάδας', (184, 37): 'παγεῖς'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    begin,end='ὧν καὶ τὰ Μεμνόνεια','πρὸς ὥραν ἐνάτην τε καὶ'
    for number,target in LINES.items():
        region=[.025,.105,.49,.34]if number<=15 else[.025,.30,.49,.54]if number<=29 else[.025,.485,.49,.73]
        original=rows[f'helladius_chrestomathia_photius_bekker_v2_0184.{number}']['text']
        chunks=[(None,target,region,begin,end)]
        m=re.search(r' ([0-9]+)$',original)
        if m:
            anchor=original[:m.start()]
            chunks=[(anchor,target,region,begin,end),(None,'{u1}'if number==1 else'',[*region],None,None,'marginal-reference',None)]
        CHUNKS[(184,number)]=chunks
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,184,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[.39,.105,.86,.59]if number==48 else[.39,.57,.86,.73]
        CHUNKS[(184,number)]=[(None,target,region,begin,end)]
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
