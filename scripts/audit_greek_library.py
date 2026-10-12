#!/usr/bin/env python3
"""Inventory Greek Library candidates; never ingest or promote their texts.

Fetches only the public catalog. Matching is conservative: exact external
anchors establish overlap; title matches only flag possible overlap. A gap is
an unmatched identifier, not proof of a new work. All candidates need review.
Run --fetch once, then rerun offline from the retained catalog.
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_URL = "https://thegreeklibrary.pages.lisn.upsaclay.fr/catalog.json.gz"
TEXT_BASE = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1"
CACHE = ROOT / "sources/greek_library"
OUT = ROOT / "data/inventory/greek_library"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def work_key(value):
    if not isinstance(value, str):
        return ""
    value = value.removeprefix("urn:cts:greekLit:").split(":")[0]
    return ".".join(value.split(".")[:2]) if "." in value else ""


def normalized_title(value):
    return re.sub(r"[^\w]+", " ", "".join(
        c for c in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(c))).strip()


def disposition(entry):
    origin = entry.get("origin", "unknown")
    license_value = entry.get("license") or {}
    terms = " ".join(str(license_value.get(k, "")) for k in ("url", "text")).lower()
    if origin in {"tlg-e", "cllg-freed", "vesuvius"}:
        return "excluded", "origin excluded by corpus policy"
    if any(x in terms for x in ("noncommercial", "non-commercial", "by-nc", "by-nd", "noderivatives")):
        return "excluded", "restricted license"
    if origin == "source-library":
        if "creativecommons.org/licenses/by-sa/4.0" not in terms:
            return "rights-review", "missing explicit edition CC BY-SA 4.0 license"
        return "source-library-review", "verify upstream book, edition boundaries, scan and OCR quality"
    if origin == "ocr-tgl":
        return "ocr-review", "verify independent scan provenance, edition rights and OCR quality"
    if origin == "papyri":
        return "dclp-upstream-review", "prefer original EpiDoc; reconcile papyrus witnesses with literary works"
    if origin in {"ogl", "perseus", "pta", "dfhg"}:
        return "existing-upstream-audit", "check aliases/coverage against existing direct upstream ingestion"
    return "rights-review", "verify upstream license and scope before considering ingestion"


def build(catalog, works, registry, catalog_rows=(), reviews=None):
    served = defaultdict(set)
    catalog_anchors = defaultdict(set)
    inventory = defaultdict(set)
    titles = defaultdict(set)
    for row in catalog_rows:
        anchor = work_key(row.get("cts_urn", ""))
        if anchor:
            catalog_anchors[anchor].add(row["slug"])
    for slug, work in works.items():
        for key in ("cts", "tlg"):
            anchor = work_key(work.get("work_anchors", {}).get(key))
            if anchor:
                served[anchor].add(slug)
        title = normalized_title(work.get("title", ""))
        if title:
            titles[title].add(slug)
    for slug, work in registry.items():
        anchor = work_key(work.get("aliases", {}).get("cts"))
        if anchor:
            inventory[anchor].add(slug)
    rows = []
    for entry in sorted(catalog["entries"], key=lambda e: e["id"]):
        review = (reviews or {}).get(entry["id"], {})
        key = work_key(entry["id"])
        status, reason = disposition(entry)
        exact = served[key]
        reviewed_overlap = review.get("overlap_slug") in works
        alternate = catalog_anchors[key] - exact
        possible = titles[normalized_title(entry["title"])]
        rows.append({
            "edition_id": entry["id"], "work_key": key,
            "origin": entry.get("origin", "unknown"),
            "author": entry["author"], "title": entry["title"],
            "disposition": status, "reason": reason,
            "coverage": "served-anchor" if exact else ("reviewed-overlap" if reviewed_overlap
                        else ("catalog-anchor-review" if alternate else "unmatched-anchor")),
            "served_slugs": ";".join(sorted(exact)),
            "catalog_anchor_slugs": ";".join(sorted(alternate)),
            "inventory_slugs": ";".join(sorted(inventory[key])),
            "possible_title_match_count": len(possible) if not exact else 0,
            "possible_title_matches": ";".join(sorted(possible)[:10]) if not exact else "",
            "license_url": (entry.get("license") or {}).get("url", ""),
            "source_rights": entry.get("sourceRights", ""),
            "edition_status": entry.get("editionStatus", ""),
            "reader_url": "https://thegreeklibrary.pages.lisn.upsaclay.fr" + entry["workPath"],
            "reading_file_url": TEXT_BASE + "/" + entry["objectKey"] + ".gz",
            "review_status": review.get("status", "not-reviewed"),
            "review_overlap_slug": review.get("overlap_slug", ""),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pin_path = OUT / "catalog-pin.json"
    if args.fetch:
        with urllib.request.urlopen(CATALOGUE_URL, timeout=60) as response:
            raw = response.read()
        catalog = json.loads(gzip.decompress(raw))
        sha = digest(raw)
        name = f"catalog-{sha}.json.gz"
        (CACHE / name).write_bytes(raw)
        pin = {"url": CATALOGUE_URL, "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "sha256": sha, "bytes": len(raw), "retained_path": str((CACHE / name).relative_to(ROOT)),
               "upstream_metadata": {k: v for k, v in catalog.items() if k != "entries"}}
        pin_path.write_text(json.dumps(pin, ensure_ascii=False, indent=2) + "\n")
    else:
        pin = json.loads(pin_path.read_text())
        raw = (ROOT / pin["retained_path"]).read_bytes()
        if digest(raw) != pin["sha256"]:
            raise SystemExit("Retained catalog hash mismatch")
        catalog = json.loads(gzip.decompress(raw))
    paths = [ROOT / "data/work_index.json", ROOT / "data/source_registry.json", ROOT / "data/corpus_catalog.tsv"]
    works = json.loads(paths[0].read_text())["works"]
    registry = json.loads(paths[1].read_text())["works"]
    with paths[2].open() as stream:
        catalog_rows = list(csv.DictReader(stream, delimiter="\t"))
    review_path = OUT / "pilot-review.json"
    reviews = json.loads(review_path.read_text())["editions"] if review_path.exists() else {}
    rows = build(catalog, works, registry, catalog_rows, reviews)
    selections = {
        "edition-audit": rows,
        "source-library-gaps": [r for r in rows if r["disposition"] == "source-library-review" and r["coverage"] == "unmatched-anchor" and not r["review_overlap_slug"]],
        "dclp-candidates": [r for r in rows if r["disposition"] == "dclp-upstream-review"],
        "ocr-candidates": [r for r in rows if r["disposition"] == "ocr-review"
                           and r["coverage"] == "unmatched-anchor" and not r["review_overlap_slug"]],
    }
    for name, selection in selections.items():
        with (OUT / f"{name}.tsv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(selection)
    summary = {
        "catalog_sha256": pin["sha256"],
        "pilot_review_sha256": digest(review_path.read_bytes()) if review_path.exists() else None,
        "local_inputs_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths},
        "local_served_work_units": len(works),
        "origin_editions": dict(sorted(Counter(r["origin"] for r in rows).items())),
        "selections": {name: {"editions": len(rs), "work_keys": len({r["work_key"] for r in rs})} for name, rs in selections.items()},
        "limitations": ["Unmatched external anchors are candidates, not confirmed new works.",
                        "Title equality flags possible duplicates but never establishes identity.",
                        "Catalog-only anchor matches require reconciliation (notably Euripides' alternate numbering).",
                        "Catalog provenance is an upstream claim, not a completed rights/quality audit.",
                        "No text is downloaded, ingested or promoted by this script."],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
