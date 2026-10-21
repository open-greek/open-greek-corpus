"""Occurrence-level source reviews for the two mismapped digital pages.

The primary authority is the printed Bekker scan. Hoeschel is a separately
typeset earlier edition; its differences remain attributed edition variants.
These observations do not infer printed readings from linguistic preference.
"""
from copy import deepcopy

REVIEWED_AT = '2026-10-21T18:23:00Z'
ARCHIVE = 'data/corpus_changes/photius-bekker-uncertainties'
SOURCES = {
    f'hoeschel1601-{page}': {
        'path': f'{ARCHIVE}/sources/hoeschel1601-page{page}.jpg',
        'sha256': digest, 'kind': 'image',
        'url': f'https://www.e-rara.ch/i3f/v20/{identifier}/full/full/0/default.jpg',
        'license': {'id': 'PDM-1.0',
                    'url': 'https://creativecommons.org/publicdomain/mark/1.0/'},
        'edition': 'hoeschel1601', 'printed_page': page,
        'catalog_url': 'https://www.e-rara.ch/zut/content/titleinfo/13222527',
        'persistent_identifier': 'https://doi.org/10.3931/e-rara-47637',
        'editor': 'David Hoeschel', 'year': 1601,
        'holding': 'ETH-Bibliothek Zürich, Rar 9426',
        'dimensions': dimensions,
    }
    for page, identifier, digest, dimensions in (
        (704, 13223228, '8621075e1bbedc4c9657dd19497a16a57d7d4dd4084b5ee6a92ed174082945ff', [2456, 4092]),
        (705, 13223229, '49ad50616721425bb00bdd22c984cb3c3e39a4a606d4314386aa0fa40caa5109', [2453, 4096]),
        (706, 13223230, '01b2e15bf4087db44ed4671f22868c84c12d0cb7ae468d48772f06ba500ae003', [2456, 4092]),
        (707, 13223231, '5fc3175a758072dac1b61222f71fd9a90f0c3f8522c1b04f778b23a33a12ef47', [2453, 4096]),
    )
}

EXPECTED_SCOPE = [
    (f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{row}', segment)
    for page, row, segments in (
        (169, 1, (1, 3, 5, 9, 11, 13, 15, 17, 19, 21)),
        (169, 3, (1, 3, 5)),
        (170, 1, (1,)), (170, 7, (1,)), (170, 8, (0,)),
        (170, 9, (1,)), (170, 10, (1,)), (170, 24, (1,)),
        (170, 25, (0,)), (170, 41, (1,)), (170, 42, (2,)),
        (170, 44, (2, 4)), (170, 45, (2,)), (170, 47, (2, 4)),
        (170, 48, (2, 4)), (170, 49, (2,)), (170, 50, (2, 4, 6)),
    ) for segment in segments
]

_SPECS = ({'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 1,
  'original_text': 'σέ-ρει·ῆς',
  'decision': 'resolved',
  'corrected_text': 'στέρεσθαι',
  'evidence': 'Bekker prints στέ- at the line end and ρεσθαι at the next line start after '
              'ἠναγκάζετο. Direct glyph inspection and the earlier typesetting support στέρεσθαι; '
              'the earlier στερεῖσθαι hypothesis is rejected.',
  'bekker_region': [0.2, 0.105, 0.6, 0.38],
  'comparisons': [{'source_id': 'hoeschel1601-704',
                   'printed_page': 704,
                   'region': [0.08, 0.5, 0.95, 0.82],
                   'text': 'στέρεσθαι',
                   'role': 'corroborating',
                   'qualification': 'Expand printed στ and σθ ligatures. Accent/ending differ from '
                                    'the old possible-scan στερεῖσθαι; compare source word after '
                                    'ἠναγκάζετο.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 3,
  'original_text': '“συμφερόν ἦσται·',
  'decision': 'resolved',
  'corrected_text': 'ἡττηθέντες ἐτραχύνθησαν',
  'evidence': 'The two printed words after τῶν συμφορῶν are ἡττηθέντες ἐτραχύνθησαν. Both are '
              'independently legible in the earlier typesetting; the retained OCR phrase does not '
              'represent these glyphs.',
  'bekker_region': [0.2, 0.105, 0.6, 0.38],
  'comparisons': [{'source_id': 'hoeschel1601-704',
                   'printed_page': 704,
                   'region': [0.08, 0.5, 0.95, 0.82],
                   'text': 'ἡττηθέντες ἐτραχύνθησαν',
                   'role': 'corroborating',
                   'qualification': 'Both words are visible in the same context after τῶν συμφορῶν '
                                    'and before πρὸς αὐτόν; punctuation differs.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 5,
  'original_text': 'ἀναμνήσθητι',
  'decision': 'resolved',
  'corrected_text': 'ἀναμνήσθητι',
  'evidence': 'Bekker clearly prints ἀναμνήσθητι between ἐνταῦθα and τοῦ τῶν ἡνιόχων. The earlier '
              'typesetting confirms the sigma/theta expansion; the display spelling is unchanged.',
  'bekker_region': [0.2, 0.105, 0.6, 0.38],
  'comparisons': [{'source_id': 'hoeschel1601-704',
                   'printed_page': 704,
                   'region': [0.08, 0.5, 0.95, 0.82],
                   'text': 'ἀναμνήσθητι',
                   'role': 'corroborating',
                   'qualification': 'The word occurs between ἐνταῦθα and τοῦ τῶν ἡνιόχων; σθ is a '
                                    'typographic ligature.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 9,
  'original_text': 'ἤχθησαν',
  'decision': 'resolved',
  'corrected_text': 'ἤχθησαν',
  'evidence': 'Bekker prints ἤχθησαν before ὑπ’ αὐτῷ τὸν ἄνω χρόνον. The same occurrence is '
              'legible in Hoeschel; no display correction is needed.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'ἤχθησαν',
                   'role': 'corroborating',
                   'qualification': 'First body line, before ὑπ’ αὐτῷ τὸν ἄνω χρόνον; word '
                                    'continues the preceding page paragraph, not a new passage.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 11,
  'original_text': 'ἐπεκώ-τησαν',
  'decision': 'resolved',
  'corrected_text': 'ἐπεσκότησεν',
  'evidence': 'The printed word after τοῖς ἔμπροσθεν is ἐπεσκότησεν, split ἐπεσκό-/τησεν. The '
              'omicron and singular ending are visible in both editions; the old ἐπεσκώτησαν '
              'candidate is not accepted.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'ἐπεσκότησεν',
                   'role': 'corroborating',
                   'qualification': 'Main reading after τοῖς ἔμπροσθεν has ο and singular ending; '
                                    'do not copy the old possible-scan ἐπεσκώτησαν.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 13,
  'original_text': 'τιμᾶσθαι',
  'decision': 'resolved',
  'corrected_text': 'τιμᾶσθαι',
  'evidence': 'Direct inspection reads τιμᾶσθαι after ἀλλὰ τὸ. The earlier edition supports the '
              'same word; resolve this uncertainty without changing the display.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'τιμᾶσθαι',
                   'role': 'corroborating',
                   'qualification': 'Printed split τιμᾶ-/σθαι is expanded only as a comparison '
                                    'whole word; no corpus join is proposed.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 15,
  'original_text': 'ἢ γὰρ τὸ μέσον κειμέν ᾗσιν',
  'decision': 'resolved',
  'corrected_text': 'οὐ γὰρ τὸ μέσον κύριόν ἐστιν',
  'evidence': 'Bekker prints οὐ γὰρ τὸ μέσον κύριόν ἐστιν before ἑκατέρων τῶν καιρῶν. The κ-υ-ρ '
              'group and ending are visible, and Hoeschel independently has κύριόν. The old κεῖνό '
              'candidate is not the source reading.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'οὐ γὰρ τὸ μέσον κύριόν ἐστιν',
                   'role': 'corroborating',
                   'qualification': 'Main text has κύριόν; preserve the adjacent marginal '
                                    'alternative separately if used, never treat the old κεῖνό '
                                    'hypothesis as established.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 17,
  'original_text': 'ἔσχον',
  'decision': 'resolved',
  'corrected_text': 'ἔστησαν',
  'evidence': 'The word between κατέγνωσαν and ἀλλὰ προσεῖχον is ἔστησαν. Bekker’s στ ligature and '
              'following ησαν agree with the earlier typesetting; ἔσχον is rejected.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'ἔστησαν',
                   'role': 'corroborating',
                   'qualification': 'Between κατέγνωσαν and ἀλλὰ προσεῖχον; printed στ is a '
                                    'conventional ligature. Does not corroborate old ἔσχον.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 19,
  'original_text': 'οἷδ’ ἡ χρή',
  'decision': 'resolved',
  'corrected_text': 'οἴεσθαι χρὴ',
  'evidence': 'Bekker prints οἴεσθαι χρὴ after τοὺς λαχόντας ἅπαντας. The earlier edition supports '
              'these words with different surrounding word order. Its complete sentence is not '
              'substituted.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'οἴεσθαι χρὴ',
                   'role': 'corroborating',
                   'qualification': 'The surrounding main text places πάντας after χρὴ; '
                                    'context/word order differ from the old retained reading and '
                                    'must remain explicit.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.1',
  'segment_index': 21,
  'original_text': 'ἀνέκτον',
  'decision': 'resolved',
  'corrected_text': 'οὐδέτερον',
  'evidence': 'Bekker prints οὐδέτερον between ἐγὼ μὲν γὰρ and ἂν φαίην. Hoeschel independently '
              'supports the same reading; neither ἀνέκτον nor the old ἀδεκτότερον candidate '
              'represents the printed word.',
  'bekker_region': [0.2, 0.265, 0.6, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.1, 0.95, 0.53],
                   'text': 'οὐδέτερον',
                   'role': 'corroborating',
                   'qualification': 'Between ἐγὼ μὲν γὰρ and ἂν φαίην; this is not the old '
                                    'possible ἀδεκτότερον.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.3',
  'segment_index': 1,
  'original_text': 'νομίζειν',
  'decision': 'resolved',
  'corrected_text': 'νομίζεσθαι',
  'evidence': 'Direct inspection reads νομίζεσθαι after φαῦλον. Hoeschel has the same occurrence '
              'and ending; retain the conventional sigma/theta expansion.',
  'bekker_region': [0.56, 0.105, 0.97, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.48, 0.95, 0.85],
                   'text': 'νομίζεσθαι',
                   'role': 'corroborating',
                   'qualification': 'In the phrase Περικλέα ἀξιοῦν φαῦλον νομίζεσθαι; whole '
                                    'contextual phrase establishes the occurrence.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.3',
  'segment_index': 3,
  'original_text': 'ἀλλ’ οὐχ ἃ μετ’',
  'decision': 'resolved',
  'corrected_text': 'ἀλλ’ ὑφ’ οἷς μεθ’',
  'evidence': 'Bekker prints ἀλλ’ ὑφ’ οἷς μεθ’ after μεθέξειν μέλλοντας. The letters and elision '
              'marks are visible. Hoeschel instead prints ἀλλ’ οὐχ ὃ μηδ’; preserve it as an '
              'edition variant rather than forcing agreement.',
  'bekker_region': [0.56, 0.105, 0.97, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-705',
                   'printed_page': 705,
                   'region': [0.08, 0.48, 0.95, 0.85],
                   'text': 'ἀλλ’ οὐχ ὃ μηδ’',
                   'role': 'edition-variant',
                   'qualification': 'The line after μεθέξειν μέλλοντας prints this phrase before '
                                    'ἐκείνοις καλῶς; it differs from both literal old '
                                    'alternatives. Elision marks retained.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0169.3',
  'segment_index': 5,
  'original_text': 'αἰτιάσετ)',
  'decision': 'retained-uncertain',
  'corrected_text': 'αἰτιάσετ)',
  'evidence': 'The compressed Bekker ending does not securely distinguish the finite αἰτιάσεται '
              'from the earlier αἰτιάσεσθαι hypothesis in this inspection. Hoeschel’s finite form '
              'is a different edition reading, not proof of Bekker’s glyph expansion. Preserve the '
              'original and exclusion.',
  'bekker_region': [0.56, 0.105, 0.97, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'αἰτιάσεται',
                   'role': 'edition-variant',
                   'qualification': 'In εἰ δ’ ἐπ’ ἀμφότερα Πλάτων … τοὺς ἄνδρας; the visible '
                                    'finite ending differs from the old infinitive hypothesis.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['αἰτιάσεται', 'αἰτιάσεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.1',
  'segment_index': 1,
  'original_text': 'ἀδικηθή-',
  'decision': 'retained-uncertain',
  'corrected_text': 'ἀδικηθή-',
  'evidence': 'The retained OCR hyphenated fragment and the whole source word require a separate '
              'boundary decision. The earlier image does not securely distinguish its initial '
              'vowel in this review. Keep the original display and all fragment/uncertainty '
              'causes.',
  'bekker_region': [0.025, 0.105, 0.49, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'ἠδικεῖσθαι',
                   'role': 'context',
                   'qualification': 'The whole word is visible after κατεψηφίσαντο and before τοῖς '
                                    'ἀνδράσι. I do not resolve the first-vowel/glyph expansion '
                                    'from this image; The whole source word spans retained row '
                                    'boundaries.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'},
                  {'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'ἀδικεῖσθαι',
                   'role': 'context',
                   'qualification': 'The whole word is visible after κατεψηφίσαντο and before τοῖς '
                                    'ἀνδράσι. I do not resolve the first-vowel/glyph expansion '
                                    'from this image; The whole source word spans retained row '
                                    'boundaries.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['ἀδικεῖσθαι', 'ἠδικεῖσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.7',
  'segment_index': 1,
  'original_text': 'νικη-',
  'decision': 'retained-uncertain',
  'corrected_text': 'νικη-',
  'evidence': 'The neighboring retained rows divide an uncertain word. Hoeschel has the whole '
              'counterpart κἀκείνων, which does not establish the exact Bekker division or '
              'authorize a join. Preserve this original fragment.',
  'bekker_region': [0.025, 0.105, 0.49, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'κἀκείνων',
                   'role': 'context',
                   'qualification': 'Same complete source word as ordinal16, after καὶ τοῦ δήμου '
                                    'and before ἢ σαφῶς. Do not count its two retained-row '
                                    'associations as independent readings or silently derive '
                                    'νικῶντων.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['νικῶ-', 'κἀκείνων']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.8',
  'segment_index': 0,
  'original_text': 'ντὸν',
  'decision': 'retained-uncertain',
  'corrected_text': 'ντὸν',
  'evidence': 'This is the continuation associated with the same whole-word Hoeschel counterpart '
              'as the preceding row. Do not treat the two fragments as independent readings or '
              'import a whole word into the suffix. Preserve both exclusions.',
  'bekker_region': [0.025, 0.105, 0.49, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'κἀκείνων',
                   'role': 'context',
                   'qualification': 'Shared complete-word counterpart with ordinal15, not an '
                                    'independently located ντων suffix. Keep the original two row '
                                    'spans and this mapping qualification.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['ντων', 'κἀκείνων']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.9',
  'segment_index': 1,
  'original_text': 'κατεγνώσθη',
  'decision': 'resolved',
  'corrected_text': 'κατεγνώσθη',
  'evidence': 'Bekker clearly prints κατεγνώσθη after ὀρθῶς ἐκεῖνα. The earlier typesetting '
              'supports the same reading; the display is unchanged.',
  'bekker_region': [0.025, 0.105, 0.49, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'κατεγνώσθη',
                   'role': 'corroborating',
                   'qualification': 'After εἰ μὲν γὰρ ὀρθῶς ἐκεῖνα and before ἠδίκουν; retains a '
                                    'conventional σθ expansion.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.10',
  'segment_index': 1,
  'original_text': 'νῦν',
  'decision': 'resolved',
  'corrected_text': 'δήπου',
  'evidence': 'After ὥστε οὐχὶ the next printed line starts δήπου ταῦτά γε. Bekker’s δήπου and the '
              'earlier edition agree; νῦν is an OCR substitution for this occurrence.',
  'bekker_region': [0.025, 0.105, 0.49, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.1, 0.95, 0.54],
                   'text': 'δήπου',
                   'role': 'corroborating',
                   'qualification': 'Between ὥστε οὐχὶ and ταῦτά γε; the alternate edition does '
                                    'not read νῦν at this occurrence.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.24',
  'segment_index': 1,
  'original_text': 'προσέσχεν',
  'decision': 'resolved',
  'corrected_text': 'προσήκειν',
  'evidence': 'Bekker prints προσήκειν between ἐκείνοις and εἰ ὅτι προσέπταισαν. The eta and κειν '
              'ending are visible. Hoeschel supports προσήκειν in its corresponding sentence; the '
              'old προσέχειν/προσέσχεν candidates are rejected.',
  'bekker_region': [0.025, 0.3, 0.49, 0.54],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.53, 0.95, 0.86],
                   'text': 'προσήκειν',
                   'role': 'corroborating',
                   'qualification': 'Main text ἐκείνους προσήκειν, εἰ ὅτι προσέπταισαν… differs '
                                    'from both literal possible-scan strings.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.25',
  'segment_index': 0,
  'original_text': 'μιζομένη',
  'decision': 'retained-uncertain',
  'corrected_text': 'μιζομένη',
  'evidence': 'The source has a printed continuation after χείρους νο-. Hoeschel’s whole '
              'νομίζεσθαι helps locate it but does not authorize joining retained rows or '
              'releasing a suffix as a lexical form. Preserve the original fragment.',
  'bekker_region': [0.025, 0.3, 0.49, 0.54],
  'comparisons': [{'source_id': 'hoeschel1601-706',
                   'printed_page': 706,
                   'region': [0.08, 0.53, 0.95, 0.86],
                   'text': 'νομίζεσθαι',
                   'role': 'context',
                   'qualification': 'Complete source word after χείρους. Old row25 is a '
                                    'continuation of row24 νο-; whole-word comparison is not '
                                    'authority to replace/count only μίζεσθαι as a whole word.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['μίζεσθαι', 'νομίζεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.41',
  'segment_index': 1,
  'original_text': 'ἀγωνίᾳ τε',
  'decision': 'resolved',
  'corrected_text': 'ἀγκῶνάς τε',
  'evidence': 'Bekker prints ἀγκῶνάς τε between ἀλλὰ καὶ and περιεδρύφθη. The gamma/kappa group '
              'and both accents are legible, corroborated by the earlier edition. Neighboring '
              'words are outside this decision.',
  'bekker_region': [0.39, 0.105, 0.81, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.1, 0.95, 0.45],
                   'text': 'ἀγκῶνάς τε',
                   'role': 'corroborating',
                   'qualification': 'Between ἀλλὰ καὶ and περιεδρύφθη. Other neighboring edition '
                                    'readings differ (including the following noun); no '
                                    'full-passage agreement is asserted.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.42',
  'segment_index': 2,
  'original_text': 'καὶ ὁ δέσποτες',
  'decision': 'resolved',
  'corrected_text': 'καὶ ὁ δάκτυλος',
  'evidence': 'The small-type Orontes sentence prints καὶ ὁ δάκτυλος before ἔφη. Hoeschel confirms '
              'δάκτυλος. This resolves its spelling only; the independent nonbody exclusion '
              'remains in force.',
  'bekker_region': [0.39, 0.105, 0.81, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.1, 0.95, 0.45],
                   'text': 'καὶ ὁ δάκτυλος',
                   'role': 'corroborating',
                   'qualification': 'Inside the bracketed Orontes saying, before ἔφη. This is not '
                                    'δέσποτος/δέσποτες; classification of Bekker small type '
                                    'remains a separate decision.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.44',
  'segment_index': 2,
  'original_text': 'ἡττήσεται',
  'decision': 'retained-uncertain',
  'corrected_text': 'ἡττήσεται',
  'evidence': 'The compressed Bekker ending remains unresolved between the retained finite form '
              'and the earlier infinitive hypothesis. Hoeschel’s finite ἡττήσεται is retained as '
              'an edition reading; it cannot settle the primary scan.',
  'bekker_region': [0.39, 0.105, 0.81, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.1, 0.95, 0.45],
                   'text': 'ἡττήσεται',
                   'role': 'edition-variant',
                   'qualification': 'In ἀλλ’ ἡττήσεται μὲν ὁ ἰσχυρὸς…; finite ending corroborates '
                                    'old form against the possible infinitive. Neighboring syntax '
                                    'differs.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['ἡττήσεται', 'ἡττήσεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.44',
  'segment_index': 4,
  'original_text': 'ἁλώσεται',
  'decision': 'retained-uncertain',
  'corrected_text': 'ἁλώσεται',
  'evidence': 'The compressed Bekker ending remains unresolved between the retained finite form '
              'and the earlier infinitive hypothesis. Hoeschel’s finite ἁλώσεται does not alone '
              'establish the Bekker expansion.',
  'bekker_region': [0.39, 0.105, 0.81, 0.34],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.1, 0.95, 0.45],
                   'text': 'ἁλώσεται',
                   'role': 'edition-variant',
                   'qualification': 'Before δὲ Βαβυλὼν αὐτοῖς τείχεσι; finite future, not the '
                                    'proposed infinitive.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['ἁλώσεται', 'ἁλώσεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.45',
  'segment_index': 2,
  'original_text': 'περιέρχεται',
  'decision': 'retained-uncertain',
  'corrected_text': 'περιέρχεται',
  'evidence': 'The Bekker ending remains unresolved between the retained finite form and the '
              'earlier infinitive hypothesis. Preserve περιέρχεται and its exclusion; the earlier '
              'edition’s finite form is separately attributed.',
  'bekker_region': [0.39, 0.3, 0.81, 0.54],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.1, 0.95, 0.45],
                   'text': 'περιέρχεται',
                   'role': 'edition-variant',
                   'qualification': 'After πάντα ταῦτα ἐναλλὰξ and before εἰ δὲ ἔσωζον; finite '
                                    'ending, not the proposed infinitive.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['περιέρχεται', 'περιέρχεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.47',
  'segment_index': 2,
  'original_text': 'δύναι·)',
  'decision': 'retained-uncertain',
  'corrected_text': 'δύναι·)',
  'evidence': 'The compressed final group in the Bekker word remains unresolved independently. The '
              'earlier comparison also retains competing expansions; neither grammar nor another '
              'edition supplies correction authority.',
  'bekker_region': [0.39, 0.3, 0.81, 0.54],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'δύνασθαι',
                   'role': 'context',
                   'qualification': 'Word after οὐκ ὀλίγου, before οἷς…; the compressed final '
                                    'group is not independently resolved in this read-only '
                                    'comparison. The comparison does not select between the two '
                                    'visible glyph expansions.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'},
                  {'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'δύνασαι',
                   'role': 'context',
                   'qualification': 'Word after οὐκ ὀλίγου, before οἷς…; the compressed final '
                                    'group is not independently resolved in this read-only '
                                    'comparison. The comparison does not select between the two '
                                    'visible glyph expansions.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['δύνασθαι', 'δύνασαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.47',
  'segment_index': 4,
  'original_text': 'γενήσεται',
  'decision': 'retained-uncertain',
  'corrected_text': 'γενήσεται',
  'evidence': 'The Bekker ending remains unresolved between the retained finite form and the '
              'earlier infinitive hypothesis. Hoeschel’s finite γενήσεται is preserved without '
              'selecting Bekker’s expansion.',
  'bekker_region': [0.39, 0.3, 0.81, 0.54],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'γενήσεται',
                   'role': 'edition-variant',
                   'qualification': 'After γέγονε καὶ and before ὧν ἐστὶ; finite future, not the '
                                    'possible infinitive.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['γενήσεται', 'γενήσεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.48',
  'segment_index': 2,
  'original_text': 'ἡττήσαντο',
  'decision': 'resolved',
  'corrected_text': 'ἠπίσταντο',
  'evidence': 'Bekker prints ἠπίσταντο before χρηστὸν οὐδέν. The initial eta and πιστ group are '
              'legible; Hoeschel supports the same word with different neighboring conjunctions. '
              'Those conjunctions are not changed here.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'ἠπίσταντο',
                   'role': 'corroborating',
                   'qualification': 'Between οὔτε and χρηστὸν οὐδέν; the preceding οὔτε and later '
                                    'οὔτε also differ from retained ὅτε contexts.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.48',
  'segment_index': 4,
  'original_text': 'δέξασθαι',
  'decision': 'resolved',
  'corrected_text': 'δέξασθαι',
  'evidence': 'Direct inspection reads δέξασθαι after ὅστις βούλεται. Hoeschel supports the same '
              'word and the display remains unchanged.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'δέξασθαι',
                   'role': 'corroborating',
                   'qualification': 'After ὅστις βούλεται and before τὸ ἐρώτημα; σθ expansion '
                                    'retained as a comparison reading.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.49',
  'segment_index': 2,
  'original_text': 'φαίνεται',
  'decision': 'retained-uncertain',
  'corrected_text': 'φαίνεται',
  'evidence': 'The compressed Bekker ending remains unresolved between the retained finite form '
              'and the earlier infinitive hypothesis. Preserve φαίνεται and its exclusion; the '
              'earlier edition is a separate reading.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'φαίνεται',
                   'role': 'edition-variant',
                   'qualification': 'In the Socrates question after λέγων ἐκείνῳ; finite ending, '
                                    'not the possible infinitive.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}],
  'alternatives': ['φαίνεται', 'φαίνεσθαι']},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.50',
  'segment_index': 2,
  'original_text': 'ἰσχυρίζεται',
  'decision': 'resolved',
  'corrected_text': 'ἰσχυρίζῃ',
  'evidence': 'Bekker’s last body line reads ἰσχυρίζῃ after συνεβούλευεν. The eta with iota '
              'subscript is visible, and the earlier typesetting agrees; it is not the retained '
              'ἰσχυρίζεται.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'ἰσχυρίζῃ',
                   'role': 'corroborating',
                   'qualification': 'After ὡς οὐ τὰ βέλτιστα συνεβούλευεν; the second-person '
                                    'ending differs from retained ἰσχυρίζεται. Do not normalize '
                                    'from grammar.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.50',
  'segment_index': 4,
  'original_text': 'οἱ',
  'decision': 'resolved',
  'corrected_text': 'εἰ',
  'evidence': 'The same printed line reads καὶ μὴν εἰ μὲν οὐδεὶς. Bekker’s epsilon-iota and the '
              'earlier edition agree; neither οἱ nor the old ᾧ hypothesis is adopted.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'εἰ',
                   'role': 'corroborating',
                   'qualification': 'In καὶ μὴν εἰ μὲν οὐδεὶς…; neither the possible relative ᾧ '
                                    'nor retained article οἱ is assumed.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0170.50',
  'segment_index': 6,
  'original_text': 'ἐπὴ',
  'decision': 'resolved',
  'corrected_text': 'ἐπῆν',
  'evidence': 'Bekker clearly prints ἐπῆν after οὐδεὶς on the last body line. The eta, circumflex, '
              'and terminal nu are visible; this decision is based on Bekker, while the earlier '
              'edition’s compressed terminal group remains unresolved.',
  'bekker_region': [0.39, 0.485, 0.81, 0.73],
  'comparisons': [{'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'ἐπῆν',
                   'role': 'context',
                   'qualification': 'The terminal word before κίνδυνος is located uniquely, but '
                                    'this review retains uncertainty about the eta/epsilon-iota '
                                    'typography and mark.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'},
                  {'source_id': 'hoeschel1601-707',
                   'printed_page': 707,
                   'region': [0.08, 0.42, 0.95, 0.84],
                   'text': 'ἐπεῖν',
                   'role': 'context',
                   'qualification': 'The terminal word before κίνδυνος is located uniquely, but '
                                    'this review retains uncertainty about the eta/epsilon-iota '
                                    'typography and mark.',
                   'region_kind': 'context band containing the whole occurrence and surrounding '
                                  'complete source lines'}]})


def records():
    return deepcopy(list(_SPECS))
