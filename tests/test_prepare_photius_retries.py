from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_photius_retries import build_retry, encode
import prepare_photius_retries as prepare


def test_checkpoint_specific_retries_pin_complete_source_body_in_order():
    for number, cut in ((47, .458), (50, .456)):
        result = build_retry(number)
        assert result["retry_of"]["page_id"] == f"photius-bekker-{number:04d}"
        assert result["retry_of"]["sha256"] == "92bb67209eaa7dcca53800c499c68b4c1a085cbb2d62f2909b27da99c0acdcd6"
        assert result["checkpoints"] == [{"model": "Qwen/Qwen3.8-27B-FP8", "revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}]
        assert [p["reading_order"] for p in result["pages"]] == list(range(4))
        assert all(p["scan_page"] == number for p in result["pages"])
        assert result["pages"][0]["region"][3] == result["pages"][1]["region"][1] == cut
        assert result["pages"][2]["region"][3] == result["pages"][3]["region"][1] == cut
        assert not result["review"]["accepted_for_primary_ingest"]
        assert encode(result) == (ROOT / f"data/ocr_requests/photius-bekker-page{number:04d}-retry.json").read_bytes()


@pytest.mark.parametrize("number,name", [(50, "left-lower"), (87, "right-middle"), (113, "right-first")])
def test_smaller_failed_strip_supplement_is_exact_partition(number, name):
    manifest = prepare.build_supplement(number, name)
    parent = prepare.build_retry(number)
    target = next(p for p in parent["pages"] if p["id"] == manifest["supplements"]["replaces_region"])
    strips = manifest["pages"]
    assert len(strips) == 3
    assert strips[0]["region"][1] == target["region"][1]
    assert strips[-1]["region"][3] == target["region"][3]
    assert all(a["region"][3] == b["region"][1] for a, b in zip(strips, strips[1:]))
    assert all(p["region"][::2] == target["region"][::2] for p in strips)
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    assert not manifest["review"]["accepted_for_primary_ingest"]
    assert encode(manifest) == (ROOT / prepare.supplement_path(number, name)).read_bytes()


def test_page87_six_strips_preserve_column_order_and_body_bounds():
    manifest = prepare.build_retry(87)
    strips = manifest["pages"]
    assert len(strips) == 6
    assert [p["reading_order"] for p in strips] == list(range(6))
    assert all(p["region"][2] < .5 for p in strips[:3])
    assert all(p["region"][0] > .5 for p in strips[3:])
    assert strips[2]["region"][3] == strips[5]["region"][3] == .840
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    assert encode(manifest) == (ROOT / prepare.manifest_path(87)).read_bytes()


def test_new_failed_pages_are_scoped_to_their_actual_checkpoint():
    for number, checkpoint in [(105, prepare.CHECKPOINT38), (109, prepare.CHECKPOINT36), (112, prepare.CHECKPOINT36)]:
        manifest = prepare.build_retry(number)
        assert manifest["checkpoints"] == [checkpoint]
        assert len(manifest["pages"]) == 6
        assert {p["scan_page"] for p in manifest["pages"]} == {number}
        assert [p["reading_order"] for p in manifest["pages"]] == list(range(6))
        assert encode(manifest) == (ROOT / prepare.manifest_path(number)).read_bytes()


def test_page113_faint_source_uses_eight_parts_without_a_second_vote():
    manifest = prepare.build_retry(113)
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    assert len(manifest["pages"]) == 8
    assert [p["reading_order"] for p in manifest["pages"]] == list(range(8))
    for group in (manifest["pages"][:4], manifest["pages"][4:]):
        assert group[0]["region"][1] == .065 and group[-1]["region"][3] == .813
        assert all(a["region"][3] == b["region"][1] for a, b in zip(group, group[1:]))
    assert encode(manifest) == (ROOT / prepare.manifest_path(113)).read_bytes()


def test_stop_terminated_repetitions_get_separately_pinned_checkpoint_requests():
    page27 = build_retry(27)
    assert page27["checkpoints"] == [prepare.CHECKPOINT38]
    assert len(page27["pages"]) == 6
    assert encode(page27) == (ROOT / prepare.manifest_path(27)).read_bytes()
    original47 = build_retry(47)
    variant = prepare.build_variant("0047-qwen36")
    assert variant["checkpoints"] == [prepare.CHECKPOINT36]
    assert variant["pages"] == original47["pages"]
    assert original47["checkpoints"] == [prepare.CHECKPOINT38]
    assert encode(variant) == (ROOT / prepare.variant_path("0047-qwen36")).read_bytes()


def test_page13_mark_stripping_exception_pins_the_exact_successful_attempt():
    manifest = prepare.build_supplement(13, "upper-preface")
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    condition = manifest["replacement_condition"]
    assert condition["kind"] == "source-confirmed-polytonic-mark-stripping"
    assert condition["greek_letters"] == 919 and condition["breathing_letters"] == 0
    assert condition["finish_reason"] == "stop"
    assert len(condition["raw_file_sha256"]) == len(condition["prediction_record_sha256"]) == 64
    assert manifest["pages"][0]["region"][1] == .05
    assert manifest["pages"][-1]["region"][3] == .441
    assert all("breathing" in p["prompt_suffix"] for p in manifest["pages"])
    assert encode(manifest) == (ROOT / prepare.supplement_path(13, "upper-preface")).read_bytes()


def test_page113_stop_loop_exception_pins_the_exact_repeated_attempt():
    manifest = prepare.build_supplement(113, "right-first")
    condition = manifest["replacement_condition"]
    assert condition["kind"] == "source-confirmed-repetition-loop"
    assert condition["finish_reason"] == "stop"
    assert condition["most_repeated_phrase_occurrences"] == condition["most_repeated_line_occurrences"] == 241
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]


def test_source_confirmed_apparatus_leaks_use_only_the_original_model_body_columns():
    for page in [41, 49, 83, 119, 147, 181, 188, 207]:
        manifest = build_retry(page)
        assert manifest["checkpoints"] == [prepare.CHECKPOINT36]
        assert len(manifest["pages"]) == 2
        assert [p["reading_order"] for p in manifest["pages"]] == [0, 1]
        assert manifest["pages"][0]["region"][2] < .5
        assert manifest["pages"][1]["region"][0] > .5
        assert all(p["scan_page"] == page for p in manifest["pages"])
        assert "apparatus" in manifest["review"]["evidence"]
        assert encode(manifest) == (ROOT / prepare.manifest_path(page)).read_bytes()


def test_later_gap_retries_pin_the_later_manifest_and_only_qwen38():
    for page in [381, 384, 388, 396, 397]:
        manifest = build_retry(page)
        assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
        assert manifest["retry_of"]["path"].endswith("photius-bekker-later-gap.json")
        assert len(manifest["pages"]) == 6
        assert [p["reading_order"] for p in manifest["pages"]] == list(range(6))
        assert all(p["scan_page"] == page for p in manifest["pages"])
        assert encode(manifest) == (ROOT / prepare.manifest_path(page)).read_bytes()
    manifest = build_retry(385)
    assert manifest["checkpoints"] == [prepare.CHECKPOINT36]
    assert manifest["retry_of"]["path"].endswith("photius-bekker-later-gap.json")
    assert len(manifest["pages"]) == 6
    assert encode(manifest) == (ROOT / prepare.manifest_path(385)).read_bytes()


def test_child_supplement_names_and_partitions_only_the_exact_looping_parent_part():
    import hashlib
    manifest = prepare.build_supplement(113, "right-first-part02")
    parent = prepare.build_supplement(113, "right-first")
    assert manifest["supplements"]["manifest_path"] == prepare.supplement_path(113, "right-first").as_posix()
    assert manifest["supplements"]["manifest_sha256"] == hashlib.sha256(encode(parent)).hexdigest()
    assert manifest["supplements"]["replaces_region"] == parent["pages"][1]["id"]
    assert manifest["pages"][0]["region"] == [.505, .126, .97, .16042]
    assert manifest["pages"][1]["region"] == [.505, .16042, .97, .195]
    assert manifest["replacement_condition"]["most_repeated_phrase_occurrences"] == 8
    assert manifest["replacement_condition"]["most_repeated_line_occurrences"] == 3
    assert encode(manifest) == (ROOT / prepare.supplement_path(113, "right-first-part02")).read_bytes()


def test_page192_coverage_omission_retries_only_the_affected_checkpoint():
    manifest = build_retry(192)
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    assert [p["reading_order"] for p in manifest["pages"]] == [0, 1]
    assert manifest["pages"][0]["region"] == [.045, .062, .495, .864]
    assert manifest["pages"][1]["region"] == [.505, .062, .975, .864]
    assert "omits and reorders" in manifest["review"]["failure"]
    assert encode(manifest) == (ROOT / prepare.manifest_path(192)).read_bytes()


def test_late_first_volume_length_and_apparatus_requests_keep_checkpoint_scope():
    for page, checkpoint, count in [(232, prepare.CHECKPOINT36, 6), (234, prepare.CHECKPOINT36, 6),
                                     (233, prepare.CHECKPOINT38, 6), (242, prepare.CHECKPOINT36, 6),
                                     (239, prepare.CHECKPOINT38, 2)]:
        manifest = build_retry(page)
        assert manifest["checkpoints"] == [checkpoint]
        assert len(manifest["pages"]) == count
        assert encode(manifest) == (ROOT / prepare.manifest_path(page)).read_bytes()
    supplement = prepare.build_supplement(381, "right-middle")
    assert supplement["replacement_condition"]["greek_letters"] == 576
    assert supplement["replacement_condition"]["breathing_letters"] == 0
    assert len(supplement["pages"]) == 3
    assert encode(supplement) == (ROOT / prepare.supplement_path(381, "right-middle")).read_bytes()
    for page, name in [(381, "right-middle-part01"), (397, "right-lower")]:
        supplement = prepare.build_supplement(page, name)
        assert supplement["replacement_condition"]["breathing_letters"] == 1
        assert encode(supplement) == (ROOT / prepare.supplement_path(page, name)).read_bytes()


def test_last_four_failed_page_requests_preserve_complete_source_columns():
    for page, count in [(245, 6), (250, 4), (252, 6), (255, 6)]:
        request = build_retry(page)
        assert request["checkpoints"] == [prepare.CHECKPOINT38]
        assert len(request["pages"]) == count
        assert [p["reading_order"] for p in request["pages"]] == list(range(count))
        assert encode(request) == (ROOT / prepare.manifest_path(page)).read_bytes()
    request = build_retry(250)
    assert request["pages"][-1]["region"] == [.505, .062, .97, .846]
