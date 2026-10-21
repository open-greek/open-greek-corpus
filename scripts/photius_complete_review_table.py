"""Compile explicitly authored passage readings into the strict review schema.

This helper does not read or align text for a reviewer. Its input consists only
of enumerated direct source observations; omitted passages remain unreviewed.
Pin this file together with each authored source table using it.
"""
from copy import deepcopy
import hashlib
import json
import re


def compile_table(rows, document, crop_png, sections, *, page, reviewed_at,
                  text, regions, digital_starts, uncertainties=None, fragments=None,
                  convention=None, evidence=None, roles=None):
    """Compile literal source observations, bounded alternatives, and exclusions."""
    uncertainties, fragments = uncertainties or {}, fragments or {}
    if any(set(mapping) - set(text) for mapping in (uncertainties, fragments, roles or {})):
        raise ValueError('Observation qualifications cannot name an unenumerated passage')
    section = f'tlg4040-tlg001-local002-s{page + 277}'
    digital = sections[section]
    starts = {}
    previous = -1
    for number, needle in digital_starts.items():
        if needle is None:
            starts[number] = None
            continue
        offset = needle if type(needle) is int else digital.index(needle, previous + 1)
        if not previous < offset < len(digital):
            raise ValueError('Reviewed digital windows must be explicit and ordered')
        starts[number], previous = offset, offset
    if set(text) != set(starts) or set(text) != set(regions):
        raise ValueError('Every enumerated source observation requires its exact region and digital window')
    counterparts = [(number, start) for number, start in starts.items() if start is not None]
    ends = {number: after for (number, _), (_, after) in zip(counterparts, counterparts[1:])}
    result = []
    for number, observed in text.items():
        row = rows[f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{number}']
        original = row['text']
        low = starts[number] if starts[number] is not None else 0
        high = ends.get(number, len(digital)) if starts[number] is not None else 0
        region = regions[number]
        image_sha = hashlib.sha256(crop_png(document, page, region)).hexdigest()
        base = {'review_basis': 'direct-scan-inspection', 'reviewed_at': reviewed_at,
            'evidence': (evidence.get(number) if isinstance(evidence, dict) else evidence) or (f'Every retained word and unchanged span was '
                f'directly compared with Bekker physical page {page} / printed '
                f'page {page + 265}. Both body columns and enlarged strips were '
                'inspected. The digital witness is separately retained, including contrary readings.'),
            'transcription_convention': convention or ('Expand directly identified ου, στ, '
                'καὶ and γὰρ type. Preserve unresolved type as explicit uncertainty. '
                'Join internal line divisions only within a retained passage; '
                'preserve boundary fragments. Distinguish marginal references '
                'and line numbers from body text. Keep declared quotation delimiters.')}
        def segment(start, end, corrected, **extra):
            if re.search(r'\{u\d+\}', corrected):
                raise ValueError('An authored uncertainty placeholder has no explicit source record')
            return {**deepcopy(base), 'start': start, 'end': end,
                'original_text': original[start:end], 'corrected_text': corrected,
                'verification': 'verified', 'scan': {'physical_page': page,
                    'region': region, 'image_sha256': image_sha, 'observed_text': corrected},
                'text_role': (roles or {}).get(number, 'authorial-body'), **extra}
        def reading(item, start, end):
            if start < end:
                item['readings'] = [{'kind': 'digital', 'section': section,
                    'start': start, 'end': end, 'text': digital[start:end]}]
        cursor, dcursor, tail, segments = 0, low, observed, []
        for index, (old, scan, dword, reason) in enumerate(uncertainties.get(number, [])):
            if isinstance(old, dict):
                start, old = old['start'], old['text']
                if type(start) is not int or original[start:start + len(old)] != old or start < cursor:
                    raise ValueError('An authored exact uncertainty offset changed')
            else:
                positions = list(re.finditer(r'(?<!\w)' + re.escape(old) + r'(?!\w)', original))
                if len(positions) != 1 or positions[0].start() < cursor:
                    raise ValueError('An authored original uncertainty changed or became ambiguous')
                start = positions[0].start()
            before, tail = tail.split('{u' + str(index) + '}')
            if isinstance(dword, dict):
                dstart, dword = dword['start'], dword['text']
                if (type(dstart) is not int or not dcursor <= dstart < high
                        or dstart + len(dword) > high or digital[dstart:dstart + len(dword)] != dword):
                    raise ValueError('An authored exact digital uncertainty offset changed')
            else:
                dstart = digital.index(dword, dcursor, high) if dword else dcursor
            if start > cursor:
                item = segment(cursor, start, before)
                reading(item, dcursor, dstart)
                segments.append(item)
            elif before:
                raise ValueError('A zero-width original span cannot carry new observed text')
            item = segment(start, start + len(old), old, verification='uncertain', uncertainty=reason)
            item['scan']['observed_text'] = scan
            reading(item, dstart, dstart + len(dword) if dword else dstart)
            segments.append(item)
            cursor, dcursor = start + len(old), dstart + len(dword) if dword else dstart
        if re.search(r'\{u\d+\}', tail):
            raise ValueError('An authored uncertainty placeholder has no explicit source record')
        if cursor < len(original):
            item = segment(cursor, len(original), tail)
            reading(item, dcursor, high)
            segments.append(item)
        elif tail:
            raise ValueError('A completed original span cannot carry unaccounted source text')
        for word, side in fragments.get(number, []):
            item = segments[0] if side == 'leading' else segments[-1]
            position = item['corrected_text'].index(word)
            item.setdefault('fragments', []).append({'start': position, 'end': position + len(word),
                'text': word, 'side': side, 'qualification': 'The printed word crosses '
                    'a retained passage boundary. Keep this visible fragment '
                    'separate and exclude it from lexical counts.'})
        result.append({'locus': row['locus'], 'original_row_sha256': hashlib.sha256(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'status': 'reviewed-with-uncertainty' if uncertainties.get(number) else 'reviewed-verified',
            'segments': segments})
    return result
