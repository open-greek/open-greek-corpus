"""The correction-quality figures have to match the censuses they come from.

`scripts/build_corpus_release.py` says of its MEASURED dict that the figures are
"not derivable from anything in this repo" and are transcribed by hand from the
README, which is true of the sampled rates and is why nothing checked them. The
censuses are different: each one leaves a gate file upstream whose agreement
matrix IS the figure, so a transcription can be checked against it.

Nothing did, and the drift was real. The 2026-08-21 confusion/accepted census
reverted 1,512 corrections and rewrote 369 served works; MEASURED and the README
went on saying 19,033 had been taken out since the 2026-08-12 sample, a figure
that stopped at the census before it, and went on presenting that cell as a
144-item sample at 84.7% when the whole cell had been read at 86.6%. Both numbers
are published in data/corpus_release.json, which a citation points at.

The gates live in the upstream correction pipeline, which is a separate private
checkout, so this test skips where that checkout is absent - the same fallback
data/corrections_log/ gets. Point PRECISION_DIR at it to override the default
sibling path.
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_corpus_release import MEASURED  # noqa: E402

README = (REPO / "README.md").read_text(encoding="utf-8")

PRECISION = Path(os.environ.get(
    "PRECISION_DIR", REPO.parent / "greek-ocr" / "data" / "precision"))
CORRECTIONS = PRECISION.parent / "corrections"

# The cell each censused route was read in. A route is one store plus one status;
# the gate directory names it with an underscore.
GATE_DIR = {
    "freq/accepted": "cell_freq_accepted",
    "freq/auto": "cell_freq_auto",
    "confusion/accepted": "cell_confusion_accepted",
    "llm/accepted": "cell_llm_accepted",
}

# The one revert since the 2026-08-12 sample that is not a cell census: the
# re-adjudication accepts pass, which has its own audit rather than a gate.
READJUDICATION = ("readjudication_2026-08-11-readj.accepts-pass.json", 1447)

needs_gates = pytest.mark.skipif(
    not PRECISION.is_dir(),
    reason=f"no upstream precision dir at {PRECISION}; set PRECISION_DIR")


def _n(s: str) -> int:
    return int(s.replace(",", ""))


def _gate(route: str) -> dict:
    fp = PRECISION / GATE_DIR[route] / "cell_gate.json"
    assert fp.is_file(), f"{route} is recorded as censused but {fp} is missing"
    return json.loads(fp.read_text(encoding="utf-8"))


def _censused() -> dict[str, dict]:
    """The per-route entries of MEASURED's censused block, without its prose."""
    return {k: v for k, v in MEASURED["censused_by_corrector"].items()
            if isinstance(v, dict)}


@needs_gates
def test_every_censused_route_matches_its_gate():
    for route, said in _censused().items():
        gate = _gate(route)
        rated = gate["agreement"]["items"]
        assert said["rated"] == rated, f"{route}: rated"
        assert said["reverted"] == len(gate["allowed"]), f"{route}: reverted"
        assert said["sound"] == round(gate["precision"]["rate"], 3), \
            f"{route}: sound rate"
        assert said["agreement"] == round(
            gate["agreement"]["identical_verdict"] / rated, 3), \
            f"{route}: rater agreement"
        # The third band. A gate reverts only both-wrong, so everything the raters
        # disagreed on is still in the served text, and the soundness rate alone
        # does not say how much. Derived from the matrix rather than transcribed.
        matrix = gate["agreement"]["matrix"]
        both_right, both_wrong = matrix["right/right"], matrix["wrong/wrong"]
        assert said["split_still_applied"] == rated - both_right - both_wrong, \
            f"{route}: split still applied"
        assert said["split_with_a_wrong_verdict"] == sum(
            matrix[k] for k in ("right/wrong", "wrong/right",
                                "unsure/wrong", "wrong/unsure")), \
            f"{route}: split records carrying a wrong verdict"


@needs_gates
def test_a_census_that_claims_completeness_has_no_outstanding_batches():
    for route in _censused():
        gate = _gate(route)
        assert gate.get("complete") is True, f"{route} is not complete"
        assert not gate.get("batches_outstanding"), f"{route} has batches left"


@needs_gates
def test_rated_never_exceeds_the_cell_it_was_drawn_from():
    """Staging drops records that no longer resolve to a served row, so a census
    reads at most its cell. A `rated` above `cell_records` means the wrong
    denominator was transcribed, which is what makes a census look complete."""
    for route, said in _censused().items():
        assert said["rated"] <= said["cell_records"], route


@needs_gates
def test_reverted_since_measurement_is_the_sum_of_its_parts():
    audit, expected = READJUDICATION
    fp = CORRECTIONS / audit
    if not fp.is_file():
        pytest.skip(f"no {audit}; data/corrections is local to the pipeline")
    blob = json.loads(fp.read_text(encoding="utf-8"))
    readj = blob.get("n_records") or len(blob.get("records", []))
    assert readj == expected, "the re-adjudication accepts pass moved"
    total = readj + sum(v["reverted"] for v in _censused().values())
    assert MEASURED["reverted_since_measurement"]["records"] == total


def test_the_readme_quotes_the_same_reverted_total():
    said = MEASURED["reverted_since_measurement"]["records"]
    m = re.search(r"([\d,]+) have been taken out since", README)
    assert m, "the reverted-since sentence moved; update this test with it"
    assert _n(m.group(1)) == said


def test_the_readme_names_every_censused_cell_with_its_own_figures():
    """The README's supersession rule only works if the reader can see which
    cells it covers. Naming two when three have been read leaves the third
    presented as the weaker sampled figure with nothing saying otherwise."""
    para = re.search(r"Most of that removal is not sampling at all\.(.+?)\n\n",
                     README, re.S)
    assert para, "the census paragraph moved; update this test with it"
    text = para.group(1)
    for route, said in _censused().items():
        store, status = route.split("/")
        if route == "llm/accepted":
            continue        # argued in its own paragraph further down
        assert f"`{store}`/{status}" in text, f"{route} is not named"
        assert f"{said['rated']:,}" in text, f"{route}: rated not quoted"
    total = sum(v["reverted"] for k, v in _censused().items()
                if k != "llm/accepted")
    assert f"{total:,}" in text, "the reverted total is not quoted"


@needs_gates
def test_overlay_reach_matches_the_upstream_measurement():
    """The three population figures were a hand count for five weeks and drifted by
    thousands because nothing could rebuild them. measure_overlay_reach.py can, so
    its artifact is the authority and MEASURED is checked against it."""
    fp = PRECISION / "overlay_reach.json"
    if not fp.is_file():
        pytest.skip("no overlay_reach.json; run measure_overlay_reach.py --write")
    got = json.loads(fp.read_text(encoding="utf-8"))
    counts = got["counts"]
    present = counts["verifiably present in the served row"]
    absent = counts["not in the text: row found, corrected form absent"]
    orphans = sum(v for k, v in counts.items() if k.startswith("orphan"))
    reach = MEASURED["overlay_reach"]

    assert MEASURED["active_records"] == got["active_records"]
    assert MEASURED["corrections_present"] == present
    assert MEASURED["corrections_present_works"] == got["present_works"]
    assert reach["orphans"] == orphans
    assert reach["row_found_but_neither_form_standing"] == absent
    # The partition has to close, or one of the figures is describing another run.
    assert present + absent + orphans == got["active_records"]
    assert (reach["placed_on_a_served_row"]
            + reach["accounted_for_but_not_served"]
            + reach["unaccounted"]) == reach["orphans"]


def test_the_readme_quotes_the_reach_figures():
    reach = MEASURED["overlay_reach"]
    for n in (MEASURED["active_records"], MEASURED["corrections_present"],
              MEASURED["corrections_present_works"], reach["orphans"],
              reach["placed_on_a_served_row"],
              reach["accounted_for_but_not_served"], reach["unaccounted"]):
        assert f"{n:,}" in README, f"the README does not quote {n:,}"


@needs_gates
def test_stamp_gap_matches_the_upstream_measurement():
    """The raw-OCR share is published as an upper bound, and this is the margin. If it
    drifts, the README's caveat is quoting a number the measurement no longer gets."""
    fp = PRECISION / "stamp_gap.json"
    if not fp.is_file():
        pytest.skip("no stamp_gap.json; run measure_stamp_gap.py --write")
    got = json.loads(fp.read_text(encoding="utf-8"))
    said = MEASURED["stamp_gap"]
    for key in ("pairs", "works_affected",
                "works_under_the_floor_only_because_of_it"):
        assert said[key] == got[key], key
    for n in (said["pairs"], said["works_affected"],
              said["works_under_the_floor_only_because_of_it"]):
        assert f"{n:,}" in README or str(n) in README, f"the README omits {n}"


def test_the_readme_quotes_the_split_residual():
    """The third band is the one a reader is most likely to miss, so the prose has
    to carry it: a gate that reverts only both-wrong leaves every disagreement in
    the text, and no soundness rate above says how many that is."""
    split = sum(v["split_still_applied"] for v in _censused().values())
    carrying = sum(v["split_with_a_wrong_verdict"] for v in _censused().values())
    assert f"{split:,} records" in README, (
        f"the README does not say {split:,} records are still applied on a split "
        f"verdict")
    assert f"{carrying:,}" in README, (
        f"the README does not say {carrying:,} of them carry a wrong verdict")
