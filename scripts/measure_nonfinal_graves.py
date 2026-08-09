#!/usr/bin/env python3
"""Partition the misplaced-grave class by where it lives and what repairing it
would cost.

Greek writes a grave only on a word's final syllable. Issue #31 counts the
tokens that break that and stops there, which leaves the obvious next step
looking easy and it is not: the mechanical repair, rewriting the stray varia as
an oxia, gives the WRONG WORD on several of the largest forms.

    ἐγὼγε   is ἔγωγε   (2,544 in corpus), not ἐγώγε  (84)
    τὰλλα   is τἄλλα   (2,157) or τἆλλα (1,834), not τάλλα (30)
    τὰναντία is τἀναντία (1,831), not τάναντία (304, itself illegal)
    ἐπεὶδὴ  is ἐπειδὴ  (32,390): the grave is DROPPED, not moved

So this publishes four competing repair shapes per form with their attestation,
never a single target column, because a "is the target attested" gate passes on
τάναντία and ἐγώγε and would inject wrong words at scale. That is how #1's
forty thousand wrong corrections happened.

The syllable test is vendored rather than imported. The sibling greek-ocr
checkout has the same logic, and tests/test_nonfinal_grave.py asserts the two
agree, but a published count must not silently change depending on whether a
directory next door exists.

  python3 scripts/measure_nonfinal_graves.py
  python3 scripts/measure_nonfinal_graves.py --write   # -> data/nonfinal_graves.json
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "nonfinal_graves.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

ACUTE, GRAVE, CIRCUMFLEX = "́", "̀", "͂"
DIAERESIS = "̈"
ACCENTS = (ACUTE, GRAVE, CIRCUMFLEX)
VOWELS = set("αειηουω")
DIPHTHONGS = {"αι", "ει", "οι", "υι", "αυ", "ευ", "ου", "ηυ", "ωυ"}


def nuclei(nfd: str) -> list[str]:
    """The combining marks of each syllable nucleus, left to right.

    Diphthong-aware: αι, ευ and the rest are one nucleus carrying the marks of
    their second vowel, unless that vowel takes a diaeresis, which is what makes
    it two syllables. Counting bare vowels instead would call ταὶς two syllables
    and score its grave as non-final, which is why the crude last-vowel test
    over-reports.
    """
    out, i = [], 0
    while i < len(nfd):
        if nfd[i].lower() not in VOWELS:
            i += 1
            continue
        j = i + 1
        marks = ""
        while j < len(nfd) and unicodedata.combining(nfd[j]):
            marks += nfd[j]
            j += 1
        if not marks and j < len(nfd) and (nfd[i] + nfd[j]).lower() in DIPHTHONGS:
            k = j + 1
            second = ""
            while k < len(nfd) and unicodedata.combining(nfd[k]):
                second += nfd[k]
                k += 1
            if DIAERESIS not in second:
                out.append(second)
                i = k
                continue
        out.append(marks)
        i = j
    return out


def has_nonfinal_grave(token: str) -> bool:
    ns = nuclei(unicodedata.normalize("NFD", token))
    if len(ns) < 2:
        return False
    return any(GRAVE in m for m in ns[:-1])


def shapes(form: str) -> dict[str, str]:
    """The competing readings of a form carrying a stray grave. Deliberately
    plural: which one is right is lexical, and the point of the artifact is that
    no single rule picks correctly."""
    nfd = unicodedata.normalize("NFD", form)
    out = {}
    # grave -> acute in place
    out["acute"] = unicodedata.normalize("NFC", nfd.replace(GRAVE, ACUTE, 1))
    # grave dropped (ἐπεὶδὴ -> ἐπειδὴ)
    out["dropped"] = unicodedata.normalize("NFC", nfd.replace(GRAVE, "", 1))
    # crasis: the mark is a coronis, so the vowel takes a smooth breathing
    out["crasis"] = unicodedata.normalize("NFC", nfd.replace(GRAVE, "̓", 1))
    # circumflex (ταὺτα -> ταῦτα)
    out["circumflex"] = unicodedata.normalize("NFC", nfd.replace(GRAVE, CIRCUMFLEX, 1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    forms: collections.Counter = collections.Counter()
    by_source: collections.Counter = collections.Counter()
    by_edition: collections.Counter = collections.Counter()
    src_total: collections.Counter = collections.Counter()
    ed_total: collections.Counter = collections.Counter()
    all_forms: collections.Counter = collections.Counter()
    works = set()
    total = 0

    for fp in sorted((DATA / "corpus").glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            src, ed = r.get("source", "?"), r.get("edition", "?")
            for w in _GK.findall(r.get("text") or ""):
                total += 1
                all_forms[w] += 1
                src_total[src] += 1
                ed_total[ed] += 1
                if has_nonfinal_grave(w):
                    forms[w] += 1
                    by_source[src] += 1
                    by_edition[ed] += 1
                    works.add(fp.stem)

    flagged = sum(forms.values())
    print(f"non-final graves: {len(forms):,} forms, {flagged:,} tokens "
          f"({flagged / total:.3%} of {total:,} served), in {len(works):,} works")
    print("  by source:")
    for s, n in by_source.most_common(6):
        print(f"    {s:<18} {n:>7,}  {n / max(src_total[s], 1):.3%} of that source")
    print("  by edition (top 5):")
    for e, n in by_edition.most_common(5):
        print(f"    {e[:34]:<34} {n:>7,}  {n / max(ed_total[e], 1):.3%}")

    # Where a repair could even be pointed: how many shapes are attested.
    rows = []
    multi = single = none = 0
    for form, n in forms.most_common():
        sh = shapes(form)
        att = {k: all_forms.get(v, 0) for k, v in sh.items() if v != form}
        live = {k: c for k, c in att.items() if c}
        if len(live) > 1:
            multi += n
        elif live:
            single += n
        else:
            none += n
        if len(rows) < 200:
            rows.append({"form": form, "tokens": n,
                         "shapes": {k: {"form": sh[k], "attested": att.get(k, 0)}
                                    for k in sh if sh[k] != form}})
    print(f"  repair shapes attested: {multi:,} tokens have MORE THAN ONE "
          f"attested reading, {single:,} exactly one, {none:,} none")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "served tokens carrying a grave on a syllable that is not the "
                "ultima, partitioned by source, edition and by what a repair "
                "could be pointed at",
        "issue": "open-greek/open-greek-corpus#31",
        "NOT_A_REPAIR_RULE": {
            "why": "the mechanical repair, rewriting the stray varia as an oxia, "
                   "gives the wrong word on several of the largest forms, and "
                   "its target is itself attested, so an 'is the target "
                   "attested' gate does not catch it. Four shapes are published "
                   "per form and no single target column, deliberately.",
            "counterexamples": {
                "ἐγὼγε": "ἔγωγε, not ἐγώγε", "τὰλλα": "τἄλλα or τἆλλα, not τάλλα",
                "τὰναντία": "τἀναντία, not τάναντία",
                "ἐπεὶδὴ": "ἐπειδὴ: the grave is dropped, not moved"},
        },
        "syllable_test": "vendored here rather than imported from greek-ocr, so "
                         "the count cannot change with whether a sibling "
                         "checkout exists; tests/test_nonfinal_grave.py asserts "
                         "the two agree",
        "forms": len(forms), "tokens": flagged,
        "served_tokens": total,
        "share": round(flagged / total, 6),
        "works_touched": len(works),
        "by_source": [{"source": s, "tokens": n,
                       "rate": round(n / max(src_total[s], 1), 6)}
                      for s, n in by_source.most_common()],
        "by_edition": [{"edition": e, "tokens": n,
                        "rate": round(n / max(ed_total[e], 1), 6)}
                       for e, n in by_edition.most_common(25)],
        "repair_reach": {"tokens_with_more_than_one_attested_shape": multi,
                         "tokens_with_exactly_one": single,
                         "tokens_with_none": none},
        "largest_forms": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
