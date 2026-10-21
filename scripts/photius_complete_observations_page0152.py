"""Complete direct scan observations for retained historical physical page152."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT = '2026-10-21T12:36:45Z'
CHUNKS = {
 (152,1):[
  ('εἰπεῖν δεῖ;', 'γος τοσοῦτον, καὶ τῷ τυράννῳ συνεῖναι δοκεῖν {u0}, ὡς ἔχων παραμυθίαν τὸ χρῆμα τῆς διατριβῆς, ἢ Δίωνα μένειν οἴκοι καὶ τῆς οὐσίας κρατεῖν ἦν. τὴν δ’ αὑτοῦ τις οἰκῶν καὶ τοῖς αὑτοῦ πολίταις καὶ γονεῦσι καὶ ἀδελφοῖς εἰ τὴν ὅπως μὴ ἀδικήσονται φυλακὴν ἔχοι, καὶ σώζοι καὶ τούτους καὶ ἑαυτόν, καὶ νὴ Δία γε εἰ τοῦτ’ αὐτὸ τύραννον {u1} τινα μέλλοντα καὶ Διονυσίῳ προσόμοιον οἷός τε εἴη κωλῦσαι, καὶ παρελθὼν λόγῳ τὰς πράξεις, καὶ τὴν ἐκ τῶν νόμων ἄδειαν ἅπασι βεβαιῶσαι, ἔπειτ’ οὐδὲν σπουδαῖον τοῦτ’ εἶναι φήσομεν, οὐδ’ ἐπαινεῖν χρὴ τὴν τοιαύτην εἴτε τέχνην εἴτε μηδὲ τέχνην εἰπεῖν δεῖ;', [.045,.112,.425,.335], 'τοσοῦτον, καὶ τῷ τυράννῳ', 'εἰπεῖν δεῖ;'),
  ('τῶν ἱκανῶν', ' ὅτι νὴ Δία οὐ μέγα τοῦτ’ ἦν κακόν, τὸ ἀδικεῖν, τὸ δὲ ἀδικεῖσθαι πρᾶγμα οὐδέν. ἐγὼ {u2} αὐτὸς ἐπέγκλημα δή που τοῦτο ποιοῦμαι, εἴ που καὶ ὁπωσοῦν ᾠήθη δεῖν εἰς Σικελίαν Πλάτων ἐλθεῖν {u3} ἕνεκα αἰτίας, ἐφ’ οἷς ἄλλος προφέρει τι τοιοῦτον εὖ φρονεῖν ἡγοῦμαι, οὔθ’ ὅλως ἔξω τῶν εἰς τὸν λόγον ἡκόντων οὐδὲν περιεργάζομαι· μὴ τοσοῦτον μηδὲν ἄξιον ἔξω νικητήριον. ἀλλ’ ἃ αὐτὸς ἔπραξε καὶ ἃ τίνων ἔπραξε χάριν αὐτὸς καθαρῶς εἴρηκε, ταῦτα συμβαίνειν φημὶ τοῖς ὑπὲρ τῆς ῥητορικῆς λόγοις. καὶ μὴν ὅσῳ κάλλιον φρόνησις ἀνδρείας, τοσούτῳ ῥητορικὴ τῆς κατὰ πόλεμον εὐψυχίας. εἰ γὰρ δεῖ συνελόντα εἰπεῖν, οὐδέν ἐστιν ἄλλο ῥητορικὴ ἢ φρόνησις λόγων δύναμιν προσειληφυῖα, ὡς μὴ μόνον “αὐτὸς ἔρδειν τὰ βέλτιστα ἀλλὰ καὶ ἑτέρους πείθειν ἔχοι. ἡγοῦμαι μὲν τοίνυν καὶ ταῦτα πίστεις ἱκανὰς ἔχειν τῆς ἀληθείας, εἰ μὴ καὶ πλείους ἄρα τῶν ἱκανῶν·', [.045,.30,.425,.535], 'ὅτι νὴ Δία', 'τῶν ἱκανῶν·'),
  (None, ' εἶμι δ’ ἐπ’ αὐτὸν ἤδη τὸν κολοφῶνα τοῦ Πλάτωνος, ὡς ἄν τις εἴποι, ῥημάτων. {u4} γὰρ μόνον ἐξ ὧν ἐλέγχεται βούλομαι φανῆναι μαρτυροῦντα αὐτόν, ἀλλὰ καὶ ὥσπερ ἂν εἰ καὶ {u5} αὐτὸς ἐμαρτύρει τῇ {u6} φωνῇ. {u7} ὅτ’ ἀδικεῖν μὲν οὐκ ἐπηνάγκαζεν, ἀδικεῖσθαι δ’ οὐκ ἐᾷ, ὡς δ’ ἐκ τῷ λόγῳ συνέβαινεν, οὐδέτερον τούτων ἐᾷ, οὔτ’ ἀδικεῖν οὔτ’ ἀδικεῖσθαι, εἰ μὲν καὶ τῆς φιλοσοφίας ὁ αὐτός ἐστιν ὅρος, φιλοσοφία τις οὖσα ἡ ῥητορικὴ φαίνεται· εἰ δὲ ἐξαρκεῖ τῇ φιλοσοφίᾳ μηδ’ ἀδικεῖν, ἡ ῥητορικὴ τελεώτερον.', [.045,.485,.425,.68], 'εἶμι δ’ ἐπ’ αὐτὸν', 'ἡ ῥητορική τελεώτερον.')],
 (152,4):[
  ('πρὸς τῷ δεσπότῃ ἐχθρὸν ἐστίν.', 'τίς γὰρ οὐκ οἶδεν ὅτι ῥητορικὴ καὶ τυραννὶς τοσοῦτον ἀλλήλων κεχώρισται, ὅσον τῷ πείθειν τὸ βιάζεσθαι; ἀλλὰ μὴν ταῦτά γε οὐδείς ἐστιν ὃς ἂν τὴν ἐναντίαν φύσιν εἰπὼν ἔχειν αἰσχυνθείη. πῶς γὰρ ὁμοῦ μὲν κολακεύουσιν οἱ ῥήτορες, ὁμοῦ δ’ ἐν τοῖς δυνάσταις εἰσίν; οἱ δ’ αὖ τύραννοι ἀπέχουσι τοσοῦτον τοῦ κολακεύειν ὥστε βίᾳ πάντας ὠθοῦσι, καὶ οὐδενός ἐστι παρ’ αὐτῶν τυχεῖν οὐδὲ τῶν μετρίων, “μή τί γε δὴ τῆς ὑπὲρ τὸ προσῆκον θεραπείας·” ὥσθ’ ὁ τύραννος μικροῦ δεῖν καὶ τὸ τοῦ δεσπότου μέτρον παρελήλυθε. καὶ κόλακος μὲν [γὰρ] οὐδέν ἐστι δή ποτε ταπεινότερον, οὐδ’ ὅ τι μᾶλλον ᾕρηται δουλεύειν· τυράννου δὲ οὐδὲν ἂν εἴποις ἀγριώτερον, οὐδ’ ὅ τι μᾶλλον πρὸς τῷ δεσπόζειν ἐθέλειν ἐστίν.', [.415,.112,.80,.335], 'τίς γὰρ ἐκ οἶδεν', 'ἐθέλειν ἐσίν.'),
  ('αὐτὸς ἀρχὴ κατ’ ἀρχὴν τὰ πράγματα,', ' ὥστε εἰ μὲν κολακεία ἡ ῥητορική, τὰ τῶν τυράννων ἐγκλήματα οὐ πρὸς αὐτῆς ἐστιν. εἰ δ’ ὁμοῦ τῇ τυραννίδι τὴν κολακείαν μεγάλοις τοῖς ὁρίοις παρελήλυθεν, οὔκουν τά γε ἕτερα πάντως ἤδη ψευδῆ. τοσοῦτον γὰρ ἡ ῥητορικὴ κεχώρισται δυναστείας ὅσον, εἰ καὶ τοῦτ’ εἰπεῖν δεῖ, Πλάτων Διονυσίου. φανήσεται γὰρ οὔθ’ ὅπου ῥητορικὴ σώζεται τύραννος ἐγγινόμενος, μέχρις ἂν σώζηται λόγῳ, οὔτ’ αὖ ἔνθα τυραννὶς κρατεῖ ῥητορικὴ περίεστιν· ἀλλ’ ὅ τε ῥήτωρ πάντα πράττων ὅπως μηδεὶς τύραννος ἐγγένηται, τό τε αὑτῷ καὶ τὸ κοινὸν ὁμοῦ προορῶν, ὅπως μηδεὶς αὐτὸν τῷ λόγῳ πείθειν παρελόμενος αὐτὸς ἄγῃ κατ’ ἀρχὴν τὰ πράγματα,', [.415,.30,.80,.535], 'ὥσε εἰ μὲν κολακεία', 'κατ’ ἀρχὴν τὰ πράγματα,'),
  (None, ' οἵ τε τύραννοι σκοποῦντες καὶ φοβούμενοι τῶν πάντων οὐδὲν μᾶλλον ἢ μή τις ἐγγένηται λέγειν καὶ πείθειν δυνατός, ὅστις συναγαγὼν τὰ πλήθη καὶ σύμβουλος καὶ μηνυτὴς τοῦ προσήκοντος γινόμενος ὁμοῦ τῆς ἀρχῆς καὶ τῆς ἐξουσίας ἀκύρους αὐτοὺς καταστήσῃ. διόπερ τὴν ἔχθραν ἀναγκαίως ἀλλήλοις ἔχουσιν· ἡ γὰρ τῶν ἑτέρων σωτηρία καὶ δύναμις μὴ εἶναι {u3} πῶς ἂν τἀναντία (φησὶν) ἀλλήλοις οἱ ῥήτορες λέγουσιν; ἔστι μὲν οὐκέτι ταῦτ’ ἐν εἰρημένοις ὑπὸ Πλάτωνος· ὅμως δὲ ὑπὲρ τοῦ πανταχῇ διακαθᾶραι τὸν λόγον μηδὲ τοῦθ’ ἡμῖν ἀνεξέταστον {u0}. καὶ τοῦτ’ οὖν {u1} πάντων ἂν {u2}, ὡς ἐν ψεύδεσιν, ὧν ἐκεῖ-', [.415,.485,.80,.68], 'οἵ τε τύραννοι σκοπῶντες', 'ὧν ἐκεῖνος')],
}
UNCERTAINTIES={
 (152,1):[
 ('ἐκ ἔργους','οὐκ ἔφυγες','The compact negative and adjacent letters are not independently resolved in this scan; digital ἐκ ἔφυγες differs materially.'),
 ('ἵσθαι','ἔσεσθαί','The compact passive ending does not independently establish all sigma/theta letters; retain original display with the digital alternative.'),
 ('γὰρ ἂν',"γ’ οὐκ",'The compressed negative/particles remain uncertain; digital γ’ ἐτ’ is also defective and not decisive.'),
 ('ἦν— νούσων','ἠσινοσῶν','The tightly set initial letters of the word divided across source lines remain uncertain; digital ἤσινοσῶν is a differing alternative.'),
 ('ὁ','οὐ','The compact initial ου ligature is uncertain independently; retain the original display rather than adopting digital ἐ.'),
 ('παρασχεῖν','παραστὰς','The compact στ glyph and participial ending are unresolved independently; digital παρασὰς loses a letter.'),
 ('ἑαυτῷ','ἑαυτοῦ','The compact pronoun ending and subscript mark are unresolved at this source resolution; digital ἑαυτῶ is retained independently.'),
 ('ὅθεν','ἑκὼν','The initial breathing and medial letters remain uncertain independently; digital ἐκᾶν is a differing alternative.')],
 (152,4):[
 ('ἀφελθῶ','ἀφείσθω','The compact σθ glyph and preceding letters are not independently resolved; do not infer the sigma from grammar or digital spelling.'),
 ('ἰχυρότατον','ἰσχυρότατον','The sigma component of the compact σχ glyph is unresolved independently.'),
 ('χεῖρον','σχεδόν','The compact σχ group and following letters remain unresolved independently; digital σχεδόν alone cannot authorize the change.'),
 ('τοῖς ἑτέροις ἐστὶ τὴν ἀρχήν.','τοὺς ἑτέρους ἐς τὴν ἀρχήν.','The case endings and compact particle before τὴν ἀρχήν are not fully resolved independently; digital τοὺς ἑτέρους ἐπὶ τὴν ἀρχήν differs from the scan and is retained separately.')],
}
LEADING_FRAGMENTS={(152,1):'γος'}


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
