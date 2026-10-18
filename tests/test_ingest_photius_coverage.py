import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_photius_coverage as ingest
import repair_photius_index as index
import photius_retries as retries
from prepare_photius_coverage import build_page13_retry
from ocr_consensus import restore_corpus_consensus


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
