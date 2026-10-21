"""Complete direct scan observations for retained historical physical page154.

Individual retained printed lines preserve their visibly divided boundaries;
subsequent admitted/fresh rows are outside this frozen historical scope.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:42:30Z'
# Printed line transcription, followed by a bounded independent witness phrase.
LINES={
 2:('ἐξ ἀνθρώπων καὶ μηδὲν ἁμαρτάνειν μηδένας ἀνθρώπων', 'ἐξ ἀνθρώπων κἀ μηδὲν ἁμαρτάνειν μηδένας ἀνθρώπων'),
 3:('μηδαμῇ. νῦν δὲ πῶς, εἰ προνοεῖν αὐτοὺς χρὴ νομίζειν,', 'μηδαμῇ. νῦν δὲ πῶς, εἰ προνοεῖν αὐτοὺς χρὴ νομίζειν,'),
 4:("ὅταν μὴ {u0} παύωνται πλημμελοῦντες ὧν ἄρχουσι,", "ὅταν μὴ [εἰ δ' ἐξ] παύωνται πλημμελοῦντες ὧν ἄρχουσι,"),
 5:('μὴ δικαίως ὑπ’ ἐνίων {u0}; καὶ ὁ μὲν ἡνίοχος', "μὴ δικαίως ὑπ' ἐνίων ἀμελεῖσθαι; καὶ ὁ μὲν ἡνίοχος"),
 6:('παραλαβὼν λακτίζοντας τοὺς ἵππους πραΰνει καὶ τιθασ-', 'παραλαβὼν λακτίζοντας τοὺς ἵππους πραΰνει καὶ τιθασσεύει'),
 7:('σεύει, καὶ τελευτῶν ἐπ’ αὐτῶν ἀσφαλῶς κατὰ πολλὴν', "τιθασσεύει, καὶ τελευτῶν ἐπ' αὐτῶν ἀσφαλῶς κατὰ πολλὴν"),
 8:('ῥᾳστώνην εἶσιν ὅποι βούλεται· οἱ θεοὶ δὲ οὔπω καὶ νῦν', 'ῥᾳστώνην εἶσιν ὅποι βούλεται· οἱ θεοὶ δὲ οὔπω καὶ νῦν'),
 9:(' ἐξῃρήκασιν ἀδικίαν ἐξ ἀνθρώπων ἐκ τοσούτου, “καὶ ταῦτα', 'ἐξῃρήκασιν ἀδικίαν ἐξ ἀνθρώπων ἐκ τοσάτου, καὶ ταῦτα'),
 10:('ἐκ παντὸς τοῦ αἰῶνος πολιτευόμενοι, καὶ προσέτι εἰς', 'ἐκ παντὸς τοῦ αἰῶνος πολιτευόμενοι, καὶ προσέτι εἰς'),
 11:('ἑαυτοὺς ἁμαρτάνοντας ὁρῶντες ἔστιν οὓς αὐτῶν. ἀλλὰ', 'ἑαυτοὺς ἁμαρτάνοντας ὁρῶντες ἔστιν οὓς αὐτῶν. ἀλλὰ'),
 12:('μὴν ὅτε ταῦτα οὐδ’ ἂν εἷς ὑγιαίνων εἴποι σπουδῇ, πλὴν', "μὴν ὅτε ταῦτα οὐδ' ἂν εἷς ὑγιαίνων εἴποι σπουδῇ, πλὴν"),
 13:('ὡς ἡμεῖς νῦν εἰς ἔλεγχον λόγου, πῶς οὐ κομιδῇ Πλάτων', 'ὡς ἡμεῖς νῦν εἰς ἔλεγχον λόγου, πῶς ὁ κομιδῇ Πλάτων'),
 14:('συκοφαντεῖ; εἰ γὰρ ἃ μηδ’ οἱ θεοὶ πώποτε πεποιήκασι,', "συκοφαντεῖ; εἰ γὰρ ἃ μηδ' οἱ θεοὶ πώποτε πεποιήκασι,"),
 15:('μηδὲ παρ’ αὐτῆς τῆς Ἀθηνᾶς τῆς πολιάδος εἶχεν ἀπαι-', "μηδὲ παρ' αὐτῆς τῆς Ἀθηνᾶς τῆς πολιάδος εἶχεν ἀπαιτῆσαι,"),
 16:('τῆσαι, ταῦτα παρὰ Θεμιστοκλέους καὶ Περικλέους ἀπαιτεῖ,', 'ἀπαιτῆσαι, ταῦτα παρὰ Θεμιστοκλέους καὶ Περικλέους ἀπαιτεῖ,'),
 17:('αὐτὸν ἐρωτῶν πῶς οὐ συκοφαντεῖ; ἀλλ’ οἶμαι τὴν μὲν', "αὐτὸν ἐρωτῶν πῶς οὐ συκοφαντεῖ; ἀλλ' οἶμαι τὴν μὲν"),
 18:('τοῦ δήμου φύσιν οὐκ ἠδυνήθησαν μεταποιῆσαι οὐδ’ ἀφα-', "τοῦ δήμου φύσιν ἐκ ἠδυνήθησαν μεταποιῆσαι οὐδ' ἀφανίσαι·"),
 19:('νίσαι· ἔστι δ’ αὕτη μηδέποτε γενέσθαι πάντα χρηστὴ μηδ’', "ἀφανίσαι· ἔστι δ' αὕτη μηδέποτε γενέσθαι πάντα χρηστὴ μηδ'"),
 20:('ἀναμάρτητον· ὅσα δὲ κινδυνεύοντας ἔδει {u0},', 'ἀναμάρτητον· ὅσα δὲ κινδυνεύοντας ἔδει προνοήσασθαι,'),
 21:('ἐν οἷς ἅμα καὶ τῶν πολλῶν καὶ τῶν ἐπιεικῶν ἦν εὐερ-', 'ἐν οἷς ἅμα καὶ τῶν πολλῶν καὶ τῶν ἐπιεικῶν ἦν εὐεργέτας'),
 22:('γέτας εἶναι, ἢ κατ’ ἐξουσίαν πράττοντας ἀπάγειν ἀπὸ', "εὐεργέτας εἶναι, ἢ κατ' ἐξουσίαν πράττοντας ἀπάγειν ἀπὸ"),
 23:('τῶν δυσχερεστάτων ἀεὶ καὶ εἰς ἐλάχιστον τρέπειν τὰ τῆς', 'τῶν δυσχερεστάτων ἀεὶ καὶ εἰς ἐλάχιστον τρέπειν τὰ τῆς'),
 24:('φύσεως ἁμαρτήματα, ταῦτα οὐκ ἔστιν ὅπως οὐ παρὰ', 'φύσεως ἁμαρτήματα, ταῦτα οὐκ ἔστιν ὅπως οὐ παρὰ'),
 25:(' τούτοις “ὄντα φανήσεται, καὶ ταῦτα πρὸς τῷ λόγῳ τῷ', 'τούτοις ὄντα φανήσεται, καὶ ταῦτα πρὸς τῷ λόγῳ τῷ'),
 26:('παρ’ ἡμῶν καὶ ταῖς ἀποδείξεσι Πλάτων αὐτὸς ἐπισφρα-', "παρ' ἡμῶν καὶ ταῖς ἀποδείξεσι Πλάτων αὐτὸς ἐπισφραγίζεται,"),
 27:('γίζεται, καὶ ἔστιν ἡμῖν κἀνταῦθα μάρτυς ὑπὸ τῆς αὐτῆς', 'ἐπισφραγίζεται, καὶ ἔστιν ἡμῖν κἀνταῦθα μάρτυς ὑπὸ τῆς αὐτῆς'),
 28:('δεξιότητος, ἥσπερ κἂν τοῖς ἄνω κατὰ τὴν χρείαν ἀεί.', 'δεξιότητος, ἥσπερ καὶ τοῖς ἄνω κατὰ τὴν χρείαν ἔδει.'),
 29:('καίτοι πῶς οὐκ ἄτοπον ἦν τὰ ἔργα κοσμεῖν τούτων,', 'καίτοι πῶς οὐκ ἄτοπον ἦν τὰ ἔργα κοσμεῖν τούτων,'),
 30:('τὴν δὲ πολιτείαν φαυλίζειν· καὶ ἃ τῆς τῶν {u0}', 'τὴν δὲ πολιτείαν φαυλίζειν· καὶ ἃ τῆς τῶν πεισθέντων'),
 31:('των ἀρετῆς τίθεταί τις δείγματα, ταῦτα μὴ τῆς τῶν', 'πεισθέντων ἀρετῆς τίθεται τις δείγματα, ταῦτα μὴ τῆς τῶν'),
 32:('πεισάντων πρῶτον ὑπάρχειν {u0}; ἔγκειται μὲν', 'πεισάντων πρῶτον ὑπάρχειν ἡγεῖσθαι; ἔγκειται μὲν'),
 33:('γάρ που ταῦτα μεταξὺ τοῦ μύθου [χωρίς τινος προφά-', 'γάρ που ταῦτα μεταξὺ τοῦ μύθου [χωρίς τινος προφάσεως]'),
 34:('σεως] οὐκ ἀσκέπτως ἐμοὶ δοκεῖν οὐδὲ φαύλως, οὐδ’', "προφάσεως] ἐκ ἀσκέπτως ἐμοὶ δοκεῖν οὐδὲ φαύλως, οὐδ'"),
 35:('ὡς ἐξέπεσεν, ἀλλ’ ὅπως συγκρυφθείη τε ὡς δυνατὸν', "ὡς ἐξέπεσεν, ἀλλ' ὅπως συγκρυφθείη τε ὡς δυνατὸν"),
 36:('μάλιστα, καὶ εἴ τις εὑρὼν χρῷτο, μηδ’ αὐτὸς δοκῇ', "μάλιστα, καὶ εἴ τις εὑρὼν χρῷτο, μηδ' αὐτὸς δοκῇ"),
 37:('παρελθεῖν, ἀλλ’ ἐνείη· οὕτω μέσην τινὰ εὗρε τάξιν,', "παρελθεῖν, ἀλλ' ἐνείη· οὕτω μέσην τινὰ εὗρε τάξιν,"),
 38:('καὶ ἅμα πρὸς τῇ τελευτῇ τοῦ λόγου τοῦ παντός, ἃ θεὶς', 'καὶ ἅμα πρὸς τῇ τελευτῇ τοῦ λόγου τοῦ παντός, ἃ θεὶς'),
 39:('ἐν ἀρχῇ τοῖς ἐφεξῆς οὐκ ἔμελλεν ἕξειν οἶμαι {u0}.', 'ἐν ἀρχῇ τοῖς ἐφεξῆς οὐκ ἔμελλεν ἕξειν οἶμαι χρήσασθαι.'),
 50:('οὐ γὰρ εἰ ῥᾴδιον ἢ μὴ τῷ ὄντι γενέσθαι ῥήτορα προ-', 'οὐ γὰρ εἰ ῥᾴδιον ἢ μὴ τῷ τῷ ὄντι γενέσθαι ῥήτορα προὔκειτο'),
}
UNCERTAINTIES={
 (154,4):[("[εἰ δ’ ὁ]","[εἰ δ’ οὐ]",'The compact negative in the bracketed source reading remains unresolved independently; digital [εἰ δ’ ἐξ] is a differing witness.')],
 (154,5):[('ἀμείλῃ','ἀμελεῖσθαι','The compressed sigma/theta group remains unresolved independently.')],
 (154,20):[('προνοοῦσιν','προνοήσασθαι','The compact sigma/theta group and final letters remain unresolved independently.')],
 (154,30):[('πειθόν-','πεισθέν-','The sigma component of the compact σθ group remains unresolved independently. Both source and original are divided printed fragments; neither may be counted as a standalone form.')],
 (154,32):[('ἡγεῖσθ','ἡγεῖσθαι','The compact final sigma/theta group and vowels remain unresolved independently.')],
 (154,39):[('χρήσθ','χρήσασθαι','The compact final sigma/theta group and vowels remain unresolved independently.')],
}
LEADING_FRAGMENTS={(154,7):'σεύει',(154,16):'τῆσαι',(154,19):'νίσαι',(154,22):'γέτας',(154,27):'γίζεται',(154,31):'των',(154,34):'σεως'}
CHUNKS={}
for number,(target,witness)in LINES.items():
    region=[.415,.112,.80,.335]if number==50 else [.045,.112,.425,.335]if number<=15 else [.045,.30,.425,.535]if number<=28 else [.045,.485,.425,.68]
    CHUNKS[(154,number)]=[(None,target,region,witness,witness)]
for number,anchor,literal in [(9,'1261R.','1261R.'),(25,'68a H.','681H.')]:
    CHUNKS[(154,number)].insert(0,(anchor,'',[.005,.20,.43,.535],None,None,'marginal-reference',literal))


def _row_sha(row):
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _reading(sections,page,begin,end):
    if begin is None:return []
    section=f'tlg4040-tlg001-local002-s{page+277}'; full=sections[section]
    starts=[m.start()for m in re.finditer(re.escape(begin),full)]
    if len(starts)!=1:raise ValueError(f'Ambiguous digital bound {page}: {begin!r}')
    a=starts[0];b=full.index(end,a)+len(end)
    return [{'kind':'digital','section':section,'start':a,'end':b,'text':full[a:b]}]


def records(rows,document,crop_png,sections):
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
                    segment['evidence']+=(' This is an isolated marginal reference label; the body projection omits it.'if role=='marginal-reference'else' This inset small-type explanatory paragraph follows the large-type body and precedes the lower apparatus; its typography establishes boundaries without establishing authorship. Exclude it pending attribution.')
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
