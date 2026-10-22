"""Source-reviewed spellings for six pages of the published Herodas excerpt.

Every existing locus is accounted for, including unchanged text. Speaker labels
and source headings remain excluded. Corrections refer to the pinned printing,
not a normalized Greek text or another edition. Uncertain source glyphs retain
explicit alternatives at offsets in corrected_text.
"""
from __future__ import annotations

SOURCE_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
REVIEWED_AT = "2026-10-22T19:19:17Z"
PAGES = (290, 292, 294, 344, 346, 472)
ORIGINAL_IMAGE_SHA256 = {
    290: "a44cfe96803fd189570c5668d43ada8a817517d45e5f1d34c14753c03322f343",
    292: "21284fa84dd4cd777ee764a687b8282d38d120d8add957b038b35e1a79f30802",
    294: "1338a25b7d99294668158c9b333a3c327d79e2696a2b36954394b338b3c857af",
    344: "e614feb3e3218357d68db5834eeeccb2922d473f35fdf2e662ea349d4669c023",
    346: "d0713eeec8f68eed315ac00aa20e9b3c6123c4c39c8a9c3ac4cb89dd2d43a8bc",
    472: "041b764609dc07058b3f3158e309ccf65f171dc2b169d90cb08cb08fb7e2129f",
}

_ORIGINALS = {
    "herodas_hk_0290.2": "Λέγε μοι σύ, Γάστρων, εἶ δ’ ὑπερκορὴς οὕτω, ὥστ’ οὐκέτ’ ἀρκεῖ τἀμά σοι σκέλεα κινεῖν ἀλλ’ Ἀμφυταίῃ τῇ Μένωνος ἔγκεισαι;",
    "herodas_hk_0290.4": "ἐγὼ Ἀμφυταίῃ; τὴν λέγεις ὀρώρηκα γυναῖκα;",
    "herodas_hk_0290.5": "προφάσεις πᾶσαν ἡμέρην ἕλκεις.",
    "herodas_hk_0290.7": "Βίτιννα, δοῦλός εἰμι· χρῶ ὅτι βούλει μοι καὶ μὴ τό μεν αἷμα νύκτα κήμέρην πῖνε.",
    "herodas_hk_0290.8": "ὅσην δὲ καὶ τὴν γλάσσαν, οὗτος, ἔσχηκας· Κύδιλλα, κοῦ ὅστις Πυρρίης; κάλει μ’ αὐτόν.",
    "herodas_hk_0290.10": "τί ἐστί;",
    "herodas_hk_0290.11": "τοῦτον δῆσον—ἀλλ’ ἔθ’ ἕστηκας;— τὴν ἐμανήθρην τοῦ κάδου ταχέως λύσας. ἦν μὴ καταικίσασα τῇ σ’ ὅλῃ χώρῃ παράδειγμα θῶ, μὰ, μή με θῇς γυναῖκ’ εἶναι. ἦρ’ οὐχὶ μᾶλλον Φρύξ; ἐγὼ αἰτίη τούτων ἐγῷμι, Γάστρων, ἥ σε θεῖσ’ ἐν ἀνθρώποις. ἀλλ’ εἰ τότ’ ἐξήμαρτον, οὐ τὰ νῦν εἶναι μῶρον Βίτινναν, ὡς δοκεῖς, ἔθ’ εὑρήσεις. φέρ’, εἰς σύ, δῆσον, τὴν ἀπληγίδ’ ἐκδύσας.",
    "herodas_hk_0292.3": "μὴ μή, Βίτιννα, τῶν σε γουνάτων δεῦμαι.",
    "herodas_hk_0292.5": "ἔκδυθι, φημί. δεῖ σ’ ὁτεύνεκ’ εἶ δοῦλος καὶ τρεῖς ὑπέρ σευ μνᾶς ἔθηκα γινώσκειν. ὡς μὴ καλῶς γένοιτο τἡμέρη κείνῃ, ἥτις σ’ ἐσήγαγ’ ὧδε. Πυρρίη, κλαύσῃ· ὁρῶ σε δήκου πάντα μᾶλλον ἢ δεῦντα. σύσφιγγε τοὺς ἀγκῶνας, ἔκπρισον δήσας.",
    "herodas_hk_0292.7": "Βίτιννα, ἄφες μοι τὴν ἁμαρτίαν ταύτην. ἄνθρωπός εἰμι, ἥμαρτον· ἀλλ’ ἐπὴν αὖτις ἔλῃς τι δρῶντα τῶν σὺ μὴ θέλῃς, στίξον.",
    "herodas_hk_0292.9": "πρὸς Ἀμφυταίην ταῦτα, μὴ μὲ πληκτίζευ, μεθ’ ἧς ἀλινδῇ καὶ ἐμὲ φὴς ποδόψηστρον.",
    "herodas_hk_0292.11": "δέδεται καλῶς σοι.",
    "herodas_hk_0292.13": "μὴ λάθῃ λυθεὶς σκέψαι. ἄγ’ αὐτὸν ἐς τὸ ζήτρειον πρὸς Ἕρμωνα καὶ χιλίας μὲν ἐς τὸ νῶτον ἐγκόψαι αὐτῷ κέλευσον χιλίας δὲ τῇ γαστρί.",
    "herodas_hk_0292.15": "ἀποκτενεῖς, Βίτιννα, μ’ οὐδ’ ἐλέγξασα εἶτ’ ἔστ’ ἀληθέα πρῶτον εἴτε καὶ ψευδέα;",
    "herodas_hk_0292.17": "ἃ δ’ αὐτὸς εἶπας ἄρτι τῇ ἰδίῃ γλάσσῃ ‘Βίτινν’, ἄφες μοι τὴν ἁμαρτίαν ταύτην’;",
    "herodas_hk_0292.19": "τήν σευ χολὴν γὰρ ἤθελον κατασβέσσαι.",
    "herodas_hk_0292.21": "ἔστηκας ἐμβλέπων σύ, κοὐκ ἄγεις αὐτόν ὅκου λέγω σοι; θλῆ, Κύδιλλα, τὸ ῥύγχος",
    "herodas_hk_0294.1": "τοῦ παντοέρκτεω τοῦδε, καὶ σύ μοι, Δρήχων, ἤδη ‘φαμάρτει τῇ σ’ ἂν οὗτος ἡγῆται. δώσεις τι, δούλη, τῷ κατηρήτῳ τούτῳ ῥάκος καλύψαι τὴν ἀνώνυμον κέρκον, ὡς μὴ δι’ ἀγορῆς γυμνὸς ὢν θεωρῆται; τὸ δεύτερόν σοι, Πυρρίη, πάλιν φωνέω, ὅκως ἐρεῖς Ἕρμωνι χιλίας ὧδε, καὶ χιλίας ὧδ’ ἐμβαλεῖν· ἀκήκοας; ὡς, ἤν τι τούτων ὧν λέγω παραστείξῃς, αὐτὸς σὺ καὶ τἀρχαῖα καὶ τόκους τίσεις. βάδιζε καὶ μὴ παρὰ τὰ Μικκάλης αὐτόν ἄγ’, ἀλλὰ τὴν ἰθεῖαν. οὗ δ’ ἐπεμνήσθην— κάλει, κάλει δραμοῦσα, πρὶν μακρὰν, δούλη, αὐτοὺς γενέσθαι.",
    "herodas_hk_0294.3": "Πυρρίης, τάλης, κωφέ, καλεῖ σε. μᾶν, δόξει τις οὐχὶ σύνδουλον αὐτὸν σπαράσσειν ἀλλὰ σημάτων φῶρα· ὀρῇς ὅκως νῦν τοῦτον ἐκ βίης ἕλκεις ἐς τὰς ἀνάγκας, Πυρρίη; σέ, μᾶν, τούτοις τοῖς δύο Κύδιλλ’ ἐπόψεθ’ ἡμερέων πέντε παρ’ Ἀντιδώρῳ τὰς Ἀχαϊκὰς κείνας, ἃς πρῶν ἔθηκας, τοῖς σφυροῖσι τρίβοντα.",
    "herodas_hk_0294.4": "οὗτος σύ, τοῦτον αὖτις ὧδ’ ἔχων ἧκε δεδεμένον οὕτως ὥσπερ ἐξάγεις αὐτόν Κόσιν τέ μοι κέλευσον ἐλθεῖν τὸν στίκτην ἔχοντα ῥαφίδας καὶ μέλαν. μιῇ δεῖ σε ὁδῷ γενέσθαι ποικίλον. κατηρτήσθω οὕτω κατάμυος ὥσπερ ἡ Δάου τιμή.",
    "herodas_hk_0294.6": "μή, τατί, ἀλλὰ νῦν μὲν αὐτόν,—οὕτω σοι ζῴη Βατυλλὶς κήπιδοις μὲν ἐλθοῦσαν ἐς ἀνδρὸς οἶκον καὶ τέκν’ ἀγκάλαις ἄραι— ἄφες, παραιτεῦμαί σε· τὴν μίαν ταύτην ἁμαρτίαν—",
    "herodas_hk_0344.2": "Κάθησο, Μητροῖ· τῇ γυναικὶ θὲς δίφρον ἀνασταθεῖσα· πάντα δεῖ με προστάσσειν αὐτήν, σὺ δ’ οὐδὲν ἄν, τάλαινα, ποιήσαις αὐτὴ ἀπὸ σαυτῆς· μᾶ, λίθος τις, οὐ δούλη ἐν τῇ οἰκίῃ εἶς· ἀλλὰ τἆλφιτ’ ἦν μέτρῳ τὰ κρίμιν’ ἀμιθρεῖ, κἢν τοσοῦτ’ ἀποστάξῃ τὴν ἡμέρην ὅλην σε τονθορύζουσαν καὶ πρημονῶσαν οὐ φέρουσιν οἱ τοῖχοι. νῦν αὐτὸν ἐκμάσσεις τε καὶ ποεῖς λαμπρόν, ὅτ’ ἐστὶ χρείη, λῃστρί; θύέ μοι ταύτῃ ἐπεί σ’ ἔγευσ’ ἂν τῶν ἐμῶν ἐγὼ χειρῶν.",
    "herodas_hk_0344.4": "φίλη Κοριττοῖ, ταῦτ’ ἐμοὶ ζυγὸν τρίβεις. κὴγὼ ἐπιβρύχουσ’ ἡμέρην τε καὶ νύκτα κύων ὑλακτέω ταῖς ἀνωνύμοις ταύταις. ἀλλ’ οὔνεκεν πρός σ’ ἦλθον—",
    "herodas_hk_0344.5": "ἐκποδὼν ἡμῖν φθείρεσθε, νώβυστρ’, ὦτα μοῦνον καὶ γλῶσσαι τὰ δ’ ἀλλ’ ἑορτή—",
    "herodas_hk_0344.7": "λίσσομαί σε, μὴ ψεύσῃ, φίλη Κοριττοῖ, τίς ποτ’ ἦν ὅ σοι ῥάψας τὸν κόκκινον βαυβῶνα;",
    "herodas_hk_0344.8": "κοῦ δ’ ὀρώρηκας, Μητροῖ, σὺ κεῖνον;",
    "herodas_hk_0346.1": "Νοσσὶς εἶχεν ἠρίννης τριτημέρη νυν· μᾶ, καλόν τι δώρημα.",
    "herodas_hk_0346.2": "Νοσσίς; κόθεν λαβοῦσα;",
    "herodas_hk_0346.3": "διαβαλεῖς ἤν σοι εἴπω;",
    "herodas_hk_0346.4": "μὰ τούτους τοὺς γλυκέας, φίλη Μητροῖ, ἐκ τοῦ Κοριττοῦς στόματος οὐδεὶς μὴ ἀκούσῃ ὅσ’ ἂν σὺ λέξῃς.",
    "herodas_hk_0346.5": "ἡ Βιτᾶδος Εὐβούλη ἔδωκεν αὐτῇ καὶ εἶπε μηδέν’ αἰσθέσθαι.",
    "herodas_hk_0346.6": "γυναῖκες, αὕτη μ’ ἡ γυνή κοτ’ ἐκτρίψει. ἐγὼ μὲν αὐτὴν λιπαρεύσαν ᾐδέσθην κῆδωκα, Μητροῖ, πρόσθεν ἢ αὐτὴ χρήσασθαι. ἡ δ’ ὥσπερ εὕρημ’ ἁρπάσασα δωρεῖται καὶ τῇσι μὴ δεῖ. χαιρέτω, φίλη, πολλά, ἐοῦσα τοίη, κήτερην τιν’ ἀνθ’ ἡμέων φίλην ἀθρείτω τἄλλα. Νοσσίδι χρῆσθαι τῇ Μηδοκέω—μέζον μὲν ἢ γυνὴ γρύξω, λάθοιμι δ’ Ἀδρήστεια—χιλίων εὔντων ἕν’ οὐκ ἂν ὅστις λεπρός ἐστι προσδοίην.",
    "herodas_hk_0346.7": "μὴ δή, Κοριττοῖ, τὴν χολὴν ἐπὶ ῥινός ἔχ’ εὐθύς, ἤν τι ῥῆμα μὴ σοφὸν πεύθῃ. γυναικός ἐστι κρηγύης φέρειν πάντα. ἐγὼ δὲ τούτων αἰτίη λαλοῦσ’ εἰμί. τί πολλά; τήν μεν γλῶσσαν ἐκτεμεῖν δεῖται. ἐκεῖνο δ’ οὔ σοι καὶ μάλιστ’ ἐπεμνήσθην, τίς ἔσθ’ ὁ ῥάψας αὐτόν; εἰ φιλεῖς μ’ εἶπον. τί μ’ ἐνβλέπεις γελῶσα; νῦν ὀρώρηκας Μητροῦν τὸ πρῶτον; ἢ τί τάβρά σοι ταῦτα; ἐνεύχομαι, Κοριττί, μή μ’ ἐπιψεύσῃ, ἀλλ’ εἰπὲ τὸν ῥάψαντα.",
    "herodas_hk_0472.3": "ἔζεσθε πᾶσαι. κοῦ τὸ παιδίον; δέξον, Μαίη. δός, Εὐέτειρα, καὶ Γλύκην. [βρῶσιν Βιτᾶδι, λαιδρή, τὴν ἑτοῖμον οὐ δώσεις; ἀεὶ καθεύδεις; μή σε κνισμάτων μνήσω, ἤνπερ τὰ δεινὰ ταῦτ’ ἀνηνύτως κνώσσῃς, ὄσσοισιν ἤδη πολλαχῇ πεποίκιλσαι, [ταῷ τε θῶ σοι βρέγμα προσφερὲς κόρσῃς, τρισάθλι’, ὡς νεύουσα δείλαιον βλέψῃ]. φέρ’ ὧδε τήν μοι κύλικα· καὶ τὰ νῦν εὔδεις; αὕτη σὺ—μὰ μὴ βλάπτεται φρενῶν Νοσσίς οὗ πρόσθ’ ἀνῆκε;—καὶ Φιλαινίς, ᾗ ξείνην τίθεσθ’ ἅμιλλαν· ὡς ἄεθλον ἐξοίσεις γλήχωνα κείνην; τοῖς τοκεῦσί σ’ ἠειρα]",
    "herodas_hk_0472.4": "ἢ χαλκέην μοι μυῖαν ἢ κύθρην παίζει ἢ τῇσι μηλάνθησιν ἅμματ’ ἐξάπτων τοῦ κεσκίου μοι τὸν γέροντα λωβᾶται.",
    "herodas_hk_0472.5": "ὡς οἰκίην οὐκ ἔστιν εὐμαρέως εὑρεῖν ἄνευ κακῶν ζώουσαν· ὃς δ’ ἔχει μεῖον, τοῦτόν τι μέζον τοῦ ἑτέρου δόκει πρήσσειν."
}

_EDITS = {
    "herodas_hk_0290.4": [("ὀρώρηκα", "ὁρώρηκα")],
    "herodas_hk_0290.7": [("τό μεν", "τό μευ"), ("κήμέρην", "κἠμέρην")],
    "herodas_hk_0290.8": [("κοῦ ὅστις", "κοῦ ’στι")],
    "herodas_hk_0290.11": [
        ("ἐμανήθρην", "ἱμανήθρην"), ("ἦν μὴ", "ἢν μὴ"),
        ("θῶ, μὰ,", "θῶ, μᾶ,"), ("τὰ νῦν εἶναι", "τὰ νῦν εὖσαν"),
        ("εἰς σύ", "εἷς σύ"), ("ἀπληγίδ’", "ἁπληγίδ’"),
    ],
    "herodas_hk_0292.5": [("τἡμέρη κείνῃ", "τἡμέρῃ κείνῃ")],
    "herodas_hk_0292.7": [("ἁμαρτίαν", "ἁμαρτίην")],
    "herodas_hk_0292.9": [("μὴ μὲ", "μὴ ’μὲ"), ("φὴς", "φῇς")],
    "herodas_hk_0292.15": [("εἶτ’", "εἴτ’")],
    "herodas_hk_0292.17": [("ἁμαρτίαν", "ἁμαρτίην")],
    "herodas_hk_0292.21": [("ἔστηκας", "ἕστηκας")],
    "herodas_hk_0294.1": [
        ("‘φαμάρτει", "’φαμάρτει"), ("πρὶν μακρὰν", "πρὶν μακρὴν"),
        ("ἀκήκοας", "ἀκήκουκας"), ("ὡς, ἤν", "ὡς, ἢν"),
    ],
    "herodas_hk_0294.3": [("μᾶν,", "μᾶ,"), ("ὀρῇς", "ὁρῇς")],
    "herodas_hk_0294.6": [
        ("κήπιδοις μὲν", "κἠπίδοις μιν"), ("ἀγκάλαις ἄραι", "ἀγκάλαις ἄραις"),
        ("ἁμαρτίαν", "ἁμαρτίην"),
    ],
    "herodas_hk_0344.2": [
        ("τἆλφιτ’ ἦν μέτρῳ", "τἄλφιτ’ ἢν μετρῇ"), ("κρίμιν’ ἀμιθρεῖ", "κρίμν’ ἀμιθρεῖς"),
        ("εἶς", "εἴς"), ("θύέ", "θῦέ"),
    ],
    "herodas_hk_0344.4": [("κὴγὼ", "κἠγὼ"), ("οὔνεκεν", "οὕνεκεν"), ("ταῦτ’", "ταὔτ’")],
    "herodas_hk_0344.5": [("γλῶσσαι", "γλάσσαι"), ("τὰ δ’ ἀλλ’", "τὰ δ’ ἄλλ’")],
    "herodas_hk_0344.8": [("ὀρώρηκας", "ὁρώρηκας")],
    "herodas_hk_0346.1": [("τριτημέρη νυν", "τριτημέρῃ νιν"), ("ἠρίννης", "ἡρίννης")],
    "herodas_hk_0346.3": [("ἤν σοι", "ἢν σοι")],
    "herodas_hk_0346.6": [("κῆδωκα", "κἤδωκα"), ("κήτερην", "κἠτέρην"), ("λιπαρεύσαν", "λιπαρεῦσαν")],
    "herodas_hk_0346.7": [
        ("ἤν τι", "ἢν τι"), ("λαλοῦσ’", "λαλεῦσ’"),
        ("τήν μεν γλῶσσαν", "τήν μευ γλάσσαν"),
        ("τάβρά", "τἁβρά"),
        ("οὔ σοι", "οὗ σοι"), ("ὀρώρηκας", "ὁρώρηκας"),
    ],
    "herodas_hk_0472.3": [
        ("ἔζεσθε", "ἕζεσθε"),
        ("αὕτη σὺ—μὰ", "αὕτη σὺ—μᾶ"), ("ἠειρα]", "ἤειρα]"),
        ("ὄσσοισιν", "ὅσσοισιν"), ("κόρσῃς", "κόρσης"),
        ("εὔδεις", "εὕδεις"), ("ᾗ ξείνην", "ἦ ξείνην"),
    ],
    "herodas_hk_0472.4": [("λωβᾶται", "λωβῆται"), ("μηλάνθησιν", "μηλάνθῃσιν")],
}

# Repeated preimages are intentional only where both identical occurrences
# were independently checked (the two invocations of μᾶ on page 294).
_REPEATED = {("herodas_hk_0294.3", "μᾶν,"): 2}

_TERMINAL_LOSSES = {
    "herodas_hk_0472.3": 2,
    "herodas_hk_0472.4": 4,
    "herodas_hk_0472.5": 1,
}

# A second reviewer checked these initially faint marks in the original color
# pixels, using neighboring characters in the same printing as shape controls.
# The PDF and color captures are the same photograph; this is not a second vote.
_SOURCE_DETAILS = {
    "herodas_hk_0290.4": "The breathing on ὁρώρηκα is open to the right (rough), not the smooth breathing in the preceding ἐγὼ.",
    "herodas_hk_0290.8": "The source prints a separate leading elision apostrophe in κοῦ ’στι.",
    "herodas_hk_0290.11": "Verse 18 prints εἷς with a rough breathing below the circumflex; its curve faces the opposite direction from the smooth breathing in εἶναι four verses above. The alpha in ἁπληγίδ’ has the same rough curve. The source retains ἕστηκας and ἦρ’ as already transcribed.",
    "herodas_hk_0292.5": "The final eta of τἡμέρῃ has a separate iota subscript to the left of the eta descender, matching the distinct subscript in neighboring κείνῃ.",
    "herodas_hk_0292.21": "The initial epsilon of ἕστηκας prints a rough breathing and acute, distinct from the smooth breathing on ἐμβλέπων beside it.",
    "herodas_hk_0294.1": "The source prints the full sequence ἀκήκουκας and a grave accent in ἢν in verse 50.",
    "herodas_hk_0294.3": "The initial omicron of ὁρῇς has a distinct rough curve, matching the rough breathing of ὅκως beside it.",
    "herodas_hk_0344.2": "Verse 5 prints εἴς with smooth breathing plus acute, rather than a circumflex; the same combined mark appears over alpha in τἄλφιτ’ beside it. The source prints θῦέ with a circumflex over upsilon and acute over epsilon. The initial review's added upsilon in τονθορύζουσαν was rejected after both reviewers checked the native pixels: the printing has τονθορύζουσαν.",
    "herodas_hk_0344.4": "The upsilon of οὕνεκεν has rough breathing plus acute, rather than smooth breathing. The upsilon of ταὔτ’ has smooth breathing plus acute, not a circumflex.",
    "herodas_hk_0344.7": "The initial review's removal of the acute from ὅ was rejected: the native scan distinctly prints rough breathing plus acute in ὅ σοι, as in the original excerpt.",
    "herodas_hk_0344.8": "The initial omicron of ὁρώρηκας has the rough curve also printed in ὅ above.",
    "herodas_hk_0346.1": "The initial eta in ἡρίννης has the rough curve also printed in the article ἡ on this page, facing the opposite direction from smooth ἐγὼ. The final eta in τριτημέρῃ has a separate iota subscript to the left of its descender.",
    "herodas_hk_0346.6": "The initial alpha of ἁρπάσασα has a distinct rough curve, matching the rough article ἡ at the beginning of its verse. The source prints a circumflex in λιπαρεῦσαν. The initial review's change of ἕν’ to ἓν was rejected: the native source has rough breathing plus acute and a separate elision apostrophe after nu.",
    "herodas_hk_0346.7": "The first alpha in τἁβρά has a rough breathing; the final alpha has the acute. The source prints rough breathing plus circumflex in οὗ and rough breathing in ὁρώρηκας; these remain literal even where the old OCR had a different word.",
    "herodas_hk_0472.3": "The source prints rough breathing plus acute in ὅσσοισιν and εὕδεις, κόρσης without a subscript, and ἦ ξείνην with smooth breathing plus circumflex and no subscript. The initial review's change of σὺ to σύ was rejected: the native scan distinctly prints a grave before the dash. The critical brackets already present remain literal.",
    "herodas_hk_0472.4": "The eta of μηλάνθῃσιν has a separate iota subscript to the left of its descender.",
}


def _build_readings():
    rows = {}
    for locus, original in _ORIGINALS.items():
        page = int(locus.rsplit("_", 1)[1].split(".", 1)[0])
        if page not in PAGES:
            raise ValueError("Unexpected Herodas excerpt source page")
        corrected = original
        for old, new in _EDITS.get(locus, []):
            if corrected.count(old) != _REPEATED.get((locus, old), 1):
                raise ValueError("Herodas excerpt observation preimage changed: " + locus)
            corrected = corrected.replace(old, new)
        losses = _TERMINAL_LOSSES.get(locus, 0)
        corrected += "\n. . . . . . . ." * losses
        evidence = (
            f"Manual inspection of pinned Headlam–Knox 1922 PDF page {page}, "
            f"printed page {page - 70}; Greek body checked against enlarged source "
            "renderings, including focused crops at ten times PDF point resolution "
            "and native original color captures for the small diacritics. "
            "Existing locus and dialogue boundaries are retained, separately printed "
            "speaker labels and editorial headings remain excluded, and printed "
            "dialect and critical marks are preserved without grammatical emendation."
        )
        evidence += (
            f" Original color capture page-{page:04d}.jp2 SHA-256 "
            f"{ORIGINAL_IMAGE_SHA256[page]} is retained in "
            "data/corpus_changes/herodas-reading-sources/manifest.json. It is the "
            "same scan as the PDF, not an independent textual witness."
        )
        if locus in _SOURCE_DETAILS:
            evidence += " Independent native-color recheck: " + _SOURCE_DETAILS[locus]
        if losses:
            evidence += (
                f" The source prints {losses} terminal dotted loss row(s), each with "
                "eight dots, before the next heading or apparatus; these were absent "
                "from the existing OCR and are retained literally."
            )
        rows[locus] = {
            "original_text": original,
            "corrected_text": corrected,
            "source_sha256": SOURCE_SHA256,
            "source_image_sha256": ORIGINAL_IMAGE_SHA256[page],
            "scan_page": page,
            "evidence": evidence,
            "reviewed_at": REVIEWED_AT,
            "uncertainties": [],
        }
    if len(rows) != 36 or set(_EDITS) - set(rows):
        raise ValueError("Herodas excerpt source review does not account for all assigned rows")
    return rows


READINGS = _build_readings()

