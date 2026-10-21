"""Complete direct scan observations for retained historical physical page158."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T12:55:56.309387Z'
CHUNKS={
 (158,1):[
  ('1272R','',[.025,.105,.44,.34],None,None,'marginal-reference','1272R.'),
  (None,' “{u0} τὰ αὐτὰ ὑπὲρ τῆς κοινῆς ἀπολογίας, ὁ τὸν ὅμοιον διὰ τῆς ἐκλογῆς περιηνθισμένος τρόπον. [ὑπὲρ Περικλέους.]',[.025,.105,.44,.34],'Ἀνεγνώσθη τὰ αὐτὰ','[ὑπὲρ Περικλέους.]')],
 (158,2):[(None,'Ἐκ τοῦ Ἀριστείδου πρὸς Πλάτωνα',[.025,.105,.44,.34],'Ἐκ τοῦ Ἀριστείδου','Πλάτωνα','unclassified-heading')],
 (158,3):[(None,'ὑπὲρ τῶν τεσσάρων.',[.025,.105,.44,.34],'ὑπὲρ τῶν τεσσάρων.','ὑπὲρ τῶν τεσσάρων.','unclassified-heading')],
 (158,4):[(None,'τὸ προοίμιον.',[.025,.105,.44,.34],'τὸ προοίμιον.','τὸ προοίμιον.','unclassified-heading')],
 (158,5):[
  ('κακοθησίας εἶναι.', '{u0} μὲν οὐκ οἶδ’ ὅ τι δεῖ περὶ τῶν αὐτῶν πολλάκις, ἄλλως τε καὶ πρὸς ἄνδρας μέλλοντας ἐρεῖν μᾶλλον ἢ ὑπὲρ ἀνδρῶν καλῶν καὶ ἀγαθῶν, καὶ τούτων οὐκ ὀλίγων, οὐδὲ ἧττον παλαιῶν ἢ Πλάτων, ὅτι μὴ καὶ {u1}, εἴ τῳ καὶ τοῦτο {u2} ἄξιον εἶναι δοκεῖ. ὥστε ὅταν ὡμολόγητο καὶ συγκεχώρητο ὑπὲρ ὃ πᾶς ἤνυτο ὁ λόγος καὶ πρὸς ὃ πάντα ταῦτ’ εἶχε τὴν ἀναφοράν, τίς ἦν ζημία τῶν ἀνδρῶν μὴ {u3}; νῦν δ’ ὥσπερ ὠδίνων, καὶ περιβαλλόμενος κύκλῳ τὴν ἐπ’ ἐκείνους ὁδόν, ὅπως ἐπιβούλως ἐλθὼν ἐπὶ τοὺς [κατ’ ἐκείνων τοὺς] λόγους φαίνεται. καὶ μὴν τὸ μὲν διάφορον οὐχὶ μικρόν· ἐκεῖνο μὲν γὰρ ἦν ὑπὲρ αὐτῆς τῆς ἀληθείας {u4}, τοῦτο δὲ ἐγὼ μὲν οὐδέ ποτε ἂν φήσαιμι, ἄλλος δ’ ἄν τις εἴποι διαβάλλων ἐν πόρρω κακοηθείας εἶναι.', [.025,.25,.44,.48], 'Παραιτεῖσθαι μὲν', 'κακοηθείας εἶναι.'),
  ('ἀθεμιτόντα', ' Περικλῆς τοίνυν τά τε ἄλλα τὸν βίον ἦν ἄριστος, καὶ οὐδὲ γελῶν πώποτε ὑπό τινος ὤφθη. καὶ τῇ μὲν τῆς πολιτείας φυλακῇ, καὶ τῷ τὸ ἴσον τοῖς ἄλλοις ἔχων ἀνέχεσθαι, κοινὸς (εἴπερ τις ἀνθρώπων) ἐσπούδαζεν εἶναι, τῷ δὲ ἀξιώματι τῆς γνώμης καὶ τῷ μὴ τῶν αὐτῶν ἡττᾶσθαι τοῖς πολλοῖς ὀλίγοις καταλιπεῖν ἐγγὺς ἐλθεῖν ἑαυτοῦ. ὃ δέ φασιν ὑπάρξαι Σωκράτει σοφιστῶν διαφερόντως, τοῦτ’ ἐκείνῳ δημαγωγῶν· ἐπαρθέντα μὲν γὰρ τὸν δῆμον καὶ μείζονα φρονήσαντα δεινότατον εἶναι συστεῖλαι καὶ καθελεῖν, ἀθυμήσαντα', [.025,.435,.44,.625], 'Περικλῆς τοίνυν', 'ἀθυμήσαντα'),
  ('682H.','{u5}',[.025,.485,.44,.73],None,None,'marginal-reference'),
  (None,'δὲ “καὶ ταπεινωθέντα ἀναγαγεῖν αὖ τοῖς λόγοις καὶ μεστὸν ἐλπίδων ποιῆσαι, ὥσπερ ἐκεῖνος εἰώθει περὶ τοὺς νέους ποιεῖν. συνελόντι δ’ εἰπεῖν, {u6} τῆς πόλεως ἦν Περικλῆς, {u7} δουλεύων ταῖς τῶν πολλῶν ἐπιθυμίαις, ἀλλ’ αὐτὸς ἄρχων τῶν πολλῶν, οὐδ’ ὅ τι δόξειεν ἐκείνοις τοῦτο λέγειν ἀξιῶν, ἀλλ’ ὅ τι δόξειεν',[.025,.485,.44,.73], 'δὲ "καὶ ταπεινωθέντα', "ἀλλ' ὅ τι δόξειεν")],
 (158,6):[(None,'αὐτῷ τοῦτ’ ἐκείνους πράττειν ἐπαναγκάζων, οὐδ’ ἐν κόλακος μοίρᾳ προσκείμενος, ἀλλ’ οὐδαμοῦ τοῖς κόλαξι πάροδον τὸ καθ’ αὑτὸν διδούς, τῇ μὲν χρηστότητι καὶ ταῖς ἐπιεικείαις ἐν πατρὸς ὢν τάξει τῷ δήμῳ, τῷ δὲ κατείργειν ἅπαντας καὶ πάνθ’ ὑφ’ ἑαυτὸν ἔχειν πλέον ἢ τύραννος. ἐξ ὧν, ὡς ἔοικεν, ἔξεστι σαφῶς ἰδεῖν ὅτι, εἴ τις ἄλλος, καὶ Περικλῆς ἑκὼν δίκαιος. οὐδαμοῦ γὰρ τὴν πλεονεξίαν ἀντὶ τῶν νόμων ἠγάπησεν, οὐδ’ ὅπως ἔσται μείζων τῆς τάξεως προὐνοήθη, παρὸν αὐτῷ μᾶλλον παντὸς Πεισιστράτου· ἀλλ’ ἦν παραπλήσιος κατέχοντι τὴν ἀκρόπολιν ἐπὶ τῷ σώζειν τοὺς νόμους καὶ τῷ πάντας εὖ ποιεῖν ἐκ μέσου [τοῦ δημοσίου].',[.39,.105,.81,.34],"αὐτῷ τοῦτ' ἐκείνους",'[τοῦ δημοσίου].')],
 (158,7):[(None,'οἷον ἴσως· τὸ γὰρ ἐκ μέσου φερόμενον ἴσον ἐπὶ πάντας ὥσπερ ἐπὶ κύκλου φέρεται, ἢ ὅτι ἡ ἀκρόπολις μέση κεῖται τῆς πόλεως.',[.39,.30,.81,.36],'οἷον ἴσως·','μέση κεῖται τῆς πόλεως.','unclassified-small-type')],
 (158,8):[
  ('ἐξέμενεν;', 'ἐπειδὴ δὲ ἐτελεύτησεν ἐκεῖνος, ὠνειροπόλουν μὲν Σικελίαν, ἐφίεντο δὲ Ἰταλίας, ὠρέγοντο δὲ Καρχηδόνος καὶ Λιβύης, πάντας δ’ ἀνθρώπους περιεσκόπουν, ἤρκει δὲ αὐτοῖς οὐδέν, μακροτέραν δὲ τοῦ πολέμου τὴν παρενθήκην ἐποιήσαντο. ὁ δὲ ταῦτα πείθων ἦν, ὦ Πλάτων τε καὶ Σώκρατες, ὁ ἡμέτερος κοινωνὸς μὲν οὐκ ἔστιν εἰπεῖν, ἑταῖρος δὲ καὶ αὐτὸς ἂν φαίης, μᾶλλον δ’ εἴρηκας. πῶς οὖν ἂν τις ταῦτα δικαίως κατηγοροίη Περικλέους, ἢ πῶς οὐκ ἀναγκαίως Ἀλκιβιάδου, ὅστις παραλαβὼν τὴν πόλιν εἰδυῖαν ἀκούειν συμβούλων, εἶθ’ οὕτως ἐξέμηνεν;', [.39,.335,.81,.54], 'ἐπειδὴ δὲ ἐτελεύτησεν', 'ἐξέμηνεν;'),
  (None,' οὐκοῦν τῷ μὲν ἅπαντος κέρδους κρείττω παρέχειν ἑαυτὸν δικαιοσύνην ἀσκῶν δῆλος ἦν, τῷ δὲ τὸν ἐν τάξει βίον ἀντὶ τῆς πρὸς ἡδονὴν {u0} σωφροσύνης πίστιν παρείχετο ἐμφανῆ. καὶ μὴν ἀνδρείας γε ἐν οἷς οὐ πρὸς χάριν οὐδ’ ὑποπεπτωκώς, ἀλλ’ ὡς οἷόν τε μάλιστα ἐλευθερίως ὡμίλει τῷ δήμῳ. μόνος τοίνυν καὶ τὰ μέλλοντα {u1} προειδὼς καὶ τοῖς παροῦσι {u2} δυνηθεὶς πῶς οὐκ ἂν σοφίας δικαίως δόξαν φέροιτο τῆς γέ που χρησιμωτάτης, εἴ τις ἀνθρωπίνως ἐθέλοι λογίζεσθαι; εἶθ’ ὃν ἐξ ἁπάντων τῶν τῆς ἀρετῆς μορίων ὑπάρχει προσειπεῖν ἀνδρεῖον, δίκαιον, φρόνιμον, σώφρονα, τοῦτον Πλάτων μετὰ τῶν κολάκων ἠρίθμησε. λάλους γάρ, φησίν, Ἀθηναίους ἐποίησε καὶ ἀργούς',[.39,.485,.81,.73],'οὐκοῦν τῷ μὲν ἅπαντος','καὶ ἀργὸς')],
}
UNCERTAINTIES={
 (158,1):[('Ἀνεγνώσθη','Ἀνεγνώσθη / Ἀνεγνώθη','The compact σθ group in this unchanged retained heading verb is unresolved independently. The digital spelling cannot alone certify its sigma component.')],
 (158,5):[
 ('Παρατεῖδι','Παραιτεῖσθαι','The compact initial verb and σθ group remain unresolved independently.'),
 ('-πρεσβύτερον ἐκεῖνον','πρεσβυτέρων ἐκείνου','The adjective and pronoun endings remain unresolved independently; digital πρεσβυτέρων ἐκείνων is retained as another reading.'),
 ('αὐδῆς','αἰδοῦς','The compact vowel and noun ending remain unresolved independently; digital αἰδῶς is another reading.'),
 ('προσοχάπετεῖν','προσκαθάπτεσθαι','The compact medial and final sigma/theta glyphs remain unresolved independently.'),
 ('ἀγωνιζόμενος','ἀγωνίζεσθαι','The compact sigma/theta ending remains unresolved independently.'),
 ('682H.','688H.','The last digit of the marginal reference is not independently resolved; retain the extracted label, exclude its role, and do not infer a number from neighboring labels.'),
 ('σχῆμα','σχῆμα / χῆμα','The sigma component of this unchanged compact σχ glyph remains independently unresolved.'),
 ('ὁ','οὐ','The compact negative at the beginning of the participial clause remains unresolved independently.')],
 (158,8):[
 ('προηρηθῶ','προῃρῆσθαι','The compact sigma/theta group and ending remain unresolved independently.'),
 ('ἐστω','ἔσεσθαι','The compact sigma/theta group and ending remain unresolved independently.'),
 ('χρήσας','χρήσασθαι','The compact sigma/theta group and ending remain unresolved independently.')],
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
