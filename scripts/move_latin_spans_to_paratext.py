#!/usr/bin/env python3
"""Take the Latin that is spelled in Greek letters out of the Greek counts.

Three works here survive only partly in Greek: Polycarp's Philippians is Latin
alone in chapters 10-12 and 14, Hermas loses its Greek partway through the
Similitudes, and Polybius' apparatus sigla are Latin. The editions print that
Latin, and somewhere upstream it was transliterated into Greek script, so it
tokenizes as Greek and counts as Greek. Issue #34, and cisco's call on
2026-08-10: keep it, take it out of the counts.

Kept means data/paratext, which is where this corpus puts text it will not
serve. Out of the counts follows from that, because every rollup globs
data/corpus.

WHY SPANS AND NOT ROWS. 16 of the 57 rows hold both languages: Polycarp 13.2 is
Greek with a Latin tail, Hermas 26.30.4 the reverse. Moving those rows whole
would take 837 tokens of real Greek out of the corpus to remove 256 tokens of
Latin. So the Latin is excised from inside the row and the Greek stays where it
is, which is the whole reason the measurement was rebuilt span-shaped first.

The span rule is measure_latin_in_greek_script's, imported rather than copied: a
run of SPAN_MIN or more unaccented tokens carrying at least one Latin function
word, looked for only inside a work the work gate admits. Nothing outside those
three works is touched.

  python3 scripts/move_latin_spans_to_paratext.py [--apply|--unapply]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "paratext" / "latin_in_greek_script.jsonl"
AUDIT = DATA / "corpus_changes" / "latin-spans-to-paratext.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_latin_in_greek_script as M  # noqa: E402
from build_public_corpus import _GK  # noqa: E402
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")


def char_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) character ranges of the Latin runs in one row.

    Same rule as the measurement, on character offsets so the run can be cut
    out. The range covers the tokens only; the whitespace between what is left
    is normalized by the caller.
    """
    toks = [(m.group(), m.start(), m.end()) for m in _GK.finditer(text)]
    out, run = [], []
    for t in toks + [None]:
        if t is not None and M._unaccented(t[0]):
            run.append(t)
            continue
        if len(run) >= M.SPAN_MIN and any(w.lower() in M.MARKERS for w, _s, _e in run):
            out.append((run[0][1], run[-1][2]))
        run = []
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true"); g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()

    if a.unapply:
        if not AUDIT.exists(): fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for blk in rec["files"]:
            p = REPO / blk["file"]
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{p.name} has moved since this audit; reverse that first")
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in blk["rows_before"]), encoding="utf-8")
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {p.name} byte-for-byte")
        OUT.unlink()
        AUDIT.unlink(); print(f"UNAPPLIED: {len(rec['files'])} file(s) restored"); return

    works = M.admitted_works()
    blocks, moved, latin_tok, greek_kept = [], [], 0, 0
    for work in sorted(works):
        fp = DATA / "corpus" / f"{work}.jsonl"
        raw = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
        before = [dict(r) for r in rows]
        touched = 0
        keep_rows = []
        for r in rows:
            text = r.get("text") or ""
            sp = char_spans(text)
            if not sp:
                keep_rows.append(r)
                continue
            touched += 1
            lat = " ".join(text[s:e] for s, e in sp)
            latin_tok += len(_GK.findall(lat))
            rest, prev = [], 0
            for s, e in sp:
                rest.append(text[prev:s])
                prev = e
            rest.append(text[prev:])
            left = " ".join(" ".join(rest).split())
            moved.append({"slug": work, "page": str(r["locus"]), "lang": "la",
                          "class": "latin_in_greek_script",
                          "script": "grc (Latin transliterated into Greek letters "
                                    "upstream, which is why it tokenized as Greek)",
                          "license": r.get("license", ""),
                          "source": r.get("source", ""),
                          "edition": r.get("edition", ""),
                          "greek_remaining_in_this_row": len(_GK.findall(left)),
                          "text": lat})
            if left:
                nr = dict(r); nr["text"] = left
                nr["row_part"] = ("the Greek of this row; its Latin spans are in "
                                  "data/paratext/latin_in_greek_script.jsonl")
                greek_kept += len(_GK.findall(left))
                keep_rows.append(nr)
        blocks.append({"file": fp.relative_to(REPO).as_posix(), "work": work,
                       "rows_touched": touched, "rows_before": before,
                       "sha256_before": sha(raw), "keep": keep_rows})
    print(f"{len(blocks)} works, {sum(b['rows_touched'] for b in blocks)} rows touched")
    print(f"  Latin moving: {latin_tok:,} tokens")
    print(f"  Greek kept in rows that held both: {greek_kept:,} tokens")
    if not a.apply: print("\nCHECK only (pass --apply to write)"); return
    if AUDIT.exists(): fail("audit exists; --unapply first")
    if OUT.exists(): fail(f"{OUT.name} exists; --unapply first")

    for b in blocks:
        p = REPO / b["file"]
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                             for r in b.pop("keep")), encoding="utf-8")
        b["sha256_after"] = sha(p.read_text(encoding="utf-8"))
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in moved),
                   encoding="utf-8")
    AUDIT.write_text(json.dumps({
        "what": "Latin spelled in Greek letters moved from data/corpus to "
                "data/paratext/latin_in_greek_script.jsonl",
        "date": "2026-08-10", "issue": "open-greek/open-greek-corpus#34",
        "decision": "cisco, 2026-08-10: keep it, exclude it from the Greek counts",
        "why_spans": "16 of the 57 rows hold both languages. Moving them whole "
                     "would have taken real Greek out of the corpus to remove the "
                     "Latin beside it, so the Latin is excised from inside the row.",
        "rule": f"a run of {M.SPAN_MIN}+ unaccented tokens carrying a Latin "
                f"function word, inside a work the work gate admits "
                f"({M.MIN_WORK_MARKERS} distinct markers over "
                f"{M.MIN_WORK_ROWS} low-accent rows)",
        "works": sorted(works), "latin_tokens": latin_tok,
        "greek_kept_in_mixed_rows": greek_kept,
        "rows_touched": sum(b["rows_touched"] for b in blocks),
        "files": blocks,
        "reverse": "python3 scripts/move_latin_spans_to_paratext.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {latin_tok:,} Latin tokens -> {OUT.relative_to(REPO)}")


if __name__ == "__main__": main()
