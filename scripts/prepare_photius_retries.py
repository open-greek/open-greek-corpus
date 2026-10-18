#!/usr/bin/env python3
"""Pin source-reviewed strips for particular failed Photius checkpoints."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_photius_coverage import ROOT, build, build_later_gap

CHECKPOINT38 = {"model": "Qwen/Qwen3.8-27B-FP8", "revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}
CHECKPOINT36 = {"model": "Qwen/Qwen3.6-27B", "revision": "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"}


def column_strips(top, bottom, left_cuts, right_cuts):
    result = []
    for side, x0, x1, cuts in (("left", .045, .495, left_cuts), ("right", .505, .97, right_cuts)):
        limits = [top, *cuts, bottom]
        result.extend((f"{side}-{name}", [x0, low, x1, high])
                      for name, low, high in zip(("upper", "middle", "lower"), limits, limits[1:]))
    return result


REVIEWS = {
    27: {"strips": [("left-upper", [.035, .055, .49, .318]),
                    ("left-middle", [.035, .318, .49, .574]),
                    ("left-lower", [.035, .574, .49, .848]),
                    ("right-upper", [.495, .055, .975, .295]),
                    ("right-middle", [.495, .295, .975, .5895]),
                    ("right-lower", [.495, .5895, .975, .848])],
         "evidence": "Printed page15 continues codex54, then contains codices55–57. The sentence ἔσφαγη, ἢ ὡς ἄλλοι φασίν, ἠφανίσθη occurs once in codex57; the source then continues its account of the later Roman kings. The original Qwen3.8 instead repeats that sentence and the following phrase122 times despite stop termination. Enlarged interline checks preserve every body line and heading in these six strips; the lower boundary excludes smaller apparatus.",
         "failure": "A stop-terminated Qwen3.8 original contains a source-confirmed repetition loop. The independent Qwen3.6 whole-page reading remains its vote."},
    47: {"cut": .458, "top": .065, "bottom": .848,
         "evidence": "Printed page 35 begins codex 70, continues codex 71 from the left-column foot into the right-column top, then begins codex 72. The four crop boundaries retain complete authorial lines and stop above the smaller apparatus. The horizontal split at .458 lies in a blank interline gap in both columns.",
         "failure": "Qwen3.8 repeats Greek function words and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    50: {"cut": .456, "top": .062, "bottom": .835,
         "evidence": "Printed page 38 continues codex 72 in two columns. The four crops include every large Greek body line; the last right-column line ends with the opening of Xerxes' campaign against the Greeks. The horizontal split at .456 lies between complete lines; the lower boundary excludes the smaller apparatus.",
         "failure": "Qwen3.8 repeats καὶ and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    87: {"strips": [("left-upper", [.045, .061, .495, .318]),
                    ("left-middle", [.045, .318, .495, .580]),
                    ("left-lower", [.045, .580, .495, .840]),
                    ("right-upper", [.505, .061, .97, .318]),
                    ("right-middle", [.505, .318, .97, .580]),
                    ("right-lower", [.505, .580, .97, .840])],
         "evidence": "Printed page75 continues the dramatic narrative in two columns. The six strips retain every large Greek body line, including the lower right paragraph beginning Ἀλλ’ ὅ γε Τύρος καὶ Εὐφράτης. Both horizontal boundaries lie between complete lines; the bottom at.840 stops above the smaller apparatus beginning at.850. Reading order is the entire left column followed by the entire right column.",
         "failure": "The original Qwen3.8 page attempt reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    105: {"strips": column_strips(.061, .840, [.340, .601], [.322, .620]),
          "evidence": "Printed page93 contains the continuation of the Origen-related notice, codex119 on Pierius, and the opening of codex120 on Epiphanius. The six strips retain the complete large body in column order. Left boundaries fall before a new paragraph and the119 heading; the lower right boundary falls before the120 heading. Enlarged boundary checks include descenders and exclude the smaller apparatus below.840.",
          "failure": "The original Qwen3.8 page attempt reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    109: {"strips": column_strips(.070, .850, [.383, .588], [.387, .611]),
          "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page97 includes codex131, the grouped132–135 notices, codices136/137 at the left foot, and codex138 on Eunomius in the right column. The enlarged boundary review preserves every large Greek line and heading, including descenders. Left splits fall between paragraphs and before the136 heading. The bottom at.850 falls between the last body line and smaller apparatus; column order is unchanged.",
          "failure": "The original Qwen3.6 page attempt reaches its output limit. The successful Qwen3.8 whole-page reading remains its vote."},
    112: {"strips": column_strips(.063, .844, [.285, .587], [.3425, .605]),
          "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page100 continues the lexicon notices153–158. The left splits precede the154 and157 headings. The right splits lie between complete body lines, checked with enlarged source crops to preserve descenders. The bottom at.844 retains the final body lines in both columns and stops above the smaller apparatus. Every authorial line remains in left-then-right column order.",
          "failure": "The original Qwen3.6 page attempt reaches its output limit. The successful Qwen3.8 whole-page reading remains its vote."},
    113: {"strips": [("left-first", [.045, .065, .495, .251]),
                     ("left-second", [.045, .251, .495, .454]),
                     ("left-third", [.045, .454, .495, .6575]),
                     ("left-fourth", [.045, .6575, .495, .813]),
                     ("right-first", [.505, .065, .97, .253]),
                     ("right-second", [.505, .253, .97, .490]),
                     ("right-third", [.505, .490, .97, .640]),
                     ("right-fourth", [.505, .640, .97, .813])],
          "evidence": "Printed page101 continues codex158 on Phrynichus and opens codex159 on Isocrates. The right column is especially faint. Eight shorter strips preserve each complete large Greek line in column order; the final right split precedes the159 heading. Enlarged boundary checks preserve descenders and the breathing marks above the following lines. The bottom at.813 excludes the smaller critical apparatus. The body contains no long dotted lacuna requiring a special ellipsis instruction.",
          "failure": "The original Qwen3.8 attempt reaches its output limit and triggers the frozen mark-loss screen. The Qwen3.6 whole-page reading remains its independent vote; the retry still requires completed source and mark review."},
}

# New checkpoint-specific requests never alter a previously queued manifest.
EXTRA_REVIEWS = {
    "0047-qwen36": {"page": 47, "checkpoints": [CHECKPOINT36],
                    "failure": "The stop-terminated Qwen3.6 original ends codex72 with an unprinted repeated ἢ sequence. Source inspection confirms further body text after that point. Use the same reviewed four strip boundaries in this separately pinned checkpoint request; retain the original and the independent Qwen3.8 retry assembly."},
}

SUPPLEMENT_REVIEWS = {
    (50, "left-lower"): {
        "cuts": [.456, .583, .712, .835],
        "evidence": "The lower left body on printed page38 is faint. Its first enlarged retry still repeats text and reaches the output limit. Three shorter strips retain the same complete source lines: the.583 boundary falls after the line ending τὴν, and the.712 boundary follows the line ending ἐκκαίει. The final strip includes the paragraph beginning Δαρεῖος νοσήσας through the left-column foot. The union is exactly the reviewed failed lower-left crop; all other successful retry strips remain unchanged.",
    },
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build_retry(page):
    review = REVIEWS[page]
    original = build() if page <= 279 else build_later_gap()
    source_page = next(p for p in original["pages"] if p["scan_page"] == page)
    strips = review.get("strips")
    if strips is None:
        cut, top, bottom = review["cut"], review["top"], review["bottom"]
        strips = [("left-upper", [.045, top, .495, cut]),
                  ("left-lower", [.045, cut, .495, bottom]),
                  ("right-upper", [.505, top, .97, cut]),
                  ("right-lower", [.505, cut, .97, bottom])]
    return {"schema_version": 1, "work": "photius.bibliotheca", "review_date": "2026-10-18",
            "purpose": "Replace only a failed checkpoint's whole-page attempt with a separately reviewed strip assembly; retain successful checkpoint readings and all failed originals.",
            "retry_of": {"path": "data/ocr_requests/photius-bekker-first-volume.json" if page <= 279 else "data/ocr_requests/photius-bekker-later-gap.json",
                         "sha256": hashlib.sha256(encode(original)).hexdigest(), "page_id": source_page["id"]},
            "checkpoints": review.get("checkpoints", [CHECKPOINT38]), "sources": original["sources"], "prompt": original["prompt"],
            "review": {"checked_scan_pages": [page], "accepted_for_primary_ingest": False,
                       "evidence": review["evidence"], "failure": review["failure"],
                       "admission_policy": "Only the listed checkpoint receives an assembled replacement vote after a completed output-to-scan review. Keep every original and retry prediction; no extra votes or arbitrary choice."},
            "pages": [{"id": source_page["id"] + "-" + name, "source": source_page["source"],
                       "scan_page": page, "printed_page": source_page["printed_page"], "region": region,
                       "max_side": 3600, "role": "reviewed-page-retry", "reading_order": order,
                       "prompt_suffix": "This crop contains one complete part of a single Greek body column. Read every complete line from left to right, then down. Preserve any codex heading; do not repeat words or complete text beyond the crop."}
                      for order, (name, region) in enumerate(strips)]}


def manifest_path(page):
    return Path(f"data/ocr_requests/photius-bekker-page{page:04d}-retry.json")


def variant_path(name):
    return Path(f"data/ocr_requests/photius-bekker-page{name}-retry.json")


def build_variant(name):
    import copy
    review = EXTRA_REVIEWS[name]
    manifest = copy.deepcopy(build_retry(review["page"]))
    manifest["checkpoints"] = review["checkpoints"]
    manifest["review"]["failure"] = review["failure"]
    return manifest


def supplement_path(page, name):
    return Path(f"data/ocr_requests/photius-bekker-page{page:04d}-{name}-supplement.json")


def build_supplement(page, name):
    review = SUPPLEMENT_REVIEWS[(page, name)]
    parent = build_retry(page)
    target = next(p for p in parent["pages"] if p["id"].endswith("-" + name))
    x0, y0, x1, y1 = target["region"]
    cuts = review["cuts"]
    if cuts[0] != y0 or cuts[-1] != y1 or cuts != sorted(set(cuts)):
        raise ValueError("Supplement must partition the exact reviewed parent strip")
    return {"schema_version": 1, "work": parent["work"], "review_date": parent["review_date"],
            "purpose": "Replace only a failed retry strip within one model-family assembly; preserve all original and retry attempts and all successful sibling strips.",
            "supplements": {"manifest_path": manifest_path(page).as_posix(),
                            "manifest_sha256": hashlib.sha256(encode(parent)).hexdigest(),
                            "replaces_region": target["id"], "page_id": parent["retry_of"]["page_id"]},
            "checkpoints": parent["checkpoints"], "sources": parent["sources"], "prompt": parent["prompt"],
            "review": {"checked_scan_pages": [page], "accepted_for_primary_ingest": False,
                       "evidence": review["evidence"],
                       "admission_policy": "Require exact failed parent-strip evidence and completed output-to-scan review. Assemble these parts once in place of that strip; retain successful siblings and one vote per model family."},
            "pages": [{**target, "id": target["id"] + f"-part{order+1:02d}",
                       "region": [x0, low, x1, high], "reading_order": order,
                       "role": "reviewed-failed-strip-supplement",
                       "prompt_suffix": "This crop contains a short consecutive part of one Greek body column. Transcribe each complete line exactly once from left to right, then down. Do not repeat words, reconstruct missing text, or continue beyond the crop."}
                      for order, (low, high) in enumerate(zip(cuts, cuts[1:]))]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=int, action="append", choices=sorted(REVIEWS))
    parser.add_argument("--variant", action="append", choices=sorted(EXTRA_REVIEWS))
    args = parser.parse_args()
    for page in args.page or ([] if args.variant else sorted(REVIEWS)):
        path = ROOT / manifest_path(page)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(build_retry(page)))
        print(f"Pinned scan {page}: {len(build_retry(page)['pages'])} strips, listed checkpoint only")
    for page, name in sorted(SUPPLEMENT_REVIEWS):
        if args.variant or args.page and page not in args.page:
            continue
        path = ROOT / supplement_path(page, name)
        path.write_bytes(encode(build_supplement(page, name)))
        print(f"Pinned scan {page}: shorter {name} supplement")
    for name in args.variant or ([] if args.page else sorted(EXTRA_REVIEWS)):
        path = ROOT / variant_path(name)
        path.write_bytes(encode(build_variant(name)))
        print(f"Pinned checkpoint-specific variant {name}")
