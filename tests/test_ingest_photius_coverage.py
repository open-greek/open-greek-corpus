import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_photius_coverage as ingest
import repair_photius_index as index


def prediction(tmp_path, manifest, model, *, missing=False, truncated=False):
    metadata = {"model": model, "revision": model * 40,
                "manifest_sha256": ingest.sha(ingest.encode(manifest)), "prompt": manifest["prompt"]}
    text = "ὁ λόγος σαφὴς καὶ καλὸς ἐστίν. " * 7
    rows = [{"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
             "region": page["region"], "image_sha256": "a" * 64,
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


def test_all_bekker_pages_are_covered_once_with_reversible_raw_readings(tmp_path, monkeypatch):
    body = root_fixture(tmp_path)
    manifests = [ingest.scan_manifest(), ingest.build_later_gap()]
    paths = [prediction(tmp_path, manifest, model) for model in ("a", "b") for manifest in manifests]
    # Test admission mechanics independently of the large real comparison text.
    source_document = {"id": "tlg4040.tlg001.local002", "license": {"text": "CC BY-SA 4.0"},
                       "sourceRights": "Source witness rights retained"}
    monkeypatch.setattr(ingest, "load_source_library", lambda path: (b"retained source", source_document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path)
    assert report["added_passages"] == 309
    assert report["historical_body_passages"] == 3846
    assert report["covered_authorial_scan_pages"] == 545
    assert report["added_scan_ranges"] == [[13, 278], [379, 421]]
    rows = [json.loads(line) for line in artifacts[index.CORPUS].decode().splitlines()]
    assert len({row["locus"] for row in rows}) == 309 + 3846
    added = [r for r in rows if r["edition"] == "bekker1824-independent-ocr-consensus"]
    assert all(len(row["ocr_consensus"]["witnesses"]) == 2 for row in added)
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
