import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import scan_ocr_bundle as bundle
import run_scan_ocr_shard as shard
from ingest_scan_coverage import load_predictions


def manifest():
    return {"prompt": "Read Greek exactly.", "sources": {"scan": {"sha256": "a" * 64, "url": "https://example.org/scan.pdf"}},
            "pages": [{"id": str(i), "source": "scan", "scan_page": i, "region": [0, 0, 1, 1],
                       "max_side": 2000, "work": "test"} for i in range(1, 5)]}


def part(tmp_path, ids, request=None, name="part", model="checkpoint", gpu="GPU A"):
    request = request or manifest()
    raw_manifest = bundle.encode(request)
    meta = {"model": model, "revision": "revision", "prompt": request["prompt"],
            "manifest_sha256": bundle.sha(raw_manifest), "runtime": {"gpu": gpu}, "runner_sha256": "b" * 64}
    rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"], "region": p["region"],
             "prompt_sha256": bundle.sha((request["prompt"] + (" " + p["prompt_suffix"] if p.get("prompt_suffix") else "")).encode()),
             "raw_prediction": "ὁ λόγος", "finish_reason": "stop",
             "image_sha256": "c" * 64} for p in request["pages"] if p["id"] in ids]
    # Real raw parts use one JSON object per line, with their exact original metadata.
    raw = ("\n".join(json.dumps(row, ensure_ascii=False) for row in [{"_meta": meta}, *rows]) + "\n").encode()
    path, mp = tmp_path / (name + ".jsonl"), tmp_path / (name + "-manifest.json")
    path.write_bytes(raw); mp.write_bytes(raw_manifest)
    return path, mp


def strict(raw, manifest_raw):
    return load_predictions(None, manifest_raw, json.loads(manifest_raw), raw)[0]


def test_disjoint_cross_host_parts_preserve_original_artifacts_and_nested_bytes(tmp_path):
    first = part(tmp_path, {"1", "3"}, name="first", gpu="GPU A")
    second = part(tmp_path, {"2", "4"}, name="second", gpu="GPU B")
    raw = bundle.write_bundle([first, second], first[1], tmp_path / "bundle.json")
    eligible, audit = bundle.load_bundle(raw, first[1].read_bytes(), strict)
    assert set(eligible) == {"1", "2", "3", "4"}
    assert eligible["1"]["artifact_sha256"] == strict(first[0].read_bytes(), first[1].read_bytes())["1"]["artifact_sha256"]
    assert {p["metadata"]["runtime"]["gpu"] for p in audit["parts"]} == {"GPU A", "GPU B"}
    assert audit["checkpoints"] == [["checkpoint", "revision"]]
    nested = bundle.write_bundle([(tmp_path / "bundle.json", first[1])], first[1], tmp_path / "nested.json")
    assert bundle.load_bundle(nested, first[1].read_bytes(), strict)[0] == eligible
    stored = json.loads(nested)["parts"][0]["prediction"]
    assert bundle.unpack(stored) == raw
    assert bundle.is_bundle(json.dumps(json.loads(raw), separators=(",", ":")).encode())


def reviewed(tmp_path):
    old = manifest()
    effective = copy.deepcopy(old)
    effective["pages"][1]["region"] = [0, 0, 1, .8]
    entry = {"id": "2", "source": "scan", "scan_page": 2, "original_region": [0, 0, 1, 1],
             "region": [0, 0, 1, .8], "evidence_id": "body-page2"}
    review = {"schema_version": 1, "kind": "scan-region-body-review", "reviewed_at": "2026-10-18",
              "sources": copy.deepcopy(old["sources"]),
              "original_manifest_sha256": bundle.sha(bundle.encode(old)),
              "evidence": {"body-page2": {**{k: v for k, v in entry.items() if k != "evidence_id"},
                  "evidence": "Source-reviewed body ends above the apparatus.", "reviewed_at": "2026-10-18",
                  "source_pdf_sha256": "a" * 64, "contact_sheet_sha256": "d" * 64}}}
    rp = tmp_path / "review.json"; rp.write_bytes(bundle.encode(review))
    effective["reviewed_substitutions"] = {"original_manifest_sha256": bundle.sha(bundle.encode(old)),
        "source_review": {"path": "data/review.json", "sha256": bundle.sha(rp.read_bytes())}, "regions": [entry]}
    ep = tmp_path / "effective.json"; ep.write_bytes(bundle.encode(effective))
    return old, effective, rp, ep


def test_only_exact_reviewed_old_geometry_is_held_without_an_extra_vote(tmp_path):
    old, effective, rp, ep = reviewed(tmp_path)
    original = part(tmp_path, {"1", "2", "3", "4"}, old, name="original")
    corrected = part(tmp_path, {"2"}, effective, name="body")
    raw = bundle.write_bundle([original, corrected], ep, tmp_path / "combined.json", [rp])
    eligible, audit = bundle.load_bundle(raw, ep.read_bytes(), strict)
    assert set(eligible) == {"1", "2", "3", "4"}
    assert len(audit["held_predictions"]) == 1
    assert audit["held_predictions"][0]["id"] == "2"
    assert eligible["2"]["artifact_sha256"] == strict(corrected[0].read_bytes(), ep.read_bytes())["2"]["artifact_sha256"]
    assert len(audit["parts"]) == 2


def test_new_geometry_only_still_requires_review_and_exact_original_authority(tmp_path):
    old, effective, rp, ep = reviewed(tmp_path)
    corrected = part(tmp_path, {"2"}, effective, name="body")
    with pytest.raises(ValueError, match="original authority"):
        bundle.write_bundle([corrected], ep, tmp_path / "combined.json", [rp])
    authority = tmp_path / "original.json"; authority.write_bytes(bundle.encode(old))
    with pytest.raises(ValueError, match="retained source review"):
        bundle.write_bundle([corrected], ep, tmp_path / "combined.json", authority_manifests=[authority])
    raw = bundle.write_bundle([corrected], ep, tmp_path / "combined.json", [rp], [authority])
    assert set(bundle.load_bundle(raw, ep.read_bytes(), strict)[0]) == {"2"}


def second_review(tmp_path, original, *, identifier="1"):
    effective = copy.deepcopy(original)
    page = next(p for p in effective["pages"] if p["id"] == identifier)
    old_region = page["region"]
    page["region"] = [0, 0, 1, .7]
    entry = {"id": identifier, "source": page["source"], "scan_page": page["scan_page"],
             "original_region": old_region, "region": page["region"], "evidence_id": "second-body-review"}
    review = {"schema_version": 1, "kind": "scan-region-body-review", "reviewed_at": "2026-10-18",
              "sources": copy.deepcopy(original["sources"]),
              "original_manifest_sha256": bundle.sha(bundle.encode(original)),
              "evidence": {entry["evidence_id"]: {**{k: v for k, v in entry.items() if k != "evidence_id"},
                  "evidence": "Second source review changes a different early crop without changing the running late request.",
                  "reviewed_at": "2026-10-18", "source_pdf_sha256": "a" * 64, "contact_sheet_sha256": "e" * 64}}}
    rp = tmp_path / "second-review.json"; rp.write_bytes(bundle.encode(review))
    effective["reviewed_substitutions"] = {"original_manifest_sha256": bundle.sha(bundle.encode(original)),
        "source_review": {"path": "data/second-review.json", "sha256": bundle.sha(rp.read_bytes())}, "regions": [entry]}
    ep = tmp_path / "second-effective.json"; ep.write_bytes(bundle.encode(effective))
    return effective, rp, ep


def test_two_stage_nested_and_flat_bundles_keep_both_authorities_and_held_attempts(tmp_path):
    old, late, r1, late_manifest = reviewed(tmp_path)
    original = part(tmp_path, {"1", "2", "3", "4"}, old, name="original")
    late_part = part(tmp_path, {"2"}, late, name="late")
    late_bundle_path = tmp_path / "late-bundle.json"
    late_bundle = bundle.write_bundle([original, late_part], late_manifest, late_bundle_path, [r1])
    final, r2, final_manifest = second_review(tmp_path, late)
    early_part = part(tmp_path, {"1"}, final, name="early")
    nested = bundle.write_bundle([(late_bundle_path, late_manifest), early_part], final_manifest,
                                 tmp_path / "nested-final.json", [r2])
    eligible, audit = bundle.load_bundle(nested, final_manifest.read_bytes(), strict)
    assert set(eligible) == {"1", "2", "3", "4"}
    assert {p["id"] for p in audit["held_predictions"]} == {"1", "2"}
    assert set(audit["source_review_sha256"]) == {bundle.sha(r1.read_bytes()), bundle.sha(r2.read_bytes())}
    assert eligible["1"]["artifact_sha256"] == strict(early_part[0].read_bytes(), final_manifest.read_bytes())["1"]["artifact_sha256"]
    assert eligible["2"]["artifact_sha256"] == strict(late_part[0].read_bytes(), late_manifest.read_bytes())["2"]["artifact_sha256"]
    assert eligible["3"]["artifact_sha256"] == strict(original[0].read_bytes(), original[1].read_bytes())["3"]["artifact_sha256"]
    assert bundle.unpack(json.loads(nested)["parts"][0]["prediction"]) == late_bundle
    assert late_bundle_path.read_bytes() == late_bundle
    flat = bundle.write_bundle([original, late_part, early_part], final_manifest, tmp_path / "flat-final.json", [r1, r2])
    assert bundle.load_bundle(flat, final_manifest.read_bytes(), strict)[0] == eligible


@pytest.mark.parametrize("missing", ["old-authority", "intermediate-authority", "first-review", "second-review"])
def test_new_only_final_geometry_still_requires_the_entire_review_chain(tmp_path, missing):
    old, late, r1, late_manifest = reviewed(tmp_path)
    old_path = tmp_path / "old-authority.json"; old_path.write_bytes(bundle.encode(old))
    final, r2, final_manifest = second_review(tmp_path, late)
    final_part = part(tmp_path, {"1", "2", "3", "4"}, final, name="final")
    reviews = [r1, r2]
    authorities = [old_path, late_manifest]
    complete = bundle.write_bundle([final_part], final_manifest, tmp_path / "complete.json", reviews, authorities)
    assert set(bundle.load_bundle(complete, final_manifest.read_bytes(), strict)[0]) == {"1", "2", "3", "4"}
    if missing == "old-authority": authorities.remove(old_path)
    elif missing == "intermediate-authority": authorities.remove(late_manifest)
    elif missing == "first-review": reviews.remove(r1)
    else: reviews.remove(r2)
    with pytest.raises(ValueError, match="authority|source review"):
        bundle.write_bundle([final_part], final_manifest, tmp_path / "missing.json", reviews, authorities)


def test_repeated_geometry_changes_keep_each_exact_transition(tmp_path):
    old, late, r1, late_manifest = reviewed(tmp_path)
    original = part(tmp_path, {"1", "2", "3", "4"}, old, name="original")
    late_part = part(tmp_path, {"2"}, late, name="late")
    final, r2, final_manifest = second_review(tmp_path, late, identifier="2")
    final_part = part(tmp_path, {"2"}, final, name="final")
    raw = bundle.write_bundle([original, late_part, final_part], final_manifest, tmp_path / "final.json", [r1, r2])
    eligible, audit = bundle.load_bundle(raw, final_manifest.read_bytes(), strict)
    held = next(p for p in audit["held_predictions"] if p["original_manifest_sha256"] == bundle.sha(original[1].read_bytes()))
    assert held["original_region"] == [0, 0, 1, 1]
    assert held["region"] == [0, 0, 1, .7]
    assert len(held["reviewed_transition_chain"]) == 2
    assert held["reviewed_transition_chain"][0]["region"] == [0, 0, 1, .8]
    assert held["reviewed_transition_chain"][1]["original_region"] == [0, 0, 1, .8]
    assert eligible["2"]["artifact_sha256"] == strict(final_part[0].read_bytes(), final_manifest.read_bytes())["2"]["artifact_sha256"]


@pytest.mark.parametrize("also_geometry", [False, True])
def test_only_exact_reviewed_page_prompt_changes_can_supersede_originals(tmp_path, also_geometry):
    old, effective, rp, ep = reviewed(tmp_path)
    suffix = "Use one ellipsis for each printed omission-dot series."
    if not also_geometry:
        effective["pages"][1]["region"] = old["pages"][1]["region"]
        effective["reviewed_substitutions"]["regions"][0]["region"] = old["pages"][1]["region"]
    effective["pages"][1]["prompt_suffix"] = suffix
    entry = effective["reviewed_substitutions"]["regions"][0]
    entry.update(original_prompt_suffix=None, prompt_suffix=suffix)
    review = json.loads(rp.read_bytes())
    review["evidence"]["body-page2"].update({k: v for k, v in entry.items() if k != "evidence_id"})
    rp.write_bytes(bundle.encode(review))
    effective["reviewed_substitutions"]["source_review"]["sha256"] = bundle.sha(rp.read_bytes())
    ep.write_bytes(bundle.encode(effective))
    original = part(tmp_path, {"1", "2"}, old, name="original")
    corrected = part(tmp_path, {"2"}, effective, name="corrected")
    raw = bundle.write_bundle([original, corrected], ep, tmp_path / "combined.json", [rp])
    eligible, audit = bundle.load_bundle(raw, ep.read_bytes(), strict)
    assert set(eligible) == {"1", "2"}
    assert audit["held_predictions"][0]["prompt_suffix"] == suffix
    assert audit["held_predictions"][0]["original_prompt_suffix"] is None
    del review["evidence"]["body-page2"]["prompt_suffix"]
    rp.write_bytes(bundle.encode(review))
    effective["reviewed_substitutions"]["source_review"]["sha256"] = bundle.sha(rp.read_bytes())
    ep.write_bytes(bundle.encode(effective))
    with pytest.raises(ValueError, match="suffix pins"):
        bundle.write_bundle([original], ep, tmp_path / "unreviewed.json", [rp])


@pytest.mark.parametrize("defect", ["duplicate", "checkpoint", "raw-checksum", "manifest-checksum", "missing-review", "evidence", "other-field"])
def test_ambiguous_or_unreviewed_bundles_are_rejected(tmp_path, defect):
    old, effective, rp, ep = reviewed(tmp_path)
    original = part(tmp_path, {"1", "2"}, old, name="original")
    new = part(tmp_path, {"1"} if defect == "duplicate" else {"2"}, effective,
               name="new", model="other" if defect == "checkpoint" else "checkpoint")
    value = {"kind": bundle.KIND, "schema_version": 1, "effective_manifest": bundle.retained(ep.read_bytes()),
             "source_reviews": [bundle.retained(rp.read_bytes())],
             "parts": [{"prediction": bundle.retained(p.read_bytes()), "manifest": bundle.retained(m.read_bytes())}
                       for p, m in [original, new]]}
    if defect == "raw-checksum": value["parts"][0]["prediction"]["raw_utf8"] += "\n"
    elif defect == "manifest-checksum": value["parts"][0]["manifest"]["raw_utf8"] += "\n"
    elif defect == "missing-review": value["source_reviews"] = []
    elif defect == "evidence":
        review = json.loads(rp.read_bytes()); review["evidence"]["body-page2"]["source_pdf_sha256"] = "wrong"
        raw_review = bundle.encode(review); value["source_reviews"] = [bundle.retained(raw_review)]
        effective["reviewed_substitutions"]["source_review"]["sha256"] = bundle.sha(raw_review)
        value["effective_manifest"] = bundle.retained(bundle.encode(effective))
    elif defect == "other-field":
        effective["pages"][0]["max_side"] = 999
        value["effective_manifest"] = bundle.retained(bundle.encode(effective))
    with pytest.raises(ValueError):
        bundle.load_bundle(bundle.encode(value), bundle.unpack(value["effective_manifest"]), strict)


def test_plans_are_disjoint_pending_ids_and_do_not_retry_failed_results(tmp_path):
    original = part(tmp_path, {"1", "3"})
    rows = [json.loads(line) for line in original[0].read_bytes().splitlines()]
    rows[-1].update(finish_reason="length", raw_prediction="μερικόν")
    original[0].write_bytes(("\n".join(json.dumps(row) for row in rows) + "\n").encode())
    raw = bundle.write_bundle([original], original[1], tmp_path / "completed.json")
    groups = bundle.pending_partitions(original[1].read_bytes(), raw, 3, model="checkpoint", revision="revision")
    assert groups == [["2"], ["4"], []]
    with pytest.raises(ValueError, match="checkpoint"):
        bundle.pending_partitions(original[1].read_bytes(), raw, 2, model="other", revision="revision")
    with pytest.raises(ValueError, match="truncated"):
        bundle.load_bundle(raw, original[1].read_bytes(), strict)


def test_shard_runner_keeps_full_manifest_and_rejects_resume_drift(tmp_path, monkeypatch):
    mp = tmp_path / "manifest.json"; mp.write_bytes(bundle.encode(manifest()))
    ids = tmp_path / "ids.json"; ids.write_bytes(bundle.encode(["1", "3"]))
    runtime = tmp_path / "runtime.json"; runtime.write_bytes(bundle.encode({"model": "checkpoint", "revision": "revision", "gpu": "GPU"}))
    image = tmp_path / "image.png"; image.write_bytes(b"image")
    calls = []
    monkeypatch.setattr(shard, "urlopen", lambda *a, **kw: io.BytesIO(b'{"data":[{"id":"checkpoint"}]}'))
    monkeypatch.setattr(shard.original, "prepare_images", lambda m, c: {p["id"]: (image, "c" * 64) for p in m["pages"]})
    def predict(args, image_path, prompt):
        calls.append(prompt)
        return {"raw_prediction": "ὁ λόγος", "finish_reason": "stop"}
    monkeypatch.setattr(shard.original, "http_prediction", predict)
    args = SimpleNamespace(manifest=mp, ids=ids, runtime_manifest=runtime, limit=None, model="checkpoint",
        revision="revision", max_tokens=12000, out=tmp_path / "out" / "shard.jsonl", base_url="https://example.org/v1",
        cache=tmp_path / "cache", workers=1)
    shard.run(args)
    meta, rows = bundle.inspect_leaf(args.out.read_bytes(), mp.read_bytes())
    assert set(rows) == {"1", "3"}
    assert meta["manifest_sha256"] == bundle.sha(mp.read_bytes())
    assert (args.out.parent / meta["manifest_archive"]).read_bytes() == mp.read_bytes()
    assert meta["shard"]["selected_ids"] == ["1", "3"]
    before = args.out.read_bytes(); shard.run(args)
    assert args.out.read_bytes() == before and len(calls) == 2
    ids.write_bytes(bundle.encode(["1", "2"]))
    with pytest.raises(ValueError, match="selected IDs changed"):
        shard.run(args)
    assert args.out.read_bytes() == before
