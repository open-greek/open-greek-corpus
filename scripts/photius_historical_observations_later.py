"""Occurrence-scoped readings checked against the 1825 Bekker source scan.

These observations are inputs to a reversible correction layer. They do not
certify whole rows, resolve the page 280 reading order, or replace source
disagreements with a preferred digital spelling.
"""

from copy import deepcopy


SOURCE_SHA256 = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
SOURCE_LIBRARY_SHA256 = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
REVIEWED_AT = "2026-10-18"

# Rectangles use normalized coordinates of the original PDF page. Each
# rectangle contains the printed line or short passage named by an observation.
REGIONS = {
    "230-left-top": [0.07, 0.11, 0.435, 0.32],
    "230-left-middle": [0.07, 0.315, 0.435, 0.525],
    "230-left-bottom": [0.07, 0.52, 0.435, 0.742],
    "230-right-top": [0.435, 0.11, 0.80, 0.32],
    "230-right-middle": [0.435, 0.315, 0.80, 0.525],
    "230-right-bottom": [0.435, 0.52, 0.80, 0.742],
    "280-left": [0.04, 0.122, 0.413, 0.295],
    "280-right": [0.413, 0.122, 0.79, 0.295],
    "280-epilogue-top": [0.04, 0.292, 0.79, 0.365],
    "280-epilogue-bottom": [0.04, 0.36, 0.79, 0.443],
}

# page, row suffix, exact old substring, source reading, region, optional
# digital counterpart (for a printed word divided at a line boundary).
_SPECS = [
    (230, 1, "τῷ δακτυλίῳ", "τοῦ δακτυλίου", "230-left-top"),
    (230, 1, "ἔβω", "ἐβίω", "230-left-top"),
    (230, 1, "ἕτη", "ἔτη", "230-left-top"),
    (230, 1, "λέγουσι,", "λέγουσιν,", "230-left-top"),
    (230, 1, "ἔχει δὲ αὐτὸ εἰκῶν", "ἔστι δὲ αὐτοῦ εἰκὼν", "230-left-top"),
    (230, 1, "ἐν τῇ πρυτανείῳ", "ἐν τῷ πρυτανείῳ", "230-left-top"),
    (230, 1, "δημηγο-ρήσαι", "δημηγο-ρῆσαι", "230-left-top", "δημηγορῆσαι"),
    (230, 1, "λέγει κατὰ", "λέγεται κατὰ", "230-left-top"),
    (230, 1, "ὥστε τὸν ῥήτορα", "ὅτε τοὺς ῥήτορας", "230-left-top"),
    (230, 1, "Ἀθηρῶν", "Ἀθηνῶν", "230-left-top"),
    (230, 1, "χρόνῳ μετὰ ταῦτα ἑτέρων αἴτησιν", "χρόνῳ μέντοι ὕστερον σίτησιν", "230-left-top"),
    (230, 1, "ἐν τῇ πρυτανείῃ", "ἐν τῷ πρυτανείῳ", "230-left-top"),
    (230, 2, "Φίροσι δὲ αὐτὸ ἀποφθέγματα πλεῖοι", "Φέρονται δὲ αὐτοῦ ἀποφθέγματα πλεῖστα", "230-left-top"),
    (230, 2, "ἀναγκάσ-σαν", "ἀνακύπτου-σαν", "230-left-top", "ἀνακύπτουσαν"),
    (230, 2, "ἀπροστίμενος", "ἁρμοττόμενος", "230-left-top"),
    (230, 2, "διασώζοντο", "διεσώσαντο", "230-left-middle"),
    (230, 2, "κυκλοφόρος ἐν 15Ἀθήναις", "κωλυόμενος ὑπὸ Ἀθηναίων", "230-left-middle"),
    (230, 2, "ἐν ἐκκλησίᾳ λέγων", "ἐν ἐκκλησίᾳ λέγειν", "230-left-middle"),
    (230, 2, "ἦρη βούλεσθαι", "ἔφη βούλεσθαι", "230-left-middle"),
    (230, 2, "δεξιομένων", "δεξαμένων", "230-left-middle"),
    (230, 2, "ναυ-νίας", "νεα-νίας", "230-left-middle", "νεανίας"),
    (230, 2, "ὦρα θέρους", "ὥρᾳ θέρους", "230-left-middle"),
    (230, 2, "ἐξ ἀέρος ὕδωρ ἐπιφύ-σατο", "ἐξ ἄστεος ὄνον ἐμισθώ-σατο", "230-left-middle", "ἐξ ἄστεος ὄνον ἐμισθώσατο"),
    (230, 2, "Μέγαράδι", "Μέγαράδε", "230-left-middle"),
    (230, 2, "τῆς χειρὸς", "τῆς ἡμέρας", "230-left-middle"),
    (230, 2, "πλεῖον ἀνατομῆτος", "πλέον ἀναπτομένης", "230-left-middle"),
    (230, 2, "τὴν τὸ ὕδωρ γενῆς σχῆμα", "τὴν τοῦ ὄνου γενέσθαι σκιάν", "230-left-middle"),
    (230, 2, "μεμι-θωκέναι τὸν ὕδωρ", "μεμι-σθωκέναι τὸν ὄνον", "230-left-middle", "μεμισθωκέναι τὸν ὄνον"),
    (230, 2, "τὸ δὲ μεμιθωμέ-νος", "ὁ δὲ μεμισθωμέ-νος", "230-left-middle", "ὁ δὲ μεμισθωμένος"),
    (230, 2, "ἵνως ἂν αὐτὸν χείρων τῷ σώματι", "ἕως ἂν αὐτὸν κύριον τοῦ σώματος", "230-left-middle"),
    (230, 2, "τὸ μῖθωμα", "τὸ μίσθωμα", "230-left-middle"),
    (230, 2, "τὴν ἄλλην ἔχων", "τὴν ἄλλην ἔχειν", "230-left-middle"),
    (230, 2, "ὑπὲρ 25δοχῶν", "ἀπῄει, ὀργώσας", "230-left-middle"),
    (230, 2, "τὰς ἀκὰς", "τὰς ἀκοὰς", "230-left-middle"),
    (230, 2, "τὴν τῶν λοχῶν δεῖ-1490χτον ἀπολίσσει", "τὴν τῶν λοιπῶν διή-γησιν ἀπολιπών", "230-left-middle", "τὴν τῶν λοιπῶν διήγησιν ἀπολιπών"),
    (230, 2, "ἐπιθύναι τῇ λόγῳ δεομένῳ", "ἐπιθεῖναι τῷ λόγῳ δεομένων", "230-left-middle"),
    (230, 2, "εἶνα", "εἶτα", "230-left-middle"),
    (230, 2, "ἵνερ μὲν ὕδωρ σκιάς βούλεσθαι", "ὑπὲρ μὲν ὄνου σκιᾶς βούλεσθε", "230-left-middle"),
    (230, 2, "ἵνερ δὲ σπου-δαίων", "ὑπὲρ δὲ σπου-δαίων", "230-left-middle", "ὑπὲρ δὲ σπουδαίων"),
    (230, 2, "ὀβούλεσθι", "οὐ βούλεσθε", "230-left-bottom"),
    (230, 3, "Βύταλον δὲ ὄνομα ἦσαν", "Βάταλον δὲ ὀνομασθῆναί", "230-left-bottom"),
    (230, 3, "νῦν ὡν", "νέος ὢν", "230-left-bottom"),
    (230, 3, "κομίζων γυναικίοις ἐλήμασιν ἀπεκέρχτο", "κωμάζων γυναικείοις ἐσθήμασιν ἀπεκέχρητο", "230-left-bottom"),
    (230, 3, "ὑποκορισκῶς", "ὑποκοριστικῶς", "230-left-bottom"),
    (230, 3, "τῦτο", "τοῦτο", "230-left-bottom"),
    (230, 3, "τῆς τροφῆς", "τῆς τροφοῦ", "230-left-bottom"),
    (230, 3, "λουδορούμενοι", "λοιδορούμενοι", "230-left-bottom"),
    (230, 3, "ὡς καὶ Λιβάνιος", "οἷς καὶ Λιβάνιος", "230-left-bottom"),
    (230, 4, "νὸς “ὡν ὁδινῶς", "νέος ὢν ἀσθενῶς", "230-left-bottom"),
    (230, 4, "φυσώδης", "νοσώδης", "230-left-bottom"),
    (230, 4, "φροντὶν εἰς παλαιμάχων", "φοιτᾶν εἰς παλαίστραν", "230-left-bottom"),
    (230, 4, "ἀνδράθεις εἰς μιλαχίαν", "ἀνδρωθεὶς εἰς μαλακίαν", "230-left-bottom"),
    (230, 4, "ἑχθρῶν ἐσκιώπετο", "ἐχθρῶν ἐσκώπτετο", "230-left-bottom"),
    (230, 4, "Βύταλος ἐπωνομάζετο", "Βάταλος ἐπωνομάζετο", "230-left-bottom"),
    (230, 4, "ἰσθρὴ γὰρ", "ἱστορεῖται γάρ", "230-left-bottom"),
    (230, 4, "Βύταλος αὐλῆ-40τῆς γένεσις", "Βάταλος αὐλη-τὴς γενέσθαι", "230-left-bottom", "Βάταλος αὐλητὴς γενέσθαι"),
    (230, 4, "ὑποδύμασι γυναικίοις", "ὑποδήμασι γυναικείοις", "230-left-bottom"),
    (230, 4, "μιλοῖς καταγνῶσι", "μέλεσι κατεαγόσι", "230-left-bottom"),
    (230, 4, "ἐκλέτους καὶ ἀνύδρους", "ἐκλύτους καὶ ἀνάνδρους", "230-left-bottom"),
    (230, 4, "Βυτάλεις ἐπωνομάζαν", "Βατάλους ἐπονομάζουσιν", "230-left-bottom"),
    (230, 5, "Ἀντιγόνῳσ᾽ΥΠΕΡΕΙΔΟΥ", "Ἀνεγνώσθησαν ΥΠΕΡΕΙΔΟΥ", "230-right-top"),
    (230, 5, "τῶν οἱ μὲν", "τούτων οἱ μὲν", "230-right-top"),
    (230, 5, "τῷ ὁμήρῳ ἀναφερόμενοι γνήσιον", "τοῦ ῥήτορος ἀναφερόμενοι γνήσιοι", "230-right-top"),
    (230, 5, "παραχόντες", "παρασχόντες", "230-right-top"),
    (230, 5, "τὸ γὰρ ὅλον", "τὸ δὲ ὅλον", "230-right-top"),
    (230, 5, "ἰσχυαίαις", "ἐργασίαις", "230-right-top"),
    (230, 5, "τινὲς μὲν ἀμφισβήτησον παραχεῖν", "τισὶ μὲν ἀμφισβήτησιν παρασχεῖν", "230-right-top"),
    (230, 5, "ὁ Ἀριστοτέλης κατὰ", "ὁ Δημοσθένης κατὰ", "230-right-top"),
    (230, 5, "ἐκεῖνα προῆλθε", "ἐκείνῳ προέχει", "230-right-top"),
    (230, 5, "Ἀριστοτέλης ὁ Ὑπερείδης", "Δημοσθένης ὁ Ὑπερείδης", "230-right-top"),
    (230, 5, "εἰσὶ δὲ οἱ", "εἰσὶ δὲ οἳ", "230-right-top"),
    (230, 5, "ἔδοντο ψῆφον Ὑπερείδη", "ἔθεντο ψῆφον Ὑπερείδῃ", "230-right-top"),
    (230, 5, "ἐγγραφάφωσι", "ἐγγράφουσι", "230-right-top"),
    (230, 5, "τῇ τῷ Ἀριστοτέλει στήλῃ", "τῇ τοῦ Δημοσθένους στήλῃ", "230-right-top"),
    (230, 6, "ἰσχν γνώμῃ φώμηρ", "ἴσην γνώμῃ ῥώμην", "230-right-top"),
    (230, 6, "ἔχει", "εἶχεν", "230-right-top"),
    (230, 7, "δ ποτ'", "οὔ ποτ’", "230-right-top"),
    (230, 8, "Οὕτος", "Οὗτος", "230-right-middle"),
    (230, 8, "τοῦ Λαυρεοῦ", "τοῦ Διονυσίου", "230-right-middle"),
    (230, 8, "Κολλενεὺς δὲ τῶν δήμων", "Κολλυτεὺς δὲ τὸν δῆμον", "230-right-middle"),
    (230, 8, "ἔχει δὲ", "ἔσχε δὲ", "230-right-middle"),
    (230, 8, "Γλαύκιππον ὁμήτορα", "Γλαύκιππον ῥήτορα", "230-right-middle"),
    (230, 8, "δς κ λόγους συντεγράψατο", "ὃς καὶ λόγους συνεγράψατο", "230-right-middle"),
    (230, 8, "τῷ φιλοσόφῳ ἠκολούθησε", "τοῦ φιλοσόφου ἠκροάσατο", "230-right-middle"),
    (230, 8, "διὰ καὶ Ἰσοκράτους", "δὴ καὶ Ἰσοκράτους", "230-right-middle"),
    (230, 8, "ἐπολιτεύσατο δὲ Ἀθηνῶν", "ἐπολιτεύσατο δὲ Ἀθήνησιν", "230-right-middle"),
    (230, 8, "ἐπιτετο προσηγάμων", "ἥπτετο πραγμάτων", "230-right-middle"),
    (230, 8, "δείκνυθ' ἀντίπαλον αὐτῷ", "δείκνυται ἀντειπὼν αὐτοῦ", "230-right-middle"),
    (230, 8, "ἧτις τοὺς ἐραστὴς τῶν Ἀθηναίων χείρους κ τῶν τραφῶν ἀπῆλθε", "ἥτις τοὺς στρατηγοὺς τῶν Ἀθηναίων καὶ τὰς τριήρεις ἀπῄτει", "230-right-middle"),
    (230, 8, "συνέβαλλε", "συνεβούλευσε", "230-right-middle"),
    (230, 8, "Ταινάρῳ", "Ταίναρον", "230-right-middle"),
    (230, 8, "διαλύσαι", "διαλῦσαι", "230-right-middle"),
    (230, 8, "Ἀριστοτέλει τιμᾶς", "Δημοσθένει τιμάς", "230-right-middle"),
    (230, 8, "τοῦ Λυσίου", "τοῦ Διοδότου", "230-right-middle"),
    (230, 8, "τῷ ψηφίσματος ἀπήγγει", "τὸ ψήφισμα ἀπέφυγε", "230-right-middle"),
    (230, 8, "περὶ Ἀριστοτέλη", "περὶ Δημοσθένην", "230-right-middle"),
    (230, 8, "Λυκούργου χείρους", "Λυκοῦργον γεγονὼς", "230-right-middle"),
    (230, 8, "συνέτηρῶν", "συνετήρησεν", "230-right-middle"),
    (230, 8, "ἀλλ' ὅπερ", "ἀλλ’ ἐπεὶ", "230-right-middle"),
    (230, 8, "Λυκούργου ὁ βίος ἀπέλειπε", "Λυκοῦργον ὁ βίος ἀπέλιπε", "230-right-middle"),
    (230, 8, "Ἀριστοτέλης δὲ εἰς κρύψιν ἦλθεν", "Δημοσθένης δὲ εἰς κρίσιν ἤγετο", "230-right-bottom"),
    (230, 8, "Ἀρσάλου δωροδοκοῦντος", "Ἁρπάλου δωροδοκήσας", "230-right-bottom"),
    (230, 8, "ἐξ ἀπάντων", "ἐξ ἁπάντων", "230-right-bottom"),
    (230, 8, "προεχειρί.θῃ τῷ ὁμήρῳ", "προεχειρίσθη τοῦ ῥήτορος", "230-right-bottom"),
    (230, 8, "κριταὶ", "κριθεὶς", "230-right-bottom"),
    (230, 8, "τοῦ Ἀριστοτέλους", "τοῦ Ἀριστογείτονος", "230-right-bottom"),
    (230, 8, "Λαϊωρίαν", "Χαιρώνειαν", "230-right-bottom"),
    (230, 8, "τὰς μετοίκους πόλεις ἐγνώμη ποιήσας", "τοὺς μετοίκους πολίτας ἔγραψε ποιήσασθαι", "230-right-bottom"),
    (230, 8, "ἐλευθέρους δὲ τὰς δούλας", "ἐλευθέρους δὲ τοὺς δούλους", "230-right-bottom"),
    (230, 8, "Πειραιῶν παραβληκ", "Πειραιᾶ παραθέσθαι", "230-right-bottom"),
    (230, 8, "κίντῶθα", "κἀνταῦθα", "230-right-bottom"),
    (230, 8, "τῷ δύναι", "τοῦ δοῦναι", "230-right-bottom"),
    (230, 8, "αὐτὸν ὡς ὁλίγων", "αὐτὸν οὐκ ὀλίγων", "230-right-bottom"),
    (230, 8, "ἀπισκᾶτι", "ἐπεσκότει", "230-right-bottom"),
    (230, 8, "ἐγνώμη", "ἔγραψε", "230-right-bottom"),
    (230, 8, "μέπω", "μήπω", "230-right-bottom"),
    (230, 8, "αἱρεῖς Ἀθηναίους μυθο", "αἱρεθεὶς Ἀθηναίοις μισθοῦ", "230-right-bottom"),
    (230, 8, "δόξασδὸς", "δόξας", "230-right-bottom"),
    (230, 8, "Πειραιῶν μετεχενάσαι", "Περσικῶν μετεσχηκέναι", "230-right-bottom"),
    (230, 8, "Ἐφιάλτης", "Ἐφιάλτῃ", "230-right-bottom"),
    (230, 8, "τριήραχος", "τριήραρχος", "230-right-bottom"),
    (280, 1, "δεῖα ἐμπνεῦσαι", "θείᾳ ἐμπνεύσει", "280-left"),
    (280, 2, "ἀνάζιον", "ἀνάξιον", "280-left"),
    (280, 3, "διοφῶντα", "διορῶντα", "280-left"),
    (280, 6, "νομοθεσίαν", "νομισθεῖσαν", "280-left"),
    (280, 7, "ἁμαρτημάτων", "ἡμαρτηκότων", "280-left"),
    (280, 7, "μετανοήσας", "μετανοοῦντας", "280-left"),
    (280, 8, "σπλαγχνικῶς πατρικῶς", "σπλάγχνοις πατρικοῖς", "280-left"),
    (280, 9, "τῦτο ἔκινος", "τοῦτο ἐκεῖνος", "280-left"),
    (280, 10, "ἐξήγαγε", "ἐῤῥάγη τε", "280-left"),
    (280, 11, "καθαρῶς", "καθαρὸς", "280-left"),
    (280, 12, "ὀνομάζας", "ὀνομάσας", "280-left"),
    (280, 24, "βεβλεψαμένους φιλαρχίας", "βδελυξαμένους φιλαρχίαν", "280-right"),
    (280, 24, "μετανοούντων ἀπόνους", "μετανοοῦντων ἀπόνοιαν", "280-right"),
    (280, 24, "καλλεικὴ μαρτυρία τίμι", "καλλινίκῳ μαρτυρίᾳ τέλει", "280-right"),
    (280, 25, "ὁ ἄνθρω", "ὁ ἀνὴρ", "280-right"),
    (280, 25, "ἡ συγγραφή", "ἢ συγγραφῇ", "280-right"),
    (280, 25, "σόλοιχα", "σόλοικα", "280-right"),
    (280, 25, "ὑποβάθραρα", "ὑποβάρβαρα", "280-right"),
    (280, 25, "γράψιν", "γράφειν", "280-right"),
    (280, 25, "παραλείπεται", "παραιτεῖται", "280-right"),
    (280, 25, "τοιαύτη φράσει", "τοιαύτῃ φράσει", "280-right"),
]

# Occurrences are zero-based within the entire pinned Source Library section.
# These choices follow the source passage, rather than the first matching word.
_DIGITAL_OCCURRENCES = {
    (230, 1, "ἕτη"): 0,
    (230, 1, "ἐν τῇ πρυτανείῳ"): 0,
    (230, 1, "ἐν τῇ πρυτανείῃ"): 1,
    (230, 2, "εἶνα"): 0,
    (230, 3, "νῦν ὡν"): 0,
    (230, 3, "τῦτο"): 0,
    (230, 8, "ἐγνώμη"): 2,
}

_OLD_OCCURRENCES = {(230, 8, "ἐγνώμη"): 1}


def observations():
    """Return independent occurrence records; no source or corpus I/O occurs."""
    out = []
    for i, spec in enumerate(_SPECS):
        page, row, before, after, region, *digital = spec
        record = {
            "page": page,
            "locus": f"helladius_chrestomathia_photius_bekker_v2_{page:04d}.{row}",
            "original_text": before,
            "corrected_text": after,
            "source_region": deepcopy(REGIONS[region]),
            "evidence": (
                f"Direct inspection of Bekker physical PDF page {page}, printed "
                f"page {page + 265}, {region.split('-', 1)[1]}: the printed "
                f"passage reads {after!r}. This is an occurrence observation, "
                "not certification of the surrounding row."
            ),
            "digital_section": f"tlg4040-tlg001-local002-s{page + 277}",
            "digital_text": digital[0] if digital else after,
            "observation_id": f"bekker-historical-{page:04d}-{i:03d}",
        }
        if (page, row, before) in _DIGITAL_OCCURRENCES:
            record["digital_occurrence"] = _DIGITAL_OCCURRENCES[page, row, before]
        if (page, row, before) in _OLD_OCCURRENCES:
            record["occurrence"] = _OLD_OCCURRENCES[page, row, before]
        out.append(record)
    return out


def scan_only_observations():
    """Two scan readings corroborated by the pinned fresh diagnostic strip.

    Section s446 is unrelated to the original PDF page 169. It is deliberately
    not cited as a counterpart for these observations.
    """
    common = {
        "page": 169,
        "locus": "helladius_chrestomathia_photius_bekker_v2_0169.1",
        "diagnostic_id": "photius-historical-0169-left-upper",
        "diagnostic_file": "data/evaluation/ocr-fresh/photius-historical-reading-diagnostics-qwen38-mlx.jsonl",
        "diagnostic_file_sha256": "94e786f11798760bab01af7ab71dfa7c0c913017064a866da8f0139f161318b6",
        "diagnostic_record_sha256": "e614c87211a9957c5b67455e5861c55411749e1f080195dd7e056b046ac18189",
        "diagnostic_text_sha256": "a902f911bb7538d0c896ce1bd81d470d0af4cf34a4d81f42f9576cd8511648f7",
        "diagnostic_image_sha256": "9db224463449c8d9b8733bbec38773a6e0bf82e69d628db8c0d2bc23407288b6",
    }
    out = []
    for old, new, region in [
        ("ἀμείπτος", "ἄμεμπτος", [0.234, 0.111, 0.582, 0.136]),
        ("τῶν ἡμιόχων", "τῶν ἡνιόχων", [0.234, 0.179, 0.582, 0.205]),
    ]:
        out.append({
            **common,
            "original_text": old,
            "corrected_text": new,
            "diagnostic_text": new,
            "source_region": region,
            "evidence": (
                "Direct inspection of original Bekker PDF page 169, printed "
                f"page 434, reads {new!r}; the fresh scan-only Qwen3.8 upper-left "
                "diagnostic independently has the exact same substring. The "
                "rest of that diagnostic is not certified. Source Library s446 "
                "contains a different printed page and is not a voting source."
            ),
        })
    return out


_EPILOGUE_SCAN_LINES = [
    "Ἅ μὲν ἐν φιλολογουμένοις ἡμῖν καθ’ ἑαυτοὺς εἰς ἀνάμνησιν ἐλθεῖν συνηνέχθη, χωρὶς ὧν ἡ σπουδὴ ϗ με-",
    "λέτη τέχνας φιλεῖ ϗ ἐπιστήμας ἐργάζεσθαι, ἀφ’ οὗ πέρ τις αἴσθησις ἡμῖν ἀμηγέπη ϗ κρίσις λόγων ἀνεφύη μέ-",
    "χρι τῆς παρούσης τῶν ἀνεγνωσμένων ὡς ἐν τύπῳ συνεκδόσεως, εἰς τοσοῦτον οἶμαι συναγεῖν πλῆθος, τριακο-",
    "σιοστῷ ϗ πεντεκαιδεκάτῳ μέρει προελθεῖν ἄχρι τῶν τριακοσίων κυλινδόμενον. σὺ δ’ ὦ τῶν ἐμοὶ κεκοινωνη-",
    "κότων μητρικῶν ὠδίνων ἐρασμιώτατε, εἰ μὲν ταύτην τὴν πρεσβείαν διανοῦντα τὸ κοινὸν ϗ ἀνθρώπινον κα-",
    "ταλάβοι τέλος, ἔχεις τὴν αἴτησιν τῆς ἐλπίδος οὐ διαμαρτῦσαν, φιλίας τε ἅμα ϗ παραμυθίας ὑπόθεσιν καὶ",
    "ἀνάμνησιν, ϗ δὴ ϗ ἀπαρχὴν ϗ τελευτὴν ἀφοσιωμένην τῶν σῶν κατὰ λογικὴν θεωρίαν αἰτήσεων τὴν ἐκπλή-",
    "ρωσιν. εἰ δ’ ἐκεῖθεν ἡμᾶς ἀνασωσάμενον τὸ θεῖόν τε καὶ φιλάνθρωπον νεῦμα εἰς τὴν ἀλλήλων θέαν καὶ",
    "προτέραν ἀπόλαυσιν ἀποκαταστήσει, τάχα ἂν ἑτέρων ἐκδόσεων ἐκ ἐλαττόνων ἀρχῇ ταῦτα εἴη, παραπλησίῳ",
    "τύπῳ παρεχομένων σοι τὴν ὠφέλειαν.",
    "Τέλος ϗ τῷ θεῷ τῷ πανοικτίρμονι δόξα εἰς αἰῶνας αἰώνων. Ἀμήν.",
]

_EPILOGUE_DIGITAL = (
    "Ἅ μὲν ἐν φιλολογουμένοις ἡμῖν καθ᾽ ἑαυτὲς εἰς ἀνάμνησιν ἐλθεῖν συνηνέχθη, χωρὶς ὧν ἡ σπεδὴ κὲ μελέτῃ τέχνας φιλεῖ ἐ ἐπισήμας ἐργάζεσθαι, ἀφ᾽ ἑ πέρ τις αἴθησις ἡμῖν ἀμηγέπη κ κρίσις λόγων ἀνεφύη μέχρι τῆς παρέσης τῶν ἀνεγνωσμένων ὡς ἐν τύπῳ συνεκδόσεως, εἰς τοσῆτον οἶμαι συνάγειν πλῆθος, τριακοσιοζῷ κὲ πεντεκαιδεκάτῳ μέρει προελθεῖν ἄχρι τῶν τριακοσίων κωλυόμενον. σὺ δ᾽ ὦ τῶν ἐμοὶ κεκοινωνηκότων μητρικῶν ὠδίνων ἐρασμιώτατε, εἰ μὲν ταύτην τὴν πρεσβείαν διανοοῦντα τὸ κοινὸν κ ἀνθρώπινον καταλάβοι τέλος, ἔχεις τὴν αἴτησιν τῆς ἐλπίδος ἐ διαμαρτῦσαν, φιλίας τε ὕμα κὲ παραμυθίας ὑπόθεσιν κὲ ἀνάμνησιν, κὲ δὴ κὲ ἀπαρχὴν κὲ τελευτὴν ἀφοσιωμένην τῶν σῶν κατὰ λογικὴν θεωρίαν αἰτήσεων τὴν ἐκπλήρωσιν. εἰ δ᾽ ἐκεῖθεν ἡμᾶς ἀνασωσάμενον τὸ θεῖόν τε καὶ φιλάνθρωπον νεῦμα εἰς τὴν ἀλλήλων θέαν καὶ προτέραν ἀπόλαυσιν ἀποκαταστήσει, τάχα ἂν ἑτέρων ἐκδόσεων ἐκ ἐλαττὸνων ἀρχῇ ταῦτα εἴη, παραπλησίῳ τύπῳ παρεχομένων σοι τὴν ὠφέλειαν. Τέλος κὲ τῷ θεῷ τῷ πανοικτίρμονι δόξα εἰς αἰῶνας αἰώνων. Ἀμήν."
)


def epilogue():
    """Return the complete bounded reading-order repair proposal for review."""
    return {
        "page": 280,
        "locus": "photius_bekker1825_0280.epilogue",
        "replaces": [
            f"helladius_chrestomathia_photius_bekker_v2_0280.{n}"
            for n in [*range(13, 24), 26, 27]
        ],
        "insert_after": "helladius_chrestomathia_photius_bekker_v2_0280.25",
        "source_region": [0.06, 0.296, 0.79, 0.453],
        "scan_text": "\n".join(_EPILOGUE_SCAN_LINES),
        "digital_section": "tlg4040-tlg001-local002-s557",
        "digital_text": _EPILOGUE_DIGITAL,
        "transcription_convention": (
            "Preserve the eleven physical lines, including printed terminal "
            "hyphens, without completing a word beyond this bounded passage. "
            "Record the printed conjunction ligature as ϗ; expand ordinary ου "
            "and στ typographic ligatures into their constituent letters. "
            "Do not modernize punctuation or change the digital witness. "
            "Two independent inspections support compact διανοῦντα; retain "
            "its disagreement with digital διανοοῦντα as an unresolved reading, "
            "without selecting either spelling from contextual grammar. "
            "The printed marginal references 1623R., 15, and 20 are outside "
            "the authored reading and are not transcribed as words."
        ),
        "evidence": (
            "Source PDF page 280 (printed 545) has two short columns ending "
            "with Εὐλόγιος / ἐνεργάσασθαι, followed by ten full-width epilogue "
            "lines and a centered closing formula. Historical rows13–22 retain "
            "the left portions; row26 concatenates detached right portions; "
            "rows23/27 split the closing formula. Preserve all thirteen exact "
            "old row dictionaries as nonvoting preimages and alias their loci "
            "to this one physical region. Rows24/25 are preceding right-column "
            "body and remain outside the replacement. Both complete manual "
            "and digital readings must remain independent witnesses with all "
            "disagreements retained. The footer apparatus begins below the "
            "closing formula and is outside this source region."
        ),
        "source_uncertainties": [{
            "text": "διανοῦντα",
            "source_region": [0.42, 0.35, 0.605, 0.371],
            "evidence": (
                "Two independent source inspections read compact διανοῦντα "
                "after πρεσβείαν and cannot verify an additional ο. Preserve "
                "manual διανοῦντα versus SL διανοοῦντα as unresolved; neither "
                "reading is authorized as an ordinary certain token."
            ),
        }],
    }


def unapplied_source_observations():
    """Retain source evidence without authorizing an occurrence correction."""
    return [{
        "page": 169,
        "locus": "helladius_chrestomathia_photius_bekker_v2_0169.1",
        "original_text": "ἀνάπνοις",
        "corrected_text": "ἀνάπαυσις",
        "source_region": [0.234, 0.151, 0.582, 0.178],
        "evidence": (
            "The fourth source line clearly prints ἀνάπαυσις. Source Library "
            "s446 is unrelated; fresh diagnostic also corrupts this word. "
            "This observation does not authorize a scalar correction; the "
            "independent comparison readings remain different."
        ),
    }]


REVIEW_SCOPE = {
    "pages": [169, 230, 280],
    "source_pages_visually_inspected": [169, 230, 280],
    "page_169_detail": "Upper-left diagnostic region; full-page mapping/layout checked.",
    "page_230_detail": "Both body columns inspected in six overlapping enlarged crops.",
    "page_280_detail": "Both short columns, complete full-width epilogue, and closing formula.",
    "certification": "Individual reported occurrences and bounded epilogue only; not whole historical rows.",
    "mapping_exception": "Original PDF169 does not match SLs446; no SL authority is asserted for169.",
}
