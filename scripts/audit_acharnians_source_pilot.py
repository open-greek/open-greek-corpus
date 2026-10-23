#!/usr/bin/env python3
"""Reproduce the frozen ten-page Dübner source/role pilot, without text edits.

Prepare from the pinned public PDF and scan XML, then check offline with the
standard library. PyMuPDF 1.28.2 is required only for source rendering.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

from acharnians_pilot_observations import OBSERVATIONS, PAGES, REGIONS, SELECTION

ROOT = Path(__file__).resolve().parents[1]
SLUG = "scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii"
PRIMARY = f"data/corpus/{SLUG}.jsonl"
BUNDLE = "data/audits/acharnians-source-pilot"
REPORT = BUNDLE + "/report.json"
DOC = "docs/acharnians-source-pilot.md"
BASELINE_COMMIT = "94d01d91762da7026bd89b6862db037d5dc1c92b"
BASELINE_SHA = "14736ad45cb79e53f6f6eb64160dc92d1aebe9b2f26ed28ae5ab2490834f38e3"
SOURCE_URL = "https://archive.org/details/scholiagraecaina00dbuoft"
DOWNLOAD_URL = "https://archive.org/download/scholiagraecaina00dbuoft/"
PDF_NAME = "scholiagraecaina00dbuoft.pdf"
PDF_SHA = "9d960c70b833f73b3871701775c557a6db1472cc95a04bea8f35054922715c07"
SCAN_NAME = "scholiagraecaina00dbuoft_scandata.xml"
SCAN_SHA = "dbfc7cfd4f08864a154813ca3129cd04359865da8d16f31812060f15e1beebbb"
CATALOG_ROW_SHA = "fcd1390c409b2feeec0535f9fa01d34371a3805838f249a5bf83e2726131e801"
MANIFEST_SHA = "70ada1a9cbe310641aa05b61e27fb60e957f0c98456aadc27a941a599d20f20c"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
LOCUS = re.compile(r"scholia_aristoph_dubner_(\d{4})\.(\d+)\Z")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def pinned(raw, expected, label):
    if sha(raw) != expected:
        raise ValueError(f"{label} does not match the frozen source pin")
    return raw


def scan_pages(raw):
    pinned(raw, SCAN_SHA, "Scan XML")
    pages = [p for p in ET.fromstring(raw).findall(".//pageData/page")
             if p.findtext("addToAccessFormats") != "false"]
    if len(pages) != 776:
        raise ValueError("Scan access-page inventory changed")
    return pages


def prepare(root, pdf, scan):
    import pymupdf
    if pymupdf.VersionBind != "1.28.2":
        raise ValueError("Source rendering requires PyMuPDF 1.28.2")
    pdf_raw = pinned(Path(pdf).read_bytes(), PDF_SHA, "PDF")
    scan_raw = Path(scan).read_bytes()
    pages = scan_pages(scan_raw)
    baseline = pinned((root / PRIMARY).read_bytes(), BASELINE_SHA, "Current primary")
    with (root / "data/corpus_catalog.tsv").open() as stream:
        catalog = next(r for r in csv.DictReader(stream, delimiter="\t") if r["slug"] == SLUG)
    catalog_raw = pinned(encoded(catalog), CATALOG_ROW_SHA, "Baseline catalog row")
    files = {"baseline.jsonl.gz": gzip.compress(baseline, mtime=0),
        "catalog-row.json": catalog_raw, "scandata.xml": scan_raw}
    page_records = []
    with pymupdf.open(stream=pdf_raw, filetype="pdf") as document:
        if len(document) != len(pages):
            raise ValueError("PDF and scan inventory disagree")
        for number, _, _ in PAGES:
            page = document[number - 1]
            png = f"page-{number:04d}.png"
            text = f"page-{number:04d}-tesseract.txt"
            files[png] = page.get_pixmap(dpi=150, alpha=False).tobytes("png")
            files[text] = page.get_text().encode()
            item = pages[number - 1]
            page_records.append({"pdf_page": number, "leaf": int(item.attrib["leafNum"]),
                "printed_page": item.findtext("pageNumber"), "image": png,
                "ocr_text": text, "pdf_points": list(page.rect),
                "source_url": SOURCE_URL + f"/page/n{item.attrib['leafNum']}/mode/1up"})
    manifest = {"schema_version": 1, "source_url": SOURCE_URL,
        "pdf": {"url": DOWNLOAD_URL + PDF_NAME, "sha256": PDF_SHA, "pages": 776},
        "scan": {"url": DOWNLOAD_URL + SCAN_NAME, "sha256": SCAN_SHA},
        "baseline": {"commit": BASELINE_COMMIT, "path": PRIMARY, "sha256": BASELINE_SHA},
        "render": {"pymupdf": "1.28.2", "dpi": 150, "alpha": False},
        "pages": page_records,
        "files": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in sorted(files.items())}}
    files["manifest.json"] = encoded(manifest)
    pinned(files["manifest.json"], MANIFEST_SHA, "Reproduced manifest")
    target = root / BUNDLE
    target.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        path = target / name
        if name != "manifest.json" and path.exists() and path.read_bytes() != raw:
            raise ValueError("Refusing to overwrite different evidence: " + name)
        path.write_bytes(raw)
    print("Source manifest SHA256:", sha(files["manifest.json"]))


def load_bundle(root):
    bundle = root / BUNDLE
    raw = pinned((bundle / "manifest.json").read_bytes(), MANIFEST_SHA, "Source manifest")
    manifest = json.loads(raw)
    for name, spec in manifest["files"].items():
        path = Path(name)
        if path.is_absolute() or len(path.parts) != 1:
            raise ValueError("Unsafe evidence path")
        value = (bundle / path).read_bytes()
        pinned(value, spec["sha256"], name)
        if len(value) != spec["bytes"]:
            raise ValueError("Evidence size changed: " + name)
    pages = scan_pages((bundle / "scandata.xml").read_bytes())
    for entry in manifest["pages"]:
        page = pages[entry["pdf_page"] - 1]
        if entry["leaf"] != int(page.attrib["leafNum"]) or entry["printed_page"] != page.findtext("pageNumber"):
            raise ValueError("PDF-to-scan mapping changed")
    baseline = pinned(gzip.decompress((bundle / "baseline.jsonl.gz").read_bytes()), BASELINE_SHA, "Archived primary")
    rows = [json.loads(line) for line in baseline.splitlines()]
    return manifest, rows


def page_number(row):
    match = LOCUS.fullmatch(row["locus"])
    if not match:
        raise ValueError("Unexpected locus: " + row["locus"])
    return int(match.group(1))


def counter(rows):
    return Counter(token for row in rows for token in GREEK.findall(row["text"]))


def summary(rows):
    counts = counter(rows)
    return {"rows": len(rows), "greek_tokens": sum(counts.values()), "greek_types": len(counts),
        "source_pages_with_rows": len({page_number(row) for row in rows})}


def diagnostics(rows):
    mixed = []
    suffixes = []
    for row in rows:
        for match in re.finditer(r"[^\W\d_]+", row["text"]):
            word = match.group()
            if GREEK.search(word) and re.search("[A-Za-z]", word):
                mixed.append({"locus": row["locus"], "form": word})
        for match in re.finditer(r"[Ͱ-Ͽἀ-῿̀-ͯ]+[0-9]+", row["text"]):
            suffixes.append({"locus": row["locus"], "form": match.group()})
    return {"non_nfc_rows": sum(unicodedata.normalize("NFC", r["text"]) != r["text"] for r in rows),
        "mixed_greek_ascii_forms": len(mixed), "mixed_examples": mixed[:10],
        "greek_digit_suffixes": len(suffixes), "digit_suffix_examples": suffixes[:10],
        "internal_print_hyphen_sequences": sum(len(re.findall(r"[Ͱ-Ͽἀ-῿]-[Ͱ-Ͽἀ-῿]", r["text"])) for r in rows),
        "qualification": "Diagnostics include source sigla, references, and print hyphenation; they are candidates, not error counts."}


def build(root=ROOT):
    root = Path(root)
    manifest, rows = load_bundle(root)
    by_locus = {r["locus"]: r for r in rows}
    if len(by_locus) != len(rows):
        raise ValueError("Duplicate primary locus")
    if any(r["urn"] != SLUG or r["cts"] != "urn:cts:greekLit:tlg5014.tlg001" for r in rows):
        raise ValueError("Unexpected work attribution")
    if any(r.get("analysis_text", r["text"]) != r["text"] for r in rows):
        raise ValueError("Baseline has unaccounted lexical exclusions")
    regions = []
    for low, high, key, title in REGIONS:
        part = [r for r in rows if low <= page_number(r) <= high]
        regions.append({"key": key, "title": title, "pdf_pages": [low, high], **summary(part)})
    if sum(p["rows"] for p in regions) != len(rows):
        raise ValueError("Region accounting lost rows")
    result_pages = []
    for (number, role, note), source in zip(PAGES, manifest["pages"], strict=True):
        if number != source["pdf_page"]:
            raise ValueError("Sample page inventory changed")
        part = [r for r in rows if page_number(r) == number]
        ocr = (root / BUNDLE / source["ocr_text"]).read_text()
        a = Counter(unicodedata.normalize("NFC", t).casefold() for t in counter(part).elements())
        b = Counter(unicodedata.normalize("NFC", t).casefold() for t in GREEK.findall(ocr))
        result_pages.append({"pdf_page": number, "printed_page": source["printed_page"],
            "role": role, "observation": note, **summary(part),
            "diagnostics": diagnostics(part), "same_scan_tesseract_greek_tokens": sum(b.values()),
            "unaligned_bag_token_overlap": sum((a & b).values()),
            "source_url": source["source_url"], "image": source["image"]})
    observations = []
    for entry in OBSERVATIONS:
        row = by_locus[entry["locus"]]
        expected = entry.get("occurrences", 1)
        if row["text"].count(entry["original"]) != expected or page_number(row) != entry["page"]:
            raise ValueError("Observation preimage changed: " + entry["id"])
        observations.append({**entry, "source_pdf_sha256": PDF_SHA,
            "baseline_sha256": BASELINE_SHA, "review_date": "2026-10-23", "status": "observed_not_applied"})
    total = summary(rows)
    catalog = json.loads(pinned((root / BUNDLE / "catalog-row.json").read_bytes(),
        CATALOG_ROW_SHA, "Archived catalog row"))
    if (catalog["slug"] != SLUG or catalog["sha256"] != BASELINE_SHA
            or int(catalog["tokens"]) != total["greek_tokens"]
            or int(catalog["passages"]) != total["rows"]):
        raise ValueError("Frozen accounting disagrees with the published catalog row")
    selected = [r for r in rows if page_number(r) in {p[0] for p in PAGES}]
    return {"schema_version": 1, "work": SLUG, "baseline_commit": BASELINE_COMMIT,
        "baseline_sha256": BASELINE_SHA, "baseline_catalog_row_sha256": CATALOG_ROW_SHA,
        "source_manifest_sha256": MANIFEST_SHA,
        "edition": {"editor": "Friedrich Dübner", "title": "Scholia graeca in Aristophanem",
            "publisher": "Ambroise Firmin-Didot", "place": "Paris", "year": 1855, "license": "PD"},
        "measurement_basis": "Greek regex runs [Ͱ-Ͽἀ-῿̀-ͯ]+ in unchanged primary text; matches the published work-token total. Region labels are provisional page scopes, not admitted work identities or final eligibility.",
        "selection": SELECTION, "total": total, "regions": regions, "sample": summary(selected),
        "sample_diagnostics": diagnostics(selected), "pages": result_pages, "observations": observations,
        "source_comparison": "Qwen served text and Tesseract embedded PDF text are separate OCR passes of the same scan. Unaligned bag overlap is not textual agreement or an accuracy score. No independent public edition has been collated; the catalog's Wilson 1975 reference is not an eligible served witness.",
        "qualification": "Ten purposively selected pages were visually inspected for source identity, roles, and extraction failures. They were not exhaustively transcribed or proofread. No population OCR error rate is estimated; 17.0507% unattested is a lookup diagnostic, not an error rate.",
        "corrections_applied": 0}


def markdown(report):
    lines = ["# Acharnians source pilot", "", "The primary labeled as Acharnians scholia contains extracts from throughout the Dübner 1855 volume. This frozen ten-page assessment changes no served text or lexical exports.", "",
        "The title page verifies *Scholia graeca in Aristophanem*, Friedrich Dübner, Paris, Ambroise Firmin-Didot, 1855. The University of Toronto scan is [publicly available](" + SOURCE_URL + "). The pinned PDF has 776 access pages; source XML has 782 leaves, six excluded from access formats. The sampled PDF page numbers match the scan leaf numbers; printed pages are separate.", "", "## Measured source scope", "",
        "| Page region | Served pages | Rows | Greek tokens |", "| --- | ---: | ---: | ---: |"]
    for row in report["regions"]:
        lines.append(f"| {row['title']} (PDF {row['pdf_pages'][0]}–{row['pdf_pages'][1]}) | {row['source_pages_with_rows']:,} | {row['rows']:,} | {row['greek_tokens']:,} |")
    total = report["total"]
    non_ach = total["greek_tokens"] - next(r["greek_tokens"] for r in report["regions"] if r["key"] == "acharnians")
    editorial = sum(r["greek_tokens"] for r in report["regions"] if r["key"] in {"critical_annotation", "indexes"})
    lines += ["", f"All {total['rows']:,} rows and {total['greek_tokens']:,} Greek tokens are accounted for. {non_ach:,} tokens ({non_ach / total['greek_tokens']:.2%}) are outside the Acharnians page block. The critical annotation and indexes contribute {editorial:,} tokens. This does not make the other plays' historical Greek noise. The regions are conservative source-scope measurements, not a finished carve: hypotheses, quoted poets, manuscript sigla, conjectures, and other intra-page roles still need occurrence-level classification.", "", "## Ten inspected pages", "", report["selection"], "", "| PDF / printed page | Source role | Served rows | Greek tokens |", "| --- | --- | ---: | ---: |"]
    for row in report["pages"]:
        printed = row["printed_page"] or "unnumbered"
        lines.append(f"| [{row['pdf_page']} / {printed}](../{BUNDLE}/{row['image']}) | {row['role'].replace('_', ' ')} | {row['rows']} | {row['greek_tokens']} |")
    lines += ["", report["qualification"], "", "## Extraction findings", "",
        "The sampled Acharnians rows retain a truncated heading, an omitted eta in Ἀθηναίοις, mixed Greek/Latin letters, and a false split of τήνελλα into τὴν ελλα. The annotation sample omits an entire printed note and attaches spurious numbers to Greek words. The final index uses three columns, while the old provenance describes a two-column mask. These are distinct problems; a dictionary-frequency correction would not repair the wrong work boundaries or restore omitted source notes.", "",
        "Exact original strings, proposed readings where justified, scan evidence, review date, and baseline/source pins are in `report.json`. They are observations only. No correction was admitted, and no printed variant was selected by an arbitrary vote.", "", report["source_comparison"], "",
        "## Reproduction", "", "Offline verification uses only the standard library:", "", "```sh", "python3 scripts/audit_acharnians_source_pilot.py --check", "python3 scripts/audit_acharnians_source_pilot.py --check-current", "```", "",
        "The first command verifies the frozen audit even after a future source repair. The second also requires the currently served primary to match the assessed baseline. To reproduce the retained images and PDF text layer, download the pinned PDF and scan XML URLs listed in the manifest, then use PyMuPDF 1.28.2:", "", "```sh", "python3 scripts/audit_acharnians_source_pilot.py --prepare \\", "  --source-pdf /path/to/scholiagraecaina00dbuoft.pdf \\", "  --scan-xml /path/to/scholiagraecaina00dbuoft_scandata.xml", "python3 scripts/audit_acharnians_source_pilot.py --check", "```", "",
        "The PDF remains an external cache input; the ten rendered pages, same-scan OCR extracts, scan XML, frozen primary, and published baseline catalog row are retained with checksums. Preparation rejects changed sources, changed current primary or catalog row, or a different renderer; the normal checker needs neither network access nor PDF rendering.", "",
        "## Admission design", "", "The [published source-scope defect](https://github.com/open-greek/open-greek-corpus/issues/102) is the outstanding-work record. A safe repair should establish an edition-wide work/role inventory before spelling review: distinct play scholia and hypotheses; separately attributed grammatical prolegomena; and out-of-line critical annotation and indexes. Preserve all old loci through citation aliases and literal archives. Review intra-page quotations and variants, then measure deduplication against already served works before assigning new identities or counting tokens. Reuse the existing reversible source-role, citation-alias, and lexical-projection gates, with exact replay/undo and source invalidation; do not republish the entire volume under a newly invented author identity.", "",
        "The pilot makes no completeness claim for the Acharnians text and provides no license to replace uncertain readings with a restricted digital edition.", ""]
    return "\n".join(lines).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--scan-xml", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-current", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        if not args.source_pdf or not args.scan_xml:
            parser.error("--prepare requires --source-pdf and --scan-xml")
        prepare(args.root, args.source_pdf, args.scan_xml)
    if args.check_current:
        pinned((args.root / PRIMARY).read_bytes(), BASELINE_SHA, "Current primary")
    report = build(args.root)
    outputs = {REPORT: encoded(report), DOC: markdown(report)}
    for name, raw in outputs.items():
        path = args.root / name
        if args.check or args.check_current:
            if path.read_bytes() != raw:
                raise ValueError("Stale pilot output: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print("Acharnians source pilot is current; no text corrections applied")


if __name__ == "__main__":
    main()
