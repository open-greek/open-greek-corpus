#!/usr/bin/env python3
"""Separate πνεύ from ἄλλους in PG118 locus 18, welded across a column break.

Locus 18 interleaves two things, the way PG151.389 does. Characters 0-228 and
1860-end are the 1532 Verona editor's preface; between them sits the ὑπόθεσις
τῆς βίβλου τῶν Πράξεων, which has its own printed head on the page. To carve the
hypothesis out, the cut at 1860 has to be at a whitespace boundary, and it was
not: our OCR ran the preface's resumption into the hypothesis' last word, giving
...πολλὰ πνεύἄλλους τοιούτους...

The reading is πνεύματα and our OCR dropped -ματα at the column break; the next
row opens ματα ἐξέβαλε, which is where it went. This inserts one space and does
NOT restore the lost syllables, on the standard 8c56a56 set: separating two
units that are visibly two is a smaller claim than supplying text our scan does
not attest. πνεύ stays a fragment and is recorded as one.

  python3 scripts/unsplice_pg118_column_break.py [--apply|--unapply]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "corpus" / "cogPG.PG118.jsonl"
AUDIT = REPO / "data" / "corpus_changes" / "cogPG.PG118.head-splice.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
LOCUS, GLUED, LEFT, RIGHT = "18", "πνεύἄλλους", "πνεύ", "ἄλλους"
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()
    raw = SRC.read_text(encoding="utf-8")
    rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
    row = next((r for r in rows if str(r["locus"]).split(".")[-1] == LOCUS), None)
    if row is None: fail(f"locus {LOCUS} is not in {SRC.name}")
    def dump():
        SRC.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                       encoding="utf-8")
    if a.unapply:
        if not AUDIT.exists(): fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        if sha(raw) != rec["sha256_after"]:
            fail("file is not in the state this audit recorded; reverse what was "
                 "applied after it first")
        row["text"] = rec["text_before"]; dump()
        if sha(SRC.read_text(encoding="utf-8")) != rec["sha256_before"]:
            fail("unapply did not restore byte-for-byte")
        AUDIT.unlink(); print("UNAPPLIED: restored byte-for-byte"); return
    t = row["text"]
    if GLUED not in t: fail(f"{GLUED!r} not in locus {LOCUS} (already applied?)")
    new = t.replace(GLUED, f"{LEFT} {RIGHT}", 1)
    b, af = len(_GK.findall(t)), len(_GK.findall(new))
    print(f"locus {LOCUS}: {GLUED!r} -> {LEFT} {RIGHT!r}; tokens {b} -> {af}")
    if not a.apply: print("\nCHECK only (pass --apply to write)"); return
    if AUDIT.exists(): fail("audit exists; --unapply first")
    row["text"] = new; dump()
    AUDIT.write_text(json.dumps({
        "what": f"one space inserted between {LEFT} and {RIGHT} in Migne PG118 "
                f"locus {LOCUS}, welded across a column break",
        "date": "2026-08-09", "issue": "open-greek/open-greek-corpus#8",
        "why": "locus 18 interleaves the 1532 Verona editor's preface with the "
               "ὑπόθεσις τῆς βίβλου τῶν Πράξεων between characters 228 and 1860. "
               "The cut at 1860 could not be made because the OCR ran the "
               "preface's resumption into the hypothesis' last word.",
        "not_done": "the reading is πνεύματα and our OCR dropped -ματα at the "
                    "column break; the next row opens ματα ἐξέβαλε. This does not "
                    "supply it from anywhere. πνεύ stays a fragment.",
        "token_delta_is_intended": f"+{af - b}, one welded token becoming two",
        "greek_tokens_before": b, "greek_tokens_after": af,
        "text_before": t, "text_after": new,
        "files": [str(SRC.relative_to(REPO))],
        "sha256_before": sha(raw), "sha256_after": sha(SRC.read_text(encoding="utf-8")),
        "reverse": "python3 scripts/unsplice_pg118_column_break.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED: audit {AUDIT.relative_to(REPO)}")
if __name__ == "__main__": main()
