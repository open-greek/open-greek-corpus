"""Admission failures preserve the predecessor and can resume from authority.

These exercise real staging, manifest checks, replacement, and undo. Only the
expensive text replay and the frozen predecessor's verifier use small fixtures.
"""
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_herodas_reading_sources as sources
import repair_herodas_body as body
import repair_herodas_readings as review


@pytest.fixture
def transaction(tmp_path, monkeypatch):
    # Obtain the released predecessor even after the real review is admitted.
    authority = ROOT / review.AUDIT / "changes.json"
    if authority.is_file():
        before = review._before(ROOT, json.loads(authority.read_bytes()))
    else:
        before = (ROOT / review.PRIMARY).read_bytes()
    assert review.sha(before) == review.INPUT_SHA256
    rows = [json.loads(line) for line in before.splitlines()]
    rows[0]["text"] = "λόγος μένει"
    rows[0]["herodas_reading_review"] = {"authority": review.AUDIT + "/changes.json"}
    after = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
    primary = tmp_path / review.PRIMARY
    primary.parent.mkdir(parents=True)
    primary.write_bytes(before)
    manifest = tmp_path / sources.BUNDLE / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"{}\n")
    (tmp_path / "predecessor.txt").write_bytes(b"frozen predecessor witness")
    monkeypatch.setattr(review, "source_pins", lambda root: {
        sources.BUNDLE + "/manifest.json": review.sha(b"{}\n")})
    monkeypatch.setattr(review, "recipe_pins", lambda: {"transaction_fixture": "a" * 64})
    monkeypatch.setattr(body, "verify", lambda root, **kwargs: ({}, {}, {review.PRIMARY: before}))
    monkeypatch.setattr(body, "authority_paths", lambda root: (review.PRIMARY, "predecessor.txt"))
    counts = {"passages": 84, "older_passages_reviewed": 62}

    def replay(previous, observation, recorded_at, images, recipes):
        assert previous == before
        assert json.loads(observation) == review.observations()
        return after, review.encoded([]), review.encoded({}), review.encoded(counts)

    monkeypatch.setattr(review, "_replay", replay)
    return {"root": tmp_path, "primary": primary, "before": before,
        "after": after, "target": tmp_path / review.AUDIT}


def apply(transaction):
    review.run(transaction["root"], "apply", "2026-10-22T20:00:00Z")


def test_primary_failure_leaves_complete_authority_that_can_resume(transaction, monkeypatch):
    replace = os.replace

    def fail_primary(source, destination):
        if Path(destination) == transaction["primary"]:
            raise OSError("injected primary replacement failure")
        return replace(source, destination)

    with monkeypatch.context() as failure:
        failure.setattr(os, "replace", fail_primary)
        with pytest.raises(OSError, match="primary replacement"):
            apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["before"]
    audit, before, raw = review.verify(transaction["root"], active=False)
    assert before == transaction["before"] and raw == transaction["after"]
    manifest = (transaction["target"] / "changes.json").read_bytes()
    review.run(transaction["root"], "apply")
    assert transaction["primary"].read_bytes() == transaction["after"]
    assert (transaction["target"] / "changes.json").read_bytes() == manifest
    assert review.verify(transaction["root"])[0] == audit


@pytest.mark.parametrize("point", ["evidence-write", "authority-install"])
def test_failed_staging_never_admits_partial_proof(transaction, monkeypatch, point):
    write, replace = Path.write_bytes, os.replace

    def fail_write(path, raw):
        if path.name == "records.json.gz" and any(part.startswith(".herodas-reading-review-") for part in path.parts):
            raise OSError("injected evidence staging failure")
        return write(path, raw)

    def fail_install(source, destination):
        if Path(destination) == transaction["target"]:
            raise OSError("injected authority install failure")
        return replace(source, destination)

    with monkeypatch.context() as failure:
        failure.setattr(Path, "write_bytes", fail_write) if point == "evidence-write" else failure.setattr(os, "replace", fail_install)
        with pytest.raises(OSError, match="injected"):
            apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["before"]
    assert not transaction["target"].exists()
    assert not list(transaction["target"].parent.glob(".herodas-reading-review-*"))
    apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["after"]


def test_check_rejects_an_unknown_current_file(transaction):
    apply(transaction)
    transaction["primary"].write_bytes(b"unknown current text")
    with pytest.raises(ValueError, match="output changed"):
        review.run(transaction["root"], "check")


@pytest.mark.parametrize("when", ["compilation", "staging"])
def test_changed_predecessor_proof_never_admits_new_text(transaction, monkeypatch, when):
    path = transaction["root"] / "predecessor.txt"
    replay, write = review._replay, Path.write_bytes

    def changed_replay(*args):
        result = replay(*args)
        path.write_bytes(b"changed predecessor witness")
        return result

    def changed_write(candidate, raw):
        result = write(candidate, raw)
        if candidate.name == "records.json.gz" and any(part.startswith(".herodas-reading-review-") for part in candidate.parts):
            write(path, b"changed predecessor witness")
        return result

    if when == "compilation":
        monkeypatch.setattr(review, "_replay", changed_replay)
    else:
        monkeypatch.setattr(Path, "write_bytes", changed_write)
    with pytest.raises(ValueError, match="inputs changed before admission"):
        apply(transaction)
    assert transaction["primary"].read_bytes() == transaction["before"]
    assert not transaction["target"].exists()


def test_failed_undo_remains_retryable_without_source_images(transaction, monkeypatch):
    apply(transaction)
    (transaction["root"] / sources.BUNDLE / "manifest.json").unlink()
    replace = os.replace

    def fail_primary(source, destination):
        if Path(destination) == transaction["primary"]:
            raise OSError("injected undo replacement failure")
        return replace(source, destination)

    with monkeypatch.context() as failure:
        failure.setattr(os, "replace", fail_primary)
        with pytest.raises(OSError, match="undo replacement"):
            review.undo(transaction["root"])
    assert transaction["primary"].read_bytes() == transaction["after"]
    review.undo(transaction["root"])
    assert transaction["primary"].read_bytes() == transaction["before"]
