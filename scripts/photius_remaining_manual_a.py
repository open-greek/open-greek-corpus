"""Individually located editorial counterparts for 32 held early passages.

Every selection is pinned to the supplied Henry source and to one immutable
held occurrence. Diagnostic word fragments and a punctuation-only mark remain
held. This source authority does not claim to resolve Bekker's printed glyphs.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-21T23:14:05.501170Z'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {}
SPECS = [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0018.19',
  'segment_index': 1,
  'start': 38,
  'end': 49,
  'original_text': 'ὅτως κ πρὸς',
  'row_sha256': '39c828252c178d74371cbe05fb46b8702b0d896e610c5166b7ddb18038bfb989',
  'inherited_record_sha256': 'a30bbaeb3247edbc2a52aa417cb3a5ad9e633db0520feba3a9400f95b28bc857',
  'selection': (7268, 7271, 'Οὕτως οὐ πρὸς'),
  'context_sha256': '581d7ba4bbee669c34dfda47651347e63bff34066ea2a9a0e691924aca99c4b0',
  'held_reason': None,
  'evidence': 'The preceding source paragraph ends αὐτὰ διομολογεῖ τὰ πράγματα σῴζεσθαι; the next '
              'starts Οὕτως οὐ πρὸς ἀλλήλους. These two sentence boundaries locate the connective '
              'independently of the damaged target. Henry has Οὕτως, unlike the earlier tentative '
              'Bekker ὅπως.',
  'surface_sha256': '00cef95bb1498819f135dbc8a62b766bfca8548dc711fb6bbbaad93c5450ac5b',
  'source_indices': [179253, 179254, 179255]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0018.36',
  'segment_index': 3,
  'start': 46,
  'end': 47,
  'original_text': '“',
  'row_sha256': '16c572d44bd0d19936da96c4e31846c9c856ed177ae2dce8e8ae53d4bbbdd683',
  'inherited_record_sha256': 'f816dfafe342edcfa25677b9a1bea5aee85bc9e1d8dc4d59f6e7e8a0d7db45fd',
  'selection': (7273, 7276, 'συγκεφαλαιωθέντος'),
  'context_sha256': 'a4186e9acf466ca81516d8315b506b48132e34a477dc9d346e5dd8e5d8b951a2',
  'held_reason': 'punctuation-only',
  'evidence': 'The count of bishops, the following συγκεφαλαιωθέντος, and the Amphilochius '
              'exception locate the high mark. Henry has no lexical token corresponding to it. '
              'Absence in Henry does not prove whether Bekker printed a quotation mark or an '
              'impression artifact. This record does not authorize deletion.',
  'surface_sha256': None,
  'source_indices': []},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0019.10',
  'segment_index': 1,
  'start': 23,
  'end': 39,
  'original_text': 'ὃν ἂν μὲν ἕως τῷ',
  'row_sha256': '6e0186afea7913d0e7fdcdcfa2208143df27ac190fb978c11cad507dd40b7844',
  'inherited_record_sha256': '83029a0ecd2ad43203fff99698d8e79bd7859e20ae2c8efd2fc078443ae90082',
  'selection': (7301, 7304, 'οὐκ ἂν μὲν ἔξω τοῦ'),
  'context_sha256': '29911969008276daec74b86f5d643b431cd1f27c940d7b5fdfa27b96bd05c1c4',
  'held_reason': None,
  'evidence': 'The discussion of ignorance attributed to Christ places the clause after ἧς ἐστιν '
              'αὐτὸς κεφαλή and before εἰκότος περιενεχθείη. Henry has οὐκ ἂν μὲν ἔξω τοῦ; retain '
              'the different verified neighboring Bekker wording εἰκότως and the old tentative '
              'scan alternatives.',
  'surface_sha256': 'e4782af012243c0ac319856ed9d6cd97c008bd585d9d6f6da1e42e849b618d15',
  'source_indices': [180185, 180186, 180187, 180188, 180189]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0020.4',
  'segment_index': 1,
  'start': 15,
  'end': 21,
  'original_text': 'μωρίας',
  'row_sha256': '37bc493360fbbf05817d3ab3aa7e2ac6c4f59456e7231c9eb87ac5a002211d06',
  'inherited_record_sha256': '688c7af9ed3a189dcdc9e2aee653a008e5f7153601d8caeb4ccc54321d9c66c4',
  'selection': (7325, 7328, 'Μυρίαις'),
  'context_sha256': '425ad49169c718bb0a1a0e016891a5931ede41b41befc9a99a4fabd24537a2ce',
  'held_reason': None,
  'evidence': 'The account of Dositheus turns from appropriating prophecy and divinity to '
              'corrupting the Mosaic Octateuch. Immediately before δὲ καὶ ποικίλαις ἄλλαις '
              'νοθείαις Henry has Μυρίαις. Its dative plural ending differs from the tentative '
              'Bekker endings; this is an editorial choice.',
  'surface_sha256': '88657f75a7d3a5fc7703213b312b90e1fa99a16c4e7e47bda1cab4383631a497',
  'source_indices': [180793]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0020.5',
  'segment_index': 1,
  'start': 30,
  'end': 44,
  'original_text': 'κατακωδηλεύσας',
  'row_sha256': 'b3eee1638a00d0bc4d724898544107016f0eec6484cef9e8b59508355c8e4466',
  'inherited_record_sha256': '47ddf53e4bb84e2cf002924230abeea22638b9c714b03b8c00651fe1fd6c1f2c',
  'selection': (7325, 7328, 'κατακιβδηλεύσας'),
  'context_sha256': '425ad49169c718bb0a1a0e016891a5931ede41b41befc9a99a4fabd24537a2ce',
  'held_reason': None,
  'evidence': 'The same Dositheus sentence uniquely places this participle after τὴν Μωσαϊκὴν '
              'Ὀκτάτευχον and before καὶ ἕτερά τινα συγγράμματα. This location is independent of '
              'the unresolved middle ligature.',
  'surface_sha256': '66fa4449adf009e9f7802e9614b5c54e4193f58eb3f23467a6f495e76a55040b',
  'source_indices': [180802]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0032.1',
  'segment_index': 1,
  'start': 22,
  'end': 32,
  'original_text': 'χρησίματος',
  'row_sha256': '9a5553dbde86f52645430d1c34e54241597ac604cf3c3fc68bc9332bf01c0cf1',
  'inherited_record_sha256': '5057ea0860834266821b223988f5afb16e074995b2b7442367d2d5969e66191e',
  'selection': (7610, 7613, 'κηρύγματος'),
  'context_sha256': '08bac119df20f6e681854244fa2a67fd1c7671ae3947fd5a4abbd65865d541ce',
  'held_reason': None,
  'evidence': 'At the continuation of the discussion of the laws, Henry reads διὰ τοῦ κηρύγματος '
              'πρὸς ὑπακοὴν τεθεὶς καὶ ἄφεσιν ἁμαρτημάτων. The immediately following phrase and '
              'preceding νόμων locate the noun. Henry also differs from the already verified '
              'preceding article τὸ; only the exact held noun is selected.',
  'surface_sha256': 'aeaa345277b658708fd91ca00da31107fdc34b58a6be33537476b96f66bf8ec9',
  'source_indices': [188450]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0033.20',
  'segment_index': 0,
  'start': 0,
  'end': 11,
  'original_text': 'ἀπαράθεντες',
  'row_sha256': '01f3ad6d46a0b10f5c28afdfe5a03a4f074a7552c43938657636f1928b0dedc0',
  'inherited_record_sha256': '1d41d1b4f192fd8fbaca4a2a5346109e11f2f5a13e7e690202d7090aea52c021',
  'selection': (7648, 7651, 'ἁρπασθέντες'),
  'context_sha256': '46d68d03387fc3069b52170c2043e139a3453e20d2a1a9447d39b79826292ef3',
  'held_reason': None,
  'evidence': 'The resurrection passage places this participle after εἰς ἀπάντησιν ἅμα αὐτοῖς and '
              'before τοῦ Κυρίου ἐνδόξως ἑορτάσωμεν. The edition is preferred for the unresolved '
              'sigma-theta group; the current verified τῷ κυρίῳ remains untouched.',
  'surface_sha256': 'cf4155d533236f723af56d2f41da08116c8ecb792bf2d2f7cf24d4cb3528a166',
  'source_indices': [189575]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0033.22',
  'segment_index': 1,
  'start': 17,
  'end': 45,
  'original_text': 'ὅκτι πεινησόμεθα ἢ λειψόμεθα',
  'row_sha256': '18f270b327055a1f8cb3aa813e01da3da7f33dd4796b69dcbf2e78049756463b',
  'inherited_record_sha256': 'b6ea7ab46bb197ab6c01e87e769eb08b7e4b6bd346700e163afecb15c252db23',
  'selection': (7649, 7652, 'οὐκέτι τεθνηξομένας ἢ λυθησομένας'),
  'context_sha256': '0eaeb41b1b4a29bbec3d8a8d864fee584cdcfd5a69567534b25f7d80f7087dee',
  'held_reason': None,
  'evidence': 'The same resurrection paragraph places this phrase after αἰωνίους ἡμῶν τὰς σκηνάς '
              'and before ἀπειλήφαμεν. Henry supplies the complete feminine plural forms and '
              'λυθησομένας, differing from the tentative scan transcription. No familiar quotation '
              'is used to reconstruct the scan.',
  'surface_sha256': 'a99fa0027dda55ed67f4c34387c0aa5cb18f9bb72a14d637e26aade3b37eea74',
  'source_indices': [189592, 189593, 189594, 189595]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.17',
  'segment_index': 0,
  'start': 0,
  'end': 5,
  'original_text': 'δῶσιν',
  'row_sha256': 'd3d26fe0b1ae8c1573fcc5d49d304a60ce615e11c57c63e2f2fa172d45f90f2b',
  'inherited_record_sha256': '93f5490730eeab91045135218a89b6ab8c8b7f285d844064be77488e219e02d6',
  'selection': (7792, 7795, 'συναΐδιον'),
  'context_sha256': 'd87bd2c04a20a1236518ae7940b6e1a3a4246de438251fd10e6f82b80ead7bd3',
  'held_reason': 'cross-row-word',
  'evidence': 'The sentence has οὔτε συναΐ-διον δι’ αὐτὸ τοῦτο. The retained previous row already '
              'ends συναΐ-, while this target is only the continuation. A complete Henry word '
              'would duplicate that prefix. Keep the source word as diagnostic evidence and '
              'require a joint boundary review.',
  'surface_sha256': None,
  'source_indices': []},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.38',
  'segment_index': 1,
  'start': 16,
  'end': 41,
  'original_text': 'συγχωρήντες ἀρχὴν ἐχηνίαν',
  'row_sha256': 'd516840a2c86d3d6ffd8be9aedfec2ea17cdb75e90fd7186cc9fc544b84214c1',
  'inherited_record_sha256': '18a635bc2cf9373298b82b8e637d08be1622d126ca0ab2b6694d0276c1f87bf1',
  'selection': (7805, 7808, 'συγχωροῦντες ἀρχὴν ἐσχηκυῖαν'),
  'context_sha256': 'a04cf06a7034ca475df6f65333f8fda06eb08b50a2fee20e6b52c8efc89c4924',
  'held_reason': None,
  'evidence': 'The argument concerning matter puts the phrase after τῆς μεταμορφώσεως τὴν ὕλην and '
              'before ἀναγκασθῶσι τῷ λόγῳ. These argument boundaries select the three Henry words '
              'without settling the Bekker σχ/χ glyph from grammar.',
  'surface_sha256': '9baaef1e60037e1245eed259bedc1bdd8f25aae0554e67e87cff517b009862c0',
  'source_indices': [192631, 192632, 192633]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0041.1',
  'segment_index': 4,
  'start': 501,
  'end': 512,
  'original_text': 'ἕτε γένοιτο',
  'row_sha256': 'b9df2186f721558d3868558fb11e789cc905971aceaced4e4739243891381286',
  'inherited_record_sha256': '9db5610aba32654574ccd566c0779c54e56e0bf26673c7884223d84987160bdf',
  'selection': (7877, 7880, 'γίνεται'),
  'boundaries': {'left': 'εἰ δὲ αὐτός ἐστι ταῦτα ὅτε', 'right': 'τὴν σύστασιν ἔχει'},
  'context_sha256': 'eb8b5f01897b6beb04af2550c550924d8401dd4fb84c0b9cfc713b283377a563',
  'held_reason': None,
  'evidence': 'The argument says εἰ δὲ αὐτός ἐστι ταῦτα, ὅτε γίνεται, τὴν σύστασιν ἔχει. The '
              'retained row already has a verified ὅτε immediately before the damaged ἕτε γένοιτο. '
              'Select only γίνεται so the preceding conjunction is not duplicated. The different '
              'verified following noun remains unchanged.',
  'surface_sha256': '8919d1144947282a848eaaeee0428923f367d3053d264248fabb6baef3137943',
  'source_indices': [194460]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.1',
  'segment_index': 1,
  'start': 80,
  'end': 117,
  'original_text': 'εἴρη γ’ αἱ φρένες εἰσάτι λύγιν χὸ νὺς',
  'row_sha256': 'd3923b0f08e8948de4893f7e745e9be8e9a30bea852a059e8ccf5f5c1f46a27c',
  'inherited_record_sha256': '2d38f7487ead74704ffa52dfcc0c978b9e48b3232c6e7c3bd6d784fef1702eeb',
  'selection': (7960, 7963, 'Στήθη γὰρ αἱ φρένες εἰκότι λόγῳ'),
  'context_sha256': '4955b7e3b75023d73bb2bdd236d742b0ee44f082e84747309a18235083cf2d0c',
  'held_reason': None,
  'evidence': 'The Jeremiah interpretation identifies the breasts with the understanding: Στήθη '
              'γὰρ αἱ φρένες εἰκότι λόγῳ καὶ ὁ νοῦς ἡμῶν εἶναι νομίζεται. Select only the phrase '
              'preceding καὶ ὁ νοῦς, which is already verified in the retained row. The old '
              'candidate had incorrectly included that following phrase.',
  'surface_sha256': '75bcbdab12ef2a78adb36b2ed37269453b9596f8b42f5a3459aca0789ec668d3',
  'source_indices': [196430, 196431, 196432, 196433, 196434, 196435]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.17',
  'segment_index': 1,
  'start': 23,
  'end': 29,
  'original_text': 'εουχεν',
  'row_sha256': '78c6dcb5c8ddad84e043bec3ae09da7e6e79c4bdfddbca7d7d77bfeecf05d684',
  'inherited_record_sha256': 'facb77bea9b8501a40695a1ae0d06feeed806a02bf68bd5c8fce720667c574c1',
  'selection': (7974, 7977, 'στοιχείου'),
  'context_sha256': '2e98b5cfd76cced7771039db3aad0d924afe6edf332367daab8181f7c907fd84',
  'held_reason': None,
  'evidence': 'The ten-virgins interpretation explains the shared number with διὰ τὴν ἔμφασιν τοῦ '
              'ἰῶτα στοιχείου, then begins Ἐστείλαντο μὲν γὰρ παραπλησίως. These two clauses '
              'locate the final noun despite substantial contrary verified wording in Bekker and '
              'the tentative scan ἐσθῆτα. Only this exact held final noun is preferred from Henry.',
  'surface_sha256': 'b80db931766c0584024ba50888fa65754fc10263157ca0792ec2e303c15826a6',
  'source_indices': [196860]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.22',
  'segment_index': 1,
  'start': 35,
  'end': 44,
  'original_text': 'διαφενται',
  'row_sha256': 'd2f8b137c3872231795384a97fd20f7a62ee38ee902aab19e59cddb465d2186f',
  'inherited_record_sha256': '2ee4c1c0e2e6447e357c427c8ef1f1ed6310ef4c753fa407ff1a9b3559cd3cc3',
  'selection': (7975, 7978, 'διαιροῦνται'),
  'context_sha256': '0eecc2b8d89f7c646a4e848bdc57623054b6fb57fe7c2ec230c71753cd961652',
  'held_reason': None,
  'evidence': 'After the lamps of the two groups, Henry says Διὸ δὴ καὶ ἰσάριθμοι πρὸς εʹ '
              'διαιροῦνται, ἐπειδήπερ τὰς πέντε αἰσθήσεις. The numeral and explanation of the five '
              'senses locate this verb; different preceding verified wording is preserved.',
  'surface_sha256': '2bdc6da68136b7e522dd200770ed7021b6b7532195bd8ba746060741988bf05c',
  'source_indices': [196898]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.26',
  'segment_index': 1,
  'start': 37,
  'end': 49,
  'original_text': 'μελλαν εξφο-',
  'row_sha256': '1389479ffa099a6e8a997fff24b69b2756cff14c342ab9dd2d2a7a510004be34',
  'inherited_record_sha256': 'e8e5be2a6c9c45850e5b292b867da72746731c616dbfdce0dab33ee65896e106',
  'selection': (7976, 7979, 'μᾶλλον εὐφόρεσαν'),
  'context_sha256': 'd3931164e0c7f6a6e412445b3863e1953b90c86dc537a49f0d9e57b29ed08ef9',
  'held_reason': 'cross-row-word',
  'evidence': 'Henry has δικαιοσύνης μᾶλλον εὐφό-ρεσαν παραπτώμασιν. The exact held target ends in '
              'a printed partial word, and the next retained row begins ρεσαν. Replacing it with '
              'the complete Henry word would duplicate that continuation. Preserve the complete '
              'diagnostic reading and require a joint boundary review.',
  'surface_sha256': None,
  'source_indices': []},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0046.4',
  'segment_index': 1,
  'start': 275,
  'end': 288,
  'original_text': '[καὶ ἄρχοντα]',
  'row_sha256': '85706f5485cf63ca69587a640d69f2a0925baf67b13290fad6e01afd824ca603',
  'inherited_record_sha256': 'b716c928d35fc48af31911bc93b1c0b40a1041534a48d8e2176ddb40cf4fe483',
  'selection': (8012, 8016, 'καὶ οὐ γέγονας'),
  'context_sha256': 'b148837429212cd480c0a33d37b5db8faa1d70911f71c3cfec68702f16ad1ca9',
  'held_reason': None,
  'evidence': 'The Sonship paragraph places this phrase after Εἶ γὰρ Υἱὸς αὐτῷ ἔφη and before '
              'ἐμφαίνων μήτε πρόσφατον. Henry has unbracketed καὶ οὐ γέγονας where the exact '
              'retained uncertainty is [καὶ ἄρχοντα] and the earlier scan observation [καὶ '
              'ἄχρονος]. Prefer the supplied edition and retire only the two bracket wrappers '
              'wholly inside this held span; all contrary words and the different neighboring '
              'participle remain archived.',
  'rendering': {'retire_prefix': '[', 'retire_suffix': ']'},
  'surface_sha256': 'a9443778df57d3e875bb0da2a62923b755ab5b1db24bee2cd983f20fef0d9b60',
  'source_indices': [197969, 197970, 197971]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0047.35',
  'segment_index': 1,
  'start': 8,
  'end': 18,
  'original_text': 'χλεωσθέντα',
  'row_sha256': 'b455e351f7892bf68dd1d15ffa6b974102638399a9a861347775a394f45c9f0a',
  'inherited_record_sha256': 'a29730a589082ac77029fa6c898eb8b1d79431368ceba03d0634a864f4abce0b',
  'selection': (8036, 8039, 'χλευασθέντα'),
  'context_sha256': '68ade279c9392a40ec8e7f8f11e2ad2f70077e25f5c667f8d4f54a9ae84e49ff',
  'held_reason': None,
  'evidence': 'The sequence of fig tree, vine, olive and thorn identifies the vine with Noah at '
              'the flood: διὰ τὸ οἴνῳ χλευασθέντα κοιμηθῆναι. Select only χλευασθέντα for the '
              'first of two adjacent held intervals; the following infinitive belongs to the '
              'separate second interval.',
  'surface_sha256': 'fa34f68393459ad19f9e7468719698affb762b56e2772b93b1e7af8122293b74',
  'source_indices': [198645]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0047.35',
  'segment_index': 3,
  'start': 19,
  'end': 39,
  'original_text': 'πορνεύσασιν αὐτὴν δὲ',
  'row_sha256': 'b455e351f7892bf68dd1d15ffa6b974102638399a9a861347775a394f45c9f0a',
  'inherited_record_sha256': '5d79e4ad197b98b7eb5ba4e5a36fc3c86ad67a0f34e066f06e93d26dfc9242c2',
  'selection': (8036, 8039, 'κοιμηθῆναι'),
  'context_sha256': '68ade279c9392a40ec8e7f8f11e2ad2f70077e25f5c667f8d4f54a9ae84e49ff',
  'held_reason': None,
  'evidence': 'The same Noah sentence has only κοιμηθῆναι between χλευασθέντα and the next item '
              'τὴν δὲ ἐλαίαν. Select that infinitive for the second held interval, without '
              'importing or duplicating the following verified τὴν δὲ. Its earlier '
              'πορρωθῆναι/πορρωσθῆναι scan alternatives remain contrary evidence.',
  'surface_sha256': '94fd2f6c049bb97294bb9bf5126e9f89779a7da582d18113b68e398057312076',
  'source_indices': [198646]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0050.4',
  'segment_index': 2,
  'start': 104,
  'end': 110,
  'original_text': 'κτίννυ',
  'row_sha256': '05432d2fbba1b8fed7ed38cbbd0ee5447146e7bbf75eb7024354f94a673918f2',
  'inherited_record_sha256': '83a99ce55a76e9360c75d5aaee3d6436c09b6bf34254d7b324b83ab292f28e4f',
  'selection': (8102, 8105, 'κτίννυται'),
  'context_sha256': '2ba1c697c1857842c718e2f0d0b7e1e2299098fdcaeb702bded2a71d503e4154',
  'held_reason': None,
  'evidence': 'The Malichus narrative ends with Herod exacting revenge for his father: ξιφιδίοις '
              'κατακεντούμενος κτίννυται. The immediately following paragraph introduces Antigonus '
              'son of Aristobulus. These boundaries locate the final verb; Henry differs from the '
              'tentative scan κτείνεται.',
  'surface_sha256': '82e6f5fa47d66b53b708d377055c4a549d2adc016053c56d146b0d18acf1b710',
  'source_indices': [200442]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0051.5',
  'segment_index': 1,
  'start': 411,
  'end': 499,
  'original_text': "μεθ' ὧν καὶ Ἡρῴδης ἐκπληγμένος καὶ- 10 ρῶν ὅχι δὴ χεῖν ἐκ φθόνου, ἢ ἐκ ἀνίας "
                   'διενεχθῆναι',
  'row_sha256': 'b170f79c165b039991588716f5966b580eb714f04e5ae1ea2ad773ec21e69c7b',
  'inherited_record_sha256': 'b3dc66d8b1ccaec46334d9017ffa5d13a50c10d0ec27b954a3bad457290f8063',
  'selection': (8129,
                8133,
                'Μεθ’ ὧν καὶ Ἡρωδιὰς ἐκπεπλεγμένη καιρίαν δέχεται πληγὴν ἐκ φθόνου καὶ οὐκ ἀνίει '
                'διενοχλοῦσα'),
  'context_sha256': '75fb5e5a4210867eac96719a5197dea56c84988c0f56af850135f2536413766d',
  'held_reason': None,
  'evidence': 'Agrippa receives his kingdom and everyone marvels at the sudden change; the next '
              'sentence describes Herodias and ends before τὸν ἄνδρα, ἕως κατειργάσατο ἀνελθεῖν '
              'εἰς Ῥώμην. These extended flanks uniquely locate the entire held clause. The full '
              'source phrase includes the cross-node και-ρίαν, but no retained-row boundary '
              'fragment: both halves lie inside this single target.',
  'surface_sha256': '881bc0391d45a75c0c5d3b19a9eacf3662f92ff121297b5d7cc814cc50c6b157',
  'source_indices': [201223,
                     201224,
                     201225,
                     201226,
                     201227,
                     201228,
                     201229,
                     201230,
                     201231,
                     201232,
                     201233,
                     201234,
                     201235,
                     201236]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0052.2',
  'segment_index': 7,
  'start': 651,
  'end': 662,
  'original_text': 'ὑπο-χόμενος',
  'row_sha256': '473ae90521647b1688cfe6e16e8004e7c285d2765fdd63c87b47f75530af10de',
  'inherited_record_sha256': '95e1b2456961a5d17b51cdaa242482ea7185691ed7378ef7ab07650ef0d1c226',
  'selection': (8146, 8149, 'ὑποσχόμενος'),
  'context_sha256': 'c8257b07cf4ff2728363c4baf3991e41490bd8b0683349d3d8a6fe53037f1bd5',
  'held_reason': None,
  'evidence': 'The Drusilla marriage account says Ἐπιφανὴς γὰρ Ἀντιόχου, καίτοι ὑποσχόμενος, οὐκ '
              'ἐδέχετο τὴν περιτομήν. The promise/refusal sentence locates the participle; both '
              'sides of its internal hyphen already lie inside the retained target.',
  'surface_sha256': 'f2c2f06b1a900e65700e6e4691788fbc2d922dcc7c2ccaf5fe6de4879bc2b136',
  'source_indices': [201653]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.14',
  'segment_index': 1,
  'start': 19,
  'end': 34,
  'original_text': 'καταψηφισάμενοι',
  'row_sha256': '2f7acde9ec89ed97ae4218eb8e381b2f7d8c5b61062da19772698a71decbe037',
  'inherited_record_sha256': 'dadf279a663cf634666f1b6597f90d3980fabeb53be9827fd649101437574a78',
  'selection': (8538, 8541, 'καταψηφίσασθαι'),
  'context_sha256': '63d1f6cd3f13ae4bd36160b607bea23d49d99378fdb104ac3e99dcfac2dd8ce6',
  'held_reason': None,
  'evidence': 'The conversation with Damis about the impending judgment contains διάκειται δὲ '
              'ὥσπερ οἱ καταψηφίσασθαι μὲν ἐπιθυμοῦντες, αἰσχυνόμενοι δὲ τὸ μὴ ἐπ’ ἀληθέσι. These '
              'flanks locate the infinitive in Henry, despite the unresolved Bekker ending.',
  'surface_sha256': '783e59c74639a1625e1f4c7a94f5b3662420fd31c7d10a805710b4b21476f8be',
  'source_indices': [212354]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.21',
  'segment_index': 0,
  'start': 0,
  'end': 36,
  'original_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
  'row_sha256': 'ec56de9d5cee831097f055aef2ca94371d147069223ae742d25ddf05ef2871bc',
  'inherited_record_sha256': '426e42820b39fd5d1163f171257513df04e5607084f711e53a7d00692990f2fd',
  'selection': (8540, 8543, 'Ἀλλ’ ὅμως οὕτω μὲν χαρακώσαντες τὸν'),
  'context_sha256': 'cc82c9a8be86ec6265b0f762a56c0aa9842bcae82a76026a3c246f7a015d1fba',
  'held_reason': 'omitted-leading-word-fragment',
  'evidence': 'The source moves from περὶ ὅ φασι τὸν Νεῖλον σχί-ζεσθαι to Ἀλλ’ ὅμως, οὕτω μὲν '
              'χαρακώσαντες τὸν πλοῦτον. The original scan record explicitly includes a missing '
              'leading ζε[σ?]θαι in this retained row, after the previous retained row ends χί-. '
              'Selecting only the existing whole words would retire a known omitted-fragment '
              'qualification. Keep this counterpart diagnostic until a joint boundary repair '
              'accounts for the missing fragment.',
  'surface_sha256': None,
  'source_indices': []},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.31',
  'segment_index': 1,
  'start': 13,
  'end': 23,
  'original_text': 'ζωῆς χάριν',
  'row_sha256': '47c0b593664ba24931178c8ad25b491f476f1af0071bde24b727467145fd0c30',
  'inherited_record_sha256': '1e8437e1707cbac33f2c72d2354c60aa1c5984d041e131a5f503029094da3ac3',
  'selection': (8542, 8545, 'ἐωνῆσθαι'),
  'context_sha256': 'feacb6f04559d2fe2f00897c7afd94015d37b37c4829a16eecd96165ae1394b2',
  'held_reason': None,
  'evidence': 'The visitor to the imprisoned Apollonius claims τὸ προσελθεῖν αὐτῷ ἐωνῆσθαι φάσκων, '
              'ξύμβουλος δὲ σωτηρίας ἥκειν. The prison visit, preceding αὐτῷ and following φάσκων '
              'fix the one infinitive corresponding to the two damaged OCR words.',
  'surface_sha256': '8b466e6a2f4b3bdfd1299ef3e6499ef3e9b30df12224605ccb2401577a25d306',
  'source_indices': [212486]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0077.1',
  'segment_index': 1,
  'start': 838,
  'end': 847,
  'original_text': 'Θεάσω.Θαὶ',
  'row_sha256': '6445383d16be8885d2dba867bd62d8e8f09e2d04a8c35e57bb6cbd4679afadc3',
  'inherited_record_sha256': '91d2d16efea839660c1402c7aa3a98f82ebbb4d13f01253f8715217fd200d86a',
  'selection': (8680, 8684, 'θεάσασθαί'),
  'context_sha256': 'e91274d4cd767d9f95e295cd9ac7ca4241d1f0151e5c5dfd8e5a6c4b6d59c6fd',
  'held_reason': None,
  'evidence': 'The specific story names Hierius son of Plutarch, his study under Proclus, and the '
              'house of Cyrinus before the tiny human head compared with a chickpea. Within that '
              'uniquely identified story the target is θεάσασθαί, immediately before φησι. The '
              'internal OCR period does not establish a source sentence break.',
  'surface_sha256': '0facdb3033ccc3ea88ad3dfb3c31887e5a487c383234d8919849b19db71b96c5',
  'source_indices': [216886]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0078.21',
  'segment_index': 1,
  'start': 16,
  'end': 26,
  'original_text': 'τὸν σκέψιν',
  'row_sha256': '407210c7565e314a74838fb8ef396b126f3c56334e6499ac5e57b916994a08c9',
  'inherited_record_sha256': '92f0042fafb7899327e1df6daf53e2dcfff8edf18e365687656c3b6d88299b2e',
  'selection': (8708, 8711, 'τὸν Εὐβοέα'),
  'context_sha256': '77ed658f828a2c8775c58b2db760552562cd401e4b786094e8bbda19eca524c9',
  'held_reason': None,
  'evidence': 'The digression returns from Pythius to Heraiscus: ἐπὶ τὸν Ἡραΐσκον ἐπανελθεῖν τὸν '
              'Εὐβοέα, followed by Ἀνεβόα μέγιστον ὅσον. This exact return formula locates the '
              'epithet. Henry differs from both the old OCR and the tentative Bekker εὐσεβέα-like '
              'forms.',
  'surface_sha256': '685dbdce47a593a7cd3425547fba434fd568d30c8bded769899069ba070f1749',
  'source_indices': [217767, 217768]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0082.1',
  'segment_index': 5,
  'start': 1162,
  'end': 1168,
  'original_text': 'κέχρησ',
  'row_sha256': 'a353bfd257dd22e53642d25f748950e0ee116ef9729298142a7f0e7a2b8b7f89',
  'inherited_record_sha256': '49de068b0dc88a55fdd03062234b8a0dbd4fb6bdf4fc89f22d0c60896d170a0b',
  'selection': (8776, 8779, 'καὶ ξύστρας'),
  'context_sha256': 'dfdffb5f6607dbcd3f7faff67362c087755008d66677f2a5287d2572753d7603',
  'held_reason': None,
  'evidence': 'Isidore prepares his box and vessels for the port, then a body of men gathers for '
              'an attack. After Ὁ δὲ Henry has καὶ ξύστρας ἤδη ἅπτεσθαι διεκελεύετο τοὺς ὑπηρέτας, '
              'before the philosophers are imprisoned again. This narrative sequence locates the '
              'two words, differing from the old tentative compact group.',
  'surface_sha256': '0ce25e02f966a9196fa024e68945c312998b6776ece009e6d2bb2ef244bb3302',
  'source_indices': [219901, 219902]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0082.32',
  'segment_index': 1,
  'start': 9,
  'end': 23,
  'original_text': 'ἀναβήσας ὕψωμα',
  'row_sha256': '47b652674e587c39d535dbb69a263c59377d28cae9e6025bb3a92e0dbfe2429d',
  'inherited_record_sha256': 'da322101b924f8bd39ff8fae1568e5ed36b91822ae159b01e55e7336ee26fe3e',
  'selection': (8789, 8792, 'ἀναρρήγνυται'),
  'context_sha256': '5a5a44262cd858131c6767eaee2355c50cd326677e2b0fa20f096b51410a29f2',
  'held_reason': None,
  'evidence': 'The description of the Stygian site in Arabia places this verb between Εἶτα '
              'ἐξαίφνης and χάσμα εἰς ἄβυθον πέτραις πανταχόθεν συνηρεφές. Select the one complete '
              'Henry verb for the two damaged OCR words.',
  'surface_sha256': '7a38771598d7a246bde01d5f7d88ee234737c73af1b513858edd89d3bdd3bba4',
  'source_indices': [220257]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0086.26',
  'segment_index': 1,
  'start': 29,
  'end': 37,
  'original_text': 'ὁρμακοῖα',
  'row_sha256': '80b1e7a92c7f0a12e2b43aefdfc239548d70178e8b8181abf4d90d70674ad37f',
  'inherited_record_sha256': '1f948dd1f841c35d17157829430b88c0c56abc79c8ef374a4eb0a3acce0e31d9',
  'selection': (8858, 8861, 'ὀμμακοΐου'),
  'context_sha256': '8fa0ba0c0382b41086c2c8261344e0ee6e592bfd7ef7d45d0ab06aa0b219f359',
  'held_reason': None,
  'evidence': 'The Asclepiodotus narrative moves from an unknown voice ordering the ship to wait '
              'to the phrase Τοῦ ὀμμακοΐου τῆς αὐτοψίας καὶ ἀκοῆς ἅμα. The sea narrative and the '
              'following paired sight/hearing terms fix this word. Henry has genitive ὀμμακοΐου; '
              'the different verified preceding Bekker τῷ is preserved.',
  'surface_sha256': 'a273c9c34db4ca1f1b02e759652080640c2714def2e4c510ee29d4b60d33710a',
  'source_indices': [222362]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0089.31',
  'segment_index': 1,
  'start': 12,
  'end': 25,
  'original_text': 'περιεργάζεται',
  'row_sha256': '1cabf03f2d09fcb96af278e6f57111c9f217b987dfbc7c183fe394059a12e8f4',
  'inherited_record_sha256': 'bf9c0e2c4aa9a5147cc8d3bf9ed331781b4af41c859373f25e926f63c1111fa9',
  'selection': (8927, 8930, 'περιεργάζεται'),
  'context_sha256': 'a3c3d17bb7996d6638cb3c3dd6cd49c708864732b68020f4d0bed2465ad77fa6',
  'held_reason': None,
  'evidence': 'The Aeschines passage says καὶ μετὰ Κτησιφῶντα καὶ τὴν φυγὴν τυράννους ἔτι '
              'περιεργάζεται, then begins Ἄνθρωπος τὴν Ἀσίαν ὅλην. These named anchors locate '
              'Henry’s unchanged finite verb, rather than imposing the tentative scan infinitive.',
  'surface_sha256': 'ec025d84b4fd8121015cac5a37a3cbef416bb9155e47284eae7022b8edeecf17',
  'source_indices': [224135]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0091.35',
  'segment_index': 1,
  'start': 27,
  'end': 39,
  'original_text': 'προτείνεσθαι',
  'row_sha256': '49864ff5082070640af35e9f68e6f527d58e61f4ea9004e69f998012a8e065c7',
  'inherited_record_sha256': '0b895d828b04f6e355f8e10b9cfd1d246e3269ffe7427383e78c382f95cf23c2',
  'selection': (8984, 8987, 'προτείνεσθαι'),
  'context_sha256': 'b1b5e9943df39f7a271d2b825b013a5faa3426b560a119ad63a2ddf498d48816',
  'held_reason': None,
  'evidence': 'The Epicurus argument asks whether defendants may put forward deeds they have not '
              'done instead of deeds they have done: τοῖς κρινομένοις ἐξὸν ἀντὶ τῶν πεπραγμένων τὰ '
              'μὴ πεπραγμένα προτείνεσθαι. The whole question fixes Henry’s infinitive, without '
              'claiming the Bekker sigma-theta group has been resolved.',
  'surface_sha256': '1ac8b68bf94fc11bf7cf92a942ba63d413d64885e50bc7c499b9b69d38860182',
  'source_indices': [225702]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0095.3',
  'segment_index': 13,
  'start': 859,
  'end': 867,
  'original_text': 'ἐξ αὐτὸν',
  'row_sha256': 'd8292b4e88942ffeed0cd2b4916c7f580873fbd2aeac22ca0dfe4571e53e7e5a',
  'inherited_record_sha256': '2e984dcf4d9d8112028629584277e2c518a0b5df02eda5c1f6cbb0fd65e99da1',
  'selection': (9066, 9069, 'ἑστᾶναι'),
  'context_sha256': '7aa7299faf3316ef39ebdca47fe766ed475de280239468603e18b15d6107b86f',
  'held_reason': None,
  'evidence': 'The address to Xerxes asks why he cuts mountains into the sea and follows with '
              'Ἔασον ἑστᾶναι τὸν Ἄθω, καὶ μὴ πέμπε μοι διὰ τῶν ὀρῶν. The Athos/flotilla context '
              'uniquely locates Henry’s verb. This explicitly prefers Henry’s ἑστᾶναι over the '
              'tentative Bekker vowel group and the contrary digital-library ἐξύναι.',
  'surface_sha256': '997057e4df05297faf7776adc882955c53e489072abc6a3c259563fb4a13ce8f',
  'source_indices': [228145]}]

QUALIFICATION = (
    'Explicit editorial preference for the supplied Henry edition, not a claim of '
    'Bekker scan agreement. The original held text, tentative scan observations, '
    'contrary digital readings, and unrelated verified text remain unchanged in '
    'their archived layers. Source context is diagnostic and not a new corpus row.'
)


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _source_tokens(units):
    tokens = edition.tokenize(units)
    by_index = {unit['unit_index']: unit for unit in units}
    endings = edition.assess.APOSTROPHES + '\u02b9\u0374'
    for token in tokens:
        ref = token['refs'][-1]
        text = by_index[ref['unit_index']]['text']
        if ref['end'] < len(text) and text[ref['end']] in endings:
            token['text'] += text[ref['end']]
            ref['end'] += 1
    return tokens


def _record(spec, units):
    if not isinstance(units, list) or _digest(units) != spec['context_sha256']:
        raise ValueError('The manually reviewed source context changed')
    first, stop, phrase = spec['selection']
    if [unit.get('unit_index') for unit in units] != list(range(first, stop)):
        raise ValueError('The manually reviewed source units lost their global identities')
    tokens = _source_tokens(units)
    wanted = [edition.normalize(match.group()) for match in edition.WORD.finditer(phrase)]
    if not wanted:
        raise ValueError('A manual source selection must contain complete Greek words')
    positions = [i for i in range(len(tokens)-len(wanted)+1)
        if [token['key'] for token in tokens[i:i+len(wanted)]] == wanted]
    boundaries = spec.get('boundaries', {})
    left = [edition.normalize(match.group()) for match in edition.WORD.finditer(boundaries.get('left', ''))]
    right = [edition.normalize(match.group()) for match in edition.WORD.finditer(boundaries.get('right', ''))]
    positions = [i for i in positions
        if (not left or i >= len(left) and [token['key'] for token in tokens[i-len(left):i]] == left)
        and (not right or [token['key'] for token in tokens[i+len(wanted):i+len(wanted)+len(right)]] == right)]
    if len(positions) != 1:
        raise ValueError('A manually reviewed phrase must occur exactly once in its pinned context')
    selected = tokens[positions[0]:positions[0]+len(wanted)]
    reading = {'text': ' '.join(token['text'] for token in selected),
        'source_id': 'tlg-photius-henry',
        'refs': [deepcopy(ref) for token in selected for ref in token['refs']],
        'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs'])} for token in selected],
        'role': 'alternative',
        'location_basis': 'Individually read named or sentence-level surrounding source context.'}
    held = spec['held_reason'] is not None
    if (held and (spec['surface_sha256'] is not None or spec['source_indices'])
            or not held and (not isinstance(spec['surface_sha256'], str)
                or len(spec['surface_sha256']) != 64
                or len(spec['source_indices']) != len(selected)
                or any(type(index) is not int or index < 0 for index in spec['source_indices']))):
        raise ValueError('The reviewed source punctuation and token-index pins are incomplete')
    return {'kind': 'individually-reviewed-remaining-reading',
        'status': 'held' if held else 'located',
        'role': 'authorial-body', 'reviewed_at': REVIEWED_AT,
        'original_text': spec['original_text'],
        'original_row_sha256': spec['row_sha256'],
        'inherited_record_sha256': spec['inherited_record_sha256'],
        'evidence': spec['evidence'], 'qualification': QUALIFICATION,
        'held_reason': spec['held_reason'],
        'readings': [] if held else [reading],
        'diagnostic_readings': [reading] if held else [],
        'surface_sha256': spec['surface_sha256'],
        'source_indices': deepcopy(spec['source_indices']),
        'rendering': deepcopy(spec.get('rendering', {})),
        'source_context': {'source_id': 'tlg-photius-henry',
            'sha256': SOURCE_SHA256, 'units_sha256': spec['context_sha256'],
            'units': deepcopy(units), 'qualification': QUALIFICATION}}


def validate_record(key, record):
    specs = {(spec['locus'], spec['segment_index']): spec for spec in SPECS}
    if key not in specs or not isinstance(record, dict):
        raise ValueError('Unknown manually reviewed remaining occurrence')
    context = record.get('source_context')
    if not isinstance(context, dict):
        raise ValueError('The manual review requires its exact decoded source context')
    expected = _record(specs[key], context.get('units'))
    if record != expected:
        raise ValueError('The manual review differs from its complete authored authority')
    return deepcopy(expected)


def review_remaining(html_raw, scopes):
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied manual-review edition changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    import prepare_photius_editorial_continuation as preparer
    source_units = preparer.source_document(html_raw)
    source_indices = {_digest(token['refs']): index
                      for index, token in enumerate(_source_tokens(parser.units))}
    result = {}
    for spec in SPECS:
        key = spec['locus'], spec['segment_index']
        if key not in scopes:
            raise ValueError('A manually reviewed remaining occurrence is missing')
        scope = scopes[key]
        if (scope['start'] != spec['start'] or scope['end'] != spec['end']
                or scope['row']['locus'] != key[0]
                or scope['record']['locus'] != key[0]
                or scope['record']['segment_index'] != key[1]
                or scope['row']['text'][scope['start']:scope['end']] != spec['original_text']
                or _digest(scope['row']) != spec['row_sha256']
                or _digest(scope['record']) != spec['inherited_record_sha256']):
            raise ValueError('The manual review lost its exact baseline occurrence')
        first, stop, _ = spec['selection']
        record = _record(spec, parser.units[first:stop])
        if record['readings']:
            reading = record['readings'][0]
            attributed = preparer.attributed_span(reading, source_units)
            surface_digest = _digest({field: attributed[field]
                for field in ('surface', 'separators', 'boundary_suffix')})
            indices = [source_indices[_digest(token['refs'])] for token in reading['tokens']]
            if surface_digest != spec['surface_sha256'] or indices != spec['source_indices']:
                raise ValueError('Fresh source punctuation or complete-edition token indices changed')
        result[key] = record
    return result
