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

build_work_lemma_counts.py applies the same checks to the persistent form->lemma
cache on load, because filtering the incoming map does not help a cache that is
already poisoned: the merge fills gaps and never overrides, so a bad entry that
got in before the checks existed can never be displaced by a good one.
"""

from __future__ import annotations

import argparse
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
_ACCENTS = {"́", "̀", "͂"}          # oxia, varia, perispomeni


def unaccent(s: str) -> str:
    """Lowercase, accent stripped, breathing and iota subscript kept."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if not (unicodedata.combining(c) and c in _ACCENTS))


def _particle_compatible(form: str, particle: str) -> bool:
    """True if `form` can be an accent or case variant of `particle`.

    A form may be MISSING a breathing or subscript the particle has - OCR drops
    them, and an all-caps heading never had them - but it may not carry a
    different one. That is what keeps `οὗ` off `οὐ` and `ᾗ`, `ῃ`, `ἧ` off `ἤ`,
    all of which share a deaccented skeleton with a particle while being other
    words entirely.
    """
    if deaccent(form) != deaccent(particle):
        return False
    f, p = unaccent(form), unaccent(particle)
    if f == p:
        return True
    marks = lambda s: {c for c in s if unicodedata.combining(c)}  # noqa: E731
    return marks(f) <= marks(p)


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
    if freq.get(lemma, 0) == 0 and len(skeleton) >= 2:
        elided = [p for p in PARTICLES
                  if deaccent(p).startswith(skeleton) and deaccent(p) != skeleton]
        if len(elided) == 1 and elided[0] != lemma:
            return elided[0]
    return None


def rejection_reason(form: str, lemma: str, freq: dict[str, int],
                     min_lemma: int = 1000) -> str | None:
    """Why this form -> lemma pair must not stand, or None if it may."""
    f_as_lemma, l_freq = freq.get(form, 0), freq.get(lemma, 0)
    if lemma != lower_initial(lemma) and lower_initial(lemma) == form \
            and f_as_lemma > l_freq:
        return "capitalized variant of the form itself"
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
        print("\n   repaired to the particle:")
        for l_freq, form, lemma, particle in sorted(repaired)[:30]:
            print(f"   {form:>14}  ->  {lemma:<14} ({l_freq:,})  "
                  f"now {particle} ({freq.get(particle, 0):,})")

    if args.write:
        args.write.write_text("\n".join(kept) + "\n", encoding="utf-8")
        print(f"\nfiltered map -> {args.write}")
    else:
        print("\nreport only; pass --write PATH to emit the filtered map.")


if __name__ == "__main__":
    main()
