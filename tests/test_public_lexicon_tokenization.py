"""Regression coverage for public-lexicon elision boundaries.

The served text is preserved verbatim.  This test protects only the derived
frequency rollup that Dilemma consumes when deciding whether a form is attested.
"""

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_public_corpus import public_lexicon_tokens  # noqa: E402


def test_final_elisions_stay_attached_and_use_one_spelling():
    tokens = public_lexicon_tokens("δ’ κατ' δʼ ἀλλ᾽ ἐπ᾿ δι´ μεθ` καθ̓")

    assert tokens == ["δ’", "κατ’", "δ’", "ἀλλ’", "ἐπ’", "δι’", "μεθ’", "καθ’"]
    assert not {"δ", "κατ", "ἀλλ", "ἐπ", "δι", "μεθ", "καθ"} & set(tokens)


def test_mark_only_runs_do_not_become_forms_and_initial_aphaeresis_survives():
    tokens = public_lexicon_tokens("᾽ ᾿ ᾿ς ᾿κ γ᾽ρ")

    assert tokens == ["᾿ς", "᾿κ", "γ᾽ρ"]


def test_single_letter_mark_forms_are_never_reduced_to_bare_letters():
    tokens = public_lexicon_tokens("α' β’ δ' αʹ Ἦχος β'")

    assert tokens == ["α’", "β’", "δ’", "αʹ", "Ἦχος", "β’"]
    assert not {"α", "β", "δ"} & set(tokens)


def test_known_detached_elision_stems_are_not_lexical_evidence():
    tokens = public_lexicon_tokens(
        "δ ἀλλ δι καθ κατ παρ ἐπ ἐφ οὐδ ὑπ ἀπ μεθ τ τε περ"
    )

    assert tokens == ["τε", "περ"]
