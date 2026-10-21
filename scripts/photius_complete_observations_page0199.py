"""Complete direct scan review of physical199, including unchanged words.

Digital expansions absent from the printed extract remain alternatives only.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:30:05.701789Z'
LINES={4: 'ὅτι ἀποδιδοὺς, φησίν, ὁ Πλάτων φιλοσόφου καὶ ἐρω-',
 5: 'τικοῦ διαφοράν, καὶ πῶς ἰσοτίμως {u0}, φι-',
 6: 'λοσοφῆσαι μὲν ἀδόλως λέγει τὸν θεωρίαν ἄνευ πρά-',
 7: 'ξεως πολιτικῆς ἀγαπήσαντα, καὶ πάντα τὰ ἄλλα παρ’',
 8: 'οὐδὲν θέμενον, καὶ ταῖς καθαρτικαῖς ἀρεταῖς ἑαυτὸν',
 9: 'παραδόντα τῇ πρὸς μόνην τὴν ἱερὰν τελείωσιν ἀνα-',
 10: 'γωγῇ, ὡς ἐν Θεαιτήτῳ διέξεισιν. ἀλλ’ ὁ μὲν ἀδόλως',
 11: 'φιλόσοφος κατὰ Πλάτωνα τοιοῦτος· ὁ δὲ ἐρωτικὸς λέ-',
 12: 'γεται παρ’ αὐτῷ, ὃς καὶ παιδεραστῆσαι μετὰ φιλοσοφίας,',
 13: 'ὁ ταῖς πρακτικαῖς ἀρεταῖς διὰ τὸ θεῖον καὶ τὸ αὐτό-',
 14: 'καλον ἐπιτηδεύσας, πολιτικὸν τῷ ὄντι καὶ παιδευτικὸν',
 15: 'τρόπον τῷ βίῳ μεταχειριζόμενος. καὶ τοῦτο ἐν πολιτείᾳ',
 16: 'παραδίδωσι, τοὺς φιλοσόφους λέγων ἄρχοντας ταῖς πό-',
 17: 'λεσιν ἐφεστάναι, ἵνα λήξωσί ποτε τῶν κακῶν, καὶ ὡς',
 18: 'οὐκ ἄν ποτε εὐδαιμονήσειε πόλις, εἰ μὴ αὐτὴν δια-',
 19: 'γράψειαν οἱ τῷ θείῳ παραδείγματι χρώμενοι. τίς δ’',
 20: 'ὁ τρόπος τῆς διαγραφῆς; ὅτι λαβόντες, ὥσπερ πί-',
 21: 'νακα, πόλιν τε καὶ ἤθη ἀνθρώπων πρῶτον μὲν κα-',
 22: 'θαρὰν ποιήσειαν, καὶ μετὰ τοῦτο ὑπογράψαιντο ἂν τὸ',
 23: 'σχῆμα τῆς πολιτείας, ἔπειτα, οἶμαι, ἀπεργαζόμενοι αὐ-',
 24: 'τὴν πυκνὰ ἂν ἑκατέρωσε ἀποβλέποιεν, πρός τε τὸ φύ-',
 25: 'σει δίκαιον καὶ καλὸν καὶ σῶφρον καὶ πάντα τὰ τοιαῦτα,',
 26: 'καὶ πρὸς ἐκεῖνο αὖ ὃ τοῖς ἀνθρώποις ἐμποιεῖ, ὡς καὶ',
 27: 'Ὅμηρος ἔφη, τὸ θεοειδές τε καὶ θεοείκελον, καὶ τὸ',
 28: 'μὲν ἐξαλείφοιεν, τὸ δὲ πάλιν ἐγγράφοιεν ἕως ὅ τι μά-',
 29: 'λιστα τὰ ἀνθρώπινα ἤθη θεοφιλῆ ποιήσειαν. τοιοῦτός',
 30: 'ἐστι πολιτειῶν ζωγράφος ὁ παιδεραστῶν μετὰ φιλοσο-',
 31: 'φίας, τουτέστιν ὁ μετὰ θεωρητικοῦ νοῦ πολιτευόμενος.',
 32: 'παῖδα γὰρ εἶναι τὴν αἴσθησιν καὶ τὸ ἐν αἰσθήσει καλόν,',
 33: 'ὡς πρὸς πρεσβύτην καὶ παιδαγωγὸν τῆς αἰσθήσεως τὸν',
 34: 'νοῦν. διὸ τὸν νῷ μόνῳ χρώμενον ἐν ὑπεροψίᾳ τῶν τῇδε',
 35: 'σώφρονι ἀδόλως φιλοσοφεῖν {u0}, τουτέστιν ἀπε-',
 36: 'ριεργάστως καὶ ἀΰλως καὶ ἀγοητεύτως· γοητεύειν γάρ',
 37: 'πως ἡ αἴσθησις ἐθέλει συνοῦσα, καὶ ἀναπείθειν τὸν',
 38: 'λογισμὸν τῶν ἐνύλων τι ἀγαθὸν ὑπολαμβάνειν οἰκεῖον.',
 39: 'τὸν δὲ τὴν αἴσθησιν κατὰ νοῦν διατάττοντα παιδερα-',
 40: 'στεῖν λέγει μετὰ φιλοσοφίας, φυλακτήριον ἔχοντα μέ-',
 41: 'γιστον τοῦ ἀνεξαπατήτως κατὰ τὴν αἴσθησιν ἐνεργεῖν',
 42: 'τὸν θεωρητικὸν νοῦν, ᾧ εἰκόνας ἰδίᾳ καὶ δημοσίᾳ γρά-',
 43: 'φειν ἐρᾷ, τὰ τῶν ἀνθρώπων ἐπανορθούμενος ἤθη, ἕως'}
PASSAGES={1: ('δὲ νῦν ἀντὶ',
     'τόπον καλέσαντες.',
     [('δὲ νῦν', 'που δὲ νῦν'),
      ('ὁσίαν', 'οὐσίαν'),
      ('καλέσαντες', 'καλοῦντες')]),
 2: ('ὅτι ἐν τοῖς νόμοις',
     'προνοητικῆς εἱμαρμένης.',
     [('ἐνδείκνυται', '{u0}'),
      ('ἀνυμαρτήτοις', 'ἀναμαρτήτοις'),
      ('προσχρωμένης', '{u1}'),
      ('ἡ γὰρ κατὰ', 'οὐ γὰρ κατὰ'),
      ('τύχῃ τῇ περὶ', 'τύχην τῇ περὶ'),
      ('γίνεται', '{u2}'),
      ('ἀπευθυνόσης', 'ἀπευθυνούσης')])}
UNCERTAINTIES={(199, 2): [('ἐνδεικνύῃ',
             'ἐνδείκνυται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.'),
            ('προχωρουμένης',
             'προσχρωμένης',
             'The compact sigma/chi group remains unresolved independently of '
             'the digital witness.'),
            ('γίνεται',
             'γίνεται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.')],
 (199, 5): [('ἀνάγκη λέγειν',
             'ἀνάγεσθαι λέγονται',
             'The compact sigma/theta and final consonants remain unresolved '
             'independently of the digital witness.')],
 (199, 35): [('ἀποφαίνει',
              'ἀποφαίνεται',
              'The compact final consonants remain unresolved independently of '
              'the digital witness.')]}
LEADING_FRAGMENTS={(199, 1): 'που', (199, 5): 'τικοῦ', (199, 6): 'λοσοφῆσαι', (199, 7): 'ξεως', (199, 10): 'γωγῇ', (199, 12): 'γεται', (199, 14): 'καλον', (199, 17): 'λεσιν', (199, 19): 'γράψειαν', (199, 21): 'νακα', (199, 22): 'θαρὰν', (199, 24): 'τὴν', (199, 25): 'σει', (199, 29): 'λιστα', (199, 31): 'φίας', (199, 36): 'ριεργάστως', (199, 40): 'στεῖν', (199, 41): 'γιστον', (199, 43): 'φειν'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,target in LINES.items():
        region=[.56,.105,.99,.34]if number<=17 else[.56,.30,.99,.54]if number<=30 else[.56,.485,.99,.73]
        CHUNKS[(199,number)]=[(None,target,region,'ὅτι ἀποδιδός, φησίν,','ἤθη, ἕως')]
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,199,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        CHUNKS[(199,number)]=[(None,target,[.20,.105,.65,.73],begin,end)]
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
