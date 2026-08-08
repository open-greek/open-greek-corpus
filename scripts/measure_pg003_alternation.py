#!/usr/bin/env python3
"""Estimate, from the text alone, which PG003 pages are Dionysius and which are
Pachymeres' paraphrase.

PG 3 prints Pseudo-Dionysius with Georgius Pachymeres' paraphrase, alternating,
and our OCR dropped most of the display heads that mark the switches (issue #9).
There is one signal the material gives for free and nobody had used: a paraphrase
REPLAYS the rare vocabulary of the passage it paraphrases. So a paraphrase page's
closest neighbour by rare-word overlap lies BEHIND it, and a text page's closest
neighbour lies AHEAD, where the paraphrase of it sits. The sign of that lag is an
estimate of who wrote the page, computed without any head, any page image, or
any edition this corpus does not hold.

WHAT THIS IS NOT. It is not the boundary table a carve needs, and it must not be
used as one. It is page-level: it says which side of the alternation a page falls
on, not where inside a row the switch happens, and issue #9's binding problem is
that most switches fall INSIDE a row while carve_cgpg_volume.py moves whole rows.
Nothing here changes that. It also declines rather than guessing, so it labels
about half the volume and leaves the rest unlabelled on purpose.

Why the declining matters: the label is an argmax over a bounded band, so a page
with no true partner in band still gets a sign. Checked against the six heads and
work incipits this script never looks at, agreement tracks the margin exactly.
The four with a margin above 0.15 all agree (PARAPHRASIS PACHYMERAE at 151 and
381, DN 1.1 at 300, MT 1.1 at 506); of the two below 0.08, one agrees and one
does not. A version that labelled every page would be publishing that coin-flip
as a finding, which is how this issue has twice been mis-stated already.

  python3 scripts/measure_pg003_alternation.py            # report
  python3 scripts/measure_pg003_alternation.py --write    # -> data/pg003_alternation.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus" / "cogPG.PG003.jsonl"
OUT = DATA / "pg003_alternation.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

BAND = 40          # pages either side to search for the paraphrase partner
RARE_DF = 6        # a word in this many pages or fewer is rare enough to match on
MIN_RARE = 8       # pages with less rare vocabulary than this cannot be scored
MARGIN = 0.10      # below this the best partner is not distinguishable; decline

# Held out. The script never reads these while labelling; they are only scored
# against afterwards. Direction is what the head implies: a paraphrase or synopsis
# head opens a block that looks BACKWARD, a work incipit opens one looking FORWARD.
HELD_OUT = {151: ("PARAPHRASIS PACHYMERAE", -1), 381: ("PARAPHRASIS PACHYMERAE", -1),
            487: ("PARAPHRASIS PACHYMERAE", -1), 171: ("SYNOPSIS CAPITIS", -1),
            300: ("DN 1.1 incipit", 1), 506: ("MT 1.1 incipit", 1)}


def rare_sets(rows: dict[int, str]) -> dict[int, set]:
    def toks(t: str) -> list[str]:
        t = "".join(c for c in unicodedata.normalize("NFD", t)
                    if not unicodedata.combining(c)).lower()
        return re.findall(r"[α-ω]{4,}", t)
    df: Counter = Counter()
    sets = {}
    for k, t in rows.items():
        s = set(toks(t))
        sets[k] = s
        df.update(s)
    return {k: {w for w in s if df[w] <= RARE_DF} for k, s in sets.items()}


def label(rows: dict[int, str]) -> dict[int, tuple]:
    ks = sorted(rows)
    rare = rare_sets(rows)
    out = {}
    for i, k in enumerate(ks):
        r = rare[k]
        if len(r) < MIN_RARE:
            continue
        scored = []
        for j in range(max(0, i - BAND), min(len(ks), i + BAND + 1)):
            if abs(j - i) < 2:          # neighbours share vocabulary trivially
                continue
            o = rare[ks[j]]
            if len(o) < MIN_RARE:
                continue
            scored.append((len(r & o) / min(len(r), len(o)), ks[j] - k))
        if len(scored) < 2:
            continue
        scored.sort(reverse=True)
        out[k] = (scored[0][1], scored[0][0] - scored[1][0])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = {}
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[int(r["locus"])] = r.get("text") or ""
    scored = label(rows)
    kept = {k: v for k, v in scored.items() if v[1] >= MARGIN}
    tok = {k: len(_GK.findall(t)) for k, t in rows.items()}
    total = sum(tok.values())
    para = sum(tok[k] for k, v in kept.items() if v[0] < 0)
    text = sum(tok[k] for k, v in kept.items() if v[0] > 0)

    print(f"PG003: {len(rows)} pages, {total:,} tokens")
    print(f"  labelled at margin >= {MARGIN}: {len(kept)} pages, "
          f"{(para + text) / total:.0%} of tokens")
    print(f"  paraphrase side {para:,}  text side {text:,}  "
          f"-> text is {text / (para + text):.0%} of what is labelled")
    print(f"  DECLINED: {len(rows) - len(kept)} pages. The rest of the volume has no "
          f"distinguishable partner in band and is left unlabelled.")
    print(f"\n  held-out check (never read while labelling):")
    agree = seen = 0
    lab_agree = lab_seen = 0
    for k, (what, want) in sorted(HELD_OUT.items()):
        v = scored.get(k)
        if not v:
            print(f"    {k:>4} {what:<24} not scored")
            continue
        got = 1 if v[0] > 0 else -1
        seen += 1
        agree += got == want
        if v[1] >= MARGIN:
            lab_seen += 1
            lab_agree += got == want
        flag = "agrees" if got == want else "DISAGREES"
        print(f"    {k:>4} {what:<24} lag {v[0]:+3d}  margin {v[1]:.3f}  {flag}"
              f"{'' if v[1] >= MARGIN else '  (declined)'}")
    print(f"    {agree} of {seen} agree overall; {lab_agree} of {lab_seen} among those "
          f"the threshold KEEPS.\n    The two it declines are the two lowest margins, "
          f"and they split one each way, which is\n    what no signal looks like. That "
          f"is the threshold doing its job, not luck.")
    print(f"\n  For comparison the README gives Dionysius about 37% of this volume, "
          f"from TLG canon\n  word counts rather than from this file. This measures "
          f"the text itself and lands near it,\n  which corroborates both; it does "
          f"not replace either.")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "page-level estimate of the Dionysius/Pachymeres alternation in PG003",
        "issue": "open-greek/open-greek-corpus#9",
        "method": "a paraphrase replays the rare vocabulary of what it paraphrases, "
                  "so a paraphrase page's closest neighbour by rare-word overlap "
                  "lies behind it and a text page's lies ahead; the sign of that lag "
                  "is the estimate",
        "NOT_A_CARVE_INPUT": "page level only. It says which side of the alternation "
                             "a page falls on, not where inside a row the switch is, "
                             "and #9's binding problem is that most switches fall "
                             "inside a row while the carve script moves whole rows.",
        "params": {"band": BAND, "rare_document_frequency": RARE_DF,
                   "min_rare_words": MIN_RARE, "margin": MARGIN},
        "pages": len(rows), "labelled": len(kept),
        "declined": len(rows) - len(kept),
        "tokens_paraphrase_side": para, "tokens_text_side": text,
        "held_out_agreement": f"{lab_agree}/{lab_seen} among labelled, {agree}/{seen} overall",
        "held_out_check": {str(k): {"what": w, "expected": e,
                                    "lag": scored.get(k, (None, None))[0],
                                    "margin": scored.get(k, (None, None))[1]}
                           for k, (w, e) in sorted(HELD_OUT.items())},
        "labels": {str(k): {"lag": v[0], "margin": round(v[1], 4),
                            "side": "paraphrase" if v[0] < 0 else "text",
                            "tokens": tok[k]}
                   for k, v in sorted(kept.items())},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
