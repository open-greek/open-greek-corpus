"""Complete direct scan review of physical195, including the source transition.

Every retained word was read; the centered identification heading remains unclassified.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:20:34.576246Z'
LINES={2: 'τὸ φῶς ἐπί τε τὴν γῆν καὶ τὸ πέλαγος βάλλει ἕως',
 3: 'ἔκτοπον καὶ πυρῶδες, ὥστε ἀμφοῖν {u0} παμμε-',
 4: 'γέθεις τὰς ὑπερβολάς. [ἕκτον] εἰς δὲ τὴν ἑσπέραν ἐναν-',
 5: 'τίον τὸ περὶ τὸν ἥλιον πάθος φασὶν {u0}· ὑποδεί-',
 6: 'ξαντα γὰρ ὅτι δέδυκε κατὰ τῆς γῆς, οὐκ ἐλάττω χρόνον',
 7: 'ὡρῶν τριῶν μετὰ ταῦτα φωτίζειν, ὃν καὶ νομίζουσι παρ’',
 8: 'αὐτοῖς καιρὸν εἶναι τῆς ἡμέρας τὸν ἥδιστον.',
 9: 'ὅτι εἰπὼν περὶ ἀμπώτεων ὁ συγγραφεὺς διαφόρους',
 10: 'αἰτίας, καὶ πάσας ὡς οὐδὲν ἐχούσας ἀληθὲς ἀποδοκι-',
 11: 'μάσας, ἐπάγει Ὅτι δὲ ταῦτα πάντα λαλιὰν μὲν ἔχει',
 12: 'σιγᾶν {u0}, πράγματος δὲ οὐδενὸς {u1}',
 13: 'βοήθειαν δυναμένου τοῖς εἰρημένοις {u0}, εὐχερές',
 14: 'ἐστι μαθεῖν. εἶτα {u0} καὶ ἕτερα τῆς αὐτῆς ἐννοίας',
 15: 'ἐχόμενα, πάλιν ἐπιφέρει Διὸ περὶ μὲν ἀμπώτιδος καὶ',
 16: 'σεισμοῦ καὶ πνευμάτων καὶ κεραυνῶν καὶ τῶν τοιούτων',
 17: 'ἁπάντων τὰς μὲν αἰτίας, δι’ ἃς {u0}, παραχωροῦμεν',
 18: 'τοῖς ἑτοιμότερον ἔχουσι πρὸς εὐκολίαν ἡμῶν· τὰ δὲ',
 19: 'πάθη τὰ γεννῶντα τὰς προφανεῖς συμφορὰς δεδηλώ-',
 20: 'καμεν, μαθόντες παρὰ τῶν εἰδότων. εὑρίσκειν δὲ πιθα-',
 21: 'νότερα τούτων εἰς μὲν ὑπόθεσιν παραδόξων φιλοτι-',
 22: 'μούμεθα, ἱστορίαν δὲ ἀπαγγέλλοντες ἀληθινὴν οὐκ ἂν',
 23: 'ὑπομείναιμεν.',
 24: 'ὅτι ἐν τῷ προειρημένῳ πόρῳ, φησί, περὶ τὰς ἐλαίας',
 25: 'τοιοῦτόν τι ξένον συμβαίνει. πλημμυρίδος ὑπαρχούσης',
 26: 'πᾶσαι {u0}, τῆς δ’ ἀμπώτεως γινομένης ἐν τῇ',
 27: 'θαλάσσῃ πάντα τὸν χρόνον θάλλουσιν. ἔστι δέ τι φυό-',
 28: 'μενον αὐτόθι κατὰ βάθος ἐν ταῖς ῥαχίαις, μελαίνῃ',
 29: '{u0} παραπλήσιον, ὅ φασιν οἱ ἐκεῖσε κατοικοῦντες',
 30: 'Ἴσιδος εἶναι τρίχωμα, μυθώδει πλάσματι πίστιν εὐήθη',
 31: 'περιτιθέναι ζητοῦντες. συμβέβηκε δ’ αὐτῷ τυπτομένῳ',
 32: 'μὲν ὑπὸ τοῦ κύματος {u0} πολλαχῶς, ἁπαλῆς οὔσης',
 33: 'τῆς ὅλης περιοχῆς καὶ τοῖς ἄλλοις παραπλησίας φυ-',
 34: 'τοῖς· ἂν δέ τις ἀποκόψας εἰς τὸν ὕπαιθρον ἀναφέρῃ',
 35: 'τόπον, σιδήρου παραχρῆμα {u0} τὸ διῃρημένον',
 36: 'σκληρότερον.',
 37: 'ὅτι καὶ ἄλλοι μὲν πολλοί, φησίν, ἰχθύες περὶ τοὺς',
 38: 'προειρημένους {u0} τόπους, παρηλλαγμένην ἔχοντες',
 39: 'τὴν φύσιν, {u0} δέ τις ἰχθὺς ὑπερβαλλόντως μέλας,',
 40: 'ἀνδρὸς ἔχων μέγεθος, ὃν καλοῦσιν αἰθίοπα διὰ τὸ καὶ',
 41: 'τοῦ προσώπου σιμὸν ἔχειν τὸν τύπον. τοῦτον κατ’ ἀρχὰς',
 42: 'μὲν οἱ θηρεύσαντες διὰ τὴν ὁμοιότητα οὔτε πωλεῖν'}
PASSAGES={48: ('ἠξίουν οὔτε καταναλίσκειν',
      'οὐδὲν ἡμαρτάνεσιν.',
      [('τῷ δὲ χρόνῳ', 'τῷ δὲ χρόνῳ'), ('ἡμαρτάνεσιν', 'ἁμαρτάνουσιν')]),
 49: ('τὰ μὲν οὖν ὑπὲρ τῶν ἐθνῶν',
      'οὐκ ἀφέξεται.',
      [('ἱσορήκαμεν', 'ἱστορήκαμεν'),
       ('ὕσερον', 'ὕστερον'),
       ('ἅτε', '{u0}'),
       ('δυναμένης', '{u1}'),
       ('ἀποσάσεις', 'ἀποστάσεις'),
       ('ἱσορίας', 'ἱστορίας')]),
 50: ('ὅτι Ἀδριανὸς',
      'φάσματα ἀποσημαίνουσιν.',
      [('Ἀδριανὸς', 'Ἀῤῥιανὸς'), ('συσάσεως', 'συστάσεως'), ('πειρᾶται', '{u0}'), ('ἀποσημαίνουσιν', '{u1}')]),
 52: ('καὶ τί, φησί,',
      "ἀλλ' οὐδὲ ὁ Θεὸς",
      [('ὑποσῆσαι', 'ὑποστῆσαι'),
       ('δύνασθαι κόσμον', '{u1} κόσμον'),
       ('ὑποσάσῃ', 'ὑποστάσῃ'),
       ('δύνασθαι, πάντων', '{u2}, πάντων'),
       ('ὑπέσησε', 'ὑπέστησε'),
       ('πειρᾶται', '{u3}'),
       ('ὑφεσὸς', 'ὑφεστὸς'),
       ('προσλήψεται', '{u4}'),
       ('ὥσε ἐκ ἀγαθὸν', 'ὥστε οὐκ ἀγαθὸν'),
       ('κοσμεῖσθαι', '{u5}')])}
UNCERTAINTIES={(195, 3): [('νομίζω',
             'νομίζεσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 5): [('ὁρᾶλ᾽',
             'ὁρᾶσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 12): [('αἰχνομένην',
              'αἰσχυνομένην',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
             ('ἀντεληφ[',
              'ἀντείληπται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 13): [('παραχεῖν',
              'παρασχεῖν',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 14): [('προαὐξὼν',
              'προσθεὶς',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 17): [('γίνε[τ]',
              'γίνεται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 26): [('καλύπτον[τ]',
              'καλύπτονται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 29): [('χοίνῃ',
              'σχοίνῳ',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 32): [('κάμπτης',
              'κάμπτεσθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (195, 35): [('γίνεται',
              'γίνεται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 38): [('τίκτον[τ]',
              'τίκτονται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 39): [('γίνε[τ]',
              'γίνεται',
              'The compact final consonants remain unresolved independently of the digital witness.')],
 (195, 49): [('ὅτι', 'ἅτε / ὅτε', 'The compact connective remains unresolved independently.'),
             ('δυτοιούμενος',
              'δυναμένης / οὐ δυναμένης',
              'The compact participle and possible negative remain unresolved independently.')],
 (195, 50): [('πειρῶθ’',
              'πειρᾶται',
              'The compact final consonants remain unresolved independently of the digital witness.'),
             ('ἀποστέλλουσιν',
              'ἀποσημαίνουσιν / ὑποσημαίνουσιν',
              'The compact prefix differs from the independent witness and remains unresolved.')],
 (195, 52): [('Ἀνεγνωσθη',
              'Ἀνεγνώσθη / Ἀνεγνώθη',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
             ('δύναμις',
              'δύνασθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
             ('δύνα-253 ἥ',
              'δύνασθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
             ('πειρῶ',
              'πειρᾶται',
              'The compact final consonants remain unresolved independently of the digital witness.'),
             ('προσέλαβε',
              'προσλήψεται',
              'The compact final consonants remain unresolved independently of the digital witness.'),
             ('κοσμεῖσθαι',
              'κοσμεῖσθαι',
              'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')]}
LEADING_FRAGMENTS={(195, 4): 'γέθεις', (195, 5): 'τίον', (195, 6): 'ξαντα', (195, 11): 'μάσας', (195, 20): 'καμεν', (195, 22): 'μούμεθα', (195, 28): 'μενον', (195, 34): 'τοῖς'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    begin,end='τὸ φῶς ἐπί τε','οὔτε πωλεῖν'
    for number,target in LINES.items():
        region=[.20,.105,.65,.34]if number<=16 else[.20,.30,.65,.54]if number<=30 else[.20,.485,.65,.73]
        original=rows[f'helladius_chrestomathia_photius_bekker_v2_0195.{number}']['text']
        chunks=[(None,target,region,begin,end)]
        m=re.search(r' [0-9]+$',original)
        if m:chunks=[(original[:m.start()],target,region,begin,end),(None,'',region,None,None,'marginal-reference',m.group().strip())]
        if number==3:chunks.insert(0,('748 ','',region,None,None,'marginal-reference','748H.'))
        if number==27:chunks.insert(0,('1377 Ἄ. ','',region,None,None,'marginal-reference','1377R.'))
        CHUNKS[(195,number)]=chunks
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,195,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        chunks=[(None,target,[.56,.105,.99,.73],begin,end)]
        if number==52:chunks.insert(0,('προνοίας.','{u0} ΙΕΡΟΚΛΕΟΥΣ ὁ περὶ προνοίας.',[.56,.30,.99,.43],'Ἀνεγνώθη ΙΕΡΟΚΛΕΟΥΣ','ὁ περὶ προνοίας.','unclassified-heading'))
        CHUNKS[(195,number)]=chunks
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
