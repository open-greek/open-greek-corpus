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
SHEET = DATA / "nonfinal_grave_tranche.json"

# Sources this repo OCR'd or republishes someone else's OCR of. They are kept
# out of the attestation base: the class exists because OCR mis-set accents, so
# letting OCR text vote on the right accent would let the error attest itself.
OCR_SOURCES = {"ocr", "cgpg"}
# A reading has to hold this much of its skeleton class, over this many clean
# tokens, before the class is treated as decided at all.
MIN_CLASS, DOMINANT = 20, 0.90
# The tranche proposed for repair is stricter again, and accent-only.
TRANCHE_SHARE, TRANCHE_CLEAN = 0.95, 100

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


def skeleton(w: str) -> str:
    """The word's letters with every combining mark removed."""
    return "".join(c for c in unicodedata.normalize("NFD", w)
                   if not unicodedata.combining(c))


def without_accents(w: str) -> str:
    """Letters, breathings, iota subscript and diaeresis; accents dropped.

    Two forms with the same value here differ only in accent, which is the test
    that keeps a repair off the lexical marks. Moving a breathing turns ὰπὸ into
    ἀπό and τὰναντία into τἀναντία, and those are different claims from moving
    a stress.
    """
    return "".join(c for c in unicodedata.normalize("NFD", w)
                   if c not in (ACUTE, GRAVE, CIRCUMFLEX))


def ultima_normalized(w: str) -> str:
    """A grave on the LAST nucleus rewritten as an acute.

    That alternation is positional, not lexical: καί before a pause is καὶ in
    running text. Without merging them a word's own attestations compete with
    each other and no reading reaches a majority.
    """
    nfd = unicodedata.normalize("NFD", w)
    ns = nuclei(nfd)
    if ns and GRAVE in ns[-1]:
        j = nfd.rfind(GRAVE)
        nfd = nfd[:j] + ACUTE + nfd[j + 1:]
    return unicodedata.normalize("NFC", nfd)


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
    clean: collections.Counter = collections.Counter()   # non-OCR attestation base
    ocr_tokens: collections.Counter = collections.Counter()
    pages: collections.Counter = collections.Counter()
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
                    if src == "ocr":
                        ocr_tokens[w] += 1
                        pages[f"{fp.stem}:{str(r.get('locus','')).rsplit('.', 1)[0]}"] += 1
                elif src not in OCR_SOURCES:
                    # The attestation base. Flagged forms are excluded from it
                    # entirely, not just the one being repaired: an illegal form
                    # must not get a vote on what the legal one is.
                    clean[w] += 1

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

    # The skeleton class. Ask which clean Greek word has these letters, rather
    # than which of four mechanical reshapings of the accent is right. The four
    # shapes above cannot decide the largest forms and the block above says so;
    # this can, for about half the mass, and it agrees with every counterexample
    # that sank the four-shape approach: ἐπεὶδὴ is ἐπειδή (the grave drops),
    # ἐγὼγε is ἔγωγε, τὰναντία is τἀναντία. It also refuses where it should,
    # τὰλλα at 0.557 between τἄλλα and τἆλλα, ὰλλὰ at 0.878 because ἄλλα shares
    # its skeleton.
    classes: dict[str, collections.Counter] = {}
    for w, n in clean.items():
        classes.setdefault(skeleton(w), collections.Counter())[ultima_normalized(w)] += n

    buckets: collections.Counter = collections.Counter()
    bucket_tokens: collections.Counter = collections.Counter()
    decided, tranche = [], []
    for form, n in forms.most_common():
        c = classes.get(skeleton(form))
        if not c:
            buckets["no clean sibling"] += 1
            bucket_tokens["no clean sibling"] += n
            continue
        size = sum(c.values())
        target, hits = c.most_common(1)[0]
        share = hits / size
        if size < MIN_CLASS:
            buckets[f"class thinner than {MIN_CLASS}"] += 1
            bucket_tokens[f"class thinner than {MIN_CLASS}"] += n
            continue
        label = (f"dominant >= {DOMINANT}" if share >= DOMINANT
                 else ("0.70-0.90" if share >= 0.70 else "below 0.70"))
        buckets[label] += 1
        bucket_tokens[label] += n
        if share < DOMINANT:
            continue
        accent_only = without_accents(form) == without_accents(target)
        runner = c.most_common(2)[1] if len(c) > 1 else None
        rec = {"form": form, "tokens": n, "ocr_tokens": ocr_tokens[form],
               "target": target, "clean_class": size, "clean_hits": hits,
               "share": round(share, 4), "accent_only": accent_only,
               "runner_up": {"form": runner[0], "clean_tokens": runner[1]}
                            if runner else None}
        decided.append(rec)
        if (accent_only and share >= TRANCHE_SHARE and hits >= TRANCHE_CLEAN
                and ocr_tokens[form]):
            tranche.append(rec)

    acc_only = [d for d in decided if d["accent_only"]]
    tr_tokens = sum(t["ocr_tokens"] for t in tranche)
    weighted = (sum(t["ocr_tokens"] * t["share"] for t in tranche) / tr_tokens
                if tr_tokens else 0.0)
    print(f"  skeleton class: " + ", ".join(
        f"{k} {buckets[k]:,} forms/{bucket_tokens[k]:,} tok"
        for k in sorted(buckets)))
    print(f"    of the dominant bucket, accent-only: {len(acc_only):,} forms, "
          f"{sum(d['tokens'] for d in acc_only):,} tokens; the rest also move a "
          f"breathing or iota subscript")
    print(f"    proposed tranche (our own OCR, accent-only, share >= "
          f"{TRANCHE_SHARE}, >= {TRANCHE_CLEAN} clean): {len(tranche):,} forms, "
          f"{tr_tokens:,} tokens, token-weighted share {weighted:.4f} "
          f"-> about {tr_tokens * (1 - weighted):,.0f} expected wrong")
    dense = sorted(pages.values(), reverse=True)
    print(f"    OCR tokens sit on {len(pages):,} distinct scan pages; the "
          f"densest 500 carry {sum(dense[:500]):,}, so a re-read is not the lever")

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
        "skeleton_class": {
            "what": "for each flagged form, which clean Greek word has its "
                    "letters. Grouped on the letter skeleton with every "
                    "combining mark stripped, counted over the non-OCR corpus "
                    "only, with a grave on the last nucleus read as an acute "
                    "because that alternation is positional.",
            "why_this_and_not_the_four_shapes": "the block above is still true: "
                "no mechanical reshaping of the accent is right for a majority. "
                "That is a fact about those four shapes, not about the class. "
                "Asking which word it is decides half the mass and gets every "
                "counterexample above right, including that ἐπεὶδὴ is ἐπειδή, "
                "where the grave is dropped rather than moved.",
            "base": {"forms": len(clean), "tokens": sum(clean.values()),
                     "excludes": "OCR sources, and every flagged form, so an "
                                 "illegal form cannot vote on the legal one"},
            "params": {"min_clean_class": MIN_CLASS, "dominant_share": DOMINANT},
            "partition": [{"bucket": k, "forms": buckets[k],
                           "tokens": bucket_tokens[k]} for k in sorted(buckets)],
            "accent_only_forms": len(acc_only),
            "accent_only_tokens": sum(d["tokens"] for d in acc_only),
            "marks_moved_tokens": sum(d["tokens"] for d in decided
                                      if not d["accent_only"]),
            "page_diffusion": {
                "distinct_scan_pages": len(pages),
                "tokens_on_the_densest_500_pages": sum(dense[:500]),
                "reading": "a re-OCR reaches a few percent of this class; it is "
                           "spread thin, not concentrated on bad pages",
            },
            "decided": decided[:400],
        },
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    SHEET.write_text(json.dumps({
        "what": "the repair tranche proposed for issue #31, NOT APPLIED",
        "issue": "open-greek/open-greek-corpus#31",
        "status": "waiting on cisco. Every token here is wrong as it stands, "
                  "since a non-final grave is not Greek, so the question is not "
                  "whether to leave them right but whether this rule is right "
                  "often enough to be worth the wrong ones it will introduce.",
        "scope": "our own OCR only (source `ocr`). cgpg is calfa-co's OCR and "
                 "first1k, perseus, dfhg, pta and saws are other people's "
                 "editions that this repo republishes; whether we may correct "
                 "those is a policy question nothing in docs/ answers, and "
                 "holding them costs 3.5% of the tranche.",
        "rule": f"the form's skeleton class has a reading holding >= "
                f"{TRANCHE_SHARE} of >= {TRANCHE_CLEAN} clean non-OCR tokens, "
                f"and the repair changes accents only: breathings, iota "
                f"subscript and diaeresis are byte-identical between the form "
                f"and its target.",
        "forms": len(tranche), "tokens": tr_tokens,
        "token_weighted_share": round(weighted, 4),
        "expected_wrong_tokens": round(tr_tokens * (1 - weighted)),
        "how_to_read_the_error": "the expected-wrong figure treats the class "
            "share as the chance the token is that word, which overstates it. "
            "Most runner-up readings are not different words: ἔγωγέ is ἔγωγε "
            "carrying an enclitic's acute, Επειδή is Ἐπειδή with the breathing "
            "lost. A hand pass over the largest forms is what would settle it.",
        "what_it_would_NOT_touch": {
            "marks_moved": sum(d["tokens"] for d in decided
                               if not d["accent_only"]),
            "why": "moving a breathing or an iota subscript is a lexical claim, "
                   "not a stress one, and belongs in its own tranche",
            "undecided": sum(bucket_tokens[k] for k in bucket_tokens
                             if k != f"dominant >= {DOMINANT}"),
        },
        "rows": tranche,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)} and {SHEET.relative_to(REPO)}")


if __name__ == "__main__":
    main()
