import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_dio_ocr as prepare


def test_jobs_replay_reviewed_greek_panels_and_keep_early_comparisons_separate():
    jobs = prepare.build()
    assert json.loads(prepare.OUTPUT.read_text()) == jobs
    assert len(jobs["pages"]) == len({p["id"] for p in jobs["pages"]}) == 1217
    assert jobs["sanity_pages"] == 6
    assert {p["source_volume"] for p in jobs["pages"][:6]} == {1, 2, 6, 7, 8, 9}
    assert all(p["region"] == [0, 0, 0.5, 1] for p in jobs["pages"])
    for row in jobs["pages"]:
        if row["source_volume"] in {1, 2}:
            assert row["admission"] == "comparison-witness-pending-panel-routing"
            assert row["transmission"] == "fragments-and-zonaras-comparison"


def test_overlap_and_final_fragments_remain_explicit_before_admission():
    pages = prepare.build()["pages"]
    overlap = next(p for p in pages if p["source_volume"] == 6 and p["scan_page"] == 206)
    assert overlap["overlap"]["served_through"] == "55.9.4"
    assert overlap["overlap"]["existing_final_words"] == "βουληθεὶς δὲ δὴ τρόπον"
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 6) == 246
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 7) == 225
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 8) == 241
    assert max(p["scan_page"] for p in pages if p["source_volume"] == 9) == 249
