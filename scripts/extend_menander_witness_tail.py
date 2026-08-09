#!/usr/bin/env python3
"""Give the Migne witness of Menander Protector back its last sentence.

Pass 5 carved PG113's Excerpta de legationibus and sent six historians to
data/corpus_secondary as witnesses, Menander among them. That witness ends at
locus PG113.474 on "ἦ γὰρ ἂν", and the volume residual's locus 475 opens
"ἄλλως μὴ ἀνέξεσθαι ἰδεῖν ἐς σπονδάς". One sentence, its halves in two files.

475 was left behind on a recorded containment of 0.764, which the plan attributes
to Theophylact Simocatta's block. That number was measured against the wrong
file: it is 0.750 against the Menander WITNESS, and against the text this corpus
actually serves, data/corpus/menander-protector...jsonl, it is 0.944. Against
Theophylact it is 0.236. So the row is neither Theophylact's nor new text; it is
the tail of the Menander block, and serving it in the volume file served 74
tokens that the corpus already holds under Menander's own slug.

It joins the witness rather than being shed into a volume-keyed secondary file,
because that is where its block is and because the sentence should be whole.
Either way it leaves the served counts.

  python3 scripts/extend_menander_witness_tail.py [--apply|--unapply]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
VOL = REPO / "data" / "corpus" / "cogPG.PG113.jsonl"
WIT = (REPO / "data" / "corpus_secondary"
       / "menander-protector.de-legationibus-romanorum-ad-gentes-fragmenta-ap-constantinum.jsonl")
AUDIT = REPO / "data" / "corpus_changes" / "menander-witness-tail-extend.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
LOCUS, OPENS, PREV_ENDS = "475", "ἄλλως μὴ ἀνέξεσθαι", "ἦ γὰρ ἂν"
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")
def rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
def dump(p, rs): p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true"); g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()
    vb, wb = VOL.read_text(encoding="utf-8"), WIT.read_text(encoding="utf-8")
    v, w = rows(VOL), rows(WIT)
    if a.unapply:
        if not AUDIT.exists(): fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for p, raw, key in ((VOL, vb, "volume"), (WIT, wb, "witness")):
            if sha(raw) != rec[key]["sha256_after"]:
                fail(f"{p.name} is not in the state this audit recorded")
        w = [r for r in w if str(r["locus"]) != rec["moved_row"]["locus"]]
        v.append(rec["moved_row"]["as_residual"])
        v.sort(key=lambda r: int(str(r["locus"]).split(".")[-1]))
        dump(WIT, w); dump(VOL, v)
        for p, key in ((VOL, "volume"), (WIT, "witness")):
            if sha(p.read_text(encoding="utf-8")) != rec[key]["sha256_before"]:
                fail(f"unapply did not restore {p.name} byte-for-byte")
        AUDIT.unlink(); print("UNAPPLIED: both files restored byte-for-byte"); return
    src = next((r for r in v if str(r["locus"]).split(".")[-1] == LOCUS), None)
    if src is None: fail(f"locus {LOCUS} not in {VOL.name} (already applied?)")
    if not src["text"].startswith(OPENS): fail(f"locus {LOCUS} should open {OPENS!r}")
    if not w[-1]["text"].rstrip().endswith(PREV_ENDS):
        fail(f"the witness should end {PREV_ENDS!r}, it ends {w[-1]['text'].rstrip()[-30:]!r}")
    n = len(_GK.findall(src["text"]))
    print(f"witness ends {w[-1]['locus']} ...{PREV_ENDS!r}")
    print(f"moving locus {LOCUS}, {n} tokens: {src['text'][:60]!r}...")
    if not a.apply: print("\nCHECK only (pass --apply to write)"); return
    if AUDIT.exists(): fail("audit exists; --unapply first")
    new = {k: w[-1][k] for k in w[-1] if k not in ("text", "locus")}
    new["locus"] = f"PG113.{LOCUS}"; new["text"] = src["text"]
    w.append(new); v = [r for r in v if r is not src]
    dump(WIT, w); dump(VOL, v)
    AUDIT.write_text(json.dumps({
        "what": f"Migne PG113 locus {LOCUS} moved from the volume residual into the "
                "Menander Protector witness, whose block it ends",
        "date": "2026-08-09", "issue": "open-greek/open-greek-corpus#8",
        "why": "the witness ends on ἦ γὰρ ἂν and this row opens ἄλλως μὴ ἀνέξεσθαι, "
               "one sentence in two files. Word-bigram containment is 0.944 against "
               "the SERVED menander-protector primary, so the volume file was "
               "serving 74 tokens the corpus already holds under Menander's slug.",
        "corrects": "the plan recorded 0.764 for this row and attributed it to "
                    "Theophylact Simocatta's block. That was measured against the "
                    "Menander witness (0.750 here), not the served primary. Against "
                    "Theophylact the row scores 0.236.",
        "greek_tokens_moved": n,
        "moved_row": {"locus": new["locus"], "as_residual": src},
        "volume": {"file": str(VOL.relative_to(REPO)), "sha256_before": sha(vb),
                   "sha256_after": sha(VOL.read_text(encoding="utf-8"))},
        "witness": {"file": str(WIT.relative_to(REPO)), "sha256_before": sha(wb),
                    "sha256_after": sha(WIT.read_text(encoding="utf-8"))},
        "reverse": "python3 scripts/extend_menander_witness_tail.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED: {n} tokens -> {WIT.name}")
if __name__ == "__main__": main()
