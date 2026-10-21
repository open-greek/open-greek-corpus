"""Complete direct scan review of physical192, preserving every retained word.

Abbreviated and corrupt digital forms are separate alternatives, not authority.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:13:16.368062Z'
LINES={1: 'πρὸς ἀμμώδη συνήλασε περιοχήν, καὶ ἄπορον τὴν σωτηρίαν παρέχε τοῖς ἐμπλέουσι. διὸ τὰ μὲν πρῶτα ὀδυρμὸς τοὺς '
    'ἐπιπλέοντας συνέχει πολὺς μέν, οὐκ ἀπογινώσκων δὲ τὴν ἀμείνω προσδοκίαν· ἤδη γάρ τινας οὕτως ἀπενεχθέντας '
    'σέσωκε πλημμυρὶς ὑπολαβοῦσα τοῖς ἀνοιδᾶσιν αἰφνιδίως ἐκ τῆς θαλάττης ὄγκοις· ἐπὰν δὲ λήγῃ τὰ τῆς τροφῆς, μυρία '
    'μὲν {u0} πάθη, τέλος δὲ {u1} πάντες ἢ λιμῷ ἢ (τοῦ λιμοῦ τὸ μακροχρόνιον οὐ φέροντες) ξίφει, ἢ αὐτῇ θαλάσσῃ σφᾶς '
    'αὐτοὺς ἐπιῤῥίπτοντες.',
 2: 'ὅτι φησί, Τὰ μὲν ἕως τῶν ταύρων καὶ Πτολεμαΐδος {u0}, τὰ δὲ ἀνωτέρω τούτων οὐ τὴν τυχοῦσαν λαμβάνει μετάβασιν. '
    'κεῖται γὰρ οὐκέτι τὰ ἐπέκεινα πρὸς μεσημβρίαν τῆς χώρας, ἀεὶ δὲ πρὸς τὴν ἀνατολὴν ἀναστρέφει μᾶλλον, καὶ τὰς '
    'σκιὰς βάλλει τέως δυεῖν ὡρῶν εἰς τὸν ἀντικείμενον τόπον τῆς ἄρκτου. ἔτι δὲ ποταμοῖς καταῤῥεῖται τὰς πηγὰς '
    'ἀναφαίνουσιν ἀπὸ τῶν Ψεβαιῶν καλουμένων ὀρῶν. τῆς δὲ χώρας ἡ μὲν εἰς τὴν μεσόγειαν ἀνατείνουσα πλήρης ἐλεφάντων '
    'καὶ ῥινοκέρων καὶ ταύρων καὶ ὑῶν, τὰ δὲ εἰς τὸν πόρον καθήκοντα νήσοις ἅπαντα πυκνοῦται τῇ φύσει μὲν ἀκάρποις, '
    'γεμούσαις δὲ ὀρνέων ἀνιστορήτους ἰδέας ἐχόντων. τὸ δὲ ἀπὸ τῆδε ἡ μὲν θάλαττα βαθεῖά τε καὶ πλόϊμος, κήτη δὲ '
    'ἔχει τηλικαῦτα ὥστε ἀγωνιᾶν τὸν ἰδόντα· οὐ μέντοι διαπεφώνηκεν οὐδείς, πλὴν τῶν περιπεπτωκότων ἀκουσίως ταῖς '
    'λοφιαῖς διὰ τὴν τῶν εἰρημένων ἄγνοιαν· καὶ γὰρ οὐδὲ διώκειν {u1} θρασύτερον τοὺς πλέοντας, τῶν ὀμμάτων τοῖς '
    'θηρίοις ἀμαυρομένων, ὅταν ἐκ τῆς θαλάττης τὰ πρόσωπα ἀναφαίνωσιν.',
 3: 'ὅτι τοῦ Φοινικῶνος τὰ μὲν ἄνωθεν ὁρώμενα πέτραις {u0} ποικίλαις {u1}, τοῖς δὲ πρὸς θάλασσαν διήκουσιν ἠϊὼν {u2} '
    'ξενή τε καὶ μακρά. τῇ δὲ εἰρημένῃ παραλίᾳ συνάπτει μὲν τόπος, ὃν προσηγόρευσαν Νῆσσαν ἀπὸ τῆς τοῦ ζῴου '
    'πολυπληθείας· αὕτη δὲ ἡ Νῆσσα κεῖται μὲν ἐγγὺς ἀκρωτηρίου καθ’ ὑπερβολὴν ὑλώδους, διατείνει δὲ ἐπ’ εὐθείας '
    'θεωρουμένη πρός τε τὴν Πέτραν καλουμένην καὶ τὴν Παλαιστίνην, εἰς ἣν Γεῤῥαῖοι καὶ Μιναῖοι καὶ πάντες οἱ πλησίον '
    'ἔχοντες τὰς οἰκήσεις Ἄραβες τὸν τε λιβανωτόν, ὡς λόγος, καὶ τὰ φορ-',
 4: 'τία τὰ πρὸς εὐωδίαν ἀνήκοντα ἀπὸ τῆς χώρας τῆς ἄνω κατάγουσιν.',
 5: 'ὅτι μετὰ τὸν καλούμενον Λαιανίτην κόλπον, ὃν Ἄραβες περιοικοῦσιν, ἡ Βυθημανέων ἐστὶ γῆ, πολλή τε καὶ πεδιάς, '
    'καὶ πᾶσα κατάῤῥυτος καὶ βαθεῖα, ἀγρώστει δὲ μόνον καὶ μηδικῇ καὶ λωτῷ βάθος ἀνδρόμηκες ἔχοντι πᾶς ὁ καρπὸς αὐτῇ '
    '{u0}, ἕτερον δὲ {u1} οὐδέν. διὸ πολλαὶ μὲν ἐν αὐτῇ ἀγρίαι κάμηλοι, πολλαὶ δὲ ἐλάφων καὶ δορκάδων ἀγέλαι, συχναὶ '
    'δὲ ποῖμναι προβάτων καὶ ἀμύθητος ἀριθμὸς ἡμιόνων καὶ βοῶν. τούτοις δὲ τοῖς εὐκληρήμασιν ἀντικείμενον {u2} '
    'κακόν· λεόντων γὰρ καὶ λύκων καὶ παρδάλεων συναναφέρει πλῆθος ἡ γῆ, ὥστε εἶναι τὸ τῆς χώρας ἐπίτευγμα τοῖς '
    'οἰκηταῖς αἴτιον ἀκληρίας.',
 6: 'ἀπὸ δὲ τῶν ἐφεξῆς αἰγιαλῶν κόλπος ἐστὶ νενευκὼς μὲν εἰς τὸν μυχὸν τῆς χώρας, οὐκ ἔλαττον δὲ σταδίων πεντακοσίων '
    'ὑποδείκνυσι τὸ βάθος. οἱ δὲ τὴν ἐντὸς τοῦ κύκλου κατοικοῦντες {u0} μὲν Βατμιζομανεῖς, εἰσὶ δὲ κυνηγοὶ τῶν '
    'χερσαίων ζῴων. τὴν δ’ εἰρημένην χώραν νῆσοι τρεῖς {u1}, λιμένας ποιοῦσαι πλείους· ὧν τὴν πρώτην Ἴσιδος ἱερὰν '
    'ὠνόμασαν, τὴν δὲ δευτέραν Σκαβύαν, τὴν δὲ τρίτην Σαλυδώ, ἐρήμους δὲ πάσας καὶ συσκίους ἐλαίαις οὐ ταῖς παρ’ '
    'ἡμῖν ἀλλὰ ταῖς ἐν ἐκείνοις τοῖς τόποις φυομέναις.',
 7: 'μετὰ δὲ τὰς νήσους τὰς ἐκκειμένας ἔστιν ἰδεῖν αἰγιαλὸν λιθώδη καὶ μακρόν· ἡ δὲ χώρα Θαμουδηνῶν Ἀράβων. ὁ δὲ '
    'πρὸς ταύτην παράπλους ἐπὶ σταδίων τῶν χιλίων πλείους πάντων χαλεπώτατος· {u0} εὔορμος, οὐ σάλος ἐπ’ ἀγκύρας, οὐ '
    'κόλπος ἐπὶ σκέπης, οὐ χηλῆς ἐντύπωμα, ἀναγκαία καταφυγή, τὸν ναυτίλον δεχόμενον. μετὰ ταῦτα δὲ οὐκ εὐθὺς '
    'ἐφεξῆς, ἀλλὰ μεθ’ ἕτερά τινα, ἔστιν αἰγιαλὸς εἰς ὑπερβολὴν κάθυδρος ἐκτεινόμενος, καὶ τὸ προσηγορευμένον Λαιμὸν '
    'ὄρος, ἀμύθητον μὲν ἀναφαῖνον τῆς περιμέτρου τὸ μέγεθος, παντοίας δὲ ὕλης δρυμοῖς διεζωσμένον.',
 8: 'ὅτι τὴν ἀσυγείτονα τῆς ὀρεινῆς χέρσου Δεδεβαὶ κατοικοῦσιν, οἱ μὲν νομάδες, οἱ δὲ γεῶχοι. ὧν κατὰ μέσην τὴν '
    'χώραν ποταμὸς {u0} τριμερὴς μὲν τῇ φύσει, ψῆγμα δὲ χρυσοῦ κατάγων, οὕτω σύνδηλον τὴν δαψίλειαν ἔχων ὥστε τὴν '
    'ἰλὺν τὴν πρὸς ταῖς ἐκβολαῖς συν-'}
BOUNDS={1: ('πρὸς ἀμμώδη', 'σφᾶς αὐτὸς ἐπιῤῥίπτοντες.'), 2: ('ὅτι φησί, Τὰ μὲν', 'τὰ πρόσωπα ἀναφαίνωσιν.'), 3: ('ὅτι τᾶ Φοινικῶνος', "τὸν τε λιβανωτόν, ὡς λόγος, κ' τὰ φορτία"), 4: ('τὰ πρὸς εὐωδίαν', 'τῆς ἄνω κατάγεσιν.'), 5: ('ὅτι μετὰ τὸν καλέμενον', 'αἴτιον ἀκληρίας.'), 6: ('ἀπὸ δὲ τῶν ἐφεξῆς', 'τόποις φυομέναις.'), 7: ('μετὰ δὲ τὰς νήσους', 'δρυμοῖς διεζωσμένον.'), 8: ('ὅτι τὴν ἀσυγειτόνα', 'πρὸς ταῖς ἐκβολαῖς συνηγμένην')}
UNCERTAINTIES={(192, 1): [('ἀναδέχονθ’',
             'ἀναδέχονται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('ἀναλίσκονθ’',
             'ἀναλίσκονται',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (192, 2): [('ἡμῖν ἐστιν',
             'ἡρμήνευται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('δύναθ’',
             'δύναται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (192, 3): [('ὀγυσι', 'ὄψεσι / ὕψεσι', 'The compact noun reading remains unresolved independently.'),
            ('κατέχει',
             'κατέχεται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('ὑπόκειν’',
             'ὑπόκειται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (192, 5): [('περιγράφει',
             'περιγράφεται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('γεωργεῖ',
             'γεωργεῖται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('παραπλέκων]',
             'παραπέπλεκται',
             'The compact final consonants remain unresolved independently of the digital witness.')],
 (192, 6): [('καλῶν',
             'καλοῦνται',
             'The compact final consonants remain unresolved independently of the digital witness.'),
            ('ἐκδέχονται',
             'ἐκδέχονται',
             'The compact sigma/theta or sigma/chi group remains unresolved independently of the digital witness.')],
 (192, 7): [('ὁ γὰρ ἐστιν, ἄκ ἐστιν ἄλιμην',
             'οὐ γὰρ ἔστιν, οὐκ ἔστιν οὐ λιμὴν',
             'The sequence of compact negative particles is retained as an unresolved literal source reading; no '
             'syntactic reconstruction is admitted.')],
 (192, 8): [('διαφέρεθ',
             'διαφέρεται',
             'The compact final consonants remain unresolved independently of the digital witness.')]}
LEADING_FRAGMENTS={(192,4):'τία'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,target in LINES.items():
        begin,end=BOUNDS[number]
        region=[.025,.105,.49,.73]if number<=3 else[.39,.105,.86,.73]
        CHUNKS[(192,number)]=[(None,target,region,begin,end)]
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
