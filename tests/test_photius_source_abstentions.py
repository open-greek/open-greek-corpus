import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import photius_source_abstentions as abstentions


def fixture(tmp_path, monkeypatch):
    authority = json.loads(abstentions.source_authority()[1])
    entries = [e for e in authority["records"] if e["id"].startswith("photius-bekker-0252-left-lower-gutter-part")]
    monkeypatch.setattr(abstentions, "REVIEWED", {e["id"]: abstentions.REVIEWED[e["id"]] for e in entries})
    request = abstentions.known_geometry_supplement_manifests()[entries[0]["manifest_sha256"]][1]
    jobs = {p["id"]: p for p in request["pages"]}
    meta = {"model": entries[0]["model"], "revision": entries[0]["revision"],
            "manifest_sha256": entries[0]["manifest_sha256"]}
    rows = [{"id": e["id"], "source": e["source"], "scan_page": e["scan_page"],
             "region": e["region"], "image_sha256": e["image_sha256"],
             "raw_prediction": e["original_text"], "finish_reason": "stop",
             "prompt_sha256": abstentions.sha((request["prompt"] + " " + jobs[e["id"]]["prompt_suffix"]).encode())}
            for e in entries]
    path = tmp_path / "retained.jsonl"
    path.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": meta}, *rows]) + b"\n")
    return path


def test_abstention_preserves_exact_source_reading_and_all_identity_pins(tmp_path, monkeypatch):
    path = fixture(tmp_path, monkeypatch)
    report = abstentions.build([path])
    assert len(report["records"]) == 3
    for row in report["records"]:
        assert row["voting_text"] == "" and row["original_text"]
        assert row["raw_file_sha256"] == abstentions.sha(path.read_bytes())
        assert row["raw_prediction_sha256"] == abstentions.sha(row["original_text"].encode())
        assert row["source_pdf_sha256"] == abstentions.SOURCE_SHA
        assert row["reason"] and row["reviewed_at"]


def test_changed_or_missing_reading_cannot_reuse_an_abstention(tmp_path, monkeypatch):
    path = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="exact source-reviewed"):
        abstentions.build([path, path])
    values = [json.loads(line) for line in path.read_bytes().splitlines()]
    values[1]["raw_prediction"] += " ἄλλος"
    path.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in values) + b"\n")
    with pytest.raises(ValueError, match="exact source-reviewed"):
        abstentions.build([path])
    path.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in values[:1]) + b"\n")
    with pytest.raises(ValueError, match="Every source-reviewed"):
        abstentions.build([path])


def test_published_authority_cannot_invent_a_voting_replacement(monkeypatch):
    path, raw = abstentions.source_authority()
    assert len(abstentions.known_abstentions()) == len(abstentions.REVIEWED)
    report = json.loads(raw); report["records"][0]["voting_text"] = "ὁ λόγος"
    monkeypatch.setattr(abstentions, "source_authority", lambda: (path, abstentions.encode(report)))
    with pytest.raises(ValueError, match="original reading"):
        abstentions.known_abstentions()
