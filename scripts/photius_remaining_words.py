"""Two occurrence-specific editorial decisions with complete word boundaries.

The supplied edition is preferred explicitly; neither decision certifies the
unresolved Bekker ligatures. No general permission to expand uncertainty masks
or replace non-Greek originals is granted by this small source authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import compare_photius_local_edition as edition
import repair_photius_uncertainties as masks

REVIEWED_AT = '2026-10-21T23:02:38Z'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {
    'data/corpus_changes/photius-bekker-editorial-substitutions/compiled-review.json.gz':
        '76abb40a4759da8659bf8646fc80a9310c1c519adc6fb4a7ef3fe5b767fed633',
    'data/corpus_changes/photius-bekker-readings/source-scan.pdf':
        'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
}
SPECS = [
    {'locus': 'helladius_chrestomathia_photius_bekker_v2_0226.1',
     'segment_index': 9, 'identity_start': 372, 'identity_end': 376,
     'identity_text': '1469', 'start': 372, 'end': 376, 'original_text': '1469',
     'row_sha256': 'b05cab2402abf32b6ba5748ea8854eab8fd528342431e07c01b24ecc03d108d4',
     'inherited_record_sha256': 'e331136989f2a593024f20c0a80781d6683a26270a2fee59eef61155aacfbaef',
     'inherited_mask_sha256': '23e92bdb48d44adfd662ae221fd6420ce16fa434c159c0d55a1523478ddf89b3',
     'selection': (12913, 12914, 'λείπεσθαι'),
     'context_sha256': 'f9e283d07d31e392415854e6c98a5ae7e198faa6a0b44f088c111671cf533d8c',
     'scan': {'physical_page': 226, 'printed_page': 491,
              'region': [0.05, 0.105, 0.43, 0.765], 'max_side': 3600,
              'image_sha256': 'cf80b87d31a8e0af2f132a548a857f146eb3b9a9782b4e9c9fe6b5ee9a63b1ed',
              'observed_text': 'λείπε[σ?]θαι'},
     'rendering': {'allow_non_greek_original': True},
     'evidence': 'The directly inspected Bekker physical226 / printed491 authorial line places '
         'a Greek word between ταῦτα and τοῦ Δημοσθενικοῦ τύπου. The original1469 is its exact '
         'non-Greek OCR preimage, not a source reference number. The compact sigma-theta group '
         'remains unresolved in the scan observation. The supplied Henry491a paragraph uniquely '
         'contains λείπεσθαι at this same sentence position.',
     'qualification': 'Adopt the supplied edition’s complete Greek word as an explicit editorial '
         'preference. Retain the numeric OCR preimage, the tentative Bekker reading, and its '
         'unresolved sigma-theta qualification. This exception authorizes only this exact '
         'four-character non-Greek occurrence, never deletion of arbitrary numeric material.'},
    {'locus': 'helladius_chrestomathia_photius_bekker_v2_0233.1',
     'segment_index': 1, 'identity_start': 6, 'identity_end': 7,
     'identity_text': 'θ', 'start': 0, 'end': 11, 'original_text': 'Ἀνεγνώθησαν',
     'row_sha256': '8b749aa358adce6f375e18f65751f6da4c7fba1066f78163fe3788a289bfc166',
     'inherited_record_sha256': 'c19871fddeb3d1d97f17d68d52e6bce16c598a2549c795320bdbbc26107458ed',
     'inherited_mask_sha256': 'b9b9bb145e11a56245e71241f17644516f7390b060944257167c34f6dff05a80',
     'selection': (13080, 13081, 'Ἀνεγνώσθη'),
     'context_sha256': '37e1f41222f090c4870598766e9b2c01e4adff4efff1e85a263f6a17e5e23ffe',
     'scan': {'physical_page': 233, 'printed_page': 498,
              'region': [0.225, 0.105, 0.59, 0.72], 'max_side': 3600,
              'image_sha256': '73a68afd3074f06e6cab28c3acd49300956ffdcebec9f99c681757f677d7864a',
              'observed_text': 'Ἀνεγνώ[σθ/θ]ησαν'},
     'rendering': {},
     'evidence': 'Direct inspection of the Bekker physical233 / printed498 Hesychius reading '
         'announcement confirms that the disputed theta belongs inside the first complete '
         'word, followed by a visible plural ending. The compact sigma-theta versus theta '
         'distinction remains unresolved. The supplied Henry498a codex269 announcement instead '
         'reads the complete singular Ἀνεγνώσθη. Replacing only theta would incorrectly retain '
         'the incompatible verified suffix; the complete11-character word already lies within '
         'one inherited unresolved-source-reading mask.',
     'qualification': 'An explicit whole-word editorial preference for Henry’s singular, not '
         'a claim of agreement with Bekker’s visible plural ending or resolution of its compact '
         'glyph. The original one-character uncertainty identity, complete original word, '
         'scan observation, contrary endings, and every unrelated exclusion remain archived.'},
]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _identity(spec):
    return {'start': spec['identity_start'], 'end': spec['identity_end'],
            'original_text': spec['identity_text']}


def _check_scope(key, scope, spec, *, adjusted=False):
    row = scope['row']
    inherited = scope.get('inherited_record') if adjusted and key == _expanded_key() else scope['record']
    identity = _identity(spec)
    if (_digest(row) != spec['row_sha256'] or _digest(inherited) != spec['inherited_record_sha256']
            or row['locus'] != key[0] or inherited['segment_index'] != key[1]
            or inherited['locus'] != key[0] or inherited['original_text'] != spec['identity_text']
            or row['text'][identity['start']:identity['end']] != spec['identity_text']):
        raise ValueError('A reviewed word lost its exact baseline row or inherited uncertainty')
    a, b = (spec['start'], spec['end']) if adjusted else (identity['start'], identity['end'])
    if scope['start'] != a or scope['end'] != b or row['text'][spec['start']:spec['end']] != spec['original_text']:
        raise ValueError('A reviewed word lost its exact occurrence coordinates')
    leaves = masks._flatten(row['text'], scope['excluded_spans'])
    covering = [leaf for leaf in leaves if leaf['classification'] == 'unresolved-source-reading'
                and leaf['start'] <= spec['start'] and spec['end'] <= leaf['end']]
    if len(covering) != 1 or _digest(covering[0]) != spec['inherited_mask_sha256']:
        raise ValueError('The complete word must lie within its one exact inherited unresolved mask')
    if adjusted and key == _expanded_key():
        expected = deepcopy(inherited)
        expected['original_text'] = spec['original_text']
        if scope.get('identity_preimage') != identity or scope['record'] != expected:
            raise ValueError('A widened word changed its frozen identity or inherited segment')


def _expanded_key():
    return 'helladius_chrestomathia_photius_bekker_v2_0233.1', 1


def adjust_scopes(scopes):
    """Widen only the authored theta word, without mutating supplied records."""
    result = dict(scopes)
    specs = {(s['locus'], s['segment_index']): s for s in SPECS}
    for key, spec in specs.items():
        if key not in scopes:
            raise ValueError('The two reviewed word identities must both be present')
        _check_scope(key, scopes[key], spec,
                     adjusted=key == _expanded_key() and 'identity_preimage' in scopes[key])
    key = _expanded_key()
    spec, original = specs[key], scopes[key]
    if any(other != key and value['row']['locus'] == key[0]
           and value['start'] < spec['end'] and spec['start'] < value['end']
           for other, value in scopes.items()):
        raise ValueError('A whole-word review cannot borrow another held uncertainty')
    if 'identity_preimage' in original:
        return result
    changed = {**original, 'start': spec['start'], 'end': spec['end'],
               'inherited_record': deepcopy(original['record']),
               'identity_preimage': _identity(spec), 'record': deepcopy(original['record'])}
    changed['record']['original_text'] = spec['original_text']
    result[key] = changed
    return result


def _reading(spec, units):
    tokens = edition.tokenize(units)
    wanted = [edition.normalize(m.group()) for m in edition.WORD.finditer(spec['selection'][2])]
    positions = [i for i in range(len(tokens) - len(wanted) + 1)
                 if [t['key'] for t in tokens[i:i + len(wanted)]] == wanted]
    if len(positions) != 1 or not wanted:
        raise ValueError('The authored word must occur once in its exact source context')
    selected = tokens[positions[0]:positions[0] + len(wanted)]
    return [{'text': ' '.join(t['text'] for t in selected), 'source_id': 'tlg-photius-henry',
             'refs': [deepcopy(ref) for token in selected for ref in token['refs']],
             'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs'])} for token in selected],
             'role': 'alternative',
             'location_basis': 'Individually reviewed complete word in its exact pinned decoded-source context.'}]


def _record(spec, units):
    if not isinstance(units, list) or _digest(units) != spec['context_sha256']:
        raise ValueError('The exact reviewed word context changed')
    scan = deepcopy(spec['scan'])
    scan.update(source={'path': 'data/corpus_changes/photius-bekker-readings/source-scan.pdf',
                        'sha256': SOURCE_PINS['data/corpus_changes/photius-bekker-readings/source-scan.pdf']},
                reviewed_at=REVIEWED_AT, review_basis='direct-scan-inspection')
    return {'kind': 'source-reviewed-whole-word-editorial-preference', 'role': 'authorial-body',
            'original_text': spec['original_text'], 'identity_preimage': _identity(spec),
            'reviewed_extent': {'start': spec['start'], 'end': spec['end'], 'original_text': spec['original_text']},
            'original_row_sha256': spec['row_sha256'],
            'inherited_record_sha256': spec['inherited_record_sha256'],
            'inherited_mask_sha256': spec['inherited_mask_sha256'],
            'evidence': spec['evidence'], 'qualification': spec['qualification'],
            'readings': _reading(spec, units), 'rendering': deepcopy(spec['rendering']), 'scan': scan,
            'word_context': {'source_id': 'tlg-photius-henry', 'sha256': SOURCE_SHA256,
                'units': deepcopy(units), 'qualification': 'Exact source data nodes locating an editorial reading; not Bekker scan certification.'}}


def validate_record(key, record):
    """Reconstruct every field from pinned public context, without live HTML."""
    specs = {(s['locus'], s['segment_index']): s for s in SPECS}
    if key not in specs or not isinstance(record, dict):
        raise ValueError('Unknown reviewed whole-word identity')
    context = record.get('word_context')
    if not isinstance(context, dict):
        raise ValueError('A reviewed word needs its exact archived source context')
    expected = _record(specs[key], context.get('units'))
    if record != expected:
        raise ValueError('Recorded word decision differs from its complete source authority')
    return deepcopy(expected)


def review_words(html_raw, scopes):
    """Validate the supplied source and return the two exact editorial reviews."""
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied word comparison source changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    result = {}
    for spec in SPECS:
        key = spec['locus'], spec['segment_index']
        if key not in scopes:
            raise ValueError('A reviewed word lost its target scope')
        _check_scope(key, scopes[key], spec, adjusted=True)
        first, stop, _ = spec['selection']
        result[key] = _record(spec, parser.units[first:stop])
    return result


def validate_scan(document, crop_png):
    """Recreate the two source images using the pinned campaign rendering."""
    for spec in SPECS:
        scan = spec['scan']
        raw = crop_png(document, scan['physical_page'], scan['region'])
        if hashlib.sha256(raw).hexdigest() != scan['image_sha256']:
            raise ValueError('A reviewed whole-word source crop changed')
    return len(SPECS)
