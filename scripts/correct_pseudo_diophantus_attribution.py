#!/usr/bin/env python3
"""Replay or withdraw the one source-backed attribution correction for2039.004.

No corpus text, tokens, work ID, edition, anchors, or foreign metadata changes.
Registry serialization and opaque author allocation use their native owners.
The public export check requires the replayed result, so regeneration cannot
silently reinstate the genuine Diophantus attribution.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from source_identity import Registry  # noqa: E402
from build_id_registry import Ledger, AUTHOR_PREFIX, author_slugs_for_served  # noqa: E402

AUDIT = 'data/corpus_changes/diophantus_fragment_pseudepigraphic_20261109.json'
AUDIT_SHA = '470d89a3ac8794d3741c6beda00a6513c418f7fd3231d3999cab202c18b98917'
WORK = 'diophantus-mathematics.fragmentum-sp-e-cod-paris-453'
CTS = 'urn:cts:greekLit:tlg2039.tlg004'
FILES = ('data/source_registry.json', 'data/author_ids.json', 'data/work_index.json')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def same(left, right):
    """Exact JSON types, including integer/float and boolean distinctions."""
    encode = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return encode(left) == encode(right)


def load(root, relative):
    return json.loads((root / relative).read_bytes())


def declaration(root):
    raw = (root / AUDIT).read_bytes()
    if digest(raw) != AUDIT_SHA:
        raise ValueError('The reviewed attribution declaration changed')
    audit = json.loads(raw)
    for evidence in audit['evidence']:
        path = Path(evidence['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe attribution evidence path')
        source = (root / path).read_bytes()
        if digest(source) != evidence['sha256']:
            raise ValueError('Attribution primary evidence changed')
        element = ET.fromstring(source)
        if path.name == 'edition.xml':
            if 'DIOPHANTUS' not in ''.join(element.itertext()) or 'PSEUDEPIGRAPHUS' not in ''.join(element.itertext()):
                raise ValueError('The edition no longer identifies the pseudepigraphic work')
        elif element.attrib.get('urn') != CTS:
            raise ValueError('The official work identity differs')
    if audit['work'] != WORK or audit['cts'] != CTS or audit['ogc_id'] != 'ogc001159':
        raise ValueError('Attribution work identity changed')
    return audit


def attribution(audit):
    return {'kind': 'pseudepigraphic', 'cts': CTS, 'year': None, 'place': None,
            'evidence': {'path': AUDIT, 'sha256': AUDIT_SHA}}


def derive(root, *, undo=False):
    audit = declaration(root)
    before = {name: load(root, name) for name in FILES}
    reg = Registry.load(root / FILES[0])
    wk = reg.works[WORK]
    idx = before[FILES[2]]['works'][WORK]
    if (wk.aliases.get('cts') != CTS or idx['id'] != audit['ogc_id']
            or idx['work_anchors'].get('cts') != CTS):
        raise ValueError('The retained work anchors changed')
    old, new = audit['original'], audit['corrected']
    if not same({k:v for k,v in idx.items() if k not in ('author','attribution')}, old['work_identity']) or not same({k:v for k,v in before[FILES[0]]['works'][WORK].items() if k not in ('author','tags','attribution')}, old['registry_identity']):
        raise ValueError('The complete retained work identity or types changed')
    block = attribution(audit)
    if new['author_slug'] in before[FILES[0]]['authors'] and not same(before[FILES[0]]['authors'][new['author_slug']], {'name':new['author_name'], 'aliases':{}}):
        raise ValueError('The complete name-only author identity changed')
    original = (wk.author == old['registry_author'] and same(wk.tags, old['registry_tags'])
                and wk.attribution is None and 'attribution' not in before[FILES[0]]['works'][WORK] and same(idx['author'], old['index_author'])
                and 'attribution' not in idx)
    ledger = Ledger.load(root / FILES[1], AUTHOR_PREFIX)
    known = ledger.current_slug_to_id().get(new['author_slug'])
    corrected_author = {'slug': new['author_slug'], 'name': new['author_name'],
                        'authorities': new['authorities'], 'id': known}
    corrected = (wk.author == new['author_slug'] and same(wk.tags, new['registry_tags'])
                 and same(wk.attribution, block) and same(idx['author'], corrected_author)
                 and same(idx.get('attribution'), block))
    if not (original or corrected):
        raise ValueError('The exact original/corrected attribution no longer matches')
    after_index = copy.deepcopy(before[FILES[2]])
    target = after_index['works'][WORK]
    active = {e['slug'] for e in ledger.entries.values() if e['status'] == 'served'}
    if undo:
        wk.author, wk.tags, wk.attribution = old['registry_author'], old['registry_tags'], None
        target['author'] = old['index_author']
        target.pop('attribution', None)
        if known:
            ledger.refresh_status(active - {new['author_slug']})
        # The new name-only author remains in the append-only registry. Its
        # opaque ID is tombstoned, never removed or allocated to another agent.
    else:
        reg.mint_author(new['author_name'], slug=new['author_slug'], aliases={})
        if reg.authors[new['author_slug']].aliases:
            raise ValueError('The pseudepigraphic label acquired personal authorities')
        ledger.mint_missing({new['author_slug']})
        ledger.refresh_status(active | {new['author_slug']})
        author_id = ledger.current_slug_to_id()[new['author_slug']]
        wk.author, wk.tags, wk.attribution = new['author_slug'], new['registry_tags'], block
        target['author'] = dict(corrected_author, id=author_id)
        target['attribution'] = block
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'registry.json'
        reg.save(path)
        native_reg = json.loads(path.read_bytes())
    # Registry.save fills omitted Edition defaults. Preserve that public
    # absence/null distinction by transporting only the native changed fields.
    after_reg = copy.deepcopy(before[FILES[0]])
    for field in ('author', 'tags'):
        after_reg['works'][WORK][field] = native_reg['works'][WORK][field]
    if undo:
        after_reg['works'][WORK].pop('attribution', None)
    else:
        after_reg['works'][WORK]['attribution'] = native_reg['works'][WORK]['attribution']
        after_reg['authors'][new['author_slug']] = native_reg['authors'][new['author_slug']]
    used_authors = author_slugs_for_served(set(after_index['works']), after_reg['works'], {})
    if undo and new['author_slug'] in used_authors:
        ledger.refresh_status(active | {new['author_slug']})
    # Keep the native ledger's field order even after a previous local JSON
    # serializer changed key order; this does not change any field or value.
    for ident, record in ledger.entries.items():
        ledger.entries[ident] = {k:record[k] for k in ('slug','former_slugs','status') if k in record} | {k:v for k,v in record.items() if k not in ('slug','former_slugs','status')}
    after = {FILES[0]: after_reg, FILES[1]: ledger.to_json('authors'), FILES[2]: after_index}
    # Exhaustive finite scope: retain every foreign work and old agent exactly.
    for slug, record in before[FILES[0]]['works'].items():
        if slug != WORK and not same(after_reg['works'][slug], record):
            raise ValueError('Foreign registry work changed: ' + slug)
    for slug, record in before[FILES[0]]['authors'].items():
        if not same(after_reg['authors'][slug], record):
            raise ValueError('Foreign registry author changed: ' + slug)
    for slug, record in before[FILES[2]]['works'].items():
        if slug != WORK and not same(after_index['works'][slug], record):
            raise ValueError('Foreign work index changed: ' + slug)
    if {k: v for k, v in idx.items() if k not in ('author', 'attribution')} != {
            k: v for k, v in target.items() if k not in ('author', 'attribution')}:
        raise ValueError('Non-attribution work metadata changed')
    for ident, record in before[FILES[1]]['authors'].items():
        if record['slug'] != new['author_slug'] and not same(after[FILES[1]]['authors'][ident], record):
            raise ValueError('Foreign opaque agent changed: ' + ident)
    return before, after


def replay(root=ROOT, *, apply=False, undo=False, check=False):
    before, after = derive(Path(root), undo=undo)
    changed = [name for name in FILES if not same(before[name], after[name])]
    if check and changed:
        raise ValueError('Attribution replay required: ' + ', '.join(changed))
    if apply:
        for name in FILES:
            (Path(root) / name).write_text(json.dumps(after[name], ensure_ascii=False, sort_keys=(name != FILES[1]), indent=1) + ('\n' if name != FILES[1] else ''))
    # Reproduce the existing public comparison/provenance projection with
    # its native owner; never edit a derived identity hash by hand.
    if (Path(root) / 'data/reference/bilby-oga-glaux-2024/manifest.json').exists():
        from compare_oga_glaux_dates import generate
        for relative, raw in generate(Path(root), published_projection=True).items():
            path = Path(root) / relative
            if path.read_bytes() != raw:
                if check:
                    raise ValueError('Native reference provenance replay required: ' + str(relative))
                changed.append(str(relative))
                if apply:
                    path.write_bytes(raw)
    return {'work': WORK, 'undo': undo, 'applied': apply, 'changed': changed,
            'evidence_sha256': AUDIT_SHA, 'text_or_token_changes': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--undo', action='store_true')
    args = parser.parse_args()
    print(json.dumps(replay(apply=args.apply, undo=args.undo, check=args.check), ensure_ascii=False))
