"""Complete direct scan observations for retained historical physical page157."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:52:50.294120Z'
CHUNKS={
 (157,1):[
  ('686Π689','',[.16,.105,.60,.54],None,None,'marginal-reference','686H. 1269R.'),
  ('ἀλλὰ μὴ πῶ περὶ', 'ἀποδημίας αὐτῷ, “καὶ ὅτι δὴ τῷ βίῳ τοῦ Πλάτωνος ἐν τούτοις ἐδοκῶμεν {u0}· ἐχρῆν δὲ ἄρα τοῦτο μὲν χωρὶς που εἶναι, τὸν λόγον δὲ ἐλέγχειν. καὶ ταῦτά γε {u1} μόνον ὄντα ἐγκλήματα, ἀλλὰ καὶ σωφρονοῦντος περὶ λόγους. ἀλλ’ ὅρα μὴ ἀναίτιόν με αἰτιᾷ. ἐγὼ γὰρ οὐκ ἔλεγον δή που Πλάτωνα κακῶς, ὥσπερ ἐν δικαστηρίῳ τινὶ κρίνων, οὐδ’ ᾐτιώμην τὰς ἀποδημίας, ἵνα χείρων νομίζοιτο, ἀλλὰ κἂν τούτοις μαρτυρεῖν ἔφασκον ἐμαυτῷ τε καὶ ῥητορικῇ. ἀλλὰ μή πω περὶ', [.20,.38,.60,.56], 'ἀποδημίας αὐτῷ,', 'ἀλλὰ μή πω περὶ'),
  (' 30','',[.20,.485,.60,.73],None,None,'marginal-reference','30'),
  ('καὶ ἐπὶ', ' τούτων. ἀλλὰ τί με χρῆν ὦ πρὸς Διὸς ποιεῖν; πότερον μὴ {u2} τὸ παράπαν τῆς ἐς Σικελίαν ἀποδημίας, ὥσπερ τι τῶν ἀποῤῥήτων μέλλοντα ἐρεῖν; ἀλλ’ οὔτε ψήφισμα συνῄδειν ἀπαγορεῦον καὶ τῷ λόγῳ συνέφερε, καὶ ἅμα ἀληθὲς ἦν· καὶ γὰρ ἔπλευσεν οὐχ ἅπαξ καὶ ὑπὲρ', [.20,.485,.60,.73], 'τούτων. ἀλλὰ τί με χρῆν', 'καὶ ὑπὲρ'),
  (' 35','',[.20,.485,.60,.73],None,None,'marginal-reference','35'),
  (None, ' τῷ Δίωνι {u3} τὰ δίκαια. ἀλλὰ νὴ Δία ἀνιαρὸν τοῦτο τοῖς Πλάτωνος ἑταίροις. ἕτερος λόγος οὗτος, οὐ πρὸς ἐμέ, ἀλλὰ πρὸς ὁντιναδήποτε. ἢ καὶ τοῦτο ἀδικῶ,', [.20,.485,.60,.73], 'τῷ Δίωνι γενέσθαι', 'ἢ καὶ τοῦτο ἀδικῶ,')],
 (157,2):[(None, 'ὅτι τὰ ἐκ τῶν νόμων αὐτῷ παρεγραψάμην; καὶ ὅπως γε κἀκεῖνο ἐπιδείξουσιν, ἐπεὶ καὶ δυσχεραίνουσιν, ὡς οὐ τοῖς αὐτοῖς αὑτῷ περιπίπτει λόγοις, ἐπειδάν τι φάσκῃ. “τοῖς δὲ εὐδαιμόνως ζῶσιν ὑπάρχειν ἀνάγκη πρῶτον τὸ μὴ ἀδικεῖν ἄλλους, μήτε αὐτὸς ὑφ’ ἑτέρων ἀδικεῖσθαι” καὶ ἑξῆς. ἢ καὶ τοῦτο ἀδικοῦμεν καὶ περιεργαζόμεθα, ὅτι προσηγάγομεν εἰς μέσον ταῦτα, καὶ οὐ προσκυνοῦμεν ὥσπερεί κίστην ἀπόῤῥητα κρύπτουσαν; ἐγὼ δὲ οὐ τοῦτο ᾤμην εἶναι τὸ τὰ ἀπόῤῥητα ἐκφέρειν, [καὶ ἄλλα ἄττα τοιαῦτα]. διὰ ταῦτα ἠξίουν {u0} διὰ τέλους, ὅστις μέλλει τὸ ἀγώνισμα πᾶν {u1} καὶ ψῆφον ὀρθὴν καὶ δικαίαν ἐποίσειν.', [.56,.105,.97,.34], 'ὅτι τὰ ἐκ τῶν νόμων', 'ἐποίσειν.')],
 (157,3):[(None, 'ὅτι ὁ Ἀριστείδης τὴν ἀνακεφαλαίωσιν τῶν προειρημένων ἐπάνοδον φησιν. ἐρεῖς δ’ ἂν καὶ συγκεφαλαίωσιν καὶ ἐπίλογον καὶ σύνοψιν καὶ ἀνάμνησιν, καὶ {u0} τὰ εἰρημένα, ὡς ὁ Δημοσθένης, καὶ συναγαγεῖν, καὶ συντόμως εἰπεῖν καὶ ἀριθμῆσαι καὶ {u1}, καὶ ἄλλ’ ἄττα τοιαῦτα, καὶ ἐπαναλαβεῖν καὶ ἀνακεφαλαιῶσαι.', [.56,.305,.97,.40], 'ὅτι ὁ Ἀριστείδης', 'ἀνακεφαλαιῶσαι.', 'unclassified-small-type')],
 (157,4):[
  ('φαίη ἄν εἰς αὐτὸν Ὀμηρος.', 'οὕτω πᾶσαν αἰδῶ καὶ τιμὴν ἀπεδώκαμεν αὐτῷ, ὥστε εἰ αὐτὸς πρὸς ἑαυτὸν ἔμελλεν ἀντερεῖν, οὐκ ἂν μοι δοκοίη μᾶλλον ἑαυτῷ {u0}. ἀτάρ, “ὦ ἄριστε Καπίτων, ἐνεθυμήθην καὶ τοῦτο μεταξὺ τῶν λόγων, ὅτι πάντα εἴδωλά ἐστι τῷ ἀνδρί, καὶ τοῦτο μὲν οἱ ποιηταὶ μιμηταὶ εἰδώλων ἀρετῆς, τοῦτο δὲ ἡ ῥητορικὴ πολιτικῆς μορίου εἴδωλον. “εἰδώλων δὲ πλέον πρόθυρον” φαίη ἂν εἰς αὐτὸν Ὅμηρος.', [.56,.375,.97,.535], 'οὕτω πᾶσαν αἰδῶ', 'αὐτὸν Ὅμηρος.'),
  (None, ' πότερον ταῦτα θρασύτερα ἢ προπετέστερα ἢ τἀμά; ἐν οἷς φημὶ Πλάτωνα ἀποδημῆσαι ὑπὲρ αὐτῶν, καὶ φημι ταῦτα λέγειν οὐ τὴν ἀποδημίαν κακίζων ἀλλὰ τῇ ἀποδημίᾳ τὸν λόγον πισούμενος. ναί, ἀλλ’ ἀπεστερήκαμεν αὐτὸν δόξης φιλοσοφίας, ὥσπερ ἐκεῖνος τοὺς μὲν τῆς τραγῳδίας ποιητὰς οὐδὲ ἐν ὀλίγῳ τίθησιν, Ὅμηρον δὲ τραγῳδοποιὸν προσεῖρηκεν {u1}, ἀλλὰ τούτους μὲν διὰ τούτων κολούων, τοῦτον δὲ ᾧ τιμᾷ καθαιρῶν. {u2} δεινόν, εἰ οὗτος μὲν καὶ τραγῳδοποιὸς καὶ κωμῳδοποιὸς καὶ πόλιν καὶ πολιτείαν καὶ νόμους ἑαυτῷ καθίστησιν, ἡμῖν δὲ μηδὲ λόγου τινὸς ἐξεῖναι πρὸς αὐτὸν ἀμφισβη-', [.56,.485,.97,.73], 'πότερον ταῦτα θρασύτερα', 'ἀμφισβητῆσαι,')],
}
UNCERTAINTIES={
 (157,1):[
 ('καθάπατε','καθάπτεσθαι','The compact σθ ending remains unresolved independently.'),
 ('ἐκ ἑρασιβ','οὐκ ἐραστοῦ','The compact negative and genitive ending are unresolved independently; digital οὐκ ἐρασᾶ differs materially.'),
 ('μηνύθηνα','μνησθῆναι','The compact σθ group and adjacent letters remain unresolved independently.'),
 ('γενέθας','γενέσθαι','The sigma component of the compact σθ group and final vowels remain unresolved independently.')],
 (157,2):[('ἀκροῖσθαι','ἀκροᾶσθαι','The compact vowel and sigma/theta group remain unresolved independently.'),('ὑπεῖναι','ὄψεσθαι','The compact sigma/theta group and preceding letters remain unresolved independently.')],
 (157,3):[('συλλογισάμενος','συλλογίσασθαι','The compact sigma/theta ending remains unresolved independently.'),('ἀναφορῶσασθαι','ἀπαριθμήσασθαι','The compact medial and final letters remain unresolved independently; the digital witness cannot alone resolve them.')],
 (157,4):[
 ('φείδωμεν','φείσασθαι','The compact sigma/theta ending remains unresolved independently.'),
 ('ὡς τῶν τῶν κόσμων','οὐ τοῦτον τούτῳ κοσμῶν','The compact particles and pronoun endings remain unresolved independently; digital ἢ τοῦτον τάτῳ κοσμῶν is a differing alternative.'),
 ('ὅκων','οὔκουν','The compact negative and accent remain unresolved independently; digital ἐκεῖν is a differing alternative.')],
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
                    segment['evidence']+=(' This is an isolated marginal reference label; the body projection omits it.'if role=='marginal-reference'else' This is part of the centered, letter-spaced source-identification heading between extracts. Its placement and type establish the heading boundary without establishing authorship; preserve its literal text and exclude it from lexical admission pending attribution.'if role=='unclassified-heading'else' This inset small-type explanatory paragraph is bounded by larger-type body paragraphs above and below; its typography establishes boundaries without establishing authorship. Exclude it pending attribution.')
                if page == 157 and number == 1 and a == 0:
                    segment['evidence'] += ' The original extraction concatenates two distinct source reference labels at different vertical positions. The observation separates their visible readings with one space; neither belongs to the body at this locus.'
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
