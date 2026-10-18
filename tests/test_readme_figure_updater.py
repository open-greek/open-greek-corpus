"""README prose refresh uses measured eligible counts and keeps unrelated prose."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_readme_figures as updater

TEXT = """Sentinel unrelated prose.
999 of the 9,999 served works have no
external id at all (the exceed-TLG material).
`work_index.json` under `work_anchors` (`cts` on 9,999 works, `tlg` on 9,999,
`wikidata` on 9,999), so joins work.
- 9,999 works served, 99.9M Greek tokens, fourteen sources.
"""


def fixture(root):
    data = root / "data"
    data.mkdir()
    works = {"a": {"work_anchors": {"cts": "c", "tlg": "t", "wikidata": "q"}}, "b": {"work_anchors": {}}}
    coverage = {"a": {"tokens": 75000000, "analysis_tokens": 5000000, "source": "ocr", "sources": ["cgpg", "ocr"]},
                "b": {"tokens": 50000000, "analysis_tokens": 500000, "source": "ocr", "sources": ["ocr"]}}
    (data / "work_index.json").write_text(json.dumps({"works": works}))
    (data / "coverage.json").write_text(json.dumps(coverage))
    (root / "README.md").write_text(TEXT)
    return data


def test_refresh_is_idempotent_and_uses_analysis_not_surface_tokens(tmp_path, monkeypatch):
    data = fixture(tmp_path)
    values, works = updater.figure_values(data)
    assert values == {"works": 2, "analysis_tokens": 5500000, "sources": ["cgpg", "ocr"]}
    rendered = updater.render(TEXT, values, works)
    assert "- 2 works served, 5.5M Greek tokens in the checked lexical projection, 2 source categories." in rendered
    assert "1 of the 2 served works have no\nexternal id at all" in rendered
    assert "`cts` on 1 works, `tlg` on 1,\n`wikidata` on 1)" in rendered
    assert updater.render(rendered, values, works) == rendered
    assert "Sentinel unrelated prose." in rendered
    assert (tmp_path / "README.md").read_text() == TEXT
    monkeypatch.setattr(sys, "argv", ["build_readme_figures.py", "--root", str(tmp_path), "--write"])
    updater.main()
    assert (tmp_path / "README.md").read_text() == rendered
    monkeypatch.setattr(sys, "argv", ["build_readme_figures.py", "--root", str(tmp_path), "--check"])
    updater.main()


def test_refresh_refuses_coverage_without_eligible_source_measurements(tmp_path):
    data = fixture(tmp_path)
    path = data / "coverage.json"
    value = json.loads(path.read_text())
    del value["a"]["analysis_tokens"]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="run build_public_corpus"):
        updater.figure_values(data)


def test_refresh_refuses_a_missing_or_ambiguous_prose_target(tmp_path):
    data = fixture(tmp_path)
    values, works = updater.figure_values(data)
    with pytest.raises(ValueError, match="status sentence is missing or ambiguous"):
        updater.render(TEXT + "- 2 works served, 5.5M Greek tokens, 2 sources.\n", values, works)
