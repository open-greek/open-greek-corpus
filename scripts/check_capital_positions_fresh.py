#!/usr/bin/env python3
"""Fail when data/capital_positions.json has folds the corpus now supports.

The file records which capitalized lemmas are capitalized only because they open
a sentence, and validate_lemma_map.py applies it as CAPITAL_FOLDS while the
per-work lemma table is built. So a fold that has been measured but not written
does not merge two spellings that should be one, and nothing anywhere says so.

Nothing in the Makefile can build it. measure_capital_positions.py reads
work_lemma_counts.tsv.gz, which takes capital_positions.json as a prerequisite,
so a real rule would close a cycle and make would resolve it by dropping an edge
without erroring, building the table from a half-updated fold set. That is worse
than the staleness. `make capital-positions` writes it deliberately, and this is
what notices when it needs to be run: it re-measures and compares, without
writing anything.

It reports one direction only. A fold present in the file but no longer measured
is not an error here, because the writer merges rather than overwrites and a
fold already applied to the table has to keep being applied for the table to
stay consistent. A fold measured and absent is the failure this exists for; it
hid three of them, 108 tokens, for three days.

  python3 scripts/check_capital_positions_fresh.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "capital_positions.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_capital_positions as m  # noqa: E402


def main() -> None:
    if not OUT.exists():
        raise SystemExit(f"ERROR: {OUT.relative_to(REPO)} does not exist; "
                         f"run `make capital-positions`")
    have = json.loads(OUT.read_text(encoding="utf-8"))["folds"]
    measured = m.measure()
    missing = {k: v for k, v in measured.items() if k not in have}
    if missing:
        print(f"{len(missing)} capital fold(s) measured but not in "
              f"{OUT.relative_to(REPO)}:", file=sys.stderr)
        for k, v in sorted(missing.items()):
            print(f"    {k} -> {v}", file=sys.stderr)
        raise SystemExit("ERROR: run `make capital-positions`, then `make` to "
                         "carry the folds into the lemma table")
    print(f"capital folds current: {len(have)} in "
          f"{OUT.relative_to(REPO)}, none measured and missing")


if __name__ == "__main__":
    main()
