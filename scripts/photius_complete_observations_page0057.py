"""Complete direct scan review of physical 57.

Every retained word inspected; unresolved glyphs and digital alternatives preserved.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:44:07.710111Z'
PASSAGES={}
UNCERTAINTIES={(57, 16): [('ὠχρον',
             'ὄσχον',
             'The compact sigma/chi group and noun ending remain unresolved '
             'independently of the digital alternative.')],
 (57, 31): [('γενέσθαι',
             'γενέσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')],
 (57, 44): [('Ἀνεγνώσθη',
             'Ἀνεγνώσθη',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')],
 (57, 71): [('ἐπιλαμβύνεται',
             'ἐπιλαμβάνεται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.')]}
LEADING_FRAGMENTS={(57, 2): 'μάτων',
 (57, 4): 'μενος',
 (57, 15): 'ναῖκας',
 (57, 18): 'ξαι',
 (57, 23): 'τραφημένοις',
 (57, 24): 'ταις',
 (57, 25): 'νυσιακοῦ',
 (57, 26): 'μενος',
 (57, 34): 'μενά',
 (57, 35): 'μενοι',
 (57, 40): 'στομαθίας',
 (57, 45): 'ΠΟΝΟΥ',
 (57, 48): 'νον',
 (57, 49): 'φωνον',
 (57, 50): 'σέως',
 (57, 53): 'γονίας',
 (57, 66): 'ναντίον',
 (57, 70): 'λειον',
 (57, 81): 'νου'}
LINES={1: 'ἀσεβήσωσιν, νικήσουσιν. ἔδοξεν οὖν αὐτοῖς ἀσεβη-',
 2: 'μάτων εἶναι μέγιστον τὸ τὴν χρησμῳδήσασαν αὐτοῖς',
 3: 'τὸν χρησμὸν ἀνελεῖν· καὶ ἀνεῖλον. αἱ δὲ περὶ τὸ τέ-',
 4: 'μενος συνιέρειαι δίκην λαβεῖν ἀπῄτουν τοῦ φόνου τὰς',
 5: 'Θηβαίας. Θηβαῖοι δὲ οὐκ ἐπιτρέπουσι γυναιξὶ μόναις',
 6: 'τὴν περὶ αὐτῶν δίκην· κοινῆς δὲ κρίσεως ἀνδρῶν καὶ',
 7: 'γυναικῶν γεγενημένης, καὶ τῶν ἀνδρῶν λευκὰς αὐτοῖς',
 8: 'ἐπενεγκόντων ψήφους, ἀπέφυγον οἱ Θηβαῖοι. ὕστερον δὲ',
 9: 'ἐπιγνόντες αὐτοῖς τὸ ὑπὸ τοῦ χρησμοῦ προστασσόμενον,',
 10: 'βαστάσαντες τῶν κατὰ τὴν Βοιωτίαν ἱερῶν τριπόδων',
 11: 'ἕνα, καὶ κατακαλύψαντες ὡς ἱερόσυλοι, ἀνέπεμψαν εἰς',
 12: 'Δωδώνην. εὐπραγήσαντες δὲ ἐξ ἐκείνου τὰ λοιπὰ τὴν',
 13: 'πρᾶξιν ἑορτὴν ἐποίουν. ὠσχοφορικὰ δὲ μέλη παρ’',
 14: 'Ἀθηναίοις ᾔδετο· τῷ χορῷ δὲ δύο νεανίαι, κατὰ γυ-',
 15: 'ναῖκας ἐστολισμένοι, κλῆμα ἀμπέλου κομίζοντες μεστὸν',
 16: 'εὐθαλῶν βοτρύων (ἐκάλουν δὲ αὐτὸ {u0}, ἀφ’ οὗ καὶ',
 17: 'τοῖς μέλεσιν ἡ ἐπωνυμία) τῆς ἑορτῆς καθηγοῦντο. ἄρ-',
 18: 'ξαι δέ φασι Θησέα πρῶτον τοῦ ἔργου· ἐπεὶ γὰρ ἑκουσίως',
 19: 'ὑποστὰς τὸν εἰς Κρήτην πλοῦν ἀπήλλαξε τὴν πατρίδα',
 20: 'τῆς κατὰ τὸν δασμὸν συμφορᾶς, χαριστήρια ἀποδιδοὺς',
 21: 'Ἀθηνᾷ καὶ Διονύσῳ, οἳ αὐτῷ κατὰ τὴν νῆσον τὴν',
 22: 'Δίαν ἐπεφάνησαν, ἔπραττε τοῦτο, δυσὶ νεανίαις ἐσκια-',
 23: 'τραφημένοις χρησάμενος πρὸς τὴν ἱερουργίαν ὑπηρέ-',
 24: 'ταις. ἦν δὲ τοῖς Ἀθηναίοις ἡ παραπομπὴ ἐκ τοῦ Διο-',
 25: 'νυσιακοῦ ἱεροῦ εἰς τὸ τῆς Ἀθηνᾶς τῆς Σκιράδος τέ-',
 26: 'μενος. εἵπετο δὲ τοῖς νεανίαις ὁ χορός, καὶ ᾔδε τὰ',
 27: 'μέλη. ἐξ ἑκάστης δὲ φυλῆς ἔφηβοι διημιλλῶντο πρὸς',
 28: 'ἀλλήλους δρόμῳ· καὶ τούτων ὁ πρότερος ἐγεύετο ἐκ τῆς',
 29: 'πενταπλῆς λεγομένης φιάλης, ἣ συνεκίρνατο ἐλαίῳ καὶ',
 30: 'οἴνῳ καὶ μέλιτι καὶ τυρῷ καὶ ἀλφίτοις. εὐκτικὰ δὲ',
 31: 'μέλη ἐγράφετο τοῖς αἰτουμένοις τι παρὰ θεοῦ {u0}.',
 32: 'πραγματικὰ δέ, ἃ τινων περιεῖχε πράξεις. ἐμπορικὰ',
 33: 'δέ, ὅσα κατὰ τὰς ἀποδημίας καὶ ἐμπορείας ἐπιδεικνύ-',
 34: 'μενά τισιν ἐγράφη. καὶ ἀποστολικὰ δέ, ὅσα διαπεμπό-',
 35: 'μενοι πρός τινας ἐποίουν. τὰ δὲ γνωμολογικὰ δῆλον',
 36: 'ὅτι παραίνεσιν ἠθῶν ἔχει, καὶ τὰ γεωργικὰ δὲ χώρας',
 37: 'καὶ φυτῶν καιροὺς καὶ ἐπιμελείας. καὶ τὰ ἐπισταλτικὰ',
 38: 'δέ, ὅσα κατ’ ἐντολὰς πρός τινας ποιοῦντες διέπεμπον.',
 39: 'οἱ μὲν δύο λόγοι τῆς Πρόκλου γραμματικῆς χρη-',
 40: 'στομαθίας ἐν τούτοις.',
 46: 'ὅτι τὸ σύγγραμμα Σεργίῳ τῷ Κωνσταντινουπόλεως',
 47: 'προσφωνεῖ, ἐκείνου προτροπῇ τοῦτον ὑπελθεῖν τὸν πό-',
 48: 'νον προοιμιαζόμενος. τὸν δὲ σκοπὸν εἶναί φησι σύμ-',
 49: 'φωνον δεῖξαι τοῖς φαινομένοις τὴν τοῦ θεσπεσίου Μω-',
 50: 'σέως κοσμογένειαν.',
 51: 'ὅτι σκοπὸς ἦν τῷ Μωσεῖ οὔτε φυσιολογῆσαι οὔτε',
 52: 'ἀστρονομῆσαι, ἀλλ’ εἰς θεογνωσίαν καὶ διὰ τῆς κοσμο-',
 53: 'γονίας ἀνθρώπους ἀγαγεῖν, καὶ παραστῆσαι ὅτι δὴ τὸ',
 54: 'μέγα τοῦτο καὶ λαμπρὸν τοῦ κόσμου δημιούργημα ἔχει',
 55: 'τὸν θεὸν ποιητήν, καὶ οὔτε αὐτόματον ἔχει τὴν ὕπαρξιν',
 56: 'οὔτε ἀγένητον τὴν ὑπόστασιν καὶ τῷ θεῷ συναΐδιον. καὶ',
 57: 'Πλάτωνα δὲ τὸν παρ’ Ἕλλησι νομισθέντα σοφώτατον,',
 58: 'καίτοι πολλαῖς ὕστερον γενεαῖς γεγονότα καὶ οὐ πλήθει',
 59: 'τυχόντι τοὺς λόγους ποιούμενον ἀλλὰ τοῖς ἐπὶ φιλοσοφίᾳ',
 60: 'τῶν ἄλλων προέχουσιν, ὅμως Μωσέα δείκνυσιν ἐν τῇ',
 61: 'τῆς κοσμογονίας αὐτοῦ διηγήσει ἐκμιμούμενον. πολὺ δὲ',
 62: 'μεγαλοπρεπέστερον Μωσέα Πλάτωνος τεθεολογηκέναι',
 63: 'παρίστησιν.',
 64: 'ὅτι οὐδέν φησιν οὐδ’ ὅλως τῶν ἐν τῇ κοσμογονίᾳ',
 65: 'τῷ προφήτῃ τῇ τοῦ παντὸς διατάξει ἀσύμφωνον· τἀ-',
 66: 'ναντίον δὲ καὶ πολλὰ τῶν ὕστερον αἰτιολογηθέντων ὑπὸ',
 67: 'τῶν φυσικῶν ἐκ τῶν Μωσέως γραφέντων εἴληφε τὴν',
 68: 'ἀρχήν.',
 69: 'ὅτι ἐν πολλοῖς ἀξίως τὸν μέγαν ἀποθειάζει Βασί-',
 70: 'λειον, καὶ Θεόδωρον τὸν Μοψουεστίας, εἰ καὶ μὴ ἐν πᾶσιν',
 71: 'οἷς ἐπαιτιᾶται, ἀλλ’ ἔν γε ἐν ὀλίγοις {u0}',
 72: 'δικαίως.',
 73: 'ὅτι τῆς ἀρχῆς πολλαχῶς φησὶ λεγομένης τὸ ἐν',
 74: 'ἀρχῇ νῦν τὴν κατὰ χρόνον ἀρχὴν δηλοῦν. κατὰ χρόνον',
 75: 'δὲ λέγειν φησὶν οὐχ ὅτι τῆς γενέσεως προηγεῖται χρόνος,',
 76: 'ὡς ἡμῶν ἑκάστου, ἀλλὰ τὸ πρῶτον τοῦ χρόνου νῦν, ἐν ᾧ',
 77: 'τὸν οὐρανὸν καὶ τὴν γῆν παρήγαγεν ὁ θεός, παντὸς',
 78: 'χρονικοῦ χωρὶς διαστήματος. πᾶσαν γὰρ ἀρχὴν ἑτέραν',
 79: 'εἶναί πάντως φησίν, ὅπερ λέγεται ἀρχή· καὶ τοῦτο διὰ',
 80: 'παραδειγμάτων κατασκευάζει. ὡς ἐν τῇ ἀρχῇ τοῦ χρό-',
 81: 'νου καὶ οὐκ ἐν χρόνῳ τὸν οὐρανὸν καὶ τὴν γῆν ἐποίησεν',
 82: 'ὁ θεός. ἀλλ’ ἐν τούτῳ σημαινόμενον τῆς ἐν ᾧ γέγονεν',
 83: 'ἀρχῆς ὁ οὐρανὸς καὶ ἡ γῆ. δεύτερον τὸ πρῶτον τοῦ κα-'}
HEADINGS={44: ('{u0} ἐκ τῶν ΙΩΑΝΝΟΥ ΤΟΥ ΦΙΛΟ-',
      'Ἀνεγνώσθη ἐκ τῶν ΙΩΑΝΝΟΥ',
      'εἰς τὴν ἑξαήμερον.',
      [0.55, 0.095, 0.95, 0.19]),
 45: ('ΠΟΝΟΥ εἰς τὴν ἑξαήμερον.',
      'Ἀνεγνώσθη ἐκ τῶν ΙΩΑΝΝΟΥ',
      'εἰς τὴν ἑξαήμερον.',
      [0.55, 0.095, 0.95, 0.19])}
RIGHT_BOUNDS=('ἀσεβήσουσι, νικήσουσιν.', 'τῆς κατασκευάσματος')
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,57,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[0.2, 0.105, 0.65, 0.73]if number<=4 else[0.56, 0.105, 0.99, 0.73]
        CHUNKS[(57,number)]=[(None,target,region,begin,end)]
    for number,target in LINES.items():
        region=[.21,.095,.61,.77]if number<=40 else[.55,.095,.95,.77]
        begin,end=RIGHT_BOUNDS if RIGHT_BOUNDS else(None,None)
        CHUNKS[(57,number)]=[(None,target,region,begin,end)]
    for number,(target,begin,end,region)in HEADINGS.items():
        CHUNKS[(57,number)]=[(None,target,region,begin,end,'unclassified-heading')]
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
