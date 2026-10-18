"""Source-verified eligibility reviews for fragments split across scan regions."""
from copy import deepcopy
import unicodedata

PAGE = "apolloniipergaei02apoluoft-pdf0096-letter"
PRECEDING_PAGE = "apolloniipergaei02apoluoft-pdf0094-letter"
SOURCE_SHA256 = "ab8f0c2dd0f4a13f16ba7415e66f571161c08a5004477b0305a6d2016779a9c0"
IMAGE_SHA256 = "db2c7668090fff78361d04889eae150c67f7f724ce12bdee2eefe1162b68ec81"
PRECEDING_IMAGE_SHA256 = "eaae7ea3a9d52c63252712401a408975d2304fb57d3c6f690284317123452955"
REVIEW = "conica-iv-letter-leading-fragment-2026-10-18"


def reviewed_fragment(result, page, source, witnesses, network_path, inputs):
    """Retain the visible continuation but exclude it as an independent word."""
    if page["id"] != PAGE:
        return result, None, None
    previous = [values.get(PRECEDING_PAGE) for values in inputs]
    if (page["work"] != "apollonius-geom.conica" or page["book"] != "4" or
            source["sha256"] != SOURCE_SHA256 or page["scan_page"] != 96 or
            page["region"] != [0, 0.07, 1, 0.659] or
            {value["image_sha256"] for value in witnesses} != {IMAGE_SHA256} or
            any(value is None or value["image_sha256"] != PRECEDING_IMAGE_SHA256 or
                not value["text"].rstrip().endswith("ὅμο-") for value in previous)):
        raise ValueError("The reviewed Conica letter fragment source, images or preceding boundary changed")
    slots = result["ocr_consensus"]["slots"]
    if not slots or slots[0]["selected"] != "γενῆ" or not result["text"].startswith("γενῆ "):
        raise ValueError("The Conica letter continuation needs a new scan review")
    from ocr_consensus import compact_corpus_consensus
    raw_key = page["id"] + ":raw-ocr"
    raw_reference = compact_corpus_consensus(result,
        {"path": network_path, "key": raw_key})["ocr_consensus"]["full_network"]
    corrected = deepcopy(result)
    analysis = result["analysis_text"].split()
    if slots[0]["lexical_eligible"]:
        if not analysis or analysis[0] != "γενῆ":
            raise ValueError("The Conica fragment analysis projection differs from its raw slot")
        analysis = analysis[1:]
    corrected["analysis_text"] = " ".join(analysis)
    audit = {"review_id": REVIEW, "date": "2026-10-18", "source_kind": "manual-scan-review",
        "change_kind": "lexical-eligibility-only", "original_text": "γενῆ", "corrected_text": "γενῆ",
        "original_analysis_text": result["analysis_text"], "corrected_analysis_text": corrected["analysis_text"],
        "original_predictions": {value["id"]: value.get("original_text", value["text"]) for value in witnesses},
        "raw_fragment_votes": deepcopy(slots[0]),
        "source": {"url": source["url"], "sha256": SOURCE_SHA256, "scan_page": 96,
            "printed_page": 4, "region": page["region"], "image_sha256": IMAGE_SHA256},
        "preceding_region": {"id": PRECEDING_PAGE, "scan_page": 94, "printed_page": 2,
            "region": [0, 0.17, 1, 0.825], "image_sha256": PRECEDING_IMAGE_SHA256,
            "terminal_readings": {value["id"]: value["text"].rstrip().split()[-1] for value in previous}},
        "evidence": "Manual enlarged inspection of the two Heiberg volume II letter crops: the first leaf ends with a printed hyphen, and the following leaf begins with the continuation γενῆ. Retain both displayed fragments and their raw votes; count neither fragment as an independent word. No joined spelling is supplied.",
        "reversal": {"raw_network_key": raw_key, "function": "scripts.scan_fragment_reviews.unapply_review",
            "policy": "Restore the unchanged raw network to remove only this eligibility review; --undo restores the complete pre-admission files."}}
    network = corrected["ocr_consensus"]
    old_status = network["slots"][0]["status"]
    network["slots"][0].update(status="scan-reviewed-fragment", lexical_eligible=False,
        lexical_exclusion="source-verified-cross-page-fragment",
        scan_review={"id": REVIEW, "raw_status": old_status, "preceding_region": PRECEDING_PAGE})
    network["counts"][old_status] -= 1
    if network["counts"][old_status] == 0:
        del network["counts"][old_status]
    network["counts"]["scan-reviewed-fragment"] = network["counts"].get("scan-reviewed-fragment", 0) + 1
    network["raw_ocr_network"] = raw_reference
    network["reviewed_corrections"] = [audit]
    network["policy"] += " A named scan review excludes the unchanged leading continuation from independent word counts; raw votes remain in the separate raw network."
    return corrected, (raw_key, result), audit


def unapply_review(result, archived_raw_result):
    """Recover the exact original consensus before fragment eligibility review."""
    from ocr_consensus import compact_corpus_consensus
    network = result["ocr_consensus"]
    if [value["review_id"] for value in network.get("reviewed_corrections", [])] != [REVIEW]:
        raise ValueError("This result does not carry the named Conica fragment review")
    reference = network["raw_ocr_network"]
    actual = compact_corpus_consensus(archived_raw_result,
        {"path": reference["path"], "key": reference["key"]})["ocr_consensus"]["full_network"]
    if actual != reference:
        raise ValueError("The original OCR network differs from the fragment review's retained evidence")
    return deepcopy(archived_raw_result)


def adjacent_mathematical_pages(manifest):
    """Identify same-book adjacent printed Greek leaves, not facing translations."""
    works = {"pappus-mathematics.synagoge", "apollonius-geom.conica"}
    ordered = sorted((page for page in manifest["pages"] if page["work"] in works),
        key=lambda page: (page["work"], int(page["book"]), page["printed_page"]))
    result = {}
    for previous, current in zip(ordered, ordered[1:]):
        if (previous["work"], previous["book"], previous["printed_page"] + 2) == (
                current["work"], current["book"], current["printed_page"]):
            result[current["id"]] = previous
    return result


def reviewed_mathematical_boundary(result, page, previous_page, manifest, inputs, witnesses,
        network_path, clean_body):
    """Verify mathematical body starts and preserve separately reviewed letters."""
    if result["ocr_consensus"].get("reviewed_corrections") or previous_page is None:
        return result, None, None
    from ocr_consensus import alignment_key, greek_letter, tokenize
    from ocr_boundary_fragments import exclude_leading_fragment
    previous = []
    body_start_evidence = {}
    for values, current in zip(inputs, witnesses):
        before = values.get(previous_page["id"])
        if before is None:
            return result, None, None
        before_body, _ = clean_body(before["text"], page["work"])
        previous.append(dict(before, text=before_body, original_text=before["text"]))
        tokens = tokenize(current["text"])
        if not tokens:
            return result, None, None
        initial = tokens[0][0]
        letters = [char for char in initial if greek_letter(char)]
        # A continuation starts within a word. Reject titles, running headers,
        # capitalized opening words and one-letter proposition/section labels.
        if (len(letters) < 2 or not letters[0].islower() or
                alignment_key(initial) in {"κωνικων", "παππου", "συναγωγησ"}):
            return result, None, None
        prefix = current["text"].lstrip().split(initial, 1)[0]
        if any(unicodedata.category(char).startswith("L") for char in prefix):
            return result, None, None
        body_start_evidence[current["id"]] = (
            "The first Greek token begins the cleaned body after only punctuation or numeric labels, "
            "contains at least two Greek letters and starts lowercase. Exact repeated Pappus headers "
            "are removed in their own audit; capitalized/title-like starts and proposition labels are held.")
    def region(value, values):
        source = manifest["sources"][value["source"]]
        return {"id": value["id"], "work": value["work"], "book": value["book"],
            "printed_page": value["printed_page"], "url": source["url"], "sha256": source["sha256"],
            "scan_page": value["scan_page"], "region": value["region"],
            "image_sha256": sorted({item["image_sha256"] for item in values})}
    review_id = "mathematical-leading-fragment:" + page["id"]
    return exclude_leading_fragment(result, previous, witnesses,
        previous_region=region(previous_page, previous), current_region=region(page, witnesses),
        body_start_evidence=body_start_evidence,
        raw_network_reference={"path": network_path, "key": page["id"] + ":raw-ocr"},
        review_id=review_id, reviewed_at="2026-10-18",
        adjacency_evidence="The hash-pinned reviewed source manifests place these leaves consecutively within the same printed book, with printed page numbers differing by two because Latin facing leaves are excluded. Both independent body witnesses show the preceding terminal hyphen and the same leading continuation; no intervening Greek leaf or book boundary is crossed.")
