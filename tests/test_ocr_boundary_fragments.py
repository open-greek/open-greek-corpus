from copy import deepcopy
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ocr_boundary_fragments import exclude_leading_fragment, unapply_review
from ocr_consensus import merge_witnesses, compact_corpus_consensus, restore_corpus_consensus


def fixture():
    previous = [{"id": str(number), "vote_group": str(number), "artifact_sha256": str(number),
                 "text": "ἐπὶ τὴν περιφέρειαν πιπτέ-"} for number in (6, 8)]
    current = [dict(value, text="τωσαν κατὰ τὰ σημεῖα.") for value in previous]
    result = merge_witnesses(current)
    arguments = {"previous_region": {"work": "conica", "book": "1", "printed_page": 10},
        "current_region": {"work": "conica", "book": "1", "printed_page": 12},
        "body_start_evidence": {value["id"]: "Verified crop begins with body continuation." for value in current},
        "raw_network_reference": {"path": "data/corpus_changes/test/networks.json.gz", "key": "page12:raw-ocr"},
        "review_id": "test-page12", "reviewed_at": "2026-10-18",
        "adjacency_evidence": "Consecutive printed Greek leaves within Book I; no omitted leaf."}
    return previous, current, result, arguments


def test_boundary_review_changes_eligibility_without_supplying_a_word():
    previous, current, raw, arguments = fixture()
    before = deepcopy(raw)
    corrected, archived, audit = exclude_leading_fragment(raw, previous, current, **arguments)
    assert raw == before and archived[1] == before
    assert corrected["text"] == raw["text"] == "τωσαν κατὰ τὰ σημεῖα."
    assert corrected["analysis_text"] == "κατὰ τὰ σημεῖα"
    assert corrected["ocr_consensus"]["slots"][0]["readings"] == raw["ocr_consensus"]["slots"][0]["readings"]
    assert corrected["ocr_consensus"]["slots"][0]["status"] == "continuation-fragment"
    assert not corrected["ocr_consensus"]["slots"][0]["lexical_eligible"]
    assert len(corrected["ocr_consensus"]["slots"]) == len(raw["ocr_consensus"]["slots"])
    assert audit["original_text"] == audit["corrected_text"]
    assert audit["boundary_observations"]["6"]["previous_terminal"] == "πιπτέ-"
    compact = compact_corpus_consensus(corrected, {"path": arguments["raw_network_reference"]["path"], "key": "page12"})
    assert restore_corpus_consensus(compact, corrected) == corrected
    assert unapply_review(compact, archived[1]) == before
    with pytest.raises(ValueError, match="original network"):
        unapply_review(compact, dict(before, text="ἄλλο"))


@pytest.mark.parametrize("defect", ["one-group", "duplicate-group", "missing-hyphen", "different-ending", "different-beginning", "unverified-start", "missing-adjacency"])
def test_uncertain_boundaries_remain_unchanged(defect):
    previous, current, raw, arguments = fixture()
    if defect == "one-group":
        previous, current = previous[:1], current[:1]
    elif defect == "duplicate-group":
        previous.append(previous[0].copy())
    elif defect == "missing-hyphen":
        previous[0]["text"] = previous[0]["text"].rstrip("-")
    elif defect == "different-ending":
        previous[0]["text"] = "διαφορετι-"
    elif defect == "different-beginning":
        current[0]["text"] = "ἄλλα κατὰ τὰ σημεῖα."
    elif defect == "unverified-start":
        arguments["body_start_evidence"] = {}
    else:
        arguments["adjacency_evidence"] = ""
    assert exclude_leading_fragment(raw, previous, current, **arguments) == (raw, None, None)
