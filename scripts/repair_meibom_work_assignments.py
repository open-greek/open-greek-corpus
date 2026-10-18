#!/usr/bin/env python3
"""Checked page routing for Meibom's 1652 musical anthology (issue 52).

The scan includes eight Greek works, Latin translations, modern commentary,
and repeated scan leaves. This authority is also the OCR crop manifest; page
parity refers to the printed page, not an unchecked arithmetic scan offset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "aristides-quintilianus-music.de-musica"
SOURCE = {
    "url": "https://archive.org/details/bub_gb_JgtAAAAAcAAJ",
    "pdf_sha256": "6e812c8c0647882881ff4f172eed9d92ba2248822d0481815f34b2e0f03754e8",
    "title": "Antiquae musicae auctores septem, Graece et Latine (Meibom 1652)",
    "checked_scan_pages": [5, 53, 60, 65, 138, 139, 197, 201, 222, 223, 246, 247,
        279, 306, 307, 319, 320, 339, 347, 411, 412, 427, 431, 451, 457, 458,
        463, 465, 466, 477, 481, 505, 506, 517, 525, 583, 608, 614, 642, 644,
        650, 700, 701],
    "evidence": "Manual inspection of the volume title, Greek work headings and explicit endings. Printed odd pages put Greek in the left column, even pages in the right. Scan 60 is blank with show-through; its repeated ἡμῖν OCR has no printed source. Gaudentius scan leaves 458-463 repeat 452-457. Aristides leaves 614-619 repeat 608-613 and 650-655 repeat 644-649. The Greek text ends at scan 700 (printed164); scan701 begins Martianus Capella's Latin text. Modern prefatory matter and Meibom's notes are not the ancient authors' text.",
}
RANGES = [
    (65, 138, "aristoxenus-music.elementa-harmonica", 64),
    (201, 222, "cleonides.introductio-harmonica", 200),
    (223, 246, "euclides-geom.sectio-canonis-sp", 200),
    (279, 306, "nicomachus-mathematics.harmonicum-enchiridion", 278),
    (307, 319, "nicomachus-mathematics.excerpta", 278),
    (347, 411, "alypius.isagoge-musica", 346),
    (431, 465, "gaudentius.harmonica-introductio", 430),
    (481, 505, "bacchius-geron.isagoge", 480),
    (525, 700, OLD, 524),
]


def page_assignment(scan_page):
    for start, end, slug, base in RANGES:
        if not start <= scan_page <= end:
            continue
        canonical = scan_page
        if slug == "gaudentius.harmonica-introductio" and scan_page >= 458:
            canonical = scan_page - 6
        if slug == OLD:
            if scan_page >= 614:
                canonical -= 6
            if scan_page >= 650:
                canonical -= 6
        printed = canonical - base
        book = (1 if printed <= 58 else 2 if printed <= 111 else 3) if slug == OLD else None
        return {"work": slug, "scan_page": scan_page, "printed_page": printed,
            "book": book, "greek_column": "left" if printed % 2 else "right",
            "duplicate_scan": (452 <= canonical <= 457 and 458 <= scan_page <= 463)
                or slug == OLD and (614 <= scan_page <= 619 or 650 <= scan_page <= 655)}
    return {"work": "paratext", "scan_page": scan_page,
        "class": "blank_scan" if scan_page in [1, 60] else "edition_paratext"}


def manifest():
    pages = [page_assignment(p) for p in range(1, 911)]
    return {"schema_version": 1, "source": SOURCE,
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/52",
        "pages": pages, "fresh_aristides_pages": [p for p in pages
            if p["work"] == OLD and not p.get("duplicate_scan")]}


def fresh_jobs():
    return {"schema_version": 1,
        "purpose": "Independent Greek-column witnesses for all 164 unique printed pages of Aristides Quintilianus in Meibom 1652; repeated source images are not independent pages.",
        "sources": {"meibom": {"url": "https://archive.org/download/bub_gb_JgtAAAAAcAAJ/bub_gb_JgtAAAAAcAAJ.pdf",
            "sha256": SOURCE["pdf_sha256"], "license": "PD (Meibom 1652)",
            "citation": "Marcus Meibom, Antiquae musicae auctores septem (Amsterdam, 1652)"}},
        "layout_evidence": SOURCE,
        "pages": [{"id": f"meibom-{p['scan_page']:04d}-greek", "source": "meibom",
            "scan_page": p["scan_page"], "printed_page": p["printed_page"],
            "book": p["book"], "greek_column": p["greek_column"],
            "region": [.02, .03, .59, .97] if p["greek_column"] == "left" else [.42, .03, .99, .97],
            "max_side": 2600} for p in manifest()["fresh_aristides_pages"]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-manifest", action="store_true")
    args = ap.parse_args()
    if args.write_manifest:
        path = ROOT / "data/source_layouts/meibom-1652.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest(), ensure_ascii=False, indent=1) + "\n")
        jobs = ROOT / "data/ingest_reviews/meibom-aristides-fresh-witnesses.json"
        jobs.parent.mkdir(parents=True, exist_ok=True)
        jobs.write_text(json.dumps(fresh_jobs(), ensure_ascii=False, indent=1) + "\n")
    print(f"{len(manifest()['fresh_aristides_pages'])} unique Aristides leaves")


if __name__ == "__main__":
    main()
