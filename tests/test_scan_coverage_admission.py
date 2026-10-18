import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_scan_coverage as ingest
from scan_coverage_extensions import load_extensions, coverage_scope


def fixture(tmp_path):
    work = "apollonius-geom.conica"
    manifest = {"prompt": "Transcribe Greek body only.", "pages": [{"id": "conica-1", "work": work, "book": "1", "printed_page": 2,
        "source": "scan", "scan_page": 20, "region": [0, 0, 1, 1]}],
        "sources": {"scan": {"url": "https://archive.org/example.pdf", "sha256": "a" * 64}}}
    raw_manifest = ingest.encoded(manifest)
    inputs, raws = [], []
    for number, text in [(6, "λόγος καλός"), (8, "λόγοι καλός")]:
        meta = {"model": f"Qwen/Qwen3.{number}-27B", "revision": f"revision-{number}",
            "manifest_sha256": ingest.sha(raw_manifest), "prompt": manifest["prompt"]}
        row = {"id": "conica-1", "source": "scan", "scan_page": 20, "region": [0, 0, 1, 1],
            "finish_reason": "stop", "raw_prediction": text, "image_sha256": "b" * 64,
            "prompt_sha256": ingest.sha(manifest["prompt"].encode())}
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
    rows[1]["finish_reason"] = "stop"
    rows[1]["prompt_sha256"] = "c" * 64
    wrong_prompt = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
    with pytest.raises(ValueError, match="region prompt"):
        ingest.load_predictions(None, raw, manifest, wrong_prompt)


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


def test_dio_overlap_archives_all_variants_without_replacing_old_readings(tmp_path):
    work = "cassius-dio.historiae-romanae"
    (tmp_path / "data/corpus").mkdir(parents=True)
    rows = [{"urn": work, "locus": "55.9.2", "text": "πρότερον ἐν τῇ πόλει"},
            {"urn": work, "locus": "55.9.3", "text": "λόγος δίκαιος"},
            {"urn": work, "locus": "55.9.4", "text": ingest.OVERLAP_ANCHOR}]
    raw = ("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode()
    path = tmp_path / f"data/corpus/{work}.jsonl"
    path.write_bytes(raw)
    manifest = {"pages": [{"id": "overlap", "work": work, "overlap": {"served_through": "55.9.4"}}]}
    inputs = [{"overlap": {"id": str(i), "vote_group": str(i), "artifact_sha256": str(i),
              "text": "πόλει λόγος δίκαιος " + ingest.OVERLAP_ANCHOR + " νέα λέξις"}} for i in (1, 2)]
    comparison = ingest.collate_overlaps(manifest, inputs, tmp_path)["overlap"]
    assert len(comparison["consensus"]["ocr_consensus"]["witnesses"]) == 3
    assert all("νέα λέξις" not in value["original_text"] for value in comparison["prefix_decisions"])
    assert path.read_bytes() == raw and comparison["existing_passages"] == rows


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
    from ocr_consensus import restore_corpus_consensus
    compact = {key: row[key] for key in ("text", "analysis_text", "ocr_consensus")}
    network = json.loads(gzip.decompress((audit / "word-networks.json.gz").read_bytes()))[row["scan_region_id"]]
    assert restore_corpus_consensus(compact, network) == result[3][row["scan_region_id"]]
    assert row["ocr_consensus"]["full_network"]["path"] == "data/corpus_changes/scan-coverage-test/word-networks.json.gz"
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


def test_additive_preface_consolidation_preserves_prior_rows_and_replays_both_audits(tmp_path):
    work, manifest, raw_manifest, inputs, raw_inputs = fixture(tmp_path)
    root = tmp_path / "repo"
    (root / "data/corpus").mkdir(parents=True)
    base_row = {"urn": work, "locus": "4.1", "text": "πρῶτον", "source": "first1k", "edition": "1st1K-grc1"}
    base = ingest.jsonl_bytes([base_row])
    corpus = root / f"data/corpus/{work}.jsonl"
    corpus.write_bytes(base)
    (root / "data/corpus_editions.json").write_bytes(ingest.encoded({work: {"n_passages": 1, "n_tokens": 1}}))
    first_result = ingest.collate(manifest, inputs)
    ingest.apply(root, raw_manifest, raw_inputs, *first_result, "first-books")
    first_bytes = corpus.read_bytes()
    first_row = first_result[0][work][0].copy()
    page = manifest["pages"][0]
    page.update(id="letter4", book="4", printed_page=2, scan_page=94, text_role="authorial-preface")
    letter_manifest = ingest.encoded(manifest)
    letter_inputs, letter_raw = [], []
    for raw in raw_inputs:
        values = ingest.records(raw)
        values[0]["_meta"]["manifest_sha256"] = ingest.sha(letter_manifest)
        values[1].update(id="letter4", scan_page=94)
        blob = ingest.jsonl_bytes(values)
        letter_raw.append(blob)
        letter_inputs.append(ingest.load_predictions(None, letter_manifest, manifest, blob)[0])
    result = ingest.collate(manifest, letter_inputs)
    ingest.apply(root, letter_manifest, letter_raw, *result, "book-four-letter")
    first_audit = root / "data/corpus_changes/first-books"
    letter_audit = root / "data/corpus_changes/book-four-letter"
    ingest.verify(first_audit, root)
    ingest.verify(letter_audit, root)
    current = ingest.records(corpus.read_bytes())
    assert [row["locus"] for row in current] == ["1.heiberg-p0002", "4.heiberg-p0002", "4.1"]
    assert current[0] == first_row and current[-1] == base_row
    extension = json.loads((root / ingest.EXTENSION_INDEX).read_text())["works"][work]
    assert len(extension["audits"]) == 2
    assert len(load_extensions(root, work, ["4.1"], [base_row])) == 2
    with pytest.raises(ValueError, match="Output changed"):
        ingest.undo(first_audit, root)
    ingest.undo(letter_audit, root)
    assert corpus.read_bytes() == first_bytes
    ingest.verify(first_audit, root)
    ingest.undo(first_audit, root)
    assert corpus.read_bytes() == base


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


def test_public_scope_counts_admissions_without_claiming_intact_works():
    pappus = coverage_scope(ROOT, "pappus-mathematics.synagoge")
    conica = coverage_scope(ROOT, "apollonius-geom.conica")
    dio = coverage_scope(ROOT, "cassius-dio.historiae-romanae")
    assert pappus["reviewed_primary_regions"] == 331
    assert conica["reviewed_primary_regions"] == 227
    assert dio["reviewed_primary_regions"] == 1082
    assert dio["reviewed_comparative_regions"] == 418
    assert dio["admitted_primary_regions"] + dio["remaining_reviewed_primary_regions"] == 1082
    assert "eighty-book" in dio["work_identity"] and "not an intact" in dio["transmission_limit"]
    assert "Books I–IV" in conica["transmission_limit"]
    assert coverage_scope(ROOT, "unrelated.work") is None


def test_bounded_digital_comparison_votes_with_attribution_but_footer_does_not(tmp_path):
    work, manifest, raw, inputs, originals = fixture(tmp_path)
    body = "Ἄνθρωπος ἀγαθὸς καὶ δίκαιος ἀεί ποτε λέγει λόγους καθαροὺς ἐν ἀγορᾷ παρὰ φίλοις ἀληθινούς."
    for source in inputs:
        source["conica-1"]["text"] = body
    manifest["pages"][0].update(work="cassius-dio.historiae-romanae", source_volume=7)
    comparison = {"id": "source-library:page20", "source_id": "source-library", "vote_group": "library",
        "text": body + "\nλόγους] λέξεις Μ. ἀπαράδεκτος ὁ ἀριθμός", "artifact_sha256": "c" * 64}
    digital = {"pages": {(7, 20): comparison}, "sources": {"source-library": {
        "id": "source-library", "license": "CC-BY-SA-4.0", "attribution": "Source Library"}}}
    primary, paratext, audits, networks = ingest.collate(manifest, inputs, digital=digital)
    row = primary["cassius-dio.historiae-romanae"][0]
    assert row["license"] == "CC-BY-SA-4.0" and row["component_attribution"][0]["attribution"] == "Source Library"
    assert "ἀπαράδεκτος" not in row["analysis_text"]
    assert len(row["ocr_consensus"]["witnesses"]) == 3
    assert audits[0]["decisions"][-1]["removed_footer"].startswith("\nλόγους]")
    comparison["text"] = "ἄλλο ἔργον"
    primary, _, audits, _ = ingest.collate(manifest, inputs, digital=digital)
    row = primary["cassius-dio.historiae-romanae"][0]
    assert row["license"] == "PD" and "component_attribution" not in row
    assert len(row["ocr_consensus"]["witnesses"]) == 2
    assert audits[0]["decisions"][-1]["status"] == "held-comparison-only"


def test_digital_source_admission_replays_original_exports_and_body_windows(tmp_path, monkeypatch):
    import dio_comparison_witnesses as comparison
    work, manifest, raw, inputs, originals = fixture(tmp_path)
    work = "cassius-dio.historiae-romanae"
    manifest["pages"][0].update(work=work, source_volume=7)
    raw = ingest.encoded(manifest)
    body = "Ἄνθρωπος ἀγαθὸς καὶ δίκαιος ἀεί ποτε λέγει λόγους καθαροὺς ἐν ἀγορᾷ παρὰ φίλοις ἀληθινούς."
    raw_inputs, inputs = [], []
    for original in originals:
        values = ingest.records(original)
        values[0]["_meta"]["manifest_sha256"] = ingest.sha(raw)
        values[1]["raw_prediction"] = body
        blob = ("\n".join(json.dumps(value, ensure_ascii=False) for value in values) + "\n").encode()
        raw_inputs.append(blob)
        inputs.append(ingest.load_predictions(None, raw, manifest, blob)[0])
    document = {"id": "tlg0385.tlg001.local003", "origin": {"id": "source-library"},
        "license": {"url": comparison.LICENSE_URL}, "sourceCitation": "Cary VII, book123",
        "sourceRights": "Public-domain print; CC BY-SA 4.0 transcription", "revisionDate": "2026-10-07",
        "sections": [{"id": "section20", "label": "Page s20", "children": [],
                      "blocks": [{"type": "paragraph", "text": body + "\nλόγους] λέξεις Μ."}]}]}
    source_raw = json.dumps(document, ensure_ascii=False).encode()
    monkeypatch.setattr(comparison, "PINS", {document["id"]: {"volume": 7, "book": "book123",
        "json_sha256": ingest.sha(source_raw)}})
    digital = comparison.load(blobs=[source_raw])
    result = ingest.collate(manifest, inputs, digital=digital)
    root = tmp_path / "repo"
    (root / "data/corpus").mkdir(parents=True)
    base = (json.dumps({"urn": work, "locus": "36.1.1", "text": "πρῶτον", "source": "perseus", "edition": "grc2"}) + "\n").encode()
    (root / f"data/corpus/{work}.jsonl").write_bytes(base)
    (root / "data/corpus_editions.json").write_bytes(ingest.encoded({work: {"n_passages": 1, "n_tokens": 1}}))
    ingest.apply(root, raw, raw_inputs, *result, "dio-digital-test", digital=digital)
    archive = root / "data/corpus_changes/dio-digital-test"
    ingest.verify(archive, root)
    audit = json.loads((archive / "changes.json").read_text())
    assert audit["digital_comparison_counts"] == {"bounded-body-voting-witness": 1}
    assert gzip.decompress((archive / ("digital-" + document["id"] + ".json.gz")).read_bytes()) == source_raw
    ingest.undo(archive, root)
    assert (root / f"data/corpus/{work}.jsonl").read_bytes() == base
