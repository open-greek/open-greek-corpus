"""Checked alias predecessors for later independent source-role admissions.

An alias overlay is usable only while its complete source authority and current
core files remain unchanged. Earlier adapters may inherit that proof for another
literal alias predecessor after independently validating their own layer.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ALIASES = Path("data/passage_aliases.json")
AUDIT = Path("data/corpus_changes/editorial-role-review")
_VALIDATED_ALIAS_FILES = ContextVar("validated_later_citation_alias_files", default={})


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pins(directory):
    return {path.relative_to(directory).as_posix(): _sha(path.read_bytes())
            for path in sorted(directory.rglob("*")) if path.is_file()}


def _overlay(source, destination, overrides):
    for child in source.iterdir():
        target = destination / child.name
        matched = {parts[1:]: raw for parts, raw in overrides.items() if parts[0] == child.name}
        if not matched:
            target.symlink_to(child, target_is_directory=child.is_dir())
        elif () in matched:
            target.write_bytes(matched[()])
        else:
            if not child.is_dir():
                raise ValueError("Citation predecessor has a non-directory ancestor")
            target.mkdir()
            _overlay(child, target, matched)


def _role_module():
    import repair_editorial_roles
    return repair_editorial_roles


def _snapshot(root):
    role = _role_module()
    return (_pins(root / AUDIT),
        tuple((path, _sha((root / path).read_bytes()) if (root / path).is_file() else None)
              for path in sorted(role.CORE - {role.ALIASES})),
        (root / ALIASES).read_bytes())


def _verify_role(root):
    return _role_module().verify(root)


def _missing_authority_is_reviewed(root):
    role = _role_module()
    if (root / ALIASES).resolve() in _VALIDATED_ALIAS_FILES.get():
        return True
    if any((root / path).exists() for path in role.RETAINED.values()):
        return True
    for work, path in role.PRIMARY.items():
        if (root / path).exists():
            raw = (root / path).read_bytes()
            if b'"editorial_role_review"' in raw or _sha(raw) != role.ORIGINAL_SHA256[work]:
                return True
    return False


def _exact_undo(root, audit, before_raw, before, initial):
    role = _role_module()
    inputs = audit.get("inputs", {})
    if set(inputs) != role.CORE or set(before) != role.CORE:
        return False
    if any(inputs.get(role.PRIMARY[work]) != digest for work, digest in role.ORIGINAL_SHA256.items()):
        return False
    if inputs.get(role.ALIASES) != role.ORIGINAL_ALIASES_SHA256:
        return False
    if any(inputs.get(path) is not None for path in role.RETAINED.values()):
        return False
    current = dict(initial[1], **{role.ALIASES: _sha(initial[2])})
    return (current == inputs
        and _sha(before_raw) == audit["outputs"][(AUDIT / "before.json.gz").as_posix()]
        and all((_sha(text.encode()) if text is not None else None) == inputs[path]
                for path, text in before.items()))


@contextmanager
def phoenix_alias_view(root=ROOT):
    """Expose the exact Phoenix-era aliases after checking the later role review."""
    root = Path(root).absolute()
    if not (root / AUDIT / "changes.json").exists():
        if _missing_authority_is_reviewed(root):
            raise ValueError("Reviewed editorial roles require their frozen citation authority")
        yield root
        return
    initial = _snapshot(root)
    before_raw = (root / AUDIT / "before.json.gz").read_bytes()
    before = json.loads(gzip.decompress(before_raw))
    previous = before[ALIASES.as_posix()].encode()
    aliases_file = (root / ALIASES).resolve()
    binding = _VALIDATED_ALIAS_FILES.get().get(aliases_file)
    if binding is not None and initial != binding:
        raise ValueError("An authorized citation view changed its source authority")
    restored = False
    if binding is None and initial[2] == previous:
        audit = json.loads((root / AUDIT / "changes.json").read_bytes())
        restored = _exact_undo(root, audit, before_raw, before, initial)
    if binding is None and not restored:
        _verify_role(root)
    if _snapshot(root) != initial:
        raise ValueError("Editorial citation authority changed during predecessor validation")
    try:
        if binding is not None or restored:
            token = _VALIDATED_ALIAS_FILES.set({**_VALIDATED_ALIAS_FILES.get(), aliases_file: initial})
            try:
                yield root
            finally:
                _VALIDATED_ALIAS_FILES.reset(token)
        else:
            with tempfile.TemporaryDirectory(prefix="citation-alias-predecessor-") as directory:
                view = Path(directory)
                _overlay(root, view, {ALIASES.parts: previous})
                proof = (initial[0], initial[1], previous)
                token = _VALIDATED_ALIAS_FILES.set({**_VALIDATED_ALIAS_FILES.get(),
                    (view / ALIASES).resolve(): proof})
                try:
                    yield view
                    if (view / ALIASES).read_bytes() != previous:
                        raise ValueError("Historical citation bytes changed during predecessor validation")
                finally:
                    _VALIDATED_ALIAS_FILES.reset(token)
    finally:
        if _snapshot(root) != initial:
            raise ValueError("Editorial citation authority changed during predecessor validation")


@contextmanager
def inherit_alias_authority(source, destination, expected_aliases):
    """Carry a live proof into an independently validated older alias overlay."""
    source, destination = Path(source).absolute(), Path(destination).absolute()
    binding = _VALIDATED_ALIAS_FILES.get().get((source / ALIASES).resolve())
    if binding is None:
        yield destination
        return
    original = _snapshot(source)
    current = _snapshot(destination)
    if (original != binding or current[:2] != original[:2]
            or current[2] != expected_aliases):
        raise ValueError("Inherited citation view changed its source authority")
    token = _VALIDATED_ALIAS_FILES.set({**_VALIDATED_ALIAS_FILES.get(),
        (destination / ALIASES).resolve(): current})
    try:
        yield destination
    finally:
        _VALIDATED_ALIAS_FILES.reset(token)
        if _snapshot(source) != original or _snapshot(destination) != current:
            raise ValueError("Inherited citation authority changed during predecessor validation")
