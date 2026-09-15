import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import serve_human_review as server  # noqa: E402


def write_queue(path: Path) -> None:
    path.write_text(json.dumps({
        "item_id": "ogc-31-test",
        "issue": 31,
        "kind": "nonfinal-grave",
        "observed": "ἐπεὶδὴ",
        "scan_url": "https://archive.org/details/book/page/n42/mode/1up",
        "allowed_decisions": ["replace", "defer"],
        "reading_required_for": ["replace"],
        "evidence_required_for": ["replace"],
    }, ensure_ascii=False) + "\n", encoding="utf-8")


def test_archive_page_becomes_direct_review_image():
    assert server.archive_image_url(
        "https://archive.org/details/book/page/n42/mode/1up"
    ) == "https://archive.org/download/book/page/n42_w1800.jpg"
    assert server.archive_image_url("https://example.test/book") is None


def test_payload_adds_both_duplicate_page_images(tmp_path):
    queue, decisions = tmp_path / "queue.jsonl", tmp_path / "decisions.tsv"
    write_jsonl = json.dumps({
        "item_id": "ogc-33-test", "issue": 33, "kind": "duplicate-page-pair",
        "page_a": {"scan_url": "https://archive.org/details/book/page/n10/mode/1up"},
        "page_b": {"scan_url": "https://archive.org/details/book/page/n20/mode/1up"},
        "allowed_decisions": ["defer"],
    }) + "\n"
    queue.write_text(write_jsonl, encoding="utf-8")

    item = server.ReviewStore(queue, decisions).payload()["items"][0]

    assert item["page_a"]["image_url"].endswith("/page/n10_w1800.jpg")
    assert item["page_b"]["image_url"].endswith("/page/n20_w1800.jpg")


def test_store_writes_valid_decision_atomically(tmp_path):
    queue, decisions = tmp_path / "queue.jsonl", tmp_path / "decisions.tsv"
    write_queue(queue)
    store = server.ReviewStore(queue, decisions)

    saved = store.save({
        "item_id": "ogc-31-test",
        "decision": "replace",
        "reading": "ἐπειδή",
        "evidence_url": "https://archive.org/details/book/page/n42/mode/1up",
        "reviewer": "Rater One",
        "reviewed_at": "2026-09-14",
        "notes": "",
    })

    assert saved["reading"] == "ἐπειδή"
    rows = list(csv.DictReader(decisions.open(encoding="utf-8"), delimiter="\t"))
    assert rows == [saved]
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("change,message", [
    ({"reading": ""}, "reviewed reading"),
    ({"evidence_url": ""}, "evidence URL"),
    ({"reviewer": ""}, "reviewer"),
])
def test_store_rejects_incomplete_decisions(tmp_path, change, message):
    queue, decisions = tmp_path / "queue.jsonl", tmp_path / "decisions.tsv"
    write_queue(queue)
    candidate = {
        "item_id": "ogc-31-test", "decision": "replace", "reading": "ἐπειδή",
        "evidence_url": "https://example.test/scan", "reviewer": "Rater",
        "reviewed_at": "2026-09-14", "notes": "",
    }
    candidate.update(change)

    with pytest.raises(server.ReviewError, match=message):
        server.ReviewStore(queue, decisions).save(candidate)

    assert not decisions.exists()


def test_store_rejects_non_object_payload(tmp_path):
    queue, decisions = tmp_path / "queue.jsonl", tmp_path / "decisions.tsv"
    write_queue(queue)

    with pytest.raises(server.ReviewError, match="JSON object"):
        server.ReviewStore(queue, decisions).save([])

    assert not decisions.exists()


def test_store_serializes_and_checks_page_segments(tmp_path):
    queue, decisions = tmp_path / "queue.jsonl", tmp_path / "decisions.tsv"
    write_queue(queue)
    item = json.loads(queue.read_text(encoding="utf-8"))
    item.update({
        "issue": 2,
        "kind": "raw-ocr-page",
        "allowed_decisions": ["transcribe"],
        "reading_required_for": ["transcribe"],
        "segments_required_for": ["transcribe"],
        "evidence_required_for": ["transcribe"],
        "rows": [
            {"locus": "scan_0042.1", "text": "old"},
            {"locus": "scan_0042.2", "text": "notes"},
        ],
    })
    write_queue_body = json.dumps(item, ensure_ascii=False) + "\n"
    queue.write_text(write_queue_body, encoding="utf-8")
    store = server.ReviewStore(queue, decisions)
    candidate = {
        "item_id": "ogc-31-test", "decision": "transcribe",
        "reading": "new\napparatus",
        "segments": [
            {"locus": "scan_0042.1", "text": "new"},
            {"locus": "scan_0042.2", "text": "apparatus"},
        ],
        "evidence_url": item["scan_url"], "reviewer": "Rater",
        "reviewed_at": "2026-09-14", "notes": "",
    }
    saved = store.save(candidate)
    assert json.loads(saved["segments"]) == candidate["segments"]

    candidate["reading"] = "does not match"
    with pytest.raises(server.ReviewError, match="newline-joined"):
        store.save(candidate)
