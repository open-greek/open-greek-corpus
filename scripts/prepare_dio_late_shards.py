#!/usr/bin/env python3
"""Pin disjoint late-only Dio selections without assigning unfinished early jobs."""
import argparse
import json
from pathlib import Path

from prepare_dio_body_regions import ORIGINAL, EFFECTIVE, REVIEW, ROOT, encode, sha

DIRECTORY = EFFECTIVE.parent / "cassius-dio-late-shards"


def build(original_raw, effective_raw, review_raw):
    from scan_ocr_bundle import _relation
    changed = _relation(original_raw, effective_raw, {sha(review_raw): review_raw})
    manifest = json.loads(effective_raw)
    late = [page["id"] for page in manifest["pages"] if page["id"] in changed]
    if len(late) != 741 or any(page["source_volume"] < 6 for page in manifest["pages"] if page["id"] in changed):
        raise ValueError("Late selections must contain exactly the 741 reviewed VI–IX regions")
    groups = [late[:371], late[371:]]
    plan = {"schema_version": 1, "generated_by": "scripts/prepare_dio_late_shards.py",
        "manifest_sha256": sha(effective_raw), "source_review_sha256": sha(review_raw),
        "policy": "Contiguous late-only selections preserve effective-manifest order. Existing clients retain all early jobs and superseded late sanity predictions; no unfinished early identity is assigned here.",
        "shards": [{"path": f"shard-{index:02d}.json", "sha256": sha(encode(ids)), "regions": len(ids)}
                   for index, ids in enumerate(groups)]}
    return groups, plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DIRECTORY)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    groups, plan = build(ORIGINAL.read_bytes(), EFFECTIVE.read_bytes(), REVIEW.read_bytes())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = [(args.out_dir / f"shard-{i:02d}.json", encode(ids)) for i, ids in enumerate(groups)]
    outputs.append((args.out_dir / "plan.json", encode(plan)))
    for path, raw in outputs:
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError("Pinned late shard selection changed")
        else:
            if path.exists() and path.read_bytes() != raw:
                raise ValueError("Refusing to change an existing pinned late selection")
            path.write_bytes(raw)
    print("741 late regions: 371 + 370; no early IDs")


if __name__ == "__main__":
    main()
