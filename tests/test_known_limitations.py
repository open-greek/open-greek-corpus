import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "build_known_limitations", REPO / "scripts" / "build_known_limitations.py")
KNOWN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(KNOWN)


@pytest.fixture(scope="module")
def rebuilt():
    # The immutable test snapshot needs one full source-audit replay, shared
    # across the assertions rather than rebuilding every OCR witness four times.
    return KNOWN.build()


def test_published_known_limitations_are_current(rebuilt):
    published = json.loads(
        (REPO / "data" / "known_limitations.json").read_text(encoding="utf-8"))
    assert published == rebuilt


def test_every_accepted_limitation_has_a_reopen_condition(rebuilt):
    limitations = rebuilt["limitations"]
    assert [row["issue"].rsplit("/", 1)[-1] for row in limitations] == ["1", "2", "31", "105", "107"]
    assert all(row["status"] == "accepted-measured-limitation" for row in limitations)
    assert all(row["reopen_when"] for row in limitations)


def test_metrics_come_from_the_current_source_artifacts(rebuilt):
    limitations = {row["key"]: row for row in rebuilt["limitations"]}
    stamp = json.loads(
        (REPO / "data" / "correction_stamp_gap.json").read_text(encoding="utf-8"))
    graves = json.loads(
        (REPO / "data" / "nonfinal_graves.json").read_text(encoding="utf-8"))

    assert limitations["raw-ocr-coverage"]["current_measurement"][
        "legacy_homogeneous_work_bucket"]["upper_bound_tokens"] == stamp["raw_ocr"]["upper_bound_tokens"]
    assert limitations["raw-ocr-coverage"]["current_measurement"]["global_raw_token_bounds"] is None
    assert limitations["nonfinal-grave-source-errors"]["current_measurement"][
        "tokens"] == graves["tokens"]
    reading = limitations["dubner-1855-unresolved-readings"]["current_measurement"]
    audit = json.loads((REPO / reading["authority"]["path"]).read_bytes())
    assert reading["counts"] == audit["counts"]
    categories = reading["counts"]["remaining_unresolved_categories"]
    assert sum(categories[key] for key in ("omission_tie", "accent_case_or_elision_only",
        "different_word_readings")) == reading["counts"]["reading_statuses"]["unresolved"]
    recovered = limitations["hesychius-recovered-columns-reading-uncertainty"]["current_measurement"]
    recovery = json.loads((REPO / recovered["authority"]["path"]).read_bytes())
    assert recovered["repair_status"] == "missing-main-text-leaf-recovered"
    assert recovered["counts"] == recovery["counts"]
    assert recovered["remaining_reading_uncertainty"]["total_slots_excluded"] == (
        recovery["counts"]["reading_statuses"]["unresolved"]
        + recovery["counts"]["single_checkpoint_slots_excluded"])


def test_coverage_findings_keep_open_work_distinct_from_verified_repairs(rebuilt):
    data = rebuilt
    active = data["active_coverage_findings"]
    resolved = data["resolved_coverage_findings"]
    findings = active + resolved
    assert len(findings) == 5
    assert all(row["status"] == "open-coverage-work" and not row["resolution"]["complete"] for row in active)
    assert all(row["resolution"]["complete"] and row["resolution"]["qualification"] for row in resolved)
    assert all(row["resolution"]["publication"]["tracker_close_criterion"] for row in resolved)
    assert all(row["evidence"] and row["corpus_file_sha256"] for row in findings)
