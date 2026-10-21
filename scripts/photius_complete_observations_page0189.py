"""Complete direct scan observations of every retained passage on physical189.

The source is transcribed literally, with digital alternatives retained separately.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:08:41.627628Z'
LINES={1: 'ἀπὸ τροπῶν χειμερινῶν ἕως μέσου χειμῶνος· εἶτα καὶ τὰς τῶν κυνῶν θηλείας ἀμέλγοντες τῷ γάλακτι {u0}, καὶ ἐξ '
    'ἄλλων δὲ θήρας ζώων. καὶ τὰ μὲν τελευταῖα τῶν πρὸς μεσημβρίαν τοιαῦτα.',
 2: 'τὰ δὲ κατὰ τοὺς τρωγλοδύτας τοιαῦτα. τὸ μὲν γένος τῆς συστάσεως τυραννίς, αἱ δὲ γυναῖκες κοιναὶ καὶ οἱ παῖδες· '
    'μόνῃ δ’ οὐκ ἔξεστι πλησιάσαι τῇ τοῦ τυράννου· τῷ δὲ τολμήσαντι πρόβατον {u0} τὸ ἐπιτίμιον {u1}. ἡ δὲ ἀναστροφὴ '
    'αὐτῶν· τὸν μὲν παρ’ αὐτοῖς',
 4: 'ταῖς κηδείαις {u0} νουνεχῶς, εἴπερ μὴ λυπεῖν ἑαυτοὺς ἐπὶ τοῖς ἀλυπήτοις συνέσεως σημεῖον. τὰς δ’ ὑπὲρ τῆς '
    'ἀναφυομένης αἰφνιδίως νομῆς ἔχθρας τε καὶ μάχας καὶ πολέμους αὐτῶν πρὸς ἀλλήλους (οὐδὲ γὰρ ὑπὲρ ἄλλου τινὸς '
    '{u1}) ἀλλ’ ἐν ταύταις αἱ πρεσβύτεραι γυναῖκες προπηδῶσαι διαλύουσι, κατὰ τὸ μέσον ἐλθοῦσαι, καὶ τοῖς πραΰνουσι '
    'λόγοις τοὺς θυμοὺς ἀνηρεθισμένους καταστέλλουσαι. ὕπνῳ δέ, φησίν, οὐ κατὰ τοὺς ἄλλους {u2}, ἀλλὰ θρεμμάτων μὲν '
    'πλῆθος ἑαυτοῖς ἔχουσι συνεπόμενον, κώδωνας δὲ ἐξέδησαν ἐκ τῶν κεράτων τῶν ἀῤῥένων πάντων, ὅπως ὁ ἀπ’ αὐτῶν '
    'ψόφος διώκῃ τὰ θηρία· ἐπὰν δὲ νὺξ ἐπῇ, εἰς μάνδρας μὲν συνάγουσι τὴν λείαν, ἄνωθεν δὲ ἐπιβάλλουσι ῥιπὰς ἐκ '
    'φοινίκων. καὶ αἱ μὲν γυναῖκες μετὰ τῶν νηπίων τούτοις ἐπιβαίνουσιν· οἱ δὲ ἄνδρες πυρὰ κύκλῳ καίουσιν, ᾄδοντες '
    'πατρίους τινὰς μύθους, καὶ τὸν ὕπνον οὕτω {u3}, ἐν πολλοῖς τῆς μελέτης διὰ τἀναγκαῖα τὴν φύσιν νικώσης. ἐπὰν δέ '
    'τινες τῷ πᾶσιν ὀφειλομένῳ γήρως βαρύνοντος μηκέτι {u4} ταῖς ποίμναις ἐπακολουθεῖν, περιθέντες βοὸς οὐρὰν περὶ '
    'τὸν αὐχένα τὸν αὑτῶν, καὶ τὸν ὀπίσω τῷ τραχήλῳ δεσμὸν εὖ μάλα περισφίγξαντες, ἀπολύουσι τοῦ βίου. εἰ δέ τις '
    'αὐτῶν τὴν τελευτὴν ὑπερβάλλοι, παραστὰς ὁ θέλων ἄφνω, ὡς ἐπ’ εὐνοίᾳ τὸν ὄκνον ἀφαιρούμενος, νουθετῶν ἅμα τῷ '
    'λόγῳ τῆς ἀναστροφῆς, διὰ τῆς αὐτῆς ὁδοῦ παρέλυσεν. οὐ τοὺς γηράσκοντας δὲ μόνον οὕτω τοῦ ζῆν ὑπεξάγουσιν, ἀλλὰ '
    'καὶ οὓς ἢ νόσος ἐπίμονος ἢ μελῶν τινὸς πήρωσις ἀχρήστους εἰς τὸ ταῖς ἀγέλαις παρασκευάσει {u5}.',
 5: 'ὅτι φησί, Τῆς ὅλης οἰκουμένης ἐν τέτταρσι κυκλιζομένης μέρεσιν, ἀνατολῆς λέγω, δύσεως, ἄρκτου καὶ μεσημβρίας, '
    'τὰ μὲν πρὸς ἑσπέραν {u0} Λύκος τε καὶ Τίμαιος, τὰ δὲ πρὸς ἀνατολὰς Ἑκαταῖός τε καὶ Βασιλεύς, τὰ δὲ πρὸς τὰς '
    'ἄρκτους Διόφαντος καὶ Δημήτριος, τὰ δὲ πρὸς μεσημβρίαν, φορτικόν, φησί, τὸ ἀληθές, ἡμεῖς.',
 6: 'ὅτι τοὺς τῶν ἀνθρώπων διαφορωτάτους βίους {u0} διαμετρεῖ καὶ διορίζει τόπος. ἐκ γὰρ τῆς Μαιώτιδος λίμνης πολλοὶ '
    'τῶν φορτιζομένων ἐν φορτηγοῖς ἀκάτοις δεκαταῖοι κατῆραν εἰς τὸν Ῥοδίων λιμένα, ἀφ’ ὧν ὑπὸ τὸν αὐτὸν καιρὸν '
    'τεταρταῖοι μὲν ἀφίκοντο εἰς'}
BOUNDS={1: ('ἀπὸ τροπῶν χειμερινῶν', 'τῶν πρὸς μεσημβρίαν τοιαῦτα.'), 2: ('τὰ δὲ κατὰ τοὺς', 'τὸν μὲν παρ’ αὐτοῖς'), 4: ('ταῖς κηδείαις καταχρῶνθ’', 'παρασκευάσει συνέπεσθαι.'), 5: ('ὅτι φησί, Τῆς', 'τὸ ἀληθές, ἡμεῖς.'), 6: ('ὅτι τὰς τῶν ἀνθρώπων', 'τεταρταῖοι μὲν ἀφίκοντο εἰς')}
UNCERTAINTIES={(189, 1): [('τρέφουσι',
             'τρέφονται / τρέφονθ’',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (189, 2): [('καταθῆναι',
             'καταθέσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
            ('θάνατος',
             'δίδοται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (189, 4): [('καταχρωμένῳ',
             'καταχρῶνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('μάχων',
             'μάχονται',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.'),
            ('τῶν ἀνθρώπων χρωμένῳ',
             'τῶν ἀνθρώπων χρῶνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('παραφθην',
             'παρωθοῦνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('δονωτὰ',
             'δύνωνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('συνέπει',
             'συνέπεσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (189, 5): [('ἐξέρχασαι',
             'ἐξείργασται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (189, 6): [('ὁ πολὺς',
             'οὐ πολὺς',
             'The compact initial particle remains unresolved independently; retain the source candidate without '
             'deriving it from syntax.')]}
LEADING_FRAGMENTS={}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,target in LINES.items():
        begin,end=BOUNDS[number]
        region=[.20,.105,.65,.38]if number in(1,2)else[.56,.105,.99,.73]
        CHUNKS[(189,number)]=[(None,target,region,begin,end)]
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
