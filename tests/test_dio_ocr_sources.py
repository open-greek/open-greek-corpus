import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_dio_ocr as prepare


def test_jobs_replay_reviewed_greek_panels_and_keep_early_comparisons_separate():
    jobs = prepare.build()
    assert json.loads(prepare.OUTPUT.read_text()) == jobs
    assert len(jobs["pages"]) == len({p["id"] for p in jobs["pages"]}) == 1500
    assert len({(p["source_volume"], p["scan_page"]) for p in jobs["pages"]}) == 1217
    assert jobs["sanity_pages"] == 7
    assert {p["source_volume"] for p in jobs["pages"][:7]} == {1, 2, 6, 7, 8, 9}
    assert all(p["region"][0] == 0 and p["region"][2] == .5 for p in jobs["pages"])
    for row in jobs["pages"]:
        if row["source_volume"] in {1, 2}:
            primary = row["panel_role"] == "fragment"
            assert row["admission"] == ("candidate-reading-pending-collation" if primary else "comparative-paratext")
            assert row["transmission"] == ("fragment-quotation" if primary else "comparative-quotation")


def test_overlap_and_final_fragments_remain_explicit_before_admission():
    pages = prepare.build()["pages"]
    overlap = next(p for p in pages if p["source_volume"] == 6 and p["scan_page"] == 206)
    assert overlap["overlap"]["served_through"] == "55.9.4"
    assert overlap["overlap"]["existing_final_words"] == "βουληθεὶς δὲ δὴ τρόπον"
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 6) == 246
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 7) == 225
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 8) == 241
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 9) == 249


def test_full_rule_separates_comparisons_but_short_apparatus_rule_does_not():
    import pymupdf
    from prepare_dio_panels import full_rules
    document = pymupdf.open()
    page = document.new_page(width=400, height=600)
    page.draw_line((35, 300), (170, 300), color=(0, 0, 0), width=.5)
    page.draw_line((35, 450), (60, 450), color=(0, 0, 0), width=.5)
    assert len(full_rules(page)) == 1
    assert abs(full_rules(page)[0] - .5) < .01


def test_faint_reviewed_rules_and_comparison_source_headings_are_preserved():
    layout = json.loads(prepare.LAYOUT.read_text())
    pages = {(p["source_volume"], p["scan_page"]): p for p in layout["pages"]}
    for key in [(1, 50), (1, 181), (2, 84)]:
        assert pages[key]["kind"] == "split"
        first, second = pages[key]["panels"]
        assert first["role"] == "fragment" and second["role"] == "comparison"
        assert first["region"][3] < second["region"][1]
    assert pages[(1, 122)]["kind"] == "comparison"
    assert pages[(2, 109)]["kind"] == "comparison"
