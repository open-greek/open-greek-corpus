"""Complete direct source review of retained passages on Bekker printed300.

Only the retained source ranges are certified here, including the short final heading.
Subsequent separately witnessed body text is outside this module's row accounting.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:00:54.528542+00:00'
_CROPS = {'L':[.205,.10,.61,.755], 'R':[.55,.10,.95,.755]}
_SPECS = [(35,
  1,
  'dfdc9c84f67d61b5b6936d349752cc37594803d39e03bdcc83f7f8755f3db423',
  'εἰς τὸν ἄδην τὸν Χριστὸν, ἀναζάτες ἤδη τινὲς ἰσορρήθησαν πρὸ αὐτοῦ, ἐν οἷς τῆς Σαραβδίνης χῆρος ὁ 928R.νιὸς '
  'καὶ τῆς Σωμαίνιδος ἢ ὁ Λάχαρος·" "λεκτὸν δὲ ἵνα εἰς τὸ κ αὐθὶς ἀποθανεῖν ἀπέχρη, ἡμᾶς 471.H.περὶ "τῶν μικρῶν '
  'μετὰ τὴν ἡμέραν διοριζόμενα 5 διοριζομένων. εἰν δὲ κ περὶ τῆς ψυχῆς διαπορήσεις φράσῃ τῷ Ἡλίῳ, ὡς τῶν μὲν '
  'γραφῶν ἀνελήφθαι αὐτὸν λεγουσῶν ἐν σαρκί, ἡμῶν δὲ ἀσώματον σαρκὸς τοῖς ἀποστόλοις ὁφθαλμοῖς φασκόντων, λεκτὸν '
  "ὅτι κ μὴν μᾶλλον τὸ λέγειν αὐτὸν ὁφθαλμοῖς ἀποστόλοις ἐν σαρκί 10 πρὸς ἡμῶν ἐστὶ. δείκνυσθ' γὰρ καὶ διὰ τῶν "
  'ἀφορισμῶν ἡμῶν ὑπάρχειν τὸ σῶμα δεκτικόν, καθάπερ εἰδείρηται καὶ ἐπὶ τῷ Ἐνώχ μετατιθεμένῳ. εἰ μὴ γὰρ ἀφορισμὸν '
  'ἠδύνατο δέξασθαι, ὅκ ἂν οὐδὲ διέμενεν ἐν ἀκαθαρσίᾳ τοσούτῳ χρόνῳ. εἰ τοίνυν ὀφθῇ μετὰ τὸ σῶματος, καὶ 15 ἤν '
  "τελευτήσας μὲν, ἀναζὰς δὲ ἤδη ἐν νεκρῶν ὁδῷ. καὶ ταῦτα ἵνα δὴ συγχωρήσωμεν τῷ Ῥωγίνῃ, καθ' αὐτὸ τὸ εἶδος "
  'λέγοντι μετὰ τὴν τελευτὴν ἀπολελυμένον ἀπὸ τοῦ σώματος τῇ ψυχῇ διδοῦθαι, ὅπερ ἐστὶν ἀπάντων ἀδύνατον τῷ '
  'προσπαλίνθῃ τὸ εἶδος τῶν σαρκικῶν ἐν ταῖς ἀλλοιώσεσι, καθάπερ καὶ τὸ χῆμα τοῦ συγχωνευομένου ἀνδριάντος πρὸ '
  "τῆς διαλύσεως τῷ ὄλῃ, 20 ὅτι μὴ δύναται χωρισθῆναι καθ' ὑπόστασιν ἀπὸ τῆς ὕλης ἢ ποιότης. χωρισθῶ μὲν γὰρ ἀπὸ "
  "τοῦ ἀνδριάντος χωνευθέντος ἢ περὶ τῷ χαλκῷ ἀφανισομένη, κ μὴν ἀντερεῖσαι ἐτι κατ' ὕλην. ἐπεὶ δὲ λέγεται τῷ "
  'θαυμάτῳ τὸ εἶδος χωρισθῆναι ἀπὸ τῆς σαρκός, φέρε τὸ χωρισθὲν ποσάκις λέγεται χωρισθῆναι ἐπισκεψώμεθα. λέγω '
  'τοίνυν χωρισθῆναι τοῦ ἀπὸ τινος ἢ ἐνέργεια καὶ ὑπόστασις, ἢ ἐπινοία, ἢ ἐνέργεια μὲν, ὅ μὴν καὶ ὑπόστασις. 25 '
  "ὡς εἰ πυρός τις καὶ κρύους μεμιγμένα χωρίσωμεν ἀπ' ἀλλήλων· ἢ μὲν γὰρ κατὰ κίνησιν χωρίζεται, ἐνέργεια λέγω, ἢ "
  'δὲ χωριζόμενα ὁρέσκειν, ὑπόστασις λέγω καὶ χωρίζεται. ἐπινοία δέ, ὅταν τὴν ὕλην ἀπὸ τῶν ποιοτήτων χωρίσωμεν '
  'καὶ τὰς ποιότητας ἀπὸ τῆς ὕλης. ἐνέργεια δέ, ὅ μὴν καὶ ὑπόστασις, ὅταν χωρισθῇ τι ἀπὸ τινος μηκέτι ὑπάρχῃ, '
  "ὑπόστασιν ὁσίαν ὅκ ἔχον. γνώῃ δ' ἂν τις καὶ ἐν τοῖς χειροτεχνήμασιν ὡς ἔχει, ἀνδριάντα ἰδὼν ἢ ἵππον χαλκόν. "
  'ταῦτα γὰρ λογιζόμενος δυνήσεται τὴν ἐφικτὸν μορφὴν διαλλάττοντα, εἰς δὲ ἑτέραν ὁρῶν μετασχεμένα τῇ ἑς τὸ '
  'ἐγγυτέρω εἶδος ἀφανισθῆναι. εἰ γὰρ τις τὰ ἔργα τὰ σχηματιζόμενα εἰς εἶδος ἀνθρώπου',
  'εἰς τὸν ᾅδην τὸν Χριστὸν, ἀναστάντες ἤδη τινὲς ἱστορήθησαν πρὸ αὐτοῦ, ἐν οἷς τῆς Σαραφθίτης χήρας ὁ υἱὸς καὶ '
  'τῆς Σωμαίνιδος καὶ ὁ Λάζαρος;“ λεκτὸν, ἀλλ’ ὅσον εἰς τὸ καὶ αὖθις ἀποθανεῖν ἀνέστησαν, ἡμεῖς δὲ περὶ τῶν '
  'νεκρῶν μετὰ τὴν ἡμέραν διοριζόμεθα τεθνηξομένων. ἐὰν δὲ καὶ περὶ τῆς ψυχῆς διαπορήσας φράσῃ τοῦ Ἡλίου, ὡς τῶν '
  'μὲν γραφῶν ἀνειλῆφθαι αὐτὸν λεγουσῶν ἐν σαρκί, ἡμῶν δὲ ἀσώματον σαρκὸς τοῖς ἀποστόλοις ὦφθαι φασκόντων, λεκτὸν '
  'ὅτι καὶ μὴν μᾶλλον τὸ λέγειν αὐτὸν ὦφθαι τοῖς ἀποστόλοις ἐν σαρκὶ πρὸς ἡμῶν ἐστί. δείκνυται γὰρ καὶ διὰ τοῦτο '
  'ἀφθαρσίας ἡμῶν ὑπάρχον τὸ σῶμα δεκτικὸν, καθάπερ ἐλέχθη καὶ ἐπὶ τοῦ Ἐνὼχ μετατιθεμένου. εἰ μὴ γὰρ ἀφθαρσίαν '
  'ἐδύνατο δέξασθαι, οὐκ ἂν οὐδὲ διέμενεν ἐν ἀπαθείᾳ τοσούτῳ χρόνῳ. εἰ τοίνυν ὤφθη μετὰ τοῦ σώματος, καὶ ἦν '
  'τελευτήσας μὲν, ἀναστὰς δὲ ἤδη ἐκ νεκρῶν ἐδόκει. καὶ ταῦτα ἵνα δὴ συγχωρήσωμεν τῷ Ὠριγένει, καθ’ ἑαυτὸ τὸ '
  'εἶδος λέγοντι μετὰ τὴν τελευτὴν ἀποζευγνύμενον ἀπὸ τοῦ σώματος τῇ ψυχῇ δίδοσθαι, ὅπερ ἐστὶν ἁπάντων ἀδύνατον '
  'τῷ προαπόλλυσθαι τὸ εἶδος τῶν σαρκῶν ἐν ταῖς ἀλλοιώσεσι, καθάπερ καὶ τὸ χῆμα τοῦ συγχωνευομένου ἀνδριάντος πρὸ '
  'τῆς διαλύσεως τῇ ὕλῃ, ὅτι μὴ δύναται χωρίζεσθαι καθ’ ὑπόστασιν ἀπὸ τῆς ὕλης ἡ ποιότης. χωρίζεται μὲν γὰρ ἀπὸ '
  "τοῦ ἀνδριάντος χωνευθέντος ἡ περὶ τῷ χαλκῷ μορφὴ ἀφανιζομένη, κ μὴν ἀντερεῖσαι ἐτι κατ' ὕλην. ἐπεὶ δὲ λέγεται "
  'ἐν τῷ θανάτῳ τὸ εἶδος χωρίζεσθαι ἀπὸ τῆς σαρκὸς, φέρε τὸ χωριζόμενον ποσαχῶς λέγεται χωρίζεσθαι ἐπισκεψώμεθα. '
  'λέγεται τοίνυν χωρίζεσθαί τι ἀπό τινος ἢ ἐνεργείᾳ καὶ ὑποστάσει, ἢ ἐπινοίᾳ, ἢ ἐνεργείᾳ μὲν, οὐ μὴν καὶ '
  'ὑποστάσει. ὡς εἰ πυρός τις καὶ κριθῆς μεμιγμένα χωρίσειεν ἀπ’ ἀλλήλων· ἡ μὲν γὰρ κατὰ κίνησιν χωρίζεται, '
  'ἐνεργείᾳ λέγεται, ἡ δὲ χωρισθέντα ὑφέστηκεν, ὑποστάσει λέγεται κεχωρίσθαι. ἐπινοίᾳ δὲ, ὅταν τὴν ὕλην ἀπὸ τῶν '
  'ποιοτήτων χωρίζωμεν καὶ τὰς ποιότητας ἀπὸ τῆς ὕλης. ἐνεργείᾳ δὲ, οὐ μὴν καὶ ὑποστάσει, ὅταν χωρισθέν τι ἀπό '
  'τινος μηκέτι ὑπάρχῃ, ὑπόστασιν ἰδίας οὐκ ἔχον. γνοίη δ’ ἄν τις καὶ ἐν τοῖς χειροτεχνήμασιν ὡς ἔχει, ἀνδριάντα '
  'ἰδὼν ἢ ἵππον χαλκοῦν. ταῦτα γὰρ λογιζόμενος δύναται τὴν ἐφικτὸν μορφὴν διαλλάττοντα, εἰς δὲ ἑτέραν ὄψιν '
  'μετασχεμένα τῇ ἑς τὸ ἐγγυτέρω εἶδος ἀφανίζεσθαι. εἰ γάρ τις τὰ ἔργα τὰ σχηματιζόμενα εἰς εἶδος ἀνθρώπου',
  'L',
  [],
  [('ἐν οἷς',
    'ἐν αἷς',
    'The small relative-pronoun vowel is unclear; possible ἐν αἷς or ἐν οἷς remain explicit with exact original '
    'display.'),
   ('τῆς Σωμαίνιδος',
    'τῆς Σωμανίτιδος',
    'The compact proper-name middle types are unclear; possible Σωμανίτιδος or Σωμαίνιδος are retained. No '
    'identification with a familiar biblical name supplies the spelling.'),
   ('ἀσώματον',
    'ἀνάπλεων',
    'The compact adjective is unresolved; possible ἀνάπλεων or ἄμοιρον and exact original ἀσώματον are retained. '
    'The argument does not determine the printed word.'),
   ('τὸ χῆμα',
    'τὸ σχῆμα',
    'The compact initial σχ/χ type is unresolved; possible τὸ σχῆμα or τὸ χῆμα and original remain explicit.'),
   ("κ μὴν ἀντερεῖσαι ἐτι κατ' ὕλην",
    'οὐ μὴν ὑφεστῶσα ἔτι κατ’ ὀψίαν',
    'The compact bounded clause is unresolved; this tentative reading and the exact original are retained.'),
   ('τὴν ἐφικτὸν μορφὴν',
    'τὴν ἔμφυτον μορφὴν',
    'The small adjective types are unclear; possible ἔμφυτον or ἔμψυτον and the exact original are retained.'),
   ('μετασχεμένα τῇ ἑς τὸ ἐγγυτέρω',
    'μεταθέμενα τὴν εἰς τὸ ἐγγινόμενον',
    'The compact participial phrase is unresolved; this tentative reading and the exact original are retained '
    'without reconstructing the illustration.')]),
 (35,
  2,
  'ee7b1c3c559d2df6bd5d2f1e88758800dceccf78d831879a79df168ebab6aca1',
  'ἡ ἵππῳ συντέχῳ, εἰρήσθω τὸ μὲν τοῦ χήματος εἶδος ἀφανιζόμενον, αὐτὴν δὲ τὴν ἕλην μένειν. ὥς ἀσύφατον τὸ λέγειν '
  'τὸ μὲν εἶδος ἀνέλαθῆ ἡμῶν μενόν, μηδὲν, τὸ δὲ σῶμα, ἐν ᾧ τὸ εἶδος ἐντετυπωμένον, ἡ διαφθείρεται. ἀλλὰ καὶ '
  'ψυχὴν, ἐν πνευματικῷ γὰρ μετατεθήσεται σώματι. ἀκοῦν ἀνάγκη τὸ μὲν εἶδος ἰδίως ὁμολογῆν αὐτὸ τὸ πρῶτον μὴ '
  'ἀνέλαθαι, τῷ συνελλοῦσθῃ αὐτὸ συμφθῖνον τῇ σαρκί. κἂν γὰρ ἐν πνευματικῷ μεταπλασθῇ σώματι, αὐτὸ μὲν ἰδίως τὸ '
  'πρῶο τὸν ὑποκείμενον ἐκεῖνο ἔχει, ὁμοίως δὲ τις ἐκεῖνο ἐν λεπτομερίᾳ μεταπλασμένῳ σώματι. εἰ δὲ μήτε τὸ εἶδος '
  'τὸ αὐτὸ μήτε τὸ σῶμα ἀνέμεται, ἀλλ’ ἕτερον ἀντὶ τῷ προτέρου (τὸ γὰρ ὁμοῖον ἕτερον τοῦ “ἰσοτύθη δμοίου ὄν”), '
  'αὐτὸ ἐκεῖνο τὸ πρῶτον, πρὸς δ’ ἐγένετο, ὅ ἄνθρω ὅ δένεται.',
  'ἢ ἵππου συντήκοι, αἱρήσει τὸ μὲν τοῦ χήματος εἶδος ἀφανιζόμενον, αὐτὴν δὲ τὴν ὕλην μένουσαν. ὥστ’ ἀσύστατον τὸ '
  'λέγειν τὸ μὲν εἶδος ἀνίστασθαι ἡμῶν μενόν, μηδὲν, τὸ δὲ σῶμα, ἐν ᾧ ἦν τὸ εἶδος ἐντετυπωμένον, ἡ διαφθείρεται. '
  'ἀλλὰ καὶ φήσουσιν, ἐν πνευματικῷ γὰρ μετατίθεται σώματι. οὐκοῦν ἀνάγκη τὸ μὲν εἶδος ἰδίως ὁμολογεῖν αὐτὸ τὸ '
  'πρῶτον μὴ ἀνίστασθαι, τῷ συνελλοῦσθῃ αὐτὸ συμφθῖνον τῇ σαρκί. κἂν γὰρ ἐν πνευματικῷ μεταπλασθῇ σώματι, αὐτὸ '
  'μὲν ἰδίως τὸ πρῶτον ὑποκείμενον ἐκεῖνο οὐκ ἔχει, ὁμοιότης δέ τις ἐκείνου ἐν λεπτομερεῖ μεταπεπλασμένῳ σώματι. '
  'εἰ δὲ μήτε τὸ εἶδος τὸ αὐτὸ μήτε τὸ σῶμα ἀνίσταται, ἀλλ’ ἕτερον ἀντὶ τοῦ προτέρου (τὸ γὰρ ὅμοιον ἕτερον τοῦ '
  'καθ’ ὃ ὅμοιον ὂν), αὐτὸ ἐκεῖνο τὸ πρῶτον, πρὸς ὃ ἐγένετο, ὅλως οὐ δύναται.',
  'R',
  [],
  [('τοῦ χήματος',
    'τοῦ σχήματος',
    'The compact initial σχ/χ group remains uncertain; possible τοῦ σχήματος or τοῦ χήματος and exact original '
    'are retained.'),
   ('ἡμῶν μενόν, μηδὲν',
    'ἡμαρτημένον μηδὲν',
    'The compact participial and negative phrase is unresolved; possible ἡμαρτημένον μηδὲν and the exact original '
    'are retained.'),
   ('ἡ διαφθείρεται',
    'διαφθείρεσθαι',
    'The compact ending σθ/θ remains uncertain; possible διαφθείρεσθαι or διαφθείρεθαι and exact original remain '
    'explicit.'),
   ('τῷ συνελλοῦσθῃ',
    'τῷ συνελλῦσθαι',
    'The compact verb ending is unresolved; possible συνελλῦσθαι or συνελλύσθαι and exact original remain '
    'explicit.')]),
 (35,
  3,
  'e8cbe3a125f9d08fd4e66c01e899aea8049973df84d263f2f07858183ab87587',
  'ὅτι εἶδός φησιν εἶναι τὸ τὴν ταυτότητα τῶν μελῶν ἐν τῷ χαρακτῆρι τῆς μορφῆς ἐκείνου ἐμφαίνον.',
  'ὅτι εἶδός φησιν εἶναι τὸ τὴν ταυτότητα τῶν μελῶν ἐν τῷ χαρακτῆρι τῆς μορφῆς ἑκάστου ἐμφαῖνον.',
  'R',
  [],
  []),
 (35,
  4,
  'ddb72e77e6fb3b823a8e9337a7ffe75bfd31933d36f259f5754f12933cf45ada',
  '“ὅτι τὸ παρὰ τῷ προφήτῃ Ἰερεμίᾳ περὶ τῆς ἀνα- 929 B   ',
  'ὅτι τὸ παρὰ τῷ προφήτῃ Ἰεζεκιὴλ περὶ τῆς ἀνα-',
  'R',
  [{'start': 41,
    'end': 45,
    'text': 'ἀνα-',
    'side': 'trailing',
    'qualification': 'Incomplete printed word continuing beyond this retained source row; exclude it as an '
                     'independent lexical token. No completion is supplied.'}],
  [])]

def records(rows, document, crop_png, sections):
    output, cache = [], {}
    for page, number, expected, original, reviewed, crop, fragments, unknown in _SPECS:
        locus = f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{number}'
        if row_sha(rows[locus]) != expected or rows[locus]['text'] != original:
            raise ValueError(f'Complete source review preimage changed: {locus}')
        if crop not in cache:
            cache[crop] = hashlib.sha256(crop_png(document,page,_CROPS[crop])).hexdigest()
        segments, offset = [], 0
        for start, end, old, corrected, uncertainty in _segments(original,reviewed,unknown):
            observed = uncertainty[0] if uncertainty else corrected
            digital, alignment = _digital_observations(observed,page,sections)
            segment = {'start':start,'end':end,'original_text':old,'corrected_text':corrected,
                'verification':'uncertain'if uncertainty else'verified',
                'review_basis':'direct-scan-inspection','reviewed_at':REVIEWED_AT,
                'evidence':'Direct visual inspection of every character in the recorded printed body range in the pinned Bekker1825 volume2 scan, with paragraph and physical-line boundaries checked against the page.',
                'scan':{'physical_page':page,'region':_CROPS[crop],'image_sha256':cache[crop],
                    'observed_text':observed,'max_side':3600},
                'readings':digital,'digital_alignment':alignment,'fragments':[],
                'transcription_convention':_CONVENTION+' Expand the conventional printed σθ ligature to ordinary Greek Unicode.'}
            if not alignment['tokens']:
                segment.pop('digital_alignment')
            if uncertainty:
                segment['uncertainty'] = uncertainty[1]
            for f in fragments:
                if offset <= f['start'] and f['end'] <= offset+len(corrected):
                    segment['fragments'].append({**deepcopy(f),'start':f['start']-offset,'end':f['end']-offset})
            offset += len(corrected)
            segments.append(segment)
        if offset != len(reviewed):
            raise ValueError(f'Complete source span accounting changed: {locus}')
        output.append({'locus':locus,'original_row_sha256':expected,
            'status':'reviewed-with-uncertainty'if unknown else'reviewed-verified','segments':segments})
    return output
