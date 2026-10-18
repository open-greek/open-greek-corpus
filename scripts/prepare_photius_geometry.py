#!/usr/bin/env python3
"""Pin source-reviewed Photius column boundaries and retain old crop attempts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from pathlib import Path

from prepare_photius_coverage import ROOT, build_page13_retry
from prepare_photius_retries import (CHECKPOINT36, CHECKPOINT38, REVIEWS, EXTRA_REVIEWS,
    SUPPLEMENT_REVIEWS, build_retry, build_variant, build_supplement, manifest_path,
    variant_path, supplement_path)

AUTHORITY = Path("data/ocr_requests/photius-gutter-source-review.json")
CONTACTS = Path("data/corpus_changes/photius-gutter-source-review")
SOURCE_SHA = "d7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6"
SOURCE_URL = "https://archive.org/download/bibliothecaexrec00photuoft/bibliothecaexrec00photuoft.pdf"

# Full-height source review: left outer/start, left end, right start, right end.
# Blank gutter and marginal line numbers do not count as authorial body text.
SOURCE_BOUNDS = {
    13: [.04, .486, .49, .985], 27: [.035, .49, .49, .975],
    41: [.035, .485, .485, .975], 47: [.045, .495, .498, .97],
    49: [.03, .483, .483, .975], 50: [.045, .495, .505, .97],
    83: [.02, .462, .462, .975], 87: [.045, .495, .505, .97],
    105: [.045, .49, .49, .97], 109: [.035, .492, .492, .97],
    112: [.045, .495, .505, .97], 113: [.03, .48, .48, .97],
    119: [.035, .485, .485, .975],
    147: [.017, .476, .480, None], 181: [None, .485, .488, None],
    188: [None, .503, .505, None], 192: [None, .510, .510, None],
    207: [None, .485, .488, None], 232: [None, .505, .505, None],
    233: [None, .487, .490, None], 234: [None, .500, .505, None],
    239: [None, .488, .490, None], 242: [None, .511, .511, None],
    245: [None, .495, .497, None], 250: [None, .510, .512, None],
    252: [None, .515, .520, None], 255: [None, .495, .497, None],
    381: [.035, .485, .488, None], 384: [None, .501, .500, None],
    385: [None, .500, .502, None], 388: [None, .503, .505, None],
    396: [None, .503, .503, None], 397: [.035, .487, .490, None],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def legacy_catalog():
    values = [("data/ocr_requests/photius-bekker-page13-retry.json", build_page13_retry())]
    values += [(manifest_path(p).as_posix(), build_retry(p)) for p in sorted(REVIEWS)]
    values += [(variant_path(n).as_posix(), build_variant(n)) for n in sorted(EXTRA_REVIEWS)]
    values += [(supplement_path(p, n).as_posix(), build_supplement(p, n)) for p, n in sorted(SUPPLEMENT_REVIEWS)]
    return {sha(encode(request)): (path, request) for path, request in values}


def selected(request, checkpoint):
    return checkpoint in {(v["model"], v["revision"]) for v in request.get("checkpoints", [CHECKPOINT36, CHECKPOINT38])}


def corrected_region(region, bounds):
    x0, y0, x1, y1 = region
    if x0 < .2 and x1 > .8:
        return list(region)  # Full-width heading, letter, or lacuna.
    if (x0 + x1) / 2 < .5:
        return [bounds[0] if bounds[0] is not None else x0, y0, bounds[1], y1]
    return [bounds[2], y0, bounds[3] if bounds[3] is not None else x1, y1]


def source_contact(pdf, page, bounds):
    import fitz
    from PIL import Image, ImageDraw
    leaf = pdf[page - 1]
    w, h = leaf.rect.width, leaf.rect.height
    panels = []
    for label, low, high, cuts in [
        ("left outer", 0, .09, [(.045, "gray"), (bounds[0], "blue")]),
        ("gutter", .44, .55, [(.495, "gray"), (.505, "gray"), (bounds[1], "red"), (bounds[2], "blue")]),
        ("right outer", .92, 1, [(.97, "gray"), (bounds[3], "blue")]),
    ]:
        pix = leaf.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(low*w, .05*h, high*w, .875*h), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(image)
        for cut, color in cuts:
            if cut is not None:
                x = (cut - low) * w * 4
                draw.line((x, 0, x, image.height), fill=color, width=1)
        panel = Image.new("RGB", (image.width, image.height + 45), "white")
        panel.paste(image, (0, 45))
        ImageDraw.Draw(panel).text((3, 4), f"PDF {page}: {label}\nnew bounds {bounds}", fill="black")
        panels.append(panel)
    contact = Image.new("RGB", (sum(p.width + 12 for p in panels), max(p.height for p in panels)), "white")
    x = 0
    for panel in panels:
        contact.paste(panel, (x, 0)); x += panel.width + 12
    output = io.BytesIO(); contact.save(output, format="PNG", compress_level=9)
    return output.getvalue()


def build_authority(paths, pdf_path):
    import fitz
    from photius_retries import validate_record, validate_retry_metadata
    if sha(pdf_path.read_bytes()) != SOURCE_SHA:
        raise ValueError("Photius source PDF changed")
    catalog = legacy_catalog()
    runs = {}
    for path in sorted(paths, key=lambda p: sha(p.read_bytes())):
        raw = path.read_bytes(); lines = [line for line in raw.splitlines() if line.strip()]
        if not lines:
            continue
        meta = json.loads(lines[0]).get("_meta", {})
        digest = meta.get("manifest_sha256")
        if digest not in catalog:
            continue  # Original whole-page inputs are retained by the main import.
        request = catalog[digest][1]
        checkpoint = (meta["model"], meta["revision"])
        validate_retry_metadata(meta, request)
        if not selected(request, checkpoint) or meta.get("prompt") != request["prompt"]:
            raise ValueError("Geometry source attempt differs from its checkpoint or prompt")
        jobs = {job["id"]: job for job in request["pages"]}
        rows = [json.loads(line) for line in lines[1:]]
        if len(rows) != len(jobs) or {r["id"] for r in rows} != set(jobs):
            raise ValueError("Geometry preparation requires every old retry outcome")
        key = (*checkpoint, digest)
        if key in runs:
            raise ValueError("Geometry preparation cannot choose between duplicate old attempts")
        records = {}
        for row, line in zip(rows, lines[1:]):
            validate_record(row, jobs[row["id"]], request)
            records[row["id"]] = {"row": row, "record_sha256": sha(line)}
        runs[key] = {"raw_sha256": sha(raw), "metadata": meta, "records": records}
    pdf = fitz.open(pdf_path)
    artifacts, page_reviews, groups = {}, {}, {}
    for page, bounds in sorted(SOURCE_BOUNDS.items()):
        contact = source_contact(pdf, page, bounds)
        contact_path = CONTACTS / f"page-{page:04d}.png"
        artifacts[contact_path] = contact
        page_reviews[str(page)] = {"bounds": bounds, "source_contact": {"path": contact_path.as_posix(), "sha256": sha(contact)},
            "evidence": "Full-height printed body edges checked against the source scan. Revised edges preserve Greek glyphs and diacritics while excluding neighboring-column body text. Marginal line numbers are not classified by this review; horizontal body and apparatus boundaries remain unchanged."}

    def visit(checkpoint, digest, job, ancestry):
        if digest in ancestry:
            raise ValueError("Cyclic old retry authority")
        request = catalog[digest][1]
        run = runs.get((*checkpoint, digest))
        if run is None:
            raise ValueError("A reviewed current leaf lacks its retained raw attempt")
        children = [(key, child) for key, (_, child) in catalog.items()
                    if child.get("supplements", {}).get("manifest_sha256") == digest
                    and child["supplements"]["replaces_region"] == job["id"] and selected(child, checkpoint)]
        if len(children) > 1:
            raise ValueError("Two old remedies name one selected leaf")
        if children:
            child_sha, child = children[0]
            for part in child["pages"]:
                visit(checkpoint, child_sha, part, (*ancestry, digest))
            return
        page = job["scan_page"]
        corrected = corrected_region(job["region"], SOURCE_BOUNDS[page])
        if corrected == job["region"]:
            return
        retained = run["records"][job["id"]]
        row = retained["row"]
        if not isinstance(row.get("raw_prediction"), str) or row.get("finish_reason") not in {"stop", "length", "error"}:
            raise ValueError("A retained geometry leaf lacks an explicit original outcome")
        key = (page, *checkpoint, digest)
        group = groups.setdefault(key, {"page": page, "model": checkpoint[0], "revision": checkpoint[1],
            "parent_path": catalog[digest][0], "parent_sha256": digest, "targets": []})
        group["targets"].append({"id": job["id"], "original_region": job["region"], "new_region": corrected,
            "raw_file_sha256": run["raw_sha256"], "prediction_record_sha256": retained["record_sha256"],
            "raw_prediction_sha256": sha(row["raw_prediction"].encode()), "finish_reason": row["finish_reason"]})

    for digest, (_, request) in catalog.items():
        if not request.get("retry_of") or request["pages"][0]["scan_page"] not in SOURCE_BOUNDS:
            continue
        for checkpoint in [(CHECKPOINT36["model"], CHECKPOINT36["revision"]), (CHECKPOINT38["model"], CHECKPOINT38["revision"])]:
            if not selected(request, checkpoint):
                continue
            if (*checkpoint, digest) not in runs:
                raise ValueError("A source-reviewed base request is not complete")
            for job in request["pages"]:
                visit(checkpoint, digest, job, ())
    authority = {"schema_version": 1, "kind": "photius-source-reviewed-column-boundaries",
        "reviewed_at": "2026-10-18", "source_pdf": {"url": SOURCE_URL, "sha256": SOURCE_SHA},
        "source_contact_legend": {"gray_reference_edges": [.045, .495, .505, .970],
            "red": "reviewed left-column end", "blue": "reviewed right-column start and changed outer edges",
            "unchanged_outer_edges": "A null outer bound preserves each parent crop's exact outer edge."},
        "scope": "Correct only source-confirmed crop boundaries in existing retry leaves. Preserve every original and retry attempt and one vote per model family; no lexical proofreading or arbitrary reading selection.",
        "pages": page_reviews, "groups": [groups[key] for key in sorted(groups)],
        "generated_by": "scripts/prepare_photius_geometry.py"}
    return authority, artifacts


def source_authority():
    path = ROOT / AUTHORITY
    return (AUTHORITY.as_posix(), path.read_bytes()) if path.exists() else (None, None)


def request_for_group(authority, raw, group):
    catalog = legacy_catalog()
    parent_path, parent = catalog[group["parent_sha256"]]
    if parent_path != group["parent_path"]:
        raise ValueError("Geometry parent request changed")
    checkpoint = (group["model"], group["revision"])
    if not selected(parent, checkpoint) or authority["source_pdf"]["sha256"] != SOURCE_SHA:
        raise ValueError("Geometry source or checkpoint differs from its authority")
    jobs = {p["id"]: p for p in parent["pages"]}
    page_id = parent.get("retry_of", parent.get("supplements"))["page_id"]
    pages, conditions = [], {}
    for order, target in enumerate(group["targets"]):
        job = jobs[target["id"]]
        if (job["scan_page"] != group["page"] or target["original_region"] != job["region"]
                or target["new_region"] != corrected_region(job["region"], authority["pages"][str(group["page"])]["bounds"])):
            raise ValueError("Geometry substitution differs from the reviewed source edges")
        pages.append({**job, "id": job["id"] + "-gutter", "replaces_region": job["id"],
            "region": target["new_region"], "reading_order": order, "max_side": 3600,
            "role": "source-reviewed-column-boundary-retry",
            "prompt_suffix": "Transcribe this complete source-reviewed Greek body span exactly once. Preserve all initial and final glyphs, polytonic accents, breathings, and headings. Omit marginal line numbers; do not repeat words, reconstruct text, or continue outside this crop."})
        conditions[job["id"]] = {"kind": "source-confirmed-column-boundary-error",
            "old_manifest_sha256": group["parent_sha256"], "source_pdf_sha256": SOURCE_SHA,
            "source_review_sha256": sha(raw), **copy.deepcopy(target)}
    request = {"schema_version": 1, "work": parent["work"], "review_date": "2026-10-18",
        "purpose": "Correct only explicitly reviewed column boundaries; retain every old attempt and successful sibling within one model-family assembly.",
        "supplements": {"manifest_path": parent_path, "manifest_sha256": group["parent_sha256"],
            "page_id": page_id, "replaces_regions": [t["id"] for t in group["targets"]]},
        "checkpoints": [{"model": group["model"], "revision": group["revision"]}],
        "sources": parent["sources"], "prompt": parent["prompt"], "replacement_conditions": conditions,
        "review": {"accepted_for_primary_ingest": False, "checked_scan_pages": [group["page"]],
            "source_authority": {"path": AUTHORITY.as_posix(), "sha256": sha(raw)},
            "evidence": authority["pages"][str(group["page"])]["evidence"],
            "admission_policy": "Require the exact old leaf, its immediate parent request, checkpoint, raw record, source PDF, reviewed old/new boxes, new image hash, and completed output-to-scan review. Preserve all original and retry text; no extra votes."},
        "pages": pages}
    family = "qwen36" if group["model"] == CHECKPOINT36["model"] else "qwen38"
    path = Path(f"data/ocr_requests/photius-bekker-page{group['page']:04d}-{family}-{group['parent_sha256'][:8]}-gutter.json")
    return path.as_posix(), request


def known_gutter_manifests():
    _, raw = source_authority()
    if raw is None:
        return {}
    authority = json.loads(raw)
    if (authority.get("kind") != "photius-source-reviewed-column-boundaries"
            or authority.get("generated_by") != "scripts/prepare_photius_geometry.py"
            or authority.get("source_pdf") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or {int(p): r["bounds"] for p, r in authority.get("pages", {}).items()} != SOURCE_BOUNDS):
        raise ValueError("Unknown Photius geometry authority")
    result, targets = {}, set()
    for group in authority["groups"]:
        keys = {(group["model"], group["revision"], group["parent_sha256"], target["id"])
                for target in group["targets"]}
        if len(keys) != len(group["targets"]) or keys & targets:
            raise ValueError("Repeated source-reviewed geometry target")
        targets.update(keys)
        path, request = request_for_group(authority, raw, group)
        digest = sha(encode(request))
        if digest in result:
            raise ValueError("Repeated geometry request")
        result[digest] = (path, request)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True, help="Retained original/retry JSONL directory")
    parser.add_argument("--scan-pdf", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    authority, artifacts = build_authority(sorted(args.raw_dir.rglob("*.jsonl")), args.scan_pdf)
    raw = encode(authority)
    artifacts[AUTHORITY] = raw
    for group in authority["groups"]:
        path, request = request_for_group(authority, raw, group)
        artifacts[Path(path)] = encode(request)
    if args.write:
        for path, content in artifacts.items():
            target = ROOT / path
            if target.exists() and target.read_bytes() != content:
                raise ValueError("Refusing to mutate an already pinned geometry authority")
        for path, content in artifacts.items():
            target = ROOT / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
    print(json.dumps({"requests": len(authority["groups"]), "changed_leaves": sum(len(g["targets"]) for g in authority["groups"]),
                      "source_pages_reviewed": len(authority["pages"]), "written": args.write}))


if __name__ == "__main__":
    main()
