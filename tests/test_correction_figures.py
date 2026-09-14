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

The gates live in the upstream correction pipeline, which is a separate checkout, so
this test skips where that checkout is absent - the same fallback
data/corrections_log/ gets. Set OCR_PIPELINE to enable it; see
scripts/upstream_pipeline.py.
"""

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_corpus_release import MEASURED, stamp_gap_block  # noqa: E402

README = (REPO / "README.md").read_text(encoding="utf-8")

from upstream_pipeline import ENV, upstream  # noqa: E402

PRECISION = upstream("data", "precision")
CORRECTIONS = upstream("data", "corrections")

# The cell each censused route was read in. A route is one store plus one status;
# the gate directory names it with an underscore.
GATE_DIR = {
    "freq/accepted": "cell_freq_accepted",
    "freq/auto": "cell_freq_auto",
    "confusion/accepted": "cell_confusion_accepted",
    "llm/accepted": "cell_llm_accepted",
    "llm/auto": "cell_llm_auto",
}

REVERT_AUDITS_SINCE_MEASUREMENT = {
    "cell_revert_llm_auto_gated_2026-09-13.json": 4459,
    "cell_revert_llm_auto_gated_2026-09-13.2.json": 2059,
    "cell_revert_llm_auto_gated_2026-09-14.json": 1123,
}

needs_gates = pytest.mark.skipif(
    PRECISION is None,
    reason=f"no upstream census gates; set {ENV} to enable this")


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
def test_latest_overlay_sample_matches_the_upstream_measurement():
    sample_dir = PRECISION / "overlay_2026-09-13"
    precision = json.loads((sample_dir / "overlay_precision.json").read_text(
        encoding="utf-8"))
    keymap = json.loads((sample_dir / "overlay_keymap.json").read_text(
        encoding="utf-8"))
    meta = keymap["_meta"]
    said = MEASURED["sample"]

    assert said["seed"] == meta["seed"]
    assert said["drawn"] == meta["per_route"] * len(meta["population"])
    assert said["population"] == sum(meta["population"].values())
    assert said["rated"] == precision["corpus_weighted"]["rated"]
    for route, value in MEASURED["precision_by_corrector"].items():
        assert value == round(precision["routes"][route]["both_right_rate"], 3)
    for key in ("sound", "wrong", "split_or_unsure", "single_rater_rate"):
        source = "bad" if key == "wrong" else key
        assert MEASURED["corpus_weighted"][key] == round(
            precision["corpus_weighted"][source], 3)


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
def test_reverted_since_measurement_is_the_sum_of_its_audits():
    """The September sample froze immediately before the three census payouts."""
    if CORRECTIONS is None:
        pytest.skip("data/corrections is local to the pipeline")
    total = 0
    for name, expected in REVERT_AUDITS_SINCE_MEASUREMENT.items():
        fp = CORRECTIONS / name
        assert fp.is_file(), name
        count = len(json.loads(fp.read_text(encoding="utf-8"))["records"])
        assert count == expected, name
        total += count
    assert MEASURED["reverted_since_measurement"]["records"] == total


@needs_gates
def test_no_active_record_carries_an_edit_a_census_condemned():
    """A census verdict is about the edit on the row, so a duplicate record from another
    corrector carrying the same edit is condemned too. 205 were not, and 169 of those
    edits were still in the served text, which is how a reverted correction comes back."""
    gate = PRECISION / "condemned_duplicates_gate.json"
    if not gate.is_file():
        pytest.skip("no condemned_duplicates_gate.json; run "
                    "find_condemned_duplicates.py")
    blob = json.loads(gate.read_text(encoding="utf-8"))
    assert blob["staged"] == len(blob["allowed"])


def test_the_readme_quotes_the_same_reverted_total():
    said = MEASURED["reverted_since_measurement"]["records"]
    m = re.search(r"([\d,]+) have been taken out since", README)
    assert m, "the reverted-since sentence moved; update this test with it"
    assert _n(m.group(1)) == said


def test_the_readme_names_every_censused_cell_with_its_own_figures():
    """The README's supersession rule only works if the reader can see which
    cells it covers. Naming two when three have been read leaves the third
    presented as the weaker sampled figure with nothing saying otherwise."""
    para = re.search(r"Five routes now have stronger census evidence than sampling\.(.+?)\n\n",
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
    public = REPO / "data" / "correction_stamp_gap.json"
    assert public.is_file(), "run measure_stamp_gap.py --write-corpus upstream"
    said = json.loads(public.read_text(encoding="utf-8"))
    assert said == got
    for key in ("pairs", "works_affected",
                "works_under_the_floor_only_because_of_it"):
        assert said[key] == got[key], key
    for n in (said["pairs"], said["works_affected"],
              said["works_under_the_floor_only_because_of_it"]):
        assert f"{n:,}" in README or str(n) in README, f"the README omits {n}"


def test_stamp_gap_artifact_refuses_drift_and_impossible_bounds(tmp_path):
    fp = tmp_path / "stamp-gap.json"
    fp.write_text(json.dumps({
        "schema_version": 1,
        "what": "test",
        "tool": "test",
        "pairs": 2,
        "by_method": {"freq": 2},
        "works_affected": 1,
        "works_under_the_floor_only_because_of_it": 1,
        "measured_against": {
            "catalog_sha256": "catalog",
            "corpus_sha256": "corpus",
            "active_correction_records": 7,
        },
        "raw_ocr": {
            "upper_bound_works": 3,
            "upper_bound_tokens": 80,
            "upper_bound_share_of_corpus_tokens": 0.8,
            "lower_bound_tokens": 50,
            "lower_bound_share_of_corpus_tokens": 0.5,
            "works_in_doubt": 1,
            "tokens_in_doubt": 30,
        },
    }), encoding="utf-8")

    current = stamp_gap_block("catalog", "corpus", {"works": 3, "tokens": 80},
                              100, 7, fp)
    assert current["stale"] is False

    drifted = stamp_gap_block("new-catalog", "corpus",
                              {"works": 3, "tokens": 80}, 100, 8, fp)
    assert drifted["stale"] is True
    assert drifted["stale_reasons"] == [
        "catalog sha256 changed", "active correction population changed"]

    blob = json.loads(fp.read_text(encoding="utf-8"))
    blob["raw_ocr"]["lower_bound_tokens"] = 81
    fp.write_text(json.dumps(blob), encoding="utf-8")
    impossible = stamp_gap_block("catalog", "corpus",
                                 {"works": 3, "tokens": 80}, 100, 7, fp)
    assert "invalid raw-OCR token bounds" in impossible["stale_reasons"]


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


# The collation pass bakes new corrections rather than reverting old ones, through a
# PENDING census: every proposal was inactive until two blind raters both called it
# right, so the figures a reader needs are the kept count, the census precision and
# the precision of what was kept, each of which a file upstream carries.
COLLATION_CELL = "cell_collation_proposed"
COLLATION_REREAD = "gate_verify_collation_proposed"


@needs_gates
def test_the_collation_census_matches_its_gate():
    said = MEASURED["history_since_2026_08_12"]["collation"]
    gate = json.loads((PRECISION / COLLATION_CELL / "cell_gate.json")
                      .read_text(encoding="utf-8"))
    assert gate["pending"] and gate["complete"] and not gate["batches_outstanding"]
    rated = gate["agreement"]["items"]
    assert said["rated"] == rated
    assert said["kept"] == gate["bake"]
    assert said["rejected"] == len(gate["allowed"])
    assert said["kept"] + said["rejected"] == rated
    assert said["sound"] == round(gate["precision"]["rate"], 3)
    assert said["agreement"] == round(
        gate["agreement"]["identical_verdict"] / rated, 3)


@needs_gates
def test_the_collation_survivors_match_their_reread():
    said = MEASURED["history_since_2026_08_12"]["survivor_precision"][
        "collation/proposed"]
    got = json.loads((PRECISION / COLLATION_REREAD / "gate_verification.json")
                     .read_text(encoding="utf-8"))
    assert said["rated"] == got["sample"]["rated"]
    assert said["rate"] == round(got["survivor_precision"]["rate"], 3)


def test_collation_written_is_what_the_bake_says_fired():
    """`written` is not the kept count. A kept record can fail to fire, and 205 of
    these would have, keyed to a carved volume the bake cannot reach, had they not
    been re-keyed to the row the census read. The bake audit lists what fired."""
    applied = MEASURED["history_since_2026_08_12"]
    said = applied["collation"]
    assert applied["records"] == sum(applied["by_bake"].values())
    assert applied["by_bake"]["2026-09-11 collation"] == said["written"]
    if CORRECTIONS is None or not any(CORRECTIONS.glob("bake_*.json")):
        pytest.skip("no bake audits; data/corrections is local to the pipeline")
    fired = sum(1 for fp in CORRECTIONS.glob("bake_*.json")
                for r in json.loads(fp.read_text(encoding="utf-8"))["records"]
                if r.get("by") == "collation")
    assert said["written"] == fired


def test_the_readme_quotes_the_collation_figures():
    said = MEASURED["history_since_2026_08_12"]["collation"]
    para = re.search(r"corrected\s+again\s+by\s+collation(.+?)\n\n", README, re.S)
    assert para, "the collation paragraph moved; update this test with it"
    for n in (said["rated"], said["kept"]):
        assert f"{n:,}" in para.group(0), f"the collation paragraph omits {n:,}"
