import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_identity import Registry


def test_complementary_and_secondary_edition_metadata_survive_registry_roundtrip(tmp_path):
    registry = Registry()
    author = registry.mint_author("Cyril")
    work = registry.mint_work(author, "Commentary")
    edition = registry.mint_edition(work, "scan", "Reviewed scan")
    registry.works[work].coverage_composition = {"volumes": ["PG073", "PG074"]}
    registry.works[work].editions[edition].storage = "secondary"
    registry.works[work].editions[edition].note = "Exact historical source reading"
    path = tmp_path / "registry.json"
    registry.save(path)
    original = path.read_bytes()
    restored = Registry.load(path)
    restored.save(path)
    assert path.read_bytes() == original
    assert restored.works[work].coverage_composition == {"volumes": ["PG073", "PG074"]}
    assert restored.works[work].editions[edition].storage == "secondary"


def test_empty_optional_fields_do_not_change_ordinary_registry_records(tmp_path):
    registry = Registry()
    author = registry.mint_author("Homer")
    work = registry.mint_work(author, "Iliad")
    edition = registry.mint_edition(work, "scan", "Scan")
    path = tmp_path / "registry.json"
    registry.save(path)
    value = json.loads(path.read_text())["works"][work]
    assert "coverage_composition" not in value
    assert "note" not in value["editions"][edition]
    assert "storage" not in value["editions"][edition]
