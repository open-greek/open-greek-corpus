"""Source-reviewed Cary body boundaries used by prepare_dio_body_regions.

Coordinates identify source-image whitespace, never replacement OCR readings.
All complete contact sheets were inspected; these exceptions received a second
source comparison because an automatic font transition was incomplete.
"""

OVERRIDES = {(6, 208): {'y1': 0.7511,
            'evidence': 'The first small note precedes the detected editor anchor; preserve the last large '
                        'Greek line and exclude all three notes. Source inspection confirms the revised '
                        'boundary retains the complete full-size body and excludes editorial notes.'},
 (6, 212): {'y1': 0.7079,
            'evidence': 'The detected anchor starts at the third note; exclude the two preceding small notes '
                        'too. Source inspection confirms the revised boundary retains the complete full-size '
                        'body and excludes editorial notes.'},
 (6, 228): {'y1': 0.8012,
            'evidence': 'Single small note containing R. Stephanus credit was not detected. Source '
                        'inspection confirms the revised boundary retains the complete full-size body and '
                        'excludes editorial notes.'},
 (6, 236): {'y1': 0.7778,
            'evidence': 'A body δέ was misrecognized as an editor abbreviation; preserve the following '
                        'full-size Greek line. Source inspection confirms the revised boundary retains the '
                        'complete full-size body and excludes editorial notes.'},
 (7, 7): {'y1': 0.8161,
          'evidence': 'Single small Bk. note was not detected. Source inspection confirms the revised '
                      'boundary retains the complete full-size body and excludes editorial notes.'},
 (7, 22): {'y1': 0.78341,
           'evidence': 'Single supplied-by-Bk. apparatus note remains above the proposed cut. Source '
                       'inspection confirms the revised boundary retains the complete full-size body and '
                       'excludes editorial notes.'},
 (7, 39): {'y1': 0.81909,
           'evidence': 'The proposed cut divides the large Greek body; move below the remaining body and '
                       'before the small apparatus. Source inspection confirms the revised boundary retains '
                       'the complete full-size body and excludes editorial notes.'},
 (7, 41): {'y1': 0.78318,
           'evidence': 'Both the short chapter cross-reference and the Deeds of Augustus explanatory '
                       'footnote are apparatus. Source inspection confirms the revised boundary retains the '
                       'complete full-size body and excludes editorial notes.'},
 (7, 60): {'y1': 0.72682,
           'evidence': 'Preserve the complete consul list; exclude the numbered editorial notes beginning '
                       'supplied by Bs. Source inspection confirms the revised boundary retains the complete '
                       'full-size body and excludes editorial notes.'},
 (7, 79): {'y1': 0.74614,
           'evidence': 'Exclude both explanatory notes, beginning the celebrated-gladiator note. Source '
                       'inspection confirms the revised boundary retains the complete full-size body and '
                       'excludes editorial notes.'},
 (7, 91): {'y1': 0.82636,
           'evidence': 'Two short small apparatus notes remain above the proposed cut. Source inspection '
                       'confirms the revised boundary retains the complete full-size body and excludes '
                       'editorial notes.'},
 (7, 95): {'y1': 0.76068,
           'evidence': 'Five small apparatus notes remain above the proposed cut. Source inspection confirms '
                       'the revised boundary retains the complete full-size body and excludes editorial '
                       'notes.'},
 (7, 109): {'y1': 0.75114,
            'evidence': 'The cut includes the first three small apparatus notes; move above note1. Source '
                        'inspection confirms the revised boundary retains the complete full-size body and '
                        'excludes editorial notes.'},
 (7, 111): {'y1': 0.81477,
            'evidence': 'Preserve the last full-size Greek body line below the proposed cut. Source '
                        'inspection confirms the revised boundary retains the complete full-size body and '
                        'excludes editorial notes.'},
 (7, 114): {'y1': 0.82659,
            'evidence': 'The cut divides the body; preserve the remaining full-size Greek paragraph above '
                        'two small notes. Source inspection confirms the revised boundary retains the '
                        'complete full-size body and excludes editorial notes.'},
 (7, 144): {'y1': 0.815,
            'evidence': 'The cut includes the first two small apparatus notes; move above note1. Source '
                        'inspection confirms the revised boundary retains the complete full-size body and '
                        'excludes editorial notes.'},
 (7, 160): {'y1': 0.75432,
            'evidence': 'The cut includes the first small Greek editorial note above the English note; move '
                        'above both. Source inspection confirms the revised boundary retains the complete '
                        'full-size body and excludes editorial notes.'},
 (7, 176): {'y1': 0.64523,
            'evidence': 'Exclude the long small-font comparative quotation beginning Cf. before the '
                        'remaining short notes. Source inspection confirms the revised boundary retains the '
                        'complete full-size body and excludes editorial notes.'},
 (7, 181): {'y1': 0.72545,
            'evidence': 'The cut includes the first small apparatus note; move above note1. Source '
                        'inspection confirms the revised boundary retains the complete full-size body and '
                        'excludes editorial notes.'},
 (7, 185): {'y1': 0.80068,
            'evidence': 'A small apparatus note lies above the proposed full-height cut. Source inspection '
                        'confirms the revised boundary retains the complete full-size body and excludes '
                        'editorial notes.'},
 (7, 187): {'y1': 0.23864,
            'evidence': 'Full-page inspection finds one high-on-page small note after the Joannes '
                        'Antiochenus credit; it is outside the bottom contact window. Source inspection '
                        'confirms the revised boundary retains the complete full-size body and excludes '
                        'editorial notes.'},
 (7, 192): {'y1': 0.83114,
            'evidence': 'Preserve the final large Greek body line below the cut, then exclude the small '
                        'Greek and English notes. Source inspection confirms the revised boundary retains '
                        'the complete full-size body and excludes editorial notes.'},
 (7, 200): {'y1': 0.83455,
            'evidence': 'Exclude the English explanatory note about Mauretania. Source inspection confirms '
                        'the revised boundary retains the complete full-size body and excludes editorial '
                        'notes.'},
 (7, 217): {'y1': 0.81909,
            'evidence': 'The proposed cut includes the first line of the English lacuna note; exclude the '
                        'complete note. Source inspection confirms the revised boundary retains the complete '
                        'full-size body and excludes editorial notes.'},
 (7, 225): {'y1': 0.73068,
            'evidence': 'Preserve the remaining full-size Greek quotation and Petrus Patricius credit below '
                        'the cut. Source inspection confirms the revised boundary retains the complete '
                        'full-size body and excludes editorial notes.'},
 (8, 12): {'y1': 0.81341,
           'evidence': 'A small Greek textual note remains above the full-height cut. Source inspection '
                       'confirms the revised boundary retains the complete full-size body and excludes '
                       'editorial notes.'},
 (8, 16): {'y1': 0.68295,
           'evidence': 'Exclude the complete comparative note beginning Cf. Petr. Patr.; its first line lies '
                       'above the cut. Source inspection confirms the revised boundary retains the complete '
                       'full-size body and excludes editorial notes.'},
 (8, 33): {'y1': 0.66182,
           'evidence': 'Exclude all seven small Greek notes and the English note below their rule. Source '
                       'inspection confirms the revised boundary retains the complete full-size body and '
                       'excludes editorial notes.'},
 (8, 60): {'y1': 0.73205,
           'evidence': 'The cut includes the first three small apparatus notes; exclude the complete '
                       'contiguous apparatus. Source inspection confirms the revised boundary retains the '
                       'complete full-size body and excludes editorial notes.'},
 (8, 76): {'y1': 0.81886,
           'evidence': 'Preserve the final large Greek body line below the proposed cut. Source inspection '
                       'confirms the revised boundary retains the complete full-size body and excludes '
                       'editorial notes.'},
 (8, 78): {'y1': 0.91,
           'evidence': 'Full-page source inspection confirms the complete Petrus Patricius credit and following primary quotation are retained; no Greek apparatus occurs on this leaf.'},
 (8, 85): {'y1': 0.79795,
           'evidence': 'Preserve the remaining full-size Greek quotation and its source credit below the '
                       'proposed cut. Source inspection confirms the revised boundary retains the complete '
                       'full-size body and excludes editorial notes.'},
 (8, 87): {'y1': 0.80205,
           'evidence': 'Three small apparatus notes remain above the full-height cut. Source inspection '
                       'confirms the revised boundary retains the complete full-size body and excludes '
                       'editorial notes.'},
 (8, 94): {'y1': 0.56023,
           'evidence': 'The cut lies within the long apparatus; exclude the preceding short notes and '
                       'complete comparative note. Source inspection confirms the revised boundary retains '
                       'the complete full-size body and excludes editorial notes.'},
 (8, 101): {'y1': 0.45,
            'evidence': 'The contact strip is already in small apparatus; inspect full page and move above '
                        'the first Cf. Joann. Antioch. note. Source inspection confirms the revised boundary '
                        'retains the complete full-size body and excludes editorial notes.'},
 (8, 103): {'y1': 0.77659,
            'evidence': 'Preserve the final full-size Greek quotation below the cut, then exclude small '
                        'Greek and English notes. Source inspection confirms the revised boundary retains '
                        'the complete full-size body and excludes editorial notes.'},
 (8, 143): {'y1': 0.83813,
            'evidence': 'Retains the final main-text line Μεγαλοφρονέστατα δὲ ἀεὶ ποτε ἐς τὸ κοινὸν; '
                        'excludes the smaller numbered variants.',
            'blank_gap': [0.83213, 0.84412]},
 (8, 150): {'y1': 0.77626,
            'evidence': 'Retains the last full-size line ending γυνὴ Πεπονίλα, ἥπερ; excludes the smaller '
                        'Berenice/reading notes.',
            'blank_gap': [0.76643, 0.78609]},
 (8, 152): {'y1': 0.83749,
            'evidence': 'Retains the full-size body ending τὴν ἐξαρίθμησιν τοῦ χρόνου πρὸς; excludes the '
                        'smaller supplied-by-Bekker note.',
            'blank_gap': [0.83174, 0.84324]},
 (8, 162): {'y1': 0.58369,
            'evidence': 'Retains the full-size closing Greek and printed Xiphilinus source reference; '
                        'excludes both smaller variant notes below.',
            'blank_gap': [0.57458, 0.59281]},
 (8, 167): {'y1': 0.80024,
            'evidence': 'Retains the last full-size main-text/source-reference line; excludes the English '
                        'editorial note containing Κελτικήν and the smaller Greek variant below.',
            'blank_gap': [0.79424, 0.80624]},
 (8, 168): {'y1': 0.76222,
            'evidence': 'Retains all remaining full-size Greek through καὶ; excludes the small '
                        'πορφυροῦν/ἀργυροῦν variant and translation notes.',
            'blank_gap': [0.75024, 0.77421]},
 (8, 174): {'y1': 0.82494,
            'evidence': 'Retains the last full-size opening of section5.1, ending Χερουσκων βασιλεύς; '
                        'excludes the smaller lacuna note below.',
            'blank_gap': [0.81775, 0.83213]},
 (8, 184): {'y1': 0.41295,
            'evidence': 'Retains the closing full-size Greek and Xiphilinus source citation; excludes both '
                        'smaller Greek/Latin notes below.',
            'blank_gap': [0.40576, 0.42014]},
 (8, 185): {'y1': 0.8693,
            'evidence': 'Retains the final full-size line καὶ ὑπ ἀρρωστίας ... τὴν τροφὴν ἀεί. No Greek '
                        'apparatus occurs on this leaf; the cut excludes the printed page number.',
            'blank_gap': [0.86859, 0.87002]},
 (8, 201): {'y1': 0.77698,
            'evidence': 'Retains the full-size final line ending τὰς ἀπειλὰς; excludes the smaller '
                        'Kelsos/Osroes reading notes below.',
            'blank_gap': [0.7717, 0.78225]},
 (8, 210): {'y1': 0.84173,
            'evidence': 'Retains the full-size parenthetical quotation beginning Ἡ δὲ Σεμίραμις and its last '
                        'line; excludes the smaller ἀναφανῆναι variant below.',
            'blank_gap': [0.83837, 0.84508]},
 (8, 215): {'y1': 0.79962,
            'evidence': 'Retains the final full-size clause ending ὥστε τὰς ἁπάσας δύο; excludes the three '
                        'small numbered reading notes.',
            'blank_gap': [0.79386, 0.80537]},
 (8, 217): {'y1': 0.83669,
            'evidence': 'Retains the final full-size Greek ending πῦρ ἐκ τοῦ; excludes the smaller Hadrian '
                        'name note.',
            'blank_gap': [0.83165, 0.84173]},
 (8, 222): {'y1': 0.86307,
            'evidence': 'Retains the final full-size line οὐ σχολάζω ... ἐκείνη ἀνακραγοῦσα. There are no '
                        'Greek apparatus notes on this leaf; the cut excludes the printed page number.',
            'blank_gap': [0.85803, 0.86811]},
 (8, 230): {'y1': 0.81592,
            'evidence': 'Retains the last full-size clause Μασσαγέται ... ὑπὸ Φαρασμάνου καὶ; excludes the '
                        'two smaller Greek variant notes below.',
            'blank_gap': [0.80968, 0.82215]},
 (9, 14): {'y1': 0.82427,
           'evidence': 'Retains the final full-size Greek sentence ending τοῦτο; excludes all three smaller '
                       'variant notes below.',
           'blank_gap': [0.81974, 0.8288]},
 (9, 17): {'y1': 0.82785,
           'evidence': 'Retains the final full-size Greek ending ἀλλὰ; excludes the smaller τοιουτοτρόπου '
                       'and καί notes.',
           'blank_gap': [0.82165, 0.83405]},
 (9, 19): {'y1': 0.78302,
           'evidence': 'Retains all full-size Greek including the bracketed Xiphilinus paragraph through '
                       'προση-. Excludes the separator and English footnotes below, which are not authorial '
                       'Greek.',
           'blank_gap': [0.77492, 0.79113]},
 (9, 22): {'y1': 0.69552,
           'evidence': 'Retains the full-size body ending τὸ διπλάσιον αὐτῶν ἀπὸ τοῦ Ἴστρου ἀποικῆσαι. '
                       'Excludes all smaller notes, including the indented tragic quotation and its Exc.Val. '
                       'citation.',
           'blank_gap': [0.6867, 0.70434]},
 (9, 27): {'y1': 0.87363,
           'evidence': 'Retains the last full-size Greek beginning Παρασκευαζομένῳ δὲ τῷ Μάρκῳ. No Greek '
                       'apparatus is on this leaf; excludes the printed page number.',
           'blank_gap': [0.87077, 0.87649]},
 (9, 29): {'y1': 0.78422,
           'evidence': 'Retains the final full-size clause ending μάλιστα μὲν; excludes all three smaller '
                       'variant notes below.',
           'blank_gap': [0.77969, 0.78875]},
 (9, 30): {'y1': 0.6216,
           'evidence': 'Retains the full-size main text ending μὴ γὰρ γένοιτο ... μηδένα. Excludes the '
                       'extensive smaller Greek notes quoting John of Antioch and Peter the Patrician.',
           'blank_gap': [0.61373, 0.62947]},
 (9, 33): {'y1': 0.78994,
           'evidence': 'Retains the full-size final line ending παρὰ τῷ Ἐνυείῳ ἐς τὸ; excludes the three '
                       'smaller variant notes.',
           'blank_gap': [0.78493, 0.79495]},
 (9, 46): {'y1': 0.81378,
           'evidence': 'Retains the full-size final line ending τῆς Κιλικίας, πρὶν; excludes smaller Greek '
                       'variant notes below.',
           'blank_gap': [0.80782, 0.81974]},
 (9, 55): {'y1': 0.84549,
           'evidence': 'Retains the final full-size line ending ἑαυτῷ δὲ; excludes the smaller μεγίστη note.',
           'blank_gap': [0.83977, 0.85122]},
 (9, 75): {'y1': 0.86934,
           'evidence': 'Restores the entire full-size paragraph11 below the erroneous old cut, through τὰ '
                       'ἐκεῖ κατεστησάμενος ἔμεινε. No Greek apparatus is on this leaf; excludes printed '
                       'page number.',
           'blank_gap': [0.86409, 0.87458]},
 (9, 103): {'y1': 0.8114,
            'evidence': 'Restores all remaining full-size Greek below the old cut, through τήν τε χώραν τῶν '
                        'βαρβάρων ἐδήουν; excludes all smaller reading notes.',
            'blank_gap': [0.80639, 0.8164]},
 (9, 119): {'y1': 0.7835,
            'evidence': 'Preserve the full-size body ending τὸν Πλαυτιανόν, καὶ ἐς αὐτοὺς τοὺς αὐτοκρά-; '
                        'exclude the smaller critical notes below.',
            'blank_gap': [0.77778, 0.78922]},
 (9, 123): {'y1': 0.40343,
            'evidence': 'Preserve the full-size body and Xiphilinus313,21–314,13 citation; exclude the '
                        'smaller ἀπηναύτισεν/ἀπεναύτισεν critical note directly below.',
            'blank_gap': [0.39771, 0.40916]},
 (9, 128): {'y1': 0.80424,
            'evidence': 'Preserve the full-size body ending οἷά που πλεῖστοι πρὸς τοὺς εὐτυχοῦντας πλάτ-; '
                        'exclude the smaller notes below.',
            'blank_gap': [0.80114, 0.80734]},
 (9, 133): {'y1': 0.81807,
            'evidence': 'Preserve the full-size body ending τῶν μὲν τῶν αὐτοκρατόρων, παρόντων δὲ καὶ; '
                        'exclude the English editorial note and its Greek reading Αὔσπικα below.',
            'blank_gap': [0.80973, 0.82642]},
 (9, 134): {'y1': 0.78851,
            'evidence': 'Preserve the full-size body ending τρέφετε, ἵνα μὴ λῃστεύωσι. πλείστους γὰρ; '
                        'exclude the smaller Greek critical notes below.',
            'blank_gap': [0.78255, 0.79447]},
 (9, 140): {'y1': 0.82046,
            'evidence': 'Preserve the full-size indented quotation and following body ending ὁμονοεῖτε, τοὺς '
                        'στρατιώτας πλουτίζετε, τῶν; exclude the smaller μήτηρ supplied-text note below.',
            'blank_gap': [0.8164, 0.82451]},
 (9, 144): {'y1': 0.83119,
            'evidence': 'Preserve the full-size body ending γὰρ καὶ φιλεῖν ἀλλήλους καὶ ἐπαινεῖν, πάντα δὲ; '
                        'exclude the smaller Παπινιανός and καί notes below.',
            'blank_gap': [0.82833, 0.83405]},
 (9, 146): {'y1': 0.86791,
            'evidence': 'Restore the last full-size body line ἐξ ὑμῶν εἰμί, καὶ δι’ ὑμᾶς μόνους ζῆν ἐθέλω; '
                        'no Greek apparatus on the left page; exclude the page number. The body descenders '
                        'and page number leave only one clear raster row at4x in the reviewed Greek column.',
            'blank_gap': [0.86791, 0.86791]},
 (9, 147): {'y1': 0.68216,
            'evidence': 'Preserve the body and Xiphilinus/Excerpta Valesiana credits through τῶν δορυφόρων '
                        'ἐπί τισι κατηγορησάντων αὐτῶν; exclude all smaller notes, including the Petrus '
                        'Patricius Greek quotation.',
            'blank_gap': [0.67287, 0.69146]},
 (9, 149): {'y1': 0.73247,
            'evidence': 'Preserve the body through the Excerpta Valesiana359 citation; exclude the smaller '
                        'ὁμοίως and Θρασέαν critical notes below.',
            'blank_gap': [0.72485, 0.7401]},
 (9, 174): {'y1': 0.38388,
            'evidence': 'Preserve the full-size body and Excerpta Valesiana396(p757) citation; exclude all '
                        'three smaller Greek critical notes immediately below.',
            'blank_gap': [0.37959, 0.38817]},
 (9, 176): {'y1': 0.74154,
            'evidence': 'Preserve the full-size body ending κινδυνεῦσαί τε ἦν καὶ ἀσθενέστατος πρᾶξαί τι ἦν; '
                        'exclude the smaller manuscript/editorial note below.',
            'blank_gap': [0.73486, 0.74821]},
 (9, 185): {'y1': 0.81354,
            'evidence': 'Preserve the full-size body ending πρὸς μὲν τὸν Σεουῆρον τοῖς ὀχήμασι τοῖς; exclude '
                        'the isolated signature and smaller προστάντα note below.',
            'blank_gap': [0.80973, 0.81736]},
 (9, 197): {'y1': 0.82904,
            'evidence': 'Restore the full-size final line ἐφ’ ᾧ δὴ καὶ δημοσίᾳ ἀτιμίαν ὑπ’ αὐτοῦ ὤφλον; '
                        'exclude the smaller ἡ τῇ and other variants below.',
            'blank_gap': [0.82594, 0.83214]},
 (9, 206): {'y1': 0.78302,
            'evidence': 'Preserve the full-size body ending Καππαδοκίᾳ ἐκέκτητο, τό τε ἀργύριον ὃ κατ’ ἔτος; '
                        'exclude the smaller τῇ and other critical notes below.',
            'blank_gap': [0.77396, 0.79208]},
 (9, 207): {'y1': 0.83214,
            'evidence': 'Preserve the full-size body ending ἥξοντας, τὸ μὲν πρῶτον ὑπό τε τοῦ ἀμάχου; '
                        'exclude the smaller τὸ critical note below.',
            'blank_gap': [0.82499, 0.83929]},
 (9, 219): {'y1': 0.76252,
            'evidence': 'Preserve the full-size body ending πάντως ἄν τι κατειργάσατο· ἡ γὰρ εὔνοια σφων; '
                        'exclude the five smaller critical notes below.',
            'blank_gap': [0.75584, 0.76919]},
 (9, 223): {'y1': 0.72365,
            'evidence': 'Preserve the book80 contents and consular list as printed paratext plus all '
                        'full-size opening body through βλήθη, τότε μὲν μετὰ τὴν νίκην ἐς τε; exclude the '
                        'smaller consular-name variants below.',
            'blank_gap': [0.71865, 0.72866]},
 (9, 225): {'y1': 0.85265,
            'evidence': 'Preserve the full-size lacunose Greek body through κρίνου, ὃν πάμπολλα ἐπῄνεσαν, ἐν '
                        'πολέμῳ; exclude the smaller ἑαυτόν reading below.',
            'blank_gap': [0.84979, 0.85551]},
 (9, 228): {'y1': 0.73701,
            'evidence': 'Preserve the full-size body ending τε Παῖτος ὅτι εἰκόνας τινὰς ἑαυτοῦ ἐπιχρύσους; '
                        'exclude the smaller Ἀλβανούς and other critical notes below.',
            'blank_gap': [0.72961, 0.7444]},
 (9, 232): {'y1': 0.77492,
            'evidence': 'Preserve the full-size body ending λαβὼν μήτε τιμὴν ἀρχῆς, καὶ ὅτι τῷ ἐπικλίῳ; '
                        'exclude the smaller editorial/Greek critical notes below.',
            'blank_gap': [0.77062, 0.77921]},
 (9, 240): {'y1': 0.59466,
            'evidence': 'Preserve the full-size upper body through Xiphilinus352,14–18; exclude the '
                        'horizontal rule and route the full-size Leo/Cedrenus and Petrus Patricius '
                        'comparison panel below separately, rather than treating it as authorial body or '
                        'apparatus.',
            'blank_gap': [0.58989, 0.59943],
            'comparison_region': [0.095, 0.615, 0.43, 0.88]}}

OVERRIDES[(9, 242)] = {
    'y1': .91,
    'evidence': 'Full-page source inspection confirms all full-size Greek and Petrus Patricius credit paragraphs through 11,1 Ὡς δὲ ποτε καὶ ἀνελεῖν αὐτὸν ἐπεχείρησεν, remain main body. No Greek apparatus occurs before the printed page 474 footer.'
}

CONTACT_SHEETS = ['6f2a9c29f7d624176afd2e83fa0e39eb9f9acad667c963368fc18860a3ddd174',
 '1ec9fbf191c2bc9ff940994c5473248ef2347a921b6766b3831f35cecd309a89',
 'f1da530e614bf9669ad605b802e032d9ba6335df1c4e7e25e0b262903278469d',
 'd19db9ae78c5ba8b507cfa9f8acc61b3ec07b863a364098210eb5e30df32250b',
 '7e45705b8a5c15e79dc3de17dd66627ae0017ea1ac4ea4aa9d51d251ccbb05b3',
 'f597feb25011c08527a41cafa2c9714c58226711f4612d3b1e28d486c6f66059',
 'e202251850a97c5633e874dbf62e57b6e1e0992cb26d544fa0f95bca948b9c29',
 'd48e6adaca58a177ba4736f3914561f24adcc4f70a6f813c259a948ffa9be60f',
 'b5bc54d6ebd7f3f313417c267ed62f6ed9d6e3d75aeac01731ebd5d74786aed1',
 '76d17af672b1ea442f830ebe9ce610abe820d7e6e676f976b7b1a4d3927671a5',
 '395b137a8a46f8328025b67cf77462e76aba1b14781fa45080ae949f1b3f935d',
 'd46178d6c279ceced2b01ca0ef15142a3bba3aeb0cd4379e4a84d4c535651bee',
 '750a49d08c8a2c45e98a1bdce553032d8ce0e853eafb7b49c4a1dac237f59f24',
 '14863f8ed52a4a7a559642582fbf600ad1ad6d1e80411e9013781955eba7fe67',
 'f18a2bdcb669f4638acb8380594770e554b0ab804060664d99bdf43a11cbfcde',
 '046cf6dbd7c484e63e14c1df3545442834481e2d6e1af4bcc3a07a8b27443b9c']

FULL_PAGE_CHECKS = {(6, 246): 'Full-page inspection confirms the short final body and no Greek apparatus.',
 (7, 187): 'Full-page inspection identifies the high-on-page apparatus after the Joannes Antiochenus credit.',
 (8, 34): 'The short body and its high apparatus were inspected on the source page.',
 (8, 78): 'Full-page inspection confirms that the Petrus Patricius credit and following quotation are main '
          'body, with no Greek apparatus.',
 (8, 101): 'Full-page inspection places the long smaller Cf. Joannes Antiochenus comparison note after the '
           'short main body.',
 (8, 133): 'Full-page inspection confirms the short body through Xiph.201,18–202,26 R.St. and no Greek '
           'apparatus.',
 (8, 184): 'Full-page inspection identifies both high-on-page apparatus notes after Xiph.225,4–226,10 R.St.',
 (9, 9): 'Full-page inspection confirms no Greek apparatus; notes occur only on the facing English page.',
 (9, 39): 'Full-page inspection confirms no Greek apparatus; notes occur only on the facing English page.',
 (9, 105): 'Full-page inspection confirms no Greek apparatus.',
 (9, 123): 'Full-page inspection identifies one high-on-page Greek apparatus note after Xiph.313,21–314,13 '
           'R.St.',
 (9, 143): 'The short body and high apparatus boundary were inspected on the source page.',
 (9, 174): 'Full-page inspection identifies three high-on-page Greek apparatus notes after '
           'Exc.Val.396(p.757).',
 (9, 222): 'The short body and high apparatus boundary were inspected on the source page.',
 (9, 242): 'Full-page inspection confirms all full-size Greek and Petrus Patricius credit paragraphs remain '
           'main body; no Greek apparatus occurs.',
 (9, 248): 'Full-page inspection confirms no Greek apparatus.'}

