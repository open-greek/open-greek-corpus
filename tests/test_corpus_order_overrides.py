"""Reviewed corpus reading order is applied at build and artifact boundaries."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from corpus_order_overrides import apply_order_override  # noqa: E402


def spec():
    return {"suda.lexicon": {
        "component": 1,
        "order": ["Ο", "Π", "Ρ", "Σ", "Τ", "Ω"],
    }}


def test_omega_block_moves_after_tau_without_reordering_its_rows():
    rows = [
        {"locus": "3.Ο.1"},
        {"locus": "3.Ω.1"},
        {"locus": "3.Ω.2"},
        {"locus": "4.Π.1"},
        {"locus": "4.Ρ.1"},
        {"locus": "4.Σ.1"},
        {"locus": "4.Τ.1"},
    ]
    ordered, report = apply_order_override(
        "suda.lexicon", rows, spec(), lambda row: row["locus"])
    assert [row["locus"] for row in ordered] == [
        "3.Ο.1", "4.Π.1", "4.Ρ.1", "4.Σ.1", "4.Τ.1", "3.Ω.1", "3.Ω.2",
    ]
    assert report["before"] == ["Ο", "Ω", "Π", "Ρ", "Σ", "Τ"]
    assert report["after"] == ["Ο", "Π", "Ρ", "Σ", "Τ", "Ω"]


def test_unreviewed_division_fails_closed():
    with pytest.raises(SystemExit, match="unreviewed divisions.*Ψ"):
        apply_order_override(
            "suda.lexicon", [{"locus": "5.Ψ.1"}], spec(),
            lambda row: row["locus"])
