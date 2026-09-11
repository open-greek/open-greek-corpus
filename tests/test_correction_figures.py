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
