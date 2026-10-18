"""Source-confirmed unrelated readings remain raw evidence without a vote."""
import copy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_photius_coverage as ingest
import photius_retries as retries
from prepare_photius_retries import build_retry, CHECKPOINT38
from test_photius_geometry_loader import geometry_child_fixture, encoded_rows


def abstention_fixture(tmp_path, monkeypatch, mutate=None):
    paths, bases, reviews, supplements, child = geometry_child_fixture(tmp_path, monkeypatch)
    raw_file = supplements[-1]
    values = [json.loads(line) for line in raw_file.read_bytes().splitlines()]
    for row in [values[1], values[3]]:
        row["raw_prediction"] = "  ἀνεκδιήγητος ξενόλεκτος.  "
    raw_file.write_bytes(encoded_rows(values[0]["_meta"], values[1:]))
    raw = raw_file.read_bytes()
    metadata = values[0]["_meta"]
    jobs = {p["id"]: p for p in child["pages"]}
    entries = {}
    for line in [raw.splitlines()[1], raw.splitlines()[3]]:
        row = json.loads(line)
        entry = {"model": metadata["model"], "revision": metadata["revision"],
            "manifest_sha256": metadata["manifest_sha256"], "id": row["id"],
            "raw_file_sha256": retries.sha(raw), "prediction_record_sha256": retries.sha(line),
            "raw_prediction_sha256": retries.sha(row["raw_prediction"].encode()),
            "source": row["source"], "scan_page": row["scan_page"], "region": row["region"],
            "source_pdf_sha256": child["sources"][row["source"]]["sha256"],
            "image_sha256": row["image_sha256"], "finish_reason": "stop", "reviewed_at": "2026-10-18",
            "original_text": row["raw_prediction"], "voting_text": "",
            "reason": "Synthetic scan review confirms this entire retained reading is unrelated to the printed source."}
        key = (metadata["model"], metadata["revision"], metadata["manifest_sha256"], row["id"])
        entries[key] = entry
    if mutate:
        mutate(next(iter(entries.values())))
    authority_path = "data/ocr_requests/photius-source-abstentions.json"
    authority_raw = retries.encode({"source_review": list(entries.values())})
    monkeypatch.setattr(retries, "known_abstentions", lambda: entries)
    monkeypatch.setattr(retries, "abstention_authority", lambda: (authority_path, authority_raw))
    review_path = next(p for p in reviews if p.name == "review-50.json")
    review_path.unlink()
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              allow_unreviewed_retry_preparation=True)
    base = build_retry(50)
    catalog = retries.known_supplement_manifests()
    retries.write_source_review(models, [p for p in bases if p.name == "retry-50-0.jsonl"], review_path,
        "Synthetic completed source comparison with explicit unrelated-reading abstentions",
        {p["id"]: "Complete source lines" for p in base["pages"]}, "2026-10-18T15:00:00Z", base, supplements,
        {p["id"]: "Source compared; exact unrelated readings abstain" for _, r in catalog.values() for p in r["pages"]})
    return paths, bases, reviews, supplements, entries


def test_abstention_keeps_exact_ordered_text_and_only_masks_reviewed_parts(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, entries = abstention_fixture(tmp_path, monkeypatch)
    _, models, evidence = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              bases, reviews, supplement_paths=supplements)
    assembly = models[(CHECKPOINT38["model"], CHECKPOINT38["revision"])]["photius-bekker-0050"][2]["reviewed_retry"]
    text = "\n\n".join(p["raw_prediction"].strip() for p in assembly["strips"])
    assert assembly["accepted_text"] == text and "ξενόλεκτος" in text
    audit = assembly["abstention_audit"]
    assert audit["reviewed_text_sha256"] == retries.sha(text.encode())
    assert len(audit["excluded_spans"]) == 2
    pieces = sorted([*audit["excluded_spans"], *assembly["voting_segments"]], key=lambda p: p["start"])
    assert "".join(p["text"] for p in pieces) == text
    assert pieces[0]["start"] == 0 and pieces[-1]["end"] == len(text)
    assert all(a["end"] == b["start"] for a, b in zip(pieces, pieces[1:]))
    assert all(p["text"] == text[p["start"]:p["end"]] for p in pieces)
    assert "ξενόλεκτος" not in "".join(p["text"] for p in assembly["voting_segments"])
    review = json.loads(next(p for p in reviews if p.name == "review-50.json").read_bytes())
    decisions = [r for d in review["reviewed_supplements"] for r in d["strip_reviews"]
                 if r["id"] in assembly["abstained_part_ids"]]
    assert len(decisions) == 2
    assert all(p["reading_complete"] is False and p["reading_basis"] == "source-confirmed-abstention" for p in decisions)
    report = ingest.outcome_quality([*paths, *bases, *supplements], models)
    assert sum(r["admission_disposition"] == "source-confirmed-abstention" for r in report["outcomes"]) == 2
    retained = next(e for e in evidence if "abstention_authority" in e)
    assert retries.sha(retained["abstention_authority"]["raw"]) == audit["source_review"]["sha256"]
    assert audit["source_review"]["path"].startswith("data/corpus_changes/photius-bekker-coverage/retry/")
    assert len(models) == 2 and all(len(pages) == 310 for pages in models.values())


@pytest.mark.parametrize("field,value", [
    ("raw_file_sha256", "0" * 64), ("prediction_record_sha256", "0" * 64),
    ("raw_prediction_sha256", "0" * 64), ("image_sha256", "0" * 64),
    ("source_pdf_sha256", "0" * 64), ("region", [0, 0, 1, 1]),
    ("source", "wrong-source"), ("scan_page", 51), ("finish_reason", "length"),
    ("original_text", "unreviewed"), ("voting_text", "invented replacement"), ("reason", ""),
])
def test_abstention_requires_every_exact_source_and_outcome_pin(tmp_path, monkeypatch, field, value):
    message = "completed source review" if field == "reason" else "exact current leaf or authority"
    with pytest.raises(ValueError, match=message):
        abstention_fixture(tmp_path, monkeypatch, lambda entry: entry.__setitem__(field, value))


@pytest.mark.parametrize("change", ["complete", "basis", "authority", "unknown"])
def test_completed_review_cannot_hide_or_fabricate_an_abstention(tmp_path, monkeypatch, change):
    paths, bases, reviews, supplements, entries = abstention_fixture(tmp_path, monkeypatch)
    review_path = next(p for p in reviews if p.name == "review-50.json")
    review = json.loads(review_path.read_bytes())
    ids = {key[-1] for key in entries}
    part = next(r for d in review["reviewed_supplements"] for r in d["strip_reviews"] if r["id"] in ids)
    if change == "complete": part["reading_complete"] = True
    elif change == "basis": part["reading_basis"] = "complete"
    elif change == "authority": part["source_authority"]["sha256"] = "0" * 64
    else: monkeypatch.setattr(retries, "known_abstentions", lambda: {})
    review_path.write_bytes(retries.encode(review))
    with pytest.raises(ValueError):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                   bases, reviews, supplement_paths=supplements)


def test_abstained_endpoint_cannot_bound_a_digital_voting_witness():
    text = "ἀρχὴ σαφὴς ἡ τοῦ λόγου ἐστίν μέση καλὴ καὶ τελευτὴ τοῦ λόγου σαφής ἐστιν"
    fresh = [{"id": "a", "vote_group": "a", "text": text}, {"id": "b", "vote_group": "b", "text": text}]
    comparison = {"id": "comparison", "text": text, "artifact_sha256": "c" * 64}
    assert ingest.bound_reviewed_comparison(fresh, comparison)[0] is not None
    fresh[0]["abstention_audit"] = {"excluded_spans": [{"start": 0, "end": 5, "text": text[:5], "reason": "Source confirmed"}]}
    bounded, audit = ingest.bound_reviewed_comparison(fresh, comparison)
    assert bounded is None and audit["status"] == "held-comparison-only"
    assert "abstention" in audit["reason"]


def test_abstention_authority_archive_masks_consensus_replays_and_undoes(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, _ = abstention_fixture(tmp_path, monkeypatch)
    document = {"id": "test-source", "license": {"text": "CC BY-SA4.0"}, "sourceRights": "Retained rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda p: (b"source", document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=bases,
                                        retry_review=reviews, supplement_paths=supplements)
    networks = json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))
    consensus = networks["50"]
    assert "ξενόλεκτος" not in consensus["text"] + consensus["analysis_text"]
    witness = next(w for w in consensus["ocr_consensus"]["witnesses"] if "abstention_audit" in w)
    assert "ξενόλεκτος" in witness["text"]
    assert len(consensus["ocr_consensus"]["witnesses"]) == 2
    assert len({w["vote_group"] for w in consensus["ocr_consensus"]["witnesses"]}) == 2
    retry = next(r for r in report["reviewed_retries"] if "abstention_authority" in r)
    pin = retry["abstention_authority"]
    assert witness["abstention_audit"]["source_review"] == {"path": pin["path"], "sha256": pin["sha256"]}
    assert artifacts[Path(pin["path"])] == retries.abstention_authority()[1]
    assert report["covered_authorial_scan_pages"] == 545 and len(networks) == 310
    before = (tmp_path / ingest.CORPUS).read_bytes()
    ingest.apply(artifacts, report, tmp_path)
    _, models, _ = ingest.prepare_report_inputs(tmp_path, report, [ingest.scan_manifest(), ingest.build_later_gap()])
    assert models[(CHECKPOINT38["model"], CHECKPOINT38["revision"])]["photius-bekker-0050"][2]["reviewed_retry"]["abstention_audit"] == witness["abstention_audit"]
    altered = copy.deepcopy(report)
    next(r for r in altered["reviewed_retries"] if "abstention_authority" in r).pop("abstention_authority")
    with pytest.raises(ValueError, match="abstention report"):
        ingest.prepare_report_inputs(tmp_path, altered, [ingest.scan_manifest(), ingest.build_later_gap()])
    archived = tmp_path / pin["path"]
    archived.write_bytes(archived.read_bytes() + b" ")
    with pytest.raises(ValueError, match="report pin"):
        ingest.prepare_report_inputs(tmp_path, report, [ingest.scan_manifest(), ingest.build_later_gap()])
    archived.write_bytes(artifacts[Path(pin["path"])])
    ingest.undo(tmp_path)
    assert (tmp_path / ingest.CORPUS).read_bytes() == before
