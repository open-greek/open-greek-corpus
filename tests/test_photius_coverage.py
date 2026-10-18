import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_photius_coverage as prepare
import repair_photius_index as repair


def fixture(tmp_path):
    raw = repair.input_bytes(ROOT)
    (tmp_path / repair.CORPUS).parent.mkdir(parents=True)
    (tmp_path / repair.CORPUS).write_bytes(raw)
    aliases = tmp_path / repair.ALIASES
    aliases.write_text(json.dumps({"schema_version": 1, "aliases": {"other": {"1": {"path": "unrelated"}}}}))
    return raw


def test_missing_scan_manifest_retains_verified_boundaries_and_small_preflight():
    manifest = prepare.build()
    assert [p["scan_page"] for p in manifest["pages"][:4]] == [13, 33, 278, 279]
    assert len(manifest["pages"]) == 267
    assert len({p["id"] for p in manifest["pages"]}) == 267
    assert {p["scan_page"] for p in manifest["pages"] if p["role"] == "missing-primary-text"} == set(range(13, 279))
    assert next(p for p in manifest["pages"] if p["scan_page"] == 279)["role"] == "overlap-check"
    assert not manifest["review"]["accepted_for_primary_ingest"]
    assert manifest["sources"]["photius-bekker-combined"]["sha256"] == prepare.SHA256
    assert not repair.is_index_locus("helladius_chrestomathia_photius_bekker_v2_0280.1")
    assert repair.is_index_locus("helladius_chrestomathia_photius_bekker_v2_0281.1")
    assert repair.is_index_locus("helladius_chrestomathia_photius_bekker_v2_0321.1")
    assert not repair.is_index_locus("unrelated_0281.1")
    later = prepare.build_later_gap()
    assert len(later["pages"]) == 43
    assert {p["scan_page"] for p in later["pages"]} == set(range(379, 422))


def test_index_split_preserves_every_historical_reading_and_roundtrips(tmp_path):
    raw = fixture(tmp_path)
    result = repair.apply(tmp_path)
    assert result["index_rows"] == 501
    assert result["body_rows"] == 3846
    old = {r["locus"]: r for r in map(json.loads, raw.decode().splitlines())}
    body = [json.loads(l) for l in (tmp_path / repair.CORPUS).read_text().splitlines()]
    index = [json.loads(l) for l in (tmp_path / repair.PARATEXT).read_text().splitlines()]
    assert len(body) + len(index) == len(old)
    assert all(old[r["locus"]]["text"] == r["text"] for r in body + index)
    assert all(r["class"] == "edition_index" for r in index)
    assert min(r["combined_scan_page"] for r in index) == 558
    repair.check(tmp_path)
    before = (tmp_path / repair.CORPUS).read_bytes()
    repair.apply(tmp_path)
    assert (tmp_path / repair.CORPUS).read_bytes() == before
    repair.undo(tmp_path)
    assert (tmp_path / repair.CORPUS).read_bytes() == raw
    assert not (tmp_path / repair.PARATEXT).exists()
    assert json.loads((tmp_path / repair.ALIASES).read_text())["aliases"] == {"other": {"1": {"path": "unrelated"}}}


def test_index_check_allows_later_additions_but_undo_refuses_them(tmp_path):
    fixture(tmp_path)
    repair.apply(tmp_path)
    with (tmp_path / repair.CORPUS).open("a") as stream:
        stream.write(json.dumps({"locus": "new-prefix.1", "text": "νέον"}) + "\n")
    repair.check(tmp_path)
    with pytest.raises(ValueError, match="later coverage"):
        repair.undo(tmp_path)


def test_unreviewed_input_and_alias_changes_are_rejected(tmp_path):
    raw = fixture(tmp_path)
    with pytest.raises(ValueError, match="snapshot"):
        repair.generate(raw + b" ")
    repair.apply(tmp_path)
    aliases = json.loads((tmp_path / repair.ALIASES).read_text())
    first = next(iter(aliases["aliases"][repair.SLUG]))
    aliases["aliases"][repair.SLUG][first]["locus"] = "wrong"
    (tmp_path / repair.ALIASES).write_text(json.dumps(aliases))
    with pytest.raises(ValueError, match="destination"):
        repair.check(tmp_path)
