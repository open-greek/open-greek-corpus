"""A release gate must fail before writing a partial review as complete."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_photius_review_observations as driver


def test_complete_scope_gate_fails_before_writing(monkeypatch, tmp_path):
    target = Path("review.json")
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "build", lambda: (
        {target: b"partial observations"}, {"scope_complete": False, "counts": {}}))
    monkeypatch.setattr(sys, "argv", ["review", "--write", "--require-complete-scope"])
    with pytest.raises(SystemExit, match="not complete"):
        driver.main()
    assert not (tmp_path / target).exists()


def test_partial_accounting_can_be_reproduced_without_claiming_completion(monkeypatch, tmp_path):
    target = Path("review.json")
    (tmp_path / target).write_bytes(b"partial observations")
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "build", lambda: (
        {target: b"partial observations"}, {"scope_complete": False, "counts": {}}))
    monkeypatch.setattr(sys, "argv", ["review", "--check"])
    driver.main()
    (tmp_path / target).write_bytes(b"changed observations")
    with pytest.raises(SystemExit, match="do not reproduce"):
        driver.main()
