import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from ocr_consensus import compact_corpus_consensus, merge_witnesses, restore_corpus_consensus


def witness(identifier, text):
    return {"id": identifier, "text": text, "license": "CC-BY-SA-4.0",
        "attribution": "Source witness", "source_url": "https://example.org/source",
        "artifact_sha256": hashlib.sha256(identifier.encode()).hexdigest()}


def test_compact_projection_preserves_every_lexical_boundary_and_raw_witness(tmp_path):
    full = merge_witnesses([witness("a", "ὁ λόγος σαφής ἀνдрῶν ἔχει ταῦτα πάντα"),
                            witness("b", "ὁ λόγος σοφός ἀνдрῶν ἔχει πάντα")])
    original = copy.deepcopy(full)
    reference = {"path": "data/corpus_changes/example/full-networks.json.gz", "key": "scan13"}
    compact = compact_corpus_consensus(full, reference)
    before, after = full["ocr_consensus"], compact["ocr_consensus"]
    assert compact["text"] == full["text"]
    assert compact["analysis_text"] == full["analysis_text"]
    assert after["witnesses"] == before["witnesses"]
    assert after["counts"] == before["counts"]
    assert after["policy"] == before["policy"]
    assert len(after["slots"]) == len(before["slots"])
    assert any(not slot["lexical_eligible"] for slot in after["slots"])
    fields = {"position", "selected", "status", "lexical_eligible", "tied_readings"}
    assert all(set(slot) == fields for slot in after["slots"])
    assert all(all(slot[k] == source[k] for k in fields)
               for slot, source in zip(after["slots"], before["slots"]))
    assert full == original  # Compacting never mutates the full audit artifact.
    archive = tmp_path / "full-networks.json.gz"
    archive.write_bytes(gzip.compress(json.dumps({reference["key"]: full}, ensure_ascii=False).encode(), mtime=0))
    loaded = json.loads(gzip.decompress(archive.read_bytes()))[after["full_network"]["key"]]
    assert restore_corpus_consensus(compact, loaded) == full
    assert any("surfaces" in reading for slot in loaded["ocr_consensus"]["slots"] for reading in slot["readings"])
    assert any(slot["abstentions"] or slot["omission_support"] for slot in loaded["ocr_consensus"]["slots"])
    compact["ocr_consensus"]["witnesses"][0]["license"] = "changed"
    assert full == original
    with pytest.raises(ValueError, match="projection differs"):
        restore_corpus_consensus(compact, loaded)


def test_archive_hash_and_reference_prevent_silent_loss_of_network_metadata():
    full = merge_witnesses([witness("a", "λόγος σαφής"), witness("b", "λόγος σοφός")])
    compact = compact_corpus_consensus(full, {"path": "data/network.json.gz", "key": "13"})
    changed = copy.deepcopy(full)
    changed["ocr_consensus"]["slots"][0]["readings"][0]["surfaces"]["a"] = "changed"
    with pytest.raises(ValueError, match="network changed"):
        restore_corpus_consensus(compact, changed)
    for path in ("/absolute/network.json.gz", "../network.json.gz", "https://example.org/network", "C:\\network"):
        with pytest.raises(ValueError, match="relative archive"):
            compact_corpus_consensus(full, {"path": path, "key": "13"})
    with pytest.raises(ValueError, match="before compacting"):
        compact_corpus_consensus(compact, {"path": "data/network.json.gz", "key": "13"})


def test_large_repeated_metadata_stays_in_archive_instead_of_each_corpus_slot():
    full = merge_witnesses([witness("source-a@" + "a" * 40, "ὁ λόγος σαφής " * 80),
                            witness("source-b@" + "b" * 40, "ὁ λόγος σοφός " * 80)])
    compact = compact_corpus_consensus(full, {"path": "data/network.json.gz", "key": "13"})
    assert len(json.dumps(compact)) < len(json.dumps(full)) / 2
