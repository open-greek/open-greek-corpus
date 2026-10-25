#!/usr/bin/env python3
"""Verify the frozen duplicate repair beneath the later Hesychius recovery.

Only the new source authority may supply its exact predecessor. All other files
remain live inputs to the original verifier; no output or source check is waived.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import tempfile

import repair_reviewed_duplicate_blocks as base

ROOT = Path(__file__).resolve().parents[1]


def _recovery():
    import hesychius_gap_state
    return hesychius_gap_state


def authority_paths(root=ROOT):
    root = Path(root)
    path = root / base.AUDIT / "changes.json"
    names = {base.AUDIT + "/changes.json", base.AUDIT + "/before.json.gz"}
    if path.is_file():
        audit = json.loads(path.read_bytes())
        names.update(audit["inputs"])
        names.update(audit["outputs"])
        names.update("scripts/" + name for name in audit["recipe_sha256"])
        capture = json.loads((root / base.AUDIT / "source-evidence.json").read_bytes())
        names.add(base.AUDIT + "/source-evidence.json")
        names.update(item["path"] for item in capture["files"])
    recovery = _recovery()
    names.update(recovery.authority_paths(root))
    names.update("scripts/" + name for name in recovery.recipe_pins())
    names.add("scripts/reviewed_duplicate_state.py")
    return names


def signature(root):
    root = Path(root)
    return tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in sorted(authority_paths(root)))


@lru_cache(maxsize=2)
def _checked(root_name, initial):
    root = Path(root_name)
    recovery = _recovery()
    if not recovery.active(root):
        audit, before = base.verify(root, replay=True)
        predecessor = None
    else:
        _, recovered_before, _ = recovery.checked_state(root)
        predecessor = recovered_before[recovery.PRIMARY]
        old_audit = json.loads((root / base.AUDIT / "changes.json").read_bytes())
        if base.sha(predecessor) != old_audit["outputs"].get(recovery.PRIMARY):
            raise ValueError("Hesychius recovery does not preserve the frozen duplicate postimage")
        from citation_alias_state import _overlay
        with tempfile.TemporaryDirectory(prefix="reviewed-duplicate-predecessor-") as directory:
            view = Path(directory)
            _overlay(root, view, {Path(recovery.PRIMARY).parts: predecessor})
            audit, before = base.verify(view, replay=True)
    if signature(root) != initial:
        raise ValueError("Duplicate or recovery source authority changed during validation")
    rows = {(row["urn"], row["locus"]): row for name in base.PRIMARY
            for row in map(json.loads, (root / name).read_bytes().splitlines())
            if row.get("edition") == base.EDITION}
    return audit, before, predecessor, rows


def checked_state(root=ROOT):
    root = Path(root).absolute()
    audit, before, _, _ = _checked(str(root), signature(root))
    return deepcopy(audit), dict(before)


def verify(root=ROOT, *, active_only=True, replay=True):
    root = Path(root).absolute()
    if not active_only:
        # Historical source replay deliberately has no live-postimage claim.
        return base.verify(root, active_only=False, replay=replay)
    return checked_state(root)


def active(root=ROOT):
    return base.active(root)


def historical_bytes(root, path):
    if path not in base.PRIMARY or not base.active(root):
        return None
    if not _recovery().active(root):
        return base.historical_bytes(root, path)
    _, before = checked_state(root)
    return before[path]


def duplicate_postimage_bytes(root, path):
    """Return only a verified output owned by the original duplicate layer."""
    root = Path(root).absolute()
    audit, _, predecessor, _ = _checked(str(root), signature(root))
    if path not in audit["outputs"] or audit["outputs"][path] is None:
        raise ValueError("The duplicate repair does not own this postimage: " + path)
    if path == _recovery().PRIMARY and predecessor is not None:
        return predecessor
    return (root / path).read_bytes()


def validate_projection(row, root=ROOT):
    root = Path(root).absolute()
    _, _, _, rows = _checked(str(root), signature(root))
    if rows.get((row.get("urn"), row.get("locus"))) != row:
        raise ValueError("Reviewed duplicate lexical projection differs from its source authority")
    return row["analysis_text"]


def alias_fragment(root=ROOT):
    root = Path(root)
    if not base.active(root):
        return None
    checked_state(root)
    return {**json.loads((root / base.FRAGMENT).read_bytes()), "authority": {
        "path": base.AUDIT + "/changes.json",
        "sha256": base.sha((root / base.AUDIT / "changes.json").read_bytes())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root)[0]["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
