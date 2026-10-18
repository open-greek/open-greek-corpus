import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_scan_coverage as ingest
from scan_coverage_extensions import load_extensions


def fixture(tmp_path):
    work = "apollonius-geom.conica"
    manifest = {"pages": [{"id": "conica-1", "work": work, "book": "1", "printed_page": 2,
        "source": "scan", "scan_page": 20, "region": [0, 0, 1, 1]}],
        "sources": {"scan": {"url": "https://archive.org/example.pdf", "sha256": "a" * 64}}}
    raw_manifest = ingest.encoded(manifest)
    inputs, raws = [], []
    for number, text in [(6, "λόγος καλός"), (8, "λόγοι καλός")]:
        meta = {"model": f"Qwen/Qwen3.{number}-27B", "revision": f"revision-{number}",
            "manifest_sha256": ingest.sha(raw_manifest)}
        row = {"id": "conica-1", "source": "scan", "scan_page": 20, "region": [0, 0, 1, 1],
            "finish_reason": "stop", "raw_prediction": text, "image_sha256": "b" * 64}
        raw = (json.dumps({"_meta": meta}) + "\n" + json.dumps(row, ensure_ascii=False) + "\n").encode()
        path = tmp_path / f"raw-{number}.jsonl"
        path.write_bytes(raw)
        inputs.append(ingest.load_predictions(path, raw_manifest, manifest)[0])
        raws.append(raw)
    return work, manifest, raw_manifest, inputs, raws


def test_runtime_manifest_and_truncated_regions_fail_closed(tmp_path):
    work, manifest, raw, inputs, originals = fixture(tmp_path)
    with pytest.raises(ValueError, match="different manifest"):
        ingest.load_predictions(None, b"different", manifest, originals[0])
    rows = ingest.records(originals[0])
    rows[1]["finish_reason"] = "length"
    bad = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
    with pytest.raises(ValueError, match="truncated"):
        ingest.load_predictions(None, raw, manifest, bad)
    with pytest.raises(ValueError, match="missing region"):
        ingest.collate(manifest, [inputs[0], {}])


def test_short_running_headers_are_audited_without_removing_book_titles():
    original = "ΠΑΠΠΟΥ ΣΥΝΑΓΩΓΗΣ Ζ.\nΠΑΠΠΟΥ ΑΛΕΞΑΝΔΡΕΩΣ ΣΥΝΑΓΩΓΗΣ Ζ.\nλόγος\n"
    text, changes = ingest.clean_running_headers(original, "pappus-mathematics.synagoge")
    assert text == "ΠΑΠΠΟΥ ΑΛΕΞΑΝΔΡΕΩΣ ΣΥΝΑΓΩΓΗΣ Ζ.\nλόγος\n"
    assert len(changes) == 1 and changes[0]["original_text"] == "ΠΑΠΠΟΥ ΣΥΝΑΓΩΓΗΣ Ζ.\n"
    assert ingest.clean_running_headers(original, "apollonius-geom.conica")[0] == original


def test_dio_overlap_requires_one_unambiguous_anchor():
    text, change = ingest.trim_shared_prefix("πρότερον βουληθεὶς δὲ δὴ τρόπον σφίσι χαρίσασθαι")
    assert text == "σφίσι χαρίσασθαι"
    assert change["original_text"] == "πρότερον βουληθεὶς δὲ δὴ τρόπον"
    for wrong in ["unrelated", ingest.OVERLAP_ANCHOR + " " + ingest.OVERLAP_ANCHOR]:
        with pytest.raises(ValueError, match="unique"):
            ingest.trim_shared_prefix(wrong)


def test_consensus_admission_replays_and_undoes_exact_bytes(tmp_path):
    work, manifest, raw_manifest, inputs, raw_inputs = fixture(tmp_path)
    result = ingest.collate(manifest, inputs)
    row = result[0][work][0]
    assert "⟦λόγοι ∥ λόγος⟧" in row["text"]
    assert row["analysis_text"] == "καλός"
    root = tmp_path / "repo"
    (root / "data/corpus").mkdir(parents=True)
    before_row = {"urn": work, "locus": "4.1", "text": "πρῶτον", "source": "first1k", "edition": "1st1K-grc1"}
    before = (json.dumps(before_row, ensure_ascii=False) + "\n").encode()
    (root / f"data/corpus/{work}.jsonl").write_bytes(before)
    editions = ingest.encoded({work: {"source": "first1k", "n_passages": 1, "n_tokens": 1}})
    (root / "data/corpus_editions.json").write_bytes(editions)
    ingest.apply(root, raw_manifest, raw_inputs, *result, "scan-coverage-test")
    audit = root / "data/corpus_changes/scan-coverage-test"
    ingest.verify(audit, root)
    current = ingest.records((root / f"data/corpus/{work}.jsonl").read_bytes())
    assert current[-1] == before_row and current[0]["locus"] == "1.heiberg-p0002"
    assert load_extensions(root, work, ["4.1"], [before_row]) == [row]
    with pytest.raises(ValueError, match="base edition changed"):
        load_extensions(root, work, ["4.1"], [dict(before_row, text="changed")])
    ingest.undo(audit, root)
    assert (root / f"data/corpus/{work}.jsonl").read_bytes() == before
    assert (root / "data/corpus_editions.json").read_bytes() == editions
    assert not (root / ingest.EXTENSION_INDEX).exists()
    assert gzip.decompress((audit / "witness-1.jsonl.gz").read_bytes()) == raw_inputs[0]


def test_comparative_dio_regions_cannot_become_primary(tmp_path):
    work, manifest, raw, inputs, originals = fixture(tmp_path)
    page = manifest["pages"][0]
    page.update(work="cassius-dio.historiae-romanae", source_volume=1,
        printed_page=2, panel_role="comparison", admission="comparative-paratext",
        transmission="comparative-quotation")
    primary, paratext, audits, networks = ingest.collate(manifest, inputs)
    assert primary == {} and len(paratext) == 1
    assert paratext[0]["kind"] == "comparative-quotation"
    assert paratext[0]["locus"] == "cary-v1-p0002-comparison"
