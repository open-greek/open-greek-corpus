#!/usr/bin/env python3
"""Serve Walz I 263-420 as its own work instead of as a witness to a text it
does not share.

`nicolaus-rhetoric.progymnasmata` is served from Felten's handbook and carries
two witnesses. One of them, Spengel Rhetores Graeci III, really is that work in
another edition: word-bigram containment 0.720 against the served text. The
other, our OCR of Walz Rhetores Graeci I 263-420, scores 0.123, which is where
unrelated progymnasmata of the same genre land. Filing it as a witness asserted
an identity the bytes refuse (issue #28), and because both witnesses share one
file the published quality report averaged them into a meaningless 0.275.

Two printed editors settle what it is, and they agree from opposite directions.
Walz prints it at 263 as ΝΙΚΟΛΑΟΥ ΣΟΦΙΣΤΟΥ ΠΡΟΓΥΜΝΑΣΜΑΤΑ with no qualifier,
heads every verso across all 158 pages ΝΙΚΟΛΑΟΥ, lists it in his contents as a
bare Νικολάου προγυμνάσματα where he writes Ἀνωνύμου for the anonymous pieces,
and at 265 defends the ascription against Schöll. But at 264 he says what he is
printing are the paradigmata from Par. 2918, the theoria being a separate work
of Nicolaus he has not got. Felten, editing that handbook in 1913, says the same
from his side: in codicibus Nicolao tribuuntur exempla, Μελέται Suidae, quae
praecepta illa illustrant, cf. Walz I 266 sq., and then that the connection is
nondum constat.

So: Nicolaus for the author, because both editors and the manuscripts say so, a
distinct work rather than a second copy of the handbook, and the note carries
Felten's caveat rather than swallowing it.

  python3 scripts/promote_walz_nicolaus_paradigmata.py
  python3 scripts/promote_walz_nicolaus_paradigmata.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus_secondary" / "nicolaus-rhetoric.progymnasmata.jsonl"
PRIMARY = DATA / "corpus" / "nicolaus-rhetoric.progymnasmata.jsonl"
NEW_SLUG = "nicolaus-rhetoric.progymnasmata-walz-i-263"
OUT = DATA / "corpus" / f"{NEW_SLUG}.jsonl"
AUDIT = DATA / "corpus_changes" / f"{NEW_SLUG}.witness-promote.json"
ARCHIVE = DATA / "corpus_changes" / f"{NEW_SLUG}.pre-promote.jsonl"

EXPECT_ROWS, EXPECT_WALZ, EXPECT_TOKENS = 1235, 932, 36298
RETIRED = "nicolaus-history.nicolaus-progymnasmata-felten"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from build_ocr_quality_report import work_bigrams, containment  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    before = SRC.read_text(encoding="utf-8")
    rows = [json.loads(l) for l in before.splitlines() if l.strip()]
    walz = [r for r in rows if "walz" in str(r.get("edition", "")).lower()]
    rest = [r for r in rows if "walz" not in str(r.get("edition", "")).lower()]
    toks = sum(len(_GK.findall(r.get("text") or "")) for r in walz)

    # Move rows by a shape assertion, never by the witness string alone: a
    # promote that ran on the wrong rows leaves no trace afterwards.
    if len(rows) != EXPECT_ROWS:
        fail(f"expected {EXPECT_ROWS} rows in the witness file, found {len(rows)}")
    if len(walz) != EXPECT_WALZ or toks != EXPECT_TOKENS:
        fail(f"expected {EXPECT_WALZ} Walz rows / {EXPECT_TOKENS} tokens, "
             f"found {len(walz)} / {toks}")

    pri = [json.loads(l) for l in PRIMARY.read_text(encoding="utf-8").splitlines()
           if l.strip()]
    P = work_bigrams(pri)
    c_walz, c_rest = containment(work_bigrams(walz), P), containment(work_bigrams(rest), P)
    print(f"Walz slice   {len(walz)} rows, {toks:,} tokens, containment {c_walz:.3f}")
    print(f"kept witness {len(rest)} rows, containment {c_rest:.3f}")
    # The identity claim, asserted rather than assumed. If the Walz slice ever
    # looked like the served work, promoting it would be splitting one work in
    # two, which is the opposite mistake and just as bad.
    if c_walz > 0.15:
        fail(f"Walz containment {c_walz:.3f} is too high to call this a different "
             f"work; it may be an edition of the served text after all")
    if c_rest < 0.65:
        fail(f"the retained witness scores only {c_rest:.3f}; it should be the "
             f"genuine other edition and something has changed")

    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if OUT.exists():
        fail(f"{OUT.relative_to(REPO)} already exists")

    ARCHIVE.write_text(before, encoding="utf-8")
    out = []
    for r in walz:
        n = dict(r)
        n["urn"] = NEW_SLUG
        for k in ("rank", "secondary_reason", "witness"):
            n.pop(k, None)
        # The volume dump's placeholder, which was never true of these rows and
        # is meaningless now that they are a work.
        if str(n.get("cts", "")).startswith("n/a"):
            n.pop("cts", None)
        out.append(n)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out),
                   encoding="utf-8")

    for r in rest:
        if RETIRED in str(r.get("secondary_reason", "")):
            r["secondary_reason"] = (
                "edition witness of this work: Spengel Rhetores Graeci III "
                "449-498 against the served Felten text, word-bigram containment "
                f"{c_rest:.3f}")
    SRC.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rest),
                   encoding="utf-8")

    AUDIT.write_text(json.dumps({
        "what": f"Walz Rhetores Graeci I 263-420 promoted from a witness of "
                f"nicolaus-rhetoric.progymnasmata to the served work {NEW_SLUG}",
        "date": "2026-08-09",
        "issue": "open-greek/open-greek-corpus#28",
        "why": "the rows share almost none of the text they were filed against "
               f"(containment {c_walz:.3f}, where the genuine other edition scores "
               f"{c_rest:.3f}), so the witness relation asserted an identity the "
               "bytes refuse",
        "author_evidence": {
            "walz": "title at printed 263 ΝΙΚΟΛΑΟΥ ΣΟΦΙΣΤΟΥ ΠΡΟΓΥΜΝΑΣΜΑΤΑ with no "
                    "qualifier; every verso running head across 263-420 reads "
                    "ΝΙΚΟΛΑΟΥ; contents entry a bare Νικολάου προγυμνάσματα where "
                    "Walz writes Ἀνωνύμου for anonymous items; at 265 he defends "
                    "the ascription against Schöll, citing Par. 2918",
            "walz_caveat": "at 264 Walz says he prints the paradigmata from Par. "
                           "2918 and that Nicolaus' theoria is a separate work he "
                           "has not found, and closes that among these men "
                           "ownership is so uncertain that he has no hope of "
                           "restoring to each what is his own",
            "felten": "praefatio to the 1913 Teubner handbook: in codicibus "
                      "Nicolao tribuuntur exempla, Μελέται Suidae, quae praecepta "
                      "illa illustrant et ipsa quoque Προγυμνάσματα nominantur "
                      "(cf. Walz I 266 sq.), sed qui nexus huic Nicolao cum illis "
                      "intercedat, nondum constat",
            "conclusion": "Nicolaus for the author on both editors' authority and "
                          "the manuscripts', but a DIFFERENT work from the "
                          "handbook, which is what both of them say in their own "
                          "words",
        },
        "rows": len(walz), "greek_tokens": toks,
        "containment_against_served_primary": round(c_walz, 4),
        "retained_witness_containment": round(c_rest, 4),
        "archived_pre_state": str(ARCHIVE.relative_to(REPO)),
        "sha256_before": hashlib.sha256(before.encode()).hexdigest(),
        "reverse": f"restore {ARCHIVE.name} over {SRC.name} and delete "
                   f"data/corpus/{NEW_SLUG}.jsonl",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {len(walz)} rows -> {OUT.relative_to(REPO)}, "
          f"audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
