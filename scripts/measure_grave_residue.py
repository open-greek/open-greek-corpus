#!/usr/bin/env python3
"""Partition the grave-lemma residue by whether any accent rule could reach it.

9,186 lemmas in the per-work table still carry a grave, holding 42,711 tokens
(issue #4). No dictionary headword carries a grave, so each of them is either a
headword in the wrong citation form or not a headword at all, and the issue has
been treated as one defect throughout. It is two, in very different proportions,
and which one it mostly is decides whether #4 is a `data-defect` or a
`limitation`.

The rules this repo has for the class all work the same way: they move a grave
lemma onto its acute counterpart, and they can only do that when the acute is
attested. So the reachable part of the residue is exactly the part whose acute
counterpart exists as a lemma. Everything else is out of reach of ANY rule of
that shape, no matter how the thresholds are set, because there is nothing to
move it onto.

What the unreachable part turns out to be is not a lemmatization problem at all.
It is OCR shrapnel (οὐδὲς, ταὺτ, κλὴν, μηδὲς) and inflected forms that were
never headwords (Παντὸς, παραστὰς). Those are not citation forms in the wrong
accent; they are strings no lexicon holds under any accent. Repairing them is an
OCR-quality question wearing a lemmatization costume, which is worth saying on
the issue plainly, because three rounds have now gone looking for an accent rule
that could reach them.

Counts come from the per-work table, which is the table the rules are applied
to, and from nothing else. No external authority is consulted: the annotation
exports are produced by the same lemmatizer that produced this residue, so they
cannot independently confirm a headword here.

  python3 scripts/measure_grave_residue.py            # report
  python3 scripts/measure_grave_residue.py --write    # -> data/grave_residue.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
WORK_LEMMAS = DATA / "work_lemma_counts.tsv.gz"
OUT = DATA / "grave_residue.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import VARIA, lower_initial, to_acute  # noqa: E402


def load_totals() -> dict[str, int]:
    out: dict[str, int] = {}
    with gzip.open(WORK_LEMMAS, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2].isdigit():
                out[p[1]] = out.get(p[1], 0) + int(p[2])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    totals = load_totals()
    grave = {k: v for k, v in totals.items()
             if VARIA in unicodedata.normalize("NFD", k)}
    reachable, unreachable = {}, {}
    for lemma, n in grave.items():
        acute = to_acute(lemma)
        # Either spelling counts as the target: the capital may be positional,
        # and #19's fold handles that separately, so refusing to see the
        # lowercase acute here would understate what is reachable.
        cands = {acute, to_acute(lower_initial(lemma))} - {lemma}
        hit = next((c for c in cands if totals.get(c, 0)), None)
        (reachable if hit else unreachable)[lemma] = (n, hit)

    # Slightly above audit_lemma_table's count, which classifies each lemma once
    # and lets an earlier class claim some of these first. Same population.
    gt, rt = sum(grave.values()), sum(n for n, _ in reachable.values())
    ut = sum(n for n, _ in unreachable.values())
    print(f"grave residue: {len(grave):,} lemmas, {gt:,} tokens "
          f"({gt / sum(totals.values()):.3%} of the lemmatized corpus)")
    print(f"  reachable   {len(reachable):>6,} lemmas {rt:>8,} tokens "
          f"{rt / gt:>6.1%}  an acute counterpart is attested to move them onto")
    print(f"  unreachable {len(unreachable):>6,} lemmas {ut:>8,} tokens "
          f"{ut / gt:>6.1%}  no acute counterpart under either case, so no rule "
          f"of this shape reaches them")
    print("\n  largest unreachable, which is what the residue actually is:")
    for lemma, (n, _) in sorted(unreachable.items(), key=lambda kv: -kv[1][0])[:12]:
        print(f"    {lemma:<16} {n:>6,}")
    print("\n  largest reachable, and note that reachable does NOT mean worth "
          "repairing:\n  a target attested at 2 or 10 tokens is shrapnel too, so "
          "moving onto it\n  empties the audit class without producing a headword:")
    for lemma, (n, hit) in sorted(reachable.items(), key=lambda kv: -kv[1][0])[:8]:
        print(f"    {lemma:<16} {n:>6,} -> {hit} ({totals.get(hit, 0):,})")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "the grave-lemma residue partitioned by whether any accent rule "
                "could reach it",
        "issue": "open-greek/open-greek-corpus#4",
        "source": "data/work_lemma_counts.tsv.gz, and nothing else",
        "why_no_external_authority": "the annotation exports come from the same "
            "lemmatizer that produced this residue, so they cannot independently "
            "confirm a headword for it",
        "lemmas": len(grave), "tokens": gt,
        "reachable": {"lemmas": len(reachable), "tokens": rt,
                      "caveat": "reachable is an upper bound on what a rule could "
                                "touch, not an estimate of what is worth touching: "
                                "many targets are themselves shrapnel attested at a "
                                "handful of tokens (λλά at 10, μονονοχί at 2), and "
                                "merging onto those empties the audit class without "
                                "producing a headword"},
        "unreachable": {"lemmas": len(unreachable), "tokens": ut,
                        "note": "no acute counterpart is attested under either "
                                "case, so no rule that moves a grave lemma onto "
                                "its acute can reach these regardless of "
                                "threshold; they are OCR shrapnel and non-headword "
                                "inflected forms, an OCR-quality problem rather "
                                "than a lemmatization one"},
        "largest_unreachable": [
            {"lemma": k, "tokens": n}
            for k, (n, _) in sorted(unreachable.items(),
                                    key=lambda kv: -kv[1][0])[:40]],
        "largest_reachable": [
            {"lemma": k, "tokens": n, "target": h, "target_tokens": totals.get(h, 0)}
            for k, (n, h) in sorted(reachable.items(),
                                    key=lambda kv: -kv[1][0])[:40]],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
