"""Occurrence review of the retained Schmidt 1867 column images.

These observations are inputs to the repair, not edits to generated corpus data.
TLG 4085.002 (Latte 1953/1966) was consulted on 2026-10-24 to locate and
interpret the entries. Every admitted reading is independently supported by
both retained Schmidt images. TLG is neither an extra OCR vote nor a replacement
edition. Its text is not copied into a new witness or public source export.
"""

TLG = {
    "work": "4085.002",
    "edition": "K. Latte, Hesychii Alexandrini lexicon, volumes 1–2, 1953/1966",
    "consulted_on": "2026-10-24",
    "url": "https://stephanus.tlg.uci.edu/Iris/indiv/browser.jsp#doc=tlg&aid=4085&wid=002",
    "role": "entry identification and comparison; Schmidt images control admission",
}

# position, corrected lexical reading (empty = merged fragment; None = held),
# printed entry, Latte alpha entry, source observation.
UNCERTAIN = {
    259: [
        (1, "ἀκριβής", "αὐθέκαστος", 8257, "Acute on eta, not circumflex."),
        (7, "τῷ", "αὐθέκαστος", 8257, "Omega with subscript in τῷ τρόπῳ."),
        (15, "αὐτῇ", "αὐθημερόν", 8263, "Smooth breathing on upsilon and circumflex eta with subscript."),
        (22, "αὐθιγενής", "αὐθιγενής", 8265, "Iota in the headword; only final eta is accented."),
        (24, "γνήσιος", "αὐθιγενής", 8265, "Acute on eta."),
        (26, "αὐθιγενές", "αὐθιγενές", 8266, "Iota and final accented epsilon."),
        (27, "ἐγγενές", "αὐθιγενές", 8266, "Double gamma; final accented epsilon."),
        (29, "", "αὐθίξας", 8268, "The spaced headword αὐ θίξας is one word. This extra αὐ slot is not another occurrence; retain the complete word at slot 30."),
        (30, "αὐθίξας", "αὐθίξας", 8268, "Printed xi, not zeta. Join the letterspaced headword once."),
        (36, "εὐθύς", "αὖθις", 8269, "Acute on upsilon before the printed period."),
        (42, "αὖτις", "αὖθις", 8269, "Tau, not theta; circumflex on upsilon."),
        (79, "ἄνευ", "αὐΐαχοι", 8275, "Smooth breathing and acute on initial alpha; final upsilon."),
        (82, "ἰαχῆς", "αὐΐαχοι", 8275, "Initial iota, not lambda."),
        (84, None, "αὐΐαχοι, second headword", 8275, "Letters are consistent with the comparison entry, but the breathing and marks over iota cannot be distinguished confidently in both scans. Preserve all original alternatives; do not import Latte's diacritics."),
        (85, "σιωπῇ", "αὐΐαχοι", 8275, "Circumflex eta with subscript."),
        (86, "ἄφοβοι", "αὐΐαχοι", 8275, "The definition has beta and the initial smooth breathing with acute."),
        (88, "αὐοὶ", "αὐΐαχοι", 8275, "Retain Schmidt's breathing on upsilon and final grave. Latte instead accents the upsilon; it does not authorize replacing this printed form."),
        (90, "ἀυϊδέτου", "ἀυϊδέτου", 8276, "Smooth breathing on alpha and diaeresis on iota; delta epsilon tau omicron upsilon."),
        (93, "ἀλκήν", "ἀ(υκ)άν", 8277, "The definition has kappa and acute on eta. The parenthesized headword remains excluded by the original source-role policy."),
        (94, "Κρῆτες", "ἀ(υκ)άν", 8277, "Circumflex on eta, final tau epsilon sigma."),
        (95, "αὐκήλως", "αὐκήλως", 8278, "Kappa, acute eta, lambda omega sigma. Schmidt has no dagger before this headword; Latte's dagger is not transferred."),
        (99, "αὐκυόνα", "αὐκυόνα", 8280, "Kappa upsilon omicron nu alpha, acute on omicron."),
        (100, "ἀλκυόνα", "αὐκυόνα", 8280, "The definition begins alpha lambda kappa; acute on omicron."),
        (101, "Κρῆτες", "αὐκυόνα", 8280, "Circumflex on eta."),
        (107, "διατρίβουσα", "αὐλαία", 8282, "Acute on iota in the definition."),
        (118, "σχίσμα", "αὖλαξ", 8284, "Iota, sigma, mu; not σχῆμα."),
        (121, "διῶρυξ", "αὖλαξ", 8284, "Both Schmidt copies show omega with circumflex. Latte has a different vowel and is retained only as a comparison reference."),
        (125, "οἰκοφύλαξ", "αὐλαρός", 8285, "Acute on upsilon; alpha before xi."),
        (127, "ἡ", "αὐλάχα", 8286, "Rough breathing, without grave accent, before ὕννις."),
    ],
    260: [
        (9, "σπεῖραν", "αὔληρον", 8290, "Schmidt prints sigma pi epsilon iota rho alpha nu with circumflex. Latte's σειράν is a different reading."),
        (14, "χόρτῳ", "αὐλῆς", 8291, "Omicron rho tau omega with subscript."),
        (20, "περιωρισμένῳ", "αὐλῆς", 8291, "Join the printed line break περιωρι- / σμένῳ; final omega with subscript."),
        (25, "σύγχορτα", "αὐλῆς", 8291, "Omicron rho tau alpha, not omega rho."),
        (49, "", "αὐλιζομενάων", 8301, "The line-end ἐλαυ- and following νομένων form one word. Remove this duplicate fragment and retain the joined word at slot 50."),
        (50, "ἐλαυνομένων", "αὐλιζομενάων", 8301, "Join ἐλαυ- / νομένων; genitive plural ending, not dative."),
        (52, "στασιάσαι", "αὐλίξαι", 8304, "Printed sigma alpha iota ending; acute on alpha."),
        (54, "Αὐλίς", "Αὐλίς", 8305, "Capital alpha, smooth breathing on upsilon, acute on iota."),
        (58, "δίδυμος", "Αὐλίς", 8305, "Acute on first iota."),
        (66, "ἐνώτια", "αὐλίσκοι", 8307, "Nu omega tau iota alpha with acute omega."),
        (72, "ἢ", "αὐλός", 8309, "Grave-accented disjunction before σῦριγξ."),
        (76, "ῥύσιν", "αὐλόν", 8310, "Initial rho with rough breathing, not phi."),
        (96, "αὐλῶνα", "αὐλῶνα", 8315, "Circumflex omega. Schmidt presents this as a separate headword; Latte combines its definition with αὐλῶνες."),
        (104, "αὐλῶνες", "αὐλῶνες", 8315, "Circumflex omega."),
        (118, "διάγουσα", "αὐλωνίζουσα", 8316, "Acute on alpha and gamma omicron upsilon sigma alpha."),
        (119, "αὐλώνων", "αὐλώνων", 8317, "Acute omega and nu omega nu. The line has only the Euripides reference; do not add a definition from another entry."),
    ],
}

# Agreement between checkpoints does not override legible contrary print.
SHARED_ERRORS = {
    259: [
        (13, "αὐθημερόν", "αὐθημερόν", 8263, "The headword's acute is on the final omicron."),
        (18, "αὖθι", "αὖθι", 8264, "Circumflex upsilon."),
        (32, "αὖθις", "αὖθις", 8269, "Circumflex upsilon."),
        (47, "αὖθι", "αὖθις", 8269, "Circumflex upsilon in the quoted form."),
        (57, "αὖθι", "αὖθις", 8269, "Circumflex upsilon in the first Homer quotation."),
        (67, "αὖθι", "αὖθις", 8269, "Circumflex upsilon in the second Homer quotation."),
        (78, "αὐΐαχοι", "αὐΐαχοι", 8275, "The headword has diaeresis and acute over iota."),
        (113, "αὔλακας", "αὔλακας", 8283, "Acute and smooth breathing on upsilon."),
        (116, "αὖλαξ", "αὖλαξ", 8284, "Circumflex upsilon."),
        (130, "ἡ", "αὐλεία", 8287, "The article has rough breathing without grave."),
    ],
    260: [
        (2, "αὔληρα", "αὔληρα", 8289, "Acute and smooth breathing on upsilon."),
        (4, "αὔληρον", "αὔληρον", 8290, "Acute and smooth breathing on upsilon."),
        (51, "αὐλίξαι", "αὐλίξαι", 8304, "The headword has xi, not zeta."),
        (65, "αὐλίσκοι", "αὐλίσκοι", 8307, "The headword has kappa, not chi."),
        (73, "σῦριγξ", "αὐλός", 8309, "Circumflex on upsilon."),
        (94, "ἔφυδρος", "αὐλών", 8314, "Initial epsilon has smooth breathing and acute."),
    ],
}
