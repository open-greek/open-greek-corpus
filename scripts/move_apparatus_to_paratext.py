#!/usr/bin/env python3
"""Move Migne's own editorial apparatus out of the served corpus.

What is left under the ten cogPG volume urns is not works. It is what the
edition prints around them: the 1532 Verona editor's preface to Oecumenius,
Migne's prefatory dissertation and testimonia for the Excerpta historians, a
florilegium about Ignatius assembled from a dozen named authors, Nicephorus
Callistus' table of contents, Leo Allatius' Latin dissertation, and several
blocks that are Latin read as Greek letter shapes. Every one is identified in
its volume's residual note in data/cgpg_carve_plan.json, and each has stayed
because it is apparatus rather than a work with an author.

Served under a volume urn it could not be cited, and it counted into the Greek
totals. data/paratext/ is the mechanism this repo already has for exactly that:
text kept so nothing printed in a public-domain volume is silently dropped,
excluded from every Greek coverage, lemma and frequency rollup. The exclusion
needs no code, because every rollup globs data/corpus and this leaves it.

Cisco's call, 2026-08-10, asked for on the tracker.

NOT a judgement that the text is worthless. It is reversible from the audit, it
keeps its volume urn and locus so any correction record keyed to them still
places, and the reason each block stayed is carried onto every row.

  python3 scripts/move_apparatus_to_paratext.py [--apply|--unapply]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "paratext" / "edition_apparatus.jsonl"
AUDIT = DATA / "corpus_changes" / "apparatus-to-paratext.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

REASONS = {
 "PG003": "20 tokens of Maximus quoted inside a Latin note, belonging to neither "
          "of the volume's two authors",
 "PG005": "the florilegium about Ignatius that the edition assembles from a dozen "
          "named authors; three of its rows are also partial duplicates of served "
          "Eusebius and Theodoret, held back from the 2026-08-09 shed at 0.607, "
          "0.673 and 0.614",
 "PG101": "scraps of the edition's apparatus, including one row that is Latin read "
          "as Greek letter shapes",
 "PG107": "the oracles testimonia the edition prints around Nicetas, plus a Latin "
          "running head read as Greek",
 "PG109": "two display lines, one of them the Latin NOTITIA",
 "PG113": "Migne's prefatory dissertation and testimonia for the seven Excerpta "
          "historians, and at 489 the list of fourteen chronicle sources the "
          "compilation excerpts",
 "PG118": "the 1532 Verona editor's preface, which names Giberti of Verona as the "
          "man who supplied the manuscript and speaks of Oecumenius in the third "
          "person, so early-modern paratext; plus one display line",
 "PG124": "garbled Latin monita",
 "PG125": "Leo Allatius' Latin dissertation, read as Greek letter shapes, with "
          "Greek quotations inside it",
 "PG139": "Nicephorus Callistus' own table of contents",
}
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true"); g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()

    if a.unapply:
        if not AUDIT.exists(): fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        if OUT.exists() and sha(OUT.read_text(encoding="utf-8")) != rec["paratext"]["sha256_after"]:
            fail("the paratext file has moved since this audit")
        for blk in rec["files"]:
            p = REPO / blk["file"]
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in blk["rows"]), encoding="utf-8")
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {p.name} byte-for-byte")
        keep = [l for l in OUT.read_text(encoding="utf-8").splitlines()
                if l.strip() and json.loads(l).get("class") != "edition_apparatus"]
        OUT.write_text("".join(l + "\n" for l in keep), encoding="utf-8") if keep else OUT.unlink()
        AUDIT.unlink(); print(f"UNAPPLIED: {len(rec['files'])} volume file(s) restored"); return

    files = sorted((DATA / "corpus").glob("cogPG.*.jsonl"))
    if not files: fail("no cogPG.* files in data/corpus (already applied?)")
    blocks, moved, tok = [], [], 0
    for fp in files:
        vol = fp.name[len("cogPG."):-len(".jsonl")]
        if vol not in REASONS: fail(f"no recorded reason for {vol}; refusing")
        raw = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
        for r in rows:
            tok += len(_GK.findall(r.get("text") or ""))
            moved.append({"slug": f"cogPG.{vol}", "page": str(r["locus"]),
                          "lang": "grc", "class": "edition_apparatus",
                          "license": r.get("license", ""), "source": r.get("source", ""),
                          "edition": r.get("edition", ""),
                          "why_not_served": REASONS[vol],
                          "text": r.get("text") or ""})
        blocks.append({"file": fp.relative_to(REPO).as_posix(), "volume": vol,
                       "rows": rows, "sha256_before": sha(raw)})
    print(f"{len(files)} volume file(s), {len(moved)} rows, {tok:,} Greek tokens")
    for b in blocks:
        print(f"   {b['volume']:>6} {len(b['rows']):>3} rows  {REASONS[b['volume']][:58]}")
    if not a.apply: print("\nCHECK only (pass --apply to write)"); return
    if AUDIT.exists(): fail("audit exists; --unapply first")

    existing = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    OUT.write_text(existing + "".join(json.dumps(r, ensure_ascii=False) + "\n"
                                      for r in moved), encoding="utf-8")
    for b in blocks: (REPO / b["file"]).unlink()
    AUDIT.write_text(json.dumps({
        "what": "Migne's editorial apparatus moved from data/corpus to "
                "data/paratext/edition_apparatus.jsonl",
        "date": "2026-08-10", "issue": "open-greek/open-greek-corpus#8",
        "why": "what remained under the ten cogPG volume urns was the edition's "
               "own apparatus rather than works: served there it could not be "
               "cited and it counted into the Greek totals. data/paratext/ is "
               "this repo's existing mechanism for text kept but not served, and "
               "the exclusion needs no code because every rollup globs "
               "data/corpus.",
        "decision": "cisco, 2026-08-10, on the tracker",
        "reversible": "each row keeps its volume urn and locus, so a correction "
                      "record keyed to them still places",
        "rows": len(moved), "greek_tokens": tok,
        "volumes": {b["volume"]: len(b["rows"]) for b in blocks},
        "reasons": REASONS,
        "files": blocks,
        "paratext": {"file": str(OUT.relative_to(REPO)),
                     "sha256_before": sha(existing) if existing else None,
                     "sha256_after": sha(OUT.read_text(encoding="utf-8"))},
        "reverse": "python3 scripts/move_apparatus_to_paratext.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {tok:,} tokens -> {OUT.relative_to(REPO)}")


if __name__ == "__main__": main()
