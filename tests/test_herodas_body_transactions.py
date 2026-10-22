"""Interrupted admission must preserve literal undo and a resumable authority.

These tests exercise real file staging, replacement, manifest validation, and
undo. The expensive OCR-to-output replay is replaced by a deterministic small
result; separate recovery tests validate recognition and source decisions.
Every writable input is materialized under tmp_path, never linked to the repo.
"""
import gzip
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import herodas_body_witnesses as witnesses
import repair_editorial_roles as previous
import repair_herodas_body as recovery


@pytest.fixture
def transaction(tmp_path, monkeypatch):
    archive = ROOT / previous.AUDIT
    original = json.loads(gzip.decompress((archive / "before.json.gz").read_bytes()))
    review = json.loads((archive / "source-review.json").read_bytes())
    before = previous.build_outputs(original, review)[0][recovery.PRIMARY]
    assert recovery.sha(before) == recovery.INPUT_SHA256
    rows = [json.loads(line) for line in before.splitlines()]
    rows.append({"urn": recovery.WORK, "edition": "herodas-hk-ocr", "source": "ocr",
        "license": "PD", "locus": "herodas_hk_0076.1", "text": "λόγος μένει",
        "analysis_text": "λόγος μένει", "herodas_body_recovery": {
            "authority": recovery.AUDIT + "/changes.json"}})
    after = recovery.jsonl(rows)
    import herodas_review_state as latest_state
    monkeypatch.setattr(latest_state, "PREDECESSOR_SHA256", recovery.sha(after))
    primary = tmp_path / recovery.PRIMARY
    primary.parent.mkdir(parents=True)
    primary.write_bytes(before)
    (tmp_path / "source.pdf").write_bytes(b"transaction source bytes")
    inputs = {name: tmp_path / filename for name, filename in {
        "witnesses": "historical.gz", "request": "request.json",
        "predictions": "predictions.jsonl"}.items()}
    inputs["witnesses"].write_bytes(recovery.compressed({"fixture": "retained witnesses"}))
    inputs["request"].write_bytes(b'{"fixture":"original request"}\n')
    inputs["predictions"].write_bytes(b'{"fixture":"original predictions"}\n')
    counts = {"original_passages": 62, "recovered_passages": 1, "primary_passages": 63}
    source_review = {76: {"text": "λόγος μένει", "evidence": "Transaction fixture"}}
    monkeypatch.setattr(recovery, "SOURCE_FILES", {
        "source.pdf": recovery.sha(b"transaction source bytes")})
    monkeypatch.setattr(recovery, "recipe_pins", lambda: {"transaction_fixture": "a" * 64})
    monkeypatch.setattr(witnesses, "validate_packet", lambda value: None)
    monkeypatch.setattr(recovery, "_verify_prediction_images", lambda *args: None)
    monkeypatch.setattr(recovery, "source_readings", lambda: source_review)

    def replay(before_raw, packet_raw, request_raw, prediction_raw, reviewed_at, recipe_digest):
        assert json.loads(gzip.decompress(before_raw)) == {recovery.PRIMARY: before.decode()}
        assert packet_raw == inputs["witnesses"].read_bytes()
        assert request_raw == inputs["request"].read_bytes()
        assert prediction_raw == inputs["predictions"].read_bytes()
        return ((recovery.PRIMARY, after),), recovery.encoded([]), recovery.encoded(counts)

    monkeypatch.setattr(recovery, "_replayed_outputs", replay)
    return {"root": tmp_path, "primary": primary, "before": before, "after": after,
        "inputs": inputs, "target": tmp_path / recovery.AUDIT,
        "reviewed_at": "2026-10-22T18:00:00Z"}


def apply(transaction):
    recovery.run(transaction["root"], "apply", **transaction["inputs"],
                 reviewed_at=transaction["reviewed_at"])


def test_failed_primary_replace_keeps_preimage_and_installed_authority_can_resume(transaction, monkeypatch):
    original_replace = os.replace

    def fail_primary(source, destination):
        if Path(destination) == transaction["primary"]:
            raise OSError("injected primary replacement failure")
        return original_replace(source, destination)

    with monkeypatch.context() as failure:
        failure.setattr(os, "replace", fail_primary)
        with pytest.raises(OSError, match="primary replacement"):
            apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["before"]
    assert (transaction["target"] / "changes.json").is_file()
    audit, before, outputs = recovery.verify(transaction["root"], active=False)
    assert before == {recovery.PRIMARY: transaction["before"].decode()}
    assert outputs == {recovery.PRIMARY: transaction["after"]}
    saved_authority = (transaction["target"] / "changes.json").read_bytes()
    # Retained evidence alone is enough to resume; no new OCR inputs are passed.
    recovery.run(transaction["root"], "apply")
    assert transaction["primary"].read_bytes() == transaction["after"]
    assert (transaction["target"] / "changes.json").read_bytes() == saved_authority
    assert recovery.verify(transaction["root"])[0] == audit
    assert not list(transaction["primary"].parent.glob(".herodas.mimiambi.jsonl.*"))


@pytest.mark.parametrize("failure_point", ["evidence-write", "authority-install"])
def test_failed_staging_keeps_primary_and_no_partial_authority(transaction, monkeypatch, failure_point):
    original_write = Path.write_bytes
    original_replace = os.replace

    def fail_evidence(path, raw):
        if path.name == "records.json.gz" and any(part.startswith(".herodas-body-") for part in path.parts):
            raise OSError("injected evidence staging failure")
        return original_write(path, raw)

    def fail_authority(source, destination):
        if Path(destination) == transaction["target"]:
            raise OSError("injected authority install failure")
        return original_replace(source, destination)

    with monkeypatch.context() as failure:
        if failure_point == "evidence-write":
            failure.setattr(Path, "write_bytes", fail_evidence)
        else:
            failure.setattr(os, "replace", fail_authority)
        with pytest.raises(OSError, match="injected"):
            apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["before"]
    assert not transaction["target"].exists()
    assert not list(transaction["target"].parent.glob(".herodas-body-*"))
    apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["after"]
    recovery.verify(transaction["root"])


def test_failed_undo_replace_preserves_checked_output_until_retry(transaction, monkeypatch):
    apply(transaction)
    original_replace = os.replace

    def fail_primary(source, destination):
        if Path(destination) == transaction["primary"]:
            raise OSError("injected undo replacement failure")
        return original_replace(source, destination)

    with monkeypatch.context() as failure:
        failure.setattr(os, "replace", fail_primary)
        with pytest.raises(OSError, match="undo replacement"):
            recovery.undo(transaction["root"])
    assert transaction["primary"].read_bytes() == transaction["after"]
    recovery.verify(transaction["root"])
    recovery.undo(transaction["root"])
    assert transaction["primary"].read_bytes() == transaction["before"]
    recovery.verify(transaction["root"], active=False)
