#!/usr/bin/env python3
"""Drop a printed leaf the OCR delivered twice.

carve_cgpg_volume.py already sheds rescanned leaves, gated on difflib
similarity >= 0.60 against the row it keeps. That catches a leaf whose two
reads agree. It does not catch this one: PG118 pages 21 and 22 arrive twice,
and the second read of page 22 walked the columns in a different order, so the
two rows of the same page score 0.482 and sail under the gate while the corpus
serves the page twice.

Similarity is the wrong test anyway. The question is not whether two rows look
alike, it is whether the copy being dropped holds text the survivor does not.
So the gate here is vocabulary: every run of three or more consecutive words in
the dropped row that do not appear anywhere in the kept row is reported, and the
plan has to name each one. An unlisted run stops the run. That is what makes
this a deletion of duplicated text rather than a deletion of text.

The duplication is established from the page, not inferred. Each plan entry
cites the scan (Internet Archive item patrologia.graeca.org) and what the page
prints, because two rows of similar Greek are not on their own evidence that a
leaf was scanned twice rather than an author repeating himself.

  python3 scripts/drop_duplicate_leaf.py --volume PG118
  python3 scripts/drop_duplicate_leaf.py --volume PG118 --apply
  python3 scripts/drop_duplicate_leaf.py --volume PG118 --unapply
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CHANGES = DATA / "corpus_changes"
PLAN = DATA / "duplicate_leaves.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from carve_cgpg_volume import greek_tokens as _ledger_tokens  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def words(s: str) -> list[str]:
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if not unicodedata.combining(c)).lower()
    return re.sub(r"[^α-ω ]+", " ", s).split()


def unique_runs(dropped: str, kept: str, n: int = 3) -> list[str]:
    """Runs of >= n consecutive words in `dropped` absent from `kept`'s
    vocabulary. This is the check that decides whether dropping loses text."""
    have = set(words(kept))
    runs, cur = [], []
    for w in words(dropped):
        if w not in have:
            cur.append(w)
        else:
            if len(cur) >= n:
                runs.append(" ".join(cur))
            cur = []
    if len(cur) >= n:
        runs.append(" ".join(cur))
    return runs


def audit_path(vol: str) -> Path:
    # Keyed by the plan entry's id, not the volume: one volume can have several
    # duplicated leaves in different works, and each needs its own reversible
    # record rather than being folded into a single file.
    return CHANGES / f"cogPG.{vol}.duplicate-leaf.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volume", required=True,
                    help="a plan entry's id, which defaults to its volume")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    vol = args.volume
    # The rows are not always still in the volume file: a duplicated leaf can
    # sit inside a work an earlier carve already moved them into, which is where
    # PG126's is. The plan names the file; the volume dump is only the default.
    plan_all = json.loads(PLAN.read_text(encoding="utf-8"))
    _p = next((v for v in plan_all["volumes"] if v.get("id", v["volume"]) == vol), None)
    fp = REPO / _p["file"] if (_p and _p.get("file")) else CORPUS / f"cogPG.{vol}.jsonl"
    ap_fp = audit_path(vol)

    if args.unapply:
        if not ap_fp.exists():
            fail(f"no audit at {ap_fp.relative_to(REPO)}")
        rec = json.loads(ap_fp.read_text(encoding="utf-8"))
        fp = REPO / rec["file"]["path"]
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in rec["original_rows"]), encoding="utf-8")
        got = sha(fp.read_text(encoding="utf-8"))
        if got != rec["file"]["sha256_before"]:
            fail(f"unapply did not restore {fp.name} byte-for-byte")
        ap_fp.unlink()
        print(f"UNAPPLIED: {fp.name} restored to {got[:12]}")
        return

    plan = _p
    if plan is None:
        fail(f"no duplicate-leaf plan entry with id {vol!r}")
    if ap_fp.exists():
        fail(f"{ap_fp.relative_to(REPO)} already exists; --unapply first")

    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    by = {str(r["locus"]): r for r in rows}
    before_text = fp.read_text(encoding="utf-8")
    dropped, report = [], []

    for d in plan["drops"]:
        k, x = str(d["keep"]), str(d["drop"])
        for loc in (k, x):
            if loc not in by:
                fail(f"locus {loc} is not in cogPG.{vol}")
        if sha(by[k]["text"]) != d["keep_sha256"]:
            fail(f"locus {k} no longer matches the row this plan was measured against")
        if sha(by[x]["text"]) != d["drop_sha256"]:
            fail(f"locus {x} no longer matches the row this plan was measured against")
        runs = unique_runs(by[x]["text"], by[k]["text"])
        listed = d.get("expected_unique_runs", [])
        unlisted = [r for r in runs if r not in listed]
        if unlisted:
            fail(f"dropping {x} would lose text the plan does not account for. "
                 f"Unlisted runs of 3+ words absent from locus {k}:\n  "
                 + "\n  ".join(unlisted[:5]))
        stale = [r for r in listed if r not in runs]
        if stale:
            fail(f"locus {x}: the plan lists runs that are no longer there "
                 f"({stale[:2]}); it was measured against different bytes")
        ratio = difflib.SequenceMatcher(None, by[k]["text"], by[x]["text"],
                                        autojunk=False).ratio()
        report.append({
            "keep": k, "drop": x,
            "similarity": round(ratio, 4),
            "dropped_tokens": len(_GK.findall(by[x]["text"])),
            "unique_runs_accounted_for": runs,
            "page_evidence": d["page_evidence"],
        })
        dropped.append(by[x])

    total = sum(r["dropped_tokens"] for r in report)
    print(f"cogPG.{vol}: dropping {len(dropped)} row(s), {total:,} greek tokens")
    for r in report:
        print(f"      locus {r['drop']} (duplicate of {r['keep']}, similarity "
              f"{r['similarity']}): {r['dropped_tokens']:,} tok")
    if not args.apply:
        print("CHECK only (pass --apply to write)")
        return

    drop_ids = {str(r["locus"]) for r in dropped}
    kept_rows = [r for r in rows if str(r["locus"]) not in drop_ids]
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                          for r in kept_rows), encoding="utf-8")

    # cgpg_works.json is compared against corpus_editions by `make check`, which
    # fails the build on drift, so the ledger moves in the same step. Its counts
    # use the whitespace-split metric that file is keyed on, not _GK.
    lp = DATA / "cgpg_works.json"
    vols = json.loads(lp.read_text(encoding="utf-8"))
    stem = fp.name[:-len(".jsonl")]
    for e in vols:
        if e.get("urn") == stem:
            e["n_passages"] = len(kept_rows)
            e["n_tokens"] = sum(_ledger_tokens(r["text"]) for r in kept_rows)
    lp.write_text(json.dumps(vols, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")
    ap_fp.write_text(json.dumps({
        "_meta": {
            "what": f"rows of cogPG.{vol} dropped as a leaf the OCR delivered twice",
            "date": plan["date"],
            "issue": plan.get("issue", ""),
            "tool": "scripts/drop_duplicate_leaf.py",
            "reverse": f"python3 scripts/drop_duplicate_leaf.py --volume {vol} --unapply",
            "note": "the served token count falls by the amount below; those "
                    "tokens were counted twice before, so the total gets smaller "
                    "and more correct at once",
        },
        "file": {
            "path": fp.relative_to(REPO).as_posix(),
            "sha256_before": sha(before_text),
            "sha256_after": sha(fp.read_text(encoding="utf-8")),
            "rows_before": len(rows), "rows_after": len(kept_rows),
            "greek_tokens_dropped": total,
        },
        "drops": report,
        "dropped_rows": dropped,
        "original_rows": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED: audit {ap_fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
