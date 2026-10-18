"""Retries require source review and replace a model input without another vote."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import jahn_retries as retries
import repair_meibom_work_assignments as repair
from test_meibom_repair import fixture


def retry_fixture(root, inputs, authority_name="jahn-aristides-page81-retry.json"):
    authority = ROOT / "data/ingest_reviews" / authority_name
    raw = authority.read_bytes()
    manifest = json.loads(raw)
    paths, runs = [], []
    for original in inputs["witnesses"]["8"]:
        meta = {k: original[k] for k in ("model", "revision", "prompt", "backend")}
        meta["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        rows = [{"_meta": meta}] + [{"id": p["id"], "region": p["region"],
            "scan_page": p["scan_page"], "image_sha256": "image-" + p["id"],
            "raw_prediction": text, "finish_reason": "stop"}
            for p, text in zip(manifest["pages"], ["οἱ μὲν", "εἰσι λόγοι", "καὶ σαφεῖς"] * 4)]
        path = root / (original["model"] + "-" + authority.stem + ".jsonl")
        path.write_bytes(repair.jsonl(rows))
        paths.append(path)
        runs.append({"model": original["model"], "revision": original["revision"],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    review = {"manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "source_pdf_sha256": manifest["sources"]["jahn1882"]["sha256"],
        "reviewed_at": "2026-10-18", "decision": "replace-source-reviewed-degraded-page",
        "source_evidence": "Fixture: complete retry strips checked against the printed polytonic source.",
        "original_artifacts_sha256": [w["artifact_sha256"] for page in sorted({str(p["printed_page"]) for p in manifest["pages"]}, key=int)
            for w in inputs["witnesses"][page]],
        "reviewed_runs": runs}
    review_path = root / (authority.stem + "-review.json")
    review_path.write_bytes(repair.dump(review))
    return paths, review_path, authority


def test_retry_admission_preserves_originals_replays_and_has_only_two_votes(tmp_path, monkeypatch):
    _, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    inputs = repair.prepare_inputs(tmp_path, fresh)
    originals = copy.deepcopy(inputs["witnesses"]["8"])
    paths, review, authority = retry_fixture(tmp_path, inputs)
    repair.run_repair(tmp_path, "apply", fresh, retry_paths=paths, retry_review=review)
    repair.run_repair(tmp_path, "check")
    archive = json.loads(gzip.decompress((tmp_path / repair.AUDIT_DIR / "witnesses.json.gz").read_bytes()))
    assert archive["held_primary_witnesses"]["8"] == originals
    assert len(archive["retry_evidence"]["raw_files"]) == 2
    assert len(archive["witnesses"]["8"]) == 2
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert primary[7]["analysis_text"] == "οἱ μὲν εἰσι λόγοι καὶ σαφεῖς"
    assert len(primary[7]["ocr_consensus"]["witnesses"]) == 2
    assert {w["vote_group"] for w in primary[7]["ocr_consensus"]["witnesses"]} == {"qwen3.6-27b", "qwen3.8-27b"}
    assert all(w["preprocessing"][0]["raw_strips"] for w in primary[7]["ocr_consensus"]["witnesses"])


@pytest.mark.parametrize("defect,message", [
    ("review", "source-reviewed decision"), ("original", "every original"),
    ("changed", "exact prediction"), ("missing", "every reviewed strip"),
    ("truncated", "complete successfully"), ("crop", "unchecked source crop")])
def test_retry_admission_rejects_unreviewed_or_incomplete_inputs(tmp_path, monkeypatch, defect, message):
    _, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    inputs = repair.prepare_inputs(tmp_path, fresh)
    paths, review_path, authority = retry_fixture(tmp_path, inputs)
    review = json.loads(review_path.read_text())
    if defect == "review":
        review["decision"] = "automatically prefer more accents"
    elif defect == "original":
        review["original_artifacts_sha256"].pop()
    else:
        rows = [json.loads(line) for line in paths[0].read_text().splitlines()]
        if defect in {"changed", "missing"}:
            rows.pop()
        elif defect == "truncated":
            rows[-1]["finish_reason"] = "length"
        elif defect == "crop":
            rows[-1]["region"] = [0, 0, 1, 1]
        paths[0].write_bytes(repair.jsonl(rows))
        if defect != "changed":
            review["reviewed_runs"][0]["sha256"] = hashlib.sha256(paths[0].read_bytes()).hexdigest()
    review_path.write_bytes(repair.dump(review))
    with pytest.raises(ValueError, match=message):
        retries.apply_reviewed_retries(inputs, paths, review_path, authority)
    assert not (tmp_path / repair.AUDIT_DIR).exists()


def test_aliases_of_one_model_family_do_not_supply_two_independent_witnesses(tmp_path, monkeypatch):
    _, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    rows = [json.loads(line) for line in fresh[1].read_text().splitlines()]
    rows[0]["_meta"]["model"] = "mlx-community/Qwen3.6-27B-8bit"
    fresh[1].write_bytes(repair.jsonl(rows))
    with pytest.raises(ValueError, match="Two fresh model witnesses"):
        repair.prepare_inputs(tmp_path, fresh)


def test_review_writer_requires_complete_evidence_before_creating_record(tmp_path, monkeypatch):
    _, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    inputs = repair.prepare_inputs(tmp_path, fresh)
    paths, prior_review, authority = retry_fixture(tmp_path, inputs)
    output = tmp_path / "recorded-review.json"
    before = copy.deepcopy(inputs)
    result = retries.write_source_review(inputs, paths, authority, output,
        "Fixture: every strip compared with source; accents and breathings are retained.", "2026-10-18")
    assert inputs == before
    assert json.loads(output.read_text()) == result
    with pytest.raises(ValueError, match="replace an existing"):
        retries.write_source_review(inputs, paths, authority, output, "Review", "2026-10-18")
    rows = [json.loads(line) for line in paths[0].read_text().splitlines()]
    paths[0].write_bytes(repair.jsonl(rows[:-1]))
    failed = tmp_path / "incomplete-review.json"
    with pytest.raises(ValueError, match="every reviewed strip"):
        retries.write_source_review(inputs, paths, authority, failed, "Review", "2026-10-18")
    assert not failed.exists()


def test_multiple_reviewed_requests_replace_length_failures_and_keep_notation_references(tmp_path, monkeypatch):
    _, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    rows = [json.loads(line) for line in fresh[1].read_text().splitlines()]
    for row in rows:
        if row.get("scan_page") in {90, 112}:
            row["finish_reason"] = "length"
    fresh[1].write_bytes(repair.jsonl(rows))
    inputs = repair.prepare_inputs(tmp_path, fresh, allow_pending_retries=True)
    first, review1, _ = retry_fixture(tmp_path, inputs)
    second, review2, _ = retry_fixture(tmp_path, inputs, "jahn-aristides-length-retry.json")
    third, review3, _ = retry_fixture(tmp_path, inputs, "jahn-aristides-notation-retry.json")
    with pytest.raises(ValueError, match="without reviewed replacements"):
        repair.prepare_inputs(tmp_path, fresh, retry_paths=first, retry_review=review1)
    assert not (tmp_path / repair.AUDIT_DIR).exists()
    repair.run_repair(tmp_path, "apply", fresh, retry_paths=first + second + third, retry_review=[review1, review2, review3])
    repair.run_repair(tmp_path, "check")
    archive = json.loads(gzip.decompress((tmp_path / repair.AUDIT_DIR / "witnesses.json.gz").read_bytes()))
    assert set(archive["held_primary_witnesses"]) == {"8", "9", "14", "17", "18", "39"}
    assert len(archive["retry_evidence"]["requests"]) == len(archive["retry_evidence"]["source_reviews"]) == 3
    assert len(archive["retry_evidence"]["raw_files"]) == 6
    assert any(w["finish_reason"] == "length" for w in archive["held_primary_witnesses"]["17"])
    assert all(w["attempt_status"] == "successful" for ws in archive["witnesses"].values() for w in ws)
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert len(primary) == 97
    assert len(primary[16]["nonlexical_source_regions"]) == 2
    assert all(not r["lexical_eligible"] and r["source"]["scan_page"] == 90 for r in primary[16]["nonlexical_source_regions"])
    assert len(primary[16]["ocr_consensus"]["witnesses"]) == 2
    assert len(primary[13]["nonlexical_source_regions"]) == 6
