import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_john_coverage as repair


def test_source_checked_work_boundaries_do_not_extrapolate_page_offsets():
    assert repair.pg74_assignment("pg074_0007.4") == "volume_title"
    assert repair.pg74_assignment("pg074_0398.4") == "john"
    assert repair.pg74_assignment("pg074_0399.1") == "acts"
    assert repair.pg74_assignment("pg074_0409.8") == "acts"
    assert repair.pg74_assignment("pg074_0409.10") == "romans"
    assert repair.pg74_assignment("pg074_0441.2") == "romans"
    for locus in ("pg074_0409.9", "pg074_0008.1", "pg073_0100.1", "pg074_0442.1"):
        with pytest.raises(ValueError):
            repair.pg74_assignment(locus)


def test_calfa_complement_preserves_pinned_readings_and_marker_positions():
    path = ROOT / repair.SOURCE
    if not path.exists():
        pytest.skip("Source archive is created by the coverage admission")
    raw = gzip.decompress(path.read_bytes())
    rows = repair.pg73_records(raw)
    assert len(rows) == 528
    assert rows[0]["source_location"]["marker_page"] == "10"
    assert rows[-1]["source_location"]["marker_page"] == "537"
    assert rows[0]["license"] == "CC-BY-4.0"
    # An obvious OCR error remains an auditable source reading, not a silent fix.
    assert "τολλῆ" in rows[0]["text"]
    assert "ἐκλάμπουσαν" in rows[-1]["text"]
    with pytest.raises(ValueError, match="pinned source"):
        repair.pg73_records(raw + b"\n")


def test_missing_page_witnesses_reject_incomplete_or_failed_outputs(tmp_path):
    (tmp_path / repair.JOBS).parent.mkdir(parents=True)
    jobs = (ROOT / repair.JOBS).read_bytes()
    (tmp_path / repair.JOBS).write_bytes(jobs)
    pages = json.loads(jobs)["pages"]
    paths = []
    for family, revision in [("3.6", "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"),
                             ("3.8", "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a")]:
        rows = [{"_meta": {"model": f"Qwen/Qwen{family}-27B", "revision": revision,
                            "manifest_sha256": repair.sha(jobs)}}]
        rows += [{**{k: p[k] for k in ("id", "source", "scan_page", "region")},
                  "raw_prediction": "Ἐν ἀρχῇ ἦν ὁ λόγος", "finish_reason": "stop",
                  "prompt_sha256": repair.sha(json.loads(jobs)["prompt"].encode())} for p in pages]
        path = tmp_path / (family + ".jsonl")
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        paths.append(path)
    fresh = repair.fresh_inputs(tmp_path, paths)
    assert len(fresh["pages"]) == 3
    with pytest.raises(ValueError, match="Both independent"):
        repair.fresh_inputs(tmp_path, paths[:1])
    rows = [json.loads(line) for line in paths[1].read_text().splitlines()]
    rows[-1]["finish_reason"] = "length"
    paths[1].write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="truncated"):
        repair.fresh_inputs(tmp_path, paths)


def test_committed_coverage_replays_and_reverses_exact_bytes(tmp_path):
    audit_path = ROOT / repair.AUDIT / "changes.json"
    if not audit_path.exists():
        pytest.skip("Coverage admission awaits the independent witnesses")
    audit = json.loads(audit_path.read_text())
    before, (generated, changes) = repair.replay(ROOT)
    ledger = json.loads(generated["data/cgpg_works.json"])
    pg73 = next(row for row in ledger if row.get("volume") == "PG073")
    assert pg73["n_passages"] == 3109
    assert pg73["n_tokens"] == 392203
    for path in [repair.SOURCE, repair.JOBS, repair.AUDIT + "/before.json.gz",
                 repair.AUDIT + "/fresh-witnesses.json.gz", repair.AUDIT + "/changes.json"]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    for path, data in generated.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    repair.check(tmp_path)
    assert len(changes) == 481
    assert audit["counts"]["added_pg74_missing_leaves"] == 3
    repair.undo(tmp_path)
    for path, original in before.items():
        target = tmp_path / path
        assert (target.read_text() if target.exists() else None) == original
    repair.apply(tmp_path)
    repair.check(tmp_path)
    repair.refresh_consensus(tmp_path)
    assert (tmp_path / repair.CORPUS).read_bytes() == generated[repair.CORPUS]
    (tmp_path / repair.CORPUS).write_bytes(generated[repair.CORPUS] + b"\n")
    with pytest.raises(ValueError, match="Unreviewed Cyril output"):
        repair.refresh_consensus(tmp_path)
    (tmp_path / repair.CORPUS).write_bytes(generated[repair.CORPUS])
    registry = tmp_path / "data/source_registry.json"
    values = json.loads(registry.read_text())
    del values["works"][repair.SLUG]["coverage_composition"]
    registry.write_text(json.dumps(values))
    with pytest.raises(ValueError, match="complementary-volume metadata"):
        repair.check(tmp_path)
