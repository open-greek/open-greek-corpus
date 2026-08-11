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

WHAT --apply WRITES. Not the merged token stream: that would throw away the
punctuation, the non-Greek text and the row structure, since the stream is only
the Greek tokens of a page joined end to end. The merge is applied as token
SUBSTITUTIONS into the base page's own rows, at the offsets its tokens already
sit at, so everything the merge did not decide is left byte-identical. The other
read then MOVES to data/corpus_secondary as a witness, which is what stops the
page being served and counted twice, and is the whole of issue #33.

Every position the merge guessed is written down three times over: in the audit
with both readings, in data/duplicate_read_merge_guesses.json for reading, and
as a count on the served row itself, so text nobody's scan attests cannot be
mistaken for text some scan did.

  python3 scripts/merge_duplicate_reads.py                # report + sample
  python3 scripts/merge_duplicate_reads.py --sample 40
  python3 scripts/merge_duplicate_reads.py --apply
  python3 scripts/merge_duplicate_reads.py --unapply
"""
from __future__ import annotations
import argparse, collections, datetime as dt, difflib, hashlib, json, sys
import unicodedata
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "duplicate_read_merge_sample.json"
GUESSES = DATA / "duplicate_read_merge_guesses.json"
SECONDARY = DATA / "corpus_secondary"
AUDIT = DATA / "corpus_changes" / "ocr.duplicate-read-merge.json"
WITNESS_SUFFIX = "duplicate-read-merged"
sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")
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


def page_spans(rows: list[dict]) -> dict:
    """page -> [(row index, start, end, NFC token)], in reading order.

    The same token stream page_text feeds the merge, but carrying where each
    token physically sits so a decision can be written back without rebuilding
    the row. Elision normalization is a one-character substitution, so it moves
    no offset; it only changes whether a trailing apostrophe joins the token,
    which is exactly the comparison the merge wants and no business of the
    stored text. tests/test_duplicate_read_merge.py asserts this stream is
    token-for-token what page_text produces.
    """
    out: dict[str, list] = {}
    for i, r in enumerate(rows):
        m = PAGE.match(str(r["locus"]))
        if not m:
            continue
        norm = norm_elision(r.get("text") or "")
        out.setdefault(m.group(1), []).extend(
            (i, mm.start(), mm.end(), unicodedata.normalize("NFC", mm.group()))
            for mm in _GK.finditer(norm))
    return out


def apply_subs(text: str, subs: list) -> str:
    """subs are (start, end, replacement) at offsets into THIS text."""
    out, prev = [], 0
    for start, end, new in sorted(subs):
        if start < prev:
            fail(f"overlapping substitutions at {start}")
        out.append(text[prev:start]); out.append(new); prev = end
    return "".join(out) + text[prev:]


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
    how: list[tuple[str, list]] = []
    for k in range(len(a)):
        variants = [p[k] for p in picks if k < len(p) and p[k] is not None]
        if not variants:
            out.append(a[k]); tally["agree"] += 1; how.append(("agree", [])); continue
        c = collections.Counter(variants)
        if len(c) == 1:
            out.append(variants[0]); tally["agree"] += 1; how.append(("agree", [])); continue
        top, n = c.most_common(1)[0]
        if len(reads) > 2 and n > 1 and n > c.most_common(2)[1][1]:
            out.append(top); tally["majority"] += 1
            how.append(("majority", sorted(c))); continue
        att = [v for v in c if v in attested and len(v) >= MIN_SUSPECT_LEN]
        if len(att) == 1:
            out.append(att[0]); tally["attested"] += 1
            how.append(("attested", sorted(c))); continue
        out.append(a[k]); tally["winner"] += 1
        how.append(("winner", sorted(c)))
    return out, dict(tally), how


def components(pairs: list[tuple[str, str]]) -> list[list[str]]:
    """Connected components over the leaf-run pairs of one file.

    Runs OVERLAP. Himerius' page 590 heads two of them (+16 and +24), and 61 of
    the pages here sit in more than one pair; one page is the base of one pair
    and the read displaced by another. Deciding pair by pair then writing the
    results into the same rows gave two different answers for one token and the
    apply refused itself. So the unit is the component, exactly as
    collapse_duplicate_reads.py already decides its winners: every read of one
    printed page is merged into a single base, and every other member of the
    component is displaced.
    """
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    out: dict[str, list[str]] = {}
    for x in parent:
        out.setdefault(find(x), []).append(x)
    return [sorted(v) for v in out.values() if len(v) > 1]


def plan(attested: set) -> list[dict]:
    """One entry per printed page read more than once: what the merge decided
    and where each decision physically sits."""
    pairs_by_file: dict[str, list] = collections.defaultdict(list)
    for rid, g in sorted(groups().items()):
        off = int(rid.split("+")[1].split("@")[0])
        nums = {p: int(p.rsplit("_", 1)[1]) for p in g["pages"]}
        for p in sorted(g["pages"]):
            q = f"{p.rsplit('_',1)[0]}_{nums[p]+off:04d}"
            if q in g["pages"]:
                pairs_by_file[g["file"]].append((p, q))

    plans = []
    for f, pairs in sorted(pairs_by_file.items()):
        rows = [json.loads(l) for l in
                (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()]
        texts = page_text(rows)
        spans = page_spans(rows)
        for comp in sorted(components(pairs)):
            members = [m for m in comp if texts.get(m) and spans.get(m)]
            if len(members) < 2:
                continue
            sc = {m: score(texts[m], attested)["net"] for m in members}
            base = max(members, key=lambda m: (sc[m], m))
            others = [m for m in members if m != base]
            reads = [[t[3] for t in spans[m]] for m in [base] + others]
            out, tally, how = merge(reads, attested, 0)
            subs, guesses = [], []
            for k, (label, variants) in enumerate(how):
                i, start, end, was = spans[base][k]
                if label == "winner":
                    # Served text nobody attests. It stays as the better read had
                    # it, so there is nothing to write; what is recorded is that
                    # a disagreement was settled by rank rather than by evidence.
                    guesses.append([i, start, was,
                                    [v for v in variants if v != was]])
                elif out[k] != was:
                    subs.append([i, start, end, was, out[k], label])
            plans.append({"file": f, "base": base, "displace": others,
                          "reads": len(members), "decisions": tally,
                          "positions": len(out), "subs": subs, "guesses": guesses,
                          "merged_opens": " ".join(out[:26]),
                          "base_opens": " ".join(reads[0][:26]),
                          "other_opens": " ".join(reads[1][:26])})
    return plans


def write_guesses(rows: list[dict], served: bool) -> None:
    """Every position where merging was a guess, with the reading that lost, so
    the class can be read without opening the audit. Quoted on #33, so it has a
    Makefile rule."""
    GUESSES.write_text(json.dumps({
        "what": "every position where merging the reads of a page was a guess: "
                "the reads disagreed and nothing in the corpus's non-OCR text "
                "attests any variant, so the better read's token was served",
        "issue": "open-greek/open-greek-corpus#33",
        "served_is_not_attested": "the token under 'served' is what the corpus "
                                  + ("now carries" if served else "would carry")
                                  + ". It is the better read's, not a reading any "
                                    "evidence chose.",
        "offsets_are_into": ("the served text" if served else
                             "the text as it stands before the merge"),
        "positions": len(rows),
        "rows": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {GUESSES.relative_to(REPO)} ({len(rows):,} positions)")


def do_unapply() -> None:
    if not AUDIT.exists():
        fail(f"no audit at {AUDIT.relative_to(REPO)}")
    rec = json.loads(AUDIT.read_text(encoding="utf-8"))
    for f, blk in sorted(rec["files"].items()):
        fp = REPO / f
        if not fp.exists():
            fail(f"{f} no longer exists; whatever moved it must be reversed first")
        if sha(fp.read_text(encoding="utf-8")) != blk["sha256_after"]:
            fail(f"{f} has moved since this audit; reverse that first")
        rows = [json.loads(l) for l in
                fp.read_text(encoding="utf-8").splitlines() if l.strip()]
        # Put the displaced rows back FIRST, lowest index first, because every
        # substitution below is recorded against the row numbering this file had
        # before anything moved.
        for e in sorted(blk["removed_rows"], key=lambda e: e["index"]):
            rows.insert(e["index"], e["row"])
        by_row: dict[int, list] = collections.defaultdict(list)
        for i, start, was in blk["subs"]:
            by_row[i].append((start, was))
        for i in blk.get("marked_rows", sorted(by_row)):
            rows[i].pop("merged_read", None)
        for i, spots in by_row.items():
            t = rows[i]["text"]
            # FORWARD. The offsets are into the original text, so they are only
            # right once everything earlier in the row is back to its original
            # length; walking backward puts every one after the first a
            # character out as soon as a replacement was a different width.
            for start, was in sorted(spots):
                m = _GK.match(t, start)
                if not m:
                    fail(f"{f}: no token at offset {start} of row {i}")
                t = t[:start] + was + t[m.end():]
            rows[i]["text"] = t
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                      encoding="utf-8")
        if sha(fp.read_text(encoding="utf-8")) != blk["sha256_before"]:
            fail(f"unapply did not restore {f} byte-for-byte")
    for f in rec["witness_files_written"]:
        if (REPO / f).exists():
            (REPO / f).unlink()
    AUDIT.unlink()
    print(f"UNAPPLIED: {len(rec['files'])} file(s) restored byte-for-byte, "
          f"{len(rec['witness_files_written'])} witness file(s) removed")


def write_sample(payload: dict) -> None:
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({len(payload['sample'])} pages to read)")


def do_apply(plans: list[dict], date: str, att_stats: dict,
             payload: dict) -> None:
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")
    by_file: dict[str, list] = collections.defaultdict(list)
    for pl in plans:
        by_file[pl["file"]].append(pl)

    # PRE-FLIGHT, before a byte is written. The first run of this pass wrote six
    # files and six witness files and then refused itself on the seventh, which
    # left a half-merged tree with no audit to reverse it. Nothing is written now
    # until the whole plan has been checked.
    for f, pls in sorted(by_file.items()):
        bases = {pl["base"] for pl in pls}
        gone = {d for pl in pls for d in pl["displace"]}
        if bases & gone:
            fail(f"{f}: {sorted(bases & gone)} would be both merged into and moved")
        seen_row: dict[int, list] = collections.defaultdict(list)
        for pl in pls:
            for i, start, end, _w, _n, _l in pl["subs"]:
                seen_row[i].append((start, end))
        for i, spots in seen_row.items():
            prev = -1
            for start, end in sorted(spots):
                if start < prev:
                    fail(f"{f} row {i}: two decisions for the token at {start}")
                prev = end

    files, written = {}, []
    moved_tokens = subbed = guessed = 0
    for f, pls in sorted(by_file.items()):
        fp = REPO / f
        raw = fp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
        subs_by_row: dict[int, list] = collections.defaultdict(list)
        guess_by_row: dict[int, int] = collections.Counter()
        mate: dict[int, str] = {}
        for pl in pls:
            for i, start, end, was, new, _lab in pl["subs"]:
                subs_by_row[i].append((start, end, new)); mate[i] = pl["displace"]
            for i, start, was, _rej in pl["guesses"]:
                guess_by_row[i] += 1; mate[i] = pl["displace"]
        audit_subs, marked = [], []
        guesses_by_row: dict[int, list] = collections.defaultdict(list)
        for pl in pls:
            for i, start, was, rej in pl["guesses"]:
                guesses_by_row[i].append([start, was, rej])
        for i in sorted(set(subs_by_row) | set(guess_by_row)):
            text = rows[i]["text"]
            if subs_by_row[i]:
                new = apply_subs(text, subs_by_row[i])
                if len(_GK.findall(new)) != len(_GK.findall(text)):
                    fail(f"{f} row {i}: substitution changed the token count")
                rows[i]["text"] = new
                audit_subs.extend([i, start, text[start:end]]
                                  for start, end, _n in sorted(subs_by_row[i]))
                # A guess is a claim about the SERVED text, so its offset has to
                # be one into the served text. A substitution earlier in the same
                # row can be a different width, which moves everything after it;
                # token ordinals do not move, because a substitution is always
                # one token for one token, so re-read the row and carry the
                # ordinal across.
                was_at = [m.start() for m in _GK.finditer(norm_elision(text))]
                now_at = [m.start() for m in _GK.finditer(norm_elision(new))]
                if len(was_at) != len(now_at):
                    fail(f"{f} row {i}: token count moved under substitution")
                shift = dict(zip(was_at, now_at))
                for g in guesses_by_row[i]:
                    if g[0] not in shift:
                        fail(f"{f} row {i}: guess at {g[0]} is not a token start")
                    g[0] = shift[g[0]]
            rows[i]["merged_read"] = {
                "with": mate[i], "substituted": len(subs_by_row[i]),
                "guessed": guess_by_row[i]}
            marked.append(i)
        subbed += sum(len(v) for v in subs_by_row.values())
        guessed += sum(guess_by_row.values())

        drop = {d for pl in pls for d in pl["displace"]}
        moved_idx = [i for i, r in enumerate(rows)
                     if (m := PAGE.match(str(r["locus"]))) and m.group(1) in drop]
        # Only the rows that move, with the index each sat at, never the whole
        # file: archiving whole files is what made two earlier audits 606 MB and
        # 251 MB, which GitHub refuses.
        removed = [{"index": i, "row": dict(rows[i])} for i in moved_idx]
        keep = [r for i, r in enumerate(rows) if i not in set(moved_idx)]
        files[f] = {"sha256_before": sha(raw), "rows_before": len(rows),
                    "rows_after": len(keep), "removed_rows": removed,
                    "subs": audit_subs, "marked_rows": marked,
                    "guesses": [[i, start, was, rej]
                                for i in sorted(guesses_by_row)
                                for start, was, rej in guesses_by_row[i]]}
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep),
                      encoding="utf-8")
        files[f]["sha256_after"] = sha(fp.read_text(encoding="utf-8"))

        witness = [dict(e["row"]) for e in removed]
        for r in witness:
            moved_tokens += len(_GK.findall(r.get("text") or ""))
            r["rank"] = "secondary"
            r["secondary_reason"] = (
                "a second OCR reading of a page this work already serves, whose "
                "readings were merged into the page kept primary rather than "
                "discarded; preserved here out of the served counts (cisco's "
                "rule 2026-08-09, merge decided 2026-08-11; "
                "scripts/merge_duplicate_reads.py)")
        wfp = SECONDARY / f"{fp.name[:-len('.jsonl')]}.{WITNESS_SUFFIX}.jsonl"
        wfp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in witness),
                       encoding="utf-8")
        written.append(wfp.relative_to(REPO).as_posix())

    AUDIT.write_text(json.dumps({
        "_meta": {
            "what": "duplicate reads of one printed page merged into the better "
                    "read, the other moved to witnesses so nothing is served twice",
            "date": date, "issue": "open-greek/open-greek-corpus#33",
            "tool": "scripts/merge_duplicate_reads.py",
            "decision": "cisco, 2026-08-11, having seen the measured split "
                        "(80.1% agree, 7.6% settled by attestation, 12.3% guessed)",
            "reverse": "python3 scripts/merge_duplicate_reads.py --unapply, "
                       "then rebuild data/duplicate_page_candidates.json, which "
                       "is swept from the corpus and so no longer lists the "
                       "pages this pass merged",
            "what_subs_hold": "index of the row, offset into that row's text as "
                              "it stood before this pass, and the token that was "
                              "there. The replacement reverses from those alone.",
            "what_guesses_hold": "index of the row in this file's numbering "
                                 "BEFORE the displaced pages were taken out, "
                                 "the offset into that row's SERVED text, the "
                                 "token now served, "
                                 "and the readings that lost. Nothing attests any "
                                 "of them; the served one is the better read's, "
                                 "which is a rank and not evidence. Recorded so "
                                 "the class can be found and re-decided later.",
        },
        "attestation": att_stats,
        "printed_pages_merged": len(plans),
        "reads_merged": sum(pl["reads"] for pl in plans),
        "tokens_substituted": subbed,
        "positions_guessed": guessed,
        "pages_displaced": sum(len(pl["displace"]) for pl in plans),
        "greek_tokens_displaced": moved_tokens,
        "witness_files_written": written,
        "sample_artifact": {**payload,
                            "what": "what merging the duplicate reads produced"},
        "files": files,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # Rewrite the published list from what was actually applied. The one main()
    # wrote is the proposal's, whose offsets are into the text as it stood before
    # the substitutions landed.
    write_guesses([{"file": f, "row": i, "offset": start,
                    "served": was, "rejected": rej}
                   for f, blk in sorted(files.items())
                   for i, start, was, rej in blk["guesses"]], served=True)

    ndisp = sum(len(pl["displace"]) for pl in plans)
    print(f"\nAPPLIED: {subbed:,} tokens substituted, {ndisp} pages "
          f"({moved_tokens:,} tokens) moved to {len(written)} witness files,\n"
          f"  {guessed:,} positions marked as guesses. "
          f"Audit {AUDIT.relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    a = ap.parse_args()
    if a.unapply:
        do_unapply(); return

    if AUDIT.exists() and not a.apply:
        # The pages this pass merges stop existing as separate pages once it has
        # run, so recomputing here would find nothing and blank both published
        # artifacts. Report what the audit records and leave them alone, which is
        # also what makes `make reports` a no-op afterwards.
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        print(f"already applied ({rec['_meta']['date']}): "
              f"{rec['printed_pages_merged']} printed pages from "
              f"{rec['reads_merged']} reads, {rec['tokens_substituted']:,} tokens "
              f"substituted, {rec['pages_displaced']} pages "
              f"({rec['greek_tokens_displaced']:,} tokens) moved to witnesses, "
              f"{rec['positions_guessed']:,} positions guessed.")
        # Rebuilt, not merely left alone: make compares timestamps, and a
        # target this never touches is out of date on every run for ever.
        write_sample(rec["sample_artifact"])
        write_guesses([{"file": f, "row": i, "offset": start,
                        "served": was, "rejected": rej}
                       for f, blk in sorted(rec["files"].items())
                       for i, start, was, rej in blk["guesses"]], served=True)
        print(f"  reverse with --unapply; evidence in {GUESSES.relative_to(REPO)}")
        return

    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions["works"] if "works" in editions else editions
    attested, st = build_attestation(editions)
    print(f"attestation: {st['n_unique_forms']:,} forms from {st['n_works']:,} non-OCR works")

    plans = plan(attested)
    total = collections.Counter()
    for pl in plans:
        total.update(pl["decisions"])
    dec = sum(total.values())
    reads = sum(pl["reads"] for pl in plans)
    print(f"\n{len(plans)} printed pages merged from {reads} reads, "
          f"{dec:,} token positions")
    if not dec:
        # Nothing to do, and the likely reason is worth saying out loud: the
        # candidate sweep is derived from the corpus, so after an --unapply it
        # still describes the merged tree and lists no pairs. Rebuild it with
        # `make data/duplicate_page_candidates.json` and run this again.
        print("  no duplicate reads found. If this followed an --unapply, "
              "rebuild data/duplicate_page_candidates.json first.")
        return
    for k in ("agree", "majority", "attested", "winner"):
        if total.get(k):
            print(f"    {k:<9} {total[k]:>7,}  {total[k]/dec:.2%}")
    guessed = total.get("winner", 0)
    print(f"\n  {guessed:,} positions ({guessed/dec:.2%}) had no attested variant to "
          f"choose from, so the merge kept the better read's token and marked it.\n"
          f"  Those are the ones where merging is guessing.")

    sample = [{"file": pl["file"],
               "pages": sorted([pl["base"]] + pl["displace"]),
               "kept_as_base": pl["base"], "decisions": pl["decisions"],
               "merged_opens": pl["merged_opens"],
               "base_opens": pl["base_opens"],
               "other_opens": pl["other_opens"]}
              for pl in plans
              if pl["decisions"].get("attested", 0) + pl["decisions"].get("winner", 0)
              ][:a.sample]
    applied = AUDIT.exists() or a.apply
    payload = {
        "what": ("what merging the duplicate reads produced" if applied else
                 "what merging the duplicate reads would produce, NOT APPLIED"),
        "issue": "open-greek/open-greek-corpus#33",
        "decision": "cisco chose merge over pick-a-winner on 2026-08-10 and "
                    "accepted the measured split on 2026-08-11.",
        "why_a_sample": "a merged page is a text no scan attests on its own. Every "
                        "position where the reads disagree is a decision this code "
                        "made, so the decisions are counted and shown rather than "
                        "presented as a result.",
        "order_of_preference": ["agree", "majority (3+ reads)",
                                "attested (exactly one variant is a known word)",
                                "winner (nothing attested; kept the better read "
                                "and marked it)"],
        "printed_pages_merged": len(plans), "reads_merged": reads,
        "token_positions": dec,
        "decisions": dict(total),
        "unattested_share": round(guessed / dec, 4) if dec else None,
        "sample": sample,
    }
    write_sample(payload)

    write_guesses([{"file": pl["file"], "page": pl["base"], "row": i,
                    "offset": start, "served": was, "rejected": rej}
                   for pl in plans for (i, start, was, rej) in pl["guesses"]],
                  served=False)

    if not a.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    do_apply(plans, a.date, st, payload)


if __name__ == "__main__":
    main()
