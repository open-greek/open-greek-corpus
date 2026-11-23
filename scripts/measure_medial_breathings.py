#!/usr/bin/env python3
"""Count the Greek words whose breathing does not stand at the head of the word.

A breathing belongs on a word's first letter, or on the second vowel of a diphthong that opens the word (αἰ, εὐ,
οὐ, Αἰ). On any other vowel it is one of two things. In crasis the mark is the coronis, which has the form of the
smooth breathing: κἀν, κἂν, ταὐτά, τοὐναντίον, θἀτέρου, καλοκἀγαθία, προὔργου, ἐγᾦμαι. Everywhere else an OCR
engine has read an acute or a grave as a breathing, as in διαφἐρον, φὑλων and στἑλλει, or the text runs two words
together, as in ἔχουσιναἱ and δἂν.

The measurement sorts each such token into one of four kinds and does not decide anything:

  vowel     a breathing on a vowel that is not crasis-shaped: an OCR error or two words run together. This is the
            class to sweep, each token read on its page.
  crasis    a smooth mark where the letters before it are one consonant (κ τ θ χ μ σ), or one consonant and the
            first vowel of a diphthong the marked vowel closes (κἀ- τοὐ- ταὐ- θοἰ-), or the προὐ- of προὔργου, or the
            κἀγαθ- of καλοκἀγαθία, or the head of ἐγᾦμαι, ἐγᾠδα or μεντἂν (an ἐγὠ is the grave of ἐγὼ). Mostly genuine, but an OCR τἀς for τὰς, κἀν for
            κἂν, τὀν for τὸν or σἰνηπι for σίνηπι has this shape too, so a sweep reads this class on its own pass.
  elision   a smooth mark on a consonant other than rho: the combining comma used for the apostrophe (ἀλλ̓, καθ̓).
  rho       a breathing on a rho that is not the first letter: παῤ for the elided παρ᾿, and the ῤῥ of some
            editions.

Spacing breathings (U+1FBF, U+1FFE, U+1FDD) and other marks that are not letters are left out of the word, so a
stray spacing mark (διεστώσας·῝) is not counted here.

  python3 scripts/measure_medial_breathings.py [--root DIR] [--json OUT]

It reads data/corpus_catalog.tsv and data/corpus/*.jsonl under DIR (default: this checkout) and prints the counts
by source and by work.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

BREATHINGS = {"̓", "̔"}
DIAERESIS = "̈"
DIPHTHONGS = {"αι", "ει", "οι", "υι", "αυ", "ευ", "ου", "ηυ", "ωυ"}
VOWELS = set("αεηιουω")
CRASIS_CONSONANTS = set("κτθχμσ")
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")


def letters(word):
    """The letters of a word, lowercase, each with the set of marks over or under it. A character that is neither a
    letter nor a combining mark (a spacing breathing, a numeral sign) is left out, with any mark on it."""
    out, last = [], None
    for char in unicodedata.normalize("NFD", word):
        if unicodedata.combining(char):
            if last is not None:
                last[1].add(char)
        elif char.isalpha():
            last = [char.lower(), set()]
            out.append(last)
        else:
            last = None
    return out


def crasis_shaped(ls, at):
    """Whether a smooth mark on the vowel at `at` stands where crasis puts the coronis."""
    char, marks = ls[at]
    if "\u0314" in marks:
        return False
    plain = "".join(c for c, _ in ls)
    before = plain[:at]
    return ((len(before) == 1 and before in CRASIS_CONSONANTS)
            or (len(before) == 2 and before[0] in CRASIS_CONSONANTS and before[1] + char in DIPHTHONGS)
            or (before == "προ" and char == "υ")
            or plain[at - 1:at + 4] == "καγαθ"
            or (before == "εγ" and char == "ω" and marks & {"\u0342", "\u0345"})
            or (before == "μεντ" and char == "α"))


def medial_kind(word):
    """None for a word whose breathings all stand at its head; else 'vowel', 'crasis', 'elision' or 'rho'."""
    ls = letters(word)
    kinds = []
    for at, (char, marks) in enumerate(ls):
        if not marks & BREATHINGS or at == 0:
            continue
        if at == 1 and ls[0][0] + char in DIPHTHONGS and DIAERESIS not in marks and not ls[0][1] & BREATHINGS:
            continue
        if char == "ρ":
            kinds.append("rho")
        elif char not in VOWELS:
            kinds.append("elision")
        elif crasis_shaped(ls, at):
            kinds.append("crasis")
        else:
            kinds.append("vowel")
    for kind in ("vowel", "crasis", "elision", "rho"):
        if kind in kinds:
            return kind
    return None


def measure(root):
    root = Path(root)
    with (root / "data/corpus_catalog.tsv").open(encoding="utf-8") as handle:
        catalog = {row["slug"]: row for row in csv.DictReader(handle, delimiter="\t")}
    works, forms = {}, defaultdict(Counter)
    for slug, row in sorted(catalog.items()):
        path = root / "data/corpus" / f"{slug}.jsonl"
        if not path.is_file():
            continue
        counts, tokens = Counter(), 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                for word in GREEK.findall(unicodedata.normalize("NFC", json.loads(line).get("text", ""))):
                    if not any(c.isalpha() for c in word):
                        continue
                    tokens += 1
                    kind = medial_kind(word)
                    if kind:
                        counts[kind] += 1
                        forms[kind][word] += 1
        works[slug] = dict(source=row["source"], edition=row["edition"], correction=row["correction"],
                           greek_tokens=tokens, **counts)
    return works, forms


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path)
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()
    works, forms = measure(args.root)
    kinds = ("vowel", "crasis", "elision", "rho")
    by_source = defaultdict(Counter)
    for work in works.values():
        source = by_source[work["source"]]
        source["works"] += 1
        source["greek_tokens"] += work["greek_tokens"]
        for kind in kinds:
            source[kind] += work.get(kind, 0)
            source[f"works_{kind}"] += bool(work.get(kind))
    print("source\tworks\tgreek_tokens\tvowel\tworks_with_vowel\tcrasis\telision\trho")
    for name, c in sorted(by_source.items(), key=lambda item: -item[1]["vowel"]):
        print(f"{name}\t{c['works']}\t{c['greek_tokens']}\t{c['vowel']}\t{c['works_vowel']}\t{c['crasis']}"
              f"\t{c['elision']}\t{c['rho']}")
    print()
    print("work\tsource\tcorrection\tgreek_tokens\tvowel\tper_10k\tcrasis\telision\trho")
    ranked = sorted(works.items(), key=lambda item: -item[1].get("vowel", 0))
    for slug, w in ranked[:args.top]:
        print(f"{slug}\t{w['source']}\t{w['correction']}\t{w['greek_tokens']}\t{w.get('vowel', 0)}\t"
              f"{10000 * w.get('vowel', 0) / max(1, w['greek_tokens']):.1f}\t{w.get('crasis', 0)}"
              f"\t{w.get('elision', 0)}\t{w.get('rho', 0)}")
    if args.json:
        args.json.write_text(json.dumps(dict(works=works, by_source=by_source,
                                             top_forms={k: forms[k].most_common(200) for k in kinds}),
                                        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
