"""Complete direct source review of retained passages on Bekker printed305.

Both retained columns were inspected in overlapping strips. Compact letter groups
and printed bracketed words remain explicit bounded uncertainties.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T14:19:34.185469+00:00'
_CROPS = {'L':[.055,.10,.455,.755], 'R':[.395,.10,.815,.755]}
_SPECS = [(40,
  1,
  'af9875f99ab5fe484988bba15c632b3ddcce37709ee8a25034a4f1f5cd0e19bc',
  'γῷ τὸν ἄνθρωπον μέρη ἔχοντα κατακωματίζομεν εἰς πολλὰ γένη. εἰ δὲ κεχωρίσθῃ φήσεις τις, ἀνάγκη εἶναι τι τὸ ἀνὰ '
  'μέσον ἀμφοτέρων, ὅπερ καὶ τῶν χωρισμῶν αὐτῶν δείκνυσιν. τοῦτο δὴ ἦτοι ταὐτὸν ὃν ἡμῶν πατέρα τῶν δύο, ἢ ἀνάγκη '
  'πάλιν ἡ ἔνωσις ἢ χωρισμὸν πρὸς τὸ ἕτερον ζητεῖν. ἔνωσιν μὲν ἀδύνατον ἰδεῖν, εἴπερ θατέρω ταὐτὸν εἶναι ἢ '
  'ἡνῶσθαι δίδου· ἡγοῦτο γὰρ ἂν ἕτερος καὶ τὸ ἐξ ἀρχῆς, ᾧ ταὐτὸν εἶναι τοῦτο ἐδόθη. εἰ δὲ κεχωρίσθω ἅπαντι ὁ '
  'λόγος, πάλιν τὸ χωρισμὸν ἅπαντι τόν, ὅπως ἂν ἀπαίρῃω ἡμῖν ἀγινέσθαι ἑαυτὸς ἀναφανῇ, τοῦτο ἂν δ’ ἄρα τις καὶ '
  'τρίτον λέξῃ λόγον, ταύτῃ τὸ μήτε κεχωρίσθω τὸν θεὸν τῆς ὕλης μηδ’ αὐ πάλιν ὡς ἐν μέρει ἡνῶσθαι, εἶναι δὲ ὡς ἐν '
  'τόπῳ [παθώμεν] τῇ ὕλῃ Π.τὸν θεὸν καὶ τὴν ὕλην ἐν τῷ θεῷ, ἀκόντως δὲ ἐὰν τόπον τῷ θεῷ τὴν ὕλην εἴπωμεν, ἐξ '
  'ἀνάγκης καὶ χωριστὸς ἔσαι, τῇ ὕλῃ περιγοσφόμενος, ἢ τῇ ὕλῃ ὁμοίως ἀτάκτως φερόμενος· τῷ γὰρ ἐν φᾶ ἐστι '
  'πλημμελῶς κυκλούμενον, ἀνάγκη καὶ τὸ ἐν αὐτῷ συγκινεῖσθαι. πότερον δὲ ἐνλήρω τὴν ὕλην ὁ θεός, ἢ ἐν μέρει αὐτῆς '
  'ἐτύγχανεν; εἰ μὲν γὰρ ἐν μέρει, μικρότερος αὐτῆς ἄτε δὴ ἐν μέρει αὐτῆς χωρισθεὶς· εἰ δὲ ἐνλήρω, πῶς ταύτην '
  'ἐδημιούργησεν; ἀνάγκη γὰρ ἢ συσολῆν τινα τῷ θεῷ λέγειν, ἢς γυναικὸς ἐδημιούργησεν ἐκεῖνο ἀφ’ ὧ ὑπεχώρησεν, ἢ '
  'καὶ αὐτὸν τῇ ὕλῃ συνδημιουργεῖν, ὅκ ἔχοντα ἰσοχωρήσιον τόπον. εἰ δὲ τὴν ὕλην ἐν τῷ θεῷ εἶναι λέγοι τις; ὅητλον '
  'πότερον ὡς δυσαμίνθᾳς αὐτοῦ ἀφ’ αὐτοῦ, καὶ ὡσπερ ἐν ἀέρι ζῴων ἐπάχη γέννη, μεριζομένου αὐτῷ εἰς ὑποδοχὴν τῶν '
  'γινομένων ἐν αὐτῇ, ἢ ὡσπερ ἐν γῇ ἕδωρ; εἰ μὲν γὰρ ὡς ἐν ἀέρι, μερισὸν ἀνάγκη λέγειν τὸν θεόν· εἰ δὲ ὡς ὕδωρ ἐν '
  'τῇ γῇ, ἢν δὲ ἄτακτος καὶ ἄκοσμος ἡ ὕλη, πρὸς δὴ τοίοις ἔχασιν καὶ κακά, τὸν θεὸν λέγειν ἀνάγκη τῶν ἀκοσμήτων ἢ '
  'κακῶν τούτων αἴτιον. ἢ δρα [γὰρ] ὡς ὕλην ὑποτιθέμενος, ἵνα μὴ τῶν κακῶν ποιητὴν εἴποις τὸν θεόν, δοχεῖον αὐτὸν '
  'τῶν κακῶν εἶναι λέγεις. λέγει δὲ καὶ ἄλλο. φήσῃ τοίνυν ἄποιον ὕλην συνυπάρχειν τῷ θεῷ, ἐξ ἧς τὴν τῷ κόσμῳ '
  'γένεσιν ἐδημιούργησεν; ὅτω μοι δοκεῖ. ἀκάν εἰ ἄποιος ἐτύγχανεν ἡ ὕλη, γέγονε δὲ κόσμος πρὸς τῷ θεῷ, ἐν δὲ τῷ '
  'κόσμῳ αἱ ποιότητες, τῶν ποιοτήτων γέγονε ποιητὴς ὁ θεός; ὅτω ἔχει. “ἔπει δὲ σοι δοκεῖ καὶ ὡς ἀδύνατον ἐξ ἀν',
  'γῷ τὸν ἄνθρωπον μέρη ἔχοντα κατακερματίζομεν εἰς πολλὰ γενητά. εἰ δὲ κεχωρίσθῃ φήσει τις, ἀνάγκη εἶναί τι τὸ '
  'ἀνὰ μέσον ἀμφοτέρων, ὅπερ καὶ τὸν χωρισμὸν αὐτῶν δείκνυσι. τοῦτο δὴ ἤτοι ταὐτόν ἐστιν θατέρῳ τῶν δύο, ἢ ἀνάγκη '
  'πάλιν ἢ ἕνωσιν ἢ χωρισμὸν πρὸς τὸ ἕτερον ζητεῖν. ἕνωσιν μὲν ἀδύνατον ἰδεῖν, εἴπερ θατέρῳ ταὐτὸν εἶναι ἢ '
  'ἡνῶσθαι δίδωσι· ἡγοῦτο γὰρ ἂν ὅπερ καὶ τὸ ἐξ ἀρχῆς, ᾧ ταὐτὸν εἶναι τοῦτο ἐδόθη. εἰ δὲ κεχωρίσθω ἅπαντά σε ὁ '
  'λόγος, πάλιν τὸ χωρίζον ἀπαιτητέον, ἕως ἂν ἀπείρων ἡμῖν ἀγενήτων εὑρετὴς ἀναφανῇ. τοῦτο ἂν δ’ ἄρα τις καὶ '
  'τρίτον λέξῃ λόγον, ταύτῃ τὸ μήτε κεχωρίσθω τὸν θεὸν τῆς ὕλης μηδ’ αὖ πάλιν ὡς ἐν μέρει ἡνῶσθαι, εἶναι δὲ ὡς ἐν '
  'τόπῳ [παθώμεν] τῇ ὕλῃ τὸν θεὸν καὶ τὴν ὕλην ἐν τῷ θεῷ. ἀκόντως δὲ ἐὰν τόπον τῷ θεῷ τὴν ὕλην εἴπωμεν, ἐξ '
  'ἀνάγκης καὶ χωρητὸς ἔσται, τῇ ὕλῃ περιγραφόμενος, καὶ τῇ ὕλῃ ὁμοίως ἀτάκτως φερόμενος· τῷ γὰρ ἐν ᾧ ἐστὶ '
  'πλημμελῶς κινουμένῳ, ἀνάγκη καὶ τὸ ἐν αὐτῷ συγκινεῖσθαι. πότερον δὲ ἐπλήρου τὴν ὕλην ὁ θεὸς, ἢ ἐν μέρει αὐτῆς '
  'ἐτύγχανεν; εἰ μὲν γὰρ ἐν μέρει, μικρότερος αὐτῆς ἅτε δὴ ἐν μέρει αὐτῆς χωρισθεὶς· εἰ δὲ ἐπλήρου, πῶς ταύτην '
  'ἐδημιούργησεν; ἀνάγκη γὰρ ἢ συστολήν τινα τῷ θεῷ λέγειν, ἧς γενομένης ἐδημιούργησεν ἐκεῖνο ἀφ’ οὗ ὑπεχώρησεν, '
  'ἢ καὶ αὐτὸν τῇ ὕλῃ συνδημιουργεῖν, οὐκ ἔχοντα ὑποχωρήσεως τόπον. εἰ δὲ τὴν ὕλην ἐν τῷ θεῷ εἶναι λέγοι τις, '
  'ῥητέον πότερον ὡς διισταμένου αὐτοῦ ἀφ’ αὑτοῦ, καὶ ὥσπερ ἐν ἀέρι ζῴων ὑπάρχει γένη, μεριζομένου αὐτοῦ εἰς '
  'ὑποδοχὴν τῶν γινομένων ἐν αὐτῷ, ἢ ὥσπερ ἐν γῇ ὕδωρ; εἰ μὲν γὰρ ὡς ἐν ἀέρι, μεριστὸν ἀνάγκη λέγειν τὸν θεόν· εἰ '
  'δὲ ὡς ὕδωρ ἐν τῇ γῇ, ἦν δὲ ἄτακτος καὶ ἄκοσμος ἡ ὕλη, πρὸς δὲ τούτοις ἔχουσα καὶ κακά, τὸν θεὸν λέγειν ἀνάγκη '
  'τῶν ἀκοσμήτων καὶ κακῶν τούτων αἴτιον. ἢ ἄρα [γὰρ] ὡς ὕλην ὑποτιθέμενος, ἵνα μὴ τῶν κακῶν ποιητὴν εἴποις τὸν '
  'θεὸν, δοχεῖον αὐτὸν τῶν κακῶν εἶναι λέγεις. λέγει δὲ καὶ ἄλλο. φῂς τοίνυν ἄποιον ὕλην συνυπάρχειν τῷ θεῷ, ἐξ '
  'ἧς τὴν τοῦ κόσμου γένεσιν ἐδημιούργησεν; οὕτω μοι δοκεῖ. ἐὰν δὲ ἄποιος ἐτύγχανεν ἡ ὕλη, γέγονε δὲ κόσμος πρὸς '
  'τοῦ θεοῦ, ἐν δὲ τῷ κόσμῳ αἱ ποιότητες, τῶν ποιοτήτων γέγονε ποιητὴς ὁ θεός; οὕτως ἔχει. ἐπεὶ δέ σοι δοκεῖ καὶ '
  'ὡς ἀδύνατον ἐξ οὐκ',
  'L',
  [],
  [('γῷ',
    'γὰρ',
    'The small conventional abbreviation at the continuation remains uncertain; possible γὰρ and exact original '
    'remain explicit.'),
   ('εἰ δὲ κεχωρίσθῃ',
    'εἰ δὲ κεχωρίσθαι',
    'The compact σθ/θ group and final letters remain unresolved; possible κεχωρίσθαι or κεχωρίθαι and exact '
    'original remain explicit.'),
   ('ταὐτὸν εἶναι ἢ ἡνῶσθαι',
    'ταὐτὸν εἶναι καὶ ἡνῶσθαι',
    'The connective and compact σθ/θ group are uncertain; possible καὶ ἡνῶσθαι or καὶ ἡνῶθαι and exact original '
    'remain explicit.'),
   ('ἡγοῦτο',
    'ἡνοῦτο',
    'The short verb types remain unresolved; possible ἡνοῦτο or ἠνοῦτο and exact original are retained.'),
   ('εἰ δὲ κεχωρίσθω',
    'εἰ δὲ κεχωρίσθαι',
    'The compact infinitive σθ/θ and ending are unresolved; possible κεχωρίσθαι or κεχωρίθαι and exact original '
    'remain explicit.'),
   ('μήτε κεχωρίσθω',
    'μήτε κεχωρίσθαι',
    'The compact σθ/θ group and ending remain unresolved; possible μήτε κεχωρίσθαι or μήτε κεχωρίθαι and exact '
    'original remain explicit.'),
   ('ἡνῶσθαι', 'ἡνῶσθαι', 'The compact σθ/θ group is unresolved; possible ἡνῶσθαι or ἡνῶθαι remain explicit.'),
   ('[παθώμεν]',
    '[καθάπερ]',
    'Printed bracketed complete word; brackets alone do not establish authorship. Preserve the exact old display '
    'and observed bracketed alternative without lexical admission.'),
   ('συγκινεῖσθαι',
    'συγκινεῖσθαι',
    'The compact σθ/θ group is unresolved; possible συγκινεῖσθαι or συγκινεῖθαι remain explicit.'),
   ('χωρισθεὶς',
    'χωρηθείς',
    'The compact consonant group remains unresolved; possible χωρηθείς or χωρισθείς and exact original remain '
    'explicit.'),
   ('[γὰρ]',
    '[γὰρ]',
    'Printed bracketed complete word; brackets alone do not establish authorship. Preserve the exact bracketed '
    'text without lexical admission.')]),
 (40,
  2,
  '19031ef6e2faa328fc53dde0487d426c47ad8420d3301e2a0a1ade754e5cfa85',
  'ὄντων γίνεσθαι τι, πρὸς τὴν ἐποίησιν ἀπόκριναι. δοκεῖ σοι τὰς τῷ κόσμῳ ποιότητας μὴ ἐξ ὑποκειμένων γεγονέναι '
  'ποιοτήτων; δοκεῖ. ἕτερον δέ τι παρὰ τὰς ὁσίας ὑπάρχειν αὐτάς; ὅτως ἔχει. ἀνῦν εἰ μήτε ἐξ ὑποκειμένων ποιοτήτων '
  'τὰς ποιότητας ἠδημύργησεν ὁ θεός, μήτε ἐκ τῶν ὁσιῶν ὑπάρχουσι τῷ μηδὲ ὁσίας αὐτὰς εἶναι, ἐκ μὴ ὄντων αὐτὰς ὑπὸ '
  'θεοῦ γεγονέναι ἀνάγκη εἶναι. περιτὸν ἄρα τὸ δοξάζειν ὡς οὐδὲν ἐξ ἄν ὄντων γίνετ) πρὸς τῷ θεῷ. ἀλλ’ ὁ μὲν περὶ '
  'τούτω λόγος οὐδὲν ἔχειτω. καὶ γὰρ παρ’ ἡμῖν δρῶμεν ἀνθρώπους ἐξ ἄν ὄντων ποιοῦντας τινα, οἷον ἐπὶ τῶν '
  'ἀρχιτεκτονικῶν τὸ παράδειγμα λάβωμεν· ἢ γὰρ ἕτοι ποιῶσι πόλεις ἐκ ἄν πόλεων καὶ ναὺς ἐκ ἄν ναῶν. εἰ δ’ ὅτι '
  'τούτοις ὁσίαι ἐπόκεινθ), οὐκ ἐξ [οὐκ] ὄντων αὐτὰς ταῦτα ποιεῖν, τῷ λόγῳ σφαλῇ. οὐδὲ γὰρ ἡ ὁσία εἶν ἡ ποίησις '
  'τὴν πόλιν ἢ τὸς ναῦς, ἀλλ’ ἡ περὶ τὴν ὁσίαν τέχνη, ἡ ἄν ἐξ ὑποκειμένης τινὸς τέχνης ἐν ταῖς ὁσίαις γίνετ), '
  'ἀλλ’ ἐξ ἄν οὔσης ἐν αὐταῖς γίνετ). ἀπαντήσων δέ μοι δοκεῖ εἶναι τῷ λόγῳ, ὅτι τεχνίτης τῇ ἐν τῇ ὁσίᾳ τέχνῃ '
  'ποιεῖ. σφίμὶ δὲ πρὸς τούτῳ ὅτι οὐδὲ ἐν τῷ ἀνθρώπῳ ἐκ τινὸς ὑποκειμένης τέχνης προσγίνετ). οὐδὲ γὰρ ἐντεῖ τὴν '
  'ἰατρικὴν ὁσίαν δύναι τὴν τέχνην. τῶν γὰρ συμβεβηκότων ἐστ), καὶ τῶν τότε τὸ εἶναι ἔχόντων, ὁπίαν τινὸς γίνετ). '
  'ὁ “μὲν γὰρ ἄνθρωπος καὶ χωρὶς τῆς τεκτο-500H. νικῆς ἕσαι· ἡ δὲ ἄν ἕσαι, ἐὰν μὴ πρῶτον ἄνθρωπος ἦ, οὐδὲν τὰς '
  'τέχνας ἐξ ἄν ὄντων εἰς ἄνθρωπὸς πεφυκέναι γίνεσθ λέγειν ἀναγκαῖον. εἰ τοίνυν τούτῳ οὕτως ἔχεν ἐκ’ ἀνθρώπων '
  'ἰδεῖν, πῶς ἂν προσῆκε τὸν θεὸν μὴ μόνον ποιότητας ἐξ ἄν ὄντων φάναι δύνασθαι ποιεῖν, ἀλλὰ καὶ ὁσίας; τῷ γὰρ '
  'δυνατὸν φαίνεσθαι τὸ γίνεσθαι τι ἐξ ἄν ὄντων, ἢ τὰς ὁσίας ὅτως ἔχειν δεῖν; Πάλιν δὲ διαληπτέον τῶν κακῶν περὶ. '
  'τὰ κακὰ πότερον ὁσίαι σοι δοκοῦσιν εἶναι ἢ ποιότητες ὁσιῶν; ποιότητες. ἡ δὲ ἰλὴ ἄποιος ἢν ἢ ἀχρημάτιστος; '
  'ὅτως. πέλεκται ἄρα τὰ ὀνόματα ταῦτα τῇ ὁσίᾳ ἐκ τῶν συμβεβηκότων αὐτῇ. ὅτε γὰρ ἕσιν ὁ φόνος ἢ οὐσία ἕτι τι τῶν '
  'ἄλλων κακῶν, ἀλλ’ ἐκ τῶν ἐνεργειῶν παρανομάζεται. ὅτε γὰρ φόνος ὁ ἄνθρωπος, ἀλλὰ τῷ ἐπιργηθῆναι τοῦτον '
  'παραωνύμως φονεὺς παρανομάζετ), μὴ ὄν φόνος αὐτός· ὅτε συλλήβδην εἰπεῖν τι τῶν ἄλλων κακῶν ἔσιν ἢ οὐσία, ἀλλὰ '
  'τῷ πρᾶξαι τι τῶν κακῶν',
  'ὄντων γίνεσθαι τι, πρὸς τὴν ἐρώτησιν ἀπόκριναι. δοκεῖ σοι τὰς τοῦ κόσμου ποιότητας μὴ ἐξ ὑποκειμένων γεγονέναι '
  'ποιοτήτων; δοκεῖ. ἕτερον δέ τι παρὰ τὰς οὐσίας ὑπάρχειν αὐτάς; οὕτως ἔχει. οὐκοῦν εἰ μήτε ἐξ ὑποκειμένων '
  'ποιοτήτων τὰς ποιότητας ἐδημιούργησεν ὁ θεὸς, μήτε ἐκ τῶν οὐσιῶν ὑπάρχουσι τῷ μηδὲ οὐσίας αὐτὰς εἶναι, ἐκ μὴ '
  'ὄντων αὐτὰς ὑπὸ θεοῦ γεγονέναι ἀνάγκη εἶναι. περιττὸν ἄρα τὸ δοξάζειν ὡς οὐδὲν ἐξ οὐκ ὄντων γίνετ) πρὸς τοῦ '
  'θεοῦ. ἀλλ’ ὁ μὲν περὶ τούτου λόγος ὧδε ἐχέτω. καὶ γὰρ παρ’ ἡμῖν ὁρῶμεν ἀνθρώπους ἐξ οὐκ ὄντων ποιοῦντάς τινα, '
  'οἷον ἐπὶ τῶν ἀρχιτεκτονικῶν τὸ παράδειγμα λάβωμεν· ἢ γὰρ ἔστι ποιοῦσι πόλεις ἐκ μὴ πόλεων καὶ ναοὺς ἐκ μὴ '
  'ναῶν. εἰ δ’ ὅτι τούτοις οὐσίαι ἐπόκεινθ), οὐκ ἐξ [οὐκ] ὄντων αὐτοὺς ταῦτα ποιεῖν, τῷ λόγῳ σφάλλῃ. οὐδὲ γὰρ ἡ '
  'οὐσία ἐστὶν ἡ ποιοῦσα τὴν πόλιν ἢ τοὺς ναοὺς, ἀλλ’ ἡ περὶ τὴν οὐσίαν τέχνη, ἡ ἄν ἐξ ὑποκειμένης τινὸς τέχνης '
  'ἐν ταῖς οὐσίαις γίνετ), ἀλλ’ ἐξ οὐκ οὔσης ἐν αὐταῖς γίνετ). ἀπαντήσων δέ μοι δοκεῖς ἐνταῦθα τῷ λόγῳ, ὅτι '
  'τεχνίτης τῇ ἐν τῇ οὐσίᾳ τέχνῃ ποιεῖ. φημὶ δὲ πρὸς τοῦτο ὅτι οὐδὲ ἐν τῷ ἀνθρώπῳ ἔκ τινος ὑποκειμένης τέχνης '
  'προσγίνετ). οὐδὲ γὰρ ἔστιν τὴν ἐφ’ ἑαυτῆς οὐσίαν εἶναι τὴν τέχνην. τῶν γὰρ συμβεβηκότων ἐστὶ, καὶ τῶν τότε τὸ '
  'εἶναι ἐχόντων, ὁπόταν ἐν οὐσίᾳ τινὶ γίνετ). ὁ μὲν γὰρ ἄνθρωπος καὶ χωρὶς τῆς τεκτονικῆς ἔσται· ἡ δὲ οὐκ ἔσται, '
  'ἐὰν μὴ πρότερον ἄνθρωπος ᾖ. ὅθεν τὰς τέχνας ἐξ οὐκ ὄντων εἰς ἀνθρώπους πεφυκέναι γίνεσθ λέγειν ἀναγκαῖον. εἰ '
  'τοίνυν ταῦτα οὕτως ἔχειν ἐπὶ ἀνθρώπων ἐδείξαμεν, πῶς οὐ προσῆκε τὸν θεὸν μὴ μόνον ποιότητας ἐξ οὐκ ὄντων φάναι '
  'δύνασθαι ποιεῖν, ἀλλὰ καὶ οὐσίας; τῷ γὰρ δυνατὸν φαίνεσθαι τὸ γίνεσθαι τι ἐξ οὐκ ὄντων, καὶ τὰς οὐσίας οὕτως '
  'ἔχειν δεῖν. Πάλιν δὲ διαληπτέον τῶν κακῶν πέρι. τὰ κακὰ πότερον οὐσίαι σοι δοκοῦσιν εἶναι ἢ ποιότητες οὐσιῶν; '
  'ποιότητες. ἡ δὲ ὕλη ἄποιος ἦν καὶ ἀχρημάτιστος; οὕτως. εἴληπται ἄρα τὰ ὀνόματα ταῦτα τῇ οὐσίᾳ ἐκ τῶν '
  'συμβεβηκότων αὐτῇ. οὔτε γάρ ἐστιν ὁ φόνος ἡ οὐσία οὔτε τι τῶν ἄλλων κακῶν, ἀλλ’ ἐκ τῶν ἐνεργειῶν '
  'παρανομάζεται. οὔτε γὰρ φόνος ὁ ἄνθρωπος, ἀλλὰ τῷ ἐνηργηκέναι τοῦτο παρωνύμως φονεὺς παρανομάζετ), μὴ ὢν φόνος '
  'αὐτός· οὔτε συλλήβδην εἰπεῖν τι τῶν ἄλλων κακῶν ἐστιν ἡ οὐσία, ἀλλὰ τῷ πρᾶξαί τι τῶν κακῶν',
  'R',
  [],
  [('γίνεσθαι τι,',
    'γίνεσθαί τι,',
    'The compact letter group remains unresolved; tentative scan reading γίνεσθαί τι, and exact original are '
    'retained.'),
   ('γίνετ) πρὸς',
    'γίνεται πρὸς',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεται πρὸς and '
    'exact original are retained.'),
   ('ἐπόκεινθ)',
    'ὑπόκεινται',
    'The compact consonant or ending remains unresolved. Tentative scan reading ὑπόκεινται and exact original are '
    'retained; no grammatical restoration is made.'),
   ('[οὐκ]',
    '[οὐκ]',
    'Printed bracketed complete word; brackets alone do not establish authorship. Preserve the exact bracketed '
    'text without lexical admission.'),
   ('ἡ ἄν',
    'ἣ οὐκ',
    'The compact letter group remains unresolved; tentative scan reading ἣ οὐκ and exact original are retained.'),
   ('γίνετ), ἀλλ’',
    'γίνεται, ἀλλ’',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεται, ἀλλ’ and '
    'exact original are retained.'),
   ('γίνετ). ἀπαντήσων',
    'γίνεται. ἀπαντήσειν',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεται. '
    'ἀπαντήσειν and exact original are retained.'),
   ('προσγίνετ)',
    'προσγίνεται',
    'The compact consonant or ending remains unresolved. Tentative scan reading προσγίνεται and exact original '
    'are retained; no grammatical restoration is made.'),
   ('γίνετ). ὁ',
    'γίνεται. ὁ',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεται. ὁ and '
    'exact original are retained.'),
   ('γίνεσθ λέγειν',
    'γίνεσθαι λέγειν',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεσθαι λέγειν '
    'and exact original are retained.'),
   ('δύνασθαι',
    'δύνασθαι',
    'The compact consonant or ending remains unresolved. Tentative scan reading δύνασθαι and exact original are '
    'retained; no grammatical restoration is made.'),
   ('φαίνεσθαι',
    'φαίνεσθαι',
    'The compact letter group remains unresolved; tentative scan reading φαίνεσθαι and exact original are '
    'retained.'),
   ('γίνεσθαι τι',
    'γίνεσθαί τι',
    'The compact γίνεσθαι/γίνεθαι or γίνεται ending remains unresolved. Tentative scan reading γίνεσθαί τι and '
    'exact original are retained.'),
   ('δεῖν',
    'δείκνυται',
    'The compact consonant or ending remains unresolved. Tentative scan reading δείκνυται and exact original are '
    'retained; no grammatical restoration is made.'),
   ('ἀχρημάτιστος',
    'ἀσχημάτιστος',
    'The compact consonant or ending remains unresolved. Tentative scan reading ἀσχημάτιστος and exact original '
    'are retained; no grammatical restoration is made.'),
   ('παρανομάζετ)',
    'παρονομάζεται',
    'The compact consonant or ending remains unresolved. Tentative scan reading παρονομάζεται and exact original '
    'are retained; no grammatical restoration is made.')])]

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
