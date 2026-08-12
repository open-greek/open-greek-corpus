#!/usr/bin/env python3
"""Resolve the cross-file duplicate pages by cisco's 2026-08-12 rulings.

A carve splits a scan item across the works printed in it, so a page the
scanner delivered twice could land once in each of two works, invisible to
every within-file sweep (issue #33, the 04a323b comment). The evidence table
(data/crossfile_page_evidence.json) scores each served pair by the
neighbor-anchor rule: the page belongs to the work whose file holds its
neighboring scan pages. cisco approved acting on the high and medium tiers
and resolved the three ties by content; both rulings live in
data/crossfile_page_decisions.json, which this script consumes.

What applying means, exactly. The losing side's copy is DISPLACED to
data/corpus_secondary/<work>.crossfile-duplicate.jsonl with a reason on every
row, never deleted, and only when it holds no run of three or more
consecutive words absent from the winning copy (the drop tool's gate,
recomputed fresh here); a pair whose losing copy holds unique text gets an
attribution record and no text change. Served counts drop by what moves;
served plus witnessed is conserved.

  python3 scripts/resolve_crossfile_pages.py            # dry run
  python3 scripts/resolve_crossfile_pages.py --apply
  python3 scripts/resolve_crossfile_pages.py --unapply
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
SECONDARY = DATA / "corpus_secondary"
EVIDENCE = DATA / "crossfile_page_evidence.json"
DECISIONS = DATA / "crossfile_page_decisions.json"
AUDIT = DATA / "corpus_changes" / "crossfile-page-attribution.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drop_duplicate_leaf import unique_runs  # noqa: E402


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fail(m):
    raise SystemExit(f"ERROR: {m}")


def load_rows(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def page_rows(fp: Path, key: str) -> list[tuple[int, dict]]:
    return [(i, r) for i, r in enumerate(load_rows(fp))
            if str(r.get("locus", "")).split(".")[0] == key]


def find_file(names: list[str], key: str) -> Path | None:
    for n in names:
        fp = CORPUS / f"{n}.jsonl"
        if fp.exists() and page_rows(fp, key):
            return fp
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()

    if a.unapply:
        if not AUDIT.exists():
            fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for frel, blk in rec["files"].items():
            fp = REPO / frel
            if sha(fp.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{fp.name} has moved since this audit; reverse that first")
            rows = fp.read_text(encoding="utf-8").splitlines()
            rows = [l for l in rows if l.strip()]
            for idx, row_json in sorted(blk["removed"], key=lambda x: x[0]):
                rows.insert(idx, json.dumps(row_json, ensure_ascii=False))
            fp.write_text("".join(l + "\n" for l in rows), encoding="utf-8")
            if sha(fp.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {fp.name}")
        for wrel, n in rec["witness_files"].items():
            wp = REPO / wrel
            lines = [l for l in wp.read_text(encoding="utf-8").splitlines()
                     if l.strip()][:-n]
            if lines:
                wp.write_text("".join(l + "\n" for l in lines), encoding="utf-8")
            else:
                wp.unlink()
        AUDIT.unlink()
        print("UNAPPLIED")
        return

    if AUDIT.exists():
        fail("already applied; --unapply first")

    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    dec = json.loads(DECISIONS.read_text(encoding="utf-8"))
    ties = dec["tie_resolutions"]

    n: Counter = Counter()
    plans, attributions = [], []
    for p in ev:
        if "side_a" not in p:
            continue
        conf = p.get("confidence")
        if conf in ("high", "medium"):
            winner = "A" if p["verdict"].endswith("A") else "B"
            basis = f"neighbor anchor, {conf} ({p['verdict']})"
        elif p["pair"] in ties:
            winner = ties[p["pair"]]["belongs"]
            basis = "content inspection: " + ties[p["pair"]]["basis"]
        else:
            n["skipped: no ruling"] += 1
            continue
        la, lb = [s.strip() for s in p["pair"].split("~")]
        win_key, lose_key = (la, lb) if winner == "A" else (lb, la)
        win_side = p["side_a"] if winner == "A" else p["side_b"]
        lose_side = p["side_b"] if winner == "A" else p["side_a"]
        win_fp = find_file(win_side["files"], win_key)
        lose_fp = find_file(lose_side["files"], lose_key)
        if not win_fp or not lose_fp:
            n["skipped: a side's rows are no longer served"] += 1
            continue
        win_text = " ".join((r.get("text") or "")
                            for _, r in page_rows(win_fp, win_key))
        lose_rows = page_rows(lose_fp, lose_key)
        lose_text = " ".join((r.get("text") or "") for _, r in lose_rows)
        runs = unique_runs(lose_text, win_text)
        entry = {"pair": p["pair"], "belongs": winner, "basis": basis,
                 "winner_file": win_fp.name, "loser_file": lose_fp.name,
                 "loser_page": lose_key, "loser_rows": len(lose_rows),
                 "loser_tokens_ws": len(lose_text.split())}
        if runs:
            entry["action"] = (f"attribution only: the losing copy holds "
                               f"{len(runs)} unique run(s) of 3+ words, so it "
                               f"stays served until merged")
            n["attribution only (loser holds unique text)"] += 1
            attributions.append(entry)
        else:
            entry["action"] = "displaced to corpus_secondary"
            n["displace (loser holds nothing unique)"] += 1
            plans.append(entry)

    for k, v in n.most_common():
        print(f"    {v:>4}  {k}")
    print(f"    {sum(e['loser_tokens_ws'] for e in plans):>4}  "
          f"~whitespace tokens leaving served text")
    if not a.apply:
        print("\nDRY RUN; nothing written.")
        return

    audit_files: dict[str, dict] = {}
    witness_files: Counter = Counter()
    by_loser: dict[str, list] = {}
    for e in plans:
        by_loser.setdefault(e["loser_file"], []).append(e)
    for fname, entries in sorted(by_loser.items()):
        fp = CORPUS / fname
        before = fp.read_text(encoding="utf-8")
        rows = load_rows(fp)
        keys = {e["loser_page"] for e in entries}
        removed = [(i, r) for i, r in enumerate(rows)
                   if str(r.get("locus", "")).split(".")[0] in keys]
        kept = [r for i, r in enumerate(rows)
                if str(r.get("locus", "")).split(".")[0] not in keys]
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in kept), encoding="utf-8")
        audit_files[str(fp.relative_to(REPO))] = {
            "sha256_before": sha(before),
            "sha256_after": sha(fp.read_text(encoding="utf-8")),
            "removed": removed,
        }
        wp = SECONDARY / (fname.replace(".jsonl", "") + ".crossfile-duplicate.jsonl")
        wtxt = wp.read_text(encoding="utf-8") if wp.exists() else ""
        out = []
        for i, r in removed:
            r2 = dict(r)
            e = next(x for x in entries
                     if x["loser_page"] == str(r.get("locus", "")).split(".")[0])
            r2["displaced_by"] = {
                "pass": "crossfile-page-attribution", "date": a.date,
                "reason": f'cross-file duplicate of {e["pair"]}; the page '
                          f'belongs to {e["winner_file"]} ({e["basis"][:120]})'}
            out.append(json.dumps(r2, ensure_ascii=False))
        wp.write_text(wtxt + "".join(l + "\n" for l in out), encoding="utf-8")
        witness_files[str(wp.relative_to(REPO))] += len(removed)

    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "cross-file duplicate pages attributed per cisco's "
                    "2026-08-12 rulings; clean losing copies displaced to "
                    "witnesses, the rest recorded",
            "issue": "open-greek/open-greek-corpus#33",
            "date": a.date,
            "tool": "scripts/resolve_crossfile_pages.py",
            "inputs": [str(EVIDENCE.relative_to(REPO)),
                       str(DECISIONS.relative_to(REPO))],
            "reverse": "python3 scripts/resolve_crossfile_pages.py --unapply",
        },
        "displaced": plans,
        "attribution_only": attributions,
        "files": audit_files,
        "witness_files": dict(witness_files),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED; audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
