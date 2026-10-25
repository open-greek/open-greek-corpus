"""Compose scan reading review with the unchanged missing-leaf authority."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

import repair_hesychius_missing_columns as base
import repair_hesychius_gap_readings as review

ROOT, PRIMARY, AUDIT, AUTHORITY = base.ROOT, base.PRIMARY, base.AUDIT, base.AUTHORITY
EDITION, SLUG, WITNESSES, QUALIFICATION = base.EDITION, base.SLUG, base.WITNESSES, base.QUALIFICATION
sha = base.sha
recipe_pins = base.recipe_pins


def authority_paths(root=ROOT):
    return review.authority_paths(root) | {"scripts/hesychius_gap_state.py"}


def active(root=ROOT):
    if review.active(root):
        review.checked_state(root)
        return True
    return base.active(root)


def signature(root):
    root = Path(root)
    return tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in sorted(authority_paths(root)))


@lru_cache(maxsize=2)
def _checked(root_name, initial):
    root = Path(root_name)
    if review.active(root):
        audit, before, rows = review.checked_state(root)
        with review.original_view(root, before[PRIMARY]) as view:
            original, original_before, _ = base.checked_state(view)
        current = {"authority": review.AUTHORITY, "counts": audit["counts"],
            "qualification": review.QUALIFICATION, "output_sha256": audit["outputs"][PRIMARY],
            "reading_review": {"path": review.AUTHORITY, "sha256": sha((root / review.AUTHORITY).read_bytes())}}
    else:
        original, original_before, rows = base.checked_state(root)
        current = {"authority": base.AUTHORITY, "counts": original["counts"],
            "qualification": base.QUALIFICATION, "output_sha256": original["outputs"][PRIMARY]}
    if signature(root) != initial:
        raise ValueError("Hesychius source authority changed during composition")
    return original, original_before, rows, current


def _state(root):
    root = Path(root).absolute()
    return _checked(str(root), signature(root))


def checked_state(root=ROOT):
    return deepcopy(_state(root)[:3])


def current_metadata(root=ROOT):
    return deepcopy(_state(root)[3])


def predecessor_bytes(root=ROOT):
    return _state(root)[1][PRIMARY] if active(root) else None


def recovery_postimage_bytes(root=ROOT):
    if review.active(root):
        return review.checked_state(root)[1][PRIMARY]
    base.checked_state(root)
    return (Path(root) / PRIMARY).read_bytes()


def validate_projection(row, root=ROOT):
    expected = _state(root)[2].get((row.get("urn"), row.get("locus")))
    if expected != row:
        raise ValueError("Hesychius lexical projection differs from checked recovery and reading review")
    return row["analysis_text"]


def lexical_segments(row, root=ROOT):
    validate_projection(row, root)
    return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(current_metadata(args.root)["counts"], sort_keys=True))
