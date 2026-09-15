#!/usr/bin/env python3
"""Apply segmented, scan-reviewed issue #2 page transcriptions.

Every replacement is guarded by the sealed queue, manifest, page and row
preimages, explicit locus order, and the pinned scan URL. The default is a dry
run. Applied audits retain complete before/after JSONL lines and can restore the
corpus byte-for-byte.

  python3 scripts/apply_reviewed_ocr_pages.py \
      --queue data/review/issue-2-joannes.jsonl \
      --reviewed data/review/issue-2-joannes.reviewed.jsonl \
      --manifest data/review/issue-2-joannes.manifest.json
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from build_human_review_queue import parse_review_segments

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
PAGE_RE = re.compile(r"_(\d{4,6})(?:\.|$)")
TAG_RE = re.compile(r"^[A-Za-z0-9._-]+$")
GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]+")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def indexed(rows: list[dict], label: str) -> dict[str, dict]:
    out = {}
    for row in rows:
        item_id = row.get("item_id")
        if not item_id or item_id in out:
            fail(f"{label} has a missing or duplicate item_id: {item_id!r}")
        out[item_id] = row
    return out


def atomic_write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def page_stem(locus: object) -> str:
    value = str(locus or "")
    return value.rsplit(".", 1)[0] if PAGE_RE.search(value) else value


def checked_inputs(queue_path: Path, reviewed_path: Path,
                   manifest_path: Path) -> tuple[list[dict], dict[str, dict], dict]:
    queue_body = queue_path.read_bytes()
    queue_sha = sha256_bytes(queue_body)
    queue_rows = read_jsonl(queue_path)
    queue = indexed(queue_rows, "queue")
    reviewed_rows = read_jsonl(reviewed_path)
    reviewed = indexed(reviewed_rows, "reviewed decisions")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("issue") != "open-greek/open-greek-corpus#2":
        fail("manifest is not for issue #2")
    if manifest.get("queue_sha256") != queue_sha:
        fail("queue does not match its manifest")
    if manifest.get("items") != len(queue_rows):
        fail("manifest item count does not match queue")
    if set(reviewed) != set(queue):
        missing = len(set(queue) - set(reviewed))
        extra = len(set(reviewed) - set(queue))
        fail(f"review is incomplete or foreign ({missing} missing, {extra} extra)")

    for item_id, decision in reviewed.items():
        item = queue[item_id]
        if item.get("issue") != 2 or item.get("kind") != "raw-ocr-page":
            fail(f"{item_id} is not an issue #2 raw-OCR page")
        if decision.get("queue_sha256") != queue_sha:
            fail(f"{item_id} was sealed against a different queue")
        if decision.get("issue") != 2 or decision.get("kind") != "raw-ocr-page":
            fail(f"{item_id} has the wrong sealed issue metadata")
        choice = decision.get("decision")
        if choice not in item.get("allowed_decisions", []):
            fail(f"{item_id} has invalid decision {choice!r}")
        if not decision.get("reviewer") or not decision.get("reviewed_at"):
            fail(f"{item_id} lacks reviewer provenance")
        if choice == "transcribe":
            if decision.get("evidence_url") != item.get("scan_url"):
                fail(f"{item_id} evidence does not match the pinned scan")
            try:
                parse_review_segments(
                    item, decision.get("segments"), decision.get("reading") or "",
                )
            except ValueError as error:
                fail(f"{item_id}: {error}")
    return queue_rows, reviewed, manifest


def build_plan(queue_path: Path, reviewed_path: Path,
               manifest_path: Path) -> dict:
    queue_rows, reviewed, manifest = checked_inputs(
        queue_path, reviewed_path, manifest_path,
    )
    summary = collections.Counter(row["decision"] for row in reviewed.values())
    mutations: dict[Path, list[tuple[dict, dict]]] = collections.defaultdict(list)
    corpus_root = CORPUS.resolve()

    for item in queue_rows:
        decision = reviewed[item["item_id"]]
        if decision["decision"] != "transcribe":
            continue
        path = resolve(Path(str(item.get("file") or ""))).resolve()
        if not path.is_relative_to(corpus_root):
            fail(f"{item['item_id']} points outside data/corpus")
        mutations[path].append((item, decision))
    if not mutations:
        fail("packet contains no reviewed page transcriptions")

    file_plans = []
    page_changes = []
    for path, pairs in sorted(mutations.items(), key=lambda pair: str(pair[0])):
        before = path.read_bytes()
        try:
            lines = before.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            fail(f"{display(path)} is not UTF-8")
        parsed = []
        pages: dict[str, list[int]] = collections.defaultdict(list)
        for index, line in enumerate(lines):
            raw = line.rstrip("\r\n")
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as error:
                fail(f"{display(path)}:{index + 1} is invalid JSON: {error}")
            parsed.append(row)
            pages[page_stem(row.get("locus"))].append(index)

        changed_indices = set()
        changed_rows = []
        for item, decision in pairs:
            expected_rows = item.get("rows") or []
            if not expected_rows:
                fail(f"{item['item_id']} has no row-level boundary preimages")
            queued_indices = [row.get("line", 0) - 1 for row in expected_rows]
            if any(index < 0 or index >= len(lines) for index in queued_indices):
                fail(f"{item['item_id']} names a missing JSONL line")
            current_page = pages.get(item.get("page"), [])
            if queued_indices != current_page:
                fail(f"{item['item_id']} does not cover the complete current page")
            queued_text = "\n".join(row.get("text") or "" for row in expected_rows)
            if queued_text != item.get("text"):
                fail(f"{item['item_id']} queue page text is internally inconsistent")
            if sha256_bytes(queued_text.encode("utf-8")) != item.get("source_text_sha256"):
                fail(f"{item['item_id']} queue page hash is internally inconsistent")

            segments = parse_review_segments(
                item, decision["segments"], decision.get("reading") or "",
            )
            item_changed = False
            page_row_changes = []
            for expected, segment, index in zip(expected_rows, segments, queued_indices):
                if index in changed_indices:
                    fail(f"two reviewed pages try to rewrite {display(path)}:{index + 1}")
                row = parsed[index]
                for field in ("locus", "source", "edition"):
                    if row.get(field) != expected.get(field):
                        fail(f"{item['item_id']} row {field} preimage changed")
                old_text = row.get("text")
                if not isinstance(old_text, str):
                    fail(f"{display(path)}:{index + 1} has no string text")
                if old_text != expected.get("text") or sha256_bytes(
                    old_text.encode("utf-8")
                ) != expected.get("text_sha256"):
                    fail(f"{item['item_id']} row text preimage changed")
                if segment["text"] == old_text:
                    continue
                newline = "\r\n" if lines[index].endswith("\r\n") else (
                    "\n" if lines[index].endswith("\n") else ""
                )
                original_line = lines[index]
                row["text"] = segment["text"]
                applied_line = json.dumps(row, ensure_ascii=False) + newline
                lines[index] = applied_line
                parsed[index] = row
                changed_indices.add(index)
                item_changed = True
                change = {
                    "line": index + 1,
                    "locus": row.get("locus"),
                    "original_line": original_line,
                    "applied_line": applied_line,
                    "original_line_sha256": sha256_bytes(original_line.encode("utf-8")),
                    "applied_line_sha256": sha256_bytes(applied_line.encode("utf-8")),
                    "text_before": old_text,
                    "text_after": segment["text"],
                }
                changed_rows.append(change)
                page_row_changes.append(change)
            if not item_changed:
                fail(f"{item['item_id']} transcription does not change the corpus")
            page_changes.append({
                "item_id": item["item_id"],
                "file": display(path),
                "page": item["page"],
                "evidence_url": decision["evidence_url"],
                "reviewer": decision["reviewer"],
                "reviewed_at": decision["reviewed_at"],
                "notes": decision.get("notes", ""),
                "rows_changed": len(page_row_changes),
                "loci": [row["locus"] for row in segments],
                "source_text_sha256": item["source_text_sha256"],
                "transcription_sha256": sha256_bytes(
                    decision["reading"].encode("utf-8")
                ),
            })

        after = "".join(lines).encode("utf-8")
        file_plans.append({
            "path": path,
            "file": display(path),
            "before": before,
            "after": after,
            "sha256_before": sha256_bytes(before),
            "sha256_after": sha256_bytes(after),
            "rows_changed": sorted(changed_rows, key=lambda row: row["line"]),
        })

    return {
        "queue_path": queue_path,
        "reviewed_path": reviewed_path,
        "manifest_path": manifest_path,
        "queue_sha256": sha256_path(queue_path),
        "reviewed_sha256": sha256_path(reviewed_path),
        "manifest_sha256": sha256_path(manifest_path),
        "manifest": manifest,
        "summary": summary,
        "files": file_plans,
        "pages": page_changes,
    }


def audit_record(plan: dict, audit_path: Path, date: str) -> dict:
    files = {}
    for block in plan["files"]:
        files[block["file"]] = {
            key: value for key, value in block.items()
            if key not in {"path", "file", "before", "after"}
        }
    return {
        "schema_version": 1,
        "what": "segmented scan-reviewed raw-OCR page transcriptions applied to served text",
        "issue": "open-greek/open-greek-corpus#2",
        "applied_at": date,
        "queue": display(plan["queue_path"]),
        "queue_sha256": plan["queue_sha256"],
        "manifest": display(plan["manifest_path"]),
        "manifest_sha256": plan["manifest_sha256"],
        "reviewed_decisions": display(plan["reviewed_path"]),
        "reviewed_decisions_sha256": plan["reviewed_sha256"],
        "release_reviewed": plan["manifest"].get("release_id"),
        "corpus_sha256_reviewed": plan["manifest"].get("corpus_sha256"),
        "decision_counts": dict(sorted(plan["summary"].items())),
        "pages_transcribed": len(plan["pages"]),
        "rows_changed": sum(len(block["rows_changed"]) for block in plan["files"]),
        "files_touched": len(plan["files"]),
        "pages": plan["pages"],
        "files": files,
        "policy": "Only explicit per-locus segments from a sealed scan review are applied; work-level raw-OCR status is not promoted by one reviewed page.",
        "reverse": f"python3 scripts/{Path(__file__).name} --audit {display(audit_path)} --unapply",
    }


def apply(plan: dict, audit_path: Path, date: str) -> None:
    if audit_path.exists():
        fail(f"audit already exists: {display(audit_path)}")
    for block in plan["files"]:
        if sha256_path(block["path"]) != block["sha256_before"]:
            fail(f"{block['file']} changed after planning")
    written = []
    try:
        for block in plan["files"]:
            atomic_write(block["path"], block["after"])
            written.append(block)
        atomic_write(
            audit_path,
            (json.dumps(audit_record(plan, audit_path, date),
                        ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
    except BaseException:
        for block in reversed(written):
            atomic_write(block["path"], block["before"])
        audit_path.unlink(missing_ok=True)
        raise


def unapply(audit_path: Path) -> None:
    if not audit_path.exists():
        fail(f"no audit at {display(audit_path)}")
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    plans = []
    for file_name, block in record.get("files", {}).items():
        path = resolve(Path(file_name))
        current = path.read_bytes()
        if sha256_bytes(current) != block.get("sha256_after"):
            fail(f"{file_name} no longer matches the applied audit")
        lines = current.decode("utf-8").splitlines(keepends=True)
        for change in block.get("rows_changed", []):
            index = change["line"] - 1
            if index >= len(lines) or lines[index] != change["applied_line"]:
                fail(f"{file_name}:{index + 1} no longer matches the applied preimage")
            lines[index] = change["original_line"]
        restored = "".join(lines).encode("utf-8")
        if sha256_bytes(restored) != block.get("sha256_before"):
            fail(f"{file_name} does not reconstruct its recorded original hash")
        plans.append((path, current, restored))
    written = []
    try:
        for path, current, restored in plans:
            atomic_write(path, restored)
            written.append((path, current))
        audit_path.unlink()
    except BaseException:
        for path, current in reversed(written):
            atomic_write(path, current)
        raise


def parse_args() -> argparse.Namespace:
    today = dt.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=Path("data/review/issue-2.jsonl"))
    parser.add_argument("--reviewed", type=Path,
                        default=Path("data/review/issue-2.reviewed.jsonl"))
    parser.add_argument("--manifest", type=Path,
                        default=Path("data/review/issue-2.manifest.json"))
    parser.add_argument("--audit", type=Path, default=Path(
        f"data/corpus_changes/issue-2-reviewed.page-transcriptions-{today}.applied.json"
    ))
    parser.add_argument("--date", default=today)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--unapply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queue = resolve(args.queue)
    reviewed = resolve(args.reviewed)
    manifest = resolve(args.manifest)
    audit = resolve(args.audit)
    if args.apply and args.unapply:
        fail("choose either --apply or --unapply")
    if args.unapply:
        unapply(audit)
        print(f"unapplied {display(audit)}")
        return
    plan = build_plan(queue, reviewed, manifest)
    print(f"reviewed issue #2 packet: {sum(plan['summary'].values())} decisions")
    print(f"  {dict(sorted(plan['summary'].items()))}")
    print(f"  {len(plan['pages'])} pages / "
          f"{sum(len(block['rows_changed']) for block in plan['files'])} changed rows / "
          f"{len(plan['files'])} files")
    if not args.apply:
        print("dry run only; pass --apply to write the corpus and audit")
        return
    apply(plan, audit, args.date)
    print(f"applied; audit: {display(audit)}")


if __name__ == "__main__":
    main()
