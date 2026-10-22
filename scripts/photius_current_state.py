"""Strict continuation views for frozen Photius validators and current reports.

Only the exact newest corpus postimage is reversed. Older validators receive
the exact preceding corpus bytes, while every other input remains the actual
repository file. No historical recipe or artifact is rewritten.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path('data/corpus/photius.bibliotheca.jsonl')
ALIASES = Path('data/passage_aliases.json')
ARCHIVE = Path('data/corpus_changes/photius-bekker-editorial-continuation')
AUDIT = ARCHIVE/'changes.json'
TAG = 'photius_editorial_continuation'


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
def predecessor_view(root=ROOT):
    """Expose exactly the first-editorial stage, checking the latest layer first."""
    root = Path(root).absolute()
    if not (root/AUDIT).exists():
        if (root/CORPUS).exists() and ('"'+TAG+'"').encode() in (root/CORPUS).read_bytes():
            raise ValueError('Continuation metadata has no frozen authority')
        yield root
        return
    import repair_photius_editorial_continuation as continuation
    raw = (root/CORPUS).read_bytes()
    before = continuation.restore_before_bytes(raw, root)
    # Metadata validation also verifies the live alias bytes. A continuation
    # cannot authorize any alias changes through this corpus-only overlay.
    continuation.active_metadata(root)
    aliases = (root/ALIASES).read_bytes()
    pins = _pins(root/ARCHIVE)
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
                or _pins(root/ARCHIVE) != pins):
            raise ValueError('Continuation inputs changed during predecessor validation')


def continuation_metadata(root=ROOT):
    root = Path(root)
    if not (root/AUDIT).exists():
        if (root/CORPUS).exists() and ('"'+TAG+'"').encode() in (root/CORPUS).read_bytes():
            raise ValueError('Continuation metadata has no frozen authority')
        return None
    from repair_photius_editorial_continuation import active_metadata
    return active_metadata(root)


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
    return result


def current_uncertainty_measurement(later):
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
