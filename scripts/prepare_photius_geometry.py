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


def request_for_group(authority, raw, group, *, catalog=None, authority_path=AUTHORITY):
    catalog = legacy_catalog() if catalog is None else catalog
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
            "source_authority": {"path": authority_path.as_posix(), "sha256": sha(raw)},
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
    result, targets, catalog = {}, set(), legacy_catalog()
    for group in authority["groups"]:
        keys = {(group["model"], group["revision"], group["parent_sha256"], target["id"])
                for target in group["targets"]}
        if len(keys) != len(group["targets"]) or keys & targets:
            raise ValueError("Repeated source-reviewed geometry target")
        targets.update(keys)
        path, request = request_for_group(authority, raw, group, catalog=catalog)
        digest = sha(encode(request))
        if digest in result:
            raise ValueError("Repeated geometry request")
        result[digest] = (path, request)
    return result


GEOMETRY_CHILD_REVIEWS = {
    233: {"parent": "photius-bekker-page0233-qwen38-67012263-gutter.json",
          "target": "photius-bekker-0233-right-lower-gutter",
          "cuts": [.59105, .6848, .7748, .849],
          "condition": {"kind": "source-confirmed-length-termination", "finish_reason": "length",
              "raw_file_sha256": "73673d3655583176f79e5d75891f60148970662ff4eef22794ce5f88254ee611",
              "prediction_record_sha256": "448ee1ff7228707b529fe3e6d399f719ef928fb1bdc8936be25c8700ac8636fb",
              "raw_prediction_sha256": "c39f5740dcb796a8bdf1f559be447e3e0d0f2bb5a29086df8f950a4831bfc6bd"},
          "evidence": "The source contains fourteen faint continuous authorial lines, with visible polytonic marks and no apparatus. The retained attempt repeats an unprinted phrase until its length limit. Cuts in the white spaces after the fifth and tenth lines preserve five, five, and four complete source lines; the reviewed horizontal glyph boundaries remain unchanged."},
    252: {"parent": "photius-bekker-page0252-qwen38-0e57cb5f-gutter.json",
          "target": "photius-bekker-0252-left-lower-gutter",
          "cuts": [.58423, .679, .7706, .859],
          "condition": {"kind": "source-confirmed-polytonic-mark-stripping", "finish_reason": "stop",
              "raw_file_sha256": "58ffeb9a9765bf6d20d01f427cca495967aa30414a6e939a768310f54c239c80",
              "prediction_record_sha256": "86d60c7a6ce1f70079db6b25c8759b341d22d78c8aca5710ea298b4b0ba61d5c",
              "raw_prediction_sha256": "e94cebdd8fc25bbb9e97c2175fc77c08f6198c0370a85e92023de7340a9dd0ee",
              "frozen_policy_sha256": "36b6a22f5889bf6e92e2e821f4e9a1e82826192b623e20e92efd6af7638ad0b9",
              "greek_letters": 700, "breathing_letters": 0},
          "evidence": "The source contains fifteen faint continuous authorial lines with visible polytonic marks, including the Sophronius passage; it contains no decree heading or numbered resolutions. The retained attempt instead invents a monotonic modern decree with placeholders and loses every breathing. Cuts in white spaces after the fifth and tenth source lines preserve three five-line spans, without changing the reviewed horizontal glyph boundaries."},
}


GEOMETRY_CHILD_REVIEWS.update({'109-left-lower': {'scan_page': 109,
                    'parent': 'photius-bekker-page0109-qwen36-ccf7243b-gutter.json',
                    'target': 'photius-bekker-0109-left-lower-gutter',
                    'cuts': [0.588, 0.701, 0.811, 0.85],
                    'condition': {'kind': 'source-confirmed-non-source-reading',
                                  'finish_reason': 'stop',
                                  'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                  'source_evidence': 'The retained reading ends at codex137 heading and '
                                                     'omits the complete first printed Eunomius body line. '
                                                     'The source crop ends after that line and before the '
                                                     'apparatus: body ink ends near y=.84523, apparatus '
                                                     'starts near .85973. Shorter spans retain codex136, '
                                                     'then its continuation, then codex137 heading and first '
                                                     'line.',
                                  'raw_file_sha256': '4cd73ba4fa92b1ee4d4a63867429946359c598f594ff18c6030128400c6b9975',
                                  'prediction_record_sha256': '7dc7419afdc32ede957e3220dad22b75177ed5aa9cd263cc72b83336f8eccc58',
                                  'raw_prediction_sha256': 'af8b6f57e04d0aa747a31655cad2e9a05ba2daaa23c26d862a66b852d13a9463'},
                    'evidence': 'The retained reading ends at codex137 heading and omits the complete first '
                                'printed Eunomius body line. The source crop ends after that line and before '
                                'the apparatus: body ink ends near y=.84523, apparatus starts near .85973. '
                                'Shorter spans retain codex136, then its continuation, then codex137 heading '
                                'and first line.',
                    'output': 'data/ocr_requests/photius-bekker-page0109-left-lower-gutter-supplement.json',
                    'prompt_suffix': 'Transcribe only the complete printed Greek body lines in this source '
                                     'crop, exactly once, preserving polytonic marks and headings. Read the '
                                     'actual visible text; do not substitute a narrative, reconstruct a '
                                     'paragraph, add material, or continue outside the crop.'},
 '232-left-lower': {'scan_page': 232,
                    'parent': 'photius-bekker-page0232-qwen36-648ba3a3-gutter.json',
                    'target': 'photius-bekker-0232-left-lower-gutter',
                    'cuts': [0.58702, 0.6787, 0.7716, 0.848],
                    'condition': {'kind': 'source-confirmed-non-source-reading',
                                  'finish_reason': 'stop',
                                  'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                  'source_evidence': 'The faint source continues theological prose from '
                                                     'Eulogius. The retained lower reading instead '
                                                     'introduces unrelated inquiry involving a center and '
                                                     'bow and theoretical discussion; equal line counts do '
                                                     'not establish source coverage. White-gap cuts retain '
                                                     'every complete printed body line and the unchanged '
                                                     'source boundaries.',
                                  'raw_file_sha256': '5fa49c95beb97952549c15ebad45de9d82c66f68a6aa6901da233c0bf965bdc5',
                                  'prediction_record_sha256': '3eab363c0e738d675d10e17df842e80068e5407991998c9c10c27d852f291a0c',
                                  'raw_prediction_sha256': '7cd6ee7ddf60cf8d3a0842376c340e917868f06c249c43fab2883351c12b2870'},
                    'evidence': 'The faint source continues theological prose from Eulogius. The retained '
                                'lower reading instead introduces unrelated inquiry involving a center and '
                                'bow and theoretical discussion; equal line counts do not establish source '
                                'coverage. White-gap cuts retain every complete printed body line and the '
                                'unchanged source boundaries.',
                    'output': 'data/ocr_requests/photius-bekker-page0232-left-lower-gutter-supplement.json',
                    'prompt_suffix': 'Transcribe only the complete printed Greek body lines in this source '
                                     'crop, exactly once, preserving polytonic marks and headings. Read the '
                                     'actual visible text; do not substitute a narrative, reconstruct a '
                                     'paragraph, add material, or continue outside the crop.'},
 '234-left-middle': {'scan_page': 234,
                     'parent': 'photius-bekker-page0234-qwen36-77a89d17-gutter.json',
                     'target': 'photius-bekker-0234-left-middle-gutter',
                     'cuts': [0.31382, 0.4073, 0.4988, 0.591],
                     'condition': {'kind': 'source-confirmed-non-source-reading',
                                   'finish_reason': 'stop',
                                   'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                   'source_evidence': 'The printed theological discussion visibly names God, '
                                                      'Savior, and Christ; the retained reading instead '
                                                      'invents Julius Nymphius, poetry, and harmonies. Three '
                                                      'shorter spans preserve the complete source lines and '
                                                      'paragraph order without admitting apparatus.',
                                   'raw_file_sha256': '05ce3662e6c68eaebf81aeb1b8896d5cc40a4d16b4f1fa98c01ee524baef6aab',
                                   'prediction_record_sha256': 'ab4570b5b9d82887902b77cddf299966092a3dee752f5bbcaf8b2076be1c3175',
                                   'raw_prediction_sha256': '689b063f0d997a46f5adeb54d73af0e8fa45477e86059f91b3045848dc3cf448'},
                     'evidence': 'The printed theological discussion visibly names God, Savior, and Christ; '
                                 'the retained reading instead invents Julius Nymphius, poetry, and '
                                 'harmonies. Three shorter spans preserve the complete source lines and '
                                 'paragraph order without admitting apparatus.',
                     'output': 'data/ocr_requests/photius-bekker-page0234-left-middle-gutter-supplement.json',
                     'prompt_suffix': 'Transcribe only the complete printed Greek body lines in this source '
                                      'crop, exactly once, preserving polytonic marks and headings. Read the '
                                      'actual visible text; do not substitute a narrative, reconstruct a '
                                      'paragraph, add material, or continue outside the crop.'},
 '234-left-lower': {'scan_page': 234,
                    'parent': 'photius-bekker-page0234-qwen36-77a89d17-gutter.json',
                    'target': 'photius-bekker-0234-left-lower-gutter',
                    'cuts': [0.591, 0.6839, 0.77485, 0.869],
                    'condition': {'kind': 'source-confirmed-non-source-reading',
                                  'finish_reason': 'stop',
                                  'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                  'source_evidence': 'The source contains continuous theological prose and '
                                                     'paragraph transitions; the retained reading '
                                                     'substitutes unrelated moral maxims and a different '
                                                     'paragraph structure. Three shorter spans follow '
                                                     'complete source lines within the same reviewed body '
                                                     'box.',
                                  'raw_file_sha256': '05ce3662e6c68eaebf81aeb1b8896d5cc40a4d16b4f1fa98c01ee524baef6aab',
                                  'prediction_record_sha256': 'da27bd6a1e137668094c248622884a4d8fcdee1eb2385cf2b1f8707560b87015',
                                  'raw_prediction_sha256': '65426da55fdfdef24af0bec95d5ffa8b0805b7e673bef8c92b78a36defcb45a4'},
                    'evidence': 'The source contains continuous theological prose and paragraph transitions; '
                                'the retained reading substitutes unrelated moral maxims and a different '
                                'paragraph structure. Three shorter spans follow complete source lines '
                                'within the same reviewed body box.',
                    'output': 'data/ocr_requests/photius-bekker-page0234-left-lower-gutter-supplement.json',
                    'prompt_suffix': 'Transcribe only the complete printed Greek body lines in this source '
                                     'crop, exactly once, preserving polytonic marks and headings. Read the '
                                     'actual visible text; do not substitute a narrative, reconstruct a '
                                     'paragraph, add material, or continue outside the crop.'},
 '385-right-middle': {'scan_page': 385,
                      'parent': 'photius-bekker-page0385-qwen36-c8462bfe-gutter.json',
                      'target': 'photius-bekker-0385-right-middle-gutter',
                      'cuts': [0.31473, 0.40751, 0.49904, 0.6057],
                      'condition': {'kind': 'source-confirmed-non-source-reading',
                                    'finish_reason': 'stop',
                                    'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                    'source_evidence': 'The source begins with the Dion passage and then the '
                                                       'prooimion heading from Sophronius. The retained '
                                                       'first five lines instead invent an Acts-like '
                                                       'narrative about Syria, brethren, Cyprus, and '
                                                       'Cilicia. Shorter spans preserve the actual '
                                                       'continuous body, heading, and following paragraph.',
                                    'raw_file_sha256': 'ce6927aee0c0dbeb0a4bd89964bee307ec7dfd0d343f0481851474447376383f',
                                    'prediction_record_sha256': 'fc54dd1ba2e90325fa5bd8c22ad075dc8a6d4bfed9dd2818bb84b5bc8504d7e5',
                                    'raw_prediction_sha256': '6d3daaba42ecaa590fdfa81ed2ed1a4209c9562826ad3f0ba27456dfccaf168a'},
                      'evidence': 'The source begins with the Dion passage and then the prooimion heading '
                                  'from Sophronius. The retained first five lines instead invent an '
                                  'Acts-like narrative about Syria, brethren, Cyprus, and Cilicia. Shorter '
                                  'spans preserve the actual continuous body, heading, and following '
                                  'paragraph.',
                      'output': 'data/ocr_requests/photius-bekker-page0385-right-middle-gutter-supplement.json',
                      'prompt_suffix': 'Transcribe only the complete printed Greek body lines in this source '
                                       'crop, exactly once, preserving polytonic marks and headings. Read '
                                       'the actual visible text; do not substitute a narrative, reconstruct '
                                       'a paragraph, add material, or continue outside the crop.'}})


GEOMETRY_CHILD_REVIEWS.update({'250-left-lower': {'scan_page': 250,
                    'parent': 'photius-bekker-page0250-qwen38-9ab8ae61-gutter.json',
                    'target': 'photius-bekker-0250-left-lower-gutter',
                    'cuts': [0.58224, 0.67249, 0.764, 0.846],
                    'condition': {'kind': 'source-confirmed-non-source-reading',
                                  'finish_reason': 'stop',
                                  'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                  'source_evidence': 'The source is historical prose with Sinope, '
                                                     'Mithridates, Diochares, and Sosigenes. The retained '
                                                     'reading instead invents Socratics, Platonists, Plato, '
                                                     'Solon, Sophocles, and a philosopher Nikephoros. Three '
                                                     'shorter spans preserve the complete source body lines '
                                                     'inside the exact reviewed box.',
                                  'raw_file_sha256': 'dfb7d06a23fdcd47bf11e3e11e8b567d293cfc84cec6cee966171aee4274cedc',
                                  'prediction_record_sha256': 'eadcdfbe2685750b75e894a36aaee67facb08a7c08bec1744cee91d3c7101c74',
                                  'raw_prediction_sha256': '42baaa7710d013229bd5455a53ff6e038710aab0645d3442a54299e5121a3dce'},
                    'evidence': 'The source is historical prose with Sinope, Mithridates, Diochares, and '
                                'Sosigenes. The retained reading instead invents Socratics, Platonists, '
                                'Plato, Solon, Sophocles, and a philosopher Nikephoros. Three shorter spans '
                                'preserve the complete source body lines inside the exact reviewed box.',
                    'output': 'data/ocr_requests/photius-bekker-page0250-left-lower-gutter-supplement.json',
                    'prompt_suffix': 'Transcribe only the complete printed Greek historical body lines '
                                     'visible in this crop, exactly once, preserving polytonic marks. Read '
                                     'the actual visible source; do not substitute a philosophical '
                                     'discussion, reconstruct a paragraph, add material, or continue outside '
                                     'the crop.'}})

GEOMETRY_CHILD_REVIEWS.update({'252-right-lower': {'scan_page': 252,
                     'parent': 'photius-bekker-page0252-qwen38-0e57cb5f-gutter.json',
                     'target': 'photius-bekker-0252-right-lower-gutter',
                     'cuts': [0.58383, 0.67556, 0.76728, 0.859],
                     'condition': {'kind': 'source-confirmed-non-source-reading',
                                   'finish_reason': 'stop',
                                   'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                   'source_evidence': 'The source contains fifteen continuous lowercase '
                                                      'theological prose lines. The retained reading inserts '
                                                      'an unprinted uppercase decree-like block in the '
                                                      'middle and unrelated wording around it. Three '
                                                      'five-line spans preserve the actual source body '
                                                      'within the corrected column box.',
                                   'raw_file_sha256': '58ffeb9a9765bf6d20d01f427cca495967aa30414a6e939a768310f54c239c80',
                                   'prediction_record_sha256': '4be67ac8dc3e5643e75da9b5f59c0200247b57e7d93d9934fd11486b24c01de4',
                                   'raw_prediction_sha256': '682ac6e57d3f74bf72fef5652987c7e74e2fac7d6c449d2238bcee85ad0e9a64'},
                     'evidence': 'The source contains fifteen continuous lowercase theological prose lines. '
                                 'The retained reading inserts an unprinted uppercase decree-like block in '
                                 'the middle and unrelated wording around it. Three five-line spans preserve '
                                 'the actual source body within the corrected column box.',
                     'output': 'data/ocr_requests/photius-bekker-page0252-right-lower-gutter-supplement.json',
                     'prompt_suffix': 'Transcribe only the complete printed Greek body lines visible in this '
                                      'crop, exactly once, preserving polytonic marks. Read the visible '
                                      'source; do not insert uppercase blocks or a decree, reconstruct a '
                                      'paragraph, add material, or continue outside the crop.'}})

GEOMETRY_CHILD_REVIEWS.update({'396-left-middle': {'scan_page': 396,
                     'parent': 'photius-bekker-page0396-qwen38-3bff0fa8-gutter.json',
                     'target': 'photius-bekker-0396-left-middle-gutter',
                     'cuts': [0.33413, 0.42634, 0.51984, 0.5898],
                     'condition': {'kind': 'source-confirmed-non-source-reading',
                                   'finish_reason': 'stop',
                                   'source_pdf_sha256': 'd7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6',
                                   'source_evidence': 'Most of the source-shaped first twelve lines remain '
                                                      'recognizable, but the final two printed lines are '
                                                      'replaced by an unsupported chain repeating autou. The '
                                                      'source instead continues historical prose without '
                                                      'that chain. Three shorter complete-line spans '
                                                      'preserve the same body box, with no apparatus or '
                                                      'inserted paragraph.',
                                   'raw_file_sha256': 'f9c0022afc9facfee06690736836d359483a60eb18ef32aa27131ce101483ab2',
                                   'prediction_record_sha256': 'a550056334d47c22ab472f1b92cf4437866bb652cc7a84995d0412dfbb022a2f',
                                   'raw_prediction_sha256': '4784ca5c22a5d6ee44c5430fc232a7b90641c3f61563680b237f075dc156bca3'},
                     'evidence': 'Most of the source-shaped first twelve lines remain recognizable, but the '
                                 'final two printed lines are replaced by an unsupported chain repeating '
                                 'autou. The source instead continues historical prose without that chain. '
                                 'Three shorter complete-line spans preserve the same body box, with no '
                                 'apparatus or inserted paragraph.',
                     'output': 'data/ocr_requests/photius-bekker-page0396-left-middle-gutter-supplement.json',
                     'prompt_suffix': 'Transcribe only the complete printed Greek historical body lines '
                                      'visible in this crop, exactly once, preserving polytonic marks. Read '
                                      'the actual visible source, including every final printed line; do not '
                                      'replace lines with repeated words, reconstruct a paragraph, add '
                                      'material, or continue outside the crop.'}})

FOLLOWUP_AUTHORITY = Path("data/ocr_requests/photius-followup-gutter-source-review.json")
FOLLOWUP_BOUNDS = {147: [.017, .462, .467, .975]}


def build_followup_authority(paths, pdf_path):
    """Inspect exact current geometry outcomes without rewriting earlier requests."""
    import fitz
    from photius_retries import validate_record, validate_retry_metadata
    if sha(pdf_path.read_bytes()) != SOURCE_SHA:
        raise ValueError("Photius source PDF changed")
    catalog = known_gutter_manifests()
    pdf = fitz.open(pdf_path)
    groups, pages, artifacts = [], {}, {}
    for path in paths:
        raw = path.read_bytes(); lines = raw.splitlines()
        if not lines:
            continue
        meta = json.loads(lines[0]).get("_meta", {})
        digest = meta.get("manifest_sha256")
        if digest not in catalog or catalog[digest][1]["pages"][0]["scan_page"] not in FOLLOWUP_BOUNDS:
            continue
        parent_path, request = catalog[digest]
        validate_retry_metadata(meta, request)
        records = {r["id"]: (r, line) for line in lines[1:] for r in [json.loads(line)]}
        if len(records) != len(request["pages"]) or set(records) != {p["id"] for p in request["pages"]}:
            raise ValueError("Follow-up source review requires the complete current geometry run")
        page = request["pages"][0]["scan_page"]; bounds = FOLLOWUP_BOUNDS[page]
        group = {"page": page, "model": meta["model"], "revision": meta["revision"],
                 "parent_path": parent_path, "parent_sha256": digest, "targets": []}
        for job in request["pages"]:
            row, line = records[job["id"]]; validate_record(row, job, request)
            new = corrected_region(job["region"], bounds)
            if new != job["region"]:
                group["targets"].append({"id": job["id"], "original_region": job["region"], "new_region": new,
                    "raw_file_sha256": sha(raw), "prediction_record_sha256": sha(line),
                    "raw_prediction_sha256": sha(row["raw_prediction"].encode()), "finish_reason": row["finish_reason"]})
        groups.append(group)
        contact = source_contact(pdf, page, bounds)
        contact_path = Path(f"data/corpus_changes/photius-followup-source-review/page-{page:04d}.png")
        artifacts[contact_path] = contact
        pages[str(page)] = {"bounds": bounds, "source_contact": {"path": contact_path.as_posix(), "sha256": sha(contact)},
            "evidence": "Independent full-height enlarged source review found remaining right initial-glyph clipping at .480 and neighboring-column initials inside the left crop ending .476. The revised .462/.467 gutter pair preserves every Greek ending and initial, including the lower Theisantes line. Marginal line numerals may occupy the gap; body and apparatus y boundaries remain unchanged."}
    if set(pages) != {str(p) for p in FOLLOWUP_BOUNDS} or len(groups) != len(FOLLOWUP_BOUNDS):
        raise ValueError("Follow-up review requires exactly one complete pinned run per source page")
    authority = {"schema_version": 1, "kind": "photius-source-reviewed-followup-column-boundaries",
        "reviewed_at": "2026-10-18", "source_pdf": {"url": SOURCE_URL, "sha256": SOURCE_SHA},
        "pages": pages, "groups": groups, "generated_by": "scripts/prepare_photius_geometry.py",
        "policy": "Keep earlier authorities and every outcome unchanged; replace only these exact current leaves, within one assembled model-family vote."}
    return authority, artifacts


def source_authorities():
    return {path.as_posix(): (ROOT / path).read_bytes() for path in (AUTHORITY, FOLLOWUP_AUTHORITY)
            if (ROOT / path).exists()}


def known_followup_geometry_manifests():
    path = ROOT / FOLLOWUP_AUTHORITY
    if not path.exists():
        return {}
    raw = path.read_bytes(); authority = json.loads(raw)
    if (authority.get("kind") != "photius-source-reviewed-followup-column-boundaries"
            or authority.get("source_pdf") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or {int(p): row["bounds"] for p, row in authority["pages"].items()} != FOLLOWUP_BOUNDS):
        raise ValueError("Unknown follow-up source geometry authority")
    catalog = known_gutter_manifests(); result = {}
    for group in authority["groups"]:
        filename, request = request_for_group(authority, raw, group, catalog=catalog, authority_path=FOLLOWUP_AUTHORITY)
        result[sha(encode(request))] = (filename, request)
    return result


def known_geometry_supplement_manifests():
    """Retain exact degraded geometry leaves and split only their source lines."""
    parents = {Path(path).name: (digest, path, request)
               for digest, (path, request) in known_gutter_manifests().items()}
    result = {}
    for key, review in sorted(GEOMETRY_CHILD_REVIEWS.items(), key=lambda value: str(value[0])):
        page = review.get("scan_page", key)
        if review["parent"] not in parents:
            continue
        digest, path, parent = parents[review["parent"]]
        job = next(p for p in parent["pages"] if p["id"] == review["target"])
        cuts = review["cuts"]
        if (job["scan_page"] != page or cuts[0] != job["region"][1]
                or cuts[-1] != job["region"][3] or cuts != sorted(set(cuts))):
            raise ValueError("Geometry child must partition its exact retained source span")
        pages = [{**job, "id": job["id"] + f"-part{number:02d}",
                  "region": [job["region"][0], low, job["region"][2], high],
                  "reading_order": number - 1, "role": "source-reviewed-failed-geometry-supplement",
                  "prompt_suffix": review.get("prompt_suffix", "Transcribe only these complete faint printed Greek body lines, exactly once. Preserve every visible accent, breathing, initial and final glyph. Do not invent a heading, decree, placeholders, numbered resolutions, or material outside the crop. Do not expand text or repeat lines.")}
                 for number, (low, high) in enumerate(zip(cuts, cuts[1:]), 1)]
        request = {"schema_version": 1, "work": parent["work"], "review_date": "2026-10-18",
                   "purpose": "Complete one exactly pinned degraded geometry leaf; preserve every ancestor and successful sibling, with one assembled vote per model family.",
                   "supplements": {"manifest_path": path, "manifest_sha256": digest,
                       "page_id": parent["supplements"]["page_id"], "replaces_region": job["id"]},
                   "checkpoints": parent["checkpoints"], "sources": parent["sources"], "prompt": parent["prompt"],
                   "replacement_condition": copy.deepcopy(review["condition"]),
                   "review": {"accepted_for_primary_ingest": False, "checked_scan_pages": [page],
                       "source_pdf_sha256": SOURCE_SHA, "evidence": review["evidence"],
                       "admission_policy": "Require the exact retained parent outcome and a completed output-to-source review. Keep all original readings and failures; no additional vote or lexical proofreading claim."},
                   "pages": pages}
        output = review.get("output", f"data/ocr_requests/photius-bekker-page{page:04d}-gutter-supplement.json")
        result[sha(encode(request))] = (output, request)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True, help="Retained original/retry JSONL directory")
    parser.add_argument("--scan-pdf", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--followup", action="store_true", help="Reproduce separate reviewed follow-up authority")
    args = parser.parse_args()
    paths = sorted(args.raw_dir.rglob("*.jsonl"))
    authority, artifacts = (build_followup_authority(paths, args.scan_pdf) if args.followup
                            else build_authority(paths, args.scan_pdf))
    raw = encode(authority)
    authority_path = FOLLOWUP_AUTHORITY if args.followup else AUTHORITY
    artifacts[authority_path] = raw
    for group in authority["groups"]:
        path, request = request_for_group(authority, raw, group,
            catalog=known_gutter_manifests() if args.followup else None, authority_path=authority_path)
        artifacts[Path(path)] = encode(request)
    for path, request in known_geometry_supplement_manifests().values():
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
