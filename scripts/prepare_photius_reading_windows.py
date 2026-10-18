#!/usr/bin/env python3
"""Reproduce source-reviewed Photius comparison windows and exact editorial masks.

This prepares an authority only. It does not change the corpus, choose a reading,
or replace any existing source-confirmed witness abstention.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('data/ingest_reviews/photius-bekker-reading-windows.json')
LIBRARY = Path('data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz')
LIBRARY_SHA = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
NETWORKS = Path('data/corpus_changes/photius-bekker-coverage/full-networks.json.gz')
NETWORKS_SHA = 'a7f867b2c83cdec5ebd77ad04837cbcf6916289adcf2fb1c40047a69db51abe5'
SCAN = {'url': 'https://archive.org/download/bibliothecaexrec00photuoft/bibliothecaexrec00photuoft.pdf',
        'sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6'}
REVIEW_DATE = '2026-10-18'
# Source-reviewed Unicode codepoint windows in the exact joined original blocks.
SPECS = {100: (4048,
       4048,
       'Both columns continue Basil’s theological outline, then introduce genuine internal108TheodoreofAlexandria. '
       'The last actual body phrase is τὰς κατ’ αὐτοῦ. The aggregate running title and smaller notes are absent '
       'digitally.'),
 101: (4063,
       4063,
       'Both columns finish Theodore and introduce genuine internal ClementofAlexandria codices109–111. The final '
       'actual body phrase is τῶν Ἰουδαίων πλάνῃ. The repeated running header, small apparatus and printer signature '
       'are absent.'),
 102: (4004,
       4004,
       'Both columns contain genuine internal ClementofRome codices112–113 and114LeuciusCharinus, ending with the '
       'actual πᾶσαν γένεσιν πονηράν. Internal titles remain body; the aggregate running header and smaller notes '
       'are absent.'),
 103: (3964,
       3964,
       'Both columns finish Leucius and contain genuine internal codices115,116and117onPaschaandOrigen, including '
       'their extended outlines. The final actual body word is οὐδὲν. The running header, smaller apparatus and '
       'printer signature are absent.'),
 104: (4193,
       4193,
       'Both columns continue the Origen discussion and genuine internal118PamphilusandEusebius, ending with actual '
       'τρέπεται διὰ. The repeated running header and smaller critical notes remain outside the digital body.'),
 105: (3993,
       4002,
       'Both columns continue the Origen discussion and contain genuine internal119Pieriusand120Irenaeus. The source '
       'ends ἐκ-, while the digital completes ἐκτιθεὶς; hold that complete word. The aggregate running header and '
       'smaller apparatus are absent.'),
 106: (3874,
       3874,
       'Both columns finish Irenaeus and contain genuine internal '
       'codices121Hippolytus,122–124Epiphaniusand125Justin. Initial printed τιθεὶς continues prior ἐκ- and is absent '
       'digitally. The final actual body phrase is ὁμοίως κατὰ. The aggregate running header and smaller notes are '
       'absent.'),
 107: (4060,
       4060,
       'Both columns finish Justin and include genuine internal126ClementwithPolycarpand127Eusebius, through the '
       'discussion of Arius ending οὐ μὴν ἀλλὰ. The aggregate running title and smaller apparatus are absent.'),
 108: (4037,
       4037,
       'Both columns finish Eusebius and contain genuine internal128Lucian,129LuciusofPatraeand130Damascius, '
       'including the verse quotation. The actual final body word is ἀδύνατα. The running title and smaller critical '
       'notes are absent.'),
 109: (3795,
       3795,
       'Both columns finish Damascius and include genuine '
       'internal131Amyntianus,132–135sophists,136Cyriland137–138Eunomius, ending with καὶ. Their internal headings '
       'are body; the aggregate running title, smaller notes and printer signature are absent.'),
 110: (3667,
       3667,
       'Both columns finish Eunomius and contain genuine internal139–140Athanasius,141–144Basiland145Helladius, '
       'ending with actual ἐκ λέξεων δὲ μόνον. The aggregate running header and smaller apparatus are absent.'),
 111: (3600,
       3600,
       'Both columns finish Helladius and contain genuine internal146–153lexical works with the '
       'PhilostratusandApollodorus comparison, ending at the actual Παυσανίου heading. The top ΛΕΞΙΚΑ running title, '
       'smaller critical notes and printer signature are absent.'),
 112: (3811,
       3811,
       'Both columns finish Pausanias, include genuine internal154–158Boethus,Dorotheus,MoerisandPhrynichus, and '
       'outline the sophistic preparation, ending with actual τὸν ἕκτον. The repeated ΛΕΞΙΚΑ running title and '
       'smaller apparatus are absent.'),
 113: (3803,
       3803,
       'Both columns finish Phrynichus and begin genuine internal159Isocrates with its speech list. The final actual '
       'body sentence ends πόλεμος. The aggregate running title and smaller critical notes are absent.'),
 114: (4146,
       4146,
       'Both columns continue Isocrates and begin genuine internal160Choricius, ending with the actual phrase ὃς '
       'εἰς. The top159–160IsocratesandChoricius running header is separately masked in Qwen3.6; the smaller notes '
       'are absent digitally.'),
 115: (4041,
       4041,
       'Both columns finish Choricius and begin genuine internal161Sopater, including its numbered excerpts and the '
       'Sibyls discussion. The source’s final abbreviated σύγκειτ’ has a digital expanded variant. The '
       'top160–161running title is separately masked in Qwen3.6; smaller notes are absent.'),
 116: (4119,
       4119,
       'Both Sopater columns continue the numbered collections and source lists through actual Θετταλῶν τέ φημι καὶ '
       'Ἀχαιῶν. These lists are full-size body; the repeated running title and smaller apparatus are absent.'),
 117: (4078,
       4078,
       'Both columns finish Sopater and introduce genuine internal162EusebiusagainstAndrew. The actual final body '
       'phrase is εἰ καὶ τῶν φθαρτῶν. The aggregate running title, smaller critical notes and printer signature are '
       'absent.'),
 118: (4139,
       4147,
       'Both columns continue the Eusebius assessment and introduce genuine internal163VindaniusAnatolius. The '
       'printed final word is συνήθροι-, while the independent digital reading ends συνήθου; hold that boundary '
       'word. The running title and smaller notes are absent.'),
 119: (4128,
       4128,
       'Both columns continue Anatolius, then genuine internal164Galenand165Himerius. Printed initial σαι continues '
       'previous συνήθροι-; digital ζαι is retained outside voting as a fragment variant. The actual final body '
       'words are εἰ καὶ τῆς. The aggregate running title, notes and printer signature are absent.'),
 120: (4276,
       4276,
       'Both Himerius columns continue the rhetorical speech list and assessment, ending with actual ἐν τοῖς λόγοις '
       'ἀσεβής. The repeated Himerius running title and smaller critical notes are absent.'),
 121: (3933,
       3933,
       'Both columns finish Himerius and begin genuine internal166AntoniusDiogenes, outlining Dercyllis, Mantinias '
       'and Dinias. The final actual body phrase is τὴν δίκην ὅμως. The running title and smaller apparatus are '
       'absent.'),
 122: (4064,
       4064,
       'Both AntoniusDiogenes columns continue the narrative and its Thule/astronomical observations, ending with '
       'actual καὶ ἔλαττον. The repeated running header and smaller critical apparatus are absent.'),
 123: (4143,
       4143,
       'Both columns finish AntoniusDiogenes, including the lists of fictional predecessors and correspondents. The '
       'actual final body phrase is τὸν χρόνον. The running title and smaller critical notes are absent.'),
 124: (4061,
       4061,
       'The body continues Antonius Diogenes, then begins codex167 Stobaeus and its chapter list. Both columns are '
       'in order through ἐπιβαλεῖν. The top aggregate running header and small footer notes are absent. The internal '
       '167/Stobaeus title belongs to the body.'),
 125: (4245,
       4245,
       'Both Stobaeus columns list the chapters of the anthology through actual περὶ νόσου. The repeated περὶ '
       'headings are the full-size table-of-contents body; the running title, smaller notes and printer signature '
       'are absent.'),
 126: (3645,
       3645,
       'Both Stobaeus columns finish the chapter list and begin the long quoted-author names list, ending with '
       'actual Εὔηνος. All names in the large two-column list belong to the body; dense smaller footer notes and '
       'running title are absent.'),
 127: (3485,
       3485,
       'Both Stobaeus columns finish the quoted authors and historians, followed by the assessment and genuine '
       'internal168BasilofSeleucia with its homily list through actual εἰς τὸν Ἠλίαν. The running title, smaller '
       'notes and printer signature are absent.'),
 128: (3850,
       3850,
       'Both columns finish BasilofSeleucia and introduce genuine internal169Cyril with its five-book theological '
       'outline. The actual final sentence ends οὗτος ὁ λόγος ἔχει. The aggregate running title and smaller notes '
       'are absent.'),
 129: (4146,
       4146,
       'The genuine internal170heading begins the fifteen-book testimonia collection, followed by171Eustratius. Both '
       'columns end with actual αἱ ψυχαὶ αὐταὶ καὶ. The top aggregate running title and smaller apparatus are '
       'absent.'),
 130: (4046,
       4051,
       'Both columns finish Eustratius and contain genuine internal172–174Chrysostom homilies and their outline. The '
       'printed final με- is completed digitally as μετὰ; hold that word, with next-page τὰ handled separately as a '
       'continued-word suffix. The running title and smaller apparatus are absent.'),
 153: (4068,
       4068,
       'Both columns cover the Temenus migration, Romulus narrative, and final Anaphe/Argonaut passage ending αἳ '
       'δῶρον ἦσαν. The top ΔΙΗΓΗΣΕΙΣ running header and small footer are absent. This restores an independent '
       'reading of the Anaphe passage omitted by the shorter fresh witness.'),
 226: (4323,
       4323,
       'Both Diodorus columns continue the anti-fate argument, including animals, parents and slaves. The actual '
       'last body words are κατὰ τοῦ. The repeated223Diodorus running header is separately masked in Qwen3.6; '
       'smaller critical notes are absent digitally.'),
 227: (4343,
       4343,
       'Both columns continue the anti-fate argument about cities, natural changes and animals learning by coercion. '
       'The last actual body words are οὐχ ὅτι ταῦτα. The running title and smaller critical notes are absent '
       'digitally.'),
 228: (4252,
       4252,
       'Both columns continue the anti-fate discussion, beginning with the parrot and proceeding through reason, '
       'crafts and nature. The actual final words are πᾶσι τοῖς. The running title and smaller apparatus are absent; '
       'this replaces the existing bounded digital vote once.'),
 229: (4170,
       4170,
       'Both columns continue the anti-fate discussion and the next numbered argument, ending with actual εἰσὶν '
       'ἕτεροι. The running title, smaller critical notes and printer signature are absent digitally.'),
 230: (4109,
       4109,
       'Both columns continue anti-fate arguments on peoples, kingdoms and the source of evil. The actual final '
       'words are ἀπὸ τῆς εἱμαρμένης. The repeated223Diodorus running header is separately masked in Qwen3.6; '
       'smaller critical notes are absent.'),
 231: (4298,
       4298,
       'Both columns continue the anti-fate argument about evil, natural disasters, divine warnings and anger. The '
       'actual final word is ἀγανακτοῦσιν. The top anti-fate running title is separately masked in Qwen3.6; smaller '
       'notes are absent.'),
 232: (4117,
       4127,
       'Both columns continue the anti-astrology discussion and its numbered chapters. The final printed line ends '
       'with θαυ-, whereas the digital reading completes θαυμιαζὸν; that complete digital word is held outside '
       'voting. No small footer or running header enters the reviewed window.'),
 233: (4270,
       4270,
       'Both columns continue the anti-fate discussion about divination, divine gifts and warnings, ending with '
       'actual πῶς. Printed initial μαζὸν continues previous-page θαυ- and is absent digitally. The repeated '
       'anti-fate running title is separately masked in Qwen3.6; smaller notes are absent.'),
 234: (4113,
       4113,
       'The left column finishes Diodorus against fate; the genuine internal224Memnon heading begins the '
       'right-column Heraclea history. The final actual body words are Ὦχος ὁ. The aggregate running title and '
       'smaller notes are absent digitally.'),
 235: (4303,
       4311,
       'Both Memnon columns recount Clearchus, Satyrus, Timotheus and Dionysius. The printed final φυ- is completed '
       'digitally as φυγάδων; hold that word. The running title and smaller apparatus are absent.'),
 236: (4172,
       4172,
       'Both Memnon columns continue Dionysius, Amastris and Clearchus, ending with actual ἐν οἷς καὶ. Printed '
       'initial γάδων continues prior-page φυ- and is absent digitally. The running title and smaller critical notes '
       'are absent.'),
 237: (4060,
       4071,
       'Both Memnon columns continue the Heraclea history through Lysimachus, Arsinoe, Heraclides and the revolt. '
       'The printed final κατέβα- is completed digitally as κατέβαλον; hold that word. The running title, smaller '
       'apparatus and printer signature are absent.'),
 238: (4137,
       4137,
       'Both Memnon columns continue Seleucus, Zipoetes, Nicomedes, Lysimachus and PtolemyCeraunus. Initial printed '
       'λον continues prior-page κατέβα- and is absent digitally. The final actual word is τρωθέντος. The running '
       'title and smaller apparatus are absent.'),
 239: (4155,
       4155,
       'Both Memnon columns recount Heraclea, Byzantium, Bithynia and the Galatians, ending with actual εἰς. The '
       'running title, smaller notes and printer signature are absent digitally.'),
 240: (4127,
       4127,
       'Both Memnon columns continue Nicomedes, Galatian settlements, Pontic affairs and the Heraclea embassy. The '
       'actual final words are ἐν τῷ. The running title and smaller critical notes are absent.'),
 241: (4042,
       4042,
       'Both Memnon columns recount Ptolemy, Rome, the Syrian wars, Roman diplomacy and Prusias, ending with actual '
       'ἐκ θαλάττης εἰς. Both source columns precede the smaller apparatus, and the running title is absent '
       'digitally.'),
 242: (4055,
       4066,
       'Both Memnon columns recount Heraclea, Bithynia and the opening Mithridatic campaigns. The printed final Μι- '
       'is completed digitally as Μιθριδάτης; hold that word. The running title and smaller apparatus are absent.'),
 243: (4079,
       4097,
       'Both Memnon columns recount Mithridates, Sulla, Archelaus and the siege of Athens. Printed initial θριδάτης '
       'is absent digitally. The printed final συνεξιππασα- is completed as συνεξίππασαμένοις; hold the completed '
       'word. The running title and smaller notes are absent.'),
 244: (4158,
       4158,
       'Both Memnon columns recount the Roman and Pontic campaigns and Heraclea’s dealings with the Roman tax '
       'collectors. Initial printed μένοις is absent digitally. The final actual word is ἀπαιτοῦντες. The running '
       'title and smaller apparatus are absent.'),
 245: (4022,
       4022,
       'Both Memnon columns recount Heraclea, Mithridates, the Roman campaigns and Nicaea, ending with actual '
       'παρθενίαν δὲ μᾶλλον ἢ. No running title or small footer enters the digital body. The existing independently '
       'reviewed fresh-witness header/footer abstention remains active.'),
 246: (4016,
       4016,
       'Both Memnon columns continue Nicaea and the campaigns of Mithridates, including Chalcedon and Cyzicus. The '
       'final actual body word is ἀγορὰν. The running title and smaller notes are absent digitally.'),
 247: (4199,
       4199,
       'Both Memnon columns recount Cappadocia, the Pontic forces and the fighting around Heraclea and Tenedos, '
       'ending with the actual parenthesis ἔδυσαν). The running title is separately masked in Qwen3.6; smaller '
       'apparatus is absent.'),
 248: (4183,
       4197,
       'Both Memnon columns recount Tenedos, the siege of Heraclea and the negotiations of Connacorex and '
       'Damopheles. The printed final εὐ- is completed digitally as εὐδαιμονήσειν; hold that word. The running title '
       'and smaller apparatus are absent.'),
 249: (4106,
       4116,
       'Both Memnon columns recount the capture and plunder of Heraclea, then Sinope and its betrayal. Initial '
       'printed δαιμονήσειν is absent digitally. Final printed στρα- is completed digitally as στρατηγὸς; hold that '
       'word. The running title and smaller notes are absent.'),
 250: (4216,
       4216,
       'Both Memnon columns recount Sinope, Mithridates, Tigranes and Lucullus. Initial printed τηγὸς is absent '
       'digitally. The last actual body words are ἐπιθεὶς τῷ. The running title and smaller apparatus are absent.'),
 251: (4182,
       4182,
       'Both Memnon columns recount the later Roman campaigns and end the sixteenth book with actual τελευτᾷ. The '
       'repeated running title is separately masked in Qwen3.6; smaller apparatus is absent.'),
 252: (4157,
       4157,
       'The left column finishes Memnon’s assessment and introduces genuine internal225Eulogius; both columns '
       'continue its theological discussion through actual διελέγξει. The running title and smaller critical notes '
       'are absent digitally. The current source-confirmed fresh-witness abstentions remain active.'),
 253: (4033,
       4033,
       'Both Eulogius columns continue the theological analysis and quotations, ending with the actual μὴ δυνηθῇ. '
       'The repeated running title, smaller notes and printer signature are absent digitally.'),
 254: (4112,
       4112,
       'Both columns continue Eulogius’s defense of Leo, ending with the actual question that continues on the '
       'following page, διὰ τοιούτων ὥδευσε. The running title and smaller critical notes are absent.'),
 255: (4094,
       4094,
       'Both columns continue Eulogius and contain genuine internal226Eulogius with its Christological discussion. '
       'The actual final body words are καθ’ ἑαυτῶν. The running title, smaller notes and printer signature are '
       'absent digitally.'),
 256: (4083,
       4083,
       'Both columns finish Eulogius’s226discussion and contain genuine internal227against the union of the '
       'Acephali, ending with actual ἐκκλησίας δογμάτων. The distinct top227running title is separately masked in '
       'both fresh checkpoints; the internal227heading remains body.'),
 257: (4313,
       4313,
       'Both columns finish Eulogius227 and contain genuine internal228Ephraim with the letter outline. The actual '
       'last body word is θεολογικὰ. The running title and smaller apparatus are absent digitally.'),
 258: (4072,
       4072,
       'Both Ephraim columns continue the numbered theological outline and quotations, ending with actual ἐν τῷ '
       'σταυρῷ. The repeated running title and smaller apparatus are absent digitally.'),
 259: (4222,
       4222,
       'Both columns continue Ephraim’s theological letters, including Isidore, Justinian, Domitian and the synod. '
       'The actual final body phrase is τὰ αὐτοῦ. The repeated running title and smaller critical notes are absent '
       'from the digital section.'),
 260: (4298,
       4298,
       'Both columns continue Ephraim’s letters and the discussion of Anatolius, ending with the actual phrase ὥστε '
       'ἡ τῶν. The repeated running title, printer signature and smaller apparatus are outside the digital body.'),
 261: (4405,
       4405,
       'Both columns continue the argument about the two natures and the analogy with body and soul. The final '
       'actual phrase is διὰ μιᾶς ἔδει φῦναι τὸ ἓν. The repeated running title and smaller critical notes are '
       'absent.'),
 262: (4309,
       4309,
       'Both columns continue the theological argument and patristic quotations, ending with actual γινωσκέτωσαν δὲ. '
       'The digital section contains the full ordered body rather than the smaller apparatus or repeated title.'),
 263: (4190,
       4190,
       'Both columns continue Ephraim’s patristic evidence, ending with the actual phrase διὰ τὴν ταυτότητα τῆς. The '
       'aggregate running title and smaller critical notes are outside the digital text.'),
 264: (4086,
       4086,
       'Both columns continue patristic quotations, including the reference to Stephen, and end with actual κἀ τὸ '
       'σκεῦος. The repeated running title and smaller apparatus are absent.'),
 265: (4228,
       4228,
       'Both columns continue the theological evidence, including Enoch, Elijah and John, ending with actual ὡς ἐκ '
       'τῶν τριῶν προάγεται. The repeated running title is absent digitally and separately masked in the Qwen3.6 raw '
       'reading; smaller notes are outside the body.'),
 266: (4207,
       4207,
       'Both columns continue the argument about Christ’s generations, ending with actual δύο γὰρ γεννήσεις τοῦ. The '
       'repeated running title, printer signature and smaller apparatus are absent from the digital body.'),
 267: (4062,
       4062,
       'Both columns continue the argument and its patristic quotations, ending with actual τοῦτο δὲ ἑρμηνεύων καὶ '
       'ὁ. The repeated running title and smaller notes are absent.'),
 268: (4208,
       4208,
       'Both columns continue Cyril and other patristic quotations. The final actual body sequence is μὴ ἀγνοῆται '
       'διαφορά followed by καὶ. The repeated running title and smaller apparatus are absent.'),
 269: (4021,
       4021,
       'Both columns continue Ambrose and the scriptural and patristic evidence, ending with the actual unfinished '
       'clause μέλλει ὁ υἱὸς τῶ ἀνθρώπε. The running title, smaller apparatus and printer signature are outside the '
       'digital body.'),
 270: (4172,
       4172,
       'Both columns continue the theological quotations and interpretation, ending with actual τί γὰρ ἂν ἄλλο καὶ '
       'σημανεῖ τὸ. The aggregate running title and smaller critical notes are absent.'),
 271: (4191,
       4191,
       'Both columns continue the argument about the two natures and hypostases, ending with actual οἱ διαιροῦντες '
       'τοίνυν τὰς ὑποστάσεις. The repeated running title is absent digitally and separately masked in the Qwen3.6 '
       'raw reading; smaller notes are outside the body.'),
 272: (4186,
       4186,
       'Both columns continue the theological argument and its patristic witnesses, ending with actual μαρτυρίας αἷς '
       'καὶ ἐν. The repeated running title and smaller critical apparatus are absent.'),
 273: (4110,
       4110,
       'Both columns continue the patristic evidence and its interpretation, ending with actual μονοναχὶ καὶ '
       'συναγείρων. The aggregate running title and smaller notes are absent from the digital body.'),
 274: (4177,
       4177,
       'Both columns continue Ephraim’s patristic evidence, including the interpretation of the two natures, ending '
       'with actual ἑαυτὸν. The repeated running title and smaller critical notes are absent.'),
 275: (4180,
       4180,
       'Both columns continue Ephraim’s response to the theological charges, ending with the actual phrase τό τε '
       'ταπεινὸν τῆς σαρκὸς καὶ. The repeated running title, printer signature and smaller apparatus are absent.'),
 276: (4113,
       4113,
       'Both columns continue the theological response and quotations, ending with actual πῶς ἂν ἀσεβείας τινὸς. The '
       'repeated running title and smaller critical notes are absent from the digital body.'),
 277: (4198,
       4198,
       'Both columns finish the extended theological response and list Ephraim’s letters, ending with actual δεικνὺς '
       'αὐτὰ δυσσεβείας γέμοντα. The repeated running title, smaller apparatus and printer signature are outside the '
       'digital body.'),
 278: (1016,
       1016,
       'The short upper-page body completes Ephraim’s letters and their pastoral purpose, ending with actual '
       'παράκλησίν τε καὶ παραίνεσιν συνεισάγουσαι. The running title and the small apparatus immediately below the '
       'two body columns are absent; the lower page is blank.'),
 34: (4109,
      4109,
      'The Procopius body starts with the Perozes narrative, includes the full-size marginal-quotation paragraphs, '
      'and ends with ὁ δὲ. The top 63. ΠΡΟΚΟΠΙΟΥ and small numbered footer are not in the digital reading.'),
 35: (3902,
      3902,
      'The Procopius narrative covers the Caspian gates, Anastasius, Persian succession, and Belisarius, ending with '
      'Alamundarus advising Cabades. Both columns and their internal quotation paragraphs precede the separate small '
      'apparatus; the running header and notes are absent from this digital body.'),
 36: (3841,
      3841,
      'Both Procopius columns cover the Antioch expedition, Persian succession, Nika revolt, Tribonian, and renewed '
      'Persian war. The last complete printed body word is ὕστερον, also the digital endpoint. The running header '
      'and smaller apparatus are absent.'),
 37: (4021,
      4028,
      'The Procopius body covers the Syrian campaigns, negotiations, plague, and Belisarius at Nisibis/Sisaura. The '
      'digital text completes final printed Περ- as Περσῶν; hold that completed word. The top running header, '
      'smaller notes, and printer signature are absent from the digital body.'),
 379: (3875,
       3875,
       'Both columns contain Himerius’s declamation extracts, including the genuine internal dialogue heading and '
       'its introduction. The actual final word is παρεσκεύασεν. The repeated ΜΕΛΕΤΑΙ running title is absent '
       'digitally and separately masked in the Qwen3.6 raw reading; small notes are outside the body.'),
 38: (4094,
      4094,
      'The page finishes Procopius and begins codex64 Theophanes with its internal heading, then Persian and Turkish '
      'affairs. Both columns end with the printed καὶ. The top running header and small apparatus are absent. The '
      'initial printed σῶν continues prior-page Περ- and has no digital reading, so Source Library abstains on that '
      'suffix.'),
 380: (4079,
       4079,
       'Both columns continue the dialogue introduction and its account of Eros, ending with actual τῆς ἡλικίας. The '
       'top aggregate title and smaller critical apparatus are absent from the digital body.'),
 381: (3859,
       3859,
       'Both columns contain the Himerius extracts and genuine internal introductory headings, ending with actual '
       'φυγὴν καὶ. The repeated running title and small notes are absent. Prior source-confirmed model abstentions, '
       'including the displaced right-lower reading, remain applicable.'),
 382: (4111,
       4111,
       'Both columns continue Himerius’s introductory extracts, ending with actual πρὸς τὰς ἄλλας. Genuine internal '
       'headings remain body; the aggregate running title, small apparatus and printer signature are absent.'),
 383: (3962,
       3962,
       'Both columns continue the declamation extracts, ending with actual μείζονος. The repeated running title and '
       'smaller critical notes are absent from the digital body.'),
 384: (3781,
       3790,
       'Both columns contain Himerius’s declamation extracts and genuine internal introductory headings. The source '
       'ends ἡμέτε-, while the digital completes ἡμέτερος; hold that whole word. The aggregate running title and '
       'smaller notes are absent.'),
 385: (3660,
       3670,
       'Both columns contain the declamation extracts and internal τὸ προοίμιον headings, ending with the '
       'Muses/cicada passage. The digital text starts after the printed continued-word suffix ρος and completes the '
       'final printed χε- as χελιδόνων. The suffix receives no omission vote and the completed final word is held. '
       'The running ΜΕΛΕΤΑΙ header, small footer, and printer signature are absent.'),
 386: (3529,
       3529,
       'Both columns contain the Himerius extracts and genuine internal headings. Initial printed λιδόνων continues '
       'the preceding χε- and is absent digitally, so receives no omission vote. The final actual word is ποίησις. '
       'The repeated running title and smaller apparatus are absent.'),
 387: (3971,
       3982,
       'Both columns contain Himerius’s introductory extracts. The source ends σο-, while the digital completes '
       'σοφώτερος; hold that complete word. The aggregate running title and smaller critical notes are absent.'),
 388: (3717,
       3717,
       'Both columns finish Himerius and contain genuine internal codex244 introducing Diodorus. Initial printed '
       'φώτερος continues the preceding σο- and is absent digitally, receiving no omission vote. The final actual '
       'word is πάντα. The aggregate running title and smaller apparatus are absent.'),
 389: (3793,
       3804,
       'Both columns continue Diodorus’s historical extracts. The source ends συν-, while the digital completes '
       'συνεἰδότων; hold that whole word. The repeated running title and smaller apparatus are absent.'),
 39: (3820,
      3820,
      'The body finishes Theophanes and begins codex65 Theophylact with its internal title and first-book outline. '
      'The right column ends with Philippicus described as the emperor’s brother-in-law. The running title, small '
      'notes, and printer signature remain outside the digital body.'),
 390: (4075,
       4084,
       'Both columns continue Diodorus’s accounts of bodily transformations. Initial printed εἰδότων continues '
       'preceding συν- and is absent digitally, receiving no omission vote. The source ends δίμορ-, while the '
       'digital completes δίμορφον; hold that word. The repeated title and smaller notes are absent.'),
 391: (4013,
       4013,
       'Both columns continue Diodorus and the genuine internal extract from book34 about Jerusalem. Initial printed '
       'φον continues preceding δίμορ- and is absent digitally, receiving no omission vote. The final actual word is '
       'Ἰουδαίων. The running title, printer signature and smaller apparatus are absent.'),
 392: (4095,
       4095,
       'Both columns continue Diodorus’s accounts of Jewish customs and laws, including the genuine internal book40 '
       'extract. The actual final word is ἐκινήθη. The repeated running title and smaller critical notes are '
       'absent.'),
 393: (4011,
       4020,
       'Both columns continue the Diodorus extracts and genuine internal book headings. The source ends το-, while '
       'the digital completes τοσαύτην; hold that whole word. The aggregate running title, printer signature and '
       'smaller apparatus are absent.'),
 394: (3991,
       3991,
       'Both columns continue Diodorus, including the history of the Cappadocian dynasty. Initial printed σαύτην '
       'continues preceding το- and is absent digitally, receiving no omission vote. The final actual phrase is '
       'πανοῦργον μάλιστα. The repeated title and smaller notes are absent.'),
 395: (3879,
       3879,
       'Both columns continue the Cappadocian history and Diodorus’s genuine internal book headings, ending with '
       'actual τῶν παρὰ τὸν. The repeated running title and smaller critical apparatus are absent.'),
 396: (4114,
       4123,
       'Both columns continue Diodorus: Viriathus, then the slave-war/Eunus narrative. The final print ends γέλωτες '
       'ἐγί-, while the digital text completes ἐγίνοντο; the completed word is held. The top 244. ΔΙΟΔΩΡΟΥ running '
       'header and small apparatus are absent.'),
 397: (4165,
       4179,
       'Both columns continue the Diodorus slave-war narrative. Initial printed νοντο continues preceding ἐγί- and '
       'is absent digitally, receiving no omission vote. The source ends ἀποπλη-, while the digital completes '
       'ἀποπληρῦντος; hold that word. The running title and smaller apparatus are absent.'),
 398: (4005,
       4005,
       'Both columns continue the Diodorus Sicilian slave-war narrative and genuine internal book36 heading. Initial '
       'printed ρῦντος continues preceding ἀποπλη- and is absent digitally, receiving no omission vote. The final '
       'actual phrase is τῷ κυρίῳ τῆς κόρης. The repeated title and smaller notes are absent.'),
 399: (4192,
       4192,
       'Both columns continue Diodorus’s Sicilian revolt and Roman history, ending with actual πολλοὺς τῶν. The '
       'repeated running title, printer signature and smaller critical apparatus are absent.'),
 40: (4018,
      4029,
      'Both Theophylact columns outline the Persian and Avar campaigns and the mutiny under Priscus. The source ends '
      'Κων-, while the digital text completes the place name Κωνξαντίνῃ; hold the entire completed digital word. The '
      'top running header and small numbered apparatus are absent.'),
 400: (4119,
       4119,
       'Both Diodorus columns cover the Sicilian revolt and Roman response. The source and digital body end with ὁ '
       'δὲ στρατηγὸς μετὰ ταῦτα τὴν ἐλευθερίαν. The running header and the smaller numbered apparatus remain outside '
       'this digital body.'),
 401: (4081,
       4081,
       'Both columns continue the Diodorus Sicilian revolt and Roman response, ending with actual καὶ. The repeated '
       'running title, printer signature and smaller critical notes are absent from the digital body.'),
 402: (4134,
       4147,
       'Both columns continue Diodorus’s Sicilian slave war and Roman history. The source ends ἐξηλ-, while the '
       'digital completes ἐξηλλαγμένην; hold that complete word. The repeated running title and smaller apparatus '
       'are outside the digital body; marginal references remain raw.'),
 403: (4093,
       4108,
       'Both columns continue Diodorus’s Roman history. Initial printed λαγμένην continues preceding ἐξηλ- and is '
       'absent digitally, receiving no omission vote. The source ends ἐπονο-, while the digital completes '
       'ἐπονομάσαντες; hold that word. The aggregate title and smaller notes are absent.'),
 404: (4062,
       4062,
       'Both columns continue Diodorus’s Roman civil wars. Initial printed μάσαντες continues preceding ἐπονο- and '
       'is absent digitally, receiving no omission vote. The actual final word is ὅμως. The repeated title is absent '
       'digitally and separately masked in the Qwen3.6 raw reading; smaller notes are outside the body.'),
 405: (3602,
       3602,
       'Both columns finish Diodorus and include genuine internal codex245 introducing Plutarch’s Parallel Lives, '
       'followed by the Dion and Brutus extracts. The actual final word is γενναίαν. The aggregate running title and '
       'smaller apparatus are absent.'),
 406: (3746,
       3746,
       'Both columns continue Plutarch’s extracts, including Aemilius, Demosthenes and Brutus, ending with actual '
       'τὴν εὐθὺ τοῦ θανάτου τείνουσαν. Genuine internal headings remain body; the repeated title and smaller '
       'critical apparatus are absent.'),
 407: (3923,
       3931,
       'Both columns contain genuine internal Plutarch extracts from Cicero, Phocion, Cato and Alexander. The source '
       'ends ἀσφα-, while the digital completes ἀσφαλῶς; hold that whole word. The repeated ΠΑΡΑΛΛΗΛΟΙ title is '
       'absent digitally and separately masked in the Qwen3.6 raw reading; smaller notes are outside the body.'),
 408: (3909,
       3909,
       'Both columns continue the Alexander extract and genuine internal Eumenes, Caesar and Sertorius headings. '
       'Initial printed λῶς continues preceding ἀσφα- and is absent digitally, receiving no omission vote. The '
       'actual final word is Ζέφυροι. The aggregate title and smaller notes are absent.'),
 409: (3938,
       3938,
       'Both columns contain the Sertorius, Demetrius and Antony extracts, ending with actual παῤῥησιαζομένους. '
       'Genuine internal headings remain body; the repeated title, printer signature and smaller apparatus are '
       'absent.'),
 41: (4197,
      4197,
      'The Theophylact outline continues through campaigns, Persian succession, Chosroes, and the restoration of '
      'Martyropolis, ending διὰ πυρὸς. The digital reading omits initial printed σαντίνῃ continuing prior-page Κων-; '
      'abstain on that suffix. The running header and small apparatus are absent.'),
 410: (3968,
       3968,
       'Both columns continue Antony and include the genuine internal Pyrrhus, Marius and Aratus extracts, ending '
       'with actual τῶν ἄλλων ὄντων. The repeated running title and smaller critical apparatus are absent.'),
 411: (3780,
       3791,
       'Both columns continue Plutarch’s extracts from Aratus, Artaxerxes, Agis and Cleomenes. The source ends '
       'κρείτ-, while the digital completes κρείττονος; hold that whole word. The aggregate running title and '
       'smaller notes are absent.'),
 412: (3951,
       3951,
       'Both columns finish Plutarch and contain genuine internal codex246 introducing Aristides and the Panathenaic '
       'speech. Initial printed τονος continues preceding κρείτ- and is absent digitally, receiving no omission '
       'vote. The actual final word is κέχρηται. Photius’s internal linguistic comment remains body; running titles '
       'and smaller apparatus are absent.'),
 413: (3950,
       3950,
       'Both columns continue the Aristides Panathenaic extracts, including Photius’s internal linguistic '
       'observations, ending with actual τὰς ἀγγέλες. The repeated running title and the small lower apparatus '
       'remain outside the digital body.'),
 414: (3900,
       3900,
       'Both columns continue the Aristides account of the Persian invasion, ending with actual χρήσασθαι τῇ πόλει. '
       'Photius’s interspersed linguistic comments remain body; the aggregate running title and smaller critical '
       'apparatus are absent.'),
 415: (3628,
       3628,
       'Both columns continue the Panathenaic extracts through the account of the Persian advance, ending with '
       'actual ἕως ἐνέτυχε. Photius’s linguistic comments remain body. The repeated running title is absent '
       'digitally and separately masked in the Qwen3.6 raw reading; smaller notes are outside the body.'),
 416: (4016,
       4016,
       'Both columns continue the Panathenaic extracts and their discussion of the Athenian response and Greek '
       'alliances, ending with actual καὶ. The aggregate running title and smaller apparatus are absent.'),
 417: (3774,
       3774,
       'Both columns continue the Panathenaic extracts and discussion of Athens and Sparta, ending with actual τὰ '
       'ἀπόντα ἐλπίζουσα. Photius’s internal linguistic comment remains body; the repeated title, printer signature '
       'and smaller apparatus are absent.'),
 418: (3923,
       3923,
       'Both columns continue the Panathenaic extracts and discussion of political power, ending with actual μεθείς, '
       'καὶ. The repeated title is absent digitally and separately masked in the Qwen3.6 raw reading; smaller '
       'apparatus is outside the body.'),
 419: (3971,
       3979,
       'Both columns continue the Panathenaic extracts, including the gifts of the gods. The source ends πολ-, while '
       'the digital completes πολλαῖς; hold that whole word. The repeated running title and smaller critical notes '
       'are absent.'),
 42: (4040,
      4040,
      'Both Theophylact columns outline books4–6, including Chosroes, embassies, prodigies, Avar campaigns, and the '
      'closing Priscus clause. The literal final abbreviated ἀποχειροτονεῖθ’ reading belongs to the body; the '
      'running header and small notes are absent.'),
 420: (3893,
       3893,
       'Both columns continue the Panathenaic extracts and their linguistic discussion. Initial printed λαῖς '
       'continues preceding πολ- and is absent digitally, receiving no omission vote. The actual final word is '
       'ἔνειμεν. The running title and smaller apparatus remain outside the digital body.'),
 421: (3684,
       3684,
       'The body finishes the Panathenaic extract and begins codex247 against Plato, retaining its internal numbered '
       'heading and introduction. The final body ends καὶ τοὺς μὲν νόμους. The aggregate running header and dense '
       'smaller apparatus are absent.'),
 43: (3978,
      3978,
      'Both Theophylact columns outline the seventh book and early eighth-book events: Slavic and Avar affairs, '
      'embassies, plague, and Maurice. The final quoted appeal ends with Ῥωμαίων. The top running header and smaller '
      'apparatus remain outside the digital body.'),
 44: (4020,
      4028,
      'Both columns finish the Theophylact outline with the revolt, Phocas, imperial family and flight. The source '
      'ends σύν-, while Source Library completes σύνθημα; hold that completed word. The running header and the '
      'smaller apparatus are absent.'),
 45: (4198,
      4208,
      'Both columns finish Theophylact and begin the internal codex66 Nicephorus and codex67 Sergius headings. '
      'Source Library omits the initial printed continued-word suffix θημα and completes final printed προσ- as '
      'προσήκατο; abstain on the missing prefix and hold that completion. The aggregate running header, apparatus '
      'and printer signature are absent.'),
 46: (3834,
      3834,
      'Both columns contain the end of Sergius, internal codex68 Cephalion and codex69 Hesychius headings, including '
      'the printed gaps and summary of the second book. Source Library omits the initial continued-word suffix ἤκατο '
      'and abstains there. The final printed body word ἐκκοπείς closes the digital body; the running header and '
      'apparatus are absent.'),
 47: (4000,
      4010,
      'Both columns contain the internal codex70 Diodorus, codex71 Dio and codex72 Ctesias openings. Their genuine '
      'body headings are retained. The final printed ἀποκα- is completed digitally as ἀποκαλῶν; hold the completed '
      'word. The separate aggregate running header, apparatus and printer signature are absent.'),
 48: (4072,
      4080,
      'Both Ctesias columns cover Astyages, Cyrus and Croesus through the Indian allies of the Derbices. Source '
      'Library omits printed initial λῶν· and completes printed final ἔφε- as ἐφερον); abstain on the initial suffix '
      'and hold the final completed word/parenthesis. The running header and apparatus are absent.'),
 49: (3908,
      3908,
      'Both Ctesias columns cover the death of Cyrus and the Cambyses/magus narrative through the introduction of '
      'Tibethes. Source Library begins after the initial printed continued-word suffix ρον) and abstains there. It '
      'ends at the actual body ὃν ὁ; the ΠΕΡΣΙΚΑ running header and small apparatus are absent.'),
 50: (3936,
      3936,
      'Both Ctesias columns continue the magus, Darius and Xerxes narrative, ending ὅτι τε. The top 72. ΚΤΗΣΙΟΥ '
      'running header is absent from the digital body and separately masked in the fresh witness; smaller footer '
      'notes are absent.'),
 51: (3886,
      3895,
      'Both Ctesias columns cover Xerxes, Greek battles, and the plot to kill Xerxes. The source ends πεί-, while '
      'Source Library completes πείθεσιν; hold that completed word. The ΠΕΡΣΙΚΑ running header and smaller apparatus '
      'are absent.'),
 52: (3942,
      3942,
      'Both Ctesias columns cover Artaxerxes, rebellions, Inarus, Amytis, and Megabyzus. Source Library omits the '
      'printed initial continued-word suffix θεσιν and abstains there. The final printed body sentence ends τῶν '
      'πεζῶν. The running header and smaller notes are absent.'),
 53: (4023,
      4023,
      'Both Ctesias columns continue Megabyzus, Amytis, Zopyrus and Artaxerxes. The final printed body phrase '
      'ἑπτακαίδεκα δὲ νόθους has a digital word variant, retained as an independent reading. No running header, '
      'smaller note or printer signature enters this body window.'),
 54: (3946,
      3946,
      'Both Ctesias columns cover the succession, Sogdianus, Darius and the Pisuthnes revolt, ending with the actual '
      'body αὐτῷ πίστεις. The running header and separate smaller apparatus remain outside the digital body.'),
 55: (3835,
      3835,
      'Both Ctesias columns cover Pisuthnes, Arsites, court affairs, Cyrus and Clearchus, ending the body with τῶν '
      'σὺν αὐτῷ. The running ΠΕΡΣΙΚΑ header, small apparatus and printer signature are absent.'),
 56: (4025,
      4025,
      'Both Ctesias columns cover the retreat of the Greeks, court punishments and the numbered final-book outline '
      'through Ctesias’s return, trial and acquittal. The final ἄφεσις belongs to the body; the running header and '
      'small notes are absent.'),
 57: (3977,
      3977,
      'Both columns finish the Persian account and discuss Ctesias’s style before introducing the genuine internal '
      'ΙΝΔΙΚΑ heading and its opening descriptions. The final word is the printed καὶ. The separate ΠΕΡΣΙΚΑ. ΙΝΔΙΚΑ. '
      'running header and smaller apparatus are absent from the digital body.'),
 58: (4065,
      4065,
      'Both Indica columns describe the manticore, justice, landscape, animals, lakes, springs, pygmies, palms and '
      'honey, ending with the printed μέλι. The repeated ὅτι clauses are full-size body, not critical apparatus. The '
      'running title and small numbered notes are absent.'),
 59: (4108,
      4108,
      'Both Indica columns describe justice, the royal fountain, minerals, birds, water and dyes, ending with the '
      'actual body βάπτουσι. The running ΙΝΔΙΚΑ title and smaller critical notes are absent.'),
 60: (4178,
      4178,
      'Both Indica columns cover dyes, animal heads, Indian customs, long life and wild asses. The final large-body '
      'phrase is τὰ τέκνα μικρὰ ὄντα. The running title and small numbered apparatus are absent from the digital '
      'reading.'),
 61: (3943,
      3952,
      'Both Indica columns continue wild asses, gold, animals, and springs before the closing assessment of Ctesias. '
      'The source ends γρά-, but the digital reading completes γράφειν; hold that complete word and its following '
      'punctuation. The running header, small apparatus and printer signature are absent.'),
 62: (3785,
      3785,
      'The page finishes Ctesias and begins the genuine internal codex73 Heliodorus heading and Ethiopian narrative. '
      'The initial printed continued-word suffix φειν is absent from Source Library and receives no omission vote. '
      'The digital body ends with the actual Χαρίκλεια, before the small apparatus; the running title is absent.'),
 63: (4151,
      4151,
      'Both Heliodorus columns continue the Ethiopian narrative and its final attribution, ending with the printed '
      'statement of his later episcopal rank. The running header, smaller critical notes and printer signature are '
      'absent from the digital body.'),
 64: (3819,
      3827,
      'Both columns contain genuine internal headings for Themistius, Lesbonax, John Philoponus and Josephus. The '
      'final printed διά- is completed digitally as διάδημα; hold that complete word. The separate aggregate running '
      'title and small critical apparatus are absent.'),
 65: (3901,
      3910,
      'Both columns finish the Josephus summary and begin the genuine internal codex77 Eunapius heading. Source '
      'Library omits the initial printed continued-word suffix δημα and completes final printed στό- as στόματος; '
      'abstain on the former and hold the latter. The aggregate running title and small apparatus are absent.'),
 66: (4066,
      4074,
      'Both columns finish Eunapius and begin the genuine internal codex78 Malchus title and summary. Source Library '
      'omits the initial continued-word suffix ματος and completes the final hyphenated token as σοφισὴς; abstain on '
      'the former and hold the complete final digital word. The aggregate running header and small notes are '
      'absent.'),
 67: (3979,
      3979,
      'Both columns finish the Malchus appraisal and begin the genuine internal codex79 Candidus title and '
      'historical outline. Source Library supplies the two printed Malchus continuation lines omitted by both fresh '
      'witnesses, while omitting the initial continued-word suffix τής and abstaining there. The final δι’ belongs '
      'to the body; the separate running79header and smaller apparatus are absent.'),
 68: (4001,
      4010,
      'Both columns finish Candidus and begin the genuine internal codex80 Olympiodorus title and Stilicho '
      'narrative. The digital final Στελίχων completes the printed Στε- and is held in full. The aggregate running '
      'title and smaller notes are absent.'),
 69: (3904,
      3904,
      'Both Olympiodorus columns contain the historical anecdotes around Stilicho, Alaric, Attalus and Jovian. The '
      'printed initial λίχων continues prior-page Στε- and is absent from Source Library, so it receives no omission '
      'vote. The final Ἰοβιανὸς is a complete body word; the repeated running title, apparatus and printer signature '
      'are absent.'),
 70: (4138,
      4138,
      'Both Olympiodorus columns continue the historical anecdotes, including Roman events, Britain, Constantine, '
      'Jovinus and the Huns. The digital body ends at the printed καὶ. The top running header and smaller apparatus '
      'are outside the digital reading.'),
 71: (3922,
      3922,
      'Both Olympiodorus columns begin the second decade and continue the western imperial affairs and Placidia '
      'narrative. The final λάρνακι is complete. Repeated numbered anecdotes are body; the top running title, small '
      'notes and printer signature are absent.'),
 72: (3979,
      3979,
      'Both Olympiodorus columns cover Ataulf, Valia, the author’s Egyptian observations, Roman civic life and the '
      'famine anecdote. The digital body ends at the complete ἀνῃρέθη. No running title or small apparatus is '
      'present.'),
 73: (3954,
      3954,
      'Both Olympiodorus columns continue embassies, education, the oasis account, imperial affairs and Gothic '
      'succession. The final τὴν ἀρχὴν διαδέχεται is complete, matching the printed body boundary. The repeated '
      'running title and smaller apparatus are absent.'),
 74: (4022,
      4032,
      'Both Olympiodorus columns cover travel, Thracian/Blemmyes observations, Roman wealth and the account of '
      'Boniface. The source ends κρείτ-, while Source Library completes κρείττων; hold that entire completed word '
      'and punctuation. The top running title and small apparatus remain outside the digital reading.'),
 75: (3946,
      3958,
      'Both columns finish Olympiodorus and begin the genuine internal codex81 Theodore heading. The initial printed '
      'continued-word suffix των is absent digitally. The final printed αἱμο- is completed digitally as αἱμομιξίας; '
      'hold that word. The running header and small notes are absent.'),
 76: (3823,
      3823,
      'Both columns finish Theodore and contain the genuine internal codex82 Dexippus and codex83 Dionysius '
      'headings. Initial printed μιξίας continues the prior αἱμο- and is absent digitally. The final printed '
      'Ὀλυμπιάδα is complete. The aggregate running header and small apparatus are absent.'),
 77: (3896,
      3896,
      'Both columns finish Dionysius and include internal codices84,85Heraclianus and86Chrysostom. The right body '
      'ends ἐν before the smaller apparatus and printer signature. The running title is absent; all internal '
      'headings remain in the body.'),
 78: (3931,
      3944,
      'Both columns finish Chrysostom, introduce internal87AchillesTatius and88theNiceneCouncil, and discuss '
      'Gelasius. The source ends ἐπεμνή-, but the digital reading completes ἐπεμνήθημεν; hold that word. The '
      'aggregate running title and small apparatus are absent.'),
 79: (4085,
      4085,
      'Both columns finish the Gelasius discussion and include internal codices89,90Libanius and91Arrian. Initial '
      'printed θημεν is absent digitally and receives no omission vote. The last body word is καὶ. The running '
      'header, smaller notes and printer signature are absent.'),
 80: (4019,
      4019,
      'Both Arrian columns finish the Alexander synopsis through the genuine final ἡ Ἰνδική. The top 91Arrian '
      'running title is absent digitally and separately masked in the fresh witness. The smaller critical notes are '
      'outside the body.'),
 81: (3827,
      3827,
      'The genuine internal codex92 heading begins the account after Alexander. Both columns cover the succession, '
      'regional assignments and Greek affairs, ending with ἐν ἐσχάτῃ πενίᾳ καὶ ἀτιμίᾳ. The repeated top running '
      'title and smaller notes are absent.'),
 82: (4055,
      4067,
      'Both Arrian columns continue the successors narrative through Eumenes and Craterus. The printed final word is '
      'ἀτολμό-, while SourceLibrary completes ἀτολμότεροι; hold the complete word. The top running title and smaller '
      'apparatus are absent.'),
 83: (4016,
      4025,
      'Both Arrian columns continue Eumenes, Perdiccas and the satrapy assignments. Printed initial μότεροι '
      'continues the previous ἀτολμό- and is absent digitally; abstain there. The final printed με- is completed as '
      'μεγίστην digitally; hold that word. The running title and smaller notes are absent.'),
 84: (3914,
      3914,
      'Both columns finish the successors narrative and begin the assessment of Arrian. Initial printed γίστην '
      'continues prior-page με- and is absent digitally. The actual final body word is μετὰ. No running title or '
      'smaller critical apparatus enters the digital body.'),
 86: (4243,
      4243,
      'Both columns finish the Iamblichus assessment and outline Sinonis and Rhodanes, including the repeated '
      'narrative clauses as full-size body. The digital body ends at actual κόρην ἐπὶ before the smaller apparatus. '
      'The running title is absent.'),
 88: (4036,
      4036,
      'Both Iamblichus columns continue the novel synopsis. The initial printed ρεῖς completes previous-page ἐμπει-; '
      'its digital fragment is held outside voting without inventing a joined spelling. The actual final parenthesis '
      'ends τῦτο). The running title and small apparatus are absent.'),
 89: (4163,
      4175,
      'Both Iamblichus columns continue the Sinonis and Rhodanes narrative and the executioner episode. The printed '
      'final word is διασώ-, while the digital body completes διασώζεται; hold that completed word. The running '
      'title and small apparatus are absent.'),
 90: (3967,
      3979,
      'The left column finishes Iamblichus, then genuine internal codex95JohnofScythopolis and96George headings '
      'follow. Initial printed ζεται continues prior-page διασώ- and is absent digitally. The enlarged source ends '
      'βα-, whereas the digital completes βαπτίσματος; hold that whole word. The aggregate running title and smaller '
      'apparatus are absent.'),
 91: (4026,
      4026,
      'Both George columns recount Chrysostom’s education, early ministry and appointment as deacon, ending with '
      'actual ἔτη. Printed initial πτίσματος continues previous-page βα- and is absent digitally. The top Chrysostom '
      'running title is separately masked in Qwen3.6; smaller apparatus is absent digitally.'),
 92: (4102,
      4102,
      'Both George columns recount Chrysostom’s ordination, ministry, imperial appointment, anti-Arian efforts and '
      'Eudoxia. The final actual body word is τῶν. The running title and smaller critical apparatus remain outside '
      'the digital reading.'),
 93: (4067,
      4076,
      'Both columns recount Chrysostom, the visiting bishops and Theophilus’s dispute with the Egyptian monks. The '
      'final printed Ἀμ- is completed digitally as Ἀμμώνιος; hold that completed word. The running title, small '
      'apparatus and printer signature are absent.'),
 94: (4138,
      4138,
      'Both columns continue the Egyptian monks, Theophilus and the proceedings against Chrysostom, ending in the '
      'sentence about the earthquake. Initial printed μώνιος continues prior Ἀμ- and is absent digitally. The full '
      'final printed θεηλάτῳ has an independent digital word variant, retained without correction. Running title and '
      'apparatus are absent.'),
 97: (4149,
      4156,
      'Both columns recount Herodian’s emperors and assess his style, ending printed πά-. SourceLibrary completes '
      'πάσαις; hold that whole word. The repeated ΤΑΜΕΤΑΜΑΡΚΟΝ running title is separately masked in Qwen3.6, and '
      'smaller apparatus is absent.'),
 98: (3640,
      3649,
      'The page finishes Herodian and contains genuine internal codices100–106 with their titles and assessments. '
      'Printed initial σαις is absent digitally. The source ends δυ-, while the digital completes δυναμένα; hold '
      'that whole word. The aggregate running title and smaller notes are absent.'),
 99: (3892,
      3892,
      'Both columns finish Theognostus and begin genuine internal codex107BasilofCilicia, including the numbered '
      'theological outline. Initial printed ναμένῳ continues prior δυ- and is absent digitally. The final actual '
      'body is ἑνώσεως. Running title and smaller notes are absent.')}
HEADER_PREFIXES = {(256, 'Qwen/Qwen3.8-27B-FP8'): '227. ΕΥΛΟΓΙΟΥ ΚΑΤΑ ΤΗΣ ΤΩΝ ΑΚΕΦΑΛΩΝ ΕΝΩΣΕΩΣ.\n\n',
 114: '159. 160. ἸΣΟΚΡΑΤΟΥΣ. ΧΟΡΙΚΙΟΥ.\n\n',
 115: '160. 161. ΧΟΡΙΚΙΟΥ. ΣΩΠΑΤΡΟΥ.\n\n',
 14: '1 — 3. ΘΕΟΔΩΡΟΥ ΠΡΕΣΒΥΤΕΡΟΥ. ΑΔΡΙΑΝΟΥ. NONNOSΟΥ.\n\n',
 153: 'ΔΙΗΓΗΣΕΙΣ.\n\n',
 226: '223. ΔΙΟΔΩΡΟΥ\n\n',
 230: '223. ΔΙΟΔΩΡΟΥ\n\n',
 231: 'ΚΑΤΑ ΕΙΜΑΡΜΕΝΙΗΣ.\n\n',
 233: 'ΚΑΤΑ ΕΙΜΑΡΜΕΝΗΣ.\n\n',
 247: 'ΤΑ ΠΕΡΙ ΠΡΑΚΛΕΙΔΗ.\n\n',
 251: 'ΤΑ ΠΕΡΙ ΗΡΑΚΛΕΙΑΝ.\n\n',
 256: '227. ΕΥΛΟΓΙΟΥ ΚΑΤΑ ΤΗΣ ΤΩΝ ΑΚΕΦΑΛΩΝ ΕΝΩΣΕΩΣ.\n\n',
 265: '229. ΕΦΡΑΙΜΙΟΥ.\n\n',
 271: '229. Εὐραϊμίου.\n\n',
 36: '63. ΠΡΟΚΟΠΙΟΥ.\n\n',
 37: '63. ΠΡΟΚΟΠΙΟΥ.\n\n',
 379: 'ΜΕΛΕΤΑΙ.\n\n',
 396: '244. ΔΙΟΔΩΡΟΥ\n\n',
 404: '244. ΔΙΟΔΩΡΟΥ\n\n',
 407: 'ΠΑΡΑΛΛΗΛΟΙ.\n\n',
 415: 'ΠΑΝΑΓΗΝΑΙΚΟΣ.\n\n',
 418: '246. ΑΡΙΣΤΕΙΔΟΥ\n\n',
 43: '65. ΘΕΟΦΥΛΑΚΤΟΥ.\n\n',
 50: '72. ΚΤΗΣΙΟΥ\n\n',
 57: 'ΠΕΡΣΙΚΑ. ΙΝΔΙΚΑ.\n\n',
 67: '79. ΚΑΝΔΙΔΟΥ.\n\n',
 69: '80. ὈΛΥΜΠΙΟΔΩΡΟΥ.\n\n',
 70: '80. ὈΛΥΜΠΙΟΔΩΡΟΥ.\n\n',
 73: '80. ὈΛΥΜΠΙΟΔΩΡΟΥ.\n\n',
 74: '80. ὈΛΥΜΠΙΟΔΩΡΟΥ.\n\n',
 80: '91. ΑΡΡΙΑΝΟΥ ΤΑ ΚΑΤΑ ΑΛΕΞΑΝΔΡΟΝ.\n\n',
 91: 'ΤΑ ΠΕΡΙ ΤΟΝ ΧΡΥΣΟΣΤΟΜΟΝ.\n\n',
 97: 'ΤΑ ΜΕΤΑ ΜΑΡΚΟΝ.\n\n'}
HELD_SUFFIXES = {105: ' ἐκτιθεὶς',
 118: ' συνήθου',
 130: ' μετὰ',
 232: ' θαυμιαζὸν',
 235: ' φυγάδων',
 237: ' κατέβαλον,',
 242: ' Μιθριδάτης',
 243: ' συνεξίππασαμένοις',
 248: ' εὐδαιμονήσειν',
 249: ' στρατηγὸς',
 37: ' Περσῶν',
 384: ' ἡμέτερος',
 385: ' χελιδόνων',
 387: ' σοφώτερος.',
 389: ' συνεἰδότων',
 390: ' δίμορφον',
 393: ' τοσαύτην',
 396: ' ἐγίνοντο',
 397: ' ἀποπληρῦντος,',
 40: ' Κωνξαντίνῃ',
 402: ' ἐξηλλαγμένην',
 403: ' ἐπονομάσαντες.',
 407: ' ἀσφαλῶς',
 411: ' κρείττονος',
 419: ' πολλαῖς',
 44: ' σύνθημα',
 45: ' προσήκατο',
 47: ' ἀποκαλῶν·',
 48: ' ἐφερον)',
 51: ' πείθεσιν',
 61: ' γράφειν,',
 64: ' διάδημα',
 65: ' στόματος',
 66: ' σοφισὴς',
 68: ' Στελίχων',
 74: ' κρείττων.',
 75: ' αἱμομιξίας.',
 78: ' ἐπεμνήθημεν.',
 82: ' ἀτολμότεροι',
 83: ' μεγίστην',
 89: ' διασώζεται.',
 90: ' βαπτίσματος',
 93: ' Ἀμμώνιος',
 97: ' πάσαις',
 98: ' δυναμένα'}
FIRST_FRAGMENTS = {106: 'τιθεὶς',
 119: 'σαι',
 233: 'μαζὸν',
 236: 'γάδων',
 238: 'λον',
 243: 'θριδάτης',
 244: 'μένοις',
 249: 'δαιμονήσειν',
 250: 'τηγὸς',
 38: 'σῶν',
 385: 'ρος',
 386: 'λιδόνων',
 388: 'φώτερος',
 390: 'εἰδότων',
 391: 'φον',
 394: 'σαύτην',
 397: 'νοντο',
 398: 'ρῦντος',
 403: 'λαγμένην',
 404: 'μάσαντες',
 408: 'λῶς',
 41: 'σαντίνῃ',
 412: 'τονος',
 420: 'λαῖς',
 45: 'θημα',
 46: 'ἤκατο',
 48: 'λῶν·',
 49: 'ρον)',
 52: 'θεσιν',
 62: 'φειν',
 65: 'δημα',
 66: 'ματος',
 67: 'τής',
 69: 'λίχων',
 75: 'των',
 76: 'μιξίας',
 79: 'θημεν',
 83: 'μότεροι',
 84: 'γίστην',
 88: 'ρεῖς',
 90: 'ζεται',
 91: 'πτίσματος',
 94: 'μώνιος',
 98: 'σαις',
 99: 'ναμένῳ'}
REGIONS = {100: {'body': [0.035, 0.055, 0.975, 0.812], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.732, 0.975, 0.812]},
 101: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 102: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 103: {'body': [0.035, 0.055, 0.975, 0.838], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.758, 0.975, 0.838]},
 104: {'body': [0.035, 0.055, 0.975, 0.838], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.758, 0.975, 0.838]},
 105: {'body': [0.035, 0.055, 0.975, 0.843], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.763, 0.975, 0.843]},
 106: {'body': [0.035, 0.055, 0.975, 0.853], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.773, 0.975, 0.853]},
 107: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 108: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 109: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 110: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 111: {'body': [0.035, 0.055, 0.975, 0.843], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.763, 0.975, 0.843]},
 112: {'body': [0.035, 0.055, 0.975, 0.843], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.763, 0.975, 0.843]},
 113: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 114: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 115: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 116: {'body': [0.035, 0.055, 0.975, 0.853], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.773, 0.975, 0.853]},
 117: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 118: {'body': [0.035, 0.055, 0.975, 0.843], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.763, 0.975, 0.843]},
 119: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 120: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 121: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 122: {'body': [0.035, 0.055, 0.975, 0.842], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.762, 0.975, 0.842]},
 123: {'body': [0.035, 0.055, 0.975, 0.845], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.765, 0.975, 0.845]},
 124: {'body': [0.035, 0.06, 0.975, 0.84], 'first': [0.035, 0.06, 0.51, 0.16], 'last': [0.5, 0.75, 0.975, 0.84]},
 125: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 126: {'body': [0.035, 0.055, 0.975, 0.75], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.67, 0.975, 0.75]},
 127: {'body': [0.035, 0.055, 0.975, 0.755], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.675, 0.975, 0.755]},
 128: {'body': [0.035, 0.055, 0.975, 0.804], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.724, 0.975, 0.804]},
 129: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 130: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 153: {'body': [0.035, 0.065, 0.975, 0.845], 'first': [0.035, 0.065, 0.51, 0.16], 'last': [0.5, 0.75, 0.975, 0.845]},
 226: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 227: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 228: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 229: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 230: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 231: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 232: {'body': [0.035, 0.065, 0.975, 0.85], 'first': [0.035, 0.065, 0.51, 0.16], 'last': [0.5, 0.77, 0.975, 0.85]},
 233: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 234: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 235: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 236: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 237: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 238: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 239: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 240: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 241: {'body': [0.035, 0.055, 0.975, 0.855], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.775, 0.975, 0.855]},
 242: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 243: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 244: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 245: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 246: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 247: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 248: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 249: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 250: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 251: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 252: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 253: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 254: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 255: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 256: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 257: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 258: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 259: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 260: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 261: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 262: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 263: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 264: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 265: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 266: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 267: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 268: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 269: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 270: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 271: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 272: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 273: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 274: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 275: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 276: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 277: {'body': [0.035, 0.055, 0.975, 0.86], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.78, 0.975, 0.86]},
 278: {'body': [0.035, 0.055, 0.975, 0.29], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.21, 0.975, 0.29]},
 34: {'body': [0.035, 0.06, 0.975, 0.84], 'first': [0.035, 0.06, 0.51, 0.16], 'last': [0.5, 0.75, 0.975, 0.84]},
 35: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 36: {'body': [0.035, 0.055, 0.975, 0.812],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7320000000000001, 0.975, 0.812]},
 37: {'body': [0.035, 0.055, 0.975, 0.812],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7320000000000001, 0.975, 0.812]},
 379: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 38: {'body': [0.035, 0.055, 0.975, 0.813], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.733, 0.975, 0.813]},
 380: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 381: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 382: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 383: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 384: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 385: {'body': [0.035, 0.05, 0.975, 0.825], 'first': [0.035, 0.05, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.825]},
 386: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 387: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 388: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 389: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 39: {'body': [0.035, 0.055, 0.975, 0.785],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7050000000000001, 0.975, 0.785]},
 390: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 391: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 392: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 393: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 394: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 395: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 396: {'body': [0.035, 0.05, 0.975, 0.825], 'first': [0.035, 0.05, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.825]},
 397: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 398: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 399: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 40: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 400: {'body': [0.035, 0.06, 0.975, 0.84], 'first': [0.035, 0.06, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.84]},
 401: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 402: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 403: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 404: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 405: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 406: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 407: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 408: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 409: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 41: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 410: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 411: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 412: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 413: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 414: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 415: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 416: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 417: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 418: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 419: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 42: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 420: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 421: {'body': [0.035, 0.05, 0.975, 0.765], 'first': [0.035, 0.05, 0.51, 0.15], 'last': [0.5, 0.7, 0.975, 0.765]},
 43: {'body': [0.035, 0.055, 0.975, 0.79],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7100000000000001, 0.975, 0.79]},
 44: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 45: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 46: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 47: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 48: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 49: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 50: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 51: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 52: {'body': [0.035, 0.055, 0.975, 0.815], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.735, 0.975, 0.815]},
 53: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 54: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 55: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 56: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 57: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 58: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 59: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 60: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 61: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 62: {'body': [0.035, 0.055, 0.975, 0.78],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7000000000000001, 0.975, 0.78]},
 63: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 64: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 65: {'body': [0.035, 0.055, 0.975, 0.81],
      'first': [0.035, 0.055, 0.51, 0.15],
      'last': [0.5, 0.7300000000000001, 0.975, 0.81]},
 66: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 67: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 68: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 69: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 70: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 71: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 72: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 73: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 74: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 75: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 76: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 77: {'body': [0.035, 0.055, 0.975, 0.843], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.763, 0.975, 0.843]},
 78: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 79: {'body': [0.035, 0.055, 0.975, 0.842], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.762, 0.975, 0.842]},
 80: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 81: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 82: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 83: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 84: {'body': [0.035, 0.055, 0.975, 0.84], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.76, 0.975, 0.84]},
 86: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 88: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 89: {'body': [0.035, 0.055, 0.975, 0.85], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.77, 0.975, 0.85]},
 90: {'body': [0.035, 0.055, 0.975, 0.82], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.74, 0.975, 0.82]},
 91: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]},
 92: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 93: {'body': [0.035, 0.055, 0.975, 0.835], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.755, 0.975, 0.835]},
 94: {'body': [0.035, 0.055, 0.975, 0.838], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.758, 0.975, 0.838]},
 97: {'body': [0.035, 0.055, 0.975, 0.832], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.752, 0.975, 0.832]},
 98: {'body': [0.035, 0.055, 0.975, 0.83], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.75, 0.975, 0.83]},
 99: {'body': [0.035, 0.055, 0.975, 0.825], 'first': [0.035, 0.055, 0.51, 0.15], 'last': [0.5, 0.745, 0.975, 0.825]}}
# Full-page images inspected for this authority, rendered from the pinned PDF.
IMAGE_SHAS = {100: '9be98fd9b59315756ade83a12abb83ad90d41cd6bb8306b225a518f1e63dac90',
 101: '46153b08101005591a2c40ae1f789585063756aed266c5ba052bf43690b2864a',
 102: 'ffbb4943ae1741724e0e19d012f7c01c6568c78844b019dbe57a722a498f0ae2',
 103: '402861e3d81fef791c6076f7ddc458f5ae5df8b557f605cc67d2deec810d3e64',
 104: '688bb263275256ff703ed57e71a88b3ecae26405f707881f38dd23265a7bd73d',
 105: '9777b9a101409fe0a16de3d31662679bb746804c7c12e03e26ba333a9eafd942',
 106: '4485c4981a5f9c49a6bcc59254e75b8512b0fd3bd31b2cb7effb7945a13060bf',
 107: '4c6293a5e023a1ab2a7a27fc118cac599974c729a18fac168ecf7c55376fe0c4',
 108: 'b825c7c85353795f9d024fe31895cee46ee959587c9173b3336f45ca0c6700bd',
 109: '8bc93a7d732b0e5ba4acf388fd23d72a572737e12a512946e4492797b7537cb8',
 110: '4d1346c26ad1152cfd704d9d2f2b5116c7e04e738c3b1f36c70988f7b035eee4',
 111: 'a1f627524b2f55e9040383adf3d3926debec14a43065a0cfca7d1779d5be1d31',
 112: '961d07dd9489c332aa85eb2589ee538efdf77cd51ea1b1d445d29649914a1d33',
 113: '220412b212b7107f2363587c40cae37743d776e6f6154dca9f468b9319800f6f',
 114: 'd6c68ab902392d5c8af008d760f9507df3382700c4c010f9cf9d3160c5ed6924',
 115: 'b26db00ed03cd30d1c774bd3b1da7a25e5c8ce60f8319ed03107d7ab4ecdd6d4',
 116: '1a151101c6f1944db84966afd0f6d904f2fd984429e1c21d64b88d0406b11146',
 117: 'aa5e1845612428aa2faf0faf4ae42a92d091f3e6c23333f9e7abe2920832f182',
 118: '3d43b1cebe772bd31ca32a7356e6fe9fb9a191605b51b509137647a904b013ff',
 119: '2ff919b1d07ba2992a8ee09565305ac2e93fa3b8e4313287adceb3cfeea709c4',
 120: '353bdd118d7fb6682d6e20af20297b476c6ec1946dd70d970fd4fea326c89d47',
 121: '419cf2bb47fbe60cf8f35d9a95aa2d6d6fd41ce2888f255e964080aaada1ae6a',
 122: 'd3bfce81917d5027670df30467d4f9b565260630497a2ea497a93f3ca3660912',
 123: '607fba24a0b6d807ff924ab1f8c961797e275beec11ccbf750826f0ca72394f9',
 124: 'c622e0ce8cec9aeb909d366bd5bf5ccc20c49becc4325a82fd113f4af31a5313',
 125: '9d77a9cb1082844323773c8f38f109085d191c29a3d2e663c26fcbfb35717b78',
 126: '98893aafde5d7776fb19a51de59e70415347e7f4a02ed9b944b5357556272c6a',
 127: 'bfdef9989d047be21efe19886d8db21892ae38fd87dd8635937acd5883afc137',
 128: 'ca7bc1cfbb8a026d0635059f61a623c676514a70632580b0132a6d55122e134c',
 129: '303ac3f1c1b6155b632fc229ecc8e143425e33b2ad07ee3183daf2387530ca58',
 130: 'abb02dbc4b9373cfe5f17c17cf2a02152b15e6626b54c90dfebe0f59126ea6f2',
 14: '8f5b81d5885a11fad281f962c57ad414ef7d8ff117c5eed4e4df71167c7c060a',
 153: '2f99104828b9932c8f51f5163736e192ef9695be5b36c7ff19b30dba99dbddc7',
 226: '6d52daa2c8502fd26d8e632fafeb2a5d30b0ea137a996ac3662e5812a72d997d',
 227: 'e110d01953908f7c2cd35c21f6a018d470cd55d1fc01ca7dff052a5f295b0bc7',
 228: '1daf711e1196bbf51b7f2b97c5d507b3459af50c6ce8d97ecc009a9029976632',
 229: '4d7806ded8620c3139427fb714022ad28f7d4a4046abbd091f7b651f6f62d3ad',
 230: '772b171f13fbd7b6d01566389c63dc83d2e597f4a0016d8a12fce3bd67a672c6',
 231: 'b0dc3b6ec59eadb8334d0f5e111004a69b8fd29e86ee5ab5b55609ae4dd97666',
 232: '36bf1e74fc82cb9efcbfe6e87da8bc62abdc6680bd39d9cc05c6d56499ddc0c9',
 233: 'e58acf53437a95b48800f368654793b25e7022b35ac21cf665566981b53f2838',
 234: 'b6ec48de6c0485ea8d792ddcc21a6277e2dde5d5c5a2dbe5220149a21185857d',
 235: 'c10ef654075266e1b7cb68ae1eb3f25ca26b54ba0299acb16679413e87812bbb',
 236: 'ff79fb9c53611a3394d2ec4cff1416c22274bad2a2aa5abb649450ca3127a96f',
 237: 'b8f14433b255b0e187a7e1b9ebb69e37ec19fe6d28923a7d1c237d4c99e7235b',
 238: '773967e8a68df5f30a092bf9d40e4e5bec727ede2062307c6c613569e0482b9d',
 239: '86cdde0d9c7deedaad6d68cfccf419e093f1dc2891b7458a8fe623b0098b700b',
 240: '862e4e7b63849f148ae5e7f773d9d4e7ff2788ffd209b252a76743a8d35dbc8f',
 241: '56a00be87e0d6a255058c3b92727376f9bde7d4e6d625efeab84ba69de483851',
 242: '264365b0034433c712340540963e9bc06ca5a8739ace9b8b5cd080b059a67355',
 243: 'e798ed05fcd4f98b41fc60e4efbbdd83d203f85d43d765354f6cf8b26536da2b',
 244: 'c9c112a3953b51acf413f7377741d373754327b5a694aa774a606d06f4f827fa',
 245: 'bbe0a341ef85ad467cebe22383e4c5574015626b5e86c13c517ec4cf1e7922a1',
 246: 'b59af04e3d6a21f6a5cc465efbee830b0c8316b89653ec1f1f9b77dc7fb913af',
 247: '5204aeb399c1aa0f0e8b3f07f1b79c114dfd7202354308f706cbdfac68c5f43f',
 248: 'e7b94c2a81e4c30ec2d08959e6001d2839b12a564f1268385399bb4e5b7c68e9',
 249: '85031eb6ed15810a9e5632b09a502126ac264c4aaf7c84e9fd62290f654923fb',
 250: '7a3c2e180467e3b39f7d437d689c60614b06ad645ee69f27fef15e85248bd29d',
 251: 'e18c790585d37e89fc29f4060e727570f5a98c632270de42afacc016155d21eb',
 252: '1f37c3e298563db35f6d7d89b0eb96fa3b1a27e63aab69db3e5a17d105a85fe0',
 253: '61ae4d14174244bb599f13205ee005b189f685969f53526d38fac1cc6fcaf14a',
 254: '3d44c155cf8ba9bcfb262692c56a361ce62d06edb46792da2aba53bcc9370a9d',
 255: '36faa62993b1daefa90f21e4b5a6e8eff44c91364a11db7e4ee0040e97911a2e',
 256: '268463d3e8ef1b0f6d4893a4b9b3fd2035a738ef685e143ee3c35b7ea2fb6bf8',
 257: 'e98195bd15bb87a21c00f5df63fc2fbc86c33df4c218883abdaff069c9f8fcf1',
 258: '41daf14eb7526f9679326d34a60a517ee296f2bd1190396e3814368891cd4915',
 259: 'ab9607f7ca209b1ed3610f0d206cb9a26e942f6a347aba0cf84aca52be8c4d8d',
 260: 'fc7fc7411f5d44fc9a7f58a8ffd7c30da821d6ec5dd8cb41df231b4b07f879f3',
 261: '9bc305d05a95dedb52e353c77a7432dbea0782a910383ac02cfcbd347014dccc',
 262: '34ba0454548e483711f7b4af8251272347d03817da495c2828ddf881cc704914',
 263: 'd48668164ff50791883427f3d7d15a67efb2ff8f72be64209aa71dd1056ef4f2',
 264: 'cefa2680588941f24821dc0558943c97b4d281ec0ee337dcb6db390528d8de90',
 265: '0c6cae99402a3b0caf3919d8377bf7b18178102644729e84d767bec3cc6d1dfa',
 266: 'c9a1d7137f27d5310d81a0458bd9ff5c0594f3ca45936db998f880a2afed589c',
 267: '30cde90ac0abc416679158e7737d1ed84c7fb2142ce285829ba253b68914be47',
 268: 'b3e164de7aac3fa2d870aab71f62052b2f06261b397ff78df88dd15162f77d57',
 269: '7f0c7f2cdae3b1b62b01905ffe9dab12d0f1fdd27aa377128be9a724dbdf0524',
 270: 'ba62ebd11d465c84e48fe40d7ea4e9d04980c4ffaa01a14b59da3082fb7f4369',
 271: '93a43f55f1f4e5ddeec1aa1f4072a0766e27d3f2e28e4aed485da3c09414fa7e',
 272: 'e8fe757a69ecc62d384ccb641b47722d8a6f7438d08ac4bd5556f70ca46947d4',
 273: 'b93208a59489a282ef6d534656ded425f4d357684a25b7819970ea7fd72774dc',
 274: 'fdd355a05bccc0dc6cb44403aeffb61a69fb16fcbbe1b38d7340c5fa20a35ac9',
 275: 'a3616fe1d355fca9aa9322b9434367d370b87e2d21c3cd6d1866420d061d0092',
 276: '30fc50fbfe3b24d8a1c1e7e575097aaa7daa849a20b45a5b1f5f7643d731e18c',
 277: '57fd9c45f5c92968203e88bb0a790b97b8411d2a6cddfe62b91733d1d7037d5d',
 278: 'dda25fa667efa48b2d1d68aa4123038a25a4ffa4d1903e1fe3d249501eb50235',
 33: 'd20b0be85c08154cba07d53a39df825684b101102bccc00f195b3595eec3734e',
 34: 'd55b56dd905c43f0ec844ed2678ce40a23b3177bab426e47b7a4696d77f51919',
 35: 'd3a57a9467f6ce14518828df0e96e6a8c789379cb32e6385bc52f11722dd250e',
 36: 'ff7fb74b170fa0f60403b461929073b172be8ea07a675e887497e326fab49396',
 37: 'e565c1249911102d4afbfec5f22c5a140000c97ea936788a1f03878141598355',
 379: '8c960ce66fe20509c455e63ef17fd67265b93edc2cf98d22e85006ff0212b8ea',
 38: 'c76d04bb23be3af0e0e2d4634a4bce4d8c3caafba8c04a35238e98615e7ef789',
 380: '101a036ab97a554426fd0a1ca8dfe1a416f25630e7b4a6d3f58c1ae526937353',
 381: 'c9421ae116a2a0de461ff0b704f4c7ddd392980e8c12690357670886ae106651',
 382: '5dcc97393fc38a2aefe3ad8c3352311bf7e5db89f887b6e3ed6a0ee6d71d0043',
 383: '76a4dbc8ed6e3ab80d51ea4f1448ca267768cdd6b04206e4fb73cfb6c0272c86',
 384: '56b0dfcee335e85151544eb78b65bbb3e2a189abffbf9b6670b55bd97f32fd54',
 385: '00b3b9d386d9fac4a32746469901cd100939dd541e5ee49d279ad4e29ffe2885',
 386: '8c3ac3485ebbf4100d68b65481a7eabdc1faf18498af6806ad9c60d73cf4d1cc',
 387: '177c17824dfd0e24e9778bcb2a3642ac7da0a420c3c102a7deeddac1871a6889',
 388: 'ae0f074e2997ccf35da5dbfc5c958483a9ddfaa3ab37930f37d6c27865c3f926',
 389: '22408846c1761c668d9c128c4ca0274ece5970579cb3bd0fd0f370757cb417f1',
 39: 'bd86fa2b5fe44c6fcd82659dbe19bb5bbe778aa9c16ca0ca4024f7a6b6a6e522',
 390: '76f6110c6561600366d122d05467ad331f53fd21b1ffe951b254fc9b2e4684a4',
 391: '65e76c0d12b75d4801e306f9719c928dc231e9ebc4349ee139c57dacd596279c',
 392: '70be334bfdfca4fbf14a332f18501432889963925a89f27f833d521eda052419',
 393: '3003ea97049e3486c6b95aa90598c66e8da870e4476842fdd5de1d6ec5958d09',
 394: '863ef03ab51269fd4938cb32e30834a7a8051fed84cbe38667d217f249af4024',
 395: '604f5145782f8856184d39a42d24dce81ab04e165b3e7b1648bed913ae5ea593',
 396: '928e1cf3bc15776b283ef10ad6bb003e6328269a4e828201eb2c2b3b9b2158d3',
 397: 'bb106a59379c2cd85d293ae4dc3ed4058d03b4a7720cf2ad279fc277d51a14cc',
 398: '5b5d03699d9414ba820e7eb6090a0c28cdc2c0711fdecb943275cee6f31c45aa',
 399: '8160ef9d85a07f8449478ac0bdb3356e5f0890318f6bb9c637a4b7797e2a2a28',
 40: '29eba325f4db266291765582118469039b69ec54d5c494f53dd31b4dce040edc',
 400: 'c89fc613fc3f2450598be7798bf2bbae403e691c968bf474918fbd886ad2b727',
 401: 'a4788cf08414e513daf352c0c98719c59016eef23c38cb27fda1008e6c0b6b43',
 402: '9b0c37bd87b3c2ca7d04b7b66a70dedda0d706c234f955a7ee148998f22a0929',
 403: '4e2cc7dd92f3a74fd79376c39bd6a3fc6f2036481afc25dcbdc30e2b0f52d00e',
 404: '6ff986685a41f76bd85e8829a8f19b1c9f6996544dc99e5fb2bbfb1b70976bb1',
 405: '734d0dc675fe5fb8ffd396a4500ed03117e3f677a042f6f4ea47e1a12f9fb006',
 406: '866eda4b08cb99f01032abe9f1f64882da50acf226aded7df09b4c815d692e37',
 407: 'c590711ead5b04a236cbcdfd022c50a7b900d1af7b880acc428321d13ea16ac8',
 408: '1e92690308ea9a9c902193a550993c8943e5154f1330423fe4edadbbd93ab973',
 409: '04b54c7154c9c58ed731a1a1fe87811685962ecf7cdb1943b888f401a3d03af8',
 41: 'f551f4258b9010a631a32b842ddc4c69d4a47589dcf81bff84626a80e96d5354',
 410: 'ed5f6662d7f3ee0cfc540c4cfaa17ef02f381380c4d754572f909231ea46e857',
 411: '80385badf5612fd7b69525f0de7ce6648ecddba8c4be484725f44605a0158ca1',
 412: 'd32b84c370bacfeffd7a5ec7d0fe11f8e39767c2a0895d67eea6c24f134a90bf',
 413: '1d02bb565cf1687bc760e20f75cdbe236fa4b4bd07167ce90fc59bf89dff45cb',
 414: '72d260ca21c671826a7d576ed2195c010c7d57135d7ee80ffe70eb98f252d0ef',
 415: 'c657a1aaa4efdbbdbdd98e291f5ea51de69f6245a7c45e9524207f2e075e77c1',
 416: '5df3147d2c8f6857cd28e6ded382520ae865a46fe487bb752d0cb5a03fe309bf',
 417: '057ffe7b661b38aa2b7741393258d0c4c386a30bc975598bd3055b511ef272a2',
 418: 'e28a36414c65597d7e462849cda662d45375835713e9af0cf7373b138925ff02',
 419: '8b543d88858d0b5b7dd46a80997645163908b5d748c153473c9107f59e90a1c6',
 42: 'b57190944c51f2678fcb61f28b68d22a8d3876dbe77050ac6a67101a10cb25f2',
 420: '8cfcbcbd6cb8540fac2b2566020e706be29265801af1335ff3cd84bf39504800',
 421: '718c1f7c2f3be174a6abcb3b4724a5dce52c42d9eeaa3a6c17b7bebf38c6ce6e',
 43: 'cdcce1d0c384120fb755c95e8330ded774364994e4a1c2ea6be5689837eb26c7',
 44: 'b91c5e33fbd7ff3f4c5a9511b35d2ba14d7a602e159b9326a0fb4b9c9bcd31da',
 45: '0340c94ad9d415fe7076f6f572965dc29fc98afa74cc2a86246d50f031d6b12f',
 46: '1ec63977e5426c574a3966d68304524c6d7130eb2c77a701a505df92e040297c',
 47: '34ccf7a569b9d8c870d974779b39fee4e1c8b6fa028aceec90b539c8b4b8039c',
 48: '3a51407352a814e3669e315c597b0818c9b4a64cbacb9d7c25394d5054973024',
 49: '43a8183753dd630982a3eec320d56298a12dd8bf7edbc2cd8b6eba6de7546133',
 50: 'dc6957807ae1911c9969e0a0e5556fcdb5e7d0a4586fba2003f243cd3ad8d0e8',
 51: '3676c71a2d2ab9bebb7cb4d2a2444e70c8e9586297d45bc5f7131b08ae0c5186',
 52: 'f5423fd7eb5171bce013e0c2d764a4d1d58b31a42a94c7309b6d79edb0030893',
 53: '82b12ba585ccc5fde1dbbe4fb4ba42f43f69b1cb91f5843f032e83d883f421b7',
 54: '2f3dab81af0ea71394d5c7716f6f24528d0995ddbd451cb9457aa40ffe74afff',
 55: 'b41541dc177ec79459d726b12b7642c7c72435cff83888d020535b8b10061209',
 56: 'ce10bc614d8f8df5421b9b8555165e8756d4c745834bdce72b57fe31339c34a5',
 57: '66e2ad8279c96eea3ab9b379e27e9c3bdf71cb92ea07a278ae7fe1f96a0b60ba',
 58: '7b97104fd164737918f6656f9f57e45cf310e3f7dc13915bdeb5aed0aaaab113',
 59: '14075bbffa67484cb7315e8c58c59bf05054b64e0f694f57e62903da2ccb9ffd',
 60: 'a3bd3b7787a480a3b44f015204267494b673d25429775669e477bee83960e854',
 61: '900eac580249470f1f79b777fc7394ea9f9db17e4b7bff7326a8ee1f7435a7ca',
 62: '1b6a37c570d00612d780226ddf2f45f4f2c13cdb7e4ceb034fda23e69907ed0a',
 63: 'b9253a56b35273bc48b5ff2911cc456c03bcdf88cf25cfd8f79b929caf357fbc',
 64: 'b0a9869a540332c53f1eae65b9b3b62d6e90b0af063ba2dd3f118cfde7540a94',
 65: '00deb36109c76cea3bdd27eff6e4db8d8c9596df87fe7f5d93fdbb1fb2bb68f4',
 66: '0eeaaaa617d68f16f72b95aa90ac752719ada3b1b69a7b732f8541eb9e5ea20c',
 67: '73cb8e50ba80e6c59ddb753e5ce0421fc5ea7fdc0471720ff59ddc3043248cba',
 68: 'e48f2826da1efbc309e78d8a9e91e5670f7d49c1d4ac559f83bdd83cc5e1f4a5',
 69: '67825389bc3a42b1c328849a01a9e5019e355871308cad52138fab3ae59c7c3d',
 70: '544785deb6f5e26942b3e8aa9fba3888a4f0d9a2099a6610dbd6ba3be0ccb983',
 71: '72e0f9ad3750de92e662d9c2a4ee781453c434065180647a67729428d9cdac7e',
 72: '94ddae93360a5911d980a968a3c8dcb5c91341e380ecd1bd462dd16cb24cb8df',
 73: 'fc4c8f1c33a70e4f934ea04a03f505e1cc67b1d00684201c8c436d0839c83060',
 74: '0e0c1424773b1491d378a45cab70cfe5e02fefb5886f2cdee278018fe6af8bf3',
 75: '691dce49e8896f2c0ef195009b2ec47b1ec04ce36e577d2388029fbf4a2ad205',
 76: '4441688f3a4a2b4dd132c69a7e20f07ed0160325de52930261c70d9048e55cbc',
 77: '97ac1eac759b61998b21959b51f22ddb284e629b4890ec857010a4d60aa512b7',
 78: 'b05a75f02b4bb7fc54a0dc66cf8f0d18f91895c188c3b4e8d60b3169b42c18fa',
 79: '01694ced1dbf389eb310b1da41da3aa97bcc37d143f66b8a0506992767b9d4c0',
 80: '37b5b4abfc9bb346833a9ffbb1b85bbc7bce08c9fcee28d43be017f90759573f',
 81: '5918d0dc46b9351ea7e8e92b762fdc055d5647b833abbd72ed0931b4ea90bc53',
 82: 'bd73439a88662cc26db13699ef5fead3c8df3714032f93d00fc1ad1e733c5ec4',
 83: '3f216b8a2b8d90dd7bc2ea5f4452d42f5c2cafa33ad57c0131e40cc0b7be7278',
 84: '30a345d1749a374e6b23451f7258ac65cc9022b0f25ff0b0a36eb91954d2329f',
 85: '24693aa78d97dd7c331973cf4a79635a2635035c70e51352fe5a60f9cbe59547',
 86: 'fc5891253557332a3dbad58a9987413765acdf429a51063c8129e6a3e618882f',
 87: '480072e3309ca0b4dfb2b57765230d41564f05b03f1ee7d5c0b333dfd582da72',
 88: '591f01d7a1e028745af9055f561aefab49085579f51c7f78be18aff12d6b7dce',
 89: '128c8ad8c8ad248076b417cb5df9d75a952093c89bac3acd70c296f3bae293c2',
 90: '0cdf37aeda3f219150d8610097f4a89661f60575ae52667bce564ea6d248e018',
 91: '45b970957cfcd08a53677bfac2090afea19c5d5dbbc71c78291f21a206c3c71a',
 92: '7859d3259fd5a429d2e2c00db29b02bc52280ab493a6ebb58d0a60cda2184ea8',
 93: '9bd27d13fd8a761990ff75989be481b7fa72cfc7a69d7d83163a2843836f0171',
 94: '1cdc444dd7502e57c94d17744323d19c864b40c0ae4d7189ccec2c8ca3750d85',
 95: 'dfa0e5a7e2f3600ae4c3d8a5a243ed1c02f83d747001e9280498eca87edc0f45',
 96: '60a37b0e095b9c1e8b902f08446537007ad435c63608d84373215217db565bd2',
 97: 'c2e63962f9de9e0680b5f072e3882a1c4d0fcb8180fd44554d7dfb116474c7b4',
 98: 'd88c8badd856510a5ec3e7067f878da41846bf0ab06a38310b38af21964fc8f5',
 99: 'e2c3cc06ec696cc39604b6ba5089e57fd5071749089dc45c6145cbd66539f3f8'}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


# A literal printed continued-word suffix is retained but does not become a full token.
HELD_PREFIXES = {88: 'ρεῖς ', 119: 'ζαι '}
UNAVAILABLE_PAGES = [14, 33, 85, 87, 95, 96]

def _tables():
    """Combine disjoint completed source reviews, retaining their exact module pin."""
    import importlib.util
    path = Path('scripts/photius_reading_windows_middle.py')
    spec = importlib.util.spec_from_file_location('reviewed_middle_windows', ROOT / path)
    middle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(middle)
    names = ('SPECS', 'HELD_SUFFIXES', 'FIRST_FRAGMENTS', 'REGIONS', 'IMAGE_SHAS', 'HEADER_PREFIXES', 'HELD_PREFIXES')
    tables = {name: dict(globals()[name]) for name in names}
    for name in names:
        additional = getattr(middle, name, {})
        if set(tables[name]) & set(additional):
            raise ValueError('Reviewed page tables overlap: ' + name)
        tables[name].update(additional)
    return tables, [{'path': path.as_posix(), 'sha256': sha((ROOT / path).read_bytes())}]


def _header_mask(page, networks, root, headers=None):
    targets = []
    for key, prefix in (HEADER_PREFIXES if headers is None else headers).items():
        if isinstance(key, tuple) and key[0] == page:
            targets.append((key[1], prefix))
        elif key == page:
            targets.append(('Qwen/Qwen3.6-27B', prefix))
    witnesses = networks[str(page)]['ocr_consensus']['witnesses']
    masks = []
    for model, prefix in targets:
        selected = [w for w in witnesses if w.get('model') == model]
        if len(selected) != 1:
            raise ValueError('A reviewed header must identify exactly one model family')
        witness = selected[0]
        text = witness['text']
        if not text.startswith(prefix) or text.count(prefix) != 1 or sha(text.encode()) != witness['text_sha256']:
            raise ValueError(f'Reviewed page{page} raw header changed')
        raw_path = Path('data/corpus_changes/photius-bekker-coverage/witnesses') / (witness['raw_file_sha256'] + '.jsonl')
        raw = (root / raw_path).read_bytes()
        if sha(raw) != witness['raw_file_sha256']:
            raise ValueError('Reviewed header raw file changed')
        records = [line for line in raw.splitlines()[1:] if json.loads(line).get('id') == f'photius-bekker-{page:04d}']
        if len(records) != 1 or json.loads(records[0])['raw_prediction'] != text:
            raise ValueError('Reviewed header record differs from the retained witness')
        masks.append({'full_network': {'path': NETWORKS.as_posix(), 'key': str(page), 'archive_sha256': NETWORKS_SHA},
            'witness': {key: witness[key] for key in ('id', 'model', 'revision', 'artifact_sha256', 'text_sha256', 'raw_file_sha256', 'image_sha256')},
            'raw_file': {'path': raw_path.as_posix(), 'sha256': sha(raw)},
            'prediction_record_sha256': sha(records[0]), 'original_text': text,
            'exclusions': [{'start': 0, 'end': len(prefix), 'original_text': prefix,
                'classification': 'running_header', 'source_region': [.18, .015, .94, .06],
                'evidence': 'This text occurs only in the top running header above the two continuing body columns. Internal numbered codex headings and all body characters remain unchanged.'}]})
    return masks


def build(root=ROOT):
    tables, table_pins = _tables()
    source_raw, network_raw = (root / LIBRARY).read_bytes(), (root / NETWORKS).read_bytes()
    if sha(source_raw) != LIBRARY_SHA or sha(network_raw) != NETWORKS_SHA:
        raise ValueError('Pinned source or original word network changed')
    document, networks = json.loads(gzip.decompress(source_raw)), json.loads(gzip.decompress(network_raw))
    sections = {int(s['label'].removeprefix('Page s')): s for s in document['sections']}
    if len(sections) != len(document['sections']):
        raise ValueError('Source page labels are not unique')
    records = []
    for page, (end, length, evidence) in sorted(tables['SPECS'].items()):
        section = sections[page]
        if len(section['blocks']) != 1 or section.get('children') or section['blocks'][0]['type'] != 'paragraph':
            raise ValueError('Unreviewed source block structure')
        text = section['blocks'][0]['text']
        if len(text) != length:
            raise ValueError('Reviewed digital body boundary changed')
        held = []
        start = 0
        if page in tables['HELD_PREFIXES']:
            prefix = tables['HELD_PREFIXES'][page]
            if not text.startswith(prefix):
                raise ValueError('Reviewed digital initial fragment changed')
            start = len(prefix)
            held.append({'start': 0, 'end': start, 'original_text': prefix,
                'reason': 'printed-continued-word-fragment',
                'evidence': 'The source page begins with only the suffix of a word hyphenated at the preceding page boundary. Retain the literal source reading outside voting and lexical analysis without inventing its joined spelling.'})
        if end != length:
            expected = tables['HELD_SUFFIXES'][page]
            if text[end:] != expected:
                raise ValueError('Reviewed boundary completion changed')
            held.append({'start': end, 'end': length, 'original_text': text[end:],
                'reason': 'unprinted-boundary-completion',
                'evidence': 'The source page ends in a hyphenated fragment. This whole completed digital word is retained for comparison without a vote or a lexical token; no joined spelling is invented.'})
        records.append({'scan_page': page, 'printed_page': page - 12,
            'locus': f'photius_bekker1824_{page:04d}.1', 'reviewed_at': REVIEW_DATE,
            'source_section': {'id': section['id'], 'label': section['label'],
                'artifact_sha256': sha(encode(section)), 'full_text_sha256': sha(text.encode()),
                'full_original_text': text},
            'voting_segments': [{'start': start, 'end': end, 'text': text[start:end]}], 'held_spans': held,
            'first_boundary_policy': 'abstain-at-unobserved-prefix: Source Library has no reading for the printed initial continued-word suffix; preserve the fresh readings without an omission vote.' if page in tables['FIRST_FRAGMENTS'] else 'observed-body-start: The first digital word corresponds to the first large body line; the running header is absent.',
            'printed_prefix_fragment': tables['FIRST_FRAGMENTS'].get(page),
            'source_regions': tables['REGIONS'][page], 'evidence': evidence,
            'source_image': {'sha256': tables['IMAGE_SHAS'][page], 'render_recipe': f'PyMuPDF Matrix(3,3), full physical PDF page{page} of the pinned combined scan.'},
            'raw_witness_masks': _header_mask(page, networks, root, tables['HEADER_PREFIXES'])})
    absent = []
    for page in UNAVAILABLE_PAGES:
        if page in sections:
            raise ValueError('Reviewed absent source page appeared')
        absent.append({'scan_page': page, 'printed_page': page - 12,
            'locus': f'photius_bekker1824_{page:04d}.1', 'reviewed_at': REVIEW_DATE,
            'reason': 'No corresponding section exists in the pinned local002 artifact. No digital reading is fabricated or mapped from a different page.',
            'source_section': None, 'voting_segments': [], 'held_spans': [],
            'source_image': {'sha256': tables['IMAGE_SHAS'][page], 'render_recipe': f'PyMuPDF Matrix(3,3), full physical PDF page{page} of the pinned combined scan.'},
            'evidence': 'Full source page inspected. Both checkpoints omit the footer; the Qwen3.6 top running header is separately masked, retaining the internal codex2 and codex3 headings.' if page == 14 else ('Full source page inspected. Neither retained fresh witness includes the running header or small footer; the internal codex63 Procopius heading is body and remains unchanged.' if page == 33 else 'Full source page inspected. This corresponding physical page is absent from the pinned digital artifact; no neighboring section is substituted and no digital omission vote is supplied.'),
            'first_boundary_policy': 'No Source Library vote: the pinned artifact contains no corresponding section. Preserve all fresh body readings and existing abstentions.',
            'raw_witness_masks': _header_mask(page, networks, root)})
    records.append(absent[0])  # Page14 changes only its exact running-header vote.
    credit = json.loads((root / 'data/corpus_changes/photius-bekker-coverage/coverage.json').read_text())['source_library']
    return {'schema_version': 1, 'kind': 'source-reviewed-photius-reading-windows',
        'work': 'photius.bibliotheca', 'reviewed_at': REVIEW_DATE,
        'source_scan': SCAN,
        'source_library': {'path': LIBRARY.as_posix(), 'sha256': LIBRARY_SHA, 'edition': document['id'],
            'url': credit['url'], 'license': credit['license'], 'rights': credit['rights'],
            'source_citation': document['sourceCitation'], 'attribution': document['origin']['label'],
            'separate_api_notice': credit['separate_api_notice']},
        'records': records, 'unavailable_source_library': absent, 'review_tables': table_pins,
        'policy': 'Admit each reviewed digital body window as exactly one additional Source Library vote. Preserve every original reading, current mask and raw archive. Apply the exact source-confirmed running-header masks in addition to existing masks, never instead of them. Hold disagreements as alternatives; do not select a source by similarity or a majority of repeated runs. Source review establishes body extent and roles, not a proofread transcription. Region coordinates are conservative viewing contexts, not word-level segmentation. Page13 prefatory title and text are outside this authority and remain unchanged.',
        'generated_by': 'scripts/prepare_photius_reading_windows.py'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    authority = build(args.root)
    raw = encode(authority); path = args.root / OUT
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    elif args.check and path.read_bytes() != raw:
        parser.exit(1, 'Reviewed Photius reading windows drift\n')
    print(json.dumps({'path': OUT.as_posix(), 'sha256': sha(raw), 'body_windows': sum(r['source_section'] is not None for r in authority['records']), 'unavailable_pages': len(authority['unavailable_source_library'])}))


if __name__ == '__main__':
    main()
