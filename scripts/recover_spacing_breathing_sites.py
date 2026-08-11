#!/usr/bin/env python3
"""Rebuild the site list the 2026-08-07 spacing-breathing composition never wrote.

That pass composed 30,557 spacing breathings onto the capital after them across
15,646 rows in 678 files, and its audit recorded only a per-file sha256 pair and
a histogram of the 14 distinct substitutions. That is not enough to reverse it.
A histogram says ᾿Ι -> Ἰ happened 4,000-odd times; it does not say where, and
splitting every Ἰ in the corpus would also split the ones the sources already
spelled that way. Issue #36.

The sites are recoverable, because the pass was committed. 0f468f8 is the commit
that applied it and its parent holds the text as it stood before, so a row-by-row
diff of the two trees says exactly which offsets moved.

The commit is also the only trustworthy list of what the pass touched, and that
is the second half of #36. The audit keys per-file counts and hashes by
BASENAME, and 60 slugs exist in both data/corpus and data/corpus_secondary, so
each of those pairs overwrote the other and only one side survived. The pass
edited 738 files; the audit names 678, and the 60 it lost hold 2,043 of the
substitutions in 1,056 rows, recorded nowhere at all. Its own totals give it
away: the per-file counts sum to 28,514 against a stated 30,557, and the missing
2,043 close the gap exactly. So this rebuilds the record from the commit's
changed-file list, keyed by PATH.

What this writes is the same shape every other audit here uses: per file, the row
index, the offset into that row, and the two characters that were there. The
round trip is asserted before anything is written, by replaying every recovered
site backwards over the committed post-composition text and requiring the result
to equal the parent's bytes exactly, for all 678 files.

This does NOT make the pass reversible today. 552 of the 678 files have been
edited since, and unapply refuses a file whose sha256 has moved, exactly as
split_carved_row.py does, because restoring one silently reverses whatever was
applied on top. It makes the record complete, so the pass is reversible on the
same terms as everything else here: unwind newest first.

  python3 scripts/recover_spacing_breathing_sites.py           # report
  python3 scripts/recover_spacing_breathing_sites.py --write
"""
from __future__ import annotations
import argparse, collections, hashlib, json, subprocess, sys, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
AUDIT = DATA / "corpus_changes" / "spacing-breathing-composition.json"
COMMIT = "0f468f8"
PSILI, DASIA = "᾿", "῾"
COMBINING = {PSILI: "̓", DASIA: "̔"}
CAPITALS = set("ΑΕΗΙΟΥΩΡ")
sha = lambda b: hashlib.sha256(b).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")


def blob(rev: str, path: str) -> bytes:
    out = subprocess.run(["git", "show", f"{rev}:{path}"],
                         capture_output=True, cwd=REPO)
    return out.stdout if out.returncode == 0 else b""


def sites(before: str, after: str) -> list:
    """Offsets into AFTER where a mark+capital became one letter, with the pair.

    Walks the two strings together. Everything outside a composition is
    identical, so a mismatch is a composition and both sides advance past it.
    """
    out, i, j = [], 0, 0
    while i < len(before) and j < len(after):
        if before[i] == after[j]:
            i += 1; j += 1; continue
        pair = before[i:i + 2]
        if (len(pair) == 2 and pair[0] in COMBINING and pair[1] in CAPITALS
                and unicodedata.normalize("NFC", pair[1] + COMBINING[pair[0]])
                == after[j]):
            out.append([j, pair]); i += 2; j += 1; continue
        return []          # not a composition; caller reports the row
    return out if i == len(before) and j == len(after) else []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rec = json.loads(AUDIT.read_text(encoding="utf-8"))
    parent = subprocess.run(["git", "rev-parse", f"{COMMIT}^"],
                            capture_output=True, text=True, cwd=REPO).stdout.strip()
    changed = [p for p in subprocess.run(
        ["git", "diff", "--name-only", f"{COMMIT}^", COMMIT],
        capture_output=True, text=True, cwd=REPO).stdout.split("\n")
        if p.endswith(".jsonl")]

    files, total, rows_touched, unresolved, lost = [], 0, 0, [], []
    for path in sorted(changed):
        b_raw, a_raw = blob(parent, path), blob(COMMIT, path)
        if not b_raw or not a_raw:
            unresolved.append(path); continue
        want_before, want_after = sha(b_raw), sha(a_raw)
        b_rows = [json.loads(l) for l in b_raw.decode().splitlines() if l.strip()]
        a_rows = [json.loads(l) for l in a_raw.decode().splitlines() if l.strip()]
        if len(b_rows) != len(a_rows):
            unresolved.append(path); continue
        edits = []
        for i, (br, ar) in enumerate(zip(b_rows, a_rows)):
            if br.get("text") == ar.get("text"):
                continue
            s = sites(br.get("text") or "", ar.get("text") or "")
            if not s:
                unresolved.append(f"{path} row {i}"); continue
            edits.append([i, s]); total += len(s); rows_touched += 1
        files.append({"file": path, "sha256_before": want_before,
                      "sha256_after": want_after, "edits": edits})
        # Recorded at all? Only if the audit's entry for this basename is
        # actually THIS file and not the same-named one next door.
        if rec["sha256_before"].get(path.rsplit("/", 1)[-1]) != want_before:
            lost.append(path)

    print(f"{total:,} sites recovered in {rows_touched:,} rows across "
          f"{len(files)} files (audit says {rec['substitutions']:,} in "
          f"{rec['rows_touched']:,} and names {len(rec['sha256_before'])} files)")
    print(f"  {len(lost)} files the audit's basename keying lost entirely")
    if unresolved:
        print(f"  UNRESOLVED: {len(unresolved)} -> {unresolved[:5]}")

    # Replay every site backwards over the committed post-composition text and
    # require the parent's bytes back, byte for byte, before writing anything.
    checked = 0
    for blk in files:
        a_rows = [json.loads(l) for l in blob(COMMIT, blk["file"]).decode().splitlines()
                  if l.strip()]
        for i, spots in blk["edits"]:
            t = a_rows[i]["text"]
            for off, pair in reversed(spots):
                t = t[:off] + pair + t[off + 1:]
            a_rows[i]["text"] = t
        got = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in a_rows)
        if sha(got.encode()) != blk["sha256_before"]:
            fail(f"replaying {blk['file']} backwards does not give sha256_before")
        checked += 1
    print(f"  round trip: {checked}/{len(files)} files replay backwards to "
          f"sha256_before exactly")
    if total != rec["substitutions"] or rows_touched != rec["rows_touched"]:
        fail("recovered site count disagrees with the audit's own totals")
    if unresolved:
        fail("some files did not resolve; not writing a partial record")
    if not a.write:
        print("\nreport only; re-run with --write")
        return
    rec["files"] = files
    rec["files_the_basename_keying_LOST"] = {
        "what": "the pass edited these and the audit never named them: per-file "
                "counts and hashes were keyed by basename, and a same-named file "
                "in the other directory overwrote each one",
        "count": len(lost), "files": sorted(lost),
    }
    rec["recovered_sites"] = {
        "what": "row index, offset into that row, and the two characters that "
                "were there, recovered from the commit that applied this pass",
        "how": f"row-by-row diff of {COMMIT} against its parent, matched to the "
               "audit's basenames by content against sha256_before",
        "date": "2026-08-11", "issue": "open-greek/open-greek-corpus#36",
        "verified": "every site replays backwards over the committed text to "
                    "sha256_before, for all files",
    }
    rec["reverse"] = ("python3 scripts/compose_spacing_breathings.py --unapply. "
                      "Refuses any file whose sha256 has moved since, which is "
                      "most of them: unwind newer passes first.")
    AUDIT.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    print(f"\nwrote {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
