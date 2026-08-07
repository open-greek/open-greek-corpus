#!/usr/bin/env python3
"""Re-file the Walz VIII Alexander as a witness, not a second primary.

`alexander-rhetoric.de-figuris` (First1K TEI, from Spengel Rhetores Graeci III
7-40) and `alexander-numenius.peri-ton-tes-dianoias-schematon` (our OCR of Walz
Rhetores Graeci VIII 414-486) are one work under two slugs: Alexander Numenius,
Peri schematon (issue #23). Two editions of the same treatise, so under the
decision in #14 the OCR of the public-domain edition is a secondary witness to
the open TEI, not a rival primary.

The evidence is the texts themselves, which is what the issue said would be
needed. They open on the same clause and close on the same one:

  First1K  Ἔστι μὲν οὐχ ἡ τυχοῦσα δυσκολία περὶ τῶν τοῦ λόγου σχημάτων εἰπεῖν
  Walz     Ἔστι μὲν οὐχ ἡ τυχοῦσα δυσκολία περὶ τῶν τοῦ λόγου σχημάτων εἰπεῖν
  First1K  ... οὐ πατὴρ ἦν, μὰ Δία, ἀλλὰ τύραννος.
  Walz     ... οὐ πατὴρ ἦν, μὰ Δία, ἀλλὰ τύραννος.

The 49% 4-gram figure in the issue, which made this look unsettleable, was
comparing unlike things. The Walz slug is not only the treatise: printed 414-420
is a group half-title, an index of figures and Walz's testimonia about Alexander,
and every page from 421 carries an apparatus criticus. That paratext can match
nothing in a Spengel-based text. It is 375 tokens of front matter plus the
apparatus rows inside the body.

Walz's fuller title, ΠΕΡΙ ΤΩΝ ΤΗΣ ΔΙΑΝΟΙΑΣ ΚΑΙ ΤΗΣ ΛΕΞΕΩΣ ΣΧΗΜΑΤΩΝ at printed
421, is where the second slug came from. It is the same treatise named at
greater length, not a second one.

This is the fifth of its class in that volume. The Walz VIII carve already filed
Tiberius, Ps.-Herodian, Trypho I and Trypho II secondary against served First1K
editions; this entry was missed because nobody had yet connected Walz's title to
the work First1K serves.

Audit (data/corpus_changes/):
  alexander-rhetoric.de-figuris.walz-witness-refile.json   record + evidence
  alexander-numenius.peri-ton-tes-dianoias-schematon.pre-witness-refile.jsonl

Reverse: restore the archived pre-witness-refile.jsonl to data/corpus/ under its
old name (its sha256 is in the record) and drop the Walz-witness rows from
data/corpus_secondary/alexander-rhetoric.de-figuris.jsonl, which are the ones
carrying this script's `witness` string.

Idempotent: exits 0 without writing if already applied.

  python3 scripts/refile_walz_alexander_witness.py            # check only
  python3 scripts/refile_walz_alexander_witness.py --apply
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
SECONDARY = DATA / "corpus_secondary"
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

OLD = "alexander-numenius.peri-ton-tes-dianoias-schematon"
NEW = "alexander-rhetoric.de-figuris"
WITNESS = "Rhetores Graeci, vol. VIII, ed. C. Walz (Stuttgart/Tubingen, Cotta, 1835)"
REASON = ("served as alexander-rhetoric.de-figuris from the First1KGreek open TEI "
          "edition (source precedence: open_corpus over our own OCR of a "
          "public-domain edition); this Walz witness is kept, not served. Same work: "
          "the two texts share their opening clause and their closing clause verbatim "
          "(issue #23)")
# What the file must look like before anything is written. A refile that ran on
# the wrong rows would be invisible afterwards, so the shape is asserted first.
EXPECT_ROWS, EXPECT_TOKENS = 485, 10_424
INCIPIT = "Ἔστι μὲν οὐχ ἡ τυχοῦσα δυσκολία"
EXPLICIT = "οὐ πατὴρ ἦν, μὰ Δία, ἀλλὰ τύραννος"


def tokens(rows: list[dict]) -> int:
    return sum(len(_GK.findall(r.get("text") or "")) for r in rows)


def read(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = CORPUS / f"{OLD}.jsonl"
    dest = SECONDARY / f"{NEW}.jsonl"
    if not src.exists():
        print(f"{src.name} is gone; already applied")
        raise SystemExit(0)
    if not (CORPUS / f"{NEW}.jsonl").exists():
        raise SystemExit(f"{NEW} is not served as a primary; refusing to make a "
                         f"witness to nothing")

    rows = read(src)
    tok = tokens(rows)
    if (len(rows), tok) != (EXPECT_ROWS, EXPECT_TOKENS):
        raise SystemExit(f"refusing: expected {EXPECT_ROWS} rows / {EXPECT_TOKENS} "
                         f"tokens, found {len(rows)} / {tok}")
    body = " ".join(r.get("text") or "" for r in rows)
    for label, probe in (("incipit", INCIPIT), ("explicit", EXPLICIT)):
        if probe not in body:
            raise SystemExit(f"refusing: {label} {probe!r} not in {OLD}")
    served = read(CORPUS / f"{NEW}.jsonl")
    served_body = " ".join(r.get("text") or "" for r in served)
    for label, probe in (("incipit", INCIPIT), ("explicit", EXPLICIT)):
        if probe not in served_body:
            raise SystemExit(f"refusing: {label} not in the served {NEW}; the two are "
                             f"not the same work after all")

    prior = read(dest) if dest.exists() else []
    keep = [r for r in prior if r.get("witness") != WITNESS]
    print(f"{OLD}: {len(rows)} rows, {tok:,} tokens")
    print(f"  incipit and explicit both present in {NEW} too")
    print(f"  {dest.name}: {len(prior)} rows now, keeping {len(keep)} from other "
          f"witnesses, adding {len(rows)}")
    if not args.apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return

    before = hashlib.sha256(src.read_bytes()).hexdigest()
    (CHANGES / f"{OLD}.pre-witness-refile.jsonl").write_bytes(src.read_bytes())
    out = []
    for r in rows:
        nr = dict(r)
        nr["urn"] = NEW
        nr["rank"] = "secondary"
        nr["secondary_reason"] = REASON
        nr["witness"] = WITNESS
        out.append(nr)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                            for r in keep + out), encoding="utf-8")
    src.unlink()

    (CHANGES / f"{NEW}.walz-witness-refile.json").write_text(json.dumps({
        "what": f"{OLD} re-filed as a secondary witness on {NEW}",
        "date": "2026-08-06",
        "issue": "open-greek/open-greek-corpus#23",
        "why": "one work under two slugs: Alexander Numenius, Peri schematon, "
               "witnessed by First1K (from Spengel III) and by our OCR of Walz VIII",
        "evidence": {
            "shared_incipit": INCIPIT,
            "shared_explicit": EXPLICIT,
            "walz_title_at_printed_421": "ΠΕΡΙ ΤΩΝ ΤΗΣ ΔΙΑΝΟΙΑΣ ΚΑΙ ΤΗΣ ΛΕΞΕΩΣ "
                                         "ΣΧΗΜΑΤΩΝ, the same treatise at greater "
                                         "length, which is where the second slug "
                                         "came from",
            "why_the_4gram_figure_was_low": "the Walz slug carries paratext the "
                                            "First1K text cannot match: printed "
                                            "414-420 is a half-title, an index of "
                                            "figures and Walz's testimonia (375 "
                                            "tokens), and every page from 421 has an "
                                            "apparatus criticus",
        },
        "rows_moved": len(rows),
        "tokens_moved": tok,
        "source_sha256": before,
        "archived": f"data/corpus_changes/{OLD}.pre-witness-refile.jsonl",
        "reverse": "restore the archived jsonl to data/corpus/ under its old name and "
                   "drop the rows carrying this witness string from the secondary file",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nmoved {len(rows)} rows; audit -> "
          f"data/corpus_changes/{NEW}.walz-witness-refile.json")


if __name__ == "__main__":
    main()
