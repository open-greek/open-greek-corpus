#!/usr/bin/env python3
"""Apply sealed issue #33 page decisions without deleting either OCR reading.

Only ``drop_a`` and ``drop_b`` decisions mutate the corpus. The named page is
moved to a pass-specific file in data/corpus_secondary; ``keep_both`` and
``defer`` are no-ops. Merges are deliberately unsupported because they create a
reading that neither scan attests. The default is a dry run.

  python3 scripts/apply_reviewed_duplicate_pages.py
  python3 scripts/apply_reviewed_duplicate_pages.py --apply
  python3 scripts/apply_reviewed_duplicate_pages.py --unapply
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
CORPUS = DATA / "corpus"
SECONDARY = DATA / "corpus_secondary"
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

    if manifest.get("issue") != "open-greek/open-greek-corpus#33":
        fail("manifest is not for issue #33")
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
        if item.get("issue") != 33 or item.get("kind") != "duplicate-page-pair":
            fail(f"{item_id} is not an issue #33 item")
        if decision.get("queue_sha256") != queue_sha:
            fail(f"{item_id} was sealed against a different queue")
        if decision.get("issue") != 33 or decision.get("kind") != "duplicate-page-pair":
            fail(f"{item_id} has the wrong sealed issue metadata")
        choice = decision.get("decision")
        if choice not in item.get("allowed_decisions", []):
            fail(f"{item_id} has invalid decision {choice!r}")
        if choice == "merge":
            fail(f"{item_id} requests a merge; reviewed merges require a separate transcription tool")
        if not decision.get("reviewer") or not decision.get("reviewed_at"):
            fail(f"{item_id} lacks reviewer provenance")
        if choice in {"drop_a", "drop_b", "keep_both"}:
            urls = {item.get("page_a", {}).get("scan_url"),
                    item.get("page_b", {}).get("scan_url")}
            if decision.get("evidence_url") not in urls:
                fail(f"{item_id} evidence is not one of its pinned page images")
    return queue_rows, reviewed, manifest


def terminal(page: str, edges: dict[str, str], label: str) -> str:
    seen = []
    while page in edges:
        if page in seen:
            fail(f"reviewed decisions form a cycle in {label}: {' -> '.join(seen + [page])}")
        seen.append(page)
        page = edges[page]
    return page


def build_plan(queue_path: Path, reviewed_path: Path,
               manifest_path: Path, audit_tag: str) -> dict:
    queue_rows, reviewed, manifest = checked_inputs(
        queue_path, reviewed_path, manifest_path,
    )
    summary = collections.Counter(row["decision"] for row in reviewed.values())
    mutations: dict[Path, list[dict]] = collections.defaultdict(list)
    corpus_root = CORPUS.resolve()

    for item in queue_rows:
        decision = reviewed[item["item_id"]]
        if decision["decision"] not in {"drop_a", "drop_b"}:
            continue
        path = resolve(Path(str(item.get("file") or ""))).resolve()
        if not path.is_relative_to(corpus_root):
            fail(f"{item['item_id']} points outside data/corpus")
        drop_side = "page_a" if decision["decision"] == "drop_a" else "page_b"
        keep_side = "page_b" if drop_side == "page_a" else "page_a"
        mutations[path].append({
            "item": item,
            "decision": decision,
            "drop": item[drop_side]["locus"],
            "keep": item[keep_side]["locus"],
        })

    if not mutations:
        fail("packet contains no reviewed page displacements")

    file_plans = []
    all_displacements = []
    for path, decisions in sorted(mutations.items(), key=lambda pair: str(pair[0])):
        before = path.read_bytes()
        lines = before.decode("utf-8").splitlines(keepends=True)
        pages: dict[str, list[tuple[int, str, dict]]] = collections.defaultdict(list)
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                fail(f"{display(path)}:{index + 1} is invalid JSON: {error}")
            pages[page_stem(row.get("locus"))].append((index, line, row))

        edges: dict[str, str] = {}
        edge_items: dict[str, list[dict]] = collections.defaultdict(list)
        for entry in decisions:
            item = entry["item"]
            for side in ("page_a", "page_b"):
                page = item[side]["locus"]
                if not pages.get(page):
                    fail(f"{item['item_id']} page {page} is no longer in {display(path)}")
                observed = "\n".join(row.get("text") or "" for _, _, row in pages[page])
                if observed != item[side].get("text"):
                    fail(f"{item['item_id']} page {page} text changed after review")
            previous = edges.get(entry["drop"])
            if previous is not None and previous != entry["keep"]:
                fail(f"{entry['drop']} was reviewed against two different retained pages")
            edges[entry["drop"]] = entry["keep"]
            edge_items[entry["drop"]].append(entry)

        terminals = {page: terminal(page, edges, display(path)) for page in edges}
        for root in terminals.values():
            if root not in pages:
                fail(f"terminal retained page {root} is absent from {display(path)}")

        drop_pages = set(edges)
        removed = []
        drop_indices = set()
        witness_rows = []
        for page in sorted(drop_pages):
            direct = edge_items[page][0]
            for index, line, row in pages[page]:
                if row.get("rank") == "secondary":
                    fail(f"{display(path)}:{index + 1} is already a secondary row")
                removed.append({
                    "index": index,
                    "line": index + 1,
                    "locus": row.get("locus"),
                    "original_line": line,
                    "original_line_sha256": sha256_bytes(line.encode("utf-8")),
                })
                drop_indices.add(index)
                moved = dict(row)
                moved["rank"] = "secondary"
                moved["secondary_reason"] = (
                    "scan-reviewed second OCR reading of a page this work already "
                    "serves; preserved outside the served counts under issue #33 "
                    f"({direct['decision']['reviewed_at']})"
                )
                witness_rows.append(moved)

            page_text = "\n".join(row.get("text") or "" for _, _, row in pages[page])
            all_displacements.append({
                "item_id": direct["item"]["item_id"],
                "file": display(path),
                "displaced_page": page,
                "retained_page_direct": edges[page],
                "retained_page_terminal": terminals[page],
                "rows": len(pages[page]),
                "greek_tokens": len(GREEK.findall(page_text)),
                "evidence_url": direct["decision"]["evidence_url"],
                "reviewer": direct["decision"]["reviewer"],
                "reviewed_at": direct["decision"]["reviewed_at"],
                "notes": direct["decision"].get("notes", ""),
            })

        after = "".join(line for index, line in enumerate(lines)
                        if index not in drop_indices).encode("utf-8")
        slug = path.name.removesuffix(".jsonl")
        witness_path = SECONDARY / f"{slug}.duplicate-read-review-{audit_tag}.jsonl"
        witness_body = "".join(
            json.dumps(row, ensure_ascii=False) + "\n" for row in witness_rows
        ).encode("utf-8")
        file_plans.append({
            "path": path,
            "file": display(path),
            "before": before,
            "after": after,
            "sha256_before": sha256_bytes(before),
            "sha256_after": sha256_bytes(after),
            "rows_before": sum(bool(line.strip()) for line in lines),
            "rows_after": sum(bool(line.strip()) for index, line in enumerate(lines)
                              if index not in drop_indices),
            "removed_rows": sorted(removed, key=lambda row: row["index"]),
            "witness_path": witness_path,
            "witness_file": display(witness_path),
            "witness_body": witness_body,
            "witness_sha256": sha256_bytes(witness_body),
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
        "displacements": all_displacements,
    }


def audit_record(plan: dict, audit_path: Path, date: str) -> dict:
    files = {}
    for block in plan["files"]:
        files[block["file"]] = {
            key: value for key, value in block.items()
            if key not in {"path", "before", "after", "witness_path", "witness_body", "file"}
        }
    return {
        "schema_version": 1,
        "what": "scan-reviewed duplicate OCR pages moved from served text to secondary witnesses",
        "issue": "open-greek/open-greek-corpus#33",
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
        "pages_displaced": len(plan["displacements"]),
        "rows_displaced": sum(len(block["removed_rows"]) for block in plan["files"]),
        "greek_tokens_displaced": sum(row["greek_tokens"] for row in plan["displacements"]),
        "files_touched": len(plan["files"]),
        "displacements": plan["displacements"],
        "witness_files_written": [block["witness_file"] for block in plan["files"]],
        "files": files,
        "policy": "Every displacement is a sealed page-image decision. No readings are merged or deleted; displaced rows remain published as secondary witnesses.",
        "reverse": f"python3 scripts/{Path(__file__).name} --audit {display(audit_path)} --unapply",
    }


def apply(plan: dict, audit_path: Path, date: str) -> None:
    if audit_path.exists():
        fail(f"audit already exists: {display(audit_path)}")
    for block in plan["files"]:
        if sha256_path(block["path"]) != block["sha256_before"]:
            fail(f"{block['file']} changed after planning")
        if block["witness_path"].exists():
            fail(f"witness already exists: {block['witness_file']}")

    written_files = []
    written_witnesses = []
    try:
        for block in plan["files"]:
            atomic_write(block["path"], block["after"])
            written_files.append(block)
            atomic_write(block["witness_path"], block["witness_body"])
            written_witnesses.append(block["witness_path"])
        atomic_write(
            audit_path,
            (json.dumps(audit_record(plan, audit_path, date),
                        ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
    except BaseException:
        for block in reversed(written_files):
            atomic_write(block["path"], block["before"])
        for path in written_witnesses:
            path.unlink(missing_ok=True)
        audit_path.unlink(missing_ok=True)
        raise


def unapply(audit_path: Path) -> None:
    if not audit_path.exists():
        fail(f"no audit at {display(audit_path)}")
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    restores = []
    witnesses = []
    corpus_root = CORPUS.resolve()
    secondary_root = SECONDARY.resolve()

    for file, block in record.get("files", {}).items():
        path = resolve(Path(file)).resolve()
        witness = resolve(Path(block["witness_file"])).resolve()
        if not path.is_relative_to(corpus_root):
            fail(f"audit points outside data/corpus: {path}")
        if not witness.is_relative_to(secondary_root):
            fail(f"audit points outside data/corpus_secondary: {witness}")
        current = path.read_bytes()
        if sha256_bytes(current) != block["sha256_after"]:
            fail(f"{file} has moved since this audit")
        if not witness.exists() or sha256_path(witness) != block["witness_sha256"]:
            fail(f"witness changed or is missing: {display(witness)}")
        lines = current.decode("utf-8").splitlines(keepends=True)
        for removed in sorted(block["removed_rows"], key=lambda row: row["index"]):
            lines.insert(removed["index"], removed["original_line"])
        before = "".join(lines).encode("utf-8")
        if sha256_bytes(before) != block["sha256_before"]:
            fail(f"unapply would not restore {file} byte-for-byte")
        restores.append((path, before))
        witnesses.append(witness)

    for path, body in restores:
        atomic_write(path, body)
    for witness in witnesses:
        witness.unlink()
    audit_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--queue", type=Path, default=Path("data/review/issue-33.jsonl"))
    parser.add_argument("--reviewed", type=Path,
                        default=Path("data/review/issue-33.reviewed.jsonl"))
    parser.add_argument("--manifest", type=Path,
                        default=Path("data/review/issue-33.manifest.json"))
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
        DATA / "corpus_changes" / f"issue-33-reviewed.{args.audit_tag}.applied.json"
    )
    if args.unapply:
        unapply(audit_path)
        print(f"UNAPPLIED: restored corpus and removed witnesses from {display(audit_path)}")
        return

    plan = build_plan(
        resolve(args.queue), resolve(args.reviewed), resolve(args.manifest), args.audit_tag,
    )
    print(f"reviewed decisions: {dict(sorted(plan['summary'].items()))}")
    print(f"{len(plan['displacements'])} pages, "
          f"{sum(len(block['removed_rows']) for block in plan['files'])} rows, "
          f"{sum(row['greek_tokens'] for row in plan['displacements']):,} Greek tokens "
          f"move to {len(plan['files'])} witness files")
    if not args.apply:
        print("CHECK only (pass --apply to write)")
        return
    apply(plan, audit_path, args.date)
    print(f"APPLIED: audit {display(audit_path)}")


if __name__ == "__main__":
    main()
