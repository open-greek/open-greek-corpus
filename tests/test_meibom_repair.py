"""A multi-author OCR delivery must split, merge, and reverse reproducibly."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_meibom_work_assignments as repair
import build_work_index as index


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(repair.dump(value))


def fixture(root, monkeypatch):
    registry = {"works": {slug: {"aliases": {"cts": "urn:cts:cogGreek:" + slug},
        "editions": {}, "default_edition": None} for slug in {r[2] for r in repair.RANGES}}}
    registry["works"][repair.OLD].update(default_edition="old")
    registry["works"][repair.OLD]["editions"]["old"] = {"servable": True}
    rows = [{"urn": repair.OLD, "edition": "old", "source": "ocr", "license": "PD",
        "locus": f"aristides_quintilianus_meibom_{scan:04d}.1", "text": "ὁ δὲ λόγος σαφής"}
        for scan in [1, 53, 60, 65, 201, 223, 279, 307, 347, 431, 481, 525, 614, 650, 681, 700]]
    primary = root / f"data/corpus/{repair.OLD}.jsonl"
    primary.parent.mkdir(parents=True)
    primary.write_bytes(repair.jsonl(rows))
    monkeypatch.setattr(repair, "INPUT_SHA256", hashlib.sha256(primary.read_bytes()).hexdigest())
    write(root / "data/source_registry.json", registry)
    write(root / "data/passage_aliases.json", {"schema_version": 1, "aliases": {}})
    write(root / "data/inventory/ocr_edition_sources.json", {})
    fresh = []
    for model in ["Qwen3.6-27B", "Qwen3.8-27B"]:
        path = root / (model + ".jsonl")
        records = [{"_meta": {"model": model, "revision": "pinned", "prompt": "Greek only", "backend": "test"}}]
        for job in repair.fresh_jobs()["pages"]:
            records.append({"scan_page": job["scan_page"], "region": job["region"],
                "raw_prediction": "ὁ δὲ λόγος σαφής", "finish_reason": "stop",
                "image_sha256": str(job["scan_page"])})
        path.write_bytes(repair.jsonl(records))
        fresh.append(path)
    return rows, fresh


def test_apply_routes_all_authors_merges_all_pages_and_undo_is_exact(tmp_path, monkeypatch):
    original_rows, fresh = fixture(tmp_path, monkeypatch)
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in (tmp_path / "data").rglob("*") if path.is_file()}
    repair.run_repair(tmp_path, "apply", fresh)
    repair.run_repair(tmp_path, "check")
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert len(primary) == 164
    assert primary[0]["locus"] == "1.1" and primary[-1]["locus"] == "3.164"
    assert all(row["analysis_text"] == "ὁ δὲ λόγος σαφής" for row in primary)
    paratext = [json.loads(line) for line in (tmp_path / repair.PARATEXT).read_text().splitlines()]
    assert {r["source_page"]["scan_page"] for r in paratext} == {1, 53, 60}
    aliases = json.loads((tmp_path / "data/passage_aliases.json").read_text())["aliases"]
    target = aliases[repair.OLD]["aristides_quintilianus_meibom_0201.1"]
    assert target["slug"] == "cleonides.introductio-harmonica"
    assert target["storage"] == "secondary"
    assert aliases[repair.OLD]["aristides_quintilianus_meibom_0614.1"]["locus"] == "2.84"
    assert aliases[repair.OLD]["aristides_quintilianus_meibom_0650.1"]["locus"] == "3.114"
    monkeypatch.setattr(index, "REPO", tmp_path)
    index.validate_passage_aliases(aliases, {slug: {} for slug in {r[2] for r in repair.RANGES}})
    audit = json.loads((tmp_path / repair.AUDIT_DIR / "changes.json").read_text())
    assert [change["original_row"] for change in audit["assignments"]] == original_rows
    assert all(not change["text_changed"] for change in audit["assignments"])
    repair.run_repair(tmp_path, "undo")
    for name, expected in before.items():
        assert (tmp_path / name).read_bytes() == expected
    assert not (tmp_path / repair.PARATEXT).exists()
    assert not list((tmp_path / "data/corpus_secondary").glob("*.jsonl"))


def test_fresh_ocr_requires_two_models_and_checked_geometry(tmp_path, monkeypatch):
    rows, fresh = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="Two fresh model witnesses"):
        repair.prepare_inputs(tmp_path, fresh[:1])
    records = [json.loads(line) for line in fresh[0].read_text().splitlines()]
    records[1]["region"] = [.02, .03, .52, .97]
    fresh[0].write_bytes(repair.jsonl(records))
    with pytest.raises(ValueError, match="unchecked crop"):
        repair.prepare_inputs(tmp_path, fresh)


def test_metadata_replay_allows_unrelated_changes_but_refuses_changed_assignments():
    before = {"works": {"old": {"title": "unchanged"}}}
    expected = {"works": {"old": {"title": "unchanged", "edition": "merged"}}}
    current = {"works": {"old": {"title": "unchanged", "edition": "merged"}, "other": {"title": "new"}}}
    repair.check_changed_fields(before, expected, current, "registry")
    current["works"]["old"]["edition"] = "wrong"
    with pytest.raises(ValueError, match="Changed Meibom metadata"):
        repair.check_changed_fields(before, expected, current, "registry")


def test_secondary_aliases_require_explicit_storage_and_matching_work(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "REPO", tmp_path)
    path = tmp_path / "data/corpus_secondary/work.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"locus":"1","text":"λόγος"}\n')
    target = {"path": "data/corpus_secondary/work.jsonl", "locus": "1", "slug": "work"}
    with pytest.raises(ValueError, match="Invalid passage alias work"):
        index.validate_passage_aliases({"work": {"old": target}}, {"work": {}})
    target["storage"] = "secondary"
    assert index.validate_passage_aliases({"work": {"old": target}}, {"work": {}})
