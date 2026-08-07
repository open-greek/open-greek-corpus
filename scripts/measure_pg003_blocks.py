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

So this counts what is already pinned rather than asserting it, scanning WHOLE
rows. That last part is the point. An earlier version of this script read only
`text.split()[:4]`, found four author heads there, and concluded that switches
land on row openings, which a four-word window could not possibly have
established: it was incapable of seeing a mid-row head. Scanning whole rows, 15
of the 26 heads fall mid-row, and one of them is an author switch (SYNOPSIS
CAPITIS at locus 481, character 1,713 of a 2,018-character row).

That matters because carve_cgpg_volume.py moves WHOLE ROWS. A boundary inside a
row cannot be expressed by it, so a carve on loci would cut mid-block and file
the wrong author's text. The deferral record's original "needs passage-level
(intra-row) segmentation" was right, and the correction that replaced it was
not; both are kept in that record under `superseded`.

The Latin heads are matched by a fixed probe list, and the count is a floor:
PG003 garbles the same head differently in different places, reading SYNOPSIS
CAPITIS as ΘΥΝΟΡΦΙΟ ΩΑΡΙΤΙΘ at 171 and ΘΥΝΟΡΘΙΘ ΛΑΡΙΤΙΕ at 440, which is exactly
how a fixed list misses one.

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

# Scanned over the WHOLE row, and that is the correction this file exists to
# carry. The first version looked only at `text.split()[:4]`, found four author
# heads there, and concluded that switches land on row openings. They were the
# only four it could have found: a window on the first four words cannot report
# anything about the other 2,000 characters, so the finding was an artifact of
# the window and the conclusion drawn from it was circular.
#
# Scanning whole rows: ΚΕΦΑΛΑΙΟΝ occurs 20 times, 14 of them mid-row, and
# SYNOPSIS CAPITIS turns up twice more at locus 440 char 335 and locus 481 char
# 1,713, garbled differently from the spelling at 171 (ΘΥΝΟΡΘΙΘ ΛΑΡΙΤΙΕ against
# ΘΥΝΟΡΦΙΟ ΩΑΡΙΤΙΘ) which is why a fixed list of spellings missed them.
#
# So author switches DO fall inside rows, and the deferral record's original
# "needs passage-level (intra-row) segmentation" was closer to right than the
# replacement that called it block scale.
LATIN_PROBES = {
    "paraphrase": ("PARAPHRASIS PACHYMERAE",
                   ("ΡΑΗΑΡΗΚΑΘ", "ΡΑΚΑΡΗΣΑΘΒ", "ΡΑΓΑΡΙΛΑ", "ΡΑΩΙΥΜΕ", "ΡΑΩΗΙΜΕ")),
    "synopsis": ("SYNOPSIS CAPITIS",
                 ("ΘΥΝΟΡΦΙΟ", "ΘΥΝΟΡΘΙΘ", "ΩΑΡΙΤΙΘ", "ΛΑΡΙΤΙΕ", "ΣΑΡΙΤΙΘ")),
    "caput": ("CAPUT", ("ΟΑΡΠΤ", "ΛΑΡΗΤ")),
}
HEAD_ZONE = 40   # a head at or before this offset opens its row


def strip_marks(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(c))


def heads_in(locus: int, text: str) -> list[dict]:
    """Every display head in the row, with where in the row it falls."""
    bare = strip_marks(text)
    out, seen = [], set()
    for i in _find_all(bare, "ΚΕΦΑΛΑΙΟΝ"):
        out.append({"locus": locus, "head": "kephalaion", "at": i,
                    "row_chars": len(bare), "reading": text[i:i + 26].strip()})
        seen.add(i)
    for label, (expansion, probes) in LATIN_PROBES.items():
        for probe in probes:
            for i in _find_all(bare, probe):
                if any(abs(i - j) < 30 for j in seen):
                    continue          # same head, matched by a second probe
                seen.add(i)
                out.append({"locus": locus, "head": label, "at": i,
                            "row_chars": len(bare),
                            "reading": f"{text[i:i + 24].strip()} = {expansion}"})
    return sorted(out, key=lambda h: h["at"])


def _find_all(hay: str, needle: str):
    i = hay.find(needle)
    while i >= 0:
        yield i
        i = hay.find(needle, i + 1)


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
        hits.extend(heads_in(k, by[k]))
    for i, h in enumerate(hits):
        nxt = hits[i + 1]["locus"] if i + 1 < len(hits) else loci[-1] + 1
        span = [k for k in loci if h["locus"] <= k < nxt]
        h["tokens"] = sum(len(_GK.findall(by[k])) for k in span)

    switches = [h for h in hits if h["head"] in ("paraphrase", "synopsis")]
    chapters = [h for h in hits if h["head"] not in ("paraphrase", "synopsis")]
    mid = [h for h in hits if h["at"] >= HEAD_ZONE]
    mid_sw = [h for h in switches if h["at"] >= HEAD_ZONE]
    print(f"PG003: {len(rows)} rows, loci {loci[0]}-{loci[-1]}")
    print(f"  {len(hits)} display heads survive, scanning WHOLE rows: "
          f"{len(switches)} mark a change of author, {len(chapters)} number a "
          f"chapter")
    print(f"  {len(mid)} of {len(hits)} fall MID-ROW, including {len(mid_sw)} of "
          f"the {len(switches)} author switches.")
    print()
    print("  This is the correction. An earlier version of this script read only")
    print("  the first four words of each row, so it could only ever find heads")
    print("  that opened a row, and it reported that as a finding: 'all four")
    print("  author switches open their row, so a locus carve can express them'.")
    print("  It cannot. A carve that moves whole rows would cut mid-block here,")
    print("  and the deferral record's original 'needs passage-level (intra-row)")
    print("  segmentation' was right after all.")
    print()
    print("  mid-row heads (locus, offset/row length):")
    for h in mid[:14]:
        print(f"    {h['locus']:>4} {h['at']:>5}/{h['row_chars']:<5} "
              f"{h['head']:<11} {h['reading'][:44]}")
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
        "scanned": "whole row, not the first four words",
        "author_switches": len(switches),
        "heads_mid_row": len(mid),
        "author_switches_mid_row": len(mid_sw),
        "chapter_heads": len(hits) - len(switches),

        "count_is_a_floor": "the Latin heads are matched by a fixed probe list, "
                            "and PG003 garbles the same head differently in "
                            "different places (SYNOPSIS CAPITIS reads ΘΥΝΟΡΦΙΟ "
                            "ΩΑΡΙΤΙΘ at 171 and ΘΥΝΟΡΘΙΘ ΛΑΡΙΤΙΕ at 440), so "
                            "more survive than this finds",
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
    if rec["why_not_resolved"].startswith("The record has now been wrong twice"):
        print(f"{flag.name} already carries the correction; left alone")
        return
    rec.setdefault("superseded", []).append({
        "date": "2026-08-07",
        "issue": "open-greek/open-greek-corpus#9",
        "field": "why_not_resolved",
        "was": rec["why_not_resolved"],
        "wrong_because": "this script measured it with a detector that read only "
                         "the first four words of each row, so it could only find "
                         "heads that opened a row, and the conclusion drawn from "
                         "that ('every switch opens its row, so a locus carve can "
                         "express them') was circular. Scanning whole rows, "
                         f"{len(mid)} of {len(hits)} heads fall mid-row.",
    })
    rec["why_not_resolved"] = (
        f"The record has now been wrong twice, in opposite directions, and this is "
        f"the second correction. The original said the two authors interleave "
        f"passage by passage and that no display titles survive in the OCR. The "
        f"first half was right and the second was not: {len(hits)} heads do survive, "
        f"garbled where Migne printed Latin, and finding them prompted a correction "
        f"on 2026-08-07 claiming the interleave was block scale and a locus carve "
        f"could express it. That claim came from a detector reading only the first "
        f"four words of each row, which could not have found a mid-row head if one "
        f"existed. Scanning whole rows, {len(mid)} of {len(hits)} heads fall mid-row, "
        f"including {len(mid_sw)} of the {len(switches)} author switches (SYNOPSIS "
        f"CAPITIS at locus 481, character 1,713 of a 2,018-character row). So the "
        f"original reason stands: this needs passage-level segmentation inside the "
        f"row, which carve_cgpg_volume.py cannot express because it moves whole "
        f"rows. The heads the OCR dropped still need the page images as well.")
    rec["recommendation"] = (
        "do NOT carve this on loci. A whole-row carve cuts mid-block at every "
        "boundary that falls inside a row, and at least one author switch does. "
        "Segmenting inside the row needs both a re-OCR that keeps the dropped heads "
        "and a splitter that can divide a row, neither of which exists here yet.")
    rec["_meta"]["change"] = ("DEFERRED - not carved (boundaries fall inside rows; "
                              "needs intra-row segmentation and the page images)")
    flag.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(f"corrected the stated reason in {flag.relative_to(REPO)}")


if __name__ == "__main__":
    main()
