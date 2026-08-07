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
from validate_lemma_map import (closed_class_lemma,  # noqa: E402
                                grave_lemma_repair, particle_capture,
                                rejection_reason, to_acute, validate_cache)

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
    # Isolated too, or every test here reads whatever the last measurement run
    # wrote to data/capital_positions.json. The tests that want a fold set one.
    monkeypatch.setattr(vlm, "CAPITAL_FOLDS", {})
    # Same reason, and it matters more: grave_lemma_repair reads the printed-form
    # census, which is 1,059,268 real forms. Left alone, these fixtures would be
    # decided by the actual corpus rather than by the table each test sets up.
    # Empty makes the rule fall back to the frequency file the fixture writes;
    # the tests that are ABOUT printed forms set one explicitly.
    monkeypatch.setattr(vlm, "PRINTED_FORMS", {})
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
    groups its occurrences, so a downstream join on it still finds them, and
    dropping it would trade lemmatized tokens for a blank.

    This used to use τὸν, which is no longer an example of anything: the article
    is a closed paradigm, so closed_class_lemma settles it as ὁ without needing
    an attested acute headword.

    Χωρὶς now loses its CAPITAL here, which it did not before. The form the
    corpus printed is lowercase, so nothing in that occurrence licenses a
    capital, and that argument needs no frequency table. The grave survives,
    because the acute the rule wants is still unattested in this bench, and
    that is the limit this test is really about: the entry is repaired as far
    as the evidence goes and is not tombstoned."""
    cache = {"χωρὶς": "Χωρὶς"}
    repaired, dropped = validate_cache(cache, bench, label="test")
    assert cache == {"χωρὶς": "χωρὶς"}
    assert "χωρὶς" not in dropped


def test_a_capitalized_grave_lemma_reaches_its_acute_headword_in_one_pass(bench):
    """`Σοφιστὴς` carries both an unlicensed capital and a positional grave, and
    each one used to shield the other: the grave rule wanted an attested acute
    that the capitalized entry had swallowed the tokens of, and the capital rule
    wanted a frequency comparison the same swallowing made unwinnable. Lowercase
    first, then the grave rule, in one pass. Landing on `σοφιστὴς` and waiting
    for the next build would look like a rule that never fired."""
    freq_file = bench.parent / "freq2.tsv"
    freq_file.write_text("σοφιστής\t3151\n", encoding="utf-8")
    cache = {"σοφιστὴς": "Σοφιστὴς"}
    validate_cache(cache, freq_file, label="test")
    assert cache == {"σοφιστὴς": "σοφιστής"}


def test_the_relaxation_does_not_reach_a_proper_noun(bench):
    """The scope test, and the one that matters. Without the grave condition
    this branch reaches 6,936 cache entries and 250,061 tokens, lowercasing
    Φίλων, Μένων and Τύχη in a single build, which is what issue #19 exists to
    prevent. Neither of these carries a grave, so neither may move on that
    account."""
    cache = {"φίλων": "Φίλων", "ἀβραάμ": "Ἀβραάμ"}
    validate_cache(cache, bench, label="test")
    assert cache == {"φίλων": "Φίλων", "ἀβραάμ": "Ἀβραάμ"}


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


# --------------------------------------------------------------------------
# The article. Its whole paradigm was lemmatized to ὅς, the relative pronoun:
# 8,926,058 tokens, 13.4% of the corpus, and it made ὅς the published #1 lemma.

def test_the_article_paradigm_lemmatizes_to_ho():
    for form in ("ὁ", "ἡ", "οἱ", "αἱ", "τό", "τὸ", "τοῦ", "τῆς", "τῷ", "τῇ",
                 "τὸν", "τὴν", "τὰ", "τῶν", "τοῖς", "ταῖς", "τοὺς", "τὰς",
                 "τοῖν", "τὼ"):
        assert closed_class_lemma(form) == "ὁ", form


def test_the_relative_keeps_its_own_lemma():
    # the corpus had these partly the other way round: ἃ was on ὁ, οἳ on ἕ
    for form in ("ὅ", "ὃ", "ἥ", "ἣ", "οἵ", "οἳ", "αἵ", "ἅ", "ἃ"):
        assert closed_class_lemma(form) == "ὅς", form


def test_accent_separates_the_article_from_the_relative():
    """The one place in this module where accent is CONTRASTIVE rather than
    positional. The article is proclitic and unaccented; the relative carries an
    accent on the same letters. Every other rule here strips the accent as noise,
    and doing that would fuse exactly the pair this rule exists to separate."""
    assert closed_class_lemma("ὁ") == "ὁ" and closed_class_lemma("ὅ") == "ὅς"
    assert closed_class_lemma("ἡ") == "ὁ" and closed_class_lemma("ἥ") == "ὅς"
    assert closed_class_lemma("οἱ") == "ὁ" and closed_class_lemma("οἵ") == "ὅς"
    assert closed_class_lemma("αἱ") == "ὁ" and closed_class_lemma("αἵ") == "ὅς"


def test_the_tau_forms_are_matched_on_the_bare_skeleton():
    # no other Greek word is spelled τοῦ, so the OCR tail is safe to sweep in:
    # dropped diacritics, a lunate sigma, an editorial dot
    for form in ("το", "του", "τῆϲ", "ΤΟΥ", "Τὸ", "τῆν", "τ̣οῦ"):
        assert closed_class_lemma(form) == "ὁ", form


def test_toi_is_left_alone():
    """τοι is the particle far more often than it is Homer's τοί for οἱ, and
    14,498 occurrences is too many to guess at."""
    assert closed_class_lemma("τοι") is None
    assert closed_class_lemma("τοί") is None


def test_a_word_that_merely_starts_with_tau_is_untouched():
    for form in ("τότε", "τοῦτο", "τῆλε", "ταῦτα", "τῶνδε", "τις", "τίς"):
        assert closed_class_lemma(form) is None, form


def test_the_article_rule_runs_before_the_graded_checks(bench):
    """It needs no frequency evidence, so it must not be reachable by a rule
    that does. τὰ sat on τίς and Τὸ on τοτέ; both are settled by paradigm."""
    cache = {"τὰ": "τίς", "Τὸ": "τοτέ", "ἃ": "ὁ", "οἳ": "ἕ"}
    repaired, dropped = validate_cache(cache, bench, label="test")
    assert not dropped
    assert cache == {"τὰ": "ὁ", "Τὸ": "ὁ", "ἃ": "ὅς", "οἳ": "ὅς"}
    assert repaired == {"τὰ", "Τὸ", "ἃ", "οἳ"}


# --------------------------------------------------------------------------
# Elided stems the corpus vouches for. The length test could not decide the
# single letters: it excluded them all to keep γ̅, χ̅ and θ̅ out, and that cost δ
# its 281,109 occurrences to save a few hundred.

@pytest.fixture
def folds(monkeypatch):
    monkeypatch.setattr(vlm, "ELIDED_FOLDS", {"δ": "δέ", "μητ": "μήτε"})


def test_a_measured_elided_stem_folds_into_its_particle(folds):
    assert particle_capture("δ", "δ", FREQ) == "δέ"
    assert particle_capture("Δ", "δ", FREQ) == "δέ"
    assert particle_capture("μήτ", "μήτʼ", FREQ) == "μήτε"


def test_an_unmeasured_stem_does_not(folds):
    """γ is the numeral and the abbreviation mark more often than it is elided
    γάρ: 30.9% before an apostrophe, against δ's 87.3%."""
    for form in ("γ", "τ", "κ", "ι"):
        assert particle_capture(form, form, FREQ) is None, form


def test_the_fold_is_not_gated_on_the_lemma_being_unattested(folds):
    """The branch below it only fires when the proposed lemma is attested
    nowhere. δ IS attested, with exactly the 281,109 tokens that are the
    problem, so gating on that would leave it untouched."""
    freq = {**FREQ, "δ": 281_109, "δέ": 1_550_869}
    assert particle_capture("δ", "δ", freq) == "δέ"


def test_the_fold_is_a_no_op_once_correct(folds):
    assert particle_capture("δ", "δέ", FREQ) is None


def test_no_rates_file_means_no_folding(monkeypatch, tmp_path):
    """Same degradation as a missing frequency table: the rule goes quiet
    rather than guessing, so a fresh clone does not fold on stale evidence."""
    monkeypatch.setattr(vlm, "ELIDED_FOLDS", {})
    assert particle_capture("δ", "δ", FREQ) is None
    assert vlm.load_elision_rates(tmp_path / "absent.json") == {}


def test_an_ambiguous_stem_is_excluded_even_at_a_decisive_rate(tmp_path):
    """The rate proves a stem is elided, not what from. εἶτ (εἶτα) and εἴτ
    (εἴτε) split 2,375 to 2,168 and the skeleton has dropped what tells them
    apart, so a 97.7% rate must not be enough on its own."""
    rates = {"stems": {
        "ειτ": {"particle": "εἴτε", "rate": 0.977, "occurrences": 5096},
        "δ": {"particle": "δέ", "rate": 0.873, "occurrences": 261507},
    }}
    fp = tmp_path / "rates.json"
    fp.write_text(json.dumps(rates, ensure_ascii=False), encoding="utf-8")
    assert vlm.load_elision_rates(fp) == {"δ": "δέ"}
    assert "ειτ" in vlm.ELISION_AMBIGUOUS


def test_a_stem_below_the_threshold_is_excluded(tmp_path):
    rates = {"stems": {"τ": {"particle": "τε", "rate": 0.464, "occurrences": 43070}}}
    fp = tmp_path / "rates.json"
    fp.write_text(json.dumps(rates, ensure_ascii=False), encoding="utf-8")
    assert vlm.load_elision_rates(fp) == {}


def test_an_unbreathed_lowercase_vowel_is_not_a_word():
    """Numerals and letter names, which the lemmatizer read as the relative:
    α alone carried 26,785 tokens of ὅς (issue #18)."""
    for form in ("α", "ε", "η", "ι", "ο", "υ", "ω", "ὰ", "ό", "ᾱ", "ῑ", "ῳ"):
        assert vlm.unbreathed_vowel(form), form


def test_a_breathing_makes_it_a_word_again():
    """The rule turns on the breathing and nothing else, so every genuine
    one-letter Greek word has to survive it."""
    for form in ("ὁ", "ἡ", "ὅ", "ἥ", "ἤ", "ἢ", "ἦ", "ᾗ", "ᾧ", "ὦ", "ὢ", "ἃ",
                 "ἅ", "ὃ", "ἄ", "ἣ"):
        assert not vlm.unbreathed_vowel(form), form


def test_the_rule_stops_at_lowercase_and_at_one_letter():
    """Capitals drop the breathing as typography, so they are out of scope;
    and a consonant is out because elision can explain it (δ’ is δέ)."""
    for form in ("Α", "Η", "Ο", "Ω", "Ι"):
        assert not vlm.unbreathed_vowel(form), form
    for form in ("δ", "τ", "γ", "μ", "κ"):
        assert not vlm.unbreathed_vowel(form), form
    for form in ("αι", "ου", "ἀπ", "εν"):
        assert not vlm.unbreathed_vowel(form), form


def test_the_drop_survives_a_missing_frequency_table(tmp_path, monkeypatch):
    """It is a fact about Greek spelling, not a reading of the corpus, so it
    must hold on a fresh clone where the frequency table is not built yet, and
    it must be written down so the next build does not re-derive it."""
    monkeypatch.setattr(vlm, "REJECTED", tmp_path / "rejected.tsv")
    cache = {"α": "ὅς", "ο": "ὅς", "καὶ": "καί"}
    vlm.validate_cache(cache, freq_path=tmp_path / "absent.tsv")
    assert cache == {"καὶ": "καί"}
    assert set(vlm.load_rejected(tmp_path / "rejected.tsv")) == {"α", "ο"}


def test_a_positional_capital_folds_into_its_lowercase_twin(bench, monkeypatch):
    """Πῶς is mid-sentence 9.1% of the time, so the capital is the sentence
    opening and not the word (issue #19)."""
    monkeypatch.setattr(vlm, "CAPITAL_FOLDS", {"Πῶς": "πῶς"})
    cache = {"Πῶς": "Πῶς", "πῶς": "πῶς"}
    vlm.validate_cache(cache, bench, label="test")
    assert cache == {"Πῶς": "πῶς", "πῶς": "πῶς"}


def test_a_lexical_capital_is_left_alone(bench, monkeypatch):
    """The measurement keeps Θεός and Λέων out of the folds, and the rule must
    have no opinion of its own about a lemma that is not in there. Folding
    Λέων would put the emperor under the lion."""
    monkeypatch.setattr(vlm, "CAPITAL_FOLDS", {"Πῶς": "πῶς"})
    cache = {"Θεός": "Θεός", "Λέων": "Λέων"}
    vlm.validate_cache(cache, bench, label="test")
    assert cache == {"Θεός": "Θεός", "Λέων": "Λέων"}


def test_no_measurement_means_no_folding(tmp_path):
    """Same degradation as the elision rates and the frequency table: with
    nothing measured the rule goes quiet rather than lowercasing on a guess."""
    assert vlm.load_capital_folds(tmp_path / "absent.json") == {}


def test_the_fold_reads_the_measured_file(tmp_path):
    fp = tmp_path / "capitals.json"
    fp.write_text(json.dumps({"folds": {
        "Πῶς": {"folds_to": "πῶς", "mid_sentence_rate": 0.091, "occurrences": 8958},
    }}, ensure_ascii=False), encoding="utf-8")
    assert vlm.load_capital_folds(fp) == {"Πῶς": "πῶς"}


# --------------------------------------------------------------------------
# Attestation reads PRINTED forms, not a lemma table (issue #4).

def test_a_grave_lemma_repairs_when_the_corpus_prints_the_acute(bench, monkeypatch):
    """The argument is about the printed text, so the evidence is the printed
    text. `Καυνεύς` is a lemma in no table this repo builds, but the corpus
    prints it, and that is what licenses taking the grave off `Καυνεὺς`."""
    monkeypatch.setattr(vlm, "PRINTED_FORMS", {"Καυνεύς": 9})
    assert vlm.grave_lemma_repair("Καυνεὺς", {}) == "Καυνεύς"


def test_the_enclitic_guard_reads_the_same_table_as_the_test(bench, monkeypatch):
    """The guard is what keeps the indefinite τὶς out of the interrogative τίς,
    and it only works if it is evaluated on the table attestation came from. On
    a frequency table it would read 0 for everything the printed-form test newly
    reaches, and stop applying without failing."""
    monkeypatch.setattr(vlm, "PRINTED_FORMS", {"τίς": 23845, "τις": 109132})
    assert vlm.grave_lemma_repair("τὶς", {}) is None


def test_the_article_is_held_by_the_closed_class_path_not_by_attestation(bench):
    """It used to be attestation: `τόν` was absent from the lemma table the rule
    read, so the acute test failed. The corpus prints `τόν` tens of thousands of
    times, so under printed forms nothing in THIS rule keeps the article off its
    own accusative. closed_class_lemma does, ahead of every graded check."""
    assert vlm.closed_class_lemma("τὸν") == vlm.ARTICLE_LEMMA
    assert vlm.closed_class_lemma("τὴν") == vlm.ARTICLE_LEMMA


def test_a_form_printed_once_is_below_the_floor(bench, monkeypatch):
    """PRINTED_MIN mirrors the min-count the per-work table is built at, so a
    form rarer than that is not in the governed table to be repaired anyway."""
    import json
    fp = bench.parent / "lex.tsv"
    fp.write_text("σοφιστής\t1\n", encoding="utf-8")
    monkeypatch.setattr(vlm, "PRINTED_FORMS", vlm.load_printed_forms(fp))
    assert vlm.grave_lemma_repair("σοφιστὴς", {}) is None
