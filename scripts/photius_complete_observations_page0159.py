"""Complete direct scan observations for retained historical physical page159.

All inset explanatory material is preserved with unresolved authorial role;
some inset passages have no counterpart in the pinned digital witness.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:59:29.852497Z'
CHUNKS={
 (159,1):[
  ('θεὸς ἄλλος.', 'καὶ δειλὸς καὶ φιλάργυρος, εἰς μισθοφορὰν καταστήσας. περὶ μὲν δὴ λάλων, ὦ Πλάτων, καὶ ἀργῶν καὶ δειλῶν αὐτόθεν κατάβαλε, μή πού τις καὶ Τρῶας ἐγείρῃσι θεὸς ἄλλος.', [.20,.105,.60,.34], 'καὶ δειλὸς καὶ φιλάργυρος,', 'θεὸς ἄλλος.'),
  ('σῦμα.', ' κατάβαλε κατάθου, {u0}', [.20,.105,.60,.34],None,None,'unclassified-small-type'),
  ('ἄκρας ἡ παρὰ', ' σὺ δὲ Μαντινικὴν μὲν ξένην καὶ Μιλησίαν ἐπίστασαι κοσμεῖν, καὶ ἅστινας ἄν σοι δοκῇ, πάνυ ῥᾳδίως μεγάλων ἠξίωσας· τῶν δὲ Ἑλλήνων τοὺς ἄκρους καὶ παρὰ', [.20,.105,.60,.34], 'σὺ δὲ Μαντινικὴν', 'τοὺς ἄκρους καὶ παρὰ'),
  ('689 H.','',[.16,.20,.60,.28],None,None,'marginal-reference','689H.'),
  ('τῶν λόγων γίνη.', ' πᾶσι βεβοημένους “ἐν φαύλῳ καθαιρεῖς. αἴτιον δ’ οὐ τὸ ἀγνοεῖν τὴν ἀξίαν, ἀλλὰ πῶς ἂν εἴποιμι εὐπρεπῶς; σφόδρα τῶν λόγων γίνῃ.', [.20,.105,.60,.34], 'πᾶσι βεβοημένους', 'τῶν λόγων γίνῃ.'),
  ('τῶν πραγμάτων ἀληθείας,', ' ἀντὶ τῷ λόγῳ γίνῃ καὶ οὐ τῆς τῶν πραγμάτων ἀληθείας.', [.20,.105,.60,.34],None,None,'unclassified-small-type'),
  ('περὶ τὰς λόγους αὐτῷ.', ' πῶς ἂν εἴη διεφθαρκὼς Ἀθηναίους ἢ πῶς λάλους πεποιηκώς, ὅς γε κἀν τοῖς λόγοις αὐτοῖς τὸ μηδὲν φαύλως μηδ’ εἰκῇ τιμήσας φαίνεται; τἀναντίον γάρ ἔμοιγε πᾶν αὐτὸς ἐθίσαι δοκεῖ, μήτε λέγειν ὅπως ἔτυχε μηδὲν μήτε ποιεῖν ἀπὸ τοῦ πρώτου παραστάντος. ἔτι δ’ ἄλλο μέν τινος πράγματος {u1} μάρτυρι κωμῳδίας διδασκάλῳ τύχῃ ἂν οὐκ {u2} ἦν· εἰς δὲ λόγων κρίσιν μή ποτε {u3} ὥσθ’ ὑπεριδεῖν τῶν ἀνδρῶν τούτων ὡς οὐδενὸς ἀξίων. ὁ μὲν τῶν Ἑλληνίδων μεγίστην ὁ Κρατῖνος τὴν ἐκείνου γλῶτταν εἴρηκε, λέγων μὲν ἴσον τι καὶ φωνήν, ἀναμίξας δέ τι τῆς παρὰ τῆς τέχνης πικρίας τοῖς ἀπὸ τῆς ἀληθείας. ὅμως δ’ οὐκ ἐξέφυγε τὸ μὴ οὐ τὰ πρῶτα δῶναι τῷ ἀνδρὶ μηδ’ {u4} τὴν μεγαλοπρέπειαν τὴν περὶ τοὺς λόγους αὐτοῦ.', [.20,.265,.60,.505], 'πῶς ἂν εἴη διεφθαρκὼς', 'περὶ τοὺς λόγους αὐτοῦ.'),
  (None, ' ὁ δὲ Ἀριστοφάνης ἀστράπτειν καὶ βροντᾶν αὐτὸν καὶ μυκᾶν φησὶ δημηγοροῦντα. μὴ γάρ μοι τοῦτο, {u5} αὐτοῦ· ἀλλ’ ὅσον εἰς τὸν παρόντα προσήκει λόγον τῆς μαρτυρίας λάβωμεν. ἀλλ’ ἐν πολλῇ τινὶ τῇ περιουσίᾳ χρώμενος οὕτω διεγίγνετο, πόρρω μὲν αὐτὸς ὢν τοῦ ληρεῖν, πλεῖστον δὲ τοὺς ἄλλους ἐθίζειν ἀπέχων. πῶς οὖν ὁ τοσοῦτον ὑπερέχων καὶ μόνος πᾶσι τοῖς κριταῖς νικῶν τήν τε φλυαρίαν εἰκῇ καὶ παρὰ καιρὸν Ἀθηναίοις ἀνεῖναι φέροιτ’ ἂν δόξαν; ἐγὼ μὲν γὰρ τἀναντίον ἡγοῦμαι, σιωπῆς αἴτιον αὐτὸν πλείονος ἢ προπετείας καταστῆναι. ἴσμεν γὰρ ὅτι κἀν ταῖς ἄλλαις δή που δυνάμεσιν, ᾗ μὲν πολλοὶ παραπλήσιοι καὶ ἐφάμιλλοι πρὸς ἀλλήλους, πολλὰ τὰ πράγματα καὶ πλείων ἡ ἔρις, ἐπειδὰν δέ τις εἷς {u6} λαμπρῶς, ἅπαντες', [.20,.425,.60,.73], 'ὁ δὲ Ἀριστοφάνης', 'λαμπρῶς, ἅπαντες')],
 (159,2):[
  ('ἂ βελτίους ἔσιν.', 'ἤδη συγκεχωρήκασιν. ἔστω δὴ καὶ λέγειν ἐπειδάν τις ἄκρος ἐγγένηται, στέργειν ἀνάγκη τοὺς πλείους καὶ μὴ πολυπραγμονεῖν, ἀλλ’ ὡς οἷόν τε μάλιστα εὐλαβεῖς καὶ κοσμίους εἶναι περὶ τοὺς λόγους. {u9} τίς ἐστι βέλτιστος, τούτῳ χείρους ἀπεργάζοιτο, ἄλλως τε καὶ πρὸς αὐτὰ ταῦτα ἃ βέλτιστός ἐστιν.', [.56,.105,.97,.34], 'ἤδη συγκεχωρήκασιν.', 'ἃ βέλτιστός ἐστιν.'),
  ('ἀλλὰ μὴν ὡς αὐτὸ ἂν ἀν', ' ἀλλὰ μὴν ὡς αὐτό γε', [.56,.105,.97,.34], 'ἀλλὰ μὴν ὡς αὐτό γε', 'αὐτό γε'),
  ('1276R.','',[.56,.105,.97,.34],None,None,'marginal-reference','1276R.'),
  ('εἰ ταῦτα διασφύρομεν.', ' ἄτιμον {u0} λέγειν, οὐδ’ εἰς ὄνειδος φέρον, οὐδὲ κατηγορίας ἄξιον οὐδέ γε συγγνώμης ἀλλά τινος κρείττονος, {u1} ἂν τοὺς λογίους θεοὺς εἰ ζητοίην ἀποδεικνύναι. πλήν γε τοσοῦτ’ ἂν εἴποιμι· ἐμοὶ γὰρ εἴη, εἴ τις ἄλλος δυσχεραίνει, καὶ τρέπει τὸ ἅπαν εἰς ἐμέ· καὶ οὐ μέμφομαι τῷ δαίμονι· ὡς ἐγὼ δεξαίμην {u2} λέγειν μετὰ χρηστοῦ βίου καὶ σώφρονος, εἰς ὅσον οἷόν τε, κάλλιστα ἀνθρώπων μᾶλλον ἢ μυριάκις Δαρεῖος ὁ Ὑστάσπεω {u3}· καὶ μικρά μοι πάνθ’ ὡς ἀληθῶς πρὸς τοῦτο ἤδη φαίνεται. οἶδα δὲ καὶ τὰ Πλάτωνος πράγματα, εἰ μὴ τετυφώμεθα, οὐδὲν ἄλλο σχεδὸν ὄντα ἢ λόγους, καὶ συγχαίρω τῆς λέξεως αὐτῷ· κἂν με προσπαίζων οὑτωσὶ πείθῃ μὴ πάνυ τούτου φροντίζειν, οὐ πάνυ πείσομαι, ἀλλ’ εἴσομαι “σφόδρα σπουδάζοντα, καὶ τηνικαῦτα μάλιστα, ἡνίκα ἂν ὡς παίζων λέγῃ. ὥστε τὸν οἴκοι θησαυρὸν διαβάλλοιμεν ἄν, εἰ ταῦτα διασύροιμεν.', [.56,.17,.97,.43], 'ἄτιμον τὸ δύνασθαι', 'εἰ ταῦτα διασύροιμεν.'),
  ('τὰ οἶκον διαβαλλόντων.', ' παροιμία. τείνεται δὲ ἐπὶ τῶν τὰ οἰκεῖα διαβαλλόντων.', [.56,.385,.97,.45],None,None,'unclassified-small-type'),
  ('εἰεν.', ' ἀλλ’ ὑπὲρ μὲν τούτων οὐδὲ λέγειν ἄξιον, ἀλλὰ τοσούτῳ ἧττον, ὅσῳ περ ἂν ᾖ κρεῖττον τὸ {u4} λέγειν. εἶεν.', [.56,.385,.97,.49], 'ἀλλ’ ὑπὲρ μὲν τούτων', 'λέγειν. εἶεν.'),
  ('φήσω τις.', ' εἶτα τὸν οὕτως ὀξὺν καὶ ἄγρυπνον καὶ ἡδίστα ἂν εἶπον ὑπόπτερον, τοῦτον ἢ ἀργεῖν αὐτὸν ἢ ἑτέρους ἐθίζειν ἐγὼ πειθῶ; οὐκ ἄρα {u5} δόξω τῶν πραγμάτων οὐδέν· ὅστις γε μὴ ὅτι Ἀθηναίοις ἀλλ’ οὐδὲ τοῖς πολεμίοις ἀργεῖν ἐπέτρεπεν, ἀλλὰ κἀκείνους ἐποίησε μεταβαλεῖν τοὺς τρόπους· τοσαύτας ἀνάγκας αὐτοῖς περιέστησε {u6}. καὶ τὸ δικαίως οἷς ἐποίει προσῆν, ἔφη Δημοσθένης. ἀλλ’ ὅμως Πλάτων ᾐτιάσατο αὐτὸν ἀργοὺς καὶ δειλοὺς πεποιηκέναι. ὁ Κρὴς δὲ τὸν πόντον, φήσει τις.', [.56,.445,.97,.65], 'εἶτα τὸν οὕτως', 'δειλοὺς πεποιηκέναι.'),
  ('τὴν θάλασσαν.', ' παροιμία ἐπὶ τῶν προσωποποιῶν τὸ ἀργοῦν· οἱ γὰρ Κρῆτες {u7}. λέγεται δὲ καὶ {u8} τὴν θάλασσαν, καὶ ὁ Σικελὸς τὴν θάλασσαν.', [.56,.605,.97,.695],None,None,'unclassified-small-type'),
  (None,' ὥσθ’ οἱ μὲν ἄλλοι τοῖς παροῦσι τούτοις ἠθύμουν, ὁ δὲ καὶ',[.56,.605,.97,.73], 'ὥσθ’ οἱ μὲν ἄλλοι', 'ὁ δὲ καὶ')],
}
UNCERTAINTIES={
 (159,1):[
 ('ἀπένους, σῦμα.','ἄκουσον, σίγα.','The last two words of this inset gloss are not independently resolved. No counterpart for this gloss is present in the pinned digital witness; preserve the original display and the apparent scan reading separately.'),
 ('σκέπτεσθι','σκήπτεσθαι','The compact sigma/theta ending and preceding vowel remain unresolved independently.'),
 ('ἴχνοὺν','ἰσχυρὸν','The compact σχ group and subsequent letters remain unresolved independently.'),
 ('ἴτω αἰῶνος γενόμεν','οὕτω σεμνὸς γενοίμην','The compact initial particles and verbal ending remain unresolved independently; the bounded digital witness gives ἔτω σεμνὸς γενοίμην.'),
 ('ἐνδιαλέχει','ἐνδείξασθαι','The compact sigma/theta group and medial letters remain unresolved independently.'),
 ('εἰ τι μίμησιν','εἴ τι μέμφεσθ’','The compact sigma/theta group and word ending remain unresolved independently; digital εἴ τι μέμφεθ’ is a different spelling.'),
 ('ὑπερχὴ','ὑπερσχῇ','The sigma component of the compact σχ glyph remains unresolved independently.')],
 (159,2):[
 ('τὸ δύνα.ἦ','τὸ δύνασθαι','The compact sigma/theta group and extracted internal punctuation remain unresolved independently.'),
 ('αἰχνοῦσιν','αἰσχυνοίμην','The compact σχ group and final letters remain unresolved independently.'),
 ('ἂν δύνα.ἦ','ἂν δύνασθαι','The compact sigma/theta group and extracted internal punctuation remain unresolved independently.'),
 ('γενέ.ἦ','γενέσθαι','The compact sigma/theta group and extracted internal punctuation remain unresolved independently.'),
 ('δύνα.θαι','δύνασθαι','The sigma component of the compact σθ glyph remains unresolved independently.'),
 ('ἐπίσκα.ἦ','ἐπίστασθαι','The compact στ/σθ groups and extracted internal punctuation remain unresolved independently.'),
 ('κινεῖ.ἦ','κινεῖσθαι','The compact sigma/theta group and extracted internal punctuation remain unresolved independently.'),
 ('ἰπτεροδύλασσοι','ἠπειροθάλασσοι','The compact compound and initial vowel remain unresolved independently. This inset note is absent from the pinned digital witness.'),
 ('ὁ σπουδὴς ἄργον','ὁ σπουδῆς ἀργεῖν','The compact noun and infinitive letters remain unresolved independently. This inset note is absent from the pinned digital witness.'),
 ('ἂν δ’ ἂν ἤ','ὃ γὰρ ἂν ᾧ γέ','The compact first relative and particles remain unresolved independently; retain the original display rather than silently adopting the bounded digital wording.')],
}
LEADING_FRAGMENTS={}


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
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
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
                    segment['evidence']+=(' This is an isolated marginal reference label; the body projection omits it.'if role=='marginal-reference'else' This is part of the centered, letter-spaced source-identification heading between extracts. Its placement and type establish the heading boundary without establishing authorship; preserve its literal text and exclude it from lexical admission pending attribution.'if role=='unclassified-heading'else' This inset small-type explanatory paragraph has distinct boundaries within the surrounding larger-type source text; its typography establishes boundaries without establishing authorship. Exclude it pending attribution.')
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
