#!/usr/bin/env python3
"""Import the reviewed Ficker 1911 Alexius decree; every edit is reversible.

The pinned source is retained verbatim in the change archive. Run without
--apply to inspect the candidate. --uncorrected --out FILE reconstructs the
original page text from the same source, without altering the served edition.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/ingest_reviews/greek-library-alexius.json"
SOURCE = ROOT / "sources/greek_library/pilot/tlg9516.tlg002.local001.json.gz"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate(source, review, corrected=True):
    raw = source.read_bytes()
    if digest(raw) != review["source_sha256"]:
        raise ValueError("Source changed after review")
    document = json.loads(gzip.decompress(raw))
    pages = {}
    for section in document["sections"]:
        page = int(section["label"].removeprefix("Page ")) - 5
        blocks = section.get("blocks", [])
        if section.get("children") or any(b.get("type") != "paragraph" for b in blocks):
            raise ValueError("Unexpected source structure")
        pages[page] = "\n".join(b["text"] for b in blocks)
    if sorted(pages) != review["printed_pages"]:
        raise ValueError("Page range changed after review")
    original = copy.deepcopy(pages)
    folios = {}
    if corrected:
        for change in review["corrections"]:
            page, before, after = change["page"], change["original"], change["corrected"]
            if pages[page].count(before) != 1:
                raise ValueError("Correction is not uniquely located")
            pages[page] = pages[page].replace(before, after)
        for join in review["page_joins"]:
            left, right = join["left_page"], join["right_page"]
            if not pages[left].endswith(join["left"]) or not pages[right].startswith(join["right"]):
                raise ValueError("Page-join evidence no longer matches")
            pages[left] = pages[left][:-len(join["left"])] + join["joined"]
            pages[right] = pages[right][len(join["right"]):].lstrip()
        for page in pages:
            markers = [m.start() for m in re.finditer("/", original[page])]
            names = review["folio_markers"].get(str(page), [])
            if len(markers) != len(names):
                raise ValueError(f"Unreviewed folio markers on page {page}")
            folios[page] = [{"folio": name, "source_text_offset": offset}
                            for name, offset in zip(names, markers)]
            pages[page] = " ".join(pages[page].replace("/", "").split())
    rows = [{"urn": review["slug"], "edition": review["edition"],
             "locus": f"ficker1911_{page:04d}.1", "source": "greek_library", "license": review["license"],
             "language": "grc", "text": text,
             "source_url": review["scan_url"], "source_provider_id": review["source_id"],
             **({"corrections": ["manual"]} if corrected and text != original[page] else {})}
            for page, text in sorted(pages.items())]
    changes = [{"locus": f"ficker1911_{page:04d}.1", "original_text": original[page],
                "corrected_text": pages[page], "source_folio_markers": folios.get(page, []),
                "evidence": f"Manual inspection of Ficker 1911, printed page {page}; page joins and folio markers are specified in the review input.",
                "evidence_source": "scan:" + review["scan_sha256"],
                "date": review["review_date"]}
               for page in sorted(pages) if pages[page] != original[page]]
    return rows, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--review", type=Path, default=REVIEW)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--uncorrected", action="store_true")
    args = parser.parse_args()
    if args.uncorrected and (args.apply or args.out is None):
        parser.error("--uncorrected requires an explicit --out and cannot use --apply")
    review = json.loads(args.review.read_text())
    rows, changes = generate(args.source, review, not args.uncorrected)
    encoded = ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode()
    if args.out:
        if args.out.resolve().is_relative_to((ROOT / "data/corpus").resolve()) and not args.apply:
            parser.error("Writing served text requires --apply")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(encoded)
    if args.apply:
        destination = ROOT / "data/corpus" / (review["slug"] + ".jsonl")
        archive = ROOT / "data/corpus_changes/alexius-ficker-1911"
        if destination.exists() and destination.read_bytes() != encoded:
            previous_audit = archive / "changes.json"
            if (not previous_audit.exists() or
                    json.loads(previous_audit.read_text())["new_sha256"] != digest(destination.read_bytes())):
                raise ValueError("Refusing to overwrite unaudited changes to the served edition")
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "source.json.gz").write_bytes(args.source.read_bytes())
        (archive / "changes.json").write_text(json.dumps({
            "schema_version": 1, "work": review["slug"], "source_sha256": review["source_sha256"],
            "new_sha256": digest(encoded), "review_sha256": digest(args.review.read_bytes()),
            "source_url": review["source_url"], "scan_url": review["scan_url"],
            "scan_sha256": review["scan_sha256"], "date": review["review_date"],
            "generated_by": "scripts/ingest_greek_library_alexius.py",
            "reversal": "Run this importer with --source data/corpus_changes/alexius-ficker-1911/source.json.gz --uncorrected --out FILE to recover the source page text. Remove the newly imported work to undo the addition.",
            "changes": changes}, ensure_ascii=False, indent=2) + "\n")
        destination.write_bytes(encoded)
    print(json.dumps({"work": review["slug"], "rows": len(rows),
                      "greek_words": sum(len(r["text"].split()) for r in rows),
                      "changed_pages": len(changes), "sha256": digest(encoded),
                      "applied": args.apply}))


if __name__ == "__main__":
    main()
