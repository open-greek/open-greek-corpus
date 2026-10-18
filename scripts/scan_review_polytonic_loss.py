#!/usr/bin/env python3
"""Serialize the source review of the immutable 60-page polytonic-loss sample.

This is a record of visual inspection, not automatic certification of new scans.
Changing the selected images or transcription requires a new source review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import benchmark_page_ocr as benchmark
from report_polytonic_loss import DEFAULT_OUT, dump

MANIFEST_SHA256 = "7781a2fe5c14231f62c0eed09e5697060740aac63092ac2740e20ee9ea7870d1"
REVIEWED = """grc_grna_or_419 grc_grna_or_425 grc_grna_or_427 grc_grna_or_429
grc_grna_or_451 grc_grna_or_455 grc_grna_or_475 grc_grna_or_479 grc_grna_or_487
grc_grna_or_489 grc_grna_or_493 grc_grna_or_497 grc_grna_or_503 grc_grna_or_531
grc_grna_or_575 grc_grna_or_589 grc_grna_or_591 grc_grna_or_601 grc_grna_or_611
grc_grna_or_619 grc_grna_or_623 grc_grna_or_629 grc_grna_or_633 grc_grna_or_679
grc_grna_or_685 grc_grna_or_693 grc_grna_or_707 grc_grna_or_719
grc_tlg_mpg114-1003 grc_tlg_mpg114-1005 grc_tlg_mpg114-1009
grc_tlg_mpg127-520 grc_tlg_mpg127-522 grc_tlg_mpg127-524
grc_tlg_mpg145-234 grc_tlg_mpg145-254 grc_tlg_mpg145-256 grc_tlg_mpg145-276
grc_tlg_mpg145-306 grc_tlg_mpg145-310 grc_tlg_mpg145-316 grc_tlg_mpg145-334
grc_tlg_mpg145-338 grc_tlg_mpg145-346 grc_tlg_mpg17-34 grc_tlg_mpg17-36
grc_tlg_mpg2-639 grc_tlg_mpg2-645 grc_tlg_mpg87-4078 grc_tlg_mpg87-4082
grc_tlg_mpg87-4084 grc_tlg_mpg89-1851 grc_tlg_mpg89-1853 grc_tlg_mpg98-1362
grc_tlg_mpg99-1704 grc_tlg_mpg99-1708 grc_tlg_mpg99-1710 grc_tlg_mpg99-1712
grc_tlg_mpg99-1714 grc_tlg_mpg99-1718""".split()

# Decisions were made against the source images before inspecting fresh outputs.
ORDER = {
    "grc_grna_or_531": "Printed heading ΛΟΓΟΣ Δʹ. is first on the scan but last in XML line order.",
    "grc_tlg_mpg145-254": "The first printed line beginning γων, καὶ μετὰ is last in XML line order, after the page's bottom line.",
    "grc_tlg_mpg145-276": "The first printed line beginning ΟΑʹ. Ἐν τοίνυν is near the end of XML line order, after the lower paragraph.",
    "grc_tlg_mpg145-334": "The six top lines beginning μένος, δυοῖν follow the bottom paragraph in XML line order.",
    "grc_tlg_mpg99-1704": "The two wide lines beginning σωτηρίαν τῶν close paragraph αʹ on the scan, but follow paragraph βʹ in XML line order.",
}
COVERAGE = {
    "grc_tlg_mpg17-36": "XML ends at μὴ δοθῆναι κατορθώσαντι. The scan also contains the lower ΚΕΦ. Γʹ. and ΚΕΦ. Ϛʹ. sections, absent from line-level text.",
    "grc_tlg_mpg87-4082": "XML ends at ἥτις ἐστὶν, before the final printed Greek lines beginning ἡ ἀνάδειξις τοῦ σωτηρίου σταυροῦ.",
    "grc_tlg_mpg98-1362": "XML stops at τὰ τοῦ Καρ, omitting the remaining sentence, ΠΕΡΙ ΤΗΣ ΤΩΝ ΚΑΡΠΑΝΙΩΝ ΑΙΡΕΣΕΩΣ heading and following paragraph. All TextLine coordinates are empty.",
    "grc_tlg_mpg99-1704": "XML omits the two Greek lines above the title and the title itself.",
}


def build(manifest_path):
    if benchmark.sha256(manifest_path) != MANIFEST_SHA256:
        raise ValueError("The reviewed manifest changed; inspect the changed source scans")
    manifest = json.loads(manifest_path.read_text())
    if set(REVIEWED) != {p["id"] for p in manifest["pages"]} or len(REVIEWED) != 60:
        raise ValueError("The source review does not cover exactly the selected 60 pages")
    pages = []
    for page in manifest["pages"]:
        identity = page["id"]
        notes = [ORDER[identity]] if identity in ORDER else []
        if identity in COVERAGE:
            notes.append(COVERAGE[identity])
        if identity == "grc_tlg_mpg114-1009":
            notes.append("The short right continuation is joined to two wide printed lines; XML follows that source order.")
        pages.append({"id": identity, "image_sha256": page["image_sha256"],
            "xml_sha256": page["xml_sha256"], "gold_sha256": page["gold_sha256"],
            "scan_reviewed": True, "printed_orthography": "polytonic",
            "reference_order": "source-order-mismatch" if identity in ORDER else "verified",
            "reference_coverage": "partial" if identity in COVERAGE else "verified",
            "notes": notes})
    return {"schema_version": 1, "review_date": "2026-10-18", "manifest_sha256": MANIFEST_SHA256,
        "method": "Visual inspection of all 60 immutable source crops, comparing printed orthography, first and last transcription lines, paragraph order and column transitions with line-level XML. Coordinate-order inversions were checked against the scans. This is a page-level suitability review, not a new character-by-character reference transcription.",
        "fresh_model_outputs_seen": False, "source_text_changed": False,
        "excluded_reference_pages": sorted(set(ORDER) | set(COVERAGE)),
        "counts": {"pages": len(pages), "order_mismatch": len(ORDER),
            "partial_reference": len(COVERAGE), "eligible_reference": len(pages) - len(set(ORDER) | set(COVERAGE))},
        "by_split": {split: dict(Counter("excluded" if p["id"] in ORDER or p["id"] in COVERAGE else "eligible"
            for p in manifest["pages"] if p["split"] == split)) for split in ("calibration", "test")},
        "pages": pages, "generated_by": "scripts/scan_review_polytonic_loss.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUT / "manifest.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "scan-review.json")
    args = parser.parse_args()
    result = build(args.manifest)
    args.out.write_bytes(dump(result))
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
