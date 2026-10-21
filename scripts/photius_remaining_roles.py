"""Individually reviewed roles of the 39 held nonbody Photius occurrences.

This append-only assessment does not rewrite any earlier source observation or
admit corpus text. The caller may adopt a Henry reading only through its own
exact source validation and reversible continuation layer. Font size is never
used to infer authorship. Transmitted explanatory notes are distinguished from
Photius's reading announcements and modern edition reference numbers.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-21T22:50:40.726396+00:00'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {'data/corpus_changes/photius-bekker-complete-review/review-status.json.gz': '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
 'data/corpus_changes/photius-bekker-editorial-substitutions/compiled-review.json.gz': '76abb40a4759da8659bf8646fc80a9310c1c519adc6fb4a7ef3fe5b767fed633',
 'data/corpus_changes/photius-bekker-editorial-substitutions/source-review.json': 'b8c04a8f67dbc0262a7ccf995959b6ef4ed4fbe4fc77e9416c352db0f1998b51',
 'data/corpus_changes/photius-bekker-readings/source-scan.pdf': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}
SPECS = [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0053.7',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθην ἐκ τῶν ΠΡΟΚΛΟΥ χρησιμωτάτης γραμματικῆς ἐκλογῶν.',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 53,
           'region': [0.55, 0.095, 0.95, 0.77],
           'image_sha256': 'b180f3ef050c2d5f8a8de045c4f6f0b8480c0a9d8084dfc465de25c054c1cbcf'},
  'selection': (8181,
                8184,
                'Ἀνεγνώσθη ἐκ τοῦ ἐπιγραφομένου βιβλίου Πρόκλου χρηστομαθείας γραμματικῆς ἐκλογαί'),
  'evidence': 'Codex239 begins after the Josephus summary. The reading announcement identifies Proclus and '
              'continues directly into the description of the book; Henry retains the announcement within '
              'codex239,318b, with an edition variant in its wording.',
  'context_sha256': 'ac6770acf0f480b055d0c1352f5c18c55ae4f0a2798092fe3c7dfea641959f57',
  'prior_observed_text': 'Ἀνεγνώσθησαν ἐκ τῆς ΠΡΟΚΛΟΥ χρηστομαθίας γραμματικῆς ἐκλογαί.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0057.44',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 57,
           'region': [0.55, 0.095, 0.95, 0.19],
           'image_sha256': '4d44b03853a54af480f762a7384f6c2c8bb185eab75083a81449d3e7f206738a'},
  'selection': (8281, 8284, 'Ἀνεγνώσθη'),
  'evidence': 'Codex240 announces extracts from John Philoponus on the Hexaemeron and continues into the '
              'book description. Henry retains the same announcement in 322b.',
  'context_sha256': '6951282ba70437609f6e68faa283c15694aa0b2d3472f67036126475cb53ab3a',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0058.9',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 58,
           'region': [0.405, 0.55, 0.835, 0.64],
           'image_sha256': '0729a4b26eb680d2958b16179c92f8ea790a2eb726c37d058eb59076f41e3869'},
  'selection': (8313, 8316, 'Ἀνεγνώσθη'),
  'evidence': 'Codex241 announces the Philostratus account of Apollonius before its narrative summary. Henry '
              'retains the announcement in 323b.',
  'context_sha256': 'eddc125558fd2dcc577a1d04eef78fb6ccce45855e72349e29e3585d6e54e503',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0088.2',
  'segment_index': 2,
  'original_text': 'Ἐκ τοῦ ὑπὲρ Δημοσθένους Τριπέρδου.',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 88,
           'region': [0.045, 0.095, 0.445, 0.77],
           'image_sha256': 'dfe4b95e21be9a216c5b9b39970efb5c5023220ec91440f60bebed33fec73951'},
  'selection': (8900, 8902, 'Ἐκ τοῦ ὑπὲρ Δημοσθένους Ὑπερίδου'),
  'evidence': 'The title identifies Himerius’s speech for Demosthenes and Hyperides, between the codex243 '
              'introduction and its theoretical extract. Henry retains it as the extract title in353a.',
  'context_sha256': 'c97446fa59447880f6c73cd5120231ec524259747bb1c3a30e405f50aab90044',
  'prior_observed_text': 'Ἐκ τοῦ ὑπὲρ Δημο[σ?]θένους Ὑπερίδου.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0095.1',
  'segment_index': 9,
  'original_text': 'Ἐν τῆς ἐκγραφῆς μελέτης, μετὰ τὰ Μη-δικὰ ἑψηρίσματα Ἀθηναίου, πρὸς τοὺς βαρβάρους '
                   'σάλειρον. καὶ ὁ βασιλεὺς ὑπέσχεν τὰ λευκασμὴν ἐπανορθώσεσθαι, εἰ τὸν πό-λεμον '
                   'καταλύσειαν. βουληθέντων αὐτῶν Θημισοκλῆς ἐντελλεῖται." αὐτὸ τὸ προοίμιον.',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 95,
           'region': [0.21, 0.095, 0.61, 0.77],
           'image_sha256': '7b8e56ddb007c7d21b5972820df76d64ce386018705957e3cdd8a4f333c48d6e'},
  'selection': (9059, 9063, None),
  'evidence': 'The title supplies the situation for Himerius’s declamation and labels its introduction. '
              'Henry retains the same title and introductory label in360a, distinct from the declamation '
              'that follows.',
  'context_sha256': '4c9557a5d1a39ce63458d728423b4e541d4c222a366523284f19ff175627445b',
  'prior_observed_text': 'Ἐκ τῆς ἐπιγραφομένης μελέτης „μετὰ τὰ Μηδικά ἐψηφίσαντο Ἀθηναῖοι πρὸς τοὺς '
                         'βαρβάρους πόλεμον. πυθόμενος ὁ βασιλεὺς ὑπέσχετο τὰ λελυμασμένα ἐπανορθώσασθαι, εἰ '
                         'τὸν πόλεμον καταλύσειαν. βουλομένων αὐτῶν Θεμιστοκλῆς ἀντιλέγει.“ αὐτὸ τὸ '
                         'προοίμιον.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0155.1',
  'segment_index': 0,
  'original_text': '685 Ἡ',
  'original_role': 'marginal-reference',
  'role': 'marginal-reference',
  'subtype': 'edition-reference',
  'confidence': 'high',
  'scan': {'physical_page': 155,
           'region': [0.16, 0.108, 0.6, 0.155],
           'image_sha256': 'e56d8d2e57462205e7dfe0d2db890687b1997072c88b0844998f13e01ac7b700'},
  'selection': None,
  'evidence': 'An isolated number with an H suffix sits outside the syntactic column at the continuation '
              'into διαφοράν. It is an edition reference, not Greek narrative; prior recorded683H and '
              'current visual685H remain contrary numeric readings.',
  'context_sha256': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',
  'prior_observed_text': '683H.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0157.3',
  'segment_index': 1,
  'original_text': 'συλλογισάμενος',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 157,
           'region': [0.56, 0.305, 0.97, 0.4],
           'image_sha256': 'fcbfa03a4b562fca08c8ec98c98385e7d0e03a4e78dbaceb7aa25a633a4e3dee'},
  'selection': (10992, 10994, 'συλλογίσασθαι'),
  'evidence': 'The inset paragraph comments on Aristides’s word for recapitulation and lists Greek synonyms. '
              'Henry includes the same explanatory paragraph at 422b, using F_1 text spans within codex247, '
              'not a modern apparatus or page-label cell.',
  'context_sha256': '1df832dcc371b143925e1db3cbd5a24992bec2d923705617f0bcad5976893d82',
  'prior_observed_text': 'συλλογίσασθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0157.3',
  'segment_index': 3,
  'original_text': 'ἀναφορῶσασθαι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 157,
           'region': [0.56, 0.305, 0.97, 0.4],
           'image_sha256': 'fcbfa03a4b562fca08c8ec98c98385e7d0e03a4e78dbaceb7aa25a633a4e3dee'},
  'selection': (10992, 10994, 'ἀπαριθμήσασθαι'),
  'evidence': 'The same recapitulation comment ends with synonyms including enumeration and recapitulation. '
              'Henry retains the paragraph at 422b; this is transmitted commentary rather than modern '
              'reference numbering.',
  'context_sha256': '1df832dcc371b143925e1db3cbd5a24992bec2d923705617f0bcad5976893d82',
  'prior_observed_text': 'ἀπαριθμήσασθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.5',
  'segment_index': 12,
  'original_text': '682H.',
  'original_role': 'marginal-reference',
  'role': 'marginal-reference',
  'subtype': 'edition-reference',
  'confidence': 'high',
  'scan': {'physical_page': 158,
           'region': [0.025, 0.485, 0.44, 0.73],
           'image_sha256': '00794cd2da0cc3e24cc36c8d69b1d5495375fee78240244e4ba715ce4f16a058'},
  'selection': None,
  'evidence': 'An H-suffixed isolated reference stands in the left margin beside the sentence about '
              'Pericles. It interrupts neither syntax nor the corresponding Henry Greek sentence; prior688H '
              'and the displayed682H remain unselected numeric readings.',
  'context_sha256': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',
  'prior_observed_text': '688H.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0159.1',
  'segment_index': 2,
  'original_text': 'ἀπένους, σῦμα.',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 159,
           'region': [0.2, 0.105, 0.6, 0.34],
           'image_sha256': '6a2e3822a4ed7495ad3f5e8966f32fdd372e41d6ba46917b4239731c1508528f'},
  'selection': (11050, 11051, 'πέπαυσο σίγα'),
  'evidence': 'The small-type synonym gloss follows κατάβαλε in the Aristides quotation and precedes the '
              'next quotation. Henry retains a corresponding gloss at 424a, with πέπαυσο in place of the '
              'tentative Bekker ἄκουσον.',
  'context_sha256': 'd88de3ee0b7b812bb1fb9d08074d9aad335bc3815be6ef898db516bf92d777ae',
  'prior_observed_text': 'ἄκουσον, σίγα.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0159.2',
  'segment_index': 24,
  'original_text': 'ἰπτεροδύλασσοι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 159,
           'region': [0.56, 0.605, 0.97, 0.695],
           'image_sha256': '8087803aeb6e37856b5fea0f5d089161ca92b6f390657e48a6c2ab9399e94ef9'},
  'selection': (11093, 11094, 'ἐμπειροθάλασσοι'),
  'evidence': 'A proverb explanation follows the quotation about Cretans and the sea and precedes the next '
              'Aristides passage. Henry retains this explanatory paragraph at 424b, with ἐμπειροθάλασσοι.',
  'context_sha256': '600c0278534dd0bfc3e0a19f777aca37789197d8e232d81bdd2a0b1542351e0f',
  'prior_observed_text': 'ἠπειροθάλασσοι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0159.2',
  'segment_index': 26,
  'original_text': 'ὁ σπουδὴς ἄργον',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 159,
           'region': [0.56, 0.605, 0.97, 0.695],
           'image_sha256': '8087803aeb6e37856b5fea0f5d089161ca92b6f390657e48a6c2ab9399e94ef9'},
  'selection': (11093, 11094, 'ὁ νησιώτης ἀγνοεῖν'),
  'evidence': 'The proverb explanation gives parallel sayings about an islander and a Sicilian. Henry '
              'retains it in 424b with ὁ νησιώτης ἀγνοεῖν; the earlier tentative source spelling is not used '
              'to choose the location.',
  'context_sha256': '600c0278534dd0bfc3e0a19f777aca37789197d8e232d81bdd2a0b1542351e0f',
  'prior_observed_text': 'ὁ σπουδῆς ἀργεῖν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0160.5',
  'segment_index': 1,
  'original_text': 'ἐκστρατευσθεὶς',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 160,
           'region': [0.39, 0.3, 0.81, 0.54],
           'image_sha256': '8e26fb70c8bcacad73528036102d7a0eddb12334f71ec53ad6d5cae550f5c47e'},
  'selection': (11126, 11130, 'Ἐξοστρακισθεὶς'),
  'evidence': 'A small-type biographical note headed Ἐκ τῶν περὶ Κίμωνος interrupts the Aristides extracts '
              'and is bounded by them. Henry retains both the heading and the biography at 425b, including '
              'the ostracism verb.',
  'context_sha256': 'a6581fb6002ceb4caa7c8566baaffedf56e0d155b46cca90c583682d58a405cd',
  'prior_observed_text': 'ἐξοστρακισθεὶς'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0161.3',
  'segment_index': 1,
  'original_text': 'διωὡς ἑκαδὴ',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 161,
           'region': [0.2, 0.3, 0.6, 0.54],
           'image_sha256': '4057094cf888e3b5cd8ad9916546897cea6bd36d2a3d7cb8564002e8717d3dc5'},
  'selection': (11143, 11144, 'δεινῶς ἐπειδὴ'),
  'evidence': 'The small-type comment explains the singular τοῦ πράγματος in the immediately preceding '
              'argument about rule and slavery. Henry retains that same note between the same two quotations '
              'in 426a.',
  'context_sha256': '1ffe2a837051cee01e6a5df3941bd3575d54153ba65905923abec89165b98e78',
  'prior_observed_text': 'δεινῶς ἑκαδὴ'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0161.3',
  'segment_index': 3,
  'original_text': 'κατεσυλλογίσασθαι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 161,
           'region': [0.2, 0.3, 0.6, 0.54],
           'image_sha256': '4057094cf888e3b5cd8ad9916546897cea6bd36d2a3d7cb8564002e8717d3dc5'},
  'selection': (11143, 11144, 'κατεσυλλογίσατο'),
  'evidence': 'The comment’s last verb describes the preceding deduction. Henry retains κατεσυλλογίσατο in '
              'the same note at 426a; this remains a different edition reading, not proof of Bekker’s '
              'ligature.',
  'context_sha256': '1ffe2a837051cee01e6a5df3941bd3575d54153ba65905923abec89165b98e78',
  'prior_observed_text': 'κατασυλλογίσασθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0161.5',
  'segment_index': 0,
  'original_text': 'Ἀποσοθεῖναι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 161,
           'region': [0.2, 0.3, 0.6, 0.54],
           'image_sha256': '4057094cf888e3b5cd8ad9916546897cea6bd36d2a3d7cb8564002e8717d3dc5'},
  'selection': (11145, 11147, 'Δημοσθενικὸν'),
  'evidence': 'The inset note comments on the rhetorical construction in the immediately preceding Cimon '
              'quotation. Henry retains it at 426a with Δημοσθενικὸν τὸ σχῆμα.',
  'context_sha256': '76428fbb8d6d4f402150ed058195eeddc5ed80bdfdec3ffdf0916171e8b08ad2',
  'prior_observed_text': 'Ἀποσθενικῶς'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0161.5',
  'segment_index': 2,
  'original_text': 'Ἦρη γὰρ ἠτιδύσασ τῷ διὰ τοὺς ἀποσολούς',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 161,
           'region': [0.2, 0.3, 0.6, 0.54],
           'image_sha256': '4057094cf888e3b5cd8ad9916546897cea6bd36d2a3d7cb8564002e8717d3dc5'},
  'selection': (11145, 11147, 'ἔφη γὰρ τεθνᾶσι τῷ δέει τοὺς ἀποστόλους'),
  'evidence': 'The same rhetorical note quotes a parallel expression and explains the construction τῷ φόβῳ '
              'τοὺς Ἕλληνας. Henry retains the note and its embedded quotation at 426a.',
  'context_sha256': '76428fbb8d6d4f402150ed058195eeddc5ed80bdfdec3ffdf0916171e8b08ad2',
  'prior_observed_text': 'ἔφη γὰρ ἐπεδύσατο διὰ τοὺς ἀποστόλους'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0161.5',
  'segment_index': 4,
  'original_text': 'γενέσθαι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 161,
           'region': [0.2, 0.3, 0.6, 0.54],
           'image_sha256': '4057094cf888e3b5cd8ad9916546897cea6bd36d2a3d7cb8564002e8717d3dc5'},
  'selection': (11145, 11147, 'γενέσθαι'),
  'evidence': 'The final infinitive completes that rhetorical explanation before the next Aristides '
              'quotation. Henry retains γενέσθαι in the note at 426a.',
  'context_sha256': '76428fbb8d6d4f402150ed058195eeddc5ed80bdfdec3ffdf0916171e8b08ad2',
  'prior_observed_text': 'γενέσθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0163.5',
  'segment_index': 1,
  'original_text': 'βεβουλεῦθαι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 163,
           'region': [0.56, 0.485, 0.97, 0.73],
           'image_sha256': '1b25928e11ab2c92b4ccb89d080720a9e720e07db2bae09257ee4faad49bccae'},
  'selection': (11254, 11258, 'βεβουλεῦσθαι'),
  'evidence': 'An inset interpretive paragraph offers alternative paraphrases of the immediately preceding '
              'rhetorical argument. Henry retains the paragraph at 428b, including βεβουλεῦσθαι.',
  'context_sha256': 'dfce6113b257873fccc04ee619ebc178bcc68ace5d7d2401fccb3b62dc8e06d2',
  'prior_observed_text': 'βεβουλεῦσθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.5',
  'segment_index': 1,
  'original_text': 'οἴδαμεν μὴ παραλαμβάνειν',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.105, 0.81, 0.34],
           'image_sha256': '3ea40907cafa13a43c592385b19d648b08a2359ec607d68817b5105be12d1e89'},
  'selection': (11275, 11276, 'οὐδαμῶς μὲν παραλαμβάνεται'),
  'evidence': 'The inset lexical comment explains Aristides’s use of ἦ που. Henry retains the explanatory '
              'paragraph at 429b, immediately after the same lemma and before the next quoted sentence.',
  'context_sha256': 'f91712f926389af82e873e70ef030ca30aa552b6ed831245f8fa121b98f88772',
  'prior_observed_text': 'οὐδεμῶς μὴ παραλαμβάνεται'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.5',
  'segment_index': 3,
  'original_text': 'αὐτὸ',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.105, 0.81, 0.34],
           'image_sha256': '3ea40907cafa13a43c592385b19d648b08a2359ec607d68817b5105be12d1e89'},
  'selection': (11275, 11276, 'ἀεί'),
  'evidence': 'The same lexical comment ends by saying the author uses the expression almost always. Henry’s '
              'ἀεί is anchored after μᾶλλον δὲ σχεδόν and before the following quotation, not selected from '
              'the uncertain OCR spelling.',
  'context_sha256': 'f91712f926389af82e873e70ef030ca30aa552b6ed831245f8fa121b98f88772',
  'prior_observed_text': 'εἰ / αὐτό'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.6',
  'segment_index': 1,
  'original_text': 'διαλύεσθαι',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.265, 0.81, 0.54],
           'image_sha256': 'fd33af41294e377f86da04bd08a434b8959487c18d6e589816ce912b564512bf'},
  'selection': (11282, 11283, 'διαλέγεσθαι'),
  'evidence': 'The proverb explanation identifies Priam and Helen observing the Greeks from the wall. Henry '
              'retains it at 429b, with the terminal διαλέγεσθαι.',
  'context_sha256': 'eee80b04d6ec3cba77d8f2d7afa88208822371e69deab7170106af526d388eee',
  'prior_observed_text': 'διαλεγομένων / διαλέγεσθαι'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'segment_index': 0,
  'original_text': 'λαλεῖν',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556'},
  'selection': (11285, 11286, 'Λείπει'),
  'evidence': 'The inset grammatical note begins by supplying an omitted δεῖ νομίζειν. Henry retains Λείπει '
              'at 429b; the earlier tentative scan λέγειν is a contrary reading rather than an authority for '
              'the selection.',
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'prior_observed_text': 'λέγειν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'segment_index': 2,
  'original_text': 'προαύσει τὴν παρακεφαλαιον',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556'},
  'selection': (11285, 11286, 'Κρανίαν τὴν περικεφαλαίαν'),
  'evidence': 'The grammatical note explains κρανίαν as περικεφαλαίαν and then the other military and '
              'nautical words. Henry retains that explanatory note at 429b with Κρανίαν τὴν περικεφαλαίαν.',
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'prior_observed_text': 'προσεῖπε τὴν περικεφαλαίαν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0171.3',
  'segment_index': 1,
  'original_text': 'τοῦτον',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 171,
           'region': [0.2, 0.3, 0.65, 0.55],
           'image_sha256': 'd2e3aa587732d1e0402d3932c32d814a8c83d04c43782b1d69e470578652d0a7'},
  'selection': (11557, 11559, 'ἴσχυεν'),
  'evidence': 'An inset explanation comments on Philip’s success through traitors and the usefulness of the '
              'episode. Henry retains the same note between the same quotations at 436a.',
  'context_sha256': '5a2c7a89aa6a804b37e41047a723d2ca373592d72aed18f75d1be6f284592e4a',
  'prior_observed_text': 'ἴσχυεν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.2',
  'segment_index': 1,
  'original_text': 'ἀπορρημένως',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 172,
           'region': [0.025, 0.205, 0.49, 0.325],
           'image_sha256': 'e9a0d718bae105547f2bab33715ca745472bcdaa4c501c6f41f7ca77b4a2920f'},
  'selection': (11590, 11592, 'ἀποβεβιωκότας'),
  'evidence': 'A small-type note comments on the writer’s creation of names and portrayal of deceased people '
              'as living interlocutors. Henry retains it at 437a between the same prose passages.',
  'context_sha256': '696c4930d0485e59e84b2c640f654eb5f71388ee038878ba77febf01a9ca1551',
  'prior_observed_text': 'ἀποβεβιωκότας'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.2',
  'segment_index': 3,
  'original_text': 'τοὺς ἐπιστάτους',
  'original_role': 'unclassified-small-type',
  'role': 'transmitted-historical-commentary',
  'subtype': 'transmitted-explanatory-note',
  'confidence': 'high',
  'scan': {'physical_page': 172,
           'region': [0.025, 0.205, 0.49, 0.325],
           'image_sha256': 'e9a0d718bae105547f2bab33715ca745472bcdaa4c501c6f41f7ca77b4a2920f'},
  'selection': (11590, 11592, 'τοῖς ἐπαΐσουσι'),
  'evidence': 'The same note identifies the hearers of those represented interlocutors. Henry retains τοῖς '
              'ἐπαΐσουσι at 437a; the earlier tentative τοὺς ἐκείνους remains a separate source reading.',
  'context_sha256': '696c4930d0485e59e84b2c640f654eb5f71388ee038878ba77febf01a9ca1551',
  'prior_observed_text': 'τοὺς ἐκείνους / τοὺς ἐκείνου'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0173.3',
  'segment_index': 0,
  'original_text': 'Ἀντενόδη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 173,
           'region': [0.56, 0.105, 0.99, 0.4],
           'image_sha256': '9df3b48519dbc5f7da1ca5d8196abf5d802782591e47fe878bb79e294999a15a'},
  'selection': (11654, 11655, 'Ἀνεγνώσθη'),
  'evidence': 'Codex249 begins after the close of Aristides and announces a Life of Pythagoras. Henry '
              'retains the announcement in 438b as part of the work’s sequence.',
  'context_sha256': 'f037c217a82ee0db4652ed301915fd9a5a6bfa45dfa15e83160c03aa30b7bdc1',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0176.3',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθησαν',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 176,
           'region': [0.39, 0.105, 0.86, 0.39],
           'image_sha256': 'f1b291236a1c6dc85fbb995a41f0a274cf990d616ba191b064f32103237ef536'},
  'selection': (11729, 11733, 'Ἀνεγνώσθη'),
  'evidence': 'Codex250 announces two books of Agatharchides before the summary of their contents. Henry '
              'retains the announcement in 441b but uses the singular Ἀνεγνώσθη; the scanned plural remains '
              'an edition variant.',
  'context_sha256': '1cd49bd6752dd9aa22149366f3b4c4de36ad0cd2afd03f75898ac92ddd7e57a5',
  'prior_observed_text': 'Ἀνεγνώσθησαν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.1',
  'segment_index': 4,
  'original_text': '134',
  'original_role': 'marginal-reference',
  'role': 'marginal-reference',
  'subtype': 'edition-reference',
  'confidence': 'high',
  'scan': {'physical_page': 184,
           'region': [0.025, 0.105, 0.49, 0.34],
           'image_sha256': '982e4bcc5b5ed0577ef56e244eda6934e65103ea7320e4e7594fd49c8dbc2e35'},
  'selection': None,
  'evidence': 'The source shows a marginal R-suffixed edition number beside the broken Μή-/δων body word. '
              'The retained134 is the captured prefix of that reference, not the completion of the Greek '
              'body word.',
  'context_sha256': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',
  'prior_observed_text': ''},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0195.52',
  'segment_index': 1,
  'original_text': 'Ἀνεγνωσθη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 195,
           'region': [0.56, 0.3, 0.99, 0.43],
           'image_sha256': 'cd2679b9f1db36babe852982f7ea37d258f90387a2b91b3ddc62e08315031638'},
  'selection': (12187, 12190, 'Ἀνεγνώσθη'),
  'evidence': 'Codex251 announces Hierocles’s work on providence between extracts. Henry retains the '
              'announcement in 460b; compact σθ/θ uncertainty does not change its role.',
  'context_sha256': '68e06f6f3e5b1e09ea58cb6194742796750ea8fa368255a34d74dc33a0bc052d',
  'prior_observed_text': 'Ἀνεγνώσθη / Ἀνεγνώθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0201.3',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθαι',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 201,
           'region': [0.56, 0.44, 0.99, 0.61],
           'image_sha256': 'f6ea0048f0e2641b88b9dcdb797fdf8f56f9f8eb7cb8c6a686078a276a735708'},
  'selection': (12326, 12327, 'Ἀνεγνώσθη'),
  'evidence': 'Codex252 announces extracts from Gregory’s life and introduces the four dialogues. Henry '
              'retains this announcement in 466b with singular Ἀνεγνώσθη; the scanned plural remains '
              'distinct.',
  'context_sha256': '16d051501b5a1402bc1595b3d777527fa0e911d48c9cbf97dd5c777b11f8ae66',
  'prior_observed_text': 'Ἀνεγνώσθησαν'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0202.17',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθι',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 202,
           'region': [0.39, 0.32, 0.86, 0.42],
           'image_sha256': '0a3c368822d7c7fe74631cf46f545d4ef89acdbd68d82b0b6613d1a9a8059ff9'},
  'selection': (12346, 12347, 'Ἀνεγνώσθη'),
  'evidence': 'Codex253 announces the martyrdom of the seven youths before the narrative. Henry retains the '
              'announcement in 467b.',
  'context_sha256': 'de71ee4865e8a0b891db433d2ae49d7969fb3455456189b970da6797ea167442',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0203.4',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθῃ',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 203,
           'region': [0.56, 0.105, 0.99, 0.22],
           'image_sha256': '04b3d9f1f171761802c326a5b258c19c6fb39c7c6cf9a1fba417887187ed53cc'},
  'selection': (12367, 12368, 'Ἀνεγνώσθη'),
  'evidence': 'Codex254 announces the martyrdom narrative of Timothy before its summary. Henry retains the '
              'announcement in 468b.',
  'context_sha256': 'b31a8924c6755693f24335aee6000175a38c0a0d59dbeb2b5f19de2b03b79183',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0204.2',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 204,
           'region': [0.025, 0.16, 0.49, 0.26],
           'image_sha256': '60770c5b4c7ffb12c68e93089c4d4dba18f888328fd3ef9e7b012d23e00a30df'},
  'selection': (12378, 12380, 'Ἀνεγνώσθη'),
  'evidence': 'Codex255 announces the martyrdom of Demetrius and relates its mode of publication to the '
              'preceding text. Henry retains it in 469a as the beginning of the codex.',
  'context_sha256': '963ee4d074ee25d9d43c701f09832295e5df3e2f39147c3d367ac7940c1be0ff',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0204.4',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 204,
           'region': [0.39, 0.26, 0.86, 0.39],
           'image_sha256': '66d14f09fa866daaefc433a03d070216085cf381bbbbf3ed38cde6e44770f4b5'},
  'selection': (12394, 12396, 'Ἀνεγνώσθη'),
  'evidence': 'Codex256 announces the work on Metrophanes and Alexander and then summarizes Constantine’s '
              'life. Henry retains this announcement in 469b.',
  'context_sha256': '998b57fa9540078241cefe554caee65eda48debb29bd0133d951205f56294f6b',
  'prior_observed_text': 'Ἀνεγνώσθη'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0204.4',
  'segment_index': 2,
  'original_text': 'ἐπεγράφη',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 204,
           'region': [0.39, 0.26, 0.86, 0.39],
           'image_sha256': '66d14f09fa866daaefc433a03d070216085cf381bbbbf3ed38cde6e44770f4b5'},
  'selection': (12394, 12396, 'ἐπιγέγραπται'),
  'evidence': 'The same announcement names the work through its title clause. Henry retains ἐπιγέγραπται '
              'before Πολιτεία in 469b; the earlier OCR ἐπεγράφη is not a modern reference label.',
  'context_sha256': '998b57fa9540078241cefe554caee65eda48debb29bd0133d951205f56294f6b',
  'prior_observed_text': 'ἐπιγέγραπται'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0220.6',
  'segment_index': 0,
  'original_text': '# Ἀντιφῶντος λόγοι διάφοροι.1452B.',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 220,
           'region': [0.405, 0.095, 0.835, 0.77],
           'image_sha256': '0020498720816e869c7cb762afc3554d8f00d692bc69d8196584bb2c747c26f2'},
  'selection': (12767, 12770, None),
  'evidence': 'Codex259 begins with the Antiphon reading announcement after the preceding work summary. '
              'Henry retains the announcement in 485b, with singular Ἀνεγνώσθη. The leading# and '
              'trailing1452B in the OCR preimage are not part of the source Greek announcement.',
  'context_sha256': 'a68dd3ce829c2c954d51c0f8e45a84d6885958f47be3f22c2e4dea7399b1203c',
  'prior_observed_text': 'Ἀνεγνώ[σ?]θησαν ΑΝΤΙΦΩΝΤΟΣ λόγοι διάφοροι.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0221.7',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθωσ ἹΣΟΚΡΑΤΟΥΣ λόγοι διάφοροι.',
  'original_role': 'unclassified-heading',
  'role': 'authorial-body',
  'subtype': 'reading-announcement-or-extract-title',
  'confidence': 'high',
  'scan': {'physical_page': 221,
           'region': [0.55, 0.095, 0.95, 0.77],
           'image_sha256': 'ba3de1cd53d7806c245df7384d62bfa6fcaf3455a44b9e067412f75e2e6a74a3'},
  'selection': (12790, 12793, None),
  'evidence': 'Codex260 begins with the Isocrates reading announcement after the preceding work summary. '
              'Henry retains the announcement in 486b, including plural Ἀνεγνώσθησαν.',
  'context_sha256': '458307515965f9b86b0867a84eccc5bfe1861562d5f352b764c1036c289e2ace',
  'prior_observed_text': 'Ἀνεγνώ[σ?]θησαν ΙΣΟΚΡΑΤΟΥΣ λόγοι διάφοροι.'}]
# Exact non-Greek envelopes of the reviewed Antiphon announcement. These are
# retirement facts, not general permission to drop punctuation or reference text.
RETIRED_WRAPPERS = {
 ('helladius_chrestomathia_photius_bekker_v2_0220.6',0):
    {'prefix':'# ','suffix':'.1452B.'}}

# The first removes only the visually identified extraneous edition wrappers.
# The second separates the source note from the following quotation without
# changing the retained verified spelling or case of its first word.
RENDERING = {
 ('helladius_chrestomathia_photius_bekker_v2_0220.6',0):
    {'retire_prefix':'# ','retire_suffix':'1452B.'},
 ('helladius_chrestomathia_photius_bekker_v2_0164.5',3):
    {'separate_verified_suffix':'καὶ','boundary_after':' '}}

NEXT_SOURCE_TOKEN = {'text': 'Καὶ',
 'refs': [{'html_line': 26308,
           'html_column': 120,
           'unit_index': 11276,
           'codex': '248',
           'bekker': '429b',
           'start': 0,
           'end': 3}]}
CORRECTIONS = [{'id': 'photius-physical0164-verified-clause-20261021',
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'start': 7,
  'end': 24,
  'original_row_sha256': '975a115dbfa71b825d6e062d0508b72e0f056876a85c6ed414570708ae4bb72d',
  'original_text': 'τὸ δὲ νομίζεσθαι.',
  'corrected_text': 'τὸ δεῖ νομίζειν.',
  'prior_verification': 'verified',
  'selection': (11285, 11286, 'τὸ δεῖ νομίζειν'),
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556',
           'observed_text': 'τὸ δεῖ νομίζειν.'},
  'evidence': 'Complete close reading of the inset grammatical note on Bekker physical 164, printed 429b. The '
              'grammatical note explicitly supplies δεῖ νομίζειν, not δὲ νομίζεσθαι. The supplied Henry base '
              'text at decoded Greek unit 11285 independently agrees. This is a new correction to previously '
              'verified text; all earlier facts and contrary readings remain frozen.',
  'qualification': 'A fresh scan-supported correction to a previously verified display clause, counted '
                   'separately from the 385 held uncertainty identities. No earlier scan observation, '
                   'archive, role decision, or uncertainty measurement is rewritten.',
  'prior_verification_evidence': {'path': 'data/corpus_changes/photius-bekker-complete-review/review-status.json.gz',
                                  'sha256': '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
                                  'segment_index': 1,
                                  'verification': 'verified',
                                  'start': 6,
                                  'end': 25,
                                  'text': ' τὸ δὲ νομίζεσθαι. '}},
 {'id': 'photius-physical0164-verified-shield-20261021',
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'start': 69,
  'end': 77,
  'original_row_sha256': '975a115dbfa71b825d6e062d0508b72e0f056876a85c6ed414570708ae4bb72d',
  'original_text': 'τὸ δέρμα',
  'corrected_text': 'τὸ ὅπλον',
  'prior_verification': 'verified',
  'selection': (11285, 11286, 'τὸ ὅπλον'),
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556',
           'observed_text': 'τὸ ὅπλον'},
  'evidence': 'Complete close reading of the inset grammatical note on Bekker physical 164, printed 429b. The '
              'note explains βύρσαν as τὸ ὅπλον, not τὸ δέρμα; the next phrase explains its leather '
              'covering. The supplied Henry base text at decoded Greek unit 11285 independently agrees. This '
              'is a new correction to previously verified text; all earlier facts and contrary readings '
              'remain frozen.',
  'qualification': 'A fresh scan-supported correction to a previously verified display clause, counted '
                   'separately from the 385 held uncertainty identities. No earlier scan observation, '
                   'archive, role decision, or uncertainty measurement is rewritten.',
  'prior_verification_evidence': {'path': 'data/corpus_changes/photius-bekker-complete-review/review-status.json.gz',
                                  'sha256': '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
                                  'segment_index': 3,
                                  'verification': 'verified',
                                  'start': 51,
                                  'end': 172,
                                  'text': ' λέγει, βύρσαν δὲ τὸ δέρμα παρὰ τὸ δεῖν βύρσαν περὶ αὐτοῦ, νήϊα '
                                          'δὲ τὰ σχοινία, κωπέας δὲ τὰ ξύλα τὰ πρὸς πλοῦν ἐπιτήδεια.'}},
 {'id': 'photius-physical0164-verified-covering-20261021',
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'start': 78,
  'end': 108,
  'original_row_sha256': '975a115dbfa71b825d6e062d0508b72e0f056876a85c6ed414570708ae4bb72d',
  'original_text': 'παρὰ τὸ δεῖν βύρσαν περὶ αὐτοῦ',
  'corrected_text': 'παρὰ τὸ ἔχειν βύρσαν περὶ αὐτὸ',
  'prior_verification': 'verified',
  'selection': (11285, 11286, 'παρὰ τὸ ἔχειν βύρσαν περὶ αὐτὸ'),
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556',
           'observed_text': 'παρὰ τὸ ἔχειν βύρσαν περὶ αὐτὸ'},
  'evidence': 'Complete close reading of the inset grammatical note on Bekker physical 164, printed 429b. The '
              'printed explanation reads παρὰ τὸ ἔχειν βύρσαν περὶ αὐτὸ; neither δεῖν nor the final genitive '
              'αὐτοῦ is printed. The supplied Henry base text at decoded Greek unit 11285 independently '
              'agrees. This is a new correction to previously verified text; all earlier facts and contrary '
              'readings remain frozen.',
  'qualification': 'A fresh scan-supported correction to a previously verified display clause, counted '
                   'separately from the 385 held uncertainty identities. No earlier scan observation, '
                   'archive, role decision, or uncertainty measurement is rewritten.',
  'prior_verification_evidence': {'path': 'data/corpus_changes/photius-bekker-complete-review/review-status.json.gz',
                                  'sha256': '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
                                  'segment_index': 3,
                                  'verification': 'verified',
                                  'start': 51,
                                  'end': 172,
                                  'text': ' λέγει, βύρσαν δὲ τὸ δέρμα παρὰ τὸ δεῖν βύρσαν περὶ αὐτοῦ, νήϊα '
                                          'δὲ τὰ σχοινία, κωπέας δὲ τὰ ξύλα τὰ πρὸς πλοῦν ἐπιτήδεια.'}},
 {'id': 'photius-physical0164-verified-oars-20261021',
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
  'start': 148,
  'end': 171,
  'original_row_sha256': '975a115dbfa71b825d6e062d0508b72e0f056876a85c6ed414570708ae4bb72d',
  'original_text': 'τὰ πρὸς πλοῦν ἐπιτήδεια',
  'corrected_text': 'τὰ πρὸς κώπας ἐπιτήδεια',
  'prior_verification': 'verified',
  'selection': (11285, 11286, 'τὰ πρὸς κώπας ἐπιτήδεια'),
  'context_sha256': 'f5f907582b1194a25175b2329b9d447b24c66fe476f39a0bea6fdd8a8a374ae5',
  'scan': {'physical_page': 164,
           'region': [0.39, 0.485, 0.81, 0.73],
           'image_sha256': '5c5a62c17e54c81c49047fe5ab5db8ef010e3acc1b8f6bec0622da18ed617556',
           'observed_text': 'τὰ πρὸς κώπας ἐπιτήδεια'},
  'evidence': 'Complete close reading of the inset grammatical note on Bekker physical 164, printed 429b. The '
              'final definition describes the wooden pieces suitable for oars: τὰ πρὸς κώπας ἐπιτήδεια, not '
              'πλοῦν. The supplied Henry base text at decoded Greek unit 11285 independently agrees. This is '
              'a new correction to previously verified text; all earlier facts and contrary readings remain '
              'frozen.',
  'qualification': 'A fresh scan-supported correction to a previously verified display clause, counted '
                   'separately from the 385 held uncertainty identities. No earlier scan observation, '
                   'archive, role decision, or uncertainty measurement is rewritten.',
  'prior_verification_evidence': {'path': 'data/corpus_changes/photius-bekker-complete-review/review-status.json.gz',
                                  'sha256': '58fa74b6e2abdf8303ea3b1739f636c32edb6eb6ac63c2596f120b53e2c6eb99',
                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0164.8',
                                  'segment_index': 3,
                                  'verification': 'verified',
                                  'start': 51,
                                  'end': 172,
                                  'text': ' λέγει, βύρσαν δὲ τὸ δέρμα παρὰ τὸ δεῖν βύρσαν περὶ αὐτοῦ, νήϊα '
                                          'δὲ τὰ σχοινία, κωπέας δὲ τὰ ξύλα τὰ πρὸς πλοῦν ἐπιτήδεια.'}}]

_QUALIFICATIONS = {
 'authorial-body': 'A reading announcement or extract title transmitted within the Bibliotheca base text in Bekker 1825 and Henry 1959–1977. Codex numbers, running heads, and marginal edition labels are outside this classification. A Henry substitution is an editorial preference and does not resolve Bekker letterforms.',
 'transmitted-historical-commentary': 'Greek explanatory material transmitted within the work in both Bekker 1825 and the supplied Henry 1959–1977 base text, distinct from modern apparatus and reference numbers. This classification establishes its transmitted textual role; it does not independently date the note or claim Photius personally composed it. Source readings and contrary earlier observations remain separate.',
 'marginal-reference': 'A modern edition reference number outside the syntactic Greek body. The role is established from position, numeric suffix, and the uninterrupted parallel Greek sentence. No choice between competing numeral readings and no text deletion is authorized.'}


def _key(text):
    return tuple(edition.normalize(m.group()) for m in edition.WORD.finditer(text))


def _reading(spec, tokens):
    selection = spec['selection']
    if selection is None:
        return []
    first, stop, phrase = selection
    candidates = [t for t in tokens
                  if first <= t['refs'][0]['unit_index'] < stop]
    if phrase is not None:
        keys, wanted = [t['key'] for t in candidates], _key(phrase)
        matches = [i for i in range(len(keys)-len(wanted)+1)
                   if tuple(keys[i:i+len(wanted)]) == wanted]
        if len(matches) != 1:
            raise ValueError('Role witness is absent or repeated within its reviewed paragraph')
        start = matches[0]
        candidates = candidates[start:start+len(wanted)]
    if not candidates:
        raise ValueError('A body role cannot authorize an empty source reading')
    return [{'text':' '.join(t['text'] for t in candidates),
             'source_id':'tlg-photius-henry',
             'refs':[deepcopy(r) for t in candidates for r in t['refs']],
             'tokens':[{'text':t['text'],'refs':deepcopy(t['refs'])}for t in candidates],
             'role':'alternative',
             'location_basis':'Individually inspected source heading or explanatory paragraph, bounded by the neighboring Greek passages and pinned Henry decoded-node range.'}]


def _digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':')).encode()).hexdigest()


def _context(spec,units):
    if _digest(units)!=spec['context_sha256']:
        raise ValueError('The exact reviewed decoded-source context changed')
    return {'source_id':'tlg-photius-henry','sha256':SOURCE_SHA256,
        'units':deepcopy(units),
        'qualification':'Exact decoded Greek data nodes identifying the reviewed local paragraph; their inclusion does not certify the Bekker scan reading.'}


def _scan(spec,*,prior_observation=True):
    scan=deepcopy(spec['scan'])
    scan.update(source={'path':'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
        'sha256':SOURCE_PINS['data/corpus_changes/photius-bekker-readings/source-scan.pdf']},
        reviewed_at=REVIEWED_AT,review_basis='direct-scan-inspection')
    if prior_observation:scan['prior_observed_text']=spec['prior_observed_text']
    return scan


def _role_record(spec,units):
    """Build the complete expected public record from authored facts and pinned nodes."""
    key=spec['locus'],spec['segment_index'];old=spec['original_text']
    wrappers=deepcopy(RETIRED_WRAPPERS.get(key,{}))
    if wrappers:
        words=list(edition.WORD.finditer(old))
        if (not words or old[:words[0].start()]!=wrappers['prefix']
                or old[words[-1].end():]!=wrappers['suffix']):
            raise ValueError('Reviewed nonbody wrappers lost their exact Greek extents')
    context=_context(spec,units)
    rendering=deepcopy(RENDERING.get(key,{}))
    if 'separate_verified_suffix' in rendering:
        rendering['next_source_token']=deepcopy(NEXT_SOURCE_TOKEN)
    return {'role':spec['role'],'original_role':spec['original_role'],
        'original_text':old,'confidence':spec['confidence'],
        'retired_wrappers':wrappers,'subtype':spec['subtype'],
        'readings':_reading(spec,edition.tokenize(units)),'rendering':rendering,
        'evidence':spec['evidence'],'scan':_scan(spec),
        'qualification':_QUALIFICATIONS[spec['role']],'role_context':context}


def validate_record(key,role):
    """Reconstruct every field without access to the optional full HTML source."""
    specs={(s['locus'],s['segment_index']):s for s in SPECS}
    if key not in specs or not isinstance(role,dict):
        raise ValueError('Unknown reviewed role identity')
    units=role.get('role_context',{}).get('units')
    if not isinstance(units,list):
        raise ValueError('A role decision needs its exact archived decoded context')
    expected=_role_record(specs[key],units)
    if role!=expected:
        raise ValueError('Recorded role decision differs from its complete reviewed source authority')
    return deepcopy(expected)


def validate_context_pins(html_raw):
    """Recompute authored decoded-context hashes from the pinned optional source."""
    if hashlib.sha256(html_raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError('The supplied comparison edition differs from the reviewed source')
    parser=edition.EditionHTML();parser.feed(html_raw.decode('utf-8-sig'))
    for spec in SPECS+CORRECTIONS:
        first,stop,_=spec['selection']if spec['selection']else(0,0,None)
        _context(spec,parser.units[first:stop])
    return parser.units


def review_roles(html_raw,scopes):
    """Return all 39 frozen occurrence assessments without changing the inputs."""
    units=validate_context_pins(html_raw);tokens=edition.tokenize(units)
    expected={(s['locus'],s['segment_index'])for s in SPECS}
    actual={k for k,s in scopes.items()if s['record']['decision']=='retained-nonbody'}
    if actual!=expected:
        raise ValueError('Role assessment requires the exact 39 published nonbody identities')
    result={}
    for spec in SPECS:
        key=spec['locus'],spec['segment_index'];scope=scopes[key]
        segment=scope['record']['original_segment']
        old=scope['row']['text'][scope['start']:scope['end']]
        if (old!=spec['original_text'] or segment['text_role']!=spec['original_role']
                or segment['scan']['observed_text']!=spec['prior_observed_text']):
            raise ValueError('An assessed role lost its exact original text, role, or prior observation')
        if key in RENDERING and 'separate_verified_suffix'in RENDERING[key]:
            suffix=RENDERING[key]['separate_verified_suffix']
            if not scope['row']['text'][scope['end']:].startswith(suffix+' μὴν'):
                raise ValueError('Reviewed paragraph boundary lost its exact verified continuation')
            last=_reading(spec,tokens)[0]['tokens'][-1]
            indexes=[i for i,t in enumerate(tokens)if t['refs']==last['refs']]
            if len(indexes)!=1 or indexes[0]+1>=len(tokens):
                raise ValueError('Reviewed paragraph boundary lost its following source token')
            following=tokens[indexes[0]+1]
            if {'text':following['text'],'refs':following['refs']}!=NEXT_SOURCE_TOKEN:
                raise ValueError('Reviewed note boundary no longer precedes the new quotation')
        first,stop,_=spec['selection']if spec['selection']else(0,0,None)
        result[key]=_role_record(spec,units[first:stop])
    return result


def _correction_record(spec,units):
    return {k:deepcopy(spec[k])for k in ('id','locus','start','end',
        'original_row_sha256','original_text','corrected_text','prior_verification',
        'evidence','qualification','prior_verification_evidence')}|{'readings':_reading(spec,edition.tokenize(units)),
        'scan':_scan(spec,prior_observation=False),'source_context':_context(spec,units)}


def validate_correction_record(record):
    """Validate a fresh correction separately from every old uncertainty identity."""
    specs={s['id']:s for s in CORRECTIONS}
    if not isinstance(record,dict)or record.get('id')not in specs:
        raise ValueError('Unknown separately reviewed correction')
    units=record.get('source_context',{}).get('units')
    if not isinstance(units,list):
        raise ValueError('A fresh correction needs its exact archived decoded context')
    expected=_correction_record(specs[record['id']],units)
    if record!=expected:
        raise ValueError('Fresh correction differs from its complete reviewed source authority')
    return deepcopy(expected)


def review_corrections(html_raw,scopes):
    units=validate_context_pins(html_raw);rows={s['row']['locus']:s['row']for s in scopes.values()}
    result=[]
    for spec in CORRECTIONS:
        row=rows.get(spec['locus'])
        if row is None:
            raise ValueError('A separately reviewed correction lost its baseline row')
        text=row['text'];a,b=spec['start'],spec['end']
        if (_digest(row)!=spec['original_row_sha256']
                or text.count(spec['original_text'])!=1 or text[a:b]!=spec['original_text']):
            raise ValueError('A fresh correction lost its exact unique baseline clause')
        # This interval was verified, not one of the 385 uncertain identities.
        if any(s['row']['locus']==spec['locus']and s['start']<b and a<s['end']for s in scopes.values()):
            raise ValueError('A fresh correction overlaps an old uncertainty identity')
        first,stop,_=spec['selection'];result.append(_correction_record(spec,units[first:stop]))
    return result


def validate_scan(document, crop_png):
    """Recreate every authored review crop with the campaign renderer."""
    checked=set()
    for spec in SPECS:
        scan=spec['scan'];key=(scan['physical_page'],tuple(scan['region']))
        if key in checked:continue
        raw=crop_png(document,key[0],list(key[1]))
        if hashlib.sha256(raw).hexdigest()!=scan['image_sha256']:
            raise ValueError('A reviewed role source crop changed')
        checked.add(key)
    return len(checked)
