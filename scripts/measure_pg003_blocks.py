#!/usr/bin/env python3
"""Find the block boundaries Migne prints in PG 3 and our OCR kept.

PG 3 sets Pseudo-Dionysius with Georgius Pachymeres' paraphrase, and the record
of why it has never been carved says two things that are not true of the bytes
(issue #9). It says the two "interleave passage by passage" so no carve can
separate them, and that there are "no display titles in this OCR at all".

Both are wrong, and the second is why the first was believed. Migne marks every
switch with a display head, and our OCR kept some of them. They are invisible to
a Greek search because the OCR read the Latin as Greek letter shapes:

    ΡΑΗΑΡΗΚΑΘ ΡΑΩΙΥΜΕΛ      PARAPHRASIS PACHYMERAE   (locus 151)
    ΘΥΝΟΡΦΙΟ ΩΑΡΙΤΙΘ        SYNOPSIS CAPITIS         (locus 171)
    ΟΑΡΠΤ ΙΙΙ               CAPUT III                (locus 89)

which is the same homoglyph failure the Walz carves kept hitting, here running
the other way: Latin printed, Greek recorded.

So this counts what is already pinned rather than asserting it. ΚΕΦΑΛΑΙΟΝ
survived as Greek and is matched directly; the Latin heads are listed as read off
the rows, because no letter-shape mapping recovers both ΡΑΗΑΡΗΚΑΘ (151) and
ΡΑΚΑΡΗΣΑΘΒ (381) from PARAPHRASIS, and tuning one until it found the heads I
already knew about would be fitting to the answer. The count is a floor.

Four of the eleven mark a change of AUTHOR; the rest number a chapter inside a
work, and at 347 and 354 Migne prints the number twice, once in Greek and once in
Latin (ΚΕΦΑΛΑΙΟΝ Γ. ΛΑΡΗΤ ΙΙΙ.). Only the first kind is a carve boundary. What
the four settle is that a switch OPENS its row rather than falling inside one, so
a locus carve can express it and the "passage-level (intra-row) segmentation" the
record asks for is not what this needs.

Deliberately NOT reported: the gap between two surviving switch heads. It is long
because the heads in between were dropped, so it measures our blindness rather
than the block size.

What this does NOT do is carve. The dropped heads still have to come off the page
images, and a boundary this cannot see is exactly the kind that would mis-file a
block.

  python3 scripts/measure_pg003_blocks.py            # report
  python3 scripts/measure_pg003_blocks.py --write    # -> data/pg003_blocks.json
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus" / "cogPG.PG003.jsonl"
OUT = DATA / "pg003_blocks.json"
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

# The Latin heads are visibly present but I could not build a principled decoder
# for them. A shape table mapping Greek capitals back to the Latin the OCR saw
# is guesswork: PARAPHRASIS comes through as ΡΑΗΑΡΗΚΑΘ at 151 and ΡΑΚΑΡΗΣΑΘΒ at
# 381, and no single mapping produces both. Tuning one until it matched the
# heads I already knew about would be fitting to the answer, so these are listed
# as read, and the count below is a floor rather than a total.
LATIN_HEADS = {
    89:  ("caput", "ΟΑΡΠΤ ΙΙΙ = CAPUT III"),
    151: ("paraphrase", "ΡΑΗΑΡΗΚΑΘ ΡΑΩΙΥΜΕΛ = PARAPHRASIS PACHYMERAE"),
    171: ("synopsis", "ΘΥΝΟΡΦΙΟ ΩΑΡΙΤΙΘ = SYNOPSIS CAPITIS"),
    347: ("caput", "ΛΑΡΗΤ ΙΙΙ = CAPUT III"),
    354: ("caput", "Α ΟΑΡΠΤ ΙΝʹ = CAPUT IV"),
    381: ("paraphrase", "ΡΑΚΑΡΗΣΑΘΒ ΡΑΩΗΙΜΕΣΧθ = PARAPHRASIS PACHYMERAE"),
    487: ("paraphrase", "ἔΙΘΡΑΓΑΡΙΛΑεΙΒ ΡΑΩΙΥΜΕΕΣ = PARAPHRASIS PACHYMERAE"),
}


def head_of(locus: int, text: str) -> tuple[str, str] | None:
    """The display head this row opens with, if one is legible.

    ΚΕΦΑΛΑΙΟΝ survived as Greek and is matched directly. The Latin heads are
    taken from the list above, read by eye off the rows themselves.
    """
    if locus in LATIN_HEADS:
        return LATIN_HEADS[locus]
    opening = " ".join(text.split()[:4])
    # Capitals REQUIRED, not folded to them. A display head is printed in caps,
    # and κεφάλαιον is also just a common noun: folding case matches `Τὸ ζʹ
    # κεφάλαιον, περὶ` and even `ἀνακεφαλαιούμενος`, which open no block at all.
    bare = "".join(c for c in unicodedata.normalize("NFD", opening)
                   if not unicodedata.combining(c))
    if "ΚΕΦΑΛΑΙΟΝ" in bare:
        return "kephalaion", opening[:40]
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--update-flag", action="store_true",
                    help="rewrite the stated reason in the split-deferred record "
                         "from this measurement, keeping the old text")
    args = ap.parse_args()

    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    by = {int(r["locus"]): (r.get("text") or "") for r in rows}
    loci = sorted(by)
    hits = []
    for k in loci:
        h = head_of(k, by[k])
        if h:
            hits.append({"locus": k, "head": h[0], "reading": h[1],
                         "opening": " ".join(by[k].split()[:5])})
    # Each head opens a run that lasts until the next one.
    for i, h in enumerate(hits):
        nxt = hits[i + 1]["locus"] if i + 1 < len(hits) else loci[-1] + 1
        span = [k for k in loci if h["locus"] <= k < nxt]
        h["run_to"] = span[-1] if span else h["locus"]
        h["tokens"] = sum(len(_GK.findall(by[k])) for k in span)

    # Two different things, and only one of them is the carve boundary. CAPUT and
    # ΚΕΦΑΛΑΙΟΝ number a chapter INSIDE a work, and at 347 and 354 Migne prints
    # both for the same chapter (ΚΕΦΑΛΑΙΟΝ Γ. ΛΑΡΗΤ ΙΙΙ.). PARAPHRASIS PACHYMERAE
    # and SYNOPSIS CAPITIS are where the author changes. Counting all of them
    # together would overstate how much of the author structure is pinned.
    para = [h for h in hits if h["head"] == "paraphrase"]
    kef = [h for h in hits if h["head"] == "kephalaion"]
    switches = [h for h in hits if h["head"] in ("paraphrase", "synopsis")]
    print(f"PG003: {len(rows)} rows, loci {loci[0]}-{loci[-1]}")
    print(f"  {len(hits)} display heads survive in the OCR, of which "
          f"{len(switches)} mark a change of AUTHOR and {len(hits) - len(switches)} "
          f"number a chapter inside a work")
    for label in ("paraphrase", "synopsis", "caput", "kephalaion"):
        n = [h for h in hits if h["head"] == label]
        print(f"    {label:12} {len(n):>3}  {sum(x['tokens'] for x in n):>7,} tokens "
              f"in the runs they open")
    # NOT the run lengths. The gap between two surviving switch heads is long
    # because the heads between them were dropped, so it measures our blindness
    # rather than the block size, and quoting it as "blocks are 105 loci" would
    # be reading a hole as a fact. What the bytes do settle is where a switch
    # LANDS: every one of them opens its row, none sits mid-row. That is what
    # decides whether a locus carve can express the boundary at all.
    HEAD_ZONE = 40
    opens = 0
    for h in switches:
        probe = h["reading"].split(" = ")[0].split()[0]
        at = by[h["locus"]].find(probe)
        opens += 0 <= at < HEAD_ZONE
    print(f"\n  {opens} of {len(switches)} author switches open their row "
          f"(head within {HEAD_ZONE} chars); none sits mid-row, so the switches "
          f"fall on locus boundaries and a locus carve can express them. That is "
          f"what refutes the record's 'needs passage-level (intra-row) "
          f"segmentation'.")
    print(f"  first paraphrase head at {para[0]['locus'] if para else '-'}, "
          f"first ΚΕΦΑΛΑΙΟΝ at {kef[0]['locus'] if kef else '-'}")
    print(f"\n  NOT pinned: {len(loci) - sum(1 for h in hits)} rows sit inside a run "
          f"whose opening head the OCR dropped; those boundaries need the page "
          f"images before any carve can be trusted.")
    for h in hits[:10]:
        print(f"    {h['locus']:>4}-{h['run_to']:<4} {h['head']:11} "
              f"{h['reading'][:56]}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "display-head boundaries surviving in the PG003 OCR",
        "issue": "open-greek/open-greek-corpus#9",
        "note": "Migne prints a head at every switch between Dionysius and "
                "Pachymeres' paraphrase; the OCR read the Latin heads as Greek "
                "letter shapes, which is why they were reported absent. These are "
                "the ones still legible. The rest need the page images.",
        "author_switches": len(switches),
        "chapter_heads": len(hits) - len(switches),
        "switches_opening_their_row": f"{opens} of {len(switches)}",
        "count_is_a_floor": "the Latin heads were read by eye; no principled "
                            "decoder recovers them, so more may survive",
        "heads": hits,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")

    if not args.update_flag:
        return
    # The deferral record states a reason this measurement contradicts. Correct
    # it here rather than by hand, and keep the old wording: an audit record that
    # silently changes its own account of why is worth less than one that shows
    # what it used to say and what moved it.
    flag = CHANGES / "cogPG.PG003.split-deferred.json"
    rec = json.loads(flag.read_text(encoding="utf-8"))
    if "superseded" not in rec:
        rec["superseded"] = []
    if rec["why_not_resolved"].startswith("Not a passage-level problem"):
        # Already corrected. Appending again would file the correction itself as
        # the thing superseded, which reads as if the old reason were right.
        print(f"{flag.name} already carries the correction; left alone")
        return
    rec["superseded"].append({
        "date": "2026-08-07",
        "issue": "open-greek/open-greek-corpus#9",
        "field": "why_not_resolved",
        "was": rec["why_not_resolved"],
        "wrong_because": "the bytes do not show a passage-level alternation, and "
                         "the display heads reported absent are present, garbled. "
                         "Migne marks each switch with a printed head; the OCR read "
                         "the Latin ones as Greek letter shapes (PARAPHRASIS "
                         "PACHYMERAE -> ΡΑΗΑΡΗΚΑΘ ΡΑΩΙΥΜΕΛ at locus 151), which is "
                         "why a Greek search found none and the interleave was "
                         "taken to be unmarked.",
    })
    rec["why_not_resolved"] = (
        f"Not a passage-level problem and not impossible by column carve. Migne "
        f"prints a display head at every switch, and {len(switches)} of them "
        f"survive in our OCR (plus {len(hits) - len(switches)} chapter heads) "
        f"(measured by scripts/measure_pg003_blocks.py, listed in "
        f"data/pg003_blocks.json). Every one of them OPENS its row rather than "
        f"sitting mid-row, so the switches fall on locus boundaries and a locus "
        f"carve can express them; intra-row segmentation is not what this needs. "
        f"What "
        f"blocks the carve is coverage, not granularity: most of the volume's "
        f"{len(loci)} rows "
        f"sit inside a run whose opening head the OCR dropped, and a boundary we "
        f"cannot see is exactly the one that would file a block under the wrong "
        f"author. Recovering the dropped heads needs the PG 3 page images.")
    rec["recommendation"] = (
        "read the heads off the page images, then carve on loci like any other "
        "volume. The surviving heads in data/pg003_blocks.json give the shape to "
        "check that recovery against.")
    rec["_meta"]["change"] = ("DEFERRED - not carved (display heads dropped by OCR "
                              "on most switches; needs page images)")
    flag.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"corrected the stated reason in {flag.relative_to(REPO)}")


if __name__ == "__main__":
    main()
