#!/usr/bin/env python3
"""Drop scan pages the line-level OCR delivered more than once.

data/duplicate_leaf_candidates.json only ever looked at the `cgpg` source, where
a printed page is one row. The `ocr` source is 1.35M rows against cgpg's 11k and
keys its loci `<item>_<page>.<line>`, so the same accident there is a duplicated
RUN of rows, and my own sweep said so and then never checked. It should have:
64 pages are in the served corpus twice or more, byte for byte, 16,205 tokens,
counted into public_lexicon.tsv, coverage.json and the released total. The
upstream pipeline has a collapse for this (`pages_skipped_collapsed` in
data/ocr_works.json) and it reads 0 on every affected work, so it never fired.

Only the BYTE-IDENTICAL class moves here, and that is the whole design. When two
pages differ, they are two readings of one page, and this repo's rule is to
prefer a merged reading over picking a winner, so deleting the loser would be a
disposition question rather than a defect fix. When they are identical there is
no reading to choose and the file itself is the evidence: the tool refuses
unless the two joined page texts hash the same.

Deduplication is per file. A scan page's rows can be split across two works, and
each file is judged on its own bytes, so one file can shed a page while another
keeps its slice; the audit records which files an item's page touches.

  python3 scripts/drop_duplicate_page.py --plan
  python3 scripts/drop_duplicate_page.py --apply
  python3 scripts/drop_duplicate_page.py --unapply
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
PLAN = DATA / "duplicate_pages.json"
AUDIT = DATA / "corpus_changes" / "ocr.duplicate-page.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from carve_cgpg_volume import greek_tokens as _ledger_tokens  # noqa: E402

# A page locus, and nothing else. 229 served ocr files use citation loci ("3.2",
# a bare "1"); reading "3" as a page there would compare whole books and could
# authorize deleting real text, so a file whose loci do not all match this shape
# is skipped entirely rather than partially.
PAGE = re.compile(r"^(.*_\d{2,})\.\d+$")
MIN_TOKENS = 20


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def pages_of(fp: Path):
    """{page key: [rows]} for a served ocr file, or None if it is not one."""
    rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    if not rows or any(r.get("source") != "ocr" for r in rows):
        return None
    out: dict[str, list] = collections.defaultdict(list)
    for r in rows:
        m = PAGE.match(str(r["locus"]))
        if not m:
            return None
        out[m.group(1)].append(r)
    return out


def find() -> list[dict]:
    hits = []
    for fp in sorted(CORPUS.glob("*.jsonl")):
        pages = pages_of(fp)
        if not pages or len(pages) < 2:
            continue
        first: dict[str, str] = {}
        for key, rows in pages.items():
            text = " ".join(r.get("text") or "" for r in rows)
            n = len(_GK.findall(text))
            if n < MIN_TOKENS:
                continue
            h = sha(text)
            if h in first:
                hits.append({
                    "file": fp.relative_to(REPO).as_posix(),
                    "item": key.rsplit("_", 1)[0],
                    "keep_page": first[h], "drop_page": key,
                    "page_sha256": h,
                    "rows": len(rows),
                    "greek_tokens": n,
                })
            else:
                first[h] = key
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="write the plan file")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    if args.unapply:
        if not AUDIT.exists():
            fail(f"no audit at {AUDIT.relative_to(REPO)}")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for f, blk in rec["files"].items():
            (REPO / f).write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n"
                        for r in blk["original_rows"]), encoding="utf-8")
            got = sha((REPO / f).read_text(encoding="utf-8"))
            if got != blk["sha256_before"]:
                fail(f"unapply did not restore {f} byte-for-byte")
        AUDIT.unlink()
        print(f"UNAPPLIED: {len(rec['files'])} file(s) restored byte-for-byte")
        return

    hits = find()
    by_file = collections.Counter(h["file"] for h in hits)
    tot = sum(h["greek_tokens"] for h in hits)
    print(f"byte-identical duplicate pages in served ocr files: {len(hits)}, "
          f"{sum(h['rows'] for h in hits):,} rows, {tot:,} greek tokens, "
          f"{len(by_file)} files")
    for h in hits[:12]:
        print(f"    {h['file'].split('/')[-1][:44]:<44} {h['drop_page']} "
              f"= {h['keep_page']}  {h['greek_tokens']:>5} tok")
    if len(hits) > 12:
        print(f"    ... {len(hits) - 12} more")

    if args.plan:
        # Every file an item's duplicated page touches, so a reader can see when
        # one work sheds a page while a sibling work keeps its slice.
        touch: dict[str, set] = collections.defaultdict(set)
        for h in hits:
            touch[f"{h['item']}/{h['drop_page']}"].add(h["file"])
        PLAN.write_text(json.dumps({
            "what": "scan pages the line-level OCR delivered more than once, "
                    "byte for byte, inside a single served work",
            "issue": "open-greek/open-greek-corpus#33",
            "rule": "only byte-identical pages are listed. Two pages that differ "
                    "are two readings of one page, and this repo prefers a merged "
                    "reading to picking a winner, so those are a disposition "
                    "question and are not here.",
            "min_greek_tokens": MIN_TOKENS,
            "pages": len(hits), "greek_tokens": tot,
            "drops": hits,
            "pages_touching_more_than_one_file": {
                k: sorted(v) for k, v in touch.items() if len(v) > 1},
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {PLAN.relative_to(REPO)}")
        return
    if not args.apply:
        print("\nCHECK only (pass --plan to record, --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")
    if not PLAN.exists():
        fail(f"{PLAN.relative_to(REPO)} does not exist; run --plan first")

    planned = {(d["file"], d["drop_page"]): d
               for d in json.loads(PLAN.read_text(encoding="utf-8"))["drops"]}
    files: dict[str, dict] = {}
    for h in hits:
        k = (h["file"], h["drop_page"])
        if k not in planned:
            fail(f"{h['file']} {h['drop_page']} is not in the plan")
        if planned[k]["page_sha256"] != h["page_sha256"]:
            fail(f"{h['file']} {h['drop_page']}: page text no longer matches "
                 f"the plan it was measured against")
    for f in sorted({h["file"] for h in hits}):
        fp = REPO / f
        rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        drop = {h["drop_page"] for h in hits if h["file"] == f}
        keep = [r for r in rows
                if (PAGE.match(str(r["locus"])).group(1) not in drop)]
        files[f] = {"sha256_before": sha(fp.read_text(encoding="utf-8")),
                    "rows_before": len(rows), "rows_after": len(keep),
                    "dropped_pages": sorted(drop),
                    "original_rows": rows}
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in keep), encoding="utf-8")
        files[f]["sha256_after"] = sha(fp.read_text(encoding="utf-8"))

    # data/ocr_works.json is compared against corpus_editions by `make check`,
    # which fails the build on drift, so the ledger moves in the same step. Its
    # counts use the whitespace-split metric that file is keyed on, not _GK.
    lp = DATA / "ocr_works.json"
    led = json.loads(lp.read_text(encoding="utf-8"))
    entries = led if isinstance(led, list) else led.get("works", led)
    seq = entries if isinstance(entries, list) else list(entries.values())
    touched = {f.split("/")[-1][:-len(".jsonl")] for f in files}
    for e in seq:
        if e.get("urn") in touched:
            fp = CORPUS / f"{e['urn']}.jsonl"
            rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
            e["n_passages"] = len(rows)
            e["n_tokens"] = sum(_ledger_tokens(r.get("text") or "") for r in rows)
    lp.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")

    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "scan pages the OCR delivered more than once, byte for byte, "
                    "removed from the served corpus",
            "issue": "open-greek/open-greek-corpus#33",
            "tool": "scripts/drop_duplicate_page.py",
            "reverse": "python3 scripts/drop_duplicate_page.py --unapply",
            "note": "the removed tokens were counted twice before, so the served "
                    "total falls and gets more correct at once. Only pages whose "
                    "text hashes identically to a page already in the same file "
                    "are removed, so no reading was chosen.",
        },
        "pages_dropped": len(hits),
        "greek_tokens_dropped": tot,
        "drops": hits,
        "files": files,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {len(hits)} pages, {tot:,} tokens, "
          f"audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
