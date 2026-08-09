#!/usr/bin/env python3
"""Separate two PG003 chapter heads our OCR ran into the word before them.

Two blocks of PG 3 are still served under the volume urn for one reason: the
head that starts them has no space in front of it. Migne prints ΚΕΦΑΛΑΙΟΝ Ζʹ on
its own line, but our OCR joined it to the tail of the preceding column, so the
rows read

    locus 283  ...νει κἀκεῖσε τῆς τάξεως τὸ ἀσύγΚΕΦΑΛΑΙΟΝ Ζʹ. Ι. Περὶ τῶν...
    locus 440  ...ἄεαηε, νεῖ οοαε αο οο ΛαΙΟΙΙΦίΚΕΦΑΛΑΙΟΝ Ζʹ. ΘΥΝΟΡΘΙΘ...

split_carved_row.py refuses an offset that is not at a whitespace boundary, and
it is right to: cutting inside a Greek run splits one word into two and files
half of it under the wrong author. So the fix belongs in the text, not in the
splitter's guard, which tests/test_row_split.py defends by name.

That these are two units and not one word is the edition's, not a guess. The
second OCR of the same volume prints each head on a line of its own, and at 283
it also keeps the word ours lost: ἀσύγ- carries over the column break to χυτον,
giving ἀσύγχυτον, while ours drops the second half and welds the remainder to
the head. At 440 what precedes the head is not Greek at all. It is Migne's Latin
column read as Greek letter shapes, ἄεαηε, νεῖ οοαε αο οο for atque, vel
quocunque alio modo, so there is no word there to break.

WHAT THIS DOES NOT DO. It does not supply the missing χυτον from the other
witness. Restoring a word one OCR dropped by copying another OCR is a different
and much larger claim than separating two units that are visibly two, and it
would put text into the corpus that our scan does not attest. ἀσύγ stays a
fragment, and stays wrong, and is recorded here as wrong.

Each insertion adds one Greek token, because one token becomes two. That is
real and it is the point, so the served total moves by exactly +2 and this audit
carries the before and after rather than leaving a consumer to find it.

  python3 scripts/unsplice_pg003_heads.py
  python3 scripts/unsplice_pg003_heads.py --apply
  python3 scripts/unsplice_pg003_heads.py --unapply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SRC = DATA / "corpus" / "cogPG.PG003.jsonl"
AUDIT = DATA / "corpus_changes" / "cogPG.PG003.head-splice.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

HEAD = "ΚΕΦΑΛΑΙΟΝ Ζʹ."
# locus, offset the head starts at, and the text that must run into it. Asserted
# rather than searched for: ΚΕΦΑΛΑΙΟΝ Ζʹ occurs elsewhere in the volume at a
# legal boundary, and a search would find those too.
SPLICES = [
    {"locus": "283", "offset": 1586, "prev_ends_with": "τὸ ἀσύγ",
     "witness": "the Internet Archive OCR of the same volume prints the head on "
                "its own line and reads the word as ἀσύγ- / χυτον across the "
                "column break; ours drops χυτον and welds ἀσύγ to the head",
     "still_wrong": "ἀσύγ is half of ἀσύγχυτον. This pass does not supply the "
                    "missing half from the other witness."},
    {"locus": "440", "offset": 321, "prev_ends_with": "ΛαΙΟΙΙΦί",
     "witness": "the Internet Archive OCR prints the head on its own line here "
                "too; what precedes it in our row is Migne's Latin column read "
                "as Greek shapes, ἄεαηε, νεῖ οοαε αο οο for atque, vel "
                "quocunque alio modo",
     "still_wrong": "the ~30 junk tokens before the head are Latin misread as "
                    "Greek and stay in the text; separating them from the head "
                    "is all this does."},
]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def load() -> tuple[list[dict], str]:
    raw = SRC.read_text(encoding="utf-8")
    return [json.loads(l) for l in raw.splitlines() if l.strip()], raw


def dump(rows: list[dict]) -> None:
    SRC.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                   encoding="utf-8")


def locus_of(r: dict) -> str:
    return str(r["locus"]).split(".")[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--apply", action="store_true")
    g.add_argument("--unapply", action="store_true")
    args = ap.parse_args()

    if args.unapply:
        if not AUDIT.exists():
            fail(f"{AUDIT.relative_to(REPO)} does not exist")
        rec = json.loads(AUDIT.read_text(encoding="utf-8"))
        rows, raw = load()
        if sha(raw) != rec["sha256_after"]:
            fail("cogPG.PG003.jsonl is not in the state this audit recorded; "
                 "unapply anything applied on top of it first")
        by = {locus_of(r): r for r in rows}
        for s in rec["splices"]:
            by[s["locus"]]["text"] = s["text_before"]
        dump(rows)
        got = sha(SRC.read_text(encoding="utf-8"))
        if got != rec["sha256_before"]:
            fail(f"restored file does not match sha256_before ({got})")
        AUDIT.unlink()
        print(f"UNAPPLIED: {len(rec['splices'])} splices restored, "
              f"cogPG.PG003.jsonl byte-for-byte")
        return

    rows, raw = load()
    by = {locus_of(r): r for r in rows}
    plan = []
    for s in SPLICES:
        r = by.get(s["locus"])
        if r is None:
            fail(f"locus {s['locus']} is not in {SRC.name}; the carve may be "
                 f"applied. Unapply it first, this runs on the volume file.")
        t, off = r["text"], s["offset"]
        got = t[off:off + len(HEAD)]
        if got != HEAD:
            fail(f"locus {s['locus']}: expected {HEAD!r} at {off}, found {got!r}")
        if not t[:off].endswith(s["prev_ends_with"]):
            fail(f"locus {s['locus']}: text before {off} should end "
                 f"{s['prev_ends_with']!r}, ends {t[max(0, off - 24):off]!r}")
        if t[off - 1].isspace():
            fail(f"locus {s['locus']}: offset {off} is already at a whitespace "
                 f"boundary; this correction has been applied")
        new = t[:off] + " " + t[off:]
        plan.append((r, s, t, new))
        print(f"locus {s['locus']:>4} offset {off}: "
              f"{t[off - len(s['prev_ends_with']):off + 14]!r}")
        print(f"            -> {new[off - len(s['prev_ends_with']):off + 15]!r}"
              f"   tokens {len(_GK.findall(t))} -> {len(_GK.findall(new))}")

    before = sum(len(_GK.findall(r.get("text") or "")) for r in rows)
    after = before + len(plan)
    print(f"\nvolume file: {before:,} Greek tokens -> {after:,} (+{len(plan)}, "
          f"one per splice; each welded pair becomes the two tokens it is)")

    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists")

    for r, _s, _old, new in plan:
        r["text"] = new
    dump(rows)
    got_after = sum(len(_GK.findall(r.get("text") or "")) for r in rows)
    if got_after != after:
        fail(f"token count after is {got_after}, expected {after}")

    AUDIT.write_text(json.dumps({
        "what": "one space inserted before each of two ΚΕΦΑΛΑΙΟΝ Ζʹ heads that "
                "our OCR ran into the text before them in Migne PG 3",
        "date": "2026-08-09",
        "issue": "open-greek/open-greek-corpus#8",
        "why": "the head has no space in front of it, so split_carved_row.py "
               "refuses the offset, and two blocks of the volume stay served "
               "under the volume urn instead of under the works they belong to. "
               "The guard is right and the text is wrong, so the text is what "
               "changes here.",
        "not_done": "the word our OCR lost at locus 283, χυτον, is NOT supplied "
                    "from the other witness. ἀσύγ stays a fragment. Restoring a "
                    "dropped word by copying a different OCR is a larger claim "
                    "than separating two units that are visibly two.",
        "token_delta_is_intended": "+2 Greek tokens, one per splice, because one "
                                   "welded token becomes the two it always was. "
                                   "The carve that follows conserves exactly.",
        "greek_tokens_before": before, "greek_tokens_after": after,
        "splices": [{"locus": s["locus"], "offset": s["offset"],
                     "head": HEAD, "prev_ends_with": s["prev_ends_with"],
                     "evidence": s["witness"], "still_wrong": s["still_wrong"],
                     "text_before": old, "text_after": new}
                    for _r, s, old, new in plan],
        "files": [str(SRC.relative_to(REPO))],
        "sha256_before": sha(raw),
        "sha256_after": sha(SRC.read_text(encoding="utf-8")),
        "reverse": "python3 scripts/unsplice_pg003_heads.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {len(plan)} splices, audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
