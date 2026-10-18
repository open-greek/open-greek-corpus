"""Explicit metadata concordances for differently-numbered work editions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_work_index import registry_work_for  # noqa: E402
from build_id_crosswalk import apply_metadata_remaps  # noqa: E402
import json
import crosswalk  # noqa: E402


def test_explicit_remap_selects_canonical_registry_metadata():
    works = {
        "euripides.cyclops": {
            "author": "euripides",
            "title": "Cyclops",
            "tags": ["genre:satyr-play"],
        }
    }
    slug, row = registry_work_for(
        "euripides.tlg0006-tlg001",
        works,
        {"euripides.tlg0006-tlg001": "euripides.cyclops"},
    )
    assert slug == "euripides.cyclops"
    assert row["tags"] == ["genre:satyr-play"]


def test_unmapped_work_uses_its_own_registry_row():
    works = {"homerus.ilias": {"title": "Ilias"}}
    slug, row = registry_work_for("homerus.ilias", works, {})
    assert slug == "homerus.ilias"
    assert row["title"] == "Ilias"


def test_identified_carve_gets_an_anchor_without_replacing_legacy_ids():
    entries = {"legacy": {"cts": "urn:cts:greekLit:tlg1.tlg2"}}
    registry = {"canonical": {"aliases": {"cts": "urn:cts:greekLit:tlg3.tlg4"},
                              "author": "author", "title": "Work"}}
    assert apply_metadata_remaps(entries, registry, {"carved": "canonical", "legacy": "canonical"},
                                {"carved", "legacy"}) == ["carved"]
    assert entries["carved"]["cts"] == "urn:cts:greekLit:tlg3.tlg4"
    assert entries["legacy"]["cts"] == "urn:cts:greekLit:tlg1.tlg2"


def test_coverage_resolves_reviewed_remap_to_served_work(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "corpus").mkdir(parents=True)
    (data / "corpus/carved.jsonl").write_text("")
    cts = "urn:cts:greekLit:tlg3.tlg4"
    (data / "source_registry.json").write_text(json.dumps({"works": {"canonical": {"aliases": {"cts": cts}}}}))
    (data / "work_metadata_remaps.json").write_text(json.dumps({"works": {"carved": "canonical"}}))
    monkeypatch.setattr(crosswalk, "REPO", tmp_path)
    monkeypatch.setattr(crosswalk, "_MAP", None)
    assert crosswalk.slug_for(cts) == "carved"
