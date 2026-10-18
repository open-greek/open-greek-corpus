"""Exclude independently verified page-start fragments without joining words."""
from __future__ import annotations

import unicodedata


def review_boundary(result, printed_page, inputs, network_path):
    if inputs.get("primary_source") != "jahn1882" or printed_page <= 1:
        return result, None, None
    if result["ocr_consensus"].get("reviewed_corrections"):
        return result, None, None
    pages = {page["printed_page"]: page for page in inputs["primary_manifest"]["pages"]}
    previous_page, page = pages[printed_page - 1], pages[printed_page]
    if (previous_page["book"] != page["book"] or previous_page["scan_page"] + 1 != page["scan_page"] or
            previous_page["printed_page"] + 1 != page["printed_page"] or
            previous_page["source"] != page["source"] or
            inputs.get("page_text_roles", {}).get(str(printed_page), ["authorial-prose"])[0] != "authorial-prose"):
        return result, None, None
    previous = inputs["witnesses"][str(printed_page - 1)]
    current = inputs["witnesses"][str(printed_page)]
    from ocr_consensus import alignment_key, greek_letter, tokenize
    body_start_evidence = {}
    for witness in current:
        tokens = tokenize(witness["text"])
        if not tokens:
            return result, None, None
        initial = tokens[0][0]
        letters = [c for c in initial if greek_letter(c)]
        prefix = witness["text"].lstrip().split(initial, 1)[0]
        if (len(letters) < 2 or not letters[0].islower() or
                any(unicodedata.category(c).startswith("L") for c in prefix) or
                alignment_key(initial) in {"περι", "μουσικησ", "αριστειδου", "βιβλιον"}):
            return result, None, None
        body_start_evidence[witness["id"]] = (
            "The first Greek token starts the source-bounded body after numeric labels or punctuation, "
            "has at least two Greek letters and starts lowercase. Initial running headers are removed "
            "by their separate recorded rule; titles and book openings are excluded.")

    def region(job, witnesses):
        source = inputs["primary_manifest"]["sources"][job["source"]]
        images = sorted({image for witness in witnesses for image in
            witness.get("source_image_sha256s", [witness.get("image_sha256")]) if image})
        witness_regions = [{"id": witness["id"], "images": [
            {"image_sha256": row["image_sha256"], "region": row["region"]}
            for correction in witness.get("preprocessing", []) for row in correction.get("raw_strips", [])]
            or [{"image_sha256": witness.get("image_sha256"), "region": witness.get("region", job["region"])}]}
            for witness in witnesses]
        return {"id": job["id"], "book": job["book"], "printed_page": job["printed_page"],
            "scan_page": job["scan_page"], "region": job["region"], "url": source["url"],
            "sha256": source["sha256"], "image_sha256": images, "witness_image_regions": witness_regions}

    from ocr_boundary_fragments import exclude_leading_fragment
    return exclude_leading_fragment(result, previous, current,
        previous_region=region(previous_page, previous), current_region=region(page, current),
        body_start_evidence=body_start_evidence,
        raw_network_reference={"path": network_path, "key": f"{printed_page}:raw-ocr"},
        review_id="jahn-leading-fragment:" + page["id"], reviewed_at="2026-10-18",
        adjacency_evidence="The source-checked Jahn manifest places these consecutive physical leaves and printed pages in the same book, with no intervening leaf. Both independent model families retain the preceding terminal printed hyphen and the same following lowercase continuation. Each original or reviewed retry image remains pinned. Preserve both fragments without supplying a joined spelling.")
