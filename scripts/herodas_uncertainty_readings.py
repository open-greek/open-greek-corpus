"""Occurrence-specific review of every archived Herodas source uncertainty.

Decisions use the pinned PDF and its original color captures, not grammatical
normalization. Original color images are the same physical scan, not another
textual witness. Printed critical damage remains outside lexical admission.
"""
from __future__ import annotations

SOURCE_READINGS_SHA256 = '427509dc2021771b3b5f43047607c96f7cfbfc682462e9e3f6a6a41c3ecfcbdf'
SOURCE_PDF_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
SOURCE_ARCHIVE_SHA256 = "a2226e05c486682e2214513156754b105dd918eb030d98521bb0be5bb7e589ed"
REVIEWED_AT = "2026-10-22T19:12:30+00:00"
SOURCE_IMAGE_SHA256 = {78: '9647bd4c341b83f9698fc447f0b582889cf578436e40a4c5f52ce5af0dcd6a5c', 134: '413bc6c56da2503198d99b4b2c461933e7f14d8a058ba17d3d2315ff6a460253', 136: '4b14f9bc0a00e1823656704d4d31c7361da961c1d6b60a9b9878e8beca84930c', 138: '2d60371acf79425f5ad80fd0ab1d1a7ffe2f16b8b20110575abc102beeb3f2bb', 184: '29a3b1f4caba5e9ca45870abffd603a51bd9ec274fc6a532b1156912507f7cd6', 186: 'eee582023abf0be42859d3a7d9fe4d856ce32e1ae6d7b995a131445420fc84e1', 242: '64bd0a65caa45ce7541e1a91fe69439f71e74c20426bdf2fba7901332b0f22dd', 392: '1b62af2352a16723c7808899fff82646b9260262d236e22f7aea9be6d91292bc', 394: 'd2e05a3a3ee9fbfcad5c436f776c160e0e6911647cba41cc4ad093aaaa7fe9f6', 396: '3b15e12111f52752cdacbb559c47544eaa48068b68168448a6e0a0c0e5a53e9b', 440: 'c68b953056af1075de70a97a54e5d10cd4629d3a27663f065ae5316058616693', 442: '02c2c0b3074923c0d75d9103b5e7e709b7235e7b66fa19a509de4c5cb49688e8', 444: 'cd0e4b4b1032b9095244c562ede90535de19c85c02edc3028afb506ac0ef8bb2'}

def _decision(page, index, source_range, original, corrected, disposition, alternatives, observation):
    return {"scan_page": page, "uncertainty_index": index,
        "source_char_range": source_range, "original_text": original,
        "corrected_text": corrected, "disposition": disposition,
        "remaining_alternatives": alternatives,
        "reviewed_at": REVIEWED_AT,
        "evidence": (f"Manual inspection of Headlam–Knox 1922, PDF page {page}, "
            f"printed page {page - 70}; pinned PDF SHA256 {SOURCE_PDF_SHA256}. "
            f"Original native color capture data/corpus_changes/herodas-reading-sources/page-{page:04d}.jp2 "
            f"has SHA256 {SOURCE_IMAGE_SHA256[page]}; original archive SHA256 {SOURCE_ARCHIVE_SHA256}. "
            "Focused native-image crops were compared at enlarged display scale. " + observation)}


DECISIONS = [
    _decision(78, 0, [371, 375], 'ὦνα’', 'ὤνα’', 'resolved', [], 'The original color capture separates the right-facing psili and rising acute stroke over omega; there is no circumflex arch. The final elision apostrophe is printed.'),
    _decision(78, 1, [261, 265], 'ἁδρῷ', 'ἁδρῷ', 'resolved', [], 'Initial alpha has the left-facing rough-breathing mark, opening to the right; the rho, omega circumflex, and iota subscript are distinct.'),
    _decision(134, 0, [1188, 1192], 'ᾤκει', 'ᾤκει', 'resolved', [], 'Initial omega has a separate iota subscript and a combined right-facing psili plus rising acute stroke above it; the breathing is present, not an unmarked omega.'),
    _decision(136, 0, [675, 680], 'ἕκητ’', 'ἕκητ’', 'resolved', [], 'The color crop separates the rough breathing opening to the right from the rising acute above initial epsilon. The final elision mark is printed.'),
    _decision(138, 0, [80, 90], 'κὠσκλήπιος', 'κὡσκλήπιος', 'resolved', [], 'The omega after kappa has the rough-breathing curve opening to the right. The acute remains on eta; no normalization of the printed name is made.'),
    _decision(184, 0, [444, 451], 'ἱκετεύω', 'ἱκετεύω', 'printed-damage', [], 'The initial iota has a rough breathing opening to the right. The entire word is between the printed cruces beginning before μὴ μὴ and ending after Λαμπρίσκε; it remains critically excluded.'),
    _decision(186, 0, [91, 97], 'Μοῦσας', 'Μούσας', 'resolved', [], 'Above upsilon there is one rising acute stroke, not a circumflex arch. The rest of the printed word is clear.'),
    _decision(242, 0, [512, 520], 'ἁμαρτίης', 'ἁμαρτίης', 'printed-damage', [], 'Initial alpha has a rough-breathing curve opening to the right. The word follows the printed opening crux and belongs to the obelized phrase ending after ’στί; recognizing the glyph does not remove that critical exclusion.'),
    _decision(392, 0, [28, 34], 'ἀνδάνῃ', 'ἁνδάνῃ', 'resolved', [], 'Initial alpha bears a rough-breathing curve opening to the right; the acute is separately printed on the following accented alpha.'),
    _decision(392, 1, [440, 446], 'ἔφηβοι', 'ἔφηβοι', 'resolved', [], 'The psili and rising acute are both printed above the initial epsilon. No accent appears over eta; the accent is not moved according to a dictionary form.'),
    _decision(392, 2, [755, 757], 'οὖ', 'οὔ', 'resolved', [], 'The original color capture shows psili plus a rising acute stroke over upsilon, matching the acute combination on the nearby printed first-vowel accents; no circumflex arch is present.'),
    _decision(392, 3, [923, 927], 'Ἑρμῆ', 'Ἑρμῆ', 'resolved', [], 'A rough-breathing curve opening to the right is printed before the capital epsilon; eta retains its visible circumflex.'),
    _decision(394, 0, [309, 320], 'κὑποδημάτων', 'κὑποδημάτων', 'resolved', [], 'The breathing above upsilon after kappa is the curve opening to the right, with no adjoining accent; the acute remains over alpha later in the word.'),
    _decision(394, 1, [542, 544], 'οὔ', 'οὔ', 'resolved', [], 'The mark above upsilon has a distinct psili on the left and a rising acute stroke on the right. Both components are visible in the native color capture.'),
    _decision(394, 2, [630, 633], 'εἷς', 'εἲς', 'resolved', [], 'The mark above iota consists of a smooth-breathing hook opening to the left and a separate stroke descending to the right. Native-color controls on this same page distinguish the ascending acute in οὔ at approximately PDF x79/y313 and the detached circumflex arch in οὖν at x105/y207 from this grave at x159/y337. The unusual printed accent is retained without grammatical emendation.'),
    _decision(396, 0, [21, 22], 'ἡ', 'ἦ', 'resolved', [], 'The native color capture separates the smooth-breathing hook opening to the left below a circumflex arch. The arch and the breathing are distinct; the sign is not a simple rough breathing or a grave. The adjacent upsilon has its own rough breathing and circumflex.'),
    _decision(396, 1, [250, 257], 'κἠμέρην', 'κἡμέρην', 'resolved', [], 'The eta after kappa has a rough-breathing curve opening to the right; the later acute over epsilon is separate.'),
    _decision(396, 2, [364, 367], 'τῆς', 'τῇς', 'resolved', [], 'The original color capture shows a separate short curled iota-subscript stroke to the left of the eta descender, matching the independently visible subscript under nearby προσθῇς. The circumflex above eta remains.'),
    _decision(396, 3, [368, 375], 'καλῆσιν', 'καλῇσιν', 'resolved', [], 'Below eta there are two distinct strokes: a short curled iota subscript on the left and the longer eta descender on the right. The color capture distinguishes these where the PDF rendering merged them.'),
    _decision(396, 4, [271, 274], 'ὧδε', 'ὧδε', 'resolved', [], 'The breathing beneath the omega circumflex opens to the right, identifying the printed rough breathing. This is the occurrence after φέρ’.'),
    _decision(396, 5, [784, 787], 'ὧδε', 'ὧδε', 'resolved', [], 'The breathing beneath the omega circumflex opens to the right, identifying the printed rough breathing. This is the occurrence after δουλίδ’.'),
    _decision(396, 6, [651, 652], 'ἡ', 'ἡ', 'resolved', [], 'The eta before μέζον bears only the rough-breathing curve opening to the right; no separate grave or circumflex is printed. The unusual printed reading is retained without grammatical emendation.'),
    _decision(396, 7, [722, 723], 'ἡ', 'ἢ', 'resolved', [], 'The eta before σαμβαλίσκων has a right-facing psili and a separate descending grave stroke. It is not the unaccented rough-breathed article.'),
    _decision(396, 8, [736, 737], 'ἡ', 'ἢ', 'resolved', [], 'The eta before ἃ has the same psili-plus-grave combination as the preceding disjunction. The following alpha has a separately oriented rough breathing.'),
    _decision(440, 0, [76, 77], 'ἡ', 'ἢ', 'resolved', [], 'Above the eta beginning the question, a right-facing psili is followed by a descending grave stroke; both are distinct in the native color image.'),
    _decision(440, 1, [835, 839], 'κἠγὼ', 'κἠγὼ', 'printed-damage', [], 'The eta after kappa bears a smooth-breathing curve opening to the left. This occurrence remains inside the square-bracket range opened at VIII.18 on this page and closed by the double bracket on PDF442.'),
    _decision(442, 0, [30, 37], 'ἁρπαγὴν', 'ἁρπαγὴν', 'printed-damage', [], 'Initial alpha has a rough breathing opening to the right. The word is inside the nested printed square brackets, themselves inside the range inherited from PDF440; both close at the printed double bracket after ἀγωνιστής.'),
    _decision(442, 1, [181, 189], 'ἠμφίεστ’', 'ἠμφίεστ’', 'resolved', [], 'The initial eta has the smooth-breathing curve opening to the left; the acute is separately printed above iota later in the word. The terminal apostrophe is printed.'),
    _decision(442, 2, [436, 442], 'ὀρθρου', 'ὄρθρου', 'resolved', [], 'The psili and rising acute appear together over the initial omicron. The final upsilon has no accent, excluding a final-syllable circumflex reading.'),
    _decision(442, 3, [815, 819], 'κἠγὼ', 'κἠγὼ', 'resolved', [], 'The breathing on eta after kappa opens to the left; the grave remains on omega. This occurs after the preceding square-bracket ranges have closed.'),
    _decision(442, 4, [869, 878], 'κἠλάλαξαν', 'κἠλάλαξαν', 'resolved', [], 'The eta after kappa has the smooth-breathing curve opening to the left; the acute over alpha is separately printed.'),
    _decision(442, 5, [900, 906], 'ἁπαλῶς', 'ἁπαλῶς', 'resolved', [], 'The alpha has the rough-breathing curve opening to the right. Omega retains the distinct circumflex.'),
    _decision(442, 6, [972, 973], 'ἐ', 'ἐ', 'printed-damage', [], 'VIII.49 prints only this epsilon after οἱ δ’ and then seven spaced loss dots. The letter is not a complete lexical word, and the printed loss is not filled.'),
    _decision(442, 7, [988, 999], 'γρυπ(άνιος)', 'γρυπ(άνιος)', 'printed-damage', [], 'VIII.50 literally prints γρυπ followed by (άνιος), with both parentheses present, then six spaced loss dots. These are printed partial-word/editorial marks, not OCR insertions or a complete unmarked attestation.'),
    _decision(442, 8, [1012, 1021], 'ῥυπ(αρὸς)', 'ῥυπ(αρὸς)', 'printed-damage', [], 'VIII.51 literally prints ῥυπ followed by (αρὸς), with both parentheses present, then seven spaced loss dots. The parenthesized completion remains critically excluded.'),
    _decision(442, 9, [1036, 1038], 'τ(', 'τ(', 'printed-damage', [], 'VIII.52 literally prints tau and an opening parenthesis, followed by eight spaced loss dots. The parenthesis is visible in the original color capture; no missing word or closing parenthesis is supplied.'),
    _decision(442, 10, [1055, 1057], 'τ(', 'τ(', 'printed-damage', [], 'VIII.53 independently prints the second tau and opening parenthesis, followed by eight spaced loss dots. This is a separate damaged occurrence, not a duplicated OCR reading.'),
    _decision(444, 0, [91, 95], 'ἁγνά', 'ἁγνά', 'resolved', [], 'The first alpha bears a rough-breathing curve opening to the right; the final alpha bears a separate acute. The reading is not chosen from expected grammar.'),
    _decision(444, 1, [169, 173], 'κἠγὼ', 'κἠγὼ', 'resolved', [], 'The eta after kappa bears a smooth-breathing curve opening to the left; the grave is separately printed on omega.'),
    _decision(444, 2, [373, 376], 'ὧδε', 'ὧδε', 'printed-damage', [], 'The omega has a rough breathing opening to the right beneath its circumflex. This first occurrence after δὸς lies within the printed range opened before διαχρῆσθαι and closed after κρίνω·.'),
    _decision(444, 3, [385, 388], 'ὧδ’', 'ὧδ’', 'printed-damage', [], 'The omega has a rough breathing opening to the right beneath its circumflex, and the final elision apostrophe is printed. This occurrence also lies inside the range ending after κρίνω·.'),
    _decision(444, 4, [624, 627], 'ὧδε', 'ὧδε', 'resolved', [], 'The omega has a rough breathing opening to the right beneath its circumflex. This later occurrence before γοῦν is outside the closed square-bracket ranges.'),
    _decision(444, 5, [716, 718], 'κἠ', 'κἠ', 'resolved', [], 'The eta after kappa has a smooth-breathing curve opening to the left; no accent is added. The following τῷ is a separate printed word.'),
]


# A neighboring source error was visible in the same native-image comparison.
# Keep it separate from the exhaustive list of archived uncertainty occurrences.
EXTRAS = [
    {key: value for key, value in _decision(
        396, None, [23, 27], 'ὑμῖν', 'ὗμιν', 'resolved', [],
        'The initial upsilon has a rough-breathing curve opening to the right '
        'below a distinct circumflex arch. The following iota has no accent. '
        'The archived reading incorrectly placed the circumflex over iota.'
    ).items() if key != 'uncertainty_index'},
]
