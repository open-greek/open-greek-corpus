"""Named scan-backed title corrections layered above unchanged OCR votes."""
from copy import deepcopy
import re

PAGE = "pappialexandrin01pappgoog-pdf0017"
SOURCE_SHA256 = "2ce354ebd49cfa7bfe3cd02b2870cea3c0997630f23bc527f1a1e7d8b3c02c95"
IMAGE_SHA256 = "ee4b2e3bf379946d4e455b0b0c14dbe75ce30e91a4a169bb832cf6d48aa44639"
REVIEW = "pappus-vi-opening-stigma-2026-10-18"
TITLE = "ΠΑΠΠΟΥ ΑΛΕΞΑΝΔΡΕΩΣ ΣΥΝΑΓΩΓΗΣ"


def reviewed_title(result, page, source, witnesses, network_path):
    """Return corrected result, original raw-network entry and an exact audit."""
    if page["id"] != PAGE:
        return result, None, None
    if (page["work"] != "pappus-mathematics.synagoge" or page["book"] != "6" or
            source["sha256"] != SOURCE_SHA256 or page["scan_page"] != 17 or page["region"] != [0, 0, 1, 1] or
            {value["image_sha256"] for value in witnesses} != {IMAGE_SHA256}):
        raise ValueError("The reviewed Pappus VI title source or image region changed")
    slots = result["ocr_consensus"]["slots"]
    if len(slots) < 4 or [slot["selected"] for slot in slots[:3]] != TITLE.split():
        raise ValueError("The Pappus VI opening no longer has the reviewed title structure")
    if slots[3]["selected"] == "Ϛ":
        return result, None, None
    match = re.match(r"^" + TITLE + r" (?:⟦[^⟧]+⟧|[ζΖϚϛςσ])[.΄ʹ']*(?=\s)", result["text"])
    if not match:
        raise ValueError("The Pappus VI title numeral needs a new scan review")
    raw_key = page["id"] + ":raw-ocr"
    from ocr_consensus import compact_corpus_consensus
    raw_reference = compact_corpus_consensus(result, {"path": network_path, "key": raw_key})["ocr_consensus"]["full_network"]
    original_title = match[0]
    corrected_title = TITLE + " Ϛ."
    audit = {"review_id": REVIEW, "date": "2026-10-18", "source_kind": "manual-scan-review",
        "original_text": original_title, "corrected_text": corrected_title,
        "original_predictions": {value["id"]: value.get("original_text", value["text"]) for value in witnesses},
        "raw_numeral_votes": deepcopy(slots[3]),
        "source": {"url": source["url"], "sha256": source["sha256"], "scan_page": 17,
            "printed_page": 474, "region": page["region"],
            "image_sha256": sorted({value["image_sha256"] for value in witnesses})},
        "evidence": "Manual enlarged inspection of Hultsch volume II printed page 474 (PDF17): the title ends with stigma, the numeral six, rather than zeta, the numeral seven. The book assignment independently agrees with the volume's table of contents and the Book VII opening at printed634.",
        "reversal": {"raw_network_key": raw_key, "function": "scripts.scan_title_reviews.unapply_review",
            "policy": "Restore the raw network to unapply only this named review; --undo restores the complete pre-admission files. All original model predictions and raw word votes remain unchanged."}}
    corrected = deepcopy(result)
    corrected["text"] = corrected_title + result["text"][match.end():]
    analysis = result["analysis_text"].split()
    consumed = 4 if slots[3]["lexical_eligible"] else 3
    if analysis[:3] != TITLE.split():
        raise ValueError("Pappus title analysis projection differs from its raw slots")
    corrected["analysis_text"] = " ".join(TITLE.split() + ["Ϛ"] + analysis[consumed:])
    network = corrected["ocr_consensus"]
    slot = network["slots"][3]
    old_status = slot["status"]
    slot.update(selected="Ϛ", status="scan-reviewed", lexical_eligible=True,
        lexical_exclusion=None, tied_readings=[],
        scan_review={"id": REVIEW, "raw_selected": slots[3]["selected"],
                     "raw_status": old_status, "corrected_selected": "Ϛ"})
    network["counts"][old_status] -= 1
    if network["counts"][old_status] == 0:
        del network["counts"][old_status]
    network["counts"]["scan-reviewed"] = network["counts"].get("scan-reviewed", 0) + 1
    network["raw_ocr_network"] = raw_reference
    network["reviewed_corrections"] = [audit]
    network["policy"] += " Named scan reviews are explicit correction layers above unchanged raw model votes, retained in the separate raw network."
    return corrected, (raw_key, result), audit


def unapply_review(result, archived_raw_result):
    """Recover the unchanged raw vote network for this named correction only."""
    from ocr_consensus import compact_corpus_consensus
    network = result["ocr_consensus"]
    if [value["review_id"] for value in network.get("reviewed_corrections", [])] != [REVIEW]:
        raise ValueError("This result does not carry the named Pappus title review")
    reference = network["raw_ocr_network"]
    actual = compact_corpus_consensus(archived_raw_result,
        {"path": reference["path"], "key": reference["key"]})["ocr_consensus"]["full_network"]
    if actual != reference:
        raise ValueError("The original OCR network differs from the title review's retained evidence")
    return deepcopy(archived_raw_result)
