"""Source observations for twelve final non-boundary Photius occurrences.

Each observation fixes one exact current preimage and preserves the preceding
source record. Modern references, bracketed variants, source corrections, and
explicit editorial word or omission choices have separate dispositions. No
routine in this helper changes corpus data or an earlier published archive.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import unicodedata

import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-22T00:54:48.654868Z'
SOURCE_ID = 'tlg-photius-henry'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
PRIOR = 'data/corpus_changes/photius-bekker-editorial-continuation/compiled-review.json.gz'
SOURCE_PINS = {'data/corpus_changes/photius-bekker-readings/source-scan.pdf': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
 'data/corpus_changes/photius-bekker-editorial-continuation/compiled-review.json.gz': '92e1bda2d83523cb07f8611c429bd869d819dea9a9decd71da5809f0e0d99d4a'}
SPECS = [{'id': 'photius-final-source-0018-36-s3',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0018.36',
                  'segment_index': 3}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0018.36',
             'start': 47,
             'end': 48,
             'original_text': '“',
             'corrected_text': '“',
             'original_row_sha256': 'f8ae18ee5fcb0ccc8908a5acf2d0f6f6b0dba8d26fde4bc8bb4a6153bebdc768'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0018.36',
                     'start': 47,
                     'end': 48,
                     'original_text': '“',
                     'original_row_sha256': 'f8ae18ee5fcb0ccc8908a5acf2d0f6f6b0dba8d26fde4bc8bb4a6153bebdc768'}],
  'disposition': 'classify-nonlexical-mark',
  'text_role': 'nonlexical-mark',
  'lexical_eligible': False,
  'glyph_resolved': False,
  'evidence': 'The exact retained high mark stands before συγκεφα- in the bishops-count line. '
              'Direct inspection confirms a raised nonlexical typographic mark, separate from the '
              'following word. Preserve its existing display rather than infer deletion from '
              'Henry, which continues directly to συγκεφαλαιωθέντος.',
  'qualification': 'Classification of nonlexical typography does not determine whether the tiny '
                   'mark is a quotation sign, reference sign, or printing artifact.',
  'scan': [{'physical_page': 18,
            'printed_page': 283,
            'region': [0.035, 0.592, 0.425, 0.655],
            'max_side': 3600,
            'image_sha256': '82fc6529de42b49345bc895f05355c1c1ccea66488ba30f25daefd758a392021',
            'observed_text': 'Raised nonlexical mark before συγκεφα-.',
            'qualification': 'The high mark is outside the following Greek word; its precise '
                             'quotation/apparatus shape is not used as lexical evidence.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (7273, 7276),
  'context_sha256': 'a4186e9acf466ca81516d8315b506b48132e34a477dc9d346e5dd8e5d8b951a2',
  'prior_identity_sha256': '8e082a1c2752d2371d3eb0e60d41a4347387c91db77fcebca1c06259d4d31e79',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0037-4-s5',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0037.4', 'segment_index': 5}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0037.4',
             'start': 916,
             'end': 920,
             'original_text': '[μὴ]',
             'corrected_text': '[μὴ]',
             'original_row_sha256': '31b0bf535327c7eac1f0cdc776d051c40b89dd549eb0e9d93115e5430a1ab6e4'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0037.4',
                     'start': 916,
                     'end': 920,
                     'original_text': '[μὴ]',
                     'original_row_sha256': '31b0bf535327c7eac1f0cdc776d051c40b89dd549eb0e9d93115e5430a1ab6e4'}],
  'disposition': 'retain-edition-variant',
  'text_role': 'printed-bracketed-reading',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'Bekker physically prints [μὴ] between ὅπως and δι’ ἑαυτόν. Henry omits this word at '
              'the same location. Preserve the visible Bekker variant and its brackets; the empty '
              'Henry interval does not authorize an unrecorded deletion.',
  'qualification': 'Printed brackets and Henry omission do not independently date or attribute the '
                   'supplied material. Keep this bounded printed-bracketed reading outside lexical '
                   'admission.',
  'scan': [{'physical_page': 37,
            'printed_page': 302,
            'region': [0.575, 0.4, 0.965, 0.475],
            'max_side': 3600,
            'image_sha256': '201e39c7bdd0bacf93da52a31bee932b3feeaa8fd89be2e994a532f1451b8b82',
            'observed_text': 'ὅπως [μὴ] δι’ ἑαυτὸν ἀλλὰ μὴ διὰ κόσμον',
            'qualification': 'The printed bracket pair and the bounded word are directly visible.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (7759, 7763),
  'context_sha256': '779f9851a30dd06dc93a4285c4935f2b7dddcf24ead3e6ef41c65834e3e5bf8e',
  'prior_identity_sha256': '3328880dc28cf0dfc9368e8ab12132f54e1d0ca86f414de593072465c2b5981c',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0038-11-s1',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.11',
                  'segment_index': 1}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.11',
             'start': 20,
             'end': 24,
             'original_text': '[μη]',
             'corrected_text': '[μὴ]',
             'original_row_sha256': '55a75d27e5bf670d33ad189161de0a598135bf954afb0814e762862c06864a59'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0038.11',
                     'start': 20,
                     'end': 24,
                     'original_text': '[μη]',
                     'original_row_sha256': '55a75d27e5bf670d33ad189161de0a598135bf954afb0814e762862c06864a59'}],
  'disposition': 'correct-scan-reading',
  'text_role': 'printed-bracketed-reading',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'Bekker prints the complete bracketed negative [μὴ] after ἐκ τοῦ and before ποιεῖν. '
              'Restore the visible accent to the exact retained [μη] preimage. Henry has no second '
              'negative here; retain that omission as contrary evidence, preserving the printed '
              'Bekker reading.',
  'qualification': 'Printed brackets and Henry omission do not independently establish editorial '
                   'authorship. The accent correction does not admit this bounded bracketed '
                   'reading to lexical counts.',
  'scan': [{'physical_page': 38,
            'printed_page': 303,
            'region': [0.055, 0.225, 0.425, 0.295],
            'max_side': 3600,
            'image_sha256': '0fb6998bc9c138cc222afd664132c78f9bcfe32e272c66b8066ceca0b89b8403',
            'observed_text': 'τὸ μὴ ποιεῖν ἐκ τοῦ [μὴ] ποιεῖν;',
            'qualification': 'The bracketed negative and its grave accent are visible in the '
                             'enlarged source line.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (7787, 7791),
  'context_sha256': '96f6ae26e5ba85c7ded1821fac447cdcc64c8e792fd5137d9c93d181bfa6337b',
  'prior_identity_sha256': '95e6d6ab9735da4522be19b2c2dc1e2fed843a9db7e1f525c3c542126a3f6208',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0152-4-s9',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0152.4', 'segment_index': 9}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0152.4',
             'start': 1871,
             'end': 1877,
             'original_text': 'χεῖρον',
             'corrected_text': 'σχεδόν',
             'original_row_sha256': '0a37a7c51a8fee455be85b3854aad9768667d82d3c873b98a50891030abb5b1c'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0152.4',
                     'start': 1871,
                     'end': 1877,
                     'original_text': 'χεῖρον',
                     'original_row_sha256': '0a37a7c51a8fee455be85b3854aad9768667d82d3c873b98a50891030abb5b1c'}],
  'disposition': 'editorial-word-choice',
  'text_role': 'authorial-body',
  'lexical_eligible': True,
  'glyph_resolved': False,
  'evidence': 'Both editions close the same argument with ἰσχυρότατον πάντων, the qualification ὡς '
              'ἐν ψεύδεσιν, and the following relative clause. Henry uniquely has σχεδόν in this '
              'clause, after ὂν, whereas the damaged Bekker target occurs before ὡς. Prefer the '
              'corresponding term σχεδόν while preserving Bekker’s existing clause order. This is '
              'an individually reviewed term correspondence, not a positional substitution or '
              'relocation of the clause.',
  'qualification': 'The compact Bekker sigma-chi group remains unresolved independently. The '
                   'supplied Henry term is preferred explicitly; all original and contrary '
                   'readings remain archived.',
  'scan': [{'physical_page': 152,
            'printed_page': 417,
            'region': [0.42, 0.597, 0.825, 0.665],
            'max_side': 3600,
            'image_sha256': '8150a66a5a5a4eb205248546b6d33d2ec7bf206b719ea7d3dadef111ad3cbbca',
            'observed_text': 'σχεδόν',
            'qualification': 'The compact sigma-chi group remains qualified as a Bekker glyph; the '
                             'chosen complete word is an editorial preference for Henry.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (10763, 10769),
  'context_sha256': '3fc0b68d2a802931807d9872b62bd981611b4f6a81507573732653bc6224c2b9',
  'prior_identity_sha256': '041d42220a6aa850b1c798b5a0fdaf00b5afaabc78928026ccbfae42db39b8a4',
  'word_selection': 'σχεδόν',
  'word_indices': [263369],
  'word_surface': {'surface': 'σχεδόν',
                   'separators': [],
                   'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0154-4-s1',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.4', 'segment_index': 1}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.4',
             'start': 8,
             'end': 17,
             'original_text': '[εἰ δ’ ὁ]',
             'corrected_text': '',
             'original_row_sha256': '8da994838c96a2e675bf5c9a3f7a7f56874e6a7e2ee6409aa228214377af897f'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.4',
                     'start': 8,
                     'end': 17,
                     'original_text': '[εἰ δ’ ὁ]',
                     'original_row_sha256': '8da994838c96a2e675bf5c9a3f7a7f56874e6a7e2ee6409aa228214377af897f'}],
  'disposition': 'editorial-word-choice-omission',
  'text_role': 'printed-bracketed-reading',
  'lexical_eligible': False,
  'glyph_resolved': False,
  'evidence': 'The exact current clause is ὅταν μὴ [εἰ δ’ ὁ] παύωνται πλημμελοῦντες. Henry’s '
              'uniquely corresponding clause is ὅταν μὴ παύωνται, followed by πλημμελοῦντες: μὴ '
              'and παύωνται are consecutive source tokens with an empty intervening Greek '
              'interval. Explicitly prefer Henry’s omission at this exact occurrence. This is a '
              'reviewed editorial preference for Henry’s edition, not a claim to '
              'have resolved Bekker’s final glyph and not a deletion inferred merely from a '
              'missing match.',
  'qualification': 'Archive the printed bracketed reading and all ὁ/οὐ/ἐξ alternatives. Printed '
                   'brackets and Henry omission do not establish authorship; the Bekker glyph '
                   'remains unresolved in its archived witness.',
  'scan': [{'physical_page': 154,
            'printed_page': 419,
            'region': [0.06, 0.12, 0.435, 0.205],
            'max_side': 3600,
            'image_sha256': '1164f5cfd1241d49961c5ebb3101f59e2c5ac74f592c4a2ecdcf4352d646bf3b',
            'observed_text': '[εἰ δ’ {ὁ/οὐ}]',
            'qualification': 'The printed bracket pair is certain; the final compact group remains '
                             'qualified, with the prior digital ἐξ also preserved.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (10808, 10813),
  'context_sha256': '7ec948718007e4379e857152e7a9b651c44ca50410594d56c2ebbe32e2d87408',
  'prior_identity_sha256': 'c6011319b9bb2ca75e99bc480651afca5bf2b5a2fabb71399de564a566e55e83',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': [{'text': 'μὴ',
                           'refs': [{'html_line': 25676,
                                     'html_column': 201,
                                     'unit_index': 10809,
                                     'codex': '247',
                                     'bekker': '419a',
                                     'start': 103,
                                     'end': 105}],
                           'source_index': 264029},
                          {'text': 'παύωνται',
                           'refs': [{'html_line': 25676,
                                     'html_column': 201,
                                     'unit_index': 10809,
                                     'codex': '247',
                                     'bekker': '419a',
                                     'start': 106,
                                     'end': 114}],
                           'source_index': 264030}],
  'residual_uncertainty': {'witness': 'archived-Bekker-reading',
                           'locus': 'helladius_chrestomathia_photius_bekker_v2_0154.4',
                           'start': 15,
                           'end': 16,
                           'original_text': 'ὁ',
                           'alternatives': [{'text': 'ὁ', 'kind': 'original'},
                                            {'text': 'οὐ', 'kind': 'prior-scan-observation'},
                                            {'text': 'ἐξ', 'kind': 'prior-digital-reading'}],
                           'glyph_resolved': False,
                           'current_display_retains': False,
                           'qualification': 'The source glyph remains unresolved in the archived '
                                            'Bekker witness. The served text follows the explicit '
                                            'Henry omission at the uniquely anchored empty '
                                            'interval.'}},
 {'id': 'photius-final-source-0155-1-s0',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0155.1', 'segment_index': 0}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0155.1',
             'start': 0,
             'end': 5,
             'original_text': '685 Ἡ',
             'corrected_text': '',
             'original_row_sha256': '5cf1aa32ac06cc9b8760176ce9620c910a2f212245340718c2c157d4426a1a1e'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0155.1',
                     'start': 0,
                     'end': 5,
                     'original_text': '685 Ἡ',
                     'original_row_sha256': '5cf1aa32ac06cc9b8760176ce9620c910a2f212245340718c2c157d4426a1a1e'}],
  'disposition': 'exclude-marginal-reference',
  'text_role': 'marginal-reference',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'The source places 685H. outside the body column immediately before the continuation '
              'διαφοράν. The retained 685 Ἡ combines that numeric edition reference with a '
              'Greek-looking OCR rendering of Latin H. Remove only the exact reference preimage '
              'from body display, retaining the following space and body word. Henry’s continuous '
              'sentence ends in διαφοράν without a reference token.',
  'qualification': 'Prior683H and the observed685H remain recorded numeric alternatives; reference '
                   'classification does not depend on choosing between their digits.',
  'scan': [{'physical_page': 155,
            'printed_page': 420,
            'region': [0.17, 0.1, 0.575, 0.158],
            'max_side': 3600,
            'image_sha256': '8bcf6336d8b06f32f5c3b235d2c76df4ebe6c3ade457ecbd7bb3aead2b853f20',
            'observed_text': '685H. διαφοράν.',
            'qualification': 'The H-suffixed number stands in the left margin; διαφοράν begins the '
                             'continuous body line to its right.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (10860, 10863),
  'context_sha256': 'dd5fea736a128cd337c1bbee5f17e2bc8572393da1807e34e798242c01fd10c3',
  'prior_identity_sha256': '02c312beec42cd5573f26d87ea2d0ac5754af5bf5d8e37030d92ef3f899bf4ae',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0158-5-s12',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.5',
                  'segment_index': 12}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.5',
             'start': 1232,
             'end': 1237,
             'original_text': '682H.',
             'corrected_text': ' ',
             'original_row_sha256': '7022a36c95c84a3beef76555a1b94e65de46de14891e6e62907f49beba97c582'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.5',
                     'start': 1232,
                     'end': 1237,
                     'original_text': '682H.',
                     'original_row_sha256': '7022a36c95c84a3beef76555a1b94e65de46de14891e6e62907f49beba97c582'}],
  'disposition': 'exclude-marginal-reference',
  'text_role': 'marginal-reference',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'The enlarged source shows 682H. in the left margin between body lines ending '
              'ἀθυμήσαντα and beginning δὲ καὶ ταπεινωθέντα. OCR fused it into ἀθυμήσαντα682H.δὲ. '
              'Replace only the exact 682H. preimage with one word-boundary space, so removal of '
              'the reference cannot concatenate the verified neighboring Greek words. Henry '
              'confirms their continuous sentence.',
  'qualification': 'The prior688H and current682H digit readings remain alternatives. Both '
                   'designate a marginal edition reference, not an Ancient Greek lexical form.',
  'scan': [{'physical_page': 158,
            'printed_page': 423,
            'region': [0.02, 0.57, 0.43, 0.65],
            'max_side': 3600,
            'image_sha256': 'fd47684eab03bd7c048da0516a058b05022a76220e175808b011fc83a007caea',
            'observed_text': 'ἀθυμήσαντα / 682H. δὲ καὶ ταπεινωθέντα',
            'qualification': 'The H-suffixed number is at the left margin beside the next printed '
                             'body line.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (11021, 11024),
  'context_sha256': '276ccbf7d3cf17b22b515909ef46159a25f8b4ffaebd46505bd00ae75dcd1dfe',
  'prior_identity_sha256': '8b0c8ef4742168f381f0b8d5dbbf50daf6dae80e3538d897c9d58b78cf20a204',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0158-8-s2',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.8', 'segment_index': 2}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.8',
             'start': 648,
             'end': 656,
             'original_text': 'προηρηθῶ',
             'corrected_text': 'προῃρῆσθαι',
             'original_row_sha256': 'af3ddb674d78031b70772209dfcd5399b506d593adc18c0686f54d97a57eff56'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0158.8',
                     'start': 648,
                     'end': 656,
                     'original_text': 'προηρηθῶ',
                     'original_row_sha256': 'af3ddb674d78031b70772209dfcd5399b506d593adc18c0686f54d97a57eff56'}],
  'disposition': 'editorial-word-choice',
  'text_role': 'authorial-body',
  'lexical_eligible': True,
  'glyph_resolved': False,
  'evidence': 'Both passages oppose the orderly life to pleasure and immediately describe the '
              'resulting proof of temperance. Henry uniquely has προῃρῆσθαι before τοῦ πρὸς '
              'ἡδονήν; Bekker’s corresponding damaged term follows the phrase πρὸς ἡδονήν. '
              'Explicitly prefer that corresponding complete Henry term while retaining Bekker’s '
              'surrounding order. The source token was not adopted by either previous editorial '
              'layer.',
  'qualification': 'This is term-level editorial corroboration, not a claim to settle the compact '
                   'Bekker sigma-theta glyph or to import Henry’s clause order.',
  'scan': [{'physical_page': 158,
            'printed_page': 423,
            'region': [0.43, 0.48, 0.825, 0.56],
            'max_side': 3600,
            'image_sha256': 'ed506032be8ce0d477d7499bce9b68047282b4882ca9ffa0ccd8419903f5d258',
            'observed_text': 'προῃρῆ[σθ/θ]αι',
            'qualification': 'The compact source group remains qualified independently; Henry '
                             'supplies the selected complete infinitive.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (11040, 11045),
  'context_sha256': 'cc97dcf437f127be2fb109e1a7753cb391520a8ebe2c3d71e4d023977a157ad3',
  'prior_identity_sha256': 'f8346aaca4e35de25e1f3e7523d72ea5e9d5379d305b998fd71023344623e16d',
  'word_selection': 'προῃρῆσθαι',
  'word_indices': [266995],
  'word_surface': {'surface': 'προῃρῆσθαι',
                   'separators': [],
                   'boundary_suffix': {'pieces': [], 'rendered': ''}},
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0172-7-s3',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.7', 'segment_index': 3}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.7',
             'start': 202,
             'end': 213,
             'original_text': '[ἀνα]χῶντον',
             'corrected_text': 'ἀναίσχυντον',
             'original_row_sha256': 'c0006f712e6bb8a6fdef64931a2ccced12bbce9221033fecb688331ef5750667'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0172.7',
                     'start': 201,
                     'end': 232,
                     'original_text': '[[ἀνα]χῶντον πάνυ τοῦτόν φασιν]',
                     'original_row_sha256': 'c0006f712e6bb8a6fdef64931a2ccced12bbce9221033fecb688331ef5750667'}],
  'disposition': 'correct-scan-reading',
  'text_role': 'printed-bracketed-reading',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'The body prints [ἀναίσχυντον πάνυ τοῦτόν φασιν] before Θρασύμαχον. The apparatus b4 '
              'separately gives the ἀναισχ. lemma and reports omission in A, corroborating the '
              'compact body stem without relying on grammar. Replace only the malformed inner OCR '
              '[ἀνα]χῶντον by ἀναίσχυντον; the existing outer bracket pair and following words '
              'remain. Review and exclude the complete printed bracketed insertion as a unit. '
              'Henry proceeds directly from μιμῇ to Θρασύμαχον.',
  'qualification': 'The apparatus establishes a textual omission variant but does not '
                   'independently date or assign authorship to the bracketed insertion. Preserve '
                   'that uncertainty and keep the entire bracketed reading outside lexical '
                   'admission.',
  'scan': [{'physical_page': 172,
            'printed_page': 437,
            'region': [0.43, 0.135, 0.825, 0.21],
            'max_side': 3600,
            'image_sha256': 'd2699cfbdd680a08d85f41ac3e24db91e81609f196e4c02e589cd100fe1a1659',
            'observed_text': 'μιμῇ [ἀναίσχυντον πάνυ τοῦτόν φασιν] Θρασύμαχον',
            'qualification': 'One printed outer bracket pair encloses the insertion; the OCR '
                             'created an extra internal bracket pair.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
           {'physical_page': 172,
            'printed_page': 437,
            'region': [0.07, 0.685, 0.83, 0.77],
            'max_side': 3600,
            'image_sha256': 'f6f70a5cabb3e481552627ec866fc664189ed1f71cad338ef0532b3c4df7b3ba',
            'observed_text': 'b.4. ἀναισχ. κ. τ. φασιν om A.',
            'qualification': 'The apparatus separately prints the abbreviated stem ἀναισχ. and '
                             'records omission in witness A.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (11610, 11614),
  'context_sha256': 'a29329b4e4e161930bc563e8d8bca5fbf628ed87f1fabe9567010c8523ff6526',
  'prior_identity_sha256': 'e7901432562e93129b2ad5bf678609a6e1ade0d9e69f41726543f102ed263635',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0179-2-s0',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0179.2', 'segment_index': 0}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0179.2',
             'start': 0,
             'end': 8,
             'original_text': 'Ἀρξίλαος',
             'corrected_text': '',
             'original_row_sha256': '1c3309271295668532bed057ef9efafb13c80c743a2ec2c6d6fde612b3c67e71'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0179.2',
                     'start': 0,
                     'end': 8,
                     'original_text': 'Ἀρξίλαος',
                     'original_row_sha256': '1c3309271295668532bed057ef9efafb13c80c743a2ec2c6d6fde612b3c67e71'}],
  'disposition': 'spurious-ocr-insertion',
  'text_role': 'ocr-insertion',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'The retained rows before and after this isolated row are positively anchored to the '
              'same printed sentence: the left column ends εἰς τὸν Ἀχέ- and the right column '
              'begins ροντα καὶ τὸν Ἅιδου τόπον. No separate name intervenes inside this '
              'continuous printed word. The isolated Ἀρξίλαος row is therefore a spurious OCR '
              'insertion at this established source boundary. Remove its text while preserving the '
              'empty row identity and alias; do not turn it into another Greek name or a lexical '
              'gap.',
  'qualification': 'This identifies an insertion in the ordered retained body stream; it does not '
                   'identify a source reading for the invented name or infer deletion solely from '
                   'Henry’s absence.',
  'scan': [{'physical_page': 179,
            'printed_page': 444,
            'region': [0.21, 0.63, 0.58, 0.71],
            'max_side': 3600,
            'image_sha256': 'be346d78825a9dcb0fa9c44162657e70d999ecbc387590ff81f1aa400fd61d87',
            'observed_text': 'εἰς τὸν Ἀχέ-',
            'qualification': 'The left printed column ends inside Ἀχέροντα.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
           {'physical_page': 179,
            'printed_page': 444,
            'region': [0.57, 0.105, 0.965, 0.17],
            'max_side': 3600,
            'image_sha256': '3290daba3cb3fc4e82154a40631423406b777bf884b0b4355b51661b9720872f',
            'observed_text': 'ροντα καὶ τὸν Ἅιδου τόπον.',
            'qualification': 'The right printed column begins with the immediate continuation of '
                             'that same body word.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (11801, 11804),
  'context_sha256': 'd8776ef0f0dce04fdf45a231aa1563f1f07ca128ea286e33c4d004b18f9b43ca',
  'prior_identity_sha256': '45b21728e845b2041d641d21bd460efdd2e7737a519e16e8bc54503c856bf6bd',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0184-1-s4',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.1', 'segment_index': 4}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.1',
             'start': 52,
             'end': 55,
             'original_text': '134',
             'corrected_text': '',
             'original_row_sha256': '4d841760a0df5968841b4eb26a5d2d18ef010fcb90ebfad458643e8da22954a5'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0184.1',
                     'start': 52,
                     'end': 55,
                     'original_text': '134',
                     'original_row_sha256': '4d841760a0df5968841b4eb26a5d2d18ef010fcb90ebfad458643e8da22954a5'}],
  'disposition': 'exclude-marginal-reference',
  'text_role': 'marginal-reference',
  'lexical_eligible': False,
  'glyph_resolved': True,
  'evidence': 'The body ends the first printed line with Μή- and continues δων καὶ Περσῶν on the '
              'next. The separate marginal1344R. is aligned with the following lines; the '
              'retained134 is only the OCR-captured prefix of that reference. Remove exactly134 '
              'while preserving the existing Μή- body fragment and its independent boundary '
              'exclusion. Henry confirms the body word Μήδων without a numeric token.',
  'qualification': 'Reference digits and the R suffix are modern edition apparatus, not a '
                   'completion of Μήδων. Do not manufacture a whole Greek word in this retained '
                   'fragment row.',
  'scan': [{'physical_page': 184,
            'printed_page': 449,
            'region': [0.02, 0.105, 0.43, 0.19],
            'max_side': 3600,
            'image_sha256': '46ed4390ee6379fb6fc6ca0ed982b1e04096740fc616b41d48c6104bee43d0d4',
            'observed_text': 'Μή- / δων καὶ Περσῶν / 1344R.',
            'qualification': 'The R-suffixed edition reference stands in the left margin below the '
                             'broken Μή-/δων body word.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (11911, 11914),
  'context_sha256': '7338f4bf2f786ddcff6f2243fdd77a746430b9383de71e15e1690d2677734c71',
  'prior_identity_sha256': '7395f32bfdef5fbbb9b1c9fa62598ed6534d5d34496502eedec3f7fcfbfc1046',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None},
 {'id': 'photius-final-source-0274-3-s23',
  'identities': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0274.3',
                  'segment_index': 23}],
  'edits': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0274.3',
             'start': 1714,
             'end': 1720,
             'original_text': 'λούσας',
             'corrected_text': 'λούσασθαι',
             'original_row_sha256': 'c9b893fadb1a2f12892cc3460766215dc1f807a627232072f5502c88dff18010'}],
  'review_ranges': [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0274.3',
                     'start': 1714,
                     'end': 1720,
                     'original_text': 'λούσας',
                     'original_row_sha256': 'c9b893fadb1a2f12892cc3460766215dc1f807a627232072f5502c88dff18010'}],
  'disposition': 'correct-scan-reading',
  'text_role': 'authorial-body',
  'lexical_eligible': True,
  'glyph_resolved': True,
  'evidence': 'Bekker prints λούσασθαι between χρείαν and ἀλλ’ ἢ in the quotation. The apparatus '
              'b34 explicitly states λούσασθαι addB, providing a separate legible lemma and '
              'identifying a transmitted manuscript variant. Restore the complete source '
              'infinitive from the retained λούσας. Henry omits the word; preserve that genuine '
              'edition difference rather than erase the Bekker/B reading.',
  'qualification': 'The addition is explicitly attributed to manuscript B by Bekker’s apparatus; '
                   'this is a transmitted textual variant, not an assumed modern editorial '
                   'invention and not a Henry-based scan certification.',
  'scan': [{'physical_page': 274,
            'printed_page': 539,
            'region': [0.43, 0.555, 0.825, 0.63],
            'max_side': 3600,
            'image_sha256': 'df3b5d2cba00cad7b6de2f1c31009abe1d6ce1d051054556a3c472e0aa20096b',
            'observed_text': 'οὐκ ἔχει χρείαν λούσασθαι ἀλλ’ ἢ τοὺς πόδας νίψασθαι',
            'qualification': 'The source prints the complete bathing infinitive in the quotation.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}},
           {'physical_page': 274,
            'printed_page': 539,
            'region': [0.4, 0.72, 0.83, 0.78],
            'max_side': 3600,
            'image_sha256': '34e535069249c3c0bba71dfbe915e7686a7554be3e303172a0b6bc0fc57899b4',
            'observed_text': 'b.34. λούσασθαι add B.',
            'qualification': 'The apparatus explicitly records the same word as an addition in '
                             'manuscript B.',
            'source': {'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                       'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'}}],
  'context': (14314, 14317),
  'context_sha256': 'ec11da6d9c8a21ca1e0d08f879aa3ac934fbe292bc71c1ad9ee20a5cca1ccfa4',
  'prior_identity_sha256': 'fd3f2cb1ec36dad6fe853f90bdc8ad912036525a35b86d3d2f363ee89da99172',
  'word_selection': None,
  'word_indices': [],
  'word_surface': None,
  'omission_boundaries': None,
  'residual_uncertainty': None}]



def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _record(spec, units, *, reviewed_at=REVIEWED_AT):
    if not isinstance(reviewed_at, str):
        raise ValueError('A final source observation needs a UTC review timestamp')
    try:
        moment = datetime.fromisoformat(reviewed_at.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('A final source observation needs a UTC review timestamp') from exc
    if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
        raise ValueError('A final source observation needs a UTC review timestamp')
    first, stop = spec['context']
    if (not isinstance(units, list) or _digest(units) != spec['context_sha256']
            or [unit.get('unit_index') for unit in units] != list(range(first, stop))):
        raise ValueError('The final source context lost its exact decoded unit witnesses')
    readings = []
    if spec['word_selection'] is not None:
        tokens = edition.tokenize(units)
        selected = [token for token in tokens
                    if token['key'] == edition.normalize(spec['word_selection'])]
        if len(selected) != 1 or len(spec['word_indices']) != 1:
            raise ValueError('The reviewed term is not uniquely located in its pinned source clause')
        token = selected[0]
        chosen = {'source_id': SOURCE_ID, 'role': 'chosen', 'text': token['text'],
            'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs']),
                        'source_index': spec['word_indices'][0]}],
            'refs': deepcopy(token['refs']), **deepcopy(spec['word_surface']),
            'qualification': 'Term-level editorial choice preserving the retained Bekker clause order.'}
        readings = [chosen]
    result = {key: deepcopy(spec[key]) for key in (
        'id', 'identities', 'edits', 'review_ranges', 'disposition', 'text_role',
        'lexical_eligible', 'glyph_resolved', 'evidence', 'qualification', 'scan',
        'residual_uncertainty')}
    result.update(reviewed_at=reviewed_at,
        prior_identity={'path': PRIOR, 'record_sha256': spec['prior_identity_sha256'],
                        **deepcopy(spec['identities'][0])},
        source_context={'source_id': SOURCE_ID, 'sha256': SOURCE_SHA256,
            'units_sha256': spec['context_sha256'], 'units': deepcopy(units),
            'qualification': 'Supplied Henry edition: exact context is comparison evidence, not a claim of Bekker agreement.'},
        contrary_readings=[{'source_id': SOURCE_ID, 'role': 'comparison',
            'text': ''.join(unit['text'] for unit in units),
            'qualification': spec['qualification']}], readings=readings)
    if readings:
        result['word_source'] = deepcopy(readings[0])
    if spec['omission_boundaries'] is not None:
        result['omission_source'] = {'source_id': SOURCE_ID, 'sha256': SOURCE_SHA256,
            'boundaries': deepcopy(spec['omission_boundaries']), 'intervening_tokens': [],
            'qualification': 'Explicit editorial omission at consecutive uniquely located Henry boundary tokens; the unresolved Bekker reading remains archived.'}
    return result


def validate_record(record):
    if not isinstance(record, dict):
        raise ValueError('A final source observation must be a complete record')
    matches = [spec for spec in SPECS if spec['id'] == record.get('id')]
    if len(matches) != 1 or not isinstance(record.get('source_context'), dict):
        raise ValueError('Unknown final source observation identity or source context')
    expected = _record(matches[0], record['source_context'].get('units'),
                       reviewed_at=record.get('reviewed_at'))
    if record != expected:
        raise ValueError('The final source observation differs from its authored authority')
    return deepcopy(expected)


def review_final(html_raw, rows, document, crop_png, *, reviewed_at=REVIEWED_AT):
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied final-review comparison source changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    import prepare_photius_editorial_continuation as preparer
    import repair_photius_editorial_substitutions as previous
    source_units = preparer.source_document(html_raw)
    source = {'id': SOURCE_ID, 'edition': 'René Henry, Photius. Bibliothèque, volumes 1–8 (1959–1977)',
              'citation': 'Thesaurus Linguae Graecae, Photius, Bibliotheca, 4040.001; Henry edition',
              'sha256': SOURCE_SHA256}
    known = previous._source_tokens(html_raw, source)
    result = []
    for spec in SPECS:
        for edit in spec['edits'] + spec['review_ranges']:
            row = rows.get(edit['locus'])
            if (not row or _digest(row) != edit['original_row_sha256']
                    or row['text'][edit['start']:edit['end']] != edit['original_text']):
                raise ValueError('A final observation lost its exact current row preimage')
        for scan in spec['scan']:
            raw = crop_png(document, scan['physical_page'], scan['region'])
            if hashlib.sha256(raw).hexdigest() != scan['image_sha256']:
                raise ValueError('The directly reviewed source crop changed')
        first, stop = spec['context']
        record = _record(spec, parser.units[first:stop], reviewed_at=reviewed_at)
        for reading in record['readings']:
            for token in reading['tokens']:
                index, actual = known[_digest(token['refs'])]
                if index != token['source_index'] or actual['text'] != token['text']:
                    raise ValueError('A chosen final source term changed its complete-edition identity')
            observed = preparer.attributed_span(reading, source_units)
            if any(reading[key] != observed[key]
                   for key in ('surface', 'separators', 'boundary_suffix')):
                raise ValueError('The final chosen source term changed its attributed surface')
        if record.get('omission_source'):
            boundaries = record['omission_source']['boundaries']
            for token in boundaries:
                index, actual = known[_digest(token['refs'])]
                if index != token['source_index'] or actual['text'] != token['text']:
                    raise ValueError('The final omission lost its exact source boundary')
            if boundaries[1]['source_index'] != boundaries[0]['source_index'] + 1:
                raise ValueError('The final omission is not an empty source interval')
        result.append(record)
    return result
