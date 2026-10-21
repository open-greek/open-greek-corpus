"""Direct complete-passage readings on Bekker printed page498.

The retained passages were compared in both body columns and enlarged source
strips. Six compact readings remain uncertain. The fresh consensus passage3
is outside this retained historical review and receives no replacement reading.
"""
from copy import deepcopy
import hashlib
import json

PAGE = 233
REVIEWED_AT = '2026-10-21T12:11:46Z'
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0233.'
LOCI = (1, 2, *range(4, 43))
REGIONS = {'left': [.225, .105, .59, .72], 'right': [.57, .105, .95, .72]}

# These are authored scan observations, not a copy of a selected digital page.
# In particular, the digital archive misreads ου and στ ligatures repeatedly.
TEXT = {
    1: 'Ἀνεγνώ{uncertain}ησαν ἩΣΥΧΙΟΥ πρεσβυτέρου Ἱεροσολύμων ἐκ τοῦ εἰς τὸν ἅγιον Ἀνδρέαν ἐγκωμίου.',
    2: ('“σάλπιγξ ἡμᾶς ἱερατικὴ πρὸς πανήγυριν ἤθροισεν Ἀνδρέας ὁ τοῦ χοροῦ τῶν ἀποστόλων '
        'πρωτότοκος, ὁ πρωτοπαγὴς τῆς ἐκκλησίας στῦλος, ὁ πρὸ Πέτρου Πέτρος, ὁ τοῦ θεμελίου '
        'θεμέλιος, ἡ τῆς ἀρχῆς ἀρχή, ὁ πρὶν κληθῆναι καλῶν, ὁ πρὶν προσαχθῆναι προσάγων. '
        'εὐαγγέλιον κηρύττει ὁ μὴ πω πεπίστευται· πρὶν μαθεῖν τῷ ἀδελφῷ ἀποκαλύπτει τὴν ζωήν· '
        'τοσοῦτον αὐτῷ πλοῦτον ἡ τοῦ „ποῦ μένεις“ ἐρώτησις ἐχαρίσατο. καίτοι τί μέγα εἶχεν '
        'ἡ ἀπόκρισις, οἷον Ἀνδρέας ἐμβυθύνων τὸν νοῦν ἐθεώρησεν; „ἔρχου“ γάρ φησι „καὶ ἴδε.“ '
        'πῶς γέγονας προφήτης; πόθεν θεοφόρος ἀθρόον; τί θορυβεῖς τοῦ Πέτρου τὰς ἀκοάς; '
        'τί φθάσαι σπεύδεις, ὃν οὐ δύνῃ φθάσαι; ὁ πανταχοῦ παρὼν πῶς εὑρεθῆναι δύναται; '
        'ἀλλὰ γὰρ οἶδεν ὁ Ἀνδρέας ὃ λέγει. εὑρήκαμεν ὃν ἀπώλεσεν ὁ Ἀδάμ, ὃν ἐζημιώθη ἡ Εὔα, '
        'ὃν ἡ νεφέλη τῆς ἁμαρτίας ἀπὸ τῶν ὀφθαλμῶν τῶν ἡμετέρων ἔκρυψεν, '
        'ὃν ἐχώρισεν ἡμῶν ἡ παρακοή, ὃν ἐζήτει Δαυίδ· „ἐν ἡμέρᾳ θλίψεώς μου τὸν θεὸν ἐξεζήτησα.“ '
        'καὶ „ζητήσατε τὸν κύριον“ Σοφονίας βοᾷ „πάντες ταπεινοὶ γῆς.“ πέπαικεν ἡμᾶς ὁ θεός, '
        'ἡνίκα τῷ Ἀδὰμ κατεδίκασε θάνατον καὶ βίον ἐπίπονον· ἰάσατο δὲ καὶ πατάξας ἐμότωσεν, '
        'ὅτε σταυρωθεὶς ὑπὲρ τοῦ γένους τῷ μώλωπι αὐτοῦ κατὰ τὸν Ἠσαΐαν καὶ τῇ ἀναστάσει '
        'πάντας ἰάσατο. γυμνὸς ἐπὶ τοῦ σταυροῦ ὁ Χριστὸς ἀνήγετο· ἁμαρτίαν γὰρ οὐκ ἔχων '
        'ἱματίων οὐκ ἐχρῇζεν. ἄμωμος ἦν καὶ λανθάνειν οὐκ ὤφειλεν. οὐδὲν ἦν ἄσχημον αὐτῷ· '
        'αὐτὸς γὰρ ἡμῶν τὰ ἀσχήμονα εὐσχήμονα δείκνυσιν. εὗρον αἱ μυροφόροι, '
        'ὅπερ διὰ τῆς Εὔας ἀπώλεσαν· εὗρε τὸ κέρδος ἡ παρασχοῦσα τῆς ζημίας τὴν ὑπόθεσιν. '
        '„ἥξει ἡμῖν ὡς ὑετὸς πρώϊμος καὶ ὄψιμος τῇ γῇ.“ ὅρα τοίνυν τὸν κύριον μετὰ '
        'τὴν ἀνάστασιν πρώϊμον ταῖς γυναιξίν, ὄψιμον τοῖς ἀποστόλοις {uncertain}. '
        'πρωῒ μὲν γὰρ ταῖς γυναιξὶ χαίρετε, ὀψὲ δὲ ἐν τῇ Σιὼν εἰρήνην τοῖς μαθηταῖς '
        'προσεφώνησε, ταῖς μέν, ἵνα λύσῃ τὴν ἀπόφασιν τῆς λύπης, τοῖς δέ, '
        'ἵνα καταλύσῃ τὴν ἔχθραν, ἣν ὁ δράκων ἐκακούργησε. „σὺ κληθήσῃ Κηφᾶς.“ '
        'πρὸ τῆς ὁμολογίας ὁ μισθός· πρὶν ἐργάσῃ τὸν ἀμπελῶνα, τὸ δηνάριον ἔλαβες· '
        'πρὶν ἀνάψεις τὸν βωμόν,'),
    4: 'τὴν θυσίαν προσδέδεξαι· πρὶν κηρύξεις, ἐστεφανώθης.',
    5: 'πτωχοὺς καὶ ἀγραμμάτους ὁ Χριστὸς ἐξελέξατο. ἡ σο-',
    6: 'φία γὰρ οὐ χρήζει συνηγόρων ἀλλ’ ὑπηρετῶν· οὐδεὶς',
    7: 'γὰρ οὐδὲν αὐτῇ παρέχει, παρ’ αὐτῆς δὲ πάντες καὶ πάντα',
    8: 'λαμβάνομεν.',
    9: 'Ἀνεγνώ{uncertain}η τοῦ ΧΡΥΣΟΣΤΟΜΟΥ ἐκ τοῦ εἰς',
    10: 'τὸν ἅγιον Παῦλον.',
    11: 'ἦλθεν εἰς τὴν Ἀντιόχου πόλιν ὁ Παῦλος, καὶ το-',
    12: 'σοῦτον πλῆθος πιστῶν ἐγεώργησεν ὡς προσηγορίαν τὴν',
    13: 'τῶν Χριστιανῶν τότε πρῶτον ἐν αὐτῇ ἀνθῆσαι.',
    14: 'ταύτην τοίνυν ἐκ τῆς ἐπιγραφῆς τοῦ βωμοῦ τὴν ἀφορ-',
    15: 'μὴν λαβὼν ὁ πνευματικὸς ἡμῶν ῥήτωρ τὴν οἰκείαν',
    16: 'παρεισάγει διδασκαλίαν, ἐκ τῶν τοῦ διαβόλου γραμμά-',
    17: 'των πιστούμενος τὴν ἀλήθειαν. βωμὸν ἀνεστήσατε διὰ',
    18: 'τῆς ἐπιγραφῆς ὡς ἔστι θεὸς ἕτερος ἀγνοούμενος· τοῦ-',
    19: 'τον ἥκω κηρύττων ἐγώ. ὢ παραδόξων πραγμάτων!',
    20: 'τὸν βωμὸν τοῦ διαβόλου συνήγορον πεποίηκε τῷ Χρι-',
    21: 'στῷ· τὸ τῆς πλάνης ἐπίγραμμα ὑπὲρ τῆς ἀληθείας',
    22: 'ἐφθέγγετο· ἡ στήλη τῆς ἀπάτης ἐστηλίτευσε τὴν ἀπά-',
    23: 'την. ἐπειδὴ τὰ τῶν προφητῶν Ἀθηναίοις ἦν δυσ-',
    24: 'παράδεκτα, ὁ βωμὸς καὶ τὰ γράμματα τῶν δαιμόνων',
    25: 'τῇ σοφίᾳ Παύλου ἐκήρυσσε τὴν εὐσέβειαν. εἱστήκει',
    26: 'θρηνῶν ὁ διάβολος, ὁρῶν αὑτοῦ τὰ σοφίσματα ὑπὲρ',
    27: 'Χριστοῦ ῥητορεύοντα. ἐπένθει βλέπων τὸν αὑτοῦ ἀριστέα',
    28: 'Παῦλον κατ’ αὑτοῦ {uncertain}, καὶ τοῖς οἰκείοις ὅπλοις',
    29: 'αὐτὸν καταβάλλοντα.',
    30: 'Ἀνεγνώ{uncertain}η τοῦ μακαρίου ἈΣΤΕΡΙΟΥ, ἐπισκόπου',
    31: 'Ἀμασείας, ἐκ τοῦ προτρεπτικοῦ εἰς τὴν μετάνοιαν.',
    32: 'ὁ τοίνυν Λουκᾶς, ὁ πλέον τῶν ψυχῶν ἢ τῶν σω-',
    33: 'μάτων ἰατρός, αὐτὸν ἡμῶν τὸν θεὸν καὶ σωτῆρα ἀνα-',
    34: 'γράφει συγγνωμονικῶς τοῖς κατεγνωσμένοις συνανα-',
    35: 'στρεφόμενον, οὐχ ἵνα τι προσλάβῃ τῆς ἐκείνων κακίας,',
    36: 'ἀλλ’ ἵνα μεταδῷ τῆς οἰκείας δικαιοσύνης. καὶ γὰρ καὶ',
    37: 'ὁ ἥλιος, ὅσον ἀπὸ τοῦ κτίσματος τῷ {uncertain} παραστῆσαι',
    38: 'τὴν πρόνοιαν, οὐ τὰς ἡπλωμένας μόνον ἐπιλάμπει χώ-',
    39: 'ρας, ἀλλὰ καὶ ὅσαι κοιλότεραι καὶ τῆς ἀντρώδους ἔλα-',
    40: 'χον θέσεως. ὁ τῆς θεραπείας ἀπελπίσας δοῦλος',
    41: 'γίγνεται καθάπαξ τῆς νόσου. εἴ τινες κατὰ παθῶν',
    42: 'νικηφόροι ἀνεδείχθησαν καὶ ὡς ἀληθῶς ἐπάνω ὄφεων',
}
UNCERTAIN = {
    1: ('θ', '[σθ/θ]', 'The compact heading glyph may be a sigma-theta ligature '
        'or the open theta variant. Its separate sigma loop cannot be certified '
        'from the pinned scan. The digital Ἀνεγνώθησαν does not resolve this distinction.'),
    2: ('φανούμενον', 'φαιν[ό/ώ]μενον', 'The compact vowel sequence and accent in '
        'the participle after τοῖς ἀποστόλοις cannot be certified from this scan. '
        'The historical φανούμενον and digital φαινόμενον remain separate readings.'),
    28: ('ἐρατηγύρτα', 'στρατηγ[έ/οῦ]ντα', 'The compact type after στρατηγ- is '
         'insufficiently distinct to certify the complete printed participle. '
         'The digital στρατηγέντα is retained without selecting an inferred grammatical reading.'),
    9: ('σθ', '[σθ/θ]', 'The compact heading glyph may be a sigma-theta ligature '
        'or the open theta variant. A separate sigma loop is not distinct enough '
        'to certify. The digital page omits this printed heading.'),
    30: ('σθ', '[σθ/θ]', 'The compact heading glyph may be a sigma-theta ligature '
         'or the open theta variant. The scan does not distinguish a separate '
         'sigma loop confidently; the digital Ἀνεγνώθη remains an alternative.'),
    37: ('κτίσει', 'κτίστῃ?', 'The compact στ ligature and final vowel/subscript '
         'after κτί- cannot be resolved confidently. The historical κτίσει and '
         'digital κτίζει remain explicit; no inferred morphological completion is admitted.'),
}
FRAGMENTS = {
    5: [('σο-', 'trailing')], 6: [('φία', 'leading')],
    11: [('το-', 'trailing')], 12: [('σοῦτον', 'leading')],
    14: [('ἀφορ-', 'trailing')], 15: [('μὴν', 'leading')],
    16: [('γραμμά-', 'trailing')], 17: [('των', 'leading')],
    18: [('τοῦ-', 'trailing')], 19: [('τον', 'leading')],
    20: [('Χρι-', 'trailing')], 21: [('στῷ', 'leading')],
    22: [('ἀπά-', 'trailing')], 23: [('την', 'leading'), ('δυσ-', 'trailing')],
    24: [('παράδεκτα', 'leading')], 32: [('σω-', 'trailing')],
    33: [('μάτων', 'leading'), ('ἀνα-', 'trailing')],
    34: [('γράφει', 'leading'), ('συνανα-', 'trailing')],
    35: [('στρεφόμενον', 'leading')], 38: [('χώ-', 'trailing')],
    39: [('ρας', 'leading'), ('ἔλα-', 'trailing')], 40: [('χον', 'leading')],
}
DIGITAL_OVERRIDE = {
    4: 'τὴν θυσίαν προσδέδεξαι· πρὶν κηρύξεις, ἐσεφανώθης.',
    5: 'πτωχὸς καὶ ἀγράμματος ὁ Χριστὸς ἐξελέξατο. ἡ σο',
    17: 'των πιστεύμενος τὴν ἀλήθειαν. βωμὸν ἀνεστήσατε διὰ',
    18: 'τῆς ἐπιγραφῆς ὡς ἐπὶ θεὸς ἕτερος ἀγνοούμενος· τοῦ',
    19: 'τον ἐγὼ κηρύττων ἐγώ. ὢ παραδόξων πραγμάτων.',
    22: 'ἐφθέγγετο· ἡ ζήλη τῆς ἀπάτης ἐζηλίτευσε τὴν ἀπά',
    30: 'Ἀνεγνώθη τῷ μακαρίῳ ΑΣΤΕΡΙΟΥ, ἐπισκόπῳ',
    39: 'ρας, ἀλλὰ καὶ ὅσαι κοιλότεραι καὶ τῆς ἀντρώδεις ἔλα',
}
CONVENTION = (
    'Expand printed ου, στ, and καὶ ligatures. Preserve quotation delimiter '
    'conventions and paragraph whitespace while distinguishing source punctuation '
    'from marginal references. The margin reference1498R. is outside the quoted '
    'body. Retained passage divisions preserve literal printed word fragments '
    'and never create cross-passage words. The complete original rows and all '
    'recorded digital variants remain archived.'
)


def _sha_row(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def _fragments(number, text):
    result = []
    for word, side in FRAGMENTS.get(number, []):
        start = text.index(word) if side == 'leading' else text.rindex(word)
        result.append({'start': start, 'end': start + len(word), 'text': word, 'side': side,
            'qualification': 'The printed word continues across this retained '
                'passage boundary. Preserve the visible fragment without '
                'inventing a completion, joined word, or lexical adjacency.'})
    return sorted(result, key=lambda item: item['start'])


def records(rows, document, crop_png, sections):
    """Compile the explicitly reviewed retained passages, preserving uncertainty."""
    digital = sections['tlg4040-tlg001-local002-s510']
    result = []
    for number in LOCI:
        row = rows[PREFIX + str(number)]
        text = row['text']
        region = REGIONS['left' if number < 4 else 'right']
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        base = {'review_basis': 'direct-scan-inspection', 'reviewed_at': REVIEWED_AT,
            'evidence': 'Direct comparison of the complete retained passage with '
                'Bekker physical page233 / printed page498. Both body columns '
                'and enlarged upper, middle, lower, ligature, and heading '
                'regions were inspected, including every unchanged word and '
                'the printed passage-boundary divisions.',
            'transcription_convention': CONVENTION}
        def segment(start, end, original, corrected, **extra):
            return {**deepcopy(base), 'start': start, 'end': end,
                'original_text': original, 'corrected_text': corrected,
                'verification': 'verified', 'scan': {'physical_page': PAGE,
                    'region': region, 'image_sha256': image_sha, 'observed_text': corrected}, **extra}
        if number in UNCERTAIN:
            word, observed, reason = UNCERTAIN[number]
            if text.count(word) != 1 or TEXT[number].count('{uncertain}') != 1:
                raise ValueError('A reviewed uncertain historical word changed')
            start, end = text.index(word), text.index(word) + len(word)
            before, after = TEXT[number].split('{uncertain}')
            first = segment(0, start, text[:start], before)
            uncertain = segment(start, end, word, word, verification='uncertain', uncertainty=reason)
            uncertain['scan']['observed_text'] = observed
            final = segment(end, len(text), text[end:], after)
            segments, status = [first, uncertain, final], 'reviewed-with-uncertainty'
        else:
            whole = segment(0, len(text), text, TEXT[number])
            whole['fragments'] = _fragments(number, TEXT[number])
            segments, status = [whole], 'reviewed-verified'
        def counterpart(item, reading, low=None):
            if low is None and digital.count(reading) != 1:
                raise ValueError(f'A recorded page498 digital counterpart changed: {reading!r}')
            low = digital.index(reading) if low is None else low
            if digital[low:low + len(reading)] != reading:
                raise ValueError('An exact source review digital window changed')
            item['readings'] = [{'kind': 'digital', 'section': 'tlg4040-tlg001-local002-s510',
                'start': low, 'end': low + len(reading), 'text': reading}]
        # Exact bounded digital readings remain separate from the direct scan.
        # They supply no automatic certification or additional consensus vote.
        if number == 1:
            high = digital.index(' "σάλπιγξ')
            counterpart(segments[0], digital[:6], 0)
            counterpart(segments[1], digital[6:7], 6)
            counterpart(segments[2], digital[7:high], 7)
        elif number == 9:
            for item in segments:
                item['evidence'] += (' The expected digital page omits this '
                    'printed Chrysostom heading; it cannot supply a counterpart.')
        elif number == 30:
            low = digital.index(DIGITAL_OVERRIDE[30])
            high = low + len(DIGITAL_OVERRIDE[30])
            counterpart(segments[0], digital[low:low + 6], low)
            counterpart(segments[1], digital[low + 6:low + 7], low + 6)
            counterpart(segments[2], digital[low + 7:high], low + 7)
        elif number in UNCERTAIN:
            reading = {2: 'φαινόμενον', 28: 'στρατηγέντα', 37: 'κτίζει'}[number]
            counterpart(segments[1], reading)
            if number == 2:
                start = digital.index('"σάλπιγξ')
                middle = digital.index(reading, start)
                end = digital.index(' τὴν θυσίαν', middle)
                counterpart(segments[0], digital[start:middle])
                counterpart(segments[2], digital[middle + len(reading):end])
            elif number == 28:
                counterpart(segments[0], 'Παῦλον κατ’ αὑτοῦ ')
                counterpart(segments[2], ', καὶ τοῖς οἰκείοις ὅπλοις')
            else:
                counterpart(segments[0], 'ὁ ἥλιος, ὅσον ἀπὸ τοῦ κτίσματος τὸ ')
                counterpart(segments[2], ' παραστῆσαι')
        elif number not in {9, 10}:
            counterpart(segments[0], DIGITAL_OVERRIDE.get(number, TEXT[number].removesuffix('-')))
        else:
            segments[0]['evidence'] += (' The expected digital page omits this '
                'printed Chrysostom heading; it cannot supply a counterpart.')
        result.append({'locus': row['locus'], 'original_row_sha256': _sha_row(row),
                       'status': status, 'segments': segments})
    return result
