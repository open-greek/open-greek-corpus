"""Regression coverage for public-lexicon elision boundaries.

The served text is preserved verbatim.  This test protects only the derived
frequency rollup that Dilemma consumes when deciding whether a form is attested.
"""

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_public_corpus import (  # noqa: E402
    public_elision_stem_candidates,
    public_lexicon_tokenization,
    public_lexicon_tokens,
)


def test_final_elisions_stay_attached_and_use_one_spelling():
    tokens = public_lexicon_tokens("δ’ κατ' δʼ ἀλλ᾽ ἐπ᾿ δι´ μεθ` καθ̓")

    assert tokens == ["δ’", "κατ’", "δ’", "ἀλλ’", "ἐπ’", "δι’", "μεθ’", "καθ’"]
    assert not {"δ", "κατ", "ἀλλ", "ἐπ", "δι", "μεθ", "καθ"} & set(tokens)


def test_mark_only_runs_do_not_become_forms_and_initial_aphaeresis_survives():
    tokens = public_lexicon_tokens("᾽ ᾿ ᾿ς ᾿κ γ᾽ρ")

    assert tokens == ["᾿ς", "᾿κ", "γ᾽ρ"]


def test_numerals_are_audited_out_but_known_single_letter_elisions_survive():
    tokens, exclusions = public_lexicon_tokenization(
        "α' β’ δ' αʹ Ἦχος β' τ’ θ’ γ’ μ’ σ’ κ’ ῥ’ ιε’ κα’ ρκς’"
    )

    assert tokens == ["δ’", "Ἦχος", "τ’", "θ’", "γ’", "μ’", "σ’", "κ’", "ῥ’"]
    assert exclusions == {
        ("greek_numeral", "α’"): 2,
        ("greek_numeral", "β’"): 2,
        ("greek_numeral", "ιε’"): 1,
        ("greek_numeral", "κα’"): 1,
        ("greek_numeral", "ρκς’"): 1,
    }
    assert not {"α", "β", "δ"} & set(tokens)


def test_final_sigma_and_grave_before_mark_are_quotes_or_numerals_not_elisions():
    tokens, exclusions = public_lexicon_tokenization(
        "ἄνθρωπος’ ὡς’ ας’ ις’ ς’ κς’ λς’ καὶ’ ὅσ’ γλῶσσ’"
    )

    assert tokens == ["ὅσ’", "γλῶσσ’"]
    assert exclusions == {
        ("final_sigma_mark", "ἄνθρωπος’"): 1,
        ("final_sigma_mark", "ὡς’"): 1,
        ("final_sigma_mark", "ας’"): 1,
        ("final_sigma_mark", "ς’"): 1,
        ("greek_numeral", "ις’"): 1,
        ("greek_numeral", "κς’"): 1,
        ("greek_numeral", "λς’"): 1,
        ("grave_before_mark", "καὶ’"): 1,
    }


def test_known_detached_elision_stems_are_not_lexical_evidence():
    tokens = public_lexicon_tokens(
        "δ ἀλλ Ἀλλ ΠΑΡ δι καθ κατ παρ ἐπ ἐφ οὐδ ὑπ ἀπ μεθ τ "
        "ἄλλ ἔπ ἔφ ὕπ μέθ οὔδ δί δὶ τε περ ἄλλος"
    )

    assert tokens == ["τε", "περ", "ἄλλος"]


def test_accented_words_survive_except_for_reviewed_detached_stems():
    tokens = public_lexicon_tokens(
        "πὰρ πάρ Πάρ Πὰρ κὰτ κάτ Κάτ Δί Δὶ Διί Ἄλλ "
        "ἔπ’ ὕπ’"
    )

    assert tokens == [
        "πὰρ", "πάρ", "Πάρ", "Πὰρ", "κὰτ", "κάτ", "Κάτ", "Δί", "Δὶ", "Διί", "ἔπ’", "ὕπ’",
    ]


def test_numeral_places_do_not_exclude_real_elisions_or_promote_unvocalized_junk():
    tokens, exclusions = public_lexicon_tokenization("μηδ’ ποθ’ τσ’ ιε’ κδ’ λβ’")

    assert tokens == ["μηδ’", "ποθ’"]
    assert exclusions == {
        ("invalid_numeral_sequence", "τσ’"): 1,
        ("greek_numeral", "ιε’"): 1,
        ("greek_numeral", "κδ’"): 1,
        ("greek_numeral", "λβ’"): 1,
    }


def test_bare_elision_candidates_need_same_lemma_validation():
    candidates = public_elision_stem_candidates({
        "ἵν": 450,
        "ἵν’": 6861,
        "ἄν": 42523,
        "ἄν’": 128,
    })

    assert candidates == [("ἵν", 450, "ἵν’", 6861)]
