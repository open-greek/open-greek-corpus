#!/usr/bin/env python3
"""Pin source-checked Greek body crops for Jahn's 1882 Aristides edition.

Use the first thin apparatus separator below the main Greek text; modern
editorial notes below it are outside the work. The final printed page's index
has its own reviewed boundary. Original scans remain unmodified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "8ccfbe7e5c43dd4210235296fae29d2b8ffdce2f910e50a80c822e7eee5539c6"
OUTPUT = ROOT / "data/ingest_reviews/jahn-aristides-fresh-witnesses.json"


def prepare_page81_retry(pdf_path, output, original=OUTPUT):
    """Pin three reviewed body strips without replacing the original request."""
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Jahn source PDF differs from the reviewed edition")
    prior = json.loads(original.read_text())
    page = next(p for p in prior["pages"] if p["scan_page"] == 81)
    regions = [[.19, .135, .86, .3965], [.19, .3965, .86, .6333],
               [.19, .6333, .86, .84]]
    manifest = {"schema_version": 1,
        "purpose": "Independent retry after both original page81 witnesses lost printed polytonic marks; original attempts remain archived.",
        "sources": prior["sources"],
        "retry_of": {"path": str(original.relative_to(ROOT)),
            "sha256": hashlib.sha256(original.read_bytes()).hexdigest(), "region_id": page["id"]},
        "review": {"recorded_at": "2026-10-18", "scan_page": 81, "printed_page": 8,
            "extent": "The complete Greek body and all three crop boundaries inspected against the source scan at fourfold PDF rendering.",
            "finding": "Accents and breathings are visibly printed throughout, including the opening οἱ μὲν εἰσι. The original two whole-page predictions lose these marks. Three nonoverlapping strips retain every body line in reading order, exclude the running header and most marginal labels, and increase rendered letter size.",
            "policy": "Retain original whole-page predictions and compare retry witnesses against the scan before admission; model retries do not create independent additional votes for the same model."},
        "pages": [{**page, "id": page["id"] + f"-retry-strip-{index}",
            "region": region, "max_side": 3200, "reading_order": index,
            "reconstructs": page["id"], "crop_evidence": "Reviewed whitespace between complete printed lines; body-only enlarged retry"}
            for index, region in enumerate(regions, 1)]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    return manifest


def prepare_failed_pages_retry(pdf_path, output, original=OUTPUT):
    """Pin complete prose strips and notation headings for two length failures."""
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Jahn source PDF differs from the reviewed edition")
    prior = json.loads(original.read_text())
    source_pages = {p["scan_page"]: p for p in prior["pages"]}
    regions = {90: [[.30, .145, .61, .17], [.275, .36, .70, .389]],
        112: [[.13, .145, .80, .386], [.13, .386, .80, .6428], [.13, .6428, .80, .85]]}
    pages = []
    for scan, strips in regions.items():
        page = source_pages[scan]
        for order, region in enumerate(strips, 1):
            pages.append({**page, "id": page["id"] + f"-retry-strip-{order}", "region": region,
                "max_side": 2200 if scan == 90 else 3200, "reading_order": order,
                "reconstructs": page["id"],
                "text_role": "authorial-notation-heading" if scan == 90 else "authorial-prose",
                "crop_evidence": "Source-inspected complete Greek heading; musical notation remains a nonlexical source-image region" if scan == 90 else "Reviewed whitespace between complete printed lines; body-only enlarged retry"})
    manifest = {"schema_version": 1,
        "purpose": "Source-reviewed retries for whole-page length failures on scans90/112; preserve every original prediction.",
        "sources": prior["sources"],
        "retry_of": {"path": str(original.relative_to(ROOT)),
            "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "region_ids": [source_pages[p]["id"] for p in regions]},
        "review": {"recorded_at": "2026-10-18", "checked_scan_pages": [90, 112],
            "extent": "Complete source pages and every retry crop boundary inspected at fourfold PDF rendering.",
            "finding": "Printed17/scan90 contains two Greek headings and extensive musical-symbol tables above modern apparatus. The symbols are preserved by source-image references rather than interpreted as Greek word strings. Printed39/scan112 is ordinary Greek prose; three consecutive crops retain all body lines, excluding the initial running header and marginal reference labels.",
            "policy": "Retain all original attempts, notation source references and retry predictions. Require an exact completed source review before replacing a model input; never supply a joined cross-page word."},
        "nonlexical_source_regions": {source_pages[90]["id"]: [
            {"class": "musical-notation", "region": region, "lexical_eligible": False,
                "retained_as": "source-image", "evidence": "Manual source inspection: paired musical signs, including rotated and reversed letter-like shapes, are not ordinary Greek word attestations."}
            for region in [[.04, .17, .90, .359], [.04, .389, .90, .652]]]},
        "pages": pages}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    return manifest


def prepare_notation_retry(pdf_path, output, original=OUTPUT):
    """Keep the prose and mode captions separate from three symbol tables."""
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Jahn source PDF differs from the reviewed edition")
    prior = json.loads(original.read_text())
    originals = {p["scan_page"]: p for p in prior["pages"]}
    regions = {82: [([.15, .145, .83, .477], "authorial-prose")],
        87: [([.20, .145, .88, .229], "authorial-prose"),
            ([.17, .244, .34, .272], "mode-caption"), ([.59, .242, .73, .271], "mode-caption"),
            ([.17, .328, .34, .352], "mode-caption"), ([.59, .330, .71, .355], "mode-caption"),
            ([.17, .407, .34, .432], "mode-caption"), ([.59, .407, .79, .435], "mode-caption"),
            ([.20, .495, .88, .753], "authorial-prose")],
        91: [([.215, .145, .88, .261], "authorial-prose")]}
    notation = {82: [[.04, .48, .93, .675]],
        87: [[.16, .273, .47, .323], [.58, .271, .90, .322],
             [.16, .353, .48, .404], [.58, .355, .82, .404],
             [.16, .434, .48, .483], [.58, .436, .82, .484]],
        91: [[.08, .264, .94, .48]]}
    pages = [{**originals[scan], "id": originals[scan]["id"] + f"-retry-strip-{order}",
        "region": region, "max_side": 2200 if role == "mode-caption" else 3200,
        "reading_order": order, "reconstructs": originals[scan]["id"], "text_role": role,
        "crop_evidence": "Complete source-inspected prose or Greek mode caption, separate from musical notation"}
        for scan, parts in regions.items() for order, (region, role) in enumerate(parts, 1)]
    manifest = {"schema_version": 1,
        "purpose": "Preserve complete Greek prose and six mode captions without counting musical-symbol tables as words.",
        "sources": prior["sources"],
        "retry_of": {"path": str(original.relative_to(ROOT)),
            "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "region_ids": [originals[p]["id"] for p in regions]},
        "review": {"recorded_at": "2026-10-18", "checked_scan_pages": list(range(74, 171)),
            "extent": "All97 body leaves reviewed as contact sheets for large notation tables; pages82,87,90,91 then inspected at enlarged resolution. Every prose/caption crop boundary inspected separately.",
            "finding": "The only substantial musical-symbol tables occur on scans82,87,90,91. Page90 has its separate length-retry request. Pages82/91 contain prose above tables; page87 contains prose above and below six labeled mode diagrams. All six Greek mode captions are retained as separate textual crops. Letter-like music signs are preserved as explicitly nonlexical source-image regions.",
            "policy": "Retain the original whole-page OCR attempts, all symbols by source-image reference, and both fresh bounded model readings. Never invent prose readings from music signs or select a tied textual reading arbitrarily."},
        "nonlexical_source_regions": {originals[scan]["id"]: [
            {"class": "musical-notation", "region": region, "lexical_eligible": False,
             "retained_as": "source-image", "evidence": "Manual scan inspection: musical-sign rows and symbol labels; ordinary Greek prose and mode captions are retained in separately reviewed text crops."}
            for region in boxes] for scan, boxes in notation.items()}, "pages": pages}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    return manifest


def body_bottom(page):
    import numpy as np
    import pymupdf
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), colorspace=pymupdf.csGRAY)
    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
    image = image[:, int(pixmap.width * .1):int(pixmap.width * .89)]
    active = np.where((image < 150).sum(1) > 4)[0]
    groups = []
    for y in active:
        if groups and y - groups[-1][-1] <= 2:
            groups[-1].append(int(y))
        else:
            groups.append([int(y)])
    for group in groups:
        if not .45 * pixmap.height <= group[0] < .9 * pixmap.height or group[-1] - group[0] > 3:
            continue
        longest = max(len(run) for y in group for run in
            "".join("1" if pixel < 150 else "0" for pixel in image[y]).split("0"))
        if longest >= pixmap.width * .045:
            return round(group[0] / pixmap.height - .003, 4), "thin apparatus or section-ending rule"
    return .92, "complete Greek body; no apparatus separator found"


def prepare(pdf_path, output=OUTPUT):
    import pymupdf
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Jahn source PDF differs from the reviewed edition")
    doc = pymupdf.open(pdf_path)
    pages = []
    for scan in range(74, 171):
        printed = scan - 73
        bottom, evidence = body_bottom(doc[scan - 1])
        if scan == 170:
            bottom, evidence = .40, "Manual scan inspection: the Greek work ends above the rule; the separately headed INDEX below is excluded"
        pages.append({"id": f"jahn-1882-{scan:04d}-greek", "source": "jahn1882",
            "scan_page": scan, "printed_page": printed,
            "book": 1 if printed <= 37 else 2 if printed <= 67 else 3,
            "region": [.04, .04, .95, bottom], "max_side": 2600,
            "crop_evidence": evidence})
    manifest = {"schema_version": 1,
        "purpose": "Independent model witnesses for the complete Greek work in Jahn 1882, with modern editorial apparatus and final index excluded from primary text.",
        "sources": {"jahn1882": {"url": "https://archive.org/download/demusicanuncpri00quingoog/demusicanuncpri00quingoog.pdf",
            "sha256": SOURCE_SHA256, "license": "PD (Jahn 1882)",
            "citation": "Aristidis Quintiliani De musica libri III, edited by Albert Jahn (Berlin: Calvary, 1882)"}},
        "layout_evidence": {"checked_scan_pages": [74, 75, 76, 77, 91, 93, 97, 109, 110, 111, 140, 141, 169, 170],
            "evidence": "The Greek body occupies scan pages74-170, printed1-97; bookII begins printed38 and bookIII printed68. Clear nineteenth-century Greek type replaces the difficult Meibom ligatures. The apparatus separator is checked against the scan layout; page170 has the final Greek paragraph followed by a separately headed index. Meibom page numbers in the margins are edition concordance labels, not authorial Greek text."},
        "pages": pages}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    sanity = {**manifest, "purpose": "Four source-layout and OCR sanity pages before the full Jahn run",
        "pages": [page for page in pages if page["scan_page"] in [74, 111, 141, 170]]}
    output.with_name("jahn-aristides-sanity.json").write_text(json.dumps(sanity, ensure_ascii=False, indent=1) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUTPUT)
    ap.add_argument("--record-layout-review", action="store_true")
    ap.add_argument("--prepare-page81-retry", action="store_true")
    ap.add_argument("--prepare-failed-pages-retry", action="store_true")
    ap.add_argument("--prepare-notation-retry", action="store_true")
    args = ap.parse_args()
    if args.prepare_page81_retry:
        output = args.out if args.out != OUTPUT else OUTPUT.with_name("jahn-aristides-page81-retry.json")
        manifest = prepare_page81_retry(args.pdf, output)
        print(f"Pinned {len(manifest['pages'])} reviewed page81 retry strips")
        return
    if args.prepare_failed_pages_retry:
        output = args.out if args.out != OUTPUT else OUTPUT.with_name("jahn-aristides-length-retry.json")
        manifest = prepare_failed_pages_retry(args.pdf, output)
        print(f"Pinned {len(manifest['pages'])} reviewed retry regions on pages90/112")
        return
    if args.prepare_notation_retry:
        output = args.out if args.out != OUTPUT else OUTPUT.with_name("jahn-aristides-notation-retry.json")
        manifest = prepare_notation_retry(args.pdf, output)
        print(f"Pinned {len(manifest['pages'])} reviewed prose/caption regions on pages82/87/91")
        return
    manifest = prepare(args.pdf, args.out)
    if args.record_layout_review:
        review = {"schema_version": 1, "review_date": "2026-10-18",
            "source_pdf_sha256": SOURCE_SHA256,
            "manifest_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
            "checked_scan_pages": list(range(74, 171)),
            "review_extent": "All97 lower-page crop boundaries inspected against scan renderings, including mathematical diagrams and long editorial apparatus. Full headings and work endings checked on representative pages74,111,141,169,170. This records layout review, not a claim that every printed word has been proofread.",
            "finding": "Each crop retains the Greek body and stops above the modern apparatus when present. The last page's separate index is excluded. No crop adjustment was required after inspection."}
        args.out.with_name("jahn-layout-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n")
    print(f"Pinned {len(manifest['pages'])} Greek body pages")


if __name__ == "__main__":
    main()
