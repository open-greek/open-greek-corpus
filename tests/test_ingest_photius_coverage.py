import gzip
from collections import Counter
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_photius_coverage as ingest
import repair_photius_index as index
import photius_retries as retries
import prepare_photius_retries as retry_requests
from report_polytonic_loss import detect
from prepare_photius_coverage import build_page13_retry
from prepare_photius_retries import build_retry, build_supplement, CHECKPOINT38
from ocr_consensus import restore_corpus_consensus


@pytest.fixture(autouse=True)
def isolate_source_geometry_authority(monkeypatch):
    # Synthetic historical retries are independent of subsequently reviewed
    # production crop boundaries and exact production raw-record pins.
    monkeypatch.setattr(retries, "known_gutter_manifests", lambda: {})


def prediction(tmp_path, manifest, model, *, missing=False, truncated=False):
    metadata = {"model": model, "revision": model * 40,
                "manifest_sha256": ingest.sha(ingest.encode(manifest)), "prompt": manifest["prompt"]}
    text = "ὁ λόγος σαφὴς καὶ καλὸς ἐστίν. " * 7
    rows = [{"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
             "region": page["region"], "image_sha256": "a" * 64,
             "prompt_sha256": ingest.sha(manifest["prompt"].encode()),
             "raw_prediction": text, "finish_reason": "length" if truncated else "stop"}
            for page in manifest["pages"]]
    if missing:
        rows.pop()
    path = tmp_path / (model + "-" + metadata["manifest_sha256"] + ".jsonl")
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [{"_meta": metadata}, *rows]) + "\n")
    return path


def root_fixture(tmp_path):
    raw = index.input_bytes(ROOT)
    archive = tmp_path / index.ARCHIVE
    archive.mkdir(parents=True)
    (archive / "before.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    body = index.generate(raw)[0]
    corpus = tmp_path / index.CORPUS
    corpus.parent.mkdir(parents=True)
    corpus.write_bytes(body)
    return body


def test_failed_truncated_missing_and_misidentified_predictions_are_rejected(tmp_path):
    manifest = ingest.scan_manifest()
    for kwargs, message in [({"missing": True}, "all requested"), ({"truncated": True}, "truncated")]:
        with pytest.raises(ValueError, match=message):
            ingest.load_prediction(prediction(tmp_path, manifest, "a", **kwargs), [manifest])
    path = prediction(tmp_path, manifest, "b")
    lines = path.read_text().splitlines()
    row = json.loads(lines[1]);row["region"] = [0, 0, .5, 1];lines[1] = json.dumps(row)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="geometry"):
        ingest.load_prediction(path, [manifest])
    with pytest.raises(ValueError, match="another scan"):
        ingest.load_prediction(prediction(tmp_path, manifest, "c"), [ingest.build_later_gap()])
    path = prediction(tmp_path, manifest, "d")
    lines = path.read_text().splitlines()
    row = json.loads(lines[1]);row["prompt_sha256"] = "changed";lines[1] = json.dumps(row)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="page prompt"):
        ingest.load_prediction(path, [manifest])


def test_two_revisions_of_one_family_cannot_supply_independent_votes(tmp_path):
    manifests = [ingest.scan_manifest(), ingest.build_later_gap()]
    paths = []
    for label in ("a", "b"):
        for manifest in manifests:
            path = prediction(tmp_path, manifest, label)
            rows = [json.loads(line) for line in path.read_bytes().splitlines()]
            rows[0]["_meta"]["model"] = "same-model-family"
            path.write_bytes(b"\n".join(json.dumps(row, ensure_ascii=False).encode() for row in rows) + b"\n")
            paths.append(path)
    with pytest.raises(ValueError, match="same model family"):
        ingest.prepare_fresh_inputs(paths, manifests)


def test_all_bekker_pages_are_covered_once_with_reversible_raw_readings(tmp_path, monkeypatch):
    body = root_fixture(tmp_path)
    manifests = [ingest.scan_manifest(), ingest.build_later_gap()]
    paths = [prediction(tmp_path, manifest, model) for model in ("a", "b") for manifest in manifests]
    # Test admission mechanics independently of the large real comparison text.
    source_document = {"id": "tlg4040.tlg001.local002", "license": {"text": "CC BY-SA 4.0"},
                       "sourceRights": "Source witness rights retained"}
    comparison_text = "κεφαλὴ προοιμίου " + "ὁ λόγος σαφὴς καὶ καλὸς ἐστίν. " * 7 + "σχόλιον κριτικὸν ἐκ τῶν κωδίκων"
    source_rows = {13: {"id": "source-library", "text": comparison_text, "artifact_sha256": "f" * 64}}
    monkeypatch.setattr(ingest, "load_source_library", lambda path: (b"retained source", source_document, source_rows))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path)
    assert report["added_passages"] == 309
    assert report["historical_body_passages"] == 3846
    assert report["quality_scope"]["proofread_critical_text"] is False
    assert report["quality_scope"]["historical_rows_byte_identical"] == 3846
    assert report["quality_scope"]["historical_apparatus_issue"].endswith("/issues/60")
    assert report["covered_authorial_scan_pages"] == 545
    assert report["added_scan_ranges"] == [[13, 278], [379, 421]]
    assert report["retained_page_mapping"]["logical_positions_are_physical_citations"] is False
    assert [(p["retained_legacy_scan_page"], p["authorial_printed_page"])
            for p in report["source_scan_exceptions"]] == [(169, 434), (170, 435)]
    assert report["source_library"]["body_comparison_counts"] == {"held-comparison-only": 1}
    comparison = json.loads(gzip.decompress(artifacts[Path(report["source_library"]["body_comparison_audit"]["path"])]))
    assert comparison["13"]["original_text"] == comparison_text
    assert comparison["13"]["status"] == "held-comparison-only"
    rows = [json.loads(line) for line in artifacts[index.CORPUS].decode().splitlines()]
    assert len({row["locus"] for row in rows}) == 309 + 3846
    added = [r for r in rows if r["edition"] == "bekker1824-independent-ocr-consensus"]
    assert all(len(row["ocr_consensus"]["witnesses"]) == 2 for row in added)
    full_networks = json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))
    assert len(full_networks) == 310  # The overlap survives in the audit, outside primary text.
    for row in added:
        reference = row["ocr_consensus"]["full_network"]
        compact = {key: row[key] for key in ("text", "analysis_text", "ocr_consensus")}
        full = restore_corpus_consensus(compact, full_networks[reference["key"]])
        assert all("readings" in slot for slot in full["ocr_consensus"]["slots"])
        assert all("readings" not in slot for slot in row["ocr_consensus"]["slots"])
    assert not any(row["physical_refs"]["scan_page"] == 279 for row in added)
    historical = "".join(line for line in artifacts[index.CORPUS].decode().splitlines(keepends=True)
                         if json.loads(line)["edition"] != "bekker1824-independent-ocr-consensus").encode()
    assert historical == body
    assert report["source_library"]["separate_api_notice"]["tdm_reservation"] == 1
    assert report["source_library"]["separate_api_notice"]["ai_training"].endswith("see tdm_policy")
    assert ingest.generate(list(reversed(paths)), tmp_path / "source", tmp_path)[0] == artifacts
    ingest.apply(artifacts, report, tmp_path)
    ingest.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == body


def test_both_requests_and_two_distinct_checkpoints_are_required(tmp_path):
    root_fixture(tmp_path)
    manifest = ingest.scan_manifest()
    paths = [prediction(tmp_path, manifest, model) for model in ("a", "b")]
    with pytest.raises(ValueError, match="both missing-volume requests"):
        ingest.generate(paths, tmp_path / "source", tmp_path)
    path = prediction(tmp_path, manifest, "a")
    with pytest.raises(ValueError, match="Repeated checkpoint"):
        ingest.generate([path, path], tmp_path / "source", tmp_path)


def test_source_comparison_checksum_is_enforced(tmp_path):
    source = tmp_path / "changed.json.gz"
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="comparison witness changed"):
        ingest.load_source_library(source)


def retry_fixture(tmp_path):
    root_fixture(tmp_path)
    manifests = [ingest.scan_manifest(), ingest.build_later_gap()]
    paths = [prediction(tmp_path, manifest, model) for model in ("a", "b") for manifest in manifests]
    lines = paths[0].read_text().splitlines()
    for i, line in enumerate(lines[1:], 1):
        row = json.loads(line)
        if row["id"] == "photius-bekker-0013":
            row.update(finish_reason="length", raw_prediction="σκοποῦ … " + ". " * 200)
            lines[i] = json.dumps(row, ensure_ascii=False)
    paths[0].write_text("\n".join(lines) + "\n")
    manifest = build_page13_retry()
    retry_paths = []
    for model in ("a", "b"):
        meta = {"model": model, "revision": model * 40, "prompt": manifest["prompt"],
                "manifest_sha256": ingest.sha(ingest.encode(manifest))}
        records = [{"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
                    "region": page["region"], "image_sha256": "b" * 64,
                    "prompt_sha256": ingest.sha((manifest["prompt"] + " " + page["prompt_suffix"]).encode()),
                    "raw_prediction": "ὁ λόγος σαφὴς καὶ καλὸς ἐστίν.", "finish_reason": "stop"}
                   for page in manifest["pages"]]
        path = tmp_path / (model + "-retry.jsonl")
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in [{"_meta": meta}, *records]) + "\n")
        retry_paths.append(path)
    _, models, _ = ingest.prepare_fresh_inputs(paths, manifests, allow_unreviewed_retry_preparation=True)
    review = tmp_path / "review.json"
    retries.write_source_review(models, retry_paths, review, "Synthetic source-review fixture",
        {page["id"]: "Synthetic reviewed complete lines with no apparatus" for page in manifest["pages"]},
        "2026-10-18T07:00:00Z")
    return paths, retry_paths, review


def test_reviewed_strips_replace_one_vote_and_preserve_failed_original(tmp_path, monkeypatch):
    paths, retry_paths, review = retry_fixture(tmp_path)
    with pytest.raises(ValueError, match="truncated"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()])
    document = {"id": "test-source", "license": {"text": "CC BY-SA 4.0"}, "sourceRights": "Retained source rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda path: (b"source", document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=retry_paths, retry_review=review)
    assert report["added_passages"] == 309
    assert len(report["fresh_ocr_files"]) == 4
    assert len(report["reviewed_retry"]["raw_files"]) == 2
    assert artifacts[Path(report["reviewed_retry"]["source_review"]["path"])] == review.read_bytes()
    networks = json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))
    witnesses = networks["13"]["ocr_consensus"]["witnesses"]
    assert len(witnesses) == 2
    assert len({w["vote_group"] for w in witnesses}) == 2
    assert all(w["text"].count("ὁ λόγος") == 5 for w in witnesses)
    assert any(w["reviewed_retry"]["original_record"]["finish_reason"] == "length" for w in witnesses)
    assert all(len(w["reviewed_retry"]["strips"]) == 5 for w in witnesses)
    assert ingest.generate(list(reversed(paths)), tmp_path / "source", tmp_path,
        retry_paths=list(reversed(retry_paths)), retry_review=review)[0] == artifacts
    ingest.apply(artifacts, report, tmp_path)
    ingest.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == index.generate(index.input_bytes(ROOT))[0]


@pytest.mark.parametrize("change, message", [
    ("geometry", "geometry"), ("prompt", "prompt"), ("truncated", "truncated"),
    ("original", "original page attempts"), ("strip-review", "Every retry strip"),
    ("image", "different source images"),
])
def test_retry_review_and_raw_input_pins_are_enforced(tmp_path, change, message):
    paths, retry_paths, review_path = retry_fixture(tmp_path)
    review = json.loads(review_path.read_text())
    if change in {"geometry", "prompt", "truncated", "image"}:
        path = retry_paths[0]
        records = [json.loads(line) for line in path.read_text().splitlines()]
        if change == "geometry": records[1]["region"] = [0, 0, 1, 1]
        elif change == "prompt": records[1]["prompt_sha256"] = "unreviewed"
        elif change == "truncated": records[1]["finish_reason"] = "length"
        else: records[1]["image_sha256"] = "c" * 64
        previous_sha = ingest.sha(path.read_bytes())
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n")
        next(run for run in review["reviewed_runs"] if run["sha256"] == previous_sha)["sha256"] = ingest.sha(path.read_bytes())
    elif change == "original": review["original_artifacts_sha256"][0] = "unreviewed"
    else: review["strip_reviews"][0]["reading_complete"] = False
    review_path.write_text(json.dumps(review) + "\n")
    with pytest.raises(ValueError, match=message):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], retry_paths, review_path)


def test_retries_without_a_separate_review_do_not_bypass_failed_page(tmp_path):
    paths, retry_paths, review_path = retry_fixture(tmp_path)
    with pytest.raises(ValueError, match="separate completed source review"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], retry_paths)


def multiple_retry_fixture(tmp_path):
    root_fixture(tmp_path)
    manifests = [ingest.scan_manifest(), ingest.build_later_gap()]
    checkpoints = [("Qwen/Qwen3.6-27B", "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"),
                   (CHECKPOINT38["model"], CHECKPOINT38["revision"])]
    paths = []
    for label, checkpoint in zip(("a", "b"), checkpoints):
        for manifest in manifests:
            path = prediction(tmp_path, manifest, label)
            data = [json.loads(line) for line in path.read_bytes().splitlines()]
            data[0]["_meta"].update(model=checkpoint[0], revision=checkpoint[1])
            for row in data[1:]:
                if row["scan_page"] == 13 or label == "b" and row["scan_page"] in (47, 50):
                    row.update(finish_reason="length", raw_prediction="καὶ " * 100)
            path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in data) + "\n")
            paths.append(path)
    _, models, _ = ingest.prepare_fresh_inputs(paths, manifests, allow_unreviewed_retry_preparation=True)
    raw_paths, reviews = [], []
    for number, request in [(13, build_page13_retry()), (47, build_retry(47)), (50, build_retry(50))]:
        selected = checkpoints if number == 13 else checkpoints[1:]
        retries_for_page = []
        for i, (model, revision) in enumerate(selected):
            meta = {"model": model, "revision": revision, "prompt": request["prompt"],
                    "manifest_sha256": ingest.sha(ingest.encode(request))}
            rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"],
                     "region": p["region"], "image_sha256": "c" * 64,
                     "prompt_sha256": ingest.sha((request["prompt"] + " " + p["prompt_suffix"]).encode()),
                     "raw_prediction": "θεὸς λέγει λόγον σαφῆ.", "finish_reason": "stop"} for p in request["pages"]]
            path = tmp_path / f"retry-{number}-{i}.jsonl"
            path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [{"_meta": meta}, *rows]) + "\n")
            retries_for_page.append(path)
        review = tmp_path / f"review-{number}.json"
        retries.write_source_review(models, retries_for_page, review, "Synthetic complete body review",
            {p["id"]: "Synthetic complete source-line fixture" for p in request["pages"]},
            "2026-10-18T07:00:00Z", request)
        reviews.append(review); raw_paths.extend(retries_for_page)
    return paths, raw_paths, reviews


def test_multiple_checkpoint_specific_retries_keep_successful_whole_page_votes(tmp_path, monkeypatch):
    paths, raw_paths, reviews = multiple_retry_fixture(tmp_path)
    inputs, models, evidence = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], raw_paths, reviews)
    assert len(inputs) == 4 and len(models) == 2 and len(evidence) == 3
    original36 = next(records for checkpoint, records in models.items() if checkpoint[0] == "Qwen/Qwen3.6-27B")
    retried38 = next(records for checkpoint, records in models.items() if checkpoint[0] == CHECKPOINT38["model"])
    assert all("reviewed_retry" not in original36[f"photius-bekker-{n:04d}"][2] for n in (47, 50))
    assert all("reviewed_retry" in retried38[f"photius-bekker-{n:04d}"][2] for n in (47, 50))
    document = {"id": "test-source", "license": {"text": "CC BY-SA 4.0"}, "sourceRights": "Retained rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda p: (b"source", document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=raw_paths, retry_review=reviews)
    assert report["reviewed_retry"] is None
    assert {r["scan_page"] for r in report["reviewed_retries"]} == {13, 47, 50}
    assert [len(r["raw_files"]) for r in sorted(report["reviewed_retries"], key=lambda r: r["scan_page"])] == [2, 1, 1]
    networks = json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))
    witnesses = networks["47"]["ocr_consensus"]["witnesses"]
    assert len(witnesses) == 2 and sum("reviewed_retry" in w for w in witnesses) == 1
    assert len(networks) == 310 and report["added_passages"] == 309
    assert ingest.generate(list(reversed(paths)), tmp_path / "source", tmp_path,
        retry_paths=list(reversed(raw_paths)), retry_review=list(reversed(reviews)))[0] == artifacts
    with pytest.raises(ValueError, match="truncated"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
            raw_paths, [p for p in reviews if p.name != "review-47.json"])


def test_retry_permission_does_not_leak_to_a_successful_other_checkpoint(tmp_path):
    paths, raw_paths, reviews = multiple_retry_fixture(tmp_path)
    path = paths[0]
    data = [json.loads(line) for line in path.read_bytes().splitlines()]
    next(row for row in data[1:] if row["scan_page"] == 50)["finish_reason"] = "length"
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in data) + "\n")
    with pytest.raises(ValueError, match="truncated"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], raw_paths, reviews)
    with pytest.raises(ValueError, match="truncated"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
            allow_unreviewed_retry_preparation=True)


def supplement_fixture(tmp_path):
    paths, base_paths, reviews = multiple_retry_fixture(tmp_path)
    base = next(path for path in base_paths if path.name == "retry-50-0.jsonl")
    records = [json.loads(line) for line in base.read_bytes().splitlines()]
    next(row for row in records[1:] if row["id"].endswith("left-lower")).update(
        finish_reason="length", raw_prediction="καὶ " * 100)
    base.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n")
    request = build_supplement(50, "left-lower")
    metadata = {**records[0]["_meta"], "manifest_sha256": ingest.sha(ingest.encode(request))}
    rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"],
             "region": p["region"], "image_sha256": "d" * 64,
             "prompt_sha256": ingest.sha((request["prompt"] + " " + p["prompt_suffix"]).encode()),
             "raw_prediction": "θεὸς λέγει λόγον σαφῆ.", "finish_reason": "stop"} for p in request["pages"]]
    supplement = tmp_path / "supplement-50.jsonl"
    supplement.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [{"_meta": metadata}, *rows]) + "\n")
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              allow_unreviewed_retry_preparation=True)
    review = next(path for path in reviews if path.name == "review-50.json")
    review.unlink()
    parent = build_retry(50)
    retries.write_source_review(models, [base], review, "Synthetic completed source comparison",
        {p["id"]: "Synthetic effective-strip source review" for p in parent["pages"]},
        "2026-10-18T07:00:00Z", parent, [supplement],
        {p["id"]: "Synthetic complete nonoverlapping source lines" for p in request["pages"]})
    return paths, base_paths, reviews, supplement


def test_failed_retry_supplement_keeps_successful_siblings_and_one_vote(tmp_path, monkeypatch):
    paths, base_paths, reviews, supplement = supplement_fixture(tmp_path)
    document = {"id": "test-source", "license": {"text": "CC BY-SA4.0"}, "sourceRights": "Retained rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda p: (b"source", document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=base_paths,
                                        retry_review=reviews, supplement_paths=[supplement])
    networks = json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))
    witnesses = networks["50"]["ocr_consensus"]["witnesses"]
    assert len(witnesses) == 2 and len({w["vote_group"] for w in witnesses}) == 2
    assembled = next(w["reviewed_retry"] for w in witnesses if "reviewed_retry" in w)
    assert len(assembled["strips"]) == 6
    assert assembled["held_retry_strips"][0]["finish_reason"] == "length"
    assert assembled["original_record"]["finish_reason"] == "length"
    assert len(assembled["supplements"]) == 1
    assert len([p for p in assembled["strips"] if "-part" not in p["id"]]) == 3
    assert report["added_passages"] == 309 and len(networks) == 310
    retry = next(r for r in report["reviewed_retries"] if r["scan_page"] == 50)
    assert len(retry["supplements"]) == 1
    retained = retry["supplements"][0]["raw_files"][0]
    assert artifacts[Path(retained["path"])] == supplement.read_bytes()
    quality = json.loads(artifacts[Path(report["fresh_outcome_quality"]["path"])])
    assert quality["selection_rule"] is None
    dispositions = [r["admission_disposition"] for r in quality["outcomes"]
                    if r["scan_page"] == 50 and r["model"] == CHECKPOINT38["model"]]
    assert Counter(dispositions) == {"held-original-attempt": 1, "held-failed-retry-strip": 1,
                                     "accepted-source-reviewed-assembly-part": 6}
    ingest.apply(artifacts, report, tmp_path)
    inputs, models, evidence = ingest.prepare_report_inputs(tmp_path, report, [ingest.scan_manifest(), ingest.build_later_gap()])
    assert len(inputs) == 4 and len(evidence) == 3 and all(len(pages) == 310 for pages in models.values())
    altered = json.loads(json.dumps(report))
    altered["fresh_ocr_files"][0]["model"] = "unreviewed"
    with pytest.raises(ValueError, match="original metadata"):
        ingest.prepare_report_inputs(tmp_path, altered, [ingest.scan_manifest(), ingest.build_later_gap()])
    ingest.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == index.generate(index.input_bytes(ROOT))[0]


@pytest.mark.parametrize("change,message", [
    ("missing", "Missing or reused"), ("geometry", "geometry"), ("prompt", "prompt"),
    ("truncated", "supplement is failed"), ("successful-parent", "successful retry strip"),
    ("source-review", "Every supplement part"),
])
def test_supplement_cannot_bypass_its_reviewed_failure(tmp_path, change, message):
    paths, base_paths, reviews, supplement = supplement_fixture(tmp_path)
    review_path = next(path for path in reviews if path.name == "review-50.json")
    review = json.loads(review_path.read_bytes())
    if change in {"geometry", "prompt", "truncated"}:
        data = [json.loads(line) for line in supplement.read_bytes().splitlines()]
        if change == "geometry": data[1]["region"] = [0, 0, 1, 1]
        elif change == "prompt": data[1]["prompt_sha256"] = "unreviewed"
        else: data[1]["finish_reason"] = "length"
        supplement.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in data) + "\n")
        review["reviewed_supplements"][0]["sha256"] = ingest.sha(supplement.read_bytes())
    elif change == "successful-parent":
        base = next(path for path in base_paths if path.name == "retry-50-0.jsonl")
        data = [json.loads(line) for line in base.read_bytes().splitlines()]
        next(row for row in data[1:] if row["id"].endswith("left-lower"))["finish_reason"] = "stop"
        base.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in data) + "\n")
        review["reviewed_runs"][0]["sha256"] = ingest.sha(base.read_bytes())
    elif change == "source-review": review["reviewed_supplements"][0]["strip_reviews"][0]["reading_complete"] = False
    review_path.write_text(json.dumps(review) + "\n")
    with pytest.raises(ValueError, match=message):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], base_paths, reviews,
                                   supplement_paths=[] if change == "missing" else [supplement])


def nested_supplement_fixture(tmp_path, monkeypatch):
    paths, bases, reviews, parent_raw = supplement_fixture(tmp_path)
    values = [json.loads(line) for line in parent_raw.read_bytes().splitlines()]
    target = values[2]
    target["raw_prediction"] = "ἡ δὲ ἡδὺς καὶ ἡδύποτος " * 9
    parent_raw.write_bytes(b"\n".join(json.dumps(v, ensure_ascii=False).encode() for v in values) + b"\n")
    target_line = parent_raw.read_bytes().splitlines()[2]
    from audit_photius_fresh import REPETITION_POLICY, repetition
    measured = repetition(target["raw_prediction"])
    condition = {"kind": "source-confirmed-repetition-loop", "raw_file_sha256": ingest.sha(parent_raw.read_bytes()),
        "prediction_record_sha256": ingest.sha(target_line), "raw_prediction_sha256": ingest.sha(target["raw_prediction"].encode()),
        "finish_reason": "stop", "greek_word_runs": measured["greek_word_runs"],
        "most_repeated_phrase_occurrences": measured["most_repeated_phrase"]["occurrences"],
        "most_repeated_line_occurrences": measured["most_repeated_line"]["occurrences"],
        "repetition_policy_sha256": ingest.sha(ingest.encode(REPETITION_POLICY))}
    assert condition["most_repeated_phrase_occurrences"] >= 4 and condition["most_repeated_line_occurrences"] < 4
    monkeypatch.setitem(retry_requests.SUPPLEMENT_REVIEWS, (50, "left-lower-part02"), {
        "parent_supplement": "left-lower", "cuts": [.583, .645, .712],
        "evidence": "Synthetic exact source-confirmed child loop", "replacement_condition": condition})
    request = build_supplement(50, "left-lower-part02")
    metadata = {**values[0]["_meta"], "manifest_sha256": ingest.sha(ingest.encode(request))}
    rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"],
             "region": p["region"], "image_sha256": "e" * 64,
             "prompt_sha256": ingest.sha((request["prompt"] + " " + p["prompt_suffix"]).encode()),
             "raw_prediction": "σαφὴς ὁ λόγος. θεὸς λέγει ἀλήθειαν.", "finish_reason": "stop"} for p in request["pages"]]
    child_raw = tmp_path / "child-50.jsonl"
    child_raw.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": metadata}, *rows]) + b"\n")
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              allow_unreviewed_retry_preparation=True)
    review_path = next(p for p in reviews if p.name == "review-50.json")
    review_path.unlink()
    base_request = build_retry(50)
    evidence = {p["id"]: "Synthetic complete effective source lines" for r in
                [build_supplement(50, "left-lower"), request] for p in r["pages"]}
    retries.write_source_review(models, [p for p in bases if p.name == "retry-50-0.jsonl"], review_path,
        "Synthetic completed nested source comparison", {p["id"]: "Synthetic full source body" for p in base_request["pages"]},
        "2026-10-18T07:00:00Z", base_request, [child_raw, parent_raw], evidence)
    return paths, bases, reviews, parent_raw, child_raw


def test_nested_retry_keeps_both_loop_attempts_and_all_successful_siblings(tmp_path, monkeypatch):
    paths, bases, reviews, parent_raw, child_raw = nested_supplement_fixture(tmp_path, monkeypatch)
    _, models, evidence = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
        bases, reviews, supplement_paths=[child_raw, parent_raw])
    assembly = models[(CHECKPOINT38["model"], CHECKPOINT38["revision"])]["photius-bekker-0050"][2]["reviewed_retry"]
    assert len(assembly["strips"]) == 7
    assert len(assembly["held_retry_strips"]) == len(assembly["held_retry_strip_sources"]) == 2
    assert {r["finish_reason"] for r in assembly["held_retry_strips"]} == {"length", "stop"}
    assert len(assembly["supplements"]) == 2
    assert len([r for r in assembly["strips"] if "-part" not in r["id"]]) == 3
    assert len([r for r in assembly["strips"] if r["id"].count("-part") == 1]) == 2
    report = ingest.outcome_quality([*paths, *bases, parent_raw, child_raw], models)
    counts = Counter(r["admission_disposition"] for r in report["outcomes"]
                     if r["model"] == CHECKPOINT38["model"] and r["scan_page"] == 50)
    assert counts == {"held-original-attempt": 1, "held-failed-retry-strip": 1,
                      "held-source-confirmed-degraded-retry-strip": 1, "accepted-source-reviewed-assembly-part": 7}
    page_evidence = next(e for e in evidence if e["manifest"]["retry_of"]["page_id"].endswith("0050"))
    assert {r["raw"] for s in page_evidence["supplements"] for r in s["raw_files"]} == {
        parent_raw.read_bytes(), child_raw.read_bytes()}
    document = {"id": "test-source", "license": {"text": "CC BY-SA4.0"}, "sourceRights": "Retained rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda p: (b"source", document, {}))
    artifacts, admission = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=bases,
        retry_review=reviews, supplement_paths=[parent_raw, child_raw])
    ingest.apply(artifacts, admission, tmp_path)
    _, replay_models, replay_evidence = ingest.prepare_report_inputs(tmp_path, admission,
        [ingest.scan_manifest(), ingest.build_later_gap()])
    assert replay_models == models
    assert len(replay_evidence) == 3 and admission["covered_authorial_scan_pages"] == 545
    assert len(json.loads(gzip.decompress(artifacts[Path(admission["full_networks"]["path"])]))) == 310
    ingest.undo(tmp_path)


@pytest.mark.parametrize("change,message", [("missing-parent", "Missing or reused"),
    ("parent-finish", "exact retained attempt"), ("child-loop", "still repeats"),
    ("parent-review", "explicit supplemental completion")])
def test_nested_retry_cannot_bypass_exact_parent_or_leaf_review(tmp_path, monkeypatch, change, message):
    paths, bases, reviews, parent_raw, child_raw = nested_supplement_fixture(tmp_path, monkeypatch)
    review_path = next(p for p in reviews if p.name == "review-50.json")
    review = json.loads(review_path.read_bytes())
    supplements = [parent_raw, child_raw]
    if change == "missing-parent":
        supplements = [child_raw]
    elif change in {"parent-finish", "child-loop"}:
        path = parent_raw if change == "parent-finish" else child_raw
        old_sha = ingest.sha(path.read_bytes())
        rows = [json.loads(line) for line in path.read_bytes().splitlines()]
        if change == "parent-finish": rows[2]["finish_reason"] = "length"
        else: rows[1]["raw_prediction"] = "θεὸς λέγει λόγον σαφῆ καὶ καλὸν εἰς τὴν ἀλήθειαν.\n" * 5
        path.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in rows) + b"\n")
        next(d for d in review["reviewed_supplements"] if d["sha256"] == old_sha)["sha256"] = ingest.sha(path.read_bytes())
    else:
        parent_sha = ingest.sha(ingest.encode(build_supplement(50, "left-lower")))
        parent = next(d for d in review["reviewed_supplements"] if d["manifest_sha256"] == parent_sha)
        parent["strip_reviews"][1].pop("completed_by_supplements")
    review_path.write_bytes(ingest.encode(review))
    with pytest.raises(ValueError, match=message):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
            bases, reviews, supplement_paths=supplements)


@pytest.mark.parametrize("kind", ["mark-stripping", "repetition-loop"])
def test_exact_source_confirmed_exception_keeps_other_successful_readings(tmp_path, monkeypatch, kind):
    paths, base_paths, reviews = multiple_retry_fixture(tmp_path)
    base = next(p for p in base_paths if p.name == "retry-13-1.jsonl")
    data = [json.loads(line) for line in base.read_bytes().splitlines()]
    target = next(r for r in data[1:] if r["id"].endswith("upper-preface"))
    target["raw_prediction"] = ("Ο ΛΟΓΟΣ\nο λογος σαφης και καλος εστιν. " * 20 if kind == "mark-stripping"
                                else "τοὺς τοὺς ἰσμορφήσιν ἰσμορφήσιν ἰσμορφήσιν\n" * 20)
    base.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in data) + b"\n")
    source_line = next(line for line in base.read_bytes().splitlines()
                       if json.loads(line).get("id") == target["id"])
    marks = detect(target["raw_prediction"])
    if kind == "mark-stripping":
        assert marks["flag"] and marks["breathing_letters"] == 0
    # The production request pins a real source-confirmed record. This synthetic
    # authority tests the same closed path without copying a full OCR run here.
    original_review = retry_requests.SUPPLEMENT_REVIEWS[(13, "upper-preface")]
    source_condition = (original_review["replacement_condition"] if kind == "mark-stripping"
                        else retry_requests.SUPPLEMENT_REVIEWS[(113, "right-first")]["replacement_condition"])
    condition = {**source_condition,
                 "raw_file_sha256": ingest.sha(base.read_bytes()),
                 "prediction_record_sha256": ingest.sha(source_line),
                 "raw_prediction_sha256": ingest.sha(target["raw_prediction"].encode()),
                 "greek_letters": marks["greek_letters"]}
    if kind == "repetition-loop":
        from audit_photius_fresh import repetition
        measured = repetition(target["raw_prediction"])
        condition.update(greek_word_runs=measured["greek_word_runs"],
                         most_repeated_phrase_occurrences=measured["most_repeated_phrase"]["occurrences"],
                         most_repeated_line_occurrences=measured["most_repeated_line"]["occurrences"])
    monkeypatch.setitem(retry_requests.SUPPLEMENT_REVIEWS, (13, "upper-preface"),
                        {**original_review, "replacement_condition": condition})
    request = build_supplement(13, "upper-preface")
    meta = {**data[0]["_meta"], "manifest_sha256": ingest.sha(ingest.encode(request))}
    rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"],
             "region": p["region"], "image_sha256": "d" * 64,
             "prompt_sha256": ingest.sha((request["prompt"] + " " + p["prompt_suffix"]).encode()),
             "raw_prediction": "ὁ λόγος σαφὴς καὶ καλός ἐστιν. " * (20 if kind == "mark-stripping" else 2), "finish_reason": "stop"}
            for p in request["pages"]]
    supplement = tmp_path / "mark-supplement.jsonl"
    supplement.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": meta}, *rows]) + b"\n")
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              allow_unreviewed_retry_preparation=True)
    review_path = next(p for p in reviews if p.name == "review-13.json")
    review_path.unlink()
    parent = build_page13_retry()
    page_paths = [p for p in base_paths if p.name.startswith("retry-13-")]
    retries.write_source_review(models, page_paths, review_path, "Synthetic completed source and mark review",
        {p["id"]: "Synthetic effective source-line review" for p in parent["pages"]},
        "2026-10-18T07:00:00Z", parent, [supplement],
        {p["id"]: "Synthetic source marks restored in complete lines" for p in request["pages"]})
    _, models, evidence = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
        base_paths, reviews, supplement_paths=[supplement])
    original36 = next(records for checkpoint, records in models.items() if checkpoint[0] == "Qwen/Qwen3.6-27B")
    retried38 = next(records for checkpoint, records in models.items() if checkpoint[0] == CHECKPOINT38["model"])
    assert len(original36["photius-bekker-0013"][2]["reviewed_retry"]["strips"]) == 5
    assembly = retried38["photius-bekker-0013"][2]["reviewed_retry"]
    assert len(assembly["strips"]) == 7
    assert len([p for p in assembly["strips"] if "-part" not in p["id"]]) == 4
    assert assembly["held_retry_strips"][0]["finish_reason"] == "stop"
    replacement = assembly["supplements"][0]
    verifier = retries.confirmed_mark_stripping if kind == "mark-stripping" else retries.confirmed_repetition_loop
    assert verifier(replacement, base.read_bytes(), source_line, target)
    assert not verifier(replacement, base.read_bytes() + b"\n", source_line, target)
    assert not verifier(replacement, base.read_bytes(), source_line + b" ", target)
    rows[1]["raw_prediction"] = "ο λογος σαφης και καλος εστιν. " * 20
    supplement.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": meta}, *rows]) + b"\n")
    review = json.loads(review_path.read_bytes())
    review["reviewed_supplements"][0]["sha256"] = ingest.sha(supplement.read_bytes())
    review_path.write_bytes(ingest.encode(review))
    with pytest.raises(ValueError, match="still strips polytonic" if kind == "mark-stripping" else "still repeats"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], base_paths, reviews,
                                    supplement_paths=[supplement])
