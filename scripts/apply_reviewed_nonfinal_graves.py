#!/usr/bin/env python3
"""Apply a sealed issue #31 review packet at its exact corpus offsets.

The queue identifies one occurrence, not a corpus-wide form. Every edit is
guarded by the queue hash, manifest, file, JSONL line, row metadata, character
offset, and observed preimage. The default is a dry run.

  python3 scripts/apply_reviewed_nonfinal_graves.py
  python3 scripts/apply_reviewed_nonfinal_graves.py --apply
  python3 scripts/apply_reviewed_nonfinal_graves.py --unapply
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

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
TAG_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


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


def indexed(rows: list[dict], label: str) -> dict[str, dict]:
    out = {}
    for row in rows:
        item_id = row.get("item_id")
        if not item_id or item_id in out:
            fail(f"{label} has a missing or duplicate item_id: {item_id!r}")
        out[item_id] = row
    return out


def checked_inputs(queue_path: Path, reviewed_path: Path,
                   manifest_path: Path) -> tuple[list[dict], dict[str, dict], dict]:
    queue_body = queue_path.read_bytes()
    queue_sha = sha256_bytes(queue_body)
    queue_rows = read_jsonl(queue_path)
    queue = indexed(queue_rows, "queue")
    reviewed_rows = read_jsonl(reviewed_path)
    reviewed = indexed(reviewed_rows, "reviewed decisions")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("issue") != "open-greek/open-greek-corpus#31":
        fail("manifest is not for issue #31")
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
        if item.get("issue") != 31 or item.get("kind") != "nonfinal-grave":
            fail(f"{item_id} is not an issue #31 item")
        if decision.get("queue_sha256") != queue_sha:
            fail(f"{item_id} was sealed against a different queue")
        if decision.get("issue") != 31 or decision.get("kind") != "nonfinal-grave":
            fail(f"{item_id} has the wrong sealed issue metadata")
        choice = decision.get("decision")
        if choice not in item.get("allowed_decisions", []):
            fail(f"{item_id} has invalid decision {choice!r}")
        if not decision.get("reviewer") or not decision.get("reviewed_at"):
            fail(f"{item_id} lacks reviewer provenance")
        if choice in {"replace", "split"} and not decision.get("reading"):
            fail(f"{item_id} lacks a reviewed reading")
        if choice in {"replace", "split", "delete"}:
            if decision.get("evidence_url") != item.get("scan_url"):
                fail(f"{item_id} evidence does not match the pinned scan")
    return queue_rows, reviewed, manifest


def build_plan(queue_path: Path, reviewed_path: Path,
               manifest_path: Path) -> dict:
    queue_rows, reviewed, manifest = checked_inputs(
        queue_path, reviewed_path, manifest_path,
    )
    by_row: dict[tuple[Path, int], list[tuple[dict, dict]]] = collections.defaultdict(list)
    summary = collections.Counter()

    corpus_root = (DATA / "corpus").resolve()
    for item in queue_rows:
        decision = reviewed[item["item_id"]]
        choice = decision["decision"]
        summary[choice] += 1
        if choice == "defer":
            continue
        row_ref = item.get("row") or {}
        path = resolve(Path(str(row_ref.get("file") or ""))).resolve()
        if not path.is_relative_to(corpus_root):
            fail(f"{item['item_id']} points outside data/corpus")
        line = row_ref.get("line")
        if not isinstance(line, int) or line < 1:
            fail(f"{item['item_id']} has an invalid JSONL line")
        by_row[(path, line)].append((item, decision))

    file_plans = []
    for path in sorted({key[0] for key in by_row}):
        before = path.read_bytes()
        try:
            text = before.decode("utf-8")
        except UnicodeDecodeError:
            fail(f"{display(path)} is not UTF-8")
        lines = text.splitlines(keepends=True)
        row_plans = []
        for (row_path, line_number), pairs in sorted(by_row.items(), key=lambda row: row[0][1]):
            if row_path != path:
                continue
            if line_number > len(lines):
                fail(f"{display(path)} has no line {line_number}")
            original_line = lines[line_number - 1]
            newline = "\r\n" if original_line.endswith("\r\n") else ("\n" if original_line.endswith("\n") else "")
            payload = original_line[:-len(newline)] if newline else original_line
            try:
                row = json.loads(payload)
            except json.JSONDecodeError as error:
                fail(f"{display(path)}:{line_number} is invalid JSON: {error}")
            original_text = row.get("text")
            if not isinstance(original_text, str):
                fail(f"{display(path)}:{line_number} has no string text")

            spans = []
            for item, decision in pairs:
                ref = item["row"]
                for field in ("locus", "source", "edition"):
                    if row.get(field) != ref.get(field):
                        fail(f"{item['item_id']} row {field} preimage changed")
                target = item.get("target") or {}
                start, end = target.get("start"), target.get("end")
                if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end):
                    fail(f"{item['item_id']} has an invalid target span")
                observed = item.get("observed")
                if original_text[start:end] != observed:
                    fail(f"{item['item_id']} target preimage changed")
                replacement = "" if decision["decision"] == "delete" else decision["reading"]
                spans.append((start, end, observed, replacement, item, decision))

            spans.sort(key=lambda span: span[0])
            for left, right in zip(spans, spans[1:]):
                if left[1] > right[0]:
                    fail(f"overlapping reviewed spans in {display(path)}:{line_number}")
            changed_text = original_text
            for start, end, _observed, replacement, _item, _decision in reversed(spans):
                changed_text = changed_text[:start] + replacement + changed_text[end:]
            if changed_text == original_text:
                fail(f"reviewed edits do not change {display(path)}:{line_number}")
            row["text"] = changed_text
            applied_line = json.dumps(row, ensure_ascii=False) + newline
            lines[line_number - 1] = applied_line
            row_plans.append({
                "line": line_number,
                "locus": row.get("locus"),
                "original_line": original_line,
                "applied_line": applied_line,
                "original_line_sha256": sha256_bytes(original_line.encode()),
                "applied_line_sha256": sha256_bytes(applied_line.encode()),
                "text_before": original_text,
                "text_after": changed_text,
                "edits": [{
                    "item_id": item["item_id"],
                    "start": start,
                    "end": end,
                    "observed": observed,
                    "decision": decision["decision"],
                    "reading": replacement,
                    "evidence_url": decision["evidence_url"],
                    "reviewer": decision["reviewer"],
                    "reviewed_at": decision["reviewed_at"],
                    "notes": decision.get("notes", ""),
                } for start, end, observed, replacement, item, decision in spans],
            })
        after = "".join(lines).encode("utf-8")
        file_plans.append({
            "path": path,
            "file": display(path),
            "sha256_before": sha256_bytes(before),
            "sha256_after": sha256_bytes(after),
            "before": before,
            "after": after,
            "rows": row_plans,
        })

    if not file_plans:
        fail("packet contains no decisive edits")
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
    }


def audit_record(plan: dict, audit_path: Path, date: str) -> dict:
    files = [{key: value for key, value in block.items()
              if key not in {"path", "before", "after"}}
             for block in plan["files"]]
    edits = sum(len(row["edits"]) for block in files for row in block["rows"])
    rows = sum(len(block["rows"]) for block in files)
    return {
        "schema_version": 1,
        "what": "scan-reviewed, occurrence-specific non-final grave repairs",
        "issue": "open-greek/open-greek-corpus#31",
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
        "edits_applied": edits,
        "rows_touched": rows,
        "files_touched": len(files),
        "files": files,
        "reverse": f"python3 scripts/{Path(__file__).name} --audit {display(audit_path)} --unapply",
    }


def apply(plan: dict, audit_path: Path, date: str) -> None:
    if audit_path.exists():
        fail(f"audit already exists: {display(audit_path)}")
    written = []
    try:
        for block in plan["files"]:
            if sha256_path(block["path"]) != block["sha256_before"]:
                fail(f"{block['file']} changed after planning")
            atomic_write(block["path"], block["after"])
            written.append(block)
        record = audit_record(plan, audit_path, date)
        atomic_write(
            audit_path,
            (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode(),
        )
    except BaseException:
        for block in reversed(written):
            atomic_write(block["path"], block["before"])
        raise


def unapply(audit_path: Path) -> None:
    if not audit_path.exists():
        fail(f"no audit at {display(audit_path)}")
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    restores = []
    corpus_root = (DATA / "corpus").resolve()
    for block in record.get("files", []):
        path = resolve(Path(block["file"])).resolve()
        if not path.is_relative_to(corpus_root):
            fail(f"audit points outside data/corpus: {path}")
        current = path.read_bytes()
        if sha256_bytes(current) != block["sha256_after"]:
            fail(f"{block['file']} has moved since this audit")
        lines = current.decode("utf-8").splitlines(keepends=True)
        for row in block["rows"]:
            index = row["line"] - 1
            if index >= len(lines) or lines[index] != row["applied_line"]:
                fail(f"{block['file']}:{row['line']} applied preimage changed")
            lines[index] = row["original_line"]
        before = "".join(lines).encode("utf-8")
        if sha256_bytes(before) != block["sha256_before"]:
            fail(f"unapply would not restore {block['file']} byte-for-byte")
        restores.append((path, before))
    for path, before in restores:
        atomic_write(path, before)
    audit_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--queue", type=Path, default=Path("data/review/issue-31.jsonl"))
    parser.add_argument("--reviewed", type=Path,
                        default=Path("data/review/issue-31.reviewed.jsonl"))
    parser.add_argument("--manifest", type=Path,
                        default=Path("data/review/issue-31.manifest.json"))
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--audit-tag", default=dt.date.today().isoformat())
    parser.add_argument("--date", default=dt.date.today().isoformat())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--unapply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not TAG_RE.fullmatch(args.audit_tag):
        fail("--audit-tag may contain only letters, numbers, dot, dash, and underscore")
    audit_path = resolve(args.audit) if args.audit else (
        DATA / "corpus_changes" / f"issue-31-reviewed.{args.audit_tag}.applied.json"
    )
    if args.unapply:
        unapply(audit_path)
        print(f"UNAPPLIED: restored corpus from {display(audit_path)}")
        return

    plan = build_plan(
        resolve(args.queue), resolve(args.reviewed), resolve(args.manifest),
    )
    edits = sum(plan["summary"].values()) - plan["summary"].get("defer", 0)
    rows = sum(len(block["rows"]) for block in plan["files"])
    print(f"reviewed decisions: {dict(sorted(plan['summary'].items()))}")
    print(f"{edits} exact edits in {rows} rows across {len(plan['files'])} files")
    if not args.apply:
        print("CHECK only (pass --apply to write)")
        return
    apply(plan, audit_path, args.date)
    print(f"APPLIED: audit {display(audit_path)}")


if __name__ == "__main__":
    main()
