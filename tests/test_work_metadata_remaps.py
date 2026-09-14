"""Explicit metadata concordances for differently-numbered work editions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_work_index import registry_work_for  # noqa: E402


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
