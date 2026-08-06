#!/usr/bin/env python3
"""Reject lemma-map entries that would overwrite a good lemma with a bad one.

data/lemma_map.tsv is produced by running dilemma over the forms the local cache
could not resolve, on a GPU box, and shipping the result back. Anything the
lemmatizer got wrong out there arrives here as a plain form/lemma pair with no
confidence attached, and build_work_lemma_counts.py used to merge it into the
cache unconditionally - so one bad row silently reassigns every occurrence of a
form. `οὐ -> οὖον` would move 658,075 occurrences of the commonest negative in
Greek onto a service-berry.

Four signatures, all measured against the corpus's own lemma frequencies:

  homograph capture   the form is itself an attested lemma (>= --min-lemma
                      occurrences) and the map proposes a different one. οὐ, εἰ,
                      αὖ, εὖ are the whole closed-class particle set here.
  particle variant    the form is a closed-class particle under a different
                      accent or case - `Οὐ`, `οὔ`, `καἰ`, `ὦς`, `δἐ` - and the
                      proposed lemma is far rarer than the particle. Testing the
                      exact form is not enough: the accented and capitalized
                      variants are not themselves attested lemmas, so they slip
                      the homograph test and carry most of the damage. This one
                      repairs rather than rejects, since a closed-class word is
                      its own lemma by definition.
  grave lemma         the proposed LEMMA carries a grave, which no headword
                      does, and the acute counterpart is attested - `ξὺν -> ξύν`,
                      `ἓξ -> ἕξ`, `ὁτὲ -> ὁτέ`. The particle rule reached 19
                      words under one accent; this reaches any word under the
                      one accent that is never lexical. Repairs, for the same
                      reason: a positional accent cannot be part of a headword.
  capitalization      the proposed lemma is the form's own capitalized variant
                      and the lowercase lemma is commoner - εὔλογος -> Εὔλογος,
                      ἰατρικός -> Ἰατρικός, βασιλίς -> Βασιλίς. The same
                      capitalized/lowercase confusion the OCR correctors had.
  unattested target   the proposed lemma occurs nowhere in the corpus at all
                      (κβ -> κβʹ, οὕστ -> ουστ, ἀνωτάτω -> ἄνω2).

Reports by default; --write emits a filtered map. Nothing is deleted silently:
every rejected row is listed with the counts that condemned it.

  python3 scripts/validate_lemma_map.py
  python3 scripts/validate_lemma_map.py --write data/lemma_map.tsv

Both lemma pipelines call validate_cache() below on their persistent form->lemma
cache at load, because filtering the incoming map does not help a cache that is
already poisoned: the merge fills gaps and never overrides, so a bad entry that
got in before the checks existed can never be displaced by a good one. They call
it a second time on whatever the lemmatizer newly derived, because a check that
only reads the cache checks nothing on a first build.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# Closed-class function words are their own lemma, always. Frequency alone cannot
# defend them: ei -> eimi looks unremarkable because eimi is enormous, yet the
# conditional particle is not a form of "to be". Kept deliberately short - only
# words whose lemma is not in genuine doubt.
PARTICLES = {"οὐ", "εἰ", "αὖ", "εὖ", "μέν", "δέ", "γάρ", "τε", "ἄν", "μή",
             "ἤ", "ὡς", "εἴτε", "οὔτε", "μήτε", "ἀλλά", "καί", "ἵνα", "ὅτι"}


def deaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if not unicodedata.combining(c))


def is_elided(form: str, lemma: str) -> bool:
    """True if `form` is the elided stem of `lemma` - hin' for hina.

    These are the entries the map exists to supply, and they trip the
    homograph test hardest: an elided form acquires spurious lemma status of its
    own precisely BECAUSE nothing has mapped it yet, so `hin` shows 6,517
    occurrences "as a lemma" and the row that fixes that looks like the rows
    that break things.
    """
    a = "".join(c for c in unicodedata.normalize("NFD", form.lower())
                if not unicodedata.combining(c))
    b = "".join(c for c in unicodedata.normalize("NFD", lemma.lower())
                if not unicodedata.combining(c))
    if len(a) >= len(b):
        return False
    if b.startswith(a):
        return True
    deasp = {"θ": "τ", "φ": "π", "χ": "κ"}
    return bool(a) and a[-1] in deasp and b.startswith(a[:-1] + deasp[a[-1]])


def lower_initial(s: str) -> str:
    d = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", d[0].lower() + d[1:]) if d else s


# Skeleton -> canonical particle, so accent and case variants resolve too.
PARTICLE_BY_SKELETON = {deaccent(p): p for p in sorted(PARTICLES)}

# Accent is positional - the grave appears only before a pause - so it cannot
# distinguish two words. Breathing and iota subscript can, and do: ὁ/ὀ, ἡ/ἠ,
# οὗ against οὐ. So the accent comes off and they stay on.
OXIA, VARIA, PERISPOMENI = "́", "̀", "͂"
_ACCENTS = {OXIA, VARIA, PERISPOMENI}
# The editorial dot below says the letter is uncertain, not that the word is a
# different one, so it is ignored - otherwise `οὐ̣` never reaches οὐ. Everything
# else stays significant, and deliberately so: a macron marks an abbreviation or
# a numeral (`η̅` is not ἤ) and a diaeresis breaks a diphthong (`ἔϋ` is not εὖ).
# Both look like noise and are not. Leaving such a form unlemmatized costs less
# than merging it into the wrong lemma.
_IGNORABLE = {"̣"}                  # U+0323 combining dot below


PSILI, DASIA = "̓", "̔"              # U+0313, U+0314
_LOWER_VOWELS = set("αεηιουω")
NOT_A_WORD = "a single unbreathed vowel, so a numeral or a letter name"


def unbreathed_vowel(form: str) -> bool:
    """True if `form` is one lowercase vowel carrying no breathing.

    Such a form cannot be a Greek word, and the argument needs no appeal to
    frequency. A word that begins with a vowel takes a breathing, and a
    one-letter word is all beginning; lowercase type always writes it. Nor can
    the missing breathing be blamed on elision, the usual reason a stray letter
    is a real word after all: elision drops the FINAL vowel and leaves a
    consonant behind, so `δ’` is a word and a bare vowel never is.

    What these actually are is Greek numerals, which are written as letters, and
    the letter names cited in the grammarians. The lemmatizer read them as
    words: `α` was 26,785 tokens of the relative ὅς, `ο` another 14,314, `η`
    12,199, on 120,837 tokens over 101 forms (issue #18). That is the same
    mistake as the article filed under ὅς - a breathing that decides the word
    being treated as noise - and it is refused the same way.

    Capitals are deliberately excluded even though most of them are numerals
    too. Display capitals drop the breathing as a matter of typography, so
    `Η` in a heading may well be ἤ, and 3,159 of the 42,140 capital cases sit in
    all-caps rows where that is exactly what has happened. Lowercase admits no
    such exception, so the rule stops where the evidence does.
    """
    d = unicodedata.normalize("NFD", form)
    base = [c for c in d if not unicodedata.combining(c)]
    return (len(base) == 1 and base[0] in _LOWER_VOWELS
            and PSILI not in d and DASIA not in d)


def unaccent(s: str) -> str:
    """Lowercase, accent stripped, breathing and iota subscript kept.

    Recomposed to NFC because the only thing this is looked up in is the
    frequency table, and that table is NFC: build_work_lemma_counts.py
    normalizes every token to NFC before counting it. Decomposed output would
    miss every entry whose breathing or subscript survives the strip.
    """
    return unicodedata.normalize("NFC", "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if not (unicodedata.combining(c) and c in _ACCENTS)))


def _particle_compatible(form: str, particle: str) -> bool:
    """True if `form` can be an accent or case variant of `particle`.

    A form may be MISSING a breathing or subscript the particle has - OCR drops
    them, and an all-caps heading never had them - but it may not carry a
    different one. That is what keeps `οὗ` off `οὐ`, `εὕ` off `εὖ`, and `ᾗ`,
    `ῃ`, `ἧ` off `ἤ`, all of which share a deaccented skeleton with a particle
    while being other words entirely.
    """
    if deaccent(form) != deaccent(particle):
        return False
    lex = lambda s: {c for c in unicodedata.normalize("NFD", s.lower())  # noqa: E731
                     if unicodedata.combining(c)
                     and c not in _ACCENTS and c not in _IGNORABLE}
    return lex(form) <= lex(particle)


def particle_capture(form: str, lemma: str, freq: dict[str, int],
                     rarer_by: int = 20) -> str | None:
    """The closed-class particle `form` belongs to, when `lemma` is not it.

    A closed-class word is its own lemma, so the answer for these is known and
    the entry is repaired rather than dropped. Dropping would be its own bug:
    `εἰ -> εἰμί` and `ἀλλ -> ἀλλ'` alone carry 349,084 occurrences, and rejecting
    them without supplying the right lemma just moves the damage into coverage.

    Three ways a form reaches a particle:

    the particle itself   `εἰ -> εἰμί`. The conditional is not a form of "to
                          be", however enormous εἰμί is, so frequency gets no
                          say here.
    an accent/case variant
                          `Οὐ`, `οὔ`, `οὖ`, `καἰ`, `ὦς`, `δἐ`. These are not
                          attested lemmas themselves, so the homograph test
                          never sees them, and they carried 32,779 of the
                          294,404 occurrences that ended up on a service-berry
                          (`οὐ` carried the other 261,120). Frequency does get a
                          say, or this would swallow every genuine homograph
                          sharing a skeleton with a particle: `ἦ` really is a
                          form of `εἰμί`, and εἰμί is enormous, so it survives.
                          A trailing homograph digit is a deliberate
                          distinction, so `Ὅτι -> ὅτι2` is left alone.
    the elided stem       `ἀλλ -> ἀλλ'`, where the proposed lemma is the
                          apostrophe form and is attested nowhere. Only taken
                          when the target is unattested, so a real lemma is
                          never overridden by this route.

    The elided route deliberately uses a stricter test than `is_elided`: a plain
    prefix of at least two letters. Allowing the deaspiration branch turns `εἶθ`
    into `εἴτε` when it is elided `εἶτα` (35,420 occurrences, and a lemma in its
    own right), and allowing single letters turns the scribal abbreviation marks
    `θ̅`, `χ̸`, `Ϊ` into particles. Those are better left unlemmatized.
    """
    if form in PARTICLES:
        return None if lemma == form else form
    skeleton = deaccent(form)
    particle = PARTICLE_BY_SKELETON.get(skeleton)
    if particle and deaccent(lemma) != skeleton \
            and deaccent(lemma.rstrip("0123456789")) != deaccent(particle) \
            and _particle_compatible(form, particle) \
            and freq.get(lemma, 0) * rarer_by < freq.get(particle, 0):
        return particle
    # The lemma is already a variant spelling of the particle rather than the
    # particle: `ἢ -> ἢ` leaves the disjunctive split over two lemmas, 351,791
    # occurrences under the grave and 13,243 under the acute, neither of which is
    # a dictionary form. Frequency gets no say here - the lemma IS the particle,
    # spelled wrong - but the breathing must agree, or this swallows `οὗ`.
    if particle and lemma != particle and deaccent(lemma) == skeleton \
            and _particle_compatible(form, particle):
        return particle
    # An elided stem the corpus itself vouches for. This branch exists because
    # the length test below cannot decide the single letters: it excludes them
    # all to keep the abbreviation marks γ̅, χ̅ and θ̅ out, and that costs δ its
    # 281,109 occurrences to save a few hundred. The page settles it instead -
    # δ is written before an apostrophe 87.3% of the time and γ 30.9% - and
    # scripts/measure_elision_rates.py is where that comes from.
    #
    # Not gated on the lemma being unattested, unlike the branch below. δ IS
    # attested as a lemma, with the 281,109 tokens that are the whole problem;
    # an attested wrong answer is still wrong, and the apostrophe is better
    # evidence than the absence of a frequency entry.
    folded = ELIDED_FOLDS.get(skeleton)
    if folded and folded != lemma:
        return folded
    if freq.get(lemma, 0) == 0 and len(skeleton) >= 2:
        elided = [p for p in PARTICLES
                  if deaccent(p).startswith(skeleton) and deaccent(p) != skeleton]
        if len(elided) == 1 and elided[0] != lemma:
            return elided[0]
    return None


def to_acute(s: str) -> str:
    """`s` with every grave rewritten as an acute and nothing else touched.

    Deliberately not unaccent-then-reaccent. The grave is the one mark in the
    string that carries no lexical information, so it is the only one allowed to
    move: stripping the rest would collapse ᾗ, ῃ and ἧ onto ἤ and οὗ onto οὐ,
    which is the merge _particle_compatible exists to refuse. Rewriting in place
    also leaves the accent on the syllable it was already on, so `ποτὲ` becomes
    ποτέ ("at some time") and can never reach πότε ("when?").
    """
    return unicodedata.normalize(
        "NFC", unicodedata.normalize("NFD", s).replace(VARIA, OXIA))


def grave_lemma_repair(lemma: str, freq: dict[str, int]) -> str | None:
    """The acute headword a grave-accented lemma stands for, or None to leave it.

    No dictionary headword carries a grave. The grave is what a final acute
    becomes when the word is not before a pause, so it records the word's
    neighbors, not the word, and PARTICLES was only ever a 19-word sample of a
    class that runs to 9,821 lemmas and 693,349 tokens in the current cache.
    9,739 of the 9,927 entries in that class are the lemmatizer echoing the
    surface form straight back (form == lemma), which splits a headword's tokens
    over two entries exactly as `ἢ` split the disjunctive. (Every count in this
    docstring is over the forms a build actually lemmatizes, corpus count >= 2,
    so they can be reproduced against public_lexicon.tsv. The whole cache,
    hapax forms included, holds 14,882 such entries.)

    Repaired only where the corpus supplies the headword itself: the acute
    counterpart must already be attested. That is the only positive evidence
    going, because the frequency table is generated from these same caches, so a
    grave lemma that has swallowed every token of its word looks impeccably
    attested while its acute counterpart sits at zero for want of anything left
    to carry - `τὸν` 610,395 against `τόν` 0. Attestation repairs 334 of the
    9,821 lemmas and 16,330 tokens; the other 9,487 lemmas and 677,019 tokens
    are left.

    Requiring the acute to be COMMONER as well is the obvious extra safeguard,
    and it is wrong here for the same reason it is wrong for `ἢ` above: the
    grave entry's count IS the tokens it took off the acute headword, so that
    test asks a split to have healed itself before it may be healed. It costs
    141 lemmas and 6,112 tokens, every one of them the same word listed twice
    (`᾿Αβραὰμ` 201 beside `᾿Αβραάμ` 122, `Ἐλπὶς` 1,100 beside `Ἐλπίς` 120,
    `Πολιτικὸς` 357 beside `Πολιτικός` 23), and leaves them split for good.

    Leaving beats tombstoning for the 9,487 with no attested acute. A grave
    lemma is the right WORD in the wrong citation form, so it still groups its
    occurrences correctly and every downstream join on it still returns the
    right passages, unlike `οὐ -> οὖον` or `κβ -> κβʹ` where the tokens land on
    a different word entirely. Tombstoning `τὸν` alone would trade 610,395
    lemmatized tokens for nothing better than a blank.

    One place a grave genuinely marks a distinct word, and the reason for the
    last test: editors print `τὶς` for the enclitic indefinite precisely to hold
    it apart from the interrogative `τίς`, and the two are separate headwords
    (τις 300,312, τίς 250,416). The acute test cannot see that, since τίς is
    attested and enormous. The corpus's own unaccented headword can: where one
    exists and is the commoner reading, the grave is doing lexical work and the
    entry is left alone. It costs 34 repairs worth 364 tokens, all of them OCR
    shrapnel (`χὰρ` 164, `ριστὸν` 28, `χροὺς` 23), to keep the indefinite
    pronoun out of the interrogative.

    What this does NOT reach: the article. `τὸν` is doubly wrong, since the
    lemma of the article is the nominative, and taking the grave off leaves
    `τόν`, an accusative that is no more a headword than `τὸν` was. So the acute
    is unattested and the entry is left, deliberately. The rest of the article's
    paradigm sits under ὅς in this cache (`τὸ`, `τὴν`, `τοὺς`, and ὁ itself),
    which makes ὅς the only lemma the data would support, and inferring it from
    a paradigm this rule cannot see is a different rule with a different way of
    being wrong. It is not invented here.
    """
    if VARIA not in unicodedata.normalize("NFD", lemma):
        return None
    acute = to_acute(lemma)
    a_freq = freq.get(acute, 0)
    if a_freq == 0:              # nothing attested to repair TO: `τὸν`
        return None
    if freq.get(unaccent(lemma), 0) > a_freq:   # the enclitic: `τὶς` under τις
        return None
    return acute


# This one has a known right answer rather than only a wrong one, so callers
# repair it instead of dropping: if the proposed lemma is just the form
# capitalized, the lemma is the form. 475 of the 560 rejects in the cache were
# this, all ordinary words - ἀπόγονος, ἀκόλαστος, εὐσχήμων - and dropping them
# traded a wrong lemma for no lemma.
ELISION_RATES = DATA / "elision_rates.json"
# The gap the measurement leaves: δ at 87.3%, then ἵνα's stem at 67.7% and τε's
# at 46.4%. Nothing lands between, so the threshold is not a tuned number.
ELIDED_MIN_RATE = 0.80

# A decisive rate proves a stem stands elided. It does not prove what it is
# elided FROM, and the skeleton these rates are keyed on has already dropped the
# accent and the breathing that decide it. Measured spellings, from
# `spellings_when_elided` in the rates file:
#
#   ειτ  εἶτ 2,375 against εἴτ 2,168 - εἶτα and εἴτε, near enough an even split
#   οτ   ὅτ 567 - that is elided ὅτε, and ὅτε is not the particle ὅτι
#   ουτ  οὔτ 1,499 with οὕτ and οὗτ behind it, so οὕτω is in the same skeleton
#   αλλ  ἀλλ 31,595 with ἄλλ and Ἄλλ at 1,165 - ἄλλος, a different word
#
# Each is left alone despite clearing the rate. δ is the one stem that is both
# decisive and single-lexeme: 227,571 δ and 744 Δ, nothing else.
ELISION_AMBIGUOUS = {
    "ειτ": "εἶτα and εἴτε share the skeleton and split almost evenly",
    "οτ": "ὅτ' is elided ὅτε, not the particle ὅτι",
    "ουτ": "οὕτω shares the skeleton with οὔτε once the breathing is gone",
    "αλλ": "ἄλλος shares the skeleton with ἀλλά; the accented form is handled "
           "by the elided-prefix branch of particle_capture instead",
}


def load_elision_rates(path: Path | None = None) -> dict[str, str]:
    """Bare stem -> the particle it folds into, for the stems the corpus says
    are elided. Empty when the measurement has not been run, which is the same
    shape of degradation as a missing frequency table: the rule goes quiet
    rather than guessing.
    """
    path = path or ELISION_RATES
    if not path.exists():
        return {}
    stems = json.loads(path.read_text(encoding="utf-8")).get("stems", {})
    return {stem: r["particle"] for stem, r in stems.items()
            if r.get("rate", 0) >= ELIDED_MIN_RATE and stem not in ELISION_AMBIGUOUS}


# Loaded once. A test that wants a different set monkeypatches this.
ELIDED_FOLDS = load_elision_rates()

CAPITAL_POSITIONS = DATA / "capital_positions.json"


def load_capital_folds(path: Path | None = None) -> dict[str, str]:
    """Capitalized lemma -> its lowercase twin, for the capitals the corpus
    says are only positional. Empty when the measurement has not been run, the
    same quiet degradation as the elision rates.

    scripts/measure_capital_positions.py decides which those are, by the same
    argument the grave accent gets: a capital at the head of a sentence is put
    there by the position, so it says nothing about the word, while one in the
    middle of a sentence has nothing but the word to explain it. Θεός is
    mid-sentence 97.8% of the time and stays; Πῶς 9.1% and folds.
    """
    path = path or CAPITAL_POSITIONS
    if not path.exists():
        return {}
    folds = json.loads(path.read_text(encoding="utf-8")).get("folds", {})
    return {cap: r["folds_to"] for cap, r in folds.items()}


CAPITAL_FOLDS = load_capital_folds()


ARTICLE_LEMMA, RELATIVE_LEMMA = "ὁ", "ὅς"

# The definite article, whose whole paradigm was lemmatized to ὅς, the relative
# pronoun: 8,926,058 tokens, 13.4% of the corpus, and it made ὅς the published
# #1 lemma. The relative went the other way in places - ἃ to ὁ, οἳ to ἕ - so the
# two were partly swapped rather than merged.
#
# Both are closed class, so the answer is known and needs no frequency evidence,
# the same ground the particle rule stands on. What is different here, and what
# the rest of this module must not be allowed to do to it, is that ACCENT IS
# CONTRASTIVE between the two: the article is proclitic and unaccented, ὁ ἡ οἱ
# αἱ, while the relative carries an accent on the same letters, ὅ ἥ οἵ αἵ. Every
# other rule in this file strips the accent as positional noise, and doing that
# here would fuse the pair it exists to separate. So the vowel-initial forms are
# matched EXACTLY, in both cases, and nothing else.
_ARTICLE_EXACT = set("ὁ Ὁ ἡ Ἡ οἱ Οἱ αἱ Αἱ".split())
_RELATIVE_EXACT = set("ὅ Ὅ ὃ Ὃ ἥ Ἥ ἣ Ἣ οἵ Οἵ οἳ Οἳ αἵ Αἵ αἳ Αἳ ἅ Ἅ ἃ Ἃ".split())

# The tau forms have no such twin - no other Greek word is spelled τοῦ or τὴν -
# so they can be matched on the bare skeleton, which is what reaches the OCR
# tail: `το`, `του` with the diacritics dropped, `τῆϲ` with a lunate sigma.
# τοι is deliberately absent. It is the particle far more often than it is
# Homer's τοί for οἱ, and 14,498 occurrences is too many to guess at.
def _sigma(s: str) -> str:
    return s.replace("ς", "σ").replace("ϲ", "σ").replace("Ϲ", "σ")


# Normalized on the way in, or the half of the paradigm that ends in a sigma
# never matches: the skeletons are compared sigma-folded, and an entry written
# with the word-final ς is not.
_ARTICLE_TAU = {_sigma(f) for f in
                ("το", "του", "της", "τω", "τη", "τον", "την", "τα", "των",
                 "τοις", "ταις", "τους", "τας", "τοιν")}


def closed_class_lemma(form: str) -> str | None:
    """ὁ for a form of the article, ὅς for one of the relative, else None."""
    if form in _ARTICLE_EXACT:
        return ARTICLE_LEMMA
    if form in _RELATIVE_EXACT:
        return RELATIVE_LEMMA
    if _sigma(deaccent(form)) in _ARTICLE_TAU:
        return ARTICLE_LEMMA
    return None


CAPITALIZED_VARIANT = "capitalized variant of the form itself"


def rejection_reason(form: str, lemma: str, freq: dict[str, int],
                     min_lemma: int = 1000) -> str | None:
    """Why this form -> lemma pair must not stand, or None if it may."""
    f_as_lemma, l_freq = freq.get(form, 0), freq.get(lemma, 0)
    if lemma != lower_initial(lemma) and lower_initial(lemma) == form \
            and f_as_lemma > l_freq:
        return CAPITALIZED_VARIANT
    if form in PARTICLES and lemma not in PARTICLES:
        return "closed-class particle reassigned to another lemma"
    if (f_as_lemma >= min_lemma and l_freq * 20 < f_as_lemma
            and not is_elided(form, lemma)
            and deaccent(form) != deaccent(lemma)):
        return "common form assigned a far rarer lemma"
    if l_freq == 0 and f_as_lemma:
        return "proposed lemma occurs nowhere in the corpus"
    return None


def load_lemma_frequencies(path: Path) -> dict[str, int]:
    freq: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[1].isdigit():
            freq[p[0]] = int(p[1])
    return freq


REJECTED = DATA / "cache" / "lemma_rejected.tsv"


def load_rejected(path: Path | None = None) -> dict[str, str]:
    """Forms whose lemma was rejected, and why. Persistent on purpose.

    A drop that lives only for the run that made it is not a drop: the form
    leaves the cache, the next run sees it as never-lemmatized, hands it back to
    the deterministic lemmatizer, and gets the same wrong answer. `βασκανία ->
    Βασκανία` came back that way after being dropped twice. Delete this file
    alongside the caches after a Dilemma upgrade, so a better model gets to
    re-answer.
    """
    path = path or REJECTED
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        form, sep, reason = line.partition("\t")
        if sep:
            out[form] = reason
    return out


def save_rejected(rejected: dict[str, str], path: Path | None = None) -> None:
    path = path or REJECTED
    if not rejected:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{f}\t{r}\n" for f, r in sorted(rejected.items())),
                    encoding="utf-8")


def validate_cache(cache: dict[str, str], freq_path: Path | None = None,
                   label: str = "cache") -> tuple[set[str], set[str]]:
    """Apply these checks to a persistent form->lemma cache, in place.

    Filtering the incoming map is not enough, and both lemma pipelines keep a
    cache that proves it: the merges fill gaps and never override, by design, so
    an entry that got in before the checks existed can never be displaced by a
    good one, and the checks give the reassuring answer while the damage sits
    upstream of them. `data/cache/form_lemma.tsv.gz` had `οὐ -> οὖον`, which put
    294,404 occurrences of the commonest negative in Greek onto a service-berry
    and published it at #27 in the top-30. `data/cache/lemma_cache.tsv` had 16
    forms of the same family.

    The corpus's own per-lemma frequencies are the reference, so the graded
    checks are skipped when that table is absent; the tombstone sweep is not,
    because a tombstone is a recorded decision and needs no reference to hold.
    Note the bootstrap for whichever pipeline WRITES that table: it is reading
    its own previous generation. That is fine while the reference is sound, and
    it is why the particle repairs that need no frequency at all - a closed-class
    word is its own lemma - carry the load.

    Call it on newly derived entries too, not only on the cache as loaded. The
    two callers each pass the lemmatizer's fresh output through a second time,
    because grading the cache and then publishing whatever came back new says
    nothing at all on a first build, where everything is new.

    Returns (repaired_forms, dropped_forms). The caller MUST keep the dropped
    set and refuse to re-derive those forms in the same run: they are dropped
    precisely because the lemmatizer's answer for them is wrong, so handing them
    back to it returns the same answer and quietly undoes the drop. That is not
    hypothetical - it is what happened the first time this was wired in, and
    `βασκανία -> Βασκανία` survived three passes because of it.
    """
    freq_path = freq_path or (DATA / "public_lemma_frequency.tsv")
    tombstones = load_rejected()
    repaired, dropped = [], []
    # Tombstones first, and independently of the reference table. A tombstone is
    # a decision already taken and written down, not one to re-derive, so it
    # holds whether or not the frequencies are on disk. This sweep used to sit
    # BELOW the early return for a missing table, which meant a fresh clone -
    # where public_lemma_frequency.tsv is a build product that does not exist
    # yet - let every form ever rejected walk straight back in on the first
    # build, with nothing on disk to show it had happened.
    for form in list(cache):
        # It crept back because the lemmatizer is deterministic: handed the same
        # form it returns the same wrong answer.
        if form in tombstones:
            dropped.append((form, cache.pop(form), tombstones[form]))
    # Also above the early return, and for the same reason as the tombstones:
    # this one is a fact about how Greek is spelled, not a reading of the
    # corpus, so there is nothing for a missing frequency table to withhold.
    for form in list(cache):
        if unbreathed_vowel(form):
            dropped.append((form, cache.pop(form), NOT_A_WORD))
            tombstones[form] = NOT_A_WORD
    if not freq_path.exists():
        # Written even here. The sweep above can mint a tombstone the run had
        # not seen before, and this return is the path a fresh clone takes, so
        # not saving would decide the same form again on every build.
        save_rejected(tombstones)
        print(f"no {freq_path.name}; {label}: applied {len(dropped):,} "
              f"tombstones, skipped the frequency checks", file=sys.stderr)
        return (set(), set(tombstones))
    freq = load_lemma_frequencies(freq_path)
    for form, lemma in list(cache.items()):
        # First, because it is the most certain rule here and the only one that
        # needs no evidence at all: the article and the relative are closed
        # paradigms, so their lemma is a fact about Greek rather than a reading
        # of this corpus. Running it ahead of the graded checks also keeps those
        # from getting an opinion about a form whose answer is already settled.
        closed = closed_class_lemma(form)
        if closed and closed != lemma:
            repaired.append((form, lemma, closed))
            cache[form] = closed
            continue
        if closed:
            continue
        particle = particle_capture(form, lemma, freq)
        if particle:
            repaired.append((form, lemma, particle))
            cache[form] = particle
            continue
        # Two spellings of one word, kept apart by a capital that only the
        # position put there. Measured, not assumed: the folds file holds just
        # the capitals the corpus shows are positional, so Λέων and Θεός are
        # not in it and do not fold into the lion and the god.
        folded = CAPITAL_FOLDS.get(lemma)
        if folded and folded != lemma:
            repaired.append((form, lemma, folded))
            cache[form] = folded
            continue
        # After the particles, so the 19 closed-class words are not handled
        # twice, and before the rejections, because a repair beats a drop.
        acute = grave_lemma_repair(lemma, freq)
        if acute:
            repaired.append((form, lemma, acute))
            cache[form] = acute
            continue
        reason = rejection_reason(form, lemma, freq)
        if reason == CAPITALIZED_VARIANT:
            repaired.append((form, lemma, form))
            cache[form] = form
            continue
        if reason:
            dropped.append((form, lemma, reason))
            tombstones[form] = reason
            del cache[form]
    save_rejected(tombstones)
    # The repairs are capped like the drops now. They were printed in full back
    # when only the 19 particles could produce one; the grave rule repairs 334
    # lemmas on the current cache, and 400 lines of stderr is not an audit. The
    # counts below are never capped, and `--write` prints its own report.
    for form, lemma, fixed in sorted(repaired)[:40]:
        print(f"  {label} repair: {form} -> {lemma} is now {fixed}",
              file=sys.stderr)
    for form, lemma, reason in sorted(dropped)[:40]:
        print(f"  {label} drop: {form} -> {lemma} ({reason})", file=sys.stderr)
    if repaired or dropped:
        print(f"{label} validated: {len(repaired):,} repaired, "
              f"{len(dropped):,} dropped (first 40 of each listed above)",
              file=sys.stderr)
    # The full tombstone set, not just what came out of the cache this run. A
    # form already absent is not "dropped" here, so returning only this run's
    # removals lets the caller re-derive it, put it back, and drop it again next
    # run - the build oscillated between 6,053,216 and 6,053,391 work-lemma
    # pairs on alternate runs until this returned the union.
    return ({f for f, _, _ in repaired}, set(tombstones))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", type=Path, default=DATA / "lemma_map.tsv")
    ap.add_argument("--freq", type=Path, default=DATA / "public_lemma_frequency.tsv")
    ap.add_argument("--min-lemma", type=int, default=1000,
                    help="how well attested a form must be AS A LEMMA before a "
                         "map row is allowed to reassign it (default 1000)")
    ap.add_argument("--write", type=Path, default=None,
                    help="write the filtered map here (may be the input path)")
    args = ap.parse_args()

    freq = load_lemma_frequencies(args.freq)
    print(f"{len(freq):,} lemma frequencies")

    kept, rejected, repaired, why = [], [], [], Counter()
    for line in args.map.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        form, _, lemma = line.partition("\t")
        lemma = lemma.strip()
        if not form or not lemma or form == lemma:
            kept.append(line)
            continue
        particle = particle_capture(form, lemma, freq)
        if particle:
            repaired.append((freq.get(lemma, 0), form, lemma, particle))
            why["closed-class particle variant captured by a rare lemma"] += 1
            kept.append(f"{form}\t{particle}")
            continue
        acute = grave_lemma_repair(lemma, freq)
        if acute:
            repaired.append((freq.get(lemma, 0), form, lemma, acute))
            why["grave-accented lemma, acute headword already attested"] += 1
            kept.append(f"{form}\t{acute}")
            continue
        reason = rejection_reason(form, lemma, freq, args.min_lemma)
        if reason:
            rejected.append((freq.get(form, 0), freq.get(lemma, 0), form, lemma,
                             reason))
            why[reason] += 1
        else:
            kept.append(line)

    print(f"kept {len(kept):,}, rejected {len(rejected):,}, "
          f"repaired {len(repaired):,}")
    for r, c in why.most_common():
        print(f"    {c:>4}  {r}")
    print()
    for f_as_lemma, l_freq, form, lemma, reason in sorted(rejected, reverse=True)[:30]:
        print(f"   {form:>14} ({f_as_lemma:>9,} as a lemma)  ->  "
              f"{lemma:<16} ({l_freq:,})   {reason}")
    if repaired:
        # Two rules land here now, the particle and the grave, so the heading no
        # longer names one of them: `Ξὺν -> ξὺν` is repaired to ξύν by the grave
        # rule and never touches the closed-class set.
        print("\n   repaired:")
        for l_freq, form, lemma, fixed in sorted(repaired)[:30]:
            print(f"   {form:>14}  ->  {lemma:<14} ({l_freq:,})  "
                  f"now {fixed} ({freq.get(fixed, 0):,})")

    if args.write:
        args.write.write_text("\n".join(kept) + "\n", encoding="utf-8")
        print(f"\nfiltered map -> {args.write}")
    else:
        print("\nreport only; pass --write PATH to emit the filtered map.")


if __name__ == "__main__":
    main()
