"""Complete direct scan observations for retained historical physical page160."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:04:36.301674Z'
CHUNKS={
 (160,2):[
 ('μὴ-μεθαι ἢ','τοῦτ’ αὐτὸ προσειλήφει μεῖζον, τὸ {u0} οὕτως ἔχοντας ὁρᾷν ὥστε ἀπόρως εἶναι {u1}, καὶ ταῦτα οὐχ ὅσον τοῖς πολεμίοις ὑποπεπτωκέναι ἀλλὰ κἀκείνῳ δυσμεναίνειν ὡς τῶν παρόντων πραγμάτων αἰτίῳ. πρὸς δυοῖν τοῖν ἀπὸ τῆς τύχης (τῷ πολέμῳ καὶ τῇ νήσῳ) δύο ταῦτα προσειληφότας ὁρῶν αὐτός, λύπην καὶ παροξυσμὸν εἰς αὑτόν, ἐν μέσοις τοῖς δεινοῖς ἐμβεβηκὼς καὶ πανταχόθεν μεμονωμένος ὡς εἰπεῖν οὐκ ἔδεισεν, οὐδ’ ὑπεχώρησεν, οὐδ’ ὥσπερ χροιὰν τὴν γνώμην μετέβαλε, τοῖς τε πολίταις καὶ τοῖς πολεμίοις ὁμοῦ ἀντιτεταγμένος· ἀλλ’ ὥσπερ ἂν ἄλλο τι μάθημα διδάσκων αὐτούς, κατὰ ταὐτὰ ἃ καὶ πρότερον διεξῄει, καὶ οὐ διέφθειρε τὰ δόγματα ἐπὶ τῶν κινδύνων, οὐδὲ ἐπὶ τῆς ἐξουσίας ἐφιλοσόφησε μόνον, ἀλλ’ ὡς περὶ ἀριθμῶν ἢ μέτρων ἐρωτηθεὶς ταὐτὸν ἀπεκρίνατο ἂν καὶ ὕστερον καὶ πρότερον, οὕτω καὶ τότε τὰς αὐτὰς ἠφίει φωνὰς ὑπὲρ τῶν ὅλων πραγμάτων, οὔτε τοῖς δεινοῖς εἴκειν ἀξιῶν οὔτε ἑαυτῷ {u2}, {u3} τε ὑπὲρ αὑτῶν ἅμα τοῖς καιροῖς ἑτέρων γεγονότων. μὴ δὴ τοῦτο λέγωμεν, ὡς οὐκ ἐξῆγεν· ἀλλ’ εἰ προσῆκον ἐξάγειν καὶ {u4} παρεώρα, τοῦτο σκοποῦμεν, ἐπεὶ καὶ Λακεδαιμονίους ἀκούομεν δή που προσκειμένων αὐτοῖς ποτὲ Θηβαίων, καὶ κελευόντων ἐξιέναι καὶ {u5} ἢ', [.025,.105,.44,.54], 'τῦτ’ αὐτὸ προσειλήφει', 'καὶ μάχεσθαι ἢ'),
 ('127R','',[.025,.30,.44,.54],None,None,'marginal-reference','1277R.'),
 ('τὰ σώματα, καὶ',' χείρους ὁμολογεῖν εἶναι σφῶν, {u6} “περὶ μὲν τοῦ πότεροι βελτίους τὰς πράξεις κρίνειν τὰς ὑπὲρ τῶν Ἑλλήνων ἑκατέροις πεπραγμένας, {u7} δὲ οὐκ ἐν τῷ τῶν πολεμίων καιρῷ οὐδ’ ὅτε ἐκεῖνοι κελεύουσιν, ἀλλ’ ἡνίκα ἂν αὐτοῖς δοκῇ, καὶ οὐ {u8} περὶ τούτου συμβούλοις Θηβαίοις.” ἐγὼ μὲν οὖν ὅπερ λέγω περὶ τούτων, οὕτω καὶ χαίρω τῇ μεγαλοπρεπείᾳ παντὸς μᾶλλον, ὥς γε ἐμαυτὸν πείθω. ὁρῶ δὲ ὅτι πολλὰ τῶν πόλεών ἐστιν ὥσπερ ἐφόλκια, οἷς ἀνάγκη συγχωρεῖν ὥσπερ ἐν σώματι. καὶ γὰρ τὰ σώματα, καὶ', [.025,.30,.44,.73], 'χείρους ὁμολογεῖν', 'τὰ σώματα, καὶ'),
 ('691 H','',[.025,.485,.44,.73],None,None,'marginal-reference','691H.'),
 (None,' τὰ χείριστα καὶ τὰ κάλλιστα, “{u9} ἐκ τῶν αὐτῶν {u10}” τῷ δὲ ἢ πλείονος ἢ ἐλάττονος τούτων ἑκάστῳ μετέχειν, τούτῳ {u11} τό τε χεῖρον καὶ τὸ βέλτιον. οὕτω δὴ καὶ τὰς πόλεις ἀνάγκη τῆς φύσεως τῆς ἀνθρωπείας ἀπολαύειν, κἂν ὡς βέλτιστα {u12} δοκῶσιν. ἐπεὶ κἀν τῷδε τῷ παντὶ τοσούτων καλῶν καὶ το-', [.025,.485,.44,.73], 'τὰ χείριστα καὶ τὰ κάλλιστα', 'τοσούτων καλῶν καὶ τοσαύτης')],
 (160,3):[(None,'σαύτης ἀγαθῆς τύχης μετειληφότι καὶ οὐδὲν ἔξω δήποθεν αὑτοῦ λελοιπότι τῶν καλῶν πολλὰ ἂν εὕροις, οἷς ἥκιστα ἂν {u0}. ἀλλ’ οὐ κατηγορεῖς διὰ ταῦτα τοῦ παντὸς οὐδὲ τοῦ ποιήσαντος, {u1} νομίζεις ἄλλον τινὰ {u2} βελτίω {u3} ποτ’ ἂν αὖθις δημιουργὸν τῶν ὅλων· ἀλλὰ δίδως τῇ φύσει ταῦτα {u4}, καὶ οὐ πολυπραγμονεῖς. τί δὴ θαυμαστόν, εἰ καὶ Ἀθήνησί τι τῶν πάντων οὕτως ἔχον ὥσπερ ἴσως ἂν που καὶ ἄλλοθι, καὶ συνεχώρησαν οἱ προεστῶτες ἅμα μὲν τὴν τῶν πολλῶν πενίαν καὶ χρείαν ἐπανορθούμενοι, δι’ ἣν οὐκ ἐλάχιστα τῶν ἁμαρτημάτων συμβαίνει, ἃ κωλύειν μᾶλλον οὗτος ἡγεῖτο, ἅμα δὲ εὐλαβούμενοι μή τι καὶ χεῖρον ἐξεργάσαιντο τῷ κατείργειν παντελῶς αὐτάς. τί γὰρ οὐκ ἦν προσδοκῆσαι ποιήσειν ἀνθρώπους τοσούτους τὸ πλῆθος καὶ οὕτως ὀξεῖς, καὶ χρημάτων τοσούτων παρόντων, εἰ μηδεὶς αὐτοῖς μετεδίδου τὰ μέτρια; ἆρ’ οὐ πάντ’ ἂν αὐτοῖς ἐπιχειρῆσαι λαβεῖν; οὐκ ἔστι ταῦτα, ὦ Πλάτων, ἀλλὰ δυοῖν θάτερον· ἢ οὐκ ἦσαν Ἀθηναῖοι τοιοῦτοι οἵους σὺ κατητιάσω, ἢ πάντες μᾶλλον ἢ Περικλῆς αἴτιος, εἴπερ γε μήτε φαύλως ἐδείκνυ τὰ παλαίσματα, μήτε ἀσαφεῖς τινὰς ἢ κιβδήλας ἢ σκολιὰς παρεῖχε τὰς γραμμάς.', [.39,.105,.81,.48], 'τοσαύτης ἀγαθῆς τύχης', 'παρεῖχε τὰς γραμμάς.')],
 (160,4):[(None,'Ἐκ τῶν περὶ Κίμωνος.',[.39,.30,.81,.54],'Ἐκ τῶν περὶ Κίμωνος.','Ἐκ τῶν περὶ Κίμωνος.','unclassified-heading')],
 (160,5):[(None,'ὅτι ὁ Κίμων Μιλτιάδου μὲν ἔφυ πατρός, εὐήθης δὲ τὰ πρῶτα δόξας ὕστερον ἐν πολλοῖς καὶ στρατηγῶν εὐδοκίμησεν. {u0} δὲ κατῆλθε, καὶ στρατηγήσας ἐνίκησεν ἐπ’ Εὐρυμέδοντι ποταμῷ καὶ κατὰ γῆν καὶ κατὰ θάλασσαν. τέθνηκε δὲ τὸ Κίτιον τῆς Κύπρου πολιορκῶν.', [.39,.30,.81,.54], 'ὅτι ὁ Κίμων Μιλτιάδου', 'τῆς Κύπρου πολιορκῶν.', 'unclassified-small-type')],
 (160,6):[(None,'Ἐβουλόμην δ’ ἂν καὶ πρὸς ἄλλον τινά μοι τὸν ἀγῶνα τυγχάνειν ὄντα καὶ μὴ πρὸς Πλάτωνα, καὶ περὶ τοῦτο λέγω καὶ περὶ τῶν ἄλλων, ἵνα πᾶσιν οἷς εἶχον ἐχρώμην θαρρούντως, καὶ μὴ συνέβαινέ μοι παραπλήσιον ὥσπερ ἂν εἰ πλέων, καὶ παρὸν ἐξ οὐρίας {u0}, εἶτα ὑφιέμην ὑπὸ δειλίας, ἢ καὶ ἵπποις ἀγωνιζόμενος, ἐξὸν καὶ ταχὺ καὶ τοσοῦτον ὅσον βούλομαι παρενεγκεῖν, εἶτ’ ἀνεῖχον ἐξεπίτηδες φειδοῖ τοῦ προειληφότος· οὕτω πολὺ πλείω ποιοῦμαι λόγον μηδὲν ἀπηχὲς εἰς Πλάτωνα τυχεῖν εἰπὼν μηδ’ ὥσπερεὶ {u1} δοκεῖν, ἢ ἐκείνων ἕκαστον ἐπαινέσαι, εἰκότως·', [.39,.485,.81,.73], 'Ἐβουλόμην δ’ ἂν', 'ἐπαινέσαι, εἰκότως·')]
}
UNCERTAINTIES={
 (160,2):[
 ('τῶν πολιτῶν','τοὺς πολίτας / τὰς πολίτας','The compact article and the following noun ending remain unresolved independently; preserve the exact original span and differing digital reading.'),
 ('χρή· ἢ','χρῆσθαι','The compact sigma/theta glyph is not independently resolved.'),
 ('μίμνεσθαι','μέμφεσθαι','The compact medial letters and sigma/theta glyph remain unresolved.'),
 ('ἀρχεῖν δὲ','αἰσχύνεσθαί','The compact sigma/chi and sigma/theta groups remain unresolved.'),
 ('μὴχεθαι','μάχεσθαι','The compact sigma/theta glyph remains unresolved.'),
 ('μὴ-μεθαι','μάχεσθαι','The compact sigma/theta glyph remains unresolved.'),
 ('ἀποκρίναι','ἀποκρίνασθαι','The compact final sigma/theta glyph remains unresolved.'),
 ('μαχεῖσθαι','μάχεσθαι','The compact sigma/theta glyph and accent remain unresolved.'),
 ('χρήσασθαι','χρήσασθαι','This unchanged original has a compact sigma/theta group; preserve it with localized uncertainty.'),
 ('ἄκων','ἀκούω','The compact vowel group and final letter remain unresolved independently; digital ἀκέω is a differing reading.'),
 ('κεκρώθῃ','κεκρᾶσθαι','The compact sigma/theta group and ending remain unresolved.'),
 ('κρίνεται','κρίνεσθαι','The compact sigma/theta group and ending remain unresolved.'),
 ('οἰκεῖν','οἰκεῖσθαι','The compact final sigma/theta group remains unresolved.')],
 (160,3):[
 ('ἡδεῖς','ἡσθείης','The compact sigma/theta group and ending remain unresolved.'),
 ("ἀλλ' νομίζεις",'ἀλλ’ νομίζεις / οὐδὲ νομίζεις','The short connective differs from the digital reading; its exact letters remain unresolved independently.'),
 ('δή πῃ','δή πῃ / δή που','The short particle and vowel group remain unresolved; digital δή που is a separate alternative.'),
 ('γενέσθαι','γενέσθαι','The unchanged compact sigma/theta group is not independently resolved.'),
 ('ἐφελκύεσθαι','ἐφειλκύσθαι','The compact sigma/theta group and preceding vowel remain unresolved.')],
 (160,5):[('ἐκστρατευσθεὶς','ἐξοστρακισθεὶς','The compact medial letters and sigma/theta group in this small type remain unresolved independently.')],
 (160,6):[('κομιζόμενος','κομίζεσθαι','The compact sigma/theta group and final ending remain unresolved.'),('θαυσόμενος','θρασύνεσθαι','The compact medial letters and sigma/theta group remain unresolved.')]
}
LEADING_FRAGMENTS={(160,3):'σαύτης'}


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
