#!/usr/bin/env python3
"""Partition the grave-lemma residue by whether any accent rule could reach it.

9,186 lemmas in the per-work table still carry a grave, holding 42,711 tokens
(issue #4). No dictionary headword carries a grave, so each of them is either a
headword in the wrong citation form or not a headword at all, and the issue has
been treated as one defect throughout. It is two, in very different proportions,
and which one it mostly is decides whether #4 is a `data-defect` or a
`limitation`.

The rules this repo has for the class all work the same way: they move a grave
lemma onto its acute counterpart, and only where the acute is attested. So
reachability is a question about ATTESTATION, and the first version of this
script asked it of the wrong table.

It asked whether the acute exists as a LEMMA in the per-work table and reported
77.4% of the residue unreachable "regardless of threshold". The accent argument
is about the printed text - a grave is what a final acute becomes before a pause
- so what settles it is whether the corpus PRINTS the acute spelling, which
data/public_lexicon.tsv answers with no lemmatizer in the loop. Asked that way,
on the same residue, the unreachable share was 52.3%, not 77.4%. The gap was the
rule's reference table (83,078 lemmas) being narrower than the table it governs
(275,871), and "regardless of threshold" was wrong.

grave_lemma_repair now reads printed forms, which consumed most of that gap:
10,135 tokens moved onto acute spellings the corpus actually prints. What is
left is the genuinely unreachable part, and it is a larger SHARE of a smaller
residue precisely because the reachable part has been taken. Both partitions
are still printed, since the old one is what the issue was quoting.

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
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
WORK_LEMMAS = DATA / "work_lemma_counts.tsv.gz"
OUT = DATA / "grave_residue.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import (VARIA, PRINTED_FORMS,  # noqa: E402
                                lower_initial, to_acute)


def load_totals() -> dict[str, int]:
    out: dict[str, int] = {}
    with gzip.open(WORK_LEMMAS, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2].isdigit():
                out[p[1]] = out.get(p[1], 0) + int(p[2])
    return out


# Dictionary headword inventories from the sibling public repo open-greek/dilemma
# (https://github.com/open-greek/dilemma), checked out beside this one. These are
# an authority INDEPENDENT of the lemmatizer that produced this residue, which is
# the gap the `why_no_external_authority` note used to record.
#
# Which lists, and why not all eleven. Included are the scholarly ancient and
# Byzantine lexica: LSJ and LSJ10, the Lexikon zur byzantinischen Graezitaet,
# DGE, Montanari's VLG, Cunliffe's Homeric lexicon, the Perseus aggregate of
# L&S/Pape/Bailly, and Aristarchus' Words in Progress. Excluded are
# ag_headwords, which is Wiktionary-derived and lists 72 of these grave lemmas
# as headwords themselves, which no real lexicon does, and mg_headwords, which
# is Modern Greek and answers a different question.
HEADWORD_FILES = ("lsj", "lsj10", "lbg", "dge", "vlg", "cunliffe", "pd", "wip")
DILEMMA = REPO.parent / "dilemma" / "data"


def load_headwords() -> tuple[set, list[dict]]:
    """(headword set, per-source provenance). Empty when the sibling checkout is
    absent, and the caller must then omit the partition rather than publish it
    as zero, which would read as a far stronger claim than no data supports."""
    words: set[str] = set()
    prov = []
    for name in HEADWORD_FILES:
        fp = DILEMMA / f"{name}_headwords.json"
        if not fp.exists():
            continue
        raw = json.loads(fp.read_text(encoding="utf-8"))
        got = {e["lemma"] if isinstance(e, dict) else e for e in raw}
        got = {unicodedata.normalize("NFC", w) for w in got if isinstance(w, str)}
        words |= got
        prov.append({"source": name, "entries": len(got),
                     "sha256": hashlib.sha256(fp.read_bytes()).hexdigest()})
    return words, prov


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    totals = load_totals()
    grave = {k: v for k, v in totals.items()
             if VARIA in unicodedata.normalize("NFD", k)}
    reachable, unreachable = {}, {}
    by_lemma_unreached = 0
    for lemma, n in grave.items():
        acute = to_acute(lemma)
        # Either spelling counts as the target: the capital may be positional,
        # and #19's fold handles that separately, so refusing to see the
        # lowercase acute here would understate what is reachable.
        # sorted, not a bare set: which candidate wins when both are printed
        # decided by set iteration order, so the published file changed between
        # runs (Κμὴ resolved to κμή or Κμή depending on the process).
        cands = sorted({acute, to_acute(lower_initial(lemma))} - {lemma})
        # Printed attestation is the real test; the lemma-table one is kept only
        # to show how much the old reference was hiding.
        hit = next((c for c in cands if PRINTED_FORMS.get(c, 0)), None)
        if not any(totals.get(c, 0) for c in cands):
            by_lemma_unreached += n
        (reachable if hit else unreachable)[lemma] = (n, hit)

    # Slightly above audit_lemma_table's count, which classifies each lemma once
    # and lets an earlier class claim some of these first. Same population.
    gt, rt = sum(grave.values()), sum(n for n, _ in reachable.values())
    ut = sum(n for n, _ in unreachable.values())

    # Independent authority: is the repair TARGET a dictionary headword at all?
    # This is a measurement, not a rule. Nothing here feeds validate_lemma_map.py,
    # and it must not: the union is deliberately over-inclusive, so it bounds the
    # residue from above and a cleaner list would back less, but anything built
    # into a repair on the strength of it would validate whatever noise it holds.
    heads, prov = load_headwords()
    backed = {}
    if heads:
        for lemma, n in grave.items():
            cands = sorted({to_acute(lemma), to_acute(lower_initial(lemma))} - {lemma})
            hit = next((c for c in cands if c in heads), None)
            if hit:
                backed[lemma] = (n, hit)
        # Control: comparably rare lemmas that carry no grave. Without it the
        # headline share means nothing, because rare lemmas are rare in
        # dictionaries too.
        rare_other = {k: v for k, v in totals.items()
                      if v <= 10 and VARIA not in unicodedata.normalize("NFD", k)}
        ctrl = sum(1 for k in rare_other if k in heads)
        rare_grave = {k: v for k, v in grave.items() if v <= 10}
        gctrl = sum(1 for k in rare_grave if k in heads or
                    any(c in heads for c in
                        sorted({to_acute(k), to_acute(lower_initial(k))} - {k})))
        print(f"  headword-backed {len(backed):>6,} lemmas "
              f"{sum(n for n, _ in backed.values()):>8,} tokens "
              f"({sum(n for n, _ in backed.values()) / gt:.1%} of the residue), "
              f"against {len(heads):,} headwords from {len(prov)} lexica")
        print(f"    control: {ctrl / max(len(rare_other), 1):.1%} of non-grave "
              f"lemmas at <=10 tokens are headwords, against "
              f"{gctrl / max(len(rare_grave), 1):.1%} of grave ones")
    else:
        print("  headword-backed: sibling checkout open-greek/dilemma absent, "
              "partition omitted")

    print(f"grave residue: {len(grave):,} lemmas, {gt:,} tokens "
          f"({gt / sum(totals.values()):.3%} of the lemmatized corpus)")
    print(f"  reachable   {len(reachable):>6,} lemmas {rt:>8,} tokens "
          f"{rt / gt:>6.1%}  an acute counterpart is attested to move them onto")
    print(f"  unreachable {len(unreachable):>6,} lemmas {ut:>8,} tokens "
          f"{ut / gt:>6.1%}  the corpus prints no acute counterpart under "
          f"either case")
    print(f"\n  measured the OLD way, against the lemma table rather than the "
          f"printed text,\n  the unreachable share reads {by_lemma_unreached:,} "
          f"tokens ({by_lemma_unreached / gt:.1%}). That difference is the "
          f"reference\n  being narrower than the table it governs, not a fact "
          f"about the residue.")
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
        "why_not_the_annotation_exports": "the annotation exports come from the "
            "same lemmatizer that produced this residue, so they cannot "
            "independently confirm a headword for it. Dictionary headword "
            "inventories can, and the headword_backed block below is that test.",
        "headword_backed": ({
            "what": "grave lemmas whose acute counterpart is a headword in a "
                    "published lexicon, which is an authority independent of the "
                    "lemmatizer that produced this residue",
            "NOT_A_REPAIR_RULE": "the union is deliberately over-inclusive, so it "
                                 "bounds the residue from above and a stricter "
                                 "list would back less. Nothing here feeds "
                                 "validate_lemma_map.py, and a repair built on it "
                                 "would validate whatever noise the lists carry.",
            "sources": prov,
            "excluded_sources": {
                "ag_headwords": "Wiktionary-derived, and lists 72 of these grave "
                                "lemmas as headwords themselves, which no lexicon "
                                "does",
                "mg_headwords": "Modern Greek, a different question",
            },
            "headwords": len(heads),
            "lemmas": len(backed),
            "tokens": sum(n for n, _ in backed.values()),
            "share_of_residue": round(sum(n for n, _ in backed.values()) / gt, 4),
            "control": {
                "what": "the same test on lemmas that carry no grave, at the same "
                        "rarity, because rare lemmas are rare in dictionaries too",
                "non_grave_lemmas_le_10_tokens_backed": round(
                    ctrl / max(len(rare_other), 1), 4),
                "grave_lemmas_le_10_tokens_backed": round(
                    gctrl / max(len(rare_grave), 1), 4),
            },
            "largest": [{"lemma": k, "tokens": n, "headword": h}
                        for k, (n, h) in sorted(
                            backed.items(), key=lambda kv: -kv[1][0])[:20]],
        } if heads else "sibling checkout open-greek/dilemma absent; not measured"),
        "lemmas": len(grave), "tokens": gt,
        "reachable": {"lemmas": len(reachable), "tokens": rt,
                      "caveat": "reachable is an upper bound on what a rule could "
                                "touch, not an estimate of what is worth touching: "
                                "many targets are themselves shrapnel attested at a "
                                "handful of tokens (λλά at 10, μονονοχί at 2), and "
                                "merging onto those empties the audit class without "
                                "producing a headword"},
        "unreachable": {"lemmas": len(unreachable), "tokens": ut,
                        "note": "the corpus prints no acute counterpart under "
                                "either case, so a rule that moves a grave lemma "
                                "onto its acute has nothing to move these onto. "
                                "They are OCR shrapnel and non-headword inflected "
                                "forms, an OCR-quality problem rather than a "
                                "lemmatization one"},
        "superseded": {"was": "an earlier version of this file reported the "
                              "unreachable share as 77.4% and said no rule of "
                              "this shape could reach it regardless of threshold",
                       "wrong_because": "it tested whether the acute exists as a "
                                        "LEMMA in the per-work table. The accent "
                                        "argument is about the printed text, and "
                                        "the rule's own reference table was "
                                        "narrower than the table it governs "
                                        "(83,078 lemmas against 275,871)",
                       "measured_the_old_way_tokens": by_lemma_unreached},
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
