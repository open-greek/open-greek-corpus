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


def test_scan_url_uses_reocr_inventory_page_offset(tmp_path):
    paths = fixture_paths(tmp_path)
    inventory = paths.data / "inventory"
    inventory.mkdir()
    (inventory / "reocr_provenance.json").write_text(json.dumps({
        "editions": [{
            "base": "sample_run",
            "source_url": "https://archive.org/download/source-book/source-book.pdf",
            "align_method": "content-offset",
            "content_offset": 7,
        }],
    }), encoding="utf-8")

    link = review.scan_url({
        "urn": "author.work", "edition": "qwen36-sample_run",
        "locus": "sample_run_0042.1",
    }, review.provenance_indexes(paths))

    assert link == "https://archive.org/details/source-book/page/n34/mode/1up"


def test_scan_url_uses_explicit_printed_page_offset(tmp_path):
    paths = fixture_paths(tmp_path)
    inventory = paths.data / "inventory"
    inventory.mkdir()
    (inventory / "reocr_provenance.json").write_text(json.dumps({
        "editions": [{
            "base": "sample_run",
            "source_url": "https://archive.org/download/source-book/source-book.pdf",
            "align_method": "content-offset",
            "content_offset": 0,
            "printed_page_offset": 8,
        }],
    }), encoding="utf-8")

    link = review.scan_url({
        "urn": "author.work", "edition": "qwen36-sample_run",
        "locus": "599.1",
    }, review.provenance_indexes(paths))

    assert link == "https://archive.org/details/source-book/page/n607/mode/1up"


@pytest.mark.parametrize(("edition", "locus", "expected"), [
    ("qwen36-walz_rhetores_v1", "530.2",
     "https://archive.org/details/rhetoresgraeciem01walzuoft/page/n551/mode/1up"),
    ("qwen36-walz_rhetores_v5", "594.1",
     "https://archive.org/details/rhetoresgraeciem05walzuoft/page/n601/mode/1up"),
    ("qwen36-walz_rhetores_v9", "610.1",
     "https://archive.org/details/rhetoresgraeciem09walzuoft/page/n647/mode/1up"),
])
def test_verified_walz_printed_pages_resolve_to_matching_archive_leaves(
        edition, locus, expected):
    indexes = review.provenance_indexes(review.Paths(review.REPO))

    assert review.scan_url({
        "urn": "carved.walz.work", "edition": edition, "locus": locus,
    }, indexes) == expected


def test_scan_url_does_not_guess_printed_page_alignment(tmp_path):
    paths = fixture_paths(tmp_path)
    inventory = paths.data / "inventory"
    inventory.mkdir()
    (inventory / "reocr_provenance.json").write_text(json.dumps({
        "editions": [{
            "base": "sample_run",
            "source_url": "https://archive.org/download/source-book/source-book.pdf",
            "align_method": "content-offset",
            "content_offset": 0,
        }],
    }), encoding="utf-8")

    link = review.scan_url({
        "urn": "author.work", "edition": "qwen36-sample_run",
        "locus": "599.1",
    }, review.provenance_indexes(paths))

    assert link == "https://archive.org/details/source-book"


def test_exact_scan_url_rejects_work_level_archive_link():
    assert review.exact_scan_url(
        "https://archive.org/details/source-book/page/n34/mode/1up"
    )
    assert not review.exact_scan_url("https://archive.org/details/source-book")


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

    assert inputs == [
        paths.data / "nonfinal_graves.json",
        paths.provenance / f"{urn}.json",
    ]
    assert len(items) == 1
    item = items[0]
    assert item["observed"] == "ἐπεὶδὴ"
    assert item["target"] == {"start": 6, "end": 12}
    assert item["corpus_evidence"]["target"] == "ἐπειδή"
    assert "<TARGET>" in item["context"]
    assert item["scan_url"].endswith("/scan-book/page/n42/mode/1up")


def test_nonfinal_grave_queue_can_require_scan_evidence(tmp_path):
    paths = fixture_paths(tmp_path)
    write_jsonl(paths.corpus / "raw.work.jsonl", [{
        "urn": "raw.work", "edition": "missing", "source": "ocr",
        "locus": "scan_0042.1", "text": "λόγος ἐπεὶδὴ τέλος",
    }])
    (paths.data / "nonfinal_graves.json").write_text(json.dumps({
        "largest_forms": [{"form": "ἐπεὶδὴ", "tokens": 10}],
    }), encoding="utf-8")

    items, _ = review.build_issue_31(paths, limit=10, seed="test", require_scan=True)

    assert items == []


def test_duplicate_queue_joins_complete_page_text(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "author.work", "qwen-test"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0009.1", "text": "before a"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0010.1", "text": "alpha"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0010.2", "text": "beta"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0011.1", "text": "after a"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0019.1", "text": "before b"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0020.1", "text": "alpha beta"},
        {"urn": urn, "edition": edition, "source": "ocr", "locus": "scan_0021.1", "text": "after b"},
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
    assert items[0]["sequence"]["page_a"]["previous"]["locus"] == "scan_0009"
    assert items[0]["sequence"]["page_a"]["next"]["text"] == "after a"
    assert items[0]["sequence"]["page_b"]["previous"]["text"] == "before b"
    assert items[0]["sequence"]["page_b"]["next"]["locus"] == "scan_0021"


def test_duplicate_queue_can_require_both_scan_images(tmp_path):
    paths = fixture_paths(tmp_path)
    urn = "author.work"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [
        {"urn": urn, "edition": "missing", "source": "ocr",
         "locus": "scan_0010.1", "text": "alpha"},
        {"urn": urn, "edition": "missing", "source": "ocr",
         "locus": "scan_0020.1", "text": "alpha"},
    ])
    (paths.data / "duplicate_page_candidates.json").write_text(json.dumps({
        "pairs": [{"file": f"data/corpus/{urn}.jsonl", "served": True,
                   "locus_a": "scan_0010", "locus_b": "scan_0020",
                   "containment": 1.0, "same_item": True}],
    }), encoding="utf-8")

    items, _ = review.build_issue_33(paths, 10, "test", require_scan=True)

    assert items == []


def test_duplicate_queue_can_rank_reviewed_run_extensions(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "author.work", "qwen-test"
    loci = ("scan_0010", "scan_0020", "scan_0011", "scan_0021",
            "scan_0030", "scan_0040")
    write_jsonl(paths.corpus / f"{urn}.jsonl", [
        {"urn": urn, "edition": edition, "source": "ocr",
         "locus": f"{locus}.1", "text": locus}
        for locus in loci
    ])
    prior = {
        "file": f"data/corpus/{urn}.jsonl", "served": True,
        "locus_a": "scan_0010", "locus_b": "scan_0020",
        "containment": 0.9, "same_item": True,
    }
    extension = {
        "file": f"data/corpus/{urn}.jsonl", "served": True,
        "locus_a": "scan_0011", "locus_b": "scan_0021",
        "containment": 0.5, "same_item": True,
    }
    unrelated = {
        "file": f"data/corpus/{urn}.jsonl", "served": True,
        "locus_a": "scan_0030", "locus_b": "scan_0040",
        "containment": 1.0, "same_item": True,
    }
    artifact = paths.data / "duplicate_page_candidates.json"
    artifact.write_text(json.dumps({"pairs": [prior, unrelated, extension]}),
                        encoding="utf-8")
    changes = paths.data / "corpus_changes"
    changes.mkdir()
    prior_id = review.stable_id(
        33, prior["file"], prior["locus_a"], prior["locus_b"],
    )
    audit = changes / "issue-33-reviewed.page-images-test.applied.json"
    audit.write_text(json.dumps({"displacements": [{
        "item_id": prior_id, "file": prior["file"],
        "displaced_page": prior["locus_a"],
        "retained_page_direct": prior["locus_b"],
    }]}), encoding="utf-8")

    items, inputs = review.build_issue_33(
        paths, 10, "test", run_extensions=True,
    )

    assert [item["page_a"]["locus"] for item in items] == ["scan_0011"]
    neighbor = items[0]["signals"]["reviewed_run_neighbor"]
    assert neighbor == {
        "distance": 1, "decision": "drop_a", "item_id": prior_id,
        "locus_a": "scan_0010", "locus_b": "scan_0020",
    }
    assert audit in inputs


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
    write_jsonl(paths.corpus / "raw.work.jsonl", [
        {"urn": "raw.work", "edition": "qwen-test", "source": "ocr",
         "locus": "scan_0042.1", "text": "raw page text"},
        {"urn": "raw.work", "edition": "qwen-test", "source": "ocr",
         "locus": "scan_0042.2", "text": "apparatus"},
    ])
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
    assert items[0]["file"] == "data/corpus/raw.work.jsonl"
    assert [row["line"] for row in items[0]["rows"]] == [1, 2]
    assert [row["locus"] for row in items[0]["rows"]] == ["scan_0042.1", "scan_0042.2"]
    assert items[0]["text"] == "raw page text\napparatus"
    assert items[0]["segments_required_for"] == ["transcribe"]


def test_raw_ocr_queue_can_select_multiple_pages_per_work(tmp_path):
    paths = fixture_paths(tmp_path)
    write_jsonl(paths.corpus / "raw.work.jsonl", [
        {"urn": "raw.work", "edition": "qwen-test", "source": "ocr",
         "locus": "scan_0042.1", "text": "longer first page"},
        {"urn": "raw.work", "edition": "qwen-test", "source": "ocr",
         "locus": "scan_0043.1", "text": "second page"},
    ])
    add_scan(paths, "raw.work", "qwen-test")
    with (paths.data / "corpus_catalog.tsv").open(
        "w", encoding="utf-8", newline="",
    ) as handle:
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

    items, _ = review.build_issue_2(
        paths, 10, "test", require_scan=True, pages_per_work=2,
    )

    assert {item["page"] for item in items} == {"scan_0042", "scan_0043"}


def test_raw_ocr_queue_can_select_an_exact_work_page(tmp_path):
    paths = fixture_paths(tmp_path)
    urn, edition = "raw.work", "qwen-test"
    write_jsonl(paths.corpus / f"{urn}.jsonl", [
        {"urn": urn, "edition": edition, "source": "ocr",
         "locus": "scan_0041.1", "text": "first page"},
        {"urn": urn, "edition": edition, "source": "ocr",
         "locus": "scan_0042.1", "text": "requested page"},
    ])
    add_scan(paths, urn, edition)
    with (paths.data / "corpus_catalog.tsv").open("w", encoding="utf-8",
                                                        newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "slug", "work_id", "author", "title", "tokens", "source",
            "correction", "unattested_rate",
        ], delimiter="\t")
        writer.writeheader()
        writer.writerow({
            "slug": urn, "work_id": "ogc1", "author": "A", "title": "T",
            "tokens": 100, "source": "ocr", "correction": "raw-ocr",
            "unattested_rate": 0.2,
        })

    items, _ = review.build_issue_2(
        paths, 10, "test", require_scan=True,
        pages_only={(urn, "scan_0042")},
    )

    assert [item["page"] for item in items] == ["scan_0042"]


def test_raw_ocr_exact_page_selection_rejects_missing_page(tmp_path):
    paths = fixture_paths(tmp_path)
    (paths.data / "corpus_catalog.tsv").write_text(
        "slug\twork_id\tauthor\ttitle\ttokens\tsource\tcorrection\t"
        "unattested_rate\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="raw.work=scan_0042"):
        review.build_issue_2(
            paths, 10, "test", pages_only={("raw.work", "scan_0042")},
        )


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


def test_transcription_validator_requires_ordered_locus_segments(tmp_path):
    queue = tmp_path / "queue.jsonl"
    item = {
        "item_id": "ogc-2-test", "issue": 2, "kind": "raw-ocr-page",
        "allowed_decisions": ["transcribe"],
        "reading_required_for": ["transcribe"],
        "segments_required_for": ["transcribe"],
        "evidence_required_for": ["transcribe"],
        "rows": [
            {"locus": "scan_1.1", "text": "old one"},
            {"locus": "scan_1.2", "text": "old two"},
        ],
    }
    write_jsonl(queue, [item])
    decisions = tmp_path / "decisions.tsv"
    row = {
        "item_id": item["item_id"], "decision": "transcribe",
        "reading": "new one\nnew two",
        "segments": json.dumps([
            {"locus": "scan_1.2", "text": "new two"},
            {"locus": "scan_1.1", "text": "new one"},
        ]),
        "evidence_url": "https://example.test/scan",
        "reviewer": "Reviewer", "reviewed_at": "2026-09-14",
    }
    with decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=review.DECISION_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(SystemExit, match="every queued locus exactly once and in order"):
        review.validate_decisions(queue, decisions)

    row["segments"] = json.dumps([
        {"locus": "scan_1.1", "text": "new one"},
        {"locus": "scan_1.2", "text": "new two"},
    ])
    with decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=review.DECISION_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow(row)
    sealed = tmp_path / "sealed.jsonl"
    review.validate_decisions(queue, decisions, sealed)
    assert json.loads(sealed.read_text(encoding="utf-8"))["segments"] == [
        {"locus": "scan_1.1", "text": "new one"},
        {"locus": "scan_1.2", "text": "new two"},
    ]
