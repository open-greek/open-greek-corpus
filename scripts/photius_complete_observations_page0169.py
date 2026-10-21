"""Complete direct scan observations for retained historical physical page169.

The pinned digital section is mismapped and is deliberately not used here.
Every retained word was inspected in overlapping source crops; unresolved glyphs
retain their exact original display with an explicit candidate source reading.
"""
from copy import deepcopy
import hashlib
import json
import re
REVIEWED_AT='2026-10-21T13:20:14.538899Z'
CHUNKS={
 (169,1):[
 ('ἐπεπράγεσαν.','ἐμμένειν, οὐκ ἄμεμπτος μόνον ἀλλὰ καὶ πολλῷ τινὶ πρῶτος ἦν. ἐπεὶ δ’ ἅμα τῆς τε χώρας ἠναγκάζετο {u0}, καὶ ὁ λοιμὸς ἅπαντα φθείρων ἐπέκειτο, καὶ κακῶν ἀνάπαυσις οὐκ ἦν, ἕως δὴ τῶν συμφορῶν {u1} πρὸς αὐτόν. “καί μοι τοῦ παραδείγματος ἐνταῦθ’ {u2} τοῦ τῶν ἡνιόχων· τάχα ἂν γὰρ ἁλοίης τοῖς ἅρμασι τοῖς σαυτοῦ, καὶ οὐ τοῖς πτεροῖς. ἀλλ’ οὐκ ἔχων (οὐχ ὁ Νέστωρ) ὅτῳ χρήσαιτο, μὴ ὅτι ἐκείνῳ τῷ τὴν πληγὴν λαβόντι, ἀλλ’ οὐδὲ τοῖς ἄλλοις ἵπποις τεταραγμένοις ὑπὸ τοῦ πάθους· ἀλλ’ οὐκ ἀπολῦσαι τὸν ῥυτῆρα ἂν τῷ θορύβῳ ῥᾳδίως ἐδύνατο, ἀλλ’ ὥσπερ ἐπὶ χαλκοῦ ζυγοῦ εἱστήκει μένων, ὅσα μὴ αὐτῷ τό γε ἀτρεμεῖν. οἴκοι πονηρῶς ἐπεπράγεσαν.',[.20,.105,.60,.38],None,None),
 ('(ἀντὶ τοῦ ἀτυχῶς.)','(ἀντὶ τοῦ ἀτυχῶς.)',[.20,.265,.60,.54],None,None,'unclassified-small-type'),
 (None,' ἀπεσείσαντο μὲν τὸν ἡνίοχον, ἀποσεισάμενοι δὲ οὕτως εὖ καὶ καλῶς “{u3} ὑπ’ αὐτῷ τὸν ἄνω χρόνον, ὥστε ἐγνωκότες τε εὖ ἔδρασαν, καὶ μετέγνωσαν, καὶ ὑποκύψαντες ἐξ ἀρχῆς παρέδοσαν ἄρχειν καὶ ἄγειν ὅποι βούλοιτο ἑαυτός. ἀλλὰ μὴν ὅτε καὶ τὸν ἔμπροσθεν χρόνον εὐδοκίμει πολλὰ ἑξῆς ἔτη, καὶ μετὰ τὴν καταδίκην μέγιστος πάλιν ἦν τῶν πολιτῶν, πῶς οὐκ ἀμφοτέρων ἕνεκα ζηλωτός ἐστι, καὶ τῆς ἀρχῆς καὶ τοῦ τέλους; οὐ γὰρ τὸ προσκροῦσαι τοῖς ἔμπροσθεν {u4}, ἀλλὰ τὸ {u5} μετὰ τοῦτο πᾶσαν παρεγράψατο τὴν συμφοράν. {u6} ἑκατέρων τῶν καιρῶν, ἀλλὰ κρατεῖ τὸ συναμφότερον τοῦ μέσου. εἴτε γὰρ τοῖς πρώτοις δεῖ διδόναι τὴν ψῆφον, ἐτιμᾶτο ἀπ’ ἀρχῆς· εἴτε τοῖς ὕστερον, οὐκ ἐν οἷς κατέγνωσαν {u7}, ἀλλὰ προσεῖχον πάλιν ὡς αὑτῶν βελτίονι. καὶ μὴν οὐχ ὅσον δύο ἀνθ’ ἑνός ἐστιν, ἀλλ’ ὅτι καὶ τὸ πλῆθος ἑκάστου χρόνου οὐκ ἴσον οὐδ’ ἐγγύς. οὐ μὴν ἀλλὰ τοὺς λαχόντας ἅπαντας {u8} καταγνῶναι τὴν γραφὴν αὐτοῦ, ἀλλ’ εἶναί τινας οἳ καὶ τῷ Περικλεῖ καλῶς ποιοῦντες εἴδοντο. οὔκουν τούτους γε βελτίους τε καὶ βελτίστους ἦν πεποιηκώς. καίτοι τί φήσομεν, ὦ τῶν Ἑλλήνων ἄριστε, πότερον δικαίως εἰς σὲ τοὺς ἐκείνους ταῦτα τολμᾶν, ἢ σὲ τῆς ἐκείνων μανίας ὑπεύθυνον εἶναι; ἐγὼ μὲν γὰρ {u9} ἂν φαίην. καὶ μὴν ἔχοι γ’ ἄν τις τοὺς σοὺς λόγους ἀμυνούμενος διπλῶς στρέφειν κατὰ σοῦ καὶ κατὰ Σωκράτους, ὡς εἰ καὶ τὰ μάλιστα',[.20,.265,.60,.73],None,None)],
 (169,3):[(None,'ἀδίκως ὑμῖν ταῦτα συνέβαινε, τρόπον γέ τινα τὰ προσήκοντα ἐπάσχετε, εἴ περ γε τοιούτους ἀπεδείκνυτε οὓς ἐπαιδεύετε. οὔκουν εἰ μὲν τὰ τῶν ὁμιλητῶν ἁμαρτήματα τῶν προεστηκότων ἐστὶ κατηγορήματα, σαφῶς καὶ τῷ ἑτέρῳ μᾶλλον κατηγόρηκας ἢ Περικλέους τε καὶ ὧν οἴει. καὶ νὴ Δί’, εἰ βούλει, τὸ μᾶλλον ἀφίημί σοι· ὅτι δὲ οὐχ ἧττον, ἀρκεῖ. εἰ δ’ ὑμεῖς ἀθῷοι, κἀκείνους ἐκ τῶν αὐτῶν εἰκὸς ἔξω εἶναι, εἴ πέρ γε τὰ ἴσα μέμνησαι καὶ μὴ ὑπερβαίνεις τὴν γεωμετρίαν ἑκών. εἶθ’ ὃν αὐτὸς ἀφῆκας ἂν τῆς αἰτίας, τοῦτον διαβάλλεις ἐκ τῆς αὐτῆς ταύτης αἰτίας. καὶ πῶς οὐκ ἄτοπον ἄλλῳ μὲν ἂν λέγοντι μὴ πιστεύειν, αὐτὸν δὲ κατηγορεῖν; καὶ δι’ ἃ τὸν λέγοντα ἡγῇ χείρω, διὰ ταῦτα Περικλέα ἀξιοῦν φαῦλον {u0}; καὶ τοὺς καταψηφισαμένους αἰτιώμενον ἡμᾶς πείθειν συγκαταγιγνώσκειν, ὥσπερ χρηστοῖς τισὶ πράγμασι μεθέξειν μέλλοντας, {u1} ἐκείνοις καλῶς εἶχε ποιῆσαι; κἀκεῖνοι μὲν αὐτοὶ τὴν ἑαυτῶν καταδίκην οὐχ ὑπελογίσαντο, ἀλλ’ ἐτίμων πάλιν ὡς χρηστὸν καὶ δίκαιον· ἡμεῖς δὲ οὐ μηδὲν ἄλλο κατηγορεῖν ἔχομεν, τοῦτον ἀτιμάσομεν διὰ τὴν δίκην; καὶ τῶν αὐτῶν ἀνδρῶν ὃ μὲν ἥμαρτον, ἰσχυρὸν ποιησόμεθα, ὃ δὲ εὖ φρονοῦντες ἔπραττον, ἐν οὐδενὸς μοίρᾳ θήσομεν, καὶ ταῦτα ὁμολογοῦντες ὡς ἥμαρτον, “μᾶλλον δὲ κατηγοροῦντες; καὶ τίνα ταῦτ’ ἂν εἶχε λόγον; ἐγὼ μὲν οὐκ ἐπινοῶ. Πλάτων δὲ τὴν συμφορὰν ὡς ἀδίκημα κατηγόρηκε, τὴν μὲν τύχην ἀντὶ γνώμης ἐξετάζων, τὴν δ’ ἑτέρων ἁμαρτίαν ὡς ἐκείνου οὖσαν τιθείς. εἰ δὲ τοὺς καταψηφισαμένους καὶ τοῖς ἵπποις ἀπεικάζων τοῖς λακτίζουσιν ἰσχυρόν τι λέγειν καθ’ ὧν ἡ ψῆφος οἴει, ταχύ γ’ ἂν εἰ τοῖς δώδεκα θεοῖς ἔχοι εἰκάσαι τοὺς καταγνόντας, ἀνάσχοιτ’ ἂν τῶν ἁλόντων τὸ μὴ οὐ κακῶς εἰπεῖν. εἰ δ’ ἐπ’ ἀμφότερα Πλάτων {u2} τοὺς ἄνδρας, ὥσπερ σοφῆς τινὸς εἰλημμένος, τί κωλύει τινὰ τὰς ὁμοίας ἀνταποδιδόντα ἐπ’ ἀμφότερα αὖ φιλονείκως ὑπολαμβάνοντα, διαιρεῖν ὡδὶ τὸν λόγον, ὅτι εἰ καλῶς καὶ τὰ δίκαια αὐτῶν Ἀθηναῖοι κατέγνωσαν, οὐκ ἦσαν ἐπ’ αὐτῶν διεφθαρμένοι· τὰ γὰρ δίκαια ἐποιοῦν. οὔκουν οὐδ’ ἐκεῖνοι διεφθάρκεσαν. ὥστε εἰ δικαίως ἑάλωσαν, οὐδὲν ταύτῃ γε χείρους ἦσαν.',[.56,.105,.97,.73],None,None)]
}
UNCERTAINTIES={
 (169,1):[('σέ-ρει·ῆς','στερεῖσθαι','The compact sigma/theta group and preceding letters remain unresolved independently.'),('“συμφερόν ἦσται·','ἡττηθέντες ἐτραχύνθησαν','The original conflates the source lines; the compact participial and verbal endings remain unresolved independently.'),('ἀναμνήσθητι','ἀναμνήσθητι','The unchanged compact sigma/theta group remains unresolved independently.'),('ἤχθησαν','ἤχθησαν','The compact consonant group remains unresolved independently.'),('ἐπεκώ-τησαν','ἐπεσκώτησαν','The compact medial consonant group remains unresolved independently.'),('τιμᾶσθαι','τιμᾶσθαι','The unchanged compact sigma/theta group remains unresolved independently.'),('ἢ γὰρ τὸ μέσον κειμέν ᾗσιν','οὐ γὰρ τὸ μέσον κεῖνό ἐστιν','The compact connective and following short phrase remain unresolved independently.'),('ἔσχον','ἔσχον','The unchanged compact sigma/chi group remains unresolved independently.'),('οἷδ’ ἡ χρή','οἴει χρῆν','The compact verbal phrase remains unresolved independently.'),('ἀνέκτον','ἀδεκτότερον','The compact medial letters remain unresolved independently.')],
 (169,3):[('νομίζειν','νομίζεσθαι','The compact final sigma/theta group remains unresolved independently.'),('ἀλλ’ οὐχ ἃ μετ’','ἀλλ’ οὐχ ἃ μετ’ / ἀλλ’ ὑφ’ οἷς μεθ’','The compact connective phrase remains unresolved independently.'),('αἰτιάσετ)','αἰτιάσεσθαι','The compact final sigma/theta group remains unresolved independently.')]
}
LEADING_FRAGMENTS={}


def records(rows,document,crop_png,sections):
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
