"""Occurrence-specific contextual readings for 32 held Photius passages.

This source authority proposes editorial preferences, never scan verification.
An orphan, two absent/reordered counterparts, and two divided-word suffixes
remain explicit holds. No source spelling alone authorizes an occurrence.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-21T23:14:28.998247+00:00'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {'data/corpus_changes/photius-bekker-editorial-substitutions/compiled-review.json.gz': '76abb40a4759da8659bf8646fc80a9310c1c519adc6fb4a7ef3fe5b767fed633',
 'data/corpus_changes/photius-bekker-readings/source-scan.pdf': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}
SPECS = [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0145.19',
  'segment_index': 1,
  'original_text': 'ὡς ὁ Κόδρος κ',
  'start': 31,
  'end': 44,
  'original_row_sha256': 'cccec2ecca986f8b245a1cb685a3ef480ba1fd45a96fddecb5fc9d4f602d9b4d',
  'inherited_record_sha256': 'a644daf6d9b6c2d7b4ea3ed42ef50c691ae4bf3cee40b60fb07b8f2fc43645aa',
  'context_start': 258413,
  'context_stop': 258432,
  'context_sha256': 'a18037a7626b06b4bcb9c4982ff0a6e2b085946c1081fd6e84073e719c498a3d',
  'selection': [258420, 258424],
  'expected_source_text': 'ὡς οὐ Κόδρῳ γε',
  'evidence': 'Within the Codrus discussion, the sentence follows Ἐὰν οὕτω κρίνωμεν and continues μετέσται '
              'τῆς φιλοτιμίας. These flanks locate ὡς οὐ Κόδρῳ γε, not another occurrence of the name.',
  'rendering': {},
  'surface_sha256': 'cc99a906d3e2ef27631e17d65bd64d4f9ea834a9ce5216f047157a762f26f808'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0145.30',
  'segment_index': 1,
  'original_text': 'μετεχκῶς',
  'start': 22,
  'end': 30,
  'original_row_sha256': '94f0f1003aace4ce53a8dcef48ce9f8c23249841bf7e0f28aaaba36e926f701a',
  'inherited_record_sha256': '92567014453d3053f96cab66e7902a8464009351389f7e72a87236982db8a6ff',
  'context_start': 258506,
  'context_stop': 258522,
  'context_sha256': 'b7f6564a75d7ff92b0f43506c201f8f5386f05fa62ef92619fc068b11c310ce7',
  'selection': [258513, 258514],
  'expected_source_text': 'μετεσχηκὼς',
  'evidence': 'The observation concerns someone participating in the present age. The full source clause '
              'has τοῦ νυνὶ χρόνου before μετεσχηκὼς and ἔχει συμβαλέσθαι γνώμην after it. The adjacent '
              'case ending differs and is not silently changed.',
  'rendering': {},
  'surface_sha256': '6ff40febc72235d6b7b5ab21162077de72546ed6cd50298c577ee02f49c796cc'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0145.30',
  'segment_index': 3,
  'original_text': 'συμβαλεῖν',
  'start': 36,
  'end': 45,
  'original_row_sha256': '94f0f1003aace4ce53a8dcef48ce9f8c23249841bf7e0f28aaaba36e926f701a',
  'inherited_record_sha256': '1be6bfa3b430337577304387677adb5778407e9cd2a52617b56f89b531d55283',
  'context_start': 258508,
  'context_stop': 258524,
  'context_sha256': 'c6c6c4c35bd18dc2f8c513c04db5854130acb6dbbd8dd9569efe9493b0f2b4b2',
  'selection': [258515, 258516],
  'expected_source_text': 'συμβαλέσθαι',
  'evidence': 'The same present-age clause places συμβαλέσθαι between ἔχει and γνώμην περὶ ὧν πρόκειται '
              'λόγος. This distinct token is not the preceding μετεσχηκὼς selected for segment1.',
  'rendering': {},
  'surface_sha256': '114c35e10cac0bcf4e584a67252b13d08edcfda5b5ae18212f476e3d8e9fec5e'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0152.4',
  'segment_index': 9,
  'original_text': 'χεῖρον',
  'start': 1871,
  'end': 1877,
  'original_row_sha256': '458898851d0e686ebdc3087a13ebd15e9013f7c9103718da0a989fe64f4ed045',
  'inherited_record_sha256': '1a156e64b1b22d5ea0b44657b5eed57997aded147fb92cddd17ec583d3e7dd9a',
  'context_start': 263359,
  'context_stop': 263375,
  'context_sha256': '38ed0ea0b4038fe88689af33c4f382683180c160b1c3ace347c22d5b3818ac4c',
  'selection': None,
  'expected_source_text': None,
  'evidence': 'The source clause reads ἰσχυρότατον πάντων ὡς ἐν ψεύδεσιν ὂν σχεδόν. The held target is '
              'before ὡς, while σχεδόν occurs after ὂν. The contextual passage is established, but this '
              'reordered clause gives no exact target-position nonempty source interval; do not borrow the '
              'later word.',
  'rendering': {},
  'held_reason': 'empty-position-counterpart',
  'surface_sha256': None},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.32',
  'segment_index': 1,
  'original_text': 'ἡγεῖσθ',
  'start': 26,
  'end': 32,
  'original_row_sha256': '69d27724993fbdc5131758eb3cb1ccd5bdcb748704f110b7e8771049fe0cddb2',
  'inherited_record_sha256': 'e40f06006396fff5ae742c471073405bb254768e2991e8a73e201bdf8e1071a1',
  'context_start': 264254,
  'context_stop': 264270,
  'context_sha256': 'f76c5d9963bef7f6a96f812a42c4e23ae9a7e6d07756435ac1a519c4bac9af3f',
  'selection': [264261, 264262],
  'expected_source_text': 'ἡγεῖσθαι',
  'evidence': 'The source continues the comparison of persuaders and the persuaded with τῶν πεισάντων '
              'πρῶτον ἡγεῖσθαι, followed by Ἔγκειται μὲν γάρ. The extra current ὑπάρχειν is outside this '
              'target and remains unchanged.',
  'rendering': {},
  'surface_sha256': 'f8498c24de3c769a481fa0eb5c0eab42ea4c2c781bf4920cf5d290041546970d'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.1',
  'segment_index': 2,
  'original_text': 'Ἀνεγνώσθη',
  'start': 2,
  'end': 11,
  'original_row_sha256': '1a9ec9b66d26af8a447eaceaec8e6a5dea6f9bce3e5048db8a2793bcee84cb78',
  'inherited_record_sha256': '0630c75c017a6952f14129479daad7ac144d0d80f0c7c674048172d2de51e0a7',
  'context_start': 266491,
  'context_stop': 266507,
  'context_sha256': '716f6485d1210fba0639550904f05155bcbc83e97c3ffcedec11d0f070cce753',
  'selection': [266498, 266499],
  'expected_source_text': 'Ἀνεγνώσθη',
  'evidence': 'This is the reading announcement for the common defense, immediately before τοῦ αὐτοῦ ὑπὲρ '
              'τῆς κοινῆς ἀπολογίας and the extract title ὑπὲρ Περικλέως. The same announcement verb '
              'elsewhere does not select this occurrence.',
  'rendering': {},
  'surface_sha256': '59253ce47c3d2b7a4462e75d14112769035c7ae4aae52b856525c67e553782d8'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.5',
  'segment_index': 0,
  'original_text': 'Παρατεῖδι',
  'start': 0,
  'end': 9,
  'original_row_sha256': 'ef3ee9be6b66dc230c5af87d2b8be63c9f38b04f616bc5aa2b6ecafd974c6a13',
  'inherited_record_sha256': '642398ae890448c9b2792cea4a5103f1dda41721b9dd708a4d8aebacfe1220ce',
  'context_start': 266517,
  'context_stop': 266533,
  'context_sha256': '191779dcb4ea545dfec52d7280e534c5d9d543fdf5e00ba8b869ec89003648fd',
  'selection': [266524, 266525],
  'expected_source_text': 'Παραιτεῖσθαι',
  'evidence': 'The proem of Aristides for the four men begins Παραιτεῖσθαι μὲν οὖν οὐκ οἶδ ὅτι δεῖ περὶ '
              'τῶν αὐτῶν πολλάκις. The following long Pericles discussion confirms this first word; the '
              'extra source οὖν is outside the target.',
  'rendering': {},
  'surface_sha256': '1cd6c7f5a682bc7b09833c9f938dc88a0ab5171c1e22ee178368f98551433585'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0160.2',
  'segment_index': 5,
  'original_text': 'μίμνεσθαι',
  'start': 875,
  'end': 884,
  'original_row_sha256': '9d6874704898d8399c65d9f90890fabc42f71d818a26558e1a65c358c2de0800',
  'inherited_record_sha256': 'dfbec94dd93b4406e72fb841844882bcbb1b5f43c70d461977ec77592577a9c1',
  'context_start': 267843,
  'context_stop': 267859,
  'context_sha256': 'aa80750d7aea6d486434e64f4d4adacf2ac5cead52a31a4f8ed1c380b2907763',
  'selection': [267850, 267851],
  'expected_source_text': 'μέμφεσθαι',
  'evidence': 'In the Pericles example, the source places μέμφεσθαι after οὔτε ἑαυτῷ and before '
              'αἰσχύνεσθαί τε ὑπὲρ αὑτῶν. The neighboring disputed expression is recorded separately.',
  'rendering': {},
  'surface_sha256': '1363c806aa4ba9673eeda2825c27dd48dd5ac7c5ea00e4e15599b60070151019'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0160.2',
  'segment_index': 7,
  'original_text': 'ἀρχεῖν δὲ',
  'start': 886,
  'end': 895,
  'original_row_sha256': '9d6874704898d8399c65d9f90890fabc42f71d818a26558e1a65c358c2de0800',
  'inherited_record_sha256': '5a4c5ae15acd429da9c69ed68be0291c12306c16366a9d9b4be7f12c4e8a3f80',
  'context_start': 267844,
  'context_stop': 267860,
  'context_sha256': '24538368e6b41bc3ccc977fa2c11a36f1acf65ae7b128d9a987a89e359d4cc38',
  'selection': [267851, 267852],
  'expected_source_text': 'αἰσχύνεσθαί',
  'evidence': 'The source has αἰσχύνεσθαί immediately after μέμφεσθαι and before τε ὑπὲρ αὑτῶν ἅμα καὶ '
              'τοῖς καιροῖς. One complete source word is preferred over this two-word transcription; no '
              'adjacent identity is consumed.',
  'rendering': {},
  'surface_sha256': '22c069bdfc228bcc31f9333c8be3290f9b77acf63abf6af533d47df2ee8865b4'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0160.3',
  'segment_index': 5,
  'original_text': 'δή πῃ',
  'start': 215,
  'end': 220,
  'original_row_sha256': '00a2905b17c0a4db28614a0813eae9e9b7f519a6903a86824239ad1b997c78c9',
  'inherited_record_sha256': 'b73483d9738271ade77fe364215439c5a6544e0cc0a13b07da46aac0c7fccd8e',
  'context_start': 268050,
  'context_stop': 268066,
  'context_sha256': '4d490cee65b404774b31ba315941f2e009a19bb5bb503a31c64ce2a18184ef78',
  'selection': [268057, 268058],
  'expected_source_text': 'δήπου',
  'evidence': 'The creator analogy locates δήπου between ἄλλον τινά and βελτίω γενέσθαι ποτὲ ἂν αὖθις '
              'δημιουργὸν τῶν ὅλων. The repeated current νομίζεις is outside the target and not repaired '
              'here.',
  'rendering': {},
  'surface_sha256': 'fcfb7b2b8ebe7e3273219bf59fc236206176c75996ac2bb745e98622395e101f'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.7',
  'segment_index': 3,
  'original_text': '[ἀνα]χῶντον',
  'start': 202,
  'end': 213,
  'original_row_sha256': '32311f098596d4c413392c20c57f52b44e095a15e699c6a5b37967af35fe1755',
  'inherited_record_sha256': '14b296121678f3457950c5e519e02226cfe71beefdb87ea4ac80df962b09335b',
  'context_start': 275830,
  'context_stop': 275845,
  'context_sha256': 'ab10e57d6ecdabe6120184010ff1bff6217882bd00fdb4378587a3b2e4a063dc',
  'selection': None,
  'expected_source_text': None,
  'evidence': 'At the corresponding imitation list, Henry moves directly from μιμῇ συκοφάντας μιμῇ to '
              'Θρασύμαχον τὸν οὐδέποτε ἐρυθριάσαντα. The Bekker bracketed insertion containing this target '
              'is absent. Do not reuse Θρασύμαχον or infer deletion from an empty counterpart.',
  'rendering': {},
  'held_reason': 'empty-position-counterpart',
  'surface_sha256': None},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0179.2',
  'segment_index': 0,
  'original_text': 'Ἀρξίλαος',
  'start': 0,
  'end': 8,
  'original_row_sha256': '4838e91af41c8123a2316407e0e75f41616465935ff3641264532443adf39a72',
  'inherited_record_sha256': 'df9f6267a06d8236b8cb772712a27e8e19c87ffdf81dd4055d8798e444c1e80c',
  'context_start': 280271,
  'context_stop': 280285,
  'context_sha256': '2cae5a23ea51e0a3e693c5a26764191764a1e60f8beb140cb8abe1630489152c',
  'selection': None,
  'expected_source_text': None,
  'evidence': 'The isolated OCR name has no positional anchor within its own row. Neighboring body text '
              'concerns the Titans returning to Acheron, and the inherited complete-page scan review found '
              'no secure counterpart. A contextual Acheron window is retained diagnostically, not asserted '
              'to locate the orphan name.',
  'rendering': {},
  'held_reason': 'unlocated-orphan',
  'surface_sha256': None},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0187.18',
  'segment_index': 1,
  'original_text': 'βασιλίαις',
  'start': 37,
  'end': 46,
  'original_row_sha256': 'c1b22ca24b4cf34b2d845e8aff411e99f4324c243c0ee9a97ef11a2a042084b6',
  'inherited_record_sha256': 'e2bf751166ca72fbeed4bf8f6c1ed774f46c277e4b58da61087002cd8f728720',
  'context_start': 285012,
  'context_stop': 285028,
  'context_sha256': '44949f8567949f54460b10136c166cc7400ec8c33503088314f4c1f7cb53ae82',
  'selection': [285019, 285020],
  'expected_source_text': 'βουνιάσιν',
  'evidence': 'The root description in the source has καυλὸν ἐκτρεφούσης παρόμοιον ταῖς καλουμέναις '
              'βουνιάσιν, followed by οἱ δὲ τῆς ὕλης τὴν ἁπαλὴν σιτοῦνται. These botanical flanks locate '
              'the source reading.',
  'rendering': {},
  'surface_sha256': '531438cbabde8361f4366eb890fd29311478ae8a4532b4d315946e4206a7bf2a'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.5',
  'segment_index': 0,
  'original_text': 'πέρποδῃ',
  'start': 0,
  'end': 7,
  'original_row_sha256': 'ac2831823836778f6bba8460978518507fde53949a4d2e81613478b4bf46fb02',
  'inherited_record_sha256': 'c65053bcc0e09826f6b135dd92ebe113ab6e2befd5a630cf538dd3616a2be16a',
  'context_start': 288945,
  'context_stop': 288961,
  'context_sha256': 'c25ab67012a383af87675fc83f067594a3fcca569bbc6b305ed245e349b74d25',
  'selection': None,
  'expected_source_text': None,
  'evidence': 'The corresponding source has πρὸς ἡμᾶς παραπέμπεσθαι τοῦ γένους τὴν δύναμιν. The preceding '
              'current row193.4 ends παρα-, so the current target is a cross-row suffix even though its '
              'inherited fragments list is empty. A full-word substitution here would duplicate the '
              'prefix. Preserve the target until a joint boundary review.',
  'rendering': {},
  'held_reason': 'source-word-boundary',
  'surface_sha256': None},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0195.3',
  'segment_index': 2,
  'original_text': 'νομίζω',
  'start': 33,
  'end': 39,
  'original_row_sha256': '6239235e97f797a194e7210901f566f28e262e07395246f74a1e852d5b4c1a33',
  'inherited_record_sha256': 'ed3ac633656e925e2a09437112d19b6a79a919ad51af447a9901547c3ae9b452',
  'context_start': 289925,
  'context_stop': 289941,
  'context_sha256': '4ea30277ae07519294d539fada2ff66d9cabaaab3e791c82c9f8a1e0fc3cf262',
  'selection': [289932, 289933],
  'expected_source_text': 'νομίζεσθαι',
  'evidence': 'The solar-light report has ὥστε ἀμφοῖν νομίζεσθαι παμμεγέθεις τὰς ὑπερβολάς. The following '
              'divided παμμε- in the current row identifies this source verb rather than another νομίζω '
              'occurrence.',
  'rendering': {},
  'surface_sha256': '4774fcdacb12bec608570ac1f2836c2c8e3358948545167cea249291d67566e9'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0195.12',
  'segment_index': 3,
  'original_text': 'ἀντεληφ[',
  'start': 39,
  'end': 47,
  'original_row_sha256': '38dfaaad203dace0df5a6b2429589cb663e7b6386dd7f7b77bf0aa62533a305e',
  'inherited_record_sha256': '7d7a5cca70183f9ce074ee1f164b580b4328faac80af5c286a4a931071c91895',
  'context_start': 289996,
  'context_stop': 290012,
  'context_sha256': '513c6f04a486503e6d517746691dfea66d47f5b725e33eddebaff81ece46fc37',
  'selection': [290003, 290004],
  'expected_source_text': 'ἀντείληπται',
  'evidence': 'The criticism of explanations has πράγματος δὲ οὐδενὸς ἀντείληπται, followed by βοήθειαν '
              'δυναμένου τοῖς εἰρημένοις παρασχεῖν. The complete source verb and inherited scan candidate '
              'do not contain the original trailing open bracket; retire only that explicitly recorded OCR '
              'wrapper.',
  'rendering': {'retire_suffix': '['},
  'surface_sha256': '4c03b505ec604f3d5a9a40110478d1755905b1b29936ee067d5d5cb29a76225c'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0199.5',
  'segment_index': 1,
  'original_text': 'ἀνάγκη λέγειν',
  'start': 33,
  'end': 46,
  'original_row_sha256': '2e3875fdde93d7ba25474f87b9b8c5f05516b45ff2fe3a9b438552be6ae1e33b',
  'inherited_record_sha256': 'cdf6781dfcf0bf3ecfecd5fe596d9e09299dc23da9212b2f4617c23278fabb35',
  'context_start': 292794,
  'context_stop': 292811,
  'context_sha256': '2e4a81c0a43d8e84d430aee7e4ff7d2abe4a5392dedffc790bf5264e0139d2c5',
  'selection': [292801, 292803],
  'expected_source_text': 'ἀνάγεσθαι λέγονται',
  'evidence': 'The philosophical and erotic distinction places ἀνάγεσθαι λέγονται after καὶ πῶς ἰσοτίμως '
              'and before φιλοσοφῆσαι μὲν ἀδόλως. Both source words constitute this one held expression.',
  'rendering': {},
  'surface_sha256': '3319e19e5a554ea58ff3965e544cb46255764fda626a8c471acc9d0cf328223d'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0202.23',
  'segment_index': 1,
  'original_text': 'ἐπεννοήντας',
  'start': 7,
  'end': 18,
  'original_row_sha256': '275e261d0d2c2cebe8561127553b54c3d47395ace89559aeab1e6058ba1357b4',
  'inherited_record_sha256': 'e66f426e15bfc8fef2dd200b6d885b48c14d6593225a4af6dae52f8ed8ed1b6b',
  'context_start': 294843,
  'context_stop': 294859,
  'context_sha256': '1603c501e3e35183c9bcf5fb029f819c21c05fa9edb2b75e6f3c463738bb0d31',
  'selection': [294850, 294851],
  'expected_source_text': 'ἐπιγνωσθέντας',
  'evidence': 'The seven noble youths are described as τὰ τῆς εὐσεβείας φρονεῖν καὶ κρατύνειν '
              'ἐπιγνωσθέντας, followed by ἀχθῆναι μὲν ἐπὶ Δεκίου. The Decius account identifies the exact '
              'participle.',
  'rendering': {},
  'surface_sha256': '7e147f4ec0e55261955f535dfc3ca6b3d45ff350dbcd5d31eab0bb2fb2f735d7'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0209.23',
  'segment_index': 1,
  'original_text': 'συλλέγον',
  'start': 7,
  'end': 15,
  'original_row_sha256': '977ba3180c39ddb79e1c850551295d310833a4fad0be1c02f63690e0b0b106ff',
  'inherited_record_sha256': '416c28a106c5870530100cde4ffb6bc10e0d703a0b781d74a76cb387938aae94',
  'context_start': 299226,
  'context_stop': 299242,
  'context_sha256': '3d23c98ac77e8811a819e89a953a952b6750a63ffb6244e4d005e64306078475',
  'selection': [299233, 299234],
  'expected_source_text': 'συλλέγονται',
  'evidence': 'The church-dedication account states ἐπίσκοποι συλλέγονται ἐνενήκοντα and immediately '
              'introduces Μάξιμος δὲ ὁ τῶν Ἱεροσολύμων ἔφορος. These flanks identify this gathering verb.',
  'rendering': {},
  'surface_sha256': '02d20d03ddeed0ee34c93ee7cfd02ee5955f80c0bb45cde125de1c2ada8183e2'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0209.28',
  'segment_index': 1,
  'original_text': 'ἀποκατασταθῇ',
  'start': 6,
  'end': 18,
  'original_row_sha256': 'ec94c80f7aebb06ec730d47970a2da8b4a42ca7ce8df1cec3d77296c0059d1b5',
  'inherited_record_sha256': '44c61f77f4a0702c11f4d2be7ec48d0b3143acd979793334112a8ab1bd55bfbd',
  'context_start': 299266,
  'context_stop': 299282,
  'context_sha256': '4bdc631ef25b19191091f19fb6ad90b0d52bf3e45429be0e79a36595d64f8851',
  'selection': [299273, 299274],
  'expected_source_text': 'ἀποσκευάσασθαι',
  'evidence': 'The Eusebius party first seeks to remove Athanasius: πρὸ τῶν ἄλλων ἀποσκευάσασθαι '
              'Ἀθανάσιον, followed by Ἐπάγουσιν οὖν πρώτην αὐτῷ αἰτίαν. The name and first accusation '
              'establish this exact source infinitive.',
  'rendering': {},
  'surface_sha256': 'f49992f687bbc74b8077a3ee0b95389477d86bbcf36be2ceeed6f031d9b4d59e'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0210.2',
  'segment_index': 17,
  'original_text': 'παραγγέλλει',
  'start': 1799,
  'end': 1810,
  'original_row_sha256': '7b6774818e27b32f166c6a4646e71e5c4acc871d6b6b00a0f631aef6ab04bb3e',
  'inherited_record_sha256': '3ff5e25111d043588e0ddc18d3ee9265fff75c76315b70dc038fe1790ada79bb',
  'context_start': 299993,
  'context_stop': 300009,
  'context_sha256': 'f2df3c4ee4cad1b5359a981d47cdba7e264ee0359ce6ea4825b3aeb0875ff321',
  'selection': [300000, 300001],
  'expected_source_text': 'παραγενέσθαι',
  'evidence': 'The summons for eastern bishops ends τὴν τῆς πίστεως ἔγγραφον ἔκθεσιν παραγενέσθαι. The '
              'next sentence sends four named men. This fixes παραγενέσθαι independently of the next '
              'disputed verb.',
  'rendering': {},
  'surface_sha256': 'bc7154f6cff4cd8385b4fd13069103585094014c98e617d2d1e147afb625fd70'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0210.2',
  'segment_index': 19,
  'original_text': 'ἐκπέμπον-ται',
  'start': 1812,
  'end': 1824,
  'original_row_sha256': '7b6774818e27b32f166c6a4646e71e5c4acc871d6b6b00a0f631aef6ab04bb3e',
  'inherited_record_sha256': 'f01a76ca7d7a395f64193d6850d692293cf4b6ff8642dc2ff6fea78cc0201f78',
  'context_start': 299994,
  'context_stop': 300010,
  'context_sha256': 'ffaf50f8ea08cc903b06327a63a49e066b69aa226668b5f978a338d5b5cee5e4',
  'selection': [300001, 300002],
  'expected_source_text': 'Ἐκπέμπονται',
  'evidence': 'The next source sentence begins Ἐκπέμπονται δὴ τέσσαρες and lists Narcissus, Theodore, '
              'Maris, and Maras. The complete word reflows its current internal line division without '
              'borrowing the preceding target.',
  'rendering': {},
  'surface_sha256': '9e345f8ded739230486efb550fce60330442d901884c5eddcfb19b427fd6e777'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0211.48',
  'segment_index': 13,
  'original_text': 'ὑπεροφζεται',
  'start': 794,
  'end': 805,
  'original_row_sha256': 'c3e99c2ccced4047a830516a748955a0e97acfcdf737266256ec42097f06ac9d',
  'inherited_record_sha256': 'e442e628bdc3b656cd5f38ea2c2aad47af75c284e3c9f0c2031d64538b89e94e',
  'context_start': 300492,
  'context_stop': 300508,
  'context_sha256': 'ec09e8f4c1eee6931b82d34947624cc4b72d11f80b7e587d0f3c7e2bacb72b89',
  'selection': [300499, 300500],
  'expected_source_text': 'ὑπερορίζεται',
  'evidence': 'Agelius, bishop of the Novatians, is said to profess the consubstantial doctrine and then '
              'ὑπερορίζεται. The source continues Καὶ ἦν ἀδιήγητον τὸ κακόν. The named bishop and '
              'doctrinal clause locate this verb.',
  'rendering': {},
  'surface_sha256': '1833379afb10b337ddd1d6ec63952e51cf4f6d09fc12fe3bd75199c324cd9ad7'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0212.17',
  'segment_index': 1,
  'original_text': 'κατατίθεται',
  'start': 14,
  'end': 25,
  'original_row_sha256': '2433a68f915e02651bebcb596f1a3fb9ce98a3cb4ae4c52dde43ad8e760d0d2a',
  'inherited_record_sha256': 'e7f4bdf0361900a09cd21209da5a144c93b419a117f2401df5b1e274cad2a1a8',
  'context_start': 301142,
  'context_stop': 301158,
  'context_sha256': '86e06f13f653e25d040fb741a1a0b931a95074b50e348274676109bfc5c72c74',
  'selection': [301149, 301150],
  'expected_source_text': 'κατατίθενται',
  'evidence': 'The burial account ends τῷ ἁγιοδόχῳ τάφῳ κατατίθενται, after the bishops, clergy, and '
              'emperor are present. The next source sentence comments on the history itself; no other '
              'burial verb is selected.',
  'rendering': {},
  'surface_sha256': 'f60bd763f00884ffe147d8ae14e6ff1180811be65bd9443298340f6400095436'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0212.23',
  'segment_index': 1,
  'original_text': '[τῷ ἐν ἁγίοις πατρὸς ἡμῶν ἐπισκόπου',
  'start': 8,
  'end': 43,
  'original_row_sha256': 'df82dc800527b01f3bb80932aba2656b597050e9e3d90a37722f9085fed15816',
  'inherited_record_sha256': 'e9f7af28641865416e77d87f7c21d6368f7eb7ac72a3257395d1a40b19d0e2ad',
  'context_start': 301179,
  'context_stop': 301200,
  'context_sha256': 'c1c8ed8f165b7dfb09613265e7e0a6511c85a5649bd2b2e286ba48b1b2fbd5a8',
  'selection': [301186, 301192],
  'expected_source_text': 'τοῦ ἐν ἁγίοις πατρὸς ἡμῶν ἐπισκόπου',
  'evidence': 'The Athanasius life title reads Βίος ἤτοι ἄθλησις τοῦ ἐν ἁγίοις πατρὸς ἡμῶν ἐπισκόπου '
              'Ἀλεξανδρείας. Select only the six complete title words covered by this target; keep its '
              'existing external opening bracket.',
  'rendering': {},
  'surface_sha256': '113d81726f95c21d3cfc2c09b6ce4e4b0446bf081e71e282b26549ff04dc0f5b'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0214.3',
  'segment_index': 1,
  'original_text': 'Ἰχέραν',
  'start': 132,
  'end': 138,
  'original_row_sha256': 'c62f331357826ee48eb61ff36091a68e8b7d80b2a5cb8635f0f7e4e811cb1178',
  'inherited_record_sha256': '7aaf8fea9c57918431edbce7dae4ec3a85b202f48125dee95ec8f3a2b802ed83',
  'context_start': 302340,
  'context_stop': 302356,
  'context_sha256': '67207ca62fcebd2581506319c9e822d780715181449fe035bba0a9a205c2aa37',
  'selection': [302347, 302348],
  'expected_source_text': 'Ἰσχύραν',
  'evidence': 'The inquiry before the emperor concerns τὰ δὲ περὶ Ἰσχύραν and proceeds καὶ ἐτάσαι καὶ '
              'σαφῶς εἰδέναι ὑπ Ἀθανασίου τετολμῆσθαι. The related source wording differs outside this '
              'exact name and remains unchanged.',
  'rendering': {},
  'surface_sha256': 'cdf6094447afa120a6351571743bd81ee310426fe9d7edd9a36efcafb2b11b36'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.5',
  'segment_index': 1,
  'original_text': 'ἀπαινεῖται',
  'start': 5,
  'end': 15,
  'original_row_sha256': '6de890dfd928540f717928990241e4b0687c1a95d04a98a771106bd988dbb3cd',
  'inherited_record_sha256': '847fe8034ede2dca3b8a22326b5d6ee5bed4f3ffc5bee860eb2b8fcbca46f34e',
  'context_start': 302606,
  'context_stop': 302622,
  'context_sha256': 'a579f0377b5ae51d6d347b79df029a76cfb0c98aaf608ae1daaebf8f509c3acc',
  'selection': [302613, 302614],
  'expected_source_text': 'ἀπελαύνεται',
  'evidence': 'The death of Arius is described after the falling of his entrails: τῆς ζωῆς ἀπελαύνεται. '
              'The next sentence turns to the renewed attack on Athanasius, fixing this particular '
              'occurrence.',
  'rendering': {},
  'surface_sha256': '10a9e2f0d949c12b88391cc1f53502a9b72e33e2e0cf13584bf8d30c65a72a4d'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
  'segment_index': 0,
  'original_text': 'δροῖζε?',
  'start': 0,
  'end': 7,
  'original_row_sha256': '34279e6fbf9e6edec2b4bbf0654ba21e7ef6d14c30415fcba156882c548cf221',
  'inherited_record_sha256': '7233a1f2e434c5a6cb49104f547ec6952f2140ca3fa70a76b2d8794f827946ad',
  'context_start': 302744,
  'context_stop': 302757,
  'context_sha256': '97d81a0b375d3276a12588728da99f31b0d2e4255af1c65a4e4d00888de5bc4f',
  'selection': None,
  'expected_source_text': None,
  'evidence': 'The Tyre council clause has βασιλέως προστάττοντος συναθροίζεται καὶ προχειρίζεται. The '
              'preceding current row215.25 ends συνα-, making this target only the following divided-word '
              'suffix. Do not duplicate the prefix by inserting the complete source word; retain pending a '
              'joint boundary review.',
  'rendering': {},
  'held_reason': 'source-word-boundary',
  'surface_sha256': None},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
  'segment_index': 2,
  'original_text': 'προχειρίζε?',
  'start': 13,
  'end': 24,
  'original_row_sha256': '34279e6fbf9e6edec2b4bbf0654ba21e7ef6d14c30415fcba156882c548cf221',
  'inherited_record_sha256': 'ef83edb26ac9700ed34aa7a6452fa361991914137b9963a6a916a60aac5fb79c',
  'context_start': 302745,
  'context_stop': 302761,
  'context_sha256': '5d465a4feb778e657612bd4e411c7b32e5832833c6227b5923b2b55be4086221',
  'selection': [302752, 302753],
  'expected_source_text': 'προχειρίζεται',
  'evidence': 'The Tyre council appoints ἄνδρα συνέστιον καὶ ὁμόφρονα Ἀρχέλαον; the exact preceding source '
              'is καὶ προχειρίζεται τὸ βασιλικὸν βούλημα. The ASCII question mark is a recorded '
              'uncertainty wrapper, absent from this source statement, and only that wrapper is retired.',
  'rendering': {'retire_suffix': '?'},
  'surface_sha256': 'e86522ea42a48c48d7cc0c50c9f008cf34bf3fbe079bd339eb7dbeb52ce94616'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0217.6',
  'segment_index': 1,
  'original_text': 'ἀναθεματίσῃ',
  'start': 5,
  'end': 16,
  'original_row_sha256': '129c420276ce5a25e01d2c9870bafb3cfed7b2de8d89872c7b8bbf0c61c21329',
  'inherited_record_sha256': '3d364ce401116c511ac124336790ffbaa5f3ed24188e4877efdbb25c69ebf1c4',
  'context_start': 303895,
  'context_stop': 303911,
  'context_sha256': 'dc72dd16db8b99e201b97b3f5045b2001acb1cf71329be3191a14ac2595b98a8',
  'selection': [303902, 303903],
  'expected_source_text': 'ἀναθεματίζουσι',
  'evidence': 'The assembly openly anathematizes the consubstantial doctrine: καὶ γλώσσης θρασύτητι '
              'ἀναθεματίζουσι, followed by καὶ τὸ ἀνόμοιον δογματίζουσι. The two neighboring held verbs '
              'select distinct source tokens.',
  'rendering': {},
  'surface_sha256': '9769494949232ee34399de554d80c152a9aeb8fc5fbd47cb266014db698d6f10'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0217.6',
  'segment_index': 3,
  'original_text': 'δογματίσῃ',
  'start': 34,
  'end': 43,
  'original_row_sha256': '129c420276ce5a25e01d2c9870bafb3cfed7b2de8d89872c7b8bbf0c61c21329',
  'inherited_record_sha256': '788d67f372b7cfd71850c3c154cf7ceba9142f73e5211f2b5f061c97895cebb0',
  'context_start': 303899,
  'context_stop': 303915,
  'context_sha256': '1e4383cccd31fa3dc138f9c6e97b53cb328b1fbf48eb840f432203bc4f694029',
  'selection': [303906, 303907],
  'expected_source_text': 'δογματίζουσι',
  'evidence': 'The same assembly clause reads καὶ τὸ ἀνόμοιον δογματίζουσι, before καὶ τὰ δυσσεβῆ '
              'ψηφίσματα πανταχοῦ διαπέμπονται. This is distinct from its preceding anathema verb.',
  'rendering': {},
  'surface_sha256': '85c0b230c6495c0dacbc1573f671035a0eee3c63058a60f211ef0eace25021ca'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0217.14',
  'segment_index': 1,
  'original_text': 'διαπέμψῃ',
  'start': 16,
  'end': 24,
  'original_row_sha256': '6a81aa19578d56dd851cbad006a7e8a16fe715d46fa706430a1a17cd12abf5de',
  'inherited_record_sha256': 'adeb9923272f75fd88e7e3f7eb921a2ca136507fc6a51ec38c8d10b7c1ffd469',
  'context_start': 303952,
  'context_stop': 303968,
  'context_sha256': 'b1d1824e09272d71891de8c6bcc526d749998019eea8e4786f7b57f6c796c109',
  'selection': [303959, 303960],
  'expected_source_text': 'διαπέμπονται',
  'evidence': 'The Sardica assembly sends letters: γράμματα πρὸς πάσας τὰς τῆς οἰκουμένης ἐκκλησίας '
              'διαπέμπονται. The next sentence introduces the western emperor, so the earlier sending of '
              'decrees is not reused.',
  'rendering': {},
  'surface_sha256': '1685ddf6f45cd81dfcd3349120c28861c40aa94714991fad9dd3f229d3498c4f'}]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _tokens(html_raw):
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The manually reviewed comparison source changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    tokens = edition.tokenize(parser.units)
    for index, token in enumerate(tokens):
        ref = token['refs'][-1]
        unit = parser.units[ref['unit_index']]['text']
        if ref['end'] < len(unit) and unit[ref['end']] in edition.assess.APOSTROPHES:
            token['text'] += unit[ref['end']]
            ref['end'] += 1
        tokens[index] = {'text': token['text'], 'refs': token['refs'], 'source_index': index}
    return tokens


def _record(spec, context):
    if (not isinstance(context, list) or _digest(context) != spec['context_sha256']
            or [t.get('source_index') for t in context] !=
                list(range(spec['context_start'], spec['context_stop']))):
        raise ValueError('The exact decoded manual source context changed')
    readings = []
    if spec['selection'] is not None:
        start, end = spec['selection']
        selected = context[start - spec['context_start']:end - spec['context_start']]
        if (not spec['context_start'] <= start < end <= spec['context_stop']
                or ' '.join(t['text'] for t in selected) != spec['expected_source_text']):
            raise ValueError('The reviewed source interval no longer selects its exact Greek words')
        readings.append({'source_id': 'tlg-photius-henry', 'role': 'alternative',
            'text': spec['expected_source_text'],
            'tokens': [{'text': t['text'], 'refs': deepcopy(t['refs']),
                        'source_index': t['source_index']} for t in selected],
            'refs': [deepcopy(ref) for t in selected for ref in t['refs']],
            'location_basis': 'Individually reviewed source sentence and exact decoded token references.'})
    return {'kind': 'manually-located-editorial-counterpart', 'reviewed_at': REVIEWED_AT,
        'original_text': spec['original_text'], 'original_row_sha256': spec['original_row_sha256'],
        'inherited_record_sha256': spec['inherited_record_sha256'],
        'reviewed_extent': {'start': spec['start'], 'end': spec['end']},
        'evidence': spec['evidence'], 'readings': readings,
        'rendering': deepcopy(spec['rendering']), 'held_reason': spec.get('held_reason'),
        'surface_sha256': spec['surface_sha256'],
        'qualification': 'An editorial source preference, not independent resolution of the Bekker ink. '
            'Original scan observations, contrary readings, and independent exclusions remain authoritative.',
        'source_context': {'source_id': 'tlg-photius-henry', 'sha256': SOURCE_SHA256,
            'tokens': deepcopy(context), 'tokens_sha256': spec['context_sha256'],
            'qualification': 'An exact bounded context for this occurrence; a held context does not assert a counterpart.'}}


def validate_record(key, record):
    """Reconstruct all fields from authored hashes and archived bounded context."""
    specs = {(s['locus'], s['segment_index']): s for s in SPECS}
    if key not in specs or not isinstance(record, dict):
        raise ValueError('Unknown manually reviewed editorial occurrence')
    expected = _record(specs[key], record.get('source_context', {}).get('tokens'))
    if expected != record:
        raise ValueError('The recorded manual decision differs from its exact source authority')
    return deepcopy(expected)


def review_remaining(html_raw, scopes):
    """Check all 32 preimages and propose only the 27 located source intervals.

    The five empty readings are explicit holds. Callers must not reinterpret
    their diagnostic contexts as deletion, omitted words, or role permission.
    This function never mutates the supplied rows, masks, or source records.
    """
    tokens = _tokens(html_raw)
    result = {}
    for spec in SPECS:
        key = spec['locus'], spec['segment_index']
        scope = scopes.get(key)
        if (scope is None or _digest(scope['row']) != spec['original_row_sha256']
                or _digest(scope['record']) != spec['inherited_record_sha256']
                or scope['row']['locus'] != spec['locus']
                or scope['record']['segment_index'] != spec['segment_index']
                or (scope['start'], scope['end']) != (spec['start'], spec['end'])
                or scope['row']['text'][scope['start']:scope['end']] != spec['original_text']):
            raise ValueError('A manual source decision lost its exact baseline occurrence')
        result[key] = _record(spec, tokens[spec['context_start']:spec['context_stop']])
    return result
