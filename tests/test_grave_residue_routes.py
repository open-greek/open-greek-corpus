"""Route attribution for the issue #4 grave-residue audit."""

import sys
import types
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import measure_grave_residue as mgr  # noqa: E402
from measure_grave_residue import has_greek_letter, mapping_route  # noqa: E402


def route(**changes):
    values = {
        "form": "σοφιστὴς",
        "lemma": "σοφιστὴς",
        "cache_is_current": True,
        "nonlexical": False,
        "structured": [],
        "current": "σοφιστὴς",
    }
    values.update(changes)
    return mapping_route(**values)


def test_nonlexical_precedes_cache_age():
    assert route(nonlexical=True, cache_is_current=False) == "nonlexical"


def test_version_mismatch_is_stale_cache():
    assert route(cache_is_current=False) == "stale_cache"


def test_exact_structured_candidate_is_live_emission():
    candidate = {"lemma": "σοφιστὴς", "source": "lookup", "via": "exact"}
    assert route(structured=[candidate]) == "structured"


def test_identity_and_model_outputs_share_the_fallback_bucket():
    assert route(current="σοφιστὴς") == "fallback"


def test_changed_or_supplied_mapping_is_validator_accepted_source():
    assert route(current=None) == "accepted_source"


def test_all_nonlexical_residue_needs_no_ignored_cache(monkeypatch, tmp_path):
    class FakeDilemma:
        def __init__(self, lang=None):
            pass

        @staticmethod
        def is_lexical(value):
            return value != "λέξις"

    module = types.ModuleType("dilemma")
    module.Dilemma = FakeDilemma
    monkeypatch.setitem(sys.modules, "dilemma", module)
    monkeypatch.setattr(mgr, "FORM_LEMMAS", tmp_path / "absent.tsv.gz")
    monkeypatch.setattr(mgr, "FORM_LEMMA_META", tmp_path / "absent.json")
    monkeypatch.setattr(mgr, "installed_dilemma_version", lambda: "1.2.3")

    report = mgr.classify_cache_routes({"λέξις": 32})
    assert report["cache_required"] is False
    assert report["by_route"]["nonlexical"]["tokens"] == 32
    assert report["by_route"]["structured"]["tokens"] == 0


def test_accent_marks_are_not_lexical_surface_targets():
    assert not has_greek_letter("̔́")
    assert has_greek_letter("σοφιστής")
