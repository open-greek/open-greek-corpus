"""Strict predecessor views for frozen Photius validators and current reports.

Only the exact newest corpus postimage is reversed. Older validators receive
the exact preceding corpus bytes, while every other input remains the actual
repository file. No historical recipe or artifact is rewritten.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import gzip
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path('data/corpus/photius.bibliotheca.jsonl')
ALIASES = Path('data/passage_aliases.json')
ARCHIVE = Path('data/corpus_changes/photius-bekker-editorial-continuation')
AUDIT = ARCHIVE/'changes.json'
TAG = 'photius_editorial_continuation'
FINAL_ARCHIVE = Path('data/corpus_changes/photius-bekker-final-review')
FINAL_AUDIT = FINAL_ARCHIVE/'changes.json'
FINAL_TAG = 'photius_final_review'
_VALIDATED_ALIAS_FILES = ContextVar('validated_photius_alias_files', default={})


def _pins(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def _overlay(source, destination, overrides):
    """Materialize only overridden ancestors; all other inputs are links."""
    for child in source.iterdir():
        target = destination/child.name
        matched = {parts[1:]: raw for parts,raw in overrides.items() if parts[0] == child.name}
        if not matched:
            target.symlink_to(child, target_is_directory=child.is_dir())
        elif () in matched:
            target.write_bytes(matched[()])
        else:
            if not child.is_dir():
                raise ValueError('Predecessor corpus has a non-directory ancestor')
            target.mkdir(); _overlay(child, target, matched)


@contextmanager
def prior_alias_view(root=ROOT):
    """Expose exact earlier aliases after checking a later unrelated extension.

    Frozen Photius recipes own their historical whole-file alias pin. The
    Phoenix authority proves that its new aliases leave every old entry
    unchanged; only those later additions are hidden from the old validators.
    """
    root = Path(root).absolute()
    phoenix = root/'data/corpus_changes/phoenix-crusius-review'
    if not (phoenix/'changes.json').exists():
        primary = root/'data/corpus/phoenix.fragmenta.jsonl'
        if ((root/ALIASES).resolve() in _VALIDATED_ALIAS_FILES.get()
                or primary.exists() and (b'"crusius_source_review"' in primary.read_bytes()
                    or b'crusius-1894-source-reviewed' in primary.read_bytes())):
            raise ValueError('Reviewed Phoenix aliases require their frozen authority')
        yield root
        return
    from repair_phoenix_crusius import verify, sha, ORIGINAL_SHA256, PRIMARY, RETAINED
    def snapshot():
        return (_pins(phoenix), (root/ALIASES).read_bytes(),
            tuple((p, sha((root/p).read_bytes()) if (root/p).is_file() else None)
                  for p in (PRIMARY, RETAINED)))
    initial = snapshot()
    before_raw = (phoenix/'before.json.gz').read_bytes()
    before = json.loads(gzip.decompress(before_raw))
    previous = before[ALIASES.as_posix()].encode()
    current = initial[1]
    aliases_file = (root/ALIASES).resolve()
    authorized = aliases_file in _VALIDATED_ALIAS_FILES.get()
    if authorized and (initial[0], initial[2], current) != _VALIDATED_ALIAS_FILES.get()[aliases_file]:
        raise ValueError('An authorized historical alias view changed its source authority')
    restored = False
    if current == previous and not authorized:
        audit = json.loads((phoenix/'changes.json').read_bytes())
        core = {PRIMARY, RETAINED, ALIASES.as_posix()}
        original = audit.get('inputs', {})
        actual = dict(initial[2], **{ALIASES.as_posix():sha(current)})
        restored = (set(original) == core and original.get(PRIMARY) == ORIGINAL_SHA256
            and original.get(RETAINED) is None and actual == original
            and sha(before_raw) == audit['outputs']['data/corpus_changes/phoenix-crusius-review/before.json.gz']
            and set(before) == core and all((sha(value.encode()) if value is not None else None)
                == original[path] for path,value in before.items()))
    if authorized or restored:
        if current != previous:
            raise ValueError('An authorized historical alias view changed its literal bytes')
    else:
        verify(root)
    if snapshot() != initial:
        raise ValueError('Later citation authority changed during predecessor validation')
    try:
        if authorized or restored:
            yield root
        else:
            with tempfile.TemporaryDirectory(prefix='photius-alias-predecessor-') as directory:
                view = Path(directory)
                _overlay(root, view, {ALIASES.parts: previous})
                token = _VALIDATED_ALIAS_FILES.set({**_VALIDATED_ALIAS_FILES.get(),
                    (view/ALIASES).resolve(): (initial[0], initial[2], previous)})
                try:
                    yield view
                    if (view/ALIASES).read_bytes() != previous:
                        raise ValueError('Historical alias bytes changed during predecessor validation')
                finally:
                    _VALIDATED_ALIAS_FILES.reset(token)
    finally:
        if snapshot() != initial:
            raise ValueError('Later citation authority changed during predecessor validation')


@contextmanager
def _stage_view(root, *, module_name, archive, audit, tag, label):
    """Reverse one exact layer while keeping every real authority visible."""
    root = Path(root).absolute()
    if not (root/audit).exists():
        if (root/CORPUS).exists() and ('"'+tag+'"').encode() in (root/CORPUS).read_bytes():
            raise ValueError(label+' metadata has no frozen authority')
        yield root
        return
    from importlib import import_module
    layer = import_module(module_name)
    raw = (root/CORPUS).read_bytes()
    before = layer.restore_before_bytes(raw, root)
    # The metadata check also verifies live aliases; a corpus-only overlay
    # cannot authorize a change to them.
    layer.active_metadata(root)
    aliases = (root/ALIASES).read_bytes()
    pins = _pins(root/archive)
    try:
        if before == raw:
            yield root
        else:
            with tempfile.TemporaryDirectory(prefix='photius-predecessor-') as directory:
                view = Path(directory)
                _overlay(root, view, {CORPUS.parts: before})
                yield view
    finally:
        if ((root/CORPUS).read_bytes() != raw or (root/ALIASES).read_bytes() != aliases
                or _pins(root/archive) != pins):
            raise ValueError(label+' inputs changed during predecessor validation')


@contextmanager
def continuation_view(root=ROOT):
    """Expose the exact continuation postimage to its frozen validators."""
    with prior_alias_view(root) as alias_root:
        with _stage_view(alias_root, module_name='repair_photius_final_review',
                         archive=FINAL_ARCHIVE, audit=FINAL_AUDIT,
                         tag=FINAL_TAG, label='Final review') as previous:
            yield previous


@contextmanager
def predecessor_view(root=ROOT):
    """Expose the first-editorial stage after checking both later layers."""
    with continuation_view(root) as continuation_root:
        with _stage_view(continuation_root,
                         module_name='repair_photius_editorial_continuation',
                         archive=ARCHIVE, audit=AUDIT, tag=TAG,
                         label='Continuation') as previous:
            yield previous


def continuation_metadata(root=ROOT):
    with continuation_view(root) as previous:
        if not (previous/AUDIT).exists():
            if (previous/CORPUS).exists() and ('"'+TAG+'"').encode() in (previous/CORPUS).read_bytes():
                raise ValueError('Continuation metadata has no frozen authority')
            return None
        from repair_photius_editorial_continuation import active_metadata
        return active_metadata(previous)


def final_metadata(root=ROOT):
    root = Path(root)
    if not (root/FINAL_AUDIT).exists():
        if (root/CORPUS).exists() and ('"'+FINAL_TAG+'"').encode() in (root/CORPUS).read_bytes():
            raise ValueError('Final review metadata has no frozen authority')
        return None
    from repair_photius_final_review import active_metadata
    with prior_alias_view(root) as previous:
        return active_metadata(previous)


def later_metadata(root=ROOT, *, current_root=None):
    from repair_photius_complete_review import later_metadata as previous_metadata
    if current_root is None:
        with predecessor_view(root) as previous:
            result = previous_metadata(previous)
    else:
        result = previous_metadata(root)
    result = deepcopy(result)
    latest = continuation_metadata(root if current_root is None else current_root)
    if latest:
        result['editorial_continuation'] = latest
    final = final_metadata(root if current_root is None else current_root)
    if final:
        result['final_review'] = final
    return result


def _continuation_measurement(later):
    from repair_photius_complete_review import current_uncertainty_measurement as previous_measurement
    result = previous_measurement(later)
    latest = later.get('editorial_continuation')
    if not latest:
        return result
    previous = later.get('editorial_substitutions')
    if not result or not previous:
        raise ValueError('Continuation measurement requires its exact editorial predecessor')
    counts = latest['counts']; count = counts['newly_editorially_substituted_spans']
    if type(count) is not int:
        raise ValueError('Continuation count must be an exact integer')
    identities = [(x['locus'],x['segment_index']) for x in counts['substituted_identities']]
    old_identities = {(x['locus'],x['segment_index']) for x in previous['counts']['substituted_identities']}
    earlier = later.get('uncertainty_admission', {}).get('counts', {}).get('resolved_identities', [])
    old_identities.update((x['locus'],x['segment_index']) for x in earlier)
    remaining = result['current_uncertainty_spans']-count
    if (count < 0 or remaining < 0
            or counts['previous_current_uncertainty_spans'] != result['current_uncertainty_spans']
            or counts['scan_uncertainty_spans'] != result['scan_uncertainty_spans']
            or counts['editorially_substituted_spans'] != result['editorially_substituted_spans']+count
            or counts['current_uncertainty_spans'] != remaining
            or counts['unsubstituted_source_uncertainty_spans'] != remaining
            or len(identities) != count or len(set(identities)) != count
            or set(identities).intersection(old_identities)):
        raise ValueError('Continuation counts do not extend distinct predecessor uncertainties')
    result = deepcopy(result)
    result.update(current_uncertainty_spans=remaining,
        unsubstituted_source_uncertainty_spans=remaining,
        newly_editorially_substituted_spans=count,
        fresh_source_corrections=counts.get('fresh_source_corrections',0),
        editorially_substituted_spans=counts['editorially_substituted_spans'],
        addressed_uncertainty_spans=result['baseline_uncertainty_spans']-remaining,
        previous_editorial_source_review=result['editorial_source_review'],
        editorial_source_review=latest['source_review'],source_review=latest['source_review'],
        qualification='Current served unresolved count after successive attributed editorial substitutions. Original scan uncertainties and scan-resolution counts remain historical measurements; editorial source choices are not scan verification. Independent fragment and nonbody exclusions survive unless separately source reviewed.')
    return result


def _identities(counts, name):
    values = counts[name]
    if (not isinstance(values, list) or any(not isinstance(v, dict)
            or not isinstance(v.get('locus'), str) or not v['locus']
            or type(v.get('segment_index')) is not int or v['segment_index'] < 0 for v in values)):
        raise ValueError('Final review identities need exact passage and segment keys')
    result = {(v['locus'],v['segment_index']) for v in values}
    if len(result) != len(values):
        raise ValueError('Final review repeats an uncertainty identity')
    return result


def current_uncertainty_measurement(later):
    """Extend served counts without calling nonlexical decisions substitutions."""
    result = _continuation_measurement(later)
    final = later.get('final_review')
    if not final:
        return result
    if not result or not later.get('editorial_continuation'):
        raise ValueError('Final review requires its exact continuation predecessor')
    counts = final['counts']
    names = ('previous_current_uncertainty_spans', 'current_uncertainty_spans',
             'resolved_uncertainty_spans', 'newly_editorially_substituted_spans',
             'nonlexically_classified_spans', 'editorially_substituted_spans')
    if any(type(counts.get(name)) is not int or counts[name] < 0 for name in names):
        raise ValueError('Final review counts must be nonnegative exact integers')
    resolved = _identities(counts, 'resolved_identities')
    lexical = _identities(counts, 'lexical_resolution_identities')
    nonlexical = _identities(counts, 'nonlexical_resolution_identities')
    admitted = _identities(counts, 'lexical_admitted_identities')
    earlier = set()
    for name in ('uncertainty_review', 'uncertainty_admission',
                 'editorial_substitutions', 'editorial_continuation'):
        previous_counts = later.get(name, {}).get('counts', {})
        for field in ('resolved_identities', 'substituted_identities'):
            earlier.update((v['locus'],v['segment_index']) for v in previous_counts.get(field, []))
    remaining = result['current_uncertainty_spans'] - len(resolved)
    roles = counts['resolved_by_text_role']
    scan_backed = counts.get('new_scan_backed_dispositions', 0)
    if type(scan_backed) is not int or scan_backed < 0:
        raise ValueError('Final scan-backed disposition count must be a nonnegative exact integer')
    dispositions = counts.get('dispositions')
    if dispositions is not None and (not isinstance(dispositions, dict)
            or any(not isinstance(k,str) or not k or type(v) is not int or v < 0
                   for k,v in dispositions.items())
            or sum(dispositions.values()) != counts['previous_current_uncertainty_spans']):
        raise ValueError('Final disposition counts do not account for every reviewed identity')
    if (counts['previous_current_uncertainty_spans'] != result['current_uncertainty_spans']
            or counts['resolved_uncertainty_spans'] != len(resolved)
            or counts['current_uncertainty_spans'] != remaining or remaining < 0
            or resolved.intersection(earlier) or lexical.intersection(nonlexical)
            or lexical.union(nonlexical) != resolved or not admitted.issubset(lexical)
            or counts['nonlexically_classified_spans'] != len(nonlexical)
            or counts['newly_editorially_substituted_spans'] > len(lexical)
            or counts['editorially_substituted_spans'] != result['editorially_substituted_spans'] + counts['newly_editorially_substituted_spans']
            or not isinstance(roles, dict) or any(not isinstance(k,str) or not k
                or type(v) is not int or v < 0 for k,v in roles.items())
            or sum(roles.values()) != len(resolved)):
        raise ValueError('Final review counts do not extend distinct predecessor uncertainties')
    if ('scan_uncertainty_spans' in counts
            and counts['scan_uncertainty_spans'] != result['scan_uncertainty_spans']):
        raise ValueError('Final review changed the historical scan uncertainty measurement')
    result = deepcopy(result)
    result.update(current_uncertainty_spans=remaining,
        unsubstituted_source_uncertainty_spans=remaining,
        resolved_uncertainty_spans=len(resolved),
        final_review_lexical_resolution_spans=len(lexical),
        final_review_lexically_admitted_spans=len(admitted),
        final_review_scan_backed_dispositions=scan_backed,
        nonlexically_classified_spans=len(nonlexical),
        resolved_by_text_role=deepcopy(roles),
        newly_editorially_substituted_spans=counts['newly_editorially_substituted_spans'],
        editorially_substituted_spans=counts['editorially_substituted_spans'],
        addressed_uncertainty_spans=result['baseline_uncertainty_spans']-remaining,
        previous_source_review=result['source_review'],
        final_source_review=final['source_review'], source_review=final['source_review'],
        qualification='Current served uncertainty count after exact final source decisions. Greek reading resolutions and lexical admission are counted separately from classified references or other nonlexical material. Historical scan uncertainties and earlier scan resolutions remain unchanged; only explicitly attributed editorial word choices increase the editorial substitution count. Original readings, exclusions, and earlier authorities remain reversible.')
    if counts['newly_editorially_substituted_spans']:
        result.update(previous_editorial_source_review=result['editorial_source_review'],
                      editorial_source_review=final['source_review'])
    if dispositions is not None:
        result['final_review_dispositions'] = deepcopy(dispositions)
    return result
