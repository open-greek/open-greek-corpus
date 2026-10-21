"""Complete passage observations on Bekker printed page496.

The full retained text was compared with both physical columns, followed by
enlarged inspection of the compact ligatures and final lines. The uncertainty in
the last paragraph remains explicit. These observations do not admit a corpus
replacement or discard the contrary digital readings.
"""
from copy import deepcopy
import hashlib
import json

PAGE = 231
REVIEWED_AT = '2026-10-21T12:04:12Z'
PREFIX = 'helladius_chrestomathia_photius_bekker_v2_0231.'
LOCI = tuple(range(1, 8))
REGIONS = {'left': [.225, .105, .59, .70], 'right': [.57, .105, .95, .70],
           'bottom': [.58, .60, .95, .705]}
CHANGES = {
    1: [('ἄντος', 'οὗτος'), ('πότερος δεῖ', 'ποτέρους δεῖ'),
        ('χρηστοῦ δεσπότου“', 'χρηστοῦ δεσπότου.“'),
        ('ἀποφεύγει, καὶ', 'ἀποφεύγει. καὶ'),
        ('ἐκπεῖν', 'ἐξειπεῖν'), ('ἐξελθεῖν', 'ἐξειπεῖν')],
    2: [('φέρον δὲ αὐτοῦ δ᾽ αἱ ζ᾽ οἷς', 'φέρονται δὲ αὐτοῦ δ᾽ καὶ ξ᾽, οἷς')],
    4: [('εἰς Ἀθῆνας', 'εἰς Ἀθήνας'), ('⟦ὢν ∥ ὤν⟧', 'ὢν'),
        ('⟦παριών ∥ παριὼν⟧', 'παριὼν'), ('⟦Ἁρπάλα ∥ Ἁρπάλου⟧', 'Ἁρπάλου')],
}
CONVENTION = (
    'Expand the printed ου and καὶ ligatures, and join internal printed line '
    'divisions only when both halves belong to the same retained passage. '
    'Preserve the retained apostrophe shapes, quotation delimiters, and paragraph '
    'whitespace. Printed passage-boundary word fragments remain explicit. '
    'Historical variant delimiters are audit notation, not printed letters; the '
    'original row and every prior source reading remain frozen separately.'
)


def _sha_row(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def _change(text, changes):
    for old, new in changes:
        if old not in text:
            raise ValueError(f'A completed page496 review span changed: {old!r}')
        text = text.replace(old, new)
    return text


def _fragment(word, text, side):
    start = text.index(word) if side == 'leading' else text.rindex(word)
    return {'start': start, 'end': start + len(word), 'text': word, 'side': side,
        'qualification': 'The printed word continues across this retained passage boundary. '
            'Preserve the visible fragment and exclude it from lexical counts without joining passages.'}


def records(rows, document, crop_png, sections):
    """Compile only the seven explicitly completed physical page231 reviews."""
    digital_text = sections['tlg4040-tlg001-local002-s508']
    result = []
    for number in LOCI:
        row = rows[PREFIX + str(number)]
        text = row['text']
        region = REGIONS['left' if number < 3 else 'right' if number < 6 else 'bottom']
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        base = {'review_basis': 'direct-scan-inspection', 'reviewed_at': REVIEWED_AT,
            'evidence': 'Direct comparison of every word, punctuation mark, and retained '
                'passage boundary with Bekker physical page231 / printed page496. '
                'The full columns and enlarged regions around οὗτος, ποτέρους, '
                'ἐξειπεῖν, the numeric speech count, Ἁρπάλου, and the final '
                'historiographical clause were inspected; unchanged text was included.',
            'transcription_convention': CONVENTION}
        def segment(start, end, original, corrected, **extra):
            return {**deepcopy(base), 'start': start, 'end': end,
                'original_text': original, 'corrected_text': corrected,
                'verification': 'verified',
                'scan': {'physical_page': PAGE, 'region': region,
                    'image_sha256': image_sha, 'observed_text': corrected}, **extra}
        if number == 6:
            if text != '# ΑΥΚΟΥΡΓΟΥ':
                raise ValueError('The duplicate historical heading artifact changed')
            reviewed = segment(0, len(text), text, '')
            reviewed['evidence'] += ' The synthetic markdown heading has no '
            reviewed['evidence'] += ('independent printed body. The printed ΛΥΚΟΥΡΓΟΥ belongs '
                'to the beginning of retained passage7, where it is reviewed separately.')
            segments, status = [reviewed], 'reviewed-verified'
        elif number == 7:
            start = text.index('φέρε δὲ')
            uncertain_start = text.index(' μεμαθηκότες', start)
            uncertain_end = uncertain_start + len(' μεμαθηκότες')
            first = segment(0, start, text[:start], text[:start])
            known = segment(start, uncertain_start, text[start:uncertain_start],
                            'φέρεσθαι δὲ αὐτοῦ ἐξ ἱστορίας')
            uncertain = segment(uncertain_start, uncertain_end,
                text[uncertain_start:uncertain_end], text[uncertain_start:uncertain_end],
                verification='uncertain', uncertainty='The compact printed connective '
                    'before μεμαθήκαμεν is insufficiently distinct to certify. The source '
                    'resembles καὶ μεμαθήκαμεν; the digital reading ἴσμεν μεμαθήκαμεν '
                    'is retained as a contrary witness rather than substituted.')
            uncertain['scan']['observed_text'] = ' [καὶ?] μεμαθήκαμεν'
            final = segment(uncertain_end, len(text), text[uncertain_end:], '. οὗτος δὲ')
            segments, status = [first, known, uncertain, final], 'reviewed-with-uncertainty'
        else:
            corrected = _change(text, CHANGES.get(number, []))
            reviewed = segment(0, len(text), text, corrected)
            if number == 2:
                reviewed['fragments'] = [_fragment('γνη-', corrected, 'trailing')]
            elif number == 3:
                reviewed['fragments'] = [_fragment('σίους', corrected, 'leading')]
            segments, status = [reviewed], 'reviewed-verified'
        # Keep the exact digital counterpart, including differences from the
        # visually observed scan. These are recorded readings, not extra votes.
        if number == 7:
            low = digital_text.index('ΛΥΚΟΥΡΓΟΥ')
            known_start = digital_text.index('φέρεσθαι δὲ', low)
            uncertain_start = digital_text.index(' ἴσμεν μεμαθήκαμεν', known_start)
            uncertain_end = uncertain_start + len(' ἴσμεν μεμαθήκαμεν')
            for item, (low, high) in zip(segments, [(low, known_start),
                    (known_start, uncertain_start), (uncertain_start, uncertain_end),
                    (uncertain_end, len(digital_text))]):
                item['readings'] = [{'kind': 'digital', 'text': digital_text[low:high],
                    'section': 'tlg4040-tlg001-local002-s508', 'start': low, 'end': high}]
        elif number != 6:
            bounds = {
                1: (0, digital_text.index(' Ἀνεγνώσθησαν ΔΕΙΝΑΡΧΟΥ')),
                2: (digital_text.index('Ἀνεγνώσθησαν ΔΕΙΝΑΡΧΟΥ'), digital_text.index('γνησίους') + 3),
                3: (digital_text.index('γνησίους') + 3, digital_text.index(' Οὗτος υἱὸς')),
                4: (digital_text.index('Οὗτος υἱὸς'), digital_text.index(' Τῶν μὲν οὖν')),
                5: (digital_text.index('Τῶν μὲν οὖν'), digital_text.index(' ΛΥΚΟΥΡΓΟΥ')),
                7: (digital_text.index('ΛΥΚΟΥΡΓΟΥ'), len(digital_text)),
            }
            low, high = bounds[number]
            segments[0]['readings'] = [{'kind': 'digital', 'text': digital_text[low:high],
                'section': 'tlg4040-tlg001-local002-s508', 'start': low, 'end': high}]
        result.append({'locus': row['locus'], 'original_row_sha256': _sha_row(row),
                       'status': status, 'segments': segments})
    return result
