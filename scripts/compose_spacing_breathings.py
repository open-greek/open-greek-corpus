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

THE SECOND PASS, --lowercase, 2026-08-11. The rule above refuses everything
before a lowercase letter because `᾿ς` and `῾τὸ` are an apostrophe and a stray
mark. That was right as a blanket rule and wrong for part of the class:
measure_spacing_marks.py splits those tokens four ways and one of the four,
uncomposed_breathing, IS the same thing this file composes for capitals, just
lower down. #35 put the class at 372 tokens. It composes 64 of them, and the
gap is the finding rather than a shortfall:

  250  no precomposed character exists (psili on capital upsilon or rho, the
       same class the first pass left alone rather than half-normalize)
   53  the composed form is attested nowhere in the non-OCR text. ῾οὺκ composes
       to ὁὺκ, which is not a word; the mark there is a quotation mark and the
       word under it is a misaccented οὐκ. Refusing these is what keeps a
       Unicode identity from turning into a guess about Greek.
    5  psili on upsilon or rho, which take the rough breathing by rule. The
       first pass refuses these for capitals; the same reasoning holds here.

Composition never changes the reading, only its encoding, which is why the bar
is lower than for a repair that picks a different word. The one risk is the
classifier being wrong about the mark, and the attestation gate covers it.

Worth saying because the issue says otherwise: composing does NOT fix
῾υμετἑρα. It gives ὑμετἑρα, which still carries the wrong accent, so that token
needs an accent repair as well and is not in the 64.

  python3 scripts/compose_spacing_breathings.py            # report
  python3 scripts/compose_spacing_breathings.py --apply
  python3 scripts/compose_spacing_breathings.py --lowercase
  python3 scripts/compose_spacing_breathings.py --lowercase --apply
  python3 scripts/compose_spacing_breathings.py --lowercase --unapply
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
LOWER_AUDIT = CHANGES / "spacing-breathing-composition.lowercase.json"
sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
def fail(m): raise SystemExit(f"ERROR: {m}")


def compose_word(w: str) -> str | None:
    """A leading spacing breathing folded onto the letter after it.

    None when there is no single precomposed character for the pair, which is
    the capital-upsilon-and-rho case the first pass documents: NFC would leave
    letter plus combining mark and taking that would change the bytes without
    composing anything.
    """
    if len(w) < 2 or w[0] not in COMBINING:
        return None
    merged = unicodedata.normalize("NFC", w[1] + COMBINING[w[0]])
    return merged + w[2:] if len(merged) == 1 else None


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


def lowercase_pass(apply: bool, unapply: bool) -> None:
    """Compose the uncomposed_breathing class measure_spacing_marks.py names."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from measure_spacing_marks import classify  # noqa: E402
    from build_ocr_quality_report import build_attestation  # noqa: E402

    if unapply:
        if not LOWER_AUDIT.exists():
            fail(f"no audit at {LOWER_AUDIT.relative_to(REPO)}")
        rec = json.loads(LOWER_AUDIT.read_text(encoding="utf-8"))
        for blk in rec["files"]:
            fp = REPO / blk["file"]
            if not fp.exists() or sha(fp.read_text(encoding="utf-8")) != blk["sha256_after"]:
                fail(f"{blk['file']} has moved since this audit; reverse that first")
            rows = [json.loads(l) for l in
                    fp.read_text(encoding="utf-8").splitlines() if l.strip()]
            for i, spots in blk["edits"]:
                t = rows[i]["text"]
                # Forward: the offsets are into the original text, so they are
                # only right once everything earlier is back to its own length,
                # and composing always shortens the token by one character.
                for start, was in spots:
                    m = _GK.match(t, start)
                    if not m:
                        fail(f"{blk['file']}: no token at offset {start}")
                    t = t[:start] + was + t[m.end():]
                rows[i]["text"] = t
            fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                  for r in rows), encoding="utf-8")
            if sha(fp.read_text(encoding="utf-8")) != blk["sha256_before"]:
                fail(f"unapply did not restore {blk['file']} byte-for-byte")
        LOWER_AUDIT.unlink()
        print(f"UNAPPLIED: {len(rec['files'])} file(s) restored")
        return

    editions = json.loads((DATA / "corpus_editions.json").read_text(encoding="utf-8"))
    editions = editions["works"] if "works" in editions else editions
    attested, st = build_attestation(editions)
    print(f"attestation: {st['n_unique_forms']:,} forms from {st['n_works']:,} "
          f"non-OCR works")

    held = Counter()
    subs: Counter = Counter()
    blocks, changed = [], 0
    for fp in sorted((DATA / "corpus").glob("*.jsonl")):
        raw = fp.read_text(encoding="utf-8")
        if PSILI not in raw and DASIA not in raw:
            continue
        rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
        edits = []
        for i, r in enumerate(rows):
            text = r.get("text") or ""
            spots, out, prev = [], [], 0
            for m in _GK.finditer(text):
                w = m.group()
                if not w or w[0] not in COMBINING or len(w) < 2:
                    continue
                if classify(w) != "uncomposed_breathing":
                    continue
                t = compose_word(w)
                if t is None:
                    held["no precomposed character"] += 1; continue
                if w[0] == PSILI and unicodedata.normalize("NFD", w[1])[0] in "υΥρΡ":
                    held["psili on upsilon or rho, which take the rough breathing"] += 1
                    continue
                if t not in attested:
                    held["composed form attested nowhere in the non-OCR text"] += 1
                    continue
                spots.append([m.start(), w])
                out.append(text[prev:m.start()] + t); prev = m.end()
                subs[f"{w} -> {t}"] += 1
            if not spots:
                continue
            new = "".join(out) + text[prev:]
            if len(_GK.findall(new)) != len(_GK.findall(text)):
                fail(f"{fp.name} {r['locus']}: token count changed")
            edits.append([i, spots]); r["text"] = new; changed += len(spots)
        if edits:
            blocks.append({"file": fp.relative_to(REPO).as_posix(),
                           "sha256_before": sha(raw), "edits": edits,
                           "rows": rows})

    print(f"\n{changed:,} tokens compose, {len(subs)} distinct, in "
          f"{sum(len(b['edits']) for b in blocks):,} rows across {len(blocks)} works")
    for k, n in held.most_common():
        print(f"  held back {n:>4}  {k}")
    for k, n in subs.most_common(8):
        print(f"    {k}   x{n}")
    if not apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if LOWER_AUDIT.exists():
        fail("audit exists; --unapply first")
    for b in blocks:
        fpath = REPO / b["file"]
        fpath.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in b.pop("rows")), encoding="utf-8")
        b["sha256_after"] = sha(fpath.read_text(encoding="utf-8"))
    LOWER_AUDIT.write_text(json.dumps({
        "what": "spacing psili/dasia composed onto the LOWERCASE vowel or rho "
                "after it, for the uncomposed_breathing class only",
        "date": "2026-08-11", "issue": "open-greek/open-greek-corpus#35",
        "decision": "cisco, 2026-08-11",
        "rule": "measure_spacing_marks.classify says the mark is a breathing "
                "(an unbreathed vowel or rho follows, and a dasia does not stand "
                "before a consonant); a single precomposed character exists; the "
                "letter is not upsilon or rho under a psili, which take the rough "
                "breathing; and the composed form is attested in the non-OCR text.",
        "not_a_repair": "composition changes the encoding and never the reading, "
                        "so this does not pick a different word. Where the reading "
                        "is also wrong the token is left alone: ῾υμετἑρα composes "
                        "to ὑμετἑρα, which still carries the wrong accent.",
        "tokens_composed": changed,
        "held_back": dict(held.most_common()),
        "distinct_substitutions": dict(sorted(subs.items())),
        "files": blocks,
        "reverse": "python3 scripts/compose_spacing_breathings.py --lowercase --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {changed:,} tokens, audit {LOWER_AUDIT.relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--lowercase", action="store_true",
                    help="the uncomposed_breathing class before lowercase letters")
    ap.add_argument("--unapply", action="store_true")
    args = ap.parse_args()
    if args.lowercase:
        lowercase_pass(args.apply, args.unapply); return
    if args.unapply:
        fail("--unapply is only implemented for --lowercase")

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
