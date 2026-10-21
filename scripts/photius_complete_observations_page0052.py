"""Complete direct source review of retained passages on Bekker printed317.

All retained passages and source boundaries were visually inspected. Compact
endings, proper names, and uncertain numerals remain separate from verified text.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:58:14.238948+00:00'
_CROPS = {'L':[.055,.10,.455,.755], 'R':[.395,.10,.815,.755]}
_SPECS = [(52,
  1,
  'a96d1f0ed048d5b945709ff39d0c0cbc28c4599321ae967d67894b7fbbd3e292',
  '18καλούμενον (ζῶν) πρὸ πέντε τῆς τελευτῆς ἡμερῶν ὑπὲρ κεφαλῆς φανέντος, ᾧ καὶ τὴν βασιλείαν προσ-αγγείλαι '
  'νομίζει Ἰώσηπος. τελευτᾷ δὲ ἐν παιδας ληψὼν δ᾽, ἀφέντα μὲν Ἀγρίππαν, ἵς ἔτος ἄγοντα, Φηλείαν δὲ γῆ, Βερενίχην '
  'Μαριάμμην δ᾽ Ἀροσίλαν. ὡν ἡ μὲν ἔτος ἄγουσα ἵς Ἡρώδῃ πατρὸς ἀδελφῇ ἐγεγόνει, Μαριάμμῃ δ᾽ ἔγνετο δέκατον καὶ '
  'Ἀροσίλα ἴκτον· ὡς οἱ Σαμαρεῖται κατ᾽ ἑαυτὸν ἄλλην πρόφασιν πλὴν τῆ μανθίνει ἀφίστασθαι ἀθρόον καὶ πορνείας '
  'ἐγκατασῆ-σαντες, πᾶσαν αὐτὰς ἔδραον ἔχτην καὶ ἀξήρητον ἐπε-ιδαζαντο. οὗς χαλεπίνως Κλαύδιος ὅμως οὐδὲν ἄξιον '
  'τῆς παρανομίας εἰσεφρύζατο.',
  'καλούμενον ζῶον) πρὸ πέντε τῆς τελευτῆς ἡμερῶν ὑπὲρ κεφαλῆς φανέντος, ᾧ καὶ τὴν βασιλείαν προσαγγεῖλαι νομίζει '
  'Ἰώσηπος. τελευτᾷ δ’ οὖν παῖδας λιπὼν δʹ, ἄρρενα μὲν Ἀγρίππαν, ἵς ἔτος ἄγοντα, θηλείας δὲ γʹ, Βερενίκην '
  'Μαριάμμην καὶ Δρουσίλαν. ὧν ἡ μὲν ἔτος ἄγουσα ἵς Ἡρώδῃ πατρὸς ἀδελφῷ ἐγεγάμητο, Μαριάμμῃ δ’ ἠνύετο δέκατον καὶ '
  'Δρουσίλᾳ ἕκτον· ὧς οἱ Σεβαστηνοὶ κατ’ οὐδεμίαν ἄλλην πρόφασιν πλὴν τὸ μανθίνει ἀφίστασθαι ἀθρόον καὶ πορνείας '
  'ἐγκατασῆ-σαντες, πᾶσαν αὐτοῖς ὕβριν ῥητὴν καὶ ἄρρητον ἐπεδείξαντο. οἷς χαλεπήνας Κλαύδιος ὅμως οὐδὲν ἄξιον τῆς '
  'παρανομίας εἰσεπράξατο.',
  'L',
  [],
  [('ἵς',
    'ιζʹ',
    'The small printed age numeral remains unresolved; ιζʹ and ιςʹ remain alternatives alongside the exact '
    'original.'),
   ('ἵς',
    'ιςʹ',
    'The small printed age numeral remains unresolved; ιςʹ and ιζʹ remain alternatives alongside the exact '
    'original.'),
   ('μανθίνει ἀφίστασθαι',
    'μανῆναι ἀρπάσαντες',
    'The compact infinitive and participle remain unresolved. Tentative μανῆναι ἀρπάσαντες or μανῆναι ἁρπάσαντες '
    'and exact original are retained without reconstructing the historical incident.'),
   ('ἐγκατασῆ-σαντες',
    'ἐγκαταστήσαντες',
    'The compact consonant group remains unresolved; ἐγκαταστήσαντες or ἐγκαταθῆσαντες and exact original are '
    'retained.')]),
 (52,
  2,
  'ea2bcc7078d030957a4c3f82f15e0a8951bdb11521799aa70a1aaef2b00e65cc',
  'ὅτι Ἀγρίππας ὁ τῷ Ἀγρίππῃ παῖς τελευτήσαντος αὐτῷ τοῦ πατρὸς εἰς Ῥώμην ἀπαίρει· Κλαύδιος δ᾽ αὐτὸν τὴν πατρῴαν '
  'ἀρχὴν ἐγνώκει χειροῦν, ἀνακοπίας δ᾽ ἐνίων βουλὰς τὸν νῖον τῆς ἡλικίας Ἀγρίππα αἰτια-σαμένων, Φῶδον μὲν '
  'ἐπίτροπον ἐκπέμπει τῆς Ἰουδαίας, Ἀγρίππαν δὲ Χαλκίδος, Ἡρώδῃ τελευτήσαντος τοῦ πατρὸς ἔχοντος τὴν βασιλείαν, '
  'εἰς βασιλεία καὶ Ἰζησι-μετὰ δὲ τέταρτον ἔτος δωρεῖ· αὐτὸν τῇ τε Φιλίππου τετραρχία καὶ Βαταναίᾳ, προσθεὶς αὐτῷ '
  'καὶ τὴν Τρα-χωνίτην· Ἀνασαὶν δ᾽ αὐτὴ τετραρχία ἐγεγόνει. ἡ ταῦτα δὲ ἀφαιρεῖται τὴν Χαλκίδα. Ἀγρίππας δὲ '
  'Ἀροσίλαν τὴν ἀδελφὴν Ἀζήβῳ τῷ Ἐμύσων βασιλεῖ περιπέμποντι δίδωσι γυναῖκα· Ἐπιφάνης γὰρ Ἀντόχας, καὶ τοῦ '
  'ὑπο-χόμενος, ἐκ ἐδίζετο τὴν περιτομὴν, ἵς ὅ καὶ ἡ τῆς ἐγγυήσεως διάλυσις ἠκολούθει. Ἀροσίλα δὲ καὶ Ἀζήβῳ '
  'διαλύει, ἡ Φηλίμ τῷ τῆς Ἰουδαίας ἐπιτρόπῳ, πολλὰ σπαδαδάσαντος ἐκείνη διὰ τὸ κάλλος, γαμεῖ· καὶ Μα-ριάμμην δὲ '
  'δίδωσιν Ἀρχελάῳ παιδὶ τῷ Ἐλχί, ᾧ καὶ 3',
  'ὅτι Ἀγρίππας ὁ τοῦ Ἀγρίππου παῖς τελευτήσαντος αὐτῷ τοῦ πατρὸς εἰς Ῥώμην ἀπαίρει· Κλαύδιος δ’ αὐτῷ τὴν πατρῴαν '
  'ἀρχὴν ἐγνώκει χαρίζειν, ἀνακοπεὶς δ’ ἐνίων βουλαῖς τὸ νέον τῆς ἡλικίας Ἀγρίππα αἰτιασαμένων, Φάδον μὲν '
  'ἐπίτροπον ἐκπέμπει τῆς Ἰουδαίας, Ἀγρίππαν δὲ Χαλκίδος, Ἡρώδου τελευτήσαντος τοῦ ταύτης ἔχοντος τὴν βασιλείαν, '
  'εἰς βασιλέα καθίστησι. μετὰ δὲ τέταρτον ἔτος δωρεῖ· αὐτὸν τῇ τε Φιλίππου τετραρχίᾳ καὶ Βαταναίᾳ, προσθεὶς αὐτῷ '
  'καὶ τὴν Τραχωνῖτιν· Λυσανίου δ’ αὕτη τετραρχία ἐγεγόνει. καὶ ταῦτα δοὺς ἀφαιρεῖται τὴν Χαλκίδα. Ἀγρίππας δὲ '
  'Δρουσίλαν τὴν ἀδελφὴν Ἀζήβῳ τῷ Ἐμέσων βασιλεῖ περιτμηθέντι δίδωσι γυναῖκα· Ἐπιφανὴς γὰρ Ἀντόχας, καίτοι '
  'ὑπο-χόμενος, οὐκ ἐδέχετο τὴν περιτομὴν, ἐξ οὗ καὶ ἡ τῆς ἐγγυήσεως διάλυσις ἠκολούθει. Δρουσίλα δὲ καὶ Ἀζήβῳ '
  'διαλύει, καὶ Φήλικι τῷ τῆς Ἰουδαίας ἐπιτρόπῳ, πολλὰ σπουδάσαντος ἐκείνου διὰ τὸ κάλλος, γαμεῖ· καὶ Μαριάμμην '
  'δὲ δίδωσιν Ἀρχελάῳ παιδὶ τῷ Ἑλκίᾳ, ᾧ καὶ',
  'L',
  [],
  [('δωρεῖ·',
    'δωρεῖται',
    'The compact verb ending remains unresolved; δωρεῖται or δωρεῖσθαι and exact original are retained.'),
   ('Ἀζήβῳ',
    'Ἀζίζῳ',
    'The compact proper name remains unresolved; Ἀζίζῳ or Ἀζήζῳ and exact original remain explicit.'),
   ('Ἀντόχας',
    'Ἀντιόχου',
    'The small name ending remains unresolved; Ἀντιόχου or Ἀντιόχῳ and exact original remain explicit.'),
   ('ὑπο-χόμενος',
    'ὑποσχόμενος',
    'The compact σχ/χ group remains unresolved; ὑποσχόμενος and ὑποχόμενος remain explicit.'),
   ('Ἀζήβῳ',
    'Ἀζίζῳ',
    'The compact proper name remains unresolved; Ἀζίζῳ or Ἀζήζῳ and exact original remain explicit.'),
   ('διαλύει',
    'διαλύεται',
    'The compact verb ending remains unresolved; διαλύεται or διαλύεσθαι and exact original remain explicit.'),
   ('γαμεῖ',
    'γαμεῖται',
    'The compact verb ending remains unresolved; γαμεῖται or γαμεῖσθαι and exact original remain explicit.')]),
 (52,
  3,
  '47c08466024736d8bbfb89963e9cdbe4bcb22bbd4a4693e1765f775e0b86feec',
  '17Β.ζῶν ὁ πατὴρ ἠρώμαστο· “ἵς ὧν τίκτεται Βερενίκη. Κλαύδιος δὲ τελευτήσαντος Νέρων κατασάς διάδοχος δωρεῖται '
  'Ἀγρίππαν μοῖραν τινὰ τῆς Γαλιλαίας, Τιβερ-ρίδα καὶ Ταρχαῖαν· κλείσας αὐτῷ ὑπικένει, προσ-τίθησι δὲ καὶ Ἰουδαία '
  'πόλιν τῆς Περαιας, ἡ κυρίας τὰς περὶ αὐτὴν δέκα. ἔτος ἔσιν Ἀγρίππας, ἐφ᾽ οὗ ὁ θεὸς Παῦλος Φήσῳ συνεδριάζοντος '
  'ἐδημηγόρησιν.',
  'ζῶν ὁ πατὴρ ἡρμόσατο· ἐξ ὧν τίκτεται Βερενίκη. Κλαυδίου δὲ τελευτήσαντος Νέρων καταστὰς διάδοχος δωρεῖται '
  'Ἀγρίππαν μοῖράν τινα τῆς Γαλιλαίας, Τιβεριάδα καὶ Ταριχαίαν κελεύσας αὐτῷ ὑπακούειν, προστίθησι δὲ καὶ '
  'Ἰουλιάδα πόλιν τῆς Περαίας, καὶ κώμας τὰς περὶ αὐτὴν δέκα. οὗτός ἐστιν Ἀγρίππας, ἐφ’ οὗ ὁ θεῖος Παῦλος Φήστῳ '
  'συνεδριάζοντος ἐδημηγόρησεν.',
  'L',
  [],
  []),
 (52,
  4,
  'e3fdd2073ee33d9d7cb9ceada92e4780bac7a1227fd05c23dee0c48825f261ce',
  'ὅτι μετὰ Φῶδον ἐπίτροπον Ἰουδαίας Κομανὸς πέμ-πεται· μεθ᾽ ὃν εἰς Ῥώμην ἀναχθέντα ἐπ᾽ αἰτίας Φηλῆς πέμπεται· '
  'μεθ᾽ ὃν Φήσος, εἶτα Ἀλβῖνος, λοιπὸς Φιλῆ-ρος. ἡ δευτέρῳ ἔτι διὰ τὴν ὑπεροχὴν τῶν παρ᾽ αὐτῷ κακῶν ὁ πρὸς '
  'Ῥωμαίους Ἰουδαίων πόλεμος ἀρχὴν ἔσχε, Νέρωνος ἔτος δωδέκατον ἐν τῇ ἀρχῇ διανύοντος.',
  'ὅτι μετὰ Φάδον ἐπίτροπον Ἰουδαίας Κουμανὸς πέμπεται· μεθ’ ὃν εἰς Ῥώμην ἀναχθέντα ἐπ’ αἰτίας Φῆλιξ πέμπεται· '
  'μεθ’ ὃν Φῆστος, εἶτα Ἀλβῖνος, λοιπὸς Φλῶρος. ἐν δευτέρῳ ἔτει διὰ τὴν ὑπερβολὴν τῶν παρ’ αὐτῷ κακῶν ὁ πρὸς '
  'Ῥωμαίους Ἰουδαίων πόλεμος ἀρχὴν ἔσχε, Νέρωνος ἔτος δωδέκατον ἐν τῇ ἀρχῇ διανύοντος.',
  'L',
  [],
  [('ἔσχε', 'ἔσχε', 'The compact σχ/χ group remains unresolved; ἔσχε and ἔχε remain explicit.')]),
 (52,
  5,
  'e8dd2adfd0d3ca5a5cac7a564645b26d0c9201e7d0af5119ca9ff2572b9ed33a',
  'ὅτι Ἄνανος ὁ Ἀνάνᾳ παῖς τὴν ἀρχιερωσύνην παραλαβὼν, ἀφαιρεθέντος αὐτῆν Ἰωσήπου, θρασὺς ἢν καὶ τολμητὴς '
  'διαφερόντως· αἴρεισιν γὰρ τὴν Σαδδουκαίων μετὰ ταῦτα ὅποι τε περὶ τὰς κρίσεις καὶ πρὸς τὸν πᾶσαν αὐθάδειαν '
  'ἔτοιμοι. οὗτος δὲ ὁ Ἄνανος Φίλιππον μὲν ἐν Ἰουδαίᾳ τελευτήσαντος, Ἀλβῖνον δὲ ἤδη καταλαμβόντος, αὐθεντήσας '
  'καθῆξιν συνέδριον, καὶ λῦσατὸν ἀδελφὸν τῷ κυρίῳ σὺν ἑτέρῳ, παρανομίαν αἰτιασάμενος, λίθους ἀναιρεθῆναι '
  'παρασκευάζει. ἣν ὁ τῶν Ἰουδαίων ἐπαρχήσας τες οἱ ἐπιμελέστεροι, καὶ αὐτὸς Ἀγρίππας ὁ βασιλεὺς, ἐμβάλλουσι '
  "ἄρξαντα μέχρι τῆς Ἰροῦν δ' ἀντ' αὐτὸν τὸν Λύμιον ἐγκατέστησαν.",
  'ὅτι Ἄνανος ὁ Ἀνάνου παῖς τὴν ἀρχιερωσύνην παραλαβὼν, ἀφαιρεθέντος αὐτὴν Ἰωσήπου, θρασὺς ἦν καὶ τολμητὴς '
  'διαφερόντως· αἵρεσιν γὰρ τὴν Σαδδουκαίων μετῄει· οὗτοι γὰρ ὠμοί τε περὶ τὰς κρίσεις καὶ πρὸς πᾶσαν αὐθάδειαν '
  'ἕτοιμοι. οὗτος δὲ ὁ Ἄνανος Φήστου μὲν ἐν Ἰουδαίᾳ τελευτήσαντος, Ἀλβῖνον δὲ ἤδη καταλαμβόντος, αὐθεντήσας '
  'καθίζει συνέδριον, καὶ Ἰάκωβον τὸν ἀδελφὸν τοῦ κυρίου σὺν ἑτέροις, παρανομίαν αἰτιασάμενος, λίθοις ἀναιρεθῆναι '
  'παρασκευάζει. ἐφ’ ᾧ τῶν Ἰουδαίων ὑπεραλγήσαντες οἱ ἐπιεικέστεροι, καὶ αὐτὸς Ἀγρίππας ὁ βασιλεὺς, ἐκβάλλουσιν '
  'ἄρξαντα μέχρι τῆς, Ἰησοῦν δ’ ἀντ’ αὐτοῦ τὸν Λύμιον ἐγκαθίζουσιν.',
  'R',
  [],
  [('Ἀλβῖνον δὲ ἤδη καταλαμβόντος',
    'Ἀλβίνου δὲ ἔπω καταλαβόντος',
    'The compact negative or adverb remains unresolved; οὔπω/ἔπω/ἔπου and exact original remain explicit without '
    'choosing the chronology from another edition.'),
   ('μέχρι τῆς',
    'μηνὶ γʹ',
    'The compact period and small numeral remain unresolved; μηνὶ γʹ or μῆνα γʹ and exact original remain '
    'explicit.'),
   ('Λύμιον',
    'Δάμναιον',
    'The compact proper name remains unresolved; Δάμναιον or Δάμνιον and exact original remain explicit.')]),
 (52,
  6,
  '2ae1cc8224c2865163088c96fe294b52f08413b27e826e84febf8fbe3a3c59ed',
  'ὅτι Ἀρῶν τελευτήσαντος, Μωϋσέως ἀδελφοῦ, οἱ παῖδες ἐκδέχονται τὴν ἀρχιερωσύνην, εἶτα ἐξ ἑξ οἱ τάτων ἔχοντο· '
  'νόμος γὰρ μέδοντα τὸν ἐξ Ἀαρὼν τὴν ἀρχιερωσύνην ἑαδέλφως πάτριος ἐκρίνει. ἐγένοντο δὲ ἀπὸ Ἀαρῶνος μέχρι Φαναβα '
  'τῷ κατὰ τὸν πόλεμον ὑπὸ τῶν ρωμαίων ἀναδειχθέντος ἀρχιερέως πρῶτον. ἐκ τούτων ἀπὸ τῆς ἐν τῇ ἐρήμῳ διαγωγῆς, ἐν '
  'ἡ ἡ σκηνὴ ἐπήγνυτο, μέχρι τοῦ νιν ὃν ἡγεῖτο ὁ βασιλεὺς Σολομῶν, ἀρχιεράτευσαν δικαίως, τὴν ἀρχιερωσύνην διὰ '
  'βία κατυχάντες ἕκασος. ἐγένετο δὲ αὐτῶν ἀρικρατορικὴ μὲν ἡ πρώτη πολιτεία, εἶτα μοναρχία, εἶτα βασιλέων ἡ '
  "τρίτη. ἀπὸ γὰρ τῆς ἀπ' Αἰγύπτου ἐξόδου ἕως τοῦ ἐν Ἱεροσολύμοις νεοῦ τῆς οἰκοδομῆς ἔτη γένεται ἱ' καὶ χ'. μετὰ "
  "δὲ τοὺς ἐφ' ἀρχιερεῖς καὶ τὴν οἰκοδομὴν τοῦ νεοῦ ἱ' καὶ ἡ τὴν ἀρχιερωσύνην ἔχον ἀπὸ Σολομῶνος βασιλέως ἐν τῷ "
  'νενῷ ἱερόμενοι, ἕως Ναβουχοδονόσορ ὁ Βαβυλωνίων βασιλεὺς τὸν νεὸν ἔμψήσας αἰχμαλώτους τὸ Ἰουδαίων ἔθνος εἰς '
  "Βαβυλῶνα μετήνεγκεν Ἀμαὶς ἐν τῷ ἀρχιερέως. τούτων χρόνος ἐστὶ τῆς ἀρχιερωσύνης τῆς', μήνες ε', ἡμέραι ε'. μετὰ "
  "δὲ τὴν ἄλωσιν ἐτῶν ο' διελθόντων Κύρος ὁ Περσῶν βασιλεὺς τὸς αἰχμαλώτους ἀπέλυσεν εἰς τὴν ἰδίαν πατρίδα. εἰς "
  "ὃν τῶν ἀναχθέντων αἰχμαλώτων λαμβάνει τὴν ἀρχιερωσύνην, καὶ ἐκεῖθεν οἱ ἐξ αὐτῶ ἔχοντο ἱ' μέχρις Ἀντίοχον τοῦ "
  "Εὐπάτορος, πολιτείας ὅσης ἐν αὐτοῖς δημοκρατορικῆς. ἡ τούτων δὲ χρόνος ἔτη νιθ'. πρῶτος δ' ἵστος Ἀντίοχος καὶ "
  'ὁ ἐρατῆς ὁ αὐτὸ Ἀυσίας τὸν Ὀνίαν, ὃ Μενλάος ἐπίλεψεν, παύσαι τῆς ἀρχιερωσύνης, ἀνελόντες αὐτὸν ἐν Βεροίᾳ, καὶ '
  'ἀντικαθεῖσαν Ἰάμμων, γένος μὲν τοῦ Ἀαρῶνος, ὁ τῆς αὐτῆς δ\' οἰκίας. "διὰ τοῦτο καὶ Ἀννίας ὁ τοῦ τελευτή-',
  'ὅτι Ἀαρὼν τελευτήσαντος, Μωϋσέως ἀδελφοῦ, οἱ παῖδες ἐκδέχονται τὴν ἀρχιερωσύνην, εἶτα ἑξῆς οἱ τούτων ἔκγονοι· '
  'νόμος γὰρ μηδένα ἢ τὸν ἐξ αἵματος Ἀαρὼν τὴν ἀρχιερωσύνην ἑαδέλφως πάτριος ἐκράτει. ἐγένοντο δὲ ἀπὸ Ἀαρῶνος '
  'μέχρι Φαναβα τοῦ κατὰ τὸν πόλεμον ὑπὸ τῶν στασιαστῶν ἀναδειχθέντος ἀρχιερέως πρῶτον. ἐκ τούτων ἀπὸ τῆς ἐν τῇ '
  'ἐρήμῳ διαγωγῆς, ἐν ᾗ καὶ ἡ σκηνὴ ἐπήγνυτο, μέχρι τοῦ νεὼ ὃν ἤγειρεν ὁ βασιλεὺς Σολομὼν, ἀρχιεράτευσαν '
  'δεκατρεῖς, τὴν ἀρχιερωσύνην διὰ βίου κατυχάντες ἕκαστος. ἐγένετο δὲ αὐτῶν ἀριστοκρατορικὴ μὲν ἡ πρώτη '
  'πολιτεία, εἶτα μοναρχία, εἶτα βασιλέων ἡ τρίτη. ἀπὸ γὰρ τῆς ἀπ’ Αἰγύπτου ἐξόδου ἕως τοῦ ἐν Ἱεροσολύμοις νεὼ '
  "τῆς οἰκοδομῆς ἔτη γίνεται ἱ' καὶ χ'. μετὰ δὲ τοὺς ἐφ' ἀρχιερεῖς καὶ τὴν οἰκοδομὴν τοῦ νεὼ ἱ' καὶ ἡ τὴν "
  'ἀρχιερωσύνην ἔχον ἀπὸ Σολομῶνος βασιλέως ἐν τῷ ναῷ ἱερώμενοι, ἕως Ναβουχοδονόσορ ὁ Βαβυλωνίων βασιλεὺς τὸν '
  'νεὼν ἐμπρήσας αἰχμαλώτους τὸ Ἰουδαίων ἔθνος εἰς Βαβυλῶνα μετήνεγκεν Ἀμαὶς ἐν τοῦ ἀρχιερέως. τούτων χρόνος ἐστὶ '
  "τῆς ἀρχιερωσύνης τῆς', μήνες ε', ἡμέραι ε'. μετὰ δὲ τὴν ἅλωσιν ἐτῶν οʹ διελθόντων Κῦρος ὁ Περσῶν βασιλεὺς τοὺς "
  'αἰχμαλώτους ἀπέλυσεν εἰς τὴν ἰδίαν πατρίδα. εἰς ὃν τῶν ἀναχθέντων αἰχμαλώτων λαμβάνει τὴν ἀρχιερωσύνην, καὶ '
  "ἐκεῖθεν οἱ ἐξ αὐτοῦ ἔγγονοι ἱ' μέχρις Ἀντιόχου τοῦ Εὐπάτορος, πολιτείας οὔσης ἐν αὐτοῖς δημοκρατορικῆς. καὶ "
  "τούτων δὲ χρόνος ἔτη νιθ'. πρῶτος δ’ οὗτος Ἀντίοχος καὶ ὁ στρατηγὸς αὐτοῦ Λυσίας τὸν Ὀνίαν, ᾧ Μενέλαος "
  'ἐπέκλην, παύουσι τῆς ἀρχιερωσύνης, ἀνελόντες αὐτὸν ἐν Βεροίᾳ, καὶ ἀντικαθιστᾶσιν Ἰάκιμον, γένος μὲν τοῦ '
  'Ἀαρῶνος, οὐ τῆς αὐτῆς δ’ οἰκίας. διὰ τοῦτο καὶ Ἀνανίας ὁ τοῦ τελευτή-',
  'R',
  [{'start': 1554,
    'end': 1562,
    'text': 'τελευτή-',
    'side': 'trailing',
    'qualification': 'Exact printed incomplete word continued on following physical page; not completed from '
                     'another edition.'}],
  [('ἑαδέλφως',
    'εἰσελθεῖν',
    'The compact infinitive remains unresolved; εἰσελθεῖν or εἰσελθέσθαι and exact original remain explicit.'),
   ('Φαναβα',
    'Φανάσου',
    'The compact proper name remains unresolved; Φανάσου or Φανάσᾳ and exact original remain explicit.'),
   ('πρῶτον',
    'πγʹ ἔτη',
    'The small numeral and following types remain unresolved; πγʹ ἔτη or πγʹ ἔτι and exact original remain '
    'explicit. No count of priests is supplied from another edition.'),
   ('κατυχάντες',
    'κατασχόντες',
    'The compact σχ/χ group remains unresolved; κατασχόντες and καταχόντες remain explicit.'),
   ("ἱ' καὶ χ'",
    'ιʹ καὶ χʹ',
    'The small chronology numeral remains unresolved; tentative ιʹ καὶ χʹ or ἰʹ καὶ χʹ and exact original are '
    'retained without harmonizing a historical date.'),
   ("ἐφ'", 'ιγʹ', 'The small numeral remains unresolved; tentative ιγʹ or ιϛʹ and exact original are retained.'),
   ("ἱ' καὶ ἡ",
    'ιʹ καὶ ηʹ',
    'The small pair of numerals remains unresolved; tentative ιʹ καὶ ηʹ or ιʹ καὶ ἡ and exact original are '
    'retained.'),
   ('ἔχον', 'ἔσχον', 'The compact σχ/χ group remains unresolved; ἔσχον and ἔχον remain explicit.'),
   ('Ἀμαὶς ἐν',
    'Ἀμαὲ τοῦ',
    'The compact proper name remains unresolved; Ἀμαὲ or Ἀμαὶς and exact original are retained.'),
   ("τῆς', μήνες ε', ἡμέραι ε'",
    'τξζʹ, μῆνες ςʹ, ἡμέραι ιʹ',
    'The small chronology numerals remain unresolved; τξζʹ/τξςʹ, ςʹ/εʹ, and ιʹ/εʹ remain alternatives alongside '
    'the exact original. No external chronology is substituted.'),
   ('εἰς ὃν',
    'εἷς οὖν',
    'The compact connective remains unresolved; εἷς οὖν or εἷς ὢν and exact original are retained.'),
   ("ἱ'", 'ιεʹ', 'The small numeral remains unresolved; ιεʹ or ιςʹ and exact original are retained.'),
   ("νιθ'",
    'υιδʹ',
    'The small numeral remains unresolved; υιδʹ or νιδʹ and exact original are retained without substituting an '
    'external date.')])]

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
