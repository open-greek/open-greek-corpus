#!/usr/bin/env python3
"""Cut a work out of a Migne volume when its boundary falls INSIDE a row.

carve_cgpg_volume.py moves whole rows, which is the right default: a row is a
printed page, and a work almost always starts on one. Some do not. Migne prints
the next work's head partway down a column, and the row that carries it holds
the tail of one work and the head of another. Three commits have named this as
the reason five identified works with printed titles are still unserved
(Euthalius Diaconus' Prologos, Apodemiai and Martyrion in PG118; Gregory
Palamas' Homologia and the archbishops' Anaphora in PG151).

The alternative to this tool is the shared-row rule, which gives the whole row
to one side. That is fine when the shared part is small next to the work. It is
not fine here: it would file 37% of a named author's work under someone else's
document. So the cut has to be real.

No new locus convention is minted. Both halves keep the SAME "<VOL>.<page>"
locus in their own work files, because a printed page legitimately carries two
works and per-work locus spaces are independent. Nothing downstream has to learn
a sub-locus form.

Boundary correctness is what this checks hardest, because token conservation
cannot see it. A cut at the wrong offset conserves every token and still puts
the wrong text under the wrong author. So each plan entry names the head string
that must appear AT the offset and the text that must end the part before it,
and both are asserted against the file before anything is written. The row's
sha256 is asserted too, so a plan measured against one state of the corpus
refuses to run against another.

  python3 scripts/split_carved_row.py --volume PG118
  python3 scripts/split_carved_row.py --volume PG118 --apply
  python3 scripts/split_carved_row.py --volume PG118 --unapply   # from the audit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CHANGES = DATA / "corpus_changes"
PLAN = DATA / "row_split_plan.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from carve_cgpg_volume import greek_tokens as _ledger_tokens  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def n_tok(s: str) -> int:
    return len(_GK.findall(s or ""))


def read_rows(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def write_rows(fp: Path, rows: list[dict]) -> None:
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                  encoding="utf-8")


def audit_path(vol: str) -> Path:
    return CHANGES / f"cogPG.{vol}.row-split.json"


def check_cut(text: str, off: int, head: str, ends_with: str, where: str) -> None:
    """The check that catches a wrong offset. Conservation never will."""
    if not 0 <= off <= len(text):
        fail(f"{where}: offset {off} outside a row of {len(text)} characters")
    if off and not text[off - 1].isspace():
        fail(f"{where}: offset {off} is not at a whitespace boundary "
             f"(would cut the word {text[max(0, off - 20):off + 20]!r})")
    got = text[off:off + len(head)]
    if got != head:
        fail(f"{where}: expected the head {head!r} at offset {off}, found {got!r}")
    before = text[:off].rstrip()
    if ends_with and not before.endswith(ends_with):
        fail(f"{where}: the text before offset {off} should end with "
             f"{ends_with!r}, it ends with {before[-len(ends_with) - 20:]!r}")


def build(vol: str, plan: dict, rows: list[dict]) -> tuple[dict, list[dict], dict]:
    by_locus = {str(r["locus"]): r for r in rows}
    order = [str(r["locus"]) for r in rows]
    # claimed[locus] = list of (start, end, slug), filled in plan order
    claimed: dict[str, list] = {}
    per_work: dict[str, list[dict]] = {}
    checks = []

    for w in plan["works"]:
        slug, a, b = w["slug"], w["from"], w["to"]
        for side in (a, b):
            if str(side["locus"]) not in by_locus:
                fail(f"{slug}: locus {side['locus']} is not in cogPG.{vol}")
        i, j = order.index(str(a["locus"])), order.index(str(b["locus"]))
        if j < i:
            fail(f"{slug}: 'to' locus precedes 'from' locus")

        row = by_locus[str(a["locus"])]
        if sha(row["text"]) != a["row_sha256"]:
            fail(f"{slug}: locus {a['locus']} no longer matches the row this "
                 f"plan was measured against")
        check_cut(row["text"], a["offset"], w["head"], a.get("prev_ends_with", ""),
                  f"{slug} start, locus {a['locus']}")
        checks.append({"slug": slug, "locus": str(a["locus"]),
                       "offset": a["offset"], "head": w["head"],
                       "prev_ends_with": a.get("prev_ends_with", "")})

        end_off = b.get("offset")
        if end_off is not None:
            erow = by_locus[str(b["locus"])]
            if sha(erow["text"]) != b["row_sha256"]:
                fail(f"{slug}: locus {b['locus']} no longer matches the plan")
            check_cut(erow["text"], end_off, b["next_head"],
                      b.get("prev_ends_with", ""),
                      f"{slug} end, locus {b['locus']}")

        out = []
        for k in range(i, j + 1):
            loc = order[k]
            text = by_locus[loc]["text"]
            s = a["offset"] if k == i else 0
            e = end_off if (k == j and end_off is not None) else len(text)
            claimed.setdefault(loc, []).append((s, e, slug))
            part = text[s:e].strip()
            if not part:
                continue
            r = dict(by_locus[loc])
            r["urn"] = slug
            r["locus"] = f"{vol}.{loc}"
            r["text"] = part
            if s or e != len(text):
                r["row_part"] = (f"characters {s}-{e} of Migne {vol} page {loc}, "
                                 f"which prints more than one work")
            out.append(r)
        per_work[slug] = out

    # residual: whatever no work claimed, in row order
    residual = []
    for r in rows:
        loc = str(r["locus"])
        spans = sorted(claimed.get(loc, []))
        if not spans:
            residual.append(r)
            continue
        prev, keep = 0, []
        for s, e, slug in spans:
            if s < prev:
                fail(f"locus {loc}: {slug} overlaps an earlier claim")
            keep.append(r["text"][prev:s])
            prev = e
        keep.append(r["text"][prev:])
        left = " ".join(" ".join(keep).split())
        if left:
            nr = dict(r)
            nr["text"] = left
            nr["row_part"] = (f"the part of Migne {vol} page {loc} that no carved "
                              f"work claims; see data/corpus_changes/"
                              f"cogPG.{vol}.row-split.json")
            residual.append(nr)

    # token conservation, per row and overall, with _GK
    before = sum(n_tok(r["text"]) for r in rows)
    after = sum(n_tok(r["text"]) for r in residual)
    for out in per_work.values():
        after += sum(n_tok(r["text"]) for r in out)
    if before != after:
        fail(f"token conservation: {before} in, {after} out (delta {after - before}). "
             f"A cut that lands inside a Greek run splits one token into two; "
             f"every offset here must sit at a whitespace boundary.")
    return per_work, residual, {"checks": checks, "tokens": before}


def update_cgpg_works(vol: str, plan: dict, per_work: dict[str, list[dict]],
                      residual: list[dict]) -> None:
    """Same ledger carve_cgpg_volume.py maintains, same shape.

    Skipping this is not cosmetic: `make check` compares this file's counts
    against the corpus and fails the build when they drift, which is how the
    last row move got caught. The three works here carry no TLG id, so their
    `works` list is empty, the way any Canon-less carved work's is.
    """
    # NB two token metrics, deliberately. Conservation uses _GK (maximal Greek
    # runs), which is what this repo publishes. cgpg_works.json is checked
    # against corpus_editions.json, which counts whitespace-split words holding
    # a Greek character, and the two disagree by a fraction of a percent. Writing
    # _GK counts here passes every check in this script and then fails `make
    # check`, which is how I found it. Match the ledger's own metric in the
    # ledger; never mix them in one file.
    fp = DATA / "cgpg_works.json"
    vols = json.loads(fp.read_text(encoding="utf-8"))
    src_urn = f"cogPG.{vol}"
    vol_idx = next((i for i, e in enumerate(vols) if e.get("urn") == src_urn), None)
    if vol_idx is None:
        fail(f"cgpg_works.json: no entry for {src_urn}")
    vol_entry = vols[vol_idx]
    template = {k: vol_entry[k] for k in ("edition", "license", "source")}
    vol_entry["n_passages"] = len(residual)
    vol_entry["n_tokens"] = sum(_ledger_tokens(r["text"]) for r in residual)

    by_slug = {w["slug"]: w for w in plan["works"]}
    new = []
    for slug, out in per_work.items():
        w = by_slug[slug]
        loci = sorted({r["locus"].split(".", 1)[1] for r in out}, key=int)
        span = loci[0] if len(loci) == 1 else f"{loci[0]}-{loci[-1]}"
        new.append({
            "volume": vol, "urn": slug, "kind": "work",
            "desc": f"{w.get('author_display', '')} - {w['title']} "
                    f"({vol} loci {span}, cut at a character offset)".strip(" -"),
            **template,
            "n_passages": len(out),
            "n_tokens": sum(_ledger_tokens(r["text"]) for r in out),
            "works": [],
            "cgpg_chosen": w.get("rank", "primary") == "primary",
        })
    slugs = {e["urn"] for e in new}
    vols = [e for e in vols
            if not (e.get("urn") in slugs and e.get("volume") == vol)]
    vol_idx = next(i for i, e in enumerate(vols) if e.get("urn") == src_urn)
    vols[vol_idx + 1:vol_idx + 1] = new
    fp.write_text(json.dumps(vols, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volume", required=True)
    ap.add_argument("--plan", default=str(PLAN))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    vol = args.volume
    vol_fp = CORPUS / f"cogPG.{vol}.jsonl"
    ap_fp = audit_path(vol)

    if args.unapply:
        if not ap_fp.exists():
            fail(f"no audit at {ap_fp.relative_to(REPO)}")
        rec = json.loads(ap_fp.read_text(encoding="utf-8"))
        for slug in rec["works"]:
            f = CORPUS / f"{slug}.jsonl"
            if f.exists():
                f.unlink()
        write_rows(vol_fp, rec["original_rows"])
        got = sha(vol_fp.read_text(encoding="utf-8"))
        if got != rec["volume"]["sha256_before"]:
            fail(f"unapply did not restore cogPG.{vol} byte-for-byte")
        ap_fp.unlink()
        print(f"UNAPPLIED: cogPG.{vol} restored to {got[:12]}, work files removed")
        return

    plan_all = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = next((v for v in plan_all["volumes"] if v["volume"] == vol), None)
    if plan is None:
        fail(f"no row-split plan entry for {vol}")
    if ap_fp.exists():
        fail(f"{ap_fp.relative_to(REPO)} already exists; --unapply first")

    rows = read_rows(vol_fp)
    before_text = vol_fp.read_text(encoding="utf-8")
    per_work, residual, meta = build(vol, plan, rows)

    print(f"cogPG.{vol}: {len(rows)} rows / {meta['tokens']:,} greek tokens ->")
    for slug, out in per_work.items():
        print(f"      {slug}  {len(out)} rows  "
              f"{sum(n_tok(r['text']) for r in out):,} tok")
    print(f"      residual: {len(residual)} rows / "
          f"{sum(n_tok(r['text']) for r in residual):,} tok")
    if not args.apply:
        print("CHECK only (pass --apply to write)")
        return

    for slug, out in per_work.items():
        f = CORPUS / f"{slug}.jsonl"
        if f.exists():
            fail(f"{f.relative_to(REPO)} already exists")
        write_rows(f, out)
    write_rows(vol_fp, residual)
    update_cgpg_works(vol, plan, per_work, residual)

    ap_fp.write_text(json.dumps({
        "_meta": {
            "what": f"rows of cogPG.{vol} cut at a character offset so works whose "
                    f"printed head falls inside a row can be served",
            "date": plan["date"],
            "issue": "open-greek/open-greek-corpus#8",
            "tool": "scripts/split_carved_row.py",
            "reverse": f"python3 scripts/split_carved_row.py --volume {vol} --unapply",
            "basis": plan.get("basis", ""),
        },
        "volume": {
            "file": f"data/corpus/cogPG.{vol}.jsonl",
            "sha256_before": sha(before_text),
            "sha256_after": sha(vol_fp.read_text(encoding="utf-8")),
            "rows_before": len(rows), "rows_after": len(residual),
        },
        "works": {slug: {
            "file": f"data/corpus/{slug}.jsonl",
            "rows": len(out),
            "greek_tokens": sum(n_tok(r["text"]) for r in out),
            "sha256": sha((CORPUS / f"{slug}.jsonl").read_text(encoding="utf-8")),
        } for slug, out in per_work.items()},
        "boundary_checks": meta["checks"],
        "token_conservation": {
            "original": meta["tokens"],
            "check": "sum over every work file and the residual == original (exact, _GK)",
        },
        "original_rows": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED: {len(per_work)} work files, residual rewritten, "
          f"audit {ap_fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
