#!/usr/bin/env python3
"""Serve a local, scan-first interface for an OGC human-review packet.

The server binds to loopback, reads one generated queue, and atomically updates
its TSV decision sheet. It never edits corpus data.

  python3 scripts/serve_human_review.py \
      --queue data/review/issue-31.jsonl --open
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from build_human_review_queue import DECISION_FIELDS, output_family

REPO = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "human_review_ui"
ARCHIVE_PAGE = re.compile(
    r"^https://archive\.org/details/([^/]+)/page/n(\d+)/mode/1up$"
)
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


class ReviewError(ValueError):
    pass


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def archive_image_url(scan_url: object, width: int = 1800) -> str | None:
    match = ARCHIVE_PAGE.match(str(scan_url or ""))
    if not match:
        return None
    ident, leaf = match.groups()
    return f"https://archive.org/download/{ident}/page/n{leaf}_w{width}.jpg"


class ReviewStore:
    def __init__(self, queue_path: Path, decisions_path: Path):
        self.queue_path = queue_path.resolve()
        self.decisions_path = decisions_path.resolve()
        self.items = load_jsonl(self.queue_path)
        self.by_id = {item["item_id"]: item for item in self.items}
        if len(self.items) != len(self.by_id):
            raise ReviewError("queue contains duplicate item IDs")
        self.queue_sha256 = hashlib.sha256(self.queue_path.read_bytes()).hexdigest()
        self.lock = threading.Lock()
        self.decisions = self._load_decisions()

    def _load_decisions(self) -> dict[str, dict[str, str]]:
        if not self.decisions_path.exists():
            return {}
        with self.decisions_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        decisions = {}
        for row in rows:
            item_id = (row.get("item_id") or "").strip()
            if item_id in self.by_id and (row.get("decision") or "").strip():
                decisions[item_id] = {
                    field: (row.get(field) or "").strip() for field in DECISION_FIELDS
                }
        return decisions

    def payload(self) -> dict:
        items = [{**item, "image_url": archive_image_url(item.get("scan_url"))}
                 for item in self.items]
        return {
            "queue": self.queue_path.name,
            "queue_sha256": self.queue_sha256,
            "items": items,
            "decisions": self.decisions,
            "decision_fields": DECISION_FIELDS,
        }

    def save(self, candidate: dict) -> dict[str, str]:
        if not isinstance(candidate, dict):
            raise ReviewError("decision payload must be a JSON object")
        item_id = str(candidate.get("item_id") or "").strip()
        item = self.by_id.get(item_id)
        if not item:
            raise ReviewError(f"unknown item ID: {item_id}")
        row = {field: str(candidate.get(field) or "").strip()
               for field in DECISION_FIELDS}
        choice = row["decision"]
        if choice not in item.get("allowed_decisions", []):
            raise ReviewError(f"{choice!r} is not allowed for {item_id}")
        if not row["reviewer"] or not row["reviewed_at"]:
            raise ReviewError("reviewer and review date are required")
        if choice in item.get("reading_required_for", []) and not row["reading"]:
            raise ReviewError("this decision requires a reviewed reading")
        if choice in item.get("evidence_required_for", []) and not row["evidence_url"]:
            raise ReviewError("this decision requires an evidence URL")
        if choice == "defer" and not row["notes"]:
            raise ReviewError("a deferral requires a note")

        with self.lock:
            self.decisions[item_id] = row
            self._write()
        return row

    def _write(self) -> None:
        self.decisions_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            dir=self.decisions_path.parent,
            prefix=f".{self.decisions_path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS, delimiter="\t")
                writer.writeheader()
                for item in self.items:
                    writer.writerow(self.decisions.get(item["item_id"], {
                        "item_id": item["item_id"],
                    }))
            os.replace(temporary, self.decisions_path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise


class ReviewHandler(BaseHTTPRequestHandler):
    store: ReviewStore

    def send_json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/review":
            self.send_json(self.store.payload())
            return
        asset = {
            "/": ASSETS / "index.html",
            "/app.js": ASSETS / "app.js",
            "/styles.css": ASSETS / "styles.css",
        }.get(path)
        if not asset or not asset.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = asset.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", MIME[asset.suffix])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://unpkg.com; "
            "img-src 'self' https://archive.org https://*.archive.org data:; "
            "style-src 'self'; "
            "connect-src 'self'; frame-src https://archive.org",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/decision":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 64 * 1024:
                raise ReviewError("invalid request size")
            candidate = json.loads(self.rfile.read(size))
            self.send_json({"decision": self.store.save(candidate)})
        except (json.JSONDecodeError, ReviewError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt: str, *args: object) -> None:
        if self.path != "/api/review":
            super().log_message(fmt, *args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("--host must be a loopback address")
    queue = args.queue if args.queue.is_absolute() else REPO / args.queue
    if not queue.exists():
        raise SystemExit(f"queue not found: {queue}")
    decisions = args.decisions
    if decisions is None:
        decisions = output_family(queue)[0]
    elif not decisions.is_absolute():
        decisions = REPO / decisions
    ReviewHandler.store = ReviewStore(queue, decisions)
    server = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Reviewing {len(ReviewHandler.store.items)} items at {url}")
    print(f"Decision sheet: {decisions}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
