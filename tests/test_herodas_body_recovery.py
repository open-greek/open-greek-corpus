"""Source readings preserve critical text, literal reversals, and admission safety."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import repair_herodas_body as recovery
import herodas_body_witness_observations as roles
import herodas_body_witnesses as witnesses
from ocr_consensus import merge_witnesses

ROOT = Path(__file__).resolve().parents[1]
SPEC = {"scan_page": 76, "region": [.2, .082, .9, .79]}


@pytest.mark.skipif(not (ROOT / recovery.AUDIT / "changes.json").exists(),
                    reason="Production recovery has not been admitted")
def test_published_recovery_replays_and_undo_survives_source_removal(tmp_path):
    """The distributed evidence replays, but literal undo requires no live source."""
    shutil.copytree(ROOT / recovery.AUDIT, tmp_path / recovery.AUDIT)
    primary = tmp_path / recovery.PRIMARY
    primary.parent.mkdir(parents=True)
    primary.write_bytes((ROOT / recovery.PRIMARY).read_bytes())
    source = tmp_path / next(iter(recovery.SOURCE_FILES))
    source.parent.mkdir(parents=True, exist_ok=True)
    source.hardlink_to(ROOT / next(iter(recovery.SOURCE_FILES)))
    audit, before, _ = recovery.verify(tmp_path)
    rows = [json.loads(line) for line in primary.read_text().splitlines()]
    original = recovery.parse_original(before[recovery.PRIMARY].encode())
    current = {row["locus"]: row for row in rows}
    assert len(rows) == 84 and audit["counts"]["body_pages"] == 35
    assert all(current[row["locus"]] == row for row in original)
    recovery.undo(tmp_path)
    assert recovery.sha(primary.read_bytes()) == recovery.INPUT_SHA256
    source.unlink()
    recovery.undo(tmp_path)
    assert primary.read_bytes() == before[recovery.PRIMARY].encode()


@pytest.mark.skipif(not (ROOT / recovery.AUDIT / "networks.json.gz").exists(),
                    reason="Production recovery networks have not been admitted")
def test_every_published_vote_key_resolves_both_reviewed_and_raw_networks():
    from ocr_consensus import compact_corpus_consensus, restore_corpus_consensus
    rows = [json.loads(line) for line in (ROOT / recovery.PRIMARY).read_text().splitlines()]
    rows = [row for row in rows if row.get("herodas_body_recovery")]
    assert len(rows) == 22
    for row in rows:
        reference = row["ocr_consensus"]["full_network"]
        networks = json.loads(gzip.decompress((ROOT / reference["path"]).read_bytes()))
        full = networks[reference["key"]]
        projection = compact_corpus_consensus(full, reference)
        assert all(row[key] == value for key, value in projection.items())
        assert restore_corpus_consensus(projection, full) == full
        raw_reference = full["ocr_consensus"]["raw_ocr_network"]
        assert raw_reference["path"] == reference["path"]
        raw = networks[raw_reference["key"]]
        assert recovery.unapply_scan_review(full, raw) == raw


def review(text, **extra):
    return {"text": text, "reviewed_at": "2026-10-22T17:00:00Z",
        "evidence": "Pinned scan, page 76, source-confirmed printed reading.",
        "speaker_labels": [], "uncertainties": [], **extra}


def vote(text="λόγος μένει"):
    return merge_witnesses([
        {"id": "qwen36", "text": text, "artifact_sha256": "a" * 64},
        {"id": "qwen38", "text": text, "artifact_sha256": "b" * 64},
    ])


@pytest.mark.parametrize("marked", ["[λέξις]", "<λέξις>", "⟨λέξις⟩", "†λέξις†", "λέ[ξ]ις", "λέ(ξις)"])
def test_printed_marks_remain_literal_and_never_become_scalar_attestations(marked):
    text = "λόγος " + marked + " μένει"
    corrected, _ = recovery.apply_scan_review(vote(), review(text), 76, SPEC)
    assert corrected["text"] == text
    assert corrected["analysis_text"] == "λόγος μένει"


def test_letter_damage_and_lacuna_boundaries_are_conservative():
    text = "λόγος λ̣έξις ... τέλος μένει"
    corrected, _ = recovery.apply_scan_review(vote(), review(text), 76, SPEC)
    assert corrected["text"] == text
    assert corrected["analysis_text"] == "λόγος μένει"


def test_source_uncertainty_addresses_one_exact_repeated_occurrence():
    text = "λόγος λόγος μένει"
    uncertainty = {"start": 6, "end": 11, "text": "λόγος", "alternatives": ["λογός"],
        "evidence": "The second occurrence's accent is indistinct."}
    corrected, _ = recovery.apply_scan_review(vote(), review(text, uncertainties=[uncertainty]), 76, SPEC)
    assert corrected["analysis_text"] == "λόγος μένει"
    assert corrected["source_uncertainties"] == [uncertainty]


@pytest.mark.parametrize("uncertainty", [
    {"start": -1, "end": 5, "alternatives": [], "evidence": "source"},
    {"start": 0, "end": 5, "text": "other", "alternatives": [], "evidence": "source"},
    {"start": 0, "end": 5, "alternatives": []},
    {"start": 0, "end": 5, "alternatives": "other", "evidence": "source"},
])
def test_invalid_uncertainty_cannot_exclude_an_arbitrary_reading(uncertainty):
    with pytest.raises(ValueError, match="exact source bounds"):
        recovery.apply_scan_review(vote(), review("λόγος μένει", uncertainties=[uncertainty]), 76, SPEC)


def test_unreadable_mark_may_abstain_without_inventing_an_alternative():
    corrected, _ = recovery.apply_scan_review(vote(), review("λόγος μένει", uncertainties=[
        {"start": 0, "end": 5, "alternatives": [], "evidence": "Indistinct mark, no asserted alternative."}
    ]), 76, SPEC)
    assert corrected["analysis_text"] == "μένει"


def test_scan_review_is_a_reversible_layer_above_unchanged_votes():
    original = vote("λογός μένει")
    saved = deepcopy(original)
    corrected, audit = recovery.apply_scan_review(original, review("λόγος μένει."), 76, SPEC)
    assert original == saved
    assert corrected["analysis_text"] == "λόγος μένει"
    assert audit["original_text"] == original["text"]
    assert audit["corrected_text"] == "λόγος μένει."
    assert audit["source_pdf_sha256"] == recovery.SCAN_SHA256
    assert audit["witness_edits"]
    assert recovery.unapply_scan_review(corrected, original) == original
    changed = deepcopy(original)
    changed["text"] += " changed"
    with pytest.raises(ValueError, match="exact pre-review vote"):
        recovery.unapply_scan_review(corrected, changed)


@pytest.mark.parametrize("original,corrected", [
    ("λόγος", "λόγος μένει"), ("λόγος μένει", "μένει"),
    ("λόγος\nμένει", "λόγος μένει."), ("λέξις λέξις", "λέξις λόγος"),
])
def test_literal_edits_reconstruct_both_directions(original, corrected):
    edits = recovery.literal_edits(original, corrected, review(corrected), 76, "qwen36")
    for text, range_key, value_key, expected in [
        (original, "original_char_range", "corrected_text", corrected),
        (corrected, "corrected_char_range", "original_text", original),
    ]:
        cursor, parts = 0, []
        for edit in edits:
            start, end = edit[range_key]
            parts += [text[cursor:start], edit[value_key]]
            cursor = end
        assert "".join(parts) + text[cursor:] == expected


@pytest.mark.parametrize("line", ["ΠΑΝΤΑ ΚΑΛΑ", "ΜΗTPΩ"])
def test_unreviewed_capitals_are_not_silently_mislabeled_as_speakers(line):
    with pytest.raises(ValueError, match="occurrence-specific source role"):
        recovery._fresh_projection(line + "\nλόγος", ["ΜΗΤΡΩ"])


def test_only_a_source_identified_speaker_line_is_excluded():
    projection = recovery._fresh_projection("ΜΗΤΡΩ\nλόγος μένει", ["ΜΗΤΡΩ"])
    assert recovery._body_text(projection) == "λόγος μένει"
    assert projection["excluded_spans"][0]["text"] == "ΜΗΤΡΩ\n"


def test_mixed_script_speaker_alias_requires_exact_prediction_and_printed_name():
    text = "ΜΗTPΩ\nλόγος μένει"
    aliases = {"ΜΗTPΩ": "ΜΗΤΡΩ"}
    projection = recovery._fresh_projection(text, ["ΜΗΤΡΩ"], aliases, recovery.sha(text.encode()))
    assert recovery._body_text(projection) == "λόγος μένει"
    for raw, names in [(text + ".", ["ΜΗΤΡΩ"]), (text, ["ΑΛΛΟΣ"])]:
        with pytest.raises(ValueError, match="raw prediction or printed role"):
            recovery._fresh_projection(raw, names, aliases, recovery.sha(text.encode()))


def test_independent_recognizers_cast_distinct_votes_when_text_is_identical(monkeypatch):
    text = "λόγος μένει"
    monkeypatch.setattr(roles, "project_qwen36", lambda page, raw: {
        "authorial_spans": [{"start": 0, "end": len(raw), "text": raw}], "excluded_spans": []})
    historical = {"qwen36": {"files": {"grc": {"text": text}}}}
    result, _ = recovery.merge_page(76, historical, {"raw_prediction": text}, SPEC, review(text))
    assert result["ocr_consensus"]["counts"] == {"agreement": 2}
    assert result["analysis_text"] == text


@pytest.fixture
def published_excerpt():
    import repair_editorial_roles as previous
    root = ROOT / previous.AUDIT
    before = json.loads(gzip.decompress((root / "before.json.gz").read_bytes()))
    source_review = json.loads((root / "source-review.json").read_bytes())
    outputs, _, _ = previous.build_outputs(before, source_review)
    return outputs[recovery.PRIMARY]


def test_bad_recognition_image_is_rejected_before_any_admission(tmp_path, monkeypatch, published_excerpt):
    primary = tmp_path / recovery.PRIMARY
    primary.parent.mkdir(parents=True)
    primary.write_bytes(published_excerpt)
    (tmp_path / "scan.pdf").write_bytes(b"scan")
    monkeypatch.setattr(recovery, "SOURCE_FILES", {"scan.pdf": recovery.sha(b"scan")})
    monkeypatch.setattr(recovery, "recipe_pins", lambda: {"test": "a" * 64})
    monkeypatch.setattr(witnesses, "validate_packet", lambda value: None)
    packet, request, predictions = [tmp_path / name for name in ("witnesses.gz", "request.json", "predictions.jsonl")]
    packet.write_bytes(recovery.compressed({}))
    request.write_bytes(b"{}")
    predictions.write_bytes(b"[]")
    def reject(*args):
        raise ValueError("recognition image differs")
    monkeypatch.setattr(recovery, "_verify_prediction_images", reject)
    with pytest.raises(ValueError, match="recognition image differs"):
        recovery.run(tmp_path, "apply", witnesses=packet, request=request, predictions=predictions,
                     reviewed_at="2026-10-22T17:00:00Z")
    assert primary.read_bytes() == published_excerpt
    assert not (tmp_path / recovery.AUDIT).exists()


def test_generated_reading_scope_matches_exact_missing_page_inventory():
    from herodas_body_source_observations import BODY_PAGES
    readings = recovery.source_readings()
    assert set(readings) == {page["scan_page"] for page in BODY_PAGES if not page["already_present"]}
    for page in BODY_PAGES:
        if page["scan_page"] in readings:
            corrected, _ = recovery.apply_scan_review(vote(), readings[page["scan_page"]], page["scan_page"], page)
            assert corrected["text"] == readings[page["scan_page"]]["text"]
