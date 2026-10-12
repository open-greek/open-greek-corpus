import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_corpus_catalog import correction_status
from build_ocr_quality_report import OCR_SOURCES
from build_provenance import OCR_MODEL


def test_independent_ocr_keeps_its_own_source_and_quality_class():
    assert "greek_library" in OCR_SOURCES
    assert "model not documented" in OCR_MODEL["greek_library"]
    assert correction_status("work", "greek_library", set(), 0, set(), set()) == "raw-ocr"
    assert correction_status("work", "greek_library", {"manual"}, 1, set(), set()) == "manual"
