#!/usr/bin/env python3
"""Sort the breathings inside words into what the print has and what a reading or an encoding got wrong.

`measure_medial_breathings.py` counts the words with a breathing that is not at their head and sorts them by shape
(vowel, crasis, elision, rho) without deciding anything. This script goes one step further for each token: it tries
the repairs that would turn the token into a word the corpus has elsewhere, and names the token by the repair whose
form is commonest. The corpus itself is the lexicon: a form counts as a word when it occurs at least `--min-count` times as a
token with no breathing inside it, in any file, and carries an accent or is one of the words Greek writes without one
(the proclitics and the enclitics), so that numerals (κη) and fragments of words (Αἰδου) do not count. A form with a
capital first letter is the same form: its count is the sum of both. Nothing is changed; a class says what a reading
of the page has to check, not what the page prints.

Forms the print has (legitimate, but for the crasis shapes listed below):

  crasis            the coronis of crasis (κἂν, ταὐτόν, τοὐναντίον, προὔργου, καλοκἀγαθία), as the measurement
                    defines it, unless an accent or a diaeresis in the place of the mark gives a form at least ten
                    times as common as the token (crasis-accent).
  crasis-rough      crasis written with the rough breathing of the second word (χὡ, χἡ, κᾗ, θοἱμάτιον): κ, χ or θ
                    before a vowel, or before a diphthong it closes, with a rough mark, under the same condition.
                    The OCR's θ, χ or κ for the υ of υἱός (θἱὸς, χἱὸν) has this shape too and lands here, and about
                    one crasis token in two hundred is an error of the same kind (σἴτιον, χαἰ).
  elision           the combining comma used for the apostrophe: a smooth mark alone on the last consonant of a word
                    with a vowel (not a numeral, κγ̓, nor a final ς), at the end of the token or before the next word
                    run on with its breathing (ἀλλ̓, καθ̓, ἵν̓, ἀλλ̓ἡ, κατ̓αὐτῶν). An encoding of the apostrophe, not a
                    breathing. Some are errors all the same (ἦν̓, κακῶσ̓).
  rho               a breathing on a doubled ρ (ῤῥ, ῥῥ), and the smooth mark on the final ρ of an elided word with a
                    vowel (παῤ, ἄῤ, δεῦῤ): an editorial convention. A breathing on any other ρ is an error (ὑπάῤχων,
                    δῤ) and is classed below.

Errors, of the reading or of the encoding:

  apostrophe        δἰ and Δἰ: the elided δι᾿ with its apostrophe set as a smooth breathing on the iota.
  crasis-accent     a crasis shape where an accent or a diaeresis in the place of the mark gives a word that occurs
                    at least ten times as often as the token (τἀς for τὰς, τοὐ for τοῦ, μἄλλον for μᾶλλον, καἰ for
                    καὶ). The token's own count includes its form with a capital first letter (Ταὐτὸν with
                    ταὐτὸν). Some are crasis the print has (κἄλλος beside κάλλος), so each needs its reading.
  double            a breathing on both vowels of a diphthong that opens the word (Ἐἰ, ἐἰς): without the first
                    the form is a word.
  compound          without the mark the form is a word. Most are the head of the second element of a compound that
                    keeps its breathing (μετἔχει, καθἄπερ, γοὖν); some editions print the elided γ᾿ οὖν this way,
                    and most of these are OCR readings of an acute. The others are a mark set on a consonant or on
                    a single ρ (ὑπάῤχων).
  accent            an acute, grave or circumflex read as a breathing (δἐ, γἀρ, Πἀλιν, τουτἐστιν, ἀεἰ, Ἀἰδου
                    for Ἀίδου).
  diaeresis         a diaeresis read as a breathing (προἰόντος, προὑπάρχει).
  joined            two words run together, the second with its breathing (ἔχουσιναἱ, τοῦτοὑπάρχει, ὁὁ), or an
                    elided word joined to the next (δἂν for δ᾿ ἂν, ἐξαὐτῶν for ἐξ αὐτῶν). The second word is cut
                    before a diphthong it opens, or else at the mark. Both words must occur at least 50 times and
                    carry an accent or be a proclitic (not an enclitic: τοι is also the head of τοιαύτη), and a word
                    of one letter must be one of the words of one letter (ὁ, ἡ, ὅ, ἃ, ἢ, ᾖ, ὦ and the like), so
                    that a stray letter does not count.
                    An elided first word must occur 50 times with its apostrophe (᾿ or ᾽) and be δ᾿, τ᾿, γ᾿, θ᾿, σ᾿
                    or μ᾿, or have a vowel and end in γ, δ, θ, κ, λ, μ, ν, ξ, π, ρ, σ, τ, φ or χ (not ν᾿ or β᾿).
                    Written with ’, which the tokens leave out, it counts without it where it has a vowel, two
                    letters or more and ends in γ, δ, θ, κ, λ, π, τ, φ or χ (καθ, ἀλλ, but not συμ or κθ). The
                    split wins over a repair above when the repaired form occurs fewer than 50 times in the
                    token's own case (δἂν, where δὰν is rare and Δὰν a name, but παρἔχει for παρέχει).
  unresolved        none of these repairs gives a word: most are letters misread as well (οὐὐν, σἷόν), or rare
                    words the corpus does not have elsewhere.

A form counts as a word at `--min-count` occurrences. A token is classed by its first breathing inside the word, so a
token with a second one (κἀκεἰνου, ἀλλ̓ἡ) goes under the class of the first, which may be a form the print has.

  python3 scripts/classify_medial_breathings.py [--root DIR] [--min-count N] [--json OUT] [--examples N]

It reads data/corpus_catalog.tsv and data/corpus/*.jsonl under DIR (default: this checkout) and prints the counts by
class and source. The JSON output adds the counts by work and the commonest forms of each class with their repair.
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from measure_medial_breathings import (BREATHINGS, DIAERESIS, DIPHTHONGS, GREEK, VOWELS,
                                       crasis_shaped, letters)

SMOOTH, ROUGH = "̓", "̔"
ACUTE, GRAVE, CIRCUMFLEX = "́", "̀", "͂"
ACCENTS = {ACUTE, GRAVE, CIRCUMFLEX}
APOSTROPHE = "’"
CLASSES = ("crasis", "crasis-rough", "elision", "rho", "apostrophe", "crasis-accent", "double", "compound", "accent",
           "diaeresis", "joined", "unresolved")
LEGITIMATE = ("crasis", "crasis-rough", "elision", "rho")
# Words Greek writes without an accent: the proclitics, and the enclitics where they lose theirs. Any other form
# without an accent is a numeral or a fragment of a word, and is no repair.
UNACCENTED = {"ὁ", "ἡ", "οἱ", "αἱ", "ἐν", "εἰς", "ἐς", "ἐκ", "ἐξ", "εἰ", "ὡς", "οὐ", "οὐκ", "οὐχ",
              "τε", "γε", "τι", "τις", "τινος", "τινι", "τινα", "τινες", "τινων", "τισι", "τισιν", "τινας", "του", "τῳ",
              "που", "ποι", "πη", "πῃ", "πως", "ποτε", "πω", "ποθεν", "μου", "μοι", "με", "σου", "σοι", "σε", "οἱ", "ἑ",
              "ἐστι", "ἐστιν", "εἰσι", "εἰσιν", "ἐσμεν", "ἐστε", "εἰμι", "φησι", "φησιν", "φημι", "φασι", "φασιν",
              "περ", "τοι", "νυν", "κε", "κεν", "ῥα", "νυ", "μιν", "νιν"}
# The words of one letter.
ONE_LETTER = set("ὁἡὃἣὅἥἢἤἦᾗᾖὦὢὤᾧἃἅ")
# How often each word of a split must occur for a token to count as two words run together.
JOINED = 50
# The words of a split without an accent: the proclitics. An enclitic does not count there, since the short ones are
# also the heads of words (τοι in τοιαὐτὴ).
PROCLITICS = {"ὁ", "ἡ", "οἱ", "αἱ", "ἐν", "εἰς", "ἐς", "ἐκ", "ἐξ", "εἰ", "ὡς", "οὐ", "οὐκ", "οὐχ"}
# The last letters of an elided word written with ’, counted without it.
ELIDED = set("γδθκλπτφχ")
# The elided words of one letter, and the last letters of a longer elided word written with ᾿ or ᾽.
ONE_ELIDED = set("γδθμστ")
LAST_ELIDED = ELIDED | set("μνξρσ")
# Marks are written in this order, so a form built here compares equal to the corpus form after NFC.
ORDER = {"̓": 0, "̔": 0, DIAERESIS: 1, ACUTE: 2, GRAVE: 2, CIRCUMFLEX: 2, "ͅ": 3}


def compose(ls, upper):
    """A word from (letter, marks) pairs; `upper` is the set of positions that were capitals."""
    out = []
    for at, (char, marks) in enumerate(ls):
        out.append((char.upper() if at in upper else char) + "".join(sorted(marks, key=lambda m: ORDER.get(m, 9))))
    return unicodedata.normalize("NFC", "".join(out))


def parse(word):
    """The letters of a word with their marks, and the positions of its capitals."""
    upper, at = set(), 0
    for char in unicodedata.normalize("NFD", word):
        if unicodedata.combining(char):
            continue
        if char.isalpha():
            if char != char.lower():
                upper.add(at)
            at += 1
    return letters(word), upper


def medial(ls):
    """The positions of the breathings that do not stand at the head of the word."""
    out = []
    for at, (char, marks) in enumerate(ls):
        if not marks & BREATHINGS or at == 0:
            continue
        if at == 1 and ls[0][0] + char in DIPHTHONGS and DIAERESIS not in marks and not ls[0][1] & BREATHINGS:
            continue
        out.append(at)
    return out


def is_medial(word):
    return bool(medial(letters(word)))


def folded(form):
    """The form with a lower-case first letter: a word at the head of a sentence is the same word."""
    return form[:1].lower() + form[1:]


def accented(form):
    """Whether the form carries an accent, or is a word Greek writes without one."""
    return bool(set(unicodedata.normalize("NFD", form)) & ACCENTS) or folded(form) in UNACCENTED


class Lexicon:
    def __init__(self, counts, minimum):
        self.counts, self.minimum = counts, minimum

    def count(self, form):
        """How often the form occurs without a breathing inside, with a lower-case or a capital first letter."""
        low = folded(form)
        high = low[:1].upper() + low[1:]
        return self.counts.get(low, 0) + (self.counts.get(high, 0) if high != low else 0)

    def word(self, form):
        """A repair: a form that occurs `minimum` times and carries an accent or is written without one."""
        return self.count(form) >= self.minimum and accented(form)


def variants(ls, at, upper, replace):
    """The forms with the mark at `at` replaced by each set of marks in `replace`."""
    char, marks = ls[at]
    rest = marks - BREATHINGS
    for new in replace:
        copy = [list(item) for item in ls]
        copy[at][1] = set(rest) | set(new)
        yield compose(copy, upper)


def classify(word, lexicon, frequency=1):
    """The class of a token with a breathing inside it, and the repair that names it (or None). `frequency` is how
    often the token itself occurs in the corpus, with its form with a lower-case first letter."""
    ls, upper = parse(word)
    spots = medial(ls)
    if not spots:
        return None, None
    at = spots[0]
    char, marks = ls[at]
    plain = "".join(c for c, _ in ls)
    last = at == len(ls) - 1
    voiced = any(c in VOWELS for c in plain[:at])
    if char == "ρ" and ("ρ" in plain[at - 1:at] + plain[at + 1:at + 2] or last and marks == {SMOOTH} and voiced):
        return "rho", None
    # The comma of elision stands on the last consonant of a word that has a vowel (not on a numeral, κγ̓, nor on a
    # final ς), at the end of the token or before the head of the next word, which carries its breathing (ἀλλ̓ἡ,
    # κατ̓αὐτῶν).
    nxt = ls[at + 1:at + 3]
    head = not last and (bool(nxt[0][1] & BREATHINGS) or len(nxt) == 2 and nxt[0][0] + nxt[1][0] in DIPHTHONGS
                                                          and bool(nxt[1][1] & BREATHINGS))
    if char not in VOWELS and char not in "ρς" and marks == {SMOOTH} and voiced and (last or head):
        return "elision", None
    if plain == "δι" and at == 1 and marks == {SMOOTH}:
        return "apostrophe", compose([["δ", set()], ["ι", set()]], upper) + APOSTROPHE
    # Each repair, with the class it names: the mark read for an accent (or beside an accent of the wrong kind, as
    # in μἄλλον for μᾶλλον), for nothing, for a diaeresis, or a breathing set on both vowels of a diphthong.
    # Where two repairs give the same form, the first named wins: the mark read for nothing (μετἔχει) before the
    # mark read beside an accent of the wrong kind.
    # A mark on a consonant or on a single ρ has only the form without it.
    options = [("compound", form) for form in variants(ls, at, upper, [set()])]
    if char in VOWELS:
        if not marks & ACCENTS:
            options += [("accent", form) for form in variants(ls, at, upper, [{ACUTE}, {GRAVE}, {CIRCUMFLEX}])]
        else:
            swapped = [list(item) for item in ls]
            swapped[at][1] = marks - ACCENTS
            options += [("accent", form) for form in variants(swapped, at, upper, [{ACUTE}, {GRAVE}, {CIRCUMFLEX}])]
        options += [("diaeresis", form) for form in variants(ls, at, upper, [{DIAERESIS}, {DIAERESIS, ACUTE},
                                                                            {DIAERESIS, GRAVE}])]
    if at == 1 and ls[0][1] & BREATHINGS and ls[0][0] + char in DIPHTHONGS:
        copy = [list(item) for item in ls]
        copy[0][1] = copy[0][1] - BREATHINGS
        options.append(("double", compose(copy, upper)))
    options = [option for option in options if lexicon.word(option[1])]
    found = max(options, key=lambda option: lexicon.count(option[1]), default=None)
    before = plain[:at]
    rough_crasis = char in VOWELS and ROUGH in marks and (before in "κχθ" and len(before) == 1 or (
        len(before) == 2 and before[0] in "κχθ" and before[1] + char in DIPHTHONGS))
    if char in VOWELS and crasis_shaped(ls, at) or rough_crasis:
        # A crasis shape is the print's unless an accent or a diaeresis in the place of the mark gives a form far
        # commoner than the token. The form without the mark is often the same crasis written without its coronis
        # (θατέρου), so it does not count here.
        marked = [option for option in options if option[0] in ("accent", "diaeresis")]
        commonest = max(marked, key=lambda option: lexicon.count(option[1]), default=None)
        if commonest and lexicon.count(commonest[1]) >= 10 * max(1, frequency):
            return "crasis-accent", commonest[1]
        return ("crasis-rough" if rough_crasis else "crasis"), None
    # Two words run together: a breathing on the second vowel of a diphthong belongs to a word that starts with the
    # diphthong (ἔχουσιναἱ), else the second word starts at the mark (τοῦτοὑπάρχει). Each word must be common and
    # accented, or a proclitic, and a word of one letter must be one; the first may be elided.
    def whole(form):
        return (bool(set(unicodedata.normalize("NFD", form)) & ACCENTS) or folded(form) in PROCLITICS) and (
            len(letters(form)) > 1 or folded(form) in ONE_LETTER)
    common = lambda form: lexicon.count(form) >= JOINED
    joined = None
    cuts = [at - 1] if at >= 2 and ls[at - 1][0] + char in DIPHTHONGS and not ls[at - 1][1] else []
    for cut in cuts + [at]:
        left, right = compose(ls[:cut], upper), compose(ls[cut:], {i - cut for i in upper if i >= cut})
        if not (common(right) and whole(right) and not is_medial(right)):
            continue
        if common(left) and whole(left):
            joined = ("joined", f"{left} {right}")
        elif ls[cut - 1][0] not in VOWELS:
            # The tokens leave out ’ (GREEK has no place for it), so καθ’ is counted as καθ. The bare form counts
            # only where it can be an elided word: a vowel, two letters or more, and one of these last letters.
            vowel = any(c in VOWELS for c, _ in ls[:cut])
            bare = lexicon.count(left) if ls[cut - 1][0] in ELIDED and cut >= 2 and vowel else 0
            # Written with ᾿ or ᾽, the elided word is one letter of the elided δέ, τε, γε, θ᾿ (τε before a rough
            # breathing), σέ or μέ, or a longer word with a vowel that ends in a consonant an elision leaves.
            marked = (cut == 1 and ls[0][0] in ONE_ELIDED) or (cut >= 2 and vowel and ls[cut - 1][0] in LAST_ELIDED)
            elided = max(lexicon.count(left + "\u1fbf"), lexicon.count(left + "\u1fbd")) if marked else 0
            elided = max(elided, bare)
            if elided >= JOINED:
                joined = ("joined", f"{left}{APOSTROPHE} {right}")
        if joined:
            break
    # The split wins over a rare repair. The repair is counted here in the token's own case only, so that a name
    # (Δὰν) does not take a lower-case token (δἂν, δ᾿ ἂν).
    if joined and (not found or lexicon.counts.get(found[1], 0) < JOINED):
        return joined
    if found:
        return found
    return "unresolved", None


def tokens(path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            text = unicodedata.normalize("NFC", json.loads(line).get("text", ""))
            # An apostrophe after a word belongs to it where it is ᾿ or ᾽ (δ᾿); GREEK leaves out ’, ʼ, ' and ´, so
            # καθ’ is counted as καθ.
            for word in GREEK.findall(text):
                if any(c.isalpha() for c in word):
                    yield word


def corpus(root):
    root = Path(root)
    with (root / "data/corpus_catalog.tsv").open(encoding="utf-8") as handle:
        catalog = {row["slug"]: row for row in csv.DictReader(handle, delimiter="\t")}
    return {slug: row for slug, row in sorted(catalog.items()) if (root / "data/corpus" / f"{slug}.jsonl").is_file()}


def build(root, minimum):
    root = Path(root)
    works = corpus(root)
    counts, flagged = Counter(), defaultdict(Counter)
    for slug in works:
        for word in tokens(root / "data/corpus" / f"{slug}.jsonl"):
            if is_medial(word):
                flagged[slug][word] += 1
            else:
                counts[word] += 1
    lexicon = Lexicon(counts, minimum)
    # The token's own count takes in its form with a lower-case first letter, as the lexicon does.
    total = Counter()
    for c in flagged.values():
        for word, n in c.items():
            total[folded(word)] += n
    by_work, forms = {}, defaultdict(Counter)
    repairs = {}
    for slug, row in works.items():
        c = Counter()
        for word, n in flagged[slug].items():
            if word not in repairs:
                repairs[word] = classify(word, lexicon, total[folded(word)])
            kind, repair = repairs[word]
            c[kind] += n
            forms[kind][word] += n
        if c:
            by_work[slug] = dict(source=row["source"], correction=row["correction"], **c)
    return works, by_work, forms, repairs


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--min-count", type=int, default=3)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--examples", type=int, default=8)
    args = parser.parse_args()
    works, by_work, forms, repairs = build(args.root, args.min_count)
    by_source = defaultdict(Counter)
    for slug, row in works.items():
        by_source[row["source"]]["works"] += 1
    for slug, w in by_work.items():
        for kind in CLASSES:
            by_source[w["source"]][kind] += w.get(kind, 0)
    print("source\tworks\t" + "\t".join(CLASSES))
    total = Counter()
    for name, c in sorted(by_source.items(), key=lambda item: -sum(item[1][k] for k in CLASSES[4:])):
        total.update(c)
        print(f"{name}\t{c['works']}\t" + "\t".join(str(c[k]) for k in CLASSES))
    print(f"all\t{total['works']}\t" + "\t".join(str(total[k]) for k in CLASSES))
    print()
    for kind in CLASSES:
        top = ", ".join(f"{word} {n}" + (f" ({repairs[word][1]})" if repairs[word][1] else "")
                        for word, n in forms[kind].most_common(args.examples))
        print(f"{kind}: {top}")
    if args.json:
        args.json.write_text(json.dumps(dict(
            min_count=args.min_count, classes=CLASSES, legitimate=LEGITIMATE, by_source=by_source, works=by_work,
            top_forms={k: [[w, n, repairs[w][1]] for w, n in forms[k].most_common(300)] for k in CLASSES}),
            ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
