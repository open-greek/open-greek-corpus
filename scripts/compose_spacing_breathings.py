#!/usr/bin/env python3
"""Compose a spacing breathing that belongs on the capital letter after it.

Older Greek typesetting, and the OCR that reads it, writes the breathing of an
initial capital as a SEPARATE spacing mark before the letter: U+1FBF psili or
U+1FFE dasia, then the bare capital. The page prints one letter with a breathing
over it; our bytes hold two characters. So the corpus carries the same word under
two encodings and treats them as different words:

    ᾿Ιουδαίων    382   beside   Ἰουδαίων   7,564
    ᾿Αθηναίων    357   beside   Ἀθηναίων   5,776
    ᾿Ισραὴλ      213   beside   Ἰσραὴλ     7,627

5,213 forms and 22,379 tokens are split this way, and the damage does not stop at
the count. The lemmatizer never saw the legacy spelling in training, so it
invents a lemma for it: `᾿Ιουδαίων` lemmatizes to `᾿ιουδαις` where `Ἰουδαίων`
reaches `Ἰουδαῖος`, and `᾿Αθηναίων` is echoed back at itself where `Ἀθηναίων`
reaches `Ἀθηναῖος`. So the split is both undercounting real headwords and minting
junk ones beside them.

The repair is Unicode identity rather than a judgment about Greek: move the
breathing after the letter as its combining mark and NFC-compose. Ἀ is what
U+0391 U+0313 composes to, and that is the character the page shows.

Three things it must not do, each of which is a real string in this corpus:

  * fire before a lowercase letter. `᾿ς` (76 tokens) and `῾τὸ` (68) are
    apostrophes and stray marks, not breathings, and composing those would
    corrupt text. Only a capital Α Ε Η Ι Ο Υ Ω Ρ qualifies.
  * fire on a letter that already carries a breathing, which would produce a
    double-breathed character.
  * pretend to compose when no precomposed character exists. Capital upsilon and
    rho with PSILI have none (initial upsilon and rho take the rough breathing),
    so 170 forms and 232 tokens are left exactly as they are rather than
    silently half-normalized. Those spellings are OCR errors for the dasia, but
    guessing that here would be a correction this rule cannot justify.

Token counts do not move: a spacing breathing is inside the Greek Extended block,
so `build_public_corpus._GK` already reads mark-plus-letter as one token, and the
composed letter is one token too.

Audit: data/corpus_changes/spacing-breathing-composition.json, with the per-file
counts and every distinct substitution, so the change is reversible by splitting
each composed letter back into mark plus bare capital.

  python3 scripts/compose_spacing_breathings.py            # report
  python3 scripts/compose_spacing_breathings.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

PSILI, DASIA = "᾿", "῾"          # spacing marks
COMBINING = {PSILI: "̓", DASIA: "̔"}
CAPITALS = set("ΑΕΗΙΟΥΩΡ")


def compose(text: str) -> tuple[str, Counter]:
    """Return the text with composable spacing breathings folded in."""
    out, subs, i = [], Counter(), 0
    while i < len(text):
        c = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if c in COMBINING and nxt in CAPITALS:
            # Refuse if the letter already carries a breathing of its own.
            decomposed = unicodedata.normalize("NFD", nxt)
            if "̓" in decomposed or "̔" in decomposed:
                out.append(c)
                i += 1
                continue
            merged = unicodedata.normalize("NFC", nxt + COMBINING[c])
            # Only accept a real precomposed character. Capital upsilon and rho
            # with psili have none, and NFC leaves them as letter + mark; taking
            # that would change the bytes without composing anything.
            if len(merged) == 1:
                out.append(merged)
                subs[f"{c}{nxt} -> {merged}"] += 1
                i += 2
                continue
        out.append(c)
        i += 1
    return "".join(out), subs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(list((DATA / "corpus").glob("*.jsonl"))
                   + list((DATA / "corpus_secondary").glob("*.jsonl")))
    per_file: dict[str, int] = {}
    subs: Counter = Counter()
    rows_touched = tok_before = tok_after = 0
    pending: dict[Path, str] = {}

    for fp in files:
        raw = fp.read_text(encoding="utf-8")
        if PSILI not in raw and DASIA not in raw:
            continue
        out_lines, n_here = [], 0
        for line in raw.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            text = row.get("text") or ""
            new, s = compose(text)
            if new != text:
                tok_before += len(_GK.findall(text))
                tok_after += len(_GK.findall(new))
                row["text"] = new
                subs.update(s)
                n_here += sum(s.values())
                rows_touched += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        if n_here:
            per_file[fp.name] = n_here
            pending[fp] = "\n".join(out_lines) + "\n"

    total = sum(subs.values())
    print(f"{total:,} spacing breathings compose, in {rows_touched:,} rows "
          f"across {len(per_file):,} files")
    print(f"  tokens in those rows: {tok_before:,} before, {tok_after:,} after "
          f"-> {'unchanged' if tok_before == tok_after else 'MOVED, STOP'}")
    print(f"  {len(subs)} distinct substitutions; commonest:")
    for s, n in subs.most_common(8):
        print(f"    {s}   x{n:,}")
    if tok_before != tok_after:
        raise SystemExit("token count moved; refusing to write")
    if not args.apply:
        print("\nreport only; nothing written. Re-run with --apply.")
        return

    before = {fp.name: hashlib.sha256(fp.read_bytes()).hexdigest() for fp in pending}
    for fp, body in pending.items():
        fp.write_text(body, encoding="utf-8")
    (CHANGES / "spacing-breathing-composition.json").write_text(json.dumps({
        "what": "spacing psili/dasia before a capital vowel or rho composed into "
                "the precomposed letter",
        "date": "2026-08-07",
        "issue": "open-greek/open-greek-corpus#4",
        "why": "the same word was carried under two encodings (᾿Ιουδαίων 382 beside "
               "Ἰουδαίων 7,564), which split every count and also minted junk "
               "lemmas: ᾿Ιουδαίων lemmatized to ᾿ιουδαις where Ἰουδαίων reaches "
               "Ἰουδαῖος.",
        "not_done": "a spacing breathing before a lowercase letter is an apostrophe "
                    "or a stray mark (᾿ς, ῾τὸ) and is untouched; so is a letter that "
                    "already carries a breathing; so are capital upsilon and rho "
                    "with psili, which have no precomposed form (170 forms, 232 "
                    "tokens) and are left rather than half-normalized.",
        "substitutions": total,
        "rows_touched": rows_touched,
        "greek_tokens_before": tok_before, "greek_tokens_after": tok_after,
        "distinct_substitutions": dict(sorted(subs.items())),
        "files": dict(sorted(per_file.items())),
        "sha256_before": before,
        "sha256_after": {fp.name: hashlib.sha256(fp.read_bytes()).hexdigest()
                         for fp in pending},
        "reverse": "for each substitution listed, split the composed letter back "
                   "into its spacing mark and bare capital; the mapping is 1:1 and "
                   "the listed counts say how many of each to expect.",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\naudit -> data/corpus_changes/spacing-breathing-composition.json")


if __name__ == "__main__":
    main()
