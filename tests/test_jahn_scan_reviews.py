"""Source adjudications preserve raw disagreements and their exact reversals."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import jahn_scan_reviews as review
from ocr_consensus import merge_witnesses


def fixture(tmp_path):
    groups, raw_files, witnesses = {}, [], {"14": [], "17": []}
    captions = [["ἀʹ Λυδιστί.", "βʹ Δαρριοςι.", "ἡ Φυσις.", "δ' Ἰασί.", "εἰ Μετολυσίᾳ.", "ζ' Συντονολυσί."],
                ["α᾽ Λυδιστί.", "β΄ Δωρισί.", "Ἰ Φρυγισί.", "δ' Ἰαστί.", "ε᾽ Μελουδιστί.", "ς Συτονολιδί."]]
    for kind in ["length", "notation"]:
        manifest_raw = (ROOT / f"data/ingest_reviews/jahn-aristides-{kind}-retry.json").read_bytes()
        manifest = json.loads(manifest_raw)
        paths = []
        for model_index, model in enumerate(["Qwen3.6", "Qwen3.8"]):
            metadata = {"model": model, "revision": "pinned", "manifest_sha256": review.sha(manifest_raw)}
            records = []
            for job in manifest["pages"]:
                text = "λόγος σαφής."
                if job["printed_page"] == 14:
                    text = captions[model_index][job["reading_order"] - 2] if job["text_role"] == "mode-caption" else (
                        "πρόλογος σαφής." if job["reading_order"] == 1 else "τέλος σαφές.")
                elif job["printed_page"] == 17:
                    text = "Ἐκθέσεις τῶν κατὰ τόνον." if job["reading_order"] == 1 else "Ἐκθεσις τῶν κατὰ ἡμιτόνιον."
                records.append({"id": job["id"], "scan_page": job["scan_page"], "region": job["region"],
                    "image_sha256": "image:" + job["id"], "finish_reason": "stop", "raw_prediction": text})
            raw = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in [{"_meta": metadata}] + records).encode()
            path = tmp_path / f"{kind}-{model}.jsonl"
            path.write_bytes(raw)
            paths.append(path)
            raw_files.append({"sha256": review.sha(raw), "metadata": metadata, "records": records})
            printed = "14" if kind == "notation" else "17"
            parts = [r for r in records if r["scan_page"] == int(printed) + 73]
            witnesses[printed].append({"id": model + ":" + printed, "model": model, "vote_group": model,
                "artifact_sha256": model + ":" + printed, "text": "\n".join(r["raw_prediction"] for r in parts),
                "preprocessing": [{"raw_strips": parts}]})
        groups[kind] = paths
    path = tmp_path / "source-review.json"
    review.record_reviews(groups["length"], groups["notation"], path)
    inputs = {"primary_manifest": {"sources": {"jahn1882": {"sha256": review.SOURCE_SHA256}}},
        "retry_evidence": {"raw_files": raw_files}, "witnesses": witnesses}
    inputs["scan_review"] = review.load_reviews(inputs, path)
    return inputs, path


def test_caption_and_heading_corrections_preserve_raw_networks_and_unreviewed_prose(tmp_path):
    inputs, path = fixture(tmp_path)
    for printed in [14, 17]:
        original = merge_witnesses(inputs["witnesses"][str(printed)])
        corrected, raw, audit = review.apply_review(original, printed, inputs, "data/changes/networks.json.gz")
        assert raw[1] == original
        assert audit["original_text"] == original["text"]
        assert audit["corrected_text"] == corrected["text"]
        assert review.unapply_review(corrected, raw[1]) == original
        changed_raw = deepcopy(raw[1])
        changed_raw["text"] += " changed"
        with pytest.raises(ValueError, match="network changed"):
            review.unapply_review(corrected, changed_raw)
        if printed == 14:
            assert corrected["text"].startswith("πρόλογος σαφής.")
            assert corrected["text"].endswith("τέλος σαφές.")
            assert "⟦ϛʹ ∥ ςʹ⟧ Συντονολυδιστί." in corrected["text"]
            assert corrected["analysis_text"] == "πρόλογος σαφής Λυδιστί Δωριστί Φρυγιστί Ἰαστί Μιξολυδιστί Συντονολυδιστί τέλος σαφές"
            assert corrected["ocr_consensus"]["counts"]["source-reviewed-numeral"] == 6
        else:
            assert corrected["text"] == "Ἔκθεσις τῶν κατὰ τόνον. Ἔκθεσις τῶν κατὰ ἡμιτόνιον."


def test_source_review_rejects_changed_images_text_or_segment_concordance(tmp_path):
    inputs, path = fixture(tmp_path)
    changed = deepcopy(inputs)
    changed["retry_evidence"]["raw_files"][0]["records"][0]["image_sha256"] = "different-image"
    with pytest.raises(ValueError, match="reading or image changed"):
        review.load_reviews(changed, path)
    document = json.loads(path.read_text())
    document["reviews"][0]["segments"][0]["tokens"][0]["selected"] = "invented"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="reproducible generator"):
        review.load_reviews(inputs, path)
    original = merge_witnesses(inputs["witnesses"]["14"])
    inputs["witnesses"]["14"][0]["text"] += " πρόσθετον"
    with pytest.raises(ValueError, match="segment boundaries"):
        review.apply_review(original, 14, inputs, "data/changes/networks.json.gz")
