#!/usr/bin/env python3
"""Prepare source-reviewed missing-column requests without changing corpus text."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

from repair_photius_index import input_bytes

ROOT = Path(__file__).resolve().parents[1]
REQUEST = Path("data/ocr_requests/photius-bekker-body-recovery.json")
PILOT = Path("data/ocr_requests/photius-bekker-body-recovery-pilot.json")
REVIEW = Path("data/ingest_reviews/photius-bekker-body-recovery.json")
PDF_SHA = "fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb"
PDF_URL = "https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf"
LIBRARY = Path("data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz")
LIBRARY_SHA = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
PROMPT = """Transcribe only the large Greek authorial text in this scanned column strip.
Preserve polytonic accents, breathings, punctuation, headings and literal printed
word fragments. Standard Greek typographic ligatures may be written as their
constituent Greek letters; record no invented letters. Do not complete a word
cut at a column or strip boundary, expand an abbreviation, modernize spelling,
correct the printed text, translate or explain. Omit marginal reference numbers,
running headers, page numbers and smaller critical apparatus. Read down this
single column, preserving complete source lines as separate lines. Output only
the transcription."""
ANCHORS = {
    "helladius_chrestomathia_photius_bekker_v2_0065.9": "1c068d9f7d8af33482c521268f49d3feeccb878e953165278cc441ce3e6884e6",
    "helladius_chrestomathia_photius_bekker_v2_0066.1": "8c05dc57c4ccfe3f09ba0dafa9606fd7e93a5578cb879a48967c3e889953e49e",
    "helladius_chrestomathia_photius_bekker_v2_0073.1": "4780a81d446c2868648baeea5324b2f4f4e254f3dde01a02bd36ee4e06aac915",
    "helladius_chrestomathia_photius_bekker_v2_0074.1": "b1c721583a5b2a403f845379a4727f6686a94bfd7498cdc8df872ccb7072aed3",
}
CASES = {
    66: {"column": "left", "x": [.055, .413], "cuts": [.108, .2113, .3106, .4380, .6665],
        "section": 343, "window": [0, 1884], "held": [],
        "anchors": list(ANCHORS)[:2], "insertion": "Before the existing physical-page66 first row, after page65 body.",
        "start_evidence": "The missing left column starts ἄπορον δὲ ἐνθυμηθῆναι, continuing the preceding physical page65 paragraph.",
        "end_evidence": "Keep the authorial heading Ἐκ τοῦ αὐτοῦ βίου through διαλάμποντα at the left-column bottom. The existing right column starts καὶ Πυθαγόρας. Smaller apparatus is below the crop.",
        "evidence": "All39 served page66 body rows transcribe the right column. The complete printed left column is absent even from the immutable historical OCR, rather than removed by the later apparatus layer."},
    73: {"column": "right", "x": [.58, .936], "cuts": [.112, .2282, .3400, .4501, .53455, .651],
        "section": 350, "window": [1855, 3689], "held": [[1845, 1855]],
        "anchors": list(ANCHORS)[2:], "insertion": "After the existing physical-page73 left-column row, before page74 body.",
        "start_evidence": "The first printed right-column token continues a word divided at the end of the left column. Transcribe its literal fragment; never supply the missing prefix. Source Library's whole βεβλεῦσθ’ is held separately; comparison begins at the following complete νομίζων.",
        "end_evidence": "The missing right column ends with the phrase εἰς τὸν Γοργίαν above the smaller apparatus. Keep the two authorial subsection headings inside the column; omit marginal numbers.",
        "evidence": "The single served page73 body row stops at the bottom of the left column. The printed right column is absent even from the immutable historical OCR."},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def row_sha(row):
    return sha(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def build(root=ROOT):
    source_raw = (root / LIBRARY).read_bytes()
    if sha(source_raw) != LIBRARY_SHA:
        raise ValueError("Pinned Source Library comparison source changed")
    document = json.loads(gzip.decompress(source_raw))
    sections = {int(s["label"].removeprefix("Page s")): s for s in document["sections"]}
    # Earlier source rows stay immutable even after this recovery is applied.
    rows = {row["locus"]: row for row in map(json.loads, input_bytes(root).splitlines())}
    for locus, digest in ANCHORS.items():
        if locus not in rows or row_sha(rows[locus]) != digest:
            raise ValueError("Reviewed legacy body boundary changed: " + locus)
    coverage = json.loads((root / "data/corpus_changes/photius-bekker-coverage/coverage.json").read_bytes())
    credit = coverage["source_library"]
    if credit["sha256"] != LIBRARY_SHA or credit["license"]["url"] != "https://creativecommons.org/licenses/by-sa/4.0/":
        raise ValueError("Pinned Source Library identity or rights changed")
    retained_credit = {key: credit[key] for key in ("edition", "url", "sha256", "license", "rights", "api_notice_url", "api_notice_checked_date", "separate_api_notice")}
    retained_credit.update(attribution=document["origin"]["label"], source_citation=document["sourceCitation"])
    reviews, jobs = [], []
    for number, case in CASES.items():
        coordinates = case["x"] + case["cuts"]
        if (not all(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1 for value in coordinates)
                or len(case["x"]) != 2 or case["x"][0] >= case["x"][1]
                or len(case["cuts"]) < 2 or any(a >= b for a, b in zip(case["cuts"], case["cuts"][1:]))):
            raise ValueError("Reviewed column strips must form a finite nonoverlapping partition")
        section = sections[case["section"]]
        text = "\n".join(block["text"] for block in section["blocks"])
        start, end = case["window"]
        if ((number == 66 and (not text[end:].startswith("καὶ Πυθαγόρας ") or start != 0))
                or (number == 73 and (not text[start:].startswith("νομίζων οἴκαδε ") or end != len(text)))):
            raise ValueError("Reviewed digital column boundary changed")
        identifier = f"photius-bekker-legacy-{number:04d}-{case['column']}"
        regions = [[case["x"][0], lo, case["x"][1], hi] for lo, hi in zip(case["cuts"], case["cuts"][1:])]
        reviews.append({"id": identifier, "scan_page": number, "printed_page": number + 265,
            "source": "photius-bekker-legacy", "column": case["column"], "region": [case["x"][0], case["cuts"][0], case["x"][1], case["cuts"][-1]],
            "strip_regions": regions, "start_evidence": case["start_evidence"], "end_evidence": case["end_evidence"],
            "evidence": case["evidence"], "insertion": case["insertion"],
            "legacy_anchors": [{"locus": locus, "row_sha256": ANCHORS[locus], "original_row": rows[locus]} for locus in case["anchors"]],
            "leading_source_fragment": number == 73,
            "source_library_window": {"path": LIBRARY.as_posix(), "sha256": LIBRARY_SHA, "section": section["id"],
                "section_sha256": row_sha(section), "start": start, "end": end, "original_text": text[start:end],
                "held_spans": [{"start": lo, "end": hi, "original_text": text[lo:hi],
                    "reason": "Digital whole word crosses the printed column boundary; no complete-word vote for the isolated source fragment."} for lo, hi in case["held"]],
                "role": "Comparison witness only until completed independent scan readings and exact source bounds have been reviewed.",
                "page_label_qualification": f"Source Library s{case['section']} matches legacy physical PDF{number}/printed{number + 265}; its label is not the legacy PDF page number."}})
        for order, region in enumerate(regions, 1):
            jobs.append({"id": f"{identifier}-part{order:02d}", "source": "photius-bekker-legacy", "scan_page": number,
                "printed_page": number + 265, "region": region, "max_side": 3600, "reconstructs": identifier,
                "reading_order": order, "role": "missing-authorial-column",
                "prompt_suffix": "This strip begins with a printed continuation fragment. Preserve only its visible letters; do not reconstruct the word." if number == 73 and order == 1 else "Preserve all visible Greek headings and literal line-end fragments."})
    review = {"schema_version": 1, "kind": "source-reviewed-missing-photius-columns", "work": "photius.bibliotheca",
        "reviewed_at": "2026-10-18", "source_scan": {"url": PDF_URL, "sha256": PDF_SHA, "edition": "Bekker1825, original second volume", "license": "PD"},
        "scope": "Pilot geometry for the missing left column of physical page66 and missing right column of physical page73. No existing reading is corrected by this preparer.",
        "geometry_policy": "Contiguous nonoverlapping horizontal strips partition each reviewed column once. Cuts lie between complete printed lines; running headers, footer apparatus and printer signatures are outside the body crops.",
        "transcription_convention": "Printed Greek ligatures may be rendered as constituent Greek letters. Abbreviations and split words must remain literal; no unprinted completion or spelling modernization is authorized.",
        "source_library_credit": retained_credit, "regions": reviews,
        "admission_policy": "Requests and comparison windows are not accepted text. Preserve every raw attempt, use at most one assembled vote per independent checkpoint, retain disagreements, exclude source fragments from lexical counts, and preserve historical passage identities. Diagnostic pilot attempts must never add an extra vote.",
        "generated_by": "scripts/prepare_photius_body_recovery.py"}
    # The first two jobs form a two-font/source pilot before the full nine strips.
    jobs.sort(key=lambda page: (page["reading_order"] != 1, page["scan_page"], page["reading_order"]))
    request = {"schema_version": 1, "work": "photius.bibliotheca", "review_date": review["reviewed_at"],
        "purpose": "Recover two source-confirmed missing authorial columns as independently reviewed scan witnesses.",
        "sources": {"photius-bekker-legacy": {"url": PDF_URL, "sha256": PDF_SHA, "license": "PD", "citation": "Photius, Bibliotheca, Immanuel Bekker, volume2 (Berlin1825), physical scans66/73, printed331/338."}},
        "prompt": PROMPT, "source_review": {"path": REVIEW.as_posix(), "sha256": sha(encoded(review))},
        "review": {"accepted_for_primary_ingest": False, "source_review_required": True,
            "pilot_policy": "Run the first page66 and page73 strips as a small sanity check before the full request; archive pilots separately and never count them as extra votes."},
        "pages": jobs}
    pilot = copy.deepcopy(request)
    pilot["purpose"] = "Two-strip diagnostic pilot: compare enlarged physical66/73 readings before a complete missing-column run. No pilot outcome is accepted primary text."
    pilot["pages"] = pilot["pages"][:2]
    return {REVIEW: encoded(review), REQUEST: encoded(request), PILOT: encoded(pilot)}


REMAINING_REQUEST = Path("data/ocr_requests/photius-bekker-body-recovery-remaining.json")
REMAINING_REVIEW = Path("data/ingest_reviews/photius-bekker-body-recovery-remaining.json")
LEGACY_PREFIX = "helladius_chrestomathia_photius_bekker_v2_"
REMAINING_ANCHORS = {
    "0078.40": "dbe3c4b214f0928de76b15fde741aa9078edd00b6062b8624d017a3471b6b9ca",
    "0079.1": "09807c8fc6c104d1b80fda32bb41d1e637eb97850f3ce7dd29aad0d86a29d5d1",
    "0090.1": "8bef8d0adb7f9fdb7224697a6023a4c1d389f09946b9cd8ff2c2512a8192633d",
    "0091.1": "d031f1f365fcfbc7f686d3caa2b5fe0b4d7033591ed507148f22950c237967cb",
    "0099.46": "a6497b7254fa9395cc94df84d3cef388c7a51455fa9b69f34445056d8df508d8",
    "0100.1": "d2125161ecbdc70c29cad9afd885d9207dbd628a6f5b7bedff93906e52d4312d",
    "0148.2": "ef2bdff6915fa6825bf8639b728907c9e56e630f3946cd378f0347b7d129ba88",
    "0148.3": "39f2424869b8e6733912112c861b51d95a3308afbe546b054732b4e16b6a802f",
    "0148.4": "7b658ccfaedb399a5c0864ed01e1b03301bb83f95aba99c12a02ea74c773fd9c",
    "0148.5": "9fbfef1f7f91e89c6fd98b9b8b80ca35947f18052cd81705db9caf4b572e854f",
    "0154.39": "4dae8131c3f9ae0272cc2266cebdd2ece8e056914946045797f153574c39970f",
    "0154.50": "5cdd520c5c9d0edb2540f853aedd757a6b3d819e4de2f652f13799e499e7df6b",
    "0155.1": "edada29649eec2a6b5ec921833e95f2a197421a6c0300474c370a17cffce359a",
    "0189.2": "fa5848efa19569f9263776e79b6744e4fe954148dc0927df6741fbcdcc976682",
    "0189.3": "de44cbbeea4b904c26f2003d8d0ba9253dcc79e90d933b82311f2fc4b19bd4a2",
    "0189.4": "566f12b44ce7d3ad149a1be6461e1baacec8995054a692736b2b12868712aa37",
}
REMAINING_CASES = {
    79: {"column": "left", "x": [.21, .57], "cuts": [.105, .34775, .4880, .6285, .674],
        "window": [0, 1932], "expected_start": "καίτοι ἐκ ἦν", "expected_after": "καὶ νοητὰ κ’ τῆς Πλάτωνος",
        "held": [], "anchors": ["0078.40", "0079.1"], "leading_fragment": None, "trailing_fragment": None,
        "legacy_action": {"kind": "insert-before", "locus": "0079.1"},
        "start_evidence": "The complete missing left column starts καίτοι and continues the preceding physical page78 paragraph.",
        "end_evidence": "The left column ends ὅσα ἀφανῆ, before the existing right column's καὶ νοητὰ. The crop ends above the smaller apparatus.",
        "evidence": "The immutable page79 body contains only the right column. All complete left-column lines must be recovered; the marginal reference numbers are not authorial words."},
    90: {"column": "right", "x": [.425, .785], "cuts": [.11, .2330, .3481, .4770, .6050, .695],
        "window": [1957, 3796], "expected_start": "ἐδαπάνων γδ’", "expected_after": "φερομένης",
        "held": [(367, 1941, 1957, "ϰινδυνεύσαντες. ", "The complete digital word crosses the printed left/right column seam; the new right-column continuation may not receive this whole-word vote."),
                 (367, 3796, 3805, "φερομένης", "The digital word completes the printed terminal φερο- fragment with letters from beyond this source page.")],
        "anchors": ["0090.1", "0091.1"], "leading_fragment": "νεύσαντες.", "trailing_fragment": "φερο-",
        "legacy_action": {"kind": "insert-after", "locus": "0090.1"},
        "start_evidence": "The first source token continues the divided κινδυ- at the end of the existing left-column row. Preserve only the visible continuation; comparison begins with the following complete ἐδαπάνων.",
        "end_evidence": "The last large body line ends εἰκῇ φερο-. Preserve that printed fragment, omit every smaller apparatus line below, and do not complete the word from the following page or the digital edition.",
        "evidence": "The single immutable page90 body row covers only the left column. Keep the authorial subsection title, ἐκ τῆς θεωρίας, ἐξ αὐτῆς τῆς μελέτης and τὸ προοίμιον within the missing right column."},
    100: {"column": "left", "x": [.06, .422], "cuts": [.105, .2265, .35415, .4844, .5254, .715],
        "window": [0, 1967], "expected_start": "ἅπασιν ὅτι", "expected_after": "πολλάκις ἐλευθερώσαντος",
        "held": [(376, 4082, 4091, "ἀνθρώποις", "The previous digital section completes ἀνθρώποις, divided on the scan between page99 ἀνθρώ- and page100 ποις. Preserve the literal leading fragment without importing this completed word."),
                 (377, 1967, 1976, "πολλάκις ", "This complete digital token lies beyond the reviewed left-column φωνῆς boundary; it must not complete the terminal πολ-. The scan additionally prints λὰς at the start of the right column, absent from this digital boundary.")],
        "anchors": ["0099.46", "0100.1"], "leading_fragment": "ποις", "trailing_fragment": "πολ-",
        "legacy_action": {"kind": "insert-before", "locus": "0100.1"},
        "start_evidence": "The first source token is literal ποις, continuing page99 ἀνθρώ-. The digital section begins at the next complete ἅπασιν and is not evidence to supply the missing prefix.",
        "end_evidence": "The last left-column line ends φωνῆς πολ-. The existing right column starts λὰς πολλάκις; retain this printed split independently of the digital omission at that boundary. Smaller apparatus is below the crop.",
        "evidence": "The immutable page100 body covers the right column only. Keep the complete authorial Ἐκ τοῦ Ἀρεοπαγιτικοῦ heading and τὸ προοίμιον in their source order."},
    148: {"column": "left", "x": [.055, .419], "cuts": [.3025, .3886, .53125, .650],
        "window": [749, 1879], "expected_start": "αὐταῖς τοίνυν,", "expected_after": "αὐτῆς, πολλὰ",
        "held": [(425, 664, 749, "ἐκ μικρῶν καὶ φαύλων τὸ κατ’ ἀρχὰς εἰς τὸ μεῖζον καὶ τελεώτερον αἱ τέχναι κατέσησαν. ", "The first crop includes two complete contextual lines already represented in old148.2; missing αὐταῖς τοίνυν begins midway through their final printed line. The existing prefix stays held overlap, not a duplicate addition.")],
        "anchors": ["0148.2", "0148.3", "0148.4", "0148.5"], "leading_fragment": None, "trailing_fragment": None,
        "legacy_action": {"kind": "replace-incomplete-row", "locus": "0148.4", "after": "0148.2", "before": "0148.5"},
        "context_overlap": {"existing_locus": "0148.2", "source_lines": 2,
            "source_end_anchor": "αἱ τέχναι κατέστησαν.", "missing_start_anchor": "αὐταῖς τοίνυν",
            "policy": "Preserve raw source context and the old row. Exclude the reviewed contextual prefix only after completed scan readings have been aligned to this exact source boundary; no inferred character offsets are authorized now."},
        "start_evidence": "Start above both complete source lines beginning ἐκ μικρῶν and τελειώτερον. Their prefix belongs to existing148.2; the missing body begins at αὐταῖς τοίνυν on the same second physical line.",
        "end_evidence": "The left-column body ends ἔχοι τις ἂν λέγειν ὑπὲρ, immediately before existing right-column αὐτῆς. The crop stops above the smaller footer apparatus.",
        "evidence": "Old148.4 is a short corrupted remnant in place of the lower left-column passage. Preserve its original reading and all later apparatus-layer exclusions; do not treat it as an independent omission vote. Old148.3 is a marginal citation, not missing body."},
    154: {"column": "right", "x": [.425, .79], "cuts": [.13522, .2760, .3888, .5146, .658],
        "window": [2015, 3865], "expected_start": "σκοπεῖν, ἐπεὶ", "expected_after": "",
        "held": [(431, 2005, 2015, "προὔκειτο ", "The completed digital word crosses the boundary between preserved old154.50 προ- and the first newly recovered printed continuation κειτο. No whole-word completion is authorized.")],
        "anchors": ["0154.39", "0154.50", "0155.1"], "leading_fragment": "κειτο", "trailing_fragment": None,
        "legacy_action": {"kind": "insert-after", "locus": "0154.50"},
        "start_evidence": "The existing154.50 is the first full right-column line and ends προ-. Start below it, retaining the complete following line's literal κειτο continuation. The one-pixel source whitespace separates these skewed printed lines.",
        "end_evidence": "The last right-column body line ends τὴν ὑπὲρ τούτου before the smaller notes. The existing first right-column line is outside the new crop and must not be duplicated.",
        "evidence": "All body after the first right-column line is absent from the immutable historical page154. Existing left-column body rows and154.50 remain unchanged."},
    189: {"column": "left", "x": [.235, .594], "cuts": [.2449, .3712, .4980, .6095, .700],
        "window": [434, 1969], "expected_start": "χειμῶνα (ἔστι", "expected_after": "ταῖς κηδείαις",
        "held": [], "anchors": ["0189.2", "0189.3", "0189.4"], "leading_fragment": None, "trailing_fragment": None,
        "legacy_action": {"kind": "insert-after", "locus": "0189.2", "before": "0189.4"},
        "start_evidence": "Start with the complete printed line χειμῶνα, immediately below the preserved old189.2 ending τὸν μὲν παρ’ αὐτοῖς. The initial crop edge lies in the narrow source interline gap.",
        "end_evidence": "Retain all remaining left-column body through οὕτω φησίν, immediately before the existing right-column ταῖς κηδείαις. The crop ends in the broad whitespace above apparatus.",
        "evidence": "The lower left column is missing between old189.2 and189.4. Old189.3 is a displaced running header already retained separately by the apparatus layer; its removal did not remove this missing body."},
}


def build_remaining(root=ROOT):
    """Build a separate six-case request; never rewrite the frozen two-case run."""
    base = json.loads(build(root)[REVIEW])
    document = json.loads(gzip.decompress((root / LIBRARY).read_bytes()))
    sections = {int(s["label"].removeprefix("Page s")): s for s in document["sections"]}
    rows = {row["locus"]: row for row in map(json.loads, input_bytes(root).splitlines())}
    for suffix, digest in REMAINING_ANCHORS.items():
        locus = LEGACY_PREFIX + suffix
        if locus not in rows or row_sha(rows[locus]) != digest:
            raise ValueError("Reviewed remaining legacy body boundary changed: " + locus)
    reviews, jobs = [], []
    for number, case in REMAINING_CASES.items():
        coordinates = case["x"] + case["cuts"]
        if (len(case["x"]) != 2 or case["x"][0] >= case["x"][1]
                or not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in coordinates)
                or len(case["cuts"]) < 2 or any(a >= b for a, b in zip(case["cuts"], case["cuts"][1:]))):
            raise ValueError("Remaining source strips must form a finite nonoverlapping partition")
        section = sections[number + 277]
        text = "\n".join(block["text"] for block in section["blocks"])
        start, end = case["window"]
        if (not (type(start) is int and type(end) is int and 0 <= start < end <= len(text))
                or not text[start:].startswith(case["expected_start"])
                or (not text[end:].startswith(case["expected_after"]) if case["expected_after"] else end != len(text))):
            raise ValueError("Reviewed remaining digital boundary changed")
        held = []
        for section_number, lo, hi, expected, reason in case["held"]:
            other = sections[section_number]
            original = "\n".join(block["text"] for block in other["blocks"])
            if not (0 <= lo < hi <= len(original)) or original[lo:hi] != expected or not reason:
                raise ValueError("Reviewed held digital fragment or overlap changed")
            if section_number == number + 277 and max(start, lo) < min(end, hi):
                raise ValueError("Held digital text cannot participate in comparison window")
            held.append({"section": other["id"], "section_sha256": row_sha(other), "start": lo, "end": hi,
                "original_text": original[lo:hi], "reason": reason})
        identifier = f"photius-bekker-legacy-{number:04d}-{case['column']}"
        regions = [[case["x"][0], lo, case["x"][1], hi] for lo, hi in zip(case["cuts"], case["cuts"][1:])]
        action = {key: (LEGACY_PREFIX + value if key != "kind" else value) for key, value in case["legacy_action"].items()}
        record = {"id": identifier, "scan_page": number, "printed_page": number + 265,
            "source": "photius-bekker-legacy", "column": case["column"],
            "region": [case["x"][0], case["cuts"][0], case["x"][1], case["cuts"][-1]],
            "strip_regions": regions, "start_evidence": case["start_evidence"], "end_evidence": case["end_evidence"],
            "evidence": case["evidence"], "legacy_action": action,
            "legacy_anchors": [{"locus": LEGACY_PREFIX + suffix, "row_sha256": REMAINING_ANCHORS[suffix],
                "original_row": rows[LEGACY_PREFIX + suffix]} for suffix in case["anchors"]],
            "leading_source_fragment": case["leading_fragment"], "trailing_source_fragment": case["trailing_fragment"],
            "source_library_window": {"path": LIBRARY.as_posix(), "sha256": LIBRARY_SHA,
                "section": section["id"], "section_sha256": row_sha(section), "start": start, "end": end,
                "original_text": text[start:end], "held_spans": held,
                "role": "Comparison witness only pending completed independent scan readings and exact source review.",
                "page_label_qualification": f"Source Library s{number + 277} matches legacy physical PDF{number}/printed{number + 265}; its label is not the legacy PDF page number."}}
        if "context_overlap" in case:
            record["context_overlap"] = copy.deepcopy(case["context_overlap"])
            record["context_overlap"]["existing_locus"] = LEGACY_PREFIX + record["context_overlap"]["existing_locus"]
        reviews.append(record)
        for order, region in enumerate(regions, 1):
            suffix = "Preserve all visible Greek authorial headings and literal line-end fragments."
            if order == 1 and case["leading_fragment"]:
                suffix = "The first printed token is a continuation fragment. Transcribe only its visible letters; never supply its missing prefix."
            if order == 1 and "context_overlap" in case:
                suffix = "The first two complete source lines contain contextual text before αὐταῖς τοίνυν. Transcribe every visible source word in order; do not trim or summarize the context."
            jobs.append({"id": f"{identifier}-part{order:02d}", "source": "photius-bekker-legacy",
                "scan_page": number, "printed_page": number + 265, "region": region, "max_side": 3600,
                "reconstructs": identifier, "reading_order": order, "role": "missing-authorial-body",
                "prompt_suffix": suffix})
    review = {"schema_version": 1, "kind": "source-reviewed-missing-photius-body", "work": "photius.bibliotheca",
        "reviewed_at": "2026-10-18", "source_scan": base["source_scan"],
        "scope": "Six additional source-confirmed omissions on legacy physical pages79,90,100,148,154,189. These requests are independent of the frozen physical66/73 pilot and full request; no corpus text is changed.",
        "geometry_policy": "Each reviewed rectangle is partitioned once into contiguous nonoverlapping strips. Every crop edge has been checked against complete source lines. Page148 deliberately includes two complete contextual lines, explicitly held as overlap until a later audited admission. Running headers and smaller apparatus remain outside all regions.",
        "transcription_convention": base["transcription_convention"], "source_library_credit": base["source_library_credit"],
        "regions": reviews, "admission_policy": base["admission_policy"],
        "legacy_policy": "Preserve every old row and later editorial correction. Legacy actions describe a proposed source boundary only. A later reversible admission must audit exact accepted text, contextual trimming, lexical exclusions for printed fragments, and every disagreement; no digital completion is authorized.",
        "generated_by": "scripts/prepare_photius_body_recovery.py --remaining"}
    request = {"schema_version": 1, "work": "photius.bibliotheca", "review_date": review["reviewed_at"],
        "purpose": "Recover six additional source-confirmed missing authorial regions with independent scan witnesses; retain source fragments and contextual overlap.",
        "sources": {"photius-bekker-legacy": {"url": PDF_URL, "sha256": PDF_SHA, "license": "PD",
            "citation": "Photius, Bibliotheca, Immanuel Bekker, volume2 (Berlin1825), physical scans79/90/100/148/154/189, printed344/355/365/413/419/454."}},
        "prompt": PROMPT, "source_review": {"path": REMAINING_REVIEW.as_posix(), "sha256": sha(encoded(review))},
        "review": {"accepted_for_primary_ingest": False, "source_review_required": True,
            "independence_policy": "One assembled vote per checkpoint only. No raw inference outcome is accepted without source review; keep all variants and original historical rows."},
        "pages": jobs}
    return {REMAINING_REVIEW: encoded(review), REMAINING_REQUEST: encoded(request)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--remaining", action="store_true", help="Prepare only the separate six-case request; preserve the frozen two-case artifacts")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.source_pdf and sha(args.source_pdf.read_bytes()) != PDF_SHA:
        parser.exit(1, "Unpinned legacy source PDF\n")
    artifacts = build_remaining(args.root) if args.remaining else build(args.root)
    for path, raw in artifacts.items():
        target = args.root / path
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        elif args.check and (not target.exists() or target.read_bytes() != raw):
            parser.exit(1, "Photius missing-column request drift: " + path.as_posix() + "\n")
    print(json.dumps({"source_pages": 6 if args.remaining else 2, "full_strips": 25 if args.remaining else 9, "pilot_strips": 0 if args.remaining else 2,
                      "artifacts": {path.as_posix(): sha(raw) for path, raw in artifacts.items()}}))


if __name__ == "__main__":
    main()
