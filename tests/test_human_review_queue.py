import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_human_review_queue as review  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def fixture_paths(tmp_path: Path) -> review.Paths:
    paths = review.Paths(tmp_path)
    paths.corpus.mkdir(parents=True)
    paths.provenance.mkdir(parents=True)
    (paths.data / "corpus_release.json").write_text(json.dumps({
        "release_id": "test-release",
        "pin": {"corpus_sha256": "abc123"},
    }), encoding="utf-8")
    return paths


def add_scan(paths: review.Paths, urn: str, edition: str, run: str = "scan") -> None:
    (paths.provenance / f"{urn}.json").write_text(json.dumps({
        "urn": urn,
        "edition": edition,
        "run_slug": run,
        "source_scan": {"source": "archive.org", "public_id": "scan-book"},
    }), encoding="utf-8")


def test_scan_url_prefers_exact_volume_edition(tmp_path):
    paths = fixture_paths(tmp_path)
    (paths.provenance / "author.work.json").write_text(json.dumps({
        "urn": "author.work",
        "edition": "volume-1",
        "source_scan": {"source": "archive.org", "public_id": "book-1"},
        "volumes": [{
            "edition": "volume-2",
            "source_scan": {"source": "archive.org", "public_id": "book-2"},
        }],
    }), encoding="utf-8")

    link = review.scan_url({
        "urn": "author.work", "edition": "volume-2", "locus": "scan_0042.1",
    }, review.provenance_indexes(paths))

    assert link == "https://archive.org/details/book-2/page/n42/mode/1up"


def test_nonfinal_grave_queue_joins_context_candidates_and_scan(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "author.work", "qwen-test"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [{
        "urn": urn, "edition": edition, "source": "ocr",
        "locus": "scan_0042.1", "text": "λόγος ἐπεὶδὴ τέλος",
    }])
    add_scan(paths, urn, edition)
    (paths.data / "nonfinal_graves.json").write_text(json.dumps({
        "largest_forms": [{"form": "ἐπεὶδὴ", "tokens": 10}],
        "skeleton_class": {"decided": [{"form": "ἐπεὶδὴ", "target": "ἐπειδή"}]},
    }), encoding="utf-8")

    items, inputs = review.build_issue_31(paths, limit=10, seed="test")

    assert inputs == [paths.data / "nonfinal_graves.json"]
    assert len(items) == 1
    item = items[0]
    assert item["observed"] == "ἐπεὶδὴ"
    assert item["target"] == {"start": 6, "end": 12}
    assert item["corpus_evidence"]["target"] == "ἐπειδή"
    assert "<TARGET>" in item["context"]
    assert item["scan_url"].endswith("/scan-book/page/n42/mode/1up")


def test_duplicate_queue_joins_complete_page_text(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "author.work", "qwen-test"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0010.1", "text": "alpha"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0010.2", "text": "beta"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0020.1", "text": "alpha beta"},
    ])
    add_scan(paths, urn, edition)
    artifact = paths.data / "duplicate_page_candidates.json"
    artifact.write_text(json.dumps({"pairs": [{
        "file": f"data/corpus/{urn}.jsonl", "served": True,
        "locus_a": "scan_0010", "locus_b": "scan_0020",
        "containment": 0.95, "same_item": True,
    }]}), encoding="utf-8")

    items, _ = review.build_issue_33(paths, limit=10, seed="test")

    assert len(items) == 1
    assert items[0]["page_a"]["text"] == "alpha\nbeta"
    assert items[0]["page_b"]["text"] == "alpha beta"
    assert items[0]["signals"]["same_item"] is True


def test_correction_queue_hides_answer_key_and_method(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "author.work", "qwen-test"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [{
        "urn": urn, "edition": edition, "source": "ocr",
        "locus": "scan_0042.1", "text": "the corrected reading",
    }])
    add_scan(paths, urn, edition)
    corrections = paths.data / "applied.jsonl"
    write_jsonl(corrections, [{
        "urn": urn, "locus": "scan_0042.1", "original": "wrong",
        "corrected": "corrected", "by": "model", "confidence": 0.9,
        "status": "accepted", "evidence": "hidden upstream evidence",
    }])

    items, audit, _ = review.build_issue_1(paths, 10, "test", corrections)

    assert len(items) == len(audit) == 1
    assert set(items[0]["options"].values()) == {"wrong", "corrected"}
    assert "corrected" not in items[0]["context"]
    assert "method" not in items[0]
    assert audit[0]["method"] == "model"
    assert items[0]["options"][audit[0]["applied_option"]] == "corrected"


def test_raw_ocr_queue_selects_only_raw_ocr_works(tmp_path):
    paths = fixture_paths(tmp_path)
    write_jsonl(paths.corpus / "raw.work.jsonl", [{
        "urn": "raw.work", "edition": "qwen-test", "source": "ocr",
        "locus": "scan_0042.1", "text": "raw page text",
    }])
    add_scan(paths, "raw.work", "qwen-test")
    with (paths.data / "corpus_catalog.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "slug", "work_id", "author", "title", "tokens", "source",
            "correction", "unattested_rate",
        ], delimiter="\t")
        writer.writeheader()
        writer.writerow({
            "slug": "raw.work", "work_id": "ogc1", "author": "A", "title": "T",
            "tokens": 100, "source": "ocr", "correction": "raw-ocr",
            "unattested_rate": 0.2,
        })
        writer.writerow({
            "slug": "other.work", "work_id": "ogc2", "author": "B", "title": "U",
            "tokens": 200, "source": "ocr", "correction": "auto-corrected",
            "unattested_rate": 0.1,
        })

    items, _ = review.build_issue_2(paths, 10, "test")

    assert [item["work"]["slug"] for item in items] == ["raw.work"]
    assert items[0]["scan_url"].endswith("/scan-book/page/n42/mode/1up")


def test_decision_validator_requires_provenance_and_seals_valid_rows(tmp_path):
    queue = tmp_path / "queue.jsonl"
    item = {
        "item_id": "ogc-31-test", "issue": 31, "kind": "nonfinal-grave",
        "allowed_decisions": ["replace", "defer"],
        "reading_required_for": ["replace"],
        "evidence_required_for": ["replace"],
    }
    write_jsonl(queue, [item])
    decisions = tmp_path / "decisions.tsv"
    with decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=review.DECISION_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow({
            "item_id": item["item_id"], "decision": "replace", "reading": "right",
            "reviewer": "Reviewer", "reviewed_at": "2026-09-14",
        })
    with pytest.raises(SystemExit, match="evidence_url is required"):
        review.validate_decisions(queue, decisions)

    rows = list(csv.DictReader(decisions.open(encoding="utf-8"), delimiter="\t"))
    rows[0]["evidence_url"] = "https://example.test/scan"
    with decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=review.DECISION_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    sealed = tmp_path / "sealed.jsonl"

    assert review.validate_decisions(queue, decisions, sealed) == 1
    record = json.loads(sealed.read_text(encoding="utf-8"))
    assert record["decision"] == "replace"
    assert record["queue_sha256"] == hashlib.sha256(queue.read_bytes()).hexdigest()
