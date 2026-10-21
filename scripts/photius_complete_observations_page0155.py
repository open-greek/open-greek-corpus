"""Complete direct scan observations for retained historical physical page155."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:45:45Z'
CHUNKS={
 (155,1):[
  ('685 Ἡ','{u0}',[.16,.108,.60,.155],None,None,'marginal-reference'),
  ('εἰεν.', ' διαφοράν. “ὅτι ἡ ῥητορικὴ διὰ πάντων τῶν τῆς ἀρετῆς μορίων διήκει, φρονήσει μὲν εὑρεθεῖσα, εὑρεθεῖσα δὲ ὑπὲρ δικαιοσύνης, σωφροσύνῃ δὲ καὶ ἀνδρείᾳ φυλαττομένη. τοῦτο δὲ καὶ κατὰ τούτους τοὺς λόγους [οὓς μέλλω εἰπεῖν αὐτῆς] ἰδεῖν ἔστιν. ἔστι μὲν γὰρ δή που ῥητορεύειν τὸ τὰ δέοντα ἐξευρεῖν καὶ τάξαι καὶ τὰ πρέποντα ἀποδοῦναι μετὰ κόσμου καὶ δυνάμεως. φαίνεται δὲ ἡ μὲν εὕρεσις κατὰ τὴν φρόνησιν ἔχουσα, εἴπερ ἀμήχανον φρονήσεως ἀπολειπόμενον τῶν χρησίμων εὑρεῖν ὁτιοῦν, ἡ δὲ σωφροσύνη κατὰ τὴν διαχείρισιν οὖσα καὶ τὴν τῶν {u1} τε καὶ εἰκότων συμφωνίαν· ἀντὶ δ’ αὐτῆς δικαιοσύνης τὸ πρέπον τιθεῖ. τοῦτο δέ ἐστιν ὁποῖα ἄττα καὶ ὁπόσα προσήκει ἑκάστῳ σῶσαι τῷ πράγματι. ἀλλὰ μὴν ἀνδρείας ἐκ τοῦ εὐθέος οὐδὲ οὕτω μετέχειν ὡς ὁ λόγος βούλεται· τὸ γὰρ ταπεινὸν καὶ ἀγεννὲς οὐδὲν οὕτως, ὡς ὁ λόγος, ἐξορίζει καὶ ὑπερφρονεῖ. εἶεν.', [.20,.105,.60,.34], 'Ὅτι ἡ ῥητορικὴ', 'ὑπερφρονεῖ. εἶεν.'),
  ('προσωπιῶν.', ' οὗτος ὁ νουθετῶν ἀνύτει, οὗτος ὁ κατηγορῶν πιστεύεται. καὶ μὴν ὅστις γε ἃ προσῆκε λέγειν οἶδεν, οἶδεν ἃ πράττειν προσήκει· οὐδεὶς γάρ ἐστιν ὅστις, ἃ προσήκει πράττειν εἰπεῖν εἰδὼς, ἃ προσήκει πράττειν ἀγνοεῖ, οὐδ’ ὅστις ἀγνοῶν ἃ προσήκει πράττειν, εἰπεῖν ἔχει. ὅσῳ γὰρ ἄρχειν βέλτιον ἢ διακονεῖν, τοσούτῳ λέγειν τὰ δέοντα βέλτιον ἢ πράττειν. ὁ μὲν γάρ, οἶμαι, πολλοῖς σύμβουλος γίνεται, ὁ δὲ ἀνθ’ ἑνὸς ἄλλου τινὸς γίνεται. ὥσπερ οὖν τοὺς ἀρχιτέκτονας τῶν τεκτόνων ἀνάγκη προέχειν, ὄντας ὅμως περὶ ταὐτὰ ἃ καὶ τῆς τῶν τεκτόνων ἐστὶν ἐμπειρίας, οὕτω καὶ τοὺς ἐν ταῖς ἀγοραῖς τε καὶ τοῖς λόγοις προέχοντας τῶν τούτοις ὑπηρετούντων βελτίους ὁ ποιητὴς ἔθηκε καὶ προσεῖπεν ἀριπρεπεῖς, μάλα ὀρθῶς προσειπών.', [.20,.30,.60,.54], 'οὗτος ὁ νουθετῶν', 'μάλα ὀρθῶς προσείπων.'),
  (None, ' εἰ δὲ δεῖ καὶ μῦθον λέγειν, δέδοικα μὲν ἐγὼ μὴ καὶ ταῖς γραυσὶν ἡμᾶς ἐξόλης ὀφλεῖν ἐπισκώπτων φῇ τις ἀνὴρ κωμικός, ἐρῶ δὲ {u2} ἄλλως αὐτὸν εἰς ἑαυτὸν τελευτῶντα, ἀλλὰ καὶ ἐνταῦθα ἡ παρὰ τῶν πραγμάτων προσέσται πίστις. ὁ μὲν οὖν Προμηθεὺς καθ’ ἕκαστον ἐπ’ ἴσης ἅπασι τὰς τε αἰσθήσεις καὶ τὰ μέλη τοῦ σώματος συμπεπλακὼς ἦν πρότερον· τὸν δὲ Ἑρμῆν οὐχ οὕτως ἐκέλευσεν ὁ Ζεὺς ὥσπερ θεωρικοῦ διάδοσιν διε-', [.20,.485,.60,.73], 'εἰ δὲ δεῖ κὴ μῦθον', 'διάδοσιν διελεῖν,')],
 (155,2):[
  ('ἐστὶ λόγος, δῆλον ἐξ αὐτῶν.', 'λεῖν, ἵνα πάντες ῥητορικῆς ἐφεξῆς μετέχοιεν ὥσπερ ὀφθαλμῶν καὶ χειρῶν καὶ ποδῶν, ἀλλ’ ἐπιλεξάμενον τοὺς ἀρίστους καὶ γενναιοτάτους καὶ τὰς φύσεις ἐῤῥωμενεστάτους, τούτοις ἐγχειρίσαι τὸ δῶρον, ἵνα ὁμοῦ σφᾶς τε αὐτοὺς καὶ τοὺς ἄλλους σώζειν ἔχοιεν. ἀφικομένης δὲ ῥητορικῆς ἐκ θεῶν οὕτως ἐς ἀνθρώπους, ἠδυνήθησαν μὲν ἄνθρωποι τὴν μετὰ τῶν θηρίων δίαιταν χαλεπὴν ἐκφυγεῖν, ἐπαύσαντο δὲ ἐχθροὶ πάντες ὄντες ἀλλήλοις ἐν κύκλῳ, κοινωνίας δὲ εὗρον ἀρχήν. καταβάντες δὲ ἐκ τῶν ὀρῶν ἄλλοι κατ’ ἄλλα μέρη τῆς οἰκουμένης ἐπλησίασάντό γε πρῶτον ὕπαιθροι, μετὰ δὲ τοῦτο ἤδη λόγῳ νικήσαντος πόλιν τε κατεσκευάσαντο καὶ διεκρίθησαν, οὐχ ὥσπερ πρότερον, ὡς ἔτυχεν, [καὶ] εἰς τὸ νῦν {u0} καὶ ἀξίωμα χρόνῳ τε καὶ κατὰ μικρὸν ἀνήχθησαν. καὶ ὁ μῦθος μὲν ἡμῖν ταύτην ἐχέτω τὴν τελευτήν, οἶμαι κεφαλὴν οὐδὲν ἄτιμον εἰληφώς. “ὅτι δὲ οὐκ ἄλλως μῦθος ταῦτα” οὐδ’ ὄναρ, ἀλλ’ ὕπαρ καὶ ὁ τῶν πραγμάτων αὐτῶν ἐστὶ λόγος, δῆλον ἐξ αὐτῶν.', [.56,.105,.97,.39], 'λεῖν, ἵνα πάντες', 'λόγος, δῆλον ἐξ αὐτῶν.'),
  ('εἶναι πράττειν.', ' ἐὰν τοίνυν ἔτι τούτων ἐγγυτέρω προσαγάγω τὸν λόγον, ἦ που τρυφή τις ἂν εἴη τῆς ἀποδείξεως, καὶ οὔτε ἔννοιαν οὔτε ἐλπίδ’ ἐλέγχων {u1} οὐδ’ εἷς ἔτι δή που λάβοι. {u2} αὐτὸς Πλάτων, ὡς πολλάκις ἐδείξαμεν πρότερον, ἀλλὰ καὶ ἐν αὐτοῖς τούτοις τοῖς λόγοις τῷ παραδόξῳ δὴ συγγράμματι διαῤῥήδην ὁμολογεῖ τῇ ῥητορικῇ τὰ κάλλιστα εἶναι πράττειν.', [.56,.30,.97,.54], 'ἐὰν τοίνυν ἔτι τέτων', 'εἶναι πράττειν.'),
  (None, ' τὰ μὲν οὖν ἄλλα ἢ ψυχαγωγίαν ἢ χρείαν ὡς ἐπὶ τὸ πλεῖστον εἰπεῖν ἔχει, μόνον δὲ τὸ τῆς ῥητορικῆς μάλιστά γε ἄμφω πληροῖ, καὶ μετὰ τῶν ὠφελειῶν τὴν χάριν θαυμαστὴν ἔχει, ὥστε καὶ ὅταν εἰς πολέμους ἀλλήλοις ἔλθωσιν ἄνθρωποι, τὰς παρὰ τῶν αὐτοχειρῶν πρέσβεις ἀφικνουμένας δέχονται καὶ ἀποπέμπουσιν, ἐνθυμούμενοι τὸ τῶν ῥητόρων φῦλον, ὑπεξαιρούμενοι τὴν τοῦ λόγου φύσιν, αἰδούμενοι ὅτι ἐξ ἀρχῆς ἐπὶ σωτηρίᾳ καὶ κοινῇ χρείᾳ τοῦ γένους εἰσῆλθεν. εἰ δέ τις ἡμῖν περὶ Πλάτωνος ὑπολάβοι ὅτι οὐ ταύτην κακῶς εἴρηκε τὴν ῥητορικήν, ὑπὲρ ἧς νῦν ἡμεῖς τοὺς λόγους ποιούμεθα, ἀλλὰ δύο οὐσῶν τὴν ἑτέραν κακίζει, πρῶτον μὲν οὐδὲν μᾶλλον τά γε ἡμῖν εἰρημένα φαύλως {u3},', [.56,.485,.97,.73], 'Τὰ μὲν οὖν ἄλλα', 'φαύλως ἔχοντα ἐλέγχοντι,')],
}
UNCERTAINTIES={
 (155,1):[
 ('685 Ἡ','683H.','The last digit of this marginal reference is not fully resolved independently. The label has no body or lexical role, regardless of its digit.'),
 ('ἡχημάτων','ἡγημένων','The medial and final letters of the compact participle remain unresolved independently; digital ἡγουμένων is a separate alternative.'),
 ('ὁ μῦθον','οὐ μῦθον','The compact ου glyph in this negative remains unresolved independently; digital ὃ μῦθον differs from the apparent scan reading.')],
 (155,2):[
 ('χῆμα','σχῆμα','The sigma component of the compact σχ group remains unresolved independently.'),
 ('ἐχνοστεύσων','ἰσχυροτέρων','The compact σχ group and subsequent letters remain unresolved independently.'),
 ('ἢ γὰρ μόνον','οὐ γὰρ μόνον','The compact negative before γὰρ remains unresolved independently; digital ὃ γὰρ μόνον is a separate alternative.'),
 ('ἔχοντι ἐλέγχου','ἔχοντα ἐλέγχονται','The final compact verbal ending remains unresolved independently; digital ἔχοντα ἐλέγχοντι is a differing alternative.')],
}
LEADING_FRAGMENTS={(155,2):'λεῖν'}


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
