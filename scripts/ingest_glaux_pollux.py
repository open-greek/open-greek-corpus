#!/usr/bin/env python3
"""Serve julius-pollux.onomasticon from the GLAUx surface text (full 10 books).

Julius Pollux, Onomasticon (tlg0542.tlg001) is a 2nd-century CE Attic-lexicon /
thesaurus in ten books. OGC previously served only a First1KGreek SAMPLE of it:
the TEI file tlg0542.tlg001.1st1K-grc1.xml is a 4.6 KB stub carrying two sections
(2.157-2.158, 111 Greek tokens) - not the work, just a fragment. No open TEI of
the complete Onomasticon exists.

The complete text does exist, openly licensed, in the GLAUx corpus
(github.com/alekkeersmaekers/glaux, xml/0542-001.xml): all ten books, 1,908
sections, ~115k Greek word tokens, morphologically annotated. GLAUx stores the
text as ordered <word> surface forms, each tagged with its printed location
(div_book / div_section, e.g. div_section="2.157"). We reconstruct the running
text per section from those surface forms in document order and serve it, keyed
by the GLAUx section numbers to tlg0542.tlg001 loci. This is an INGEST of an
existing open digital text, not OCR.

Reconstruction (verified reliable, 2026-07-14):
  - LOCUS: div_section is always "book.section" (two integer components) and its
    book prefix always equals div_book (0 mismatches); the 1,908 (book, section)
    pairs are unique (no duplicate loci) and every section's words form a single
    contiguous block in the document. So each locus is unambiguous.
  - ORDER: words within a section keep GLAUx document order (the correct Greek
    word order). Rows are EMITTED in numeric (book, section) order. The document
    happens to serialize three book-6 sections out of sequence (6.146-148 appear
    after 6.149-150), but read in numeric order the content flows correctly
    (6.145 "on one who speaks little" -> 6.146 "on one who speaks much" -> ...),
    confirming the section labels, so numeric order is the right citation order.
  - ORTHOGRAPHY: GLAUx surface forms already use normal medial/final sigma
    (σ/ς), not the lunate ϲ of the First1K stub; forms are normalized to NFC.
  - EDITORIAL TOKENS: GLAUx marks illegible spots with the placeholder form
    "G?" (form_original "[G?]"); these carry no lexical content and are dropped
    (11 tokens). Angle-bracket editorial supplements keep their clean form.
    Artificial (elliptic) treebank tokens are excluded (no surface text).

License: the ancient text is public domain; the GLAUx corpus is distributed
CC BY-SA 4.0 (repo README). GLAUx metadata.txt records this text's source
license as unspecified ("NA"), which is not NonCommercial, so it is admissible
under OGC policy (no CC BY-NC-SA texts).

The First1K stub is retired for this work: on --apply the two stub rows are
archived verbatim to data/corpus_changes/ (reversible) and the work is added to
data/non_tei_authoritative.json so a TEI rebuild (build_corpus_loci.py) never
overwrites the served GLAUx text with the sample again.

  python3 scripts/ingest_glaux_pollux.py            # dry run + report
  python3 scripts/ingest_glaux_pollux.py --apply     # replace the served text

After --apply, run the rollup: `make all` (build_corpus_loci skips this work via
the keep-list, then the yardstick + id layer + sourcing regenerate).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
CHANGES = COG / "data" / "corpus_changes"
NON_TEI = COG / "data" / "non_tei_authoritative.json"
NEEDS = COG / "data" / "needs_ocr_cleanup.json"

SLUG = "julius-pollux.onomasticon"
CTS = "urn:cts:greekLit:tlg0542.tlg001"
TLG = "tlg0542.tlg001"
EDITION = "glaux-0542-001"
SOURCE = "glaux"
LICENSE = "PD (ancient text); GLAUx corpus CC BY-SA 4.0"
OLD_EDITION = "1st1K-grc1"

GLAUX_ID = "0542-001"
GLAUX_REPO = "github.com/alekkeersmaekers/glaux"
# Pinned to the retained GLAUx clone; recorded in provenance for reproducibility.
GLAUX_COMMIT = "b077d8f6ff429a5c7245954bc16bb7d1d7948823"
GLAUX_URL = f"https://{GLAUX_REPO}/blob/master/xml/{GLAUX_ID}.xml"

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")          # any single Greek letter (membership test)
_GKW = re.compile(r"[Ͱ-Ͽἀ-῿]+")        # a Greek word run (token count)
GAP_FORM = "G?"                          # GLAUx illegibility placeholder -> dropped

# Detokenization: join surface forms with single spaces, but hug punctuation the
# way an edition prints it. The Greek word tokens stay space-separated either
# way, so the yardstick token count is unaffected; this only governs readability.
NO_SPACE_BEFORE = set(",.;·)")           # closing punctuation + ano teleia
NO_SPACE_AFTER = set("(")


def glaux_xml_path() -> Path:
    root = os.environ.get("GLAUX_DIR")
    base = Path(root) if root else Path.home() / "Documents" / "glaux"
    return base / "xml" / f"{GLAUX_ID}.xml"


def load_sections(xml_path: Path) -> "OrderedDict[tuple[int, int], list[str]]":
    """(book, section) -> surface forms in document order.

    Mirrors load_glaux_tokens in open-greek-corpus-annotations'
    build_gold_glaux.py: NFC forms, artificial tokens excluded. Additionally
    drops the "G?" illegibility placeholder (no lexical content). Asserts the
    div_section / div_book invariants the reconstruction relies on."""
    if not xml_path.exists():
        raise SystemExit(f"ABORT: GLAUx source missing: {xml_path} "
                         "(set GLAUX_DIR to the glaux checkout)")
    sections: "OrderedDict[tuple[int, int], list[str]]" = OrderedDict()
    dropped_gap = 0
    for _event, el in ET.iterparse(str(xml_path), events=("end",)):
        if el.tag != "word":
            continue
        if el.get("artificial"):
            el.clear()
            continue
        form = unicodedata.normalize("NFC", el.get("form") or "")
        book = (el.get("div_book") or "").strip()
        sect = (el.get("div_section") or "").strip()
        if not form or not book or not sect:
            el.clear()
            continue
        parts = sect.split(".")
        if len(parts) != 2 or parts[0] != book or not parts[1].isdigit():
            raise SystemExit(
                f"ABORT: unexpected div_section {sect!r} (div_book {book!r}); "
                "the reconstruction assumes 'book.section' with matching book")
        if form == GAP_FORM:
            dropped_gap += 1
            el.clear()
            continue
        sections.setdefault((int(book), int(parts[1])), []).append(form)
        el.clear()
    # Contiguity + uniqueness are asserted by the loader's own structure only if
    # we re-check: sections built via setdefault would silently merge a split
    # section, so verify each key's block is contiguous by re-scanning order.
    return sections, dropped_gap


def detok(forms: list[str]) -> str:
    pieces: list[str] = []
    suppress = False
    quote_open = False
    for i, tok in enumerate(forms):
        is_quote = tok == '"'
        opening = is_quote and not quote_open
        closing = is_quote and quote_open
        space = not (i == 0 or suppress or tok in NO_SPACE_BEFORE or closing)
        pieces.append((" " if space else "") + tok)
        suppress = tok in NO_SPACE_AFTER or opening
        if is_quote:
            quote_open = not quote_open
    return "".join(pieces)


def assert_contiguous(xml_path: Path) -> None:
    """Each (book, section) must occupy a single contiguous run in the document;
    otherwise setdefault-based grouping would silently reorder a split section."""
    blocks: list[tuple[int, int]] = []
    last = None
    for _e, el in ET.iterparse(str(xml_path), events=("end",)):
        if el.tag != "word":
            continue
        if el.get("artificial"):
            el.clear()
            continue
        book = (el.get("div_book") or "").strip()
        sect = (el.get("div_section") or "").strip()
        if book and sect and "." in sect:
            key = (int(book), int(sect.split(".")[-1]))
            if key != last:
                blocks.append(key)
                last = key
        el.clear()
    seen = set()
    for k in blocks:
        if k in seen:
            raise SystemExit(
                f"ABORT: section {k} is non-contiguous in the GLAUx document; "
                "running-text reconstruction would be unreliable - not writing")
        seen.add(k)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_rows(sections) -> list[tuple[str, str]]:
    """(locus, text) in numeric (book, section) order."""
    out = []
    for (book, sect) in sorted(sections.keys()):
        text = detok(sections[(book, sect)])
        out.append((f"{book}.{sect}", text))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="replace the served corpus file (default: dry run)")
    args = ap.parse_args()

    xml_path = glaux_xml_path()
    assert_contiguous(xml_path)
    sections, dropped_gap = load_sections(xml_path)
    rows = build_rows(sections)

    books = sorted({b for b, _ in sections})
    ntok = sum(len(_GKW.findall(t)) for _l, t in rows)
    incipit = rows[0][1]
    explicit = rows[-1][1]
    print(f"{'' if args.apply else 'DRY '}GLAUx Pollux Onomasticon: "
          f"{len(books)} books, {len(rows)} sections, {ntok:,} Greek tokens "
          f"(dropped {dropped_gap} 'G?' gap placeholders)")
    print(f"  first locus {rows[0][0]}: {incipit[:90]}")
    print(f"  last  locus {rows[-1][0]}: ...{explicit[-70:]}")
    if not (incipit.startswith("Ἰούλιος Πολυδεύκης Κομμόδῳ Καίσαρι χαίρειν")):
        raise SystemExit("ABORT: incipit is not the Commodus dedication; "
                         "GLAUx source looks wrong - not writing")
    if not args.apply:
        print("DRY RUN - nothing written (use --apply)")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dst = CORPUS / f"{SLUG}.jsonl"
    CHANGES.mkdir(parents=True, exist_ok=True)

    # 1. Archive the retired First1K stub verbatim (idempotent: only when the
    #    file on disk is still the 1st1K-grc1 stub). Reversible record.
    archive = CHANGES / f"{SLUG}.pre-glaux-stub.jsonl"
    old_meta = None
    if dst.exists():
        old_rows = [json.loads(l) for l in dst.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
        old_ed = old_rows[0].get("edition") if old_rows else None
        if old_ed == OLD_EDITION:
            old_meta = {
                "edition": old_ed,
                "source": old_rows[0].get("source"),
                "rows": len(old_rows),
                "loci": [r.get("locus") for r in old_rows],
                "tokens": sum(len(_GKW.findall(r.get("text", ""))) for r in old_rows),
                "sha256": _sha(dst),
                "archived_to": str(archive.relative_to(COG)),
            }
            archive.write_text(dst.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  archived {len(old_rows)} stub rows -> {archive.relative_to(COG)}")

    # 2. Write the served GLAUx text.
    prov = {"source_repo": GLAUX_REPO, "glaux_id": GLAUX_ID,
            "commit": GLAUX_COMMIT[:7]}
    with dst.open("w", encoding="utf-8") as f:
        for locus, text in rows:
            f.write(json.dumps({
                "urn": SLUG, "edition": EDITION, "locus": locus,
                "source": SOURCE, "license": LICENSE, "text": text,
                "provenance": prov,
            }, ensure_ascii=False) + "\n")
    print(f"  wrote {len(rows)} sections -> {dst.relative_to(COG)} (edition {EDITION})")

    # 3. Protect the served text from the TEI rebuild (keep-list upsert).
    keep = json.loads(NON_TEI.read_text(encoding="utf-8")) if NON_TEI.exists() else {}
    keep[SLUG] = {
        "kept_source": SOURCE,
        "kept_edition": EDITION,
        "reason": ("Full 10-book Onomasticon (~115k Greek tokens, 1,908 sections) "
                   "reconstructed from the GLAUx surface text. first1k "
                   "tlg0542.tlg001.1st1K-grc1.xml is a 2-section sample (111 "
                   "tokens); keep the GLAUx text primary."),
        "as_of": today,
    }
    NON_TEI.write_text(json.dumps(keep, ensure_ascii=False, indent=1, sort_keys=True),
                       encoding="utf-8")
    print(f"  keep-list: {SLUG} -> {NON_TEI.relative_to(COG)}")

    # 4. Clear the stale ocr_cleanup flag (the served text is now complete/clean).
    if NEEDS.exists():
        needs = json.loads(NEEDS.read_text(encoding="utf-8"))
        if SLUG in needs:
            needs.pop(SLUG)
            NEEDS.write_text(
                json.dumps(needs, ensure_ascii=False, indent=1, sort_keys=True),
                encoding="utf-8")
            print(f"  removed {SLUG} from {NEEDS.relative_to(COG)}")

    # 5. Reversible audit + provenance record.
    audit = CHANGES / f"{SLUG}.glaux-full-text.json"
    audit.write_text(json.dumps({
        "_meta": {
            "change": "replace served text (source swap: First1K sample -> GLAUx full text)",
            "work": SLUG, "tlg": TLG, "cts": CTS,
            "applied_by": "scripts/ingest_glaux_pollux.py",
            "date": today,
            "reversible": (
                "restore the archived stub jsonl in this directory and remove "
                f"the {SLUG} entry from data/non_tei_authoritative.json to reinstate "
                "the pre-replacement served text; re-run scripts/ingest_glaux_pollux.py "
                "to regenerate the GLAUx text."),
        },
        "old": old_meta or {
            "edition": OLD_EDITION, "source": "first1k",
            "note": "already replaced before this run; see git history / archived jsonl"},
        "new": {
            "edition": EDITION, "source": SOURCE, "license": LICENSE,
            "books": len(books), "sections": len(rows), "tokens": ntok,
            "incipit": incipit[:120], "explicit": explicit[-120:],
        },
        "provenance": {
            "source": "GLAUx corpus (automatically annotated Ancient Greek)",
            "repo": GLAUX_REPO, "commit": GLAUX_COMMIT,
            "glaux_text_id": GLAUX_ID, "url": GLAUX_URL,
            "source_format": "TEI treebank XML (ordered <word> surface forms)",
            "reference_parser": ("open-greek-corpus-annotations/scripts/"
                                 "build_gold_glaux.py load_glaux_tokens"),
            "method": (
                "running text reconstructed per locus from GLAUx <word> surface "
                "forms (NFC) in document order, keyed by div_book/div_section; "
                "rows emitted in numeric (book, section) order; artificial "
                "(elliptic) tokens and the 'G?' illegibility placeholder dropped"),
            "reconstruction_checks": {
                "div_section_matches_div_book": True,
                "unique_loci": len(rows),
                "all_sections_contiguous": True,
                "gap_placeholders_dropped": dropped_gap,
                "doc_order_note": ("book 6 serializes 6.146-148 after 6.149-150 in "
                                   "the GLAUx document; numeric order is the correct "
                                   "reading/citation order (content confirms it)"),
            },
            "license_note": (
                "ancient text is public domain; GLAUx corpus distributed CC BY-SA "
                "4.0 (repo README). GLAUx metadata.txt SOURCE_LICENSE for this text "
                "is 'NA' (unspecified), which is not NonCommercial, so admissible "
                "under OGC policy."),
            "date": today,
        },
        "evidence": (
            "The previously served edition 1st1K-grc1 is the First1KGreek TEI file "
            "tlg0542.tlg001.1st1K-grc1.xml, a 4.6 KB sample holding only sections "
            "2.157-2.158 (111 Greek tokens). No open TEI of the complete Onomasticon "
            "exists. GLAUx xml/0542-001.xml carries all ten books (1,908 sections, "
            "~115k Greek word tokens); the reconstructed incipit is the Commodus "
            "dedication (Ἰούλιος Πολυδεύκης Κομμόδῳ Καίσαρι χαίρειν) and orthography "
            "uses normal σ/ς."),
        "source_url": GLAUX_URL,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote audit -> {audit.relative_to(COG)}")
    print("now run `make all`")


if __name__ == "__main__":
    main()
