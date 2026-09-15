import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import apply_reviewed_duplicate_pages as reviewed_apply  # noqa: E402


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def fixture(tmp_path: Path, *, stale: bool = False, cycle: bool = False,
            complete: bool = True):
    corpus = tmp_path / "data/corpus/work.jsonl"
    rows = [
        {"urn": "author.work", "source": "ocr", "locus": "scan_0010.1", "text": "alpha"},
        {"urn": "author.work", "source": "ocr", "locus": "scan_0010.2", "text": "beta"},
        {"urn": "author.work", "source": "ocr", "locus": "scan_0020.1", "text": "alpha beta"},
        {"urn": "author.work", "source": "ocr", "locus": "scan_0030.1", "text": "alpha beta?"},
    ]
    write_jsonl(corpus, rows)
    pages = {"scan_0010": "alpha\nbeta", "scan_0020": "alpha beta",
             "scan_0030": "alpha beta?"}
    if stale:
        pages["scan_0010"] = "old text"
    pairs = [("one", "scan_0010", "scan_0020", "drop_a")]
    pairs.append(("two", "scan_0020" if cycle else "scan_0030",
                  "scan_0010", "drop_a"))
    queue_rows, reviewed_rows = [], []
    for item_id, a, b, decision in pairs:
        queue_rows.append({
            "item_id": item_id, "issue": 33, "kind": "duplicate-page-pair",
            "file": "data/corpus/work.jsonl", "work": "author.work",
            "page_a": {"locus": a, "text": pages[a],
                       "scan_url": f"https://example.test/{a}"},
            "page_b": {"locus": b, "text": pages[b],
                       "scan_url": f"https://example.test/{b}"},
            "allowed_decisions": ["keep_both", "drop_a", "drop_b", "merge", "defer"],
        })
    queue = tmp_path / "data/review/issue-33.jsonl"
    write_jsonl(queue, queue_rows)
    queue_sha = sha(queue.read_bytes())
    for item, (_, _, _, decision) in zip(queue_rows, pairs):
        reviewed_rows.append({
            "item_id": item["item_id"], "issue": 33,
            "kind": "duplicate-page-pair", "queue_sha256": queue_sha,
            "decision": decision, "reading": "",
            "evidence_url": item["page_a"]["scan_url"],
            "reviewer": "Reviewer", "reviewed_at": "2026-09-14", "notes": "scan",
        })
    reviewed = tmp_path / "data/review/issue-33.reviewed.jsonl"
    write_jsonl(reviewed, reviewed_rows if complete else reviewed_rows[:1])
    manifest = tmp_path / "data/review/issue-33.manifest.json"
    manifest.write_text(json.dumps({
        "issue": "open-greek/open-greek-corpus#33", "queue_sha256": queue_sha,
        "items": len(queue_rows), "release_id": "test", "corpus_sha256": "pin",
    }), encoding="utf-8")
    return corpus, queue, reviewed, manifest


def configure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(reviewed_apply, "REPO", tmp_path)
    monkeypatch.setattr(reviewed_apply, "DATA", tmp_path / "data")
    monkeypatch.setattr(reviewed_apply, "CORPUS", tmp_path / "data/corpus")
    monkeypatch.setattr(reviewed_apply, "SECONDARY", tmp_path / "data/corpus_secondary")


def test_apply_and_unapply_preserve_overlapping_loser_as_witness(tmp_path, monkeypatch):
    corpus, queue, reviewed, manifest = fixture(tmp_path)
    configure(tmp_path, monkeypatch)
    audit = tmp_path / "data/corpus_changes/reviewed.applied.json"
    before = corpus.read_bytes()

    plan = reviewed_apply.build_plan(queue, reviewed, manifest, "test")
    assert len(plan["displacements"]) == 2
    assert {row["retained_page_terminal"] for row in plan["displacements"]} == {"scan_0020"}
    reviewed_apply.apply(plan, audit, "2026-09-14")

    served = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
    assert [row["locus"] for row in served] == ["scan_0020.1"]
    witness = tmp_path / "data/corpus_secondary/work.duplicate-read-review-test.jsonl"
    moved = [json.loads(line) for line in witness.read_text(encoding="utf-8").splitlines()]
    assert [row["locus"] for row in moved] == ["scan_0010.1", "scan_0010.2", "scan_0030.1"]
    assert all(row["rank"] == "secondary" for row in moved)

    reviewed_apply.unapply(audit)
    assert corpus.read_bytes() == before
    assert not witness.exists()
    assert not audit.exists()


def test_stale_page_preimage_is_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path, stale=True)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="text changed after review"):
        reviewed_apply.build_plan(queue, reviewed, manifest, "test")


def test_cycles_are_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path, cycle=True)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="form a cycle"):
        reviewed_apply.build_plan(queue, reviewed, manifest, "test")


def test_partial_review_is_refused(tmp_path, monkeypatch):
    _corpus, queue, reviewed, manifest = fixture(tmp_path, complete=False)
    configure(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="review is incomplete"):
        reviewed_apply.build_plan(queue, reviewed, manifest, "test")
