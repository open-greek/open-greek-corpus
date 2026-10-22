#!/usr/bin/env python3
"""Run the frozen Phoenix admission against its checked alias predecessor."""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import repair_phoenix_crusius as frozen
from citation_alias_state import phoenix_alias_view


def verify(root, *, active=True):
    with phoenix_alias_view(root) as previous:
        return frozen.verify(previous, active=active)


def _projection_signature(root):
    """Content pins keep the cache independent of timestamps and temporary paths."""
    import repair_editorial_roles as roles
    paths = {frozen.PRIMARY, frozen.RETAINED, frozen.ALIASES, *roles.CORE}
    for directory in (frozen.AUDIT, roles.AUDIT):
        paths.update(path.relative_to(root).as_posix()
                     for path in (root / directory).rglob("*") if path.is_file())
    files = tuple((path, hashlib.sha256((root / path).read_bytes()).hexdigest()
                   if (root / path).is_file() else None) for path in sorted(paths))
    scripts = Path(__file__).resolve().parent
    recipes = {**frozen.recipe_pins(), **roles.recipe_pins(),
        **{name: hashlib.sha256((scripts / name).read_bytes()).hexdigest()
           for name in ("phoenix_current_state.py", "citation_alias_state.py")}}
    return files, tuple(sorted(recipes.items()))


@lru_cache(maxsize=4)
def _lexical_projections(root_name, signature):
    root = Path(root_name)
    rows = [json.loads(line) for line in (root / frozen.PRIMARY).read_bytes().splitlines()]
    with phoenix_alias_view(root) as previous:
        # One live context keeps the frozen verifier's own cache useful across
        # all 21 rows. No temporary view or context authorization survives here.
        projections = {row["locus"]: (row, frozen.lexical_segments(row, previous)) for row in rows}
    if _projection_signature(root) != signature:
        raise ValueError("Phoenix source inputs changed while caching lexical projections")
    return projections


def lexical_segments(row, root=None):
    root = Path(frozen.ROOT if root is None else root).absolute()
    signature = _projection_signature(root)
    expected = _lexical_projections(str(root), signature).get(row["locus"])
    if expected is None or expected[0] != row:
        raise ValueError("Phoenix lexical row differs from its scan-reviewed postimage")
    return deepcopy(expected[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=frozen.ROOT)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    audit, _, _ = verify(args.root)
    print(json.dumps(audit["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
