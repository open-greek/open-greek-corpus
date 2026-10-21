"""Complete direct scan observations for retained historical physical page150.

Every source word was inspected in overlapping pinned readable crops. The
inset small-type paragraph is preserved without inferring its authorship.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re

REVIEWED_AT = '2026-10-21T12:32:18Z'
# Each chunk has exact original end anchor, inspected source transcription,
# pinned crop, and exact bounded beginning/end in the independent witness.
CHUNKS = {
 (150,1):[
  ('ἀπώσαμεν.', 'μακον εὑρεθῆναι τῷ γένει, ταὐτὸν ἅπασι συμφέρον, τοῖς ἰσχυροῖς, τοῖς ἥττοσι, τοῖς ἐπιεικέσιν, ὡς τοὺς μὲν ἢ κωλῦσαι πρὸ τῶν ἀδικημάτων ἢ παρ’ αὐτὰ τιμωρήσασθαι, τοῖς δὲ ἄδειαν τοῦ βίου παρασκευάσαι, τοῖς δὲ χάριν τὴν πρέπουσαν, ὅσοι τὸ δίκαιον ἐτίμων ἑκόντες. {u0} τοίνυν ἐκ τούτων ῥητορική, καὶ παρῆλθε φυλακτήριον δικαιοσύνης καὶ σύνδεσμος τοῦ βίου τοῖς ἀνθρώποις, ὅπως μὴ ταῖς χερσὶ μηδὲ τοῖς ὅπλοις μηδὲ τῷ προλαβεῖν μηδὲ πλήθει καὶ μεγέθει, μηδ’ ἄλλῳ τῶν ἀνίσων μηδενὶ κρίνοιτο τὰ πράγματα, ἀλλ’ ὁ λόγος τὸ δίκαιον ἐφ’ ἡσυχίας διαιροῖ. ἀρχὴ μὲν οὖν αὕτη καὶ φύσις ῥητορικῆς, καὶ βούλημα τοῦτο, σῶσαι πάντας ἀνθρώπους καὶ τὸν βίον διὰ τῆς πειθοῦς {u1}.', [.045,.112,.425,.335], 'εὑρεθῆναι τῷ γένει,', 'ἀπώσασθαι.'),
  (None, ' φαίνεται τοίνυν ἡ ῥητορικὴ τῇ νομοθετικῇ τῆς αὐτῆς μετειληφυῖα φύσεως, εἴπερ τό γε ἀκριβὲς ἐπ’ ἀμφοτέρων δεῖ θεωρεῖν· μᾶλλον δὲ μέρος οὖσα τῆς ῥητορικῆς ἡ νομοθετική, καὶ τοῖς πᾶσι δευτέρα. πῶς; πρῶτον μὲν ὅτι καὶ περὶ αὐτῶν ἔδει τῶν νόμων.', [.045,.30,.425,.535], 'φαίνεται τοίνυν ἡ ῥητορικὴ', 'τῶν νόμων')],
 (150,2):[
  ('576H.', '', [.005,.36,.43,.51], None, None, 'marginal-reference', '676H.'),
  (None, 'λόγου τοῦ πείθοντος. εἰ γὰρ ἔστιν εὔδηλον ὅτι οἱ νόμοι μὲν ὑπὲρ τοῦ πάντας τὸ προσῆκον ἔχειν ἔμελλον {u0}, τοῦτο δὲ οἱ τῇ χειρὶ κρείττους ἔμελλον {u1}, πῶς ἂν ἀναγκαίως ἔδει λόγου τοῦ πείθοντος ἤδη; οὐ γὰρ βιάσασθαί γε ἐνῆν τοὺς πρὸς αὐτὸ τοῦτο πεφυκότας, οὐδ’ ἦν αὕτη νόμων ἀρχή· ὑπὲρ γὰρ αὐτοῦ τοῦ μὴ {u2} τοὺς νόμους ἔδει {u3}. οὔκουν ἦν', [.045,.30,.425,.535], 'λόγου τοῦ πείθοντος.', 'οὔκουν ἦν')],
 (150,3):[
  ('1252R.', '', [.005,.36,.43,.51], None,None,'marginal-reference','1252R.'),
  (None, 'τιθέναι βιασάμενον, “ἀλλὰ τοῦτ’ ἦν πρῶτον παρὰ τοὺς νόμους. φαίνεται τοίνυν κἀνταῦθα ἡ ῥητορικὴ βουλομένη μὲν ταὐτὰ τῇ δικαστικῇ, τοσοῦτον δὲ νικῶσα ὅσον ἀμφοτέρας [τὴν νομοθετικὴν καὶ δικαστικὴν] συνέχει μόνη βεβαίως. βουλομένη γὰρ ἡ δικαστικὴ καθάπερ ἐν μάχῃ τῇ νομοθετικῇ βοηθῆσαι, ταὐτὸν ἔπαθεν αὕτη τῇ νομοθετικῇ. ἐκείνη τε γὰρ ῥητορικῆς πρότερον ἐδέησεν, ὥστε ταύτῃ ἔχειν πάροδον τοὺς νόμους· ἥ τε δικαστικὴ {u0} ἐπικούρου λαβοῦσα τοῖς νόμοις, αὐτὴ πρότερον προσεδεήθη τῆς παρὰ τῆς ῥητορικῆς βοηθείας. ἔδει γὰρ δυνηθῆναι βοηθῆσαι, τοῦτο δ’ οὐκ ἦν ἄνευ ῥητορικῆς. πότερον οὖν πολιτικῆς μορίω εἴδωλον ἡ ῥητορική, ἢ τὰ τῆς πολιτικῆς, ὡς σὺ φῄς,', [.045,.485,.425,.68], 'τιθέναι βιασάμενον,', 'ὡς σὺ φῄς,')],
 (150,5):[(None, 'μόρια ὑπὸ τῆς ῥητορικῆς συνέχει; ἐμοὶ μὲν γὰρ ὡς ἀληθῶς ἡ ῥητορικὴν ἐν τούτοις κακίζειν φαίνεται, οὐδὲ πολιτικῆς μορίω εἴδωλον δεικνύναι, ἀλλ’ οὕτως ὥσπερ εἴδωλον ῥητορικῆς ἀπειληφὼς ἐπὶ τούτῳ σπουδάζειν, αὐτῆς δὲ οὐδ’ {u0}, ὥσπερ οἱ Στησιχόρῳ Τρῶες οἱ τὸ τῆς Ἑλένης εἴδωλον ἔχοντες ὡς αὐτήν. διαφέροι δ’ ἂν τοσοῦτον, ὅτι οὐδὲν ὅμοιον τῇ ῥητορικῇ τὸ εἴδωλον.', [.39,.112,.80,.335], 'μόρια ὑπὸ τῆς ῥητορικῆς', 'τῇ ῥητορικῇ τὸ εἴδωλον.')],
 (150,6):[
  ('ἕτερα ἀδικεῖσθαι κράττον ἢ ἀδικεῖν.', 'ἐκεῖνο ὁπότε μήτ’ ἀδικεῖν μήτ’ ἀδικεῖσθαί φησι βούλεσθαι, δῆλον ὅτι καὶ τὸ ἀδικεῖσθαι κακὸν ἡγούμενος οὔ φησι βούλεσθαι, ἀλλὰ τὸ μὲν ἀδικεῖν ἄμεινον τὸ ἀδικεῖσθαι, οὐ μὴν ἐκεῖνά γε τὸ μήτ’ ἀδικεῖν μήτ’ ἀδικεῖσθαι, ὀρθῶς οἶμαι καὶ γινώσκων καὶ λέγων. εἰ μὲν τοίνυν ἡ ῥητορικὴ ἀδικεῖσθαι μὲν ἐκώλυεν, ἀδικεῖν δὲ προηνάγκαζεν, οὐδ’ οὕτω μὲν ἴσως ἂν καθάπαξ πονηρὸν ἦν, πονηρὸν γε ὂν κωλῦσαι τὸ ἀδικεῖσθαι, χεῖρον δ’ ἂν ἴσως βελτίονος, ὅπερ ἀδικεῖσθαι κρεῖττον ἢ ἀδικεῖν.', [.39,.112,.80,.335], 'ἐκεῖνο ὁπότε', 'κρεῖττον ἢ ἀδικεῖν.'),
  ('τοῦ μὴ ἔχειν ἀδικεῖν ἔχει.', ' εἰ δ’ οὔτ’ ἐκεῖνος ἐπαναγκάζει καὶ τοῦτο κωλύει, κατ’ ἐκεῖνο μὲν οὔτε ἀγαθὸν οὔτε κακόν πω (δῶμεν γὰρ ὡς ἐν τῷ παρόντι), κατὰ τοῦτο δὲ κυρίως ἀγαθόν. καὶ μὴν ὁ μὲν μὴ ἀδικεῖν {u0} ἅμα αὐτός τε τοῦ κακουργεῖν ἀπέχεται καὶ τὸ ἀδικεῖσθαι πέφευγεν· αὐτὸ γὰρ τοῦτο ἦν ἀδικεῖν, τὸ κακῶς ὃν οὐ προσῆκε ποιεῖν. ὥσθ’ ἕως ἂν ἐν ἀνθρώποις ᾖ τὸ κακουργεῖν, ἀδικήσεται. ὁ δὲ τὴν τοῦ μὴ ἀδικεῖσθαι φυλακὴν ἔχων ἅμα καὶ τὸ ἀδικεῖν που κωλύει. ὥσπερ γὰρ ἅμα ἠδίκηται καὶ ἠδίκηκεν ὁ ἕτερος, οὕτως ὁ τὴν τοῦ μὴ ἀδικεῖσθαι δύναμιν ἔχων τὴν αὐτὴν τοῦ μὴ ἐᾶν ἀδικεῖν ἔχει.', [.39,.30,.80,.535], "εἰ δ' οὔτ' ἐκεῖνος", 'τοῦ μὴ ἐᾶν ἀδικεῖν ἔχει.'),
  (None, ' ὥστε εἰ τὸ μὲν μὴ ἀδικεῖσθαι τῆς ῥητορικῆς τίθησι, τὸ δὲ μὴ ἀδικεῖν τῆς φιλοσοφίας, τοσούτῳ χείρων φιλοσοφίας ῥητορική, ὅσῳ τὸ ἀδικεῖσθαι τοῦ ἀδικεῖν. ὁπότε δ’ αὖ πρὸ τούτου τίθησι τὸ μήτε ἀδικεῖν μήτε ἀδικεῖσθαι, τούτῳ βελτίων αὖ γίνεται ῥητορικὴ φιλοσοφίας, ἐπειδή γε ὁμοῦ τὸ ἀδικεῖσθαι καὶ τὸ ἀδικεῖν ἀναιρεῖ, ἐπεὶ καὶ οἱ νόμοι κωλύοντες ἀδικεῖσθαι ἅμα τὸ ἀδικεῖν δή που κωλύουσιν.', [.39,.485,.80,.68], 'ὥσε εἰ τὸ μὲν', 'δή που κωλύουσιν.')],
 (150,7):[(None, '“ταῦτα πιθανῶς μᾶλλον ἢ ἀναγκαίως λέγει Ἀριστείδης. τῷ γὰρ περὶ τὸ μὴ ἀδικεῖσθαι καὶ τῆς ῥητορικῆς ἐπιμελεῖσθαι, κρείττω δεικνύναι φιλοσοφίας φιλοτιμούμενος τὴν ῥητορικήν.', [.39,.485,.80,.68], '"ταῦτα πιθανῶς', 'τὴν ῥητορικήν,', 'unclassified-small-type')],
}
UNCERTAINTIES = {
 (150,1):[
 ('εὗρίσθη','εὑρέθη','The compact theta group does not independently establish whether a sigma component is present; the digital witness reads εὑρέθη. Retain the original form rather than dropping sigma from inference.'),
 ('ἀπώσαμεν','ἀπώσασθαι','The compact final sigma/theta and ending are unresolved independently. Digital ἀπώσασθαι is retained as a separate reading.')],
 (150,2):[
 ('τεθάμενοι','τεθήσεσθαι','The densely set future passive ending is not independently resolved; digital τεθήσεσθαι alone does not authorize supplying its letters.'),
 ('συμβληθῆσθαι','συμβουλήσεσθαι','The compact medial and final glyphs are not sufficiently resolved to change every letter independently.'),
 ('βιαλῶθ','βιάζεσθαι','The compact terminal group remains uncertain independently of the digital witness.'),
 ('θεός','θέσθαι','The compact final glyph can represent a sigma/theta combination; preserve the original display until independently resolved.')],
 (150,3):[('χεῖμα','σχῆμα','The sigma component of the compact σχ glyph is not independently established; the digital witness is not decisive.')],
 (150,5):[('ἀπεῖχε','ἅπτεσθαι','The compact middle and terminal glyphs do not establish the full participial/infinitive reading independently; retain the original display and digital variant.')],
 (150,6):[('ἐγνωκὼς ἂν','ἐγνωκὼς οὐχ','The compact negative before ἅμα is not independently resolved; the digital witness instead has ἐξ, so preserve all alternatives.')],
}
LEADING_FRAGMENTS={(150,1):'μακον'}


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
