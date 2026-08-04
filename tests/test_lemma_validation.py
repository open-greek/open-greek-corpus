"""Tests for the lemma-cache checks (scripts/validate_lemma_map.py).

These pin the distinctions that took three passes to get right. The cache put
294,404 occurrences of οὐ, the commonest negative in Greek, onto οὖον, a
service-berry, and published it at #27 in the top-30. Getting that out without
taking real words with it turns on one rule: accent is positional, so it cannot
tell two words apart, while breathing and iota subscript can.

Synthetic inputs throughout, so nothing here depends on the real corpus.
"""

import gzip
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_lemma_map as vlm  # noqa: E402
from validate_lemma_map import (grave_lemma_repair,  # noqa: E402
                                particle_capture, rejection_reason, to_acute,
                                validate_cache)

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


# --------------------------------------------------------------------------
# The grave, generalized past the 19-word particle set. Same rule as ἢ -> ἤ,
# applied to any lemma: 9,821 of them in the cache, carrying 693,349 tokens.

# ξύν is attested and its grave twin is not; Ἐλπὶς has taken the tokens off
# Ἐλπίς; τόν does not exist as a lemma at all; τις and τίς are two words.
GRAVE_FREQ = {**FREQ, "ξύν": 20, "Ἐλπὶς": 1_100, "Ἐλπίς": 120,
              "τὸν": 610_395, "τις": 300_312, "τίς": 250_416}


def test_a_grave_lemma_is_repaired_to_its_attested_acute_headword():
    assert grave_lemma_repair("ξὺν", GRAVE_FREQ) == "ξύν"


def test_the_acute_headword_need_not_be_the_commoner_of_the_two():
    """The grave entry's count IS the tokens it took off the acute headword, so
    demanding the acute be commoner asks the split to heal before healing it.
    Ἐλπὶς holds 1,100 and Ἐλπίς 120, and they are one word."""
    assert grave_lemma_repair("Ἐλπὶς", GRAVE_FREQ) == "Ἐλπίς"


def test_an_unattested_acute_leaves_the_entry_alone():
    # τόν is nowhere in the table, and inventing it would only trade one
    # non-headword for another: the lemma of the article is the nominative
    assert grave_lemma_repair("τὸν", GRAVE_FREQ) is None


def test_the_enclitic_indefinite_is_not_merged_into_the_interrogative():
    """The one place a grave really does mark a distinct word. Editors print
    τὶς for the enclitic precisely to hold it apart from interrogative τίς, and
    the acute test cannot see it: τίς is attested and enormous. The corpus's own
    unaccented headword is what blocks it."""
    assert grave_lemma_repair("τὶς", GRAVE_FREQ) is None


def test_a_lemma_with_no_grave_is_never_touched():
    assert grave_lemma_repair("ὅς", GRAVE_FREQ) is None
    assert grave_lemma_repair("οὖον", GRAVE_FREQ) is None


def test_only_the_grave_moves():
    # a strip-and-reaccent would lose the subscript and the diaeresis, which are
    # lexical, and could land the accent on another syllable: ποτέ is "at some
    # time" and πότε is "when?"
    assert to_acute("ᾲ") == "ᾴ"
    assert to_acute("ῒ") == "ΐ"
    assert to_acute("ποτὲ") == "ποτέ"
    assert to_acute("οὗ") == "οὗ"


def test_the_repair_reaches_a_grave_lemma_under_any_form(bench):
    """The point of generalizing. particle_capture only ever saw forms whose own
    skeleton was a particle's, so καὶ as a LEMMA slipped past it on every form
    that was not itself καί: κάτα, καυτὸς, Κἀκείνων."""
    assert particle_capture("κάτα", "καὶ", vlm.load_lemma_frequencies(bench)) is None
    cache = {"κάτα": "καὶ"}
    repaired, _ = validate_cache(cache, bench, label="test")
    assert repaired == {"κάτα"} and cache["κάτα"] == "καί"


def test_a_grave_lemma_with_no_acute_headword_is_left_not_tombstoned(bench):
    """A grave lemma is the right WORD in the wrong citation form: it still
    groups its occurrences, so a downstream join on it still finds them. Dropping
    τὸν would trade 610,395 lemmatized tokens for a blank."""
    cache = {"τὸν": "τὸν"}
    repaired, dropped = validate_cache(cache, bench, label="test")
    assert cache == {"τὸν": "τὸν"}
    assert "τὸν" not in repaired and "τὸν" not in dropped


# --------------------------------------------------------------------------
# The fresh-clone hole: on a first build there is no cache, so validating only
# the cache validates nothing, and every lemma goes out unread.


def _fake_dilemma(answers: dict[str, str], asked: list | None = None):
    """A deterministic stand-in for the lemmatizer, answering "" for anything it
    does not know - which is what Dilemma does when it declines a form. Records
    what it was asked, because "do not re-derive a dropped form" is a claim
    about the questions, not just the answers."""
    mod = types.ModuleType("dilemma")

    class Dilemma:
        def __init__(self, lang=None):
            pass

        def lemmatize_batch(self, forms):
            if asked is not None:
                asked.extend(forms)
            return [answers.get(f, "") for f in forms]

    mod.Dilemma = Dilemma
    return mod


@pytest.fixture
def work_counts(tmp_path, monkeypatch):
    """build_work_lemma_counts pointed at a tmp tree with no lemma cache.

    Exactly what a first build sees: a corpus, no form->lemma cache, and the
    previous generation's frequency table as the reference.
    """
    import build_work_lemma_counts as bwlc
    data = tmp_path / "data"
    (data / "cache").mkdir(parents=True)
    (data / "corpus").mkdir()
    (data / "corpus" / "w.jsonl").write_text(
        json.dumps({"urn": "urn:cts:test", "text": "οὐ οὐ κβ κβ"},
                   ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "public_lemma_frequency.tsv").write_text(
        "οὐ\t658075\nοὖον\t205\nκβ\t1118\n", encoding="utf-8")
    for name, value in (("DATA", data), ("CORPUS", data / "corpus"),
                        ("CACHE", data / "cache"),
                        ("WORK_FORMS", data / "cache" / "work_forms"),
                        ("MANIFEST", data / "cache" / "manifest.json"),
                        ("LEMMA_CACHE", data / "cache" / "form_lemma.tsv.gz"),
                        ("LEMMA_META", data / "cache" / "form_lemma_meta.json")):
        monkeypatch.setattr(bwlc, name, value)
    monkeypatch.setattr(vlm, "DATA", data)
    monkeypatch.setattr(vlm, "REJECTED", data / "cache" / "lemma_rejected.tsv")
    monkeypatch.setattr(sys, "argv", ["build_work_lemma_counts.py"])
    return bwlc, data


def _published(data: Path) -> set[str]:
    with gzip.open(data / "work_lemma_counts.tsv.gz", "rt", encoding="utf-8") as f:
        return {line.rstrip("\n").split("\t")[1] for line in f}


def test_a_first_build_checks_what_the_lemmatizer_just_returned(work_counts,
                                                                monkeypatch):
    """validate_cache used to run under `if lemma_cache:` and before
    lemmatize_local, so on an empty cache it never ran and nothing checked the
    lemmatizer. οὐ -> οὖον would have been published again from a clean clone,
    with the validator sitting right there in the pipeline."""
    bwlc, data = work_counts
    monkeypatch.setattr(bwlc, "lemmatize_local",
                        lambda forms, cache: cache.update(
                            {f: "οὖον" for f in forms if f == "οὐ"}))
    bwlc.main()
    assert _published(data) == {"οὐ"}


def test_a_first_build_still_honors_the_tombstones(work_counts, monkeypatch):
    """The other half of the same hole: skipping validation skipped the load of
    lemma_rejected.tsv, so every form ever rejected was handed straight back to
    the lemmatizer, which is deterministic and says the same thing again."""
    bwlc, data = work_counts
    (data / "cache" / "lemma_rejected.tsv").write_text(
        "κβ\tproposed lemma occurs nowhere in the corpus\n", encoding="utf-8")
    asked = []

    def fake(forms, cache):
        asked.extend(forms)
        cache.update(dict.fromkeys(forms, "κβʹ"))

    monkeypatch.setattr(bwlc, "lemmatize_local", fake)
    bwlc.main()
    assert "κβ" not in asked         # never re-derived, not merely re-dropped
    assert "κβʹ" not in _published(data)


@pytest.fixture
def freq_build(tmp_path, monkeypatch):
    """build_lemma_frequency with a lexicon, a reference table and no cache."""
    import build_lemma_frequency as blf
    data = tmp_path / "data"
    (data / "cache").mkdir(parents=True)
    (data / "public_lexicon.tsv").write_text("οὐ\t658075\nκβ\t1118\n",
                                             encoding="utf-8")
    (data / "public_lemma_frequency.tsv").write_text(
        "οὐ\t658075\nοὖον\t205\nκβ\t1118\n", encoding="utf-8")
    monkeypatch.setattr(blf, "DATA", data)
    monkeypatch.setattr(vlm, "DATA", data)
    monkeypatch.setattr(vlm, "REJECTED", data / "cache" / "lemma_rejected.tsv")
    monkeypatch.setattr(sys, "argv", ["build_lemma_frequency.py"])
    return blf, data


def test_a_first_frequency_build_checks_the_new_lemmas(freq_build, monkeypatch):
    blf, data = freq_build
    monkeypatch.setitem(sys.modules, "dilemma", _fake_dilemma({"οὐ": "οὖον"}))
    blf.main()
    published = dict(line.split("\t") for line in
                     (data / "public_lemma_frequency.tsv").read_text(
                         encoding="utf-8").splitlines())
    assert "οὖον" not in published
    assert published["οὐ"] == "658075"


def test_a_first_frequency_build_does_not_re_derive_a_tombstoned_form(
        freq_build, monkeypatch):
    """Same hole, same file: `if cache:` meant a first build never opened
    lemma_rejected.tsv, so a form rejected on the last machine went back through
    the transformer here and came out with the same wrong lemma."""
    blf, data = freq_build
    (data / "cache" / "lemma_rejected.tsv").write_text(
        "κβ\tproposed lemma occurs nowhere in the corpus\n", encoding="utf-8")
    asked = []
    monkeypatch.setitem(sys.modules, "dilemma",
                        _fake_dilemma({"οὐ": "οὐ", "κβ": "κβʹ"}, asked))
    blf.main()
    assert "κβ" not in asked
    assert "κβʹ" not in (data / "public_lemma_frequency.tsv").read_text(
        encoding="utf-8")


def test_a_form_the_lemmatizer_declined_is_not_tombstoned(freq_build,
                                                          monkeypatch):
    """An empty lemma is Dilemma saying nothing, not saying something wrong. It
    is the negative-cache row that stops the form being recomputed every run, so
    it is held out of the checks - the unattested-target rule reads it as a
    lemma occurring nowhere and would tombstone every one of them."""
    blf, data = freq_build
    monkeypatch.setitem(sys.modules, "dilemma", _fake_dilemma({"οὐ": "οὐ"}))
    blf.main()
    rejected = data / "cache" / "lemma_rejected.tsv"
    assert not rejected.exists() or "κβ" not in rejected.read_text(encoding="utf-8")
    assert "κβ\t\n" in (data / "cache" / "lemma_cache.tsv").read_text(
        encoding="utf-8")


def test_a_tombstone_applies_without_the_frequency_table(bench, tmp_path):
    """The tombstone sweep used to sit below the early return for a missing
    reference table, and public_lemma_frequency.tsv is a build product: on a
    clone that had not built it yet, every rejected form walked back in."""
    validate_cache({"κβ": "κβʹ"}, bench, label="test")   # records the tombstone
    cache = {"κβ": "κβʹ"}
    _, dropped = validate_cache(cache, tmp_path / "not-built-yet.tsv",
                                label="test")
    assert "κβ" not in cache and "κβ" in dropped
