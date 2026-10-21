"""Complete direct scan observations for retained historical physical page156."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:49:00Z'
CHUNKS={
 (156,1):[(None, 'ἀλλὰ κατ’ αὐτὸ τοῦτο καλῶς καὶ προσηκόντως ἅπαντα ταῦτα {u0} μαρτυρεῖ· ὥσπερ γὰρ ἐκεῖνος τὴν φαύλην δικαίως ψέγει, τί κωλύει τήν γε ἐναντίαν ἡμᾶς ἐπαινοῦντας ὀρθῶς ποιεῖν; ἔπειτα οὐκ ἀναιρεῖ τοὺς παρ’ ἡμῶν ἐλέγχους ἡ παραίτησις αὕτη, ἀλλὰ καὶ οὕτως ἐναντία φαίνοιτ’ ἂν εἰρηκὼς αὐτὸς ἑαυτῷ, εἰ διττὴν εἶναι τὴν ῥητορικὴν ἀξιῶν εἶθ’ ὡς μιᾶς καὶ ἁπλῆς τινὸς οὔσης τὴν κατηγορίαν πεποίηται. δῆλον γὰρ ὅτι εἰ τοῦτ’ ἐστὶν ἀληθές, τὴν μὲν φαυλίζειν τὴν δ’ ἐπαινεῖν προσῆκεν αὐτῷ διελομένῳ, ὥσπερ ἐν τοῖς περὶ ἔρωτος λόγοις φαίνεται πεποιηκὼς καὶ πολὺ γε μειζόνων εὐφημιῶν τὸν χρηστὸν ἠξιωκὼς ἢ οἵων τὸν ἕτερον βλασφημιῶν.', [.025,.105,.44,.34], 'ἀλλὰ κατ’ αὐτὸ τοῦτο', 'τὸν ἕτερον βλασφημιῶν.')],
 (156,2):[
  ('παρασθίνται.', '{u0} αὐτὸς λόγος καὶ περὶ πάσης φιλοσοφίας καὶ περὶ γε τῶν τῆς ἀρετῆς, εἴ τις βούλοιτο διαιρούμενος πρῶτον μὲν σοφίας δύο προσαγορεύειν, τὴν μὲν ᾗ τὰ βέλτιστα συνίεμεν, τὴν δ’ ἑτέραν ᾗ κακουργοῦσιν, ἔπειτα σωφροσύνην διπλῆν, τὴν μὲν σπουδῆς ἀξίαν καὶ πολιτικήν, τὴν δὲ νωθράν τε καὶ ὑπτίαν, ἔτι δ’ αὖ δικαιοσύνην ὀρθὴν καὶ ἑτέραν ταπεινήν, καὶ διπλῆν {u1} τὴν μὲν σὺν νῷ καὶ φρεσίν, τὴν δὲ ἀπόνοιαν καὶ μανίαν οὖσαν. ἀλλ’ οἶμαι, πάντα ταῦτα τῶν φυρόντων ἐστὶ τὰ ὀνόματα, καὶ διῄρηται σοφία καὶ κακουργία, σωφροσύνη καὶ βλακεία, δικαιοσύνη τε καὶ εὐήθεια, ἀνδρεία καὶ θρασύτης· οὐδέτερον δέ γε οὔτε καλὸν χαλεπὸν οὔτε προσῆκον. πολλῷ γὰρ ταῦτα ἀπ’ ἀλλήλων διῄρηται, καὶ οὐ δεῖ τὰς κακίας {u2} τῷ τῆς ἀρετῆς ὀνόματι, οὔτε τὰς ἀρετὰς φαυλίζειν τὰ τῆς κακίας ἑκάστῃ παρατιθέντα.', [.025,.265,.44,.515], 'ὁ δ’ ἐν αὐτὸς λόγος', 'ἑκάστῃ παρατιθέντα.'),
  (None, ' εἰ γ’ ὅτι μάλιστα οὕτω Πλάτων διανοῖτο, ὥσπερ ἔγωγε οὐκ ἀντιλέγω, ἀλλ’ {u3} τὴν καθαρὰν καὶ τῷ ὄντι ῥητορικήν, ἄξιον μὴ {u4}, μηδ’ ἀγνοῆσαι τοῦτο αὐτὸ τοὺς πολλούς, “μηδ’ ὡς ψήφῳ καθαρᾷ προσέχοντας θᾶττον ἢ συμφέρει {u5} περὶ τῶν τηλικούτων. πανταχῇ δὲ καὶ διὰ πάντων ἐκπίπτουσιν ἡμῖν αἱ ψῆφοι. πρῶτος δὲ Πλάτων αὐτὸς ψηφίζεται καὶ μέσος (φασί) καὶ τελευταῖος. καὶ κινδυνεύω δοκῶν ἀντιλέγειν Πλάτωνι παντὸς μᾶλλον συνηγορεύειν. εἰ δὲ δεῖ τι καὶ παῖξαι, δοκῶ', [.025,.465,.44,.73], 'εἰ γ’ ὅτι μάλιστα', 'παῖξαι, δοκῶ')],
 (156,3):[
  ('αὐτῷ', 'μοι “{u0} κωμῳδοποιοὺς ὥσπερ ἀποδιδράσκοντα αὐτὸν', [.39,.105,.81,.34], 'μοι "τὰς κωμῳδοποιοὺς', 'αὐτὸν'),
  (None,'',[.39,.105,.81,.34],None,None,'marginal-reference','1268R.')],
}
LINES={
 4:('ἕλξειν εἰς {u0} ῥήτορας, ὅτι μαθὼν καλλωπίζεται.', 'ἔλξειν εἰς τὰς', 'καλλωπίζεται.'),
 5:('Ἀριστείδου ἐκ τοῦ ἐπιγραφομένου λόγου', 'Ἀριστείδου ἐκ τοῦ', 'λόγου'),
 6:('Πλατωνικὸς τρίτος πρὸς Καπίτωνα.', 'Πλατωνικὸς τρίτος,', 'Καπίτωνα.'),
 7:('τὸ προοίμιον.', 'τὸ προοίμιον.', 'τὸ προοίμιον.'),
 8:('Νῦν σε καὶ μᾶλλον {u0}, οὕτως ἐρωτικῶς τοῦ', 'Νῦν σε καὶ μᾶλλον', 'τοῦ'),
 9:('Πλάτωνος ἔχοντα, ὃν ἐγὼ φαίην ἂν τιμῶν καθ’ Ὅμη-', 'Πλάτωνος ἔχοντα,', 'Ὅμηρον'),
 10:('ρον ἶσον ἐμῇ κεφαλῇ. εἰ γάρ τοι καὶ πάντες φαῦλοι', 'Ὅμηρον ἶσον', 'φαῦλοι'),
 11:('πρὸς ἐκεῖνον, ἀλλ’ ἕκαστος τιμιώτατος αὐτὸς ἑαυτῷ,', 'πρὸς ἐκεῖνον, ἀλλ’ ἕκαστος', 'ἑαυτῷ,'),
 12:('φασί. καίτοι τί λέγω; οὐκ οἶδα μὲν γ’ εἰ πιστεύεις, ἀλη-', 'φασί. καίτοι τί λέγω;', 'ἀληθὲς'),
 13:('θὲς δ’ ἐρῶ. εἰ δὲ μὴ ἐγγὺς ἐκείνου ἔφησας ἡμῶν εἶ-', 'ἀληθὲς δ’ ἐρῶ.', 'εἶναι,'),
 14:('ναι, οὐκ ἂν οὕτω με εὔφρανας, ὡς ὅτι προκατείληψαι', 'εἶναι, ἐκ ἂν οὕτω', 'προκατείληψαι'),
 15:('δείξας· οὕτως ἐμοὶ φίλος ἀνὴρ καὶ φίλων ἐπέκεινα. συν-', 'δείξας· οὕτως ἐμοὶ', 'συνέβη'),
 16:('έβη δέ μοι καὶ περὶ Δημοσθένην τοιοῦτον ἕτερον· φράσω', 'συνέβη δέ μοι', 'φράσω'),
 17:('δὲ καὶ πρὸς σέ. ἀνὴρ τῶν ἐκ τῆς γερουσίας τῆς Ῥω-', 'δὲ καὶ πρὸς σέ.', 'Ῥωμαίων,'),
 18:('μαίων, Λίβυς τὰ ἀρχαῖα, Μάξιμος τοὔνομα, ἄξιος', 'Ῥωμαίων, Λίβυς', 'ἄξιος'),
 19:('ὅτε βούλει (φασὶ δὲ οἱ ταῦτα δεινοὶ καὶ ῥήτορα αὐτὸν', 'ὅτε βέλει', 'αὐτὸν'),
 20:('ἐν πρώτοις εἶναι Ῥωμαίων), οὗτος τοῖς τε Δημοσθένους', 'ἐν πρώτοις εἶναι', 'Δημοσθένους'),
 21:('λόγοις προσέκειτο ὑπερφυῶς, καὶ οὐκ οἶδ’ ὅντινα τρό-', 'λόγοις προσέκειτο', 'τρόπον'),
 22:('πον καὶ τοῖς ἡμετέροις ἑάλω τούτοις. ἔτυχε γάρ μοι', 'τρόπον καὶ τοῖς', 'μοι'),
 23:('λόγος τις πεποιημένος ἐκ τρίτων πρὸς Λεπτίνην, ἐξ', 'λόγος τις πεποιημένος', 'ἐξ'),
 24:('ἀρχῆς τοιᾶσδε. εἶχον μὲν γ’ ἐν χερσὶ τὸν λόγον τὸν', 'ἀρχῆς τοιᾶσδε.', 'τὸν λόγον τὸν'),
 25:('τοῦ Δημοσθένους, καὶ ὡς ἐγενόμην ἐπὶ τῶν κεφαλαίων', 'τοῦ Δημοσθένους, καὶ ὡς', 'κεφαλαίων'),
 26:('ἃ τῷ Λεπτίνῃ μέλλοντος ἐρεῖν ὑποτέμνεται, ἀποστήσας', 'ἃ τῷ Λεπτίνῃ', 'ἀποστήσας'),
 27:('ἐμαυτὸν τοῦ Δημοσθένους ὑπ’ ἐμαυτοῦ τι συνεώρων. ὡς', 'ἐμαυτὸν τοῦ Δημοσθένους', 'ὡς'),
 28:('δὲ εὗρον καὶ δύο καὶ τρία τῶν χρησίμων, ἐνταῦθα πά-', 'δὲ εὗρον καὶ δύο', 'πάλιν'),
 29:('λιν αὖ ἐπ’ ἄλλο τι ἐχώρουν. καί μοι πειρωμένῳ τὸ αὐτὸ', 'πάλιν αὖ ἐπ’ ἄλλο', 'τὸ αὐτὸ'),
 30:('ἀεὶ συνέβαινε. καὶ ἔστω δὴ ἀπὸ τοῦ κρασπέδου θοιμά-', 'ἀεὶ συνέβαινε.', 'θοιμάτιον,'),
 31:('τιον, εἰ δὲ βούλει, τὸν λέοντα ἀπὸ τοῦ ὄνυχος ἀπειργα-', 'θοιμάτιον, εἰ δὲ', 'ἀπειργασάμην.'),
 32:('σάμην. τοῦτον αὐτῷ τὸν λόγον δεῖξαι ἐπεχείρησα· καὶ', 'ἀπειργασάμην. τοῦτον', 'καὶ'),
 33:('μέλλων δείξειν, προεῖπον ὅτι πρὸς Λεπτίνην ἐφευρη-', 'μέλλων δείξειν,', 'ἐφευρημένος'),
 34:('μένος σὺν τῷ πρὸς Λεπτίνην ἐφευρήσει. ἆρα μὴ ἀδικῶ', 'ἐφευρημένος σὺν τῷ', 'ἀδικῶ'),
 35:('σε; ἔφην ἐγώ. καὶ ὃς μὰ Δία εὐγενῶς τε καὶ ὡς ἂν', 'σε; ἔφην ἐγώ.', 'ἂν'),
 36:('πᾶς {u0} {u1} ὅστις φιλόλογος, οἶσθα, ἔφη,', 'πᾶς ἡράσθη', 'ἔφη,'),
 37:('ὅτι κάθημαι πρὸς τῷ Δημοσθένει; κἀγώ, τὸν αὐτὸν', 'ὅτι κάθημαι πρὸς', 'αὐτὸν'),
 38:('ἄρα, ἔφην, ἐμοὶ βουκολεῖς, ὥστε εἰ νικῴη μ’, οὐκ ἐχθρὸς', 'ἄρα, ἔφην,', 'ἐχθρὸς'),
 39:('ὁ {u0}, ἀλλ’ ᾧ σύ γε κἀγὼ συσπεύδομεν. ὡς', 'ὁ στεφανώμενος,', 'συσπεύδομεν. ὡς'),
}
for number,(target,begin,last)in LINES.items():
 region=[.39,.105,.81,.34]if number<=18 else [.39,.30,.81,.54]if number<=29 else [.39,.485,.81,.73]
 CHUNKS[(156,number)]=[(None,target,region,begin,last)]
for number,label in [(9,'5'),(15,'10'),(20,'15'),(25,'20'),(30,'25'),(35,'30')]:
 CHUNKS[(156,number)].insert(0,(label,'',CHUNKS[(156,number)][0][2],None,None,'marginal-reference',label))
for number in (5,6,7):
 CHUNKS[(156,number)][0]=(*CHUNKS[(156,number)][0],'unclassified-heading')
UNCERTAINTIES={
 (156,1):[('ἡνέχῃ','ἡνίωξε','The compact verb and its ending are not independently resolved; digital ἡνίωξεν is a separate alternative.')],
 (156,2):[
 ("ὁ δ' ἂν",'ὁ δ’ οὖν','The compact particle and accent remain unresolved independently; digital ὁ δ’ ἐν differs.'),
 ('ἀνδραγαγίαν','ἀνδρίαν','The compact noun is unresolved independently; the following words in the original also contain extraction noise.'),
 ('ὑποκορίζεσθαι','ὑποκορίζεσθαι','The compact σθ group in this unchanged original form remains ambiguous independently; retain it with explicit uncertainty rather than silently certifying it.'),
 ('ἐπεξήρη','ὑπεξῃρῆσθαι','The compact final σθ group and preceding letters remain unresolved independently; digital ὑπεξῃρημένην is a materially different reading.'),
 ('παρακαρἡναι','παρακρουσθῆναι','The compact sigma/theta group and medial letters remain unresolved independently.'),
 ('βελειώσας','βουλεύσασθαι','The compact sigma/theta group and verb ending remain unresolved independently.')],
 (156,3):[('τὰς','τοὺς','The compact article ending is unresolved independently; digital τὰς is a separate reading rather than grammatical authority.')],
 (156,4):[('τὰς','τοὺς','The compact article ending is unresolved independently; digital τὰς is a separate reading rather than grammatical authority.')],
 (156,8):[('φιλήμην','φιλοίμην / φιλήμην','The medial vowel and verbal ending are unresolved independently; digital φιλοῦμεν is a materially different reading.')],
 (156,36):[('Ἡρώδῃ τε','ἠράσθη τε','The compact sigma/theta glyph and ending are not independently resolved.'),('κ Ἡρώδῃ','καὶ ἠγάσθη','The compact sigma/theta glyph and medial consonant are not independently resolved.')],
 (156,39):[('σιρανόμενος','στεφανούμενος','The compact participle and the ου/ω ending are unresolved independently; digital στεφανώμενος is retained as a separate reading.')],
}
LEADING_FRAGMENTS={(156,10):'ρον',(156,13):'θὲς',(156,14):'ναι',(156,16):'έβη',(156,18):'μαίων',(156,22):'πον',(156,29):'λιν',(156,31):'τιον',(156,32):'σάμην',(156,34):'μένος'}


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
