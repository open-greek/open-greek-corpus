#!/usr/bin/env python3
"""Separate ΔΕΞΙΠΠΟΥ from the word our OCR welded it to in PG113 locus 330.

Locus 330 ends the proem to Constantine VII's Excerpta de legationibus and the
next block's head runs straight into its last word:

    ...οὕτως ἢ ἑτέρως αὐτῷ τῶν πραγμάτων ἐπισυμβαινόνΔΕΞΙΠΠΟΥ

Two units, one token. The proem's real last word is ἐπισυμβαινόν and ΔΕΞΙΠΠΟΥ is
the display head of the Dexippus excerpts, which pass 5 already carved out as a
witness. Left as it is, the proem's closing token is a word that does not exist,
and it is counted, lemmatized and served as one.

This inserts one space. It does NOT decide where the boundary falls: the carve
that follows takes locus 330 whole under the shared-row rule, so ΔΕΞΙΠΠΟΥ still
travels with the proem. What changes is that it travels as the head it is,
rather than fused onto a Greek word, and a later pass can move it without first
having to repair a token.

Same shape as scripts/unsplice_pg003_heads.py, which did this for two
ΚΕΦΑΛΑΙΟΝ heads in PG 3. Kept separate rather than folded into it because that
script's audit is applied and rewriting its identity would break the trail.

  python3 scripts/unsplice_pg113_dexippus_head.py
  python3 scripts/unsplice_pg113_dexippus_head.py --apply
  python3 scripts/unsplice_pg113_dexippus_head.py --unapply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus" / "cogPG.PG113.jsonl"
AUDIT = DATA / "corpus_changes" / "cogPG.PG113.head-splice.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

LOCUS = "330"
HEAD = "ΔΕΞΙΠΠΟΥ"
PREV_ENDS = "ἐπισυμβαινόν"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def rows() -> tuple[list[dict], str]:
    raw = SRC.read_text(encoding="utf-8")
    return [json.loads(l) for l in raw.splitlines() if l.strip()], raw


def dump(rs: list[dict]) -> None:
    SRC.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs),
                   encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    rs, raw = rows()
    row = next((r for r in rs if str(r["locus"]).split(".")[-1] == LOCUS), None)
    if row is None:
        fail(f"locus {LOCUS} is not in {SRC.name}")

    if args.unapply:
        if not AUDIT.exists():
            fail(f"{AUDIT.relative_to(REPO)} does not exist")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        if sha(raw) != rec["sha256_after"]:
            fail("the file is not in the state this audit recorded")
        row["text"] = rec["text_before"]
        dump(rs)
        if sha(SRC.read_text(encoding="utf-8")) != rec["sha256_before"]:
            fail("unapply did not restore the file byte-for-byte")
        AUDIT.unlink()
        print("UNAPPLIED: restored byte-for-byte")
        return

    text = row["text"]
    glued = PREV_ENDS + HEAD
    if glued not in text:
        if f"{PREV_ENDS} {HEAD}" in text:
            fail("already applied: the head is already separated")
        fail(f"expected {glued!r} in locus {LOCUS}, not found")
    new = text.replace(glued, f"{PREV_ENDS} {HEAD}", 1)
    before, after = len(_GK.findall(text)), len(_GK.findall(new))
    print(f"locus {LOCUS}: {glued!r} -> {PREV_ENDS + ' ' + HEAD!r}")
    print(f"  row tokens {before} -> {after} (+{after - before}, the welded pair "
          f"becoming the two it is)")

    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")

    row["text"] = new
    dump(rs)
    AUDIT.write_text(json.dumps({
        "what": f"one space inserted between {PREV_ENDS} and the display head "
                f"{HEAD} in Migne PG113 locus {LOCUS}",
        "date": "2026-08-09",
        "issue": "open-greek/open-greek-corpus#8",
        "why": "the proem to Constantine VII's Excerpta de legationibus ended on "
               "a token that is not a word, its real last word fused to the head "
               "of the Dexippus excerpts that follow. It was counted, lemmatized "
               "and served in that state.",
        "not_a_boundary_decision": f"{HEAD} still travels with the proem when "
               "locus 330 is carved whole, under the shared-row rule the plan "
               "already uses. This only makes it a separate token, so a later "
               "pass can move it without first repairing a word.",
        "token_delta_is_intended": f"+{after - before}, the welded pair becoming "
                                   "the two tokens it always was",
        "greek_tokens_before": before, "greek_tokens_after": after,
        "text_before": text, "text_after": new,
        "files": [str(SRC.relative_to(REPO))],
        "sha256_before": sha(raw),
        "sha256_after": sha(SRC.read_text(encoding="utf-8")),
        "reverse": "python3 scripts/unsplice_pg113_dexippus_head.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
