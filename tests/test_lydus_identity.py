"""The edition's identity follows its checked source, with reversible links."""
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_lydus_identity as repair


def test_route_preserves_readings_and_correction_history():
    original = {"urn": repair.OLD, "edition": repair.EDITION,
                "cts": "urn:cts:greekLit:tlg2580.tlg001",
                "locus": "lydus_mensibus_wuensch_0038.1",
                "text": "Περὶ μηνῶν καὶ δρόμου σελήνης", "corrections": ["dehyphenation"]}
    output, changes, aliases = repair.route(json.dumps(original).encode())
    row = json.loads(output)
    assert row["urn"] == repair.NEW and row["cts"] == repair.CTS
    assert row["text"] == original["text"]
    assert row["corrections"] == original["corrections"]
    assert aliases[original["locus"]]["slug"] == repair.NEW
    assert changes[0]["original_assignment"]["cts"].endswith("001")
    assert changes[0]["text_changed"] is False
    with pytest.raises(ValueError, match="Repeated"):
        repair.route(output.replace(repair.NEW.encode(), repair.OLD.encode()) * 2)
    original["edition"] = "different-edition"
    with pytest.raises(ValueError, match="Unreviewed"):
        repair.route(json.dumps(original).encode())


def test_committed_identity_and_replay():
    repair.run(ROOT, "check")
    index = json.loads((ROOT / "data/work_index.json").read_text())
    work = index["works"][repair.NEW]
    assert work["id"] == "ogc002117"
    assert work["work_anchors"]["tlg"] == "tlg2580.tlg002"
    assert work["work_anchors"]["wikidata"] == "Q123477897"
    assert index["redirects"][repair.OLD] == repair.NEW
    assert repair.OLD not in index["works"]
    registry = json.loads((ROOT / "data/source_registry.json").read_text())["works"]
    assert registry[repair.OLD]["aliases"]["cts"].endswith("001")
    assert not any(ed.get("servable") for ed in registry[repair.OLD]["editions"].values())
    assert repair.NEW + ".wunsch-1898" in registry[repair.NEW]["editions"]


def test_undo_restores_every_original_byte_and_rejects_later_edits(tmp_path):
    audit_dir = ROOT / repair.AUDIT
    audit = json.loads((audit_dir / "changes.json").read_text())
    snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
    import repair_manetho_citations as manetho
    from migration_fixtures import copy_repair_state
    copy_repair_state(ROOT, tmp_path, repair, [manetho])
    target = tmp_path / ("data/corpus/" + repair.NEW + ".jsonl")
    original = target.read_bytes()
    target.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        repair.run(tmp_path, "undo")
    target.write_bytes(original)
    repair.run(tmp_path, "undo")
    for path, expected in snapshots.items():
        target = tmp_path / path
        assert (target.read_text() if target.exists() else None) == expected, path
