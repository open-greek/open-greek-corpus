#!/usr/bin/env python3
"""Merge the cross-file duplicate pages whose losing copy still holds text.

A carve splits a scan item across the works printed in it, so a page the
scanner delivered twice can land once in each of two works. resolve_crossfile_
pages.py attributed all 78 of those pairs and displaced the 33 whose losing
copy held nothing the winner did not. The other 45 could not be displaced: each
holds at least one run of three or more words the winner is missing, so
dropping it would lose text. They have stayed served, and their ~17,600 tokens
are counted twice.

Merging is what resolve could not do. Both copies are reads of the SAME printed
page, so where they disagree one of them misread; the merge takes the winner's
stream as the spine, aligns the loser's against it, and prefers a reading the
clean corpus attests when only one of the two is a real word. The winner's rows
are rewritten in place, the loser's rows move to
data/corpus_secondary/<work>.crossfile-duplicate.jsonl with the reason on every
row, and served counts drop by exactly what moved.

Positions where the reads disagree and neither is attested fall through to the
winner and are enumerated in the audit, the same honesty the same-item merge
keeps: text nobody's scan attests is recorded as guessed rather than presented
as read.

  python3 scripts/merge_crossfile_pages.py            # dry run
  python3 scripts/merge_crossfile_pages.py --apply
  python3 scripts/merge_crossfile_pages.py --unapply
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
SOURCE = DATA / "corpus_changes" / "crossfile-page-attribution.json"
AUDIT = DATA / "corpus_changes" / "crossfile-page-merge.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ocr_quality_report import build_attestation  # noqa: E402
from merge_duplicate_reads import apply_subs, merge, page_spans  # noqa: E402


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fail(m):
    raise SystemExit(f"ERROR: {m}")


def index_bound() -> dict[str, str]:
    """Files whose row NUMBERING another applied audit still depends on.

    Several passes record their work as row indices rather than loci, and their
    --unapply reinserts at those indices. Removing a row from such a file
    silently invalidates that audit: the reversal still runs, and puts the rows
    back in the wrong places. The duplicate-read merge is the live example, and
    tests/test_duplicate_read_merge.py catches it by walking its guesses back to
    the served token, which is how this was found rather than shipped.

    So those files are off limits to this pass, and a pair that would touch one
    stays attributed instead of merged. Ordering is the real fix and it is not
    available retroactively.
    """
    out: dict[str, str] = {}
    for fp in sorted((DATA / "corpus_changes").glob("*.json")):
        if fp.name == AUDIT.name:
            continue
        try:
            rec = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        files = rec.get("files") if isinstance(rec, dict) else None
        if not isinstance(files, dict):
            continue
        for frel, blk in files.items():
            if isinstance(blk, dict) and any(
                    blk.get(k) for k in ("guesses", "removed_rows")):
                out.setdefault(frel, fp.name)
    return out


def load(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def dump(fp: Path, rows: list[dict]) -> None:
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                  encoding="utf-8")


def do_unapply() -> None:
    if not AUDIT.exists():
        fail("no audit")
    rec = json.loads(AUDIT.read_text(encoding="utf-8"))
    for frel, blk in rec["files"].items():
        fp = REPO / frel
        if sha(fp.read_text(encoding="utf-8")) != blk["sha256_after"]:
            fail(f"{fp.name} has moved since this audit; reverse that first")
        rows = load(fp)
        for idx, text in blk.get("rewritten", []):
            rows[idx]["text"] = text
        for idx, row in sorted(blk.get("removed", []), key=lambda x: x[0]):
            rows.insert(idx, row)
        dump(fp, rows)
        if sha(fp.read_text(encoding="utf-8")) != blk["sha256_before"]:
            fail(f"unapply did not restore {fp.name}")
    for wrel, n in rec["witness_files"].items():
        wp = REPO / wrel
        lines = [l for l in wp.read_text(encoding="utf-8").splitlines() if l.strip()]
        rest = lines[:-n]
        if rest:
            wp.write_text("".join(l + "\n" for l in rest), encoding="utf-8")
        else:
            wp.unlink()
    AUDIT.unlink()
    print("UNAPPLIED")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()

    if a.unapply:
        do_unapply()
        return
    if AUDIT.exists():
        fail("already applied; --unapply first")
    if not SOURCE.exists():
        fail(f"missing {SOURCE.relative_to(REPO)}; run resolve_crossfile_pages.py")

    pairs = json.loads(SOURCE.read_text(encoding="utf-8"))["attribution_only"]
    print(f"    {len(pairs):>4}  cross-file pairs whose losing copy holds unique text")
    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions.get("works", editions)
    attested, att_stats = build_attestation(editions)
    print(f"    {att_stats['n_unique_forms']:>4,}  attested forms from "
          f"{att_stats['n_works']:,} non-OCR works")

    bound = index_bound()
    n: Counter = Counter()
    plans, guesses, held = [], [], []
    for p in pairs:
        sides = [s.strip() for s in p["pair"].split("~")]
        win_page = next(s for s in sides if s != p["loser_page"])
        win_fp, lose_fp = CORPUS / p["winner_file"], CORPUS / p["loser_file"]
        if not (win_fp.exists() and lose_fp.exists()):
            n["skipped: a side's file is gone"] += 1
            continue
        owner = bound.get(str(lose_fp.relative_to(REPO)))
        if owner:
            n["held: another audit indexes the losing file by row"] += 1
            held.append({"pair": p["pair"], "loser_file": p["loser_file"],
                         "blocked_by": owner,
                         "why": "removing rows would invalidate that audit's "
                                "row indices, so this pair stays attributed"})
            continue
        win_rows, lose_rows = load(win_fp), load(lose_fp)
        win_spans = page_spans(win_rows).get(win_page)
        lose_spans = page_spans(lose_rows).get(p["loser_page"])
        if not win_spans or not lose_spans:
            n["skipped: a side's page no longer has rows"] += 1
            continue

        merged, tally, how = merge([[t[3] for t in win_spans],
                                    [t[3] for t in lose_spans]], attested, 0)
        subs: dict[int, list] = {}
        changed = 0
        for k, (i, start, end, tok) in enumerate(win_spans):
            if merged[k] != tok:
                subs.setdefault(i, []).append((start, end, merged[k]))
                changed += 1
            if how[k][0] == "winner" and how[k][1]:
                guesses.append({"pair": p["pair"], "page": win_page,
                                "position": k, "kept": tok,
                                "variants": how[k][1]})
        n["pairs merged"] += 1
        n["tokens substituted"] += changed
        plans.append({"pair": p["pair"], "winner_file": p["winner_file"],
                      "winner_page": win_page, "loser_file": p["loser_file"],
                      "loser_page": p["loser_page"], "basis": p["basis"],
                      "substitutions": changed, "how": dict(tally),
                      "loser_rows": len(lose_rows and [r for r in lose_rows]),
                      "loser_tokens_ws": p["loser_tokens_ws"],
                      "_subs": {str(k): v for k, v in subs.items()}})

    for k, v in n.most_common():
        print(f"    {v:>4}  {k}")
    print(f"    {sum(p['loser_tokens_ws'] for p in plans):>4}  ~whitespace tokens "
          f"leaving served text")
    print(f"    {len(guesses):>4}  positions where the reads disagree and neither "
          f"is attested")
    if not a.apply:
        print("\nDRY RUN; nothing written.")
        return

    files: dict[str, dict] = {}
    witness: Counter = Counter()

    by_winner: dict[str, list] = {}
    by_loser: dict[str, list] = {}
    for p in plans:
        by_winner.setdefault(p["winner_file"], []).append(p)
        by_loser.setdefault(p["loser_file"], []).append(p)

    # Winners first: rewrite text in place, grouped per FILE so two pairs
    # landing in one work cannot each write from their own stale read.
    for fname, ps in sorted(by_winner.items()):
        fp = CORPUS / fname
        before = fp.read_text(encoding="utf-8")
        rows = load(fp)
        rewritten = []
        for p in ps:
            for idx, subs in p["_subs"].items():
                i = int(idx)
                rewritten.append([i, rows[i]["text"]])
                rows[i]["text"] = apply_subs(rows[i]["text"],
                                             [tuple(s) for s in subs])
        dump(fp, rows)
        files[str(fp.relative_to(REPO))] = {
            "sha256_before": sha(before),
            "sha256_after": sha(fp.read_text(encoding="utf-8")),
            "rewritten": rewritten}

    # Losers second: their pages move out to witnesses.
    for fname, ps in sorted(by_loser.items()):
        fp = CORPUS / fname
        before = fp.read_text(encoding="utf-8")
        rows = load(fp)
        keys = {p["loser_page"] for p in ps}
        removed = [[i, r] for i, r in enumerate(rows)
                   if str(r.get("locus", "")).split(".")[0] in keys]
        kept = [r for r in rows
                if str(r.get("locus", "")).split(".")[0] not in keys]
        dump(fp, kept)
        blk = files.setdefault(str(fp.relative_to(REPO)),
                               {"sha256_before": sha(before), "rewritten": []})
        blk["removed"] = removed
        blk["sha256_after"] = sha(fp.read_text(encoding="utf-8"))
        wp = SECONDARY / (fname.replace(".jsonl", "") + ".crossfile-duplicate.jsonl")
        prev = wp.read_text(encoding="utf-8") if wp.exists() else ""
        out = []
        for i, r in removed:
            p = next(x for x in ps
                     if x["loser_page"] == str(r.get("locus", "")).split(".")[0])
            r2 = dict(r)
            r2["displaced_by"] = {
                "pass": "crossfile-page-merge", "date": a.date,
                "reason": f'merged into {p["winner_file"]} page {p["winner_page"]} '
                          f'({p["basis"][:100]}); its readings were folded in '
                          f'before the rows moved'}
            out.append(json.dumps(r2, ensure_ascii=False))
        wp.write_text(prev + "".join(l + "\n" for l in out), encoding="utf-8")
        witness[str(wp.relative_to(REPO))] += len(removed)

    for p in plans:
        p.pop("_subs", None)
    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "cross-file duplicate pages merged: the losing copy's "
                    "readings folded into the winner, then its rows displaced "
                    "to witnesses. These are the 45 pairs resolve_crossfile_"
                    "pages.py could only attribute, because each held unique "
                    "text that displacing alone would have lost",
            "issue": "open-greek/open-greek-corpus#33",
            "date": a.date,
            "tool": "scripts/merge_crossfile_pages.py",
            "input": str(SOURCE.relative_to(REPO)),
            "reverse": "python3 scripts/merge_crossfile_pages.py --unapply",
        },
        "counts": dict(n),
        "held_back": held,
        "merged": plans,
        "guessed_positions": guesses,
        "files": files,
        "witness_files": dict(witness),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED; audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
