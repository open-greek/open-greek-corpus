"""Complete source review of the four retained passages on printed page499.

Long historical paragraphs were read against both complete body columns and
enlarged strips. Compact unresolved readings remain explicit spans and preserve
their historical display, rather than being completed from the digital witness.
"""
from copy import deepcopy
import hashlib
import json

PAGE = 234
REVIEWED_AT = '2026-10-21T12:20:42Z'
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0234.'
LOCI = (1, 2, 3, 4)
REGIONS = {'left': [.05, .105, .43, .725], 'right': [.41, .105, .81, .725]}
TEXT = {
    1: ('καὶ σκορπίων τὰ ἴχνη ἔθεντο, οὐδὲ τούτους χρὴ πρὸς τὴν οἰκείαν ἀνδρείαν καὶ τῶν '
        'ἄλλων κανονίζειν τὸν βίον, ἀλλὰ τῆς μὲν ἰδίας εὐδοκιμήσεως τῷ δεδωκότι θεῷ τὴν χάριν '
        'ὁμολογεῖν, τοῖς δ’ ἀσθενεστέροις οὐκ ἐπεμβαίνειν ἀλλὰ φιλάδελφον ὀρέγειν δεξιάν. '
        'ζηλώσατε τοῦ Χριστοῦ τὴν ἀγάπην. μέλλων γὰρ ἀνθρώποις ἐπιφαίνεσθαι, προκαθῆκε '
        'τὸν Ἰωάννην μετανοίας κήρυκα. Πέτρον ἐρώτησον, ὅπως μετανοήσας ἐκαθάρθη, καὶ '
        'οὐκ ἀνέλυσε εἰς τὸν Σίμωνα, ἀλλὰ διέμεινεν ὁ ἀπόστολος. ἐγὼ δὲ νομίζω ὅτι καὶ '
        'Ἰούδας ὁ προδότης, εἰ μὴ ταχέως αὐτὸς ἑαυτῷ ἐγένετο δήμιος, προσπεσὼν δὲ τὸν '
        'ἔλεον {u0}, οὐκ ἂν τῶν οἰκτιρμῶν τῶν πάσης ὑπερερχομένων τῆς οἰκουμένης ἡσύχησε. '
        'τεκμήριον δὲ οἱ μετανοήσαντες ἐκ τῶν σταυρωσάντων καὶ τῆς σωτηρίας διὰ τῆς μετανοίας '
        'ἀπολαύσαντες. ἐδίωκε ποτὲ καὶ Παῦλος Χριστιανούς, ἀλλὰ βαστάσας ὕστερον ἀλύσεις '
        'ὑπὲρ Χριστοῦ ἔλυσε τὰ ἐγκλήματα. ἐλίθαζε Στέφανον, ἀλλὰ {u1} ἐξήλειψε τὸ πλημμέλημα. '
        'ταῦτα καὶ Μωσῆς εἰδώς (ἄνθρωπος γὰρ ἦν καὶ τὴν φύσιν ἐγνώριζε) τὸν {u2} '
        'ὑπὲρ τοῦ ἱερέως {u3} διέταξεν, ἁμαρτηκότος πάντως καὶ καθαρσίων δεομένου. '
        'ὅπερ δὲ ἦν τότε ὁ ἐν σαρκὶ {u4}, τοῦτο νῦν ἐστὶν ἡ ἀσώματος μεταμέλεια καὶ '
        'ἡ ἀναίμακτος δέησις. ἐπὶ τοσοῦτον δὲ προσῆκε τὸν ἱερέα τὴν φιλανθρωπίαν ἀσκεῖν, '
        'ὥστε κἂν ὁ δεσπότης ἐκκόπτειν κελεύσῃ τινὰ ὡς φυτὸν ἄχρηστον, αὐτὸν ὡς φυτοκόμον '
        'αἰτεῖν δεῖ τὴν φειδὼ καὶ ὑπέρθεσιν. τοῦτον γὰρ ἡμῖν παρίησι τὸν νοῦν τῆς ἀκάρπου '
        'συκῆς ὁ ἐν τῷ εὐαγγελίῳ λόγος. σκόπησον τὴν ἁμαρτωλὸν γυναῖκα. οὐ τὸ πλῆθος τῶν '
        'ἑστιωμένων ἠρυθρίασεν, οὐ τὸν καιρὸν τῆς εὐωχίας ὡς ἄκαιρον τῆς ἐξομολογήσεως '
        'ἔφυγεν, ἀλλὰ σφοδρὸν ἔχουσα τὸ πένθος οὐδὲ τὸ βραχύτατον ἠφίει τὸν τῶν ἁμαρτιῶν '
        'ἰατρόν. οὐ μὴν οὐδὲ κατ’ ὄψιν ἐρχομένη ἱκέτευεν· ἀλλὰ τὸ ἀνάξιον ἑαυτῆς διὰ '
        'τοῦ σχήματος ἑρμηνεύουσα, τὴν κατὰ νῶτα χώραν καταλαβοῦσα, καὶ τῶν ποδῶν λαβομένη, '
        'καὶ λύσασα τὰς κόμας, καὶ δημοσιεύουσα πᾶσιν οἷς ἔπραττε τὴν πενθοῦσαν ψυχήν, '
        'καὶ τοὺς πόδας τοῦ σωτῆρος τοῖς δάκρυσιν ἐπιρραίνουσα μετὰ πολλῆς τῆς συμπαθείας '
        'ἤτει τὸν ἔλεον. Τοῦ αὐτοῦ ἐκ τοῦ εἰς τὸν πρωτομάρτυρα Στέφανον. '
        'εἱστήκει δὲ μόνος τῷ δήμῳ τῶν φονώντων κεκυ-'),
    2: ('κλωμένος, οὐδεὶς δὲ κατ’ ἐκείνην τὴν ὥραν ἐγγύς, οὐ φίλος, οὐκ οἰκεῖος, οὐ συγγενής· '
        'φέρει γάρ πως παραμυθίαν τοῖς κινδυνεύουσι τὸ βλέπειν παρόντα τινὰ τῶν γνωρίμων. '
        'προσετίθει τῇ δεήσει καὶ τὴν ὑπὲρ τῶν λιθαζόντων εὐχήν· εὐηργέτουν γὰρ καὶ '
        'λιθάζοντες ἄκοντες. καὶ ἡ εὐχὴ τίνα φέρει σκοπόν; οὐκ ἀνεύθυνον γενέσθαι τῶν ἐχθρῶν '
        'αἰτεῖται τὸ ἁμάρτημα· τοῦτο γὰρ φανερῶς τῇ τοῦ θεοῦ διατυπώσει ἀνθίσταται, '
        'ἣ τοῖς ἀνδροφόνοις τὴν δικαίαν κρίσιν ὥρισεν· ἀλλὰ τί φησι; μὴ στήσῃς αὐτοῖς '
        'τὴν ἁμαρτίαν ταύτην, τουτέστι δὸς φόβον κατανύξεως, ἄγαγε πρὸς μετάνοιαν τῶν νῦν '
        'τετολμημένων. καὶ ἦν ὑπηρέτης ὁ φυλάττων Παῦλος τὰ ἱμάτια τῶν ἀναιρούντων {u0}. '
        '{u1} καὶ διὰ τὸν Λίβυν Σαβέλλιον, προανακόπτων αὐτοῦ τῶν ἐκκλησιῶν τὴν βλάβην, '
        'δείκνυσι μὲν ἑαυτὸν ἐν ἰδίᾳ καὶ αὐτοτελεῖ δόξῃ, δείκνυσι δὲ καὶ τὸν υἱὸν ἐν '
        'ἀπηρτισμένῳ προσώπῳ. ἵστησι δὲ ἐκ δεξιῶν αὐτοῦ, ἵνα τῇ διευκρινήσει τῶν προσώπων '
        'ἑρμηνεύσῃ τὰς ὑποστάσεις. καὶ τὸ πνεῦμα τὸ ἅγιον {u2}· καὶ γὰρ προεῖπεν '
        '„καὶ οὐκ ἴσχυον ἀντιστῆναι τῇ σοφίᾳ καὶ τῷ πνεύματι, ᾧ ἐλάλει.“ '
        'ἰδοὺ τοίνυν, καὶ τὸ τοῦ πνεύματος ἡμῖν πρόσωπον εὐκρινῶς ὁ λόγος {u3}. '
        'εἰ δὲ τὸ πνεῦμα πρότερον γέγραπται, ἔπειτα δὲ ὁ πατὴρ καὶ ὁ υἱός, οὐδὲν τῆς τάξεως '
        'ἡ ἐναλλαγὴ τῇ πίστει λυμαίνεται. σύνηθες γὰρ τοῦτο τῇ γραφῇ· ποτὲ μὲν ὀνομάζει '
        'τὸν υἱὸν μόνον, ποτὲ δὲ τὸ πνεῦμα σὺν τῷ υἱῷ· ἄλλοτε δὲ ἄρχεται μὲν τοῦ πατρός, '
        'καταλήγει δὲ εἰς τὸ πνεῦμα, καὶ τὸ ἀνάπαλιν. ἀρχὴν μὲν ποιεῖται τὸ πνεῦμα, '
        'ὁδεύει δὲ διὰ τοῦ υἱοῦ ἐπὶ τὸν πατέρα. καὶ τὸ ἰδίωμα τοῦτο μάλιστα τῷ θείῳ '
        'συντηρεῖται Παύλῳ.'),
    3: 'Τοῦ αὐτοῦ εἰς τὸ «ἄνθρωπός τις κατέβαινεν ἀπὸ Ἱερουσαλὴμ εἰς Ἰεριχώ.»',
    4: ('τί τοίνυν ὁ Χριστὸς πρὸς τὸν πειράζοντα νομικὸν φησιν; «ἐν τῷ νόμῳ τί γέγραπται;» '
        'ὑπομιμνήσκων αὐτὸν τῆς πρὸς θεὸν καὶ τῆς πρὸς τὸν πλησίον ἀγάπης, μόνον οὐχὶ '
        'λέγων ὡς εἰ μὲν θεὸς ἐγώ σοι δοκῶ, ὀφείλεις μοι τὴν ἀγάπην· εἰ δ’ ἀπιστεῖς καὶ '
        'ὅμοιον σοὶ νομίζεις ἐμὲ ψιλὸν ἄνθρωπον, καὶ οὕτω τὸ ἀγαπᾶν χρεωστεῖς κατὰ τὸν '
        'νόμον. ἀδελφοὺς καλοῦμεν ἐκείνους, οἳ ἐξ ἑνὸς ἔφυσαν σπέρματος καὶ μιᾶς γαστρός. '
        'οἱ δὲ τὸν αὐτὸν ἔχοντες ποιητὴν καὶ μίαν μητέρα τὴν γῆν, ἀφ’ ἧς {u0}, '
        'καὶ ψυχῆς ἀξίωμα παρα-'),
}
UNCERTAIN = {
    1: [
        ('ᾔτησεν', 'ᾔτησεν/ἤτησεν', 'ἤτησεν', 'The eta subscript/breathing in this verb is not distinct enough to certify.'),
        ('λισαθεὶς', 'λιθα[σ?]θεὶς', 'λιθαθεὶς', 'A separate sigma loop before theta is not distinct enough to resolve the compact printed reading.'),
        ('μύρον', 'μό[σ?]χον', 'μόχον', 'The compact sigma-chi combination cannot be distinguished confidently from the chi variant.'),
        ('ἱεραρχεῖν', 'ἱερουργεῖ[σ?]θαι', 'ἱερεργείας', 'The terminal compact type is not sufficiently distinct to certify the complete verb.'),
        ('μῦρος', 'μό[σ?]χος', 'μόχος', 'The sigma-chi loop is not distinct enough to certify the complete printed noun.'),
    ],
    2: [
        ('δήμα δεῖμα', 'δῆμα/δήμιον δημίων?', 'δήμα δημίς', 'The two short words following ἀναιρούντων remain unclear; no grammatical reconstruction is selected.'),
        ('διὰ τι ἄν ἄλλα', 'διά τε τἄλλα?', 'Διά τε ἓν ἄλλα', 'The compact introductory connective and possible crasis are not distinct enough to certify.'),
        ('συν- 10οτέταχθ', 'συντέτακται?', 'συντέτακθ’', 'The compact final type may represent a contracted ending; its expansion remains uncertain.'),
        ('ἐπιφανῶς', 'ὑπέ[στη/ξη]σεν', 'ὑπέξησεν', 'The final verb contains a compact cluster that cannot be certified as separate letters from this scan.'),
    ],
    4: [('διπλασίασμεν', 'διεπλά[σ?]θημεν', 'διεπλάθημεν',
         'The sigma-theta cluster is insufficiently distinct to certify the exact source form.')],
}
CONVENTION = (
    'Expand clearly identified ου, στ, καὶ, and γὰρ ligatures and abbreviations. '
    'Retain unresolved compact type as explicit uncertainty. Join internal '
    'printed line divisions only within a retained passage; preserve actual '
    'passage-boundary fragments. Margin references and line numbers are not '
    'authorial body text. Preserve declared historical quotation delimiters '
    'and paragraph whitespace. The full original rows remain reversible.'
)


def _sha_row(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def records(rows, document, crop_png, sections):
    """Compile only the four explicitly completed physical page234 reviews."""
    digital = sections['tlg4040-tlg001-local002-s511']
    split = digital.index('κεκυκλωμένος') + len('κεκυ')
    heading = digital.index('Τοῦ αὐτοῦ εἰς τὸ')
    last = digital.index('τί τοίνυν ὁ Χρισὸς')
    windows = {1: (0, split), 2: (split, heading - 1), 3: (heading, last - 1), 4: (last, len(digital))}
    result = []
    for number in LOCI:
        row = rows[PREFIX + str(number)]
        text = row['text']
        region = REGIONS['left' if number == 1 else 'right']
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        base = {'review_basis': 'direct-scan-inspection', 'reviewed_at': REVIEWED_AT,
            'evidence': 'Direct comparison of every retained word and unchanged '
                'span with Bekker physical page234 / printed page499. Full body '
                'columns and enlarged upper-left, middle-left, upper-right, and '
                'lower-right strips were inspected. Compact unresolved readings '
                'are recorded separately; margin references and numbered lines '
                'were distinguished from the authorial body.',
            'transcription_convention': CONVENTION}
        def segment(start, end, original, corrected, **extra):
            return {**deepcopy(base), 'start': start, 'end': end,
                'original_text': original, 'corrected_text': corrected,
                'verification': 'verified', 'scan': {'physical_page': PAGE,
                    'region': region, 'image_sha256': image_sha, 'observed_text': corrected}, **extra}
        low, high = windows[number]
        original_cursor, digital_cursor = 0, low
        segments = []
        tail = TEXT[number]
        for index, (old, observed, digital_word, reason) in enumerate(UNCERTAIN.get(number, [])):
            if text.count(old) != 1 or tail.count('{u' + str(index) + '}') != 1:
                raise ValueError('A reviewed page499 uncertain original span changed')
            start = text.index(old)
            if start < original_cursor:
                raise ValueError('Reviewed page499 uncertainties changed source order')
            before, tail = tail.split('{u' + str(index) + '}')
            digital_start = digital.index(digital_word, digital_cursor, high)
            if start > original_cursor:
                item = segment(original_cursor, start, text[original_cursor:start], before)
                item['readings'] = [{'kind': 'digital', 'section': 'tlg4040-tlg001-local002-s511',
                    'start': digital_cursor, 'end': digital_start,
                    'text': digital[digital_cursor:digital_start]}]
                segments.append(item)
            item = segment(start, start + len(old), old, old, verification='uncertain',
                           uncertainty=reason)
            item['scan']['observed_text'] = observed
            item['readings'] = [{'kind': 'digital', 'section': 'tlg4040-tlg001-local002-s511',
                'start': digital_start, 'end': digital_start + len(digital_word), 'text': digital_word}]
            segments.append(item)
            original_cursor = start + len(old)
            digital_cursor = digital_start + len(digital_word)
        final = segment(original_cursor, len(text), text[original_cursor:], tail)
        final['readings'] = [{'kind': 'digital', 'section': 'tlg4040-tlg001-local002-s511',
            'start': digital_cursor, 'end': high, 'text': digital[digital_cursor:high]}]
        segments.append(final)
        for item, word, side in ((segments[-1], 'κεκυ-', 'trailing'),) if number == 1 else (
                ((segments[0], 'κλωμένος', 'leading'),) if number == 2 else (
                ((segments[-1], 'παρα-', 'trailing'),) if number == 4 else ())):
            position = item['corrected_text'].index(word)
            item['fragments'] = [{'start': position, 'end': position + len(word),
                'text': word, 'side': side, 'qualification': 'The printed word '
                    'crosses this retained passage boundary. Keep the visible '
                    'fragment separate and exclude it from lexical counts.'}]
        result.append({'locus': row['locus'], 'original_row_sha256': _sha_row(row),
            'status': 'reviewed-with-uncertainty' if number in UNCERTAIN else 'reviewed-verified',
            'segments': segments})
    return result
