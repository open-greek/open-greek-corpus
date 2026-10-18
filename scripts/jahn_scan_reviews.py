"""Named source corrections for eight short notation headings and captions."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "8ccfbe7e5c43dd4210235296fae29d2b8ffdce2f910e50a80c822e7eee5539c6"
CAPTIONS = ["Λυδιστί", "Δωριστί", "Φρυγιστί", "Ἰαστί", "Μιξολυδιστί", "Συντονολυδιστί"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_tokens(printed, index):
    if printed == 17:
        text = "Ἔκθεσις τῶν κατὰ " + ("τόνον." if index == 0 else "ἡμιτόνιον.")
        return [{"selected": word.rstrip("."), "display": word, "lexical_eligible": True}
            for word in text.split()]
    label = ["αʹ", "βʹ", "γʹ", "δʹ", "εʹ", None][index]
    return [{"selected": label, "display": label or "⟦ϛʹ ∥ ςʹ⟧", "lexical_eligible": False,
        "tied_readings": [] if label else ["ϛʹ", "ςʹ"], "role": "caption-numeral", "ordinal": index + 1},
        {"selected": CAPTIONS[index], "display": CAPTIONS[index] + ".", "lexical_eligible": True}]


def record_reviews(length_paths, notation_paths, output):
    if output.exists():
        raise ValueError("Refusing to replace a completed source review")
    reviews = []
    for printed, paths, name, selected in [
        (17, length_paths, "jahn-aristides-length-retry.json", [1, 2]),
        (14, notation_paths, "jahn-aristides-notation-retry.json", list(range(2, 8)))]:
        raw_manifest = (ROOT / "data/ingest_reviews" / name).read_bytes()
        manifest = json.loads(raw_manifest)
        if manifest["sources"]["jahn1882"]["sha256"] != SOURCE_SHA256:
            raise ValueError("The source-reviewed Jahn edition changed")
        jobs = [p for p in manifest["pages"] if p["printed_page"] == printed and p["reading_order"] in selected]
        images, predictions, runs = {}, {}, []
        for path in paths:
            raw = path.read_bytes()
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
            meta, values = rows[0]["_meta"], {r["id"]: r for r in rows[1:]}
            if meta.get("manifest_sha256") != sha(raw_manifest):
                raise ValueError("Source review refers to a different crop manifest")
            runs.append({"sha256": sha(raw), "model": meta["model"], "revision": meta["revision"]})
            for job in jobs:
                record = values[job["id"]]
                if record.get("finish_reason") != "stop" or record.get("region") != job["region"]:
                    raise ValueError("A reviewed heading or caption is not complete")
                if images.setdefault(job["id"], record["image_sha256"]) != record["image_sha256"]:
                    raise ValueError("Source review images differ between models")
                predictions.setdefault(job["id"], {})[meta["model"]] = record["raw_prediction"]
        if len({r["model"] for r in runs}) != 2:
            raise ValueError("Retain both independently pinned raw model readings")
        segments = []
        for index, job in enumerate(jobs):
            segments.append({"region_id": job["id"], "region": job["region"], "scan_page": job["scan_page"],
                "image_sha256": images[job["id"]], "original_predictions": predictions[job["id"]], "tokens": canonical_tokens(printed, index)})
        reviews.append({"review_id": f"jahn-notation-source-reading:{printed}", "printed_page": printed,
            "scan_page": printed + 73, "source": {**manifest["sources"]["jahn1882"]},
            "manifest": "data/ingest_reviews/" + name, "manifest_sha256": sha(raw_manifest),
            "runs": runs, "segments": segments,
            "evidence": "Enlarged direct inspection of the printed source, independently checked against a second source reading. The two headings read Ἔκθεσις with smooth breathing and acute; the second ends ἡμιτόνιον with rough breathing. The six captions read Λυδιστί, Δωριστί, Φρυγιστί, Ἰαστί, Μιξολυδιστί, Συντονολυδιστί. The sixth numeral's printed stigma/final-sigma-shaped glyph does not distinguish Unicode conventions; preserve both glyph readings and exclude numeral labels from lexical counts. No dictionary or model-score preference is used."})
    document = {"schema_version": 1, "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "source_pdf_sha256": SOURCE_SHA256, "source_kind": "manual-scan-review", "reviews": reviews,
        "policy": "Explicit source adjudications layered above unchanged model votes. Keep every losing reading in the pre-review network and retain all raw source crops."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n")
    return document


def load_reviews(inputs, path):
    document = json.loads(path.read_text())
    if document["source_pdf_sha256"] != inputs["primary_manifest"]["sources"]["jahn1882"]["sha256"]:
        raise ValueError("Jahn source review uses another printed source")
    raw_files = {r["sha256"]: r for r in inputs["retry_evidence"]["raw_files"]}
    for review in document["reviews"]:
        if review["printed_page"] not in {14, 17} or len(review["segments"]) != (6 if review["printed_page"] == 14 else 2):
            raise ValueError("This source review extends beyond the eight inspected Jahn readings")
        if any(segment["tokens"] != canonical_tokens(review["printed_page"], index) for index, segment in enumerate(review["segments"])):
            raise ValueError("Source-adjudicated text changed outside its reproducible generator")
        if sha((ROOT / review["manifest"]).read_bytes()) != review["manifest_sha256"]:
            raise ValueError("Jahn source-review geometry changed")
        for run in review["runs"]:
            raw = raw_files.get(run["sha256"])
            if not raw or any(raw["metadata"][key] != run[key] for key in ["model", "revision"]):
                raise ValueError("Jahn source-review predictions changed")
            records = {r["id"]: r for r in raw["records"]}
            for segment in review["segments"]:
                record = records[segment["region_id"]]
                if (record["image_sha256"] != segment["image_sha256"] or record["region"] != segment["region"] or
                        record["raw_prediction"] != segment["original_predictions"][run["model"]]):
                    raise ValueError("A source-reviewed Jahn reading or image changed")
    return {"document": document, "sha256": sha(path.read_bytes())}


def _display(slot):
    if "source_display" in slot:
        return slot["source_display"]
    if slot["status"] == "unresolved":
        return "⟦" + " ∥ ".join(key or "∅" for key in slot["tied_readings"]) + "⟧"
    if slot["status"] == "omission":
        return ""
    values = Counter(surface for reading in slot["readings"] if reading["text"] == slot["selected"]
        for surface in reading["surfaces"].values())
    maximum = max(values.values())
    winners = sorted(surface for surface, count in values.items() if count == maximum)
    return winners[0] if len(winners) == 1 else "⟦" + " ∥ ".join(winners) + "⟧"


def apply_review(result, printed_page, inputs, network_path):
    document = inputs.get("scan_review", {}).get("document")
    if not document:
        return result, None, None
    review = next((r for r in document["reviews"] if r["printed_page"] == printed_page), None)
    if review is None:
        return result, None, None
    from ocr_consensus import tokenize, compact_corpus_consensus
    slots = result["ocr_consensus"]["slots"]
    if " ".join(filter(None, (_display(s) for s in slots))) != result["text"]:
        raise ValueError("The raw Jahn display no longer matches its vote slots")
    targets = {s["region_id"] for s in review["segments"]}
    target_positions, other_positions = set(), set()
    for witness in inputs["witnesses"][str(printed_page)]:
        parts = witness["preprocessing"][0]["raw_strips"]
        flattened, relevant = [], set()
        for part in parts:
            tokens = tokenize(part["raw_prediction"].strip())
            if part["id"] in targets:
                relevant.update(range(len(flattened), len(flattened) + len(tokens)))
            flattened.extend(tokens)
        if flattened != tokenize(witness["text"]):
            raise ValueError("Reviewed Jahn segment boundaries require a new alignment review")
        index = 0
        for position, slot in enumerate(slots):
            reading = next((r for r in slot["readings"] if witness["id"] in r["support"]), None)
            if reading is None:
                continue
            if index >= len(flattened) or reading["text"] != flattened[index][0]:
                raise ValueError("A Jahn raw word differs from its source-segment alignment")
            (target_positions if index in relevant else other_positions).add(position)
            index += 1
        if index != len(flattened):
            raise ValueError("Jahn source review lacks a complete raw-token concordance")
    start, end = min(target_positions), max(target_positions) + 1
    if set(range(start, end)) != target_positions or other_positions & set(range(start, end)):
        raise ValueError("Jahn source review would replace text outside its reviewed crops")
    corrected = deepcopy(result)
    replacements = []
    for segment in review["segments"]:
        for token in segment["tokens"]:
            replacements.append({"position": 0, "selected": token["selected"],
                "source_display": token["display"], "lexical_eligible": token["lexical_eligible"],
                "status": "scan-reviewed" if token["lexical_eligible"] else "source-reviewed-numeral",
                "tied_readings": token.get("tied_readings", []), "readings": [], "vote_status": "source-adjudication",
                "scan_review": {"id": review["review_id"], "region_id": segment["region_id"],
                    "source_token": token, "raw_network_span": [start, end]}})
    network = corrected["ocr_consensus"]
    network["slots"] = network["slots"][:start] + replacements + network["slots"][end:]
    for position, slot in enumerate(network["slots"]):
        slot["position"] = position
    corrected["text"] = " ".join(filter(None, (_display(s) for s in network["slots"])))
    corrected["analysis_text"] = " ".join(s["selected"] for s in network["slots"] if s["lexical_eligible"])
    raw_key = f"{printed_page}:source-review-raw"
    reference = compact_corpus_consensus(result, {"path": network_path, "key": raw_key})["ocr_consensus"]["full_network"]
    audit = {"generator": "scripts/jahn_scan_reviews.py", "review_id": review["review_id"],
        "source_kind": "manual-scan-review", "timestamp": document["reviewed_at"],
        "original_text": result["text"], "corrected_text": corrected["text"],
        "original_analysis_text": result["analysis_text"], "corrected_analysis_text": corrected["analysis_text"],
        "source_review_sha256": inputs["scan_review"]["sha256"], "source_review": review,
        "raw_slots": deepcopy(slots[start:end]), "raw_network": reference,
        "policy": "Direct source reading above unchanged raw model votes; numeral labels stay visible and excluded from ordinary lexical counts.",
        "reversal": {"function": "scripts.jahn_scan_reviews.unapply_review", "raw_network_key": raw_key}}
    network["counts"] = dict(Counter(s["status"] for s in network["slots"]))
    network["raw_ocr_network"] = reference
    network["reviewed_corrections"] = [audit]
    network["policy"] += " A named scan review adjudicates only the source-bounded short headings and mode captions; raw votes remain separately archived."
    return corrected, (raw_key, result), audit


def unapply_review(result, raw_result):
    from ocr_consensus import compact_corpus_consensus
    reference = result["ocr_consensus"]["raw_ocr_network"]
    if not any(r.get("generator") == "scripts/jahn_scan_reviews.py" for r in result["ocr_consensus"].get("reviewed_corrections", [])):
        raise ValueError("No named Jahn source reading review")
    if compact_corpus_consensus(raw_result, reference)["ocr_consensus"]["full_network"] != reference:
        raise ValueError("The retained pre-review Jahn word network changed")
    return deepcopy(raw_result)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--length", type=Path, action="append", required=True)
    parser.add_argument("--notation", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    record_reviews(args.length, args.notation, args.out)
    print("Recorded the completed source inspection of two headings and six mode captions")


if __name__ == "__main__":
    main()
