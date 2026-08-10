#!/usr/bin/env python3
"""Where the OCR read one printed page more than once, serve one read and keep
the rest as witnesses.

The byte-identical case was handled by drop_duplicate_page.py, where there is no
reading to choose. This is the harder class: the reads differ, so one has to be
picked, and the loser is a genuine variant rather than redundant text. Cisco's
rule, 2026-08-09: nothing is served twice, one best primary is picked, and the
other reading stays available but outside the counts. So losers MOVE to
data/corpus_secondary as witnesses; nothing is deleted.

HOW THE WINNER IS PICKED, and why not the obvious things. Ranked by net attested
tokens, attested minus unattested, against the same attestation set
build_ocr_quality_report.py uses. Validated against an independent referee that
aligns the two token streams, looks only at the blocks where they read the SAME
word differently, and scores attested minus unattested on each side: net agrees
with it on 90.3% of the pairs it can decide, against 88.9% for raw attested
count, 61.6% for the illegal-accent rate, 53.0% for length and 44.2% for the
junk-token rate, which is worse than a coin flip. Length and quality are nearly
opposite (they disagree on 53% of pairs), so the choice is not cosmetic.

THREE THINGS THAT LOOK LIKE DETAILS AND ARE NOT.

Elision apostrophes are normalized before anything else. Whichever read happens
to spell ἀλλ' with a right single quote loses every elided form, because it
tokenizes to a 3-character fragment below the length floor while ἀλλ᾽ is checked
and attested. Pure typography, and it flipped 10 of 725 verdicts.

The decision is per GROUP, not per pair: pages are gathered into connected
components and exactly one winner is kept per component. One page in Aeneas
Gazaeus was read seven times, another in Themistius five, and 64 groups have
three or more members; pairwise verdicts on a seven-clique are incoherent.

Only same-item pairs. Two reads of one page is an OCR question; the same passage
in two printed editions (Diels VS1 against FVS2, inside one testimonia file) is a
precedence question and is left alone.

WHAT STOPS IT LOSING TEXT. Containment is a bag-of-words test and passes happily
on a read that shattered a page into out-of-order fragments, where the two reads
are complementary rather than redundant and collapsing them would lose the page.
So every displacement must also clear a post-condition against the chosen
winner: at least 60% of the loser's tokens inside runs of 5+ tokens shared with
the winner, and at most MAX_ATTESTED_LOSS attested tokens present in the loser
and absent from the winner. A page that fails stays primary and is reported. At
the 0.80 cut that holds back 21 of 327 pages and cuts the attested loss from
3,527 to 2,993, and both numbers go in the audit rather than going unsaid.

  python3 scripts/collapse_duplicate_reads.py
  python3 scripts/collapse_duplicate_reads.py --apply
  python3 scripts/collapse_duplicate_reads.py --unapply
"""

from __future__ import annotations

import argparse
import collections
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
SECONDARY = DATA / "corpus_secondary"
CANDIDATES = DATA / "duplicate_page_candidates.json"
AUDIT = DATA / "corpus_changes" / "ocr.duplicate-read-collapse.json"
# A later pass names itself, so it writes its own audit and its own witness
# files instead of refusing because the first pass's audit exists. Writing one
# audit over another would destroy the earlier pass's reconstruction record
# while appearing to succeed, which is the same reason carve_cgpg_volume.py
# takes --pass. Each pass stays independently reversible, newest first.
WITNESS_SUFFIX = "duplicate-read"

GATE = 0.80              # containment below this is not collapsed at all
MIN_SHARED_RUN_MASS = 0.60
MAX_ATTESTED_LOSS = 20
RUN = 5                  # tokens; a "shared run" is at least this long

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402
from build_ocr_quality_report import (  # noqa: E402
    build_attestation, greek_tokens, MIN_SUSPECT_LEN)
from drop_duplicate_page import PAGE  # noqa: E402

APOS = re.compile(r"(?<=[Ͱ-Ͽἀ-῿])['’ʼ‘´΄]")


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def norm_elision(s: str) -> str:
    """Apostrophe after a Greek letter -> koronis. Typography, not text."""
    return APOS.sub("᾽", s)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def score(text: str, attested: set) -> dict:
    toks = greek_tokens(norm_elision(text))
    checked = [t for t in toks if len(t) >= MIN_SUSPECT_LEN and not t.isupper()]
    un = [t for t in checked if t not in attested]
    return {"tokens": len(toks), "checked": len(checked), "unattested": len(un),
            "net": len(checked) - 2 * len(un),
            "unattested_rate": round(len(un) / len(checked), 6) if checked else 1.0}


def shared_run_mass(loser: str, winner: str) -> float:
    """Fraction of the loser's tokens inside runs of RUN+ tokens shared with the
    winner. Containment alone passes on a page shattered into out-of-order
    fragments; requiring shared RUNS is what distinguishes a second reading of a
    page from a complementary half of it."""
    a = greek_tokens(norm_elision(loser))
    b = greek_tokens(norm_elision(winner))
    if not a:
        return 1.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    inside = sum(n for _, _, n in sm.get_matching_blocks() if n >= RUN)
    return inside / len(a)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unapply", action="store_true")
    ap.add_argument("--gate", type=float, default=GATE)
    ap.add_argument("--id", default=None,
                    help="name this pass; it writes <id>.duplicate-read-collapse"
                         ".json and its own witness files, leaving an earlier "
                         "pass's audit and witnesses intact")
    args = ap.parse_args()
    if args.id:
        globals()["AUDIT"] = (DATA / "corpus_changes"
                              / f"{args.id}.duplicate-read-collapse.json")
        globals()["WITNESS_SUFFIX"] = f"duplicate-read-{args.id}"

    if args.unapply:
        if not AUDIT.exists():
            fail(f"no audit at {AUDIT.relative_to(REPO)}")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        for f, blk in rec["files"].items():
            rows = [json.loads(l) for l in
                    (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()]
            # Re-insert each removed row at the index it came from, lowest first,
            # so the surrounding rows keep their positions.
            for e in sorted(blk["removed_rows"], key=lambda e: e["index"]):
                rows.insert(e["index"], e["row"])
            (REPO / f).write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n"
                        for r in rows), encoding="utf-8")
            if sha((REPO / f).read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {f} byte-for-byte")
        for f in rec["witness_files_written"]:
            if (REPO / f).exists():
                (REPO / f).unlink()
        AUDIT.unlink()
        print(f"UNAPPLIED: {len(rec['files'])} file(s) restored byte-for-byte, "
              f"{len(rec['witness_files_written'])} witness file(s) removed")
        return

    cand = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    # Two ways in, and the second one is why this pass exists. A pair clears on
    # containment as before, OR it belongs to a leaf-run: consecutive pages
    # repeating at a fixed offset inside one scan item, which the sweep detects
    # from position rather than from wording. The run is what catches a second
    # read the scanner garbled differently: Nicetas' page 504 reads Ἐπηγγέλατο
    # in one copy and Ἐπηγεμῶτο in the other, and enough of the page goes that
    # way to hold the score under any gate a single pair could safely use.
    #
    # This widens what is CONSIDERED and nothing else. The winner rule, the
    # shared-run-mass floor and the attested-loss cap are untouched, so a run
    # member that cannot be shown to be a repetition of the page that beat it is
    # held back exactly like any other.
    pairs = [h for h in cand["pairs"]
             if h["served"]
             and (h["containment"] >= args.gate or h.get("run"))
             and h["locus_a"].rsplit("_", 1)[0] == h["locus_b"].rsplit("_", 1)[0]]
    # Both pages must live in the file the pair names. This tool resolves a
    # locus to text through that one file, so a pair whose two pages sit in
    # different files would look up the absent one, get "", and then sail
    # through every post-condition: shared_run_mass returns 1.0 on an empty
    # loser by its own guard at the top, and the attested-loss list is empty
    # because there are no tokens to lose. The result is an audited
    # displacement that removes nothing, in the one script here allowed to take
    # rows out of the served corpus.
    #
    # The sweep does not emit cross-file pairs today, because it compares rows
    # inside one file. 90 of the 244 served scan items are carved across more
    # than one file, so widening it to see them is real work that is wanted;
    # this is the guard that has to exist first. A cross-file duplicate is also
    # not this tool's decision: it means two WORKS carry the same page, which is
    # an attribution question, not a choice between two readings.
    dropped = []
    for f in {h["file"] for h in pairs}:
        keys = set()
        for line in (REPO / f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                m = PAGE.match(str(json.loads(line)["locus"]))
                if m:
                    keys.add(m.group(1))
        for h in [x for x in pairs if x["file"] == f]:
            if h["locus_a"] not in keys or h["locus_b"] not in keys:
                dropped.append(h)
    if dropped:
        pairs = [h for h in pairs if h not in dropped]
        print(f"  refused {len(dropped)} pair(s) whose pages are not both in the "
              f"file named: this tool cannot displace across files")

    by_run = len([h for h in pairs if h["containment"] < args.gate])
    print(f"pairs served, same item: {len(pairs)} "
          f"({len(pairs) - by_run} at containment >= {args.gate}, "
          f"{by_run} admitted on a leaf-run below it)")

    # connected components per file
    per_file: dict[str, list] = collections.defaultdict(list)
    for h in pairs:
        per_file[h["file"]].append(h)

    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions["works"] if "works" in editions else editions
    attested, att_stats = build_attestation(editions)
    print(f"attestation: {att_stats['n_unique_forms']:,} forms from "
          f"{att_stats['n_works']:,} non-OCR works")

    plans, held = [], []
    for f, hs in sorted(per_file.items()):
        rows = [json.loads(l) for l in (REPO / f).read_text(encoding="utf-8").splitlines()
                if l.strip()]
        pages: dict[str, list] = collections.defaultdict(list)
        for r in rows:
            m = PAGE.match(str(r["locus"]))
            if m:
                pages[m.group(1)].append(r)
        parent: dict[str, str] = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for h in hs:
            a, b = find(h["locus_a"]), find(h["locus_b"])
            if a != b:
                parent[a] = b
        groups: dict[str, list] = collections.defaultdict(list)
        for k in list(parent):
            groups[find(k)].append(k)

        for g in groups.values():
            g = sorted(set(g))
            texts = {k: " ".join(r.get("text") or "" for r in pages[k]) for k in g}
            sc = {k: score(t, attested) for k, t in texts.items()}
            win = sorted(g, key=lambda k: (-sc[k]["net"], sc[k]["unattested_rate"],
                                           -sc[k]["tokens"], k))[0]
            for k in g:
                if k == win:
                    continue
                mass = shared_run_mass(texts[k], texts[win])
                wt = set(greek_tokens(norm_elision(texts[win])))
                lost = [t for t in greek_tokens(norm_elision(texts[k]))
                        if t in attested and t not in wt]
                rec = {"file": f, "keep": win, "displace": k,
                       "keep_net": sc[win]["net"], "displaced_net": sc[k]["net"],
                       "shared_run_mass": round(mass, 4),
                       "attested_tokens_lost": len(lost),
                       "greek_tokens": len(_GK.findall(texts[k])),
                       "rows": len(pages[k]),
                       "group_size": len(g)}
                if mass < MIN_SHARED_RUN_MASS or len(lost) > MAX_ATTESTED_LOSS:
                    rec["held_back"] = (
                        f"shared-run mass {mass:.2f} < {MIN_SHARED_RUN_MASS}"
                        if mass < MIN_SHARED_RUN_MASS else
                        f"{len(lost)} attested tokens absent from the kept read "
                        f"(limit {MAX_ATTESTED_LOSS})")
                    held.append(rec)
                else:
                    plans.append(rec)

    tot = sum(p["greek_tokens"] for p in plans)
    print(f"groups resolved; {len(plans)} pages displace, {tot:,} tokens leave the "
          f"served count; {len(held)} held back by the post-condition")
    print(f"  attested tokens the kept reads lack: {sum(p['attested_tokens_lost'] for p in plans):,} "
          f"across the displaced pages")
    for h in held[:6]:
        print(f"    HELD {h['file'].split('/')[-1][:38]:<38} {h['displace']}: {h['held_back']}")
    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")

    files, written = {}, []
    by_file: dict[str, list] = collections.defaultdict(list)
    for p in plans:
        by_file[p["file"]].append(p)
    for f, ps in sorted(by_file.items()):
        fp = REPO / f
        rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        drop = {p["displace"] for p in ps}
        keep, moved = [], []
        for r in rows:
            m = PAGE.match(str(r["locus"]))
            (moved if (m and m.group(1) in drop) else keep).append(r)
        # A DEEP copy for the audit. The witness rows below get rank and
        # secondary_reason stamped onto them, and those are the same dict
        # objects, so storing them by reference made --unapply write the
        # mutated rows back and fail its own byte-for-byte check. The round
        # trip caught it; nothing else would have.
        # Only the rows that MOVE, with the index they sat at, never the whole
        # file. Archiving every row of every touched file made this record 119 MB
        # and GitHub refused the push; it was also redundant, since the witness
        # file holds those rows and the rest of the file did not change.
        moved_idx = []
        for i, r in enumerate(rows):
            m = PAGE.match(str(r["locus"]))
            if m and m.group(1) in drop:
                moved_idx.append(i)
        files[f] = {"sha256_before": sha(fp.read_text(encoding="utf-8")),
                    "rows_before": len(rows), "rows_after": len(keep),
                    "removed_rows": [{"index": i, "row": dict(rows[i])}
                                     for i in moved_idx]}
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep),
                      encoding="utf-8")
        files[f]["sha256_after"] = sha(fp.read_text(encoding="utf-8"))

        slug = fp.name[:-len(".jsonl")]
        wfp = SECONDARY / f"{slug}.{WITNESS_SUFFIX}.jsonl"
        moved = [dict(r) for r in moved]
        for r in moved:
            r["rank"] = "secondary"
            r["secondary_reason"] = (
                "a second OCR reading of a page this work already serves; the "
                "read with more attested and fewer unattested tokens was kept "
                "primary and this one is preserved out of the served counts "
                "(cisco's rule, 2026-08-09; scripts/collapse_duplicate_reads.py)")
        wfp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in moved),
                       encoding="utf-8")
        written.append(wfp.relative_to(REPO).as_posix())

    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "second OCR readings of pages already served, moved to "
                    "witnesses so no text is served twice",
            "date": "2026-08-09",
            "issue": "open-greek/open-greek-corpus#33",
            "tool": "scripts/collapse_duplicate_reads.py",
            "reverse": "python3 scripts/collapse_duplicate_reads.py --unapply",
            "criterion": "net attested tokens (attested minus unattested) after "
                         "elision-apostrophe normalization, decided per connected "
                         "component, same scan item only, containment gate "
                         f"{args.gate}",
        },
        "gate": args.gate,
        "attestation": att_stats,
        "pages_displaced": len(plans),
        "greek_tokens_displaced": tot,
        "attested_tokens_absent_from_kept_reads": sum(
            p["attested_tokens_lost"] for p in plans),
        "held_back": held,
        "displacements": plans,
        "witness_files_written": written,
        "files": files,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {len(plans)} pages -> {len(written)} witness files, "
          f"audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
