"""Complete retained passage observations on Bekker printed page497.

Both body columns were compared in full, with enlarged inspection of the source
negations, ου ligatures, speech count, and the split ἐπαινεῖται. Contrary digital
readings and the original historical variants remain evidence, not hidden edits.
"""
from copy import deepcopy
import hashlib
import json

PAGE = 232
REVIEWED_AT = '2026-10-21T12:07:37Z'
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0232.'
LOCI = tuple(range(1, 7))
REGIONS = {'left': [.05, .105, .43, .725], 'right': [.41, .105, .81, .705]}
CHANGES = {
    1: [('ἡ τῶν λ τυραννὶς', "ἡ τῶν λ' τυραννὶς"),
        ('Ἐτεοβουτάδης ἠκροάσατο', 'Ἐτεοβουτάδης· ἠκροάσατο'),
        ('σύλληψιν καὶ οὕτως', 'σύλληψιν· καὶ οὕτως'),
        ('τὰς ἄλλας', 'τοὺς ἄλλους'),
        ('νομιζόμενος. διὸ', 'νομιζόμενος· διὸ'),
        ('νόμον εἰσφορᾶς διαφόρων ὧν', 'νόμων εἰσφορὰς διαφόρων· ὧν')],
    2: [('⟦συντυχών ∥ συντυχὼν⟧', 'συντυχών'),
        ('" ἔφη "', '" ἔφη, "'), ('χάριν ἐπαί', 'χάριν· ἐπαι-')],
    3: [('νεται γὰρ', 'νεῖται γὰρ')],
    4: [('⟦Ἐν ∥ Ἓν⟧', 'Ἓν'), ('⟦οὐκ ∥ ἐκ⟧', 'οὐκ')],
    6: [('λόγοι κά,', 'λόγοι κα᾽,'), ('⟦ἐκλογή ∥ ἐκλογὴ⟧', 'ἐκλογὴ')],
}
CONVENTION = (
    'Expand printed ου and καὶ ligatures. Preserve historical quotation and '
    'apostrophe shapes and paragraph whitespace. A printed numeric prime is '
    'represented by the existing Greek numeral apostrophe convention, including '
    'κα᾽ for the speech count. Join internal printed divisions only where both '
    'halves belong to the same retained passage; preserve passage-boundary '
    'fragments. Historical variant brackets are audit notation, not source '
    'letters; all original rows and contrary source readings remain archived.'
)


def _sha_row(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def _change(text, changes):
    for old, new in changes:
        if old not in text:
            raise ValueError(f'A completed page497 review span changed: {old!r}')
        text = text.replace(old, new)
    return text


def records(rows, document, crop_png, sections):
    """Compile exactly the six completed physical page232 passage reviews."""
    digital = sections['tlg4040-tlg001-local002-s509']
    result = []
    starts = [0, digital.index('Ξενοκράτει δέ ποτε'), digital.index('νεῖται γὰρ'),
              digital.index('Ἐν δὲ ἱμάτιον'), digital.index('Κατέλιπε δὲ'),
              digital.index('Ἀνεγνώσθησαν διαφόρων')]
    ends = [starts[1] - 1, starts[2], starts[3] - 1, starts[4] - 1, starts[5] - 1, len(digital)]
    for number in LOCI:
        row = rows[PREFIX + str(number)]
        text = row['text']
        corrected = _change(text, CHANGES.get(number, []))
        region = REGIONS['left' if number <= 2 else 'right']
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        segment = {'start': 0, 'end': len(text), 'original_text': text,
            'corrected_text': corrected, 'verification': 'verified',
            'review_basis': 'direct-scan-inspection', 'reviewed_at': REVIEWED_AT,
            'evidence': 'Direct comparison of the complete retained passage with '
                'Bekker physical page232 / printed page497, including unchanged '
                'words, punctuation, and line boundaries. Enlarged source regions '
                'were checked for τοὺς ἄλλους, νόμων εἰσφορὰς, the οὐκ ligatures, '
                'the divided ἐπαινεῖται, the numeric speech count, and the '
                'source spellings ἔχεν and αἰδῶς, which are preserved.',
            'transcription_convention': CONVENTION,
            'scan': {'physical_page': PAGE, 'region': region,
                'image_sha256': image_sha, 'observed_text': corrected},
            'readings': [{'kind': 'digital', 'section': 'tlg4040-tlg001-local002-s509',
                'start': starts[number - 1], 'end': ends[number - 1],
                'text': digital[starts[number - 1]:ends[number - 1]]}]}
        if number in {2, 3}:
            word, side = ('ἐπαι-', 'trailing') if number == 2 else ('νεῖται', 'leading')
            start = corrected.index(word)
            segment['fragments'] = [{'start': start, 'end': start + len(word),
                'text': word, 'side': side, 'qualification': 'The printed word '
                    'ἐπαινεῖται crosses this retained passage boundary. Keep '
                    'the two visible fragments separate and exclude them from '
                    'lexical counts without manufacturing a joined word.'}]
        result.append({'locus': row['locus'], 'original_row_sha256': _sha_row(row),
                       'status': 'reviewed-verified', 'segments': [segment]})
    return result
