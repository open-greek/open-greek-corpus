"""Complete direct source review of retained passages on Bekker printed313.

All retained paragraphs were inspected against the pinned scan. Printed bracketed
words, ambiguous compact types, and uncertain numerals remain explicitly bounded.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:41:50.288483+00:00'
_CROPS = {'L':[.055,.10,.455,.755], 'R':[.395,.10,.815,.755]}
_SPECS = [(48,
  1,
  '1bc62472442d83cbe932aff0940e263d9d5c03f2141013790e200f7eb87fc5d8',
  'μώλωπας ἐκ ἑαυτῶν το βασιλεύειν αὐτῶν, μέχρις ὁ θεὸς τέταρτον κατελεήσας τὸν ἄνθρωπον τὴν ἀγνείαν ἀπέδωκε '
  'βασιλεύειν, ἣν ἡμῖν ὁπολοῦθως ἐκάλεσεν ἡ γραφή· ἔτις καταναλώσασα τὰς ἡδονάς, καὶ ἀμελήσασα λοιπόν, ἢ μὴ αὐτὴ '
  'πεισθῆναι πᾶσιν ἢ ἐν ἀληθείᾳ προσέχουσι, πρὸς καταδυναστεῖν πάντας· ἔπειτα γὰρ μετὰ ταύτην ἔστω νόμος ἢ '
  'διδασκαλία ἐτέρα, ἀλλὰ ἡ κρίσις καὶ πῦρ καὶ διὰ τοῦτο λοιπὸν ἀπ’ ἐντεῦθεν δικαιοπραγῶν ὁ ἄνθρωπος ἔχεται καὶ '
  'πεισθῆναι βεβαίως τῷ θεῷ καὶ ἀποχρίναι τῷ διαβόλῳ.',
  'μώλωπας οὐκ ἐβούλοντο βασιλεύειν αὐτῶν, μέχρις ὁ θεὸς τέταρτον κατελεήσας τὸν ἄνθρωπον τὴν ἁγνείαν προσέδωκε '
  'βασιλεύειν, ἣν ῥάμνον ἀκολούθως ἐκάλεσεν ἡ γραφή· ἥτις καταναλώσασα τὰς ἡδονὰς, καὶ ἀπειλήσασα λοιπὸν, ἢ μὴ '
  'αὐτὴ πεισθῆναι πᾶσιν καὶ ἐν ἀληθείᾳ προσέχοιντο, πυρὶ καταδυναστεύσειν πάντας· οὐκέτι γὰρ μετὰ ταύτην ἔστω '
  'νόμος ἢ διδασκαλία ἑτέραν, ἀλλὰ καὶ κρίσιν καὶ πῦρ καὶ διὰ τοῦτο λοιπὸν ἀπ’ ἐντεῦθεν δικαιοπραγῶν ὁ ἄνθρωπος '
  'ἤρξατο καὶ πειθαρχεῖν βεβαίως τῷ θεῷ καὶ ἀποχρίναι τῷ διαβόλῳ.',
  'L',
  [],
  [('ἢ μὴ αὐτὴ πεισθῆναι πᾶσιν',
    'εἰ μὴ αὐτῇ πείθοιντο πάντες',
    'The compact verbal letters and ending remain unresolved; tentative print reading and exact original remain '
    'explicit.'),
   ('ἔστω',
    'ἔσεσθαι',
    'The compact σθ/θ group remains unresolved; possible ἔσεσθαι or ἔσεθαι and exact original remain explicit.'),
   ('ἀποχρίναι',
    'ἀποτάξασθαι',
    'The compact σθ/θ group remains unresolved; possible ἀποτάξασθαι or ἀποτάξαθαι and exact original remain '
    'explicit.')]),
 (48,
  2,
  '0d94657dd85096353193d4084889bdada6e50dc291248d813462f52c91ff7fa2',
  'ὅτι σημειωτέον ὡς οὗτος ὁ διάλογος, ὡς ἐπιγραφὴ συμπάσῳ ἢ περὶ ἀγνείας, παρὰ πολὺ ἐστι νευροθεμένος· εὑρήσεις '
  'γὰρ ἐν αὐτῷ παραβεβλημένας τὰς Ἀρειωνικὰς δοξασίας καὶ ἔκφρων τινῶν κακολογουμένων μυθολογημάτων.',
  'ὅτι σημειωτέον ὡς οὗτος ὁ διάλογος, ᾧ ἐπιγραφὴ συμπόσιον ἢ περὶ ἁγνείας, παρὰ πολύ ἐστι νενοθευμένος· εὑρήσεις '
  'γὰρ ἐν αὐτῷ παραβεβλημένας καὶ τὰς Ἀρειωνικὰς δοξασίας καὶ ἑτέρων τινῶν κακολογουμένων μυθολογήματα.',
  'L',
  [],
  [('τὰς Ἀρειωνικὰς',
    'Ἀρειανικὰς',
    'The compact technical adjective remains uncertain; possible Ἀρειανικὰς or Ἀρειωνικὰς and exact original are '
    'retained without doctrinal restoration.'),
   ('κακολογουμένων',
    'κακοδοξησάντων',
    'The compact participial ending remains unresolved; possible κακοδοξησάντων or κακοδοξούντων and exact '
    'original remain explicit.')]),
 (48,
  3,
  '6dea94145d178c307e04f04a10f048c3993007c26f81ee5b1d400bd9242e661b',
  'ὅτι σημειωτέον τί ποτε ἐστὶ τὸ κατ’ εἰκόνα, ὁ μόνος ἐχόμενος λέγει ἄνθρωπος τῶν ὑπὸ θεῷ γεγεννημένων.',
  'ὅτι σημειωτέον τί ποτέ ἐστι τὸ κατ’ εἰκόνα, ὃ μόνος ἐχόμενος λέγει ἄνθρωπος τῶν ὑπὸ θεοῦ γεγενημένων.',
  'L',
  [],
  [('ἐχόμενος λέγει',
    'ἐκδέχεσθαι λέγεται',
    'The compact σθ/θ group and adjacent ending remain unresolved; possible ἐκδέχεσθαι λέγεται or ἐκδέχεθαι '
    'λέγεται and exact original remain explicit.')]),
 (48,
  4,
  'a784ee92c9f8141218f0afec80a03a5d95b0c4fc111622389b3da4eeee77aa4c',
  '265 ὅδε γὰρ “ἂν εὑρῶ τις ἐν’ ἀνθρώπῳ το τῶν τιμίων, ὁ μὴ ἡ ἀγγέλων μετέχει φύσις. ἔτι γὰρ τὸ ἀνθρώπου, ἢ γὰρ '
  'ἄγγελος, ἔτι τὸ αὐτεξέσιον· εἰ γὰρ ὅτι ἄγγελοι κατὰ τοὺς θεολόγους ἐπὶ τὸ ἀγαθὸν μᾶλλον ἢ ῥοή, κατὰ τοῦτο ὅρα '
  'ὅτι μὴδ’ ὅλως δυνατὸν τὸ κατ’ εἰκόνα τοῦτο εἶναι. εἰ δὲ τὸ ἀρχικὸν λέγεις (ἀρχὴν γὰρ ἔχουσι καὶ τῶν ἄλλων ὁ '
  'ἄνθρωπος πρὸς θεῷ ἔχειν ἐν τῇ τῆς κοσμογονίας ἐγγραφῇ), ὅδ’ ἔτιως ἀλλοτριώσας τῶν ἀγγέλων ἀρχὴν γὰρ τῶν '
  'ἀγγέλων τὰς πλείους ὄντας καὶ φυλὰς παρὰ τῆς γραφῆς ἰδίως δεδοχάμεθα. εἰ δ’ ὅτι μὴ χειροήθεις αὐτοῖς τὰς '
  'ἀρχαίας τιλοῦσι τὴν διαφορὰν εἰσάγεις, καθάπερ ἐκεῖνοι τὰ πολλὰ τῶν ζῴων, ὅδεν πρὸς τῷ γέλῳ κομπάζεις· ὅδε γὰρ '
  'ὁ εἰκόνα 30 φέρειν ὁ ἄνθρωπος λέγει, χειροήθεις τὰς ἀρχαίας (ἄπαγε) δεκνύει. τί οὖν ἐστὶ τὸ κατ’ εἰκόνα; δοκεῖ '
  'γὰρ',
  'οὐδὲν γὰρ ἂν εὕροι τις ἐπ’ ἀνθρώπῳ τι τῶν τιμίων, ᾧ μὴ καὶ ἀγγέλων μετέχει φύσις. ἔστι γὰρ τὸ ἀθάνατον, καὶ '
  'γὰρ καὶ ἄγγελος, ἔστι τὸ αὐτεξούσιον· εἰ γὰρ ὅτι ἀγγέλοις κατὰ τοὺς θεολόγους ἐπὶ τὸ ἀγαθὸν μᾶλλον ἡ ῥοπὴ, '
  'κατὰ τοῦτο ὅρα ὅτι μηδ’ ὅλως δυνατὸν τὸ κατ’ εἰκόνα τοῦτο εἶναι. εἰ δὲ τὸ ἀρχικὸν λέγεις (ἄρχειν γὰρ τῶν '
  'ἰχθύων καὶ τῶν ἄλλων ὁ ἄνθρωπος πρὸς θεοῦ τέτακται ἐν τῇ τῆς κοσμογονίας συγγραφῇ), οὐδ’ οὕτως ἀλλοτριώσεις '
  'τῶν ἀγγέλων· ἀρχὰς γὰρ τῶν ἀγγέλων τὰς πλείους ὄντας καὶ φυλὰς παρὰ τῆς γραφῆς ἰδίως δεδιδάγμεθα. εἰ δ’ ὅτι μὴ '
  'χειροήθεις αὐτοῖς τὰς ἀρχομένας τελοῦσι τὴν διαφορὰν εἰσάγεις, καθάπερ ἐκεῖνοι τὰ πολλὰ τῶν ζῴων, οὐδὲν πρὸς '
  'τῷ γέλωτι κομπάζεις· οὐδὲ γὰρ ὁ εἰκόνα φέρειν ὁ ἄνθρωπος λέγει, χειροήθεις τὰς ἀρχομένας (ἄπαγε) δεικνύει. τί '
  'οὖν ἐστι τὸ κατ’ εἰκόνα; ὅπως γὰρ',
  'L',
  [],
  [('λέγει',
    'λέγεται',
    'The compact verb ending remains unresolved; possible λέγεται or λέγεσθαι and exact original remain '
    'explicit.')]),
 (48,
  5,
  'd368c18891b1310162186cba483eabff17449740d6e7f69ed1c7950eb05c1d27',
  '512 τὴν τῷ σωματικῷ σχήματι ὑπηρεσίαν ἐξαφώθησαν, πρὸς τοὺς μικροὺς ἄλλοις, ὅδε τῆς πρὸς τὸν ἄγγελον κοινωνίας '
  'κατὰ τοῦτο, ὅπερ ἐστὶ τὸ ζητούμενον, τὸν ἄνθρωπον ἠλεκτήσων· ἀνθρωπόμορφον γὰρ αἱ δαίμονες γραφαὶ τὰς ἄγγελος '
  'ἡμῖν ἐνδεικνύειν ἤμα ὑπετέτυπον. εἰ δὲ τὸ δημιουργικὸν καὶ πρακτικὸν εἰς ὕπαρξιν τὸ κατ’ εἰκόνα φυλάσσειν '
  'ἔχεις ἐν’ ἀνθρώπῳ (δημιουργεῖ γὰρ θεὸς τὸ πᾶν, ἀφράδως καὶ ἀνεπίστωτος προάγων ὅ τι μὴ δύντα, ἀλλὰ καὶ '
  'ἄνθρωπος· ἐνίοτε μὲν ἐκ τῆς',
  '512 τὴν τῷ σωματικῷ σχήματι ὑπηρεσίαν ἐξαφώθησαν, πρὸς τοῖς μυρίοις ἐλέγχοις, οὐδὲ τῆς πρὸς τὸν ἄγγελον '
  'κοινωνίας κατὰ τοῦτο, ὅπερ ἐστὶ τὸ ζητούμενον, τὸν ἄνθρωπον ἠλευθέρωσαν· ἀνθρωπόμορφον γὰρ αἱ θεῖαι γραφαὶ τὰς '
  'ἀγγέλους ἡμῖν ἐνδεικνύειν ἤμα ὑπετέτυπον. εἰ δὲ τὸ δημιουργικὸν καὶ πρακτικὸν εἰς ὕπαρξιν τὸ κατ’ εἰκόνα '
  'φυλάσσειν ἔχεις ἐπ’ ἀνθρώπῳ (δημιουργεῖ γὰρ θεὸς τὸ πᾶν, ἀφράστως καὶ ἀνεπιστάτως προάγων τὰ μὴ ὄντα, ἀλλὰ καὶ '
  'ἄνθρωπος· ἐνίοτε μὲν ἐκ τῆς',
  'L',
  [],
  [('512 τὴν τῷ σωματικῷ σχήματι ὑπηρεσίαν ἐξαφώθησαν,',
    'τὴν τοῦ σωματικοῦ σχήματος ὑπηρεσίαν ἐξεφάθησαν,',
    'The compact noun and verb group is unresolved; tentative scan reading and exact original are retained '
    'without completing the philosophical argument.'),
   ('ἐνδεικνύειν ἤμα ὑπετέτυπον',
    'ἐνδεικνύσθαι ἐμφανέστατα',
    'The compact σθ/θ group and adjacent word types remain unresolved; tentative reading and exact original are '
    'retained.')]),
 (48,
  6,
  'c91bb230386a3a815f25836298bcb363a87127d9e0c62bf846f63fc45c058ad7',
  'ιδίας ἑσίας καὶ φθόγγος σποράς καταβολή, ὁμοῖον ἀν-θρωπον γεωργῶν, ἔνιοι δὲ τέχνη πολλὰ τῶν τεχνιτῶν '
  'δημιουργῶν, εἰ καὶ μὴ ἐκ τοῦ μηδαμῶς μηδαμῶς ὄντος), ἀλλὰ ἡ τῷι τὶ πιθανὸν ἔχον φαίνεσθαι ἐλήλυθε. οἱ [εἰ] γὰρ '
  "μονάζοντες, καὶ διὰ τὸ δοκεῖν φιλάσθαι τὸ κατ' εἰκόνα παντὸς ἀνθρωπίνου [συγχώματος ἢ] συγχώματος ἀνωτέρω "
  "ἑαυτὸς ἐργασάμενοι, ἄθλιοι ἀν θάνοιεν, τὸ κατ' εἰκόνα δὲ αὐτὸ ἐκεῖνο ἀπολιπόντες. τὶ οὖν τὸ κατ' εἰκόνα; ἢ τῶν "
  "ἀρετῶν δὲ ἐπιμελείας κτήσις· ἄγγελοι μὲν γὰρ ἔχων ἀρετὴν, ἀλλ' οὐ τὴν δὲ ἐπιμελείας καὶ κόπον, ὅτι μὴ "
  "μεθελκοντ' ὑπὸ κακίας, δοξάζονται. ἀλλ' εἰ καὶ τοῦτο συγχωρηθείη, ἄκοπον ἀρετῶν κτῆσιν τοῖς ἀγγέλοις "
  "ἀποκαληφθῆν, ἢ ἡ ἑτοῖ τὸ κατ' εἰκόνα τῇ ἀκόπως ἔχειν θεὸν μᾶλλον πλησιώῃσαντες ἑξασιν, ἢ εἰ μὴ ἑτοῖ, πολλῷ "
  "μᾶλλον ὑπ' ἀνθρωπος, ὅτι μετὰ ταύτης ἢ πρὸ ταύτης τὴν κτῆσιν πολλῶν παραχῶν καὶ πόνων ἐμπιπλώμενος ταύτην "
  'ἐκδέχετο.',
  'ἰδίας οὐσίας καὶ φύσεως σπορᾶς καταβολῇ ὅμοιον ἄνθρωπον γεωργῶν, ἐνίοτε δὲ τέχνῃ πολλὰ τῶν τεχνητῶν '
  'δημιουργῶν, εἰ καὶ μὴ ἐκ τοῦ μηδαμῇ μηδαμῶς ὄντος), ἀλλὰ καὶ τοῦτό τι πιθανὸν ἔχον εὐλύτως φαίνεσθαι ἐλήλυθε. '
  'οἱ [εἰ] γὰρ μονάζοντες, καὶ διὰ τὸ δοκεῖν φυλάσσειν τὸ κατ’ εἰκόνα παντὸς ἀνθρωπίνου [συγχώματος ἢ] '
  'συγχρώματος ἀνωτέρω ἑαυτοὺς ἐργασάμενοι, ἄθλιοι ἂν φανοῖεν, τὸ κατ’ εἰκόνα δι’ αὐτὸ ἐκεῖνο ἀπολιπόντες. τί οὖν '
  'τὸ κατ’ εἰκόνα; ἡ τῶν ἀρετῶν δι’ ἐπιμελείας κτῆσις· ἄγγελοι μὲν γὰρ ἔχουσιν ἀρετὴν, ἀλλ’ οὐ τὴν δι’ ἐπιμελείας '
  "καὶ κόπου, ὅτι μὴ μεθελκοντ' ὑπὸ κακίας, δοξάζονται. ἀλλ’ εἰ καὶ τοῦτο συγχωρηθείη, ἄκοπον ἀρετῶν κτῆσιν τοῖς "
  'ἀγγέλοις ἀποκαληφθῆν, ἢ καὶ ἔσται τὸ κατ’ εἰκόνα τῷ ἀκόπως ἔχειν θεῷ μᾶλλον πλησιάζοντες ἕξουσιν, ἢ εἰ μὴ '
  'ἔσται, πολλῷ μᾶλλον οὐδ’ ὁ ἄνθρωπος, ὅτι μετὰ ταύτης ἢ πρὸ ταύτης τὴν κτῆσιν πολλῶν ταράχων καὶ πόνων '
  'ἐμπιπλώμενος ταύτην ἐκδέχετο.',
  'R',
  [],
  [('φαίνεσθαι ἐλήλυθε',
    'ἐλέγχεται',
    'The compact verb ending remains unresolved; possible ἐλέγχεται or ἐλέγχεσθαι and exact original remain '
    'explicit.'),
   ('[εἰ]',
    '[εἰ]',
    'Printed bracketed complete word. Brackets alone do not establish authorship; exact bracketed text is '
    'retained without lexical admission.'),
   ('[συγχώματος ἢ]',
    '[ἐργήματος ἢ]',
    'Printed bracketed complete words. Brackets alone do not establish authorship; exact original and observed '
    'alternative are retained without lexical admission.'),
   ("μεθελκοντ'",
    'μεθέλκονται',
    'The compact verb ending remains unresolved; possible μεθέλκονται or μεθέλκοντο and exact original remain '
    'explicit.'),
   ('ἀποκαληφθῆν',
    'ἀποκεκληρῶσθαι',
    'The compact σθ/θ group remains unresolved; possible ἀποκεκληρῶσθαι or ἀποκεκληρῶθαι and exact original '
    'remain explicit.'),
   ('ἐκδέχετο',
    'ἐκδέχεται',
    'The compact verb ending remains unresolved; possible ἐκδέχεται or ἐκδέχεσθαι and exact original remain '
    'explicit.')]),
 (48,
  7,
  '673533efabd2080bb9d3c7902fb44cb0601a58fe011865e8ad5e0971b019ad9f',
  'Ἀνερνώδη ἸΩΣΗΠΟΥ ἢ ἀρχαιολογία· ἧς ἢ ἐκλογή, ὅσα τε ἰσορεῖ περὶ Ἡρώδου, καταλέγει, τὴν τε ἀνακοδομὴν τῆ ναῦ, '
  'ὅπως τε τὴν Ἰουδαϊκὴν ἐπικεσθῆ βασιλείαν, καὶ ὅπως αὐτὴ τὴν ἀρχὴν οἱ ἐκ γένους διεδέξαντο, ὅπως τε αὐτὴ εἰς '
  'ἀριστοκρατίαν καταλλελθ, τὴν προασιὰν τῷ Ἴωνι τῶν ἀρχιερέων ἀναδιδομένων, ἢ ὅσα ἄλλα τέτοις συνδιαπλέκεται.',
  'Ἀνερνώδη ἸΩΣΗΠΟΥ ἡ ἀρχαιολογία· ἧς ἡ ἐκλογὴ, ὅσα τε ἱστορεῖ περὶ Ἡρώδου, καταλέγει, τήν τε ἀνοικοδομὴν τοῦ '
  'ναοῦ, ὅπως τε τὴν Ἰουδαϊκὴν ἐπικεσθῆ βασιλείαν, καὶ ὅπως αὐτοῦ τὴν ἀρχὴν οἱ ἐκ γένους διεδέξαντο, ὅπως τε αὕτη '
  'εἰς ἀριστοκρατίαν καταλλελθ, τὴν προστασίαν τοῦ ἔθνους τῶν ἀρχιερέων ἀναδεξαμένων, καὶ ὅσα ἄλλα τούτοις '
  'συνδιαπλέκεται.',
  'R',
  [],
  [('Ἀνερνώδη',
    'Ἀνεγνώσθη',
    'The compact heading σθ/θ group remains unresolved; possible Ἀνεγνώσθη or Ἀνεγνώθη and exact original remain '
    'explicit.'),
   ('ἐπικεσθῆ',
    'ὑπεισῆλθε',
    'The compact consonants and ending remain unresolved; this tentative reading and exact original are '
    'retained.'),
   ('καταλλελθ',
    'κατελύθη',
    'The compact verb ending remains unresolved; possible κατελύθη or κατελύσθη and exact original remain '
    'explicit.')]),
 (48,
  8,
  '1b450eabdaa2c9c60e930f6a28a8cef3962c6707d5694a578fc52bdaef9932b1',
  "διὲ Ἰώσηπος πρὸς τῷ τέλει τῆς ιε' κατὰ τὴν ἀρχαιολογίαν ἰσορίας, ὀκτωκαιδέκατον ἔτος τῆς βασιλείας Ἡρώδην "
  'αὐτοῖν τὸν ἐν Ἱεροσολύμοις ναὸν, ἐν ἑκτισι 968 R. Σολομὼν δ βασιλεύς, κατασφαγίντα δὲ πάλιν οἱ ἐκ Βαβυλῶνος '
  "ἀναχθέντες αἰχμάλωτοι Ἀρείῳ τῷ Περσῶν βασιλέως συναραμίνῳ αὐτοῖς ἀνέθισαν ἐν ε' ἑκτὶ εἰς μ', τῦνόν ἡγοῦ τὸν "
  "πειρώμενον νεὼν μετὰ τὴν ἑξακάσια, ἀνιόντα μὲν τὰς ἀρχαίας θεμελίους, ἑτέρως δὲ καταβαλόντα ἐπ' αὐτῶν τὸν "
  'Ἡρώδην διπλάσιον τοῦ προτέρον ἀνασῆσαι· λείπει δὲ τὸν ὑπὸ τῶν αἰχμαλώτων τῷ Σολομωντείῳ μέτρου κατὰ τὸ ὕψος '
  "τισίν. εἶχε δὲ ὁ Ἡρώδης νεὼς μήκος μὲν πήχεις ρ', ὕψος δὲ κ' περιτοῖς, ὅς καὶ ὑπέρῃ τῷ χρόνῳ τῶν θεμελίων "
  "συνιζοσάντων· δ ἢ κατὰ τὰς Νέρωνος καιρὰς Ἰουδαῖοι ἐγνώμιασαν ἐπιχειρῶν. οἰκοδομηθῆναι δ' Ἡρώδη τὸν ναὸν "
  "Ἰώσηπος φησιν ἐνιαυτῷ ἐνὶ καὶ μηνὶ ε', τῶν δὲ",
  'ὅτι Ἰώσηπος πρὸς τῷ τέλει τῆς ιεʹ κατὰ τὴν ἀρχαιολογίαν ἱστορίας, ὀκτωκαιδέκατον ἔτος τῆς βασιλείας Ἡρώδην '
  'ἀνιόντα τὸν ἐν Ἱεροσολύμοις ναὸν, ὃν ἔκτισε Σολομὼν ὁ βασιλεὺς, καταστραφέντα δὲ πάλιν οἱ ἐκ Βαβυλῶνος '
  "ἀναχθέντες αἰχμάλωτοι Δαρείῳ τῷ Περσῶν βασιλέως συναραμένῳ αὐτοῖς ἀνέστησαν ἐν ε' ἑκτὶ εἰς μ', τοῦτόν φησι τὸν "
  'χειρώτερον νεὼν μετὰ ἔτη ἑξακόσια, ἀνελόντα μὲν τὰς ἀρχαίας θεμελίας, ἑτέρας δὲ καταβαλόντα ἐπ’ αὐτῶν τὸν '
  'Ἡρώδην διπλάσιον τοῦ προτέρου ἀναστῆσαι· λείπει γὰρ τὸν ὑπὸ τῶν αἰχμαλώτων τῷ Σολομωντείῳ μέτρῳ κατὰ τὸ ὕψος '
  'τισίν. εἶχε δὲ ὁ Ἡρώδειος ναὸς μῆκος μὲν πήχεις ρʹ, ὕψος δὲ κʹ περιττοῖς, ὃς καὶ ὑπέβη τῷ χρόνῳ τῶν θεμελίων '
  'συνιζησάντων· ὃ καὶ κατὰ τοὺς Νέρωνος καιροὺς Ἰουδαῖοι ἐγνώκεσαν ἐπεγείρειν. οἰκοδομηθῆναι δ’ Ἡρώδῃ τοῦτον τὸν '
  'ναὸν Ἰώσηπός φησιν ἐνιαυτῷ ἑνὶ καὶ μησὶν ϛʹ, τῶν δὲ',
  'R',
  [],
  [("ἐν ε' ἑκτὶ εἰς μ'",
    'ἐν ϛʹ ἔτεσι καὶ μʹ',
    'The small printed numeral and intervening word remain uncertain; possible ἐν ϛʹ ἔτεσι καὶ μʹ or ἐν ἓξ ἔτεσι '
    'καὶ μʹ and exact original are retained. No chronological harmonization is supplied.'),
   ('λείπει',
    'λείπεσθαι',
    'The compact consonants and ending remain unresolved; this tentative reading and exact original are '
    'retained.')])]

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
