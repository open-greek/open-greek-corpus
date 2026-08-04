"""Tests for the lemma-cache checks (scripts/validate_lemma_map.py).

These pin the distinctions that took three passes to get right. The cache put
294,404 occurrences of οὐ, the commonest negative in Greek, onto οὖον, a
service-berry, and published it at #27 in the top-30. Getting that out without
taking real words with it turns on one rule: accent is positional, so it cannot
tell two words apart, while breathing and iota subscript can.

Synthetic inputs throughout, so nothing here depends on the real corpus.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_lemma_map as vlm  # noqa: E402
from validate_lemma_map import (particle_capture,  # noqa: E402
                                rejection_reason, validate_cache)

# οὐ is enormous, οὖον is not; that gap is what condemns the capture.
FREQ = {"οὐ": 658_075, "οὖον": 205, "ἤ": 366_052, "εἰμί": 1_190_360,
        "ἀλλά": 373_725, "εὖ": 8_934, "ἕ": 400, "ὅς": 8_940_360, "καί": 3_756_282}


def test_the_particle_itself_is_its_own_lemma():
    # frequency gets no say: the conditional is not a form of "to be", however
    # enormous εἰμί is
    assert particle_capture("εἰ", "εἰμί", FREQ) == "εἰ"
    assert particle_capture("οὐ", "οὖον", FREQ) == "οὐ"
    assert particle_capture("οὐ", "οὐ", FREQ) is None


def test_accent_and_case_variants_reach_the_particle():
    # none of these is an attested lemma itself, so the homograph test never
    # sees them; between them they carried 32,779 occurrences
    for form in ("Οὐ", "οὔ", "οὖ", "οὒ", "Οὔ"):
        assert particle_capture(form, "οὖον", FREQ) == "οὐ", form


def test_a_variant_spelling_of_the_particle_is_normalized():
    # ἢ -> ἢ left the disjunctive split over two lemmas, neither a headword
    assert particle_capture("ἢ", "ἢ", FREQ) == "ἤ"


def test_breathing_and_subscript_are_lexical_and_block_the_repair():
    # each of these shares a deaccented skeleton with a particle and is a
    # different word: οὗ the relative, ᾗ/ῃ/ἧ datives and relatives, εὕ rough
    for form, lemma in (("Οὗ", "ὅς"), ("ᾗ", "ὅς"), ("ῃ", "ῃ"), ("ἧ", "ἧ")):
        assert particle_capture(form, lemma, FREQ) is None, form
    assert particle_capture("εὕ", "ἕ", FREQ) is None


def test_an_editorial_dot_below_does_not_block_the_repair():
    # the dot says the letter is uncertain, not that the word is another one;
    # blocking on it would strand the form unlemmatized
    assert particle_capture("οὐ̣", "οὖον", FREQ) == "οὐ"


def test_a_macron_or_diaeresis_does_block_it():
    # these look like noise and are not: a macron marks an abbreviation or a
    # numeral, a diaeresis breaks the diphthong. η̅ is not ἤ and ἔϋ is not εὖ.
    freq = {**FREQ, "η̅": 0, "ἔϋ": 0}
    assert particle_capture("η̅", "η̅", freq) is None
    assert particle_capture("ἔϋ", "ἔϋ", freq) is None


def test_a_homograph_digit_is_a_distinction_not_a_capture():
    assert particle_capture("Ὅτι", "ὅτι2", FREQ) is None


def test_genuine_homograph_survives_on_frequency():
    # ἦ really is a form of εἰμί, and εἰμί is enormous
    assert particle_capture("ἦ", "εἰμί", FREQ) is None


def test_service_berry_forms_keep_their_lemma():
    assert particle_capture("οὖα", "οὖον", FREQ) is None


def test_elided_stem_reaches_the_particle_only_as_a_plain_prefix():
    assert particle_capture("ἀλλ", "ἀλλ'", FREQ) == "ἀλλά"
    # εἶθ' is elided εἶτα, not εἴτε; the deaspiration branch used to claim it
    assert particle_capture("εἶθ", "εἴτα", FREQ) != "εἴτε"
    # single letters are scribal abbreviation marks, not elided particles
    assert particle_capture("γ", "γάρος", FREQ) is None


def test_capitalized_variant_of_the_form_is_rejected():
    freq = {**FREQ, "εὔνους": 606, "Εὔνους": 148}
    assert rejection_reason("εὔνους", "Εὔνους", freq) is not None


@pytest.fixture
def bench(tmp_path, monkeypatch):
    """A frequency table and an isolated tombstone file."""
    # κβ is attested as a lemma and κβʹ is attested nowhere, which is what makes
    # the mapping rejectable: the rule will not condemn a form it has never seen
    freq = {**FREQ, "κβ": 1_118, "βασκανία": 300, "Βασκανία": 6}
    freq_file = tmp_path / "freq.tsv"
    freq_file.write_text("\n".join(f"{k}\t{v}" for k, v in freq.items()) + "\n",
                         encoding="utf-8")
    monkeypatch.setattr(vlm, "REJECTED", tmp_path / "rejected.tsv")
    return freq_file


def test_validate_cache_reports_the_forms_it_dropped(bench):
    cache = {"οὐ": "οὖον", "Οὐ": "οὖον", "οὖα": "οὖον", "κβ": "κβʹ"}
    repaired, dropped = validate_cache(cache, bench, label="test")
    assert repaired == {"οὐ", "Οὐ"}
    assert cache["οὐ"] == "οὐ" and cache["Οὐ"] == "οὐ"
    assert cache["οὖα"] == "οὖον"          # the real service-berry form stays
    assert "κβ" in dropped and "κβ" not in cache


def test_a_capitalized_variant_is_repaired_to_the_form_not_dropped(bench):
    # 475 of 560 rejects were this, all ordinary words; dropping traded a wrong
    # lemma for no lemma
    cache = {"βασκανία": "Βασκανία"}
    repaired, dropped = validate_cache(cache, bench, label="test")
    assert repaired == {"βασκανία"} and not dropped
    assert cache["βασκανία"] == "βασκανία"


def test_a_drop_persists_across_runs(bench):
    """The whole point of the tombstone. A form absent from the cache looks
    never-lemmatized, so without a record the next run re-derives it, gets the
    same wrong answer from the same deterministic lemmatizer, and stores it."""
    cache = {"κβ": "κβʹ"}
    validate_cache(cache, bench, label="test")
    assert "κβ" not in cache
    # a later run: the form is gone, so there is nothing to drop, but the caller
    # still has to know not to re-derive it
    fresh: dict[str, str] = {}
    _, dropped = validate_cache(fresh, bench, label="test")
    assert "κβ" in dropped


def test_a_tombstoned_form_that_creeps_back_is_removed_again(bench, tmp_path):
    """The tombstone has to bite on its own, not only where the live rules
    happen to agree. The reference table is rebuilt every run, so a mapping
    condemned once can stop tripping any rule later - here κβʹ becomes attested,
    which is exactly what the unattested-target rule keyed on."""
    validate_cache({"κβ": "κβʹ"}, bench, label="test")

    softer = tmp_path / "freq2.tsv"
    softer.write_text(bench.read_text(encoding="utf-8") + "κβʹ\t900\n",
                      encoding="utf-8")
    assert rejection_reason("κβ", "κβʹ", vlm.load_lemma_frequencies(softer)) is None

    crept_back = {"κβ": "κβʹ"}
    _, dropped = validate_cache(crept_back, softer, label="test")
    assert "κβ" not in crept_back and "κβ" in dropped


def test_validate_cache_is_idempotent(bench):
    cache = {"οὐ": "οὖον", "Οὐ": "οὖον", "ἢ": "ἢ", "βασκανία": "Βασκανία"}
    validate_cache(cache, bench, label="test")
    again = dict(cache)
    repaired, _ = validate_cache(cache, bench, label="test")
    assert not repaired
    assert cache == again
