"""Structured corrections applied at the TEI-to-corpus boundary."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_corpus_loci import (  # noqa: E402
    apply_text_corrections, load_text_corrections,
)


def test_load_and_apply_exact_scoped_correction(tmp_path):
    path = tmp_path / "corrections.json"
    path.write_text(json.dumps({"corrections": [{
        "work": "plato.apologia", "locus": "18",
        "original": ">ἐμοῦ", "correction": "ἐμοῦ",
        "expected_occurrences": 1, "evidence": "markup residue", "date": "2026-09-13",
    }]}), encoding="utf-8")
    rules = load_text_corrections(path)
    assert apply_text_corrections("plato.apologia", "18", "λέγω. >ἐμοῦ", rules) == "λέγω. ἐμοῦ"
    assert apply_text_corrections("plato.apologia", "19", "λέγω. >ἐμοῦ", rules) == "λέγω. >ἐμοῦ"


def test_control_count_refuses_a_rule_that_does_not_fire():
    rules = {("plato.apologia", "18"): [{
        "original": ">ἐμοῦ", "correction": "ἐμοῦ", "expected_occurrences": 1,
    }]}
    with pytest.raises(SystemExit, match="expected 1 occurrences.*found 0"):
        apply_text_corrections("plato.apologia", "18", "ἐμοῦ", rules)
