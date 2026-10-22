"""Physical source boundaries must not turn doubtful or modern Greek into body."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import herodas_body_source_observations as source
from prepare_herodas_body import build_manifest


BODY_PAGES = [
    72, 74, 76, 78, 132, 134, 136, 138, 180, 182, 184, 186,
    236, 238, 240, 242, 290, 292, 294, 296, 344, 346, 348, 350,
    388, 390, 392, 394, 396, 440, 442, 444, 472, 480, 486,
]
MISSING_PAGES = [
    76, 78, 134, 136, 138, 184, 186, 240, 242, 296, 348, 350,
    388, 390, 392, 394, 396, 440, 442, 444, 480, 486,
]


def test_full_physical_inventory_has_35_pages_and_22_missing_pages():
    packet = source.build_inventory()
    assert [row["scan_page"] for row in packet["body_pages"]] == BODY_PAGES
    assert [row["scan_page"] for row in packet["body_pages"] if not row["already_present"]] == MISSING_PAGES
    assert packet["accounting"] == {"body_pages": 35, "already_present_pages": 13,
        "missing_body_pages": 22, "preserved_primary_rows": 62}
    for row in packet["body_pages"]:
        assert row["printed_page"] == row["scan_page"] - 70
        assert row["first_body"] and row["last_body"] and row["evidence"]


def test_existing_page_claim_matches_all_62_frozen_role_review_passages():
    path = ROOT / "data/corpus_changes/editorial-role-review/records.jsonl.gz"
    records = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    preserved = [record["corrected_row"] for record in records
        if record["work"] == "herodas.mimiambi" and record["corrected_row"] is not None]
    assert len(preserved) == 62
    pages = {int(re.fullmatch(r"herodas_hk_([0-9]{4})\.[0-9]+", row["locus"])[1])
             for row in preserved}
    assert pages == set(source.EXISTING_BODY_PAGES)
    assert len(pages) == 13
    assert pages.isdisjoint(MISSING_PAGES)
    assert pages | set(MISSING_PAGES) == set(BODY_PAGES)


def test_seven_holds_keep_modern_renderings_and_unplaced_letters_explicit():
    holds = source.build_inventory()["holds"]
    assert len(holds) == 7
    assert [row["scan_page"] for row in holds] == [472, 482, 483, 486, 487, 490, 493]
    modern = next(row for row in holds if row["scan_page"] == 490)
    assert modern["status"] == "excluded-modern-rendering"
    assert "Headlam" in modern["evidence"] and "Latin Mattius" in modern["evidence"]
    unplaced = next(row for row in holds if row["scan_page"] == 493)
    assert unplaced["status"] == "unplaced-nonlexical-fragment"
    assert "ξυ" in unplaced["evidence"] and "IXa and IXb" in unplaced["evidence"]
    assert not {482, 483, 487, 490, 493} & set(BODY_PAGES)


def test_x_and_xi_crops_isolate_only_the_attributed_greek_verses():
    pages = {row["scan_page"]: row for row in source.BODY_PAGES}
    height = 611.10
    # X: title ends193.5, verse204.1–251.4, English heading begins280.8.
    _, top, _, bottom = pages[480]["region"]
    assert 193.5 < top * height < 204.1
    assert 251.4 < bottom * height < 280.8
    assert pages[480]["mime"] == "X" and pages[480]["verses"] == "1–4"
    # XI body also retains the dot-loss row near212. The original OCR crop
    # recognized only the verse; XIa's actual heading glyphs begin near225.
    _, top, _, bottom = pages[486]["region"]
    assert 179.4 < top * height < 189.6
    assert pages[486]["region"] == [.20, .304, .96, .360]
    assert 212 < bottom * height < 225
    _, ocr_top, _, ocr_bottom = pages[486]["ocr_region"]
    assert pages[486]["ocr_region"] == [.20, .304, .96, .344]
    assert 179.4 < ocr_top * height < 189.6
    assert 201.2 < ocr_bottom * height < 219.9
    assert pages[486]["mime"] == "XI" and pages[486]["verses"] == "1"
    xia = next(row for row in source.HOLDS if row["scan_page"] == 486)
    assert bottom < xia["region"][1]
    assert xia["status"] == "attribution-hold" and "Strabo" in xia["evidence"]


@pytest.mark.parametrize("left,right,left_range,right_range", [
    (184, 186, "60–81a", "81b–97"),
    (236, 238, "1–25a", "25b–53"),
    (294, 296, "42–73a", "73b–85"),
    (344, 346, "1–20a", "20b–47a"),
    (346, 348, "20b–47a", "47b–78"),
])
def test_shared_verses_remain_single_verses_across_page_breaks(left, right, left_range, right_range):
    pages = {row["scan_page"]: row for row in source.BODY_PAGES}
    assert pages[left]["verses"] == left_range
    assert pages[right]["verses"] == right_range
    assert "contin" in pages[left]["evidence"]
    assert "complete" in pages[right]["evidence"]


def test_viii_lacunae_are_not_treated_as_missing_ocr_words():
    pages = {row["scan_page"]: row for row in source.BODY_PAGES}
    assert pages[442]["verses"] == "24–54"
    assert "two isolated initial letters" in pages[442]["evidence"]
    assert "not the bottom" in pages[442]["evidence"]
    assert pages[444]["verses"] == "55–79"
    assert "55–57" in pages[444]["evidence"] and "verse 58" in pages[444]["evidence"]


def test_scan_pin_matches_bundled_source_and_rejects_another_file(tmp_path):
    source_path = ROOT / source.SOURCE["audit_path"]
    raw = source_path.read_bytes()
    assert len(raw) == 35869325
    assert hashlib.sha256(raw).hexdigest() == "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
    assert source.build_inventory(source_path)["source"]["sha256"] == source.SOURCE_SHA256
    other = tmp_path / "source.pdf"
    other.write_bytes(b"not the reviewed edition")
    with pytest.raises(ValueError, match="source scan changed"):
        source.build_inventory(other)


def test_inventory_is_detached_and_contains_no_implicit_lexical_admission():
    first = source.build_inventory()
    expected = deepcopy(first)
    first["source"]["sha256"] = "0" * 64
    first["body_pages"][0]["region"][0] = 1
    first["holds"].clear()
    assert source.build_inventory() == expected
    assert all("text" not in row and "lexical_eligible" not in row for row in expected["body_pages"])
    assert "do not authorize admitting all" in source.__doc__
    assert "not replacement transcriptions" in source.QUALIFICATION
    assert "literal readings are preserved" in source.QUALIFICATION
    request = build_manifest(expected["body_pages"])
    assert "no automatic admission" in request["purpose"]
    assert "timestamp" not in expected and "reviewed_at" not in expected


def test_prepare_manifest_keeps_source_pin_and_exact_reviewed_regions():
    request = build_manifest(source.BODY_PAGES)
    assert len(request["pages"]) == 35
    assert request["sources"]["herodas-headlam-knox"]["sha256"] == source.SOURCE_SHA256
    assert [row["scan_page"] for row in request["pages"]] == BODY_PAGES
    assert [row["region"] for row in request["pages"]] == [row.get("ocr_region", row["region"]) for row in source.BODY_PAGES]
    assert len({row["id"] for row in request["pages"]}) == 35


@pytest.mark.parametrize("pages", [
    [],
    [{"scan_page": 0, "region": [0, 0, 1, 1]}],
    [{"scan_page": 543, "region": [0, 0, 1, 1]}],
    [{"scan_page": True, "region": [0, 0, 1, 1]}],
    [{"scan_page": "76", "region": [0, 0, 1, 1]}],
    [{"scan_page": 76, "region": [0, 0, 1]}],
    [{"scan_page": 76, "region": [-.1, 0, 1, 1]}],
    [{"scan_page": 76, "region": [0, .9, 1, .1]}],
    [{"scan_page": 76, "region": [.5, 0, .5, 1]}],
    [{"scan_page": 76, "region": [0, 0, 1.1, 1]}],
    [{"scan_page": 76, "region": [0, float("nan"), 1, 1]}],
    [{"scan_page": 76, "region": [0, 0, 1, 1]},
     {"scan_page": 76, "region": [.1, .1, .9, .9]}],
])
def test_prepare_manifest_rejects_invalid_or_duplicate_page_requests(pages):
    with pytest.raises(ValueError):
        build_manifest(pages)
