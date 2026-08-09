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


def load_file(fp: Path) -> list[dict]:
    if not fp.exists():
        fail(f"{fp} does not exist")
    return read_rows(fp)


def build(vol: str, plan: dict) -> tuple[dict, dict, dict]:
    """(per-work rows, per-file residual rows, audit meta).

    A work is a list of PARTS, each naming its own file, locus and character
    range. Nothing is inferred from row order, because the thing this has to
    express is not a range: PG151 locus 389 is column-interleaved, so the
    Homologia holds characters 1207-1392 AND 3068-end of that row while the
    tome keeps the 1,676 characters between them. A start/end model cannot say
    that; a list of parts can, and it says it in the plan where a reader can
    check it against the page.
    """
    files: dict[str, list[dict]] = {}
    by_key: dict[tuple, dict] = {}
    for w in plan["works"]:
        for pt in w["parts"]:
            f = pt["file"]
            if f not in files:
                files[f] = load_file(REPO / f)
                for r in files[f]:
                    by_key[(f, str(r["locus"]))] = r

    claimed: dict[tuple, list] = {}
    per_work: dict[str, list[dict]] = {}
    checks = []

    for w in plan["works"]:
        slug = w["slug"]
        merged: dict[tuple, list[str]] = {}
        order: list[tuple] = []
        for pt in w["parts"]:
            key = (pt["file"], str(pt["locus"]))
            row = by_key.get(key)
            if row is None:
                fail(f"{slug}: {pt['locus']} is not in {pt['file']}")
            text = row["text"]
            if sha(text) != pt["row_sha256"]:
                fail(f"{slug}: {pt['locus']} in {pt['file']} no longer matches "
                     f"the row this plan was measured against")
            a = pt.get("start", 0)
            b = pt.get("end", len(text))
            if a:
                check_cut(text, a, pt.get("at", ""), pt.get("prev_ends_with", ""),
                          f"{slug} start, {pt['locus']}")
            if b != len(text):
                check_cut(text, b, pt.get("after", ""), pt.get("ends_with", ""),
                          f"{slug} end, {pt['locus']}")
            if b <= a:
                fail(f"{slug}: {pt['locus']} end {b} not after start {a}")
            claimed.setdefault(key, []).append((a, b, slug))
            checks.append({"slug": slug, "file": pt["file"],
                           "locus": str(pt["locus"]), "start": a, "end": b,
                           "at": pt.get("at", ""),
                           "prev_ends_with": pt.get("prev_ends_with", ""),
                           "after": pt.get("after", ""),
                           "ends_with": pt.get("ends_with", "")})
            part = text[a:b].strip()
            if not part:
                continue
            if key not in merged:
                merged[key] = []
                order.append(key)
            merged[key].append(part)

        out = []
        for key in order:
            f, loc = key
            src = by_key[key]
            r = dict(src)
            r["urn"] = slug
            r["locus"] = loc if loc.startswith(f"{vol}.") else f"{vol}.{loc}"
            r["text"] = " ".join(merged[key])
            spans = [(a, b) for a, b, sl in claimed[key] if sl == slug]
            if spans != [(0, len(src["text"]))]:
                r["row_part"] = (
                    "characters " + ", ".join(f"{a}-{b}" for a, b in spans)
                    + f" of Migne {vol} page {loc.split('.')[-1]}, which prints "
                      f"more than one work"
                    + (" in interleaved columns" if len(spans) > 1 else ""))
            out.append(r)
        per_work[slug] = out

    residual: dict[str, list[dict]] = {}
    for f, rows in files.items():
        keep_rows = []
        for r in rows:
            key = (f, str(r["locus"]))
            spans = sorted(claimed.get(key, []))
            if not spans:
                keep_rows.append(r)
                continue
            prev, keep = 0, []
            for a, b, sl in spans:
                if a < prev:
                    fail(f"{r['locus']} in {f}: {sl} overlaps an earlier claim")
                keep.append(r["text"][prev:a])
                prev = b
            keep.append(r["text"][prev:])
            left = " ".join(" ".join(keep).split())
            if left:
                nr = dict(r)
                nr["text"] = left
                nr["row_part"] = (
                    f"the part of Migne {vol} page "
                    f"{str(r['locus']).split('.')[-1]} that no carved work claims; "
                    f"see data/corpus_changes/cogPG.{vol}.row-split.json")
                keep_rows.append(nr)
        residual[f] = keep_rows

    before = sum(n_tok(r["text"]) for rows in files.values() for r in rows)
    after = sum(n_tok(r["text"]) for rows in residual.values() for r in rows)
    after += sum(n_tok(r["text"]) for out in per_work.values() for r in out)
    if before != after:
        fail(f"token conservation across {len(files)} file(s): {before} in, "
             f"{after} out (delta {after - before}). A cut inside a Greek run "
             f"splits one token into two; every offset must sit at a whitespace "
             f"boundary.")
    return per_work, residual, {"checks": checks, "tokens": before,
                                "files": {f: sha((REPO / f).read_text(encoding="utf-8"))
                                          for f in files}}


def update_cgpg_works(vol: str, plan: dict, per_work: dict[str, list[dict]],
                      residual: dict[str, list[dict]]) -> None:
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
    # Every file this cut took text OUT of now holds fewer tokens, not just the
    # volume. Two of PG151's seams sat in rows an earlier carve had already
    # moved into work files, so those works shrank too; leaving their entries
    # alone is what `make check` caught.
    by_urn = {e.get("urn"): e for e in vols}
    for f, rows in residual.items():
        urn = f.split("/")[-1][:-len(".jsonl")]
        e = by_urn.get(urn)
        if e is None or urn == src_urn:
            continue
        e["n_passages"] = len(rows)
        e["n_tokens"] = sum(_ledger_tokens(r["text"]) for r in rows)

    vol_rows = residual.get(f"data/corpus/{src_urn}.jsonl", [])
    vol_entry["n_passages"] = len(vol_rows)
    vol_entry["n_tokens"] = sum(_ledger_tokens(r["text"]) for r in vol_rows)
    if not vol_rows:
        vol_entry["desc"] = (vol_entry["desc"].split(" (split per-work")[0]
                             .split(" (fully split per-work")[0]
                             + " (fully split per-work; the last rows were cut at "
                               "character offsets by scripts/split_carved_row.py "
                               "and the volume file removed)")
        vol_entry["works"] = []

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
    ap_fp = audit_path(vol)

    if args.unapply:
        if not ap_fp.exists():
            fail(f"no audit at {ap_fp.relative_to(REPO)}")
        rec = json.loads(ap_fp.read_text(encoding="utf-8"))

        # Refuse if anything has been applied on top of this pass. The audit
        # records what every file looked like when it was written; if a file has
        # moved since, restoring its archived rows silently reverses whatever
        # moved it, and nothing fails.
        #
        # That is not hypothetical. On 2026-08-09 unapplying PG118's split to add
        # four works to it also took the Oecumenius tail extension back out of the
        # volume file while its work file kept the rows, serving 70 tokens twice,
        # and resurrected loci 23-24 that the duplicate-leaf drop had removed,
        # 1,063 tokens. Both passed every check this tool had. They were caught
        # only by comparing the corpus total against the last tag.
        #
        # Unwind in LIFO order instead: reverse what was applied after this,
        # reverse this, then re-apply forwards.
        stale = []
        for f, rec_f in (rec.get("sources") or {}).items():
            want = rec_f.get("sha256_after")
            if want and (REPO / f).exists():
                got = sha((REPO / f).read_text(encoding="utf-8"))
                if got != want:
                    stale.append(f"{f} ({got[:12]} != {want[:12]})")
        for slug, blk in (rec.get("works") or {}).items():
            f = CORPUS / f"{slug}.jsonl"
            want = blk.get("sha256") if isinstance(blk, dict) else None
            if want and f.exists():
                got = sha(f.read_text(encoding="utf-8"))
                if got != want:
                    stale.append(f"{f.name} ({got[:12]} != {want[:12]})")
        if stale:
            fail("something has been applied on top of this pass, so unapplying "
                 "it would silently reverse that too. Reverse the later change "
                 "first, newest first, then this.\n  moved since this audit: "
                 + "\n                          ".join(stale))

        for slug in rec["works"]:
            f = CORPUS / f"{slug}.jsonl"
            if f.exists():
                f.unlink()
        # Restore every source file, then prove it. Two of PG151's four seams
        # sit in rows an earlier carve already moved into work files, so this
        # has to reverse edits to files another audit also records. Reversing
        # in the wrong order would leave both audits individually consistent
        # and the chain broken, which is why the restored bytes are hashed
        # against what was measured rather than assumed.
        srcs = rec.get("sources")
        if srcs is None:
            # An audit written before this tool grew multi-file support. It is
            # still a valid record and must still reverse: refusing to read it
            # would make a published change irreversible, which is the one
            # thing the audit exists to prevent.
            srcs = {rec["volume"]["file"]: {
                "sha256_before": rec["volume"]["sha256_before"],
                "original_rows": rec["original_rows"]}}
        for f, rec_f in srcs.items():
            write_rows(REPO / f, rec_f["original_rows"])
            got = sha((REPO / f).read_text(encoding="utf-8"))
            if got != rec_f["sha256_before"]:
                fail(f"unapply did not restore {f} byte-for-byte "
                     f"({got[:12]} != {rec_f['sha256_before'][:12]})")
        ap_fp.unlink()
        print(f"UNAPPLIED: {len(srcs)} source file(s) restored "
              f"byte-for-byte, {len(rec['works'])} work file(s) removed")
        return

    plan_all = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = next((v for v in plan_all["volumes"] if v["volume"] == vol), None)
    if plan is None:
        fail(f"no row-split plan entry for {vol}")
    if ap_fp.exists():
        fail(f"{ap_fp.relative_to(REPO)} already exists; --unapply first")

    originals = {f: read_rows(REPO / f)
                 for f in {pt["file"] for w in plan["works"] for pt in w["parts"]}}
    per_work, residual, meta = build(vol, plan)

    print(f"{vol}: {sum(len(v) for v in originals.values())} rows / "
          f"{meta['tokens']:,} greek tokens across {len(originals)} file(s) ->")
    for slug, out in per_work.items():
        print(f"      {slug}  {len(out)} rows  "
              f"{sum(n_tok(r['text']) for r in out):,} tok")
    for f, rows in residual.items():
        print(f"      keeps {f.split('/')[-1]}: {len(rows)} rows / "
              f"{sum(n_tok(r['text']) for r in rows):,} tok")
    if not args.apply:
        print("CHECK only (pass --apply to write)")
        return

    for slug, out in per_work.items():
        f = CORPUS / f"{slug}.jsonl"
        if f.exists():
            fail(f"{f.relative_to(REPO)} already exists")
        write_rows(f, out)
    for f, rows in residual.items():
        if rows:
            write_rows(REPO / f, rows)
        else:
            # Every row claimed: the volume is fully carved and an empty
            # corpus file would be a served work with no text. carve_cgpg_
            # volume.py removes the file in the same situation; unapply
            # recreates it from this audit's original_rows.
            (REPO / f).unlink()
    update_cgpg_works(vol, plan, per_work, residual)

    ap_fp.write_text(json.dumps({
        "_meta": {
            "what": f"rows of {vol} cut at a character offset so works whose "
                    f"boundary falls inside a row can be served",
            "date": plan["date"],
            "issue": "open-greek/open-greek-corpus#8",
            "tool": "scripts/split_carved_row.py",
            "reverse": f"python3 scripts/split_carved_row.py --volume {vol} --unapply",
            "ordering": "reverse this BEFORE the per-work-split audit of any file "
                        "listed under `sources`: this record's `original_rows` are "
                        "that carve's output, not the volume's original text.",
            "basis": plan.get("basis", ""),
        },
        "sources": {f: {
            "sha256_before": meta["files"][f],
            "sha256_after": (sha((REPO / f).read_text(encoding="utf-8"))
                             if (REPO / f).exists() else None),
            "removed": not (REPO / f).exists(),
            "rows_before": len(originals[f]),
            "rows_after": len(residual[f]),
            "original_rows": originals[f],
        } for f in originals},
        "works": {slug: {
            "file": f"data/corpus/{slug}.jsonl",
            "rows": len(out),
            "greek_tokens": sum(n_tok(r["text"]) for r in out),
            "sha256": sha((CORPUS / f"{slug}.jsonl").read_text(encoding="utf-8")),
        } for slug, out in per_work.items()},
        "boundary_checks": meta["checks"],
        "token_conservation": {
            "original": meta["tokens"],
            "check": "sum over every work file and every source's remainder == "
                     "original (exact, _GK), across all source files together",
        },
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"APPLIED: {len(per_work)} work files, {len(residual)} source file(s) "
          f"rewritten, audit {ap_fp.relative_to(REPO)}")


if __name__ == "__main__":
    main()
