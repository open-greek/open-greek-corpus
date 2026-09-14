#!/usr/bin/env python3
"""Apply reviewed reading-order overrides to corpus JSONL rows.

The same function is imported by build_corpus_loci.py, so applying an override
to the committed artifact and rebuilding it later use one rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Callable, TypeVar

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ORDER_OVERRIDES = DATA / "corpus_order_overrides.json"
T = TypeVar("T")


def load_order_overrides(path: Path = ORDER_OVERRIDES) -> dict[str, dict]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    works = raw.get("works", {})
    for work, spec in works.items():
        required = {"component", "order", "previous_order", "evidence", "date"}
        missing = required - spec.keys()
        if missing:
            raise SystemExit(f"{path.name}: {work} missing {sorted(missing)}")
        if len(spec["order"]) != len(set(spec["order"])):
            raise SystemExit(f"{path.name}: {work} order contains duplicates")
    return works


def apply_order_override(work: str, rows: list[T], overrides: dict[str, dict],
                         locus_getter: Callable[[T], str]) -> tuple[list[T], dict]:
    """Stable-sort reviewed locus divisions and refuse any unknown division."""
    spec = overrides.get(work)
    if spec is None or not rows:
        return rows, {"changed": False, "before": [], "after": []}

    component = int(spec["component"])
    rank = {value: i for i, value in enumerate(spec["order"])}

    def division(row: T) -> str:
        parts = str(locus_getter(row)).split(".")
        if component >= len(parts):
            raise SystemExit(
                f"corpus order override {work}: locus {locus_getter(row)!r} "
                f"has no component {component}"
            )
        return parts[component]

    before = []
    for row in rows:
        value = division(row)
        if not before or before[-1] != value:
            before.append(value)
    unknown = sorted(set(before) - rank.keys())
    if unknown:
        raise SystemExit(
            f"corpus order override {work}: unreviewed divisions {unknown}"
        )

    ordered = [row for _i, row in sorted(
        enumerate(rows), key=lambda pair: (rank[division(pair[1])], pair[0]))]
    after = []
    for row in ordered:
        value = division(row)
        if not after or after[-1] != value:
            after.append(value)
    return ordered, {"changed": ordered != rows, "before": before, "after": after}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    path = DATA / "corpus" / f"{args.work}.jsonl"
    original = path.read_bytes()
    rows = [json.loads(line) for line in original.decode("utf-8").splitlines()
            if line.strip()]
    overrides = load_order_overrides()
    ordered, report = apply_order_override(
        args.work, rows, overrides, lambda row: row["locus"])
    print(f"{args.work}: {len(rows):,} rows; "
          f"{'reordered' if report['changed'] else 'already ordered'}")
    print(f"  before: {' '.join(report['before'])}")
    print(f"  after:  {' '.join(report['after'])}")
    if not args.write:
        print("dry run; nothing written. Re-run with --write.")
        return

    rendered = "".join(json.dumps(row, ensure_ascii=False) + "\n"
                       for row in ordered).encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(rendered)
    os.replace(tmp, path)

    spec = overrides[args.work]
    audit = DATA / "corpus_changes" / f"{args.work}.division-order.json"
    audit.write_text(json.dumps({
        "_meta": {
            "change": "stable-sort corpus rows into reviewed reading order",
            "work": args.work,
            "applied_by": "scripts/corpus_order_overrides.py",
            "date": spec["date"],
            "evidence": spec["evidence"],
            "reversible": spec.get("reversible"),
        },
        "n_rows": len(rows),
        "before": report["before"],
        "after": report["after"],
        "sha256_before": _sha256(original),
        "sha256_after": _sha256(rendered),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"audit -> {audit.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
