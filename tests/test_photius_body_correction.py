"""The single bounded body repair preserves prefix, variants, and exact undo."""
import copy
import gzip
import json

import pytest

from test_photius_apparatus_repair import ROOT, fixture_review
import repair_photius_apparatus as repair
import repair_photius_body as body
from frequency_projection import FrequencyProjection, lexical_text
from ocr_consensus import restore_corpus_consensus


def body_fixture(tmp_path):
    fixture_review(tmp_path)
    authority = json.loads((ROOT / body.REVIEW).read_bytes())
    target = tmp_path / body.REVIEW
    target.write_bytes(repair.encode(authority))
    source = tmp_path / body.LIBRARY
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes((ROOT / body.LIBRARY).read_bytes())
    return authority


def test_bounded_body_repair_preserves_prefix_ties_sources_and_exact_reversal(tmp_path):
    authority = body_fixture(tmp_path)
    before = (tmp_path / repair.CORPUS).read_bytes()
    old = next(row for row in map(json.loads, before.splitlines()) if row["locus"] == body.LOCUS)
    artifacts, audit = repair.build(tmp_path)
    assert audit["counts"]["body_corrected_rows"] == 1
    correction = audit["body_correction"]
    assert correction["counts"] == {"corrected_rows": 1, "retained_prefix_characters": 162,
        "held_loop_characters": 32, "replacement_agreement_slots": 76, "replacement_unresolved_slots": 12}
    updated = correction["changes"][0]["corrected_row"]
    assert updated["text"].startswith(old["text"][:162])
    assert updated["source_body_correction"]["original_text"] == old["text"]
    assert "ἡμῖν ἡμῖν" not in updated["text"]
    assert "editorial_layer" not in updated
    assert updated["license"] == "CC-BY-SA-4.0"
    assert updated["component_attribution"][1]["separate_api_notice"]["tdm_reservation"] == 1
    network_path = repair.ARCHIVE / "body-word-networks.json.gz"
    full = json.loads(gzip.decompress(artifacts[network_path]))[body.LOCUS]
    compact = {key: updated[key] for key in ("text", "analysis_text", "ocr_consensus")}
    assert restore_corpus_consensus(compact, full) == full
    assert len([slot for slot in full["ocr_consensus"]["slots"] if slot["status"] == "unresolved"]) == 12
    tail = full["ocr_consensus"]["span_networks"]["replacement_tail"]
    assert all("historical-prefix" not in reading["support"]
               for slot in tail["ocr_consensus"]["slots"] for reading in slot["readings"])
    assert full["ocr_consensus"]["witnesses"][0]["text"] == old["text"]
    assert full["ocr_consensus"]["witnesses"][0]["abstention_audit"]["excluded_spans"][0]["text"] == old["text"][162:]
    assert lexical_text(updated) == updated["analysis_text"]
    segments = FrequencyProjection(tmp_path / "data").segments(updated)
    assert len(segments) > 1 and "τοῦ διαβόλου" not in " ".join(segments)
    assert FrequencyProjection(tmp_path / "data").contextual_text(updated) is None
    repair.apply(tmp_path)
    assert repair.check(tmp_path) == audit
    assert repair.restore_legacy_bytes((tmp_path / repair.CORPUS).read_bytes(), tmp_path) == before
    assert (tmp_path / repair.ARCHIVE / "body-source-library.json.gz").read_bytes() == (ROOT / body.LIBRARY).read_bytes()
    assert repair.active_metadata(tmp_path)["body_correction"]["counts"] == correction["counts"]
    assert json.loads((tmp_path / repair.ARCHIVE / "body-review.json").read_bytes()) == authority
    (tmp_path / body.REVIEW).write_bytes(b"source invalidated")
    with pytest.raises(ValueError, match="invalidated"):
        repair.check(tmp_path)
    repair.undo(tmp_path)
    assert (tmp_path / repair.CORPUS).read_bytes() == before


@pytest.mark.parametrize("change", ["old-row", "scope", "source", "following", "image", "window", "manual", "digital",
                                    "vote-mask", "license", "rights", "reservation", "convention"])
def test_body_authority_never_generalizes_to_unreviewed_readings(tmp_path, change):
    authority = body_fixture(tmp_path)
    if change == "old-row": authority["row_sha256"] = "0" * 64
    elif change == "scope": authority["replacement_scope"]["start"] -= 1
    elif change == "source": authority["source"]["scan_page"] += 1
    elif change == "following": authority["following_body_anchor"]["row_sha256"] = "0" * 64
    elif change == "image": authority["source_image"]["crop_sha256"] = "0" * 64
    elif change == "window": authority["source_library_window"]["start"] -= 1
    elif change == "manual":
        witness = next(w for w in authority["witnesses"] if w["id"] == "manual-scan-review")
        witness["text"] += " ἄλλο"
        witness["artifact_sha256"] = body.sha(witness["text"].encode())
    elif change == "digital":
        next(w for w in authority["witnesses"] if w["id"] == "source-library-local002")["text"] += " ἄλλο"
    elif change == "vote-mask": authority["witnesses"][0]["voting_segments"] = []
    elif change == "license": authority["source_library_credit"]["license"]["url"] = "PD"
    elif change == "rights": authority["source_library_credit"]["rights"] = ""
    elif change == "reservation": authority["source_library_credit"]["separate_api_notice"]["tdm_reservation"] = 0
    else: authority["transcription_convention"] = ""
    (tmp_path / body.REVIEW).write_bytes(repair.encode(authority))
    with pytest.raises(ValueError):
        repair.build(tmp_path)


@pytest.mark.parametrize("key", ["text", "analysis_text"])
def test_body_projection_rejects_independent_edits(tmp_path, key):
    body_fixture(tmp_path)
    _, audit = repair.build(tmp_path)
    row = copy.deepcopy(audit["body_correction"]["changes"][0]["corrected_row"])
    row[key] += " ἄλλο"
    with pytest.raises(ValueError, match="Body correction lexical projection"):
        lexical_text(row)


@pytest.mark.parametrize("target", ["body-review.json", "body-source-library.json.gz", "body-word-networks.json.gz"])
def test_every_body_source_and_network_is_frozen_in_the_same_layer(tmp_path, target):
    body_fixture(tmp_path)
    repair.apply(tmp_path)
    path = tmp_path / repair.ARCHIVE / target
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises((ValueError, json.JSONDecodeError, OSError)):
        repair.restore_legacy_bytes((tmp_path / repair.CORPUS).read_bytes(), tmp_path)


def test_registry_separately_credits_the_one_licensed_body_correction(tmp_path):
    from test_reviewed_manifestations import photius_fixture, registry
    import reviewed_manifestations as reviewed
    photius_fixture(tmp_path)
    body_fixture(tmp_path)
    with (tmp_path / repair.CORPUS).open("ab") as stream:
        for number in range(14, 322):
            stream.write(repair.jsonl([{"urn": "photius.bibliotheca", "locus": f"photius_bekker1824_{number:04d}.1",
                                       "text": "νεώτερος λόγος", "source": "synthetic-coverage-fixture"}]))
    path = tmp_path / "data/corpus_changes/photius-bekker-coverage/coverage.json"
    coverage = json.loads(path.read_bytes())
    coverage["new_corpus_sha256"] = repair.sha((tmp_path / repair.CORPUS).read_bytes())
    coverage["source_library"]["sha256"] = body.LIBRARY_SHA
    path.write_bytes(repair.encode(coverage))
    frozen_coverage = path.read_bytes()
    repair.apply(tmp_path)
    reg = registry("photius.bibliotheca")
    metadata = reviewed.register_reviewed_manifestations(reg, tmp_path)["photius.bibliotheca"]
    components = metadata["coverage_composition"]["components"]
    assert components[0]["passages"] == 3835
    correction = next(c for c in components if c.get("role") == "reviewed-historical-body-correction")
    assert correction["passages"] == 1 and correction["license"] == "CC-BY-SA-4.0"
    assert correction["source_library"]["separate_api_notice"]["tdm_reservation"] == 1
    assert path.read_bytes() == frozen_coverage


def test_two_explicit_body_cases_keep_separate_sources_networks_and_exact_undo(tmp_path):
    body_fixture(tmp_path)
    (tmp_path / body.REVIEW7).write_bytes((ROOT / body.REVIEW7).read_bytes())
    before = (tmp_path / repair.CORPUS).read_bytes()
    artifacts, audit = repair.build(tmp_path)
    report = audit["body_correction"]
    assert report["counts"] == {"corrected_rows": 2, "retained_prefix_characters": 1143,
        "held_loop_characters": 81, "replacement_agreement_slots": 253, "replacement_unresolved_slots": 19}
    assert set(report["cases"]) == {body.LOCUS, body.LOCUS7}
    assert len(report["source_reviews"]) == len(report["networks"]) == 2
    assert len({pin["path"] for pin in report["source_reviews"]}) == 2
    assert len({pin["path"] for pin in report["networks"]}) == 2
    for change in report["changes"]:
        locus = change["locus"]
        case = body.CASES[locus]
        updated = change["corrected_row"]
        assert updated["text"].startswith(change["original_text"][:case["start"]])
        lexical_text(updated)
        full = json.loads(gzip.decompress(artifacts[repair.ARCHIVE / case["network_file"]]))[locus]
        restore_corpus_consensus({key: updated[key] for key in ("text", "analysis_text", "ocr_consensus")}, full)
        assert len([slot for slot in full["ocr_consensus"]["slots"] if slot["status"] == "unresolved"]) == case["counts"]["unresolved"]
    repair.apply(tmp_path)
    assert repair.restore_legacy_bytes((tmp_path / repair.CORPUS).read_bytes(), tmp_path) == before
    (tmp_path / body.REVIEW7).write_bytes(b"source invalidated")
    with pytest.raises(ValueError, match="invalidated"):
        repair.check(tmp_path)
    repair.undo(tmp_path)
    assert (tmp_path / repair.CORPUS).read_bytes() == before


@pytest.mark.parametrize("change", ["scope", "region", "manual", "window", "image", "unapproved-locus"])
def test_second_case_has_independent_frozen_source_guards(tmp_path, change):
    body_fixture(tmp_path)
    authority = json.loads((ROOT / body.REVIEW7).read_bytes())
    if change == "scope": authority["replacement_scope"]["start"] -= 1
    elif change == "region": authority["source"]["region"][-1] += .01
    elif change == "manual": authority["witnesses"][0]["text"] += " ἄλλο"
    elif change == "window": authority["source_library_window"]["start"] -= 1
    elif change == "image": authority["source_image"]["crop_sha256"] = "0" * 64
    else: authority["locus"] = "helladius_chrestomathia_photius_bekker_v2_0007.4"
    (tmp_path / body.REVIEW7).write_bytes(repair.encode(authority))
    with pytest.raises(ValueError):
        repair.build(tmp_path)
