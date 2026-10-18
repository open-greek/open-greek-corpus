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


def test_dio_English_running_title_removal_is_initial_and_source_guarded():
    page = {"id": "dio-cary-v9-pdf0179", "source_volume": 9}
    source = {"sha256": "f71fb53d3b4fa4894947148f7fdf018739c746b3d413c9ba179176b17cb70db4"}
    text = "DIO'S ROMAN HISTORY\nZonaras 9, 27.\nἄνθρωπος\nDIO'S ROMAN HISTORY\n"
    body, decisions = ingest.clean_running_headers(text, "cassius-dio.historiae-romanae", page, source)
    assert body == "Zonaras 9, 27.\nἄνθρωπος\nDIO'S ROMAN HISTORY\n"
    assert decisions[0]["offset"] == 0
    assert decisions[0]["original_text"] + body == text
    assert ingest.clean_running_headers(text, "cassius-dio.historiae-romanae", page, {"sha256": "changed"}) == (text, [])
    assert ingest.clean_running_headers(text, "pappus-mathematics.synagoge", page, source) == (text, [])


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
    assert dio["reviewed_comparative_regions"] == 419
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


def reviewed_crop_bundle(manifest, original_raw, old_prediction, new_prediction):
    from copy import deepcopy
    from scan_ocr_bundle import retained
    old_rows = ingest.records(old_prediction)
    old_rows[0]["_meta"].update(runtime={"name": "fixture"}, runner_sha256="d" * 64)
    old_prediction = ingest.jsonl_bytes(old_rows)
    effective = deepcopy(manifest)
    page = effective["pages"][0]
    page["region"] = [0, 0, 1, .8]
    decision = {"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
        "original_region": [0, 0, 1, 1], "region": page["region"]}
    review = {"kind": "scan-region-body-review", "reviewed_at": "2026-10-18",
        "original_manifest_sha256": ingest.sha(original_raw), "sources": manifest["sources"],
        "evidence": {"body": {**decision, "source_pdf_sha256": "a" * 64,
            "contact_sheet_sha256": "c" * 64, "reviewed_at": "2026-10-18", "evidence": "Checked body above notes."}}}
    review_raw = ingest.encoded(review)
    effective["reviewed_substitutions"] = {"original_manifest_sha256": ingest.sha(original_raw),
        "source_review": {"path": "review.json", "sha256": ingest.sha(review_raw)},
        "regions": [{**decision, "evidence_id": "body"}]}
    effective_raw = ingest.encoded(effective)
    new_rows = ingest.records(new_prediction)
    new_rows[0]["_meta"].update(runtime={"name": "fixture"}, runner_sha256="d" * 64)
    new_rows[0]["_meta"]["manifest_sha256"] = ingest.sha(effective_raw)
    new_rows[1]["region"] = page["region"]
    new_raw = ingest.jsonl_bytes(new_rows)
    bundle = ingest.encoded({"kind": "scan-ocr-bundle", "schema_version": 1,
        "effective_manifest": retained(effective_raw), "source_reviews": [retained(review_raw)],
        "parts": [{"prediction": retained(raw), "manifest": retained(request)}
            for raw, request in [(old_prediction, original_raw), (new_raw, effective_raw)]]})
    return bundle, effective_raw, effective, new_raw


def test_bundle_preserves_failed_superseded_attempt_and_original_artifact_hash(tmp_path):
    _, manifest, original_raw, _, raws = fixture(tmp_path)
    rows = ingest.records(raws[0])
    rows[1].update(finish_reason="length", raw_prediction="")
    old_raw = ingest.jsonl_bytes(rows)
    bundle, effective_raw, effective, new_raw = reviewed_crop_bundle(manifest, original_raw, old_raw, raws[0])
    predictions, retained = ingest.load_predictions(None, effective_raw, effective, bundle)
    direct, _ = ingest.load_predictions(None, effective_raw, effective, new_raw)
    assert retained == bundle and predictions == direct
    audit = ingest.prediction_bundle_audit(bundle, effective_raw)
    assert len(audit["held_predictions"]) == 1 and len(audit["parts"]) == 2
    assert audit["held_predictions"][0]["original_region"] == [0, 0, 1, 1]


def test_bundle_never_admits_failed_effective_crop_or_forged_review(tmp_path):
    _, manifest, original_raw, _, raws = fixture(tmp_path)
    rows = ingest.records(raws[0])
    rows[1]["finish_reason"] = "length"
    failed = ingest.jsonl_bytes(rows)
    bundle, effective_raw, effective, _ = reviewed_crop_bundle(manifest, original_raw, raws[0], failed)
    with pytest.raises(ValueError, match="truncated"):
        ingest.load_predictions(None, effective_raw, effective, bundle)
    bundle, effective_raw, effective, _ = reviewed_crop_bundle(manifest, original_raw, raws[0], raws[0])
    forged = json.loads(bundle)
    forged["source_reviews"] = []
    with pytest.raises(ValueError, match="retained source review"):
        ingest.load_predictions(None, effective_raw, effective, ingest.encoded(forged))


def test_exact_private_failure_scope_reaches_retained_bundle_leaf_without_rewriting(tmp_path):
    _, manifest, original_raw, _, raws = fixture(tmp_path)
    rows = ingest.records(raws[0])
    rows[1]["finish_reason"] = "length"
    failed = ingest.jsonl_bytes(rows)
    bundle, effective_raw, effective, new_raw = reviewed_crop_bundle(manifest, original_raw, raws[0], failed)
    with pytest.raises(ValueError, match="truncated"):
        ingest.load_predictions(None, effective_raw, effective, bundle)
    allowed = frozenset({"conica-1"})
    loaded, retained = ingest.load_predictions(None, effective_raw, effective, bundle, allow_failed_ids=allowed)
    direct, _ = ingest.load_predictions(None, effective_raw, effective, new_raw, allow_failed_ids=allowed)
    assert retained == bundle and loaded == direct
    assert loaded["conica-1"]["text"] == rows[1]["raw_prediction"]
    with pytest.raises(ValueError, match="truncated"):
        ingest.load_predictions(None, effective_raw, effective, bundle, allow_failed_ids={"different-id"})


def test_conica_running_header_removal_is_source_page_and_initial_position_guarded():
    manifest = json.loads((ROOT / "data/ingest_reviews/coverage/mathematical-ocr-jobs.json").read_text())
    page = next(p for p in manifest["pages"] if p["id"] == "apolloniipergaei01apoluoft-pdf0208")
    source = manifest["sources"][page["source"]]
    original = "ΚΩΝΙΚΩΝ α'.\nἡ μὲν ΑΓ\nΚΩΝΙΚΩΝ α'.\n"
    body, edits = ingest.clean_running_headers(original, page["work"], page, source)
    assert body == "ἡ μὲν ΑΓ\nΚΩΝΙΚΩΝ α'.\n" and len(edits) == 1
    assert edits[0]["original_text"] + body == original
    assert edits[0]["source_pdf_sha256"] == source["sha256"]
    assert edits[0]["image_sha256"] == "f654f53f09e6ecbc5118465b7b41129c569e32ac3d9a18d38408379d9d814406"
    for changed_page, changed_source in [(dict(page, scan_page=206), source),
            (page, dict(source, sha256="different")), (dict(page, region=[0, .1, 1, 1]), source)]:
        assert ingest.clean_running_headers(original, page["work"], changed_page, changed_source)[0] == original


def test_comparison_only_admission_registers_paratext_without_primary_rows_and_undoes(tmp_path):
    _, manifest, _, _, old_raws = fixture(tmp_path)
    work = "cassius-dio.historiae-romanae"
    page = manifest["pages"][0]
    page.update(id="dio-cary-v9-pdf0240-comparison", work=work, source_volume=9,
        scan_page=240, printed_page=470, region=[.095, .615, .43, .88],
        panel_role="comparison", transmission="comparative-quotation", admission="comparative-paratext")
    request_raw = ingest.encoded(manifest)
    raws, inputs = [], []
    for raw in old_raws:
        rows = ingest.records(raw)
        rows[0]["_meta"]["manifest_sha256"] = ingest.sha(request_raw)
        rows[1].update(id=page["id"], scan_page=240, region=page["region"])
        value = ingest.jsonl_bytes(rows)
        raws.append(value)
        inputs.append(ingest.load_predictions(None, request_raw, manifest, value)[0])
    result = ingest.collate(manifest, inputs)
    assert result[0] == {} and len(result[1]) == 1
    root = tmp_path / "repo"
    directory = root / "data/ingest_reviews/coverage"
    directory.mkdir(parents=True)
    for name in ["cassius-dio-reviewed-ocr-jobs.json", "cassius-dio-late-comparison-jobs.json"]:
        (directory / name).write_bytes((ROOT / "data/ingest_reviews/coverage" / name).read_bytes())
    editions = ingest.encoded({work: {"n_passages": 0, "n_tokens": 0}})
    (root / "data/corpus_editions.json").write_bytes(editions)
    ingest.apply(root, request_raw, raws, *result, "separate-comparison")
    audit = root / "data/corpus_changes/separate-comparison"
    ingest.verify(audit, root)
    index = json.loads((root / ingest.EXTENSION_INDEX).read_text())
    assert index["works"] == {}
    assert index["comparative_admissions"][work][0]["regions"] == [page["id"]]
    scope = coverage_scope(root, work)
    assert scope["admitted_primary_regions"] == 0
    assert scope["admitted_comparative_regions"] == 1
    assert scope["remaining_reviewed_comparative_regions"] == 418
    assert scope["comparative_admission_audits"] == ["data/corpus_changes/separate-comparison/changes.json"]
    assert not (root / f"data/corpus/{work}.jsonl").exists()
    ingest.undo(audit, root)
    assert not (root / ingest.EXTENSION_INDEX).exists()
    assert (root / "data/corpus_editions.json").read_bytes() == editions
