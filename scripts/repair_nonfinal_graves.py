#!/usr/bin/env python3
"""Repair served tokens that put a grave where Greek never puts one.

A grave sits only on a word's final syllable. Every token in issue #31's class
breaks that: not a variant, not doubtful, just not Greek. What was missing was a
rule saying which word each one is, and the skeleton class supplies it (see
measure_nonfinal_graves.py): group the corpus's own non-OCR text by letter
skeleton with the combining marks stripped, read a grave on the last nucleus as
an acute because that alternation is positional, drop every flagged form from
the base so an illegal form cannot vote, and take the reading holding almost all
of its class.

WHAT THIS WILL NOT DO. By default only accent marks move: breathings, iota
subscript and diaeresis are asserted byte-identical between form and target,
because moving one of those is a lexical claim (ὰπὸ to ἀπό, τὰναντία to
τἀναντία). --allow-mark-moves lifts that for a tranche built to carry the
claim, and the assertion becomes the weaker one that the two words have the
SAME LETTERS and differ only in their marks, which is the skeleton class the
targets were chosen from to begin with. It is opt-in per run because it changes
what a repair is allowed to assert; cisco decided it tranche by tranche, the
mark-moving one on 2026-08-11. Only the sources a tranche names are edited. And
a target must be DOMINANT over a real class, not merely attested: an
attested-target gate passes on ἐγώγε and τάναντία, which is how #1's forty thousand
wrong corrections happened.

Token counts do not change. An accent lives inside its token, so a swap
conserves under _GK and a delta means something else moved.

The audit stores only the rows that changed and the index each sits at. Storing
whole files made two audits 606 MB and 251 MB, which GitHub refuses, and was
redundant anyway: an accent swap reverses from the pair of texts alone.

  python3 scripts/repair_nonfinal_graves.py --tranche data/nonfinal_grave_tranche.json
  python3 scripts/repair_nonfinal_graves.py --tranche ... --apply
  python3 scripts/repair_nonfinal_graves.py --tranche ... --allow-mark-moves --apply
  python3 scripts/repair_nonfinal_graves.py --tranche ... --unapply
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from measure_nonfinal_graves import (  # noqa: E402
    has_nonfinal_grave, skeleton, without_accents)
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tranche", required=True)
    ap.add_argument("--sources", default="ocr")
    ap.add_argument("--allow-mark-moves", action="store_true",
                    help="permit a target that moves a breathing or coronis as "
                         "well as an accent, as long as the letters do not change")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--decision", default="")
    ap.add_argument("--audit-tag", default="",
                    help="suffix for the audit filename. A tranche sheet is "
                         "regenerated and drains to zero once applied, but its "
                         "audit is permanent; a second apply from the same "
                         "sheet path needs its own audit rather than a fight "
                         "over the first one's name")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true"); g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()
    tranche = json.loads((REPO / a.tranche).read_text(encoding="utf-8"))
    stem = Path(a.tranche).stem + (f".{a.audit_tag}" if a.audit_tag else "")
    AUDIT = DATA / "corpus_changes" / f"{stem}.applied.json"
    sources = set(a.sources.split(","))

    if a.unapply:
        if not AUDIT.exists(): fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for blk in rec["files"]:
            p = REPO / blk["file"]
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{p.name} has moved since this audit; reverse that first")
            rows = [json.loads(l) for l in
                    p.read_text(encoding="utf-8").splitlines() if l.strip()]
            for e in blk["edits"]:
                t = rows[e["index"]]["text"]
                for off, orig in e["was"]:
                    # FORWARD, not reversed. The offsets are into the ORIGINAL
                    # text, so they are only correct once everything earlier in
                    # the row is back to its original length. Reversed works
                    # while every repair is the same length as what it replaced,
                    # which every accent-only tranche was, and silently corrupts
                    # the row the first time one is not: 7 of the mark-moving
                    # forms are a vowel wearing two accents that composes to one
                    # character shorter.
                    m = _GK.match(t, off)
                    if not m:
                        fail(f"{p.name}: no token at offset {off}")
                    t = t[:off] + orig + t[m.end():]
                rows[e["index"]]["text"] = t
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in rows), encoding="utf-8")
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {p.name} byte-for-byte")
        AUDIT.unlink(); print(f"UNAPPLIED: {len(rec['files'])} file(s) restored"); return

    repl = {}
    for r in tranche["rows"]:
        f, t = r["form"], r["target"]
        if a.allow_mark_moves:
            # The letters have to be the same word. That is the entire content of
            # the claim: κἂι and καί are one skeleton wearing different marks.
            # Anything failing this is a different word, not a repair.
            if skeleton(f) != skeleton(t):
                fail(f"{f!r} -> {t!r} changes letters, not just marks")
        elif not r.get("accent_only") or without_accents(f) != without_accents(t):
            fail(f"{f!r} -> {t!r} moves more than an accent; a tranche built "
                 "to assert that needs --allow-mark-moves")
        if not has_nonfinal_grave(f): fail(f"{f!r} carries no non-final grave")
        if has_nonfinal_grave(t): fail(f"target {t!r} is itself illegal")
        repl[f] = t

    blocks, changed, rows_touched = [], 0, 0
    for fp in sorted((DATA / "corpus").glob("*.jsonl")):
        raw = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
        edits, hit = [], 0
        for i, r in enumerate(rows):
            if r.get("source") not in sources:
                continue
            text = r.get("text") or ""
            # Offsets and the original form, not the whole row. A swap reverses
            # from those, and storing texts made this audit 37 MB.
            spots, out, prev = [], [], 0
            for m in _GK.finditer(text):
                w = m.group()
                if w not in repl:
                    continue
                spots.append([m.start(), w])
                out.append(text[prev:m.start()] + repl[w])
                prev = m.end()
            if not spots:
                continue
            new = "".join(out) + text[prev:]
            n = len(spots)
            if len(_GK.findall(new)) != len(_GK.findall(text)):
                fail(f"{fp.name} {r['locus']}: token count changed")
            edits.append({"index": i, "was": spots})
            r["text"] = new
            hit += 1
            changed += n
        if hit:
            rows_touched += hit
            blocks.append({"file": fp.relative_to(REPO).as_posix(),
                           "sha256_before": sha(raw), "edits": edits,
                           "rows": rows, "rows_touched": hit})
    print(f"{len(repl):,} forms, sources {sorted(sources)}")
    print(f"  {changed:,} tokens in {rows_touched:,} rows across {len(blocks)} works")
    if not a.apply: print("\nCHECK only (pass --apply to write)"); return
    if AUDIT.exists(): fail("audit exists; --unapply first")
    for b in blocks:
        p = REPO / b["file"]
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                             for r in b.pop("rows")), encoding="utf-8")
        b["sha256_after"] = sha(p.read_text(encoding="utf-8"))
    AUDIT.write_text(json.dumps({
        "what": f"non-final grave repairs from {a.tranche}",
        "date": a.date, "issue": "open-greek/open-greek-corpus#31",
        "decision": a.decision or f"cisco, {a.date}",
        "rule": tranche.get("rule"), "sources_edited": sorted(sources),
        "token_weighted_share": tranche.get("token_weighted_share"),
        "expected_wrong_tokens": tranche.get("expected_wrong_tokens"),
        "marks_moved": ("a breathing or coronis moved as well as an accent; every "
                        "form and its target were asserted here to have identical "
                        "letters, so nothing but the marks changed")
                       if a.allow_mark_moves else
                       ("breathings, iota subscript and diaeresis are byte-identical "
                        "between every form and its target; only accents moved"),
        "tokens_changed": changed, "rows_touched": rows_touched, "forms": len(repl),
        "substitutions": dict(sorted(repl.items())),
        "files": blocks,
        "reverse": (f"python3 scripts/repair_nonfinal_graves.py --tranche {a.tranche}"
                    + (f" --audit-tag {a.audit_tag}" if a.audit_tag else "")
                    + " --unapply"),
        "forward": ("python3 scripts/repair_nonfinal_graves.py --tranche "
                    f"{a.tranche} --sources {a.sources}"
                    + (" --allow-mark-moves" if a.allow_mark_moves else "")
                    + (f" --audit-tag {a.audit_tag}" if a.audit_tag else "")
                    + f" --date {a.date} --apply"),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {changed:,} tokens, audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__": main()
