"""The retained historical predictions must remain complete and independently named."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import phoenix_crusius_witnesses as witnesses


@pytest.fixture
def source(tmp_path, monkeypatch):
    """Use tiny historical-file substitutes; CI does not need unbundled OCR runs."""
    contents = {}
    for path in witnesses.EXPECTED_SHA256:
        if path.endswith("_timing.json"):
            model = next(w["model"] for w in witnesses.WITNESSES if path.startswith(w["directory"]))
            contents[path] = json.dumps({"model": model}).encode()
        elif path.endswith("_alignment.json"):
            contents[path] = b'{"class":"identical","offset":0}'
        else:
            contents[path] = (path.replace(witnesses.ALIGNED, witnesses.REDO) + "\nἜσθλοι\n").encode()
    monkeypatch.setattr(witnesses, "EXPECTED_SHA256", {p: hashlib.sha256(raw).hexdigest() for p, raw in contents.items()})
    for relative, raw in contents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return tmp_path


def test_two_historical_predictions_and_one_dependent_copy(source):
    packet = witnesses.build_packet(source)
    witnesses.validate_packet(packet)
    witnesses.validate_packet(packet, source)
    assert len(packet["witnesses"]) == 2
    assert packet["derived_copy"]["independent_witness"] is False
    assert {p["scan_page"] for w in packet["witnesses"] for p in w["pages"]} == {68, 69}


def test_missing_original_witness_is_rejected(source):
    packet = witnesses.build_packet(source)
    packet["witnesses"] = packet["witnesses"][1:]
    with pytest.raises(ValueError, match="identity or independence"):
        witnesses.validate_packet(packet)


def test_recomputed_untrusted_content_hash_cannot_replace_prediction(source):
    packet = witnesses.build_packet(source)
    relative = witnesses.OLD + witnesses.BASE + "_0068.grc.txt"
    replacement = "A revised prediction\n"
    packet["files"][relative] = {"text": replacement, "bytes": len(replacement.encode()), "sha256": hashlib.sha256(replacement.encode()).hexdigest()}
    with pytest.raises(ValueError, match="prediction changed"):
        witnesses.validate_packet(packet)


@pytest.mark.parametrize("part", ["tagged_prediction_path", "greek_extraction_path"])
def test_full_predictions_and_extractions_are_both_required(source, part):
    packet = witnesses.build_packet(source)
    relative = packet["witnesses"][0]["pages"][0][part]
    del packet["files"][relative]
    with pytest.raises(ValueError, match="accounting changed"):
        witnesses.validate_packet(packet)
    (source / relative).unlink()
    with pytest.raises(ValueError, match="Missing historical OCR input"):
        witnesses.build_packet(source)


def test_fresh_validation_rejects_changed_source_but_archive_remains_valid(source):
    packet = witnesses.build_packet(source)
    relative = packet["witnesses"][1]["pages"][1]["tagged_prediction_path"]
    (source / relative).write_text("Changed source\n")
    witnesses.validate_packet(packet)
    with pytest.raises(ValueError, match="Live historical OCR input changed"):
        witnesses.validate_packet(packet, source)
    with pytest.raises(ValueError, match="Historical OCR input changed"):
        witnesses.build_packet(source)


def test_dependent_copy_cannot_be_promoted_to_independent(source):
    packet = copy.deepcopy(witnesses.build_packet(source))
    packet["derived_copy"]["independent_witness"] = True
    with pytest.raises(ValueError, match="identity or independence"):
        witnesses.validate_packet(packet)
