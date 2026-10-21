"""Complete direct scan observations for retained historical physical page153."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT = '2026-10-21T12:40:00Z'
CHUNKS={
 (153,1):[
  ('680Π.','',[.16,.105,.585,.20],None,None,'marginal-reference','680H.'),
  ('τὴν ταύτην.', 'νος εἴρηκεν, ὅτι οἶμαι καὶ ἡμῖν αὐτοῖς ἀπαντῶμεν “ἐν τῷ λόγῳ, αὐτὸ τοῦτο κἀγὼ νῦν πεποίηκα. ἀλλ’ οὐδὲν μᾶλλον ὅ γε ἐξ ἀρχῆς λόγος διαφθείρεται, ἐπεὶ καὶ οἱ φιλοσοφεῖν οὕτω λεγόμενοι οὐ τοῖς αὐτοῖς λόγοις ἅπαντες δή που χρῶνται, ἀλλὰ καὶ τοῖς ἐναντιωτάτοις ἀλλήλοις· ἀλλ’ οὐδὲν κωλύει κατὰ τοὺς τυγχάνοντας τῆς ἀληθείας φιλοσοφίαν εἶναι καλόν. {u0} αὐτὸ ἑαυτῷ. πῶς οὖν, ἂν φαίη τις, ἢ φιλοσοφεῖν {u1} φήσομεν τἀναντία λέγοντας, ἢ τὸ φιλοσοφεῖν εἶναι καλόν; οὕτως ὡς ἔφην. ἴδοις δ’ ἂν καὶ κυβερνήτας ἐναντία ἀλλήλοις ναυμαχοῦντας· ἀλλ’ ὅμως τῆς κυβερνητικῆς ἐστι σώζειν τὴν ναῦν.', [.21,.112,.585,.335], 'εἴρηκεν, ὅτι οἶμαι', 'σώζειν τὴν ναῦν.'),
  (None, ' οὕτω τοίνυν καὶ ὅταν οἱ ῥήτορες ἀλλήλοις ἐναντία, ὡς ἄν τις φαίη, λέγωσιν, οὐ κωλύεται τὸ ἐξ ἀρχῆς κεφάλαιον τῆς ῥητορικῆς, ἀλλὰ τὸ συμβαῖνον τῷ λόγῳ χρὴ σκοπεῖν, μεμνημένους ὧν ἕνεκα εὑρέθη. [εὑρέθη δὲ τὸ λέγειν ὑπὲρ τῶν δικαίων.] ὁ μὲν οὖν ὑπὲρ ῥητορικῆς λόγος οὗτος.', [.21,.30,.585,.535], 'οὕτω τοίνυν καὶ ὅταν', 'λόγος οὗτος.')],
 (153,2):[(None,'(ὁ μὲν αʹ λόγος ὑπὲρ ῥητορικῆς μόνον ἦν· οὗτος δὲ καὶ ὑπὲρ ῥητορικῆς καὶ ὑπὲρ ῥητόρων.)',[.21,.30,.585,.535],"(ὁ μὲν α' λόγος",'ὑπὲρ ῥητόρων.)')],
 (153,3):[
  ('συγχωρούντων μὲν γ-', 'ἐπεὶ δὲ καὶ Μιλτιάδου καὶ Θεμιστοκλέους καθήψατο καὶ Κίμωνος καὶ Περικλέους, οὐ πρὸς τὸ βέλτιστον φάσκων προσῆναι τῆς πόλεως, ἔτι μὲν οὖν ἴσως οὐδὲν κατεπεῖγον περὶ τούτων νῦν {u0}. οὗτοι μὲν γάρ, εἰ δίκαια Πλάτων αὐτῶν κατηγόρηκε, δικαίως ἂν φαῦλοι νομίζοιντο· ῥητορικὴ δέ, εἰ καὶ πάντων μοχθηροτάτους τούτους θείημεν, οὐδὲν μᾶλλον ἐλέγχεται. συγχωρούντων μὲν οὖν', [.21,.45,.585,.625], 'ἐπεὶ δὲ καὶ Μιλτιάδε', 'συγχωρέντων μὲν οὖν'),
  ('1260R', '', [.16,.49,.585,.60],None,None,'marginal-reference','1260R.'),
  (None, ' ἡμῶν “ὅ γε ὑπὲρ ῥητορικῆς οὐκ ἀπόλωλε λόγος. εἰ δὲ δὴ καὶ περὶ τούτων ἐλέγχοιτο {u1} τῷ λόγῳ κεχρημένος, πανταχῇ {u2} φιλονεικῶν. τοῦτ’ ἐστὶ προὔργου τὸ καὶ περὶ τούτων εἰπεῖν.', [.21,.485,.585,.68], 'ἡμῶν ὅ γε ὑπὲρ ῥητορικῆς', 'τὸ καὶ περὶ τούτων εἰπεῖν.')],
 (153,4):[(None, 'αὐτοὶ παράδειγμα τοῖς ἄλλοις γινόμενοι τῷ πῶς δεῖ καρτερεῖν, ἐν αὐτοῖς τοῖς δεινοῖς καὶ ταῖς ἀκμαῖς τῶν κινδύνων τὴν ἡμετέραν αὐτῶν, εἰ συγχωρεῖς εἰπεῖν, ἀρετὴν ἐπιδεικνύμενοι. {u0} ἡμῖν προσφέρεις κολακείαν καὶ διακονίαν, καὶ τὰς ἰδίᾳ τροφεῖα μὴ ἐκτίνοντας φαύλους ἂν εἶναι συμφήσας αὐτὸς ἡμῖν οὐ καλὴν χάριν', [.16,.60,.585,.735], 'αὐτοὶ παράδειγμα', 'οὐ καλὴν χάριν')],
 (153,5):[
  ('κἂν τούτοις ἂν ἀνάγκη θάτερα ἐφεί· ἢ,', 'ἐκτίνεις τῆς κοινῆς τῶν Ἑλλήνων σωτηρίας καὶ τροφῆς, ἣν σύ τε καὶ οἱ ἄλλοι δι’ ἡμᾶς ἐν ἐλευθερίᾳ τέτραφθε. εἰ ταῦτα λέγοιεν οἱ ἄνδρες, ποίους λαβυρίνθους σοφίας ἀνελίττων ἢ τί λέγων τῶν πάντων οἷός τε γένοιτ’ ἂν ἀντειπεῖν; πᾶσι τοίνυν προτέροις ἐστὶ λόγος πρὸς ταῦτα ἢ Πλάτωνι. διὰ τί; ὅτι ἐν αὐτοῖς τούτοις ἃ πρὸς τοὺς Δίωνος γέγραφεν ἑταίρους, καὶ ἐν οἷς ὁ Δίων αὐτῷ τετελευτηκὼς ὑπόκειται λέγων ὡς ἔμπνους, ἔνεστι ταυτί. τὸ δὲ πάντων ἀτοπώτατον, ὅτι χρῆται μὲν τούτοις ἐν ἐλέγχῳ τῷ κολακείαν εἶναι τὴν ῥητορικήν, ὡς δὴ τούτους ὄντας ῥήτορας, πάλιν δ’ αὐτὸς αὐτοὺς ἀφίησιν τῆς κολακείας, ὅταν φησὶ γε αὐτὸς ταύτῃ {u0}, ἐν οἷς περὶ ὧν ἔπαθον λέγει. κἂν τούτοις ἂν ἀνάγκη θάτερα {u1}', [.57,.112,.95,.335], 'ἐκτίνεις τῆς κοινῆς', 'θάτερα ψεύδεσθ.'),
  ('ὃς ἐν τριάκοντα τοῖς πονηροτάτοις τῶν Ἑλλήνων πρῶτος ἦν,', ' εἰ μὲν γὰρ ἡ ῥητορικὴ κολακεία, πάντως δεῖ κόλακας τούτους εἶναι, ῥήτοράς γε ὄντας, ὥς φησιν· εἰ δὲ οὐδὲν οὗτοι κολακείᾳ προσήκουσι, ποῦ ῥητορικὴ κολακείᾳ προσήκει διὰ τούτους, ἢ τί τούτων ἔδει τῶν παραδειγμάτων; ᾤμην δὲ οὐδὲ τοῦτο τῶν δικαίων εἶναι, τὰς προαιρέσεις τὰς ἐκείνων ἐξετάζοντας τὰς συμφορὰς αἷς ἐχρήσαντο ὑπολογίζεσθαι. οὐ γὰρ εἰ μὴ κατὰ νοῦν ἀπήλλαξαν, φαῦλοι γεγόνασιν, ἀλλ’ εἰ μὴ τὰ βέλτιστα ἐβουλεύοντο τοῖς πράγμασιν. ἐκεῖνο μὲν γάρ ἐστι τῆς τύχης κατηγορεῖν, τοῦτο δὲ τὴν γνώμην ἐλέγχειν. ἐνθυμοῦμαι δὲ ἔγωγε πῶς {u2} χρή, ὅταν Ἀλκιβιάδην μὲν καὶ Κριτίαν Σωκράτει συγγενομένους, οἳ τοσαύτας καὶ τηλικαύτας αἰτίας ἐσχήκασι καὶ ὑπὸ τῶν πολλῶν καὶ ὑπὸ τῶν ἐπιεικῶν, ὥστε Κριτίᾳ γε οὐδ’ ἐπινοῆσαι ῥᾴδιον ἐξωλέστερον, ὃς ἐν τριάκοντα τοῖς πονηροτάτοις τῶν Ἑλλήνων πρῶτος ἦν,', [.57,.30,.95,.535], 'εἰ μὲν γ’ ἡ ῥητορικὴ', 'τῶν Ἑλλήνων πρῶτος ἦν,'),
  (None, ' τοὺς μὲν οὐ φασι δεῖν ἐν τεκμηρίῳ {u3} ὅτι Σωκράτης τοὺς νέους διέφθειρεν, οὐδ’ εἶναι τὰ ἐκείνων ἁμαρτήματα οὐδ’ ὁτιοῦν πρὸς Σωκράτην τὸν οὐδὲ αὐτὸν ἔξαρνον ὄντα {u4} τοῖς νέοις· εἰ δ’ Ἀθηναίων δῆμος ἐν πολλοῖς καὶ μεγάλοις οἷς καὶ ὑπὲρ αὑτοῦ καὶ ὑπὲρ τῶν Ἑλλήνων διεχείρισεν, ἔσθ’ ἃ μὲν ὀρθῶς καὶ προσηκόντως ἐβουλεύσατο, ἔστι δὲ ἃ καὶ ἐξήμαρτεν εἰς τοὺς προεστηκότας, ταῦτ’ ἀξιοῦσιν αὐτοῖς τοῖς προστάταις λογίζεσθαι. ὥσπερ ἂν εἴ τις καὶ τῷ θείῳ κατηγοροίη τοῖς αὐτοῖς λόγοις, ὅτι χρῆν αὐτῷ τὴν πρόνοιαν εἶναι τοιαύτην ὥστ’ ἀδικίαν καὶ ἀγνωμοσύνην ἀνελεῖν παντάπασιν', [.56,.485,.95,.735], 'τοὺς μὲν ἔ φασι', 'ἀνελεῖν παντάπασιν')],
}
UNCERTAINTIES={
 (153,1):[
 ("ἡ δὴ πῦ διπλῆν ἐστὶν ὁθ' ἐναντίον",'οὐ δή που διπλοῦν ἐστιν οὐδ’ ἐναντίον','The compact negatives and the adjective ending remain unresolved independently; the digital witness has materially differing particles and διπλῆν.'),
 ('ἀμφοτέρως','ἀμφοτέρους','The compact ending remains unresolved independently; digital ἀμφοτέρες does not establish the scan reading.')],
 (153,3):[
 ('διαφέρειν','διαφέρεσθαι','The compact sigma/theta glyph is not independently resolved.'),
 ('ἢ παντὶ πᾶσιν εἰρημένος','ὁ παντάπασιν εὐγνωμόνως','The compact particle and adverb letters remain unresolved independently; digital ἃ παντάπασιν εὐγνωμόνως differs from the apparent scan initial.'),
 ('διεχθήσετ','δειχθήσεται','The compact medial glyph and terminal letters remain unresolved independently.')],
 (153,4):[('τί ἄν','τί οὖν','The tightly set initial words of the question are not resolved independently; preserve original display and the bounded digital reading.')],
 (153,5):[
 ('χρή· ἢ','χρῆσθαι','The compact sigma/theta group remains unresolved independently; preserve the original display with the digital witness.'),
 ('ἐφεί· ἢ,','ἐψεῦσθαι','The compact verb is unresolved independently; digital ψεύδεσθ differs from the apparent scan prefix and ending.'),
 ('ἀνέχεται','ἀνέχεσθαι','The compact sigma/theta group is unresolved independently.'),
 ('ποιήσας','ποιεῖσθαι','The compact sigma/theta group and preceding vowel remain unresolved independently.'),
 ('τὸ μὴ ἀδιαλέγεσθαι','τὸ μὴ διαλέγεσθαι','The letters immediately following μὴ and the compact final glyph remain unresolved independently; digital τὸ μὴ ἐδιαλέγεθ is a separate variant.')],
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
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source line or page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
                if page == 153 and number == 1 and a == len('680Π.') and text.startswith('νος'):
                    fragments.append({'start':0,'end':3,'text':'νος','side':'leading','qualification':'Printed continuation of the word begun on the preceding page; the preceding marginal label is not part of this word. Exclude the suffix from lexical counts.'})
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
                if page == 153 and number == 2:
                    segment['evidence'] += ' This parenthetical transition is printed at normal body size between the end of the first extract and the letter-spaced heading of the second. Parentheses alone do not establish editorial authorship; preserve it as body.'
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
