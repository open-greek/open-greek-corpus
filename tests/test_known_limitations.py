import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "build_known_limitations", REPO / "scripts" / "build_known_limitations.py")
KNOWN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(KNOWN)


def test_published_known_limitations_are_current():
    published = json.loads(
        (REPO / "data" / "known_limitations.json").read_text(encoding="utf-8"))
    assert published == KNOWN.build()


def test_every_accepted_limitation_has_a_reopen_condition():
    limitations = KNOWN.build()["limitations"]
    assert [row["issue"].rsplit("/", 1)[-1] for row in limitations] == ["1", "2", "31"]
    assert all(row["status"] == "accepted-measured-limitation" for row in limitations)
    assert all(row["reopen_when"] for row in limitations)


def test_metrics_come_from_the_current_source_artifacts():
    limitations = {row["key"]: row for row in KNOWN.build()["limitations"]}
    stamp = json.loads(
        (REPO / "data" / "correction_stamp_gap.json").read_text(encoding="utf-8"))
    graves = json.loads(
        (REPO / "data" / "nonfinal_graves.json").read_text(encoding="utf-8"))

    assert limitations["raw-ocr-coverage"]["current_measurement"][
        "upper_bound_tokens"] == stamp["raw_ocr"]["upper_bound_tokens"]
    assert limitations["nonfinal-grave-source-errors"]["current_measurement"][
        "tokens"] == graves["tokens"]
