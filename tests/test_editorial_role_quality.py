"""Herodas source-role accounting does not imply improved OCR recognition."""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_ocr_quality_report import herodas_role_qualification
from repair_editorial_roles import AUDIT


def test_herodas_quality_qualification_counts_only_the_reviewed_role_partition():
    current = herodas_role_qualification(ROOT)
    counts = current["counts"]
    assert counts["original_analysis_tokens"] == 2846
    assert counts["primary_analysis_tokens"] == 2036
    assert counts["retained_analysis_tokens"] == 810
    assert counts["original_rows"] == 136 and counts["primary_rows"] == 62
    assert current["audit"] == {"path": f"{AUDIT}/changes.json",
        "sha256": hashlib.sha256((ROOT / AUDIT / "changes.json").read_bytes()).hexdigest()}
    assert "without correcting Greek spellings" in current["qualification"]
    assert "not character error rate" in current["qualification"]
    assert "does not certify every retained OCR reading" in current["qualification"]
    assert "missing Herodas pages" in current["qualification"]


def test_absent_role_admission_makes_no_quality_claim(tmp_path):
    assert herodas_role_qualification(tmp_path) is None
