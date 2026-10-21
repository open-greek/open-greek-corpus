#!/usr/bin/env python3
"""Locate Photius uncertainties in a user-supplied comparison HTML edition.

This optional diagnostic never edits corpus text. It uses consecutive verified
body words on both sides; the uncertain spelling cannot select a location.
Equal best locations remain alternatives. Licensed text stays in the optional
private output; the classification output contains only counts, keys, and pins.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata

import assess_photius_historical as assess

ROOT = Path(__file__).resolve().parents[1]
COMPLETE = Path('data/corpus_changes/photius-bekker-complete-review/review-status.json.gz')
CONTEXT = Path('data/corpus_changes/photius-bekker-context/source-review.json.gz')
PRIOR = Path('data/corpus_changes/photius-bekker-uncertainties/source-review.json')
WORD = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                   if not unicodedata.combining(c)).replace('ς', 'σ')


class EditionHTML(HTMLParser):
    """Retain column labels and distinct HTML data-node positions.

    Token start/end offsets are decoded-node character offsets, not HTML byte
    offsets. The node line, column, and ordinal make repeated nodes distinct.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.codex = self.bekker = self.header = None
        self.header_text = ''
        self.ignore = False
        self.units = []

    def handle_starttag(self, tag, attrs):
        if tag in {'h2', 'h3'}:
            self.header, self.header_text = tag, ''
        if tag == 'td':
            self.ignore = dict(attrs).get('class') == 'Y'

    def handle_endtag(self, tag):
        if tag == self.header:
            if tag == 'h3':
                self.codex = self.header_text.strip()
            else:
                self.bekker = self.header_text.strip()
            self.header = None

    def handle_data(self, data):
        if self.header:
            self.header_text += data
        elif not self.ignore and self.bekker and WORD.search(data):
            self.units.append({'text': data, 'html_line': self.getpos()[0],
                               'html_column': self.getpos()[1], 'unit_index': len(self.units),
                               'codex': self.codex, 'bekker': self.bekker})


def tokenize(units):
    result, previous_tail = [], ''
    for unit in units:
        matches = list(WORD.finditer(unit['text']))
        if not matches:
            continue
        for number, match in enumerate(matches):
            ref = {k: v for k, v in unit.items() if k != 'text'}
            ref.update(start=match.start(), end=match.end())
            separator = (previous_tail + unit['text'][:match.start()] if number == 0
                         else unit['text'][matches[number - 1].end():match.start()])
            if result and re.fullmatch(r'[-‐‑]\s*[\d{}\[\]\s]*', separator):
                result[-1]['text'] += match.group()
                result[-1]['refs'].append(ref)
                result[-1]['key'] = normalize(result[-1]['text'])
            else:
                result.append({'text': match.group(), 'key': normalize(match.group()), 'refs': [ref]})
        previous_tail = unit['text'][matches[-1].end():]
    return result


def verified_flanks(tokens, reliable, start, end, limit=5):
    """Stop at the first unreliable word; never borrow a neighboring row."""
    left, right = [], []
    for i in reversed([i for i, t in enumerate(tokens) if t['end'] <= start]):
        if i not in reliable or len(left) == limit:
            break
        left.append(tokens[i]['key'])
    for i, token in enumerate(tokens):
        if token['start'] < end:
            continue
        if i not in reliable or len(right) == limit:
            break
        right.append(token['key'])
    return list(reversed(left)), right


class Matcher:
    def __init__(self, tokens):
        self.by_page = defaultdict(list)
        for token in tokens:
            label = str(token['refs'][0].get('bekker', ''))
            if re.fullmatch(r'\d+[ab]?', label):
                self.by_page[int(re.match(r'\d+', label)[0])].append(token)

    @lru_cache(maxsize=None)
    def page_index(self, page):
        tokens = [t for p in (page-1, page, page+1) for t in self.by_page[p]]
        index = {n: defaultdict(list) for n in range(2, 6)}
        keys = [t['key'] for t in tokens]
        for n in index:
            for j in range(len(keys)-n+1):
                index[n][tuple(keys[j:j+n])].append(j)
        return tokens, index

    def match(self, page, left, right, *, min_side=3):
        if min_side not in {2, 3}:
            raise ValueError('Require two or three verified words on each side')
        tokens, index = self.page_index(page)
        best, matches = -1, {}
        for nl in range(min(5, len(left)), min_side-1, -1):
            for nr in range(min(5, len(right)), min_side-1, -1):
                if nl+nr < best:
                    continue
                for a in index[nl].get(tuple(left[-nl:]), []):
                    for b in index[nr].get(tuple(right[:nr]), []):
                        start = a+nl
                        if not start <= b <= start+12:
                            continue
                        if nl+nr > best:
                            best, matches = nl+nr, {}
                        matches[(start, b)] = {
                            'reading': ' '.join(t['text'] for t in tokens[start:b]),
                            'left': ' '.join(t['text'] for t in tokens[a:start]),
                            'right': ' '.join(t['text'] for t in tokens[b:b+nr]),
                            'refs': [ref for t in tokens[start:b] for ref in t['refs']],
                            'location': {'page_window': [page-1, page, page+1],
                                         'token_start': start, 'token_end': b},
                            'left_refs': [ref for t in tokens[a:start] for ref in t['refs']],
                            'right_refs': [ref for t in tokens[b:b+nr] for ref in t['refs']],
                            'matched_flank_tokens': best}
        return {'match_status': 'unmatched' if not matches else 'unique' if len(matches) == 1 else 'tied',
                'match_count': len(matches), 'anchor_count': best, 'candidates': list(matches.values())}


def compare(html_raw, complete_raw, context_raw, prior_raw, *, min_side=3):
    started = time.perf_counter()
    complete = json.loads(gzip.decompress(complete_raw))
    context = {r['locus']: r for r in json.loads(gzip.decompress(context_raw))['rows']}
    prior = json.loads(prior_raw)
    resolved = {(r['locus'], r['segment_index']) for r in prior['records'] if r['decision'] == 'resolved'}
    parser = EditionHTML(); parser.feed(html_raw.decode('utf-8-sig'))
    matcher = Matcher(tokenize(parser.units))
    public, private = [], []
    for row in complete['rows']:
        observed = ''.join(s['scan']['observed_text'] for s in row['segments'])
        # The context authority's indices belong to this exact tokenizer.
        tokens = [{**t, 'key': normalize(t['text'].rstrip(assess.APOSTROPHES))}
                  for t in assess.tokens(observed)]
        reliable = set(context[row['locus']]['context']['reliable_source_indices'])
        offset = 0
        for i, segment in enumerate(row['segments']):
            end = offset+len(segment['scan']['observed_text'])
            if segment['verification'] == 'uncertain' and (row['locus'], i) not in resolved:
                left, right = verified_flanks(tokens, reliable, offset, end)
                result = matcher.match(int(row['printed_page']), left, right, min_side=min_side)
                candidates = result.pop('candidates')
                item = {'locus': row['locus'], 'segment_index': i, **result}
                public.append(item)
                private.append({**item, 'candidates': candidates})
            offset = end
    pins = {'compiled_sha256': sha(complete_raw), 'context_sha256': sha(context_raw),
            'prior_uncertainties_sha256': sha(prior_raw), 'local_html_sha256': sha(html_raw)}
    metadata = {'schema': 'photius-comparison-locations-v1', 'pins': pins, 'min_verified_words_each_side': min_side,
        'qualification': 'Locations in a comparison edition, never correction authority. No uncertain target spelling selects a match. Ties remain alternatives. Column labels and offsets occur only in the optional private output.',
        'elapsed_seconds': time.perf_counter()-started,
        'counts': dict(Counter(r['match_status'] for r in public))}
    return {**metadata, 'records': public}, {**metadata, 'records': private}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison-html', type=Path, required=True)
    parser.add_argument('--classification', type=Path, required=True,
                        help='Classification-only JSON; contains no comparison text or local paths')
    parser.add_argument('--private-output', type=Path,
                        help='Optional licensed excerpts; keep outside public repositories')
    parser.add_argument('--min-side', type=int, choices=(2, 3), default=3)
    args = parser.parse_args()
    public, private = compare(args.comparison_html.read_bytes(), (ROOT/COMPLETE).read_bytes(),
        (ROOT/CONTEXT).read_bytes(), (ROOT/PRIOR).read_bytes(), min_side=args.min_side)
    for path, value in ((args.classification, public), (args.private_output, private)):
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'records': len(public['records']), 'counts': public['counts'],
                      'elapsed_seconds': public['elapsed_seconds']}))


if __name__ == '__main__':
    main()
