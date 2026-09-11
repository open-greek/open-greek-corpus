#!/usr/bin/env python3
"""Where the upstream OCR correction pipeline is checked out, if it is.

This repository holds the corrected text. The pipeline that produces it, the raw
OCR, and the reversible correction store are a separate checkout, and a handful of
things here can use it when it happens to be present: two tests cross-check a
vendored rule against the implementation it was copied from, and a couple of
measurements read the census gate files.

None of them may REQUIRE it, because this repository has to build and test from a
fresh clone on its own. And none of them names it, because it is private: a path
naming it is a dead end for anyone outside and says that it exists. So the name
lives in one environment variable in a developer's shell and nowhere in the tree.

    export OCR_PIPELINE=/path/to/the/pipeline/checkout

Callers ask for what they need and handle None by skipping:

    from upstream_pipeline import upstream
    precision = upstream("data/precision")
    if precision is None:
        ...                     # no checkout; do without it
"""

from __future__ import annotations

import os
from pathlib import Path

ENV = "OCR_PIPELINE"

WHY = (f"set {ENV} to the upstream OCR pipeline checkout to enable this; it is a "
       f"separate repository and nothing here requires it")


def root() -> Path | None:
    """The pipeline checkout, or None when the environment does not name one."""
    named = os.environ.get(ENV)
    if not named:
        return None
    path = Path(os.path.expanduser(named))
    return path if path.is_dir() else None


def upstream(*parts: str) -> Path | None:
    """A path inside the pipeline checkout, or None when it is absent.

    Returns None rather than a path that does not exist, so a caller that tests the
    result covers both "no checkout" and "a checkout without this in it".
    """
    base = root()
    if base is None:
        return None
    path = base.joinpath(*parts)
    return path if path.exists() else None
