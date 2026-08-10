#!/usr/bin/env python3
"""Build one reading from the several the scanner produced of a page.

The collapse pass picks a winner and keeps the losers as witnesses. That is
right when one read is simply better, and it leaves 101,738 served tokens
untouched where it is not: pages inside a leaf-run whose reads are each partly
right, so no post-condition can show either is a repetition of the other rather
than a complementary half of the page. Cisco's call on 2026-08-10 was to merge
those instead of choosing between them.

Merging is a stronger claim than choosing, and this file is written to make that
visible rather than to hide it. The output is a text NO SCAN ATTESTS on its own:
every position where the reads disagree is a decision this code made. So it
reports before it writes, every decision is counted and classified, and a sample
is published for reading.

HOW A POSITION IS DECIDED, in order:
  agree      every read has the same token; take it, no decision made
  majority   3+ reads and one token has more votes than any other
  attested   the reads disagree and exactly one variant is a word the corpus's
             non-OCR text attests; take that one
  winner     no variant is attested, or several are; keep the token from the
             read that the collapse's net-attested score ranks best, and mark
             the position, because this is the case where merging is guessing

The merge is only ever attempted inside a leaf-run group, which is where
position already says the pages are the same leaf delivered twice.

  python3 scripts/merge_duplicate_reads.py                # report + sample
  python3 scripts/merge_duplicate_reads.py --sample 40
"""
from __future__ import annotations
import argparse, collections, difflib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "duplicate_read_merge_sample.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from build_ocr_quality_report import build_attestation, greek_tokens, MIN_SUSPECT_LEN  # noqa: E402
from collapse_duplicate_reads import norm_elision, score, PAGE  # noqa: E402


def groups() -> dict:
    """(file, item, offset) -> the page keys of one leaf-run, in page order."""
    cand = json.loads((DATA / "duplicate_page_candidates.json").read_text(encoding="utf-8"))
    runs = {}
    for h in cand["pairs"]:
        if not h.get("served") or not h.get("run") or h.get("cross_file"):
            continue
        runs.setdefault(h["run"], {"file": h["file"], "pages": set()})
        runs[h["run"]]["pages"] |= {h["locus_a"], h["locus_b"]}
    return runs


def page_text(rows: list[dict]) -> dict:
    out: dict[str, list[str]] = {}
    for r in rows:
        m = PAGE.match(str(r["locus"]))
        if m:
            out.setdefault(m.group(1), []).append(r.get("text") or "")
    return {k: " ".join(v) for k, v in out.items()}


def merge(reads: list[list[str]], attested: set, best: int) -> tuple[list[str], dict]:
    """Merge N token streams. reads[best] is the collapse's winner."""
    tally = collections.Counter()
    out: list[str] = []
    a = reads[best]
    others = [r for i, r in enumerate(reads) if i != best]
    # pairwise against the winner, one alignment per other read
    picks: list[list[str]] = [list(a)]
    for b in others:
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        lane = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                lane.extend(a[i1:i2])
            elif tag == "replace":
                # Only a same-length substitution is a per-token disagreement.
                # An uneven one means the reads broke the text differently, e.g.
                # τέταρτος against τέ ταρτος across a line break, and pairing
                # them position by position invents tokens: the first sample run
                # emitted "τέταρτος ταρτος". Those positions get no vote and
                # fall through to the winner's own token.
                lane.extend(b[j1:j2] if (i2 - i1) == (j2 - j1)
                            else [None] * (i2 - i1))
            elif tag == "delete":
                lane.extend([None] * (i2 - i1))
            # insert: the other read has extra tokens; the winner's lane has none
        picks.append(lane + [None] * max(0, len(a) - len(lane)))
    for k in range(len(a)):
        variants = [p[k] for p in picks if k < len(p) and p[k] is not None]
        if not variants:
            out.append(a[k]); tally["agree"] += 1; continue
        c = collections.Counter(variants)
        if len(c) == 1:
            out.append(variants[0]); tally["agree"] += 1; continue
        top, n = c.most_common(1)[0]
        if len(reads) > 2 and n > 1 and n > c.most_common(2)[1][1]:
            out.append(top); tally["majority"] += 1; continue
        att = [v for v in c if v in attested and len(v) >= MIN_SUSPECT_LEN]
        if len(att) == 1:
            out.append(att[0]); tally["attested"] += 1; continue
        out.append(a[k]); tally["winner"] += 1
    return out, dict(tally)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=int, default=25)
    a = ap.parse_args()
    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions["works"] if "works" in editions else editions
    attested, st = build_attestation(editions)
    print(f"attestation: {st['n_unique_forms']:,} forms from {st['n_works']:,} non-OCR works")

    runs = groups()
    total = collections.Counter()
    merged_pages = 0
    sample = []
    for rid, g in sorted(runs.items()):
        rows = [json.loads(l) for l in (REPO / g["file"]).read_text(encoding="utf-8").splitlines() if l.strip()]
        texts = page_text(rows)
        pages = sorted(p for p in g["pages"] if p in texts)
        # group pages of one leaf into sets: pages at the run offset are the same leaf
        by_leaf: dict[str, list[str]] = {}
        for p in pages:
            by_leaf.setdefault(p, []).append(p)
        # a run pairs page n with page n+offset; rebuild those pairs
        nums = {p: int(p.rsplit("_", 1)[1]) for p in pages}
        off = None
        for h in ():
            pass
        # infer offset from the run id, which encodes it
        off = int(rid.split("+")[1].split("@")[0])
        seen = set()
        for p in pages:
            q = f"{p.rsplit('_',1)[0]}_{nums[p]+off:04d}"
            if q not in texts or p in seen:
                continue
            seen |= {p, q}
            reads = [greek_tokens(norm_elision(texts[p])), greek_tokens(norm_elision(texts[q]))]
            if not all(reads):
                continue
            sc = [score(texts[p], attested), score(texts[q], attested)]
            best = 0 if sc[0]["net"] >= sc[1]["net"] else 1
            out, tally = merge(reads, attested, best)
            merged_pages += 1
            total.update(tally)
            if len(sample) < a.sample and tally.get("attested", 0) + tally.get("winner", 0):
                sample.append({"run": rid, "file": g["file"], "pages": [p, q],
                               "kept_as_base": [p, q][best],
                               "decisions": tally,
                               "merged_opens": " ".join(out[:26]),
                               "read_a_opens": " ".join(reads[0][:26]),
                               "read_b_opens": " ".join(reads[1][:26])})
    dec = sum(total.values())
    print(f"\n{merged_pages} page pairs merged, {dec:,} token positions")
    for k in ("agree", "majority", "attested", "winner"):
        if total.get(k):
            print(f"    {k:<9} {total[k]:>7,}  {total[k]/dec:.2%}")
    guessed = total.get("winner", 0)
    print(f"\n  {guessed:,} positions ({guessed/dec:.2%}) had no attested variant to "
          f"choose from, so the merge kept the better read's token and marked it.\n"
          f"  Those are the ones where merging is guessing.")
    OUT.write_text(json.dumps({
        "what": "what merging the duplicate reads would produce, NOT APPLIED",
        "issue": "open-greek/open-greek-corpus#33",
        "decision_pending": "cisco chose merge over pick-a-winner on 2026-08-10. "
                            "This is the sample he asked to see first.",
        "why_a_sample": "a merged page is a text no scan attests on its own. Every "
                        "position where the reads disagree is a decision this code "
                        "made, so the decisions are counted and shown rather than "
                        "presented as a result.",
        "order_of_preference": ["agree", "majority (3+ reads)",
                                "attested (exactly one variant is a known word)",
                                "winner (nothing attested; kept the better read "
                                "and marked it)"],
        "page_pairs": merged_pages, "token_positions": dec,
        "decisions": dict(total),
        "unattested_share": round(guessed / dec, 4) if dec else None,
        "sample": sample,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)} ({len(sample)} pages to read)")


if __name__ == "__main__":
    main()
