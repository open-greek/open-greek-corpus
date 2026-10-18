import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import compare_oga_glaux_dates as dates


def test_astronomical_year_zero_and_bce_ce_labels():
    before = dates.endpoint("-0001-12", convention="astronomical")
    zero = dates.endpoint("+0000-01", convention="astronomical")
    after = dates.endpoint("+0001-01", convention="astronomical")
    assert [v["era_label"] for v in (before, zero, after)] == ["2 BCE", "1 BCE", "1 CE"]
    assert dates.endpoint("—0001", convention="astronomical")["year"] == -1
    assert dates.endpoint("−0001", convention="astronomical")["year"] == -1
    assert dates.endpoint("–0001", convention="astronomical")["year"] == -1
    cross = dates.normalize_intervals("-0001-12/+0001-01")["intervals"][0]
    assert dates.interval_key(cross) == (-1, 12, 1, 1, 1, 31)


def test_historical_years_do_not_have_year_zero():
    assert dates.endpoint("-0001", convention="historical")["year"] == 0
    assert dates.endpoint("-0100", convention="historical")["era_label"] == "100 BCE"
    assert dates.endpoint("+0001", convention="historical")["era_label"] == "1 CE"
    with pytest.raises(ValueError, match="no year zero"):
        dates.endpoint("+0000", convention="historical")
    with pytest.raises(ValueError, match="negative zero"):
        dates.endpoint("-0000", convention="astronomical")


def test_unknown_year_numbering_keeps_both_interpretations():
    value = dates.normalize_intervals("-0100/-0001", convention="unspecified")
    assert value["status"] == "ambiguous"
    assert [dates.interval_key(i) for i in value["intervals"]] == [
        (-100, 1, 1, -1, 12, 31), (-99, 1, 1, 0, 12, 31)]
    assert {i["interpretation"] for i in value["intervals"]} == {"historical", "astronomical"}
    # Positive years coincide, but both source-convention readings survive.
    positive = dates.normalize_intervals("+0100/+0200", convention="unspecified")
    assert positive["status"] == "valid"
    assert len(positive["intervals"]) == 2


def test_multiple_intervals_are_never_collapsed_or_inferred_from_a_slash_list():
    value = dates.normalize_intervals("-0400/-0300; +0100/+0200")
    assert value["status"] == "multiple"
    assert len(value["intervals"]) == 2
    assert dates.normalize_intervals(["+0100/+0200", "+0300/+0400"])["status"] == "multiple"
    ambiguous = dates.normalize_intervals("+0100/+0200/+0300")
    assert ambiguous["status"] == "unresolved"
    assert ambiguous["intervals"] == []
    assert ambiguous["issues"][0]["reason"] == "ambiguous or open interval"
    assert dates.normalize_intervals("")["status"] == "missing"
    assert dates.normalize_intervals("2nd century BCE")["status"] == "unresolved"


@pytest.mark.parametrize("raw", ["+0200-13/+0300-01", "+0300/+0200", "+0001-02-29/+0001-03-01", "+0100/", "circa +0100"])
def test_invalid_and_uncertain_dates_remain_unresolved(raw):
    value = dates.normalize_intervals(raw)
    assert value["status"] == "unresolved"
    assert value["intervals"] == []
    assert value["issues"]


def test_calendar_boundaries_and_precision_are_explicit():
    zero = dates.normalize_intervals("+0000-02")["intervals"][0]
    assert zero["end"]["day"] == 29
    assert zero["end"]["precision"] == "month"
    century = dates.normalize_intervals("+0100-02")["intervals"][0]
    assert century["end"]["day"] == 28
    exact = dates.normalize_intervals("+2000-02-29")["intervals"][0]
    assert exact["start"]["precision"] == "day"
    assert exact["end"]["day"] == 29


def test_exact_cts_suffixes_are_not_folded_to_parent_work():
    assert dates.glaux_cts("0096-002a") == "tlg0096.tlg002a"
    assert dates.glaux_cts("0096-002b") == "tlg0096.tlg002b"
    assert dates.cts_key("urn:cts:greekLit:tlg0096.tlg002a") == "tlg0096.tlg002a"
    with pytest.raises(ValueError):
        dates.cts_key("urn:cts:greekLit:tlg0096.tlg002a:1")
    with pytest.raises(ValueError):
        dates.glaux_cts("0096-002/003")


def test_all_source_rows_and_dependent_provenance_survive_without_a_vote():
    artifacts = dates.generate()
    manifest = json.loads(artifacts[dates.MANIFEST])
    output = json.loads(artifacts[dates.OUT])
    assert manifest["version_doi"] == "10.5281/zenodo.14254073"
    assert manifest["license"] == "CC-BY-SA-4.0"
    assert manifest["creator"] == "Mark G. Bilby"
    assert manifest["counts"]["bilby_rows_by_file"] == {
        "glaux_oga_matches.csv": 1182, "glaux_unique.csv": 239, "oga_unique.csv": 735}
    assert manifest["counts"]["exact_cts_keys"] == 2149
    assert len(output["works"]["tlg2018.tlg007"]["readings"]) >= 3  # two CSV rows plus OGA
    for suffix in ("a", "b"):
        work = output["works"]["tlg0096.tlg002" + suffix]
        assert "aesopus-et-aesopica.fabulae" not in work["corpus_work_candidates"]
        assert {r["cts"] for r in work["readings"]} == {"tlg0096.tlg002" + suffix}
    work = output["works"]["tlg0012.tlg001"]
    bilby = next(r for r in work["readings"] if r["source"] == "bilby-0.1")
    assert bilby["source_families"] == ["oga", "glaux"]
    assert work["comparison"]["selection"] is None
    assert work["comparison"]["independent_third_vote"] is False
    assert len(work["comparison"]["available_intervals"]) == 2
    oga = next(r for r in work["readings"] if r["source"] == "oga-v0.2.0")
    assert oga["raw"]["formatted_work_date"].startswith("—")
    assert oga["raw"]["date_source"]
    assert dates.generate() == artifacts


def test_checksum_drift_is_rejected():
    name = "oga_unique.csv"
    raw = (dates.ROOT / dates.REFERENCE / name).read_bytes()
    dates.verify_source(name, raw)
    with pytest.raises(ValueError, match="checksum"):
        dates.verify_source(name, raw + b" ")


def test_comparison_retains_disagreement_and_year_convention_dependence():
    def reading(name, raw, convention="astronomical"):
        return {"id": name, "source": "bilby-0.1" if name == "bilby" else "glaux-current",
                "date": dates.normalize_intervals(raw, convention=convention)}
    bilby = reading("bilby", "-0099/+0000")
    glaux = reading("glaux", "-0100/-0001", "unspecified")
    before = copy.deepcopy([bilby, glaux])
    result = dates.compare_readings([bilby, glaux])
    assert result["bilby_source_comparisons"][0]["relation"] == "convention-dependent"
    assert result["bilby_source_comparisons"][0]["matching_interpretations"] == ["historical"]
    assert [bilby, glaux] == before
    different = dates.compare_readings([bilby, reading("oga", "+0100/+0200")])
    assert different["bilby_source_comparisons"][0]["relation"] == "different"
    assert len(different["available_intervals"]) == 2
