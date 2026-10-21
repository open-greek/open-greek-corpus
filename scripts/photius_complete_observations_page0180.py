"""Complete direct scan observations for retained historical physical page 180.

All words and unchanged lines were visually inspected. Authored line transcriptions
retain boundary fragments, uncertainty, and independent bounded digital variants.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T13:46:56.207628Z'
LINES={5: 'κόλακος εἰρωνείαν καιρῷ προσομιλοῦσαν. “οἶδα γάρ,',
 6: 'πρεσβύτερος ὢν καὶ πολλῶν ἔμπειρος γεγονὼς πραγμά-',
 7: 'των, διὰ τοὺς θωπεύειν ἐπιβεβλημένους τοὺς ἐν ταῖς',
 8: 'ὑπεροχαῖς καὶ τὰς μεγίστας βασιλείας ἄρδην ἀνῃρημέ-',
 9: 'νας, τὴν Κασάνδρου, τὴν Λυσιμάχου, τὴν Ἀλεξάνδρου',
 10: 'τηλικαύτην οὖσαν, τὴν Μήδων, τὴν Σύρων, τὴν Περ-',
 11: 'σῶν, ὥστε μηδὲ σπέρμα καταλελεῖφθαι τοῦ γένους. οὐκ',
 12: 'ἀλόγως· νέῳ γὰρ πολλὰ μὲν ἀγνοοῦντος διὰ τὴν ἡλικίαν,',
 13: 'εὐλογουμένῳ δὲ ἐπὶ τοῖς ἁμαρτήμασιν οὐδὲν σφαλερώ-',
 14: 'τερον οὐδὲ ἐπικινδυνότερον. ὁ γοῦν Ἀλέξανδρος, ἀήτ-',
 15: 'τητος ὢν ἐν τοῖς ὅπλοις, {u0} ἦν ἐν ταῖς ὁμι-',
 16: 'λίαις· ἡλίσκετο γὰρ ὑπὸ τῶν ἐπαίνων. καὶ Ζεὺς καλού-',
 17: 'μενος οὐ {u0} ἐνόμιζεν ἀλλὰ {u1}, τῶν μὲν',
 18: 'ἀδυνάτων ἐπιθυμῶν, τῆς δὲ φύσεως ἐπιλελησμένος.',
 19: 'ὅταν ὁ δημαγωγὸς τοῖς πολλοῖς {u0}, μὴ τὴν',
 20: 'τῷ φίλῳ τάξιν {u0} ἀλλὰ τὴν τοῦ κόλακος, ἡ',
 21: 'τῶν ὄχλων ὁρμὴ βεβαιωτὴν λαβοῦσα τῆς ἁμαρτίας τὸν',
 22: 'σύμβουλον ἀνέτρεψε τὴν πόλιν. ἐνσκήπτει γὰρ ὁ μῶ-',
 23: 'μος οὐ κατὰ τῶν ὑπαιτίων μόνον, ἀλλὰ καὶ οἷς ἂν ὁ',
 24: 'φθόνος αὐτῷ τὴν ἔφοδον προοδοποιήσαιτο. ἢ κρατεῖ',
 25: 'γὰρ ὁ μῶμος οὐ τῶν ὑπαιτίων μόνον, ἀλλ’ {u0} καὶ',
 26: 'τῶν ἐπικρατεστέρων αἰτίας, ἐπειδὰν ὁ φθόνος πικρὸν',
 27: 'τὸ βέλος ἀφεὶς προκατειργάσατο τὸν οὐκ ἄξιον τοῦτο',
 28: '{u0}.',
 29: 'χρῶνται δὲ ἐπὶ τῶν κινδύνων τῶν πολεμικῶν Αἰθίο-',
 30: 'πες τοῖς μὲν τόξοις μεγάλοις, βραχέσι δὲ τοῖς ὀϊστοῖς·',
 31: 'ἐπὶ δὲ τῆς ἄκρας τοῦ καλάμου κερκίδος ἀντὶ τοῦ σιδήρου',
 32: 'παραμήκης τῷ τύπῳ λίθος {u0}, νεύροις ἐσφί-',
 33: 'γμένος, ὀξὺς μὲν ὑπερβολῇ, φαρμάκοις δὲ θανασίμοις',
 34: 'βεβαμμένος.',
 35: 'ὅτι Πτολεμαῖος, φησίν, εἰς τὸν κατὰ Αἰθιόπων πό-',
 36: 'λεμον ἀπὸ τῆς Ἑλλάδος πεντακοσίας συνέλεξεν ἱππεῖς,',
 37: 'ὧν τοῖς προκινδυνεύειν μέλλουσι καὶ καθηγουμένοις, τὸ',
 38: 'πλῆθος οὖσιν ἑκατόν, ὁπλισμῷ περιέθηκε τρόπον· στολὰς',
 39: 'γὰρ αὐτοῖς τε καὶ τοῖς ἵπποις ἀνέδωκε πηλητάς, ἃς οἱ',
 40: 'κατὰ τὴν χώραν ἐκείνην {u0} κάσας, ὥστε',
 41: 'πᾶν κρύπτειν τὸ σῶμα πλὴν τῶν ὀφθαλμῶν.',
 42: 'Ἐκ τῆς ε’ Ἀγαθαρχίδου ἱστορίας',
 43: 'τῆς περὶ τὴν ἐρυθρὰν θάλασσαν.',
 44: 'ὅτι πολλοί, φησί, καὶ τῶν πολιτικῶν ἀνδρῶν καὶ',
 45: 'τῶν ποίημα γεγραφότων διηπορήκασι πῶς τὰς ὑπερ-',
 46: 'βαλλούσας ἐνίοις ἀκληρίας τῶν ἐκτὸς τῶν κινδύνων κεί-',
 47: 'μενον πρεπόντως ἐξαγγελτέον· ὧν ὁ τρόπος οὐ λίαν'}
PASSAGES={1: ('λύπης ἀλλὰ',
     'ἔνια πυρίωμεν.',
     [('ἀλόγων', 'λόγων'), ('αἱρώμεθα', 'αἱρούμεθα'), ('Θεῶν', 'θεῶν'), ('πυρίωμεν', 'παρίωμεν')]),
 2: ('ἰδιώτῃ μὲν', 'τῶν ἀσθενεστέρων.', [('ὁσίαν', 'οὐσίαν'), ('ἀσθενεστέρων', '{u0}')]),
 3: ('ὅτι φησίν, Ἐκ πολλοῦ',
     'καταπλήξονται τοὺς',
     [('ἀσχολίαν', '{u0}'),
      ('διαψεύδεται', '{u1}'),
      ('τὰς αὑτῷ φιλὰς βουλῆς κοινωνὸς', 'τοὺς αὐτῷ φίλους βουλῆς κοινωνοὺς'),
      ('ἐπώσοντος δεῖται', '{u2}'),
      ('ἄβελος', 'ἄβουλος'),
      ('τὸ δοκὲν', 'τὸ δοκοῦν'),
      ('τὸ ταῦτα κεκτημένον', '{u3}'),
      ('ὠφελεῖσθαι', '{u4}'),
      ('τί ἐν ἀμηχάνῳ', 'τί ἂν ἀμήχανον'),
      ('εὐλαβεῖσθαι', '{u5}')]),
 4: ('Ἕλληνας οἱ Αἰθίοπες.',
     'χρόνῳ στοχαζομένην, ἐκ',
     [('ἐκ ὑπερβαίνει', 'οὐχ ὑπερβαίνει'),
      ('ἐκ ὄψει', 'οὐκ ὄψει'),
      ('ἐναντιοῦσθαι', '{u0}'),
      ('περιαιρούμενος τὴν', 'περιαιρούμενος οὐ τὴν'),
      ('χρόνῳ στοχαζομένην, ἐκ', 'χρόνῳ στοχαζομένην, οὐ')])}
UNCERTAINTIES={(180, 2): [('ἀδυνεστέρων', 'ἀσθενεστέρων', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 3): [('ἀχολίαν', 'ἀσχολίαν', 'The compact sigma/chi group remains unresolved independently.'),
            ('διαφθείδου', 'διαψεύδεται', 'The compact final consonants remain unresolved independently.'),
            ('ἐπώσους δεῖ', 'ἐπώσοντος δεῖται', 'The compact verb ending remains unresolved independently.'),
            ('τὰ ταῦτα κεκτημένα',
             'τὸν ταῦτα κεκτημένον / τὸ ταῦτα κεκτημένον',
             'The compact article and participle endings remain unresolved independently.'),
            ('ἀφελῆθι', 'ὠφελεῖσθαι', 'The compact sigma/theta group remains unresolved independently.'),
            ('εὐλαβεῖν', 'εὐλαβεῖσθαι', 'The compact final sigma/theta group remains unresolved independently.')],
 (180, 4): [('ἐναν-τιώθι', 'ἐναντιοῦσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 15): [('ἀθενέστατος', 'ἀσθενέστατος', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 17): [('χιτῶνιζόμενος', 'χλευάζεσθαι', 'The compact sigma/theta group remains unresolved independently.'),
             ('τιμῶν', 'τιμᾶσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 19): [('διαλέγηται',
              'διαλέγηται / διαλέγησθαι',
              'The compact unchanged ending remains unresolved independently.')],
 (180, 20): [('ἐπισχησάμενος', 'ὑποσχησάμενος', 'The compact sigma/chi group remains unresolved independently.')],
 (180, 25): [('ἐφ’ ὅτι', 'ἔσθ’ ὅτε', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 28): [('πεῖσαι', 'πείσεσθαι / πεῖσθαι', 'The compact sigma/theta group remains unresolved independently.')],
 (180, 32): [('ἀνεξέριπτε', 'ἀνεξήρικται', 'The compact final consonants remain unresolved independently.')],
 (180, 40): [('προσαγορεύεσθαι',
              'προσαγορεύεσθαι / προσαγορεύεται',
              'The unchanged compact sigma/theta group remains unresolved independently.')]}
LEADING_FRAGMENTS={(180, 7): 'των', (180, 9): 'νας', (180, 11): 'σῶν', (180, 14): 'τερον', (180, 15): 'τητος', (180, 16): 'λίαις', (180, 17): 'μενος', (180, 23): 'μος', (180, 30): 'πες', (180, 33): 'γμένος', (180, 36): 'λεμον', (180, 46): 'βαλλούσας', (180, 47): 'μενον'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,180,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[.025,.105,.49,.30]if number<=2 else[.025,.27,.49,.58]if number==3 else[.025,.49,.49,.73]
        chunks=[(None,target,region,begin,end)]
        if number==4:chunks.insert(0,('795 Η.','',[.025,.49,.49,.60],None,None,'marginal-reference','725H.'))
        CHUNKS[(180,number)]=chunks
    begin,end='κόλακος εἰρωνείαν','ὧν ὁ τρόπος οὐ λίαν'
    for number,target in LINES.items():
        region=[.39,.105,.86,.34]if number<=20 else[.39,.30,.86,.54]if number<=35 else[.39,.485,.86,.73]
        item=(None,target,region,begin,end)
        if number in(42,43):item=(*item,'unclassified-heading')
        chunks=[item]
        if number==5:chunks.insert(0,('13398. ','',[.025,.66,.49,.73],None,None,'marginal-reference','1333R.'))
        original=rows[f'helladius_chrestomathia_photius_bekker_v2_0180.{number}']['text']
        m=re.match(r'^[0-9]+',original)
        if m and number!=5:chunks.insert(0,(m.group(),'',[*region],None,None,'marginal-reference',str((number-10)//5*5+5)))
        CHUNKS[(180,number)]=chunks
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
