import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import apply_reviewed_ocr_pages as page_apply  # noqa: E402
import build_human_review_queue as review  # noqa: E402


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def fixture(tmp_path: Path, *, stale: bool = False, partial: bool = False):
    corpus = tmp_path / "data/corpus/work.jsonl"
    rows = [
        {"urn": "author.work", "edition": "qwen-test", "source": "ocr",
         "license": "PD", "locus": "scan_0010.1", "text": "old main"},
        {"urn": "author.work", "edition": "qwen-test", "source": "ocr",
         "license": "PD", "locus": "scan_0010.2", "text": "old notes"},
        {"urn": "author.work", "edition": "qwen-test", "source": "ocr",
         "license": "PD", "locus": "scan_0011.1", "text": "next page"},
    ]
    write_jsonl(corpus, rows)
    queued_rows = [{
        "line": index + 1, "locus": row["locus"], "source": row["source"],
        "edition": row["edition"], "text": row["text"],
        "text_sha256": sha(row["text"].encode()),
    } for index, row in enumerate(rows[:1 if partial else 2])]
    if stale:
        queued_rows[0]["text"] = "stale"
    text = "\n".join(row["text"] for row in queued_rows)
    item = {
        "item_id": "ogc-2-test", "issue": 2, "kind": "raw-ocr-page",
        "file": "data/corpus/work.jsonl", "page": "scan_0010",
        "loci": [row["locus"] for row in queued_rows], "rows": queued_rows,
        "text": text, "source_text_sha256": sha(text.encode()),
        "scan_url": "https://archive.org/details/book/page/n10/mode/1up",
        "allowed_decisions": ["transcribe", "defer"],
        "reading_required_for": ["transcribe"],
        "segments_required_for": ["transcribe"],
        "evidence_required_for": ["transcribe"],
    }
    queue = tmp_path / "data/review/issue-2.jsonl"
    write_jsonl(queue, [item])
    queue_sha = sha(queue.read_bytes())
    segments = [
        {"locus": "scan_0010.1", "text": "new main"},
        {"locus": "scan_0010.2", "text": "new notes"},
    ][:len(queued_rows)]
    reviewed = tmp_path / "data/review/issue-2.reviewed.jsonl"
    write_jsonl(reviewed, [{
        "item_id": item["item_id"], "issue": 2, "kind": "raw-ocr-page",
        "queue_sha256": queue_sha, "decision": "transcribe",
        "reading": "\n".join(row["text"] for row in segments),
        "segments": segments, "evidence_url": item["scan_url"],
        "reviewer": "Reviewer", "reviewed_at": "2026-09-14", "notes": "scan",
    }])
    manifest = tmp_path / "data/review/issue-2.manifest.json"
    manifest.write_text(json.dumps({
        "issue": "open-greek/open-greek-corpus#2", "queue_sha256": queue_sha,
        "items": 1, "release_id": "test", "corpus_sha256": "pin",
    }), encoding="utf-8")
    return corpus, queue, reviewed, manifest


def configure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(page_apply, "REPO", tmp_path)
    monkeypatch.setattr(page_apply, "DATA", tmp_path / "data")
    monkeypatch.setattr(page_apply, "CORPUS", tmp_path / "data/corpus")


def test_apply_and_unapply_segmented_page_byte_exact(tmp_path, monkeypatch):
    corpus, queue, reviewed, manifest = fixture(tmp_path)
    configure(tmp_path, monkeypatch)
    audit = tmp_path / "data/corpus_changes/page.applied.json"
    before = corpus.read_bytes()

    plan = page_apply.build_plan(queue, reviewed, manifest)
    assert len(plan["pages"]) == 1
    assert sum(len(block["rows_changed"]) for block in plan["files"]) == 2
    page_apply.apply(plan, audit, "2026-09-14")

    rows = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
    assert [row["text"] for row in rows] == ["new main", "new notes", "next page"]
    assert "corrections" not in rows[0]
    page_apply.unapply(audit)
    assert corpus.read_bytes() == before
    assert not audit.exists()


def test_stale_row_preimage_is_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path, stale=True)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="row text preimage changed"):
        page_apply.build_plan(queue, reviewed, manifest)


def test_partial_page_boundary_map_is_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path, partial=True)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="complete current page"):
        page_apply.build_plan(queue, reviewed, manifest)


def test_sealed_segment_order_is_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path)
    decisions = list(page_apply.read_jsonl(reviewed))
    decisions[0]["segments"].reverse()
    write_jsonl(reviewed, decisions)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="exactly once and in order"):
        page_apply.build_plan(queue, reviewed, manifest)
