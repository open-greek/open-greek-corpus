#!/usr/bin/env python3
"""Serve musaeus-grammaticus.hero-et-leander from the Greek Wikisource transcription.

The work is Musaeus Grammaticus, Hero and Leander (tlg4082.tlg001), a ~343-line
late-antique hexameter epyllion. It was previously served from our own Qwen3.6
OCR of Dilthey 1874 (edition ``qwen36-musaeus_dilthey_1874``), but that redo OCR
is broken: the 1868 served rows are not the poem at all (the OCR ran off onto
unrelated prose, e.g. a Passion narrative naming Pilate), only ~4.8k Greek
tokens, and the work sat flagged for OCR cleanup.

There is no need to re-OCR. The complete poem is transcribed on Greek Wikisource
as a single continuous Greek verse text. The ancient poem is public domain; the
Wikisource contributor layer is CC BY-SA 4.0 - no NC. This matches the existing
Greek Wikisource path in this repo (Proclus Institutio physica; Septuagint
Ecclesiastes) and drops the broken OCR from the corpus.

Source: el.wikisource.org "Τα καθ' Ηρώ και Λέανδρον".

Provenance / quality notes (verified 2026-07-12):
  - EDITION: the Wikisource page names NO printed edition ("Μουσαίος, Τα καθ'
    Ηρώ και Λέανδρον"), so this text is NOT tied to Dilthey 1874, Kost 1971, or
    Livrea 1982. It is the same public-domain ancient poem, ingested as a
    Wikisource-sourced PD text, not as a claim on any modern critical edition.
  - COVERAGE: the transcription carries 341 physical verse lines. Line-number
    markers embedded every 5th line (canonical numbering) place a 2-line gap at
    331-332, so the lines are numbered 1..343 with 331 and 332 absent (honestly
    missing from the source, not renumbered away). The incipit (line 1, "Εἰπέ,
    θεά, κρυφίων ἐπιμάρτυρα λύχνον Ἐρώτων") and the closing line 343 ("ἀλλήλων δ'
    ἀπόναντο καὶ ἐν πυμάτῳ περ ὀλέθρῳ.") match the standard text.
  - PUNCTUATION is preserved as transcribed (including the "•" high-dot and the
    "–" parenthetical dashes of the source); only wiki markup is stripped.

Markup handled: the ``{{Τίτλος2|...}}`` title template, ``::``-indented verse
lines, ``'''bold'''``, bare-numeral line-number markers (used to anchor the
canonical numbering, then dropped), and the trailing ``[[Κατηγορία:...]]`` block.

  python3 scripts/ingest_musaeus_hero_leander.py            # dry run + report
  python3 scripts/ingest_musaeus_hero_leander.py --fetch    # (re)fetch the page
  python3 scripts/ingest_musaeus_hero_leander.py --apply    # replace the corpus file

On --apply the broken OCR that was being served is archived verbatim to
data/corpus_changes/ (reversible) and recorded in the audit trail there. Then run
the id layer + rollup (see Makefile): `make ids` and `make sourcing`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
CACHE = COG / "data" / "cache" / "wikisource" / "musaeus"
CHANGES = COG / "data" / "corpus_changes"
NEEDS = COG / "data" / "needs_ocr_cleanup.json"

SLUG = "musaeus-grammaticus.hero-et-leander"
EDITION = "wikisource-musaeus-hero-leander"
SOURCE = "wikisource"
LICENSE = "PD (ancient poem); Wikisource transcription CC BY-SA 4.0"
OLD_EDITION = "qwen36-musaeus_dilthey_1874"
PAGE_TITLE = "Τα καθ' Ηρώ και Λέανδρον"
PAGE_URL = "https://el.wikisource.org/wiki/" + urllib.parse.quote(PAGE_TITLE)
EDITION_NOTE = ("Wikisource page names no printed edition; same public-domain "
                "ancient poem, not tied to Dilthey 1874 / Kost 1971 / Livrea 1982")

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
WIKI = CACHE / "hero_leander.wiki"


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    url = ("https://el.wikisource.org/w/index.php?title="
           + urllib.parse.quote(PAGE_TITLE) + "&action=raw")
    req = urllib.request.Request(url, headers={"User-Agent": "corpus-of-open-greek/ingest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    if "{{Τίτλος2" not in text and "Λέανδρον" not in text:
        raise SystemExit("ABORT: fetched page does not look like the Musaeus text")
    WIKI.write_text(text, encoding="utf-8")
    print(f"fetched {len(text):,} bytes -> {WIKI.relative_to(COG)}")


def parse_lines() -> list[tuple[int, str]]:
    if not WIKI.exists():
        raise SystemExit(f"ABORT: {WIKI.relative_to(COG)} missing; run --fetch")
    expected = 1
    out: list[tuple[int, str]] = []
    for raw in WIKI.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("{{") or s.startswith("[["):          # title template / categories
            continue
        if re.fullmatch(r"\d+", s):                            # line-number marker: anchor
            expected = int(s)
            continue
        if s.startswith("::"):
            t = s.lstrip(":").strip().strip("'").strip()       # drop indent + wiki bold
            t = " ".join(t.split())
            if t:
                out.append((expected, t))
                expected += 1
    nums = [n for n, _ in out]
    if len(set(nums)) != len(nums):
        raise SystemExit("ABORT: non-unique line numbers after anchoring")
    return out


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="(re)fetch the wikisource page")
    ap.add_argument("--apply", action="store_true", help="replace the corpus file")
    args = ap.parse_args()
    if args.fetch:
        fetch()

    lines = parse_lines()
    ntok = sum(1 for _n, t in lines for w in t.split() if _GK.search(w))
    nums = [n for n, _ in lines]
    missing = sorted(set(range(min(nums), max(nums) + 1)) - set(nums))
    print(f"{'' if args.apply else 'DRY '}Musaeus Hero & Leander: {len(lines)} "
          f"verse lines, numbered {min(nums)}..{max(nums)} "
          f"(missing {missing or 'none'}), {ntok:,} Greek tokens")
    print(f"  incipit: {lines[0][1]}")
    print(f"  explicit: {lines[-1][1]}")
    if not args.apply:
        print("DRY RUN - nothing written (use --apply)")
        return

    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dst = CORPUS / f"{SLUG}.jsonl"
    CHANGES.mkdir(parents=True, exist_ok=True)

    # Archive the broken OCR we are replacing (only on the first replacement, so a
    # re-run is idempotent). This is the reversible record of the old served text.
    archive = CHANGES / f"{SLUG}.pre-wikisource-ocr.jsonl"
    old_meta = None
    if dst.exists():
        old_rows = [json.loads(l) for l in dst.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
        old_ed = old_rows[0].get("edition") if old_rows else None
        if old_ed == OLD_EDITION:
            old_meta = {"edition": old_ed, "rows": len(old_rows),
                        "tokens": sum(1 for r in old_rows for w in r.get("text", "").split()
                                      if _GK.search(w)),
                        "sha256": _sha(dst),
                        "archived_to": str(archive.relative_to(COG))}
            archive.write_text(dst.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  archived {len(old_rows)} broken-OCR rows -> {archive.relative_to(COG)}")

    with dst.open("w", encoding="utf-8") as f:
        for locus, text in lines:
            f.write(json.dumps({
                "urn": SLUG, "edition": EDITION, "locus": str(locus),
                "source": SOURCE, "license": LICENSE, "text": text,
                "provenance": {"page": PAGE_TITLE, "url": PAGE_URL,
                               "fetched": fetched, "note": EDITION_NOTE},
            }, ensure_ascii=False) + "\n")
    print(f"wrote {len(lines)} verse lines -> {dst.relative_to(COG)} (edition {EDITION})")

    # Drop the OCR-cleanup flag: the served text is now a clean transcription.
    needs = json.loads(NEEDS.read_text(encoding="utf-8"))
    if SLUG in needs:
        needs.pop(SLUG)
        NEEDS.write_text(json.dumps(needs, ensure_ascii=False, indent=1, sort_keys=True),
                         encoding="utf-8")
        print(f"  removed {SLUG} from needs_ocr_cleanup.json")

    audit = CHANGES / "musaeus-hero-leander-replacement.json"
    audit.write_text(json.dumps({
        "_meta": {
            "change": "replace served text (source swap: broken OCR -> Greek Wikisource)",
            "work": SLUG, "tlg": "tlg4082.tlg001",
            "applied_by": "scripts/ingest_musaeus_hero_leander.py",
            "date": fetched,
            "reversible": ("re-run the ocr pipeline, or restore the archived jsonl in "
                           "this directory, to reinstate the pre-replacement served text"),
        },
        "old": old_meta or {"edition": OLD_EDITION,
                            "note": "already replaced before this run; see git history / archive"},
        "new": {"edition": EDITION, "source": SOURCE, "license": LICENSE,
                "lines": len(lines), "tokens": ntok,
                "numbered": f"{min(nums)}..{max(nums)}", "missing_lines": missing},
        "evidence": (
            "The previous served edition qwen36-musaeus_dilthey_1874 was a broken redo OCR "
            "of Dilthey 1874 (1868 rows of unrelated prose, incl. a Passion narrative naming "
            "Pilate; ~4.8k Greek tokens; flagged for ocr_cleanup). The complete poem is on "
            "Greek Wikisource as continuous verse; incipit and explicit match the standard "
            "text. " + EDITION_NOTE + "."),
        "source": PAGE_URL,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote audit -> {audit.relative_to(COG)}")
    print("now run `make ids` and `make sourcing`")


if __name__ == "__main__":
    main()
