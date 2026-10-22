#!/usr/bin/env python3
"""Present the checked Herodas predecessor to the frozen source-role review.

The body recovery owns only the Herodas primary. Citation aliases and the older
source-role archives retain their separate authorities.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "data/corpus/herodas.mimiambi.jsonl"
AUDIT = "data/corpus_changes/herodas-headlam-knox-body"
PREDECESSOR_SHA256 = "b50c5d810cac0a8a44a2acdd567aa1c7f7e7266e83698325122501b0656e68ef"
ORIGINAL_SHA256 = "266915ced62896c3503c2ae0bb59bfc202a7e25dfe6c8ff1035313cdfaa00274"
_VALIDATED_PRIMARY_FILES = ContextVar("validated_herodas_predecessor_files", default={})
_ACTIVE_AUTHORITIES = ContextVar("active_herodas_body_authorities", default={})


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _body_module():
    import repair_herodas_body
    return repair_herodas_body


def _file_pins(root, paths):
    return tuple((path, _sha((root / path).read_bytes()) if (root / path).is_file() else None)
                 for path in sorted(paths))


def _archive_paths(root, relative):
    return {path.relative_to(root).as_posix() for path in (root / relative).rglob("*")
            if path.is_file()}


def _authority_snapshot(root):
    """Pin live evidence before verification, including any external scan."""
    import repair_editorial_roles as roles
    body = _body_module()
    paths = set(body.authority_paths(root)) - {PRIMARY}
    paths.update(_archive_paths(root, roles.AUDIT))
    paths.update(roles.CORE - {roles.ALIASES, PRIMARY})
    return (_file_pins(root, paths), tuple(sorted(body.recipe_pins().items())),
            tuple(sorted(roles.recipe_pins().items())), _sha(Path(__file__).read_bytes()))


def _snapshot(root):
    return _authority_snapshot(root), _file_pins(root, {PRIMARY})


def _literal_snapshot(root):
    """Literal undo must remain usable after a correction source is removed."""
    from citation_alias_state import _literal_snapshot as role_snapshot
    return (_file_pins(root, {PRIMARY, AUDIT + "/changes.json", AUDIT + "/before.json.gz"}),
            role_snapshot(root) if (root / "data/corpus_changes/editorial-role-review/changes.json").is_file()
            else None)


def _missing_authority_is_recovered(root):
    path = root / PRIMARY
    if path.resolve() in _VALIDATED_PRIMARY_FILES.get():
        return True
    if not path.is_file():
        return False
    raw = path.read_bytes()
    if b'"herodas_body_recovery"' in raw:
        return True
    digest = _sha(raw)
    if digest in {PREDECESSOR_SHA256, ORIGINAL_SHA256}:
        return False
    return True


def _literal_before(root):
    body = _body_module()
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("inputs") != {PRIMARY: PREDECESSOR_SHA256}
            or set(body.CORE) != {PRIMARY}):
        raise ValueError("Herodas body recovery predecessor identity changed")
    before = body._before(root, audit)
    if (set(before) != {PRIMARY} or not isinstance(before[PRIMARY], str)
            or _sha(before[PRIMARY].encode()) != PREDECESSOR_SHA256):
        raise ValueError("Herodas body recovery literal predecessor changed")
    return audit, before


def _is_unapplied(root, before):
    if (root / PRIMARY).is_file() and (root / PRIMARY).read_bytes() == before[PRIMARY].encode():
        return True
    from citation_alias_state import role_is_unapplied
    return role_is_unapplied(root)


def body_is_unapplied(root):
    """Recognize literal body undo and the separately proved earlier undo epochs."""
    root = Path(root).absolute()
    if not (root / AUDIT / "changes.json").is_file():
        return False
    initial = _literal_snapshot(root)
    _, before = _literal_before(root)
    result = _is_unapplied(root, before)
    if _literal_snapshot(root) != initial:
        raise ValueError("Herodas literal authority changed during undo recognition")
    return result


@contextmanager
def role_predecessor_view(root=ROOT):
    """Expose exactly the 62-row role postimage while its later proof is live."""
    root = Path(root).absolute()
    path = root / AUDIT / "changes.json"
    if not path.is_file():
        if _missing_authority_is_recovered(root):
            raise ValueError("Recovered Herodas text requires its frozen body authority")
        initial = _file_pins(root, {PRIMARY, AUDIT + "/changes.json"})
        try:
            yield root
        finally:
            if _file_pins(root, {PRIMARY, AUDIT + "/changes.json"}) != initial:
                raise ValueError("Herodas admission changed during predecessor validation")
        return

    literal_initial = _literal_snapshot(root)
    audit, before = _literal_before(root)
    primary_file = (root / PRIMARY).resolve()
    binding = _VALIDATED_PRIMARY_FILES.get().get(primary_file)
    authority_file = path.resolve()
    active_authority = _ACTIVE_AUTHORITIES.get().get(authority_file)

    if binding is not None:
        initial = _snapshot(root)
        if initial != binding:
            raise ValueError("An authorized Herodas view changed its source authority")
    elif active_authority is not None:
        # Materializing another file with the same predecessor bytes cannot
        # detach a nested view from its outer source proof.
        initial = _snapshot(root)
        if initial[0] != active_authority:
            raise ValueError("A nested Herodas view changed its source authority")
    else:
        initial = None

    restored = binding is None and _is_unapplied(root, before)
    if restored:
        if _literal_snapshot(root) != literal_initial:
            raise ValueError("Herodas literal authority changed during undo recognition")
        try:
            yield root
        finally:
            if _literal_snapshot(root) != literal_initial:
                raise ValueError("Herodas literal authority changed during predecessor validation")
        return

    if initial is None:
        initial = _snapshot(root)
    if binding is None:
        _body_module().verify(root)
    if _snapshot(root) != initial or _literal_snapshot(root) != literal_initial:
        raise ValueError("Herodas source authority changed during predecessor validation")
    try:
        if binding is not None:
            yield root
        else:
            from citation_alias_state import _overlay
            with tempfile.TemporaryDirectory(prefix="herodas-body-predecessor-") as directory:
                view = Path(directory)
                previous = before[PRIMARY].encode()
                _overlay(root, view, {Path(PRIMARY).parts: previous})
                proof = (initial[0], ((PRIMARY, _sha(previous)),))
                primary_token = _VALIDATED_PRIMARY_FILES.set({**_VALIDATED_PRIMARY_FILES.get(),
                    (view / PRIMARY).resolve(): proof})
                authority_token = _ACTIVE_AUTHORITIES.set({**_ACTIVE_AUTHORITIES.get(),
                    authority_file: initial[0]})
                try:
                    yield view
                    if _snapshot(view) != proof:
                        raise ValueError("Historical Herodas bytes or authority changed during predecessor validation")
                finally:
                    _ACTIVE_AUTHORITIES.reset(authority_token)
                    _VALIDATED_PRIMARY_FILES.reset(primary_token)
    finally:
        if _snapshot(root) != initial:
            raise ValueError("Herodas source authority changed during predecessor validation")


def verify_roles(root, *, active=True):
    import repair_editorial_roles as frozen
    with role_predecessor_view(root) as previous:
        return frozen.verify(previous, active=active)


def check_roles(root):
    import repair_editorial_roles as frozen
    with role_predecessor_view(root) as previous:
        return frozen.run(previous, "check")


def projection_signature(root):
    """Content pins also invalidate projections cached by earlier adapters."""
    root = Path(root).absolute()
    paths = {PRIMARY, AUDIT + "/changes.json", AUDIT + "/before.json.gz"}
    paths.update(_archive_paths(root, AUDIT))
    recipes = {"herodas_current_state.py": _sha(Path(__file__).read_bytes())}
    if (root / AUDIT / "changes.json").is_file():
        body = _body_module()
        paths.update(body.authority_paths(root))
        recipes.update(body.recipe_pins())
    return _file_pins(root, paths), tuple(sorted(recipes.items()))


def _role_projection_signature(root):
    import repair_editorial_roles as roles
    paths = {*roles.CORE, *_archive_paths(root, roles.AUDIT)}
    return (_file_pins(root, paths), tuple(sorted(roles.recipe_pins().items())),
            projection_signature(root))


@lru_cache(maxsize=4)
def _role_projections(root_name, signature):
    import repair_editorial_roles as frozen
    root = Path(root_name)
    with role_predecessor_view(root) as previous:
        rows = [json.loads(line) for line in (previous / PRIMARY).read_bytes().splitlines()]
        result = {row["locus"]: (row, frozen.lexical_segments(row, previous)) for row in rows
                  if row.get("editorial_role_review")}
    if _role_projection_signature(root) != signature:
        raise ValueError("Herodas inputs changed while caching role projections")
    return result


def role_lexical_segments(row, root=None):
    root = Path(ROOT if root is None else root).absolute()
    expected = _role_projections(str(root), _role_projection_signature(root)).get(row["locus"])
    if expected is None or expected[0] != row:
        raise ValueError("Herodas lexical row differs from its reviewed role postimage")
    return deepcopy(expected[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    check_roles(args.root)


if __name__ == "__main__":
    main()
