#!/usr/bin/env python3
"""Give Oecumenius' Acts commentary back the end of its last sentence.

The carve of PG118 ended oecumenius.commentarius-in-acta-apostolorum at locus
PG118.162, which stops on a verb:

    ...Μετὰ γὰρ τὴν τοῦ Κυρίαυ ἀνάληψιν, μεθ ἡμέρας τινὰς ὀλέγας, προχειρίζονται

and the volume residual's locus 163 opens with that verb's subject and object:

    οἱ ἀπόστολοι εἰς διακονίαν Στέφανον καὶ τοὺς ἀμφὶ αὐτόν.

One sentence, "the apostles appoint Stephen and those with him to the
diaconate", with the subject in one file and the verb in another. What follows
in the same row is the rest of that chronology, Stephen stoned, Paul called, down
to Paul beheaded in Nero's thirteenth year. 70 Greek tokens of a served work
sitting under a volume urn, which is why nobody could cite the end of it.

The row is not moved whole. Its last 47 characters are a display line,
ΔΙΗ Γ Η Σ ΙΣ ΠΕΡΙ ΝΑΚΚΑΤΙΟ ΒΕ ΡΓνΟ ΡΑΟ ΑΡΟΘΤΟΙΟ, whose second half is Latin read
as Greek letter shapes. It heads neither work: Euthalius' Prologos, which starts
immediately after it, carries its own head (ΕΥΘΑΛΙΟΥ ΔΙΑΚΟΝΟΥ ΠΡΟΛΟΓΟΣ, already
carved out of this row at offset 526). So those 11 tokens stay in the residual,
where matter claimed by nothing belongs, and the plan's description of the whole
residual part as "a garbled Latin title line that no work claims" is corrected:
it describes the last 47 characters of 525.

The cut is at a space, checked, because an offset inside a Greek run splits one
word in half. This is its own script because carve_cgpg_volume.py cannot re-open
an applied pass: that pass's audit is its reconstruction trail and rewriting it
would destroy the record while appearing to succeed. Same reason
extend_delectus_legum_back_matter.py exists, one volume over.

  python3 scripts/extend_oecumenius_acts_tail.py            # check only
  python3 scripts/extend_oecumenius_acts_tail.py --apply
  python3 scripts/extend_oecumenius_acts_tail.py --unapply
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
AUDIT = DATA / "corpus_changes" / "oecumenius-acts-tail-extend.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

WORK = CORPUS / "oecumenius.commentarius-in-acta-apostolorum.jsonl"
VOLUME = CORPUS / "cogPG.PG118.jsonl"
LOCUS = "163"
HEAD = "ΔΙΗ Γ Η Σ ΙΣ"          # the display line that stays behind
OPENS = "οἱ ἀπόστολοι εἰς διακονίαν Στέφανον"
PREV_ENDS = "προχειρίζονται"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def rows(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def dump(fp: Path, rs: list[dict]) -> None:
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs),
                  encoding="utf-8")


def tok(s: str) -> int:
    return len(_GK.findall(s or ""))


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
        w, v = rows(WORK), rows(VOLUME)
        if sha(WORK.read_text(encoding="utf-8")) != rec["work"]["sha256_after"]:
            fail("the work file is not in the state this audit recorded")
        w = [r for r in w if str(r["locus"]) != rec["moved_row"]["locus"]]
        for r in v:
            if str(r["locus"]) == LOCUS:
                r["text"] = rec["residual_row"]["text_before"]
        dump(WORK, w)
        dump(VOLUME, v)
        for fp, key in ((WORK, "work"), (VOLUME, "volume")):
            if sha(fp.read_text(encoding="utf-8")) != rec[key]["sha256_before"]:
                fail(f"unapply did not restore {fp.name} byte-for-byte")
        AUDIT.unlink()
        print("UNAPPLIED: both files restored byte-for-byte")
        return

    w_before = WORK.read_text(encoding="utf-8")
    v_before = VOLUME.read_text(encoding="utf-8")
    w, v = rows(WORK), rows(VOLUME)

    last = w[-1]
    if not last["text"].rstrip().endswith(PREV_ENDS):
        fail(f"the work's last row should end {PREV_ENDS!r}, it ends "
             f"{last['text'].rstrip()[-40:]!r}")
    src = next((r for r in v if str(r["locus"]) == LOCUS), None)
    if src is None:
        fail(f"locus {LOCUS} is not in {VOLUME.name}; already applied?")
    text = src["text"]
    if not text.startswith(OPENS):
        fail(f"locus {LOCUS} should open {OPENS!r}, it opens {text[:44]!r}")
    cut = text.find(HEAD)
    if cut < 1:
        fail(f"the display line {HEAD!r} is not in locus {LOCUS}")
    if not text[cut - 1].isspace():
        fail(f"offset {cut} is not at a whitespace boundary")

    moving, staying = text[:cut].rstrip(), text[cut:]
    print(f"work ends   {last['locus']}: ...{last['text'].rstrip()[-46:]!r}")
    print(f"moving      {LOCUS}[:{cut}] {tok(moving):>3} tokens: {moving[:52]!r}...")
    print(f"staying     {LOCUS}[{cut}:] {tok(staying):>3} tokens: {staying!r}")
    if tok(moving) + tok(staying) != tok(text):
        fail("the cut does not conserve tokens")

    if not args.apply:
        print("\nCHECK only (pass --apply to write)")
        return
    if AUDIT.exists():
        fail(f"{AUDIT.relative_to(REPO)} already exists; --unapply first")

    new = {k: last[k] for k in ("urn", "edition", "source", "license")}
    new["locus"] = f"PG118.{LOCUS}"
    new["text"] = moving
    w.append(new)
    for r in v:
        if str(r["locus"]) == LOCUS:
            r["text"] = staying
    dump(WORK, w)
    dump(VOLUME, v)

    AUDIT.write_text(json.dumps({
        "what": "the first 478 characters of Migne PG118 page 163 moved from the "
                "volume residual into oecumenius.commentarius-in-acta-apostolorum",
        "date": "2026-08-09",
        "issue": "open-greek/open-greek-corpus#8",
        "why": "the work's last row ends on the verb προχειρίζονται and this row "
               "opens with its subject and object, οἱ ἀπόστολοι εἰς διακονίαν "
               "Στέφανον. One sentence with its halves in two files, so the end "
               "of a served work was not citable under it.",
        "not_moved": "the last 47 characters, ΔΙΗ Γ Η Σ ΙΣ ΠΕΡΙ ΝΑΚΚΑΤΙΟ ΒΕ ΡΓνΟ "
                     "ΡΑΟ ΑΡΟΘΤΟΙΟ, a display line whose second half is Latin read "
                     "as Greek shapes. It heads neither work, since Euthalius' "
                     "Prologos carries its own head, so it stays in the residual.",
        "corrects": "the PG118 plan entry called this residual part 'a garbled "
                    "Latin title line that no work claims'. That is true of its "
                    "last 47 characters and not of the other 478.",
        "greek_tokens": {"row_before": tok(text), "moved": tok(moving),
                         "left_in_residual": tok(staying)},
        "moved_row": {"locus": new["locus"], "text": moving},
        "residual_row": {"locus": LOCUS, "text_before": text,
                         "text_after": staying},
        "work": {"file": str(WORK.relative_to(REPO)),
                 "sha256_before": sha(w_before),
                 "sha256_after": sha(WORK.read_text(encoding="utf-8"))},
        "volume": {"file": str(VOLUME.relative_to(REPO)),
                   "sha256_before": sha(v_before),
                   "sha256_after": sha(VOLUME.read_text(encoding="utf-8"))},
        "reverse": "python3 scripts/extend_oecumenius_acts_tail.py --unapply",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nAPPLIED: {tok(moving)} tokens -> {WORK.name}, "
          f"audit {AUDIT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
