"""Locate held editorial readings using elastic, ordered context.

Only already eligible context words establish a location. Excluded text has
neither spelling nor token-count influence: its alignment gaps are free. A
reading is chosen only when every optimal path fixes both immediate reliable
boundary words. This helper returns evidence; it never changes a corpus row.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math

import compare_photius_local_edition as edition
import repair_photius_context as context
import repair_photius_uncertainties as masks

SOURCE_ID = 'tlg-photius-henry'
END_MARKS = edition.assess.APOSTROPHES + '\u02b9\u0374'
MAX_SOURCE_TOKENS = 1600
MAX_ALIGNMENT_CELLS = 12_000_000
MAX_GAP_TOKENS = 48


def _sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def elastic_alignment(source, digital, neutral):
    """Retain all optimal semiglobal paths without an uncertain-length vote."""
    m, n = len(source), len(digital)
    previous = [0] * (n + 1)
    back = [bytearray(n + 1)]
    for i, word in enumerate(source, 1):
        unknown = i - 1 in neutral
        deletion_cost = 0 if unknown else context.GAP_COST
        insertion_cost = 0 if unknown or i in neutral else context.GAP_COST
        first = int(previous[0]) + deletion_cost
        if context._np is not None and n:
            np = context._np
            prior = np.asarray(previous, dtype=np.int64)
            costs = (np.zeros(n, dtype=np.int64) if unknown else
                     np.fromiter((context._substitution(word, other) for other in digital),
                                 dtype=np.int64, count=n))
            diagonal, deletion = prior[:-1] + costs, prior[1:] + deletion_cost
            positions = np.arange(n + 1, dtype=np.int64) * insertion_cost
            current = np.minimum.accumulate(np.r_[first,
                np.minimum(diagonal, deletion) - positions[1:]]) + positions
            directions = bytearray(n + 1)
            directions[0] = 2
            directions[1:] = ((diagonal == current[1:]).astype(np.uint8) |
                ((deletion == current[1:]).astype(np.uint8) << 1) |
                ((current[:-1] + insertion_cost == current[1:]).astype(np.uint8) << 2)).tobytes()
        else:
            current, directions = [first] + [0] * n, bytearray(n + 1)
            directions[0] = 2
            for j, other in enumerate(digital, 1):
                diagonal = previous[j - 1] + (0 if unknown else context._substitution(word, other))
                deletion, insertion = previous[j] + deletion_cost, current[j - 1] + insertion_cost
                best = min(diagonal, deletion, insertion)
                current[j] = best
                directions[j] = int(diagonal == best) | int(deletion == best) << 1 | int(insertion == best) << 2
        back.append(directions)
        previous = current
    best = int(min(previous))
    ends = [j for j, value in enumerate(previous) if value == best]
    pending, seen, starts = [(m, j) for j in ends], set(), set()
    counterparts, absent = [set() for _ in source], [False] * m
    while pending:
        i, j = pending.pop()
        if (i, j) in seen:
            continue
        seen.add((i, j))
        if not i:
            starts.add(j)
            continue
        direction = back[i][j]
        if direction & 1:
            counterparts[i - 1].add(j - 1)
            pending.append((i - 1, j - 1))
        if direction & 2:
            absent[i - 1] = True
            pending.append((i - 1, j))
        if direction & 4:
            pending.append((i, j - 1))
    return {'cost': best, 'starts': sorted(starts), 'ends': ends,
            'counterparts': [sorted(values) for values in counterparts],
            'may_be_unaligned': absent, 'aligned': bool(m and best < m * context.GAP_COST)}


def _tokens(text, excluded):
    leaves = masks._flatten(text, excluded)
    tokens = [{'start': match.start(), 'end': match.end(), 'text': match.group(),
               'key': edition.normalize(match.group())}
              for match in edition.WORD.finditer(text)]
    # A wholly unread numeral or symbol still occupies an uncertain source
    # interval. An opaque neutral placeholder lets it have an elastic gap too.
    opaque = {(leaf['start'], leaf['end']): leaf['text'] for leaf in leaves
              if leaf['text'].strip() and not any(
                  leaf['start'] < token['end'] and token['start'] < leaf['end'] for token in tokens)}
    tokens.extend({'start': a, 'end': b, 'text': value, 'key': ''}
                  for (a, b), value in opaque.items())
    tokens.sort(key=lambda token: (token['start'], token['end']))
    return tokens, {i for i, token in enumerate(tokens)
        if any(leaf['start'] < token['end'] and token['start'] < leaf['end'] for leaf in leaves)}


def _alternative(record):
    result = []
    for reading in record.get('readings', []):
        if reading.get('source_id') == SOURCE_ID:
            result.append({**deepcopy(reading), 'role': 'alternative'})
    return result


def _window(scope, neighbors):
    row = scope['row']
    target_page = int(scope['record']['printed_page'])
    entries = (scope.get('context_rows') or []) if neighbors else []
    if not entries:
        entries = [{'row': row, 'excluded_spans': scope['excluded_spans'],
                    'printed_page': target_page}]
    if len(entries) > 3 or sum(len(entry['row']['text']) for entry in entries) > 32_000:
        return None
    occurrences = sum(entry['row']['locus'] == row['locus'] for entry in entries)
    if not occurrences:
        return None
    if occurrences != 1:
        raise ValueError('A source-ordered context window must contain its exact target row once')
    texts, tokens, neutral, offsets, cursor, source_order = [], [], set(), {}, 0, []
    for entry in entries:
        other = entry['row']
        if abs(int(entry['printed_page']) - target_page) > 1:
            return None
        if other['locus'] == row['locus'] and other != row:
            raise ValueError('The context target differs from its supplied current row')
        if other['locus'] in offsets:
            raise ValueError('A context window repeats a source row')
        ts, ns = _tokens(other['text'], entry['excluded_spans'])
        offsets[other['locus']] = cursor
        neutral.update(len(tokens) + i for i in ns)
        tokens.extend({**token, 'start': cursor + token['start'], 'end': cursor + token['end']}
                      for token in ts)
        texts.append(other['text'])
        source_order.append({'locus': other['locus'], 'row_sha256': _sha(other),
                             'masks_sha256': _sha(entry['excluded_spans'])})
        cursor += len(other['text']) + 1  # diagnostic separator only; no word is joined
    return {'text': '\n'.join(texts), 'tokens': tokens, 'neutral': neutral,
            'offsets': offsets, 'source_order': source_order}


def locate_remaining(html_raw, scopes):
    """Return checked readings for a complete mapping of held occurrence scopes.

    Each scope contains row, current start/end, frozen held record, and current
    effective excluded_spans. Optional context_rows are an explicitly ordered
    list of at most three row/mask/printed_page dictionaries. Do not infer that
    historical row identifiers alone establish physical reading order.
    """
    parser = edition.EditionHTML()
    parser.feed(html_raw.decode('utf-8-sig'))
    digital_tokens = edition.tokenize(parser.units)
    for token in digital_tokens:
        ref = token['refs'][-1]
        unit = parser.units[ref['unit_index']]['text']
        if ref['end'] < len(unit) and unit[ref['end']] in END_MARKS:
            token['text'] += unit[ref['end']]
            ref['end'] += 1
    matcher, cache, result = edition.Matcher(digital_tokens), {}, {}
    row_scopes = {}
    for key, scope in scopes.items():
        row, record = scope['row'], scope['record']
        a, b = scope['start'], scope['end']
        if (key != (row['locus'], record['segment_index']) or record['locus'] != row['locus']
                or type(a) is not int or type(b) is not int or not 0 <= a < b <= len(row['text'])
                or row['text'][a:b] != record['original_text'] or 'excluded_spans' not in scope):
            raise ValueError('A held scope requires exact current coordinates and effective masks')
        row_scopes.setdefault(row['locus'], []).append((a, b))
    for key, scope in scopes.items():
        record, row = scope['record'], scope['row']
        answer = {'readings': _alternative(record), 'method': 'elastic-ordered-context',
                  'evidence': {'status': 'held', 'source_sha256': hashlib.sha256(html_raw).hexdigest()}}
        result[key] = answer
        segment = record['original_segment']
        if segment.get('fragments') or segment.get('text_role') != 'authorial-body':
            answer['evidence']['status'] = 'held-fragment-or-nonbody'
            continue
        page = int(record['printed_page'])
        digital, _ = matcher.page_index(page)
        for neighbors in (False, True):
            if neighbors and not scope.get('context_rows'):
                break
            window = _window(scope, neighbors)
            if window is None:
                continue
            tokens = window['tokens']
            neutral = set(window['neutral'])
            # All held scopes remain neutral even if a caller's masks omitted a cause.
            for locus, offset in window['offsets'].items():
                neutral.update(i for i, token in enumerate(tokens) if any(
                    offset + a < token['end'] and token['start'] < offset + b
                    for a, b in row_scopes.get(locus, [])))
            a = window['offsets'][row['locus']] + scope['start']
            b = window['offsets'][row['locus']] + scope['end']
            overlapping = [i for i, token in enumerate(tokens) if a < token['end'] and token['start'] < b]
            extent = (tokens[overlapping[0]]['start'], tokens[overlapping[-1]]['end']) if overlapping else (a, b)
            left = [i for i, token in enumerate(tokens) if token['end'] <= extent[0]]
            right = [i for i, token in enumerate(tokens) if token['start'] >= extent[1]]
            if not left or not right or left[-1] in neutral or right[0] in neutral:
                answer['evidence']['status'] = 'held-no-immediate-reliable-boundaries'
                continue
            reliable = set(range(len(tokens))) - neutral
            if (len(reliable) < 5 or len(tokens) > MAX_SOURCE_TOKENS
                    or len(tokens) * len(digital) > MAX_ALIGNMENT_CELLS):
                answer['evidence']['status'] = 'held-context-size-or-anchor-count'
                continue
            cache_key = (page, tuple(t['key'] for t in tokens), tuple(sorted(neutral)))
            if cache_key not in cache:
                cache[cache_key] = elastic_alignment(list(cache_key[1]), [t['key'] for t in digital], neutral)
            aligned = cache[cache_key]
            anchors = [i for i in reliable if len(aligned['counterparts'][i]) == 1
                and not aligned['may_be_unaligned'][i]
                and tokens[i]['key'] == digital[aligned['counterparts'][i][0]]['key']]
            proof = {'cost': aligned['cost'], 'source_tokens': len(tokens), 'reliable_tokens': len(reliable),
                     'exact_unique_anchors': len(anchors), 'minimum_anchors': max(5, math.ceil(.7 * len(reliable))),
                     'source_order': window['source_order'], 'neighborhood': neighbors,
                     'neutral_spelling_and_length_cost': 0}
            answer['evidence'] = {'status': 'held-context-quality', **proof,
                                  'source_sha256': hashlib.sha256(html_raw).hexdigest()}
            if (not aligned['aligned'] or len(anchors) < 5 or 10 * len(anchors) < 7 * len(reliable)
                    or 100 * aligned['cost'] > 35 * len(tokens) * context.GAP_COST):
                continue
            li, ri = left[-1], right[0]
            if li not in anchors or ri not in anchors:
                answer['evidence']['status'] = 'held-ambiguous-boundaries'
                continue
            if neighbors and (sum(i <= li for i in anchors) < 2 or sum(i >= ri for i in anchors) < 2):
                answer['evidence']['status'] = 'held-one-sided-neighborhood'
                continue
            first, last = aligned['counterparts'][li][0] + 1, aligned['counterparts'][ri][0]
            if not 0 <= first <= last <= len(digital) or last - first > MAX_GAP_TOKENS:
                answer['evidence']['status'] = 'held-invalid-or-excessive-gap'
                continue
            option = digital[first:last]
            reused = [token for token in option if _sha(token['refs'])
                      in scope.get('previously_used_source_refs', set())]
            if reused:
                answer['readings'] = []
                answer['evidence'].update(status='held-already-admitted-source-ref',
                                         block_prior_fallback=True,
                                         reused_refs=[deepcopy(token['refs']) for token in reused])
                continue
            boundary_tokens = [digital[first - 1], digital[last]]
            codices = {ref['codex'] for token in [*boundary_tokens, *option] for ref in token['refs']}
            if len(codices) != 1:
                answer['evidence']['status'] = 'held-cross-codex-boundaries'
                continue
            reading = {'text': ' '.join(token['text'] for token in option),
                       'tokens': [{'text': token['text'], 'refs': deepcopy(token['refs'])} for token in option],
                       'refs': [deepcopy(ref) for token in option for ref in token['refs']],
                       'role': 'chosen' if option else 'alternative', 'source_id': SOURCE_ID}
            answer['readings'] = [reading]
            answer['evidence'].update(status='located' if option else 'held-empty-source-gap',
                source_extent=[extent[0] - window['offsets'][row['locus']],
                               extent[1] - window['offsets'][row['locus']]],
                left_boundary={'text': tokens[li]['text'], 'refs': deepcopy(boundary_tokens[0]['refs'])},
                right_boundary={'text': tokens[ri]['text'], 'refs': deepcopy(boundary_tokens[1]['refs'])})
            break
    # Separate held intervals cannot silently claim the same supplied source
    # word. A future joint-word repair may reconcile them, but this occurrence
    # helper must not manufacture two independent attestations from one token.
    owners = {}
    for key, answer in result.items():
        if answer['evidence']['status'] == 'located':
            for token in answer['readings'][0]['tokens']:
                owners.setdefault(_sha(token['refs']), set()).add(key)
    for key, answer in result.items():
        if answer['evidence']['status'] != 'located':
            continue
        conflicts = sorted({other for token in answer['readings'][0]['tokens']
                            for other in owners[_sha(token['refs'])] if other != key})
        if conflicts:
            answer['readings'] = []
            answer['evidence'].update(status='held-reused-new-source-ref',
                                     block_prior_fallback=True,
                                     conflicting_targets=[list(other) for other in conflicts])
    return result
