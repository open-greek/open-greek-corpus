from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_scan_coverage as ingest
from scan_fragment_reviews import PAGE, PRECEDING_PAGE, IMAGE_SHA256, PRECEDING_IMAGE_SHA256, unapply_review


def fixture():
    manifest = json.loads((ROOT / "data/ingest_reviews/coverage/apollonius-conica-4-letter-jobs.json").read_text())
    raw_manifest = ingest.encoded(manifest)
    inputs, raws = [], []
    for number in (6, 8):
        values = [{"_meta": {"model": f"Qwen/Qwen3.{number}-27B", "revision": str(number),
            "manifest_sha256": ingest.sha(raw_manifest), "prompt": manifest["prompt"]}}]
        for page, text, image in [(manifest["pages"][0], "καὶ τὰ ἄλλα τὰ ὅμο-", PRECEDING_IMAGE_SHA256),
                                  (manifest["pages"][1], "γενῆ τούτοις ἀπλῶς ὑπὸ οὐδενὸς νενοημένα εὕρηκα.", IMAGE_SHA256)]:
            values.append({key: page[key] for key in ("id", "source", "scan_page", "region")})
            values[-1].update(finish_reason="stop", raw_prediction=text, image_sha256=image,
                prompt_sha256=ingest.sha(manifest["prompt"].encode()))
        raw = ingest.jsonl_bytes(values)
        inputs.append(ingest.load_predictions(None, raw_manifest, manifest, raw)[0])
        raws.append(raw)
    return manifest, raw_manifest, inputs, raws


def test_fragment_exclusion_keeps_all_displayed_readings_and_raw_votes():
    manifest, _, inputs, _ = fixture()
    primary, _, changes, networks = ingest.collate(manifest, inputs)
    row = primary["apollonius-geom.conica"][1]
    raw = networks[PAGE + ":raw-ocr"]
    assert row["text"] == raw["text"]
    assert raw["analysis_text"].startswith("γενῆ ")
    assert row["analysis_text"].startswith("τούτοις ")
    assert row["ocr_consensus"]["slots"][0]["selected"] == "γενῆ"
    assert not row["ocr_consensus"]["slots"][0]["lexical_eligible"]
    assert row["ocr_consensus"]["slots"][0]["status"] == "scan-reviewed-fragment"
    assert unapply_review(row, raw) == raw
    audit = changes[1]["decisions"][-1]
    assert audit["preceding_region"]["id"] == PRECEDING_PAGE
    assert set(audit["preceding_region"]["terminal_readings"].values()) == {"ὅμο-"}
    assert "ὁμογενῆ" not in row["text"] and "ὅμογενῆ" not in row["text"]
    wrong = deepcopy(inputs)
    wrong[0][PRECEDING_PAGE]["text"] += " προσθήκη"
    with pytest.raises(ValueError, match="preceding boundary changed"):
        ingest.collate(manifest, wrong)


def test_fragment_admission_replays_and_undoes_exact_previous_bytes(tmp_path):
    manifest, raw_manifest, inputs, raws = fixture()
    result = ingest.collate(manifest, inputs)
    work = "apollonius-geom.conica"
    (tmp_path / "data/corpus").mkdir(parents=True)
    path = tmp_path / f"data/corpus/{work}.jsonl"
    original = ingest.jsonl_bytes([{"urn": work, "locus": "4.1", "text": "πρῶτον"}])
    path.write_bytes(original)
    (tmp_path / "data/corpus_editions.json").write_bytes(ingest.encoded({work: {"n_passages": 1, "n_tokens": 1}}))
    ingest.apply(tmp_path, raw_manifest, raws, *result, "letter-fragment-test")
    archive = tmp_path / "data/corpus_changes/letter-fragment-test"
    ingest.verify(archive, tmp_path)
    row = next(row for row in ingest.records(path.read_bytes()) if row.get("scan_region_id") == PAGE)
    networks = json.loads(gzip.decompress((archive / "word-networks.json.gz").read_bytes()))
    raw = unapply_review(row, networks[PAGE + ":raw-ocr"])
    assert raw["analysis_text"].startswith("γενῆ ")
    ingest.undo(archive, tmp_path)
    assert path.read_bytes() == original
