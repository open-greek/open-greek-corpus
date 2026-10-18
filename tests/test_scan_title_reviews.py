from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scan_title_reviews import reviewed_title, unapply_review, PAGE, SOURCE_SHA256, IMAGE_SHA256, TITLE
from ocr_consensus import merge_witnesses, compact_corpus_consensus, restore_corpus_consensus


def test_reviewed_stigma_does_not_rewrite_or_reattribute_original_ocr_votes():
    text = TITLE + " ζ. Περιέχει δὲ ἀποριῶν λύσεις."
    witnesses = [{"id": str(number), "vote_group": str(number), "text": text,
                  "artifact_sha256": str(number), "image_sha256": IMAGE_SHA256} for number in (6, 8)]
    raw = merge_witnesses(witnesses)
    before = deepcopy(raw)
    page = {"id": PAGE, "work": "pappus-mathematics.synagoge", "book": "6", "scan_page": 17, "region": [0, 0, 1, 1]}
    source = {"url": "https://archive.org/source.pdf", "sha256": SOURCE_SHA256}
    path = "data/corpus_changes/test/word-networks.json.gz"
    corrected, archived, audit = reviewed_title(raw, page, source, witnesses, path)
    assert raw == before and archived[1] == before
    assert corrected["text"].startswith(TITLE + " Ϛ.")
    assert corrected["ocr_consensus"]["slots"][3]["status"] == "scan-reviewed"
    assert corrected["ocr_consensus"]["slots"][3]["readings"] == raw["ocr_consensus"]["slots"][3]["readings"]
    assert all(value["text"].startswith(TITLE + " ζ.") for value in corrected["ocr_consensus"]["witnesses"])
    assert audit["original_predictions"] == {"6": text, "8": text}
    assert audit["source"]["image_sha256"] == [IMAGE_SHA256]
    compact = compact_corpus_consensus(corrected, {"path": path, "key": PAGE})
    assert restore_corpus_consensus(compact, corrected) == corrected
    assert unapply_review(compact, archived[1]) == before
    with pytest.raises(ValueError, match="original OCR network"):
        unapply_review(compact, dict(before, text="ἄλλο"))
    with pytest.raises(ValueError, match="image region changed"):
        reviewed_title(raw, page, source, [dict(witnesses[0], image_sha256="b" * 64)], path)


def test_scan_review_admission_replays_and_recovers_raw_title(tmp_path):
    import ingest_scan_coverage as ingest
    work = "pappus-mathematics.synagoge"
    page = {"id": PAGE, "work": work, "book": "6", "printed_page": 474,
            "source": "scan", "scan_page": 17, "region": [0, 0, 1, 1]}
    manifest = {"prompt": "Transcribe Greek body only.", "pages": [page],
        "sources": {"scan": {"url": "https://archive.org/source.pdf", "sha256": SOURCE_SHA256}}}
    raw_manifest = ingest.encoded(manifest)
    inputs, raws = [], []
    for number in (6, 8):
        values = [{"_meta": {"model": f"Qwen/Qwen3.{number}-27B", "revision": str(number),
            "manifest_sha256": ingest.sha(raw_manifest), "prompt": manifest["prompt"]}},
            {"id": PAGE, "source": "scan", "scan_page": 17, "region": [0, 0, 1, 1],
            "finish_reason": "stop", "raw_prediction": TITLE + " ζ. Περιέχει δὲ λύσεις.",
            "image_sha256": IMAGE_SHA256, "prompt_sha256": ingest.sha(manifest["prompt"].encode())}]
        raw = ingest.jsonl_bytes(values)
        inputs.append(ingest.load_predictions(None, raw_manifest, manifest, raw)[0])
        raws.append(raw)
    result = ingest.collate(manifest, inputs)
    root = tmp_path / "repo"
    (root / "data/corpus").mkdir(parents=True)
    path = root / f"data/corpus/{work}.jsonl"
    original = ingest.jsonl_bytes([{"urn": work, "locus": "2.1", "text": "πρῶτον"}])
    path.write_bytes(original)
    (root / "data/corpus_editions.json").write_bytes(ingest.encoded({work: {"n_passages": 1, "n_tokens": 1}}))
    ingest.apply(root, raw_manifest, raws, *result, "pappus-title-test")
    archive = root / "data/corpus_changes/pappus-title-test"
    ingest.verify(archive, root)
    row = ingest.records(path.read_bytes())[-1]
    networks = json.loads(gzip.decompress((archive / "word-networks.json.gz").read_bytes()))
    reference = row["ocr_consensus"]["raw_ocr_network"]
    assert reference["path"] == "data/corpus_changes/pappus-title-test/word-networks.json.gz"
    raw = unapply_review(row, networks[reference["key"]])
    assert raw["text"].startswith(TITLE + " ζ.")
    assert row["text"].startswith(TITLE + " Ϛ.")
    assert row["correction_sources"] == ["pappus-vi-opening-stigma-2026-10-18"]
    ingest.undo(archive, root)
    assert path.read_bytes() == original
