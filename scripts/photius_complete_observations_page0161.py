"""Complete direct scan observations for retained historical physical page161."""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:06:09.960369Z'
CHUNKS={
 (161,1):[('ἀμφο-','οὐδὲ γὰρ ἐλάττονος ἄξια χάριτός μοι τὰ πρὸς τοῦτον. οὐ μὴν ἀλλ’ εἴγε ἄμφω {u0} καὶ τὰς κατ’ ἐκείνων αἰτίας {u1} καὶ Πλάτωνι πᾶν ὅσον αἰδοῦς καὶ τιμῆς ἔξεστι σεσωκέναι, καὶ προσέσται τὸ δίκαιον ἀμφο-', [.20,.105,.60,.34], 'οὐδὲ γὰρ ἐλάττονος', 'μετρίως ἂν ἔχοι τὸ δίκαιον πανταχῇ.'),('1280','',[.20,.105,.60,.34],None,None,'marginal-reference','1280R.'),(None,'τέροις, μετρίως ἂν ἔχοι τὸ δίκαιον πανταχῇ.',[.20,.105,.60,.34],'οὐδὲ γὰρ ἐλάττονος','μετρίως ἂν ἔχοι τὸ δίκαιον πανταχῇ.')],
 (161,2):[('δουλεία,','“εἰ γὰρ τἀναντία τοῖς ἐναντίοις {u0}, πῶς ἕκαστον ἐφ’ ἑαυτοῦ σώσει τὴν ἑαυτοῦ φύσιν; εἰ γὰρ ἡ ἀρχὴ δουλεία,',[.20,.105,.60,.34],'"εἰ γὰρ τἀναντία','ἡ ἀρχὴ δουλεία,'),('67a Ἡ','',[.20,.105,.60,.34],None,None,'marginal-reference','692H.'),(None,' σχολῇ γ’ ἂν ἄλλο τι δουλείαν ἐκφύγοι. κἂν εἰ γε τὴν ἀρχὴν δουλείαν εἶναι {u1}, τί κωλύει καὶ τὴν δουλείαν ἀρχὴν τοῖς αὐτοῖς τούτοις τίθεσθαι λόγοις; κἂν τοῦτο περιέλθῃ ἡμῖν ἡ θέσις καὶ οὐδέ ποτε ἐν τῷ αὐτῷ μένῃ, ἀλλ’ ἡ μὲν ἀρχὴ δουλεία πρότερον γενομένη δι’ ἐκείνης πάλιν ἀρχὴ γίνηται, ἡ δ’ αὖ δουλεία πρότερον ἀρχὴ {u2} ὑπ’ αὐτῆς τῆς ἀρχῆς ἐπάνεισι δουλεία πάλιν εἶναι. καὶ οὕτω {u3} καὶ μεταχωρήσει τὰ ὀνόματα ταῦτα, τῶν ἐναντίων πραγμάτων ὄντα, εἰ δὲ βούλει, τὰ ἐναντία τοῦ πράγματος.',[.20,.105,.60,.515],'σχολῇ γ’ ἂν ἄλλο','τὰ ἐναντία τοῦ πράγματος.')],
 (161,3):[(None,'τοῦ πράγματος εἶναι, {u1} ἐν καὶ ταὐτὸν εἶναι τὴν ἀρχὴν καὶ τὴν δουλείαν {u0}.',[.20,.30,.60,.54],None,None,'unclassified-small-type')],
 (161,4):[('παρέ-','τοιούτους ἐπικούρους ὦ Πλάτων τοῖς Ἕλλησι παρέ-',[.20,.30,.60,.54],'τοιούτους ἐπικούρους','τοὺς Ἕλληνας.'),('20','',[.20,.30,.60,.54],None,None,'marginal-reference','20'),(None,'σχετο, ὥστε ἕως ἔζη Κίμων, τεθνάναι περιῆν τοῖς βαρβάροις τῷ φόβῳ τοὺς Ἕλληνας.',[.20,.30,.60,.54],'τοιούτους ἐπικούρους','τοὺς Ἕλληνας.')],
 (161,5):[(None,'{u2} τὸ σχῆμα· {u0}· τῷ δὲ φόβῳ τοὺς Ἕλληνας ἀντὶ τῷ φόβῳ τῶν Ἑλλήνων, καὶ ὅτι κατέστησεν τοὺς Ἕλληνας οὕτως ὡς ἐγγὺς τῷ τεθνάναι {u1}.',[.20,.30,.60,.54],None,None,'unclassified-small-type')],
 (161,6):[('μετέγνωσαν καὶ','Νὴ Δία ἀλλ’ {u0} αὐτόν, ὅπως αὐτοῦ δέκα ἐτῶν τῆς φωνῆς μὴ ἀκούσειαν. καὶ πάλιν γε κατήγαγον, πρὶν τὰ δέκα ἐξήκειν ἔτη, ἵνα αὐτοῦ τῆς φωνῆς ἀκούσειαν· οὕτως ἐπόθησαν. σὺ δὲ ὡς μὲν κατέγνωσαν, λέγεις, ὡς δὲ μετέγνωσαν, οὐκ ἐνθυμῇ. καὶ ἃ μὲν ἀδίκως ἐψηφίσαντο κατ’ ἀμφοτέρων, λέγεις, ἃ δὲ ὀρθῶς ἐβουλεύσαντο, οὐχ ἡγῇ τοῖς μὲν προαχθεῖσι παραίτησιν τῷ δὲ ἀφεθέντι μεγίστην πίστιν τῆς ἀρετῆς ἔχειν. καὶ ὡς ἔοικεν, οἱ μὲν καταγνόντες αὐτοὶ μετέγνωσαν καὶ',[.20,.46,.60,.73],'Νὴ Δία ἀλλ’','αὐτοὶ μετέγνωσαν καὶ'),('30','',[.20,.485,.60,.73],None,None,'marginal-reference','30'),('ἀρετῆς',' οὐκ ἔμειναν ἐφ’ ὧν ἔγνωσαν ἐξ ἀρχῆς, σὺ δὲ ὥσπερ τι κύριον ἐγκέκληκας, καὶ οὐκ ἠξίωσας ταύτῃ {u1} τοὺς Ἀθηναίους, ἀφεὶς τὸν ἄνδρα τῆς αἰτίας, ἀλλ’ ὃ μὲν ἦν χαλεπώτερον αὐτῶν ἐμιμήσω, τὸ δὲ λοιπὸν εἴασας. καὶ μὴν πολὺ μεῖζον καὶ κάλλιον εἰς ἀρετῆς',[.20,.485,.60,.73],'οὐκ ἔμειναν','εἰς ἀρετῆς λόγον'),(None,'',[.20,.485,.60,.73],None,None,'marginal-reference','40')],
 (161,8):[(None,'λόγον ἐκπεσόντα κατελθεῖν ἢ μὴ φυγεῖν ὅλως. τὸ μὲν γὰρ καὶ τοῖς τυχοῦσιν ὑπάρχει δή που, τοῦτο δὲ οὐ κατὰ τοὺς πολλοὺς ἄνδρας ἦν· κἀκεῖνο μὲν ἂν τῇ τύχῃ τις εἶχε {u0}, τοῦτο δὲ τῷ κρείττονα ἢ κατὰ τοὺς ἄλλους ὄντα {u1}. τὸ μὲν γὰρ ἐκπεσεῖν καὶ φεύγειν φθόνος αἴτιος καὶ τύχη ἄν τι καὶ ἄλλο τοιοῦτο φανείη, τῆς δὲ πρὸ τοῦ χρόνου κλήσεως καὶ παρακλήσεως οὐδὲν ἔσθ’ ἕτερον πλὴν τῆς ἀρετῆς {u2}, δι’ ἣν καὶ ἀπόντα {u3} καὶ παρεῖναι λυσιτελεῖν αὑτοῖς ὑπελάμβανον, καὶ τὸ μέγιστον, σφῶν αὐτῶν καταγιγνώσκειν μᾶλλον ἠξίουν ἢ ἐκείνου. ὥστε εἰ μὲν αὐτὸν ἐφ’ ἑαυτοῦ δεῖ σκοπεῖν, τί δεῖ λέγειν, εἴ τις εἰς ἐκεῖνον ἐξήμαρτεν; εἰ δὲ ἀπὸ τῶν ἄλλων αὐτὸν δεῖ θεωρῆσαι, διαφερόντως οὗτος τιμηθεὶς φαίνεται. ἀλλὰ μή πω ταῦτα· αὐτίκα γὰρ μᾶλλον ἴσως ἁρμόσει.',[.56,.105,.97,.36],'λόγον ἐκπεσόντα','ἴσως ἁρμόσει.')],
 (161,9):[(None,'ἤγουν ἐν τῇ κοινῇ ἀπολογίᾳ.',[.56,.30,.97,.54],None,None,'unclassified-small-type')],
 (161,10):[(None,'Ὑπὲρ Μιλτιάδου. τὸ προοίμιον.',[.56,.30,.97,.54],'Ὑπὲρ Μιλτιάδου.','τὸ προοίμιον.','unclassified-heading')],
 (161,11):[(None,'Περιήκει δ’ ἡμῖν ὁ λόγος εἰς αὐτὸν τὸν Μιλτιάδην, ὃν ἐγὼ μᾶλλον {u0} ἐπαινῶν ἢ ψέγων· οὕτω μοι δοκῶ πάντα ἂν ἔλαττον εἰπεῖν ἢ βούλομαι.',[.56,.30,.97,.54],'Περιήκει δ’ ἡμῖν','ἢ βούλομαι.')],
 (161,12):[('μη-','Μιλτιάδης δὲ πάλαι “πεπεικὼς ἦν Ἀθηναίους μη-',[.56,.30,.97,.54],'Μιλτιάδης δὲ πάλαι','νόμων ἡγεῖσθαι,'),('1291A.','',[.56,.30,.97,.54],None,None,'marginal-reference','1281R.'),(None,'δένα δεσπότην πλὴν τῶν νόμων {u0}, μηδὲ τοῦ καλοῦ καὶ δικαίου μηδένα κρείττω νομίσαι φόβον, μηδ’ οὕτως ἀνάγκην ἰσχυρὰν δι’ ἣν προσήκειν {u1} χείροσι. διὰ ταῦτα εἶχεν ὅ τι χρῷτο αὐτοῖς. ἀλλ’ ὥσπερ οἱ γεωργοὶ πολλοστῷ μηνὶ τῶν σπερμάτων τὴν ἐπικαρπίαν κομίζονται, καὶ οὐχ ἅμα τῷ καταβαλεῖν, οὕτω καὶ ἐκεῖνος Μιλτιάδης παλαιαῖς ὁμολογίαις κατειληφὼς εἶχεν ἐν καιρῷ χρησίμους, οὐκ ἐπὶ τῆς χρείας λαμβάνοντας τὰ μαθήματα (αἰσχρῶς γ’ ἂν οὕτω γε χορὸς ἠγωνίσατο αὐτῷ) ἀλλ’ ἐπὶ τῆς ἐξουσίας εἰς τὴν χρείαν ἠσκημένος. οἷα τοίνυν καὶ Μιλτιάδου προεστῶτος τοὺς μὲν ὡς πλεῖστον τῆς ἐκείνου δυνάμεως ἀπολαῦσαι, τοὺς δὲ μέσως· κἂν τῷ μέσῳ τὸ παραλλὰξ αὖ τίθει. γένοιτο δ’ ἄν τις ἐν πλήθει καὶ περὶ ὦτα ἀτυχέστερος· οὔ τοι πάντας οὐδ’ ὁ ἥλιος οἷός ἐστι θερμαίνειν, ἀλλ’ ἤδη τις ἐν καθαρῷ τῆς μεσημβρίας ἐρρίγωσε, τῆς καταβολῆς {u2}. ἀλλ’ ἐκεῖνος ὁ καιρὸς ὥσπερ κῆρυξ ἐκάλει τῶν Ἑλλήνων τὸν ἀνδρειότατον καὶ τὸν ἐκ πλείστου τοῖς ἀρίστοις λογισμοῖς ὡμι-', [.56,.30,.97,.73], 'μηδένα δεσπότην','τοῖς ἀρίστοις λογισμοῖς ὡμιληκότα,')]
}
UNCERTAINTIES={
 (161,1):[('συμβήσεται','συμβήσεσθαι','The compact sigma/theta group remains unresolved.'),('ἀπολύσασθαι','ἀπολύσασθαι','The unchanged compact sigma/theta group remains unresolved.')],
 (161,2):[('ὁρῶμενθα','ὁριούμεθα','The compact verb and vowel group remain unresolved independently.'),('πεποίθμεν','τιθείημεν','The compact verb and its ending remain unresolved; digital τιθείημεν is a separate alternative.'),('νομιζθεῖσα','νομισθεῖσα','The compact sigma/theta group remains unresolved.'),('πλανηθεῖσι','πλανήσεσθαι','The compact sigma/theta group remains unresolved; digital πλανήσεται differs.')],
 (161,3):[('κατεσυλλογίσασθαι','κατασυλλογίσασθαι','The compact small-type sigma/theta group and medial letters remain unresolved.'),('διωὡς ἑκαδὴ','δεινῶς ἑκαδὴ','The small-type adverb and adjacent short words remain unresolved independently; no digital counterpart is available for this inset.')],
 (161,5):[('Ἦρη γὰρ ἠτιδύσασ τῷ διὰ τοὺς ἀποσολούς','ἔφη γὰρ ἐπεδύσατο διὰ τοὺς ἀποστόλους','The small-type clause remains unresolved independently; no digital counterpart is available.'),('γενέσθαι','γενέσθαι','The unchanged compact sigma/theta group remains unresolved.'),('Ἀποσοθεῖναι','Ἀποσθενικῶς','The small-type initial technical word remains unresolved independently.')],
 (161,6):[('ἐξασφάλισαν','ἐξωστράκισαν','The compact medial consonants remain unresolved independently.'),('μνημόσθη','μιμήσασθαι','The compact medial letters and sigma/theta group remain unresolved.')],
 (161,8):[('λογίζεσθαι','λογίζεσθαι','The unchanged compact sigma/theta group remains unresolved.'),('γιγνώσκειν','γιγνώσκεσθαι','The compact sigma/theta group remains unresolved.'),('αἰτιῶν','αἰτιᾶσθαι','The compact sigma/theta group and ending remain unresolved.'),('ἡχέοντο','ᾐσχύνοντο','The compact sigma/chi group and first vowel remain unresolved independently.')],
 (161,11):[('αἰχνοῦμαι','αἰσχυνοίμην','The compact sigma/chi group and ending remain unresolved independently.')],
 (161,12):[('ἡγεῖσθαι','ἡγεῖσθαι','The unchanged compact sigma/theta group remains unresolved.'),('γενέσθαι','γενέσθαι','The unchanged compact sigma/theta group remains unresolved.'),('ἐπιλάθους','ἐπελθούσης','The compact vowel group and ending remain unresolved independently.')]
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
                if (page,number)==(161,1) and text.startswith('τέροις'):
                    fragments.append({'start':0,'end':6,'text':'τέροις','side':'leading','qualification':'Printed continuation after an intervening marginal reference of the divided word ἀμφο-τέροις; retain this suffix without counting it as a standalone word.'})
                if (page,number)==(161,4) and text.startswith('σχετο'):
                    fragments.append({'start':0,'end':5,'text':'σχετο','side':'leading','qualification':'Printed continuation after an intervening line number of the divided word παρέ-σχετο; preserve the source suffix without lexical admission.'})
                if (page,number)==(161,12) and text.startswith('δένα'):
                    fragments.append({'start':0,'end':4,'text':'δένα','side':'leading','qualification':'Printed continuation after an intervening marginal reference of the divided word μη-δένα; preserve the source suffix without lexical admission.'})
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
