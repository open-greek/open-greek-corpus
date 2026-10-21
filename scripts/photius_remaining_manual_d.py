"""Four individually located readings whose broad automatic intervals tied.

These choices replace only the held occurrence. The surrounding verified text
and every previously recorded contrary reading remain unchanged.
"""
from copy import deepcopy
import hashlib
import json
import compare_photius_local_edition as edition

REVIEWED_AT = '2026-10-21T23:10:13Z'
SOURCE_SHA256 = '8ffaad0d30bdd87e87b9e24f55495a6b56d64e91591c1e393e4d2e82dd5b6daa'
SOURCE_PINS = {}
SPECS = [{'locus': 'helladius_chrestomathia_photius_bekker_v2_0094.8',
  'segment_index': 11,
  'start': 458,
  'end': 466,
  'original_text': 'βεβίαται',
  'row_sha256': '842145058b252edb082a31ee6bf64c04938ba6f66d3472337732ae1ce7937fa8',
  'inherited_record_sha256': '2f5d4bc18f0b107dd749489cfed97fe90b61fbf1d36962eab1680100523822ba',
  'selection': (9043, 9045, 'βεβίασται'),
  'context_sha256': 'dc9291c737c3719858cddcebac12998b62b1884b26c7fa24bf0fbcdd2ad1da6b',
  'evidence': 'The sentence places this verb after μητὴρ εἰς μῖξιν ἀθέμιτον παιδὸς and before the '
              'new address Ἀλλ’ ὦ. The longer tied interval incorrectly includes the following '
              'sentence. Select only the verb, retaining the unresolved Bekker ending as contrary '
              'evidence.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0246.40',
  'segment_index': 1,
  'start': 14,
  'end': 19,
  'original_text': 'μόχον',
  'row_sha256': '91f228a6c93785f3ea8448b0da0540c273d4ca495017d3ac568a5b8f08e9689c',
  'inherited_record_sha256': 'dec024cf67601b7b66e76f21763909fbd81383dab50e30cd6daee49ac03a2414',
  'selection': (13463, 13465, 'μόσχον'),
  'context_sha256': '1838563567422d4cdfac05c1f5452b642f55927bea55b607cbb1875f5235a172',
  'evidence': 'The preceding retained passage ends within ἀνέδειξε; the current passage continues '
              'δειξε· σὺ τὸν and then names the calf before ἐπὶ τῆς φάτνης ἔθρεψας. The longer '
              'tied interval repeats text already present before this occurrence. Select only '
              'μόσχον.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0265.3',
  'segment_index': 9,
  'start': 1031,
  'end': 1037,
  'original_text': 'ὀξύνει',
  'row_sha256': '512b3e9c4cfe748163f34250d42bb0fa10e0ab9400130263346f8de1275c125f',
  'inherited_record_sha256': '216b6163a2bb3470c784d958966419c133d91b41dcadcf37b1e22297ce1d44ff',
  'selection': (13996, 13998, 'ὀξύνεται'),
  'context_sha256': '552cad6b9160df89dfa93505d1e9ba9162efb3671583be61a174a045f1bbe164',
  'evidence': 'The contrast is καὶ τὰ μὲν ὀξύνεται, τὸ δὲ περισπᾶται before the separate quantity '
              'contrast. The longer tied interval includes verified intervening text and another '
              'held verb. Select only the accentuation verb.'},
 {'locus': 'helladius_chrestomathia_photius_bekker_v2_0265.3',
  'segment_index': 13,
  'start': 1068,
  'end': 1076,
  'original_text': 'βραχύνει',
  'row_sha256': '512b3e9c4cfe748163f34250d42bb0fa10e0ab9400130263346f8de1275c125f',
  'inherited_record_sha256': '916ef1556e997b550eb45c85f5bd66cf705e24db0113f1f4e77a180ceee7bf2b',
  'selection': (13996, 13998, 'βραχύνεται'),
  'context_sha256': '552cad6b9160df89dfa93505d1e9ba9162efb3671583be61a174a045f1bbe164',
  'evidence': 'The separate quantity contrast is καὶ τὰ μὲν βραχύνεται, τὸ δὲ μακρόν ἐστι φύσει '
              'after the accentuation contrast. The longer tied interval repeats the other held '
              'verb and verified intervening text. Select only the quantity verb.'}]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def _record(spec, units):
    if not isinstance(units, list) or _digest(units) != spec['context_sha256']:
        raise ValueError('The individually reviewed tied-reading context changed')
    tokens = edition.tokenize(units)
    wanted = [edition.normalize(m.group()) for m in edition.WORD.finditer(spec['selection'][2])]
    positions = [i for i in range(len(tokens)-len(wanted)+1)
                 if [t['key'] for t in tokens[i:i+len(wanted)]] == wanted]
    if len(positions) != 1 or not wanted:
        raise ValueError('The reviewed reading must occur exactly once in its source context')
    selected = tokens[positions[0]:positions[0]+len(wanted)]
    reading = {'text': ' '.join(t['text'] for t in selected), 'source_id': 'tlg-photius-henry',
        'refs': [deepcopy(ref) for token in selected for ref in token['refs']],
        'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs'])} for token in selected],
        'role': 'alternative', 'location_basis': 'Individually reviewed sentence position in the pinned source context.'}
    return {'kind': 'individually-reviewed-tied-reading', 'role': 'authorial-body',
        'reviewed_at': REVIEWED_AT, 'original_text': spec['original_text'],
        'original_row_sha256': spec['row_sha256'],
        'inherited_record_sha256': spec['inherited_record_sha256'],
        'evidence': spec['evidence'], 'readings': [reading], 'rendering': {},
        'manual_context': {'source_id': 'tlg-photius-henry', 'sha256': SOURCE_SHA256,
            'units': deepcopy(units), 'qualification': 'Editorial preference; no claim of Bekker scan certification.'}}


def validate_record(key, record):
    specs = {(s['locus'], s['segment_index']): s for s in SPECS}
    if key not in specs or not isinstance(record, dict):
        raise ValueError('Unknown individually reviewed tied-reading identity')
    context = record.get('manual_context')
    if not isinstance(context, dict):
        raise ValueError('The tied-reading review needs its exact source context')
    expected = _record(specs[key], context.get('units'))
    if record != expected:
        raise ValueError('The tied-reading review differs from its complete authority')
    return deepcopy(expected)


def review_remaining(html_raw, scopes):
    if hashlib.sha256(html_raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('The supplied tied-reading source changed')
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    result = {}
    for spec in SPECS:
        key = spec['locus'], spec['segment_index']
        if key not in scopes:
            raise ValueError('The reviewed tied-reading occurrence is missing')
        target = scopes[key]
        if (target['start'] != spec['start'] or target['end'] != spec['end']
            or target['row']['text'][target['start']:target['end']] != spec['original_text']
            or _digest(target['row']) != spec['row_sha256']
            or _digest(target['record']) != spec['inherited_record_sha256']):
            raise ValueError('The reviewed tied reading lost its exact baseline occurrence')
        first, stop, _ = spec['selection']
        result[key] = _record(spec, parser.units[first:stop])
    return result
