"""Complete direct scan review of physical193, all retained words and lines.

Uncertain continuations and differing independent readings are preserved.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:15:51.742671Z'
LINES={5: '{u0} τῷ γένει τὴν δύναμιν. ἐπὶ δὲ τῆς μεσογείας',
 6: 'δρυμοὶ συνεχεῖς ἑστήκασι καὶ μεγάλοι· δένδρα γὰρ ἡλί-',
 7: 'βατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς δὲ καὶ κιννα-',
 8: 'μώμου φοίνικός τε καὶ καλάμου καὶ τῶν ἄλλων {u0}',
 9: '{u0} τῶν τοιούτων, ὥστε εἶναι μηδενὶ λόγῳ τὸ πρᾶγμα δη-',
 10: 'λωτόν, ὃ συμβαίνει τοῖς περὶ τὰς αἰσθήσεις εἰληχόσι',
 11: 'τοῦ γένους τὴν δοκιμασίαν. {u0}',
 12: 'καὶ παλαιὰν ἔχει τῶν ἀρωμάτων ἀπόλαυσιν, οὐδὲ τὴν',
 13: 'ἀπὸ τοῦ γεννῶντος καὶ τρέφοντος ὄγκου διακεχωρισμέ-',
 14: 'νην, ἀλλὰ τὴν ἀνθοῦσαν ἀπὸ τῆς θείας ἀκμῆς καὶ τὴν',
 15: 'ἀπὸ τῶν οἰκείων καὶ φυσικῶν τὸ θαυμαζόμενον ἀπο-',
 16: 'πέμπουσαν· ὥστε πολλοὺς εἰς λήθην ἀφικομένους τῶν',
 17: 'θνητῶν εὐτυχημάτων τῆς ἀμβροσίας ὑπονοεῖν ἀπο-',
 18: 'λαμβάνειν, ὄνομα τοῦ πράγματος ἐπιζητοῦντος οἰκεῖον',
 19: 'τῆς ὑπερβολῆς. περὶ δὲ τὰς δρυμὰς τῶν εὐωδῶν',
 20: 'γένος ἐστὶν ὄφεων ἰδιώτατον πάντων, οἱονεὶ φθονούσης',
 21: 'τοῖς ἁδροῖς ἐπιτεύγμασι τῆς τύχης καὶ παραπλεξάσης',
 22: 'τἀγαθῷ τὸ βλαβερόν, ὅπως μηδεὶς εἰς τέλος ἐξυβρίζων',
 23: 'τιτανῶδες καὶ κατεγνωκὸς τοῦ θείου τὸ φρόνημα λαμ-',
 24: 'βάνῃ τῶν ἀγαθῶν ἐπιτυχόντων, παιδευθῇ δὲ τῇ παρα-',
 25: 'θέσει καὶ μνήμῃ τῶν ἐναντίων. τὸ δὲ γένος τῶν ὄφεων',
 26: 'χρῶμα μὲν ἔχει φοινικοῦν, μῆκος δὲ ὅσον σπιθαμῆς,',
 27: 'δῆγμα δὲ ἀνίατον, ἂν τῆς λαγόνος ἀνώτερον αἱμάξῃ·',
 28: 'τὴν δὲ πληγὴν δίδωσι παλλόμενον εἰς ὕψος. παρ’',
 29: 'αὐτοῖς δὲ τοῖς Σαβαίοις ἡ μὲν ὀσμὴ τῶν εὐωδῶν',
 30: 'ἀκροτάτη, ἡ δὲ χάρις ἐλλιπής· τὸ γὰρ ἐνδελεχὲς ἐκ νη-',
 31: 'πίου κινεῖ μὲν τὴν αἴσθησιν ἧττον, ἀμβλυτέραν δὲ κα-',
 32: 'τασκευάζει, μεταβολῆς τοῖς βίοις οὐχ ὑποκειμένης. οὐ',
 33: 'μὴν ἀλλὰ κἀπειδὰν {u0} τὴν ζωὴν παιδαγωγεῖν',
 34: 'παραπλησίως εὐπαθῆ, διαπνεομένου τοῦ σώματος ὑπ’',
 35: 'ἀκράτου καὶ τμητικῆς δυνάμεως, καὶ τὴν σύμμετρον',
 36: 'πύκνωσιν ἐπὶ πλεῖον ἀγούσης ὥστε ἄγειν εἰς ἔκλυσιν',
 37: '{u0}, τότε δὴ ἀσφάλτῳ παραθυμιῶντες βραχὺ καὶ',
 38: 'τράγου πώγωνα τοῖς τοιούτοις {u0} τὴν ἄγαν',
 39: 'εὐώδη τῆς ἐπιφορᾶς ὑπερβολήν, καὶ τῇ μίξει τοῦ δο-',
 40: 'κοῦντος λυπεῖν τὸ τῆς ἡδονῆς βλαβερόν ὑποκαταστέλ-',
 41: 'λουσιν. οὕτως ἅπαν ἐπίτευγμα μεσότητι μὲν καὶ τάξει',
 42: 'κυβερνώμενον παραπέμπει τὸν βίον, συμμετρίας δὲ καὶ',
 43: 'καιροῦ στερηθὲν οὐκ ἔχει τὴν κτῆσιν ὀνησιφόρον. τὸ',
 44: 'δὲ τῶν Σαβαίων ἄστυ τοῦ παντὸς ἔθνους προσηγορίαν',
 45: 'δηλοῦν, ἐπ’ ὄρους ἐστὶν οὐ μεγάλου, πολὺ κάλλιστον τῶν'}
PASSAGES={1: ('πόῤῥωθεν ἀποστίλβειν.',
     'ἀφ’ Ἡρακλέους ἱστορίαν.',
     [('πόῤῥωθεν', 'ηγμένην πόῤῥωθεν'), ('ὑπερβολὴν πᾶσιν', 'ὑπερβολὴν οὐ πᾶσιν')]),
 2: ('τούτων ἀσυγειτονές',
     'ἐκ τὸν συντηκόμενον',
     [('κέκτηνται', '{u0}'),
      ('γίνονται', '{u1}'),
      ('ἢ πᾶσα', 'οὐ πᾶσα'),
      ('ἐκ τὸν συντηκόμενον', 'οὐ τὸν συντηκόμενον')]),
 3: ('μετ’ ἐπιστήμης καὶ τέχνης',
     'κρῆναι πλείους ἀναβάλλουσιν.',
     [('ἔστι τὸ μὲν ἐλάχιστον', '{u0}'),
      ('παραβάλλεσθαι', '{u1}'),
      ('τε τὰς καρπὸς', 'τε τοὺς καρποὺς'),
      ('τρισάθμιον', 'τριστάθμιον'),
      ('ἀλλάττονται', '{u2}'),
      ('δέκα δύναται μοίρας', '{u3}'),
      ('ἢ πρὸς τὴν φύσιν', 'οὐ πρὸς τὴν φύσιν'),
      ('ἀγχιβαθῆς', 'ἀγχιβαθοῦς')]),
 4: ('Ἐφεξῆς δὲ τὸ τῶν Σαβαίων',
     'πρὸς ἡμᾶς παραπέμπεσθαι',
     [('ἐπισυνάπτει', '{u0}'), ('ἀμαυροῦσθαι', '{u1}'), ('παραπέμπεσθαι', 'παρα-')])}
UNCERTAINTIES={(193, 2): [('μικτὴν)',
             'κέκτηνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('γίνονται',
             'γίνονται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (193, 3): [('ὁ δὲ μὲν ἄλογος',
             'οὗ τὸ μὲν ἐλάχιστον / ὃ τὸ μὲν ἐλάχιστον',
             'The compact relative and adjective remain unresolved independently; the digital opening differs.'),
            ('παραβάλλεσθαι',
             'παραβάλλεσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
            ('αὐλῶντο',
             'ἀλλάττονται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('δέκα δέκα μοίρας',
             'δέκα δύναται μοίρας',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (193, 4): [('ἐπισυνάπτεται',
             'ἐπισυνάπτεται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('ὁἀπασανρθῆς',
             'ἀπαμαυροῦσθαι / ἀμαυροῦσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (193, 5): [('πέρποδῃ',
             'πέμπεσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (193, 8): [('ἀντι-',
             'ἀντι- / ἀνεί-',
             'The compact terminal prefix remains unresolved; preserve the original fragment without completing it '
             'from the digital witness.')],
 (193, 9): [('δ',
             'δῶν',
             'The compact leading continuation of the uncertain preceding printed word remains unresolved; preserve '
             'the original single-letter fragment.')],
 (193, 11): [('ἡ γὰρ τεθραμμένη',
              'οὐ γὰρ τὴν τεθησαυρισμένην',
              'The compact opening and participle remain unresolved independently; the digital witness differs.')],
 (193, 33): [('ἢ δένυσι',
              'οὐ δύνωνται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (193, 37): [('ἄχθην',
              'ἐσχάτην',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (193, 38): [('ἀφαιροῦνται',
              'ἀφαιροῦνται',
              'The compact final consonants remain unresolved independently of the digital witness.')]}
LEADING_FRAGMENTS={(193, 1): 'ηγμένην', (193, 7): 'βατα', (193, 8): 'μώμου', (193, 9): 'δ', (193, 10): 'λωτόν', (193, 14): 'νην', (193, 16): 'πέμπουσαν', (193, 18): 'λαμβάνειν', (193, 24): 'βάνῃ', (193, 25): 'θέσει', (193, 31): 'πίου', (193, 32): 'τασκευάζει', (193, 40): 'κοῦντος', (193, 41): 'λουσιν'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    begin,end='παραπέμπεσθαι τῇ γένει','οὐ μεγάλου, πολὺ κάλλιστον τῶν'
    for number,target in LINES.items():
        region=[.56,.105,.99,.34]if number<=19 else[.56,.30,.99,.54]if number<=33 else[.56,.485,.99,.73]
        original=rows[f'helladius_chrestomathia_photius_bekker_v2_0193.{number}']['text']
        chunks=[(None,target,region,begin,end)]
        m=re.match(r'[0-9]+ ',original)
        if m:chunks.insert(0,(m.group(),' ',region,None,None,'marginal-reference',m.group().strip()))
        if number==27:chunks=[(original[:-6],target,region,begin,end),(None,'',region,None,None,'marginal-reference','746H.')]
        CHUNKS[(193,number)]=chunks
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,193,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        chunks=[(None,target,[.20,.105,.65,.73],begin,end)]
        if number==3:chunks.insert(0,('746 Π. ','',[.20,.28,.65,.38],None,None,'marginal-reference','746H.'))
        if number==4:chunks.insert(0,('1372R ','',[.20,.50,.65,.60],None,None,'marginal-reference','1372R.'))
        CHUNKS[(193,number)]=chunks
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
