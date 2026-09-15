#!/usr/bin/env python3
"""Publish the measured corpus limitations that no safe bulk rule can finish.

An issue is useful while it can drive a bounded repair. Once every approved
automatic class is empty and the remainder needs new evidence or per-record
review, leaving the issue open forever does not add information. This artifact
keeps the limitation visible, pins the measurements behind it, and states the
condition that would make the work actionable again.

  python3 scripts/build_known_limitations.py
  python3 scripts/build_known_limitations.py --write
  python3 scripts/build_known_limitations.py --check
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_corpus_release import MEASURED


REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "known_limitations.json"
STAMP_GAP = DATA / "correction_stamp_gap.json"
NONFINAL_GRAVES = DATA / "nonfinal_graves.json"
CATALOG = DATA / "corpus_catalog.tsv"
OCR_SOURCES = {"ocr", "cgpg"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    stamp_gap = json.loads(STAMP_GAP.read_text(encoding="utf-8"))
    nonfinal = json.loads(NONFINAL_GRAVES.read_text(encoding="utf-8"))
    raw = stamp_gap["raw_ocr"]
    measured = stamp_gap["measured_against"]
    with CATALOG.open(encoding="utf-8", newline="") as handle:
        catalog = list(csv.DictReader(handle, delimiter="\t"))

    catalog_sha = sha256(CATALOG)
    pin_lines = [f"{row['slug']}\t{row['sha256']}\n" for row in catalog]
    corpus_sha = hashlib.sha256(
        "".join(sorted(pin_lines)).encode("utf-8")).hexdigest()
    raw_rows = [row for row in catalog
                if row["source"] in OCR_SOURCES and row["correction"] == "raw-ocr"]
    raw_tokens = sum(int(row["tokens"]) for row in raw_rows)
    failures = []
    if measured["catalog_sha256"] != catalog_sha:
        failures.append("correction-stamp catalog hash is stale")
    if measured["corpus_sha256"] != corpus_sha:
        failures.append("correction-stamp corpus hash is stale")
    if raw["upper_bound_works"] != len(raw_rows):
        failures.append("raw-OCR upper-bound work count is stale")
    if raw["upper_bound_tokens"] != raw_tokens:
        failures.append("raw-OCR upper-bound token count is stale")
    if nonfinal["served_tokens"] != sum(int(row["tokens"]) for row in catalog):
        failures.append("non-final-grave served-token count is stale")
    if failures:
        raise SystemExit("; ".join(failures))

    estimate_at_sample = MEASURED["wrong_rows_estimate"]
    reverted = MEASURED["reverted_since_measurement"]["records"]
    # The source estimate is intentionally no finer than a hundred records.
    estimated_remaining = ((estimate_at_sample - reverted) // 100) * 100

    return {
        "schema_version": 1,
        "what": (
            "Known quality limitations of the served corpus whose safe automatic "
            "repair classes are exhausted. Closing the linked work item accepts "
            "the measured limitation; it does not assert that the count is zero."
        ),
        "decision_date": "2026-09-15",
        "generated_from": {
            "corpus_sha256": corpus_sha,
            "corpus_catalog": {
                "path": measured["catalog"],
                "sha256": catalog_sha,
            },
            "correction_stamp_gap": {
                "path": STAMP_GAP.relative_to(REPO).as_posix(),
                "sha256": sha256(STAMP_GAP),
            },
            "nonfinal_graves": {
                "path": NONFINAL_GRAVES.relative_to(REPO).as_posix(),
                "sha256": sha256(NONFINAL_GRAVES),
            },
        },
        "limitations": [
            {
                "key": "applied-correction-error",
                "issue": "https://github.com/open-greek/open-greek-corpus/issues/1",
                "status": "accepted-measured-limitation",
                "current_measurement": {
                    "estimated_wrong_records_at_sample": estimate_at_sample,
                    "unanimously_wrong_records_reverted_after_sample": reverted,
                    "estimated_wrong_records_remaining_rounded": estimated_remaining,
                    "corpus_weighted_wrong_share_at_sample":
                        MEASURED["corpus_weighted"]["wrong"],
                    "corpus_weighted_split_or_unsure_share_at_sample":
                        MEASURED["corpus_weighted"]["split_or_unsure"],
                },
                "why_no_bulk_action_remains": (
                    "Every major correction cell was sampled or censused by two "
                    "blind raters and unanimous wrong verdicts were paid out. The "
                    "remaining estimate does not identify which records are wrong; "
                    "the strongest discovered rule would revert about one sound "
                    "correction for every bad one."
                ),
                "reopen_when": (
                    "A new per-record evidence source or independently validated "
                    "gate identifies a bounded correction class with an acceptable "
                    "false-positive rate."
                ),
            },
            {
                "key": "raw-ocr-coverage",
                "issue": "https://github.com/open-greek/open-greek-corpus/issues/2",
                "status": "accepted-measured-limitation",
                "current_measurement": {
                    "lower_bound_works": raw["lower_bound_works"],
                    "lower_bound_tokens": raw["lower_bound_tokens"],
                    "lower_bound_share": raw["lower_bound_share_of_corpus_tokens"],
                    "upper_bound_works": raw["upper_bound_works"],
                    "upper_bound_tokens": raw["upper_bound_tokens"],
                    "upper_bound_share": raw["upper_bound_share_of_corpus_tokens"],
                    "works_in_stamp_gap": raw["works_in_doubt"],
                    "tokens_in_stamp_gap": raw["tokens_in_doubt"],
                },
                "why_no_bulk_action_remains": (
                    "The upstream correction workflow and boundary-safe page "
                    "re-ingest path now exist, but untouched OCR cannot honestly be "
                    "relabelled as corrected. Finishing the remainder means reading "
                    "the source pages, not changing a confidence threshold."
                ),
                "reopen_when": (
                    "A funded or otherwise staffed source-page correction campaign "
                    "is ready to ingest reviewed pages, or a newly validated "
                    "correction method is approved for a defined tranche."
                ),
            },
            {
                "key": "nonfinal-grave-source-errors",
                "issue": "https://github.com/open-greek/open-greek-corpus/issues/31",
                "status": "accepted-measured-limitation",
                "current_measurement": {
                    "forms": nonfinal["forms"],
                    "tokens": nonfinal["tokens"],
                    "share": nonfinal["share"],
                    "works": nonfinal["works_touched"],
                },
                "why_no_bulk_action_remains": (
                    "All forms clearing the approved corpus-skeleton gates were "
                    "repaired, and four scan-backed review rounds applied only exact "
                    "readings. The residue is distributed over thousands of source "
                    "pages; changing grave to acute blindly is known to choose the "
                    "wrong word in common cases."
                ),
                "reopen_when": (
                    "Page images, an aligned independent edition, or another "
                    "approved evidence type makes a bounded set of occurrences "
                    "deterministically repairable."
                ),
            },
        ],
    }


def rendered() -> str:
    return json.dumps(build(), ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    output = rendered()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != output:
            raise SystemExit(
                "data/known_limitations.json is stale; run "
                "python3 scripts/build_known_limitations.py --write"
            )
        print("known limitations are current")
    elif args.write:
        OUT.write_text(output, encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
