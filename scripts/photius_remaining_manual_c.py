"""Occurrence-specific supplied-edition readings for remaining Photius batch C.

These are editorial source selections, never blanket proofreading or scan
certification. The original scan readings and all contrary earlier witnesses
remain part of the caller's reversible audit.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-21T23:22:16Z'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {
    'data/corpus_changes/photius-bekker-editorial-substitutions/compiled-review.json.gz':
        '76abb40a4759da8659bf8646fc80a9310c1c519adc6fb4a7ef3fe5b767fed633',
    'data/corpus_changes/photius-bekker-readings/source-scan.pdf':
        'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
}
SPECS = [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0217.23',
  'segment_index': 1,
  'original_text': 'ἀποδίδωσι',
  'start': 17,
  'end': 26,
  'row_sha256': '5f61cf7e7708c6788e7c00432ff950a71ed728f6f8550aaf1b7c485513f0b3ad',
  'inherited_record_sha256': 'bba0bc7e8c557cbd5710c942a4df4b4239ef4a48f1cb2763703d5a60a2fa0293',
  'selection': (12695, 12698, 'ἀποδίδωσι'),
  'context_sha256': '5656593fe02f1fb24dd060b1cc4d09fad6866447c8557e80a13a83e2491bd643',
  'evidence': 'The western emperor writes to his brother about receiving Athanasius and restoring the '
              'episcopal throne; the same conditional sentence contains the target verb between '
              'ἀχιερατικὸν and θρόνον.',
  'rendering': {},
  'source_indices': [304025],
  'surface_sha256': 'c492ecfcd7bb4259efff554b0455a8a5cdf26112d29a8c9a2f3e7f6b5bfc5705'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0223.18',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθησαν',
  'start': 0,
  'end': 12,
  'row_sha256': '8a2cc38bd8d8a289570ac631bf62cd402b5118e7b8bd8344e95d55c7fe68a056',
  'inherited_record_sha256': '02186b13132cda146c016c45128e1d064bcb0b0f24511add7d53582b5a0891bc',
  'selection': (12849, 12854, 'Ἀνεγνώσθη'),
  'context_sha256': 'd02d8517bf293756cfecfb5fd2abe1939ed80e37e9fd8e5c879e23d9a4f65806',
  'evidence': 'The end of the Andocides account is followed by the codex 262 Lysias reading '
              'announcement and the inventory of his speeches. Select only the opening verb, not '
              'another occurrence elsewhere.',
  'rendering': {},
  'source_indices': [307946],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0225.45',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθησαν',
  'start': 0,
  'end': 12,
  'row_sha256': 'b29c03e87ef07266d9bacc1a2362dfe42081add347a85846115427ac11e45f1c',
  'inherited_record_sha256': '1fa87edd65c88e4f0b38f79a3c867ffccb2c0042706826e460e12fdc19cc626f',
  'selection': (12907, 12911, 'Ἀνεγνώσθη'),
  'context_sha256': 'ece6c07ccb6eb2a7dd612b0788f4016a8ef96bf08524eb16c7a6f3c8379627d5',
  'evidence': 'The Aeschines biography ends with death on the island; codex 265 then announces '
              'Demosthenes and his nearly complete speeches. This uniquely identifies the singular '
              'announcement verb.',
  'rendering': {},
  'source_indices': [309377],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0227.18',
  'segment_index': 1,
  'original_text': 'ἱζάων),',
  'start': 33,
  'end': 40,
  'row_sha256': 'a209156cf4fd696a068fad50abdd6251e61b6942920f41a00dd9c59647a859b7',
  'inherited_record_sha256': '326c122395d8772d38b3d227cc90328a39b54986904c842d615f5cd9b7145184',
  'selection': (12945, 12948, 'ἐξάγονται'),
  'context_sha256': '5661606800b0ee1434e9001ed4e1c87c38d724fdae56b23a5ee200583c8b14c2',
  'evidence': 'The discussion of a harsher and more passionate nature names Demosthenes and Aristides, '
              'then says διόπερ πολλάκις before the target and τῆς προθέσεως after it.',
  'rendering': {'retire_suffix': '),', 'boundary_after': ','},
  'scan': {'image_sha256': '870a4b1ba3adf3e08358c04a1a23ff432754fed2ec2a240e73128a8601aee521',
           'max_side': 3600,
           'observed_text': 'ἐξάγον[ται],',
           'physical_page': 227,
           'printed_page': 492,
           'region': [0.55, 0.105, 0.95, 0.765],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
  'source_indices': [310466],
  'surface_sha256': '984e01f192aa4d483a925fd731522351013ae49126b779b67e32fa63c3c48858'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0229.9',
  'segment_index': 1,
  'original_text': 'λοιδορεῖν',
  'start': 34,
  'end': 43,
  'row_sha256': '2dce8b934dad06358a73dae5c8164a894de2ac27571811df39611d8b93e68c21',
  'inherited_record_sha256': '6b8f8f9299c80317a176027c137175bde37363d83641d7a428614f46a89f4aab',
  'selection': (12978, 12981, 'λοιδορεῖται'),
  'context_sha256': '30960eeb89abe93d9dba7e0799c50acbf1f07f6b694b2b0d8be44743b7dceffc',
  'evidence': 'The Chaeronea anecdote describes the bush catching his cloak, his turning around, and '
              'the following Ζώγρει utterance; this pins the intervening verb independently of its '
              'uncertain ending.',
  'rendering': {},
  'source_indices': [311335],
  'surface_sha256': 'a9cbec0a3874d35b89ad76e32746f08997dba33e1df149025f7e7c25093c6196'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0233.30',
  'segment_index': 1,
  'original_text': 'σθ',
  'start': 6,
  'end': 8,
  'row_sha256': 'efcd021610837c4e3e245e863c25a7b60b960839f7a7ee875fe60e4df729ef4e',
  'inherited_record_sha256': 'b61c19a70ae8fd4770ea13b95acbafccec38626538807b71b0eb228495d642f6',
  'selection': (13108, 13112, 'Ἀνεγνώσθη'),
  'context_sha256': '51d3d89ce20042328d69115eb7177228ffaee7ddee854e527c34cf93264de124',
  'evidence': 'The conclusion about Paul overthrowing the adversary is immediately followed by codex '
              '271 announcing Asterius of Amasea and his exhortation to repentance. The source word '
              'supplies only the disputed internal sigma-theta letters after trimming the retained '
              'affixes.',
  'rendering': {},
  'source_indices': [314215],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0235.14',
  'segment_index': 1,
  'original_text': 'ἡμᾶφέτο',
  'start': 30,
  'end': 37,
  'row_sha256': '2ab5d09b264cd4c2dbd29157b8f0a8817ecfef02b961f10ce8d9e5a9233c47cc',
  'inherited_record_sha256': '4186ea702713a0b234f19a075ef3e96ceb4f19a877a5c73ded08b226197feb29',
  'selection': (13167, 13170, 'ἠμπίσχετο'),
  'context_sha256': 'd72e5a129209c4cd131dea1e5f719161169ed08457bc81ca3e4beb2e2820a199',
  'evidence': 'The good-Samaritan explanation identifies the mount as the body, with ὑποζύγιον τὸ '
              'ὁμόφυλον before ὅπερ and τυγχάνει σῶμα after the target verb.',
  'rendering': {},
  'source_indices': [315386],
  'surface_sha256': 'c7334c513ef1820e9ab16399afe3426ebbfb5af1c7c9ed0776497034ebcaf3df'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0235.20',
  'segment_index': 1,
  'original_text': 'προσεύξασθαι',
  'start': 6,
  'end': 18,
  'row_sha256': 'aea75fe0e1a982bb6d6a62c1fd69891303c265abdad497424a15e21372967baf',
  'inherited_record_sha256': '69454ffa054b49fd1d66a6d814999e0dc85a4d766ccc8b1975fbc7c1027994d9',
  'selection': (13170, 13173, 'προσεύξασθαι'),
  'context_sha256': '541a2ef34321d2ba9b801340aa16a6c411c2d46512c1d609a9b9c970f343c5cc',
  'evidence': 'The extract title quotes the two men ascending to the temple and is followed by the '
              'commentary on prayer in two parables. The target closes that particular quotation.',
  'rendering': {},
  'source_indices': [315428],
  'surface_sha256': 'c569874db182b17141932137d79eddf117d3432c25038e32b6d98d27b0ce7a71'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0241.1',
  'segment_index': 0,
  'original_text': 'συνέχατο; ἡ Λαζάρα',
  'start': 0,
  'end': 18,
  'row_sha256': '943439cf62a9e29e11b302dc0d2a8897a45c9534d36e3930f5ecbb224e2695ad',
  'inherited_record_sha256': 'aea584b9f57aee429858d708538310b76053231c63c85bd406eb86c19b11adc0',
  'selection': (13318, 13321, 'συνεξανοίξει Λαζάρου'),
  'context_sha256': '49b693465e502e8b68ebc014707f359d2b1e6e4923194a1f36843d51ca07c187',
  'evidence': 'The Lazarus introduction ends the preceding page with τὸ ἐμὸν στόμα τῷ τάφῳ and '
              'continues with this two-word expression before περικαθαίρων and κηλῖδα. The supplied '
              'edition divides συνεξανοίξει across adjacent decoded units; keep its complete source '
              'references together.',
  'rendering': {},
  'source_indices': [318858, 318859],
  'surface_sha256': '73e46a43882a030463499fa309267b20759d63f8eff23e6aee6e736cf692d8d5'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0241.19',
  'segment_index': 1,
  'original_text': 'φθόνῳ',
  'start': 7,
  'end': 12,
  'row_sha256': '0cf6b86b54fddb8132f21f789159a32d741194d95a381bbc8b3b4936727eead9',
  'inherited_record_sha256': 'd7aad0fce8cdff269dee1aead00c321f856bfadd57795edba3a44a90d78cedbd',
  'selection': (13323, 13326, 'φθόνου'),
  'context_sha256': 'ebc8aa686e7eca79e4d3cd2ae99e0fbaab7fdbf91211be1f21bdd37b5763e977',
  'evidence': 'The garden command to work and guard is followed by the warning about an unguarded gift '
              'becoming an entry for envy. The target is directly bounded by πρὸς ἐπιβουλήν and '
              'πρόσοδον τοῦ Θεοῦ in the same passage.',
  'rendering': {},
  'source_indices': [318992],
  'surface_sha256': 'b38332aa793258857e2b22a742b3503e244adfc33a3c9e71bc378d55e20b95af'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0246.9',
  'segment_index': 1,
  'original_text': 'προέρχεται',
  'start': 12,
  'end': 22,
  'row_sha256': 'a79825b268ca6247f4c70026feed1668a280f5576b3de3512152a02f2bed9f5d',
  'inherited_record_sha256': '2f919d1a382d6d6ca5a6e9baa3e165e96c33011966a705c2e5a44216203c3abf',
  'selection': (13453, 13456, 'προέρχεται'),
  'context_sha256': 'd8d47b0f2545c1590cd0d15f40bc10e02075f2968302d23698617d42540e1ef0',
  'evidence': 'The introductory comparison with two connected Chrysostom speeches ends by saying this '
              'speech proceeds from its own beginning; the next paragraph begins Ἰωάννην ἀνευφημήσω.',
  'rendering': {},
  'source_indices': [322052],
  'surface_sha256': '1d88c31deb58314c5c04025b3131ed8a8eccf0837208dc67f8321635c5fc4df1'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0246.25',
  'segment_index': 0,
  'original_text': 'Ἀνῴδη',
  'start': 0,
  'end': 5,
  'row_sha256': '1a0c27b4cae42482a3d2b36f71c21509e4cc76e7abcb4e7b6c1dc723975dab06',
  'inherited_record_sha256': '9d1c71f87b229b790b114b733fd67fed1908c5f6e4b956b6ef947f1d9b226490',
  'selection': (13457, 13462, 'Ἀνεγνώσθη'),
  'context_sha256': 'd18017188048653e6e964bc0518a03336a8a48aa817b6d5e7960c2b99d18cabf',
  'evidence': 'The preceding John-the-Baptist encomium closes with a voice sounding through the world; '
              'codex 275 next announces Hesychius of Jerusalem on James and David. Select only that '
              'announcement verb.',
  'rendering': {},
  'source_indices': [322179],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0260.5',
  'segment_index': 1,
  'original_text': 'διαλύεται',
  'start': 12,
  'end': 21,
  'row_sha256': 'fc97f5262d495086d58c1dfa2089ca8d423fa4137a4a4ac4f945fba2be49b335',
  'inherited_record_sha256': '293e3be6ea8dd2f81855bb858d642d44dc79505f4dace2e1ed422024500195a2',
  'selection': (13817, 13820, 'διαλέλυται'),
  'context_sha256': 'a8a29dd69318d44d48bc4615c6697e6938f5b4218d0e30f89174411688075a12',
  'evidence': 'The rich man is asked where his attendants and luxury have gone; leaves, winter, and the '
              'ended dream precede the target, and the question about Noah, Jacob, Isaac, and Abraham '
              'follows.',
  'rendering': {},
  'source_indices': [331296],
  'surface_sha256': 'e361e6b9c4db8ee5b40619a4988b596740192351215acf6e3941669b1cf362d3'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0260.18',
  'segment_index': 1,
  'original_text': 'ἀρρήσθ',
  'start': 20,
  'end': 26,
  'row_sha256': '5759ee3512e6e95949eface43e2e9ce40f0393b193760b3a0c02fcddfcc7ff5b',
  'inherited_record_sha256': 'c66637f077fe8f1dc6f5a4c69d99edd23cee05c382d0f8778d4a3ae25d0bc1ba',
  'selection': (13821, 13824, 'ἀφῄρηται'),
  'context_sha256': '44ae446280626b558b114521d666a0769d31fee2870ee462fbf581f42be9f060',
  'evidence': 'The passage contrasts joy over the righteous dead with not grieving for a sinner, then '
              'refers to the removed addition of sins before the Cyriacus letter summary. The chosen '
              'form is the supplied edition’s reading, not certification of the contrary contracted '
              'Bekker ending.',
  'rendering': {},
  'source_indices': [331395],
  'surface_sha256': '1a3dbace3215a2f83eec842a044baf63c1a54dd61f46721c5cb1dfc6dd9087b2'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0261.1',
  'segment_index': 3,
  'original_text': 'ὀνομάσθη',
  'start': 122,
  'end': 130,
  'row_sha256': '906eb33d8879de19a5dbc527efd0b8a6f6535a2bdb0707368d9d03d583addd39',
  'inherited_record_sha256': '94491dc3a2e79eede33945580935fef7915bff935d058be6fcd02e187c16b426',
  'selection': (13845, 13848, 'ὠνομάσθη'),
  'context_sha256': '427670644081a028480153cc898e67abd8b83711fc4260481961024b2f8025b1',
  'evidence': 'The physiological account says oppressive heat prevents breathing and gives the name '
              'πνῖγος; the naming verb precedes the independent explanation πνίγεται γάρ.',
  'rendering': {},
  'source_indices': [331900],
  'surface_sha256': 'efde9a02a8f001c430774e595dd689570ec0ce931034a3babf8b96db1b404c18'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0261.1',
  'segment_index': 5,
  'original_text': 'ἀν/γ)',
  'start': 132,
  'end': 137,
  'row_sha256': '906eb33d8879de19a5dbc527efd0b8a6f6535a2bdb0707368d9d03d583addd39',
  'inherited_record_sha256': '3d52a1c6ebcdd77ec2ce5f26101bd486b3623ff6ac8058d5c311d8cdbb943ce3',
  'selection': (13845, 13848, 'πνίγεται'),
  'context_sha256': '427670644081a028480153cc898e67abd8b83711fc4260481961024b2f8025b1',
  'evidence': 'The same paragraph explains the word πνῖγος with this verb before γὰρ ἢ καὶ πνιγομένῳ. '
              'It is a separate token from the preceding naming verb and is selected once. Direct '
              'inspection of the pinned Bekker upper-column crop shows a contracted word ending '
              'before γάρ, without a parenthetical clause; the preimage closing parenthesis is an '
              'OCR contraction wrapper rather than source punctuation.',
  'rendering': {'retire_suffix': ')'},
  'scan': {'image_sha256': '94d5dfea267e9ca01e9f6b2625cd290f28177d73310d202441cf34c6dcb4a8d1',
           'max_side': 3600, 'observed_text': 'πνίγε[σ?]θαι', 'physical_page': 261,
           'printed_page': 526, 'region': [0.21, 0.105, 0.59, 0.765],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
  'source_indices': [331901],
  'surface_sha256': 'd45d57649dba2fa1e060044b884c63d2d69c8635753eea0ec608267530a1db51'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0261.4',
  'segment_index': 19,
  'original_text': 'σεί(ε)ἡ',
  'start': 1841,
  'end': 1848,
  'row_sha256': '0585c8bce053c445a078c0743d7132fa5887ea3ee377d3aa3e4d6d020aa55b6e',
  'inherited_record_sha256': 'ec0448057e7bccc47870cbf605ed8dcbdfa5dfaf0baef6093b20015635e07b56',
  'selection': (13870, 13873, 'σείεσθαι'),
  'context_sha256': '570e5d069ee27236546494bfaae0ee4f454d77fd61783388185f8a20ff6a9608',
  'evidence': 'The dizziness explanation describes looking at high, large, steep objects and the '
              'extended sight being shaken, followed by καὶ κραδαίνεσθαι τὴν ὄψιν.',
  'rendering': {},
  'source_indices': [332511],
  'surface_sha256': '2402e2a1e2fccb0397ae5ef7d63271b9a06d54539754eec8bbdb002068eec294'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0261.4',
  'segment_index': 21,
  'original_text': 'κραδαίνε(σ)',
  'start': 1853,
  'end': 1864,
  'row_sha256': '0585c8bce053c445a078c0743d7132fa5887ea3ee377d3aa3e4d6d020aa55b6e',
  'inherited_record_sha256': 'ee3b971f24377cf60b945d7e2733b46221a41917c759ffab96be9a47bef6ed21',
  'selection': (13870, 13873, 'κραδαίνεσθαι'),
  'context_sha256': '570e5d069ee27236546494bfaae0ee4f454d77fd61783388185f8a20ff6a9608',
  'evidence': 'The same extended-sight clause coordinates this second infinitive after σείεσθαι καί and '
              'before τὴν ὄψιν; select its own token rather than reusing the first verb.',
  'rendering': {},
  'source_indices': [332513],
  'surface_sha256': '069246c7b333e0b6aafa230d38714f1b8f7c516a3f1446e4baccb3dc20e44a8a'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0263.7',
  'segment_index': 1,
  'original_text': 'οἴων',
  'start': 9,
  'end': 13,
  'row_sha256': '2229826c536c5046c89ba41ea09dd6c4eba62f2400fc1a20d3c7284fa4f977fc',
  'inherited_record_sha256': '4e0da70736e02ce1cb703d9b3796d208030e901cb179f5ff024b1edf7ad07d7a',
  'selection': (13902, 13905, 'οἴονται'),
  'context_sha256': 'a3efe8c0e884229ad2023cebba776e8993beec33c7e1ab7af508569c46f1f78d',
  'evidence': 'The locust and bruchus account first describes generation from each other, then '
              'introduces an opinion about a color-based sign before returning to food and generation.',
  'rendering': {},
  'source_indices': [333266],
  'surface_sha256': '0c8d772e5eba9ba6a3b277df7c17eaf84ae8fc158d4e187a2f5bb826da69d36f'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0263.24',
  'segment_index': 1,
  'original_text': 'γένεθ',
  'start': 16,
  'end': 21,
  'row_sha256': '3d015a3dbcd4426ba3b97f9514001eb6667ec44d9aa91afb223f86f2ba2f95b5',
  'inherited_record_sha256': '1b276b70bab8834eb4277ff0e2729b109ab560190e5e631b4077cf9b3016abd9',
  'selection': (13906, 13909, 'γενέσθαι'),
  'context_sha256': 'cd759374fc33466126236a9bf316f85e9e9196d83ba4898922e8a8302fcf74e7',
  'evidence': 'The paragraph lists rain and bloodshed as causes of snakes and then specifically reports '
              'a multitude of snakes in Thessaly; the target closes that report before the mice account '
              'begins.',
  'rendering': {},
  'source_indices': [333406],
  'surface_sha256': 'a283983a06bb454d9a70566061d2845e1c76f59b40482752a38762e2457b6a6d'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0263.39',
  'segment_index': 1,
  'original_text': 'ἀνμῶν',
  'start': 7,
  'end': 12,
  'row_sha256': '8ded7d73760ccb2aecc16d3635cc8b7184c461f047cc825bf6ba365267db935f',
  'inherited_record_sha256': '255e237d980bb069ce3581098804384a14d5ef1d80aa6023d64e45b8740ae39a',
  'selection': (13910, 13913, 'ἀνιμῶνται'),
  'context_sha256': 'd5571aa5b30d08306b13f76b68a9eeb56b65c7edfa666255aa722b9ebf8bd2fd',
  'evidence': 'Mice are said to eat iron and gold; those working the gold mines then cut them open and '
              'retrieve gold. The target closes that sentence before the Egyptian two-footed-mice '
              'report.',
  'rendering': {},
  'source_indices': [333516],
  'surface_sha256': '0fe1b989e136c9b073ba87cfefebf8dfd3121695384ed1801d36f9553c03f7ee'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0264.7',
  'segment_index': 1,
  'original_text': 'Ἀνεγράφη',
  'start': 0,
  'end': 8,
  'row_sha256': '4bae939bf71dc413d98d2c840b710797785608dcb528b8b9c61d0ec41303eb67',
  'inherited_record_sha256': '746ee91ad8b2249ba16a791170aa4b2c48a9e43090ea3106d8977e950c05b787',
  'selection': (13949, 13953, 'Ἀνεγνώσθη'),
  'context_sha256': 'a570d95aba3112c88cafc4bd1a440d21e57500fee31e585b86634023e30f4013',
  'evidence': 'After the honey and bee discussion, codex 279 announces Helladius of Besantinus and the '
              'Chrestomathies. Select the opening announcement verb independently of the following '
              'title variants.',
  'rendering': {},
  'source_indices': [334469],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0267.2',
  'segment_index': 3,
  'original_text': 'φροντίεται',
  'start': 558,
  'end': 568,
  'row_sha256': '9a61b3d79f3126622e635207a13299161dad4b43a4c936524e76b66e0bc0fb19',
  'inherited_record_sha256': '6b6bb97c5f9347826a6e5e515202091d2e3c1dbc7aab32231826b86aabcf3dd1',
  'selection': (14087, 14090, 'βρενθύνεται'),
  'context_sha256': '106d18a40b3acf4bf883ed2b32f407db1f7e585bf7631db9e79381820a6d4364',
  'evidence': 'The Helladius lexical note follows Callimachus’s unusual φοιτίζειν and defines a verb '
              'through ἀλαζονεύεται, then derives it from βρένθιον and perfume. These ordered '
              'neighboring glosses uniquely locate the target.',
  'rendering': {},
  'source_indices': [336372],
  'surface_sha256': '9688351cf4762fdea618f9c1f862494cc482a106397edc388f3967c029e10f19'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0268.1',
  'segment_index': 13,
  'original_text': 'ὠλε....',
  'start': 1392,
  'end': 1399,
  'row_sha256': '9909cc272526ac2458114ebbe4b93a8909a357890ba83750addb9f5c799476d3',
  'inherited_record_sha256': '92a27da2ddb42c31a0c2860118bd893fd0922be28a4ddf9c4cfdfcb9f8a61bf9',
  'selection': (14117, 14124, 'ὤμιλλαν οἱ Ἀττικοὶ διὰ τοῦ ο'),
  'context_sha256': '0434e973129f80662dfa706af72bcbadcb517ef6f50c717e6d299f7a0e0090c3',
  'evidence': 'The spelling note follows εἴσω versus ἔσω and contrasts Attic pronunciation with '
              'customary α. Bekker visibly prints an ellipsis after the partial word; the supplied '
              'Henry 533a text provides this complete bounded Greek gap before προφέρουσιν. This is an '
              'explicit editorial fill, not a transcription of hidden Bekker letters.',
  'rendering': {'retire_suffix': '....'},
  'scan': {'image_sha256': '5322b5100706ace010b8fec7066686789d65b9b73ff40379c53ef587054ff5b7',
           'max_side': 3600,
           'observed_text': 'ὕλε....',
           'physical_page': 268,
           'printed_page': 533,
           'region': [0.05, 0.105, 0.43, 0.765],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
  'source_indices': [336837, 336838, 336839, 336840, 336841, 336842],
  'surface_sha256': 'b76b3b0770869f297cecc08a4ac8cd5498f3f96bb5a5fc6326d14375ea66e33b'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0271.3',
  'segment_index': 0,
  'original_text': 'Ἀνεγνώσθι',
  'start': 0,
  'end': 9,
  'row_sha256': 'c463e46a3d8562f3bb7d93ace6beefcca7e6c0559d15a020a9d1fe0c69db00a5',
  'inherited_record_sha256': '97277958f9593b79aa2e30caa6b1e457eba6594044928d812bec24cca9d84039',
  'selection': (14227, 14232, 'Ἀνεγνώσθη'),
  'context_sha256': 'a6fe8a5d11bd77c85cc56a965b0d1ee168c01937c79e4480841a2dca2df10717',
  'evidence': 'Codex280 announces Eulogius, archbishop of Alexandria, after the preceding Helladius '
              'materials and before the first numbered discourse. Only the opening verb is selected; '
              'the differing book description remains outside this occurrence.',
  'rendering': {},
  'source_indices': [338765],
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0271.5',
  'segment_index': 3,
  'original_text': 'ποιεῖν',
  'start': 152,
  'end': 158,
  'row_sha256': '5deb3732ae8a256c7e9826fd9c0f29345fe723e7dcaa84d38ab0da84eb7a4fd4',
  'inherited_record_sha256': '32a69316122f0f1df25ff89e982b243458e301ecc7558da98ea0c2c5655ddf72',
  'selection': (14232, 14235, 'ποιεῖσθαι'),
  'context_sha256': 'afd457c9a3e9f9d3edbf432afb7574307eed27b7310297096d42fce59a46ad41',
  'evidence': 'The Novatian discussion states that even purified people refuse gathering with others '
              'and prayers and psalms; this infinitive follows ψαλμῳδίας and precedes the separately '
              'selected refusal verb.',
  'rendering': {},
  'source_indices': [338819],
  'surface_sha256': '181a9f170add530142aadbb536332d79e53218e82aae762ca4379fac6af37c42'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0271.5',
  'segment_index': 5,
  'original_text': 'ἡμῖν παρατινῶσι',
  'start': 159,
  'end': 174,
  'row_sha256': '5deb3732ae8a256c7e9826fd9c0f29345fe723e7dcaa84d38ab0da84eb7a4fd4',
  'inherited_record_sha256': '4f79a48f591407b4b08733a82d1434ea22d2b3259f885fb8c59d580244039335',
  'selection': (14232, 14235, 'παραιτοῦνται'),
  'context_sha256': 'afd457c9a3e9f9d3edbf432afb7574307eed27b7310297096d42fce59a46ad41',
  'evidence': 'In the same Novatian sentence this refusal verb follows ποιεῖσθαι and precedes the Abel '
              'and Cain example. It corresponds to the two-word uncertain OCR span without borrowing '
              'the adjacent held infinitive.',
  'rendering': {},
  'source_indices': [338820],
  'surface_sha256': '0952b4a1b4edb4e3bf7019d79f865d0566e83a19e6e22311fca597d0d8ccb6bf'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0275.31',
  'segment_index': 0,
  'original_text': '30σημαίνοντος',
  'start': 0,
  'end': 13,
  'row_sha256': '4033f006d95c1a1d63a20147c1544305b43636a8edb8c60103f26a814ad38d93',
  'inherited_record_sha256': '4278521126377cc5f92d3c6a97168f78f00418f89256915d96f35e79d1d44597',
  'selection': (14341, 14344, 'σφαγιασθέντος'),
  'context_sha256': '60d4a0fb2a3e18d44e7ca3075343f0c43b7f9e46498b6f5330adff60c6bc9b22',
  'evidence': 'The Hebrews explanation speaks of the one true sacrifice and the lamb of God taking away '
              'the world’s sin, followed by the selected participle and μηκέτι ὑπολελεῖφθαι. The fused '
              '30 in the preimage is visibly the marginal line number, not part of this Greek word.',
  'rendering': {'retire_prefix': '30'},
  'scan': {'image_sha256': '6bf0932ea8608b7b117ff5f58c62e4aaca0ca419c711b1dd04ed5bc94d4b0c85',
           'max_side': 3600,
           'observed_text': 'σφαγια[σ?]θέντος',
           'physical_page': 275,
           'printed_page': 540,
           'region': [0.55, 0.105, 0.95, 0.765],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
  'source_indices': [341658],
  'surface_sha256': 'c71a82895b3f601092943cffb16fc32a77bdb40174eb778928449043fec8c769'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0278.1',
  'segment_index': 3,
  'original_text': 'ἐπεορᾶζ(ω)',
  'start': 114,
  'end': 124,
  'row_sha256': '8d6781f8a99cc18e70b6ecf2e9c5ba6309cfd2b772d410adb91b4eac81e9a366',
  'inherited_record_sha256': '037ac001a8b7fc2807e82d469c17c5d03fc79fd06948feebb3eb9c47646cfc88',
  'selection': (14394, 14397, 'ὑπερορίζεται'),
  'context_sha256': '4fa8c4b9964c47c155d62dbc9ecb6a85a3dba256115861a6c9de420e501c3f86',
  'evidence': 'The comparison of Job and the Corinthian sinner says the evil one does not receive '
              'authority over the soul, then has μᾶλλον μὲν οὖν before the target and αὐτῆς after it. '
              'The following sentence explains the handing over for bodily destruction.',
  'rendering': {},
  'source_indices': [343132],
  'surface_sha256': '1833379afb10b337ddd1d6ec63952e51cf4f6d09fc12fe3bd75199c324cd9ad7'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0279.3',
  'segment_index': 3,
  'original_text': 'λέγε·θροῦ',
  'start': 150,
  'end': 159,
  'row_sha256': '8a39a1e2a3a890b20ceeebcd2eb8a1cbab7223497c99a90ae795c964320e9639',
  'inherited_record_sha256': '2b37d777a1f4b8164acf7f91dcc99c246243bceea5c53b3ea513a7778fccf8a2',
  'selection': (14434, 14438, 'λέγεται'),
  'context_sha256': '2411970819449cc834ca98c3410dc072d570bae721b1efeb61293cded96f1273',
  'evidence': 'The judgment discussion denies literal co-seating as judges and compares the saints’ '
              'role with the Gospel Ninevites and queen of the south. The target stands between ὥσπερ '
              'and καὶ ἐν τοῖς εὐαγγελίοις.',
  'rendering': {},
  'source_indices': [344148],
  'surface_sha256': 'cf9649e50f2430481115a74c5bc5cf62d0f5078d18ef519ede03c2e5ab35e991'}]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _reading(spec, units):
    tokens = edition.tokenize(units)
    wanted = [edition.normalize(match.group())
              for match in edition.WORD.finditer(spec['selection'][2])]
    starts = [i for i in range(len(tokens) - len(wanted) + 1)
              if [token['key'] for token in tokens[i:i + len(wanted)]] == wanted]
    if not wanted or len(starts) != 1:
        raise ValueError('The authored manual reading must occur once in its exact context')
    chosen = tokens[starts[0]:starts[0] + len(wanted)]
    indexes = spec['source_indices']
    if (len(indexes) != len(chosen) or any(type(i) is not int or i < 0 for i in indexes)
            or any(right != left + 1 for left, right in zip(indexes, indexes[1:]))):
        raise ValueError('A manual reading needs its consecutive complete-edition token indices')
    return [{'text': ' '.join(token['text'] for token in chosen),
             'source_id': 'tlg-photius-henry', 'role': 'alternative',
             'refs': [deepcopy(ref) for token in chosen for ref in token['refs']],
             'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs']), 'source_index': index}
                        for token, index in zip(chosen, indexes)],
             'location_basis': 'An individually reviewed occurrence in the exact decoded paragraph and its ordered neighboring context.'}]


def _record(spec, units):
    if not isinstance(units, list) or _digest(units) != spec['context_sha256']:
        raise ValueError('The pinned decoded manual context changed')
    first, stop, _ = spec['selection']
    if [unit['unit_index'] for unit in units] != list(range(first, stop)):
        raise ValueError('Manual context no longer has its exact ordered source units')
    scan = deepcopy(spec.get('scan'))
    if scan is not None:
        scan.update(reviewed_at=REVIEWED_AT,
            review_basis='direct-scan-inspection-of-disputed-rendering',
            qualification='The image establishes the declared ellipsis, marginal line number, or contraction wrapper; it does not certify unresolved Greek letterforms.')
    return {'kind': 'source-reviewed-editorial-occurrence', 'role': 'authorial-body',
            'original_text': spec['original_text'],
            'current_extent': {'start': spec['start'], 'end': spec['end']},
            'original_row_sha256': spec['row_sha256'],
            'inherited_record_sha256': spec['inherited_record_sha256'],
            'surface_sha256': spec['surface_sha256'],
            'readings': _reading(spec, units), 'rendering': deepcopy(spec['rendering']),
            'evidence': spec['evidence'], 'reviewed_at': REVIEWED_AT, 'scan': scan,
            'qualification': 'Prefer this exact supplied-edition Greek reading under the explicit editorial policy. It does not certify the Bekker scan or other text in the row; retain all previous readings, uncertainty qualifications, fragments, and unrelated exclusions.',
            'source_context': {'source_id': 'tlg-photius-henry', 'sha256': SOURCE_SHA256,
                               'units_sha256': spec['context_sha256'], 'units': deepcopy(units)}}


def validate_record(key, record):
    """Reconstruct the complete authored record from frozen public source nodes."""
    specs = {(spec['locus'], spec['segment_index']): spec for spec in SPECS}
    if key not in specs or not isinstance(record, dict):
        raise ValueError('Unknown manual batch C identity')
    context = record.get('source_context')
    if not isinstance(context, dict):
        raise ValueError('Manual review requires its exact archived source context')
    expected = _record(specs[key], context.get('units'))
    if record != expected:
        raise ValueError('The manual decision differs from its complete authored authority')
    return deepcopy(expected)


def review_remaining(html_raw, scopes):
    """Return all 30 exact manual decisions without modifying their live scopes."""
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied manual comparison source changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    result = {}
    for spec in SPECS:
        key = spec['locus'], spec['segment_index']
        if key not in scopes:
            raise ValueError('A manual batch C identity is absent')
        scope = scopes[key]
        row, inherited = scope['row'], scope['record']
        if (_digest(row) != spec['row_sha256'] or _digest(inherited) != spec['inherited_record_sha256']
                or row['locus'] != key[0] or inherited['locus'] != key[0]
                or inherited['segment_index'] != key[1] or scope['start'] != spec['start']
                or scope['end'] != spec['end'] or inherited['original_text'] != spec['original_text']
                or row['text'][spec['start']:spec['end']] != spec['original_text']
                or inherited['original_segment'].get('fragments')
                or inherited['original_segment']['text_role'] != 'authorial-body'):
            raise ValueError('A manual occurrence lost its exact original scope or exclusion status')
        first, stop, _ = spec['selection']
        result[key] = _record(spec, parser.units[first:stop])
    return result


def validate_scan(document, crop_png):
    """Reproduce the four directly inspected special-rendering source images."""
    count = 0
    for spec in SPECS:
        scan = spec.get('scan')
        if scan is None:
            continue
        raw = crop_png(document, scan['physical_page'], scan['region'])
        if hashlib.sha256(raw).hexdigest() != scan['image_sha256']:
            raise ValueError('A manually reviewed rendering source image changed')
        count += 1
    return count
