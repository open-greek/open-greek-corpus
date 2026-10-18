import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("math_retry_prepare", ROOT / "scripts/prepare_mathematical_ocr_retries.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_committed_request_pins_originals_and_source_review():
    request = json.loads((ROOT / prepare.OUTPUT).read_text())
    assert request["retry_of"]["sha256"] == prepare.MANIFEST_SHA256
    assert request["retry_of"]["original_predictions_sha256"] == prepare.ORIGINAL_SHA256
    assert request["retry_of"]["model"] == prepare.MODEL
    assert request["retry_of"]["revision"] == prepare.REVISION
    assert len(request["pages"]) == 15
    assert set(request["review"]["findings"]) == set(prepare.REGIONS)
    for identifier, regions in prepare.REGIONS.items():
        jobs = [p for p in request["pages"] if p["reconstructs"] == identifier]
        assert [p["reading_order"] for p in jobs] == [1, 2, 3]
        assert [p["region"] for p in jobs] == regions
        assert all(p["max_side"] == 3200 for p in jobs)
        finding = request["review"]["findings"][identifier]
        assert finding["original_text"]
        assert len(finding["original_image_sha256"]) == 64
        assert len(finding["original_prediction_sha256"]) == 64
        assert finding["source_pdf_sha256"] == request["sources"][jobs[0]["source"]]["sha256"]


def test_reprepare_rejects_changed_original_request(tmp_path):
    original = tmp_path / "manifest.json"
    predictions = tmp_path / "predictions.jsonl"
    original.write_text("{}")
    predictions.write_text("{}")
    with pytest.raises(ValueError, match="Original mathematical"):
        prepare.prepare(original, predictions, tmp_path, tmp_path / "retry.json")
    assert not (tmp_path / "retry.json").exists()


@pytest.fixture
def bundle_fixture(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import mathematical_ocr_retries as bundle
    request = json.loads((ROOT / prepare.OUTPUT).read_text())
    selected = {}
    for job in request["pages"]:
        identifier = job["reconstructs"]
        selected.setdefault(identifier, {**job, "id": identifier, "region": [0, 0, 1, 1]})
    for i in range(551):
        selected[f"fixture-{i}"] = {**next(iter(selected.values())), "id": f"fixture-{i}"}
    manifest = {"sources": request["sources"], "prompt": request["prompt"], "pages": list(selected.values())}
    manifest_raw = prepare.encode(manifest)
    manifest_sha = prepare.sha(manifest_raw)
    metadata = {"model": prepare.MODEL, "revision": prepare.REVISION,
                "prompt": request["prompt"], "manifest_sha256": manifest_sha}
    def record(job, text):
        return {"id": job["id"], "source": job["source"], "scan_page": job["scan_page"],
                "region": job["region"], "image_sha256": prepare.sha(job["id"].encode()),
                "prompt_sha256": prepare.sha(request["prompt"].encode()),
                "finish_reason": "stop", "raw_prediction": text}
    originals = [record(job, "επει γαρ") for job in selected.values()]
    original_raw = b"\n".join(json.dumps(row, ensure_ascii=False).encode() for row in [{"_meta": metadata}, *originals]) + b"\n"
    request["retry_of"]["sha256"] = manifest_sha
    request["retry_of"]["original_predictions_sha256"] = prepare.sha(original_raw)
    original_by_id = {row["id"]: row for row in originals}
    for identifier in prepare.REGIONS:
        row = original_by_id[identifier]
        request["review"]["findings"][identifier].update(
            original_prediction_sha256=prepare.sha(prepare.encode(row)),
            original_image_sha256=row["image_sha256"], original_text=row["raw_prediction"])
    authority = tmp_path / "authority.json"
    authority.write_bytes(prepare.encode(request))
    retry_metadata = {**metadata, "manifest_sha256": prepare.sha(authority.read_bytes())}
    retries = [record(job, "Ἐπεὶ γὰρ δέδεικται") for job in request["pages"]]
    retry_raw = b"\n".join(json.dumps(row, ensure_ascii=False).encode() for row in [{"_meta": retry_metadata}, *retries]) + b"\n"
    original = tmp_path / "original.jsonl"
    retry = tmp_path / "retry.jsonl"
    manifest_path = tmp_path / "manifest.json"
    review = tmp_path / "review.json"
    original.write_bytes(original_raw)
    retry.write_bytes(retry_raw)
    manifest_path.write_bytes(manifest_raw)
    monkeypatch.setattr(bundle, "AUTHORITY", authority)
    monkeypatch.setattr(bundle, "MANIFEST_SHA256", manifest_sha)
    monkeypatch.setattr(bundle, "ORIGINAL_SHA256", prepare.sha(original_raw))
    calls = []
    def leaf(raw, request_raw, request):
        meta, records = bundle.values(raw)
        assert meta["manifest_sha256"] == prepare.sha(request_raw)
        jobs = {p["id"]: p for p in request["pages"]}
        result = {}
        for row in records:
            job = jobs[row["id"]]
            if row["finish_reason"] != "stop" or row.get("error"):
                raise ValueError("Failed OCR strip")
            if row["region"] != job["region"] or row["scan_page"] != job["scan_page"]:
                raise ValueError("Unchecked source geometry")
            result[row["id"]] = {"id": meta["model"] + "@" + meta["revision"],
                "model": meta["model"], "revision": meta["revision"], "vote_group": "qwen3.6-27b",
                "text": row["raw_prediction"], "image_sha256": row["image_sha256"],
                "artifact_sha256": prepare.sha(prepare.encode(row))}
        calls.append(len(result))
        return result, raw
    evidence = {identifier: "Completed comparison of all three source strips, printed marks and final body line." for identifier in prepare.REGIONS}
    bundle.write_review(original, retry, evidence, review, "2026-10-18T00:00:00Z")
    return bundle, original, retry, review, manifest_path, leaf, calls


def test_bundle_preserves_full_attempt_and_one_model_vote(bundle_fixture, tmp_path):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    out = tmp_path / "bundle.json"
    descriptor = bundle.write_bundle(original, retry, review, manifest, out, leaf)
    result, raw = bundle.load_bundle(out.read_bytes(), manifest.read_bytes(), json.loads(manifest.read_text()), leaf)
    assert len(result) == 556
    assert set(descriptor["replaced_page_ids"]) == set(prepare.REGIONS)
    archived = json.loads(raw)
    assert bundle._decode(archived["original"]) == original.read_bytes()
    assert bundle._decode(archived["retry"]) == retry.read_bytes()
    assert calls == [556, 15, 556, 15]
    assert result["fixture-0"]["text"] == "επει γαρ"
    for identifier in prepare.REGIONS:
        witness = result[identifier]
        assert witness["vote_group"] == "qwen3.6-27b"
        assert witness["text"] == "\n".join(["Ἐπεὶ γὰρ δέδεικται"] * 3)
        assert witness["preprocessing"][0]["original_text"] == "επει γαρ"
        assert len(witness["retry_image_sha256s"]) == 3


def test_bundle_rejects_changed_retry_after_review(bundle_fixture, tmp_path):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    retry.write_bytes(retry.read_bytes().replace("δέδεικται".encode(), "γέγραπται".encode()))
    with pytest.raises(ValueError, match="completed review"):
        bundle.write_bundle(original, retry, review, manifest, tmp_path / "bundle.json", leaf)
    assert calls == []


def test_bundle_rejects_fresh_review_without_page_evidence(bundle_fixture, tmp_path):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    value = json.loads(review.read_text())
    value["pages"][next(iter(prepare.REGIONS))]["source_evidence"] = ""
    review.write_bytes(prepare.encode(value))
    with pytest.raises(ValueError, match="source evidence"):
        bundle.write_bundle(original, retry, review, manifest, tmp_path / "bundle.json", leaf)


def test_bundle_rejects_failed_strip_even_with_exact_review(bundle_fixture, tmp_path):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    rows = [json.loads(line) for line in retry.read_bytes().splitlines()]
    rows[1]["finish_reason"] = "length"
    retry.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in rows) + b"\n")
    review.unlink()
    with pytest.raises(ValueError, match="Failed, empty or truncated OCR strip"):
        bundle.write_review(original, retry, {i: "Reviewed pixels." for i in prepare.REGIONS}, review, "2026-10-18T00:00:00Z")
    assert not review.exists()


def test_bundle_rejects_relabeling_another_checkpoint(bundle_fixture, tmp_path):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    rows = [json.loads(line) for line in retry.read_bytes().splitlines()]
    rows[0]["_meta"]["revision"] = "different-checkpoint"
    retry.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in rows) + b"\n")
    review.unlink()
    with pytest.raises(ValueError, match="checkpoint"):
        bundle.write_review(original, retry, {i: "Reviewed pixels." for i in prepare.REGIONS}, review, "2026-10-18T00:00:00Z")


def test_review_rejects_changed_crop_before_writing(bundle_fixture):
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    rows = [json.loads(line) for line in retry.read_bytes().splitlines()]
    rows[1]["region"][1] += .01
    retry.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in rows) + b"\n")
    review.unlink()
    with pytest.raises(ValueError, match="Unchecked source geometry"):
        bundle.write_review(original, retry, {i: "Reviewed pixels." for i in prepare.REGIONS}, review, "2026-10-18T00:00:00Z")
    assert not review.exists()


def test_exact_shard_prefix_survives_append_and_partial_line(tmp_path):
    import audit_mathematical_ocr as audit
    path = tmp_path / "shard.jsonl"
    prefix = b'{"_meta": {}}\n{"id": "first"}\n'
    path.write_bytes(prefix)
    before = audit.read_prefix(path, 1)
    path.write_bytes(prefix + b'{"id": "second"}\n{"id": "incomplete')
    assert audit.read_prefix(path, 1) == before == prefix
    assert audit.read_prefix(path) == prefix + b'{"id": "second"}\n'
    with pytest.raises(ValueError, match="not complete"):
        audit.read_prefix(path, 3)


def test_apparatus_screen_does_not_flag_uppercase_geometry(tmp_path, monkeypatch):
    import audit_mathematical_ocr as audit
    request = json.loads((ROOT / prepare.OUTPUT).read_text())
    jobs = [{**p, "id": p["reconstructs"], "region": [0,0,1,1]} for p in request["pages"][:2]]
    jobs[1]["id"] = "other"
    manifest = {"prompt": request["prompt"], "sources": request["sources"], "pages": jobs}
    records = [{"_meta": {"manifest_sha256": prepare.MANIFEST_SHA256, "prompt": request["prompt"]}}]
    for job, text in zip(jobs, ["επει γαρ " * 80 + " AZB EAB", "Ἐπεὶ γὰρ δέδεικται. add. corr. retinuit"]):
        records.append({"id": job["id"], "source": job["source"], "scan_page": job["scan_page"],
                        "region": job["region"], "raw_prediction": text, "finish_reason": "stop"})
    path = tmp_path / "fixture.jsonl"
    raw = b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in records) + b"\n"
    path.write_bytes(raw)
    result = audit.audit_predictions(path, manifest)
    assert path.read_bytes() == raw
    assert result["flagged"] == 1
    assert not result["pages"][0]["exploratory_apparatus_screen"]["candidate"]
    assert result["pages"][1]["exploratory_apparatus_screen"]["candidate"]
    assert result["pages"][0]["prediction_sha256"] == prepare.sha(records[1]["raw_prediction"].encode())


def test_bundle_roundtrips_through_corpus_admission_loader(bundle_fixture, tmp_path):
    admission = pytest.importorskip("ingest_scan_coverage")
    bundle, original, retry, review, manifest, leaf, calls = bundle_fixture
    manifest_raw = manifest.read_bytes()
    document = json.loads(manifest_raw)
    def strict_leaf(raw, request_raw, request):
        return admission.load_predictions(None, request_raw, request, raw)
    out = tmp_path / "reviewed.bundle.json"
    bundle.write_bundle(original, retry, review, manifest, out, strict_leaf)
    predictions, retained = admission.load_predictions(out, manifest_raw, document)
    assert retained == out.read_bytes()
    assert len(predictions) == 556
    assert all(w["vote_group"] == "qwen3.6-27b" for w in predictions.values())
    assert sum("preprocessing" in w for w in predictions.values()) == 5


def test_qwen38_request_preserves_original_checkpoint_and_body_blocks(tmp_path):
    import prepare_mathematical_qwen38_retry as retry
    request = json.loads((ROOT / retry.OUTPUT).read_text())
    assert request["retry_of"]["source_part_sha256"] == retry.SOURCE_PART_SHA256
    assert request["retry_of"]["model"] == retry.MODEL
    assert request["retry_of"]["revision"] == retry.REVISION
    assert request["retry_of"]["sha256"] == prepare.MANIFEST_SHA256
    assert [p["region"] for p in request["pages"]] == retry.REGIONS
    assert {p["reconstructs"] for p in request["pages"]} == {retry.PAGE_ID}
    assert request["review"]["original_text"]
    assert request["review"]["source_pdf_sha256"] == request["sources"]["pappialexandrin01pappgoog"]["sha256"]
    fake = tmp_path / "bad.json"
    fake.write_text("{}")
    with pytest.raises(ValueError, match="completed Qwen3.8 shard03"):
        retry.prepare(fake, fake, tmp_path, tmp_path / "out.json")
