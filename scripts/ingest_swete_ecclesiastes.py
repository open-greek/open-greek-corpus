#!/usr/bin/env python3
"""Serve Ecclesiastes from the digital Swete transcription and displace the
whole-volume Swete OCR placeholder.

septuaginta.ecclesiastes was a page-keyed OCR of ALL of Swete, The Old
Testament in Greek, vol. II (2nd ed., Cambridge 1896; 847 pp: 1-2 Chronicles,
Esdras, Psalms, Proverbs, Ecclesiastes, Canticum, Job, Wisdom, Sirach, Esther,
Judith, Tobit) - a whole-volume shortcut. Twelve of its thirteen books are
already served from First1K under their own slugs; only Ecclesiastes proper
had no digital text anywhere (the First1K tlg0527.tlg030 file is an empty
stub). This script:

  1. displaces the whole-volume OCR work to corpus_secondary (rank=secondary;
     the qwen36 re-OCR of the full volume stays banked in greek-ocr runs/ for
     any future delivery);
  2. writes Ecclesiastes verse-keyed from the digital transcription as the
     slug's new primary.

Source text: github.com/eliranwong/LXX-Swete-1930 (word + versification CSVs,
vendored under sources/swete_digital/). It transcribes the SAME Swete edition
(provenance: Abram Kidd Amicarelli's BibleWorks module); the repo's GPL
license cannot encumber a verbatim transcription of a PD edition, so the text
is PD. Quality was verified 2026-07-08: 90.7% of words byte-identical to our
qwen36 OCR with nearly all differences being OUR OCR's errors (including a
dropped stichos at Eccl 2:3, present here). Text-critical sigla (U+2E00-2E0F
brackets) are stripped at ingest; punctuation is kept.

  python scripts/ingest_swete_ecclesiastes.py --write   (dry-run without --write)
  then: python scripts/reconcile_corpus_editions.py
"""

from __future__ import annotations

import bisect
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "swete_digital"
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"

SLUG = "septuaginta.ecclesiastes"
EDITION = "swete-ot2-1896-digital"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_SIGLA = re.compile(r"[⸀-⸏]")

DISPLACE_REASON = ("whole-volume Swete vol.2 placeholder: 12 books served from "
                   "first1k under their own slugs, Ecclesiastes now served from "
                   "the digital Swete transcription")


def load_verses():
    words = {}
    for line in (SRC / "swete_words.csv").open(encoding="utf-8"):
        i, t = line.rstrip("\n").split("\t", 1)
        words[int(i)] = t
    vers = []
    for line in (SRC / "swete_versification.csv").open(encoding="utf-8"):
        i, ref = line.rstrip("\n").split("\t", 1)
        vers.append((int(i), ref))
    vers.sort()
    idx = [i for i, _ in vers]
    out = []
    for pos, (start, ref) in enumerate(vers):
        if not ref.startswith("Ecc."):
            continue
        end = idx[pos + 1] if pos + 1 < len(idx) else max(words) + 1
        text = " ".join(words[j] for j in range(start, end) if j in words)
        text = _SIGLA.sub("", text)
        text = " ".join(text.split())
        locus = ref[4:].replace(":", ".")          # Ecc.1:1 -> 1.1
        out.append((locus, text))
    return out


def main() -> None:
    write = "--write" in sys.argv
    verses = load_verses()
    ntok = sum(1 for _l, t in verses for w in t.split() if _GK.search(w))
    print(f"{'' if write else 'DRY '}Ecclesiastes: {len(verses)} verses, "
          f"{ntok:,} Greek tokens from {SRC.relative_to(REPO)}")

    src = CORPUS / f"{SLUG}.jsonl"
    old = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()] \
        if src.exists() else []
    print(f"displacing {SLUG}: {len(old)} rows -> secondary")
    if not write:
        return

    SECONDARY.mkdir(parents=True, exist_ok=True)
    kept = old
    for r in kept:
        r["rank"] = "secondary"
        r["secondary_reason"] = DISPLACE_REASON
    dst = SECONDARY / f"{SLUG}.jsonl"
    with dst.open("a" if dst.exists() else "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with src.open("w", encoding="utf-8") as f:
        for locus, text in verses:
            f.write(json.dumps({
                "urn": SLUG, "edition": EDITION, "locus": locus,
                "source": "swete_digital", "license": "PD", "text": text,
            }, ensure_ascii=False) + "\n")
    print(f"wrote {len(verses)} verse records as {SLUG} primary "
          f"(edition {EDITION}); now run reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
