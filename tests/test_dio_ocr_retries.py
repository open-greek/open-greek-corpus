"""Exact artifact scopes preserve failed originals without weakening defaults."""
from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dio_ocr_retries as retry
import scan_ocr_bundle as generic


def jsonl(rows):
    return b"\n".join(json.dumps(row, ensure_ascii=False).encode() for row in rows) + b"\n"


def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


@pytest.fixture(params=["qwen36", "qwen38"])
def fixture(request, tmp_path, monkeypatch):
    key = request.param
    model, revision, family = retry.CHECKPOINTS[key]
    locations = {"dio-cary-v6-pdf0206": (6,206), "dio-cary-v8-pdf0116": (8,116),
                 "dio-cary-v9-pdf0178": (9,178), "dio-cary-v9-pdf0179": (9,179),
                 "dio-cary-v9-pdf0231": (9,231)}
    targets = set(locations) - {"dio-cary-v9-pdf0231"} if key == "qwen38" else {"dio-cary-v9-pdf0231"}
    failed_ids = targets & {"dio-cary-v9-pdf0178", "dio-cary-v9-pdf0179", "dio-cary-v9-pdf0231"}
    pages = [{"id": identifier, "source": "scan" + str(volume), "source_volume": volume,
              "scan_page": scan, "region": [0,0,.5,.9], "work": "cassius-dio.historiae-romanae"}
             for identifier, (volume,scan) in locations.items()]
    pages += [{**pages[0], "id": f"other-{i}"} for i in range(1495)]
    sources = {"scan" + str(v): {"url": f"https://example.org/{v}.pdf", "sha256": str(v) * 64, "license": "PD"}
               for v in [6,8,9]}
    manifest = {"prompt": "Transcribe Greek body only.", "sources": sources, "pages": pages}
    manifest_raw = retry.encode(manifest)
    manifest_path = put(tmp_path / "manifest.json", manifest_raw)
    metadata = {"model": model, "revision": revision, "prompt": manifest["prompt"],
                "manifest_sha256": retry.sha(manifest_raw), "runner_sha256": "a" * 64, "runtime": {"gpu": "fixture"}}
    original_rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"], "region": p["region"],
                      "finish_reason": "length" if p["id"] in failed_ids else "stop", "raw_prediction": "επει γαρ ..." if p["id"] in targets else "Ἐπεὶ γὰρ δέδεικται",
                      "image_sha256": retry.sha(p["id"].encode()), "prompt_sha256": retry.sha(manifest["prompt"].encode())}
                     for p in pages]
    original_by_id = {r["id"]: r for r in original_rows}
    part = put(tmp_path / "part.jsonl", jsonl([{"_meta": metadata}, *original_rows]))
    original = tmp_path / "original.bundle.json"
    generic.write_bundle([(part,manifest_path)], manifest_path, original)
    jobs = []
    for identifier in sorted(targets):
        page = next(p for p in pages if p["id"] == identifier)
        for index in range(3):
            jobs.append({**page, "id": identifier + "-strip-" + str(index+1), "reconstructs": identifier,
                         "reading_order": index+1, "region": [0,index*.3,.5,(index+1)*.3]})
    authority = {"prompt": manifest["prompt"], "sources": sources, "pages": jobs,
                 "retry_of": {"path": retry.MANIFEST_PATH, "sha256": retry.sha(manifest_raw), "model": model, "revision": revision},
                 "review": {"original_predictions": {identifier: {"artifact_sha256": retry.sha(retry.encode({"metadata": metadata, "prediction": original_by_id[identifier]})),
                     "original_metadata": metadata, "original_prediction": original_by_id[identifier],
                     "source_evidence": "Complete source page and all strip boundaries inspected; original loss or loop confirmed."}
                     for identifier in sorted(targets)}}}
    authority_path = put(tmp_path / "authority.json", retry.encode(authority))
    monkeypatch.setattr(retry, "AUTHORITIES", {key: authority_path})
    retry_meta = {**metadata, "manifest_sha256": retry.sha(authority_path.read_bytes()),
                  "generation_policy": json.loads(json.dumps(retry.GENERATION_POLICY)),
                  "temperature": retry.GENERATION_POLICY["temperature"], "max_tokens": 6000, "backend": "http",
                  "runner": "scripts/run_reviewed_scan_retry.py", "runner_sha256": retry.RETRY_RUNNER_SHA256,
                  "image_helper_sha256": retry.IMAGE_HELPER_SHA256,
                  "runtime": {**metadata["runtime"], "model": model, "revision": revision}}
    retry_rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"], "region": p["region"],
                   "finish_reason": "stop", "raw_prediction": "Ἐπεὶ γὰρ δέδεικται", "image_sha256": retry.sha(p["id"].encode()),
                   "prompt_sha256": retry.sha(manifest["prompt"].encode())} for p in jobs]
    raw_retry = put(tmp_path / "retry.jsonl", jsonl([{"_meta": retry_meta}, *retry_rows]))
    calls = []
    def leaf(raw, request_raw, request_manifest, *, allow_failed_ids=frozenset()):
        calls.append(set(allow_failed_ids))
        try:
            document = json.loads(raw)
        except ValueError:
            document = None
        if isinstance(document, dict) and document.get("kind") == generic.KIND:
            return generic.load_bundle(raw, request_raw,
                lambda original_raw, original_manifest_raw: leaf(original_raw, original_manifest_raw,
                    json.loads(original_manifest_raw), allow_failed_ids=allow_failed_ids)[0])[0], raw
        meta, rows = retry.records(raw)
        if meta["manifest_sha256"] != retry.sha(request_raw):
            raise ValueError("Wrong request")
        jobs_by_id = {p["id"]: p for p in request_manifest["pages"]}
        result = {}
        for row in rows:
            job = jobs_by_id[row["id"]]
            if retry.failed(row) and row["id"] not in allow_failed_ids:
                raise ValueError("Ordinary strict loader rejects failed OCR")
            if row["region"] != job["region"] or row["source"] != job["source"] or row["scan_page"] != job["scan_page"]:
                raise ValueError("Unchecked source crop")
            result[row["id"]] = {"id": meta["model"] + "@" + meta["revision"], "model": meta["model"],
                "revision": meta["revision"], "vote_group": family, "text": row["raw_prediction"],
                "artifact_sha256": retry.sha(retry.encode({"metadata": meta, "prediction": row})),
                "image_sha256": row["image_sha256"]}
        return result, raw
    evidence = {identifier: "All complete retry strips compared with the pinned scan; body coverage, marks, finite gaps and apparatus boundaries checked. Literal local errors remain variants." for identifier in targets}
    return {"key": key, "model": model, "revision": revision, "family": family,
            "original": original, "part": part, "retry": raw_retry, "request": authority_path,
            "manifest": manifest_path, "targets": targets, "failed_ids": failed_ids,
            "evidence": evidence, "leaf": leaf, "calls": calls, "tmp": tmp_path}


def build(f):
    review, out = f["tmp"] / "review.json", f["tmp"] / "reviewed.bundle.json"
    descriptor = retry.write_reviewed_bundle(f["original"], f["retry"], f["manifest"], review, out,
        f["evidence"], "2026-10-18T00:00:00Z", f["leaf"], request_path=f["request"])
    return review, out, descriptor


def test_checkpoint_scopes_retain_original_bytes_and_one_vote(fixture):
    f = fixture
    review, out, descriptor = build(f)
    manifest_raw = f["manifest"].read_bytes()
    result, retained = retry.load_bundle(out.read_bytes(), manifest_raw, json.loads(manifest_raw), f["leaf"])
    assert len(result) == 1500
    assert sum("preprocessing" in w for w in result.values()) == len(f["targets"])
    assert all(w["model"] == f["model"] and w["revision"] == f["revision"] and w["vote_group"] == f["family"] for w in result.values())
    assert set(descriptor["replaced_page_ids"]) == f["targets"]
    assert set(descriptor["held_length_failure_ids"]) == f["failed_ids"]
    assert retry.unpack(json.loads(retained)["original"]) == f["original"].read_bytes()
    assert retry.unpack(json.loads(retained)["retry"]) == f["retry"].read_bytes()
    assert all(not allowed or allowed == f["failed_ids"] for allowed in f["calls"])
    for identifier in f["targets"]:
        assert result[identifier]["text"] == "\n".join(["Ἐπεὶ γὰρ δέδεικται"] * 3)
        assert result[identifier]["preprocessing"][0]["original_text"] == "επει γαρ ..."


def test_ordinary_loading_remains_strict(fixture):
    f = fixture
    raw = f["manifest"].read_bytes()
    with pytest.raises(ValueError, match="strict loader rejects"):
        f["leaf"](f["original"].read_bytes(), raw, json.loads(raw))


def test_additional_failed_page_cannot_receive_an_exception(fixture):
    f = fixture
    values = [json.loads(line) for line in f["part"].read_bytes().splitlines()]
    values[-1]["finish_reason"] = "length"
    f["part"].write_bytes(jsonl(values))
    f["original"].unlink()
    generic.write_bundle([(f["part"],f["manifest"])], f["manifest"], f["original"])
    with pytest.raises(ValueError, match="unreviewed failed Dio"):
        build(f)
    assert f["calls"] == []
    assert not (f["tmp"] / "review.json").exists()


def test_failed_original_text_is_never_rewritten_to_pass(fixture):
    f = fixture
    values = [json.loads(line) for line in f["part"].read_bytes().splitlines()]
    row = next(r for r in values[1:] if r["id"] in f["failed_ids"])
    row["raw_prediction"] += "changed"
    f["part"].write_bytes(jsonl(values))
    f["original"].unlink()
    generic.write_bundle([(f["part"],f["manifest"])], f["manifest"], f["original"])
    with pytest.raises(ValueError, match="exact source-reviewed artifact"):
        build(f)
    assert not (f["tmp"] / "reviewed.bundle.json").exists()


def test_any_failed_retry_strip_rejects_before_private_exception(fixture):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[1]["finish_reason"] = "length"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="successful complete reviewed strip"):
        build(f)
    assert f["calls"] == []


def test_changed_retry_checkpoint_rejects_without_substitution(fixture):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"]["revision"] = "different-revision"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="checkpoint"):
        build(f)


def test_missing_completed_page_evidence_cannot_be_approved(fixture):
    f = fixture
    f["evidence"][next(iter(f["targets"]))] = ""
    with pytest.raises(ValueError, match="completed source comparison"):
        build(f)


def test_archive_checksum_guards_original_and_review(fixture):
    f = fixture
    _, out, _ = build(f)
    bundle = json.loads(out.read_bytes())
    bundle["source_review"]["sha256"] = "0" * 64
    raw = f["manifest"].read_bytes()
    with pytest.raises(ValueError, match="artifact bytes changed"):
        retry.load_bundle(retry.encode(bundle), raw, json.loads(raw), f["leaf"])


def test_real_corpus_dispatch_preserves_scoped_failures(fixture):
    admission = pytest.importorskip("ingest_scan_coverage")
    f = fixture
    def actual(raw, request_raw, manifest, *, allow_failed_ids=frozenset()):
        return admission.load_predictions(None, request_raw, manifest, raw, allow_failed_ids=allow_failed_ids)
    f["leaf"] = actual
    _, out, _ = build(f)
    raw = f["manifest"].read_bytes()
    result, retained = admission.load_predictions(out, raw, json.loads(raw))
    assert len(result) == 1500
    assert sum("preprocessing" in w for w in result.values()) == len(f["targets"])


@pytest.mark.parametrize("field", ["presence_penalty", "seed", "top_k", "chat_template_kwargs"])
def test_unapproved_decoder_policy_cannot_replace_reviewed_source(fixture, field):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"]["generation_policy"][field] = "unapproved"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="decoding policy"):
        build(f)
    assert f["calls"] == []


@pytest.mark.parametrize("field", ["runner_sha256", "image_helper_sha256", "max_tokens"])
def test_original_runner_and_image_helper_authorities_are_pinned(fixture, field):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"][field] = "changed"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="decoding policy"):
        build(f)


def test_frozen_policy_matches_separate_approved_runner():
    runner = pytest.importorskip("run_reviewed_scan_retry")
    assert retry.GENERATION_POLICY == runner.POLICY
    assert retry.sha(Path(runner.__file__).read_bytes()) == retry.RETRY_RUNNER_SHA256
    assert retry.sha(Path(runner.original.__file__).read_bytes()) == retry.IMAGE_HELPER_SHA256
