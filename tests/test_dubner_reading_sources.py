"""Source readings remain exact, bounded, reversible, and independently checked."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_dubner_readings as capture
import dubner_reading_observations as observations
import repair_dubner_scholias as scope


@pytest.fixture(scope="module")
def review():
    return observations.build(ROOT)


@pytest.fixture(scope="module")
def literal_rows():
    records = scope.source_records(ROOT, scope.archived_inputs(ROOT))
    return {(record["path"], record["row"]["locus"]): record["row"]
            for record in records if not record["derived"]}


def test_every_occurrence_names_an_exact_unnormalized_original_span(review, literal_rows):
    assert len(review["claims"]) == 33
    assert len(review["observations"]) == 49
    ids = set()
    for item in review["observations"]:
        row = literal_rows[(item["path"], item["locus"])]
        assert hashlib.sha256(row["text"].encode()).hexdigest() == item["row_sha256"]
        assert row["text"][item["start"]:item["end"]] == item["original"]
        assert item["original"] == item["original_text"]
        assert item["corrected"] == item["corrected_text"]
        assert item["original"] != item["corrected"]
        assert item["source_pdf_sha256"] == observations.SOURCE_PDFS[item["source_pdf"]]["sha256"]
        assert item["evidence"] and item["reviewed_at"] and item["evidence_crops"]
        assert item["id"] not in ids
        ids.add(item["id"])


def test_concrete_pilot_readings_retain_all_declared_contrary_ocr_forms(review):
    items = review["observations"]
    eta = [item for item in items if item["claim_id"] == "lenaiois-source-reading"]
    assert {item["original"] for item in eta} == {"Ἀθναίοις", "Ἀγναίοις"}
    assert {item["corrected"] for item in eta} == {"Ληναίοις"}
    lenaiois = next(item for item in review["claims"] if item["id"] == "lenaiois-source-reading")
    assert lenaiois["supersedes"]["proposed_reading"] == "Ἀθηναίοις"
    tenella = [item for item in items if item["claim_id"] == "tenella-unsplit"]
    assert len(tenella) == 6
    assert {item["original"] for item in tenella} == {"τὴν ελλα", "σήνελλα"}
    assert {item["corrected"] for item in tenella} == {"τήνελλα"}
    assert len({item["start"] for item in tenella if item["source_pdf"] == "toronto"}) == 3
    claim = next(claim for claim in review["claims"] if claim["id"] == "tenella-unsplit")
    assert claim["independent_edition"] is False
    assert claim["contrary_readings"] == ["σήνελλα", "τὴν ελλα"]


def test_same_word_keeps_its_occurrence_specific_printed_accent(review):
    askon = sorted((item for item in review["observations"]
                    if item["claim_id"] == "askon-scholion1225"), key=lambda item: item["start"])
    assert [item["corrected"] for item in askon] == ["ἀσκόν", "ἀσκόν", "ἀσκὸν"]


def test_corrections_are_local_and_do_not_overlap_or_drop_surrounding_text(review, literal_rows):
    groups = {}
    for item in review["observations"]:
        groups.setdefault((item["path"], item["locus"]), []).append(item)
    for key, items in groups.items():
        original = literal_rows[key]["text"]
        previous = 0
        corrected, reverse = original, []
        shift = 0
        for item in sorted(items, key=lambda value: value["start"]):
            assert item["start"] >= previous
            previous = item["end"]
            reverse.append((item["start"] + shift, item["corrected"], item["original"]))
            shift += len(item["corrected"]) - len(item["original"])
        for item in sorted(items, key=lambda value: value["start"], reverse=True):
            corrected = corrected[:item["start"]] + item["corrected"] + corrected[item["end"]:]
        for start, was, old in reversed(reverse):
            assert corrected[start:start + len(was)] == was
            corrected = corrected[:start] + old + corrected[start + len(was):]
        assert corrected == original


def test_review_does_not_claim_exhaustive_proofreading_or_reclassify_apparatus(review):
    assert {entry["toronto_page"] for entry in review["page_reviews"]} == {9, 43, 58, 73, 74, 251, 431, 543, 657, 768}
    assert "not exhaustive" in review["qualification"]
    nonhistorical = [item for item in review["observations"] if item["scope"] != "historical"]
    assert len(nonhistorical) == 4
    assert {item["scope"] for item in nonhistorical} == {"heading", "paratext"}
    assert not any("lexical_eligible" in item for item in review["observations"])
    assert {item["id"] for item in review["deferred"]} >= {"archilochus-kiolaos-crasis", "missing-editorial-note443"}


def test_changed_original_inputs_fail_instead_of_relocating_a_match(monkeypatch):
    records = scope.source_records(ROOT, scope.archived_inputs(ROOT))
    altered = deepcopy(records)
    row = next(record["row"] for record in altered if record["row"]["locus"] == "scholia_aristoph_dubner_0043.6")
    row["text"] = row["text"].replace("Ἀθναίοις", "different")
    monkeypatch.setattr(scope, "source_records", lambda root, before: altered)
    with pytest.raises(ValueError, match="preimage"):
        observations.build(ROOT)


def test_capture_checks_from_committed_evidence_without_external_pdfs():
    manifest = capture.check(ROOT)
    assert len(manifest["files"]) == 30
    assert manifest["render"]["images_retouched"] is False
    assert manifest["recipe_sha256"] == capture.recipe_pins()


def test_tampered_image_or_observation_cannot_validate(tmp_path):
    manifest = capture.check(ROOT)
    names = {item["path"] for item in manifest["files"]}
    names.add(observations.CAPTURE_PATH)
    names.add(scope.AUDIT + "/before.json.gz")
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    capture.check(tmp_path)
    image = next(item for item in manifest["files"] if item["kind"] == "source-reading-crop")
    path = tmp_path / image["path"]
    original = path.read_bytes()
    path.write_bytes(original + b"changed")
    with pytest.raises(ValueError, match="evidence changed"):
        capture.check(tmp_path)
    path.write_bytes(original)
    review_path = tmp_path / observations.REVIEW_PATH
    changed = json.loads(review_path.read_bytes())
    changed["observations"][0]["start"] += 1
    review_path.write_bytes(capture.encoded(changed))
    with pytest.raises(ValueError, match="observations no longer reproduce"):
        capture.check(tmp_path)


def test_bad_pdf_pin_is_rejected_before_writing_or_importing_a_renderer(tmp_path):
    pdf = tmp_path / "wrong.pdf"
    pdf.write_bytes(b"a different source")
    with pytest.raises(ValueError, match="PDF pin mismatch"):
        capture.capture(tmp_path, pdf, pdf)
    assert not (tmp_path / observations.OUTPUT).exists()
