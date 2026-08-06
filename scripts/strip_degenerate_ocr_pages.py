#!/usr/bin/env python3
"""Remove the pages where the OCR model looped instead of reading.

A vision model that loses the page sometimes emits one line over and over until
its budget runs out. Three pages in the served corpus are that, and they are not
bad readings of real text, they are text that is not on the page at all:

  ocr.walz_rhetores_v7pt2 scan 0666       235 of 254 rows read
      `Ἡ ἐπανασύνταξις τῆς ἱστορίας.` under a fabricated ΠΕΡΙΕΧΟΜΕΝΑ, in MODERN
      Greek, about historiography. Walz's Rhetores Graeci has no such page.
  joannes-grammar.ekfrasis-tou-kosmikou-pinakos scan 0004   289 of 293 rows
      `ΕΝ ΤΩΙ ΑΓΩΓΕΙΩΙ ΤΗΣ ΠΑΙΔΕΙΑΣ,`
  alexander-lyric.fragmenta scan 0016     176 of 178 rows
      `ΠΕΡΙ ΤΩΝ ΕΝ ΤΩΙ ΑΙΘΕΡΙ`

Found while carving Walz VII.2, where scan 0666 looked like a contents page and
turned out to be a hallucinated one for a different book entirely.

Only the repeated rows go. The first row or two of these pages is often a real
heading the model read before it lost its footing - `ΛΟΓΙΚΗ`, `ΤΕΤΡΑΔΟΣ Α` - and
dropping a whole page to be rid of a loop would throw that away.

An empty repeated line is left alone. Blank rows repeat on plenty of pages for
ordinary reasons, they carry no tokens, and removing them would be churn rather
than a correction.

  strip_degenerate_ocr_pages.py            # report
  strip_degenerate_ocr_pages.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CHANGES = DATA / "corpus_changes"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

# A page has to be long before repetition means anything: a short page of
# formulaic entries repeats legitimately.
MIN_ROWS = 40
# How many times one line must recur, and what share of the page it must fill.
# The three real cases run 176-289 repeats at 88-99%; the highest innocent page
# found in the corpus is far below both.
MIN_REPEATS = 20
MIN_SHARE = 0.5
# The loop sometimes numbers its own repetitions, so the raw strings all differ:
# Walz VII.2 scan 0666 runs `α) Ἡ ἐπανασύνταξις τῆς ἱστορίας.`, `β) Ἡ
# ἐπανασύνταξις ...` for 235 rows. The enumerator comes off before counting.
_ENUM = re.compile(r"^\s*(?:[Α-Ωα-ω]+|\d+|[ivxlcIVXLC]+)['’ʹ]*\s*[).\]]\s*")
# And it sometimes alternates two lines rather than repeating one: Cyril's
# dialogues have a page of 425 bare `Α` / `Β` speaker labels and no speech at
# all, where every other page in that work carries the label WITH its speech
# (`B Καὶ μάλα.`). A page saying almost nothing distinct is the same failure.
MAX_DISTINCT = 3


def _norm(text: str) -> str:
    return _ENUM.sub("", (text or "").strip())


def page_of(locus: str) -> str:
    return locus.rsplit(".", 1)[0]


def looped_rows(rows: list[dict]) -> tuple[str, list[dict]]:
    """(the repeated line, the rows carrying it) for a page that has one."""
    if len(rows) < MIN_ROWS:
        return "", []
    counts = Counter(_norm(r.get("text")) for r in rows if _norm(r.get("text")))
    if not counts:
        return "", []
    line, n = counts.most_common(1)[0]
    dominated = n >= MIN_REPEATS and n / len(rows) >= MIN_SHARE
    # A page with almost nothing distinct on it, however the repeats are spelled.
    barren = len(counts) <= MAX_DISTINCT and len(rows) >= MIN_ROWS
    if not (dominated or barren):
        return "", []
    if barren and not dominated:
        keep_first = {id(rows[0])}
        return (f"{len(counts)} distinct lines over {len(rows)} rows",
                [r for r in rows if id(r) not in keep_first])
    return line, [r for r in rows if _norm(r.get("text")) == line]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    CHANGES.mkdir(parents=True, exist_ok=True)
    total_rows = total_tokens = 0
    touched = []
    for fp in sorted(CORPUS.glob("*.jsonl")):
        rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        pages: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            pages[page_of(r["locus"])].append(r)
        drop: list[dict] = []
        found = []
        for page, prows in pages.items():
            # To a fixed point. Stripping one repeated line can leave a page that
            # is still degenerate: Cyril's scan 0575 is 213 `Α` and 212 `Β`, and
            # removing the `Α` rows leaves a page that is 99.5% `Β`. Running once
            # would have left that behind and made the script non-idempotent.
            remaining, page_drop = list(prows), []
            while True:
                line, looped = looped_rows(remaining)
                if not looped:
                    break
                if not page_drop:
                    found.append((page, line, len(looped), len(prows)))
                page_drop.extend(looped)
                gone_ids = {id(r) for r in looped}
                remaining = [r for r in remaining if id(r) not in gone_ids]
            if page_drop:
                drop.extend(page_drop)
                found[-1] = (page, found[-1][1], len(page_drop), len(prows))
        if not drop:
            continue
        gone = {id(r) for r in drop}
        kept = [r for r in rows if id(r) not in gone]
        tokens = sum(len(_GK.findall(r.get("text") or "")) for r in drop)
        total_rows += len(drop)
        total_tokens += tokens
        touched.append(fp.stem)
        for page, line, n, of in found:
            print(f"  {fp.stem[:46]:48} {page.split('_')[-1]:>9}  "
                  f"{n:>4}/{of:<4} rows  {line[:40]!r}")

        if not args.apply:
            continue
        before = hashlib.sha256(fp.read_bytes()).hexdigest()
        fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept),
                      encoding="utf-8")
        audit = {
            "what": f"removed looped OCR rows from {fp.stem}",
            "date": "2026-08-06",
            "issue": "open-greek/open-greek-corpus#27",
            "why": "the vision model emitted one line repeatedly instead of reading "
                   "the page; the text is not on the page in any form, so this is "
                   "fabricated content rather than a bad reading",
            "detector": f"a page of at least {MIN_ROWS} rows where one non-empty "
                        f"line recurs at least {MIN_REPEATS} times and fills at "
                        f"least {MIN_SHARE:.0%} of it",
            "pages": [{"page": p, "line": l, "repeats": n, "page_rows": of}
                      for p, l, n, of in found],
            "sha256_before": before,
            "sha256_after": hashlib.sha256(fp.read_bytes()).hexdigest(),
            "rows_before": len(rows),
            "rows_after": len(kept),
            "tokens_removed": tokens,
            "removed_rows": [{"locus": r["locus"], "text": r.get("text")}
                             for r in drop],
            "reverse": "reinsert removed_rows at their loci, in locus order",
        }
        (CHANGES / f"{fp.stem}.looped-ocr-strip.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\n{len(touched)} works, {total_rows:,} looped rows, "
          f"{total_tokens:,} Greek tokens")
    if not args.apply:
        print("report only; re-run with --apply.")


if __name__ == "__main__":
    main()
