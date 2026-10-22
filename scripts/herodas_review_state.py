"""Expose the checked published body beneath later Herodas proofreading.

The current reading authority remains live through nested body, role, and alias
views. Literal chronological undo needs only the pinned preimage archives.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "data/corpus/herodas.mimiambi.jsonl"
AUDIT = "data/corpus_changes/herodas-reading-review"
PREDECESSOR_SHA256 = "4f604f16151fdc8748dabdd973feacf040a8a6f49170870173df5c3c07fac939"
_VALIDATED_PRIMARY_FILES = ContextVar("validated_herodas_reading_predecessors", default={})
_ACTIVE_AUTHORITIES = ContextVar("active_herodas_reading_authorities", default={})


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _module():
    import repair_herodas_readings
    return repair_herodas_readings


def _file_pins(root, paths):
    return tuple((path, _sha((root / path).read_bytes()) if (root / path).is_file() else None)
                 for path in sorted(paths))


def _authority_snapshot(root):
    from herodas_current_state import _authority_snapshot as body_authority
    module = _module()
    paths = set(module.authority_paths(root)) - {PRIMARY}
    return (_file_pins(root, paths), tuple(sorted(module.recipe_pins().items())),
            body_authority(root), _sha(Path(__file__).read_bytes()))


def _snapshot(root):
    return _authority_snapshot(root), _file_pins(root, {PRIMARY})


def _literal_snapshot(root):
    from herodas_current_state import _literal_snapshot as body_literal
    return (_file_pins(root, {PRIMARY, AUDIT + "/changes.json", AUDIT + "/before.json.gz"}),
            body_literal(root))


def _literal_before(root):
    module = _module()
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("inputs") != {PRIMARY: PREDECESSOR_SHA256}
            or module.INPUT_SHA256 != PREDECESSOR_SHA256 or module.PRIMARY != PRIMARY):
        raise ValueError("Herodas reading review predecessor identity changed")
    before = module._before(root, audit)
    if not isinstance(before, bytes) or _sha(before) != PREDECESSOR_SHA256:
        raise ValueError("Herodas reading review literal predecessor changed")
    return audit, before


def _is_unapplied(root, before):
    if (root / PRIMARY).is_file() and (root / PRIMARY).read_bytes() == before:
        return True
    from herodas_current_state import _body_is_unapplied
    return _body_is_unapplied(root)


def is_unapplied(root):
    root = Path(root).absolute()
    if not (root / AUDIT / "changes.json").is_file():
        return False
    initial = _literal_snapshot(root)
    _, before = _literal_before(root)
    result = _is_unapplied(root, before)
    if _literal_snapshot(root) != initial:
        raise ValueError("Herodas reading literal authority changed during undo recognition")
    return result


def review_is_unapplied(root):
    return is_unapplied(root)


def _missing_authority_is_reviewed(root):
    from herodas_current_state import ORIGINAL_SHA256, PREDECESSOR_SHA256 as ROLE_SHA256
    path = root / PRIMARY
    if path.resolve() in _VALIDATED_PRIMARY_FILES.get():
        return True
    if not path.is_file():
        return False
    raw = path.read_bytes()
    if b'"herodas_reading_review"' in raw:
        return True
    digest = _sha(raw)
    if digest in {PREDECESSOR_SHA256, ROLE_SHA256, ORIGINAL_SHA256}:
        return False
    return True


@contextmanager
def predecessor_view(root=ROOT):
    """Present exact released body bytes while retaining their latest proof."""
    root = Path(root).absolute()
    authority = root / AUDIT / "changes.json"
    if not authority.is_file():
        if _missing_authority_is_reviewed(root):
            if (root / PRIMARY).is_file() and b'"herodas_reading_review"' in (root / PRIMARY).read_bytes():
                raise ValueError("Proofread Herodas text requires its reading review authority")
            raise ValueError("Unproved Herodas text requires its frozen body authority or reading review authority")
        initial = _file_pins(root, {PRIMARY, AUDIT + "/changes.json"})
        yield root
        if _file_pins(root, {PRIMARY, AUDIT + "/changes.json"}) != initial:
            raise ValueError("Herodas reading admission changed during predecessor validation")
        return

    literal_initial = _literal_snapshot(root)
    _, before = _literal_before(root)
    binding = _VALIDATED_PRIMARY_FILES.get().get((root / PRIMARY).resolve())
    authority_file = authority.resolve()
    active_authority = _ACTIVE_AUTHORITIES.get().get(authority_file)
    if binding is not None:
        initial = _snapshot(root)
        if initial != binding:
            raise ValueError("An authorized Herodas reading view changed its source authority")
    elif active_authority is not None:
        initial = _snapshot(root)
        if initial[0] != active_authority:
            raise ValueError("A nested Herodas reading view changed its source authority")
    elif _ACTIVE_AUTHORITIES.get():
        # An alias overlay may materialize an identical manifest and primary,
        # giving them new resolved paths. It still belongs to the live source
        # chain and cannot turn altered evidence into an apparent literal undo.
        initial = _snapshot(root)
        if initial[0] not in _ACTIVE_AUTHORITIES.get().values():
            raise ValueError("A materialized Herodas reading view changed its source authority")
    else:
        initial = None

    restored = binding is None and _is_unapplied(root, before)
    if restored:
        if _literal_snapshot(root) != literal_initial:
            raise ValueError("Herodas reading literal authority changed during undo recognition")
        try:
            yield root
        finally:
            if _literal_snapshot(root) != literal_initial:
                raise ValueError("Herodas reading literal authority changed during predecessor validation")
            if initial is not None and _snapshot(root) != initial:
                raise ValueError("A nested Herodas reading view changed its source authority")
        return

    if initial is None:
        initial = _snapshot(root)
    if binding is None:
        _module().verify(root)
    if _snapshot(root) != initial or _literal_snapshot(root) != literal_initial:
        raise ValueError("Herodas reading source authority changed during predecessor validation")
    try:
        if binding is not None:
            yield root
        else:
            from citation_alias_state import _overlay
            with tempfile.TemporaryDirectory(prefix="herodas-reading-predecessor-") as directory:
                view = Path(directory)
                _overlay(root, view, {Path(PRIMARY).parts: before})
                proof = (initial[0], ((PRIMARY, _sha(before)),))
                primary_token = _VALIDATED_PRIMARY_FILES.set({**_VALIDATED_PRIMARY_FILES.get(),
                    (view / PRIMARY).resolve(): proof})
                authority_token = _ACTIVE_AUTHORITIES.set({**_ACTIVE_AUTHORITIES.get(),
                    authority_file: initial[0]})
                try:
                    yield view
                    if _snapshot(view) != proof:
                        raise ValueError("Historical Herodas body bytes or reading authority changed during validation")
                finally:
                    _ACTIVE_AUTHORITIES.reset(authority_token)
                    _VALIDATED_PRIMARY_FILES.reset(primary_token)
    finally:
        if _snapshot(root) != initial:
            raise ValueError("Herodas reading source authority changed during predecessor validation")


def projection_signature(root):
    """Content pins invalidate every earlier cached view after a latest change."""
    root = Path(root).absolute()
    paths = {PRIMARY, AUDIT + "/changes.json", AUDIT + "/before.json.gz"}
    recipes = {"herodas_review_state.py": _sha(Path(__file__).read_bytes())}
    if (root / AUDIT / "changes.json").is_file():
        module = _module()
        paths.update(module.authority_paths(root))
        recipes.update(module.recipe_pins())
    return _file_pins(root, paths), tuple(sorted(recipes.items()))


def manifestation_metadata(root):
    root = Path(root)
    if not (root / AUDIT / "changes.json").is_file() or is_unapplied(root):
        return {}
    return _module().manifestation_metadata(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    _module().run(args.root, "check")


if __name__ == "__main__":
    main()
