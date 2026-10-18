"""Completed source review for early Cary Greek panel geometry.

The constants identify source-image boundaries and their evidence. They do not
replace OCR readings. The generator reproduces all font proposals and applies
these reviewed exceptions before writing immutable retry requests.
"""

PROPOSALS_SHA256 = 'e86908258878e8886860d46e3b5e590545736f86ed56e357521d3912ac6ab7db'

OVERRIDES = {'dio-cary-v1-pdf0043-comparison': {'y1': 0.3125,
                                    'first_note_y0': 0.31988,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0050-fragment': {'y1': 0.6112,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0054-comparison': {'y1': 0.80545,
                                    'first_note_y0': 0.80419,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0055-fragment': {'y1': 0.1649,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0059-fragment': {'y1': 0.2476,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0060-comparison': {'y1': 0.8375,
                                    'first_note_y0': 0.84137,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0063-fragment': {'y1': 0.2097,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0064-fragment': {'y1': 0.1831,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0068-comparison': {'y1': 0.79364,
                                    'first_note_y0': 0.79123,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0073-fragment': {'y1': 0.1939,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0074-fragment': {'y1': 0.5137,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0078-comparison': {'y1': 0.94,
                                    'evidence': 'Full source contact review identifies all text through the '
                                                'original panel end as body or an attached transmission '
                                                'credit. The font proposal divided a continuing body '
                                                'paragraph, quotation or source credit; retain the original '
                                                'panel boundary.',
                                    'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0079-fragment': {'y1': 0.189,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0082-comparison': {'y1': 0.85659,
                                    'first_note_y0': 0.86084,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0084-comparison': {'y1': 0.80864,
                                    'first_note_y0': 0.80818,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0085-comparison': {'y1': 0.82182,
                                    'first_note_y0': 0.82448,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0086-fragment': {'y1': 0.5553,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0095-fragment': {'y1': 0.259,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0107-fragment': {'y1': 0.263,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0112-comparison': {'y1': 0.94,
                                    'evidence': 'Full source contact review identifies all text through the '
                                                'original panel end as body or an attached transmission '
                                                'credit. The font proposal divided a continuing body '
                                                'paragraph, quotation or source credit; retain the original '
                                                'panel boundary.',
                                    'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0129-comparison': {'y1': 0.80886,
                                    'first_note_y0': 0.81344,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0133-comparison': {'y1': 0.83477,
                                    'first_note_y0': 0.83961,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0137-fragment': {'y1': 0.79795,
                                  'first_note_y0': 0.80395,
                                  'evidence': 'Full source inspection identifies smaller editorial notes '
                                              'below the complete Greek body and attached transmission '
                                              'credit. The boundary lies in the verified blank gap before '
                                              'the first note; preserve all original predictions as held '
                                              'evidence.',
                                  'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0138-fragment': {'y1': 0.5408,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0141-comparison': {'y1': 0.94,
                                    'evidence': 'Full source contact review identifies all text through the '
                                                'original panel end as body or an attached transmission '
                                                'credit. The font proposal divided a continuing body '
                                                'paragraph, quotation or source credit; retain the original '
                                                'panel boundary.',
                                    'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0143-comparison': {'y1': 0.82795,
                                    'first_note_y0': 0.82818,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0148-comparison': {'y1': 0.82932,
                                    'first_note_y0': 0.83151,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0151-fragment': {'y1': 0.6387,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0152-comparison': {'y1': 0.80205,
                                    'first_note_y0': 0.80667,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0161-comparison': {'y1': 0.84295,
                                    'first_note_y0': 0.84484,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0168-fragment': {'y1': 0.234,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0172-comparison': {'y1': 0.69841,
                                    'first_note_y0': 0.70207,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0173-comparison': {'y1': 0.80682,
                                    'first_note_y0': 0.81047,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0174-fragment': {'y1': 0.67614,
                                  'first_note_y0': 0.68234,
                                  'evidence': 'Full source inspection identifies smaller editorial notes '
                                              'below the complete Greek body and attached transmission '
                                              'credit. The boundary lies in the verified blank gap before '
                                              'the first note; preserve all original predictions as held '
                                              'evidence.',
                                  'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0177-fragment': {'y1': 0.6553,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0199-fragment': {'y1': 0.6124,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0200-comparison': {'y1': 0.82159,
                                    'first_note_y0': 0.82611,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0200-fragment': {'y1': 0.7408,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0213-comparison': {'y1': 0.94,
                                    'evidence': 'Full source contact review identifies all text through the '
                                                'original panel end as body or an attached transmission '
                                                'credit. The font proposal divided a continuing body '
                                                'paragraph, quotation or source credit; retain the original '
                                                'panel boundary.',
                                    'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0216-fragment': {'y1': 0.1692,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0217-fragment': {'y1': 0.3498,
                                  'evidence': 'Full source contact review identifies all text through the '
                                              'original panel end as body or an attached transmission '
                                              'credit. The font proposal divided a continuing body '
                                              'paragraph, quotation or source credit; retain the original '
                                              'panel boundary.',
                                  'action': 'retain-original-panel-end'},
 'dio-cary-v1-pdf0220-comparison': {'y1': 0.85341,
                                    'first_note_y0': 0.86017,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0223-comparison': {'y1': 0.86068,
                                    'first_note_y0': 0.86309,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0227-comparison': {'y1': 0.86114,
                                    'first_note_y0': 0.86757,
                                    'evidence': 'Full source inspection identifies smaller editorial notes '
                                                'below the complete Greek body and attached transmission '
                                                'credit. The boundary lies in the verified blank gap before '
                                                'the first note; preserve all original predictions as held '
                                                'evidence.',
                                    'action': 'exclude-source-confirmed-editorial-notes'},
 'dio-cary-v1-pdf0230-comparison': {'y1': 0.94,
                                    'evidence': 'Full source contact review identifies all text through the '
                                                'original panel end as body or an attached transmission '
                                                'credit. The font proposal divided a continuing body '
                                                'paragraph, quotation or source credit; retain the original '
                                                'panel boundary.',
                                    'action': 'retain-original-panel-end'},
 'dio-cary-v2-pdf0009-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0019-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0021-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0023-fragment': {'y1': 0.586,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0025-fragment': {'y1': 0.5017,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0026-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0027-comparison': {'y1': 0.83818,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.83318, 0.84318],
                                    'source_note_anchor': 0.84173},
 'dio-cary-v2-pdf0030-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0037-comparison': {'y1': 0.8275,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.825, 0.83],
                                    'source_note_anchor': 0.82983},
 'dio-cary-v2-pdf0045-comparison': {'y1': 0.85227,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.845, 0.85955],
                                    'source_note_anchor': 0.85788},
 'dio-cary-v2-pdf0046-comparison': {'y1': 0.85091,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.84773, 0.85409],
                                    'source_note_anchor': 0.85247},
 'dio-cary-v2-pdf0046-fragment': {'y1': 0.2486,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0051-comparison': {'y1': 0.83,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.82545, 0.83455],
                                    'source_note_anchor': 0.83388},
 'dio-cary-v2-pdf0052-comparison': {'y1': 0.82318,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.81818, 0.82818],
                                    'source_note_anchor': 0.82917},
 'dio-cary-v2-pdf0061-comparison': {'y1': 0.80864,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.80364, 0.81364],
                                    'source_note_anchor': 0.81147},
 'dio-cary-v2-pdf0063-fragment': {'y1': 0.6782,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0065-fragment': {'y1': 0.5952,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0068-comparison': {'y1': 0.85636,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85091, 0.86182],
                                    'source_note_anchor': 0.85994},
 'dio-cary-v2-pdf0068-fragment': {'y1': 0.5439,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0072-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0075-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0077-comparison': {'y1': 0.90023,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.89545, 0.905],
                                    'source_note_anchor': 0.90291},
 'dio-cary-v2-pdf0078-comparison': {'y1': 0.85523,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85273, 0.85773],
                                    'source_note_anchor': 0.85787},
 'dio-cary-v2-pdf0086-comparison': {'y1': 0.84227,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.83818, 0.84636],
                                    'source_note_anchor': 0.84483},
 'dio-cary-v2-pdf0089-comparison': {'y1': 0.86273,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85955, 0.86591],
                                    'source_note_anchor': 0.86478},
 'dio-cary-v2-pdf0091-comparison': {'y1': 0.87341,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.87, 0.87682],
                                    'source_note_anchor': 0.87693},
 'dio-cary-v2-pdf0097-fragment': {'y1': 0.3469,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0098-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0099-comparison': {'y1': 0.85864,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85545, 0.86182],
                                    'source_note_anchor': 0.86044},
 'dio-cary-v2-pdf0104-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0104-fragment': {'y1': 0.1779,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0105-comparison': {'y1': 0.82523,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.82227, 0.82818],
                                    'source_note_anchor': 0.82732},
 'dio-cary-v2-pdf0106-comparison': {'y1': 0.85864,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.855, 0.86227],
                                    'source_note_anchor': 0.86158},
 'dio-cary-v2-pdf0107-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0110-comparison': {'y1': 0.85841,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85545, 0.86136],
                                    'source_note_anchor': 0.86085},
 'dio-cary-v2-pdf0111-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0115-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0117-fragment': {'y1': 0.4583,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0119-fragment': {'y1': 0.7286,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0120-comparison': {'y1': 0.87273,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.86955, 0.87591],
                                    'source_note_anchor': 0.87355},
 'dio-cary-v2-pdf0121-comparison': {'y1': 0.8445,
                                    'evidence': 'Detailed source inspection preserves the complete final '
                                                'primary word ἀνεῖχον, including its breathing/descender '
                                                'marks, above the smaller supplied-by-Gros note. The '
                                                'boundary is y=.8445.',
                                    'blank_gap': [0.8435, 0.8455],
                                    'source_note_anchor': 0.8412},
 'dio-cary-v2-pdf0123-fragment': {'y1': 0.2701,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0126-comparison': {'y1': 0.84227,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.83955, 0.845],
                                    'source_note_anchor': 0.84432},
 'dio-cary-v2-pdf0126-fragment': {'y1': 0.6439,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0127-fragment': {'y1': 0.594,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0128-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0130-fragment': {'y1': 0.2602,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0132-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0134-fragment': {'y1': 0.408,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0135-fragment': {'y1': 0.4322,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0139-fragment': {'y1': 0.1685,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0140-comparison': {'y1': 0.81591,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.805, 0.82682],
                                    'source_note_anchor': 0.82548},
 'dio-cary-v2-pdf0143-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0143-fragment': {'y1': 0.4904,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0145-comparison': {'y1': 0.84705,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.84455, 0.84955],
                                    'source_note_anchor': 0.84967},
 'dio-cary-v2-pdf0151-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0156-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0161-comparison': {'y1': 0.85841,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.855, 0.86182],
                                    'source_note_anchor': 0.8612},
 'dio-cary-v2-pdf0163-fragment': {'y1': 0.1568,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0164-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0165-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0167-comparison': {'y1': 0.83273,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.82955, 0.83591],
                                    'source_note_anchor': 0.83506},
 'dio-cary-v2-pdf0170-fragment': {'y1': 0.6166,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0171-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0174-comparison': {'y1': 0.84,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.83636, 0.84364],
                                    'source_note_anchor': 0.8434},
 'dio-cary-v2-pdf0180-comparison': {'y1': 0.81409,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.80955, 0.81864],
                                    'source_note_anchor': 0.81829},
 'dio-cary-v2-pdf0183-comparison': {'y1': 0.86477,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.85955, 0.87],
                                    'source_note_anchor': 0.86834},
 'dio-cary-v2-pdf0184-fragment': {'y1': 0.5477,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0185-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0187-comparison': {'y1': 0.79455,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.78682, 0.80227],
                                    'source_note_anchor': 0.80025},
 'dio-cary-v2-pdf0194-comparison': {'y1': 0.81568,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.81227, 0.81909],
                                    'source_note_anchor': 0.81943},
 'dio-cary-v2-pdf0195-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0196-fragment': {'y1': 0.1682,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0201-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0204-comparison': {'y1': 0.94,
                                    'evidence': 'Source pixels confirm that the font proposal divided a '
                                                'complete primary Greek paragraph, comparative quotation or '
                                                'attached transmission credit. Retain the entire original '
                                                'panel, including all numbered sections and source credits; '
                                                'no terminal apparatus is present.',
                                    'blank_gap': None,
                                    'source_note_anchor': None},
 'dio-cary-v2-pdf0206-comparison': {'y1': 0.82682,
                                    'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                                'numbered sections and attached transmission credits precede '
                                                'this blank-gap boundary. Exclude the complete smaller '
                                                'terminal editorial apparatus while retaining every original '
                                                'prediction in the reviewed input bundle.',
                                    'blank_gap': [0.82, 0.83364],
                                    'source_note_anchor': 0.83374},
 'dio-cary-v2-pdf0210-fragment': {'y1': 0.825,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.82, 0.83],
                                  'source_note_anchor': 0.82946},
 'dio-cary-v2-pdf0218-fragment': {'y1': 0.77886,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.775, 0.78273],
                                  'source_note_anchor': 0.78221},
 'dio-cary-v2-pdf0220-fragment': {'y1': 0.29886,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.29409, 0.30364],
                                  'source_note_anchor': 0.30266},
 'dio-cary-v2-pdf0225-fragment': {'y1': 0.79932,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.79227, 0.80636],
                                  'source_note_anchor': 0.80612},
 'dio-cary-v2-pdf0226-fragment': {'y1': 0.77886,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.77182, 0.78591],
                                  'source_note_anchor': 0.78435},
 'dio-cary-v2-pdf0228-fragment': {'y1': 0.79705,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.79227, 0.80182],
                                  'source_note_anchor': 0.80069},
 'dio-cary-v2-pdf0229-fragment': {'y1': 0.80841,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.80364, 0.81318],
                                  'source_note_anchor': 0.812},
 'dio-cary-v2-pdf0232-fragment': {'y1': 0.295,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.28955, 0.30045],
                                  'source_note_anchor': 0.29987},
 'dio-cary-v2-pdf0233-fragment': {'y1': 0.83068,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.82455, 0.83682],
                                  'source_note_anchor': 0.83537},
 'dio-cary-v2-pdf0234-fragment': {'y1': 0.77523,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.77182, 0.77864],
                                  'source_note_anchor': 0.77755},
 'dio-cary-v2-pdf0235-fragment': {'y1': 0.94,
                                  'evidence': 'Source pixels confirm that the font proposal divided a '
                                              'complete primary Greek paragraph, comparative quotation or '
                                              'attached transmission credit. Retain the entire original '
                                              'panel, including all numbered sections and source credits; no '
                                              'terminal apparatus is present.',
                                  'blank_gap': None,
                                  'source_note_anchor': None},
 'dio-cary-v2-pdf0238-fragment': {'y1': 0.35477,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.34955, 0.36],
                                  'source_note_anchor': 0.35914},
 'dio-cary-v2-pdf0241-fragment': {'y1': 0.79795,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.79045, 0.80545],
                                  'source_note_anchor': 0.80428},
 'dio-cary-v2-pdf0243-fragment': {'y1': 0.83909,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.835, 0.84318],
                                  'source_note_anchor': 0.84594},
 'dio-cary-v2-pdf0245-fragment': {'y1': 0.83045,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.82636, 0.83455],
                                  'source_note_anchor': 0.83344},
 'dio-cary-v2-pdf0253-fragment': {'y1': 0.80045,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.79545, 0.80545],
                                  'source_note_anchor': 0.80494},
 'dio-cary-v2-pdf0254-fragment': {'y1': 0.76727,
                                  'evidence': 'Source pixels confirm that all main Greek paragraphs, '
                                              'numbered sections and attached transmission credits precede '
                                              'this blank-gap boundary. Exclude the complete smaller '
                                              'terminal editorial apparatus while retaining every original '
                                              'prediction in the reviewed input bundle.',
                                  'blank_gap': [0.76364, 0.77091],
                                  'source_note_anchor': 0.7705}}

CONTACTS = {'dio-cary-v1-pdf0029-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0029-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0030-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0031-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0031-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0032-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0032-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0033-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0034-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0034-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0035-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0036-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0036-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0037-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0038-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0038-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0039-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0039-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0040-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0040-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0041-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0041-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0042-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0042-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0043-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0043-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0044-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0044-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0045-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0045-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0046-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0046-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0047-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0047-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0048-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0048-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0049-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0049-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0050-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0050-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0051-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0051-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0052-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0053-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0054-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0055-fragment': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0055-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0056-comparison': 'ac61aa06b45000227d82dcbefe329e699a90937c2c86481fd7253ddaf87dbfed',
 'dio-cary-v1-pdf0057-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0058-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0058-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0059-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0059-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0060-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0060-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0061-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0061-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0062-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0062-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0063-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0063-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0064-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0064-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0065-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0066-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0067-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0067-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0068-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0068-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0069-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0069-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0070-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0070-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0071-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0071-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0072-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0072-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0073-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0073-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0074-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0074-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0075-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0075-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0076-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0076-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0077-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0078-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0079-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0079-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0080-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0080-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0081-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0081-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0082-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0082-comparison': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0083-fragment': '7110bc2e5929f11c948ab4301f6da62e56b95157c34d834078dab47406f30569',
 'dio-cary-v1-pdf0083-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0084-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0084-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0085-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0085-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0086-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0086-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0087-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0087-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0088-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0088-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0089-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0089-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0090-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0090-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0091-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0092-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0092-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0093-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0093-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0094-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0095-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0095-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0096-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0096-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0097-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0097-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0098-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0098-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0099-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0099-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0100-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0100-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0101-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0101-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0102-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0102-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0103-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0103-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0104-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0104-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0105-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0105-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0106-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0106-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0107-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0107-comparison': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0108-fragment': '98fe29fdea1b2f38a83c57c102e2ed8a40f772d7ac2b757e7b6b71542171d54a',
 'dio-cary-v1-pdf0108-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0109-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0109-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0110-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0110-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0111-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0111-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0112-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0113-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0113-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0114-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0114-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0115-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0116-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0117-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0118-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0119-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0120-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0121-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0121-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0122-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0123-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0124-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0125-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0126-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0127-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0128-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0128-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0129-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0129-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0130-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0130-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0131-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0131-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0132-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0132-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0133-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0133-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0134-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0134-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0135-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0135-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0136-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0137-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0138-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0138-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0139-fragment': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0139-comparison': 'deeb11e32f58093e6eb3eb3d8ac42c27c7c81dee2232bde96188c13d0ac689cb',
 'dio-cary-v1-pdf0140-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0140-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0141-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0141-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0142-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0143-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0143-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0144-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0144-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0145-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0146-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0146-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0147-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0147-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0148-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0148-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0149-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0149-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0150-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0150-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0151-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0151-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0152-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0152-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0153-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0154-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0154-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0155-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0155-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0156-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0156-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0157-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0158-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0158-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0159-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0159-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0160-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0160-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0161-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0161-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0162-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0162-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0163-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0163-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0164-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0164-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0165-fragment': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0165-comparison': 'e88f62a259d5e6230c7bc832a11a1baf3a548b6685624c3d7c7a7ab44d37f955',
 'dio-cary-v1-pdf0166-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0166-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0167-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0167-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0168-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0168-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0169-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0169-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0170-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0170-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0171-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0171-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0172-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0172-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0173-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0173-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0174-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0175-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0175-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0176-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0176-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0177-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0177-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0178-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0178-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0179-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0179-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0180-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0180-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0181-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0181-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0182-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0182-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0183-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0183-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0184-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0184-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0185-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0185-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0186-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0186-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0187-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0188-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0188-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0189-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0189-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0190-fragment': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0190-comparison': '61697ea4ddc37c383b6a0d3870be24ff8dc40416120619a1b84eacaa84f34efa',
 'dio-cary-v1-pdf0191-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0191-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0192-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0192-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0193-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0193-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0194-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0194-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0195-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0195-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0196-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0196-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0197-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0197-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0198-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0198-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0199-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0199-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0200-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0200-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0201-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0202-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0202-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0203-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0204-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0204-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0205-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0206-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0206-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0207-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0207-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0208-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0209-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0209-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0210-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0210-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0211-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0211-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0212-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0212-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0213-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0214-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0214-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0215-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0215-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0216-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0216-comparison': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0217-fragment': 'd9a69163d2b072d41fa02f79f1501606fbbdd7c59ee029c0ac4ce74f6ff63f61',
 'dio-cary-v1-pdf0217-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0218-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0218-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0219-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0219-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0220-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0220-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0221-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0221-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0222-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0222-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0223-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0223-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0224-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0224-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0225-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0225-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0226-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0226-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0227-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0227-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0228-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0229-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0230-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0231-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0231-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0232-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0232-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0233-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0233-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0234-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0234-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0235-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0236-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0237-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0237-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0238-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0238-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0239-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0239-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0240-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0241-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0241-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0242-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0242-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0243-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0244-comparison': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0245-fragment': '1f7b565ea042a722fc97b200ec538e17f6d6ceef8694ff891f1cb916f35bf618',
 'dio-cary-v1-pdf0245-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0246-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0247-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0248-fragment': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0248-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0249-fragment': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0249-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0250-fragment': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0250-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0251-fragment': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0251-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v1-pdf0252-comparison': '89ff0126488dea12f67b1b5db25f05cdac5b398ace621436db16c0e0f38c0bb6',
 'dio-cary-v2-pdf0007-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0008-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0009-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0010-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0011-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0011-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0012-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0013-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0014-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0015-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0016-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0017-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0017-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0018-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0018-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0019-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0020-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0020-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0021-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0022-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0022-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0023-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0023-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0024-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0024-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0025-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0025-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0026-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0027-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0027-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0028-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0028-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0029-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0029-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0030-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0031-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0031-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0032-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0033-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0034-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0035-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0036-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0036-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0037-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0037-comparison': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0038-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0039-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0040-fragment': '4f089ae0740c9b58d5ffa4345e1fa37ce120d80a1e7ec73f249ff92fdd463119',
 'dio-cary-v2-pdf0041-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0041-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0042-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0042-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0043-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0043-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0044-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0044-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0045-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0045-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0046-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0046-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0047-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0047-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0048-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0049-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0049-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0050-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0050-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0051-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0051-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0052-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0052-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0053-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0053-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0054-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0055-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0056-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0056-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0057-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0057-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0058-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0059-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0060-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0060-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0061-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0061-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0062-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0062-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0063-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0063-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0064-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0064-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0065-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0065-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0066-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0066-comparison': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0067-fragment': '524dc049e0934c7e6cbc42c4747c4b6d8a5c4335e2e5e6f02a298c7d626c4cb7',
 'dio-cary-v2-pdf0067-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0068-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0068-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0069-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0069-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0070-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0071-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0072-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0073-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0073-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0074-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0074-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0075-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0075-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0076-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0077-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0077-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0078-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0078-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0079-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0079-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0080-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0081-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0082-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0082-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0083-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0083-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0084-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0084-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0085-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0086-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0086-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0087-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0088-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0089-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0090-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0091-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0092-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0092-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0093-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0094-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0095-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0096-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0097-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0097-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0098-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0099-fragment': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0099-comparison': 'cf6572dba3ccc2de85e7ac22e492365dc9a762a2d4d0e31153e257d773198fda',
 'dio-cary-v2-pdf0100-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0100-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0101-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0101-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0102-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0102-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0103-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0104-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0104-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0105-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0105-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0106-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0106-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0107-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0107-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0108-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0109-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0110-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0111-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0112-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0113-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0114-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0115-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0115-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0116-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0117-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0117-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0118-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0118-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0119-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0119-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0120-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0120-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0121-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0121-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0122-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0122-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0123-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0123-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0124-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0124-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0125-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0125-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0126-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0126-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0127-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0127-comparison': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0128-fragment': 'f5c23bf60bf504a469be429b6928c3123e5c7b1a10df6f372897cfb0e9a6ba1e',
 'dio-cary-v2-pdf0128-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0129-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0129-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0130-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0130-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0131-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0132-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0132-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0133-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0133-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0134-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0134-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0135-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0135-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0136-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0136-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0137-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0138-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0138-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0139-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0139-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0140-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0140-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0141-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0141-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0142-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0142-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0143-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0143-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0144-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0145-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0145-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0146-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0146-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0147-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0147-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0148-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0148-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0149-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0150-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0151-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0152-fragment': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0152-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0153-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0154-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0155-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0156-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0157-comparison': 'eb76bdaec333c814d9d19d811297edb2dab1f711fabb4f8e64f5df692db9e606',
 'dio-cary-v2-pdf0158-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0159-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0160-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0161-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0161-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0162-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0163-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0163-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0164-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0164-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0165-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0166-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0167-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0167-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0168-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0169-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0169-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0170-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0170-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0171-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0172-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0173-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0174-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0175-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0175-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0176-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0176-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0177-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0178-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0179-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0179-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0180-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0180-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0181-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0182-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0182-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0183-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0183-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0184-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0184-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0185-fragment': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0185-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0186-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0187-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0188-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0189-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0190-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0191-comparison': 'ae1a0c3c9f91549c32b6e21b2f1bc346d0c9fb90ce5eb58af761b3873ea5e769',
 'dio-cary-v2-pdf0192-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0193-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0193-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0194-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0194-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0195-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0195-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0196-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0196-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0197-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0198-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0199-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0199-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0200-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0200-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0201-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0202-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0203-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0204-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0205-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0206-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0206-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0207-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0207-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0208-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0209-comparison': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0210-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0211-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0212-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0213-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0214-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0215-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0216-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0217-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0218-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0219-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0220-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0221-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0222-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0223-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0224-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0225-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0226-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0227-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0228-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0229-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0230-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0231-fragment': '6208d3441449f6dc7008c93519c034766c4a93002a4d4b56ac44608e7c1b65b5',
 'dio-cary-v2-pdf0232-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0233-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0234-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0235-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0236-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0237-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0238-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0239-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0240-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0241-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0242-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0243-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0244-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0245-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0246-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0247-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0248-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0249-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0250-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0251-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0252-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0253-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0254-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0255-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0256-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0257-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5',
 'dio-cary-v2-pdf0258-fragment': '16b679e671cb94437a4ebc78c4e44f38b32dafa30d5ce4219bec6d200aefc0a5'}

FULL_PAGE_IMAGES = {'v2-confirm-01.png': 'e1d5835c34420dfc24e44ba61f81b02b2ff8b3dccacdd8c8b1a84593382a1823',
 'v2-full-02.png': '318f766c079f018fe53a6f021552a7e35f16cb86a1e467bbeb2d5f1ec1d7f823',
 'v2-full-03.png': 'ed92ed5ef952a65ab88db994b0ae24988fa20e1880f76ae5b96d7954e348052a',
 'v2-confirm-02.png': '4d2c9065db86f57bbff367238e2de2cbc3cf6cc34d36c78fb5147d3eb4d49f78',
 'v2-full-01.png': '6f9d0eeb63056bbced8bb74b954eab377082979bd961513600119be8fd7f99ef',
 'v2-confirm-03.png': '4c65d525abe6febf2b350b6f44aaebb3eb146f965736976fdf38aaefc3909b5e',
 'v2-full-04.png': 'f466c5e2b2a08d252b7cc31edf5a0ca3173bd5a769b5e2c85f43c50cd67268e2',
 'v1-sparse-full.png': 'fdbd5cc98d00ffa3749d13ca3403a72a8ca2415a7022cbbff1c995ad67bf41b1',
 'v2-full-05.png': '1bc27ab12be3287ec04acc1c0d09d93ae4c42345845e562fb4574875ff7000f7',
 'v2-121-detail.png': 'b0872062822d99d10c58e87031c82ece7c2c0d3fa510718eea750ae48199ad7c',
 'v1-189-full.png': 'fbf6a80ec08b4228ee858a1649b004b6a5909649a79db8410a79bad653e6d84f',
 'root-v1-confirm-01.png': 'd0c95a947d18ae4d8b4cc44d8d3504f0938ef3826f1a6514e5ff0885327cc103',
 'root-v1-confirm-02.png': '82ea179fbde338ef577081bebdebba7b06c0195fff219361078f4d31a5fe60a5'}

FULL_PAGE_CHECKS = {'dio-cary-v1-pdf0073-comparison': 'Full-page source inspection confirms no Greek apparatus; preserve the '
                                   'original panel.',
 'dio-cary-v1-pdf0094-comparison': 'Full-page source inspection confirms no Greek apparatus; preserve the '
                                   'original panel.',
 'dio-cary-v1-pdf0252-comparison': 'Full-page source inspection confirms no Greek apparatus; preserve the '
                                   'original panel.',
 'dio-cary-v1-pdf0043-comparison': 'Full-page source inspection identifies one high-on-page Greek apparatus '
                                   'note below the three-line Zonaras7,5 quotation.',
 'dio-cary-v1-pdf0189-fragment': 'The primary fragment is exactly one printed line before the full-width '
                                 'rule; preserve the original boundary.',
 'dio-cary-v1-pdf0189-comparison': 'Full-page source inspection confirms the long Greek comparison has no '
                                   'apparatus.',
 'dio-cary-v2-pdf0032-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0048-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0071-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0116-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0155-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0188-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0209-comparison': 'Full-page inspection confirms all Greek body and source credits, with no '
                                   'terminal Greek apparatus.',
 'dio-cary-v2-pdf0216-fragment': 'Full-page inspection confirms all Greek body and source credits, with no '
                                 'terminal Greek apparatus.',
 'dio-cary-v2-pdf0227-fragment': 'Full-page inspection confirms all Greek body and source credits, with no '
                                 'terminal Greek apparatus.',
 'dio-cary-v2-pdf0236-fragment': 'Full-page inspection confirms all Greek body and source credits, with no '
                                 'terminal Greek apparatus.',
 'dio-cary-v2-pdf0210-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0225-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0229-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0241-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0243-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0253-fragment': 'Full-page inspection confirms the later numbered Greek paragraphs are '
                                 'primary body, despite the font proposal; all are preserved before the '
                                 'final smaller editorial notes.',
 'dio-cary-v2-pdf0220-fragment': 'Full-page inspection identifies high-on-page smaller apparatus beneath the '
                                 'short primary Greek body, outside the terminal contact window.',
 'dio-cary-v2-pdf0232-fragment': 'Full-page inspection identifies high-on-page smaller apparatus beneath the '
                                 'short primary Greek body, outside the terminal contact window.',
 'dio-cary-v2-pdf0238-fragment': 'Full-page inspection identifies high-on-page smaller apparatus beneath the '
                                 'short primary Greek body, outside the terminal contact window.',
 'dio-cary-v2-pdf0121-comparison': 'Detailed source inspection preserves the complete final primary word '
                                   'ἀνεῖχον, including its breathing/descender marks, above the smaller '
                                   'supplied-by-Gros note. The boundary is y=.8445.'}

