#!/usr/bin/env python3
"""Check that a rebuild produces byte-identical artifacts.

The build has to be reproducible for any of its published numbers to mean
anything, and the obvious way of checking it does not work. Running `make` twice
and comparing hashes is what I did for weeks: the second run finds everything up
to date and compares each file with itself, so it passes without testing
anything.

The bug it should have caught is in data/grave_residue.json. Where a grave lemma
could repair onto either the acute or the lowercased acute and both are attested,
the target was picked by iterating a two-element set, and set order over strings
varies between processes because PYTHONHASHSEED is not fixed. So Κμὴ resolved to
κμή on one run and Κμή on the next, in published data. This script was checked
against exactly that: with the sort removed it names the file and exits 1.

Worth recording what is NOT the bug, since I got it wrong first. The per-work
lemma table also differed between rebuilds, and that is the lemma cache
converging rather than any ordering problem: validate_cache repairs the cache in
memory and the repaired result feeds the next build, so the first rebuild after a
rule change differs and later ones agree. Two passes over an already-converged
tree is the right test; a pass taken straight after a rule change is not.

So this forces the rebuild rather than hoping for one: it touches the corpus
files first, which is what every downstream rule keys on, then compares. Two
passes, because the failure is process-dependent and a single pass against a
committed state can agree by luck.

data/cache/ is excluded. It is gitignored build state whose whole job is to
record the mtime and size of files this script deliberately touches, so it is
expected to differ and its differing says nothing.

Takes several minutes: it rebuilds the per-work lemma table twice.

  python3 scripts/check_build_reproducible.py
  python3 scripts/check_build_reproducible.py --passes 3
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
# The corpus itself is the input, not an artifact; data/cache is build state.
SKIP = ("data/corpus/", "data/corpus_secondary/", "data/cache/")
SUFFIXES = (".json", ".tsv", ".gz", ".csv")


def artifacts() -> list[Path]:
    out = []
    for p in sorted(DATA.rglob("*")):
        if not p.is_file() or p.suffix not in SUFFIXES:
            continue
        rel = p.relative_to(REPO).as_posix()
        if any(rel.startswith(s) for s in SKIP):
            continue
        out.append(p)
    return out


def digest(paths: list[Path]) -> dict[str, str]:
    return {p.relative_to(REPO).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def rebuild() -> None:
    # Touching the corpus is what forces the rules to fire. Without it `make`
    # reports everything up to date and the comparison tests nothing.
    for p in (DATA / "corpus").glob("*.jsonl"):
        p.touch()
    subprocess.run(["make"], cwd=REPO, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passes", type=int, default=2)
    args = ap.parse_args()

    paths = artifacts()
    print(f"tracking {len(paths):,} artifacts under data/, excluding the corpus "
          f"and data/cache/")
    runs = []
    for i in range(args.passes):
        rebuild()
        runs.append(digest(paths))
        print(f"  pass {i + 1} rebuilt")

    base = runs[0]
    unstable = sorted({k for r in runs[1:] for k in base
                       if r.get(k) != base[k]})
    if not unstable:
        print(f"\nOK: every artifact is byte-identical across {args.passes} forced "
              f"rebuilds.")
        return
    print(f"\n{len(unstable)} artifact(s) NOT reproducible:")
    for k in unstable:
        print(f"    {k}")
    print("\nA rebuild that changes bytes without changing inputs means something "
          "downstream\nis reading an unordered collection. Sort it at the point it "
          "is written.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
