#!/usr/bin/env python3
"""Assess retained historical Photius readings without authorizing corrections.

Every minimum-cost local alignment is retained as token candidate edges, rather
than selecting one path through repeated words. Row fragments align independently
against their full digital page; source order is never inferred from row order.
Unicode offsets always address untouched input strings. This is a comparison of
two imperfect readings, not scan review, a new consensus, or an admission layer.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from difflib import SequenceMatcher
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

try:
    import numpy as _np
except ImportError:  # The identical standard-library path remains supported.
    _np = None

ROOT = Path(__file__).resolve().parents[1]
RECIPE_FILE = Path(__file__).resolve()
RECIPE_SHA256 = hashlib.sha256(RECIPE_FILE.read_bytes()).hexdigest()
CORPUS = Path('data/corpus/photius.bibliotheca.jsonl')
LIBRARY = Path('data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz')
LIBRARY_SHA256 = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
ORIGINAL = Path('data/corpus_changes/photius-bekker-index/before.jsonl.gz')
ORIGINAL_SHA256 = '95f5814a95ac9c0b26010c624dc605248f1937868d9fe1e15178ab6cd9f0ee68'
SOURCE_PDF_SHA256 = 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb'
COVERAGE = Path('data/corpus_changes/photius-bekker-coverage/coverage.json')
OUT = Path('data/audits/photius-historical-readings.json')
PAGE = re.compile(r'helladius_chrestomathia_photius_bekker_v2_(\d{4})\.(\d+)')
SECTION_PREFIX = 'tlg4040-tlg001-local002-s'
GAP_COST = 60
MAX_FRAGMENT_TOKENS = 24
APOSTROPHES = "'’ʼ᾽"
MAPPING_EXCEPTIONS = {
    169: {'authorial_printed_page': 434, 'digital_scan_printed_page': 334,
          'evidence': 'Combined scan446, the source of digital section s446, repeats printed334; legacy physical169 preserves genuine printed434.'},
    170: {'authorial_printed_page': 435, 'digital_scan_printed_page': 335,
          'evidence': 'Combined scan447, the source of digital section s447, repeats printed335; legacy physical170 preserves genuine printed435.'},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def encode(value):
    # Shared token tables avoid repeating full digital spans at every edge.
    return canonical(value) + b'\n'


def _base(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))


def _key(text):
    return _base(text.casefold()).replace('ς', 'σ').rstrip(APOSTROPHES)


def tokens(text):
    """Keep exact Unicode codepoint spans; never join printed word fragments."""
    result, i = [], 0
    while i < len(text):
        if not unicodedata.category(text[i]).startswith(('L', 'M')):
            i += 1
            continue
        start = i
        while i < len(text) and (unicodedata.category(text[i]).startswith(('L', 'M')) or text[i] in APOSTROPHES):
            i += 1
        word = text[start:i]
        if any(unicodedata.category(c).startswith('L') and 'GREEK' in unicodedata.name(c, '') for c in word):
            token = {'start': start, 'end': i, 'text': word}
            if i < len(text) and text[i] in '-‐':
                token['following_hyphen'] = {'start': i, 'end': i + 1, 'text': text[i]}
            result.append(token)
    return result


def _comparison(old, digital):
    if old == digital:
        return 'exact'
    if _base(old) == _base(digital):
        return 'mark-only'
    return 'substantive'


@lru_cache(maxsize=250000)
def _substitution(a, b):
    if a == b:
        return 0
    if not set(a).intersection(b):
        return 100
    # Character resemblance locates candidates; it never establishes a spelling.
    return max(1, round(100 * (1 - SequenceMatcher(None, a, b, autojunk=False).ratio())))


def _exact_windows(needle, haystack):
    width = len(needle)
    return [j for j in range(len(haystack) - width + 1) if haystack[j:j + width] == needle]


def _local_alignment(old, digital):
    """Return the union of edges in ALL optimal semiglobal alignment paths.

    Digital prefix/suffix are unobserved, not deletion claims. Candidate edges
    can belong to mutually exclusive paths; the report never treats their union
    as one chosen sequence. No candidate/path-count cutoff discards ties.
    """
    m, n = len(old), len(digital)
    if not m:
        raise ValueError('An assessment fragment must contain an original token')
    exact = _exact_windows(old, digital)
    if exact:
        return {'cost': 0, 'starts': exact, 'ends': [j + m for j in exact],
                'counterparts': [sorted(j + i for j in exact) for i in range(m)],
                'may_be_unaligned': [False] * m, 'digital_only': [],
                'ambiguous': len(exact) > 1, 'aligned': True}
    previous = [0] * (n + 1)
    back = [bytearray(n + 1)]
    for i, word in enumerate(old, 1):
        if _np is not None and n:
            prior = _np.asarray(previous, dtype=_np.int64)
            cost = _np.fromiter((_substitution(word, other) for other in digital), dtype=_np.int64, count=n)
            diagonal, deletion = prior[:-1] + cost, prior[1:] + GAP_COST
            positions = _np.arange(n + 1, dtype=_np.int64) * GAP_COST
            # The leftward insertion recurrence is a prefix minimum. Integer
            # arithmetic preserves every tied predecessor, including the first.
            current = _np.minimum.accumulate(_np.r_[i * GAP_COST,
                _np.minimum(diagonal, deletion) - positions[1:]]) + positions
            directions = bytearray(n + 1)
            directions[0] = 2
            directions[1:] = ((diagonal == current[1:]).astype(_np.uint8) |
                ((deletion == current[1:]).astype(_np.uint8) << 1) |
                ((current[:-1] + GAP_COST == current[1:]).astype(_np.uint8) << 2)).tobytes()
            back.append(directions)
            previous = current
            continue
        current = [i * GAP_COST] + [0] * n
        directions = bytearray(n + 1)
        directions[0] = 2
        for j, other in enumerate(digital, 1):
            diagonal = previous[j - 1] + _substitution(word, other)
            deletion, insertion = previous[j] + GAP_COST, current[j - 1] + GAP_COST
            best = min(diagonal, deletion, insertion)
            current[j] = best
            directions[j] = ((1 if diagonal == best else 0) |
                             (2 if deletion == best else 0) |
                             (4 if insertion == best else 0))
        back.append(directions)
        previous = current
    best = int(min(previous))
    ends = [j for j, value in enumerate(previous) if value == best]
    pending = [(m, j) for j in ends]
    seen, starts, inserted = set(), set(), set()
    counterparts = [set() for _ in old]
    unmatched = [False] * m
    ambiguous = len(ends) > 1
    while pending:
        i, j = pending.pop()
        if (i, j) in seen:
            continue
        seen.add((i, j))
        if i == 0:
            starts.add(j)
            continue
        direction = back[i][j]
        if direction not in (1, 2, 4):
            ambiguous = True
        if direction & 1:
            counterparts[i - 1].add(j - 1)
            pending.append((i - 1, j - 1))
        if direction & 2:
            unmatched[i - 1] = True
            pending.append((i - 1, j))
        if direction & 4:
            inserted.add(j - 1)
            pending.append((i, j - 1))
    return {'cost': best, 'starts': sorted(starts), 'ends': ends,
            'counterparts': [sorted(v) for v in counterparts],
            'may_be_unaligned': unmatched, 'digital_only': sorted(inserted),
            'ambiguous': ambiguous, 'aligned': best < m * GAP_COST}


def _fragments(text, old, digital):
    """Split only for computation; no fragment is asserted to be a printed line."""
    a, b = [_key(t['text']) for t in old], [_key(t['text']) for t in digital]
    anchor_index = defaultdict(list)
    for j in range(max(0, len(b) - 2)):
        anchor_index[tuple(b[j:j + 3])].append(j)
    anchors = [set() for _ in a]
    for i in range(max(0, len(a) - 2)):
        for j in anchor_index.get(tuple(a[i:i + 3]), []):
            for shift in range(3):
                anchors[i + shift].add(j + shift)
    start, reason = 0, 'row-start'
    for i in range(1, len(old)):
        split = None
        if '\n' in text[old[i - 1]['end']:old[i]['start']]:
            split = 'explicit-newline'
        elif anchors[i - 1] and anchors[i] and not {j + 1 for j in anchors[i - 1]}.intersection(anchors[i]):
            split = 'independent-anchor-discontinuity'
        elif i - start >= MAX_FRAGMENT_TOKENS:
            split = 'computational-token-limit'
        if split:
            yield start, i, reason
            start, reason = i, split
    if old:
        yield start, len(old), reason


def _row_assessment(row, page, original=None):
    text = row.get('text')
    if not isinstance(text, str):
        raise ValueError('An assessed historical row needs its exact current text')
    old, digital = tokens(text), page['tokens']
    result = {'locus': row['locus'], 'physical_page': page['physical_page'],
              'section': page['section'], 'current_row_sha256': sha(canonical(row)),
              'current_row': deepcopy(row), 'tokens': old, 'fragments': [], 'fragment_order_candidates': []}
    if original is not None:
        result.update(original_row_sha256=sha(canonical(original)), original_row=deepcopy(original))
    exception = page.get('source_mapping_exception')
    status = 'source-mapping-exception' if exception else ('digital-section-missing' if not page['available'] else 'diagnostic-only')
    result['comparison_status'] = status
    if status != 'diagnostic-only' or not old or not digital:
        for token in old:
            token.update(classification='unaligned', counterpart_indices=[], may_be_unaligned=True)
        result.update(classification='unaligned', ambiguous=False)
        return result
    keys = [_key(t['text']) for t in digital]
    aligned = False
    for start, end, reason in _fragments(text, old, digital):
        alignment = _local_alignment([_key(t['text']) for t in old[start:end]], keys)
        aligned |= alignment['aligned']
        result['fragments'].append({'token_start': start, 'token_end': end, 'reason': reason,
            'codepoint_start': old[start]['start'], 'codepoint_end': old[end - 1]['end'],
            'minimum_cost': alignment['cost'], 'possible_source_starts': alignment['starts'],
            'possible_source_ends': alignment['ends'], 'digital_only_candidates': alignment['digital_only'],
            'ambiguous': alignment['ambiguous'], 'aligned': alignment['aligned']})
        for k, token in enumerate(old[start:end]):
            candidates = alignment['counterparts'][k]
            comparisons = [_comparison(token['text'], digital[j]['text']) for j in candidates]
            classification = ('unaligned' if not comparisons else
                'substantive' if 'substantive' in comparisons or alignment['may_be_unaligned'][k] else
                'mark-only' if 'mark-only' in comparisons else 'exact')
            token.update(classification=classification, counterpart_indices=candidates,
                         may_be_unaligned=alignment['may_be_unaligned'][k])
    substantive = any(t['classification'] not in ('exact', 'mark-only') for t in old)
    substantive |= any(f['digital_only_candidates'] for f in result['fragments'])
    displacement = []
    for index, (left, right) in enumerate(zip(result['fragments'], result['fragments'][1:])):
        ends, starts = left['possible_source_ends'], right['possible_source_starts']
        if ends and starts and max(ends) > min(starts):
            disposition = ('reverse-or-overlap-in-every-local-candidate' if min(ends) > max(starts)
                           else 'reverse-or-overlap-in-some-local-candidates')
            displacement.append({'left_fragment': index, 'right_fragment': index + 1,
                                 'disposition': disposition})
    result['fragment_order_candidates'] = displacement
    substantive |= any(v['disposition'] == 'reverse-or-overlap-in-every-local-candidate' for v in displacement)
    result.update(classification=('unaligned' if not aligned else 'substantive' if substantive else
        'mark-only' if any(t['classification'] == 'mark-only' for t in old) else 'exact'),
        ambiguous=any(f['ambiguous'] for f in result['fragments']))
    return result


def _rows(value):
    if isinstance(value, bytes):
        return [json.loads(line) for line in value.splitlines() if line.strip()], sha(value)
    if isinstance(value, dict):
        value = list(value.values())
    value = list(value)
    return value, sha(canonical(value))


def candidates(rows, library, *, original_rows=None, input_pins=None):
    """Return all historical-row candidates; pure, deterministic, and read-only.

    rows accepts JSONL bytes or row iterables. library accepts frozen gzip/JSON
    bytes or its parsed document. materialize(report,locus) expands shared digital
    token indices to exact section/codepoint/text pointers for source reviewers.
    """
    current, current_sha = _rows(rows)
    reserved = {'current_rows_sha256', 'original_rows_sha256', 'digital_archive_sha256'}
    if reserved.intersection(input_pins or {}):
        raise ValueError('Caller pins cannot override hashes computed from the actual assessment inputs')
    originals, original_sha = _rows(original_rows) if original_rows is not None else ([], None)
    by_original = {r['locus']: r for r in originals}
    if len(by_original) != len(originals):
        raise ValueError('Historical originals repeat a locus')
    if isinstance(library, bytes):
        library_sha = sha(library)
        document = json.loads(gzip.decompress(library) if library.startswith(b'\x1f\x8b') else library)
    else:
        document, library_sha = deepcopy(library), sha(canonical(library))
    if document.get('id') != 'tlg4040.tlg001.local002':
        raise ValueError('Historical assessment needs the exact Photius digital edition identity')
    sections = {s['id']: s for s in document['sections']}
    if len(sections) != len(document['sections']):
        raise ValueError('Digital edition repeats a section identity')
    selected = []
    for row in current:
        match = PAGE.fullmatch(row.get('locus', ''))
        if match and not row.get('ocr_consensus'):
            if row.get('urn') != 'photius.bibliotheca':
                raise ValueError('A historical Photius locus has a different work identity')
            selected.append((int(match[1]), int(match[2]), row))
    selected.sort(key=lambda v: (v[0], v[1]))
    if len({r['locus'] for _, _, r in selected}) != len(selected):
        raise ValueError('Current historical rows repeat a locus')
    if original_rows is not None and any(row['locus'] not in by_original for _, _, row in selected):
        raise ValueError('A selected historical row is absent from the supplied immutable originals')
    pages = {}
    for physical in sorted({p for p, _, _ in selected}):
        section = SECTION_PREFIX + str(physical + 277)
        source = sections.get(section)
        text = '\n'.join(b['text'] for b in source['blocks']) if source else ''
        page = {'physical_page': physical, 'printed_page': physical + 265, 'section': section,
                'available': source is not None, 'text': text, 'text_sha256': sha(text.encode()),
                'section_sha256': sha(canonical(source)) if source else None, 'tokens': tokens(text)}
        page['usable_for_counterparts'] = source is not None and physical not in MAPPING_EXCEPTIONS
        if physical in MAPPING_EXCEPTIONS:
            page['source_mapping_exception'] = deepcopy(MAPPING_EXCEPTIONS[physical])
        pages[physical] = page
    assessed = [_row_assessment(row, pages[p], by_original.get(row['locus'])) for p, _, row in selected]
    return {'schema_version': 1, 'kind': 'diagnostic-historical-reading-comparison',
        'work': 'photius.bibliotheca', 'admission_authorized': False, 'scan_reviewed': False,
        'qualification': 'Digital disagreement is a candidate for source inspection, never a scan-reviewed correction or a voted reading. Exact or mark-only comparison does not certify the source text. Shared errors and digital omissions remain possible.',
        'policy': {'offsets': 'Unicode codepoints in untouched input strings; no word joining or letter substitution.',
            'alignment': 'Independent local fragments; all minimum-cost path edges retained. Candidate edges may belong to mutually exclusive alignments.',
            'digital_scope': 'Full frozen digital pages may include editorial matter. Similarity does not classify a passage as authorial text or apparatus.',
            'segmentation': 'Explicit newlines, independent three-word anchor discontinuities, and a maximum24-token computational fragment; no whole-page row-order constraint.',
            'cost': {'insertion': GAP_COST, 'deletion': GAP_COST,
                     'substitution': 'Rounded100*(1-SequenceMatcher ratio) of casefolded accent-insensitive token keys; minimum1 for differing keys.'},
            'mark_only': 'Only combining-mark or canonical Unicode differences; case/letter changes remain substantive.',
            'mapping_exceptions': 'Legacy169/170 have no valid counterpart in expected digital s446/s447. The wrong digital windows are retained for diagnosis only.'},
        'input_pins': {'current_rows_sha256': current_sha, 'original_rows_sha256': original_sha,
            'digital_archive_sha256': library_sha, **deepcopy(input_pins or {})},
        'digital_source': {key: deepcopy(document.get(key)) for key in ('id', 'sourceUrl', 'sourceCitation', 'sourceRights', 'license', 'availability')},
        'pages': list(pages.values()), 'rows': assessed,
        'counts': {'rows': len(assessed), 'pages': len(pages),
            'row_classifications': dict(sorted(Counter(r['classification'] for r in assessed).items())),
            'token_classifications': dict(sorted(Counter(t['classification'] for r in assessed for t in r['tokens']).items())),
            'ambiguous_rows': sum(r['ambiguous'] for r in assessed),
            'fragment_order_candidate_rows': sum(bool(r.get('fragment_order_candidates')) for r in assessed),
            'source_mapping_exception_rows': sum(r['comparison_status'] == 'source-mapping-exception' for r in assessed),
            'source_mapping_exception_pages': sum('source_mapping_exception' in p for p in pages.values()),
            'missing_digital_sections': sum(not p['available'] for p in pages.values())}}


def materialize(report, locus):
    """Expand shared source indices without guessing one preferred counterpart."""
    row = next(r for r in report['rows'] if r['locus'] == locus)
    page = next(p for p in report['pages'] if p['physical_page'] == row['physical_page'])
    values = []
    for index, token in enumerate(row['tokens']):
        values.append({'token_index': index, **deepcopy(token),
            'original_span': {'start': token['start'], 'end': token['end'], 'original_text': token['text']},
            'counterparts': [
            {'section': page['section'], **deepcopy(page['tokens'][j]),
             'original_text': page['tokens'][j]['text'],
             'comparison': _comparison(token['text'], page['tokens'][j]['text'])}
            for j in token['counterpart_indices']]})
    return {'locus': locus, 'comparison_status': row['comparison_status'],
            'classification': row['classification'], 'tokens': values}


def build(root=ROOT):
    if sha(RECIPE_FILE.read_bytes()) != RECIPE_SHA256:
        raise ValueError('Assessment code changed after import; restart with the frozen recipe')
    current, library = (root / CORPUS).read_bytes(), (root / LIBRARY).read_bytes()
    original_raw = (root / ORIGINAL).read_bytes()
    originals = gzip.decompress(original_raw)
    if sha(library) != LIBRARY_SHA256 or sha(originals) != ORIGINAL_SHA256:
        raise ValueError('Frozen digital or original historical source changed or was invalidated')
    coverage_raw = (root / COVERAGE).read_bytes()
    coverage = json.loads(coverage_raw)
    actual = {e['retained_legacy_scan_page']: e for e in coverage['source_scan_exceptions']}
    if (coverage['legacy_source']['sha256'] != SOURCE_PDF_SHA256
            or len(actual) != len(coverage['source_scan_exceptions'])
            or set(actual) != set(MAPPING_EXCEPTIONS) or any(
            actual[p]['authorial_printed_page'] != v['authorial_printed_page']
            or actual[p]['combined_scan_printed_page'] != v['digital_scan_printed_page']
            or actual[p]['logical_combined_position'] != p + 277
            or actual[p]['source']['sha256'] != SOURCE_PDF_SHA256
            for p, v in MAPPING_EXCEPTIONS.items())):
        raise ValueError('Known physical/digital source mapping exceptions changed')
    credit = coverage['source_library']
    if (credit['sha256'] != LIBRARY_SHA256 or credit['edition'] != 'tlg4040.tlg001.local002'
            or credit['license']['url'] != 'https://creativecommons.org/licenses/by-sa/4.0/'):
        raise ValueError('Historical assessment digital attribution differs from its frozen source')
    report = candidates(current, library, original_rows=originals, input_pins={
        'current_corpus': {'path': CORPUS.as_posix(), 'sha256': sha(current)},
        'original_corpus': {'path': ORIGINAL.as_posix(), 'sha256': sha(original_raw), 'uncompressed_sha256': sha(originals)},
        'digital_archive': {'path': LIBRARY.as_posix(), 'sha256': sha(library)},
        'physical_scan': deepcopy(coverage['legacy_source']),
        'source_mapping_review': {'path': COVERAGE.as_posix(), 'sha256': sha(coverage_raw)},
        'recipe': {'path': 'scripts/assess_photius_historical.py', 'sha256': RECIPE_SHA256}})
    report['digital_source']['credit'] = {key: deepcopy(credit.get(key)) for key in
        ('edition', 'url', 'sha256', 'license', 'rights', 'api_notice_url',
         'api_notice_checked_date', 'separate_api_notice')}
    if sha(RECIPE_FILE.read_bytes()) != RECIPE_SHA256:
        raise ValueError('Assessment code changed during the run; restart with the frozen recipe')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true')
    action.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = encode(build())
    if args.write:
        (ROOT / OUT).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / OUT).write_bytes(expected)
    elif args.check:
        if (ROOT / OUT).read_bytes() != expected:
            raise SystemExit('Historical assessment does not reproduce from current pinned inputs')
    else:
        print(json.dumps({'output': OUT.as_posix(), 'sha256': sha(expected), 'bytes': len(expected),
                          'counts': json.loads(expected)['counts'], 'admission_authorized': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
