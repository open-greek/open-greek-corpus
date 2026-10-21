"""Complete direct source review of retained passages on Bekker printed307.

Retained row1 begins at printed line4. Earlier unrepresented continuation lines
were inspected for context but are not inserted into this retained preimage.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:23:38.270607+00:00'
_CROPS = {'L':[.055,.10,.455,.755], 'R':[.395,.10,.815,.755]}
_SPECS = [(42,
  1,
  'e29f2af46b643d3edf36ee31d0536f9e6f9cbd3ee0f41631c35eb90e4df65fa9',
  '11 δὲ μὴ πάντα τὰ πάντα τὰ κακὰ τῶν ἄνδρῶν, τὰ δὲ ἀνδρῶν τῶν ἄνδρῶν τῇ φύσει ἀδύνατον ἐπάρχειν ἑαυτῇ τῇ πικρίᾳ '
  'τῇ φύσει διδαχθεῖσιν πρὸς τινὸς χρηστοῦ, ὅρα ὁποῖον τοῦτον προσάπτειν ἐθέλων τῇ παντοχότῃ καὶ ἀγαθῇ Θεῷ.',
  '11 δὲ μὴ πάντα τὰ πάντα παῦσαι τὰ κακὰ τῶν ἄνδρῶν, τὰ δὲ ἀνδρῶν τῶν ἄνδρῶν τῇ φύσει ἀδύνατον ἐπάρχειν ἑαυτῇ τῇ '
  'πικρίᾳ τῇ φύσει διδαχθεῖσιν πρός τινος κρείττονος, ὅρα ὁποῖον τούτων προσάπτειν ἐθέλεις τῷ παντοκράτορι καὶ '
  'ἀγαθῷ θεῷ.',
  'L',
  [],
  [('11 δὲ μὴ πάντα τὰ πάντα',
    'εἰ δὲ μὴ δεδύνησθαι',
    'The opening compact clause is unresolved; possible εἰ δὲ μὴ δεδύνησθαι or εἰ δὲ μὴ δεδύνηθαι and exact '
    'original are retained. This retained row begins at the fourth printed body line; the three earlier '
    'continuation lines are not silently inserted.'),
   ('τῶν ἄνδρῶν, τὰ δὲ ἀνδρῶν τῶν ἄνδρῶν τῇ φύσει ἀδύνατον ἐπάρχειν ἑαυτῇ τῇ πικρίᾳ τῇ φύσει διδαχθεῖσιν',
    'τὸν θεὸν φῂς, τὸ δὲ ἀδύνατον ἤτοι τῇ φύσει ἀσθενῆ ὑπάρχειν ἔστιν ἢ τῷ νικᾶσθαι τῷ φόβῳ δουλούμενον',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.')]),
 (42,
  2,
  '3fd38e795f8b0352cab74910e3d60f86d98f56f69671112976bde3e219ea04a0',
  'ἀλλὰ πάλιν περὶ τῆς ὕλης ἀπόκριναι, πότερον ἀπλῆ τις ἐστὶν ἡ ὕλη ἢ σύνθετος; εἰ γὰρ ἀπλῆ τις ἐτέχθην ἕλη καὶ '
  'μονοειδής, σύνθετος δὲ ὁ κόσμος ἐκ διαφόρων οὐσιῶν συνεστώς ἐστιν, ἀδύνατον τοῦτον ἐξ ὕλης γενομένη λέγειν, τῷ '
  'τὰ σύνθετα μὴ εἶναι ἐξ ἑνὸς ἀποῖν τὴν οὐσίαν ἔχειν· τὸ γὰρ σύνθετον ἀπλίων εἶναι μὴν μητέτι, ἀλλ’ αὐ πάλιν '
  'φήσομεν λέγειν τὴν ὕλην, πάντως ἐξ ἁπλῶν συνετέθη, καὶ ἂν ποτὲ καθ’ ἑαυτὴ ἀπλῆ, ὧν συντεθετῶν γέγονεν ἡ ὕλη· '
  'τὰ δὲ σύνθετα ἐξ ἁπλῶν τὴν οὐσίαν ἔχει. ἂν ποτὲ καιρὸς ὅτε ἡ ὕλη ἦν, τοτέζε πρὸν τὰ ἀπλᾶ συνέθετο. εἰ δὲ ἂν '
  'ποτὲ καιρὸς ὅτε ἡ ὕλη ἦν, ἂν ἡν δὲ ποτὲ καιρὸς ὅτε ἀγέννητον ἦν ἡν, ἂν ἄρα ἕνα ἀγέννητον ἡ ὕλη· τὸ δ’ ἐντεῦθεν '
  'ὅρα ἕστι πολλά τὰ ἀγέννητα. εἰ γὰρ ἀγέννητος ὁ Θεός, ἂν δὲ ἀγέννητα καὶ τὰ ἀπλᾶ ἐξ ὧν ἡ ὕλη συνετέθη, ἂν ἄρα '
  'ἕστι δύο καὶ μόνον τὰ ἀγέννητα, ἕνα πάρισον τὸ ἐπιζητῆσαι τί ὄντα ἕστιν ἀπλᾶ, ὕλη ἡ εἴδος· πολλά γὰρ ἕτως '
  'ἄτοπα ἀκολουθήσονται.',
  'ἀλλὰ πάλιν περὶ τῆς ὕλης ἀπόκριναι, πότερον ἁπλῆ τίς ἐστιν ἡ ὕλη ἢ σύνθετος; εἰ γὰρ ἁπλῆ τις ἐτύγχανεν ὕλη καὶ '
  'μονοειδὴς, σύνθετος δὲ ὁ κόσμος καὶ ἐκ διαφόρων οὐσιῶν συνεστώς ἐστιν, ἀδύνατον τοῦτον ἐξ ὕλης γεγονέναι '
  'λέγειν, τῷ τὰ σύνθετα μὴ οἷόν τε ἐξ ἑνὸς ἁπλοῦ τὴν σύστασιν ἔχειν· τὸ γὰρ σύνθετον ἁπλῶν τινῶν δηλοῖ μὴν '
  'μητέτι. εἰ δ’ αὖ πάλιν σύνθετον λέγεις τὴν ὕλην, πάντως ἐξ ἁπλῶν συνετέθη, καὶ ἦν ποτὲ καθ’ ἑαυτὰ ἁπλᾶ, ὧν '
  'συντεθέντων γέγονεν ἡ ὕλη· τὰ δὲ σύνθετα ἐξ ἁπλῶν τὴν σύστασιν ἔχει. ἦν ποτὲ καιρὸς ὅτε ἡ ὕλη οὐκ ἦν, τουτέστι '
  'πρὶν τὰ ἁπλᾶ συνελθεῖν. εἰ δὲ ἦν ποτὲ καιρὸς ὅτε ἡ ὕλη οὐκ ἦν, οὐκ ἦν δέ ποτε καιρὸς ὅτε ἀγένητον οὐκ ἦν, οὐκ '
  'ἄρα ἔσται ἀγένητος ἡ ὕλη· τὸ δ’ ἐντεῦθεν ἄρα ἔσται πολλὰ τὰ ἀγένητα. εἰ γὰρ ἦν ἀγένητος ὁ θεὸς, ἦν δὲ ἀγένητα '
  'καὶ τὰ ἁπλᾶ ἐξ ὧν ἡ ὕλη συνετέθη, οὐκ ἄρα ἔσται δύο καὶ μόνα τὰ ἀγένητα, ἵνα παρίδω τὸ ἐπιζητῆσαί τί ὄντα '
  'ἐστὶν ἁπλᾶ, ὕλη ἢ εἶδος· πολλὰ γὰρ καὶ οὕτως ἄτοπα ἀκολουθήσουσιν.',
  'L',
  [],
  [('μὴν μητέτι',
    'μίξιν μητέον',
    'The small noun and abbreviation ending remain unresolved; possible μίξιν μητέον or μίξιν ῥητέον and exact '
    'original are retained.')]),
 (42,
  3,
  'cf8ab7c9ccae13ee353facf27b0d160d4b9c86d0726be40599c54e4a56493686',
  'δοκεῖ δὲ σοι μηδὲν τῶν ὄντων αὐτῷ ἑαυτῷ ἀντικειῖν; δοκεῖ· ἀντικεῖ δὲ τῷ πυρὶ τὸ ὕδωρ, καὶ τῷ φωτὶ τὸ σκότος, ἢ '
  'τῷ ψυχρῷ τὸ θερμόν, ἢ τῷ ξηρῷ τὸ ὑγρόν; οὕτως ἕχει μοι δοκεῖ. ἄκοιν εἰ μηδὲν τῶν ὄντων αὐτῷ ἑαυτῷ ἀντικεῖ, '
  'ἀλλήλοις δὲ ταῦτα ἀντικεῖ, ἂν ἕσον’ ὕλη μία, ὅλὴ μὴν ἐξ ὕλης μιᾶς.',
  'δοκεῖ δέ σοι μηδὲν τῶν ὄντων αὐτὸ ἑαυτῷ ἀντικειῖν; δοκεῖ. ἀντίκειται δὲ τῷ πυρὶ τὸ ὕδωρ, καὶ τῷ φωτὶ τὸ '
  'σκότος, καὶ τῷ ψυχρῷ τὸ θερμὸν, καὶ τῷ ξηρῷ τὸ ὑγρόν; οὕτως ἔχειν μοι δοκεῖ. οὐκοῦν εἰ μηδὲν τῶν ὄντων αὐτὸ '
  'ἑαυτῷ ἀντικεῖ, ἀλλήλοις δὲ ταῦτα ἀντικεῖ, ἂν ἔσται ὕλη μία, ἀλλὰ μὴν ἐξ ὕλης μιᾶς.',
  'L',
  [],
  [('ἀντικειῖν',
    'ἀντικεῖσθαι',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.'),
   ('ἀντικεῖ, ἀλλήλοις',
    'ἀντίκειται, ἀλλήλοις',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.'),
   ('ἀντικεῖ, ἂν',
    'ἀντίκειται, οὐκ',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.')]),
 (42,
  4,
  '40f9925e38b13f44ccb08a62f6c2471d9fa76dd169ad9eec5f97a9e0091e4edd',
  'πάλιν δὲ πυθῶ βούλομαι· δοκεῖ σοι τὰ μέρη μὴ ἀνααιρετικὰ ἀλλήλων εἶναι; δοκεῖ. εἶναι δὲ τῆς ὕλης μέρος τὸ τε '
  'πῦρ ἢ τὸ ὕδωρ, ὁμοίως δὲ καὶ τὰ λοιπά; οὕτως ἕχω. τί δέ, οὐ δοκεῖ σοι ἀνααιρετικὸν μὲν εἶναι τὸ πυρὸς τὸ ὕδωρ, '
  'τὸ δὲ σκότους τὸ φῶς, καὶ τὰλλα ὅσα τοῖτοις παραπλήσια; δοκεῖ. ἄκοιν εἰ τὰ μέρη ἂν ἕσιν ἀλλήλων ἀνααιρετικά, '
  'ταῦτα δὲ ἀνααιρετικά τυγχάνει, ἂν ἄρα ἕστι ἀλλήλων μέρη; εἰ δ’ ἂν',
  'πάλιν δὲ πυθῶ βούλομαι· δοκεῖ σοι τὰ μέρη μὴ ἀναιρετικὰ ἀλλήλων εἶναι; δοκεῖ. εἶναι δὲ τῆς ὕλης μέρος τό τε '
  'πῦρ καὶ τὸ ὕδωρ, ὡσαύτως δὲ καὶ τὰ λοιπά; οὕτως ἔχω. τί δὲ, οὐ δοκεῖ σοι ἀναιρετικὸν μὲν εἶναι τὸ πυρὸς τὸ '
  'ὕδωρ, τὸ δὲ σκότους τὸ φῶς, καὶ τἄλλα ὅσα τούτοις παραπλήσια; δοκεῖ. οὐκοῦν εἰ τὰ μέρη οὐκ ἔστιν ἀλλήλων '
  'ἀναιρετικὰ, ταῦτα δὲ ἀναιρετικὰ τυγχάνει, οὐκ ἄρα ἔσται ἀλλήλων μέρη· εἰ δ’ οὐκ',
  'L',
  [],
  [('πυθῶ',
    'πυθέσθαι',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.')]),
 (42,
  5,
  '9c2be47703146f78db7ac7cbf6139cae8ac713bd4e0a86e2d235edfe74f609b8',
  'ἔχει ἀλλήλων μέρη, οὐκ ἔσονται ἕλης μᾶς. ἀλλὰ μὴν οὐδ’ αὐτ’ ἔσονται ὕλη, τῇ μηδὲν π τῶν ὄντων αὐτὸ ἑαυτῷ '
  'ἀναρκεῖν ἔναι, οὕτως ἂν τῶν ἀντικειμένων ἔχόντων τὸ μὴ εἶναι τὴν ἕλην δείκνυσται.',
  'εἰσὶν ἀλλήλων μέρη, οὐκ ἔσονται ὕλης μιᾶς. ἀλλὰ μὴν οὐδ’ αὖ ἔσονται ὕλη, τῷ μηδέν τι τῶν ὄντων αὐτὸ ἑαυτῷ '
  'ἀναιρετικὸν εἶναι. οὕτως οὖν τῶν ἀντικειμένων ἐχόντων τὸ μὴ εἶναι τὴν ὕλην δείκνυται.',
  'R',
  [],
  []),
 (42,
  6,
  'c8e69ec990007acf67e293d2993803585860a0a23e18f20e43eea383f0b8ca43',
  'περὶ μὲν τῆς ἕλης ἀπευκτῶς ἔχει· “ἕλι δὲ τὴν τῶν κακῶν ἕξευσιν ἵησε.Ὡς δὴ, καὶ ἀναγκαῖον ἀναζητεῖν τὰ παρὰ '
  'ἀνθρώποις. τὰ παρ’ ἀνθρώποις κακὰ πότερον εἴδη τυγχάνει κακὴ ἢ μέρη; εἰ γὰρ εἴδη, ὅσα ἔχει ἕτερον πυρὰ ταῦτα '
  'τὸ κακόν· καὶ αὐτό, ἔστω τὰ γένη ἐν ταῖς εἴδεσιν ἐξετάζω.Ὡς καὶ ἑφεσάμην, εἰ δὲ τῦτο, γεντῶν ἄρα ἔχει τὸ '
  'κακόν· τὰ γὰρ εἴδη γεντῶ ὄντα δείκνυσιν, οἷον φάσις καὶ μοιχεία καὶ τὰ τοιούτοις παραπλήσια. εἰ δὲ μέρη τινὸς '
  'κακοῦ ταῦτα εἶναι ἴσθλοις, ἔχει δὲ ταῦτα γεντῶ, ἀνάγκη κἀκεῖνο γεντῶν ἐπάρχειν. ὅν γὰρ τὰ μέρη γεντῶ, ταῦτα '
  'ὁμοίως ἑξ ἀνάγκης ἑσὶ γεντῶ· τὸ γὰρ ὅλον ἐκ μερῶν συνέσχει. καὶ τὸ μὲν ὅλον ἂν ἔχει μὴ ὄντων τῶν μερῶν, ἔχει '
  'δὲ τινα τῶν μερῶν κἂν μὴ τὸ ὅλον πάσῃ. ὁδὲνὸς δὲ τῶν ὄντων μέρος μὲν ἔστι γεντῶν, μέρος δὲ ἀγέννητον. εἰ δὲ κ’ '
  'τῦτο συγχωρήσωμεν τῷ λόγῳ, ἂν ποτὲ τὸ κακόν, ὅτι ὁλόκληρον ἂν ἦν, ταῦτ’ ἐστι πρὶν δημιουργῆσαι τὴν ἕλην τὸν '
  'θεόν· τότε δὲ ὁλόκληρον γίνεσθαι, ὅτε πρὸς θεῷ γέγονεν ἄνθρωπος· τῶν γὰρ μερῶν τῷ κακῷ ἄνθρωπος ὑπάρχει '
  'ποιητής. κ’ τὸ ἐντεῦθεν ὁλόκληρον εἶναι τὸ κακόν· αὐτὸς ἔστι δημιουργήσας ὁ θεός, ὅπερ ἀσεβές. εἰ δ’ ἄν’ '
  'ὁπότερον τούτων λέγεις τὸ κακόν, πρᾶξιν δὲ τινος κακοῦ εἶναι λέγεις, γεντῶν αὐτὸ ὑπάρχειν μηνίως· ἢ γὰρ τῇ '
  'τινὸς πράξει ἀρχὴν τὰ εἶναι λαμβάνει. πρὸς δὲ τάτοις ὁδὲν ἐπερον παρὰ ταῦτα τὸ κακόν ἑπεὶν ἔχεις. ποίαν γὰρ '
  'πρᾶξιν κακὴν ἑτέραν παρὰ τὸ ἐν ἀνθρώποις δείκνυσιν ἔχεις; ὅτε γὰρ ὁ ἐνεργῶν ὁ κατὰ τὸν τῆς ὁσίας λόγον ὑπάρχει '
  'κακία, ἀλλὰ κατ’ αὐτὸ τὸ ἐνεργεῖν τὸ κακόν, ἡδὴ δέδεικται.',
  'περὶ μὲν τῆς ὕλης αὐτάρκως ἔχει· ἐπὶ δὲ τὴν τῶν κακῶν ἐξέτασιν ἔρχεσθαι δεῖ, καὶ ἀναγκαίως ἀναζητεῖν τὰ παρὰ '
  'ἀνθρώποις. τὰ παρ’ ἀνθρώποις κακὰ πότερον εἴδη τυγχάνει κακοῦ ἢ μέρη; εἰ γὰρ εἴδη, ὅσα ἔσται ἕτερον παρὰ ταῦτα '
  'τὸ κακὸν καθ’ αὑτὸ, τῷ τὰ γένη ἐν τοῖς εἴδεσιν ἐξετάζω.Ὡς καὶ ἑφεσάμην. εἰ δὲ τοῦτο, γενητὸν ἄρα ἔσται τὸ '
  'κακόν· τὰ γὰρ εἴδη γενητὰ ὄντα δείκνυσιν, οἷον φόνος καὶ μοιχεία καὶ τὰ τούτοις παραπλήσια. εἰ δὲ μέρη τινὸς '
  'κακοῦ ταῦτα εἶναι ἐθέλοις, ἔστι δὲ ταῦτα γενητὰ, ἀνάγκη κἀκεῖνο γενητὸν ὑπάρχειν. ὧν γὰρ τὰ μέρη γενητὰ, ταῦτα '
  'ὁμοίως ἐξ ἀνάγκης ἐστὶ γενητά· τὸ γὰρ ὅλον ἐκ μερῶν συνέστηκε. καὶ τὸ μὲν ὅλον οὐκ ἔστι μὴ ὄντων μερῶν· ἔσται '
  'δέ τινα τῶν μερῶν κἂν μὴ τὸ ὅλον παρῇ. οὐδενὸς δὲ τῶν ὄντων μέρος μέν ἐστι γενητὸν, μέρος δὲ ἀγένητον. εἰ δὲ '
  'καὶ τοῦτο συγχωρήσαιμι τῷ λόγῳ, ἦν ποτὲ τὸ κακὸν, ὅτε ὁλόκληρον οὐκ ἦν, τουτέστι πρὶν δημιουργῆσαι τὴν ὕλην '
  'τὸν θεόν· τότε δὲ ὁλόκληρον γίνεσθαι, ὅτε πρὸς θεοῦ γέγονεν ἄνθρωπος· τῶν γὰρ μερῶν τοῦ κακοῦ ἄνθρωπος ὑπάρχει '
  'ποιητής. καὶ τὸ ἐντεῦθεν ὁλόκληρον εἶναι τὸ κακὸν αἴτιος ἔσται δημιουργήσας ὁ θεὸς, ὅπερ ἀσεβές. εἰ δ’ οὐδ’ '
  'ὁπότερον τούτων λέγεις τὸ κακὸν, πρᾶξιν δέ τινος κακοῦ εἶναι λέγεις, γενητὸν αὐτὸ ὑπάρχειν μηνύεις· ἡ γὰρ τοῦ '
  'τινος πρᾶξις ἀρχὴν τῷ εἶναι λαμβάνει. πρὸς δὲ τούτοις οὐδὲν ἕτερον παρὰ ταῦτα τὸ κακὸν εἰπεῖν ἔχεις. ποίαν γὰρ '
  'πρᾶξιν κακὴν ἑτέραν παρὰ τὸ ἐν ἀνθρώποις δείκνυσιν ἔχεις; οὔτε γὰρ ὁ ἐνεργῶν ὁ κατὰ τὸν τῆς οὐσίας λόγον '
  'ὑπάρχει κακία, ἀλλὰ κατ’ αὐτὸ τὸ ἐνεργεῖν τὸ κακὸν, ἤδη δέδεικται.',
  'R',
  [],
  [('ὅσα',
    'οὐκ ἄρα',
    'The small connective types remain unresolved; possible οὐκ ἄρα and exact original are retained.'),
   ('ἐξετάζω.Ὡς',
    'ἐξετάζεσθαι',
    'The compact σθ/θ group and ending remain unresolved; possible ἐξετάζεσθαι or ἐξετάζεθαι and exact original '
    'are retained.'),
   ('ἑφεσάμην',
    'ὑφεστάναι',
    'The compact participial or infinitival ending remains unresolved; possible ὑφεστάναι or ὑφέστηκε and exact '
    'original remain explicit.'),
   ('δείκνυσιν',
    'δείκνυται',
    'The compact verb ending is unresolved; possible δείκνυται or δείκνυσθαι and exact original remain explicit.'),
   ('γίνεσθαι', 'γίνεσθαι', 'The compact σθ/θ group is unresolved; possible γίνεσθαι or γίνεθαι remain explicit.'),
   ('δείκνυσιν',
    'δεικνύνειν',
    'The compact verb ending is unresolved; possible δεικνύνειν or δεικνύναι and exact original remain '
    'explicit.')]),
 (42,
  7,
  '9716346501b49a84a7eb3edd3d5a59a91eac8b5193997fec6ea8ab14c6770574',
  'ὅτι τῇ φύσει κακὸν ὁδὲν ἔστιν, ἀλλὰ τῇ χρήσει γίνεσθαι κακὰ τὰ κακά.',
  'ὅτι τῇ φύσει κακὸν οὐδέν ἐστιν, ἀλλὰ τῇ χρήσει γίνεσθαι κακὰ τὰ κακά.',
  'R',
  [],
  [('γίνεσθαι',
    'γίνεσθαι',
    'The compact σθ/θ group remains unresolved; possible γίνεσθαι or γίνεθαι remain explicit.')]),
 (42,
  8,
  '8bd86069a1e3d0e0a5ca544ca6c93ee9a0ef506e35818423b2ccae52c45082f2',
  'ὅτι αὐτεξούσιον φησι γεγονέναι φημι τὸν ἄνθρωπον ὡς ὡς προϋποκείμενα τινὸς ἡδὴ κακοῦ, οὐ τὴν ἕξασίαν τῷ ἑλάθῃ, '
  'εἰ βούλοιτο, ἄνθρωπος ἐλάμβανεν· ἀλλὰ τὴν τῷ ὑπακούειν τῷ θεῷ καὶ μὴ ὑπακούειν αἰτίαν μόνον ἦν. τοῦτο γὰρ τὸ '
  'αὐτεξούσιον ἐξοῦκετο',
  'ὅτι αὐτεξούσιόν φησι γεγονέναι φημὶ τὸν ἄνθρωπον οὐχ ὡς προϋποκειμένου τινὸς ἤδη κακοῦ, οὗ τὴν ἐξουσίαν τῷ '
  'ἑλάθῃ, εἰ βούλοιτο, ἄνθρωπος ἐλάμβανεν· ἀλλὰ τὴν τοῦ ὑπακούειν τῷ θεῷ καὶ μὴ ὑπακούειν αἴτιον μόνον ἦν. τοῦτο '
  'γὰρ τὸ αὐτεξούσιον ἐβούλετο',
  'R',
  [],
  [('τῷ ἑλάθῃ',
    'τῷ ἑλέσθαι',
    'The compact consonant group or ending, including σθ/θ where present, remains unresolved; this tentative scan '
    'reading and exact original are retained.')])]

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
