"""Reviewed readings replay from frozen originals and unapply exactly."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_photius_readings as layer
import prepare_photius_reading_windows as review


@pytest.fixture
def source_tree(tmp_path, monkeypatch):
    authority = json.loads((ROOT / layer.REVIEW).read_bytes())
    # Stable initial cases: a third vote, a header, and an initial source
    # fragment that both checkpoints would otherwise count as a full word.
    authority["records"] = [r for r in authority["records"] if r["scan_page"] in {14, 34, 38}]
    assert len(authority["records"]) == 3
    loci = {r["locus"] for r in authority["records"]}
    baseline = (ROOT / layer.CORPUS).read_bytes()
    if (ROOT / layer.BEFORE).exists():
        baseline = gzip.decompress((ROOT / layer.BEFORE).read_bytes())
    before = b"".join(line for line in baseline.splitlines(keepends=True) if json.loads(line)["locus"] in loci)
    monkeypatch.setattr(layer, "BASE_SHA", layer.sha(before))
    monkeypatch.setattr(layer, "BODY_BATCHES", ())
    monkeypatch.setattr(review, "build", lambda root=tmp_path: deepcopy(authority))
    paths = {layer.REVIEW: layer.encode(authority), layer.CORPUS: before}
    for path, raw in paths.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(raw)
    network = Path("data/corpus_changes/photius-bekker-coverage/full-networks.json.gz")
    for path in (layer.LIBRARY, network):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, tmp_path / path)
    return tmp_path, before, network


def test_replay_retains_all_models_one_digital_vote_and_exact_undo(source_tree):
    root, before, original_network = source_tree
    old_network = (root / original_network).read_bytes()
    audit = layer.apply(root)
    assert audit["counts"]["reviewed_rows"] == 3
    assert audit["counts"]["digital_voting_rows"] == 2
    assert audit["counts"]["editorial_spans"] == 1
    assert layer.check(root) == audit
    assert (root / original_network).read_bytes() == old_network
    full = json.loads(gzip.decompress((root / layer.NETWORKS).read_bytes()))
    for locus, network in full.items():
        witnesses = network["ocr_consensus"]["witnesses"]
        assert len([w for w in witnesses if w.get("model")]) == 2
        assert len([w for w in witnesses if w["id"] == "source-library-local002"]) == int("0014" not in locus)
    locus = 'photius_bekker1824_0038.1'
    revised, original = full[locus], full[locus + ':raw-vote']
    assert revised['text'] == original['text']
    assert original['ocr_consensus']['slots'][0]['selected'] == 'σῶν'
    assert original['ocr_consensus']['slots'][0]['lexical_eligible']
    assert not revised['ocr_consensus']['slots'][0]['lexical_eligible']
    current = next(json.loads(line) for line in (root / layer.CORPUS).read_bytes().splitlines()
                   if json.loads(line)['locus'] == locus)
    layer.validate_projection(current, root)
    changed = deepcopy(current)
    changed['analysis_text'] += ' σῶν'
    with pytest.raises(ValueError, match='lexical projection'):
        layer.validate_projection(changed, root)
    from photius_body_vote import unapply_boundary_projection
    assert unapply_boundary_projection(revised, original) == original
    raw = (root / layer.CORPUS).read_bytes()
    assert layer.restore_before_bytes(raw, root) == before
    assert raw != before
    layer.undo(root)
    assert (root / layer.CORPUS).read_bytes() == before
    assert not (root / layer.PARATEXT).exists()
    layer.apply(root)
    assert (root / layer.CORPUS).read_bytes() == raw


@pytest.mark.parametrize("path", [layer.REVIEW, layer.LIBRARY])
def test_invalidated_current_source_blocks_check_but_not_frozen_undo(source_tree, path):
    root, before, _ = source_tree
    layer.apply(root)
    (root / path).write_bytes(b"source invalidated")
    with pytest.raises(ValueError, match="invalidated"):
        layer.check(root)
    layer.undo(root)
    assert (root / layer.CORPUS).read_bytes() == before


def test_changed_original_network_blocks_check_but_not_frozen_undo(source_tree):
    root, before, original_network = source_tree
    layer.apply(root)
    (root / original_network).write_bytes(b"source invalidated")
    with pytest.raises(ValueError, match="network changed"):
        layer.check(root)
    layer.undo(root)
    assert (root / layer.CORPUS).read_bytes() == before


def test_independent_reader_edits_cannot_be_hidden_by_repair_or_undo(source_tree):
    root, _, _ = source_tree
    layer.apply(root)
    rows = list(map(json.loads, (root / layer.CORPUS).read_bytes().splitlines()))
    rows[0]["text"] += " ἄλλο"
    raw = layer.jsonl(rows)
    (root / layer.CORPUS).write_bytes(raw)
    for operation in (layer.check, layer.apply, layer.undo):
        with pytest.raises(ValueError):
            operation(root)
    assert (root / layer.CORPUS).read_bytes() == raw


def test_frozen_audit_and_raw_evidence_cannot_be_replaced(source_tree):
    root, _, _ = source_tree
    layer.apply(root)
    audit = json.loads((root / layer.AUDIT).read_bytes())
    path = Path(audit["network_inputs"][0]["frozen_path"])
    (root / path).write_bytes(b"altered frozen evidence")
    for operation in (layer.check, layer.apply, layer.undo):
        with pytest.raises(ValueError, match="network changed"):
            operation(root)


@pytest.mark.parametrize("path", ["/tmp/private.json.gz", "data/../private.json", "data\\private.json", "file:private"])
def test_input_paths_stay_within_public_data(path):
    with pytest.raises(ValueError):
        layer.public_path(path)
