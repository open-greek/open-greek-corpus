"""Readings checked on eight body pages of the pinned Headlam–Knox scan.

The original printed critical marks and losses remain literal. Explicit glyph
uncertainties are occurrence keyed; they do not authorize a preferred reading.
"""
from __future__ import annotations

import re

SOURCE_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
REVIEWED_AT = "2026-10-22T17:38:27+00:00"


def _reading(page, text, *, labels=(), uncertain=(), evidence_note=""):
    text = text.strip()
    items = []
    for word, occurrence, alternatives, reason in uncertain:
        matches = list(re.finditer(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text))
        if not 1 <= occurrence <= len(matches):
            raise ValueError("Unknown Herodas source uncertainty occurrence")
        match = matches[occurrence - 1]
        items.append({"start": match.start(), "end": match.end(), "text": word,
            "alternatives": list(alternatives), "reason": reason,
            "evidence": f"Pinned Headlam–Knox PDF page {page}, high-resolution visual inspection: {reason}"})
    return {"text": text, "evidence": (f"Manual inspection of the pinned Headlam–Knox 1922 PDF, physical page {page}, printed page {page - 70}; source SHA-256 {SOURCE_SHA256}. Body crop rendered at four times PDF point resolution; headings, marginal verse numbers, and separately printed speaker names excluded. Existing Qwen3.6 output used only as a comparison draft. " + evidence_note).rstrip(),
        "reviewed_at": REVIEWED_AT, "uncertainties": items, "speaker_labels": list(labels)}


READINGS = {
    392: _reading(392, """
χαλκῶν δέ. τοῦτ’ ἢν μὴ ὑμῖν ἀνδάνῃ, Μητροῖ,
τὸ ζεῦγος, ἕτερον κἤτερον μάλ’ ἐξοίσει,
ἔστ’ ἂν νόῳ πεισθῆτε μὴ λέγειν ψεύδεα
Κέρδωνα. τὰς μοι σαμβαλουχίδας πάσας
ἔνεγκε, Πίστε· δεῖ μάλ’ εἰς γ’ ἴχνη θείσας
ὑμέας ἀπελθεῖν, ὦ γυναῖκες, εἰς οἶκον.
θήσεσθε δ’ ὑμεῖς· γένεα ταῦτα παντοῖα·
Σικυώνι’, Ἀμβρακίδια, νοσσίδες, Χῖαι,
ψιττάκια, κανναβίσκα, βαυκίδες, βλαῦται,
Ἰωνικ’ ἀμφίσφαιρα, νυκτιπήδηκες,
ἀκροσφύρια, καρκίνια, σάμβαλ’ Ἀργεῖα,
κοκκίδες, ἔφηβοι, διάβαθρ’· ὧν ἐρᾷ θυμός
ὑμέων ἑκάστης εἴπατ’· ὡς ἂν αἴσθοισθε
σκύτεα γυναῖκες καὶ κύνες τί βρώζουσιν.
κόσου χρεΐζεις κείν’ ὃ πρόσθεν ἤειρας
ἀπεμπολὴν μοι ζεῦγος; ἀλλὰ μὴ βροντέων
αὐτὸς σὺ τρέψον μέζον εἰς φυγὴν ἡμέας.
αὐτὴ σὺ καὶ τίμησον εἰ θέλεις αὐτό
καὶ στῆσον ἧς κοτ’ ἐστὶν ἄξιον τιμῆς.
ἢ τοῦτο· ἐὰν γὰρ οὖ σε ῥηδίως χρήναι
σκυτέων, γύναι, τὠληθὲς ἢν θέλῃς, ἔργον
ἐρεῖς τι. ναὶ μὰ τήνδε τὴν τεφρὴν κόρσην,
ἐφ’ ἧς ἀλώπηξ νοσσίην πεποίηται,
τάχ’ ἀλφιτηρὸν ἐργαλεῖα κινεῦσι,
Ἑρμῆ τε Κερδέων καὶ σὺ Κερδείη Πειθοῖ,
ὡς, ἢν τι μὴ νῦν ἡμῖν ἐς βόλον κύρσῃ,
οὐκ οἶδ’ ὅκως ἄμεινον ἡ κύθρη πρήξει.
τί τουνθρύζεις κοὐκ ἐλευθέρῃ γλάσσῃ
τὸν τῖμον ὅστις ἐστὶν ἐξεδίφησας;
""", labels=("ΓΥΝΗ", "ΚΕΡΔΩΝ"), uncertain=(
        ("ἀνδάνῃ", 1, ("ἁνδάνῃ",), "The small initial breathing is less distinct than the printed letters."),
        ("ἔφηβοι", 1, ("ἐφήβοι", "ἑφήβοι"), "The first-vowel breathing and accent require a second scan check."),
        ("οὖ", 1, ("οὗ", "οὐ"), "The upsilon diacritics are not sufficiently distinct to certify."),
        ("Ἑρμῆ", 1, ("Ἐρμῆ",), "The initial capital's breathing requires a second scan check."),
    )),
    394: _reading(394, """
γύναι, μιῆς μνῆς ἐστιν ἄξιον τοῦτο
τὸ ζεῦγος, ἢ ἄνω σ’ ἢ κάτω βλέπειν· χαλκοῦ
ῥίνημ’ ὃ δήκοτ’ ἐστὶ τῆς Ἀθηναίης
ὠνευμένης αὐτῆς ἂν οὐκ ἀποστάξαι.
μάλ’ εἰκότως σευ τὸ στεγύλλιον, Κέρδων,
πέπληθε δαψιλέων τε καὶ καλῶν ἔργων.
φύλασσε κλείσας αὐτά· τῇ γὰρ εἰκοστῇ
τοῦ Ταυρεῶνος ἡ ’κατῆ γάμον ποιεῖ
τῆς Ἀρτακηνῆς, κὑποδημάτων χρείη·
τάχ’ οὖν, τάλης, ἄξουσι σὺν τύχῃ πρὸς σε,
μᾶλλον δὲ πάντως· ἀλλὰ θύλακον ῥάψαι
τὰς μνέας ὅκως σοι μὴ αἱ γαλαῖ διοίσουσι.
ἢν τ’ ἡ ’κάτη ἔλθῃ, μνῆς ἔλασσον οὐκ οἴσει,
ἢν τ’ ἡ Ἀρτακηνή· πρὸς τάδ’, εἰ θέλεις, σκέπτευ.
οὔ σοι δίδωσιν ἡ ἀγαθὴ τύχη, Κέρδων,
ψαῦσαι ποδίσκων ὧν πόθοι τε κἤρωτες
ψαύουσιν, ἀλλ’ εἷς κνῦσα καὶ κακὴ λώβη·
ὥστ’ ἐκ μὲν ἡμέων δι’ ἔλεόν σεο ἡ πρῆξις,
ταύτῃ δὲ δώσεις κεῖνο τὸ ἕτερον ζεῦγος
κόσου; πάλιν πρήμηνον ἀξίην φωνὴν
σωυτοῦ.
στατῆρας πέντε, ναὶ μὰ θεούς, φοιτᾷ
ἡ ψάλτρι’ Εὐέτηρις ἡμέρην πᾶσαν
λαβεῖν ἀνώγουσ’, ἀλλ’ ἐγώ μιν ἐχθαίρω,
κἢν τέσσαράς μοι Δαρικοὺς ὑπόσχηται,
ὁτεύνεκέν μευ τὴν γυναῖκα τωθάζει
κακοῖσι δέννοις· εἰ δὲ καί σ’ ἔχει χρείη
φέρ’,—εὐλαβοῦ δὲ τῶν τριῶν ὄναρ δοῦναι—
""", labels=("ΚΕΡΔΩΝ", "ΓΥΝΗ", "ΜΗΤΡΩ"), uncertain=(
        ("κὑποδημάτων", 1, ("κὐποδημάτων",), "The crasis breathing is too small to certify independently."),
        ("οὔ", 1, ("οὐ",), "The mark over upsilon may be an acute accent in addition to the breathing."),
        ("εἷς", 1, ("εἶς", "εἰς"), "The breathing and accent over iota are not fully distinct."),
    )),
    396: _reading(396, """
καὶ ταῦτα καὶ ταῦτα· ἡ ὑμῖν ἑπτὰ Δαρεικῶν
ἕκητι Μητροῦς τῆσδε μηδὲν ἀντεῖπον·
δύναιτό μ’ ἐλάσαι σὴ ἂν ἰὴ τὸν πίσυγγον
ἐόντα λίθινον ἐς θεοὺς ἀναπτῆναι·
ἔχεις γὰρ οὐχὶ γλάσσαν ἡδονῆς δ’ ἰσθμόν·
ἆ, θεῶν ἐκεῖνος οὐ μακρὴν ἀπῴκισται
ὁτέῳ σὺ χείλεα νύκτα κἠμέρην οἴγεις.
φέρ’ ὧδε τὸν ποδίσκον· εἰς ἴχνος θῶ μιν.
πάξ· μήτε προσθῇς μήτ’ ἀπ’ οὖν ἕλῃς μηδέν·
τὰ καλὰ πάντα τῆς καλῆσιν ἁρμόζει·
αὐτὴν ἐρεῖς τὸ πέλμα τὴν Ἀθηναίην
τεμεῖν. δὸς αὐτὴ καὶ σὺ τὸν πόδ’· ἆ, ψωρῇ
ἄρηρεν ὁπλῇ βοῦς ὁ λακτίσας ὑμέας.
εἴ τις πρὸς ἴχνος ἠκόνησε τὴν σμιλήν,
οὐκ ἂν, μὰ τὴν Κέρδωνος ἑστίην, οὕτω
τοὔργον σαφέως ἔκειτ’ ἂν ὡς σαφέως κεῖται.
αὐτὴ σύ, δώσεις ἑπτὰ Δαρικοὺς τοὔδε,
ἡ μέζον ἵππου πρὸς θύρην κιχλίζουσα;
γυναῖκες, ἢν ἔχητε κἠτέρων χρείην
ἡ σαμβαλίσκων ἡ ἃ κατ’ οἰκίην ἕλκειν
εἴθισθε, τὴν μοι δουλίδ’ ὧδε δεῖ πέμπειν.
σὺ δ’ ἧκε, Μητροῖ, πρός με τῇ ἐνάτῃ πάντως
ὅκως λάβῃς καρκίνια· τὴν γὰρ οὖν βαίτην
θάλπους ἄνευ νόον τὸν φρονοῦντα δεῖ ῥάπτειν.
""", uncertain=(
        ("ἡ", 1, ("ἢ",), "The initial eta's breathing and accent are not fully distinct."),
        ("κἠμέρην", 1, ("κἡμέρην",), "The crasis breathing requires a second visual check."),
        ("τῆς", 1, ("τῇς",), "The eta's descender cannot be securely distinguished from a separate iota subscript."),
        ("καλῆσιν", 1, ("καλῇσιν",), "The eta's descender cannot be securely distinguished from a separate iota subscript."),
        ("ὧδε", 1, ("ὦδε",), "The breathing over omega is not fully distinct."),
        ("ὧδε", 2, ("ὦδε",), "The breathing over omega is not fully distinct."),
        ("ἡ", 2, ("ἢ",), "The eta before μέζον has an indistinct diacritic."),
        ("ἡ", 3, ("ἢ",), "The eta before σαμβαλίσκων has an indistinct diacritic."),
        ("ἡ", 4, ("ἢ",), "The eta before ἃ has an indistinct diacritic."),
    )),
    440: _reading(440, """
Ἄστηθι, δούλη Ψύλλα· μέχρι τέο κείσῃ
ῥέγχουσα; τὴν δὲ χοῖρον αὐόνη δρύπτει·
ἡ προσμένεις σὺ μέχρι σευ ἥλιος θάλψει
τὸν κυσὸν ἐσδύς; κῶς δ’, ἄτρυτε, κοὐ κάμνεις
τὰ πλευρὰ κνώσσουσ’; αἱ δὲ νύκτες ἐννέωροι.
ἄστηθι, φημί, καὶ ἄψον, εἰ θέλεις, λύχνον,
καὶ τὴν ἄναγνον χοῖρον ἐς νομὴν πέμψον.
τούνθρυζε καὶ κνῶ, μέχρις οὗ παραστάς σοι
τὸ βρέγμα τῷ σκίπωνι μαλθακὸν θῶμαι.
δειλὴ Μεγαλλί, καὶ σὺ Λάτμιον κνώσσεις;
οὐ τἄργα σὲ τρύχουσιν· ἀλλὰ μὴν στέμμα
ἐπ’ ἱρὰ διζόμεσθα· βαιὸς οὐχ ἡμῖν
ἐν τῇ οἰκίῃ ’στι μαλλὸς εἰρίων. δειλή,
ἄστηθι· σὺ τέ μοι τοῦναρ, εἰ θέλεις, Ἀννᾶ,
ἄκουσον, οὐ γὰρ νηπίας φρένας βόσκεις.
τράγον τιν’ ἕλκειν διὰ φάραγγος ὠΐσθην
μακρῆς, ὁ δ’ εὐπώγων τε κεὐκέρως ἦν τις.
[ἐπεὶ δ’ ἐδεῖτ’, ἄψ ἦλθον ἐκ δὲ τῆς βήσσης,
ἠοῦς φαούσης, τοῦ κόπου γὰρ ἐσσῶμαι,
σύθην ὅκου θύοντες αἰπόλοι πλείην
τὴν κοιλάδ’ οὐλέων εἰρίων τ’ ἐποιεῦντο.
κἠγὼ οὐκ ἐσύλευν ἀλλ’ ὁ μ’ αἴξ φυγὼν ἄλλης
καὶ ἄλλης δρυὸς μάλ’ αὖτε γεύεται τρώγων.
""", uncertain=(
        ("ἡ", 1, ("ἢ",), "The eta introducing the question has an indistinct diacritic."),
        ("κἠγὼ", 1, ("κἡγὼ",), "The crasis breathing requires a second visual check."),
    )),
    442: _reading(442, """
οἱ δ’ ἀμφί, κάρτ’ ὀχθεῦντες, [ἁρπαγὴν μοι, Ἀννᾶ,
τὸν αἶγ’ ἐποίευν καὶ ἐσπαράξαν ἐν χερσίν.
καὶ πλησίον μευ παιγνίην ἀγυνεῦντες
κατήρεσαν· μᾶ, λεῖος ἦν ἀγωνιστής·]]
σχιστὸν κροκωτὸν ἠμφίεστ’ ὅθεν μηροῦ
ὤφθη τι λεπτῆς ἄντυγος θεωρεῦντι·
στολίδας δὲ νεβροῦ χλανιδίων κατεζώσθη
καὶ λινέην κύπασσιν ἀμφὶ τοῖς ὤμοις,
κόρυμβα δ’ ἀμφὶ κρητὶ κίσσιν’ ἔστεπτο·
χρυσέους κοθόρνους περὶ πόδας καταζώστρῃ
τετάνυστο· κὠ μὲν τόσσα· σάγμα δ’ εἰς φρίκης
ὀρθρου ἀλεωρὴν εἶχεν, ἀμφιθεὶς ὤμοις
στεγνὸν τὸ λῶπος. κώρυκον δὲ πειρῆσθαι,
ναύταις Ὀδυσσέως ὀλοὸν Αἰόλου δῶρον
[ἐκεῖνο φήσεις, θέντο, πάντα λακτίζειν
στάδην λέγοντες ἐκφέρειν δὲ τὸν λῷστον,]
ὥσπερ τελεῦμεν ἐν χοροῖς Διωνύσου.
κοἱ μὲν μετώποις ἐς κόνιν κολυμβῶντες
ἔκοπτον ἀρνευτῆρες ἐκ βίης οὖδας,
οἱ δ’ ὕπτι’ ἐρριπτεῦντο· πάντα δ’ ἦν, Ἀννᾶ,
εἰς ἓν γέλως τε κἀνίη ’ναμιχθέντα.
κἠγὼ δόκεον δισμύρι’ ἐκ τόσσης λείης
ἐπ’ οὖν ἁλέσθαι· κἠλάλαξαν ὤνθρωποι
ὡς μ’ εἶδον ἁπαλῶς τὴν δορὴν πιεζεῦσαν
καὶ [φασὶν οἱ μὲν ἐκφέρειν με τάεθλον]
οἱ δ’ ἐ . . . . . . .
γρυπ(άνιος) . . . . . .
ῥυπ(αρὸς) . . . . . . .
τ( . . . . . . . .
τ( . . . . . . . .
. . . . . . . . .
""", uncertain=(
        ("ἁρπαγὴν", 1, ("ἀρπαγὴν",), "The initial breathing is not sufficiently distinct to certify."),
        ("ἠμφίεστ’", 1, ("ἡμφίεστ’",), "The breathing over initial eta is not fully distinct."),
        ("ὀρθρου", 1, ("ὄρθρου", "ὀρθροῦ"), "The printed accent over the middle of this word is faint."),
        ("κἠγὼ", 1, ("κἡγὼ",), "The crasis breathing is not fully distinct."),
        ("κἠλάλαξαν", 1, ("κἡλάλαξαν",), "The crasis breathing is not fully distinct."),
        ("ἁπαλῶς", 1, ("ἀπαλῶς",), "The alpha breathing is not fully distinct."),
        ("ἐ", 1, (), "Verse 49 preserves only an initial epsilon before the printed dotted loss."),
        ("γρυπ(άνιος)", 1, (), "The printed verse is incomplete; preserve the parenthesized reconstruction and following loss."),
        ("ῥυπ(αρὸς)", 1, (), "The printed verse is incomplete; preserve the parenthesized reconstruction and following loss."),
        ("τ(", 1, (), "The first isolated tau begins an incomplete printed word."),
        ("τ(", 2, (), "The second isolated tau begins an incomplete printed word."),
    )),
    444: _reading(444, """
. . . . . . . . .
. . . . . . . . .
. . . . . . . . .
‘τὰ δεινὰ πνεῦσαι, λὰξ πατέοντα θεῶν ἁγνά;
ἔρρ’ ἐκ προσώπου, μή σε καίπερ ὢν πρέσβυς
οὐλῇ κατιθὺ τῇ βατηρίῃ κόψω.’
κἠγὼ μεταῦτις· ‘ὦ παρεόντες, οὐκ ἄκων
θανεῦμ’ ὑπὲρ γῆς, εἰ ὁ γέρων μ’ ἐπιτρέψει·
μαρτύρομαι δὲ τὸν νεηνίην αὐτόν.’
ὁ δ’ εἶπεν ἄμφω τὸν δορέα [διαχρῆσθαι.
καὶ τοῦτ’ ἰδὼν ἔληξα. τοὔνδυτον κοῦ μοι;
Ἀννᾶ δὸς ὧδε. τοὔναρ ὧδ’ ἰδὼν κρίνω·]
ὅκως τὸν αἶγα τῆς φάραγγος ἐξεῖλκον,
[οὐ σχὼν παρ’ ἄλλου δῶρον, εἰς Διωνύσου,]
οἱ δ’ αἰπόλοι νιν ἐκ βίης ἐλωβεῦντο,
τὰ ἔνθεα τελεῦντες, καὶ κρεῶν ἐδαίνυντο,
τὰ μέλεα πολλοὶ κάρτα, τοὺς ἐμοὺς μόχθους,
τιλεῦσιν ἐν μούσῃσιν· ὧδε γοῦν κρίνω.
τὸ μὴν ἄεθλον ὡς δόκουν ἔχειν μοῦνος,
πολλῶν τὸν ἄπνουν κώρυκον πατησάντων,
κἠ τῷ γέροντι ξὺν’ ἐπρῆξ’ ὀρινθέντι,
ἕξω κλέος, ναὶ μοῦσαν, ἥ μ’ ἔπεα κοσμεῖς,
μέγ’ ἐξ ἰάμβων, ἥ με δευτέρῃ γνώμῃ
ποιεῖς μεθ’ Ἱππώνακτα τὸν πάλαι κεῖνον
τὰ κύλλ’ ἀείδειν Ξουθίδαις ἐπίουσιν.
""", uncertain=(
        ("ἁγνά", 1, ("ἀγνά",), "The alpha breathing requires a second scan check."),
        ("κἠγὼ", 1, ("κἡγὼ",), "The crasis breathing is not fully distinct."),
        ("ὧδε", 1, ("ὦδε",), "The omega breathing requires a second scan check."),
        ("ὧδ’", 1, ("ὦδ’",), "The omega breathing requires a second scan check."),
        ("ὧδε", 2, ("ὦδε",), "The omega breathing requires a second scan check."),
        ("κἠ", 1, ("κἡ",), "The contracted eta breathing is not fully distinct."),
    )),
    480: _reading(480, """
Ἐπὴν τὸν ἑξηκοστὸν ἥλιον κάμψῃς
ὦ Γρύλλε, Γρύλλε, θνῆσκε καὶ τέφρη γίνευ·
ὡς τυφλὸς οὐπέκεινα τοῦ βίου καμπτήρ·
ἤδη γὰρ αὐγὴ τῆς ζοῆς ἀπήμβλυνται.
"""),
    486: _reading(486, """
προσφὺς ὅκως τις χοιράδων ἀνηρίτης.
. . . . . . . .
""", evidence_note="The full XI body region [0.20, 0.304, 0.96, 0.360] includes its terminal eight-dot loss row. The historical recognition request used [0.20, 0.304, 0.96, 0.344], which ends above that row. The dots were checked directly on the fuller scan block; they are not claimed as recognition output. The following separately headed XIa quotation remains excluded."),
}

# VIII.18 opens an outer editorial bracket on PDF 440. PDF 442 begins
# inside that range, then opens another bracket before ἁρπαγὴν; the two
# closing brackets after ἀγωνιστής close the nested and inherited ranges.
READINGS[442]["initial_brackets"] = ["]"]
READINGS[442]["initial_brackets_evidence"] = (
    "Pinned Headlam–Knox PDF440, VIII.18: [ἐπεὶ opens the outer range. "
    "That range continues through the end of PDF440 and into PDF442, VIII.24. "
    "The additional [ before ἁρπαγὴν on PDF442 is nested; the printed ]] "
    "after ἀγωνιστής in VIII.27 closes both ranges. The words before the "
    "new opener on PDF442 therefore remain inside the inherited outer range."
)
READINGS[444]["initial_brackets"] = []
READINGS[444]["initial_brackets_evidence"] = (
    "Pinned Headlam–Knox PDF442: the final square-bracket range, καὶ [φασὶν "
    "... τάεθλον], closes in VIII.48. No square-bracket range carries into "
    "PDF444. The isolated τ( remnants in VIII.52–53 are local incomplete "
    "printed words, not editorial ranges extending beyond the damaged lines. "
    "PDF444 begins with the three dotted losses VIII.55–57, followed by the "
    "unbracketed text of VIII.58; its first new editorial [ occurs in VIII.64."
)
