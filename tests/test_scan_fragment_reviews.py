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


def test_generic_same_book_boundary_replays_without_changing_the_letter_audit(tmp_path):
    manifest, _, _, raws = fixture()
    for number, page in enumerate(manifest["pages"]):
        page.update(id=f"conica-body-{number}", book="1", printed_page=10 + 2 * number, scan_page=28 + 2 * number)
        page.pop("text_role")
    raw_manifest = ingest.encoded(manifest)
    inputs, modified_raws = [], []
    for raw in raws:
        values = ingest.records(raw)
        values[0]["_meta"]["manifest_sha256"] = ingest.sha(raw_manifest)
        for row, page in zip(values[1:], manifest["pages"]):
            row.update({key: page[key] for key in ("id", "scan_page")})
        blob = ingest.jsonl_bytes(values)
        inputs.append(ingest.load_predictions(None, raw_manifest, manifest, blob)[0])
        modified_raws.append(blob)
    result = ingest.collate(manifest, inputs)
    rows = result[0]["apollonius-geom.conica"]
    assert rows[0]["text"].endswith("ὅμο-") and not rows[0]["ocr_consensus"]["slots"][-1]["lexical_eligible"]
    assert rows[1]["text"].startswith("γενῆ ") and not rows[1]["ocr_consensus"]["slots"][0]["lexical_eligible"]
    assert rows[1]["corrections"] == ["structural"]
    assert rows[1]["ocr_consensus"]["slots"][0]["status"] == "continuation-fragment"
    work = "apollonius-geom.conica"
    (tmp_path / "data/corpus").mkdir(parents=True)
    path = tmp_path / f"data/corpus/{work}.jsonl"
    original = ingest.jsonl_bytes([{"urn": work, "locus": "4.1", "text": "πρῶτον"}])
    path.write_bytes(original)
    (tmp_path / "data/corpus_editions.json").write_bytes(ingest.encoded({work: {"n_passages": 1, "n_tokens": 1}}))
    ingest.apply(tmp_path, raw_manifest, modified_raws, *result, "body-fragment-test")
    archive = tmp_path / "data/corpus_changes/body-fragment-test"
    ingest.verify(archive, tmp_path)
    ingest.undo(archive, tmp_path)
    assert path.read_bytes() == original
    # A book boundary cannot establish an incomplete word across the transition.
    manifest["pages"][1]["book"] = "2"
    rows = ingest.collate(manifest, inputs)[0][work]
    assert rows[1]["analysis_text"].startswith("γενῆ ")
    manifest["pages"][1]["book"] = "1"
    for values in inputs:
        values["conica-body-1"]["text"] = "ΚΩΝΙΚΩΝ γενῆ τούτοις"
    rows = ingest.collate(manifest, inputs)[0][work]
    assert "correction_sources" not in rows[1]
