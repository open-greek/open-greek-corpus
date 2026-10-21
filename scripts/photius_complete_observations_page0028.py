"""Complete direct source review of retained historical passages on Bekker printed293.

All ten retained passages were visually inspected in overlapping scan crops. Compact
Greek ligatures and unclear technical phrases keep their exact original uncertainties.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T13:41:49.975634+00:00'
_CROPS = {'L1':[.055,.10,.455,.20], 'L2':[.055,.16,.455,.33], 'L3':[.055,.27,.455,.42], 'L4':[.055,.35,.455,.60], 'L5':[.055,.49,.455,.65], 'L6':[.055,.56,.455,.71], 'R1':[.395,.10,.815,.20], 'R2':[.395,.16,.815,.43], 'R3':[.395,.395,.815,.57], 'R4':[.395,.47,.815,.755]}
_SPECS = [(28,
  1,
  '9ae5028dda4553783e88f0d39adf9ae7507a3fb55b5aca2c148d8d8363f81afa',
  '908. Ἀνεγνώσθη τοῦ ἁγίου ΜΕΘΟΔΙΟΥ, ἐπισκόπου καὶ μάρτυρος, ἐκ τῷ περὶ ἀναστάσεως λόγῳ, οὗ ἡ ἐκλογὴ τὰ '
  'ὑποκείμενα λέγει.',
  'Ἀνεγνώσθη τοῦ ἁγίου ΜΕΘΟΔΙΟΥ, ἐπισκόπου καὶ μάρτυρος, ἐκ τοῦ περὶ ἀναστάσεως λόγῳ, οὗ ἡ ἐκλογὴ τὰ ὑποκείμενα '
  'λέγει.',
  'L1',
  [],
  [('Ἀνεγνώσθη',
    'Ἀνεγνώθη',
    'The compact heading σθ/θ group remains uncertain. Both Ἀνεγνώσθη and Ἀνεγνώθη are preserved without '
    'restoring the familiar formula.'),
   ('λόγῳ',
    'λόγου',
    'The compact final ου/ῳ type is uncertain. Original λόγῳ and possible λόγου are retained without correcting '
    'the case from syntax.')]),
 (28,
  2,
  '8393e9cf6b94e4b7b1af589c52bb8579ba57912e8de3bf45b41505c9cb69f6a4',
  'δι’ οὐ διαμοῦν φησι τὸ σῶμα τῆς ψυχῆς εἶναι, ὡς Ὠριγένης ἧστο, ἀλλ’ δεσμοῦντας τὰς ψυχὰς παρὰ τῷ προφήτῃ '
  'Ἰερεμίᾳ κυλτεῖν διὰ τὸ ἐν σώμασιν αὐτὰς τυγχάνειν. οὐ γὰρ ἐμποδίζειν τὰς τῆς ψυχῆς ἐνεργίας τὸ σῶμα τίθεσι, '
  'συμπεριφέρεσθαι δὲ μᾶλλον τὸ σῶμα καὶ συνεργεῖν πρὸς ἣ ἡ ψυχὴ ἐπιτρέπει. ἀλλὰ το- 480. πῶς “τὸ τὸ Θεολόγου '
  'Γρηγορίου ροπτεῖον καὶ ἄλλων πολλῶν ;',
  'ὅτι οὐ δεσμὸν φησι τὸ σῶμα τῆς ψυχῆς εἶναι, ὡς Ὠριγένης ᾤετο, ἀλλὰ δεσμώτιδας τὰς ψυχὰς παρὰ τῷ προφήτῃ '
  'Ἱερεμίᾳ κυλτεῖν διὰ τὸ ἐν σώμασιν αὐτὰς τυγχάνειν. οὐ γὰρ ἐμποδίζειν τὰς τῆς ψυχῆς ἐνεργείας τὸ σῶμα τίθεται, '
  'συμπεριφέρεσθαι δὲ μᾶλλον τὸ σῶμα καὶ συνεργεῖν πρὸς ἃ ἡ ψυχὴ ἐπιτρέπει. ἀλλὰ το- 480. πῶς τὸ τοῦ θεολόγου '
  'Γρηγορίου νοητέον καὶ ἄλλων πολλῶν;',
  'L2',
  [],
  [('κυλτεῖν',
    'καλεῖσθαι',
    'The compact middle and terminal types remain uncertain, including σθ/θ; possible καλεῖσθαι or καλεῖθαι and '
    'original κυλτεῖν remain explicit.'),
   ('ἀλλὰ το- 480. πῶς',
    'ἀλλὰ τοῦτο πῶς',
    'The compact line-boundary demonstrative is unclear; possible ἀλλὰ τοῦτο πῶς and the exact original remain '
    'explicit, including the OCR line intrusion.')]),
 (28,
  3,
  'bed0522328794f5dcd524900607755d16be2bda4157cb19b831f2af49eb4ae4b',
  'δι’ Ὠριγένης διαμοῦν τὸ σῶμα ἔλεγε δεδὸθῆ τῇ ψυχῇ μετὰ τὴν παράβασιν, πρὶν δὲ ἀσωμάτων αὐτὴν εἶναι. ἀλλὰ καὶ '
  'τῷτο τὸ σῶμα, ὃ παρακελεύεται, αἰτίων εἶναι τῶν ἁμαρτιῶν διὰ τοῦτο ἡ διαμοῦν ἔλεγεν, ὡς ἀπὸ τῶν ἀγαθῶν ἔργων '
  'κυλτεῖν δυνάμενον τὴν ψυχήν.',
  'ὅτι Ὠριγένης δεσμὸν τὸ σῶμα ἔλεγε δεδὸθῆ τῇ ψυχῇ μετὰ τὴν παράβασιν, πρὶν δὲ ἀσώματον αὐτὴν βιοτεύειν. ἀλλὰ '
  'καὶ τοῦτο τὸ σῶμα, ὃ περικείμεθα, αἴτιον εἶναι τῶν ἁμαρτιῶν· διὰ τοῦτο καὶ δεσμὸν ἔλεγε, ὡς ἀπὸ τῶν ἀγαθῶν '
  'ἔργων κυλτεῖν δυνάμενον τὴν ψυχήν.',
  'L3',
  [],
  [('δεδὸθῆ',
    'δεδόσθαι',
    'The compact terminal σθ group is not independently resolved; possible δεδόσθαι or δεδόθαι and original '
    'δεδὸθῆ remain explicit.'),
   ('κυλτεῖν',
    'κωλύειν',
    'The compact vowel and middle types remain uncertain; possible κωλύειν or κωλῦειν and original κυλτεῖν remain '
    'explicit.')]),
 (28,
  4,
  'c710cb6af52d57743fe863265f0c33ddb78968d81c69eeace607b8b0ec4be6c3',
  'δι’ εἰ δεσμός ἐδόθη τὸ σῶμα μετὰ τὴν παράβασιν, ἢ τῶν κακῶν ἢ τῶν ἀγαθῶν ἐδόθη τῇ ψυχῇ. τῶν μὲν οὖν ἀγαθῶν '
  'ἀδύνατον· ἀλλ’ γὰρ ἰατρὸς ἢ τιχνιτῶν ἄλλος τῷ ἁμαρτήσαντι δίδωσι φάρμακον ὥσπε πλὸν ἐξαρμαρτήσαι, μὴ ὅτε γε '
  'Θάος. λείπεσθ δὴ τῶν κακῶν. ἀλλὰ μὴν δρῶμεν ὡς κατ’ ἀρχὰς ὁ μὲν Κάιν περιελόμενος τῷτο τὸ σῶμα ἐφρόνουν· οἱ δὲ '
  'ἔριζες πρὸς ἄς ἀθεμιουργίας ἐξώκειλαν, δῆλον. οὐδὲ τῶν κακῶν ἄρα δεσμός τὸ σῶμα. ἀλλ’ ὅμως ἦρα δεσμός, οὐδ’ '
  'ἔστρον αὐτὸ ἡφμάσατο μετὰ τὴν παράβασιν ἢ ψυχή.',
  'ὅτι εἰ δεσμὸς ἐδόθη τὸ σῶμα μετὰ τὴν παράβασιν, ἢ τῶν κακῶν ἢ τῶν ἀγαθῶν ἐδόθη τῇ ψυχῇ. τῶν μὲν οὖν ἀγαθῶν '
  'ἀδύνατον· οὐδὲ γὰρ ἰατρὸς ἢ τεχνιτῶν ἄλλος τῷ ἁμαρτήσαντι δίδωσι φάρμακον ὥστε πλέον ἐξαμαρτῆσαι, μὴ ὅτι γε '
  'θεός. λείπεται δὴ τῶν κακῶν. ἀλλὰ μὴν ὁρῶμεν ὡς κατ’ ἀρχὰς ὁ μὲν Κάϊν περικείμενος τοῦτο τὸ σῶμα ἐφόνευσεν· οἱ '
  'δ’ ἐφεξῆς πρὸς ἃς ἀθεμιτουργίας ἐξώκειλαν, δῆλον. οὐδὲ τῶν κακῶν ἄρα δεσμὸς τὸ σῶμα. οὐδ’ ὅλως ἄρα δεσμὸς, '
  'οὐδ’ ὕστερον αὐτὸ ἠμφιάσατο μετὰ τὴν παράβασιν ἡ ψυχή.',
  'L4',
  [],
  []),
 (28,
  5,
  'e435726cf28c6fc3e8cda358af3b428d95c3dd1bb3a7809ec5902b10ce1c0ce2',
  'δι’ Ἄνθρωπός φησι λέγεσθ ἀληθέστατα κατὰ φύσιν ὅλὅτε ψυχὴ χωρὶς σώματος ὅτε αὐ πάλιν σῶμα χωρὶς ψυχῆς, ἀλλὰ τὸ '
  'ἐκ συστάσεως ψυχῆς ἢ σώματος εἰς μίαν τὴν τὸ καλοῦ μορφὴν συντεθεῖν. ὁ δ’ Ὠριγένης τὴν ψυχὴν μόνην ἔλεγεν '
  'ἄνθρωπον, ὡς ὁ Πλάτων.',
  'ὅτι Ἄνθρωπός φησι λέγεσθαι ἀληθέστατα κατὰ φύσιν οὔτε ψυχὴ χωρὶς σώματος οὔτε αὖ πάλιν σῶμα χωρὶς ψυχῆς, ἀλλὰ '
  'τὸ ἐκ συστάσεως ψυχῆς καὶ σώματος εἰς μίαν τὴν τοῦ καλοῦ μορφὴν συντεθέν. ὁ δ’ Ὠριγένης τὴν ψυχὴν μόνην ἔλεγεν '
  'ἄνθρωπον, ὡς ὁ Πλάτων.',
  'L5',
  [],
  []),
 (28,
  6,
  '03c8ce0ca0b814a10f2bec2bb58faff7eccdccab28f12c32e153029f47bb665b',
  'δι’ διαφοράν ἀνθρώπῳ ἢ τῶν ἄλλων ζῴων φησί· καὶ ταῖς μὲν διαφόροις χήματα φύσιως δίδωσιν ἢ μορφαί, ὁπόσας ἢ '
  'χειρῶνιος καὶ ὁρατὴ φύσις κειλόντος ἐγέννησε Θεός, τῷ δὲ τὸ Θεοειδὲς καὶ Θεοεικλον καὶ πάντα πρὸς ἐκείνην '
  'ἀππρεβωμένον τὴν πρωτότυπον τὸ πατρὸς ἢ μονογενῆ εἰκόνα, καὶ πῶς τῷτο λέγει ὁ κυδιος, ἐπισκοπτήσιν.',
  'ὅτι διαφορὰν ἀνθρώπου καὶ τῶν ἄλλων ζῴων φησί· καὶ τοῖς μὲν διάφορα χήματα φύσεως δίδοται καὶ μορφαὶ, ὁπόσας ἡ '
  'χειρῶνιος καὶ ὁρατὴ φύσις κελεύοντος ἐγέννησε θεοῦ, τῷ δὲ τὸ θεοειδὲς καὶ θεοείκελον καὶ πάντα πρὸς ἐκείνην '
  'ἀπηκριβωμένον τὴν πρωτότυπον τοῦ πατρὸς καὶ μονογενῆ εἰκόνα, καὶ πῶς τοῦτο λέγει ὁ ἅγιος, ἐπισκοπητέον.',
  'L6',
  [],
  [('χήματα',
    'σχήματα',
    'The compact initial σχ group remains unresolved; possible σχήματα and original χήματα remain explicit.'),
   ('χειρῶνιος καὶ ὁρατὴ',
    'χερσαῖος καὶ ὑγρὰ',
    'The compact adjective types and endings in this phrase remain uncertain; possible χερσαῖος καὶ ὑγρὰ or '
    'χερσαία καὶ ὑγρὰ and original χειρῶνιος καὶ ὁρατὴ remain explicit.')]),
 (28,
  7,
  '0572e67c2e3971d7680ffbf41f11b0c457590219c8676bd7ce4a8254892d9283',
  'ὅτι φησὶ Φωιδιᾶν τὸν ἀγαλματοποιὸν τὸ Πασαῖον εἴδωλον ποιήσαντα ἐξ ἐλέφαντος προσάξαι Ἰλαίων ἐμπροσθεν τὸ '
  'ἀγάλματος ἐκλείειν, ὡς ἀδύνατον ἐξ ὁμραμὶν αὐτὸ φυλάσσαιθ.',
  'ὅτι φησὶ Φειδίαν τὸν ἀγαλματοποιὸν τὸ Πισαῖον εἴδωλον ποιήσαντα ἐξ ἐλέφαντος προστάξαι ἔλαιον ἔμπροσθεν τοῦ '
  'ἀγάλματος ἐγχέειν, ὡς ἀδύνατον ἐξ ὁμραμὶν αὐτὸ φυλάσσαιθ.',
  'R1',
  [],
  [('ἐξ ὁμραμὶν',
    'ἐξ ὑγραμῶν',
    'The compact prepositional phrase cannot be securely resolved; possible ἐξ ὑγραμῶν or ἐξ ὑγιερῶν and original '
    'ἐξ ὁμραμὶν remain explicit. No ivory-conservation explanation supplies the source word.'),
   ('φυλάσσαιθ',
    'φυλάσσεσθαι',
    'The compact verb ending is unclear, including σθ/θ; possible φυλάσσεσθαι or φυλάσσεθαι and original '
    'φυλάσσαιθ remain explicit.')]),
 (28,
  8,
  'f8e946693377fb9e7b93329eaab66b299f9ccc525b729b33845c8ad88e79bb0c',
  'ὅτι φησίν, Ὁ διάβολος ἐκὶ πνεῦμα περὶ τὴν ἑλὴν γεγόνυον ὑπὸ τῷ θεῷ, καθάπερ ἡ Ἀθηναῖορα ἐλέχθη, ὡσπερ δὴ καὶ '
  'οἱ λοιποὶ γεγόνασιν ὑπ’ αὐτῷ ἄγγελοι, καὶ τὴν ἐπὶ τῇ ἑλῃ κ τοὺς τῆς ἑλῆς εἴδεισι πειπειμένον διοίκοσιν. τούτων '
  'γὰ ἡ [τῶν ἀγγέλων] σύςασις τῷ θεῷ ἐπὶ προνοία γεγονυίας τοὺς ὑπ’ αὐτῷ διακικοασμῆνοισ, ἵνα τὴν μὲν παντελικὴν '
  'καὶ γνησίαν ὁ θεὸς ἔχων τῶν ὅλων πρόνοιαν ἢ τὸ κῦρος καὶ τὸ κράτος ἀπάντων αὐτὸς ἀνῃρημένος, ἀλλ’ οἱ μὲν '
  'λοιποί, ἐφ’ ὧν αὐτὸς ἐποίησε κ διέταξεν ὁ θεός, ἑμι- 5 ταν’ αὐτὸς δὲ ἐνέθρισε κ ποτρεψε περὶ τὴν τῶν '
  'πεπειευμένων ἐγένετο διοίκησιν, φθόνον ἐχυσσῆσας καθ’ ἡμῶν, ὡσπερ καὶ οἱ μετὰ ταῦτα σαρκῶν ἐραδέντες καὶ ταὶς '
  'τῶν ἀνθρώπων εἰς φιλοτισίαν ὁμιλήσαντες 909 R. Συναγράσων. αὐθαίρετον γὰ κ’ αὐτοὶς ἔχειν πρὸς ἐκάστερα '
  'διετάξατο βούλεσιν ὁ θεός, οἷα καὶ ἐπὶ τῶν ἀνθρώπων. καὶ πῶς τὲτο ληπτέον;',
  'ὅτι φησίν, Ὁ διάβολός ἐστι πνεῦμα περὶ τὴν ὕλην γενόμενον ὑπὸ τοῦ θεοῦ, καθάπερ καὶ Ἀθηναγόρᾳ διελέχθη, ὥσπερ '
  'δὴ καὶ οἱ λοιποὶ γεγόνασιν ὑπ’ αὐτοῦ ἄγγελοι, καὶ τὴν ἐπὶ τῇ ὕλῃ καὶ τοῖς τῆς ὕλης εἴδεσι καταμερισμένον '
  'διοίκησιν. τούτων γὰρ ἡ [τῶν ἀγγέλων] σύστασις τῷ θεῷ ἐπὶ προνοίᾳ γεγονέναι τοῖς ὑπ’ αὐτῷ διακεκοσμημένοις, '
  'ἵνα τὴν μὲν παντελικὴν καὶ γενικὴν ὁ θεὸς ἔχων τῶν ὅλων πρόνοιαν καὶ τὸ κῦρος καὶ τὸ κράτος ἁπάντων αὐτὸς '
  'ἀνῃρημένος, ἀλλ’ οἱ μὲν λοιποὶ, ἐφ’ ὧν αὐτοὺς ἐποίησε καὶ διέταξεν ὁ θεός, ἔμειναν· αὐτὸς δὲ ἐνύβρισε καὶ '
  'πονηρῶς περὶ τὴν τῶν πεπιστευμένων ἐγένετο διοίκησιν, φθόνον ἐχυσσῆσας καθ’ ἡμῶν, ὥσπερ καὶ οἱ μετὰ ταῦτα '
  'σαρκῶν ἐραδέντες καὶ ταῖς τῶν ἀνθρώπων εἰς φιλοτεκνίαν ὁμιλήσαντες θυγατράσιν. αὐθαίρετον γὰρ καὶ αὐτοῖς ἔχειν '
  'πρὸς ἑκάτερα διετάξατο βούλησιν ὁ θεὸς, οἷα καὶ ἐπὶ τῶν ἀνθρώπων. καὶ πῶς τοῦτο ληπτέον;',
  'R2',
  [],
  [('[τῶν ἀγγέλων]',
    '[τῶν ἀγγέλων]',
    'The scan prints this bounded phrase in square brackets in the body. Brackets alone do not establish '
    'editorial authorship. Preserve the bracketed source reading while retaining original display and excluding '
    'this exact uncertain span from lexical admission.'),
   ('ἐχυσσῆσας',
    'ἐγκαστήσας',
    'The compact internal types and accent remain unclear; possible ἐγκαστήσας or ἐγκαστῆσας and original '
    'ἐχυσσῆσας remain explicit.'),
   ('ἐραδέντες',
    'ἐρασθέντες',
    'The compact internal σθ/θ group is unresolved; possible ἐρασθέντες or ἐραθέντες and original ἐραδέντες '
    'remain explicit. No sigma is supplied from grammar.')]),
 (28,
  9,
  'a47b16db791acefc05eaa8df690169b101e9b1ed3d94c1c8244c839a1c0226d3',
  'ὅτι δεσμανίνως χιτῶνας τὴν θάνατόν φησι. λέγει. γὰ περὶ τὸ Ἀδάμ, ὃν ὁ θεὸς ὁ παντοκράτωρ ἀθάνατὸν κακὸν ἐξ '
  'ἐπιβληῆς ἰδὼν γεγεννημένον, “καθάπερ ἔδει H. 5 καὶ ὁ πλανήσας αὐτὸν διάβολος ἤν, τὸς δεσμανίνως χιτῶνας διὰ '
  'τὸτο κατεσκιώσιν, οἷον εἰ νεκρότητι περιβαλὼν αὐτόν, ὅπως διὰ τῆς λύσεως τῷ σώματος πᾶν τὸ ἐν αὐτῷ γεννηθέν. '
  'κακὸν ἀποθάνη.',
  'ὅτι δερματίνους χιτῶνας τὸν θάνατόν φησι. λέγει γὰρ περὶ τοῦ Ἀδὰμ, ὃν ὁ θεὸς ὁ παντοκράτωρ ἀθάνατον κακὸν ἐξ '
  'ἐπιβουλῆς ἰδὼν γεγενημένον, καθάπερ καὶ ὁ πλανήσας αὐτὸν διάβολος ἦν, τοὺς δερματίνους χιτῶνας διὰ τοῦτο '
  'κατασκευάσαι, οἷον ἐν νεκρότητι περιβαλὼν αὐτὸν, ὅπως διὰ τῆς λύσεως τοῦ σώματος πᾶν τὸ ἐν αὐτῷ γεννηθὲν κακὸν '
  'ἀποθάνῃ.',
  'R3',
  [],
  []),
 (28,
  10,
  'e140aee0079e25b0bf934ace1684b45e1b1106df8f9beb428347002637f511f0',
  'ὅτι δὲ ἀποκάλυψις φησὶ γεγονέναι τῷ ἁγίῳ Παύλω, λέγει γὰρ, Ἀλλ’ ἰδε ὁ ἀπόστολος ὑποτίθεται εἰναι τὸν '
  'παράδεισον ἐν τῷ τρίτῳ ὧρανῷ τοὺς λεπτῶν ἀκροῶ.β λόγων ἐπισκεμένοις. „οἶδα” γὰ „τὸν τοιούτον ὧραγεῖντα ἕως '
  'τρίτα ὧρανῷ” λέγων „καὶ οἶδα τὸν τοιούτον ἄνθρωπον, εἴτε ἐν σώματι εἴτε χωρὶς τοῦ σώματος, ὁ 5 θεὸς οἶδεν, ὅτι '
  'ἁρπάγη εἰς τὸν παράδεισον” ὅδο ἀποκάλυψις μεγάλας ἰσχυχνάται μηνύει, δις ἀναληφθεὶς ἐπαργῶς, ἅπαξ μὲν ἕως '
  'τρίτα ὧρανῷ, ἅπαξ δ’ εἰς τὸν παράδεισον. τὸ γὰ „οἶδα ἀφραγεῖντα τὸν τοιούτον ἕως τρίτα ὧρανῷ” ἰδίως ἀποκάλυψιν '
  'αὐτῷ κατὰ τὸν τρίο τον ὧρανὸν πεφηνέναι συνίησιν· τὸ δὲ „κ’ οἶδα” πάλιν ἐπιφερόμενον „τὸν τοιούτον ἄνθρωπον, '
  'εἴτε ἐν σώ-',
  'ὅτι δύο ἀποκαλύψεις φησὶ γεγονέναι τῷ ἁγίῳ Παύλῳ, λέγει γὰρ, Ἀλλ’ οὐδὲ ὁ ἀπόστολος ὑποτίθεται εἶναι τὸν '
  'παράδεισον ἐν τῷ τρίτῳ οὐρανῷ τοῖς λεπτῶν ἀκρίβειαν λόγων ἐπεσκεμμένοις. „οἶδα“ γὰρ „τὸν τοιοῦτον ἁρπαγέντα '
  'ἕως τρίτου οὐρανοῦ“ λέγων „καὶ οἶδα τὸν τοιοῦτον ἄνθρωπον, εἴτε ἐν σώματι εἴτε χωρὶς τοῦ σώματος, ὁ θεὸς '
  'οἶδεν, ὅτι ἡρπάγη εἰς τὸν παράδεισον“ δύο ἀποκαλύψεις μεγάλας ἰσχυχνάται μηνύει, δὶς ἀναληφθεὶς ἐναργῶς, ἅπαξ '
  'μὲν ἕως τρίτου οὐρανοῦ, ἅπαξ δ’ εἰς τὸν παράδεισον. τὸ γὰρ „οἶδα ἁρπαγέντα τὸν τοιοῦτον ἕως τρίτου οὐρανοῦ“ '
  'ἰδίαν ἀποκάλυψιν αὐτῷ κατὰ τὸν τρίτον οὐρανὸν πεφηνέναι συνίστησιν· τὸ δὲ „καὶ οἶδα“ πάλιν ἐπιφερόμενον „τὸν '
  'τοιοῦτον ἄνθρωπον, εἴτε ἐν σώ-',
  'R4',
  [{'start': 671,
    'end': 674,
    'text': 'σώ-',
    'side': 'trailing',
    'qualification': 'Incomplete printed word continuing on the next physical page; it is not an independent '
                     'lexical token and no completion is supplied.'}],
  [('ἰσχυχνάται',
    'ἐσχηκέναι',
    'The compact initial σχ group and ending are unresolved; possible ἐσχηκέναι or ἐχηκέναι and original '
    'ἰσχυχνάται remain explicit. The apostolic quotation is not restored from memory.')])]

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
