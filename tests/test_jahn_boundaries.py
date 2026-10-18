"""Bounded adjacent-leaf evidence excludes fragments, without joined spellings."""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jahn_boundaries import review_boundary
from ocr_consensus import merge_witnesses
from ocr_boundary_fragments import unapply_review


def fixture():
    def witnesses(page, text):
        return [{"id": f"{model}-{page}", "vote_group": model, "artifact_sha256": f"sha-{model}-{page}",
            "text": text, "image_sha256": f"image-{page}"} for model in ["qwen3.6", "qwen3.8"]]
    return {"primary_source": "jahn1882", "primary_manifest": {"sources": {"scan": {
        "url": "https://example.org/source.pdf", "sha256": "source-digest"}}, "pages": [
        {"id": f"page-{n}", "book": 1, "printed_page": n, "scan_page": n + 73,
            "source": "scan", "region": [.04, .04, .95, .9]} for n in [1, 2]]},
        "witnesses": {"1": witnesses(1, "ὁ λό-"), "2": witnesses(2, "γος σαφής")}}


def test_same_book_adjacent_hyphen_and_verified_body_start_exclude_only_fragment():
    inputs = fixture()
    original = merge_witnesses(inputs["witnesses"]["2"])
    corrected, raw, audit = review_boundary(original, 2, inputs, "data/changes/networks.json.gz")
    assert corrected["text"] == original["text"] == "γος σαφής"
    assert corrected["analysis_text"] == "σαφής"
    assert raw[0] == "2:raw-ocr"
    assert audit["original_analysis_text"] == "γος σαφής"
    assert audit["boundary_observations"]["qwen3.6"]["previous_terminal"] == "λό-"
    assert unapply_review(corrected, raw[1]) == original
    assert "λόγος" not in corrected["text"]


def test_uncertain_or_cross_book_boundaries_do_not_create_an_eligibility_review():
    for defect in ["book", "gap", "title", "disagreement", "missing-hyphen", "notation"]:
        inputs = fixture()
        if defect == "book":
            inputs["primary_manifest"]["pages"][1]["book"] = 2
        elif defect == "gap":
            inputs["primary_manifest"]["pages"][1]["scan_page"] += 1
        elif defect == "title":
            for witness in inputs["witnesses"]["2"]:
                witness["text"] = "ΠΕΡΙ ΜΟΥΣΙΚΗΣ γος σαφής"
        elif defect == "disagreement":
            inputs["witnesses"]["2"][0]["text"] = "γως σαφής"
        elif defect == "missing-hyphen":
            inputs["witnesses"]["1"][0]["text"] = "ὁ λό"
        else:
            inputs["page_text_roles"] = {"2": ["authorial-notation-heading"]}
        original = merge_witnesses(inputs["witnesses"]["2"])
        assert review_boundary(original, 2, inputs, "data/changes/networks.json.gz") == (original, None, None)
