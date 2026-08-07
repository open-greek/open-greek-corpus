#!/usr/bin/env python3
"""Move the Delectus legum's back matter into it, from the PG113 residual.

The pass-3 carve of PG113 ended the Delectus legum compendiarius at locus 283
because locus 284's tail reads ΛΕΟΥΟΕΙ ΘΑΟΤΗΜ, which I read as the head of a
following work. The page scans say otherwise: it is LECTORI SALUTEM, this work's
own. Columns 545-546 are still under the DELECTUS LEGUM running head and carry
its ΤΩ ΑΝΑΓΝΩΣΤΗ ΧΑΙΡΕΙΝ note ("Ἐνταῦθα τέλος ἔσχε τὸ ἓν τῶν ἀντιγράφων τῆς
ἐπανορθώσεως τῶν νόμων Λέοντος καὶ Κωνσταντίνου") and the index of its tituli 29
to 59. Constantine VII's Novellae start after that, at column 549, and are
carved separately.

So loci 284 and 285 are the Delectus's back matter and belong with it. This
exists as its own script because carve_cgpg_volume.py cannot re-open a pass it
has already applied: its audit record is the reconstruction trail for that pass
and must not be rewritten, and its append mode refuses a second append of the
same volume prefix, which is the guard that stops a volume being double-counted.

Reverse: drop the two rows carrying loci PG113.284 and PG113.285 from the
Delectus file, strip the "PG113." prefix from their loci, and re-insert them into
data/corpus/cogPG.PG113.jsonl sorted by locus. The audit record holds both files'
sha256 before and after, and the rows verbatim.

  python3 scripts/extend_delectus_legum_back_matter.py            # check only
  python3 scripts/extend_delectus_legum_back_matter.py --apply
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
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

VOL = "PG113"
SRC = CORPUS / f"cogPG.{VOL}.jsonl"
SLUG = "anonymi-delectus-legum.delectus-legum-compendiarius"
DEST = CORPUS / f"{SLUG}.jsonl"
MOVE = (284, 285)

# Asserted before anything is written. A move that ran on the wrong rows would be
# invisible afterwards, so the shape of both sides is pinned first.
EXPECT_MOVE_ROWS, EXPECT_MOVE_TOKENS = 2, 631
EXPECT_DEST_ROWS, EXPECT_DEST_TOKENS = 46, 17_014
# The two things on those rows that identify them as this work's back matter.
PROBES = ("ΑΝΑΓΝΩΣΤΗ", "Ἐνταῦθα τέλος ἔσχε")


def tokens(rows: list[dict]) -> int:
    return sum(len(_GK.findall(r.get("text") or "")) for r in rows)


def read(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]


def page(locus) -> int:
    """The Migne column, from either locus form.

    The residual keys rows as "284"; a carved work keys them as "PG113.284",
    since the carve prefixes the volume so the page identity survives the move.
    Both have to be read here, because this compares the two files.
    """
    s = str(locus)
    if s.startswith(f"{VOL}."):
        s = s[len(VOL) + 1:]
    return int(s.split(".")[0])


def locus_key(locus):
    return tuple(int(p) if p.isdigit() else 0 for p in str(locus).split("."))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not SRC.exists() or not DEST.exists():
        raise SystemExit("expected both cogPG.PG113.jsonl and the Delectus file")
    src_rows = read(SRC)
    dest_rows = read(DEST)

    if any(page(r["locus"]) in MOVE for r in dest_rows):
        print(f"{DEST.name} already holds {MOVE}; already applied")
        raise SystemExit(0)

    moving = [r for r in src_rows if page(r["locus"]) in MOVE]
    staying = [r for r in src_rows if page(r["locus"]) not in MOVE]
    if (len(moving), tokens(moving)) != (EXPECT_MOVE_ROWS, EXPECT_MOVE_TOKENS):
        raise SystemExit(f"refusing: expected {EXPECT_MOVE_ROWS} rows / "
                         f"{EXPECT_MOVE_TOKENS} tokens to move, found "
                         f"{len(moving)} / {tokens(moving)}")
    if (len(dest_rows), tokens(dest_rows)) != (EXPECT_DEST_ROWS, EXPECT_DEST_TOKENS):
        raise SystemExit(f"refusing: {DEST.name} is not the file this was measured "
                         f"against ({len(dest_rows)} rows / {tokens(dest_rows)})")
    body = " ".join(r.get("text") or "" for r in moving)
    for probe in PROBES:
        if probe not in body:
            raise SystemExit(f"refusing: {probe!r} not in the rows being moved; "
                             f"these are not the Delectus's back matter")

    print(f"moving {len(moving)} rows / {tokens(moving):,} tokens "
          f"({', '.join(str(page(r['locus'])) for r in moving)}) "
          f"into {SLUG}")
    print(f"  {DEST.name}: {len(dest_rows)} rows -> {len(dest_rows) + len(moving)}")
    print(f"  {SRC.name}:  {len(src_rows)} rows -> {len(staying)}")
    if not args.apply:
        print("\ncheck only; nothing written. Re-run with --apply.")
        return

    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (SRC, DEST)}
    archived = [dict(r) for r in moving]
    rekeyed = []
    for r in moving:
        nr = dict(r)
        nr["urn"] = SLUG
        nr["locus"] = f"{VOL}.{r['locus']}"
        rekeyed.append(nr)
    out = sorted(dest_rows + rekeyed, key=lambda r: locus_key(r["locus"]))
    DEST.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out),
                    encoding="utf-8")
    SRC.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in staying),
                   encoding="utf-8")

    (CHANGES / f"{SLUG}.back-matter-extend.json").write_text(json.dumps({
        "what": f"loci {MOVE[0]}-{MOVE[1]} moved from cogPG.{VOL} into {SLUG}",
        "date": "2026-08-07",
        "issue": "open-greek/open-greek-corpus#8",
        "why": "the pass-3 carve ended this work one row early. Locus 284's tail "
               "reads ΛΕΟΥΟΕΙ ΘΑΟΤΗΜ, which was read as a following work's head; "
               "the page scans show it is LECTORI SALUTEM, this work's own. "
               "Columns 545-546 are still under the DELECTUS LEGUM running head "
               "and carry the ΤΩ ΑΝΑΓΝΩΣΤΗ ΧΑΙΡΕΙΝ note and the index of tituli "
               "29-59. Constantine VII's Novellae begin after it at column 549.",
        "not_done_by_the_carve_script": "carve_cgpg_volume.py cannot re-open an "
               "applied pass: its audit is that pass's reconstruction trail and "
               "must not be rewritten, and its append mode refuses a second "
               "append of the same volume prefix.",
        "rows_moved": len(moving), "tokens_moved": tokens(moving),
        "sha256_before": before,
        "sha256_after": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (SRC, DEST)},
        "archived_rows": archived,
        "reverse": "drop the rows whose locus is PG113.284 or PG113.285 from the "
                   "work file, strip the 'PG113.' prefix from their loci, and "
                   "re-insert them into data/corpus/cogPG.PG113.jsonl sorted by "
                   "locus; the rows are held verbatim in archived_rows.",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\naudit -> data/corpus_changes/{SLUG}.back-matter-extend.json")


if __name__ == "__main__":
    main()
