import copy
import hashlib
import json
from pathlib import Path
import sys
import unicodedata

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import report_polytonic_loss as report


def strip_marks(text):
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def test_mark_counts_normalize_unicode_without_counting_spacing_breathings():
    text = "ἄνθρωπος ἐστὶν ἀγαθός. " * 30
    result = report.detect(text)
    assert result == report.detect(unicodedata.normalize("NFD", text))
    assert result["applicable"] and not result["flag"]
    assert result["accented_letters"] == 90
    assert result["breathing_letters"] == 90
    assert len(report.greek_letters("᾿ ῾ .\u0313ἄ")) == 1
    damaged = report.detect(strip_marks(text))
    assert damaged["flag"]
    assert damaged["reasons"] == ["low-accented-letter-rate", "low-breathing-letter-rate"]


def test_sparse_and_uppercase_pages_require_review_instead_of_a_loss_claim():
    assert not report.detect("ἄνθρωπος")["applicable"]
    assert not report.detect("ΑΝΘΡΩΠΟΣ " * 50)["applicable"]
    assert report.detect("Latin only " * 100)["accented_letter_rate"] is None


def test_reference_alignment_distinguishes_loss_from_wrong_mark_type():
    gold = "ἄνθρωπος ἐστὶν ἀγαθός. " * 30
    loss = report.truth_label(gold, strip_marks(gold))
    assert loss["assessable"] and loss["systematic_loss"]
    assert loss["base_text_recall"] == 1
    assert loss["loss_classes"] == ["accent", "breathing"]
    wrong_accent = gold.replace("ἄ", "ἂ").replace("ός", "ὸς")
    marked = report.truth_label(gold, wrong_accent)
    assert marked["assessable"] and not marked["systematic_loss"]
    assert marked["classes"]["accent"]["mark_presence_recall"] == 1
    assert marked["classes"]["accent"]["exact_marks_retained"] < 90
    assert not report.truth_label(gold, "άσχετον " * 5)["assessable"]


def test_operating_limits_include_intentional_monotonic_and_dense_reference_marks():
    monotonic = "άνθρωπος είναι καλός " * 35
    assert report.detect(monotonic)["flag"]  # no breathings, possibly intentional
    assert not report.truth_label(monotonic, monotonic)["systematic_loss"]
    gold = "ἄ " * 300
    prediction = "α " * 180 + "ἄ " * 120
    assert report.truth_label(gold, prediction)["systematic_loss"]
    assert not report.detect(prediction)["flag"]  # absolute-rate blind spot is explicit


def test_previous_physical_ids_normalize_prefixes_paths_and_leading_zeros():
    assert report.physical_key("PG_145-328") == report.physical_key("dir/grc_tlg_mpg0145-0328")
    assert report.physical_key("dir/grc_grna_or_0419") == report.physical_key("grc_grna_or_419")
    assert report.physical_key("PG_145-328") != report.physical_key("PG_144-328")
    first = {"physical_refs": {"scan_page": 13, "scan_sha256": "volume-one"}}
    second = {"physical_refs": {"scan_page": 13, "scan_sha256": "volume-two"}}
    assert report.page_identity(first) != report.page_identity(second)
    assert report.page_identity({"source_location": {"scan_page": 13, "source": "pg74", "region": [.5, 0, 1, 1]}})[1] == "explicit-source-region"


def fixture(tmp_path):
    gold = "ἄνθρωπος ἐστὶν ἀγαθός. " * 30
    pages = []
    for n in range(60):
        identity = f"fresh-{n}"
        xml = tmp_path / (identity + ".xml")
        xml.write_text('<PcGts xmlns="urn:test"><Page imageFilename="' + identity + '.jpg"><TextRegion><TextLine><TextEquiv><Unicode>' + gold + '</Unicode></TextEquiv></TextLine></TextRegion></Page></PcGts>')
        image = tmp_path / (identity + ".jpg");image.write_bytes(b"pinned test image " + str(n).encode())
        page = {"id": identity, "xml": xml.name, "image": image.name,
                "xml_sha256": report.benchmark.sha256(xml), "image_sha256": report.benchmark.sha256(image),
                "gold_sha256": hashlib.sha256(gold.strip().encode()).hexdigest(),
                "split": "calibration" if n < 20 else "test", "volume": "fixture"}
        pages.append(page)
    policy = tmp_path / "policy.json";policy.write_bytes(report.dump(report.POLICY))
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(report.dump({"policy_sha256": report.benchmark.sha256(policy), "pages": pages}))
    review = tmp_path / "review.json"
    review.write_bytes(report.dump({"manifest_sha256": report.benchmark.sha256(manifest),
                                   "pages": [{"id": p["id"], "scan_reviewed": True,
                                       "reference_order": "verified", "reference_coverage": "verified",
                                       **{key: p[key] for key in ("image_sha256", "xml_sha256", "gold_sha256")}} for p in pages]}))
    prediction = tmp_path / "predictions.jsonl"
    metadata = {"model": "fixture", "revision": "pinned-fixture", "prompt": report.benchmark.PROMPT,
                "manifest_sha256": report.benchmark.sha256(manifest)}
    rows = [{"id": p["id"], "split": p["split"], "volume": p["volume"], "raw_prediction": strip_marks(gold), "finish_reason": "stop"} for p in pages]
    rows[-1].update({"raw_prediction": "", "finish_reason": "error"})
    prediction.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [{"_meta": metadata}, *rows]) + "\n")
    return manifest, policy, review, prediction


def test_fresh_validation_keeps_failures_and_separates_held_out_results(tmp_path):
    manifest, policy, review, prediction = fixture(tmp_path)
    result = report.validate_fresh(tmp_path, manifest, policy, [prediction], review)
    run = result["runs"][0]
    assert result["scan_review_complete"]
    assert result["selection_rule"] is None
    assert run["by_split"]["calibration"]["true_positive"] == 20
    assert run["by_split"]["test"]["true_positive"] == 39
    assert run["by_split"]["test"]["failed_or_truncated"] == 1
    assert run["by_split"]["test"]["unassessable"] == 1
    assert run["pages"][-1]["raw_prediction"] == ""
    assert run["unassessable_pages"] == ["fresh-59"]
    assert report.validate_fresh(tmp_path, manifest, policy, [prediction], review) == result


def test_source_order_disagreement_is_reported_instead_of_labeled_loss(tmp_path):
    manifest, policy, review, prediction = fixture(tmp_path)
    doc = json.loads(review.read_text());doc["pages"][0]["reference_order"] = "source-order-mismatch"
    review.write_bytes(report.dump(doc))
    result = report.validate_fresh(tmp_path, manifest, policy, [prediction], review)
    assert result["runs"][0]["pages"][0]["truth"]["label"] == "reference-order-review-required"
    doc["pages"][0]["reference_order"] = "verified"
    doc["pages"][0]["reference_coverage"] = "partial"
    review.write_bytes(report.dump(doc))
    result = report.validate_fresh(tmp_path, manifest, policy, [prediction], review)
    assert result["runs"][0]["pages"][0]["truth"]["label"] == "reference-coverage-review-required"
    doc["pages"][0]["image_sha256"] = "changed"
    review.write_bytes(report.dump(doc))
    with pytest.raises(ValueError, match="Scan-review source hashes"):
        report.validate_fresh(tmp_path, manifest, policy, [prediction], review)


def test_changed_policy_source_and_duplicate_predictions_are_rejected(tmp_path):
    manifest, policy, review, prediction = fixture(tmp_path)
    changed = json.loads(policy.read_text());changed["detector"]["minimum_accented_letter_rate"] = .07
    policy.write_bytes(report.dump(changed))
    with pytest.raises(ValueError, match="locked"):
        report.validate_fresh(tmp_path, manifest, policy, [prediction], review)
    policy.write_bytes(report.dump(report.POLICY))
    rows = prediction.read_text().splitlines();rows.append(rows[-1]);prediction.write_text("\n".join(rows) + "\n")
    with pytest.raises(ValueError, match="Repeated page"):
        report.validate_fresh(tmp_path, manifest, policy, [prediction], review)


def test_corpus_report_scores_separate_raw_witnesses_without_counting_tie_display(tmp_path):
    corpus = tmp_path / "corpus";corpus.mkdir()
    good = "ἄνθρωπος ἐστὶν ἀγαθός. " * 30
    (corpus / "test.work.jsonl").write_text(json.dumps({"locus": "source_0010.1", "source": "ocr", "edition": "merged", "text": "⟦irrelevant display⟧",
        "ocr_consensus": {"witnesses": [{"id": "good", "text": good}, {"id": "damaged", "text": strip_marks(good)}]}}, ensure_ascii=False) + "\n")
    out, summary = tmp_path / "pages.jsonl", tmp_path / "summary.json"
    result = report.corpus_report(corpus, out, summary)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert result["counts"] == {"readings": 2, "flagged": 1, "unflagged": 1}
    assert next(r for r in rows if r["witness"] == "damaged")["flag"]
    assert all(r["greek_letters"] > 200 for r in rows)
    expected = hashlib.sha256(("test.work\t" + report.benchmark.sha256(corpus / "test.work.jsonl") + "\n").encode()).hexdigest()
    assert result["corpus_sha256"] == expected
    (corpus / "new.digital.jsonl").write_text('{"locus":"1","source":"perseus","text":"λόγος"}\n')
    changed = report.corpus_report(corpus, out, summary)
    assert changed["input_corpus_files"] == result["input_corpus_files"]
    assert changed["counts"] == result["counts"]
    assert changed["corpus_sha256"] != result["corpus_sha256"]


def test_frozen_scan_review_is_bound_to_all_sixty_images_and_keeps_reference_defects():
    import scan_review_polytonic_loss as review
    result = review.build(ROOT / "data/evaluation/polytonic-loss/manifest.json")
    assert result["counts"] == {"pages": 60, "order_mismatch": 5, "partial_reference": 4, "eligible_reference": 52}
    assert result["fresh_model_outputs_seen"] is False
    assert result["source_text_changed"] is False
    assert len(result["excluded_reference_pages"]) == 8
