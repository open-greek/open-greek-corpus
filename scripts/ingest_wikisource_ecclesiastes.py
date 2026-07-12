#!/usr/bin/env python3
"""Serve septuaginta.ecclesiastes from the Greek Wikisource LXX transcription.

Ecclesiastes is the one Septuagint book with no digital text in our open TEI
sources: First1K carries all 56 other tlg0527 books as populated
`1st1K-grc1` editions (Swete, Cambridge 1896), but tlg0527.tlg030 (Ecclesiastes)
is a bare `__cts__.xml` stub upstream and locally. It was previously served from
`sources/swete_digital/` (word + versification CSVs vendored from
github.com/eliranwong/LXX-Swete-1930). That repo is GPL-3.0 and bundles James
Tauber's CCAT-lineage morphology; even though a verbatim transcription of the
public-domain Swete text carries no new copyright, we do not want a GPL repo in
the source table of a public corpus. This ingester drops that dependency.

Source: el.wikisource.org "Εκκλησιαστής" (Παλαιά Διαθήκη / Μετάφραση Ο'), the
proofread verse-keyed LXX transcription. The ancient LXX text is public domain;
the Wikisource contributor layer is CC BY-SA 4.0 (+ GFDL) - no NC. This is the
same open source our downstream LXX (GLAUx / Diorisis) draws on, and matches the
existing Greek Wikisource path in this repo (Proclus, Institutio physica).

Provenance / quality notes (verified 2026-07-11, diff vs the retired eliranwong
Swete text; both total 222 verses across 12 chapters):
  - RECENSION: the Wikisource text is the ecclesiastical / Byzantine-tradition
    LXX (Δαβίδ, rough-breathing Ἱερουσαλήμ, capitalized Θεός, movable-nu), NOT
    Swete's diplomatic Vaticanus text (Δαυείδ). So Ecclesiastes now differs
    orthographically from its 56 First1K Swete siblings - a legitimate variant,
    lemmatization-invariant, not OCR error.
  - VERSIFICATION: the ch6/ch7 boundary differs by one verse. Wikisource follows
    the mainstream numbering (ch6 = 12 verses, ch7 = 29); the retired Swete text
    had ch6 = 11, ch7 = 30. Both total 222. We keep Wikisource's native numbering.
  - The base edition is not named on the page ("Μετάφραση Ο'"); it is a mainstream
    ecclesiastical LXX whose ancient text is public domain.

Markup handled: `{{κ|N}}` verse markers, `===Κεφάλαιον X'===` chapter headers
(Greek alphabetic numerals, "ΣΤ" = 6), and `~...~` text-critical brackets whose
enclosed words are kept (only the tilde marks are stripped). Templates, wikilinks,
HTML comments and the trailing category/interwiki block are removed.

  python3 scripts/ingest_wikisource_ecclesiastes.py            # dry run + report
  python3 scripts/ingest_wikisource_ecclesiastes.py --fetch    # (re)fetch the page
  python3 scripts/ingest_wikisource_ecclesiastes.py --apply    # write corpus file

Then run the id layer + rollup (see Makefile): `make ids` and `make sourcing`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
CACHE = COG / "data" / "cache" / "wikisource" / "ecclesiastes"

SLUG = "septuaginta.ecclesiastes"
EDITION = "wikisource-lxx-ecclesiastes"
SOURCE = "wikisource"
LICENSE = "PD (ancient LXX text); Wikisource transcription CC BY-SA 4.0"
SECONDARY = COG / "data" / "corpus_secondary" / f"{SLUG}.jsonl"
# The whole-volume Swete OCR placeholder for this book was demoted to secondary
# rank earlier; keep its audit note pointing at the CURRENT served source so it
# does not go stale when the primary source changes.
DISPLACE_REASON = ("whole-volume Swete vol.2 placeholder: 12 books served from "
                   "first1k under their own slugs, Ecclesiastes now served from "
                   "the Greek Wikisource transcription")
PAGE_TITLE = "Εκκλησιαστής"
PAGE_URL = "https://el.wikisource.org/wiki/" + urllib.parse.quote(PAGE_TITLE)

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
# Chapter numeral -> int (chapters 1..12; "ΣΤ" is the digraph for 6).
_CHAP = {"Α": 1, "Β": 2, "Γ": 3, "Δ": 4, "Ε": 5, "ΣΤ": 6, "Ϛ": 6, "Ζ": 7,
         "Η": 8, "Θ": 9, "Ι": 10, "ΙΑ": 11, "ΙΒ": 12}


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"https://el.wikisource.org/wiki/{urllib.parse.quote(PAGE_TITLE)}?action=raw"
    req = urllib.request.Request(url, headers={"User-Agent": "corpus-of-open-greek/ingest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    (CACHE / "eccl.wiki").write_text(text, encoding="utf-8")
    print(f"fetched {len(text):,} bytes -> {(CACHE / 'eccl.wiki').relative_to(COG)}")


def clean(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"\{\{[^{}]*\}\}", " ", text)           # residual templates
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)  # [[a|b]] -> b
    text = re.sub(r"\[\[[^\]]*\]\]", " ", text)           # [[a]] / categories / interwiki
    text = re.sub(r"''+", "", text)                        # wiki bold/italic
    text = text.replace("~", " ")                          # text-critical brackets: keep words
    return " ".join(text.split())


def parse_verses() -> list[tuple[str, str]]:
    src = CACHE / "eccl.wiki"
    if not src.exists():
        raise SystemExit(f"ABORT: {src.relative_to(COG)} missing; run --fetch")
    wt = src.read_text(encoding="utf-8")
    parts = re.split(r"===\s*Κεφάλαιον\s+([^=]+?)\s*===", wt)
    out: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        label = parts[i].replace("'", "").replace("ʹ", "").strip()
        ch = _CHAP.get(label)
        if ch is None:
            raise SystemExit(f"ABORT: unrecognized chapter numeral {label!r}")
        body = parts[i + 1]
        vs = re.split(r"\{\{κ\|(\d+)\}\}", body)
        for j in range(1, len(vs), 2):
            v = int(vs[j])
            txt = clean(vs[j + 1])
            if txt:
                out.append((f"{ch}.{v}", txt))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="(re)fetch the wikisource page")
    ap.add_argument("--apply", action="store_true", help="write the corpus file")
    args = ap.parse_args()
    if args.fetch:
        fetch()
    verses = parse_verses()
    ntok = sum(1 for _l, t in verses for w in t.split() if _GK.search(w))
    chaps = sorted({int(l.split(".")[0]) for l, _t in verses})
    per = {c: sum(1 for l, _t in verses if int(l.split(".")[0]) == c) for c in chaps}
    print(f"{'' if args.apply else 'DRY '}Ecclesiastes: {len(verses)} verses, "
          f"chapters {chaps}, {ntok:,} Greek tokens from {PAGE_URL}")
    print(f"verses/chapter: {per}")
    if not args.apply:
        return
    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dst = CORPUS / f"{SLUG}.jsonl"
    with dst.open("w", encoding="utf-8") as f:
        for locus, text in verses:
            f.write(json.dumps({
                "urn": SLUG, "edition": EDITION, "locus": locus,
                "source": SOURCE, "license": LICENSE, "text": text,
                "provenance": {"page": PAGE_TITLE, "url": PAGE_URL, "fetched": fetched},
            }, ensure_ascii=False) + "\n")
    print(f"wrote {len(verses)} verse records -> {dst.relative_to(COG)} "
          f"(edition {EDITION}); now run `make ids` and `make sourcing`")
    # Keep the demoted whole-volume placeholder's audit note current (it named the
    # now-retired digital Swete transcription).
    if SECONDARY.exists():
        rows = [json.loads(l) for l in SECONDARY.read_text(encoding="utf-8").splitlines() if l.strip()]
        for r in rows:
            r["secondary_reason"] = DISPLACE_REASON
        with SECONDARY.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"refreshed secondary_reason on {len(rows)} rows -> {SECONDARY.relative_to(COG)}")


if __name__ == "__main__":
    main()
