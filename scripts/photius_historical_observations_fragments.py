"""Source-confirmed eligibility of retained halves of printed Greek words.

These observations change lexical eligibility only. They preserve every
displayed character and do not assemble words across passage boundaries.
"""
from copy import deepcopy

BATCH_ID = 'photius-historical-fragment-eligibility'
REVIEWED_AT = '2026-10-19T03:23:50Z'
SOURCE_SHA256 = 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'
SOURCE_LIBRARY_SHA256 = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
REGIONS = {
    '2-left': [.05, .108, .415, .708],
    '2-right': [.408, .108, .77, .708],
    '3-right': [.578, .108, .93, .708],
    '170-left': [.07, .108, .415, .685],
    '170-right': [.42, .108, .77, .685],
    '231-left-bottom': [.23, .60, .585, .70],
}
REVIEW_SCOPE = {
    'physical_pages': [2, 3, 170, 231],
    'qualification': 'Only the recorded source word divisions are reviewed for lexical eligibility. Their visible fragments and surrounding text are not replaced or joined.',
}

# Physical page, retained row suffix, exact visible fragment, incomplete edge,
# viewing region, full nonvoting comparison word (where the digital page is valid).
_SPECS = [
    (2, 22, 'παρα-', 'trailing', '2-left', 'παραφυάδας'),
    (2, 23, 'φυάδας', 'leading', '2-left', 'παραφυάδας'),
    (2, 25, 'κε-', 'trailing', '2-left', 'κεχρῆσθαι'),
    (2, 26, 'χρῆσθαι', 'leading', '2-left', 'κεχρῆσθαι'),
    (2, 50, 'δια-', 'trailing', '2-right', 'διασώζουσα'),
    (2, 51, 'σώζουσα', 'leading', '2-right', 'διασώζουσα'),
    (2, 58, 'δοξά-', 'trailing', '2-right', 'δοξάζουσιν'),
    (2, 59, 'ζουσιν', 'leading', '2-right', 'δοξάζουσιν'),
    (3, 24, 'ταυ-', 'trailing', '3-right', 'ταυτοβουλίᾳ'),
    (3, 25, 'τοβουλίᾳ', 'leading', '3-right', 'ταυτοβουλίᾳ'),
    (3, 45, 'σο-', 'trailing', '3-right', 'σοφιστικῶς'),
    (3, 46, 'φιστικῶς', 'leading', '3-right', 'σοφιστικῶς'),
    (170, 5, 'λεῖν', 'leading', '170-left', None),
    (170, 6, 'τὸς', 'leading', '170-left', None),
    (170, 16, 'τας', 'leading', '170-left', None),
    (170, 22, 'τέρων', 'leading', '170-left', None),
    (170, 41, 'μηλος', 'leading', '170-right', None),
    (231, 2, 'γνη-', 'trailing', '231-left-bottom', 'γνησίους'),
]

_DIVISIONS = {
    (2, 22): 'παρα-/φυάδας across retained rows 0002.22–23',
    (2, 23): 'παρα-/φυάδας across retained rows 0002.22–23',
    (2, 25): 'κε-/χρῆσθαι across retained rows 0002.25–26',
    (2, 26): 'κε-/χρῆσθαι across retained rows 0002.25–26',
    (2, 50): 'δια-/σώζουσα across retained rows 0002.50–51',
    (2, 51): 'δια-/σώζουσα across retained rows 0002.50–51',
    (2, 58): 'δοξά-/ζουσιν across retained rows 0002.58–59',
    (2, 59): 'δοξά-/ζουσιν across retained rows 0002.58–59',
    (3, 24): 'ταυ-/τοβουλίᾳ across retained rows 0003.24–25',
    (3, 25): 'ταυ-/τοβουλίᾳ across retained rows 0003.24–25',
    (3, 45): 'σο-/φιστικῶς across retained rows 0003.45–46',
    (3, 46): 'σο-/φιστικῶς across retained rows 0003.45–46',
    (170, 5): 'ἐγκα-/λεῖν across retained rows 0170.4–5',
    (170, 6): 'αὐ-/τὸς across retained rows 0170.5–6',
    (170, 16): 'τιμήσαν-/τας across retained rows 0170.15–16',
    (170, 22): 'ἀμφο-/τέρων across retained rows 0170.21–22',
    (170, 41): 'Εὔ-/μηλος across retained rows 0170.40–41',
    (231, 2): 'γνη-/σίους across retained rows 0231.2–3',
}


def observations():
    result = []
    for page, row, text, side, region, full_word in _SPECS:
        qualification = ('Manual inspection confirms the printed division ' + _DIVISIONS[page, row]
            + '. This exact visible fragment is an incomplete word and remains unchanged; only its lexical eligibility changes.')
        item = dict(page=page, locus=f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{row}',
            original_text=text, corrected_text=text, occurrence=0, projection_only=True,
            source_region=REGIONS[region], source_fragment={side: True, 'qualification': qualification},
            evidence=f'Manual inspection of the pinned Bekker volume II scan, physical page {page}, printed page {page+265}. ' + qualification,
            reviewed_at=REVIEWED_AT)
        if full_word:
            item['digital_context_text'] = full_word
        else:
            item['scan_only'] = True
            item['qualification'] = 'The mapped digital page repeats unrelated printed material. The source scan confirms this word division; no digital replacement or completion is selected.'
        result.append(item)
    return deepcopy(result)
