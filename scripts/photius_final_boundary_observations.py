"""Individually reviewed joint-word decisions for final Photius boundaries.

The caller freezes and reverses every original row. Each complete supplied-edition
word has one display owner; its other printed fragments are removed only by the
paired, exact edits below. Contrary scan and digital observations remain archived.
This module does not write corpus data or change any earlier source judgment.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import unicodedata

import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-22T00:57:14Z'
SOURCE_ID = 'tlg-photius-henry'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
BASELINE_SHA256 = 'aa39e3465387f5f192a509acbb7b8107c4641e3bf2a92bdf774d3253b2c7a1a0'
SOURCE_PINS = {
    'data/corpus_changes/photius-bekker-readings/source-scan.pdf':
        'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
    'data/corpus_changes/photius-bekker-editorial-substitutions/compiled-review.json.gz':
        '76abb40a4759da8659bf8646fc80a9310c1c519adc6fb4a7ef3fe5b767fed633',
    'data/corpus_changes/photius-bekker-editorial-continuation/compiled-review.json.gz':
        '92e1bda2d83523cb07f8611c429bd869d819dea9a9decd71da5809f0e0d99d4a',
}
SPECS = [{'id': 'boundary-0038.17',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.17',
                  'segment_index': 0,
                  'start': 0,
                  'end': 5,
                  'original_text': 'δῶσιν',
                  'inherited_record_sha256': '3b878eb72d7e6204ac3989faf05852c7a684ade62e9e818aabb8781172d655dc',
                  'original_segment_sha256': '55e37e2e149e5be20534f4b8ed91917de986189678c30c584d8d8bf9faa5f680'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.16',
             'start': 46,
             'end': 52,
             'original_text': 'συναΐ-',
             'corrected_text': '',
             'original_row_sha256': '5f9ae882bf8faaaaf509b02ccf846eea8ddd00fac3a5638e0873e1d033dae3d2'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.17',
             'start': 0,
             'end': 5,
             'original_text': 'δῶσιν',
             'corrected_text': 'συναΐδιον',
             'original_row_sha256': '5facd2474ec4833d06bda17cfebd51d3252b88f4f87279ce811d7e7a0378c7cd'}],
  'evidence': 'The physical line ends συναΐ- and the following line resumes διον before δι’ αὐτὸ τοῦτο. The '
              'current suffix δῶσιν cannot be replaced independently while retaining συναΐ-. Select the '
              'supplied edition’s complete συναΐδιον once and retain the scan line break and prior suffix '
              'readings as evidence.',
  'scan': {'image_sha256': '1df8dcec923bcf2e3871d108ac98108f3cca14ed2cfcb2b062f095163fbde0bf',
           'max_side': 3600,
           'observed_text': 'συναΐ-\nδιον',
           'physical_page': 38,
           'printed_page': 303,
           'region': [0.055, 0.1, 0.455, 0.755],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 7792,
                'stop': 7795,
                'units_sha256': 'd87bd2c04a20a1236518ae7940b6e1a3a4246de438251fd10e6f82b80ead7bd3',
                'units': [{'text': ' Οὐδ’ ἄρα ὅτ’ ἐποίει τὸν κόσ‐ \n'
                                   'μον, ἠλλοιῶσθαι αὐτὸν ἀνάγκη παρ’ ὃ ἦν ὅτε οὐκ ἐποίει·',
                           'html_line': 18664,
                           'html_column': 59,
                           'unit_index': 7792,
                           'codex': '235',
                           'bekker': '303a'},
                          {'text': 'καὶ οὔτε ἀνάγκη συνυπάρχειν αὐτῷ τὸ πᾶν δεῖν λέγειν \n'
                                   'διὰ τὸ μὴ ἀναγκάζεσθαι λέγειν ἠλλοιῶσθαι, οὔτε συναΐ‐ \n'
                                   'διον δι’ αὐτὸ τοῦτο. \n'
                                   '    Καί μοι φάθι καὶ ὧδε· γενητὸν τὸ μὴ γενέσεως \n'
                                   'ἔχον ἀρχὴν φαίης ἄν; ',
                           'html_line': 18665,
                           'html_column': 68,
                           'unit_index': 7793,
                           'codex': '235',
                           'bekker': '303a'},
                          {'text': ' Οὐ δῆτα· εἰ γὰρ μὴ ὑποπίπτει',
                           'html_line': 18669,
                           'html_column': 38,
                           'unit_index': 7794,
                           'codex': '235',
                           'bekker': '303a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'συναΐδιον',
              'refs': [{'html_line': 18665,
                        'html_column': 68,
                        'unit_index': 7793,
                        'codex': '235',
                        'bekker': '303a',
                        'start': 100,
                        'end': 105},
                       {'html_line': 18665,
                        'html_column': 68,
                        'unit_index': 7793,
                        'codex': '235',
                        'bekker': '303a',
                        'start': 108,
                        'end': 112}],
              'tokens': [{'text': 'συναΐδιον',
                          'refs': [{'html_line': 18665,
                                    'html_column': 68,
                                    'unit_index': 7793,
                                    'codex': '235',
                                    'bekker': '303a',
                                    'start': 100,
                                    'end': 105},
                                   {'html_line': 18665,
                                    'html_column': 68,
                                    'unit_index': 7793,
                                    'codex': '235',
                                    'bekker': '303a',
                                    'start': 108,
                                    'end': 112}],
                          'source_index': 192478}],
              'surface': 'συναΐδιον',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.17',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 5,
                                              'corrected_start': 0,
                                              'corrected_text': 'δῶσιν',
                                              'digital_alignment': {'admission_authorized': False,
                                                                    'aligned': True,
                                                                    'ambiguous': True,
                                                                    'cost': 33,
                                                                    'digital_insertions': [],
                                                                    'qualification': 'All optimal diagnostic '
                                                                                     'token counterparts are '
                                                                                     'retained; character '
                                                                                     'similarity does not '
                                                                                     'certify a source '
                                                                                     'reading.',
                                                                    'section': 'tlg4040-tlg001-local002-s315',
                                                                    'tokens': [{'counterpart_count': 7,
                                                                                'end': 4,
                                                                                'may_be_unaligned': False,
                                                                                'start': 0,
                                                                                'text': 'διον'}]},
                                              'end': 5,
                                              'evidence': 'Direct visual inspection of every character in '
                                                          'the recorded printed body range in the pinned '
                                                          'Bekker1825 volume2 scan, with paragraph and '
                                                          'physical-line boundaries checked against the '
                                                          'page.',
                                              'fragments': [],
                                              'original_text': 'δῶσιν',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': 'd4263f3a975ca26a7a45330530cd065f422bdc803893f39ae31b7feafca4cfbc',
                                                            'text': 'δῶσιν'},
                                                           {'image_sha256': '1df8dcec923bcf2e3871d108ac98108f3cca14ed2cfcb2b062f095163fbde0bf',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 38,
                                                            'region': [0.055, 0.1, 0.455, 0.755],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'διον'},
                                                           {'end': 48,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 45,
                                                            'text': 'δι’'},
                                                           {'end': 797,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 794,
                                                            'text': 'δι’'},
                                                           {'end': 1174,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 1169,
                                                            'text': 'δῆλον'},
                                                           {'end': 1848,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 1840,
                                                            'text': 'διοικεῖν'},
                                                           {'end': 2161,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2158,
                                                            'text': 'δι’'},
                                                           {'end': 2272,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2269,
                                                            'text': 'δι’'},
                                                           {'end': 2527,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 4,
                                                                            'start': 0,
                                                                            'text': 'διον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s315',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2524,
                                                            'text': 'δι’'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:12:22.905683+00:00',
                                              'scan': {'image_sha256': '1df8dcec923bcf2e3871d108ac98108f3cca14ed2cfcb2b062f095163fbde0bf',
                                                       'max_side': 3600,
                                                       'observed_text': 'διον',
                                                       'physical_page': 38,
                                                       'printed_page': 303,
                                                       'region': [0.055, 0.1, 0.455, 0.755],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand the printed ου and στ '
                                                                          'ligatures and the καὶ sign to '
                                                                          'ordinary Greek Unicode; retain '
                                                                          'the current apostrophe and '
                                                                          'quotation encoding and printed '
                                                                          'line breaks. Marginal edition '
                                                                          'references and line numbers are '
                                                                          'paratext, and are removed from '
                                                                          'body readings while remaining '
                                                                          'reversible in the exact original '
                                                                          'row and source scan. Digital '
                                                                          'counterpart candidates are '
                                                                          'diagnostic source observations '
                                                                          'and do not authorize the scan '
                                                                          'reading. Expand the conventional '
                                                                          'printed σθ ligature to ordinary '
                                                                          'Greek Unicode.',
                                              'uncertainty': 'This continuation after preceding συναΐ- has '
                                                             'unclear small vowel types; possible διον or '
                                                             'δον and exact original remain explicit. No '
                                                             'complete independent word is supplied.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'δῶσιν',
                                                  'decision': 'retained',
                                                  'evidence': 'The sentence has οὔτε συναΐ-διον δι’ αὐτὸ '
                                                              'τοῦτο. The retained previous row already ends '
                                                              'συναΐ-, while this target is only the '
                                                              'continuation. A complete Henry word would '
                                                              'duplicate that prefix. Keep the source word '
                                                              'as diagnostic evidence and require a joint '
                                                              'boundary review.',
                                                  'location_evidence': {'source_sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                        'status': 'held-no-immediate-reliable-boundaries'},
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.17',
                                                  'manual_review': {'module': 'photius_remaining_manual_a',
                                                                    'review': {'diagnostic_readings': [{'location_basis': 'Individually '
                                                                                                                          'read '
                                                                                                                          'named '
                                                                                                                          'or '
                                                                                                                          'sentence-level '
                                                                                                                          'surrounding '
                                                                                                                          'source '
                                                                                                                          'context.',
                                                                                                        'refs': [{'bekker': '303a',
                                                                                                                  'codex': '235',
                                                                                                                  'end': 105,
                                                                                                                  'html_column': 68,
                                                                                                                  'html_line': 18665,
                                                                                                                  'start': 100,
                                                                                                                  'unit_index': 7793},
                                                                                                                 {'bekker': '303a',
                                                                                                                  'codex': '235',
                                                                                                                  'end': 112,
                                                                                                                  'html_column': 68,
                                                                                                                  'html_line': 18665,
                                                                                                                  'start': 108,
                                                                                                                  'unit_index': 7793}],
                                                                                                        'role': 'alternative',
                                                                                                        'source_id': 'tlg-photius-henry',
                                                                                                        'text': 'συναΐδιον',
                                                                                                        'tokens': [{'refs': [{'bekker': '303a',
                                                                                                                              'codex': '235',
                                                                                                                              'end': 105,
                                                                                                                              'html_column': 68,
                                                                                                                              'html_line': 18665,
                                                                                                                              'start': 100,
                                                                                                                              'unit_index': 7793},
                                                                                                                             {'bekker': '303a',
                                                                                                                              'codex': '235',
                                                                                                                              'end': 112,
                                                                                                                              'html_column': 68,
                                                                                                                              'html_line': 18665,
                                                                                                                              'start': 108,
                                                                                                                              'unit_index': 7793}],
                                                                                                                    'text': 'συναΐδιον'}]}],
                                                                               'evidence': 'The sentence has '
                                                                                           'οὔτε συναΐ-διον '
                                                                                           'δι’ αὐτὸ τοῦτο. '
                                                                                           'The retained '
                                                                                           'previous row '
                                                                                           'already ends '
                                                                                           'συναΐ-, while '
                                                                                           'this target is '
                                                                                           'only the '
                                                                                           'continuation. A '
                                                                                           'complete Henry '
                                                                                           'word would '
                                                                                           'duplicate that '
                                                                                           'prefix. Keep the '
                                                                                           'source word as '
                                                                                           'diagnostic '
                                                                                           'evidence and '
                                                                                           'require a joint '
                                                                                           'boundary review.',
                                                                               'held_reason': 'cross-row-word',
                                                                               'inherited_record_sha256': '93f5490730eeab91045135218a89b6ab8c8b7f285d844064be77488e219e02d6',
                                                                               'kind': 'individually-reviewed-remaining-reading',
                                                                               'original_row_sha256': 'd3d26fe0b1ae8c1573fcc5d49d304a60ce615e11c57c63e2f2fa172d45f90f2b',
                                                                               'original_text': 'δῶσιν',
                                                                               'qualification': 'Explicit '
                                                                                                'editorial '
                                                                                                'preference '
                                                                                                'for the '
                                                                                                'supplied '
                                                                                                'Henry '
                                                                                                'edition, '
                                                                                                'not a claim '
                                                                                                'of Bekker '
                                                                                                'scan '
                                                                                                'agreement. '
                                                                                                'The '
                                                                                                'original '
                                                                                                'held text, '
                                                                                                'tentative '
                                                                                                'scan '
                                                                                                'observations, '
                                                                                                'contrary '
                                                                                                'digital '
                                                                                                'readings, '
                                                                                                'and '
                                                                                                'unrelated '
                                                                                                'verified '
                                                                                                'text remain '
                                                                                                'unchanged '
                                                                                                'in their '
                                                                                                'archived '
                                                                                                'layers. '
                                                                                                'Source '
                                                                                                'context is '
                                                                                                'diagnostic '
                                                                                                'and not a '
                                                                                                'new corpus '
                                                                                                'row.',
                                                                               'readings': [],
                                                                               'rendering': {},
                                                                               'reviewed_at': '2026-10-21T23:14:05.501170Z',
                                                                               'role': 'authorial-body',
                                                                               'source_context': {'qualification': 'Explicit '
                                                                                                                   'editorial '
                                                                                                                   'preference '
                                                                                                                   'for '
                                                                                                                   'the '
                                                                                                                   'supplied '
                                                                                                                   'Henry '
                                                                                                                   'edition, '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'claim '
                                                                                                                   'of '
                                                                                                                   'Bekker '
                                                                                                                   'scan '
                                                                                                                   'agreement. '
                                                                                                                   'The '
                                                                                                                   'original '
                                                                                                                   'held '
                                                                                                                   'text, '
                                                                                                                   'tentative '
                                                                                                                   'scan '
                                                                                                                   'observations, '
                                                                                                                   'contrary '
                                                                                                                   'digital '
                                                                                                                   'readings, '
                                                                                                                   'and '
                                                                                                                   'unrelated '
                                                                                                                   'verified '
                                                                                                                   'text '
                                                                                                                   'remain '
                                                                                                                   'unchanged '
                                                                                                                   'in '
                                                                                                                   'their '
                                                                                                                   'archived '
                                                                                                                   'layers. '
                                                                                                                   'Source '
                                                                                                                   'context '
                                                                                                                   'is '
                                                                                                                   'diagnostic '
                                                                                                                   'and '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'new '
                                                                                                                   'corpus '
                                                                                                                   'row.',
                                                                                                  'sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                                                  'source_id': 'tlg-photius-henry',
                                                                                                  'units': [{'bekker': '303a',
                                                                                                             'codex': '235',
                                                                                                             'html_column': 59,
                                                                                                             'html_line': 18664,
                                                                                                             'text': ' '
                                                                                                                     'Οὐδ’ '
                                                                                                                     'ἄρα '
                                                                                                                     'ὅτ’ '
                                                                                                                     'ἐποίει '
                                                                                                                     'τὸν '
                                                                                                                     'κόσ‐ \n'
                                                                                                                     'μον, '
                                                                                                                     'ἠλλοιῶσθαι '
                                                                                                                     'αὐτὸν '
                                                                                                                     'ἀνάγκη '
                                                                                                                     'παρ’ '
                                                                                                                     'ὃ '
                                                                                                                     'ἦν '
                                                                                                                     'ὅτε '
                                                                                                                     'οὐκ '
                                                                                                                     'ἐποίει·',
                                                                                                             'unit_index': 7792},
                                                                                                            {'bekker': '303a',
                                                                                                             'codex': '235',
                                                                                                             'html_column': 68,
                                                                                                             'html_line': 18665,
                                                                                                             'text': 'καὶ '
                                                                                                                     'οὔτε '
                                                                                                                     'ἀνάγκη '
                                                                                                                     'συνυπάρχειν '
                                                                                                                     'αὐτῷ '
                                                                                                                     'τὸ '
                                                                                                                     'πᾶν '
                                                                                                                     'δεῖν '
                                                                                                                     'λέγειν \n'
                                                                                                                     'διὰ '
                                                                                                                     'τὸ '
                                                                                                                     'μὴ '
                                                                                                                     'ἀναγκάζεσθαι '
                                                                                                                     'λέγειν '
                                                                                                                     'ἠλλοιῶσθαι, '
                                                                                                                     'οὔτε '
                                                                                                                     'συναΐ‐ \n'
                                                                                                                     'διον '
                                                                                                                     'δι’ '
                                                                                                                     'αὐτὸ '
                                                                                                                     'τοῦτο. \n'
                                                                                                                     '    '
                                                                                                                     'Καί '
                                                                                                                     'μοι '
                                                                                                                     'φάθι '
                                                                                                                     'καὶ '
                                                                                                                     'ὧδε· '
                                                                                                                     'γενητὸν '
                                                                                                                     'τὸ '
                                                                                                                     'μὴ '
                                                                                                                     'γενέσεως \n'
                                                                                                                     'ἔχον '
                                                                                                                     'ἀρχὴν '
                                                                                                                     'φαίης '
                                                                                                                     'ἄν; ',
                                                                                                             'unit_index': 7793},
                                                                                                            {'bekker': '303a',
                                                                                                             'codex': '235',
                                                                                                             'html_column': 38,
                                                                                                             'html_line': 18669,
                                                                                                             'text': ' '
                                                                                                                     'Οὐ '
                                                                                                                     'δῆτα· '
                                                                                                                     'εἰ '
                                                                                                                     'γὰρ '
                                                                                                                     'μὴ '
                                                                                                                     'ὑποπίπτει',
                                                                                                             'unit_index': 7794}],
                                                                                                  'units_sha256': 'd87bd2c04a20a1236518ae7940b6e1a3a4246de438251fd10e6f82b80ead7bd3'},
                                                                               'source_indices': [],
                                                                               'status': 'held',
                                                                               'surface_sha256': None}},
                                                  'original_text': 'δῶσιν',
                                                  'readings': [],
                                                  'reason': 'individually-held-reading',
                                                  'segment_index': 0}}],
  'surface_sha256': 'ac436bee25aafa8fbe9d9e4758013af431230a740b39729adfb669e1c0d6026b'},
 {'id': 'boundary-0044.26',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.26',
                  'segment_index': 1,
                  'start': 37,
                  'end': 49,
                  'original_text': 'μελλαν εξφο-',
                  'inherited_record_sha256': '15de8a9f85ff7dc86d1f630762b1abe572e3e118c033e79adefec82cedc01494',
                  'original_segment_sha256': '58923065350717b9feb3a97479cb8e5aa7388b357ad6e2b2f7205630bff2a1b2'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.26',
             'start': 37,
             'end': 49,
             'original_text': 'μελλαν εξφο-',
             'corrected_text': 'μᾶλλον',
             'original_row_sha256': '0108ebf7f93be705d0237cbf63bd0cb1a17982823e312a1be6ffdcb3659a44f6'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.27',
             'start': 0,
             'end': 5,
             'original_text': 'ρεσαν',
             'corrected_text': 'εὐφόρεσαν',
             'original_row_sha256': '02d941665ec6ebf934381bdbc399af03d43d11ed4fec67cfafb799667efdd178'}],
  'evidence': 'The lines after ἐγκρατευσά-μεναι and ἁγνεύσασαι divide the disputed verb before ρεσαν. The '
              'supplied edition reads μᾶλλον εὐφό-ρεσαν. Adopt its two complete words as an explicit '
              'editorial selection; retain the tentative Bekker μᾶλλον εἰσώ- reading without claiming '
              'identical letterforms.',
  'scan': {'image_sha256': 'c36de497e9b589a4d0af56e0581e5ce3ae9f8812f34f7c35ca19452412756395',
           'max_side': 3600,
           'observed_text': 'The disputed compact prefix is followed by ρεσαν on the next line; its complete '
                            'letterforms are not certified here.',
           'physical_page': 44,
           'printed_page': 309,
           'region': [0.395, 0.1, 0.815, 0.755],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 7975,
                'stop': 7979,
                'units_sha256': 'a530c69cee95c2bb34f034038d4d53d186b30c5d7e5110693e5b523421e8a4ba',
                'units': [{'text': 'τὴν ἔμφασιν τοῦ ἰῶτα στοιχείου. Ἐστείλαντο μὲν γὰρ παρα‐ \n'
                                   'πλησίως ἑαυτὰς εἰς τοῦτο καθομολογήσασαι, καὶ ταύτῃ \n'
                                   'κικλήσκονται δέκα, οὐκέτι δὲ ὁμοίως ἐξῆλθον ὑπαντή‐ \n'
                                   'σουσαι τῷ νυμφίῳ· αἱ μὲν γὰρ τροφὴν ἄφθονον ἐπορί‐ \n'
                                   'σαντο ταῖς ἐλαιοθρέπτοις λαμπάσιν, αἱ δὲ κατερρα‐',
                           'html_line': 19057,
                           'html_column': 101,
                           'unit_index': 7975,
                           'codex': '237',
                           'bekker': '309b'},
                          {'text': 'θύμησαν. Διὸ δὴ καὶ ἰσάριθμοι πρὸς εʹ διαιροῦνται, \n'
                                   'ἐπειδήπερ τὰς πέντε αἰσθήσεις αἱ μὲν αὐτῶν ἐφυλάξαντο \n'
                                   'καθαράς, ἃς οἱ πλεῖστοι σοφίας πύλας προσηγόρευσαν, \n'
                                   'αἱ δὲ τοὐναντίον κατελωβήσαντο κακίᾳ. Ἐγκρατευσά‐ \n'
                                   'μεναι γὰρ καὶ ἁγνεύσασαι δικαιοσύνης μᾶλλον εὐφό‐',
                           'html_line': 19061,
                           'html_column': 63,
                           'unit_index': 7976,
                           'codex': '237',
                           'bekker': '309b'},
                          {'text': 'ρεσαν παραπτώμασιν· ἐξ οὗ καὶ συνέβη αὐτὰς ἀπαγο‐ \n'
                                   'ρευθῆναι. Εἴτε γὰρ κατορθοῦμεν, εἴτε πλημμελοῦμεν, διὰ \n'
                                   'τούτων ἑκάτερα καὶ τὰ ἀνδραγαθήματα κρατύνεται καὶ \n'
                                   'τὰ κακὰ πράγματα. Καὶ ὥσπερ ἡ Θάλλουσα καὶ ὀφθαλ‐ \n'
                                   'μῶν ἁγνείαν ἔφη καὶ ὤτων εἶναι καὶ γλώσσης καὶ τῶν',
                           'html_line': 19065,
                           'html_column': 63,
                           'unit_index': 7977,
                           'codex': '237',
                           'bekker': '309b'},
                          {'text': 'λοιπῶν καθεξῆς αἰσθητηρίων, οὕτω δὴ καὶ τὰ ἐνταῦθα \n'
                                   'τὴν πίστιν ἄσυλον ἡ φυλαξαμένη τῶν πέντε διόδων τῆς \n'
                                   'ἀρετῆς, ὁράσεως, γεύσεως, ὀσφρήσεως, ἁφῆς τε καὶ \n'
                                   'ἀκοῆς, πέντε προσαγορεύεται παρθένοι, διὰ τὸ τὰς \n'
                                   'πέντε τῆς αἰσθήσεως ἁγνὰς ἀποκαταστῆσαι τῷ Χριστῷ',
                           'html_line': 19069,
                           'html_column': 64,
                           'unit_index': 7978,
                           'codex': '237',
                           'bekker': '309b'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'μᾶλλον εὐφόρεσαν',
              'refs': [{'html_line': 19061,
                        'html_column': 63,
                        'unit_index': 7976,
                        'codex': '237',
                        'bekker': '309b',
                        'start': 248,
                        'end': 254},
                       {'html_line': 19061,
                        'html_column': 63,
                        'unit_index': 7976,
                        'codex': '237',
                        'bekker': '309b',
                        'start': 255,
                        'end': 259},
                       {'html_line': 19065,
                        'html_column': 63,
                        'unit_index': 7977,
                        'codex': '237',
                        'bekker': '309b',
                        'start': 0,
                        'end': 5}],
              'tokens': [{'text': 'μᾶλλον',
                          'refs': [{'html_line': 19061,
                                    'html_column': 63,
                                    'unit_index': 7976,
                                    'codex': '237',
                                    'bekker': '309b',
                                    'start': 248,
                                    'end': 254}],
                          'source_index': 196924},
                         {'text': 'εὐφόρεσαν',
                          'refs': [{'html_line': 19061,
                                    'html_column': 63,
                                    'unit_index': 7976,
                                    'codex': '237',
                                    'bekker': '309b',
                                    'start': 255,
                                    'end': 259},
                                   {'html_line': 19065,
                                    'html_column': 63,
                                    'unit_index': 7977,
                                    'codex': '237',
                                    'bekker': '309b',
                                    'start': 0,
                                    'end': 5}],
                          'source_index': 196925}],
              'surface': 'μᾶλλον εὐφόρεσαν',
              'separators': [{'pieces': [{'text': ' ',
                                          'ref': {'html_line': 19061,
                                                  'html_column': 63,
                                                  'node_index': 8068,
                                                  'codex': '237',
                                                  'bekker': '309b',
                                                  'start': 254,
                                                  'end': 255}}],
                              'rendered': ' '}],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.26',
                                      'segment_index': 1},
                         'original_segment': {'corrected_end': 49,
                                              'corrected_start': 37,
                                              'corrected_text': 'μελλαν εξφο-',
                                              'digital_alignment': {'admission_authorized': False,
                                                                    'aligned': True,
                                                                    'ambiguous': False,
                                                                    'cost': 60,
                                                                    'digital_insertions': [],
                                                                    'qualification': 'All optimal diagnostic '
                                                                                     'token counterparts are '
                                                                                     'retained; character '
                                                                                     'similarity does not '
                                                                                     'certify a source '
                                                                                     'reading.',
                                                                    'section': 'tlg4040-tlg001-local002-s321',
                                                                    'tokens': [{'counterpart_count': 1,
                                                                                'end': 6,
                                                                                'may_be_unaligned': False,
                                                                                'start': 0,
                                                                                'text': 'μᾶλλον'},
                                                                               {'counterpart_count': 0,
                                                                                'end': 11,
                                                                                'may_be_unaligned': True,
                                                                                'start': 7,
                                                                                'text': 'εἰσώ'}]},
                                              'end': 49,
                                              'evidence': 'Direct visual inspection of every character in '
                                                          'the recorded printed body range in the pinned '
                                                          'Bekker1825 volume2 scan, with paragraph and '
                                                          'physical-line boundaries checked against the '
                                                          'page.',
                                              'fragments': [],
                                              'original_text': 'μελλαν εξφο-',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '53024a63c4e0583146105d5f032b726c44169dd961240d06394f70ae71b77693',
                                                            'text': 'μελλαν εξφο-'},
                                                           {'image_sha256': 'c36de497e9b589a4d0af56e0581e5ce3ae9f8812f34f7c35ca19452412756395',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 44,
                                                            'region': [0.395, 0.1, 0.815, 0.755],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'μᾶλλον εἰσώ-'},
                                                           {'end': 3234,
                                                            'kind': 'digital',
                                                            'may_be_unaligned': False,
                                                            'review_span': {'end': 6,
                                                                            'start': 0,
                                                                            'text': 'μᾶλλον'},
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s321',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 3228,
                                                            'text': 'μᾶλλον'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:28:23.748119+00:00',
                                              'scan': {'image_sha256': 'c36de497e9b589a4d0af56e0581e5ce3ae9f8812f34f7c35ca19452412756395',
                                                       'max_side': 3600,
                                                       'observed_text': 'μᾶλλον εἰσώ-',
                                                       'physical_page': 44,
                                                       'printed_page': 309,
                                                       'region': [0.395, 0.1, 0.815, 0.755],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 37,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand the printed ου and στ '
                                                                          'ligatures and the καὶ sign to '
                                                                          'ordinary Greek Unicode; retain '
                                                                          'the current apostrophe and '
                                                                          'quotation encoding and printed '
                                                                          'line breaks. Marginal edition '
                                                                          'references and line numbers are '
                                                                          'paratext, and are removed from '
                                                                          'body readings while remaining '
                                                                          'reversible in the exact original '
                                                                          'row and source scan. Digital '
                                                                          'counterpart candidates are '
                                                                          'diagnostic source observations '
                                                                          'and do not authorize the scan '
                                                                          'reading. Expand the conventional '
                                                                          'printed σθ ligature to ordinary '
                                                                          'Greek Unicode.',
                                              'uncertainty': 'The small verb fragment and adjacent adverb '
                                                             'remain unresolved; possible μᾶλλον εἰσώ- or '
                                                             'μᾶλλον εἰσέ- and exact original remain '
                                                             'explicit. No lexical completion is supplied.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'μελλαν εξφο-',
                                                  'decision': 'retained',
                                                  'evidence': 'Henry has δικαιοσύνης μᾶλλον εὐφό-ρεσαν '
                                                              'παραπτώμασιν. The exact held target ends in a '
                                                              'printed partial word, and the next retained '
                                                              'row begins ρεσαν. Replacing it with the '
                                                              'complete Henry word would duplicate that '
                                                              'continuation. Preserve the complete '
                                                              'diagnostic reading and require a joint '
                                                              'boundary review.',
                                                  'location_evidence': {'source_sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                        'status': 'held-no-immediate-reliable-boundaries'},
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0044.26',
                                                  'manual_review': {'module': 'photius_remaining_manual_a',
                                                                    'review': {'diagnostic_readings': [{'location_basis': 'Individually '
                                                                                                                          'read '
                                                                                                                          'named '
                                                                                                                          'or '
                                                                                                                          'sentence-level '
                                                                                                                          'surrounding '
                                                                                                                          'source '
                                                                                                                          'context.',
                                                                                                        'refs': [{'bekker': '309b',
                                                                                                                  'codex': '237',
                                                                                                                  'end': 254,
                                                                                                                  'html_column': 63,
                                                                                                                  'html_line': 19061,
                                                                                                                  'start': 248,
                                                                                                                  'unit_index': 7976},
                                                                                                                 {'bekker': '309b',
                                                                                                                  'codex': '237',
                                                                                                                  'end': 259,
                                                                                                                  'html_column': 63,
                                                                                                                  'html_line': 19061,
                                                                                                                  'start': 255,
                                                                                                                  'unit_index': 7976},
                                                                                                                 {'bekker': '309b',
                                                                                                                  'codex': '237',
                                                                                                                  'end': 5,
                                                                                                                  'html_column': 63,
                                                                                                                  'html_line': 19065,
                                                                                                                  'start': 0,
                                                                                                                  'unit_index': 7977}],
                                                                                                        'role': 'alternative',
                                                                                                        'source_id': 'tlg-photius-henry',
                                                                                                        'text': 'μᾶλλον '
                                                                                                                'εὐφόρεσαν',
                                                                                                        'tokens': [{'refs': [{'bekker': '309b',
                                                                                                                              'codex': '237',
                                                                                                                              'end': 254,
                                                                                                                              'html_column': 63,
                                                                                                                              'html_line': 19061,
                                                                                                                              'start': 248,
                                                                                                                              'unit_index': 7976}],
                                                                                                                    'text': 'μᾶλλον'},
                                                                                                                   {'refs': [{'bekker': '309b',
                                                                                                                              'codex': '237',
                                                                                                                              'end': 259,
                                                                                                                              'html_column': 63,
                                                                                                                              'html_line': 19061,
                                                                                                                              'start': 255,
                                                                                                                              'unit_index': 7976},
                                                                                                                             {'bekker': '309b',
                                                                                                                              'codex': '237',
                                                                                                                              'end': 5,
                                                                                                                              'html_column': 63,
                                                                                                                              'html_line': 19065,
                                                                                                                              'start': 0,
                                                                                                                              'unit_index': 7977}],
                                                                                                                    'text': 'εὐφόρεσαν'}]}],
                                                                               'evidence': 'Henry has '
                                                                                           'δικαιοσύνης '
                                                                                           'μᾶλλον '
                                                                                           'εὐφό-ρεσαν '
                                                                                           'παραπτώμασιν. '
                                                                                           'The exact held '
                                                                                           'target ends in a '
                                                                                           'printed partial '
                                                                                           'word, and the '
                                                                                           'next retained '
                                                                                           'row begins '
                                                                                           'ρεσαν. Replacing '
                                                                                           'it with the '
                                                                                           'complete Henry '
                                                                                           'word would '
                                                                                           'duplicate that '
                                                                                           'continuation. '
                                                                                           'Preserve the '
                                                                                           'complete '
                                                                                           'diagnostic '
                                                                                           'reading and '
                                                                                           'require a joint '
                                                                                           'boundary review.',
                                                                               'held_reason': 'cross-row-word',
                                                                               'inherited_record_sha256': 'e8e5be2a6c9c45850e5b292b867da72746731c616dbfdce0dab33ee65896e106',
                                                                               'kind': 'individually-reviewed-remaining-reading',
                                                                               'original_row_sha256': '1389479ffa099a6e8a997fff24b69b2756cff14c342ab9dd2d2a7a510004be34',
                                                                               'original_text': 'μελλαν '
                                                                                                'εξφο-',
                                                                               'qualification': 'Explicit '
                                                                                                'editorial '
                                                                                                'preference '
                                                                                                'for the '
                                                                                                'supplied '
                                                                                                'Henry '
                                                                                                'edition, '
                                                                                                'not a claim '
                                                                                                'of Bekker '
                                                                                                'scan '
                                                                                                'agreement. '
                                                                                                'The '
                                                                                                'original '
                                                                                                'held text, '
                                                                                                'tentative '
                                                                                                'scan '
                                                                                                'observations, '
                                                                                                'contrary '
                                                                                                'digital '
                                                                                                'readings, '
                                                                                                'and '
                                                                                                'unrelated '
                                                                                                'verified '
                                                                                                'text remain '
                                                                                                'unchanged '
                                                                                                'in their '
                                                                                                'archived '
                                                                                                'layers. '
                                                                                                'Source '
                                                                                                'context is '
                                                                                                'diagnostic '
                                                                                                'and not a '
                                                                                                'new corpus '
                                                                                                'row.',
                                                                               'readings': [],
                                                                               'rendering': {},
                                                                               'reviewed_at': '2026-10-21T23:14:05.501170Z',
                                                                               'role': 'authorial-body',
                                                                               'source_context': {'qualification': 'Explicit '
                                                                                                                   'editorial '
                                                                                                                   'preference '
                                                                                                                   'for '
                                                                                                                   'the '
                                                                                                                   'supplied '
                                                                                                                   'Henry '
                                                                                                                   'edition, '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'claim '
                                                                                                                   'of '
                                                                                                                   'Bekker '
                                                                                                                   'scan '
                                                                                                                   'agreement. '
                                                                                                                   'The '
                                                                                                                   'original '
                                                                                                                   'held '
                                                                                                                   'text, '
                                                                                                                   'tentative '
                                                                                                                   'scan '
                                                                                                                   'observations, '
                                                                                                                   'contrary '
                                                                                                                   'digital '
                                                                                                                   'readings, '
                                                                                                                   'and '
                                                                                                                   'unrelated '
                                                                                                                   'verified '
                                                                                                                   'text '
                                                                                                                   'remain '
                                                                                                                   'unchanged '
                                                                                                                   'in '
                                                                                                                   'their '
                                                                                                                   'archived '
                                                                                                                   'layers. '
                                                                                                                   'Source '
                                                                                                                   'context '
                                                                                                                   'is '
                                                                                                                   'diagnostic '
                                                                                                                   'and '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'new '
                                                                                                                   'corpus '
                                                                                                                   'row.',
                                                                                                  'sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                                                  'source_id': 'tlg-photius-henry',
                                                                                                  'units': [{'bekker': '309b',
                                                                                                             'codex': '237',
                                                                                                             'html_column': 63,
                                                                                                             'html_line': 19061,
                                                                                                             'text': 'θύμησαν. '
                                                                                                                     'Διὸ '
                                                                                                                     'δὴ '
                                                                                                                     'καὶ '
                                                                                                                     'ἰσάριθμοι '
                                                                                                                     'πρὸς '
                                                                                                                     'εʹ '
                                                                                                                     'διαιροῦνται, \n'
                                                                                                                     'ἐπειδήπερ '
                                                                                                                     'τὰς '
                                                                                                                     'πέντε '
                                                                                                                     'αἰσθήσεις '
                                                                                                                     'αἱ '
                                                                                                                     'μὲν '
                                                                                                                     'αὐτῶν '
                                                                                                                     'ἐφυλάξαντο \n'
                                                                                                                     'καθαράς, '
                                                                                                                     'ἃς '
                                                                                                                     'οἱ '
                                                                                                                     'πλεῖστοι '
                                                                                                                     'σοφίας '
                                                                                                                     'πύλας '
                                                                                                                     'προσηγόρευσαν, \n'
                                                                                                                     'αἱ '
                                                                                                                     'δὲ '
                                                                                                                     'τοὐναντίον '
                                                                                                                     'κατελωβήσαντο '
                                                                                                                     'κακίᾳ. '
                                                                                                                     'Ἐγκρατευσά‐ \n'
                                                                                                                     'μεναι '
                                                                                                                     'γὰρ '
                                                                                                                     'καὶ '
                                                                                                                     'ἁγνεύσασαι '
                                                                                                                     'δικαιοσύνης '
                                                                                                                     'μᾶλλον '
                                                                                                                     'εὐφό‐',
                                                                                                             'unit_index': 7976},
                                                                                                            {'bekker': '309b',
                                                                                                             'codex': '237',
                                                                                                             'html_column': 63,
                                                                                                             'html_line': 19065,
                                                                                                             'text': 'ρεσαν '
                                                                                                                     'παραπτώμασιν· '
                                                                                                                     'ἐξ '
                                                                                                                     'οὗ '
                                                                                                                     'καὶ '
                                                                                                                     'συνέβη '
                                                                                                                     'αὐτὰς '
                                                                                                                     'ἀπαγο‐ \n'
                                                                                                                     'ρευθῆναι. '
                                                                                                                     'Εἴτε '
                                                                                                                     'γὰρ '
                                                                                                                     'κατορθοῦμεν, '
                                                                                                                     'εἴτε '
                                                                                                                     'πλημμελοῦμεν, '
                                                                                                                     'διὰ \n'
                                                                                                                     'τούτων '
                                                                                                                     'ἑκάτερα '
                                                                                                                     'καὶ '
                                                                                                                     'τὰ '
                                                                                                                     'ἀνδραγαθήματα '
                                                                                                                     'κρατύνεται '
                                                                                                                     'καὶ \n'
                                                                                                                     'τὰ '
                                                                                                                     'κακὰ '
                                                                                                                     'πράγματα. '
                                                                                                                     'Καὶ '
                                                                                                                     'ὥσπερ '
                                                                                                                     'ἡ '
                                                                                                                     'Θάλλουσα '
                                                                                                                     'καὶ '
                                                                                                                     'ὀφθαλ‐ \n'
                                                                                                                     'μῶν '
                                                                                                                     'ἁγνείαν '
                                                                                                                     'ἔφη '
                                                                                                                     'καὶ '
                                                                                                                     'ὤτων '
                                                                                                                     'εἶναι '
                                                                                                                     'καὶ '
                                                                                                                     'γλώσσης '
                                                                                                                     'καὶ '
                                                                                                                     'τῶν',
                                                                                                             'unit_index': 7977},
                                                                                                            {'bekker': '309b',
                                                                                                             'codex': '237',
                                                                                                             'html_column': 64,
                                                                                                             'html_line': 19069,
                                                                                                             'text': 'λοιπῶν '
                                                                                                                     'καθεξῆς '
                                                                                                                     'αἰσθητηρίων, '
                                                                                                                     'οὕτω '
                                                                                                                     'δὴ '
                                                                                                                     'καὶ '
                                                                                                                     'τὰ '
                                                                                                                     'ἐνταῦθα \n'
                                                                                                                     'τὴν '
                                                                                                                     'πίστιν '
                                                                                                                     'ἄσυλον '
                                                                                                                     'ἡ '
                                                                                                                     'φυλαξαμένη '
                                                                                                                     'τῶν '
                                                                                                                     'πέντε '
                                                                                                                     'διόδων '
                                                                                                                     'τῆς \n'
                                                                                                                     'ἀρετῆς, '
                                                                                                                     'ὁράσεως, '
                                                                                                                     'γεύσεως, '
                                                                                                                     'ὀσφρήσεως, '
                                                                                                                     'ἁφῆς '
                                                                                                                     'τε '
                                                                                                                     'καὶ \n'
                                                                                                                     'ἀκοῆς, '
                                                                                                                     'πέντε '
                                                                                                                     'προσαγορεύεται '
                                                                                                                     'παρθένοι, '
                                                                                                                     'διὰ '
                                                                                                                     'τὸ '
                                                                                                                     'τὰς \n'
                                                                                                                     'πέντε '
                                                                                                                     'τῆς '
                                                                                                                     'αἰσθήσεως '
                                                                                                                     'ἁγνὰς '
                                                                                                                     'ἀποκαταστῆσαι '
                                                                                                                     'τῷ '
                                                                                                                     'Χριστῷ',
                                                                                                             'unit_index': 7978}],
                                                                                                  'units_sha256': 'd3931164e0c7f6a6e412445b3863e1953b90c86dc537a49f0d9e57b29ed08ef9'},
                                                                               'source_indices': [],
                                                                               'status': 'held',
                                                                               'surface_sha256': None}},
                                                  'original_text': 'μελλαν εξφο-',
                                                  'readings': [],
                                                  'reason': 'individually-held-reading',
                                                  'segment_index': 1}}],
  'surface_sha256': '5ca223a52b9a64498c61044dde62e4e43e15052d9f9cf00e9ba90a9ea298024a'},
 {'id': 'boundary-0069.21',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.21',
                  'segment_index': 0,
                  'start': 0,
                  'end': 36,
                  'original_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
                  'inherited_record_sha256': '293d6b65795a9c8ffafd84a9b9c4eb3e5fd852f4b1ebe131f21b0ca5082414b9',
                  'original_segment_sha256': 'fb7aafd3cda4d8210f17f745d1a01df911bf914fd10bf8e2f5265d2107791e2d'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.20',
             'start': 45,
             'end': 48,
             'original_text': 'χί-',
             'corrected_text': '',
             'original_row_sha256': '8f57c3dc52b53e1474bd2c09d2e013c9da5866106e4d1ab68f184873177c8203'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.21',
             'start': 0,
             'end': 36,
             'original_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
             'corrected_text': 'σχίζεσθαι. Ἀλλ’ ὅμως, οὕτω μὲν χαρακώσαντες τὸν',
             'original_row_sha256': 'cf2f1f5fc7382087c2fb9aeb5098d06bc177c04aff862b57910defcb764fd777'}],
  'evidence': 'The Delta sentence ends the preceding physical line Νεῖλον χί- and resumes ζεσθαι before ἀλλ’ '
              'ὅμως. The current whole held row lacks that suffix. Henry prints σχί-ζεσθαι, followed by the '
              'entire same clause; replace the whole held row with its attributed clause and remove the '
              'surviving OCR prefix once. The χί-/σχί- difference is an editorial variant, not scan '
              'certification.',
  'scan': {'image_sha256': '334f1901250e4c177c76a8882247e3d0d517058ff1268abc6447758ddc56f427',
           'max_side': 3600,
           'observed_text': 'Νεῖλον χί-\nζεσθαι. ἀλλ’ ὅμως, οὕτω μὲν χαρακώσαντες τὸν',
           'physical_page': 69,
           'printed_page': 334,
           'region': [0.55, 0.095, 0.95, 0.77],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 8539,
                'stop': 8543,
                'units_sha256': '23cfab471f9cc305cd562ef9566f356147519725e77dc27c5b3faedaf2325ab3',
                'units': [{'text': 'γος, εἰ συμβουλεύοιμι αὐτῷ μὴ κυβιστᾶν ἐπ’ ὀρθὰ ξίφη, \n'
                                   'μηδ’ ἀναρρίπτειν πρὸς τυραννίδα, ἧς οὔπω χαλεπω‐ \n'
                                   'τέρα». Ὅ τι μὲν γὰρ ψηφιεῖται ἐπί σοι, οὐκ οἶδα· διά‐ \n'
                                   'κειται δὲ ὥσπερ οἱ καταψηφίσασθαι μὲν ἐπιθυμοῦντες, \n'
                                   'αἰσχυνόμενοι δὲ τὸ μὴ ἐπ’ ἀληθέσι, καὶ πρόφασιν ἀπω‐',
                           'html_line': 20558,
                           'html_column': 66,
                           'unit_index': 8539,
                           'codex': '241',
                           'bekker': '334b'},
                          {'text': 'λείας ὑπάτων ἀνδρῶν ποιεῖταί σε. Βούλεται μὲν γὰρ ἃ μὴ \n'
                                   'δεῖ, πράττει δὲ αὐτὰ καταρρυθμίζων εἰς τὴν τοῦ δι‐ \n'
                                   'καίου δόξαν. Ἔλεγε δ’ αὐτὰ μασώμενός τε καὶ ξυγ‐ \n'
                                   'γελῶν. Ὁ δὲ οὐκ ἀκηκοότι ὅμοιος διελέγετο πρὸς τὸν \n'
                                   'Δάμιν ὑπὲρ τοῦ Δέλτα, περὶ ὅ φασι τὸν Νεῖλον σχί‐',
                           'html_line': 20562,
                           'html_column': 66,
                           'unit_index': 8540,
                           'codex': '241',
                           'bekker': '334b'},
                          {'text': 'ζεσθαι. Ἀλλ’ ὅμως, οὕτω μὲν χαρακώσαντες τὸν \n'
                                   'πλοῦτον, οὕτω δὲ ἀσφαλῶς τειχισάμενοι, κινδυνεύομεν \n'
                                   'περὶ αὐτῷ νῦν. Οἰκίας τε ἐπὶ τῶν ἁμαξῶν πέ‐ \n'
                                   'πανται. Ἴστροι τε γὰρ αὐτοὺς καὶ Τανάϊδες ὁρίζουσιν, \n'
                                   'οὐ ῥᾴδιοι ποταμοὶ ὑπερβῆναι. Ἑώρων μὲν δὴ ἐς',
                           'html_line': 20566,
                           'html_column': 98,
                           'unit_index': 8541,
                           'codex': '241',
                           'bekker': '334b'},
                          {'text': 'τὸν Ἀπολλώνιον πάντες· αὐτοῦ τε γὰρ τοῦ σχήματος ἀπε‐ \n'
                                   'βλέπετο, καὶ θεία ἐδόκει ἡ περὶ τῷ εἴδει ἔκπληξις. \n'
                                   '    Ὑπὲρ μὲν τῆς κουρᾶς· «Ἐλελήθειν, ὦ βασιλεῦ, ἔφη, \n'
                                   'περὶ ταῖς θριξὶ κινδυνεύων». Δεδεμένου τοῦ Ἀπολ‐ \n'
                                   'λωνίου ἀφικνεῖταί τις ἐς τὸ δεσμωτήριον τὸ προσ‐',
                           'html_line': 20570,
                           'html_column': 58,
                           'unit_index': 8542,
                           'codex': '241',
                           'bekker': '334b'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'σχίζεσθαι Ἀλλ’ ὅμως οὕτω μὲν χαρακώσαντες τὸν',
              'refs': [{'html_line': 20562,
                        'html_column': 66,
                        'unit_index': 8540,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 255,
                        'end': 258},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 0,
                        'end': 6},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 8,
                        'end': 12},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 13,
                        'end': 17},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 19,
                        'end': 23},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 24,
                        'end': 27},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 28,
                        'end': 40},
                       {'html_line': 20566,
                        'html_column': 98,
                        'unit_index': 8541,
                        'codex': '241',
                        'bekker': '334b',
                        'start': 41,
                        'end': 44}],
              'tokens': [{'text': 'σχίζεσθαι',
                          'refs': [{'html_line': 20562,
                                    'html_column': 66,
                                    'unit_index': 8540,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 255,
                                    'end': 258},
                                   {'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 0,
                                    'end': 6}],
                          'source_index': 212409},
                         {'text': 'Ἀλλ’',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 8,
                                    'end': 12}],
                          'source_index': 212410},
                         {'text': 'ὅμως',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 13,
                                    'end': 17}],
                          'source_index': 212411},
                         {'text': 'οὕτω',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 19,
                                    'end': 23}],
                          'source_index': 212412},
                         {'text': 'μὲν',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 24,
                                    'end': 27}],
                          'source_index': 212413},
                         {'text': 'χαρακώσαντες',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 28,
                                    'end': 40}],
                          'source_index': 212414},
                         {'text': 'τὸν',
                          'refs': [{'html_line': 20566,
                                    'html_column': 98,
                                    'unit_index': 8541,
                                    'codex': '241',
                                    'bekker': '334b',
                                    'start': 41,
                                    'end': 44}],
                          'source_index': 212415}],
              'surface': 'σχίζεσθαι. Ἀλλ’ ὅμως, οὕτω μὲν χαρακώσαντες τὸν',
              'separators': [{'pieces': [{'text': '. ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 6,
                                                  'end': 8}}],
                              'rendered': '. '},
                             {'pieces': [{'text': ' ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 12,
                                                  'end': 13}}],
                              'rendered': ' '},
                             {'pieces': [{'text': ', ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 17,
                                                  'end': 19}}],
                              'rendered': ', '},
                             {'pieces': [{'text': ' ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 23,
                                                  'end': 24}}],
                              'rendered': ' '},
                             {'pieces': [{'text': ' ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 27,
                                                  'end': 28}}],
                              'rendered': ' '},
                             {'pieces': [{'text': ' ',
                                          'ref': {'html_line': 20566,
                                                  'html_column': 98,
                                                  'node_index': 8636,
                                                  'codex': '241',
                                                  'bekker': '334b',
                                                  'start': 40,
                                                  'end': 41}}],
                              'rendered': ' '}],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.21',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 36,
                                              'corrected_start': 0,
                                              'corrected_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
                                              'end': 36,
                                              'evidence': 'Every retained word and unchanged span was '
                                                          'directly compared with Bekker physical page 69 / '
                                                          'printed page 334. Both body columns and enlarged '
                                                          'strips were inspected. The digital witness is '
                                                          'separately retained, including contrary readings.',
                                              'fragments': [],
                                              'original_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': 'd0e8697db9417b73a163e2def3fb2296875996ddd91c77fed2f2c70edb6792bd',
                                                            'text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν"},
                                                           {'image_sha256': '334f1901250e4c177c76a8882247e3d0d517058ff1268abc6447758ddc56f427',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 69,
                                                            'region': [0.55, 0.095, 0.95, 0.77],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'ζε[σ?]θαι. ἀλλ’ ὅμως, οὕτω μὲν '
                                                                    'χαρακώσαντες τὸν'},
                                                           {'boundary_fragments': [{'end': 6,
                                                                                    'full_token': {'end': 2729,
                                                                                                   'start': 2721,
                                                                                                   'text': 'χίζεσθαι'},
                                                                                    'start': 0,
                                                                                    'text': 'ζεσθαι'}],
                                                            'end': 2767,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s346',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2723,
                                                            'text': 'ζεσθαι. ἀλλ’ ὅμως, οὕτω μὲν '
                                                                    'χαρακώσαντες τὸν'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:10:57Z',
                                              'scan': {'image_sha256': '334f1901250e4c177c76a8882247e3d0d517058ff1268abc6447758ddc56f427',
                                                       'max_side': 3600,
                                                       'observed_text': 'ζε[σ?]θαι. ἀλλ’ ὅμως, οὕτω μὲν '
                                                                        'χαρακώσαντες τὸν',
                                                       'physical_page': 69,
                                                       'printed_page': 334,
                                                       'region': [0.55, 0.095, 0.95, 0.77],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand directly identified ου, '
                                                                          'στ, καὶ and γὰρ type. Preserve '
                                                                          'unresolved type as explicit '
                                                                          'uncertainty. Join internal line '
                                                                          'divisions only within a retained '
                                                                          'passage; preserve boundary '
                                                                          'fragments. Distinguish marginal '
                                                                          'references and line numbers from '
                                                                          'body text. Keep declared '
                                                                          'quotation delimiters.',
                                              'uncertainty': 'The earlier OCR omitted the printed leading '
                                                             'word fragment; the compact source ending '
                                                             'remains unresolved. Hold the exact original '
                                                             'row and preserve the complete observed '
                                                             'alternative.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
                                                  'decision': 'retained',
                                                  'evidence': 'The source moves from περὶ ὅ φασι τὸν Νεῖλον '
                                                              'σχί-ζεσθαι to Ἀλλ’ ὅμως, οὕτω μὲν '
                                                              'χαρακώσαντες τὸν πλοῦτον. The original scan '
                                                              'record explicitly includes a missing leading '
                                                              'ζε[σ?]θαι in this retained row, after the '
                                                              'previous retained row ends χί-. Selecting '
                                                              'only the existing whole words would retire a '
                                                              'known omitted-fragment qualification. Keep '
                                                              'this counterpart diagnostic until a joint '
                                                              'boundary repair accounts for the missing '
                                                              'fragment.',
                                                  'location_evidence': {'source_sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                        'status': 'held-no-immediate-reliable-boundaries'},
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0069.21',
                                                  'manual_review': {'module': 'photius_remaining_manual_a',
                                                                    'review': {'diagnostic_readings': [{'location_basis': 'Individually '
                                                                                                                          'read '
                                                                                                                          'named '
                                                                                                                          'or '
                                                                                                                          'sentence-level '
                                                                                                                          'surrounding '
                                                                                                                          'source '
                                                                                                                          'context.',
                                                                                                        'refs': [{'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 12,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 8,
                                                                                                                  'unit_index': 8541},
                                                                                                                 {'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 17,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 13,
                                                                                                                  'unit_index': 8541},
                                                                                                                 {'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 23,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 19,
                                                                                                                  'unit_index': 8541},
                                                                                                                 {'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 27,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 24,
                                                                                                                  'unit_index': 8541},
                                                                                                                 {'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 40,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 28,
                                                                                                                  'unit_index': 8541},
                                                                                                                 {'bekker': '334b',
                                                                                                                  'codex': '241',
                                                                                                                  'end': 44,
                                                                                                                  'html_column': 98,
                                                                                                                  'html_line': 20566,
                                                                                                                  'start': 41,
                                                                                                                  'unit_index': 8541}],
                                                                                                        'role': 'alternative',
                                                                                                        'source_id': 'tlg-photius-henry',
                                                                                                        'text': 'Ἀλλ’ '
                                                                                                                'ὅμως '
                                                                                                                'οὕτω '
                                                                                                                'μὲν '
                                                                                                                'χαρακώσαντες '
                                                                                                                'τὸν',
                                                                                                        'tokens': [{'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 12,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 8,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'Ἀλλ’'},
                                                                                                                   {'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 17,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 13,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'ὅμως'},
                                                                                                                   {'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 23,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 19,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'οὕτω'},
                                                                                                                   {'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 27,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 24,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'μὲν'},
                                                                                                                   {'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 40,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 28,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'χαρακώσαντες'},
                                                                                                                   {'refs': [{'bekker': '334b',
                                                                                                                              'codex': '241',
                                                                                                                              'end': 44,
                                                                                                                              'html_column': 98,
                                                                                                                              'html_line': 20566,
                                                                                                                              'start': 41,
                                                                                                                              'unit_index': 8541}],
                                                                                                                    'text': 'τὸν'}]}],
                                                                               'evidence': 'The source moves '
                                                                                           'from περὶ ὅ φασι '
                                                                                           'τὸν Νεῖλον '
                                                                                           'σχί-ζεσθαι to '
                                                                                           'Ἀλλ’ ὅμως, οὕτω '
                                                                                           'μὲν χαρακώσαντες '
                                                                                           'τὸν πλοῦτον. The '
                                                                                           'original scan '
                                                                                           'record '
                                                                                           'explicitly '
                                                                                           'includes a '
                                                                                           'missing leading '
                                                                                           'ζε[σ?]θαι in '
                                                                                           'this retained '
                                                                                           'row, after the '
                                                                                           'previous '
                                                                                           'retained row '
                                                                                           'ends χί-. '
                                                                                           'Selecting only '
                                                                                           'the existing '
                                                                                           'whole words '
                                                                                           'would retire a '
                                                                                           'known '
                                                                                           'omitted-fragment '
                                                                                           'qualification. '
                                                                                           'Keep this '
                                                                                           'counterpart '
                                                                                           'diagnostic until '
                                                                                           'a joint boundary '
                                                                                           'repair accounts '
                                                                                           'for the missing '
                                                                                           'fragment.',
                                                                               'held_reason': 'omitted-leading-word-fragment',
                                                                               'inherited_record_sha256': '426e42820b39fd5d1163f171257513df04e5607084f711e53a7d00692990f2fd',
                                                                               'kind': 'individually-reviewed-remaining-reading',
                                                                               'original_row_sha256': 'ec56de9d5cee831097f055aef2ca94371d147069223ae742d25ddf05ef2871bc',
                                                                               'original_text': "ἀλλ' ὅμως, "
                                                                                                'οὕτω μὲν '
                                                                                                'χαρακώσαντες '
                                                                                                'τὸν',
                                                                               'qualification': 'Explicit '
                                                                                                'editorial '
                                                                                                'preference '
                                                                                                'for the '
                                                                                                'supplied '
                                                                                                'Henry '
                                                                                                'edition, '
                                                                                                'not a claim '
                                                                                                'of Bekker '
                                                                                                'scan '
                                                                                                'agreement. '
                                                                                                'The '
                                                                                                'original '
                                                                                                'held text, '
                                                                                                'tentative '
                                                                                                'scan '
                                                                                                'observations, '
                                                                                                'contrary '
                                                                                                'digital '
                                                                                                'readings, '
                                                                                                'and '
                                                                                                'unrelated '
                                                                                                'verified '
                                                                                                'text remain '
                                                                                                'unchanged '
                                                                                                'in their '
                                                                                                'archived '
                                                                                                'layers. '
                                                                                                'Source '
                                                                                                'context is '
                                                                                                'diagnostic '
                                                                                                'and not a '
                                                                                                'new corpus '
                                                                                                'row.',
                                                                               'readings': [],
                                                                               'rendering': {},
                                                                               'reviewed_at': '2026-10-21T23:14:05.501170Z',
                                                                               'role': 'authorial-body',
                                                                               'source_context': {'qualification': 'Explicit '
                                                                                                                   'editorial '
                                                                                                                   'preference '
                                                                                                                   'for '
                                                                                                                   'the '
                                                                                                                   'supplied '
                                                                                                                   'Henry '
                                                                                                                   'edition, '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'claim '
                                                                                                                   'of '
                                                                                                                   'Bekker '
                                                                                                                   'scan '
                                                                                                                   'agreement. '
                                                                                                                   'The '
                                                                                                                   'original '
                                                                                                                   'held '
                                                                                                                   'text, '
                                                                                                                   'tentative '
                                                                                                                   'scan '
                                                                                                                   'observations, '
                                                                                                                   'contrary '
                                                                                                                   'digital '
                                                                                                                   'readings, '
                                                                                                                   'and '
                                                                                                                   'unrelated '
                                                                                                                   'verified '
                                                                                                                   'text '
                                                                                                                   'remain '
                                                                                                                   'unchanged '
                                                                                                                   'in '
                                                                                                                   'their '
                                                                                                                   'archived '
                                                                                                                   'layers. '
                                                                                                                   'Source '
                                                                                                                   'context '
                                                                                                                   'is '
                                                                                                                   'diagnostic '
                                                                                                                   'and '
                                                                                                                   'not '
                                                                                                                   'a '
                                                                                                                   'new '
                                                                                                                   'corpus '
                                                                                                                   'row.',
                                                                                                  'sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                                                  'source_id': 'tlg-photius-henry',
                                                                                                  'units': [{'bekker': '334b',
                                                                                                             'codex': '241',
                                                                                                             'html_column': 66,
                                                                                                             'html_line': 20562,
                                                                                                             'text': 'λείας '
                                                                                                                     'ὑπάτων '
                                                                                                                     'ἀνδρῶν '
                                                                                                                     'ποιεῖταί '
                                                                                                                     'σε. '
                                                                                                                     'Βούλεται '
                                                                                                                     'μὲν '
                                                                                                                     'γὰρ '
                                                                                                                     'ἃ '
                                                                                                                     'μὴ \n'
                                                                                                                     'δεῖ, '
                                                                                                                     'πράττει '
                                                                                                                     'δὲ '
                                                                                                                     'αὐτὰ '
                                                                                                                     'καταρρυθμίζων '
                                                                                                                     'εἰς '
                                                                                                                     'τὴν '
                                                                                                                     'τοῦ '
                                                                                                                     'δι‐ \n'
                                                                                                                     'καίου '
                                                                                                                     'δόξαν. '
                                                                                                                     'Ἔλεγε '
                                                                                                                     'δ’ '
                                                                                                                     'αὐτὰ '
                                                                                                                     'μασώμενός '
                                                                                                                     'τε '
                                                                                                                     'καὶ '
                                                                                                                     'ξυγ‐ \n'
                                                                                                                     'γελῶν. '
                                                                                                                     'Ὁ '
                                                                                                                     'δὲ '
                                                                                                                     'οὐκ '
                                                                                                                     'ἀκηκοότι '
                                                                                                                     'ὅμοιος '
                                                                                                                     'διελέγετο '
                                                                                                                     'πρὸς '
                                                                                                                     'τὸν \n'
                                                                                                                     'Δάμιν '
                                                                                                                     'ὑπὲρ '
                                                                                                                     'τοῦ '
                                                                                                                     'Δέλτα, '
                                                                                                                     'περὶ '
                                                                                                                     'ὅ '
                                                                                                                     'φασι '
                                                                                                                     'τὸν '
                                                                                                                     'Νεῖλον '
                                                                                                                     'σχί‐',
                                                                                                             'unit_index': 8540},
                                                                                                            {'bekker': '334b',
                                                                                                             'codex': '241',
                                                                                                             'html_column': 98,
                                                                                                             'html_line': 20566,
                                                                                                             'text': 'ζεσθαι. '
                                                                                                                     'Ἀλλ’ '
                                                                                                                     'ὅμως, '
                                                                                                                     'οὕτω '
                                                                                                                     'μὲν '
                                                                                                                     'χαρακώσαντες '
                                                                                                                     'τὸν \n'
                                                                                                                     'πλοῦτον, '
                                                                                                                     'οὕτω '
                                                                                                                     'δὲ '
                                                                                                                     'ἀσφαλῶς '
                                                                                                                     'τειχισάμενοι, '
                                                                                                                     'κινδυνεύομεν \n'
                                                                                                                     'περὶ '
                                                                                                                     'αὐτῷ '
                                                                                                                     'νῦν. '
                                                                                                                     'Οἰκίας '
                                                                                                                     'τε '
                                                                                                                     'ἐπὶ '
                                                                                                                     'τῶν '
                                                                                                                     'ἁμαξῶν '
                                                                                                                     'πέ‐ \n'
                                                                                                                     'πανται. '
                                                                                                                     'Ἴστροι '
                                                                                                                     'τε '
                                                                                                                     'γὰρ '
                                                                                                                     'αὐτοὺς '
                                                                                                                     'καὶ '
                                                                                                                     'Τανάϊδες '
                                                                                                                     'ὁρίζουσιν, \n'
                                                                                                                     'οὐ '
                                                                                                                     'ῥᾴδιοι '
                                                                                                                     'ποταμοὶ '
                                                                                                                     'ὑπερβῆναι. '
                                                                                                                     'Ἑώρων '
                                                                                                                     'μὲν '
                                                                                                                     'δὴ '
                                                                                                                     'ἐς',
                                                                                                             'unit_index': 8541},
                                                                                                            {'bekker': '334b',
                                                                                                             'codex': '241',
                                                                                                             'html_column': 58,
                                                                                                             'html_line': 20570,
                                                                                                             'text': 'τὸν '
                                                                                                                     'Ἀπολλώνιον '
                                                                                                                     'πάντες· '
                                                                                                                     'αὐτοῦ '
                                                                                                                     'τε '
                                                                                                                     'γὰρ '
                                                                                                                     'τοῦ '
                                                                                                                     'σχήματος '
                                                                                                                     'ἀπε‐ \n'
                                                                                                                     'βλέπετο, '
                                                                                                                     'καὶ '
                                                                                                                     'θεία '
                                                                                                                     'ἐδόκει '
                                                                                                                     'ἡ '
                                                                                                                     'περὶ '
                                                                                                                     'τῷ '
                                                                                                                     'εἴδει '
                                                                                                                     'ἔκπληξις. \n'
                                                                                                                     '    '
                                                                                                                     'Ὑπὲρ '
                                                                                                                     'μὲν '
                                                                                                                     'τῆς '
                                                                                                                     'κουρᾶς· '
                                                                                                                     '«Ἐλελήθειν, '
                                                                                                                     'ὦ '
                                                                                                                     'βασιλεῦ, '
                                                                                                                     'ἔφη, \n'
                                                                                                                     'περὶ '
                                                                                                                     'ταῖς '
                                                                                                                     'θριξὶ '
                                                                                                                     'κινδυνεύων». '
                                                                                                                     'Δεδεμένου '
                                                                                                                     'τοῦ '
                                                                                                                     'Ἀπολ‐ \n'
                                                                                                                     'λωνίου '
                                                                                                                     'ἀφικνεῖταί '
                                                                                                                     'τις '
                                                                                                                     'ἐς '
                                                                                                                     'τὸ '
                                                                                                                     'δεσμωτήριον '
                                                                                                                     'τὸ '
                                                                                                                     'προσ‐',
                                                                                                             'unit_index': 8542}],
                                                                                                  'units_sha256': 'cc82c9a8be86ec6265b0f762a56c0aa9842bcae82a76026a3c246f7a015d1fba'},
                                                                               'source_indices': [],
                                                                               'status': 'held',
                                                                               'surface_sha256': None}},
                                                  'original_text': "ἀλλ' ὅμως, οὕτω μὲν χαρακώσαντες τὸν",
                                                  'readings': [],
                                                  'reason': 'individually-held-reading',
                                                  'segment_index': 0}}],
  'surface_sha256': '171f4301eb021006adf950f1b62c6fd464ad72843fcc151bdc54d97600e102c3'},
 {'id': 'boundary-0154.30',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.30',
                  'segment_index': 1,
                  'start': 42,
                  'end': 49,
                  'original_text': 'πειθόν-',
                  'inherited_record_sha256': '704d3f18030196427ad4ec12df9860171a609bf9d47ad356f65dbfb0e02faa10',
                  'original_segment_sha256': '0b4e4541fef3a807e23e1edbff369a7899da18d715cd2859edbd9cc81fe830c9'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.30',
             'start': 42,
             'end': 49,
             'original_text': 'πειθόν-',
             'corrected_text': 'πεισθέντων',
             'original_row_sha256': '8c68f0b5e86c4f1d54dcf61d725c3ac9911d2f5280edf6024da9a8b5caae5c22'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.31',
             'start': 0,
             'end': 3,
             'original_text': 'των',
             'corrected_text': '',
             'original_row_sha256': '74d36980873dbcc9dc2d1dfc6dc28df8f67afa261a8fdf4da803ee1133936c9d'}],
  'evidence': 'The source has πεισθέν- at the line end and των at the beginning of the next line before '
              'ἀρετῆς. Reconstruct the complete supplied-edition πεισθέντων once in the first row; keep the '
              'compact scan letterforms and prior πειθόν- as contrary raw observations.',
  'scan': {'image_sha256': 'cac8512827e80f16545e1e268f9a945973bba2a0fdfd92bcbb8edb2cc3311b0b',
           'max_side': 3600,
           'observed_text': 'πεισθέν-\nτων',
           'physical_page': 154,
           'printed_page': 419,
           'region': [0.045, 0.485, 0.425, 0.68],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 10826,
                'stop': 10830,
                'units_sha256': '73c2cbc0f81e4a926945756e9440277f89efbdcf62ed81c113ebf61620982ec1',
                'units': [{'text': 'ἦν',
                           'html_line': 25697,
                           'html_column': 42,
                           'unit_index': 10826,
                           'codex': '247',
                           'bekker': '419a'},
                          {'text': '] τὰ ἔργα κοσμεῖν ὧν \n'
                                   'τὴν πολιτείαν φαυλίζειν ἔστι· καὶ ἃ τῆς τῶν πεισθέν‐',
                           'html_line': 25697,
                           'html_column': 51,
                           'unit_index': 10827,
                           'codex': '247',
                           'bekker': '419a'},
                          {'text': 'των ἀρετῆς τίθεταί τις δείγματα, ταῦτα μὴ τῆς τῶν \n'
                                   'πεισάντων πρῶτον ἡγεῖσθαι;',
                           'html_line': 25698,
                           'html_column': 66,
                           'unit_index': 10828,
                           'codex': '247',
                           'bekker': '419a'},
                          {'text': 'Ἔγκειται μὲν \n[',
                           'html_line': 25699,
                           'html_column': 60,
                           'unit_index': 10829,
                           'codex': '247',
                           'bekker': '419a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'πεισθέντων',
              'refs': [{'html_line': 25697,
                        'html_column': 51,
                        'unit_index': 10827,
                        'codex': '247',
                        'bekker': '419a',
                        'start': 66,
                        'end': 73},
                       {'html_line': 25698,
                        'html_column': 66,
                        'unit_index': 10828,
                        'codex': '247',
                        'bekker': '419a',
                        'start': 0,
                        'end': 3}],
              'tokens': [{'text': 'πεισθέντων',
                          'refs': [{'html_line': 25697,
                                    'html_column': 51,
                                    'unit_index': 10827,
                                    'codex': '247',
                                    'bekker': '419a',
                                    'start': 66,
                                    'end': 73},
                                   {'html_line': 25698,
                                    'html_column': 66,
                                    'unit_index': 10828,
                                    'codex': '247',
                                    'bekker': '419a',
                                    'start': 0,
                                    'end': 3}],
                          'source_index': 264250}],
              'surface': 'πεισθέντων',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.30',
                                      'segment_index': 1},
                         'original_segment': {'corrected_end': 49,
                                              'corrected_start': 42,
                                              'corrected_text': 'πειθόν-',
                                              'end': 47,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 7,
                                                             'lexical_eligible': False,
                                                             'qualification': 'This retained passage ends '
                                                                              'within a visibly divided '
                                                                              'printed word; preserve the '
                                                                              'source fragment and exclude '
                                                                              'it from lexical counts.',
                                                             'side': 'trailing',
                                                             'start': 0,
                                                             'text': 'πειθόν-'}],
                                              'original_text': 'πειθόν-',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '238487b93b5d783fac42e2debdc97ca03d2c8e2610a188d24c4d25402b84a8ce',
                                                            'text': 'πειθόν-'},
                                                           {'image_sha256': 'cac8512827e80f16545e1e268f9a945973bba2a0fdfd92bcbb8edb2cc3311b0b',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 154,
                                                            'region': [0.045, 0.485, 0.425, 0.68],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'πεισθέν-'},
                                                           {'end': 1506,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s431',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 1454,
                                                            'text': 'τὴν δὲ πολιτείαν φαυλίζειν· καὶ ἃ τῆς '
                                                                    'τῶν πεισθέντων'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T12:42:30Z',
                                              'scan': {'image_sha256': 'cac8512827e80f16545e1e268f9a945973bba2a0fdfd92bcbb8edb2cc3311b0b',
                                                       'max_side': 3600,
                                                       'observed_text': 'πεισθέν-',
                                                       'physical_page': 154,
                                                       'printed_page': 419,
                                                       'region': [0.045, 0.485, 0.425, 0.68],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 40,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The sigma component of the compact σθ group '
                                                             'remains unresolved independently. Both source '
                                                             'and original are divided printed fragments; '
                                                             'neither may be counted as a standalone form.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'πειθόν-',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.30',
                                                  'original_text': 'πειθόν-',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 1}}],
  'surface_sha256': 'fcb558176b8abbaae4915e118422f1649d255dab0e21a191a13533086ddb14e8'},
 {'id': 'boundary-0170.1',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.1',
                  'segment_index': 1,
                  'start': 42,
                  'end': 50,
                  'original_text': 'ἀδικηθή-',
                  'inherited_record_sha256': 'f6095d1f4854be80cfc94802976bd2ccf26ddbcea1301f2b261a89b765e232de',
                  'original_segment_sha256': '71b758d6759702bec5a39516473fdc65e806e98ddc36fbb5d1ef58d3eaed3b1a'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.1',
             'start': 42,
             'end': 50,
             'original_text': 'ἀδικηθή-',
             'corrected_text': 'ἀδικεῖσθαι',
             'original_row_sha256': '98221c9e0ebcfaa4af0de0a3e6af0b5c4be4c55f9ff9b3c2a8e3bc6a7cb1e6c9'}],
  'evidence': 'Bekker prints complete ἀδικεῖσθαι on the first physical line after κατεψηφίσαντο; the next '
              'line starts τοῖς ἀνδράσι. The existing terminal hyphen is an OCR artifact, not a printed word '
              'division. Henry divides ἀδικεῖ-σθαι in its own layout but supplies the same complete word.',
  'scan': {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
           'max_side': 3600,
           'observed_text': 'ἀδικεῖσθαι',
           'physical_page': 170,
           'printed_page': 435,
           'region': [0.025, 0.105, 0.49, 0.34],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 11512,
                'stop': 11515,
                'units_sha256': 'ddf0379bbb06541e2bdea74c23ecce1a1e8763c43ca678c846c69b901319862c',
                'units': [{'text': '] φιλονείκως ὑπολαμβάνοντα διαλύειν \n'
                                   'ὡδὶ τὸν λόγον, ὅτι εἰ καλῶς καὶ τὰ δίκαια αὐτῶν Ἀθη‐ \n'
                                   'ναῖοι κατέγνωσαν, οὐκ ἦσαν ὑπ’ αὐτῶν διεφθαρμένοι· \n'
                                   'τὰ γὰρ δίκαια ἐποίουν. Οὐκοῦν οὐδὲ ἐκεῖνοι διεφθάρκεσαν· \n'
                                   'ὥστε εἰ δικαίως ἑάλωσαν, οὐδὲν ταύτῃ γε χείρους ἦσαν.',
                           'html_line': 26625,
                           'html_column': 98,
                           'unit_index': 11512,
                           'codex': '248',
                           'bekker': '434b'},
                          {'text': 'Εἰ δὲ ἀδίκως αὐτῶν ἐκεῖνοι κατεψηφίσαντο, ἀδικεῖ‐ \n'
                                   'σθαι τοῖς ἀνδράσι περίεστιν, ἀδικεῖν δὲ οὐδαμῶς· τοῖς δ’ \n'
                                   'ἀδικηθεῖσι βοηθεῖν, οὐκ ἐγκαλεῖν εἰκός ἐστιν. Εἰ δέ τοι \n'
                                   'καὶ μὴ δυνατὸν βοηθεῖν, ἀλλ’ οὐχὶ καὶ δίκαιον ἐγκα‐',
                           'html_line': 26629,
                           'html_column': 106,
                           'unit_index': 11513,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': 'λεῖν. Ἐγὼ δὲ ταῦτα μὲν τοῖς κομψοτέροις παρίημι· αὐ‐ \n'
                                   'τὸς δὲ τί φημι καὶ πῶς δέχομαι λόγον; Οὐκ ἔστι',
                           'html_line': 26632,
                           'html_column': 74,
                           'unit_index': 11514,
                           'codex': '248',
                           'bekker': '435a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'ἀδικεῖσθαι',
              'refs': [{'html_line': 26629,
                        'html_column': 106,
                        'unit_index': 11513,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 42,
                        'end': 48},
                       {'html_line': 26629,
                        'html_column': 106,
                        'unit_index': 11513,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 51,
                        'end': 55}],
              'tokens': [{'text': 'ἀδικεῖσθαι',
                          'refs': [{'html_line': 26629,
                                    'html_column': 106,
                                    'unit_index': 11513,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 42,
                                    'end': 48},
                                   {'html_line': 26629,
                                    'html_column': 106,
                                    'unit_index': 11513,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 51,
                                    'end': 55}],
                          'source_index': 274173}],
              'surface': 'ἀδικεῖσθαι',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.1',
                                      'segment_index': 1},
                         'original_segment': {'corrected_end': 50,
                                              'corrected_start': 42,
                                              'corrected_text': 'ἀδικηθή-',
                                              'end': 50,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 8,
                                                             'lexical_eligible': False,
                                                             'qualification': 'The unchanged uncertain '
                                                                              'original ends in an OCR '
                                                                              'hyphenated fragment. Its '
                                                                              'source candidate remains '
                                                                              'unresolved; preserve this '
                                                                              'original display and exclude '
                                                                              'it rather than asserting a '
                                                                              'complete lexical form.',
                                                             'side': 'trailing',
                                                             'start': 0,
                                                             'text': 'ἀδικηθή-'}],
                                              'original_text': 'ἀδικηθή-',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '56fa678791ece768be8a5f6da2a8a2d19b3a5f108af19e436d82f924751a8b20',
                                                            'text': 'ἀδικηθή-'},
                                                           {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 170,
                                                            'region': [0.025, 0.105, 0.49, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'ἀδικεῖσθαι'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:23:05.576924Z',
                                              'scan': {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                       'max_side': 3600,
                                                       'observed_text': 'ἀδικεῖσθαι',
                                                       'physical_page': 170,
                                                       'printed_page': 435,
                                                       'region': [0.025, 0.105, 0.49, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 42,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact sigma/theta group remains '
                                                             'unresolved; the original OCR hyphen does not '
                                                             'establish a complete source word.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'ἀδικηθή-',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.1',
                                                  'original_text': 'ἀδικηθή-',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 1}}],
  'surface_sha256': 'f25f951144eabb2edb80bccc99e773cba78895a90a85b9480cfb50e2d8dfc5c2'},
 {'id': 'boundary-0170.7',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.7',
                  'segment_index': 1,
                  'start': 43,
                  'end': 48,
                  'original_text': 'νικη-',
                  'inherited_record_sha256': 'd666de07eea817d3a6ea96c284f54395bed9233714fe7faab4b1e41487ee66bc',
                  'original_segment_sha256': 'd1f57feb87797ff344af344cd07e5b23d00cae5debf06904fd28e5b20b135e12'},
                 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.8',
                  'segment_index': 0,
                  'start': 0,
                  'end': 4,
                  'original_text': 'ντὸν',
                  'inherited_record_sha256': '12ca0918f6f296c755eabc0caa22e989ffd6911c792517a393a7404cd0788ffa',
                  'original_segment_sha256': '703448b0824d67a6b71959d851e329ab6f27f18d7b3554c78c703b8391cb19ce'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.7',
             'start': 43,
             'end': 48,
             'original_text': 'νικη-',
             'corrected_text': '',
             'original_row_sha256': '85ba13f00fce48ac623e3d11cf9eb146a5aad21425e5fed7e4810553b676c454'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.8',
             'start': 0,
             'end': 4,
             'original_text': 'ντὸν',
             'corrected_text': 'κἀκείνων',
             'original_row_sha256': 'e6df49389ca6d1abd6593065b3c2a86e1aa86e666c7d610bc623400531cf28f3'}],
  'evidence': 'At the row boundary the inspected Bekker lines show κἀκεί- followed by νων before ἢ σαφῶς. '
              'Henry’s exact word κἀκείνων has the same ordered context. The previous νικη-/ντὸν and '
              'tentative νικῶ-/ντων readings remain archived; no change is authorized to the different '
              'neighboring τῷ δήμῳ/toῦ δήμου clause.',
  'scan': {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
           'max_side': 3600,
           'observed_text': 'κἀκεί-\nνων',
           'physical_page': 170,
           'printed_page': 435,
           'region': [0.025, 0.105, 0.49, 0.34],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 11514,
                'stop': 11517,
                'units_sha256': '4bc9a88bd3901dca82726dfbe49ef54ed1b1ceb74ec1c1a073d0c58fb0e7fe16',
                'units': [{'text': 'λεῖν. Ἐγὼ δὲ ταῦτα μὲν τοῖς κομψοτέροις παρίημι· αὐ‐ \n'
                                   'τὸς δὲ τί φημι καὶ πῶς δέχομαι λόγον; Οὐκ ἔστι',
                           'html_line': 26632,
                           'html_column': 74,
                           'unit_index': 11514,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': 'δίκαιον ἅμα ἀμφοῖν κατηγορεῖν, καὶ τοῦ δήμου κἀκεί‐ \n'
                                   'νων· ἢ σαφῶς τοὺς ἑτέρους συκοφαντήσομεν. Εἰ μὲν γὰρ \n'
                                   'ὀρθῶς ἐκεῖνα κατεγνώσθη, ἠδίκουν μέν (ὡς ἔοικεν)',
                           'html_line': 26633,
                           'html_column': 54,
                           'unit_index': 11515,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': 'ἐκεῖνοι, τῷ δήμῳ δ’ ἃ προσήκει πέπρακται, ὥστε οὐχὶ \n'
                                   'δήπου ταῦτά γε δίκαιον κατηγορεῖν αὐτοῦ. [',
                           'html_line': 26635,
                           'html_column': 97,
                           'unit_index': 11516,
                           'codex': '248',
                           'bekker': '435a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'κἀκείνων',
              'refs': [{'html_line': 26633,
                        'html_column': 54,
                        'unit_index': 11515,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 45,
                        'end': 50},
                       {'html_line': 26633,
                        'html_column': 54,
                        'unit_index': 11515,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 53,
                        'end': 56}],
              'tokens': [{'text': 'κἀκείνων',
                          'refs': [{'html_line': 26633,
                                    'html_column': 54,
                                    'unit_index': 11515,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 45,
                                    'end': 50},
                                   {'html_line': 26633,
                                    'html_column': 54,
                                    'unit_index': 11515,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 53,
                                    'end': 56}],
                          'source_index': 274224}],
              'surface': 'κἀκείνων',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.7',
                                      'segment_index': 1},
                         'original_segment': {'corrected_end': 48,
                                              'corrected_start': 43,
                                              'corrected_text': 'νικη-',
                                              'end': 48,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 5,
                                                             'lexical_eligible': False,
                                                             'qualification': 'The unchanged uncertain '
                                                                              'original ends in an OCR '
                                                                              'hyphenated fragment. Its '
                                                                              'source candidate remains '
                                                                              'unresolved; preserve this '
                                                                              'original display and exclude '
                                                                              'it rather than asserting a '
                                                                              'complete lexical form.',
                                                             'side': 'trailing',
                                                             'start': 0,
                                                             'text': 'νικη-'}],
                                              'original_text': 'νικη-',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '85490c3777169a14e51d04884dcc8ec8a8ed7b768271d8fdc15d64bc585bea4c',
                                                            'text': 'νικη-'},
                                                           {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 170,
                                                            'region': [0.025, 0.105, 0.49, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'νικῶ-'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:23:05.576924Z',
                                              'scan': {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                       'max_side': 3600,
                                                       'observed_text': 'νικῶ-',
                                                       'physical_page': 170,
                                                       'printed_page': 435,
                                                       'region': [0.025, 0.105, 0.49, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 43,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact word ending is unresolved '
                                                             'independently at the printed division.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'νικη-',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.7',
                                                  'original_text': 'νικη-',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 1}},
                        {'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.8',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 4,
                                              'corrected_start': 0,
                                              'corrected_text': 'ντὸν',
                                              'end': 4,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 4,
                                                             'lexical_eligible': False,
                                                             'qualification': 'Printed continuation of a '
                                                                              'word begun on the preceding '
                                                                              'source line or page. Preserve '
                                                                              'the suffix without supplying '
                                                                              'missing letters or counting '
                                                                              'it as a standalone lexical '
                                                                              'form.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'ντὸν'}],
                                              'original_text': 'ντὸν',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': 'b0510f51a2b13f25cb01ee4486aef0c99f5f58728d8115a347dbc85f5250989e',
                                                            'text': 'ντὸν'},
                                                           {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 170,
                                                            'region': [0.025, 0.105, 0.49, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'ντων'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:23:05.576924Z',
                                              'scan': {'image_sha256': 'e7b6f5b79db73443107336aa0950ca70589d01af6cd5254d561a9ec91a156af3',
                                                       'max_side': 3600,
                                                       'observed_text': 'ντων',
                                                       'physical_page': 170,
                                                       'printed_page': 435,
                                                       'region': [0.025, 0.105, 0.49, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The printed continuation and accent remain '
                                                             'unresolved independently.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'ντὸν',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.8',
                                                  'original_text': 'ντὸν',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': '653c6bc73dd7ac4cb090522e82eefe16ce1e8d1d1473943482eff6e097dacee3'},
 {'id': 'boundary-0170.25',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.25',
                  'segment_index': 0,
                  'start': 0,
                  'end': 8,
                  'original_text': 'μιζομένη',
                  'inherited_record_sha256': '929b20c7a8281667f58dc8f16f0479c31412f9f4d6260715dd571308070b59cb',
                  'original_segment_sha256': '743cd5b4a989fcf425c8e963cb0e647d91c6493ee5aeb1f1583af7d3a9756a24'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.24',
             'start': 49,
             'end': 52,
             'original_text': 'νο-',
             'corrected_text': '',
             'original_row_sha256': 'c5392d2b3091f5cce144649b3e12f98361058a6ae8ae7cdaad036388e53d4c87'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.25',
             'start': 0,
             'end': 8,
             'original_text': 'μιζομένη',
             'corrected_text': 'νομίζεσθαι',
             'original_row_sha256': '885b0bfd861e85f3beeeec3c2d98002b68e76e1eda3ae6d4492ab44fead50929'}],
  'evidence': 'The inspected source divides νο- at the preceding line end and μίζεσθαι before the full stop, '
              'followed by καὶ οὐκ ἐπὶ μὲν τῶν ἀθλητῶν. Henry gives that same complete word; retire only the '
              'reviewed pair, not the later συμ- fragment.',
  'scan': {'image_sha256': '3ef6ce42c9928b338a8aa055d140071caa1d9ac2cbf8d1c34e49121e284460b5',
           'max_side': 3600,
           'observed_text': 'νο-\nμίζεσθαι',
           'physical_page': 170,
           'printed_page': 435,
           'region': [0.025, 0.3, 0.49, 0.54],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 11521,
                'stop': 11525,
                'units_sha256': '0ced546f55f80640241ebc35bbe12749e42c33f99a8f26b46b02f69c04171d11',
                'units': [{'text': 'οὐκ ἀδικοῦντας κακῶς λέγειν καὶ συκοφαντεῖν οὐχὶ δίκαια \nποιεῖν ἐστιν',
                           'html_line': 26643,
                           'html_column': 92,
                           'unit_index': 11521,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': ']. Ἡμεῖς τοίνυν ἀντὶ τοῦ κατηγορεῖν ἀμφο‐ \n'
                                   'τέρων ὑπὲρ ἀμφοτέρων τὰ πρέποντα ἀπολογούμεθα, \n'
                                   'οὔτε τοῦ δήμου τὴν αἰτίαν πάντως εἶναι φάσκοντες, οὔτε \n'
                                   'ἐκείνους προσήκειν, εἰ ὅτι προσέπταισαν, χείρους νο‐',
                           'html_line': 26644,
                           'html_column': 19,
                           'unit_index': 11522,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': 'μίζεσθαι.',
                           'html_line': 26647,
                           'html_column': 66,
                           'unit_index': 11523,
                           'codex': '248',
                           'bekker': '435a'},
                          {'text': 'Καὶ οὐκ ἐπὶ μὲν τῶν ἀθλητῶν οὕτω συμ‐ \n'
                                   'βαίνει, τὰ δὲ τῆς μουσικῆς ἑστηκυίαν ἔχει τὴν νίκην \n'
                                   'τοῖς κρείττοσιν, ἀλλὰ κἀνταῦθα τὸ τοῦ Πινδάρου κρα‐ \n'
                                   'τεῖ· πάνυ γὰρ μετ’ ἀληθείας τοῦτ’ ἐκεῖνος ὕμνησεν· \n',
                           'html_line': 26647,
                           'html_column': 109,
                           'unit_index': 11524,
                           'codex': '248',
                           'bekker': '435a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'νομίζεσθαι',
              'refs': [{'html_line': 26644,
                        'html_column': 19,
                        'unit_index': 11522,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 196,
                        'end': 198},
                       {'html_line': 26647,
                        'html_column': 66,
                        'unit_index': 11523,
                        'codex': '248',
                        'bekker': '435a',
                        'start': 0,
                        'end': 8}],
              'tokens': [{'text': 'νομίζεσθαι',
                          'refs': [{'html_line': 26644,
                                    'html_column': 19,
                                    'unit_index': 11522,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 196,
                                    'end': 198},
                                   {'html_line': 26647,
                                    'html_column': 66,
                                    'unit_index': 11523,
                                    'codex': '248',
                                    'bekker': '435a',
                                    'start': 0,
                                    'end': 8}],
                          'source_index': 274361}],
              'surface': 'νομίζεσθαι',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.25',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 8,
                                              'corrected_start': 0,
                                              'corrected_text': 'μιζομένη',
                                              'end': 8,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 8,
                                                             'lexical_eligible': False,
                                                             'qualification': 'Printed continuation of a '
                                                                              'word begun on the preceding '
                                                                              'source line or page. Preserve '
                                                                              'the suffix without supplying '
                                                                              'missing letters or counting '
                                                                              'it as a standalone lexical '
                                                                              'form.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'μιζομένη'}],
                                              'original_text': 'μιζομένη',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '82ad989942be70ae98295b5476fa2b9a21ae9ce7b8cfc959d6cbfbf33ba1b973',
                                                            'text': 'μιζομένη'},
                                                           {'image_sha256': '3ef6ce42c9928b338a8aa055d140071caa1d9ac2cbf8d1c34e49121e284460b5',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 170,
                                                            'region': [0.025, 0.3, 0.49, 0.54],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'μίζεσθαι'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:23:05.576924Z',
                                              'scan': {'image_sha256': '3ef6ce42c9928b338a8aa055d140071caa1d9ac2cbf8d1c34e49121e284460b5',
                                                       'max_side': 3600,
                                                       'observed_text': 'μίζεσθαι',
                                                       'physical_page': 170,
                                                       'printed_page': 435,
                                                       'region': [0.025, 0.3, 0.49, 0.54],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact sigma/theta group remains '
                                                             'unresolved in this printed continuation.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'μιζομένη',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.25',
                                                  'original_text': 'μιζομένη',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': '4774fcdacb12bec608570ac1f2836c2c8e3358948545167cea249291d67566e9'},
 {'id': 'boundary-0184.4',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.4',
                  'segment_index': 0,
                  'start': 0,
                  'end': 12,
                  'original_text': 'σκευασθεῖσαι',
                  'inherited_record_sha256': '6ad3e2993a97431768e27abb3f26b291763d62c8854cfc9d6e0e59ef32925537',
                  'original_segment_sha256': 'c6ba257ea3d265f678e3857c2bef62a283e9658689119e7b980abb522d13ffca'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.3',
             'start': 45,
             'end': 50,
             'original_text': 'κατα-',
             'corrected_text': '',
             'original_row_sha256': '93193325525f1afed03586307938ea386cefa19be9c131f1004e1f703c96b99b'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.4',
             'start': 0,
             'end': 12,
             'original_text': 'σκευασθεῖσαι',
             'corrected_text': 'κατασκευασθεῖσι',
             'original_row_sha256': '747ff0ef64a08c42fe07f4e368580247923d25f837d283bf8fc3e3a7d7e9792c'}],
  'evidence': 'The source ends the preceding line κατα- and begins σκευασθεῖσι before λατομίδες. The '
              'supplied edition gives complete κατασκευασθεῖσι. The source’s intervening marginal 1344R '
              'reference is not part of either word fragment.',
  'scan': {'image_sha256': '982e4bcc5b5ed0577ef56e244eda6934e65103ea7320e4e7594fd49c8dbc2e35',
           'max_side': 3600,
           'observed_text': 'κατα-\nσκευασθεῖσι',
           'physical_page': 184,
           'printed_page': 449,
           'region': [0.025, 0.105, 0.49, 0.34],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 11912,
                'stop': 11916,
                'units_sha256': 'd093b8efc0096ba870e1f57dfe974c4273cb8d85741271a897f5659c2c6edec5',
                'units': [{'text': 'ὧν καὶ τὰ Μεμνόνεια συντετελέσθαι φασί), ποτε δὲ \n'
                                   'Μήδων καὶ Περσῶν ἐπικρατησάντων.',
                           'html_line': 27476,
                           'html_column': 200,
                           'unit_index': 11912,
                           'codex': '250',
                           'bekker': '449a'},
                          {'text': 'Εὑρίσκονται δὲ ἔτι καὶ \n'
                                   'καθ’ ἡμᾶς ἐν τοῖς χρυσείοις τοῖς ὑπ’ ἐκείνων κατα‐ \n'
                                   'σκευασθεῖσι λατομίδες μὲν χαλκαῖ, διὰ τὸ μήπω τὴν',
                           'html_line': 27477,
                           'html_column': 65,
                           'unit_index': 11913,
                           'codex': '250',
                           'bekker': '449a'},
                          {'text': 'τοῦ σιδήρου κατ’ ἐκεῖνον τὸν χρόνον ἐγνωρίσθαι χρείαν, \n'
                                   'ὀστᾶ δὲ ἀνθρώπων ἄπιστα τῷ πλήθει, πτωμάτων (ὅπερ \n'
                                   'εἰκὸς γίνεσθαι) οὐκ ὀλίγων ἐν τοῖς χαύνοις καὶ πλακώ‐ \n'
                                   'δεσιν ὑπονόμοις γενομένων, τηλικαῦτα δὲ ὀρυγμάτων \n'
                                   'μεγέθη, καὶ διατείνοντα βάθεσιν ἐπικαρσίοις ἐπ’ αὐ‐',
                           'html_line': 27479,
                           'html_column': 62,
                           'unit_index': 11914,
                           'codex': '250',
                           'bekker': '449a'},
                          {'text': 'τὴν τὴν θάλασσαν. \n'
                                   '    Ὅτι παρὰ τὴν νότιον τῆς Αἰγύπτου κλίσιν τέσσαρά \n'
                                   'ἐστι φῦλα τὰ μέγιστα, τὸ μὲν τοῖς ποταμοῖς παρεζευγμέ‐ \n'
                                   'νον, ὃ σπείρει σήσαμον καὶ κέγχρον, τὸ δὲ περὶ τὰς \n'
                                   'λίμνας οἰκοῦν, ὃ τοῦ καλάμου καὶ τῆς ὕλης ἅπτεται τῆς',
                           'html_line': 27483,
                           'html_column': 65,
                           'unit_index': 11915,
                           'codex': '250',
                           'bekker': '449a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'κατασκευασθεῖσι',
              'refs': [{'html_line': 27477,
                        'html_column': 65,
                        'unit_index': 11913,
                        'codex': '250',
                        'bekker': '449a',
                        'start': 69,
                        'end': 73},
                       {'html_line': 27477,
                        'html_column': 65,
                        'unit_index': 11913,
                        'codex': '250',
                        'bekker': '449a',
                        'start': 76,
                        'end': 87}],
              'tokens': [{'text': 'κατασκευασθεῖσι',
                          'refs': [{'html_line': 27477,
                                    'html_column': 65,
                                    'unit_index': 11913,
                                    'codex': '250',
                                    'bekker': '449a',
                                    'start': 69,
                                    'end': 73},
                                   {'html_line': 27477,
                                    'html_column': 65,
                                    'unit_index': 11913,
                                    'codex': '250',
                                    'bekker': '449a',
                                    'start': 76,
                                    'end': 87}],
                          'source_index': 283048}],
              'surface': 'κατασκευασθεῖσι',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.4',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 12,
                                              'corrected_start': 0,
                                              'corrected_text': 'σκευασθεῖσαι',
                                              'end': 12,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 12,
                                                             'lexical_eligible': False,
                                                             'qualification': 'Printed continuation of a '
                                                                              'word begun on the preceding '
                                                                              'source line or page. Preserve '
                                                                              'the suffix without supplying '
                                                                              'missing letters or counting '
                                                                              'it as a standalone lexical '
                                                                              'form.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'σκευασθεῖσαι'}],
                                              'original_text': 'σκευασθεῖσαι',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': 'b4444d07296eaf84e8744e4c68fb91a7ce6309d5266bde82d1a59ff1225f2818',
                                                            'text': 'σκευασθεῖσαι'},
                                                           {'image_sha256': '982e4bcc5b5ed0577ef56e244eda6934e65103ea7320e4e7594fd49c8dbc2e35',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 184,
                                                            'region': [0.025, 0.105, 0.49, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'σκευασθεῖσι'},
                                                           {'end': 1959,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s461',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 0,
                                                            'text': 'ὧν καὶ τὰ Μεμνόνεια συντετελέσθαι '
                                                                    'φασί), ποτὲ δὲ Μήδων καὶ Περσῶν '
                                                                    "ἐπικρατησάντων. εὑρίσκονθ' δὲ ἔτι καὶ "
                                                                    "καθ' ἡμᾶς ἐν τοῖς χρυσείοις τοῖς ὑπ' "
                                                                    'ἐκείνων κατασκευασθεῖσι "λατομίδες μὲν '
                                                                    'χαλκαῖ, διὰ τὸ μήπω τὴν τοῦ σιδήρου '
                                                                    "κατ' ἐκεῖνον τὸν χρόνον ἐγνωρίσθαι "
                                                                    'χρείαν, ὀστᾶ δὲ ἀνθρώπων ἄπιστα τῷ '
                                                                    'πλήθει, πτωμάτων (ὅπερ εἰκὸς γίνεσθαι) '
                                                                    'ἐκ ὀλίγων ἐν τοῖς χαύνοις καὶ '
                                                                    'πλακώδεσιν ὑπονόμοις γενομένων, '
                                                                    'τηλικαῦτα δὲ ὀρυγμάτων μεγέθη, καὶ '
                                                                    "διατείνοντα βάθεσιν ἐπικαρσίοις ἐπ' "
                                                                    'αὐτὴν τὴν θάλασσαν. ὅτι παρὰ τὴν νότιον '
                                                                    'τῆς Αἰγύπτου κλίσιν τέσσαρά ἐστι φῦλα '
                                                                    'τὰ μέγιστα, τὸ μὲν τοῖς ποταμοῖς '
                                                                    'παρεζευγμένον, ὃ σπείρει σήσαμον καὶ '
                                                                    'κέγχρον, τὸ δὲ περὶ τὰς λίμνας οἰκῶν, ὃ '
                                                                    'τῷ καλάμῳ καὶ τῆς ὕλης ἅπτεται τῆς '
                                                                    'ἁπαλῆς, τὸ δὲ εἰκῇ πλανώμενον, ὃ σαρκὶ '
                                                                    'καὶ γάλακτι παραπέμπει τὸν βίον, τὸ δὲ '
                                                                    'ἐκ τῆς παραλίας ὁρμώμενον, τοὺς ἰχθύας '
                                                                    'ἀγρεῦον. τοῦτο δὲ τὸ γένος ἔχει μὲν '
                                                                    "οὔτε πόλεις οὔτε χώρας ἔτ' ἄλλης "
                                                                    'ἐντέχνου κατασκευῆς ὑπογραφὴν οὐδεμίαν, '
                                                                    'ἐστὶ δὲ τῶν ὑπολοίπων, ὡς ἔνιοί φασι, '
                                                                    'μέγιστον ἀπὸ γὰρ Αὐταίων, οἳ τὸν '
                                                                    'ἔσχατον μυχὸν κατοικήσουσι, ὃν τῇ '
                                                                    'μεγάλῃ συμβέβηκε συγκλείεσθαι θαλάττῃ, '
                                                                    'μέχρι τῆς Ἰνδικῆς καὶ Κεδρωσίας, ἔτι δὲ '
                                                                    'Γερμανίας καὶ Περσῶν καὶ τῶν τοῖς '
                                                                    'εἰρημένοις γένεσιν ὑποκειμένων νήσων, '
                                                                    'ἰχθυοφάγοι πάντη κατοικοῦσι, γυμνοὶ μὲν '
                                                                    'ὄντες αὐτοί, γυμνὰς δὲ ἔχοντες τὰς '
                                                                    'γυναῖκας, κοινὴν δὲ τέκνων γένεσιν, ἔτι '
                                                                    'δὲ ἡδονῆς μὲν καὶ πόνου φυσικὴν ἔχοντες '
                                                                    'γνῶσιν, αἰσχρῶν δὲ καὶ καλῶν οὐδὲ τὴν '
                                                                    'ἐλαχίστην εἰσφερόμενοι ἔννοιαν. τούτοις '
                                                                    "δὲ τὰ μὲν ἀγχιβαθῆ πάντ' ἐστὶ πρὸς τὸν "
                                                                    'βίον ἀλλότρια, παραπλησίως δὲ τὰ '
                                                                    'παρακείμενα μακραῖς ἠϊόσι· θήραν γὰρ '
                                                                    "οὔτε ἰχθύος οὔτ' ἄλλου γένους "
                                                                    'ὁμοιοπαθοῦς ἁδροτέραν παραδίδωσιν ἡ '
                                                                    'τοιάδε χέρσος. αἱ δὲ οἰκήσεις πᾶσιν '
                                                                    'ἐκείνοις τοῖς εἰρημένοις παρὰ τὰς '
                                                                    'ῥαχίας, αἳ καὶ κοιλάδας βαθείας ἔχουσι '
                                                                    'καὶ φάραγγας ἀνωμάλους καὶ στενὰς '
                                                                    'αὐλῶνας καὶ σκολιὰς ἐκτροπάς. ὧν πρὸς '
                                                                    'τὴν χρείαν ὑποκειμένων οἰκείως, '
                                                                    'ἀναθέμενοι πέτρους αὐτοπαγεῖς ἐπὶ τῆς '
                                                                    'κοιλίας οἱονεί τινας ὡραιάς. ὅταν οὖν '
                                                                    'ἐκ πελάγους ἡ πλημμυρὶς ἐπὶ τὴν χέρσον '
                                                                    'φέροιτο (ὃ ποιεῖ δὶς ἑκάστης ἡμέρας, '
                                                                    'πρὸς ὥραν ἐνάτην τε καὶ'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:57:11.305070Z',
                                              'scan': {'image_sha256': '982e4bcc5b5ed0577ef56e244eda6934e65103ea7320e4e7594fd49c8dbc2e35',
                                                       'max_side': 3600,
                                                       'observed_text': 'σκευασθεῖσι',
                                                       'physical_page': 184,
                                                       'printed_page': 449,
                                                       'region': [0.025, 0.105, 0.49, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact sigma/theta group remains '
                                                             'unresolved independently.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'σκευασθεῖσαι',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.4',
                                                  'original_text': 'σκευασθεῖσαι',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': 'e1288f159e6e67921802b6df4030da86aedf8b2c620064aafeca91dca16da854'},
 {'id': 'boundary-0193.5',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.5',
                  'segment_index': 0,
                  'start': 0,
                  'end': 7,
                  'original_text': 'πέρποδῃ',
                  'inherited_record_sha256': '1c5945da99bcbe32eb7af8962202301c2e64d9fca8a30a4f05fe908a3f145cf1',
                  'original_segment_sha256': '207a90b81545f0cc1f17bdfa58fa2cd6bd47906ce4fe2ad6cb0f8c0e78d988f9'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.4',
             'start': 600,
             'end': 605,
             'original_text': 'παρα-',
             'corrected_text': '',
             'original_row_sha256': 'f208ff6962fa3f9a87dc4f918071d08c23ad22a7c22cc2d54d1ac36978eee551'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.5',
             'start': 0,
             'end': 7,
             'original_text': 'πέρποδῃ',
             'corrected_text': 'παραπέμπεσθαι',
             'original_row_sha256': '267fe7110ccb416e60a6e6d77f373ceeee6ceb95080992db988040f81655730b'}],
  'evidence': 'The plant-description sentence crosses the column boundary after πρὸς ἡμᾶς παρα- and resumes '
              'πέμπεσθαι before the δύναμιν phrase. Select Henry’s complete παραπέμπεσθαι once; preserve the '
              'unrelated differing τῷ γένει/toῦ γένους reading.',
  'scan': {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
           'max_side': 3600,
           'observed_text': 'παρα-\nπέμπεσθαι',
           'physical_page': 193,
           'printed_page': 458,
           'region': [0.56, 0.105, 0.99, 0.34],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 12132,
                'stop': 12136,
                'units_sha256': '64318f4b5544619b9154c5a97248bcd6ff87b85dc3381d84fc38a2a915a241d4',
                'units': [{'text': 'ἀμυθήτοις. Ὀσμή τε πᾶσαν ἐπέχει τὴν παραλίαν, θέας \n'
                                   'τε καὶ λόγου κρείττω τέρψιν τοῖς ἀφικνουμένοις κατα‐ \n'
                                   'σκευάζουσα. Παρὰ μὲν γὰρ αὐτὴν πέφυκε τὴν θάλατταν \n'
                                   'τό τε βάλσαμον πολὺ καὶ κασσία καὶ πόα τις ἄλλη πρόσ‐ \n'
                                   'φατος μὲν ἡδίστην δὲ ἔχουσα τῶν ὀμμάτων τέρψιν, ἐν δὲ',
                           'html_line': 28055,
                           'html_column': 64,
                           'unit_index': 12132,
                           'codex': '250',
                           'bekker': '458a'},
                          {'text': 'τῷ χρονίζειν γινομένη συντόμως ἐξίτηλος, ὥστε πρότερον \n'
                                   'ἀπαμαυροῦσθαι τοῦ φυτοῦ τὴν χρείαν ἢ πρὸς ἡμᾶς παρα‐',
                           'html_line': 28059,
                           'html_column': 67,
                           'unit_index': 12133,
                           'codex': '250',
                           'bekker': '458a'},
                          {'text': 'πέμπεσθαι τοῦ γένους τὴν δύναμιν.',
                           'html_line': 28060,
                           'html_column': 105,
                           'unit_index': 12134,
                           'codex': '250',
                           'bekker': '458b'},
                          {'text': 'Ἐπὶ δὲ τῆς μεσογείου \n'
                                   'δρυμοὶ συνεχεῖς στείχουσι καὶ μεγάλοι· δένδρα γὰρ ἠλί‐ \n'
                                   'βατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς δὲ καὶ κιννα‐ \n'
                                   'μώμου φοίνικός τε καὶ καλάμου καὶ τῶν ἄλλων ἀνεῖται',
                           'html_line': 28060,
                           'html_column': 171,
                           'unit_index': 12135,
                           'codex': '250',
                           'bekker': '458b'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'παραπέμπεσθαι',
              'refs': [{'html_line': 28059,
                        'html_column': 67,
                        'unit_index': 12133,
                        'codex': '250',
                        'bekker': '458a',
                        'start': 103,
                        'end': 107},
                       {'html_line': 28060,
                        'html_column': 105,
                        'unit_index': 12134,
                        'codex': '250',
                        'bekker': '458b',
                        'start': 0,
                        'end': 9}],
              'tokens': [{'text': 'παραπέμπεσθαι',
                          'refs': [{'html_line': 28059,
                                    'html_column': 67,
                                    'unit_index': 12133,
                                    'codex': '250',
                                    'bekker': '458a',
                                    'start': 103,
                                    'end': 107},
                                   {'html_line': 28060,
                                    'html_column': 105,
                                    'unit_index': 12134,
                                    'codex': '250',
                                    'bekker': '458b',
                                    'start': 0,
                                    'end': 9}],
                          'source_index': 288953}],
              'surface': 'παραπέμπεσθαι',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.5',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 7,
                                              'corrected_start': 0,
                                              'corrected_text': 'πέρποδῃ',
                                              'end': 7,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [],
                                              'original_text': 'πέρποδῃ',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '9bcb4f0bb8bc64a576e5775e4bc2abefa18e7438e12b579a14181dc217c96e6a',
                                                            'text': 'πέρποδῃ'},
                                                           {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 193,
                                                            'region': [0.56, 0.105, 0.99, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'πέμπεσθαι'},
                                                           {'end': 4111,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s470',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2056,
                                                            'text': 'παραπέμπεσθαι τῇ γένει τὴν δύναμιν. ἐπὶ '
                                                                    'δὲ τῆς μεσογείας δρυμοὶ συνεχεῖς '
                                                                    'ἑστήκασι καὶ μεγάλοι· δένδρα γὰρ '
                                                                    'ἡλίβατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς '
                                                                    'δὲ καὶ κινναμώμου φοίνικός τε καὶ '
                                                                    'καλάμου καὶ τῶν ἄλλων ἀνείδη τῶν '
                                                                    'τοιούτων, ὥστε εἶναι μηδενὶ λόγῳ τὸ '
                                                                    'πρᾶγμα δηλωτόν, ὃ συμβαίνει τοῖς περὶ '
                                                                    'τὰς αἰσθήσεις εἰληχόσι τοῦ γένους τὴν '
                                                                    'δοκιμασίαν. ὁ γὰρ τὴν τεθησαυρισμένην '
                                                                    'καὶ παλαιὰν ἔχει τῶν ἀρωμάτων '
                                                                    'ἀπόλαυσιν, οὐδὲ τὴν ἀπὸ τοῦ γεννῶντος '
                                                                    'καὶ τρέφοντος ὄγκου διακεχωρισμένην, '
                                                                    'ἀλλὰ τὴν ἀνθοῦσαν ἀπὸ τῆς θείας ἀκμῆς '
                                                                    'καὶ τὴν ἀπὸ τῶν οἰκείων καὶ φυσικῶν τὸ '
                                                                    'θαυμαζόμενον ἀποπέμπουσαν· ὥστε πολλοὺς '
                                                                    'εἰς λήθην ἀφικομένους τῶν θνητῶν '
                                                                    'εὐτυχημάτων τῆς ἀμβροσίας ὑπονοεῖν '
                                                                    'ἀπολαμβάνειν, ὄνομα τῷ πράγματος '
                                                                    'ἐπιζητοῦντος οἰκεῖον τῆς ὑπερβολῆς. '
                                                                    'περὶ δὲ τὰς δρυμὰς τῶν εὐωδῶν γένος '
                                                                    'ἐστὶν ὄφεων ἰδιώτατον πάντων, οἱονεὶ '
                                                                    'φθονήσης τοῖς ἁδροῖς ἐπιτεύγμασι τῆς '
                                                                    'τύχης καὶ παραπλεξάσης τἀγαθῷ τὸ '
                                                                    'βλαβερόν, ὅπως μηδεὶς εἰς τέλος '
                                                                    'ἐξυβρίζων τιτανῶδες καὶ κατεγνωκὸς τοῦ '
                                                                    'θείου τὸ φρόνημα λαμβάνῃ τῶν ἀγαθῶν '
                                                                    'εὐτυχέντων, παιδευθῇ δὲ τῇ παραθέσει '
                                                                    'καὶ μνήμῃ τῶν ἐναντίων. τὸ δὲ γένος τῶν '
                                                                    'ὄφεων χρῶμα μὲν ἔχει φοινικοῦν, μῆκος '
                                                                    'δὲ ὅσον σπιθαμῆς, δῆγμα δὲ ἀνίατον, ἂν '
                                                                    'τῆς λαγόνος ἀνώτερον αἱμάξῃ· τὴν δὲ '
                                                                    'πληγὴν δίδωσι παλλόμενον εἰς ὕψος. παρ’ '
                                                                    'αὐτοῖς δὲ τοῖς Σαβαίοις ἡ μὲν ὀσμὴ τῶν '
                                                                    'εὐωδῶν ἀκροτάτη, ἡ δὲ χάρις ἐλλιπής· τὸ '
                                                                    'γὰρ ἐνδελεχὲς ἐκ νηπίου κινεῖ μὲν τὴν '
                                                                    'αἴσθησιν ἧττον, ἀμβλυτέραν δὲ '
                                                                    'κατασκευάζει, μεταβολῆς τοῖς βίοις οὐχ '
                                                                    'ὑποκειμένης. οὐ μὴν ἀλλὰ κἀπειδὰν '
                                                                    'ἐκδύνωνται τὴν ζωὴν παιδαγωγεῖν '
                                                                    'παραπλησίως εὐπαθῆ, διαπνεομένου τοῦ '
                                                                    'σώματος ὑπ’ ἀκράτου καὶ τμητικῆς '
                                                                    'δυνάμεως, καὶ τὴν σύμμετρον πύκνωσιν '
                                                                    'ἐπὶ πλεῖον ἀγούσης ὥστε ἄγειν εἰς '
                                                                    'ἔκλυσιν ἐσχάτην, τότε δὴ ἀσφάλτῳ '
                                                                    'παραθυμιῶντες βραχὺ καὶ τράγου πώγωνα '
                                                                    'τοῖς τοιούτοις ἀφαιροῦνται τὴν ἄγαν '
                                                                    'εὐώδη τῆς ἐπιφορᾶς ὑπερβολήν, καὶ τῇ '
                                                                    'μίξει τοῦ δοκέντος λυπεῖν τὸ τῆς ἡδονῆς '
                                                                    'βλαβερόν ὑποκαταζεύλασιν. οὕτως ἅπαν '
                                                                    'ἐπίτευγμα μεσότητι μὲν καὶ τάξει '
                                                                    'κυβερνώμενον παραπέμπει τὸν βίον, '
                                                                    'συμμετρίας δὲ καὶ καιροῦ στερηθὲν οὐκ '
                                                                    'ἔχει τὴν κτῆσιν ὀνησιφόρον. τὸ δὲ τῶν '
                                                                    'Σαβαίων ἄστυ τοῦ παντὸς ἔθνους '
                                                                    'προσηγορίαν δηλοῦν, ἐπ’ ὄρους ἐστὶν οὐ '
                                                                    'μεγάλου, πολὺ κάλλιστον τῶν'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:15:51.742671Z',
                                              'scan': {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                       'max_side': 3600,
                                                       'observed_text': 'πέμπεσθαι',
                                                       'physical_page': 193,
                                                       'printed_page': 458,
                                                       'region': [0.56, 0.105, 0.99, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact sigma/theta or sigma/chi group '
                                                             'remains unresolved independently of the '
                                                             'digital witness.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'πέρποδῃ',
                                                  'decision': 'retained',
                                                  'evidence': 'The corresponding source has πρὸς ἡμᾶς '
                                                              'παραπέμπεσθαι τοῦ γένους τὴν δύναμιν. The '
                                                              'preceding current row193.4 ends παρα-, so the '
                                                              'current target is a cross-row suffix even '
                                                              'though its inherited fragments list is empty. '
                                                              'A full-word substitution here would duplicate '
                                                              'the prefix. Preserve the target until a joint '
                                                              'boundary review.',
                                                  'location_evidence': {'source_sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                        'status': 'held-no-immediate-reliable-boundaries'},
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.5',
                                                  'manual_review': {'module': 'photius_remaining_manual_b',
                                                                    'review': {'evidence': 'The '
                                                                                           'corresponding '
                                                                                           'source has πρὸς '
                                                                                           'ἡμᾶς '
                                                                                           'παραπέμπεσθαι '
                                                                                           'τοῦ γένους τὴν '
                                                                                           'δύναμιν. The '
                                                                                           'preceding '
                                                                                           'current row193.4 '
                                                                                           'ends παρα-, so '
                                                                                           'the current '
                                                                                           'target is a '
                                                                                           'cross-row suffix '
                                                                                           'even though its '
                                                                                           'inherited '
                                                                                           'fragments list '
                                                                                           'is empty. A '
                                                                                           'full-word '
                                                                                           'substitution '
                                                                                           'here would '
                                                                                           'duplicate the '
                                                                                           'prefix. Preserve '
                                                                                           'the target until '
                                                                                           'a joint boundary '
                                                                                           'review.',
                                                                               'held_reason': 'source-word-boundary',
                                                                               'inherited_record_sha256': 'c65053bcc0e09826f6b135dd92ebe113ab6e2befd5a630cf538dd3616a2be16a',
                                                                               'kind': 'manually-located-editorial-counterpart',
                                                                               'original_row_sha256': 'ac2831823836778f6bba8460978518507fde53949a4d2e81613478b4bf46fb02',
                                                                               'original_text': 'πέρποδῃ',
                                                                               'qualification': 'An '
                                                                                                'editorial '
                                                                                                'source '
                                                                                                'preference, '
                                                                                                'not '
                                                                                                'independent '
                                                                                                'resolution '
                                                                                                'of the '
                                                                                                'Bekker ink. '
                                                                                                'Original '
                                                                                                'scan '
                                                                                                'observations, '
                                                                                                'contrary '
                                                                                                'readings, '
                                                                                                'and '
                                                                                                'independent '
                                                                                                'exclusions '
                                                                                                'remain '
                                                                                                'authoritative.',
                                                                               'readings': [],
                                                                               'rendering': {},
                                                                               'reviewed_at': '2026-10-21T23:14:28.998247+00:00',
                                                                               'reviewed_extent': {'end': 7,
                                                                                                   'start': 0},
                                                                               'source_context': {'qualification': 'An '
                                                                                                                   'exact '
                                                                                                                   'bounded '
                                                                                                                   'context '
                                                                                                                   'for '
                                                                                                                   'this '
                                                                                                                   'occurrence; '
                                                                                                                   'a '
                                                                                                                   'held '
                                                                                                                   'context '
                                                                                                                   'does '
                                                                                                                   'not '
                                                                                                                   'assert '
                                                                                                                   'a '
                                                                                                                   'counterpart.',
                                                                                                  'sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                                                  'source_id': 'tlg-photius-henry',
                                                                                                  'tokens': [{'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 69,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 56,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288945,
                                                                                                              'text': 'ἀπαμαυροῦσθαι'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 73,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 70,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288946,
                                                                                                              'text': 'τοῦ'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 79,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 74,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288947,
                                                                                                              'text': 'φυτοῦ'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 83,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 80,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288948,
                                                                                                              'text': 'τὴν'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 90,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 84,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288949,
                                                                                                              'text': 'χρείαν'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 92,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 91,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288950,
                                                                                                              'text': 'ἢ'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 97,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 93,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288951,
                                                                                                              'text': 'πρὸς'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 102,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 98,
                                                                                                                        'unit_index': 12133}],
                                                                                                              'source_index': 288952,
                                                                                                              'text': 'ἡμᾶς'},
                                                                                                             {'refs': [{'bekker': '458a',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 107,
                                                                                                                        'html_column': 67,
                                                                                                                        'html_line': 28059,
                                                                                                                        'start': 103,
                                                                                                                        'unit_index': 12133},
                                                                                                                       {'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 9,
                                                                                                                        'html_column': 105,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 0,
                                                                                                                        'unit_index': 12134}],
                                                                                                              'source_index': 288953,
                                                                                                              'text': 'παραπέμπεσθαι'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 13,
                                                                                                                        'html_column': 105,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 10,
                                                                                                                        'unit_index': 12134}],
                                                                                                              'source_index': 288954,
                                                                                                              'text': 'τοῦ'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 20,
                                                                                                                        'html_column': 105,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 14,
                                                                                                                        'unit_index': 12134}],
                                                                                                              'source_index': 288955,
                                                                                                              'text': 'γένους'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 24,
                                                                                                                        'html_column': 105,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 21,
                                                                                                                        'unit_index': 12134}],
                                                                                                              'source_index': 288956,
                                                                                                              'text': 'τὴν'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 32,
                                                                                                                        'html_column': 105,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 25,
                                                                                                                        'unit_index': 12134}],
                                                                                                              'source_index': 288957,
                                                                                                              'text': 'δύναμιν'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 3,
                                                                                                                        'html_column': 171,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 0,
                                                                                                                        'unit_index': 12135}],
                                                                                                              'source_index': 288958,
                                                                                                              'text': 'Ἐπὶ'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 6,
                                                                                                                        'html_column': 171,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 4,
                                                                                                                        'unit_index': 12135}],
                                                                                                              'source_index': 288959,
                                                                                                              'text': 'δὲ'},
                                                                                                             {'refs': [{'bekker': '458b',
                                                                                                                        'codex': '250',
                                                                                                                        'end': 10,
                                                                                                                        'html_column': 171,
                                                                                                                        'html_line': 28060,
                                                                                                                        'start': 7,
                                                                                                                        'unit_index': 12135}],
                                                                                                              'source_index': 288960,
                                                                                                              'text': 'τῆς'}],
                                                                                                  'tokens_sha256': 'c25ab67012a383af87675fc83f067594a3fcca569bbc6b305ed245e349b74d25'},
                                                                               'surface_sha256': None}},
                                                  'original_text': 'πέρποδῃ',
                                                  'readings': [],
                                                  'reason': 'individually-held-reading',
                                                  'segment_index': 0}}],
  'surface_sha256': 'e29a58b4bda2dd0a8bde38a7fbdc9d3b09e675ddda9e42e115e4933f7a246dca'},
 {'id': 'boundary-0193.8',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.8',
                  'segment_index': 1,
                  'start': 44,
                  'end': 49,
                  'original_text': 'ἀντι-',
                  'inherited_record_sha256': 'ebfbf4120abd3f74c7c3f70f45c9df0b2801fd9456d9ae5c61d470e08cdb4847',
                  'original_segment_sha256': '9a1e53b4e96255022aea7c86bfc541dd8caae053da8b1fbf2f190eaa765467be'},
                 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.9',
                  'segment_index': 0,
                  'start': 0,
                  'end': 1,
                  'original_text': 'δ',
                  'inherited_record_sha256': '8482ff25b58c1db4d4175e9644e8b28958d394855f4fd98570f40c7f21af3e74',
                  'original_segment_sha256': '0d5bc521eb6e3a1aa09caa87be132413bdb6e282c8d9eebc48adb61fe8c77ea2',
                  'text_role': 'line-number',
                  'lexical_eligible': False}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.8',
             'start': 44,
             'end': 49,
             'original_text': 'ἀντι-',
             'corrected_text': 'ἀνεῖται',
             'original_row_sha256': 'd8a900c12573d01298198d43760a757d5f36deaa1c23e27df7553a72afd2de58'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.9',
             'start': 0,
             'end': 1,
             'original_text': 'δ',
             'corrected_text': '',
             'original_row_sha256': '5f1d29e0684dfd5490c1bdccaf1215c3e6909600c8b8a154010bee5cf695eafa'}],
  'evidence': 'The line ending after τῶν ἄλλων contains one compact body word; the next line begins τῶν '
              'τοιούτων. Its separate left-margin 5 is the δ-shaped OCR artifact, not a continuation suffix. '
              'Select Henry’s complete ἀνεῖται at the body-word location as an editorial preference. Do not '
              'manufacture a Bekker split word from the marginal numeral; retain tentative ἀντι-/ἀνεί-/δῶν '
              'and Source Library ἀνείδη readings as contrary evidence.',
  'scan': {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
           'max_side': 3600,
           'observed_text': 'A compact body word follows ἄλλων; the next line starts with the separate '
                            'marginal 5, then τῶν τοιούτων.',
           'physical_page': 193,
           'printed_page': 458,
           'region': [0.56, 0.105, 0.99, 0.34],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 12134,
                'stop': 12138,
                'units_sha256': '16345c1f1e6d5703d542ef01aafdec2f7f208fae8824bd28908d0807c51726f4',
                'units': [{'text': 'πέμπεσθαι τοῦ γένους τὴν δύναμιν.',
                           'html_line': 28060,
                           'html_column': 105,
                           'unit_index': 12134,
                           'codex': '250',
                           'bekker': '458b'},
                          {'text': 'Ἐπὶ δὲ τῆς μεσογείου \n'
                                   'δρυμοὶ συνεχεῖς στείχουσι καὶ μεγάλοι· δένδρα γὰρ ἠλί‐ \n'
                                   'βατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς δὲ καὶ κιννα‐ \n'
                                   'μώμου φοίνικός τε καὶ καλάμου καὶ τῶν ἄλλων ἀνεῖται',
                           'html_line': 28060,
                           'html_column': 171,
                           'unit_index': 12135,
                           'codex': '250',
                           'bekker': '458b'},
                          {'text': 'τῶν τοιούτων, ὥστε εἶναι μηδενὶ λόγῳ τὸ πρᾶγμα δη‐ \n'
                                   'λωτόν, ὃ συμβαίνει τοῖς περὶ τὰς αἰσθήσεις εἰληχόσι \n'
                                   'τοῦ γένους τὴν δοκιμασίαν. Οὐ γὰρ τὴν τεθησαυρισμένην \n'
                                   'καὶ παλαιὰν ἔχει τῶν ἀρωμάτων ἀπόλαυσιν, οὐδὲ τὴν \n'
                                   'ἀπὸ τοῦ γεννῶντος καὶ τρέφοντος ὄγκου διακεχωρισμέ‐',
                           'html_line': 28063,
                           'html_column': 64,
                           'unit_index': 12136,
                           'codex': '250',
                           'bekker': '458b'},
                          {'text': 'νην, ἀλλὰ τὴν ἀνθοῦσαν ἀπὸ τῆς θείας ἀκμῆς καὶ τὴν \n'
                                   'ἀπὸ τῶν οἰκείων καὶ φυσικῶν τὸ θαυμαζόμενον ἀπο‐ \n'
                                   'πέμπουσαν· ὥστε πολλοὺς εἰς λήθην ἀφικομένους τῶν \n'
                                   'θνητῶν εὐτυχημάτων τῆς ἀμβροσίας ὑπονοῖεν ἀπο‐ \n'
                                   'λαμβάνειν, ὄνομα τοῦ πράγματος ἐπιζητοῦντος οἰκεῖον',
                           'html_line': 28067,
                           'html_column': 65,
                           'unit_index': 12137,
                           'codex': '250',
                           'bekker': '458b'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'ἀνεῖται',
              'refs': [{'html_line': 28060,
                        'html_column': 171,
                        'unit_index': 12135,
                        'codex': '250',
                        'bekker': '458b',
                        'start': 173,
                        'end': 180}],
              'tokens': [{'text': 'ἀνεῖται',
                          'refs': [{'html_line': 28060,
                                    'html_column': 171,
                                    'unit_index': 12135,
                                    'codex': '250',
                                    'bekker': '458b',
                                    'start': 173,
                                    'end': 180}],
                          'source_index': 288985}],
              'surface': 'ἀνεῖται',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.8',
                                      'segment_index': 1},
                         'original_segment': {'corrected_end': 49,
                                              'corrected_start': 44,
                                              'corrected_text': 'ἀντι-',
                                              'end': 49,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 5,
                                                             'lexical_eligible': False,
                                                             'qualification': 'This retained passage ends '
                                                                              'within a visibly divided '
                                                                              'printed word; preserve the '
                                                                              'source fragment and exclude '
                                                                              'it from lexical counts.',
                                                             'side': 'trailing',
                                                             'start': 0,
                                                             'text': 'ἀντι-'}],
                                              'original_text': 'ἀντι-',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '1183744bb1f0732908445fd913b194adca32581972b644abf8b739c6abc0a9f6',
                                                            'text': 'ἀντι-'},
                                                           {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 193,
                                                            'region': [0.56, 0.105, 0.99, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'ἀντι- / ἀνεί-'},
                                                           {'end': 4111,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s470',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2056,
                                                            'text': 'παραπέμπεσθαι τῇ γένει τὴν δύναμιν. ἐπὶ '
                                                                    'δὲ τῆς μεσογείας δρυμοὶ συνεχεῖς '
                                                                    'ἑστήκασι καὶ μεγάλοι· δένδρα γὰρ '
                                                                    'ἡλίβατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς '
                                                                    'δὲ καὶ κινναμώμου φοίνικός τε καὶ '
                                                                    'καλάμου καὶ τῶν ἄλλων ἀνείδη τῶν '
                                                                    'τοιούτων, ὥστε εἶναι μηδενὶ λόγῳ τὸ '
                                                                    'πρᾶγμα δηλωτόν, ὃ συμβαίνει τοῖς περὶ '
                                                                    'τὰς αἰσθήσεις εἰληχόσι τοῦ γένους τὴν '
                                                                    'δοκιμασίαν. ὁ γὰρ τὴν τεθησαυρισμένην '
                                                                    'καὶ παλαιὰν ἔχει τῶν ἀρωμάτων '
                                                                    'ἀπόλαυσιν, οὐδὲ τὴν ἀπὸ τοῦ γεννῶντος '
                                                                    'καὶ τρέφοντος ὄγκου διακεχωρισμένην, '
                                                                    'ἀλλὰ τὴν ἀνθοῦσαν ἀπὸ τῆς θείας ἀκμῆς '
                                                                    'καὶ τὴν ἀπὸ τῶν οἰκείων καὶ φυσικῶν τὸ '
                                                                    'θαυμαζόμενον ἀποπέμπουσαν· ὥστε πολλοὺς '
                                                                    'εἰς λήθην ἀφικομένους τῶν θνητῶν '
                                                                    'εὐτυχημάτων τῆς ἀμβροσίας ὑπονοεῖν '
                                                                    'ἀπολαμβάνειν, ὄνομα τῷ πράγματος '
                                                                    'ἐπιζητοῦντος οἰκεῖον τῆς ὑπερβολῆς. '
                                                                    'περὶ δὲ τὰς δρυμὰς τῶν εὐωδῶν γένος '
                                                                    'ἐστὶν ὄφεων ἰδιώτατον πάντων, οἱονεὶ '
                                                                    'φθονήσης τοῖς ἁδροῖς ἐπιτεύγμασι τῆς '
                                                                    'τύχης καὶ παραπλεξάσης τἀγαθῷ τὸ '
                                                                    'βλαβερόν, ὅπως μηδεὶς εἰς τέλος '
                                                                    'ἐξυβρίζων τιτανῶδες καὶ κατεγνωκὸς τοῦ '
                                                                    'θείου τὸ φρόνημα λαμβάνῃ τῶν ἀγαθῶν '
                                                                    'εὐτυχέντων, παιδευθῇ δὲ τῇ παραθέσει '
                                                                    'καὶ μνήμῃ τῶν ἐναντίων. τὸ δὲ γένος τῶν '
                                                                    'ὄφεων χρῶμα μὲν ἔχει φοινικοῦν, μῆκος '
                                                                    'δὲ ὅσον σπιθαμῆς, δῆγμα δὲ ἀνίατον, ἂν '
                                                                    'τῆς λαγόνος ἀνώτερον αἱμάξῃ· τὴν δὲ '
                                                                    'πληγὴν δίδωσι παλλόμενον εἰς ὕψος. παρ’ '
                                                                    'αὐτοῖς δὲ τοῖς Σαβαίοις ἡ μὲν ὀσμὴ τῶν '
                                                                    'εὐωδῶν ἀκροτάτη, ἡ δὲ χάρις ἐλλιπής· τὸ '
                                                                    'γὰρ ἐνδελεχὲς ἐκ νηπίου κινεῖ μὲν τὴν '
                                                                    'αἴσθησιν ἧττον, ἀμβλυτέραν δὲ '
                                                                    'κατασκευάζει, μεταβολῆς τοῖς βίοις οὐχ '
                                                                    'ὑποκειμένης. οὐ μὴν ἀλλὰ κἀπειδὰν '
                                                                    'ἐκδύνωνται τὴν ζωὴν παιδαγωγεῖν '
                                                                    'παραπλησίως εὐπαθῆ, διαπνεομένου τοῦ '
                                                                    'σώματος ὑπ’ ἀκράτου καὶ τμητικῆς '
                                                                    'δυνάμεως, καὶ τὴν σύμμετρον πύκνωσιν '
                                                                    'ἐπὶ πλεῖον ἀγούσης ὥστε ἄγειν εἰς '
                                                                    'ἔκλυσιν ἐσχάτην, τότε δὴ ἀσφάλτῳ '
                                                                    'παραθυμιῶντες βραχὺ καὶ τράγου πώγωνα '
                                                                    'τοῖς τοιούτοις ἀφαιροῦνται τὴν ἄγαν '
                                                                    'εὐώδη τῆς ἐπιφορᾶς ὑπερβολήν, καὶ τῇ '
                                                                    'μίξει τοῦ δοκέντος λυπεῖν τὸ τῆς ἡδονῆς '
                                                                    'βλαβερόν ὑποκαταζεύλασιν. οὕτως ἅπαν '
                                                                    'ἐπίτευγμα μεσότητι μὲν καὶ τάξει '
                                                                    'κυβερνώμενον παραπέμπει τὸν βίον, '
                                                                    'συμμετρίας δὲ καὶ καιροῦ στερηθὲν οὐκ '
                                                                    'ἔχει τὴν κτῆσιν ὀνησιφόρον. τὸ δὲ τῶν '
                                                                    'Σαβαίων ἄστυ τοῦ παντὸς ἔθνους '
                                                                    'προσηγορίαν δηλοῦν, ἐπ’ ὄρους ἐστὶν οὐ '
                                                                    'μεγάλου, πολὺ κάλλιστον τῶν'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:15:51.742671Z',
                                              'scan': {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                       'max_side': 3600,
                                                       'observed_text': 'ἀντι- / ἀνεί-',
                                                       'physical_page': 193,
                                                       'printed_page': 458,
                                                       'region': [0.56, 0.105, 0.99, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 44,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact terminal prefix remains '
                                                             'unresolved; preserve the original fragment '
                                                             'without completing it from the digital '
                                                             'witness.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'ἀντι-',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.8',
                                                  'original_text': 'ἀντι-',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 1}},
                        {'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.9',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 1,
                                              'corrected_start': 0,
                                              'corrected_text': 'δ',
                                              'end': 1,
                                              'evidence': 'Direct inspection of every word and punctuation '
                                                          'mark, including unchanged text, in this '
                                                          'contiguous passage. The overlapping pinned crops '
                                                          'cover the full retained source. Independent '
                                                          'digital readings remain bounded alternatives, not '
                                                          'automatic authority.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 1,
                                                             'lexical_eligible': False,
                                                             'qualification': 'Printed continuation of a '
                                                                              'word begun on the preceding '
                                                                              'source line or page. Preserve '
                                                                              'the suffix without supplying '
                                                                              'missing letters or counting '
                                                                              'it as a standalone lexical '
                                                                              'form.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'δ'}],
                                              'original_text': 'δ',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '6c55473e92cb9c20371fa846417ecc2e05a5625e3d15a51493941d55b89efa31',
                                                            'text': 'δ'},
                                                           {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 193,
                                                            'region': [0.56, 0.105, 0.99, 0.34],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'δῶν'},
                                                           {'end': 4111,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s470',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 2056,
                                                            'text': 'παραπέμπεσθαι τῇ γένει τὴν δύναμιν. ἐπὶ '
                                                                    'δὲ τῆς μεσογείας δρυμοὶ συνεχεῖς '
                                                                    'ἑστήκασι καὶ μεγάλοι· δένδρα γὰρ '
                                                                    'ἡλίβατα σμύρνης τε καὶ λιβανωτοῦ, πρὸς '
                                                                    'δὲ καὶ κινναμώμου φοίνικός τε καὶ '
                                                                    'καλάμου καὶ τῶν ἄλλων ἀνείδη τῶν '
                                                                    'τοιούτων, ὥστε εἶναι μηδενὶ λόγῳ τὸ '
                                                                    'πρᾶγμα δηλωτόν, ὃ συμβαίνει τοῖς περὶ '
                                                                    'τὰς αἰσθήσεις εἰληχόσι τοῦ γένους τὴν '
                                                                    'δοκιμασίαν. ὁ γὰρ τὴν τεθησαυρισμένην '
                                                                    'καὶ παλαιὰν ἔχει τῶν ἀρωμάτων '
                                                                    'ἀπόλαυσιν, οὐδὲ τὴν ἀπὸ τοῦ γεννῶντος '
                                                                    'καὶ τρέφοντος ὄγκου διακεχωρισμένην, '
                                                                    'ἀλλὰ τὴν ἀνθοῦσαν ἀπὸ τῆς θείας ἀκμῆς '
                                                                    'καὶ τὴν ἀπὸ τῶν οἰκείων καὶ φυσικῶν τὸ '
                                                                    'θαυμαζόμενον ἀποπέμπουσαν· ὥστε πολλοὺς '
                                                                    'εἰς λήθην ἀφικομένους τῶν θνητῶν '
                                                                    'εὐτυχημάτων τῆς ἀμβροσίας ὑπονοεῖν '
                                                                    'ἀπολαμβάνειν, ὄνομα τῷ πράγματος '
                                                                    'ἐπιζητοῦντος οἰκεῖον τῆς ὑπερβολῆς. '
                                                                    'περὶ δὲ τὰς δρυμὰς τῶν εὐωδῶν γένος '
                                                                    'ἐστὶν ὄφεων ἰδιώτατον πάντων, οἱονεὶ '
                                                                    'φθονήσης τοῖς ἁδροῖς ἐπιτεύγμασι τῆς '
                                                                    'τύχης καὶ παραπλεξάσης τἀγαθῷ τὸ '
                                                                    'βλαβερόν, ὅπως μηδεὶς εἰς τέλος '
                                                                    'ἐξυβρίζων τιτανῶδες καὶ κατεγνωκὸς τοῦ '
                                                                    'θείου τὸ φρόνημα λαμβάνῃ τῶν ἀγαθῶν '
                                                                    'εὐτυχέντων, παιδευθῇ δὲ τῇ παραθέσει '
                                                                    'καὶ μνήμῃ τῶν ἐναντίων. τὸ δὲ γένος τῶν '
                                                                    'ὄφεων χρῶμα μὲν ἔχει φοινικοῦν, μῆκος '
                                                                    'δὲ ὅσον σπιθαμῆς, δῆγμα δὲ ἀνίατον, ἂν '
                                                                    'τῆς λαγόνος ἀνώτερον αἱμάξῃ· τὴν δὲ '
                                                                    'πληγὴν δίδωσι παλλόμενον εἰς ὕψος. παρ’ '
                                                                    'αὐτοῖς δὲ τοῖς Σαβαίοις ἡ μὲν ὀσμὴ τῶν '
                                                                    'εὐωδῶν ἀκροτάτη, ἡ δὲ χάρις ἐλλιπής· τὸ '
                                                                    'γὰρ ἐνδελεχὲς ἐκ νηπίου κινεῖ μὲν τὴν '
                                                                    'αἴσθησιν ἧττον, ἀμβλυτέραν δὲ '
                                                                    'κατασκευάζει, μεταβολῆς τοῖς βίοις οὐχ '
                                                                    'ὑποκειμένης. οὐ μὴν ἀλλὰ κἀπειδὰν '
                                                                    'ἐκδύνωνται τὴν ζωὴν παιδαγωγεῖν '
                                                                    'παραπλησίως εὐπαθῆ, διαπνεομένου τοῦ '
                                                                    'σώματος ὑπ’ ἀκράτου καὶ τμητικῆς '
                                                                    'δυνάμεως, καὶ τὴν σύμμετρον πύκνωσιν '
                                                                    'ἐπὶ πλεῖον ἀγούσης ὥστε ἄγειν εἰς '
                                                                    'ἔκλυσιν ἐσχάτην, τότε δὴ ἀσφάλτῳ '
                                                                    'παραθυμιῶντες βραχὺ καὶ τράγου πώγωνα '
                                                                    'τοῖς τοιούτοις ἀφαιροῦνται τὴν ἄγαν '
                                                                    'εὐώδη τῆς ἐπιφορᾶς ὑπερβολήν, καὶ τῇ '
                                                                    'μίξει τοῦ δοκέντος λυπεῖν τὸ τῆς ἡδονῆς '
                                                                    'βλαβερόν ὑποκαταζεύλασιν. οὕτως ἅπαν '
                                                                    'ἐπίτευγμα μεσότητι μὲν καὶ τάξει '
                                                                    'κυβερνώμενον παραπέμπει τὸν βίον, '
                                                                    'συμμετρίας δὲ καὶ καιροῦ στερηθὲν οὐκ '
                                                                    'ἔχει τὴν κτῆσιν ὀνησιφόρον. τὸ δὲ τῶν '
                                                                    'Σαβαίων ἄστυ τοῦ παντὸς ἔθνους '
                                                                    'προσηγορίαν δηλοῦν, ἐπ’ ὄρους ἐστὶν οὐ '
                                                                    'μεγάλου, πολὺ κάλλιστον τῶν'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:15:51.742671Z',
                                              'scan': {'image_sha256': 'd3ef178e1f528ebd6fb03647e5a61ff090fa826098a698879cede5bab86bff46',
                                                       'max_side': 3600,
                                                       'observed_text': 'δῶν',
                                                       'physical_page': 193,
                                                       'printed_page': 458,
                                                       'region': [0.56, 0.105, 0.99, 0.34],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand clearly visible printed '
                                                                          'ου, στ, and καί ligatures. Reflow '
                                                                          'complete words visibly divided '
                                                                          'between lines within a retained '
                                                                          'passage. Preserve incomplete '
                                                                          'passage boundaries; omit marginal '
                                                                          'references and printed line '
                                                                          'numbers from body transcription.',
                                              'uncertainty': 'The compact leading continuation of the '
                                                             'uncertain preceding printed word remains '
                                                             'unresolved; preserve the original '
                                                             'single-letter fragment.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'δ',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0193.9',
                                                  'original_text': 'δ',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': '1e8785478847e56dcd381e1e838f7936644dc2ee4e4f0c3262b95bf6b57a916b'},
 {'id': 'boundary-0215.26',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
                  'segment_index': 0,
                  'start': 0,
                  'end': 7,
                  'original_text': 'δροῖζε?',
                  'inherited_record_sha256': 'e23d2aa5b34b4359d16c57e76874800b0810bebfd624d288474dada6eecf221f',
                  'original_segment_sha256': 'c04dfd2aaf1823b18a06590c63c565c961cfb75b56564714568659b63e8d0ee4'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.25',
             'start': 40,
             'end': 45,
             'original_text': 'συνα-',
             'corrected_text': '',
             'original_row_sha256': 'aa37789e58cef8c4f35395f31c40b8536bec410a94a64a61846e8be95f57a173'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
             'start': 0,
             'end': 7,
             'original_text': 'δροῖζε?',
             'corrected_text': 'συναθροίζεται',
             'original_row_sha256': '8596fb29de1a68a45f3f88269d1110d55baa0bdef70e7875f9e6c97a2258bf92'}],
  'evidence': 'The council sentence has βασιλέως προστάττοντος συνα- at the line end and θροίζεται before '
              'the comma at the next line. Henry joins exactly συναθροίζεται. Preserve the following comma '
              'and all neighboring words while counting the reviewed whole word once.',
  'scan': {'image_sha256': '2fbb79222df4dd73744d217a31804ce5fb306bd71e054005216b1da5f5ac39eb',
           'max_side': 3600,
           'observed_text': 'συνα-\nθροίζεται',
           'physical_page': 215,
           'printed_page': 480,
           'region': [0.21, 0.095, 0.61, 0.77],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 12649,
                'stop': 12654,
                'units_sha256': '61a7c231f49bdbdf80b36284d9c16794a9f8c02a3fffddcef4cf6600f84ca269',
                'units': [{'text': 'συκοφαντίας κατὰ τοῦ ὁσίου ἐκκόψαντες καθωπλίσαντο· \n'
                                   'Ἀρσενίου δὲ ταύτην ἐφήμιζον, καὶ ὑπὸ Ἀθανασίου \n'
                                   'μὲν ἐκκεκόφθαι, εἶναι δὲ αὐτῷ ταύτην μαγικῆς τέχνης \n'
                                   'ὄργανον.',
                           'html_line': 29434,
                           'html_column': 80,
                           'unit_index': 12649,
                           'codex': '258',
                           'bekker': '480a'},
                          {'text': 'Καὶ ἡ μὲν τῆς ὑπερορίας ψῆφος οὐ λύεται, συνέ‐',
                           'html_line': 29437,
                           'html_column': 25,
                           'unit_index': 12650,
                           'codex': '258',
                           'bekker': '480a'},
                          {'text': 'δριον δ’ ἐν Τύρῳ βασιλέως προστάττοντος συνα‐ \n'
                                   'θροίζεται, καὶ προχειρίζεται τὸ βασιλικὸν βούλημα ἄνδρα \n'
                                   'συνέστιον καὶ ὁμόφρονα, Ἀρχέλαον ὄνομα, καὶ σὺν αὐ‐ \n'
                                   'τῷ τὸν Φοινίκης ἄρχοντα, συνεδριάσαι τε τοῖς περὶ \n'
                                   'Εὐσέβιον, καὶ συνδιασκέψασθαι ἃ κατὰ τοῦ Ἀθανασίου',
                           'html_line': 29437,
                           'html_column': 119,
                           'unit_index': 12651,
                           'codex': '258',
                           'bekker': '480a'},
                          {'text': 'συνεσκεύαστο. Ἐχρόνιζον οὖν οἱ ἐν Τύρῳ, ὡς μὲν οἱ \n'
                                   'δυσσεβεῖς ἐπλάττοντο, τοὺς ἀπὸ Ἀλεξανδρείας κατη‐ \n'
                                   'γόρους ἀναμένοντες, οὓς καὶ τοῦ μύσους αὐτόπτας καὶ τὸν \n'
                                   'Ἀρσένιον καλῶς ἐπιγινώσκειν διήγγελλον, ὡς δὲ τὸ \n'
                                   'ἐκβεβηκὸς ἔδειξε, κατὰ θείαν πρόνοιαν. Ἦν μὲν γὰρ ὁ',
                           'html_line': 29441,
                           'html_column': 64,
                           'unit_index': 12652,
                           'codex': '258',
                           'bekker': '480a'},
                          {'text': 'Ἀρσένιος τῆς ἐν Ἀλεξανδρείᾳ ἐκκλησίας ἀναγνώστης, \n'
                                   'καί ποτε δίκην αἰσχρᾶς αἰτίας μέλλων ὑπέχειν ἐξαρ‐ \n'
                                   'πάζεται μὲν ὑπὸ Ἀθανασίου, δρασμῷ δὲ τὴν σωτηρίαν \n'
                                   'καρποῦται, καὶ τὸ ἀφανὲς τοῦ φυγάδος θαρρεῖν τῷ \n'
                                   'πλάσματι τῆς δυσσεβείας ὑπετίθετο. Ἀλλ’ οἶκτον λα‐',
                           'html_line': 29445,
                           'html_column': 65,
                           'unit_index': 12653,
                           'codex': '258',
                           'bekker': '480a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'συναθροίζεται',
              'refs': [{'html_line': 29437,
                        'html_column': 119,
                        'unit_index': 12651,
                        'codex': '258',
                        'bekker': '480a',
                        'start': 40,
                        'end': 44},
                       {'html_line': 29437,
                        'html_column': 119,
                        'unit_index': 12651,
                        'codex': '258',
                        'bekker': '480a',
                        'start': 47,
                        'end': 56}],
              'tokens': [{'text': 'συναθροίζεται',
                          'refs': [{'html_line': 29437,
                                    'html_column': 119,
                                    'unit_index': 12651,
                                    'codex': '258',
                                    'bekker': '480a',
                                    'start': 40,
                                    'end': 44},
                                   {'html_line': 29437,
                                    'html_column': 119,
                                    'unit_index': 12651,
                                    'codex': '258',
                                    'bekker': '480a',
                                    'start': 47,
                                    'end': 56}],
                          'source_index': 302750}],
              'surface': 'συναθροίζεται',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 7,
                                              'corrected_start': 0,
                                              'corrected_text': 'δροῖζε?',
                                              'end': 7,
                                              'evidence': 'Every retained word and unchanged span was '
                                                          'directly compared with Bekker physical page 215 / '
                                                          'printed page 480. Both body columns and enlarged '
                                                          'strips were inspected. The digital witness is '
                                                          'separately retained, including contrary readings.',
                                              'fragments': [],
                                              'original_text': 'δροῖζε?',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '77e04a08ce30b8996345a08606a156aef35a52d3a0738986de222ef15a6bda43',
                                                            'text': 'δροῖζε?'},
                                                           {'image_sha256': '2fbb79222df4dd73744d217a31804ce5fb306bd71e054005216b1da5f5ac39eb',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 215,
                                                            'region': [0.21, 0.095, 0.61, 0.77],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'θροίζε[ται?]'},
                                                           {'boundary_fragments': [{'end': 8,
                                                                                    'full_token': {'end': 1135,
                                                                                                   'start': 1123,
                                                                                                   'text': 'συναθροίζετο'},
                                                                                    'start': 0,
                                                                                    'text': 'θροίζετο'}],
                                                            'end': 1135,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s492',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 1127,
                                                            'text': 'θροίζετο'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T14:23:29Z',
                                              'scan': {'image_sha256': '2fbb79222df4dd73744d217a31804ce5fb306bd71e054005216b1da5f5ac39eb',
                                                       'max_side': 3600,
                                                       'observed_text': 'θροίζε[ται?]',
                                                       'physical_page': 215,
                                                       'printed_page': 480,
                                                       'region': [0.21, 0.095, 0.61, 0.77],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand directly identified ου, '
                                                                          'στ, καὶ and γὰρ type. Preserve '
                                                                          'unresolved type as explicit '
                                                                          'uncertainty. Join internal line '
                                                                          'divisions only within a retained '
                                                                          'passage; preserve boundary '
                                                                          'fragments. Distinguish marginal '
                                                                          'references and line numbers from '
                                                                          'body text. Keep declared '
                                                                          'quotation delimiters.',
                                              'uncertainty': 'The contracted ending differs among witnesses '
                                                             'and remains unresolved.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'δροῖζε?',
                                                  'decision': 'retained',
                                                  'evidence': 'The Tyre council clause has βασιλέως '
                                                              'προστάττοντος συναθροίζεται καὶ '
                                                              'προχειρίζεται. The preceding current '
                                                              'row215.25 ends συνα-, making this target only '
                                                              'the following divided-word suffix. Do not '
                                                              'duplicate the prefix by inserting the '
                                                              'complete source word; retain pending a joint '
                                                              'boundary review.',
                                                  'location_evidence': {'source_sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                        'status': 'held-no-immediate-reliable-boundaries'},
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0215.26',
                                                  'manual_review': {'module': 'photius_remaining_manual_b',
                                                                    'review': {'evidence': 'The Tyre council '
                                                                                           'clause has '
                                                                                           'βασιλέως '
                                                                                           'προστάττοντος '
                                                                                           'συναθροίζεται '
                                                                                           'καὶ '
                                                                                           'προχειρίζεται. '
                                                                                           'The preceding '
                                                                                           'current '
                                                                                           'row215.25 ends '
                                                                                           'συνα-, making '
                                                                                           'this target only '
                                                                                           'the following '
                                                                                           'divided-word '
                                                                                           'suffix. Do not '
                                                                                           'duplicate the '
                                                                                           'prefix by '
                                                                                           'inserting the '
                                                                                           'complete source '
                                                                                           'word; retain '
                                                                                           'pending a joint '
                                                                                           'boundary review.',
                                                                               'held_reason': 'source-word-boundary',
                                                                               'inherited_record_sha256': '7233a1f2e434c5a6cb49104f547ec6952f2140ca3fa70a76b2d8794f827946ad',
                                                                               'kind': 'manually-located-editorial-counterpart',
                                                                               'original_row_sha256': '34279e6fbf9e6edec2b4bbf0654ba21e7ef6d14c30415fcba156882c548cf221',
                                                                               'original_text': 'δροῖζε?',
                                                                               'qualification': 'An '
                                                                                                'editorial '
                                                                                                'source '
                                                                                                'preference, '
                                                                                                'not '
                                                                                                'independent '
                                                                                                'resolution '
                                                                                                'of the '
                                                                                                'Bekker ink. '
                                                                                                'Original '
                                                                                                'scan '
                                                                                                'observations, '
                                                                                                'contrary '
                                                                                                'readings, '
                                                                                                'and '
                                                                                                'independent '
                                                                                                'exclusions '
                                                                                                'remain '
                                                                                                'authoritative.',
                                                                               'readings': [],
                                                                               'rendering': {},
                                                                               'reviewed_at': '2026-10-21T23:14:28.998247+00:00',
                                                                               'reviewed_extent': {'end': 7,
                                                                                                   'start': 0},
                                                                               'source_context': {'qualification': 'An '
                                                                                                                   'exact '
                                                                                                                   'bounded '
                                                                                                                   'context '
                                                                                                                   'for '
                                                                                                                   'this '
                                                                                                                   'occurrence; '
                                                                                                                   'a '
                                                                                                                   'held '
                                                                                                                   'context '
                                                                                                                   'does '
                                                                                                                   'not '
                                                                                                                   'assert '
                                                                                                                   'a '
                                                                                                                   'counterpart.',
                                                                                                  'sha256': '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa',
                                                                                                  'source_id': 'tlg-photius-henry',
                                                                                                  'tokens': [{'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 45,
                                                                                                                        'html_column': 25,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 41,
                                                                                                                        'unit_index': 12650},
                                                                                                                       {'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 5,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 0,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302744,
                                                                                                              'text': 'συνέδριον'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 8,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 6,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302745,
                                                                                                              'text': 'δ’'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 11,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 9,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302746,
                                                                                                              'text': 'ἐν'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 16,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 12,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302747,
                                                                                                              'text': 'Τύρῳ'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 25,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 17,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302748,
                                                                                                              'text': 'βασιλέως'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 39,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 26,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302749,
                                                                                                              'text': 'προστάττοντος'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 44,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 40,
                                                                                                                        'unit_index': 12651},
                                                                                                                       {'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 56,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 47,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302750,
                                                                                                              'text': 'συναθροίζεται'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 61,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 58,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302751,
                                                                                                              'text': 'καὶ'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 75,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 62,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302752,
                                                                                                              'text': 'προχειρίζεται'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 78,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 76,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302753,
                                                                                                              'text': 'τὸ'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 88,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 79,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302754,
                                                                                                              'text': 'βασιλικὸν'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 96,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 89,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302755,
                                                                                                              'text': 'βούλημα'},
                                                                                                             {'refs': [{'bekker': '480a',
                                                                                                                        'codex': '258',
                                                                                                                        'end': 102,
                                                                                                                        'html_column': 119,
                                                                                                                        'html_line': 29437,
                                                                                                                        'start': 97,
                                                                                                                        'unit_index': 12651}],
                                                                                                              'source_index': 302756,
                                                                                                              'text': 'ἄνδρα'}],
                                                                                                  'tokens_sha256': '97d81a0b375d3276a12588728da99f31b0d2e4255af1c65a4e4d00888de5bc4f'},
                                                                               'surface_sha256': None}},
                                                  'original_text': 'δροῖζε?',
                                                  'readings': [],
                                                  'reason': 'individually-held-reading',
                                                  'segment_index': 0}}],
  'surface_sha256': '8766aa049621650dfd250201e63c63f789d1b4683c0107728f21c04c99a21c76'},
 {'id': 'boundary-0247.43',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0247.43',
                  'segment_index': 0,
                  'start': 0,
                  'end': 8,
                  'original_text': 'δείκνυσι',
                  'inherited_record_sha256': '2cbd9a100e3295e637b7c270218e94fa523367b2bd3d5b939d40e48a1128fb27',
                  'original_segment_sha256': 'e73321a243a3507bb9b6646179a347817b22994904fdbb6a186bbe2a0c022267'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0247.42',
             'start': 44,
             'end': 48,
             'original_text': 'ἀνα-',
             'corrected_text': '',
             'original_row_sha256': '4ac1fdfb5bec165bf194358a1d497958e50c3738106751a5ea20643a9c252283'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0247.43',
             'start': 0,
             'end': 8,
             'original_text': 'δείκνυσι',
             'corrected_text': 'ἀναδείκνυται',
             'original_row_sha256': '66d072d7232e830f66a21a7558a53037a354a52e400341a0677b62ef17b0671b'}],
  'evidence': 'The inspected source divides ἀνα- and δείκνυται after θάνατος τόκου πατήρ, followed by καινὸς '
              'οὗτος. Henry supplies complete ἀναδείκνυται; retain the prior δείκνυσι and tentative source '
              'ending in the audit.',
  'scan': {'image_sha256': 'daaf12a447ec0990042aa4e67c580241639a9dae9fb4b6ecf7c513702c2421f9',
           'max_side': 3600,
           'observed_text': 'ἀνα-\nδείκνυται',
           'physical_page': 247,
           'printed_page': 512,
           'region': [0.57, 0.105, 0.95, 0.735],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 13506,
                'stop': 13510,
                'units_sha256': '436c787bdc4ff1b4a9dcea4f429e8625ce2d71039fa2df51ea23fc7cf7e3e725',
                'units': [{'text': 'λαβοῦσα τὰ σπέρματα μιμεῖται τὰ μνήματα, καὶ σήπει \n'
                                   'τὸν κόκκον ὡς τάφος τὸ σῶμα, καὶ δεξαμένη ζῶντα \n'
                                   'καταφθείρει νεκρότητι, μέσην τε σαφῶς τὴν τοῦ κόκ‐ \n'
                                   'κου διασήψασα καρδίαν ἄχρηστον καὶ μύρμηξιν εἰς \n'
                                   'τροφὴν ἀπεργάζεται. Ὥσπερ δέ τινα σύλληψιν τὴν φθο‐',
                           'html_line': 31481,
                           'html_column': 61,
                           'unit_index': 13506,
                           'codex': '276',
                           'bekker': '512b'},
                          {'text': 'ρὰν κτησαμένη, κυοφορεῖ νεκρωθέντα τῇ σήψει τῶν \n'
                                   'σπερμάτων τὰ ἔμβρυα· καὶ γίνεται μήτηρ ζωῆς τοῖς \n'
                                   'κόκκοις ἡ νέκρωσις, καὶ θάνατος τόκου πατὴρ ἀνα‐ \n'
                                   'δείκνυται.',
                           'html_line': 31485,
                           'html_column': 65,
                           'unit_index': 13507,
                           'codex': '276',
                           'bekker': '512b'},
                          {'text': 'Καινὸς οὗτος τῇ γῇ τῶν ὠδίνων ὁ νόμος· ἂν \n'
                                   'μὴ γένηται νεκρὸν τὸ βρέφος, οὐ πλάττεται· ἂν ζῇ, οὐ',
                           'html_line': 31488,
                           'html_column': 44,
                           'unit_index': 13508,
                           'codex': '276',
                           'bekker': '512b'},
                          {'text': 'μορφοῦται. Ταύτῃ ἄρα καὶ μύρμηκες τετμημένους τοὺς \n'
                                   'κόκκους εἰς γῆν ἀποτίθενται, τῇ τομῇ τὴν ἀπὸ τῆς νε‐ \n'
                                   'κρώσεως βλάστησιν κωλύοντες· ἔδει γὰρ καὶ μυρμήκων',
                           'html_line': 31489,
                           'html_column': 66,
                           'unit_index': 13509,
                           'codex': '276',
                           'bekker': '512b'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'ἀναδείκνυται',
              'refs': [{'html_line': 31485,
                        'html_column': 65,
                        'unit_index': 13507,
                        'codex': '276',
                        'bekker': '512b',
                        'start': 143,
                        'end': 146},
                       {'html_line': 31485,
                        'html_column': 65,
                        'unit_index': 13507,
                        'codex': '276',
                        'bekker': '512b',
                        'start': 149,
                        'end': 158}],
              'tokens': [{'text': 'ἀναδείκνυται',
                          'refs': [{'html_line': 31485,
                                    'html_column': 65,
                                    'unit_index': 13507,
                                    'codex': '276',
                                    'bekker': '512b',
                                    'start': 143,
                                    'end': 146},
                                   {'html_line': 31485,
                                    'html_column': 65,
                                    'unit_index': 13507,
                                    'codex': '276',
                                    'bekker': '512b',
                                    'start': 149,
                                    'end': 158}],
                          'source_index': 323175}],
              'surface': 'ἀναδείκνυται',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0247.43',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 8,
                                              'corrected_start': 0,
                                              'corrected_text': 'δείκνυσι',
                                              'end': 8,
                                              'evidence': 'Every retained word and unchanged span was '
                                                          'directly compared with Bekker physical page 247 / '
                                                          'printed page 512. Both body columns and enlarged '
                                                          'strips were inspected. The digital witness is '
                                                          'separately retained, including contrary readings.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 8,
                                                             'lexical_eligible': False,
                                                             'qualification': 'The printed word crosses a '
                                                                              'retained passage boundary. '
                                                                              'Keep this visible fragment '
                                                                              'separate and exclude it from '
                                                                              'lexical counts.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'δείκνυσι'}],
                                              'original_text': 'δείκνυσι',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '81cbae55243c6861c838d3653543b03cd05801e4612db31df281e68d76741bd1',
                                                            'text': 'δείκνυσι'},
                                                           {'image_sha256': 'daaf12a447ec0990042aa4e67c580241639a9dae9fb4b6ecf7c513702c2421f9',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 247,
                                                            'region': [0.57, 0.105, 0.95, 0.735],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'δείκνυ[ται]'},
                                                           {'boundary_fragments': [{'end': 7,
                                                                                    'full_token': {'end': 3655,
                                                                                                   'start': 3645,
                                                                                                   'text': 'ἀναδείκνυθ'},
                                                                                    'start': 0,
                                                                                    'text': 'δείκνυθ'}],
                                                            'end': 3655,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s524',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 3648,
                                                            'text': 'δείκνυθ'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:14:07Z',
                                              'scan': {'image_sha256': 'daaf12a447ec0990042aa4e67c580241639a9dae9fb4b6ecf7c513702c2421f9',
                                                       'max_side': 3600,
                                                       'observed_text': 'δείκνυ[ται]',
                                                       'physical_page': 247,
                                                       'printed_page': 512,
                                                       'region': [0.57, 0.105, 0.95, 0.735],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand directly identified ου, '
                                                                          'στ, καὶ and γὰρ type. Preserve '
                                                                          'unresolved type as explicit '
                                                                          'uncertainty. Join internal line '
                                                                          'divisions only within a retained '
                                                                          'passage; preserve boundary '
                                                                          'fragments. Distinguish marginal '
                                                                          'references and line numbers from '
                                                                          'body text. Keep declared '
                                                                          'quotation delimiters.',
                                              'uncertainty': 'The contracted verb ending remains unresolved; '
                                                             'retain the boundary fragment.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'δείκνυσι',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0247.43',
                                                  'original_text': 'δείκνυσι',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': 'cc4c0195b924c3264d94bae019a4016142b0e1a21d5f6e79425eb74a7aeeada4'},
 {'id': 'boundary-0250.3',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0250.3',
                  'segment_index': 0,
                  'start': 0,
                  'end': 5,
                  'original_text': 'γάγεῖ',
                  'inherited_record_sha256': '88af1c0d5fec4e559549cebb1d88042c1a1e66f4ea9e72dd440b8ee2978e293f',
                  'original_segment_sha256': '6116434a5c733b8a452a64b9f22b9eed2ba2a5672944a05100f42671543959d5'}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0250.2',
             'start': 46,
             'end': 50,
             'original_text': 'ἐπα-',
             'corrected_text': '',
             'original_row_sha256': '9d5b3cefc0a07b3763d9be272d6b70ee3fb8c08e454147b86cc6b70bafe12c5c'},
            {'locus': 'helladius_chrestomathia_photius_bekker_v2_0250.3',
             'start': 0,
             'end': 5,
             'original_text': 'γάγεῖ',
             'corrected_text': 'ἐπανάγεται',
             'original_row_sha256': 'eb2d81554a570dd0df87267ded1d17c409a6a548c72f818c59469d5d9717500c'}],
  'evidence': 'The inspected source has εὐκόλως ἐπα- at the preceding line end and νάγεται μορφήν on the '
              'next line. Henry gives complete ἐπανάγεται. Remove only the reviewed prefix fragment and '
              'replace only the incorrect suffix, preserving the comma after μορφήν and the later με- '
              'fragment.',
  'scan': {'image_sha256': '9e6607454dedcf7ffa3d455ecc32d1a999258e8789f64c9060ddce94b1bb4986',
           'max_side': 3600,
           'observed_text': 'ἐπα-\nνάγεται',
           'physical_page': 250,
           'printed_page': 515,
           'region': [0.05, 0.105, 0.43, 0.735],
           'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                      'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
           'qualification': 'Direct inspection establishes the declared physical boundary or marginal '
                            'artifact. The selected Henry spelling is an explicit editorial preference; it '
                            'does not certify every Bekker letter or normalize contrary readings.'},
  'selection': {'first': 13557,
                'stop': 13561,
                'units_sha256': '77d8286f3f9a9ec22dcf0157f80191fa9899432037978e6aefaddf252fd8f73b',
                'units': [{'text': 'καὶ συνέσεως ὑπερέχουσα, καὶ τὴν τῶν ὅλων οὐσίαν ἐν \n'
                                   'ἑαυτῇ συλλαβοῦσα καὶ περιέχουσα, καὶ τὴν πολύτροπον \n'
                                   'τῶν σωμάτων σύγκρισιν καὶ μῖξιν ἐν τοῖς τῆς φύσεως \n'
                                   'εὐκρινῆ συντηρεῖ ταμιείοις. Οὐ γὰρ ἔξω τῆς ἐν τῇ κτίσει φύ‐',
                           'html_line': 31618,
                           'html_column': 66,
                           'unit_index': 13557,
                           'codex': '276',
                           'bekker': '514b'},
                          {'text': 'σεως ἡ τοῦ σώματος φύσις, κἂν διὰ μυρίων ῥέῃ \n'
                                   'λυομένη θανάτων. Διὸ πρὸς τὴν οἰκείαν εὐκόλως ἐπα‐ \n'
                                   'νάγεται μορφήν, καὶ κοινωνεῖ τῶν τιμῶν, ὧν αὐτῇ με‐ \n'
                                   'τασχεῖν ἔδει συνδιενεγκούσῃ καὶ τοὺς ἄθλους.',
                           'html_line': 31621,
                           'html_column': 112,
                           'unit_index': 13558,
                           'codex': '276',
                           'bekker': '515a'},
                          {'text': 'Τοῦ αὐτοῦ ἐκ τοῦ εἰς τὴν ἀνάληψιν αʹ λόγου. \n',
                           'html_line': 31624,
                           'html_column': 106,
                           'unit_index': 13559,
                           'codex': '276',
                           'bekker': '515a'},
                          {'text': 'Τὸ προοίμιον.',
                           'html_line': 31625,
                           'html_column': 20,
                           'unit_index': 13560,
                           'codex': '276',
                           'bekker': '515a'}]},
  'reading': {'source_id': 'tlg-photius-henry',
              'role': 'chosen',
              'text': 'ἐπανάγεται',
              'refs': [{'html_line': 31621,
                        'html_column': 112,
                        'unit_index': 13558,
                        'codex': '276',
                        'bekker': '515a',
                        'start': 92,
                        'end': 95},
                       {'html_line': 31621,
                        'html_column': 112,
                        'unit_index': 13558,
                        'codex': '276',
                        'bekker': '515a',
                        'start': 98,
                        'end': 105}],
              'tokens': [{'text': 'ἐπανάγεται',
                          'refs': [{'html_line': 31621,
                                    'html_column': 112,
                                    'unit_index': 13558,
                                    'codex': '276',
                                    'bekker': '515a',
                                    'start': 92,
                                    'end': 95},
                                   {'html_line': 31621,
                                    'html_column': 112,
                                    'unit_index': 13558,
                                    'codex': '276',
                                    'bekker': '515a',
                                    'start': 98,
                                    'end': 105}],
                          'source_index': 324551}],
              'surface': 'ἐπανάγεται',
              'separators': [],
              'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'contrary_readings': [{'identity': {'locus': 'helladius_chrestomathia_photius_bekker_v2_0250.3',
                                      'segment_index': 0},
                         'original_segment': {'corrected_end': 5,
                                              'corrected_start': 0,
                                              'corrected_text': 'γάγεῖ',
                                              'end': 5,
                                              'evidence': 'Every retained word and unchanged span was '
                                                          'directly compared with Bekker physical page 250 / '
                                                          'printed page 515. Both body columns and enlarged '
                                                          'strips were inspected. The digital witness is '
                                                          'separately retained, including contrary readings.',
                                              'fragments': [{'classification': 'source-confirmed-word-fragment',
                                                             'end': 5,
                                                             'lexical_eligible': False,
                                                             'qualification': 'The printed word crosses a '
                                                                              'retained passage boundary. '
                                                                              'Keep this visible fragment '
                                                                              'separate and exclude it from '
                                                                              'lexical counts.',
                                                             'side': 'leading',
                                                             'start': 0,
                                                             'text': 'γάγεῖ'}],
                                              'original_text': 'γάγεῖ',
                                              'readings': [{'kind': 'original',
                                                            'source_row_sha256': '0f3493ba70f3753a3b97806027dd0b1a04153488256189988b779db82f06d318',
                                                            'text': 'γάγεῖ'},
                                                           {'image_sha256': '9e6607454dedcf7ffa3d455ecc32d1a999258e8789f64c9060ddce94b1bb4986',
                                                            'kind': 'direct-scan',
                                                            'physical_page': 250,
                                                            'region': [0.05, 0.105, 0.43, 0.735],
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'},
                                                            'text': 'νάγε[ται]'},
                                                           {'boundary_fragments': [{'end': 5,
                                                                                    'full_token': {'end': 98,
                                                                                                   'start': 90,
                                                                                                   'text': 'ἐπανάγει'},
                                                                                    'start': 0,
                                                                                    'text': 'νάγει'}],
                                                            'end': 98,
                                                            'kind': 'digital',
                                                            'role': 'recorded-source-reading',
                                                            'section': 'tlg4040-tlg001-local002-s527',
                                                            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-library.json.gz',
                                                                       'sha256': '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'},
                                                            'start': 93,
                                                            'text': 'νάγει'}],
                                              'review_basis': 'direct-scan-inspection',
                                              'reviewed_at': '2026-10-21T13:22:48Z',
                                              'scan': {'image_sha256': '9e6607454dedcf7ffa3d455ecc32d1a999258e8789f64c9060ddce94b1bb4986',
                                                       'max_side': 3600,
                                                       'observed_text': 'νάγε[ται]',
                                                       'physical_page': 250,
                                                       'printed_page': 515,
                                                       'region': [0.05, 0.105, 0.43, 0.735],
                                                       'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                                                                  'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
                                              'start': 0,
                                              'text_role': 'authorial-body',
                                              'transcription_convention': 'Expand directly identified ου, '
                                                                          'στ, καὶ and γὰρ type. Preserve '
                                                                          'unresolved type as explicit '
                                                                          'uncertainty. Join internal line '
                                                                          'divisions only within a retained '
                                                                          'passage; preserve boundary '
                                                                          'fragments. Distinguish marginal '
                                                                          'references and line numbers from '
                                                                          'body text. Keep declared '
                                                                          'quotation delimiters.',
                                              'uncertainty': 'The contracted verb ending remains unresolved; '
                                                             'retain its visible boundary fragment.',
                                              'verification': 'uncertain'},
                         'previous_disposition': {'corrected_text': 'γάγεῖ',
                                                  'decision': 'retained',
                                                  'evidence': 'The word crosses a retained passage boundary; '
                                                              'preserve its fragment exclusion until a joint '
                                                              'group is verified.',
                                                  'locus': 'helladius_chrestomathia_photius_bekker_v2_0250.3',
                                                  'original_text': 'γάγεῖ',
                                                  'readings': [],
                                                  'reason': 'split-word',
                                                  'segment_index': 0}}],
  'surface_sha256': '28e50457dda7350a93f3f1163a758196f05d7e32116fdf8a850fb61b89003e41'}]

EXPECTED_SCOPE = frozenset((i['locus'], i['segment_index'])
    for spec in SPECS for i in spec['identities'])


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _placements(spec):
    """Map each nonempty edit to its exact complete source-token sequence."""
    reading = spec['reading']
    tokens = reading['tokens']
    placements = []
    cursor = 0
    for edit in spec['edits']:
        if not edit['corrected_text']:
            continue
        wanted = [edition.normalize(m.group()) for m in edition.WORD.finditer(edit['corrected_text'])]
        selected = tokens[cursor:cursor + len(wanted)]
        if not wanted or [edition.normalize(m.group()) for t in selected for m in edition.WORD.finditer(t['text'])] != wanted:
            raise ValueError('A joint replacement no longer owns its complete source words')
        placements.append({'locus': edit['locus'], 'start': edit['start'], 'end': edit['end'],
            'corrected_text': edit['corrected_text'],
            'source_indices': [t['source_index'] for t in selected]})
        cursor += len(wanted)
    if cursor != len(tokens):
        raise ValueError('A joint decision duplicates or omits a chosen source token')
    return placements


def _record(spec, units, reviewed_at):
    import prepare_photius_review_campaign as campaign
    campaign._timestamp(reviewed_at)
    selection = spec['selection']
    if (not isinstance(units, list) or _digest(units) != selection['units_sha256']
            or [u.get('unit_index') for u in units] != list(range(selection['first'], selection['stop']))):
        raise ValueError('The authored boundary context lost its exact decoded source units')
    reading = deepcopy(spec['reading'])
    if (reading['surface'] != unicodedata.normalize('NFC', reading['surface'])
            or _digest({k: reading[k] for k in ('surface', 'separators', 'boundary_suffix')}) != spec['surface_sha256']):
        raise ValueError('A joint word lost its exact source punctuation or Unicode surface')
    indices = [t['source_index'] for t in reading['tokens']]
    if (not indices or any(type(i) is not int or i < 0 for i in indices)
            or any(b != a + 1 for a, b in zip(indices, indices[1:]))):
        raise ValueError('A joint reading requires exact consecutive full-edition token indices')
    review_ranges = [{k: deepcopy(e[k]) for k in ('locus', 'start', 'end', 'original_text', 'original_row_sha256')}
                     for e in spec['edits']]
    return {'id': spec['id'], 'kind': 'source-reviewed-joint-word-boundary',
        'identities': deepcopy(spec['identities']), 'edits': deepcopy(spec['edits']),
        'review_ranges': review_ranges, 'disposition': 'joint-editorial-word-choice',
        'text_role': 'authorial-body', 'lexical_eligible': True,
        'glyph_resolved': False, 'evidence': spec['evidence'], 'reviewed_at': reviewed_at,
        'qualification': 'The complete Henry word is chosen under the explicit supplied-edition editorial policy. Direct scan review establishes the occurrence and boundary; all old tentative readings, contrary witnesses, original rows, and unrelated exclusions remain historical evidence. These bounded decisions do not certify entire rows.',
        'scan': [deepcopy(spec['scan'])], 'readings': [reading], 'word_source': deepcopy(reading),
        'surface_sha256': spec['surface_sha256'], 'source_placements': _placements(spec),
        'superseded_source_refs': [],
        'source_context': {'source_id': SOURCE_ID, 'sha256': SOURCE_SHA256,
            'units_sha256': selection['units_sha256'], 'units': deepcopy(units)},
        'contrary_readings': deepcopy(spec['contrary_readings'])}


def validate_record(record):
    """Reconstruct the whole authored decision for public-literal replay."""
    if not isinstance(record, dict):
        raise ValueError('A boundary decision must be a complete record')
    specs = [s for s in SPECS if s['id'] == record.get('id')]
    context = record.get('source_context')
    if len(specs) != 1 or not isinstance(context, dict):
        raise ValueError('Unknown joint boundary identity or source context')
    expected = _record(specs[0], context.get('units'), record.get('reviewed_at'))
    if record != expected:
        raise ValueError('The joint boundary decision differs from its authored authority')
    return deepcopy(expected)


def review_final(html_raw, rows_mapping, document, crop_png, *, reviewed_at=REVIEWED_AT):
    """Validate live preimages and source pixels, returning thirteen pure plans."""
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied boundary comparison HTML changed or was invalidated')
    import prepare_photius_editorial_continuation as preparer
    import repair_photius_editorial_substitutions as previous
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    source_units = preparer.source_document(html_raw)
    source = {'id': SOURCE_ID, 'edition': 'Henry, Photius Bibliothèque, volumes 1–8 (1959–1977)',
        'citation': 'Photius, Bibliotheca, TLG 4040.001', 'sha256': SOURCE_SHA256}
    known = previous._source_tokens(html_raw, source)
    result, seen_identities, seen_refs, last_index = [], set(), set(), -1
    crop_digests = {}
    for spec in SPECS:
        for edit in spec['edits']:
            row = rows_mapping.get(edit['locus'])
            if (not isinstance(row, dict) or _digest(row) != edit['original_row_sha256']
                    or row['text'][edit['start']:edit['end']] != edit['original_text']):
                raise ValueError('A joint boundary lost its exact released row preimage')
        for identity in spec['identities']:
            key = identity['locus'], identity['segment_index']
            if key in seen_identities:
                raise ValueError('A joint boundary repeats an inherited identity')
            seen_identities.add(key)
            if not any(e['locus'] == identity['locus'] and e['start'] <= identity['start']
                       and identity['end'] <= e['end'] for e in spec['edits']):
                raise ValueError('A joint edit does not cover its entire inherited identity')
        scan = spec['scan']
        geometry = scan['physical_page'], tuple(scan['region'])
        if geometry not in crop_digests:
            crop_digests[geometry] = hashlib.sha256(crop_png(document, geometry[0], list(geometry[1]))).hexdigest()
        if crop_digests[geometry] != scan['image_sha256']:
            raise ValueError('A directly reviewed joint source image changed')
        selection = spec['selection']
        record = _record(spec, parser.units[selection['first']:selection['stop']], reviewed_at)
        reading = record['word_source']
        for token in reading['tokens']:
            key = _digest(token['refs'])
            index, actual = known[key]
            if index != token['source_index'] or actual['text'] != token['text']:
                raise ValueError('A joint word lost its exact whole-edition source identity')
            if key in seen_refs or index <= last_index:
                raise ValueError('Joint source words are duplicated or cross their source order')
            seen_refs.add(key)
            last_index = index
        attributed = preparer.attributed_span(reading, source_units)
        if any(reading[k] != attributed[k] for k in ('surface', 'separators', 'boundary_suffix')):
            raise ValueError('A joint word lost its exact attributed source surface')
        result.append(record)
    if seen_identities != EXPECTED_SCOPE or len(result) != len(SPECS):
        raise ValueError('The authored joint boundary scope changed')
    return result
