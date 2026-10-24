"""Source-supported role observations for the Dübner 1855 volume.

This module changes no readings. Offsets use Unicode code points in the frozen
Toronto primary. Apparatus quotations stay out of historical lexical counts.
The lower diagrams on PDF 36 are retained as unresolved historical witnesses,
not relabeled as modern editorial prose. These are local source keys; the
admission pipeline owns destination identities and deduplication.
"""

from __future__ import annotations

import hashlib

TORONTO_PDF_SHA256 = "9d960c70b833f73b3871701775c557a6db1472cc95a04bea8f35054922715c07"
TORONTO_BASELINE_SHA256 = "14736ad45cb79e53f6f6eb64160dc92d1aebe9b2f26ed28ae5ab2490834f38e3"

TORONTO_FRONT_ROWS_SHA256 = 'afb988561813bcccaf7516f9e281ed0969b45e2d473ccd914e6de533774320b3'

# Per-page entries: (first_row, last_row, source_work_key, role, lexical_eligible).
# Row numbers are numeric and inclusive; the extraction sometimes interleaves
# lower apparatus before the right-column historical continuation.
FRONT_PARTITIONS = {7: ((1, 6, 'editorial-material', 'edition-heading', False),),
 13: ((1, 7, 'editorial-material', 'editorial-preface', False),),
 14: ((1, 2, 'editorial-material', 'editorial-preface', False),),
 15: ((1, 2, 'editorial-material', 'editorial-preface', False),),
 16: ((1, 3, 'editorial-material', 'editorial-preface', False),),
 17: ((1, 5, 'editorial-material', 'editorial-preface', False),),
 18: ((1, 5, 'editorial-material', 'editorial-preface', False),),
 19: ((1, 2, 'editorial-material', 'editorial-preface', False),),
 20: ((1, 3, 'editorial-material', 'editorial-preface', False),),
 23: ((1, 2, 'platonius', 'edition-heading', False),
      (3, 5, 'platonius', 'historical-prolegomena', True)),
 24: ((1, 1, 'platonius', 'historical-prolegomena', True),
      (2, 3, 'platonius', 'edition-heading', False),
      (4, 4, 'platonius', 'historical-prolegomena', True),
      (5, 5, 'editorial-material', 'editorial-apparatus', False),
      (6, 6, 'platonius', 'historical-prolegomena', True),
      (7, 7, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (8, 11, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 25: ((1, 31, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (32, 44, 'editorial-material', 'editorial-apparatus', False),
      (45, 71, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (72, 72, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (73, 73, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (74, 75, 'editorial-material', 'editorial-apparatus', False)),
 26: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (3, 4, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (5, 5, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (6, 6, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (7, 7, 'editorial-material', 'editorial-apparatus', False)),
 27: ((1, 2, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (3, 3, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (4, 10, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (11, 11, 'editorial-material', 'editorial-apparatus', False),
      (12, 12, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (13, 14, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (15, 15, 'editorial-material', 'editorial-apparatus', False)),
 28: ((1, 41, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (42, 46, 'editorial-material', 'editorial-apparatus', False),
      (47, 48, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 29: ((1, 5, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),),
 30: ((1, 4, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (5, 5, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (6, 6, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 31: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'editorial-material', 'editorial-apparatus', False),
      (3, 8, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 32: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'andronicus-poet-order', 'edition-heading', False),
      (3, 3, 'andronicus-poet-order', 'historical-prolegomena', True),
      (4, 4, 'editorial-material', 'editorial-apparatus', False)),
 33: ((1, 2, 'tzetzes-poet-differences', 'edition-heading', False),
      (3, 82, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (83, 88, 'editorial-material', 'editorial-apparatus', False)),
 34: ((1, 43, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (44, 55, 'editorial-material', 'editorial-apparatus', False),
      (56, 98, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (99, 103, 'editorial-material', 'editorial-apparatus', False)),
 35: ((1, 10, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (11, 11, 'tzetzes-technical-iambics', 'edition-heading', False),
      (12, 78, 'tzetzes-technical-iambics', 'historical-prolegomena', True),
      (79, 87, 'editorial-material', 'editorial-apparatus', False)),
 36: ((1, 24, 'tzetzes-technical-iambics', 'historical-prolegomena', True),
      (25, 50, 'anonymous-coislinianus', 'unresolved-diagram', False),
      (51, 51, 'tzetzes-technical-iambics', 'historical-prolegomena', True),
      (52, 57, 'anonymous-coislinianus', 'unresolved-diagram', False),
      (58, 59, 'anonymous-coislinianus', 'historical-prolegomena', True),
      (60, 73, 'anonymous-coislinianus', 'unresolved-diagram', False)),
 37: ((1, 5, 'anonymous-coislinianus', 'historical-prolegomena', True),
      (6, 6, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (7, 7, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (8, 8, 'editorial-material', 'editorial-apparatus', False),
      (9, 13, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (14, 14, 'editorial-material', 'editorial-apparatus', False)),
 38: ((1, 5, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (6, 6, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (7, 7, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (8, 8, 'editorial-material', 'editorial-apparatus', False),
      (9, 11, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (12, 13, 'editorial-material', 'editorial-apparatus', False)),
 39: ((1, 13, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (14, 14, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (15, 36, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (37, 40, 'editorial-material', 'editorial-apparatus', False),
      (41, 41, 'suda-aristophanes-excerpt', 'edition-heading', False),
      (42, 42, 'suda-aristophanes-excerpt', 'historical-prolegomena', True),
      (43, 43, 'thomas-magister-aristophanes-life', 'edition-heading', False),
      (44, 45, 'thomas-magister-aristophanes-life', 'historical-prolegomena', True)),
 40: ((1, 1, 'thomas-magister-aristophanes-life', 'historical-prolegomena', True),
      (2, 2, 'triclinius-meters', 'historical-prolegomena', True),
      (3, 3, 'triclinius-common-syllable-signs', 'edition-heading', False),
      (4, 4, 'triclinius-common-syllable-signs', 'historical-prolegomena', True)),
 41: ((1, 3, 'triclinius-common-syllable-signs', 'historical-prolegomena', True),)}


def build(rows):
    """Expand all frozen Toronto front rows into exhaustive character partitions.

    This requires the entire frozen pre-scholia input, so removing an observed
    row is detected as reliably as changing a source string. Rows from later
    pages may be passed too and are ignored by this front matter inventory.
    """
    import json

    front = []
    for row in rows:
        locus = row["locus"]
        if not locus.startswith("scholia_aristoph_dubner_"):
            continue
        page = int(locus.rsplit("_", 1)[1].split(".")[0])
        if page < 43:
            front.append(row)
    original = sorted((row["locus"], row["text"]) for row in front)
    digest = hashlib.sha256(json.dumps(
        original, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if digest != TORONTO_FRONT_ROWS_SHA256:
        raise ValueError("Changed or incomplete Dübner front matter preimages")
    result = {}
    for row in front:
        page, number = map(int, row["locus"].rsplit("_", 1)[1].split("."))
        matches = [entry for entry in FRONT_PARTITIONS.get(page, ())
                   if entry[0] <= number <= entry[1]]
        if len(matches) != 1 or row["locus"] in result:
            raise ValueError(f"Unassessed or duplicate front matter locus: {row['locus']}")
        _, _, work, role, eligible = matches[0]
        result[row["locus"]] = [{
            "start": 0, "end": len(row["text"]), "work": work,
            "role": role, "lexical_eligible": eligible,
            "evidence": f"toronto-pdf-{page:04}",
            "original_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(),
        }]
    return result


# Printed source identities; these are edition attributions, not new CTS IDs.
PROLEGOMENA_UNITS = ({'source_section': 'I',
  'title': 'Ἐκ τῶν Πλατωνίου Περὶ διαφορᾶς κωμῳδιῶν',
  'pdf_pages': (23, 24),
  'work': 'platonius',
  'evidence': 'Printed attribution to Platonius. PDF24 left column ends before II.'},
 {'source_section': 'II',
  'title': 'Τοῦ αὐτοῦ Περὶ διαφορᾶς χαρακτήρων',
  'pdf_pages': (24, 24),
  'work': 'platonius',
  'evidence': 'Begins lower left column and ends upper right column before III; apparatus row24.5 '
              'is excluded.'},
 {'source_section': 'III',
  'title': 'Περὶ κωμῳδίας',
  'pdf_pages': (24, 25),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'No author printed. Starts right column after II.'},
 {'source_section': 'IV',
  'title': 'Ἄλλως περὶ κωμῳδίας',
  'pdf_pages': (25, 26),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'No author printed; begins at bottom of PDF25 right column.'},
 {'source_section': 'V',
  'title': 'Ἄλλως περὶ κωμῳδίας',
  'pdf_pages': (26, 26),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'No author printed; left lower column through upper right column.'},
 {'source_section': 'VI',
  'title': 'Ἄλλως περὶ κωμῳδίας',
  'pdf_pages': (26, 27),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'No author printed; right column through next page left upper column.'},
 {'source_section': 'VII',
  'title': 'Untitled note on the comic chorus',
  'pdf_pages': (27, 27),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'Printed VII; starts Ὁ χορὸς ὁ κωμικός. No author printed.'},
 {'source_section': 'VIII',
  'title': 'Τῶν τῆς ἀρχαίας κωμῳδίας ποιητῶν ὀνόματα καὶ δράματα',
  'pdf_pages': (27, 27),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'List of poets and drama counts; anonymous historical list, not an editorial index.'},
 {'source_section': 'IXa',
  'title': 'Περὶ κωμῳδίας',
  'pdf_pages': (27, 30),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'Printed source note cites Cramer Anecdota Parisiensia I p3; no author printed. '
              'Lower apparatus is separate.'},
 {'source_section': 'IXb',
  'title': 'Περὶ κωμῳδίας',
  'pdf_pages': (30, 32),
  'work': 'anonymous-comedy-prolegomena',
  'evidence': 'Printed source note cites scholia to Dionysius Thrax and Bekker p747–748; source '
              'text includes an unheaded related continuation from Baroccianus116 per apparatus. '
              'Preserve collection, do not fabricate individual authorship.'},
 {'source_section': 'X',
  'title': 'Ἀνδρονίκου Περὶ τάξεως ποιητῶν',
  'pdf_pages': (32, 32),
  'work': 'andronicus-poet-order',
  'evidence': 'Heading attributes to Andronicus. Dübner footnote identifies Caecius/Tzetzes '
              'following Dindorf: conflicting attribution must remain explicit. Toronto OCR omits '
              'beginning of Greek body; surviving row32.3 begins Κωμικῶν.'},
 {'source_section': 'Xa',
  'title': 'Scholion Plautinum',
  'pdf_pages': (32, 32),
  'work': 'anonymous-latin-scholion',
  'evidence': 'Historical Latin scholion edited from a Roman manuscript, not Dübner Latin '
              'commentary. No Toronto Greek rows correspond; do not invent missing transcription.'},
 {'source_section': 'Xb',
  'title': 'Ἰωάννου τοῦ Τζέτζου Στίχοι περὶ διαφορᾶς ποιητῶν',
  'pdf_pages': (33, 35),
  'work': 'tzetzes-poet-differences',
  'evidence': 'Explicit printed attribution to John Tzetzes. Embedded apparatus and its extended '
              'quotations are excluded.'},
 {'source_section': 'Xc',
  'title': 'Τοῦ αὐτοῦ ἴαμβοι τεχνικοὶ περὶ κωμῳδίας',
  'pdf_pages': (35, 36),
  'work': 'tzetzes-technical-iambics',
  'evidence': 'Printed Τοῦ αὐτοῦ refers to Tzetzes. Preserve edition attribution; no independent '
              'authorship adjudication.'},
 {'source_section': 'Xd',
  'title': 'Anonymous comedy treatise from Codex Coislinianus',
  'pdf_pages': (36, 37),
  'work': 'anonymous-coislinianus',
  'evidence': 'Printed Ex codice Coisliniano apud Cramer Anecd. Paris I403. Two schematic diagrams '
              'on PDF36 have scrambled OCR retained as unresolved historical witnesses, not modern '
              'apparatus.'},
 {'source_section': 'XI',
  'title': 'Ἀριστοφάνους βίος',
  'pdf_pages': (37, 38),
  'work': 'anonymous-aristophanes-lives',
  'evidence': 'Anonymous biography; ends PDF38 left before XII.'},
 {'source_section': 'XII',
  'title': 'Ἄλλως [βίος Ἀριστοφάνους]',
  'pdf_pages': (38, 39),
  'work': 'anonymous-aristophanes-lives',
  'evidence': 'Printed source note Ex codice Veneto474; no author printed.'},
 {'source_section': 'XIII',
  'title': 'Ἄλλως [βίος Ἀριστοφάνους]',
  'pdf_pages': (39, 39),
  'work': 'anonymous-aristophanes-lives',
  'evidence': 'Printed source note scholia on Plato Apology, Porson Miscellanea p268 Kidd; no '
              'author printed.'},
 {'source_section': 'XIV',
  'title': 'Ἄλλως [βίος Ἀριστοφάνους]',
  'pdf_pages': (39, 39),
  'work': 'suda-aristophanes-excerpt',
  'evidence': 'Printed source note Ex Suida; should deduplicate against already served Suda rather '
              'than create a new anonymous primary.'},
 {'source_section': 'XV',
  'title': 'Θωμᾶ τοῦ Μαγίστρου [βίος Ἀριστοφάνους]',
  'pdf_pages': (39, 40),
  'work': 'thomas-magister-aristophanes-life',
  'evidence': 'Explicit Thomas Magister attribution. Also includes the following unheaded '
              'comedy-origin paragraph on PDF40 before XVI; keep its relation visible.'},
 {'source_section': 'XVIa',
  'title': 'Ἀντιπάτρου Θεσσαλονικέως εἰς Ἀριστοφάνην',
  'pdf_pages': (40, 40),
  'work': 'antipater-thessalonica-aristophanes-epigram',
  'evidence': 'Printed Anthologia Palatina IX186. Entire epigram omitted from Toronto extraction; '
              'Harvard has it. Deduplicate against AP source.'},
 {'source_section': 'XVIb',
  'title': 'Διοδώρου ἐπιτύμβιον [εἰς Ἀριστοφάνην]',
  'pdf_pages': (40, 40),
  'work': 'diodorus-aristophanes-epitaph',
  'evidence': 'Printed Anthologia Palatina VII38. Entire epigram omitted from Toronto extraction; '
              'Harvard has it. Deduplicate against AP source.'},
 {'source_section': 'XVIIa',
  'title': 'Δημητρίου τοῦ Τρικλινίου [περὶ μέτρων]',
  'pdf_pages': (40, 40),
  'work': 'triclinius-meters',
  'evidence': 'Explicit printed author heading; Toronto omits opening column section and retains '
              'only right-column continuation starting δακτυλικοῦ.'},
 {'source_section': 'XVIIb',
  'title': 'Τοῦ αὐτοῦ περὶ σημείων τῆς κοινῆς συλλαβῆς τῶν ἐντὸς κειμένων τῆς βίβλου',
  'pdf_pages': (40, 41),
  'work': 'triclinius-common-syllable-signs',
  'evidence': 'Subheading attributes to same Demetrius Triclinius. Ends PDF41 with no subsequent '
              'historical text on blank42.'})


HARVARD_PDF_SHA256 = "61c07b9dbde80569c6e54238f2cbb0897d8bb33386a9ecad389836bd67e0c600"
HARVARD_FRONT_ROWS_SHA256 = '434eb213e38fa2fb366787771c16f9580dccad843f8e4f3f85b7fdfffa2a5f1b'

# Includes all572 primary and8 exact cross-work secondary front rows.
HARVARD_FRONT_PARTITIONS = {8: ((1, 4, 'editorial-material', 'edition-heading', False),),
 14: ((1, 4, 'editorial-material', 'editorial-preface', False),),
 18: ((1, 2, 'editorial-material', 'editorial-preface', False),),
 19: ((1, 16, 'editorial-material', 'editorial-preface', False),),
 24: ((1, 3, 'platonius', 'edition-heading', False),
      (4, 6, 'platonius', 'historical-prolegomena', True)),
 25: ((1, 2, 'platonius', 'historical-prolegomena', True),
      (3, 3, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (4, 4, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (5, 6, 'platonius', 'edition-heading', False),
      (7, 7, 'platonius', 'historical-prolegomena', True)),
 26: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'anonymous-comedy-prolegomena', 'edition-heading', False)),
 27: ((1, 2, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (3, 3, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (4, 4, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (5, 5, 'editorial-material', 'editorial-apparatus', False),
      (6, 6, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (7, 7, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (8, 8, 'editorial-material', 'editorial-apparatus', False)),
 28: ((1, 2, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (3, 3, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (4, 10, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (11, 11, 'editorial-material', 'editorial-apparatus', False),
      (12, 12, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (13, 14, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (15, 15, 'editorial-material', 'editorial-apparatus', False)),
 29: ((1, 4, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),),
 30: ((1, 2, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),),
 31: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'anonymous-comedy-prolegomena', 'edition-heading', False),
      (3, 3, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 32: ((1, 33, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (34, 34, 'editorial-material', 'editorial-apparatus', False),
      (35, 40, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True)),
 33: ((1, 1, 'anonymous-comedy-prolegomena', 'historical-prolegomena', True),
      (2, 2, 'andronicus-poet-order', 'edition-heading', False),
      (3, 3, 'andronicus-poet-order', 'historical-prolegomena', True),
      (4, 4, 'editorial-material', 'editorial-apparatus', False)),
 34: ((1, 2, 'tzetzes-poet-differences', 'edition-heading', False),
      (3, 82, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (83, 97, 'editorial-material', 'editorial-apparatus', False)),
 35: ((1, 43, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (44, 55, 'editorial-material', 'editorial-apparatus', False),
      (56, 98, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (99, 104, 'editorial-material', 'editorial-apparatus', False)),
 36: ((1, 10, 'tzetzes-poet-differences', 'historical-prolegomena', True),
      (11, 11, 'tzetzes-technical-iambics', 'edition-heading', False),
      (12, 78, 'tzetzes-technical-iambics', 'historical-prolegomena', True),
      (79, 87, 'editorial-material', 'editorial-apparatus', False)),
 37: ((1, 25, 'tzetzes-technical-iambics', 'historical-prolegomena', True),
      (26, 31, 'anonymous-coislinianus', 'unresolved-diagram', False),
      (32, 40, 'anonymous-coislinianus', 'historical-prolegomena', True),
      (41, 57, 'anonymous-coislinianus', 'unresolved-diagram', False),
      (58, 60, 'editorial-material', 'editorial-apparatus', False)),
 38: ((1, 5, 'anonymous-coislinianus', 'historical-prolegomena', True),
      (6, 8, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (9, 9, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (10, 10, 'anonymous-aristophanes-lives', 'historical-prolegomena', True)),
 39: ((1, 5, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (6, 6, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (7, 7, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (8, 10, 'editorial-material', 'editorial-apparatus', False)),
 40: ((1, 13, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (14, 14, 'anonymous-aristophanes-lives', 'edition-heading', False),
      (15, 36, 'anonymous-aristophanes-lives', 'historical-prolegomena', True),
      (37, 40, 'editorial-material', 'editorial-apparatus', False),
      (41, 41, 'suda-aristophanes-excerpt', 'edition-heading', False),
      (42, 52, 'suda-aristophanes-excerpt', 'historical-prolegomena', True),
      (53, 53, 'thomas-magister-aristophanes-life', 'edition-heading', False),
      (54, 77, 'thomas-magister-aristophanes-life', 'historical-prolegomena', True),
      (78, 82, 'editorial-material', 'editorial-apparatus', False)),
 41: ((1, 1, 'thomas-magister-aristophanes-life', 'historical-prolegomena', True),
      (2, 2, 'triclinius-meters', 'historical-prolegomena', True),
      (3, 3, 'triclinius-common-syllable-signs', 'edition-heading', False),
      (4, 4, 'triclinius-common-syllable-signs', 'historical-prolegomena', True),
      (5, 5, 'antipater-thessalonica-aristophanes-epigram', 'edition-heading', False),
      (6, 7, 'antipater-thessalonica-aristophanes-epigram', 'historical-prolegomena', True),
      (8, 8, 'diodorus-aristophanes-epitaph', 'edition-heading', False),
      (9, 9, 'diodorus-aristophanes-epitaph', 'historical-prolegomena', True),
      (10, 10, 'triclinius-meters', 'historical-prolegomena', True)),
 42: ((1, 3, 'triclinius-common-syllable-signs', 'historical-prolegomena', True),)}


def build_harvard(rows):
    """Expand original Harvard front witnesses, including exact secondary rows.

    This consumes literal source rows, not constructed fallback rows, as returned
    by dubner_witness_alignment.source_rows. It does not select a winning OCR
    reading or count the same printed passage as an independent occurrence.
    """
    import json

    front = []
    for row in rows:
        locus = row["locus"]
        if not locus.startswith("platonius_duebner_scholaristoph1_"):
            continue
        page = int(locus.rsplit("_", 1)[1].split(".")[0])
        if page < 44:
            front.append(row)
    original = sorted((row["locus"], row["text"]) for row in front)
    digest = hashlib.sha256(json.dumps(
        original, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if digest != HARVARD_FRONT_ROWS_SHA256:
        raise ValueError("Changed or incomplete Harvard front matter preimages")
    result = {}
    for row in front:
        page, number = map(int, row["locus"].rsplit("_", 1)[1].split("."))
        matches = [entry for entry in HARVARD_FRONT_PARTITIONS.get(page, ())
                   if entry[0] <= number <= entry[1]]
        if len(matches) != 1 or row["locus"] in result:
            raise ValueError(f"Unassessed or duplicate Harvard front locus: {row['locus']}")
        _, _, work, role, eligible = matches[0]
        spans = [{"start": 0, "end": len(row["text"]), "work": work,
                  "role": role, "lexical_eligible": eligible,
                  "evidence": f"harvard-pdf-{page:04}",
                  "original_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest()}]
        if row["locus"] == "platonius_duebner_scholaristoph1_0031.3":
            # The source's italic Latin citation (including its Greek quotation)
            # precedes the historical treatise body in this one original row.
            offset = row["text"].index("Κωμῳδία ἐστὶν")
            spans = [dict(spans[0], end=offset, work="editorial-material",
                          role="editorial-source-note", lexical_eligible=False),
                     dict(spans[0], start=offset)]
        result[row["locus"]] = spans
    return result


# Printed play/hypothesis/author headings; preserve but exclude from lexical counts.
PLAY_HEADING_LOCI = {'toronto': ('scholia_aristoph_dubner_0043.1',
             'scholia_aristoph_dubner_0043.2',
             'scholia_aristoph_dubner_0043.9',
             'scholia_aristoph_dubner_0043.10',
             'scholia_aristoph_dubner_0074.1',
             'scholia_aristoph_dubner_0074.3',
             'scholia_aristoph_dubner_0074.9',
             'scholia_aristoph_dubner_0074.10',
             'scholia_aristoph_dubner_0119.1',
             'scholia_aristoph_dubner_0119.6',
             'scholia_aristoph_dubner_0119.7',
             'scholia_aristoph_dubner_0120.3',
             'scholia_aristoph_dubner_0177.1',
             'scholia_aristoph_dubner_0177.4',
             'scholia_aristoph_dubner_0177.5',
             'scholia_aristoph_dubner_0211.1',
             'scholia_aristoph_dubner_0211.2',
             'scholia_aristoph_dubner_0211.4',
             'scholia_aristoph_dubner_0212.1',
             'scholia_aristoph_dubner_0212.2',
             'scholia_aristoph_dubner_0251.1',
             'scholia_aristoph_dubner_0251.5',
             'scholia_aristoph_dubner_0252.12',
             'scholia_aristoph_dubner_0252.13',
             'scholia_aristoph_dubner_0290.1',
             'scholia_aristoph_dubner_0290.2',
             'scholia_aristoph_dubner_0290.4',
             'scholia_aristoph_dubner_0290.5',
             'scholia_aristoph_dubner_0306.1',
             'scholia_aristoph_dubner_0306.46',
             'scholia_aristoph_dubner_0315.1',
             'scholia_aristoph_dubner_0315.8',
             'scholia_aristoph_dubner_0315.9',
             'scholia_aristoph_dubner_0315.20',
             'scholia_aristoph_dubner_0316.3',
             'scholia_aristoph_dubner_0357.1',
             'scholia_aristoph_dubner_0357.2',
             'scholia_aristoph_dubner_0357.4',
             'scholia_aristoph_dubner_0357.5',
             'scholia_aristoph_dubner_0357.10',
             'scholia_aristoph_dubner_0365.1',
             'scholia_aristoph_dubner_0365.2',
             'scholia_aristoph_dubner_0365.5',
             'scholia_aristoph_dubner_0366.1',
             'scholia_aristoph_dubner_0366.2'),
 'harvard': ('platonius_duebner_scholaristoph1_0044.1',
             'platonius_duebner_scholaristoph1_0044.2',
             'platonius_duebner_scholaristoph1_0044.4',
             'platonius_duebner_scholaristoph1_0044.5',
             'platonius_duebner_scholaristoph1_0075.1',
             'platonius_duebner_scholaristoph1_0075.2',
             'platonius_duebner_scholaristoph1_0075.4',
             'platonius_duebner_scholaristoph1_0075.9',
             'platonius_duebner_scholaristoph1_0120.1',
             'platonius_duebner_scholaristoph1_0120.2',
             'platonius_duebner_scholaristoph1_0120.6',
             'platonius_duebner_scholaristoph1_0120.7',
             'platonius_duebner_scholaristoph1_0121.3',
             'platonius_duebner_scholaristoph1_0186.1',
             'platonius_duebner_scholaristoph1_0186.2',
             'platonius_duebner_scholaristoph1_0186.5',
             'platonius_duebner_scholaristoph1_0186.6',
             'platonius_duebner_scholaristoph1_0238.1',
             'platonius_duebner_scholaristoph1_0238.2',
             'platonius_duebner_scholaristoph1_0239.1',
             'platonius_duebner_scholaristoph1_0239.2',
             'platonius_duebner_scholaristoph1_0278.1',
             'platonius_duebner_scholaristoph1_0279.67',
             'platonius_duebner_scholaristoph1_0279.68',
             'platonius_duebner_scholaristoph1_0317.1',
             'platonius_duebner_scholaristoph1_0317.2',
             'platonius_duebner_scholaristoph1_0317.4',
             'platonius_duebner_scholaristoph1_0317.5',
             'platonius_duebner_scholaristoph1_0333.1',
             'platonius_duebner_scholaristoph1_0342.1',
             'platonius_duebner_scholaristoph1_0342.2',
             'platonius_duebner_scholaristoph1_0342.4',
             'platonius_duebner_scholaristoph1_0342.5',
             'platonius_duebner_scholaristoph1_0342.7',
             'platonius_duebner_scholaristoph1_0343.25',
             'platonius_duebner_scholaristoph1_0390.1',
             'platonius_duebner_scholaristoph1_0390.2',
             'platonius_duebner_scholaristoph1_0391.1',
             'platonius_duebner_scholaristoph1_0391.2')}
