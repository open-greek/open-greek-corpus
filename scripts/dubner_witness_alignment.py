"""Load the preserved Dübner 1855 Harvard OCR readings without duplicate votes.

The current Platonius file is a partly merged OCR reading of a whole printed
volume. Exact cross-work copies and the original duplicate-page reads live in
secondary storage. They are readings of the same edition, not additional
historical occurrences. Every record returned here therefore shares one vote
``group``. The alternative lane preserves all rejected fallback readings from
the earlier merge; it is explicitly a constructed projection, not a new scan.

``before`` maps repository-relative paths to exact original bytes. A repair can
supply its archived inputs after the files have been split, so replay does not
rely on the current serving layout. Source pins and preimages fail closed.
"""
from __future__ import annotations

import bisect
import copy
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Mapping

A_SLUG = "scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii"
B_SLUG = "platonius.fragmenta-de-comoedia-graeca"
B_PRIMARY = f"data/corpus/{B_SLUG}.jsonl"
B_CROSSWORK = f"data/corpus_secondary/{B_SLUG}.jsonl"
B_DUPLICATE = f"data/corpus_secondary/{B_SLUG}.duplicate-read-merged.jsonl"
MERGE_AUDIT = "data/corpus_changes/ocr.duplicate-read-merge.json"
MERGE_GUESSES = "data/duplicate_read_merge_guesses.json"
B_GROUP = "dubner-1855-harvard"
SOURCE_SCANS = {
    "harvard": {
        "url": "https://archive.org/download/scholiagraecain01dbgoog/scholiagraecain01dbgoog.pdf",
        "sha256": "61c07b9dbde80569c6e54238f2cbb0897d8bb33386a9ecad389836bd67e0c600",
        "pages": 801,
    },
    "toronto": {
        "url": "https://archive.org/download/scholiagraecaina00dbuoft/scholiagraecaina00dbuoft.pdf",
        "sha256": "9d960c70b833f73b3871701775c557a6db1472cc95a04bea8f35054922715c07",
        "pages": 776,
    },
}
PINS = {
    B_PRIMARY: "9e2caeeb7764f10c01b21b404efbf9a8c516d06116e6b855e4615d1af09c01d5",
    B_CROSSWORK: "a7fd9c346538459198375b282156474371f0efb2adbce9a6f2627c514f6fa958",
    B_DUPLICATE: "28c3dcc1b1e1b6d55ed40dfb7fe3d9278c6af0071016acdf06e5f03c1b48d58d",
    MERGE_AUDIT: "7f9ff1cd1e258fa63ff0c7c8b24dde0750a7f23e95a1e939c36b299050f72551",
    MERGE_GUESSES: "eae993c4e89566b59720c98e38f57d3556e3c6a9ab40129022956604c6df4ff2",
}
PAGE = re.compile(r"platonius_duebner_scholaristoph1_(\d{4})\.(\d+)\Z")
APOS = re.compile(r"(?<=[Ͱ-Ͽἀ-῿])['’ʼ‘´΄]")


def norm_elision(text: str) -> str:
    """Use the historical merge's one-character typographic normalization."""
    return APOS.sub("᾽", text)


def harvard_to_toronto(page: int) -> int | None:
    """Return a verified same-printed-page concordance, not a line alignment.

    Eight and eighteen repeated leaves, two missing leaves, and two repeated
    annotation leaves prevent a global offset. The low-Greek Latin index pages
    between Harvard 684 and 770 are intentionally not assigned by approximate
    text matches. They remain preserved source-specific editorial pages.
    """
    if page in {8, 14, 18, 19}:
        return page - 1
    for first, last, offset in (
        (24, 138, 1), (139, 208, 9), (209, 382, 27),
        (383, 534, 25), (535, 683, 27), (771, 793, 25),
    ):
        if first <= page <= last:
            return page - offset
    return None


def source_bytes(root: Path, path: str, before: Mapping[str, bytes] | None = None) -> bytes:
    data = before[path] if before is not None and path in before else (root / path).read_bytes()
    if not isinstance(data, bytes):
        raise ValueError(f"archived source must contain bytes: {path}")
    if hashlib.sha256(data).hexdigest() != PINS[path]:
        raise ValueError(f"Dübner source pin mismatch: {path}")
    return data


def _record(path: str, row: dict, *, derived: bool = False, alternatives: list | None = None) -> dict:
    match = PAGE.fullmatch(str(row.get("locus", "")))
    if not match:
        raise ValueError(f"unexpected Harvard locus in {path}: {row.get('locus')}")
    page = int(match.group(1))
    suffix = ":fallback-alternative" if derived else ""
    return {
        "id": f"{path}#{row['locus']}{suffix}",
        "group": B_GROUP,
        "path": path,
        "sha256": PINS[path],
        "row": copy.deepcopy(row),
        "source_page": page,
        "toronto_page": harvard_to_toronto(page),
        "derived": derived,
        "alternatives": alternatives or [],
    }


def fallback_rows(primary: list[dict], audit: dict, guesses: dict) -> list[tuple[dict, list]]:
    """Project the rejected lane, validating all 1,854 original preimages.

    The ledger indexes rows before displaced pages were removed. Correct that
    index using the removal audit, then validate the literal position against
    the current merged reading. This does not fuzzy-match or relocate a token.
    """
    entry = audit["files"][B_PRIMARY]
    removed = sorted(item["index"] for item in entry["removed_rows"])
    if len(primary) != entry["rows_after"]:
        raise ValueError("Harvard merged row accounting differs from the audit")
    by_row: dict[int, list] = defaultdict(list)
    for variant in guesses["rows"]:
        if variant["file"] != B_PRIMARY:
            continue
        original = variant["row"]
        if original in removed:
            raise ValueError("fallback points to a displaced row")
        current = original - bisect.bisect_left(removed, original)
        if current < 0 or current >= len(primary):
            raise ValueError("fallback row index is outside the pinned source")
        row = primary[current]
        start = variant["offset"]
        served = variant["served"]
        if norm_elision(row["text"])[start:start + len(served)] != served:
            raise ValueError(f"fallback preimage mismatch at {row['locus']}:{start}")
        if len(variant["rejected"]) != 1:
            raise ValueError("one alternative lane cannot represent multiple rejected readings")
        by_row[current].append({
            "offset": start,
            "original": row["text"][start:start + len(served)],
            "alternative": variant["rejected"][0],
            "pre_removal_row_index": original,
            "source": MERGE_GUESSES,
            "source_sha256": PINS[MERGE_GUESSES],
        })
    if sum(map(len, by_row.values())) != 1854 or len(by_row) != 476:
        raise ValueError("Harvard fallback ledger accounting changed")
    projected = []
    for index, variants in sorted(by_row.items()):
        row = copy.deepcopy(primary[index])
        end = 0
        for variant in sorted(variants, key=lambda item: item["offset"]):
            if variant["offset"] < end:
                raise ValueError("overlapping fallback alternatives")
            end = variant["offset"] + len(variant["original"])
        for variant in sorted(variants, key=lambda item: item["offset"], reverse=True):
            start = variant["offset"]
            row["text"] = row["text"][:start] + variant["alternative"] + row["text"][start + len(variant["original"]):]
        projected.append((row, variants))
    return projected


def source_rows(root: Path, before: Mapping[str, bytes] | None = None) -> list[dict]:
    """Return literal Harvard rows plus the constructed rejected-reading lane.

    All rows, including derived alternatives, have ``group == B_GROUP``. A
    consensus algorithm must count that group at most once per reading. Literal
    records are suitable for archives and old-locus resolution; derived records
    are comparison evidence only and must not create extra served occurrences.
    """
    root = Path(root)
    inputs = {path: source_bytes(root, path, before) for path in PINS}
    rows = {path: [json.loads(line) for line in inputs[path].splitlines() if line]
            for path in (B_PRIMARY, B_CROSSWORK, B_DUPLICATE)}
    result = [_record(path, row) for path in rows for row in rows[path]]
    audit = json.loads(inputs[MERGE_AUDIT])
    guesses = json.loads(inputs[MERGE_GUESSES])
    for row, variants in fallback_rows(rows[B_PRIMARY], audit, guesses):
        result.append(_record(B_PRIMARY, row, derived=True, alternatives=variants))
    ids = [record["id"] for record in result]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Harvard witness record identity")
    return result
