"""Complete direct source review of retained passages on Bekker printed308.

Every retained paragraph and both column boundaries were inspected. Unreadable
quotation and compact ligatures remain explicit instead of scriptural restoration.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:28:43.129222+00:00'
_CROPS = {'L':[.205,.10,.61,.755], 'R':[.55,.10,.95,.755]}
_SPECS = [(43,
  1,
  'fc88a27aa58b0937330201cad53f5ee1faea08335f2554a8491fdb303599572d',
  'τότε. καὶ γενόμενος ὁ ἄνθρωπος ἐντολὴν λαμβάνει παρὰ τοῦ Θεοῦ, ἥ ἐντεῦθεν ἤδη τὸ κακὸν ἄρχει· ἡ μὲν πειθὼ τῷ '
  'Σαῖφ προστάγματι. καὶ τοῦτο μὲν μόνον ἦν τὸ κακόν, ἡ παρακοή, ἥτις τῷ εἶναι ἤρξατο.',
  'τότε. καὶ γενόμενος ὁ ἄνθρωπος ἐντολὴν λαμβάνει παρὰ τοῦ θεοῦ, καὶ ἐντεῦθεν ἤδη τὸ κακὸν ἄρχει· τὸ γὰρ μὴ ἡ '
  'μὲν πειθὼ τῷ θείῳ προστάγματι. καὶ τοῦτο καὶ μόνον ἦν τὸ κακὸν, ἡ παρακοὴ, ἥτις τῷ εἶναι ἤρξατο.',
  'L',
  [],
  [('ἄρχει',
    'ἔρχεται',
    'The compact verb ending is unresolved; possible ἔρχεται or ἄρχεται and exact original remain explicit.'),
   ('ἡ μὲν πειθὼ',
    'μὴ πείθεσθαι',
    'The compact σθ/θ group and short words remain unresolved; possible μὴ πείθεσθαι or μὴ πείθεθαι and exact '
    'original remain explicit.')]),
 (43,
  2,
  'b8ac6a768bee7fced553df7f45899c3b3a08270fdbb6665e6709af340cffa5a9',
  "Ἀνεγνώσθη τῇ αὐτῇ ἐκ τῶ περὶ ἀγνείας, ὡς κ' ἐν ὁμοίῳ συνόντως ἐξῆδόθη τύπω.",
  'Ἀνεγνώσθη τῷ αὐτῷ ἐκ τοῦ περὶ ἁγνείας, ὃς καὶ ἐν ὁμοίῳ συντόμως ἐξεδόθη τύπῳ.',
  'L',
  [],
  [('Ἀνεγνώσθη',
    'Ἀνεγνώσθη',
    'The compact heading σθ/θ group remains unresolved; possible Ἀνεγνώσθη or Ἀνεγνώθη remain explicit.')]),
 (43,
  3,
  '863f11260d5291fc3293eb51773418509d502e76d6c85546c9604bc72e7428ea',
  'ὅτι φησίν, Ὁ γὰν Ἀβραὰμ πρῶτος ἐν διαθήκῃ τὴν περιτομὴν λαβὼν οὐδὲν ἔτιρον αἰνίττεσθαι δοκεῖ, τῷ οἰκείῳ '
  'ἀποτιμωμένους τῆς σαρκὸς αὐτῷ μέλος, ἡ ἰο τούτο, τὸ μηχὲι εἰς τὴν ἐκ τῶ αὐτῆ σήματος σάρκα δημιουργηθεῖσαν '
  'παιδοπορίαν ἐπιτελεῖν, ἀνὸ τῆς ἰδίας ἕκαστον διδάσκων ἀδελφὴς οἱ σαρκὸς ἀποτέμεναι τὴν κατὰ συνοσίαν ἡδονήν.',
  'ὅτι φησὶν, Ὁ γὰρ Ἀβραὰμ πρῶτος ἐν διαθήκῃ τὴν περιτομὴν λαβὼν οὐδὲν ἕτερον αἰνίττεσθαι δοκεῖ, τῷ οἰκείῳ '
  'ἀποτιμωμένους τῆς σαρκὸς αὐτῷ μέλος, ἢ τοῦτο, τὸ μηκέτι εἰς τὴν ἐκ τοῦ αὐτοῦ αἵματος σάρκα δημιουργηθεῖσαν '
  'παιδοποιΐαν ἐπιτελεῖν, ἀπὸ τῆς ἰδίας ἕκαστον διδάσκων ἀδελφὴς οἱ σαρκὸς ἀποτέμνειν τὴν κατὰ συνουσίαν ἡδονήν.',
  'L',
  [],
  [('αἰνίττεσθαι',
    'αἰνίττεσθαι',
    'The compact σθ/θ group remains unresolved; possible αἰνίττεσθαι or αἰνίττεθαι remain explicit.'),
   ('ἀποτιμωμένους',
    'ἀποτεμνόμενος',
    'The compact participial ending remains unresolved; possible ἀποτεμνόμενος or ἀποτεμνομένους and exact '
    'original remain explicit.'),
   ('ἀδελφὴς οἱ σαρκὸς',
    'ἀδελφῆς οἷα σαρκὸς',
    'The compact words after ἀδελφῆς remain unresolved; possible ἀδελφῆς οἷα σαρκὸς and exact original are '
    'retained without interpreting the kinship claim.')]),
 (43,
  4,
  'c3eb97d1b968064f71d8f1eacd0320ed34199252763d240aae3e23642382f917',
  'ὅτι φησίν, Ἐγὼ γὰρ καθειρωκέναι μοι δοκεῖ σαφῶς ὑπὸ τῶν γραφῶν, ὅτι παρθενίας ἤδοῦσης ὁ λόγος ἐκ ἀνείλε πάντῃ '
  'τεκνογονίαν. ἡ γὰρ ἐπειδὴ τῶν ἀξρῶν ἡ σελήνη μικρὸν ἔχει, παρὰ τοῦτο τῶν ἀλλων ἀστέρων τὸ φῶς ἀναμείει, ἡ '
  "παυδὴ τῶν ἄλλων ἐστὶ γλυκύτερον τὸ μέλι κ' ἡδύτερον, τὰ λοιπὰ πικρὰ κ' ἀνίδονα νομιεῖον.",
  'ὅτι φησὶν, Ἐγὼ γὰρ καθεωρακέναι μοι δοκῶ σαφῶς ἀπὸ τῶν γραφῶν, ὅτι παρθενίας ἐλθούσης ὁ λόγος οὐκ ἀνεῖλε πάντῃ '
  'τεκνογονίαν. οὐ γὰρ ἐπειδὴ τῶν ἄστρων ἡ σελήνη μείζων ἐστὶ, παρὰ τοῦτο τῶν ἄλλων ἀστέρων τὸ φῶς ἀναμείει, ἢ '
  'ἐπειδὴ τῶν ἄλλων ἐστὶ γλυκύτερον τὸ μέλι καὶ ἥδιον, τὰ λοιπὰ πικρὰ καὶ ἀνήδονα νομιστέον.',
  'L',
  [],
  [('ἀναμείει',
    'ἀναιρεῖται',
    'The compact verb letters and ending are unresolved; possible ἀναιρεῖται or ἀναμενεῖ and exact original '
    'remain explicit.')]),
 (43,
  5,
  'e5e56824e1b1b89c1737c0d529b23cbc956f6eaa2e4a2caf156874daee7aac01',
  '232R. "ὅτι τὸ "τίκνα δὲ μοιχῶν ἀπελεοφόρηται" περὶ τῶν τὴν ἀλήθειαν μοιχομένων φησιν· εἰρήση, οὕτεκως '
  'κλεψίσωροι, νοθεύοντες τὰς γραφάς, ἀπελεοφόρητον γεννήσει σοφίαν, τῇ Θεοστίμῳ συγχαίροντες τὴν πλάνην. ἄλλως '
  "γὰρ νοηθῆναι οὐκ ἐχώρει. οὔτε γὰρ ἐπὶ τῷ μὴ τίκτειν τὰ ἐκ μοιχείας τέκνα κ' εἰς φῶς ἀλθτὸν ἄγγελθ δυναῖ νοεῖν, "
  "ὅτι πολλοὶ ὁ μόνον ἐτεξήθησαν ἀλλὰ καὶ τετράχσαν ἐκ μοιχείας τεχθέντες, ὅτε 504H.ἐπὶ τὸ πνευματικῶς κ' θείως "
  '"τελειοφορηθῆναι" πολλῶν γὰρ μοιχῶν τέκνα πλήρη ἐγίνοντο ἁγίου πνεύματος.',
  'ὅτι τὸ „τέκνα δὲ μοιχῶν ἀτελεσφόρητα“ περὶ τῶν τὴν ἀλήθειαν μοιχωμένων φησὶν εἰρῆσθαι, οἵτινες κλεψίφρονες, '
  'νοθεύοντες τὰς γραφὰς, ἀτελεσφόρητον γεννῶσι σοφίαν, τῇ Θεοστίμῳ συγχαίροντες τὴν πλάνην. ἄλλως γὰρ νοηθῆναι '
  'οὐκ ἐγχωρεῖ. οὔτε γὰρ ἐπὶ τῷ μὴ τίκτειν τὰ ἐκ μοιχείας τέκνα καὶ εἰς φῶς αἰσθητὸν ἄγγελθ δυναῖ νοεῖν, ὅτι '
  'πολλοὶ οὐ μόνον ἐτεξήθησαν ἀλλὰ καὶ τετόκασιν ἐκ μοιχείας τυχθέντες, οὔτε ἐπὶ τῷ πνευματικῶς καὶ θείως '
  '„τελεσφορηθῆναι“· πολλῶν γὰρ μοιχῶν τέκνα πλήρη ἐγένοντο ἁγίου πνεύματος.',
  'L',
  [],
  [('Θεοστίμῳ',
    'θεοστυγίᾳ',
    'The compact noun types are unresolved; possible θεοστυγίᾳ or θεοσεβείᾳ and exact original remain explicit.'),
   ('τίκτειν',
    'τίκτεσθαι',
    'The compact σθ/θ group remains unresolved; possible τίκτεσθαι or τίκτεθαι and exact original remain '
    'explicit.'),
   ('ἄγγελθ',
    'ἄγεσθαι',
    'The compact σθ/θ group remains unresolved; possible ἄγεσθαι or ἄγεθαι and exact original remain explicit.'),
   ('δυναῖ',
    'δύναται',
    'The compact verb ending is unresolved; possible δύναται or δύναιτο and exact original remain explicit.'),
   ('νοεῖν',
    'νοεῖσθαι',
    'The compact σθ/θ group remains unresolved; possible νοεῖσθαι or νοεῖθαι and exact original remain explicit.'),
   ('ἐτεξήθησαν',
    'ἐτέχθησαν',
    'The compact verb consonant group remains uncertain; possible ἐτέχθησαν or ἐτέθησαν and exact original remain '
    'explicit.')]),
 (43,
  6,
  '0effac173b189cc1d1bdc713c4ec8ca88170c50f2a6d80cbb4f04e0f544e82f2',
  "ὅτι ἀπορεῖ λέγων, εἰ παρὰ Θεοῦ δίδοντ' αἱ ψυχαὶ ἀλλ' ὁ παρὰ τῷ πατρὸς τοῖς τικτομένοις, πῶς δίδωσι καὶ τοῖς ἐκ "
  'μοιχείας τικτομένοις; εἰ γὰρ δίδωσι, συνφορεῖν ἂν δόξειν τοῖς μοιχομένοις· εἰ γὰρ μὴ ἔδωκε τὴν ψυχήν, οὐκ ἂν '
  'ἐτάκτοντο. λέει δὲ τὴν ἀπορίαν διὰ πλειόνων καὶ σαφῶν παραδειγμάτων.',
  "ὅτι ἀπορεῖ λέγων, εἰ παρὰ θεοῦ δίδοντ' αἱ ψυχαὶ ἀλλ’ οὐ παρὰ τῶν πατρῶν τοῖς τικτομένοις, πῶς δίδωσι καὶ τοῖς "
  'ἐκ μοιχείας τικτομένοις; εἰ γὰρ δίδωσι, συνεργεῖν ἂν δόξειεν τοῖς μοιχωμένοις· εἰ γὰρ μὴ ἔδωκε τὴν ψυχὴν, οὐκ '
  'ἂν ἐτέκτοντο. λύει δὲ τὴν ἀπορίαν διὰ πλειόνων καὶ σαφῶν παραδειγμάτων.',
  'L',
  [],
  [("δίδοντ'",
    'δίδονται',
    'The compact verb ending is unresolved; possible δίδονται or δίδοντο and exact original remain explicit.')]),
 (43,
  7,
  '1843c59d6ec32a83b52daa43b27785fc7a85ec232df03a869fbdbf57c478a29c',
  'ὅτι τὰ ἐν τῇ Γενέσει γερόμενα, οἷον τὸ "τοῦτο ἂν δροῦν ἐκ τῶν ὀστῶν μου καὶ σάρξ ἐκ τῶν σαρκῶν μου αὕτη '
  "κληθήσετ' γυνή, ὅτι ἐκ τοῦ ἀνδρὸς αὐτῆς ἐλήφθη· ἔντεκεν τούτο καταλείψει ἄνθρωπος τὸν πατέρα αὐτῶ κ' τὴν "
  "μητέρα, καὶ προσκαλληθήσετ' τῇ γυναικὶ αὐ-",
  "ὅτι τὰ ἐν τῇ Γενέσει φερόμενα, οἷον τὸ „τοῦτο ἐκ τῶν ὀστέων μου καὶ σὰρξ ἐκ τῶν σαρκῶν μου· αὕτη κληθήσετ' "
  'γυνὴ, ὅτι ἐκ τοῦ ἀνδρὸς αὐτῆς ἐλήφθη· ἕνεκεν τούτου καταλείψει ἄνθρωπος τὸν πατέρα αὐτοῦ καὶ τὴν μητέρα, καὶ '
  "προσκαλληθήσετ' τῇ γυναικὶ αὐ-",
  'L',
  [{'start': 243,
    'end': 246,
    'text': 'αὐ-',
    'side': 'trailing',
    'qualification': 'Printed incomplete word continued at top of facing column; no completion inferred.'}],
  [("κληθήσετ'",
    'κληθήσεται',
    'The compact ending is uncertain; possible κληθήσεται or κληθήσεσθαι and exact original remain explicit.'),
   ("προσκαλληθήσετ'",
    'προσκολληθήσεται',
    'The compact consonants and ending are uncertain; possible προσκολληθήσεται or προσκολληθήσεσθαι and exact '
    'original remain explicit.')]),
 (43,
  8,
  '310d71596d7bc03e2653faa6b704fbfc3bfb7b3aa5e02ff03dba53e3b57b3c7d',
  'τοῦ, καὶ Ἰσού) οἱ δύο εἰς σάρκα μίαν,” ταῦτα οὖν οἱ κατὰ τὸ γράμμα φησὶ δεῖν μόνον νοεῖν, ἀλλὰ καὶ πνευματικῶς '
  'εἰς Χριστὸν καὶ εἰς τὴν ἐκκλησίαν. καὶ φησὶν ὅτι κ δ ὅσιος Παῦλος μετὰ τὴν τῶν φησι τῶν τάτων ἔκθεσιν λέγει '
  '„τὸ μυστήριον τοῦτο μέγα ἐστίν, λέγω δ’ ἐγὼ εἰς Χριστὸν καὶ εἰς τὴν ἐκκλησίαν.” ἀλλὰ καὶ τὸ „αὐξάνεσθε κ '
  'πληθύνεσθε” οὐχ ἕνεκα τῶν ἐκ σπέρματος καὶ μίξεως γεννωμένων ἀνθρώπων καὶ σιτίοις αὐξανομένων φησὶν εἰρηθῆναι '
  'μόνον, ἀλλὰ καὶ ὁ περὶ τῶν κατὰ πνεῦμα τελειωμένων καὶ γεννωμένων, καθὼς κ Παῦλος βοᾷ, τέκνα καλῶν τὰς ἑαυτῶ '
  'αὐτοῦ γεννηθέντας· „τέκνα” γὰρ φησιν „εἰς πάλιν ὁδίλω, ὅπως κ Χριστὸς ἐν ὑμῖν μορφωθῇ” κ πάλιν „ἐν γ’ Χριστῷ '
  'Ἰησοῦ διὰ τοῦ εὐαγγελίου ἐγὼ ὑμᾶς ἐγέννησα.”',
  'τοῦ, καὶ Ἰσού) οἱ δύο εἰς σάρκα μίαν,“ ταῦτα οὖν οὐ κατὰ τὸ γράμμα φησὶ δεῖν μόνον νοεῖν, ἀλλὰ καὶ πνευματικῶς '
  'εἰς Χριστὸν καὶ εἰς τὴν ἐκκλησίαν. καὶ φησιν ὅτι καὶ ὁ θεῖος Παῦλος μετὰ τὴν τῶν ῥητῶν τούτων ἔκθεσιν λέγει '
  '„τὸ μυστήριον τοῦτο μέγα ἐστὶ, λέγω δ’ ἐγὼ εἰς Χριστὸν καὶ εἰς τὴν ἐκκλησίαν.“ ἀλλὰ καὶ τὸ „αὐξάνεσθε κ '
  'πληθύνεσθε” οὐχ ἐπὶ τῶν ἐκ σπέρματος καὶ μίξεως γεννωμένων ἀνθρώπων καὶ σιτίοις αὐξανομένων φησὶν εἰρηθῆναι '
  'μόνον, ἀλλὰ καὶ περὶ τῶν κατὰ πνεῦμα τελειουμένων καὶ γεννωμένων, καθὼς καὶ Παῦλος βοᾷ, τέκνα καλῶν τοὺς '
  'ἑαυτοῦ δι’ αὐτοῦ γεννηθέντας· „τέκνα“ γάρ φησιν „οὓς πάλιν ὠδίνω, ἕως ὁ Χριστὸς ἐν ὑμῖν μορφωθῇ“ καὶ πάλιν „ἐν '
  'γὰρ Χριστῷ Ἰησοῦ διὰ τοῦ εὐαγγελίου ἐγὼ ὑμᾶς ἐγέννησα.“',
  'R',
  [{'start': 0,
    'end': 3,
    'text': 'τοῦ',
    'side': 'leading',
    'qualification': 'Printed continuation of αὐ- from preceding column; incomplete word retained as a '
                     'fragment.'}],
  [('Ἰσού)',
    'ἔσονται',
    'The compact verb ending is unresolved; possible ἔσονται or ἔσονθαι and exact original remain explicit.'),
   ('νοεῖν',
    'νοεῖσθαι',
    'The compact σθ/θ group remains unresolved; possible νοεῖσθαι or νοεῖθαι and exact original remain explicit.'),
   ('„αὐξάνεσθε κ πληθύνεσθε”',
    '„αὐξάνεσθε καὶ πληθύνεσθε“',
    'The compact σθ/θ group remains unresolved; this tentative scan reading and exact original are retained, with '
    'sigma-bearing and sigma-less alternatives explicit.'),
   ('εἰρηθῆναι',
    'εἰρῆσθαι',
    'The compact σθ/θ group remains unresolved; possible εἰρῆσθαι or εἰρῆθαι and exact original remain '
    'explicit.')]),
 (43,
  9,
  'da64530709544029d8bd6090b095d20101cf254d9b681d4fcb6ef75e2e8072e4',
  'ὅτι τὸ ἐν τοῖς εὐαγγελίοις εἰρημένον παραβολικῶς „εἰς ἐστιν ἐξ ὑμῶν ἄνθρωπος ὃς ἔχει ἑκατὸν πρόβατα καὶ '
  'ἀπολέσας ἕν ἐξ αὐτῶν” καὶ ἐξῆς, ἐνενήκοντα ἐννέια μὲν πρόβατα τὰς οὐρανίας δυνάμεις φησὶν ἐκδιχῶς χρή, ἐν δὲ '
  'τὸ ἀπολωλὸς τὸν ἄνθρωπον ἢ γὰρ τὴν ἀνθρωπίναν φύσιν, ὃν ἦν καὶ κατελθόντων τὸν λόγον τοῦ πατρὸς ἐκ τῶν '
  'οὐρανῶν.',
  'ὅτι τὸ ἐν τοῖς εὐαγγελίοις εἰρημένον παραβολικῶς „τίς ἐστιν ἐξ ὑμῶν ἄνθρωπος ὃς ἔχει ἑκατὸν πρόβατα καὶ '
  'ἀπολέσας ἓν ἐξ αὐτῶν“ καὶ ἐξῆς, ἐνενήκοντα ἐννέα μὲν πρόβατα τὰς οὐρανίους δυνάμεις φησὶν ἐκδιχῶς χρῆν, ἓν δὲ '
  'τὸ ἀπολωλὸς τὸν ἄνθρωπον ἤγουν τὴν ἀνθρωπείαν φύσιν, δι’ ἣν καὶ κατεληλυθέναι τὸν λόγον τοῦ πατρὸς ἐκ τῶν '
  'οὐρανῶν.',
  'R',
  [],
  [('ἐκδιχῶς',
    'ἐκδέχεσθαι',
    'The compact σθ/θ group and other ending types remain unresolved; possible ἐκδέχεσθαι or ἐκδέχεθαι and exact '
    'original remain explicit.')]),
 (43,
  10,
  '19c54b9dd4437aafbea2c03000654440923dff4657b99f98c72daa8b2470f828',
  'ὅτι τὸ „ἐκ τῶν ποταμῶν Βαβυλῶνος” κ ἐξῆς αἱ ψυχαὶ φησὶ λέγονται. ἔχον γὰρ ὄργανα καλῶσα τὰ σκηνώματα ἑαυτῶν, ἐ '
  'ἐκρίμασαν ἀπὸ τῶν πνευματῶν τῆς ἀγνείας ἐξάψασαι τὸ ξύλον, ἵνα μὴ δυνηθῶσιν ἐξαπαλαίψωσι πάλιν παρασυνήγαι τῷ '
  'θεῖματε τῆς ἀκρασίας· Βαβυλὼν γὰρ, τάραχος ἢ σύγχυσις ἑρμηνευομένη, τὸν περίφροτον βίον δείκνυσι τῶν, ἐν μέσῳ '
  'καθεστῶτας περιελυζόμεθα τῶν ποταμῶν τῆς κακίας ἐφορμῶντων. διὸ κ βοῶμεν μετὰ κλυνθμοῦ πρὸς τὸν θεόν, ἵνα μὴ '
  'κατολιθήσωσιν ἡμῶν ἀποδραχθέντα τοῖς κήμασι τῆς ἁδονῆς ἀπὸ τῆ φωτὶ τῆς ἀγνείας τὰ ὄργανα. ἐν τούτῳ γὰρ τῆς '
  'παρθενίας τὴν ἰτίαν πανταχῇ παραλαμβάνουσιν αἱ γραφαί, ἐπειδὴ περ τὸ ἄνθος αὐτῆς εἰς ἕδωρ ἀποτρίβειν ἀν ποῇ, '
  'πᾶν δσον εἰς ὀχείας ἀναλῆ καὶ ἱριδισμοῦς ἀποσβέννυσιν, ἵστ’ ἄν εἰς ἕδην ἀποσφύρωσιν τὴν ἐπὶ παιδοποιίαν φορὰν, '
  'ὡσπερ δὴ κ ὁ Ὀμηρος ἐμήνυσιν, διὰ τοῦτο καλῶσα ὠλμοκάπηρος τὰς ἰτίας.',
  'ὅτι τὸ „ἐπὶ τῶν ποταμῶν Βαβυλῶνος“ καὶ ἐξῆς αἱ ψυχαὶ φησὶ λέγουσιν. ἔσχον γὰρ ὄργανα καλέσασαι τὰ σκηνώματα '
  'ἑαυτῶν, ἃ ἐκρέμασαν ἀπὸ τῶν πεισμάτων τῆς ἁγνείας ἐξάψασαι τῷ ξύλῳ, ἵνα μὴ δυνηθῶσιν ἐξαπαλαίψωσι πάλιν '
  'παρασυρῆναι τῷ ῥεύματι τῆς ἀκρασίας· Βαβυλὼν γὰρ, τάραχος καὶ σύγχυσις ἑρμηνευομένη, τὸν περίῤῥυτον βίον '
  'δείκνυσι τοῦτον, ἐν ᾧ μέσῳ καθεστῶτας περιελυζόμεθα τῶν ποταμῶν τῆς κακίας ἐφορμώντων. διὸ καὶ βοῶμεν μετὰ '
  'κλαυθμοῦ πρὸς τὸν θεὸν, ἵνα μὴ κατολιθήσωσιν ἡμῶν ἀποῤῥαγέντα τοῖς κύμασι τῆς ἡδονῆς ἀπὸ τοῦ φυτοῦ τῆς ἁγνείας '
  'τὰ ὄργανα. ἐν τούτῳ γὰρ τῆς παρθενίας τὴν ἰδέαν πανταχῇ παραλαμβάνουσιν αἱ γραφαὶ, ἐπειδή περ τὸ ἄνθος αὐτῆς '
  'εἰς ὕδωρ ἀποτριβὲν ἂν ποθῇ, πᾶν ὅσον εἰς ὀχείας ἀναζεῖ καὶ ἐρεθισμοὺς ἀποσβέννυσιν, ἔστ’ ἂν εἰς ἄρδην '
  'ἀποξηράνῃ τὴν ἐπὶ παιδοποιΐαν φορὰν, ὥσπερ δὴ καὶ ὁ Ὅμηρος ἐμήνυσε, διὰ τοῦτο καλέσας ὠλεσικάρπους τὰς ἰτέας.',
  'R',
  [],
  [('ἐξαπαλαίψωσι',
    'ἐξαρπασθεῖσαι',
    'The compact σθ/θ group remains unresolved; this tentative scan reading and exact original are retained, with '
    'sigma-bearing and sigma-less alternatives explicit.'),
   ('καθεστῶτας',
    'καθεστῶτες',
    'The compact ending remains uncertain; possible καθεστῶτες or καθεστῶτας and exact original remain explicit.'),
   ('περιελυζόμεθα',
    'περικλυζόμεθα',
    'The compact verb letters remain unresolved; possible περικλυζόμεθα or περιεκλυζόμεθα and exact original '
    'remain explicit.'),
   ('κατολιθήσωσιν',
    'κατολισθήσωσιν',
    'The compact σθ/θ group remains unresolved; this tentative scan reading and exact original are retained, with '
    'sigma-bearing and sigma-less alternatives explicit.')]),
 (43,
  11,
  'd2a5b0d0d498d44f50336f241bd42db9a9fcfde7099f1998184643d205e3e095',
  'ὅτι φησίν, Ἀμὴν τὸ μὴ ἐπιδιᾶλῃ νόμησιν τὸν 933 Π κόσμον μηδὲ παράθεσιν τὴν ἐξηδοσμίδια, “λεγόμενον 5511.',
  'ὅτι φησίν, Ἀμὴν τὸ μὴ ἐπιδιᾶλῃ νόμησιν τὸν 933 Π κόσμον μηδὲ παράθεσιν τὴν ἐξηδοσμίδια, “λεγόμενον 5511.',
  'R',
  [],
  [('ὅτι φησίν, Ἀμὴν τὸ μὴ ἐπιδιᾶλῃ νόμησιν τὸν 933 Π κόσμον μηδὲ παράθεσιν τὴν ἐξηδοσμίδια, “λεγόμενον 5511.',
    'ὅτι φησὶν, Ἄμβλω τὸ μὴ ἐπιδιόδασθαι νόμησον τὸν κόσμον μηδὲ παρθένον τὴν ξηλοδοσμίαν λεγόμενον',
    'The final retained two-line quotation is substantially damaged in OCR and its compact printed words cannot '
    'be read securely. This tentative literal scan transcription and exact original remain explicit, including '
    'possible Ἄμβλω/Ἄμβλα and ἐπιδιόδασθαι/ἐπιδιόθεσθαι; no meaning is reconstructed.')])]

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
