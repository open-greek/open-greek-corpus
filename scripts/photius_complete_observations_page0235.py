"""Complete direct source review of retained passages on printed page 500."""
from copy import deepcopy
import hashlib
import json
import re

PAGE = 235
REVIEWED_AT = '2026-10-21T12:31:03Z'
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0235.'
REGIONS = {'left': [.225, .105, .59, .72], 'right': [.57, .105, .95, .72]}
TEXT = {
    1: ('πλήσιον, εὐσεβείας δὲ καὶ πολιτείας ἕνα θεσμόν, καὶ τὴν ἐλπίδα τοῦ μέλλοντος τὴν αὐτήν, '
        'πῶς οὐ πάσης ἀδελφότητος καὶ συγγενείας ἐσμὲν ἀλλήλων ἐγγύτεροι; καὶ ὅταν ἄνθρωπον '
        'ἴδῃς, σαυτὸν ὁρᾷς ἐν ἐκείνῳ. δεῖ οὖν καὶ τὰ {u0} θεωρηθέντα πάθη, λιμόν, δίψαν, '
        'γυμνότητα, τὴν ἄλλην ἔνδειαν καὶ τὰς νόσους καὶ τοὺς ἄλλους πειρασμοὺς ὡς οἰκεῖα '
        'πάθη καὶ συμφορὰς οἰκτείρειν. πολλοὺς ἔγνωμεν ἐπὶ μὲν τῶν λόγων ὁμολογήσαντας '
        'προκινδυνεύειν, ἐπὶ δὲ τῆς πείρας ψευσαμένους τὴν εὔνοιαν. “ὁ μὲν σωτὴρ ἡμῶν '
        'οὕτως ἠγάπησε τὸ ἴδιον ποίημα, οὐχ ὡς ἑαυτόν, ἀλλ’ ὑπὲρ ἑαυτόν· ἡμῖν δὲ τὸ '
        'ἔλαττον {u1}, ἀγαπᾶν τὸν πλησίον ὡς ἑαυτόν, τὴν ὑπερβολὴν ἀφελῶν, ἵνα μὴ '
        'βαρεῖαν ποιήσῃ καὶ δυσήνυτον τὴν ἐντολήν. ἵνα διὰ τῶν ἔργων σαφέστερον '
        'ἐπιδείξῃ τὸν τῆς ἀγάπης ὁ δεσπότης νόμον, πρᾶγμα γέμον μὲν ἐλέου συμβὰν δὲ '
        'πάντως κατὰ τὸν χρόνον ἐκεῖνον ὑπ’ ὄψιν ἄγει τῷ λόγῳ, ἐκπαιδεύων τὸν νομικὸν '
        'ὅτι πλησίον ἡμῶν ἐκεῖνός ἐστιν, ὃς ἂν τὴν ἐμπαθῆ ταύτην περικείμενος σάρκα '
        'χρῄζῃ βοηθείας καὶ οἰκτιρμῶν. τὸ δὲ πάθος· ὁδοιπόρος ἐξ Ἱερουσαλὴμ κατέβαινεν '
        'εἰς Ἱεριχώ, καὶ ληστῶν ἐπιδραμόντων ἀφηρέθη μὲν ἃ ἔφερεν, ἐγυμνώθη δὲ καὶ '
        'τῶν ἱματίων, καὶ τραύμασι τοῖς ἀπὸ τῶν ληστῶν θανάτῳ προσομιλῶν ἤπλωτο κατὰ '
        'τὴν λεωφόρον ψυχοῤῥαγῶν. πρᾶγμα λίαν οἰκτρὸν ὀφθαλμοῖς ἔχουσιν ἔλεον ἢ '
        'εἰδόσιν ἔλεον. ὁ κύριος τοῖς Ἑβραίοις διαλεγόμενος, καὶ διδάσκων ὡς ἄφρονας καὶ '
        'μάτην ἀναστρεφομένους ἐν ταύτῃ τῇ τοῦ κλαυθμῶνος κοιλάδι, οὕτω πώς φησιν '
        '„ὑμεῖς ἐκ τῶν κάτω ἐστέ, ἐγὼ ἐκ τῶν ἄνω εἰμί,“ ἐκ τῶν ὀνομάτων μόνον τοῦ '
        'ἄνω καὶ κάτω τὸ καλὸν καὶ τὸ χεῖρον ποιούμενος τὴν διάκρισιν. καὶ νῦν δὲ '
        'καταβαίνοντα εἰπὼν κατὰ τὴν αὐτὴν ἔννοιαν ἔφη. ἦν δ’ ἂν οὗτος ὁ Ἀδάμ, '
        'ἀποκυλιόμενος τῆς μακαρίας ἐκείνης καὶ ὑψηλῆς διαγωγῆς εἰς τὸν βάραθρον καὶ '
        'χαμαίζηλον βίον. τίς ὁ ἱερεύς; τίς ὁ Λευΐτης; εἴησαν δ’ ἂν κατὰ θεωρίαν '
        'Μωσῆς καὶ Ἰωάννης, ἄμφω τοῖς παραπετάσμασι τῆς παραβολῆς ἔνδον κρυπτόμενοι '
        'καὶ τὴν τῶν πολλῶν ὄψιν λανθάνοντες. οὗτοι γὰρ καταλαβόντες τὸν ἄνθρωπον '
        '(τουτέστι τὸ γένος ὅλον) γυμνὸν εὐσεβείας καὶ ἀρετῆς καὶ τοῖς ἐναντίοις '
        'τετραυματισμένον, ἐθεάσαντο μέν, οὐ μὴν ἐπήρκεσαν θεραπεῦσαι. ἀλλ’ ὁ Σαμαρείτης κα-'),
    2: 'ταλαβών, ἐν ὀνόματι καθυβρισμένῳ θησαυρὸν ἀγα-',
    3: 'θῶν φέρων, παρέχει τὴν ἴασιν· ὅς ἐστιν ἡμῶν ὁ σω-',
    4: 'τὴρ, τῇ δυσφήμῳ προσηγορίᾳ τοῦ Σαμαρείτου καλυ-',
    5: 'πτόμενος καὶ τὰς τῆς σωτηρίας τῷ κειμένῳ πηγὰς ἀνα-',
    6: 'βλύζων. Σαμαρείτην δὲ τὸν σωτῆρα ὁ λόγος ὀνομά-',
    7: 'ζει, αἰσχύνων κἀνταῦθα τὴν τῶν οὕτως αὐτὸν καλε-',
    8: 'σάντων παράνοιαν Ἰουδαίων, ὅτι τὸν ὑπὲρ τοὺς λευί-',
    9: 'τας καὶ ἱερέας σπλαγχνιζόμενον καὶ θεραπεύοντα τὸν',
    10: 'τετραυματισμένον Σαμαρείτην ἐξύβριζον. τί δὲ',
    11: 'τυγχάνει τὸ κτῆνος, ἐφ’ ὃ τὸν ψυχοῤῥαγοῦντα κατα-',
    12: 'θέμενος εἰς τὸ πανδοχεῖον ἤγαγεν ὁ σωτήρ; ἢ δῆλον',
    13: 'ὅτι ὄχημα τῷ θεοῦ λόγῳ καὶ (ὡς ἄν τις εἴποι) ὑπο-',
    14: 'ζύγιον τὸ ὁμόφυλον ἡμῶν, ὅπερ {u0}, τυγχάνει',
    15: 'σῶμα, ἐφ’ ὃ καὶ δι’ ὃ πάντας ἀνέχων καὶ διαβαστάζων',
    16: 'ἄγει πρὸς τὴν ἀπαλλαγὴν τῆς νόσου καὶ τὴν ἐκκλησίαν·',
    17: 'καὶ γὰρ τῶν τραυμάτων αὕτη ἐστὶν ἡ τελεία θεραπεία',
    18: 'καὶ ἀπαλλαγή.',
    19: 'Τοῦ αὐτοῦ εἰς τὸ „ἄνθρωποι δύο ἀνέβησαν εἰς τὸ',
    20: 'ἱερὸν {u0}.“',
    21: 'τὸν περὶ τῆς προσευχῆς λόγον ἐν δυσὶ παραβο-',
    22: 'λαῖς κατέκλεισε, τὸ μὲν εὐτόνως {u0} διὰ τοῦ',
    23: 'κριτοῦ καὶ τῆς χήρας διδάξας ἡμᾶς, τὸ δὲ μετ’ εὐλα-',
    24: 'βοῦς γνώμης διὰ τοῦ Φαρισαίου καὶ τοῦ τελώνου. ὅτι',
    25: 'ἄριστόν ἐστι τὸ συνεχῶς ἐννοεῖν ποιήματα μὲν ἡμᾶς καὶ',
    26: 'ζῶα ἐπίκηρα, δημιουργὸν δὲ τὸν θεὸν καὶ ἄριστον τῆς',
    27: 'ἡμετέρας ζωῆς οἰκονόμον. τοῦτο δὲ πρὸ πάντων ἡ',
    28: 'προσευχὴ κατορθοῖ. οὐκ ἂν γάρ τις προσεύξαιτο τὰ',
    29: 'συμφέροντα, μὴ πληροφορίαν πρότερον λαβὼν ὅτι',
    30: 'θεὸς ἐστιν ὁ τῆς ἱκετηρίας ἐπήκοος καὶ δυνατὸς παρα-',
    31: 'σχεῖν ἃ αἰτεῖται. εὐχὴ τῆς ζωῆς ἡμῶν βοήθεια,',
    32: 'ὁμιλία πρὸς θεόν, λήθη τῶν γηίνων, ἄνοδος πρὸς',
    33: 'οὐρανόν. καὶ τὸ ὄρθιον δὲ τῆς προσευχῆς, ἐκτε-',
    34: 'ταμένας προβαλλομένων τὰς χεῖρας, τὸ τοῦ σταυροῦ πά-',
    35: 'θος ἐν τῷ σχήματι ἐξεικονίζει. εἰ δ’ ὡς ἀληθῶς προσ-',
    36: 'εύχοιτο καὶ θεαρέστως ὁ προσευχόμενος, οὐκ ἐν τῷ',
    37: 'σχήματι μόνον τὸν σταυρὸν διατυποῖ, ἀλλὰ καὶ κατὰ',
    38: 'τὴν διάθεσιν. ὡς γὰρ ὁ τῷ σταυρῷ προσηλωθείς, οὕτω',
    39: 'νεκροποιεῖ πᾶσαν μὲν ἐπιθυμίαν σαρκὸς τῆς μνήμης',
    40: 'ἀποτιναξάμενος, παντὸς δὲ πλούτου καὶ δόξης καὶ γένους',
    41: 'προσπάθειαν. οὐδὲν δὲ οὕτω πρᾶγμα ἐπιθυμητὸν',
    42: 'αὐτῷ καὶ ἐπέραστον ὡς εὑρίσκειν καιρὸν ἢ σχολὴν ἐμ-',
    43: 'πεσεῖν τῇ γνώμῃ. ἀλλὰ πρὸς δύο ταῦτα συντέ-',
}
UNCERTAIN = {
    1: [('ἐκεῖνο', 'ἐκείνῳ?', 'ἐκεῖνα', 'The case ending of this short word is not sufficiently distinct to certify.'),
        ('ἐγκλείει', 'ἐγκελεύεται?', 'ἐγκελεῦεθ', 'The compact final type does not support an exact expansion with sufficient confidence.')],
    14: [('ἡμᾶφέτο', 'ἠμπί[σ?]χετο', 'ἐμπίχετο', 'The compact sigma-chi cluster and initial breathing are not distinct enough to certify.')],
    20: [('προσεύξασθαι', 'προσεύξα[σ?]θαι', 'προσεύξασθαι', 'The compact sigma-theta type cannot be distinguished confidently from the theta variant.')],
    22: [('προευχῆς', 'προσεύχε[σ?]θαι', 'προσεύχεσθι', 'The compact printed ending remains uncertain rather than being completed from grammatical expectation.')],
}
DSTART = {
    2:'ταλαβών', 3:'θῶν φέρων', 4:'τήρ, τῇ', 5:'πτόμενος κὶ', 6:'βλύζων.',
    7:'ζει, αἰσχύνων', 8:'σάντων παράνοιαν', 9:'τας καὶ ἱερέας', 10:'τετραυματισμένον σαμαρείτην',
    11:'τυγχάνει τὸ κτῆνος', 12:'θέμενος εἰς τὸ', 13:'ὅτι ὄχημα', 14:'ζύγιον τὸ',
    15:"σῶμα, ἐφ'", 16:'ἄγει πρὸς', 17:"καὶ γδ' τῶν", 18:'καὶ ἀπαλλαγή',
    19:'τοῦ αὐτοῦ εἰς', 20:'ἱερὸν προσεύξασθαι', 21:'τὸν περὶ τῆς προσευχῆς',
    22:'λαῖς κατέκλεισε', 23:'κριτὲ κὶ τῆς', 24:'βῆς γνώμης', 25:'ἄρισον ἐξι',
    26:'ζῶα ἐπίκηρα', 27:'ἡμετέρας ζωῆς', 28:'προσευχὴ κατορθοῖ', 29:'συμφέροντα',
    30:'θεὸς ἐξιν ὁ τῆς', 31:'χεῖν ἃ αἰτεῖται', 32:'ὁμιλία πρὸς θεόν', 33:'ἐρανόν.',
    34:'ταμένας προβαλλόμενον', 35:'θεν ἐν τῷ χήματι', 36:'εὔχοιτο καὶ θεαρέως',
    37:'χήματι μόνον', 38:'τὴν διάθεσιν', 39:'νεκροποιεῖ', 40:'ἀποτιναξάμενος',
    41:'προσπάθειαν.', 42:'αὐτῷ κὶ ἐπέρασον', 43:'πεσεῖν τῇ γνώμῃ',
}
FRAGMENTS = {
    1:[('πλήσιον','leading'),('κα-','trailing')], 2:[('ταλαβών','leading'),('ἀγα-','trailing')],
    3:[('θῶν','leading'),('σω-','trailing')], 4:[('τὴρ','leading'),('καλυ-','trailing')],
    5:[('πτόμενος','leading'),('ἀνα-','trailing')], 6:[('βλύζων','leading'),('ὀνομά-','trailing')],
    7:[('ζει','leading'),('καλε-','trailing')], 8:[('σάντων','leading'),('λευί-','trailing')],
    9:[('τας','leading')], 11:[('κατα-','trailing')], 12:[('θέμενος','leading')],
    13:[('ὑπο-','trailing')], 14:[('ζύγιον','leading')], 21:[('παραβο-','trailing')],
    22:[('λαῖς','leading')], 23:[('εὐλα-','trailing')], 24:[('βοῦς','leading')],
    30:[('παρα-','trailing')], 31:[('σχεῖν','leading')], 33:[('ἐκτε-','trailing')],
    34:[('ταμένας','leading'),('πά-','trailing')], 35:[('θος','leading'),('προσ-','trailing')],
    36:[('εύχοιτο','leading')], 42:[('ἐμ-','trailing')], 43:[('πεσεῖν','leading'),('συντέ-','trailing')],
}


def records(rows, document, crop_png, sections):
    """Reproduce only the forty-three explicitly inspected retained passages."""
    section = 'tlg4040-tlg001-local002-s512'
    digital = sections[section]
    starts = {1: 0}
    for number, needle in DSTART.items():
        starts[number] = digital.index(needle, starts[number - 1] + 1)
    result = []
    for number, observed in TEXT.items():
        row = rows[PREFIX + str(number)]
        text = row['text']
        low, high = starts[number], starts.get(number + 1, len(digital))
        region = REGIONS['left' if number == 1 else 'right']
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        base = {'review_basis': 'direct-scan-inspection', 'reviewed_at': REVIEWED_AT,
            'evidence': 'Every retained word and unchanged span was directly compared '
                'with Bekker physical page 235 / printed page 500. Both complete '
                'body columns and enlarged upper/lower strips were inspected. '
                'The pinned digital reading is separately retained, including '
                'its contrary forms and its omitted leading page fragment.',
            'transcription_convention': 'Expand identified ου, στ, καὶ and γὰρ '
                'type, preserve unresolved type as uncertainty, and retain '
                'historical quotation delimiters. Join internal line divisions '
                'within the long passage, preserve all passage-boundary fragments, '
                'and distinguish marginal references and line numbers from body text.'}
        def segment(start, end, corrected, **extra):
            return {**deepcopy(base), 'start': start, 'end': end,
                'original_text': text[start:end], 'corrected_text': corrected,
                'verification': 'verified', 'scan': {'physical_page': PAGE,
                    'region': region, 'image_sha256': image_sha, 'observed_text': corrected}, **extra}
        cursor, dcursor, tail, segments = 0, low, observed, []
        for index, (old, scan, dword, reason) in enumerate(UNCERTAIN.get(number, [])):
            positions = list(re.finditer(r'(?<!\w)' + re.escape(old) + r'(?!\w)', text))
            if len(positions) != 1:
                raise ValueError('A reviewed page 500 original uncertainty changed')
            start = positions[0].start()
            before, tail = tail.split('{u' + str(index) + '}')
            dstart = digital.index(dword, dcursor, high)
            if start > cursor:
                item = segment(cursor, start, before)
                item['readings'] = [{'kind': 'digital', 'section': section, 'start': dcursor,
                    'end': dstart, 'text': digital[dcursor:dstart]}]
                segments.append(item)
            item = segment(start, start + len(old), old, verification='uncertain', uncertainty=reason)
            item['scan']['observed_text'] = scan
            item['readings'] = [{'kind': 'digital', 'section': section,
                'start': dstart, 'end': dstart + len(dword), 'text': dword}]
            segments.append(item)
            cursor, dcursor = start + len(old), dstart + len(dword)
        item = segment(cursor, len(text), tail)
        item['readings'] = [{'kind': 'digital', 'section': section,
            'start': dcursor, 'end': high, 'text': digital[dcursor:high]}]
        segments.append(item)
        for word, side in FRAGMENTS.get(number, []):
            item = segments[0] if side == 'leading' else segments[-1]
            position = item['corrected_text'].index(word)
            item.setdefault('fragments', []).append({'start': position, 'end': position + len(word),
                'text': word, 'side': side, 'qualification': 'The printed word crosses '
                'a retained passage boundary. Preserve and exclude this visible '
                'fragment rather than inventing a complete lexical form.'})
        result.append({'locus': row['locus'], 'original_row_sha256': hashlib.sha256(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'status': 'reviewed-with-uncertainty' if number in UNCERTAIN else 'reviewed-verified',
            'segments': segments})
    return result
