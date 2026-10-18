from pathlib import Path
import sys

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


def test_smaller_failed_strip_supplement_is_exact_partition():
    manifest = prepare.build_supplement(50, "left-lower")
    parent = prepare.build_retry(50)
    target = next(p for p in parent["pages"] if p["id"] == manifest["supplements"]["replaces_region"])
    strips = manifest["pages"]
    assert len(strips) == 3
    assert strips[0]["region"][1] == target["region"][1]
    assert strips[-1]["region"][3] == target["region"][3]
    assert all(a["region"][3] == b["region"][1] for a, b in zip(strips, strips[1:]))
    assert all(p["region"][::2] == target["region"][::2] for p in strips)
    assert manifest["checkpoints"] == [prepare.CHECKPOINT38]
    assert not manifest["review"]["accepted_for_primary_ingest"]
    assert encode(manifest) == (ROOT / prepare.supplement_path(50, "left-lower")).read_bytes()


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
