#!/usr/bin/env python3
"""Split the spacing breathing marks that tokenize as Greek words.

U+1FBF and U+1FFE are spacing diacritics, not letters, but they sit inside the
Greek block, so build_public_corpus._GK reads them as Greek and a bare one
becomes a word. Issue #35 counted the class; this says what each token is,
because the disposition turns on that and only one of the four must be left
alone.

THE TEST, and it is decidable without reading a page:

  punctuation_only      the mark alone, or repeated. Not a word under any
                        reading.
  quotation_mark        the following word already carries its own breathing, or
                        a dasia stands before a consonant. Neither can be a
                        breathing: only vowels and rho take one. This is how the
                        Aristotle commentators mark quotation, ῾τὸ ... ᾿.
  uncomposed_breathing  the mark stands before an unbreathed vowel or rho and
                        belongs on it: ῾υμετἑρα is ὑμετέρα, ῾ρωγαλέῳ is ῥωγαλέῳ.
                        The class compose_spacing_breathings.py fixed for
                        capitals on 2026-08-07 and left before lowercase letters
                        on the ground that those were apostrophes; for these it
                        was wrong.
  aphaeresis            a psili standing for an elided syllable in the Byzantine
                        vernacular: ᾿ς, ᾿κ, ᾿γὼ. Genuine text. Not to be touched.

The one that is easy to get wrong is the second. A breathing sits on the SECOND
vowel of a diphthong, so ῾εἰ and ῾οὐκ already carry one and the spacing mark is a
quote; testing only the letter directly after the mark misses that and files 267
tokens as breathings that are not.

REPORTS ONLY. Three of the four are mechanically fixable and the fourth must not
be, and which to act on is not a measurement.

  python3 scripts/measure_spacing_marks.py [--write]
"""
from __future__ import annotations
import argparse, collections, json, sys, unicodedata
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "spacing_mark_classes.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

PSILI, DASIA = "᾿", "῾"
VOWELS = set("αειηουωΑΕΙΗΟΥΩ")
BREATHINGS = ("̓", "̔")


def head_is_breathed(w: str) -> bool:
    """A breathing sits on the second vowel of a diphthong, so look at two."""
    return any(c in BREATHINGS for c in unicodedata.normalize("NFD", w[1:3]))


def classify(w: str) -> str:
    if all(c in (PSILI, DASIA) for c in w):
        return "punctuation_only"
    nxt = w[1]
    base = unicodedata.normalize("NFD", nxt)[0]
    if head_is_breathed(w):
        return "quotation_mark"
    if w[0] == DASIA and base not in VOWELS and base not in "ρΡ":
        return "quotation_mark"
    if base in VOWELS or base in "ρΡ":
        return "uncomposed_breathing"
    return "aphaeresis"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    cls: collections.Counter = collections.Counter()
    forms: dict = collections.defaultdict(collections.Counter)
    works: dict = collections.defaultdict(set)
    src: dict = collections.defaultdict(collections.Counter)
    for fp in sorted((DATA / "corpus").glob("*.jsonl")):
        slug = fp.name[:-len(".jsonl")]
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            for w in _GK.findall(r.get("text") or ""):
                if not w or w[0] not in (PSILI, DASIA):
                    continue
                k = classify(w)
                cls[k] += 1
                forms[k][w] += 1
                works[k].add(slug)
                src[k][r.get("source")] += 1
    total = sum(cls.values())
    for k, n in cls.most_common():
        print(f"  {k:<22} {n:>5} {n / total:>6.1%}  {len(works[k]):>3} works  "
              f"e.g. {' '.join(w for w, _ in forms[k].most_common(4))}")
    if not a.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "spacing breathing marks that tokenize as Greek words, split by "
                "what each one actually is",
        "issue": "open-greek/open-greek-corpus#35",
        "discriminator": "only vowels and rho take a breathing, so a dasia before "
                         "a consonant is not one; and a mark before a word that "
                         "already carries its own breathing is not one either. A "
                         "breathing sits on the second vowel of a diphthong, so "
                         "῾εἰ is already breathed: testing only the letter after "
                         "the mark misses that and mis-files 267 tokens.",
        "NOT_A_DISPOSITION": "three of the four are mechanically fixable and the "
                             "fourth, aphaeresis, must not be touched. Which to "
                             "act on is not a measurement.",
        "total": total,
        "by_class": {k: {"tokens": n, "share": round(n / total, 4),
                         "forms": len(forms[k]), "works": len(works[k]),
                         "by_source": dict(src[k].most_common()),
                         "examples": [w for w, _ in forms[k].most_common(6)]}
                     for k, n in cls.most_common()},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
