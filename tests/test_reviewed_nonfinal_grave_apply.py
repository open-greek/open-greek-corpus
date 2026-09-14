import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import apply_reviewed_nonfinal_graves as reviewed_apply  # noqa: E402


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def fixture(tmp_path: Path, *, observed: str = "ἐπεὶδὴ",
            reviewed: bool = True):
    corpus = tmp_path / "data/corpus/work.jsonl"
    write_jsonl(corpus, [{
        "urn": "author.work", "edition": "qwen-test", "source": "ocr",
        "locus": "page_0001.1", "text": f"λόγος {observed} τέλος",
    }])
    start = len("λόγος ")
    queue = tmp_path / "data/review/issue-31.jsonl"
    item = {
        "item_id": "ogc-31-test", "issue": 31, "kind": "nonfinal-grave",
        "row": {"file": "data/corpus/work.jsonl", "line": 1,
                "locus": "page_0001.1", "source": "ocr", "edition": "qwen-test"},
        "target": {"start": start, "end": start + len(observed)},
        "observed": observed,
        "scan_url": "https://archive.org/details/book/page/n1/mode/1up",
        "allowed_decisions": ["split", "defer"],
    }
    write_jsonl(queue, [item])
    queue_sha = sha(queue.read_bytes())
    sealed = tmp_path / "data/review/issue-31.reviewed.jsonl"
    if reviewed:
        write_jsonl(sealed, [{
            "item_id": "ogc-31-test", "issue": 31, "kind": "nonfinal-grave",
            "queue_sha256": queue_sha, "decision": "split",
            "reading": "ἐπεὶ δὴ", "evidence_url": item["scan_url"],
            "reviewer": "A Reviewer", "reviewed_at": "2026-09-14", "notes": "scan",
        }])
    else:
        write_jsonl(sealed, [])
    manifest = tmp_path / "data/review/issue-31.manifest.json"
    manifest.write_text(json.dumps({
        "issue": "open-greek/open-greek-corpus#31", "queue_sha256": queue_sha,
        "items": 1, "release_id": "test", "corpus_sha256": "test-pin",
    }), encoding="utf-8")
    return corpus, queue, sealed, manifest


def test_apply_and_unapply_are_exact_and_occurrence_specific(tmp_path, monkeypatch):
    corpus, queue, sealed, manifest = fixture(tmp_path)
    audit = tmp_path / "data/corpus_changes/reviewed.applied.json"
    before = corpus.read_bytes()
    monkeypatch.setattr(reviewed_apply, "REPO", tmp_path)
    monkeypatch.setattr(reviewed_apply, "DATA", tmp_path / "data")

    plan = reviewed_apply.build_plan(queue, sealed, manifest)
    assert corpus.read_bytes() == before
    reviewed_apply.apply(plan, audit, "2026-09-14")
    assert json.loads(corpus.read_text(encoding="utf-8"))["text"] == "λόγος ἐπεὶ δὴ τέλος"
    record = json.loads(audit.read_text(encoding="utf-8"))
    assert record["edits_applied"] == 1
    assert record["files"][0]["sha256_before"] == sha(before)

    reviewed_apply.unapply(audit)
    assert corpus.read_bytes() == before
    assert not audit.exists()


def test_stale_target_preimage_is_refused(tmp_path, monkeypatch):
    corpus, queue, sealed, manifest = fixture(tmp_path)
    row = json.loads(corpus.read_text(encoding="utf-8"))
    row["text"] = "λόγος ἐπειδὴ τέλος"
    write_jsonl(corpus, [row])
    monkeypatch.setattr(reviewed_apply, "REPO", tmp_path)
    monkeypatch.setattr(reviewed_apply, "DATA", tmp_path / "data")

    with pytest.raises(SystemExit, match="target preimage changed"):
        reviewed_apply.build_plan(queue, sealed, manifest)


def test_partial_review_is_refused(tmp_path, monkeypatch):
    _corpus, queue, sealed, manifest = fixture(tmp_path, reviewed=False)
    monkeypatch.setattr(reviewed_apply, "REPO", tmp_path)
    monkeypatch.setattr(reviewed_apply, "DATA", tmp_path / "data")

    with pytest.raises(SystemExit, match="review is incomplete"):
        reviewed_apply.build_plan(queue, sealed, manifest)
