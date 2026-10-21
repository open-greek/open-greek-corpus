"""Complete direct scan observations for retained historical physical page170.

The pinned digital section is mismapped, so this page has scan-only observations.
Every retained source line was inspected in overlapping readable crops.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:23:05.576924Z'
LINES={
 1:'εἰ δὲ ἀδίκως αὐτῶν ἐκεῖνοι κατεψηφίσαντο, {u0}',
 2:'τοῖς ἀνδράσι πρόσεστιν, ἀδικεῖν δὲ οὐδαμῶς· τοῖς δ’',
 3:'ἀδικηθεῖσι βοηθεῖν, οὐκ ἐγκαλεῖν εἰκός ἐστιν. εἰ δέ του',
 4:'καὶ μὴ δυνατὸν βοηθεῖν, ἀλλ’ οὐχὶ καὶ δίκαιον ἐγκα-',
 5:'λεῖν. ἐγὼ δὲ ταῦτα μὲν τοῖς κοινοτέροις παρίημι· αὐ-',
 6:'τὸς δὲ τί φημι καὶ πῶς δέχομαι τὸν λόγον; οὐκ ἔστι',
 7:'δίκαιον ἅμα ἀμφοῖν κατηγορεῖν, καὶ τῷ δήμῳ {u0}',
 8:'{u0}· ἢ σαφῶς τοὺς ἑτέρους συγκαταψηφίσομεν. εἰ μὲν γὰρ',
 9:'ὀρθῶς ἐκεῖνα {u0}, ἠδίκουν μὲν (ὡς ἔοικεν)',
 10:'ἐκεῖνοι, τῷ δήμῳ δ’ ἃ προσήκει πέπρακται, ὥστε οὐχὶ {u0}',
 11:'δὴ πο ταῦτά γε δίκαιον κατηγορεῖν αὐτῷ. πῶς ἂν τοῖς',
 12:'ἀγριαίνουσι τῶν ζῴων αὐτὸν ἀπεικάζοντες ὀρθῶς φή-',
 13:'σομεν ποιεῖν; εἰ δ’ ἥμαρτεν ὁ δῆμος, ἅμα τε ἐκείνῳ',
 14:'ἡμάρτηται καὶ τοῖς ἀνδράσι τούτοις; ἀλλ’ οὐδ’. αὐτὸ γὰρ',
 15:'τοῦτο φαμεν δήπουθεν ἁμαρτεῖν Ἀθηναίους, τιμήσαν-',
 16:'τας ἐκείνους φυγῆς ἢ χρημάτων ἢ ὁτουδήποτε ἐτίμη-',
 17:'σαν ἐκείνους. οὗτος δὲ ὁ λόγος τί λέγει; μηδενὸς τούτων',
 18:'ἐκείνους ἀξίους εἶναι. καὶ μὴν εἴ γε ἠδίκουν, ἄξιοι τούτων',
 19:'ἦσαν· ὅτι δὲ οὐ τούτων ἄξιοι, σαφῶς οὐκ ἠδίκουν. τοὺς δ’',
 20:'οὐκ ἀδικήσαντας κακῶς λέγειν καὶ συκοφαντεῖν οὐ δίκαια',
 21:'ποιεῖν ἐστίν. ἡμεῖς τοίνυν ἀντὶ τοῦ κατηγορεῖν ἀμφο-',
 22:'τέρων ὑπὲρ ἀμφοτέρων τὰ πρέποντα ἀπολογούμεθα,',
 23:'ὅτι τῷ δήμῳ τὴν αἰτίαν παντός εἶναι φάσκοντες, ὅτι',
 24:'ἐκείνοις {u0}, εἰ ὅτι προσέπταισαν, χείρους νο-',
 25:'{u0}. καὶ οὐκ ἐπὶ μὲν τῶν ἀθλητῶν οὕτω συμ-',
 26:'βαίνει, τὰ δὲ τῆς μουσικῆς ἐναντία ἔχει τὴν νίκην',
 27:'τοῖς κρείττοσιν, ἀλλὰ κἀνταῦθα τὸ τοῦ Πινδάρου κρα-',
 28:'τεῖ· πάνυ γὰρ μετ’ ἀληθείας τότ’ ἐκεῖνος ἐμνήσθη “ἐν',
 29:'ἔργμασι νικᾷ τύχα, οὐ σθένος.” ὥστε ἰδὼν τὸν Εὔ-',
 30:'μηλον Ἀχιλλεὺς τοῦ ἅρματος ἐκπιπτόντα ᾤκτειρέ τε',
 31:'καὶ λέγει',
 32:'λοίσθιος ἀνὴρ ἄριστος ἐλαύνει μώνυχας ἵππους.',
 33:'ἆρ’ οὐ παράδοξον ἑξῆς οὑτωσὶ θεῖναι παράλληλα, καὶ',
 34:'τὸν αὐτὸν λοίσθιόν τε καὶ ἄριστον προσειπεῖν; ἀλλ’ ὅμως',
 35:'τοιαῦτα, φησί, τὰ ἀνθρώπινα (τοῦτο γάρ μοι δοκεῖ τῶν',
 36:'ῥημάτων τὸ βούλημα εἶναι·) ὁ αὐτὸς ἀνὴρ ἄριστός τε',
 37:'καὶ ἔσχατος. ὅπερ περὶ τὸν δακτύλιον φασὶ ποτ’ εἰπεῖν',
 38:'Ὀρόντην τὸν Πέρσην, ὡς ὁ αὐτὸς ὢν τῇ θέᾳ ποτὲ',
 39:'μὲν τὰ μύρια σημαίνει, ποτὲ δ’ οὐ πλέον ἢ ἕν. ὡς',
 40:'ἐμοὶ μὲν ἀντικρὺς εἰς τὸ Πλάτωνος παράδειγμα ὁ Εὔ-',
 41:'μηλος τείνειν δοκεῖ, κατά τε ἄλλα, καὶ οὐχ ὅσον τῆς νίκης ἐξερίφθη, ἀλλὰ καὶ {u0} περιεδρύφθη σῶμά τε ῥῖνάς τε ὑπὸ τῶν ἵππων τῶν ἰδίων καὶ ἐφ’ ὧν οὐδὲ πώποτε ἐσφάλη.',
 42:'“Ὀρόντης ὁ Πέρσης ἐκπεσὼν τῆς ἀρχῆς· {u0} ἔφη “ποτὲ μὲν ἓν ποτὲ δὲ μύρια σημαίνων.”',
 43:'εἰ φίλους ἔχεις, εἰ χρήμασιν, εἰ δόξαν ἔχεις ἐν τῇ πόλει, μηδενὶ τούτων ἐπαρθῇς, μηδὲ μεῖζον φρονήσῃς τῆς ἐξουσίας. εἰ πάντων κρατήσεις, ἡττήσῃ τῆς τύχης.',
 44:'ταῦτ’ ἐστὶν ὁ ἀγὼν οὗτος, ταῦθ’ Ὅμηρος λέγει. οὐδὲν τῶν ἀνθρωπείων ἀσφαλὲς οὐδ’ ὁμαλὸν οὐδ’ ἀτάραχον, ἀλλ’ {u0} μὲν ὁ ἰσχυρὸς τῷ ἀνδρείῳ, ὅταν καιρὸς ἢ τύχη, {u1} δὲ Βαβυλὼν αὐτοῖς τείχεσι, πάλιν δὲ τοὺς Πέρσας πορθήσασιν ἕτεροι· πάντα ταῦτα ἐναλλὰξ',
 45:'{u0}. εἰ δὲ ἔσωζον μὲν οἱ κυβερνῆται πάντες ἅπαντας τοὺς ἐμπλέοντας, ἔσωζον δ’ οἱ ἰατροὶ πάντες ἅπαντας τοὺς κάμνοντας, ἐνίκων δὲ οἱ κρείττονες, ἐνίκων δὲ οἱ μείζονες, τὸ δ’ ἀεὶ τούτοις πᾶσι προσῆν, μηδεὶς δ’ ἐσφάλλετο τῶν ἀρξαμένων κατορθοῦν, εὐχὴ',
 46:'οὐδὲ καὶ δύναμις μηδενὶ διέφερον, ἀθάνατα πάντ’ ἦν τὰ τῶν ἀνθρώπων πράγματα, καὶ οὐδὲν ἂν ἴσως εὐτυχὲς προσείη, οὐδ’ ἂν κατέπληξεν ἡμᾶς τῶν πόθων ἕτερος ὥσπερ νῦν. μὴ τοίνυν θαυμάσῃς εἰ Περικλῆς ἔχων ἐπιστήμην καὶ τέχνην τῷ θεῷ καὶ τῆς τύχης ἡττᾶτο·',
 47:'μηδ’ ἀμνημόνει τῶν καιρῶν, ὡς αὐτὸς φῇς οὐκ ἐξ ὀλίγου {u0}, οἷς οὐ προσηκόντως ἐκεῖνος τότε χρησάμενος φαίνεται. πολλὰ καὶ παράδοξα κατ’ ἀνθρώπους καὶ γέγονε καὶ {u1}· ὧν ἐστὶ καὶ τὰ τότε τοῖς ἀνδράσι συμβάντα. τίς δ’ ἂν οὐκ φαίη; ἀλλ’ ἔστω ταῦτά ἐστιν ἔλεγχος',
 48:'κατ’ αὐτῶν ὡς ὅτε {u0} χρηστὸν οὐδὲν, ὅτε ἐδύναντο βελτίους ποιεῖν· ἀλλ’ ἐξῆν αὐτοῖς τήν γε τέχνην δήπουθεν ἔχειν καὶ τὸ χρηστοῖς εἶναι, εἰ καὶ τῶν μειζόνων ἐπικουρῶν ἐν γε τῷ τότε ἐξήρτητο. ἡδέως δ’ ἂν ἐροίμην, ὅστις βούλεται {u1} τὸ ἐρώτημα ὑπὲρ',
 49:'Πλάτωνος, αὐτὸς δὲ δὴ τί μαθὼν ἡμῖν ὁ Πλάτων οὐκ ἐπολιτεύσατο; ἆρ’ ἄλλο τι φήσομεν ἂν ἀξιοῦν ἢ τὸ αὐτὸ τοῦτο, ὅπερ καὶ Σωκράτης λέγων ἐκεῖνος {u0}; τί μὴν ἕτερον; εἶθ’ ὁ φοβηθεὶς μὴ πάθῃ οὐκ ἐδημηγόρει, ταῦτ’ εἴ τις ἐκείνῳ πέπονθεν, ὡς οὐ τὰ βέλ-',
 50:'τιστα συνεβούλευεν {u0}; καὶ μὴν {u1} μὲν οὐδεὶς {u2}'
}
UNCERTAINTIES={
 (170,1):[('ἀδικηθή-','ἀδικεῖσθαι','The compact sigma/theta group remains unresolved; the original OCR hyphen does not establish a complete source word.')],
 (170,7):[('νικη-','νικῶ-','The compact word ending is unresolved independently at the printed division.')],
 (170,8):[('ντὸν','ντων','The printed continuation and accent remain unresolved independently.')],
 (170,9):[('κατεγνώσθη','κατεγνώσθη','The unchanged compact sigma/theta group remains unresolved independently.')],
 (170,10):[('νῦν','νῦν','The compact terminal word remains unresolved independently; retain its original display.')],
 (170,24):[('προσέσχεν','προσέχειν / προσέσχεν','The compact sigma/chi group and ending remain unresolved independently.')],
 (170,25):[('μιζομένη','μίζεσθαι','The compact sigma/theta group remains unresolved in this printed continuation.')],
 (170,41):[('ἀγωνίᾳ τε','ἀγκῶνάς τε','The compact noun and ending remain unresolved independently.')],
 (170,42):[('καὶ ὁ δέσποτες','καὶ ὁ δέσποτος','The small-type phrase is unresolved independently.')],
 (170,44):[('ἡττήσεται','ἡττήσεσθαι','The compact sigma/theta group remains unresolved independently.'),('ἁλώσεται','ἁλώσεσθαι','The compact sigma/theta group remains unresolved independently.')],
 (170,45):[('περιέρχεται','περιέρχεσθαι','The compact sigma/theta group remains unresolved independently.')],
 (170,47):[('δύναι·)','δύνασθαι','The compact sigma/theta group remains unresolved independently.'),('γενήσεται','γενήσεσθαι','The compact sigma/theta group remains unresolved independently.')],
 (170,48):[('ἡττήσαντο','ἠπίσταντο','The compact initial and medial consonants remain unresolved independently.'),('δέξασθαι','δέξασθαι','The unchanged compact sigma/theta group remains unresolved independently.')],
 (170,49):[('φαίνεται','φαίνεσθαι','The compact sigma/theta group remains unresolved independently.')],
 (170,50):[('ἰσχυρίζεται','ἰσχυρίζεται','The compact sigma/chi group remains unresolved independently.'),('οἱ','ᾧ / οἱ','The short relative or article and its accent remain unresolved independently.'),('ἐπὴ','ἐπῆν','The terminal verb and accent remain unresolved independently.')]
}
LEADING_FRAGMENTS={(170,5):'λεῖν',(170,6):'τὸς',(170,8):'ντὸν',(170,13):'σομεν',(170,16):'τας',(170,17):'σαν',(170,22):'τέρων',(170,25):'μιζομένη',(170,26):'βαίνει',(170,28):'τεῖ',(170,30):'μηλον',(170,41):'μηλος',(170,50):'τιστα'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,target in LINES.items():
        region=[.025,.105,.49,.34]if number<=14 else[.025,.30,.49,.54]if number<=27 else[.025,.485,.49,.73]if number<=40 else[.39,.105,.81,.34]if number<=44 else[.39,.30,.81,.54]if number<=47 else[.39,.485,.81,.73]
        item=(None,target,region,None,None)
        if number==42:item=(*item,'unclassified-small-type')
        chunks=[item]
        if number in(42,44,45,46,47,48,49,50):
            label={42:'5',44:'10',45:'15',46:'20',47:'25',48:'30',49:'35',50:'40'}[number]
            chunks.insert(0,(label,'',region,None,None,'marginal-reference',label))
        CHUNKS[(170,number)]=chunks
    return _records(rows,document,crop_png,sections)


def _row_sha(row):
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _reading(sections,page,begin,end):
    if begin is None:return []
    section=f'tlg4040-tlg001-local002-s{page+277}'; full=sections[section]
    starts=[m.start()for m in re.finditer(re.escape(begin),full)]
    if len(starts)!=1:raise ValueError(f'Ambiguous digital bound {page}: {begin!r}')
    a=starts[0];b=full.index(end,a)+len(end)
    return [{'kind':'digital','section':section,'start':a,'end':b,'text':full[a:b]}]


def _records(rows,document,crop_png,sections):
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
                if leading and not role and (a==0 or all(s.get('text_role')for s in segments)):
                    if not text.startswith(leading):raise ValueError('Changed printed leading fragment')
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source line or page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
                if text.endswith('-'):
                    m=re.search(r'[^\W\d_]+-$',text)
                    fragments.append({'start':m.start(),'end':m.end(),'text':m.group(),'side':'trailing','qualification':('The unchanged uncertain original ends in an OCR hyphenated fragment. Its source candidate remains unresolved; preserve this original display and exclude it rather than asserting a complete lexical form.' if reason else 'This retained passage ends within a visibly divided printed word; preserve the source fragment and exclude it from lexical counts.')})
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


def occurrence_observations(rows,document,crop_png,sections):
    """The pinned digital section is unrelated, so no paired projection exists."""
    return []
