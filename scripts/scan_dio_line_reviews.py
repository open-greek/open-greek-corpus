"""A source-checked polytonic line above unchanged independent Dio OCR votes."""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = "data/ingest_reviews/coverage/dio-zonaras-378-line-review.json"
PAGE = "dio-cary-v2-pdf0195-comparison"
REVIEW = "cary-zonaras-378-first-line-2026-10-18"
SOURCE_SHA256 = "57ebb19f9880de06c18d67676f15b59b987944de1bcf1c3023b11ea1a618901c"
IMAGE_SHA256 = "a4af8e661151b3858b5a76c0a6597af13bc1a4b03c0523084c91c740c652c341"
LINE = "τριος ἦν· δι’ ἃ καὶ τὸν φθόνον ἐξέφυγεν. ἴσος"
WORDS = ["τριος", "ἦν", "δι’", "ἃ", "καὶ", "τὸν", "φθόνον", "ἐξέφυγεν", "ἴσος"]
PINS = {
    "qwen36": "47779b1b1e5c7446b41380d3c2877e69134674dc0d142262cbefd828cdc73252",
    "qwen38": "4072f6239bad42773a3728b3e872e03f0bd25a1937953e6b278971836f4012dd",
}
PREVIOUS_PINS = {
    "qwen36": "cf27b9f056e047102adcd8fc56003cfc06b21b2c6be9d291ad93906bd6ad0cdc",
    "qwen38": "9e6fb543bc9ce5773af6d3998c4d0c962925c6102b850ccae4128baac4997790",
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def sha(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def key(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(c).startswith("L")).replace("ς", "σ")


def prepare(finer, previous, output):
    records = {}
    from dio_ocr_retries import CHECKPOINTS
    for family in PINS:
        checked = {}
        for label, path, identifier, pin in [
                ("finer", finer[family], PAGE + "-supplement-strip-1-finer-child-1", PINS[family]),
                ("previous", previous[family], "dio-cary-v2-pdf0194-comparison", PREVIOUS_PINS[family])]:
            values = [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]
            metadata = values[0]["_meta"]
            row = next(row for row in values[1:] if row["id"] == identifier)
            if (sha(encoded({"metadata": metadata, "prediction": row})) != pin or
                    (metadata["model"], metadata["revision"]) != CHECKPOINTS[family][:2]):
                raise ValueError("The manually inspected Dio source record changed")
            checked[label] = {"artifact_sha256": pin, "metadata": metadata, "prediction": row}
        records[family] = checked
    record = {"review_id": REVIEW, "reviewed_at": "2026-10-18", "source_kind": "manual-scan-review",
        "source_pdf_sha256": SOURCE_SHA256, "scan_page": 195, "printed_page": 378,
        "region": [.04,.4542,.47,.5085], "image_sha256": IMAGE_SHA256,
        "corrected_line": LINE, "records": records,
        "evidence": "Enlarged inspection of Cary II printed378: every accent and breathing in the first Zonaras9.27 Greek line is visible. Two checkpoints and two enlarged retries still strip its marks. The preceding printed376 comparison ends μέ-; the next begins τριος. Preserve that fragment visibly but exclude it from independent word counts; do not invent a joined spelling.",
        "policy": "A named correction above the merged word network, not an additional model vote. Preserve every raw prediction, raw vote and tied reading in a separate full network.",
        "reversal": "Restore the hash-checked raw network with scripts.scan_dio_line_reviews.unapply_review, or undo the complete admission."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded(record))
    return record


def load_authority():
    raw = (ROOT / AUTHORITY).read_bytes()
    record = json.loads(raw)
    if (record.get("review_id"), record.get("source_pdf_sha256"), record.get("image_sha256"), record.get("corrected_line")) != (REVIEW, SOURCE_SHA256, IMAGE_SHA256, LINE):
        raise ValueError("The named Dio line review changed its source or correction")
    for family, pair in record["records"].items():
        for label, expected in [("finer", PINS[family]), ("previous", PREVIOUS_PINS[family])]:
            value = pair[label]
            if value["artifact_sha256"] != expected or sha(encoded({"metadata": value["metadata"], "prediction": value["prediction"]})) != expected:
                raise ValueError("The named Dio review no longer pins the inspected raw readings")
    return raw, record


def reviewed_line(result, page, source, witnesses, network_path):
    if page["id"] != PAGE:
        return result, None, None
    if (page["work"] != "cassius-dio.historiae-romanae" or page["scan_page"] != 195
            or page["region"] != [0,.4542,.5,.94] or source["sha256"] != SOURCE_SHA256):
        raise ValueError("The named Dio line's source or panel changed")
    authority_raw, authority = load_authority()
    if len(witnesses) != 2:
        raise ValueError("New Dio line witnesses require another source review")
    matched = set()
    for witness in witnesses:
        family = "qwen36" if "3.6" in witness["model"] else "qwen38" if "3.8" in witness["model"] else None
        if family is None or family in matched:
            raise ValueError("Dio source review requires both exact independent checkpoints")
        expected = authority["records"][family]["finer"]
        strips = witness.get("preprocessing", [{}])[-1].get("raw_strips", [])
        if (not strips or strips[0] != expected["prediction"] or
                (witness["model"], witness["revision"]) != (expected["metadata"]["model"], expected["metadata"]["revision"])):
            raise ValueError("A Dio first-line reading changed outside its scan review")
        matched.add(family)
    slots = result["ocr_consensus"]["slots"]
    if len(slots) < len(WORDS):
        raise ValueError("The source-reviewed Dio line lost words")
    for slot, word in zip(slots, WORDS):
        if not slot["readings"] or any(key(r["text"]) != key(word) for r in slot["readings"]):
            raise ValueError("Dio line alignment needs another source review")
    surfaces = list(re.finditer(r"⟦[^⟧]*⟧|\S+", result["text"]))
    boundary = surfaces[len(WORDS)-1].end()
    original_line = result["text"][:boundary]
    raw_key = page["id"] + ":raw-ocr"
    from ocr_consensus import compact_corpus_consensus
    reference = compact_corpus_consensus(result, {"path": network_path, "key": raw_key})["ocr_consensus"]["full_network"]
    audit = {"review_id": REVIEW, "date": "2026-10-18", "source_kind": "manual-scan-review",
        "original_text": original_line, "corrected_text": LINE,
        "original_predictions": {w["id"]: w.get("original_text", w["text"]) for w in witnesses},
        "original_slots": deepcopy(slots[:len(WORDS)]), "source": {"url": source["url"],
            "sha256": SOURCE_SHA256, "scan_page": 195, "printed_page": 378,
            "region": authority["region"], "image_sha256": IMAGE_SHA256},
        "authority": {"path": AUTHORITY, "sha256": sha(authority_raw)}, "evidence": authority["evidence"],
        "eligibility": {"display_fragment": "τριος", "preceding_fragment": "μέ-", "preceding_scan_page": 194,
            "lexical_eligible": False, "joined_spelling_invented": False},
        "reversal": {"raw_network_key": raw_key, "function": "scripts.scan_dio_line_reviews.unapply_review"}}
    corrected = deepcopy(result)
    corrected["text"] = LINE + result["text"][boundary:]
    consumed = sum(slot["lexical_eligible"] for slot in slots[:len(WORDS)])
    analysis = result["analysis_text"].split()
    if analysis[:consumed] != [slot["selected"] for slot in slots[:len(WORDS)] if slot["lexical_eligible"]]:
        raise ValueError("Dio analysis differs from the reviewed slot projection")
    corrected["analysis_text"] = " ".join(WORDS[1:] + analysis[consumed:])
    network = corrected["ocr_consensus"]
    for position, word in enumerate(WORDS):
        slot = network["slots"][position]
        old_status = slot["status"]
        new_status = "incomplete-reading" if position == 0 else "scan-reviewed"
        slot.update(selected=word, status=new_status, lexical_eligible=position != 0,
            lexical_exclusion="source-page-start-fragment" if position == 0 else None, tied_readings=[],
            scan_review={"id": REVIEW, "raw_selected": slots[position]["selected"], "raw_status": old_status})
        network["counts"][old_status] -= 1
        if not network["counts"][old_status]:
            del network["counts"][old_status]
        network["counts"][new_status] = network["counts"].get(new_status, 0) + 1
    network["raw_ocr_network"] = reference
    network["reviewed_corrections"] = [audit]
    network["policy"] += " The named source line review is above unchanged raw model votes; its leading printed continuation remains ineligible."
    return corrected, (raw_key, result), audit


def unapply_review(result, archived_raw_result):
    from ocr_consensus import compact_corpus_consensus
    network = result["ocr_consensus"]
    if [v["review_id"] for v in network.get("reviewed_corrections", [])] != [REVIEW]:
        raise ValueError("This network does not carry the named Dio line review")
    reference = network["raw_ocr_network"]
    actual = compact_corpus_consensus(archived_raw_result,
        {"path": reference["path"], "key": reference["key"]})["ocr_consensus"]["full_network"]
    if actual != reference:
        raise ValueError("The retained raw Dio network changed")
    return deepcopy(archived_raw_result)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for kind in ("finer", "previous"):
        for family in ("qwen36", "qwen38"):
            p.add_argument("--" + kind + "-" + family, type=Path, required=True)
    a = p.parse_args()
    prepare({f: getattr(a, "finer_"+f) for f in PINS},
        {f: getattr(a, "previous_"+f) for f in PINS}, ROOT / AUTHORITY)
