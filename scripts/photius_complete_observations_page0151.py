"""Complete direct scan observations for retained historical physical page151."""
from copy import deepcopy
import hashlib
import json
import re

REVIEWED_AT = '2026-10-21T12:34:45Z'
CHUNKS = {
 (151,1):[
  ('ἐπιάρχειν.', 'τὴν ῥητορικὴν δείκνυμεν εὑρεθεῖσαν, καὶ τὴν “αὐτὴν καθαρῶς τάξιν ἔχουσαν τοῖς νόμοις, ὡς δέδεικται, ἔχει τὴν αὐτὴν {u5} (ὡς ἔοικεν) ὁ ῥήτωρ· τὸ μὲν ἀδικεῖσθαι {u0}, τὸ δ’ ἀδικεῖν βεβαιώσει, ἀλλ’ οὐδὲν οὕτως ὡς τὸ ἀδικεῖν κωλύσει. οὐ γὰρ μόνον τῶν εἰς αὑτὸν χρήσει πρόνοιαν, ἀλλ’ ὅπως μηδ’ ἄλλος πείσεται κακῶς, εἴπερ ὧν τοὺς νόμους χάριν, τούτων καὶ τὴν ῥητορικὴν {u1} νενίκηκεν. ἀλλὰ μὴν ὅ γε ἑτέρους τὰ δίκαια πράττειν ἐπαναγκάζων πολὺ πω πρότερον αὑτός γε παρασκευάσεται. {u2} μὲν τῷ δικαίῳ, τοῦ δὲ καταλύειν τὸ δίκαιον αὐτὸν πρῶτον ὑπάρχειν.', [.21,.112,.585,.335], 'τὴν ῥητορικὴν δείκνυμεν', 'αὐτὸν πρῶτον ὑπάρχειν.'),
  ('τῷ βίῳ.', ' οὐ μὴν ἀλλ’ εἰ τοῦτο Πλάτων {u3}, ὡς οὐ πολλήν τινα οὐδ’ ἀξίαν σπουδῆς οὐδὲ λόγου χρείαν ἡ ῥητορικὴ παρέχεται, ὅτι οὐ τηλικοῦτόν ἐστι τὸ ἀδικεῖσθαι κακὸν ἡλίκον τὸ ἀδικεῖν, τί κωλύει καὶ τοὺς νόμους αὐτὸν ἅπαντας τοῖς αὐτοῖς τούτοις διαγράφειν λόγοις; ἀλλ’ ὥσπερ ἑταιρείας καταγνωσθείσης, μετὰ καὶ τῶν ταῦτα συμβεβουλευκότων νόμων ἐξελαθήσεται. καὶ τότε ῥητορικὴν ἐκπέμψομεν καὶ προπηλακιῶμεν, ὅταν καὶ τοὺς νόμους [συνεκπέμψαι καλῶς ἡμῖν ἔχῃ] ἐκβάλλωμεν τῆς πόλεως καὶ τοῦ βίου.', [.21,.30,.585,.535], "οὐ μὴν ἀλλ' εἰ τοῦτο Πλάτων", 'τοῦ βίου.'),
  (None, ' ἀλλ’ ὦ δαιμόνιε καὶ πάντα σὺ θαυμαστὰ εὑρίσκων, εἰ μηδέν ἐστι πρᾶγμα τὸ ἀδικεῖσθαι, μηδ’ ἡ τοῦτο κωλύουσα δύναμις μηδενὸς ἀξία λόγου, μηδ’ ὁπόσα ἔστι καὶ γίνεται μὴ δι’ αὐτῆς μηδὲν χρηστόν, ἀλλ’ οὕτως ἄτιμον καὶ ἀνελεύθερον ὥστ’ εἶναι μόριον κολακείας καὶ σκιᾶς, τί χάριν ταύτην οἰκίζων τὴν ἐν τῇ βίβλῳ πόλιν καθίστης αὐτῇ πολιτείαν, ἀφ’ ἧς μηδ’ ὁτιοῦν πείσεται, καὶ τὸ μάχιμον χωρὶς τῶν ἄλλων {u4} κελεύεις, τιμὴν τὴν πρώτην ἀποδούς, ἵνα μήτι πάθῃ μηδ’ ὑπό τινων ἀδικηθῇ πολεμίων; εἰ γὰρ ἐξήρκει μὴ ἀδικεῖν, τί δέδοικας, εἰ πρὸς τοῦτό γ’ αὐτὴν παρεσκεύασας; εἰ δὲ δὴ καὶ χεῖρον τοῖς ἀδικοῦσιν, ὅταν μὴ διδῶσι δίκην, καὶ χρὴ δὴ κατὰ σὲ καὶ αὐτὸν ἑαυτοῦ κατήγορον, ὅταν ἀδικήσῃ, γίνεσθαι καὶ παίδων καὶ πατρὸς αὐτοῦ, τοὺς δ’ ἐχθροὺς ἐᾶν, τί σὺ συνεύχῃ τοῖς πολεμίοις', [.21,.485,.585,.68], "ἀλλ' ὦ δαιμόνιε", 'τοῖς πολεμίοις')],
 (151,3):[
  ('ἐποίησε.', 'ἐπελθεῖν καὶ λαβεῖν τὴν πόλιν, καὶ νὴ Δία τοὺς μὲν ἐν ἡλικίᾳ πάντας κατακόψαι, καὶ ταῦτα πρὸς τοῖς βωμοῖς, παῖδας δὲ καὶ γυναῖκας {u0} πέρα, εἰ βούλει, Γαδείρων, τὰ δὲ ἱερὰ συλήσαντας κατασκάψαι πάντα, μὴ λιπεῖν δὲ μηδὲ τοὺς τάφους ἀθῴους τῆς ἑαυτῶν πλεονεξίας, ἵν’ ἀδικήσαντες τὰ μέγιστα ἐν τοῖς μεγίστοις δὴ κακοῖς ὦσι, μὴ δόντες δίκην. ἀλλὰ τοσοῦτον ἀπέχεις τοῦ ταῦτα συμπράττειν, ὥστε κωλύεις καὶ βίον ἐν τοῖς ὅπλοις εὕρηκας, ἵνα μήτι τοιοῦτον γένοιτο· κἂν τις ἐγγένηται προδότης, {u1} κελεύεις οὐδὲ κηρύττειν, ἀλλὰ “ταὐτὰ τοῖς ἄλλοις νομοθέταις περὶ τούτων νομίζεις. εἰπέ, πρὸς Διὸς τερασίου, τί χρὴ περὶ τούτων ἡμᾶς νομίζειν; εἶεν, ὦ γενναῖε· νόμους δὲ δὴ τί χάριν ἡμῖν ἐτίθης.', [.57,.112,.95,.335], 'ἐπελθεῖν καὶ λαβεῖν', 'ἡμῖν ἐτίθης.'),
  ('προτιμήσομαι.', ' εἰ γάρ, ὦ τάν, τὸ δίκην λαμβάνειν καὶ τὸ μὴ ἐᾶν ἀδικεῖν οὐχ ἕν τι τῶν σπουδαίων ἦν, τί χάριν ταῦτα πραγματεύῃ, καὶ σκοπεῖς ὅπως μηδείς [πω τῶν ἐν τῇ πόλει] ἀδικήσεται; καὶ μὴν ἐν μὲν οἷς ἡμεῖς λέγομεν, καὶ τοῖς ἄλλοις συνδοκεῖν ἔστι καὶ τῷ Πλάτωνι πρόσεστιν· ἃ δ’ οὗτος ἐνταῦθα εἴρηκεν, οὐ μόνον τοῖς τῶν πραγμάτων λόγοις ἀλλὰ καὶ τοῖς αὐτοῦ Πλάτωνος ἐξελέγχεται καὶ λόγοις καὶ βουλήμασιν. ἐκείνων μὲν ὀρθῶς ἔχειν συγχωρουμένων, καὶ ἡ παρὰ τῶν ἄλλων μαρτυρεῖ δόξα καὶ ψῆφος ὀρθή· ταῦτα δὲ εἰ δοίημεν κρατεῖν, ἄπεισι τὸ ὁτῳοῦν συνδοκεῖν τῶν ἄλλων. “{u2} δὲ τὸ {u3} τὸ μηδενὶ καὶ μηδὲ Πλάτωνι συνδοκεῖν, ὡς οὗτος ἀλλαχοῦ. οὐκοῦν οὐ τὴν παρὰ τούτου μαρτυρίαν διὰ τὴν παρὰ τῶν ἄλλων φευξόμεθα, ἀλλὰ τῇ τῶν ἄλλων τὴν παρὰ τούτου προσθησόμεθα.', [.57,.30,.95,.535], 'εἰ γάρ, ὦ τάν,', 'προσθησόμεθα.'),
  (None, ' ἡγοῦμαι μὲν τοίνυν κἂν τούτοις τὴν ἔργῳ μαρτυρίαν {u4}· τὸ γὰρ δὴ λόγοις πρὸς λόγους ἀγωνιζόμενον λόγοις ἑτέροις σπουδαίοις μαρτυροῦντα ἀποφαίνειν τὸν ἀντίπαλον τὴν ἔργῳ {u5} μαρτυρίαν ἐστίν. οὐ μὴν ἀλλ’ ἔτι καὶ προσωτέρω προελθεῖν βούλομαι, ἵνα, ἐπειδὴ τιμᾷ τὸ ἕνα ἐπιψηφίζειν καὶ αὐτὸν πρὸς ὃν ἂν οἱ λόγοι γίγνωνται, καὶ λόγῳ καὶ ἔργῳ σύμψηφον ὄντα αὐτόν μοι δείξω. σὺ μὲν ξένῳ χάριν Συρακουσίῳ, κοινοῦ τῆς πατρίδος ἐχθροῦ, ἔπλεις οὐχ ἅπαξ ἀλλὰ καὶ δὶς καὶ τρίς, ἐν γήρᾳ, πέλα-', [.57,.485,.95,.68], 'ἡγέμαι μὲν τοίνυν', 'ἐν γήρᾳ, πέλαγος')],
}
UNCERTAINTIES = {
 (151,1):[
 ('φεύξῃ','φεύξεσθαι','The compact ending of this verb does not independently establish all sigma/theta letters. The digital reading is preserved without treating it as authority.'),
 ('εἰρήχεν','εὑρέσθαι','The compressed sigma/theta group in the infinitive remains unresolved independently.'),
 ('ὁ γὰρ ἔχων σοφίαν','οὐ γὰρ ἐγχωρεῖ βοηθεῖν','The tightly set initial negative and following verbs are not sufficiently resolved independently; digital εἰ γὰρ ἐγχωρεῖ βοηθεῖν conflicts with the apparent scan initial.'),
 ('ἔχρηζεν','ἰσχυρίζεται','The compact σχ ligature is not independently resolved; do not infer its sigma component from grammar or digital spelling.'),
 ('ἱδρύθη','ἱδρῦσθαι','The sigma/theta group and terminal letters remain uncertain independently.'),
 ('ὁ μόνον','οὐ μόνον','The compact ου ligature before μόνον is not independently resolved; retain original display and the separate digital reading.')],
 (151,3):[
 ('ἐξανθραποδίσαι. Ἡγ','ἐξανδραποδισθῆναι','The compact passive sigma/theta ending cannot be independently resolved; retain the exact original display and the digital alternative.'),
 ('τούτον δὲ σεφανὺν','τοῦτον ἐκστεφανῶν','The prefix and compact στ glyph in this participle are uncertain; digital ἐκσεφανῶν loses a character and is not decisive.'),
 ('ἰχνώτερον','ἰσχυρότερον','The sigma component of the compact σχ glyph remains independently uncertain.'),
 ('ἑ ἄπασα ἑ Πλάτωσι','οὐχ ἅπασι καὶ Πλάτωνι','The compact initial negative and the name divided at the printed line boundary remain uncertain. Digital ἐξ ἅπασι καὶ τινι is an independently differing reading.'),
 ('παρέχειν','παρέχεσθαι','The compact sigma/theta group is not independently established; do not expand solely from the digital witness.'),
 ('παρχεῖν','παρέχεσθαι','The compact sigma/theta group is not independently established; preserve the original display and digital alternative.')],
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
