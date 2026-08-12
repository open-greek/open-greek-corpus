#!/usr/bin/env python3
"""Merge the four half-clean cgpg leaves instead of half-fixing them.

A doubled leaf delivers two printed columns twice. Where one copy of a column
holds nothing the other lacks, scripts/drop_duplicate_leaf.py can drop it on
page evidence; but on these four leaves the SIBLING column's two reads each
hold text the other lacks, so dropping the clean half leaves the leaf still
duplicated and the sweep still red. cisco ruled on 2026-08-12 for the complete
fix: give both pairs of each leaf the duplicate-read merge treatment that
emptied the ocr leaf-runs on 2026-08-11.

Mechanics reused from scripts/merge_duplicate_reads.py, not reimplemented: the
same merge() vote (agree / attested / winner-guess, majorities cannot arise in
a two-read merge), the same winner rule (collapse_duplicate_reads.score, net
attested minus unattested), the same substitution-into-winner-text apply, and
the same displacement of losing reads to data/corpus_secondary with a reason
on every row. Guesses are enumerated in the audit, never silent.

The leaves have no page-image anchor (PG118's resisted a three-read hunt), so
the merged row keeps the LOWER locus of its pair and the audit records the
one-slot ambiguity per leaf; that is a citation-drift note of the kind the
PG118 and PG122 drop entries already carry, not new text damage.

  python3 scripts/merge_halfclean_leaves.py                  # dry run + previews
  python3 scripts/merge_halfclean_leaves.py --preview OUT.json
  python3 scripts/merge_halfclean_leaves.py --apply          # after cisco's eyeball
  python3 scripts/merge_halfclean_leaves.py --unapply
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
SECONDARY = DATA / "corpus_secondary"
AUDIT = DATA / "corpus_changes" / "cgpg-halfclean-leaf-merge.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from build_ocr_quality_report import build_attestation  # noqa: E402
from carve_cgpg_volume import greek_tokens as ledger_tokens  # noqa: E402
from collapse_duplicate_reads import norm_elision, score  # noqa: E402
from merge_duplicate_reads import apply_subs, merge  # noqa: E402


def fail(m):
    raise SystemExit(f"ERROR: {m}")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def leaves() -> list[dict]:
    """The interlocked served pairs of data/duplicate_leaf_candidates.json:
    (a, a+2) and (a+1, a+3) in one file are one doubled leaf."""
    cand = json.loads((DATA / "duplicate_leaf_candidates.json").read_text(encoding="utf-8"))
    by_file: dict[str, list] = {}
    for p in cand["pairs"]:
        if not p["served"]:
            continue
        la, lb = str(p["locus_a"]), str(p["locus_b"])
        na, nb = int(la.rsplit(".", 1)[1]), int(lb.rsplit(".", 1)[1])
        if abs(na - nb) == 2:
            by_file.setdefault(p["file"], []).append((min(na, nb), la, lb))
    out = []
    for fp, ps in sorted(by_file.items()):
        ps.sort()
        used = set()
        for i, (n, la, lb) in enumerate(ps):
            if n in used:
                continue
            mate = next(((m, ma, mb) for m, ma, mb in ps if m == n + 1), None)
            if mate:
                used.add(mate[0])
                out.append({"file": fp, "pairs": [(la, lb), (mate[1], mate[2])]})
    return out


def spans(text: str) -> list[tuple[int, int, str]]:
    norm = norm_elision(text)
    return [(m.start(), m.end(), unicodedata.normalize("NFC", m.group()))
            for m in _GK.finditer(norm)]


def merge_pair(rows_by_locus: dict, la: str, lb: str, attested: set) -> dict:
    ra, rb = rows_by_locus.get(la), rows_by_locus.get(lb)
    if ra is None or rb is None:
        fail(f"locus {la} or {lb} not served")
    ta, tb = ra.get("text") or "", rb.get("text") or ""
    sa_, sb_ = score(ta, attested)["net"], score(tb, attested)["net"]
    best_is_a = sa_ >= sb_
    win_row, lose_row = (ra, rb) if best_is_a else (rb, ra)
    win_text, lose_text = (ta, tb) if best_is_a else (tb, ta)
    win_spans = spans(win_text)
    reads = [[t for _, _, t in win_spans],
             [t for _, _, t in spans(lose_text)]]
    merged_toks, tally, how = merge(reads, attested, 0)
    subs, guesses = [], []
    for k, (start, end, tok) in enumerate(win_spans):
        if merged_toks[k] != tok:
            subs.append((start, end, merged_toks[k]))
        kind, variants = how[k]
        if kind == "winner" and variants:
            guesses.append({"offset": start, "kept": tok,
                            "rejected": [v for v in variants if v != tok]})
    merged_text = apply_subs(win_text, subs)
    keep_locus = min(la, lb, key=lambda s: int(s.rsplit(".", 1)[1]))
    return {
        "pair": f"{la} ~ {lb}", "keep_locus": keep_locus,
        "winner_locus": str(win_row["locus"]), "loser_locus": str(lose_row["locus"]),
        "score_a": sa_, "score_b": sb_, "tally": tally,
        "tokens_substituted": len(subs), "guesses": guesses,
        "read_a": ta, "read_b": tb, "merged": merged_text,
        "win_row": win_row, "lose_row": lose_row,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", default=None,
                    help="write the per-pair previews (both reads, merged "
                         "text, guesses) to this JSON file")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()

    if a.unapply:
        if not AUDIT.exists():
            fail("no audit")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for fp, blk in rec["files"].items():
            p = REPO / fp
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{p.name} has moved since this audit; reverse that first")
            p.write_text(blk["original_text"], encoding="utf-8")
            if sha(p.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {p.name}")
        for fp, blk in rec["witness_files"].items():
            p = REPO / fp
            lines = [l for l in p.read_text(encoding="utf-8").splitlines()
                     if l.strip()][: -blk["rows_appended"]]
            p.write_text("".join(l + "\n" for l in lines), encoding="utf-8")
            if not lines:
                p.unlink()
        lp = DATA / "cgpg_works.json"
        lp.write_text(rec["ledger_before"], encoding="utf-8")
        AUDIT.unlink()
        print("UNAPPLIED")
        return

    if AUDIT.exists():
        fail("already applied; --unapply first")

    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions["works"] if "works" in editions else editions
    attested, st = build_attestation(editions)
    print(f"attestation: {st['n_unique_forms']:,} forms")

    plans, previews = [], []
    for leaf in leaves():
        fp = REPO / leaf["file"]
        rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        by_locus = {str(r["locus"]): r for r in rows}
        merged_pairs = [merge_pair(by_locus, la, lb, attested)
                        for la, lb in leaf["pairs"]]
        plans.append({"file": leaf["file"], "rows": rows, "pairs": merged_pairs})
        for m in merged_pairs:
            previews.append({k: m[k] for k in
                             ("pair", "keep_locus", "winner_locus", "tally",
                              "tokens_substituted", "guesses", "read_a",
                              "read_b", "merged")}
                            | {"file": leaf["file"]})
        print(f"{fp.name}: " + "; ".join(
            f'{m["pair"]} -> keep {m["keep_locus"]} '
            f'({m["tally"]}, {len(m["guesses"])} guesses)'
            for m in merged_pairs))

    if a.preview:
        Path(a.preview).write_text(json.dumps(previews, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        print(f"previews -> {a.preview}")
    if not a.apply:
        print("\nDRY RUN; nothing written. --apply after the previews are approved.")
        return

    # One write per FILE, never per leaf: amphilochia and the Zonaras volume
    # each hold two doubled leaves, and a per-leaf write would rebuild the file
    # from that leaf's own pre-apply row list, resurrecting the rows the
    # earlier leaf dropped. Group first, then read-modify-write once.
    by_file: dict[str, list] = {}
    for plan in plans:
        by_file.setdefault(plan["file"], []).extend(plan["pairs"])

    audit_files, witness_files = {}, {}
    ledger_before = (DATA / "cgpg_works.json").read_text(encoding="utf-8")
    for file_rel, pairs_of_file in sorted(by_file.items()):
        fp = REPO / file_rel
        before = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in before.splitlines() if l.strip()]
        by_locus = {str(r["locus"]): r for r in rows}
        drop_loci, displaced = set(), []
        for m in pairs_of_file:
            keep = by_locus[m["keep_locus"]]
            keep["text"] = m["merged"]
            keep["merged_read"] = {
                "of": m["pair"], "guesses": len(m["guesses"]),
                "note": "cgpg half-clean leaf merge; no page-image anchor, "
                        "lower locus kept, one-slot ambiguity recorded"}
            other = (set(m["pair"].split(" ~ ")) - {m["keep_locus"]}).pop()
            drop_loci.add(other)
            lose = dict(by_locus[other])
            lose["displaced_by"] = {
                "pass": "cgpg-halfclean-leaf-merge", "date": a.date,
                "reason": f'losing read of {m["pair"]}; merged into '
                          f'{m["keep_locus"]}'}
            displaced.append(lose)
        kept_rows = [r for r in rows if str(r["locus"]) not in drop_loci]
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in kept_rows), encoding="utf-8")
        audit_files[file_rel] = {
            "sha256_before": sha(before),
            "sha256_after": sha(fp.read_text(encoding="utf-8")),
            "original_text": before,
        }
        wfp = SECONDARY / (fp.name.replace(".jsonl", "") + ".duplicate-read-merged.jsonl")
        wtxt = wfp.read_text(encoding="utf-8") if wfp.exists() else ""
        wfp.write_text(wtxt + "".join(json.dumps(r, ensure_ascii=False) + "\n"
                                      for r in displaced), encoding="utf-8")
        witness_files[str(wfp.relative_to(REPO))] = {"rows_appended": len(displaced)}
        lp = DATA / "cgpg_works.json"
        vols = json.loads(lp.read_text(encoding="utf-8"))
        stem = fp.name[: -len(".jsonl")]
        for e in vols:
            if e.get("urn") == stem:
                e["n_passages"] = len(kept_rows)
                e["n_tokens"] = sum(ledger_tokens(r["text"]) for r in kept_rows)
        lp.write_text(json.dumps(vols, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")

    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "the four half-clean cgpg leaves merged per pair instead "
                    "of half-dropped",
            "issue": "open-greek/open-greek-corpus#33",
            "date": a.date,
            "tool": "scripts/merge_halfclean_leaves.py",
            "reverse": "python3 scripts/merge_halfclean_leaves.py --unapply",
            "locus_note": "no page-image anchor exists for these leaves; each "
                          "merged row keeps the lower locus and later loci in "
                          "these files may sit one slot above their printed "
                          "columns",
        },
        "pairs": [{k: m[k] for k in ("pair", "keep_locus", "winner_locus",
                                     "tally", "tokens_substituted", "guesses")}
                  for plan in plans for m in plan["pairs"]],
        "files": audit_files,
        "witness_files": witness_files,
        "ledger_before": ledger_before,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED; audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
