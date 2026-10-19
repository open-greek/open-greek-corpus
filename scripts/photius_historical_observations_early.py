"""Bounded historical Photius corrections read on the pinned Bekker scan.

Only listed occurrences were checked. These observations are inputs to the
reversible historical reading compiler; they never rewrite corpus files.
The full original rows, exact source images, digital windows and earlier
correction history are retained by that compiler.
"""
from copy import deepcopy

SOURCE_PDF_SHA256 = 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'
SOURCE_LIBRARY_SHA256 = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
REVIEWED_AT = '2026-10-19T00:30:00Z'

_OBSERVATIONS = [{'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.1',
  'original_text': 'ἁγίῳ',
  'corrected_text': 'ἁγίοις',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.1',
  'original_text': 'Εὐαλογίου',
  'corrected_text': 'ΕΥΛΟΓΙΟΥ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.1',
  'original_text': 'βίβλῳ',
  'corrected_text': 'βίβλος',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.2',
  'original_text': "λόγος μ'",
  'corrected_text': "λόγοις ια'",
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.2',
  'original_text': "τούτων δ' ἁ Γώμης",
  'corrected_text': "τούτων ὁ α' Ῥώμης",
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.2',
  'original_text': 'ἤλεγ-',
  'corrected_text': 'ἔλεγε',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.3',
  'original_text': 'ὡς ἰδεῖσθαι μέν',
  'corrected_text': 'ὃς ἐδέξατο μὲν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.3',
  'original_text': 'παρὰ τῷ συγγραφέως',
  'corrected_text': 'παρὰ τοῦ συγγραφέως',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.4',
  'original_text': 'ἐπισολῆν',
  'corrected_text': 'ἐπιστολὴν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.4',
  'original_text': 'ἐνδαὶν',
  'corrected_text': 'ἐνδεῖν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.4',
  'original_text': 'ἀντεδύλωσαν',
  'corrected_text': 'ἀντεδήλωσεν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.5',
  'original_text': 'τεσσαράων',
  'corrected_text': 'τεσσάρων',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.5',
  'original_text': 'προσοχρησίας ὀνόματι',
  'corrected_text': 'προσηγορίας ῥήματι',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.6',
  'original_text': 'συνῆψαν',
  'corrected_text': 'συνέστησαν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.6',
  'original_text': 'τὰ πλήθους',
  'corrected_text': 'τοῦ πλήθους',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.7',
  'original_text': 'τῶν ἀρχῶν ὀνομάτων ἔσχησαν',
  'corrected_text': 'τὸν ἀριθμὸν ἑκάστης ἐσήμηνε',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.7',
  'original_text': "δι' αὐτὸ ἢ",
  'corrected_text': "ὅτι οὐδ' ἡ",
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.8',
  'original_text': 'ἁγίῳ',
  'corrected_text': 'ἁγίοις',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.9',
  'original_text': 'Λιδοκωρος',
  'corrected_text': 'Διόσκορος',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.10',
  'original_text': 'ἀναίρεματι παρεδιδόμην',
  'corrected_text': 'ἀναθέματι παρεδόθησαν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.10',
  'original_text': "δι' ἣν ἡν",
  'corrected_text': 'ὅτι ἡ ἐν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.11',
  'original_text': 'ἔχουν ἀπηγύησαν',
  'corrected_text': 'ἐχρῆν ἀπηγγέλλετο',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.11',
  'original_text': 'ἡ μὲν οὖ τα',
  'corrected_text': 'ἃ μὲν ὁ τὰ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.12',
  'original_text': 'ἡττῷτο',
  'corrected_text': 'ᾐτιᾶτο',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.12',
  'original_text': 'γν· ὁ μόντοι',
  'corrected_text': 'ἦν· ὁ μέντοι',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.13',
  'original_text': 'ἡτιώθη διδύς',
  'corrected_text': 'ᾐτιάθη διδούς',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.14',
  'original_text': 'παρειλῆχθαι',
  'corrected_text': 'περιειλῆφθαι',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.14',
  'original_text': 'τῇσιν',
  'corrected_text': 'φησὶν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.15',
  'original_text': 'εἰ ἰδοὺς παραλειφθῆναι',
  'corrected_text': 'ἃ ἔδοξε παραλελεῖφθαι',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.15',
  'original_text': 'πλατεῖν',
  'corrected_text': 'πλατύτερον',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.16',
  'original_text': 'νὶν εἰσαὶν',
  'corrected_text': 'νῦν εἰπεῖν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.16',
  'original_text': 'μηδὲν λαβεῖν ὑπὸν',
  'corrected_text': 'μηδένα λαβεῖν ὄκνον',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.17',
  'original_text': 'σπουδαῖος',
  'corrected_text': 'σπουδαίως',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.17',
  'original_text': 'Θεοφρόνως',
  'corrected_text': 'θεοφρόνως',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.17',
  'original_text': 'ἐπιτιλῶν',
  'corrected_text': 'ἐπιτελῶν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.17',
  'original_text': 'ἀρῖαν',
  'corrected_text': 'ἄριστόν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.18',
  'original_text': 'τελειότατον',
  'corrected_text': 'τελεώτατον',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.18',
  'original_text': 'τὰ τε ἄλλα ἢ',
  'corrected_text': 'τά τε ἄλλα καὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.18',
  'original_text': 'πέσεως',
  'corrected_text': 'πίστεως',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.19',
  'original_text': 'ἱερῶν',
  'corrected_text': 'ἱερὰν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.19',
  'original_text': 'διατιθῆσαν',
  'corrected_text': 'διατίθησιν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.21',
  'original_text': 'ἀδιαίρετον τε ἢ',
  'corrected_text': 'ἀδιαίρετόν τε καὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.22',
  'original_text': 'ἕνωσιν ἔμει',
  'corrected_text': 'ἕνωσιν ὑμνεῖ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.22',
  'original_text': 'ἐκστρέψαν',
  'corrected_text': 'ἑκατέρωθεν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.23',
  'original_text': 'φράδας',
  'corrected_text': 'φυάδας',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.23',
  'original_text': 'κέχρη δὲ',
  'corrected_text': 'κέχρηται δὲ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.25',
  'original_text': 'ἄνεν Ἀπολιναρίων',
  'corrected_text': 'ἄθεον Ἀπολινάριον',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.26',
  'original_text': 'χρηθῆ διμαστροφημένως',
  'corrected_text': 'χρῆσθαι διαμαρτυρόμενος',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.27',
  'original_text': 'δπαπεβὴ',
  'corrected_text': 'δυσσεβῆ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.29',
  'original_text': 'ἀδιαιρέτοις τε ἢ',
  'corrected_text': 'ἀδιαιρέτοις τε καὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.30',
  'original_text': 'Θεότητι ἢ',
  'corrected_text': 'θεότητι καὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.31',
  'original_text': 'σύγχυσιν αὐτῷ δηλώσῃς',
  'corrected_text': 'σύγχυσιν αὐτῷ δηλώσης',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.32',
  'original_text': 'παρασαγῆσης',
  'corrected_text': 'παρεισαγούσης',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.32',
  'original_text': 'τούτοις δὲ ἢ',
  'corrected_text': 'τούτοις δὲ καὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.34',
  'original_text': 'τῷ Θεῷ λόγῳ',
  'corrected_text': 'τοῦ θεοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.35',
  'original_text': "ἐν ᾧ γ' ἔγραψαν σιααρχωμένην",
  'corrected_text': 'ἐν οἷς γάρ φησαν σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.36',
  'original_text': 'ἀνέκηρυσαν',
  'corrected_text': 'ἀνεκήρυξαν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.37',
  'original_text': 'αὐτὸ πόνοις',
  'corrected_text': 'αὐτοῦ πόνοις',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.38',
  'original_text': 'ἐπισχημαζόμενος',
  'corrected_text': 'ἐπισημηνάμενος',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.38',
  'original_text': 'τῇσι μερίζεται διανοία',
  'corrected_text': 'φησὶ μερίζεσθαι διανοίᾳ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.39',
  'original_text': 'παρῆσαν',
  'corrected_text': 'παροῦσαν',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.39',
  'original_text': "καὶ γ' τὸ σιααρχωμένην ἢ ἀντί",
  'corrected_text': 'καὶ γὰρ τὸ σεσαρκωμένη ἢ ἀντὶ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.40',
  'original_text': 'τῷ σαρκὶ ἐχματισμένην ἢ σὸν εἰδοποιηθεῖσα, ὥστε',
  'corrected_text': 'τοῦ σαρκὶ ἐσχηματισμένη καὶ οἷον εἰδοποιηθεῖσα, ὥσπερ',
  'occurrence': 0,
  'source_region': [0.05, 0.108, 0.415, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.45',
  'original_text': 'χαλὰς',
  'corrected_text': 'χαλκοῦς',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.45',
  'original_text': 'τῷ ἀνθρώπινος',
  'corrected_text': 'τοῦ ἀνδριάντος',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.45',
  'original_text': 'ἐκληγδεῖν ἂν',
  'corrected_text': 'ἐκληφθείη ἄν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.46',
  'original_text': 'εἰς σώματα',
  'corrected_text': 'εἰς σάρκα',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.46',
  'original_text': 'τῷ λόγῳ φέσεως τραπέσεως ἢ οὐ',
  'corrected_text': 'τοῦ λόγου φύσεως τραπείσης καὶ οἷον',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.47',
  'original_text': 'ἀποσαφωθεῖσης',
  'corrected_text': 'ἀποσαρκωθείσης',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.47',
  'original_text': 'ἢ φέσις· ἢ δτι μία δόσ',
  'corrected_text': 'ἡ φύσις· ἢ ὅτι μία οὖσα',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.48',
  'original_text': 'τῷ λόγῳ φέσις',
  'corrected_text': 'τοῦ λόγου φύσις',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.48',
  'original_text': 'ἄνετι',
  'corrected_text': 'οὐκέτι',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.49',
  'original_text': 'θεωρεῖ',
  'corrected_text': 'θεωρεῖται',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.49',
  'original_text': 'ἄτρεπτον ἢ',
  'corrected_text': 'ἄτρεπτον καὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.50',
  'original_text': 'προσληψίσει',
  'corrected_text': 'προσληφθείσῃ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.51',
  'original_text': 'σώσασα',
  'corrected_text': 'σώζουσα',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.52',
  'original_text': 'ἵσσει ἢ Εὐτυχία',
  'corrected_text': 'ἴσασι καὶ Εὐτυχέα',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.52',
  'original_text': 'δόξα τὴ',
  'corrected_text': 'δόξα τοῦ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.53',
  'original_text': 'ἀποσύλων',
  'corrected_text': 'ἀποστόλων',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.54',
  'original_text': 'συνείληφεν. ἢ',
  'corrected_text': 'συνετήρησεν. καὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.55',
  'original_text': 'εἰσελθεῖν',
  'corrected_text': 'εὐσεβεῖν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.56',
  'original_text': 'φησιν τοῦ λόγου σσαρκομένην',
  'corrected_text': 'φύσιν τοῦ λόγου σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.56',
  'original_text': 'φρονεῖν ἐν',
  'corrected_text': 'φρονεῖν ἂν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.57',
  'original_text': 'χαριτωθεῖς',
  'corrected_text': 'χαριτωθείη',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.57',
  'original_text': 'δύο φύσεως ἀδιαρέτους ἢ ἀσυγχέτως',
  'corrected_text': 'δύο φύσεις ἀδιαιρέτως καὶ ἀσυγχύτως',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.58',
  'original_text': 'θεωρεῖν τε καὶ',
  'corrected_text': 'θεωροῦσί τε καὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.59',
  'original_text': 'ζειν',
  'corrected_text': 'ζουσιν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.59',
  'original_text': 'Ἀπολυνάριον',
  'corrected_text': 'Ἀπολινάριον',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.60',
  'original_text': 'δραμίζεται',
  'corrected_text': 'δραμεῖται',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.60',
  'original_text': 'φησιν',
  'corrected_text': 'φύσιν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 3},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.61',
  'original_text': 'ἐποσάσεως εἰρήθη',
  'corrected_text': 'ὑποστάσεως εἰρῆσθαι',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.61',
  'original_text': 'σσαρκομένην',
  'corrected_text': 'σεσαρκωμένη',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 4},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.63',
  'original_text': 'φησιν τῷ λόγῳ σσαρκομένην',
  'corrected_text': 'φύσιν τοῦ λόγου σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.64',
  'original_text': 'τῷ λόγῳ',
  'corrected_text': 'τοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 4},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.64',
  'original_text': 'ἀναλαβόντα',
  'corrected_text': 'ἀναλαβῶσαν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.65',
  'original_text': 'ἐπιζητῶμενοι',
  'corrected_text': 'ἐπεξηγούμενοι',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.65',
  'original_text': 'ἐπάγαγον',
  'corrected_text': 'ἐπάγουσιν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.66',
  'original_text': 'ἀνηρημένης',
  'corrected_text': 'ἀνῃρημένης',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.67',
  'original_text': 'ἐκατέρας',
  'corrected_text': 'ἑκατέρας',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.68',
  'original_text': 'δρῷ',
  'corrected_text': 'ὅρῳ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.68',
  'original_text': 'αὐτῷ ἢ ἐνὶ',
  'corrected_text': 'αὐτῷ καὶ ἑνὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.69',
  'original_text': 'ὧδε',
  'corrected_text': 'ὥστε',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.70',
  'original_text': 'ὁμολογεῖ, ἢ δὲ ὁμολογεῖ, ἢ ἀριθμεῖται',
  'corrected_text': 'ὁμολογεῖται, ἃ δὲ ὁμολογεῖται, καὶ ἀριθμεῖται',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.71',
  'original_text': 'τῷ λόγῳ σσαρκομένην, ἢ',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην, καὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.72',
  'original_text': 'ἀδιαρέτους',
  'corrected_text': 'ἀδιαιρέτως',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.73',
  'original_text': 'διαφορὰν ἴδειαν',
  'corrected_text': 'διαφορὰν οὐδεμίαν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.73',
  'original_text': 'ἔμπειρόν',
  'corrected_text': 'ἐμποιεῖ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.74',
  'original_text': 'ἢ τοιαῦτα εἰπεῖν πειρατοῦ',
  'corrected_text': 'καὶ τοιαῦτα ἕτερα εἰπὼν περατοῖ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.75',
  'original_text': 'ἐπιγράφει',
  'corrected_text': 'ἐπιγράφεται',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.75',
  'original_text': 'δὲ ἢ',
  'corrected_text': 'δὲ καὶ',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.76',
  'original_text': 'ἀπαγγέλλει πίσεως· ἐν ᾧ τὴν τε',
  'corrected_text': 'ἀπαγγέλλει πίστεως· ἐν ᾗ τήν τε',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.79',
  'original_text': 'ὅδὲν',
  'corrected_text': 'οὐδὲν',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.79',
  'original_text': 'καθυστερῆς',
  'corrected_text': 'καθυφιείς',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.80',
  'original_text': 'ἢ ταῦτα',
  'corrected_text': 'καὶ ταῦτα',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.80',
  'original_text': 'πειραίνει',
  'corrected_text': 'περαίνει',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.82',
  'original_text': 'ἀσπάσασθι',
  'corrected_text': 'ἀσπάσασθαι',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.84',
  'original_text': 'ἐπηρετῶν τῷ λόγῳ',
  'corrected_text': 'ὑπηρετῶν τοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 2,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.85',
  'original_text': 'ἢ διαφορὰ',
  'corrected_text': 'ἡ διαφορά',
  'occurrence': 0,
  'source_region': [0.408, 0.108, 0.77, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 2, printed page 267, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s279; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'μετ ἐπιχρύψεως',
  'corrected_text': 'μετ’ ἐπικρύψεως',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἀπαγγέλλει, ἥ',
  'corrected_text': 'ἀπαγγέλλεθαι, καὶ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἐξέπτηδες περιβάλλει',
  'corrected_text': 'ἐξεπίτηδες περιβάλλεσθαι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'βεβήλοις εἰς τὰ ἅγια ἔνδετα ἢ',
  'corrected_text': 'βεβήλοις εἶεν τὰ ἅγια ἔκθετα καὶ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'τοὺς χοίρους προκείμενος',
  'corrected_text': 'τοῖς χοίροις προκείμενοι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'χρυψίματα',
  'corrected_text': 'κηρύγματα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἐπιχρύψεως ἀπαγγέλλει, ἡ',
  'corrected_text': 'ἐπικρύψεως ἀπαγγέλλεσθαι, καὶ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'μάλιστα δσα',
  'corrected_text': 'μάλιστα ὅσα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἐντολῶν ἢ',
  'corrected_text': 'ἐντολῶν καὶ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'συντήρησιν ἀναφέρεται',
  'corrected_text': 'συντήρησιν ἀναφέρεσθαι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἄναι δὲ ἡ',
  'corrected_text': 'εἶναι δὲ καὶ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἐτι τινὰ μυσικώτερα',
  'corrected_text': 'ἔτι τινὰ μυστικώτερα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ὡς τὸ ἴππος φάναι σσεῖν',
  'corrected_text': 'ὡς τὸ ἔπος φάναι σεσίγηται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'ἐκεῖνος δὲ μόνους μυσικῶς παραδίδωσι',
  'corrected_text': 'ἐκείνοις δὲ μόνοις μυστικῶς παραδέδοται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.1',
  'original_text': 'οἱ διὰ λόγον ζῆτον',
  'corrected_text': 'οἳ διὰ λόγου ζῶντος',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'πεισοὺς ταῦτα παρατίθεται',
  'corrected_text': 'πιστοῖς ταῦτα παρατίθεσθαι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἐτι δὲ διασολὴ',
  'corrected_text': 'ἔτι δὲ διαστολὴν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἐπὶ τῷ Χριστῷ λεγομένων ποιεῖ',
  'corrected_text': 'ἐπὶ Χριστοῦ λεγομένων ποιεῖται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἀναφέρει',
  'corrected_text': 'ἀναφέρεσθαι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἀναχωμὲν',
  'corrected_text': 'ἀναχομένης',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἢ τε ἁμαρτία ἢ τε κατάρα, ὅσα',
  'corrected_text': 'ἥ τε ἁμαρτία καὶ ἡ κατάρα καὶ ὅσα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ὅτως δὲ',
  'corrected_text': 'ἔστω δὲ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἀγνωσίαν',
  'corrected_text': 'ἄγνοιαν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ὡς κεφαλὴ τοῦ',
  'corrected_text': 'ὡς κεφαλὴν τοῦ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἀναδίδωσι',
  'corrected_text': 'ἀναδέχεσθαι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'μὴ με θεῖ μὴ, ἵνα τὸ αὐτὸ με ἐγκαταλίπης;',
  'corrected_text': 'Θεέ με Θεέ με, ἵνα τί με ἐγκατέλιπες;',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ἀγαθὸν φιλανθρωπίαν',
  'corrected_text': 'ἄφατον φιλανθρωπίαν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.2',
  'original_text': 'ὡς ἑαυτὸ τὰ ἡμέτερα οἰκειώμενον',
  'corrected_text': 'ὡς ἑαυτοῦ τὰ ἡμέτερα οἰκειούμενον',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ἀγωνίζει',
  'corrected_text': 'ἀγωνίζεται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'Σικενσον',
  'corrected_text': 'Σούκενσον',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'αἱ τῷ μακαρίῳ',
  'corrected_text': 'αἳ τῷ μακαρίῳ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'δσα ἄλλα',
  'corrected_text': 'ὅσα ἄλλα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'συντρέχουσι δοκεῖ',
  'corrected_text': 'συντρέχειν δοκοῦσι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': "διευκρινεῖ (ἢ γὰρ οἱ δι' ἐναντίας ἀπὸ τῶν τοιούτων",
  'corrected_text': 'διευκρινεῖ (καὶ γὰρ οἱ δι’ ἐναντίας ἀπὸ τοιούτων',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ἀχροπόλεως',
  'corrected_text': 'ἀκροπόλεως',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'φροντιστὴν',
  'corrected_text': 'φρυάττονται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ἐπειτα',
  'corrected_text': 'ἔπειτα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ἀποσκευάζει',
  'corrected_text': 'ἀποσκευάζεται',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'τὸ μὲν ἄν',
  'corrected_text': 'τὸ μὲν οὖν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'Σικενσον ἐπιστολῆς χρήσων',
  'corrected_text': 'Σούκενσον ἐπιστολῆς χρῆσιν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'φύσεις ἀδιορίστους',
  'corrected_text': 'φύσεις ἀδιαιρέτους',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'μίαν προαβέυσιν',
  'corrected_text': 'μίαν πρεσβεύουσι',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'σισαρχωμένην',
  'corrected_text': 'σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'σισαρχωμένην',
  'corrected_text': 'σεσαρκωμένην',
  'occurrence': 1,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'οἱς ἀντιπορέων',
  'corrected_text': 'οἷς ἀνθυποφέρων',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'οἱ μὲν τὸ λόγον',
  'corrected_text': 'οἱ μίαν τοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ποιῶν',
  'corrected_text': 'ποιεῖν',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'προύποχάντα',
  'corrected_text': 'προϋποστάντα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'σώφες',
  'corrected_text': 'σὰρξ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'τῆς μυστήρια',
  'corrected_text': 'τῷ μυστηρίῳ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'πῶ γὰρ διὰ',
  'corrected_text': 'πῶς γὰρ ἔστι διὰ',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
  'original_text': 'ἢν ἢ ἀναληφθεῖσα',
  'corrected_text': 'ἦν ἡ ἀναληφθεῖσα',
  'occurrence': 0,
  'source_region': [0.225, 0.108, 0.579, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.5',
  'original_text': 'ἰσχυράτισο',
  'corrected_text': 'ἐσχημάτιστο',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.6',
  'original_text': "πῶν δ'",
  'corrected_text': 'πόθεν δ’',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.8',
  'original_text': 'εἶναι δὲ αὐτῆς τὸ εἶδος',
  'corrected_text': 'ἔστιν ἐξ αὐτῆς εὑρεῖν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.8',
  'original_text': 'διὰ τῶτο γὰρ ἡ',
  'corrected_text': 'διὰ τοῦτο γὰρ καὶ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.9',
  'original_text': 'Εὐτυχὲς',
  'corrected_text': 'Εὐτυχεῖ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.10',
  'original_text': 'συγχάοντι',
  'corrected_text': 'συγχέοντι',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.11',
  'original_text': 'ἀλλὰ ἡ',
  'corrected_text': 'ἀλλὰ καὶ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.12',
  'original_text': 'ἢ ψυχή, χῆμασι',
  'corrected_text': 'ἡ φωνή, σχήματι',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.13',
  'original_text': 'διὸ',
  'corrected_text': 'δύο',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.14',
  'original_text': 'ἀδιαίρετος',
  'corrected_text': 'ἀδιαιρέτως',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.14',
  'original_text': 'μὴν',
  'corrected_text': 'μὲν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 6},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.15',
  'original_text': 'μόντοι',
  'corrected_text': 'μέντοι',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.16',
  'original_text': 'κρύπτουσιν ἔνωσιν',
  'corrected_text': 'κηρύττειν ἕνωσιν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.17',
  'original_text': 'κοιλόγυος',
  'corrected_text': 'κακούργως',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.17',
  'original_text': 'Νεσώριος',
  'corrected_text': 'Νεστόριος',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.17',
  'original_text': 'τιμὴ ἡ',
  'corrected_text': 'τιμῇ καὶ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.18',
  'original_text': 'ἐπιτυχνώσασιν',
  'corrected_text': 'ἐπιτεχνάσμασιν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.19',
  'original_text': 'τῶτο ἡ ὁ Σείος',
  'corrected_text': 'τοῦτο καὶ ὁ θεῖος',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.19',
  'original_text': 'τὸ πέραν',
  'corrected_text': 'τὸ πέρας',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.20',
  'original_text': 'ἐπισολῆς',
  'corrected_text': 'ἐπιστολῆς',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.22',
  'original_text': 'αὐτὸ δὲ ὡς ἔγω νομίζω',
  'corrected_text': 'αὐτοὶ δὲ οὐχ οὕτω νοῦσι',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.23',
  'original_text': 'Νεσώρια κενωσωσίας',
  'corrected_text': 'Νεστορίῳ κενοφωνίας',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.24',
  'original_text': 'λαμβάνει',
  'corrected_text': 'λαμβάνεται',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.24',
  'original_text': 'ἰσχυρίᾳ',
  'corrected_text': 'ἰσοτιμίᾳ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.25',
  'original_text': 'τοβυλίᾳ',
  'corrected_text': 'τοβουλίᾳ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.26',
  'original_text': 'ἐν φῶ κατακύσας',
  'corrected_text': 'ἐν ᾧ κατῴκησεν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.27',
  'original_text': 'οὐδὲ',
  'corrected_text': 'οἶδε',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.28',
  'original_text': 'ὀρθοῦν τε καὶ ὀρθοδόξῃ φρονήσεως',
  'corrected_text': 'οἰκεῖόν τε καὶ ὀρθοδόξου φρονήματος',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.28',
  'original_text': 'διχλὴ',
  'corrected_text': 'διχῇ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.29',
  'original_text': 'τὰ ἀδιαίρετα λεγομένα',
  'corrected_text': 'ἀδιαιρέτου λεγομένου',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.30',
  'original_text': 'σισαρκωμένην',
  'corrected_text': 'σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.31',
  'original_text': 'Νεσώριον',
  'corrected_text': 'Νεστόριον',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.31',
  'original_text': 'ἀψαιρέτους',
  'corrected_text': 'ἀδιαιρέτους',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.32',
  'original_text': 'τῶτο τὸ φητὸν ὀρθῆς γίνετ',
  'corrected_text': 'τοῦτο τὸ ῥητὸν ὀρθῆς γίνεται',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.33',
  'original_text': "ἀπομερισθὲν δὲ κατ' ἄλλας",
  'corrected_text': 'ἀπομερίζεται δὲ κατ’ ἄλλους',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.35',
  'original_text': 'αὐτὴ',
  'corrected_text': 'αὕτη',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.35',
  'original_text': 'πληρῶσα',
  'corrected_text': 'πληροῦσα',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.36',
  'original_text': 'τῶν δόλων ἐκτίνει Νεσώριον',
  'corrected_text': 'τὸν δόλον ἐλαύνει Νεστορίῳ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.36',
  'original_text': 'συκοφάντας',
  'corrected_text': 'συκοφαντίας',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.37',
  'original_text': 'ἐσθεβείας καταργύνει',
  'corrected_text': 'εὐσεβείας καταισχύνει',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.37',
  'original_text': 'ἄν ἑκάτερα',
  'corrected_text': 'οὖν ἑκατέρα',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.38',
  'original_text': 'δήλον',
  'corrected_text': 'δῆλον',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.39',
  'original_text': 'τῷ λόγῳ',
  'corrected_text': 'τοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 3},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.40',
  'original_text': 'σισαρκωμένην',
  'corrected_text': 'σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 3},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.40',
  'original_text': 'ἀδιαίρετος',
  'corrected_text': 'ἀδιαιρέτους',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.41',
  'original_text': 'ἑκάτερα συμπληρωμένη',
  'corrected_text': 'ἑκατέρα συμπλεκομένη',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.41',
  'original_text': 'τῷ λόγῳ',
  'corrected_text': 'τοῦ λόγου',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 4},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.42',
  'original_text': 'φύσεις σισαρκωμένη τῇ',
  'corrected_text': 'φύσις σεσαρκωμένη τὴν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.42',
  'original_text': 'ἀπλῶς',
  'corrected_text': 'ἁπλῶς',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.44',
  'original_text': 'ἀσάφροτον',
  'corrected_text': 'ἀφύρτον',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.45',
  'original_text': 'οὐκὼν ἀπορρωθῆσιν φωνὴ Θαίρεας ἢ',
  'corrected_text': 'οὐκῶν ἀπομερισθεῖσα φωνὴ θατέρας ἡ',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.46',
  'original_text': 'φεισιῶς',
  'corrected_text': 'φιστικῶς',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 3,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.46',
  'original_text': 'ἄν',
  'corrected_text': 'ἂν',
  'occurrence': 0,
  'source_region': [0.578, 0.108, 0.93, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 3, printed page 268, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s280; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'εἰσεὶδὼς ἤκουσαν παραχῶν, ἢ',
  'corrected_text': 'εὐσεβῶς ἔχουσαν παραχών, καὶ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τῷ λόγῳ σαρκομένῃ',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τῷ λόγῳ σαρκομένῃ',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην',
  'occurrence': 1,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τῷ λόγῳ σαρκομένῃ',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην',
  'occurrence': 2,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἀπλῶς',
  'corrected_text': 'ἁπλῶς',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐξ ἀμορίων',
  'corrected_text': 'ἐξ ἀμφοτέρων',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ὥς ἂ συγχέει τὰ συνθέμενα περιποιεῖν',
  'corrected_text': 'ὥστε καὶ συγχύσει τὰ συνελθόντα περιπεσεῖν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'βούλεται',
  'corrected_text': 'βούλεσθαι',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τῷ πατρὸς',
  'corrected_text': 'τοῦ πατρὸς',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'καὶ ἐπόσαυσιν',
  'corrected_text': 'καθ’ ὑπόστασιν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ὡς ἂ τῷ Θεολόγῳ',
  'corrected_text': 'ὡς καὶ τῷ θεολόγῳ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'σαρξ ἐγένετο ἢ',
  'corrected_text': 'σὰρξ ἐγένετο καὶ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'διὰ πλάτος',
  'corrected_text': 'διὰ πλάτους',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἢ ἀπολογούμενος ὅπου',
  'corrected_text': 'καὶ ἀπολογησάμενος οὕτω',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἂ Κέριλλον ἐπαγγέλλει',
  'corrected_text': 'τὸν Κύριλλον ἐπαγγέλλεται',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'οὐ μὴν γὰρ',
  'corrected_text': 'εἰ μὲν γὰρ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'εἰπόντες τῷ λόγῳ φύσιν σαργήκαμεν',
  'corrected_text': 'εἰπόντες τοῦ λόγου φύσιν σεσιγήκαμεν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐνεργοῦντες τὸ σαρκομένον',
  'corrected_text': 'ἐπενεγκόντες τὸ σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': "ἀλλ' οὐδὲν ἴδω τὸν ἔχοντα",
  'corrected_text': 'ἀλλ’ οἷον ἔξω τιθέντες',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἢν αὐτοῖς τὴν παρὰ καὶ ἂν',
  'corrected_text': 'ἦν αὐτοῖς τάχα που καὶ οὐκ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'προσποιούμενος ἐρωτῶν',
  'corrected_text': 'προσποιουμένοις ἐρωτᾶν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τὸ τῆλεῖν',
  'corrected_text': 'τὸ τέλειον',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἠξίωσεν ἢ καὶ ἡμᾶς ὁσία',
  'corrected_text': 'ὑφέστηκεν ἡ καθ’ ἡμᾶς οὐσία',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τελειότης ἢ τῆς καὶ ἡμᾶς ὁσίας ἢ δηλώσεις εἰσχεύωμεν διὰ τὸ λέγειν',
  'corrected_text': 'τελειότης καὶ τῆς καθ’ ἡμᾶς οὐσίας ἡ δήλωσις εἰσκεκόμισται διὰ τοῦ λέγειν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'σαρκομένην, παντάπασι καλαμίνην ἡμῶν ἐαυτοῖς ὑποζῶντες',
  'corrected_text': 'σεσαρκωμένην, παυσάσθωσαν καλαμίνην ῥάβδον ἑαυτοῖς ὑποστήσαντες',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τὰς δύο φύσεις ἢ',
  'corrected_text': 'τὰς δύο φύσεις ἡ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'τῷ ἀδιαίρετον εἰσίγνυται ἐπισήμανσις',
  'corrected_text': 'τῷ ἀδιαιρέτῳ εἰσήνεγκεν ἐπισφίγγουσα',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐμβόῳ ὁ Κίριλλος',
  'corrected_text': 'ἐμβοᾷ ὁ Κύριλλος',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': "φαίνετ' ἄμηνος",
  'corrected_text': 'φαίνεται φάμενος',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'Χριστῷ ἀπλῶς',
  'corrected_text': 'Χριστοῦ ἁπλῶς',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἂν ἂν ἁλοίη',
  'corrected_text': 'οὐκ ἂν ἁλοίη',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'σῶς ἢν ψυχῇ σῶμα',
  'corrected_text': 'σὰρξ ἐψυχωμένη νοερῶς',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'πάλιν σώζει τῶν συνδρομούντων εἰς ἓν ὄνομα ἀδιαίρετον ἐκάτερον',
  'corrected_text': 'πάλιν σώζεσθαι τῶν συνδραμόντων εἰς ἕνωσιν ἀδιαιρέτως ἑκάτερον',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'δῆλον ἂν',
  'corrected_text': 'δῆλον οὖν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἂ πρὸς ἄλλον',
  'corrected_text': 'ἢ πρὸς ἄλλον',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἢ ὅστις',
  'corrected_text': 'ἢ ὄψις',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐπὶ τῇ δεσπότου',
  'corrected_text': 'ἐπὶ τοῦ δεσπότου',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'συνυφύσασαν',
  'corrected_text': 'συνεισάγουσαν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'σῶζω',
  'corrected_text': 'σώζεσθαι',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'συνδρομούντων εἰς ἓν ὄνομα',
  'corrected_text': 'συνδραμόντων εἰς ἕνωσιν',
  'occurrence': 1,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐκάτερον',
  'corrected_text': 'ἑκάτερον',
  'occurrence': 1,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'παρισχυθεῖν',
  'corrected_text': 'παρεισαχθείη',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐπὶ τῷ σωτῆρος Χριστῷ συνημένος χρηστῶν ἀδιαίρετος ἢ',
  'corrected_text': 'ἐπὶ τοῦ σωτῆρος Χριστοῦ σωζομένας κηρύττων ἀδιαιρέτως καὶ',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἢ τοῦτο φανερώτερον',
  'corrected_text': 'καὶ τοῦτο φανερώτερον',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'Σακίνουσον',
  'corrected_text': 'Σούκενσον',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'δευτέρα ποιεῖ',
  'corrected_text': 'δευτέρᾳ ποιεῖται',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἐρωτητέον',
  'corrected_text': 'ἑρμηνεύων',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ἢ μία φύσις',
  'corrected_text': 'ἡ μία φύσις',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'σαρκομένη,',
  'corrected_text': 'σεσαρκωμένη,',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'ὡς ἐστιν υἱὸς ὁ φύσει',
  'corrected_text': 'ὡς ἔστιν υἱὸς φύσει',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': "εἰκαὶ κατὰ πρόσληψιν σαρκὸς ἂν ἀνέχῃ ἀλλ' ἢν ψυχωμένης",
  'corrected_text': 'εἰ καὶ κατὰ πρόσληψιν σαρκὸς ἐκ ἀψύχου ἀλλ’ ἐψυχωμένης',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
  'original_text': 'προσῆλθεν',
  'corrected_text': 'προῆλθεν',
  'occurrence': 0,
  'source_region': [0.08, 0.108, 0.435, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, left body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.4',
  'original_text': 'ὡς ἂ διὰ τοῦτο μερισθῆσε)',
  'corrected_text': 'ὡς οὐ διὰ τοῦτο μερισθήσεται',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.5',
  'original_text': 'ἢ τινὸς',
  'corrected_text': 'ἢ υἱούς',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.5',
  'original_text': 'ἀλλὰ κ ὥσπ διαμετεῖ εἰς, προσέθηκεν πῶς ὁκ',
  'corrected_text': 'ἀλλὰ καὶ οὕτω διαμενεῖ εἷς, προστίθησι πῶς οὐκ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.6',
  'original_text': 'ἀπαρχος οὐδὲ ἐξω',
  'corrected_text': 'ἄσαρκος οὐδὲ ἔξω',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.7',
  'original_text': 'καθ’ ἕκαστον',
  'corrected_text': 'καθ’ ἕνωσιν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.8',
  'original_text': 'ἐπισηλῆ κ',
  'corrected_text': 'ἐπιστολῇ καὶ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.9',
  'original_text': 'εἰρίσκεται',
  'corrected_text': 'εὑρίσκεται',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.9',
  'original_text': 'Σιλήριον',
  'corrected_text': 'Σεβῆρον',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.11',
  'original_text': 'ὁκ ἀνέχονται, κακῶς τε κ',
  'corrected_text': 'οὐκ ἀνεχόμενοι, κακούργως τε καὶ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.12',
  'original_text': 'τάττοντι τὰς φύσεις αἱ τὴν διαφορὰν δηλᾶσαι',
  'corrected_text': 'τάττουσι τὰς φωνὰς αἳ τὴν διαφορὰν δηλοῦσι',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.13',
  'original_text': 'ἐπειτα',
  'corrected_text': 'ἔπειτα',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.13',
  'original_text': 'ἀναστέγοντες',
  'corrected_text': 'ἀνατρέποντες',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.14',
  'original_text': 'τῷ λόγῳ συναρκομένην',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 3},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.14',
  'original_text': 'ὁκ ὥσπ',
  'corrected_text': 'οὐχ οὕτω',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.15',
  'original_text': 'εἰσέρεια',
  'corrected_text': 'εὐσέβεια',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.15',
  'original_text': 'προοῦσα',
  'corrected_text': 'προθεῖσα',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.16',
  'original_text': 'εἴθους ἐρεξὴς',
  'corrected_text': 'εὐθὺς ἐφεξῆς',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.16',
  'original_text': 'σώζειν',
  'corrected_text': 'σώζεσθαι',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.17',
  'original_text': 'ἀδιαιρέτους ἕκαστον',
  'corrected_text': 'ἀδιαιρέτως ἑκάτερον',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 2},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.18',
  'original_text': 'ὁλὴχουσα τὴς δυσσεβείας',
  'corrected_text': 'ἐλέγχουσα τοὺς δυσσεβεῖς',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.20',
  'original_text': 'ἑκάστων',
  'corrected_text': 'ὑπόστασιν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 1},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.20',
  'original_text': 'φυλαττομένην',
  'corrected_text': 'φυλαττομένων',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.23',
  'original_text': 'χρηστέον',
  'corrected_text': 'κηρύττουσα',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.23',
  'original_text': 'τῷ λόγῳ συναρκομένην',
  'corrected_text': 'τοῦ λόγου σεσαρκωμένην',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 4},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.24',
  'original_text': 'τῷ πατρὸς προαιωνίῳ λόγῳ',
  'corrected_text': 'τοῦ πατρὸς προαιώνιον λόγον',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.25',
  'original_text': 'δογματίζειν',
  'corrected_text': 'δογματίζουσα',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.28',
  'original_text': 'φρονεῖσαν τε καὶ προέττονσαν',
  'corrected_text': 'φρονοῦσάν τε καὶ κηρύττουσαν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.29',
  'original_text': 'διὰ τε ἄλλων κ',
  'corrected_text': 'διά τε ἄλλων καὶ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.29',
  'original_text': 'τὴν ἐν ἁγίῳ Φιλαρετῷ',
  'corrected_text': 'τὸ ἐν ἁγίοις Φλαβιανοῦ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.30',
  'original_text': 'πεῖν ἀναγνοῦσιν',
  'corrected_text': 'πίστιν ἀναγνωσθεῖσαν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.30',
  'original_text': 'ἐπεκρίνωσεν',
  'corrected_text': 'ἐπεκύρωσεν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.32',
  'original_text': 'ἢν περὶ',
  'corrected_text': 'ἣν περὶ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.33',
  'original_text': 'Σαυτοῦ ὁ Λουκιανὸς ἐπέσπασε',
  'corrected_text': 'αὐτοῦ ὁ Δομετιανὸς ὑπετόπαζε',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.34',
  'original_text': 'εὐδιαίτητον',
  'corrected_text': 'ἐνδιάθετον',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.34',
  'original_text': 'οἰκειώδη',
  'corrected_text': 'οἰκειοῦσθαι',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.35',
  'original_text': 'προαίγν',
  'corrected_text': 'προάγειν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.35',
  'original_text': 'καὶ ὡς',
  'corrected_text': 'καὶ ὥστε',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.36',
  'original_text': 'τὰς ἄκρους ἐμμεχάνως',
  'corrected_text': 'τοὺς ἀκροατὰς εὐμηχάνως',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.38',
  'original_text': 'διαμάχων',
  'corrected_text': 'διαστάσεων',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.38',
  'original_text': 'ἐπέκρινας, ἄπερ',
  'corrected_text': 'ἐπιστείλας, ἅπερ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.39',
  'original_text': 'προλαβὼσι',
  'corrected_text': 'προλαβοῦσι',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.39',
  'original_text': 'διεξῆλθον',
  'corrected_text': 'διεξελήλυθε',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.39',
  'original_text': 'Σιμήν',
  'corrected_text': 'θερμὸν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.40',
  'original_text': 'Καλχηδόνι συνόδου πρόθυμον',
  'corrected_text': 'Χαλκηδόνα συνόδου πρόμαχον',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.41',
  'original_text': 'τῷ ἐν ἁγίῳ',
  'corrected_text': 'τῶν ἐν ἁγίοις',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.42',
  'original_text': 'παραστήσόμενος',
  'corrected_text': 'παραστησάμενος',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.43',
  'original_text': 'πέραν',
  'corrected_text': 'πέρας',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.43',
  'original_text': 'ἐπιθήσιν',
  'corrected_text': 'ἐπιτίθησιν',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.44',
  'original_text': 'Θεοπίσιος ἄνθρ κ',
  'corrected_text': 'θεσπέσιος ἀνὴρ καὶ',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0},
 {'page': 16,
  'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.45',
  'original_text': 'ἐπίγραφε',
  'corrected_text': 'ἐπιγράφει',
  'occurrence': 0,
  'source_region': [0.435, 0.108, 0.79, 0.708],
  'evidence': 'Manual inspection of the pinned Bekker volume 2 scan, physical page 16, printed page 281, right body '
              'column. The bounded word or phrase and its polytonic marks were read in the image and corroborated by '
              'the exact local002 section s293; surrounding unassessed text is not certified.',
  'digital_occurrence': 0}]


def observations():
    """Return independent exact occurrence records without filesystem access."""
    return deepcopy(_OBSERVATIONS)


def unresolved():
    """Return source/digital boundary readings deliberately left unselected."""
    return [
        {'page': 16, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.32',
         'original_text': 'ἑαυτὸν ὁκ εὐαγὲς',
         'digital_text': 'ἑαυτὸν ἐκ εὐαγὲς',
         'source_region': [.435, .50, .79, .57],
         'reason': 'The compact printed negative and following genitive are not securely resolved; the digital expansion is not adopted. The historical reading stays unchanged.'},
        {'page': 2, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0002.1',
         'original_text': 'τῷ ἐν ἁγίῳ',
         'digital_text': 'τὸ ἐν ἁγίοις',
         'source_region': [.05, .108, .415, .20],
         'reason': 'Only the independently legible plural ἁγίοις is corrected. The short article uses compact old-type marks and the digital τὸ is not adopted as a resolution of the historical τῷ.'},
        {'page': 3, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0003.3',
         'original_text': 'ἐκ ἀνθρώπων προύποχάντα',
         'digital_text': 'ἐκ ἄνθρωπον προϋποστάντα',
         'source_region': [.225, .55, .579, .708],
         'reason': 'The preposition or negative before ἄνθρωπον is not resolved from the compact printed ligature and differing digital reading. The separately legible προϋποστάντα is corrected; the remaining clause is not certified.'},
        {'page': 16, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
         'original_text': "ἀλλ' ἐνεργοῦντες τὸ σαρκομένον",
         'digital_text': 'ἐκ ἐπενεγκόντες τὸ σεσαρκωμένην',
         'source_region': [.08, .27, .435, .38],
         'reason': 'Only the legible internal words ἐπενεγκόντες τὸ σεσαρκωμένην are corrected. The preceding compact negative or connective is not selected from the differing digital reading.'},
        {'page': 16, 'locus': 'helladius_chrestomathia_photius_bekker_v2_0016.1',
         'original_text': 'ἀκὴν τὰς δύο φύσεις ἢ',
         'digital_text': 'ἐκεῖνον τὰς δύο φύσεις ἡ',
         'source_region': [.08, .36, .435, .42],
         'reason': 'The initial word is not securely resolved from the scan and is left unchanged. Only the unambiguous article after τὰς δύο φύσεις is corrected.'},
    ]
