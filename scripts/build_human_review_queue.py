#!/usr/bin/env python3
"""Build evidence packets for the corpus defects automation cannot decide.

The queue is deliberately not an apply tool. It joins audit artifacts to the
served row, supplies a candidate scan link when the OCR provenance permits it,
and writes a decision sheet. ``validate`` checks completed sheets and can seal
their decisions as JSONL, but no command here changes data/corpus.

Build examples::

  python3 scripts/build_human_review_queue.py build --issue 31 --limit 100
  python3 scripts/build_human_review_queue.py build --issue 33 --limit 100
  python3 scripts/build_human_review_queue.py build --issue 1 \
      --corrections-log data/corrections_log/applied.jsonl --limit 200
  python3 scripts/build_human_review_queue.py build --issue 2 --limit 100
  python3 scripts/build_human_review_queue.py build --issue 2 \
      --page adrianus-rhetor.meletai=530.2

Validate a completed sheet::

  python3 scripts/build_human_review_queue.py validate \
      --queue data/review/issue-31.jsonl \
      --decisions data/review/issue-31.decisions.tsv \
      --write data/review/issue-31.reviewed.jsonl
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_public_corpus import _GK  # noqa: E402
from measure_nonfinal_graves import has_nonfinal_grave, shapes  # noqa: E402

DECISION_FIELDS = [
    "item_id", "decision", "reading", "segments", "evidence_url", "reviewer",
    "reviewed_at", "notes",
]
ISSUES = {1, 2, 31, 33}
PAGE_RE = re.compile(r"_(\d{4,6})(?:\.|$)")
PRINTED_PAGE_RE = re.compile(r"^(\d{1,6})(?:\.|$)")
ARCHIVE_RE = re.compile(r"https?://archive\.org/(?:download|details)/([^/?#]+)")
ARCHIVE_PAGE_RE = re.compile(
    r"^https?://archive\.org/details/[^/?#]+/page/n\d+/mode/1up$"
)


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def corpus(self) -> Path:
        return self.data / "corpus"

    @property
    def provenance(self) -> Path:
        return self.data / "ocr_provenance"


def stable_id(issue: int, *parts: object) -> str:
    raw = "\0".join([str(issue), *(str(part) for part in parts)])
    return f"ogc-{issue}-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_line"] = line_number
                yield row


def corpus_rows(paths: Paths) -> Iterator[tuple[Path, dict]]:
    for path in sorted(paths.corpus.glob("*.jsonl")):
        for row in read_jsonl(path):
            yield path, row


def archive_id(url: object) -> str | None:
    match = ARCHIVE_RE.search(str(url or ""))
    return match.group(1) if match else None


def provenance_source_paths(paths: Paths) -> list[Path]:
    inventory = paths.data / "inventory"
    candidates = [
        inventory / "reocr_provenance.json",
        inventory / "ocr_edition_sources.json",
        *sorted(paths.provenance.glob("*.json")),
    ]
    return [path for path in candidates if path.exists()]


def provenance_indexes(paths: Paths) -> tuple[dict[str, dict], dict[str, dict]]:
    by_urn, by_edition = {}, {}

    # These inventories cover far more OCR editions than the richer per-work
    # records below. Only exact Archive item URLs become page links; a search
    # result or an unresolved source is evidence for discovery, not alignment.
    reocr_path = paths.data / "inventory" / "reocr_provenance.json"
    if reocr_path.exists():
        inventory = json.loads(reocr_path.read_text(encoding="utf-8"))
        for entry in inventory.get("editions", []):
            ident = archive_id(entry.get("source_url"))
            if not ident or not entry.get("base"):
                continue
            content_offset = entry.get("content_offset")
            # Re-OCR page N aligns to source PDF page N - content_offset.
            # Archive leaves are zero-based while those PDF page keys are
            # one-based, hence the additional -1.
            page_offset = (-content_offset - 1
                           if isinstance(content_offset, int) else None)
            by_edition[f"qwen36-{entry['base']}"] = {
                "edition": f"qwen36-{entry['base']}",
                "source_scan": {"source": "archive.org", "public_id": ident},
                "page_offset": page_offset,
                "printed_page_offset": entry.get("printed_page_offset"),
                "alignment": entry.get("align_method"),
                "provenance_route": "reocr-inventory",
            }

    sources_path = paths.data / "inventory" / "ocr_edition_sources.json"
    if sources_path.exists():
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
        for edition, source in sources.items():
            ident = archive_id(source.get("url"))
            if ident:
                by_edition.setdefault(edition, {
                    "edition": edition,
                    "source_scan": {"source": "archive.org", "public_id": ident},
                    "page_offset": 0,
                    "provenance_route": "edition-source-inventory",
                })

    # Dedicated records are the most specific evidence and intentionally win.
    for path in sorted(paths.provenance.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("urn"):
            by_urn[record["urn"]] = record
        if record.get("edition"):
            by_edition[record["edition"]] = record
        for volume in record.get("volumes", []):
            if volume.get("edition"):
                by_edition[volume["edition"]] = {**record, **volume}
    return by_urn, by_edition


def scan_url(row: dict, indexes: tuple[dict[str, dict], dict[str, dict]]) -> str | None:
    by_urn, by_edition = indexes
    record = by_edition.get(row.get("edition")) or by_urn.get(row.get("urn"))
    if not record:
        return None
    scan = record.get("source_scan") or {}
    if scan.get("source") != "archive.org" or not scan.get("public_id"):
        return None
    locus = str(row.get("locus", ""))
    leaves = PAGE_RE.findall(locus)
    offset = record.get("page_offset", 0)
    if not leaves:
        printed = PRINTED_PAGE_RE.match(locus)
        printed_offset = record.get("printed_page_offset")
        if not printed or not isinstance(printed_offset, int):
            return f"https://archive.org/details/{scan['public_id']}"
        leaves = [printed.group(1)]
        offset = printed_offset
    if not isinstance(offset, int):
        return f"https://archive.org/details/{scan['public_id']}"
    leaf = int(leaves[-1]) + offset
    if leaf < 0:
        return f"https://archive.org/details/{scan['public_id']}"
    return (f"https://archive.org/details/{scan['public_id']}/page/"
            f"n{leaf}/mode/1up")


def exact_scan_url(value: object) -> bool:
    return bool(ARCHIVE_PAGE_RE.match(str(value or "")))


def page_stem(locus: object) -> str:
    value = str(locus or "")
    return value.rsplit(".", 1)[0] if PAGE_RE.search(value) else value


def excerpt(text: str, start: int | None = None, end: int | None = None,
            window: int = 700) -> str:
    if start is None or end is None:
        return text[: window * 2]
    left, right = max(0, start - window), min(len(text), end + window)
    return (("..." if left else "") + text[left:start] + "<TARGET>" +
            text[end:right] + ("..." if right < len(text) else ""))


def row_reference(paths: Paths, path: Path, row: dict) -> dict:
    return {
        "work": row.get("urn") or path.stem,
        "file": str(path.relative_to(paths.root)),
        "line": row["_line"],
        "locus": row.get("locus"),
        "source": row.get("source"),
        "edition": row.get("edition"),
    }


def build_issue_31(paths: Paths, limit: int, seed: str,
                   require_scan: bool = False) -> tuple[list[dict], list[dict]]:
    artifact_path = paths.data / "nonfinal_graves.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    frequencies = {row["form"]: row["tokens"] for row in artifact.get("largest_forms", [])}
    decided = {
        row["form"]: row
        for row in artifact.get("skeleton_class", {}).get("decided", [])
    }
    indexes = provenance_indexes(paths)
    candidates: list[dict] = []
    page_density: Counter[str] = Counter()

    for path, row in corpus_rows(paths):
        text = row.get("text") or ""
        for match in _GK.finditer(text):
            form = match.group()
            if not has_nonfinal_grave(form):
                continue
            item_id = stable_id(31, path.name, row["_line"], match.start(), form)
            evidence = scan_url(row, indexes)
            page_key = f"{path.name}:{page_stem(row.get('locus'))}"
            page_density[page_key] += 1
            shape_options = [
                {"kind": kind, "reading": reading}
                for kind, reading in shapes(form).items() if reading != form
            ]
            candidate = {
                "item_id": item_id,
                "issue": 31,
                "kind": "nonfinal-grave",
                "row": row_reference(paths, path, row),
                "target": {"start": match.start(), "end": match.end()},
                "context": excerpt(text, match.start(), match.end()),
                "observed": form,
                "candidate_readings": shape_options,
                "corpus_evidence": decided.get(form),
                "scan_url": evidence,
                "allowed_decisions": ["replace", "split", "delete", "defer"],
                "reading_required_for": ["replace", "split"],
                "evidence_required_for": ["replace", "split", "delete"],
                "_page_key": page_key,
                "_frequency": frequencies.get(form, 0),
                "_tie": stable_id(31, seed, item_id),
            }
            candidates.append(candidate)

    candidates.sort(key=lambda row: (
        not bool(row["scan_url"]),
        row["row"]["source"] != "ocr",
        -page_density[row["_page_key"]],
        -row["_frequency"],
        row["_tie"],
    ))
    for row in candidates:
        row["page_defects"] = page_density[row.pop("_page_key")]
        row.pop("_frequency")
        row.pop("_tie")
    if require_scan:
        candidates = [row for row in candidates if exact_scan_url(row.get("scan_url"))]
    return candidates[:limit], [artifact_path, *provenance_source_paths(paths)]


def page_rows(path: Path) -> dict[str, list[dict]]:
    pages: dict[str, list[dict]] = defaultdict(list)
    for row in read_jsonl(path):
        pages[page_stem(row.get("locus"))].append(row)
    return pages


def page_neighbor(pages: dict[str, list[dict]], locus: str, offset: int,
                  indexes: tuple[dict[str, dict], dict[str, dict]]) -> dict | None:
    ordered = list(pages)
    try:
        neighbor_locus = ordered[ordered.index(locus) + offset]
    except (ValueError, IndexError):
        return None
    rows = pages[neighbor_locus]
    text = "\n".join(row.get("text") or "" for row in rows)
    first = rows[0] if rows else {"locus": neighbor_locus}
    return {
        "locus": neighbor_locus,
        "text": text[-500:] if offset < 0 else text[:500],
        "scan_url": scan_url(first, indexes),
    }


def locus_page_number(locus: object) -> tuple[str, int] | None:
    match = PAGE_RE.search(str(locus or ""))
    if not match:
        return None
    return str(locus)[:match.start(1)], int(match.group(1))


def reviewed_duplicate_runs(paths: Paths) -> tuple[list[dict], list[Path]]:
    runs, inputs = [], []
    pattern = "issue-33-reviewed.page-images*.applied.json"
    for path in sorted((paths.data / "corpus_changes").glob(pattern)):
        audit = json.loads(path.read_text(encoding="utf-8"))
        inputs.append(path)
        for displacement in audit.get("displacements", []):
            displaced = displacement.get("displaced_page")
            retained = displacement.get("retained_page_direct")
            displaced_page = locus_page_number(displaced)
            retained_page = locus_page_number(retained)
            if not displaced_page or not retained_page:
                continue
            if displaced_page[0] != retained_page[0]:
                continue
            if displaced_page[1] < retained_page[1]:
                locus_a, locus_b = displaced, retained
                decision = "drop_a"
            elif retained_page[1] < displaced_page[1]:
                locus_a, locus_b = retained, displaced
                decision = "drop_b"
            else:
                continue
            runs.append({
                "file": displacement.get("file"),
                "locus_a": locus_a,
                "locus_b": locus_b,
                "decision": decision,
                "item_id": displacement.get("item_id"),
            })
    return runs, inputs


def reviewed_run_neighbor(pair: dict, runs: list[dict], max_distance: int = 4) -> dict | None:
    page_a = locus_page_number(pair.get("locus_a"))
    page_b = locus_page_number(pair.get("locus_b"))
    if not page_a or not page_b:
        return None
    matches = []
    for run in runs:
        if run["file"] != pair.get("file"):
            continue
        run_a = locus_page_number(run["locus_a"])
        run_b = locus_page_number(run["locus_b"])
        if not run_a or not run_b or page_a[0] != run_a[0] or page_b[0] != run_b[0]:
            continue
        delta_a, delta_b = page_a[1] - run_a[1], page_b[1] - run_b[1]
        distance = abs(delta_a)
        if delta_a == delta_b and 0 < distance <= max_distance:
            matches.append((distance, run["item_id"], run))
    if not matches:
        return None
    distance, _item_id, run = min(matches)
    return {
        "distance": distance,
        "decision": run["decision"],
        "item_id": run["item_id"],
        "locus_a": run["locus_a"],
        "locus_b": run["locus_b"],
    }


def build_issue_33(paths: Paths, limit: int, seed: str,
                   require_scan: bool = False,
                   run_extensions: bool = False) -> tuple[list[dict], list[dict]]:
    artifact_path = paths.data / "duplicate_page_candidates.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    indexes = provenance_indexes(paths)
    cache: dict[Path, dict[str, list[dict]]] = {}
    items = []

    pairs = [pair for pair in artifact.get("pairs", []) if pair.get("served")]
    audit_inputs = []
    if run_extensions:
        runs, audit_inputs = reviewed_duplicate_runs(paths)
        ranked_pairs = []
        for pair in pairs:
            neighbor = reviewed_run_neighbor(pair, runs)
            if neighbor:
                ranked_pairs.append((pair, neighbor))
        ranked_pairs.sort(key=lambda value: (
            value[1]["distance"],
            not value[0].get("same_item", False),
            -float(value[0].get("containment", 0)),
            int(value[0].get("words_absent_from_a", 0)),
            stable_id(33, seed, value[0].get("file"), value[0].get("locus_a"),
                      value[0].get("locus_b")),
        ))
    else:
        pairs.sort(key=lambda pair: (
            not pair.get("same_item", False),
            -float(pair.get("containment", 0)),
            int(pair.get("words_absent_from_a", 0)),
            stable_id(33, seed, pair.get("file"), pair.get("locus_a"), pair.get("locus_b")),
        ))
        ranked_pairs = [(pair, None) for pair in pairs]
    for pair, reviewed_run in ranked_pairs:
        path = paths.root / pair["file"]
        pages = cache.setdefault(path, page_rows(path))
        rows_a, rows_b = pages.get(pair["locus_a"], []), pages.get(pair["locus_b"], [])
        first_a = rows_a[0] if rows_a else {"urn": path.stem, "locus": pair["locus_a"]}
        first_b = rows_b[0] if rows_b else {"urn": path.stem, "locus": pair["locus_b"]}
        item_id = stable_id(33, pair["file"], pair["locus_a"], pair["locus_b"])
        item = {
            "item_id": item_id,
            "issue": 33,
            "kind": "duplicate-page-pair",
            "file": pair["file"],
            "work": first_a.get("urn") or path.stem,
            "page_a": {
                "locus": pair["locus_a"],
                "text": "\n".join(row.get("text") or "" for row in rows_a),
                "scan_url": scan_url(first_a, indexes),
            },
            "page_b": {
                "locus": pair["locus_b"],
                "text": "\n".join(row.get("text") or "" for row in rows_b),
                "scan_url": scan_url(first_b, indexes),
            },
            "sequence": {
                "page_a": {
                    "previous": page_neighbor(pages, pair["locus_a"], -1, indexes),
                    "next": page_neighbor(pages, pair["locus_a"], 1, indexes),
                },
                "page_b": {
                    "previous": page_neighbor(pages, pair["locus_b"], -1, indexes),
                    "next": page_neighbor(pages, pair["locus_b"], 1, indexes),
                },
            },
            "signals": {key: pair.get(key) for key in (
                "containment", "bigrams_a", "bigrams_b", "tokens_b",
                "words_absent_from_a", "same_item", "page_offset",
                "unique_runs_if_a_dropped", "unique_runs_if_b_dropped",
            )},
            "allowed_decisions": ["keep_both", "drop_a", "drop_b", "merge", "defer"],
            "reading_required_for": ["merge"],
            "evidence_required_for": ["keep_both", "drop_a", "drop_b", "merge"],
        }
        if reviewed_run:
            item["signals"]["reviewed_run_neighbor"] = reviewed_run
        if require_scan and not (
            exact_scan_url(item["page_a"]["scan_url"])
            and exact_scan_url(item["page_b"]["scan_url"])
        ):
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return items, [artifact_path, *audit_inputs, *provenance_source_paths(paths)]


def stratified(records: Iterable[dict], seed: str) -> Iterator[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        groups[str(row.get("by") or "unknown")].append(row)
    for rows in groups.values():
        rows.sort(key=lambda row: stable_id(1, seed, row.get("urn"), row.get("locus"),
                                            row.get("original"), row.get("corrected")))
    keys = sorted(groups)
    while keys:
        remaining = []
        for key in keys:
            if groups[key]:
                yield groups[key].pop()
            if groups[key]:
                remaining.append(key)
        keys = remaining


def load_work(paths: Paths, urn: str, cache: dict[str, list[dict]]) -> list[dict]:
    if urn not in cache:
        path = paths.corpus / f"{urn}.jsonl"
        cache[urn] = list(read_jsonl(path)) if path.exists() else []
    return cache[urn]


def find_locus(rows: list[dict], locus: object) -> dict | None:
    value = str(locus or "")
    return next((row for row in rows if str(row.get("locus")) == value), None)


def build_issue_1(paths: Paths, limit: int, seed: str,
                  corrections_log: Path) -> tuple[list[dict], list[dict], list[dict]]:
    if not corrections_log.exists():
        raise SystemExit(f"corrections log not found: {corrections_log}")
    records = list(read_jsonl(corrections_log))
    indexes = provenance_indexes(paths)
    work_cache: dict[str, list[dict]] = {}
    items, audit = [], []

    for correction in stratified(records, seed):
        urn = str(correction.get("urn") or "")
        row = find_locus(load_work(paths, urn, work_cache), correction.get("locus"))
        if not row:
            continue
        text = row.get("text") or ""
        corrected = str(correction.get("corrected") or "")
        original = str(correction.get("original") or "")
        start = text.find(corrected)
        if not corrected or start < 0 or corrected == original:
            continue
        item_id = stable_id(1, urn, correction.get("locus"), original, corrected)
        applied_first = int(hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest(), 16) % 2 == 0
        options = ({"A": corrected, "B": original} if applied_first
                   else {"A": original, "B": corrected})
        path = paths.corpus / f"{urn}.jsonl"
        items.append({
            "item_id": item_id,
            "issue": 1,
            "kind": "blind-correction-rating",
            "row": row_reference(paths, path, row),
            "context": excerpt(text, start, start + len(corrected)),
            "options": options,
            "scan_url": scan_url(row, indexes),
            "allowed_decisions": ["A", "B", "neither", "defer"],
            "reading_required_for": ["neither"],
            "evidence_required_for": ["A", "B", "neither"],
        })
        audit.append({
            "item_id": item_id,
            "applied_option": "A" if applied_first else "B",
            "original": original,
            "corrected": corrected,
            "method": correction.get("by"),
            "confidence": correction.get("confidence"),
            "status": correction.get("status"),
            "upstream_evidence": correction.get("evidence"),
        })
        if len(items) >= limit:
            break
    return items, audit, [corrections_log, *provenance_source_paths(paths)]


def build_issue_2(paths: Paths, limit: int, seed: str,
                  works_only: set[str] | None = None,
                  require_scan: bool = False,
                  pages_per_work: int = 1,
                  pages_only: set[tuple[str, str]] | None = None,
                  ) -> tuple[list[dict], list[dict]]:
    catalog_path = paths.data / "corpus_catalog.tsv"
    indexes = provenance_indexes(paths)
    with catalog_path.open(encoding="utf-8", newline="") as handle:
        works = [row for row in csv.DictReader(handle, delimiter="\t")
                 if row.get("source") == "ocr" and row.get("correction") == "raw-ocr"]
    if pages_only:
        works = [row for row in works
                 if row.get("slug") in {slug for slug, _page in pages_only}]
    elif works_only:
        works = [row for row in works if row.get("slug") in works_only]
    candidates = []
    for work in works:
        path = paths.corpus / f"{work['slug']}.jsonl"
        if not path.exists():
            continue
        pages = page_rows(path)
        ranked = []
        for page, rows in pages.items():
            if pages_only and (work["slug"], page) not in pages_only:
                continue
            text = "\n".join(row.get("text") or "" for row in rows)
            if not text.strip():
                continue
            link = scan_url(rows[0], indexes)
            ranked.append((not bool(link), -len(_GK.findall(text)),
                           stable_id(2, seed, work["slug"], page), page, rows, link, text))
        if require_scan:
            ranked = [candidate for candidate in ranked
                      if exact_scan_url(candidate[5])]
        if not ranked:
            continue
        selected = sorted(ranked)
        if not pages_only:
            selected = selected[:pages_per_work]
        for _, _, _, page, rows, link, text in selected:
            item_id = stable_id(2, work["slug"], page)
            candidates.append({
                "item_id": item_id,
                "issue": 2,
                "kind": "raw-ocr-page",
                "file": str(path.relative_to(paths.root)),
                "work": {
                    "slug": work["slug"],
                    "work_id": work.get("work_id"),
                    "author": work.get("author"),
                    "title": work.get("title"),
                    "tokens": int(work.get("tokens") or 0),
                    "unattested_rate": float(work.get("unattested_rate") or 0),
                },
                "page": page,
                "loci": [row.get("locus") for row in rows],
                "rows": [{
                    "line": row["_line"],
                    "locus": row.get("locus"),
                    "source": row.get("source"),
                    "edition": row.get("edition"),
                    "text": row.get("text") or "",
                    "text_sha256": hashlib.sha256(
                        (row.get("text") or "").encode("utf-8")
                    ).hexdigest(),
                } for row in rows],
                "text": text,
                "source_text_sha256": hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest(),
                "scan_url": link,
                "allowed_decisions": [
                    "accept_ocr", "transcribe", "non_text", "defer",
                ],
                "reading_required_for": ["transcribe"],
                "segments_required_for": ["transcribe"],
                "evidence_required_for": [
                    "accept_ocr", "transcribe", "non_text",
                ],
            })
    candidates.sort(key=lambda item: (
        not bool(item["scan_url"]),
        -item["work"]["tokens"],
        -len(_GK.findall(item["text"])),
        stable_id(2, seed, item["work"]["slug"], item["page"]),
    ))
    if pages_only:
        found = {(item["work"]["slug"], item["page"]) for item in candidates}
        missing = sorted(pages_only - found)
        if missing:
            rendered = ", ".join(f"{slug}={page}" for slug, page in missing)
            raise SystemExit(f"requested issue #2 pages not found: {rendered}")
    return candidates[:limit], [catalog_path, *provenance_source_paths(paths)]


def work_page(value: str) -> tuple[str, str]:
    slug, separator, page = value.partition("=")
    if not separator or not slug or not page:
        raise argparse.ArgumentTypeError("expected WORK=PAGE")
    return slug, page


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def output_family(output: Path) -> tuple[Path, Path, Path]:
    base = output.with_suffix("")
    return (base.with_suffix(".decisions.tsv"), base.with_suffix(".manifest.json"),
            base.with_suffix(".audit.jsonl"))


def write_packet(paths: Paths, issue: int, items: list[dict], output: Path,
                 inputs: list[Path], audit: list[dict] | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items)
    output.write_text(body, encoding="utf-8")
    decisions, manifest_path, audit_path = output_family(output)
    with decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS, delimiter="\t")
        writer.writeheader()
        for item in items:
            writer.writerow({"item_id": item["item_id"]})
    if audit is not None:
        audit_path.write_text("".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in audit
        ), encoding="utf-8")

    release_path = paths.data / "corpus_release.json"
    release = json.loads(release_path.read_text(encoding="utf-8")) if release_path.exists() else {}
    manifest = {
        "schema_version": 1,
        "issue": f"open-greek/open-greek-corpus#{issue}",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_commit": repository_commit(paths.root),
        "release_id": release.get("release_id"),
        "corpus_sha256": release.get("pin", {}).get("corpus_sha256"),
        "queue": str(output),
        "queue_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "decisions": str(decisions),
        "items": len(items),
        "inputs": [
            {"path": str(path), "sha256": file_sha256(path)} for path in inputs
        ],
        "blind_audit": str(audit_path) if audit is not None else None,
        "safety": "review artifacts only; no command in this tool edits data/corpus",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"wrote {len(items)} items to {output}")
    print(f"decision sheet: {decisions}")
    print(f"manifest: {manifest_path}")
    if audit is not None:
        print(f"blind audit key (do not give to raters): {audit_path}")


def load_queue(path: Path) -> tuple[dict[str, dict], str]:
    body = path.read_bytes()
    rows = {row["item_id"]: row for row in read_jsonl(path)}
    return rows, hashlib.sha256(body).hexdigest()


def parse_review_segments(item: dict, raw: object, reading: str) -> list[dict]:
    """Validate the explicit locus boundary map for a page transcription."""
    if isinstance(raw, str):
        try:
            segments = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f"segments are not valid JSON: {error.msg}") from error
    else:
        segments = raw
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must be a non-empty JSON array")
    expected = item.get("rows") or []
    expected_loci = [row.get("locus") for row in expected]
    observed_loci = [row.get("locus") if isinstance(row, dict) else None
                     for row in segments]
    if observed_loci != expected_loci:
        raise ValueError("segments must name every queued locus exactly once and in order")
    if any(not isinstance(row.get("text"), str) for row in segments):
        raise ValueError("every segment must contain string text")
    joined = "\n".join(row["text"] for row in segments)
    if joined != reading:
        raise ValueError("reading must equal the newline-joined segment texts")
    return [{"locus": row["locus"], "text": row["text"]} for row in segments]


def validate_decisions(queue_path: Path, decisions_path: Path,
                       write: Path | None = None) -> int:
    queue, queue_sha = load_queue(queue_path)
    accepted, errors, seen = [], [], set()
    with decisions_path.open(encoding="utf-8", newline="") as handle:
        for line_number, decision in enumerate(csv.DictReader(handle, delimiter="\t"), 2):
            item_id = (decision.get("item_id") or "").strip()
            choice = (decision.get("decision") or "").strip()
            if not choice:
                continue
            if item_id in seen:
                errors.append(f"line {line_number}: duplicate item_id {item_id}")
                continue
            seen.add(item_id)
            item = queue.get(item_id)
            if not item:
                errors.append(f"line {line_number}: unknown item_id {item_id}")
                continue
            if choice not in item["allowed_decisions"]:
                errors.append(f"line {line_number}: {choice!r} is not allowed for {item_id}")
            if not (decision.get("reviewer") or "").strip():
                errors.append(f"line {line_number}: reviewer is required for {item_id}")
            if not (decision.get("reviewed_at") or "").strip():
                errors.append(f"line {line_number}: reviewed_at is required for {item_id}")
            reading = (decision.get("reading") or "").strip()
            if choice in item.get("reading_required_for", []) and not reading:
                errors.append(f"line {line_number}: reading is required for {item_id}={choice}")
            if choice in item.get("evidence_required_for", []) and not (decision.get("evidence_url") or "").strip():
                errors.append(f"line {line_number}: evidence_url is required for {item_id}={choice}")
            if choice == "defer" and not (decision.get("notes") or "").strip():
                errors.append(f"line {line_number}: notes are required when deferring {item_id}")
            record = {key: (decision.get(key) or "").strip() for key in DECISION_FIELDS}
            if choice in item.get("segments_required_for", []):
                try:
                    record["segments"] = parse_review_segments(
                        item, decision.get("segments") or "", reading,
                    )
                except ValueError as error:
                    errors.append(f"line {line_number}: {item_id}: {error}")
            accepted.append(record)
    if errors:
        raise SystemExit("invalid decisions:\n  " + "\n  ".join(errors))
    if not accepted:
        raise SystemExit("no completed decisions found")
    if write:
        write.parent.mkdir(parents=True, exist_ok=True)
        with write.open("w", encoding="utf-8") as handle:
            for row in accepted:
                handle.write(json.dumps({
                    **row,
                    "issue": queue[row["item_id"]]["issue"],
                    "kind": queue[row["item_id"]]["kind"],
                    "queue_sha256": queue_sha,
                }, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"sealed {len(accepted)} decisions to {write}")
    else:
        print(f"valid: {len(accepted)} completed decisions")
    return len(accepted)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="build a pinned queue and blank decision sheet")
    build.add_argument("--issue", type=int, choices=sorted(ISSUES), required=True)
    build.add_argument("--limit", type=int, default=100)
    build.add_argument("--seed", default="ogc-human-review-v1")
    build.add_argument("--output", type=Path)
    build.add_argument("--corrections-log", type=Path,
                       default=Path("data/corrections_log/applied.jsonl"))
    build.add_argument("--work", action="append", default=[],
                       help="for issue #2, restrict the packet to this work slug")
    build.add_argument("--page", type=work_page, action="append", default=[],
                       metavar="WORK=PAGE",
                       help="for issue #2, include this exact work page; repeatable")
    build.add_argument("--pages-per-work", type=int, default=1,
                       help="for issue #2, consider this many ranked pages per work")
    build.add_argument("--require-scan", action="store_true",
                       help="include only items with every required exact scan link")
    build.add_argument("--run-extensions", action="store_true",
                       help="for issue #33, select synchronized pages within four "
                            "steps of a previously reviewed duplicate run")
    build.add_argument("--exclude", type=Path, action="append", default=[],
                       help="skip item IDs found in a prior queue or sealed JSONL")
    validate = sub.add_parser("validate", help="validate and optionally seal decisions")
    validate.add_argument("--queue", type=Path, required=True)
    validate.add_argument("--decisions", type=Path, required=True)
    validate.add_argument("--write", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "validate":
        validate_decisions(args.queue, args.decisions, args.write)
        return

    if args.limit < 1:
        raise SystemExit("--limit must be positive")
    if args.pages_per_work < 1:
        raise SystemExit("--pages-per-work must be positive")
    paths = Paths(REPO)
    if args.work and args.issue != 2:
        raise SystemExit("--work is only valid for issue #2")
    if args.page and args.issue != 2:
        raise SystemExit("--page is only valid for issue #2")
    if args.work and args.page:
        raise SystemExit("--work and --page cannot be combined")
    if args.page and args.pages_per_work != 1:
        raise SystemExit("--pages-per-work cannot be combined with --page")
    if args.page and args.limit < len(set(args.page)):
        raise SystemExit("--limit is smaller than the number of requested pages")
    if args.pages_per_work != 1 and args.issue != 2:
        raise SystemExit("--pages-per-work is only valid for issue #2")
    if args.run_extensions and args.issue != 33:
        raise SystemExit("--run-extensions is only valid for issue #33")
    excluded = set()
    for excluded_path in args.exclude:
        if not excluded_path.is_absolute():
            excluded_path = paths.root / excluded_path
        excluded.update(row.get("item_id") for row in read_jsonl(excluded_path))
    build_limit = args.limit + len(excluded)
    output = args.output or paths.data / "review" / f"issue-{args.issue}.jsonl"
    audit = None
    if args.issue == 31:
        items, inputs = build_issue_31(paths, build_limit, args.seed, args.require_scan)
    elif args.issue == 33:
        items, inputs = build_issue_33(
            paths, build_limit, args.seed, args.require_scan, args.run_extensions,
        )
    elif args.issue == 2:
        items, inputs = build_issue_2(
            paths, build_limit, args.seed, set(args.work), args.require_scan,
            args.pages_per_work, set(args.page),
        )
    else:
        corrections_log = args.corrections_log
        if not corrections_log.is_absolute():
            corrections_log = paths.root / corrections_log
        items, audit, inputs = build_issue_1(
            paths, build_limit, args.seed, corrections_log,
        )
    items = [item for item in items if item["item_id"] not in excluded][:args.limit]
    if audit is not None:
        keep = {item["item_id"] for item in items}
        audit = [row for row in audit if row["item_id"] in keep]
    if not items:
        raise SystemExit(f"no reviewable items found for issue #{args.issue}")
    write_packet(paths, args.issue, items, output, inputs, audit)


if __name__ == "__main__":
    main()
