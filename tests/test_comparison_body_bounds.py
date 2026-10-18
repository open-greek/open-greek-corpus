from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bound_comparison_witness import bound_comparison_witness

BODY = "Ἄνθρωπος ἀγαθὸς καὶ δίκαιος ἀεί ποτε λέγει λόγους καθαροὺς ἐν ἀγορᾷ παρὰ φίλοις ἀληθινούς."


def inputs(body=BODY):
    return [{"id": "fresh36", "vote_group": "qwen36", "text": body},
            {"id": "fresh38", "vote_group": "qwen38", "text": body}]


def test_unreviewed_greek_footer_and_header_never_vote_through_abstention():
    source = {"id": "library", "text": "ΔΙΩΝΟΣ ΡΩΜΑΪΚΑ\n" + BODY + "\nλόγους] λόγον Μ. λείπει τὸ ῥῆμα"}
    bounded, audit = bound_comparison_witness(inputs(), source)
    assert bounded["text"] == BODY
    assert audit["removed_prefix"] == "ΔΙΩΝΟΣ ΡΩΜΑΪΚΑ\n"
    assert audit["removed_footer"] == "\nλόγους] λόγον Μ. λείπει τὸ ῥῆμα"
    assert audit["original_text"] == source["text"]
    assert audit["start_anchor"]["length"] >= 4 and audit["end_anchor"]["length"] >= 4


def test_interior_unique_source_reading_remains_while_bounds_ignore_accents():
    source = {"id": "library", "text": BODY.replace("Ἄνθρωπος", "ἀνθρωπος").replace("λέγει", "διηγεῖται")}
    bounded, audit = bound_comparison_witness(inputs(), source)
    assert "διηγεῖται" in bounded["text"] and bounded["text"].startswith("ἀνθρωπος")
    assert audit["status"] == "bounded-body-voting-witness"


@pytest.mark.parametrize("fresh,source", [
    (inputs()[:1], BODY),
    ([{**row, "vote_group": "same"} for row in inputs()], BODY),
    (inputs()[:-1] + [{**inputs()[-1], "text": BODY + " ἕτερον"}], BODY),
    (inputs(), "ἄλλο ἔργον ἄλλη φωνή"),
    (inputs(), BODY + " " + BODY),
])
def test_unmatched_or_ambiguous_source_stays_outside_voting(fresh, source):
    bounded, audit = bound_comparison_witness(fresh, {"id": "library", "text": source})
    assert bounded is None and audit["status"] == "held-comparison-only"
    assert audit["original_text"] == source and audit["corrected_text"] is None


def test_short_anchors_cannot_be_requested():
    with pytest.raises(ValueError, match="four words"):
        bound_comparison_witness(inputs(), {"id": "library", "text": BODY}, minimum_words=3)
