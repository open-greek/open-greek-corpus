import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("lemma_frequency", Path(__file__).parents[1] / "scripts/build_lemma_frequency.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def test_cache_merge_keeps_disagreements_and_only_adds_consensus(tmp_path):
    first, second = tmp_path / "one.tsv", tmp_path / "two.tsv"
    first.write_text("α\tα\nβ\tβ\nγ\tγ\n")
    second.write_text("α\tα\nβ\tβάλλω\nδ\tδ\n")
    active = {"γ": "γῆ"}
    count, conflicts = f.merge_maps(active, [first, second])
    assert count == 2
    assert active == {"γ": "γῆ", "α": "α", "δ": "δ"}
    assert {r["form"] for r in conflicts} == {"β", "γ"}
    assert conflicts[0]["readings"].keys() == {"β", "βάλλω"}
